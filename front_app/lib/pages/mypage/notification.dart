import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class NotificationItem {
  final String title;
  final String date; // yyyy-MM-dd 형식 저장

  NotificationItem({required this.title, required this.date});

  Map<String, dynamic> toJson() => {'title': title, 'date': date};
  factory NotificationItem.fromJson(Map<String, dynamic> json) =>
      NotificationItem(title: json['title'], date: json['date']);
}

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  List<NotificationItem> notifications = [];
  bool isDeleteMode = false; // 삭제 모드 여부
  Set<int> selectedIndices = {}; // 선택된 항목의 인덱스 집합
  bool isAllSelected = false;

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getStringList('notifications') ?? [];

    // 저장된 문자열 리스트를 NotificationItem으로 복원
    List<NotificationItem> loaded = saved
        .map((e) => NotificationItem.fromJson(jsonDecode(e)))
        .toList();

    // 3일 지난 알림 삭제
    final now = DateTime.now();
    loaded = loaded.where((n) {
      final date = DateTime.parse(n.date);
      return now.difference(date).inDays <= 3;
    }).toList();

    // 최신 상태 저장
    await prefs.setStringList(
        'notifications', loaded.map((n) => jsonEncode(n.toJson())).toList());

    setState(() => notifications = loaded);
  }

  // 날짜 형식을 yyyy.MM.dd로 변환
  String _formatDate(String dateStr) {
    final date = DateTime.parse(dateStr);
    return '${date.year}.${date.month.toString().padLeft(2, '0')}.${date.day.toString().padLeft(2, '0')}';
  }

  // 삭제 모드 진입
  void _enterDeleteMode() {
    setState(() {
      isDeleteMode = true;
      selectedIndices.clear();
      isAllSelected = false;
    });
  }

  // 삭제 모드 종료
  void _exitDeleteMode() {
    setState(() {
      isDeleteMode = false;
      selectedIndices.clear();
      isAllSelected = false;
    });
  }

  // 전체 선택/해제 토글
  void _toggleSelectAll() {
    setState(() {
      if (isAllSelected) {
        selectedIndices.clear();
        isAllSelected = false;
      } else {
        selectedIndices =
            Set.from(List.generate(notifications.length, (i) => i));
        isAllSelected = true;
      }
    });
  }

  // 개별 항목 선택/해제 토글
  void _toggleItemSelection(int index) {
    setState(() {
      if (selectedIndices.contains(index)) {
        selectedIndices.remove(index);
        isAllSelected = false;
      } else {
        selectedIndices.add(index);
        // 모든 항목이 선택되었는지 확인
        if (selectedIndices.length == notifications.length) {
          isAllSelected = true;
        }
      }
    });
  }

  // 선택된 항목 삭제
  Future<void> _deleteSelected() async {
    if (selectedIndices.isEmpty) {
      return;
    }

    List<NotificationItem> updatedNotifications = [];
    for (int i = 0; i < notifications.length; i++) {
      if (!selectedIndices.contains(i)) {
        updatedNotifications.add(notifications[i]);
      }
    }

    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList('notifications',
        updatedNotifications.map((n) => jsonEncode(n.toJson())).toList());

    setState(() {
      notifications = updatedNotifications;
      selectedIndices.clear();
      isAllSelected = false;
      isDeleteMode = false;
    });
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              GestureDetector(
                onTap: () {
                  if (isDeleteMode) {
                    _exitDeleteMode();
                  } else {
                    Navigator.of(context).pop();
                  }
                },
                child: const Icon(
                  Icons.chevron_left,
                  color: Colors.black,
                  size: 28,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  const Text(
                    '알림',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.black,
                    ),
                  ),
                  const Spacer(),
                  if (isDeleteMode)
                    Column(
                      mainAxisSize: MainAxisSize.min,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        GestureDetector(
                          onTap: _toggleSelectAll,
                          child: Container(
                            width: 16,
                            height: 16,
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              color: isAllSelected
                                  ? const Color(0xFF9400FF)
                                  : Colors.transparent,
                              border: Border.all(
                                color: isAllSelected
                                    ? const Color(0xFF9400FF)
                                    : Colors.grey[400]!,
                                width: 2,
                              ),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: isAllSelected
                                ? const Icon(
                                    Icons.check,
                                    color: Colors.white,
                                    size: 12,
                                  )
                                : null,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '전체',
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey[400],
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            Flexible(
              flex: isDeleteMode ? 8 : 1,
              child: notifications.isEmpty
                  ? const Center(
                      child: Text(
                        '최근 3일 내 알림이 없습니다',
                        style: TextStyle(
                          fontSize: 16,
                          color: Color(0xFF9400FF),
                        ),
                      ),
                    )
                  : Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: ListView.builder(
                        padding: EdgeInsets.only(
                          bottom: isDeleteMode ? 60 : 16,
                        ),
                        itemCount: notifications.length,
                        itemBuilder: (context, index) {
                          final item = notifications[index];
                          final isSelected = selectedIndices.contains(index);

                          return GestureDetector(
                            onLongPress: () {
                              if (!isDeleteMode) {
                                _enterDeleteMode();
                                _toggleItemSelection(index);
                              }
                            },
                            child: Padding(
                              padding: EdgeInsets.only(
                                bottom: isDeleteMode ? 8 : 16,
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    width: 20,
                                    height: 20,
                                    decoration: const BoxDecoration(
                                      color: Color(0xFF27005D),
                                      shape: BoxShape.circle,
                                    ),
                                    child: const Icon(
                                      Icons.notifications,
                                      color: Colors.white,
                                      size: 15,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          item.title,
                                          style: const TextStyle(
                                            fontSize: 16,
                                            color: Colors.black,
                                          ),
                                        ),
                                        const SizedBox(height: 2),
                                        Text(
                                          _formatDate(item.date),
                                          style: TextStyle(
                                            fontSize: 14,
                                            color: Colors.deepPurple[300],
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  if (isDeleteMode) ...[
                                    const SizedBox(width: 12),
                                    GestureDetector(
                                      onTap: () =>
                                          _toggleItemSelection(index),
                                      child: Container(
                                        width: 16,
                                        height: 16,
                                        alignment: Alignment.center,
                                        decoration: BoxDecoration(
                                          color: isSelected
                                              ? const Color(0xFF9400FF)
                                              : Colors.transparent,
                                          border: Border.all(
                                            color: isSelected
                                                ? const Color(0xFF9400FF)
                                                : Colors.grey,
                                            width: 2,
                                          ),
                                          borderRadius:
                                              BorderRadius.circular(4),
                                        ),
                                        child: isSelected
                                            ? const Icon(
                                                Icons.check,
                                                color: Colors.white,
                                                size: 12,
                                              )
                                            : null,
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
            ),
            if (isDeleteMode)
              Flexible(
                flex: 2,
                child: Padding(
                  padding: const EdgeInsets.only(top: 0, bottom: 16),
                  child: Center(
                  child: GestureDetector(
                    onTap: selectedIndices.isEmpty ? null : _deleteSelected,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.delete,
                          color: selectedIndices.isEmpty
                              ? Colors.grey[400]
                              : const Color(0xFF27005D),
                          size: 25,
                        ),
                        Text(
                          '삭제',
                          style: TextStyle(
                            fontSize: 13,
                            color: selectedIndices.isEmpty
                                ? Colors.grey[400]
                                : const Color(0xFF27005D),
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
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
