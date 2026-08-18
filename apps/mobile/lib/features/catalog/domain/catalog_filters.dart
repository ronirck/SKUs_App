/// Pura: decide qué filtro de marca aplicar a la consulta remota de
/// productos. `null` significa "sin filtro" (traer todas las marcas de la
/// sede) — el caso [marcasPermitidas] vacío, que representa acceso a TODAS
/// las marcas, no una lista sin coincidencias.
List<String>? marcaFilterFor(List<String> marcasPermitidas) {
  if (marcasPermitidas.isEmpty) return null;
  return marcasPermitidas;
}
