// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $CachedCategoriasTable extends CachedCategorias
    with TableInfo<$CachedCategoriasTable, CachedCategoria> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedCategoriasTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _codigoMeta = const VerificationMeta('codigo');
  @override
  late final GeneratedColumn<String> codigo = GeneratedColumn<String>(
    'codigo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _nombreMeta = const VerificationMeta('nombre');
  @override
  late final GeneratedColumn<String> nombre = GeneratedColumn<String>(
    'nombre',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _mnemotecniaMeta = const VerificationMeta(
    'mnemotecnia',
  );
  @override
  late final GeneratedColumn<String> mnemotecnia = GeneratedColumn<String>(
    'mnemotecnia',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _sedeMeta = const VerificationMeta('sede');
  @override
  late final GeneratedColumn<String> sede = GeneratedColumn<String>(
    'sede',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [codigo, nombre, mnemotecnia, sede];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_categorias';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedCategoria> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('codigo')) {
      context.handle(
        _codigoMeta,
        codigo.isAcceptableOrUnknown(data['codigo']!, _codigoMeta),
      );
    } else if (isInserting) {
      context.missing(_codigoMeta);
    }
    if (data.containsKey('nombre')) {
      context.handle(
        _nombreMeta,
        nombre.isAcceptableOrUnknown(data['nombre']!, _nombreMeta),
      );
    } else if (isInserting) {
      context.missing(_nombreMeta);
    }
    if (data.containsKey('mnemotecnia')) {
      context.handle(
        _mnemotecniaMeta,
        mnemotecnia.isAcceptableOrUnknown(
          data['mnemotecnia']!,
          _mnemotecniaMeta,
        ),
      );
    }
    if (data.containsKey('sede')) {
      context.handle(
        _sedeMeta,
        sede.isAcceptableOrUnknown(data['sede']!, _sedeMeta),
      );
    } else if (isInserting) {
      context.missing(_sedeMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {codigo};
  @override
  CachedCategoria map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedCategoria(
      codigo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}codigo'],
      )!,
      nombre: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}nombre'],
      )!,
      mnemotecnia: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}mnemotecnia'],
      ),
      sede: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sede'],
      )!,
    );
  }

  @override
  $CachedCategoriasTable createAlias(String alias) {
    return $CachedCategoriasTable(attachedDatabase, alias);
  }
}

