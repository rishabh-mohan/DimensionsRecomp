// bench_cs.cpp - Agent 11 helper B (Task #10 item 3): does a bounded
// read-then-CAS pause spin in RtlEnterCriticalSection pay off?
//
// A single-file replica of rexglue-sdk's guest critical section
// (src/kernel/xboxkrnl/xboxkrnl_rtl.cpp: RtlEnterCriticalSection_entry and
// RtlLeaveCriticalSection_entry) and of the kernel wait/set path it falls into
// (xeKeWaitForSingleObject / xeKeSetEvent -> XObject::GetNativeObject, which
// takes the recursive global critical region twice and retains/releases the
// object, then an auto-reset Win32 event with 5 s wait slices). The interlocked
// helpers are out of line, as in src/core/atomic_win.cpp.
//
// Variants (comma-separated list):
//   old       current SDK code, guest spin 0 (what RtlInitializeCriticalSection
//             sets): no spin, straight to atomic_inc and the kernel wait.
//   oldg:N    current SDK code with a guest spin count of N: tight CAS loop.
//   iter:N    cs_spin candidate A (rounds 1-2): one CAS, then up to N x (pause;
//             plain read; CAS only when the read shows -1), then the unchanged
//             wait path.
//   timecas:NS  the FINAL SDK shape (CAS first). Round 2 printed an earlier
//             version of it as "time:" and round 3 as "timecas:" (QPC deadline).
//             From round 4 it is the exact SDK code: if a spin is configured,
//             one CAS, then pause / plain read / CAS only when the read shows -1
//             until the steady_clock deadline NS ns away (checked every 16
//             pauses) and the guest spin count are both used up; then the
//             original loop with spin_count = 0 and the unchanged wait path.
//   time:NS   read-first alternative (round 3, rejected): one plain read; free
//             -> the original atomic_inc path; held -> the pause/read/CAS loop.
//             A stale "free" read on a contended line commits to atomic_inc and
//             then to a kernel wait: 3-25x more kernel waits than timecas.
//   off:NS    timecas:NS with the cs_spin "cvar" false: the cvar read, then the
//             original code. The cost of shipping the change default-off.
// A "#tag" suffix (e.g. old#aa) makes a second copy of a variant: an A/A
// control for the paired mode.
//
// Modes:
//   info
//   uncontended [reps=7] [pairs=3000000] [variants=old,iter:64]
//   paired      [rounds=300] [batch=20000] [variants=old,iter:64]   (uncontended,
//               batch-interleaved on one pinned thread; robust on a loaded machine)
//   contended   [reps=5] [ms=100] [holds=50,500,5000] [variants=old,iter:64,time:3000]
//               [affs=none,pp,ee,pe] [gap_ns=200]
// At most 2 worker threads. Runs are interleaved rep-major; medians reported.
// bench_common.h serializes agent11 bench processes (named mutex).
#include "bench_common.h"

#include <immintrin.h>
#include <intrin.h>

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <string>
#include <thread>

// ------------------------------------------------------------------ timing --
static double g_tsc_per_ns = 1.0;

