import 'package:flutter/material.dart';

import '../../data/auth_repository.dart';
import '../../domain/auth_failure.dart';

/// No navega manualmente al iniciar sesión: AuthGate escucha
/// [AuthRepository.onAuthStateChange] y re-enruta solo.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.authRepository});

  final AuthRepository authRepository;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _loading = false;
  String? _error;

  Future<void> _signIn() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await widget.authRepository.signInWithGoogle();
    } on AuthFailure catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'No se pudo iniciar sesión. Verifica tu conexión e intenta de nuevo.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.school, size: 64),
                const SizedBox(height: 16),
                Text('SKUs App', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 8),
                const Text(
                  'Memoriza el catálogo de productos de tu sede',
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                if (_error != null) ...[
                  Text(
                    _error!,
                    style: const TextStyle(color: Colors.red),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                ],
                FilledButton.icon(
                  onPressed: _loading ? null : _signIn,
                  icon: _loading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.login),
                  label: const Text('Continuar con Google'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
