/// Busca el primer asset .apk entre los assets de un release de GitHub y
/// retorna su tamaño en bytes, o null si no hay asset o no trae tamaño.
/// Espejo de `find_apk_url.dart`: ambos deben mirar el MISMO asset.
int? findApkSize(List<dynamic> assets) {
  for (final asset in assets) {
    final name = asset['name'] as String? ?? '';
    if (name.endsWith('.apk')) {
      return asset['size'] as int?;
    }
  }
  return null;
}
