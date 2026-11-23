// B5: cost of a log call, OLD (pristine macros) vs NEW (section D level floor,
// cvar log_level_gate on), with the real header-only spdlog/fmt from the SDK's
// thirdparty tree and null_sink_mt loggers.
//   disabled trace  : all loggers at warn, REXLOG trace call (floor = warn)
//   filtered        : another category at trace (floor = trace), so the call
//                     passes the floor and is rejected by should_log(). This is
//                     also the path every disabled call takes with
//                     log_level_gate=false (floor stays 0 = trace).
//   enabled warn    : warn call that formats and reaches null_sink_mt
// 1 and 2 threads (2 threads run the same loop at the same time; ns/call is
// per thread).
//
// Ablation mode (`ablate`, 1 thread). Only v1' is SDK code (since 19:54):
//   v0  = superseded SDK draft ([[unlikely]] on the floor test + GetLoggerRawAndBindFloor)
//   v1  = superseded SDK macro 19:27-19:54 (v0 without [[unlikely]]; bind before should_log)
//   v1' = NEW as in the SDK working tree now (no hint, GetLoggerRaw directly,
//         BindLogLevelFloor only on a logged line)
//   v2  = [[unlikely]] kept, direct GetLoggerRaw(cat) (no bound-flag load)
//   v3  = v1 + direct GetLoggerRaw (no hint, no bind)
//   v4  = v3 with a one-load floor: per-module constinit atomic<int> compared
//         directly (models a registration scheme; no pointer, no bind)
//   v4h = v2 with the one-load floor ([[unlikely]] kept)
//   v5  = v0 with the category function declared __forceinline
// Diagnosis that motivated it: under [[unlikely]] clang treats the block as a
// cold call site and does not inline the category function (out-of-line call
// with an sret return), which was the extra cost of v0 in the filtered case.
//
// Usage: b5_log.exe [runs=5] [disabled_calls=100000000] [ablate | only=<case>[,<case>...]]
//   cases: 0 disabled trace, 1 disabled debug, 2 filtered, 3 enabled warn
#include "b5_log_shared.h"
#include "common.h"

#include <array>
#include <atomic>
#include <cstdlib>
#include <cstring>
#include <thread>

REXB_DEFINE_CATEGORY(fs)
REXB_DEFINE_CATEGORY(gpu)

// Bench-only: same as REXB_DEFINE_CATEGORY but forced inline (v5).
namespace rexb::log {
__forceinline ::rexb::LogCategoryId fs_fi() {
  static const ::rexb::LogCategoryId id = ::rexb::RegisterLogCategory("fs_fi");
  return id;
}
}  // namespace rexb::log

namespace b12abl {
// Bench-only per-module floor copy (v4/v4h), kept equal to the shared floor.
inline constinit std::atomic<int> g_floor_copy{0};

// Bench-only copy of api.h's GetLoggerRawAndBindFloor (SDK 19:27-19:54, removed
// at 19:54), used by v0, v1 and v5.
inline spdlog::logger* GetLoggerRawAndBindFloorV1(::rexb::LogCategoryId category) {
  if (!::rexb::detail::g_log_level_floor_bound.load(std::memory_order_relaxed)) [[unlikely]] {
    ::rexb::detail::g_log_level_floor_ptr.store(::rexb::detail::SharedLogLevelFloorImport(),
                                                std::memory_order_relaxed);
    ::rexb::detail::g_log_level_floor_bound.store(true, std::memory_order_relaxed);
  }
  return ::rexb::GetLoggerRawImport(category);
}
}  // namespace b12abl

#define B12_LOG_BODY(get, cat, lvl, ...)                                                     \
  auto* rex_log_ptr_ = get(cat);                                                             \
  if (rex_log_ptr_ && rex_log_ptr_->should_log(lvl))                                         \
    rex_log_ptr_->log(spdlog::source_loc{__FILE__, __LINE__, __FUNCTION__}, lvl, __VA_ARGS__)

#define B12_FLOOR_PTR(lvl) ::rexb::detail::LogLevelMayBeEnabled(lvl)
#define B12_FLOOR_ONE(lvl) ((lvl) >= ::b12abl::g_floor_copy.load(std::memory_order_relaxed))
#define B12_GET_BIND ::b12abl::GetLoggerRawAndBindFloorV1
#define B12_GET_RAW ::rexb::GetLoggerRawImport

