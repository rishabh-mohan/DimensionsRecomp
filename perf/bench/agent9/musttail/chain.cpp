// chain.cpp - tail-chain depth test: chain_a -> chain_b -> chain_c -> chain_a ... N hops (default
// 1,000,000). Each is a generated-style guest function (DEFINE_REX_FUNC from the real generated
// headers: weak alias `name` -> body `__imp__name`, signature (PPCContext& __restrict, uint8_t*))
// ending in a guest tail call. Without musttail a hop that clang does not sibcall is call+ret, so
// the host stack grows by one frame per hop and overflows the default 1 MB main-thread stack; with
// [[clang::musttail]] every hop is a jmp and the depth is unbounded.
//   -DMUSTTAIL=0/1  today's text `f(ctx, base); return;` / the musttail_calls text
//   -DESCAPE=0/1    1: a local PPCRegister escapes to a hook by reference (the mid-asm hook shape),
//                   which stops clang's own sibcall optimisation even at -O2
#include "chain_types.h"

#include <cstdio>
#include <cstdlib>

#if MUSTTAIL
#define TAIL(f) [[clang::musttail]] return f(ctx, base)
#else
#define TAIL(f) \
  f(ctx, base); \
  return
#endif

#if ESCAPE
#define HOOK() chain_hook(r31, ctx)
#else
#define HOOK() ((void)0)
#endif

void chain_hook(PPCRegister& r31, PPCContext& ctx);
DECLARE_REX_FUNC(chain_a);
DECLARE_REX_FUNC(chain_b);
DECLARE_REX_FUNC(chain_c);

#define CHAIN_BODY(next)       \
  REX_FUNC_PROLOGUE();         \
  PPCRegister r31{};           \
  r31.u64 = ctx.r3.u64;        \
  HOOK();                      \
  ctx.r4.u64 = ctx.r4.u64 + 1; \
  ctx.r3.s64 = r31.s64 - 1;    \
  if (ctx.r3.s64 <= 0) return; \
  TAIL(next);

DEFINE_REX_FUNC(chain_a) { CHAIN_BODY(chain_b) }
DEFINE_REX_FUNC(chain_b) { CHAIN_BODY(chain_c) }
DEFINE_REX_FUNC(chain_c) { CHAIN_BODY(chain_a) }

extern "C" __declspec(dllimport) unsigned int __stdcall SetErrorMode(unsigned int);

int main(int argc, char** argv) {
  SetErrorMode(3);  // no Windows Error Reporting dialog on the expected stack overflow
  const long long n = argc > 1 ? std::atoll(argv[1]) : 1000000;
  static PPCContext ctx{};
  alignas(64) static uint8_t base[64];
  ctx.r3.s64 = n;
  ctx.r4.u64 = 0;
  ctx.r5.u64 = 0;
  chain_a(ctx, base);
  std::printf("depth %lld: %llu hops completed\n", n, (unsigned long long)ctx.r4.u64);
  return ctx.r4.u64 == (unsigned long long)n ? 0 : 1;
}
