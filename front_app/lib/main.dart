import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:deepflect_app/pages/login/landing.dart';
import 'package:deepflect_app/firebase_options.dart';
import 'package:deepflect_app/services/fcm_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Firebase 초기화
  try {
    await Firebase.initializeApp(
      name: "deepflect_app",
      options: DefaultFirebaseOptions.currentPlatform,
    );
    print('Firebase 초기화 성공');

    // FCM 초기화
    try {
      await FcmService.initialize();
      print('FCM 초기화 성공');
    } catch (e) {
      print('FCM 초기화 실패: $e');
    }
  } catch (e) {
    print('Firebase 초기화 실패: $e');
  }

  // 환경 변수 로드
  await dotenv.load(fileName: ".env");

  runApp(const ProviderScope(child: DeepflectApp()));
}

class DeepflectApp extends StatelessWidget {
  const DeepflectApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Deepflect App',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        scaffoldBackgroundColor: Colors.white,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const LandingPage(),
    );
  }
}
