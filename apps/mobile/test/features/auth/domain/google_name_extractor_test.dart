import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/auth/domain/google_name_extractor.dart';

void main() {
  group('edge cases', () {
    test('null metadata returns empty strings, not a crash', () {
      final result = extractNameFromGoogleMetadata(null);
      expect(result.nombre, '');
      expect(result.apellido, '');
    });

    test('empty full_name and no given/family name returns empty strings', () {
      final result = extractNameFromGoogleMetadata({'full_name': '   '});
      expect(result.nombre, '');
      expect(result.apellido, '');
    });

    test('full_name with a single word has no apellido', () {
      final result = extractNameFromGoogleMetadata({'full_name': 'Madonna'});
      expect(result.nombre, 'Madonna');
      expect(result.apellido, '');
    });
  });

  group('happy paths', () {
    test('prefers given_name/family_name when present', () {
      final result = extractNameFromGoogleMetadata({
        'given_name': 'Ana',
        'family_name': 'Pérez',
        'full_name': 'Ignorada Ignorada',
      });
      expect(result.nombre, 'Ana');
      expect(result.apellido, 'Pérez');
    });

    test('falls back to splitting full_name on the first space', () {
      final result = extractNameFromGoogleMetadata({'full_name': 'Ana María Pérez Gómez'});
      expect(result.nombre, 'Ana');
      expect(result.apellido, 'María Pérez Gómez');
    });
  });
}
