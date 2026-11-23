// Agent 10 (task #9): replays the SDK's known-answer tests (tests/ppc/asm/instr_*.s) through the emitted
// forms with a chosen helper implementation. Only the vector instructions these helpers serve are run.
#pragma once
#include <immintrin.h>

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>

#include "impls.h"

struct KatTest {
  std::string name;
  ref::V vin[32] = {};
  bool vin_set[32] = {};
  uint64_t gpr[32] = {};
  std::vector<std::pair<std::string, std::vector<std::string>>> insns;
  std::vector<std::pair<int, ref::V>> vout;
};

inline std::vector<KatTest> kat_parse(const std::string& path) {
  std::vector<KatTest> tests;
  std::ifstream f(path);
  std::string line;
  while (std::getline(f, line)) {
    size_t p = line.find_first_not_of(" \t");
    if (p == std::string::npos) continue;
    std::string s = line.substr(p);
    while (!s.empty() && (s.back() == '\r' || s.back() == ' ')) s.pop_back();
    if (s.empty()) continue;
    if (s.back() == ':' && s.find(' ') == std::string::npos) { tests.push_back({}); tests.back().name = s.substr(0, s.size() - 1); continue; }
    if (tests.empty()) continue;
    KatTest& t = tests.back();
    int n; unsigned w[4]; long long imm;
    if (sscanf(s.c_str(), "#_ REGISTER_IN v%d [%x, %x, %x, %x]", &n, &w[0], &w[1], &w[2], &w[3]) == 5) {
      uint32_t pw[4] = {w[0], w[1], w[2], w[3]}; t.vin[n] = ref::from_ppc_words(pw); t.vin_set[n] = true;
    } else if (sscanf(s.c_str(), "#_ REGISTER_IN r%d %lli", &n, &imm) == 2) {
      t.gpr[n] = uint64_t(imm);
    } else if (sscanf(s.c_str(), "#_ REGISTER_OUT v%d [%x, %x, %x, %x]", &n, &w[0], &w[1], &w[2], &w[3]) == 5) {
      uint32_t pw[4] = {w[0], w[1], w[2], w[3]}; t.vout.push_back({n, ref::from_ppc_words(pw)});
    } else if (s[0] != '#') {
      std::string mn = s.substr(0, s.find(' '));
      std::vector<std::string> ops;
      if (s.find(' ') != std::string::npos) {
        std::string rest = s.substr(s.find(' ') + 1), cur;
        for (char ch : rest) { if (ch == ',') { ops.push_back(cur); cur.clear(); } else if (ch != ' ') cur += ch; }
        if (!cur.empty()) ops.push_back(cur);
      }
      if (mn != "blr") t.insns.push_back({mn, ops});
    }
  }
  return tests;
}

// Returns false if the mnemonic is not handled.
template <class I> bool kat_exec(const std::string& mn, const std::vector<std::string>& o, ref::V* vr, uint64_t* gpr) {
  auto R = [&](int i) { return std::atoi(o[i].c_str() + 1); };
  auto A = [&](int i) { return ld(vr[R(i)]); };
  if (mn == "li") { gpr[R(0)] = uint64_t(std::strtoll(o[1].c_str(), nullptr, 0)); return true; }
  if (mn == "lvsl" || mn == "lvsr") {
    uint64_t ea = (R(1) ? gpr[R(1)] : 0) + gpr[R(2)];
    const uint8_t* t = (mn == "lvsl" ? I::shiftL() : I::shiftR()) + (ea & 0xF) * 16;
    vr[R(0)] = st(simde_mm_load_si128(reinterpret_cast<const m128i*>(t)));
    return true;
  }
  m128i r;
  if (mn == "vslo") r = I::vslo(A(1), A(2));
  else if (mn == "vsro") r = I::vsro(A(1), A(2));
  else if (mn == "vsl") r = I::vsl(A(1), A(2));
  else if (mn == "vsr") r = I::vsr(A(1), A(2));
  else if (mn == "vperm") r = I::perm(A(1), A(2), A(3));
  else if (mn == "vslb") r = e_vslb<I>(A(1), A(2));
  else if (mn == "vslh") r = e_vslh<I>(A(1), A(2));
  else if (mn == "vsrh") r = e_vsrh<I>(A(1), A(2));
  else if (mn == "vsrah") r = e_vsrah<I>(A(1), A(2));
  else if (mn == "vrlh") r = e_vrlh<I>(A(1), A(2));
  else if (mn == "vctuxs") {
    unsigned csr = _mm_getcsr();
    _mm_setcsr(csr | 0x8040);  // generated code runs vctuxs in flush mode (FTZ|DAZ)
    r = e_vctuxs<I>(ldps(vr[R(1)]), std::atoi(o[2].c_str()));
    _mm_setcsr(csr);
  } else return false;
  vr[R(0)] = st(r);
  return true;
}

// Runs every test in the given files; returns the number of failures.
template <class I> int kat_run(const std::vector<std::string>& files, int& ran) {
  int fails = 0;
  for (const auto& path : files) {
    for (const KatTest& t : kat_parse(path)) {
      ref::V vr[32]; uint64_t gpr[32];
      for (int i = 0; i < 32; i++) { vr[i] = t.vin[i]; gpr[i] = t.gpr[i]; }
      bool ok = true, handled = true;
      for (const auto& in : t.insns) handled = handled && kat_exec<I>(in.first, in.second, vr, gpr);
      if (!handled) { printf("  KAT %s: unhandled instruction, skipped\n", t.name.c_str()); continue; }
      for (const auto& out : t.vout) {
        if (!(vr[out.first] == out.second)) {
          ok = false;
          printf("  KAT FAIL [%s] %s v%d: got %08X %08X %08X %08X want %08X %08X %08X %08X\n", I::name, t.name.c_str(), out.first,
                 ref::ppc_word(vr[out.first], 0), ref::ppc_word(vr[out.first], 1), ref::ppc_word(vr[out.first], 2), ref::ppc_word(vr[out.first], 3),
                 ref::ppc_word(out.second, 0), ref::ppc_word(out.second, 1), ref::ppc_word(out.second, 2), ref::ppc_word(out.second, 3));
        }
      }
      ran++;
      fails += ok ? 0 : 1;
    }
  }
  return fails;
}
