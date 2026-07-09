class UpdateInfo {
  const UpdateInfo({
    required this.isCritical,
    required this.latestVersion,
    required this.changelog,
    required this.apkUrl,
    required this.releaseUrl,
  });

  final bool isCritical;
  final String latestVersion;
  final List<String> changelog;
  final String? apkUrl;
  final String? releaseUrl;
}
