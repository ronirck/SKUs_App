import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/catalog/domain/cache_version.dart';

void main() {
  group('edge cases', () {
    test('no local cache (never synced) always needs refresh', () {
      final remote = const CacheVersion(configVersion: 1, versionDatos: 'v1');
      expect(needsRefresh(local: null, remote: remote), isTrue);
    });

    test('same configVersion but different versionDatos still needs refresh', () {
      final local = const CacheVersion(configVersion: 3, versionDatos: 'v1');
      final remote = const CacheVersion(configVersion: 3, versionDatos: 'v2');
      expect(needsRefresh(local: local, remote: remote), isTrue);
    });

    test('same versionDatos but different configVersion still needs refresh', () {
      final local = const CacheVersion(configVersion: 3, versionDatos: 'v1');
      final remote = const CacheVersion(configVersion: 4, versionDatos: 'v1');
      expect(needsRefresh(local: local, remote: remote), isTrue);
    });
  });

  group('happy path', () {
    test('identical versions do not need refresh', () {
      final local = const CacheVersion(configVersion: 5, versionDatos: 'v9');
      final remote = const CacheVersion(configVersion: 5, versionDatos: 'v9');
      expect(needsRefresh(local: local, remote: remote), isFalse);
    });
  });
}
