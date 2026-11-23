// Agent 10 (task #9): microbenchmarks for the guest SIMD helpers, old (pin copy) vs candidates vs the current
// SDK header. Single thread, pinned (--cpu N), FTZ|DAZ like generated code, interleaved implementations,
// median of --reps runs (default 9). Units: TSC ticks per op (relative numbers; compare rows, not machines).
//   thr = independent ops over 512-entry arrays (throughput); lat = dependent chain x = op(x, b[i]) (latency).
// Usage: bench_intrinsics [--reps 9] [--cpu 2] [--fixed]   (--fixed = one constant count/control for all ops)
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <intrin.h>

#include <algorithm>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "impls.h"

static constexpr int N = 512, K = 2000;
alignas(64) static m128i g_a[N], g_b[N], g_out[N];
static m128i g_sink;

template <class Op> static double thr(Op op) {
  uint64_t t0 = __rdtsc();
  for (int r = 0; r < K; r++) {
    // The arrays are internal globals: hand their addresses to the asm so the clobber covers them and the
    // compiler cannot hoist the loop-invariant ops out of the repetition loop or drop the dead stores.
    asm volatile("" : : "r"(g_a), "r"(g_b), "r"(g_out) : "memory");
    for (int i = 0; i < N; i++) g_out[i] = op(g_a[i], g_b[i]);
    asm volatile("" : : "r"(g_out) : "memory");
  }
  return double(__rdtsc() - t0) / (double(N) * K);
}
template <class Op> static double lat(Op op) {
  m128i x = g_a[0];
  uint64_t t0 = __rdtsc();
  for (int r = 0; r < K; r++)
    for (int i = 0; i < N; i++) x = op(x, g_b[i]);
  g_sink = simde_mm_xor_si128(g_sink, x);
  return double(__rdtsc() - t0) / (double(N) * K);
}

struct Row { std::string op, impl; std::vector<double> t, l; };
static std::vector<Row> g_rows;
static Row& row(const char* op, const char* impl) {
  for (auto& r : g_rows) if (r.op == op && r.impl == impl) return r;
  g_rows.push_back({op, impl, {}, {}});
  return g_rows.back();
}
template <class I, class Op> static void meas(const char* op, Op f) {
  Row& r = row(op, I::name);
  r.t.push_back(thr(f));
  r.l.push_back(lat(f));
}

template <class I> static void bench_one() {
  meas<I>("vslh (emitted)", [](m128i a, m128i b) { return e_vslh<I>(a, b); });
  meas<I>("vsrh (emitted)", [](m128i a, m128i b) { return e_vsrh<I>(a, b); });
  meas<I>("vsrah (emitted)", [](m128i a, m128i b) { return e_vsrah<I>(a, b); });
  meas<I>("vrlh (emitted)", [](m128i a, m128i b) { return e_vrlh<I>(a, b); });
  meas<I>("vslb (emitted)", [](m128i a, m128i b) { return e_vslb<I>(a, b); });
  meas<I>("vslo", [](m128i a, m128i b) { return I::vslo(a, b); });
  meas<I>("vsro", [](m128i a, m128i b) { return I::vsro(a, b); });
  meas<I>("vsl", [](m128i a, m128i b) { return I::vsl(a, b); });
  meas<I>("vperm (c = b)", [](m128i a, m128i b) { return I::perm(a, b, b); });
  meas<I>("vctuxs (+xor glue)", [](m128i a, m128i b) { return I::vctuxs(simde_mm_castsi128_ps(simde_mm_xor_si128(a, b))); });
}

static double median(std::vector<double> v) { std::sort(v.begin(), v.end()); return v[v.size() / 2]; }

int main(int argc, char** argv) {
  int reps = 9, cpu = 2;
  bool fixed = false;
  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "--reps") && i + 1 < argc) reps = std::max(5, atoi(argv[++i]));
    else if (!strcmp(argv[i], "--cpu") && i + 1 < argc) cpu = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--fixed")) fixed = true;
  }
  SetThreadAffinityMask(GetCurrentThread(), DWORD_PTR(1) << cpu);
  SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_ABOVE_NORMAL);
  _mm_setcsr(_mm_getcsr() | 0x8040);  // generated code runs vector float ops in flush mode
  ref::Rng rng(42);
  for (int i = 0; i < N; i++) {
    g_a[i] = ld(rng.vec());
    // Data floats: mostly in the vctuxs range of interest (|x| < 2^33), some specials via random bits.
    ref::V b = rng.vec();
    if (fixed) memset(b.b, 0x1B, 16);  // count 3 octets / 3 bits / 11 elements; control byte 0x1B
    g_b[i] = ld(b);
  }
  for (int r = 0; r < reps; r++) {  // interleave implementations inside every repetition
    bench_one<OldImpl>();
    bench_one<CandImpl>();
    bench_one<AltImpl>();
    bench_one<CurImpl>();
  }
  printf("bench_intrinsics: %s counts, %d reps (median), cpu %d, AVX2 candidates %s; TSC ticks/op\n",
         fixed ? "fixed" : "random", reps, cpu,
#if defined(CAND_HAVE_AVX2)
         "native (alt = AVX2 element shifts, LUT vslo/vsro, maxadd vctuxs)");
#else
         "absent (alt = LUT vslo/vsro, maxadd vctuxs)");
#endif
  printf("%-20s %-5s %8s %8s %10s %10s\n", "op", "impl", "thr", "lat", "thr range", "lat range");
  for (auto& r : g_rows) {
    auto [tn, tx] = std::minmax_element(r.t.begin(), r.t.end());
    auto [ln, lx] = std::minmax_element(r.l.begin(), r.l.end());
    printf("%-20s %-5s %8.2f %8.2f %4.2f-%-5.2f %4.2f-%-5.2f\n", r.op.c_str(), r.impl.c_str(), median(r.t), median(r.l), *tn, *tx, *ln, *lx);
  }
  ref::V s = st(g_sink);
  printf("(sink %02X)\n", s.b[0]);
  return 0;
}
