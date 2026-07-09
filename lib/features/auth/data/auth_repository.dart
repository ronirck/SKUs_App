import 'package:google_sign_in/google_sign_in.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../core/config/app_config.dart';
import '../domain/auth_failure.dart';

abstract class AuthRepository {
  Future<void> initialize();
  Session? get currentSession;
  Map<String, dynamic>? get currentUserMetadata;
  Stream<AuthState> get onAuthStateChange;
  Future<void> signInWithGoogle();
  Future<void> signOut();
}

class SupabaseAuthRepository implements AuthRepository {
  SupabaseAuthRepository(this._client);

  final SupabaseClient _client;
  bool _googleSignInInitialized = false;

  @override
  Future<void> initialize() async {
    if (_googleSignInInitialized) return;
    await GoogleSignIn.instance.initialize(serverClientId: AppConfig.googleWebClientId);
    _googleSignInInitialized = true;
  }

  @override
  Session? get currentSession => _client.auth.currentSession;

  @override
  Map<String, dynamic>? get currentUserMetadata => _client.auth.currentUser?.userMetadata;

  @override
  Stream<AuthState> get onAuthStateChange => _client.auth.onAuthStateChange;

  @override
  Future<void> signInWithGoogle() async {
    final GoogleSignInAccount account;
    try {
      account = await GoogleSignIn.instance.authenticate();
    } on GoogleSignInException catch (e) {
      if (e.code == GoogleSignInExceptionCode.canceled) {
        throw const AuthFailure(AuthFailureType.cancelled, 'Inicio de sesión cancelado.');
      }
      throw AuthFailure(
        AuthFailureType.network,
        'No se pudo conectar con Google. Verifica tu conexión e intenta de nuevo.',
      );
    } catch (_) {
      throw const AuthFailure(
        AuthFailureType.network,
        'No se pudo conectar con Google. Verifica tu conexión e intenta de nuevo.',
      );
    }

    final idToken = account.authentication.idToken;
    if (idToken == null) {
      throw const AuthFailure(
        AuthFailureType.unknown,
        'Google no devolvió las credenciales esperadas. Intenta de nuevo.',
      );
    }

    try {
      await _client.auth.signInWithIdToken(provider: OAuthProvider.google, idToken: idToken);
    } on AuthException catch (e) {
      // statusCode es null cuando el error ocurrió antes de recibir respuesta
      // HTTP (p. ej. sin red) — en ese caso e.message es el texto crudo de la
      // excepción de bajo nivel (SocketException, etc.), no apto para mostrar.
      if (e.statusCode == null) {
        throw const AuthFailure(
          AuthFailureType.network,
          'No se pudo completar el inicio de sesión. Verifica tu conexión e intenta de nuevo.',
        );
      }
      throw AuthFailure(AuthFailureType.unknown, e.message);
    } catch (e) {
      throw const AuthFailure(
        AuthFailureType.network,
        'No se pudo completar el inicio de sesión. Verifica tu conexión e intenta de nuevo.',
      );
    }
  }

  @override
  Future<void> signOut() async {
    await GoogleSignIn.instance.signOut();
    await _client.auth.signOut();
  }
}
