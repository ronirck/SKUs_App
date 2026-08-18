import 'package:flutter/material.dart';

import '../../data/apk_downloader.dart';
import '../../data/apk_installer.dart';
import '../../domain/update_info.dart';
import 'update_install_section.dart';

/// Diálogo bloqueante: sin botón de cierre, `barrierDismissible: false` y
/// `PopScope(canPop: false)` para que ni el botón atrás de Android lo cierre.
/// El usuario queda aquí hasta que descargue e instale la nueva versión
/// (la descarga y el lanzamiento del instalador ocurren dentro de la app).
Future<void> showCriticalUpdateDialog(
  BuildContext context,
  UpdateInfo info, {
  required ApkDownloader downloader,
  required ApkInstaller installer,
}) {
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
                'Esta versión ya no es compatible. Instala la versión '
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
            UpdateInstallSection(info: info, downloader: downloader, installer: installer),
        ],
      ),
    ),
  );
}
