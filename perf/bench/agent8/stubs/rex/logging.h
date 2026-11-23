// Bench stub for rex/logging.h (agent8 runtime benches).
//
// Log calls are counted and their arguments are not evaluated, the same as a
// build with the log level compiled out. Nothing is printed: in the cheat
// bench a failed Save() logs from inside the destructor being timed.
#pragma once

#include <atomic>

namespace rexbench {
inline std::atomic<unsigned> g_log_calls{0};
}  // namespace rexbench

#define REXBENCH_LOG_CALL() ((void)::rexbench::g_log_calls.fetch_add(1, std::memory_order_relaxed))
#define REXLOG_TRACE(...) REXBENCH_LOG_CALL()
#define REXLOG_DEBUG(...) REXBENCH_LOG_CALL()
#define REXLOG_INFO(...) REXBENCH_LOG_CALL()
#define REXLOG_WARN(...) REXBENCH_LOG_CALL()
#define REXLOG_ERROR(...) REXBENCH_LOG_CALL()
#define REXLOG_CRITICAL(...) REXBENCH_LOG_CALL()
