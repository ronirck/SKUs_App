import 'dart:math';

import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/game/domain/quiz_engine.dart';
import 'package:skus_app/features/game/domain/quiz_item.dart';
import 'package:skus_app/features/game/domain/quiz_type_source.dart';

const _categorias = [
  QuizItem(code: '01', name: 'Tornillos'),
  QuizItem(code: '02', name: 'Tuercas'),
  QuizItem(code: '03', name: 'Cables'),
  QuizItem(code: '04', name: 'Pilas'),
  QuizItem(code: '05', name: 'Cintas'),
];

const _productos = [
  QuizItem(code: '01-01-001', name: 'Tornillo 1', groupKey: '01-01'),
  QuizItem(code: '01-01-002', name: 'Tornillo 2', groupKey: '01-01'),
  QuizItem(code: '02-01-001', name: 'Tuerca 1', groupKey: '02-01'),
];

QuizTypeSource _source(String tipo, List<QuizItem> items) =>
    QuizTypeSource(tipoElemento: tipo, items: items);

void main() {
  group('error cases', () {
    test('throws when optionsPerRound is below 2', () {
      expect(
        () => QuizEngine(sources: [_source('categoria', _categorias)], optionsPerRound: 1),
        throwsArgumentError,
      );
    });

    test('throws when there are no sources at all', () {
      expect(() => QuizEngine(sources: []), throwsArgumentError);
    });

    test('throws when a source has fewer than 2 real items (mode unplayable)', () {
      expect(
        () => QuizEngine(sources: [_source('categoria', _categorias.take(1).toList())]),
        throwsArgumentError,
      );
    });
  });

  group('happy path — single source', () {
    test('each round has unique options including the correct answer, capped at optionsPerRound', () {
      final engine = QuizEngine(sources: [_source('categoria', _categorias)], optionsPerRound: 3, random: Random(42));
      final rounds = engine.buildRounds(roundCount: 10);

      for (final round in rounds) {
        expect(round.tipoElemento, 'categoria');
        expect(round.options.length, lessThanOrEqualTo(3));
        expect(round.options.toSet().length, round.options.length, reason: 'options must be unique');
        expect(round.options, contains(round.correctAnswer));
        expect(round.correctAnswer, round.prompt);
      }
    });

    test('roundCount controls how many rounds are produced', () {
      final engine = QuizEngine(sources: [_source('categoria', _categorias)], random: Random(1));
      expect(engine.buildRounds(roundCount: 2).length, 2);
      expect(engine.buildRounds(roundCount: 5).length, 5);
    });

    test('repeats items to fill roundCount when the catalog has fewer than roundCount items', () {
      final engine = QuizEngine(sources: [_source('categoria', _categorias)], random: Random(7));
      final rounds = engine.buildRounds(roundCount: 12);
      final usedCodes = rounds.map((r) => r.correctAnswer.code).toSet();
      expect(usedCodes.length, _categorias.length, reason: 'every item should appear at least once before repeating');
    });

    test('reduces option count instead of inventing codes when the pool is too small', () {
      final engine = QuizEngine(sources: [_source('categoria', _categorias.take(2).toList())], optionsPerRound: 8, random: Random(3));
      final rounds = engine.buildRounds(roundCount: 5);
      for (final round in rounds) {
        expect(round.options.length, 2, reason: 'only 2 real categorias exist, so options reduce to 2');
      }
    });
  });

  group('happy path — multiple sources (contrarreloj)', () {
    test('every round comes from one of the provided sources, with matching tipoElemento', () {
      final engine = QuizEngine(
        sources: [_source('categoria', _categorias), _source('producto', _productos)],
        optionsPerRound: 2,
        random: Random(5),
      );
      final rounds = engine.buildRounds(roundCount: 20);

      expect(rounds.map((r) => r.tipoElemento).toSet(), {'categoria', 'producto'});
      for (final round in rounds) {
        final sourceItems = round.tipoElemento == 'categoria' ? _categorias : _productos;
        expect(sourceItems, contains(round.correctAnswer));
      }
    });
  });
}
