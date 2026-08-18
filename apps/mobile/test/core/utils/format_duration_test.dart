import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/core/utils/format_duration.dart';

void main() {
  group('edge cases', () {
    test('zero duration formats as 00:00:00', () {
      expect(formatHms(Duration.zero), '00:00:00');
    });

    test('durations longer than 24 hours keep accumulating hours', () {
      expect(formatHms(const Duration(hours: 25, minutes: 3, seconds: 4)), '25:03:04');
    });
  });

  group('happy path', () {
    test('pads single-digit components with a leading zero', () {
      expect(formatHms(const Duration(hours: 1, minutes: 2, seconds: 3)), '01:02:03');
    });
  });
}
