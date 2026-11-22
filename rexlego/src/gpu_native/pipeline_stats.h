#pragma once

// Opt-in PSO instrumentation for the native renderer (task #5, report #8).
//
// LEGO_NATIVE_PSO_STATS=1 turns it on; StartPipelineLibrary reads it once.
// While it is off, every hook site costs one relaxed load of g_enabled and one
// predictable branch, and nothing below runs. While it is on, it counts and
// times:
//  - Plume cache lookups (warm, driver-library hit, miss), waits for the
//    library mutex and ID3D12PipelineLibrary loads;
//  - draw-path driver compiles: the time from a lookup miss to the store()
//    Plume makes on the same thread once CreateGraphicsPipelineState returns;
//  - auxiliary pipelines, the cache open, startup preparation and autosaves;
//  - async compiles (pipeline_async.h) when that toggle is on;
//  - every present, so blocking compiles can be matched to frame hitches, plus
//    a per-minute table for the "FPS improves the longer you play" symptom.
// The summary is logged by StopPipelineLibrary, by LogPipelineStats(), and
// when <exe>/cache/pso-stats.now appears (checked every 2 s on the present
// thread, then deleted). LEGO_NATIVE_PSO_STATS_INTERVAL=<seconds> also logs a
// one-line delta at that interval (unset or 0: never).

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <iterator>
#include <mutex>
#include <system_error>
#include <vector>

#include <rex/logging.h>

namespace legodimensions::gpu_native::pso_stats {

inline std::atomic<bool> g_enabled{false};

// The whole cost of the instrumentation while it is off.
inline bool Enabled() { return g_enabled.load(std::memory_order_relaxed); }

inline uint64_t Nanos() {
  return uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(
                      std::chrono::steady_clock::now().time_since_epoch())
                      .count());
}
inline double Millis(uint64_t nanos) { return double(nanos) / 1e6; }
inline double Average(uint64_t total, uint64_t count) { return count ? double(total) / double(count) : 0.0; }

struct Counter {
  std::atomic<uint64_t> value{0};
  void Add(uint64_t amount = 1) { value.fetch_add(amount, std::memory_order_relaxed); }
  void Max(uint64_t candidate) {
    uint64_t current = value.load(std::memory_order_relaxed);
    while (candidate > current &&
           !value.compare_exchange_weak(current, candidate, std::memory_order_relaxed)) {
    }
  }
  void Set(uint64_t amount) { value.store(amount, std::memory_order_relaxed); }
  uint64_t Get() const { return value.load(std::memory_order_relaxed); }
};

// Which thread a compile ran on. The present thread marks itself in OnFrame()
// and async pool threads mark themselves. Everything else (the thread that
// issues draws, if it is not the present thread, and startup code) is "other".
enum ThreadKind : uint8_t { kOtherThread, kPresentThread, kAsyncThread, kThreadKinds };
inline thread_local ThreadKind t_thread_kind = kOtherThread;
// Set by a lookup miss and consumed by the store() Plume makes after compiling.
inline thread_local uint64_t t_miss_time = 0;

inline constexpr std::size_t kCompileBuckets = 6;  // <1, 1-4, 4-16, 16-64, 64-256, >=256 ms
inline constexpr std::size_t kFrameBuckets = 6;    // <=16.7, <=33.3, <=50, <=100, <=250, >250 ms
inline constexpr uint64_t kHitchNs = 50'000'000;
// A frame during which at least this much blocking compile time finished.
inline constexpr uint64_t kCompileFrameNs = 4'000'000;
inline constexpr uint64_t kMinuteNs = 60'000'000'000ull;
inline constexpr std::size_t kMinuteRows = 240;  // the last four hours
inline constexpr uint64_t kTriggerCheckNs = 2'000'000'000ull;

inline std::size_t CompileBucket(uint64_t nanos) {
  constexpr uint64_t kBounds[] = {1'000'000, 4'000'000, 16'000'000, 64'000'000, 256'000'000};
  std::size_t bucket = 0;
  while (bucket < std::size(kBounds) && nanos >= kBounds[bucket]) ++bucket;
  return bucket;
}

