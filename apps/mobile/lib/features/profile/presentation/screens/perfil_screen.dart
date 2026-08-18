import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme_controller.dart';
import '../../../../core/utils/format_duration.dart';
import '../../../admin/data/admin_repository.dart';
import '../../../admin/domain/sedes.dart';
import '../../../auth/data/profile_repository.dart';
import '../../../auth/domain/user_profile.dart';
import '../../../catalog/data/catalog_repository.dart';
import '../../../reportes/data/reportes_repository.dart';
import '../../../session/domain/session_clock.dart';

class PerfilScreen extends StatefulWidget {
  const PerfilScreen({
    super.key,
    required this.profileRepository,
    required this.catalogRepository,
    this.adminRepository,
    required this.reportesRepository,
    required this.themeController,
    required this.sessionClock,
    required this.userId,
    required this.profile,
    required this.onSignOut,
  });

  final ProfileRepository profileRepository;
  final CatalogRepository catalogRepository;

  /// Requerido para el selector de casa del admin; `null` en la demo de
  /// onboarding (donde la sección Casa no se muestra).
  final AdminRepository? adminRepository;
  final ReportesRepository reportesRepository;
  final AppThemeController themeController;
  final SessionClock sessionClock;
  final String userId;
  final UserProfile profile;
  final Future<void> Function() onSignOut;

  @override
  State<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends State<PerfilScreen> {
  late final _nombreCtrl = TextEditingController(text: widget.profile.nombre ?? '');
  late final _apellidoCtrl = TextEditingController(text: widget.profile.apellido ?? '');
  bool _savingNombre = false;
  String? _nombreError;

  bool _refreshingCatalog = false;
  String? _refreshMessage;

  String? _casaActual;
  bool _cambiandoCasa = false;

  bool get _isAdmin => widget.profile.rol == 'admin';
  late Future<List<ReporteError>> _reportesFuture = widget.reportesRepository.fetchAllReports();

  @override
  void initState() {
    super.initState();
    widget.catalogRepository.cachedSede().then((sede) {
      if (mounted) setState(() => _casaActual = sede);
    });
  }

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _apellidoCtrl.dispose();
    super.dispose();
  }

