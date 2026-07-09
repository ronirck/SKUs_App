import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

part 'app_database.g.dart';

class CachedCategorias extends Table {
  TextColumn get codigo => text()();
  TextColumn get nombre => text()();
  TextColumn get mnemotecnia => text().nullable()();
  TextColumn get sede => text()();

  @override
  Set<Column> get primaryKey => {codigo};
}

class CachedSubcategorias extends Table {
  TextColumn get codigo => text()();
  TextColumn get categoriaCodigo => text()();
  TextColumn get nombre => text()();
  TextColumn get mnemotecnia => text().nullable()();
  TextColumn get sede => text()();

  // El código de subcategoría se repite bajo distintas categorías (ej. "01"
  // existe tanto bajo la categoría "01" como bajo la "02") — la clave real
  // es el par (categoriaCodigo, codigo), no el código solo.
  @override
  Set<Column> get primaryKey => {categoriaCodigo, codigo};
}

class CachedProductos extends Table {
  TextColumn get id => text()();
  TextColumn get codigo => text()();
  TextColumn get codigoCompleto => text().nullable()();
  TextColumn get categoriaCodigo => text()();
  TextColumn get subcategoriaCodigo => text()();
  TextColumn get nombre => text()();
  TextColumn get mnemotecnia => text().nullable()();
  TextColumn get imagenUrl => text().nullable()();
  TextColumn get estatus => text()();
  TextColumn get marca => text()();
  TextColumn get sede => text()();

  @override
  Set<Column> get primaryKey => {id};
}

class CachedEstatusProducto extends Table {
  TextColumn get codigo => text()();
  TextColumn get nombre => text()();
  BoolColumn get esInfaltable => boolean()();

  @override
  Set<Column> get primaryKey => {codigo};
}

/// Tabla de una sola fila: metadatos de la última sincronización exitosa.
/// Comparar [configVersion]/[versionDatos] contra el servidor es lo que
/// decide si hace falta reconstruir la caché (ver CatalogRepository).
class CacheMeta extends Table {
  IntColumn get id => integer().withDefault(const Constant(1))();
  TextColumn get sede => text().nullable()();
  IntColumn get configVersion => integer().nullable()();
  TextColumn get versionDatos => text().nullable()();
  DateTimeColumn get syncedAt => dateTime().nullable()();

  // Valor de `usuario_config.solo_infaltables` al momento de sincronizar. Es
  // solo el punto de partida del switch "Solo infaltables" en la Guía — el
  // catálogo siempre se descarga completo (ver CatalogRepository), así que el
  // usuario puede desactivarlo durante la sesión sin perder acceso a nada.
  BoolColumn get soloInfaltablesDefault => boolean().withDefault(const Constant(false))();

  @override
  Set<Column> get primaryKey => {id};
}

/// Cola local de resultados de partida que no se pudieron guardar en
/// Supabase al terminar (sin red). Se reintenta al abrir la app; ver
/// `SupabaseGameResultRecorder.flushPending`. Los campos jsonb de
/// `resultados_codex` se guardan serializados como texto.
class PendingGameResults extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get usuarioId => text()();
  TextColumn get tipoJuego => text()();
  IntColumn get aciertos => integer()();
  IntColumn get fallos => integer()();
  IntColumn get totalPreguntas => integer()();
  IntColumn get duracionSegundos => integer()();
  TextColumn get sede => text()();
  TextColumn get configuracionJson => text()();
  TextColumn get detalleInteraccionesJson => text()();
  TextColumn get erroresJson => text()();
  DateTimeColumn get creadoEn => dateTime()();
}

/// Cola local de minutos de sesión que no se pudieron sumar a `session_logs`
/// (sin red). [fecha] es medianoche del día LOCAL al que pertenece ese
/// tramo de tiempo (ver `splitByLocalDay`). Se reintenta vía
/// `SessionTimeSyncer.flushPending`.
class PendingSessionTime extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get usuarioId => text()();
  DateTimeColumn get fecha => dateTime()();
  IntColumn get duracionSegundos => integer()();
  DateTimeColumn get creadoEn => dateTime()();
}

@DriftDatabase(
  tables: [
    CachedCategorias,
    CachedSubcategorias,
    CachedProductos,
    CachedEstatusProducto,
    CacheMeta,
    PendingGameResults,
    PendingSessionTime,
  ],
)
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());
  AppDatabase.forTesting(super.executor);

  @override
  int get schemaVersion => 1;
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'skus_app_cache.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
