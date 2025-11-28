import 'package:flutter/material.dart';

enum UploadStatus { uploading, done, error }
enum UploadType { image, video }

class UploadProgressButton extends StatelessWidget {
  final String fileName;
  final String fileSize;
  final double progress;
  final String? progressStatus;
  final UploadStatus status;
  final UploadType type;
  final VoidCallback? onDownload;
  final VoidCallback? onDelete;

  const UploadProgressButton({
    super.key,
    required this.fileName,
    required this.fileSize,
    required this.progress,
    this.progressStatus,
    required this.status,
    required this.type,
    this.onDownload,
    this.onDelete,
  });

  String _getProgressStatusText() {
    if (progressStatus != null && progressStatus!.isNotEmpty) {
      final progressPercent = (progress * 100).round();
      
      if (type == UploadType.video) {
        if (progressPercent == 30) {
          return '음성 처리 중';
        } else if (progressPercent == 70) {
          return '영상 처리 중';
        } else if (progressPercent == 80) {
          return '병합 중';
        }
      }
      
      return progressStatus!;
    }
    
    final progressPercent = (progress * 100).round();
    if (progressPercent == 0) {
      return '시작';
    } else if (progressPercent == 100) {
      return '완료';
    } else {
      return '${progressPercent}%';
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding = 20.0;
    final containerWidth = screenWidth - (horizontalPadding * 2);

    IconData leftIcon;
    switch (type) {
      case UploadType.image:
        leftIcon = Icons.image_outlined;
        break;
      case UploadType.video:
        leftIcon = Icons.videocam_outlined;
        break;
    }

    Widget? progressText;
    if (status == UploadStatus.uploading) {
      progressText = Text(
        _getProgressStatusText(),
        style: const TextStyle(
          color: Color(0xFF1D0523),
          fontSize: 10,
          fontFamily: 'K2D',
          fontWeight: FontWeight.w500,
        ),
      );
    }

    Widget? rightIcon;
    if (status == UploadStatus.done) {
      rightIcon = IconButton(
        icon: const Icon(
          Icons.download_outlined,
          color: Color(0xFF1D0523),
          size: 20,
        ),
        onPressed: onDownload,
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
          Positioned(
            left: 14,
            top: status == UploadStatus.uploading ? 14 : 21, 
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

          Positioned(
            left: 52,
            right: 70,
            top: status == UploadStatus.uploading ? 15 : 22,
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    fileName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Color(0xFF1D0523),
                      fontSize: 13,
                      fontFamily: 'K2D',
                      fontWeight: FontWeight.w500,
                      height: 1.69,
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  fileSize,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Color(0xFFA2A2A2),
                    fontSize: 10,
                    fontFamily: 'K2D',
                    fontWeight: FontWeight.w500,
                    height: 2.20,
                  ),
                ),
              ],
            ),
          ),

          if (progressText != null)
            Positioned(
              right: 14,
              top: 20,
              child: progressText,
            ),

          if (rightIcon != null)
            Positioned(
              right: 8,
              top: 14,
              child: rightIcon,
            ),

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
