class QuizItem {
  const QuizItem({required this.code, required this.name, this.mnemotecnia, this.groupKey});

  final String code;
  final String name;
  final String? mnemotecnia;

  /// Agrupa elementos "cercanos" (mismo padre en la jerarquía) para priorizar
  /// distractores didácticos. `null` significa que este tipo no tiene padre
  /// (categorías) — sin agrupación posible.
  final String? groupKey;

  @override
  bool operator ==(Object other) => other is QuizItem && other.code == code;

  @override
  int get hashCode => code.hashCode;
}
