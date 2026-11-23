// m1_copybench.cpp (Agent 5, task #7, 2026-11-22): microbench for S4 M1, the non-temporal
// upload copy (cvar shared_memory_upload_nontemporal_copy, default off; S4-DRAFT row 11;
// step 2 of the test plan in build/agent5/s4-m1/NOTE.md). No game involved.
//
// Status: task #7 staged it; bench/agent5/m1_copybench_syntax.ps1 syntax-checks it. Task #18
// added --check-only, the functional gate before M1 is ever ON; build/agent5/s4-m1/HASHES.txt
// records each build and check run. The rate part has not been run (no timing allowed yet).
//
// 1. Correctness. CopyToUploadBufferNonTemporal is a verbatim copy of the M1 helper (the lines
//    between HELPER-BEGIN and HELPER-END; the syntax script compares them with
//    build/agent5/s4-m1/new/shared_memory.cpp). It must produce memcpy's bytes for every dst
//    misalignment 0-63 x sizes 0-300, and for 7 large sizes up to 3844 KB, from several src
//    misalignments. It must leave the guard bytes on both sides untouched. Two guard values
//    are used, so a skipped byte can't match by chance. The check runs on normal memory and
//    on the mapped upload buffer, which is read back with SSE4.1 streaming loads (it is
//    uncached). Each group of cases (memory, guard, then the src misalignment or the large
//    size) prints its case count, failures and PASS/FAIL; a RESULT line ends part 1.
// 2. Rate. GB/s of four ways to copy 4 KB-aligned pages to 4 KB-aligned destinations, the
//    way UploadRanges does:
//      memcpy: the CRT memcpy that UploadRanges calls today, through a volatile pointer so it
//              can't be inlined. In a-prof it was vcruntime with a rep movsb stub.
//      nt:     the M1 helper: streaming stores, then an sfence.
//      movsb:  a bare rep movsb. Is the CRT's choice of string copy the slow part?
//      sse2:   the helper's loop with ordinary aligned stores and no sfence: explicit
//              64-byte stores without the streaming hint.
//    Destinations:
//      "upload": a mapped D3D12 upload-heap buffer of 8 MiB (4 pool pages). The header
//                prints its CPU page property: WRITE_COMBINE on a discrete GPU.
//      "wb":     VirtualAlloc'd normal memory, as a reference.
//    Sources:
//      "warm": 4 MiB, cache-resident after the first pass.
//      "cold": 256 MiB walked in order, so each copy reads lines that left the caches long
//              ago.
//    Chunks: 4 KB, 64 KB, 256 KB, 1 MiB and 2 MiB, plus "avol": a-vol's 3844 KB buffer as a
//    2 MiB + 1796 KB pair (one possible pool split).
//    Each sample copies at least --mb MiB. The variants run in a rotated order in each
//    sample, and every variant gets an sfence before the stop time. The CSV gives the median
//    and best GB/s per variant, plus the median rate as ms per a-vol frame (3847 KB).
//    Compare that with a-prof's 2.9-3.1 ms/f of memcpy.
//
// Build (only once benchmarks are allowed), in a dev shell (. env\devshell.ps1), on one line:
//   clang++ -std=c++23 -O3 -march=x86-64-v2 -fno-strict-aliasing -fms-runtime-lib=dll
//     bench\agent5\m1_copybench.cpp -o build\agent5\m1_copybench.exe
// d3d12.lib and dxgi.lib come in through #pragma comment. The DLL CRT is the one the game
// uses.
// Run: m1_copybench.exe [--adapter N] [--cpu N] [--samples N] [--mb N] [--csv FILE]
//                       [--skip-check] [--skip-rate] [--check-only]
//   --skip-rate and --check-only leave the rate buffers out (no GB/s, no 256 MiB cold source);
//   --check-only also says so in the header line and can't be combined with --skip-check.
// Exit: 0 = every correctness case passed and the upload buffer was available;
//       1 = a correctness failure; 2 = bad arguments or a setup failure.

#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>

#include <d3d12.h>
#include <dxgi1_6.h>
#include <wrl/client.h>

#include <emmintrin.h>
#include <intrin.h>
#include <smmintrin.h>

#include <algorithm>
#include <cstdarg>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#pragma comment(lib, "d3d12.lib")
#pragma comment(lib, "dxgi.lib")

