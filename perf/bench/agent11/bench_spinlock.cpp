// bench_spinlock.cpp - Agent 11 helper B (Task #10 item 4): kernel spinlock
// acquire. Today: CAS, and SwitchToThread (MaybeYield) after every failed CAS.
// Proposed (spinlock_pause_spin): test-and-test-and-set with a CPU pause, and
// MaybeYield only after a bounded number of pauses.
//
// Replica of rexglue-sdk src/kernel/xboxkrnl/xboxkrnl_threading.cpp
// xeKeKfAcquireSpinLock / xeKeKfReleaseSpinLock: the owner is the byte-swapped
// PCR address, the interlocked helpers are out of line (src/core/atomic_win.cpp,
// uint32 overloads inline as in include/rex/thread/atomic.h), MaybeYield is
// SwitchToThread + MemoryBarrier (src/core/threading_win.cpp), and the IRQL is
// raised/lowered on a fake per-thread PCR.
//
// Variants:
//   old        while (!cas(0, self)) MaybeYield();
//   ttas:K     cas; on failure do { if (++pauses < K) pause; else { MaybeYield(); pauses = 0; } }
//              while (lock != 0); then retry the cas. The pause budget is per acquire.
//   ttast:NS   the SDK shape: reads the cvar first (off -> the old loop), then one
//              CAS and the same TTAS, but MaybeYield only after NS ns of pausing
//              (steady_clock every 32 pauses; armed on the first failure,
//              re-armed per yield). Rounds 1-3 used a raw QPC deadline.
//   off        ttast with the spinlock_pause_spin "cvar" false: the cvar read,
//              then the original loop. The cost of shipping the change default-off.
// A "#tag" suffix (e.g. old#aa) makes a second copy of a variant (A/A control).
// Contended mode also reports the latency of contended acquires (those that
// failed at least one CAS): mean, p50/p99 (log histogram) and max.
// Modes:
//   paired      [rounds=300] [batch=20000] [variants=old,ttas:64]   (uncontended,
//               batch-interleaved on one pinned thread; robust on a loaded machine)
//   uncontended [reps=7] [n=5000000] [variants=old,ttas:128]
//   contended   [reps=5] [ms=100] [hold_ns=100] [variants=old,ttas:128] [affs=none,pp,ee,pe]
//               [long_every=500] [long_ns=20000] [gap_ns=200]
// At most 2 worker threads. Interleaved rep-major; medians reported.
#include "bench_common.h"

#include <immintrin.h>
#include <intrin.h>

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <string>
#include <thread>

static double g_tsc_per_ns = 1.0;
static void calibrate_tsc() {
  const int64_t q0 = qpc();
  const uint64_t c0 = __rdtsc();
  spin_ticks(qpf() / 20);
  const uint64_t c1 = __rdtsc();
  const int64_t q1 = qpc();
  g_tsc_per_ns = double(c1 - c0) / ticks_ns(q1 - q0);
}
static inline uint64_t ns_to_tsc(double ns) { return uint64_t(ns * g_tsc_per_ns + 0.5); }
static inline void busy_tsc(uint64_t t) {
  if (!t) return;
  const uint64_t t0 = __rdtsc();
  while (__rdtsc() - t0 < t) {
  }
}
static uint64_t ft64(const FILETIME& f) { return (uint64_t(f.dwHighDateTime) << 32) | f.dwLowDateTime; }
static double process_cpu_s() {
  FILETIME c, e, k, u;
  GetProcessTimes(GetCurrentProcess(), &c, &e, &k, &u);
  return double(ft64(k) + ft64(u)) / 1e7;
}

// ------------------------------------------------- SDK replica: atomics ----
namespace rx {
__declspec(noinline) bool atomic_cas(int32_t old_value, int32_t new_value,
                                     volatile int32_t* value) {
  return _InterlockedCompareExchange(reinterpret_cast<volatile long*>(value), new_value,
                                     old_value) == old_value;
}
inline bool atomic_cas(uint32_t old_value, uint32_t new_value, volatile uint32_t* value) {
  return atomic_cas(int32_t(old_value), int32_t(new_value),
                    reinterpret_cast<volatile int32_t*>(value));
}
__declspec(noinline) void atomic_store_release(int32_t new_value, volatile int32_t* value) {
  _InterlockedExchange(reinterpret_cast<volatile long*>(value), new_value);
}
inline void atomic_store_release(uint32_t new_value, volatile uint32_t* value) {
  atomic_store_release(int32_t(new_value), reinterpret_cast<volatile int32_t*>(value));
}
__declspec(noinline) void MaybeYield() {
  SwitchToThread();
  MemoryBarrier();
}
}  // namespace rx

