import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// 서브타이틀이 있는 메뉴 아이템 위젯
class MenuItemWithSubtitle extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const MenuItemWithSubtitle({
    super.key,
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              icon,
              size: 24,
              color: const Color(0xFF1D0523),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: GoogleFonts.k2d(
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                      color: const Color(0xFF1D0523),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: GoogleFonts.k2d(
                      fontSize: 13,
                      fontWeight: FontWeight.w400,
                      color: const Color(0xFF9400FF),
                    ),
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

