import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/material.dart';

class FcmService {
  static final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  static final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();
  static bool _isInitialized = false;

  // FCM 초기화
  static Future<void> initialize() async {
    try {
      print('FCM 초기화 시작...');
      
      // 로컬 알림 초기화
      const AndroidInitializationSettings initializationSettingsAndroid =
          AndroidInitializationSettings('@mipmap/ic_launcher');
      
      const DarwinInitializationSettings initializationSettingsIOS =
          DarwinInitializationSettings();
      
      const InitializationSettings initializationSettings =
          InitializationSettings(
        android: initializationSettingsAndroid,
        iOS: initializationSettingsIOS,
      );
      
      await _localNotifications.initialize(initializationSettings);
      print('로컬 알림 초기화 완료');
      
      // Firebase Messaging 초기화 시도
      try {
        // 포그라운드 메시지 핸들러 설정
        FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
        print('포그라운드 메시지 핸들러 설정 완료');
        
        // 백그라운드 메시지 핸들러 설정
        FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
        print('백그라운드 메시지 핸들러 설정 완료');
      } catch (firebaseError) {
        print('Firebase Messaging 설정 실패 (로컬 알림만 사용): $firebaseError');
        // Firebase가 설정되지 않아도 로컬 알림은 사용 가능
      }
      
      _isInitialized = true;
      print('FCM 초기화 완료');
    } catch (e, stackTrace) {
      print('FCM 초기화 실패: $e');
      print('스택 트레이스: $stackTrace');
      _isInitialized = false;
      // 에러를 다시 throw하지 않음 - 앱이 계속 실행되도록
    }
  }

  // FCM 토큰 가져오기
  static Future<String?> getFcmToken() async {
    if (!_isInitialized) {
      print('FCM이 초기화되지 않았습니다.');
      return null;
    }
    
    try {
      // 알림 권한 요청
      NotificationSettings settings = await _firebaseMessaging.requestPermission(
        alert: true,
        announcement: false,
        badge: true,
        carPlay: false,
        criticalAlert: false,
        provisional: false,
        sound: true,
      );

      if (settings.authorizationStatus == AuthorizationStatus.authorized) {
        // FCM 토큰 가져오기
        String? token = await _firebaseMessaging.getToken();
        print('FCM 토큰: $token');
        return token;
      } else {
        print('알림 권한이 거부되었습니다.');
        return null;
      }
    } catch (e) {
      print('FCM 토큰 가져오기 실패: $e');
      return null;
    }
  }

  // FCM 토큰 삭제
  static Future<void> deleteFcmToken() async {
    if (!_isInitialized) {
      print('FCM이 초기화되지 않았습니다.');
      return;
    }
    
    try {
      await _firebaseMessaging.deleteToken();
      print('FCM 토큰 삭제 완료');
    } catch (e) {
      print('FCM 토큰 삭제 실패: $e');
    }
  }

