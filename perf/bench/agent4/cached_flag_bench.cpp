// Item 6 (perf-notes/agent4-draw-path.md): process-constant diagnostic flags on the per-draw path.
// Unit tests for draw_cached_flag.h, then old vs new per-draw cost with every diagnostic off.
// `--expect-on` (run_benches.py sets the three variables) only checks values with them set.
#include <atomic>
#include <chrono>
#include <cstring>
#include <thread>

#include "bench_common.h"
#include "draw_cached_flag.h"
#include "flag_tu.h"

using legodimensions::gpu_native::CachedProcessFlag;

namespace {

int g_false_reads = 0, g_true_reads = 0;
bool ReadFalse() { ++g_false_reads; return false; }
bool ReadTrue() { ++g_true_reads; return true; }
std::atomic<int> g_slow_reads{0};
bool SlowRead() {
  g_slow_reads.fetch_add(1);
  std::this_thread::sleep_for(std::chrono::milliseconds(20));
  return true;
}

void UnitTests(bool expect_on) {
  // Read runs on the first check only and its value is kept.
  for (int i = 0; i < 1000; ++i) {
    BENCH_CHECK(!CachedProcessFlag<ReadFalse>());
    BENCH_CHECK(CachedProcessFlag<ReadTrue>());
  }
  BENCH_CHECK(g_false_reads == 1 && g_true_reads == 1);
  // Threads racing the first check may each call Read; all get its value and Read is not called again.
  bool seen[2]{};
  std::thread a([&] { seen[0] = CachedProcessFlag<SlowRead>(); });
  std::thread b([&] { seen[1] = CachedProcessFlag<SlowRead>(); });
  a.join();
  b.join();
  const int racing = g_slow_reads.load();
  BENCH_CHECK(seen[0] && seen[1] && racing >= 1 && racing <= 2);
  for (int i = 0; i < 100; ++i) BENCH_CHECK(CachedProcessFlag<SlowRead>());
  BENCH_CHECK(g_slow_reads.load() == racing);
  // The cached checks give the uncached functions' values, with the variables unset or set.
  BENCH_CHECK(NewTimingValue() == shipped::NativeTextureTimingEnabled());
  BENCH_CHECK(NewPortraitValue() == shipped::PortraitProbeEnabled());
  BENCH_CHECK(NewLongProbeValue() == OldLongProbeValue());
  BENCH_CHECK(NewTimingValue() == expect_on && NewPortraitValue() == expect_on &&
              NewLongProbeValue() == expect_on);
  std::printf("cached_flag unit tests (variables %s): OK\n", expect_on ? "set" : "unset");
}

}  // namespace

int main(int argc, char** argv) {
  const bool expect_on = argc > 1 && std::strcmp(argv[1], "--expect-on") == 0;
  UnitTests(expect_on);
  if (expect_on) return 0;
  constexpr size_t kDraws = 1'000'000, kChecks = 20'000'000;
  bench::RunCases("cached_flag", {
      {"per draw old: 5 flag calls + 20 guarded LongProbe", [] {
         return bench::NsPerOp(kDraws, [] { bench::DoNotOptimize(OldPerDraw(kDraws)); }); }},
      {"per draw new: 25 cached-flag checks", [] {
         return bench::NsPerOp(kDraws, [] { bench::DoNotOptimize(NewPerDraw(kDraws)); }); }},
      {"one check old NativeTextureTimingEnabled()", [] {
         return bench::NsPerOp(kChecks, [] { bench::DoNotOptimize(OldTimingChecks(kChecks)); }); }},
      {"one check new TimingEnabled()", [] {
         return bench::NsPerOp(kChecks, [] { bench::DoNotOptimize(NewTimingChecks(kChecks)); }); }},
      {"one check old LongProbeEnabled()", [] {
         return bench::NsPerOp(kChecks, [] { bench::DoNotOptimize(OldLongProbeChecks(kChecks)); }); }},
      {"one check new LongProbeEnabled()", [] {
         return bench::NsPerOp(kChecks, [] { bench::DoNotOptimize(NewLongProbeChecks(kChecks)); }); }},
  });
  return 0;
}
