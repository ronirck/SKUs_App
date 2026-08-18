import 'package:supabase_flutter/supabase_flutter.dart';

import '../../auth/domain/user_profile.dart';

class AdminUserSummary {
  const AdminUserSummary({
    required this.usuarioId,
    required this.nombre,
    required this.apellido,
    required this.estado,
    required this.rol,
    required this.creadoEn,
    required this.sede,
    required this.marcasPermitidas,
    required this.soloInfaltables,
    required this.configVersion,
  });

  final String usuarioId;
  final String? nombre;
  final String? apellido;
  final EstadoUsuario estado;
  final String rol;
  final DateTime creadoEn;
  final String sede;
  final List<String> marcasPermitidas;
  final bool soloInfaltables;
  final int configVersion;
}

class TopError {
  const TopError({
    required this.tipoElemento,
    required this.elementoCodigo,
    required this.elementoNombre,
    required this.vecesFallado,
  });

  final String tipoElemento;
  final String elementoCodigo;
  final String elementoNombre;
  final int vecesFallado;
}

class AdminUserStats {
  const AdminUserStats({
    required this.totalPartidas,
    required this.efectividad,
    required this.duracionSesionTotal,
    required this.topErrores,
  });

  final int totalPartidas;
  final double efectividad;
  final Duration duracionSesionTotal;
  final List<TopError> topErrores;
}

class AdminRepository {
  AdminRepository(this._client);

  final SupabaseClient _client;

  Future<List<AdminUserSummary>> fetchAllUsers() async {
    // El admin autenticado se excluye de la lista: no debe poder cambiarse
    // el estado o la configuración a sí mismo (p. ej. quitarse el acceso).
    final propioId = _client.auth.currentUser?.id;
    final perfiles = await _client.from('perfil_usuario').select();
    final configs = await _client.from('usuario_config').select();
    final configPorUsuario = {
      for (final c in configs) c['usuario_id'] as String: c,
    };

    return perfiles.where((p) => p['usuario_id'] != propioId).map((p) {
      final usuarioId = p['usuario_id'] as String;
      final config = configPorUsuario[usuarioId];
      return AdminUserSummary(
        usuarioId: usuarioId,
        nombre: p['nombre'] as String?,
        apellido: p['apellido'] as String?,
        estado: EstadoUsuario.fromString(p['estado'] as String),
        rol: p['rol'] as String? ?? 'user',
        creadoEn: DateTime.parse(p['creado_en'] as String),
        sede: config?['sede'] as String? ?? '',
        marcasPermitidas: List<String>.from(config?['marcas_permitidas'] as List? ?? const []),
        soloInfaltables: config?['solo_infaltables'] as bool? ?? false,
        configVersion: config?['config_version'] as int? ?? 0,
      );
    }).toList();
  }

  Future<void> setEstado({required String usuarioId, required EstadoUsuario estado}) async {
    await _client
        .from('perfil_usuario')
        .update({'estado': estado.name}).eq('usuario_id', usuarioId);
  }

  /// Incrementa `config_version` para que la caché local del usuario se
  /// reconstruya en su próximo chequeo de conectividad (ver Fase 2/4).
  Future<void> updateUsuarioConfig({
    required String usuarioId,
    required String sede,
    required List<String> marcasPermitidas,
    required bool soloInfaltables,
  }) async {
    final current = await _client
        .from('usuario_config')
        .select('config_version')
        .eq('usuario_id', usuarioId)
        .single();
    final nextVersion = (current['config_version'] as int) + 1;

    // `.select()` devuelve las filas afectadas: si RLS bloquea el UPDATE el
    // resultado llega vacío sin error, y eso debe tratarse como fallo.
    final updated = await _client
        .from('usuario_config')
        .update({
          'sede': sede,
          'marcas_permitidas': marcasPermitidas,
          'solo_infaltables': soloInfaltables,
          'config_version': nextVersion,
        })
        .eq('usuario_id', usuarioId)
        .select();
    if (updated.isEmpty) {
      throw StateError('usuario_config no se actualizó (¿política RLS?)');
    }
  }

  /// Cambia la sede (casa) que ve el PROPIO admin autenticado. Sube su
  /// `config_version` para que `ensureSynced` detecte el cambio y
  /// reconstruya el caché con el catálogo de la casa nueva.
  Future<void> updateOwnSede(String sede) async {
    final usuarioId = _client.auth.currentUser?.id;
    if (usuarioId == null) {
      throw StateError('No hay sesión activa.');
    }
    final current = await _client
        .from('usuario_config')
        .select('config_version')
        .eq('usuario_id', usuarioId)
        .single();
    final nextVersion = (current['config_version'] as int) + 1;

    final updated = await _client
        .from('usuario_config')
        .update({'sede': sede, 'config_version': nextVersion})
        .eq('usuario_id', usuarioId)
        .select();
    if (updated.isEmpty) {
      throw StateError('usuario_config no se actualizó (¿política RLS?)');
    }
  }

  Future<List<String>> fetchMarcas(String sede) async {
    final rows = await _client.from('marcas').select('nombre').eq('sede', sede);
    return rows.map((r) => r['nombre'] as String).toList();
  }

  Future<AdminUserStats> fetchUserStats(String usuarioId) async {
    final resultados =
        await _client.from('resultados_codex').select().eq('usuario_id', usuarioId);
    final totalPartidas = resultados.length;
    final totalAciertos = resultados.fold<int>(0, (s, r) => s + (r['aciertos'] as int));
    final totalPreguntas = resultados.fold<int>(0, (s, r) => s + (r['total_preguntas'] as int));
    final efectividad = totalPreguntas == 0 ? 0.0 : (totalAciertos / totalPreguntas) * 100;

    final sesiones = await _client
        .from('session_logs')
        .select('duracion_segundos')
        .eq('usuario_id', usuarioId);
    final totalSegundos =
        sesiones.fold<int>(0, (s, r) => s + (r['duracion_segundos'] as int));

    final errores = await _client
        .from('errores_partida')
        .select()
        .eq('usuario_id', usuarioId)
        .order('veces_fallado', ascending: false)
        .limit(5);
    final topErrores = errores
        .map((e) => TopError(
              tipoElemento: e['tipo_elemento'] as String,
              elementoCodigo: e['elemento_codigo'] as String,
              elementoNombre: e['elemento_nombre'] as String,
              vecesFallado: e['veces_fallado'] as int,
            ))
        .toList();

    return AdminUserStats(
      totalPartidas: totalPartidas,
      efectividad: efectividad,
      duracionSesionTotal: Duration(seconds: totalSegundos),
      topErrores: topErrores,
    );
  }
}
