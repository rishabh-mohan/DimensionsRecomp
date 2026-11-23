// Agent 7 (task #6) microbenchmarks for the present-path edits. One thread, no GPU, no game.
//   1. Cost of the per-present Win32 queries that edit (c) moved out from under g_mutex.
//   2. Lateness of the high-resolution waitable timer (sizes the 2 ms PaceFrameBeforeLock
//      margin and explains the limiter's 0.5 ms spin window).
//   3. Pacing simulation with verbatim copies of the production LimitFrameRate,
//      PublishFramePace and HostDevice::PaceFrameBeforeLock (device.cpp): old path vs
//      LEGO_NATIVE_UNLOCKED_PACING, plus the published-deadline gap (never negative).
//      Same deadlines? How long is the recording gate held per frame?
// Build and run: python bench/agent7/run_microbench.py   (clang++ from env/devshell.ps1)
#define NOMINMAX
#include <windows.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#pragma comment(lib, "user32.lib")

using clk = std::chrono::steady_clock;

namespace {

double Us(clk::duration d) { return std::chrono::duration<double, std::micro>(d).count(); }

double Percentile(std::vector<double> v, double p) {
  if (v.empty()) return 0;
  std::sort(v.begin(), v.end());
  return v[size_t(std::lround(p * double(v.size() - 1)))];
}

double Mean(const std::vector<double>& v) {
  double s = 0;
  for (double x : v) s += x;
  return v.empty() ? 0 : s / double(v.size());
}

double Stddev(const std::vector<double>& v) {
  const double m = Mean(v);
  double s = 0;
  for (double x : v) s += (x - m) * (x - m);
  return v.size() < 2 ? 0 : std::sqrt(s / double(v.size() - 1));
}

void BusyFor(double us) {
  const auto end = clk::now() + std::chrono::duration_cast<clk::duration>(
                                    std::chrono::duration<double, std::micro>(us));
  while (clk::now() < end) {
  }
}

// ---- 1. Win32 queries ---------------------------------------------------------------------
void BenchWin32Queries(HWND hwnd) {
  constexpr int kRuns = 7, kIters = 20000;
  volatile LONG_PTR sink = 0;
  std::vector<double> all, fg, style, mon;
  for (int r = 0; r < kRuns; ++r) {
    auto t0 = clk::now();
    for (int i = 0; i < kIters; ++i) {
      // Exactly the per-present block in PresentTexture.
      const bool focused = GetForegroundWindow() == hwnd;
      const bool borderless = (GetWindowLongPtrW(hwnd, GWL_STYLE) & WS_POPUP) != 0;
      const HMONITOR monitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST);
      sink = sink + LONG_PTR(focused) + LONG_PTR(borderless) + reinterpret_cast<LONG_PTR>(monitor);
    }
    all.push_back(Us(clk::now() - t0) * 1000.0 / kIters);
    t0 = clk::now();
    for (int i = 0; i < kIters; ++i) sink = sink + reinterpret_cast<LONG_PTR>(GetForegroundWindow());
    fg.push_back(Us(clk::now() - t0) * 1000.0 / kIters);
    t0 = clk::now();
    for (int i = 0; i < kIters; ++i) sink = sink + GetWindowLongPtrW(hwnd, GWL_STYLE);
    style.push_back(Us(clk::now() - t0) * 1000.0 / kIters);
    t0 = clk::now();
    for (int i = 0; i < kIters; ++i)
      sink = sink + reinterpret_cast<LONG_PTR>(MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST));
    mon.push_back(Us(clk::now() - t0) * 1000.0 / kIters);
  }
  std::printf("[win32] %d runs x %d iterations, ns per call: median (min..max)\n", kRuns, kIters);
  auto row = [](const char* name, const std::vector<double>& v) {
    std::printf("[win32]   %-34s %8.1f (%7.1f..%7.1f)\n", name, Percentile(v, 0.5),
                *std::min_element(v.begin(), v.end()), *std::max_element(v.begin(), v.end()));
  };
  row("all three (per present)", all);
  row("GetForegroundWindow", fg);
  row("GetWindowLongPtrW(GWL_STYLE)", style);
  row("MonitorFromWindow", mon);
}

