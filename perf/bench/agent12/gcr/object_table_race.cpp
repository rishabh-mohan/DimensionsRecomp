// S2 (Agent 12 / J3, checklist C7 C8 C10, hazard H4): replica of
// rex::system::ObjectTable (slot table grown by reallocation, per-slot
// handle_ref_count + object pointer, refcounted objects) raced by two threads:
//   T0 "mutator": AddHandle (forcing many resizes), RemoveHandle, unrelated
//                 work holding G (stands in for ENTER sections / other exports),
//                 periodic table reset (another reallocation event).
//   T1 "guest":   LookupObject (Retain/type check/Release) 75%, RemoveHandle 25%.
// Schemes:
//   G-fixed       : RemoveHandle takes G before indexing the table.
//   G-buggy       : today's RemoveHandle: LookupTable() (takes+drops G) at
//                   object_table.cpp:186, G re-taken at :191.
//   G-buggy-wide  : same, with a ~2000-pause gap to widen the window.
//   G+T           : Agent 11 item 7: writers G then T exclusive, lookups T shared
//                   only; remover clears the slot under exclusive T, Release after.
//   G+T-rel-first : WRONG order: remover releases (under G only) before clearing
//                   the slot under T; lookups under shared T can retain a dead object.
// Detection: freed objects are poisoned and quarantined (never returned to the
// heap during a run); retired table blocks are filled with 0xDD and checked
// before being freed, so a write through a stale entry pointer is counted.
// Every resize moves the block (worst case of realloc).
// Standalone, no SDK. 2 busy threads, ~3 s per scheme.
#define NOMINMAX
#include <windows.h>
#include <immintrin.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <mutex>
#include <shared_mutex>
#include <thread>
#include <vector>

constexpr uint32_t kLive = 0x4C495645u;
constexpr uint32_t kDead = 0xDEADDEADu;

struct Stats {
  std::atomic<uint64_t> lookups{0}, hits{0}, adds{0}, removes{0}, resizes{0}, resets{0};
  std::atomic<uint64_t> retain_after_free{0}, dead_magic{0}, refcount_underflow{0}, double_free{0};
  std::atomic<uint64_t> stale_entry_reads{0}, stale_table_writes{0}, stale_handle_type{0};
  void Clear() {
    for (auto* a : {&lookups, &hits, &adds, &removes, &resizes, &resets, &retain_after_free,
                    &dead_magic, &refcount_underflow, &double_free, &stale_entry_reads,
                    &stale_table_writes, &stale_handle_type}) {
      a->store(0);
    }
  }
};
static Stats g;

struct Obj {
  std::atomic<uint32_t> magic{kLive};
  std::atomic<int> refs{1};
  int type = 0;
};

class Pool {
 public:
  Obj* Alloc(int type) {
    Obj* o = nullptr;
    {
      std::lock_guard<std::mutex> l(m_);
      if (q_.size() > kQuarantine) {
        o = q_.front();
        q_.pop_front();
      }
    }
    if (!o) o = new Obj();
    o->type = type;
    o->refs.store(1);
    o->magic.store(kLive);
    return o;
  }
  void Free(Obj* o) {
    std::lock_guard<std::mutex> l(m_);
    q_.push_back(o);
  }

 private:
  static constexpr size_t kQuarantine = size_t(1) << 15;
  std::mutex m_;
  std::deque<Obj*> q_;
};
static Pool g_pool;

static void Retain(Obj* o) {
  const int old = o->refs.fetch_add(1);
  if (old <= 0) g.retain_after_free++;
  if (o->magic.load() != kLive) g.dead_magic++;
}
static void Release(Obj* o) {
  const int old = o->refs.fetch_sub(1);
  if (old == 1) {
    uint32_t expected = kLive;
    if (o->magic.compare_exchange_strong(expected, kDead)) {
      g_pool.Free(o);
    } else {
      g.double_free++;
    }
  } else if (old <= 0) {
    g.refcount_underflow++;
  }
}

