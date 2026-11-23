// timer_highres_check.cpp - (d2) are CREATE_WAITABLE_TIMER_HIGH_RESOLUTION timers safe for
// Win32Timer (APC completion routines, manual reset, absolute due times, periodic, cancel)?
// Prints PASS/FAIL per check. 1 thread. Usage: timer_highres_check.exe [runs=5]
#include "bench_common.h"
#include <mmsystem.h>
#include <cstdlib>
#pragma comment(lib, "winmm.lib")

using bench_a::summarize;
static int g_fail = 0;
static void verdict(bool pass, const char* what) {
  printf("%s  %s\n", pass ? "PASS" : "FAIL", what);
  if (!pass) ++g_fail;
}
static uint64_t ft_coarse() { FILETIME f; GetSystemTimeAsFileTime(&f); return bench_a::ft_u64(f); }   // SDK QueryHostSystemTime
static uint64_t ft_precise() { FILETIME f; GetSystemTimePreciseAsFileTime(&f); return bench_a::ft_u64(f); }
static HANDLE make_timer(bool hr, bool manual) {
  if (hr)
    return CreateWaitableTimerExW(nullptr, nullptr,
                                  CREATE_WAITABLE_TIMER_HIGH_RESOLUTION | (manual ? CREATE_WAITABLE_TIMER_MANUAL_RESET : 0),
                                  TIMER_ALL_ACCESS);
  return CreateWaitableTimerW(nullptr, manual, nullptr);
}
static bool arm(HANDLE t, int64_t due100ns, LONG period_ms = 0, PTIMERAPCROUTINE apc = nullptr, void* arg = nullptr) {
  LARGE_INTEGER d;
  d.QuadPart = due100ns;
  return SetWaitableTimer(t, &d, period_ms, apc, arg, FALSE) != 0;
}
static void hr_sleep_us(int64_t us) {  // helper wait that does not touch the timer under test
  static HANDLE h = make_timer(true, false);
  arm(h, -us * 10);
  WaitForSingleObject(h, INFINITE);
}

struct ApcCtx { int count = 0; void* arg = nullptr; int64_t q = 0; uint64_t ft = 0; };
static VOID CALLBACK OneApc(LPVOID a, DWORD lo, DWORD hi) {
  auto c = static_cast<ApcCtx*>(a);
  c->count++; c->arg = a; c->q = qpc(); c->ft = (uint64_t(hi) << 32) | lo;
}
struct PerCtx { int64_t t[160]; int n = 0; };
static VOID CALLBACK PerApc(LPVOID a, DWORD, DWORD) {
  auto c = static_cast<PerCtx*>(a);
  if (c->n < 160) c->t[c->n++] = qpc();
}
static VOID CALLBACK NoopApc(ULONG_PTR) {}

static void check_apc() {
  printf("\n-- 1. APC completion routine (absolute due = GetSystemTimeAsFileTime + 2 ms, as Win32Timer) --\n");
  for (int hr = 1; hr >= 0; --hr)
    for (int manual = 0; manual <= 1; ++manual) {
      HANDLE t = make_timer(hr, manual);
      int okA = 0, okB = 0, wic = 0, obj = 0, iters = 10;
      double lat = 0;
      for (int i = 0; i < iters; ++i) {
        ApcCtx c;  // A: alertable SleepEx (thread idles in an alertable wait)
        int64_t t0 = qpc();
        bool armed = arm(t, int64_t(ft_coarse() + 20000), 0, OneApc, &c);
        DWORD r = SleepEx(2000, TRUE);
        okA += armed && r == WAIT_IO_COMPLETION && c.count == 1 && c.arg == &c && c.ft != 0;
        lat += ticks_ms(c.q - t0);
        ApcCtx d;  // B: alertable wait on the timer itself
        armed = arm(t, int64_t(ft_coarse() + 20000), 0, OneApc, &d);
        r = WaitForSingleObjectEx(t, 2000, TRUE);
        wic += r == WAIT_IO_COMPLETION; obj += r == WAIT_OBJECT_0;
        if (d.count == 0) SleepEx(0, TRUE);  // APC may be pending if the wait returned WAIT_OBJECT_0
        okB += armed && (r == WAIT_OBJECT_0 || r == WAIT_IO_COMPLETION) && d.count == 1;
        if (manual) WaitForSingleObject(t, 0);
      }
      char buf[256];
      snprintf(buf, sizeof(buf), "%s %s timer: APC via SleepEx %d/%d (mean set->APC %.2f ms); "
               "APC via WFSOEx(timer) %d/%d (returned WAIT_IO_COMPLETION %d, WAIT_OBJECT_0 %d)",
               hr ? "high-res" : "normal", manual ? "manual-reset" : "sync", okA, iters, lat / iters, okB, iters, wic, obj);
      verdict(okA == iters && okB == iters, buf);
      CloseHandle(t);
    }
}

