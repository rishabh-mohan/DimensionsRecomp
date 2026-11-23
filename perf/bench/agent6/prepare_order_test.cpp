// Agent 6, task #5 item 3: tests for gpu_native/pipeline_parallel.h
// (RunOrdered), the ordered parallel map behind LEGO_NATIVE_PSO_PREPARE_THREADS.
//
//   powershell -NoProfile -ExecutionPolicy Bypass -File bench/agent6/run_benches.ps1 -Only prepare_order_test
//
// Work items sleep instead of spinning, so the test needs little CPU. The last
// test runs a model of PipelineLibrary::Prepare's commit step (the same
// switch, resident cap and pre-filter as pipeline_library.cpp) with 1, 2, 4 and
// 8 threads and requires identical results.

#include "gpu_native/pipeline_parallel.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <unordered_set>
#include <vector>

namespace gn = legodimensions::gpu_native;

namespace {

int g_failures = 0;
#define CHECK(...)                                                        \
  do {                                                                    \
    if (!(__VA_ARGS__)) {                                                 \
      std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #__VA_ARGS__);  \
      ++g_failures;                                                       \
    }                                                                     \
  } while (0)

void Report(const char* name, int failures_before) {
  std::printf("%-26s %s\n", name, g_failures == failures_before ? "PASS" : "FAIL");
}

// Up to 0.4 ms, varied so results finish out of order.
void Nap(std::size_t index) { std::this_thread::sleep_for(std::chrono::microseconds((index * 37) % 400)); }

void UpdateMax(std::atomic<std::size_t>& maximum, std::size_t value) {
  std::size_t current = maximum.load();
  while (value > current && !maximum.compare_exchange_weak(current, value)) {
  }
}

void TestOrder() {
  const int before = g_failures;
  constexpr std::size_t kCount = 200;
  constexpr unsigned kThreads = 4;
  constexpr std::size_t kWindow = 8;
  std::vector<std::atomic<int>> calls(kCount);
  std::atomic<std::size_t> in_flight{0}, max_in_flight{0}, committed{0}, max_ahead{0};
  std::size_t expected = 0;
  bool in_order = true;
  const bool complete = gn::RunOrdered<std::size_t>(
      kCount, kThreads, kWindow,
      [&](std::size_t i) {
        calls[i].fetch_add(1);
        UpdateMax(max_in_flight, in_flight.fetch_add(1) + 1);
        UpdateMax(max_ahead, i - committed.load());
        Nap(i);
        in_flight.fetch_sub(1);
        return i * 3;
      },
      [&](std::size_t i, std::size_t&& value) {
        in_order &= i == expected && value == i * 3;
        ++expected;
        committed.store(i + 1);
        return true;
      });
  CHECK(complete);
  CHECK(in_order);
  CHECK(expected == kCount);
  CHECK(std::all_of(calls.begin(), calls.end(), [](const std::atomic<int>& count) { return count.load() == 1; }));
  CHECK(max_in_flight.load() <= kThreads);
  CHECK(max_in_flight.load() >= 2);  // it did run in parallel
  CHECK(max_ahead.load() < kWindow);
  Report("order, once each, bounds", before);
}

void TestStop() {
  const int before = g_failures;
  constexpr std::size_t kCount = 100, kStopAt = 37, kWindow = 16;
  std::atomic<std::size_t> max_started{0};
  std::size_t commits = 0;
  const bool complete = gn::RunOrdered<int>(
      kCount, 4, kWindow,
      [&](std::size_t i) {
        UpdateMax(max_started, i);
        Nap(i);
        return int(i);
      },
      [&](std::size_t i, int&&) {
        ++commits;
        return i != kStopAt;
      });
  CHECK(!complete);
  CHECK(commits == kStopAt + 1);
  CHECK(max_started.load() < kStopAt + kWindow);
  Report("commit stops the run", before);
}

void TestExceptions() {
  const int before = g_failures;
  std::size_t commits = 0;
  bool caught = false;
  try {
    gn::RunOrdered<int>(
        100, 4, 16,
        [&](std::size_t i) {
          Nap(i);
          if (i == 20) throw std::runtime_error("work 20");
          return int(i);
        },
        [&](std::size_t, int&&) {
          ++commits;
          return true;
        });
  } catch (const std::runtime_error& error) {
    caught = std::string(error.what()) == "work 20";
  }
  CHECK(caught);
  CHECK(commits <= 20);
  caught = false;
  try {
    gn::RunOrdered<int>(
        100, 4, 16,
        [&](std::size_t i) {
          Nap(i);
          return int(i);
        },
        [&](std::size_t i, int&&) {
          if (i == 10) throw std::logic_error("commit 10");
          return true;
        });
  } catch (const std::logic_error&) {
    caught = true;
  }
  CHECK(caught);  // and the workers were joined: no std::terminate
  Report("exceptions", before);
}

void TestSerial() {
  const int before = g_failures;
  const auto main_thread = std::this_thread::get_id();
  std::vector<std::string> events;
  bool same_thread = true;
  const auto work = [&](std::size_t i) {
    same_thread &= std::this_thread::get_id() == main_thread;
    events.push_back("w" + std::to_string(i));
    return int(i);
  };
  const auto commit = [&](std::size_t i, int&&) {
    events.push_back("c" + std::to_string(i));
    return true;
  };
  CHECK(gn::RunOrdered<int>(5, 1, 64, work, commit));
  CHECK(events == std::vector<std::string>{"w0", "c0", "w1", "c1", "w2", "c2", "w3", "c3", "w4", "c4"});
  events.clear();
  CHECK(gn::RunOrdered<int>(1, 4, 64, work, commit));  // one item: serial even with threads
  CHECK(events == std::vector<std::string>{"w0", "c0"});
  CHECK(same_thread);
  int calls = 0;
  CHECK(gn::RunOrdered<int>(
      0, 4, 64,
      [&](std::size_t) {
        ++calls;
        return 0;
      },
      [&](std::size_t, int&&) {
        ++calls;
        return true;
      }));
  CHECK(calls == 0);
  int commits = 0;
  CHECK(!gn::RunOrdered<int>(
      10, 1, 64, [](std::size_t i) { return int(i); },
      [&](std::size_t i, int&&) {
        ++commits;
        return i != 3;
      }));
  CHECK(commits == 4);
  Report("serial and edge counts", before);
}

void TestMoveOnly() {
  const int before = g_failures;
  bool values = true;
  std::size_t commits = 0;
  CHECK(gn::RunOrdered<std::unique_ptr<std::size_t>>(
      50, 3, 8,
      [](std::size_t i) {
        Nap(i);
        return std::make_unique<std::size_t>(i * i);
      },
      [&](std::size_t i, std::unique_ptr<std::size_t>&& value) {
        values &= value && *value == i * i;
        ++commits;
        return true;
      }));
  CHECK(values && commits == 50);
  Report("move-only results", before);
}

// --- model of PipelineLibrary::Prepare --------------------------------------

enum class Result { kLoaded, kCompiled, kFailed, kRemoved };

struct Item {
  Result result = Result::kFailed;
  std::string pipeline;
};

struct Outcome {
  bool complete = true;
  uint64_t loaded = 0, compiled = 0, failed = 0;
  std::vector<std::string> stored, resident, prepared;
  bool operator==(const Outcome&) const = default;
};

uint64_t Hash(const std::string& text) {
  uint64_t hash = 1469598103934665603ull;
  for (const char c : text) {
    hash ^= uint8_t(c);
    hash *= 1099511628211ull;
  }
  return hash;
}

// What the driver would do with a recipe: a pure function of the name.
Item Classify(const std::string& name, const std::string& removed) {
  if (name == removed) return {Result::kRemoved, {}};
  switch (Hash(name) % 10) {
    case 0:
    case 1: return {Result::kCompiled, "pso:" + name};
    case 2: return {Result::kFailed, {}};
    default: return {Result::kLoaded, "pso:" + name};
  }
}

Outcome RunModel(unsigned threads, const std::string& removed) {
  // The local recordings, then a seed that repeats 40 local names (some of
  // them failed locally, so the seed retries them). Names are unique within a
  // source, as PipelineRecipes guarantees.
  std::vector<std::vector<std::string>> sources(2);
  for (int i = 0; i < 180; ++i) sources[0].push_back("a" + std::to_string(i));
  for (int i = 0; i < 120; ++i) sources[1].push_back("b" + std::to_string(i));
  for (int i = 0; i < 40; ++i) sources[1].insert(sources[1].begin() + i * 3, "a" + std::to_string(i * 4));
  Outcome outcome;
  std::unordered_set<std::string> prepared;
  constexpr std::size_t kMaxResident = 64;
  // pipeline_library.cpp's commit lambda, with the D3D12 calls replaced.
  const auto commit = [&](const std::string& name, Item&& item) {
    switch (item.result) {
      case Result::kLoaded:
        ++outcome.loaded;
        break;
      case Result::kCompiled:
        ++outcome.compiled;
        outcome.stored.push_back(name);
        break;
      case Result::kFailed:
        ++outcome.failed;
        return true;
      case Result::kRemoved:
        ++outcome.failed;
        return false;
    }
    prepared.insert(name);
    outcome.prepared.push_back(name);
    if (outcome.resident.size() < kMaxResident) outcome.resident.push_back(std::move(item.pipeline));
    return true;
  };
  for (const auto& source : sources) {
    bool complete = true;
    if (threads <= 1) {
      // Prepare's serial loop.
      for (std::size_t i = 0; i < source.size() && complete; ++i) {
        if (prepared.contains(source[i])) continue;
        complete = commit(source[i], Classify(source[i], removed));
      }
    } else {
      // PrepareParallel: the same pre-filter, then RunOrdered.
      std::vector<std::string> names;
      std::unordered_set<std::string> seen;
      for (const auto& name : source)
        if (!prepared.contains(name) && seen.insert(name).second) names.push_back(name);
      complete = gn::RunOrdered<Item>(
          names.size(), threads, 64,
          [&](std::size_t i) {
            Nap(i);
            return Classify(names[i], removed);
          },
          [&](std::size_t i, Item&& item) { return commit(names[i], std::move(item)); });
    }
    if (!complete) {
      outcome.complete = false;
      break;
    }
  }
  return outcome;
}

void TestPrepareModel() {
  const int before = g_failures;
  for (const std::string removed : {"", "a120", "b50"}) {
    const Outcome serial = RunModel(1, removed);
    CHECK(serial.complete == removed.empty());
    CHECK(serial.resident.size() == 64);
    CHECK(serial.compiled > 0 && serial.failed > 0);
    for (const unsigned threads : {2u, 4u, 8u}) {
      const Outcome parallel = RunModel(threads, removed);
      if (!(parallel == serial)) {
        std::printf("FAIL: prepare model differs with %u threads (removed '%s'): loaded %llu/%llu compiled %llu/%llu "
                    "failed %llu/%llu\n",
                    threads, removed.c_str(), (unsigned long long)parallel.loaded,
                    (unsigned long long)serial.loaded, (unsigned long long)parallel.compiled,
                    (unsigned long long)serial.compiled, (unsigned long long)parallel.failed,
                    (unsigned long long)serial.failed);
        ++g_failures;
      }
    }
    std::printf("  model removed='%s': loaded %llu compiled %llu failed %llu complete %d\n", removed.c_str(),
                (unsigned long long)serial.loaded, (unsigned long long)serial.compiled,
                (unsigned long long)serial.failed, int(serial.complete));
  }
  Report("prepare model 1=2=4=8", before);
}

}  // namespace

int main() {
  TestOrder();
  TestStop();
  TestExceptions();
  TestSerial();
  TestMoveOnly();
  TestPrepareModel();
  std::printf("prepare_order_test: %s (%d failures)\n", g_failures ? "FAIL" : "PASS", g_failures);
  return g_failures ? 1 : 0;
}
