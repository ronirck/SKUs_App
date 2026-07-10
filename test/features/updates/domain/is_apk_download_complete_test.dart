import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/updates/domain/is_apk_download_complete.dart';

void main() {
  group('isApkDownloadComplete', () {
    test('archivo vacío nunca es válido, ni siquiera sin referencia', () {
      expect(isApkDownloadComplete(actualBytes: 0), isFalse);
      expect(isApkDownloadComplete(actualBytes: 0, expectedBytes: 0), isFalse);
    });

    test('tamaño distinto al esperado es incompleto', () {
      expect(isApkDownloadComplete(actualBytes: 99, expectedBytes: 100), isFalse);
      expect(isApkDownloadComplete(actualBytes: 101, expectedBytes: 100), isFalse);
    });

    test('sin tamaño de referencia basta con que no esté vacío', () {
      expect(isApkDownloadComplete(actualBytes: 1), isTrue);
      expect(isApkDownloadComplete(actualBytes: 1, expectedBytes: -1), isTrue);
    });

    test('tamaño exacto es completo', () {
      expect(isApkDownloadComplete(actualBytes: 100, expectedBytes: 100), isTrue);
    });
  });
}
