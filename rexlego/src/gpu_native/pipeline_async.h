// Opt-in asynchronous PSO creation for GetPipeline (draw.cpp).
//
// LEGO_NATIVE_PSO_ASYNC=1 moves the driver compile of a g_pipelines miss onto
// a small pool. The drawing thread waits for it within a per-miss and a
// per-frame budget; if the PSO is still not ready the draw is skipped, and a
// later draw with the same key joins the same compile or finds its result.
// Unset (the default), nothing here starts a thread, allocates or logs, and
// GetPipeline keeps its synchronous path.
//
//   LEGO_NATIVE_PSO_ASYNC=1           enable (default off)
//   LEGO_NATIVE_PSO_ASYNC_THREADS     compile threads, 1..4 (default 2)
//   LEGO_NATIVE_PSO_ASYNC_WAIT_US     longest wait for one miss (default 2000)
//   LEGO_NATIVE_PSO_ASYNC_FRAME_US    total wait per ~16.7 ms window (default 4000)
//
// The cache mutex (g_pipeline_mutex) is never held while waiting on a compile
// or on the pool; jobs take it only to publish.
#pragma once

#include <windows.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <system_error>
#include <thread>
#include <type_traits>
#include <unordered_map>
#include <utility>
#include <vector>

#include <rex/logging.h>

#include "gpu_native/pipeline_stats.h"

namespace legodimensions::gpu_native {

// One posted compile. Waiters and the job share it, so it outlives its table
// entry. Finish() runs once, after the result has been published.
class AsyncPipelineCompile {
 public:
  void Finish(bool ok) {
    {
      std::lock_guard lock(mutex_);
      ok_ = ok;
      finished_ = true;
    }
    finished_cv_.notify_all();
  }

  // True once finished; waits at most budget_us.
  bool WaitFor(uint64_t budget_us) {
    std::unique_lock lock(mutex_);
    if (!finished_ && budget_us)
      finished_cv_.wait_for(lock, std::chrono::microseconds(budget_us), [this] { return finished_; });
    return finished_;
  }

  bool Finished() const {
    std::lock_guard lock(mutex_);
    return finished_;
  }

  bool Succeeded() const {
    std::lock_guard lock(mutex_);
    return finished_ && ok_;
  }

 private:
  mutable std::mutex mutex_;
  std::condition_variable finished_cv_;
  bool finished_ = false;
  bool ok_ = false;
};

// Compiles in flight, keyed like g_pipelines; every call holds the cache
// mutex. An entry lives from Begin() until its job has published (or failed)
// and called End(). Failures are not cached: the next miss posts again, as
// the synchronous path retries. The map is created by the first Begin(), so
// an unused table allocates nothing.
template <class Key, class Hash = std::hash<Key>>
class AsyncPipelineTable {
 public:
  using Compile = std::shared_ptr<AsyncPipelineCompile>;

  Compile Find(const Key& key) const {
    if (!map_) return nullptr;
    const auto found = map_->find(key);
    return found == map_->end() ? nullptr : found->second;
  }

  // The caller missed both caches and holds the key's creation lease.
  Compile Begin(const Key& key) {
    if (!map_) map_ = std::make_unique<Map>();
    auto compile = std::make_shared<AsyncPipelineCompile>();
    (*map_)[key] = compile;
    return compile;
  }

  // Drops the entry only if it still belongs to compile.
  void End(const Key& key, const Compile& compile) {
    if (!map_) return;
    const auto found = map_->find(key);
    if (found != map_->end() && found->second == compile) map_->erase(found);
  }

  // Device teardown, after DrainAsyncPipelineJobs().
  void Clear() { map_.reset(); }
  std::size_t Size() const { return map_ ? map_->size() : 0; }

 private:
  using Map = std::unordered_map<Key, Compile, Hash>;
  std::unique_ptr<Map> map_;
};

// Fixed compile threads ("PSO compile N", pso_stats::kAsyncThread). Drain()
// returns once every posted job, queued or running, has finished and dropped
// its captures. The destructor runs what is queued, then joins.
class AsyncPipelinePool {
 public:
  explicit AsyncPipelinePool(unsigned threads) {
    threads_.reserve(threads);
    for (unsigned i = 0; i < threads; ++i) {
      try {
        threads_.emplace_back([this, i] { Run(i); });
      } catch (const std::system_error&) {
        break;
      }
    }
  }

  ~AsyncPipelinePool() {
    {
      std::lock_guard lock(mutex_);
      stopping_ = true;
    }
    work_.notify_all();
    for (auto& thread : threads_) thread.join();
  }

