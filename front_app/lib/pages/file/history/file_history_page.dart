import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:deepflect_app/widgets/file/history/filter_button.dart';
import 'package:deepflect_app/services/file_service.dart';
import 'package:deepflect_app/services/token_storage.dart';
import 'package:deepflect_app/models/auth/auth_provider.dart';

class FileHistoryPage extends ConsumerStatefulWidget {
  final GlobalKey<FileHistoryPageState>? stateKey;
  
  const FileHistoryPage({super.key, this.stateKey});

  @override
  ConsumerState<FileHistoryPage> createState() => FileHistoryPageState();
}

class FileHistoryPageState extends ConsumerState<FileHistoryPage> {
  final FileService _fileService = FileService();
  int selectedTab = 0;
  final List<String> tabs = ['ALL', '사진', '동영상'];
  List<Map<String, dynamic>> files = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    // 로그인 상태 확인 후 파일 로드
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkAuthAndLoadFiles();
    });
  }

  void refresh() {
    _checkAuthAndLoadFiles();
  }

  Future<void> _checkAuthAndLoadFiles() async {
    // 로그인 상태와 토큰 모두 확인
    final authState = ref.read(authNotifierProvider);
    final hasToken = await TokenStorage.hasTokens();
    
    // 로그인 상태가 아니고 토큰도 없으면 에러 표시
    if (!authState.isAuthenticated && !hasToken) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = '로그인이 필요합니다.';
        });
      }
      return;
    }

    // 로그인 상태이거나 토큰이 있으면 파일 로드
    _loadFiles();
  }

  Future<void> _loadFiles() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      String? type;
      if (selectedTab == 1) {
        type = 'image';
      } else if (selectedTab == 2) {
        type = 'video';
      }

      final fetchedFiles = await _fileService.getFiles(type: type);
      
      if (mounted) {
        setState(() {
          files = fetchedFiles;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        final errorMsg = e.toString().replaceAll('Exception: ', '');
        setState(() {
          _errorMessage = errorMsg;
          _isLoading = false;
        });
        
        // 토큰 관련 에러인 경우 로그인 상태 확인
        if (errorMsg.contains('액세스 토큰') || errorMsg.contains('로그인')) {
          // 로그인 상태 다시 확인
          final authState = ref.read(authNotifierProvider);
          if (!authState.isAuthenticated) {
            setState(() {
              _errorMessage = '로그인이 필요합니다.';
            });
          }
        }
      }
    }
  }

  Future<void> _deleteFile(String taskId, int index) async {
    try {
      await _fileService.deleteFile(taskId);
      if (mounted) {
        setState(() {
          files.removeAt(index);
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('파일이 삭제되었습니다.'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('파일 삭제 실패: ${e.toString().replaceAll('Exception: ', '')}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _downloadFile(String taskId, String fileName) async {
    if (taskId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('다운로드할 수 없는 파일입니다.'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    try {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('$fileName 다운로드를 시작합니다.'),
          duration: const Duration(seconds: 2),
        ),
      );

      final savedPath = await _fileService.downloadFile(taskId, fileName);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('파일이 저장되었습니다: $savedPath'),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('다운로드 실패: ${e.toString().replaceAll('Exception: ', '')}'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            // 헤더 영역
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '히스토리',
                    style: GoogleFonts.k2d(
                      fontSize: 26,
                      fontWeight: FontWeight.w600,
                      color: const Color(0xFF1D0523),
                    ),
                  ),
                  const SizedBox(height: 24),
                  // 상단 필터 버튼
                  Row(
                    children: List.generate(tabs.length, (i) {
                      return Expanded(
                        child: Padding(
                          padding: EdgeInsets.only(
                            right: i < tabs.length - 1 ? 8 : 0,
                          ),
                          child: FilterButton(
                            title: tabs[i],
                            isSelected: selectedTab == i,
                            onTap: () {
                              setState(() {
                                selectedTab = i;
                              });
                              _loadFiles(); // 탭 변경 시 파일 다시 로드
                            },
                          ),
                        ),
                      );
                    }),
                  ),
                ],
              ),
            ),
            // 파일 목록
            Expanded(
              child: _isLoading
                  ? const Center(
                      child: CircularProgressIndicator(
                        color: Color(0xFF27005D),
                      ),
                    )
                  : _errorMessage != null
                      ? Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.error_outline,
                                size: 48,
                                color: Colors.red[300],
                              ),
                              const SizedBox(height: 16),
                              Text(
                                _errorMessage!,
                                style: GoogleFonts.k2d(
                                  fontSize: 14,
                                  color: Colors.grey[600],
                                ),
                                textAlign: TextAlign.center,
                              ),
                              const SizedBox(height: 16),
                              ElevatedButton(
                                onPressed: _loadFiles,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF27005D),
                                  foregroundColor: Colors.white,
                                ),
                                child: const Text('다시 시도'),
                              ),
                            ],
                          ),
                        )
                      : files.isEmpty
                          ? Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    Icons.folder_open,
                                    size: 64,
                                    color: Colors.grey[400],
                                  ),
                                  const SizedBox(height: 16),
                                  Text(
                                    '업로드한 파일이 없습니다',
                                    style: GoogleFonts.k2d(
                                      fontSize: 16,
                                      color: Colors.grey[600],
                                    ),
                                  ),
                                ],
                              ),
                            )
                          : GridView.builder(
                              padding: const EdgeInsets.symmetric(horizontal: 24),
                              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                                crossAxisCount: 3,
                                childAspectRatio: 1,
                                crossAxisSpacing: 12,
                                mainAxisSpacing: 12,
                              ),
                              itemCount: files.length,
                              itemBuilder: (context, index) {
                                final file = files[index];
                                final taskId = file['taskId']?.toString() ?? '';
                                final fileName = file['fileName']?.toString() ?? file['name']?.toString() ?? 'unknown';
                                final previewUrl = file['previewUrl']?.toString();
                                
                                final colors = [
                                  Colors.blue[200]!,
                                  Colors.green[200]!,
                                  Colors.orange[200]!,
                                  Colors.purple[200]!,
                                  Colors.red[200]!,
                                  Colors.teal[200]!,
                                ];
                                
                                final color = colors[index % colors.length];
                                
                                return GestureDetector(
                                  // 사진/동영상 모두 탭 시 바로 다운로드
                                  onTap: () async {
                                    _downloadFile(taskId, fileName);
                                  },
                                  onLongPress: () {
                                    showDialog(
                                      context: context,
                                      builder: (context) => AlertDialog(
                                        title: Text(
                                          '파일 옵션',
                                          style: GoogleFonts.k2d(),
                                        ),
                                        content: Column(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            ListTile(
                                              leading: const Icon(Icons.download_outlined, color: Colors.deepPurple),
                                              title: Text(
                                                '다운로드',
                                                style: GoogleFonts.k2d(),
                                              ),
                                              onTap: () {
                                                Navigator.pop(context);
                                                _downloadFile(taskId, fileName);
                                              },
                                            ),
                                            ListTile(
                                              leading: const Icon(Icons.delete_outline, color: Colors.red),
                                              title: Text(
                                                '삭제',
                                                style: GoogleFonts.k2d(
                                                  color: Colors.red,
                                                ),
                                              ),
                                              onTap: () {
                                                Navigator.pop(context);
                                                _deleteFile(taskId, index);
                                              },
                                            ),
                                          ],
                                        ),
                                        actions: [
                                          TextButton(
                                            onPressed: () => Navigator.pop(context),
                                            child: Text(
                                              '취소',
                                              style: GoogleFonts.k2d(),
                                            ),
                                          ),
                                        ],
                                      ),
                                    );
                                  },
                                  child: Container(
                                    decoration: BoxDecoration(
                                      borderRadius: BorderRadius.circular(12),
                                      color: color,
                                    ),
                                    child: ClipRRect(
                                      borderRadius: BorderRadius.circular(12),
                                      child: previewUrl != null && previewUrl.isNotEmpty
                                          ? Image.network(
                                              previewUrl,
                                              fit: BoxFit.cover,
                                              errorBuilder: (context, error, stackTrace) {
                                                return _buildPlaceholder(fileName, color);
                                              },
                                            )
                                          : _buildPlaceholder(fileName, color),
                                    ),
                                  ),
                                );
                              },
                            ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlaceholder(String fileName, Color color) {
    return Container(
      color: color,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.image,
            size: 50,
            color: Colors.black54,
          ),
          const SizedBox(height: 8),
          Text(
            fileName.length > 10 ? '${fileName.substring(0, 10)}...' : fileName,
            style: GoogleFonts.k2d(
              fontSize: 10,
              color: Colors.grey[600],
            ),
            textAlign: TextAlign.center,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}
