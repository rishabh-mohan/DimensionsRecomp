#pragma once
// Agent 8 bench timing helpers (journal and HexWords benches).
//
// Every measurement reports wall-clock time and thread CPU time. The CPU time
// comes from QueryThreadCycleTime (TSC reference cycles consumed by the calling
// thread, converted with a measured TSC rate), so it excludes time the thread
// spent preempted. That matters on this machine, where other agents' builds
// often keep every logical CPU busy. Spin-waiting on a contended lock is CPU
// time and is still counted.
#include <windows.h>
#include <intrin.h>

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <vector>

namespace bench {

struct Measure {
  double wall = 0, cpu = 0;  // ns per op
};

inline double TscPerNs() {
  static const double value = [] {
    LARGE_INTEGER frequency{}, a{}, b{};
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&a);
    const uint64_t t0 = __rdtsc();
    do {
      QueryPerformanceCounter(&b);
    } while (double(b.QuadPart - a.QuadPart) / double(frequency.QuadPart) < 0.05);
    const uint64_t t1 = __rdtsc();
    return double(t1 - t0) / (double(b.QuadPart - a.QuadPart) * 1e9 / double(frequency.QuadPart));
  }();
  return value;
}

class Stopwatch {
 public:
  Stopwatch() {
    QueryThreadCycleTime(GetCurrentThread(), &cycles0_);
    wall0_ = Clock::now();
  }
  Measure PerOp(double ops) const {
    const auto wall1 = Clock::now();
    ULONG64 cycles1 = 0;
    QueryThreadCycleTime(GetCurrentThread(), &cycles1);
    return {std::chrono::duration<double, std::nano>(wall1 - wall0_).count() / ops,
            double(cycles1 - cycles0_) / TscPerNs() / ops};
  }

 private:
  using Clock = std::chrono::steady_clock;
  Clock::time_point wall0_;
  ULONG64 cycles0_ = 0;
};

inline double Median(std::vector<double> v) {
  if (v.empty()) return 0;
  std::sort(v.begin(), v.end());
  return v.size() % 2 ? v[v.size() / 2] : (v[v.size() / 2 - 1] + v[v.size() / 2]) / 2;
}

inline double Min(const std::vector<double>& v) {
  return v.empty() ? 0 : *std::min_element(v.begin(), v.end());
}

inline double Max(const std::vector<double>& v) {
  return v.empty() ? 0 : *std::max_element(v.begin(), v.end());
}

// ABOVE_NORMAL keeps the scheduler from preempting the (at most 2) bench
// threads for normal-priority build jobs; --normal-priority turns it off.
inline const char* SetBenchPriority(bool raise) {
  if (raise && SetPriorityClass(GetCurrentProcess(), ABOVE_NORMAL_PRIORITY_CLASS)) {
    return "above-normal";
  }
  return "normal";
}

// A 50 ms spin: CPU and wall time agree when the thread was not preempted.
inline void PrintCalibration() {
  Stopwatch watch;
  volatile uint64_t spin = 0;
  const auto end = std::chrono::steady_clock::now() + std::chrono::milliseconds(50);
  while (std::chrono::steady_clock::now() < end) spin = spin + 1;
  const Measure m = watch.PerOp(1);
  std::printf("calibration: TSC %.3f GHz; 50 ms spin: wall %.2f ms, thread CPU %.2f ms\n",
              TscPerNs(), m.wall / 1e6, m.cpu / 1e6);
}

}  // namespace bench
