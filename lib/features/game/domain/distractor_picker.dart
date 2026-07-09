import 'dart:math';

import 'quiz_item.dart';

/// Elige distractores reales para [correct] desde [pool], nunca inventando
/// códigos. Prioridad: primero elementos con el mismo [QuizItem.groupKey]
/// (más didácticos — mismo padre en la jerarquía), luego cualquier otro
/// elemento real del pool. Si no hay suficientes, devuelve menos de [wanted]
/// en vez de repetir o inventar — quien arma la ronda debe reducir las
/// opciones mostradas en consecuencia.
List<QuizItem> pickDistractors({
  required QuizItem correct,
  required List<QuizItem> pool,
  required int wanted,
  required Random random,
}) {
  final candidates = pool.where((item) => item.code != correct.code).toList();

  final near = <QuizItem>[];
  final far = <QuizItem>[];
  for (final candidate in candidates) {
    if (correct.groupKey != null && candidate.groupKey == correct.groupKey) {
      near.add(candidate);
    } else {
      far.add(candidate);
    }
  }
  near.shuffle(random);
  far.shuffle(random);

  final chosen = <QuizItem>[];
  final seenCodes = <String>{};
  for (final candidate in [...near, ...far]) {
    if (chosen.length >= wanted) break;
    if (!seenCodes.add(candidate.code)) continue;
    chosen.add(candidate);
  }
  return chosen;
}