  AsyncPipelinePool(const AsyncPipelinePool&) = delete;
  AsyncPipelinePool& operator=(const AsyncPipelinePool&) = delete;

  // Runs the job inline if no thread could be started.
  void Post(std::function<void()> job) {
    if (threads_.empty()) {
      RunJob(job);
      return;
    }
    {
      std::lock_guard lock(mutex_);
      ++pending_;
      queue_.push_back(std::move(job));
    }
    work_.notify_one();
  }

  void Drain() {
    std::unique_lock lock(mutex_);
    idle_.wait(lock, [this] { return pending_ == 0; });
  }

  std::size_t Threads() const { return threads_.size(); }

 private:
  // Destroys the captures before the caller counts the job as done.
  static void RunJob(std::function<void()>& job) {
    try {
      job();
    } catch (...) {
    }
    job = nullptr;
  }

  void Run(unsigned index) {
    pso_stats::t_thread_kind = pso_stats::kAsyncThread;
    const std::wstring name = L"PSO compile " + std::to_wstring(index + 1);
    SetThreadDescription(GetCurrentThread(), name.c_str());
    std::unique_lock lock(mutex_);
    for (;;) {
      work_.wait(lock, [this] { return stopping_ || !queue_.empty(); });
      if (queue_.empty()) return;
      auto job = std::move(queue_.front());
      queue_.pop_front();
      lock.unlock();
      RunJob(job);
      lock.lock();
      if (--pending_ == 0) idle_.notify_all();
    }
  }

  std::mutex mutex_;
  std::condition_variable work_, idle_;
  std::deque<std::function<void()>> queue_;
  std::size_t pending_ = 0;
  bool stopping_ = false;
  std::vector<std::thread> threads_;
};

// A pipeline description that owns its input slot, input element and spec
// constant arrays: GetPipeline builds them in locals (integer-input elements
// in a thread_local) and a posted compile outlives those. The layout and the
// shaders stay borrowed (the device and the captured shader owners keep them
// alive), as do element semantic names (string literals, UsageName()).
template <class Desc>
struct OwnedPipelineDesc {
  using Slot = std::remove_cvref_t<decltype(*std::declval<const Desc&>().inputSlots)>;
  using Element = std::remove_cvref_t<decltype(*std::declval<const Desc&>().inputElements)>;
  using SpecConstant = std::remove_cvref_t<decltype(*std::declval<const Desc&>().specConstants)>;

  explicit OwnedPipelineDesc(const Desc& source)
      : desc(source),
        slots(Copy(source.inputSlots, source.inputSlotsCount)),
        elements(Copy(source.inputElements, source.inputElementsCount)),
        spec_constants(Copy(source.specConstants, source.specConstantsCount)) {
    Repoint();
  }
  OwnedPipelineDesc(const OwnedPipelineDesc& other)
      : desc(other.desc), slots(other.slots), elements(other.elements), spec_constants(other.spec_constants) {
    Repoint();
  }
  OwnedPipelineDesc(OwnedPipelineDesc&& other) noexcept
      : desc(other.desc),
        slots(std::move(other.slots)),
        elements(std::move(other.elements)),
        spec_constants(std::move(other.spec_constants)) {
    Repoint();
    other.Repoint();
  }
  OwnedPipelineDesc& operator=(const OwnedPipelineDesc&) = delete;
  OwnedPipelineDesc& operator=(OwnedPipelineDesc&&) = delete;

  Desc desc;
  std::vector<Slot> slots;
  std::vector<Element> elements;
  std::vector<SpecConstant> spec_constants;

 private:
  template <class T>
  static std::vector<T> Copy(const T* data, std::size_t count) {
    return data && count ? std::vector<T>(data, data + count) : std::vector<T>();
  }

