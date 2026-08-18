import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

import '../../data/apk_downloader.dart';
import '../../data/apk_installer.dart';
import '../../domain/compute_download_progress.dart';
import '../../domain/is_apk_download_complete.dart';
import '../../domain/update_info.dart';

enum _Fase { inicial, descargando, instalando, error }

/// Sección compartida por el banner y el diálogo crítico: botón
/// "Descargar e instalar" → barra de progreso → instalador del sistema.
/// En error muestra la causa con "Reintentar" y el fallback "Copiar enlace".
class UpdateInstallSection extends StatefulWidget {
  const UpdateInstallSection({
    super.key,
    required this.info,
    required this.downloader,
    required this.installer,
    this.getDownloadDirectory = getTemporaryDirectory,
  });

  final UpdateInfo info;
  final ApkDownloader downloader;
  final ApkInstaller installer;

  /// Inyectable para tests; por defecto el cache de la app (no requiere
  /// permisos de storage y el sistema puede limpiarlo solo).
  final Future<Directory> Function() getDownloadDirectory;

  @override
  State<UpdateInstallSection> createState() => _UpdateInstallSectionState();
}

class _UpdateInstallSectionState extends State<UpdateInstallSection> {
  _Fase _fase = _Fase.inicial;
  String? _mensajeError;
  int _recibidos = 0;
  int? _total;

  /// APK ya descargado y validado — un reintento tras `permisoDenegado`
  /// relanza el instalador sin volver a descargar.
  File? _apkListo;

  Future<File> _destino() async {
    final dir = await widget.getDownloadDirectory();
    // Limpia APKs de versiones anteriores para no acumular basura en cache.
    await for (final entry in dir.list()) {
      if (entry is File && entry.path.contains('skus_app-') && entry.path.endsWith('.apk')) {
        try {
          await entry.delete();
        } catch (_) {}
      }
    }
    return File('${dir.path}${Platform.pathSeparator}skus_app-${widget.info.latestVersion}.apk');
  }

  Future<void> _descargarEInstalar() async {
    if (_apkListo != null) return _instalar(_apkListo!);

    setState(() {
      _fase = _Fase.descargando;
      _mensajeError = null;
      _recibidos = 0;
      _total = widget.info.apkSizeBytes;
    });
    try {
      final destino = await _destino();
      if (await destino.exists() &&
          isApkDownloadComplete(
            actualBytes: await destino.length(),
            expectedBytes: widget.info.apkSizeBytes,
          )) {
        // Descarga previa intacta: directo al instalador.
        return _instalar(destino);
      }
      final apk = await widget.downloader.download(
        url: widget.info.apkUrl!,
        destination: destino,
        expectedBytes: widget.info.apkSizeBytes,
        onProgress: (received, total) {
          if (!mounted) return;
          setState(() {
            _recibidos = received;
            _total = total;
          });
        },
      );
      await _instalar(apk);
    } on ApkDownloadException catch (e) {
      _mostrarError(switch (e.error) {
        ApkDownloadError.sinConexion => 'Sin conexión. Verifica tu red e inténtalo de nuevo.',
        ApkDownloadError.respuestaInvalida => 'No se pudo descargar la actualización.',
        ApkDownloadError.interrumpida => 'La descarga se interrumpió. Verifica tu red.',
        ApkDownloadError.archivoDanado => 'El archivo descargado llegó dañado. Intenta de nuevo.',
      });
    } catch (_) {
      _mostrarError('No se pudo descargar la actualización.');
    }
  }

  Future<void> _instalar(File apk) async {
    if (mounted) setState(() => _fase = _Fase.instalando);
    final resultado = await widget.installer.install(apk);
    if (!mounted) return;
    switch (resultado) {
      case ApkInstallResult.lanzado:
        // El instalador del sistema tomó el control; si el usuario cancela y
        // vuelve, puede reintentar sin re-descargar.
        setState(() {
          _apkListo = apk;
          _fase = _Fase.inicial;
        });
      case ApkInstallResult.permisoDenegado:
        _apkListo = apk;
        _mostrarError(
          'Autoriza a SKUs App para instalar actualizaciones (Ajustes > '
          'Instalar apps desconocidas) y vuelve a intentar.',
        );
      case ApkInstallResult.error:
        _apkListo = apk;
        _mostrarError('No se pudo abrir el instalador. Intenta de nuevo.');
    }
  }

  void _mostrarError(String mensaje) {
    if (!mounted) return;
    setState(() {
      _fase = _Fase.error;
      _mensajeError = mensaje;
    });
  }

  Future<void> _copiarEnlace() async {
    await Clipboard.setData(ClipboardData(text: widget.info.apkUrl!));
    if (mounted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Enlace copiado.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    switch (_fase) {
      case _Fase.inicial:
        return FilledButton.icon(
          onPressed: _descargarEInstalar,
          icon: const Icon(Icons.download),
          label: Text(_apkListo == null ? 'Descargar e instalar' : 'Instalar'),
        );
      case _Fase.descargando:
        final progreso = computeDownloadProgress(_recibidos, _total);
        return Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            LinearProgressIndicator(value: progreso),
            const SizedBox(height: 8),
            Text(
              progreso == null
                  ? 'Descargando actualización...'
                  : 'Descargando... ${(progreso * 100).round()}%',
            ),
          ],
        );
      case _Fase.instalando:
        return const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
            SizedBox(width: 8),
            Text('Abriendo el instalador...'),
          ],
        );
      case _Fase.error:
        return Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_mensajeError ?? 'Ocurrió un error.',
                style: TextStyle(color: Theme.of(context).colorScheme.error)),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextButton(onPressed: _descargarEInstalar, child: const Text('Reintentar')),
                TextButton(onPressed: _copiarEnlace, child: const Text('Copiar enlace')),
              ],
            ),
          ],
        );
    }
  }
}
