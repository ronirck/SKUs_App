import 'dart:math';

import 'distractor_picker.dart';
import 'quiz_item.dart';
import 'quiz_round.dart';
import 'quiz_type_source.dart';

/// Motor de preguntas de opción múltiple, decoupled from persistence and UI.
/// Un solo [QuizTypeSource] arma un modo simple (categorías/subcategorías/
/// productos); varios arman 'contrarreloj' (cada pregunta elige un origen al
/// azar). Reutilizado tal cual por la partida demo del onboarding (Fase 1)
/// con un único origen.
class QuizEngine {
  QuizEngine({required this.sources, this.optionsPerRound = 4, Random? random})
      : _random = random ?? Random() {
    if (optionsPerRound < 2) {
      throw ArgumentError.value(optionsPerRound, 'optionsPerRound', 'Debe ser al menos 2');
    }
    if (sources.isEmpty) {
      throw ArgumentError('Se necesita al menos un origen de preguntas.');
    }
    for (final source in sources) {
      if (source.items.length < 2) {
        throw ArgumentError(
          'El tipo "${source.tipoElemento}" necesita al menos 2 elementos reales para jugar '
          '(hay ${source.items.length}).',
        );
      }
    }
  }

  final List<QuizTypeSource> sources;
  final int optionsPerRound;
  final Random _random;

  List<QuizRound> buildRounds({required int roundCount}) {
    final orders = {
      for (final source in sources)
        source.tipoElemento: (List<QuizItem>.from(source.items)..shuffle(_random)),
    };
    final cursors = {for (final source in sources) source.tipoElemento: 0};

    return List.generate(roundCount, (_) {
      final source = sources[_random.nextInt(sources.length)];
      final order = orders[source.tipoElemento]!;
      final cursor = cursors[source.tipoElemento]!;
      final correct = order[cursor % order.length];
      cursors[source.tipoElemento] = cursor + 1;

      final distractors = pickDistractors(
        correct: correct,
        pool: source.items,
        wanted: optionsPerRound - 1,
        random: _random,
      );
      final options = [correct, ...distractors]..shuffle(_random);

      return QuizRound(
        tipoElemento: source.tipoElemento,
        prompt: correct,
        options: options,
        correctAnswer: correct,
      );
    });
  }
}
