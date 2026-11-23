// Agent 10 (task #9): equivalence tests for the guest SIMD helpers. Every implementation (old_ppc = pin
// copy, rex::ppc = current SDK header, cand/alt = candidates) is checked against the scalar PPC reference
// in ppc_ref.h. Usage: test_intrinsics [--quick] [--threads N<=2] [--kat <tests/ppc/asm dir>]
#include <immintrin.h>

#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <thread>
#include <vector>

#include "kat.h"

static int g_threads = 2;
static bool g_quick = false;
static std::atomic<long long> g_fail{0};
template <class... Is> struct Impls {};
#if defined(AGENT10_MUTANTS)  // test-the-test: every group below must report FAILED
struct MutImpl : CandImpl {
  static constexpr const char* name = "MUTANT";
  static m128i sllv16(m128i a, m128i c) { return cand::sllv_epi16(a, simde_mm_and_si128(c, simde_mm_set1_epi16(31))); }
  static m128i srlv16(m128i a, m128i c) { return cand::srlv_epi16(a, simde_mm_max_epu16(c, simde_mm_set1_epi16(1))); }
  static m128i srav16(m128i a, m128i c) { return cand::srlv_epi16(a, c); }
  static m128i sllv8(m128i a, m128i c) { return cand::sllv_epi8(a, simde_mm_min_epu8(c, simde_mm_set1_epi8(7))); }
  static m128i vslo(m128i a, m128i b) { return simde_mm_shuffle_epi8(cand::vslo(a, b), simde_mm_setr_epi8(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 14)); }
  static m128i vsro(m128i a, m128i b) { return cand::vslo(a, b); }
  static m128i vsl(m128i a, m128i b) { return cand::vsl(a, simde_mm_slli_si128(b, 15)); }
  static m128i perm(m128i a, m128i b, m128i c) { return cand::perm(b, a, c); }
  static m128i vctuxs(m128 a) { return simde_mm_cvttps_epi32(simde_mm_max_ps(a, simde_mm_setzero_ps())); }
};
using All = Impls<MutImpl>;
#else
using All = Impls<OldImpl, CurImpl, CandImpl, AltImpl>;
#endif

template <class F> static void par(uint64_t n, F f) {
  std::vector<std::thread> ts;
  for (int t = 0; t < g_threads; t++)
    ts.emplace_back([=] { f(n * t / g_threads, n * (t + 1) / g_threads, t); });
  for (auto& t : ts) t.join();
}
static bool eq(m128i x, m128i y) { return simde_mm_movemask_epi8(simde_mm_cmpeq_epi8(x, y)) == 0xFFFF; }
static void report(const char* impl, const char* what, std::initializer_list<m128i> in, m128i got, m128i want) {
  if (g_fail.fetch_add(1) >= 25) return;
  char buf[512]; int p = snprintf(buf, sizeof buf, "  FAIL [%s] %s in:", impl, what);
  auto hex = [&](m128i v) { ref::V x = st(v); p += snprintf(buf + p, sizeof buf - p, " "); for (int i = 15; i >= 0; i--) p += snprintf(buf + p, sizeof buf - p, "%02X", x.b[i]); };
  for (m128i v : in) hex(v);
  p += snprintf(buf + p, sizeof buf - p, " got"); hex(got);
  p += snprintf(buf + p, sizeof buf - p, " want"); hex(want);
  printf("%s (x86 bytes 15..0)\n", buf);
}
template <class I> static void chk(const char* what, m128i got, m128i want, std::initializer_list<m128i> in) {
  if (!eq(got, want)) report(I::name, what, in, got, want);
}
#define CHK(I, what, expr, want, ...) chk<I>(what, (expr), (want), {__VA_ARGS__})
template <class T> static m128i ldv(const T* p) { return simde_mm_loadu_si128(reinterpret_cast<const m128i*>(p)); }

