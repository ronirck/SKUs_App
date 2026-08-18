import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/updates/domain/is_critical_release.dart';

void main() {
  group('edge cases', () {
    test('a name without the marker is not critical', () {
      expect(isCriticalRelease('Release 2.0.0'), isFalse);
    });

    test('the marker is matched case-insensitively', () {
      expect(isCriticalRelease('[critical] Release 2.0.0'), isTrue);
    });
  });

  group('happy path', () {
    test('a name with [CRITICAL] is critical', () {
      expect(isCriticalRelease('[CRITICAL] Release 2.0.0'), isTrue);
    });
  });
}