inline std::size_t FrameBucket(uint64_t nanos) {
  constexpr uint64_t kBounds[] = {16'700'000, 33'300'000, 50'000'000, 100'000'000, 250'000'000};
  std::size_t bucket = 0;
  while (bucket < std::size(kBounds) && nanos > kBounds[bucket]) ++bucket;
  return bucket;
}

struct Totals {
  // Plume lookups: one load() call per pipeline Plume creates.
  Counter lookups, warm_hits, library_hits, misses;
  Counter lookup_ns, max_lookup_ns;
  Counter lock_wait_ns, max_lock_wait_ns, lock_waits_over_1ms;
  Counter library_loads, library_load_ns, max_library_load_ns;
  // Draw-path driver compiles, timed from the lookup miss to store().
  Counter compiles, compile_ns, max_compile_ns, untimed_stores;
  std::array<Counter, kCompileBuckets> compile_histogram;
  std::array<Counter, kThreadKinds> thread_compiles, thread_compile_ns;
  // Compile time spent outside async threads: the part that can delay a frame.
  Counter blocking_compile_ns;
  Counter stores, store_ns, max_store_ns;
  // CreateAuxiliaryPipeline.
  Counter aux_requests, aux_hits, aux_compiles, aux_failed, aux_compile_ns, max_aux_compile_ns;
  // Autosaves and the final save.
  Counter saves, save_failed, save_postponed, save_bytes, save_lock_ns, save_max_lock_ns;
  Counter save_copy_ns, save_alloc_ns, save_write_ns, save_retries, save_under_lock;
  // pipeline_async.h.
  Counter async_posted, async_ready, async_failed, async_skipped_draws;
  Counter async_waits, async_wait_ns, async_timeouts;
};
inline Totals g_totals;

enum class CacheState : uint8_t {
  kUnknown,       // StartPipelineLibrary has not run
  kDisabled,      // LEGO_NATIVE_PSO_CACHE=0
  kCaptureLayer,  // RenderDoc or another capture layer
  kUnavailable,   // CreatePipelineLibrary failed
  kNoFile,        // no usable file: started empty
  kLoaded,        // the driver accepted the file
  kRejected,      // the driver rejected the file: started empty
};

inline const char* CacheStateName(CacheState state) {
  switch (state) {
    case CacheState::kDisabled: return "off (LEGO_NATIVE_PSO_CACHE=0)";
    case CacheState::kCaptureLayer: return "skipped (capture layer)";
    case CacheState::kUnavailable: return "unavailable";
    case CacheState::kNoFile: return "new (no usable file)";
    case CacheState::kLoaded: return "loaded";
    case CacheState::kRejected: return "rebuilt (file rejected by the driver)";
    default: return "not started";
  }
}

struct Startup {
  std::atomic<CacheState> cache{CacheState::kUnknown};
  Counter file_bytes, read_ns, create_ns;
  Counter prepared, loaded, compiled, failed, resident, threads;
  Counter prepare_ns, load_ns, compile_ns, max_compile_ns;
};
inline Startup g_startup;

inline void OnCacheState(CacheState state) { g_startup.cache.store(state, std::memory_order_relaxed); }

inline void OnOpen(CacheState state, uint64_t file_bytes, uint64_t read_ns, uint64_t create_ns) {
  OnCacheState(state);
  g_startup.file_bytes.Set(file_bytes);
  g_startup.read_ns.Set(read_ns);
  g_startup.create_ns.Set(create_ns);
}

struct PrepareSample {
  uint64_t loaded = 0, compiled = 0, failed = 0, resident = 0, threads = 1;
  uint64_t elapsed_ns = 0, load_ns = 0, compile_ns = 0, max_compile_ns = 0;
};

inline void OnPrepare(const PrepareSample& sample) {
  auto& s = g_startup;
  s.prepared.Set(1);
  s.loaded.Set(sample.loaded);
  s.compiled.Set(sample.compiled);
  s.failed.Set(sample.failed);
  s.resident.Set(sample.resident);
  s.threads.Set(sample.threads);
  s.prepare_ns.Set(sample.elapsed_ns);
  s.load_ns.Set(sample.load_ns);
  s.compile_ns.Set(sample.compile_ns);
  s.max_compile_ns.Set(sample.max_compile_ns);
}

