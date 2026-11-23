// B5 shared header: replicas of rex/logging/api.h + macros.h.
//   OLD = pristine HEAD macros (GetLoggerRaw(cat) on every call).
//   NEW = working tree section D (cvar log_level_gate on): inline level-floor
//         compare first; the category and GetLoggerRaw only above the floor.
// GetLoggerRaw lives in b5_log_registry.cpp and is called through a const
// function pointer defined there, which models the DLL import (the SDK is a
// DLL built with WINDOWS_EXPORT_ALL_SYMBOLS).
#pragma once
#include <spdlog/spdlog.h>

#include <atomic>
#include <cstdint>

namespace rexb {

struct LogCategoryId {
  uint16_t id = 0;
  constexpr LogCategoryId() = default;
  constexpr explicit LogCategoryId(uint16_t i) : id(i) {}
};

LogCategoryId RegisterLogCategory(const char* name);
spdlog::logger* GetLoggerRaw(LogCategoryId category);
extern spdlog::logger* (*const GetLoggerRawImport)(LogCategoryId);

namespace detail {
inline constinit std::atomic<int> g_log_level_floor{0};
inline constinit std::atomic<const std::atomic<int>*> g_log_level_floor_ptr{&g_log_level_floor};
inline constinit std::atomic<bool> g_log_level_floor_bound{false};

const std::atomic<int>* SharedLogLevelFloor();
extern const std::atomic<int>* (*const SharedLogLevelFloorImport)();

inline bool LogLevelMayBeEnabled(int level) {
  return level >=
         g_log_level_floor_ptr.load(std::memory_order_relaxed)->load(std::memory_order_relaxed);
}

// GetLoggerRawAndBindFloor was removed from api.h at 19:54; the bench-only copy
// used by ablation variants v0/v1/v5 lives in b5_log.cpp.

// Verbatim api.h (19:54): the macros call this only for a line that is logged.
inline void BindLogLevelFloor() {
  if (!g_log_level_floor_bound.load(std::memory_order_relaxed)) [[unlikely]] {
    g_log_level_floor_ptr.store(SharedLogLevelFloorImport(), std::memory_order_relaxed);
    g_log_level_floor_bound.store(true, std::memory_order_relaxed);
  }
}
}  // namespace detail

// Bench control (stand-ins for InitLogging / SetCategoryLevel + floor recompute).
void BenchInitLogging(spdlog::level::level_enum level, bool gate);
void BenchSetCategoryLevel(LogCategoryId id, spdlog::level::level_enum level);

}  // namespace rexb

// REXLOG_DEFINE_CATEGORY (unchanged).
#define REXB_DEFINE_CATEGORY(name)                                              \
  namespace rexb::log {                                                         \
  inline ::rexb::LogCategoryId name() {                                         \
    static const ::rexb::LogCategoryId id = ::rexb::RegisterLogCategory(#name); \
    return id;                                                                  \
  }                                                                             \
  }

// Pristine REX_LOG_IMPL.
#define REXB_LOG_IMPL_OLD(cat, lvl, ...)                                                     \
  do {                                                                                       \
    auto* rex_log_ptr_ = ::rexb::GetLoggerRawImport(cat);                                    \
    if (rex_log_ptr_ && rex_log_ptr_->should_log(lvl))                                       \
      rex_log_ptr_->log(spdlog::source_loc{__FILE__, __LINE__, __FUNCTION__}, lvl, __VA_ARGS__); \
  } while (0)

// Working-tree REX_LOG_IMPL (section D), re-synced 19:57 to macros.h of 19:54:
// no [[unlikely]] on the floor test, GetLoggerRaw directly, and the floor is
// bound (BindLogLevelFloor) only by a line that passes should_log and is logged.
#define REXB_LOG_IMPL_NEW(cat, lvl, ...)                                                       \
  do {                                                                                         \
    if (::rexb::detail::LogLevelMayBeEnabled(lvl)) {                                           \
      auto* rex_log_ptr_ = ::rexb::GetLoggerRawImport(cat);                                    \
      if (rex_log_ptr_ && rex_log_ptr_->should_log(lvl)) {                                     \
        ::rexb::detail::BindLogLevelFloor();                                                   \
        rex_log_ptr_->log(spdlog::source_loc{__FILE__, __LINE__, __FUNCTION__}, lvl, __VA_ARGS__); \
      }                                                                                        \
    }                                                                                          \
  } while (0)
