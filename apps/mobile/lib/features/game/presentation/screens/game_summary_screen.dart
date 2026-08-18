import 'package:flutter/material.dart';

import '../../domain/quiz_round.dart';

class GameSummaryScreen extends StatelessWidget {
  const GameSummaryScreen({
    super.key,
    required this.aciertos,
    required this.fallos,
    required this.duracion,
    required this.fallosRounds,
  });

  final int aciertos;
  final int fallos;
  final Duration duracion;
  final List<QuizRound> fallosRounds;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Resultado')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _Stat(label: 'Aciertos', value: '$aciertos', color: Colors.green),
                _Stat(label: 'Fallos', value: '$fallos', color: Colors.red),
                _Stat(label: 'Tiempo', value: _formatDuration(duracion)),
              ],
            ),
            const SizedBox(height: 32),
            if (fallosRounds.isNotEmpty) ...[
              const Text('Para reforzar:', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ...fallosRounds.map(
                (round) => ListTile(
                  leading: const Icon(Icons.close, color: Colors.red),
                  title: Text('${round.correctAnswer.code} — ${round.correctAnswer.name}'),
                  subtitle: round.correctAnswer.mnemotecnia != null
                      ? Text(round.correctAnswer.mnemotecnia!)
                      : null,
                ),
              ),
            ],
            const SizedBox(height: 24),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Volver a Desafíos'),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDuration(Duration d) {
    final minutes = d.inMinutes;
    final seconds = d.inSeconds % 60;
    return '$minutes:${seconds.toString().padLeft(2, '0')}';
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value, this.color});

  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
        Text(label),
      ],
    );
  }
}