enum class Lookup : uint8_t { kWarm, kLibrary, kMiss };

struct LookupTimes {
  uint64_t start = 0;       // load() entry, before the name hash
  uint64_t lock_begin = 0;  // before the library mutex
  uint64_t locked = 0;      // mutex acquired
  uint64_t load_begin = 0;  // ID3D12PipelineLibrary::LoadGraphicsPipeline, when it ran
  uint64_t load_end = 0;
};

inline void OnLookup(Lookup result, const LookupTimes& times) {
  const uint64_t end = Nanos();
  auto& t = g_totals;
  t.lookups.Add();
  if (result == Lookup::kMiss) {
    t.misses.Add();
    t_miss_time = end;
  } else {
    (result == Lookup::kWarm ? t.warm_hits : t.library_hits).Add();
    t_miss_time = 0;
  }
  t.lookup_ns.Add(end - times.start);
  t.max_lookup_ns.Max(end - times.start);
  const uint64_t wait = times.locked - times.lock_begin;
  t.lock_wait_ns.Add(wait);
  t.max_lock_wait_ns.Max(wait);
  if (wait >= 1'000'000) t.lock_waits_over_1ms.Add();
  if (times.load_end) {
    const uint64_t load = times.load_end - times.load_begin;
    t.library_loads.Add();
    t.library_load_ns.Add(load);
    t.max_library_load_ns.Max(load);
  }
}

// A lookup with no disk library behind it (cache off, capture layer, or the
// library could not be created).
inline void OnUncachedLookup() {
  g_totals.lookups.Add();
  g_totals.misses.Add();
  t_miss_time = Nanos();
}

inline void RecordCompile(uint64_t nanos, ThreadKind kind) {
  auto& t = g_totals;
  t.compiles.Add();
  t.compile_ns.Add(nanos);
  t.max_compile_ns.Max(nanos);
  t.compile_histogram[CompileBucket(nanos)].Add();
  t.thread_compiles[kind].Add();
  t.thread_compile_ns[kind].Add(nanos);
  if (kind != kAsyncThread) t.blocking_compile_ns.Add(nanos);
}

// store() entry: Plume has just compiled the pipeline this thread missed on.
// Returns the entry time for OnStored().
inline uint64_t OnStore() {
  const uint64_t now = Nanos();
  if (t_miss_time && now >= t_miss_time)
    RecordCompile(now - t_miss_time, t_thread_kind);
  else
    g_totals.untimed_stores.Add();
  t_miss_time = 0;
  return now;
}

inline void OnStored(uint64_t begin) {
  const uint64_t nanos = Nanos() - begin;
  g_totals.stores.Add();
  g_totals.store_ns.Add(nanos);
  g_totals.max_store_ns.Max(nanos);
}

// hit: the library had it. Otherwise compile_ns is the CreateGraphicsPipelineState
// time, whether or not it succeeded.
inline void OnAuxiliary(bool hit, bool ok, uint64_t compile_ns) {
  auto& t = g_totals;
  t.aux_requests.Add();
  if (hit) {
    t.aux_hits.Add();
    return;
  }
  (ok ? t.aux_compiles : t.aux_failed).Add();
  t.aux_compile_ns.Add(compile_ns);
  t.max_aux_compile_ns.Max(compile_ns);
  if (t_thread_kind != kAsyncThread) t.blocking_compile_ns.Add(compile_ns);
}

struct SaveSample {
  uint64_t lock_ns = 0, max_lock_ns = 0, copy_ns = 0, alloc_ns = 0, retries = 0;
  bool under_lock = false;
};

inline void OnSaveSnapshot(const SaveSample& sample) {
  auto& t = g_totals;
  t.save_lock_ns.Add(sample.lock_ns);
  t.save_max_lock_ns.Max(sample.max_lock_ns);
  t.save_copy_ns.Add(sample.copy_ns);
  t.save_alloc_ns.Add(sample.alloc_ns);
  t.save_retries.Add(sample.retries);
  if (sample.under_lock) t.save_under_lock.Add();
}

