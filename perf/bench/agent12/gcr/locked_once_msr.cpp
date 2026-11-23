// S5 (Agent 12 / J3, checklist C4 C9, hazards H3 H9 H10):
//  a) "locked once" violation: a callee that receives the global lock and does
//     unlock(); wait-for-producer; lock() (rexlego PhysicalDependencyProvider::
//     Deliver, EntryTable::GetOrCreate) or condition_variable_any::wait(lock),
//     while the thread holds the recursive mutex twice (MMIO fault inside an
//     ENTER section / kernel export / guest ISR). Producer needs the mutex.
//  b) the proposed fix: a thread_local depth on the global critical region and
//     an assert(depth == 1) before any unlock/wait in callees.
//  c) REX_CHECK_GLOBAL_LOCK (mfmsr) locked read vs rexlego LockElidedMsr()
//     lock-free read: how often does a thread that is NOT in an ENTER section
//     see "interrupts disabled"?
//  d) mfmsr rendezvous: latency of the locked CHECK while another thread holds
//     G for 20 us out of every ~100 us (long kernel G holds).
// Standalone, no SDK. 2 busy threads max, < 10 s.
#define NOMINMAX
#include <windows.h>
#include <immintrin.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <thread>
#include <vector>

using clk = std::chrono::steady_clock;

static double g_ticks_per_us = 0;
static inline int64_t Qpc() {
  LARGE_INTEGER t;
  QueryPerformanceCounter(&t);
  return t.QuadPart;
}
static inline void SpinUs(double us) {
  const int64_t end = Qpc() + int64_t(us * g_ticks_per_us);
  while (Qpc() < end) _mm_pause();
}

struct ProdState {
  std::recursive_mutex* m;
  std::atomic<int> produced{0};
  std::condition_variable_any cv;
};

// Callee pattern 1: unlock / wait for producer / relock.
static bool CalleeUnlockWait(std::unique_lock<std::recursive_mutex>& lk, ProdState* st,
                             std::thread& producer, int timeout_ms) {
  producer = std::thread([st] {
    {
      std::lock_guard<std::recursive_mutex> g(*st->m);
      st->produced = 1;
    }
    st->cv.notify_all();
  });
  lk.unlock();
  const auto deadline = clk::now() + std::chrono::milliseconds(timeout_ms);
  while (clk::now() < deadline && !st->produced.load()) Sleep(1);
  lk.lock();
  return st->produced.load() != 0;
}

// Callee pattern 2: condition_variable_any::wait_for on the passed-in lock.
static bool CalleeCvWait(std::unique_lock<std::recursive_mutex>& lk, ProdState* st,
                         std::thread& producer, int timeout_ms) {
  producer = std::thread([st] {
    {
      std::lock_guard<std::recursive_mutex> g(*st->m);
      st->produced = 1;
    }
    st->cv.notify_all();
  });
  return st->cv.wait_for(lk, std::chrono::milliseconds(timeout_ms),
                         [st] { return st->produced.load() != 0; });
}

static void RunLockedOnce(const char* name, int depth, bool use_cv) {
  std::recursive_mutex m;
  ProdState st;
  st.m = &m;
  for (int i = 1; i < depth; ++i) m.lock();  // outer holders (ENTER section, export, ...)
  std::thread producer;
  bool ok;
  {
    std::unique_lock<std::recursive_mutex> lk(m);  // "global_lock_locked_once"
    ok = use_cv ? CalleeCvWait(lk, &st, producer, 600) : CalleeUnlockWait(lk, &st, producer, 600);
  }
  for (int i = 1; i < depth; ++i) m.unlock();
  producer.join();  // the producer gets the mutex once the outer levels are gone
  printf("  %-34s depth=%d -> %s\n", name, depth,
         ok ? "ok (producer ran while waiting)" : "DEADLOCK while waiting (timed out; G still held by the waiter)");
}

// b) depth-tracked global critical region.
struct TrackedG {
  std::recursive_mutex m;
  static inline thread_local int depth = 0;
  void lock() {
    m.lock();
    ++depth;
  }
  void unlock() {
    --depth;
    m.unlock();
  }
};

static void RunDepthAssert(int depth) {
  TrackedG g;
  for (int i = 0; i < depth; ++i) g.lock();
  // Callee contract check before dropping the lock:
  const bool would_deadlock = TrackedG::depth != 1;
  for (int i = 0; i < depth; ++i) g.unlock();
  printf("  depth-tracked G, depth=%d: callee check depth==1 -> %s\n", depth,
         would_deadlock ? "REFUSES to unlock+wait (assert fires / fall back to non-blocking path)"
                        : "unlock+wait allowed");
}

