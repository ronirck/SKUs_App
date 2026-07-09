import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/updates/domain/extract_target.dart';

void main() {
  group('edge cases', () {
    test('no marker defaults to "all"', () {
      expect(extractTarget('Just a plain body.'), 'all');
    });

    test('an unrecognized target value defaults to "all"', () {
      expect(extractTarget('<!-- APP_TARGET: superadmin -->'), 'all');
    });
  });

  group('happy path', () {
    test('extracts a recognized target, case-insensitively', () {
      expect(extractTarget('<!-- APP_TARGET: admin -->'), 'admin');
      expect(extractTarget('<!-- APP_TARGET: USER -->'), 'user');
      expect(extractTarget('<!-- APP_TARGET: All -->'), 'all');
    });
  });
}