// v0: superseded SDK draft (hint, bind).  v1: SDK 19:27-19:54 (no hint, bind).
// v1' is REXB_LOG_IMPL_NEW (no hint, raw, bind only on a logged line).
// v2: hint, raw.  v3: no hint, raw.  v4: one load, no hint, raw.  v4h: one load, hint, raw.
#define B12_LOG_V0(cat, lvl, ...) do { if (B12_FLOOR_PTR(lvl)) [[unlikely]] { B12_LOG_BODY(B12_GET_BIND, cat, lvl, __VA_ARGS__); } } while (0)
#define B12_LOG_V1(cat, lvl, ...) do { if (B12_FLOOR_PTR(lvl)) { B12_LOG_BODY(B12_GET_BIND, cat, lvl, __VA_ARGS__); } } while (0)
#define B12_LOG_V2(cat, lvl, ...) do { if (B12_FLOOR_PTR(lvl)) [[unlikely]] { B12_LOG_BODY(B12_GET_RAW, cat, lvl, __VA_ARGS__); } } while (0)
#define B12_LOG_V3(cat, lvl, ...) do { if (B12_FLOOR_PTR(lvl)) { B12_LOG_BODY(B12_GET_RAW, cat, lvl, __VA_ARGS__); } } while (0)
#define B12_LOG_V4(cat, lvl, ...) do { if (B12_FLOOR_ONE(lvl)) { B12_LOG_BODY(B12_GET_RAW, cat, lvl, __VA_ARGS__); } } while (0)
#define B12_LOG_V4H(cat, lvl, ...) do { if (B12_FLOOR_ONE(lvl)) [[unlikely]] { B12_LOG_BODY(B12_GET_RAW, cat, lvl, __VA_ARGS__); } } while (0)

namespace {

using b12::qpc_seconds;

enum Case { kDisabledTrace, kDisabledDebug, kFiltered, kEnabledWarn, kNumCases };
const char* kCaseNames[kNumCases] = {"disabled trace (level=warn)", "disabled debug (level=warn)",
                                     "trace filtered by logger (floor=trace)",
                                     "enabled warn -> null_sink_mt"};

enum Variant { kOld, kV0, kV1, kV1p, kV2, kV3, kV4, kV4h, kV5, kNumVariants };
const char* kVariantNames[kNumVariants] = {"OLD", "v0 (draft)", "v1 (SDK 19:27-19:54)", "v1' = NEW (SDK 19:54)",
                                           "v2", "v3", "v4", "v4h", "v5"};
constexpr int kNew = kV1p;  // the SDK working-tree macro

#define B12_FMT "read {} bytes at {:X}", i, 42
#define B12_LOG_VARIANT(V, LVL)                                                         \
  do {                                                                                  \
    if constexpr (V == kOld) REXB_LOG_IMPL_OLD(::rexb::log::fs(), LVL, B12_FMT);        \
    else if constexpr (V == kV0) B12_LOG_V0(::rexb::log::fs(), LVL, B12_FMT);           \
    else if constexpr (V == kV1) B12_LOG_V1(::rexb::log::fs(), LVL, B12_FMT);           \
    else if constexpr (V == kV1p) REXB_LOG_IMPL_NEW(::rexb::log::fs(), LVL, B12_FMT);   \
    else if constexpr (V == kV2) B12_LOG_V2(::rexb::log::fs(), LVL, B12_FMT);           \
    else if constexpr (V == kV3) B12_LOG_V3(::rexb::log::fs(), LVL, B12_FMT);           \
    else if constexpr (V == kV4) B12_LOG_V4(::rexb::log::fs(), LVL, B12_FMT);           \
    else if constexpr (V == kV4h) B12_LOG_V4H(::rexb::log::fs(), LVL, B12_FMT);         \
    else B12_LOG_V0(::rexb::log::fs_fi(), LVL, B12_FMT);                                \
  } while (0)

template <int kVariant, int kCase>
__declspec(noinline) void loop(uint64_t n) {
  for (uint64_t i = 0; i < n; ++i) {
    if constexpr (kCase == kDisabledTrace || kCase == kFiltered) {
      B12_LOG_VARIANT(kVariant, spdlog::level::trace);
    } else if constexpr (kCase == kDisabledDebug) {
      B12_LOG_VARIANT(kVariant, spdlog::level::debug);
    } else {
      B12_LOG_VARIANT(kVariant, spdlog::level::warn);
    }
  }
}

using LoopFn = void (*)(uint64_t);
template <int V>
constexpr std::array<LoopFn, kNumCases> row() {
  return {loop<V, 0>, loop<V, 1>, loop<V, 2>, loop<V, 3>};
}
LoopFn pick(int v, int c) {
  static const std::array<LoopFn, kNumCases> table[kNumVariants] = {
      row<0>(), row<1>(), row<2>(), row<3>(), row<4>(), row<5>(), row<6>(), row<7>(), row<8>()};
  return table[v][c];
}

// ns per call per thread (mean over threads).
double timed(LoopFn fn, uint64_t n, int nthreads) {
  if (nthreads == 1) {
    const double t0 = qpc_seconds();
    fn(n);
    return (qpc_seconds() - t0) * 1e9 / double(n);
  }
  std::atomic<int> ready{0};
  std::atomic<bool> go{false};
  std::vector<double> ns(nthreads);
  std::vector<std::thread> th;
  for (int t = 0; t < nthreads; ++t) {
    th.emplace_back([&, t] {
      ready.fetch_add(1);
      while (!go.load(std::memory_order_acquire)) {
      }
      const double t0 = qpc_seconds();
      fn(n);
      ns[t] = (qpc_seconds() - t0) * 1e9 / double(n);
    });
  }
  while (ready.load() != nthreads) {
  }
  go.store(true, std::memory_order_release);
  for (auto& x : th) x.join();
  double sum = 0;
  for (double x : ns) sum += x;
  return sum / nthreads;
}

void set_case_levels(int c) {
  // fs, fs_fi and gpu at warn; for kFiltered gpu at trace lowers the floor to trace.
  rexb::BenchSetCategoryLevel(rexb::log::gpu(), c == kFiltered ? spdlog::level::trace
                                                               : spdlog::level::warn);
  b12abl::g_floor_copy.store(rexb::detail::g_log_level_floor.load(std::memory_order_relaxed),
                             std::memory_order_relaxed);
}

void run_ablation(int runs, uint64_t ndis) {
  std::printf("\n## Ablation (v1-v5 are bench-only variants; 1 thread; ns/call)\n");
  std::printf("| case | calls | floor |");
  for (int v = 0; v < kNumVariants; ++v) std::printf(" %s |", kVariantNames[v]);
  std::printf(" load median |\n|---|---:|---:|");
  for (int v = 0; v < kNumVariants; ++v) std::printf("---|");
  std::printf("---:|\n");
  for (int c : {int(kDisabledTrace), int(kFiltered)}) {
    set_case_levels(c);
    const uint64_t n = c == kFiltered ? ndis / 2 : ndis;
    std::vector<double> r[kNumVariants], ld;
    for (int v = 0; v < kNumVariants; ++v) timed(pick(v, c), n / 20, 1);  // warm-up
    for (int k = 0; k < runs; ++k) {
      ld.push_back(100.0 * b12::sample_machine_load(30));
      // Rotate the start variant per run so no variant always runs first.
      for (int j = 0; j < kNumVariants; ++j) {
        const int v = (j + k) % kNumVariants;
        r[v].push_back(timed(pick(v, c), n, 1));
      }
    }
    std::printf("| %s | %llu | %d |", kCaseNames[c], (unsigned long long)n,
                rexb::detail::g_log_level_floor.load());
    for (int v = 0; v < kNumVariants; ++v) {
      const b12::Summary s = b12::summarize(r[v]);
      std::printf(" %.2f [%.2f-%.2f] |", s.median, s.min, s.max);
    }
    std::printf(" %.0f%% |\n", b12::summarize(ld).median);
  }
  std::printf("\n(median [min-max] of n=%d runs, variants interleaved with rotating order, after a warm-up)\n",
              runs);
}

}  // namespace

