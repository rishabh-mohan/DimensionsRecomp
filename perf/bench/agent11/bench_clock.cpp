// bench_clock.cpp - guest clock reads (agent11 bench (f)).
// OLD = replica of the mutex-based UpdateGuestClock() locked path in
//       src/core/clock.cpp (std::mutex try_lock, else lock() and return last).
// NEW = replica of the seqlock now in clock.cpp (ReadGuestClockLockFree +
//       SetGuestTickRatioLocked). It matches agent11-s2-plan.md step 7, except
//       that an odd seq is retried without _mm_pause and the host clock is
//       sampled inside the read window (after the loads, before the re-check).
// Usage: bench_clock.exe [runs=5]
#include "bench_common.h"

#include <immintrin.h>
#include <atomic>
#include <cstdlib>
#include <mutex>
#include <thread>

using u64 = uint64_t;
static constexpr auto rlx = std::memory_order_relaxed;
static inline u64 host() { return (u64)qpc(); }
static inline u64 scale(u64 d, u64 n, u64 den) { return (d / den) * n + (d % den) * n / den; }

// ---- OLD: UpdateGuestClock() (clock_no_scaling off), same arithmetic ----
struct OldClock {
  u64 num = 1, den = 1, last_guest = 0, last_host = 0;
  std::mutex m;  // tick_mutex_
  u64 read() {
    u64 host_tick_count = host();
    std::unique_lock<std::mutex> lock(m, std::defer_lock);
    if (lock.try_lock()) {
      u64 host_tick_delta = host_tick_count > last_host ? host_tick_count - last_host : 0;
      last_host = host_tick_count;
      u64 guest_tick_delta = host_tick_delta * num / den;
      last_guest += guest_tick_delta;
      return last_guest;
    } else {
      lock.lock();
      return last_guest;
    }
  }
  void reset(u64 n, u64 d) { num = n; den = d; last_guest = 0; last_host = host(); }
};

enum Rebase { kNaive = 0, kAligned = 1, kNaiveMfence = 2 };
static const char* kRebaseName[] = {"naive(SDK)", "aligned", "naive+mfence"};

// ---- NEW: seqlock; `locked` is the fallback locked clock (same tick_mutex_) ----
struct SeqClock {
  std::atomic<uint32_t> seq{0};
  std::atomic<u64> hb{0}, gb{0}, num{0}, den{0};
  OldClock locked;
  std::atomic<u64> fallbacks{0};

  template <bool kLateQpc>
  bool try_read(u64* out) {
    for (int attempt = 0; attempt < 16; ++attempt) {
      const uint32_t s = seq.load(std::memory_order_acquire);
      const u64 d = den.load(rlx);
      if (!d) return false;
      if (s & 1) continue;
      const u64 n = num.load(rlx), b = hb.load(rlx), g = gb.load(rlx);
      u64 now = kLateQpc ? 0 : host();
      std::atomic_thread_fence(std::memory_order_acquire);
      if (seq.load(rlx) != s) continue;
      if (kLateQpc) {  // positive control: host clock sampled AFTER validation
        for (int i = 0; i < 64; ++i) _mm_pause();
        now = host();
      }
      *out = g + scale(now > b ? now - b : 0, n, d);
      return true;
    }
    return false;
  }
  template <bool kLateQpc = false>
  u64 read() {
    u64 v;
    if (try_read<kLateQpc>(&v)) return v;
    fallbacks.fetch_add(1, rlx);
    return locked.read();
  }
  // SetGuestTickRatioLocked with clock_lockfree on. kAligned: rebase at
  // h0' = hb + ceil((now-hb)/den_old)*den_old, G0' = gb + ceil(..)*num_old.
  void set_ratio(u64 fn, u64 fd, Rebase kind) {
    std::lock_guard<std::mutex> lk(locked.m);
    const u64 od = den.load(rlx);
    const uint32_t s = seq.load(rlx);
    seq.store(s + 1, rlx);
    if (kind == kNaiveMfence) std::atomic_thread_fence(std::memory_order_seq_cst);
    else std::atomic_thread_fence(std::memory_order_release);
    const u64 now = host();
    u64 nb = now, g;
    if (od) {
      const u64 b = hb.load(rlx), on = num.load(rlx), go = gb.load(rlx);
      if (kind == kAligned) {
        const u64 k = now > b ? (now - b + od - 1) / od : 0;
        nb = b + k * od;
        g = go + k * on;
      } else {
        g = go + scale(now > b ? now - b : 0, on, od);
      }
    } else {
      const u64 delta = now > locked.last_host ? now - locked.last_host : 0;
      g = locked.last_guest + delta * fn / fd;
    }
    locked.last_host = nb; locked.last_guest = g; locked.num = fn; locked.den = fd;
    hb.store(nb, rlx); gb.store(g, rlx); num.store(fn, rlx); den.store(fd, rlx);
    seq.store(s + 2, std::memory_order_release);
  }
  void reset(u64 fn, u64 fd) {  // only while no other thread uses the clock
    const u64 now = host();
    locked.reset(fn, fd);
    locked.last_host = now;
    hb.store(now, rlx); gb.store(0, rlx); num.store(fn, rlx); den.store(fd, rlx);
    seq.store(seq.load(rlx) + 2, std::memory_order_release);
    fallbacks.store(0, rlx);
  }
};

