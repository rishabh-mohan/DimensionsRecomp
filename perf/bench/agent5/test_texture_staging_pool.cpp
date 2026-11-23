// Unit test for gpu_native/upload_buffer_pool.h after the batch-2 budget change
// (constructor budget, default 192 MB) and for the shared_mutex composition that
// textures.cpp uses for LEGO_NATIVE_TEXTURE_STAGING_POOL (Acquire under a shared
// lock, Reset under an exclusive lock).
// Build/run: powershell -File bench/agent5/build.ps1 -Run -Only test_staging_pool_v3
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <random>
#include <shared_mutex>
#include <thread>
#include <vector>

#include "gpu_native/upload_buffer_pool.h"

using legodimensions::gpu_native::UploadBufferPool;

namespace {
int g_failures = 0;
#define CHECK(cond)                                                            \
  do {                                                                         \
    if (!(cond)) {                                                             \
      ++g_failures;                                                            \
      std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);              \
    }                                                                          \
  } while (0)

std::atomic<int64_t> g_live{0}, g_destroyed{0}, g_created{0};

struct Buffer {
  explicit Buffer(uint64_t size) : capacity(size) { ++g_live; ++g_created; }
  ~Buffer() { --g_live; ++g_destroyed; }
  uint64_t capacity;
  std::atomic<int> holder{0};  // stress: the thread that currently owns it
};

auto Create() {
  return [](uint64_t capacity) { return std::make_unique<Buffer>(capacity); };
}

constexpr uint64_t MB = 1024 * 1024;

void TestDefaultBudgetUnchanged() {
  CHECK(UploadBufferPool<Buffer>::kDefaultBudget == 192 * MB);
  const auto destroyed = g_destroyed.load();
  {
    UploadBufferPool<Buffer> pool;  // buffers.cpp's g_upload_pool / g_resident_pool form
    std::vector<std::shared_ptr<Buffer>> held;
    for (int i = 0; i < 4; ++i) held.push_back(pool.Acquire(uint32_t(64 * MB), 1, Create()));
    held.clear();
    const auto stats = pool.Stats();
    CHECK(stats.count == 3);
    CHECK(stats.bytes == 192 * MB);
    CHECK(g_destroyed.load() - destroyed == 1);
    // A pooled 64 MB buffer is handed out again.
    auto again = pool.Acquire(uint32_t(64 * MB), 1, Create());
    CHECK(pool.Stats().hits == 1);
    CHECK(pool.Stats().count == 2);
  }
  CHECK(g_live.load() == 0);
}

void TestCustomBudget() {
  const auto destroyed = g_destroyed.load();
  UploadBufferPool<Buffer> pool(64 * MB);  // the texture staging pool's budget
  std::vector<std::shared_ptr<Buffer>> held;
  for (int i = 0; i < 3; ++i) held.push_back(pool.Acquire(uint32_t(32 * MB), 0, Create()));
  held.clear();
  CHECK(pool.Stats().count == 2);
  CHECK(pool.Stats().bytes == 64 * MB);
  CHECK(g_destroyed.load() - destroyed == 1);
  // Over-budget sizes are never pooled: 65 MB rounds to a 128 MB class.
  {
    auto big = pool.Acquire(uint32_t(65 * MB), 0, Create());
    CHECK(big && big->capacity == 128 * MB);
  }
  CHECK(g_destroyed.load() - destroyed == 2);
  CHECK(pool.Stats().count == 2);
  // Small buffers are charged 64 KB each against the budget: the budget is full,
  // so a released 256-byte buffer is destroyed too.
  { auto small = pool.Acquire(100, 0, Create()); }
  CHECK(g_destroyed.load() - destroyed == 3);
  pool.Reset();
  CHECK(g_live.load() == 0);
}

void TestNoReuseWhileHeld() {
  UploadBufferPool<Buffer> pool(64 * MB);
  auto a = pool.Acquire(1000, 0, Create());
  auto a_copy = a;  // e.g. the publication LRU plus a RetireResource fence slot
  const Buffer* a_raw = a.get();
  a.reset();
  auto b = pool.Acquire(1000, 0, Create());
  CHECK(b.get() != a_raw);
  CHECK(pool.Stats().misses == 2 && pool.Stats().hits == 0);
  a_copy.reset();  // last owner: now it may be reused
  auto c = pool.Acquire(1000, 0, Create());
  CHECK(c.get() == a_raw);
  CHECK(pool.Stats().hits == 1);
  b.reset(); c.reset();
  pool.Reset();
  CHECK(g_live.load() == 0);
}

