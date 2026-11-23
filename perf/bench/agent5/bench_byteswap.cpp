// Item 3 bench: the old scalar ByteSwapElements (byteswap_reference.h) against
// SwapUploadElementBytes (gpu_native/vertex_upload.h), same TU and flags.
// Usage: bench_byteswap.exe [samples=7]. One thread; each sample swaps about
// 64 MB in total; prints the median per call. Destinations are ordinary cached
// memory: production writes into mapped UPLOAD (write-combined) memory or a
// heap scratch, which a microbench can't reproduce.
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>
#include "byteswap_reference.h"
#include "gpu_native/vertex_upload.h"

namespace {
inline void Clobber(void* p) { asm volatile("" : : "r"(p) : "memory"); }

template <class F>
double MedianNs(int samples, size_t reps, F&& body) {
  body();  // warm-up
  std::vector<double> times;
  for (int s = 0; s < samples; ++s) {
    const auto start = std::chrono::steady_clock::now();
    for (size_t r = 0; r < reps; ++r) body();
    const auto stop = std::chrono::steady_clock::now();
    times.push_back(std::chrono::duration<double, std::nano>(stop - start).count() / double(reps));
  }
  std::nth_element(times.begin(), times.begin() + times.size() / 2, times.end());
  return times[times.size() / 2];
}
}  // namespace

int main(int argc, char** argv) {
  const int samples = argc > 1 ? std::max(5, std::atoi(argv[1])) : 7;
  std::printf("ByteSwapElements bench: path=%s, %d samples, median per call\n",
#if defined(__AVX2__)
              "AVX2+SSSE3",
#elif defined(__SSSE3__)
              "SSSE3",
#else
              "scalar",
#endif
              samples);
  std::printf("%-9s %-5s %12s %12s %9s %9s %8s\n", "size", "elem", "old ns", "new ns", "old GB/s",
              "new GB/s", "speedup");
  std::mt19937_64 rng(42);
  for (size_t size : {size_t(96), size_t(4) << 10, size_t(64) << 10, size_t(1) << 20, size_t(8) << 20}) {
    std::vector<uint8_t> source(size), destination(size);
    for (auto& b : source) b = uint8_t(rng());
    const size_t reps = std::max<size_t>(1, (size_t(64) << 20) / size);
    for (uint32_t element_size : {2u, 4u}) {
      const double old_ns = MedianNs(samples, reps, [&] {
        agent5_reference::ByteSwapElements(destination.data(), source.data(), size, element_size);
        Clobber(destination.data());
      });
      const double new_ns = MedianNs(samples, reps, [&] {
        legodimensions::gpu_native::SwapUploadElementBytes(destination.data(), source.data(), size,
                                                           element_size);
        Clobber(destination.data());
      });
      char label[32];
      if (size >= (size_t(1) << 20)) std::snprintf(label, sizeof label, "%zu MB", size >> 20);
      else if (size >= 1024) std::snprintf(label, sizeof label, "%zu KB", size >> 10);
      else std::snprintf(label, sizeof label, "%zu B", size);
      std::printf("%-9s %-5u %12.1f %12.1f %9.2f %9.2f %7.1fx\n", label, element_size, old_ns, new_ns,
                  double(size) / old_ns, double(size) / new_ns, old_ns / new_ns);
    }
  }
  return 0;
}
