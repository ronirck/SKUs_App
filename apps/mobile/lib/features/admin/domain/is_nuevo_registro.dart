/// Un usuario se marca "Nuevo" en la lista de admin durante los 7 días
/// posteriores a su registro. [now] es inyectable para pruebas.
bool isNuevoRegistro(DateTime creadoEn, {DateTime? now}) {
  final reference = now ?? DateTime.now();
  final antiguedad = reference.difference(creadoEn);
  return !antiguedad.isNegative && antiguedad <= const Duration(days: 7);
}
