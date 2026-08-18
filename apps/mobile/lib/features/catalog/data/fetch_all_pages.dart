/// Descarga TODAS las páginas de una consulta remota. Supabase (PostgREST)
/// trunca cualquier respuesta a `db-max-rows` filas (1000 por defecto) aunque
/// no se pida límite, así que una consulta sin paginar sobre `productos`
/// devuelve un catálogo incompleto en silencio.
///
/// [fetchPage] recibe el rango inclusivo (`from`, `to`) y devuelve esa página;
/// se itera hasta recibir una página corta. Los errores de red propagan al
/// llamador (quien decide si son fatales, igual que en `ensureSynced`).
Future<List<Map<String, dynamic>>> fetchAllPages(
  Future<List<Map<String, dynamic>>> Function(int from, int to) fetchPage, {
  int pageSize = 1000,
}) async {
  assert(pageSize > 0);
  final all = <Map<String, dynamic>>[];
  var from = 0;
  while (true) {
    final page = await fetchPage(from, from + pageSize - 1);
    all.addAll(page);
    if (page.length < pageSize) return all;
    from += pageSize;
  }
}
