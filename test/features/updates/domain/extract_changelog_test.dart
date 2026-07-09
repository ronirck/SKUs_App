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

  group('role-specific blocks', () {
    const bodyConBloquesPorRol = '''
<!-- APP_CHANGELOG_USER_START -->
- Mensaje para usuarios
<!-- APP_CHANGELOG_USER_END -->

<!-- APP_CHANGELOG_ADMIN_START -->
- Mensaje para admins
<!-- APP_CHANGELOG_ADMIN_END -->
''';

    test('picks the block matching the role', () {
      expect(extractChangelog(bodyConBloquesPorRol, role: 'user'), ['Mensaje para usuarios']);
      expect(extractChangelog(bodyConBloquesPorRol, role: 'admin'), ['Mensaje para admins']);
    });

    test('role without a specific block falls back to the generic one', () {
      const body = '<!-- APP_CHANGELOG_START -->\n- Genérico\n<!-- APP_CHANGELOG_END -->';
      expect(extractChangelog(body, role: 'admin'), ['Genérico']);
    });

    test('generic block coexisting with role blocks is ignored for that role', () {
      const body = '''
<!-- APP_CHANGELOG_START -->
- Genérico
<!-- APP_CHANGELOG_END -->
<!-- APP_CHANGELOG_ADMIN_START -->
- Solo admins
<!-- APP_CHANGELOG_ADMIN_END -->
''';
      expect(extractChangelog(body, role: 'admin'), ['Solo admins']);
      expect(extractChangelog(body, role: 'user'), ['Genérico']);
    });

    test('no role given keeps the legacy behavior (generic block only)', () {
      expect(extractChangelog(bodyConBloquesPorRol), isEmpty);
    });
  });
}
