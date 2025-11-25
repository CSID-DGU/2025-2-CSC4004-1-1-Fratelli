import 'package:dio/dio.dart';
import 'package:deepflect_app/services/api_service.dart';
import 'package:deepflect_app/services/token_storage.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';

class FileService {
  late final ApiService _apiService;

  FileService() {
    _apiService = ApiService();
  }

  // 파일 업로드
  Future<Map<String, dynamic>> uploadFile(File file, String type) async {
    try {
      print('파일 업로드 요청: ${file.path}, type: $type');

      final fileName = file.path.split('/').last;
      // 명세: form-data, key: (파일 필드 하나) → 여기서는 'file' 키로 전송
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(file.path, filename: fileName),
      });

      final response = await _apiService.postWithAuth(
        '/api/v1/files/uploads?type=$type',
        data: formData,
        isMultipart: true,
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200 || response.statusCode == 201) {
        final responseData = response.data;
        // 명세(최신):
        // FileUploadResponse {
        //   "taskId": "f_67890",
        //   "fileName": "video1.mp4",
        //   "fileType": "video",
        //   "size": 10485760, // 바이트
        //   "status": "uploading",
        //   "timestamp": "2025-10-09T12:00:00Z"
        // }
        if (responseData is Map<String, dynamic>) {
          return responseData;
        }

        // 서버가 200/201 이고 body에 UUID 문자열만 내려주는 경우
        if (responseData is String && responseData.trim().isNotEmpty) {
          final taskId = responseData.trim();
          return {
            'taskId': taskId,
            'fileName': fileName,
            'fileType': type,
            'status': 'uploading',
          };
        }

        // 그 외(JSON 바디가 없거나 예기치 못한 형식)
        return {'success': true, 'rawResponse': responseData};
      } else {
        throw Exception('파일 업로드 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');

      if (e.response?.statusCode == 401) {
        throw Exception('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else if (e.response?.statusCode == 400) {
        throw Exception('파일 형식이 올바르지 않습니다.');
      } else if (e.response?.statusCode == 413) {
        throw Exception('파일 크기가 너무 큽니다.');
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }

  // 업로드 중인 파일 목록
  Future<List<Map<String, dynamic>>> getUploadingFiles({String? type}) async {
    try {
      print('업로드 중인 파일 목록 요청, type: $type');

      final endpoint = type != null
          ? '/api/v1/files/uploads?type=$type'
          : '/api/v1/files/uploads';

      final response = await _apiService.getWithAuth(endpoint);

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        // 명세(최신):
        // {
        //   "uploads": [
        //     {
        //       "taskId": "f_67890",
        //       "fileName": "video1.mp4",
        //       "fileType": "video",
        //       "status": "uploading",
        //       "timestamp": "2025-10-09T12:00:00Z"
        //     },
        //     ...
        //   ]
        // }
        if (responseData is Map<String, dynamic> &&
            responseData['uploads'] is List) {
          final List<dynamic> uploads =
              responseData['uploads'] as List<dynamic>;
          return uploads
              .where((item) => item is Map<String, dynamic>)
              .map((item) => item as Map<String, dynamic>)
              .toList();
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다.');
        }
      } else {
        throw Exception('파일 목록 조회 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');

      if (e.response?.statusCode == 401) {
        throw Exception('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }

  // 업로드 취소(삭제) - taskId 기준
  Future<void> cancelUpload(String taskId) async {
    try {
      print('업로드 취소 요청: $taskId');

      final response = await _apiService.deleteWithAuth(
        '/api/v1/files/uploads/$taskId',
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        print('업로드 취소 성공');
      } else {
        throw Exception('업로드 취소 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');

      if (e.response?.statusCode == 401) {
        throw Exception('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else if (e.response?.statusCode == 404) {
        throw Exception('파일을 찾을 수 없습니다.');
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }

  // 전체 결과 목록
  Future<List<Map<String, dynamic>>> getFiles({String? type}) async {
    try {
      print('전체 결과 목록 요청, type: $type');

      final endpoint = type != null
          ? '/api/v1/files?type=$type'
          : '/api/v1/files';

      final response = await _apiService.getWithAuth(endpoint);

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        // 명세(최신):
        // FileListResponse {
        //   "files": [
        //     {
        //       "taskId": "f_67890",
        //       "fileName": "video1.mp4",
        //       "fileType": "video",
        //       "size": 10485760,
        //       "url": "https://...",
        //       "timestamp": "2025-10-09T12:05:00Z"
        //     },
        //     ...
        //   ]
        // }
        if (responseData is Map<String, dynamic> &&
            responseData['files'] is List) {
          final List<dynamic> files = responseData['files'] as List<dynamic>;
          return files
              .where((item) => item is Map<String, dynamic>)
              .map((item) => item as Map<String, dynamic>)
              .toList();
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다.');
        }
      } else {
        throw Exception('파일 목록 조회 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');

      if (e.response?.statusCode == 401) {
        throw Exception('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }

  // 결과 다운로드 URL 가져오기
  Future<String> getDownloadUrl(String taskId) async {
    try {
      print('결과 다운로드 요청: $taskId');

      final response = await _apiService.getWithAuth(
        '/api/v1/files/$taskId/download',
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData is Map<String, dynamic>) {
          // 여러 가능한 필드명 확인
          final url = responseData['downloadUrl'];
          if (url != null && url.isNotEmpty) {
            print('다운로드 URL 획득: $url');
            return url;
          } else {
            print('다운로드 URL 필드를 찾을 수 없습니다. 응답 데이터: $responseData');
            throw Exception('다운로드 URL이 응답에 없습니다. 파일이 아직 처리 중일 수 있습니다.');
          }
        } else {
          print(
            '서버 응답이 Map이 아닙니다. 타입: ${responseData.runtimeType}, 데이터: $responseData',
          );
          throw Exception('서버 응답 형식이 올바르지 않습니다.');
        }
      } else {
        print(
          '다운로드 URL 요청 실패: 상태 코드 ${response.statusCode}, 메시지: ${response.statusMessage}',
        );
        throw Exception('다운로드 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');

      if (e.response?.statusCode == 401) {
        throw Exception('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else if (e.response?.statusCode == 404) {
        throw Exception('파일을 찾을 수 없습니다.');
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }

  // 결과 파일 다운로드 및 저장
  Future<String> downloadFile(String taskId, String fileName) async {
    try {
      print('파일 다운로드 시작: taskId=$taskId, fileName=$fileName');

      // 다운로드 URL 가져오기
      var downloadUrl = await getDownloadUrl(taskId);

      if (downloadUrl.isEmpty) {
        throw Exception('다운로드 URL을 가져올 수 없습니다.');
      }

      print('다운로드 URL (원본): $downloadUrl');

      // 상대 URL 처리
      if (!downloadUrl.startsWith('http://') &&
          !downloadUrl.startsWith('https://')) {
        String baseUrl = 'http://localhost:8080';
        try {
          final apiHost = dotenv.env['API_HOST'];
          if (apiHost != null && apiHost.isNotEmpty) {
            baseUrl = apiHost;
            print('환경 변수에서 API 호스트 로드: $baseUrl');
          }
        } catch (e) {
          print('dotenv 접근 실패, 기본 URL 사용: $e');
        }
        if (!downloadUrl.startsWith('/')) {
          downloadUrl = '/$downloadUrl';
        }
        downloadUrl = '$baseUrl$downloadUrl';
        print('다운로드 URL (절대 경로): $downloadUrl');
      }

      // 저장소 권한 요청
      var status = await _ensureStoragePermission();
      print('저장소 권한 상태: $status');
      if (!status) {
        throw Exception('저장소 권한이 필요합니다.');
      }

      // 저장 디렉토리 설정
      Directory directory;
      if (Platform.isAndroid) {
        directory = Directory('/storage/emulated/0/Deepflect');
      } else {
        directory = await getApplicationDocumentsDirectory();
        directory = Directory('${directory.path}/Deepflect');
      }

      // 폴더가 없으면 생성
      if (!await directory.exists()) {
        await directory.create(recursive: true);
      }

      // 파일 다운로드
      final accessToken = await TokenStorage.getAccessToken();
      final dio = Dio();

      final savePath = '${directory.path}/$fileName';
      print('파일 저장 경로: $savePath');

      print('파일 다운로드 요청 시작: $downloadUrl');
      final response = await dio.download(
        downloadUrl,
        savePath,
        options: Options(
          headers: accessToken != null
              ? {'Authorization': 'Bearer $accessToken'}
              : {},
        ),
        onReceiveProgress: (received, total) {
          if (total != -1) {
            final progress = (received / total * 100).toStringAsFixed(1);
            print('다운로드 진행률: $progress% ($received/$total bytes)');
          }
        },
      );

      print('다운로드 응답 상태 코드: ${response.statusCode}');
      if (response.statusCode == 200) {
        print('파일 다운로드 성공: $savePath');
        return savePath;
      } else {
        throw Exception('파일 다운로드 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('파일 다운로드 중 오류가 발생했습니다: $e');
    }
  }

  // 결과 파일 삭제
  Future<void> deleteFile(String taskId) async {
    try {
      print('결과 파일 삭제 요청: $taskId');

      final response = await _apiService.deleteWithAuth(
        '/api/v1/files/$taskId',
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        print('파일 삭제 성공');
      } else {
        throw Exception('파일 삭제 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');

      if (e.response?.statusCode == 401) {
        throw Exception('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else if (e.response?.statusCode == 404) {
        throw Exception('파일을 찾을 수 없습니다.');
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }

  Future<bool> _ensureStoragePermission() async {
    if (Platform.isAndroid) {
      if (Platform.version.compareTo('33') >= 0) {
        final photos = await Permission.photos.request();
        final videos = await Permission.videos.request();
        final audio = await Permission.audio.request();
        return photos.isGranted || videos.isGranted || audio.isGranted;
      } else {
        var status = await Permission.storage.request();
        if (status.isDenied &&
            await Permission.manageExternalStorage.isDenied) {
          status = await Permission.manageExternalStorage.request();
        }
        return status.isGranted ||
            await Permission.manageExternalStorage.isGranted;
      }
    }
    final status = await Permission.storage.request();
    return status.isGranted;
  }
}
