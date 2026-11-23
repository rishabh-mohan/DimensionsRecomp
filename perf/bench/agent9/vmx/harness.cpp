// harness.cpp - VMX fallback proof, step 2 (values).
//
// gen_out/kernels.inc (written by gen.exe) holds, for every op and operand pattern, the statements
// the ORIGINAL emitter printed (k_*_old), the NEW emitter's output with vmx_vector_fallbacks on
// (k_*_new) and the distinct-operand SSE text renamed to the pattern's registers (k_*_sse). Each
// kernel is a standalone function over the real PPCContext, like generated code.
//
// Every kernel triple gets the same inputs, and the harness counts:
//   lanes  output lanes (of v1, v2 and v3, so every register a pattern touches) where new != old
//   sat    cases where vscr_sat differs between old and new, or where either one changed it
//   ctx    memcmp of the whole old and new PPCContext after the run (must be identical)
//   ref    cases where vD differs from the ISA result (host lane order; SAT is not modeled
//          because no emitter writes vscr_sat today), for old / new / sse
// Inputs: every pair of 32-bit special values in every lane (32-bit ops), every byte x count pair
// in every lane (vsrb, vsrab), every halfword in every lane (vpkuhus), then random vectors.
// Usage: harness.exe [random_distinct=10000000] [random_aliased=2000000] [bench_iters=20000000]
// Exit code 1 on any old/new difference or any unexpected reference mismatch.

#include <rex/ppc/context.h>
#include <rex/ppc/intrinsics.h>

#include <algorithm>
#include <bit>
#include <chrono>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string_view>
#include <vector>

#define REX_KERNEL(name) \
  extern "C" __attribute__((noinline)) void name([[maybe_unused]] PPCContext& __restrict ctx)
using KernelFn = void (*)(PPCContext&);
struct KernelInfo {
  const char* op;
  const char* pat;
  int d, a, b;
  KernelFn old_fn, new_fn, sse_fn;
};
#include "gen_out/kernels.inc"

