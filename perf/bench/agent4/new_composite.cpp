// The same per-draw checks after session 2: draw.cpp:436-437 TimingEnabled / PortraitProbeOn over
// the real draw_cached_flag.h, and LongProbeEnabled from the real dev long_probe.h.
#include <cstdint>

#include "bench_common.h"
#include "draw_cached_flag.h"
#include "flag_tu.h"
#include "long_probe.h"

using legodimensions::gpu_native::CachedProcessFlag;
using legodimensions::gpu_native::LongProbeEnabled;

namespace {
bool TimingEnabled() { return CachedProcessFlag<shipped::NativeTextureTimingEnabled>(); }
bool PortraitProbeOn() { return CachedProcessFlag<shipped::PortraitProbeEnabled>(); }
thread_local bool t_preparing_draw = false;
}  // namespace

uint64_t NewPerDraw(size_t draws) {
  uint64_t taken = 0;
  for (size_t i = 0; i < draws; ++i) {
    if (TimingEnabled()) ++taken;
    bench::ClobberMemory();
    for (int timer = 0; timer < 3; ++timer) {
      if (TimingEnabled() && !t_preparing_draw) ++taken;
      bench::ClobberMemory();
    }
    if (PortraitProbeOn()) ++taken;
    bench::ClobberMemory();
    for (int check = 0; check < 20; ++check) {
      if (LongProbeEnabled()) ++taken;
      bench::ClobberMemory();
    }
  }
  return taken;
}

uint64_t NewTimingChecks(size_t checks) {
  uint64_t taken = 0;
  for (size_t i = 0; i < checks; ++i) {
    if (TimingEnabled()) ++taken;
    bench::ClobberMemory();
  }
  return taken;
}

uint64_t NewLongProbeChecks(size_t checks) {
  uint64_t taken = 0;
  for (size_t i = 0; i < checks; ++i) {
    if (LongProbeEnabled()) ++taken;
    bench::ClobberMemory();
  }
  return taken;
}

bool NewTimingValue() { return TimingEnabled(); }
bool NewPortraitValue() { return PortraitProbeOn(); }
bool NewLongProbeValue() { return LongProbeEnabled(); }
bool LongProbeEnabledForPortrait() { return LongProbeEnabled(); }
