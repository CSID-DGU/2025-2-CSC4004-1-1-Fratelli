import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';

class FileUploadButton extends StatefulWidget {
  final void Function(List<PlatformFile> files)? onFilesSelected;

  const FileUploadButton({super.key, this.onFilesSelected});

  @override
  State<FileUploadButton> createState() => _FileSelectButtonState();
}

class _FileSelectButtonState extends State<FileUploadButton> {
  bool _isLoading = false;

  Future<void> _pickFiles() async {
    setState(() => _isLoading = true);

    final result = await FilePicker.platform.pickFiles(
      allowMultiple: true,
      type: FileType.custom,
      allowedExtensions: [
        // 비디오
        'mp4', 'mov', 'mkv', 'avi', 'webm',
        // 이미지
        'jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp',
      ],
    );

    setState(() => _isLoading = false);

    if (result != null && widget.onFilesSelected != null) {
      widget.onFilesSelected!(result.files);
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalPadding = 20.0; 
    final containerWidth = screenWidth - (horizontalPadding * 2);

    return Container(
      width: containerWidth,
      height: 207,
      margin: EdgeInsets.symmetric(horizontal: horizontalPadding),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        border: Border.all(
          color: const Color(0xFF27005D),
          width: 2,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: InkWell(
        onTap: _pickFiles,
        borderRadius: BorderRadius.circular(15),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _isLoading
                ? const CircularProgressIndicator(
                    color: Color(0xFF27005D),
                    strokeWidth: 3,
                  )
                : const Icon(
                    Icons.upload_file,
                    size: 40,
                    color: Color(0xFF9400FF),
                  ),
            const SizedBox(height: 16),
            const Text(
              'Select File to Upload',
              style: TextStyle(
                color: Color(0xFF27005D),
                fontSize: 22,
                fontFamily: 'K2D',
                fontWeight: FontWeight.w500,
                height: 1,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              '지원 파일 형식: JPG, JPEG, PNG, MP4, MOV 등',
              style: TextStyle(
                color: Color(0x6827005D),
                fontSize: 12,
                fontFamily: 'K2D',
                fontWeight: FontWeight.w500,
                height: 1.22,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