inline void OnSaveWritten(bool ok, uint64_t bytes, uint64_t write_ns) {
  auto& t = g_totals;
  (ok ? t.saves : t.save_failed).Add();
  if (ok) t.save_bytes.Add(bytes);
  t.save_write_ns.Add(write_ns);
}

inline void OnSavePostponed() { g_totals.save_postponed.Add(); }

inline void OnAsyncPosted() { g_totals.async_posted.Add(); }
inline void OnAsyncFinished(bool ok) { (ok ? g_totals.async_ready : g_totals.async_failed).Add(); }
inline void OnAsyncSkippedDraw() { g_totals.async_skipped_draws.Add(); }
inline void OnAsyncWait(uint64_t nanos, bool timed_out) {
  g_totals.async_waits.Add();
  g_totals.async_wait_ns.Add(nanos);
  if (timed_out) g_totals.async_timeouts.Add();
}

// Counter values at the start of a reporting period.
struct Marks {
  uint64_t compiles = 0, compile_ns = 0, blocking_ns = 0, misses = 0, hits = 0, skipped = 0;
};

inline Marks TakeMarks() {
  const auto& t = g_totals;
  Marks marks;
  marks.compiles = t.compiles.Get() + t.aux_compiles.Get() + t.aux_failed.Get();
  marks.compile_ns = t.compile_ns.Get() + t.aux_compile_ns.Get();
  marks.blocking_ns = t.blocking_compile_ns.Get();
  marks.misses = t.misses.Get();
  marks.hits = t.warm_hits.Get() + t.library_hits.Get();
  marks.skipped = t.async_skipped_draws.Get();
  return marks;
}

struct Period {
  uint64_t start_ns = 0, frames = 0, worst_ns = 0, hitches = 0, compile_frames = 0;
  Marks marks;
  void Reset(uint64_t now) {
    *this = {};
    start_ns = now;
    marks = TakeMarks();
  }
  void Add(uint64_t frame_ns, bool hitch, bool compile_frame) {
    ++frames;
    worst_ns = std::max(worst_ns, frame_ns);
    hitches += hitch;
    compile_frames += compile_frame;
  }
};

struct PeriodRow {
  uint64_t index = 0;  // minute number, counted from the first frame
  uint64_t frames = 0, hitches = 0, compile_frames = 0, compiles = 0, misses = 0, hits = 0, skipped = 0;
  double seconds = 0, worst_ms = 0, compile_ms = 0, blocking_ms = 0;
  double Fps() const { return seconds > 0 ? double(frames) / seconds : 0.0; }
};

inline PeriodRow MakeRow(const Period& period, uint64_t now, uint64_t index) {
  const Marks current = TakeMarks();
  PeriodRow row;
  row.index = index;
  row.frames = period.frames;
  row.hitches = period.hitches;
  row.compile_frames = period.compile_frames;
  row.compiles = current.compiles - period.marks.compiles;
  row.misses = current.misses - period.marks.misses;
  row.hits = current.hits - period.marks.hits;
  row.skipped = current.skipped - period.marks.skipped;
  row.seconds = now > period.start_ns ? double(now - period.start_ns) / 1e9 : 0.0;
  row.worst_ms = Millis(period.worst_ns);
  row.compile_ms = Millis(current.compile_ns - period.marks.compile_ns);
  row.blocking_ms = Millis(current.blocking_ns - period.marks.blocking_ns);
  return row;
}

struct FrameState {
  std::mutex mutex;
  uint64_t first_ns = 0, last_ns = 0, frames = 0, worst_ns = 0;
  uint64_t hitches = 0, compile_frames = 0, compile_hitches = 0, last_blocking_ns = 0;
  std::array<uint64_t, kFrameBuckets> histogram{};
  Period minute, interval;
  uint64_t minute_index = 0;
  std::vector<PeriodRow> rows;  // ring: row i lives at rows[i % kMinuteRows]
  uint64_t interval_ns = 0;
  std::filesystem::path trigger;
  uint64_t next_trigger_ns = 0;
};
inline FrameState g_frames;

inline std::mutex g_log_mutex;
inline std::atomic<bool> g_exit_logged{false};

