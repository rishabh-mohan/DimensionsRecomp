// Writes tests/ppc/asm/instr_rlw_lowering.s. Expected values come from the reference
// model (refmodel.h); the comment line of each test shows the lowering class and text.
// Usage: asmgen.exe <out.s>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <map>
#include <optional>
#include <string>

#include "refmodel.h"
#include "rotate_mask.h"

using namespace rex::codegen;

static std::string g_out;
static int g_tests = 0;

static const char* formName(rlw::Form f) {
  static const char* const n[] = {"generic form, mask wraps", "copy", "mask", "shl", "shl+mask",
                                  "shr", "shr+mask", "rotate", "rotate+mask"};
  return n[int(f)];
}
static std::string R(int r) { return "r" + std::to_string(r); }
static std::string describe(const char* what, rlw::Form f, const std::optional<std::string>& s) {
  std::string d = std::string(what) + " -> " + formName(f);
  if (s)
    d += ": " + *s;
  return d;
}

static void emit(const std::string& name, const std::string& comment,
                 const std::map<int, uint64_t>& in, const std::string& insn, bool record,
                 const std::map<int, uint64_t>& out) {
  char buf[128];
  const std::string op = insn.substr(0, insn.find_first_of(". "));  // rlwinm / rlwimi / rlwnm
  g_out += "test_rlw_lowering_" + op + "_" + name + ":\n";
  g_out += "  # " + comment + "\n";
  for (const auto& [r, v] : in) {
    std::snprintf(buf, sizeof buf, "  #_ REGISTER_IN r%d 0x%016llX\n", r, (unsigned long long)v);
    g_out += buf;
  }
  g_out += "  " + insn + "\n";
  if (record)
    g_out += "  mfcr r12\n";
  g_out += "  blr\n";
  for (const auto& [r, v] : out) {
    std::snprintf(buf, sizeof buf, "  #_ REGISTER_OUT r%d 0x%016llX\n", r, (unsigned long long)v);
    g_out += buf;
  }
  g_out += "\n";
  ++g_tests;
}

static constexpr uint64_t kGarbage = 0xDEADBEEFDEADBEEFull;  // rA preset: must be overwritten

static void rlwinm(const std::string& name, const char* what, int ra, int rs, unsigned sh,
                   unsigned mb, unsigned me, uint64_t rsv, bool record = false) {
  std::map<int, uint64_t> in;
  if (ra != rs)
    in[ra] = kGarbage;
  in[rs] = rsv;
  const uint64_t res = ref::rlwinm(rsv, sh, ref::mask(mb + 32, me + 32));
  std::map<int, uint64_t> out = in;
  out[ra] = res;
  if (record)
    out[12] = ref::cr0(res);
  char insn[96];
  std::snprintf(insn, sizeof insn, "rlwinm%s r%d, r%d, %u, %u, %u", record ? "." : "", ra, rs, sh,
                mb, me);
  emit(name, describe(what, rlw::classify(sh, mb, me), rlw::lowerRlwinm(R(ra), R(rs), sh, mb, me)),
       in, insn, record, out);
}

static void rlwimi(const std::string& name, const char* what, int ra, int rs, unsigned sh,
                   unsigned mb, unsigned me, uint64_t rav, uint64_t rsv, bool record = false) {
  if (ra == rs)
    rav = rsv;
  std::map<int, uint64_t> in;
  in[ra] = rav;
  in[rs] = rsv;
  const uint64_t res = ref::rlwimi(rav, rsv, sh, ref::mask(mb + 32, me + 32));
  std::map<int, uint64_t> out = in;
  out[ra] = res;
  if (record)
    out[12] = ref::cr0(res);
  char insn[96];
  std::snprintf(insn, sizeof insn, "rlwimi%s r%d, r%d, %u, %u, %u", record ? "." : "", ra, rs, sh,
                mb, me);
  emit(name, describe(what, rlw::classify(sh, mb, me), rlw::lowerRlwimi(R(ra), R(rs), sh, mb, me)),
       in, insn, record, out);
}

