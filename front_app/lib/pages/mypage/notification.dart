import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:deepflect_app/services/notification_service.dart';

class NotificationItem {
  final String id;
  final String title;
  final String date; // yyyy-MM-dd 형식 저장

  NotificationItem({
    required this.id,
    required this.title,
    required this.date,
  });

  factory NotificationItem.fromJson(Map<String, dynamic> json) {
    // API 응답 형식에 맞게 조정
    final id = json['id']?.toString() ?? json['notificationId']?.toString() ?? '';
    final title = json['title']?.toString() ?? json['message']?.toString() ?? '';
    final dateStr = json['createdAt']?.toString() ?? json['date']?.toString() ?? DateTime.now().toIso8601String();
    
    // 날짜 형식 변환 (ISO8601 또는 yyyy-MM-dd)
    String formattedDate = dateStr;
    try {
      final date = DateTime.parse(dateStr);
      formattedDate = date.toIso8601String().split('T')[0]; // yyyy-MM-dd 형식으로 변환
    } catch (e) {
      formattedDate = DateTime.now().toIso8601String().split('T')[0];
    }
    
    return NotificationItem(
      id: id,
      title: title,
      date: formattedDate,
    );
  }
}

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> with WidgetsBindingObserver {
  final NotificationService _notificationService = NotificationService();
  List<NotificationItem> notifications = [];
  bool isDeleteMode = false; // 삭제 모드 여부
  Set<int> selectedIndices = {}; // 선택된 항목의 인덱스 집합
  bool isAllSelected = false;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _loadNotifications();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);
    // 앱이 포그라운드로 돌아올 때 알림 목록 새로고침
    if (state == AppLifecycleState.resumed) {
      _loadNotifications();
    }
  }

  Future<void> _loadNotifications() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await _notificationService.getNotifications();
      
      // API 응답을 NotificationItem으로 변환
      final loaded = response.map((json) => NotificationItem.fromJson(json)).toList();
      
      // 날짜순으로 정렬 (최신순)
      loaded.sort((a, b) => b.date.compareTo(a.date));

      if (mounted) {
        setState(() {
          notifications = loaded;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceAll('Exception: ', '');
          _isLoading = false;
        });
      }
    }
  }

  // 날짜 형식을 yyyy.MM.dd로 변환
  String _formatDate(String dateStr) {
    final date = DateTime.parse(dateStr);
    return '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}';
  }

  // 삭제 모드 진입
  void _enterDeleteMode() {
    setState(() {
      isDeleteMode = true;
      selectedIndices.clear();
      isAllSelected = false;
    });
  }

  // 삭제 모드 종료
  void _exitDeleteMode() {
    setState(() {
      isDeleteMode = false;
      selectedIndices.clear();
      isAllSelected = false;
    });
  }

  // 전체 선택/해제 토글
  void _toggleSelectAll() {
    setState(() {
      if (isAllSelected) {
        selectedIndices.clear();
        isAllSelected = false;
      } else {
        selectedIndices =
            Set.from(List.generate(notifications.length, (i) => i));
        isAllSelected = true;
      }
    });
  }

  // 개별 항목 선택/해제 토글
  void _toggleItemSelection(int index) {
    setState(() {
      if (selectedIndices.contains(index)) {
        selectedIndices.remove(index);
        isAllSelected = false;
      } else {
        selectedIndices.add(index);
        // 모든 항목이 선택되었는지 확인
        if (selectedIndices.length == notifications.length) {
          isAllSelected = true;
        }
      }
    });
  }

  // 선택된 항목 삭제
  Future<void> _deleteSelected() async {
    if (selectedIndices.isEmpty) {
      return;
    }

    // 선택된 알림들의 ID 수집
    final selectedIds = selectedIndices.map((index) => notifications[index].id).toList();
    
    // 서버에 삭제 요청
    bool allSuccess = true;
    for (final id in selectedIds) {
      try {
        await _notificationService.deleteNotification(id);
      } catch (e) {
        allSuccess = false;
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('일부 알림 삭제 실패: ${e.toString().replaceAll('Exception: ', '')}'),
              backgroundColor: Colors.orange,
            ),
          );
        }
      }
    }

    if (allSuccess && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('알림이 삭제되었습니다.'),
          backgroundColor: Colors.green,
        ),
      );
    }

    // 로컬 상태 업데이트
    List<NotificationItem> updatedNotifications = [];
    for (int i = 0; i < notifications.length; i++) {
      if (!selectedIndices.contains(i)) {
        updatedNotifications.add(notifications[i]);
      }
    }

    if (mounted) {
      setState(() {
        notifications = updatedNotifications;
        selectedIndices.clear();
        isAllSelected = false;
        isDeleteMode = false;
      });
    }
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              GestureDetector(
                onTap: () {
                  if (isDeleteMode) {
                    _exitDeleteMode();
                  } else {
                    Navigator.of(context).pop();
                  }
                },
                child: const Icon(
                  Icons.chevron_left,
                  color: Colors.black,
                  size: 28,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Text(
                    '알림',
                    style: GoogleFonts.k2d(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.black,
                    ),
                  ),
                  const Spacer(),
                  if (isDeleteMode)
                    Column(
                      mainAxisSize: MainAxisSize.min,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        GestureDetector(
                          onTap: _toggleSelectAll,
                          child: Container(
                            width: 16,
                            height: 16,
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              color: isAllSelected
                                  ? const Color(0xFF9400FF)
                                  : Colors.transparent,
                              border: Border.all(
                                color: isAllSelected
                                    ? const Color(0xFF9400FF)
                                    : Colors.grey[400]!,
                                width: 2,
                              ),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: isAllSelected
                                ? const Icon(
                                    Icons.check,
                                    color: Colors.white,
                                    size: 12,
                                  )
                                : null,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '전체',
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey[400],
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            Flexible(
              flex: isDeleteMode ? 8 : 1,
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
                                onPressed: _loadNotifications,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF27005D),
                                  foregroundColor: Colors.white,
                                ),
                                child: Text(
                                  '다시 시도',
                                  style: GoogleFonts.k2d(),
                                ),
                              ),
                            ],
                          ),
                        )
                      : notifications.isEmpty
                          ? Center(
                              child: Text(
                                '알림이 없습니다',
                                style: GoogleFonts.k2d(
                                  fontSize: 16,
                                  color: const Color(0xFF9400FF),
                                ),
                              ),
                            )
                          : Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 16),
                              child: ListView.builder(
                                padding: EdgeInsets.only(
                                  bottom: isDeleteMode ? 60 : 16,
                                ),
                                itemCount: notifications.length,
                                itemBuilder: (context, index) {
                          final item = notifications[index];
                          final isSelected = selectedIndices.contains(index);

                          return GestureDetector(
                            onLongPress: () {
                              if (!isDeleteMode) {
                                _enterDeleteMode();
                                _toggleItemSelection(index);
                              }
                            },
                            child: Padding(
                              padding: EdgeInsets.only(
                                bottom: isDeleteMode ? 8 : 16,
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    width: 20,
                                    height: 20,
                                    decoration: const BoxDecoration(
                                      color: Color(0xFF27005D),
                                      shape: BoxShape.circle,
                                    ),
                                    child: const Icon(
                                      Icons.notifications,
                                      color: Colors.white,
                                      size: 15,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          item.title,
                                          style: GoogleFonts.k2d(
                                            fontSize: 16,
                                            color: Colors.black,
                                            fontWeight: FontWeight.w500,
                                          ),
                                        ),
                                        const SizedBox(height: 2),
                                        Text(
                                          _formatDate(item.date),
                                          style: GoogleFonts.k2d(
                                            fontSize: 14,
                                            color: Colors.deepPurple[300],
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  if (isDeleteMode) ...[
                                    const SizedBox(width: 12),
                                    GestureDetector(
                                      onTap: () =>
                                          _toggleItemSelection(index),
                                      child: Container(
                                        width: 16,
                                        height: 16,
                                        alignment: Alignment.center,
                                        decoration: BoxDecoration(
                                          color: isSelected
                                              ? const Color(0xFF9400FF)
                                              : Colors.transparent,
                                          border: Border.all(
                                            color: isSelected
                                                ? const Color(0xFF9400FF)
                                                : Colors.grey,
                                            width: 2,
                                          ),
                                          borderRadius:
                                              BorderRadius.circular(4),
                                        ),
                                        child: isSelected
                                            ? const Icon(
                                                Icons.check,
                                                color: Colors.white,
                                                size: 12,
                                              )
                                            : null,
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
            ),
            if (isDeleteMode)
              Flexible(
                flex: 2,
                child: Padding(
                  padding: const EdgeInsets.only(top: 0, bottom: 16),
                  child: Center(
                  child: GestureDetector(
                    onTap: selectedIndices.isEmpty ? null : _deleteSelected,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.delete,
                          color: selectedIndices.isEmpty
                              ? Colors.grey[400]
                              : const Color(0xFF27005D),
                          size: 25,
                        ),
                        Text(
                          '삭제',
                          style: TextStyle(
                            fontSize: 13,
                            color: selectedIndices.isEmpty
                                ? Colors.grey[400]
                                : const Color(0xFF27005D),
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
