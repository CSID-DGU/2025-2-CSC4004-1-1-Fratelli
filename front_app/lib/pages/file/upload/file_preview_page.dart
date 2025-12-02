import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:gal/gal.dart';
import 'package:dio/dio.dart';

class FilePreviewPage extends StatelessWidget {
  final String fileName;
  final String filePath; // 로컬 파일 경로나 asset 경로

  const FilePreviewPage({
    super.key,
    required this.fileName,
    required this.filePath,
  });

  Future<void> _downloadImage(BuildContext context) async {
    try {
      // 권한 확인 및 요청
      if (!await Gal.hasAccess()) {
        await Gal.requestAccess();
        if (!await Gal.hasAccess()) {
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text("갤러리 접근 권한이 필요합니다.")),
            );
          }
          return;
        }
      }

      // 이미지 파일 경로 준비
      String imagePath;
      if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
        // 네트워크 이미지일 경우 다운로드
        final dio = Dio();
        final tempDir = await getTemporaryDirectory();
        final String downloadPath = '${tempDir.path}/$fileName';
        await dio.download(filePath, downloadPath);
        imagePath = downloadPath;
      } else if (filePath.startsWith('assets/')) {
        // asset 파일일 경우 임시 파일로 복사
        ByteData data = await rootBundle.load(filePath);
        final Uint8List imageBytes = data.buffer.asUint8List();
        final tempDir = await getTemporaryDirectory();
        final String tempPath = '${tempDir.path}/$fileName';
        final File tempFile = File(tempPath);
        await tempFile.writeAsBytes(imageBytes);
        imagePath = tempPath;
      } else {
        // 로컬 파일일 경우 그대로 사용
        imagePath = filePath;
      }

      // gal을 사용하여 갤러리에 저장
      await Gal.putImage(imagePath);

      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('이미지가 갤러리에 저장되었습니다.'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } on GalException catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('저장 실패: ${e.type.message}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('다운로드 실패: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Widget _buildImageWidget() {
    if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
      // 네트워크 이미지
      return Image.network(
        filePath,
        fit: BoxFit.contain,
        errorBuilder: (context, error, stackTrace) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline, size: 48, color: Colors.red),
                SizedBox(height: 16),
                Text('이미지를 불러올 수 없습니다.'),
              ],
            ),
          );
        },
        loadingBuilder: (context, child, loadingProgress) {
          if (loadingProgress == null) return child;
          return const Center(
            child: CircularProgressIndicator(),
          );
        },
      );
    } else if (filePath.startsWith('assets/')) {
      // Asset 이미지
      return Image.asset(
        filePath,
        fit: BoxFit.contain,
      );
    } else if (filePath.isNotEmpty) {
      // 로컬 파일
      return Image.file(
        File(filePath),
        fit: BoxFit.contain,
        errorBuilder: (context, error, stackTrace) {
          return const Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline, size: 48, color: Colors.red),
                SizedBox(height: 16),
                Text('파일을 불러올 수 없습니다.'),
              ],
            ),
          );
        },
      );
    } else {
      // 빈 경로
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.image_not_supported, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text('미리보기를 사용할 수 없습니다.'),
          ],
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(fileName, style: const TextStyle(color: Colors.black)),
        centerTitle: false,
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Navigator.pop(context), // 뒤로가기
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.download_outlined, color: Colors.deepPurple),
            onPressed: () => _downloadImage(context),
          )
        ],
      ),
      body: Center(
        child: _buildImageWidget(),
      ),
    );
  }
}
