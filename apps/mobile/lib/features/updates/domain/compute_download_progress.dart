/// Progreso de descarga en [0, 1], o null cuando el total es desconocido
/// (respuesta sin Content-Length) — la UI muestra una barra indeterminada.
double? computeDownloadProgress(int receivedBytes, int? totalBytes) {
  if (totalBytes == null || totalBytes <= 0) return null;
  if (receivedBytes <= 0) return 0;
  if (receivedBytes >= totalBytes) return 1;
  return receivedBytes / totalBytes;
}
