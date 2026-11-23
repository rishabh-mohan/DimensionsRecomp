// Item 1 (perf-notes/agent4-draw-path.md): QueryDrawScope's entry on every draw.
// Old: lock `mutex`, then none_of over every created query (unordered_map of shared_ptr<Query>).
// New (queries.cpp): an atomic count of active queries, read before locking and again under the lock.
// N = created-but-inactive queries in the map; the game's N is not known yet, so it is swept.
#include <algorithm>
#include <atomic>
#include <memory>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>

#include "bench_common.h"

namespace {

struct Samples {};
struct Query {  // queries.cpp layout (ComPtr fence as a pointer)
  bool active = false, ended = false, failed = false;
  bool summed = false;
  uint32_t sum = 0;
  std::vector<std::pair<std::shared_ptr<Samples>, double>> draws;
  void* completion = nullptr;
  uint64_t completion_value = 0;
};
std::mutex mutex;
std::unordered_map<uint32_t, std::shared_ptr<Query>> queries;
std::atomic<size_t> active_queries{0};

// Both return whether the draw would go on to build a scope (true only inside BEGIN/END).
BENCH_NOINLINE bool OldScope() {
  std::lock_guard lock(mutex);
  if (std::none_of(queries.begin(), queries.end(),
                   [](const auto& entry) { return entry.second->active; }))
    return false;
  return true;
}
BENCH_NOINLINE bool NewScope() {
  if (active_queries.load(std::memory_order_acquire) == 0) return false;
  std::lock_guard lock(mutex);
  if (active_queries.load(std::memory_order_relaxed) == 0) return false;
  return true;
}

void Populate(size_t created) {
  std::lock_guard lock(mutex);
  queries.clear();
  active_queries.store(0);
  // Guest query headers; other allocations in between so the nodes are not packed together.
  std::vector<std::unique_ptr<char[]>> noise;
  for (size_t i = 0; i < created; ++i) {
    queries[0x4A000000u + uint32_t(i) * 0x40u] = std::make_shared<Query>();
    noise.push_back(std::make_unique<char[]>(96));
  }
}

void SetActive(size_t index, bool active) {
  std::lock_guard lock(mutex);
  auto it = std::next(queries.begin(), ptrdiff_t(index));
  if (it->second->active != active) active ? ++active_queries : --active_queries;
  it->second->active = active;
}

void UnitTests() {
  for (size_t created : {0u, 1u, 16u, 256u}) {
    Populate(created);
    BENCH_CHECK(!OldScope() && !NewScope());
    if (!created) continue;
    SetActive(created - 1, true);
    BENCH_CHECK(OldScope() && NewScope());
    SetActive(created - 1, false);
    BENCH_CHECK(!OldScope() && !NewScope());
  }
  std::puts("query_scope unit tests: OK");
}

template <bool kNew>
uint64_t Draws(size_t draws) {
  uint64_t scoped = 0;
  for (size_t i = 0; i < draws; ++i) {
    scoped += (kNew ? NewScope() : OldScope()) ? 1 : 0;
    bench::ClobberMemory();
  }
  return scoped;
}

template <bool kNew>
double TwoThreads(size_t draws) {
  std::atomic<int> ready{0};
  std::atomic<bool> go{false};
  double ns[2]{};
  auto body = [&](int index) {
    ready.fetch_add(1);
    while (!go.load()) {}
    ns[index] = bench::NsPerOp(draws, [&] { bench::DoNotOptimize(Draws<kNew>(draws)); });
  };
  std::thread a(body, 0), b(body, 1);
  while (ready.load() < 2) {}
  go.store(true);
  a.join();
  b.join();
  return ns[0] > ns[1] ? ns[0] : ns[1];
}

}  // namespace

int main() {
  UnitTests();
  for (size_t created : {0u, 16u, 64u, 256u}) {
    Populate(created);
    char group[32];
    std::snprintf(group, sizeof(group), "query_scope N=%zu", created);
    const size_t draws = created >= 64 ? 200'000 : 2'000'000;
    bench::RunCases(group, {
        {"N=" + std::to_string(created) + " 1T old lock+none_of", [=] {
           return bench::NsPerOp(draws, [=] { bench::DoNotOptimize(Draws<false>(draws)); }); }},
        {"N=" + std::to_string(created) + " 1T new atomic count", [=] {
           return bench::NsPerOp(draws, [=] { bench::DoNotOptimize(Draws<true>(draws)); }); }},
        {"N=" + std::to_string(created) + " 2T old lock+none_of", [=] { return TwoThreads<false>(draws / 4); }},
        {"N=" + std::to_string(created) + " 2T new atomic count", [=] { return TwoThreads<true>(draws / 4); }},
    });
  }
  return 0;
}
