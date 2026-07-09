final _changelogBlock = RegExp(
  '<!-- APP_CHANGELOG_START -->(.*?)<!-- APP_CHANGELOG_END -->',
  dotAll: true,
);

/// Extrae los items del changelog embebidos en el body de un release de
/// GitHub entre los marcadores APP_CHANGELOG_START/END. Sin el bloque,
/// retorna una lista vacía (no hay changelog que mostrar).
List<String> extractChangelog(String body) {
  final match = _changelogBlock.firstMatch(body);
  if (match == null) return const [];

  final block = match.group(1)!.trim();
  if (block.isEmpty) return const [];

  final items = <String>[];
  for (final rawLine in block.split('\n')) {
    final line = rawLine.trim();
    if (line.isEmpty) continue;
    items.add(line.startsWith('- ') ? line.substring(2).trim() : line);
  }
  return items;
}
