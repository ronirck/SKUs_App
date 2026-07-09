import 'dart:async';
import 'dart:math';

import 'package:flutter/material.dart';

import '../../domain/game_result_recorder.dart';
import '../../domain/quiz_engine.dart';
import '../../domain/quiz_item.dart';
import '../../domain/quiz_round.dart';
import '../../domain/quiz_type_source.dart';
import 'game_summary_screen.dart';

class GamePlayScreen extends StatefulWidget {
  const GamePlayScreen({
    super.key,
    required this.tipoJuego,
    required this.sources,
    required this.dificultad,
    required this.sede,
    required this.recorder,
    this.timeLimit,
  });

  static const fixedTotalPreguntas = 10;

  /// `null` → modo de 10 preguntas fijas. No nulo → 'contrarreloj': se
  /// responden tantas preguntas como alcance dentro de este tiempo.
  final Duration? timeLimit;

  final String tipoJuego;
  final List<QuizTypeSource> sources;
  final int dificultad;
  final String sede;
  final GameResultRecorder recorder;

  @override
  State<GamePlayScreen> createState() => _GamePlayScreenState();
}

class _GamePlayScreenState extends State<GamePlayScreen> {
  bool get _isContrarreloj => widget.timeLimit != null;

  late final List<QuizRound> _rounds = QuizEngine(
    sources: widget.sources,
    optionsPerRound: widget.dificultad,
    random: Random(),
  ).buildRounds(
    roundCount: _isContrarreloj ? 200 : GamePlayScreen.fixedTotalPreguntas,
  );

  final Stopwatch _stopwatch = Stopwatch()..start();
  final List<QuizRound> _fallosRounds = [];

  Timer? _countdownTimer;
  Duration? _remaining;

  int _currentIndex = 0;
  int _answeredCount = 0;
  int _correctCount = 0;
  QuizItem? _selected;
  bool _finishing = false;

  @override
  void initState() {
    super.initState();
    if (widget.timeLimit != null) {
      _remaining = widget.timeLimit;
      _countdownTimer = Timer.periodic(const Duration(seconds: 1), (_) {
        final next = _remaining! - const Duration(seconds: 1);
        if (next <= Duration.zero) {
          _countdownTimer?.cancel();
          _finish();
        } else {
          setState(() => _remaining = next);
        }
      });
    }
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    super.dispose();
  }

  Future<void> _answer(QuizItem option) async {
    if (_selected != null || _finishing) return;
    final round = _rounds[_currentIndex];
    final correct = option == round.correctAnswer;
    setState(() => _selected = option);

    await widget.recorder.recordAnswer(round: round, selected: option, correct: correct);
    _answeredCount++;
    if (correct) {
      _correctCount++;
    } else {
      _fallosRounds.add(round);
    }

    await Future.delayed(const Duration(milliseconds: 700));
    if (!mounted || _finishing) return;

    if (_isContrarreloj) {
      setState(() {
        _currentIndex = (_currentIndex + 1) % _rounds.length;
        _selected = null;
      });
    } else if (_currentIndex + 1 < _rounds.length) {
      setState(() {
        _currentIndex++;
        _selected = null;
      });
    } else {
      await _finish();
    }
  }

  Future<void> _finish() async {
    if (_finishing) return;
    _finishing = true;
    _countdownTimer?.cancel();
    _stopwatch.stop();
    await widget.recorder.recordSessionEnd(
      tipoJuego: widget.tipoJuego,
      sede: widget.sede,
      dificultad: widget.dificultad,
      totalRounds: _answeredCount,
      correctCount: _correctCount,
      duracion: _stopwatch.elapsed,
    );
    if (!mounted) return;
    Navigator.of(context).pushReplacement(MaterialPageRoute(
      builder: (_) => GameSummaryScreen(
        aciertos: _correctCount,
        fallos: _answeredCount - _correctCount,
        duracion: _stopwatch.elapsed,
        fallosRounds: _fallosRounds,
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final round = _rounds[_currentIndex];
    return Scaffold(
      appBar: AppBar(
        title: Text(
          _isContrarreloj
              ? 'Contrarreloj — ${_remaining!.inSeconds}s'
              : 'Pregunta ${_currentIndex + 1}/${_rounds.length}',
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              LinearProgressIndicator(
                value: _isContrarreloj
                    ? _remaining!.inSeconds / widget.timeLimit!.inSeconds
                    : _currentIndex / _rounds.length,
              ),
              const SizedBox(height: 32),
              Text(
                round.prompt.name,
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              ...round.options.map((option) {
                final isSelected = _selected == option;
                final isCorrect = option == round.correctAnswer;
                Color? color;
                if (_selected != null && isSelected) {
                  color = isCorrect ? Colors.green.shade100 : Colors.red.shade100;
                } else if (_selected != null && isCorrect) {
                  color = Colors.green.shade50;
                }
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: OutlinedButton(
                    style: OutlinedButton.styleFrom(
                      backgroundColor: color,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    onPressed: _selected == null ? () => _answer(option) : null,
                    child: Text(option.code, style: const TextStyle(fontSize: 18)),
                  ),
                );
              }),
              if (_selected != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    _selected == round.correctAnswer
                        ? '¡Correcto!'
                        : 'Incorrecto. El código correcto era ${round.correctAnswer.code}.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: _selected == round.correctAnswer ? Colors.green : Colors.red,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