struct Entry {
  int32_t handle_ref_count;
  int32_t pad;
  Obj* object;
};
static_assert(sizeof(Entry) == 16, "entry layout");

enum Scheme { kGFixed, kGBuggy, kGBuggyWide, kGT, kGTReleaseFirst, kSchemeCount };
static const char* kSchemeNames[kSchemeCount] = {"G-fixed", "G-buggy (today)", "G-buggy-wide",
                                                 "G+T (A11 order)", "G+T-rel-first (wrong)"};
static Scheme g_scheme = kGFixed;
static bool UsesT() { return g_scheme == kGT || g_scheme == kGTReleaseFirst; }

static std::recursive_mutex G;  // the global critical region
static std::shared_mutex T;     // Agent 11's table lock
static Entry* table_ = nullptr;
static uint32_t capacity_ = 0;
static uint32_t last_free_ = 1;
static uint32_t live_ = 0;
static std::atomic<uint32_t> capacity_mirror_{0};

struct OldBlock {
  Entry* p;
  uint32_t cap;
};
static std::deque<OldBlock> old_blocks_;  // under G
constexpr size_t kOldBlocks = 512;

static void CheckAndFree(const OldBlock& b) {
  const uint8_t* bytes = reinterpret_cast<const uint8_t*>(b.p);
  const size_t n = size_t(b.cap) * sizeof(Entry);
  for (size_t i = 0; i < n; ++i) {
    if (bytes[i] != 0xDD) {
      g.stale_table_writes++;
      break;
    }
  }
  free(b.p);
}

static void RetireBlockLocked(Entry* p, uint32_t cap) {
  if (!p) return;
  memset(p, 0xDD, size_t(cap) * sizeof(Entry));
  old_blocks_.push_back({p, cap});
  if (old_blocks_.size() > kOldBlocks) {
    CheckAndFree(old_blocks_.front());
    old_blocks_.pop_front();
  }
}

static void ResizeLocked(uint32_t new_cap) {
  Entry* n = static_cast<Entry*>(malloc(size_t(new_cap) * sizeof(Entry)));
  memset(n, 0, size_t(new_cap) * sizeof(Entry));
  if (table_) memcpy(n, table_, size_t(std::min(capacity_, new_cap)) * sizeof(Entry));
  RetireBlockLocked(table_, capacity_);
  table_ = n;
  capacity_ = new_cap;
  capacity_mirror_.store(new_cap, std::memory_order_relaxed);
  g.resizes++;
}

// G, then T exclusive when the scheme uses T (TableWriteLock after G).
struct WriteLock {
  std::unique_lock<std::recursive_mutex> gl;
  bool t = false;
  WriteLock() : gl(G) {
    if (UsesT()) {
      T.lock();
      t = true;
    }
  }
  ~WriteLock() {
    if (t) T.unlock();
  }
};

static uint32_t AddHandle(Obj* o) {
  WriteLock l;
  uint32_t slot = 0;
  for (uint32_t i = 0; i < capacity_; ++i) {
    const uint32_t s = (last_free_ + i) % capacity_;
    if (s != 0 && !table_[s].object) {
      slot = s;
      break;
    }
  }
  if (!slot) {
    const uint32_t old = capacity_;
    ResizeLocked(capacity_ ? capacity_ + 32 : 32);
    slot = old ? old : 1;
  }
  table_[slot].object = o;
  table_[slot].handle_ref_count = 1;
  last_free_ = slot + 1;
  live_++;
  g.adds++;
  return slot;
}

static Entry* LookupTable(uint32_t h) {  // object_table.cpp:245-260
  std::lock_guard<std::recursive_mutex> l(G);
  if (h == 0 || h >= capacity_) return nullptr;
  return &table_[h];
}