// ---- harness ----
struct Ctl {
  std::atomic<int> ready{0};
  std::atomic<bool> go{false}, stop{false};
};
struct Loop { double ns = NAN; u64 calls = 0, back = 0, maxstep = 0; };

// Reads until stop (the owner sets stop after `dur` QPC ticks); counts per-thread step-backs.
template <class F>
static void reader_loop(F& f, int64_t dur, bool owner, Ctl& c, Loop* out) {
  c.ready.fetch_add(1);
  while (!c.go.load(std::memory_order_acquire)) _mm_pause();
  u64 prev = 0, n = 0, b = 0, ms = 0;
  const int64_t t0 = qpc(), end = t0 + dur;
  for (;;) {
    for (int i = 0; i < 256; ++i) {
      const u64 v = f();
      if (v < prev) { ++b; ms = std::max(ms, prev - v); }
      prev = v;
    }
    n += 256;
    if (owner && qpc() >= end) c.stop.store(true, rlx);
    if (c.stop.load(rlx)) break;
  }
  out->ns = ticks_ns(qpc() - t0) / double(n);
  out->calls = n; out->back = b; out->maxstep = ms;
}

// T1 = this thread (reader). T2 = reader `f2` or any other loop body `g2(Ctl&)`.
template <class F1, class G2>
static void run_pair(F1& f1, G2 g2, int64_t dur, Loop* l1) {
  Ctl c;
  std::thread t2([&] { g2(c); });
  while (c.ready.load() < 1) _mm_pause();
  c.go.store(true, std::memory_order_release);
  reader_loop(f1, dur, true, c, l1);
  t2.join();
}

struct Cfg { const char* name; int var; u64 n, d; int threads; };  // var: 0 QPC, 1 OLD, 2 NEW
struct Res { Loop l[2]; double drift = NAN; u64 fb = 0; };

static Res run_cfg(const Cfg& cf, OldClock& oc, SeqClock& sc, int64_t dur) {
  Res r;
  auto fq = [] { return host(); };
  auto fo = [&] { return oc.read(); };
  auto fn = [&] { return sc.read(); };
  oc.reset(cf.n, cf.d);
  sc.reset(cf.n, cf.d);
  const u64 h0 = cf.var == 1 ? oc.last_host : sc.hb.load();
  auto go = [&](auto& f) {
    if (cf.threads == 1) {
      Ctl c;
      c.go = true;
      reader_loop(f, dur, true, c, &r.l[0]);
    } else {
      run_pair(f, [&](Ctl& c) { reader_loop(f, dur, false, c, &r.l[1]); }, dur, &r.l[0]);
    }
  };
  if (cf.var == 0) go(fq);
  else if (cf.var == 1) go(fo);
  else go(fn);
  if (cf.var) {
    const u64 g = cf.var == 1 ? oc.read() : sc.read();
    const u64 h = host();
    r.drift = double(g) / (double(h - h0) * double(cf.n) / double(cf.d));
    r.fb = sc.fallbacks.load();
  }
  return r;
}

// Monotonicity with a concurrent writer. alt: rebase about every 1 ms (Sleep(1)
// under timeBeginPeriod(1)), alternating 5/3 and 1/1; else rebase every ~10 us
// with the same ratio 5/3. late: reader samples QPC after validation.
struct Mono { u64 reads = 0, back = 0, maxstep = 0, rebases = 0, fb = 0; };
static Mono run_mono(SeqClock& sc, Rebase kind, bool alt, bool late, int64_t dur) {
  Mono m;
  Loop l;
  sc.reset(5, 3);
  std::atomic<u64> rebases{0};
  auto writer = [&](Ctl& c) {
    c.ready.fetch_add(1);
    while (!c.go.load(std::memory_order_acquire)) _mm_pause();
    const int64_t gap = qpf() / 100000;  // 10 us
    bool flip = false;
    while (!c.stop.load(rlx)) {
      if (alt) Sleep(1); else spin_ticks(gap);
      flip = !flip;
      if (alt && flip) sc.set_ratio(1, 1, kind);
      else sc.set_ratio(5, 3, kind);
      rebases.fetch_add(1, rlx);
    }
  };
  auto fe = [&] { return sc.read<false>(); };
  auto fl = [&] { return sc.read<true>(); };
  if (late) run_pair(fl, writer, dur, &l);
  else run_pair(fe, writer, dur, &l);
  m.reads = l.calls; m.back = l.back; m.maxstep = l.maxstep;
  m.rebases = rebases.load(); m.fb = sc.fallbacks.load();
  return m;
}

