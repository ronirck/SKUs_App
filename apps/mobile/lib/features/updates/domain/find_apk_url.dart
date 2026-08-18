/// Busca el primer asset .apk entre los assets de un release de GitHub y
/// retorna su URL de descarga directa, o null si no hay ninguno adjunto.
String? findApkUrl(List<dynamic> assets) {
  for (final asset in assets) {
    final name = asset['name'] as String? ?? '';
    if (name.endsWith('.apk')) {
      return asset['browser_download_url'] as String?;
    }
  }
  return null;
}
