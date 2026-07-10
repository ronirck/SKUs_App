import 'dart:io';

import 'package:http/http.dart' as http;

import '../domain/is_apk_download_complete.dart';

enum ApkDownloadError {
  /// No se pudo ni iniciar la conexión (sin red, DNS caído).
  sinConexion,

  /// El servidor respondió pero no con el APK (HTTP distinto de 200).
  respuestaInvalida,

  /// La descarga arrancó pero se cortó a mitad.
  interrumpida,

  /// El archivo llegó con un tamaño distinto al publicado.
  archivoDanado,
}

class ApkDownloadException implements Exception {
  const ApkDownloadException(this.error);

  final ApkDownloadError error;

  @override
  String toString() => 'ApkDownloadException($error)';
}

/// Descarga el APK de una actualización por streaming, reportando progreso.
/// Ante cualquier falla borra el archivo parcial y lanza
/// [ApkDownloadException] con la causa — nunca deja un APK a medias en disco.
class ApkDownloader {
  ApkDownloader(this._client);

  final http.Client _client;

  Future<File> download({
    required String url,
    required File destination,
    int? expectedBytes,
    void Function(int received, int? total)? onProgress,
  }) async {
    http.StreamedResponse response;
    try {
      // GitHub responde 302 hacia el CDN; http sigue redirects por defecto.
      response = await _client.send(http.Request('GET', Uri.parse(url)));
    } on Exception {
      throw const ApkDownloadException(ApkDownloadError.sinConexion);
    }

    if (response.statusCode != 200) {
      throw const ApkDownloadException(ApkDownloadError.respuestaInvalida);
    }

    final total = response.contentLength ?? expectedBytes;
    var received = 0;
    final sink = destination.openWrite();
    try {
      await for (final chunk in response.stream) {
        sink.add(chunk);
        received += chunk.length;
        onProgress?.call(received, total);
      }
      await sink.flush();
      await sink.close();
    } catch (_) {
      await sink.close();
      await _deleteQuietly(destination);
      throw const ApkDownloadException(ApkDownloadError.interrumpida);
    }

    if (!isApkDownloadComplete(actualBytes: received, expectedBytes: expectedBytes)) {
      await _deleteQuietly(destination);
      throw const ApkDownloadException(ApkDownloadError.archivoDanado);
    }
    return destination;
  }

  Future<void> _deleteQuietly(File file) async {
    try {
      if (await file.exists()) await file.delete();
    } catch (_) {
      // Borrar el parcial es best-effort; el error original es el que importa.
    }
  }
}