// Check (a): deterministic. Base hb=0, gb=0, ratio 5/3. The writer samples hw
// and rebases; a stale reader that validated the old snapshot but sampled
// q >= hw returns old(q). Step-back if old(q) > new(q).
static void check_a_enum() {
  struct Agg { int pairs = 0, backs = 0; u64 maxb = 0; } a[4];
  auto oldv = [](u64 q) { return scale(q, 5, 3); };
  for (u64 hw = 1; hw <= 30; ++hw) {
    const u64 k = (hw + 2) / 3;
    const u64 bh[2] = {hw, 3 * k}, bg[2] = {oldv(hw), 5 * k};  // naive, aligned
    for (u64 q = hw; q <= hw + 10; ++q)
      for (int dec = 0; dec < 2; ++dec)
        for (int al = 0; al < 2; ++al) {
          const u64 nn = dec ? 1 : 5, nd = dec ? 1 : 3;
          const u64 nv = bg[al] + scale(q > bh[al] ? q - bh[al] : 0, nn, nd), ov = oldv(q);
          Agg& g = a[dec * 2 + al];
          ++g.pairs;
          if (ov > nv) { ++g.backs; g.maxb = std::max(g.maxb, ov - nv); }
        }
  }
  const char* nm[4] = {"same ratio 5/3, naive rebase  ", "same ratio 5/3, aligned rebase",
                       "5/3 -> 1/1,     naive rebase  ", "5/3 -> 1/1,     aligned rebase"};
  printf("CHECK(a) enumeration: hb=0 gb=0 ratio 5/3, writer host sample hw=1..30, stale read at q in [hw,hw+10]\n");
  for (int i = 0; i < 4; ++i)
    printf("  %s: step-backs %3d/%d pairs, max %llu tick(s)\n", nm[i], a[i].backs, a[i].pairs,
           (unsigned long long)a[i].maxb);
  printf("  example hw=1 q=2: old=%llu naive_new=%llu aligned_new=%llu (G0'=5 at h0'=3; q<h0' clamps to G0')\n",
         (unsigned long long)oldv(2), (unsigned long long)(oldv(1) + scale(1, 5, 3)), 5ull);
  printf("  stale reads at q<=hw never step back (new >= G0' >= old(hw)); a ratio DEcrease steps back for both.\n");
}

