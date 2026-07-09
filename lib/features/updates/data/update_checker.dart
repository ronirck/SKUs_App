import '../domain/compare_versions.dart';
import '../domain/extract_changelog.dart';
import '../domain/extract_target.dart';
import '../domain/find_apk_url.dart';
import '../domain/is_critical_release.dart';
import '../domain/should_notify_role.dart';
import '../domain/update_info.dart';
import 'github_release_data_source.dart';

class UpdateChecker {
  UpdateChecker(this._dataSource);

  final GithubReleaseDataSource _dataSource;

  /// Retorna null si no hay conexión, no hay releases, la versión instalada
  /// ya es la más reciente, o el release no aplica al rol de [userRole]
  /// (marcador APP_TARGET) — en cualquiera de esos casos no hay nada que
  /// notificar.
  Future<UpdateInfo?> check({
    required String repo,
    required String currentVersion,
    required String userRole,
  }) async {
    final release = await _dataSource.fetchLatestRelease(repo);
    if (release == null) return null;

    final tag = (release['tag_name'] as String? ?? '').trim();
    final latestVersion = tag.replaceFirst(RegExp('^v', caseSensitive: false), '');
    if (!isNewerVersion(latestVersion, currentVersion)) return null;

    final body = release['body'] as String? ?? '';
    if (!shouldNotifyForRole(extractTarget(body), userRole)) return null;

    final name = release['name'] as String? ?? '';
    final assets = release['assets'] as List<dynamic>? ?? const [];

    return UpdateInfo(
      isCritical: isCriticalRelease(name),
      latestVersion: latestVersion,
      changelog: extractChangelog(body, role: userRole),
      apkUrl: findApkUrl(assets),
      releaseUrl: release['html_url'] as String?,
    );
  }
}