static void RemoveHandle(uint32_t h) {
  if (g_scheme == kGBuggy || g_scheme == kGBuggyWide) {
    Entry* e = LookupTable(h);  // object_table.cpp:186, before the lock
    if (!e) return;
    if (g_scheme == kGBuggyWide) {
      for (int i = 0; i < 2000; ++i) _mm_pause();
    }
    std::lock_guard<std::recursive_mutex> l(G);  // object_table.cpp:191
    Obj* o = e->object;
    if (reinterpret_cast<uintptr_t>(o) == 0xDDDDDDDDDDDDDDDDull ||
        uint32_t(e->handle_ref_count) == 0xDDDDDDDDu) {
      // The entry pointer is into a retired block. The real code would now
      // dereference garbage; model the write into freed memory and the lost remove.
      g.stale_entry_reads++;
      e->object = nullptr;
      e->handle_ref_count = 0;
      return;
    }
    if (o) {
      e->object = nullptr;
      e->handle_ref_count = 0;
      if (h < last_free_) last_free_ = h;
      live_--;
      g.removes++;
      Release(o);
    }
    return;
  }
  if (g_scheme == kGTReleaseFirst) {
    std::lock_guard<std::recursive_mutex> l(G);
    if (h == 0 || h >= capacity_) return;
    Obj* o = table_[h].object;
    if (!o) return;
    Release(o);  // too early: shared-T lookups can still reach o
    for (int i = 0; i < 200; ++i) _mm_pause();
    std::lock_guard<std::shared_mutex> t(T);
    table_[h].object = nullptr;
    table_[h].handle_ref_count = 0;
    if (h < last_free_) last_free_ = h;
    live_--;
    g.removes++;
    return;
  }
  Obj* o = nullptr;
  {
    WriteLock l;
    if (h == 0 || h >= capacity_) return;
    o = table_[h].object;
    if (!o) return;
    table_[h].object = nullptr;
    table_[h].handle_ref_count = 0;
    if (h < last_free_) last_free_ = h;
    live_--;
    g.removes++;
  }
  Release(o);  // after the slot is unreachable (C10)
}

static Obj* LookupObject(uint32_t h) {
  g.lookups.fetch_add(1, std::memory_order_relaxed);
  if (UsesT()) {
    std::shared_lock<std::shared_mutex> t(T);
    if (h == 0 || h >= capacity_) return nullptr;
    Obj* o = table_[h].object;
    if (o) Retain(o);
    return o;
  }
  std::lock_guard<std::recursive_mutex> l(G);
  if (h == 0 || h >= capacity_) return nullptr;
  Obj* o = table_[h].object;
  if (o) Retain(o);
  return o;
}

static void ResetTable() {
  std::vector<Obj*> objs;
  {
    WriteLock l;
    for (uint32_t i = 1; i < capacity_; ++i) {
      if (table_[i].object) objs.push_back(table_[i].object);
    }
    RetireBlockLocked(table_, capacity_);
    table_ = nullptr;
    capacity_ = 0;
    last_free_ = 1;
    live_ = 0;
    ResizeLocked(32);
    g.resets++;
  }
  for (Obj* o : objs) Release(o);
}

constexpr int kRing = 1024;
static std::atomic<uint32_t> g_ring[kRing];  // (type << 24) | handle

static void Mutator(std::atomic<bool>* stop) {
  uint32_t x = 12345;
  uint32_t it = 0;
  while (!stop->load(std::memory_order_relaxed)) {
    x = x * 1664525u + 1013904223u;
    const int n = 1 + int(x >> 29);  // 1..8
    for (int i = 0; i < n; ++i) {
      const int type = 1 + int((x >> (i + 3)) & 1);
      Obj* o = g_pool.Alloc(type);
      const uint32_t h = AddHandle(o);
      g_ring[(it * 8 + i) % kRing].store((uint32_t(type) << 24) | h, std::memory_order_release);
    }
    for (int i = 0; i + 1 < n; ++i) {
      x = x * 1664525u + 1013904223u;
      const uint32_t v = g_ring[(x >> 10) % kRing].load(std::memory_order_acquire);
      if (v) RemoveHandle(v & 0xFFFFFF);
    }
    {
      // Unrelated work under G (ENTER sections, other kernel exports).
      std::lock_guard<std::recursive_mutex> l(G);
      for (int i = 0; i < 100; ++i) _mm_pause();
    }
    if (capacity_mirror_.load(std::memory_order_relaxed) > 2048) ResetTable();
    ++it;
  }
}

