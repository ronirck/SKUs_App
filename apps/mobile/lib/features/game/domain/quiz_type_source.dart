import 'quiz_item.dart';

/// Un origen de preguntas de un tipo (categoría, subcategoría o producto).
/// El modo 'contrarreloj' combina varios; los modos simples usan uno solo.
class QuizTypeSource {
  const QuizTypeSource({required this.tipoElemento, required this.items});

  final String tipoElemento;
  final List<QuizItem> items;
}
