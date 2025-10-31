import 'package:flutter/widgets.dart';

class FullButton extends StatelessWidget {
  final String text;
  final Function onTap;
  const FullButton(
      {super.key, required this.text, required this.onTap});
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
        onTap: () => onTap(),
        child: Column(
          children: [
            Container(
              width: 333,
              height: 55,
              child: Stack(
                children: [
                  Positioned(
                    left: 0,
                    top: 0,
                    child: Container(
                      width: 333,
                      height: 55,
                      decoration: ShapeDecoration(
                        shape: RoundedRectangleBorder(
                          side: BorderSide(width: 2, color: Color.fromRGBO(39, 0, 93, 1.0)),
                          borderRadius: BorderRadius.circular(15),
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    left: 79,
                    top: 16,
                    child: SizedBox(
                      width: 171,
                      height: 22,
                      child: Text(
                        text,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: Color.fromRGBO(39, 0, 93, 1.0),
                          fontSize: 16,
                          fontFamily: 'Pretendard',
                          fontWeight: FontWeight.w600,
                          height: 0.09,
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
