import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/catalog/domain/catalog_filters.dart';

void main() {
  group('marcaFilterFor edge cases', () {
    test('empty marcasPermitidas means no filter (all brands), not zero matches', () {
      expect(marcaFilterFor([]), isNull);
    });

    test('non-empty marcasPermitidas returns the same list to filter by', () {
      expect(marcaFilterFor(['Febeca', 'Prisma']), ['Febeca', 'Prisma']);
    });
  });
}