// The test from rex/platform.h L77-78, so the helper below compiles unchanged.
#if defined(_M_AMD64) || defined(__amd64__)
#define REX_ARCH_AMD64 1
#else
#error "m1_copybench measures the x86-64 path of the M1 helper"
#endif

#if defined(__clang__) || defined(__GNUC__)
#define M1_PRINTF_FORMAT __attribute__((format(printf, 1, 2)))
#else
#define M1_PRINTF_FORMAT
#endif

namespace {

using Microsoft::WRL::ComPtr;

constexpr size_t kKiB = 1024;
constexpr size_t kMiB = 1024 * kKiB;
constexpr size_t kPage = 4096;                    // UploadRanges' dst and src alignment
constexpr size_t kUploadBytes = 8 * kMiB;         // 4 upload pool pages of 2 MiB
constexpr size_t kWarmSrcBytes = 4 * kMiB;
constexpr size_t kColdSrcBytes = 256 * kMiB;
constexpr size_t kCheckBytes = 4 * kMiB + kPage;  // the largest check case plus its guards
constexpr size_t kAvolFrameBytes = 3847 * kKiB;   // a-vol: mean invalidated KB per frame

// ---- HELPER-BEGIN (verbatim from build/agent5/s4-m1/new/shared_memory.cpp) ----
void CopyToUploadBufferNonTemporal(uint8_t* dst, const uint8_t* src, size_t size) {
#if REX_ARCH_AMD64
  size_t head = (64 - (reinterpret_cast<uintptr_t>(dst) & 63)) & 63;
  if (head > size) {
    head = size;
  }
  if (head) {
    std::memcpy(dst, src, head);
    dst += head;
    src += head;
    size -= head;
  }
  size_t body = size & ~size_t(63);
  for (size_t offset = 0; offset < body; offset += 64) {
    __m128i data0 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset));
    __m128i data1 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset + 16));
    __m128i data2 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset + 32));
    __m128i data3 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset + 48));
    _mm_stream_si128(reinterpret_cast<__m128i*>(dst + offset), data0);
    _mm_stream_si128(reinterpret_cast<__m128i*>(dst + offset + 16), data1);
    _mm_stream_si128(reinterpret_cast<__m128i*>(dst + offset + 32), data2);
    _mm_stream_si128(reinterpret_cast<__m128i*>(dst + offset + 48), data3);
  }
  if (size > body) {
    std::memcpy(dst + body, src + body, size - body);
  }
  _mm_sfence();
#else
  std::memcpy(dst, src, size);
#endif
}
// ---- HELPER-END ----

using CopyFn = void (*)(uint8_t* dst, const uint8_t* src, size_t size);

// The CRT memcpy that UploadRanges calls today. Called through a volatile pointer, so the
// compiler can neither inline it nor see the size.
void* (*volatile g_memcpy)(void*, const void*, size_t) = &memcpy;

void CopyCrtMemcpy(uint8_t* dst, const uint8_t* src, size_t size) { g_memcpy(dst, src, size); }

void CopyRepMovsb(uint8_t* dst, const uint8_t* src, size_t size) {
#if defined(__clang__) || defined(__GNUC__)
  asm volatile("rep movsb" : "+D"(dst), "+S"(src), "+c"(size) : : "memory");
#else
  __movsb(dst, src, size);
#endif
}

// The helper's loop with ordinary aligned stores and no sfence. The empty asm statement
// keeps the compiler from turning the loop back into a memcpy call.
void CopySse2Stores(uint8_t* dst, const uint8_t* src, size_t size) {
  size_t head = (64 - (reinterpret_cast<uintptr_t>(dst) & 63)) & 63;
  if (head > size) {
    head = size;
  }
  std::memcpy(dst, src, head);
  dst += head;
  src += head;
  size -= head;
  size_t body = size & ~size_t(63);
  for (size_t offset = 0; offset < body; offset += 64) {
    __m128i data0 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset));
    __m128i data1 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset + 16));
    __m128i data2 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset + 32));
    __m128i data3 = _mm_loadu_si128(reinterpret_cast<const __m128i*>(src + offset + 48));
    _mm_store_si128(reinterpret_cast<__m128i*>(dst + offset), data0);
    _mm_store_si128(reinterpret_cast<__m128i*>(dst + offset + 16), data1);
    _mm_store_si128(reinterpret_cast<__m128i*>(dst + offset + 32), data2);
    _mm_store_si128(reinterpret_cast<__m128i*>(dst + offset + 48), data3);
