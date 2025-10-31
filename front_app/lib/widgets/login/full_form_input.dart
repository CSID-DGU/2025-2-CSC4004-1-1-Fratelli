import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class FullFormInput extends StatelessWidget {
  final String text;
  final String text2;
  final bool isPassword;
  final TextEditingController? controller;
  final Widget? prefixIcon;

  const FullFormInput({
    super.key,
    required this.text,
    required this.text2,
    this.isPassword = false,
    this.controller,
    this.prefixIcon,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 333,
          height: 80,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              //라벨 텍스트
              Expanded (
                flex: 1,
                child: Container(
                  child: Text(
                    text,
                    textAlign: TextAlign.left,
                    style: GoogleFonts.k2d(
                      color: Color.fromRGBO(29, 5, 35, 1),
                      fontSize: 20,
                      fontWeight: FontWeight.w500,
                      height: 0.06,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),

              //입력 필드
              Expanded(
                flex: 10,
                child: Container(
                  width:333,
                  height:53,
                  decoration: ShapeDecoration(
                    shape: RoundedRectangleBorder(
                      side: const BorderSide(
                        width: 1,
                        color: Color.fromRGBO(39, 0, 93, 1)
                        ),
                        borderRadius: BorderRadius.circular(15),
                        ),
                        // 그림자 제거
                    ),
                    child: TextField(
                      controller: controller,
                      obscureText: isPassword,
                      decoration: InputDecoration(
                        hintText: text2,
                        hintStyle: GoogleFonts.k2d(
                          color: Color.fromRGBO(140, 140, 140, 1),
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                        ),
                        border: InputBorder.none,
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 20,
                        ),
                        prefixIcon: prefixIcon,
                      ),
                      style: GoogleFonts.k2d(
                        fontSize: 15,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}