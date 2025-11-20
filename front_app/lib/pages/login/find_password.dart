import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:deepflect_app/widgets/login/full_form_input.dart';
import 'package:deepflect_app/widgets/login/login_button.dart';
import 'package:deepflect_app/pages/login/sent_password.dart';
import 'package:deepflect_app/models/auth/auth_provider.dart';

class FindPasswordPage extends ConsumerStatefulWidget {
  const FindPasswordPage({super.key});

  @override
  ConsumerState<FindPasswordPage> createState() => _FindPasswordState();
}

class _FindPasswordState extends ConsumerState<FindPasswordPage> {
  final TextEditingController _emailController = TextEditingController();

  Future<void> _sendPasswordResetEmail() async {
    final email = _emailController.text.trim();

    if (email.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("이메일을 입력해주세요."),
          backgroundColor: Color.fromRGBO(39, 0, 93, 1),
        ),
      );
      return;
    }

    try {
      // 비밀번호 재설정 API 호출
      await ref.read(authNotifierProvider.notifier).passwordReset(email);

      if (!mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => SentPasswordPage(email: email),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString().replaceAll('Exception: ', '')),
          backgroundColor: Colors.red[700],
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);
    final isLoading = authState.isLoading;
    return Scaffold(
      resizeToAvoidBottomInset: true, 
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.start,
          children: <Widget>[
            Padding(
              padding: const EdgeInsets.only(left: 10.0, top: 15.0),
              child: IconButton(
                icon: Icon(
                  Icons.chevron_left,
                  color: Color.fromRGBO(39, 0, 93, 1),
                ),
                onPressed: isLoading ? null : () => Navigator.pop(context),
              ),
            ),
            
            // 제목
            Padding(
              padding: const EdgeInsets.only(
                left: 30.0,
                top: 120.0,
                right: 20.0,
                bottom: 70.0,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    "비밀번호 찾기",
                    style: GoogleFonts.k2d(
                      fontSize: 30,
                      fontWeight: FontWeight.w600,
                      color: Colors.black,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "가입하신 이메일을 입력해주세요.\n비밀번호 재설정 이메일을 보내드립니다.",
                    style: GoogleFonts.k2d(
                      fontSize: 15,
                      color: Color.fromRGBO(136, 86, 204, 1),
                    ),
                  ),
                ],
              ),
            ),
            
            // 폼 필드
            Expanded(
              child: Align(
                alignment: Alignment.topCenter,
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 24.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    mainAxisAlignment: MainAxisAlignment.start,
                    children: [

                    // 이메일 입력
                    FullFormInput(
                      text: "Email",
                      text2: "이메일을 입력하세요.",
                      controller: _emailController,
                      prefixIcon: Icon(Icons.mail, color: Color.fromRGBO(39, 0, 93, 1)),
                    ),

                    const SizedBox(height: 50),

                    // 발송 버튼
                    LoginButton(
                      text: isLoading ? "처리 중..." : "이메일 발송",
                      onTap: isLoading ? null : _sendPasswordResetEmail,
                    ),
                  ],
                ),
              ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
