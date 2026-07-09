final _targetMarker = RegExp(
  r'<!--\s*APP_TARGET:\s*(admin|user|all)\s*-->',
  caseSensitive: false,
);

/// Extrae el rol objetivo de un release desde su body. Sin marcador (o con
/// un valor no reconocido), el release aplica a todos los roles.
String extractTarget(String body) {
  final match = _targetMarker.firstMatch(body);
  return match?.group(1)?.toLowerCase() ?? 'all';
}
