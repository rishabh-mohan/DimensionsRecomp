// bench_sleep.cpp - (d) host sleep/wait latency, OLD (no timeBeginPeriod) vs NEW
// (timeBeginPeriod(1) + power-throttling timer-resolution opt-out), plus the guest-path model
// and SwitchToThread vs Sleep(0) cost. Max 1 thread. Usage: bench_sleep.exe [runs=5] [samples=40]
#include "bench_common.h"
#include <mmsystem.h>
#include <cstdlib>
#pragma comment(lib, "winmm.lib")

using bench_a::Summary;
using bench_a::summarize;

struct PptState {  // PROCESS_POWER_THROTTLING_STATE (own copy: SDK-version independent)
  ULONG Version, ControlMask, StateMask;
};
static constexpr int kProcessPowerThrottling = 4;  // PROCESS_INFORMATION_CLASS value
static constexpr ULONG kIgnoreTimerResolution = 0x4;  // PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION

static bool set_throttling(ULONG control, ULONG state, DWORD* err) {
  PptState s{1, control, state};
  BOOL ok = SetProcessInformation(GetCurrentProcess(), (PROCESS_INFORMATION_CLASS)kProcessPowerThrottling,
                                  &s, sizeof(s));
  *err = ok ? 0 : GetLastError();
  return ok != 0;
}

static HANDLE g_hr, g_nt, g_ev;
static void timer_wait(HANDLE t, int64_t us) {
  LARGE_INTEGER due;
  due.QuadPart = -us * 10;  // relative, 100 ns units (as SleepPrecise)
  SetWaitableTimer(t, &due, 0, nullptr, nullptr, FALSE);
  WaitForSingleObjectEx(t, INFINITE, TRUE);
}

struct Row { const char* name; void (*fn)(); };
static const Row kRows[] = {
    {"Sleep(1)", [] { Sleep(1); }},
    {"SleepEx(1,TRUE)", [] { SleepEx(1, TRUE); }},
    {"WFSOEx(ev,1,TRUE)", [] { WaitForSingleObjectEx(g_ev, 1, TRUE); }},
    {"WFSOEx(ev,1,FALSE)", [] { WaitForSingleObjectEx(g_ev, 1, FALSE); }},
    {"WFSOEx(ev,2,FALSE)", [] { WaitForSingleObjectEx(g_ev, 2, FALSE); }},
    {"HR timer 500us", [] { timer_wait(g_hr, 500); }},
    {"HR timer 1000us", [] { timer_wait(g_hr, 1000); }},
    {"HR timer 2000us", [] { timer_wait(g_hr, 2000); }},
    {"normal timer 1000us", [] { timer_wait(g_nt, 1000); }},
    {"SleepEx(0,TRUE)", [] { SleepEx(0, TRUE); }},
    {"SwitchToThread", [] { SwitchToThread(); }},
};
enum { kSleep1, kSleepEx1, kWfso1A, kWfso1, kWfso2, kHr500, kHr1000, kHr2000, kNt1000, kSleepEx0, kSwitch };
constexpr int kNumRows = int(sizeof(kRows) / sizeof(kRows[0]));

// res[phase][row] = per-run summaries (ms)
static std::vector<Summary> res[2][kNumRows];

static void measure_phase(int phase, int samples) {
  std::vector<double> v[kNumRows];
  for (int s = 0; s < samples; ++s)  // round-robin: rows interleaved sample by sample
    for (int r = 0; r < kNumRows; ++r) {
      int64_t t0 = qpc();
      kRows[r].fn();
      v[r].push_back(ticks_ms(qpc() - t0));
    }
  for (int r = 0; r < kNumRows; ++r) {
    Summary s = summarize(v[r]);
    res[phase][r].push_back(s);
    printf("  %-4s %-22s med %8.3f  p90 %8.3f  p99 %8.3f  max %8.3f ms  (n=%zu)\n", phase ? "NEW" : "OLD",
           kRows[r].name, s.med, s.p90, s.p99, s.max, s.n);
  }
}

static double med_of(const std::vector<Summary>& v, double Summary::*f) {
  std::vector<double> x;
  for (auto& s : v) x.push_back(s.*f);
  return median(x);
}
static double max_of(const std::vector<Summary>& v, double Summary::*f) {
  double m = 0;
  for (auto& s : v) m = std::max(m, s.*f);
  return m;
}
static double min_of(const std::vector<Summary>& v, double Summary::*f) {
  double m = 1e300;
  for (auto& s : v) m = std::min(m, s.*f);
  return m;
}

