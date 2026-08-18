import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/updates/domain/find_apk_size.dart';

void main() {
  group('findApkSize', () {
    test('sin assets devuelve null', () {
      expect(findApkSize(const []), isNull);
    });

    test('assets sin .apk devuelve null', () {
      expect(
        findApkSize(const [
          {'name': 'notas.txt', 'size': 10},
        ]),
        isNull,
      );
    });

    test('asset .apk sin size devuelve null', () {
      expect(
        findApkSize(const [
          {'name': 'app-release.apk'},
        ]),
        isNull,
      );
    });

    test('devuelve el size del primer .apk', () {
      expect(
        findApkSize(const [
          {'name': 'notas.txt', 'size': 1},
          {'name': 'app-release.apk', 'size': 62161195},
          {'name': 'otro.apk', 'size': 5},
        ]),
        62161195,
      );
    });
  });
}
