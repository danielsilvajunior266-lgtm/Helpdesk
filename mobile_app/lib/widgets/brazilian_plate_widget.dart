import 'package:flutter/material.dart';

enum PlateSize { sm, md, lg }

class BrazilianPlateWidget extends StatelessWidget {
  final String rawPlate;
  final PlateSize size;

  const BrazilianPlateWidget({
    super.key,
    required this.rawPlate,
    this.size = PlateSize.md,
  });

  bool get isMercosul {
    final clean = rawPlate.replaceAll(RegExp(r'[^A-Za-z0-9]'), '').toUpperCase();
    if (clean.length == 7) {
      final fourth = clean[3];
      final fifth = clean[4];
      return RegExp(r'[0-9]').hasMatch(fourth) && RegExp(r'[A-Z]').hasMatch(fifth);
    }
    return false;
  }

  String get formattedPlate {
    final clean = rawPlate.replaceAll(RegExp(r'[^A-Za-z0-9]'), '').toUpperCase();
    if (clean.length == 7) {
      if (isMercosul) {
        return clean; // Ex: ABC1D23
      } else {
        return '${clean.substring(0, 3)}-${clean.substring(3)}'; // Ex: ABC-1234
      }
    }
    return rawPlate.toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    if (isMercosul) {
      return _buildMercosulPlate();
    } else {
      return _buildAntigoPlate();
    }
  }

  Widget _buildMercosulPlate() {
    double width;
    double height;
    double headerHeight;
    double fontSize;
    double headerFontSize;
    double flagSize;

    switch (size) {
      case PlateSize.sm:
        width = 96;
        height = 36;
        headerHeight = 11;
        fontSize = 13;
        headerFontSize = 6.5;
        flagSize = 8;
        break;
      case PlateSize.md:
        width = 128;
        height = 48;
        headerHeight = 15;
        fontSize = 18;
        headerFontSize = 8.5;
        flagSize = 11;
        break;
      case PlateSize.lg:
        width = 160;
        height = 60;
        headerHeight = 19;
        fontSize = 23;
        headerFontSize = 10.5;
        flagSize = 14;
        break;
    }

    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: const Color(0xFF003399), width: 1.8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.45),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(4),
        child: Column(
          children: [
            // Top Blue Header
            Container(
              height: headerHeight,
              padding: const EdgeInsets.symmetric(horizontal: 4),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF002277), Color(0xFF003399), Color(0xFF0044CC)],
                  begin: Alignment.centerLeft,
                  end: Alignment.centerRight,
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // Mercosul Emblem Symbol
                  Row(
                    children: [
                      Container(
                        width: flagSize * 0.7,
                        height: flagSize * 0.7,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.yellow, width: 0.8),
                        ),
                        child: const Center(
                          child: Icon(Icons.star, size: 4, color: Colors.yellow),
                        ),
                      ),
                    ],
                  ),
                  // BRASIL Text
                  Text(
                    'BRASIL',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: headerFontSize,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1.2,
                    ),
                  ),
                  // Brasil Flag Mini
                  Container(
                    width: flagSize * 1.3,
                    height: flagSize * 0.9,
                    decoration: BoxDecoration(
                      color: const Color(0xFF009B3A),
                      borderRadius: BorderRadius.circular(1.5),
                    ),
                    child: Center(
                      child: Container(
                        width: flagSize * 0.7,
                        height: flagSize * 0.5,
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEDF00),
                          borderRadius: BorderRadius.circular(1),
                        ),
                        child: Center(
                          child: Container(
                            width: flagSize * 0.35,
                            height: flagSize * 0.35,
                            decoration: const BoxDecoration(
                              color: Color(0xFF002776),
                              shape: BoxShape.circle,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            // Characters body
            Expanded(
              child: Container(
                color: Colors.white,
                alignment: Alignment.center,
                child: Text(
                  formattedPlate,
                  style: TextStyle(
                    color: const Color(0xFF111111),
                    fontSize: fontSize,
                    fontWeight: FontWeight.w900,
                    fontFamily: 'monospace',
                    letterSpacing: 2.0,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAntigoPlate() {
    double width;
    double height;
    double headerHeight;
    double fontSize;
    double headerFontSize;

    switch (size) {
      case PlateSize.sm:
        width = 96;
        height = 36;
        headerHeight = 10;
        fontSize = 12.5;
        headerFontSize = 6.5;
        break;
      case PlateSize.md:
        width = 128;
        height = 48;
        headerHeight = 13;
        fontSize = 17;
        headerFontSize = 8.5;
        break;
      case PlateSize.lg:
        width = 160;
        height = 60;
        headerHeight = 16;
        fontSize = 21;
        headerFontSize = 10.5;
        break;
    }

    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: const Color(0xFFC0C7CE),
        borderRadius: BorderRadius.circular(5),
        border: Border.all(color: const Color(0xFF4A5568), width: 1.8),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.45),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(3.5),
        child: Column(
          children: [
            // Top Header
            Container(
              height: headerHeight,
              alignment: Alignment.center,
              decoration: const BoxDecoration(
                color: Color(0xFF8A939E),
                border: Border(bottom: BorderSide(color: Color(0xFF4A5568), width: 0.8)),
              ),
              child: Text(
                'BRASIL',
                style: TextStyle(
                  color: const Color(0xFF1E232A),
                  fontSize: headerFontSize,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.5,
                ),
              ),
            ),
            // Characters body
            Expanded(
              child: Container(
                color: const Color(0xFFB8BFC6),
                alignment: Alignment.center,
                child: Text(
                  formattedPlate,
                  style: TextStyle(
                    color: const Color(0xFF15181C),
                    fontSize: fontSize,
                    fontWeight: FontWeight.w900,
                    fontFamily: 'monospace',
                    letterSpacing: 1.5,
                    shadows: [
                      Shadow(
                        color: Colors.white.withValues(alpha: 0.8),
                        offset: const Offset(0.5, 0.5),
                        blurRadius: 0,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