static inline void CpuRelax() { _mm_pause(); }
static inline uint32_t bs(uint32_t v) { return _byteswap_ulong(v); }

// Fake PCR: xeKfRaiseIrql/xeKfLowerIrql translate r13 and write current_irql.
struct alignas(64) FakePcr {
  uint8_t pad[0x40];
  volatile uint8_t current_irql;
};
__declspec(noinline) uint32_t RaiseIrql(FakePcr* pcr, uint8_t new_irql) {
  const uint8_t old_irql = pcr->current_irql;
  pcr->current_irql = new_irql;
  return old_irql;
}
__declspec(noinline) void LowerIrql(FakePcr* pcr, uint8_t new_irql) { pcr->current_irql = new_irql; }
constexpr uint8_t IRQL_DISPATCH = 2;

struct alignas(64) Stats {
  uint64_t ops = 0, fails = 0, yields = 0, acq_tsc = 0;
  uint64_t cont = 0, cont_tsc = 0, cont_max = 0;  // acquires that failed >= 1 CAS
  uint64_t cycles = 0;
  int64_t t_start = 0, t_end = 0;
  uint32_t hist[256] = {};  // contended acquire latency in TSC ticks, log2 x 4
};

// Log-linear histogram: 4 sub-buckets per power of two (about +-12%).
static inline int hbucket(uint64_t v) {
  if (v < 4) return int(v);
  unsigned long msb;
  _BitScanReverse64(&msb, v);
  return int(msb * 4 + ((v >> (msb - 2)) & 3));
}
static inline double hbucket_hi(int idx) {  // exclusive upper bound, ticks
  if (idx < 4) return double(idx + 1);
  const int msb = idx / 4, sub = idx % 4;
  return double(uint64_t(4 + sub + 1) << (msb - 2));
}

static volatile bool g_cvar_spinlock_pause_spin = true;
static volatile uint32_t g_param = 0;     // K pauses per yield
static volatile int64_t g_yield_ticks = 0;  // QPC ticks for ttast:NS

enum Kind : int { kOld = 0, kTtas = 1, kTtasTime = 2 };

template <int K>
__declspec(noinline) uint32_t Acquire(volatile uint32_t* lock, FakePcr* pcr, uint32_t pcr_addr,
                                      Stats& st) {
  const uint32_t old_irql = RaiseIrql(pcr, IRQL_DISPATCH);
  const uint32_t self = bs(pcr_addr);
  if constexpr (K == kOld) {
    while (!rx::atomic_cas(0u, self, lock)) {
      ++st.fails;
      ++st.yields;
      rx::MaybeYield();
    }
  } else if constexpr (K == kTtas) {
    if (!g_cvar_spinlock_pause_spin) {
      while (!rx::atomic_cas(0u, self, lock)) rx::MaybeYield();
      return old_irql;
    }
    const uint32_t pauses_per_yield = g_param;
    uint32_t pauses = 0;
    while (!rx::atomic_cas(0u, self, lock)) {
      ++st.fails;
      do {
        if (++pauses < pauses_per_yield) {
          CpuRelax();
        } else {
          ++st.yields;
          rx::MaybeYield();
          pauses = 0;
        }
      } while (*lock != 0);
    }
  } else {
    // The SDK shape (spinlock_pause_spin; AcquireSpinLockPauseSpin in
    // xboxkrnl_threading.cpp): cvar off -> the original loop; on -> one CAS,
    // then TTAS: pause + plain reads until the lock reads free, then the CAS
    // again. MaybeYield only after the yield bound of pausing (steady_clock,
    // checked every 32 pauses; armed on the first failure, re-armed per yield).
    if (!g_cvar_spinlock_pause_spin) {
      while (!rx::atomic_cas(0u, self, lock)) rx::MaybeYield();
      return old_irql;
    }
    if (rx::atomic_cas(0u, self, lock)) return old_irql;
    ++st.fails;
    auto deadline = std::chrono::steady_clock::now() + std::chrono::nanoseconds(g_param);
    for (;;) {
      uint32_t n = 0;
      do {
        CpuRelax();
        if ((++n & 31) == 0 && std::chrono::steady_clock::now() >= deadline) {
          ++st.yields;
          rx::MaybeYield();
          deadline = std::chrono::steady_clock::now() + std::chrono::nanoseconds(g_param);
        }
      } while (*lock != 0);
      if (rx::atomic_cas(0u, self, lock)) return old_irql;
      ++st.fails;
    }
  }
  return old_irql;
}

