// bench_timerq.cpp - Agent 11, S3 task #10 lead: why rex::thread::TimerQueue uses 52-62% of a core
// (window 3, Agent 8's per-thread table), and the test bench for the staged fix.
//
// Links a timer_queue.cpp compiled next to this file, with bench/agent11/timerq_shim standing in for
// rex/assert.h, rex/thread.h, rex/cvar.h and rex/logging.h: the LIVE rexglue-sdk/src/core/
// timer_queue.cpp, unmodified, or (built with /DBENCH_STAGED) the staged copy in
// build/agent11/timerq/stage with the timer_queue_precise_wait cvar, for which this file also
// defines rex::thread::SleepPrecise the way the SDK's src/core/threading_win.cpp does.
// Drives it the way the game does: one recurring 1 ms timer whose callback stores a millisecond count,
// like the KeTimeStampBundle timer in src/kernel/xboxkrnl/xboxkrnl_module.cpp:195 (the only TimerQueue
// user on Windows).
//
// Environment: REX_TIMER_WAIT_BLOCKING (read at static init) picks the blocking wait. Staged builds
// only: TIMERQ_PRECISE=1 sets timer_queue_precise_wait before the first timer is queued (as startup
// does: cvars are applied before the kernel creates its timer), and TIMERQ_NO_HIRES=1 makes
// SleepPrecise take the SDK's fallback (no high-resolution timer, as before Windows 10 1803).
//
//   bench_timerq run <seconds> <timeBeginPeriod ms, 0 = none> [<process affinity mask, hex>]
//       Prints the timer thread's CPU (GetThreadTimes and QueryThreadCycleTime), callbacks/s and
//       the gaps between callbacks (how stale the guest tick count gets).
//   bench_timerq stress <count> [<spread ms, default 50>] [<1 ms timer: 1 = on (default), 0 = off>]
//       With the 1 ms timer running, queues <count> one-shot timers from this thread as fast as it
//       can, due 20 ms + i*spread/count from now. More than 512 overflows the ring, so QueueTimer
//       also waits for ring space (the claim wait and the consumer's notify). Checks that each fires
//       exactly once and none early; prints the lateness and the longest QueueTimer call.
//       With the 1 ms timer off, the queue waits for the one-shots alone, so deadlines more than
//       20 ms out (the condition-variable stretch of the precise wait) are exercised too.
//       Prints RESULT ok / RESULT FAIL; exit 1 on FAIL.
//   bench_timerq exit
//       Arms the 1 ms timer and a one-shot 60 s out, then returns from main without disarming: the
//       queue's static destructor must stop its thread mid-wait. The caller times the process.
//   bench_timerq spin [<rounds>]
//       Cost of one disruptorplus spin_wait busy phase (its first 10 spin_once calls, 4+8+...+2048 =
//       4092 _mm_pause, before the deadline is first checked) on each logical processor in turn,
//       plus sleep_for(1 ms) with and without timeBeginPeriod(1), and SwitchToThread.
//   bench_timerq classes
//       Prints the P-core and E-core affinity masks (EfficiencyClass from GetSystemCpuSetInformation).
// At most 2 threads: the timer thread and the main thread.
#include <windows.h>
#include <timeapi.h>
#include <intrin.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <string_view>
#include <thread>
#include <vector>

#include <disruptorplus/spin_wait.hpp>
#include <rex/thread/timer_queue.h>
#ifdef BENCH_STAGED
#include <rex/cvar.h>
REXCVAR_DECLARE(bool, timer_queue_precise_wait);
#endif

#pragma comment(lib, "winmm.lib")

namespace {
std::atomic<uint64_t> g_sleep_calls{0};  // SleepPrecise calls (staged builds)
}  // namespace

