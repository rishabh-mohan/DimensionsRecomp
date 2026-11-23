// scan_baseline.cpp - replays the codegen's MXCSR flush-mode state machine over generated code and
// counts the switch lines that flush_mode_elision removes.
//
// Model (DimensionsRecomp/rexglue-sdk/src/codegen):
//   builders/context.cpp emit_set_flush_mode(enable): required = enable ? VMX : FPU. If csrState !=
//     required it prints ctx.fpscr.{enable|disable}FlushMode{Unconditional}(); (the Unconditional
//     suffix iff csrState != Unknown) and sets csrState = required.
//   function_graph.cpp: csrState = Unknown at function entry (564) and at every emitted label (597).
//   builders/control_flow.cpp: Unknown after bl to a Function/Import (84; a bl to an internal label
//     prints goto loc_X and keeps the state), after blrl (107) and after bctrl (193).
// Replays, per function:
//   off - the codegen as it is (flag off). Validated instruction by instruction against the switch
//         line actually printed after each instruction comment.
//   on  - flag on: elided builders print nothing and leave the state unchanged.
//   df  - dataflow estimate (off and on): a label takes the meet of its incoming states (every
//         goto loc_X to it plus the fallthrough) instead of Unknown, solved to a fixpoint; calls still
//         reset. Sizes what a dataflow pass in function_graph.cpp could remove on top.
// Usage: scan_baseline <generated dir> [comma-separated elided builders]
#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace fs = std::filesystem;
using sv = std::string_view;
typedef unsigned long long ull;

enum St : uint8_t { S_UNK = 0, S_FPU = 1, S_VMX = 2, S_TOP = 3 };
static inline St meet(St a, St b) { return a == S_TOP ? b : b == S_TOP ? a : a == b ? a : S_UNK; }

struct Builder {
  const char* name;
  char file;  // F floating_point.cpp, M memory.cpp (both require flush off = FPU), V vector.cpp (VMX)
};
static const Builder kB[] = {
    {"fabs", 'F'},     {"fnabs", 'F'},      {"fneg", 'F'},        {"fmr", 'F'},         {"fcfid", 'F'},
    {"fctid", 'F'},    {"fctidz", 'F'},     {"fctiw", 'F'},       {"fctiwz", 'F'},      {"frsp", 'F'},
    {"fcmpu", 'F'},    {"fadd", 'F'},       {"fadds", 'F'},       {"fsub", 'F'},        {"fsubs", 'F'},
    {"fmul", 'F'},     {"fmuls", 'F'},      {"fdiv", 'F'},        {"fdivs", 'F'},       {"fmadd", 'F'},
    {"fmadds", 'F'},   {"fmsub", 'F'},      {"fmsubs", 'F'},      {"fnmadd", 'F'},      {"fnmadds", 'F'},
    {"fnmsub", 'F'},   {"fnmsubs", 'F'},    {"fres", 'F'},        {"frsqrte", 'F'},     {"fsqrt", 'F'},
    {"fsqrts", 'F'},   {"fsel", 'F'},       {"lfd", 'M'},         {"lfdx", 'M'},        {"lfs", 'M'},
    {"lfsx", 'M'},     {"lfdu", 'M'},       {"lfdux", 'M'},       {"lfsu", 'M'},        {"lfsux", 'M'},
    {"stfd", 'M'},     {"stfdx", 'M'},      {"stfdux", 'M'},      {"stfiwx", 'M'},      {"stfs", 'M'},
    {"stfsx", 'M'},    {"stfdu", 'M'},      {"stfsu", 'M'},       {"stfsux", 'M'},      {"vaddfp", 'V'},
    {"vsubfp", 'V'},   {"vmulfp128", 'V'},  {"vmaddfp", 'V'},     {"vnmsubfp", 'V'},    {"vmaxfp", 'V'},
    {"vminfp", 'V'},   {"vrefp", 'V'},      {"vrsqrtefp", 'V'},   {"vexptefp", 'V'},    {"vlogefp", 'V'},
    {"vmsum3fp128", 'V'}, {"vmsum4fp128", 'V'}, {"vrfim", 'V'},   {"vrfin", 'V'},       {"vrfip", 'V'},
    {"vrfiz", 'V'},    {"vcmpbfp", 'V'},    {"vcmpeqfp", 'V'},    {"vcmpgefp", 'V'},    {"vcmpgtfp", 'V'},
    {"vctsxs", 'V'},   {"vcfsx", 'V'},      {"vcfux", 'V'},       {"vctuxs", 'V'},      {"vpkd3d128", 'V'},
};
constexpr int NB = int(sizeof(kB) / sizeof(kB[0]));
static_assert(NB == 75, "75 emit_set_flush_mode call sites");
// instruction_dispatch.cpp entries that reach a site builder under another mnemonic (99 entries total).
static const char* const kAlias[][2] = {
    {"fcmpo", "fcmpu"},          {"vaddfp128", "vaddfp"},     {"vsubfp128", "vsubfp"},
    {"vmaddfp128", "vmaddfp"},   {"vmaddcfp128", "vmaddfp"},  {"vnmsubfp128", "vnmsubfp"},
    {"vmaxfp128", "vmaxfp"},     {"vminfp128", "vminfp"},     {"vrefp128", "vrefp"},
    {"vrsqrtefp128", "vrsqrtefp"}, {"vexptefp128", "vexptefp"}, {"vlogefp128", "vlogefp"},
    {"vrfim128", "vrfim"},       {"vrfin128", "vrfin"},       {"vrfip128", "vrfip"},
    {"vrfiz128", "vrfiz"},       {"vcmpbfp128", "vcmpbfp"},   {"vcmpeqfp128", "vcmpeqfp"},
    {"vcmpgefp128", "vcmpgefp"}, {"vcmpgtfp128", "vcmpgtfp"}, {"vcfpsxws128", "vctsxs"},
    {"vcfpuxws128", "vctuxs"},   {"vcsxwfp128", "vcfsx"},     {"vcuxwfp128", "vcfux"},
};
static const char* const kDefaultElide =
    "fabs,fnabs,fneg,fmr,fcfid,fctidz,fctiwz,lfd,lfdx,lfdu,lfdux,stfd,stfdx,stfdux,stfiwx,stfdu,"
    "vrfin,vrfiz,vctsxs,vcfsx,vcfux,vctuxs,vpkd3d128";

