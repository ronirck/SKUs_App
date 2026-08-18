import 'package:flutter/material.dart';
import 'package:tutorial_coach_mark/tutorial_coach_mark.dart';

import '../../../../../core/theme/app_theme_controller.dart';
import '../../../../catalog/data/catalog_repository.dart';
import '../../../../catalog/presentation/screens/guia_categorias_screen.dart';
import '../../../../game/demo/demo_catalog_repository.dart';
import '../../../../game/domain/game_result_recorder.dart';
import '../../../../game/presentation/screens/desafios_home_screen.dart';
import '../../../../profile/presentation/screens/perfil_screen.dart';
import '../../../../reportes/data/reportes_repository.dart';
import '../../../../session/domain/session_clock.dart';
import '../../../data/profile_repository.dart';
import '../../../domain/user_profile.dart';

/// Recorrido guiado para cuentas nuevas: coach marks sobre las 3 pestañas de
/// la app (Guía, Desafíos, Perfil) — todas reales y navegables, respaldadas
/// por un catálogo ficticio en memoria ([buildDemoCatalogRepository]) para
/// que un usuario 'pendiente' (bloqueado de la base real por RLS) pueda
/// explorar la app completa antes de ser aprobado.
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({
    super.key,
    required this.profileRepository,
    required this.reportesRepository,
    required this.themeController,
    required this.profile,
    required this.onSignOut,
    required this.onProceed,
  });

  final ProfileRepository profileRepository;
  final ReportesRepository reportesRepository;
  final AppThemeController themeController;
  final UserProfile profile;
  final Future<void> Function() onSignOut;
  final Future<void> Function() onProceed;

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _keyGuia = GlobalKey();
  final _keyDesafios = GlobalKey();
  final _keyPerfil = GlobalKey();

  late final Future<CatalogRepository> _demoRepoFuture = buildDemoCatalogRepository();
  final _demoSessionClock = SessionClock()..resume();
  static const GameResultRecorder _demoRecorder = NoopGameResultRecorder();

  int _index = 0;
  bool _finishing = false;
  bool _justApproved = false;

  late final TutorialCoachMark _tutorial = TutorialCoachMark(
    targets: _buildTargets(),
    colorShadow: Colors.black,
    paddingFocus: 8,
    opacityShadow: 0.85,
    textSkip: 'Saltar',
  );

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _tutorial.show(context: context));
  }

  @override
  void dispose() {
    _demoSessionClock.dispose();
    super.dispose();
  }

  List<TargetFocus> _buildTargets() {
    return [
      _target(_keyGuia, 'Guía de Estudio',
          'Aquí navegas el catálogo: categorías, subcategorías y productos, con códigos y mnemotecnias. Esta es una vista de ejemplo con datos ficticios.'),
      _target(_keyDesafios, 'Desafíos',
          'Los 4 modos de juego para memorizar: categorías, subcategorías, productos y contrarreloj. Pruébalos con este catálogo de ejemplo.'),
      _target(_keyPerfil, 'Perfil',
          'Tu nombre, el tema de la app, y cuánto tiempo llevas estudiando. Toca "Finalizar recorrido" cuando quieras continuar.'),
    ];
  }

  TargetFocus _target(GlobalKey key, String title, String body) {
    return TargetFocus(
      identify: title,
      keyTarget: key,
      shape: ShapeLightFocus.RRect,
      contents: [
        TargetContent(
          align: ContentAlign.top,
          builder: (context, controller) => Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title,
                  style: const TextStyle(
                      color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
              const SizedBox(height: 8),
              Text(body, style: const TextStyle(color: Colors.white)),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _finishOnboarding() async {
    setState(() => _finishing = true);
    await widget.profileRepository.markOnboardingCompleted();
    final profile = await widget.profileRepository.fetchCurrentProfile();
    if (!mounted) return;
    if (profile?.estado == EstadoUsuario.aprobado) {
      setState(() {
        _finishing = false;
        _justApproved = true;
      });
    } else {
      await widget.onProceed();
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_justApproved) {
      return Scaffold(
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.celebration, color: Colors.green, size: 64),
                const SizedBox(height: 16),
                const Text('¡Tu cuenta ya fue aprobada!', textAlign: TextAlign.center),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: widget.onProceed,
                  child: const Text('Cargar información de usuario'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return FutureBuilder<CatalogRepository>(
      future: _demoRepoFuture,
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        final demoCatalogRepository = snapshot.data!;

        final pages = [
          GuiaCategoriasScreen(catalogRepository: demoCatalogRepository),
          DesafiosHomeScreen(
            catalogRepository: demoCatalogRepository,
            userId: widget.profile.id,
            recorderOverride: _demoRecorder,
          ),
          PerfilScreen(
            profileRepository: widget.profileRepository,
            catalogRepository: demoCatalogRepository,
            reportesRepository: widget.reportesRepository,
            themeController: widget.themeController,
            sessionClock: _demoSessionClock,
            userId: widget.profile.id,
            profile: widget.profile,
            onSignOut: widget.onSignOut,
          ),
        ];

        return Scaffold(
          body: Column(
            children: [
              Container(
                width: double.infinity,
                color: Theme.of(context).colorScheme.secondaryContainer,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: SafeArea(
                  bottom: false,
                  child: Text(
                    'Vista de ejemplo — este catálogo es ficticio, solo para que conozcas la app.',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ),
              Expanded(child: IndexedStack(index: _index, children: pages)),
            ],
          ),
          bottomNavigationBar: NavigationBar(
            selectedIndex: _index,
            onDestinationSelected: (i) => setState(() => _index = i),
            destinations: [
              NavigationDestination(icon: Icon(Icons.menu_book, key: _keyGuia), label: 'Guía'),
              NavigationDestination(
                  icon: Icon(Icons.videogame_asset, key: _keyDesafios), label: 'Desafíos'),
              NavigationDestination(icon: Icon(Icons.person, key: _keyPerfil), label: 'Perfil'),
            ],
          ),
          floatingActionButton: FloatingActionButton.extended(
            onPressed: _finishing ? null : _finishOnboarding,
            icon: _finishing
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.check),
            label: const Text('Finalizar recorrido'),
          ),
        );
      },
    );
  }
}
