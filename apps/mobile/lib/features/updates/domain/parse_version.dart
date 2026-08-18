/// Convierte "v1.2.3" en [1, 2, 3]. Cualquier formato inválido (vacío,
/// no numérico) retorna [0, 0, 0] en vez de lanzar.
List<int> parseVersion(String versionStr) {
  final clean = versionStr.trim().replaceFirst(RegExp('^v', caseSensitive: false), '');
  if (clean.isEmpty) return const [0, 0, 0];

  final parts = <int>[];
  for (final segment in clean.split('.')) {
    final n = int.tryParse(segment.trim());
    if (n == null) return const [0, 0, 0];
    parts.add(n);
  }
  while (parts.length < 3) {
    parts.add(0);
  }
  return parts;
}
