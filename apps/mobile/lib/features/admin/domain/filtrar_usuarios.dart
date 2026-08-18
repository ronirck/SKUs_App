import '../data/admin_repository.dart';
import 'is_nuevo_registro.dart';

/// Filtra la lista de usuarios del admin por nombre/apellido, antigüedad
/// (nuevo/antiguo) y sede. Cualquier filtro en `null`/vacío no restringe.
List<AdminUserSummary> filtrarUsuarios(
  List<AdminUserSummary> usuarios, {
  String busqueda = '',
  bool? soloNuevos,
  String? sede,
  DateTime? now,
}) {
  final query = busqueda.trim().toLowerCase();
  return usuarios.where((u) {
    if (query.isNotEmpty) {
      final nombreCompleto = '${u.nombre ?? ''} ${u.apellido ?? ''}'.toLowerCase();
      if (!nombreCompleto.contains(query)) return false;
    }
    if (soloNuevos != null && isNuevoRegistro(u.creadoEn, now: now) != soloNuevos) {
      return false;
    }
    if (sede != null && sede.isNotEmpty && u.sede != sede) {
      return false;
    }
    return true;
  }).toList();
}
