// Bench stub for rex/cvar.h (agent8 runtime benches).
//
// Same shape as the SDK macros (rexglue-sdk/include/rex/cvar.h): DEFINE makes
// a global FLAGS_<name>_storage_() returning a reference to a function-local
// static holding the default, and GET calls it. The registrar is replaced by a
// dummy constant so the use site's trailing ';' still closes a declaration.
#pragma once

#include <string>

#define REXCVAR_DEFINE_BOOL(name, default_val, category, desc) \
  bool& FLAGS_##name##_storage_() {                            \
    static bool storage = (default_val);                       \
    return storage;                                            \
  }                                                            \
  [[maybe_unused]] static const bool _cvar_reg_##name = true

#define REXCVAR_DEFINE_STRING(name, default_val, category, desc) \
  std::string& FLAGS_##name##_storage_() {                       \
    static std::string storage = (default_val);                  \
    return storage;                                              \
  }                                                              \
  [[maybe_unused]] static const bool _cvar_reg_##name = true

#define REXCVAR_GET(name) (FLAGS_##name##_storage_())
#define REXCVAR_SET(name, value) (FLAGS_##name##_storage_() = (value))