#if defined(__clang__) || defined(__GNUC__)
    asm volatile("" : : : "memory");
#endif
  }
  std::memcpy(dst + body, src + body, size - body);
}

struct Variant {
  const char* name;
  CopyFn fn;
};

constexpr Variant kVariants[] = {
    {"memcpy", CopyCrtMemcpy},
    {"nt", CopyToUploadBufferNonTemporal},
    {"movsb", CopyRepMovsb},
    {"sse2", CopySse2Stores},
};
constexpr size_t kNumVariants = sizeof(kVariants) / sizeof(kVariants[0]);

struct Pattern {
  const char* name;
  size_t chunks[2];
  size_t count;
};

constexpr Pattern kPatterns[] = {
    {"4k", {4 * kKiB, 0}, 1},
    {"64k", {64 * kKiB, 0}, 1},
    {"256k", {256 * kKiB, 0}, 1},
    {"1m", {1 * kMiB, 0}, 1},
    {"2m", {2 * kMiB, 0}, 1},
    {"avol", {2 * kMiB, 1796 * kKiB}, 2},  // a-vol's 3844 KB buffer split at a pool page
};

struct Options {
  int adapter = 0;
  int cpu = -1;
  size_t samples = 9;
  size_t mib_per_sample = 64;
  const char* csv_path = nullptr;
  bool skip_check = false;
  bool skip_rate = false;
  bool check_only = false;  // --check-only: part 1 alone (also sets skip_rate)
};

FILE* g_csv = nullptr;

// printf to stdout, and to the --csv file if there is one.
M1_PRINTF_FORMAT void Emit(const char* format, ...) {
  va_list args;
  va_start(args, format);
  std::vprintf(format, args);
  va_end(args);
  if (g_csv) {
    va_start(args, format);
    std::vfprintf(g_csv, format, args);
    va_end(args);
  }
}

double NowSeconds() {
  static const double seconds_per_tick = [] {
    LARGE_INTEGER frequency;
    QueryPerformanceFrequency(&frequency);
    return 1.0 / double(frequency.QuadPart);
  }();
  LARGE_INTEGER now;
  QueryPerformanceCounter(&now);
  return double(now.QuadPart) * seconds_per_tick;
}

