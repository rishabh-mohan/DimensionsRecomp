// neg_seh.cpp - an SEH-wrapped body. On Win32, SEH_TRY is `__try {` (rex/platform/exceptions.h),
// and codegen emits `SEH_TRY {` ... `SEH_CATCH ...` around the whole body. Expected: rejected.
#include "legodimensions_pch.h"

DECLARE_REX_FUNC(callee_a);

DEFINE_REX_FUNC(neg_seh) {
  REX_FUNC_PROLOGUE();
  __try {
    {
      ctx.r3.s64 = 1;
      [[clang::musttail]] return callee_a(ctx, base);
    }
  } __except (1) {
    ctx.r3.s64 = 0;
  }
}
