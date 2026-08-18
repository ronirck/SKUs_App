import 'package:drift/drift.dart';

import '../../../core/database/app_database.dart';
import '../domain/cache_version.dart';
import '../domain/catalog_filters.dart';
import '../domain/producto_busqueda.dart';
import 'catalog_remote_data_source.dart';

class ProductoConEstatus {
  const ProductoConEstatus({required this.producto, required this.esInfaltable});

  final CachedProducto producto;
  final bool esInfaltable;
}

class CatalogRepository {
  CatalogRepository(this._db, this._remote);

  final AppDatabase _db;
  final CatalogRemoteDataSource _remote;
  bool _syncing = false;

  Future<bool> hasCachedCatalog() async {
    final meta = await (_db.select(_db.cacheMeta)..where((t) => t.id.equals(1))).getSingleOrNull();
    return meta?.syncedAt != null;
  }

  Future<String?> cachedSede() async {
    final meta = await (_db.select(_db.cacheMeta)..where((t) => t.id.equals(1))).getSingleOrNull();
    return meta?.sede;
  }

  /// Valor de `usuario_config.solo_infaltables` al momento de la última
  /// sincronización. Cuando es true el catálogo cacheado ya viene acotado a
  /// infaltables (ver [_rebuildCache]) y la Guía debe ocultar el switch
  /// "Solo infaltables": es una restricción impuesta por el admin, igual que
  /// sede/marcas, no una preferencia del usuario.
  Future<bool> soloInfaltablesForzado() async {
    final meta = await (_db.select(_db.cacheMeta)..where((t) => t.id.equals(1))).getSingleOrNull();
    return meta?.soloInfaltablesDefault ?? false;
  }

  /// Emite un valor distinto cada vez que el caché se reconstruye (cambio de
  /// sede/casa, de configuración o de datos). Las pantallas que leen el
  /// catálogo una sola vez al montarse (p. ej. Desafíos) se remontan con
  /// esta señal como key para no quedarse con fuentes viejas.
  Stream<String> watchCacheKey() {
    return (_db.select(_db.cacheMeta)..where((t) => t.id.equals(1)))
        .watchSingleOrNull()
        .map((m) => '${m?.sede}|${m?.configVersion}|${m?.versionDatos}');
  }

  /// Compara versión local vs remota y reconstruye la caché si hace falta.
  /// Deja que las excepciones de red propaguen — quien llama decide si eso
  /// es un error (primera sincronización) o algo a ignorar en silencio
  /// (refresco en segundo plano con caché ya disponible). Devuelve si
  /// realmente se reconstruyó (útil para el refresco manual desde Perfil).
  Future<bool> ensureSynced({required String userId}) async {
    if (_syncing) return false;
    _syncing = true;
    try {
      final remoteConfig = await _remote.fetchUsuarioConfig(userId);
      final remoteVersionDatos = await _remote.fetchVersionDatos();
      final remote = CacheVersion(
        configVersion: remoteConfig.configVersion,
        versionDatos: remoteVersionDatos,
      );

      final localMeta =
          await (_db.select(_db.cacheMeta)..where((t) => t.id.equals(1))).getSingleOrNull();
      final local = localMeta == null
          ? null
          : CacheVersion(configVersion: localMeta.configVersion, versionDatos: localMeta.versionDatos);

      if (!needsRefresh(local: local, remote: remote)) return false;

      await _rebuildCache(config: remoteConfig, versionDatos: remoteVersionDatos);
      return true;
    } finally {
      _syncing = false;
    }
  }

  /// Borra la caché local del catálogo (categorías/subcategorías/productos/
  /// estatus + metadatos de versión). Se usa al cerrar sesión para que otro
  /// usuario en el mismo dispositivo no vea datos del anterior sin red.
  Future<void> clearCache() async {
    await _db.transaction(() async {
      await _db.delete(_db.cachedCategorias).go();
      await _db.delete(_db.cachedSubcategorias).go();
      await _db.delete(_db.cachedProductos).go();
      await _db.delete(_db.cachedEstatusProducto).go();
      await _db.delete(_db.cacheMeta).go();
    });
  }