static bool g_elide[NB];
static std::unordered_map<std::string, int> g_mnem;  // mnemonic -> builder
static std::vector<std::pair<std::string, int>> g_mnemList;
static std::unordered_map<std::string, ull> g_mnemCount;

enum EvT : uint8_t { E_LABEL, E_SITE, E_RESET, E_GOTO, E_NOFALL };
struct Ev {
  EvT type;
  uint8_t req;     // E_SITE: S_FPU / S_VMX
  uint8_t actual;  // E_SITE: 0 none, 1 enable, 2 disable, 3 enableUnconditional, 4 disableUnconditional, 5 several
  int32_t b;       // E_SITE: builder
  uint32_t idx;    // E_LABEL / E_GOTO: label index; E_SITE: line number
};
struct Count {
  ull sw = 0, cond = 0, uncond = 0, cause[3] = {0, 0, 0};  // cause of the Unknown state: entry, label, call
  ull perB[NB] = {};
};
static Count C_off, C_on, C_dfoff, C_dfon;
static ull g_inst[NB], g_actual[NB], g_mism[NB];
static ull g_files, g_bytes, g_lines, g_funcs, g_labels, g_insns, g_sites, g_gotos, g_resets, g_nofall;
static ull g_actSw, g_actCond, g_actUncond, g_actEn, g_actDis, g_unattrib, g_several, g_mismTotal;
static ull g_lblDefined, g_lblKnownOff, g_lblKnownOn, g_solvePasses, g_solveMax;
static int g_shownMism, g_shownUnattr;

// Per-function state.
static std::vector<Ev> F;
static std::unordered_map<uint32_t, uint32_t> F_lab;
static bool F_open, F_pendBl, F_blLocal, F_pendReset;
static int F_cur = -1;  // index in F of the current instruction's E_SITE event, -1 if not a site
static std::string F_file;

static uint32_t labelIndex(uint32_t addr) { return F_lab.try_emplace(addr, (uint32_t)F_lab.size()).first->second; }
static void flushPending() {
  if (F_pendReset || (F_pendBl && !F_blLocal)) {
    F.push_back({E_RESET, 0, 0, -1, 0});
    g_resets++;
  }
  F_pendBl = F_blLocal = F_pendReset = false;
}