__declspec(noinline) void Release(volatile uint32_t* lock, FakePcr* pcr, uint32_t old_irql) {
  rx::atomic_store_release(0u, lock);
  if (old_irql < IRQL_DISPATCH) LowerIrql(pcr, uint8_t(old_irql));
}

using AcquireFn = uint32_t (*)(volatile uint32_t*, FakePcr*, uint32_t, Stats&);
static AcquireFn acquire_for(int k) {
  switch (k) {
    case kOld: return &Acquire<kOld>;
    case kTtas: return &Acquire<kTtas>;
    default: return &Acquire<kTtasTime>;
  }
}

struct Variant {
  int kind = kOld;
  uint32_t param = 0;
  bool cvar_on = true;  // g_cvar_spinlock_pause_spin while this variant runs
  std::string name;
};
static std::vector<std::string> split(const std::string& s) {
  std::vector<std::string> out;
  size_t p = 0;
  while (p <= s.size()) {
    size_t c = s.find(',', p);
    if (c == std::string::npos) c = s.size();
    if (c > p) out.push_back(s.substr(p, c - p));
    p = c + 1;
  }
  return out;
}
static std::vector<Variant> parse_variants(const std::string& s) {
  std::vector<Variant> out;
  for (auto& t : split(s)) {
    Variant v;
    v.name = t;
    const std::string b = t.substr(0, t.find('#'));  // "old#aa": A/A control copy
    const size_t colon = b.find(':');
    const std::string k = b.substr(0, colon);
    v.param = colon == std::string::npos ? 0 : uint32_t(strtoul(b.c_str() + colon + 1, nullptr, 10));
    if (k == "old") v.kind = kOld;
    else if (k == "ttas") v.kind = kTtas;
    else if (k == "ttast") v.kind = kTtasTime;
    else if (k == "off") {
      v.kind = kTtasTime;
      v.cvar_on = false;
    } else {
      fprintf(stderr, "bad variant '%s'\n", t.c_str());
      exit(2);
    }
    out.push_back(v);
  }
  return out;
}
static void apply_variant(const Variant& v) {
  g_cvar_spinlock_pause_spin = v.cvar_on;
  g_param = v.param;
  g_yield_ticks = int64_t(double(v.param) * double(qpf()) / 1e9 + 0.5);
}

struct Aff {
  const char* name;
  DWORD_PTR m[2];
};
static const Aff kAffs[] = {
    {"none", {0, 0}}, {"pp", {0x3, 0xC}}, {"ee", {0xF0, 0xF00}}, {"pe", {0xF, 0xFF0}}};
static const Aff* find_aff(const std::string& n) {
  for (auto& a : kAffs)
    if (n == a.name) return &a;
  return nullptr;
}

struct alignas(64) Shared {
  volatile uint32_t lock;  // X_KSPINLOCK::prcb_of_owner raw value
  char pad0[60];
  volatile uint64_t counter;  // protected by the lock
  char pad1[56];
};
static Shared g_sh;
static std::atomic<int> g_ready{0};
static std::atomic<bool> g_go{false}, g_stop{false};

struct RunOut {
  double ns_op = 0, cpu_ns_op = 0, util = 0, yields_M = 0, fails_M = 0, acq_ns = 0, fair = 0;
  double cont_M = 0, wait_mean = 0, wait_p50 = 0, wait_p99 = 0, wait_max = 0;
  bool excl_ok = true;
};

static double hist_pct_ns(const uint64_t* h, double p) {
  uint64_t total = 0;
  for (int i = 0; i < 256; ++i) total += h[i];
  if (!total) return 0;
  uint64_t cum = 0;
  for (int i = 0; i < 256; ++i) {
    cum += h[i];
    if (double(cum) >= p * double(total)) return hbucket_hi(i) / g_tsc_per_ns;
  }
  return hbucket_hi(255) / g_tsc_per_ns;
}

