import 'package:flutter/widgets.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class FullButton extends StatelessWidget {
  final String text;
  final Function onTap;
  const FullButton(
      {super.key, required this.text, required this.onTap});
  @override
  Widget build(BuildContext context) {
    // 화면 너비에서 양쪽 여백을 뺀 크기 계산
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding = 24.0; // 양쪽 여백
    final buttonWidth = screenWidth - (horizontalPadding * 2);
    
    return GestureDetector(
        onTap: () => onTap(),
        child: Column(
          children: [
            Container(
              width: buttonWidth,
              height: 55,
              child: Stack(
                children: [
                  Positioned(
                    left: 0,
                    top: 0,
                    child: Container(
                      width: buttonWidth,
                      height: 55,
                      decoration: ShapeDecoration(
                        shape: RoundedRectangleBorder(
                          side: BorderSide(width: 1.5, color: Color.fromRGBO(39, 0, 93, 1.0)),
                          borderRadius: BorderRadius.circular(15),
                        ),
                      ),
                    ),
                  ),
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.only(top: 16),
                      child: SizedBox(
                        height: 22,
                        child: Text(
                          text,
                          textAlign: TextAlign.center,
                          style: GoogleFonts.k2d(
                            color: Color.fromRGBO(29, 5, 35, 1),
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            height: 0.09,
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
      ));
  }
}
