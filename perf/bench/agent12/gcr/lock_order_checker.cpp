// S3 (Agent 12 / J3, checklist C1 C12 C13): a drop-in debug lock-order checker
// (per-thread held-lock stack, global "acquired-after" graph, cycle detection,
// recursion- and shared-mode-aware) plus a replay of the real lock edges from
// perf-notes/agent12-gcr-map.md §3 and injected inversions a narrowing could
// introduce. Also measures the checker's per-acquisition overhead.
//
// Intended SDK use (debug builds only): wrap global_critical_region::mutex(),
// BaseHeap::heap_mutex_, ObjectTable::name_mutex_, dispatch_mutex_,
// on_demand_mutex_, memexport_cpu_writes_mutex_ and any new lock (e.g. Agent
// 11's table shared_mutex) in CheckedMutex / CheckedSharedMutex, and call
// OnAcquire/OnRelease from REX_ENTER/LEAVE_GLOBAL_LOCK.
// Standalone, no SDK. Single thread (plus none).
#define NOMINMAX
#include <windows.h>

#include <atomic>
#include <chrono>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <mutex>
#include <shared_mutex>
#include <vector>

namespace lockorder {

constexpr int kMaxClasses = 64;
enum class Mode { kExclusive, kShared };

struct Held {
  int cls;
  Mode mode;
  int depth;
  const char* site;
};

class Checker {
 public:
  int Register(const char* name, bool recursive) {
    std::lock_guard<std::mutex> l(m_);
    const int id = n_++;
    names_[id] = name;
    recursive_[id] = recursive;
    return id;
  }

  void OnAcquire(int cls, Mode mode, const char* site) {
    std::vector<Held>& held = Stack();
    for (auto it = held.rbegin(); it != held.rend(); ++it) {
      if (it->cls != cls) continue;
      if (it->mode == Mode::kExclusive && mode == Mode::kExclusive && recursive_[cls]) {
        it->depth++;
        return;
      }
      if (it->mode == Mode::kShared && mode == Mode::kShared) {
        Report("shared re-entry of [%s] at %s (shared since %s): deadlocks if a writer queues in between",
               names_[cls], site, it->site);
      } else if (it->mode == Mode::kShared && mode == Mode::kExclusive) {
        Report("upgrade: exclusive [%s] at %s while holding it shared (since %s): self-deadlock",
               names_[cls], site, it->site);
      } else if (it->mode == Mode::kExclusive && mode == Mode::kShared) {
        Report("shared [%s] at %s while holding it exclusive (since %s): self-deadlock without depth tracking",
               names_[cls], site, it->site);
      } else {
        Report("non-recursive [%s] re-acquired at %s (held since %s): self-deadlock", names_[cls],
               site, it->site);
      }
      held.push_back({cls, mode, 1, site});
      return;
    }
    const uint64_t bit = uint64_t(1) << cls;
    for (const Held& h : held) {
      if (adj_[h.cls].load(std::memory_order_relaxed) & bit) continue;  // known edge, fast path
      std::lock_guard<std::mutex> l(m_);
      if (adj_[h.cls].load(std::memory_order_relaxed) & bit) continue;
      int path[kMaxClasses];
      int path_len = 0;
      if (FindPath(cls, h.cls, path, &path_len)) {
        char buf[1024];
        int off = 0;
        for (int i = 0; i + 1 < path_len && off < 900; ++i) {
          off += snprintf(buf + off, sizeof(buf) - off, "\n      [%s] -> [%s] first at %s",
                          names_[path[i]], names_[path[i + 1]], site_[path[i]][path[i + 1]]);
        }
        Report("lock-order inversion: acquiring [%s] at %s while holding [%s] (since %s); existing order:%s",
               names_[cls], site, names_[h.cls], h.site, buf);
        continue;  // keep the graph as the legit order
      }
      site_[h.cls][cls] = site;
      adj_[h.cls].fetch_or(bit, std::memory_order_relaxed);
    }
    held.push_back({cls, mode, 1, site});
  }

  void OnRelease(int cls) {
    std::vector<Held>& held = Stack();
    for (auto it = held.rbegin(); it != held.rend(); ++it) {
      if (it->cls == cls) {
        if (--it->depth == 0) held.erase(std::next(it).base());
        return;
      }
    }
    Report("release of [%s] which this thread does not hold", names_[cls]);
  }

  int violations() const { return violations_.load(); }
  bool quiet = false;

  void PrintEdges() {
    std::lock_guard<std::mutex> l(m_);
    for (int a = 0; a < n_; ++a) {
      for (int b = 0; b < n_; ++b) {
        if (adj_[a].load() & (uint64_t(1) << b)) {
          printf("    [%s] -> [%s]   (first at %s)\n", names_[a], names_[b], site_[a][b]);
        }
      }
    }
  }

