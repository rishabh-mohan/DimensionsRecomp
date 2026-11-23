// neg_tracy.cpp - the profiling build: REX_FUNC_PROLOGUE() declares a Tracy zone (non-trivial
// destructor) when REXGLUE_PROFILE_GUEST_FUNCTIONS and REXGLUE_ENABLE_PROFILING are defined.
// Expected: clang rejects the musttail. Compiled with -DREXGLUE_PROFILE_GUEST_FUNCTIONS
// -DREXGLUE_ENABLE_PROFILING -DTRACY_ENABLE and the SDK's Tracy include dir.
#include "legodimensions_pch.h"

DECLARE_REX_FUNC(callee_a);

DEFINE_REX_FUNC(neg_tracy) {
  REX_FUNC_PROLOGUE();
  [[clang::musttail]] return callee_a(ctx, base);
}
