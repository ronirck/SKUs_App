/// Configuración de la app, inyectada en tiempo de compilación vía
/// `--dart-define-from-file`. No hay lectura de `.env` en runtime: en móvil
/// ese archivo no se empaqueta, así que las variables deben quedar embebidas
/// en el build. Ver env.example.json y README.md para el comando de build.
class AppConfig {
  AppConfig._();

  static const String supabaseUrl = String.fromEnvironment('SUPABASE_URL');
  static const String supabaseAnonKey =
      String.fromEnvironment('SUPABASE_ANON_KEY');
  static const String githubRepo = String.fromEnvironment('GITHUB_REPO');
  static const String googleWebClientId =
      String.fromEnvironment('GOOGLE_WEB_CLIENT_ID');

  /// `imagenUrl` en `productos` es una ruta relativa dentro del bucket
  /// público `product-images` (ej. 'febeca/03-15-028.webp').
  static String productImageUrl(String imagenUrl) =>
      '$supabaseUrl/storage/v1/object/public/product-images/$imagenUrl';

  /// Falla rápido y con un mensaje claro si el build se hizo sin inyectar
  /// las variables, en vez de fallar más adelante con errores de red opacos.
  static void assertConfigured() {
    final missing = <String>[
      if (supabaseUrl.isEmpty) 'SUPABASE_URL',
      if (supabaseAnonKey.isEmpty) 'SUPABASE_ANON_KEY',
      if (githubRepo.isEmpty) 'GITHUB_REPO',
      if (googleWebClientId.isEmpty) 'GOOGLE_WEB_CLIENT_ID',
    ];
    if (missing.isNotEmpty) {
      throw StateError(
        'Faltan variables de configuración: ${missing.join(', ')}. '
        'Compila con --dart-define-from-file=env.json (ver env.example.json).',
      );
    }
  }
}
