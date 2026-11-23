// gpu_wait_backoff.cpp -- DRAFT by Agent 9 (task #32, 2026-11-22; N1-N4 of Agent 10's b2r S26 added in run-2
// task #11). Syntax-checked only (clang -fsyntax-only with devoffB's flags: syntax-*.txt beside the draft).
// NOT BUILT, NOT LINKED, NOT RUN.
// S4 item "GPU-wait spin back-off": perf-notes/agent9-codegen.md S5.2 (S4-DRAFT rows #24 stage 1, #25 stage 2).
// Target: DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp. That needs an S4 grant (Agent 1 / the user).
//
// What it does
//   The render thread spins in two guest loops while it waits for the command processor (CP):
//   - L1, fence wait: sub_83FBF7D0 calls the poll step sub_83FAF180 until block+0 = *(dev+11024)+0 has passed
//     fence r4. The poll step returns 0 if dev+11069 & 2 (GPU off); it stores a moved block+0 to waitctx+8.
//   - L2, query poll: sub_82BDCFB8 makes one GetData (sub_83FB09E8) try from lr 0x82BDD000, then, if the wait flag
//     is set, calls it back to back from lr 0x82BDD028 while it returns 1 (S_FALSE). No yield.
//   The hooks below pass through to the original (__imp__) and only delay the NEXT poll while the polled word has
//   not moved. They never write guest memory or guest registers. Neither loop counts polls or has a live timeout
//   (L1's timeout reads KTHREAD+0x58, which the SDK never writes; L2 has none). So only poll timing changes.
//
// Switches (environment, read once on first use)
//   LEGO_GPU_WAIT_BACKOFF_US=<Q>  unset or empty = OFF (default): every hook calls the original at once.
//                                 Q = 0: pause phase, then SwitchToThread on every later poll (Agent 6's (e)).
//                                 Q > 0: pause phase, one SwitchToThread, then a Q us sleep per poll. Max 2000.
//   LEGO_GPU_WAIT_SPIN_US=<S>     pause phase of a stalled wait before the first yield. Default 30, max 200.
//                                 Q and S take decimal digits only; a larger value clamps to the max. Anything
//                                 else ("-5", "+5", " 5", "5us") logs a warning and is ignored: Q stays OFF, S 30.
//   LEGO_GPU_WAIT_STATS=1         probe P1 counters (S4.1.4), one log line per 5 s. Works with the back-off OFF.
//                                 Profiling runs only; a STATS run never counts as a timing run.
//
// Build (DimensionsRecomp/rexlego/CMakeLists.txt), Xenos builds only. Before `if(WIN32)` / add_executable
// (:168), the same pattern as :150-152:
//        if(NOT LEGODIMENSIONS_NATIVE_GPU)
//            list(APPEND LEGODIMENSIONS_SOURCES src/gpu_wait_backoff.cpp)
//            set_property(SOURCE src/gpu_wait_backoff.cpp APPEND PROPERTY
//                COMPILE_DEFINITIONS LEGO_GPU_WAIT_HOOK_GETDATA=1)
//        endif()
//   Map check after the build (b2r S26 item 3): sub_83FBF7D0, sub_83FAF180, sub_83FB09E8 and sub_83FC0C10 (H0-H3)
//   all resolve to gpu_wait_backoff.cpp.obj, so devoffB's 27 hooked aliases become 31.
//   Native builds have nothing to save: the native device is never ring-initialised (dev+11024 stays 0), the hot
//   callers of sub_83FBF7D0 are hooked, and GetData is replaced (Agent 3, 07:34; build/agent3/logs/fe-11024.txt).
//   Native already defines sub_83FB09E8 (gpu_native/queries.cpp:320) and sub_83FC0C10 (hooks_device.cpp:340), so
//   H2 and H3 stay behind the define: a native build that includes this file by mistake still links (H0/H1 only).
//   No SDK change in stage 1. Stage 2 (WaitOnAddress on a CP sequence counter) is S5.2.3 and is not drafted here.
//
// Style checked against rexlego (07:45): the pch include and extern "C" __imp__ declarations as in
// native_lock_elide.cpp:3-37; guest loads use the pch's REX_LOAD_U32 / REX_LOAD_U8 (legodimensions_pch.h:120-129
// in generated/default, :124-133 in B's batch-nolr pch; same text, the macros the generated bodies use); the env
// switch is a magic static like native_lock_elide.cpp:40-46; <windows.h> without WIN32_LEAN_AND_MEAN (the SDK
// defines it, discord_presence.cpp:37-39); the high-resolution timer as in sample_profiler.cpp:70-71.
//
// Review: Agent 10 rated D176CA8D in b2r S26 (landing OFF SAFE once S5.2.4 step 0 is done; ON SAFE to test after
// steps 1-4). These were the review TODOs; b2r S26 answers all three as PASS:
//   - H2 reads ctx.lr at entry (crash_guards.cpp:69 reads it too): skip_lr must stay off (it is off in every build).
//   - Every L1 waiter gets the back-off, not only the render thread (BlockOnFence callers, S4.1.1). The same
//     output-identical argument holds for each; the stall state is per thread.
//   - Worst-case added latency per wait: one quantum Q after the word moves (half on average); the spin phase keeps
//     waits shorter than S at today's speed.

