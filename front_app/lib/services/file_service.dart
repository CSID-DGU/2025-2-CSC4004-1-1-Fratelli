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
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          file.path,
          filename: fileName,
        ),
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
        if (responseData['success'] == true && responseData['data'] != null) {
          return responseData['data'] as Map<String, dynamic>;
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다.');
        }
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
  Future<List<Map<String, dynamic>>> getUploadingFiles() async {
    try {
      print('업로드 중인 파일 목록 요청');
      
      final response = await _apiService.getWithAuth('/api/v1/files/uploads');

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData['success'] == true && responseData['data'] != null) {
          final List<dynamic> dataList = responseData['data'];
          return dataList.map((item) => item as Map<String, dynamic>).toList();
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

  // 업로드 취소(삭제)
  Future<void> cancelUpload(String tempFileId) async {
    try {
      print('업로드 취소 요청: $tempFileId');
      
      final response = await _apiService.deleteWithAuth(
        '/api/v1/files/uploads/$tempFileId',
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
        if (responseData['success'] == true && responseData['data'] != null) {
          final List<dynamic> dataList = responseData['data'];
          return dataList.map((item) => item as Map<String, dynamic>).toList();
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

  // 결과 미리보기
  Future<Map<String, dynamic>> getPreview(String fileId) async {
    try {
      print('결과 미리보기 요청: $fileId');
      
      final response = await _apiService.getWithAuth(
        '/api/v1/files/$fileId/preview',
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData['success'] == true && responseData['data'] != null) {
          return responseData['data'] as Map<String, dynamic>;
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다.');
        }
      } else {
        throw Exception('미리보기 조회 실패: ${response.statusMessage}');
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

  // 결과 다운로드 URL 가져오기
  Future<String> getDownloadUrl(String fileId) async {
    try {
      print('결과 다운로드 요청: $fileId');
      
      final response = await _apiService.getWithAuth(
        '/api/v1/files/$fileId/download',
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData['success'] == true && responseData['data'] != null) {
          final downloadData = responseData['data'] as Map<String, dynamic>;
          // 다운로드 URL이 있다면 반환
          return downloadData['url'] ?? downloadData['downloadUrl'] ?? '';
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다.');
        }
      } else {
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
  Future<String> downloadFile(String fileId, String fileName) async {
    try {
      // 1. 다운로드 URL 가져오기
      var downloadUrl = await getDownloadUrl(fileId);
      
      if (downloadUrl.isEmpty) {
        throw Exception('다운로드 URL을 가져올 수 없습니다.');
      }

      // 2. 상대 URL인 경우 baseUrl 추가
      if (!downloadUrl.startsWith('http://') && !downloadUrl.startsWith('https://')) {
        String baseUrl = 'http://localhost:3000';
        try {
          final apiHost = dotenv.env['API_HOST'];
          if (apiHost != null && apiHost.isNotEmpty) {
            baseUrl = apiHost;
          }
        } catch (e) {
          print('dotenv 접근 실패, 기본 URL 사용: $e');
        }
        // 상대 URL이 /로 시작하지 않으면 추가
        if (!downloadUrl.startsWith('/')) {
          downloadUrl = '/$downloadUrl';
        }
        downloadUrl = '$baseUrl$downloadUrl';
      }

      // 3. 저장소 권한 요청
      var status = await Permission.storage.request();
      if (!status.isGranted) {
        throw Exception('저장소 권한이 필요합니다.');
      }

      // 4. 저장 디렉토리 설정
      Directory directory;
      if (Platform.isAndroid) {
        directory = Directory('/storage/emulated/0/Deepflect');
      } else {
        directory = await getApplicationDocumentsDirectory();
        directory = Directory('${directory.path}/Deepflect');
      }

      // 5. 폴더가 없으면 생성
      if (!await directory.exists()) {
        await directory.create(recursive: true);
      }

      // 6. 파일 다운로드
      final accessToken = await TokenStorage.getAccessToken();
      final dio = Dio();
      
      final savePath = '${directory.path}/$fileName';

      final response = await dio.download(
        downloadUrl,
        savePath,
        options: Options(
          headers: accessToken != null
              ? {'Authorization': 'Bearer $accessToken'}
              : {},
        ),
      );

      if (response.statusCode == 200) {
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
  Future<void> deleteFile(String fileId) async {
    try {
      print('결과 파일 삭제 요청: $fileId');
      
      final response = await _apiService.deleteWithAuth('/api/v1/files/$fileId');

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
}