inline void LogPeriod(const PeriodRow& row) {
  REXLOG_INFO(
      "Native GPU PSO stats, last {:.0f} s: {} frames, {:.1f} fps, worst {:.1f} ms, {} hitches, "
      "{} compile frames; {} compiles, {:.1f} ms ({:.1f} ms blocking), {} misses, {} hits, "
      "{} skipped draws",
      row.seconds, row.frames, row.Fps(), row.worst_ms, row.hitches, row.compile_frames, row.compiles,
      row.compile_ms, row.blocking_ms, row.misses, row.hits, row.skipped);
}

inline void LogRow(const PeriodRow& row, const char* note) {
  REXLOG_INFO("PSO minute {:>4}: {:>6} {:>6.1f} {:>8.1f} {:>4} {:>4} {:>5} {:>8.1f} {:>8.1f} {:>5} {:>6} {:>5}{}",
              row.index, row.frames, row.Fps(), row.worst_ms, row.hitches, row.compile_frames,
              row.compiles, row.compile_ms, row.blocking_ms, row.misses, row.hits, row.skipped, note);
}

// Logs everything counted so far. Safe from any thread; never called with
// the library mutex held.
inline void LogSummary(const char* reason) {
  std::lock_guard log_lock(g_log_mutex);
  uint64_t first_ns, last_ns, frames, worst_ns, hitches, compile_frames, compile_hitches;
  std::array<uint64_t, kFrameBuckets> histogram;
  std::vector<PeriodRow> rows;
  PeriodRow partial;
  bool have_partial;
  {
    std::lock_guard lock(g_frames.mutex);
    const auto& f = g_frames;
    first_ns = f.first_ns;
    last_ns = f.last_ns;
    frames = f.frames;
    worst_ns = f.worst_ns;
    hitches = f.hitches;
    compile_frames = f.compile_frames;
    compile_hitches = f.compile_hitches;
    histogram = f.histogram;
    // Oldest first.
    const std::size_t count = f.rows.size();
    const std::size_t oldest = count < kMinuteRows ? 0 : std::size_t(f.minute_index % kMinuteRows);
    rows.reserve(count);
    for (std::size_t i = 0; i < count; ++i) rows.push_back(f.rows[(oldest + i) % count]);
    have_partial = f.minute.frames != 0;
    if (have_partial) partial = MakeRow(f.minute, f.last_ns, f.minute_index);
  }
  const auto& t = g_totals;
  const auto& s = g_startup;
  const double seconds = last_ns > first_ns ? double(last_ns - first_ns) / 1e9 : 0.0;
  REXLOG_INFO("Native GPU PSO stats ({}): {} frames over {:.1f} s", reason, frames, seconds);
  REXLOG_INFO("PSO startup: cache {}, file {} bytes, read {:.1f} ms, library create {:.1f} ms",
              CacheStateName(s.cache.load(std::memory_order_relaxed)), s.file_bytes.Get(),
              Millis(s.read_ns.Get()), Millis(s.create_ns.Get()));
  if (s.prepared.Get())
    REXLOG_INFO(
        "PSO startup preparation: loaded {}, compiled {}, failed {}, resident {}, threads {}, {:.1f} ms "
        "(library loads {:.1f} ms, compiles {:.1f} ms, worst compile {:.1f} ms)",
        s.loaded.Get(), s.compiled.Get(), s.failed.Get(), s.resident.Get(), s.threads.Get(),
        Millis(s.prepare_ns.Get()), Millis(s.load_ns.Get()), Millis(s.compile_ns.Get()),
        Millis(s.max_compile_ns.Get()));
  REXLOG_INFO(
      "PSO lookups: {} (warm {}, library {}, miss {}), avg {:.3f} ms, worst {:.3f} ms; mutex wait "
      "{:.1f} ms in total, worst {:.3f} ms, {} waits of 1 ms or more; library loads {}, avg {:.3f} ms, "
      "worst {:.3f} ms",
      t.lookups.Get(), t.warm_hits.Get(), t.library_hits.Get(), t.misses.Get(),
      Average(t.lookup_ns.Get(), t.lookups.Get()) / 1e6, Millis(t.max_lookup_ns.Get()),
      Millis(t.lock_wait_ns.Get()), Millis(t.max_lock_wait_ns.Get()), t.lock_waits_over_1ms.Get(),
      t.library_loads.Get(), Average(t.library_load_ns.Get(), t.library_loads.Get()) / 1e6,
      Millis(t.max_library_load_ns.Get()));
  REXLOG_INFO(
      "PSO compiles: {} taking {:.1f} ms (avg {:.2f} ms, worst {:.1f} ms); <1 ms {}, 1-4 {}, 4-16 {}, "
      "16-64 {}, 64-256 {}, >=256 {}; untimed stores {}; store() avg {:.3f} ms, worst {:.3f} ms",
      t.compiles.Get(), Millis(t.compile_ns.Get()), Average(t.compile_ns.Get(), t.compiles.Get()) / 1e6,
      Millis(t.max_compile_ns.Get()), t.compile_histogram[0].Get(), t.compile_histogram[1].Get(),
      t.compile_histogram[2].Get(), t.compile_histogram[3].Get(), t.compile_histogram[4].Get(),
      t.compile_histogram[5].Get(), t.untimed_stores.Get(), Average(t.store_ns.Get(), t.stores.Get()) / 1e6,
      Millis(t.max_store_ns.Get()));
  REXLOG_INFO("PSO compiles by thread: present {} ({:.1f} ms), async {} ({:.1f} ms), other {} ({:.1f} ms)",
              t.thread_compiles[kPresentThread].Get(), Millis(t.thread_compile_ns[kPresentThread].Get()),
              t.thread_compiles[kAsyncThread].Get(), Millis(t.thread_compile_ns[kAsyncThread].Get()),
              t.thread_compiles[kOtherThread].Get(), Millis(t.thread_compile_ns[kOtherThread].Get()));
  REXLOG_INFO("PSO auxiliary: {} requests, {} library hits, {} compiles, {} failed, {:.1f} ms compiling, worst {:.1f} ms",
              t.aux_requests.Get(), t.aux_hits.Get(), t.aux_compiles.Get(), t.aux_failed.Get(),
              Millis(t.aux_compile_ns.Get()), Millis(t.max_aux_compile_ns.Get()));
  REXLOG_INFO(
      "PSO saves: {} written ({} bytes), {} failed, {} postponed; mutex held {:.1f} ms in total, worst "
      "{:.1f} ms; copy {:.1f} ms, allocation outside the mutex {:.1f} ms, write {:.1f} ms; {} retries, "
      "{} allocations under the mutex",
      t.saves.Get(), t.save_bytes.Get(), t.save_failed.Get(), t.save_postponed.Get(),
      Millis(t.save_lock_ns.Get()), Millis(t.save_max_lock_ns.Get()), Millis(t.save_copy_ns.Get()),
      Millis(t.save_alloc_ns.Get()), Millis(t.save_write_ns.Get()), t.save_retries.Get(),
      t.save_under_lock.Get());
  if (t.async_posted.Get() || t.async_skipped_draws.Get())
    REXLOG_INFO(
        "PSO async: {} posted, {} ready, {} failed, {} skipped draws, {} waits ({:.1f} ms), {} timeouts",
        t.async_posted.Get(), t.async_ready.Get(), t.async_failed.Get(), t.async_skipped_draws.Get(),
        t.async_waits.Get(), Millis(t.async_wait_ns.Get()), t.async_timeouts.Get());
  REXLOG_INFO(
      "PSO frames: {} at {:.1f} fps, worst {:.1f} ms; <=16.7 ms {}, <=33.3 {}, <=50 {}, <=100 {}, "
      "<=250 {}, >250 {}; hitches of 50 ms or more {}, frames with 4 ms or more of blocking compiles {}, "
      "both {}",
      frames, seconds > 0 ? double(frames) / seconds : 0.0, Millis(worst_ns), histogram[0], histogram[1],
      histogram[2], histogram[3], histogram[4], histogram[5], hitches, compile_frames, compile_hitches);
  if (!rows.empty() || have_partial) {
    REXLOG_INFO(
        "PSO minute    #: frames    fps worst_ms hitch cfrm  comp  comp_ms block_ms  miss   hits  skip");
    for (const auto& row : rows) LogRow(row, "");
    if (have_partial) LogRow(partial, " (partial)");
  }
}