static void countRun(const std::vector<St>* in, bool elide, Count& C, bool validate) {
  St st = S_UNK;
  int cause = 0;
  for (const Ev& e : F) {
    switch (e.type) {
      case E_LABEL:
        st = in ? ((*in)[e.idx] == S_TOP ? S_UNK : (*in)[e.idx]) : S_UNK;
        cause = 1;
        break;
      case E_RESET:
        st = S_UNK;
        cause = 2;
        break;
      case E_SITE: {
        uint8_t pred = 0;
        if (!(elide && g_elide[e.b]) && st != e.req) {
          pred = uint8_t((e.req == S_VMX ? 1 : 2) + (st != S_UNK ? 2 : 0));
          C.sw++;
          C.perB[e.b]++;
          if (st == S_UNK) {
            C.cond++;
            C.cause[cause]++;
          } else {
            C.uncond++;
          }
          st = (St)e.req;
        }
        if (validate && pred != e.actual) {
          g_mismTotal++;
          g_mism[e.b]++;
          if (g_shownMism < 12) {
            g_shownMism++;
            printf("  mismatch %s:%u %s: replay %d, actual %d (1 en, 2 dis, 3 enU, 4 disU, 5 several)\n",
                   F_file.c_str(), e.idx, kB[e.b].name, pred, e.actual);
          }
        }
        break;
      }
      default:
        break;
    }
  }
}

// Forward dataflow over the function's labels, optimistic start (TOP), in-place meets until stable.
// Code after an unconditional goto/return/jump table is not live until the next label, so its gotos
// and fallthrough add nothing.
static void solve(bool elide, std::vector<St>& in) {
  in.assign(F_lab.size(), S_TOP);
  for (ull pass = 1;; pass++) {
    bool changed = false;
    St st = S_UNK;
    bool live = true;
    auto upd = [&](uint32_t l) {
      const St n = meet(in[l], st);
      if (n != in[l]) {
        in[l] = n;
        changed = true;
      }
    };
    for (const Ev& e : F) {
      switch (e.type) {
        case E_LABEL:
          if (live) upd(e.idx);
          st = in[e.idx];
          live = true;
          break;
        case E_SITE:
          if (!(elide && g_elide[e.b])) st = (St)e.req;
          break;
        case E_RESET:
          st = S_UNK;
          break;
        case E_GOTO:
          if (live) upd(e.idx);
          break;
        case E_NOFALL:
          live = false;
          break;
      }
    }
    if (!changed || pass > 4 * F_lab.size() + 8) {
      g_solvePasses += pass;
      g_solveMax = std::max(g_solveMax, pass);
      if (changed) fprintf(stderr, "solve: no fixpoint in %s\n", F_file.c_str());
      return;
    }
  }
}

static void finishFunc() {
  if (!F_open) return;
  flushPending();
  countRun(nullptr, false, C_off, true);
  countRun(nullptr, true, C_on, false);
  std::vector<St> in;
  solve(false, in);
  for (const Ev& e : F)
    if (e.type == E_LABEL) {
      g_lblDefined++;
      g_lblKnownOff += in[e.idx] == S_FPU || in[e.idx] == S_VMX;
    }
  countRun(&in, false, C_dfoff, false);
  solve(true, in);
  for (const Ev& e : F)
    if (e.type == E_LABEL) g_lblKnownOn += in[e.idx] == S_FPU || in[e.idx] == S_VMX;
  countRun(&in, true, C_dfon, false);
  F.clear();
  F_lab.clear();
  F_open = false;
  F_cur = -1;
}

