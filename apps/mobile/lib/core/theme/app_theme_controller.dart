import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum AppColorSeed {
  magenta(Colors.pink, 'Magenta'),
  azul(Colors.blue, 'Azul'),
  verde(Colors.green, 'Verde'),
  naranja(Colors.orange, 'Naranja'),
  morado(Colors.deepPurple, 'Morado'),
  rojo(Colors.red, 'Rojo');

  const AppColorSeed(this.color, this.label);

  final Color color;
  final String label;
}

/// Preferencias de apariencia (tema claro/oscuro + paleta de color),
/// persistidas localmente y aplicadas de inmediato en toda la app.
class AppThemeController extends ChangeNotifier {
  AppThemeController._(this._prefs, this._themeMode, this._colorSeed);

  static const _kThemeMode = 'theme_mode';
  static const _kColorSeed = 'color_seed';

  final SharedPreferences _prefs;
  ThemeMode _themeMode;
  AppColorSeed _colorSeed;

  ThemeMode get themeMode => _themeMode;
  AppColorSeed get colorSeed => _colorSeed;

  static Future<AppThemeController> load() async {
    final prefs = await SharedPreferences.getInstance();
    final mode = ThemeMode.values.firstWhere(
      (m) => m.name == prefs.getString(_kThemeMode),
      orElse: () => ThemeMode.system,
    );
    final seed = AppColorSeed.values.firstWhere(
      (s) => s.name == prefs.getString(_kColorSeed),
      orElse: () => AppColorSeed.morado,
    );
    return AppThemeController._(prefs, mode, seed);
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    if (mode == _themeMode) return;
    _themeMode = mode;
    notifyListeners();
    await _prefs.setString(_kThemeMode, mode.name);
  }

  Future<void> setColorSeed(AppColorSeed seed) async {
    if (seed == _colorSeed) return;
    _colorSeed = seed;
    notifyListeners();
    await _prefs.setString(_kColorSeed, seed.name);
  }
}
