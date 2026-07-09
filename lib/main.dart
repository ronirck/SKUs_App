import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'core/config/app_config.dart';
import 'core/database/app_database.dart';
import 'core/theme/app_theme_controller.dart';
import 'features/admin/data/admin_repository.dart';
import 'features/auth/data/auth_repository.dart';
import 'features/auth/data/profile_repository.dart';
import 'features/auth/presentation/auth_gate.dart';
import 'features/catalog/data/catalog_remote_data_source.dart';
import 'features/catalog/data/catalog_repository.dart';
import 'features/game/data/pending_game_results_syncer.dart';
import 'features/reportes/data/reportes_repository.dart';
import 'features/session/data/session_time_syncer.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  String? configError;
  try {
    AppConfig.assertConfigured();
  } on StateError catch (e) {
    configError = e.message;
  }

  if (configError != null) {
    runApp(ConfigErrorApp(message: configError));
    return;
  }

  // ignore: deprecated_member_use
  await Supabase.initialize(url: AppConfig.supabaseUrl, anonKey: AppConfig.supabaseAnonKey);
  final authRepository = SupabaseAuthRepository(Supabase.instance.client);
  await authRepository.initialize();
  final profileRepository = SupabaseProfileRepository(Supabase.instance.client);
  final appDatabase = AppDatabase();
  final catalogRepository = CatalogRepository(
    appDatabase,
    CatalogRemoteDataSource(Supabase.instance.client),
  );
  final pendingGameResultsSyncer = PendingGameResultsSyncer(Supabase.instance.client, appDatabase);
  final sessionTimeSyncer = SessionTimeSyncer(Supabase.instance.client, appDatabase);
  final adminRepository = AdminRepository(Supabase.instance.client);
  final reportesRepository = ReportesRepository(Supabase.instance.client);
  final themeController = await AppThemeController.load();

  runApp(MyApp(
    authRepository: authRepository,
    profileRepository: profileRepository,
    catalogRepository: catalogRepository,
    adminRepository: adminRepository,
    reportesRepository: reportesRepository,
    pendingGameResultsSyncer: pendingGameResultsSyncer,
    sessionTimeSyncer: sessionTimeSyncer,
    themeController: themeController,
  ));
}

class MyApp extends StatelessWidget {
  const MyApp({
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
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: themeController,
      builder: (context, _) {
        return MaterialApp(
          title: 'SKUs App',
          themeMode: themeController.themeMode,
          theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: themeController.colorSeed.color)),
          darkTheme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: themeController.colorSeed.color,
              brightness: Brightness.dark,
            ),
          ),
          home: AuthGate(
            authRepository: authRepository,
            profileRepository: profileRepository,
            catalogRepository: catalogRepository,
            adminRepository: adminRepository,
            reportesRepository: reportesRepository,
            pendingGameResultsSyncer: pendingGameResultsSyncer,
            sessionTimeSyncer: sessionTimeSyncer,
            themeController: themeController,
          ),
        );
      },
    );
  }
}

/// Se muestra en vez de la app cuando el build no recibió las 4 variables de
/// `AppConfig` vía `--dart-define-from-file` (ver README.md).
class ConfigErrorApp extends StatelessWidget {
  const ConfigErrorApp({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SKUs App — Config error',
      home: Scaffold(
        appBar: AppBar(title: const Text('SKUs App — Config error')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.error_outline, color: Colors.red, size: 48),
                const SizedBox(height: 16),
                Text(message, textAlign: TextAlign.center, style: const TextStyle(color: Colors.red)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