static void Guest(std::atomic<bool>* stop) {
  uint32_t x = 999;
  while (!stop->load(std::memory_order_relaxed)) {
    x = x * 1664525u + 1013904223u;
    const uint32_t v = g_ring[(x >> 12) % kRing].load(std::memory_order_acquire);
    if (!v) continue;
    const uint32_t h = v & 0xFFFFFF;
    const int type = int(v >> 24);
    if ((x >> 28) < 12) {
      Obj* o = LookupObject(h);
      if (o) {
        g.hits.fetch_add(1, std::memory_order_relaxed);
        if (o->type != type) g.stale_handle_type.fetch_add(1, std::memory_order_relaxed);
        Release(o);
      }
    } else {
      RemoveHandle(h);
    }
  }
}

int main(int argc, char** argv) {
  setvbuf(stdout, nullptr, _IONBF, 0);
  const int ms = argc > 1 ? atoi(argv[1]) : 3000;
  printf("S2 object_table_race: %d ms per scheme, 2 threads (mutator + guest)\n", ms);
  printf("%-22s %10s %10s %9s %8s | %8s %8s %8s %8s %8s %8s | %10s\n", "scheme", "lookups/s",
         "adds/s", "resizes", "resets", "stEntRd", "stTblWr", "retFree", "deadMag", "dblFree",
         "underflw", "staleType");
  int failures = 0;
  for (int s = 0; s < kSchemeCount; ++s) {
    g.Clear();
    g_scheme = Scheme(s);
    for (auto& r : g_ring) r.store(0);
    {
      WriteLock l;
      ResizeLocked(32);
    }
    std::atomic<bool> stop{false};
    const auto t0 = std::chrono::steady_clock::now();
    std::thread a(Mutator, &stop), b(Guest, &stop);
    Sleep(ms);
    stop = true;
    a.join();
    b.join();
    const double secs = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    ResetTable();
    {
      std::lock_guard<std::recursive_mutex> l(G);
      RetireBlockLocked(table_, capacity_);
      table_ = nullptr;
      capacity_ = 0;
      while (!old_blocks_.empty()) {
        CheckAndFree(old_blocks_.front());
        old_blocks_.pop_front();
      }
    }
    const uint64_t bad = g.stale_entry_reads + g.stale_table_writes + g.retain_after_free +
                         g.dead_magic + g.double_free + g.refcount_underflow;
    printf("%-22s %10.0f %10.0f %9llu %8llu | %8llu %8llu %8llu %8llu %8llu %8llu | %10llu  %s\n",
           kSchemeNames[s], g.lookups / secs, g.adds / secs, (unsigned long long)g.resizes.load(),
           (unsigned long long)g.resets.load(), (unsigned long long)g.stale_entry_reads.load(),
           (unsigned long long)g.stale_table_writes.load(),
           (unsigned long long)g.retain_after_free.load(), (unsigned long long)g.dead_magic.load(),
           (unsigned long long)g.double_free.load(), (unsigned long long)g.refcount_underflow.load(),
           (unsigned long long)g.stale_handle_type.load(), bad ? "ANOMALIES" : "clean");
    if (bad && (s == kGFixed || s == kGT)) failures++;
  }
  printf("legend: stEntRd = RemoveHandle used an entry pointer into a retired table block;\n"
         "        stTblWr = retired block modified after retirement (write through stale pointer);\n"
         "        retFree/deadMag = Retain on a freed object; dblFree/underflw = refcount corruption;\n"
         "        staleType = a stale handle resolved to a different-type object (slot reuse, all schemes).\n");
  printf("result: %s (correct schemes must be clean)\n", failures ? "FAIL" : "PASS");
  fflush(stdout);
  std::_Exit(failures ? 1 : 0);
}
