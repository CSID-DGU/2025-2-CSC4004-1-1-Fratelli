import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:deepflect_app/services/token_storage.dart';

class ApiService {
  late final Dio _dio;
  
  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: dotenv.env['API_HOST'] ?? 'http://localhost:3000',
      headers: {
        'Content-Type': 'application/json',
      },
      validateStatus: (status) {
        return status != null && status < 500; // 5xx 에러만 자동으로 throw
      },
    ));
  }

  // Bearer 토큰을 포함한 요청
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

  Future<Response> postWithAuth(String endpoint, {dynamic data}) async {
    final accessToken = await TokenStorage.getAccessToken();
    if (accessToken == null) {
      throw Exception('액세스 토큰이 없습니다. 로그인이 필요합니다.');
    }

    try {
      final response = await _dio.post(
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

  // 토큰 없이 요청 (로그인 등)
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
      final response = await _dio.post(endpoint, data: data);
      return response;
    } on DioException catch (e) {
      throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
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