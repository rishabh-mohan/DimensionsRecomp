// Item 5 (perf-notes/agent4-draw-path.md): "log the first N" throttles on the per-draw path.
// Old: `counter.fetch_add(1) < limit` on every draw, a locked RMW forever. New: TakeLogBudget from the
// real draw_log_throttle.h. One modelled draw passes the three DispatchDraw sites (depth state 32,
// instanced 16, issued draw 8) with the budgets already spent, which is the steady state.
#include <atomic>
#include <cstdint>
#include <thread>

#include "bench_common.h"
#include "draw_log_throttle.h"

using legodimensions::gpu_native::TakeLogBudget;

namespace {

bool OldBudget(std::atomic<uint32_t>& counter, uint32_t limit) { return counter.fetch_add(1) < limit; }

template <bool kNew>
inline bool Take(std::atomic<uint32_t>& counter, uint32_t limit) {
  if constexpr (kNew) return TakeLogBudget(counter, limit);
  else return OldBudget(counter, limit);
}

// Function-local statics in DispatchDraw; kept on separate lines here (no false sharing helps old).
struct alignas(64) Counter { std::atomic<uint32_t> value{0}; };
Counter g_depth, g_instanced, g_issued;

template <bool kNew>
BENCH_NOINLINE uint64_t Draws(size_t draws) {
  uint64_t logged = 0;
  for (size_t i = 0; i < draws; ++i) {
    if (Take<kNew>(g_depth.value, 32)) ++logged;
    bench::ClobberMemory();
    if (Take<kNew>(g_instanced.value, 16)) ++logged;
    bench::ClobberMemory();
    if (Take<kNew>(g_issued.value, 8)) ++logged;
    bench::ClobberMemory();
  }
  return logged;
}

// Both threads draw at once on the shared counters (threaded recording / parallel preparation).
template <bool kNew>
double TwoThreads(size_t draws) {
  std::atomic<int> ready{0};
  std::atomic<bool> go{false};
  double ns[2]{};
  auto body = [&](int index) {
    ready.fetch_add(1);
    while (!go.load()) {}
    ns[index] = bench::NsPerOp(draws, [&] { bench::DoNotOptimize(Draws<kNew>(draws)); });
  };
  std::thread a(body, 0), b(body, 1);
  while (ready.load() < 2) {}
  go.store(true);
  a.join();
  b.join();
  return ns[0] > ns[1] ? ns[0] : ns[1];
}

void UnitTests() {
  // One thread: true for exactly the first `limit` calls, as the old form; the counter stops at limit.
  for (uint32_t limit : {0u, 1u, 8u, 16u, 32u}) {
    std::atomic<uint32_t> fresh{0}, old{0};
    for (uint32_t i = 0; i < 1000; ++i) {
      const bool taken = TakeLogBudget(fresh, limit);
      BENCH_CHECK(taken == OldBudget(old, limit));
      BENCH_CHECK(taken == (i < limit));
    }
    BENCH_CHECK(fresh.load() == limit);
    BENCH_CHECK(old.load() == 1000);
  }
  // Two threads racing from zero: exactly `limit` trues in total; at most one stale load per thread
  // can add past the limit, and the thread that took the last slot cannot, so <= limit + 1.
  for (int round = 0; round < 50; ++round) {
    for (uint32_t limit : {1u, 8u, 32u}) {
      std::atomic<uint32_t> counter{0}, trues{0};
      std::atomic<bool> go{false};
      auto body = [&] {
        while (!go.load()) {}
        uint32_t taken = 0;
        for (int i = 0; i < 100000; ++i) taken += TakeLogBudget(counter, limit) ? 1 : 0;
        trues.fetch_add(taken);
      };
      std::thread a(body), b(body);
      go.store(true);
      a.join();
      b.join();
      BENCH_CHECK(trues.load() == limit);
      BENCH_CHECK(counter.load() >= limit && counter.load() <= limit + 1);
    }
  }
  // The accepted log-only difference: the old counter wraps after 2^32 calls and logs again.
  std::atomic<uint32_t> near_wrap_old{0xFFFFFFF0u}, near_wrap_new{0xFFFFFFF0u};
  uint32_t old_trues = 0, new_trues = 0;
  for (int i = 0; i < 64; ++i) {
    old_trues += OldBudget(near_wrap_old, 8) ? 1 : 0;
    new_trues += TakeLogBudget(near_wrap_new, 8) ? 1 : 0;
  }
  BENCH_CHECK(old_trues == 8 && new_trues == 0 && near_wrap_new.load() == 0xFFFFFFF0u);
  std::puts("log_throttle unit tests: OK");
}

}  // namespace

int main() {
  UnitTests();
  constexpr size_t kDraws = 4'000'000, kDraws2T = 1'000'000;
  bench::RunCases("log_throttle", {
      {"1T old fetch_add, 3 sites/draw", [] {
         g_depth.value = 32; g_instanced.value = 16; g_issued.value = 8;
         return bench::NsPerOp(kDraws, [] { bench::DoNotOptimize(Draws<false>(kDraws)); }); }},
      {"1T new TakeLogBudget, 3 sites/draw", [] {
         g_depth.value = 32; g_instanced.value = 16; g_issued.value = 8;
         return bench::NsPerOp(kDraws, [] { bench::DoNotOptimize(Draws<true>(kDraws)); }); }},
      {"2T old fetch_add, 3 sites/draw", [] {
         g_depth.value = 32; g_instanced.value = 16; g_issued.value = 8;
         return TwoThreads<false>(kDraws2T); }},
      {"2T new TakeLogBudget, 3 sites/draw", [] {
         g_depth.value = 32; g_instanced.value = 16; g_issued.value = 8;
         return TwoThreads<true>(kDraws2T); }},
  });
  return 0;
}
