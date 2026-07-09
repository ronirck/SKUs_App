/// Pura: decide si un producto coincide con una búsqueda de texto libre
/// (case-insensitive, substring) contra su nombre o cualquiera de sus
/// códigos. Una búsqueda vacía coincide con todo.
bool productoCoincideBusqueda({
  required String nombre,
  required String codigo,
  String? codigoCompleto,
  required String busqueda,
}) {
  final query = busqueda.trim().toLowerCase();
  if (query.isEmpty) return true;
  if (nombre.toLowerCase().contains(query)) return true;
  if (codigo.toLowerCase().contains(query)) return true;
  if (codigoCompleto != null && codigoCompleto.toLowerCase().contains(query)) return true;
  return false;
}
