// chain_hook.cpp - a mid-asm hook: user code that receives a guest register by reference. It keeps
// no reference after returning (the hook contract), but the caller's compiler cannot see that,
// because this TU is opaque to it.
#include "chain_types.h"

void chain_hook(PPCRegister& r31, PPCContext& ctx) {
  r31.u64 = r31.u64 + ctx.r5.u64;  // r5 == 0: value unchanged, but written through the reference
}
