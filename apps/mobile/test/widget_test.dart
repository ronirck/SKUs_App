import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase/supabase.dart';

import 'package:skus_app/core/database/app_database.dart';
import 'package:skus_app/core/theme/app_theme_controller.dart';
import 'package:skus_app/features/admin/data/admin_repository.dart';
import 'package:skus_app/features/auth/presentation/auth_gate.dart';
import 'package:skus_app/features/catalog/data/catalog_remote_data_source.dart';
import 'package:skus_app/features/catalog/data/catalog_repository.dart';
import 'package:skus_app/features/game/data/pending_game_results_syncer.dart';
import 'package:skus_app/features/reportes/data/reportes_repository.dart';
import 'package:skus_app/features/session/data/session_time_syncer.dart';
import 'package:skus_app/main.dart';

import 'fakes/fake_auth_repository.dart';
import 'fakes/fake_profile_repository.dart';

SupabaseClient _fakeSupabaseClient() => SupabaseClient(
      'https://example.supabase.co',
      'anon-key',
      authOptions: const AuthClientOptions(autoRefreshToken: false),
    );

void main() {
  testWidgets('ConfigErrorApp shows the missing-variables error when unconfigured',
      (WidgetTester tester) async {
    await tester.pumpWidget(const ConfigErrorApp(message: 'Faltan variables de configuración: SUPABASE_URL'));

    expect(find.textContaining('Faltan variables de configuración'), findsOneWidget);
    expect(find.byIcon(Icons.error_outline), findsOneWidget);
  });

  testWidgets('AuthGate shows the login screen when there is no session', (WidgetTester tester) async {
    // Sin mock, SharedPreferences.getInstance() queda esperando una respuesta
    // del canal de plataforma que en un testWidgets nunca llega.
    SharedPreferences.setMockInitialValues({});
    final client = _fakeSupabaseClient();
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    final themeController = await AppThemeController.load();
    await tester.pumpWidget(MaterialApp(
      home: AuthGate(
        authRepository: FakeAuthRepository(),
        profileRepository: FakeProfileRepository(),
        catalogRepository: CatalogRepository(db, CatalogRemoteDataSource(client)),
        adminRepository: AdminRepository(client),
        reportesRepository: ReportesRepository(client),
        pendingGameResultsSyncer: PendingGameResultsSyncer(client, db),
        sessionTimeSyncer: SessionTimeSyncer(client, db),
        themeController: themeController,
      ),
    ));
    await tester.pump();

    expect(find.text('Continuar con Google'), findsOneWidget);
  });
}
