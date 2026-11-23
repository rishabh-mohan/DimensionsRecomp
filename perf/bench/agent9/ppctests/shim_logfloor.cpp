// Test-harness-only shim (bench/agent9/ppctests), linked only when the generated tests are compiled with the
// dev-tree headers against the pin (baseline) rexruntime.dll.
// Dev rex/logging/api.h declares rex::detail::SharedLogLevelFloor() (defined in dev src/rex/logging.cpp); the
// pin rexruntime.dll predates it. The function only feeds the logging macros' level gate; a floor of 0 (trace)
// makes every macro take the full path, which per api.h "costs speed but changes no output".
#include <atomic>

namespace rex::detail {
const std::atomic<int>* SharedLogLevelFloor() {
  static constinit std::atomic<int> floor{0};
  return &floor;
}
}  // namespace rex::detail