//--- 16-bit helper shifts: every (a, count) pair, lanes carry different counts ------------------
template <class I> static void chk16(m128i a, m128i c, m128i wl, m128i wr, m128i wa) {
  CHK(I, "sllv_epi16", I::sllv16(a, c), wl, a, c);
  CHK(I, "srlv_epi16", I::srlv16(a, c), wr, a, c);
  CHK(I, "srav_epi16", I::srav16(a, c), wa, a, c);
}
template <class... Is> static void test_shift16(Impls<Is...>) {
  uint64_t n = g_quick ? (8192ull << 7) : (1ull << 29);  // full: 2^32 (a, c) pairs
  par(n, [](uint64_t b, uint64_t e, int) {
    alignas(16) uint16_t a[8], c[8], rl[8], rr[8], ra[8];
    for (uint64_t j = b; j < e; j++) {
      uint32_t ab = uint32_t(j & 8191), cb = uint32_t(j >> 13);
      if (g_quick && cb >= 64) cb = (cb * 1021u) & 0xFFFF;
      for (int k = 0; k < 8; k++) {
        a[k] = uint16_t(ab * 8 + k); c[k] = uint16_t(cb + 31 * k);
        rl[k] = ref::sllv16(a[k], c[k]); rr[k] = ref::srlv16(a[k], c[k]); ra[k] = ref::srav16(a[k], c[k]);
      }
      (chk16<Is>(ldv(a), ldv(c), ldv(rl), ldv(rr), ldv(ra)), ...);
    }
  });
  ref::Rng rng(16);  // random vectors, counts biased to the 0..31 range
  for (int i = 0; i < (g_quick ? 100000 : 10000000); i++) {
    ref::V a = rng.vec(), c = rng.vec(), rl, rr, ra;
    for (int k = 0; k < 8; k++) {
      uint16_t ck = ref::h(c, k); if (k & 1) ck &= 31; ref::seth(c, k, ck);
      ref::seth(rl, k, ref::sllv16(ref::h(a, k), ck)); ref::seth(rr, k, ref::srlv16(ref::h(a, k), ck)); ref::seth(ra, k, ref::srav16(ref::h(a, k), ck));
    }
    (chk16<Is>(ld(a), ld(c), ld(rl), ld(rr), ld(ra)), ...);
  }
}

//--- sllv_epi8: all 2^16 (a, count) pairs + random ---------------------------------------------
template <class... Is> static void test_shift8(Impls<Is...>) {
  alignas(16) uint8_t a[16], c[16], r[16];
  for (uint32_t j = 0; j < 4096; j++) {
    for (int k = 0; k < 16; k++) { a[k] = uint8_t(16 * (j & 15) + k); c[k] = uint8_t((j >> 4) + 37 * k); r[k] = ref::sllv8(a[k], c[k]); }
    (CHK(Is, "sllv_epi8", Is::sllv8(ldv(a), ldv(c)), ldv(r), ldv(a), ldv(c)), ...);
  }
  ref::Rng rng(8);
  for (int i = 0; i < (g_quick ? 100000 : 1000000); i++) {
    ref::V va = rng.vec(), vc = rng.vec(), vr;
    for (int k = 0; k < 16; k++) { if (k & 1) vc.b[k] &= 15; vr.b[k] = ref::sllv8(va.b[k], vc.b[k]); }
    (CHK(Is, "sllv_epi8", Is::sllv8(ld(va), ld(vc)), ld(vr), ld(va), ld(vc)), ...);
  }
}

//--- Emitted instruction forms (masked counts): all a values x all low count bits ---------------
template <class I> static void chk_emit16(m128i a, m128i b, m128i w1, m128i w2, m128i w3, m128i w4) {
  CHK(I, "vslh(emitted)", e_vslh<I>(a, b), w1, a, b);
  CHK(I, "vsrh(emitted)", e_vsrh<I>(a, b), w2, a, b);
  CHK(I, "vsrah(emitted)", e_vsrah<I>(a, b), w3, a, b);
  CHK(I, "vrlh(emitted)", e_vrlh<I>(a, b), w4, a, b);
}
template <class... Is> static void test_emitted(Impls<Is...>) {
  alignas(16) uint16_t a[8], b[8], w1[8], w2[8], w3[8], w4[8];
  for (uint32_t j = 0; j < 8192u * 64; j++) {
    for (int k = 0; k < 8; k++) {
      a[k] = uint16_t((j & 8191) * 8 + k);
      b[k] = uint16_t((((j >> 13) + 5 * k) & 63) | (((j * 0x9E37u) + k * 0x3Bu) << 6));
      w1[k] = ref::vslh(a[k], b[k]); w2[k] = ref::vsrh(a[k], b[k]); w3[k] = ref::vsrah(a[k], b[k]); w4[k] = ref::vrlh(a[k], b[k]);
    }
    (chk_emit16<Is>(ldv(a), ldv(b), ldv(w1), ldv(w2), ldv(w3), ldv(w4)), ...);
  }
  alignas(16) uint8_t x[16], y[16], r[16];
  for (uint32_t j = 0; j < 4096; j++) {
    for (int k = 0; k < 16; k++) { x[k] = uint8_t(16 * (j & 15) + k); y[k] = uint8_t((j >> 4) + 37 * k); r[k] = ref::vslb(x[k], y[k]); }
    (CHK(Is, "vslb(emitted)", e_vslb<Is>(ldv(x), ldv(y)), ldv(r), ldv(x), ldv(y)), ...);
  }
}

