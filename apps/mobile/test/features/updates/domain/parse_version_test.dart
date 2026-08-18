import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/updates/domain/parse_version.dart';

void main() {
  group('edge cases', () {
    test('empty string parses as 0.0.0', () {
      expect(parseVersion(''), [0, 0, 0]);
    });

    test('non-numeric segments parse as 0.0.0, never throw', () {
      expect(parseVersion('abc'), [0, 0, 0]);
      expect(parseVersion('1.x.3'), [0, 0, 0]);
    });

    test('fewer than 3 components are padded with zeros', () {
      expect(parseVersion('v1.2'), [1, 2, 0]);
      expect(parseVersion('5'), [5, 0, 0]);
    });
  });

  group('happy path', () {
    test('leading "v" and surrounding whitespace are stripped', () {
      expect(parseVersion('v1.2.3'), [1, 2, 3]);
      expect(parseVersion('  2.0.0  '), [2, 0, 0]);
    });
  });
}
