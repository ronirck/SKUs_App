import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/catalog/domain/producto_busqueda.dart';

void main() {
  group('edge cases', () {
    test('an empty búsqueda matches everything', () {
      expect(
        productoCoincideBusqueda(nombre: 'Tornillo', codigo: 'T-01', busqueda: ''),
        isTrue,
      );
    });

    test('a búsqueda with no match in name or codes returns false', () {
      expect(
        productoCoincideBusqueda(nombre: 'Tornillo', codigo: 'T-01', busqueda: 'zzz'),
        isFalse,
      );
    });

    test('a null codigoCompleto never crashes and is simply skipped', () {
      expect(
        productoCoincideBusqueda(
          nombre: 'Tornillo',
          codigo: 'T-01',
          codigoCompleto: null,
          busqueda: 't-01',
        ),
        isTrue,
      );
    });
  });

  group('happy path', () {
    test('matches case-insensitively against nombre', () {
      expect(
        productoCoincideBusqueda(nombre: 'Tornillo Phillips', codigo: 'X', busqueda: 'PHILLIPS'),
        isTrue,
      );
    });

    test('matches against codigo', () {
      expect(
        productoCoincideBusqueda(nombre: 'Tornillo', codigo: 'AU-01-001', busqueda: 'au-01'),
        isTrue,
      );
    });

    test('matches against codigoCompleto when provided', () {
      expect(
        productoCoincideBusqueda(
          nombre: 'Tornillo',
          codigo: '001',
          codigoCompleto: 'AU-01-001',
          busqueda: 'au-01-001',
        ),
        isTrue,
      );
    });
  });
}