static RunOut run_contended(const Variant& v, const Aff& a, double hold_ns, uint32_t long_every,
                            double long_ns, double gap_ns, int ms) {
  g_sh.lock = 0;
  g_sh.counter = 0;
  apply_variant(v);
  const AcquireFn acquire = acquire_for(v.kind);
  const uint64_t hold = ns_to_tsc(hold_ns), long_hold = ns_to_tsc(long_ns), gap = ns_to_tsc(gap_ns);
  g_ready.store(0);
  g_go.store(false);
  g_stop.store(false);
  Stats st[2];
  auto body = [&](int idx) {
    if (a.m[idx]) SetThreadAffinityMask(GetCurrentThread(), a.m[idx]);
    FakePcr pcr{};
    const uint32_t pcr_addr = 0x7FFE0000u + 0x1000u * uint32_t(idx);
    Stats s;
    uint32_t n = 0;
    g_ready.fetch_add(1);
    while (!g_go.load(std::memory_order_acquire)) _mm_pause();
    ULONG64 c0 = 0, c1 = 0;
    QueryThreadCycleTime(GetCurrentThread(), &c0);
    s.t_start = qpc();
    while (!g_stop.load(std::memory_order_relaxed)) {
      const uint64_t f0 = s.fails;
      const uint64_t a0 = __rdtsc();
      const uint32_t old_irql = acquire(&g_sh.lock, &pcr, pcr_addr, s);
      const uint64_t dt = __rdtsc() - a0;
      g_sh.counter = g_sh.counter + 1;
      busy_tsc((long_every && ++n % long_every == 0) ? long_hold : hold);
      Release(&g_sh.lock, &pcr, old_irql);
      s.acq_tsc += dt;
      if (s.fails != f0) {  // contended acquire: record how long it waited
        ++s.cont;
        s.cont_tsc += dt;
        s.cont_max = std::max(s.cont_max, dt);
        ++s.hist[hbucket(dt)];
      }
      ++s.ops;
      busy_tsc(gap);
    }
    s.t_end = qpc();
    QueryThreadCycleTime(GetCurrentThread(), &c1);
    s.cycles = c1 - c0;
    st[idx] = s;
  };
  std::thread t0(body, 0), t1(body, 1);
  while (g_ready.load() < 2) Sleep(0);
  g_go.store(true, std::memory_order_release);
  Sleep(DWORD(ms));
  g_stop.store(true, std::memory_order_relaxed);
  t0.join();
  t1.join();

  RunOut r;
  const uint64_t ops_u = st[0].ops + st[1].ops;
  const double ops = double(std::max<uint64_t>(ops_u, 1));
  const double wall_ns =
      ticks_ns(std::max(st[0].t_end, st[1].t_end) - std::min(st[0].t_start, st[1].t_start));
  const double cpu_ns = double(st[0].cycles + st[1].cycles) / g_tsc_per_ns;
  r.ns_op = wall_ns / ops;
  r.cpu_ns_op = cpu_ns / ops;
  r.util = cpu_ns / wall_ns;
  r.yields_M = double(st[0].yields + st[1].yields) * 1e6 / ops;
  r.fails_M = double(st[0].fails + st[1].fails) * 1e6 / ops;
  r.acq_ns = double(st[0].acq_tsc + st[1].acq_tsc) / g_tsc_per_ns / ops;
  r.fair = double(std::min(st[0].ops, st[1].ops)) / ops;
  r.excl_ok = g_sh.counter == ops_u;
  uint64_t h[256];
  for (int i = 0; i < 256; ++i) h[i] = uint64_t(st[0].hist[i]) + st[1].hist[i];
  const uint64_t cont = st[0].cont + st[1].cont;
  r.cont_M = double(cont) * 1e6 / ops;
  r.wait_mean = cont ? double(st[0].cont_tsc + st[1].cont_tsc) / g_tsc_per_ns / double(cont) : 0;
  r.wait_p50 = hist_pct_ns(h, 0.50);
  r.wait_p99 = hist_pct_ns(h, 0.99);
  r.wait_max = double(std::max(st[0].cont_max, st[1].cont_max)) / g_tsc_per_ns;
  return r;
}

