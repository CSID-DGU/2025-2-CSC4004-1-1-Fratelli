import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:file_picker/file_picker.dart';
import 'package:deepflect_app/widgets/file/upload/file_upload_button.dart';
import 'package:deepflect_app/widgets/file/upload/upload_progress_button.dart';
import 'package:deepflect_app/services/file_service.dart';

class FileUploadPage extends StatefulWidget {
  final VoidCallback? onUploadSuccess;

  const FileUploadPage({super.key, this.onUploadSuccess});

  @override
  State<FileUploadPage> createState() => _FileUploadPageState();
}

class _FileUploadPageState extends State<FileUploadPage> {
  final FileService _fileService = FileService();
  List<Map<String, dynamic>> files = [];
  Timer? _uploadPollTimer;

  String _determineFileType(String fileName) {
    final extension = fileName.toLowerCase().split('.').last;
    const videoExtensions = ['mp4', 'mov', 'mkv', 'avi', 'webm'];
    if (videoExtensions.contains(extension)) {
      return 'VIDEO';
    }
    const imageExtensions = ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp'];
    if (imageExtensions.contains(extension)) {
      return 'IMAGE';
    }
    return 'IMAGE';
  }

  @override
  void initState() {
    super.initState();
    _loadUploadingFiles();
    _uploadPollTimer = Timer.periodic(
      const Duration(seconds: 3),
      (_) => _loadUploadingFiles(),
    );
  }

