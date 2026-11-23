// Agent 6, task #5 item 4: tests for gpu_native/pipeline_async.h, the opt-in
// async PSO compile behind LEGO_NATIVE_PSO_ASYNC (and Lease::Release()).
//
//   powershell -NoProfile -ExecutionPolicy Bypass -File bench/agent6/run_benches.ps1 -Only async_table_test
//
// The process first runs with the toggle unset (nothing may start, allocate or
// log), then re-runs itself with LEGO_NATIVE_PSO_ASYNC=1 (--enabled) for the
// pooled path, since the toggle is read once per process. Jobs sleep or block
// instead of spinning, with at most two pool threads. Timing checks use wide
// bounds because the machine is loaded.

#include "gpu_native/pipeline_async.h"
#include "gpu_native/pipeline_creation_gate.h"

#include <process.h>
#include <tlhelp32.h>

#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <new>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <unordered_map>
#include <vector>

// The real description, to check OwnedPipelineDesc against Plume's fields.
#include "../../DimensionsRecomp/thirdparty/plume/plume_render_interface_types.h"

// Counts operator new calls, for the toggle-off checks.
std::atomic<uint64_t> g_allocations{0};
void* operator new(std::size_t size) {
  g_allocations.fetch_add(1, std::memory_order_relaxed);
  if (void* memory = std::malloc(size ? size : 1)) return memory;
  throw std::bad_alloc();
}
void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t) noexcept { std::free(memory); }

namespace gn = legodimensions::gpu_native;
using namespace std::chrono_literals;

namespace {

int g_failures = 0;
#define CHECK(...)                                                        \
  do {                                                                    \
    if (!(__VA_ARGS__)) {                                                 \
      std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #__VA_ARGS__);  \
      ++g_failures;                                                       \
    }                                                                     \
  } while (0)

const char* g_prefix = "";
void Report(const char* name, int failures_before) {
  std::printf("%s%-26s %s\n", g_prefix, name, g_failures == failures_before ? "PASS" : "FAIL");
}

constexpr const char* kToggles[] = {"LEGO_NATIVE_PSO_ASYNC", "LEGO_NATIVE_PSO_ASYNC_THREADS",
                                    "LEGO_NATIVE_PSO_ASYNC_WAIT_US", "LEGO_NATIVE_PSO_ASYNC_FRAME_US"};

void ClearToggles() {
  for (const char* name : kToggles) _putenv_s(name, "");
}

int64_t MillisSince(std::chrono::steady_clock::time_point start) {
  return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now() - start).count();
}

std::set<DWORD> ProcessThreads() {
  std::set<DWORD> ids;
  const HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
  if (snapshot == INVALID_HANDLE_VALUE) return ids;
  THREADENTRY32 entry{};
  entry.dwSize = sizeof(entry);
  const DWORD process = GetCurrentProcessId();
  for (BOOL more = Thread32First(snapshot, &entry); more; more = Thread32Next(snapshot, &entry))
    if (entry.th32OwnerProcessID == process) ids.insert(entry.th32ThreadID);
  CloseHandle(snapshot);
  return ids;
}

std::size_t NewThreads(const std::set<DWORD>& before) {
  std::size_t added = 0;
  for (const DWORD id : ProcessThreads()) added += before.count(id) ? 0 : 1;
  return added;
}

// Threads of this process whose description starts with prefix. Unlike
// NewThreads(), immune to thread ids being reused after startup threads exit.
std::size_t NamedThreads(const wchar_t* prefix) {
  std::size_t named = 0;
  for (const DWORD id : ProcessThreads()) {
    const HANDLE thread = OpenThread(THREAD_QUERY_LIMITED_INFORMATION, FALSE, id);
    if (!thread) continue;
    PWSTR name = nullptr;
    if (SUCCEEDED(GetThreadDescription(thread, &name)) && name) {
      if (std::wstring_view(name).starts_with(prefix)) ++named;
      LocalFree(name);
    }
    CloseHandle(thread);
  }
  return named;
}

constexpr const wchar_t* kPoolName = L"PSO compile ";

