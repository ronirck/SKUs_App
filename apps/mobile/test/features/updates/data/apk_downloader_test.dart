import 'dart:async';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:skus_app/features/updates/data/apk_downloader.dart';

void main() {
  late Directory tempDir;

  setUp(() async {
    tempDir = await Directory.systemTemp.createTemp('apk_downloader_test');
  });

  tearDown(() async {
    if (await tempDir.exists()) await tempDir.delete(recursive: true);
  });

  File destino() => File('${tempDir.path}${Platform.pathSeparator}app.apk');

  MockClient clienteStreaming(Stream<List<int>> Function() body, {int status = 200}) {
    return MockClient.streaming((request, _) async {
      return http.StreamedResponse(body(), status);
    });
  }

  group('ApkDownloader', () {
    test('error al conectar lanza sinConexion y no crea archivo', () async {
      final client = MockClient.streaming((request, body) async {
        throw const SocketException('sin red');
      });
      await expectLater(
        ApkDownloader(client).download(url: 'https://x/apk', destination: destino()),
        throwsA(isA<ApkDownloadException>()
            .having((e) => e.error, 'error', ApkDownloadError.sinConexion)),
      );
      expect(destino().existsSync(), isFalse);
    });

    test('HTTP distinto de 200 lanza respuestaInvalida y no crea archivo', () async {
      final client = clienteStreaming(() => const Stream.empty(), status: 404);
      await expectLater(
        ApkDownloader(client).download(url: 'https://x/apk', destination: destino()),
        throwsA(isA<ApkDownloadException>()
            .having((e) => e.error, 'error', ApkDownloadError.respuestaInvalida)),
      );
      expect(destino().existsSync(), isFalse);
    });

    test('stream que se corta lanza interrumpida y borra el parcial', () async {
      Stream<List<int>> cortado() async* {
        yield [1, 2, 3];
        throw const SocketException('se cayó la red');
      }

      final client = clienteStreaming(cortado);
      await expectLater(
        ApkDownloader(client).download(url: 'https://x/apk', destination: destino()),
        throwsA(isA<ApkDownloadException>()
            .having((e) => e.error, 'error', ApkDownloadError.interrumpida)),
      );
      expect(destino().existsSync(), isFalse);
    });

    test('tamaño final distinto al esperado lanza archivoDanado y borra', () async {
      final client = clienteStreaming(() => Stream.value([1, 2, 3]));
      await expectLater(
        ApkDownloader(client).download(
          url: 'https://x/apk',
          destination: destino(),
          expectedBytes: 10,
        ),
        throwsA(isA<ApkDownloadException>()
            .having((e) => e.error, 'error', ApkDownloadError.archivoDanado)),
      );
      expect(destino().existsSync(), isFalse);
    });

    test('descarga completa escribe el archivo y reporta progreso creciente', () async {
      final client = clienteStreaming(() => Stream.fromIterable([
            [1, 2, 3],
            [4, 5],
          ]));
      final progreso = <int>[];
      final file = await ApkDownloader(client).download(
        url: 'https://x/apk',
        destination: destino(),
        expectedBytes: 5,
        onProgress: (received, _) => progreso.add(received),
      );
      expect(file.existsSync(), isTrue);
      expect(file.lengthSync(), 5);
      expect(progreso, [3, 5]);
    });
  });
}
