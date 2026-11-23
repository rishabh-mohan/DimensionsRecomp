// The per-draw diagnostic checks before session 2: baseline draw.cpp DrawTimer / ConstantTimer /
// DispatchDraw and the baseline long_probe.h LongProbeEnabled (verbatim, own namespace).
#include <cstdint>
#include <cstdlib>
#include <filesystem>

#include "bench_common.h"
#include "flag_tu.h"

namespace old_lp {
inline const std::filesystem::path& LongProbeDirectory() {
  static const std::filesystem::path path = [] {
    char* value = nullptr; size_t length = 0;
    _dupenv_s(&value, &length, "LEGO_NATIVE_TRACE_DIR");
    std::filesystem::path result(value ? value : "");
    std::free(value); return result;
  }();
  return path;
}
inline bool LongProbeEnabled() { return !LongProbeDirectory().empty(); }
}  // namespace old_lp

namespace {
thread_local bool t_preparing_draw = false;
}

// One draw on the default path with every diagnostic off: DrawTimer, three ConstantTimers, the
// portrait probe in DispatchDraw and ~20 LongProbeEnabled checks (per texture slot and draw tail).
uint64_t OldPerDraw(size_t draws) {
  uint64_t taken = 0;
  for (size_t i = 0; i < draws; ++i) {
    if (shipped::NativeTextureTimingEnabled()) ++taken;
    bench::ClobberMemory();
    for (int timer = 0; timer < 3; ++timer) {
      if (!t_preparing_draw && shipped::NativeTextureTimingEnabled()) ++taken;
      bench::ClobberMemory();
    }
    if (shipped::PortraitProbeEnabled()) ++taken;
    bench::ClobberMemory();
    for (int check = 0; check < 20; ++check) {
      if (old_lp::LongProbeEnabled()) ++taken;
      bench::ClobberMemory();
    }
  }
  return taken;
}

uint64_t OldTimingChecks(size_t checks) {
  uint64_t taken = 0;
  for (size_t i = 0; i < checks; ++i) {
    if (shipped::NativeTextureTimingEnabled()) ++taken;
    bench::ClobberMemory();
  }
  return taken;
}

uint64_t OldLongProbeChecks(size_t checks) {
  uint64_t taken = 0;
  for (size_t i = 0; i < checks; ++i) {
    if (old_lp::LongProbeEnabled()) ++taken;
    bench::ClobberMemory();
  }
  return taken;
}

bool OldLongProbeValue() { return old_lp::LongProbeEnabled(); }
