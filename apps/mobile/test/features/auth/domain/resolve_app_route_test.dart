import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/auth/domain/app_route.dart';
import 'package:skus_app/features/auth/domain/user_profile.dart';

UserProfile _profile({
  String? nombre,
  String? apellido,
  required EstadoUsuario estado,
  bool onboardingCompletado = false,
}) {
  return UserProfile(
    id: 'user-1',
    nombre: nombre,
    apellido: apellido,
    estado: estado,
    onboardingCompletado: onboardingCompletado,
    rol: 'user',
  );
}

void main() {
  group('edge cases', () {
    test('no session routes to login regardless of profile', () {
      expect(
        resolveAppRoute(hasSession: false, profile: null),
        AppRoute.login,
      );
    });

    test('session without a profile yet (trigger race) routes to loadingProfile, not a crash', () {
      expect(
        resolveAppRoute(hasSession: true, profile: null),
        AppRoute.loadingProfile,
      );
    });

    test('pendiente with only nombre filled (apellido missing) still needs name confirmation', () {
      final profile = _profile(nombre: 'Ana', apellido: null, estado: EstadoUsuario.pendiente);
      expect(
        resolveAppRoute(hasSession: true, profile: profile),
        AppRoute.needsNameConfirmation,
      );
    });

    test('pendiente with blank-string nombre/apellido still needs name confirmation', () {
      final profile = _profile(nombre: '  ', apellido: '  ', estado: EstadoUsuario.pendiente);
      expect(
        resolveAppRoute(hasSession: true, profile: profile),
        AppRoute.needsNameConfirmation,
      );
    });

    test('aprobado with onboarding not completed still skips onboarding (re-entry of approved user)', () {
      final profile = _profile(
        nombre: 'Ana',
        apellido: 'Pérez',
        estado: EstadoUsuario.aprobado,
        onboardingCompletado: false,
      );
      expect(
        resolveAppRoute(hasSession: true, profile: profile),
        AppRoute.approved,
      );
    });
  });

  group('happy paths', () {
    test('rechazado routes to rejected', () {
      final profile = _profile(nombre: 'Ana', apellido: 'Pérez', estado: EstadoUsuario.rechazado);
      expect(resolveAppRoute(hasSession: true, profile: profile), AppRoute.rejected);
    });

    test('pendiente + confirmed name + onboarding not done routes to needsOnboarding', () {
      final profile = _profile(
        nombre: 'Ana',
        apellido: 'Pérez',
        estado: EstadoUsuario.pendiente,
        onboardingCompletado: false,
      );
      expect(resolveAppRoute(hasSession: true, profile: profile), AppRoute.needsOnboarding);
    });

    test('pendiente + confirmed name + onboarding done routes to waitingApproval', () {
      final profile = _profile(
        nombre: 'Ana',
        apellido: 'Pérez',
        estado: EstadoUsuario.pendiente,
        onboardingCompletado: true,
      );
      expect(resolveAppRoute(hasSession: true, profile: profile), AppRoute.waitingApproval);
    });

    test('aprobado with confirmed name routes to approved', () {
      final profile = _profile(nombre: 'Ana', apellido: 'Pérez', estado: EstadoUsuario.aprobado);
      expect(resolveAppRoute(hasSession: true, profile: profile), AppRoute.approved);
    });
  });
}