int main(int argc, char** argv) {
  const int runs = argc > 1 ? std::atoi(argv[1]) : 5;
  const uint64_t ndis = argc > 2 ? std::strtoull(argv[2], nullptr, 0) : 100000000ull;
  const bool ablate = argc > 3 && std::strcmp(argv[3], "ablate") == 0;
  setvbuf(stdout, nullptr, _IONBF, 0);
  b12::print_machine_header(ablate ? "B5 logging ablation" : "B5 logging OLD vs NEW");

  // InitLogging registers the built-in categories up front when the gate is on.
  (void)rexb::log::fs();
  (void)rexb::log::fs_fi();
  (void)rexb::log::gpu();
  rexb::BenchInitLogging(spdlog::level::warn, true);

  if (ablate) {
    run_ablation(runs, ndis);
    return 0;
  }

  const uint64_t n_of[kNumCases] = {ndis, ndis, ndis / 2, ndis / 50};
  bool want[kNumCases] = {true, true, true, true};
  if (argc > 3 && std::strncmp(argv[3], "only=", 5) == 0) {
    for (bool& w : want) w = false;
    for (const char* p = argv[3] + 5; *p; ++p)
      if (*p >= '0' && *p < '0' + kNumCases) want[*p - '0'] = true;
  }
  std::printf("| case | threads | calls/thread | OLD ns/call median [min-max] | NEW ns/call median [min-max] | OLD/NEW | load median |\n");
  std::printf("|---|---:|---:|---|---|---:|---:|\n");
  for (int c = 0; c < kNumCases; ++c) {
    if (!want[c]) continue;
    set_case_levels(c);
    for (int nt : {1, 2}) {
      std::vector<double> o, nw, ld;
      timed(pick(kOld, c), n_of[c] / 20, nt);  // warm-up
      timed(pick(kNew, c), n_of[c] / 20, nt);
      for (int r = 0; r < runs; ++r) {
        ld.push_back(100.0 * b12::sample_machine_load(30));
        o.push_back(timed(pick(kOld, c), n_of[c], nt));
        nw.push_back(timed(pick(kNew, c), n_of[c], nt));
      }
      const b12::Summary so = b12::summarize(o), sn = b12::summarize(nw), sl = b12::summarize(ld);
      std::printf("| %s | %d | %llu | %.2f [%.2f-%.2f] | %.2f [%.2f-%.2f] | %.1fx | %.0f%% |\n",
                  kCaseNames[c], nt, (unsigned long long)n_of[c], so.median, so.min, so.max,
                  sn.median, sn.min, sn.max, so.median / sn.median, sl.median);
    }
  }
  std::printf("\n(n=%d runs per row, OLD and NEW interleaved, after a warm-up)\n", runs);
  return 0;
}
