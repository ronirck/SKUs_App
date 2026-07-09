import 'package:flutter/material.dart';

import '../../data/auth_repository.dart';

class RejectedScreen extends StatelessWidget {
  const RejectedScreen({super.key, required this.authRepository});

  final AuthRepository authRepository;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.block, color: Colors.red, size: 64),
              const SizedBox(height: 16),
              Text('Acceso rechazado', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              const Text(
                'Un administrador rechazó el acceso de esta cuenta. '
                'Si crees que es un error, contacta a tu administrador.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              OutlinedButton(
                onPressed: authRepository.signOut,
                child: const Text('Cerrar sesión'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
