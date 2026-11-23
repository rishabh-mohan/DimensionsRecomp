// Microbench for rexlego/src/native_atomics.cpp Enabled(): the old
// function-local `static const bool` (a thread-safe static, so every call
// tests the init guard against the thread's _Init_thread_epoch in TLS) against
// the new latched std::atomic<int8_t> (one relaxed byte load). Both Enabled()
// bodies are copied verbatim (old: build/agent8/orig/native_atomics.cpp, new:
// DimensionsRecomp/rexlego/src/native_atomics.cpp), as are SetCr0() and the
// big-endian CAS Add() of the hooks; Add() is kept noinline.
//
//   bench_atomics.exe verify unset|0|1
//       LEGO_NATIVE_ATOMICS semantics (set with _putenv_s before the first
//       call): old == new == expected, both latch, hooks route correctly.
//   bench_atomics.exe time [rounds=5] [calls=100000000] [contended_calls=2500000]
//       ns per hook call single-threaded (old / new / no check at all), ns per
//       bare Enabled() call, and a 2-thread contended run on one word.
#include <windows.h>
#include <immintrin.h>

#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <thread>
#include <vector>

#include "../common/bench_util.h"

using u8 = uint8_t;
using u32 = uint32_t;
using u64 = uint64_t;

// Only the PPCContext members the hooks touch (the SDK's context has the full
// register file; the layout does not change the code being measured).
union PPCRegister {
  int32_t s32;
  uint32_t u32;
  int64_t s64;
  uint64_t u64;
};
struct PPCXERRegister {
  uint8_t so;
  uint8_t ov;
  uint8_t ca;
};
struct PPCCRRegister {
  uint8_t lt;
  uint8_t gt;
  uint8_t eq;
  uint8_t so;
  template <typename T>
  void compare(T left, T right, const PPCXERRegister& xer) {
    lt = left < right;
    gt = left > right;
    eq = left == right;
    so = xer.so;
  }
};
struct PPCContext {
  PPCRegister r3;
  PPCRegister r4;
  PPCRegister r5;
  PPCCRRegister cr0;
  PPCCRRegister cr6;
  PPCXERRegister xer;
};
// Guest address -> host pointer: base of the guest mapping + 32-bit address.
#define REX_RAW_ADDR(addr) (base + uint32_t(addr))

namespace old_variant {
// Verbatim from build/agent8/orig/native_atomics.cpp.
bool Enabled() {
  static const bool enabled = [] {
    const char* value = std::getenv("LEGO_NATIVE_ATOMICS");
    return !value || std::strcmp(value, "0") != 0;
  }();
  return enabled;
}
}  // namespace old_variant

namespace new_variant {
// Verbatim from DimensionsRecomp/rexlego/src/native_atomics.cpp.
std::atomic<int8_t> g_enabled{-1};

bool Enabled() {
  const int8_t latched = g_enabled.load(std::memory_order_relaxed);
  if (latched >= 0) [[likely]] return latched != 0;
  const char* value = std::getenv("LEGO_NATIVE_ATOMICS");
  const bool enabled = !value || std::strcmp(value, "0") != 0;
  g_enabled.store(enabled ? 1 : 0, std::memory_order_relaxed);
  return enabled;
}
}  // namespace new_variant

namespace {

void SetCr0(PPCContext& ctx) {
  ctx.cr0.lt = 0;
  ctx.cr0.gt = 0;
  ctx.cr0.eq = 1;
  ctx.cr0.so = ctx.xer.so;
}

__attribute__((noinline)) void Add(PPCContext& ctx, u8* base, u32 delta) {
  auto* p = reinterpret_cast<u32*>(REX_RAW_ADDR(ctx.r3.u32));
  std::atomic_ref<u32> word(*p);
  u32 raw = word.load(std::memory_order_relaxed);
  for (;;) {
    const u32 next = __builtin_bswap32(__builtin_bswap32(raw) + delta);
    if (word.compare_exchange_weak(raw, next, std::memory_order_seq_cst,
                                  std::memory_order_relaxed)) {
      ctx.r3.u64 = __builtin_bswap32(next);
      SetCr0(ctx);
      return;
    }
  }
}
static_assert(std::atomic_ref<u32>::is_always_lock_free);

std::atomic<uint64_t> g_fallback_calls{0};

}  // namespace

// Stand-in for the recompiled guest routine (__imp__sub_82A2A160).
extern "C" __attribute__((noinline)) void imp_fallback(PPCContext& __restrict ctx, u8* base) {
  (void)base;
  g_fallback_calls.fetch_add(1, std::memory_order_relaxed);
  ctx.r3.u64 = 0;
}

