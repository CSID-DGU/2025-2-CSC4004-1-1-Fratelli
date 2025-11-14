import 'package:flutter/material.dart';

class FilterButton extends StatelessWidget {
  final String title;
  final VoidCallback onTap;
  final bool isSelected;

  const FilterButton({
    super.key,
    required this.title,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onTap(),
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 6, horizontal: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF27005D) : Colors.white,
          border: Border.all(
            color: isSelected ? const Color(0xFF27005D) :const Color(0xFF27005D),
          ),
          borderRadius: BorderRadius.circular(8),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: Color(0x55000000),
                    blurRadius: 20,
                    offset: Offset(4, 10),
                    spreadRadius: -10,
                  ),
                ]
              : [],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.center, // 가운데 정렬
          children: [
            Text(
              title,
              textAlign: TextAlign.center, // 가운데 정렬
              style: TextStyle(
                color: isSelected ? Colors.white : const Color(0xFF27005D),
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