// c) LockElidedMsr vs locked CHECK.
static void RunMsrCheck(bool locked, int ms) {
  std::recursive_mutex G;
  std::atomic<int> count{0};
  std::atomic<bool> stop{false};
  std::thread enter([&] {  // non-elided ENTER sections on another thread
    while (!stop.load(std::memory_order_relaxed)) {
      G.lock();
      count.fetch_add(1);
      for (int i = 0; i < 30; ++i) _mm_pause();
      count.fetch_sub(1);
      G.unlock();
      for (int i = 0; i < 30; ++i) _mm_pause();
    }
  });
  uint64_t n = 0, disabled = 0;
  const auto end = clk::now() + std::chrono::milliseconds(ms);
  while (clk::now() < end) {
    for (int k = 0; k < 256; ++k) {
      int v;
      if (locked) {
        std::lock_guard<std::recursive_mutex> l(G);  // REX_CHECK_GLOBAL_LOCK
        v = count.load();
      } else {
        v = count.load(std::memory_order_acquire);  // LockElidedMsr-style
      }
      ++n;
      if (v) ++disabled;
    }
  }
  stop = true;
  enter.join();
  printf("  %-28s reads=%llu  reported 'EE disabled' (wrong, reader is not in a section)=%llu (%.2f%%)\n",
         locked ? "locked CHECK (mfmsr today)" : "lock-free (LockElidedMsr)", (unsigned long long)n,
         (unsigned long long)disabled, n ? 100.0 * disabled / n : 0.0);
}

// d) mfmsr latency while another thread holds G for long stretches.
static void RunMsrLatency(int ms, double hold_us, double gap_us) {
  std::recursive_mutex G;
  std::atomic<int> count{0};
  std::atomic<bool> stop{false};
  std::thread holder([&] {
    while (!stop.load(std::memory_order_relaxed)) {
      G.lock();
      SpinUs(hold_us);
      G.unlock();
      SpinUs(gap_us);
    }
  });
  std::vector<double> lat;
  lat.reserve(1 << 20);
  const auto end = clk::now() + std::chrono::milliseconds(ms);
  while (clk::now() < end && lat.size() < (1u << 20)) {
    const int64_t t0 = Qpc();
    {
      std::lock_guard<std::recursive_mutex> l(G);
      (void)count.load();
    }
    const int64_t t1 = Qpc();
    lat.push_back(double(t1 - t0) / g_ticks_per_us);
    SpinUs(1.0);  // guest work between mfmsr instructions
  }
  stop = true;
  holder.join();
  std::sort(lat.begin(), lat.end());
  double sum = 0;
  size_t over1 = 0;
  for (double v : lat) {
    sum += v;
    if (v > 1.0) ++over1;
  }
  const size_t n = lat.size();
  printf("  G held %.0f us every %.0f us: mfmsr n=%zu avg=%.2fus p50=%.2fus p99=%.2fus max=%.2fus, >1us: %.1f%%\n",
         hold_us, hold_us + gap_us, n, sum / n, lat[n / 2], lat[std::min(n - 1, n * 99 / 100)],
         lat[n - 1], 100.0 * over1 / n);
}

int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  LARGE_INTEGER f;
  QueryPerformanceFrequency(&f);
  g_ticks_per_us = double(f.QuadPart) / 1e6;
  printf("S5 locked_once_msr\na) callee drops the passed-in global lock while waiting for a producer that needs it\n");
  RunLockedOnce("unlock/wait/lock (Deliver-style)", 1, false);
  RunLockedOnce("unlock/wait/lock (Deliver-style)", 2, false);
  RunLockedOnce("condition_variable_any::wait_for", 1, true);
  RunLockedOnce("condition_variable_any::wait_for", 2, true);
  printf("b) proposed fix: thread_local depth + assert(depth == 1) in callees\n");
  RunDepthAssert(1);
  RunDepthAssert(2);
  printf("c) mfmsr semantics: reader thread not in a section, other thread in ENTER sections ~50%% of the time (1 s each)\n");
  RunMsrCheck(true, 1000);
  RunMsrCheck(false, 1000);
  printf("d) mfmsr rendezvous cost (locked CHECK) while another thread holds G (1.5 s each)\n");
  RunMsrLatency(1500, 2.0, 98.0);
  RunMsrLatency(1500, 20.0, 80.0);
  fflush(stdout);
  std::_Exit(0);
}
