import 'package:freezed_annotation/freezed_annotation.dart';
part 'auth.freezed.dart';
part 'auth.g.dart';

@freezed
class LoginRequest with _$LoginRequest {
  const factory LoginRequest({
    required String email,
    required String password,
  }) = _LoginRequest;

  factory LoginRequest.fromJson(Map<String, dynamic> json) =>
      _$LoginRequestFromJson(json);
}

@freezed
class UserInfo with _$UserInfo {
  const factory UserInfo({
    required int id,
    required String email,
    required String nickname,
  }) = _UserInfo;

  factory UserInfo.fromJson(Map<String, dynamic> json) =>
      _$UserInfoFromJson(json);
}

@freezed
class LoginResponse with _$LoginResponse {
  const factory LoginResponse({
    required String accessToken,
    required String refreshToken,
    required String accessTokenExpiresAt,
    required String refreshTokenExpiresAt,
  }) = _LoginResponse;

  factory LoginResponse.fromJson(Map<String, dynamic> json) =>
      _$LoginResponseFromJson(json);
}

@freezed
class AuthState with _$AuthState {
  const factory AuthState({
    @Default(false) bool isLoading,
    @Default(false) bool isAuthenticated,
    String? accessToken,
    String? refreshToken,
    UserInfo? userInfo,
    String? error,
  }) = _AuthState;
} 