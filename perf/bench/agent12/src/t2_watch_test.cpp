// T2: section A lockless write-watch pre-check.
//  (a) PhysicalHeap::MayHaveWriteWatches(va, len) must equal the any_watched
//      result of the locked scan in TriggerCallbacks (its return value) for
//      random bit patterns, ranges and heaps (host_address_offset 0 and 0x1000,
//      partial last block).
//  (b) Store-buffering stress, 2 threads. IO side: data store, then
//      MayHaveWriteWatches (seq_cst fence + relaxed bit loads). Watcher side:
//      EnableAccessCallbacks (bit store under the global lock + seq_cst fence),
//      then it reads the data. Forbidden: IO saw no watch AND the watcher read
//      the old data. Control variants without the fences show the harness can
//      see the reordering.
//
// Usage: t2_watch_test.exe [equiv_iters=400000] [sb_iters=2000000]
#include "mock_memory.h"

#include <cinttypes>
#include <intrin.h>
#include <thread>

using namespace b12;

namespace {

struct Rng {
  uint64_t s;
  uint64_t next() { return xorshift64(s); }
  uint32_t below(uint64_t n) { return n ? uint32_t(next() % n) : 0; }
  bool chance(uint32_t pct) { return below(100) < pct; }
};

uint64_t gen_bits(Rng& r, int d) {
  switch (d) {
    case 0: return 0;
    case 1: return r.next() & r.next() & r.next() & r.next() & r.next() & r.next();
    case 2: return r.next() & r.next();
    case 3: return ~0ull;
    case 4: return 1ull << r.below(64);
    default: return r.chance(5) ? (1ull << r.below(64)) : 0;
  }
}

Layout t2_layout() {
  Layout l;
  l.heaps = {
      // P0: hao 0, size not a multiple of 64 system pages (partial last block).
      {HeapType::kGuestPhysical, 0x00100000, 0x00123000, 0x1000, false, 0x000000},
      // P1: like the 0xE0000000 heap (hao 0x1000), 4 KB pages.
      {HeapType::kGuestPhysical, 0x00300000, 0x00100000, 0x1000, true, 0x200000},
      // P2: hao 0x1000 with 64 KB guest pages.
      {HeapType::kGuestPhysical, 0x00500000, 0x00080000, 0x10000, true, 0x400000},
      // P3: stress heap, 1024 pages, hao 0x1000.
      {HeapType::kGuestPhysical, 0x01000000, 0x00400000, 0x1000, true, 0x500000},
  };
  l.virtual_commit = 0x10000;
  l.physical_commit = 0x910000;
  return l;
}

// ---------------------------------------------------------------- (a)
uint64_t equivalence(MockMemory& m, uint64_t iters, uint64_t seed, uint64_t* true_count) {
  Rng r{seed};
  uint64_t mismatches = 0;
  *true_count = 0;
  auto check = [&](PhysicalHeap* h, uint32_t va, uint32_t len) {
    bool pre = h->MayHaveWriteWatches(va, len);
    bool locked = h->TriggerCallbacks(global_critical_region::AcquireDirect(), va, len, true, true,
                                      r.chance(50));
    *true_count += locked;
    if (pre != locked) {
      if (++mismatches <= 10) {
        std::printf("MISMATCH heap 0x%08X va 0x%08X len 0x%08X: precheck %d locked %d\n",
                    h->heap_base(), va, len, int(pre), int(locked));
      }
    }
  };
  for (uint64_t it = 0; it < iters; ++it) {
    PhysicalHeap* h = m.physical_heap(r.below(3));
    int d = int(r.below(6));
    for (auto& b : h->flags()) b.notify_on_invalidation = gen_bits(r, d);
    uint32_t base = h->heap_base(), size = h->heap_size();
    uint32_t va;
    switch (r.below(6)) {
      case 0: va = base - r.below(0x3000); break;
      case 1: va = base + size - 1 - r.below(0x3000); break;
      case 2: va = base + size + r.below(0x3000); break;
      case 3: va = uint32_t(r.next()); break;
      default: va = base + r.below(size); break;
    }
    uint32_t len;
    switch (r.below(7)) {
      case 0: len = 0; break;
      case 1: len = 1 + r.below(16); break;
      case 2: len = r.below(0x3000); break;
      case 3: len = (1 + r.below(64)) * 4096 - r.below(2); break;
      case 4: len = r.below(uint64_t(size) * 2); break;
      case 5: len = UINT32_MAX - r.below(0x2000); break;
      default: len = r.below(0x40000); break;
    }
    check(h, va, len);
  }
  // Targeted sweep: one watched page next to block boundaries, ranges whose
  // ends sit just around it.
  for (int hi = 0; hi < 3; ++hi) {
    PhysicalHeap* h = m.physical_heap(hi);
    uint32_t count = h->system_page_count();
    uint32_t hao = h->host_address_offset();
    std::vector<uint32_t> bits = {0, 1, 2, 62, 63, 64, 65, 127, 128, count - 2, count - 1};
    for (uint32_t bit : bits) {
      if (bit >= count) continue;
      for (int64_t f = int64_t(bit) - 2; f <= int64_t(bit) + 2; ++f) {
        for (int64_t l = f; l <= int64_t(bit) + 3; ++l) {
          if (f < 0 || l < f) continue;
          for (auto& b : h->flags()) b.notify_on_invalidation = 0;
          h->flags()[bit >> 6].notify_on_invalidation = 1ull << (bit & 63);
          // System page p covers heap-relative [p*4096 - hao, (p+1)*4096 - hao).
          int64_t rel_first = f * 4096 - int64_t(hao);
          int64_t rel_last = l * 4096 + 4095 - int64_t(hao);
          if (rel_first < 0) rel_first = 0;
          if (rel_last < rel_first) continue;
          uint32_t va = h->heap_base() + uint32_t(rel_first);
          uint32_t len = uint32_t(rel_last - rel_first + 1);
          check(h, va, len);
          check(h, va + 1, len > 2 ? len - 2 : 1);
        }
      }
    }
  }
  return mismatches;
}

// ---------------------------------------------------------------- (b)
struct SpinBarrier {
  std::atomic<uint32_t> count{0};
  std::atomic<uint32_t> gen{0};
  void wait() {
    uint32_t g = gen.load(std::memory_order_acquire);
    if (count.fetch_add(1, std::memory_order_acq_rel) == 1) {
      count.store(0, std::memory_order_relaxed);
      gen.store(g + 1, std::memory_order_release);
    } else {
      while (gen.load(std::memory_order_acquire) == g) _mm_pause();
    }
  }
};

enum class Variant { kReal, kNoFences, kIoNoFence };
const char* variant_name(Variant v) {
  switch (v) {
    case Variant::kReal: return "REAL (MayHaveWriteWatches / EnableAccessCallbacks)";
    case Variant::kNoFences: return "CONTROL no fences";
    default: return "CONTROL IO side without its fence";
  }
}

inline void spin_delay(uint32_t n) {
  for (volatile uint32_t i = 0; i < n; i = i + 1) {
  }
}

struct SbResult {
  uint64_t iters = 0, forbidden = 0, io_saw_watch = 0, watcher_saw_new = 0;
  double seconds = 0;
};

SbResult store_buffering(MockMemory& m, Variant v, uint64_t iters, uint64_t seed) {
  PhysicalHeap* h = m.physical_heap(3);
  const uint32_t kSlots = 1024;
  std::vector<uint32_t> va(kSlots), pa(kSlots);
  std::vector<uint64_t*> data(kSlots);
  for (uint32_t i = 0; i < kSlots; ++i) {
    va[i] = h->heap_base() + i * 4096;
    pa[i] = h->GetPhysicalAddress(va[i]);
    data[i] = reinterpret_cast<uint64_t*>(m.TranslatePhysical(pa[i]));
    *data[i] = 0;
  }
  for (auto& b : h->flags()) b.notify_on_invalidation = 0;
  h->ResetGuestProtect();
  // Random small delays so the two sides meet at different relative times.
  std::vector<uint8_t> delay_io(4096), delay_w(4096);
  Rng r{seed};
  for (size_t i = 0; i < delay_io.size(); ++i) {
    delay_io[i] = uint8_t(r.below(24));
    delay_w[i] = uint8_t(r.below(24));
  }
  SpinBarrier bar;
  std::vector<uint8_t> seen(1);
  uint64_t got = 0;
  SbResult res;
  res.iters = iters;

  std::thread watcher([&] {
    for (uint64_t it = 1; it <= iters; ++it) {
      uint32_t s = uint32_t(it % kSlots);
      bar.wait();
      spin_delay(delay_w[it & 4095]);
      uint64_t g;
      if (v == Variant::kNoFences) {
        auto lock = global_critical_region::AcquireDirect();
        auto& blk = h->flags()[(s + 1) >> 6].notify_on_invalidation;  // system page s+1 (hao)
        StoreWatchBitsRelaxed(blk, blk | (1ull << ((s + 1) & 63)));
        g = std::atomic_ref<uint64_t>(*data[s]).load(std::memory_order_relaxed);
      } else {
        h->EnableAccessCallbacks(pa[s], 4096, true, false);
        g = std::atomic_ref<uint64_t>(*data[s]).load(std::memory_order_relaxed);
      }
      got = g;
      bar.wait();
      bar.wait();  // main thread checks and resets
    }
  });

  double t0 = qpc_seconds();
  for (uint64_t it = 1; it <= iters; ++it) {
    uint32_t s = uint32_t(it % kSlots);
    bar.wait();
    spin_delay(delay_io[it & 4095]);
    std::atomic_ref<uint64_t>(*data[s]).store(it, std::memory_order_relaxed);
    bool watched;
    if (v == Variant::kReal) {
      watched = h->MayHaveWriteWatches(va[s], 4096);
    } else {
      uint32_t p = s + 1;  // system page of guest page s with hao 0x1000
      watched = (LoadWatchBitsRelaxed(h->flags()[p >> 6].notify_on_invalidation) >> (p & 63)) & 1;
    }
    bar.wait();
    uint64_t g = got;
    res.io_saw_watch += watched;
    res.watcher_saw_new += (g == it);
    if (!watched && g != it) ++res.forbidden;
    // Reset the watch bit for the next use of this slot.
    uint32_t p = s + 1;
    auto& blk = h->flags()[p >> 6].notify_on_invalidation;
    StoreWatchBitsRelaxed(blk, blk & ~(1ull << (p & 63)));
    bar.wait();
  }
  res.seconds = qpc_seconds() - t0;
  watcher.join();
  return res;
}

}  // namespace

