import 'parse_version.dart';

/// true si [latest] es estrictamente mayor que [current] (comparación
/// numérica por componente, no lexicográfica de strings).
bool isNewerVersion(String latest, String current) {
  final a = parseVersion(latest);
  final b = parseVersion(current);
  final length = a.length > b.length ? a.length : b.length;
  for (var i = 0; i < length; i++) {
    final ai = i < a.length ? a[i] : 0;
    final bi = i < b.length ? b[i] : 0;
    if (ai != bi) return ai > bi;
  }
  return false;
}