static void processLine(sv line, uint32_t lineNo) {
  if (!line.empty() && line.back() == '\r') line.remove_suffix(1);
  size_t tabs = 0;
  while (tabs < line.size() && line[tabs] == '\t') tabs++;
  sv s = line.substr(tabs);
  while (!s.empty() && s.front() == ' ') s.remove_prefix(1);
  if (s.empty()) return;
  if (tabs == 0 && s.starts_with("DEFINE_REX_FUNC(")) {
    finishFunc();
    F_open = true;
    F_cur = -1;
    g_funcs++;
    return;
  }
  if (!F_open) return;
  if (s.starts_with("loc_") && s.back() == ':') {
    flushPending();
    const uint32_t addr = (uint32_t)strtoul(std::string(s.substr(4, s.size() - 5)).c_str(), nullptr, 16);
    F.push_back({E_LABEL, 0, 0, -1, labelIndex(addr)});
    g_labels++;
    F_cur = -1;
    return;
  }
  if (s.starts_with("// ")) {
    sv rest = s.substr(3);
    if (!rest.empty() && rest[0] >= 'a' && rest[0] <= 'z') {  // "\t// mnemonic operands"
      sv m = rest.substr(0, rest.find(' '));
      flushPending();
      g_insns++;
      F_cur = -1;
      if (!m.empty() && m.back() == '.') m.remove_suffix(1);
      const std::string ms(m);
      auto it = g_mnem.find(ms);
      if (it != g_mnem.end()) {
        const int b = it->second;
        g_inst[b]++;
        g_sites++;
        g_mnemCount[ms]++;
        F_cur = (int)F.size();
        F.push_back({E_SITE, uint8_t(kB[b].file == 'V' ? S_VMX : S_FPU), 0, b, lineNo});
      } else if (ms == "bl") {
        F_pendBl = true;
        F_blLocal = false;
      } else if (ms == "blrl" || ms == "bctrl") {
        F_pendReset = true;
      }
      return;
    }
  }
  if (s.starts_with("ctx.fpscr.")) {
    const int k = s == "ctx.fpscr.enableFlushMode();"                ? 1
                  : s == "ctx.fpscr.disableFlushMode();"             ? 2
                  : s == "ctx.fpscr.enableFlushModeUnconditional();"  ? 3
                  : s == "ctx.fpscr.disableFlushModeUnconditional();" ? 4
                                                                      : 0;
    if (k) {
      g_actSw++;
      (k & 1 ? g_actEn : g_actDis)++;
      (k <= 2 ? g_actCond : g_actUncond)++;
      if (F_cur >= 0) {
        Ev& e = F[F_cur];
        if (e.actual == 0) {
          e.actual = (uint8_t)k;
          g_actual[e.b]++;
        } else {
          e.actual = 5;
          g_several++;
        }
      } else {
        g_unattrib++;
        if (g_shownUnattr < 12) {
          g_shownUnattr++;
          printf("  unattributed switch %s:%u: %.*s\n", F_file.c_str(), lineNo, (int)s.size(), s.data());
        }
      }
      return;
    }
  }
  for (size_t pos = s.find("goto loc_"); pos != sv::npos; pos = s.find("goto loc_", pos)) {
    pos += 9;
    size_t e = pos;
    while (e < s.size() && isxdigit((unsigned char)s[e])) e++;
    const uint32_t addr = (uint32_t)strtoul(std::string(s.substr(pos, e - pos)).c_str(), nullptr, 16);
    F.push_back({E_GOTO, 0, 0, -1, labelIndex(addr)});
    g_gotos++;
    if (F_pendBl) F_blLocal = true;
  }
  if ((tabs == 1 && (s.starts_with("goto loc_") || s == "return;")) ||
      s.find("__builtin_trap(); // Switch case out of range") != sv::npos) {
    F.push_back({E_NOFALL, 0, 0, -1, 0});
    g_nofall++;
  }
  if (F_pendBl && s.find("REX_FATAL(") != sv::npos) F_blLocal = true;  // unresolved bl: no reset
}

static void printCount(const char* name, const Count& c) {
  printf("%-13s %8llu switch lines: conditional %8llu (after entry %llu, label %llu, call %llu), unconditional %8llu\n",
         name, c.sw, c.cond, c.cause[0], c.cause[1], c.cause[2], c.uncond);
}