  Future<void> _rebuildCache({
    required RemoteUsuarioConfig config,
    required String? versionDatos,
  }) async {
    final estatusRows = await _remote.fetchEstatusProducto();

    final categoriaRows = await _remote.fetchCategorias(config.sede);
    final subcategoriaRows = await _remote.fetchSubcategorias(config.sede);
    // "Solo infaltables" activado por el admin es una restricción de acceso
    // igual que sede/marcas_permitidas: el catálogo se descarga ya acotado a
    // los estatus infaltables, con lo que la restricción aplica a la Guía,
    // la búsqueda y los juegos por igual. Sin la restricción se descarga
    // completo y el switch de la Guía queda como filtro de sesión.
    final estatusInfaltables = estatusRows
        .where((r) => r['es_infaltable'] as bool)
        .map((r) => r['codigo'] as String)
        .toList();
    final productoRows = await _remote.fetchProductos(
      sede: config.sede,
      marcaFilter: marcaFilterFor(config.marcasPermitidas),
      estatusFilter: config.soloInfaltables ? estatusInfaltables : null,
    );

    await _db.transaction(() async {
      await _db.delete(_db.cachedCategorias).go();
      await _db.delete(_db.cachedSubcategorias).go();
      await _db.delete(_db.cachedProductos).go();
      await _db.delete(_db.cachedEstatusProducto).go();

      await _db.batch((batch) {
        batch.insertAll(
          _db.cachedCategorias,
          categoriaRows.map(
            (r) => CachedCategoriasCompanion.insert(
              codigo: r['codigo'] as String,
              nombre: r['nombre'] as String,
              mnemotecnia: Value(r['mnemotecnia'] as String?),
              sede: r['sede'] as String,
            ),
          ),
        );
        batch.insertAll(
          _db.cachedSubcategorias,
          subcategoriaRows.map(
            (r) => CachedSubcategoriasCompanion.insert(
              codigo: r['codigo'] as String,
              categoriaCodigo: r['categoria_codigo'] as String,
              nombre: r['nombre'] as String,
              mnemotecnia: Value(r['mnemotecnia'] as String?),
              sede: r['sede'] as String,
            ),
          ),
        );
        batch.insertAll(
          _db.cachedEstatusProducto,
          estatusRows.map(
            (r) => CachedEstatusProductoCompanion.insert(
              codigo: r['codigo'] as String,
              nombre: r['nombre'] as String,
              esInfaltable: r['es_infaltable'] as bool,
            ),
          ),
        );
        batch.insertAll(
          _db.cachedProductos,
          productoRows.map(
            (r) => CachedProductosCompanion.insert(
              id: r['id'] as String,
              codigo: r['codigo'] as String,
              codigoCompleto: Value(r['codigo_completo'] as String?),
              categoriaCodigo: r['categoria_codigo'] as String,
              subcategoriaCodigo: r['subcategoria_codigo'] as String,
              nombre: r['nombre'] as String,
              mnemotecnia: Value(r['mnemotecnia'] as String?),
              imagenUrl: Value(r['imagen_url'] as String?),
              estatus: r['estatus'] as String,
              marca: r['marca'] as String,
              sede: r['sede'] as String,
            ),
          ),
        );
      });

      await _db.into(_db.cacheMeta).insertOnConflictUpdate(
            CacheMetaCompanion.insert(
              id: const Value(1),
              sede: Value(config.sede),
              configVersion: Value(config.configVersion),
              versionDatos: Value(versionDatos),
              syncedAt: Value(DateTime.now()),
              soloInfaltablesDefault: Value(config.soloInfaltables),
            ),
          );
    });
  }