static double run_uncontended(const Variant& v, DWORD_PTR mask, uint64_t n) {
  g_sh.lock = 0;
  apply_variant(v);
  const AcquireFn acquire = acquire_for(v.kind);
  double result = 0;
  std::thread t([&] {
    if (mask) SetThreadAffinityMask(GetCurrentThread(), mask);
    FakePcr pcr{};
    Stats s;
    for (int i = 0; i < 20000; ++i) Release(&g_sh.lock, &pcr, acquire(&g_sh.lock, &pcr, 0x7FFE0000u, s));
    const int64_t t0 = qpc();
    for (uint64_t i = 0; i < n; ++i) Release(&g_sh.lock, &pcr, acquire(&g_sh.lock, &pcr, 0x7FFE0000u, s));
    const int64_t t1 = qpc();
    result = ticks_ns(t1 - t0) / double(n);
  });
  t.join();
  return result;
}

int main(int argc, char** argv) {
  calibrate_tsc();
  {
    SYSTEM_POWER_STATUS ps{};
    if (GetSystemPowerStatus(&ps))
      printf("[power] ACLineStatus=%u (1=AC, 0=battery) battery=%u%%  tsc=%.4f GHz\n",
             ps.ACLineStatus, ps.BatteryLifePercent, g_tsc_per_ns);
  }
  const std::string mode = argc > 1 ? argv[1] : "contended";
  if (mode == "paired") {
    // Uncontended, batch-interleaved on one pinned thread (robust on a loaded
    // machine): each round runs one batch of every variant back to back.
    const int rounds = argc > 2 ? atoi(argv[2]) : 300;
    const uint64_t batch = argc > 3 ? strtoull(argv[3], nullptr, 10) : 20000ull;
    const auto vs = parse_variants(argc > 4 ? argv[4] : "old,ttas:64");
    struct Core {
      const char* name;
      DWORD_PTR mask;
    } cores[] = {{"P", 0xF}, {"E", 0xFF0}};
    printf("uncontended acquire+release, paired: %d rounds x %llu per variant per core\n", rounds,
           (unsigned long long)batch);
    for (auto& core : cores) {
      std::vector<std::vector<double>> res(vs.size());
      std::thread t([&] {
        SetThreadAffinityMask(GetCurrentThread(), core.mask);
        FakePcr pcr{};
        Stats s;
        g_sh.lock = 0;
        std::vector<AcquireFn> fns;
        for (auto& v : vs) fns.push_back(acquire_for(v.kind));
        for (size_t i = 0; i < vs.size(); ++i) {
          apply_variant(vs[i]);
          for (int k = 0; k < 20000; ++k)
            Release(&g_sh.lock, &pcr, fns[i](&g_sh.lock, &pcr, 0x7FFE0000u, s));
        }
        for (int r = 0; r < rounds; ++r)
          for (size_t i0 = 0; i0 < vs.size(); ++i0) {
            const size_t i = (i0 + size_t(r)) % vs.size();
            apply_variant(vs[i]);
            const AcquireFn fn = fns[i];
            const uint64_t a = __rdtsc();
            for (uint64_t k = 0; k < batch; ++k)
              Release(&g_sh.lock, &pcr, fn(&g_sh.lock, &pcr, 0x7FFE0000u, s));
            const uint64_t b = __rdtsc();
            res[i].push_back(double(b - a) / g_tsc_per_ns / double(batch));
          }
      });
      t.join();
      for (size_t i = 0; i < vs.size(); ++i) {
        std::vector<double> d;
        for (size_t r = 0; r < res[i].size(); ++r) d.push_back(res[i][r] - res[0][r]);
        printf("  core=%s  %-12s median %6.2f  p10 %6.2f  p90 %6.2f ns   paired diff vs %s: "
               "%+5.2f ns\n",
               core.name, vs[i].name.c_str(), median(res[i]), pct(res[i], 0.1),
               pct(res[i], 0.9), vs[0].name.c_str(), median(d));
      }
    }
  } else if (mode == "uncontended") {
    const int reps = argc > 2 ? atoi(argv[2]) : 7;
    const uint64_t n = argc > 3 ? strtoull(argv[3], nullptr, 10) : 5000000ull;
    const auto vs = parse_variants(argc > 4 ? argv[4] : "old,ttas:128");
    struct Core {
      const char* name;
      DWORD_PTR mask;
    } cores[] = {{"P", 0xF}, {"E", 0xFF0}};
    std::vector<std::vector<double>> res(2 * vs.size());
    for (int rep = 0; rep < reps; ++rep)
      for (int c = 0; c < 2; ++c)
        for (size_t i = 0; i < vs.size(); ++i)
          res[c * vs.size() + i].push_back(run_uncontended(vs[i], cores[c].mask, n));
    printf("uncontended acquire+release, %llu x %d reps (median [min..max] ns)\n",
           (unsigned long long)n, reps);
    for (int c = 0; c < 2; ++c)
      for (size_t i = 0; i < vs.size(); ++i) {
        auto& v = res[c * vs.size() + i];
        printf("  core=%s  %-12s %6.2f [%6.2f .. %6.2f]\n", cores[c].name, vs[i].name.c_str(),
               median(v), vmin(v), vmax(v));
      }
  } else if (mode == "contended") {
    const int reps = argc > 2 ? atoi(argv[2]) : 5;
    const int ms = argc > 3 ? atoi(argv[3]) : 100;
    const double hold_ns = argc > 4 ? atof(argv[4]) : 100.0;
    const auto vs = parse_variants(argc > 5 ? argv[5] : "old,ttas:128");
    std::vector<const Aff*> affs;
    for (auto& s : split(argc > 6 ? argv[6] : "none,pp,ee,pe")) {
      const Aff* a = find_aff(s);
      if (!a) {
        fprintf(stderr, "bad affinity '%s'\n", s.c_str());
        return 2;
      }
      affs.push_back(a);
    }
    const uint32_t long_every = argc > 7 ? uint32_t(atoi(argv[7])) : 500u;
    const double long_ns = argc > 8 ? atof(argv[8]) : 20000.0;
    const double gap_ns = argc > 9 ? atof(argv[9]) : 200.0;
    const size_t NV = vs.size(), NA = affs.size();
    std::vector<std::vector<RunOut>> res(NA * NV);
    bool excl_ok = true;
    for (int rep = 0; rep < reps; ++rep)
      for (size_t a = 0; a < NA; ++a)
        for (size_t i = 0; i < NV; ++i) {
          RunOut r = run_contended(vs[i], *affs[a], hold_ns, long_every, long_ns, gap_ns, ms);
          excl_ok &= r.excl_ok;
          res[a * NV + i].push_back(r);
        }
    printf("contended spinlock: 2 threads, %d ms x %d reps, hold %.0f ns (every %u-th: %.0f ns), "
           "gap %.0f ns. Medians.\n",
           ms, reps, hold_ns, long_every, long_ns, gap_ns);
    printf("Contended acquire = one that failed at least one CAS; wait = its acquire latency "
           "(p50/p99 from a log histogram, +-12%%; max = median over reps of the run max).\n");
    printf("%-4s %-12s %8s %8s %8s %9s %5s %9s %9s %9s %9s %8s %8s %9s %5s\n", "aff", "variant",
           "ns/acq", "min", "max", "cpu_ns/acq", "util", "yield/1M", "fail/1M", "cont/1M",
           "wait_avg", "wait_p50", "wait_p99", "wait_max", "fair");
    for (size_t a = 0; a < NA; ++a)
      for (size_t i = 0; i < NV; ++i) {
        auto& rr = res[a * NV + i];
        auto col = [&](double RunOut::* m) {
          std::vector<double> v;
          for (auto& r : rr) v.push_back(r.*m);
          return v;
        };
        auto ns = col(&RunOut::ns_op);
        printf("%-4s %-12s %8.1f %8.1f %8.1f %9.1f %5.2f %9.0f %9.0f %9.0f %9.0f %8.0f %8.0f "
               "%9.0f %5.3f\n",
               affs[a]->name, vs[i].name.c_str(), median(ns), vmin(ns), vmax(ns),
               median(col(&RunOut::cpu_ns_op)), median(col(&RunOut::util)),
               median(col(&RunOut::yields_M)), median(col(&RunOut::fails_M)),
               median(col(&RunOut::cont_M)), median(col(&RunOut::wait_mean)),
               median(col(&RunOut::wait_p50)), median(col(&RunOut::wait_p99)),
               median(col(&RunOut::wait_max)), median(col(&RunOut::fair)));
      }
    printf("mutual exclusion check: %s\n", excl_ok ? "OK" : "VIOLATED");
  } else {
    fprintf(stderr, "usage: bench_spinlock uncontended ... | contended ...\n");
    return 2;
  }
  printf("[cpu] process CPU time %.2f s\n", process_cpu_s());
  return 0;
}