namespace rex::thread {
void set_current_thread_name(const std::string_view name) {
  std::wstring w(name.begin(), name.end());
  SetThreadDescription(GetCurrentThread(), w.c_str());
}

#ifdef BENCH_STAGED
// As src/core/threading_win.cpp: one high-resolution waitable timer per thread, created on first
// use; without one (before Windows 10 1803, or TIMERQ_NO_HIRES here) rex::thread::Sleep, which
// yields below 100 us and otherwise calls ::Sleep(whole ms), i.e. Sleep(0) below 1 ms.
namespace {
bool NoHiRes() {
  static const bool no_hires = std::getenv("TIMERQ_NO_HIRES") != nullptr;
  return no_hires;
}
struct ThreadSleepTimer {
  HANDLE handle = NoHiRes() ? nullptr
                            : CreateWaitableTimerExW(nullptr, nullptr,
                                                     CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,
                                                     TIMER_ALL_ACCESS);
  ThreadSleepTimer() = default;
  ThreadSleepTimer(const ThreadSleepTimer&) = delete;
  ThreadSleepTimer& operator=(const ThreadSleepTimer&) = delete;
  ~ThreadSleepTimer() {
    if (handle) CloseHandle(handle);
  }
};
HANDLE GetThreadSleepTimer() {
  thread_local ThreadSleepTimer timer;
  return timer.handle;
}
}  // namespace

void SleepPrecise(std::chrono::microseconds duration) {
  g_sleep_calls.fetch_add(1, std::memory_order_relaxed);
  HANDLE timer = GetThreadSleepTimer();
  LARGE_INTEGER due;
  due.QuadPart = -std::clamp<int64_t>(duration.count(), 0, INT64_MAX / 10) * 10;  // relative
  if (!timer || !SetWaitableTimer(timer, &due, 0, nullptr, nullptr, FALSE)) {
    if (duration.count() < 100) {
      SwitchToThread();
    } else {
      ::Sleep(DWORD(duration.count() / 1000));
    }
    return;
  }
  WaitForSingleObject(timer, INFINITE);
}
#endif
}  // namespace rex::thread

