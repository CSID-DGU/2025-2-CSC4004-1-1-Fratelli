import 'package:flutter/widgets.dart';
import 'package:google_fonts/google_fonts.dart';

class TextButton extends StatelessWidget {
  final String text;
  final Function onTap;
  final double fontSize;
  const TextButton(
      {super.key, required this.text, required this.onTap, this.fontSize=17});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
        onTap: () => onTap(),
        child: Container(
          color: Color.fromARGB(0, 148, 0, 255),
          padding: EdgeInsets.all(2),
          child: Text(
            text,
            textAlign: TextAlign.center,
            style: GoogleFonts.k2d(
              color: Color.fromRGBO(136, 86, 204, 1),
              fontSize: fontSize,
              fontWeight: FontWeight.w500,
              height: 0.08,
            ),
          ),
        ));
  }
}
