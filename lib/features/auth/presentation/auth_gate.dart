import 'dart:async';

import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart' show AuthState;

import '../../../core/theme/app_theme_controller.dart';
import '../../admin/data/admin_repository.dart';
import '../../catalog/data/catalog_repository.dart';
import '../../catalog/presentation/catalog_gate.dart';
import '../../game/data/pending_game_results_syncer.dart';
import '../../reportes/data/reportes_repository.dart';
import '../../session/data/session_time_syncer.dart';
import '../data/auth_repository.dart';
import '../data/profile_repository.dart';
import '../domain/app_route.dart';
import '../domain/google_name_extractor.dart';
import '../domain/user_profile.dart';
import 'screens/loading_profile_screen.dart';
import 'screens/login_screen.dart';
import 'screens/name_confirmation_screen.dart';
import 'screens/onboarding/onboarding_screen.dart';
import 'screens/rejected_screen.dart';
import 'screens/waiting_approval_screen.dart';

/// Máquina de estados de arranque: escucha sesión + perfil y muestra la
/// pantalla correspondiente según [resolveAppRoute].
class AuthGate extends StatefulWidget {
  const AuthGate({
    super.key,
    required this.authRepository,
    required this.profileRepository,
    required this.catalogRepository,
    required this.adminRepository,
    required this.reportesRepository,
    required this.pendingGameResultsSyncer,
    required this.sessionTimeSyncer,
    required this.themeController,
  });

  final AuthRepository authRepository;
  final ProfileRepository profileRepository;
  final CatalogRepository catalogRepository;
  final AdminRepository adminRepository;
  final ReportesRepository reportesRepository;
  final PendingGameResultsSyncer pendingGameResultsSyncer;
  final SessionTimeSyncer sessionTimeSyncer;
  final AppThemeController themeController;

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  UserProfile? _profile;
  StreamSubscription<AuthState>? _authSub;

  @override
  void initState() {
    super.initState();
    _authSub = widget.authRepository.onAuthStateChange.listen((_) => _refresh());
    _refresh();
  }

  @override
  void dispose() {
    _authSub?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    if (widget.authRepository.currentSession == null) {
      if (mounted) setState(() => _profile = null);
      return;
    }

    var profile = await _fetchProfileOrNull();
    // El trigger que crea perfil_usuario corre justo después del login; si
    // la lectura ocurre antes de que termine, reintenta unas pocas veces en
    // vez de tratarlo como un error.
    for (var attempt = 0; attempt < 4 && profile == null; attempt++) {
      await Future.delayed(const Duration(seconds: 1));
      if (!mounted || widget.authRepository.currentSession == null) return;
      profile = await _fetchProfileOrNull();
    }

    if (profile != null) {
      await widget.profileRepository.saveLastKnownProfile(profile);
    } else {
      // Sin red no se puede leer el perfil real; usa el último conocido en
      // vez de quedar atascado en la pantalla de carga (offline-first).
      profile = await widget.profileRepository.loadLastKnownProfile();
    }

    if (!mounted) return;
    setState(() => _profile = profile);
  }

  Future<UserProfile?> _fetchProfileOrNull() async {
    try {
      return await widget.profileRepository.fetchCurrentProfile();
    } catch (e) {
      debugPrint('No se pudo leer perfil_usuario: $e');
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final route = resolveAppRoute(
      hasSession: widget.authRepository.currentSession != null,
      profile: _profile,
    );

    switch (route) {
      case AppRoute.login:
        return LoginScreen(authRepository: widget.authRepository);
      case AppRoute.loadingProfile:
        return const LoadingProfileScreen();
      case AppRoute.rejected:
        return RejectedScreen(authRepository: widget.authRepository);
      case AppRoute.needsNameConfirmation:
        final prefill = extractNameFromGoogleMetadata(widget.authRepository.currentUserMetadata);
        return NameConfirmationScreen(
          profileRepository: widget.profileRepository,
          initialNombre: prefill.nombre,
          initialApellido: prefill.apellido,
          onConfirmed: _refresh,
        );
      case AppRoute.needsOnboarding:
        return OnboardingScreen(
          profileRepository: widget.profileRepository,
          reportesRepository: widget.reportesRepository,
          themeController: widget.themeController,
          profile: _profile!,
          onSignOut: widget.authRepository.signOut,
          onProceed: _refresh,
        );
      case AppRoute.waitingApproval:
        return WaitingApprovalScreen(
          onRefresh: _refresh,
          authRepository: widget.authRepository,
        );
      case AppRoute.approved:
        return CatalogGate(
          catalogRepository: widget.catalogRepository,
          profileRepository: widget.profileRepository,
          adminRepository: widget.adminRepository,
          reportesRepository: widget.reportesRepository,
          pendingGameResultsSyncer: widget.pendingGameResultsSyncer,
          sessionTimeSyncer: widget.sessionTimeSyncer,
          themeController: widget.themeController,
          profile: _profile!,
          onSignOut: widget.authRepository.signOut,
        );
    }
  }
}
