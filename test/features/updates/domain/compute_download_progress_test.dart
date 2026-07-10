import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/updates/domain/compute_download_progress.dart';

void main() {
  group('computeDownloadProgress', () {
    test('total desconocido (null) devuelve null', () {
      expect(computeDownloadProgress(100, null), isNull);
    });

    test('total cero o negativo devuelve null', () {
      expect(computeDownloadProgress(100, 0), isNull);
      expect(computeDownloadProgress(100, -5), isNull);
    });

    test('recibido negativo o cero devuelve 0', () {
      expect(computeDownloadProgress(-1, 100), 0);
      expect(computeDownloadProgress(0, 100), 0);
    });

    test('recibido mayor que el total se limita a 1', () {
      expect(computeDownloadProgress(150, 100), 1);
    });

    test('progreso normal es la fracción recibida', () {
      expect(computeDownloadProgress(25, 100), 0.25);
      expect(computeDownloadProgress(100, 100), 1);
    });
  });
}
