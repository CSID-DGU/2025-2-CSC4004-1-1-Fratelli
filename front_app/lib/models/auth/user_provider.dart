import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:deepflect_app/models/auth/auth.dart';
import 'package:deepflect_app/services/auth_service.dart';

part 'user_provider.g.dart';

@riverpod
class UserNotifier extends _$UserNotifier {
  late final AuthService _authService;

  @override
  UserInfo? build() {
    _authService = AuthService();
    return null;
  }

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

  void clearUserInfo() {
    state = null;
  }

  void updateUserInfo(UserInfo userInfo) {
    state = userInfo;
  }
}

@riverpod
Future<UserInfo?> userInfo(UserInfoRef ref) async {
  final userNotifier = ref.watch(userNotifierProvider.notifier);
  final currentUser = ref.watch(userNotifierProvider);
  
  if (currentUser != null) {
    return currentUser;
  }
  
  return await userNotifier.fetchUserInfo();
} 