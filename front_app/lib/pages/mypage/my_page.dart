import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:deepflect_app/widgets/mypage/upload_statistics.dart';
import 'package:deepflect_app/pages/mypage/edit_account.dart';
import 'package:deepflect_app/models/auth/auth_provider.dart';
import 'package:deepflect_app/pages/login/login.dart';
import 'package:deepflect_app/pages/mypage/delete_account.dart';
import 'package:deepflect_app/pages/mypage/notification.dart';
import 'package:deepflect_app/widgets/mypage/menu_item.dart';
import 'package:deepflect_app/widgets/mypage/menu_item2.dart';

class MyPage extends ConsumerWidget {
  const MyPage({super.key});

  void _showLogoutDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      barrierColor: Colors.black.withOpacity(0.5), // 어두운 배경
      builder: (BuildContext context) {
        return AlertDialog(
          backgroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '로그아웃',
                style: GoogleFonts.k2d(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF1D0523),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                '로그아웃 하시겠습니까?',
                style: GoogleFonts.k2d(
                  fontSize: 15,
                  fontWeight: FontWeight.w400,
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Color.fromRGBO(39, 0, 93, 1),
                        side: BorderSide(
                          color: Color.fromRGBO(39, 0, 93, 1),
                          width: 1.0,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10.0),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      child: Text(
                        '취소',
                        style: GoogleFonts.k2d(
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () {
                        Navigator.pop(context);
                        ref.read(authNotifierProvider.notifier).logout();
                        Navigator.of(context).pushAndRemoveUntil(
                          MaterialPageRoute(
                            builder: (context) => const LoginMain(),
                          ),
                          (route) => false,
                        );
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Color.fromRGBO(39, 0, 93, 1),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10.0),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      child: Text(
                        '확인',
                        style: GoogleFonts.k2d(
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            // 헤더 섹션 (다크 퍼플)
            Container(
              height: 210,
              width: double.infinity,
              decoration: const BoxDecoration(
                color: Color(0xFF27005D),
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(5),
                  bottomRight: Radius.circular(5),
                ),
              ),
              padding: const EdgeInsets.fromLTRB(27, 24, 27, 40),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 마이페이지 제목
                  Text(
                    '마이페이지',
                    style: GoogleFonts.k2d(
                      fontSize: 26,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 28),
                  // 사용자 정보 (프로필 아이콘 + 이메일)
                  Row(
                    children: [
                      // 프로필 아이콘
                      Container(
                        width: 35,
                        height: 35,
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(100),
                        ),
                        child: const Icon(
                          Icons.account_box,
                          color: Color(0xFF27005D),
                          size: 24,
                        ),
                      ),
                      const SizedBox(width: 12),
                      // 이메일
                      Text(
                        'email@example.com',
                        style: GoogleFonts.k2d(
                          fontSize: 20,
                          fontWeight: FontWeight.w500,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            // UploadStatistics 위젯 (헤더와 메인 콘텐츠 사이에 위치)
            Transform.translate(
              offset: const Offset(0, -50),
              child: const UploadStatistics(
                photoCount: 3,
                videoCount: 1,
              ),
            ),
            // 메인 콘텐츠 영역
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.fromLTRB(27, 0, 27, 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 20),
                    // 알림 섹션
                    Text(
                      '알림',
                      style: GoogleFonts.k2d(
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                        color: const Color(0xFF1D0523),
                      ),
                    ),
                    const SizedBox(height: 16),
                    // 알림 메뉴 아이템
                    MenuItem(
                      icon: Icons.notifications_outlined,
                      title: '알림',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const NotificationScreen(),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 12),
                    MenuItem(
                      icon: Icons.settings_outlined,
                      title: '알림 설정',
                      onTap: () {},
                    ),
                    const SizedBox(height: 24),
                    // 구분선
                    const Divider(
                      color: Color(0xFFE5E0F2),
                      thickness: 1,
                    ),
                    const SizedBox(height: 24),
                    // 계정 섹션
                    Text(
                      '계정',
                      style: GoogleFonts.k2d(
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                        color: const Color(0xFF1D0523),
                      ),
                    ),
                    const SizedBox(height: 16),
                    // 회원정보 수정 메뉴 아이템
                    MenuItemWithSubtitle(
                      icon: Icons.info_outline,
                      title: '회원정보 수정',
                      subtitle: '이메일, 비밀번호 변경',
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const EditProfilePage(),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 12),
                    // 로그아웃 메뉴 아이템
                    MenuItem(
                      icon: Icons.logout,
                      title: '로그아웃',
                      onTap: () => _showLogoutDialog(context, ref),
                    ),
                    const SizedBox(height: 16),
                    // 회원탈퇴
                    Center(
                      child: GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => const DeleteAccountScreen(),
                            ),
                          );
                        },
                        child: Text(
                          '회원탈퇴',
                          style: GoogleFonts.k2d(
                            fontSize: 13,
                            fontWeight: FontWeight.w400,
                            color: const Color(0xFF9400FF),
                            decoration: TextDecoration.underline,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
