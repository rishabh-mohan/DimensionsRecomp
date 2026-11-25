import os, hashlib
NEW = r'<workspace>\build\agent2\final\work\new\DimensionsRecomp'

def edit(rel, pairs, crlf=False):
    p = os.path.join(NEW, rel)
    b = open(p, 'rb').read()
    assert (b'\r\n' in b) == crlf, rel
    s = b.decode('utf-8')
    for old, new in pairs:
        if crlf:
            old = old.replace('\n', '\r\n'); new = new.replace('\n', '\r\n')
        n = s.count(old)
        assert n == 1, (rel, old[:60], n)
        s = s.replace(old, new)
    open(p, 'wb').write(s.encode('utf-8'))
    print(hashlib.sha256(s.encode()).hexdigest()[:16].upper(), rel)

# ---- runtime.cpp: one startup line with value(source) of the 11 rexruntime switches ----
edit(r'rexglue-sdk\src\system\runtime.cpp', [
('''// The runtime that applied the host timing settings; it restores them.
static Runtime* host_timing_owner_ = nullptr;
''',
'''// The runtime that applied the host timing settings; it restores them.
static Runtime* host_timing_owner_ = nullptr;

// Final build (build/agent2/final): one startup line with the value and source of each
// rexruntime switch whose default the final build changed, so a log shows whether a
// launch ran the shipped defaults. rexgpu-xenos logs its two in SharedMemory.
static void LogFinalDefaults() {
  static constexpr const char* kNames[] = {
      "physical_protect_hold_global_lock", "physical_protect_keep_watch",
      "host_timer_resolution_ms",          "host_timer_throttling_optout",
      "precise_guest_sleep",               "wait_timeout_round_up",
      "cs_spin",                           "spinlock_pause_spin",
      "clock_lockfree",                    "tls_bounds_fix",
      "timer_queue_precise_wait"};
  static constexpr const char* kSources[] = {"default", "config", "env", "cmdline", "runtime"};
  std::string line;
  for (const char* name : kNames) {
    if (!cvar::GetFlagInfo(name)) {
      line += fmt::format(" {}=unregistered", name);
      continue;
    }
    const auto source = static_cast<size_t>(cvar::GetFlagSource(name));
    line += fmt::format(" {}={}({})", name, cvar::GetFlagByName(name),
                        source < std::size(kSources) ? kSources[source] : "?");
  }
  REXSYS_INFO("Final defaults:{}", line);
}
'''),
('''    thread::ConfigureHostTiming(timing);
    host_timing_owner_ = this;
  }
''',
'''    thread::ConfigureHostTiming(timing);
    host_timing_owner_ = this;
    LogFinalDefaults();
  }
'''),
])

# ---- shared_memory.cpp: rexgpu-xenos half of the line (P2 + C1 verify) ----
edit(r'rexglue-sdk\src\graphics\shared_memory.cpp', [
('''namespace rex::graphics {

SharedMemory::SharedMemory(memory::Memory& memory) : memory_(memory) {''',
'''namespace rex::graphics {

namespace {
// Final build (build/agent2/final): "name=value(source)" for the startup defaults line.
std::string FinalDefault(const char* name) {
  static constexpr const char* kSources[] = {"default", "config", "env", "cmdline", "runtime"};
  const auto source = static_cast<size_t>(cvar::GetFlagSource(name));
  return fmt::format("{}={}({})", name, cvar::GetFlagByName(name),
                     source < std::size(kSources) ? kSources[source] : "?");
}
}  // namespace

SharedMemory::SharedMemory(memory::Memory& memory) : memory_(memory) {'''),
('''  memory_invalidation_callback_handle_ = memory_.RegisterPhysicalMemoryInvalidationCallback(
      MemoryInvalidationCallbackThunk, this, MemoryKeepWatchGuardThunk);
}
''',
'''  memory_invalidation_callback_handle_ = memory_.RegisterPhysicalMemoryInvalidationCallback(
      MemoryInvalidationCallbackThunk, this, MemoryKeepWatchGuardThunk);

  REXGPU_INFO("Final defaults (GPU): {} {}", FinalDefault("shared_memory_single_hold_rearm"),
              FinalDefault("physical_protect_keep_watch_verify"));
}
'''),
])

# ---- shaders.cpp (CRLF): LEGO_NATIVE_SHADER_MISS_CACHE default ON ----
edit(r'rexlego\src\gpu_native\shaders.cpp', [
('''// LEGO_NATIVE_SHADER_MISS_CACHE=1 (default OFF): remember a placement shader that missed the AOT index, so its
''',
'''// LEGO_NATIVE_SHADER_MISS_CACHE (default ON): remember a placement shader that missed the AOT index, so its
'''),
('''bool ShaderMissCacheEnabled() {
  static const bool enabled = ShaderMissEnvironmentSet("LEGO_NATIVE_SHADER_MISS_CACHE", true) &&
                              !ShaderMissEnvironmentSet("LEGO_DUMP_MISSING_SHADERS", false);
  return enabled;
}
''',
'''// LEGO_NATIVE_SHADER_MISS_CACHE unset or empty = the build default, LEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT (1 = ON;
// OFF bins build with -DLEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT=0); "0" = OFF; any other value = ON.
#ifndef LEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT
#define LEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT 1
#endif

bool ShaderMissCacheEnabled() {
  static const bool enabled = [] {
    char* value = nullptr;
    size_t length = 0;
    _dupenv_s(&value, &length, "LEGO_NATIVE_SHADER_MISS_CACHE");
    const bool set = value && length > 1;
    const bool requested = set ? std::strcmp(value, "0") != 0 : LEGO_NATIVE_SHADER_MISS_CACHE_DEFAULT != 0;
    std::free(value);
    const bool capture = ShaderMissEnvironmentSet("LEGO_DUMP_MISSING_SHADERS", false);
    REXLOG_INFO("Native GPU: shader miss cache {} ({}{})", requested && !capture ? "ON" : "OFF",
                set ? "LEGO_NATIVE_SHADER_MISS_CACHE set" : "build default",
                capture ? "; LEGO_DUMP_MISSING_SHADERS keeps the full path" : "");
    return requested && !capture;
  }();
  return enabled;
}
'''),
], crlf=True)
