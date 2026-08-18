import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/catalog/data/fetch_all_pages.dart';

List<Map<String, dynamic>> _rows(int from, int count) =>
    List.generate(count, (i) => {'n': from + i});

void main() {
  group('fetchAllPages', () {
    test('propaga el error del servidor sin tragarlo', () async {
      expect(
        fetchAllPages((from, to) async => throw Exception('sin red')),
        throwsException,
      );
    });

    test('un error en la segunda página también propaga', () async {
      expect(
        fetchAllPages((from, to) async {
          if (from > 0) throw Exception('se cayó la red a mitad');
          return _rows(0, 3);
        }, pageSize: 3),
        throwsException,
      );
    });

    test('resultado vacío devuelve lista vacía', () async {
      final result = await fetchAllPages((from, to) async => []);
      expect(result, isEmpty);
    });

    test('una sola página corta no pide más páginas', () async {
      final rangos = <(int, int)>[];
      final result = await fetchAllPages((from, to) async {
        rangos.add((from, to));
        return _rows(from, 2);
      }, pageSize: 5);
      expect(result, hasLength(2));
      expect(rangos, [(0, 4)]);
    });

    test('concatena varias páginas completas más el resto', () async {
      const total = 12;
      final rangos = <(int, int)>[];
      final result = await fetchAllPages((from, to) async {
        rangos.add((from, to));
        final count = (from + 5 <= total) ? 5 : total - from;
        return _rows(from, count);
      }, pageSize: 5);
      expect(result, hasLength(total));
      expect(result.first['n'], 0);
      expect(result.last['n'], total - 1);
      expect(rangos, [(0, 4), (5, 9), (10, 14)]);
    });

    test('total exactamente múltiplo del tamaño de página termina igual', () async {
      const total = 10;
      final result = await fetchAllPages((from, to) async {
        final count = (from + 5 <= total) ? 5 : total - from;
        return _rows(from, count);
      }, pageSize: 5);
      expect(result, hasLength(total));
    });
  });
}
