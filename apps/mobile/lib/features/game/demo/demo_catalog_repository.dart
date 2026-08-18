import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../../core/database/app_database.dart';
import '../../catalog/data/catalog_remote_data_source.dart';
import '../../catalog/data/catalog_repository.dart';
import 'demo_catalog_data.dart';

const _demoEstatusCodigo = 'N';

/// Arma un [CatalogRepository] real respaldado por una base de datos en
/// memoria, pre-sembrada con el catálogo ficticio — así la demo de
/// onboarding reutiliza exactamente las mismas pantallas de Guía y Desafíos
/// que ve un usuario aprobado, sin tocar la base real ni depender de que el
/// usuario 'pendiente' pueda leerla (RLS se lo impide).
///
/// El [CatalogRemoteDataSource] que recibe nunca se invoca en el flujo normal
/// de la demo (no se llama `ensureSynced`) — solo existe para satisfacer el
/// constructor de [CatalogRepository]; si el usuario toca "Actualizar
/// catálogo ahora" en el Perfil de la demo, fallará de forma controlada
/// (RLS) y se mostrará el mensaje de error ya existente en esa pantalla.
Future<CatalogRepository> buildDemoCatalogRepository() async {
  final db = AppDatabase.forTesting(NativeDatabase.memory());

  await db.batch((batch) {
    batch.insertAll(
      db.cachedEstatusProducto,
      [
        CachedEstatusProductoCompanion.insert(
          codigo: _demoEstatusCodigo,
          nombre: 'Normal',
          esInfaltable: false,
        ),
      ],
    );
    batch.insertAll(
      db.cachedCategorias,
      demoCategorias.map(
        (c) => CachedCategoriasCompanion.insert(
          codigo: c.codigo,
          nombre: c.nombre,
          mnemotecnia: Value(c.mnemotecnia),
          sede: 'DEMO',
        ),
      ),
    );
    batch.insertAll(
      db.cachedSubcategorias,
      demoSubcategorias.map(
        (s) => CachedSubcategoriasCompanion.insert(
          codigo: s.codigo,
          categoriaCodigo: s.categoriaCodigo,
          nombre: s.nombre,
          mnemotecnia: Value(s.mnemotecnia),
          sede: 'DEMO',
        ),
      ),
    );
    batch.insertAll(
      db.cachedProductos,
      demoProductos.map(
        (p) => CachedProductosCompanion.insert(
          id: p.codigoCompleto,
          codigo: p.codigo,
          codigoCompleto: Value(p.codigoCompleto),
          categoriaCodigo: p.categoriaCodigo,
          subcategoriaCodigo: p.subcategoriaCodigo,
          nombre: p.nombre,
          estatus: _demoEstatusCodigo,
          marca: p.marca,
          sede: 'DEMO',
        ),
      ),
    );
  });

  return CatalogRepository(db, CatalogRemoteDataSource(Supabase.instance.client));
}
