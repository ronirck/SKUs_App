import 'package:supabase_flutter/supabase_flutter.dart';

import 'fetch_all_pages.dart';

class RemoteUsuarioConfig {
  const RemoteUsuarioConfig({
    required this.sede,
    required this.marcasPermitidas,
    required this.soloInfaltables,
    required this.configVersion,
  });

  final String sede;
  final List<String> marcasPermitidas;
  final bool soloInfaltables;
  final int configVersion;
}

class CatalogRemoteDataSource {
  CatalogRemoteDataSource(this._client);

  final SupabaseClient _client;

  Future<RemoteUsuarioConfig> fetchUsuarioConfig(String userId) async {
    final row = await _client.from('usuario_config').select().eq('usuario_id', userId).single();
    return RemoteUsuarioConfig(
      sede: row['sede'] as String,
      marcasPermitidas: List<String>.from(row['marcas_permitidas'] as List? ?? const []),
      soloInfaltables: row['solo_infaltables'] as bool? ?? false,
      configVersion: row['config_version'] as int,
    );
  }

  Future<String?> fetchVersionDatos() async {
    final row =
        await _client.from('app_config').select().eq('clave', 'version_datos').maybeSingle();
    return row?['valor'] as String?;
  }

  // Todas las lecturas de catálogo van paginadas con `fetchAllPages`:
  // Supabase corta cualquier respuesta en 1000 filas aunque no se pida
  // límite, y `productos` supera eso con holgura en varias sedes. El
  // `order` fija un orden estable para que las páginas no se solapen.
  Future<List<Map<String, dynamic>>> fetchCategorias(String sede) {
    return fetchAllPages(
      (from, to) => _client.from('categorias').select().eq('sede', sede).order('codigo', ascending: true).range(from, to),
    );
  }

  Future<List<Map<String, dynamic>>> fetchSubcategorias(String sede) {
    return fetchAllPages(
      (from, to) => _client
          .from('subcategorias')
          .select()
          .eq('sede', sede)
          .order('categoria_codigo', ascending: true)
          .order('codigo', ascending: true)
          .range(from, to),
    );
  }

  Future<List<Map<String, dynamic>>> fetchEstatusProducto() {
    return fetchAllPages(
      (from, to) => _client.from('estatus_producto').select().order('codigo', ascending: true).range(from, to),
    );
  }

  Future<List<Map<String, dynamic>>> fetchProductos({
    required String sede,
    List<String>? marcaFilter,
    List<String>? estatusFilter,
  }) {
    return fetchAllPages((from, to) {
      var query = _client.from('productos').select().eq('sede', sede);
      if (marcaFilter != null) query = query.inFilter('marca', marcaFilter);
      if (estatusFilter != null) query = query.inFilter('estatus', estatusFilter);
      return query.order('id', ascending: true).range(from, to);
    });
  }
}
