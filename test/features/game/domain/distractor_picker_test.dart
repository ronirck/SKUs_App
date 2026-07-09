import 'dart:math';

import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/game/domain/distractor_picker.dart';
import 'package:skus_app/features/game/domain/quiz_item.dart';

void main() {
  group('edge cases', () {
    test('never returns the correct answer itself as a distractor', () {
      const correct = QuizItem(code: '01', name: 'A');
      final pool = [correct, const QuizItem(code: '02', name: 'B')];
      final result = pickDistractors(correct: correct, pool: pool, wanted: 5, random: Random(1));
      expect(result, isNot(contains(correct)));
    });

    test('returns fewer than wanted when the pool has too few real items, never invents', () {
      const correct = QuizItem(code: '01', name: 'A');
      final pool = [correct, const QuizItem(code: '02', name: 'B')];
      final result = pickDistractors(correct: correct, pool: pool, wanted: 7, random: Random(1));
      expect(result.length, 1);
      expect(result.single.code, '02');
    });

    test('never duplicates a distractor within the same round', () {
      const correct = QuizItem(code: '01', name: 'A');
      final pool = [
        correct,
        const QuizItem(code: '02', name: 'B'),
        const QuizItem(code: '02', name: 'B duplicate entry'),
      ];
      final result = pickDistractors(correct: correct, pool: pool, wanted: 5, random: Random(1));
      expect(result.map((i) => i.code).toSet().length, result.length);
    });

    test('prioritizes same-groupKey items over the rest of the pool', () {
      const correct = QuizItem(code: '04-01', name: 'A', groupKey: '04');
      final near = const QuizItem(code: '04-02', name: 'B', groupKey: '04');
      final far = const QuizItem(code: '05-01', name: 'C', groupKey: '05');
      final result = pickDistractors(
        correct: correct,
        pool: [correct, near, far],
        wanted: 1,
        random: Random(1),
      );
      expect(result, [near]);
    });

    test('falls back to far pool when near pool is insufficient', () {
      const correct = QuizItem(code: '04-01', name: 'A', groupKey: '04');
      final far1 = const QuizItem(code: '05-01', name: 'C', groupKey: '05');
      final far2 = const QuizItem(code: '06-01', name: 'D', groupKey: '06');
      final result = pickDistractors(
        correct: correct,
        pool: [correct, far1, far2],
        wanted: 2,
        random: Random(1),
      );
      expect(result.toSet(), {far1, far2});
    });
  });

  group('happy path', () {
    test('returns exactly wanted distractors when the pool is large enough', () {
      const correct = QuizItem(code: '01', name: 'A');
      final pool = [
        correct,
        const QuizItem(code: '02', name: 'B'),
        const QuizItem(code: '03', name: 'C'),
        const QuizItem(code: '04', name: 'D'),
      ];
      final result = pickDistractors(correct: correct, pool: pool, wanted: 3, random: Random(1));
      expect(result.length, 3);
    });
  });
}
