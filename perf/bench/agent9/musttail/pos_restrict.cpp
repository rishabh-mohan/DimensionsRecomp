// pos_restrict.cpp - cases that must be ACCEPTED:
//  - a callee declared without __restrict (PPCFunc in rex/ppc/func.h has none), and
//  - an indirect musttail through PPCFunc* (what a REX_TAIL_CALL_INDIRECT_FUNC template macro
//    would need; codegen does not emit it today).
#include "legodimensions_pch.h"

extern "C" void no_restrict(PPCContext& ctx, uint8_t* base);
PPCFunc* volatile g_target;

DEFINE_REX_FUNC(pos_no_restrict) {
  REX_FUNC_PROLOGUE();
  [[clang::musttail]] return no_restrict(ctx, base);
}

DEFINE_REX_FUNC(pos_indirect) {
  REX_FUNC_PROLOGUE();
  PPCFunc* fn = g_target;
  [[clang::musttail]] return fn(ctx, base);
}
