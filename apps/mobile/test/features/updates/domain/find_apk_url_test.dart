import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/updates/domain/find_apk_url.dart';

void main() {
  group('edge cases', () {
    test('no assets returns null', () {
      expect(findApkUrl(const []), isNull);
    });

    test('assets with no .apk file return null', () {
      final assets = [
        {'name': 'source.zip', 'browser_download_url': 'https://example.com/source.zip'},
      ];
      expect(findApkUrl(assets), isNull);
    });
  });

  group('happy path', () {
    test('returns the download URL of the first .apk asset', () {
      final assets = [
        {'name': 'notes.txt', 'browser_download_url': 'https://example.com/notes.txt'},
        {'name': 'app-release.apk', 'browser_download_url': 'https://example.com/app-release.apk'},
      ];
      expect(findApkUrl(assets), 'https://example.com/app-release.apk');
    });
  });
}
