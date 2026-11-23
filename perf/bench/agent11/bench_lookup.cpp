// bench_lookup.cpp - agent11 item 7: GetNativeObject cost and global-mutex contention.
// OLD = replica of XObject::GetNativeObject (src/system/xobject.cpp): takes
//       global_critical_region (one static std::recursive_mutex G), checks the
//       big-endian wait_list_flink signature, reads the handle from
//       wait_list_blink; ObjectTable::LookupObject(handle, false) locks G again,
//       reads table_[slot].object, Retain()s, unlocks; the caller's object_ref
//       Release()s afterwards.
// NEW = acquire-load of flink + compare, relaxed load of blink, std::shared_lock
//       on a separate std::shared_mutex T for the slot read + Retain, unlock;
//       Release afterwards. Falls back to OLD if the fast path misses.
// Modes: 1T; 2T same handle; 2T different handles; 2T where thread 2 holds G
//        exclusively ~2 us every ~20 us while thread 1 looks up.
// Usage: bench_lookup.exe [runs=5] [lookups_per_pass=300000]
#include "bench_common.h"

#include <immintrin.h>
#include <atomic>
#include <cstdlib>
#include <mutex>
#include <shared_mutex>
#include <thread>

static constexpr auto rlx = std::memory_order_relaxed;
constexpr uint32_t kXObjSignature = 0x52455800;  // make_fourcc('R','E','X',0)
constexpr uint32_t kSigBE = 0x00584552;          // the same, as the big-endian guest word reads on x86
constexpr uint32_t kHandleBase = 0xF8000000;

struct X_DISPATCH_HEADER {  // guest memory, big-endian fields
  uint8_t type, absolute, size, inserted;
  uint32_t signal_state;
  uint32_t wait_list_flink;
  uint32_t wait_list_blink;
};
struct alignas(64) GuestObj { X_DISPATCH_HEADER header; };
struct alignas(64) XObj { std::atomic<int32_t> pointer_ref_count{1}; uint32_t handle = 0; };
struct ObjectTableEntry { int handle_ref_count = 0; XObj* object = nullptr; };

static std::recursive_mutex G;  // global_critical_region::mutex()
static std::shared_mutex T;     // NEW: object-table lock
static constexpr uint32_t kCap = 16384;
static ObjectTableEntry table_[kCap];
static uint32_t table_capacity_ = kCap;
static GuestObj guest[2];
static XObj objs[2];
static uint32_t current_thread_handle = 0;
static volatile uint32_t g_sink;

static inline uint32_t be(uint32_t v) { return _byteswap_ulong(v); }
static inline uint32_t TranslateHandle(uint32_t h) {
  if (h == 0xFFFFFFFF) return 0;
  if (h == 0xFFFFFFFE) return current_thread_handle;
  return h;
}

// ObjectTable::LookupObject(handle, already_locked = false)
static XObj* LookupObject(uint32_t handle) {
  handle = TranslateHandle(handle);
  if (!handle) return nullptr;
  XObj* object = nullptr;
  G.lock();
  const uint32_t slot = (handle - kHandleBase) >> 2;
  if (slot < table_capacity_) {
    ObjectTableEntry& entry = table_[slot];
    if (entry.object) object = entry.object;
  }
  if (object) ++object->pointer_ref_count;  // Retain
  G.unlock();
  return object;
}

static XObj* GetNativeObjectOld(void* native_ptr, int32_t as_type = -1) {
  std::unique_lock<std::recursive_mutex> global_lock(G);  // AcquireDirect()
  auto header = reinterpret_cast<X_DISPATCH_HEADER*>(native_ptr);
  if (as_type == -1) as_type = header->type;
  if (be(header->wait_list_flink) == kXObjSignature) {
    const uint32_t handle = be(header->wait_list_blink);
    return LookupObject(handle);
  }
  return nullptr;  // first-use creation path not modelled
}