  Future<void> _saveNombre() async {
    final nombre = _nombreCtrl.text.trim();
    final apellido = _apellidoCtrl.text.trim();
    if (nombre.isEmpty || apellido.isEmpty) {
      setState(() => _nombreError = 'Nombre y apellido son obligatorios.');
      return;
    }
    setState(() {
      _savingNombre = true;
      _nombreError = null;
    });
    try {
      await widget.profileRepository.confirmNombreApellido(nombre: nombre, apellido: apellido);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Nombre actualizado.')));
      }
    } catch (_) {
      if (mounted) setState(() => _nombreError = 'No se pudo guardar. Verifica tu conexión.');
    } finally {
      if (mounted) setState(() => _savingNombre = false);
    }
  }

  Future<void> _refreshCatalog() async {
    setState(() {
      _refreshingCatalog = true;
      _refreshMessage = null;
    });
    try {
      final changed = await widget.catalogRepository.ensureSynced(userId: widget.userId);
      if (mounted) {
        setState(() => _refreshMessage = changed ? 'Catálogo actualizado.' : 'Ya estabas al día.');
      }
    } catch (_) {
      if (mounted) {
        setState(() => _refreshMessage = 'No se pudo actualizar. Verifica tu conexión.');
      }
    } finally {
      if (mounted) setState(() => _refreshingCatalog = false);
    }
  }

  /// Cambia la casa (sede) que ve el admin: actualiza su config remota y
  /// espera a que el caché quede reconstruido con la casa nueva. Si no hay
  /// conexión, la config remota no cambia y el caché anterior queda intacto
  /// (la reconstrucción es transaccional), así que solo se informa el error.
  Future<void> _cambiarCasa(String nueva) async {
    final anterior = _casaActual;
    setState(() {
      _cambiandoCasa = true;
      _casaActual = nueva;
    });
    try {
      await widget.adminRepository!.updateOwnSede(nueva);
      // `ensureSynced` puede devolver sin reconstruir si una sincronización
      // en segundo plano va a mitad; se reintenta hasta ver la casa nueva.
      for (var intento = 0; intento < 4; intento++) {
        await widget.catalogRepository.ensureSynced(userId: widget.userId);
        if (await widget.catalogRepository.cachedSede() == nueva) break;
        await Future.delayed(const Duration(milliseconds: 500));
      }
      if (await widget.catalogRepository.cachedSede() != nueva) {
        throw StateError('el caché no se reconstruyó con la casa nueva');
      }
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Ahora estás viendo $nueva.')));
      }
    } catch (_) {
      if (mounted) {
        setState(() => _casaActual = anterior);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No se pudo cambiar de casa. Comprueba tu conexión e inténtalo más tarde.'),
        ));
      }
    } finally {
      if (mounted) setState(() => _cambiandoCasa = false);
    }
  }

  Future<void> _showReportDialog() async {
    final controller = TextEditingController();
    final quiereEnviar = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Reportar un problema'),
        content: TextField(
          controller: controller,
          maxLines: 4,
          autofocus: true,
          decoration: const InputDecoration(hintText: 'Describe el problema...'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Enviar'),
          ),
        ],
      ),
    );

    if (quiereEnviar != true) return;
    final mensaje = controller.text.trim();
    if (mensaje.isEmpty) return;

    try {
      await widget.reportesRepository.submitReport(mensaje);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Reporte enviado. ¡Gracias!')));
      }
      if (_isAdmin) _reloadReportes();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo enviar. Verifica tu conexión e intenta de nuevo.')),
        );
      }
    }
  }

  void _reloadReportes() {
    setState(() => _reportesFuture = widget.reportesRepository.fetchAllReports());
  }

  Future<void> _cambiarEstatusReporte(ReporteError reporte, String nuevoEstatus) async {
    try {
      await widget.reportesRepository.updateEstatus(id: reporte.id, estatus: nuevoEstatus);
      _reloadReportes();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('No se pudo actualizar el estatus.')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Perfil')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            AnimatedBuilder(
              animation: widget.sessionClock,
              builder: (context, _) => Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      const Text('Tiempo de sesión activa'),
                      const SizedBox(height: 8),
                      Text(
                        formatHms(widget.sessionClock.elapsed),
                        style: Theme.of(context).textTheme.headlineMedium,
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),
            const Text('Datos personales', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            TextField(
              controller: _nombreCtrl,
              decoration: const InputDecoration(labelText: 'Nombre', border: OutlineInputBorder()),
              textCapitalization: TextCapitalization.words,
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _apellidoCtrl,
              decoration: const InputDecoration(labelText: 'Apellido', border: OutlineInputBorder()),
              textCapitalization: TextCapitalization.words,
            ),
            if (_nombreError != null) ...[
              const SizedBox(height: 8),
              Text(_nombreError!, style: const TextStyle(color: Colors.red)),
            ],
            const SizedBox(height: 8),
            FilledButton(
              onPressed: _savingNombre ? null : _saveNombre,
              child: _savingNombre
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Guardar cambios'),
            ),
            const SizedBox(height: 24),
            const Text('Apariencia', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            AnimatedBuilder(
              animation: widget.themeController,
              builder: (context, _) => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SegmentedButton<ThemeMode>(
                    segments: const [
                      ButtonSegment(
                        value: ThemeMode.system,
                        label: Text('Sistema'),
                        icon: Icon(Icons.brightness_auto),
                      ),
                      ButtonSegment(
                        value: ThemeMode.light,
                        label: Text('Claro'),
                        icon: Icon(Icons.light_mode),
                      ),
                      ButtonSegment(
                        value: ThemeMode.dark,
                        label: Text('Oscuro'),
                        icon: Icon(Icons.dark_mode),
                      ),
                    ],
                    selected: {widget.themeController.themeMode},
                    onSelectionChanged: (s) => widget.themeController.setThemeMode(s.first),
                  ),
                  const SizedBox(height: 16),
                  const Text('Color'),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 16,
                    runSpacing: 8,
                    children: AppColorSeed.values.map((seed) {
                      final selected = widget.themeController.colorSeed == seed;
                      return GestureDetector(
                        onTap: () => widget.themeController.setColorSeed(seed),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            CircleAvatar(
                              backgroundColor: seed.color,
                              radius: 18,
                              child: selected
                                  ? const Icon(Icons.check, color: Colors.white)
                                  : null,
                            ),
                            const SizedBox(height: 4),
                            Text(seed.label, style: const TextStyle(fontSize: 11)),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
            if (_isAdmin && widget.adminRepository != null) ...[
              const SizedBox(height: 24),
              const Text('Casa', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text(
                _casaActual == null
                    ? 'Cargando casa actual...'
                    : 'Estás viendo el catálogo de: $_casaActual',
              ),
              const SizedBox(height: 8),
              DropdownButton<String>(
                value: kSedes.contains(_casaActual) ? _casaActual : null,
                isExpanded: true,
                hint: const Text('Cambiar de casa'),
                items: kSedes.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
                onChanged: (_cambiandoCasa || _casaActual == null)
                    ? null
                    : (v) {
                        if (v != null && v != _casaActual) _cambiarCasa(v);
                      },
              ),
              if (_cambiandoCasa) ...[
                const SizedBox(height: 8),
                const Row(
                  children: [
                    SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                    SizedBox(width: 8),
                    Text('Descargando el catálogo de la casa nueva...'),
                  ],
                ),
              ],
            ],
            const SizedBox(height: 24),
            const Text('Catálogo', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _refreshingCatalog ? null : _refreshCatalog,
              icon: _refreshingCatalog
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.refresh),
              label: const Text('Actualizar catálogo ahora'),
            ),
            if (_refreshMessage != null) ...[
              const SizedBox(height: 8),
              Text(_refreshMessage!),
            ],
            const SizedBox(height: 24),
            const Text('Ayuda', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _showReportDialog,
              icon: const Icon(Icons.flag_outlined),
              label: const Text('Reportar un problema'),
            ),
            if (_isAdmin) ...[
              const SizedBox(height: 24),
              const Text('Reportes', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              FutureBuilder<List<ReporteError>>(
                future: _reportesFuture,
                builder: (context, snapshot) {
                  if (!snapshot.hasData) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  final reportes = snapshot.data!;
                  if (reportes.isEmpty) {
                    return const Text('No hay reportes todavía.');
                  }
                  return Column(
                    children: reportes.map((r) {
                      return Card(
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(r.mensaje),
                              const SizedBox(height: 8),
                              DropdownButton<String>(
                                value: r.estatus,
                                isDense: true,
                                items: kEstatusReporte
                                    .map((e) => DropdownMenuItem(value: e, child: Text(e)))
                                    .toList(),
                                onChanged: (value) {
                                  if (value != null) _cambiarEstatusReporte(r, value);
                                },
                              ),
                            ],
                          ),
                        ),
                      );
                    }).toList(),
                  );
                },
              ),
            ],
            const SizedBox(height: 32),
            OutlinedButton(onPressed: widget.onSignOut, child: const Text('Cerrar sesión')),
          ],
        ),
      ),
    );
  }
}
