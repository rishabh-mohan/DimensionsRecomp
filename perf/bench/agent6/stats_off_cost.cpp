// Agent 6, task #5 item 2 (report #8): tests for gpu_native/pipeline_stats.h
// and the cost of its hooks while LEGO_NATIVE_PSO_STATS is off.
//
//   powershell -NoProfile -ExecutionPolicy Bypass -File bench/agent6/run_benches.ps1 -Only stats_off_cost
//
// rex/logging.h resolves to bench/agent6/include/rex/logging.h, which keeps the
// REXLOG lines so the summary text can be checked. Single-threaded except for
// one short helper thread; the cost bench takes about 5 CPU-seconds.

#include <rex/logging.h>

#include "gpu_native/pipeline_stats.h"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <memory>
#include <mutex>
#include <random>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

namespace ps = legodimensions::gpu_native::pso_stats;

namespace {

int g_failures = 0;
#define CHECK(...)                                                        \
  do {                                                                    \
    if (!(__VA_ARGS__)) {                                                 \
      std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #__VA_ARGS__);  \
      ++g_failures;                                                       \
    }                                                                     \
  } while (0)

constexpr uint64_t kMs = 1'000'000;
constexpr uint64_t kSec = 1'000'000'000;

template <class T>
void Rebuild(T& object) {
  std::destroy_at(&object);
  std::construct_at(&object);
}

void ResetAll(bool enabled = true) {
  Rebuild(ps::g_totals);
  Rebuild(ps::g_startup);
  Rebuild(ps::g_frames);
  ps::t_miss_time = 0;
  ps::t_thread_kind = ps::kOtherThread;
  ps::g_exit_logged = false;
  ps::g_enabled = enabled;
  bench_log::Take();
}

int CountLines(const std::vector<std::string>& lines, const std::string& needle) {
  return int(std::count_if(lines.begin(), lines.end(),
                           [&](const std::string& line) { return line.find(needle) != std::string::npos; }));
}

bool HasLine(const std::vector<std::string>& lines, const std::string& needle) {
  return CountLines(lines, needle) > 0;
}

// Minute numbers of the per-minute table rows, in log order.
std::vector<int> MinuteRows(const std::vector<std::string>& lines) {
  std::vector<int> rows;
  for (const auto& line : lines) {
    int index = 0;
    if (std::sscanf(line.c_str(), "PSO minute %d:", &index) == 1) rows.push_back(index);
  }
  return rows;
}

void Report(const char* name, int failures_before) {
  std::printf("%-22s %s\n", name, g_failures == failures_before ? "PASS" : "FAIL");
}

void TestFrames() {
  const int before = g_failures;
  ResetAll();
  uint64_t now = 1000 * kSec;
  ps::OnFrameAt(now);  // the first present only starts the clock
  const auto frame = [&](uint64_t ms) {
    now += ms * kMs;
    ps::OnFrameAt(now);
  };
  frame(10);
  ps::RecordCompile(5 * kMs, ps::kAsyncThread);  // async compiles never block a frame
  frame(10);
  ps::RecordCompile(3 * kMs, ps::kOtherThread);  // under the 4 ms compile-frame threshold
  frame(10);
  frame(20);
  frame(40);
  ps::RecordCompile(2 * kMs, ps::kPresentThread);
  ps::RecordCompile(3 * kMs, ps::kPresentThread);  // 5 ms in one frame: a compile frame
  frame(60);
  frame(120);
  frame(300);
  const auto& f = ps::g_frames;
  const auto& t = ps::g_totals;
  CHECK(f.frames == 8);
  CHECK(f.histogram == std::array<uint64_t, ps::kFrameBuckets>{3, 1, 1, 1, 1, 1});
  CHECK(f.hitches == 3);
  CHECK(f.compile_frames == 1);
  CHECK(f.compile_hitches == 1);
  CHECK(f.worst_ns == 300 * kMs);
  CHECK(t.compiles.Get() == 4);
  CHECK(t.blocking_compile_ns.Get() == 8 * kMs);
  CHECK(t.thread_compiles[ps::kAsyncThread].Get() == 1);
  CHECK(t.thread_compiles[ps::kPresentThread].Get() == 2);
  CHECK(t.thread_compile_ns[ps::kPresentThread].Get() == 5 * kMs);
  CHECK(t.compile_histogram[1].Get() == 3);  // 1-4 ms
  CHECK(t.compile_histogram[2].Get() == 1);  // 4-16 ms
  CHECK(t.max_compile_ns.Get() == 5 * kMs);
  CHECK(ps::CompileBucket(999'999) == 0 && ps::CompileBucket(kMs) == 1 && ps::CompileBucket(300 * kMs) == 5);
  CHECK(ps::FrameBucket(16'700'000) == 0 && ps::FrameBucket(16'700'001) == 1 && ps::FrameBucket(kSec) == 5);
  Report("frames", before);
}

void TestMinutes() {
  const int before = g_failures;
  ResetAll();
  uint64_t now = 5000 * kSec;
  ps::OnFrameAt(now);
  const uint64_t minutes = ps::kMinuteRows + 5;
  for (uint64_t minute = 0; minute < minutes; ++minute) {
    if (minute == 243) ps::RecordCompile(10 * kMs, ps::kPresentThread);
    now += 30 * kSec;
    ps::OnFrameAt(now);
    now += 30 * kSec;
    ps::OnFrameAt(now);  // closes this minute
  }
  const auto& f = ps::g_frames;
  CHECK(f.minute_index == minutes);
  CHECK(f.rows.size() == ps::kMinuteRows);
  const auto& row = f.rows[243 % ps::kMinuteRows];
  CHECK(row.index == 243);
  CHECK(row.frames == 2);
  CHECK(row.compiles == 1);
  CHECK(row.compile_ms == 10.0);
  CHECK(row.blocking_ms == 10.0);
  CHECK(row.seconds == 60.0);
  CHECK(f.rows[242 % ps::kMinuteRows].compiles == 0);
  ps::LogSummary("minutes");
  auto lines = bench_log::Take();
  const auto rows = MinuteRows(lines);
  CHECK(rows.size() == ps::kMinuteRows);
  CHECK(!rows.empty() && rows.front() == 5 && rows.back() == 244);  // the oldest rows were dropped
  CHECK(std::is_sorted(rows.begin(), rows.end()));
  CHECK(!HasLine(lines, "(partial)"));
  now += 10 * kSec;
  ps::OnFrameAt(now);  // one frame into minute 245
  ps::LogSummary("partial");
  lines = bench_log::Take();
  CHECK(HasLine(lines, "(partial)"));
  CHECK(MinuteRows(lines).back() == 245);
  Report("minute table", before);
}

void TestInterval() {
  const int before = g_failures;
  ResetAll();
  ps::g_frames.interval_ns = 10 * kSec;
  uint64_t now = 9000 * kSec;
  ps::OnFrameAt(now);
  for (int i = 0; i < 25; ++i) {
    now += kSec;
    ps::OnFrameAt(now);
  }
  CHECK(CountLines(bench_log::Take(), "Native GPU PSO stats, last 10 s: 10 frames, 1.0 fps") == 2);
  Report("interval delta", before);
}

void TestTrigger() {
  const int before = g_failures;
  ResetAll();
  _putenv_s("LEGO_NATIVE_PSO_STATS_INTERVAL", "");
  const auto directory = std::filesystem::temp_directory_path() / "agent6_pso_stats_test";
  std::filesystem::create_directories(directory);
  ps::Configure(directory);
  const auto trigger = directory / "pso-stats.now";
  CHECK(ps::g_frames.trigger == trigger);
  std::ofstream(trigger) << "now";
  uint64_t now = 100 * kSec;
  ps::OnFrameAt(now);  // first present: the first check is 2 s later
  now += kSec;
  ps::OnFrameAt(now);
  CHECK(std::filesystem::exists(trigger));
  CHECK(!HasLine(bench_log::Take(), "(pso-stats.now)"));
  now += 1500 * kMs;
  ps::OnFrameAt(now);  // 2.5 s: checked, deleted, logged
  CHECK(!std::filesystem::exists(trigger));
  CHECK(CountLines(bench_log::Take(), "Native GPU PSO stats (pso-stats.now)") == 1);
  now += 3 * kSec;
  ps::OnFrameAt(now);  // no file: no summary
  CHECK(!HasLine(bench_log::Take(), "(pso-stats.now)"));
  std::error_code error;
  std::filesystem::remove_all(directory, error);
  Report("trigger file", before);
}

void TestLookupsAndSummary() {
  const int before = g_failures;
  ResetAll();
  auto& t = ps::g_totals;
  // A miss that waited 2 ms for the mutex and ran a 0.3 ms library load.
  ps::LookupTimes times;
  times.start = ps::Nanos() - 3 * kMs;
  times.lock_begin = times.start + kMs / 10;
  times.locked = times.lock_begin + 2 * kMs;
  times.load_begin = times.locked;
  times.load_end = times.load_begin + 3 * kMs / 10;
  ps::OnLookup(ps::Lookup::kMiss, times);
  CHECK(t.lookups.Get() == 1 && t.misses.Get() == 1);
  CHECK(t.lock_waits_over_1ms.Get() == 1 && t.max_lock_wait_ns.Get() == 2 * kMs);
  CHECK(t.library_loads.Get() == 1 && t.library_load_ns.Get() == 3 * kMs / 10);
  CHECK(ps::t_miss_time != 0);
  // Plume compiled for 5 ms after the miss, then called store().
  ps::t_miss_time = ps::Nanos() - 5 * kMs;
  ps::OnStored(ps::OnStore());
  CHECK(t.compiles.Get() == 1);
  CHECK(t.compile_ns.Get() >= 5 * kMs && t.compile_ns.Get() < 1000 * kMs);
  CHECK(t.compile_histogram[2].Get() == 1);
  CHECK(t.thread_compiles[ps::kOtherThread].Get() == 1);
  CHECK(t.blocking_compile_ns.Get() == t.compile_ns.Get());
  CHECK(t.stores.Get() == 1 && ps::t_miss_time == 0);
  // A store with no miss before it is counted but not timed.
  ps::OnStored(ps::OnStore());
  CHECK(t.untimed_stores.Get() == 1 && t.compiles.Get() == 1);
  // A hit after a miss clears the pending miss.
  ps::OnLookup(ps::Lookup::kMiss, times);
  ps::LookupTimes warm;
  warm.start = warm.lock_begin = warm.locked = ps::Nanos();
  ps::OnLookup(ps::Lookup::kWarm, warm);
  CHECK(ps::t_miss_time == 0);
  CHECK(t.warm_hits.Get() == 1 && t.library_loads.Get() == 2);
  // Async pool threads add no blocking time.
  const uint64_t blocking = t.blocking_compile_ns.Get();
  std::thread([] {
    ps::t_thread_kind = ps::kAsyncThread;
    ps::t_miss_time = ps::Nanos() - 2 * kMs;
    ps::OnStored(ps::OnStore());
  }).join();
  CHECK(t.thread_compiles[ps::kAsyncThread].Get() == 1);
  CHECK(t.blocking_compile_ns.Get() == blocking);
  // The present thread marks itself in OnFrame().
  ps::OnFrame();
  ps::t_miss_time = ps::Nanos() - kMs;
  ps::OnStored(ps::OnStore());
  CHECK(t.thread_compiles[ps::kPresentThread].Get() == 1);
  ps::t_thread_kind = ps::kOtherThread;
  // Without a library every lookup misses.
  ps::OnUncachedLookup();
  CHECK(t.lookups.Get() == 4 && t.misses.Get() == 3 && ps::t_miss_time != 0);
  ps::t_miss_time = 0;
  ps::OnAuxiliary(true, true, 0);
  ps::OnAuxiliary(false, true, 3 * kMs);
  ps::OnAuxiliary(false, false, kMs);
  CHECK(t.aux_requests.Get() == 3 && t.aux_hits.Get() == 1 && t.aux_compiles.Get() == 1 && t.aux_failed.Get() == 1);
  CHECK(t.aux_compile_ns.Get() == 4 * kMs);
  ps::OnSaveSnapshot({kMs, kMs, kMs / 2, 2 * kMs, 1, false});
  ps::OnSaveWritten(true, 1000, 4 * kMs);
  ps::OnSavePostponed();
  CHECK(t.saves.Get() == 1 && t.save_bytes.Get() == 1000 && t.save_postponed.Get() == 1 && t.save_retries.Get() == 1);
  bench_log::Take();
  ps::LogSummary("test");
  auto lines = bench_log::Take();
  for (const char* needle :
       {"Native GPU PSO stats (test)", "PSO startup: cache not started", "PSO lookups: 4 (warm 1, library 0, miss 3)",
        "PSO compiles: 3 taking", "PSO compiles by thread: present 1", "async 1", "other 1",
        "PSO auxiliary: 3 requests, 1 library hits, 1 compiles, 1 failed",
        "PSO saves: 1 written (1000 bytes), 0 failed, 1 postponed", "PSO frames:"})
    if (!HasLine(lines, needle)) {
      std::printf("missing summary text: %s\n", needle);
      ++g_failures;
    }
  CHECK(!HasLine(lines, "PSO async:"));
  CHECK(!HasLine(lines, "PSO startup preparation"));
  ps::OnAsyncPosted();
  ps::OnPrepare({10, 5, 1, 15, 4, 100 * kMs, 20 * kMs, 70 * kMs, 9 * kMs});
  ps::OnOpen(ps::CacheState::kLoaded, 4096, kMs, 2 * kMs);
  ps::LogSummary("again");
  lines = bench_log::Take();
  CHECK(HasLine(lines, "PSO async: 1 posted"));
  CHECK(HasLine(lines, "PSO startup preparation: loaded 10, compiled 5, failed 1, resident 15, threads 4, 100.0 ms"));
  CHECK(HasLine(lines, "PSO startup: cache loaded, file 4096 bytes, read 1.0 ms, library create 2.0 ms"));
  Report("lookups and summary", before);
  std::printf("--- sample summary ---\n");
  for (const auto& line : lines) std::printf("%s\n", line.c_str());
  std::printf("----------------------\n");
}

void TestEnvironment() {
  const int before = g_failures;
  ResetAll(false);
  _putenv_s("LEGO_NATIVE_PSO_STATS", "1");
  CHECK(ps::ReadEnvironment() && ps::Enabled());
  _putenv_s("LEGO_NATIVE_PSO_STATS", "0");
  CHECK(!ps::ReadEnvironment() && !ps::Enabled());
  _putenv_s("LEGO_NATIVE_PSO_STATS", "");  // removes the variable
  CHECK(!ps::ReadEnvironment());
  _putenv_s("LEGO_NATIVE_PSO_STATS", "yes");
  CHECK(ps::ReadEnvironment());
  const auto directory = std::filesystem::temp_directory_path();
  _putenv_s("LEGO_NATIVE_PSO_STATS_INTERVAL", "99999");
  ps::Configure(directory);
  CHECK(ps::g_frames.interval_ns == 3600 * kSec);
  _putenv_s("LEGO_NATIVE_PSO_STATS_INTERVAL", "30");
  ps::Configure(directory);
  CHECK(ps::g_frames.interval_ns == 30 * kSec);
  _putenv_s("LEGO_NATIVE_PSO_STATS_INTERVAL", "");
  ps::Configure(directory);
  CHECK(ps::g_frames.interval_ns == 0);
  CHECK(HasLine(bench_log::Take(), "PSO stats on (LEGO_NATIVE_PSO_STATS)"));
  ps::LogExitSummary();
  ps::LogExitSummary();
  CHECK(CountLines(bench_log::Take(), "Native GPU PSO stats (exit)") == 1);
  ps::ReadEnvironment();  // the next StartPipelineLibrary
  ps::LogExitSummary();
  CHECK(CountLines(bench_log::Take(), "Native GPU PSO stats (exit)") == 1);
  _putenv_s("LEGO_NATIVE_PSO_STATS", "");
  ps::g_enabled = false;
  Report("environment", before);
}

// --- cost of the hooks ------------------------------------------------------

struct FakeDesc {
  uint8_t bytes[64];
};

std::mutex g_cost_mutex;
std::unordered_map<uint64_t, int> g_cost_map;
void* volatile g_fake_library = nullptr;
std::atomic<uint64_t> g_frame_work{0};

uint64_t Fnv(const FakeDesc& desc) {
  uint64_t hash = 1469598103934665603ull;
  for (const uint8_t byte : desc.bytes) {
    hash ^= byte;
    hash *= 1099511628211ull;
  }
  return hash;
}

// The shape of PipelineLibrary::Load<kStats>: name hash, mutex, lookup, hooks.
template <bool kStats>
int MimicLoad(const FakeDesc& desc) {
  ps::LookupTimes times;
  if constexpr (kStats) times.start = ps::Nanos();
  const uint64_t name = Fnv(desc);
  if constexpr (kStats) times.lock_begin = ps::Nanos();
  std::lock_guard lock(g_cost_mutex);
  if constexpr (kStats) times.locked = ps::Nanos();
  const auto entry = g_cost_map.find(name);
  const int value = entry == g_cost_map.end() ? -1 : entry->second;
  if constexpr (kStats) ps::OnLookup(value >= 0 ? ps::Lookup::kLibrary : ps::Lookup::kMiss, times);
  return value;
}

// load() before the change, and after it (one relaxed load and a branch).
__declspec(noinline) int LoadBefore(const FakeDesc& desc) { return MimicLoad<false>(desc); }
__declspec(noinline) int LoadAfter(const FakeDesc& desc) {
  return ps::Enabled() ? MimicLoad<true>(desc) : MimicLoad<false>(desc);
}

// PipelineLibraryFrame() before and after.
__declspec(noinline) void FrameBefore() {
  if (g_fake_library) g_frame_work.fetch_add(1, std::memory_order_relaxed);
}
__declspec(noinline) void FrameAfter() {
  if (ps::Enabled()) ps::OnFrame();
  if (g_fake_library) g_frame_work.fetch_add(1, std::memory_order_relaxed);
}

template <class Call>
double NsPerCall(int count, Call&& call) {
  const auto start = std::chrono::steady_clock::now();
  for (int i = 0; i < count; ++i) call(i);
  return std::chrono::duration<double, std::nano>(std::chrono::steady_clock::now() - start).count() / count;
}

void CostBench() {
  ResetAll(false);
  std::mt19937_64 random(6);
  std::vector<FakeDesc> descs(1024);
  for (std::size_t i = 0; i < descs.size(); ++i) {
    for (auto& byte : descs[i].bytes) byte = uint8_t(random());
    if (i % 2 == 0) g_cost_map.emplace(Fnv(descs[i]), int(i));  // half hit, half miss
  }
  constexpr int kLoads = 2'000'000;
  constexpr int kFrames = 10'000'000;
  constexpr int kRepeats = 7;
  double load_before = 1e9, load_off = 1e9, load_on = 1e9;
  double frame_before = 1e9, frame_off = 1e9, frame_on = 1e9;
  long long sink = 0;
  for (int repeat = 0; repeat < kRepeats; ++repeat) {
    ps::g_enabled = false;
    load_before = std::min(load_before, NsPerCall(kLoads, [&](int i) { sink += LoadBefore(descs[i & 1023]); }));
    load_off = std::min(load_off, NsPerCall(kLoads, [&](int i) { sink += LoadAfter(descs[i & 1023]); }));
    frame_before = std::min(frame_before, NsPerCall(kFrames, [&](int) { FrameBefore(); }));
    frame_off = std::min(frame_off, NsPerCall(kFrames, [&](int) { FrameAfter(); }));
    ps::g_enabled = true;
    load_on = std::min(load_on, NsPerCall(kLoads, [&](int i) { sink += LoadAfter(descs[i & 1023]); }));
    frame_on = std::min(frame_on, NsPerCall(kFrames / 10, [&](int) { FrameAfter(); }));
    ps::g_enabled = false;
  }
  ps::t_thread_kind = ps::kOtherThread;
  std::printf("cost, min of %d runs, ns per call (sink %lld):\n", kRepeats, sink & 1);
  std::printf("  load():  before %.2f, stats off %.2f (%+.2f), stats on %.2f (%+.2f)\n", load_before, load_off,
              load_off - load_before, load_on, load_on - load_before);
  std::printf("  frame(): before %.2f, stats off %.2f (%+.2f), stats on %.2f (%+.2f)\n", frame_before, frame_off,
              frame_off - frame_before, frame_on, frame_on - frame_before);
  // One relaxed load and a predictable branch: well under the run-to-run noise.
  const int before = g_failures;
  CHECK(load_off - load_before <= std::max(2.0, 0.05 * load_before));
  CHECK(frame_off - frame_before <= 2.0);
  Report("cost while off", before);
}

}  // namespace

int main() {
  bench_log::g_quiet = true;
  TestFrames();
  TestMinutes();
  TestInterval();
  TestTrigger();
  TestLookupsAndSummary();
  TestEnvironment();
  CostBench();
  std::printf("stats_off_cost: %s (%d failures)\n", g_failures ? "FAIL" : "PASS", g_failures);
  return g_failures ? 1 : 0;
}
