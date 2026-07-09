import 'quiz_item.dart';
import 'quiz_round.dart';

/// Decouples the quiz engine from persistence. La partida demo del
/// onboarding (Fase 1) usa [NoopGameResultRecorder]; los modos reales
/// (Fase 3) usan una implementación que escribe en `resultados_codex` /
/// `errores_partida`, encolando localmente si no hay red.
abstract class GameResultRecorder {
  Future<void> recordAnswer({
    required QuizRound round,
    required QuizItem selected,
    required bool correct,
  });

  Future<void> recordSessionEnd({
    required String tipoJuego,
    required String sede,
    required int dificultad,
    required int totalRounds,
    required int correctCount,
    required Duration duracion,
  });
}

class NoopGameResultRecorder implements GameResultRecorder {
  const NoopGameResultRecorder();

  @override
  Future<void> recordAnswer({
    required QuizRound round,
    required QuizItem selected,
    required bool correct,
  }) async {}

  @override
  Future<void> recordSessionEnd({
    required String tipoJuego,
    required String sede,
    required int dificultad,
    required int totalRounds,
    required int correctCount,
    required Duration duracion,
  }) async {}
}