  @override
  void dispose() {
    _uploadPollTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadUploadingFiles() async {
    try {
      final uploads = await _fileService.getUploadingFiles();

      if (!mounted) return;

      setState(() {
        final List<Map<String, dynamic>> serverFiles = uploads.map((item) {
          final formattedSize = _formatFileSize(item['size']);
          final rawStatus = item['status']?.toString() ?? 'uploading';

          double progress = 0.0;
          if (item['progress'] is num) {
            progress = (item['progress'] as num).clamp(0, 100) / 100.0;
          } else if (rawStatus == 'success') {
            progress = 1.0;
          }

          final String mappedStatus;
          if (rawStatus == 'success') {
            mappedStatus = 'done';
          } else if (rawStatus == 'failed') {
            mappedStatus = 'error';
          } else {
            mappedStatus = 'uploading';
          }

          return {
            "id": item['taskId']?.toString() ?? '',
            "name": item['fileName']?.toString() ?? '',
            "size": formattedSize,
            "progress": progress,
            "progressStatus": item['progressStatus']?.toString(),
            "status": mappedStatus,
            "file": null,
            "fileType": item['fileType']?.toString() ?? 'image',
            "taskId": item['taskId']?.toString(),
            "localId": item['taskId']?.toString(),
          };
        }).toList();

        final serverTaskIds = serverFiles
            .map((e) => e['taskId'].toString())
            .toSet();

        final serverFileNames = serverFiles
            .map((e) => e['name'].toString().trim().toLowerCase())
            .toSet();

        final List<Map<String, dynamic>> keptLocalFiles = [];

        for (final oldFile in files) {
          final oldTaskId = oldFile['taskId']?.toString();
          final oldName = oldFile['name']?.toString().trim().toLowerCase() ?? '';
          
          if (oldTaskId != null && serverTaskIds.contains(oldTaskId)) {
            continue;
          }

          if (serverFileNames.contains(oldName)) {
            continue;
          }

          if (oldTaskId != null && !serverTaskIds.contains(oldTaskId)) {
            if (oldFile['status'] != 'error') {
              keptLocalFiles.add({
                ...oldFile,
                "status": "done",
                "progress": 1.0,
                "progressStatus": null,
              });
            } else {
              keptLocalFiles.add(oldFile);
            }
            continue;
          }

          keptLocalFiles.add(oldFile);
        }

        files = [
          ...serverFiles,      
          ...keptLocalFiles,   
        ];
      });
    } catch (e) {
      if (!mounted) return;
    }
  }

  Future<void> _onFileSelected(List<PlatformFile> selectedFiles) async {
    final List<Map<String, dynamic>> newFiles = [];

    for (var platformFile in selectedFiles) {
      final fileName = platformFile.name;
      final fileSize = "${(platformFile.size / 1024).toStringAsFixed(2)} KB";
      final fileType = _determineFileType(fileName);

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

      final localId =
          'local-${DateTime.now().microsecondsSinceEpoch}-${files.length}-${platformFile.hashCode}';

      newFiles.add({
        "name": fileName,
        "size": fileSize,
        "progress": 0.0,
        "progressStatus": null,
        "status": "uploading",
        "file": file,
        "fileType": fileType,
        "taskId": null,
        "localId": localId,
      });
    }

    if (newFiles.isNotEmpty) {
      setState(() {
        files.addAll(newFiles);
      });

      for (final newFile in newFiles) {
        final file = newFile["file"] as File;
        final fileType = newFile["fileType"] as String;
        final localId = newFile["localId"] as String;
        _uploadFile(localId, file, fileType);
      }
    }
  }

  Future<void> _uploadFile(String localId, File file, String type) async {
    try {
      final response = await _fileService.uploadFile(file, type);

      if (!mounted) return;
      
      final taskId = response['taskId']?.toString();
      
      setState(() {
        final targetIndex =
            files.indexWhere((element) => element["localId"] == localId);
        if (targetIndex != -1 && taskId != null) {
          files[targetIndex]["taskId"] = taskId;
        }
      });

      await _loadUploadingFiles();
      
      widget.onUploadSuccess?.call();
    } catch (e) {
      if (!mounted) return;

      setState(() {
        final targetIndex =
            files.indexWhere((element) => element["localId"] == localId);
        if (targetIndex == -1) return;
        files[targetIndex]["status"] = "error";
        files[targetIndex]["error"] = e.toString().replaceAll('Exception: ', '');
      });

      final failedName = file.path.split('/').last;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('업로드 실패: $failedName\n${e.toString().replaceAll('Exception: ', '')}'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 3),
        ),
      );
    }
  }

  Future<void> _cancelUpload(int index) async {
    final file = files[index];
    final taskId = file["taskId"];

    if (taskId == null) {
      setState(() {
        files.removeAt(index);
      });
      return;
    }

    try {
      await _fileService.cancelUpload(taskId.toString());
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
            content: Text(
              '업로드 취소 실패: ${e.toString().replaceAll('Exception: ', '')}',
            ),
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
    const videoExtensions = ['mp4', 'mov', 'mkv', 'avi', 'webm'];
    if (videoExtensions.contains(extension)) {
      return UploadType.video;
    }
    return UploadType.image;
  }

  String _formatFileSize(dynamic rawSize) {
    if (rawSize == null) return '';

    double? parsedSize;
    if (rawSize is num) {
      parsedSize = rawSize.toDouble();
    } else {
      parsedSize = double.tryParse(rawSize.toString());
    }

    if (parsedSize == null || parsedSize <= 0) return '';

    var sizeValue = parsedSize;

    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    var unitIndex = 0;

    while (sizeValue >= 1024 && unitIndex < units.length - 1) {
      sizeValue /= 1024;
      unitIndex++;
    }

    final fixed = unitIndex == 0 ? 0 : 2;
    return '${sizeValue.toStringAsFixed(fixed)} ${units[unitIndex]}';
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
                "노이즈를 추가할 파일을 업로드해주세요",
                style: GoogleFonts.k2d(
                  fontSize: 14,
                  color: Color(0x6827005D),
                ),
              ),
              const SizedBox(height: 24),
              FileUploadButton(onFilesSelected: _onFileSelected),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: Container(height: 1, color: const Color(0xFFA2A2A2)),
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
                    child: Container(height: 1, color: const Color(0xFFA2A2A2)),
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
                      key: Key(
                        (file["taskId"] ?? file["localId"] ?? '${file["name"]}_$index')
                            .toString(),
                      ),
                      direction: DismissDirection.endToStart,
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
                        progressStatus: file["progressStatus"]?.toString(),
                        status: _convertStatus(file["status"]),
                        type: _determineUploadType(file["name"]),
                        onDownload: () async {
                          final dynamic rawFile = files[index];
                          if (rawFile is! Map<String, dynamic>) {
                            return;
                          }
                          final file = rawFile;
                          final fileData = file["taskId"].toString();
                          String? taskId;
                          try {
                            final Map<String, dynamic> fileDataMap = jsonDecode(
                              fileData,
                            );
                            taskId = fileDataMap["taskId"]?.toString();
                          } catch (e) {
                            taskId = file["taskId"]?.toString();
                          }
                          final status = file["status"]?.toString() ?? '';

                          if (taskId == null || taskId.isEmpty) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('업로드가 완료되지 않아 다운로드할 수 없습니다.'),
                                backgroundColor: Colors.orange,
                              ),
                            );
                            return;
                          }

                          if (status != 'done') {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('파일이 아직 처리 중입니다. (상태: $status)'),
                                backgroundColor: Colors.orange,
                              ),
                            );
                            return;
                          }

                          try {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('${file["name"]} 다운로드를 시작합니다.'),
                                duration: const Duration(seconds: 2),
                              ),
                            );

                            final savedPath = await _fileService.downloadFile(
                              taskId.toString(),
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
                                  content: Text(
                                    '다운로드 실패: ${e.toString().replaceAll('Exception: ', '')}',
                                  ),
                                  backgroundColor: Colors.red,
                                  duration: const Duration(seconds: 3),
                                ),
                              );
                            }
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