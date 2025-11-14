import 'package:flutter/material.dart';

// 커스텀 네비게이션 바
class CustomNavigationBar extends StatelessWidget {
  final int currentIndex;
  final Function(int) onTap;

  const CustomNavigationBar({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: 60,
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: const Color(0xFFD0D6E1),
            blurRadius: 20,
            offset: const Offset(0, -2),
            spreadRadius: 0,
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          // 히스토리 (왼쪽)
          Expanded(
            child: _NavItem(
              label: '히스토리',
              icon: Icons.access_time_outlined,
              isSelected: currentIndex == 0,
              onTap: () => onTap(0),
            ),
          ),
          // 홈/업로드 (중앙 - 보라색 원형 배경)
          _HomeNavItem(
            isSelected: currentIndex == 1,
            onTap: () => onTap(1),
          ),
          // 마이페이지 (오른쪽)
          Expanded(
            child: _NavItem(
              label: '마이페이지',
              icon: Icons.person_outline,
              isSelected: currentIndex == 2,
              onTap: () => onTap(2),
            ),
          ),
        ],
      ),
    );
  }
}

// 개별 네비 아이템 (히스토리, 마이페이지)
class _NavItem extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  const _NavItem({
    super.key,
    required this.label,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final iconColor = isSelected 
        ? const Color(0xFF27005D) 
        : const Color(0xFFA2A2A2);
    final textColor = isSelected 
        ? const Color(0xFF27005D) 
        : const Color(0xFFA2A2A2);
    
    return InkWell(
      onTap: onTap,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            icon,
            size: 24,
            color: iconColor,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: textColor,
              fontSize: 12,
              fontWeight: FontWeight.w500,
              fontFamily: 'K2D',
            ),
          ),
        ],
      ),
    );
  }
}

// 홈 네비 아이템 (중앙 - 보라색 원형 배경, 약간 위로 올라온 형태)
class _HomeNavItem extends StatelessWidget {
  final bool isSelected;
  final VoidCallback onTap;

  const _HomeNavItem({
    super.key,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Transform.translate(
        offset: const Offset(0, -16), // 위로 약간 올림
        child: Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            color: const Color(0xFF27005D),
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF27005D).withOpacity(0.3),
                blurRadius: 8,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: const Icon(
            Icons.home,
            color: Colors.white,
            size: 28,
          ),
        ),
      ),
    );
  }
}
