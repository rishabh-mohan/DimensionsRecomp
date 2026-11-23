// chain_types.h - the real generated headers, or (-DCHAIN_NO_PCH, fallback only if the real-pch
// build does not link) a minimal stand-in with the same signature and the same weak-alias
// DEFINE_REX_FUNC as the generated legodimensions_pch.h (non-Apple branch).
#pragma once
#ifdef CHAIN_NO_PCH
#include <cstdint>
struct PPCRegister {
  union {
    uint64_t u64;
    int64_t s64;
    uint32_t u32;
    int32_t s32;
  };
};
struct PPCContext {
  PPCRegister r3, r4, r5;
};
#define REX_FUNC(x) void x([[maybe_unused]] PPCContext& __restrict ctx, uint8_t* base)
#define REX_EXTERN(x) extern "C" REX_FUNC(x)
#define DECLARE_REX_FUNC(name) \
  REX_EXTERN(name);            \
  REX_EXTERN(__imp__##name)
#define DEFINE_REX_FUNC(name)                                \
  __attribute__((alias("__imp__" #name)))                    \
  __attribute__((weak, noinline)) extern "C" REX_FUNC(name); \
  REX_EXTERN(__imp__##name)
#define REX_FUNC_PROLOGUE() ((void)0)
#else
#include "legodimensions_pch.h"
#endif
