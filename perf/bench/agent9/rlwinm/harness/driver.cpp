// Runs every generated case: old (generic text) vs new (flag-on text) on the full
// 64-bit registers, plus old vs the independent reference model (refmodel.h).
#include <cstdint>
#include <cstdio>
#include <vector>

#include "refmodel.h"
#include "tables.h"
#include "types.h"

static uint64_t g_seed = 0x243F6A8885A308D3ull;
static uint64_t rnd() {  // splitmix64
  uint64_t z = (g_seed += 0x9E3779B97F4A7C15ull);
  z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
  z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
  return z ^ (z >> 31);
}

struct Stats {
  uint64_t evals = 0, newVsOld = 0, oldVsRef = 0, clobber = 0;
};
static int g_printed = 0;
static void bad(const char* what, const char* insn, int sh, int mb, int me, uint64_t ra,
                uint64_t rs, uint64_t rb, uint64_t got, uint64_t want) {
  if (g_printed++ < 10)
    std::printf("MISMATCH %s %s sh/rb=%d mb=%d me=%d ra=%016llX rs=%016llX rb=%016llX got=%016llX "
                "want=%016llX\n",
                what, insn, sh, mb, me, (unsigned long long)ra, (unsigned long long)rs,
                (unsigned long long)rb, (unsigned long long)got, (unsigned long long)want);
}

static std::vector<uint64_t> specials() {
  return {0,
          ~0ull,
          0x80000000ull,
          0x00000000FFFFFFFFull,
          0xFFFFFFFF00000000ull,
          0x0123456789ABCDEFull,
          0xFEDCBA9876543210ull,
          0xAAAAAAAAAAAAAAAAull,
          0x5555555555555555ull,
          0x8000000080000000ull,
          0x7FFFFFFF7FFFFFFFull,
          1,
          0x80000001ull,
          0xFFFFFFFF7FFFFFFFull,
          0x12345678ull};
}
static std::vector<uint64_t> inputs(int randoms) {
  std::vector<uint64_t> v = specials();
  for (int i = 0; i < 64; ++i)
    v.push_back(1ull << i);  // walking 1
  for (int i = 0; i < 64; ++i)
    v.push_back(~(1ull << i));  // walking 0
  for (int i = 0; i < randoms; ++i)
    v.push_back(rnd());  // random, garbage in the high word
  return v;
}

// One evaluation: run old and new on identical copies, compare with each other and the model.
static void check2(Stats& st, const char* insn, const Case2& c, uint64_t want, uint64_t ra,
                   uint64_t rs, bool alias) {
  ++st.evals;
  Reg a0, s0, a1, s1;
  a0.u64 = a1.u64 = ra;
  s0.u64 = s1.u64 = rs;
  if (alias) {
    c.oldf(a0, a0);
    c.newf(a1, a1);
  } else {
    c.oldf(a0, s0);
    c.newf(a1, s1);
    if (s0.u64 != rs || s1.u64 != rs) {
      ++st.clobber;
      bad("rS-clobbered", insn, c.sh, c.mb, c.me, ra, rs, 0, s1.u64, rs);
    }
  }
  if (a1.u64 != a0.u64) {
    ++st.newVsOld;
    bad("new!=old", insn, c.sh, c.mb, c.me, ra, rs, 0, a1.u64, a0.u64);
  }
  if (a0.u64 != want) {
    ++st.oldVsRef;
    bad("old!=ref", insn, c.sh, c.mb, c.me, ra, rs, 0, a0.u64, want);
  }
}

static std::vector<const Case2*> collect(const Case2* const* parts) {
  std::vector<const Case2*> all(32768);
  for (int p = 0; p < kParts; ++p)
    for (int i = 0; i < kPerPart; ++i) {
      const Case2& c = parts[p][i];
      all[c.sh * 1024 + c.mb * 32 + c.me] = &c;
    }
  return all;
}

static void printStats(const char* name, uint64_t cases, uint64_t lowered, const Stats& st) {
  std::printf("%-7s configurations=%llu lowered=%llu evaluations=%llu new!=old=%llu old!=ref=%llu "
              "src-clobbered=%llu\n",
              name, (unsigned long long)cases, (unsigned long long)lowered,
              (unsigned long long)st.evals, (unsigned long long)st.newVsOld,
              (unsigned long long)st.oldVsRef, (unsigned long long)st.clobber);
}