namespace {

uint64_t g_rng = 0x243F6A8885A308D3ull;  // splitmix64, fixed seed
inline uint64_t next64() {
  uint64_t z = (g_rng += 0x9E3779B97F4A7C15ull);
  z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
  z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
  return z ^ (z >> 31);
}

enum class Op { vsubsws, vsraw, vsrw, vrlw, vsrb, vsrab, vpkuhus, vpkuwus };
Op op_of(std::string_view n) {
  if (n == "vsubsws") return Op::vsubsws;
  if (n == "vsraw") return Op::vsraw;
  if (n == "vsrw") return Op::vsrw;
  if (n == "vrlw") return Op::vrlw;
  if (n == "vsrb") return Op::vsrb;
  if (n == "vsrab") return Op::vsrab;
  if (n == "vpkuhus") return Op::vpkuhus;
  if (n == "vpkuwus") return Op::vpkuwus;
  std::fprintf(stderr, "unknown op %.*s\n", int(n.size()), n.data());
  std::exit(2);
}
enum class Kind { W32, H16, B8 };
Kind kind_of(Op op) {
  if (op == Op::vsrb || op == Op::vsrab) return Kind::B8;
  if (op == Op::vpkuhus) return Kind::H16;
  return Kind::W32;
}
int out_lane_bytes(Op op) {
  if (op == Op::vsrb || op == Op::vsrab || op == Op::vpkuhus) return 1;
  if (op == Op::vpkuwus) return 2;
  return 4;
}

// ISA result in host lane order (host lane k of a 32-bit vector is guest word 3 - k; lane-wise
// ops are unaffected, and the packs put vB in the low host lanes).
PPCVRegister reference(Op op, const PPCVRegister& a, const PPCVRegister& b) {
  PPCVRegister r{};
  switch (op) {
    case Op::vsubsws:
      for (int k = 0; k < 4; ++k)
        r.s32[k] = int32_t(std::clamp<int64_t>(int64_t(a.s32[k]) - b.s32[k], INT32_MIN, INT32_MAX));
      break;
    case Op::vsraw:
      for (int k = 0; k < 4; ++k) r.s32[k] = a.s32[k] >> (b.u32[k] & 31);
      break;
    case Op::vsrw:
      for (int k = 0; k < 4; ++k) r.u32[k] = a.u32[k] >> (b.u32[k] & 31);
      break;
    case Op::vrlw:
      for (int k = 0; k < 4; ++k) r.u32[k] = std::rotl(a.u32[k], int(b.u32[k] & 31));
      break;
    case Op::vsrb:
      for (int k = 0; k < 16; ++k) r.u8[k] = uint8_t(a.u8[k] >> (b.u8[k] & 7));
      break;
    case Op::vsrab:
      for (int k = 0; k < 16; ++k) r.s8[k] = int8_t(a.s8[k] >> (b.u8[k] & 7));
      break;
    case Op::vpkuhus:
      for (int k = 0; k < 8; ++k) {
        r.u8[k] = uint8_t(std::min<uint32_t>(b.u16[k], 0xFF));
        r.u8[8 + k] = uint8_t(std::min<uint32_t>(a.u16[k], 0xFF));
      }
      break;
    case Op::vpkuwus:
      for (int k = 0; k < 4; ++k) {
        r.u16[k] = uint16_t(std::min<uint32_t>(b.u32[k], 0xFFFF));
        r.u16[4 + k] = uint16_t(std::min<uint32_t>(a.u32[k], 0xFFFF));
      }
      break;
  }
  return r;
}

std::vector<uint32_t> make_specials32() {
  std::vector<uint32_t> s = {0x0000007F, 0x00000080, 0x000000FF, 0x00000100, 0x00007FFF,
                             0x00008000, 0x0000FFFE, 0x0000FFFF, 0x00010000, 0x00010001,
                             0x0001FFFF, 0x3FFFFFFF, 0x40000000, 0xBFFFFFFF, 0xC0000000,
                             0xFFFF0000, 0xFFFF7FFF, 0xFFFF8000, 0x00FF00FF, 0xFF00FF00,
                             0x55555555, 0xAAAAAAAA, 0x12345678, 0x87654321, 0xDEADBEEF,
                             0x80008000, 0x7FFF7FFF, 0x0000001F, 0xFFFFFFE0, 0x7FFFFFE0};
  for (uint32_t k = 0; k < 64; ++k) {
    s.push_back(k);                     // 0..63: every shift count, and 32/33/63
    s.push_back(uint32_t(-int64_t(k)));  // -k
    s.push_back(0x7FFFFFFFu - k);       // INT_MAX - k
    s.push_back(0x80000000u + k);       // INT_MIN + k
  }
  for (uint32_t c = 0; c < 32; ++c) {
    s.push_back(0xFFFFFF00u | c);  // counts with junk in the other bits
    s.push_back(0x12345600u | c);
    s.push_back(0xABCDEF00u | (c << 3) | 7);  // bits 3..7 junk, so & 0x1F matters
  }
  std::sort(s.begin(), s.end());
  s.erase(std::unique(s.begin(), s.end()), s.end());
  return s;
}
const std::vector<uint32_t> kS32 = make_specials32();
const uint16_t kS16[] = {0x0000, 0x0001, 0x007F, 0x0080, 0x00FE, 0x00FF, 0x0100,
                         0x0101, 0x7FFF, 0x8000, 0x8001, 0xFFFE, 0xFFFF};

uint32_t rand32() {
  const uint64_t r = next64();
  switch (r & 3) {
    case 0:
    case 1:
      return uint32_t(r >> 32);
    case 2:
      return kS32[(r >> 8) % kS32.size()];
    default:
      return kS32[(r >> 8) % kS32.size()] + uint32_t(int32_t((r >> 40) & 7) - 3);
  }
}
void rand_lanes(Kind kind, PPCVRegister& v) {
  switch (kind) {
    case Kind::W32:
      for (auto& w : v.u32) w = rand32();
      break;
    case Kind::H16:
      for (auto& h : v.u16) {
        const uint64_t r = next64();
        h = (r & 3) == 3 ? kS16[(r >> 8) % std::size(kS16)] : uint16_t(r >> 32);
      }
      break;
    case Kind::B8:
      v.u64[0] = next64();
      v.u64[1] = next64();
      break;
  }
}

struct Stats {
  uint64_t cases = 0, lanes = 0, sat = 0, ref_old = 0, ref_new = 0, ref_sse = 0;
  bool ctx_equal = true;
};

PPCVRegister& vreg(PPCContext& c, int n) { return n == 1 ? c.v1 : n == 2 ? c.v2 : c.v3; }

PPCContext* g_tmpl;
PPCContext* g_old;
PPCContext* g_new;
PPCContext* g_sse;

// v1 = A, v2 = B0, v3 = D0 in all three contexts. With vA == vB the instruction's B is A.
void run_case(const KernelInfo& k, Op op, int lane_bytes, const PPCVRegister& A,
              const PPCVRegister& B0, const PPCVRegister& D0, uint8_t sat0, Stats& st) {
  for (PPCContext* c : {g_old, g_new, g_sse}) {
    c->v1 = A;
    c->v2 = B0;
    c->v3 = D0;
    c->vscr_sat = sat0;
  }
  k.old_fn(*g_old);
  k.new_fn(*g_new);
  k.sse_fn(*g_sse);
  ++st.cases;
  for (int r = 1; r <= 3; ++r) {
    const uint8_t* o = vreg(*g_old, r).u8;
    const uint8_t* n = vreg(*g_new, r).u8;
    for (int l = 0; l < 16; l += lane_bytes) st.lanes += std::memcmp(o + l, n + l, lane_bytes) != 0;
  }
  st.sat += g_old->vscr_sat != g_new->vscr_sat || g_old->vscr_sat != sat0;
  const PPCVRegister expect = reference(op, A, k.b == k.a ? A : B0);
  st.ref_old += std::memcmp(vreg(*g_old, k.d).u8, expect.u8, 16) != 0;
  st.ref_new += std::memcmp(vreg(*g_new, k.d).u8, expect.u8, 16) != 0;
  st.ref_sse += std::memcmp(vreg(*g_sse, k.d).u8, expect.u8, 16) != 0;
}

Stats run_kernel(const KernelInfo& k, uint64_t n_random) {
  Stats st;
  const Op op = op_of(k.op);
  const Kind kind = kind_of(op);
  const int lb = out_lane_bytes(op);
  for (PPCContext* c : {g_old, g_new, g_sse}) std::memcpy(c, g_tmpl, sizeof(PPCContext));
  PPCVRegister A{}, B{}, D{};
  uint8_t sat = 0;
  auto rnd = [](PPCVRegister& v) {
    v.u64[0] = next64();
    v.u64[1] = next64();
  };
  if (kind == Kind::W32) {
    // Lane l of A walks the list from i + l and lane l of B from j + 7l, so as i and j cover
    // the list every lane sees every (a, b) pair of special values exactly once.
    const size_t n = kS32.size();
    for (size_t i = 0; i < n; ++i)
      for (size_t j = 0; j < n; ++j) {
        for (int l = 0; l < 4; ++l) {
          A.u32[l] = kS32[(i + l) % n];
          B.u32[l] = kS32[(j + 7 * l) % n];
        }
        rnd(D);
        run_case(k, op, lb, A, B, D, sat ^= 1, st);
      }
  } else if (kind == Kind::B8) {
    for (int i = 0; i < 256; ++i)
      for (int j = 0; j < 256; ++j) {
        for (int l = 0; l < 16; ++l) {
          A.u8[l] = uint8_t(i + 17 * l);
          B.u8[l] = uint8_t(j + 29 * l);
        }
        rnd(D);
        run_case(k, op, lb, A, B, D, sat ^= 1, st);
      }
  } else {
    for (uint32_t i = 0; i < 65536; ++i) {
      for (int l = 0; l < 8; ++l) {
        A.u16[l] = uint16_t(i + 0x1234u * l);
        B.u16[l] = uint16_t(7u * i + 0x0F0Fu * l + 0x8000u);
      }
      rnd(D);
      run_case(k, op, lb, A, B, D, sat ^= 1, st);
    }
  }
  for (uint64_t c = 0; c < n_random; ++c) {
    rand_lanes(kind, A);
    rand_lanes(kind, B);
    rnd(D);
    run_case(k, op, lb, A, B, D, sat ^= 1, st);
  }
  st.ctx_equal = std::memcmp(g_old, g_new, sizeof(PPCContext)) == 0;
  return st;
}

double bench_ns(KernelFn fn, uint64_t iters) {
  PPCContext& c = *g_old;
  std::memcpy(&c, g_tmpl, sizeof(PPCContext));
  rand_lanes(Kind::W32, c.v1);
  rand_lanes(Kind::W32, c.v2);
  const auto t0 = std::chrono::steady_clock::now();
  for (uint64_t i = 0; i < iters; ++i) {
    fn(c);
    c.v1.u32[0] ^= uint32_t(i);  // keep the inputs moving
  }
  const auto t1 = std::chrono::steady_clock::now();
  return std::chrono::duration<double, std::nano>(t1 - t0).count() / double(iters);
}

}  // namespace

