import 'dart:convert';

import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../core/database/app_database.dart';
import 'game_result_payload.dart';

/// Envía un resultado de partida a Supabase; si falla (sin red u otro
/// error), lo encola en [PendingGameResults] en vez de perderlo.
/// [flushPending] reintenta lo encolado — se llama best-effort desde
/// `CatalogGate` al abrir la app (la sincronización robusta con reintentos
/// en segundo plano es Fase 4).
class PendingGameResultsSyncer {
  PendingGameResultsSyncer(this._client, this._db);

  final SupabaseClient _client;
  final AppDatabase _db;

  Future<void> sendOrQueue(PendingGameResultPayload payload) async {
    try {
      await _sendToSupabase(payload);
    } catch (_) {
      await _queueLocally(payload);
    }
  }

  Future<void> flushPending() async {
    final pending = await _db.select(_db.pendingGameResults).get();
    for (final row in pending) {
      try {
        final payload = PendingGameResultPayload(
          usuarioId: row.usuarioId,
          tipoJuego: row.tipoJuego,
          aciertos: row.aciertos,
          fallos: row.fallos,
          totalPreguntas: row.totalPreguntas,
          duracionSegundos: row.duracionSegundos,
          sede: row.sede,
          configuracion: jsonDecode(row.configuracionJson) as Map<String, dynamic>,
          detalleInteracciones:
              (jsonDecode(row.detalleInteraccionesJson) as List).cast<Map<String, dynamic>>(),
          errores: (jsonDecode(row.erroresJson) as List)
              .map((e) => FailedItem.fromJson(e as Map<String, dynamic>))
              .toList(),
        );
        await _sendToSupabase(payload);
        await (_db.delete(_db.pendingGameResults)..where((t) => t.id.equals(row.id))).go();
      } catch (_) {
        // Sigue sin red o falló de nuevo — se reintenta la próxima vez.
      }
    }
  }

  Future<void> _sendToSupabase(PendingGameResultPayload payload) async {
    final resultRow = await _client
        .from('resultados_codex')
        .insert({
          'usuario_id': payload.usuarioId,
          'tipo_juego': payload.tipoJuego,
          'aciertos': payload.aciertos,
          'fallos': payload.fallos,
          'total_preguntas': payload.totalPreguntas,
          'duracion_segundos': payload.duracionSegundos,
          'sede': payload.sede,
          'configuracion': payload.configuracion,
          'detalle_interacciones': payload.detalleInteracciones,
        })
        .select()
        .single();
    final resultadoId = resultRow['id'] as String;

    for (final error in payload.errores) {
      await _upsertError(usuarioId: payload.usuarioId, resultadoId: resultadoId, error: error);
    }
  }

  Future<void> _upsertError({
    required String usuarioId,
    required String resultadoId,
    required FailedItem error,
  }) async {
    final existing = await _client
        .from('errores_partida')
        .select('id, veces_fallado')
        .eq('usuario_id', usuarioId)
        .eq('tipo_elemento', error.tipoElemento)
        .eq('elemento_codigo', error.elementoCodigo)
        .maybeSingle();

    if (existing == null) {
      await _client.from('errores_partida').insert({
        'usuario_id': usuarioId,
        'resultado_id': resultadoId,
        'tipo_elemento': error.tipoElemento,
        'elemento_codigo': error.elementoCodigo,
        'elemento_nombre': error.elementoNombre,
        'mnemotecnia': error.mnemotecnia,
        'veces_fallado': 1,
      });
    } else {
      await _client.from('errores_partida').update({
        'resultado_id': resultadoId,
        'veces_fallado': (existing['veces_fallado'] as int) + 1,
        'elemento_nombre': error.elementoNombre,
        'mnemotecnia': error.mnemotecnia,
      }).eq('id', existing['id'] as String);
    }
  }

  Future<void> _queueLocally(PendingGameResultPayload payload) async {
    await _db.into(_db.pendingGameResults).insert(
          PendingGameResultsCompanion.insert(
            usuarioId: payload.usuarioId,
            tipoJuego: payload.tipoJuego,
            aciertos: payload.aciertos,
            fallos: payload.fallos,
            totalPreguntas: payload.totalPreguntas,
            duracionSegundos: payload.duracionSegundos,
            sede: payload.sede,
            configuracionJson: jsonEncode(payload.configuracion),
            detalleInteraccionesJson: jsonEncode(payload.detalleInteracciones),
            erroresJson: jsonEncode(payload.errores.map((e) => e.toJson()).toList()),
            creadoEn: DateTime.now(),
          ),
        );
  }
}