#if defined(_WIN32)

#include "legodimensions_pch.h"  // PPCContext, REX_LOAD_U8 / REX_LOAD_U32, <rex/logging.h>
#include <rex/hook.h>

#include <windows.h>
#include <immintrin.h>

#include <atomic>
#include <cstdint>
#include <cstdlib>

#ifndef LEGO_GPU_WAIT_HOOK_GETDATA
#define LEGO_GPU_WAIT_HOOK_GETDATA 0
#endif

extern "C" void __imp__sub_83FBF7D0(PPCContext& __restrict ctx, uint8_t* base);
extern "C" void __imp__sub_83FAF180(PPCContext& __restrict ctx, uint8_t* base);
#if LEGO_GPU_WAIT_HOOK_GETDATA
extern "C" void __imp__sub_83FB09E8(PPCContext& __restrict ctx, uint8_t* base);
extern "C" void __imp__sub_83FC0C10(PPCContext& __restrict ctx, uint8_t* base);
#endif

namespace {

// ---- Guest layout (A tree; perf-notes/agent9-codegen.md S4.1.1 and S5.2.1) ----
constexpr uint32_t kWaitDev = 0;            // waitctx+0 = dev (waitctx is on the guest stack, sub_83FAF088)
constexpr uint32_t kWaitLastSeen = 8;       // waitctx+8 = block+0 at the last poll (the poll step updates it)
constexpr uint32_t kDevFenceBlock = 11024;  // dev+11024 -> fence block; block+0 = last fence the GPU passed
constexpr uint32_t kDevFlags = 11069;       // byte; & 2 = GPU off: the poll step returns 0 and the wait ends
constexpr uint32_t kGpuOffBit = 0x02;
constexpr uint32_t kLrGetDataTry = 0x82BDD000u;   // sub_82BDCFB8: the one try (bl at 0x82BDCFFC)
constexpr uint32_t kLrGetDataLoop = 0x82BDD028u;  // sub_82BDCFB8: the blocking loop (bl at 0x82BDD024)
constexpr uint32_t kGetDataNotReady = 1;          // S_FALSE
constexpr uint32_t kTimerWaitCapMs = 20;          // safety bound on one timer wait (Q is at most 2 ms)

inline int64_t Qpc() {
  LARGE_INTEGER t;
  QueryPerformanceCounter(&t);
  return t.QuadPart;
}

// ---- Config ----
struct Config {
  bool on = false;          // LEGO_GPU_WAIT_BACKOFF_US is set and valid
  bool stats = false;       // LEGO_GPU_WAIT_STATS=1
  uint32_t quantum_us = 0;  // Q
  uint32_t spin_us = 30;    // S
  int64_t qpf = 1;          // QPC ticks per second
  int64_t spin_ticks = 0;
};

// Parses a decimal value; false if absent or invalid. Digits only (N1: strtoul alone takes "-5", wraps it and
// clamps it to max, so a stray sign would turn the back-off ON at Q = 2000). Clamps to max.
bool ParseUs(const char* s, uint32_t max, uint32_t* out) {
  if (!s || *s < '0' || *s > '9') return false;  // also rejects "", "+5" and " 5"
  char* end = nullptr;
  const unsigned long v = std::strtoul(s, &end, 10);  // saturates at ULONG_MAX, which then clamps to max
  if (end == s || *end != '\0') return false;
  *out = v > max ? max : static_cast<uint32_t>(v);
  return true;
}

const Config& Cfg() {
  // Magic static: read once, thread-safe, on the first hooked call (after logging is up).
  static const Config cfg = [] {
    Config c;
    const char* q = std::getenv("LEGO_GPU_WAIT_BACKOFF_US");
    c.on = ParseUs(q, 2000, &c.quantum_us);
    const char* sp = std::getenv("LEGO_GPU_WAIT_SPIN_US");
    uint32_t s = 0;
    const bool spin_ok = ParseUs(sp, 200, &s);
    if (spin_ok) c.spin_us = s;
    const char* st = std::getenv("LEGO_GPU_WAIT_STATS");
    c.stats = st && st[0] == '1';
    LARGE_INTEGER f;
    if (QueryPerformanceFrequency(&f) && f.QuadPart > 0) c.qpf = f.QuadPart;
    c.spin_ticks = c.qpf * c.spin_us / 1000000;
    if (q && *q && !c.on) {
      REXLOG_WARN("GPU wait back-off: LEGO_GPU_WAIT_BACKOFF_US=\"{}\" is not a plain number; back-off stays OFF.", q);
    }
    if (sp && *sp && !spin_ok) {
      REXLOG_WARN("GPU wait back-off: LEGO_GPU_WAIT_SPIN_US=\"{}\" is not a plain number; spin stays {} us.", sp,
                  c.spin_us);
    }
    if (c.on || c.stats) {
      REXLOG_INFO("GPU wait back-off: {} (quantum {} us, spin {} us); stats {}; GetData hook {}.",
                  c.on ? "ON" : "OFF", c.quantum_us, c.spin_us, c.stats ? "ON" : "OFF",
                  LEGO_GPU_WAIT_HOOK_GETDATA ? "built" : "not built (native GPU build)");
    }
    return c;
  }();
  return cfg;
}

// ---- Per-thread state ----
struct Stall {
  int64_t since = 0;     // QPC of the first poll that saw no movement (0 = not stalled)
  int64_t start = 0;     // L2 only, STATS only: QPC of the try
  bool yielded = false;  // Q > 0: the one SwitchToThread of this stall is done
  bool slept = false;    // the last back-off action was a sleep (latency-cost counters)
};

thread_local Stall t_l1;
thread_local Stall t_l2;

inline void Reset(Stall& st) {
  st.since = 0;
  st.yielded = false;
  st.slept = false;
}

struct ThreadTimer {
  HANDLE h = nullptr;
  bool failed = false;
  ~ThreadTimer() {
    if (h) CloseHandle(h);
  }
};

thread_local ThreadTimer t_timer;

// High-resolution relative sleep. Never falls back to Sleep(1) (1-15.6 ms): on failure the caller yields instead.
bool SleepUs(uint32_t us) {
  if (!t_timer.h && !t_timer.failed) {
    t_timer.h = CreateWaitableTimerExW(nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,
                                       TIMER_MODIFY_STATE | SYNCHRONIZE);
    if (!t_timer.h) t_timer.failed = true;
  }
  if (!t_timer.h) return false;
  LARGE_INTEGER due;
  due.QuadPart = -static_cast<LONGLONG>(us) * 10;  // relative, in 100 ns units
  return SetWaitableTimer(t_timer.h, &due, 0, nullptr, nullptr, FALSE) &&
         WaitForSingleObject(t_timer.h, kTimerWaitCapMs) == WAIT_OBJECT_0;
}

// ---- Stats (probe P1; relaxed atomics; only touched when LEGO_GPU_WAIT_STATS=1) ----
struct Stats {
  std::atomic<uint64_t> l1_waits{0}, l1_polls{0}, l1_moved{0}, l1_gpu_off{0};
  std::atomic<uint64_t> l1_sleep_then_moved{0}, l1_sleep_then_done{0};
  std::atomic<uint64_t> l2_tries{0}, l2_polls{0}, l2_delayed{0}, l2_waits{0}, l2_sleep_then_ready{0};
  std::atomic<uint64_t> kicks{0};
  std::atomic<uint64_t> pauses{0}, yields{0}, sleeps{0}, sleep_fails{0};
  std::atomic<uint64_t> sleep_ticks{0};  // N4: QPC ticks inside SleepUs, failed tries included
  std::atomic<uint64_t> l1_ticks{0}, l1_max_ticks{0}, l2_ticks{0}, l2_max_ticks{0};
  std::atomic<uint64_t> hist[5] = {};  // L1 wait time: <50 us, <200 us, <1 ms, <4 ms, >= 4 ms
  std::atomic<int64_t> next_log{0};
};

Stats g_stats;

inline void Inc(std::atomic<uint64_t>& a, uint64_t n = 1) { a.fetch_add(n, std::memory_order_relaxed); }

inline uint64_t Take(std::atomic<uint64_t>& a) { return a.exchange(0, std::memory_order_relaxed); }

inline void Max(std::atomic<uint64_t>& a, uint64_t v) {
  uint64_t cur = a.load(std::memory_order_relaxed);
  while (v > cur && !a.compare_exchange_weak(cur, v, std::memory_order_relaxed)) {
  }
}

void AddL1Wait(const Config& c, int64_t ticks) {
  const uint64_t t = ticks > 0 ? static_cast<uint64_t>(ticks) : 0;
  Inc(g_stats.l1_ticks, t);
  Max(g_stats.l1_max_ticks, t);
  const uint64_t us = t * 1000000 / static_cast<uint64_t>(c.qpf);
  const int bin = us < 50 ? 0 : us < 200 ? 1 : us < 1000 ? 2 : us < 4000 ? 3 : 4;
  Inc(g_stats.hist[bin]);
}

double TicksToMs(const Config& c, uint64_t t) { return static_cast<double>(t) * 1000.0 / static_cast<double>(c.qpf); }

// One line per 5 s; each line covers one interval (counters are taken and cleared). Per-frame numbers: divide by
// the frames in the same interval from the runner's perf.csv. sleep_sum = time spent in sleeps (N4).
void MaybeLog(const Config& c) {
  const int64_t now = Qpc();
  int64_t next = g_stats.next_log.load(std::memory_order_relaxed);
  if (next != 0 && now < next) return;
  if (!g_stats.next_log.compare_exchange_strong(next, now + 5 * c.qpf, std::memory_order_relaxed)) return;
  if (next == 0) return;  // first call only arms the interval
  const uint64_t w1 = Take(g_stats.l1_waits), w2 = Take(g_stats.l2_waits);
  REXLOG_INFO(
      "GPU wait stats (5 s): L1 waits {} polls {} moved {} gpu_off {} sleep>moved {} sleep>done {} | "
      "L2 tries {} waits {} polls {} delayed {} sleep>ready {} | kicks {} | pause {} yield {} sleep {} "
      "sleep_sum {:.2f} ms sleep_fail {} | L1 sum {:.2f} ms max {:.3f} ms hist <50us {} <200us {} <1ms {} "
      "<4ms {} >=4ms {} | L2 sum {:.2f} ms max {:.3f} ms",
      w1, Take(g_stats.l1_polls), Take(g_stats.l1_moved), Take(g_stats.l1_gpu_off),
      Take(g_stats.l1_sleep_then_moved), Take(g_stats.l1_sleep_then_done), Take(g_stats.l2_tries), w2,
      Take(g_stats.l2_polls), Take(g_stats.l2_delayed), Take(g_stats.l2_sleep_then_ready), Take(g_stats.kicks),
      Take(g_stats.pauses), Take(g_stats.yields), Take(g_stats.sleeps), TicksToMs(c, Take(g_stats.sleep_ticks)),
      Take(g_stats.sleep_fails), TicksToMs(c, Take(g_stats.l1_ticks)), TicksToMs(c, Take(g_stats.l1_max_ticks)),
      Take(g_stats.hist[0]), Take(g_stats.hist[1]), Take(g_stats.hist[2]), Take(g_stats.hist[3]),
      Take(g_stats.hist[4]), TicksToMs(c, Take(g_stats.l2_ticks)), TicksToMs(c, Take(g_stats.l2_max_ticks)));
}

enum class Action : uint8_t { kPause, kYield, kSleep, kSleepFailed };

// One back-off step for a poll that saw no movement. Stall time t = now - since:
//   t < S: 32 x _mm_pause (about 1-2.5 us at 1.9 GHz); then SwitchToThread (every poll if Q = 0, else once);
//   then a Q us high-resolution sleep per poll (a failed timer yields instead).
Action BackOff(Stall& st, const Config& c) {
  const int64_t now = Qpc();
  if (st.since == 0) st.since = now;
  Action a;
  if (now - st.since < c.spin_ticks) {
    for (int i = 0; i < 32; ++i) _mm_pause();
    a = Action::kPause;
  } else if (c.quantum_us == 0 || !st.yielded) {
    st.yielded = true;
    SwitchToThread();
    a = Action::kYield;
  } else {
    const int64_t s0 = c.stats ? Qpc() : 0;
    const bool ok = SleepUs(c.quantum_us);
    if (c.stats) {
      const int64_t d = Qpc() - s0;
      Inc(g_stats.sleep_ticks, d > 0 ? static_cast<uint64_t>(d) : 0);
    }
    if (ok) {
      a = Action::kSleep;
    } else {
      SwitchToThread();
      a = Action::kSleepFailed;
    }
  }
  st.slept = (a == Action::kSleep);
  if (c.stats) {
    switch (a) {
      case Action::kPause: Inc(g_stats.pauses); break;
      case Action::kYield: Inc(g_stats.yields); break;
      case Action::kSleep: Inc(g_stats.sleeps); break;
      case Action::kSleepFailed: Inc(g_stats.sleep_fails); break;
    }
  }
  return a;
}

}  // namespace

