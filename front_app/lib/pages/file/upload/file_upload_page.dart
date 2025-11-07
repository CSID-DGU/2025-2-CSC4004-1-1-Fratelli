import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:deepflect_app/widgets/file/upload/file_upload_button.dart';
import 'package:deepflect_app/widgets/file/upload/upload_progress_button.dart';
import 'package:deepflect_app/pages/file/upload/file_preview_page.dart';

class FileUploadPage extends StatefulWidget {
  const FileUploadPage({super.key});

  @override
  State<FileUploadPage> createState() => _FileUploadPageState();
}

class _FileUploadPageState extends State<FileUploadPage> {
  List<Map<String, dynamic>> files = [];

  void _onFileSelected(String fileName, String fileSize) {
    setState(() {
      files.add({
        "name": fileName,
        "size": fileSize,
        "progress": 0.0,
        "status": "uploading",
      });
    });

    Future.delayed(const Duration(milliseconds: 500), () {
      _simulateProgress(files.length - 1);
    });
  }

  void _simulateProgress(int index) async {
    for (int i = 1; i <= 10; i++) {
      await Future.delayed(const Duration(milliseconds: 300));
      if (!mounted) return;
      setState(() {
        files[index]["progress"] = i / 10.0;
      });
    }
    // 완료 처리
    setState(() {
      files[index]["status"] =
          (index % 3 == 0) ? "error" : (files[index]["name"].endsWith(".mp4") ? "done" : "done");
    });
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
    if (fileName.endsWith(".mp4")) return UploadType.video;
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
                onFilesSelected: (selectedFiles) {
                  for (var file in selectedFiles) {
                    _onFileSelected(
                      file.name,
                      "${(file.size / 1024).toStringAsFixed(2)} KB",
                    );
                  }
                },
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
                        setState(() {
                          files.removeAt(index);
                        });
                      },
                      child: UploadProgressButton(
                        fileName: file["name"],
                        fileSize: file["size"],
                        progress: file["progress"],
                        status: _convertStatus(file["status"]),
                        type: _determineUploadType(file["name"]),
                        onPreview: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => FilePreviewPage(
                                fileName: file["name"],
                                filePath: "assets/images/${file["name"]}", // 예시 경로
                              ),
                            ),
                          );
                        },
                        onDownload: () {
                          // 영상 다운로드
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('${file["name"]} 다운로드를 시작합니다.'),
                              duration: const Duration(seconds: 2),
                            ),
                          );
                          // TODO: 실제 다운로드 API 호출 구현 필요
                          // 예: ApiService를 통해 서버에서 파일 다운로드 후 로컬 저장
                        },
                        onDelete: () {
                          setState(() {
                            files.removeAt(index);
                          });
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
