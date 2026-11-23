// bench_waitsignal.cpp - agent11 bench (c). Two threads ping-pong on two
// auto-reset events (SetEvent, then WaitForSingleObjectEx(other, 5000, FALSE)).
// Every Set and Wait is wrapped in one of:
//   NONE - nothing;
//   OLD  - what GetNativeObject costs today: std::recursive_mutex locked twice
//          (nested), Retain (atomic inc), unlocked twice; Release (atomic dec)
//          after the call;
//   NEW  - acquire-load of the signature word, std::shared_lock on a
//          std::shared_mutex, Retain; Release after the call.
// Modes are interleaved in chunks of 10k round trips.
// Usage: bench_waitsignal.exe [runs=5] [chunks_per_mode=10]
#include "bench_common.h"

#include <atomic>
#include <cstdlib>
#include <mutex>
#include <shared_mutex>
#include <thread>

constexpr uint32_t kSigBE = 0x00584552;  // 'REX\0' big-endian word as read on x86
struct Obj {
  alignas(64) std::atomic<int32_t> refs{1};
  HANDLE ev = nullptr;
  uint32_t sig = kSigBE;
};
static std::recursive_mutex G;  // global_critical_region
static std::shared_mutex T;     // NEW: separate object-table lock
static Obj A, B;
static std::atomic<int> g_bad{0};

template <int M>
static inline void pre(Obj& o) {
  if constexpr (M == 1) {
    G.lock();
    G.lock();
    ++o.refs;
    G.unlock();
    G.unlock();
  } else if constexpr (M == 2) {
    if (std::atomic_ref<uint32_t>(o.sig).load(std::memory_order_acquire) != kSigBE) g_bad++;
    std::shared_lock<std::shared_mutex> lk(T);
    ++o.refs;
  }
}
template <int M>
static inline void post(Obj& o) {
  if constexpr (M != 0) --o.refs;
}

template <int M>
static bool t1_chunk(int n, float* lat, double tpn) {
  for (int i = 0; i < n; ++i) {
    const uint64_t t0 = bench_a::tsc_begin();
    pre<M>(A); SetEvent(A.ev); post<M>(A);
    pre<M>(B); const DWORD r = WaitForSingleObjectEx(B.ev, 5000, FALSE); post<M>(B);
    if (r != WAIT_OBJECT_0) return false;
    lat[i] = float(double(bench_a::tsc_end() - t0) / tpn);
  }
  return true;
}
template <int M>
static bool t2_chunk(int n) {
  for (int i = 0; i < n; ++i) {
    pre<M>(A); const DWORD r = WaitForSingleObjectEx(A.ev, 5000, FALSE); post<M>(A);
    if (r != WAIT_OBJECT_0) return false;
    pre<M>(B); SetEvent(B.ev); post<M>(B);
  }
  return true;
}
static bool t1_dispatch(int m, int n, float* lat, double tpn) {
  return m == 0 ? t1_chunk<0>(n, lat, tpn) : m == 1 ? t1_chunk<1>(n, lat, tpn) : t1_chunk<2>(n, lat, tpn);
}
static bool t2_dispatch(int m, int n) {
  return m == 0 ? t2_chunk<0>(n) : m == 1 ? t2_chunk<1>(n) : t2_chunk<2>(n);
}

int main(int argc, char** argv) {
  const int runs = argc > 1 ? atoi(argv[1]) : 5;
  const int cpm = argc > 2 ? atoi(argv[2]) : 10;
  const int chunk = 10000;
  const char* kMode[3] = {"NONE", "OLD ", "NEW "};
  bench_a::print_machine_state("start");
  const double tpn = bench_a::tsc_per_ns();
  printf("TSC %.3f GHz; runs=%d; %d round trips per mode per run (chunks of %d, modes interleaved)\n", tpn, runs,
         cpm * chunk, chunk);
  A.ev = CreateEventW(nullptr, FALSE, FALSE, nullptr);
  B.ev = CreateEventW(nullptr, FALSE, FALSE, nullptr);
  std::vector<double> mean[3], p50[3], p90[3], p99[3], mx[3];
  std::vector<float> lat(chunk);
  for (int r = 0; r < runs; ++r) {
    const int nch = 3 * cpm;
    std::atomic<bool> ok2{true};
    std::thread t2([&] {
      for (int c = 0; c < nch; ++c)
        if (!t2_dispatch((c + r) % 3, chunk)) { ok2 = false; return; }
    });
    std::vector<double> all[3];
    int64_t tot[3] = {0, 0, 0};
    bool ok = true;
    for (int c = 0; c < nch && ok; ++c) {
      const int m = (c + r) % 3;
      const int64_t t0 = qpc();
      ok = t1_dispatch(m, chunk, lat.data(), tpn);
      tot[m] += qpc() - t0;
      all[m].insert(all[m].end(), lat.begin(), lat.end());
    }
    t2.join();
    if (!ok || !ok2) {
      printf("ERROR: a wait timed out in run %d\n", r + 1);
      return 1;
    }
    printf("run %d:", r + 1);
    for (int m = 0; m < 3; ++m) {
      const auto s = bench_a::summarize(all[m]);
      const double mn = ticks_ns(tot[m]) / double(cpm * chunk);
      mean[m].push_back(mn); p50[m].push_back(s.med); p90[m].push_back(s.p90);
      p99[m].push_back(s.p99); mx[m].push_back(s.max);
      printf("  %s mean %.0f p50 %.0f p99 %.0f max %.0f |", kMode[m], mn, s.med, s.p99, s.max);
    }
    printf("\n");
    fflush(stdout);
  }
  printf("\nSUMMARY ns per round trip (4 guarded calls per round trip), median of %d runs [min..max of run values]\n",
         runs);
  printf("  mode | mean ns/RT              | p50     | p90     | p99     | max(all) | mean - NONE\n");
  for (int m = 0; m < 3; ++m)
    printf("  %s | %7.0f [%6.0f..%6.0f] | %7.0f | %7.0f | %7.0f | %8.0f | %+.0f\n", kMode[m], median(mean[m]),
           vmin(mean[m]), vmax(mean[m]), median(p50[m]), median(p90[m]), median(p99[m]), vmax(mx[m]),
           median(mean[m]) - median(mean[0]));
  printf("signature mismatches: %d\n", g_bad.load());
  bench_a::print_machine_state("end");
  return 0;
}