//--- Whole-register shifts: every count byte x random data -------------------------------------
template <class I> static void chk_oct(const ref::V& a, const ref::V& b, const ref::V& bu) {
  CHK(I, "vslo", I::vslo(ld(a), ld(b)), ld(ref::vslo(a, b)), ld(a), ld(b));
  CHK(I, "vsro", I::vsro(ld(a), ld(b)), ld(ref::vsro(a, b)), ld(a), ld(b));
  CHK(I, "vsr", I::vsr(ld(bu), ld(bu)) , ld(ref::vsr(bu, bu)), ld(bu));
  CHK(I, "vsl(sdk: PPC byte 0)", I::vsl(ld(a), ld(b)), ld(ref::vsl_sdk(a, b)), ld(a), ld(b));
  CHK(I, "vsl(uniform vB = ISA)", I::vsl(ld(a), ld(bu)), ld(ref::vsl_isa(a, bu)), ld(a), ld(bu));
  CHK(I, "vsr(uniform vB)", I::vsr(ld(a), ld(bu)), ld(ref::vsr(a, bu)), ld(a), ld(bu));
}
template <class... Is> static void test_octet(Impls<Is...>) {
  int per = g_quick ? 400 : 40000;
  par(256, [per](uint64_t b0, uint64_t e0, int) {
    for (uint64_t cnt = b0; cnt < e0; cnt++) {
      ref::Rng rng(1000 + cnt);
      for (int i = 0; i < per + 2; i++) {
        ref::V a = rng.vec(), b = rng.vec(), bu;
        if (i == per) for (int k = 0; k < 16; k++) a.b[k] = uint8_t(k);
        if (i == per + 1) memset(a.b, 0xFF, 16);
        b.b[0] = uint8_t(cnt);                 // vslo/vsro/vsr read x86 byte 0 (PPC byte 15)
        if (i & 1) b.b[15] = uint8_t(cnt);     // vsl (SDK) reads x86 byte 15 (PPC byte 0)
        memset(bu.b, int(cnt), 16);
        (chk_oct<Is>(a, b, bu), ...);
      }
    }
  });
}

//--- vperm --------------------------------------------------------------------------------------
template <class... Is> static void test_perm(Impls<Is...>) {
  ref::Rng rng(77);
  auto one = [](const ref::V& a, const ref::V& b, const ref::V& c) {
    m128i w = ld(ref::vperm(a, b, c));
    (CHK(Is, "vperm", Is::perm(ld(a), ld(b), ld(c)), w, ld(a), ld(b), ld(c)), ...);
  };
  for (int i = 0; i < (g_quick ? 100000 : 10000000); i++) one(rng.vec(), rng.vec(), rng.vec());
  for (int lane = 0; lane < 16; lane++)
    for (int v = 0; v < 256; v++)
      for (int r = 0; r < 20; r++) { ref::V c = rng.vec(); c.b[lane] = uint8_t(v); one(rng.vec(), rng.vec(), c); }
}

//--- vctuxs: every float bit pattern, default MXCSR and FTZ|DAZ ---------------------------------
static const uint32_t kFloatEdges[] = {0, 0x80000000, 1, 0x007FFFFF, 0x80000001, 0x807FFFFF, 0x00800000, 0x3F000000,
    0x3F7FFFFF, 0x3F800000, 0xBF800000, 0xBF7FFFFF, 0x4EFFFFFF, 0x4F000000, 0x4F000001, 0x4F7FFFFF, 0x4F800000,
    0x4F800001, 0x7F7FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000, 0x7F800001, 0x7FFFFFFF, 0xFFC00000, 0xFFFFFFFF};
template <class... Is> static void test_vctuxs(Impls<Is...>, unsigned csr_or) {
  uint64_t n = 1ull << 30;
  par(n, [csr_or](uint64_t b, uint64_t e, int) {
    unsigned csr = _mm_getcsr(); _mm_setcsr(csr | csr_or);
    alignas(16) uint32_t x[4], r[4];
    uint64_t step = g_quick ? 4099 : 1;
    for (uint64_t j = b; j < e; j += step) {
      for (int k = 0; k < 4; k++) { x[k] = uint32_t(j * 4 + k); r[k] = ref::vctuxs_bits(x[k]); }
      m128 v = simde_mm_castsi128_ps(ldv(x));
      (CHK(Is, "vctuxs", Is::vctuxs(v), ldv(r), ldv(x)), ...);
    }
    if (b == 0) {  // edge cases and the emitted form with UIMM scaling
      ref::Rng rng(5);
      const int uimms[] = {0, 1, 2, 15, 16, 30, 31};
      for (int u : uimms)
        for (int i = 0; i < (g_quick ? 20000 : 1000000); i++) {
          for (int k = 0; k < 4; k++) {
            uint32_t bits = uint32_t(rng.next());
            if (k == 1) bits = kFloatEdges[rng.next() % (sizeof kFloatEdges / 4)];
            if (k == 2) bits = (bits & 0x807FFFFF) | uint32_t(110 + rng.next() % 50) << 23;  // near the interesting range
            x[k] = bits; r[k] = ref::vctuxs_bits(bits, u);
          }
          m128 v = simde_mm_castsi128_ps(ldv(x));
          (CHK(Is, u ? "vctuxs(emitted, uimm)" : "vctuxs(edges)", e_vctuxs<Is>(v, u), ldv(r), ldv(x)), ...);
        }
    }
    _mm_setcsr(csr);
  });
}