std::wstring ThreadName() {
  PWSTR name = nullptr;
  std::wstring result;
  if (SUCCEEDED(GetThreadDescription(GetCurrentThread(), &name)) && name) {
    result = name;
    LocalFree(name);
  }
  return result;
}

using Map = std::unordered_map<int, std::unique_ptr<int>>;

// Must run first: the toggle is read once, and nothing may have started.
void TestToggleOff() {
  const int before = g_failures;
  const auto threads = ProcessThreads();
  bench_log::Take();
  const uint64_t allocations = g_allocations.load();
  const bool enabled = gn::AsyncPipelineCompileEnabled();
  const bool enabled_again = gn::AsyncPipelineCompileEnabled();
  gn::DrainAsyncPipelineJobs();
  gn::AsyncPipelineCompile pending;
  const bool pending_ready = gn::WaitForAsyncPipeline(pending);
  gn::AsyncPipelineTable<int> table;
  const bool table_empty = !table.Find(1) && table.Size() == 0;
  table.Clear();
  const uint64_t allocated = g_allocations.load() - allocations;
  CHECK(!enabled && !enabled_again);
  CHECK(!pending_ready);
  CHECK(table_empty);
  CHECK(allocated == 0);
  CHECK(gn::g_async_pipeline_runtime.load() == nullptr);
  // A finished compile is reported without waiting.
  pending.Finish(true);
  CHECK(gn::WaitForAsyncPipeline(pending));
  // Post runs inline on the caller.
  std::thread::id ran_on;
  gn::PostAsyncPipelineJob([&ran_on] { ran_on = std::this_thread::get_id(); });
  CHECK(ran_on == std::this_thread::get_id());
  CHECK(gn::g_async_pipeline_runtime.load() == nullptr);
  CHECK(NewThreads(threads) == 0);
  CHECK(NamedThreads(kPoolName) == 0);
  CHECK(bench_log::Take().empty());
  Report("toggle off", before);
}

void TestSettings() {
  const int before = g_failures;
  CHECK(gn::ParseAsyncPipelineSetting(nullptr, 2, 1, 4) == 2);
  CHECK(gn::ParseAsyncPipelineSetting("", 2, 1, 4) == 2);
  CHECK(gn::ParseAsyncPipelineSetting("x", 2, 1, 4) == 2);
  CHECK(gn::ParseAsyncPipelineSetting("-1", 2, 1, 4) == 2);
  CHECK(gn::ParseAsyncPipelineSetting(" 3", 2, 1, 4) == 2);
  CHECK(gn::ParseAsyncPipelineSetting("3x", 2, 1, 4) == 2);
  CHECK(gn::ParseAsyncPipelineSetting("0", 2, 1, 4) == 1);
  CHECK(gn::ParseAsyncPipelineSetting("3", 2, 1, 4) == 3);
  CHECK(gn::ParseAsyncPipelineSetting("9", 2, 1, 4) == 4);
  CHECK(gn::ParseAsyncPipelineSetting("99999999999999999999999", 2, 1, 4) == 4);
  CHECK(gn::ParseAsyncPipelineSetting("0", 2000, 0, 1'000'000) == 0);
  // ReadAsyncPipelineSettings() reads the environment as it is now.
  CHECK(!gn::ReadAsyncPipelineSettings().enabled);
  _putenv_s("LEGO_NATIVE_PSO_ASYNC", "0");
  CHECK(!gn::ReadAsyncPipelineSettings().enabled);
  _putenv_s("LEGO_NATIVE_PSO_ASYNC", "1");
  _putenv_s("LEGO_NATIVE_PSO_ASYNC_THREADS", "7");
  _putenv_s("LEGO_NATIVE_PSO_ASYNC_WAIT_US", "abc");
  _putenv_s("LEGO_NATIVE_PSO_ASYNC_FRAME_US", "5000");
  const auto read = gn::ReadAsyncPipelineSettings();
  CHECK(read.enabled && read.threads == 4 && read.wait_us == 2000 && read.frame_us == 5000);
  _putenv_s("LEGO_NATIVE_PSO_ASYNC_THREADS", "0");
  CHECK(gn::ReadAsyncPipelineSettings().threads == 1);
  ClearToggles();
  const auto defaults = gn::AsyncPipelineSettings{};
  CHECK(!defaults.enabled && defaults.threads == 2 && defaults.wait_us == 2000 && defaults.frame_us == 4000);
  // The cached configuration does not follow the environment.
  CHECK(!gn::AsyncPipelineCompileEnabled());
  CHECK(bench_log::Take().empty());
  Report("settings", before);
}

