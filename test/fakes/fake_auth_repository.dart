import 'dart:async';

import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:skus_app/features/auth/data/auth_repository.dart';

/// Test double — no habla con Google ni Supabase. Solo lo que hace falta
/// para ejercitar AuthGate en pruebas de widget.
class FakeAuthRepository implements AuthRepository {
  Session? session;
  Map<String, dynamic>? metadata;
  final _controller = StreamController<AuthState>.broadcast();

  @override
  Future<void> initialize() async {}

  @override
  Session? get currentSession => session;

  @override
  Map<String, dynamic>? get currentUserMetadata => metadata;

  @override
  Stream<AuthState> get onAuthStateChange => _controller.stream;

  @override
  Future<void> signInWithGoogle() async {}

  @override
  Future<void> signOut() async {
    session = null;
  }
}
