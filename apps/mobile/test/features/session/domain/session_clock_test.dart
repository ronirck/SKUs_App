import 'package:flutter_test/flutter_test.dart';
import 'package:skus_app/features/session/domain/session_clock.dart';

void main() {
  group('edge cases', () {
    test('pause() when never resumed returns null and elapsed stays zero', () {
      final clock = SessionClock(now: () => DateTime(2026, 7, 5, 10, 0));
      expect(clock.pause(), isNull);
      expect(clock.elapsed, Duration.zero);
      clock.dispose();
    });

    test('resume() called twice in a row does not reset accumulated time', () {
      var current = DateTime(2026, 7, 5, 10, 0);
      final clock = SessionClock(now: () => current);

      clock.resume();
      current = current.add(const Duration(seconds: 30));
      clock.resume(); // no-op: ya estaba corriendo
      current = current.add(const Duration(seconds: 30));

      expect(clock.elapsed, const Duration(seconds: 60));
      clock.pause();
      clock.dispose();
    });

    test('pause() after pause() again returns null (already stopped)', () {
      var current = DateTime(2026, 7, 5, 10, 0);
      final clock = SessionClock(now: () => current);
      clock.resume();
      current = current.add(const Duration(seconds: 10));
      clock.pause();
      expect(clock.pause(), isNull);
      clock.dispose();
    });
  });

  group('happy path', () {
    test('elapsed reflects live time while running', () {
      var current = DateTime(2026, 7, 5, 10, 0);
      final clock = SessionClock(now: () => current);

      clock.resume();
      current = current.add(const Duration(seconds: 45));
      expect(clock.elapsed, const Duration(seconds: 45));

      clock.pause();
      clock.dispose();
    });

    test('accumulates correctly across multiple resume/pause cycles', () {
      var current = DateTime(2026, 7, 5, 10, 0);
      final clock = SessionClock(now: () => current);

      clock.resume();
      current = current.add(const Duration(seconds: 20));
      final first = clock.pause()!;
      expect(first.start, DateTime(2026, 7, 5, 10, 0));
      expect(first.end, current);

      current = current.add(const Duration(minutes: 5)); // tiempo en segundo plano, no cuenta
      clock.resume();
      current = current.add(const Duration(seconds: 10));
      clock.pause();

      expect(clock.elapsed, const Duration(seconds: 30));
      clock.dispose();
    });
  });
}