  // 강력한 테스트 알림 (시뮬레이터용)
  static Future<void> showStrongTestNotification() async {
    try {
      print('강력한 테스트 알림 시작...');
      
      // iOS 시뮬레이터용 강력한 알림 설정
      const DarwinNotificationDetails iOSPlatformChannelSpecifics =
          DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
        sound: 'default',
        badgeNumber: 1,
        categoryIdentifier: 'test_category',
        threadIdentifier: 'test_thread',
        interruptionLevel: InterruptionLevel.active,
      );
      
      const AndroidNotificationDetails androidPlatformChannelSpecifics =
          AndroidNotificationDetails(
        'strong_test_channel',
        'Strong Test Notifications',
        channelDescription: '강력한 테스트 알림',
        importance: Importance.max,
        priority: Priority.max,
        showWhen: true,
        enableVibration: true,
        playSound: true,
        sound: RawResourceAndroidNotificationSound('notification_sound'),
        largeIcon: DrawableResourceAndroidBitmap('@mipmap/ic_launcher'),
        color: Color(0xFFFF6B35),
        enableLights: true,
        ledColor: Color(0xFFFF6B35),
        ledOnMs: 1000,
        ledOffMs: 500,
      );
      
      const NotificationDetails platformChannelSpecifics = NotificationDetails(
        android: androidPlatformChannelSpecifics,
        iOS: iOSPlatformChannelSpecifics,
      );
      
      // 즉시 알림 표시
      await _localNotifications.show(
        1000,
        '🚨 강력한 테스트 알림 🚨',
        '이 알림이 보이면 알림 시스템이 정상 작동합니다!',
        platformChannelSpecifics,
      );
      
      print('강력한 테스트 알림 표시 완료');
      
      // 3초 후 두 번째 알림
      await Future.delayed(Duration(seconds: 3));
      await _localNotifications.show(
        1001,
        '📱 두 번째 알림 📱',
        '3초 후에 표시되는 알림입니다!',
        platformChannelSpecifics,
      );
      
      print('두 번째 알림 표시 완료');
      
    } catch (e) {
      print('강력한 테스트 알림 실패: $e');
    }
  }

  // 간단한 테스트 알림 (시뮬레이터용)
  static Future<void> showSimpleTestNotification() async {
    try {
      print('간단한 테스트 알림 시작...');
      
      // 기본 설정으로 알림 표시
      await _localNotifications.show(
        999,
        '간단한 테스트',
        '이 알림이 보이나요?',
        const NotificationDetails(),
      );
      
      print('간단한 테스트 알림 표시 완료');
    } catch (e) {
      print('간단한 테스트 알림 실패: $e');
    }
  }

  // 테스트용 로컬 알림 (시뮬레이터용)
  static Future<void> showTestNotification() async {
    try {
      print('테스트 알림 시작...');
      print('FCM 초기화 상태: $_isInitialized');
      
      // 로컬 알림 초기화 확인
      if (!_isInitialized) {
        print('FCM이 초기화되지 않았습니다. 로컬 알림만 초기화합니다.');
        await _initializeLocalNotifications();
      }
      
      // iOS 알림 권한 확인 및 요청
      await _requestNotificationPermission();
      
      // iOS 시뮬레이터용 알림 설정
      const DarwinNotificationDetails iOSPlatformChannelSpecifics =
          DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
        sound: 'default',
      );
      
      const AndroidNotificationDetails androidPlatformChannelSpecifics =
          AndroidNotificationDetails(
        'deepflect_channel',
        'Deepflect Notifications',
        channelDescription: 'Deepflect 앱 알림',
        importance: Importance.max,
        priority: Priority.high,
        showWhen: true,
        enableVibration: true,
        playSound: true,
      );
      
      const NotificationDetails platformChannelSpecifics = NotificationDetails(
        android: androidPlatformChannelSpecifics,
        iOS: iOSPlatformChannelSpecifics,
      );
      
      // 여러 번 시도
      for (int i = 0; i < 3; i++) {
        await _localNotifications.show(
          i,
          '테스트 알림 ${i + 1}',
          '시뮬레이터에서 로컬 알림이 정상 작동합니다! (${i + 1}/3)',
          platformChannelSpecifics,
        );
        print('테스트 알림 ${i + 1} 표시 완료');
        await Future.delayed(Duration(seconds: 2));
      }
      
      print('모든 테스트 알림 표시 완료');
    } catch (e) {
      print('테스트 알림 표시 실패: $e');
    }
  }

  // 포그라운드 메시지 처리
  static void _handleForegroundMessage(RemoteMessage message) {
    print('포그라운드 메시지 수신: ${message.notification?.title}');
    
    // 로컬 알림 표시
    _showLocalNotification(message);
  }

  // 로컬 알림 표시
  static Future<void> _showLocalNotification(RemoteMessage message) async {
    const AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
      'deepflect_channel',
      'Deepflect Notifications',
      channelDescription: 'Deepflect 앱 알림',
      importance: Importance.max,
      priority: Priority.high,
    );
    
    const DarwinNotificationDetails iOSPlatformChannelSpecifics =
        DarwinNotificationDetails();
    
    const NotificationDetails platformChannelSpecifics = NotificationDetails(
      android: androidPlatformChannelSpecifics,
      iOS: iOSPlatformChannelSpecifics,
    );
    
    await _localNotifications.show(
      message.hashCode,
      message.notification?.title,
      message.notification?.body,
      platformChannelSpecifics,
    );
  }

  // 알림 권한 요청
  static Future<void> _requestNotificationPermission() async {
    try {
      final settings = await _localNotifications.resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin>()?.requestPermissions(
        alert: true,
        badge: true,
        sound: true,
      );
      
      print('알림 권한 설정: $settings');
    } catch (e) {
      print('알림 권한 요청 실패: $e');
    }
  }

  // 로컬 알림만 초기화
  static Future<void> _initializeLocalNotifications() async {
    try {
      const AndroidInitializationSettings initializationSettingsAndroid =
          AndroidInitializationSettings('@mipmap/ic_launcher');
      
      const DarwinInitializationSettings initializationSettingsIOS =
          DarwinInitializationSettings();
      
      const InitializationSettings initializationSettings =
          InitializationSettings(
        android: initializationSettingsAndroid,
        iOS: initializationSettingsIOS,
      );
      
      await _localNotifications.initialize(initializationSettings);
      print('로컬 알림 초기화 완료');
    } catch (e) {
      print('로컬 알림 초기화 실패: $e');
    }
  }
}

// 백그라운드 메시지 핸들러 (최상위 레벨 함수여야 함)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  print('백그라운드 메시지 수신: ${message.notification?.title}');
} 