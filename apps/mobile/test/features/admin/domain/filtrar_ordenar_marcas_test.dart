import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/admin/domain/filtrar_ordenar_marcas.dart';

void main() {
  final marcas = ['Zeta', 'alfa', 'Beta', 'gamma'];

  group('edge cases', () {
    test('empty búsqueda keeps every marca', () {
      expect(
        filtrarYOrdenarMarcas(marcas, seleccionadas: const {}),
        containsAll(marcas),
      );
    });

    test('a búsqueda with no matches returns an empty list', () {
      expect(filtrarYOrdenarMarcas(marcas, seleccionadas: const {}, busqueda: 'zzz'), isEmpty);
    });

    test('búsqueda is case-insensitive', () {
      expect(filtrarYOrdenarMarcas(marcas, seleccionadas: const {}, busqueda: 'ALFA'), ['alfa']);
    });
  });

  group('happy path', () {
    test('sin selección, ordena alfabéticamente sin distinguir mayúsculas', () {
      expect(
        filtrarYOrdenarMarcas(marcas, seleccionadas: const {}),
        ['alfa', 'Beta', 'gamma', 'Zeta'],
      );
    });

    test('las seleccionadas van primero, luego el resto alfabético', () {
      expect(
        filtrarYOrdenarMarcas(marcas, seleccionadas: {'Zeta'}),
        ['Zeta', 'alfa', 'Beta', 'gamma'],
      );
    });

    test('búsqueda y orden por selección se combinan', () {
      expect(
        filtrarYOrdenarMarcas(marcas, seleccionadas: {'gamma'}, busqueda: 'a'),
        ['gamma', 'alfa', 'Beta', 'Zeta'],
      );
    });
  });
}