// REX_HOOK_RAW(sub_82A2A160) with each Enabled(), and with no check at all.
extern "C" __attribute__((noinline)) void hook_old(PPCContext& __restrict ctx, u8* base) {
  if (!old_variant::Enabled()) { imp_fallback(ctx, base); return; }
  Add(ctx, base, 1);
}
extern "C" __attribute__((noinline)) void hook_new(PPCContext& __restrict ctx, u8* base) {
  if (!new_variant::Enabled()) { imp_fallback(ctx, base); return; }
  Add(ctx, base, 1);
}
extern "C" __attribute__((noinline)) void hook_nocheck(PPCContext& __restrict ctx, u8* base) {
  Add(ctx, base, 1);
}
extern "C" __attribute__((noinline)) bool enabled_old() { return old_variant::Enabled(); }
extern "C" __attribute__((noinline)) bool enabled_new() { return new_variant::Enabled(); }

namespace {

using HookFn = decltype(&hook_old);
using EnabledFn = decltype(&enabled_old);

constexpr const char* kBench = "atomics";
constexpr u32 kAddr = 0x40;
alignas(64) u8 g_guest[4096];

u32 LoadBE(u32 addr) {
  return __builtin_bswap32(std::atomic_ref<u32>(*reinterpret_cast<u32*>(g_guest + addr)).load());
}
void StoreBE(u32 addr, u32 v) {
  std::atomic_ref<u32>(*reinterpret_cast<u32*>(g_guest + addr)).store(__builtin_bswap32(v));
}

template <HookFn F>
__attribute__((noinline)) double TimeSingle(uint64_t n, bool& count_ok) {
  PPCContext ctx{};
  u8* base = g_guest;
  const u32 start = LoadBE(kAddr);
  const int64_t t0 = benchutil::NowNs();
  for (uint64_t i = 0; i < n; ++i) {
    ctx.r3.u64 = kAddr;
    F(ctx, base);
  }
  const int64_t t1 = benchutil::NowNs();
  count_ok = LoadBE(kAddr) == u32(start + n) && ctx.r3.u32 == u32(start + n) && ctx.cr0.eq == 1;
  return double(t1 - t0) / double(n);
}

template <EnabledFn E>
__attribute__((noinline)) double TimeEnabled(uint64_t n, uint64_t& sink) {
  uint64_t s = 0;
  const int64_t t0 = benchutil::NowNs();
  for (uint64_t i = 0; i < n; ++i) {
    s += E() ? 1 : 0;
  }
  const int64_t t1 = benchutil::NowNs();
  sink += s;
  return double(t1 - t0) / double(n);
}

// Two threads hammering one word, as two guest threads on one lock count would.
template <HookFn F>
double TimeContended(uint64_t n, bool& count_ok) {
  std::atomic<int> ready{0};
  std::atomic<bool> go{false};
  const u32 start = LoadBE(kAddr);
  auto body = [&] {
    PPCContext ctx{};
    u8* base = g_guest;
    ready.fetch_add(1);
    while (!go.load(std::memory_order_acquire)) {
      _mm_pause();
    }
    for (uint64_t i = 0; i < n; ++i) {
      ctx.r3.u64 = kAddr;
      F(ctx, base);
    }
  };
  std::thread a(body);
  std::thread b(body);
  while (ready.load() < 2) {
    std::this_thread::yield();
  }
  const int64_t t0 = benchutil::NowNs();
  go.store(true, std::memory_order_release);
  a.join();
  b.join();
  const int64_t t1 = benchutil::NowNs();
  count_ok = LoadBE(kAddr) == u32(start + 2 * n);
  return double(t1 - t0) / double(n);
}

const char* VariantName(int v) { return v == 0 ? "old" : v == 1 ? "new" : "nocheck"; }

int RunVerify(const std::string& mode) {
  // Exactly what the game sees: the variable is applied (or removed) with
  // _putenv_s before the first hook call.
  const char* value = mode == "unset" ? "" : mode.c_str();
  if (_putenv_s("LEGO_NATIVE_ATOMICS", value) != 0) {
    std::fprintf(stderr, "_putenv_s failed\n");
    return 2;
  }
  const char* seen = std::getenv("LEGO_NATIVE_ATOMICS");
  const bool expected = mode != "0";
  const bool o = enabled_old();
  const bool n = enabled_new();
  const std::string tag = "verify_" + mode;
  const std::string detail = std::string("env=") + (seen ? seen : "<unset>") +
                             " expected=" + (expected ? "1" : "0") + " old=" + (o ? "1" : "0") +
                             " new=" + (n ? "1" : "0");
  benchutil::Check(kBench, "both", tag + "_old_eq_expected", o == expected, detail);
  benchutil::Check(kBench, "both", tag + "_new_eq_expected", n == expected, detail);
  benchutil::Check(kBench, "both", tag + "_old_eq_new", o == n, detail);

  // Latched: flipping the variable afterwards changes neither.
  _putenv_s("LEGO_NATIVE_ATOMICS", expected ? "0" : "1");
  const bool o2 = enabled_old();
  const bool n2 = enabled_new();
  benchutil::Check(kBench, "both", tag + "_latched", o2 == o && n2 == n,
                   std::string("after_flip old=") + (o2 ? "1" : "0") + " new=" + (n2 ? "1" : "0"));

  // Routing: enabled -> native BE increment; disabled -> the guest fallback.
  bool routing_ok = true;
  for (int v = 0; v < 2; ++v) {
    StoreBE(kAddr, 41);
    g_fallback_calls.store(0);
    PPCContext ctx{};
    ctx.r3.u64 = kAddr;
    (v == 0 ? hook_old : hook_new)(ctx, g_guest);
    const bool ok = expected ? (LoadBE(kAddr) == 42 && ctx.r3.u64 == 42 && ctx.cr0.eq == 1 &&
                                g_fallback_calls.load() == 0)
                             : (LoadBE(kAddr) == 41 && g_fallback_calls.load() == 1);
    routing_ok = routing_ok && ok;
  }
  benchutil::Check(kBench, "both", tag + "_hook_routing", routing_ok, "");
  return 0;
}

int RunTime(int rounds, uint64_t calls, uint64_t contended_calls) {
  _putenv_s("LEGO_NATIVE_ATOMICS", "");  // unset = enabled, the default
  uint64_t sink = 0;
  sink += enabled_old() + enabled_new();  // latch both before timing
  StoreBE(kAddr, 0);
  bool single_ok = true;
  bool contended_ok = true;
  for (int r = 0; r < rounds; ++r) {
    const int order[3] = {(r & 1) ? 2 : 0, 1, (r & 1) ? 0 : 2};
    for (int v : order) {
      bool ok = false;
      const double ns = v == 0   ? TimeSingle<hook_old>(calls, ok)
                        : v == 1 ? TimeSingle<hook_new>(calls, ok)
                                 : TimeSingle<hook_nocheck>(calls, ok);
      single_ok = single_ok && ok;
      benchutil::Result(kBench, VariantName(v), "single_ns", ns, "ns/call");
    }
    for (int i = 0; i < 2; ++i) {
      const bool old_first = ((r + i) & 1) == 0;
      const double ns =
          old_first ? TimeEnabled<enabled_old>(calls, sink) : TimeEnabled<enabled_new>(calls, sink);
      benchutil::Result(kBench, old_first ? "old" : "new", "enabled_only_ns", ns, "ns/call");
    }
    for (int v : order) {
      bool ok = false;
      const double ns = v == 0   ? TimeContended<hook_old>(contended_calls, ok)
                        : v == 1 ? TimeContended<hook_new>(contended_calls, ok)
                                 : TimeContended<hook_nocheck>(contended_calls, ok);
      contended_ok = contended_ok && ok;
      benchutil::Result(kBench, VariantName(v), "contended_ns", ns, "ns/call/thread");
    }
  }
  benchutil::Check(kBench, "all", "single_counts", single_ok, "every single-thread run added exactly N");
  benchutil::Check(kBench, "all", "contended_counts", contended_ok, "every 2-thread run added exactly 2N");
  benchutil::Check(kBench, "all", "no_fallback_when_enabled", g_fallback_calls.load() == 0,
                   "fallback_calls=" + std::to_string(g_fallback_calls.load()));
  std::printf("SINK %llu\n", (unsigned long long)sink);
  return 0;
}

}  // namespace

int main(int argc, char** argv) {
  const std::string mode = argc > 1 ? argv[1] : "time";
  std::printf("INFO bench=atomics mode=%s pid=%lu\n", mode.c_str(), GetCurrentProcessId());
  if (mode == "verify" && argc > 2) {
    return RunVerify(argv[2]);
  }
  if (mode == "time") {
    const int rounds = argc > 2 ? std::atoi(argv[2]) : 5;
    const uint64_t calls = argc > 3 ? std::strtoull(argv[3], nullptr, 10) : 100000000ull;
    const uint64_t contended = argc > 4 ? std::strtoull(argv[4], nullptr, 10) : 2500000ull;
    return RunTime(rounds, calls, contended);
  }
  std::fprintf(stderr, "usage: %s verify unset|0|1 | time [rounds] [calls] [contended_calls]\n",
               argv[0]);
  return 1;
}
