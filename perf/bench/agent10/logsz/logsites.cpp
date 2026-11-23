// Task #18: code-size and call-site probe for REX_LOG_IMPL (Agent 12's 19:27 macros.h/api.h edit).
// Compiled twice with the SDK's own flags: "new" = working-tree headers, "old" = the baseline
// rex/logging/{api,macros}.h shadowed in front of the working tree. Nothing is linked.
#include <rex/logging.h>

#define R4(x) x x x x
#define R16(x) R4(R4(x))
#define R64(x) R4(R16(x))

extern "C" __declspec(noinline) void one_debug(int a) {
  REXLOG_DEBUG("probe {}", a);
}
extern "C" __declspec(noinline) void one_trace(int a) {
  REXLOG_TRACE("probe {}", a);
}
extern "C" __declspec(noinline) void one_warn(int a) {
  REXLOG_WARN("probe {}", a);
}
// A disabled trace inside a hot loop.
extern "C" __declspec(noinline) int loop_trace(const int* p, int n) {
  int s = 0;
  for (int i = 0; i < n; ++i) {
    s += p[i];
    REXLOG_TRACE("i={} s={}", i, s);
  }
  return s;
}
// 64 distinct call sites (different arguments, so nothing can be merged).
extern "C" __declspec(noinline) void many64(int a) {
  R64(REXLOG_DEBUG("a {}", a + __COUNTER__);)
}