static void calibrate_tsc() {
  const int64_t q0 = qpc();
  const uint64_t c0 = __rdtsc();
  spin_ticks(qpf() / 20);  // 50 ms
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
static uint64_t thread_time_100ns() {
  FILETIME c, e, k, u;
  GetThreadTimes(GetCurrentThread(), &c, &e, &k, &u);
  auto v = [](const FILETIME& f) { return (uint64_t(f.dwHighDateTime) << 32) | f.dwLowDateTime; };
  return v(k) + v(u);
}
static double process_cpu_s() {
  FILETIME c, e, k, u;
  GetProcessTimes(GetCurrentProcess(), &c, &e, &k, &u);
  auto v = [](const FILETIME& f) { return (uint64_t(f.dwHighDateTime) << 32) | f.dwLowDateTime; };
  return double(v(k) + v(u)) / 1e7;
}
static void print_power() {
  SYSTEM_POWER_STATUS ps{};
  if (GetSystemPowerStatus(&ps)) {
    printf("[power] ACLineStatus=%u (1=AC, 0=battery) BatteryFlag=0x%02x battery=%u%%\n",
           ps.ACLineStatus, ps.BatteryFlag, ps.BatteryLifePercent);
  }
}

// ------------------------------------------------- SDK replica: atomics ----
namespace rx {
__declspec(noinline) int32_t atomic_inc(volatile int32_t* value) {
  return _InterlockedIncrement(reinterpret_cast<volatile long*>(value));
}
__declspec(noinline) int32_t atomic_dec(volatile int32_t* value) {
  return _InterlockedDecrement(reinterpret_cast<volatile long*>(value));
}
__declspec(noinline) bool atomic_cas(int32_t old_value, int32_t new_value,
                                     volatile int32_t* value) {
  return _InterlockedCompareExchange(reinterpret_cast<volatile long*>(value), new_value,
                                     old_value) == old_value;
}
}  // namespace rx

static inline void CpuRelax() { _mm_pause(); }

// ---------------------------------------------- SDK replica: structures ----
#pragma pack(push, 1)
struct X_DISPATCH_HEADER {
  uint8_t type;
  uint8_t absolute;  // spin count / 256
  uint8_t size;
  uint8_t inserted;
  uint32_t signal_state_be;
  uint32_t wait_list_flink_be;
  uint32_t wait_list_blink_be;
};
struct X_RTL_CRITICAL_SECTION {
  X_DISPATCH_HEADER header;
  int32_t lock_count;           // 0x10, native, -1 when free
  uint32_t recursion_count_be;  // rex::be<int32_t>
  uint32_t owning_thread_be;    // rex::be<uint32_t>
};
#pragma pack(pop)
static_assert(sizeof(X_RTL_CRITICAL_SECTION) == 28, "layout");

static inline uint32_t bs(uint32_t v) { return _byteswap_ulong(v); }

// --------------------------------------- SDK replica: kernel wait/set path --
constexpr uint32_t kXObjSignature = 0x58454E00;  // 'XEN\0'
constexpr uint32_t X_STATUS_TIMEOUT = 0x00000102;

struct KernelReplica {
  std::recursive_mutex global_critical_region;
  HANDLE event = nullptr;  // native handle of the XEvent backing the CS
  std::atomic<int32_t> refs{1};
  std::atomic<bool> terminating{false};
};
static KernelReplica g_kernel;

__declspec(noinline) bool CheckTitleTermination() {
  return g_kernel.terminating.load(std::memory_order_acquire);
}
// ObjectTable::LookupObject: takes the global critical region again, retains.
__declspec(noinline) HANDLE LookupObject(uint32_t handle) {
  std::lock_guard<std::recursive_mutex> lock(g_kernel.global_critical_region);
  (void)handle;
  g_kernel.refs.fetch_add(1, std::memory_order_acq_rel);
  return g_kernel.event;
}
// XObject::GetNativeObject: global critical region, signature check, lookup.
__declspec(noinline) HANDLE GetNativeObject(X_DISPATCH_HEADER* header) {
  std::lock_guard<std::recursive_mutex> lock(g_kernel.global_critical_region);
  if (bs(header->wait_list_flink_be) != kXObjSignature) return nullptr;
  return LookupObject(bs(header->wait_list_blink_be));
}
__declspec(noinline) uint32_t xeKeWaitForSingleObject(X_DISPATCH_HEADER* header,
                                                      uint64_t* timeout) {
  HANDLE h = GetNativeObject(header);
  if (!h) return 0xC0000008;
  // XObject::Wait: relative guest 100 ns ticks -> ms.
  DWORD ms = INFINITE;
  if (timeout) {
    int64_t t = int64_t(*timeout);
    ms = DWORD((t < 0 ? -t : t) / 10000);
  }
  uint32_t result = 0;
  if (CheckTitleTermination()) {
    result = 0xC000004B;
  } else {
    DWORD r = WaitForSingleObjectEx(h, ms, FALSE);
    CheckTitleTermination();
    if (r == WAIT_TIMEOUT) {
      SwitchToThread();  // MaybeYield
      MemoryBarrier();
      result = X_STATUS_TIMEOUT;
    }
  }
  g_kernel.refs.fetch_sub(1, std::memory_order_acq_rel);  // object_ref release
  return result;
}
__declspec(noinline) void xeKeSetEvent(X_DISPATCH_HEADER* header) {
  HANDLE h = GetNativeObject(header);
  if (!h) return;
  SetEvent(h);  // XEvent::Set
  g_kernel.refs.fetch_sub(1, std::memory_order_acq_rel);
}

// XThread::GetCurrentThread()->guest_object()
static thread_local uint32_t t_guest_thread_object = 0;
__declspec(noinline) uint32_t CurrentGuestThreadObject() { return t_guest_thread_object; }

// --------------------------------------------------------------- stats -----
struct alignas(64) Stats {
  uint64_t ops = 0, fast = 0, spun = 0, late = 0, kwaits = 0, ksets = 0, timeouts = 0;
  uint64_t cycles = 0, thread_100ns = 0;
  int64_t t_start = 0, t_end = 0;
};

// "cvars": read on every Enter, as REXCVAR_GET reads the storage.
static volatile bool g_cvar_cs_spin = true;
static volatile uint32_t g_cvar_param = 0;  // cs_spin_count / guest spin / ns
static volatile int64_t g_time_ticks = 0;   // QPC ticks for time:NS

enum Kind : int { kOld = 0, kOldGuest = 1, kIter = 2, kTime = 3, kTimeCas = 4 };

static inline void SetOwner(X_RTL_CRITICAL_SECTION* cs, uint32_t cur_thread) {
  cs->owning_thread_be = bs(cur_thread);
  cs->recursion_count_be = bs(1u);
}

static void InitCS(X_RTL_CRITICAL_SECTION* cs) {
  // xeRtlInitializeCriticalSection, plus the signature GetNativeObject stamps
  // into the header the first time the CS's event is created.
  cs->header.type = 1;
  cs->header.absolute = 0;
  cs->header.size = 0;
  cs->header.inserted = 0;
  cs->header.signal_state_be = 0;
  cs->header.wait_list_flink_be = bs(kXObjSignature);
  cs->header.wait_list_blink_be = bs(0xF8000010u);
  cs->lock_count = -1;
  cs->recursion_count_be = 0;
  cs->owning_thread_be = 0;
}

template <int K>
__declspec(noinline) void Enter(X_RTL_CRITICAL_SECTION* cs, Stats& st) {
  const uint32_t cur_thread = CurrentGuestThreadObject();
  uint32_t spin_count = cs->header.absolute * 256;
  bool spun = false;

  if (bs(cs->owning_thread_be) == cur_thread) {
    rx::atomic_inc(&cs->lock_count);
    cs->recursion_count_be = bs(bs(cs->recursion_count_be) + 1);
    return;
  }

  if constexpr (K == kOld || K == kOldGuest) {
    // The SDK spin loop as it is today (cs_spin off).
    if constexpr (K == kOldGuest) spin_count = g_cvar_param;
    bool first = true;
    while (spin_count--) {
      if (rx::atomic_cas(-1, 0, &cs->lock_count)) {
        SetOwner(cs, cur_thread);
        ++(first ? st.fast : st.spun);
        return;
      }
      first = false;
      spun = true;
    }
  } else if constexpr (K == kIter) {
    // Iteration-bounded, CAS first (measured in rounds 1-2).
    if (!g_cvar_cs_spin) {
      // (original loop; not exercised here)
    } else if (const uint32_t spin = std::max(spin_count, uint32_t(g_cvar_param))) {
      if (rx::atomic_cas(-1, 0, &cs->lock_count)) {
        SetOwner(cs, cur_thread);
        ++st.fast;
        return;
      }
      spun = true;
      const volatile int32_t* lock_count = &cs->lock_count;
      for (uint32_t i = 0; i < spin; ++i) {
        CpuRelax();
        if (*lock_count == -1 && rx::atomic_cas(-1, 0, &cs->lock_count)) {
          SetOwner(cs, cur_thread);
          ++st.spun;
          return;
        }
      }
    }
  } else if constexpr (K == kTimeCas) {
    // The final SDK shape (cs_spin on; SpinForCriticalSection in
    // xboxkrnl_rtl.cpp): if a spin is configured (cs_spin_ns or a guest spin
    // count), one CAS, then pause / plain read / CAS only when the read shows
    // -1, until both the time bound (steady_clock, checked every 16 pauses)
    // and the guest spin count are used up. The original loop then runs with
    // spin_count = 0 (a no-op), then the unchanged atomic_inc / wait path.
    if (g_cvar_cs_spin) {
      const uint32_t spin_ns = g_cvar_param;
      if (spin_ns || spin_count) {
        if (rx::atomic_cas(-1, 0, &cs->lock_count)) {
          SetOwner(cs, cur_thread);
          ++st.fast;
          return;
        }
        spun = true;
        const volatile int32_t* lock_count = &cs->lock_count;
        const auto deadline =
            std::chrono::steady_clock::now() + std::chrono::nanoseconds(spin_ns);
        for (uint32_t i = 1;; ++i) {
          CpuRelax();
          if (*lock_count == -1 && rx::atomic_cas(-1, 0, &cs->lock_count)) {
            SetOwner(cs, cur_thread);
            ++st.spun;
            return;
          }
          if ((i & 15) == 0 && i >= spin_count && std::chrono::steady_clock::now() >= deadline) {
            break;
          }
        }
      }
      spin_count = 0;
    }
    while (spin_count--) {
      if (rx::atomic_cas(-1, 0, &cs->lock_count)) {
        SetOwner(cs, cur_thread);
        ++st.fast;
        return;
      }
    }
  } else {
    // Final SDK shape (cs_spin on): one plain read first. Free -> straight to
    // the original atomic_inc path, so the uncontended cost is one extra load.
    // Held -> spin (pause; read; CAS only when it reads -1) until both the time
    // bound and the guest spin count are used up, then the unchanged
    // atomic_inc / wait path. Spinners never touch a handed-off lock
    // (lock_count >= 0 while a woken waiter is in flight).
    const volatile int32_t* lock_count = &cs->lock_count;
    if (g_cvar_cs_spin && (g_cvar_param || spin_count) && *lock_count != -1) {
      spun = true;
      const int64_t deadline = qpc() + g_time_ticks;
      for (uint32_t i = 1;; ++i) {
        CpuRelax();
        if (*lock_count == -1 && rx::atomic_cas(-1, 0, &cs->lock_count)) {
          SetOwner(cs, cur_thread);
          ++st.spun;
          return;
        }
        if ((i & 15) == 0 && i >= spin_count && qpc() >= deadline) break;
      }
    }
  }

  if (rx::atomic_inc(&cs->lock_count) != 0) {
    ++st.kwaits;
    const int64_t slice = -10000000LL * 5;  // critical_section_stuck_seconds = 5
    for (;;) {
      uint64_t timeout = uint64_t(slice);
      if (xeKeWaitForSingleObject(&cs->header, &timeout) != X_STATUS_TIMEOUT) break;
      ++st.timeouts;
    }
  } else {
    ++(spun ? st.late : st.fast);
  }
  SetOwner(cs, cur_thread);
}

__declspec(noinline) void Leave(X_RTL_CRITICAL_SECTION* cs, Stats& st) {
  const int32_t recursion = int32_t(bs(cs->recursion_count_be)) - 1;
  cs->recursion_count_be = bs(uint32_t(recursion));
  if (recursion != 0) {
    rx::atomic_dec(&cs->lock_count);
    return;
  }
  cs->owning_thread_be = 0;
  if (rx::atomic_dec(&cs->lock_count) != -1) {
    ++st.ksets;
    xeKeSetEvent(&cs->header);
  }
}

using EnterFn = void (*)(X_RTL_CRITICAL_SECTION*, Stats&);
static EnterFn enter_for(int kind) {
  switch (kind) {
    case kOld: return &Enter<kOld>;
    case kOldGuest: return &Enter<kOldGuest>;
    case kIter: return &Enter<kIter>;
    case kTimeCas: return &Enter<kTimeCas>;
    default: return &Enter<kTime>;
  }
}

// ------------------------------------------------------------- harness -----
struct Variant {
  int kind = kOld;
  uint32_t param = 0;
  bool cvar_on = true;  // g_cvar_cs_spin while this variant runs
  std::string name;
};
static bool parse_variant(const std::string& s0, Variant& v) {
  v.name = s0;
  const std::string s = s0.substr(0, s0.find('#'));  // "old#aa": A/A control copy
  if (s == "old") {
    v.kind = kOld;
    v.param = 0;
    return true;
  }
  const size_t colon = s.find(':');
  if (colon == std::string::npos) return false;
  const std::string k = s.substr(0, colon);
  v.param = uint32_t(strtoul(s.c_str() + colon + 1, nullptr, 10));
  if (k == "oldg") v.kind = kOldGuest;
  else if (k == "iter") v.kind = kIter;
  else if (k == "time") v.kind = kTime;
  else if (k == "timecas") v.kind = kTimeCas;
  else if (k == "off") {
    v.kind = kTimeCas;
    v.cvar_on = false;
  } else return false;
  return true;
}
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
    if (!parse_variant(t, v)) {
      fprintf(stderr, "bad variant '%s'\n", t.c_str());
      exit(2);
    }
    out.push_back(v);
  }
  return out;
}
static void apply_variant(const Variant& v) {
  g_cvar_cs_spin = v.cvar_on;
  g_cvar_param = v.param;
  g_time_ticks = int64_t(double(v.param) * double(qpf()) / 1e9 + 0.5);
}

