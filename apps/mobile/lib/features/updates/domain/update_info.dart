class UpdateInfo {
  const UpdateInfo({
    required this.isCritical,
    required this.latestVersion,
    required this.changelog,
    required this.apkUrl,
    required this.releaseUrl,
    this.apkSizeBytes,
  });

  final bool isCritical;
  final String latestVersion;
  final List<String> changelog;
  final String? apkUrl;
  final String? releaseUrl;

  /// Tamaño publicado del asset .apk — referencia para validar que la
  /// descarga in-app llegó completa.
  final int? apkSizeBytes;
}
