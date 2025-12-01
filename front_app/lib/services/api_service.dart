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

  /// 401/403 등 인증 오류 시 refresh 토큰으로 재발급을 시도하고,
  /// 성공하면 원래 요청을 한 번만 재시도하는 공통 로직
  Future<Response> _requestWithAutoRefresh(
    Future<Response> Function(String accessToken) requestFn, {
    bool retryOnAuthFail = true,
  }) async {
    final accessToken = await TokenStorage.getAccessToken();
    if (accessToken == null) {
      throw Exception('액세스 토큰이 없습니다. 로그인이 필요합니다.');
    }

    try {
      final response = await requestFn(accessToken);

      // 401/403 이 아닌 경우 그대로 반환
      if (response.statusCode != 401 && response.statusCode != 403) {
        return response;
      }

      // 여기까지 왔으면 인증 오류
      if (!retryOnAuthFail) {
        // 이미 한 번 재시도한 후라면 더 이상 재시도하지 않음
        await TokenStorage.deleteTokens();
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다. 다시 로그인해주세요.');
      }
    } on DioException catch (e) {
      // 네트워크 에러인데 401/403 인 경우에만 refresh 시도
      final statusCode = e.response?.statusCode;
      if (statusCode != 401 && statusCode != 403) {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
      if (!retryOnAuthFail) {
        await TokenStorage.deleteTokens();
        throw Exception('접근 권한이 없습니다. 토큰이 만료되었을 수 있습니다. 다시 로그인해주세요.');
      }
    }

    // 여기서부터는 access 토큰 만료로 보고 refresh 토큰 사용
    final refreshToken = await TokenStorage.getRefreshToken();
    if (refreshToken == null) {
      await TokenStorage.deleteTokens();
      throw Exception('리프레시 토큰이 없습니다. 다시 로그인해주세요.');
    }

    try {
      print('리프레시 토큰으로 액세스 토큰 재발급 시도');
      final refreshResponse = await _dio.post(
        '/api/v1/auth/refresh',
        options: Options( headers: {'Authorization': 'Bearer $refreshToken',},),
        // data: {'refreshToken': refreshToken,},
      );

      print('리프레시 응답 상태 코드: ${refreshResponse.statusCode}');
      print('리프레시 응답 데이터: ${refreshResponse.data}');

      if (refreshResponse.statusCode != 200 ||
          refreshResponse.data is! Map<String, dynamic>) {
        throw Exception('토큰 재발급 실패: ${refreshResponse.statusMessage}');
      }

      final Map<String, dynamic> body =
          refreshResponse.data as Map<String, dynamic>;
      final newAccessToken = body['accessToken']?.toString();
      final newRefreshToken = body['refreshToken']?.toString();

      if (newAccessToken == null || newRefreshToken == null) {
        throw Exception('토큰 재발급 응답에 토큰 정보가 없습니다.');
      }

      // 새 토큰 저장
      await TokenStorage.saveTokens(
        accessToken: newAccessToken,
        refreshToken: newRefreshToken,
      );

      // 새 토큰으로 원래 요청 한 번만 재시도
      final retryResponse =
          await _requestWithAutoRefresh(requestFn, retryOnAuthFail: false);
      return retryResponse;
    } on DioException catch (e) {
      print('DioException 발생(리프레시): ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');

      if (e.response?.statusCode == 401) {
        await TokenStorage.deleteTokens();
        throw Exception('리프레시 토큰이 유효하지 않습니다. 다시 로그인해주세요.');
      }
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
    }
  }
  
  // Bearer 토큰 포함 요청
  Future<Response> getWithAuth(String endpoint) async {
    return _requestWithAutoRefresh(
      (accessToken) => _dio.get(
        endpoint,
        options: Options(
          headers: {
            'Authorization': 'Bearer $accessToken',
          },
        ),
      ),
    );
  }

  Future<Response> postWithAuth(String endpoint, {dynamic data, bool isMultipart = false}) async {
    return _requestWithAutoRefresh(
      (accessToken) {
        final headers = <String, dynamic>{
          'Authorization': 'Bearer $accessToken',
        };

        // multipart/form-data 인 경우 서버가 JSON이 아닌 응답(빈 바디, 텍스트 등)을 줄 수 있으므로
        // JSON 파싱 오류(FormatException) 방지를 위해 responseType을 적절히 설정
        if (!isMultipart) {
          headers['Content-Type'] = 'application/json';
        }

        return _dio.post(
          endpoint,
          data: data,
          options: Options(
            headers: headers,
            responseType: isMultipart ? ResponseType.plain : ResponseType.json,
            validateStatus: (status) {
              // 500 이상만 에러로 취급 (나머지는 클라이언트에서 분기)
              return status != null && status < 500;
            },
          ),
        );
      },
    );
  }

  Future<Response> putWithAuth(String endpoint, {dynamic data}) async {
    return _requestWithAutoRefresh(
      (accessToken) => _dio.put(
        endpoint,
        data: data,
        options: Options(
          headers: {
            'Authorization': 'Bearer $accessToken',
          },
        ),
      ),
    );
  }

  Future<Response> patchWithAuth(String endpoint, {dynamic data}) async {
    return _requestWithAutoRefresh(
      (accessToken) => _dio.patch(
        endpoint,
        data: data,
        options: Options(
          headers: {
            'Authorization': 'Bearer $accessToken',
          },
        ),
      ),
    );
  }

  Future<Response> deleteWithAuth(String endpoint, {dynamic data}) async {
    return _requestWithAutoRefresh(
      (accessToken) => _dio.delete(
        endpoint,
        data: data,
        options: Options(
          headers: {
            'Authorization': 'Bearer $accessToken',
          },
        ),
      ),
    );
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
      final isPasswordResetEndpoint = endpoint.contains('/auth/password-reset');
      final response = await _dio.post(
        endpoint,
        data: data,
        options: Options(
          responseType: (isRegisterEndpoint || isPasswordResetEndpoint) 
              ? ResponseType.plain 
              : ResponseType.json,
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
        if (e.response != null && 
            (e.response!.statusCode == 200 || 
             e.response!.statusCode == 201 || 
             e.response!.statusCode == 204)) {
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