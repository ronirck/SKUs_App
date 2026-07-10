import 'package:flutter/material.dart';

import '../../data/apk_downloader.dart';
import '../../data/apk_installer.dart';
import '../../domain/update_info.dart';
import 'update_install_section.dart';

class UpdateBanner extends StatelessWidget {
  const UpdateBanner({
    super.key,
    required this.info,
    required this.onDismiss,
    required this.downloader,
    required this.installer,
  });

  final UpdateInfo info;
  final VoidCallback onDismiss;
  final ApkDownloader downloader;
  final ApkInstaller installer;

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
          UpdateInstallSection(info: info, downloader: downloader, installer: installer),
        TextButton(onPressed: onDismiss, child: const Text('Ignorar')),
      ],
    );
  }
}
