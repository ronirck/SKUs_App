import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/admin/domain/calcular_efectividad.dart';

void main() {
  group('edge cases', () {
    test('zero total preguntas returns 0, never divides by zero', () {
      expect(calcularEfectividad(aciertos: 0, totalPreguntas: 0), 0);
    });

    test('all correct returns 100', () {
      expect(calcularEfectividad(aciertos: 10, totalPreguntas: 10), 100);
    });

    test('all incorrect returns 0', () {
      expect(calcularEfectividad(aciertos: 0, totalPreguntas: 10), 0);
    });
  });

  group('happy path', () {
    test('partial correctness computes the right percentage', () {
      expect(calcularEfectividad(aciertos: 3, totalPreguntas: 4), 75);
    });
  });
}
