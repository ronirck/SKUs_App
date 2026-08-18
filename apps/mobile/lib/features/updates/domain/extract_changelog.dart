RegExp _changelogBlock(String suffix) => RegExp(
      '<!-- APP_CHANGELOG${suffix}_START -->(.*?)<!-- APP_CHANGELOG${suffix}_END -->',
      dotAll: true,
    );

/// Extrae los items del changelog embebidos en el body de un release de
/// GitHub. Si se pasa [role] y existe un bloque específico para ese rol
/// (APP_CHANGELOG_ADMIN_START/END o APP_CHANGELOG_USER_START/END), se usa
/// ese; si no, cae al bloque genérico APP_CHANGELOG_START/END. Sin ningún
/// bloque, retorna una lista vacía (no hay changelog que mostrar).
List<String> extractChangelog(String body, {String? role}) {
  Match? match;
  if (role != null && role.trim().isNotEmpty) {
    match = _changelogBlock('_${role.trim().toUpperCase()}').firstMatch(body);
  }
  match ??= _changelogBlock('').firstMatch(body);
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
