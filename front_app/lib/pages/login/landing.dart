import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:deepflect_app/pages/login/login.dart';
import 'package:deepflect_app/pages/login/sign_up.dart';
import 'package:deepflect_app/widgets/login/login_button.dart';
import 'package:deepflect_app/widgets/login/full_button.dart';

class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            Expanded(flex: 3, child: SizedBox()),
            Expanded(
              flex: 7,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    // 앱 이름
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Text(
                          'Deepflect',
                          style: GoogleFonts.k2d(
                            fontSize: 32,
                            fontWeight: FontWeight.bold,
                            color: Color.fromRGBO(29, 5, 35, 1),
                          )
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Welcome to Deepflect',
                          style: GoogleFonts.k2d(
                            fontSize: 16,
                            color: Color.fromRGBO(136, 86, 204, 1),
                          )
                        )
                    ],),
                    
                    const SizedBox(height: 130),

                    // 로그인 버튼
                    LoginButton(
                      text: '로그인',
                      icon: Icons.login,
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => const LoginMain(),
                          ),
                        );
                      },
                    ),
                    
                    const SizedBox(height: 16),
                    
                    // 회원가입 버튼
                    FullButton(
                      text: '회원가입',
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => const SignUpPage(),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 16),
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