int main(int argc, char** argv) {
  int runs = argc > 1 ? atoi(argv[1]) : 5, samples = argc > 2 ? atoi(argv[2]) : 40;
  setvbuf(stdout, nullptr, _IONBF, 0);
  printf("bench_sleep: runs=%d samples/row/run=%d QPF=%lld\n", runs, samples, (long long)qpf());
  print_timer_res("start");
  g_hr = CreateWaitableTimerExW(nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_ALL_ACCESS);
  g_nt = CreateWaitableTimerW(nullptr, FALSE, nullptr);
  g_ev = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  printf("high-res timer create: %s (err %lu)\n", g_hr ? "OK" : "FAILED", g_hr ? 0 : GetLastError());
  if (!g_hr || !g_nt || !g_ev) return 1;

  std::vector<double> yield_sw, yield_s0, yield_frac;
  for (int run = 0; run < runs; ++run) {
    char tag[64];
    snprintf(tag, sizeof(tag), "run %d", run + 1);
    bench_a::print_machine_state(tag);
    print_timer_res("OLD phase (no timeBeginPeriod in effect)");
    measure_phase(0, samples);

    MMRESULT mm = timeBeginPeriod(1);
    DWORD err = 0;
    bool opt = set_throttling(kIgnoreTimerResolution, 0, &err);
    printf("timeBeginPeriod(1) = %u (%s); SetProcessInformation(IGNORE_TIMER_RESOLUTION opt-out) %s (err %lu)\n",
           mm, mm == TIMERR_NOERROR ? "ok" : "FAILED", opt ? "succeeded" : "FAILED", err);
    print_timer_res("after timeBeginPeriod(1)");
    measure_phase(1, samples);
    timeEndPeriod(1);
    set_throttling(0, 0, &err);  // back to system-managed
    print_timer_res("after timeEndPeriod(1)");

    // SwitchToThread vs Sleep(0): 200k calls each, 10 interleaved chunks of 20k.
    const int kChunk = 20000, kChunks = 10;
    int64_t tsw = 0, ts0 = 0, yielded = 0;
    for (int c = 0; c < kChunks; ++c) {
      int64_t t0 = qpc();
      for (int i = 0; i < kChunk; ++i) yielded += SwitchToThread() ? 1 : 0;
      int64_t t1 = qpc();
      for (int i = 0; i < kChunk; ++i) Sleep(0);
      int64_t t2 = qpc();
      tsw += t1 - t0;
      ts0 += t2 - t1;
    }
    double n = double(kChunk) * kChunks;
    yield_sw.push_back(ticks_ns(tsw) / n);
    yield_s0.push_back(ticks_ns(ts0) / n);
    yield_frac.push_back(double(yielded) / n);
    printf("  yield: SwitchToThread %.0f ns/call (%.1f%% actually yielded), Sleep(0) %.0f ns/call\n",
           yield_sw.back(), 100.0 * yield_frac.back(), yield_s0.back());
  }

  printf("\n== SUMMARY over %d runs: median of run medians | median of run p90s | max of run maxes | "
         "range of run medians (ms) ==\n", runs);
  for (int ph = 0; ph < 2; ++ph)
    for (int r = 0; r < kNumRows; ++r) {
      auto& v = res[ph][r];
      printf("%-4s %-22s med %8.3f | p90 %8.3f | max %8.3f | [%.3f .. %.3f]\n", ph ? "NEW" : "OLD", kRows[r].name,
             med_of(v, &Summary::med), med_of(v, &Summary::p90), max_of(v, &Summary::max),
             min_of(v, &Summary::med), max_of(v, &Summary::med));
    }
  printf("yield: SwitchToThread med %.0f ns/call (yielded %.1f%%), Sleep(0) med %.0f ns/call (200k calls/run)\n",
         median(yield_sw), 100.0 * median(yield_frac), median(yield_s0));

  struct G { const char* guest; int old_row; int new_row; };
  const G model[] = {
      {"Delay(-10000) non-alertable: OLD Sleep(1) | NEW HR 1000us", kSleep1, kHr1000},
      {"Delay(-10000) alertable: OLD SleepEx(1,TRUE) | NEW HR 1000us", kSleepEx1, kHr1000},
      {"Delay(-5000) alertable: OLD SleepEx(0,TRUE) | NEW HR 500us", kSleepEx0, kHr500},
      {"Delay(-5000) non-alertable: OLD SwitchToThread | NEW HR 500us", kSwitch, kHr500},
      {"wait timeout 1.5 ms: OLD WFSOEx(1 ms) | NEW WFSOEx(2 ms)", kWfso1, kWfso2},
  };
  printf("\n== GUEST-PATH MODEL (OLD rows from the OLD phase, NEW rows from the NEW phase) ==\n");
  for (auto& g : model)
    printf("%-64s OLD med %7.3f p90 %7.3f max %7.3f | NEW med %7.3f p90 %7.3f max %7.3f ms\n", g.guest,
           med_of(res[0][g.old_row], &Summary::med), med_of(res[0][g.old_row], &Summary::p90),
           max_of(res[0][g.old_row], &Summary::max), med_of(res[1][g.new_row], &Summary::med),
           med_of(res[1][g.new_row], &Summary::p90), max_of(res[1][g.new_row], &Summary::max));
  print_timer_res("end");
  return 0;
}
