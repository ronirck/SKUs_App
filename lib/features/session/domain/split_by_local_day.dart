/// Divide una sesión [start, end) en duración por día LOCAL. Una sesión que
/// cruza medianoche debe repartirse entre ambos días, no contarse toda en
/// uno solo — [session_logs] guarda minutos por `fecha` (día local).
///
/// Las llaves del mapa son medianoche local de cada día involucrado
/// (`DateTime(y, m, d)`).
Map<DateTime, Duration> splitByLocalDay(DateTime start, DateTime end) {
  if (!end.isAfter(start)) return {};

  final result = <DateTime, Duration>{};
  var cursor = start;
  while (cursor.isBefore(end)) {
    final dayStart = DateTime(cursor.year, cursor.month, cursor.day);
    final nextDayStart = dayStart.add(const Duration(days: 1));
    final segmentEnd = end.isBefore(nextDayStart) ? end : nextDayStart;
    result[dayStart] = (result[dayStart] ?? Duration.zero) + segmentEnd.difference(cursor);
    cursor = segmentEnd;
  }
  return result;
}