// ---- H0: start of each L1 wait (sub_83FBF7D0; r3 = dev, r4 = fence). ----
// waitctx sits on the guest stack, so back-to-back waits can reuse its address: a new wait is detected here.
REX_HOOK_RAW(sub_83FBF7D0) {
  const Config& c = Cfg();
  if (!c.on && !c.stats) {
    __imp__sub_83FBF7D0(ctx, base);
    return;
  }
  Reset(t_l1);
  const int64_t t0 = c.stats ? Qpc() : 0;
  __imp__sub_83FBF7D0(ctx, base);
  if (c.stats) {
    Inc(g_stats.l1_waits);
    if (t_l1.slept) Inc(g_stats.l1_sleep_then_done);  // the fence passed during the last sleep
    AddL1Wait(c, Qpc() - t0);
    MaybeLog(c);
  }
  Reset(t_l1);
}

// ---- H1: L1 poll step (sub_83FAF180; r3 = waitctx). The caller tests completion before every poll. ----
REX_HOOK_RAW(sub_83FAF180) {
  const Config& c = Cfg();
  if (!c.on && !c.stats) {
    __imp__sub_83FAF180(ctx, base);
    return;
  }
  const uint32_t wc = ctx.r3.u32;
  // Guest reads only, with the pch macros (they use this hook's `base`).
  const uint32_t dev = REX_LOAD_U32(wc + kWaitDev);
  if (c.stats) Inc(g_stats.l1_polls);
  // Same read order as the original: the GPU-off flag first, then the fence block.
  if (REX_LOAD_U8(dev + kDevFlags) & kGpuOffBit) {
    if (c.stats) Inc(g_stats.l1_gpu_off);
    Reset(t_l1);
  } else {
    const uint32_t block = REX_LOAD_U32(dev + kDevFenceBlock);
    if (REX_LOAD_U32(block) != REX_LOAD_U32(wc + kWaitLastSeen)) {
      // The fence word moved since the last poll: never delay this poll (Agent 6's check).
      if (c.stats) {
        Inc(g_stats.l1_moved);
        if (t_l1.slept) Inc(g_stats.l1_sleep_then_moved);
      }
      Reset(t_l1);
    } else if (c.on) {
      BackOff(t_l1, c);
    }
  }
  __imp__sub_83FAF180(ctx, base);
}

