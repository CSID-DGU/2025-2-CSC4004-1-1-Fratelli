import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class MenuItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final VoidCallback onTap;

  const MenuItem({
    super.key,
    required this.icon,
    required this.title,
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
          children: [
            Icon(
              icon,
              size: 24,
              color: const Color(0xFF1D0523),
            ),
            const SizedBox(width: 12),
            Text(
              title,
              style: GoogleFonts.k2d(
                fontSize: 15,
                fontWeight: FontWeight.w500,
                color: const Color(0xFF1D0523),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