 private:
  static std::vector<Held>& Stack() {
    thread_local std::vector<Held> s;
    return s;
  }
  // BFS from -> to over the edge sets; writes the path (from..to).
  bool FindPath(int from, int to, int* path, int* len) {
    int parent[kMaxClasses];
    for (int i = 0; i < kMaxClasses; ++i) parent[i] = -2;
    int queue[kMaxClasses];
    int qh = 0, qt = 0;
    queue[qt++] = from;
    parent[from] = -1;
    while (qh < qt) {
      const int c = queue[qh++];
      if (c == to) break;
      const uint64_t e = adj_[c].load(std::memory_order_relaxed);
      for (int d = 0; d < n_; ++d) {
        if ((e & (uint64_t(1) << d)) && parent[d] == -2) {
          parent[d] = c;
          queue[qt++] = d;
        }
      }
    }
    if (parent[to] == -2) return false;
    int rev[kMaxClasses];
    int n = 0;
    for (int c = to; c != -1; c = parent[c]) rev[n++] = c;
    for (int i = 0; i < n; ++i) path[i] = rev[n - 1 - i];
    *len = n;
    return true;
  }
  void Report(const char* fmt, ...) {
    violations_++;
    if (quiet) return;
    va_list ap;
    va_start(ap, fmt);
    printf("    VIOLATION: ");
    vprintf(fmt, ap);
    printf("\n");
    va_end(ap);
  }

  std::mutex m_;  // leaf, never checked
  const char* names_[kMaxClasses] = {};
  bool recursive_[kMaxClasses] = {};
  std::atomic<uint64_t> adj_[kMaxClasses] = {};
  const char* site_[kMaxClasses][kMaxClasses] = {};
  int n_ = 0;
  std::atomic<int> violations_{0};
};

Checker& Global() {
  static Checker c;
  return c;
}

// Drop-in wrappers.
template <class M>
class CheckedMutex {
 public:
  CheckedMutex(const char* name, bool recursive) : cls_(Global().Register(name, recursive)) {}
  void lock(const char* site = "?") {
    Global().OnAcquire(cls_, Mode::kExclusive, site);
    m_.lock();
  }
  void unlock() {
    m_.unlock();
    Global().OnRelease(cls_);
  }
  M& raw() { return m_; }

 private:
  M m_;
  int cls_;
};

}  // namespace lockorder

using lockorder::Mode;

