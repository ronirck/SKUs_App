import 'package:flutter/material.dart';

import '../../../../core/database/app_database.dart';
import '../../data/catalog_repository.dart';
import 'guia_productos_screen.dart';

class GuiaSubcategoriasScreen extends StatelessWidget {
  const GuiaSubcategoriasScreen({
    super.key,
    required this.catalogRepository,
    required this.categoriaCodigo,
    required this.categoriaNombre,
    this.marca,
    this.soloInfaltables = false,
  });

  final CatalogRepository catalogRepository;
  final String categoriaCodigo;
  final String categoriaNombre;
  final String? marca;
  final bool soloInfaltables;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(categoriaNombre)),
      body: StreamBuilder<List<CachedSubcategoria>>(
        stream: catalogRepository.watchSubcategorias(
          categoriaCodigo,
          marca: marca,
          soloInfaltables: soloInfaltables,
        ),
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final subcategorias = snapshot.data!;
          if (subcategorias.isEmpty) {
            return const Center(child: Text('No hay subcategorías en esta categoría.'));
          }
          return ListView.separated(
            itemCount: subcategorias.length,
            separatorBuilder: (_, _) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final subcategoria = subcategorias[index];
              return ListTile(
                leading: CircleAvatar(child: Text(subcategoria.codigo)),
                title: Text(subcategoria.nombre),
                subtitle: subcategoria.mnemotecnia != null ? Text(subcategoria.mnemotecnia!) : null,
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => GuiaProductosScreen(
                      catalogRepository: catalogRepository,
                      categoriaCodigo: categoriaCodigo,
                      subcategoriaCodigo: subcategoria.codigo,
                      subcategoriaNombre: subcategoria.nombre,
                      marca: marca,
                      soloInfaltables: soloInfaltables,
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
