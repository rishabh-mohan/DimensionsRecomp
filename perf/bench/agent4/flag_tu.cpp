// Verbatim copies of the unchanged out-of-line flags (separate TU, like textures.cpp and
// hooks_portrait.cpp, so the composite TUs call them as draw.cpp does).
#include <cstdlib>
#include <cstring>

#include "flag_tu.h"

namespace shipped {

bool NativeTextureTimingEnabled() {
  static const bool enabled = [] {
    char* value = nullptr;
    size_t size = 0;
    _dupenv_s(&value, &size, "LEGO_NATIVE_TIMING");
    const bool result = value && *value;
    std::free(value);
    return result;
  }();
  return enabled;
}

bool PortraitProbeEnabled() {
  static const bool requested = [] {
    const auto* value = std::getenv("LEGO_NATIVE_PORTRAIT_TRACE");
    return value && std::strcmp(value, "1") == 0;
  }();
  return requested && LongProbeEnabledForPortrait();
}

}  // namespace shipped
