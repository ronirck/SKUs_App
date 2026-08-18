import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../domain/user_profile.dart';

abstract class ProfileRepository {
  Future<UserProfile?> fetchCurrentProfile();
  Future<void> confirmNombreApellido({required String nombre, required String apellido});
  Future<void> markOnboardingCompleted();

  /// Persiste el último perfil leído con éxito, para poder enrutar sin red
  /// (ver [loadLastKnownProfile]).
  Future<void> saveLastKnownProfile(UserProfile profile);

  /// Último perfil guardado por [saveLastKnownProfile], o `null` si nunca se
  /// guardó uno. Se usa como respaldo cuando no hay red para leer el perfil
  /// real — deja que la app siga funcionando offline en vez de atascarse.
  Future<UserProfile?> loadLastKnownProfile();

  /// Borra el último perfil conocido — se usa al cerrar sesión para que, sin
  /// red, otro usuario en el mismo dispositivo no herede el estado del
  /// anterior.
  Future<void> clearLastKnownProfile();
}

class SupabaseProfileRepository implements ProfileRepository {
  SupabaseProfileRepository(this._client);

  static const _kId = 'last_known_profile_id';
  static const _kNombre = 'last_known_profile_nombre';
  static const _kApellido = 'last_known_profile_apellido';
  static const _kEstado = 'last_known_profile_estado';
  static const _kOnboarding = 'last_known_profile_onboarding';
  static const _kRol = 'last_known_profile_rol';

  final SupabaseClient _client;

  @override
  Future<UserProfile?> fetchCurrentProfile() async {
    final userId = _client.auth.currentUser?.id;
    if (userId == null) return null;
    final row = await _client.from('perfil_usuario').select().eq('usuario_id', userId).maybeSingle();
    if (row == null) return null;
    return UserProfile.fromMap(row);
  }

  @override
  Future<void> saveLastKnownProfile(UserProfile profile) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kId, profile.id);
    await prefs.setString(_kEstado, profile.estado.name);
    await prefs.setBool(_kOnboarding, profile.onboardingCompletado);
    await prefs.setString(_kRol, profile.rol);
    if (profile.nombre != null) {
      await prefs.setString(_kNombre, profile.nombre!);
    } else {
      await prefs.remove(_kNombre);
    }
    if (profile.apellido != null) {
      await prefs.setString(_kApellido, profile.apellido!);
    } else {
      await prefs.remove(_kApellido);
    }
  }

  @override
  Future<UserProfile?> loadLastKnownProfile() async {
    final prefs = await SharedPreferences.getInstance();
    final id = prefs.getString(_kId);
    final estado = prefs.getString(_kEstado);
    if (id == null || estado == null) return null;
    return UserProfile(
      id: id,
      nombre: prefs.getString(_kNombre),
      apellido: prefs.getString(_kApellido),
      estado: EstadoUsuario.fromString(estado),
      onboardingCompletado: prefs.getBool(_kOnboarding) ?? false,
      rol: prefs.getString(_kRol) ?? 'user',
    );
  }

  @override
  Future<void> clearLastKnownProfile() async {
    final prefs = await SharedPreferences.getInstance();
    await Future.wait([
      prefs.remove(_kId),
      prefs.remove(_kNombre),
      prefs.remove(_kApellido),
      prefs.remove(_kEstado),
      prefs.remove(_kOnboarding),
      prefs.remove(_kRol),
    ]);
  }

  @override
  Future<void> confirmNombreApellido({required String nombre, required String apellido}) async {
    final userId = _client.auth.currentUser!.id;
    await _client
        .from('perfil_usuario')
        .update({'nombre': nombre, 'apellido': apellido}).eq('usuario_id', userId);
  }

  @override
  Future<void> markOnboardingCompleted() async {
    final userId = _client.auth.currentUser!.id;
    await _client
        .from('perfil_usuario')
        .update({'onboarding_completado': true}).eq('usuario_id', userId);
  }
}
