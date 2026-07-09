import 'package:skus_app/features/auth/data/profile_repository.dart';
import 'package:skus_app/features/auth/domain/user_profile.dart';

class FakeProfileRepository implements ProfileRepository {
  UserProfile? profile;

  @override
  Future<UserProfile?> fetchCurrentProfile() async => profile;

  @override
  Future<void> confirmNombreApellido({required String nombre, required String apellido}) async {}

  @override
  Future<void> markOnboardingCompleted() async {}

  @override
  Future<void> saveLastKnownProfile(UserProfile profile) async {}

  @override
  Future<UserProfile?> loadLastKnownProfile() async => null;

  @override
  Future<void> clearLastKnownProfile() async {}
}
