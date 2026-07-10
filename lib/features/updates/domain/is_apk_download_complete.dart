/// Valida que el APK descargado esté completo comparando contra el tamaño
/// del asset publicado en GitHub. Sin tamaño de referencia solo se exige que
/// el archivo no esté vacío.
bool isApkDownloadComplete({required int actualBytes, int? expectedBytes}) {
  if (actualBytes <= 0) return false;
  if (expectedBytes == null || expectedBytes <= 0) return true;
  return actualBytes == expectedBytes;
}