//--- Tables -------------------------------------------------------------------------------------
template <class I> static void test_tables(bool require_align) {
  struct T { const char* n; const uint8_t* p; uint8_t (*f)(int, int); } ts[] = {
      {"VectorMaskL", I::maskL(), ref::mask_l}, {"VectorMaskR", I::maskR(), ref::mask_r},
      {"VectorShiftTableL", I::shiftL(), ref::shift_l}, {"VectorShiftTableR", I::shiftR(), ref::shift_r}};
  for (auto& t : ts) {
    for (int s = 0; s < 16; s++)
      for (int j = 0; j < 16; j++)
        if (t.p[s * 16 + j] != t.f(s, j) && g_fail.fetch_add(1) < 25)
          printf("  FAIL [%s] %s row %d lane %d: %02X want %02X\n", I::name, t.n, s, j, t.p[s * 16 + j], t.f(s, j));
    bool al = (reinterpret_cast<uintptr_t>(t.p) & 15) == 0;
    if (!al) printf("  %s [%s] %s is not 16-byte aligned\n", require_align ? "FAIL" : "note:", I::name, t.n);
    if (!al && require_align) g_fail++;
  }
}

int main(int argc, char** argv) {
  std::vector<std::string> kat;
  bool tables_aligned = false;
  for (int i = 1; i < argc; i++) {
    if (!strcmp(argv[i], "--quick")) g_quick = true;
    else if (!strcmp(argv[i], "--threads") && i + 1 < argc) g_threads = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--require-aligned-tables")) tables_aligned = true;
    else if (!strcmp(argv[i], "--kat") && i + 1 < argc) {
      const char* names[] = {"vslo", "vsro", "vsl", "vsr", "vperm", "vctuxs", "vslb", "vslh", "vsrh", "vsrah", "vrlh", "lvsl", "lvsr"};
      for (auto n : names) kat.push_back(std::string(argv[i + 1]) + "/instr_" + n + ".s");
      i++;
    }
  }
  if (g_threads < 1 || g_threads > 2) g_threads = 2;
  printf("test_intrinsics: %s, %d thread(s), AVX2 candidates %s\n", g_quick ? "quick" : "full", g_threads,
#if defined(CAND_HAVE_AVX2)
         "native");
#else
         "absent");
#endif
  long long total = 0;
  auto run = [&](const char* name, auto fn) {
    auto t0 = std::chrono::steady_clock::now();
    long long before = g_fail.load();
    fn();
    double s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    printf("%-34s %s  (%.1f s)\n", name, g_fail.load() == before ? "ok" : "FAILED", s);
    fflush(stdout);
  };
  run("tables (old, sdk)", [&] { test_tables<OldImpl>(false); test_tables<CurImpl>(tables_aligned); });
  run("sllv/srlv/srav_epi16 (2^32 pairs)", [] { test_shift16(All{}); });
  run("sllv_epi8 (2^16 pairs)", [] { test_shift8(All{}); });
  run("vslb/vslh/vsrh/vsrah/vrlh emitted", [] { test_emitted(All{}); });
  run("vslo/vsro/vsl/vsr", [] { test_octet(All{}); });
  run("vperm", [] { test_perm(All{}); });
  run("vctuxs (2^32, default MXCSR)", [] { test_vctuxs(All{}, 0); });
  run("vctuxs (2^32, FTZ|DAZ)", [] { test_vctuxs(All{}, 0x8040); });
  if (!kat.empty()) {
    run("KAT replay (tests/ppc/asm)", [&] {
      int ran = 0, f = 0;
      f += kat_run<OldImpl>(kat, ran); f += kat_run<CurImpl>(kat, ran); f += kat_run<CandImpl>(kat, ran); f += kat_run<AltImpl>(kat, ran);
      printf("  KAT: %d test runs, %d failed\n", ran, f);
      g_fail += f;
    });
  }
  total = g_fail.load();
  printf("%s: %lld failure(s)\n", total ? "FAILED" : "PASSED", total);
  return total ? 1 : 0;
}
