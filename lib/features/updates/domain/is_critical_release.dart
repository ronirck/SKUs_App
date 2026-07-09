/// true si el título del release marca una actualización obligatoria.
bool isCriticalRelease(String releaseName) {
  return releaseName.toUpperCase().contains('[CRITICAL]');
}