struct Aff {
  const char* name;
  DWORD_PTR m[2];
};
static const Aff kAffs[] = {
    {"none", {0, 0}},          // scheduler's choice
    {"pp", {0x3, 0xC}},        // P-core 0 (SMT pair) vs P-core 1
    {"ee", {0xF0, 0xF00}},     // E cluster 0 vs E cluster 1
    {"pe", {0xF, 0xFF0}},      // any P vs any E
};
static const Aff* find_aff(const std::string& n) {
  for (auto& a : kAffs)
    if (n == a.name) return &a;
  return nullptr;
}

struct alignas(64) Shared {
  X_RTL_CRITICAL_SECTION cs;
  char pad0[64 - sizeof(X_RTL_CRITICAL_SECTION)];
  volatile uint64_t counter;  // protected by cs, on its own line
  char pad1[56];
};
static Shared g_sh;
static std::atomic<int> g_ready{0};
static std::atomic<bool> g_go{false}, g_stop{false};

struct RunOut {
  double ns_op = 0, kw_M = 0, ks_M = 0, cpu_ns_op = 0, util = 0, util_gtt = 0;
  double spin_pct = 0, late_M = 0, fair = 0, to = 0;
  uint64_t ops = 0;
  bool excl_ok = true;
};

static RunOut run_contended(const Variant& v, const Aff& a, double hold_ns, double gap_ns,
                            int ms) {
  InitCS(&g_sh.cs);
  g_sh.counter = 0;
  apply_variant(v);
  const EnterFn enter = enter_for(v.kind);
  const uint64_t hold = ns_to_tsc(hold_ns), gap = ns_to_tsc(gap_ns);
  g_ready.store(0);
  g_go.store(false);
  g_stop.store(false);
  Stats st[2];
  auto body = [&](int idx) {
    if (a.m[idx]) SetThreadAffinityMask(GetCurrentThread(), a.m[idx]);
    t_guest_thread_object = 0x80070100u + 0x100u * uint32_t(idx);
    Stats s;
    g_ready.fetch_add(1);
    while (!g_go.load(std::memory_order_acquire)) _mm_pause();
    ULONG64 c0 = 0, c1 = 0;
    QueryThreadCycleTime(GetCurrentThread(), &c0);
    const uint64_t tt0 = thread_time_100ns();
    s.t_start = qpc();
    while (!g_stop.load(std::memory_order_relaxed)) {
      enter(&g_sh.cs, s);
      g_sh.counter = g_sh.counter + 1;
      busy_tsc(hold);
      Leave(&g_sh.cs, s);
      ++s.ops;
      busy_tsc(gap);
    }
    s.t_end = qpc();
    QueryThreadCycleTime(GetCurrentThread(), &c1);
    s.cycles = c1 - c0;
    s.thread_100ns = thread_time_100ns() - tt0;
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
  r.ops = st[0].ops + st[1].ops;
  const double wall_ns =
      ticks_ns(std::max(st[0].t_end, st[1].t_end) - std::min(st[0].t_start, st[1].t_start));
  const double ops = double(std::max<uint64_t>(r.ops, 1));
  r.ns_op = wall_ns / ops;
  r.kw_M = double(st[0].kwaits + st[1].kwaits) * 1e6 / ops;
  r.ks_M = double(st[0].ksets + st[1].ksets) * 1e6 / ops;
  const double cpu_ns = double(st[0].cycles + st[1].cycles) / g_tsc_per_ns;
  r.cpu_ns_op = cpu_ns / ops;
  r.util = cpu_ns / wall_ns;
  r.util_gtt = double(st[0].thread_100ns + st[1].thread_100ns) * 100.0 / wall_ns;
  const uint64_t fast = st[0].fast + st[1].fast;
  const uint64_t contended = r.ops > fast ? r.ops - fast : 0;
  r.spin_pct = contended ? 100.0 * double(st[0].spun + st[1].spun) / double(contended) : 0;
  r.late_M = double(st[0].late + st[1].late) * 1e6 / ops;
  r.fair = double(std::min(st[0].ops, st[1].ops)) / ops;
  r.to = double(st[0].timeouts + st[1].timeouts);
  r.excl_ok = (g_sh.counter == r.ops);
  return r;
}

static double run_uncontended(const Variant& v, DWORD_PTR mask, uint64_t pairs) {
  InitCS(&g_sh.cs);
  apply_variant(v);
  const EnterFn enter = enter_for(v.kind);
  double result = 0;
  std::thread t([&] {
    if (mask) SetThreadAffinityMask(GetCurrentThread(), mask);
    t_guest_thread_object = 0x80070100u;
    Stats s;
    for (int i = 0; i < 20000; ++i) {
      enter(&g_sh.cs, s);
      Leave(&g_sh.cs, s);
    }
    const int64_t t0 = qpc();
    for (uint64_t i = 0; i < pairs; ++i) {
      enter(&g_sh.cs, s);
      Leave(&g_sh.cs, s);
    }
    const int64_t t1 = qpc();
    result = ticks_ns(t1 - t0) / double(pairs);
    if (s.kwaits || s.ksets) printf("  !! uncontended run took kernel path\n");
  });
  t.join();
  return result;
}

// ---------------------------------------------------------------- info -----
static volatile int32_t g_probe = -1;
static volatile uint64_t g_sink = 0;

template <class F>
static double med_tsc_ns(int reps, int n, F f) {
  std::vector<double> v;
  for (int r = 0; r < reps; ++r) {
    const uint64_t a = __rdtsc();
    f(n);
    const uint64_t b = __rdtsc();
    v.push_back(double(b - a) / g_tsc_per_ns / n);
  }
  return median(v);
}

static void info_topology() {
  DWORD len = 0;
  GetLogicalProcessorInformationEx(RelationAll, nullptr, &len);
  std::vector<uint8_t> buf(len);
  auto* base = reinterpret_cast<PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX>(buf.data());
  if (!GetLogicalProcessorInformationEx(RelationAll, base, &len)) {
    printf("[topo] GetLogicalProcessorInformationEx failed %lu\n", GetLastError());
    return;
  }
  for (DWORD off = 0; off < len;) {
    auto* e = reinterpret_cast<PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX>(buf.data() + off);
    if (e->Relationship == RelationProcessorCore) {
      printf("[topo] core mask=0x%03llx efficiency_class=%u smt=%u\n",
             (unsigned long long)e->Processor.GroupMask[0].Mask, e->Processor.EfficiencyClass,
             (e->Processor.Flags & LTP_PC_SMT) ? 1u : 0u);
    } else if (e->Relationship == RelationCache && e->Cache.Level >= 2) {
      printf("[topo] L%u cache %lu KB mask=0x%03llx\n", e->Cache.Level,
             e->Cache.CacheSize / 1024, (unsigned long long)e->Cache.GroupMask.Mask);
    }
    off += e->Size;
  }
}

static void info_cpu(int cpu) {
  const DWORD_PTR old = SetThreadAffinityMask(GetCurrentThread(), DWORD_PTR(1) << cpu);
  Sleep(1);
  const DWORD on = GetCurrentProcessorNumber();
  const double pause = med_tsc_ns(15, 20000, [](int n) {
    for (int i = 0; i < n; ++i) _mm_pause();
  });
  const double pause_read = med_tsc_ns(15, 20000, [](int n) {
    uint64_t hits = 0;
    for (int i = 0; i < n; ++i) {
      _mm_pause();
      if (g_probe == -1) ++hits;
    }
    g_sink = hits;
  });
  const double q = med_tsc_ns(15, 20000, [](int n) {
    int64_t s = 0;
    for (int i = 0; i < n; ++i) s += qpc();
    g_sink = uint64_t(s);
  });
  const double r = med_tsc_ns(15, 20000, [](int n) {
    uint64_t s = 0;
    for (int i = 0; i < n; ++i) s += __rdtsc();
    g_sink = s;
  });
  const double y = med_tsc_ns(5, 2000, [](int n) {
    for (int i = 0; i < n; ++i) SwitchToThread();
  });
  printf("[cpu%-2d on=%-2lu] pause=%6.1f ns  pause+read=%6.1f ns  qpc=%5.1f ns  rdtsc=%5.1f ns  "
         "SwitchToThread=%7.0f ns  -> pauses per 1 us=%.0f\n",
         cpu, on, pause, pause_read, q, r, y, 1000.0 / pause_read);
  SetThreadAffinityMask(GetCurrentThread(), old);
}

static void mode_info() {
  print_timer_res("info");
  printf("[tsc] %.4f GHz  qpf=%lld\n", g_tsc_per_ns, (long long)qpf());
  info_topology();
  SYSTEM_INFO si;
  GetSystemInfo(&si);
  for (int cpu : {0, 1, 2, 4, 8, 11}) {
    if (cpu < int(si.dwNumberOfProcessors)) info_cpu(cpu);
  }
}

// ------------------------------------------------------------ uncontended --
static void mode_uncontended(int reps, uint64_t pairs, const std::vector<Variant>& vs) {
  struct Core {
    const char* name;
    DWORD_PTR mask;
  } cores[] = {{"P", 0xF}, {"E", 0xFF0}};
  std::vector<std::vector<double>> res(2 * vs.size());
  for (int rep = 0; rep < reps; ++rep)
    for (int c = 0; c < 2; ++c)
      for (size_t i = 0; i < vs.size(); ++i)
        res[c * vs.size() + i].push_back(run_uncontended(vs[i], cores[c].mask, pairs));
  printf("uncontended Enter+Leave pair, %llu pairs x %d reps (median [min..max] ns/pair)\n",
         (unsigned long long)pairs, reps);
  for (int c = 0; c < 2; ++c)
    for (size_t i = 0; i < vs.size(); ++i) {
      auto& v = res[c * vs.size() + i];
      printf("  core=%s  %-12s %6.2f [%6.2f .. %6.2f]\n", cores[c].name, vs[i].name.c_str(),
             median(v), vmin(v), vmax(v));
    }
}

// Paired version for a loaded machine: one pinned thread runs a batch of every
// variant back to back in each round (order rotated per round), so frequency
// drift and preemption hit all variants alike. Reports the median and p10 of
// per-batch ns/pair, and the median of the per-round difference to the first
// variant (the paired estimate of the change).
static void mode_uncontended_paired(int rounds, uint64_t batch, const std::vector<Variant>& vs) {
  struct Core {
    const char* name;
    DWORD_PTR mask;
  } cores[] = {{"P", 0xF}, {"E", 0xFF0}};
  printf("uncontended Enter+Leave pair, paired: %d rounds x %llu pairs per variant per core\n",
         rounds, (unsigned long long)batch);
  for (auto& core : cores) {
    std::vector<std::vector<double>> res(vs.size());
    std::thread t([&] {
      SetThreadAffinityMask(GetCurrentThread(), core.mask);
      t_guest_thread_object = 0x80070100u;
      InitCS(&g_sh.cs);
      Stats s;
      std::vector<EnterFn> fns;
      for (auto& v : vs) fns.push_back(enter_for(v.kind));
      for (size_t i = 0; i < vs.size(); ++i) {
        apply_variant(vs[i]);
        for (int k = 0; k < 20000; ++k) {
          fns[i](&g_sh.cs, s);
          Leave(&g_sh.cs, s);
        }
      }
      for (int r = 0; r < rounds; ++r) {
        for (size_t i0 = 0; i0 < vs.size(); ++i0) {
          const size_t i = (i0 + size_t(r)) % vs.size();
          apply_variant(vs[i]);
          const EnterFn fn = fns[i];
          const uint64_t a = __rdtsc();
          for (uint64_t k = 0; k < batch; ++k) {
            fn(&g_sh.cs, s);
            Leave(&g_sh.cs, s);
          }
          const uint64_t b = __rdtsc();
          res[i].push_back(double(b - a) / g_tsc_per_ns / double(batch));
        }
      }
      if (s.kwaits || s.ksets) printf("  !! uncontended run took kernel path\n");
    });
    t.join();
    for (size_t i = 0; i < vs.size(); ++i) {
      std::vector<double> d;
      for (size_t r = 0; r < res[i].size(); ++r) d.push_back(res[i][r] - res[0][r]);
      printf("  core=%s  %-12s median %6.2f  p10 %6.2f  p90 %6.2f ns/pair   paired diff vs %s: "
             "%+5.2f ns\n",
             core.name, vs[i].name.c_str(), median(res[i]), pct(res[i], 0.1), pct(res[i], 0.9),
             vs[0].name.c_str(), median(d));
    }
  }
}

// -------------------------------------------------------------- contended --
static void mode_contended(int reps, int ms, const std::vector<double>& holds,
                           const std::vector<Variant>& vs, const std::vector<const Aff*>& affs,
                           double gap_ns) {
  const size_t NV = vs.size(), NH = holds.size(), NA = affs.size();
  std::vector<std::vector<RunOut>> res(NA * NH * NV);
  bool excl_ok = true;
  for (int rep = 0; rep < reps; ++rep)
    for (size_t a = 0; a < NA; ++a)
      for (size_t h = 0; h < NH; ++h)
        for (size_t i = 0; i < NV; ++i) {
          RunOut r = run_contended(vs[i], *affs[a], holds[h], gap_ns, ms);
          excl_ok &= r.excl_ok;
          res[(a * NH + h) * NV + i].push_back(r);
        }
  printf("contended: 2 threads, %d ms x %d reps, gap %.0f ns. Medians; ns/op is wall time per "
         "acquire (both threads), cpu = QueryThreadCycleTime.\n",
         ms, reps, gap_ns);
  printf("%-4s %5s %-11s %9s %9s %9s %9s %9s %7s %6s %6s %7s %5s\n", "aff", "hold", "variant",
         "ns/op", "min", "max", "kwait/1M", "kset/1M", "cpu_ns/op", "util", "gtt", "spin%",
         "fair");
  for (size_t a = 0; a < NA; ++a)
    for (size_t h = 0; h < NH; ++h)
      for (size_t i = 0; i < NV; ++i) {
        auto& rr = res[(a * NH + h) * NV + i];
        auto col = [&](double RunOut::* m) {
          std::vector<double> v;
          for (auto& r : rr) v.push_back(r.*m);
          return v;
        };
        auto ns = col(&RunOut::ns_op);
        printf("%-4s %5.0f %-11s %9.1f %9.1f %9.1f %9.0f %9.0f %9.1f %7.2f %6.2f %6.1f %5.3f\n",
               affs[a]->name, holds[h], vs[i].name.c_str(), median(ns), vmin(ns), vmax(ns),
               median(col(&RunOut::kw_M)), median(col(&RunOut::ks_M)),
               median(col(&RunOut::cpu_ns_op)), median(col(&RunOut::util)),
               median(col(&RunOut::util_gtt)), median(col(&RunOut::spin_pct)),
               median(col(&RunOut::fair)));
      }
  printf("mutual exclusion check: %s\n", excl_ok ? "OK" : "VIOLATED");
}

int main(int argc, char** argv) {
  calibrate_tsc();
  g_kernel.event = CreateEventW(nullptr, FALSE, FALSE, nullptr);  // auto-reset
  print_power();
  const std::string mode = argc > 1 ? argv[1] : "info";
  if (mode == "info") {
    mode_info();
  } else if (mode == "uncontended") {
    const int reps = argc > 2 ? atoi(argv[2]) : 7;
    const uint64_t pairs = argc > 3 ? strtoull(argv[3], nullptr, 10) : 3000000ull;
    mode_uncontended(reps, pairs, parse_variants(argc > 4 ? argv[4] : "old,iter:64"));
  } else if (mode == "paired") {
    const int rounds = argc > 2 ? atoi(argv[2]) : 300;
    const uint64_t batch = argc > 3 ? strtoull(argv[3], nullptr, 10) : 20000ull;
    mode_uncontended_paired(rounds, batch, parse_variants(argc > 4 ? argv[4] : "old,iter:64"));
  } else if (mode == "contended") {
    const int reps = argc > 2 ? atoi(argv[2]) : 5;
    const int ms = argc > 3 ? atoi(argv[3]) : 100;
    std::vector<double> holds;
    for (auto& s : split(argc > 4 ? argv[4] : "50,500,5000")) holds.push_back(atof(s.c_str()));
    const auto vs = parse_variants(argc > 5 ? argv[5] : "old,iter:64,time:3000");
    std::vector<const Aff*> affs;
    for (auto& s : split(argc > 6 ? argv[6] : "none,pp,ee,pe")) {
      const Aff* a = find_aff(s);
      if (!a) {
        fprintf(stderr, "bad affinity '%s'\n", s.c_str());
        return 2;
      }
      affs.push_back(a);
    }
    const double gap = argc > 7 ? atof(argv[7]) : 200.0;
    mode_contended(reps, ms, holds, vs, affs, gap);
  } else {
    fprintf(stderr, "usage: bench_cs info | uncontended ... | contended ...\n");
    return 2;
  }
  printf("[cpu] process CPU time %.2f s\n", process_cpu_s());
  return 0;
}
