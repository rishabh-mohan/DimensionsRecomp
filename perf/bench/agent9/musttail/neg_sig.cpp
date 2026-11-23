// neg_sig.cpp - a callee with a different signature (an extra parameter / a return value).
// Codegen never emits this (all guest functions and imports use REX_FUNC); shown to prove clang
// checks the match. Expected: rejected.
#include "legodimensions_pch.h"

extern "C" void three_args(PPCContext& __restrict ctx, uint8_t* base, uint32_t extra);
extern "C" int returns_int(PPCContext& __restrict ctx, uint8_t* base);

DEFINE_REX_FUNC(neg_sig) {
  REX_FUNC_PROLOGUE();
  [[clang::musttail]] return three_args(ctx, base, 0);
}

DEFINE_REX_FUNC(neg_ret) {
  REX_FUNC_PROLOGUE();
  [[clang::musttail]] return (void)returns_int(ctx, base);
}
