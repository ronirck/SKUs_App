import 'dart:async';

import 'package:flutter/foundation.dart';

/// Cronómetro de la sesión activa, visible en Perfil: tiempo acumulado en
/// primer plano desde el login, nunca reinicia mientras la sesión sigue
/// activa. [now] es inyectable para poder probar la acumulación sin
/// depender del reloj real.
class SessionClock extends ChangeNotifier {
  SessionClock({DateTime Function()? now}) : _now = now ?? DateTime.now;

  final DateTime Function() _now;
  Duration _accumulated = Duration.zero;
  DateTime? _resumedAt;
  Timer? _ticker;

  bool get isRunning => _resumedAt != null;

  Duration get elapsed {
    final resumedAt = _resumedAt;
    if (resumedAt == null) return _accumulated;
    return _accumulated + _now().difference(resumedAt);
  }

  void resume() {
    if (_resumedAt != null) return;
    _resumedAt = _now();
    _ticker ??= Timer.periodic(const Duration(seconds: 1), (_) => notifyListeners());
    notifyListeners();
  }

  /// Pausa y devuelve el intervalo `[start, end)` transcurrido desde el
  /// último [resume] — para repartirlo por día local y sincronizarlo.
  /// `null` si no estaba corriendo.
  ({DateTime start, DateTime end})? pause() {
    _ticker?.cancel();
    _ticker = null;
    final resumedAt = _resumedAt;
    if (resumedAt == null) return null;
    final end = _now();
    _accumulated += end.difference(resumedAt);
    _resumedAt = null;
    notifyListeners();
    return (start: resumedAt, end: end);
  }

  @override
  void dispose() {
    _ticker?.cancel();
    super.dispose();
  }
}
