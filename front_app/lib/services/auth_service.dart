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
        final responseData = response.data;
        if (responseData is Map<String, dynamic>) {
          // userInfo가 없을 수 있으므로 처리
          final loginResponse = LoginResponse.fromJson(responseData);
          // userInfo가 없으면 이메일로부터 생성 (JWT 토큰에서 이메일 추출 가능하지만, 일단 null 허용)
          return loginResponse;
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다. (JSON 객체 아님)');
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

  // 회원가입
  Future<void> register(String email, String password) async {
    try {
      print('회원가입 시도: $email');
      print('회원가입 엔드포인트: /api/v1/auth/register');
      print('요청 데이터: {email: $email, password: [비밀번호 숨김]}');
      
      final response = await _apiService.post(
        '/api/v1/auth/register',
        data: {
          'email': email,
          'password': password,
        },
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터 타입: ${response.data.runtimeType}');
      print('응답 데이터: ${response.data}');

      // 회원가입 성공
      if (response.statusCode == 200 || response.statusCode == 201) {
        print('회원가입 성공 (바디 없음, 상태 코드로만 확인)');
        return;
      } else {
        final responseData = response.data;
        String errorMessage;
        
        if (responseData == null || responseData == '' || (responseData is String && responseData.trim().isEmpty)) {
          errorMessage = response.statusMessage ?? '알 수 없는 오류';
        } else if (responseData is Map) {
          errorMessage = responseData['message'] ?? 
                        responseData['error'] ?? 
                        responseData['msg'] ??
                        response.statusMessage ?? 
                        '알 수 없는 오류';
        } else if (responseData is String && responseData.isNotEmpty) {
          errorMessage = responseData;
        } else {
          errorMessage = response.statusMessage ?? '알 수 없는 오류';
        }
        
        print('회원가입 실패 - 상태 코드: ${response.statusCode}, 메시지: $errorMessage, 응답: $responseData');
        
        // 상태 코드별 에러 메시지
        if (response.statusCode == 400) {
          throw Exception('입력 정보를 확인해주세요. $errorMessage');
        } else if (response.statusCode == 403) {
          // 403 에러일 때 이메일 중복 메시지 확인
          final lowerErrorMsg = errorMessage.toLowerCase();
          if (lowerErrorMsg.contains('email') || 
              lowerErrorMsg.contains('이메일') || 
              lowerErrorMsg.contains('exist') || 
              lowerErrorMsg.contains('already') ||
              lowerErrorMsg.contains('중복') ||
              lowerErrorMsg.contains('존재')) {
            throw Exception('이미 존재하는 이메일입니다.');
          }
          throw Exception('접근 권한이 없습니다. $errorMessage');
        } else if (response.statusCode == 409) {
          throw Exception('이미 존재하는 이메일입니다.');
        } else {
          throw Exception('회원가입 실패 (${response.statusCode}): $errorMessage');
        }
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('에러 전체: ${e.toString()}');
      print('요청 URI: ${e.requestOptions.uri}');
      if (e.error != null) {
        print('에러 객체: ${e.error}');
        print('에러 객체 타입: ${e.error.runtimeType}');
      }
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');
      
      if (e.response?.statusCode == 400) {
        final responseData = e.response?.data;
        final errorMsg = responseData is Map 
            ? (responseData['message'] ?? responseData['error'] ?? '입력 정보를 확인해주세요.')
            : '입력 정보를 확인해주세요.';
        throw Exception(errorMsg);
      } else if (e.response?.statusCode == 403) {
        final responseData = e.response?.data;
        String errorMsg;
        if (responseData is Map) {
          errorMsg = responseData['message'] ?? 
                    responseData['error'] ?? 
                    responseData['msg'] ??
                    '접근 권한이 없습니다.';
        } else if (responseData is String && responseData.isNotEmpty) {
          errorMsg = responseData;
        } else {
          errorMsg = '접근 권한이 없습니다.';
        }
        
        // 403 에러일 때 이메일 중복 메시지 확인
        final lowerErrorMsg = errorMsg.toLowerCase();
        if (lowerErrorMsg.contains('email') || 
            lowerErrorMsg.contains('이메일') || 
            lowerErrorMsg.contains('exist') || 
            lowerErrorMsg.contains('already') ||
            lowerErrorMsg.contains('중복') ||
            lowerErrorMsg.contains('존재')) {
          throw Exception('이미 존재하는 이메일입니다.');
        }
        throw Exception(errorMsg);
      } else if (e.response?.statusCode == 409) {
        throw Exception('이미 존재하는 이메일입니다.');
      } else if (e.type == DioExceptionType.connectionTimeout) {
        throw Exception('서버 연결 시간이 초과되었습니다.');
      } else if (e.type == DioExceptionType.receiveTimeout) {
        throw Exception('서버 응답 시간이 초과되었습니다.');
      } else if (e.type == DioExceptionType.connectionError) {
        throw Exception('서버에 연결할 수 없습니다. 네트워크를 확인해주세요.');
      } else if (e.type == DioExceptionType.unknown) {
        String errorMsg = '서버에 연결할 수 없습니다. ';
        if (e.error != null) {
          errorMsg += '오류: ${e.error}';
        } else {
          errorMsg += '서버가 실행 중인지 확인해주세요.';
        }
        throw Exception(errorMsg);
      } else {
        throw Exception('네트워크 오류가 발생했습니다: ${e.message ?? e.toString()}');
      }
    } catch (e) {
      print('일반 Exception 발생: $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }

  // 로그아웃
  Future<void> logout() async {
    try {
      print('로그아웃 요청');
      
      final response = await _apiService.postWithAuth('/api/v1/auth/logout');

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData is Map<String, dynamic>) {
          final message = responseData['message']?.toString() ?? '';
          if (message.toLowerCase().contains('success')) {
            print('로그아웃 성공: $message');
            return;
          } else {
            throw Exception('로그아웃 실패: $message');
          }
        } else {
          print('로그아웃 성공');
          return;
        }
      } else {
        throw Exception('로그아웃 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');
      
      if (e.response?.statusCode == 401) {
        throw Exception('인증이 만료되었습니다.');
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
      
      final response = await _apiService.getWithAuth('/api/v1/auth/user');

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

  // 회원 정보 수정
  Future<UserInfo> updateUser(Map<String, dynamic> userData) async {
    try {
      print('회원 정보 수정 요청');
      
      final response = await _apiService.patchWithAuth(
        '/api/v1/auth/user',
        data: userData,
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData is Map<String, dynamic> &&
            responseData['email'] is String) {
          return UserInfo(
            id: 0,
            email: responseData['email'] as String,
          );
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다.');
        }
      } else {
        throw Exception('회원 정보 수정 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');
      
      if (e.response?.statusCode == 401) {
        throw Exception('인증이 만료되었습니다. 다시 로그인해주세요.');
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

  // 회원탈퇴
  Future<void> quit() async {
    try {
      print('회원탈퇴 요청');
      
      final makeRequest = () async {
        return await _apiService.deleteWithAuth('/api/v1/auth/quit');
      };
      
      var response = await makeRequest();
      
      // 401 에러 시 토큰 갱신 후 재시도
      if (response.statusCode == 401) {
        try {
          // ApiService의 _requestWithAutoRefresh가 자동으로 토큰 갱신을 시도하지만,
          // 명시적으로 재시도하기 위해 다시 호출
          response = await makeRequest();
        } catch (e) {
          // 토큰 갱신 실패 시 예외를 다시 던짐
          rethrow;
        }
      }

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        print('회원탈퇴 성공');
        return;
      } else {
        throw Exception('회원탈퇴 실패: ${response.statusMessage}');
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
        print('디바이스 삭제 성공');
        return;
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
  // 비밀번호 재설정 요청
  Future<void> passwordReset(String email) async {
    try {
      print('비밀번호 재설정 요청: $email');

      final response = await _apiService.post(
        '/api/v1/auth/password-reset',
        data: {
          'email': email,
        },
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200 || response.statusCode == 204) {
        print('비밀번호 재설정 메일 전송 성공');
        return;
      } else {
        final responseData = response.data;
        String errorMessage;

        if (responseData is Map) {
          errorMessage = responseData['message'] ??
              responseData['error'] ??
              response.statusMessage ??
              '알 수 없는 오류';
        } else if (responseData is String && responseData.isNotEmpty) {
          errorMessage = responseData;
        } else {
          errorMessage = response.statusMessage ?? '알 수 없는 오류';
        }

        throw Exception(
            '비밀번호 재설정 요청 실패 (${response.statusCode}): $errorMessage');
      }
    } on DioException catch (e) {
      print('DioException 발생: ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');

      if (e.type == DioExceptionType.connectionTimeout) {
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

  // 리프레시 토큰으로 토큰 재발급
  Future<LoginResponse> refreshAccessToken(String refreshToken) async {
    try {
      print('리프레시 토큰으로 재발급 시도');

      final response = await _apiService.post(
        '/api/v1/auth/refresh',
        data: {
          'refreshToken': refreshToken,
        },
      );

      print('응답 상태 코드: ${response.statusCode}');
      print('응답 데이터: ${response.data}');

      if (response.statusCode == 200) {
        final responseData = response.data;
        if (responseData is Map<String, dynamic>) {
          return LoginResponse.fromJson(responseData);
        } else {
          throw Exception('서버 응답 형식이 올바르지 않습니다. (JSON 객체 아님)');
        }
      } else {
        throw Exception('토큰 재발급 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      print('DioException 발생(리프레시): ${e.type}');
      print('에러 메시지: ${e.message}');
      print('응답 데이터: ${e.response?.data}');
      print('상태 코드: ${e.response?.statusCode}');

      if (e.response?.statusCode == 401) {
        throw Exception('리프레시 토큰이 유효하지 않습니다. 다시 로그인해주세요.');
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
      print('일반 Exception 발생(리프레시): $e');
      throw Exception('알 수 없는 오류가 발생했습니다: $e');
    }
  }
}