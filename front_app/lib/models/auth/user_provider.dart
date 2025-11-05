import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:deepflect_app/models/auth/auth.dart';
import 'package:deepflect_app/services/auth_service.dart';

part 'user_provider.g.dart';

// 사용자 정보만을 위한 별도 Provider
@riverpod
class UserNotifier extends _$UserNotifier {
  late final AuthService _authService;

  @override
  UserInfo? build() {
    _authService = AuthService();
    return null; // 초기값은 null
  }

  // 사용자 정보 가져오기 (캐싱됨)
  Future<UserInfo?> fetchUserInfo() async {
    try {
      final userInfo = await _authService.getMe();
      state = userInfo;
      return userInfo;
    } catch (e) {
      print('사용자 정보 가져오기 실패: $e');
      return null;
    }
  }

  // 사용자 정보 초기화
  void clearUserInfo() {
    state = null;
  }

  // 사용자 정보 업데이트 (로그인 시)
  void updateUserInfo(UserInfo userInfo) {
    state = userInfo;
  }
}

// 사용자 정보 상태만 제공 (캐싱됨)
@riverpod
Future<UserInfo?> userInfo(UserInfoRef ref) async {
  final userNotifier = ref.watch(userNotifierProvider.notifier);
  final currentUser = ref.watch(userNotifierProvider);
  
  // 이미 사용자 정보가 있으면 그대로 반환 (캐싱)
  if (currentUser != null) {
    return currentUser;
  }
  
  // 없으면 새로 가져오기
  return await userNotifier.fetchUserInfo();
} 