/// Filtra marcas por búsqueda y las ordena: seleccionadas primero, luego
/// alfabéticamente (dentro de cada grupo).
List<String> filtrarYOrdenarMarcas(
  List<String> marcas, {
  required Set<String> seleccionadas,
  String busqueda = '',
}) {
  final query = busqueda.trim().toLowerCase();
  final filtradas = query.isEmpty
      ? marcas
      : marcas.where((m) => m.toLowerCase().contains(query)).toList();

  final ordenadas = [...filtradas]..sort((a, b) {
      final aSel = seleccionadas.contains(a);
      final bSel = seleccionadas.contains(b);
      if (aSel != bSel) return aSel ? -1 : 1;
      return a.toLowerCase().compareTo(b.toLowerCase());
    });
  return ordenadas;
}
