import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../core/database/app_database.dart';

/// Suma minutos de sesión a `session_logs` (upsert diario por
/// `(usuario_id, fecha)`). Si falla (sin red), encola el incremento en
/// [PendingSessionTime] en vez de perderlo; [flushPending] reintenta.
class SessionTimeSyncer {
  SessionTimeSyncer(this._client, this._db);

  final SupabaseClient _client;
  final AppDatabase _db;

  Future<void> addDuration({
    required String usuarioId,
    required DateTime fechaLocal,
    required int segundos,
  }) async {
    if (segundos <= 0) return;
    try {
      await _upsert(usuarioId: usuarioId, fechaLocal: fechaLocal, segundos: segundos);
    } catch (_) {
      await _db.into(_db.pendingSessionTime).insert(
            PendingSessionTimeCompanion.insert(
              usuarioId: usuarioId,
              fecha: _dateOnly(fechaLocal),
              duracionSegundos: segundos,
              creadoEn: DateTime.now(),
            ),
          );
    }
  }

  Future<void> flushPending() async {
    final pending = await _db.select(_db.pendingSessionTime).get();
    for (final row in pending) {
      try {
        await _upsert(usuarioId: row.usuarioId, fechaLocal: row.fecha, segundos: row.duracionSegundos);
        await (_db.delete(_db.pendingSessionTime)..where((t) => t.id.equals(row.id))).go();
      } catch (_) {
        // Sigue sin red o falló de nuevo — se reintenta la próxima vez.
      }
    }
  }

  Future<void> _upsert({
    required String usuarioId,
    required DateTime fechaLocal,
    required int segundos,
  }) async {
    final fecha = _dateOnly(fechaLocal);
    final fechaStr =
        '${fecha.year.toString().padLeft(4, '0')}-${fecha.month.toString().padLeft(2, '0')}-${fecha.day.toString().padLeft(2, '0')}';

    final existing = await _client
        .from('session_logs')
        .select('id, duracion_segundos')
        .eq('usuario_id', usuarioId)
        .eq('fecha', fechaStr)
        .maybeSingle();

    if (existing == null) {
      await _client.from('session_logs').insert({
        'usuario_id': usuarioId,
        'fecha': fechaStr,
        'duracion_segundos': segundos,
      });
    } else {
      await _client.from('session_logs').update({
        'duracion_segundos': (existing['duracion_segundos'] as int) + segundos,
        'actualizado_en': DateTime.now().toUtc().toIso8601String(),
      }).eq('id', existing['id'] as String);
    }
  }

  DateTime _dateOnly(DateTime d) => DateTime(d.year, d.month, d.day);
}
