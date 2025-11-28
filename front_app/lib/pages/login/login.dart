import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:deepflect_app/models/auth/auth_provider.dart';
import 'package:deepflect_app/pages/home/home_page.dart';
import 'package:deepflect_app/pages/login/sign_up.dart';
import 'package:deepflect_app/widgets/login/full_form_input.dart';
import 'package:deepflect_app/widgets/login/text_button.dart' as custom;
import 'package:deepflect_app/widgets/login/login_button.dart';
import 'package:deepflect_app/pages/login/find_password.dart';

class LoginMain extends ConsumerStatefulWidget {
  const LoginMain({super.key});

  @override
  ConsumerState<LoginMain> createState() => _LoginMainState();
}

class _LoginMainState extends ConsumerState<LoginMain> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _handleLogin() async {
    if (_emailController.text.isEmpty || _passwordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('이메일과 비밀번호를 입력해주세요.'),
          backgroundColor: Color.fromRGBO(39, 0, 93, 1),
        ),
      );
      return;
    }

    await ref.read(authNotifierProvider.notifier).login(
      _emailController.text,
      _passwordController.text,
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider);

    // 로그인 성공
    if (authState.isAuthenticated) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('로그인 성공!'),
            backgroundColor: Color.fromARGB(255, 57, 132, 58),
          ),
        );
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(
            builder: (context) => const HomePage(),
          ),
          (route) => false, 
        );
      });
    }

    // 에러 처리
    if (authState.error != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(authState.error!),
            backgroundColor: Colors.red,
          ),
        );
        ref.read(authNotifierProvider.notifier).clearError();
      });
    }

    final screenHeight = MediaQuery.of(context).size.height;
    final keyboardHeight = MediaQuery.of(context).viewInsets.bottom;

    return Scaffold(
      resizeToAvoidBottomInset: true,
      body: SafeArea(
        child: SingleChildScrollView(
          physics: const ClampingScrollPhysics(),
          child: ConstrainedBox(
            constraints: BoxConstraints(
              minHeight: screenHeight - MediaQuery.of(context).padding.top - MediaQuery.of(context).padding.bottom,
            ),
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
                    onPressed: () => Navigator.pop(context),
                  ),
                ),
                
                // 제목
                Padding(
                  padding: EdgeInsets.only(
                    left: 30.0,
                    top: screenHeight < 700 ? 30.0 : 70.0,
                    right: 20.0,
                    bottom: screenHeight < 700 ? 20.0 : 50.0,
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: const [
                      Text(
                        "로그인",
                        style: TextStyle(
                          fontSize: 30,
                          fontFamily: 'K2D',
                          fontWeight: FontWeight.w600,
                          color: Colors.black,
                        ),
                      ),
                      SizedBox(height: 8),
                      Text(
                        "Lets login to use Deepflect",
                        style: TextStyle(
                          fontSize: 15,
                          fontFamily: 'K2D',
                          color: Color.fromRGBO(136, 86, 204, 1),
                        ),
                      ),
                    ],
                  ),
                ),
                
                SizedBox(height: screenHeight < 700 ? 10 : 20),
                
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    mainAxisAlignment: MainAxisAlignment.start,
                    children: [
                      FullFormInput(
                        text: "Email", 
                        text2: "이메일을 입력하세요.",
                        controller: _emailController,
                        prefixIcon: Icon(
                          Icons.mail,
                          color: Color.fromRGBO(39, 0, 93, 1),
                        ),
                      ),
                      SizedBox(height: screenHeight < 700 ? 20 : 35),
                      FullFormInput(
                        text: "Password",
                        text2: "비밀번호를 입력하세요.",
                        isPassword: true,
                        controller: _passwordController,
                        prefixIcon: Icon(
                          Icons.lock,
                          color: Color.fromRGBO(39, 0, 93, 1),
                        ),
                      ),
                      const SizedBox(height: 15),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          custom.TextButton(
                            text: "비밀번호 찾기",
                            fontSize: 15,
                            onTap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(builder: (_) => const FindPasswordPage()),
                              );
                            },
                          ),
                        ],
                      ),
                      SizedBox(height: screenHeight < 700 ? 30 : 50),
                      authState.isLoading
                          ? const Center(
                              child: CircularProgressIndicator(),
                            )
                          : LoginButton(
                              text: "로그인",
                              onTap: _handleLogin,
                            ),
                      const SizedBox(height: 16),
                      custom.TextButton(
                        text: "회원가입",
                        onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(builder: (context) => const SignUpPage())),
                      ),
                      SizedBox(height: keyboardHeight > 0 ? 20 : 0),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
