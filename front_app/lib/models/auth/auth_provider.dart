import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:deepflect_app/models/auth/auth.dart';
import 'package:deepflect_app/services/auth_service.dart';
import 'package:deepflect_app/services/token_storage.dart';
import 'package:deepflect_app/services/fcm_service.dart';

part 'auth_provider.g.dart';

@riverpod
class AuthNotifier extends _$AuthNotifier {
  late final AuthService _authService;

  @override
  AuthState build() {
    _authService = AuthService();
    Future.microtask(() => _checkAuthStatus());
    return const AuthState();
  }

  // 토큰 확인
  Future<void> _checkAuthStatus() async {
    final hasTokens = await TokenStorage.hasTokens();
    if (hasTokens) {
      final accessToken = await TokenStorage.getAccessToken();
      final refreshToken = await TokenStorage.getRefreshToken();
      state = state.copyWith(
        isAuthenticated: true,
        accessToken: accessToken,
        refreshToken: refreshToken,
      );
    }
  }

  // 회원가입
  Future<void> register(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      await _authService.register(email, password);

      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString().replaceAll('Exception: ', ''),
      );
      rethrow; 
    }
  }

  // 비밀번호 초기화
  Future<void> passwordReset(String email) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      await _authService.passwordReset(email);
      state = state.copyWith(isLoading: false);
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString().replaceAll('Exception: ', ''),
      );
      rethrow;
    }
  }

  // 로그인
  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      final loginResponse = await _authService.login(email, password);
      
        await TokenStorage.saveTokens(
          accessToken: loginResponse.accessToken,
          refreshToken: loginResponse.refreshToken,
        );
      
      final fcmToken = await FcmService.getFcmToken();
      if (fcmToken != null) {
        try {
          await _authService.registerDevice(fcmToken);
          print('FCM 토큰 등록 성공');
        } catch (e) {
          print('FCM 토큰 등록 실패: $e');
        }
      }
      
      state = state.copyWith(
        isLoading: false,
        isAuthenticated: true,
        accessToken: loginResponse.accessToken,
        refreshToken: loginResponse.refreshToken,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString().replaceAll('Exception: ', ''),
      );
    }
  }

  // 로그아웃 처리
  Future<void> logout() async {
    try {
      try {
        await _authService.logout();
        print('로그아웃 API 호출 성공');
      } catch (e) {
        print('로그아웃 API 호출 실패: $e');
      }
      
      // FCM 토큰 삭제
      final fcmToken = await FcmService.getFcmToken();
      if (fcmToken != null) {
        try {
          await _authService.deleteDevice(fcmToken);
          print('FCM 토큰 삭제 성공');
        } catch (e) {
          print('FCM 토큰 삭제 실패: $e');
        }
      }
      
      // 로컬 FCM 토큰 삭제
      await FcmService.deleteFcmToken();
      
      // 저장 토큰 삭제
      await TokenStorage.deleteTokens();
      
      state = const AuthState();
    } catch (e) {
      print('로그아웃 중 오류: $e');
      await TokenStorage.deleteTokens();
      state = const AuthState();
    }
  }

  // 회원 정보 수정
  Future<UserInfo> updateUser(Map<String, dynamic> userData) async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      final updatedUser = await _authService.updateUser(userData);
      
      state = state.copyWith(
        isLoading: false,
        userInfo: updatedUser,
      );
      
      return updatedUser;
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString().replaceAll('Exception: ', ''),
      );
      rethrow;
    }
  }

  // 회원탈퇴
  Future<void> quit() async {
    state = state.copyWith(isLoading: true, error: null);
    
    try {
      await _authService.quit();
      
      // FCM 토큰 삭제
      final fcmToken = await FcmService.getFcmToken();
      if (fcmToken != null) {
        try {
          await _authService.deleteDevice(fcmToken);
          print('FCM 토큰 삭제 성공');
        } catch (e) {
          print('FCM 토큰 삭제 실패: $e');
        }
      }
      
      // 로컬 FCM 토큰 제거
      await FcmService.deleteFcmToken();
      
      // 남은 토큰 삭제
      await TokenStorage.deleteTokens();
      
      state = const AuthState();
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString().replaceAll('Exception: ', ''),
      );
      rethrow;
    }
  }

  void clearError() {
    state = state.copyWith(error: null);
  }
}

@riverpod
AuthState authState(AuthStateRef ref) {
  return ref.watch(authNotifierProvider);
}

@riverpod
bool isLoading(IsLoadingRef ref) {
  return ref.watch(authNotifierProvider).isLoading;
}

@riverpod
bool isAuthenticated(IsAuthenticatedRef ref) {
  return ref.watch(authNotifierProvider).isAuthenticated;
} 