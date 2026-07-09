class GoogleNamePrefill {
  const GoogleNamePrefill({required this.nombre, required this.apellido});
  final String nombre;
  final String apellido;
}

/// Extrae nombre/apellido del `user_metadata` que Supabase guarda del login
/// con Google, para pre-llenar (no confirmar) el formulario. Google entrega
/// `given_name`/`family_name` la mayoría de las veces; si faltan, se parte
/// `full_name`/`name` por espacios como respaldo.
GoogleNamePrefill extractNameFromGoogleMetadata(Map<String, dynamic>? metadata) {
  if (metadata == null) return const GoogleNamePrefill(nombre: '', apellido: '');

  final givenName = metadata['given_name'] as String?;
  final familyName = metadata['family_name'] as String?;
  if ((givenName != null && givenName.trim().isNotEmpty) ||
      (familyName != null && familyName.trim().isNotEmpty)) {
    return GoogleNamePrefill(nombre: givenName?.trim() ?? '', apellido: familyName?.trim() ?? '');
  }

  final fullName = (metadata['full_name'] ?? metadata['name']) as String?;
  if (fullName == null || fullName.trim().isEmpty) {
    return const GoogleNamePrefill(nombre: '', apellido: '');
  }

  final parts = fullName.trim().split(RegExp(r'\s+'));
  if (parts.length == 1) return GoogleNamePrefill(nombre: parts.first, apellido: '');
  return GoogleNamePrefill(nombre: parts.first, apellido: parts.sublist(1).join(' '));
}
