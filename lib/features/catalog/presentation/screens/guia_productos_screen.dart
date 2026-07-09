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
    return Scaffold(
      appBar: AppBar(title: Text(subcategoriaNombre)),
      body: StreamBuilder<List<ProductoConEstatus>>(
        stream: catalogRepository.watchProductos(
          categoriaCodigo: categoriaCodigo,
          subcategoriaCodigo: subcategoriaCodigo,
          marca: marca,
          soloInfaltables: soloInfaltables,
        ),
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final productos = snapshot.data!;
          if (productos.isEmpty) {
            return const Center(child: Text('No hay productos en esta subcategoría.'));
          }
          return ListView.separated(
            itemCount: productos.length,
            separatorBuilder: (_, _) => const Divider(height: 1),
            itemBuilder: (context, index) => ProductoTile(item: productos[index]),
          );
        },
      ),
    );
  }
}