static void rlwnm(const std::string& name, const char* what, int ra, int rs, int rb, unsigned mb,
                  unsigned me, uint64_t rsv, uint64_t rbv, bool record = false) {
  if (rs == rb)
    rbv = rsv;
  std::map<int, uint64_t> in;
  if (ra != rs && ra != rb)
    in[ra] = kGarbage;
  in[rs] = rsv;
  in[rb] = rbv;
  const uint64_t res = ref::rlwnm(rsv, rbv, ref::mask(mb + 32, me + 32));
  std::map<int, uint64_t> out = in;
  out[ra] = res;
  if (record)
    out[12] = ref::cr0(res);
  char insn[96];
  std::snprintf(insn, sizeof insn, "rlwnm%s r%d, r%d, r%d, %u, %u", record ? "." : "", ra, rs, rb,
                mb, me);
  const auto s = rlw::lowerRlwnm(R(ra), R(rs), R(rb), mb, me);
  const rlw::Form f = !s                                   ? rlw::Form::kNone
                      : rlw::mask32(mb, me) == 0xFFFFFFFFu ? rlw::Form::kRotate
                                                           : rlw::Form::kRotateMask;
  emit(name, describe(what, f, s), in, insn, record, out);
}

int main(int argc, char** argv) {
  const char* path = argc > 1 ? argv[1] : "instr_rlw_lowering.s";
  g_out =
      "# rlwinm / rlwnm / rlwimi with RecompilerConfig::rlwinmLowering (one test per lowering\n"
      "# class). Expected values come from a reference model of the 64-bit ISA text:\n"
      "# rA = ROTL32(rS, n) & MASK(mb + 32, me + 32), rlwimi keeps rA outside the mask.\n"
      "# rS always has garbage in its high word and rA starts as garbage, so rA's high word\n"
      "# must come out cleared (rlwinm, rlwnm) or kept (rlwimi). The wrap tests (mb > me)\n"
      "# keep the generic 64-bit form. The text after \"->\" is the lowered statement.\n"
      "\n";

  // rlwinm (encodings the disassembler turns into rotlwi / clrlwi are avoided).
  rlwinm("clrrwi", "clrrwi 4", 3, 4, 0, 0, 27, 0xCAFEBABE12345678ull);
  rlwinm("mask_mid", "rlwinm 0,8,23", 3, 4, 0, 8, 23, 0xFFFFFFFF89ABCDEFull);
  rlwinm("slwi", "slwi 4", 3, 4, 4, 0, 27, 0xFFFFFFFF12345678ull);
  rlwinm("slwi_31", "slwi 31", 3, 4, 31, 0, 0, 0xFFFFFFFE00000003ull);
  rlwinm("shl_mask", "rlwinm 2,20,29", 3, 4, 2, 20, 29, 0xDEADBEEF123456FFull);
  rlwinm("extlwi", "extlwi 8,8", 3, 4, 8, 0, 7, 0x0123456789ABCDEFull);
  rlwinm("srwi", "srwi 8", 3, 4, 24, 8, 31, 0xA5A5A5A512345678ull);
  rlwinm("srwi_31", "srwi 31", 3, 4, 1, 31, 31, 0x0000000180000000ull);
  rlwinm("extrwi", "extrwi 4,25", 3, 4, 29, 28, 31, 0xFFFFFFFF00000030ull);
  rlwinm("shr_mask", "rlwinm 24,8,15", 3, 4, 24, 8, 15, 0xA5A5A5A512345678ull);
  rlwinm("rotate_mask", "rlwinm 8,16,27", 3, 4, 8, 16, 27, 0xFFFFFFFF12345678ull);
  rlwinm("rotate_mask_bit31", "rlwinm 31,0,15", 3, 4, 31, 0, 15, 0xFFFFFFFF00000001ull);
  rlwinm("wrap", "rlwinm 8,28,3", 3, 4, 8, 28, 3, 0xFFFFFFFF12345678ull);
  rlwinm("alias", "slwi 4, rA == rS", 4, 4, 4, 0, 27, 0xFFFFFFFF87654321ull);
  rlwinm("record", "slwi. 4", 3, 4, 4, 0, 27, 0xFFFFFFFF01234567ull, true);
  rlwinm("record_zero", "rlwinm. 0,0,3", 3, 4, 0, 0, 3, 0xFFFFFFFF0FFFFFFFull, true);

  // rlwimi (no disassembler alias); rA has a nonzero high word that must be kept.
  rlwimi("shl", "rlwimi 2,0,29", 6, 4, 2, 0, 29, 0xDEADBEEF00000003ull, 0xCAFEBABE90003000ull);
  rlwimi("insrwi", "insrwi 8,16", 6, 4, 8, 16, 23, 0x0123456789ABCDEFull, 0xFFFFFFFF000000ABull);
  rlwimi("inslwi", "inslwi 8,16", 6, 4, 16, 16, 23, 0x0123456789ABCDEFull, 0x555555553C000000ull);
  rlwimi("mask", "rlwimi 0,8,15", 6, 4, 0, 8, 15, 0xDEADBEEF11223344ull, 0xFFFFFFFF00AA0000ull);
  rlwimi("shl_16", "rlwimi 16,0,15", 6, 4, 16, 0, 15, 0x22222222DEAD1234ull, 0x111111110000BEEFull);
  rlwimi("shr", "rlwimi 24,8,31", 6, 4, 24, 8, 31, 0x8000000077777777ull, 0xFFFFFFFFAABBCCDDull);
  rlwimi("rotate_mask", "rlwimi 8,16,27", 6, 4, 8, 16, 27, 0xCAFEBABE00000000ull, 0xFFFFFFFF12345678ull);
  rlwimi("copy", "rlwimi 0,0,31", 6, 4, 0, 0, 31, 0xABCDEF0011111111ull, 0xFFFFFFFF12345678ull);
  rlwimi("rotate", "rlwimi 8,0,31", 6, 4, 8, 0, 31, 0xFFFFFFFFFFFFFFFFull, 0x7777777712345678ull);
  rlwimi("wrap", "rlwimi 8,28,3", 6, 4, 8, 28, 3, 0xDEADBEEFCAFEBABEull, 0xFFFFFFFF12345678ull);
  rlwimi("alias", "rlwimi 16,0,15, rA == rS", 4, 4, 16, 0, 15, 0, 0xDEADBEEF0000CAFEull);
  rlwimi("record", "rlwimi. 4,0,27", 6, 4, 4, 0, 27, 0x000000010000000Full, 0xFFFFFFFFF1234567ull, true);

  // rlwnm: the count is rB & 0x1F; rB > 31 and garbage in rB's high bits.
  rlwnm("rb_40", "rB = 0x28", 3, 4, 5, 16, 27, 0xFFFFFFFF12345678ull, 0x28);
  rlwnm("rb_garbage", "rB = 0xFFFFFFFF000000F8", 3, 4, 5, 8, 31, 0xA5A5A5A512345678ull, 0xFFFFFFFF000000F8ull);
  rlwnm("rb_32", "rB = 32", 3, 4, 5, 4, 27, 0xFFFFFFFF12345678ull, 0x20);
  rlwnm("rb_63", "rB = 63", 3, 4, 5, 0, 15, 0xFFFFFFFF00000003ull, 0x3F);
  rlwnm("wrap", "rlwnm 28,3", 3, 4, 5, 28, 3, 0xFFFFFFFF12345678ull, 0x48);
  rlwnm("alias", "rA == rS == rB", 5, 5, 5, 16, 27, 0xFFFFFFFF12345668ull, 0);
  rlwnm("record", "rlwnm. 0,27", 3, 4, 5, 0, 27, 0xFFFFFFFF01234567ull, 0x24, true);

  std::ofstream f(path, std::ios::binary);
  f << g_out;
  if (!f) {
    std::fprintf(stderr, "asmgen: cannot write %s\n", path);
    return 1;
  }
  std::printf("asmgen: wrote %d tests to %s\n", g_tests, path);
  return 0;
}
