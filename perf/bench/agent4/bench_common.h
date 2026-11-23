// Shared helpers for the bench/agent4 microbenches (clang++ -O2 -march=x86-64-v3, MSVC ABI).
// Each case is timed once per rep and the reps of all cases are interleaved, so drift from other
// load on the machine hits every case alike. Lines starting with RESULT are parsed by run_benches.py.
#pragma once
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <string>
#include <vector>

#define BENCH_NOINLINE __attribute__((noinline))
#define BENCH_CHECK(cond)                                                                   \
  do {                                                                                      \
    if (!(cond)) {                                                                          \
      std::fprintf(stderr, "CHECK failed %s:%d: %s\n", __FILE__, __LINE__, #cond);          \
      std::exit(1);                                                                         \
    }                                                                                       \
  } while (0)

namespace bench {

template <class T>
inline void DoNotOptimize(T& value) { asm volatile("" : "+r,m"(value) : : "memory"); }
template <class T>
inline void DoNotOptimize(const T& value) { asm volatile("" : : "r,m"(value) : "memory"); }
inline void ClobberMemory() { asm volatile("" : : : "memory"); }

// Nanoseconds per op for one call of `body`, which must perform `ops` ops.
template <class F>
inline double NsPerOp(size_t ops, F&& body) {
  const auto start = std::chrono::steady_clock::now();
  body();
  const auto stop = std::chrono::steady_clock::now();
  return std::chrono::duration<double, std::nano>(stop - start).count() / double(ops);
}

struct Case {
  std::string name;
  std::function<double()> run;  // returns ns per op
};

// One warm-up pass, then `reps` interleaved passes; prints median/min/max ns per op per case.
inline void RunCases(const char* group, const std::vector<Case>& cases, int reps = 9) {
  std::vector<std::vector<double>> samples(cases.size());
  for (const auto& c : cases) c.run();
  for (int rep = 0; rep < reps; ++rep)
    for (size_t i = 0; i < cases.size(); ++i) samples[i].push_back(cases[i].run());
  for (size_t i = 0; i < cases.size(); ++i) {
    auto& s = samples[i];
    std::sort(s.begin(), s.end());
    std::printf("RESULT\t%s\t%s\t%.4f\t%.4f\t%.4f\n", group, cases[i].name.c_str(), s[s.size() / 2],
                s.front(), s.back());
  }
  std::fflush(stdout);
}

}  // namespace bench
