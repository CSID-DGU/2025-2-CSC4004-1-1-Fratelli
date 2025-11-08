import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:deepflect_app/models/auth/user_provider.dart';
import 'package:deepflect_app/widgets/login/Full_Form_Input.dart';
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

                      // 이메일 수정 폼
                      if (_isEmailMode) ...[
                        FullFormInput(
                          text: "Email", 
                          text2: "이메일을 입력하세요.",
                          controller: _emailController,
                          prefixIcon: Icon(Icons.mail, color: Color.fromRGBO(39, 0, 93, 1)),
                        ),
                        const SizedBox(height: 35),
                        FullFormInput(
                          text: "비밀번호",
                          text2: "비밀번호를 입력하세요",
                          isPassword: true,
                          controller: _passwordForEmailController,
                          prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                        ),
                        const SizedBox(height: 16),
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
                        const SizedBox(height: 50),
                        LoginButton(
                          text: "수정",
                          onTap: _handleEmailChange,
                        ),
                      ],

                      // 비밀번호 수정 폼
                      if (!_isEmailMode) ...[
                        FullFormInput(
                          text: "현재 비밀번호", 
                          text2: "현재 비밀번호를 입력하세요.",
                          isPassword: true,
                          controller: _currentPasswordController,
                          prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                        ),
                        const SizedBox(height: 35),
                        FullFormInput(
                          text: "새 비밀번호", 
                          text2: "새 비밀번호를 입력하세요.",
                          isPassword: true,
                          controller: _newPasswordController,
                          prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                        ),
                        const SizedBox(height: 35),
                        FullFormInput(
                          text: "새 비밀번호 확인",
                          text2: "새 비밀번호를 입력하세요.",
                          isPassword: true,
                          controller: _confirmPasswordController,
                          prefixIcon: Icon(Icons.lock, color: Color.fromRGBO(39, 0, 93, 1)),
                        ),
                        const SizedBox(height: 50),
                        LoginButton(
                          text: "수정",
                          onTap: _handlePasswordChange,
                        ),
                      ],
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

  void _handleEmailChange() {
    // 이메일 변경 로직
    if (_emailController.text.isEmpty || _passwordForEmailController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('모든 필드를 입력해주세요.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }
    
    // TODO: API 호출하여 이메일 변경
    print('이메일 변경: ${_emailController.text}');
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('이메일 변경이 완료되었습니다.'),
        backgroundColor: Colors.green,
      ),
    );
  }

  void _handlePasswordChange() {
    // 비밀번호 변경 로직
    if (_currentPasswordController.text.isEmpty ||
        _newPasswordController.text.isEmpty ||
        _confirmPasswordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('모든 필드를 입력해주세요.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    if (_newPasswordController.text != _confirmPasswordController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('새 비밀번호가 일치하지 않습니다.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }
    
    // TODO: API 호출하여 비밀번호 변경
    print('비밀번호 변경');
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('비밀번호 변경이 완료되었습니다.'),
        backgroundColor: Colors.green,
      ),
    );
  }
} 