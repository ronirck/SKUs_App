import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../domain/update_info.dart';

class UpdateBanner extends StatelessWidget {
  const UpdateBanner({super.key, required this.info, required this.onDismiss});

  final UpdateInfo info;
  final VoidCallback onDismiss;

  Future<void> _copyLink(BuildContext context) async {
    await Clipboard.setData(ClipboardData(text: info.apkUrl!));
    if (context.mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Enlace copiado.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialBanner(
      content: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Nueva versión ${info.latestVersion} disponible',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
          for (final item in info.changelog)
            Padding(padding: const EdgeInsets.only(top: 4), child: Text('• $item')),
        ],
      ),
      actions: [
        if (info.apkUrl != null)
          TextButton(onPressed: () => _copyLink(context), child: const Text('Copiar enlace')),
        TextButton(onPressed: onDismiss, child: const Text('Ignorar')),
      ],
    );
  }
}
