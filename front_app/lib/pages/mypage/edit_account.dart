import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:deepflect_app/models/auth/user_provider.dart';
import 'package:deepflect_app/models/auth/auth_provider.dart';
import 'package:deepflect_app/widgets/login/full_form_input.dart';
import 'package:deepflect_app/widgets/login/login_button.dart';

class EditProfilePage extends ConsumerStatefulWidget {
  const EditProfilePage({super.key});

  @override
  ConsumerState<EditProfilePage> createState() => _EditProfilePageState();
}

class _EditProfilePageState extends ConsumerState<EditProfilePage> {
  bool _isEmailMode = true; // true: 이메일 수정, false: 비밀번호 수정
  
  // 이메일 수정용 컨트롤러
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordForEmailController = TextEditingController();
  
  // 비밀번호 수정용 컨트롤러
  final TextEditingController _currentPasswordController = TextEditingController();
  final TextEditingController _newPasswordController = TextEditingController();
  final TextEditingController _confirmPasswordController = TextEditingController();
  
  final _formKey = GlobalKey<FormState>();
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    // 현재 사용자 이메일로 초기화
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final userInfo = ref.read(userInfoProvider);
      userInfo.whenData((data) {
        if (data != null) {
          _emailController.text = data.email;
        }
      });
    });
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordForEmailController.dispose();
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
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
    if (value != _newPasswordController.text) {
      return '비밀번호가 일치하지 않습니다.';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = ref.watch(authNotifierProvider).isLoading;
    final screenHeight = MediaQuery.of(context).size.height;

    return Scaffold(
      resizeToAvoidBottomInset: true,
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
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
              padding: EdgeInsets.only(
                left: 30.0,
                top: screenHeight < 700 ? 30.0 : 70.0,
                right: 20.0,
                bottom: screenHeight < 700 ? 20.0 : 50.0,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    "회원정보 수정",
                    style: TextStyle(
                      fontSize: 30,
                      fontFamily: 'K2D',
                      fontWeight: FontWeight.w600,
                      color: Colors.black,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8.0, horizontal: 0.0),
                    child: Row(
                      children: [
                        Expanded(
                          child: RadioListTile<bool>(
                            contentPadding: EdgeInsets.zero,
                            dense: true,
                            title: Text('Email', style: TextStyle(fontSize: 14, fontFamily: 'K2D')),
                            value: true,
                            groupValue: _isEmailMode,
                            onChanged: (value) {
                              setState(() {
                                _isEmailMode = value!;
                              });
                            },
                            activeColor: Color.fromRGBO(39, 0, 93, 1),
                          ),
                        ),
                        Expanded(
                          child: RadioListTile<bool>(
                            contentPadding: EdgeInsets.zero,
                            dense: true,
                            title: Text('비밀번호', style: TextStyle(fontSize: 14, fontFamily: 'K2D')),
                            value: false,
                            groupValue: _isEmailMode,
                            onChanged: (value) {
                              setState(() {
                                _isEmailMode = value!;
                              });
                            },
                            activeColor: Color.fromRGBO(39, 0, 93, 1),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            
            SizedBox(height: screenHeight < 700 ? 10 : 20),
            
            // 폼 필드 영역
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                mainAxisAlignment: MainAxisAlignment.start,
                children: [

                      // 이메일 수정 폼
                      if (_isEmailMode) ...[
                        FullFormInput(
                          text: "Email", 
                          text2: "이메일을 입력하세요.",
                          controller: _emailController,
                          validator: _validateEmail,
                          prefixIcon: Icon(Icons.mail, color: Color.fromRGBO(39, 0, 93, 1)),
                        ),
                        SizedBox(height: screenHeight < 700 ? 20 : 35),
                        FullFormInput(
                          text: "비밀번호",
                          text2: "비밀번호를 입력하세요",
                          isPassword: true,
                          controller: _passwordForEmailController,
                          validator: _validatePassword,
                          prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                        ),
                        SizedBox(height: screenHeight < 700 ? 12 : 16),
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.grey[50],
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '*반드시 본인의 이메일을 입력해주세요.',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[600],
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '*계정 분실시 비밀번호 찾기 등에 사용됩니다.',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[600],
                                ),
                              ),
                            ],
                          ),
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
                          text: isLoading ? "처리 중..." : "수정",
                          onTap: isLoading ? null : _handleEmailChange,
                        ),
                      ],

                      // 비밀번호 수정 폼
                      if (!_isEmailMode) ...[
                        FullFormInput(
                          text: "현재 비밀번호", 
                          text2: "현재 비밀번호를 입력하세요.",
                          isPassword: true,
                          controller: _currentPasswordController,
                          validator: _validatePassword,
                          prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                        ),
                        SizedBox(height: screenHeight < 700 ? 20 : 35),
                        FullFormInput(
                          text: "새 비밀번호", 
                          text2: "새 비밀번호를 입력하세요.",
                          isPassword: true,
                          controller: _newPasswordController,
                          validator: _validatePassword,
                          prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                        ),
                        SizedBox(height: screenHeight < 700 ? 20 : 35),
                        FullFormInput(
                          text: "새 비밀번호 확인",
                          text2: "새 비밀번호를 입력하세요.",
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
                          text: isLoading ? "처리 중..." : "수정",
                          onTap: isLoading ? null : _handlePasswordChange,
                        ),
                      ],
                    ],
                  ),
            ),
            // 키보드가 올라올 때 여유 공간 확보
            SizedBox(height: MediaQuery.of(context).viewInsets.bottom > 0 ? 20 : 0),
          ],
        ),
          ),
        ),
      ),
    );
  }

  Future<void> _handleEmailChange() async {
    // 폼 유효성 검사
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (_emailController.text.isEmpty || _passwordForEmailController.text.isEmpty) {
      setState(() {
        _errorMessage = '모든 필드를 입력해주세요.';
      });
      return;
    }

    // 이메일 형식 검증
    if (!_emailController.text.contains('@') || !_emailController.text.contains('.')) {
      setState(() {
        _errorMessage = '올바른 이메일 형식을 입력해주세요.';
      });
      return;
    }

    setState(() {
      _errorMessage = null;
    });

    try {
      final updatedUser = await ref.read(authNotifierProvider.notifier).updateUser({
        'email': _emailController.text.trim(),
      });

      // UserProvider도 업데이트
      ref.read(userNotifierProvider.notifier).updateUserInfo(updatedUser);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('이메일 변경이 완료되었습니다.'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  Future<void> _handlePasswordChange() async {
    // 폼 유효성 검사
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (_currentPasswordController.text.isEmpty ||
        _newPasswordController.text.isEmpty ||
        _confirmPasswordController.text.isEmpty) {
      setState(() {
        _errorMessage = '모든 필드를 입력해주세요.';
      });
      return;
    }

    if (_newPasswordController.text.length < 6) {
      setState(() {
        _errorMessage = '비밀번호는 최소 6자 이상이어야 합니다.';
      });
      return;
    }

    if (_newPasswordController.text != _confirmPasswordController.text) {
      setState(() {
        _errorMessage = '새 비밀번호가 일치하지 않습니다.';
      });
      return;
    }

    setState(() {
      _errorMessage = null;
    });

    try {
      final updatedUser = await ref.read(authNotifierProvider.notifier).updateUser({
        'password': _newPasswordController.text,
        'currentPassword': _currentPasswordController.text,
      });

      // UserProvider도 업데이트
      ref.read(userNotifierProvider.notifier).updateUserInfo(updatedUser);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('비밀번호 변경이 완료되었습니다.'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }
} 