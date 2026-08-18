import 'package:flutter/material.dart';

import '../../data/catalog_repository.dart';
import '../widgets/producto_tile.dart';

class GuiaProductosScreen extends StatelessWidget {
  const GuiaProductosScreen({
    super.key,
    required this.catalogRepository,
    required this.categoriaCodigo,
    required this.subcategoriaCodigo,
    required this.subcategoriaNombre,
    this.marca,
    this.soloInfaltables = false,
  });

  final CatalogRepository catalogRepository;
  final String categoriaCodigo;
  final String subcategoriaCodigo;
  final String subcategoriaNombre;
  final String? marca;
  final bool soloInfaltables;

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<List<ProductoConEstatus>>(
      stream: catalogRepository.watchProductos(
        categoriaCodigo: categoriaCodigo,
        subcategoriaCodigo: subcategoriaCodigo,
        marca: marca,
        soloInfaltables: soloInfaltables,
      ),
      builder: (context, snapshot) {
        final productos = snapshot.data;
        return Scaffold(
          appBar: AppBar(
            title: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(subcategoriaNombre, overflow: TextOverflow.ellipsis),
                if (productos != null)
                  Text(
                    productos.length == 1 ? '1 producto' : '${productos.length} productos',
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant),
                  ),
              ],
            ),
          ),
          body: productos == null
              ? const Center(child: CircularProgressIndicator())
              : productos.isEmpty
                  ? const Center(child: Text('No hay productos en esta subcategoría.'))
                  : ListView.separated(
                      itemCount: productos.length,
                      separatorBuilder: (_, _) => const Divider(height: 1),
                      itemBuilder: (context, index) => ProductoTile(item: productos[index]),
                    ),
        );
      },
    );
  }
}
