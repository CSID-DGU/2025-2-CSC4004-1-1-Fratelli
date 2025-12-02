import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';

class NotificationSettingPage extends StatefulWidget {
  const NotificationSettingPage({super.key});

  @override
  State<NotificationSettingPage> createState() =>
      _NotificationSettingPageState();
}

class _NotificationSettingPageState extends State<NotificationSettingPage> {
  static const String _autoCleanupKey = 'notification_auto_cleanup';
  bool _autoCleanup = true;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSetting();
  }

  Future<void> _loadSetting() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _autoCleanup = prefs.getBool(_autoCleanupKey) ?? true;
      _isLoading = false;
    });
  }

  Future<void> _updateAutoCleanup(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_autoCleanupKey, value);
    setState(() {
      _autoCleanup = value;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.chevron_left, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          '알림 설정',
          style: GoogleFonts.k2d(
            fontSize: 20,
            fontWeight: FontWeight.w600,
            color: Colors.black,
          ),
        ),
      ),
      body: _isLoading
          ? const Center(
              child: CircularProgressIndicator(
                color: Color(0xFF27005D),
              ),
            )
          : Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF5F1FF),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '3일 지난 알림 자동 삭제',
                                style: GoogleFonts.k2d(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w600,
                                  color: const Color(0xFF1D0523),
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                '활성화하면 3일이 지난 처리 완료 알림은\n자동으로 삭제됩니다.',
                                style: GoogleFonts.k2d(
                                  fontSize: 13,
                                  color: Colors.grey[600],
                                ),
                              ),
                            ],
                          ),
                        ),
                        Switch(
                          value: _autoCleanup,
                          onChanged: _updateAutoCleanup,
                          activeColor: const Color(0xFF9400FF),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}

