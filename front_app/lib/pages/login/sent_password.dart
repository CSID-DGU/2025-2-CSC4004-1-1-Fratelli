import 'package:flutter/material.dart';
import 'package:deepflect_app/pages/login/login.dart';

class SentPasswordPage extends StatelessWidget {
  final String email;

  const SentPasswordPage({super.key, required this.email});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.mark_email_unread,
                size: 100,
                color: Color.fromRGBO(39, 0, 93, 1.0),
                ),
              SizedBox(height: 20),

              Text(
                "Check your email",
                textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 30, 
                      fontFamily: 'K2D',
                      color: Color.fromRGBO(29, 5, 35, 1.0)
                      ),
              ),
              SizedBox(height: 20),
              
              Column(
                children: [
                  Text(
                    email,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 18, color: Color.fromRGBO(148, 0, 255, 1.0)),
                  ),
                  SizedBox(height: 8),
                  Text(
                    "비밀번호 재설정 메일이 발송되었습니다.",
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 18, color: Color.fromRGBO(191, 157, 238, 1.0)),
                  ),
                ],
              ),
              SizedBox(height: 40),
              ElevatedButton(
                onPressed: () {
                  Navigator.of(context).pushAndRemoveUntil(
                    MaterialPageRoute(
                      builder: (context) => const LoginMain(),
                    ),
                    (route) => false,
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Color.fromRGBO(29, 5, 35, 1.0),
                  side: BorderSide(
                    color: Color.fromRGBO(29, 5, 35, 1.0),
                    width: 1.0,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10.0),
                  ),
                ),
                child: Text("확인"),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
