import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:deepflect_app/pages/mypage/my_page.dart';
import 'package:deepflect_app/pages/file/upload/file_upload_page.dart';
import 'package:deepflect_app/pages/file/history/file_history_page.dart';
import 'package:deepflect_app/widgets/home/custom_navigation_bar.dart';
import 'package:deepflect_app/models/auth/auth_provider.dart';
import 'package:deepflect_app/pages/login/landing.dart';

class HomePage extends ConsumerStatefulWidget {
  const HomePage({super.key});

  @override
  ConsumerState<HomePage> createState() => _HomePageState();
}

class _HomePageState extends ConsumerState<HomePage> {
  int _currentIndex = 1; // 홈(업로드) 페이지가 기본
  final GlobalKey<FileHistoryPageState> _historyPageKey = GlobalKey<FileHistoryPageState>();

  List<Widget> get _pages => [
    FileHistoryPage(key: _historyPageKey, stateKey: _historyPageKey), // 히스토리 페이지 (index 0)
    FileUploadPage(
      onUploadSuccess: () {
        _historyPageKey.currentState?.refresh();
      },
    ),
    const MyPage(),
  ];

  void _onNavTap(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    
    // 인증되지 않은 경우 랜딩 페이지로 리다이렉트
    if (!authState.isAuthenticated) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (context) => const LandingPage()),
          (route) => false,
        );
      });
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    return Scaffold(
      body: _pages[_currentIndex],
      bottomNavigationBar: CustomNavigationBar(
        currentIndex: _currentIndex,
        onTap: _onNavTap,
      ),
    );
  }
}