static XObj* GetNativeObjectNew(void* native_ptr) {
  auto header = reinterpret_cast<X_DISPATCH_HEADER*>(native_ptr);
  if (std::atomic_ref<uint32_t>(header->wait_list_flink).load(std::memory_order_acquire) == kSigBE) {
    const uint32_t handle = TranslateHandle(be(std::atomic_ref<uint32_t>(header->wait_list_blink).load(rlx)));
    if (handle) {
      std::shared_lock<std::shared_mutex> lock(T);
      const uint32_t slot = (handle - kHandleBase) >> 2;
      if (slot < table_capacity_) {
        if (XObj* object = table_[slot].object) {
          ++object->pointer_ref_count;
          return object;
        }
      }
    }
  }
  return GetNativeObjectOld(native_ptr);
}

template <int V>
static inline XObj* Get(void* p) { return V ? GetNativeObjectNew(p) : GetNativeObjectOld(p); }
static inline void Release(XObj* o) {
  if (--o->pointer_ref_count == 0) __debugbreak();
}

enum { k1T = 0, k2Same = 1, k2Diff = 2, kContend = 3 };
struct Ctl { std::atomic<int> ready{0}; std::atomic<bool> go{false}, stop{false}; };
struct T2Out { uint64_t ops = 0; double secs = 0; };
struct Pass { double ns = NAN, over1us = NAN; bench_a::Summary lat; T2Out t2; };

template <int V>
static void t2_body(int mode, Ctl& c, T2Out* out) {
  c.ready.store(1);
  while (!c.go.load(std::memory_order_acquire)) _mm_pause();
  uint64_t n = 0;
  uint32_t acc = 0;
  const int64_t t0 = qpc();
  if (mode == kContend) {
    const double tpn = bench_a::tsc_per_ns();
    const uint64_t hold = uint64_t(2000 * tpn), gap = uint64_t(18000 * tpn);
    while (!c.stop.load(rlx)) {
      G.lock();
      uint64_t s = __rdtsc();
      while (__rdtsc() - s < hold) _mm_pause();
      G.unlock();
      ++n;
      s = __rdtsc();
      while (__rdtsc() - s < gap) _mm_pause();
    }
  } else {
    void* p = &guest[mode == k2Diff ? 1 : 0].header;
    while (!c.stop.load(rlx)) {
      for (int i = 0; i < 64; ++i) {
        XObj* o = Get<V>(p);
        acc += o->handle;
        Release(o);
      }
      n += 64;
    }
  }
  out->secs = ticks_ms(qpc() - t0) / 1000.0;
  out->ops = n;
  g_sink = acc;
}

template <int V>
static Pass run_pass(int mode, int n, bool timed, uint64_t ovh, std::vector<double>& lat) {
  Pass p;
  Ctl c;
  std::thread t2;
  if (mode != k1T) {
    t2 = std::thread([&] { t2_body<V>(mode, c, &p.t2); });
    while (!c.ready.load()) _mm_pause();
  }
  c.go.store(true, std::memory_order_release);
  void* h = &guest[0].header;
  uint32_t acc = 0;
  if (!timed) {
    const int64_t t0 = qpc();
    for (int i = 0; i < n; ++i) {
      XObj* o = Get<V>(h);
      acc += o->handle;
      Release(o);
    }
    p.ns = ticks_ns(qpc() - t0) / n;
  } else {
    lat.resize(n);
    const double tpn = bench_a::tsc_per_ns();
    for (int i = 0; i < n; ++i) {
      const uint64_t a = bench_a::tsc_begin();
      XObj* o = Get<V>(h);
      acc += o->handle;
      Release(o);
      const uint64_t d = bench_a::tsc_end() - a;
      lat[i] = double(d > ovh ? d - ovh : 0) / tpn;
    }
  }
  c.stop.store(true);
  if (t2.joinable()) t2.join();
  g_sink = acc;
  if (timed) {
    p.lat = bench_a::summarize(lat);
    p.over1us = 100.0 * double(std::count_if(lat.begin(), lat.end(), [](double x) { return x > 1000.0; })) / n;
  }
  return p;
}

