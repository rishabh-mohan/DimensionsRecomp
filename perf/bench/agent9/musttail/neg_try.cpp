// neg_try.cpp - the non-Win32 SEH_TRY: `{ ::rex::SehGuard __seh_guard; try` (a local with a
// non-trivial destructor plus a C++ try block). Expected: rejected.
#include "legodimensions_pch.h"

DECLARE_REX_FUNC(callee_a);

struct SehGuardLike {  // ::rex::SehGuard on POSIX restores seh_active() in its destructor
  SehGuardLike();
  ~SehGuardLike();
};

DEFINE_REX_FUNC(neg_try) {
  REX_FUNC_PROLOGUE();
  try {
    ctx.r3.s64 = 1;
    [[clang::musttail]] return callee_a(ctx, base);
  } catch (...) {
    ctx.r3.s64 = 0;
  }
}

DEFINE_REX_FUNC(neg_guard) {
  REX_FUNC_PROLOGUE();
  SehGuardLike guard;
  [[clang::musttail]] return callee_a(ctx, base);
}
