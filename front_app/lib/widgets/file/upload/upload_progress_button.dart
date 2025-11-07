import 'package:flutter/material.dart';

enum UploadStatus { uploading, done, error }
enum UploadType { image, video }

class UploadProgressButton extends StatelessWidget {
  final String fileName;
  final String fileSize;
  final double progress; // 0 ~ 100
  final UploadStatus status;
  final UploadType type;
  final VoidCallback? onPreview;
  final VoidCallback? onDownload;
  final VoidCallback? onDelete;

  const UploadProgressButton({
    super.key,
    required this.fileName,
    required this.fileSize,
    required this.progress,
    required this.status,
    required this.type,
    this.onPreview,
    this.onDownload,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    // 화면 너비에서 양쪽 여백을 뺀 크기 계산
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding = 20.0; // 양쪽 여백
    final containerWidth = screenWidth - (horizontalPadding * 2);

    // 왼쪽 아이콘: 파일 타입
    IconData leftIcon;
    switch (type) {
      case UploadType.image:
        leftIcon = Icons.image_outlined;
        break;
      case UploadType.video:
        leftIcon = Icons.videocam_outlined;
        break;
      default:
        leftIcon = Icons.insert_drive_file_outlined;
    }

    // 오른쪽 퍼센트: 업로드 중일 때만
    Widget? progressText;
    if (status == UploadStatus.uploading) {
      progressText = Text(
        '${(progress * 100).round()}%',
        style: const TextStyle(
          color: Color(0xFF1D0523),
          fontSize: 10,
          fontFamily: 'K2D',
          fontWeight: FontWeight.w500,
        ),
      );
    }

    // 오른쪽 아이콘: 완료 또는 에러일 때만
    Widget? rightIcon;
    if (status == UploadStatus.done) {
      rightIcon = IconButton(
        icon: Icon(
          type == UploadType.image
              ? Icons.remove_red_eye_outlined
              : Icons.download_outlined,
          color: const Color(0xFF1D0523),
          size: 20,
        ),
        onPressed: type == UploadType.image ? onPreview : onDownload,
      );
    } else if (status == UploadStatus.error) {
      rightIcon = IconButton(
        icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 20),
        onPressed: onDelete,
      );
    }

    return Container(
      width: containerWidth,
      height: 66,
      margin: EdgeInsets.symmetric(horizontal: horizontalPadding).copyWith(bottom: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.grey,
          width: 0.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 6,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Stack(
        children: [
          // 아이콘
          Positioned(
            left: 14,
            top: status == UploadStatus.uploading ? 14 : 21, // 업로드 중일 때는 위로
            child: Container(
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Icon(leftIcon, color: const Color(0xFF1D0523), size: 18),
            ),
          ),

          // 파일 이름
          Positioned(
            left: 52,
            top: status == UploadStatus.uploading ? 15 : 22, // 업로드 중일 때는 위로
            child: Text(
              fileName,
              style: const TextStyle(
                color: Color(0xFF1D0523),
                fontSize: 13,
                fontFamily: 'K2D',
                fontWeight: FontWeight.w500,
                height: 1.69,
              ),
            ),
          ),

          // 파일 크기
          Positioned(
            left: 300,
            top: status == UploadStatus.uploading ? 17 : 24, // 업로드 중일 때는 위로
            child: Text(
              fileSize,
              style: const TextStyle(
                color: Color(0xFFA2A2A2),
                fontSize: 10,
                fontFamily: 'K2D',
                fontWeight: FontWeight.w500,
                height: 2.20,
              ),
            ),
          ),

          // 오른쪽 퍼센트 (업로드 중일 때만)
          if (progressText != null)
            Positioned(
              right: 14,
              top: 20,
              child: progressText!,
            ),

          // 오른쪽 아이콘 (완료 또는 에러일 때만)
          if (rightIcon != null)
            Positioned(
              right: 8,
              top: 14,
              child: rightIcon!,
            ),

          // 업로드 진행 바 (진행 중일 때만)
          if (status == UploadStatus.uploading)
            Positioned(
              left: 14,
              right: 14,
              bottom: 10,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: progress,
                  minHeight: 5,
                  backgroundColor: const Color(0xFFECECEC),
                  color: const Color(0xFF1D0523),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