int main(int argc, char** argv) {
  const int runs = argc > 1 ? atoi(argv[1]) : 5;
  bench_a::print_machine_state("start");
  printf("QPF=%lld Hz, runs=%d, threads<=2\n", (long long)qpf(), runs);
  check_a_enum();
  fflush(stdout);

  static OldClock oc;
  static SeqClock sc;
  const Cfg cfgs[] = {
      {"QPC only     1T", 0, 1, 1, 1}, {"QPC only     2T", 0, 1, 1, 2},
      {"OLD 1/1      1T", 1, 1, 1, 1}, {"NEW 1/1      1T", 2, 1, 1, 1},
      {"OLD 5/3      1T", 1, 5, 3, 1}, {"NEW 5/3      1T", 2, 5, 3, 1},
      {"OLD 1/1      2T", 1, 1, 1, 2}, {"NEW 1/1      2T", 2, 1, 1, 2},
      {"OLD 5/3      2T", 1, 5, 3, 2}, {"NEW 5/3      2T", 2, 5, 3, 2},
      {"OLD 5/1(rt)  2T", 1, 5, 1, 2},
  };
  constexpr int N = sizeof(cfgs) / sizeof(cfgs[0]);
  struct MonoCfg { const char* name; Rebase kind; bool alt, late; };
  const MonoCfg mcfgs[] = {
      {"alt 5/3<->1/1 ~1ms, SDK reader, naive(SDK) rebase", kNaive, true, false},
      {"alt 5/3<->1/1 ~1ms, SDK reader, aligned rebase   ", kAligned, true, false},
      {"5/3 every ~10us, late-QPC reader, naive rebase   ", kNaive, false, true},
      {"5/3 every ~10us, late-QPC reader, aligned rebase ", kAligned, false, true},
      {"5/3 every ~10us, SDK reader, naive(SDK) rebase   ", kNaive, false, false},
      {"5/3 every ~10us, SDK reader, naive+mfence rebase ", kNaiveMfence, false, false},
  };
  constexpr int M = sizeof(mcfgs) / sizeof(mcfgs[0]);
  std::vector<std::vector<Res>> res(N);
  std::vector<std::vector<Mono>> mres(M);
  const int64_t dur = qpf() / 10;          // 100 ms per ns/call config
  const int64_t mdur = qpf() * 25 / 100;   // 250 ms per monotonic config

  for (int r = 0; r < runs; ++r) {
    printf("--- run %d ---\n", r + 1);
    for (int i = 0; i < N; ++i) {
      const int c = (i + r * 3) % N;
      Res x = run_cfg(cfgs[c], oc, sc, dur);
      res[c].push_back(x);
      printf("  %s  T1 %7.1f ns/call", cfgs[c].name, x.l[0].ns);
      if (cfgs[c].threads == 2) printf("  T2 %7.1f", x.l[1].ns); else printf("           ");
      if (cfgs[c].var) printf("  drift %.4f", x.drift);
      printf("  back %llu fb %llu\n", (unsigned long long)(x.l[0].back + x.l[1].back), (unsigned long long)x.fb);
    }
    timeBeginPeriod(1);
    for (int i = 0; i < M; ++i) {
      const int c = (i + r) % M;
      Mono m = run_mono(sc, mcfgs[c].kind, mcfgs[c].alt, mcfgs[c].late, mdur);
      mres[c].push_back(m);
      printf("  MONO %s: reads %llu rebases %llu step-backs %llu max %llu fb %llu\n", mcfgs[c].name,
             (unsigned long long)m.reads, (unsigned long long)m.rebases, (unsigned long long)m.back,
             (unsigned long long)m.maxstep, (unsigned long long)m.fb);
    }
    timeEndPeriod(1);
    fflush(stdout);
  }

  printf("\nSUMMARY ns/call (median of %d runs [min..max]); drift = guest elapsed / (host elapsed * ratio)\n", runs);
  printf("  %-15s | %-24s | %-24s | %-26s | back | fb\n", "config", "T1 ns/call", "T2 ns/call", "drift");
  for (int c = 0; c < N; ++c) {
    std::vector<double> a, b, d;
    u64 back = 0, fb = 0;
    for (auto& x : res[c]) {
      a.push_back(x.l[0].ns);
      if (cfgs[c].threads == 2) b.push_back(x.l[1].ns);
      if (cfgs[c].var) d.push_back(x.drift);
      back += x.l[0].back + x.l[1].back;
      fb += x.fb;
    }
    char sb[64] = "-", sd[64] = "-";
    if (!b.empty()) snprintf(sb, sizeof sb, "%7.1f [%.1f..%.1f]", median(b), vmin(b), vmax(b));
    if (!d.empty()) snprintf(sd, sizeof sd, "%.4f [%.4f..%.4f]", median(d), vmin(d), vmax(d));
    printf("  %-15s | %7.1f [%.1f..%.1f] | %-24s | %-26s | %4llu | %llu\n", cfgs[c].name, median(a), vmin(a),
           vmax(a), sb, sd, (unsigned long long)back, (unsigned long long)fb);
  }
  printf("\nSUMMARY monotonicity (T1 reads while T2 rebases; per-run step-backs listed)\n");
  for (int c = 0; c < M; ++c) {
    std::vector<double> rd, rb;
    u64 tot = 0, mx = 0, fb = 0;
    char list[128] = "";
    for (auto& m : mres[c]) {
      rd.push_back(double(m.reads)); rb.push_back(double(m.rebases));
      tot += m.back; mx = std::max(mx, m.maxstep); fb += m.fb;
      char t[24];
      snprintf(t, sizeof t, "%llu ", (unsigned long long)m.back);
      strncat_s(list, t, _TRUNCATE);
    }
    printf("  %s: reads/run %.0f, rebases/run %.0f, step-backs total %llu (%s), max step %llu, fallbacks %llu\n",
           mcfgs[c].name, median(rd), median(rb), (unsigned long long)tot, list, (unsigned long long)mx,
           (unsigned long long)fb);
  }
  bench_a::print_machine_state("end");
  return 0;
}
