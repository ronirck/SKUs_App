import 'user_profile.dart';

enum AppRoute {
  login,
  loadingProfile,
  rejected,
  needsNameConfirmation,
  needsOnboarding,
  waitingApproval,
  approved,
}

/// Pure boot-time routing decision. No I/O, no framework dependency — testable
/// in isolation. [profile] is null only while a session exists but the
/// profile row created by the backend trigger hasn't been read yet (a
/// transient race, not an error).
AppRoute resolveAppRoute({required bool hasSession, required UserProfile? profile}) {
  if (!hasSession) return AppRoute.login;
  if (profile == null) return AppRoute.loadingProfile;

  switch (profile.estado) {
    case EstadoUsuario.rechazado:
      return AppRoute.rejected;
    case EstadoUsuario.aprobado:
      return AppRoute.approved;
    case EstadoUsuario.pendiente:
      if (!profile.nombreApellidoConfirmado) return AppRoute.needsNameConfirmation;
      if (!profile.onboardingCompletado) return AppRoute.needsOnboarding;
      return AppRoute.waitingApproval;
  }
}