int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  lockorder::Checker C;
  const int G = C.Register("G global_critical_region", true);
  const int HEAP = C.Register("BaseHeap::heap_mutex_", true);
  const int NAME = C.Register("ObjectTable::name_mutex_", false);
  const int DISP = C.Register("FunctionDispatcher::dispatch_mutex_", false);
  const int OND = C.Register("CP::on_demand_mutex_", false);
  const int MCW = C.Register("CP::memexport_cpu_writes_mutex_", false);
  const int FRAMES = C.Register("SDL driver frames_mutex_", false);
  const int TLS = C.Register("guest spinlock tls_lock", false);
  const int T = C.Register("A11 object-table shared_mutex T", false);
  auto A = [&](int c, const char* site) { C.OnAcquire(c, Mode::kExclusive, site); };
  auto S = [&](int c, const char* site) { C.OnAcquire(c, Mode::kShared, site); };
  auto R = [&](int c) { C.OnRelease(c); };

  printf("S3 lock_order_checker\n1) replay of the legit edges from the map (expect 0 violations)\n");
  A(G, "mtmsrd r13 (REX_ENTER_GLOBAL_LOCK)");
  A(G, "GetNativeObject xobject.cpp:395");
  A(G, "AddHandle object_table.cpp:103");
  A(NAME, "AddNameMapping");
  R(NAME);
  R(G);
  R(G);
  R(G);
  A(G, "PhysicalHeap::Release xmemory.cpp:2104");
  A(HEAP, "BaseHeap::Release xmemory.cpp:1655");
  R(HEAP);
  R(G);
  A(G, "CreateNative xobject.cpp:335");
  A(HEAP, "SystemHeapAlloc xobject.cpp:339");
  R(HEAP);
  A(G, "SetNativePointer xobject.cpp:363");
  R(G);
  R(G);
  A(G, "UnloadUserModule kernel_state.cpp:884");
  A(DISP, "FunctionDispatcher::UnregisterModule");
  R(DISP);
  R(G);
  A(G, "PublishOnDemandMemexport command_processor.cpp:3182");
  A(OND, "command_processor.cpp:3183");
  A(G, "SetDataProviders xmemory.cpp:2543");
  R(G);
  A(MCW, "command_processor.cpp:3205");
  R(MCW);
  R(OND);
  R(G);
  A(G, "FireWatchesLocked shared_memory.cpp:245");
  A(MCW, "MemexportCpuWriteWatchThunk command_processor.cpp:3403");
  R(MCW);
  R(G);
  A(G, "SubmitFrame audio_system.cpp:273");
  A(FRAMES, "SDL driver WriteFrame");
  R(FRAMES);
  R(G);
  A(TLS, "FreeTLS kernel_state.cpp:406");
  A(G, "GetObjectsByType object_table.cpp:305");
  R(G);
  R(TLS);
  A(G, "AddHandle (A11 plan)");
  A(T, "TableWriteLock (A11 plan)");
  A(NAME, "AddNameMapping (A11 plan)");
  R(NAME);
  R(T);
  R(G);
  S(T, "LookupObject fast path (shared)");
  R(T);
  A(G, "MMIOHandler::ExceptionCallback mmio_handler.cpp:408");
  A(G, "SharedMemory::MemoryInvalidationCallback shared_memory.cpp:529");
  R(G);
  R(G);
  const int legit = C.violations();
  printf("   violations in legit replay: %d -> %s\n   learned order:\n", legit, legit ? "FAIL" : "ok");
  C.PrintEdges();

  struct Inj {
    const char* what;
    std::function<void()> run;
  };
  std::vector<Inj> inj = {
      {"A: narrowed GetObjectByName keeps name_mutex_ across LookupObject",
       [&] {
         A(NAME, "GetObjectByName (narrowed)");
         A(G, "LookupObject");
         R(G);
         R(NAME);
       }},
      {"B: Publish narrowed off G (on_demand_mutex_ then SetDataProviders)",
       [&] {
         A(OND, "PublishOnDemandMemexport without G");
         A(G, "SetDataProviders xmemory.cpp:2543");
         R(G);
         R(OND);
       }},
      {"C: host write to a watched page while holding heap_mutex_ (VEH takes G)",
       [&] {
         A(HEAP, "BaseHeap op touching guest memory");
         A(G, "MMIOHandler::ExceptionCallback (fault)");
         R(G);
         R(HEAP);
       }},
      {"D: Release -> ~XThread -> UnregisterThread under shared T (no G)",
       [&] {
         S(T, "LookupObject fast path");
         A(G, "KernelState::UnregisterThread kernel_state.cpp:1078");
         R(G);
         R(T);
       }},
      {"E: a G holder spins on the guest tls_lock spinlock",
       [&] {
         A(G, "some export holding G");
         A(TLS, "xeKeKfAcquireSpinLock");
         R(TLS);
         R(G);
       }},
      {"F: nested shared T (lookup inside lookup) - SRWLOCK shared re-entry",
       [&] {
         S(T, "LookupObject");
         S(T, "nested LookupObject");
         R(T);
         R(T);
       }},
      {"G: upgrade shared T -> exclusive (lookup path ends in RemoveHandle)",
       [&] {
         S(T, "LookupObject");
         A(T, "RemoveHandle TableWriteLock");
         R(T);
         R(T);
       }},
      {"H: kernel call (G) from inside the SDL audio callback holding frames_mutex_",
       [&] {
         A(FRAMES, "SDL audio callback");
         A(G, "kernel export");
         R(G);
         R(FRAMES);
       }},
  };
  printf("\n2) injected inversions (each must be detected)\n");
  int detected = 0;
  for (const Inj& i : inj) {
    const int before = C.violations();
    printf("  %s\n", i.what);
    i.run();
    const bool hit = C.violations() > before;
    detected += hit;
    printf("   -> %s\n", hit ? "DETECTED" : "MISSED");
  }
  printf("   detected %d/%zu\n", detected, inj.size());

  // 3) overhead: raw vs checked, single thread, G -> heap nesting.
  printf("\n3) overhead (single thread, nested G -> heap acquire/release pair)\n");
  {
    std::recursive_mutex rg, rh;
    lockorder::CheckedMutex<std::recursive_mutex> cg("bench G", true), ch("bench heap", true);
    constexpr int kIters = 2000000;
    auto t0 = std::chrono::steady_clock::now();
    for (int i = 0; i < kIters; ++i) {
      rg.lock();
      rh.lock();
      rh.unlock();
      rg.unlock();
    }
    auto t1 = std::chrono::steady_clock::now();
    for (int i = 0; i < kIters; ++i) {
      cg.lock("bench G");
      ch.lock("bench heap");
      ch.unlock();
      cg.unlock();
    }
    auto t2 = std::chrono::steady_clock::now();
    const double raw = std::chrono::duration<double, std::nano>(t1 - t0).count() / kIters;
    const double chk = std::chrono::duration<double, std::nano>(t2 - t1).count() / kIters;
    printf("   raw %.1f ns/iter, checked %.1f ns/iter (+%.1f ns per 2 acquisitions), violations=%d\n",
           raw, chk, chk - raw, lockorder::Global().violations());
  }
  const bool pass = legit == 0 && detected == int(inj.size());
  printf("\nresult: %s\n", pass ? "PASS" : "FAIL");
  return pass ? 0 : 1;
}