void TestClassesAndKinds() {
  UploadBufferPool<Buffer> pool(64 * MB);
  uint64_t seen = 0;
  auto create = [&](uint64_t capacity) { seen = capacity; return std::make_unique<Buffer>(capacity); };
  { auto x = pool.Acquire(1, 0, create); CHECK(seen == 256); }
  { auto x = pool.Acquire(1000, 0, create); CHECK(seen == 1024); }
  const auto created = g_created.load();
  { auto x = pool.Acquire(1024, 0, create); CHECK(x->capacity == 1024); }  // hit (1000 -> 1024 class)
  CHECK(g_created.load() == created);
  { auto x = pool.Acquire(1025, 0, create); CHECK(seen == 2048 && x->capacity == 2048); }
  CHECK(g_created.load() == created + 1);
  { auto x = pool.Acquire(1024, 1, create); }  // another kind never shares a class
  CHECK(g_created.load() == created + 2);
  CHECK(!pool.Acquire(0, 0, create));  // zero length: no buffer (textures.cpp never routes 0 here)
  // Per-class cap (256) is unchanged.
  std::vector<std::shared_ptr<Buffer>> held;
  for (int i = 0; i < 300; ++i) held.push_back(pool.Acquire(256, 2, create));
  held.clear();
  CHECK(pool.Stats().count == 256 + 4);  // + the four single buffers pooled above
  pool.Reset();
  CHECK(g_live.load() == 0);
}

void TestResetSemantics() {
  UploadBufferPool<Buffer> pool(64 * MB);
  auto held = pool.Acquire(4096, 0, Create());
  { auto idle = pool.Acquire(8192, 0, Create()); }
  CHECK(pool.Stats().count == 1);
  const auto destroyed = g_destroyed.load();
  pool.Reset();
  CHECK(g_destroyed.load() - destroyed == 1);  // idle buffers are destroyed by Reset
  CHECK(pool.Stats().count == 0 && pool.Stats().bytes == 0 && pool.Stats().hits == 0);
  held.reset();                                // released after Reset: destroyed, not pooled
  CHECK(g_destroyed.load() - destroyed == 2);
  CHECK(pool.Stats().count == 0);
  // The budget survives Reset: 2 x 32 MB fit, a third does not.
  std::vector<std::shared_ptr<Buffer>> many;
  for (int i = 0; i < 3; ++i) many.push_back(pool.Acquire(uint32_t(32 * MB), 0, Create()));
  many.clear();
  CHECK(pool.Stats().count == 2 && pool.Stats().bytes == 64 * MB);
  pool.Reset();
  CHECK(g_live.load() == 0);
  // A buffer that outlives the pool object is destroyed at its release.
  std::shared_ptr<Buffer> orphan;
  {
    UploadBufferPool<Buffer> scoped(64 * MB);
    orphan = scoped.Acquire(4096, 0, Create());
  }
  orphan.reset();
  CHECK(g_live.load() == 0);
}

// textures.cpp composition: Acquire under a shared lock from 2 threads, Reset
// under the exclusive lock from a third. No buffer may be handed out to two
// holders at once, capacities must cover the request, and nothing may leak.
void TestStress() {
  UploadBufferPool<Buffer> pool(64 * MB);
  std::shared_mutex mutex;
  std::atomic<bool> stop{false};
  std::atomic<int64_t> acquired{0}, double_handout{0}, short_capacity{0};
  auto worker = [&](int id) {
    std::mt19937 random(1234u + unsigned(id));
    std::vector<std::shared_ptr<Buffer>> ring(8);
    for (int i = 0; i < 150000; ++i) {
      const uint32_t bytes = 1 + random() % (2u * 1024 * 1024);
      std::shared_ptr<Buffer> buffer;
      {
        std::shared_lock lock(mutex);
        buffer = pool.Acquire(bytes, uint8_t(random() % 2), Create());
      }
      ++acquired;
      if (!buffer) { ++short_capacity; continue; }
      if (buffer->capacity < bytes) ++short_capacity;
      int expected = 0;
      if (!buffer->holder.compare_exchange_strong(expected, id)) ++double_handout;
      auto& slot = ring[random() % ring.size()];
      if (slot) slot->holder.store(0);  // the holder clears its tag before release
      slot = std::move(buffer);
    }
    for (auto& slot : ring) if (slot) { slot->holder.store(0); slot.reset(); }
  };
  std::thread a(worker, 1), b(worker, 2);
  std::thread resetter([&] {
    int resets = 0;
    while (!stop.load()) {
      std::this_thread::sleep_for(std::chrono::microseconds(500));
      std::unique_lock lock(mutex);
      pool.Reset();
      ++resets;
    }
    std::printf("stress: %d resets\n", resets);
  });
  a.join(); b.join();
  stop = true;
  resetter.join();
  const auto stats = pool.Stats();
  std::printf("stress: %lld acquires, final idle=%llu buffers %llu bytes\n",
      (long long)acquired.load(), (unsigned long long)stats.count, (unsigned long long)stats.bytes);
  CHECK(double_handout.load() == 0);
  CHECK(short_capacity.load() == 0);
  CHECK(stats.bytes <= 64 * MB);
  CHECK(g_live.load() == int64_t(stats.count));
  pool.Reset();
  CHECK(g_live.load() == 0);
}
}  // namespace

int main() {
  TestDefaultBudgetUnchanged();
  TestCustomBudget();
  TestNoReuseWhileHeld();
  TestClassesAndKinds();
  TestResetSemantics();
  TestStress();
  std::printf("test_texture_staging_pool: %s (%d failures, %lld buffers created)\n",
      g_failures ? "FAILED" : "passed", g_failures, (long long)g_created.load());
  return g_failures ? 1 : 0;
}
