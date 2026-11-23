#pragma once

// Bench stand-in for the SDK's rex/logging.h (Agent 6, task #5). REXLOG_*
// formats with std::format (compile-time checked, like the SDK's fmt-based
// macros), keeps every line for tests to inspect, and prints it unless quiet.

#include <cstdio>
#include <format>
#include <mutex>
#include <string>
#include <utility>
#include <vector>

namespace bench_log {

inline std::mutex g_mutex;
inline std::vector<std::string> g_lines;
inline bool g_quiet = false;

inline void Emit(const char* level, std::string text) {
  std::lock_guard lock(g_mutex);
  if (!g_quiet) std::printf("[%s] %s\n", level, text.c_str());
  g_lines.push_back(std::move(text));
}

// Returns and clears the lines logged so far.
inline std::vector<std::string> Take() {
  std::lock_guard lock(g_mutex);
  return std::exchange(g_lines, {});
}

}  // namespace bench_log

#define REXLOG_INFO(...) ::bench_log::Emit("info", std::format(__VA_ARGS__))
#define REXLOG_WARN(...) ::bench_log::Emit("warn", std::format(__VA_ARGS__))
#define REXLOG_ERROR(...) ::bench_log::Emit("error", std::format(__VA_ARGS__))
#define REXLOG_DEBUG(...) ::bench_log::Emit("debug", std::format(__VA_ARGS__))
