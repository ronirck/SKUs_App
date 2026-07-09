import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/admin/domain/is_nuevo_registro.dart';

void main() {
  final now = DateTime(2026, 7, 12);

  group('edge cases', () {
    test('a creadoEn in the future (clock skew) is never "nuevo"', () {
      expect(isNuevoRegistro(now.add(const Duration(days: 1)), now: now), isFalse);
    });

    test('exactly 7 days old still counts as "nuevo"', () {
      expect(isNuevoRegistro(now.subtract(const Duration(days: 7)), now: now), isTrue);
    });

    test('7 days and 1 second old no longer counts as "nuevo"', () {
      expect(
        isNuevoRegistro(now.subtract(const Duration(days: 7, seconds: 1)), now: now),
        isFalse,
      );
    });

    test('registered exactly now counts as "nuevo"', () {
      expect(isNuevoRegistro(now, now: now), isTrue);
    });
  });

  group('happy path', () {
    test('registered 2 days ago is "nuevo"', () {
      expect(isNuevoRegistro(now.subtract(const Duration(days: 2)), now: now), isTrue);
    });

    test('registered 30 days ago is not "nuevo"', () {
      expect(isNuevoRegistro(now.subtract(const Duration(days: 30)), now: now), isFalse);
    });
  });
}
