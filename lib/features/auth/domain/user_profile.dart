enum EstadoUsuario {
  pendiente,
  aprobado,
  rechazado;

  static EstadoUsuario fromString(String value) {
    return EstadoUsuario.values.firstWhere(
      (e) => e.name == value,
      orElse: () => throw ArgumentError('Estado de usuario desconocido: $value'),
    );
  }
}

class UserProfile {
  const UserProfile({
    required this.id,
    required this.nombre,
    required this.apellido,
    required this.estado,
    required this.onboardingCompletado,
    required this.rol,
  });

  factory UserProfile.fromMap(Map<String, dynamic> map) {
    return UserProfile(
      id: map['usuario_id'] as String,
      nombre: map['nombre'] as String?,
      apellido: map['apellido'] as String?,
      estado: EstadoUsuario.fromString(map['estado'] as String),
      onboardingCompletado: map['onboarding_completado'] as bool? ?? false,
      rol: map['rol'] as String? ?? 'user',
    );
  }

  final String id;
  final String? nombre;
  final String? apellido;
  final EstadoUsuario estado;
  final bool onboardingCompletado;
  final String rol;

  bool get nombreApellidoConfirmado =>
      (nombre != null && nombre!.trim().isNotEmpty) &&
      (apellido != null && apellido!.trim().isNotEmpty);
}