// ---- 2. Timer lateness --------------------------------------------------------------------
void BenchTimer() {
  HANDLE timer = CreateWaitableTimerExW(nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,
                                        TIMER_ALL_ACCESS);
  if (!timer) {
    std::printf("[timer] CREATE_WAITABLE_TIMER_HIGH_RESOLUTION unavailable\n");
    return;
  }
  constexpr int kRuns = 5, kSamples = 200;
  std::printf("[timer] high-resolution waitable timer, %d runs x %d samples; lateness in us\n",
              kRuns, kSamples);
  std::printf("[timer]   request  median    p95     p99   p99.9     max   run-medians\n");
  for (const int request_us : {500, 1000, 1500, 3500}) {
    std::vector<double> late, run_medians;
    for (int r = 0; r < kRuns; ++r) {
      std::vector<double> run;
      for (int i = 0; i < kSamples; ++i) {
        const auto t0 = clk::now();
        LARGE_INTEGER due;
        due.QuadPart = -int64_t(request_us) * 10;
        if (SetWaitableTimer(timer, &due, 0, nullptr, nullptr, FALSE)) WaitForSingleObject(timer, INFINITE);
        run.push_back(Us(clk::now() - t0) - request_us);
      }
      run_medians.push_back(Percentile(run, 0.5));
      late.insert(late.end(), run.begin(), run.end());
    }
    std::printf("[timer]   %5d   %6.1f  %6.1f  %6.1f  %6.1f  %6.1f  ", request_us, Percentile(late, 0.5),
                Percentile(late, 0.95), Percentile(late, 0.99), Percentile(late, 0.999),
                Percentile(late, 1.0));
    for (double m : run_medians) std::printf(" %.1f", m);
    std::printf("\n");
  }
  CloseHandle(timer);
}

// ---- 3. Pacing simulation -----------------------------------------------------------------
// Verbatim from device.cpp except: state lives in structs (reset per run) and the spin
// is timed. Keep in sync with LimitFrameRate / PublishFramePace /
// HostDevice::PaceFrameBeforeLock.
std::atomic<int64_t> g_pace_next{0};
std::atomic<int32_t> g_pace_limit{0};

struct Limiter {
  clk::time_point next = clk::now();
  int32_t previous_limit = -1;
  HANDLE timer = CreateWaitableTimerExW(nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,
                                        TIMER_ALL_ACCESS);
  double spin_us = 0;
  ~Limiter() {
    if (timer) CloseHandle(timer);
  }
  void LimitFrameRate(int32_t limit) {
    using clock = clk;
    if (previous_limit != limit) { next = clock::now(); previous_limit = limit; }
    if (limit <= 0) return;
    const auto period = std::chrono::duration_cast<clock::duration>(
        std::chrono::duration<double>(1.0 / limit));
    auto now = clock::now();
    if (next > now) {
      const auto sleep_for = next - now - std::chrono::microseconds(500);
      if (timer && sleep_for > clock::duration::zero()) {
        LARGE_INTEGER due;
        due.QuadPart = -std::chrono::duration_cast<std::chrono::nanoseconds>(sleep_for).count() / 100;
        if (SetWaitableTimer(timer, &due, 0, nullptr, nullptr, FALSE))
          WaitForSingleObject(timer, INFINITE);
      }
      const auto spin_start = clock::now();
      while (clock::now() < next) YieldProcessor();
      spin_us += Us(clock::now() - spin_start);
      now = next;
    }
    next = (std::max)(next + period, now);
  }
};

struct PacePublisher {  // PublishFramePace
  clk::time_point next;
  int32_t previous_limit = -1;
  void Publish(int32_t limit, clk::time_point entered) {
    using clock = clk;
    if (previous_limit != limit) { next = entered; previous_limit = limit; }
    g_pace_limit.store(limit, std::memory_order_relaxed);
    if (limit <= 0) return;
    const auto period = std::chrono::duration_cast<clock::duration>(
        std::chrono::duration<double>(1.0 / limit));
    next = (std::max)(next + period, entered);
    g_pace_next.store(next.time_since_epoch().count(), std::memory_order_release);
  }
};

