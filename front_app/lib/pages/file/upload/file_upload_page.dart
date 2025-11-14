import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:file_picker/file_picker.dart';
import 'package:deepflect_app/widgets/file/upload/file_upload_button.dart';
import 'package:deepflect_app/widgets/file/upload/upload_progress_button.dart';
import 'package:deepflect_app/pages/file/upload/file_preview_page.dart';
import 'package:deepflect_app/services/file_service.dart';

class FileUploadPage extends StatefulWidget {
  const FileUploadPage({super.key});

  @override
  State<FileUploadPage> createState() => _FileUploadPageState();
}

class _FileUploadPageState extends State<FileUploadPage> {
  final FileService _fileService = FileService();
  List<Map<String, dynamic>> files = [];

  String _determineFileType(String fileName) {
    final extension = fileName.toLowerCase().split('.').last;
    if (extension == 'mp4' || extension == 'mp3') {
      return 'video';
    } else if (extension == 'jpg' || extension == 'jpeg' || extension == 'png') {
      return 'image';
    }
    return 'image'; // 기본값
  }

  Future<void> _onFileSelected(List<PlatformFile> selectedFiles) async {
    for (var platformFile in selectedFiles) {
      final fileName = platformFile.name;
      final fileSize = "${(platformFile.size / 1024).toStringAsFixed(2)} KB";
      final fileType = _determineFileType(fileName);
      
      // 파일이 로컬 경로를 가지고 있는지 확인
      if (platformFile.path == null) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('파일 경로를 가져올 수 없습니다: $fileName'),
              backgroundColor: Colors.red,
            ),
          );
        }
        continue;
      }

      final file = File(platformFile.path!);
      if (!await file.exists()) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('파일을 찾을 수 없습니다: $fileName'),
              backgroundColor: Colors.red,
            ),
          );
        }
        continue;
      }

      final fileIndex = files.length;
      setState(() {
        files.add({
          "name": fileName,
          "size": fileSize,
          "progress": 0.0,
          "status": "uploading",
          "file": file,
          "fileType": fileType,
          "tempFileId": null, // 업로드 시작 후 서버에서 받은 tempFileId
        });
      });

      // 실제 업로드 시작
      _uploadFile(fileIndex, file, fileType);
    }
  }

  Future<void> _uploadFile(int index, File file, String type) async {
    try {
      final response = await _fileService.uploadFile(file, type);
      
      if (!mounted) return;

      setState(() {
        files[index]["tempFileId"] = response['tempFileId'];
        files[index]["status"] = "done";
        files[index]["progress"] = 1.0;
        files[index]["fileId"] = response['fileId'];
      });
    } catch (e) {
      if (!mounted) return;
      
      setState(() {
        files[index]["status"] = "error";
        files[index]["error"] = e.toString().replaceAll('Exception: ', '');
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('업로드 실패: ${files[index]["name"]}\n${files[index]["error"]}'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }

  Future<void> _cancelUpload(int index) async {
    final file = files[index];
    final tempFileId = file["tempFileId"];

    if (tempFileId == null) {
      // 아직 업로드가 시작되지 않았거나 완료된 경우
      setState(() {
        files.removeAt(index);
      });
      return;
    }

    try {
      await _fileService.cancelUpload(tempFileId.toString());
      if (mounted) {
        setState(() {
          files.removeAt(index);
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('업로드가 취소되었습니다.'),
            backgroundColor: Colors.orange,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('업로드 취소 실패: ${e.toString().replaceAll('Exception: ', '')}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  UploadStatus _convertStatus(String status) {
    switch (status) {
      case "uploading":
        return UploadStatus.uploading;
      case "done":
        return UploadStatus.done;
      case "error":
        return UploadStatus.error;
      default:
        return UploadStatus.uploading;
    }
  }

  UploadType _determineUploadType(String fileName) {
    final extension = fileName.toLowerCase().split('.').last;
    if (extension == 'mp4' || extension == 'mp3') return UploadType.video;
    return UploadType.image;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "Deepflect",
                style: GoogleFonts.k2d(
                  fontSize: 26,
                  color: const Color(0xFF1D0523),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                "딥페이크 생성 방지를 위해 노이즈를 추가할 파일을 업로드해주세요",
                style: GoogleFonts.k2d(
                  fontSize: 14,
                  color: const Color(0xFFB3A4CC),
                ),
              ),
              const SizedBox(height: 24),
              FileUploadButton(
                onFilesSelected: _onFileSelected,
              ),
              const SizedBox(height: 24),
              // 작업 목록 구분선 및 제목
              Row(
                children: [
                  Expanded(
                    child: Container(
                      height: 1,
                      color: const Color(0xFFA2A2A2),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text(
                      "작업 목록",
                      style: GoogleFonts.k2d(
                        color: const Color(0xFFA2A2A2),
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Container(
                      height: 1,
                      color: const Color(0xFFA2A2A2),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Expanded(
                child: ListView.builder(
                  itemCount: files.length,
                  itemBuilder: (context, index) {
                    final file = files[index];
                    return Dismissible(
                      key: Key('${file["name"]}_$index'),
                      direction: DismissDirection.endToStart, // 오른쪽에서 왼쪽으로 스와이프
                      background: Container(
                        alignment: Alignment.centerRight,
                        padding: const EdgeInsets.only(right: 20),
                        decoration: BoxDecoration(
                          color: Colors.redAccent,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(
                          Icons.delete_outline,
                          color: Colors.white,
                          size: 28,
                        ),
                      ),
                      onDismissed: (direction) {
                        _cancelUpload(index);
                      },
                      child: UploadProgressButton(
                        fileName: file["name"],
                        fileSize: file["size"],
                        progress: file["progress"],
                        status: _convertStatus(file["status"]),
                        type: _determineUploadType(file["name"]),
                        onPreview: () async {
                          final fileId = file["fileId"];
                          if (fileId != null) {
                            try {
                              final previewData = await _fileService.getPreview(fileId.toString());
                              final previewUrl = previewData['previewUrl']?.toString() ?? 
                                               previewData['url']?.toString() ?? '';
                              
                              if (mounted) {
                                if (previewUrl.isNotEmpty) {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (context) => FilePreviewPage(
                                        fileName: file["name"],
                                        filePath: previewUrl,
                                      ),
                                    ),
                                  );
                                } else {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('미리보기 URL을 가져올 수 없습니다.'),
                                      backgroundColor: Colors.orange,
                                    ),
                                  );
                                }
                              }
                            } catch (e) {
                              if (mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text('미리보기 실패: ${e.toString().replaceAll('Exception: ', '')}'),
                                    backgroundColor: Colors.red,
                                  ),
                                );
                              }
                            }
                          } else {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('파일 미리보기를 사용할 수 없습니다.'),
                                backgroundColor: Colors.orange,
                              ),
                            );
                          }
                        },
                        onDownload: () async {
                          final fileId = file["fileId"];
                          if (fileId != null) {
                            try {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('${file["name"]} 다운로드를 시작합니다.'),
                                  duration: const Duration(seconds: 2),
                                ),
                              );
                              
                              final savedPath = await _fileService.downloadFile(
                                fileId.toString(),
                                file["name"],
                              );
                              
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
                          } else {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('다운로드할 수 없는 파일입니다.'),
                                backgroundColor: Colors.orange,
                              ),
                            );
                          }
                        },
                        onDelete: () {
                          _cancelUpload(index);
                        },
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