namespace {

using Clock = rex::thread::TimerQueueWaitItem::clock;

double QpcFreq() {
  LARGE_INTEGER f;
  QueryPerformanceFrequency(&f);
  return double(f.QuadPart);
}
int64_t Qpc() {
  LARGE_INTEGER c;
  QueryPerformanceCounter(&c);
  return c.QuadPart;
}
uint64_t Ft64(FILETIME f) { return (uint64_t(f.dwHighDateTime) << 32) | f.dwLowDateTime; }

// TSC ticks per second (QueryThreadCycleTime counts TSC ticks on current Windows).
double TscFreq() {
  const int64_t q0 = Qpc();
  const uint64_t t0 = __rdtsc();
  Sleep(200);
  const int64_t q1 = Qpc();
  const uint64_t t1 = __rdtsc();
  return double(t1 - t0) / (double(q1 - q0) / QpcFreq());
}

struct CpuSetInfo {
  std::vector<int> cls;  // efficiency class per logical processor
  DWORD_PTR p_mask = 0, e_mask = 0;
};
CpuSetInfo GetCpuSets() {
  CpuSetInfo info;
  ULONG len = 0;
  GetSystemCpuSetInformation(nullptr, 0, &len, GetCurrentProcess(), 0);
  std::vector<char> buf(len);
  auto* p = reinterpret_cast<SYSTEM_CPU_SET_INFORMATION*>(buf.data());
  if (!GetSystemCpuSetInformation(p, len, &len, GetCurrentProcess(), 0)) return info;
  int max_cls = 0;
  for (char* c = buf.data(); c < buf.data() + len;) {
    auto* s = reinterpret_cast<SYSTEM_CPU_SET_INFORMATION*>(c);
    if (s->Type == CpuSetInformation && s->CpuSet.Group == 0) {
      const int lp = s->CpuSet.LogicalProcessorIndex;
      if (lp >= int(info.cls.size())) info.cls.resize(lp + 1, -1);
      info.cls[lp] = s->CpuSet.EfficiencyClass;
      max_cls = std::max<int>(max_cls, s->CpuSet.EfficiencyClass);
    }
    c += s->Size;
  }
  for (size_t lp = 0; lp < info.cls.size() && lp < 64; ++lp) {
    if (info.cls[lp] < 0) continue;
    (info.cls[lp] == max_cls ? info.p_mask : info.e_mask) |= DWORD_PTR(1) << lp;
  }
  return info;
}

// Which wait the queue will use. Call before the first timer is queued: the staged code picks
// the precise wait on its first QueueTimer call.
struct ModeInfo {
  bool blocking = false, precise = false, no_hires = false;
  std::string label;
};
ModeInfo SelectMode() {
  ModeInfo m;
  m.blocking = std::getenv("REX_TIMER_WAIT_BLOCKING") != nullptr;
  const bool want_precise = std::getenv("TIMERQ_PRECISE") != nullptr;
#ifdef BENCH_STAGED
  m.label = "staged ";
  if (want_precise) {
    REXCVAR_SET(timer_queue_precise_wait, true);
    m.precise = true;
  }
  m.no_hires = std::getenv("TIMERQ_NO_HIRES") != nullptr;
#else
  m.label = "live ";
  if (want_precise) std::printf("note: TIMERQ_PRECISE ignored (the live code has no such cvar)\n");
#endif
  m.label += m.precise    ? "PRECISE (timer_queue_precise_wait)"
             : m.blocking ? "BLOCKING (REX_TIMER_WAIT_BLOCKING)"
                          : "SPIN (default)";
  if (m.precise && m.blocking) m.label += " + REX_TIMER_WAIT_BLOCKING";
  if (m.no_hires) m.label += " + TIMERQ_NO_HIRES";
  return m;
}

constexpr size_t kMaxStamps = size_t(1) << 22;
int64_t g_stamps[kMaxStamps];
std::atomic<size_t> g_count{0};
std::atomic<DWORD> g_tid{0};
volatile uint32_t g_tick;  // stands in for KeTimeStampBundle.TickCount

struct ThreadCpu {
  uint64_t user, kernel, cycles;  // 100 ns, 100 ns, TSC ticks
};
ThreadCpu GetThreadCpu(HANDLE h) {
  FILETIME c, e, k, u;
  GetThreadTimes(h, &c, &e, &k, &u);
  ULONG64 cyc = 0;
  QueryThreadCycleTime(h, &cyc);
  return {Ft64(u), Ft64(k), cyc};
}

double Pct(std::vector<double>& v, double q) {
  if (v.empty()) return 0;
  const size_t i = std::min(v.size() - 1, size_t(q * (v.size() - 1) + 0.5));
  return v[i];
}

int Run(int secs, int tbp, DWORD_PTR mask) {
  const ModeInfo m = SelectMode();
  if (mask && !SetProcessAffinityMask(GetCurrentProcess(), mask)) {
    std::printf("SetProcessAffinityMask(0x%llx) failed: %lu\n", (unsigned long long)mask,
                GetLastError());
    return 2;
  }
  if (tbp && timeBeginPeriod(UINT(tbp)) != TIMERR_NOERROR) {
    std::printf("timeBeginPeriod(%d) failed\n", tbp);
    return 2;
  }
  const double f = QpcFreq();
  const double tsc = TscFreq();
  const int64_t t0 = Qpc();
  auto item = rex::thread::QueueTimerRecurring(
      [t0, f](void*) {
        const int64_t now = Qpc();
        if (!g_tid.load(std::memory_order_relaxed)) g_tid.store(GetCurrentThreadId());
        g_tick = uint32_t(double(now - t0) * 1000.0 / f);
        const size_t i = g_count.fetch_add(1, std::memory_order_relaxed);
        if (i < kMaxStamps) g_stamps[i] = now;
      },
      nullptr, Clock::now(), std::chrono::milliseconds(1));
  Sleep(1000);  // warm-up
  const DWORD tid = g_tid.load();
  HANDLE th = tid ? OpenThread(THREAD_QUERY_LIMITED_INFORMATION, FALSE, tid) : nullptr;
  if (!th) {
    std::printf("no callback in the 1 s warm-up, or OpenThread failed (%lu)\n", GetLastError());
    return 2;
  }
  const size_t i0 = g_count.load();
  const uint64_t s0 = g_sleep_calls.load();
  const ThreadCpu c0 = GetThreadCpu(th);
  const int64_t q0 = Qpc();
  Sleep(DWORD(secs) * 1000);
  const size_t i1 = g_count.load();
  const uint64_t s1 = g_sleep_calls.load();
  const ThreadCpu c1 = GetThreadCpu(th);
  const int64_t q1 = Qpc();
  if (auto w = item.lock()) w->Disarm();

  const double wall = double(q1 - q0) / f;
  const double user = double(c1.user - c0.user) / 1e7, kernel = double(c1.kernel - c0.kernel) / 1e7;
  const double cyc = double(c1.cycles - c0.cycles) / tsc;
  std::vector<double> gaps;
  const size_t end = std::min(i1, kMaxStamps);
  for (size_t i = i0 + 1; i < end; ++i) gaps.push_back(double(g_stamps[i] - g_stamps[i - 1]) * 1000.0 / f);
  // Time the tick count spends more than 2 ms behind: a gap g leaves it stale for g - 2 ms.
  // Gaps under 0.5 ms are catch-up callbacks (occurrences that were already overdue).
  double stale = 0;
  int over2 = 0, over5 = 0, over10 = 0, burst = 0;
  for (double g : gaps) {
    if (g > 2) stale += g - 2, ++over2;
    if (g > 5) ++over5;
    if (g > 10) ++over10;
    if (g < 0.5) ++burst;
  }
  std::sort(gaps.begin(), gaps.end());
  std::printf(
      "mode %s  timeBeginPeriod %d  affinity 0x%llx  window %.2f s\n"
      "  timer thread CPU: %.1f%% of a core by GetThreadTimes (user %.1f%%, kernel %.1f%%), %.1f%% by "
      "cycles\n"
      "  callbacks: %.0f/s; gap ms p10 %.3f p50 %.3f p90 %.3f p99 %.3f max %.3f; gaps <0.5 ms %d, "
      ">2 ms %d, >5 ms %d, >10 ms %d; tick count >2 ms stale %.1f%% of the time\n",
      m.label.c_str(), tbp, (unsigned long long)mask, wall, 100 * (user + kernel) / wall,
      100 * user / wall, 100 * kernel / wall, 100 * cyc / wall, double(i1 - i0) / wall,
      Pct(gaps, 0.1), Pct(gaps, 0.5), Pct(gaps, 0.9), Pct(gaps, 0.99), gaps.empty() ? 0 : gaps.back(),
      burst, over2, over5, over10, 100 * (stale / 1000) / wall);
#ifdef BENCH_STAGED
  std::printf("  SleepPrecise calls: %.0f/s\n", double(s1 - s0) / wall);
#else
  (void)s0, (void)s1;
#endif
  CloseHandle(th);
  if (tbp) timeEndPeriod(UINT(tbp));
  return 0;
}

constexpr int kMaxStress = 100000;
int64_t g_late_ns[kMaxStress];
std::atomic<uint32_t> g_fires[kMaxStress];
std::atomic<int> g_fired{0};

int Stress(int count, int spread_ms, bool recurring) {
  if (count < 1 || count > kMaxStress || spread_ms < 0) {
    std::printf("stress: count 1..%d, spread >= 0 ms\n", kMaxStress);
    return 2;
  }
  const ModeInfo m = SelectMode();
  const double f = QpcFreq();
  std::weak_ptr<rex::thread::TimerQueueWaitItem> rec;
  if (recurring) {
    rec = rex::thread::QueueTimerRecurring([](void*) { g_tick = g_tick + 1; }, nullptr,
                                           Clock::now(), std::chrono::milliseconds(1));
  }
  Sleep(100);
  const auto t0 = Clock::now() + std::chrono::milliseconds(20);
  double longest_ms = 0;
  const int64_t qa = Qpc();
  for (int i = 0; i < count; ++i) {
    const auto due = t0 + std::chrono::microseconds(int64_t(spread_ms) * 1000 * i / count);
    const int64_t a = Qpc();
    rex::thread::QueueTimerOnce(
        [i, due](void*) {
          g_late_ns[i] =
              std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now() - due).count();
          g_fires[i].fetch_add(1, std::memory_order_relaxed);
          g_fired.fetch_add(1, std::memory_order_release);
        },
        nullptr, due);
    longest_ms = std::max(longest_ms, double(Qpc() - a) * 1000 / f);
  }
  const double queue_ms = double(Qpc() - qa) * 1000 / f;
  const auto give_up = t0 + std::chrono::milliseconds(spread_ms + 5000);
  while (g_fired.load(std::memory_order_acquire) < count && Clock::now() < give_up) Sleep(5);
  Sleep(50);  // a duplicate fire would land by now
  if (auto w = rec.lock()) w->Disarm();
  int fired = 0, missing = 0, twice = 0, early = 0;
  std::vector<double> late_ms;
  for (int i = 0; i < count; ++i) {
    const uint32_t n = g_fires[i].load(std::memory_order_acquire);
    if (n == 0) {
      ++missing;
      continue;
    }
    ++fired;
    if (n > 1) ++twice;
    if (g_late_ns[i] < 0) ++early;
    late_ms.push_back(double(g_late_ns[i]) / 1e6);
  }
  std::sort(late_ms.begin(), late_ms.end());
  const bool ok = missing == 0 && twice == 0 && early == 0;
  std::printf(
      "mode %s\n"
      "  stress: %d one-shots due over %d ms (from +20 ms) %s; queued in "
      "%.2f ms, longest QueueTimer call %.3f ms\n"
      "  fired %d, missing %d, fired twice %d, early %d; lateness ms p50 %.3f p90 %.3f p99 %.3f "
      "max %.3f\n"
      "  RESULT %s\n",
      m.label.c_str(), count, spread_ms,
      recurring ? "with the 1 ms timer running" : "with no other timer", queue_ms, longest_ms,
      fired, missing, twice, early,
      Pct(late_ms, 0.5), Pct(late_ms, 0.9), Pct(late_ms, 0.99), late_ms.empty() ? 0 : late_ms.back(),
      ok ? "ok" : "FAIL");
  return ok ? 0 : 1;
}

