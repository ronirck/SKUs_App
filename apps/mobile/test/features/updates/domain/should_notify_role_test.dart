import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/updates/domain/should_notify_role.dart';

void main() {
  group('edge cases', () {
    test('a target for a different role is not notified', () {
      expect(shouldNotifyForRole('user', 'admin'), isFalse);
      expect(shouldNotifyForRole('admin', 'user'), isFalse);
    });
  });

  group('happy path', () {
    test('target "all" notifies every role', () {
      expect(shouldNotifyForRole('all', 'admin'), isTrue);
      expect(shouldNotifyForRole('all', 'user'), isTrue);
    });

    test('a matching target notifies that role', () {
      expect(shouldNotifyForRole('admin', 'admin'), isTrue);
      expect(shouldNotifyForRole('user', 'user'), isTrue);
    });
  });
}