void TestTable() {
  const int before = g_failures;
  gn::AsyncPipelineTable<int> table;
  CHECK(table.Size() == 0 && !table.Find(5));
  const auto first = table.Begin(5);
  CHECK(first && table.Find(5) == first && table.Size() == 1 && !table.Find(6));
  table.End(6, first);
  CHECK(table.Size() == 1);
  const auto second = table.Begin(5);
  table.End(5, first);  // a stale compile leaves the newer entry alone
  CHECK(table.Find(5) == second && table.Size() == 1);
  table.End(5, second);
  CHECK(table.Size() == 0 && !table.Find(5));
  table.Begin(1);
  table.Begin(2);
  CHECK(table.Size() == 2);
  table.Clear();
  CHECK(table.Size() == 0 && !table.Find(1) && !table.Find(2));
  table.End(1, first);  // after Clear: harmless
  // An entry's compile outlives the table entry.
  CHECK(!first->Finished());
  first->Finish(true);
  CHECK(first->Succeeded());
  Report("table", before);
}

void TestCompileWait() {
  const int before = g_failures;
  gn::AsyncPipelineCompile compile;
  CHECK(!compile.WaitFor(0) && !compile.Finished() && !compile.Succeeded());
  auto start = std::chrono::steady_clock::now();
  CHECK(!compile.WaitFor(20'000));
  auto waited = MillisSince(start);
  CHECK(waited >= 15 && waited < 1000);
  // Finish() on another thread wakes the waiter long before its budget.
  std::thread finisher([&compile] {
    std::this_thread::sleep_for(10ms);
    compile.Finish(true);
  });
  start = std::chrono::steady_clock::now();
  CHECK(compile.WaitFor(5'000'000));
  waited = MillisSince(start);
  finisher.join();
  CHECK(waited < 2000);
  CHECK(compile.Finished() && compile.Succeeded());
  gn::AsyncPipelineCompile failed;
  failed.Finish(false);
  CHECK(failed.WaitFor(1000) && failed.Finished() && !failed.Succeeded());
  Report("compile wait", before);
}

void TestBudget() {
  const int before = g_failures;
  constexpr uint64_t kMs = 1'000'000;
  gn::AsyncWaitBudget budget;
  const auto t0 = gn::AsyncWaitBudget::Clock::now();
  const auto a = budget.Reserve(t0, 2 * kMs, 4 * kMs);
  const auto b = budget.Reserve(t0 + 1ms, 2 * kMs, 4 * kMs);
  const auto c = budget.Reserve(t0 + 2ms, 2 * kMs, 4 * kMs);
  CHECK(a.nanos == 2 * kMs && b.nanos == 2 * kMs && c.nanos == 0);
  CHECK(a.window == b.window && b.window == c.window);
  budget.Settle(a, kMs / 2);  // refunds 1.5 ms
  const auto d = budget.Reserve(t0 + 3ms, 2 * kMs, 4 * kMs);
  CHECK(d.nanos == 1'500'000);
  budget.Settle(d, 15 * kMs);  // a timer overshoot is charged
  CHECK(budget.Reserve(t0 + 4ms, 2 * kMs, 4 * kMs).nanos == 0);
  // About one frame later a new window starts.
  const auto e = budget.Reserve(t0 + 17ms, 2 * kMs, 4 * kMs);
  CHECK(e.nanos == 2 * kMs && e.window == a.window + 1);
  budget.Settle(b, 0);  // from the previous window: ignored
  CHECK(budget.UsedNanos() == 2 * kMs);
  CHECK(budget.Reserve(t0 + 18ms, 10 * kMs, 4 * kMs).nanos == 2 * kMs);
  gn::AsyncWaitBudget zero;
  CHECK(zero.Reserve(t0, 2 * kMs, 0).nanos == 0);
  CHECK(zero.Reserve(t0, 0, 4 * kMs).nanos == 0);
  Report("wait budget", before);
}

void TestPool() {
  const int before = g_failures;
  const auto threads = ProcessThreads();
  std::atomic<int> done{0}, async_kind{0}, named{0};
  {
    gn::AsyncPipelinePool pool(2);
    CHECK(pool.Threads() == 2);
    for (int i = 0; i < 20; ++i)
      pool.Post([&done, &async_kind, &named, i] {
        if (gn::pso_stats::t_thread_kind == gn::pso_stats::kAsyncThread) ++async_kind;
        if (ThreadName().starts_with(kPoolName)) ++named;
        std::this_thread::sleep_for(std::chrono::microseconds(200 * (i % 4)));
        ++done;
      });
    pool.Drain();
    CHECK(done == 20 && async_kind == 20 && named == 20);
    std::printf("pool: %zu new threads, %zu named\n", NewThreads(threads), NamedThreads(kPoolName));
    CHECK(NamedThreads(kPoolName) == 2);
    CHECK(gn::pso_stats::t_thread_kind == gn::pso_stats::kOtherThread);
    // Drain() waits for a running job and for its captures to be destroyed.
    std::atomic<bool> finished{false}, released{false};
    auto token = std::shared_ptr<int>(new int(0), [&released](int* value) {
      delete value;
      released = true;
    });
    const auto start = std::chrono::steady_clock::now();
    pool.Post([&finished, token] {
      std::this_thread::sleep_for(50ms);
      finished = true;
    });
    token.reset();
    pool.Drain();
    CHECK(finished && released);
    CHECK(MillisSince(start) >= 40);
    // A throwing job does not stop its thread.
    pool.Post([] { throw std::runtime_error("job"); });
    pool.Post([&done] { ++done; });
    pool.Drain();
    CHECK(done == 21);
    // The destructor runs what is still queued, then joins.
    for (int i = 0; i < 4; ++i)
      pool.Post([&done] {
        std::this_thread::sleep_for(2ms);
        ++done;
      });
  }
  CHECK(done == 25);
  Report("pool", before);
}

struct FakeSlot {
  uint32_t index = 0, stride = 0;
};
struct FakeElement {
  const char* semanticName = nullptr;
  uint32_t slotIndex = 0, alignedByteOffset = 0;
};
struct FakeSpec {
  uint32_t index = 0, value = 0;
};
struct FakeDesc {
  const void* pipelineLayout = nullptr;
  const FakeSlot* inputSlots = nullptr;
  uint32_t inputSlotsCount = 0;
  const FakeElement* inputElements = nullptr;
  uint32_t inputElementsCount = 0;
  const FakeSpec* specConstants = nullptr;
  uint32_t specConstantsCount = 0;
  uint32_t renderTargetCount = 0;
};

void TestOwnedDesc() {
  const int before = g_failures;
  int layout = 0;
  FakeSlot slots[3] = {{0, 16}, {1, 32}, {2, 48}};
  FakeElement elements[2] = {{"POSITION", 0, 0}, {"TEXCOORD", 1, 8}};
  FakeDesc source;
  source.pipelineLayout = &layout;
  source.inputSlots = slots;
  source.inputSlotsCount = 3;
  source.inputElements = elements;
  source.inputElementsCount = 2;
  source.renderTargetCount = 2;
  gn::OwnedPipelineDesc owned(source);
  // The caller's arrays change (or go out of scope) after posting.
  slots[1] = {9, 9};
  elements[0].alignedByteOffset = 99;
  CHECK(owned.desc.inputSlots != slots && owned.desc.inputSlots == owned.slots.data());
  CHECK(owned.desc.inputSlotsCount == 3 && owned.desc.inputSlots[1].stride == 32);
  CHECK(owned.desc.inputElements == owned.elements.data() && owned.desc.inputElementsCount == 2);
  CHECK(owned.desc.inputElements[0].alignedByteOffset == 0 && owned.desc.inputElements[1].alignedByteOffset == 8);
  CHECK(owned.desc.inputElements[1].semanticName == elements[1].semanticName);  // literals stay borrowed
  CHECK(owned.desc.specConstants == nullptr && owned.desc.specConstantsCount == 0);
  CHECK(owned.desc.pipelineLayout == &layout && owned.desc.renderTargetCount == 2);
  // Copies and moves point at their own storage.
  const gn::OwnedPipelineDesc<FakeDesc> copy(owned);
  CHECK(copy.desc.inputSlots == copy.slots.data() && copy.desc.inputSlots != owned.desc.inputSlots);
  CHECK(copy.desc.inputSlots[2].stride == 48 && copy.desc.inputElements == copy.elements.data());
  gn::OwnedPipelineDesc<FakeDesc> movable(owned);
  const FakeSlot* storage = movable.slots.data();
  const gn::OwnedPipelineDesc<FakeDesc> moved(std::move(movable));
  CHECK(moved.desc.inputSlots == storage && moved.desc.inputSlots == moved.slots.data());
  CHECK(movable.desc.inputSlots == nullptr && movable.desc.inputSlotsCount == 0);  // NOLINT(bugprone-use-after-move)
  // A job holding one survives std::function copies, as GetPipeline's does.
  std::function<uint32_t()> job = [held = gn::OwnedPipelineDesc(source)] {
    return held.desc.inputSlots[1].stride + held.desc.inputSlotsCount;
  };
  slots[1] = {7, 7};
  const auto job_copy = job;
  job = nullptr;
  CHECK(job_copy() == 9 + 3);
  // Plume's description: spec constants too.
  plume::RenderInputSlot real_slots[2] = {plume::RenderInputSlot(0, 16), plume::RenderInputSlot(1, 24)};
  plume::RenderInputElement real_elements[1] = {
      plume::RenderInputElement("POSITION", 0, 0, plume::RenderFormat::R32G32B32_FLOAT, 0, 0)};
  plume::RenderSpecConstant specs[2] = {plume::RenderSpecConstant(0, 5), plume::RenderSpecConstant(3, 7)};
  plume::RenderGraphicsPipelineDesc real;
  real.inputSlots = real_slots;
  real.inputSlotsCount = 2;
  real.inputElements = real_elements;
  real.inputElementsCount = 1;
  real.specConstants = specs;
  real.specConstantsCount = 2;
  real.renderTargetCount = 1;
  const gn::OwnedPipelineDesc owned_real(real);
  specs[1].value = 0;
  real_slots[1].stride = 0;
  CHECK(owned_real.desc.specConstants == owned_real.spec_constants.data() && owned_real.desc.specConstantsCount == 2);
  CHECK(owned_real.desc.specConstants[1].index == 3 && owned_real.desc.specConstants[1].value == 7);
  CHECK(owned_real.desc.inputSlots[1].stride == 24 && owned_real.desc.inputElementsCount == 1);
  CHECK(owned_real.desc.renderTargetCount == 1);
  Report("owned desc", before);
}

void TestLease() {
  const int before = g_failures;
  gn::PipelineCreationGate<int> gate;
  auto lease = gate.Acquire(3);
  std::atomic<bool> acquired{false};
  std::thread other([&gate, &acquired] {
    auto second = gate.Acquire(3);
    acquired = true;
  });
  std::this_thread::sleep_for(20ms);
  CHECK(!acquired);
  lease.Release();
  other.join();
  CHECK(acquired);
  lease.Release();  // a second call is harmless
  gate.ClearAfterDrain();  // asserts that no lease still holds its mutex
  Report("lease release", before);
}

// Toggle off, PostAsyncPipelineJob() runs the job inline: the GetPipeline
// helpers still publish, end the entry and never cache a failure.
void TestCompileInline() {
  const int before = g_failures;
  std::mutex mutex;
  Map pipelines;
  gn::AsyncPipelineTable<int> table;
  int attempts = 0;
  const auto failing = [&attempts] {
    ++attempts;
    return std::unique_ptr<int>();
  };
  std::unique_lock lock(mutex);
  CHECK(gn::CompilePipelineAsync(lock, pipelines, table, 7, failing) == nullptr);
  CHECK(lock.owns_lock() && table.Size() == 0 && pipelines.empty() && attempts == 1);
  CHECK(!table.Find(7));  // so the next miss posts again
  CHECK(gn::CompilePipelineAsync(lock, pipelines, table, 7, failing) == nullptr && attempts == 2);
  int* const published = gn::CompilePipelineAsync(lock, pipelines, table, 7, [] { return std::make_unique<int>(42); });
  CHECK(published && *published == 42 && pipelines.size() == 1 && table.Size() == 0);
  CHECK(gn::CompilePipelineAsync(lock, pipelines, table, 8, []() -> std::unique_ptr<int> {
          throw std::runtime_error("driver");
        }) == nullptr);
  CHECK(table.Size() == 0 && !pipelines.count(8));
  CHECK(gn::g_async_pipeline_runtime.load() == nullptr);
  Report("compile inline (off)", before);
}

// --enabled: LEGO_NATIVE_PSO_ASYNC=1, THREADS=2, WAIT_US=200000, FRAME_US=300000.
void TestEnabled() {
  g_prefix = "[enabled] ";
  gn::pso_stats::g_enabled = true;
  auto& totals = gn::pso_stats::g_totals;
  int before = g_failures;
  const auto threads = ProcessThreads();
  bench_log::Take();
  CHECK(gn::AsyncPipelineCompileEnabled());
  const auto& config = gn::AsyncPipelineConfig();
  CHECK(config.threads == 2 && config.wait_us == 200'000 && config.frame_us == 300'000);
  const auto lines = bench_log::Take();
  CHECK(lines.size() == 1 && lines[0].find("async PSO compile on") != std::string::npos);
  gn::DrainAsyncPipelineJobs();
  CHECK(gn::g_async_pipeline_runtime.load() == nullptr);  // the pool starts on the first post
  CHECK(NewThreads(threads) == 0);
  Report("settings", before);

  // A compile that outlasts the wait: the draw is skipped, later misses join
  // the same compile, and the job publishes the result.
  before = g_failures;
  std::mutex mutex;
  Map pipelines;
  gn::AsyncPipelineTable<int> table;
  std::promise<void> release;
  std::shared_future<void> gate = release.get_future().share();
  std::atomic<int> kind{-1};
  std::wstring name;
  std::unique_lock lock(mutex);
  auto start = std::chrono::steady_clock::now();
  int* const first = gn::CompilePipelineAsync(lock, pipelines, table, 1, [gate, &kind, &name] {
    kind = gn::pso_stats::t_thread_kind;
    name = ThreadName();
    gate.wait();
    return std::make_unique<int>(11);
  });
  const auto waited = MillisSince(start);
  CHECK(first == nullptr && lock.owns_lock());
  CHECK(waited >= 150 && waited < 3000);
  CHECK(table.Size() == 1 && pipelines.empty());
  const auto compile = table.Find(1);
  CHECK(compile != nullptr);
  CHECK(gn::AwaitAsyncPipeline(lock, pipelines, 1, compile) == nullptr && lock.owns_lock());
  release.set_value();
  lock.unlock();
  gn::DrainAsyncPipelineJobs();
  lock.lock();
  CHECK(table.Size() == 0 && pipelines.size() == 1 && pipelines.count(1) && *pipelines[1] == 11);
  CHECK(kind == gn::pso_stats::kAsyncThread && name.starts_with(kPoolName));
  CHECK(compile->Succeeded());
  CHECK(gn::AwaitAsyncPipeline(lock, pipelines, 1, compile) == pipelines[1].get());
  Report("slow compile skips", before);

  // A fast compile is ready within the wait: no draw is skipped.
  before = g_failures;
  int* const fast = gn::CompilePipelineAsync(lock, pipelines, table, 2, [] { return std::make_unique<int>(22); });
  CHECK(fast && *fast == 22 && table.Size() == 0);
  Report("fast compile", before);

  // A failed compile is not cached: the next miss posts it again.
  before = g_failures;
  std::atomic<int> attempts{0};
  const auto failing = [&attempts] {
    ++attempts;
    return std::unique_ptr<int>();
  };
  CHECK(gn::CompilePipelineAsync(lock, pipelines, table, 3, failing) == nullptr);
  lock.unlock();
  gn::DrainAsyncPipelineJobs();
  lock.lock();
  CHECK(!table.Find(3) && !pipelines.count(3) && attempts == 1);
  CHECK(gn::CompilePipelineAsync(lock, pipelines, table, 3, failing) == nullptr);
  lock.unlock();
  gn::DrainAsyncPipelineJobs();
  CHECK(attempts == 2 && table.Size() == 0);
  Report("failure reposts", before);

  // Drain waits for a job in flight.
  before = g_failures;
  std::atomic<bool> done{false};
  start = std::chrono::steady_clock::now();
  gn::PostAsyncPipelineJob([&done] {
    std::this_thread::sleep_for(50ms);
    done = true;
  });
  gn::DrainAsyncPipelineJobs();
  CHECK(done && MillisSince(start) >= 40);
  std::printf("%spool: %zu new threads, %zu named\n", g_prefix, NewThreads(threads), NamedThreads(kPoolName));
  CHECK(NamedThreads(kPoolName) == 2);
  Report("drain", before);

  before = g_failures;
  CHECK(totals.async_posted.Get() == 4);
  CHECK(totals.async_ready.Get() == 2 && totals.async_failed.Get() == 2);
  CHECK(totals.async_skipped_draws.Get() == 4);
  CHECK(totals.async_timeouts.Get() >= 2 && totals.async_waits.Get() >= totals.async_timeouts.Get());
  std::printf("%sstats: %llu posted, %llu ready, %llu failed, %llu skipped, %llu waits (%.1f ms), %llu timeouts\n",
              g_prefix, (unsigned long long)totals.async_posted.Get(), (unsigned long long)totals.async_ready.Get(),
              (unsigned long long)totals.async_failed.Get(), (unsigned long long)totals.async_skipped_draws.Get(),
              (unsigned long long)totals.async_waits.Get(), totals.async_wait_ns.Get() / 1e6,
              (unsigned long long)totals.async_timeouts.Get());
  Report("stats hooks", before);
}

int RunEnabledChild() {
  std::fflush(stdout);
  _putenv_s("LEGO_NATIVE_PSO_ASYNC", "1");
  _putenv_s("LEGO_NATIVE_PSO_ASYNC_THREADS", "2");
  _putenv_s("LEGO_NATIVE_PSO_ASYNC_WAIT_US", "200000");
  _putenv_s("LEGO_NATIVE_PSO_ASYNC_FRAME_US", "300000");
  char path[MAX_PATH] = {};
  GetModuleFileNameA(nullptr, path, MAX_PATH);
  const intptr_t code = _spawnl(_P_WAIT, path, "async_table_test", "--enabled", nullptr);
  ClearToggles();
  if (code < 0) {
    std::printf("FAIL could not start the --enabled run\n");
    return 1;
  }
  return int(code);
}

}  // namespace

int main(int argc, char** argv) {
  if (argc > 1 && std::strcmp(argv[1], "--enabled") == 0) {
    TestEnabled();
    std::fflush(stdout);
    return g_failures;
  }
  ClearToggles();
  TestToggleOff();
  TestSettings();
  TestTable();
  TestCompileWait();
  TestBudget();
  TestPool();
  TestOwnedDesc();
  TestLease();
  TestCompileInline();
  g_failures += RunEnabledChild();
  std::printf("%s: %d failure(s)\n", g_failures ? "FAILED" : "OK", g_failures);
  return g_failures;
}
