// B5 registry TU: the parts of src/core/logging.cpp the macros call
// (GetLoggerRaw, RegisterLogCategory, SharedLogLevelFloor, floor recompute).
// Loggers write to spdlog::sinks::null_sink_mt.
#include "b5_log_shared.h"

#include <spdlog/sinks/null_sink.h>

#include <algorithm>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

namespace rexb {
namespace {

struct LogCategoryEntry {
  std::string name;
  std::shared_ptr<spdlog::logger> logger;
};
std::vector<LogCategoryEntry> g_registry;
bool g_early_initialized = false;
bool g_initialized = false;
bool g_gate = false;
int g_default_level = spdlog::level::info;
std::mutex g_mutex;
spdlog::sink_ptr g_sink;

__declspec(noinline) void InitLoggingEarly() { g_early_initialized = true; }

void RecomputeLogLevelFloorLocked() {
  int floor = spdlog::level::trace;
  if (g_initialized && g_gate) {
    floor = g_default_level;
    for (const auto& entry : g_registry)
      if (entry.logger) floor = std::min<int>(floor, entry.logger->level());
  }
  detail::g_log_level_floor.store(floor, std::memory_order_relaxed);
}

}  // namespace

LogCategoryId RegisterLogCategory(const char* name) {
  std::lock_guard lock(g_mutex);
  if (!g_sink) g_sink = std::make_shared<spdlog::sinks::null_sink_mt>();
  auto logger = std::make_shared<spdlog::logger>(name, g_sink);
  logger->set_level(spdlog::level::level_enum(g_default_level));
  g_registry.push_back({name, std::move(logger)});
  return LogCategoryId(uint16_t(g_registry.size() - 1));
}

// Pristine GetLoggerRaw (logging.cpp:395).
__declspec(noinline) spdlog::logger* GetLoggerRaw(LogCategoryId category) {
  if (!g_initialized && !g_early_initialized) InitLoggingEarly();
  if (category.id < g_registry.size()) {
    return g_registry[category.id].logger.get();
  }
  return nullptr;
}
spdlog::logger* (*const GetLoggerRawImport)(LogCategoryId) = &GetLoggerRaw;

namespace detail {
const std::atomic<int>* SharedLogLevelFloor() { return &g_log_level_floor; }
const std::atomic<int>* (*const SharedLogLevelFloorImport)() = &SharedLogLevelFloor;
}  // namespace detail

void BenchInitLogging(spdlog::level::level_enum level, bool gate) {
  std::lock_guard lock(g_mutex);
  g_default_level = level;
  g_gate = gate;
  for (auto& e : g_registry) e.logger->set_level(level);
  g_initialized = true;
  RecomputeLogLevelFloorLocked();
}

void BenchSetCategoryLevel(LogCategoryId id, spdlog::level::level_enum level) {
  std::lock_guard lock(g_mutex);
  g_registry[id.id].logger->set_level(level);
  RecomputeLogLevelFloorLocked();
}

}  // namespace rexb