uint8_t* AllocPages(size_t bytes) {
  return static_cast<uint8_t*>(
      VirtualAlloc(nullptr, bytes, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
}

// xorshift64 bytes: nearby offsets hold different data, so a copy from the wrong offset
// can't pass the check.
void FillPattern(uint8_t* p, size_t n, uint64_t seed) {
  uint64_t x = seed * 0x9E3779B97F4A7C15ull + 1;
  for (size_t i = 0; i < n; i += 8) {
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    std::memcpy(p + i, &x, std::min<size_t>(8, n - i));
  }
}

// Reads n bytes from p (64-byte aligned) into out. SSE4.1 streaming loads are the fast way
// to read write-combined (uncached) memory; on normal memory they act as plain loads.
void ReadBack(uint8_t* out, const uint8_t* p, size_t n) {
  size_t body = n & ~size_t(63);
  for (size_t offset = 0; offset < body; offset += 64) {
    __m128i data0 = _mm_stream_load_si128(reinterpret_cast<const __m128i*>(p + offset));
    __m128i data1 = _mm_stream_load_si128(reinterpret_cast<const __m128i*>(p + offset + 16));
    __m128i data2 = _mm_stream_load_si128(reinterpret_cast<const __m128i*>(p + offset + 32));
    __m128i data3 = _mm_stream_load_si128(reinterpret_cast<const __m128i*>(p + offset + 48));
    _mm_storeu_si128(reinterpret_cast<__m128i*>(out + offset), data0);
    _mm_storeu_si128(reinterpret_cast<__m128i*>(out + offset + 16), data1);
    _mm_storeu_si128(reinterpret_cast<__m128i*>(out + offset + 32), data2);
    _mm_storeu_si128(reinterpret_cast<__m128i*>(out + offset + 48), data3);
  }
  for (size_t i = body; i < n; ++i) {
    out[i] = p[i];
  }
}

struct CheckResult {
  unsigned long long cases = 0;
  unsigned long long failures = 0;
  unsigned long long skipped = 0;  // large cases that don't fit the region (none expected)
};

// One case: guard bytes on both sides of dst, copy with the helper, read back, compare.
// region is 64-byte aligned and holds at least 64 + 63 + size + 64 bytes.
void CheckCase(const char* mem, uint8_t* region, const uint8_t* src_base, uint8_t* scratch,
               size_t dst_mis, size_t src_mis, size_t size, uint8_t guard,
               CheckResult& result) {
  const size_t lead = 64 + dst_mis;
  const size_t span = lead + size + 64;
  const uint8_t* src = src_base + src_mis;
  std::memset(region, guard, span);
  _mm_sfence();  // the guard stores land before the helper's (write-combined memory)
  CopyToUploadBufferNonTemporal(region + lead, src, size);
  ReadBack(scratch, region, span);
  ++result.cases;
  size_t bad = span;
  uint8_t want = guard;
  for (size_t i = 0; i < lead && bad == span; ++i) {
    if (scratch[i] != guard) {
      bad = i;
    }
  }
  if (bad == span && std::memcmp(scratch + lead, src, size) != 0) {
    for (size_t i = 0; i < size; ++i) {
      if (scratch[lead + i] != src[i]) {
        bad = lead + i;
        want = src[i];
        break;
      }
    }
  }
  for (size_t i = lead + size; i < span && bad == span; ++i) {
    if (scratch[i] != guard) {
      bad = i;
    }
  }
  if (bad == span) {
    return;
  }
  if (result.failures++ < 10) {
    Emit("# FAIL check %s: dst_mis %zu, src_mis %zu, size %zu, guard 0x%02X: byte %lld from dst "
         "is 0x%02X, expected 0x%02X\n",
         mem, dst_mis, src_mis, size, unsigned(guard), (long long)bad - (long long)lead,
         unsigned(scratch[bad]), unsigned(want));
  }
}

// Prints one group's line (PASS only if every case ran and matched) and adds it to total.
void EndGroup(const char* mem, uint8_t guard, const char* what, const CheckResult& group,
              CheckResult& total) {
  const bool pass = group.cases != 0 && group.failures == 0 && group.skipped == 0;
  Emit("# check %s guard 0x%02X %s: %llu cases, %llu failures, %llu skipped: %s\n", mem,
       unsigned(guard), what, group.cases, group.failures, group.skipped, pass ? "PASS" : "FAIL");
  total.cases += group.cases;
  total.failures += group.failures;
  total.skipped += group.skipped;
}

CheckResult RunCheck(const char* mem, uint8_t* region, size_t region_bytes,
                     const uint8_t* src_base, uint8_t* scratch, const size_t* src_mis_list,
                     size_t src_mis_count) {
  static constexpr uint8_t kGuards[] = {0xCD, 0x32};
  static constexpr size_t kLargeSizes[] = {4095,     4096,          4097,        64 * kKiB + 17,
                                           2 * kMiB, 2 * kMiB + 33, 3844 * kKiB};
  static constexpr size_t kLargeDstMis[] = {0, 1, 16, 63};
  static constexpr size_t kLargeSrcMis[] = {0, 1};
  char what[96];
  CheckResult total;
  for (uint8_t guard : kGuards) {
    for (size_t s = 0; s < src_mis_count; ++s) {
      CheckResult group;
      for (size_t dst_mis = 0; dst_mis < 64; ++dst_mis) {
        for (size_t size = 0; size <= 300; ++size) {
          CheckCase(mem, region, src_base, scratch, dst_mis, src_mis_list[s], size, guard,
                    group);
        }
      }
      std::snprintf(what, sizeof(what), "src_mis %zu: dst_mis 0-63 x size 0-300",
                    src_mis_list[s]);
      EndGroup(mem, guard, what, group, total);
    }
    for (size_t size : kLargeSizes) {
      CheckResult group;
      for (size_t src_mis : kLargeSrcMis) {
        for (size_t dst_mis : kLargeDstMis) {
          if (64 + dst_mis + size + 64 > region_bytes || src_mis + size > kCheckBytes) {
            ++group.skipped;
            continue;
          }
          CheckCase(mem, region, src_base, scratch, dst_mis, src_mis, size, guard, group);
        }
      }
      std::snprintf(what, sizeof(what), "size %zu: dst_mis 0/1/16/63 x src_mis 0/1", size);
      EndGroup(mem, guard, what, group, total);
    }
  }
  return total;
}

size_t RoundUpToPage(size_t n) { return (n + kPage - 1) & ~(kPage - 1); }

struct Cursor {
  size_t dst = 0;
  size_t src = 0;
};

// One sample: copies the pattern until at least run_bytes have moved; returns GB/s. The
// cursors advance by whole pages, like the upload pool and the guest pages.
double TimeSample(CopyFn fn, const Pattern& pattern, uint8_t* dst, size_t dst_bytes,
                  const uint8_t* src, size_t src_bytes, Cursor& cursor, size_t run_bytes) {
  size_t pattern_bytes = 0;
  for (size_t c = 0; c < pattern.count; ++c) {
    pattern_bytes += pattern.chunks[c];
  }
  const size_t iterations = std::max<size_t>(1, run_bytes / pattern_bytes);
  const double start = NowSeconds();
  for (size_t i = 0; i < iterations; ++i) {
    for (size_t c = 0; c < pattern.count; ++c) {
      const size_t n = pattern.chunks[c];
      if (cursor.dst + n > dst_bytes) {
        cursor.dst = 0;
      }
      if (cursor.src + n > src_bytes) {
        cursor.src = 0;
      }
      fn(dst + cursor.dst, src + cursor.src, n);
      cursor.dst += RoundUpToPage(n);
      cursor.src += RoundUpToPage(n);
    }
  }
  _mm_sfence();  // drain every variant's write-combining buffers before the stop time
  const double seconds = NowSeconds() - start;
  return double(iterations * pattern_bytes) / seconds * 1e-9;
}

double Median(std::vector<double> values) {
  if (values.empty()) {
    return 0.0;
  }
  std::sort(values.begin(), values.end());
  const size_t n = values.size();
  return n % 2 ? values[n / 2] : 0.5 * (values[n / 2 - 1] + values[n / 2]);
}

void RunRates(const Options& options, uint8_t* upload, uint8_t* wb_dst, const uint8_t* warm_src,
              const uint8_t* cold_src) {
  struct Target {
    const char* name;
    uint8_t* p;
  };
  struct Source {
    const char* name;
    const uint8_t* p;
    size_t bytes;
  };
  const Target targets[] = {{"upload", upload}, {"wb", wb_dst}};
  const Source sources[] = {{"warm", warm_src, kWarmSrcBytes}, {"cold", cold_src, kColdSrcBytes}};
  const size_t run_bytes = options.mib_per_sample * kMiB;
  Emit("dst,src,chunks,variant,samples,mib_per_sample,median_gbs,best_gbs,"
       "median_ms_per_avol_frame\n");
  for (const Target& target : targets) {
    if (!target.p) {
      continue;
    }
    for (const Source& source : sources) {
      for (const Pattern& pattern : kPatterns) {
        Cursor cursor;
        std::vector<double> rates[kNumVariants];
        for (size_t v = 0; v < kNumVariants; ++v) {  // one untimed warm-up sample each
          TimeSample(kVariants[v].fn, pattern, target.p, kUploadBytes, source.p, source.bytes,
                     cursor, run_bytes);
        }
        for (size_t sample = 0; sample < options.samples; ++sample) {
          for (size_t k = 0; k < kNumVariants; ++k) {
            const size_t v = (sample + k) % kNumVariants;
            rates[v].push_back(TimeSample(kVariants[v].fn, pattern, target.p, kUploadBytes,
                                          source.p, source.bytes, cursor, run_bytes));
          }
        }
        for (size_t v = 0; v < kNumVariants; ++v) {
          const double median = Median(rates[v]);
          const double best = *std::max_element(rates[v].begin(), rates[v].end());
          const double ms = median > 0.0 ? double(kAvolFrameBytes) / (median * 1e9) * 1e3 : 0.0;
          Emit("%s,%s,%s,%s,%zu,%zu,%.3f,%.3f,%.3f\n", target.name, source.name, pattern.name,
               kVariants[v].name, options.samples, options.mib_per_sample, median, best, ms);
        }
      }
    }
  }
}

std::string Narrow(const wchar_t* text) {
  const int n = WideCharToMultiByte(CP_UTF8, 0, text, -1, nullptr, 0, nullptr, nullptr);
  if (n <= 1) {
    return std::string();
  }
  std::string out(size_t(n - 1), '\0');
  WideCharToMultiByte(CP_UTF8, 0, text, -1, out.data(), n, nullptr, nullptr);
  return out;
}

const char* PagePropertyName(D3D12_CPU_PAGE_PROPERTY property) {
  switch (property) {
    case D3D12_CPU_PAGE_PROPERTY_UNKNOWN:
      return "UNKNOWN";
    case D3D12_CPU_PAGE_PROPERTY_NOT_AVAILABLE:
      return "NOT_AVAILABLE";
    case D3D12_CPU_PAGE_PROPERTY_WRITE_COMBINE:
      return "WRITE_COMBINE";
    case D3D12_CPU_PAGE_PROPERTY_WRITE_BACK:
      return "WRITE_BACK";
  }
  return "?";
}

const char* PoolName(D3D12_MEMORY_POOL pool) {
  switch (pool) {
    case D3D12_MEMORY_POOL_UNKNOWN:
      return "UNKNOWN";
    case D3D12_MEMORY_POOL_L0:
      return "L0 (system memory)";
    case D3D12_MEMORY_POOL_L1:
      return "L1 (video memory)";
  }
  return "?";
}

void PrintCpu() {
  int regs[4] = {};
  char brand[49] = {};
  __cpuid(regs, int(0x80000000u));
  if (unsigned(regs[0]) >= 0x80000004u) {
    for (int i = 0; i < 3; ++i) {
      __cpuid(regs, int(0x80000002u + unsigned(i)));
      std::memcpy(brand + 16 * i, regs, 16);
    }
  }
  __cpuid(regs, 0);
  const int max_leaf = regs[0];
  int erms = 0;
  int fsrm = 0;
  if (max_leaf >= 7) {
    __cpuidex(regs, 7, 0);
    erms = (regs[1] >> 9) & 1;
    fsrm = (regs[3] >> 4) & 1;
  }
  SYSTEM_INFO info;
  GetSystemInfo(&info);
  Emit("# cpu: %s; ERMS %d, FSRM %d; %lu logical processors\n", brand, erms, fsrm,
       info.dwNumberOfProcessors);
}

struct UploadTarget {
  ComPtr<ID3D12Device> device;
  ComPtr<ID3D12Resource> buffer;
  uint8_t* mapping = nullptr;
};

// Picks the adapter the SDK's D3D12 provider would pick (EnumAdapterByGpuPreference with
// HIGH_PERFORMANCE; EnumAdapters1 if IDXGIFactory6 is missing; software adapters skipped),
// or the index-th hardware adapter in that order. Lists them all, creates the device and an
// 8 MiB upload-heap buffer, and maps it.
bool CreateUploadTarget(int index, UploadTarget& target) {
  ComPtr<IDXGIFactory1> factory;
  if (FAILED(CreateDXGIFactory1(IID_PPV_ARGS(&factory)))) {
    Emit("# d3d12: CreateDXGIFactory1 failed\n");
    return false;
  }
  ComPtr<IDXGIFactory6> factory6;
  factory.As(&factory6);
  std::vector<ComPtr<IDXGIAdapter1>> adapters;
  for (UINT i = 0;; ++i) {
    ComPtr<IDXGIAdapter1> adapter;
    const HRESULT hr = factory6 ? factory6->EnumAdapterByGpuPreference(
                                      i, DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE, IID_PPV_ARGS(&adapter))
                                : factory->EnumAdapters1(i, &adapter);
    if (FAILED(hr)) {
      break;  // DXGI_ERROR_NOT_FOUND after the last adapter
    }
    DXGI_ADAPTER_DESC1 desc;
    if (FAILED(adapter->GetDesc1(&desc)) || (desc.Flags & DXGI_ADAPTER_FLAG_SOFTWARE)) {
      continue;
    }
    adapters.push_back(adapter);
  }
  for (size_t i = 0; i < adapters.size(); ++i) {
    DXGI_ADAPTER_DESC1 desc = {};
    adapters[i]->GetDesc1(&desc);
    Emit("# adapter %zu%s: %s (vendor 0x%04X, %llu MB dedicated)\n", i,
         i == size_t(index) ? " (used)" : "", Narrow(desc.Description).c_str(),
         unsigned(desc.VendorId), (unsigned long long)(desc.DedicatedVideoMemory / kMiB));
  }
  if (index < 0 || size_t(index) >= adapters.size()) {
    Emit("# d3d12: no hardware adapter %d (%zu found)\n", index, adapters.size());
    return false;
  }
  if (FAILED(D3D12CreateDevice(adapters[size_t(index)].Get(), D3D_FEATURE_LEVEL_11_0,
                               IID_PPV_ARGS(&target.device)))) {
    Emit("# d3d12: D3D12CreateDevice failed\n");
    return false;
  }
  D3D12_FEATURE_DATA_ARCHITECTURE architecture = {};
  target.device->CheckFeatureSupport(D3D12_FEATURE_ARCHITECTURE, &architecture,
                                     sizeof(architecture));
  const D3D12_HEAP_PROPERTIES custom =
      target.device->GetCustomHeapProperties(0, D3D12_HEAP_TYPE_UPLOAD);
  Emit("# d3d12: UMA %d, CacheCoherentUMA %d; upload heap: CPU page property %s, pool %s\n",
       int(architecture.UMA), int(architecture.CacheCoherentUMA),
       PagePropertyName(custom.CPUPageProperty), PoolName(custom.MemoryPoolPreference));
  D3D12_HEAP_PROPERTIES heap_properties = {};
  heap_properties.Type = D3D12_HEAP_TYPE_UPLOAD;
  D3D12_RESOURCE_DESC buffer_desc = {};
  buffer_desc.Dimension = D3D12_RESOURCE_DIMENSION_BUFFER;
  buffer_desc.Width = kUploadBytes;
  buffer_desc.Height = 1;
  buffer_desc.DepthOrArraySize = 1;
  buffer_desc.MipLevels = 1;
  buffer_desc.Format = DXGI_FORMAT_UNKNOWN;
  buffer_desc.SampleDesc.Count = 1;
  buffer_desc.Layout = D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
  if (FAILED(target.device->CreateCommittedResource(
          &heap_properties, D3D12_HEAP_FLAG_NONE, &buffer_desc, D3D12_RESOURCE_STATE_GENERIC_READ,
          nullptr, IID_PPV_ARGS(&target.buffer)))) {
    Emit("# d3d12: CreateCommittedResource (upload, 8 MiB) failed\n");
    return false;
  }
  void* mapping = nullptr;
  if (FAILED(target.buffer->Map(0, nullptr, &mapping)) || !mapping) {  // read back by the check
    Emit("# d3d12: Map failed\n");
    return false;
  }
  if (reinterpret_cast<uintptr_t>(mapping) & (kPage - 1)) {
    Emit("# d3d12: the mapping is not page-aligned\n");
    target.buffer->Unmap(0, nullptr);
    return false;
  }
  target.mapping = static_cast<uint8_t*>(mapping);
  return true;
}

bool ParseOptions(int argc, char** argv, Options& options) {
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    const bool has_value = i + 1 < argc;
    if (arg == "--adapter" && has_value) {
      options.adapter = std::atoi(argv[++i]);
    } else if (arg == "--cpu" && has_value) {
      options.cpu = std::atoi(argv[++i]);
    } else if (arg == "--samples" && has_value) {
      options.samples = std::strtoull(argv[++i], nullptr, 10);
    } else if (arg == "--mb" && has_value) {
      options.mib_per_sample = std::strtoull(argv[++i], nullptr, 10);
    } else if (arg == "--csv" && has_value) {
      options.csv_path = argv[++i];
    } else if (arg == "--skip-check") {
      options.skip_check = true;
    } else if (arg == "--skip-rate") {
      options.skip_rate = true;
    } else if (arg == "--check-only") {
      options.check_only = true;
      options.skip_rate = true;
    } else {
      return false;
    }
  }
  return options.samples >= 1 && options.mib_per_sample >= 1 && options.cpu < 64 &&
         !(options.check_only && options.skip_check);
}

}  // namespace

