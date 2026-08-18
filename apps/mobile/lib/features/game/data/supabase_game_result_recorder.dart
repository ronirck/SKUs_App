import '../domain/game_result_recorder.dart';
import '../domain/quiz_item.dart';
import '../domain/quiz_round.dart';
import 'game_result_payload.dart';
import 'pending_game_results_syncer.dart';

/// Instanciar uno nuevo por partida — acumula cada respuesta hasta
/// [recordSessionEnd], donde arma el resultado completo y se lo entrega a
/// [PendingGameResultsSyncer] (que decide enviarlo o encolarlo sin red).
class SupabaseGameResultRecorder implements GameResultRecorder {
  SupabaseGameResultRecorder(this._syncer, this._userId);

  final PendingGameResultsSyncer _syncer;
  final String _userId;

  final List<Map<String, dynamic>> _interacciones = [];
  final List<FailedItem> _fallos = [];

  @override
  Future<void> recordAnswer({
    required QuizRound round,
    required QuizItem selected,
    required bool correct,
  }) async {
    _interacciones.add({
      'tipo_elemento': round.tipoElemento,
      'prompt_codigo': round.prompt.code,
      'prompt_nombre': round.prompt.name,
      'seleccionado_codigo': selected.code,
      'correcto': correct,
    });
    if (!correct) {
      _fallos.add(FailedItem(
        tipoElemento: round.tipoElemento,
        elementoCodigo: round.correctAnswer.code,
        elementoNombre: round.correctAnswer.name,
        mnemotecnia: round.correctAnswer.mnemotecnia,
      ));
    }
  }

  @override
  Future<void> recordSessionEnd({
    required String tipoJuego,
    required String sede,
    required int dificultad,
    required int totalRounds,
    required int correctCount,
    required Duration duracion,
  }) async {
    final payload = PendingGameResultPayload(
      usuarioId: _userId,
      tipoJuego: tipoJuego,
      aciertos: correctCount,
      fallos: totalRounds - correctCount,
      totalPreguntas: totalRounds,
      duracionSegundos: duracion.inSeconds,
      sede: sede,
      configuracion: {'dificultad': dificultad},
      detalleInteracciones: _interacciones,
      errores: _fallos,
    );
    await _syncer.sendOrQueue(payload);
  }
}
