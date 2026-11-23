// Agent 6, task #5 item 1 (report #1): how long the pipeline-cache autosave
// holds the library mutex, old algorithm vs SnapshotPipelineLibrary
// (DimensionsRecomp/rexlego/src/gpu_native/pipeline_snapshot.h).
//
// Build and run:
//   powershell -NoProfile -ExecutionPolicy Bypass -File bench/agent6/run_benches.ps1 -Only save_lock_hold
// Options: --sizes 64,256,512 (MiB, max 512)  --reps 3  --quick  --checks-only  --out <dir>
//
// The library is simulated. GetSerializedSize() returns the current size and
// Serialize() fills exactly that many bytes from a 16 MiB random block, so it
// runs at memcpy speed (a driver serialize is at least this slow). A loader
// thread takes the same mutex every ~50 us, like draw-time load()/store() on a
// PSO miss, and records how long each lock() waited. Two threads in total.
//
// Algorithms:
//   old    the pre-change Save(): GetSerializedSize, std::vector resize
//          (allocation, zero-fill, first-touch page faults) and Serialize, all
//          under the mutex.
//   snap   SnapshotPipelineLibrary(..., 3), the new Save(): allocate and
//          zero-fill outside the mutex; query and Serialize under it.
//   snap0  SnapshotPipelineLibrary(..., 0): the old algorithm expressed through
//          the helper (allocation under the mutex). Should time like `old`.
// Every saved buffer is hashed over the bytes Save() writes and compared with
// `old`. At the smallest size `old` and `snap` are also written to files the
// way Save() writes them, and the files are compared byte for byte.
// Unit checks cover retries, the under-lock fallback, a shrinking library,
// nothing-to-save, copy failure and out-of-memory.

#include "gpu_native/pipeline_snapshot.h"

#include <immintrin.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <random>
#include <string>
#include <thread>
#include <vector>

namespace gn = legodimensions::gpu_native;
using Clock = std::chrono::steady_clock;
using Status = gn::PipelineSnapshot::Status;

