import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:flutter/services.dart';

Future<void> downloadFile(String sourcePath, String fileName, BuildContext context) async {
  // 저장소 권한 요청
  var status = await Permission.storage.request();
  if (!status.isGranted) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("저장소 권한이 필요합니다.")),
    );
    return;
  }

  try {
    // Android는 외부 저장소, iOS는 앱 Documents
    Directory directory;
    if (Platform.isAndroid) {
      directory = Directory('/storage/emulated/0/Deepflect');
    } else {
      directory = await getApplicationDocumentsDirectory();
    }

    // 폴더 없으면 생성
    if (!await directory.exists()) {
      await directory.create(recursive: true);
    }

    // 파일 저장
    final File newFile = File('${directory.path}/$fileName');

    if (sourcePath.startsWith('assets/')) {
      // asset 파일
      ByteData data = await rootBundle.load(sourcePath);
      final bytes = data.buffer.asUint8List();
      await newFile.writeAsBytes(bytes);
    } else {
      // 로컬 파일
      await File(sourcePath).copy(newFile.path);
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('파일이 ${directory.path}에 저장되었습니다.')),
    );
  } catch (e) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('다운로드 실패: $e')),
    );
  }
}

