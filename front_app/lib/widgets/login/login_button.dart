import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:google_fonts/google_fonts.dart';

class LoginButton extends StatelessWidget {
  final String text;
  final VoidCallback? onTap;
  final IconData? icon;
  const LoginButton({
    super.key, 
    required this.text, 
    this.onTap,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    // 화면 너비에서 양쪽 여백을 뺀 크기 계산
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding = 24.0; // 양쪽 여백
    final buttonWidth = screenWidth - (horizontalPadding * 2);
    
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          SizedBox(
            width: buttonWidth,
            height: 60,
            child: Stack(
              children: [
                Positioned(
                  left: 0,
                  top: 0,
                  child: Container(
                    width: buttonWidth,
                    height: 55,
                    decoration: ShapeDecoration(
                      color: Color.fromRGBO(39, 0, 93, 1),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(15),
                      ),
                      shadows: [
                        BoxShadow(
                          color: Color(0x3F000000),
                          blurRadius: 50,
                          offset: Offset(0, 4),
                          spreadRadius: 0,
                        ),
                      ],
                    ),
                  ),
                ),
                Center(
                  child: Transform.translate(
                    offset: const Offset(0, -2),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (icon != null) ...[
                          Icon(icon, color: Colors.white, size: 24),
                          const SizedBox(width: 8),
                        ],
                        Text(
                          text,
                          textAlign: TextAlign.center,
                          style: GoogleFonts.k2d(
                            color: Colors.white,
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            height: 0.99,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
