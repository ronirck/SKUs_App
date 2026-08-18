import 'package:flutter/material.dart';

/// Se muestra brevemente justo después del login mientras se espera a que el
/// trigger del backend termine de crear `perfil_usuario` (condición de
/// carrera esperada, no un error).
class LoadingProfileScreen extends StatelessWidget {
  const LoadingProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Preparando tu cuenta...'),
          ],
        ),
      ),
    );
  }
}
