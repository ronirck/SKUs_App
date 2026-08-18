import 'dart:convert';

import 'package:http/http.dart' as http;

/// Consulta la API pública de GitHub Releases, sin autenticación (60
/// req/hora por IP — ver README.md, decisión de Paso 0 de no embeber un
/// GITHUB_TOKEN en el APK).
class GithubReleaseDataSource {
  GithubReleaseDataSource(this._client);

  final http.Client _client;

  /// Retorna el release más reciente de [repo] (formato "owner/repo"), o
  /// null ante cualquier falla (sin red, timeout, repo sin releases, etc.)
  /// — un chequeo de actualización nunca debe bloquear ni fallar el arranque.
  Future<Map<String, dynamic>?> fetchLatestRelease(String repo) async {
    try {
      final response = await _client
          .get(
            Uri.parse('https://api.github.com/repos/$repo/releases/latest'),
            headers: const {
              'Accept': 'application/vnd.github+json',
              'X-GitHub-Api-Version': '2022-11-28',
            },
          )
          .timeout(const Duration(seconds: 5));
      if (response.statusCode != 200) return null;
      return jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }
}
