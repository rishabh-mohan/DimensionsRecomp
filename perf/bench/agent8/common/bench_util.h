// Shared helpers for the agent8 runtime microbenches: a QPC clock, summary
// statistics, a high-resolution timed wait, and the RESULT/CHECK line format
// that build-runtime-benches.ps1 parses:
//   RESULT <bench> <variant> <key> <value> <unit>
//   CHECK  <bench> <variant> <name> PASS|FAIL <detail...>
#pragma once

#include <windows.h>

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#ifndef CREATE_WAITABLE_TIMER_HIGH_RESOLUTION
#define CREATE_WAITABLE_TIMER_HIGH_RESOLUTION 0x00000002
#endif

namespace benchutil {

inline int64_t QpcFrequency() {
  static const int64_t frequency = [] {
    LARGE_INTEGER li;
    QueryPerformanceFrequency(&li);
    return int64_t(li.QuadPart);
  }();
  return frequency;
}

inline int64_t NowNs() {
  LARGE_INTEGER li;
  QueryPerformanceCounter(&li);
  const int64_t f = QpcFrequency();
  return (li.QuadPart / f) * 1000000000LL + (li.QuadPart % f) * 1000000000LL / f;
}

struct Stats {
  double median = 0.0;
  double min = 0.0;
  double max = 0.0;
  double mean = 0.0;
  size_t n = 0;
};

inline Stats Summarize(std::vector<double> v) {
  Stats s;
  s.n = v.size();
  if (v.empty()) {
    return s;
  }
  std::sort(v.begin(), v.end());
  s.min = v.front();
  s.max = v.back();
  const size_t h = v.size() / 2;
  s.median = (v.size() % 2) ? v[h] : 0.5 * (v[h - 1] + v[h]);
  double sum = 0.0;
  for (double x : v) {
    sum += x;
  }
  s.mean = sum / double(v.size());
  return s;
}

inline void Result(const char* bench, const char* variant, const std::string& key, double value,
                   const char* unit) {
  std::printf("RESULT %s %s %s %.6g %s\n", bench, variant, key.c_str(), value, unit);
  std::fflush(stdout);
}

inline void Check(const char* bench, const char* variant, const std::string& name, bool pass,
                  const std::string& detail) {
  std::printf("CHECK %s %s %s %s %s\n", bench, variant, name.c_str(), pass ? "PASS" : "FAIL",
              detail.empty() ? "-" : detail.c_str());
  std::fflush(stdout);
}

// Timed waits that do not depend on the 15.6 ms scheduler tick, so a delay
// lands at an arbitrary phase relative to tick-aligned sleepers. Falls back to
// Sleep() if the high-resolution timer is unavailable.
class HiResWaiter {
 public:
  HiResWaiter() {
    timer_ = CreateWaitableTimerExW(nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,
                                    TIMER_ALL_ACCESS);
    high_res_ = timer_ != nullptr;
    if (!timer_) {
      timer_ = CreateWaitableTimerExW(nullptr, nullptr, 0, TIMER_ALL_ACCESS);
    }
  }
  ~HiResWaiter() {
    if (timer_) {
      CloseHandle(timer_);
    }
  }
  HiResWaiter(const HiResWaiter&) = delete;
  HiResWaiter& operator=(const HiResWaiter&) = delete;

  bool high_res() const { return high_res_; }

  void WaitNs(int64_t ns) {
    LARGE_INTEGER due;
    due.QuadPart = -std::max<int64_t>(1, ns / 100);
    if (timer_ && SetWaitableTimer(timer_, &due, 0, nullptr, nullptr, FALSE)) {
      WaitForSingleObject(timer_, INFINITE);
    } else {
      Sleep(DWORD(std::max<int64_t>(1, ns / 1000000)));
    }
  }

 private:
  HANDLE timer_ = nullptr;
  bool high_res_ = false;
};

}  // namespace benchutil
