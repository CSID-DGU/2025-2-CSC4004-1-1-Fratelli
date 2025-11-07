import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:deepflect_app/widgets/login/Full_Form_Input.dart';
import 'package:deepflect_app/widgets/login/login_button.dart';
import 'package:deepflect_app/pages/login/login.dart';

class SignUpPage extends StatelessWidget {
  const SignUpPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.start,
          children: <Widget>[
            // 뒤로가기 버튼 (상단 고정)
            Padding(
              padding: const EdgeInsets.only(left: 10.0, top: 15.0),
              child: IconButton(
                icon: Icon(
                  Icons.chevron_left,
                  color: Color.fromRGBO(39, 0, 93, 1),
                ),
                onPressed: () => Navigator.pop(context),
              ),
            ),
            
            // 제목 영역
            Padding(
              padding: const EdgeInsets.only(
                left: 30.0,
                top: 70.0,
                right: 20.0,
                bottom: 50.0,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: const [
                  Text(
                    "회원가입",
                    style: TextStyle(
                      fontSize: 30,
                      fontFamily: 'K2D',
                      fontWeight: FontWeight.w600,
                      color: Colors.black,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    "Create account to use Deepflect",
                    style: TextStyle(
                      fontSize: 15,
                      fontFamily: 'K2D',
                      color: Color.fromRGBO(136, 86, 204, 1),
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 20),

            // 폼 필드 영역
            Expanded(
              child: Align(
                alignment: Alignment.topCenter,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    mainAxisAlignment: MainAxisAlignment.start,
                    children: [
                    const FullFormInput(
                      text: "Email",
                      text2: "이메일을 입력하세요.",
                      prefixIcon: Icon(Icons.mail, color: Color.fromRGBO(39, 0, 93, 1)),
                    ),
                    const SizedBox(height: 35),
                    const FullFormInput(
                      text: "Password",
                      text2: "비밀번호를 입력하세요",
                      isPassword: true,
                      prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                    ),
                    const SizedBox(height: 35),
                    const FullFormInput(
                      text: "Password 확인",
                      text2: "비밀번호를 입력하세요.",
                      isPassword: true,
                      prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                    ),
                    const SizedBox(height: 50),
                    LoginButton(
                      text: "회원가입",
                      onTap: () {
                        print("회원가입");
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const LoginMain(),
                          ),
                        );
                      },
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
