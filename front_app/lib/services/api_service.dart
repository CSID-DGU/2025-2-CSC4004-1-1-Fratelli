import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter/foundation.dart';
import 'package:deepflect_app/services/token_storage.dart';

class ApiService {
  late final Dio _dio;
  
  ApiService() {
    String baseUrl = kDebugMode 
        ? (defaultTargetPlatform == TargetPlatform.android 
            ? 'http://10.0.2.2:8080'  // Android 에뮬레이터용
            : 'http://localhost:8080')  // iOS/웹/데스크톱용
        : 'http://localhost:8080';
    
    try {
      final apiHost = dotenv.env['API_HOST'];
      if (apiHost != null && apiHost.isNotEmpty) {
        baseUrl = apiHost;
        print('환경 변수에서 API 호스트 로드: $baseUrl');
      } else {
        print('기본 API 호스트 사용: $baseUrl');
      }
    } catch (e) {
      print('dotenv 접근 실패, 기본 URL 사용: $baseUrl ($e)');
    }
    
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      sendTimeout: const Duration(seconds: 10),
      validateStatus: (status) {
        return status != null && status < 500; 
      },
    ));
    
    // 요청/응답 인터셉터 (디버깅용)
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        print('=== 요청 인터셉터 ===');
        print('URL: ${options.uri}');
        print('Method: ${options.method}');
        print('Headers: ${options.headers}');
        print('Data: ${options.data}');
        return handler.next(options);
      },
      onResponse: (response, handler) {
        print('=== 응답 인터셉터 ===');
        print('Status: ${response.statusCode}');
        print('Headers: ${response.headers}');
        print('Data: ${response.data}');
        return handler.next(response);
      },
      onError: (error, handler) {
        print('=== 에러 인터셉터 ===');
        print('Error Type: ${error.type}');
        print('Error Message: ${error.message}');
        print('Error: ${error.toString()}');
        print('Request Options: ${error.requestOptions.uri}');
        print('Request Method: ${error.requestOptions.method}');
        print('Request Headers: ${error.requestOptions.headers}');
        print('Request Data: ${error.requestOptions.data}');
        print('Response: ${error.response?.data}');
        print('Status: ${error.response?.statusCode}');
        if (error.error != null) {
          print('Error Object: ${error.error}');
          print('Error Object Type: ${error.error.runtimeType}');
        }
        return handler.next(error);
      },
    ));
  }

  // Bearer 토큰 포함 요청
  Future<Response> getWithAuth(String endpoint) async {
    final accessToken = await TokenStorage.getAccessToken();
    if (accessToken == null) {
      throw Exception('액세스 토큰이 없습니다. 로그인이 필요합니다.');
    }

    try {
      final response = await _dio.get(
        endpoint,
        options: Options(
          headers: {
            'Authorization': 'Bearer $accessToken',
          },
        ),
      );
      
      if (response.statusCode == 403) {
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다.');
      }
      
      return response;
    } on DioException catch (e) {
      if (e.response?.statusCode == 403) {
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다.');
      }
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
    }
  }

  Future<Response> postWithAuth(String endpoint, {dynamic data, bool isMultipart = false}) async {
    final accessToken = await TokenStorage.getAccessToken();
    if (accessToken == null) {
      throw Exception('액세스 토큰이 없습니다. 로그인이 필요합니다.');
    }

    try {
      final headers = <String, dynamic>{
        'Authorization': 'Bearer $accessToken',
      };
      
      // multipart/form-data인 경우
      if (!isMultipart) {
        headers['Content-Type'] = 'application/json';
      }

      final response = await _dio.post(
        endpoint,
        data: data,
        options: Options(
          headers: headers,
        ),
      );
      
      if (response.statusCode == 403) {
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다.');
      }
      
      return response;
    } on DioException catch (e) {
      if (e.response?.statusCode == 403) {
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다.');
      }
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
    }
  }

  Future<Response> putWithAuth(String endpoint, {dynamic data}) async {
    final accessToken = await TokenStorage.getAccessToken();
    if (accessToken == null) {
      throw Exception('액세스 토큰이 없습니다. 로그인이 필요합니다.');
    }

    try {
      final response = await _dio.put(
        endpoint,
        data: data,
        options: Options(
          headers: {
            'Authorization': 'Bearer $accessToken',
          },
        ),
      );
      
      if (response.statusCode == 403) {
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다.');
      }
      
      return response;
    } on DioException catch (e) {
      if (e.response?.statusCode == 403) {
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다.');
      }
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
    }
  }

  Future<Response> patchWithAuth(String endpoint, {dynamic data}) async {
    final accessToken = await TokenStorage.getAccessToken();
    if (accessToken == null) {
      throw Exception('액세스 토큰이 없습니다. 로그인이 필요합니다.');
    }

    try {
      final response = await _dio.patch(
        endpoint,
        data: data,
        options: Options(
          headers: {
            'Authorization': 'Bearer $accessToken',
          },
        ),
      );
      
      if (response.statusCode == 403) {
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다.');
      }
      
      return response;
    } on DioException catch (e) {
      if (e.response?.statusCode == 403) {
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다.');
      }
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
    }
  }

  Future<Response> deleteWithAuth(String endpoint, {dynamic data}) async {
    final accessToken = await TokenStorage.getAccessToken();
    if (accessToken == null) {
      throw Exception('액세스 토큰이 없습니다. 로그인이 필요합니다.');
    }

    try {
      final response = await _dio.delete(
        endpoint,
        data: data,
        options: Options(
          headers: {
            'Authorization': 'Bearer $accessToken',
          },
        ),
      );
      
      if (response.statusCode == 403) {
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다.');
      }
      
      return response;
    } on DioException catch (e) {
      if (e.response?.statusCode == 403) {
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다.');
      }
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
    }
  }

  // 토큰 없이 요청
  Future<Response> get(String endpoint) async {
    try {
      final response = await _dio.get(endpoint);
      
      if (response.statusCode == 404) {
        throw Exception('요청한 리소스를 찾을 수 없습니다.');
      }
      
      return response;
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) {
        throw Exception('요청한 리소스를 찾을 수 없습니다.');
      }
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
    }
  }

  Future<Response> post(String endpoint, {dynamic data}) async {
    try {
      print('POST 요청: ${_dio.options.baseUrl}$endpoint');
      print('요청 데이터: $data');
      
      final isRegisterEndpoint = endpoint.contains('/auth/register');
      final response = await _dio.post(
        endpoint,
        data: data,
        options: Options(
          responseType: isRegisterEndpoint ? ResponseType.plain : ResponseType.json,
          validateStatus: (status) {
            return status != null && status < 500;
          },
        ),
      );
      
      print('응답 상태: ${response.statusCode}');
      print('응답 헤더: ${response.headers}');
      print('응답 데이터 타입: ${response.data.runtimeType}');
      print('응답 데이터: ${response.data}');
      
      return response;
    } on DioException catch (e) {
      print('POST 요청 실패: ${_dio.options.baseUrl}$endpoint');
      print('에러 타입: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('에러 전체: ${e.toString()}');
      print('요청 URI: ${e.requestOptions.uri}');
      print('요청 메서드: ${e.requestOptions.method}');
      if (e.error != null) {
        print('에러 객체: ${e.error}');
        print('에러 객체 타입: ${e.error.runtimeType}');
      }
      print('응답 데이터: ${e.response?.data}');
      print('응답 상태 코드: ${e.response?.statusCode}');
      
      if (e.type == DioExceptionType.unknown && e.error is FormatException) {
        if (e.response != null && (e.response!.statusCode == 200 || e.response!.statusCode == 201)) {
          return e.response!;
        }
        throw Exception('서버 응답 형식 오류: ${e.error}');
      }
      
      if (e.type == DioExceptionType.unknown) {
        String errorMsg = '서버에 연결할 수 없습니다. ';
        if (e.error != null) {
          errorMsg += '오류: ${e.error}';
        } else {
          errorMsg += '서버가 실행 중인지 확인해주세요. (${_dio.options.baseUrl})';
        }
        throw Exception(errorMsg);
      }
      
      throw Exception('네트워크 오류가 발생했습니다: ${e.message ?? e.toString()}');
    }
  }

  Future<Response> put(String endpoint, {dynamic data}) async {
    try {
      final response = await _dio.put(endpoint, data: data);
      return response;
    } on DioException catch (e) {
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
    }
  }

  Future<Response> delete(String endpoint) async {
    try {
      final response = await _dio.delete(endpoint);
      return response;
    } on DioException catch (e) {
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
    }
  }
} 