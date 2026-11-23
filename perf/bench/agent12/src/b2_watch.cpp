// B2: latency of the per-read write-watch check on a physical heap.
//   locked   = OLD: TriggerCallbacks(global_critical_region::AcquireDirect(), ...)
//              with no watched page (the common case): global recursive mutex
//              + block scan, returns false.
//   lockless = NEW (section A): MayHaveWriteWatches(): seq_cst fence + relaxed
//              block scan, no lock.
// Uncontended, and with a holder thread that owns the global mutex 50 us out
// of every 200 us (25%), like a busy GPU/kernel thread.
// Per-call latency by rdtsc (lfence-serialized), calls paced ~5 us apart so the
// samples cover the holder's duty cycle. Built with -DB12_NO_COUNTERS.
//
// Usage: b2_watch.exe [runs=5] [samples=100000]
#include "mock_memory.h"

#include <atomic>
#include <cinttypes>
#include <cstdlib>
#include <intrin.h>
#include <thread>

using namespace b12;

namespace {

constexpr uint32_t HP_BASE = 0x10000000, HP_SIZE = 0x04000000;  // 64 MB, 0xE0-like (hao 0x1000)

inline uint64_t tsc() {
  _mm_lfence();
  uint64_t t = __rdtsc();
  _mm_lfence();
  return t;
}

double g_tsc_per_ns = 1.0;
void calibrate() {
  const double q0 = qpc_seconds();
  const uint64_t t0 = tsc();
  while (qpc_seconds() - q0 < 0.1) {
  }
  const uint64_t t1 = tsc();
  const double q1 = qpc_seconds();
  g_tsc_per_ns = double(t1 - t0) / ((q1 - q0) * 1e9);
}
void spin_ns(double ns) {
  const uint64_t end = tsc() + uint64_t(ns * g_tsc_per_ns);
  while (tsc() < end) _mm_pause();
}

struct Stats {
  double mean, p50, p99, max;
};
Stats stats_of(std::vector<double>& v) {
  std::sort(v.begin(), v.end());
  double sum = 0;
  for (double x : v) sum += x;
  auto pct = [&](double p) { return v[std::min(v.size() - 1, size_t(p * double(v.size())))]; };
  return {sum / double(v.size()), pct(0.50), pct(0.99), v.back()};
}

enum Method { kLocked, kLockless, kNumMethods };
const char* kMethodNames[kNumMethods] = {"locked TriggerCallbacks (OLD)",
                                         "lockless MayHaveWriteWatches (NEW)"};

}  // namespace

int main(int argc, char** argv) {
  const int runs = argc > 1 ? std::atoi(argv[1]) : 5;
  const size_t samples = argc > 2 ? size_t(std::strtoull(argv[2], nullptr, 0)) : 100000;
  setvbuf(stdout, nullptr, _IONBF, 0);
  print_machine_header("B2 watch check latency");
  calibrate();

  Layout l;
  l.heaps = {{HeapType::kGuestPhysical, HP_BASE, HP_SIZE, 0x1000, true, 0}};
  l.virtual_commit = 0x10000;
  l.physical_commit = 0x10000;
  MockMemory mem(l);
  PhysicalHeap* heap = mem.physical_heap(0);
  // Some watched pages elsewhere in the heap (GPU textures), none in the
  // ranges the reads hit: the check must scan and come back false.
  for (size_t b = 0; b < heap->flags().size(); b += 7) heap->flags()[b].notify_on_invalidation = 0;
  heap->flags().back().notify_on_invalidation = 1ull << 63;

  // empty-measurement overhead
  std::vector<double> ov(20000);
  for (double& x : ov) {
    const uint64_t a = tsc();
    const uint64_t b = tsc();
    x = double(b - a) / g_tsc_per_ns;
  }
  const double overhead = stats_of(ov).p50;
  std::printf("rdtsc %.3f ticks/ns; empty-measurement overhead %.1f ns (subtracted)\n",
              g_tsc_per_ns, overhead);

  const uint32_t lengths[] = {4096, 1u << 20};
  std::printf("| check | range | holder | mean ns median [min-max] | p50 ns median | p99 ns median [min-max] | max ns (worst run) | load median |\n");
  std::printf("|---|---:|---|---|---:|---|---:|---:|\n");
  for (int contended = 0; contended < 2; ++contended) {
    std::atomic<bool> stop{false};
    std::thread holder;
    if (contended) {
      holder = std::thread([&] {
        while (!stop.load(std::memory_order_relaxed)) {
          {
            auto lock = global_critical_region::AcquireDirect();
            spin_ns(50000);
          }
          spin_ns(150000);
        }
      });
    }
    for (uint32_t len : lengths) {
      std::vector<double> means[kNumMethods], p50s[kNumMethods], p99s[kNumMethods],
          maxs[kNumMethods], loads[kNumMethods];
      volatile bool sink = false;
      for (int r = -1; r < runs; ++r) {  // r = -1: warm-up
        for (int m = 0; m < kNumMethods; ++m) {
          if (r >= 0) loads[m].push_back(100.0 * sample_machine_load(30));
          std::vector<double> lat(samples);
          uint64_t s = 0x2B2B2B2Bull + uint64_t(r + 1) * 77 + m;
          for (size_t i = 0; i < samples; ++i) {
            const uint32_t pages = (HP_SIZE - len) / 4096;
            const uint32_t va = HP_BASE + uint32_t(xorshift64(s) % pages) * 4096;
            const uint64_t a = tsc();
            bool w;
            if (m == kLocked) {
              w = heap->TriggerCallbacks(global_critical_region::AcquireDirect(), va, len, true, true);
            } else {
              w = heap->MayHaveWriteWatches(va, len);
            }
            const uint64_t b = tsc();
            sink = sink || w;
            lat[i] = std::max(0.0, double(b - a) / g_tsc_per_ns - overhead);
            spin_ns(5000);
          }
          if (r >= 0) {
            Stats st = stats_of(lat);
            means[m].push_back(st.mean);
            p50s[m].push_back(st.p50);
            p99s[m].push_back(st.p99);
            maxs[m].push_back(st.max);
          }
        }
      }
      if (sink) std::printf("unexpected: a watched page was reported\n");
      for (int m = 0; m < kNumMethods; ++m) {
        const Summary mean = summarize(means[m]), p50 = summarize(p50s[m]),
                      p99 = summarize(p99s[m]), mx = summarize(maxs[m]), ld = summarize(loads[m]);
        std::printf("| %s | %u KB | %s | %.1f [%.1f-%.1f] | %.1f | %.1f [%.1f-%.1f] | %.0f | %.0f%% |\n",
                    kMethodNames[m], len / 1024, contended ? "25% held" : "none", mean.median,
                    mean.min, mean.max, p50.median, p99.median, p99.min, p99.max, mx.max,
                    ld.median);
      }
    }
    stop.store(true);
    if (holder.joinable()) holder.join();
  }
  std::printf("\n(n=%d runs x %zu paced samples per row after a warm-up run)\n", runs, samples);
  return 0;
}
