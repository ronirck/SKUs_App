import 'package:flutter/material.dart';

import '../../../auth/domain/user_profile.dart';
import '../../data/admin_repository.dart';
import '../../domain/filtrar_usuarios.dart';
import '../../domain/is_nuevo_registro.dart';
import '../../domain/sedes.dart';
import 'user_detail_screen.dart';

class UsuariosScreen extends StatefulWidget {
  const UsuariosScreen({super.key, required this.adminRepository});

  final AdminRepository adminRepository;

  @override
  State<UsuariosScreen> createState() => _UsuariosScreenState();
}

class _UsuariosScreenState extends State<UsuariosScreen> {
  late Future<List<AdminUserSummary>> _future = widget.adminRepository.fetchAllUsers();

  String _busqueda = '';
  bool? _soloNuevos;
  String? _sede;

  Future<void> _reload() async {
    final next = widget.adminRepository.fetchAllUsers();
    setState(() {
      _future = next;
    });
    await next;
  }

  Color _colorFor(EstadoUsuario estado) {
    switch (estado) {
      case EstadoUsuario.aprobado:
        return Colors.green;
      case EstadoUsuario.pendiente:
        return Colors.orange;
      case EstadoUsuario.rechazado:
        return Colors.red;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Usuarios')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: TextField(
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: 'Buscar por nombre o apellido...',
                border: OutlineInputBorder(),
                isDense: true,
              ),
              onChanged: (value) => setState(() => _busqueda = value),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String?>(
                    initialValue: _sede,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: 'Sede',
                      isDense: true,
                      border: OutlineInputBorder(),
                    ),
                    items: [
                      const DropdownMenuItem(value: null, child: Text('Todas')),
                      ...kSedes.map((s) => DropdownMenuItem(value: s, child: Text(s))),
                    ],
                    onChanged: (v) => setState(() => _sede = v),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: DropdownButtonFormField<bool?>(
                    initialValue: _soloNuevos,
                    isExpanded: true,
                    decoration: const InputDecoration(
                      labelText: 'Antigüedad',
                      isDense: true,
                      border: OutlineInputBorder(),
                    ),
                    items: const [
                      DropdownMenuItem(value: null, child: Text('Todos')),
                      DropdownMenuItem(value: true, child: Text('Nuevos')),
                      DropdownMenuItem(value: false, child: Text('Antiguos')),
                    ],
                    onChanged: (v) => setState(() => _soloNuevos = v),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: RefreshIndicator(
              onRefresh: _reload,
              child: FutureBuilder<List<AdminUserSummary>>(
                future: _future,
                builder: (context, snapshot) {
                  if (!snapshot.hasData) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  final usuarios = filtrarUsuarios(
                    snapshot.data!,
                    busqueda: _busqueda,
                    soloNuevos: _soloNuevos,
                    sede: _sede,
                  );
                  if (usuarios.isEmpty) {
                    return ListView(
                      children: const [
                        Padding(
                          padding: EdgeInsets.all(24),
                          child: Center(child: Text('No hay usuarios que coincidan.')),
                        ),
                      ],
                    );
                  }
                  return ListView.separated(
                    itemCount: usuarios.length,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final u = usuarios[index];
                      final nombreCompleto =
                          [u.nombre, u.apellido].whereType<String>().join(' ');
                      return ListTile(
                        leading: CircleAvatar(backgroundColor: _colorFor(u.estado), radius: 8),
                        title: Text(nombreCompleto.isEmpty ? '(sin nombre)' : nombreCompleto),
                        subtitle: Text(u.sede.isEmpty ? 'Sin sede asignada' : u.sede),
                        trailing: isNuevoRegistro(u.creadoEn)
                            ? const Chip(
                                label: Text('Nuevo'),
                                visualDensity: VisualDensity.compact,
                              )
                            : const Icon(Icons.chevron_right),
                        onTap: () async {
                          await Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => UserDetailScreen(
                                adminRepository: widget.adminRepository,
                                usuario: u,
                              ),
                            ),
                          );
                          _reload();
                        },
                      );
                    },
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}
