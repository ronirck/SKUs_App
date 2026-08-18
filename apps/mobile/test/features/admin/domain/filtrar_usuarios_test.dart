import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/admin/data/admin_repository.dart';
import 'package:skus_app/features/admin/domain/filtrar_usuarios.dart';
import 'package:skus_app/features/auth/domain/user_profile.dart';

final _now = DateTime(2026, 7, 12);

AdminUserSummary _user({
  required String nombre,
  required String apellido,
  required String sede,
  required DateTime creadoEn,
}) {
  return AdminUserSummary(
    usuarioId: '$nombre-$apellido',
    nombre: nombre,
    apellido: apellido,
    estado: EstadoUsuario.aprobado,
    rol: 'user',
    creadoEn: creadoEn,
    sede: sede,
    marcasPermitidas: const [],
    soloInfaltables: false,
    configVersion: 1,
  );
}

void main() {
  final nuevo = _user(
    nombre: 'Ana',
    apellido: 'Pérez',
    sede: 'FEBECA',
    creadoEn: _now.subtract(const Duration(days: 1)),
  );
  final antiguo = _user(
    nombre: 'Luis',
    apellido: 'Gómez',
    sede: 'SILLACA',
    creadoEn: _now.subtract(const Duration(days: 60)),
  );
  final usuarios = [nuevo, antiguo];

  group('edge cases', () {
    test('empty filters return every user unchanged', () {
      expect(filtrarUsuarios(usuarios, now: _now), usuarios);
    });

    test('search is case-insensitive and matches nombre or apellido', () {
      expect(filtrarUsuarios(usuarios, busqueda: 'pérez', now: _now), [nuevo]);
      expect(filtrarUsuarios(usuarios, busqueda: 'GÓMEZ', now: _now), [antiguo]);
    });

    test('a search with no matches returns an empty list, not everyone', () {
      expect(filtrarUsuarios(usuarios, busqueda: 'zzz', now: _now), isEmpty);
    });

    test('soloNuevos=false excludes recently-registered users', () {
      expect(filtrarUsuarios(usuarios, soloNuevos: false, now: _now), [antiguo]);
    });
  });

  group('happy path', () {
    test('soloNuevos=true keeps only recently-registered users', () {
      expect(filtrarUsuarios(usuarios, soloNuevos: true, now: _now), [nuevo]);
    });

    test('sede filters to an exact match', () {
      expect(filtrarUsuarios(usuarios, sede: 'SILLACA', now: _now), [antiguo]);
    });

    test('combined filters narrow down together', () {
      expect(
        filtrarUsuarios(usuarios, busqueda: 'ana', sede: 'FEBECA', soloNuevos: true, now: _now),
        [nuevo],
      );
    });
  });
}
