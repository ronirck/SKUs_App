/// true si un release dirigido a [target] ('admin'|'user'|'all') debe
/// notificarse a un usuario con rol [userRole].
bool shouldNotifyForRole(String target, String userRole) {
  return target == 'all' || target == userRole;
}