void PaceFrameBeforeLock(int64_t margin_us) {
  if (!margin_us || g_pace_limit.load(std::memory_order_relaxed) <= 0) return;
  using clock = clk;
  const auto wake = clock::time_point(clock::duration(g_pace_next.load(std::memory_order_acquire))) -
                    std::chrono::microseconds(margin_us);
  const auto now = clock::now();
  if (wake <= now) return;
  const auto sleep_for = (std::min)(wake - now, clock::duration(std::chrono::seconds(1)));
  static thread_local HANDLE timer = CreateWaitableTimerExW(nullptr, nullptr,
      CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_ALL_ACCESS);
  LARGE_INTEGER due;
  due.QuadPart = -std::chrono::duration_cast<std::chrono::nanoseconds>(sleep_for).count() / 100;
  if (timer && SetWaitableTimer(timer, &due, 0, nullptr, nullptr, FALSE))
    WaitForSingleObject(timer, INFINITE);
}

struct PacingResult {
  std::vector<double> interval_us, late_us, held_us;
  std::vector<double> publish_gap_us;  // LimitFrameRate next - PublishFramePace next
  double spin_us_per_frame = 0;
};

// Per frame: guest work outside the gate, [pre-lock pacing], gate taken, work under the
// gate before PresentTexture (temporal/resolve), LimitFrameRate, present, post-present
// work under the gate, gate released.
PacingResult SimulatePacing(int32_t limit, int64_t margin_us, int frames, double guest_us,
                            double pre_us, double post_us) {
  constexpr int kWarmup = 30;
  Limiter limiter;
  PacePublisher publisher;
  g_pace_next.store(0);
  g_pace_limit.store(0);
  PacingResult result;
  clk::time_point previous_present{};
  for (int f = 0; f < frames + kWarmup; ++f) {
    BusyFor(guest_us);
    PaceFrameBeforeLock(margin_us);
    const auto gate = clk::now();
    BusyFor(pre_us);
    const auto deadline = limiter.next;
    const double spin_before = limiter.spin_us;
    // As PresentTexture: publish only when LEGO_NATIVE_UNLOCKED_PACING is on.
    const bool publish_pace = margin_us != 0;
    const auto pace_entered = publish_pace ? clk::now() : clk::time_point{};
    limiter.LimitFrameRate(limit);
    if (publish_pace) publisher.Publish(limit, pace_entered);
    const auto present = clk::now();
    BusyFor(post_us);
    const auto released = clk::now();
    if (f >= kWarmup) {
      result.interval_us.push_back(Us(present - previous_present));
      result.late_us.push_back(Us(present - deadline));
      result.held_us.push_back(Us(released - gate));
      result.spin_us_per_frame += limiter.spin_us - spin_before;
      if (publish_pace) result.publish_gap_us.push_back(Us(limiter.next - publisher.next));
    }
    previous_present = present;
  }
  result.spin_us_per_frame /= frames;
  return result;
}