namespace {

int64_t Ns(Clock::duration duration) {
  return std::chrono::duration_cast<std::chrono::nanoseconds>(duration).count();
}
double Ms(int64_t ns) { return double(ns) / 1e6; }

constexpr std::size_t kMiB = std::size_t{1} << 20;
constexpr std::size_t kMaxLibraryBytes = 512 * kMiB;  // pipeline_library.cpp

int g_failures = 0;
#define CHECK(condition)                                                        \
  do {                                                                          \
    if (!(condition)) {                                                         \
      std::printf("CHECK FAILED %s:%d: %s\n", __FILE__, __LINE__, #condition); \
      ++g_failures;                                                             \
    }                                                                           \
  } while (0)

void Spin(Clock::time_point until) {
  while (Clock::now() < until) _mm_pause();
}

uint64_t Hash(const uint8_t* data, std::size_t size) {
  uint64_t hash = 0xcbf29ce484222325ull ^ size;
  std::size_t i = 0;
  for (; i + 8 <= size; i += 8) {
    uint64_t word;
    std::memcpy(&word, data + i, 8);
    hash = (hash ^ word) * 0x100000001b3ull;
    hash ^= hash >> 29;
  }
  for (; i < size; ++i) hash = (hash ^ data[i]) * 0x100000001b3ull;
  return hash;
}

// Hold times are recorded only for the thread that sets t_record (the saver).
thread_local bool t_record = false;
struct HoldStats {
  int64_t max_ns = 0;
  int64_t total_ns = 0;
  uint64_t holds = 0;
};

class TimedMutex {
 public:
  void lock() {
    mutex_.lock();
    if (t_record) locked_at_ = Clock::now();
  }
  void unlock() {
    if (t_record) {
      const int64_t held = Ns(Clock::now() - locked_at_);
      stats_.total_ns += held;
      stats_.max_ns = std::max(stats_.max_ns, held);
      ++stats_.holds;
    }
    mutex_.unlock();
  }
  // Called by the recording thread only, while it does not hold the mutex.
  HoldStats Take() {
    const HoldStats stats = stats_;
    stats_ = {};
    return stats;
  }

 private:
  std::mutex mutex_;
  Clock::time_point locked_at_{};
  HoldStats stats_;
};

class FakeLibrary {
 public:
  explicit FakeLibrary(std::size_t pattern_bytes) : pattern_(pattern_bytes / sizeof(uint64_t)) {
    std::mt19937_64 random(0x5eed);
    for (auto& word : pattern_) word = random();
  }
  std::size_t size = 0;
  std::size_t GetSerializedSize() const { return size; }
  // Like ID3D12PipelineLibrary::Serialize: fails when the buffer is smaller
  // than the serialized size and writes exactly `size` bytes otherwise.
  bool Serialize(uint8_t* destination, std::size_t bytes) const {
    if (bytes < size) return false;
    const std::size_t block = pattern_.size() * sizeof(uint64_t);
    for (std::size_t offset = 0, index = 0; offset < size; offset += block, ++index) {
      const std::size_t count = std::min(block, size - offset);
      std::memcpy(destination + offset, pattern_.data(), count);
      // Position-dependent, so a shifted or short copy changes the hash.
      std::memcpy(destination + offset, &index, std::min(count, sizeof(index)));
    }
    return true;
  }

 private:
  std::vector<uint64_t> pattern_;
};

struct WaitStats {
  uint64_t samples = 0;
  int64_t max_ns = 0;
  int64_t p99_ns = 0;
  int64_t p999_ns = 0;
  int64_t total_ns = 0;
  uint64_t over_1ms = 0;
  uint64_t over_4ms = 0;
  uint64_t over_16ms = 0;
};

WaitStats Summarize(std::vector<int64_t>& waits) {
  WaitStats stats;
  stats.samples = waits.size();
  if (waits.empty()) return stats;
  for (const int64_t wait : waits) {
    stats.total_ns += wait;
    if (wait > 1'000'000) ++stats.over_1ms;
    if (wait > 4'000'000) ++stats.over_4ms;
    if (wait > 16'000'000) ++stats.over_16ms;
  }
  std::sort(waits.begin(), waits.end());
  stats.max_ns = waits.back();
  stats.p99_ns = waits[std::min(waits.size() - 1, waits.size() * 99 / 100)];
  stats.p999_ns = waits[std::min(waits.size() - 1, waits.size() * 999 / 1000)];
  return stats;
}

// Draw-time library traffic: lock, ~1 us of work, unlock, every ~50 us.
class LoaderThread {
 public:
  explicit LoaderThread(TimedMutex& mutex) : mutex_(mutex) {
    waits_.reserve(std::size_t{1} << 21);
    thread_ = std::thread([this] { Run(); });
  }
  ~LoaderThread() {
    if (thread_.joinable()) Finish();
  }
  WaitStats Finish() {
    stop_.store(true);
    thread_.join();
    return Summarize(waits_);
  }

 private:
  void Run() {
    while (!stop_.load(std::memory_order_relaxed)) {
      const auto attempt = Clock::now();
      mutex_.lock();
      const auto acquired = Clock::now();
      Spin(acquired + std::chrono::microseconds(1));
      mutex_.unlock();
      if (waits_.size() < waits_.capacity()) waits_.push_back(Ns(acquired - attempt));
      Spin(acquired + std::chrono::microseconds(50));
    }
  }

  TimedMutex& mutex_;
  std::atomic<bool> stop_{false};
  std::vector<int64_t> waits_;
  std::thread thread_;
};

enum class Algorithm { kOld, kSnap, kSnap0 };
const char* Name(Algorithm algorithm) {
  switch (algorithm) {
    case Algorithm::kOld: return "old";
    case Algorithm::kSnap: return "snap";
    case Algorithm::kSnap0: return "snap0";
  }
  return "?";
}

struct SaveOutcome {
  bool ok = false;
  std::size_t size = 0;
  int64_t wall_ns = 0;           // query, allocation and copy; excludes the write
  int64_t alloc_outside_ns = 0;  // allocation outside the mutex
  uint32_t passes = 0;
  uint32_t retries = 0;
};

// One save. `write` receives exactly the bytes the real Save() writes to disk.
template <class Write>
SaveOutcome RunSave(Algorithm algorithm, TimedMutex& mutex, const FakeLibrary& library, Write&& write) {
  SaveOutcome outcome;
  const auto start = Clock::now();
  if (algorithm == Algorithm::kOld) {
    // pipeline_library.cpp Save() before task #5.
    std::vector<uint8_t> data;
    {
      std::lock_guard lock(mutex);
      const std::size_t size = library.GetSerializedSize();
      if (size <= 1024 || size > kMaxLibraryBytes) return outcome;
      data.resize(size);
      if (!library.Serialize(data.data(), size)) return outcome;
    }
    outcome.wall_ns = Ns(Clock::now() - start);
    outcome.ok = true;
    outcome.size = data.size();
    outcome.passes = 1;
    write(data.data(), data.size());
    return outcome;
  }
  auto snapshot = gn::SnapshotPipelineLibrary(
      mutex,
      [&]() -> std::size_t {
        const std::size_t size = library.GetSerializedSize();
        return size <= 1024 || size > kMaxLibraryBytes ? 0 : size;
      },
      [&](uint8_t* data, std::size_t size) { return library.Serialize(data, size); },
      algorithm == Algorithm::kSnap ? 3u : 0u);
  outcome.wall_ns = Ns(Clock::now() - start);
  if (snapshot.status != Status::kCopied) return outcome;
  outcome.ok = true;
  outcome.size = snapshot.size;
  outcome.alloc_outside_ns = snapshot.alloc_us * 1000;
  outcome.passes = snapshot.passes;
  outcome.retries = snapshot.retries;
  write(snapshot.data.get(), snapshot.size);
  return outcome;
}

// Same calls as Save(): write a .tmp, then rename over the target.
bool WriteLikeSave(const std::filesystem::path& path, const uint8_t* data, std::size_t size) {
  auto temporary = path;
  temporary += L".tmp";
  {
    std::ofstream file(temporary, std::ios::binary | std::ios::trunc);
    if (!file.write(reinterpret_cast<const char*>(data), std::streamsize(size))) return false;
  }
  std::error_code error;
  std::filesystem::rename(temporary, path, error);
  return !error;
}

bool SameFiles(const std::filesystem::path& a, const std::filesystem::path& b) {
  std::error_code error;
  const auto size = std::filesystem::file_size(a, error);
  if (error || size != std::filesystem::file_size(b, error) || error) return false;
  std::ifstream first(a, std::ios::binary), second(b, std::ios::binary);
  std::vector<char> x(4 * kMiB), y(4 * kMiB);
  for (uintmax_t left = size; left;) {
    const auto count = std::streamsize(std::min<uintmax_t>(left, x.size()));
    if (!first.read(x.data(), count) || !second.read(y.data(), count)) return false;
    if (std::memcmp(x.data(), y.data(), std::size_t(count))) return false;
    left -= uintmax_t(count);
  }
  return true;
}

struct PhaseResult {
  int saves = 0;
  bool ok = true;
  uint64_t hash = 0;
  int64_t max_hold_ns = 0;
  int64_t hold_ns = 0;
  int64_t wall_ns = 0;
  int64_t alloc_outside_ns = 0;
  uint32_t passes = 0;
  uint32_t retries = 0;
  bool file_written = false;
  WaitStats waits;
};

PhaseResult RunPhase(Algorithm algorithm, std::size_t bytes, int reps, FakeLibrary& library,
                     const std::filesystem::path* file) {
  PhaseResult result;
  TimedMutex mutex;
  library.size = bytes;
  LoaderThread loader(mutex);
  std::this_thread::sleep_for(std::chrono::milliseconds(20));
  for (int rep = 0; rep < reps; ++rep) {
    t_record = true;
    const SaveOutcome outcome =
        RunSave(algorithm, mutex, library, [&](const uint8_t* data, std::size_t size) {
          if (rep) return;
          result.hash = Hash(data, size);
          if (file) result.file_written = WriteLikeSave(*file, data, size);
        });
    t_record = false;
    const HoldStats holds = mutex.Take();
    result.ok = result.ok && outcome.ok && outcome.size == bytes;
    ++result.saves;
    result.max_hold_ns = std::max(result.max_hold_ns, holds.max_ns);
    result.hold_ns += holds.total_ns;
    result.wall_ns += outcome.wall_ns;
    result.alloc_outside_ns += outcome.alloc_outside_ns;
    result.passes += outcome.passes;
    result.retries += outcome.retries;
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
  }
  result.waits = loader.Finish();
  return result;
}

struct Script {
  std::vector<std::size_t> sizes;
  std::size_t calls = 0;
  std::size_t operator()() { return sizes[std::min(calls++, sizes.size() - 1)]; }
};

struct CheckRun {
  gn::PipelineSnapshot snapshot;
  std::size_t queries = 0;
  std::size_t copies = 0;
  std::size_t copy_size = 0;
};

void RunUnitChecks() {
  FakeLibrary library(kMiB);
  std::mutex mutex;
  const auto reference = [&](std::size_t size) {
    FakeLibrary& source = library;
    const std::size_t old_size = source.size;
    source.size = size;
    std::vector<uint8_t> data(size);
    source.Serialize(data.data(), size);
    source.size = old_size;
    return Hash(data.data(), size);
  };
  const auto run = [&](std::vector<std::size_t> sizes, uint32_t attempts, bool fail_copy = false) {
    CheckRun result;
    Script script{std::move(sizes)};
    result.snapshot = gn::SnapshotPipelineLibrary(
        mutex, script,
        [&](uint8_t* data, std::size_t size) {
          ++result.copies;
          result.copy_size = size;
          if (fail_copy) return false;
          library.size = size;
          return library.Serialize(data, size);
        },
        attempts);
    result.queries = script.calls;
    const bool released = mutex.try_lock();  // never returns with the mutex held
    CHECK(released);
    if (released) mutex.unlock();
    CHECK(result.snapshot.max_lock_us <= result.snapshot.lock_us);
    return result;
  };
  const auto hash_of = [](const gn::PipelineSnapshot& snapshot) {
    return snapshot.data ? Hash(snapshot.data.get(), snapshot.size) : 0;
  };
  constexpr std::size_t S = 8 * kMiB;
  {  // Steady library: a size-only pass, one allocation outside the lock, then the copy.
    const auto r = run({S}, 3);
    CHECK(r.snapshot.status == Status::kCopied);
    CHECK(r.snapshot.passes == 2 && r.snapshot.retries == 0 && !r.snapshot.allocated_under_lock);
    CHECK(r.snapshot.size == S && r.copy_size == S && r.copies == 1 && r.queries == 2);
    CHECK(r.snapshot.capacity >= S);
    CHECK(hash_of(r.snapshot) == reference(S));
  }
  {  // The library grew between passes: one retry, still allocated outside the lock.
    const std::size_t grown = S + S / 8, last = grown + 256 * 1024;
    const auto r = run({S, grown, last}, 3);
    CHECK(r.snapshot.status == Status::kCopied);
    CHECK(r.snapshot.passes == 3 && r.snapshot.retries == 1 && !r.snapshot.allocated_under_lock);
    CHECK(r.snapshot.size == last && r.copy_size == last && r.copies == 1);
    CHECK(hash_of(r.snapshot) == reference(last));
  }
  {  // The library keeps outgrowing the buffer: after 3 unlocked attempts the
     // buffer is allocated under the lock at the exact size, like the old code.
    const auto r = run({kMiB, 2 * kMiB, 4 * kMiB, 8 * kMiB}, 3);
    CHECK(r.snapshot.status == Status::kCopied);
    CHECK(r.snapshot.passes == 4 && r.snapshot.retries == 3 && r.snapshot.allocated_under_lock);
    CHECK(r.snapshot.capacity == 8 * kMiB && r.snapshot.size == 8 * kMiB);
    CHECK(hash_of(r.snapshot) == reference(8 * kMiB));
  }
  {  // unlocked_attempts = 0 is the old algorithm: one pass, allocation under the lock.
    const auto r = run({S}, 0);
    CHECK(r.snapshot.status == Status::kCopied);
    CHECK(r.snapshot.passes == 1 && r.snapshot.retries == 0 && r.snapshot.allocated_under_lock);
    CHECK(r.snapshot.capacity == S && r.snapshot.size == S && r.copy_size == S);
    CHECK(hash_of(r.snapshot) == reference(S));
  }
  {  // The library shrank between passes: the copy gets the smaller size.
    const auto r = run({S, S / 2}, 3);
    CHECK(r.snapshot.status == Status::kCopied);
    CHECK(r.snapshot.passes == 2 && r.snapshot.size == S / 2 && r.copy_size == S / 2);
    CHECK(hash_of(r.snapshot) == reference(S / 2));
  }
  {  // Nothing to save: no allocation, no copy.
    const auto r = run({0}, 3);
    CHECK(r.snapshot.status == Status::kNothing);
    CHECK(r.snapshot.passes == 1 && r.copies == 0 && !r.snapshot.data && r.snapshot.size == 0);
  }
  {  // Serialize failed.
    const auto r = run({S}, 3, true);
    CHECK(r.snapshot.status == Status::kFailed);
    CHECK(r.snapshot.size == 0 && r.copies == 1);
  }
  {  // Out of memory outside the lock.
    const std::size_t huge = std::size_t{1} << 62;
    const auto r = run({huge}, 3);
    CHECK(r.snapshot.status == Status::kNoMemory);
    CHECK(r.snapshot.wanted == huge && !r.snapshot.data && r.copies == 0 && r.snapshot.passes == 1);
  }
  {  // Out of memory under the lock (old-algorithm mode) also releases the lock.
    const std::size_t huge = std::size_t{1} << 62;
    const auto r = run({huge}, 0);
    CHECK(r.snapshot.status == Status::kNoMemory);
    CHECK(!r.snapshot.data && r.copies == 0 && r.snapshot.passes == 1);
  }
  std::printf("unit checks: %s (%d failure(s))\n", g_failures ? "FAILED" : "ok", g_failures);
}

}  // namespace

int main(int argc, char** argv) {
  std::vector<std::size_t> sizes_mib{64, 256, 512};
  int reps = 3;
  bool checks_only = false;
  std::filesystem::path out_dir =
      argc > 0 ? std::filesystem::path(argv[0]).parent_path() : std::filesystem::path(".");
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "--quick") {
      sizes_mib = {16, 64};
      reps = 2;
    } else if (arg == "--checks-only") {
      checks_only = true;
    } else if (arg == "--reps" && i + 1 < argc) {
      reps = std::max(1, std::atoi(argv[++i]));
    } else if (arg == "--out" && i + 1 < argc) {
      out_dir = argv[++i];
    } else if (arg == "--sizes" && i + 1 < argc) {
      sizes_mib.clear();
      const std::string list = argv[++i];
      for (std::size_t start = 0; start <= list.size();) {
        const std::size_t comma = std::min(list.find(',', start), list.size());
        const std::size_t mib = std::strtoull(list.substr(start, comma - start).c_str(), nullptr, 10);
        if (mib < 1 || mib > 512) {
          std::printf("sizes must be 1..512 MiB\n");
          return 2;
        }
        sizes_mib.push_back(mib);
        start = comma + 1;
      }
    } else {
      std::printf("usage: save_lock_hold [--sizes 64,256,512] [--reps N] [--quick] [--checks-only] [--out dir]\n");
      return 2;
    }
  }
  if (out_dir.empty()) out_dir = ".";

  RunUnitChecks();
  if (checks_only) return g_failures ? 1 : 0;

  std::printf("\nsave_lock_hold: simulated pipeline-cache autosave; 2 threads (saver, loader)\n");
  std::printf("loader: lock, 1 us of work, unlock, every 50 us; %d saves per row, 30 ms apart\n", reps);
  std::printf("hold = time the saver held the mutex; wait = loader lock() latency\n\n");
  std::printf("%8s %-5s %12s %13s %9s %13s %8s %11s %11s %13s %5s %5s %6s %s\n", "size_MiB", "algo",
              "max_hold_ms", "mean_hold_ms", "save_ms", "alloc_out_ms", "samples", "max_wait_ms",
              "p99_wait_us", "p99.9_wait_us", ">1ms", ">4ms", ">16ms", "identical");
  FakeLibrary library(16 * kMiB);
  const auto old_file = out_dir / "save_lock_hold_old.bin";
  const auto new_file = out_dir / "save_lock_hold_snap.bin";
  bool files_compared = false, files_same = false;
  struct Summary {
    std::size_t mib;
    double old_hold, snap_hold, old_wait, snap_wait;
  };
  std::vector<Summary> summaries;
  for (const std::size_t mib : sizes_mib) {
    const bool smallest = mib == *std::min_element(sizes_mib.begin(), sizes_mib.end());
    uint64_t reference = 0;
    Summary summary{mib, 0, 0, 0, 0};
    for (const Algorithm algorithm : {Algorithm::kOld, Algorithm::kSnap, Algorithm::kSnap0}) {
      const std::filesystem::path* file = nullptr;
      if (smallest && !files_compared) {
        if (algorithm == Algorithm::kOld) file = &old_file;
        if (algorithm == Algorithm::kSnap) file = &new_file;
      }
      const PhaseResult r = RunPhase(algorithm, mib * kMiB, reps, library, file);
      CHECK(r.ok);
      bool identical = true;
      if (algorithm == Algorithm::kOld)
        reference = r.hash;
      else
        identical = r.hash == reference;
      CHECK(identical);
      if (file) CHECK(r.file_written);
      std::printf("%8zu %-5s %12.2f %13.2f %9.2f %13.2f %8llu %11.2f %11.1f %13.1f %5llu %5llu %6llu %s\n",
                  mib, Name(algorithm), Ms(r.max_hold_ns), Ms(r.hold_ns) / r.saves, Ms(r.wall_ns) / r.saves,
                  Ms(r.alloc_outside_ns) / r.saves, static_cast<unsigned long long>(r.waits.samples),
                  Ms(r.waits.max_ns), r.waits.p99_ns / 1e3, r.waits.p999_ns / 1e3,
                  static_cast<unsigned long long>(r.waits.over_1ms),
                  static_cast<unsigned long long>(r.waits.over_4ms),
                  static_cast<unsigned long long>(r.waits.over_16ms),
                  algorithm == Algorithm::kOld ? "reference" : (identical ? "yes" : "NO"));
      if (algorithm == Algorithm::kOld) {
        summary.old_hold = Ms(r.max_hold_ns);
        summary.old_wait = Ms(r.waits.max_ns);
      } else if (algorithm == Algorithm::kSnap) {
        summary.snap_hold = Ms(r.max_hold_ns);
        summary.snap_wait = Ms(r.waits.max_ns);
      }
    }
    summaries.push_back(summary);
    if (smallest && !files_compared) {
      files_compared = true;
      files_same = SameFiles(old_file, new_file);
      CHECK(files_same);
      std::error_code error;
      std::filesystem::remove(old_file, error);
      std::filesystem::remove(new_file, error);
    }
  }
  std::printf("\nsummary (old -> snap):\n");
  for (const auto& s : summaries)
    std::printf("  %4zu MiB: max hold %.1f -> %.1f ms (%.1fx), loader max wait %.1f -> %.1f ms\n", s.mib,
                s.old_hold, s.snap_hold, s.snap_hold > 0 ? s.old_hold / s.snap_hold : 0.0, s.old_wait,
                s.snap_wait);
  std::printf("written files byte-identical (old vs snap, smallest size): %s\n",
              files_compared ? (files_same ? "yes" : "NO") : "not run");
  std::printf("%s\n", g_failures ? "SAVE LOCK HOLD: FAILED" : "SAVE LOCK HOLD: OK");
  return g_failures ? 1 : 0;
}
