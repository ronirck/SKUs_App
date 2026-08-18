import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/session/domain/split_by_local_day.dart';

void main() {
  group('edge cases', () {
    test('end equal to start returns empty (zero-length session)', () {
      final t = DateTime(2026, 7, 5, 10, 0);
      expect(splitByLocalDay(t, t), isEmpty);
    });

    test('end before start returns empty, never negative durations', () {
      final start = DateTime(2026, 7, 5, 10, 0);
      final end = DateTime(2026, 7, 5, 9, 0);
      expect(splitByLocalDay(start, end), isEmpty);
    });

    test('a session crossing midnight splits into two day buckets', () {
      final start = DateTime(2026, 7, 5, 23, 50);
      final end = DateTime(2026, 7, 6, 0, 10);
      final result = splitByLocalDay(start, end);

      expect(result.length, 2);
      expect(result[DateTime(2026, 7, 5)], const Duration(minutes: 10));
      expect(result[DateTime(2026, 7, 6)], const Duration(minutes: 10));
    });

    test('a session spanning multiple midnights splits into one bucket per day', () {
      final start = DateTime(2026, 7, 5, 23, 0);
      final end = DateTime(2026, 7, 7, 1, 0);
      final result = splitByLocalDay(start, end);

      expect(result.length, 3);
      expect(result[DateTime(2026, 7, 5)], const Duration(hours: 1));
      expect(result[DateTime(2026, 7, 6)], const Duration(hours: 24));
      expect(result[DateTime(2026, 7, 7)], const Duration(hours: 1));
    });
  });

  group('happy path', () {
    test('a session entirely within one day returns a single bucket', () {
      final start = DateTime(2026, 7, 5, 9, 0);
      final end = DateTime(2026, 7, 5, 9, 45);
      final result = splitByLocalDay(start, end);

      expect(result, {DateTime(2026, 7, 5): const Duration(minutes: 45)});
    });
  });
}