static void check_manual_reset() {
  printf("\n-- 2. CREATE_WAITABLE_TIMER_MANUAL_RESET | HIGH_RESOLUTION --\n");
  HANDLE m = make_timer(true, true), a = make_timer(true, false);
  verdict(m != nullptr, "CreateWaitableTimerExW(MANUAL_RESET|HIGH_RESOLUTION) succeeds");
  if (!m) return;
  arm(m, -20000);
  DWORD r1 = WaitForSingleObject(m, 1000), r2 = WaitForSingleObject(m, 0), r3 = WaitForSingleObject(m, 0);
  verdict(r1 == WAIT_OBJECT_0 && r2 == WAIT_OBJECT_0 && r3 == WAIT_OBJECT_0, "manual-reset high-res timer stays signaled after the wait");
  arm(a, -20000);
  DWORD a1 = WaitForSingleObject(a, 1000), a2 = WaitForSingleObject(a, 0);
  verdict(a1 == WAIT_OBJECT_0 && a2 == WAIT_TIMEOUT, "sync (auto-reset) high-res timer resets after one wait");
  arm(m, -50000);  // re-arm a signaled manual-reset timer
  DWORD r4 = WaitForSingleObject(m, 0);
  printf("INFO  re-arming a signaled manual-reset timer with SetWaitableTimer %s the signal (0 ms wait -> %s)\n",
         r4 == WAIT_TIMEOUT ? "clears" : "keeps", r4 == WAIT_TIMEOUT ? "timeout" : "signaled");
  CloseHandle(m); CloseHandle(a);
}

// 3. 2 ms one-shot error. mode 0 = relative, 1 = absolute from GetSystemTimeAsFileTime (SDK), 2 = absolute precise.
static const char* kMode[3] = {"relative", "abs coarse (SDK)", "abs precise"};
static std::vector<double> err_med[2][2][3], err_p90[2][2][3], err_min[2][2][3];  // [tbp][hr][mode]
static void oneshot_run(int tbp, int samples) {
  HANDLE t[2] = {make_timer(false, false), make_timer(true, false)};
  std::vector<double> e[2][3];
  for (int s = 0; s < samples; ++s)
    for (int hr = 0; hr < 2; ++hr)
      for (int m = 0; m < 3; ++m) {
        int64_t t0 = qpc();
        int64_t due = m == 0 ? -20000 : int64_t((m == 1 ? ft_coarse() : ft_precise()) + 20000);
        arm(t[hr], due);
        WaitForSingleObjectEx(t[hr], INFINITE, TRUE);
        e[hr][m].push_back(ticks_ms(qpc() - t0) - 2.0);
      }
  for (int hr = 0; hr < 2; ++hr)
    for (int m = 0; m < 3; ++m) {
      auto s = summarize(e[hr][m]);
      err_med[tbp][hr][m].push_back(s.med); err_p90[tbp][hr][m].push_back(s.p90);
      err_min[tbp][hr][m].push_back(vmin(e[hr][m]));
    }
  CloseHandle(t[0]); CloseHandle(t[1]);
}

// 4. 16 ms periodic, 100 periods, absolute due = precise now + 2 ms; high-res and normal armed together.
static std::vector<double> per_mean[2][2], per_j50[2][2], per_j99[2][2], per_first[2][2];
static void periodic_run(int tbp) {
  HANDLE t[2] = {make_timer(false, false), make_timer(true, false)};
  PerCtx c[2];
  int64_t t0 = qpc();
  uint64_t due = ft_precise() + 20000;
  for (int hr = 0; hr < 2; ++hr) arm(t[hr], int64_t(due), 16, PerApc, &c[hr]);
  while ((c[0].n < 101 || c[1].n < 101) && ticks_ms(qpc() - t0) < 10000) SleepEx(1000, TRUE);
  for (int hr = 0; hr < 2; ++hr) CancelWaitableTimer(t[hr]);
  SleepEx(0, TRUE);
  for (int hr = 0; hr < 2; ++hr) {
    std::vector<double> j;
    for (int i = 0; i < 100 && i + 1 < c[hr].n; ++i) j.push_back(std::fabs(ticks_ms(c[hr].t[i + 1] - c[hr].t[i]) - 16.0));
    int n = std::min(c[hr].n, 101);
    per_mean[tbp][hr].push_back(n > 1 ? ticks_ms(c[hr].t[n - 1] - c[hr].t[0]) / (n - 1) : NAN);
    auto s = summarize(j);
    per_j50[tbp][hr].push_back(s.med); per_j99[tbp][hr].push_back(s.p99);
    per_first[tbp][hr].push_back(n ? ticks_ms(c[hr].t[0] - t0) : NAN);
    CloseHandle(t[hr]);
  }
}

