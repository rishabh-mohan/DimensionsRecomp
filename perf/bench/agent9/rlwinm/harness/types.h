// Shared types for the rlwinm/rlwnm/rlwimi lowering equivalence harness.
#pragma once
#include <cstdint>

// Copy of rex::ppc Register (include/rex/ppc/context.h).
union Reg {
  int8_t s8;
  uint8_t u8;
  int16_t s16;
  uint16_t u16;
  int32_t s32;
  uint32_t u32;
  int64_t s64;
  uint64_t u64;
  float f32;
  double f64;
};

using Fn2 = void (*)(Reg& ra, Reg& rs);
using Fn3 = void (*)(Reg& ra, Reg& rs, Reg& rb);

struct Case2 {  // rlwinm / rlwimi
  uint8_t sh, mb, me, form;
  Fn2 oldf, newf;
};
struct Case3 {  // rlwnm
  uint8_t mb, me, form;
  Fn3 oldf, newf;
};
