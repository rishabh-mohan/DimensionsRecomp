// Agent 10 (task #9): candidate helper implementations (namespace cand). The winners are copied into
// rex/ppc/intrinsics.h; test_intrinsics.cpp checks every candidate against ppc_ref.h, bench_intrinsics.cpp
// times them against old_ppc (the pin-2897c31 copy).
#pragma once
#include <cstdint>
#include <cstring>

#include <simde/x86/avx2.h>
#include <simde/x86/sse4.1.h>

namespace cand {

//--- vslo / vsro: one pshufb with a computed index, no memory round trip -------------------------
// n = bits 3..6 of x86 byte 0 (PPC byte 15), broadcast to every byte.
inline simde__m128i octet_count(simde__m128i b) {
  simde__m128i n = simde_mm_and_si128(simde_mm_srli_epi16(b, 3), simde_mm_set1_epi8(0xF));
  return simde_mm_shuffle_epi8(n, simde_mm_setzero_si128());
}
// x86 byte i takes byte i-n; negative indices have bit 7 set, and pshufb writes 0.
inline simde__m128i vslo(simde__m128i a, simde__m128i b) {
  simde__m128i idx = simde_mm_sub_epi8(
      simde_mm_setr_epi8(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15), octet_count(b));
  return simde_mm_shuffle_epi8(a, idx);
}
// x86 byte i takes byte i+n; 0x70+i+n reaches 0x80 (zero) exactly when i+n > 15.
inline simde__m128i vsro(simde__m128i a, simde__m128i b) {
  simde__m128i idx = simde_mm_add_epi8(
      simde_mm_setr_epi8(0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x7B, 0x7C,
                         0x7D, 0x7E, 0x7F),
      octet_count(b));
  return simde_mm_shuffle_epi8(a, idx);
}
// Alternative: sliding 48-byte window (GPR extract + unaligned load).
alignas(16) inline constexpr uint8_t kOctetWindow[48] = {
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80,
    0,    1,    2,    3,    4,    5,    6,    7,    8,    9,    10,   11,   12,   13,   14,   15,
    0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80};
// simde's portable simde_mm_loadu_si128 (SIMDE_NO_NATIVE) reads through a packed struct whose member
// keeps the union's 16-byte alignment, and clang 23 emits movaps for it: an unaligned window load
// faults (0xC0000005). Bench-only: use memcpy there. The SDK headers never call loadu_si128.
inline simde__m128i octet_window(int off) {
#if defined(SIMDE_X86_SSE2_NATIVE)
  return simde_mm_loadu_si128(kOctetWindow + off);
#else
  simde__m128i r;
  memcpy(&r, kOctetWindow + off, sizeof(r));
  return r;
#endif
}
inline simde__m128i vslo_lut(simde__m128i a, simde__m128i b) {
  int n = (simde_mm_cvtsi128_si32(b) >> 3) & 0xF;
  return simde_mm_shuffle_epi8(a, octet_window(16 - n));
}
inline simde__m128i vsro_lut(simde__m128i a, simde__m128i b) {
  int n = (simde_mm_cvtsi128_si32(b) >> 3) & 0xF;
  return simde_mm_shuffle_epi8(a, octet_window(16 + n));
}

//--- vperm: 15 - (c & 15) == ~c & 15 -------------------------------------------------------------
inline simde__m128i perm(simde__m128i a, simde__m128i b, simde__m128i c) {
  simde__m128i e = simde_mm_andnot_si128(c, simde_mm_set1_epi8(0xF));
  return simde_mm_blendv_epi8(simde_mm_shuffle_epi8(a, e), simde_mm_shuffle_epi8(b, e),
                              simde_mm_slli_epi32(c, 3));
}

//--- vsl: branch-free. Count = low 3 bits of x86 byte 15 (the SDK's current choice, kept). -------
// Dwords 0, 1, 3 of sll_epi64(a) are already right; dword 2 also needs the carry out of the low
// qword, which is dword 3 of sll_epi64(a << 32).
inline simde__m128i vsl(simde__m128i a, simde__m128i b) {
  simde__m128i n = simde_mm_and_si128(simde_mm_srli_si128(b, 15), simde_mm_cvtsi32_si128(7));
  simde__m128 lo = simde_mm_castsi128_ps(simde_mm_sll_epi64(a, n));
  simde__m128 hi = simde_mm_castsi128_ps(simde_mm_sll_epi64(simde_mm_slli_si128(a, 4), n));
  return simde_mm_castps_si128(simde_mm_insert_ps(lo, hi, 0xE0));
}

//--- vctuxs ---------------------------------------------------------------------------------------
// max_ps(src, 0) maps NaN, -0 and negatives to +0. Lanes >= 2^31 convert (src - 2^31) and set bit 31;
// lanes >= 2^32 (and +inf) are forced to all-ones. cvtt never sees an out-of-range value it keeps.
inline simde__m128i vctuxs(simde__m128 src) {
  const simde__m128 two31 = simde_mm_set1_ps(2147483648.0f);
  simde__m128 clamped = simde_mm_max_ps(src, simde_mm_setzero_ps());
  simde__m128 high = simde_mm_cmpge_ps(src, two31);
  simde__m128i r = simde_mm_cvttps_epi32(simde_mm_sub_ps(clamped, simde_mm_and_ps(high, two31)));
  r = simde_mm_or_si128(r, simde_mm_slli_epi32(simde_mm_castps_si128(high), 31));
  return simde_mm_or_si128(r,
                           simde_mm_castps_si128(simde_mm_cmpge_ps(src, simde_mm_set1_ps(4294967296.0f))));
}
// Alternative: relies on cvtt returning 0x80000000 for >= 2^31 (x86 only; not with SIMDE_FAST_CONVERSION_RANGE).
inline simde__m128i vctuxs_maxadd(simde__m128 src) {
  const simde__m128 two31 = simde_mm_set1_ps(2147483648.0f);
  simde__m128 clamped = simde_mm_max_ps(src, simde_mm_setzero_ps());
  simde__m128i r = simde_mm_add_epi32(
      simde_mm_cvttps_epi32(clamped),
      simde_mm_max_epi32(simde_mm_cvttps_epi32(simde_mm_sub_ps(clamped, two31)), simde_mm_setzero_si128()));
  return simde_mm_or_si128(r,
                           simde_mm_castps_si128(simde_mm_cmpge_ps(src, simde_mm_set1_ps(4294967296.0f))));
}

//--- Variable element shifts, SSE4.1 forms, exact for every count --------------------------------
// Copy the low byte of each 16-bit lane into its high byte (counts here are <= 16).
inline simde__m128i dup_lo_byte16(simde__m128i n) {
  return simde_mm_shuffle_epi8(
      n, simde_mm_setr_epi8(0, 0, 2, 2, 4, 4, 6, 6, 8, 8, 10, 10, 12, 12, 14, 14));
}
// a * 2^n. pow2 low byte = table[n] via index n+0x70 (n=16 -> 0x80 -> 0); high byte via n+0x68.
inline simde__m128i sllv_epi16(simde__m128i a, simde__m128i count) {
  simde__m128i n = simde_mm_min_epu16(count, simde_mm_set1_epi16(16));
  simde__m128i idx = simde_mm_add_epi8(dup_lo_byte16(n), simde_mm_set1_epi16(0x6870));
  simde__m128i pow2 = simde_mm_shuffle_epi8(
      simde_mm_setr_epi8(1, 2, 4, 8, 16, 32, 64, char(128), 0, 0, 0, 0, 0, 0, 0, 0), idx);
  return simde_mm_mullo_epi16(a, pow2);
}
// mulhi(a, 2^(16-n)) for n = 1..16 (m(16) = 1 gives 0); n = 0 passes a through.
// Index bytes are n-9 (low) and n-1 (high), subtracted byte-wise.
inline simde__m128i srlv_epi16(simde__m128i a, simde__m128i count) {
  simde__m128i n = simde_mm_min_epu16(count, simde_mm_set1_epi16(16));
  simde__m128i idx = simde_mm_sub_epi8(dup_lo_byte16(n), simde_mm_set1_epi16(0x0109));
  simde__m128i m = simde_mm_shuffle_epi8(
      simde_mm_setr_epi8(char(128), 64, 32, 16, 8, 4, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0), idx);
  return simde_mm_or_si128(simde_mm_mulhi_epu16(a, m),
                           simde_mm_and_si128(a, simde_mm_cmpeq_epi16(count, simde_mm_setzero_si128())));
}
// Arithmetic shift = logical shift of (a ^ sign) re-xored with sign; counts >= 16 give the sign fill.
inline simde__m128i srav_epi16(simde__m128i a, simde__m128i count) {
  simde__m128i s = simde_mm_srai_epi16(a, 15);
  return simde_mm_xor_si128(srlv_epi16(simde_mm_xor_si128(a, s), count), s);
}
// Bytes: multiply even and odd bytes separately by 2^n (n >= 8 -> table[8] = 0).
inline simde__m128i sllv_epi8(simde__m128i a, simde__m128i count) {
  simde__m128i pow2 = simde_mm_shuffle_epi8(
      simde_mm_setr_epi8(1, 2, 4, 8, 16, 32, 64, char(128), 0, 0, 0, 0, 0, 0, 0, 0),
      simde_mm_min_epu8(count, simde_mm_set1_epi8(8)));
  const simde__m128i lo = simde_mm_set1_epi16(0x00FF);
  simde__m128i even = simde_mm_and_si128(simde_mm_mullo_epi16(a, simde_mm_and_si128(pow2, lo)), lo);
  simde__m128i odd = simde_mm_mullo_epi16(simde_mm_andnot_si128(lo, a), simde_mm_srli_epi16(pow2, 8));
  return simde_mm_or_si128(even, odd);
}

//--- Variable element shifts, native AVX2 forms (even/odd 16-bit lanes via 32-bit shifts) --------
#if defined(SIMDE_X86_AVX2_NATIVE)
#define CAND_HAVE_AVX2 1
inline simde__m128i sllv_epi16_avx2(simde__m128i a, simde__m128i count) {
  const simde__m128i lo = simde_mm_set1_epi32(0xFFFF);
  simde__m128i even = simde_mm_sllv_epi32(a, simde_mm_and_si128(count, lo));
  simde__m128i odd = simde_mm_sllv_epi32(simde_mm_andnot_si128(lo, a), simde_mm_srli_epi32(count, 16));
  return simde_mm_blend_epi16(even, odd, 0xAA);
}
inline simde__m128i srlv_epi16_avx2(simde__m128i a, simde__m128i count) {
  const simde__m128i lo = simde_mm_set1_epi32(0xFFFF);
  simde__m128i even = simde_mm_srlv_epi32(simde_mm_and_si128(a, lo), simde_mm_and_si128(count, lo));
  simde__m128i odd = simde_mm_srlv_epi32(a, simde_mm_srli_epi32(count, 16));
  return simde_mm_blend_epi16(even, odd, 0xAA);
}
inline simde__m128i srav_epi16_avx2(simde__m128i a, simde__m128i count) {
  const simde__m128i lo = simde_mm_set1_epi32(0xFFFF);
  simde__m128i even = simde_mm_srav_epi32(simde_mm_srai_epi32(simde_mm_slli_epi32(a, 16), 16),
                                          simde_mm_and_si128(count, lo));
  simde__m128i odd = simde_mm_srav_epi32(a, simde_mm_srli_epi32(count, 16));
  return simde_mm_blend_epi16(even, odd, 0xAA);
}
#endif

}  // namespace cand
