// Shim for bench_timerq (Agent 11): lets the live rexglue-sdk/src/core/timer_queue.cpp compile
// on its own. Release-style asserts, like the SDK's NDEBUG builds.
#pragma once
#include <cassert>
#define assert_not_null(expr) assert((expr) != nullptr)
#define assert_true(expr) assert(expr)