void BenchPacing(int runs) {
  constexpr double kGuest = 2000, kPre = 600, kPost = 400;  // us; illustrative frame shape
  std::printf("[pace] frame shape: guest %.0f us outside the gate, %.0f us under it before the limiter, "
              "%.0f us after the present; %d runs per row, medians of per-run values\n",
              kGuest, kPre, kPost, runs);
  std::printf("[pace]  pub-gap = LimitFrameRate's next minus PublishFramePace's, min..max over all "
              "frames and runs (us); never negative means the published deadline is never late\n");
  std::printf("[pace]  cap  mode            interval-mean  interval-sd  late-p50  late-p99  "
              "gate-held-mean  spin/frame   pub-gap-min  pub-gap-max\n");
  for (const int32_t limit : {240, 120, 60}) {
    const int frames = limit * 2;  // two seconds per run
    for (const int64_t margin : {int64_t(0), int64_t(2000), int64_t(4000)}) {
      std::vector<double> mean_interval, sd_interval, late50, late99, held, spin;
      double gap_min = 1e300, gap_max = -1e300;
      for (int r = 0; r < runs; ++r) {
        const auto res = SimulatePacing(limit, margin, frames, kGuest, kPre, kPost);
        mean_interval.push_back(Mean(res.interval_us));
        sd_interval.push_back(Stddev(res.interval_us));
        late50.push_back(Percentile(res.late_us, 0.5));
        late99.push_back(Percentile(res.late_us, 0.99));
        held.push_back(Mean(res.held_us));
        spin.push_back(res.spin_us_per_frame);
        for (const double gap : res.publish_gap_us) {
          gap_min = (std::min)(gap_min, gap);
          gap_max = (std::max)(gap_max, gap);
        }
      }
      char mode[32];
      if (margin) std::snprintf(mode, sizeof(mode), "unlocked-%lldus", static_cast<long long>(margin));
      else std::snprintf(mode, sizeof(mode), "old");
      char gap[48];
      if (margin) std::snprintf(gap, sizeof(gap), "%12.3f %12.3f", gap_min, gap_max);
      else std::snprintf(gap, sizeof(gap), "%12s %12s", "-", "-");
      std::printf("[pace]  %3d  %-14s %12.1f %12.1f %9.1f %9.1f %15.1f %11.1f  %s\n", limit, mode,
                  Percentile(mean_interval, 0.5),
                  Percentile(sd_interval, 0.5), Percentile(late50, 0.5), Percentile(late99, 0.5),
                  Percentile(held, 0.5), Percentile(spin, 0.5), gap);
    }
  }
}

}  // namespace

int main(int argc, char** argv) {
  bool win32 = true, timer = true, pacing = true, foreground = false;
  int runs = 5;
  for (int i = 1; i < argc; ++i) {
    if (!std::strcmp(argv[i], "--only-win32")) timer = pacing = false;
    if (!std::strcmp(argv[i], "--only-timer")) win32 = pacing = false;
    if (!std::strcmp(argv[i], "--only-pacing")) win32 = timer = false;
    if (!std::strcmp(argv[i], "--foreground")) foreground = true;
    if (!std::strcmp(argv[i], "--runs") && i + 1 < argc) runs = std::max(1, std::atoi(argv[++i]));
  }
  if (foreground) {
    // Approximate the game in a quiet window: no EcoQoS/power throttling, timer resolution
    // honoured, and one priority step above the other agents' build processes.
    PROCESS_POWER_THROTTLING_STATE process{};
    process.Version = PROCESS_POWER_THROTTLING_CURRENT_VERSION;
    process.ControlMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED |
                          PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION;
    process.StateMask = 0;
    const BOOL process_ok = SetProcessInformation(GetCurrentProcess(), ProcessPowerThrottling,
                                                  &process, sizeof(process));
    THREAD_POWER_THROTTLING_STATE thread{};
    thread.Version = THREAD_POWER_THROTTLING_CURRENT_VERSION;
    thread.ControlMask = THREAD_POWER_THROTTLING_EXECUTION_SPEED;
    thread.StateMask = 0;
    const BOOL thread_ok = SetThreadInformation(GetCurrentThread(), ThreadPowerThrottling, &thread,
                                                sizeof(thread));
    const BOOL priority_ok = SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_ABOVE_NORMAL);
    std::printf("[mode] foreground-like: power throttling off (process %d, thread %d), "
                "ABOVE_NORMAL priority %d\n", int(process_ok), int(thread_ok), int(priority_ok));
  } else {
    std::printf("[mode] as launched (background console process, normal priority)\n");
  }
  if (win32) {
    WNDCLASSW wc{};
    wc.lpfnWndProc = DefWindowProcW;
    wc.hInstance = GetModuleHandleW(nullptr);
    wc.lpszClassName = L"agent7_present_microbench";
    RegisterClassW(&wc);
    HWND hwnd = CreateWindowExW(0, wc.lpszClassName, L"agent7", WS_POPUP, 0, 0, 320, 240, nullptr,
                                nullptr, wc.hInstance, nullptr);
    if (!hwnd) {
      std::printf("[win32] CreateWindowExW failed (%lu)\n", GetLastError());
    } else {
      BenchWin32Queries(hwnd);
      DestroyWindow(hwnd);
    }
  }
  if (timer) BenchTimer();
  if (pacing) BenchPacing(runs);
  return 0;
}
