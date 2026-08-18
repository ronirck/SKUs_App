import 'quiz_item.dart';

class QuizRound {
  const QuizRound({
    required this.tipoElemento,
    required this.prompt,
    required this.options,
    required this.correctAnswer,
  });

  /// 'categoria' | 'subcategoria' | 'producto' — constante en modos simples,
  /// variable pregunta a pregunta en 'contrarreloj'.
  final String tipoElemento;
  final QuizItem prompt;
  final List<QuizItem> options;
  final QuizItem correctAnswer;
}