int main(int argc, char** argv) {
  uint64_t equiv_iters = argc > 1 ? std::strtoull(argv[1], nullptr, 0) : 400000;
  uint64_t sb_iters = argc > 2 ? std::strtoull(argv[2], nullptr, 0) : 2000000;
  setvbuf(stdout, nullptr, _IONBF, 0);
  MockMemory m(t2_layout());

  uint64_t true_count = 0;
  double t0 = qpc_seconds();
  uint64_t mism = equivalence(m, equiv_iters, 0xA11CE5ull, &true_count);
  std::printf("T2a equivalence: %" PRIu64 " random checks + boundary sweep, %" PRIu64
              " watched (locked scan true), mismatches %" PRIu64 " (%.2f s) -> %s\n",
              equiv_iters, true_count, mism, qpc_seconds() - t0, mism ? "FAIL" : "PASS");

  bool sb_ok = true;
  uint64_t control_forbidden = 0;
  for (Variant v : {Variant::kReal, Variant::kNoFences, Variant::kIoNoFence}) {
    uint64_t n = v == Variant::kReal ? sb_iters : sb_iters / 2;
    SbResult r = store_buffering(m, v, n, 0xB0B0 + int(v));
    std::printf("T2b %-52s iters %8" PRIu64 " forbidden %7" PRIu64 " (IO saw watch %" PRIu64
                ", watcher saw new data %" PRIu64 ") %.2f s\n",
                variant_name(v), r.iters, r.forbidden, r.io_saw_watch, r.watcher_saw_new,
                r.seconds);
    if (v == Variant::kReal && r.forbidden) sb_ok = false;
    if (v != Variant::kReal) control_forbidden += r.forbidden;
  }
  std::printf("T2b store-buffering: REAL forbidden outcomes %s; controls %s (%" PRIu64
              " forbidden outcomes without the fences)\n",
              sb_ok ? "none" : "PRESENT", control_forbidden ? "sensitive" : "saw none (harness "
                                                                              "may be insensitive)",
              control_forbidden);
  bool pass = !mism && sb_ok;
  std::printf("\nT2 RESULT: %s\n", pass ? "PASS" : "FAIL");
  return pass ? 0 : 1;
}