int main() {
  const std::vector<uint64_t> RS = inputs(256);      // 15 + 64 + 64 + 256 = 399
  const std::vector<uint64_t> RSsmall = inputs(32);  // 175
  std::vector<uint64_t> RA = {0, ~0ull, 0xDEADBEEF00000003ull, 0xFFFFFFFF00000000ull,
                              0x00000000FFFFFFFFull, 0x8000000000000000ull};
  for (int i = 0; i < 6; ++i)
    RA.push_back(rnd());
  std::vector<uint64_t> RB;  // every low byte, clean and with garbage above it
  for (uint64_t b = 0; b < 256; ++b) {
    RB.push_back(b);
    RB.push_back(b | (rnd() << 8));
    RB.push_back(b | 0xFFFFFFFFFFFFFF00ull);
  }
  std::vector<uint64_t> RBsmall;  // rB 0..63 for the aliased runs
  for (uint64_t b = 0; b < 64; ++b) {
    RBsmall.push_back(b);
    RBsmall.push_back(b | (rnd() << 8));
    RBsmall.push_back(b | 0xFFFFFFFFFFFFFF00ull);
  }
  std::printf("inputs: rS=%zu (rlwnm %zu), rA=%zu (rlwimi), rB=%zu (aliased %zu)\n", RS.size(),
              RSsmall.size(), RA.size(), RB.size(), RBsmall.size());

  bool ok = true;
  uint64_t formCount[9] = {};
  for (int kind = 0; kind < 2; ++kind) {
    const char* insn = kind == 0 ? "rlwinm" : "rlwimi";
    const std::vector<const Case2*> all = collect(kind == 0 ? kRlwinmParts : kRlwimiParts);
    Stats st;
    uint64_t lowered = 0;
    for (const Case2* cp : all) {
      const Case2& c = *cp;
      const uint64_t m = ref::mask(c.mb + 32, c.me + 32);
      if (c.newf != c.oldf)
        ++lowered;
      if (kind == 0)
        ++formCount[c.form];
      if (kind == 0) {
        for (uint64_t rs : RS) {
          const uint64_t want = ref::rlwinm(rs, c.sh, m);
          check2(st, insn, c, want, ~rs ^ 0x5A5A5A5A5A5A5A5Aull, rs, false);  // rA = garbage
          check2(st, insn, c, want, rs, rs, true);                            // rA == rS
        }
      } else {
        for (uint64_t rs : RS)
          for (uint64_t ra : RA)
            check2(st, insn, c, ref::rlwimi(ra, rs, c.sh, m), ra, rs, false);
        for (int i = 0; i < 64; ++i) {  // basis vectors: the forms are linear in (rA, rS)
          check2(st, insn, c, ref::rlwimi(0, 1ull << i, c.sh, m), 0, 1ull << i, false);
          check2(st, insn, c, ref::rlwimi(1ull << i, 0, c.sh, m), 1ull << i, 0, false);
        }
        for (uint64_t rs : RS)
          check2(st, insn, c, ref::rlwimi(rs, rs, c.sh, m), rs, rs, true);  // rA == rS
      }
    }
    printStats(insn, all.size(), lowered, st);
    ok = ok && st.newVsOld == 0 && st.oldVsRef == 0 && st.clobber == 0;

    // Sensitivity control: a deliberately wrong pairing must be caught by the same inputs.
    uint64_t pairs = 0, caught = 0;
    for (const Case2* cp : all) {
      const Case2& c = *cp;
      if (c.newf == c.oldf)
        continue;
      const Case2* wrong[2] = {all[c.sh * 1024 + c.mb * 32 + (c.me + 1) % 32],
                               all[((c.sh + 1) % 32) * 1024 + c.mb * 32 + c.me]};
      for (const Case2* w : wrong) {
        ++pairs;
        bool diff = false;
        for (size_t i = 0; i < RS.size() && !diff; ++i) {
          Reg a0, s0, a1, s1;
          a0.u64 = a1.u64 = RA[i % RA.size()];
          s0.u64 = s1.u64 = RS[i];
          c.newf(a1, s1);
          w->oldf(a0, s0);
          diff = a0.u64 != a1.u64;
        }
        caught += diff;
      }
    }
    std::printf("%-7s sensitivity: %llu of %llu wrong pairings (me+1, sh+1) detected\n", insn,
                (unsigned long long)caught, (unsigned long long)pairs);
    ok = ok && caught == pairs;
  }
  static const char* const kNames[] = {"none(wrap)", "copy", "mask", "shl", "shl+mask",
                                       "shr", "shr+mask", "rotate", "rotate+mask"};
  std::printf("rlwinm/rlwimi forms:");
  for (int f = 0; f < 9; ++f)
    std::printf(" %s=%llu", kNames[f], (unsigned long long)formCount[f]);
  std::printf("\n");

  {  // rlwnm
    Stats st;
    uint64_t lowered = 0;
    for (int i = 0; i < kRlwnmCount; ++i) {
      const Case3& c = kRlwnm[i];
      const uint64_t m = ref::mask(c.mb + 32, c.me + 32);
      if (c.newf != c.oldf)
        ++lowered;
      auto run = [&](uint64_t ra, uint64_t rs, uint64_t rb, int alias, uint64_t want) {
        ++st.evals;
        Reg a0, s0, b0, a1, s1, b1;
        a0.u64 = a1.u64 = ra;
        s0.u64 = s1.u64 = rs;
        b0.u64 = b1.u64 = rb;
        switch (alias) {
          case 0: c.oldf(a0, s0, b0); c.newf(a1, s1, b1); break;  // distinct
          case 1: c.oldf(a0, a0, b0); c.newf(a1, a1, b1); break;  // rA == rS
          case 2: c.oldf(a0, s0, a0); c.newf(a1, s1, a1); break;  // rA == rB
          case 3: c.oldf(a0, s0, s0); c.newf(a1, s1, s1); break;  // rS == rB
          default: c.oldf(a0, a0, a0); c.newf(a1, a1, a1); break; // all three
        }
        const bool srcOk = (alias == 1 || alias >= 4 || (s0.u64 == rs && s1.u64 == rs)) &&
                           (alias == 2 || alias >= 3 || (b0.u64 == rb && b1.u64 == rb));
        if (!srcOk) {
          ++st.clobber;
          bad("src-clobbered", "rlwnm", int(rb & 0xFF), c.mb, c.me, ra, rs, rb, s1.u64, rs);
        }
        if (a1.u64 != a0.u64) {
          ++st.newVsOld;
          bad("new!=old", "rlwnm", int(rb & 0xFF), c.mb, c.me, ra, rs, rb, a1.u64, a0.u64);
        }
        if (a0.u64 != want) {
          ++st.oldVsRef;
          bad("old!=ref", "rlwnm", int(rb & 0xFF), c.mb, c.me, ra, rs, rb, a0.u64, want);
        }
      };
      for (uint64_t rb : RB)
        for (uint64_t rs : RSsmall)
          run(~rs, rs, rb, 0, ref::rlwnm(rs, rb, m));
      for (uint64_t rb : RBsmall)
        for (uint64_t rs : RSsmall) {
          run(rs, rs, rb, 1, ref::rlwnm(rs, rb, m));
          run(rb, rs, rb, 2, ref::rlwnm(rs, rb, m));
        }
      for (const std::vector<uint64_t>* set :
           std::initializer_list<const std::vector<uint64_t>*>{&RB, &RSsmall})
        for (uint64_t v : *set) {
          run(~v, v, v, 3, ref::rlwnm(v, v, m));
          run(v, v, v, 4, ref::rlwnm(v, v, m));
        }
    }
    printStats("rlwnm", kRlwnmCount, lowered, st);
    ok = ok && st.newVsOld == 0 && st.oldVsRef == 0 && st.clobber == 0;
  }
  std::printf("RESULT: %s\n", ok ? "PASS (0 mismatches)" : "FAIL");
  return ok ? 0 : 1;
}