int main(int argc, char** argv) {
  const char* dir = argc > 1 ? argv[1] : "baseline/DimensionsRecomp/rexlego/generated/default";
  const std::string elist = argc > 2 ? argv[2] : kDefaultElide;
  for (int b = 0; b < NB; b++) {
    g_mnem[kB[b].name] = b;
    g_mnemList.push_back({kB[b].name, b});
  }
  for (auto& a : kAlias) {
    int b = g_mnem.at(a[1]);
    g_mnem[a[0]] = b;
    g_mnemList.push_back({a[0], b});
  }
  size_t p0 = 0;
  while (p0 <= elist.size()) {
    size_t p1 = elist.find(',', p0);
    if (p1 == std::string::npos) p1 = elist.size();
    const std::string nm = elist.substr(p0, p1 - p0);
    if (!nm.empty()) {
      int found = -1;
      for (int b = 0; b < NB; b++)
        if (nm == kB[b].name) found = b;
      if (found < 0) {
        fprintf(stderr, "unknown builder in elide list: %s\n", nm.c_str());
        return 2;
      }
      g_elide[found] = true;
    }
    p0 = p1 + 1;
  }
  std::vector<fs::path> files;
  for (auto& de : fs::directory_iterator(dir))
    if (de.is_regular_file() && de.path().extension() == ".cpp") files.push_back(de.path());
  std::sort(files.begin(), files.end());
  printf("scan_baseline: %s (%zu .cpp files)\nelided builders:", dir, files.size());
  int nel = 0;
  for (int b = 0; b < NB; b++)
    if (g_elide[b]) printf(" %s", kB[b].name), nel++;
  printf(" (%d)\n\n", nel);

  std::string buf;
  for (auto& path : files) {
    FILE* f = fopen(path.string().c_str(), "rb");
    if (!f) {
      fprintf(stderr, "cannot open %s\n", path.string().c_str());
      continue;
    }
    fseek(f, 0, SEEK_END);
    const long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    buf.resize(sz > 0 ? (size_t)sz : 0);
    const size_t got = buf.empty() ? 0 : fread(buf.data(), 1, buf.size(), f);
    fclose(f);
    buf.resize(got);
    g_files++;
    g_bytes += got;
    F_file = path.filename().string();
    const char* d = buf.data();
    size_t i = 0;
    uint32_t ln = 0;
    while (i < got) {
      const char* nl = (const char*)memchr(d + i, '\n', got - i);
      const size_t e = nl ? (size_t)(nl - d) : got;
      processLine(sv(d + i, e - i), ++ln);
      i = e + 1;
    }
    g_lines += ln;
    finishFunc();
  }

  ull elInst = 0, elActual = 0;
  for (int b = 0; b < NB; b++)
    if (g_elide[b]) elInst += g_inst[b], elActual += g_actual[b];
  printf("\nscan: %llu files, %.1f MB, %llu lines, %llu functions, %llu labels, %llu instructions, %llu gotos, %llu call resets\n",
         g_files, g_bytes / 1048576.0, g_lines, g_funcs, g_labels, g_insns, g_gotos, g_resets);
  printf("site instructions: %llu at the 75 builders, %llu of them at the %d elided builders\n", g_sites, elInst, nel);
  printf("actual switch lines: %llu (conditional %llu, unconditional %llu; enable %llu, disable %llu)\n", g_actSw,
         g_actCond, g_actUncond, g_actEn, g_actDis);
  printf("  at elided builders: %llu; not after a site instruction: %llu; second switch at one instruction: %llu\n",
         elActual, g_unattrib, g_several);
  printCount("replay off:", C_off);
  printf("validation: %llu instructions where the replay differs from the actual switch line\n", g_mismTotal);
  printCount("replay on:", C_on);
  printCount("dataflow off:", C_dfoff);
  printCount("dataflow on:", C_dfon);
  printf("labels with a known state under dataflow: off %llu, on %llu, of %llu (solver passes: total %llu, max %llu)\n",
         g_lblKnownOff, g_lblKnownOn, g_lblDefined, g_solvePasses, g_solveMax);
  const double pct = C_off.sw ? 100.0 * (double)(C_off.sw - C_on.sw) / (double)C_off.sw : 0.0;
  printf("\nflush_mode_elision removes %llu of %llu switch lines (%.1f%%); a dataflow pass on top would leave %llu (flag on) / %llu (flag off)\n",
         C_off.sw - C_on.sw, C_off.sw, pct, C_dfon.sw, C_dfoff.sw);

  printf("\n| builder | file | elided | instructions | mnemonics | actual switch lines | replay off | replay on | dataflow off | dataflow on | replay mismatches |\n");
  printf("|---|---|---|---|---|---|---|---|---|---|---|\n");
  for (int b = 0; b < NB; b++) {
    std::string mn;
    for (auto& [m, bb] : g_mnemList) {
      if (bb != b) continue;
      auto it = g_mnemCount.find(m);
      if (it == g_mnemCount.end() || !it->second) continue;
      if (!mn.empty()) mn += ", ";
      mn += m + " " + std::to_string(it->second);
    }
    printf("| %s | %s | %s | %llu | %s | %llu | %llu | %llu | %llu | %llu | %llu |\n", kB[b].name,
           kB[b].file == 'F' ? "floating_point.cpp" : kB[b].file == 'M' ? "memory.cpp" : "vector.cpp",
           g_elide[b] ? "yes" : "no", g_inst[b], mn.empty() ? "-" : mn.c_str(), g_actual[b], C_off.perB[b],
           C_on.perB[b], C_dfoff.perB[b], C_dfon.perB[b], g_mism[b]);
  }
  printf("\nSCAN: validation %s (replay mismatches %llu, unattributed switch lines %llu) | removed %llu of %llu switch lines | elided-builder instructions %llu\n",
         g_mismTotal == 0 && g_unattrib == 0 ? "PASS" : "FAIL", g_mismTotal, g_unattrib, C_off.sw - C_on.sw, C_off.sw,
         elInst);
  return 0;
}
