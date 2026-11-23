// bench_common.h - shared helpers for Agent 11 micro-benchmarks (Windows only).
#pragma once
#define NOMINMAX
#include <windows.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <vector>

#ifndef CREATE_WAITABLE_TIMER_HIGH_RESOLUTION
#define CREATE_WAITABLE_TIMER_HIGH_RESOLUTION 0x00000002
#endif
#ifndef CREATE_WAITABLE_TIMER_MANUAL_RESET
#define CREATE_WAITABLE_TIMER_MANUAL_RESET 0x00000001
#endif

inline int64_t qpc() {
  LARGE_INTEGER q;
  QueryPerformanceCounter(&q);
  return q.QuadPart;
}
inline int64_t qpf() {
  static int64_t f = [] {
    LARGE_INTEGER x;
    QueryPerformanceFrequency(&x);
    return x.QuadPart;
  }();
  return f;
}
inline double ticks_ms(int64_t t) { return double(t) * 1000.0 / double(qpf()); }
inline double ticks_us(int64_t t) { return double(t) * 1e6 / double(qpf()); }
inline double ticks_ns(int64_t t) { return double(t) * 1e9 / double(qpf()); }

// Percentile with linear interpolation; p in [0,1]. Takes a copy.
inline double pct(std::vector<double> v, double p) {
  if (v.empty()) return NAN;
  std::sort(v.begin(), v.end());
  double idx = p * double(v.size() - 1);
  size_t lo = size_t(idx), hi = std::min(lo + 1, v.size() - 1);
  double f = idx - double(lo);
  return v[lo] * (1.0 - f) + v[hi] * f;
}
inline double median(const std::vector<double>& v) { return pct(v, 0.5); }
inline double vmin(const std::vector<double>& v) { return v.empty() ? NAN : *std::min_element(v.begin(), v.end()); }
inline double vmax(const std::vector<double>& v) { return v.empty() ? NAN : *std::max_element(v.begin(), v.end()); }

// Busy-wait for `ticks` QPC ticks.
inline void spin_ticks(int64_t ticks) {
  int64_t t0 = qpc();
  while (qpc() - t0 < ticks) {
  }
}

// Serializes all agent11 bench processes machine-wide (session-local named
// mutex), so two helpers never time things at the same moment. Released when
// the process exits; an abandoned mutex (crash) still grants ownership.
struct BenchSerializer {
  HANDLE h = nullptr;
  BenchSerializer() {
    h = CreateMutexW(nullptr, FALSE, L"Local\\agent11-bench-serialize");
    if (!h) return;
    DWORD r = WaitForSingleObject(h, 0);
    if (r == WAIT_TIMEOUT) {
      fprintf(stderr, "[bench] waiting for another agent11 bench to finish...\n");
      WaitForSingleObject(h, INFINITE);
    }
  }
  ~BenchSerializer() {
    if (h) {
      ReleaseMutex(h);
      CloseHandle(h);
    }
  }
};
inline BenchSerializer g_bench_serializer;

typedef LONG(NTAPI* NtQueryTimerResolution_t)(PULONG, PULONG, PULONG);
// Prints NtQueryTimerResolution (100 ns units -> ms). "min" is the coarsest value, "max" the finest.
inline void print_timer_res(const char* tag) {
  static auto fn = reinterpret_cast<NtQueryTimerResolution_t>(
      GetProcAddress(GetModuleHandleW(L"ntdll.dll"), "NtQueryTimerResolution"));
  ULONG mn = 0, mx = 0, cur = 0;
  LONG st = fn ? fn(&mn, &mx, &cur) : -1;
  printf("[%s] NtQueryTimerResolution st=0x%08lx current=%.4f ms min(coarsest)=%.4f ms max(finest)=%.4f ms\n",
         tag, (unsigned long)st, cur / 1e4, mn / 1e4, mx / 1e4);
}

// ---- Added by helper A (session 2). New names only, inside namespace bench_a. ----
#include <intrin.h>
namespace bench_a {
inline uint64_t ft_u64(FILETIME f) { return (uint64_t(f.dwHighDateTime) << 32) | f.dwLowDateTime; }

// AC line state + system-wide CPU load sampled over `ms` with GetSystemTimes.
inline void print_machine_state(const char* tag, DWORD ms = 250) {
  SYSTEM_POWER_STATUS ps{};
  GetSystemPowerStatus(&ps);
  FILETIME i0, k0, u0, i1, k1, u1;
  GetSystemTimes(&i0, &k0, &u0);
  Sleep(ms);
  GetSystemTimes(&i1, &k1, &u1);
  uint64_t idle = ft_u64(i1) - ft_u64(i0);
  uint64_t total = (ft_u64(k1) - ft_u64(k0)) + (ft_u64(u1) - ft_u64(u0));  // kernel includes idle
  double load = total ? 100.0 * double(total - idle) / double(total) : NAN;
  printf("[%s] AC=%s battery=%d%% cpu_load=%.0f%% (GetSystemTimes, %lu ms)\n", tag,
         ps.ACLineStatus == 1 ? "online" : (ps.ACLineStatus == 0 ? "OFFLINE" : "unknown"),
         ps.BatteryLifePercent == 255 ? -1 : int(ps.BatteryLifePercent), load, (unsigned long)ms);
}

// Serialized TSC reads for short intervals (invariant TSC). Use tsc_per_ns() to convert.
inline uint64_t tsc_begin() { _mm_lfence(); uint64_t t = __rdtsc(); _mm_lfence(); return t; }
inline uint64_t tsc_end() { unsigned aux; uint64_t t = __rdtscp(&aux); _mm_lfence(); return t; }
inline double tsc_per_ns() {
  static double f = [] {
    int64_t q0 = qpc();
    uint64_t t0 = __rdtsc();
    Sleep(100);
    int64_t q1 = qpc();
    uint64_t t1 = __rdtsc();
    return double(t1 - t0) / ticks_ns(q1 - q0);
  }();
  return f;
}

struct Summary {
  double med = NAN, p90 = NAN, p99 = NAN, p999 = NAN, max = NAN, mean = NAN;
  size_t n = 0;
};
// One sort; linear interpolation like pct().
inline Summary summarize(std::vector<double> v) {
  Summary s;
  s.n = v.size();
  if (v.empty()) return s;
  std::sort(v.begin(), v.end());
  auto at = [&](double p) {
    double idx = p * double(v.size() - 1);
    size_t lo = size_t(idx), hi = std::min(lo + 1, v.size() - 1);
    return v[lo] + (v[hi] - v[lo]) * (idx - double(lo));
  };
  double sum = 0;
  for (double x : v) sum += x;
  s.med = at(0.5); s.p90 = at(0.9); s.p99 = at(0.99); s.p999 = at(0.999);
  s.max = v.back(); s.mean = sum / double(v.size());
  return s;
}
}  // namespace bench_a
