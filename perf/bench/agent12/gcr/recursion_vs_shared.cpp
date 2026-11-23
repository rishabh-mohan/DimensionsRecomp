// S1 (Agent 12 / J3, checklist C2 + C14): re-entrancy of today's global critical
// region (std::recursive_mutex, everything exclusive + recursive) versus
// std::shared_mutex based replacements (MSVC: SRWLOCK), including the
// thread_local write-depth scheme of Agent 11's plan item 7.
//
// Part 1: pattern matrix. Each pattern runs on fresh threads; "DEADLOCK" means
//         no progress within the timeout (the stuck threads are leaked and the
//         process ends with _Exit).
// Part 2: mutual exclusion + nesting under 2 threads for the schemes that allow it.
// Part 3: writer wait under a 2-reader flood (lookups vs AddHandle/RemoveHandle).
//
// Standalone, no SDK. <= 3 threads alive at a time doing work, 2 busy.
#define NOMINMAX
#include <windows.h>
#include <immintrin.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <shared_mutex>
#include <thread>
#include <vector>

using clk = std::chrono::steady_clock;

struct Scheme {
  virtual ~Scheme() = default;
  virtual const char* name() const = 0;
  virtual void lockR() = 0;
  virtual void unlockR() = 0;
  virtual void lockW() = 0;
  virtual void unlockW() = 0;
};

struct RecursiveG final : Scheme {
  std::recursive_mutex m;
  const char* name() const override { return "recursive_mutex (G today)"; }
  void lockR() override { m.lock(); }
  void unlockR() override { m.unlock(); }
  void lockW() override { m.lock(); }
  void unlockW() override { m.unlock(); }
};

struct RawShared final : Scheme {
  std::shared_mutex m;
  const char* name() const override { return "shared_mutex, no depth"; }
  void lockR() override { m.lock_shared(); }
  void unlockR() override { m.unlock_shared(); }
  void lockW() override { m.lock(); }
  void unlockW() override { m.unlock(); }
};

thread_local int t_wdepth = 0;
thread_local int t_rdepth = 0;

// Agent 11 plan item 7: thread_local write depth; a lookup skips the shared
// lock when the thread already holds the table exclusively.
struct WriteDepthShared final : Scheme {
  std::shared_mutex m;
  const char* name() const override { return "shared_mutex + write depth (A11)"; }
  void lockR() override {
    if (t_wdepth == 0) m.lock_shared();
  }
  void unlockR() override {
    if (t_wdepth == 0) m.unlock_shared();
  }
  void lockW() override {
    if (t_wdepth++ == 0) m.lock();
  }
  void unlockW() override {
    if (--t_wdepth == 0) m.unlock();
  }
};

// Additionally tracks read depth, so a nested lookup never re-acquires shared.
struct RWDepthShared final : Scheme {
  std::shared_mutex m;
  const char* name() const override { return "shared_mutex + read+write depth"; }
  void lockR() override {
    if (t_wdepth > 0) return;
    if (t_rdepth++ == 0) m.lock_shared();
  }
  void unlockR() override {
    if (t_wdepth > 0) return;
    if (--t_rdepth == 0) m.unlock_shared();
  }
  void lockW() override {  // upgrade from a read section still self-deadlocks
    if (t_wdepth++ == 0) m.lock();
  }
  void unlockW() override {
    if (--t_wdepth == 0) m.unlock();
  }
};

static Scheme* MakeScheme(int i) {
  switch (i) {
    case 0: return new RecursiveG();
    case 1: return new RawShared();
    case 2: return new WriteDepthShared();
    default: return new RWDepthShared();
  }
}

enum Pattern { kRR_WriterQueued, kRR_NoWriter, kR_then_W, kW_then_R, kW_then_W, kPatternCount };
static const char* kPatternNames[kPatternCount] = {"R>R + queued writer", "R>R no writer",
                                                   "R>W (upgrade)", "W>R", "W>W"};

struct RunState {
  std::atomic<int> ready{0}, writer_started{0}, holder_done{0}, writer_done{0};
};

// True if the pattern completed, false on timeout (deadlock).
static bool RunPattern(Scheme* s, Pattern p, int timeout_ms) {
  auto* st = new RunState();
  std::thread holder([s, st, p] {
    switch (p) {
      case kRR_WriterQueued:
        s->lockR();
        st->ready = 1;
        while (!st->writer_started) Sleep(1);
        Sleep(100);  // let the writer block in lockW()
        s->lockR();
        st->holder_done = 1;
        s->unlockR();
        s->unlockR();
        break;
      case kRR_NoWriter:
        s->lockR();
        s->lockR();
        st->holder_done = 1;
        s->unlockR();
        s->unlockR();
        break;
      case kR_then_W:
        s->lockR();
        s->lockW();
        st->holder_done = 1;
        s->unlockW();
        s->unlockR();
        break;
      case kW_then_R:
        s->lockW();
        s->lockR();
        st->holder_done = 1;
        s->unlockR();
        s->unlockW();
        break;
      case kW_then_W:
        s->lockW();
        s->lockW();
        st->holder_done = 1;
        s->unlockW();
        s->unlockW();
        break;
      default:
        break;
    }
  });
  std::thread writer;
  if (p == kRR_WriterQueued) {
    writer = std::thread([s, st] {
      while (!st->ready) Sleep(1);
      st->writer_started = 1;
      s->lockW();
      st->writer_done = 1;
      s->unlockW();
    });
  }
  const auto deadline = clk::now() + std::chrono::milliseconds(timeout_ms);
  bool ok = false;
  while (clk::now() < deadline) {
    if (st->holder_done && (p != kRR_WriterQueued || st->writer_done)) {
      ok = true;
      break;
    }
    Sleep(2);
  }
  if (ok) {
    holder.join();
    if (writer.joinable()) writer.join();
    delete st;
  } else {
    holder.detach();
    if (writer.joinable()) writer.detach();
    // st and the scheme are leaked on purpose: the stuck threads still use them.
  }
  return ok;
}