static void check_cancel() {
  printf("\n-- 5. CancelWaitableTimer after an alertable wait returned WAIT_IO_COMPLETION --\n");
  HANDLE t = make_timer(true, false);
  int wic = 0, clean = 0, iters = 20;
  for (int i = 0; i < iters; ++i) {  // 5a: cancel before the due time (AlertableSleepPrecise path)
    arm(t, -50000);  // 5 ms
    QueueUserAPC(NoopApc, GetCurrentThread(), 0);
    DWORD r = WaitForSingleObjectEx(t, INFINITE, TRUE);
    wic += r == WAIT_IO_COMPLETION;
    CancelWaitableTimer(t);
    hr_sleep_us(8000);  // past the original due time
    clean += WaitForSingleObject(t, 0) == WAIT_TIMEOUT;
  }
  char buf[200];
  snprintf(buf, sizeof(buf), "wait returned WAIT_IO_COMPLETION %d/%d; no stray signal after cancel %d/%d", wic, iters, clean, iters);
  verdict(wic == iters && clean == iters, buf);
  int stray = 0, cleared = 0;
  for (int i = 0; i < iters; ++i) {  // 5b: the timer fires between the APC wake-up and the cancel
    arm(t, -10000);  // 1 ms
    QueueUserAPC(NoopApc, GetCurrentThread(), 0);
    WaitForSingleObjectEx(t, INFINITE, TRUE);
    spin_ticks(qpf() * 3 / 1000);  // 3 ms busy: the timer expires meanwhile
    CancelWaitableTimer(t);
    stray += WaitForSingleObject(t, 0) == WAIT_OBJECT_0 ? 1 : 0;  // consumes the stray signal if present
    arm(t, -10000); hr_sleep_us(3000);  // let it fire -> signaled, nobody consumes it
    arm(t, -50000);                     // re-arm while signaled
    cleared += WaitForSingleObject(t, 0) == WAIT_TIMEOUT ? 1 : 0;
    CancelWaitableTimer(t);
    WaitForSingleObject(t, 0);
  }
  printf("INFO  late cancel (timer already expired) left a stray signal %d/%d times; "
         "SetWaitableTimer re-arm cleared a pending signal %d/%d times\n", stray, iters, cleared, iters);
  CloseHandle(t);
}

int main(int argc, char** argv) {
  int runs = argc > 1 ? atoi(argv[1]) : 5;
  setvbuf(stdout, nullptr, _IONBF, 0);
  printf("timer_highres_check: runs=%d QPF=%lld\n", runs, (long long)qpf());
  bench_a::print_machine_state("start");
  print_timer_res("start");
  check_apc();
  check_manual_reset();
  check_cancel();

  printf("\n-- 3/4. one-shot 2 ms error and 16 ms periodic, %d runs, timeBeginPeriod off/on alternating --\n", runs);
  for (int run = 0; run < runs; ++run)
    for (int tbp = 0; tbp < 2; ++tbp) {
      if (tbp) timeBeginPeriod(1);
      oneshot_run(tbp, 20);
      periodic_run(tbp);
      if (tbp) timeEndPeriod(1);
    }
  const char* kT[2] = {"normal", "high-res"};
  printf("\n3. 2 ms one-shot error (ms), median of %d run medians [median run p90] {min single sample}:\n", runs);
  for (int tbp = 0; tbp < 2; ++tbp)
    for (int hr = 1; hr >= 0; --hr)
      for (int m = 0; m < 3; ++m)
        printf("   tBP %-3s %-8s %-17s err med %+7.3f  [p90 %+7.3f]  {min %+7.3f}\n", tbp ? "on" : "off", kT[hr], kMode[m],
               median(err_med[tbp][hr][m]), median(err_p90[tbp][hr][m]), vmin(err_min[tbp][hr][m]));
  bool ok3 = true;
  for (int tbp = 0; tbp < 2; ++tbp)
    for (int m : {0, 2}) ok3 = ok3 && std::fabs(median(err_med[tbp][1][m])) < 0.5;
  verdict(ok3, "high-res 2 ms one-shot (relative and precise absolute): |median error| < 0.5 ms, tBP off and on");
  printf("\n4. 16 ms periodic (lPeriod=16, absolute due = precise now + 2 ms), medians over %d runs:\n", runs);
  for (int tbp = 0; tbp < 2; ++tbp)
    for (int hr = 1; hr >= 0; --hr)
      printf("   tBP %-3s %-8s mean period %7.3f ms  |period-16| p50 %6.3f p99 %6.3f ms  first tick after %6.3f ms\n",
             tbp ? "on" : "off", kT[hr], median(per_mean[tbp][hr]), median(per_j50[tbp][hr]), median(per_j99[tbp][hr]),
             median(per_first[tbp][hr]));
  bool ok4 = true;
  for (int tbp = 0; tbp < 2; ++tbp)
    ok4 = ok4 && std::fabs(median(per_mean[tbp][1]) - 16.0) < 0.2 && median(per_j50[tbp][1]) < 0.5;
  verdict(ok4, "high-res periodic: mean period within 0.2 ms of 16 ms and p50 jitter < 0.5 ms, tBP off and on");
  print_timer_res("end");
  printf("\n%s: %d failed check(s)\n", g_fail ? "SOME CHECKS FAILED" : "ALL CHECKS PASSED", g_fail);
  return g_fail ? 1 : 0;
}
