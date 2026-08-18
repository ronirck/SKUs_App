import 'package:flutter/material.dart';

import '../../../../core/database/app_database.dart';
import '../../data/catalog_repository.dart';
import '../widgets/producto_tile.dart';
import 'guia_subcategorias_screen.dart';

class GuiaCategoriasScreen extends StatefulWidget {
  const GuiaCategoriasScreen({super.key, required this.catalogRepository});

  final CatalogRepository catalogRepository;

  @override
  State<GuiaCategoriasScreen> createState() => _GuiaCategoriasScreenState();
}

class _GuiaCategoriasScreenState extends State<GuiaCategoriasScreen> {
  String _busqueda = '';
  String? _marca;
  bool _soloInfaltables = false;
  bool _forzado = false;
  bool _filtroListo = false;

  @override
  void initState() {
    super.initState();
    widget.catalogRepository.soloInfaltablesForzado().then((value) {
      if (!mounted) return;
      setState(() {
        _forzado = value;
        _soloInfaltables = value;
        _filtroListo = true;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        // El subtítulo muestra cuántos productos son visibles con los filtros
        // de sesión activos (búsqueda, marca, solo infaltables).
        title: StreamBuilder<List<ProductoConEstatus>>(
          stream: widget.catalogRepository.watchProductosBusqueda(
            busqueda: _busqueda,
            marca: _marca,
            soloInfaltables: _soloInfaltables,
          ),
          builder: (context, snapshot) {
            final count = snapshot.data?.length;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Guía de Estudio'),
                if (count != null)
                  Text(
                    count == 1 ? '1 producto' : '$count productos',
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
                  ),
              ],
            );
          },
        ),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: TextField(
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: 'Buscar un producto...',
                border: OutlineInputBorder(),
                isDense: true,
              ),
              onChanged: (v) => setState(() => _busqueda = v),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: StreamBuilder<List<String>>(
                    stream: widget.catalogRepository.watchMarcasDisponibles(),
                    builder: (context, snapshot) {
                      final marcas = snapshot.data ?? const <String>[];
                      if (marcas.length <= 1) return const SizedBox.shrink();
                      return DropdownButtonFormField<String?>(
                        initialValue: _marca,
                        isExpanded: true,
                        decoration: const InputDecoration(
                          labelText: 'Marca',
                          isDense: true,
                          border: OutlineInputBorder(),
                        ),
                        items: [
                          const DropdownMenuItem(value: null, child: Text('Todas las marcas')),
                          ...marcas.map((m) => DropdownMenuItem(value: m, child: Text(m))),
                        ],
                        onChanged: (v) => setState(() => _marca = v),
                      );
                    },
                  ),
                ),
                if (!_forzado) ...[
                  const SizedBox(width: 12),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('Solo infaltables'),
                      Switch(
                        value: _soloInfaltables,
                        onChanged:
                            _filtroListo ? (v) => setState(() => _soloInfaltables = v) : null,
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          Expanded(child: _busqueda.trim().isEmpty ? _buildCategorias() : _buildBusqueda()),
        ],
      ),
    );
  }

  Widget _buildCategorias() {
    return StreamBuilder<List<CachedCategoria>>(
      stream: widget.catalogRepository.watchCategorias(
        marca: _marca,
        soloInfaltables: _soloInfaltables,
      ),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        final categorias = snapshot.data!;
        if (categorias.isEmpty) {
          return const Center(child: Text('No hay categorías disponibles con estos filtros.'));
        }
        return ListView.separated(
          itemCount: categorias.length,
          separatorBuilder: (_, _) => const Divider(height: 1),
          itemBuilder: (context, index) {
            final categoria = categorias[index];
            return ListTile(
              leading: CircleAvatar(child: Text(categoria.codigo)),
              title: Text(categoria.nombre),
              subtitle: categoria.mnemotecnia != null ? Text(categoria.mnemotecnia!) : null,
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => GuiaSubcategoriasScreen(
                    catalogRepository: widget.catalogRepository,
                    categoriaCodigo: categoria.codigo,
                    categoriaNombre: categoria.nombre,
                    marca: _marca,
                    soloInfaltables: _soloInfaltables,
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildBusqueda() {
    return StreamBuilder<List<ProductoConEstatus>>(
      stream: widget.catalogRepository.watchProductosBusqueda(
        busqueda: _busqueda,
        marca: _marca,
        soloInfaltables: _soloInfaltables,
      ),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        final productos = snapshot.data!;
        if (productos.isEmpty) {
          return const Center(child: Text('Ningún producto coincide con tu búsqueda.'));
        }
        return ListView.separated(
          itemCount: productos.length,
          separatorBuilder: (_, _) => const Divider(height: 1),
          itemBuilder: (context, index) => ProductoTile(item: productos[index]),
        );
      },
    );
  }
}
