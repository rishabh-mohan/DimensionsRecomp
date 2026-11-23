// Agent 10 (task #9): tests for the two rex/math.h fixes.
//  1. clamp_float<T> kept the intermediate in a float, which rounded double inputs to float precision.
//  2. rotate_left<T>(v, 0) shifted by the full type width, which is UB for 32/64-bit T.
// Built with -fsanitize=shift -fsanitize-trap=shift, so the old rotate_left traps at sh = 0.
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <limits>

#include <rex/math.h>

static int g_fail = 0;
#define EXPECT(c, ...) do { if (!(c)) { g_fail++; printf("  FAIL: " __VA_ARGS__); printf("\n"); } } while (0)

template <class T> static void rot_all() {
  constexpr int w = sizeof(T) * 8;
  const uint64_t vals[] = {0, 1, 0x80, 0x8001, 0x12345678u, 0x80000001u, 0x0123456789ABCDEFull, ~0ull, 0xF0F0F0F0F0F0F0F0ull};
  for (uint64_t v64 : vals) {
    T v = T(v64);
    for (int sh = 0; sh < 256; sh++) {  // every uint8_t count; rotation is by sh mod width
      uint64_t mask = w == 64 ? ~0ull : ((1ull << w) - 1);
      uint64_t u = uint64_t(v) & mask;
      int s = sh % w;
      uint64_t want = s ? (((u << s) | (u >> (w - s))) & mask) : u;
      T got = rex::rotate_left<T>(v, uint8_t(sh));
      EXPECT((uint64_t(got) & mask) == want, "rotate_left<%d-bit>(%llx, %d) = %llx, want %llx", w,
             (unsigned long long)u, sh, (unsigned long long)(uint64_t(got) & mask), (unsigned long long)want);
    }
  }
}

int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);  // keep output if the shift sanitizer traps
  // clamp_float<double>: values that are not representable as float must come back unchanged.
  const double xs[] = {1.0 + 1e-12, 0.1, 0.333333333333333314829616256247, 1e-300, 0.9999999999};
  for (double x : xs) {
    double got = rex::clamp_float<double>(x, 0.0, 2.0);
    EXPECT(got == x, "clamp_float<double>(%.17g, 0, 2) = %.17g", x, got);
  }
  EXPECT(rex::clamp_float<double>(3.0, 0.0, 2.0) == 2.0, "clamp_float<double> upper bound");
  EXPECT(rex::clamp_float<double>(-1.0, 0.0, 2.0) == 0.0, "clamp_float<double> lower bound");
  EXPECT(rex::clamp_float<double>(std::numeric_limits<double>::quiet_NaN(), 0.0, 2.0) == 0.0, "clamp_float<double>(NaN) = min");
  EXPECT(rex::clamp_float<double>(1e300, 0.0, 1e301) == 1e300, "clamp_float<double> beyond float range");
  // float behaviour is unchanged
  EXPECT(rex::clamp_float<float>(0.5f, 0.0f, 1.0f) == 0.5f, "clamp_float<float> inside");
  EXPECT(rex::clamp_float<float>(std::numeric_limits<float>::quiet_NaN(), 0.0f, 1.0f) == 0.0f, "clamp_float<float>(NaN)");
  EXPECT(std::signbit(rex::saturate(-0.0f)) == std::signbit(rex::clamp_float(-0.0f, 0.0f, 1.0f)), "saturate(-0)");
  EXPECT(rex::saturate(2.0) == 1.0 && rex::saturate(0.25) == 0.25, "saturate<double>");

  rot_all<uint8_t>();
  rot_all<uint16_t>();
  rot_all<uint32_t>();
  rot_all<uint64_t>();

  printf("test_math: %s (%d failure(s))\n", g_fail ? "FAILED" : "PASSED", g_fail);
  return g_fail ? 1 : 0;
}
