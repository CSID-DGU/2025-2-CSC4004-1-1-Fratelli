import 'package:flutter/material.dart';

// 점선 구분선을 그리기 위한 CustomPainter
class DottedLinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF1D0523)
      ..strokeWidth = 1;

    const dashHeight = 4;
    const dashSpace = 4;
    double startY = 0;

    while (startY < size.height) {
      canvas.drawLine(
        Offset(0, startY),
        Offset(0, startY + dashHeight),
        paint,
      );
      startY += dashHeight + dashSpace;
    }
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}

class UploadStatistics extends StatelessWidget {
  final int photoCount;
  final int videoCount;

  const UploadStatistics({
    super.key,
    required this.photoCount,
    required this.videoCount,
  });

  @override
  Widget build(BuildContext context) {
    // 화면 너비에서 양쪽 여백을 뺀 크기 계산
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding = 24.0; // 양쪽 여백
    final containerWidth = screenWidth - (horizontalPadding * 2);
    
    return Container(
      width: containerWidth,
      height: 118,
      margin: EdgeInsets.symmetric(horizontal: horizontalPadding),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: const Color.fromRGBO(39, 0, 93, 1),
          width: 1,
        ),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // 사진 섹션
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.photo,
                  size: 24,
                  color: const Color(0xFF27005D), // 어두운 보라색
                ),
                const SizedBox(height: 8),
                const Text(
                  '사진',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Color(0xFF1D0523),
                    fontSize: 13,
                    fontFamily: 'K2D',
                    fontWeight: FontWeight.w500,
                    height: 1.69,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  photoCount.toString(),
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Color(0xFF9400FF), // 밝은 보라색
                    fontSize: 13,
                    fontFamily: 'K2D',
                    fontWeight: FontWeight.w500,
                    height: 1.69,
                  ),
                ),
              ],
            ),
          ),
          // 구분선 (점선)
          CustomPaint(
            painter: DottedLinePainter(),
            size: const Size(1, 80),
          ),
          // 동영상 섹션
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.video_camera_back,
                  size: 24,
                  color: const Color(0xFF27005D), // 어두운 보라색
                ),
                const SizedBox(height: 8),
                const Text(
                  '동영상',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Color(0xFF1D0523),
                    fontSize: 13,
                    fontFamily: 'K2D',
                    fontWeight: FontWeight.w500,
                    height: 1.69,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  videoCount.toString(),
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Color(0xFF9400FF), // 밝은 보라색
                    fontSize: 13,
                    fontFamily: 'K2D',
                    fontWeight: FontWeight.w500,
                    height: 1.69,
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