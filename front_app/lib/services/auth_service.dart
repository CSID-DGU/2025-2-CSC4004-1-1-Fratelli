import 'package:dio/dio.dart';
import 'package:deepflect_app/models/auth/auth.dart';
import 'package:deepflect_app/services/api_service.dart';

class AuthService {
  late final ApiService _apiService;
  
  AuthService() {
    _apiService = ApiService();
  }

  // 로그인
  Future<LoginResponse> login(String email, String password) async {
    try {
      print('로그인 시도: $email');
      
      final response = await _apiService.post(
        '/api/v1/auth/login',
        data: {
          'email': email,
          'password': password,
        },
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        // 서버 응답 구조에 맞게 data 필드에서 추출
        final responseData = response.data;
        if (responseData['success'] == true && responseData['data'] != null) {
          return LoginResponse.fromJson(responseData['data']);
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다.');
        }
      } else {
        throw Exception('로그인 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');
      
      if (e.response?.statusCode == 401) {
        throw Exception('이메일 또는 비밀번호가 올바르지 않습니다.');
      } else if (e.response?.statusCode == 400) {
        throw Exception('입력 정보를 확인해주세요.');
      } else if (e.type == DioExceptionType.connectionTimeout) {
        throw Exception('서버 연결 시간이 초과되었습니다.');
      } else if (e.type == DioExceptionType.receiveTimeout) {
        throw Exception('서버 응답 시간이 초과되었습니다.');
      } else if (e.type == DioExceptionType.connectionError) {
        throw Exception('서버에 연결할 수 없습니다. 네트워크를 확인해주세요.');
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }

  // 사용자 정보 가져오기
  Future<UserInfo> getMe() async {
    try {
      print('사용자 정보 요청');
      
      final response = await _apiService.getWithAuth('/api/v1/auth/me');

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData['success'] == true && responseData['data'] != null) {
          return UserInfo.fromJson(responseData['data']);
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다.');
        }
      } else {
        throw Exception('사용자 정보 조회 실패: ${response.statusMessage}');
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

  // 회원탈퇴
  Future<void> quit(String password) async {
    try {
      print('회원탈퇴 요청');
      
      final response = await _apiService.postWithAuth(
        '/api/v1/auth/quit',
        data: {
          'password': password,
        },
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData['success'] == true) {
          print('회원탈퇴 성공');
        } else {
          throw Exception('회원탈퇴 실패: ${responseData['message']}');
        }
      } else {
        throw Exception('회원탈퇴 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');
      
      if (e.response?.statusCode == 401) {
        throw Exception('비밀번호가 올바르지 않습니다.');
      } else if (e.response?.statusCode == 400) {
        throw Exception('입력 정보를 확인해주세요.');
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }

  // 디바이스 등록
  Future<void> registerDevice(String fcmToken) async {
    try {
      print('디바이스 등록 요청');
      
      final response = await _apiService.postWithAuth(
        '/api/v1/auth/device',
        data: {
          'fcmToken': fcmToken,
        },
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData['success'] == true) {
          print('디바이스 등록 성공');
        } else {
          throw Exception('디바이스 등록 실패: ${responseData['message']}');
        }
      } else {
        throw Exception('디바이스 등록 실패: ${response.statusMessage}');
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

  // 디바이스 삭제
  Future<void> deleteDevice(String fcmToken) async {
    try {
      print('디바이스 삭제 요청');
      
      final response = await _apiService.deleteWithAuth(
        '/api/v1/auth/device',
        data: {
          'fcmToken': fcmToken,
        },
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData['success'] == true) {
          print('디바이스 삭제 성공');
        } else {
          throw Exception('디바이스 삭제 실패: ${responseData['message']}');
        }
      } else {
        throw Exception('디바이스 삭제 실패: ${response.statusMessage}');
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
} 