  void Repoint() {
    desc.inputSlots = slots.empty() ? nullptr : slots.data();
    desc.inputSlotsCount = static_cast<decltype(desc.inputSlotsCount)>(slots.size());
    desc.inputElements = elements.empty() ? nullptr : elements.data();
    desc.inputElementsCount = static_cast<decltype(desc.inputElementsCount)>(elements.size());
    desc.specConstants = spec_constants.empty() ? nullptr : spec_constants.data();
    desc.specConstantsCount = static_cast<decltype(desc.specConstantsCount)>(spec_constants.size());
  }
};

// Total wait allowed per window of about one 60 Hz frame. Self-contained: a
// window starts at the first reservation after the previous one elapsed, so
// no frame hook is needed. Concurrent waiters reserve their share up front;
// Settle() then charges what the wait really took, timer overshoot included.
class AsyncWaitBudget {
 public:
  using Clock = std::chrono::steady_clock;
  static constexpr std::chrono::microseconds kWindow{16'667};

  struct Grant {
    uint64_t window = 0;
    uint64_t nanos = 0;
  };

  Grant Reserve(Clock::time_point now, uint64_t want_ns, uint64_t frame_ns) {
    std::lock_guard lock(mutex_);
    if (!window_ || now - start_ >= kWindow) {
      start_ = now;
      ++window_;
      used_ns_ = 0;
    }
    const uint64_t left = used_ns_ < frame_ns ? frame_ns - used_ns_ : 0;
    const uint64_t nanos = (std::min)(want_ns, left);
    used_ns_ += nanos;
    return {window_, nanos};
  }

  // A grant from an earlier window is not charged.
  void Settle(const Grant& grant, uint64_t actual_ns) {
    std::lock_guard lock(mutex_);
    if (grant.window != window_) return;
    used_ns_ = (used_ns_ >= grant.nanos ? used_ns_ - grant.nanos : 0) + actual_ns;
  }

  uint64_t UsedNanos() const {
    std::lock_guard lock(mutex_);
    return used_ns_;
  }

 private:
  mutable std::mutex mutex_;
  Clock::time_point start_{};
  uint64_t window_ = 0;
  uint64_t used_ns_ = 0;
};

struct AsyncPipelineSettings {
  bool enabled = false;
  unsigned threads = 2;
  uint64_t wait_us = 2000;
  uint64_t frame_us = 4000;
};

// Unset, empty or malformed values keep the default; others are clamped.
inline uint64_t ParseAsyncPipelineSetting(const char* text, uint64_t fallback, uint64_t low, uint64_t high) {
  if (!text || *text < '0' || *text > '9') return fallback;
  char* end = nullptr;
  const unsigned long long value = std::strtoull(text, &end, 10);
  if (*end) return fallback;
  return std::clamp<uint64_t>(value, low, high);
}

// The environment as it is now. Enabled like LEGO_NATIVE_PSO_STATS: set,
// nonempty and not "0".
inline AsyncPipelineSettings ReadAsyncPipelineSettings() {
  AsyncPipelineSettings settings;
  const char* enabled = std::getenv("LEGO_NATIVE_PSO_ASYNC");
  settings.enabled = enabled && *enabled && std::strcmp(enabled, "0") != 0;
  if (!settings.enabled) return settings;
  settings.threads = unsigned(ParseAsyncPipelineSetting(std::getenv("LEGO_NATIVE_PSO_ASYNC_THREADS"), 2, 1, 4));
  settings.wait_us = ParseAsyncPipelineSetting(std::getenv("LEGO_NATIVE_PSO_ASYNC_WAIT_US"), 2000, 0, 1'000'000);
  settings.frame_us = ParseAsyncPipelineSetting(std::getenv("LEGO_NATIVE_PSO_ASYNC_FRAME_US"), 4000, 0, 1'000'000);
  return settings;
}

// Read once, on first use (a function-local static: no heap, thread-safe).
inline const AsyncPipelineSettings& AsyncPipelineConfig() {
  static const AsyncPipelineSettings settings = [] {
    const AsyncPipelineSettings read = ReadAsyncPipelineSettings();
    if (read.enabled)
      REXLOG_INFO("Native GPU: async PSO compile on (threads={} wait_us={} frame_us={})", read.threads,
                  read.wait_us, read.frame_us);
    return read;
  }();
  return settings;
}

inline bool AsyncPipelineCompileEnabled() { return AsyncPipelineConfig().enabled; }

struct AsyncPipelineRuntime {
  explicit AsyncPipelineRuntime(const AsyncPipelineSettings& config) : settings(config), pool(config.threads) {}
  const AsyncPipelineSettings settings;
  AsyncWaitBudget budget;
  AsyncPipelinePool pool;
};

// Null until the first post with the toggle on. Never deleted (like Plume's
// caches), so no static destructor joins compile threads during exit.
inline std::atomic<AsyncPipelineRuntime*> g_async_pipeline_runtime{nullptr};

inline AsyncPipelineRuntime& AsyncPipelineRuntimeInstance() {
  static AsyncPipelineRuntime* const runtime = [] {
    auto* created = new AsyncPipelineRuntime(AsyncPipelineConfig());
    g_async_pipeline_runtime.store(created, std::memory_order_release);
    return created;
  }();
  return *runtime;
}

// Toggle off: runs the job inline (GetPipeline never posts then).
inline void PostAsyncPipelineJob(std::function<void()> job) {
  if (!AsyncPipelineCompileEnabled()) {
    job();
    return;
  }
  AsyncPipelineRuntimeInstance().pool.Post(std::move(job));
}

// True when the compile finished and succeeded, after waiting at most
// LEGO_NATIVE_PSO_ASYNC_WAIT_US and never past the window's frame budget.
// Without timeBeginPeriod(1) a short wait can overshoot to a 15.6 ms tick;
// that is charged, so the rest of the window does not wait. Call without the
// cache mutex.
inline bool WaitForAsyncPipeline(AsyncPipelineCompile& compile) {
  auto* const runtime = g_async_pipeline_runtime.load(std::memory_order_acquire);
  if (!runtime || compile.Finished()) return compile.Succeeded();
  const auto start = AsyncWaitBudget::Clock::now();
  const auto grant =
      runtime->budget.Reserve(start, runtime->settings.wait_us * 1000, runtime->settings.frame_us * 1000);
  const bool finished = compile.WaitFor(grant.nanos / 1000);
  const auto waited = uint64_t(
      std::chrono::duration_cast<std::chrono::nanoseconds>(AsyncWaitBudget::Clock::now() - start).count());
  runtime->budget.Settle(grant, waited);
  if (pso_stats::Enabled()) pso_stats::OnAsyncWait(waited, !finished);
  return compile.Succeeded();
}

// Device teardown, before the caches are cleared: waits until every posted
// compile has published. Never creates the pool.
inline void DrainAsyncPipelineJobs() {
  if (auto* const runtime = g_async_pipeline_runtime.load(std::memory_order_acquire)) runtime->pool.Drain();
}

namespace async_pipeline_detail {

// lock is released on entry and held on return.
template <class Map>
typename Map::mapped_type::pointer WaitThenFind(std::unique_lock<std::mutex>& lock, const Map& pipelines,
                                                const typename Map::key_type& key,
                                                std::shared_ptr<AsyncPipelineCompile> compile) {
  WaitForAsyncPipeline(*compile);
  compile.reset();
  lock.lock();
  if (const auto found = pipelines.find(key); found != pipelines.end()) return found->second.get();
  if (pso_stats::Enabled()) pso_stats::OnAsyncSkippedDraw();
  return nullptr;
}

}  // namespace async_pipeline_detail

// GetPipeline found a compile for key in flight: waits within the budget with
// lock released, then returns the published PSO, or null (the caller skips
// the draw). The caller holds lock and no creation lease.
template <class Map>
typename Map::mapped_type::pointer AwaitAsyncPipeline(std::unique_lock<std::mutex>& lock, const Map& pipelines,
                                                      const typename Map::key_type& key,
                                                      std::shared_ptr<AsyncPipelineCompile> compile) {
  lock.unlock();
  return async_pipeline_detail::WaitThenFind(lock, pipelines, key, std::move(compile));
}

// GetPipeline missed both caches (lock held): registers the compile, posts
// create(), which returns the finished PSO or null, and then waits like
// AwaitAsyncPipeline. The creation lease may be released just before this
// call, since the entry is visible before lock is dropped. The job publishes
// under the cache mutex, ends the entry, then completes the compile.
template <class Map, class Hash, class Create>
typename Map::mapped_type::pointer CompilePipelineAsync(std::unique_lock<std::mutex>& lock, Map& pipelines,
                                                        AsyncPipelineTable<typename Map::key_type, Hash>& table,
                                                        const typename Map::key_type& key, Create create) {
  auto compile = table.Begin(key);
  std::mutex& mutex = *lock.mutex();
  lock.unlock();
  if (pso_stats::Enabled()) pso_stats::OnAsyncPosted();
  PostAsyncPipelineJob([&mutex, &pipelines, &table, key, compile, create = std::move(create)]() mutable {
    typename Map::mapped_type pipeline;
    try {
      pipeline = create();
    } catch (...) {
      pipeline = nullptr;
    }
    const bool ok = pipeline != nullptr;
    {
      std::lock_guard guard(mutex);
      if (ok) pipelines.emplace(key, std::move(pipeline));
      table.End(key, compile);
    }
    compile->Finish(ok);
    if (pso_stats::Enabled()) pso_stats::OnAsyncFinished(ok);
  });
  return async_pipeline_detail::WaitThenFind(lock, pipelines, key, std::move(compile));
}

}  // namespace legodimensions::gpu_native
