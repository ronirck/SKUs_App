import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';

import '../../../core/theme/app_theme_controller.dart';
import '../../admin/data/admin_repository.dart';
import '../../auth/data/profile_repository.dart';
import '../../auth/domain/user_profile.dart';
import '../../game/data/pending_game_results_syncer.dart';
import '../../home/presentation/home_shell.dart';
import '../../reportes/data/reportes_repository.dart';
import '../../session/data/session_time_syncer.dart';
import '../../session/domain/session_clock.dart';
import '../../session/domain/split_by_local_day.dart';
import '../data/catalog_repository.dart';

/// Punto de entrada del catálogo tras aprobarse el usuario. Si ya hay caché,
/// la muestra de inmediato (arranque instantáneo) y sincroniza en segundo
/// plano sin bloquear. Solo bloquea con un loader cuando NUNCA se ha
/// sincronizado (primera vez, requiere red).
///
/// También mide tiempo de uso (mientras la app está en primer plano y ya
/// aprobada, vía [SessionClock]) y dispara la sincronización de lo encolado
/// sin red — no solo al abrir la app, también al recuperar conexión o
/// reanudar desde segundo plano.
class CatalogGate extends StatefulWidget {
  const CatalogGate({
    super.key,
    required this.catalogRepository,
    required this.profileRepository,
    required this.adminRepository,
    required this.reportesRepository,
    required this.pendingGameResultsSyncer,
    required this.sessionTimeSyncer,
    required this.themeController,
    required this.profile,
    required this.onSignOut,
  });

  final CatalogRepository catalogRepository;
  final ProfileRepository profileRepository;
  final AdminRepository adminRepository;
  final ReportesRepository reportesRepository;
  final PendingGameResultsSyncer pendingGameResultsSyncer;
  final SessionTimeSyncer sessionTimeSyncer;
  final AppThemeController themeController;
  final UserProfile profile;
  final Future<void> Function() onSignOut;

  @override
  State<CatalogGate> createState() => _CatalogGateState();
}

class _CatalogGateState extends State<CatalogGate> with WidgetsBindingObserver {
  bool _ready = false;
  String? _error;

  final SessionClock _sessionClock = SessionClock();
  StreamSubscription<List<ConnectivityResult>>? _connectivitySub;
  bool _wasConnected = true;

  String get _userId => widget.profile.id;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _connectivitySub = Connectivity().onConnectivityChanged.listen(_onConnectivityChanged);
    _bootstrap();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _connectivitySub?.cancel();
    unawaited(_flushSessionTime());
    _sessionClock.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _startSessionTimer();
      _syncEverything();
    } else if (state == AppLifecycleState.paused) {
      unawaited(_flushSessionTime());
    }
  }

  void _onConnectivityChanged(List<ConnectivityResult> results) {
    final connected = results.any((r) => r != ConnectivityResult.none);
    if (connected && !_wasConnected) {
      _syncEverything();
    }
    _wasConnected = connected;
  }

  void _syncEverything() {
    unawaited(widget.pendingGameResultsSyncer.flushPending().catchError((_) {}));
    unawaited(widget.sessionTimeSyncer.flushPending().catchError((_) {}));
    unawaited(widget.catalogRepository.ensureSynced(userId: _userId).catchError((_) => false));
  }

  void _startSessionTimer() {
    if (!_ready) return;
    _sessionClock.resume();
  }

  Future<void> _flushSessionTime() async {
    final interval = _sessionClock.pause();
    if (interval == null) return;
    final buckets = splitByLocalDay(interval.start, interval.end);
    for (final entry in buckets.entries) {
      await widget.sessionTimeSyncer.addDuration(
        usuarioId: _userId,
        fechaLocal: entry.key,
        segundos: entry.value.inSeconds,
      );
    }
  }

  Future<void> _handleSignOut() async {
    await _flushSessionTime();
    await widget.catalogRepository.clearCache();
    await widget.profileRepository.clearLastKnownProfile();
    await widget.onSignOut();
  }

  Future<void> _bootstrap() async {
    unawaited(widget.pendingGameResultsSyncer.flushPending().catchError((_) {}));
    unawaited(widget.sessionTimeSyncer.flushPending().catchError((_) {}));

    final hasCache = await widget.catalogRepository.hasCachedCatalog();
    if (hasCache) {
      if (mounted) {
        setState(() => _ready = true);
        _startSessionTimer();
      }
      unawaited(widget.catalogRepository.ensureSynced(userId: _userId).catchError((_) => false));
      return;
    }

    try {
      await widget.catalogRepository.ensureSynced(userId: _userId);
      if (mounted) {
        setState(() => _ready = true);
        _startSessionTimer();
      }
    } catch (e) {
      debugPrint('No se pudo sincronizar el catálogo: $e');
      if (mounted) {
        setState(() {
          _error = 'Necesitas conexión a internet para descargar el catálogo por primera vez.';
        });
      }
    }
  }

  Future<void> _retry() async {
    setState(() => _error = null);
    await _bootstrap();
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.cloud_off, size: 48, color: Colors.red),
                const SizedBox(height: 16),
                Text(_error!, textAlign: TextAlign.center),
                const SizedBox(height: 16),
                FilledButton(onPressed: _retry, child: const Text('Reintentar')),
                const SizedBox(height: 8),
                TextButton(onPressed: _handleSignOut, child: const Text('Cerrar sesión')),
              ],
            ),
          ),
        ),
      );
    }

    if (!_ready) {
      return const Scaffold(
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Descargando catálogo...'),
            ],
          ),
        ),
      );
    }

    return HomeShell(
      catalogRepository: widget.catalogRepository,
      profileRepository: widget.profileRepository,
      adminRepository: widget.adminRepository,
      reportesRepository: widget.reportesRepository,
      pendingGameResultsSyncer: widget.pendingGameResultsSyncer,
      themeController: widget.themeController,
      sessionClock: _sessionClock,
      profile: widget.profile,
      onSignOut: _handleSignOut,
    );
  }
}
