import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:package_info_plus/package_info_plus.dart';

import '../../../core/config/app_config.dart';
import '../../../core/theme/app_theme_controller.dart';
import '../../admin/data/admin_repository.dart';
import '../../admin/presentation/screens/usuarios_screen.dart';
import '../../auth/data/profile_repository.dart';
import '../../auth/domain/user_profile.dart';
import '../../catalog/data/catalog_repository.dart';
import '../../catalog/presentation/screens/guia_categorias_screen.dart';
import '../../game/data/pending_game_results_syncer.dart';
import '../../game/presentation/screens/desafios_home_screen.dart';
import '../../profile/presentation/screens/perfil_screen.dart';
import '../../reportes/data/reportes_repository.dart';
import '../../session/domain/session_clock.dart';
import '../../updates/data/github_release_data_source.dart';
import '../../updates/data/update_checker.dart';
import '../../updates/domain/update_info.dart';
import '../../updates/presentation/widgets/critical_update_dialog.dart';
import '../../updates/presentation/widgets/update_banner.dart';

/// Pestañas de la app aprobada: Guía, Desafíos y Perfil — idénticas para
/// cualquier rol. Si `profile.rol == 'admin'`, se agrega una 4ta pestaña
/// "Usuarios". Cada pestaña mantiene su propio Scaffold/AppBar; este shell
/// solo aporta la barra de navegación inferior.
class HomeShell extends StatefulWidget {
  const HomeShell({
    super.key,
    required this.catalogRepository,
    required this.profileRepository,
    required this.adminRepository,
    required this.reportesRepository,
    required this.pendingGameResultsSyncer,
    required this.themeController,
    required this.sessionClock,
    required this.profile,
    required this.onSignOut,
  });

  final CatalogRepository catalogRepository;
  final ProfileRepository profileRepository;
  final AdminRepository adminRepository;
  final ReportesRepository reportesRepository;
  final PendingGameResultsSyncer pendingGameResultsSyncer;
  final AppThemeController themeController;
  final SessionClock sessionClock;
  final UserProfile profile;
  final Future<void> Function() onSignOut;

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;

  final _httpClient = http.Client();
  UpdateInfo? _updateInfo;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkForUpdates());
  }

  @override
  void dispose() {
    _httpClient.close();
    super.dispose();
  }

  Future<void> _checkForUpdates() async {
    if (AppConfig.githubRepo.isEmpty) return;
    try {
      final packageInfo = await PackageInfo.fromPlatform();
      final checker = UpdateChecker(GithubReleaseDataSource(_httpClient));
      final info = await checker.check(
        repo: AppConfig.githubRepo,
        currentVersion: packageInfo.version,
        userRole: widget.profile.rol,
      );
      if (info == null || !mounted) return;
      if (info.isCritical) {
        showCriticalUpdateDialog(context, info);
      } else {
        setState(() => _updateInfo = info);
      }
    } catch (_) {
      // Un chequeo de actualización nunca debe romper el arranque de la app.
    }
  }

  @override
  Widget build(BuildContext context) {
    final isAdmin = widget.profile.rol == 'admin';

    final pages = [
      GuiaCategoriasScreen(catalogRepository: widget.catalogRepository),
      DesafiosHomeScreen(
        catalogRepository: widget.catalogRepository,
        pendingGameResultsSyncer: widget.pendingGameResultsSyncer,
        userId: widget.profile.id,
      ),
      if (isAdmin) UsuariosScreen(adminRepository: widget.adminRepository),
      PerfilScreen(
        profileRepository: widget.profileRepository,
        catalogRepository: widget.catalogRepository,
        reportesRepository: widget.reportesRepository,
        themeController: widget.themeController,
        sessionClock: widget.sessionClock,
        userId: widget.profile.id,
        profile: widget.profile,
        onSignOut: widget.onSignOut,
      ),
    ];

    final destinations = [
      const NavigationDestination(icon: Icon(Icons.menu_book), label: 'Guía'),
      const NavigationDestination(icon: Icon(Icons.videogame_asset), label: 'Desafíos'),
      if (isAdmin) const NavigationDestination(icon: Icon(Icons.people), label: 'Usuarios'),
      const NavigationDestination(icon: Icon(Icons.person), label: 'Perfil'),
    ];

    return Scaffold(
      body: Column(
        children: [
          if (_updateInfo != null)
            UpdateBanner(
              info: _updateInfo!,
              onDismiss: () => setState(() => _updateInfo = null),
            ),
          Expanded(child: IndexedStack(index: _index, children: pages)),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: destinations,
      ),
    );
  }
}
