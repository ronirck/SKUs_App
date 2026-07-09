import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/updates/domain/extract_changelog.dart';

void main() {
  group('edge cases', () {
    test('no markers returns an empty list', () {
      expect(extractChangelog('Just a plain release body.'), isEmpty);
    });

    test('markers present but empty block returns an empty list', () {
      const body = '<!-- APP_CHANGELOG_START -->\n\n<!-- APP_CHANGELOG_END -->';
      expect(extractChangelog(body), isEmpty);
    });
  });

  group('happy path', () {
    test('extracts "- item" lines, stripping the leading dash', () {
      const body = '''
Intro text.

<!-- APP_CHANGELOG_START -->
- Corrige el modo contrarreloj
- Agrega filtros de usuarios
<!-- APP_CHANGELOG_END -->

More text.
''';
      expect(extractChangelog(body), [
        'Corrige el modo contrarreloj',
        'Agrega filtros de usuarios',
      ]);
    });

    test('non-dash lines inside the block are kept as-is', () {
      const body = '<!-- APP_CHANGELOG_START -->\nSin viñeta\n- Con viñeta\n<!-- APP_CHANGELOG_END -->';
      expect(extractChangelog(body), ['Sin viñeta', 'Con viñeta']);
    });
  });
}