// Part 2: 2 threads, random nesting depth 1..8 of write sections with a nested
// lookup; asserts that at most one thread is ever inside.
static void PartMutualExclusion(Scheme* s, int ms) {
  std::atomic<int> inside{0};
  std::atomic<uint64_t> violations{0}, iters{0};
  std::atomic<bool> stop{false};
  auto body = [&](uint32_t x) {
    while (!stop.load(std::memory_order_relaxed)) {
      x = x * 1664525u + 1013904223u;
      const int depth = 1 + int((x >> 28) % 8);
      for (int d = 0; d < depth; ++d) {
        s->lockW();
        if (d == 0 && inside.fetch_add(1) != 0) violations++;
        if (d == 1) {
          s->lockR();
          s->unlockR();
        }
      }
      for (int d = depth - 1; d >= 0; --d) {
        if (d == 0) inside.fetch_sub(1);
        s->unlockW();
      }
      iters.fetch_add(1, std::memory_order_relaxed);
    }
  };
  std::thread a(body, 1u), b(body, 7u);
  Sleep(ms);
  stop = true;
  a.join();
  b.join();
  printf("  %-36s iterations=%-10llu mutual-exclusion violations=%llu -> %s\n", s->name(),
         (unsigned long long)iters.load(), (unsigned long long)violations.load(),
         violations.load() ? "FAIL" : "ok");
}

// Part 3: 2 reader threads flood lookups (hold ~50 pauses); a mostly sleeping
// writer acquires every ~1 ms and records its wait.
static void PartWriterWait(Scheme* s, int ms) {
  std::atomic<bool> stop{false};
  std::atomic<uint64_t> reads{0};
  auto reader = [&] {
    while (!stop.load(std::memory_order_relaxed)) {
      s->lockR();
      for (int i = 0; i < 50; ++i) _mm_pause();
      s->unlockR();
      reads.fetch_add(1, std::memory_order_relaxed);
    }
  };
  std::vector<double> waits;
  waits.reserve(4096);
  std::thread r1(reader), r2(reader);
  const auto t_start = clk::now();
  const auto end = t_start + std::chrono::milliseconds(ms);
  while (clk::now() < end) {
    const auto t0 = clk::now();
    s->lockW();
    const auto t1 = clk::now();
    for (int i = 0; i < 20; ++i) _mm_pause();
    s->unlockW();
    waits.push_back(std::chrono::duration<double, std::micro>(t1 - t0).count());
    Sleep(1);
  }
  stop = true;
  r1.join();
  r2.join();
  const double secs = std::chrono::duration<double>(clk::now() - t_start).count();
  std::sort(waits.begin(), waits.end());
  double sum = 0;
  for (double w : waits) sum += w;
  const size_t n = waits.size();
  printf("  %-36s reads/s=%9.0f  writer waits: n=%zu avg=%.2fus p50=%.2fus p99=%.2fus max=%.2fus\n",
         s->name(), reads.load() / secs, n, n ? sum / n : 0.0, n ? waits[n / 2] : 0.0,
         n ? waits[std::min(n - 1, n * 99 / 100)] : 0.0, n ? waits[n - 1] : 0.0);
}

int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  const int kTimeoutMs = 700;
  printf("S1 recursion_vs_shared: re-entrancy matrix (OK = completed, DEADLOCK = no progress in %d ms)\n",
         kTimeoutMs);
  printf("  %-36s", "scheme \\ pattern");
  for (int p = 0; p < kPatternCount; ++p) printf(" | %-19s", kPatternNames[p]);
  printf("\n");
  for (int si = 0; si < 4; ++si) {
    Scheme* name_probe = MakeScheme(si);
    printf("  %-36s", name_probe->name());
    delete name_probe;
    for (int p = 0; p < kPatternCount; ++p) {
      Scheme* s = MakeScheme(si);
      const bool ok = RunPattern(s, Pattern(p), kTimeoutMs);
      printf(" | %-19s", ok ? "OK" : "DEADLOCK");
      if (ok) delete s;
    }
    printf("\n");
  }

  printf("\nPart 2: mutual exclusion with nesting (2 threads, 1 s each)\n");
  {
    Scheme* a = MakeScheme(0);
    PartMutualExclusion(a, 1000);
    delete a;
    Scheme* b = MakeScheme(2);
    PartMutualExclusion(b, 1000);
    delete b;
    Scheme* c = MakeScheme(3);
    PartMutualExclusion(c, 1000);
    delete c;
  }

  printf("\nPart 3: writer wait under a 2-reader lookup flood (2 s each)\n");
  {
    Scheme* a = MakeScheme(0);
    PartWriterWait(a, 2000);
    delete a;
    Scheme* b = MakeScheme(1);
    PartWriterWait(b, 2000);
    delete b;
  }
  fflush(stdout);
  std::_Exit(0);
}
