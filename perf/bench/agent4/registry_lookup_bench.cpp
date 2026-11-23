// Section 1.2 / S2.9 (perf-notes/agent4-draw-path.md): the cost of one ResourceRegistry::Lookup hit.
// It uses the real header (gpu_native/resource_registry.h, Agent 5's). The proposed LookupBorrowed keeps
// the same TLS direct-mapped cache and the same bucket-version check, but returns a raw pointer, with no
// weak_ptr::lock() and no shared_ptr release (two locked RMWs per lookup).
// 2T: both threads look up the same entries, as the recorder and the preparation worker can.
#include <array>
#include <atomic>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>

#include "bench_common.h"
#include "resource_registry.h"

namespace {

using legodimensions::gpu_native::ResourceRegistry;

struct Texture {
  uint32_t guest_address = 0, width = 0;
};

ResourceRegistry<Texture> registry;
std::mutex registry_mutex;

// The current path: what FindTexture pays per registry hit (the wrapper stands in for FindTexture).
BENCH_NOINLINE std::shared_ptr<Texture> LookupShared(uint32_t address) {
  return registry.Lookup(address, registry_mutex);
}

// The proposed borrowed variant: identical validation, but the entry keeps a raw pointer.
struct BorrowedEntry {
  const void* registry = nullptr;
  uint64_t generation = 0;
  uint32_t address = 0;
  Texture* raw = nullptr;
};
BENCH_NOINLINE Texture* LookupBorrowed(uint32_t address) {
  if (!address) return nullptr;
  static thread_local std::array<BorrowedEntry, 128> entries;
  const uint32_t hash = (address ^ (address >> 12) ^ (address >> 23)) * 0x9E3779B9u;
  auto& entry = entries[hash >> 25];
  const auto version = registry.BucketVersion(address);
  if (entry.registry == &registry && entry.generation == version && entry.address == address)
    return entry.raw;
  std::lock_guard lock(registry_mutex);
  const auto found = registry.find(address);
  if (found == registry.end()) return nullptr;
  entry = {&registry, version, address, found->second.get()};
  return found->second.get();
}

// A draw's working set: colour targets, depth and sampled textures. The TLS slots must not collide.
constexpr std::array<uint32_t, 6> kHot = {0x1A000000u, 0x1A800000u, 0x1B200000u,
                                          0x1C004000u, 0x1C1C0000u, 0x1D550000u};

void Populate() {
  std::lock_guard lock(registry_mutex);
  // Other textures, so the map is game-sized and the hot nodes are not adjacent.
  for (uint32_t i = 0; i < 2048; ++i) {
    const uint32_t address = 0x40000000u + i * 0x1000u;
    registry.emplace(address, std::make_shared<Texture>(Texture{address, i}));
  }
  for (uint32_t address : kHot) registry.emplace(address, std::make_shared<Texture>(Texture{address, 64}));
}

uint32_t Slot(uint32_t address) {
  return ((address ^ (address >> 12) ^ (address >> 23)) * 0x9E3779B9u) >> 25;
}

void UnitTests() {
  for (size_t i = 0; i < kHot.size(); ++i)
    for (size_t j = i + 1; j < kHot.size(); ++j) BENCH_CHECK(Slot(kHot[i]) != Slot(kHot[j]));
  for (int pass = 0; pass < 2; ++pass)  // cold (miss) then warm (TLS hit)
    for (uint32_t address : kHot) {
      const auto shared = LookupShared(address);
      BENCH_CHECK(shared && shared->guest_address == address && LookupBorrowed(address) == shared.get());
    }
  BENCH_CHECK(!LookupShared(0x1E000000u) && !LookupBorrowed(0x1E000000u) && !LookupBorrowed(0));
  // Erase: the bucket version moves, so both miss and return null.
  const uint32_t victim = kHot[2];
  std::shared_ptr<Texture> old;
  {
    std::lock_guard lock(registry_mutex);
    const auto it = registry.find(victim);
    old = it->second;
    registry.erase(it);
  }
  BENCH_CHECK(!LookupShared(victim) && !LookupBorrowed(victim));
  // Replace at the same address: both return the new owner, never the cached old one.
  const auto fresh = std::make_shared<Texture>(Texture{victim, 128});
  {
    std::lock_guard lock(registry_mutex);
    registry.emplace(victim, fresh);
  }
  BENCH_CHECK(LookupShared(victim) == fresh && LookupBorrowed(victim) == fresh.get());
  BENCH_CHECK(LookupBorrowed(victim) != old.get());
  std::puts("registry_lookup unit tests: OK");
}

template <bool kBorrowed>
uint64_t Lookups(size_t ops) {
  uint64_t sum = 0;
  for (size_t i = 0; i < ops; ++i) {
    const uint32_t address = kHot[i % kHot.size()];
    if constexpr (kBorrowed) {
      sum += LookupBorrowed(address)->width;
    } else {
      sum += LookupShared(address)->width;  // the shared_ptr dies here, as at a caller's scope end
    }
    bench::ClobberMemory();
  }
  return sum;
}

template <bool kBorrowed>
double TwoThreads(size_t ops) {
  std::atomic<int> ready{0};
  std::atomic<bool> go{false};
  double ns[2]{};
  auto body = [&](int index) {
    Lookups<kBorrowed>(64);  // warm this thread's TLS cache
    ready.fetch_add(1);
    while (!go.load()) {}
    ns[index] = bench::NsPerOp(ops, [&] { bench::DoNotOptimize(Lookups<kBorrowed>(ops)); });
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
  Populate();
  UnitTests();
  constexpr size_t kOps = 2'000'000;
  bench::RunCases("registry_lookup", {
      {"1T Lookup hit (weak_ptr::lock + release)", [] {
         return bench::NsPerOp(kOps, [] { bench::DoNotOptimize(Lookups<false>(kOps)); }); }},
      {"1T LookupBorrowed hit (raw pointer)", [] {
         return bench::NsPerOp(kOps, [] { bench::DoNotOptimize(Lookups<true>(kOps)); }); }},
      {"2T Lookup hit, same entries", [] { return TwoThreads<false>(kOps / 4); }},
      {"2T LookupBorrowed hit, same entries", [] { return TwoThreads<true>(kOps / 4); }},
  });
  return 0;
}
