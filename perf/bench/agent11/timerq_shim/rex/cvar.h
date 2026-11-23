// Shim for bench_timerq (Agent 11): just enough of rex/cvar.h for the staged timer_queue.cpp
// (REXCVAR_DEFINE_BOOL with a chained .lifecycle(), REXCVAR_GET) and for bench_timerq.cpp
// (REXCVAR_DECLARE, REXCVAR_SET). Storage and accessor names match the SDK's macros
// (include/rex/cvar.h): a static local behind bool& FLAGS_<name>_storage_(). No registry.
#pragma once
#include <utility>
namespace rex::cvar {
enum class Lifecycle { kInitOnly, kHotReload, kRequiresRestart };
struct FlagRegistrar {
  const char* name;
  FlagRegistrar&& lifecycle(Lifecycle) && { return std::move(*this); }
};
}  // namespace rex::cvar
#define REXCVAR_DECLARE(type, name) type& FLAGS_##name##_storage_()
#define REXCVAR_GET(name) (FLAGS_##name##_storage_())
#define REXCVAR_SET(name, value) (FLAGS_##name##_storage_() = (value))
#define REXCVAR_DEFINE_BOOL(name, default_val, category, desc) \
  bool& FLAGS_##name##_storage_() {                            \
    static bool storage = (default_val);                       \
    return storage;                                            \
  }                                                            \
  static auto _cvar_reg_##name = ::rex::cvar::FlagRegistrar{#name}