#if LEGO_GPU_WAIT_HOOK_GETDATA
// ---- H2: L2 poll (GetData sub_83FB09E8; one static caller, sub_82BDCFB8). Xenos builds only. ----
// The back-off runs AFTER the original returned S_FALSE, so a kick done inside GetData (q+24 == dev+11036) has
// already happened: the loop never waits on an unsubmitted fence.
REX_HOOK_RAW(sub_83FB09E8) {
  const Config& c = Cfg();
  if (!c.on && !c.stats) {
    __imp__sub_83FB09E8(ctx, base);
    return;
  }
  const uint32_t lr = static_cast<uint32_t>(ctx.lr);  // the caller's return address, saved before the call
  __imp__sub_83FB09E8(ctx, base);
  const uint32_t hr = ctx.r3.u32;
  if (lr == kLrGetDataTry) {
    Reset(t_l2);
    if (c.stats) {
      Inc(g_stats.l2_tries);
      t_l2.start = Qpc();
    }
    return;
  }
  if (lr != kLrGetDataLoop) return;  // no other caller is known; pass through untouched
  if (c.stats) Inc(g_stats.l2_polls);
  if (hr != kGetDataNotReady) {
    if (c.stats) {
      Inc(g_stats.l2_waits);
      if (t_l2.slept) Inc(g_stats.l2_sleep_then_ready);
      const int64_t t = Qpc() - t_l2.start;
      const uint64_t ticks = t > 0 ? static_cast<uint64_t>(t) : 0;
      Inc(g_stats.l2_ticks, ticks);
      Max(g_stats.l2_max_ticks, ticks);
      MaybeLog(c);
    }
    Reset(t_l2);
    return;
  }
  if (c.on) {
    BackOff(t_l2, c);
    if (c.stats) Inc(g_stats.l2_delayed);
  }
}

// ---- H3: kick counter (sub_83FC0C10), STATS only, never delays. Xenos builds only (P1, S4.1.4). ----
REX_HOOK_RAW(sub_83FC0C10) {
  if (Cfg().stats) Inc(g_stats.kicks);
  __imp__sub_83FC0C10(ctx, base);
}
#endif  // LEGO_GPU_WAIT_HOOK_GETDATA

#endif  // _WIN32
