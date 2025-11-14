import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:image_gallery_saver/image_gallery_saver.dart';
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
      // 권한 요청
      PermissionStatus status;
      if (Platform.isAndroid) {
        // Android 13 이상은 사진 권한 사용
        if (await Permission.photos.isGranted) {
          status = PermissionStatus.granted;
        } else {
          status = await Permission.photos.request();
        }
      } else {
        // iOS는 사진 라이브러리 권한 사용
        status = await Permission.photos.request();
      }

      if (!status.isGranted) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("갤러리 접근 권한이 필요합니다.")),
          );
        }
        return;
      }

      // 이미지 파일을 가져오기
      Uint8List imageBytes;
      if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
        // 네트워크 이미지일 경우
        final dio = Dio();
        final response = await dio.get<List<int>>(
          filePath,
          options: Options(responseType: ResponseType.bytes),
        );
        if (response.statusCode == 200 && response.data != null) {
          imageBytes = Uint8List.fromList(response.data!);
        } else {
          throw Exception('이미지를 다운로드할 수 없습니다.');
        }
      } else if (filePath.startsWith('assets/')) {
        // asset 파일일 경우
        ByteData data = await rootBundle.load(filePath);
        imageBytes = data.buffer.asUint8List();
      } else {
        // 로컬 파일일 경우
        File file = File(filePath);
        imageBytes = await file.readAsBytes();
      }

      // 임시 파일 저장 경로 설정
      Directory tempDir;
      if (Platform.isAndroid) {
        // Android의 경우 Pictures/deepflect 폴더에 저장
        tempDir = Directory('/storage/emulated/0/Pictures/deepflect');
      } else {
        // iOS의 경우 임시 디렉토리 사용
        tempDir = await getTemporaryDirectory();
        tempDir = Directory('${tempDir.path}/deepflect');
      }

      // 폴더가 없으면 생성
      if (!await tempDir.exists()) {
        await tempDir.create(recursive: true);
      }

      // 파일 저장
      final String savePath = '${tempDir.path}/$fileName';
      final File saveFile = File(savePath);
      await saveFile.writeAsBytes(imageBytes);

      // 갤러리에 저장 (saveFile은 파일 경로만 받습니다)
      final result = await ImageGallerySaver.saveFile(savePath);

      if (context.mounted) {
        if (result['isSuccess'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('이미지가 갤러리의 deepflect 폴더에 저장되었습니다.'),
              backgroundColor: Colors.green,
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('저장 실패: ${result['errorMessage'] ?? '알 수 없는 오류'}'),
              backgroundColor: Colors.red,
            ),
          );
        }
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
