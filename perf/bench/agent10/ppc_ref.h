// Agent 10 (task #9): scalar reference semantics for the guest SIMD helpers in rex/ppc/intrinsics.h.
// Plain C++ only (no SIMD), written from the PPC ISA plus the documented behaviour of the old helpers.
// Vector layout = the SDK's register layout: x86 byte i holds PPC byte 15-i, and x86 u32[3-k] holds PPC word k.
#pragma once
#include <cstdint>
#include <cstring>

namespace ref {

struct alignas(16) V {
  uint8_t b[16];
};
inline bool operator==(const V& x, const V& y) { return memcmp(x.b, y.b, 16) == 0; }
inline uint8_t pb(const V& v, int i) { return v.b[15 - i]; }  // PPC byte i
inline void setpb(V& v, int i, uint8_t x) { v.b[15 - i] = x; }
inline uint16_t h(const V& v, int k) { uint16_t x; memcpy(&x, v.b + 2 * k, 2); return x; }  // x86 lane
inline void seth(V& v, int k, uint16_t x) { memcpy(v.b + 2 * k, &x, 2); }
inline uint32_t w(const V& v, int k) { uint32_t x; memcpy(&x, v.b + 4 * k, 4); return x; }  // x86 lane
inline void setw(V& v, int k, uint32_t x) { memcpy(v.b + 4 * k, &x, 4); }
inline V from_ppc_words(const uint32_t pw[4]) { V v; for (int k = 0; k < 4; k++) setw(v, 3 - k, pw[k]); return v; }
inline uint32_t ppc_word(const V& v, int k) { return w(v, 3 - k); }

// xoshiro256** seeded by splitmix64: deterministic, fast.
struct Rng {
  uint64_t s[4];
  explicit Rng(uint64_t seed) {
    for (auto& x : s) {
      seed += 0x9E3779B97F4A7C15ull;
      uint64_t z = seed;
      z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ull;
      z = (z ^ (z >> 27)) * 0x94D049BB133111EBull;
      x = z ^ (z >> 31);
    }
  }
  static uint64_t rotl(uint64_t x, int k) { return (x << k) | (x >> (64 - k)); }
  uint64_t next() {
    uint64_t r = rotl(s[1] * 5, 7) * 9, t = s[1] << 17;
    s[2] ^= s[0]; s[3] ^= s[1]; s[1] ^= s[2]; s[0] ^= s[3]; s[2] ^= t; s[3] = rotl(s[3], 45);
    return r;
  }
  V vec() { V v; uint64_t a = next(), b = next(); memcpy(v.b, &a, 8); memcpy(v.b + 8, &b, 8); return v; }
};

//---------------------------------------------------------------------------
// Helper-level contracts (what the old helpers did for EVERY count value; callers mask, but the
// new helpers must still match for all inputs).
inline uint16_t sllv16(uint16_t a, uint16_t c) { return c >= 16 ? 0 : uint16_t(a << c); }
inline uint16_t srlv16(uint16_t a, uint16_t c) { return c >= 16 ? 0 : uint16_t(a >> c); }
inline uint16_t srav16(uint16_t a, uint16_t c) { return uint16_t(int16_t(a) >> (c > 15 ? 15 : c)); }
inline uint8_t sllv8(uint8_t a, uint8_t c) { return c >= 8 ? 0 : uint8_t(a << c); }

//---------------------------------------------------------------------------
// Instruction-level semantics (PPC ISA, element order is irrelevant for element-wise ops).
inline uint8_t vslb(uint8_t a, uint8_t b) { return uint8_t(a << (b & 7)); }
inline uint16_t vslh(uint16_t a, uint16_t b) { return uint16_t(a << (b & 15)); }
inline uint16_t vsrh(uint16_t a, uint16_t b) { return uint16_t(a >> (b & 15)); }
inline uint16_t vsrah(uint16_t a, uint16_t b) { return uint16_t(int16_t(a) >> (b & 15)); }
inline uint16_t vrlh(uint16_t a, uint16_t b) {
  int s = b & 15;
  return uint16_t((a << s) | (a >> ((16 - s) & 15)));
}

// vslo: shift left by octets, count = bits 121:124 of vB = (PPC byte 15 >> 3) & 0xF.
inline V vslo(const V& a, const V& b) {
  int sh = (pb(b, 15) >> 3) & 0xF;
  V r;
  for (int i = 0; i < 16; i++) setpb(r, i, i + sh < 16 ? pb(a, i + sh) : 0);
  return r;
}
inline V vsro(const V& a, const V& b) {
  int sh = (pb(b, 15) >> 3) & 0xF;
  V r;
  for (int i = 0; i < 16; i++) setpb(r, i, i >= sh ? pb(a, i - sh) : 0);
  return r;
}

// Whole-register bit shifts. The PPC big-endian 128-bit value equals the x86 little-endian 128-bit value.
inline V shl128(const V& a, int sh) {
  uint64_t lo, hi;
  memcpy(&lo, a.b, 8); memcpy(&hi, a.b + 8, 8);
  if (sh) { hi = (hi << sh) | (lo >> (64 - sh)); lo <<= sh; }
  V r; memcpy(r.b, &lo, 8); memcpy(r.b + 8, &hi, 8);
  return r;
}
inline V shr128(const V& a, int sh) {
  uint64_t lo, hi;
  memcpy(&lo, a.b, 8); memcpy(&hi, a.b + 8, 8);
  if (sh) { lo = (lo >> sh) | (hi << (64 - sh)); hi >>= sh; }
  V r; memcpy(r.b, &lo, 8); memcpy(r.b + 8, &hi, 8);
  return r;
}
// ISA: count = low 3 bits of PPC byte 15; all bytes must agree, otherwise the result is undefined.
inline V vsl_isa(const V& a, const V& b) { return shl128(a, pb(b, 15) & 7); }
// SDK behaviour (kept): count from PPC byte 0 (x86 byte 15). Equal to the ISA for uniform vB.
inline V vsl_sdk(const V& a, const V& b) { return shl128(a, pb(b, 0) & 7); }
inline V vsr(const V& a, const V& b) { return shr128(a, pb(b, 15) & 7); }

// vperm: result PPC byte i = (vA || vB)[vC PPC byte i & 0x1F].
inline V vperm(const V& a, const V& b, const V& c) {
  V r;
  for (int i = 0; i < 16; i++) {
    int k = pb(c, i) & 0x1F;
    setpb(r, i, k < 16 ? pb(a, k) : pb(b, k - 16));
  }
  return r;
}

// vctuxs on raw float bits, scaled by 2^uimm, decoded with integer math (independent of MXCSR).
// NaN -> 0, negative -> 0 (saturate), >= 2^32 -> 0xFFFFFFFF, otherwise truncate toward zero.
// Zero/denormal inputs give 0 for every uimm <= 31 (largest denormal * 2^31 < 2^-95).
inline uint32_t vctuxs_bits(uint32_t x, int uimm = 0) {
  uint32_t sign = x >> 31, exp = (x >> 23) & 0xFF, man = x & 0x7FFFFF;
  if (exp == 0xFF) return man ? 0u : (sign ? 0u : 0xFFFFFFFFu);
  if (exp == 0 || sign) return 0;
  int e = int(exp) - 127 + uimm;
  if (e < 0) return 0;
  if (e >= 32) return 0xFFFFFFFFu;
  uint64_t m = (1u << 23) | man;
  return uint32_t(e >= 23 ? (m << (e - 23)) : (m >> (23 - e)));
}

// Table rows (x86 byte order), from the lvsl/lvsr/lvlx/lvrx definitions.
inline uint8_t mask_l(int s, int j) { return j >= s ? uint8_t(s + 15 - j) : 0xFF; }
inline uint8_t mask_r(int s, int j) { return j < s ? uint8_t(s - 1 - j) : 0xFF; }
inline uint8_t shift_l(int s, int j) { return uint8_t(s + 15 - j); }  // lvsl: PPC bytes sh..sh+15
inline uint8_t shift_r(int s, int j) { return uint8_t(31 - s - j); }  // lvsr: PPC bytes 16-sh..31-sh

}  // namespace ref
