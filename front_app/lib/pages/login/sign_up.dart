import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:deepflect_app/widgets/login/full_form_input.dart';
import 'package:deepflect_app/widgets/login/login_button.dart';
import 'package:deepflect_app/models/auth/auth_provider.dart';

class SignUpPage extends ConsumerStatefulWidget {
  const SignUpPage({super.key});

  @override
  ConsumerState<SignUpPage> createState() => _SignUpPageState();
}

class _SignUpPageState extends ConsumerState<SignUpPage> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _handleSignUp() async {
    // 폼 유효성 검사
    if (!_formKey.currentState!.validate()) {
      return;
    }

    // 비밀번호 확인 검증
    if (_passwordController.text != _confirmPasswordController.text) {
      setState(() {
        _errorMessage = '비밀번호가 일치하지 않습니다.';
      });
      return;
    }

    setState(() {
      _errorMessage = null;
    });

    try {
      await ref.read(authNotifierProvider.notifier).register(
            _emailController.text.trim(),
            _passwordController.text,
          );

      // 회원가입 성공 시
      if (mounted) {
        // 로그인 상태로 변경되었으므로 홈으로 이동하거나 로그인 페이지로 이동
        Navigator.of(context).popUntil((route) => route.isFirst);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  String? _validateEmail(String? value) {
    if (value == null || value.isEmpty) {
      return '이메일을 입력해주세요.';
    }
    if (!value.contains('@') || !value.contains('.')) {
      return '올바른 이메일 형식을 입력해주세요.';
    }
    return null;
  }

  String? _validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return '비밀번호를 입력해주세요.';
    }
    if (value.length < 6) {
      return '비밀번호는 최소 6자 이상이어야 합니다.';
    }
    return null;
  }

  String? _validateConfirmPassword(String? value) {
    if (value == null || value.isEmpty) {
      return '비밀번호 확인을 입력해주세요.';
    }
    if (value != _passwordController.text) {
      return '비밀번호가 일치하지 않습니다.';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = ref.watch(authNotifierProvider).isLoading;
    final screenHeight = MediaQuery.of(context).size.height;
    final keyboardHeight = MediaQuery.of(context).viewInsets.bottom;

    return Scaffold(
      resizeToAvoidBottomInset: true,
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            physics: const ClampingScrollPhysics(),
            child: ConstrainedBox(
              constraints: BoxConstraints(
                minHeight: screenHeight - MediaQuery.of(context).padding.top - MediaQuery.of(context).padding.bottom,
              ),
              child: IntrinsicHeight(
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
                        onPressed: isLoading ? null : () => Navigator.pop(context),
                      ),
                    ),
                    
                    // 제목 영역
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
                    
                    SizedBox(height: screenHeight < 700 ? 10 : 20),

                    // 폼 필드 영역
                    Flexible(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 24.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          mainAxisAlignment: MainAxisAlignment.start,
                          children: [
                            FullFormInput(
                              text: "Email",
                              text2: "이메일을 입력하세요.",
                              controller: _emailController,
                              validator: _validateEmail,
                              prefixIcon: Icon(Icons.mail, color: Color.fromRGBO(39, 0, 93, 1)),
                            ),
                            SizedBox(height: screenHeight < 700 ? 20 : 35),
                            FullFormInput(
                              text: "Password",
                              text2: "비밀번호를 입력하세요",
                              isPassword: true,
                              controller: _passwordController,
                              validator: _validatePassword,
                              prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                            ),
                            SizedBox(height: screenHeight < 700 ? 20 : 35),
                            FullFormInput(
                              text: "Password 확인",
                              text2: "비밀번호를 입력하세요.",
                              isPassword: true,
                              controller: _confirmPasswordController,
                              validator: _validateConfirmPassword,
                              prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                            ),
                            if (_errorMessage != null) ...[
                              SizedBox(height: screenHeight < 700 ? 12 : 16),
                              Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: Colors.red[50],
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: Colors.red[300]!),
                                ),
                                child: Row(
                                  children: [
                                    Icon(Icons.error_outline, color: Colors.red[700], size: 20),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        _errorMessage!,
                                        style: TextStyle(
                                          color: Colors.red[700],
                                          fontSize: 14,
                                          fontFamily: 'K2D',
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                            SizedBox(height: screenHeight < 700 ? 30 : 50),
                            LoginButton(
                              text: isLoading ? "처리 중..." : "회원가입",
                              onTap: isLoading ? null : _handleSignUp,
                            ),
                            // 키보드가 올라올 때 여유 공간 확보
                            SizedBox(height: keyboardHeight > 0 ? 20 : 0),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