  /// Subconsulta de productos visibles dados los filtros de sesión de la
  /// Guía (marca seleccionada, solo infaltables). Cuando `soloInfaltables` es
  /// true hace falta el join con el catálogo de estatus para saber cuáles
  /// son infaltables; si no, es una consulta simple sobre `cachedProductos`.
  /// Se usa tanto para el `existsQuery` que oculta categorías/subcategorías
  /// vacías como, indirectamente, para las listas de productos.
  BaseSelectStatement _productosVisibles({
    Expression<String>? categoriaCodigo,
    Expression<String>? subcategoriaCodigo,
    String? marca,
    required bool soloInfaltables,
  }) {
    if (soloInfaltables) {
      final query = _db.select(_db.cachedProductos).join([
        innerJoin(
          _db.cachedEstatusProducto,
          _db.cachedEstatusProducto.codigo.equalsExp(_db.cachedProductos.estatus),
        ),
      ]);
      if (categoriaCodigo != null) {
        query.where(_db.cachedProductos.categoriaCodigo.equalsExp(categoriaCodigo));
      }
      if (subcategoriaCodigo != null) {
        query.where(_db.cachedProductos.subcategoriaCodigo.equalsExp(subcategoriaCodigo));
      }
      if (marca != null) {
        query.where(_db.cachedProductos.marca.equals(marca));
      }
      query.where(_db.cachedEstatusProducto.esInfaltable.equals(true));
      return query;
    }

    final query = _db.select(_db.cachedProductos);
    if (categoriaCodigo != null) {
      query.where((p) => p.categoriaCodigo.equalsExp(categoriaCodigo));
    }
    if (subcategoriaCodigo != null) {
      query.where((p) => p.subcategoriaCodigo.equalsExp(subcategoriaCodigo));
    }
    if (marca != null) {
      query.where((p) => p.marca.equals(marca));
    }
    return query;
  }

  // Solo muestra categorías/subcategorías que tengan al menos un producto
  // visible con los filtros activos (marcas_permitidas ya aplicado al
  // descargar; marca/soloInfaltables son filtros de sesión) — de lo
  // contrario la navegación queda llena de niveles vacíos.
  Stream<List<CachedCategoria>> watchCategorias({String? marca, bool soloInfaltables = false}) {
    return (_db.select(_db.cachedCategorias)
          ..where((t) => existsQuery(
                _productosVisibles(
                  categoriaCodigo: t.codigo,
                  marca: marca,
                  soloInfaltables: soloInfaltables,
                ),
              ))
          ..orderBy([(t) => OrderingTerm(expression: t.codigo)]))
        .watch();
  }

  Stream<List<CachedSubcategoria>> watchSubcategorias(
    String categoriaCodigo, {
    String? marca,
    bool soloInfaltables = false,
  }) {
    return (_db.select(_db.cachedSubcategorias)
          ..where((t) => t.categoriaCodigo.equals(categoriaCodigo))
          ..where((t) => existsQuery(
                _productosVisibles(
                  categoriaCodigo: t.categoriaCodigo,
                  subcategoriaCodigo: t.codigo,
                  marca: marca,
                  soloInfaltables: soloInfaltables,
                ),
              ))
          ..orderBy([(t) => OrderingTerm(expression: t.codigo)]))
        .watch();
  }

  // subcategoriaCodigo por sí solo no es único (se repite bajo distintas
  // categorías), así que hay que filtrar también por categoriaCodigo.
  Stream<List<ProductoConEstatus>> watchProductos({
    required String categoriaCodigo,
    required String subcategoriaCodigo,
    String? marca,
    bool soloInfaltables = false,
  }) {
    final query = _db.select(_db.cachedProductos).join([
      leftOuterJoin(
        _db.cachedEstatusProducto,
        _db.cachedEstatusProducto.codigo.equalsExp(_db.cachedProductos.estatus),
      ),
    ])
      ..where(_db.cachedProductos.categoriaCodigo.equals(categoriaCodigo) &
          _db.cachedProductos.subcategoriaCodigo.equals(subcategoriaCodigo))
      ..orderBy([OrderingTerm(expression: _db.cachedProductos.codigo)]);
    if (marca != null) {
      query.where(_db.cachedProductos.marca.equals(marca));
    }
    if (soloInfaltables) {
      query.where(_db.cachedEstatusProducto.esInfaltable.equals(true));
    }

    return query.watch().map(
          (rows) => rows.map((row) {
            final producto = row.readTable(_db.cachedProductos);
            final estatus = row.readTableOrNull(_db.cachedEstatusProducto);
            return ProductoConEstatus(producto: producto, esInfaltable: estatus?.esInfaltable ?? false);
          }).toList(),
        );
  }