int main(int argc, char** argv) {
  const int runs = argc > 1 ? atoi(argv[1]) : 5;
  const int n = argc > 2 ? atoi(argv[2]) : 300000;
  bench_a::print_machine_state("start");
  const double tpn = bench_a::tsc_per_ns();
  for (int i = 0; i < 2; ++i) {  // two native objects, as StashHandle leaves them
    const uint32_t slot = i ? 9 : 5;
    objs[i].handle = kHandleBase + (slot << 2);
    table_[slot].object = &objs[i];
    table_[slot].handle_ref_count = 1;
    guest[i].header.type = 1;
    guest[i].header.wait_list_blink = be(objs[i].handle);
    guest[i].header.wait_list_flink = be(kXObjSignature);
  }
  if (GetNativeObjectOld(&guest[1].header) != &objs[1] || GetNativeObjectNew(&guest[1].header) != &objs[1]) {
    printf("ERROR: lookup replica broken\n");
    return 1;
  }
  Release(&objs[1]);
  Release(&objs[1]);
  std::vector<double> ov(20001);
  for (auto& x : ov) {
    const uint64_t a = bench_a::tsc_begin();
    x = double(bench_a::tsc_end() - a);
  }
  const uint64_t ovh = uint64_t(median(ov));
  printf("TSC %.3f GHz; timing overhead %llu cycles subtracted; runs=%d; %d lookups per pass\n", tpn,
         (unsigned long long)ovh, runs, n);

  const char* kModeName[4] = {"1T", "2T same handle", "2T diff handles", "2T, T2 holds G 2us/20us"};
  const char* kVar[2] = {"OLD", "NEW"};
  std::vector<Pass> tp[4][2], lt[4][2];
  std::vector<double> lat;
  for (int r = 0; r < runs; ++r) {
    printf("--- run %d ---\n", r + 1);
    for (int i = 0; i < 8; ++i) {
      const int idx = (i + r * 3) % 8, mode = idx / 2, v = idx % 2;
      Pass a = v ? run_pass<1>(mode, n, false, ovh, lat) : run_pass<0>(mode, n, false, ovh, lat);
      Pass b = v ? run_pass<1>(mode, n, true, ovh, lat) : run_pass<0>(mode, n, true, ovh, lat);
      tp[mode][v].push_back(a);
      lt[mode][v].push_back(b);
      printf("  %-24s %s  mean %6.1f ns  p50 %6.1f p99 %7.1f p99.9 %8.1f max %9.1f ns  >1us %.3f%%", kModeName[mode],
             kVar[v], a.ns, b.lat.med, b.lat.p99, b.lat.p999, b.lat.max, b.over1us);
      if (mode == kContend) printf("  G duty %.1f%%\n", 100.0 * a.t2.ops * 2e-6 / a.t2.secs);
      else if (mode != k1T) printf("  T2 %.1f ns/lookup\n", a.t2.secs * 1e9 / double(a.t2.ops));
      else printf("\n");
    }
    fflush(stdout);
  }
  printf("\nSUMMARY thread-1 ns per lookup+Release, median of %d runs (max = max over all runs)\n", runs);
  printf("  %-24s | var | mean (untimed)         | p50    | p99     | p99.9    | max       | >1us   | T2\n", "mode");
  for (int m = 0; m < 4; ++m)
    for (int v = 0; v < 2; ++v) {
      std::vector<double> mean, p50, p99, p999, mx, o1, t2;
      for (auto& x : tp[m][v]) {
        mean.push_back(x.ns);
        if (m == kContend) t2.push_back(100.0 * x.t2.ops * 2e-6 / x.t2.secs);
        else if (m != k1T) t2.push_back(x.t2.secs * 1e9 / double(x.t2.ops));
      }
      for (auto& x : lt[m][v]) {
        p50.push_back(x.lat.med); p99.push_back(x.lat.p99); p999.push_back(x.lat.p999);
        mx.push_back(x.lat.max); o1.push_back(x.over1us);
      }
      char t2s[48] = "-";
      if (!t2.empty()) snprintf(t2s, sizeof t2s, m == kContend ? "G duty %.1f%%" : "%.1f ns", median(t2));
      printf("  %-24s | %s | %6.1f [%6.1f..%6.1f] | %6.1f | %7.1f | %8.1f | %9.1f | %.3f%% | %s\n", kModeName[m],
             kVar[v], median(mean), vmin(mean), vmax(mean), median(p50), median(p99), median(p999), vmax(mx),
             median(o1), t2s);
    }
  bench_a::print_machine_state("end");
  return 0;
}