int main(int argc, char** argv) {
  Options options;
  if (!ParseOptions(argc, argv, options)) {
    std::fprintf(stderr,
                 "usage: m1_copybench [--adapter N] [--cpu N] [--samples N] [--mb N] "
                 "[--csv FILE] [--skip-check] [--skip-rate] [--check-only]\n");
    return 2;
  }
  if (options.csv_path && fopen_s(&g_csv, options.csv_path, "w") != 0) {
    std::fprintf(stderr, "cannot write %s\n", options.csv_path);
    return 2;
  }
  if (options.cpu >= 0) {
    SetThreadAffinityMask(GetCurrentThread(), DWORD_PTR(1) << options.cpu);
  }
  SYSTEMTIME now;
  GetLocalTime(&now);
  char mode[64];
  if (options.check_only) {
    std::snprintf(mode, sizeof(mode), "check only, no rate part");
  } else {
    std::snprintf(mode, sizeof(mode), "%zu samples of %zu MiB", options.samples,
                  options.mib_per_sample);
  }
  Emit("# m1_copybench (S4 M1) %04u-%02u-%02u %02u:%02u:%02u; %s; cpu %d\n",
       unsigned(now.wYear), unsigned(now.wMonth), unsigned(now.wDay), unsigned(now.wHour),
       unsigned(now.wMinute), unsigned(now.wSecond), mode, options.cpu);
  PrintCpu();

  // The rate buffers only exist when the rate part runs (cold_src alone is 256 MiB).
  const bool rates = !options.skip_rate;
  uint8_t* check_src = AllocPages(kCheckBytes);
  uint8_t* check_wb = AllocPages(kCheckBytes);
  uint8_t* scratch = AllocPages(kCheckBytes);
  uint8_t* warm_src = rates ? AllocPages(kWarmSrcBytes) : nullptr;
  uint8_t* cold_src = rates ? AllocPages(kColdSrcBytes) : nullptr;
  uint8_t* wb_dst = rates ? AllocPages(kUploadBytes) : nullptr;
  if (!check_src || !check_wb || !scratch || (rates && (!warm_src || !cold_src || !wb_dst))) {
    std::fprintf(stderr, "VirtualAlloc failed\n");
    return 2;
  }
  FillPattern(check_src, kCheckBytes, 1);
  std::memset(check_wb, 0, kCheckBytes);
  std::memset(scratch, 0, kCheckBytes);
  if (rates) {
    FillPattern(warm_src, kWarmSrcBytes, 2);
    FillPattern(cold_src, kColdSrcBytes, 3);
    std::memset(wb_dst, 0, kUploadBytes);
  }

  UploadTarget upload;
  const bool have_upload = CreateUploadTarget(options.adapter, upload);
  if (have_upload) {
    std::memset(upload.mapping, 0, kUploadBytes);  // first touch outside the timed runs
    _mm_sfence();
  }

  unsigned long long failures = 0;  // failed or skipped check cases
  if (!options.skip_check) {
    static constexpr size_t kWbSrcMis[] = {0, 1, 15, 33};
    static constexpr size_t kUploadSrcMis[] = {0, 1};
    double start = NowSeconds();
    const CheckResult wb =
        RunCheck("wb", check_wb, kCheckBytes, check_src, scratch, kWbSrcMis, 4);
    Emit("# check wb: %llu cases, %llu failures, %llu skipped (%.1f s)\n", wb.cases,
         wb.failures, wb.skipped, NowSeconds() - start);
    failures += wb.failures + wb.skipped;
    if (have_upload) {
      start = NowSeconds();
      const CheckResult up = RunCheck("upload", upload.mapping, kUploadBytes, check_src,
                                      scratch, kUploadSrcMis, 2);
      Emit("# check upload: %llu cases, %llu failures, %llu skipped (%.1f s)\n", up.cases,
           up.failures, up.skipped, NowSeconds() - start);
      failures += up.failures + up.skipped;
    }
    if (failures) {
      Emit("# RESULT: FAIL (%llu failed or skipped cases)\n", failures);
    } else if (!have_upload) {
      Emit("# RESULT: FAIL (no upload buffer, so only normal memory was checked)\n");
    } else {
      Emit("# RESULT: PASS (normal memory and the upload buffer)\n");
    }
  }
  if (!options.skip_rate) {
    RunRates(options, have_upload ? upload.mapping : nullptr, wb_dst, warm_src, cold_src);
  }

  if (have_upload) {
    upload.buffer->Unmap(0, nullptr);
  }
  for (uint8_t* p : {check_src, check_wb, scratch, warm_src, cold_src, wb_dst}) {
    if (p) {
      VirtualFree(p, 0, MEM_RELEASE);
    }
  }
  if (g_csv) {
    std::fclose(g_csv);
  }
  if (failures) {
    return 1;
  }
  return have_upload ? 0 : 2;
}