// Called once per present (PipelineLibraryFrame) with the current time.
inline void OnFrameAt(uint64_t now) {
  PeriodRow report;
  bool have_report = false;
  std::filesystem::path trigger;
  {
    std::lock_guard lock(g_frames.mutex);
    auto& f = g_frames;
    if (!f.first_ns) {
      f.first_ns = f.last_ns = now;
      f.last_blocking_ns = g_totals.blocking_compile_ns.Get();
      f.minute.Reset(now);
      f.interval.Reset(now);
      f.next_trigger_ns = now + kTriggerCheckNs;
      return;
    }
    const uint64_t frame = now > f.last_ns ? now - f.last_ns : 0;
    f.last_ns = now;
    const uint64_t blocking = g_totals.blocking_compile_ns.Get();
    const bool compile_frame = blocking - f.last_blocking_ns >= kCompileFrameNs;
    f.last_blocking_ns = blocking;
    const bool hitch = frame >= kHitchNs;
    ++f.frames;
    f.worst_ns = std::max(f.worst_ns, frame);
    ++f.histogram[FrameBucket(frame)];
    f.hitches += hitch;
    f.compile_frames += compile_frame;
    f.compile_hitches += hitch && compile_frame;
    f.minute.Add(frame, hitch, compile_frame);
    f.interval.Add(frame, hitch, compile_frame);
    if (now - f.minute.start_ns >= kMinuteNs) {
      const PeriodRow row = MakeRow(f.minute, now, f.minute_index++);
      if (f.rows.size() < kMinuteRows)
        f.rows.push_back(row);
      else
        f.rows[std::size_t(row.index % kMinuteRows)] = row;
      f.minute.Reset(now);
    }
    if (f.interval_ns && now - f.interval.start_ns >= f.interval_ns) {
      report = MakeRow(f.interval, now, 0);
      have_report = true;
      f.interval.Reset(now);
    }
    if (!f.trigger.empty() && now >= f.next_trigger_ns) {
      f.next_trigger_ns = now + kTriggerCheckNs;
      trigger = f.trigger;
    }
  }
  if (have_report) LogPeriod(report);
  if (!trigger.empty()) {
    std::error_code error;
    if (std::filesystem::remove(trigger, error)) LogSummary("pso-stats.now");
  }
}

