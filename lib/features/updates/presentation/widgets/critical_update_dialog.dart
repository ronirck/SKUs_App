import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../domain/update_info.dart';

/// Diálogo bloqueante: sin botón de cierre, `barrierDismissible: false` y
/// `PopScope(canPop: false)` para que ni el botón atrás de Android lo cierre.
/// El usuario queda aquí hasta que actualice e instale la nueva versión.
Future<void> showCriticalUpdateDialog(BuildContext context, UpdateInfo info) {
  return showDialog<void>(
    context: context,
    barrierDismissible: false,
    builder: (dialogContext) => PopScope(
      canPop: false,
      child: AlertDialog(
        title: const Text('Actualización requerida'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Esta versión ya no es compatible. Descarga la versión '
                '${info.latestVersion} para continuar.',
              ),
              if (info.changelog.isNotEmpty) ...[
                const SizedBox(height: 12),
                for (final item in info.changelog) Text('• $item'),
              ],
            ],
          ),
        ),
        actions: [
          if (info.apkUrl != null)
            FilledButton(
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: info.apkUrl!));
                if (dialogContext.mounted) {
                  ScaffoldMessenger.of(dialogContext)
                      .showSnackBar(const SnackBar(content: Text('Enlace copiado.')));
                }
              },
              child: const Text('Copiar enlace'),
            ),
        ],
      ),
    ),
  );
}
