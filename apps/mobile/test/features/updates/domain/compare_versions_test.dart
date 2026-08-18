import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/updates/domain/compare_versions.dart';

void main() {
  group('edge cases', () {
    test('identical versions are never "newer"', () {
      expect(isNewerVersion('1.2.3', '1.2.3'), isFalse);
    });

    test('a lower latest version is never "newer"', () {
      expect(isNewerVersion('1.0.0', '1.2.3'), isFalse);
    });

    test('an unparsable latest version defaults to 0.0.0 and is never "newer"', () {
      expect(isNewerVersion('not-a-version', '1.0.0'), isFalse);
    });

    test('differing component counts compare correctly (missing = 0)', () {
      expect(isNewerVersion('1.2', '1.1.9'), isTrue);
      expect(isNewerVersion('1.2.0', '1.2'), isFalse);
    });
  });

  group('happy path', () {
    test('a higher patch version is newer', () {
      expect(isNewerVersion('1.2.4', '1.2.3'), isTrue);
    });

    test('a higher major version is newer regardless of minor/patch', () {
      expect(isNewerVersion('2.0.0', '1.9.9'), isTrue);
    });
  });
}
