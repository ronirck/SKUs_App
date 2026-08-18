import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../../../../core/config/app_config.dart';
import '../../data/catalog_repository.dart';

class ProductoTile extends StatelessWidget {
  const ProductoTile({super.key, required this.item});

  final ProductoConEstatus item;

  @override
  Widget build(BuildContext context) {
    final producto = item.producto;
    return ListTile(
      leading: item.esInfaltable && producto.imagenUrl != null
          ? ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: CachedNetworkImage(
                imageUrl: AppConfig.productImageUrl(producto.imagenUrl!),
                width: 48,
                height: 48,
                fit: BoxFit.cover,
                placeholder: (_, _) => const SizedBox(
                  width: 48,
                  height: 48,
                  child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
                ),
                errorWidget: (_, _, _) => const Icon(Icons.image_not_supported),
              ),
            )
          : CircleAvatar(child: Text(producto.codigo)),
      title: Text(producto.nombre),
      subtitle: Text(
        [producto.codigoCompleto ?? producto.codigo, producto.mnemotecnia]
            .whereType<String>()
            .join(' — '),
      ),
    );
  }
}