class CachedCategoria extends DataClass implements Insertable<CachedCategoria> {
  final String codigo;
  final String nombre;
  final String? mnemotecnia;
  final String sede;
  const CachedCategoria({
    required this.codigo,
    required this.nombre,
    this.mnemotecnia,
    required this.sede,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['codigo'] = Variable<String>(codigo);
    map['nombre'] = Variable<String>(nombre);
    if (!nullToAbsent || mnemotecnia != null) {
      map['mnemotecnia'] = Variable<String>(mnemotecnia);
    }
    map['sede'] = Variable<String>(sede);
    return map;
  }

  CachedCategoriasCompanion toCompanion(bool nullToAbsent) {
    return CachedCategoriasCompanion(
      codigo: Value(codigo),
      nombre: Value(nombre),
      mnemotecnia: mnemotecnia == null && nullToAbsent
          ? const Value.absent()
          : Value(mnemotecnia),
      sede: Value(sede),
    );
  }

  factory CachedCategoria.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedCategoria(
      codigo: serializer.fromJson<String>(json['codigo']),
      nombre: serializer.fromJson<String>(json['nombre']),
      mnemotecnia: serializer.fromJson<String?>(json['mnemotecnia']),
      sede: serializer.fromJson<String>(json['sede']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'codigo': serializer.toJson<String>(codigo),
      'nombre': serializer.toJson<String>(nombre),
      'mnemotecnia': serializer.toJson<String?>(mnemotecnia),
      'sede': serializer.toJson<String>(sede),
    };
  }

  CachedCategoria copyWith({
    String? codigo,
    String? nombre,
    Value<String?> mnemotecnia = const Value.absent(),
    String? sede,
  }) => CachedCategoria(
    codigo: codigo ?? this.codigo,
    nombre: nombre ?? this.nombre,
    mnemotecnia: mnemotecnia.present ? mnemotecnia.value : this.mnemotecnia,
    sede: sede ?? this.sede,
  );
  CachedCategoria copyWithCompanion(CachedCategoriasCompanion data) {
    return CachedCategoria(
      codigo: data.codigo.present ? data.codigo.value : this.codigo,
      nombre: data.nombre.present ? data.nombre.value : this.nombre,
      mnemotecnia: data.mnemotecnia.present
          ? data.mnemotecnia.value
          : this.mnemotecnia,
      sede: data.sede.present ? data.sede.value : this.sede,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedCategoria(')
          ..write('codigo: $codigo, ')
          ..write('nombre: $nombre, ')
          ..write('mnemotecnia: $mnemotecnia, ')
          ..write('sede: $sede')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(codigo, nombre, mnemotecnia, sede);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedCategoria &&
          other.codigo == this.codigo &&
          other.nombre == this.nombre &&
          other.mnemotecnia == this.mnemotecnia &&
          other.sede == this.sede);
}

class CachedCategoriasCompanion extends UpdateCompanion<CachedCategoria> {
  final Value<String> codigo;
  final Value<String> nombre;
  final Value<String?> mnemotecnia;
  final Value<String> sede;
  final Value<int> rowid;
  const CachedCategoriasCompanion({
    this.codigo = const Value.absent(),
    this.nombre = const Value.absent(),
    this.mnemotecnia = const Value.absent(),
    this.sede = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedCategoriasCompanion.insert({
    required String codigo,
    required String nombre,
    this.mnemotecnia = const Value.absent(),
    required String sede,
    this.rowid = const Value.absent(),
  }) : codigo = Value(codigo),
       nombre = Value(nombre),
       sede = Value(sede);
  static Insertable<CachedCategoria> custom({
    Expression<String>? codigo,
    Expression<String>? nombre,
    Expression<String>? mnemotecnia,
    Expression<String>? sede,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (codigo != null) 'codigo': codigo,
      if (nombre != null) 'nombre': nombre,
      if (mnemotecnia != null) 'mnemotecnia': mnemotecnia,
      if (sede != null) 'sede': sede,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedCategoriasCompanion copyWith({
    Value<String>? codigo,
    Value<String>? nombre,
    Value<String?>? mnemotecnia,
    Value<String>? sede,
    Value<int>? rowid,
  }) {
    return CachedCategoriasCompanion(
      codigo: codigo ?? this.codigo,
      nombre: nombre ?? this.nombre,
      mnemotecnia: mnemotecnia ?? this.mnemotecnia,
      sede: sede ?? this.sede,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (codigo.present) {
      map['codigo'] = Variable<String>(codigo.value);
    }
    if (nombre.present) {
      map['nombre'] = Variable<String>(nombre.value);
    }
    if (mnemotecnia.present) {
      map['mnemotecnia'] = Variable<String>(mnemotecnia.value);
    }
    if (sede.present) {
      map['sede'] = Variable<String>(sede.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedCategoriasCompanion(')
          ..write('codigo: $codigo, ')
          ..write('nombre: $nombre, ')
          ..write('mnemotecnia: $mnemotecnia, ')
          ..write('sede: $sede, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedSubcategoriasTable extends CachedSubcategorias
    with TableInfo<$CachedSubcategoriasTable, CachedSubcategoria> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedSubcategoriasTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _codigoMeta = const VerificationMeta('codigo');
  @override
  late final GeneratedColumn<String> codigo = GeneratedColumn<String>(
    'codigo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _categoriaCodigoMeta = const VerificationMeta(
    'categoriaCodigo',
  );
  @override
  late final GeneratedColumn<String> categoriaCodigo = GeneratedColumn<String>(
    'categoria_codigo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _nombreMeta = const VerificationMeta('nombre');
  @override
  late final GeneratedColumn<String> nombre = GeneratedColumn<String>(
    'nombre',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _mnemotecniaMeta = const VerificationMeta(
    'mnemotecnia',
  );
  @override
  late final GeneratedColumn<String> mnemotecnia = GeneratedColumn<String>(
    'mnemotecnia',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _sedeMeta = const VerificationMeta('sede');
  @override
  late final GeneratedColumn<String> sede = GeneratedColumn<String>(
    'sede',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    codigo,
    categoriaCodigo,
    nombre,
    mnemotecnia,
    sede,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_subcategorias';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedSubcategoria> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('codigo')) {
      context.handle(
        _codigoMeta,
        codigo.isAcceptableOrUnknown(data['codigo']!, _codigoMeta),
      );
    } else if (isInserting) {
      context.missing(_codigoMeta);
    }
    if (data.containsKey('categoria_codigo')) {
      context.handle(
        _categoriaCodigoMeta,
        categoriaCodigo.isAcceptableOrUnknown(
          data['categoria_codigo']!,
          _categoriaCodigoMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_categoriaCodigoMeta);
    }
    if (data.containsKey('nombre')) {
      context.handle(
        _nombreMeta,
        nombre.isAcceptableOrUnknown(data['nombre']!, _nombreMeta),
      );
    } else if (isInserting) {
      context.missing(_nombreMeta);
    }
    if (data.containsKey('mnemotecnia')) {
      context.handle(
        _mnemotecniaMeta,
        mnemotecnia.isAcceptableOrUnknown(
          data['mnemotecnia']!,
          _mnemotecniaMeta,
        ),
      );
    }
    if (data.containsKey('sede')) {
      context.handle(
        _sedeMeta,
        sede.isAcceptableOrUnknown(data['sede']!, _sedeMeta),
      );
    } else if (isInserting) {
      context.missing(_sedeMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {categoriaCodigo, codigo};
  @override
  CachedSubcategoria map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedSubcategoria(
      codigo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}codigo'],
      )!,
      categoriaCodigo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}categoria_codigo'],
      )!,
      nombre: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}nombre'],
      )!,
      mnemotecnia: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}mnemotecnia'],
      ),
      sede: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sede'],
      )!,
    );
  }

  @override
  $CachedSubcategoriasTable createAlias(String alias) {
    return $CachedSubcategoriasTable(attachedDatabase, alias);
  }
}

class CachedSubcategoria extends DataClass
    implements Insertable<CachedSubcategoria> {
  final String codigo;
  final String categoriaCodigo;
  final String nombre;
  final String? mnemotecnia;
  final String sede;
  const CachedSubcategoria({
    required this.codigo,
    required this.categoriaCodigo,
    required this.nombre,
    this.mnemotecnia,
    required this.sede,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['codigo'] = Variable<String>(codigo);
    map['categoria_codigo'] = Variable<String>(categoriaCodigo);
    map['nombre'] = Variable<String>(nombre);
    if (!nullToAbsent || mnemotecnia != null) {
      map['mnemotecnia'] = Variable<String>(mnemotecnia);
    }
    map['sede'] = Variable<String>(sede);
    return map;
  }

  CachedSubcategoriasCompanion toCompanion(bool nullToAbsent) {
    return CachedSubcategoriasCompanion(
      codigo: Value(codigo),
      categoriaCodigo: Value(categoriaCodigo),
      nombre: Value(nombre),
      mnemotecnia: mnemotecnia == null && nullToAbsent
          ? const Value.absent()
          : Value(mnemotecnia),
      sede: Value(sede),
    );
  }

  factory CachedSubcategoria.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedSubcategoria(
      codigo: serializer.fromJson<String>(json['codigo']),
      categoriaCodigo: serializer.fromJson<String>(json['categoriaCodigo']),
      nombre: serializer.fromJson<String>(json['nombre']),
      mnemotecnia: serializer.fromJson<String?>(json['mnemotecnia']),
      sede: serializer.fromJson<String>(json['sede']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'codigo': serializer.toJson<String>(codigo),
      'categoriaCodigo': serializer.toJson<String>(categoriaCodigo),
      'nombre': serializer.toJson<String>(nombre),
      'mnemotecnia': serializer.toJson<String?>(mnemotecnia),
      'sede': serializer.toJson<String>(sede),
    };
  }

  CachedSubcategoria copyWith({
    String? codigo,
    String? categoriaCodigo,
    String? nombre,
    Value<String?> mnemotecnia = const Value.absent(),
    String? sede,
  }) => CachedSubcategoria(
    codigo: codigo ?? this.codigo,
    categoriaCodigo: categoriaCodigo ?? this.categoriaCodigo,
    nombre: nombre ?? this.nombre,
    mnemotecnia: mnemotecnia.present ? mnemotecnia.value : this.mnemotecnia,
    sede: sede ?? this.sede,
  );
  CachedSubcategoria copyWithCompanion(CachedSubcategoriasCompanion data) {
    return CachedSubcategoria(
      codigo: data.codigo.present ? data.codigo.value : this.codigo,
      categoriaCodigo: data.categoriaCodigo.present
          ? data.categoriaCodigo.value
          : this.categoriaCodigo,
      nombre: data.nombre.present ? data.nombre.value : this.nombre,
      mnemotecnia: data.mnemotecnia.present
          ? data.mnemotecnia.value
          : this.mnemotecnia,
      sede: data.sede.present ? data.sede.value : this.sede,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedSubcategoria(')
          ..write('codigo: $codigo, ')
          ..write('categoriaCodigo: $categoriaCodigo, ')
          ..write('nombre: $nombre, ')
          ..write('mnemotecnia: $mnemotecnia, ')
          ..write('sede: $sede')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(codigo, categoriaCodigo, nombre, mnemotecnia, sede);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedSubcategoria &&
          other.codigo == this.codigo &&
          other.categoriaCodigo == this.categoriaCodigo &&
          other.nombre == this.nombre &&
          other.mnemotecnia == this.mnemotecnia &&
          other.sede == this.sede);
}

class CachedSubcategoriasCompanion extends UpdateCompanion<CachedSubcategoria> {
  final Value<String> codigo;
  final Value<String> categoriaCodigo;
  final Value<String> nombre;
  final Value<String?> mnemotecnia;
  final Value<String> sede;
  final Value<int> rowid;
  const CachedSubcategoriasCompanion({
    this.codigo = const Value.absent(),
    this.categoriaCodigo = const Value.absent(),
    this.nombre = const Value.absent(),
    this.mnemotecnia = const Value.absent(),
    this.sede = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedSubcategoriasCompanion.insert({
    required String codigo,
    required String categoriaCodigo,
    required String nombre,
    this.mnemotecnia = const Value.absent(),
    required String sede,
    this.rowid = const Value.absent(),
  }) : codigo = Value(codigo),
       categoriaCodigo = Value(categoriaCodigo),
       nombre = Value(nombre),
       sede = Value(sede);
  static Insertable<CachedSubcategoria> custom({
    Expression<String>? codigo,
    Expression<String>? categoriaCodigo,
    Expression<String>? nombre,
    Expression<String>? mnemotecnia,
    Expression<String>? sede,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (codigo != null) 'codigo': codigo,
      if (categoriaCodigo != null) 'categoria_codigo': categoriaCodigo,
      if (nombre != null) 'nombre': nombre,
      if (mnemotecnia != null) 'mnemotecnia': mnemotecnia,
      if (sede != null) 'sede': sede,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedSubcategoriasCompanion copyWith({
    Value<String>? codigo,
    Value<String>? categoriaCodigo,
    Value<String>? nombre,
    Value<String?>? mnemotecnia,
    Value<String>? sede,
    Value<int>? rowid,
  }) {
    return CachedSubcategoriasCompanion(
      codigo: codigo ?? this.codigo,
      categoriaCodigo: categoriaCodigo ?? this.categoriaCodigo,
      nombre: nombre ?? this.nombre,
      mnemotecnia: mnemotecnia ?? this.mnemotecnia,
      sede: sede ?? this.sede,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (codigo.present) {
      map['codigo'] = Variable<String>(codigo.value);
    }
    if (categoriaCodigo.present) {
      map['categoria_codigo'] = Variable<String>(categoriaCodigo.value);
    }
    if (nombre.present) {
      map['nombre'] = Variable<String>(nombre.value);
    }
    if (mnemotecnia.present) {
      map['mnemotecnia'] = Variable<String>(mnemotecnia.value);
    }
    if (sede.present) {
      map['sede'] = Variable<String>(sede.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedSubcategoriasCompanion(')
          ..write('codigo: $codigo, ')
          ..write('categoriaCodigo: $categoriaCodigo, ')
          ..write('nombre: $nombre, ')
          ..write('mnemotecnia: $mnemotecnia, ')
          ..write('sede: $sede, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedProductosTable extends CachedProductos
    with TableInfo<$CachedProductosTable, CachedProducto> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedProductosTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _codigoMeta = const VerificationMeta('codigo');
  @override
  late final GeneratedColumn<String> codigo = GeneratedColumn<String>(
    'codigo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _codigoCompletoMeta = const VerificationMeta(
    'codigoCompleto',
  );
  @override
  late final GeneratedColumn<String> codigoCompleto = GeneratedColumn<String>(
    'codigo_completo',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _categoriaCodigoMeta = const VerificationMeta(
    'categoriaCodigo',
  );
  @override
  late final GeneratedColumn<String> categoriaCodigo = GeneratedColumn<String>(
    'categoria_codigo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _subcategoriaCodigoMeta =
      const VerificationMeta('subcategoriaCodigo');
  @override
  late final GeneratedColumn<String> subcategoriaCodigo =
      GeneratedColumn<String>(
        'subcategoria_codigo',
        aliasedName,
        false,
        type: DriftSqlType.string,
        requiredDuringInsert: true,
      );
  static const VerificationMeta _nombreMeta = const VerificationMeta('nombre');
  @override
  late final GeneratedColumn<String> nombre = GeneratedColumn<String>(
    'nombre',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _mnemotecniaMeta = const VerificationMeta(
    'mnemotecnia',
  );
  @override
  late final GeneratedColumn<String> mnemotecnia = GeneratedColumn<String>(
    'mnemotecnia',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _imagenUrlMeta = const VerificationMeta(
    'imagenUrl',
  );
  @override
  late final GeneratedColumn<String> imagenUrl = GeneratedColumn<String>(
    'imagen_url',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _estatusMeta = const VerificationMeta(
    'estatus',
  );
  @override
  late final GeneratedColumn<String> estatus = GeneratedColumn<String>(
    'estatus',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _marcaMeta = const VerificationMeta('marca');
  @override
  late final GeneratedColumn<String> marca = GeneratedColumn<String>(
    'marca',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _sedeMeta = const VerificationMeta('sede');
  @override
  late final GeneratedColumn<String> sede = GeneratedColumn<String>(
    'sede',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    codigo,
    codigoCompleto,
    categoriaCodigo,
    subcategoriaCodigo,
    nombre,
    mnemotecnia,
    imagenUrl,
    estatus,
    marca,
    sede,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_productos';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedProducto> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('codigo')) {
      context.handle(
        _codigoMeta,
        codigo.isAcceptableOrUnknown(data['codigo']!, _codigoMeta),
      );
    } else if (isInserting) {
      context.missing(_codigoMeta);
    }
    if (data.containsKey('codigo_completo')) {
      context.handle(
        _codigoCompletoMeta,
        codigoCompleto.isAcceptableOrUnknown(
          data['codigo_completo']!,
          _codigoCompletoMeta,
        ),
      );
    }
    if (data.containsKey('categoria_codigo')) {
      context.handle(
        _categoriaCodigoMeta,
        categoriaCodigo.isAcceptableOrUnknown(
          data['categoria_codigo']!,
          _categoriaCodigoMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_categoriaCodigoMeta);
    }
    if (data.containsKey('subcategoria_codigo')) {
      context.handle(
        _subcategoriaCodigoMeta,
        subcategoriaCodigo.isAcceptableOrUnknown(
          data['subcategoria_codigo']!,
          _subcategoriaCodigoMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_subcategoriaCodigoMeta);
    }
    if (data.containsKey('nombre')) {
      context.handle(
        _nombreMeta,
        nombre.isAcceptableOrUnknown(data['nombre']!, _nombreMeta),
      );
    } else if (isInserting) {
      context.missing(_nombreMeta);
    }
    if (data.containsKey('mnemotecnia')) {
      context.handle(
        _mnemotecniaMeta,
        mnemotecnia.isAcceptableOrUnknown(
          data['mnemotecnia']!,
          _mnemotecniaMeta,
        ),
      );
    }
    if (data.containsKey('imagen_url')) {
      context.handle(
        _imagenUrlMeta,
        imagenUrl.isAcceptableOrUnknown(data['imagen_url']!, _imagenUrlMeta),
      );
    }
    if (data.containsKey('estatus')) {
      context.handle(
        _estatusMeta,
        estatus.isAcceptableOrUnknown(data['estatus']!, _estatusMeta),
      );
    } else if (isInserting) {
      context.missing(_estatusMeta);
    }
    if (data.containsKey('marca')) {
      context.handle(
        _marcaMeta,
        marca.isAcceptableOrUnknown(data['marca']!, _marcaMeta),
      );
    } else if (isInserting) {
      context.missing(_marcaMeta);
    }
    if (data.containsKey('sede')) {
      context.handle(
        _sedeMeta,
        sede.isAcceptableOrUnknown(data['sede']!, _sedeMeta),
      );
    } else if (isInserting) {
      context.missing(_sedeMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CachedProducto map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedProducto(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      codigo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}codigo'],
      )!,
      codigoCompleto: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}codigo_completo'],
      ),
      categoriaCodigo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}categoria_codigo'],
      )!,
      subcategoriaCodigo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}subcategoria_codigo'],
      )!,
      nombre: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}nombre'],
      )!,
      mnemotecnia: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}mnemotecnia'],
      ),
      imagenUrl: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}imagen_url'],
      ),
      estatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}estatus'],
      )!,
      marca: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}marca'],
      )!,
      sede: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sede'],
      )!,
    );
  }

  @override
  $CachedProductosTable createAlias(String alias) {
    return $CachedProductosTable(attachedDatabase, alias);
  }
}

class CachedProducto extends DataClass implements Insertable<CachedProducto> {
  final String id;
  final String codigo;
  final String? codigoCompleto;
  final String categoriaCodigo;
  final String subcategoriaCodigo;
  final String nombre;
  final String? mnemotecnia;
  final String? imagenUrl;
  final String estatus;
  final String marca;
  final String sede;
  const CachedProducto({
    required this.id,
    required this.codigo,
    this.codigoCompleto,
    required this.categoriaCodigo,
    required this.subcategoriaCodigo,
    required this.nombre,
    this.mnemotecnia,
    this.imagenUrl,
    required this.estatus,
    required this.marca,
    required this.sede,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['codigo'] = Variable<String>(codigo);
    if (!nullToAbsent || codigoCompleto != null) {
      map['codigo_completo'] = Variable<String>(codigoCompleto);
    }
    map['categoria_codigo'] = Variable<String>(categoriaCodigo);
    map['subcategoria_codigo'] = Variable<String>(subcategoriaCodigo);
    map['nombre'] = Variable<String>(nombre);
    if (!nullToAbsent || mnemotecnia != null) {
      map['mnemotecnia'] = Variable<String>(mnemotecnia);
    }
    if (!nullToAbsent || imagenUrl != null) {
      map['imagen_url'] = Variable<String>(imagenUrl);
    }
    map['estatus'] = Variable<String>(estatus);
    map['marca'] = Variable<String>(marca);
    map['sede'] = Variable<String>(sede);
    return map;
  }

  CachedProductosCompanion toCompanion(bool nullToAbsent) {
    return CachedProductosCompanion(
      id: Value(id),
      codigo: Value(codigo),
      codigoCompleto: codigoCompleto == null && nullToAbsent
          ? const Value.absent()
          : Value(codigoCompleto),
      categoriaCodigo: Value(categoriaCodigo),
      subcategoriaCodigo: Value(subcategoriaCodigo),
      nombre: Value(nombre),
      mnemotecnia: mnemotecnia == null && nullToAbsent
          ? const Value.absent()
          : Value(mnemotecnia),
      imagenUrl: imagenUrl == null && nullToAbsent
          ? const Value.absent()
          : Value(imagenUrl),
      estatus: Value(estatus),
      marca: Value(marca),
      sede: Value(sede),
    );
  }

  factory CachedProducto.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedProducto(
      id: serializer.fromJson<String>(json['id']),
      codigo: serializer.fromJson<String>(json['codigo']),
      codigoCompleto: serializer.fromJson<String?>(json['codigoCompleto']),
      categoriaCodigo: serializer.fromJson<String>(json['categoriaCodigo']),
      subcategoriaCodigo: serializer.fromJson<String>(
        json['subcategoriaCodigo'],
      ),
      nombre: serializer.fromJson<String>(json['nombre']),
      mnemotecnia: serializer.fromJson<String?>(json['mnemotecnia']),
      imagenUrl: serializer.fromJson<String?>(json['imagenUrl']),
      estatus: serializer.fromJson<String>(json['estatus']),
      marca: serializer.fromJson<String>(json['marca']),
      sede: serializer.fromJson<String>(json['sede']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'codigo': serializer.toJson<String>(codigo),
      'codigoCompleto': serializer.toJson<String?>(codigoCompleto),
      'categoriaCodigo': serializer.toJson<String>(categoriaCodigo),
      'subcategoriaCodigo': serializer.toJson<String>(subcategoriaCodigo),
      'nombre': serializer.toJson<String>(nombre),
      'mnemotecnia': serializer.toJson<String?>(mnemotecnia),
      'imagenUrl': serializer.toJson<String?>(imagenUrl),
      'estatus': serializer.toJson<String>(estatus),
      'marca': serializer.toJson<String>(marca),
      'sede': serializer.toJson<String>(sede),
    };
  }

  CachedProducto copyWith({
    String? id,
    String? codigo,
    Value<String?> codigoCompleto = const Value.absent(),
    String? categoriaCodigo,
    String? subcategoriaCodigo,
    String? nombre,
    Value<String?> mnemotecnia = const Value.absent(),
    Value<String?> imagenUrl = const Value.absent(),
    String? estatus,
    String? marca,
    String? sede,
  }) => CachedProducto(
    id: id ?? this.id,
    codigo: codigo ?? this.codigo,
    codigoCompleto: codigoCompleto.present
        ? codigoCompleto.value
        : this.codigoCompleto,
    categoriaCodigo: categoriaCodigo ?? this.categoriaCodigo,
    subcategoriaCodigo: subcategoriaCodigo ?? this.subcategoriaCodigo,
    nombre: nombre ?? this.nombre,
    mnemotecnia: mnemotecnia.present ? mnemotecnia.value : this.mnemotecnia,
    imagenUrl: imagenUrl.present ? imagenUrl.value : this.imagenUrl,
    estatus: estatus ?? this.estatus,
    marca: marca ?? this.marca,
    sede: sede ?? this.sede,
  );
  CachedProducto copyWithCompanion(CachedProductosCompanion data) {
    return CachedProducto(
      id: data.id.present ? data.id.value : this.id,
      codigo: data.codigo.present ? data.codigo.value : this.codigo,
      codigoCompleto: data.codigoCompleto.present
          ? data.codigoCompleto.value
          : this.codigoCompleto,
      categoriaCodigo: data.categoriaCodigo.present
          ? data.categoriaCodigo.value
          : this.categoriaCodigo,
      subcategoriaCodigo: data.subcategoriaCodigo.present
          ? data.subcategoriaCodigo.value
          : this.subcategoriaCodigo,
      nombre: data.nombre.present ? data.nombre.value : this.nombre,
      mnemotecnia: data.mnemotecnia.present
          ? data.mnemotecnia.value
          : this.mnemotecnia,
      imagenUrl: data.imagenUrl.present ? data.imagenUrl.value : this.imagenUrl,
      estatus: data.estatus.present ? data.estatus.value : this.estatus,
      marca: data.marca.present ? data.marca.value : this.marca,
      sede: data.sede.present ? data.sede.value : this.sede,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedProducto(')
          ..write('id: $id, ')
          ..write('codigo: $codigo, ')
          ..write('codigoCompleto: $codigoCompleto, ')
          ..write('categoriaCodigo: $categoriaCodigo, ')
          ..write('subcategoriaCodigo: $subcategoriaCodigo, ')
          ..write('nombre: $nombre, ')
          ..write('mnemotecnia: $mnemotecnia, ')
          ..write('imagenUrl: $imagenUrl, ')
          ..write('estatus: $estatus, ')
          ..write('marca: $marca, ')
          ..write('sede: $sede')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    codigo,
    codigoCompleto,
    categoriaCodigo,
    subcategoriaCodigo,
    nombre,
    mnemotecnia,
    imagenUrl,
    estatus,
    marca,
    sede,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedProducto &&
          other.id == this.id &&
          other.codigo == this.codigo &&
          other.codigoCompleto == this.codigoCompleto &&
          other.categoriaCodigo == this.categoriaCodigo &&
          other.subcategoriaCodigo == this.subcategoriaCodigo &&
          other.nombre == this.nombre &&
          other.mnemotecnia == this.mnemotecnia &&
          other.imagenUrl == this.imagenUrl &&
          other.estatus == this.estatus &&
          other.marca == this.marca &&
          other.sede == this.sede);
}

class CachedProductosCompanion extends UpdateCompanion<CachedProducto> {
  final Value<String> id;
  final Value<String> codigo;
  final Value<String?> codigoCompleto;
  final Value<String> categoriaCodigo;
  final Value<String> subcategoriaCodigo;
  final Value<String> nombre;
  final Value<String?> mnemotecnia;
  final Value<String?> imagenUrl;
  final Value<String> estatus;
  final Value<String> marca;
  final Value<String> sede;
  final Value<int> rowid;
  const CachedProductosCompanion({
    this.id = const Value.absent(),
    this.codigo = const Value.absent(),
    this.codigoCompleto = const Value.absent(),
    this.categoriaCodigo = const Value.absent(),
    this.subcategoriaCodigo = const Value.absent(),
    this.nombre = const Value.absent(),
    this.mnemotecnia = const Value.absent(),
    this.imagenUrl = const Value.absent(),
    this.estatus = const Value.absent(),
    this.marca = const Value.absent(),
    this.sede = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedProductosCompanion.insert({
    required String id,
    required String codigo,
    this.codigoCompleto = const Value.absent(),
    required String categoriaCodigo,
    required String subcategoriaCodigo,
    required String nombre,
    this.mnemotecnia = const Value.absent(),
    this.imagenUrl = const Value.absent(),
    required String estatus,
    required String marca,
    required String sede,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       codigo = Value(codigo),
       categoriaCodigo = Value(categoriaCodigo),
       subcategoriaCodigo = Value(subcategoriaCodigo),
       nombre = Value(nombre),
       estatus = Value(estatus),
       marca = Value(marca),
       sede = Value(sede);
  static Insertable<CachedProducto> custom({
    Expression<String>? id,
    Expression<String>? codigo,
    Expression<String>? codigoCompleto,
    Expression<String>? categoriaCodigo,
    Expression<String>? subcategoriaCodigo,
    Expression<String>? nombre,
    Expression<String>? mnemotecnia,
    Expression<String>? imagenUrl,
    Expression<String>? estatus,
    Expression<String>? marca,
    Expression<String>? sede,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (codigo != null) 'codigo': codigo,
      if (codigoCompleto != null) 'codigo_completo': codigoCompleto,
      if (categoriaCodigo != null) 'categoria_codigo': categoriaCodigo,
      if (subcategoriaCodigo != null) 'subcategoria_codigo': subcategoriaCodigo,
      if (nombre != null) 'nombre': nombre,
      if (mnemotecnia != null) 'mnemotecnia': mnemotecnia,
      if (imagenUrl != null) 'imagen_url': imagenUrl,
      if (estatus != null) 'estatus': estatus,
      if (marca != null) 'marca': marca,
      if (sede != null) 'sede': sede,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedProductosCompanion copyWith({
    Value<String>? id,
    Value<String>? codigo,
    Value<String?>? codigoCompleto,
    Value<String>? categoriaCodigo,
    Value<String>? subcategoriaCodigo,
    Value<String>? nombre,
    Value<String?>? mnemotecnia,
    Value<String?>? imagenUrl,
    Value<String>? estatus,
    Value<String>? marca,
    Value<String>? sede,
    Value<int>? rowid,
  }) {
    return CachedProductosCompanion(
      id: id ?? this.id,
      codigo: codigo ?? this.codigo,
      codigoCompleto: codigoCompleto ?? this.codigoCompleto,
      categoriaCodigo: categoriaCodigo ?? this.categoriaCodigo,
      subcategoriaCodigo: subcategoriaCodigo ?? this.subcategoriaCodigo,
      nombre: nombre ?? this.nombre,
      mnemotecnia: mnemotecnia ?? this.mnemotecnia,
      imagenUrl: imagenUrl ?? this.imagenUrl,
      estatus: estatus ?? this.estatus,
      marca: marca ?? this.marca,
      sede: sede ?? this.sede,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (codigo.present) {
      map['codigo'] = Variable<String>(codigo.value);
    }
    if (codigoCompleto.present) {
      map['codigo_completo'] = Variable<String>(codigoCompleto.value);
    }
    if (categoriaCodigo.present) {
      map['categoria_codigo'] = Variable<String>(categoriaCodigo.value);
    }
    if (subcategoriaCodigo.present) {
      map['subcategoria_codigo'] = Variable<String>(subcategoriaCodigo.value);
    }
    if (nombre.present) {
      map['nombre'] = Variable<String>(nombre.value);
    }
    if (mnemotecnia.present) {
      map['mnemotecnia'] = Variable<String>(mnemotecnia.value);
    }
    if (imagenUrl.present) {
      map['imagen_url'] = Variable<String>(imagenUrl.value);
    }
    if (estatus.present) {
      map['estatus'] = Variable<String>(estatus.value);
    }
    if (marca.present) {
      map['marca'] = Variable<String>(marca.value);
    }
    if (sede.present) {
      map['sede'] = Variable<String>(sede.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedProductosCompanion(')
          ..write('id: $id, ')
          ..write('codigo: $codigo, ')
          ..write('codigoCompleto: $codigoCompleto, ')
          ..write('categoriaCodigo: $categoriaCodigo, ')
          ..write('subcategoriaCodigo: $subcategoriaCodigo, ')
          ..write('nombre: $nombre, ')
          ..write('mnemotecnia: $mnemotecnia, ')
          ..write('imagenUrl: $imagenUrl, ')
          ..write('estatus: $estatus, ')
          ..write('marca: $marca, ')
          ..write('sede: $sede, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CachedEstatusProductoTable extends CachedEstatusProducto
    with TableInfo<$CachedEstatusProductoTable, CachedEstatusProductoData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CachedEstatusProductoTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _codigoMeta = const VerificationMeta('codigo');
  @override
  late final GeneratedColumn<String> codigo = GeneratedColumn<String>(
    'codigo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _nombreMeta = const VerificationMeta('nombre');
  @override
  late final GeneratedColumn<String> nombre = GeneratedColumn<String>(
    'nombre',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _esInfaltableMeta = const VerificationMeta(
    'esInfaltable',
  );
  @override
  late final GeneratedColumn<bool> esInfaltable = GeneratedColumn<bool>(
    'es_infaltable',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("es_infaltable" IN (0, 1))',
    ),
  );
  @override
  List<GeneratedColumn> get $columns => [codigo, nombre, esInfaltable];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cached_estatus_producto';
  @override
  VerificationContext validateIntegrity(
    Insertable<CachedEstatusProductoData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('codigo')) {
      context.handle(
        _codigoMeta,
        codigo.isAcceptableOrUnknown(data['codigo']!, _codigoMeta),
      );
    } else if (isInserting) {
      context.missing(_codigoMeta);
    }
    if (data.containsKey('nombre')) {
      context.handle(
        _nombreMeta,
        nombre.isAcceptableOrUnknown(data['nombre']!, _nombreMeta),
      );
    } else if (isInserting) {
      context.missing(_nombreMeta);
    }
    if (data.containsKey('es_infaltable')) {
      context.handle(
        _esInfaltableMeta,
        esInfaltable.isAcceptableOrUnknown(
          data['es_infaltable']!,
          _esInfaltableMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_esInfaltableMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {codigo};
  @override
  CachedEstatusProductoData map(
    Map<String, dynamic> data, {
    String? tablePrefix,
  }) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CachedEstatusProductoData(
      codigo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}codigo'],
      )!,
      nombre: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}nombre'],
      )!,
      esInfaltable: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}es_infaltable'],
      )!,
    );
  }

  @override
  $CachedEstatusProductoTable createAlias(String alias) {
    return $CachedEstatusProductoTable(attachedDatabase, alias);
  }
}

class CachedEstatusProductoData extends DataClass
    implements Insertable<CachedEstatusProductoData> {
  final String codigo;
  final String nombre;
  final bool esInfaltable;
  const CachedEstatusProductoData({
    required this.codigo,
    required this.nombre,
    required this.esInfaltable,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['codigo'] = Variable<String>(codigo);
    map['nombre'] = Variable<String>(nombre);
    map['es_infaltable'] = Variable<bool>(esInfaltable);
    return map;
  }

  CachedEstatusProductoCompanion toCompanion(bool nullToAbsent) {
    return CachedEstatusProductoCompanion(
      codigo: Value(codigo),
      nombre: Value(nombre),
      esInfaltable: Value(esInfaltable),
    );
  }

  factory CachedEstatusProductoData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CachedEstatusProductoData(
      codigo: serializer.fromJson<String>(json['codigo']),
      nombre: serializer.fromJson<String>(json['nombre']),
      esInfaltable: serializer.fromJson<bool>(json['esInfaltable']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'codigo': serializer.toJson<String>(codigo),
      'nombre': serializer.toJson<String>(nombre),
      'esInfaltable': serializer.toJson<bool>(esInfaltable),
    };
  }

  CachedEstatusProductoData copyWith({
    String? codigo,
    String? nombre,
    bool? esInfaltable,
  }) => CachedEstatusProductoData(
    codigo: codigo ?? this.codigo,
    nombre: nombre ?? this.nombre,
    esInfaltable: esInfaltable ?? this.esInfaltable,
  );
  CachedEstatusProductoData copyWithCompanion(
    CachedEstatusProductoCompanion data,
  ) {
    return CachedEstatusProductoData(
      codigo: data.codigo.present ? data.codigo.value : this.codigo,
      nombre: data.nombre.present ? data.nombre.value : this.nombre,
      esInfaltable: data.esInfaltable.present
          ? data.esInfaltable.value
          : this.esInfaltable,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CachedEstatusProductoData(')
          ..write('codigo: $codigo, ')
          ..write('nombre: $nombre, ')
          ..write('esInfaltable: $esInfaltable')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(codigo, nombre, esInfaltable);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CachedEstatusProductoData &&
          other.codigo == this.codigo &&
          other.nombre == this.nombre &&
          other.esInfaltable == this.esInfaltable);
}

class CachedEstatusProductoCompanion
    extends UpdateCompanion<CachedEstatusProductoData> {
  final Value<String> codigo;
  final Value<String> nombre;
  final Value<bool> esInfaltable;
  final Value<int> rowid;
  const CachedEstatusProductoCompanion({
    this.codigo = const Value.absent(),
    this.nombre = const Value.absent(),
    this.esInfaltable = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CachedEstatusProductoCompanion.insert({
    required String codigo,
    required String nombre,
    required bool esInfaltable,
    this.rowid = const Value.absent(),
  }) : codigo = Value(codigo),
       nombre = Value(nombre),
       esInfaltable = Value(esInfaltable);
  static Insertable<CachedEstatusProductoData> custom({
    Expression<String>? codigo,
    Expression<String>? nombre,
    Expression<bool>? esInfaltable,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (codigo != null) 'codigo': codigo,
      if (nombre != null) 'nombre': nombre,
      if (esInfaltable != null) 'es_infaltable': esInfaltable,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CachedEstatusProductoCompanion copyWith({
    Value<String>? codigo,
    Value<String>? nombre,
    Value<bool>? esInfaltable,
    Value<int>? rowid,
  }) {
    return CachedEstatusProductoCompanion(
      codigo: codigo ?? this.codigo,
      nombre: nombre ?? this.nombre,
      esInfaltable: esInfaltable ?? this.esInfaltable,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (codigo.present) {
      map['codigo'] = Variable<String>(codigo.value);
    }
    if (nombre.present) {
      map['nombre'] = Variable<String>(nombre.value);
    }
    if (esInfaltable.present) {
      map['es_infaltable'] = Variable<bool>(esInfaltable.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CachedEstatusProductoCompanion(')
          ..write('codigo: $codigo, ')
          ..write('nombre: $nombre, ')
          ..write('esInfaltable: $esInfaltable, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $CacheMetaTable extends CacheMeta
    with TableInfo<$CacheMetaTable, CacheMetaData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CacheMetaTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(1),
  );
  static const VerificationMeta _sedeMeta = const VerificationMeta('sede');
  @override
  late final GeneratedColumn<String> sede = GeneratedColumn<String>(
    'sede',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _configVersionMeta = const VerificationMeta(
    'configVersion',
  );
  @override
  late final GeneratedColumn<int> configVersion = GeneratedColumn<int>(
    'config_version',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _versionDatosMeta = const VerificationMeta(
    'versionDatos',
  );
  @override
  late final GeneratedColumn<String> versionDatos = GeneratedColumn<String>(
    'version_datos',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _syncedAtMeta = const VerificationMeta(
    'syncedAt',
  );
  @override
  late final GeneratedColumn<DateTime> syncedAt = GeneratedColumn<DateTime>(
    'synced_at',
    aliasedName,
    true,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _soloInfaltablesDefaultMeta =
      const VerificationMeta('soloInfaltablesDefault');
  @override
  late final GeneratedColumn<bool> soloInfaltablesDefault =
      GeneratedColumn<bool>(
        'solo_infaltables_default',
        aliasedName,
        false,
        type: DriftSqlType.bool,
        requiredDuringInsert: false,
        defaultConstraints: GeneratedColumn.constraintIsAlways(
          'CHECK ("solo_infaltables_default" IN (0, 1))',
        ),
        defaultValue: const Constant(false),
      );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    sede,
    configVersion,
    versionDatos,
    syncedAt,
    soloInfaltablesDefault,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cache_meta';
  @override
  VerificationContext validateIntegrity(
    Insertable<CacheMetaData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('sede')) {
      context.handle(
        _sedeMeta,
        sede.isAcceptableOrUnknown(data['sede']!, _sedeMeta),
      );
    }
    if (data.containsKey('config_version')) {
      context.handle(
        _configVersionMeta,
        configVersion.isAcceptableOrUnknown(
          data['config_version']!,
          _configVersionMeta,
        ),
      );
    }
    if (data.containsKey('version_datos')) {
      context.handle(
        _versionDatosMeta,
        versionDatos.isAcceptableOrUnknown(
          data['version_datos']!,
          _versionDatosMeta,
        ),
      );
    }
    if (data.containsKey('synced_at')) {
      context.handle(
        _syncedAtMeta,
        syncedAt.isAcceptableOrUnknown(data['synced_at']!, _syncedAtMeta),
      );
    }
    if (data.containsKey('solo_infaltables_default')) {
      context.handle(
        _soloInfaltablesDefaultMeta,
        soloInfaltablesDefault.isAcceptableOrUnknown(
          data['solo_infaltables_default']!,
          _soloInfaltablesDefaultMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  CacheMetaData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CacheMetaData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      sede: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sede'],
      ),
      configVersion: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}config_version'],
      ),
      versionDatos: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}version_datos'],
      ),
      syncedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}synced_at'],
      ),
      soloInfaltablesDefault: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}solo_infaltables_default'],
      )!,
    );
  }

  @override
  $CacheMetaTable createAlias(String alias) {
    return $CacheMetaTable(attachedDatabase, alias);
  }
}

class CacheMetaData extends DataClass implements Insertable<CacheMetaData> {
  final int id;
  final String? sede;
  final int? configVersion;
  final String? versionDatos;
  final DateTime? syncedAt;
  final bool soloInfaltablesDefault;
  const CacheMetaData({
    required this.id,
    this.sede,
    this.configVersion,
    this.versionDatos,
    this.syncedAt,
    required this.soloInfaltablesDefault,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    if (!nullToAbsent || sede != null) {
      map['sede'] = Variable<String>(sede);
    }
    if (!nullToAbsent || configVersion != null) {
      map['config_version'] = Variable<int>(configVersion);
    }
    if (!nullToAbsent || versionDatos != null) {
      map['version_datos'] = Variable<String>(versionDatos);
    }
    if (!nullToAbsent || syncedAt != null) {
      map['synced_at'] = Variable<DateTime>(syncedAt);
    }
    map['solo_infaltables_default'] = Variable<bool>(soloInfaltablesDefault);
    return map;
  }

  CacheMetaCompanion toCompanion(bool nullToAbsent) {
    return CacheMetaCompanion(
      id: Value(id),
      sede: sede == null && nullToAbsent ? const Value.absent() : Value(sede),
      configVersion: configVersion == null && nullToAbsent
          ? const Value.absent()
          : Value(configVersion),
      versionDatos: versionDatos == null && nullToAbsent
          ? const Value.absent()
          : Value(versionDatos),
      syncedAt: syncedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(syncedAt),
      soloInfaltablesDefault: Value(soloInfaltablesDefault),
    );
  }

  factory CacheMetaData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CacheMetaData(
      id: serializer.fromJson<int>(json['id']),
      sede: serializer.fromJson<String?>(json['sede']),
      configVersion: serializer.fromJson<int?>(json['configVersion']),
      versionDatos: serializer.fromJson<String?>(json['versionDatos']),
      syncedAt: serializer.fromJson<DateTime?>(json['syncedAt']),
      soloInfaltablesDefault: serializer.fromJson<bool>(
        json['soloInfaltablesDefault'],
      ),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'sede': serializer.toJson<String?>(sede),
      'configVersion': serializer.toJson<int?>(configVersion),
      'versionDatos': serializer.toJson<String?>(versionDatos),
      'syncedAt': serializer.toJson<DateTime?>(syncedAt),
      'soloInfaltablesDefault': serializer.toJson<bool>(soloInfaltablesDefault),
    };
  }

  CacheMetaData copyWith({
    int? id,
    Value<String?> sede = const Value.absent(),
    Value<int?> configVersion = const Value.absent(),
    Value<String?> versionDatos = const Value.absent(),
    Value<DateTime?> syncedAt = const Value.absent(),
    bool? soloInfaltablesDefault,
  }) => CacheMetaData(
    id: id ?? this.id,
    sede: sede.present ? sede.value : this.sede,
    configVersion: configVersion.present
        ? configVersion.value
        : this.configVersion,
    versionDatos: versionDatos.present ? versionDatos.value : this.versionDatos,
    syncedAt: syncedAt.present ? syncedAt.value : this.syncedAt,
    soloInfaltablesDefault:
        soloInfaltablesDefault ?? this.soloInfaltablesDefault,
  );
  CacheMetaData copyWithCompanion(CacheMetaCompanion data) {
    return CacheMetaData(
      id: data.id.present ? data.id.value : this.id,
      sede: data.sede.present ? data.sede.value : this.sede,
      configVersion: data.configVersion.present
          ? data.configVersion.value
          : this.configVersion,
      versionDatos: data.versionDatos.present
          ? data.versionDatos.value
          : this.versionDatos,
      syncedAt: data.syncedAt.present ? data.syncedAt.value : this.syncedAt,
      soloInfaltablesDefault: data.soloInfaltablesDefault.present
          ? data.soloInfaltablesDefault.value
          : this.soloInfaltablesDefault,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CacheMetaData(')
          ..write('id: $id, ')
          ..write('sede: $sede, ')
          ..write('configVersion: $configVersion, ')
          ..write('versionDatos: $versionDatos, ')
          ..write('syncedAt: $syncedAt, ')
          ..write('soloInfaltablesDefault: $soloInfaltablesDefault')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    sede,
    configVersion,
    versionDatos,
    syncedAt,
    soloInfaltablesDefault,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CacheMetaData &&
          other.id == this.id &&
          other.sede == this.sede &&
          other.configVersion == this.configVersion &&
          other.versionDatos == this.versionDatos &&
          other.syncedAt == this.syncedAt &&
          other.soloInfaltablesDefault == this.soloInfaltablesDefault);
}

class CacheMetaCompanion extends UpdateCompanion<CacheMetaData> {
  final Value<int> id;
  final Value<String?> sede;
  final Value<int?> configVersion;
  final Value<String?> versionDatos;
  final Value<DateTime?> syncedAt;
  final Value<bool> soloInfaltablesDefault;
  const CacheMetaCompanion({
    this.id = const Value.absent(),
    this.sede = const Value.absent(),
    this.configVersion = const Value.absent(),
    this.versionDatos = const Value.absent(),
    this.syncedAt = const Value.absent(),
    this.soloInfaltablesDefault = const Value.absent(),
  });
  CacheMetaCompanion.insert({
    this.id = const Value.absent(),
    this.sede = const Value.absent(),
    this.configVersion = const Value.absent(),
    this.versionDatos = const Value.absent(),
    this.syncedAt = const Value.absent(),
    this.soloInfaltablesDefault = const Value.absent(),
  });
  static Insertable<CacheMetaData> custom({
    Expression<int>? id,
    Expression<String>? sede,
    Expression<int>? configVersion,
    Expression<String>? versionDatos,
    Expression<DateTime>? syncedAt,
    Expression<bool>? soloInfaltablesDefault,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (sede != null) 'sede': sede,
      if (configVersion != null) 'config_version': configVersion,
      if (versionDatos != null) 'version_datos': versionDatos,
      if (syncedAt != null) 'synced_at': syncedAt,
      if (soloInfaltablesDefault != null)
        'solo_infaltables_default': soloInfaltablesDefault,
    });
  }

  CacheMetaCompanion copyWith({
    Value<int>? id,
    Value<String?>? sede,
    Value<int?>? configVersion,
    Value<String?>? versionDatos,
    Value<DateTime?>? syncedAt,
    Value<bool>? soloInfaltablesDefault,
  }) {
    return CacheMetaCompanion(
      id: id ?? this.id,
      sede: sede ?? this.sede,
      configVersion: configVersion ?? this.configVersion,
      versionDatos: versionDatos ?? this.versionDatos,
      syncedAt: syncedAt ?? this.syncedAt,
      soloInfaltablesDefault:
          soloInfaltablesDefault ?? this.soloInfaltablesDefault,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (sede.present) {
      map['sede'] = Variable<String>(sede.value);
    }
    if (configVersion.present) {
      map['config_version'] = Variable<int>(configVersion.value);
    }
    if (versionDatos.present) {
      map['version_datos'] = Variable<String>(versionDatos.value);
    }
    if (syncedAt.present) {
      map['synced_at'] = Variable<DateTime>(syncedAt.value);
    }
    if (soloInfaltablesDefault.present) {
      map['solo_infaltables_default'] = Variable<bool>(
        soloInfaltablesDefault.value,
      );
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CacheMetaCompanion(')
          ..write('id: $id, ')
          ..write('sede: $sede, ')
          ..write('configVersion: $configVersion, ')
          ..write('versionDatos: $versionDatos, ')
          ..write('syncedAt: $syncedAt, ')
          ..write('soloInfaltablesDefault: $soloInfaltablesDefault')
          ..write(')'))
        .toString();
  }
}

class $PendingGameResultsTable extends PendingGameResults
    with TableInfo<$PendingGameResultsTable, PendingGameResult> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PendingGameResultsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _usuarioIdMeta = const VerificationMeta(
    'usuarioId',
  );
  @override
  late final GeneratedColumn<String> usuarioId = GeneratedColumn<String>(
    'usuario_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _tipoJuegoMeta = const VerificationMeta(
    'tipoJuego',
  );
  @override
  late final GeneratedColumn<String> tipoJuego = GeneratedColumn<String>(
    'tipo_juego',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _aciertosMeta = const VerificationMeta(
    'aciertos',
  );
  @override
  late final GeneratedColumn<int> aciertos = GeneratedColumn<int>(
    'aciertos',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _fallosMeta = const VerificationMeta('fallos');
  @override
  late final GeneratedColumn<int> fallos = GeneratedColumn<int>(
    'fallos',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _totalPreguntasMeta = const VerificationMeta(
    'totalPreguntas',
  );
  @override
  late final GeneratedColumn<int> totalPreguntas = GeneratedColumn<int>(
    'total_preguntas',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _duracionSegundosMeta = const VerificationMeta(
    'duracionSegundos',
  );
  @override
  late final GeneratedColumn<int> duracionSegundos = GeneratedColumn<int>(
    'duracion_segundos',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _sedeMeta = const VerificationMeta('sede');
  @override
  late final GeneratedColumn<String> sede = GeneratedColumn<String>(
    'sede',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _configuracionJsonMeta = const VerificationMeta(
    'configuracionJson',
  );
  @override
  late final GeneratedColumn<String> configuracionJson =
      GeneratedColumn<String>(
        'configuracion_json',
        aliasedName,
        false,
        type: DriftSqlType.string,
        requiredDuringInsert: true,
      );
  static const VerificationMeta _detalleInteraccionesJsonMeta =
      const VerificationMeta('detalleInteraccionesJson');
  @override
  late final GeneratedColumn<String> detalleInteraccionesJson =
      GeneratedColumn<String>(
        'detalle_interacciones_json',
        aliasedName,
        false,
        type: DriftSqlType.string,
        requiredDuringInsert: true,
      );
  static const VerificationMeta _erroresJsonMeta = const VerificationMeta(
    'erroresJson',
  );
  @override
  late final GeneratedColumn<String> erroresJson = GeneratedColumn<String>(
    'errores_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _creadoEnMeta = const VerificationMeta(
    'creadoEn',
  );
  @override
  late final GeneratedColumn<DateTime> creadoEn = GeneratedColumn<DateTime>(
    'creado_en',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    usuarioId,
    tipoJuego,
    aciertos,
    fallos,
    totalPreguntas,
    duracionSegundos,
    sede,
    configuracionJson,
    detalleInteraccionesJson,
    erroresJson,
    creadoEn,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'pending_game_results';
  @override
  VerificationContext validateIntegrity(
    Insertable<PendingGameResult> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('usuario_id')) {
      context.handle(
        _usuarioIdMeta,
        usuarioId.isAcceptableOrUnknown(data['usuario_id']!, _usuarioIdMeta),
      );
    } else if (isInserting) {
      context.missing(_usuarioIdMeta);
    }
    if (data.containsKey('tipo_juego')) {
      context.handle(
        _tipoJuegoMeta,
        tipoJuego.isAcceptableOrUnknown(data['tipo_juego']!, _tipoJuegoMeta),
      );
    } else if (isInserting) {
      context.missing(_tipoJuegoMeta);
    }
    if (data.containsKey('aciertos')) {
      context.handle(
        _aciertosMeta,
        aciertos.isAcceptableOrUnknown(data['aciertos']!, _aciertosMeta),
      );
    } else if (isInserting) {
      context.missing(_aciertosMeta);
    }
    if (data.containsKey('fallos')) {
      context.handle(
        _fallosMeta,
        fallos.isAcceptableOrUnknown(data['fallos']!, _fallosMeta),
      );
    } else if (isInserting) {
      context.missing(_fallosMeta);
    }
    if (data.containsKey('total_preguntas')) {
      context.handle(
        _totalPreguntasMeta,
        totalPreguntas.isAcceptableOrUnknown(
          data['total_preguntas']!,
          _totalPreguntasMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_totalPreguntasMeta);
    }
    if (data.containsKey('duracion_segundos')) {
      context.handle(
        _duracionSegundosMeta,
        duracionSegundos.isAcceptableOrUnknown(
          data['duracion_segundos']!,
          _duracionSegundosMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_duracionSegundosMeta);
    }
    if (data.containsKey('sede')) {
      context.handle(
        _sedeMeta,
        sede.isAcceptableOrUnknown(data['sede']!, _sedeMeta),
      );
    } else if (isInserting) {
      context.missing(_sedeMeta);
    }
    if (data.containsKey('configuracion_json')) {
      context.handle(
        _configuracionJsonMeta,
        configuracionJson.isAcceptableOrUnknown(
          data['configuracion_json']!,
          _configuracionJsonMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_configuracionJsonMeta);
    }
    if (data.containsKey('detalle_interacciones_json')) {
      context.handle(
        _detalleInteraccionesJsonMeta,
        detalleInteraccionesJson.isAcceptableOrUnknown(
          data['detalle_interacciones_json']!,
          _detalleInteraccionesJsonMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_detalleInteraccionesJsonMeta);
    }
    if (data.containsKey('errores_json')) {
      context.handle(
        _erroresJsonMeta,
        erroresJson.isAcceptableOrUnknown(
          data['errores_json']!,
          _erroresJsonMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_erroresJsonMeta);
    }
    if (data.containsKey('creado_en')) {
      context.handle(
        _creadoEnMeta,
        creadoEn.isAcceptableOrUnknown(data['creado_en']!, _creadoEnMeta),
      );
    } else if (isInserting) {
      context.missing(_creadoEnMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  PendingGameResult map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return PendingGameResult(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      usuarioId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}usuario_id'],
      )!,
      tipoJuego: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}tipo_juego'],
      )!,
      aciertos: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}aciertos'],
      )!,
      fallos: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}fallos'],
      )!,
      totalPreguntas: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}total_preguntas'],
      )!,
      duracionSegundos: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}duracion_segundos'],
      )!,
      sede: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sede'],
      )!,
      configuracionJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}configuracion_json'],
      )!,
      detalleInteraccionesJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}detalle_interacciones_json'],
      )!,
      erroresJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}errores_json'],
      )!,
      creadoEn: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}creado_en'],
      )!,
    );
  }

  @override
  $PendingGameResultsTable createAlias(String alias) {
    return $PendingGameResultsTable(attachedDatabase, alias);
  }
}

class PendingGameResult extends DataClass
    implements Insertable<PendingGameResult> {
  final int id;
  final String usuarioId;
  final String tipoJuego;
  final int aciertos;
  final int fallos;
  final int totalPreguntas;
  final int duracionSegundos;
  final String sede;
  final String configuracionJson;
  final String detalleInteraccionesJson;
  final String erroresJson;
  final DateTime creadoEn;
  const PendingGameResult({
    required this.id,
    required this.usuarioId,
    required this.tipoJuego,
    required this.aciertos,
    required this.fallos,
    required this.totalPreguntas,
    required this.duracionSegundos,
    required this.sede,
    required this.configuracionJson,
    required this.detalleInteraccionesJson,
    required this.erroresJson,
    required this.creadoEn,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['usuario_id'] = Variable<String>(usuarioId);
    map['tipo_juego'] = Variable<String>(tipoJuego);
    map['aciertos'] = Variable<int>(aciertos);
    map['fallos'] = Variable<int>(fallos);
    map['total_preguntas'] = Variable<int>(totalPreguntas);
    map['duracion_segundos'] = Variable<int>(duracionSegundos);
    map['sede'] = Variable<String>(sede);
    map['configuracion_json'] = Variable<String>(configuracionJson);
    map['detalle_interacciones_json'] = Variable<String>(
      detalleInteraccionesJson,
    );
    map['errores_json'] = Variable<String>(erroresJson);
    map['creado_en'] = Variable<DateTime>(creadoEn);
    return map;
  }

  PendingGameResultsCompanion toCompanion(bool nullToAbsent) {
    return PendingGameResultsCompanion(
      id: Value(id),
      usuarioId: Value(usuarioId),
      tipoJuego: Value(tipoJuego),
      aciertos: Value(aciertos),
      fallos: Value(fallos),
      totalPreguntas: Value(totalPreguntas),
      duracionSegundos: Value(duracionSegundos),
      sede: Value(sede),
      configuracionJson: Value(configuracionJson),
      detalleInteraccionesJson: Value(detalleInteraccionesJson),
      erroresJson: Value(erroresJson),
      creadoEn: Value(creadoEn),
    );
  }

  factory PendingGameResult.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return PendingGameResult(
      id: serializer.fromJson<int>(json['id']),
      usuarioId: serializer.fromJson<String>(json['usuarioId']),
      tipoJuego: serializer.fromJson<String>(json['tipoJuego']),
      aciertos: serializer.fromJson<int>(json['aciertos']),
      fallos: serializer.fromJson<int>(json['fallos']),
      totalPreguntas: serializer.fromJson<int>(json['totalPreguntas']),
      duracionSegundos: serializer.fromJson<int>(json['duracionSegundos']),
      sede: serializer.fromJson<String>(json['sede']),
      configuracionJson: serializer.fromJson<String>(json['configuracionJson']),
      detalleInteraccionesJson: serializer.fromJson<String>(
        json['detalleInteraccionesJson'],
      ),
      erroresJson: serializer.fromJson<String>(json['erroresJson']),
      creadoEn: serializer.fromJson<DateTime>(json['creadoEn']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'usuarioId': serializer.toJson<String>(usuarioId),
      'tipoJuego': serializer.toJson<String>(tipoJuego),
      'aciertos': serializer.toJson<int>(aciertos),
      'fallos': serializer.toJson<int>(fallos),
      'totalPreguntas': serializer.toJson<int>(totalPreguntas),
      'duracionSegundos': serializer.toJson<int>(duracionSegundos),
      'sede': serializer.toJson<String>(sede),
      'configuracionJson': serializer.toJson<String>(configuracionJson),
      'detalleInteraccionesJson': serializer.toJson<String>(
        detalleInteraccionesJson,
      ),
      'erroresJson': serializer.toJson<String>(erroresJson),
      'creadoEn': serializer.toJson<DateTime>(creadoEn),
    };
  }

  PendingGameResult copyWith({
    int? id,
    String? usuarioId,
    String? tipoJuego,
    int? aciertos,
    int? fallos,
    int? totalPreguntas,
    int? duracionSegundos,
    String? sede,
    String? configuracionJson,
    String? detalleInteraccionesJson,
    String? erroresJson,
    DateTime? creadoEn,
  }) => PendingGameResult(
    id: id ?? this.id,
    usuarioId: usuarioId ?? this.usuarioId,
    tipoJuego: tipoJuego ?? this.tipoJuego,
    aciertos: aciertos ?? this.aciertos,
    fallos: fallos ?? this.fallos,
    totalPreguntas: totalPreguntas ?? this.totalPreguntas,
    duracionSegundos: duracionSegundos ?? this.duracionSegundos,
    sede: sede ?? this.sede,
    configuracionJson: configuracionJson ?? this.configuracionJson,
    detalleInteraccionesJson:
        detalleInteraccionesJson ?? this.detalleInteraccionesJson,
    erroresJson: erroresJson ?? this.erroresJson,
    creadoEn: creadoEn ?? this.creadoEn,
  );
  PendingGameResult copyWithCompanion(PendingGameResultsCompanion data) {
    return PendingGameResult(
      id: data.id.present ? data.id.value : this.id,
      usuarioId: data.usuarioId.present ? data.usuarioId.value : this.usuarioId,
      tipoJuego: data.tipoJuego.present ? data.tipoJuego.value : this.tipoJuego,
      aciertos: data.aciertos.present ? data.aciertos.value : this.aciertos,
      fallos: data.fallos.present ? data.fallos.value : this.fallos,
      totalPreguntas: data.totalPreguntas.present
          ? data.totalPreguntas.value
          : this.totalPreguntas,
      duracionSegundos: data.duracionSegundos.present
          ? data.duracionSegundos.value
          : this.duracionSegundos,
      sede: data.sede.present ? data.sede.value : this.sede,
      configuracionJson: data.configuracionJson.present
          ? data.configuracionJson.value
          : this.configuracionJson,
      detalleInteraccionesJson: data.detalleInteraccionesJson.present
          ? data.detalleInteraccionesJson.value
          : this.detalleInteraccionesJson,
      erroresJson: data.erroresJson.present
          ? data.erroresJson.value
          : this.erroresJson,
      creadoEn: data.creadoEn.present ? data.creadoEn.value : this.creadoEn,
    );
  }

  @override
  String toString() {
    return (StringBuffer('PendingGameResult(')
          ..write('id: $id, ')
          ..write('usuarioId: $usuarioId, ')
          ..write('tipoJuego: $tipoJuego, ')
          ..write('aciertos: $aciertos, ')
          ..write('fallos: $fallos, ')
          ..write('totalPreguntas: $totalPreguntas, ')
          ..write('duracionSegundos: $duracionSegundos, ')
          ..write('sede: $sede, ')
          ..write('configuracionJson: $configuracionJson, ')
          ..write('detalleInteraccionesJson: $detalleInteraccionesJson, ')
          ..write('erroresJson: $erroresJson, ')
          ..write('creadoEn: $creadoEn')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    usuarioId,
    tipoJuego,
    aciertos,
    fallos,
    totalPreguntas,
    duracionSegundos,
    sede,
    configuracionJson,
    detalleInteraccionesJson,
    erroresJson,
    creadoEn,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is PendingGameResult &&
          other.id == this.id &&
          other.usuarioId == this.usuarioId &&
          other.tipoJuego == this.tipoJuego &&
          other.aciertos == this.aciertos &&
          other.fallos == this.fallos &&
          other.totalPreguntas == this.totalPreguntas &&
          other.duracionSegundos == this.duracionSegundos &&
          other.sede == this.sede &&
          other.configuracionJson == this.configuracionJson &&
          other.detalleInteraccionesJson == this.detalleInteraccionesJson &&
          other.erroresJson == this.erroresJson &&
          other.creadoEn == this.creadoEn);
}

class PendingGameResultsCompanion extends UpdateCompanion<PendingGameResult> {
  final Value<int> id;
  final Value<String> usuarioId;
  final Value<String> tipoJuego;
  final Value<int> aciertos;
  final Value<int> fallos;
  final Value<int> totalPreguntas;
  final Value<int> duracionSegundos;
  final Value<String> sede;
  final Value<String> configuracionJson;
  final Value<String> detalleInteraccionesJson;
  final Value<String> erroresJson;
  final Value<DateTime> creadoEn;
  const PendingGameResultsCompanion({
    this.id = const Value.absent(),
    this.usuarioId = const Value.absent(),
    this.tipoJuego = const Value.absent(),
    this.aciertos = const Value.absent(),
    this.fallos = const Value.absent(),
    this.totalPreguntas = const Value.absent(),
    this.duracionSegundos = const Value.absent(),
    this.sede = const Value.absent(),
    this.configuracionJson = const Value.absent(),
    this.detalleInteraccionesJson = const Value.absent(),
    this.erroresJson = const Value.absent(),
    this.creadoEn = const Value.absent(),
  });
  PendingGameResultsCompanion.insert({
    this.id = const Value.absent(),
    required String usuarioId,
    required String tipoJuego,
    required int aciertos,
    required int fallos,
    required int totalPreguntas,
    required int duracionSegundos,
    required String sede,
    required String configuracionJson,
    required String detalleInteraccionesJson,
    required String erroresJson,
    required DateTime creadoEn,
  }) : usuarioId = Value(usuarioId),
       tipoJuego = Value(tipoJuego),
       aciertos = Value(aciertos),
       fallos = Value(fallos),
       totalPreguntas = Value(totalPreguntas),
       duracionSegundos = Value(duracionSegundos),
       sede = Value(sede),
       configuracionJson = Value(configuracionJson),
       detalleInteraccionesJson = Value(detalleInteraccionesJson),
       erroresJson = Value(erroresJson),
       creadoEn = Value(creadoEn);
  static Insertable<PendingGameResult> custom({
    Expression<int>? id,
    Expression<String>? usuarioId,
    Expression<String>? tipoJuego,
    Expression<int>? aciertos,
    Expression<int>? fallos,
    Expression<int>? totalPreguntas,
    Expression<int>? duracionSegundos,
    Expression<String>? sede,
    Expression<String>? configuracionJson,
    Expression<String>? detalleInteraccionesJson,
    Expression<String>? erroresJson,
    Expression<DateTime>? creadoEn,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (usuarioId != null) 'usuario_id': usuarioId,
      if (tipoJuego != null) 'tipo_juego': tipoJuego,
      if (aciertos != null) 'aciertos': aciertos,
      if (fallos != null) 'fallos': fallos,
      if (totalPreguntas != null) 'total_preguntas': totalPreguntas,
      if (duracionSegundos != null) 'duracion_segundos': duracionSegundos,
      if (sede != null) 'sede': sede,
      if (configuracionJson != null) 'configuracion_json': configuracionJson,
      if (detalleInteraccionesJson != null)
        'detalle_interacciones_json': detalleInteraccionesJson,
      if (erroresJson != null) 'errores_json': erroresJson,
      if (creadoEn != null) 'creado_en': creadoEn,
    });
  }

  PendingGameResultsCompanion copyWith({
    Value<int>? id,
    Value<String>? usuarioId,
    Value<String>? tipoJuego,
    Value<int>? aciertos,
    Value<int>? fallos,
    Value<int>? totalPreguntas,
    Value<int>? duracionSegundos,
    Value<String>? sede,
    Value<String>? configuracionJson,
    Value<String>? detalleInteraccionesJson,
    Value<String>? erroresJson,
    Value<DateTime>? creadoEn,
  }) {
    return PendingGameResultsCompanion(
      id: id ?? this.id,
      usuarioId: usuarioId ?? this.usuarioId,
      tipoJuego: tipoJuego ?? this.tipoJuego,
      aciertos: aciertos ?? this.aciertos,
      fallos: fallos ?? this.fallos,
      totalPreguntas: totalPreguntas ?? this.totalPreguntas,
      duracionSegundos: duracionSegundos ?? this.duracionSegundos,
      sede: sede ?? this.sede,
      configuracionJson: configuracionJson ?? this.configuracionJson,
      detalleInteraccionesJson:
          detalleInteraccionesJson ?? this.detalleInteraccionesJson,
      erroresJson: erroresJson ?? this.erroresJson,
      creadoEn: creadoEn ?? this.creadoEn,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (usuarioId.present) {
      map['usuario_id'] = Variable<String>(usuarioId.value);
    }
    if (tipoJuego.present) {
      map['tipo_juego'] = Variable<String>(tipoJuego.value);
    }
    if (aciertos.present) {
      map['aciertos'] = Variable<int>(aciertos.value);
    }
    if (fallos.present) {
      map['fallos'] = Variable<int>(fallos.value);
    }
    if (totalPreguntas.present) {
      map['total_preguntas'] = Variable<int>(totalPreguntas.value);
    }
    if (duracionSegundos.present) {
      map['duracion_segundos'] = Variable<int>(duracionSegundos.value);
    }
    if (sede.present) {
      map['sede'] = Variable<String>(sede.value);
    }
    if (configuracionJson.present) {
      map['configuracion_json'] = Variable<String>(configuracionJson.value);
    }
    if (detalleInteraccionesJson.present) {
      map['detalle_interacciones_json'] = Variable<String>(
        detalleInteraccionesJson.value,
      );
    }
    if (erroresJson.present) {
      map['errores_json'] = Variable<String>(erroresJson.value);
    }
    if (creadoEn.present) {
      map['creado_en'] = Variable<DateTime>(creadoEn.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PendingGameResultsCompanion(')
          ..write('id: $id, ')
          ..write('usuarioId: $usuarioId, ')
          ..write('tipoJuego: $tipoJuego, ')
          ..write('aciertos: $aciertos, ')
          ..write('fallos: $fallos, ')
          ..write('totalPreguntas: $totalPreguntas, ')
          ..write('duracionSegundos: $duracionSegundos, ')
          ..write('sede: $sede, ')
          ..write('configuracionJson: $configuracionJson, ')
          ..write('detalleInteraccionesJson: $detalleInteraccionesJson, ')
          ..write('erroresJson: $erroresJson, ')
          ..write('creadoEn: $creadoEn')
          ..write(')'))
        .toString();
  }
}

class $PendingSessionTimeTable extends PendingSessionTime
    with TableInfo<$PendingSessionTimeTable, PendingSessionTimeData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PendingSessionTimeTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _usuarioIdMeta = const VerificationMeta(
    'usuarioId',
  );
  @override
  late final GeneratedColumn<String> usuarioId = GeneratedColumn<String>(
    'usuario_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _fechaMeta = const VerificationMeta('fecha');
  @override
  late final GeneratedColumn<DateTime> fecha = GeneratedColumn<DateTime>(
    'fecha',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _duracionSegundosMeta = const VerificationMeta(
    'duracionSegundos',
  );
  @override
  late final GeneratedColumn<int> duracionSegundos = GeneratedColumn<int>(
    'duracion_segundos',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _creadoEnMeta = const VerificationMeta(
    'creadoEn',
  );
  @override
  late final GeneratedColumn<DateTime> creadoEn = GeneratedColumn<DateTime>(
    'creado_en',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    usuarioId,
    fecha,
    duracionSegundos,
    creadoEn,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'pending_session_time';
  @override
  VerificationContext validateIntegrity(
    Insertable<PendingSessionTimeData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('usuario_id')) {
      context.handle(
        _usuarioIdMeta,
        usuarioId.isAcceptableOrUnknown(data['usuario_id']!, _usuarioIdMeta),
      );
    } else if (isInserting) {
      context.missing(_usuarioIdMeta);
    }
    if (data.containsKey('fecha')) {
      context.handle(
        _fechaMeta,
        fecha.isAcceptableOrUnknown(data['fecha']!, _fechaMeta),
      );
    } else if (isInserting) {
      context.missing(_fechaMeta);
    }
    if (data.containsKey('duracion_segundos')) {
      context.handle(
        _duracionSegundosMeta,
        duracionSegundos.isAcceptableOrUnknown(
          data['duracion_segundos']!,
          _duracionSegundosMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_duracionSegundosMeta);
    }
    if (data.containsKey('creado_en')) {
      context.handle(
        _creadoEnMeta,
        creadoEn.isAcceptableOrUnknown(data['creado_en']!, _creadoEnMeta),
      );
    } else if (isInserting) {
      context.missing(_creadoEnMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  PendingSessionTimeData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return PendingSessionTimeData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      usuarioId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}usuario_id'],
      )!,
      fecha: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}fecha'],
      )!,
      duracionSegundos: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}duracion_segundos'],
      )!,
      creadoEn: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}creado_en'],
      )!,
    );
  }

  @override
  $PendingSessionTimeTable createAlias(String alias) {
    return $PendingSessionTimeTable(attachedDatabase, alias);
  }
}

class PendingSessionTimeData extends DataClass
    implements Insertable<PendingSessionTimeData> {
  final int id;
  final String usuarioId;
  final DateTime fecha;
  final int duracionSegundos;
  final DateTime creadoEn;
  const PendingSessionTimeData({
    required this.id,
    required this.usuarioId,
    required this.fecha,
    required this.duracionSegundos,
    required this.creadoEn,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['usuario_id'] = Variable<String>(usuarioId);
    map['fecha'] = Variable<DateTime>(fecha);
    map['duracion_segundos'] = Variable<int>(duracionSegundos);
    map['creado_en'] = Variable<DateTime>(creadoEn);
    return map;
  }

  PendingSessionTimeCompanion toCompanion(bool nullToAbsent) {
    return PendingSessionTimeCompanion(
      id: Value(id),
      usuarioId: Value(usuarioId),
      fecha: Value(fecha),
      duracionSegundos: Value(duracionSegundos),
      creadoEn: Value(creadoEn),
    );
  }

  factory PendingSessionTimeData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return PendingSessionTimeData(
      id: serializer.fromJson<int>(json['id']),
      usuarioId: serializer.fromJson<String>(json['usuarioId']),
      fecha: serializer.fromJson<DateTime>(json['fecha']),
      duracionSegundos: serializer.fromJson<int>(json['duracionSegundos']),
      creadoEn: serializer.fromJson<DateTime>(json['creadoEn']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'usuarioId': serializer.toJson<String>(usuarioId),
      'fecha': serializer.toJson<DateTime>(fecha),
      'duracionSegundos': serializer.toJson<int>(duracionSegundos),
      'creadoEn': serializer.toJson<DateTime>(creadoEn),
    };
  }

  PendingSessionTimeData copyWith({
    int? id,
    String? usuarioId,
    DateTime? fecha,
    int? duracionSegundos,
    DateTime? creadoEn,
  }) => PendingSessionTimeData(
    id: id ?? this.id,
    usuarioId: usuarioId ?? this.usuarioId,
    fecha: fecha ?? this.fecha,
    duracionSegundos: duracionSegundos ?? this.duracionSegundos,
    creadoEn: creadoEn ?? this.creadoEn,
  );
  PendingSessionTimeData copyWithCompanion(PendingSessionTimeCompanion data) {
    return PendingSessionTimeData(
      id: data.id.present ? data.id.value : this.id,
      usuarioId: data.usuarioId.present ? data.usuarioId.value : this.usuarioId,
      fecha: data.fecha.present ? data.fecha.value : this.fecha,
      duracionSegundos: data.duracionSegundos.present
          ? data.duracionSegundos.value
          : this.duracionSegundos,
      creadoEn: data.creadoEn.present ? data.creadoEn.value : this.creadoEn,
    );
  }

  @override
  String toString() {
    return (StringBuffer('PendingSessionTimeData(')
          ..write('id: $id, ')
          ..write('usuarioId: $usuarioId, ')
          ..write('fecha: $fecha, ')
          ..write('duracionSegundos: $duracionSegundos, ')
          ..write('creadoEn: $creadoEn')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, usuarioId, fecha, duracionSegundos, creadoEn);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is PendingSessionTimeData &&
          other.id == this.id &&
          other.usuarioId == this.usuarioId &&
          other.fecha == this.fecha &&
          other.duracionSegundos == this.duracionSegundos &&
          other.creadoEn == this.creadoEn);
}

class PendingSessionTimeCompanion
    extends UpdateCompanion<PendingSessionTimeData> {
  final Value<int> id;
  final Value<String> usuarioId;
  final Value<DateTime> fecha;
  final Value<int> duracionSegundos;
  final Value<DateTime> creadoEn;
  const PendingSessionTimeCompanion({
    this.id = const Value.absent(),
    this.usuarioId = const Value.absent(),
    this.fecha = const Value.absent(),
    this.duracionSegundos = const Value.absent(),
    this.creadoEn = const Value.absent(),
  });
  PendingSessionTimeCompanion.insert({
    this.id = const Value.absent(),
    required String usuarioId,
    required DateTime fecha,
    required int duracionSegundos,
    required DateTime creadoEn,
  }) : usuarioId = Value(usuarioId),
       fecha = Value(fecha),
       duracionSegundos = Value(duracionSegundos),
       creadoEn = Value(creadoEn);
  static Insertable<PendingSessionTimeData> custom({
    Expression<int>? id,
    Expression<String>? usuarioId,
    Expression<DateTime>? fecha,
    Expression<int>? duracionSegundos,
    Expression<DateTime>? creadoEn,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (usuarioId != null) 'usuario_id': usuarioId,
      if (fecha != null) 'fecha': fecha,
      if (duracionSegundos != null) 'duracion_segundos': duracionSegundos,
      if (creadoEn != null) 'creado_en': creadoEn,
    });
  }

  PendingSessionTimeCompanion copyWith({
    Value<int>? id,
    Value<String>? usuarioId,
    Value<DateTime>? fecha,
    Value<int>? duracionSegundos,
    Value<DateTime>? creadoEn,
  }) {
    return PendingSessionTimeCompanion(
      id: id ?? this.id,
      usuarioId: usuarioId ?? this.usuarioId,
      fecha: fecha ?? this.fecha,
      duracionSegundos: duracionSegundos ?? this.duracionSegundos,
      creadoEn: creadoEn ?? this.creadoEn,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (usuarioId.present) {
      map['usuario_id'] = Variable<String>(usuarioId.value);
    }
    if (fecha.present) {
      map['fecha'] = Variable<DateTime>(fecha.value);
    }
    if (duracionSegundos.present) {
      map['duracion_segundos'] = Variable<int>(duracionSegundos.value);
    }
    if (creadoEn.present) {
      map['creado_en'] = Variable<DateTime>(creadoEn.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PendingSessionTimeCompanion(')
          ..write('id: $id, ')
          ..write('usuarioId: $usuarioId, ')
          ..write('fecha: $fecha, ')
          ..write('duracionSegundos: $duracionSegundos, ')
          ..write('creadoEn: $creadoEn')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $CachedCategoriasTable cachedCategorias = $CachedCategoriasTable(
    this,
  );
  late final $CachedSubcategoriasTable cachedSubcategorias =
      $CachedSubcategoriasTable(this);
  late final $CachedProductosTable cachedProductos = $CachedProductosTable(
    this,
  );
  late final $CachedEstatusProductoTable cachedEstatusProducto =
      $CachedEstatusProductoTable(this);
  late final $CacheMetaTable cacheMeta = $CacheMetaTable(this);
  late final $PendingGameResultsTable pendingGameResults =
      $PendingGameResultsTable(this);
  late final $PendingSessionTimeTable pendingSessionTime =
      $PendingSessionTimeTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    cachedCategorias,
    cachedSubcategorias,
    cachedProductos,
    cachedEstatusProducto,
    cacheMeta,
    pendingGameResults,
    pendingSessionTime,
  ];
}

typedef $$CachedCategoriasTableCreateCompanionBuilder =
    CachedCategoriasCompanion Function({
      required String codigo,
      required String nombre,
      Value<String?> mnemotecnia,
      required String sede,
      Value<int> rowid,
    });
typedef $$CachedCategoriasTableUpdateCompanionBuilder =
    CachedCategoriasCompanion Function({
      Value<String> codigo,
      Value<String> nombre,
      Value<String?> mnemotecnia,
      Value<String> sede,
      Value<int> rowid,
    });

class $$CachedCategoriasTableFilterComposer
    extends Composer<_$AppDatabase, $CachedCategoriasTable> {
  $$CachedCategoriasTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get codigo => $composableBuilder(
    column: $table.codigo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get nombre => $composableBuilder(
    column: $table.nombre,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mnemotecnia => $composableBuilder(
    column: $table.mnemotecnia,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sede => $composableBuilder(
    column: $table.sede,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedCategoriasTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedCategoriasTable> {
  $$CachedCategoriasTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get codigo => $composableBuilder(
    column: $table.codigo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get nombre => $composableBuilder(
    column: $table.nombre,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mnemotecnia => $composableBuilder(
    column: $table.mnemotecnia,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sede => $composableBuilder(
    column: $table.sede,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedCategoriasTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedCategoriasTable> {
  $$CachedCategoriasTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get codigo =>
      $composableBuilder(column: $table.codigo, builder: (column) => column);

  GeneratedColumn<String> get nombre =>
      $composableBuilder(column: $table.nombre, builder: (column) => column);

  GeneratedColumn<String> get mnemotecnia => $composableBuilder(
    column: $table.mnemotecnia,
    builder: (column) => column,
  );

  GeneratedColumn<String> get sede =>
      $composableBuilder(column: $table.sede, builder: (column) => column);
}

class $$CachedCategoriasTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedCategoriasTable,
          CachedCategoria,
          $$CachedCategoriasTableFilterComposer,
          $$CachedCategoriasTableOrderingComposer,
          $$CachedCategoriasTableAnnotationComposer,
          $$CachedCategoriasTableCreateCompanionBuilder,
          $$CachedCategoriasTableUpdateCompanionBuilder,
          (
            CachedCategoria,
            BaseReferences<
              _$AppDatabase,
              $CachedCategoriasTable,
              CachedCategoria
            >,
          ),
          CachedCategoria,
          PrefetchHooks Function()
        > {
  $$CachedCategoriasTableTableManager(
    _$AppDatabase db,
    $CachedCategoriasTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedCategoriasTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedCategoriasTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedCategoriasTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> codigo = const Value.absent(),
                Value<String> nombre = const Value.absent(),
                Value<String?> mnemotecnia = const Value.absent(),
                Value<String> sede = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedCategoriasCompanion(
                codigo: codigo,
                nombre: nombre,
                mnemotecnia: mnemotecnia,
                sede: sede,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String codigo,
                required String nombre,
                Value<String?> mnemotecnia = const Value.absent(),
                required String sede,
                Value<int> rowid = const Value.absent(),
              }) => CachedCategoriasCompanion.insert(
                codigo: codigo,
                nombre: nombre,
                mnemotecnia: mnemotecnia,
                sede: sede,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedCategoriasTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedCategoriasTable,
      CachedCategoria,
      $$CachedCategoriasTableFilterComposer,
      $$CachedCategoriasTableOrderingComposer,
      $$CachedCategoriasTableAnnotationComposer,
      $$CachedCategoriasTableCreateCompanionBuilder,
      $$CachedCategoriasTableUpdateCompanionBuilder,
      (
        CachedCategoria,
        BaseReferences<_$AppDatabase, $CachedCategoriasTable, CachedCategoria>,
      ),
      CachedCategoria,
      PrefetchHooks Function()
    >;
typedef $$CachedSubcategoriasTableCreateCompanionBuilder =
    CachedSubcategoriasCompanion Function({
      required String codigo,
      required String categoriaCodigo,
      required String nombre,
      Value<String?> mnemotecnia,
      required String sede,
      Value<int> rowid,
    });
typedef $$CachedSubcategoriasTableUpdateCompanionBuilder =
    CachedSubcategoriasCompanion Function({
      Value<String> codigo,
      Value<String> categoriaCodigo,
      Value<String> nombre,
      Value<String?> mnemotecnia,
      Value<String> sede,
      Value<int> rowid,
    });

class $$CachedSubcategoriasTableFilterComposer
    extends Composer<_$AppDatabase, $CachedSubcategoriasTable> {
  $$CachedSubcategoriasTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get codigo => $composableBuilder(
    column: $table.codigo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get categoriaCodigo => $composableBuilder(
    column: $table.categoriaCodigo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get nombre => $composableBuilder(
    column: $table.nombre,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mnemotecnia => $composableBuilder(
    column: $table.mnemotecnia,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sede => $composableBuilder(
    column: $table.sede,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedSubcategoriasTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedSubcategoriasTable> {
  $$CachedSubcategoriasTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get codigo => $composableBuilder(
    column: $table.codigo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get categoriaCodigo => $composableBuilder(
    column: $table.categoriaCodigo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get nombre => $composableBuilder(
    column: $table.nombre,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mnemotecnia => $composableBuilder(
    column: $table.mnemotecnia,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sede => $composableBuilder(
    column: $table.sede,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedSubcategoriasTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedSubcategoriasTable> {
  $$CachedSubcategoriasTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get codigo =>
      $composableBuilder(column: $table.codigo, builder: (column) => column);

  GeneratedColumn<String> get categoriaCodigo => $composableBuilder(
    column: $table.categoriaCodigo,
    builder: (column) => column,
  );

  GeneratedColumn<String> get nombre =>
      $composableBuilder(column: $table.nombre, builder: (column) => column);

  GeneratedColumn<String> get mnemotecnia => $composableBuilder(
    column: $table.mnemotecnia,
    builder: (column) => column,
  );

  GeneratedColumn<String> get sede =>
      $composableBuilder(column: $table.sede, builder: (column) => column);
}

class $$CachedSubcategoriasTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedSubcategoriasTable,
          CachedSubcategoria,
          $$CachedSubcategoriasTableFilterComposer,
          $$CachedSubcategoriasTableOrderingComposer,
          $$CachedSubcategoriasTableAnnotationComposer,
          $$CachedSubcategoriasTableCreateCompanionBuilder,
          $$CachedSubcategoriasTableUpdateCompanionBuilder,
          (
            CachedSubcategoria,
            BaseReferences<
              _$AppDatabase,
              $CachedSubcategoriasTable,
              CachedSubcategoria
            >,
          ),
          CachedSubcategoria,
          PrefetchHooks Function()
        > {
  $$CachedSubcategoriasTableTableManager(
    _$AppDatabase db,
    $CachedSubcategoriasTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedSubcategoriasTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedSubcategoriasTableOrderingComposer(
                $db: db,
                $table: table,
              ),
          createComputedFieldComposer: () =>
              $$CachedSubcategoriasTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<String> codigo = const Value.absent(),
                Value<String> categoriaCodigo = const Value.absent(),
                Value<String> nombre = const Value.absent(),
                Value<String?> mnemotecnia = const Value.absent(),
                Value<String> sede = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedSubcategoriasCompanion(
                codigo: codigo,
                categoriaCodigo: categoriaCodigo,
                nombre: nombre,
                mnemotecnia: mnemotecnia,
                sede: sede,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String codigo,
                required String categoriaCodigo,
                required String nombre,
                Value<String?> mnemotecnia = const Value.absent(),
                required String sede,
                Value<int> rowid = const Value.absent(),
              }) => CachedSubcategoriasCompanion.insert(
                codigo: codigo,
                categoriaCodigo: categoriaCodigo,
                nombre: nombre,
                mnemotecnia: mnemotecnia,
                sede: sede,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedSubcategoriasTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedSubcategoriasTable,
      CachedSubcategoria,
      $$CachedSubcategoriasTableFilterComposer,
      $$CachedSubcategoriasTableOrderingComposer,
      $$CachedSubcategoriasTableAnnotationComposer,
      $$CachedSubcategoriasTableCreateCompanionBuilder,
      $$CachedSubcategoriasTableUpdateCompanionBuilder,
      (
        CachedSubcategoria,
        BaseReferences<
          _$AppDatabase,
          $CachedSubcategoriasTable,
          CachedSubcategoria
        >,
      ),
      CachedSubcategoria,
      PrefetchHooks Function()
    >;
typedef $$CachedProductosTableCreateCompanionBuilder =
    CachedProductosCompanion Function({
      required String id,
      required String codigo,
      Value<String?> codigoCompleto,
      required String categoriaCodigo,
      required String subcategoriaCodigo,
      required String nombre,
      Value<String?> mnemotecnia,
      Value<String?> imagenUrl,
      required String estatus,
      required String marca,
      required String sede,
      Value<int> rowid,
    });
typedef $$CachedProductosTableUpdateCompanionBuilder =
    CachedProductosCompanion Function({
      Value<String> id,
      Value<String> codigo,
      Value<String?> codigoCompleto,
      Value<String> categoriaCodigo,
      Value<String> subcategoriaCodigo,
      Value<String> nombre,
      Value<String?> mnemotecnia,
      Value<String?> imagenUrl,
      Value<String> estatus,
      Value<String> marca,
      Value<String> sede,
      Value<int> rowid,
    });

class $$CachedProductosTableFilterComposer
    extends Composer<_$AppDatabase, $CachedProductosTable> {
  $$CachedProductosTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get codigo => $composableBuilder(
    column: $table.codigo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get codigoCompleto => $composableBuilder(
    column: $table.codigoCompleto,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get categoriaCodigo => $composableBuilder(
    column: $table.categoriaCodigo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get subcategoriaCodigo => $composableBuilder(
    column: $table.subcategoriaCodigo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get nombre => $composableBuilder(
    column: $table.nombre,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mnemotecnia => $composableBuilder(
    column: $table.mnemotecnia,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get imagenUrl => $composableBuilder(
    column: $table.imagenUrl,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get estatus => $composableBuilder(
    column: $table.estatus,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get marca => $composableBuilder(
    column: $table.marca,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sede => $composableBuilder(
    column: $table.sede,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedProductosTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedProductosTable> {
  $$CachedProductosTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get codigo => $composableBuilder(
    column: $table.codigo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get codigoCompleto => $composableBuilder(
    column: $table.codigoCompleto,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get categoriaCodigo => $composableBuilder(
    column: $table.categoriaCodigo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get subcategoriaCodigo => $composableBuilder(
    column: $table.subcategoriaCodigo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get nombre => $composableBuilder(
    column: $table.nombre,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mnemotecnia => $composableBuilder(
    column: $table.mnemotecnia,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get imagenUrl => $composableBuilder(
    column: $table.imagenUrl,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get estatus => $composableBuilder(
    column: $table.estatus,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get marca => $composableBuilder(
    column: $table.marca,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sede => $composableBuilder(
    column: $table.sede,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedProductosTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedProductosTable> {
  $$CachedProductosTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get codigo =>
      $composableBuilder(column: $table.codigo, builder: (column) => column);

  GeneratedColumn<String> get codigoCompleto => $composableBuilder(
    column: $table.codigoCompleto,
    builder: (column) => column,
  );

  GeneratedColumn<String> get categoriaCodigo => $composableBuilder(
    column: $table.categoriaCodigo,
    builder: (column) => column,
  );

  GeneratedColumn<String> get subcategoriaCodigo => $composableBuilder(
    column: $table.subcategoriaCodigo,
    builder: (column) => column,
  );

  GeneratedColumn<String> get nombre =>
      $composableBuilder(column: $table.nombre, builder: (column) => column);

  GeneratedColumn<String> get mnemotecnia => $composableBuilder(
    column: $table.mnemotecnia,
    builder: (column) => column,
  );

  GeneratedColumn<String> get imagenUrl =>
      $composableBuilder(column: $table.imagenUrl, builder: (column) => column);

  GeneratedColumn<String> get estatus =>
      $composableBuilder(column: $table.estatus, builder: (column) => column);

  GeneratedColumn<String> get marca =>
      $composableBuilder(column: $table.marca, builder: (column) => column);

  GeneratedColumn<String> get sede =>
      $composableBuilder(column: $table.sede, builder: (column) => column);
}

class $$CachedProductosTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedProductosTable,
          CachedProducto,
          $$CachedProductosTableFilterComposer,
          $$CachedProductosTableOrderingComposer,
          $$CachedProductosTableAnnotationComposer,
          $$CachedProductosTableCreateCompanionBuilder,
          $$CachedProductosTableUpdateCompanionBuilder,
          (
            CachedProducto,
            BaseReferences<
              _$AppDatabase,
              $CachedProductosTable,
              CachedProducto
            >,
          ),
          CachedProducto,
          PrefetchHooks Function()
        > {
  $$CachedProductosTableTableManager(
    _$AppDatabase db,
    $CachedProductosTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedProductosTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CachedProductosTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CachedProductosTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> codigo = const Value.absent(),
                Value<String?> codigoCompleto = const Value.absent(),
                Value<String> categoriaCodigo = const Value.absent(),
                Value<String> subcategoriaCodigo = const Value.absent(),
                Value<String> nombre = const Value.absent(),
                Value<String?> mnemotecnia = const Value.absent(),
                Value<String?> imagenUrl = const Value.absent(),
                Value<String> estatus = const Value.absent(),
                Value<String> marca = const Value.absent(),
                Value<String> sede = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedProductosCompanion(
                id: id,
                codigo: codigo,
                codigoCompleto: codigoCompleto,
                categoriaCodigo: categoriaCodigo,
                subcategoriaCodigo: subcategoriaCodigo,
                nombre: nombre,
                mnemotecnia: mnemotecnia,
                imagenUrl: imagenUrl,
                estatus: estatus,
                marca: marca,
                sede: sede,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String codigo,
                Value<String?> codigoCompleto = const Value.absent(),
                required String categoriaCodigo,
                required String subcategoriaCodigo,
                required String nombre,
                Value<String?> mnemotecnia = const Value.absent(),
                Value<String?> imagenUrl = const Value.absent(),
                required String estatus,
                required String marca,
                required String sede,
                Value<int> rowid = const Value.absent(),
              }) => CachedProductosCompanion.insert(
                id: id,
                codigo: codigo,
                codigoCompleto: codigoCompleto,
                categoriaCodigo: categoriaCodigo,
                subcategoriaCodigo: subcategoriaCodigo,
                nombre: nombre,
                mnemotecnia: mnemotecnia,
                imagenUrl: imagenUrl,
                estatus: estatus,
                marca: marca,
                sede: sede,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedProductosTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedProductosTable,
      CachedProducto,
      $$CachedProductosTableFilterComposer,
      $$CachedProductosTableOrderingComposer,
      $$CachedProductosTableAnnotationComposer,
      $$CachedProductosTableCreateCompanionBuilder,
      $$CachedProductosTableUpdateCompanionBuilder,
      (
        CachedProducto,
        BaseReferences<_$AppDatabase, $CachedProductosTable, CachedProducto>,
      ),
      CachedProducto,
      PrefetchHooks Function()
    >;
typedef $$CachedEstatusProductoTableCreateCompanionBuilder =
    CachedEstatusProductoCompanion Function({
      required String codigo,
      required String nombre,
      required bool esInfaltable,
      Value<int> rowid,
    });
typedef $$CachedEstatusProductoTableUpdateCompanionBuilder =
    CachedEstatusProductoCompanion Function({
      Value<String> codigo,
      Value<String> nombre,
      Value<bool> esInfaltable,
      Value<int> rowid,
    });

class $$CachedEstatusProductoTableFilterComposer
    extends Composer<_$AppDatabase, $CachedEstatusProductoTable> {
  $$CachedEstatusProductoTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get codigo => $composableBuilder(
    column: $table.codigo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get nombre => $composableBuilder(
    column: $table.nombre,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get esInfaltable => $composableBuilder(
    column: $table.esInfaltable,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CachedEstatusProductoTableOrderingComposer
    extends Composer<_$AppDatabase, $CachedEstatusProductoTable> {
  $$CachedEstatusProductoTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get codigo => $composableBuilder(
    column: $table.codigo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get nombre => $composableBuilder(
    column: $table.nombre,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get esInfaltable => $composableBuilder(
    column: $table.esInfaltable,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CachedEstatusProductoTableAnnotationComposer
    extends Composer<_$AppDatabase, $CachedEstatusProductoTable> {
  $$CachedEstatusProductoTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get codigo =>
      $composableBuilder(column: $table.codigo, builder: (column) => column);

  GeneratedColumn<String> get nombre =>
      $composableBuilder(column: $table.nombre, builder: (column) => column);

  GeneratedColumn<bool> get esInfaltable => $composableBuilder(
    column: $table.esInfaltable,
    builder: (column) => column,
  );
}

class $$CachedEstatusProductoTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CachedEstatusProductoTable,
          CachedEstatusProductoData,
          $$CachedEstatusProductoTableFilterComposer,
          $$CachedEstatusProductoTableOrderingComposer,
          $$CachedEstatusProductoTableAnnotationComposer,
          $$CachedEstatusProductoTableCreateCompanionBuilder,
          $$CachedEstatusProductoTableUpdateCompanionBuilder,
          (
            CachedEstatusProductoData,
            BaseReferences<
              _$AppDatabase,
              $CachedEstatusProductoTable,
              CachedEstatusProductoData
            >,
          ),
          CachedEstatusProductoData,
          PrefetchHooks Function()
        > {
  $$CachedEstatusProductoTableTableManager(
    _$AppDatabase db,
    $CachedEstatusProductoTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CachedEstatusProductoTableFilterComposer(
                $db: db,
                $table: table,
              ),
          createOrderingComposer: () =>
              $$CachedEstatusProductoTableOrderingComposer(
                $db: db,
                $table: table,
              ),
          createComputedFieldComposer: () =>
              $$CachedEstatusProductoTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<String> codigo = const Value.absent(),
                Value<String> nombre = const Value.absent(),
                Value<bool> esInfaltable = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CachedEstatusProductoCompanion(
                codigo: codigo,
                nombre: nombre,
                esInfaltable: esInfaltable,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String codigo,
                required String nombre,
                required bool esInfaltable,
                Value<int> rowid = const Value.absent(),
              }) => CachedEstatusProductoCompanion.insert(
                codigo: codigo,
                nombre: nombre,
                esInfaltable: esInfaltable,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CachedEstatusProductoTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CachedEstatusProductoTable,
      CachedEstatusProductoData,
      $$CachedEstatusProductoTableFilterComposer,
      $$CachedEstatusProductoTableOrderingComposer,
      $$CachedEstatusProductoTableAnnotationComposer,
      $$CachedEstatusProductoTableCreateCompanionBuilder,
      $$CachedEstatusProductoTableUpdateCompanionBuilder,
      (
        CachedEstatusProductoData,
        BaseReferences<
          _$AppDatabase,
          $CachedEstatusProductoTable,
          CachedEstatusProductoData
        >,
      ),
      CachedEstatusProductoData,
      PrefetchHooks Function()
    >;
typedef $$CacheMetaTableCreateCompanionBuilder =
    CacheMetaCompanion Function({
      Value<int> id,
      Value<String?> sede,
      Value<int?> configVersion,
      Value<String?> versionDatos,
      Value<DateTime?> syncedAt,
      Value<bool> soloInfaltablesDefault,
    });
typedef $$CacheMetaTableUpdateCompanionBuilder =
    CacheMetaCompanion Function({
      Value<int> id,
      Value<String?> sede,
      Value<int?> configVersion,
      Value<String?> versionDatos,
      Value<DateTime?> syncedAt,
      Value<bool> soloInfaltablesDefault,
    });

class $$CacheMetaTableFilterComposer
    extends Composer<_$AppDatabase, $CacheMetaTable> {
  $$CacheMetaTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sede => $composableBuilder(
    column: $table.sede,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get configVersion => $composableBuilder(
    column: $table.configVersion,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get versionDatos => $composableBuilder(
    column: $table.versionDatos,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get syncedAt => $composableBuilder(
    column: $table.syncedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get soloInfaltablesDefault => $composableBuilder(
    column: $table.soloInfaltablesDefault,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CacheMetaTableOrderingComposer
    extends Composer<_$AppDatabase, $CacheMetaTable> {
  $$CacheMetaTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sede => $composableBuilder(
    column: $table.sede,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get configVersion => $composableBuilder(
    column: $table.configVersion,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get versionDatos => $composableBuilder(
    column: $table.versionDatos,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get syncedAt => $composableBuilder(
    column: $table.syncedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get soloInfaltablesDefault => $composableBuilder(
    column: $table.soloInfaltablesDefault,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CacheMetaTableAnnotationComposer
    extends Composer<_$AppDatabase, $CacheMetaTable> {
  $$CacheMetaTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get sede =>
      $composableBuilder(column: $table.sede, builder: (column) => column);

  GeneratedColumn<int> get configVersion => $composableBuilder(
    column: $table.configVersion,
    builder: (column) => column,
  );

  GeneratedColumn<String> get versionDatos => $composableBuilder(
    column: $table.versionDatos,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get syncedAt =>
      $composableBuilder(column: $table.syncedAt, builder: (column) => column);

  GeneratedColumn<bool> get soloInfaltablesDefault => $composableBuilder(
    column: $table.soloInfaltablesDefault,
    builder: (column) => column,
  );
}

class $$CacheMetaTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CacheMetaTable,
          CacheMetaData,
          $$CacheMetaTableFilterComposer,
          $$CacheMetaTableOrderingComposer,
          $$CacheMetaTableAnnotationComposer,
          $$CacheMetaTableCreateCompanionBuilder,
          $$CacheMetaTableUpdateCompanionBuilder,
          (
            CacheMetaData,
            BaseReferences<_$AppDatabase, $CacheMetaTable, CacheMetaData>,
          ),
          CacheMetaData,
          PrefetchHooks Function()
        > {
  $$CacheMetaTableTableManager(_$AppDatabase db, $CacheMetaTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CacheMetaTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CacheMetaTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CacheMetaTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String?> sede = const Value.absent(),
                Value<int?> configVersion = const Value.absent(),
                Value<String?> versionDatos = const Value.absent(),
                Value<DateTime?> syncedAt = const Value.absent(),
                Value<bool> soloInfaltablesDefault = const Value.absent(),
              }) => CacheMetaCompanion(
                id: id,
                sede: sede,
                configVersion: configVersion,
                versionDatos: versionDatos,
                syncedAt: syncedAt,
                soloInfaltablesDefault: soloInfaltablesDefault,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String?> sede = const Value.absent(),
                Value<int?> configVersion = const Value.absent(),
                Value<String?> versionDatos = const Value.absent(),
                Value<DateTime?> syncedAt = const Value.absent(),
                Value<bool> soloInfaltablesDefault = const Value.absent(),
              }) => CacheMetaCompanion.insert(
                id: id,
                sede: sede,
                configVersion: configVersion,
                versionDatos: versionDatos,
                syncedAt: syncedAt,
                soloInfaltablesDefault: soloInfaltablesDefault,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CacheMetaTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CacheMetaTable,
      CacheMetaData,
      $$CacheMetaTableFilterComposer,
      $$CacheMetaTableOrderingComposer,
      $$CacheMetaTableAnnotationComposer,
      $$CacheMetaTableCreateCompanionBuilder,
      $$CacheMetaTableUpdateCompanionBuilder,
      (
        CacheMetaData,
        BaseReferences<_$AppDatabase, $CacheMetaTable, CacheMetaData>,
      ),
      CacheMetaData,
      PrefetchHooks Function()
    >;
typedef $$PendingGameResultsTableCreateCompanionBuilder =
    PendingGameResultsCompanion Function({
      Value<int> id,
      required String usuarioId,
      required String tipoJuego,
      required int aciertos,
      required int fallos,
      required int totalPreguntas,
      required int duracionSegundos,
      required String sede,
      required String configuracionJson,
      required String detalleInteraccionesJson,
      required String erroresJson,
      required DateTime creadoEn,
    });
typedef $$PendingGameResultsTableUpdateCompanionBuilder =
    PendingGameResultsCompanion Function({
      Value<int> id,
      Value<String> usuarioId,
      Value<String> tipoJuego,
      Value<int> aciertos,
      Value<int> fallos,
      Value<int> totalPreguntas,
      Value<int> duracionSegundos,
      Value<String> sede,
      Value<String> configuracionJson,
      Value<String> detalleInteraccionesJson,
      Value<String> erroresJson,
      Value<DateTime> creadoEn,
    });

class $$PendingGameResultsTableFilterComposer
    extends Composer<_$AppDatabase, $PendingGameResultsTable> {
  $$PendingGameResultsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get usuarioId => $composableBuilder(
    column: $table.usuarioId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get tipoJuego => $composableBuilder(
    column: $table.tipoJuego,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get aciertos => $composableBuilder(
    column: $table.aciertos,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get fallos => $composableBuilder(
    column: $table.fallos,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get totalPreguntas => $composableBuilder(
    column: $table.totalPreguntas,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get duracionSegundos => $composableBuilder(
    column: $table.duracionSegundos,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sede => $composableBuilder(
    column: $table.sede,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get configuracionJson => $composableBuilder(
    column: $table.configuracionJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get detalleInteraccionesJson => $composableBuilder(
    column: $table.detalleInteraccionesJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get erroresJson => $composableBuilder(
    column: $table.erroresJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get creadoEn => $composableBuilder(
    column: $table.creadoEn,
    builder: (column) => ColumnFilters(column),
  );
}

class $$PendingGameResultsTableOrderingComposer
    extends Composer<_$AppDatabase, $PendingGameResultsTable> {
  $$PendingGameResultsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get usuarioId => $composableBuilder(
    column: $table.usuarioId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get tipoJuego => $composableBuilder(
    column: $table.tipoJuego,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get aciertos => $composableBuilder(
    column: $table.aciertos,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get fallos => $composableBuilder(
    column: $table.fallos,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get totalPreguntas => $composableBuilder(
    column: $table.totalPreguntas,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get duracionSegundos => $composableBuilder(
    column: $table.duracionSegundos,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sede => $composableBuilder(
    column: $table.sede,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get configuracionJson => $composableBuilder(
    column: $table.configuracionJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get detalleInteraccionesJson => $composableBuilder(
    column: $table.detalleInteraccionesJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get erroresJson => $composableBuilder(
    column: $table.erroresJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get creadoEn => $composableBuilder(
    column: $table.creadoEn,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$PendingGameResultsTableAnnotationComposer
    extends Composer<_$AppDatabase, $PendingGameResultsTable> {
  $$PendingGameResultsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get usuarioId =>
      $composableBuilder(column: $table.usuarioId, builder: (column) => column);

  GeneratedColumn<String> get tipoJuego =>
      $composableBuilder(column: $table.tipoJuego, builder: (column) => column);

  GeneratedColumn<int> get aciertos =>
      $composableBuilder(column: $table.aciertos, builder: (column) => column);

  GeneratedColumn<int> get fallos =>
      $composableBuilder(column: $table.fallos, builder: (column) => column);

  GeneratedColumn<int> get totalPreguntas => $composableBuilder(
    column: $table.totalPreguntas,
    builder: (column) => column,
  );

  GeneratedColumn<int> get duracionSegundos => $composableBuilder(
    column: $table.duracionSegundos,
    builder: (column) => column,
  );

  GeneratedColumn<String> get sede =>
      $composableBuilder(column: $table.sede, builder: (column) => column);

  GeneratedColumn<String> get configuracionJson => $composableBuilder(
    column: $table.configuracionJson,
    builder: (column) => column,
  );

  GeneratedColumn<String> get detalleInteraccionesJson => $composableBuilder(
    column: $table.detalleInteraccionesJson,
    builder: (column) => column,
  );

  GeneratedColumn<String> get erroresJson => $composableBuilder(
    column: $table.erroresJson,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get creadoEn =>
      $composableBuilder(column: $table.creadoEn, builder: (column) => column);
}

class $$PendingGameResultsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $PendingGameResultsTable,
          PendingGameResult,
          $$PendingGameResultsTableFilterComposer,
          $$PendingGameResultsTableOrderingComposer,
          $$PendingGameResultsTableAnnotationComposer,
          $$PendingGameResultsTableCreateCompanionBuilder,
          $$PendingGameResultsTableUpdateCompanionBuilder,
          (
            PendingGameResult,
            BaseReferences<
              _$AppDatabase,
              $PendingGameResultsTable,
              PendingGameResult
            >,
          ),
          PendingGameResult,
          PrefetchHooks Function()
        > {
  $$PendingGameResultsTableTableManager(
    _$AppDatabase db,
    $PendingGameResultsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$PendingGameResultsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$PendingGameResultsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$PendingGameResultsTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> usuarioId = const Value.absent(),
                Value<String> tipoJuego = const Value.absent(),
                Value<int> aciertos = const Value.absent(),
                Value<int> fallos = const Value.absent(),
                Value<int> totalPreguntas = const Value.absent(),
                Value<int> duracionSegundos = const Value.absent(),
                Value<String> sede = const Value.absent(),
                Value<String> configuracionJson = const Value.absent(),
                Value<String> detalleInteraccionesJson = const Value.absent(),
                Value<String> erroresJson = const Value.absent(),
                Value<DateTime> creadoEn = const Value.absent(),
              }) => PendingGameResultsCompanion(
                id: id,
                usuarioId: usuarioId,
                tipoJuego: tipoJuego,
                aciertos: aciertos,
                fallos: fallos,
                totalPreguntas: totalPreguntas,
                duracionSegundos: duracionSegundos,
                sede: sede,
                configuracionJson: configuracionJson,
                detalleInteraccionesJson: detalleInteraccionesJson,
                erroresJson: erroresJson,
                creadoEn: creadoEn,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String usuarioId,
                required String tipoJuego,
                required int aciertos,
                required int fallos,
                required int totalPreguntas,
                required int duracionSegundos,
                required String sede,
                required String configuracionJson,
                required String detalleInteraccionesJson,
                required String erroresJson,
                required DateTime creadoEn,
              }) => PendingGameResultsCompanion.insert(
                id: id,
                usuarioId: usuarioId,
                tipoJuego: tipoJuego,
                aciertos: aciertos,
                fallos: fallos,
                totalPreguntas: totalPreguntas,
                duracionSegundos: duracionSegundos,
                sede: sede,
                configuracionJson: configuracionJson,
                detalleInteraccionesJson: detalleInteraccionesJson,
                erroresJson: erroresJson,
                creadoEn: creadoEn,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$PendingGameResultsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $PendingGameResultsTable,
      PendingGameResult,
      $$PendingGameResultsTableFilterComposer,
      $$PendingGameResultsTableOrderingComposer,
      $$PendingGameResultsTableAnnotationComposer,
      $$PendingGameResultsTableCreateCompanionBuilder,
      $$PendingGameResultsTableUpdateCompanionBuilder,
      (
        PendingGameResult,
        BaseReferences<
          _$AppDatabase,
          $PendingGameResultsTable,
          PendingGameResult
        >,
      ),
      PendingGameResult,
      PrefetchHooks Function()
    >;
typedef $$PendingSessionTimeTableCreateCompanionBuilder =
    PendingSessionTimeCompanion Function({
      Value<int> id,
      required String usuarioId,
      required DateTime fecha,
      required int duracionSegundos,
      required DateTime creadoEn,
    });
typedef $$PendingSessionTimeTableUpdateCompanionBuilder =
    PendingSessionTimeCompanion Function({
      Value<int> id,
      Value<String> usuarioId,
      Value<DateTime> fecha,
      Value<int> duracionSegundos,
      Value<DateTime> creadoEn,
    });

class $$PendingSessionTimeTableFilterComposer
    extends Composer<_$AppDatabase, $PendingSessionTimeTable> {
  $$PendingSessionTimeTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get usuarioId => $composableBuilder(
    column: $table.usuarioId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get fecha => $composableBuilder(
    column: $table.fecha,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get duracionSegundos => $composableBuilder(
    column: $table.duracionSegundos,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get creadoEn => $composableBuilder(
    column: $table.creadoEn,
    builder: (column) => ColumnFilters(column),
  );
}

class $$PendingSessionTimeTableOrderingComposer
    extends Composer<_$AppDatabase, $PendingSessionTimeTable> {
  $$PendingSessionTimeTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get usuarioId => $composableBuilder(
    column: $table.usuarioId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get fecha => $composableBuilder(
    column: $table.fecha,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get duracionSegundos => $composableBuilder(
    column: $table.duracionSegundos,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get creadoEn => $composableBuilder(
    column: $table.creadoEn,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$PendingSessionTimeTableAnnotationComposer
    extends Composer<_$AppDatabase, $PendingSessionTimeTable> {
  $$PendingSessionTimeTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get usuarioId =>
      $composableBuilder(column: $table.usuarioId, builder: (column) => column);

  GeneratedColumn<DateTime> get fecha =>
      $composableBuilder(column: $table.fecha, builder: (column) => column);

  GeneratedColumn<int> get duracionSegundos => $composableBuilder(
    column: $table.duracionSegundos,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get creadoEn =>
      $composableBuilder(column: $table.creadoEn, builder: (column) => column);
}

class $$PendingSessionTimeTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $PendingSessionTimeTable,
          PendingSessionTimeData,
          $$PendingSessionTimeTableFilterComposer,
          $$PendingSessionTimeTableOrderingComposer,
          $$PendingSessionTimeTableAnnotationComposer,
          $$PendingSessionTimeTableCreateCompanionBuilder,
          $$PendingSessionTimeTableUpdateCompanionBuilder,
          (
            PendingSessionTimeData,
            BaseReferences<
              _$AppDatabase,
              $PendingSessionTimeTable,
              PendingSessionTimeData
            >,
          ),
          PendingSessionTimeData,
          PrefetchHooks Function()
        > {
  $$PendingSessionTimeTableTableManager(
    _$AppDatabase db,
    $PendingSessionTimeTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$PendingSessionTimeTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$PendingSessionTimeTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$PendingSessionTimeTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> usuarioId = const Value.absent(),
                Value<DateTime> fecha = const Value.absent(),
                Value<int> duracionSegundos = const Value.absent(),
                Value<DateTime> creadoEn = const Value.absent(),
              }) => PendingSessionTimeCompanion(
                id: id,
                usuarioId: usuarioId,
                fecha: fecha,
                duracionSegundos: duracionSegundos,
                creadoEn: creadoEn,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String usuarioId,
                required DateTime fecha,
                required int duracionSegundos,
                required DateTime creadoEn,
              }) => PendingSessionTimeCompanion.insert(
                id: id,
                usuarioId: usuarioId,
                fecha: fecha,
                duracionSegundos: duracionSegundos,
                creadoEn: creadoEn,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$PendingSessionTimeTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $PendingSessionTimeTable,
      PendingSessionTimeData,
      $$PendingSessionTimeTableFilterComposer,
      $$PendingSessionTimeTableOrderingComposer,
      $$PendingSessionTimeTableAnnotationComposer,
      $$PendingSessionTimeTableCreateCompanionBuilder,
      $$PendingSessionTimeTableUpdateCompanionBuilder,
      (
        PendingSessionTimeData,
        BaseReferences<
          _$AppDatabase,
          $PendingSessionTimeTable,
          PendingSessionTimeData
        >,
      ),
      PendingSessionTimeData,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$CachedCategoriasTableTableManager get cachedCategorias =>
      $$CachedCategoriasTableTableManager(_db, _db.cachedCategorias);
  $$CachedSubcategoriasTableTableManager get cachedSubcategorias =>
      $$CachedSubcategoriasTableTableManager(_db, _db.cachedSubcategorias);
  $$CachedProductosTableTableManager get cachedProductos =>
      $$CachedProductosTableTableManager(_db, _db.cachedProductos);
  $$CachedEstatusProductoTableTableManager get cachedEstatusProducto =>
      $$CachedEstatusProductoTableTableManager(_db, _db.cachedEstatusProducto);
  $$CacheMetaTableTableManager get cacheMeta =>
      $$CacheMetaTableTableManager(_db, _db.cacheMeta);
  $$PendingGameResultsTableTableManager get pendingGameResults =>
      $$PendingGameResultsTableTableManager(_db, _db.pendingGameResults);
  $$PendingSessionTimeTableTableManager get pendingSessionTime =>
      $$PendingSessionTimeTableTableManager(_db, _db.pendingSessionTime);
}
