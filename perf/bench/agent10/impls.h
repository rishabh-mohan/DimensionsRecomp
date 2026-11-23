// Agent 10 (task #9): uniform wrappers around each helper implementation, plus the exact emitted
// forms from src/codegen (builders/context.cpp:521 emit_vec_var_shift, vector.cpp vrlh/vctuxs).
#pragma once
#include "old_intrinsics.h"   // namespace old_ppc: verbatim intrinsics.h at pin 2897c31
#include <rex/ppc/intrinsics.h>  // namespace rex::ppc: whatever the SDK header holds now
#include "variants.h"         // namespace cand

using m128i = simde__m128i;
using m128 = simde__m128;

#define IMPL_FWD(NS)                                                                       \
  static m128i sllv16(m128i a, m128i c) { return NS::simde_mm_sllv_epi16(a, c); }         \
  static m128i srlv16(m128i a, m128i c) { return NS::simde_mm_srlv_epi16(a, c); }         \
  static m128i srav16(m128i a, m128i c) { return NS::simde_mm_srav_epi16(a, c); }         \
  static m128i sllv8(m128i a, m128i c) { return NS::simde_mm_sllv_epi8(a, c); }           \
  static m128i vslo(m128i a, m128i b) { return NS::simde_mm_vslo(a, b); }                 \
  static m128i vsro(m128i a, m128i b) { return NS::simde_mm_vsro(a, b); }                 \
  static m128i vsl(m128i a, m128i b) { return NS::simde_mm_vsl(a, b); }                   \
  static m128i vsr(m128i a, m128i b) { return NS::simde_mm_vsr(a, b); }                   \
  static m128i perm(m128i a, m128i b, m128i c) { return NS::simde_mm_perm_epi8_(a, b, c); } \
  static m128i vctuxs(m128 a) { return NS::simde_mm_vctuxs(a); }                          \
  static const uint8_t* maskL() { return NS::VectorMaskL; }                               \
  static const uint8_t* maskR() { return NS::VectorMaskR; }                               \
  static const uint8_t* shiftL() { return NS::VectorShiftTableL; }                        \
  static const uint8_t* shiftR() { return NS::VectorShiftTableR; }

struct OldImpl {
  static constexpr const char* name = "old";
  IMPL_FWD(old_ppc)
};
struct CurImpl {
  static constexpr const char* name = "sdk";
  IMPL_FWD(rex::ppc)
};
// All-vector candidates, SSE4.1 element shifts.
struct CandImpl {
  static constexpr const char* name = "cand";
  static m128i sllv16(m128i a, m128i c) { return cand::sllv_epi16(a, c); }
  static m128i srlv16(m128i a, m128i c) { return cand::srlv_epi16(a, c); }
  static m128i srav16(m128i a, m128i c) { return cand::srav_epi16(a, c); }
  static m128i sllv8(m128i a, m128i c) { return cand::sllv_epi8(a, c); }
  static m128i vslo(m128i a, m128i b) { return cand::vslo(a, b); }
  static m128i vsro(m128i a, m128i b) { return cand::vsro(a, b); }
  static m128i vsl(m128i a, m128i b) { return cand::vsl(a, b); }
  static m128i vsr(m128i a, m128i b) { return old_ppc::simde_mm_vsr(a, b); }
  static m128i perm(m128i a, m128i b, m128i c) { return cand::perm(a, b, c); }
  static m128i vctuxs(m128 a) { return cand::vctuxs(a); }
  static const uint8_t* maskL() { return old_ppc::VectorMaskL; }
  static const uint8_t* maskR() { return old_ppc::VectorMaskR; }
  static const uint8_t* shiftL() { return old_ppc::VectorShiftTableL; }
  static const uint8_t* shiftR() { return old_ppc::VectorShiftTableR; }
};
// Alternatives: LUT vslo/vsro, maxadd vctuxs, and (if native) AVX2 element shifts.
struct AltImpl : CandImpl {
  static constexpr const char* name = "alt";
  static m128i vslo(m128i a, m128i b) { return cand::vslo_lut(a, b); }
  static m128i vsro(m128i a, m128i b) { return cand::vsro_lut(a, b); }
  static m128i vctuxs(m128 a) { return cand::vctuxs_maxadd(a); }
#if defined(CAND_HAVE_AVX2)
  static m128i sllv16(m128i a, m128i c) { return cand::sllv_epi16_avx2(a, c); }
  static m128i srlv16(m128i a, m128i c) { return cand::srlv_epi16_avx2(a, c); }
  static m128i srav16(m128i a, m128i c) { return cand::srav_epi16_avx2(a, c); }
#endif
};

// Emitted forms (generated code masks the count before calling the helper).
template <class I> inline m128i e_vslb(m128i a, m128i b) {
  return I::sllv8(a, simde_mm_and_si128(b, simde_mm_set1_epi8(0x7)));
}
template <class I> inline m128i e_vslh(m128i a, m128i b) {
  return I::sllv16(a, simde_mm_and_si128(b, simde_mm_set1_epi16(0xF)));
}
template <class I> inline m128i e_vsrh(m128i a, m128i b) {
  return I::srlv16(a, simde_mm_and_si128(b, simde_mm_set1_epi16(0xF)));
}
template <class I> inline m128i e_vsrah(m128i a, m128i b) {
  return I::srav16(a, simde_mm_and_si128(b, simde_mm_set1_epi16(0xF)));
}
template <class I> inline m128i e_vrlh(m128i a, m128i b) {
  m128i sh = simde_mm_and_si128(b, simde_mm_set1_epi16(0xF));
  m128i rsh = simde_mm_sub_epi16(simde_mm_set1_epi16(16), sh);
  return simde_mm_or_si128(I::sllv16(a, sh), I::srlv16(a, rsh));
}
template <class I> inline m128i e_vctuxs(m128 v, int uimm) {
  return I::vctuxs(uimm ? simde_mm_mul_ps(v, simde_mm_set1_ps(float(1u << uimm))) : v);
}

// ref::V <-> m128i
#include "ppc_ref.h"
inline m128i ld(const ref::V& v) { return simde_mm_load_si128(reinterpret_cast<const m128i*>(v.b)); }
inline m128 ldps(const ref::V& v) { return simde_mm_load_ps(reinterpret_cast<const float*>(v.b)); }
inline ref::V st(m128i x) {
  ref::V v;
  simde_mm_store_si128(reinterpret_cast<m128i*>(v.b), x);
  return v;
}