int main(int argc, char** argv) {
  const uint64_t n_distinct = argc > 1 ? std::strtoull(argv[1], nullptr, 10) : 10000000ull;
  const uint64_t n_aliased = argc > 2 ? std::strtoull(argv[2], nullptr, 10) : 2000000ull;
  const uint64_t n_bench = argc > 3 ? std::strtoull(argv[3], nullptr, 10) : 20000000ull;

#if defined(__AVX2__)
  const int avx2 = 1;
#else
  const int avx2 = 0;
#endif
#if defined(SIMDE_X86_AVX2_NATIVE)
  const int simde_avx2 = 1;
#else
  const int simde_avx2 = 0;
#endif
#if defined(SIMDE_X86_SSE4_1_NATIVE)
  const int simde_sse41 = 1;
#else
  const int simde_sse41 = 0;
#endif
  std::printf("config: __AVX2__=%d SIMDE_X86_AVX2_NATIVE=%d SIMDE_X86_SSE4_1_NATIVE=%d clang %s\n",
              avx2, simde_avx2, simde_sse41, __clang_version__);
  std::printf("random cases: %" PRIu64 " per distinct-operand kernel, %" PRIu64
              " per aliased kernel; %zu special 32-bit values\n",
              n_distinct, n_aliased, kS32.size());

  g_tmpl = new PPCContext{};
  g_old = new PPCContext{};
  g_new = new PPCContext{};
  g_sse = new PPCContext{};
  {
    // Fill the template with a byte pattern so stray writes anywhere in the context show up.
    auto* p = reinterpret_cast<uint8_t*>(g_tmpl);
    for (size_t i = 0; i < sizeof(PPCContext); ++i) p[i] = uint8_t(0xA5 ^ (i * 31));
  }

  std::printf("%-8s %-9s %10s %6s %4s %4s %8s %8s %8s\n", "op", "pattern", "cases", "lanes",
              "sat", "ctx", "ref_old", "ref_new", "ref_sse");
  int failures = 0;
  uint64_t total_cases = 0, total_lanes = 0, total_sat = 0;
  for (const KernelInfo& k : kKernels) {
    const bool distinct = std::string_view(k.pat) == "distinct";
    const Stats st = run_kernel(k, distinct ? n_distinct : n_aliased);
    const bool vpku_alias = std::string_view(k.op).starts_with("vpku") && (k.d == k.a || k.d == k.b);
    // The scalar vpku*us text is wrong when vD aliases vA or vB (old, and new, which keeps it
    // there); everything else must match the ISA.
    const bool bad = st.lanes || st.sat || !st.ctx_equal || st.ref_sse ||
                     (!vpku_alias && (st.ref_old || st.ref_new));
    failures += bad;
    total_cases += st.cases;
    total_lanes += st.lanes;
    total_sat += st.sat;
    std::printf("%-8s %-9s %10" PRIu64 " %6" PRIu64 " %4" PRIu64 " %4s %8" PRIu64 " %8" PRIu64
                " %8" PRIu64 "%s%s\n",
                k.op, k.pat, st.cases, st.lanes, st.sat, st.ctx_equal ? "ok" : "DIFF", st.ref_old,
                st.ref_new, st.ref_sse, vpku_alias ? "  (scalar text kept: old bug)" : "",
                bad ? "  <-- FAIL" : "");
  }
  std::printf("TOTAL cases %" PRIu64 ", old/new lane mismatches %" PRIu64
              ", sat mismatches %" PRIu64 ", failing kernels %d\n",
              total_cases, total_lanes, total_sat, failures);

  if (n_bench) {
    std::printf("\nrough timing, %" PRIu64 " calls each (shared machine, call overhead included)\n",
                n_bench);
    std::printf("%-8s %9s %9s %7s\n", "op", "old ns", "new ns", "speedup");
    for (const KernelInfo& k : kKernels) {
      if (std::string_view(k.pat) != "distinct") continue;
      const double o = bench_ns(k.old_fn, n_bench);
      const double n = bench_ns(k.new_fn, n_bench);
      std::printf("%-8s %9.2f %9.2f %6.2fx\n", k.op, o, n, o / n);
    }
  }
  return failures ? 1 : 0;
}