int Exit() {
  const ModeInfo m = SelectMode();
  rex::thread::QueueTimerRecurring([](void*) { g_tick = g_tick + 1; }, nullptr, Clock::now(),
                                   std::chrono::milliseconds(1));
  rex::thread::QueueTimerOnce([](void*) {}, nullptr, Clock::now() + std::chrono::seconds(60));
  Sleep(300);
  std::printf(
      "mode %s\n  exit: %u ticks in 300 ms; returning from main with both timers armed (the static "
      "TimerQueue must stop its thread)\n",
      m.label.c_str(), unsigned(g_tick));
  std::fflush(stdout);
  return 0;
}

int Spin(int rounds) {
  const CpuSetInfo cs = GetCpuSets();
  const double f = QpcFreq();
  for (size_t lp = 0; lp < cs.cls.size() && lp < 64; ++lp) {
    if (!SetThreadAffinityMask(GetCurrentThread(), DWORD_PTR(1) << lp)) continue;
    Sleep(1);  // move to that processor
    auto busy = [] {
      disruptorplus::spin_wait s;  // as in TimerWaitStrategy: fresh per wait
      for (int i = 0; i < 10; ++i) s.spin_once();
    };
    busy();
    std::vector<double> us;
    for (int r = 0; r < rounds; ++r) {
      const int64_t a = Qpc();
      busy();
      us.push_back(double(Qpc() - a) * 1e6 / f);
    }
    std::sort(us.begin(), us.end());
    std::printf("LP %2zu class %d: busy phase median %.1f us (%.1f ns per pause), min %.1f, max %.1f\n", lp,
                cs.cls[lp], Pct(us, 0.5), Pct(us, 0.5) * 1000 / 4092, us.front(), us.back());
  }
  SetThreadAffinityMask(GetCurrentThread(), cs.p_mask | cs.e_mask);
  for (int tbp : {0, 1}) {
    if (tbp) timeBeginPeriod(1);
    std::vector<double> ms;
    for (int i = 0; i < 40; ++i) {
      const int64_t a = Qpc();
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
      ms.push_back(double(Qpc() - a) * 1000 / f);
    }
    if (tbp) timeEndPeriod(1);
    std::sort(ms.begin(), ms.end());
    std::printf("sleep_for(1 ms), timeBeginPeriod %d: median %.2f ms, min %.2f, max %.2f\n", tbp,
                Pct(ms, 0.5), ms.front(), ms.back());
  }
  const int n = 100000;
  int switched = 0;
  const int64_t a = Qpc();
  for (int i = 0; i < n; ++i) switched += SwitchToThread() ? 1 : 0;
  std::printf("SwitchToThread: %.2f us per call, %d of %d switched\n", double(Qpc() - a) * 1e6 / f / n,
              switched, n);
  return 0;
}

}  // namespace

int main(int argc, char** argv) {
  const std::string mode = argc > 1 ? argv[1] : "";
  if (mode == "run" && argc >= 4) {
    return Run(std::atoi(argv[2]), std::atoi(argv[3]),
               argc > 4 ? DWORD_PTR(std::strtoull(argv[4], nullptr, 16)) : 0);
  }
  if (mode == "stress" && argc >= 3) {
    return Stress(std::atoi(argv[2]), argc > 3 ? std::atoi(argv[3]) : 50,
                  argc > 4 ? std::atoi(argv[4]) != 0 : true);
  }
  if (mode == "exit") return Exit();
  if (mode == "spin") return Spin(argc > 2 ? std::atoi(argv[2]) : 300);
  if (mode == "classes") {
    const CpuSetInfo cs = GetCpuSets();
    std::printf("P 0x%llx E 0x%llx\n", (unsigned long long)cs.p_mask, (unsigned long long)cs.e_mask);
    return 0;
  }
  std::printf(
      "usage: bench_timerq run <seconds> <tbp> [<mask hex>] | stress <count> [<spread ms>] [<1|0>] | "
      "exit | spin [<rounds>] | classes\n");
  return 2;
}
