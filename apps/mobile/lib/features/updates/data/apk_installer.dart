import 'dart:io';

import 'package:open_filex/open_filex.dart';

enum ApkInstallResult {
  /// El instalador del sistema se abrió con el APK.
  lanzado,

  /// Falta autorizar "instalar apps desconocidas" para esta app.
  permisoDenegado,

  /// Cualquier otra falla al lanzar el instalador.
  error,
}

/// Envoltorio fino sobre el plugin: lanza el instalador del sistema con el
/// APK descargado. Sin tests unitarios — solo delega en `OpenFilex.open`
/// (que aporta su propio FileProvider); se verifica en dispositivo real.
class ApkInstaller {
  Future<ApkInstallResult> install(File apk) async {
    try {
      final result = await OpenFilex.open(
        apk.path,
        type: 'application/vnd.android.package-archive',
      );
      return switch (result.type) {
        ResultType.done => ApkInstallResult.lanzado,
        ResultType.permissionDenied => ApkInstallResult.permisoDenegado,
        _ => ApkInstallResult.error,
      };
    } catch (_) {
      return ApkInstallResult.error;
    }
  }
}