inline void OnFrame() {
  t_thread_kind = kPresentThread;
  OnFrameAt(Nanos());
}

// Called first by StartPipelineLibrary. Returns whether stats are on.
inline bool ReadEnvironment() {
  const char* value = std::getenv("LEGO_NATIVE_PSO_STATS");
  const bool on = value && *value && std::strcmp(value, "0") != 0;
  g_enabled.store(on, std::memory_order_relaxed);
  g_exit_logged.store(false, std::memory_order_relaxed);
  return on;
}

// Called by StartPipelineLibrary once stats are on.
inline void Configure(const std::filesystem::path& cache_directory) {
  uint64_t seconds = 0;
  if (const char* value = std::getenv("LEGO_NATIVE_PSO_STATS_INTERVAL"))
    seconds = std::min<uint64_t>(std::strtoull(value, nullptr, 10), 3600);
  std::filesystem::path trigger = cache_directory / "pso-stats.now";
  {
    std::lock_guard lock(g_frames.mutex);
    g_frames.trigger = trigger;
    g_frames.interval_ns = seconds * 1'000'000'000ull;
    g_frames.rows.reserve(kMinuteRows);
  }
  REXLOG_INFO(
      "Native GPU: PSO stats on (LEGO_NATIVE_PSO_STATS); summary at exit and whenever {} is created, "
      "delta every {} s (LEGO_NATIVE_PSO_STATS_INTERVAL, 0 = off)",
      trigger.string(), seconds);
}

// The exit summary, logged once per StartPipelineLibrary.
inline void LogExitSummary() {
  if (!g_exit_logged.exchange(true)) LogSummary("exit");
}

}  // namespace legodimensions::gpu_native::pso_stats
