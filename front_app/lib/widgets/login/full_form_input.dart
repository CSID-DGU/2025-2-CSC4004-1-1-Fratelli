import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class FullFormInput extends StatelessWidget {
  final String text;
  final String text2;
  final bool isPassword;
  final TextEditingController? controller;
  final Widget? prefixIcon;
  final String? Function(String?)? validator;

  const FullFormInput({
    super.key,
    required this.text,
    required this.text2,
    this.isPassword = false,
    this.controller,
    this.prefixIcon,
    this.validator,
  });
  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding = 24.0; 
    final inputWidth = screenWidth - (horizontalPadding * 2);
    return FormField<String>(
      validator: validator,
      builder: (fieldState) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: inputWidth,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    text,
                    textAlign: TextAlign.left,
                    style: GoogleFonts.k2d(
                      color: Color.fromRGBO(29, 5, 35, 1),
                      fontSize: 20,
                      fontWeight: FontWeight.w500,
                      height: 1.2,
                    ),
                  ),
                  const SizedBox(height: 16),
                  // 입력 필드 (에러 텍스트는 숨김)
                  Container(
                    width: inputWidth,
                    decoration: ShapeDecoration(
                      shape: RoundedRectangleBorder(
                        side: const BorderSide(
                          width: 1.3,
                          color: Color.fromRGBO(39, 0, 93, 1),
                        ),
                        borderRadius: BorderRadius.circular(15),
                      ),
                    ),
                    child: TextField(
                      controller: controller,
                      obscureText: isPassword,
                      onChanged: (value) => fieldState.didChange(value),
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
                ],
              ),
            ),
            if (fieldState.hasError) ...[
              const SizedBox(height: 6),
              Padding(
                padding: EdgeInsets.only(left: horizontalPadding),
                child: Text(
                  fieldState.errorText ?? '',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.red[700],
                  ),
                ),
              ),
            ],
          ],
        );
      },
    );
  }
}