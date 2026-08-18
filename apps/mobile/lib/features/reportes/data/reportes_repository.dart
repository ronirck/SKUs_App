import 'package:supabase_flutter/supabase_flutter.dart';

class ReporteError {
  const ReporteError({
    required this.id,
    required this.usuarioId,
    required this.mensaje,
    required this.estatus,
    required this.creadoEn,
  });

  factory ReporteError.fromMap(Map<String, dynamic> map) => ReporteError(
        id: map['id'] as String,
        usuarioId: map['usuario_id'] as String,
        mensaje: map['mensaje'] as String,
        estatus: map['estatus'] as String,
        creadoEn: DateTime.parse(map['creado_en'] as String),
      );

  final String id;
  final String usuarioId;
  final String mensaje;
  final String estatus;
  final DateTime creadoEn;
}

/// 'sin_revisar' → 'en_revision' → 'pendiente' → 'resuelto' (CHECK constraint
/// en `reportes_error.estatus`).
const kEstatusReporte = ['sin_revisar', 'en_revision', 'pendiente', 'resuelto'];

class ReportesRepository {
  ReportesRepository(this._client);

  final SupabaseClient _client;

  /// Cualquier usuario puede reportar un problema — no se encola sin red
  /// (a diferencia de partidas/tiempo de sesión): es una acción manual y
  /// deliberada, no algo que se pierda por estar en curso.
  Future<void> submitReport(String mensaje) async {
    final userId = _client.auth.currentUser!.id;
    await _client.from('reportes_error').insert({
      'usuario_id': userId,
      'mensaje': mensaje,
      'estatus': 'sin_revisar',
    });
  }

  Future<List<ReporteError>> fetchAllReports() async {
    final rows =
        await _client.from('reportes_error').select().order('creado_en', ascending: false);
    return rows.map(ReporteError.fromMap).toList();
  }

  Future<void> updateEstatus({required String id, required String estatus}) async {
    await _client.from('reportes_error').update({
      'estatus': estatus,
      'actualizado_en': DateTime.now().toUtc().toIso8601String(),
    }).eq('id', id);
  }
}
