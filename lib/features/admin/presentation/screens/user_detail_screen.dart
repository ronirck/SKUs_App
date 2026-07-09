import 'package:flutter/material.dart';

import '../../../../core/utils/format_duration.dart';
import '../../../auth/domain/user_profile.dart';
import '../../data/admin_repository.dart';
import '../../domain/filtrar_ordenar_marcas.dart';
import '../../domain/sedes.dart';

class UserDetailScreen extends StatefulWidget {
  const UserDetailScreen({super.key, required this.adminRepository, required this.usuario});

  final AdminRepository adminRepository;
  final AdminUserSummary usuario;

  @override
  State<UserDetailScreen> createState() => _UserDetailScreenState();
}

class _UserDetailScreenState extends State<UserDetailScreen> {
  late EstadoUsuario _estado = widget.usuario.estado;
  late String _sede = widget.usuario.sede.isNotEmpty ? widget.usuario.sede : kSedes.first;
  late Set<String> _marcasSeleccionadas = widget.usuario.marcasPermitidas.toSet();
  late bool _soloInfaltables = widget.usuario.soloInfaltables;
  late Future<List<String>> _marcasDisponibles = widget.adminRepository.fetchMarcas(_sede);
  late final Future<AdminUserStats> _stats =
      widget.adminRepository.fetchUserStats(widget.usuario.usuarioId);

  String _marcaBusqueda = '';
  bool _saving = false;
  bool _savingEstado = false;

  void _onSedeChanged(String? sede) {
    if (sede == null || sede == _sede) return;
    setState(() {
      _sede = sede;
      _marcasSeleccionadas = {};
      _marcaBusqueda = '';
      _marcasDisponibles = widget.adminRepository.fetchMarcas(sede);
    });
  }

  Future<void> _guardarConfig() async {
    setState(() => _saving = true);
    try {
      await widget.adminRepository.updateUsuarioConfig(
        usuarioId: widget.usuario.usuarioId,
        sede: _sede,
        marcasPermitidas: _marcasSeleccionadas.toList(),
        soloInfaltables: _soloInfaltables,
      );
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Configuración actualizada.')));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo guardar. Verifica tu conexión.')),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _setEstado(EstadoUsuario estado) async {
    if (estado == _estado) return;
    setState(() => _savingEstado = true);
    try {
      await widget.adminRepository.setEstado(usuarioId: widget.usuario.usuarioId, estado: estado);
      if (mounted) {
        setState(() => _estado = estado);
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Estado actualizado.')));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('No se pudo actualizar el estado.')));
      }
    } finally {
      if (mounted) setState(() => _savingEstado = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final u = widget.usuario;
    final nombreCompleto = [u.nombre, u.apellido].whereType<String>().join(' ');

    return Scaffold(
      appBar: AppBar(title: Text(nombreCompleto.isEmpty ? 'Usuario' : nombreCompleto)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text('Estado', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            SegmentedButton<EstadoUsuario>(
              segments: const [
                ButtonSegment(value: EstadoUsuario.pendiente, label: Text('Pendiente')),
                ButtonSegment(value: EstadoUsuario.aprobado, label: Text('Aprobado')),
                ButtonSegment(value: EstadoUsuario.rechazado, label: Text('Rechazado')),
              ],
              selected: {_estado},
              onSelectionChanged: _savingEstado ? null : (s) => _setEstado(s.first),
            ),
            const SizedBox(height: 24),
            const Text('Configuración', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: _sede,
              decoration: const InputDecoration(labelText: 'Sede', border: OutlineInputBorder()),
              items: kSedes.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
              onChanged: _onSedeChanged,
            ),
            const SizedBox(height: 16),
            const Text('Marcas permitidas (ninguna seleccionada = todas)'),
            const SizedBox(height: 8),
            TextField(
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: 'Buscar marca...',
                border: OutlineInputBorder(),
                isDense: true,
              ),
              onChanged: (v) => setState(() => _marcaBusqueda = v),
            ),
            const SizedBox(height: 8),
            FutureBuilder<List<String>>(
              future: _marcasDisponibles,
              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return const Padding(
                    padding: EdgeInsets.all(16),
                    child: Center(child: CircularProgressIndicator()),
                  );
                }
                final marcas = snapshot.data!;
                if (marcas.isEmpty) {
                  return const Text('No hay marcas registradas para esta sede.');
                }
                final ordenadas = filtrarYOrdenarMarcas(
                  marcas,
                  seleccionadas: _marcasSeleccionadas,
                  busqueda: _marcaBusqueda,
                );
                return Container(
                  height: 240,
                  decoration: BoxDecoration(
                    border: Border.all(color: Theme.of(context).dividerColor),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: ordenadas.isEmpty
                      ? const Center(child: Text('Sin coincidencias.'))
                      : ListView.builder(
                          itemCount: ordenadas.length,
                          itemBuilder: (context, index) {
                            final m = ordenadas[index];
                            final selected = _marcasSeleccionadas.contains(m);
                            return CheckboxListTile(
                              dense: true,
                              controlAffinity: ListTileControlAffinity.leading,
                              title: Text(m),
                              value: selected,
                              onChanged: (v) => setState(() {
                                if (v ?? false) {
                                  _marcasSeleccionadas.add(m);
                                } else {
                                  _marcasSeleccionadas.remove(m);
                                }
                              }),
                            );
                          },
                        ),
                );
              },
            ),
            const SizedBox(height: 8),
            SwitchListTile(
              title: const Text('Solo infaltables'),
              value: _soloInfaltables,
              onChanged: (v) => setState(() => _soloInfaltables = v),
            ),
            const SizedBox(height: 8),
            FilledButton(
              onPressed: _saving ? null : _guardarConfig,
              child: _saving
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Guardar configuración'),
            ),
            const SizedBox(height: 32),
            const Text('Estadísticas', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            FutureBuilder<AdminUserStats>(
              future: _stats,
              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }
                final stats = snapshot.data!;
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Partidas jugadas: ${stats.totalPartidas}'),
                    Text('Efectividad: ${stats.efectividad.toStringAsFixed(1)}%'),
                    Text('Tiempo de sesión total: ${formatHms(stats.duracionSesionTotal)}'),
                    const SizedBox(height: 12),
                    const Text('Puntos ciegos (errores frecuentes):'),
                    if (stats.topErrores.isEmpty) const Text('Sin datos todavía.'),
                    ...stats.topErrores.map(
                      (e) => Text('${e.elementoCodigo} — ${e.elementoNombre} (${e.vecesFallado}x)'),
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}
