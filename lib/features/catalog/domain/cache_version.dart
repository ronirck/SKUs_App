class CacheVersion {
  const CacheVersion({required this.configVersion, required this.versionDatos});

  final int? configVersion;
  final String? versionDatos;
}

/// Pura: decide si la caché local está obsoleta frente a lo que hay en el
/// servidor. `local == null` (nunca se ha sincronizado) siempre necesita
/// refresco.
bool needsRefresh({required CacheVersion? local, required CacheVersion remote}) {
  if (local == null) return true;
  return local.configVersion != remote.configVersion || local.versionDatos != remote.versionDatos;
}
