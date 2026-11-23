// Unit-style tests for rex/threading_timeout.h, the NT timeout conversion used by
// XObject::TimeoutTicksToMs (cvar wait_timeout_round_up) and XThread::Delay
// (cvar precise_guest_sleep). Compile-time checks (static_assert) plus a runtime
// table comparing the new conversion with a replica of the old one.
//
// Build (single-threaded, from the workspace root, in env\devshell.ps1):
//   cl /nologo /O2 /std:c++20 /EHsc /W4 /I DimensionsRecomp\rexglue-sdk\include ^
//      bench\agent11\test_timeouts.cpp /Fe:build\agent11\test_timeouts.exe /Fo:build\agent11\
// Exit code = number of failed cases.

#include <rex/threading_timeout.h>

#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <limits>

using namespace rex::thread;

constexpr int64_t kInt64Min = std::numeric_limits<int64_t>::min();
constexpr uint64_t kUint64Max = std::numeric_limits<uint64_t>::max();

// ---- compile-time checks ----------------------------------------------------
static_assert(NtTimeoutToRelative100ns(0, 123) == 0, "0 = poll");
static_assert(NtTimeoutToRelative100ns(-1, 0) == 1, "relative 100 ns");
static_assert(NtTimeoutToRelative100ns(kInt64Min, 0) == (uint64_t(1) << 63), "no overflow");
static_assert(NtTimeoutToRelative100ns(1000, 999) == 1, "absolute, 100 ns ahead");
static_assert(NtTimeoutToRelative100ns(1000, 1000) == 0, "absolute, due now");
static_assert(NtTimeoutToRelative100ns(1000, 2000) == 0, "absolute, already past");
static_assert(Relative100nsToMillis(0) == 0, "");
static_assert(Relative100nsToMillis(1) == 1, "round up");
static_assert(Relative100nsToMillis(9999) == 1, "round up");
static_assert(Relative100nsToMillis(10000) == 1, "exact");
static_assert(Relative100nsToMillis(10001) == 2, "round up");
static_assert(Relative100nsToMillis(0xFFFFFFFDull * 10000) == 0xFFFFFFFDu, "largest exact");
static_assert(Relative100nsToMillis(0xFFFFFFFEull * 10000) == kMaxFiniteWaitMillis, "");
static_assert(Relative100nsToMillis(0xFFFFFFFFull * 10000) == kMaxFiniteWaitMillis,
              "finite never becomes INFINITE");
static_assert(Relative100nsToMillis(kUint64Max) == kMaxFiniteWaitMillis, "saturates");
static_assert(Relative100nsToMicros(0) == 0, "");
static_assert(Relative100nsToMicros(1) == 1, "round up");
static_assert(Relative100nsToMicros(10) == 1, "exact");
static_assert(Relative100nsToMicros(11) == 2, "round up");
static_assert(Relative100nsToMicros(kUint64Max) == kUint64Max / 10 + 1, "no overflow");
static_assert(NtTimeoutToMillis(-10000, 0) == 1, "");
static_assert(NtTimeoutToMillis(kInt64Min, 0) == kMaxFiniteWaitMillis, "");

// ---- replica of the old conversion (xobject.cpp / xthread.cpp before session 2)
// Absolute timeouts hit assert_always() and became 0; relative ones were
// truncated with uint32_t(-ticks / 10000). Returns false where the old code had
// undefined behaviour (negating INT64_MIN).
static bool OldTimeoutTicksToMs(int64_t ticks, uint32_t* ms) {
  if (ticks == kInt64Min) {
    return false;
  }
  if (ticks > 0) {
    *ms = 0;
  } else if (ticks < 0) {
    *ms = static_cast<uint32_t>(-ticks / 10000);
  } else {
    *ms = 0;
  }
  return true;
}

struct Case {
  const char* name;
  int64_t timeout;
  uint64_t now;  // Guest system time (only used for absolute timeouts).
  uint32_t want_ms;
  uint64_t want_us;
};

int main() {
  // A guest system time (FILETIME, 100 ns since 1601) in 2026.
  constexpr uint64_t kNow = 134'000'000'000'000'000ull;
  constexpr int64_t kNowI = static_cast<int64_t>(kNow);
  const Case cases[] = {
      {"zero (poll)", 0, 0, 0, 0},
      {"-1 (100 ns)", -1, 0, 1, 1},
      {"-5000 (0.5 ms)", -5000, 0, 1, 500},
      {"-9999", -9999, 0, 1, 1000},
      {"-10000 (1 ms)", -10000, 0, 1, 1000},
      {"-10001", -10001, 0, 2, 1001},
      {"-15000 (1.5 ms)", -15000, 0, 2, 1500},
      {"-1e6 (100 ms)", -1000000, 0, 100, 100000},
      {"-(2^32-1) ms", -int64_t(0xFFFFFFFFll * 10000), 0, kMaxFiniteWaitMillis,
       0xFFFFFFFFull * 1000},
      {"-(2^32) ms", -int64_t(0x100000000ll * 10000), 0, kMaxFiniteWaitMillis,
       0x100000000ull * 1000},
      {"INT64_MIN", kInt64Min, 0, kMaxFiniteWaitMillis, (uint64_t(1) << 63) / 10 + 1},
      {"abs now+1 ms", kNowI + 10000, kNow, 1, 1000},
      {"abs now+100 ns", kNowI + 1, kNow, 1, 1},
      {"abs == now", kNowI, kNow, 0, 0},
      {"abs 1 us past", kNowI - 10, kNow, 0, 0},
      {"abs now+5 s", kNowI + 50'000'000, kNow, 5000, 5'000'000},
  };

  int failures = 0;
  std::printf("%-18s %22s %12s %12s %20s  %s\n", "case", "timeout", "old_ms", "new_ms",
              "new_us (Delay)", "result");
  for (const Case& c : cases) {
    const uint64_t rel = NtTimeoutToRelative100ns(c.timeout, c.now);
    const uint32_t new_ms = NtTimeoutToMillis(c.timeout, c.now);
    const uint64_t new_us = Relative100nsToMicros(rel);
    char old_text[16];
    uint32_t old_ms = 0;
    if (OldTimeoutTicksToMs(c.timeout, &old_ms)) {
      std::snprintf(old_text, sizeof(old_text), "%" PRIu32, old_ms);
    } else {
      std::snprintf(old_text, sizeof(old_text), "UB");
    }
    const bool ok = new_ms == c.want_ms && new_us == c.want_us;
    failures += ok ? 0 : 1;
    std::printf("%-18s %22" PRId64 " %12s %12" PRIu32 " %20" PRIu64 "  %s\n", c.name, c.timeout,
                old_text, new_ms, new_us, ok ? "ok" : "FAIL");
    if (!ok) {
      std::printf("    want ms=%" PRIu32 " us=%" PRIu64 "\n", c.want_ms, c.want_us);
    }
  }
  std::printf("%d failure(s)\n", failures);
  return failures;
}