  /// Búsqueda de un producto específico por nombre o código, sin importar en
  /// qué categoría/subcategoría esté — el filtrado de texto se hace en Dart
  /// (vía [productoCoincideBusqueda]) sobre el resultado ya filtrado por
  /// marca/soloInfaltables en SQL, ya que el catálogo de un distribuidor es
  /// lo bastante pequeño para que no haga falta un `LIKE` en la base.
  Stream<List<ProductoConEstatus>> watchProductosBusqueda({
    required String busqueda,
    String? marca,
    bool soloInfaltables = false,
  }) {
    final query = _db.select(_db.cachedProductos).join([
      leftOuterJoin(
        _db.cachedEstatusProducto,
        _db.cachedEstatusProducto.codigo.equalsExp(_db.cachedProductos.estatus),
      ),
    ])
      ..orderBy([OrderingTerm(expression: _db.cachedProductos.nombre)]);
    if (marca != null) {
      query.where(_db.cachedProductos.marca.equals(marca));
    }
    if (soloInfaltables) {
      query.where(_db.cachedEstatusProducto.esInfaltable.equals(true));
    }

    return query.watch().map((rows) => rows
        .map((row) {
          final producto = row.readTable(_db.cachedProductos);
          final estatus = row.readTableOrNull(_db.cachedEstatusProducto);
          return ProductoConEstatus(producto: producto, esInfaltable: estatus?.esInfaltable ?? false);
        })
        .where((item) => productoCoincideBusqueda(
              nombre: item.producto.nombre,
              codigo: item.producto.codigo,
              codigoCompleto: item.producto.codigoCompleto,
              busqueda: busqueda,
            ))
        .toList());
  }

  /// Marcas presentes en el catálogo ya cacheado (por lo tanto, ya acotadas a
  /// `marcas_permitidas`) — para el dropdown de marca en la Guía. Solo tiene
  /// sentido mostrarlo si hay más de una.
  Stream<List<String>> watchMarcasDisponibles() {
    final query = _db.selectOnly(_db.cachedProductos)
      ..addColumns([_db.cachedProductos.marca])
      ..groupBy([_db.cachedProductos.marca]);
    return query.watch().map((rows) {
      final marcas = rows.map((r) => r.read(_db.cachedProductos.marca)!).toList();
      marcas.sort();
      return marcas;
    });
  }

  // Lecturas puntuales (no reactivas) para armar una partida — el motor de
  // juego arma sus rondas una sola vez al empezar, no necesita un stream.
  Future<List<CachedCategoria>> categoriasJugables() {
    return (_db.select(_db.cachedCategorias)
          ..where((t) => existsQuery(
                _db.select(_db.cachedProductos)
                  ..where((p) => p.categoriaCodigo.equalsExp(t.codigo)),
              )))
        .get();
  }

  Future<List<CachedSubcategoria>> subcategoriasJugables() {
    return (_db.select(_db.cachedSubcategorias)
          ..where((t) => existsQuery(
                _db.select(_db.cachedProductos)
                  ..where((p) =>
                      p.categoriaCodigo.equalsExp(t.categoriaCodigo) &
                      p.subcategoriaCodigo.equalsExp(t.codigo)),
              )))
        .get();
  }

  Future<List<CachedProducto>> productosJugables() {
    return _db.select(_db.cachedProductos).get();
  }
}
