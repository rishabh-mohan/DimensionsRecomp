// pthrottle_test.cpp - S4 task #19 (Agent 1, 04:07): the read-back test for the staged
// host_execution_throttling_optout change (build\agent11\pthrottle\stage, pthrottle_stage.ps1).
//
// pthrottle_test.ps1 copies HostTimingConfig and the threading_win.cpp code under test
// (timer_period_ms_, the constants, GetTimePeriodFn, the opt-out function, ConfigureHostTiming,
// RestoreHostTiming) VERBATIM from the staged and the pristine copies into pthrottle_impl.inc,
// as namespaces staged_impl and pristine_impl, and builds this file with cl. Two test seams,
// nothing else is changed:
//   - spdlog is a shim that records each log line ("LOG <level> <text>");
//   - GetProcAddress is a macro around the extracted text that hands out a recorder for
//     SetProcessInformation: it records each call ("CALL ...") and forwards it to the real
//     function, or simulates Windows 10 (a ControlMask with more than EXECUTION_SPEED fails
//     with ERROR_INVALID_PARAMETER) or a missing export (null, ERROR_PROC_NOT_FOUND).
//
// The throttling state is per process, so every run of ConfigureHostTiming happens in a fresh
// child process. The parent creates it suspended, reads (or presets) its state through the
// child handle, resumes it; the child configures, reads its own state back with
// GetProcessInformation(GetCurrentProcess(), ProcessPowerThrottling) and signals; the parent
// reads the state again through its handle and, in some scenarios, changes it the way Agent 8's
// runner would (read-modify-write through a handle with only PROCESS_SET_INFORMATION |
// PROCESS_QUERY_LIMITED_INFORMATION); then the child calls RestoreHostTiming and exits.
// No game runs. Single-threaded: one child at a time, and the parent waits. Exit 0 = PASS.
//
//   pthrottle_test.exe [run-dir]                                        parent: all scenarios
//   pthrottle_test.exe child <impl> <timer> <exec> <period> <sim> <out> <tag>   (internal)
#define WIN32_LEAN_AND_MEAN
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <format>
#include <fstream>
#include <string>
#include <string_view>
#include <vector>

static_assert(ProcessPowerThrottling == 4, "PROCESS_INFORMATION_CLASS");
static_assert(PROCESS_POWER_THROTTLING_CURRENT_VERSION == 1, "version");
static_assert(PROCESS_POWER_THROTTLING_EXECUTION_SPEED == 0x1, "execution speed flag");
#ifdef PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION
static_assert(PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION == 0x4, "timer flag");
#endif
static_assert(sizeof(PROCESS_POWER_THROTTLING_STATE) == 12, "state size");

// ---- the recorder: shared by the spdlog shim and the SetProcessInformation hook ----
namespace rec {
std::vector<std::string> events;
enum class Sim { kNone, kWin10, kNoApi };
Sim sim = Sim::kNone;
const std::string kSimWin10Fail = "fail 87 (simulated: Windows 10 knows only EXECUTION_SPEED)";
const std::string kResolveNull = "RESOLVE SetProcessInformation -> null (simulated: no export)";

BOOL WINAPI SetProcessInformationRec(HANDLE process, int info_class, LPVOID info, DWORD size) {
  ULONG version = 0, control = 0, state = 0;
  if (info && size >= 3 * sizeof(ULONG)) {
    const ULONG* p = static_cast<const ULONG*>(info);
    version = p[0];
    control = p[1];
    state = p[2];
  }
  const std::string head =
      std::format("CALL SetProcessInformation self={} cls={} size={} V={} C=0x{:X} S=0x{:X}",
                  process == GetCurrentProcess() ? 1 : 0, info_class, size, version, control, state);
  if (sim == Sim::kWin10 && info_class == ProcessPowerThrottling &&
      (control & ~ULONG{PROCESS_POWER_THROTTLING_EXECUTION_SPEED}) != 0) {
    events.push_back(head + " -> " + kSimWin10Fail);
    SetLastError(ERROR_INVALID_PARAMETER);
    return FALSE;
  }
  const BOOL ok = ::SetProcessInformation(
      process, static_cast<PROCESS_INFORMATION_CLASS>(info_class), info, size);
  const DWORD err = ok ? 0 : GetLastError();
  events.push_back(head + (ok ? std::string(" -> ok") : std::format(" -> fail {}", err)));
  if (!ok) {
    SetLastError(err);
  }
  return ok;
}

FARPROC GetProcAddressHook(HMODULE module, LPCSTR name) {
  const bool by_name = reinterpret_cast<ULONG_PTR>(name) > 0xFFFF;
  if (by_name && std::strcmp(name, "SetProcessInformation") == 0) {
    if (sim == Sim::kNoApi) {
      events.push_back(kResolveNull);
      SetLastError(ERROR_PROC_NOT_FOUND);
      return nullptr;
    }
    if (module != GetModuleHandleW(L"kernel32.dll") || !::GetProcAddress(module, name)) {
      events.push_back("RESOLVE SetProcessInformation -> not from kernel32 (unexpected)");
      return ::GetProcAddress(module, name);
    }
    return reinterpret_cast<FARPROC>(&SetProcessInformationRec);
  }
  return ::GetProcAddress(module, name);
}
}  // namespace rec

// ---- the spdlog shim (the extracted code calls spdlog::debug / info / warn) ----
namespace spdlog {
template <typename... A>
void Emit(const char* level, std::string_view fmt, A&... a) {
  rec::events.push_back(std::string("LOG ") + level + " " +
                        std::vformat(fmt, std::make_format_args(a...)));
}
template <typename... A>
void debug(std::string_view fmt, A&&... a) {
  Emit("debug", fmt, a...);
}
template <typename... A>
void info(std::string_view fmt, A&&... a) {
  Emit("info", fmt, a...);
}
template <typename... A>
void warn(std::string_view fmt, A&&... a) {
  Emit("warn", fmt, a...);
}
template <typename... A>
void error(std::string_view fmt, A&&... a) {
  Emit("error", fmt, a...);
}
}  // namespace spdlog

#define GetProcAddress rec::GetProcAddressHook
#include "pthrottle_impl.inc"
#undef GetProcAddress

// The constants the SDK spells out must equal the Windows SDK ones.
static_assert(staged_impl::kProcessPowerThrottlingClass == ProcessPowerThrottling, "class");
static_assert(staged_impl::kPowerThrottlingExecutionSpeed ==
                  PROCESS_POWER_THROTTLING_EXECUTION_SPEED, "execution speed flag");
#ifdef PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION
static_assert(staged_impl::kPowerThrottlingIgnoreTimerResolution ==
                  PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION, "timer flag");
#endif

namespace {

enum class Action { kNone, kPlainSet, kRmw, kAccess };
enum class Cmp { kNone, kIdentical, kLegacyLogs };

const wchar_t* SimName(rec::Sim s) {
  return s == rec::Sim::kWin10 ? L"win10" : s == rec::Sim::kNoApi ? L"noapi" : L"none";
}
rec::Sim ParseSim(std::wstring_view s) {
  return s == L"win10" ? rec::Sim::kWin10 : s == L"noapi" ? rec::Sim::kNoApi : rec::Sim::kNone;
}

bool ReadState(HANDLE process, PROCESS_POWER_THROTTLING_STATE& s) {
  s = {};
  s.Version = PROCESS_POWER_THROTTLING_CURRENT_VERSION;
  return GetProcessInformation(process, ProcessPowerThrottling, &s, sizeof(s)) != FALSE;
}
bool WriteState(HANDLE process, ULONG control, ULONG state) {
  PROCESS_POWER_THROTTLING_STATE s = {};
  s.Version = PROCESS_POWER_THROTTLING_CURRENT_VERSION;
  s.ControlMask = control;
  s.StateMask = state;
  return SetProcessInformation(process, ProcessPowerThrottling, &s, sizeof(s)) != FALSE;
}
std::string Str(ULONG control, ULONG state) {
  return std::format("C=0x{:X} S=0x{:X}", control, state);
}
std::string Str(const PROCESS_POWER_THROTTLING_STATE& s) { return Str(s.ControlMask, s.StateMask); }

// ---- child ----
int ChildMain(int argc, wchar_t** argv) {
  if (argc != 9) {
    return 2;
  }
  const std::wstring impl = argv[2];
  const bool timer = argv[3][0] == L'1';
  const bool exec = argv[4][0] == L'1';
  const uint32_t period = static_cast<uint32_t>(_wtoi(argv[5]));
  const rec::Sim sim = ParseSim(argv[6]);
  const std::wstring out_path = argv[7];
  const std::wstring tag = argv[8];
  HANDLE ready = OpenEventW(EVENT_MODIFY_STATE, FALSE,
                            (L"Local\\pthrottle_test_" + tag + L"_ready").c_str());
  HANDLE go = OpenEventW(SYNCHRONIZE, FALSE, (L"Local\\pthrottle_test_" + tag + L"_go").c_str());
  if (!ready || !go) {
    return 3;
  }
  std::vector<std::string> out;
  PROCESS_POWER_THROTTLING_STATE s;
  out.push_back(ReadState(GetCurrentProcess(), s)
                    ? "before " + Str(s)
                    : std::format("before read-failed {}", GetLastError()));
  rec::events.clear();
  rec::sim = sim;
  uint32_t held = 0;
  if (impl == L"staged") {
    staged_impl::HostTimingConfig config;
    config.timer_resolution_ms = period;
    config.keep_timer_resolution_in_background = timer;
    config.keep_execution_speed_in_background = exec;
    staged_impl::ConfigureHostTiming(config);
    held = staged_impl::timer_period_ms_.load();
  } else if (impl == L"pristine" && !exec) {
    pristine_impl::HostTimingConfig config;
    config.timer_resolution_ms = period;
    config.keep_timer_resolution_in_background = timer;
    pristine_impl::ConfigureHostTiming(config);
    held = pristine_impl::timer_period_ms_.load();
  } else {
    return 2;
  }
  rec::sim = rec::Sim::kNone;
  for (const std::string& e : rec::events) {
    out.push_back("EV " + e);
  }
  out.push_back(ReadState(GetCurrentProcess(), s)
                    ? "after " + Str(s)
                    : std::format("after read-failed {}", GetLastError()));
  out.push_back(std::format("held {}", held));
  SetEvent(ready);
  const DWORD w = WaitForSingleObject(go, 20000);
  uint32_t restored = 0;
  if (impl == L"staged") {
    staged_impl::RestoreHostTiming();
    restored = staged_impl::timer_period_ms_.load();
  } else {
    pristine_impl::RestoreHostTiming();
    restored = pristine_impl::timer_period_ms_.load();
  }
  out.push_back(std::format("restored {}", restored));
  out.push_back(w == WAIT_OBJECT_0 ? "go ok" : "go timeout");
  std::ofstream f(out_path, std::ios::binary | std::ios::trunc);
  for (const std::string& l : out) {
    f << l << "\n";
  }
  f.close();
  return f ? 0 : 4;
}

// ---- parent ----
struct Run {
  std::string error;  // empty = the child ran and reported
  PROCESS_POWER_THROTTLING_STATE launch{}, preset_read{}, parent_after{};
  std::string before, after;
  std::vector<std::string> events;
  uint32_t held = 99, restored = 99;
  bool go_ok = false;
  DWORD exit_code = 0;
  bool act_ok = false;
  DWORD act_err = 0;
  PROCESS_POWER_THROTTLING_STATE act_before{}, act_after{};
  bool ql_get_ok = false, ql_set_ok = true, so_set_ok = false, so_get_ok = true;
  DWORD ql_set_err = 0, so_get_err = 0;
};

struct Scenario {
  std::string id;
  std::string what;
  bool timer = false;
  bool exec = false;
  uint32_t period = 0;
  rec::Sim sim = rec::Sim::kNone;
  bool preset = false;
  ULONG preset_c = 0, preset_s = 0;
  Action action = Action::kNone;
  Cmp cmp = Cmp::kNone;
  ULONG exp_c = 0, exp_s = 0;
  std::vector<std::string> exp_events;
  ULONG act_c = 0, act_s = 0;
};

std::wstring g_exe, g_dir;
int g_index = 0, g_checks = 0, g_failed = 0;

void Check(bool ok, const std::string& what) {
  ++g_checks;
  if (!ok) {
    ++g_failed;
  }
  std::printf("  %s  %s\n", ok ? "PASS" : "FAIL", what.c_str());
}

void DoAction(Action action, DWORD pid, HANDLE full, Run& r) {
  if (action == Action::kPlainSet || action == Action::kRmw) {
    // What a runner gets with OpenProcess; Start-Process's handle has more rights.
    HANDLE h = OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    if (!h) {
      r.error = std::format("OpenProcess failed {}", GetLastError());
      return;
    }
    ReadState(h, r.act_before);
    ULONG control = PROCESS_POWER_THROTTLING_EXECUTION_SPEED, state = 0;
    if (action == Action::kRmw) {
      control = r.act_before.ControlMask | PROCESS_POWER_THROTTLING_EXECUTION_SPEED;
      state = r.act_before.StateMask & ~ULONG{PROCESS_POWER_THROTTLING_EXECUTION_SPEED};
    }
    r.act_ok = WriteState(h, control, state);
    r.act_err = r.act_ok ? 0 : GetLastError();
    ReadState(h, r.act_after);
    CloseHandle(h);
  } else if (action == Action::kAccess) {
    PROCESS_POWER_THROTTLING_STATE tmp;
    HANDLE q = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    r.ql_get_ok = q && ReadState(q, tmp);
    r.ql_set_ok = q && WriteState(q, PROCESS_POWER_THROTTLING_EXECUTION_SPEED, 0);
    r.ql_set_err = r.ql_set_ok ? 0 : GetLastError();
    HANDLE so = OpenProcess(PROCESS_SET_INFORMATION, FALSE, pid);
    r.so_set_ok = so && WriteState(so, PROCESS_POWER_THROTTLING_EXECUTION_SPEED, 0);
    r.so_get_ok = so && ReadState(so, tmp);
    r.so_get_err = r.so_get_ok ? 0 : GetLastError();
    ReadState(full, r.act_after);
    if (q) {
      CloseHandle(q);
    }
    if (so) {
      CloseHandle(so);
    }
  }
}

Run RunChild(const wchar_t* impl, const Scenario& sc, bool exec, Action action) {
  Run r;
  const int index = g_index++;
  const std::wstring tag = std::format(L"{}_{}", GetCurrentProcessId(), index);
  const std::wstring out = std::format(L"{}\\child-{:02}-{}.txt", g_dir, index, impl);
  DeleteFileW(out.c_str());
  HANDLE ready = CreateEventW(nullptr, TRUE, FALSE, (L"Local\\pthrottle_test_" + tag + L"_ready").c_str());
  HANDLE go = CreateEventW(nullptr, TRUE, FALSE, (L"Local\\pthrottle_test_" + tag + L"_go").c_str());
  std::wstring cmd = std::format(L"\"{}\" child {} {} {} {} {} \"{}\" {}", g_exe, impl,
                                 sc.timer ? 1 : 0, exec ? 1 : 0, sc.period, SimName(sc.sim), out, tag);
  STARTUPINFOW si = {};
  si.cb = sizeof(si);
  PROCESS_INFORMATION pi = {};
  if (!ready || !go ||
      !CreateProcessW(g_exe.c_str(), cmd.data(), nullptr, nullptr, FALSE, CREATE_SUSPENDED, nullptr,
                      nullptr, &si, &pi)) {
    r.error = std::format("could not start the child ({})", GetLastError());
    return r;
  }
  if (!ReadState(pi.hProcess, r.launch)) {
    r.error = std::format("read at launch failed ({})", GetLastError());
  }
  if (sc.preset && (!WriteState(pi.hProcess, sc.preset_c, sc.preset_s) ||
                    !ReadState(pi.hProcess, r.preset_read))) {
    r.error = std::format("preset failed ({})", GetLastError());
  }
  ResumeThread(pi.hThread);
  HANDLE waits[2] = {ready, pi.hProcess};
  const DWORD w = WaitForMultipleObjects(2, waits, FALSE, 20000);
  if (w == WAIT_OBJECT_0) {
    if (!ReadState(pi.hProcess, r.parent_after)) {
      r.error = std::format("parent read failed ({})", GetLastError());
    }
    DoAction(action, pi.dwProcessId, pi.hProcess, r);
  } else if (r.error.empty()) {
    r.error = w == WAIT_OBJECT_0 + 1 ? "child exited before it was ready" : "child not ready in 20 s";
  }
  SetEvent(go);
  if (WaitForSingleObject(pi.hProcess, 20000) != WAIT_OBJECT_0) {
    TerminateProcess(pi.hProcess, 99);  // our own test child
    WaitForSingleObject(pi.hProcess, 5000);
    if (r.error.empty()) {
      r.error = "child did not exit in 20 s";
    }
  }
  GetExitCodeProcess(pi.hProcess, &r.exit_code);
  CloseHandle(pi.hThread);
  CloseHandle(pi.hProcess);
  CloseHandle(ready);
  CloseHandle(go);
  std::ifstream f(out);
  std::string line;
  while (std::getline(f, line)) {
    if (line.starts_with("EV ")) {
      r.events.push_back(line.substr(3));
    } else if (line.starts_with("before ")) {
      r.before = line.substr(7);
    } else if (line.starts_with("after ")) {
      r.after = line.substr(6);
    } else if (line.starts_with("held ")) {
      r.held = static_cast<uint32_t>(std::stoul(line.substr(5)));
    } else if (line.starts_with("restored ")) {
      r.restored = static_cast<uint32_t>(std::stoul(line.substr(9)));
    } else if (line == "go ok") {
      r.go_ok = true;
    }
  }
  if (r.error.empty() && r.exit_code != 0) {
    r.error = std::format("child exit code {}", r.exit_code);
  }
  if (r.error.empty() && r.after.empty()) {
    r.error = "no child report";
  }
  return r;
}

void Show(const char* label, const Run& r) {
  std::printf("  %-8s launch %s%s | child before %s, after %s | parent after %s | held %u, restored %u\n",
              label, Str(r.launch).c_str(),
              r.preset_read.Version ? (" -> preset " + Str(r.preset_read)).c_str() : "",
              r.before.c_str(), r.after.c_str(), Str(r.parent_after).c_str(), r.held, r.restored);
  if (r.events.empty()) {
    std::printf("             (no SetProcessInformation call, no log line)\n");
  }
  for (const std::string& e : r.events) {
    std::printf("             %s\n", e.c_str());
  }
  if (!r.error.empty()) {
    std::printf("             ERROR: %s\n", r.error.c_str());
  }
}

std::vector<std::string> LegacyLogs(const std::vector<std::string>& events) {
  std::vector<std::string> v;
  for (const std::string& e : events) {
    if (e.starts_with("LOG ") && e.find("Execution speed") == std::string::npos) {
      v.push_back(e);
    }
  }
  return v;
}

std::string Call(ULONG control, const std::string& result = "ok") {
  return std::format("CALL SetProcessInformation self=1 cls=4 size=12 V=1 C=0x{:X} S=0x0 -> {}",
                     control, result);
}
std::string TimerFail(DWORD e) {
  return std::format("LOG debug Timer resolution power throttling opt-out failed (0x{:08X})", e);
}
std::string ExecFail(DWORD e) {
  return std::format("LOG warn Execution speed power throttling opt-out failed (0x{:08X})", e);
}
const std::string kExecOn = "LOG info Execution speed power throttling opt-out on";
const std::string kHostOn = "LOG info Host timer resolution set to 1 ms (background opt-out on)";
const std::string kHostOff = "LOG info Host timer resolution set to 1 ms (background opt-out off)";

void RunScenario(const Scenario& sc) {
  std::printf("\n[%s] %s\n", sc.id.c_str(), sc.what.c_str());
  std::printf("  config: timer opt-out %d, execution speed opt-out %d, period %u ms, sim %ls%s\n",
              sc.timer ? 1 : 0, sc.exec ? 1 : 0, sc.period, SimName(sc.sim),
              sc.preset ? (", preset at launch " + Str(sc.preset_c, sc.preset_s)).c_str() : "");
  const Run s = RunChild(L"staged", sc, sc.exec, sc.action);
  Show("staged", s);
  Run p;
  if (sc.cmp != Cmp::kNone) {
    p = RunChild(L"pristine", sc, false, Action::kNone);
    Show("pristine", p);
  }
  Check(s.error.empty() && s.go_ok, "staged child ran" + (s.error.empty() ? "" : ": " + s.error));
  if (!s.error.empty()) {
    return;
  }
  if (sc.preset) {
    Check(s.before == Str(sc.preset_c, sc.preset_s),
          "the child started with the preset state " + Str(sc.preset_c, sc.preset_s));
  } else {
    Check(s.before == "C=0x0 S=0x0", "the child started with nothing controlled (C=0x0 S=0x0)");
  }
  bool same = s.events == sc.exp_events;
  Check(same, std::format("staged calls and log lines as expected ({} expected)", sc.exp_events.size()));
  if (!same) {
    for (const std::string& e : sc.exp_events) {
      std::printf("        expected: %s\n", e.c_str());
    }
  }
  const std::string exp = Str(sc.exp_c, sc.exp_s);
  Check(s.after == exp && Str(s.parent_after) == exp,
        "state after ConfigureHostTiming " + exp + " (GetProcessInformation in the child and via the parent's handle)");
  Check(s.held == sc.period && s.restored == 0,
        std::format("timer period held {} (expected {}), 0 after RestoreHostTiming", s.held, sc.period));
  if (sc.cmp != Cmp::kNone) {
    Check(p.error.empty() && p.go_ok, "pristine child ran" + (p.error.empty() ? "" : ": " + p.error));
    if (p.error.empty()) {
      if (sc.cmp == Cmp::kIdentical) {
        Check(p.events == s.events && p.after == s.after,
              "identical to pristine: same SetProcessInformation calls, log lines and final state");
      } else {
        Check(LegacyLogs(p.events) == LegacyLogs(s.events),
              "every log line pristine writes is written unchanged and in order (the new lines aside)");
      }
    }
  }
  switch (sc.action) {
    case Action::kPlainSet:
      Check(s.act_ok && Str(s.act_before) == exp && Str(s.act_after) == Str(sc.act_c, sc.act_s),
            std::format("plain Set C=0x1 S=0x0 on {} reads back {} (replaced, not merged)",
                        Str(s.act_before), Str(s.act_after)));
      break;
    case Action::kRmw:
      Check(s.act_ok && Str(s.act_after) == Str(sc.act_c, sc.act_s),
            std::format("read-modify-write via SET_INFORMATION|QUERY_LIMITED handle: {} -> {} (expected {})",
                        Str(s.act_before), Str(s.act_after), Str(sc.act_c, sc.act_s)));
      break;
    case Action::kAccess:
      Check(s.ql_get_ok && !s.ql_set_ok && s.ql_set_err == ERROR_ACCESS_DENIED,
            std::format("QUERY_LIMITED-only handle: Get ok {}, Set ok {} (error {})", s.ql_get_ok,
                        s.ql_set_ok, s.ql_set_err));
      Check(s.so_set_ok && !s.so_get_ok && s.so_get_err == ERROR_ACCESS_DENIED &&
                Str(s.act_after) == Str(sc.act_c, sc.act_s),
            std::format("SET_INFORMATION-only handle: Set ok {}, Get ok {} (error {}); state now {}",
                        s.so_set_ok, s.so_get_ok, s.so_get_err, Str(s.act_after)));
      break;
    case Action::kNone:
      break;
  }
}

int ParentMain(int argc, wchar_t** argv) {
  wchar_t buf[MAX_PATH] = {};
  GetModuleFileNameW(nullptr, buf, MAX_PATH);
  g_exe = buf;
  g_dir = argc > 1 ? argv[1] : g_exe.substr(0, g_exe.find_last_of(L'\\')) + L"\\run";
  CreateDirectoryW(g_dir.c_str(), nullptr);
  using RtlGetVersionFn = LONG(WINAPI*)(OSVERSIONINFOW*);
  OSVERSIONINFOW vi = {};
  vi.dwOSVersionInfoSize = sizeof(vi);
  if (auto get = reinterpret_cast<RtlGetVersionFn>(
          reinterpret_cast<void (*)()>(::GetProcAddress(GetModuleHandleW(L"ntdll.dll"), "RtlGetVersion")))) {
    get(&vi);
  }
  PROCESS_POWER_THROTTLING_STATE own;
  const bool own_ok = ReadState(GetCurrentProcess(), own);
  std::printf("pthrottle_test (S4 task #19): Windows %lu.%lu build %lu; this process %s\n",
              vi.dwMajorVersion, vi.dwMinorVersion, vi.dwBuildNumber,
              own_ok ? Str(own).c_str() : "unreadable");
  std::printf("C = ControlMask, S = StateMask (0x1 EXECUTION_SPEED, 0x4 IGNORE_TIMER_RESOLUTION)\n");

  std::vector<Scenario> all;
  all.push_back({.id = "a", .what = "both opt-outs off (the defaults), period 0: no call",
                 .cmp = Cmp::kIdentical});
  all.push_back({.id = "a1", .what = "both off, period 1 ms", .period = 1, .cmp = Cmp::kIdentical,
                 .exp_events = {kHostOff}});
  all.push_back({.id = "a2", .what = "both off; a state someone else set (EcoQoS on) stays untouched",
                 .preset = true, .preset_c = 1, .preset_s = 1, .cmp = Cmp::kIdentical,
                 .exp_c = 1, .exp_s = 1});
  all.push_back({.id = "b", .what = "timer opt-out only (the new cvar off), period 0",
                 .timer = true, .cmp = Cmp::kIdentical, .exp_c = 4, .exp_events = {Call(4)}});
  all.push_back({.id = "b1", .what = "timer opt-out only, period 1 ms", .timer = true, .period = 1,
                 .cmp = Cmp::kIdentical, .exp_c = 4, .exp_events = {Call(4), kHostOn}});
  all.push_back({.id = "c", .what = "execution speed opt-out only, period 0", .exec = true,
                 .cmp = Cmp::kLegacyLogs, .exp_c = 1, .exp_events = {Call(1), kExecOn}});
  all.push_back({.id = "c1", .what = "execution speed opt-out only, period 1 ms", .exec = true,
                 .period = 1, .cmp = Cmp::kLegacyLogs, .exp_c = 1,
                 .exp_events = {Call(1), kExecOn, kHostOff}});
  all.push_back({.id = "d", .what = "both opt-outs, period 0: ONE call with the combined mask",
                 .timer = true, .exec = true, .cmp = Cmp::kLegacyLogs, .exp_c = 5,
                 .exp_events = {Call(5), kExecOn}});
  all.push_back({.id = "e", .what = "both opt-outs, period 1 ms", .timer = true, .exec = true,
                 .period = 1, .cmp = Cmp::kLegacyLogs, .exp_c = 5,
                 .exp_events = {Call(5), kExecOn, kHostOn}});
  all.push_back({.id = "i0", .what = "timer opt-out only on simulated Windows 10 (flag rejected)",
                 .timer = true, .period = 1, .sim = rec::Sim::kWin10, .cmp = Cmp::kIdentical,
                 .exp_events = {Call(4, rec::kSimWin10Fail), TimerFail(87), kHostOff}});
  all.push_back({.id = "i", .what = "both on simulated Windows 10: combined call rejected, 0x1 retried alone",
                 .timer = true, .exec = true, .period = 1, .sim = rec::Sim::kWin10,
                 .cmp = Cmp::kLegacyLogs, .exp_c = 1,
                 .exp_events = {Call(5, rec::kSimWin10Fail), TimerFail(87), Call(1), kExecOn, kHostOff}});
  all.push_back({.id = "j", .what = "execution speed only, SetProcessInformation export missing (simulated)",
                 .exec = true, .sim = rec::Sim::kNoApi, .cmp = Cmp::kLegacyLogs,
                 .exp_events = {rec::kResolveNull, ExecFail(ERROR_PROC_NOT_FOUND)}});
  all.push_back({.id = "j1", .what = "both, SetProcessInformation export missing (simulated)",
                 .timer = true, .exec = true, .sim = rec::Sim::kNoApi, .cmp = Cmp::kLegacyLogs,
                 .exp_events = {rec::kResolveNull, TimerFail(ERROR_PROC_NOT_FOUND), rec::kResolveNull,
                                ExecFail(ERROR_PROC_NOT_FOUND)}});
  all.push_back({.id = "h", .what = "an opt-out set at launch (C=0x1, before the game's own call) is replaced",
                 .timer = true, .preset = true, .preset_c = 1, .cmp = Cmp::kIdentical, .exp_c = 4,
                 .exp_events = {Call(4)}});
  all.push_back({.id = "f", .what = "replace semantics: a plain Set of C=0x1 after the game's C=0x4",
                 .timer = true, .action = Action::kPlainSet, .exp_c = 4, .exp_events = {Call(4)},
                 .act_c = 1});
  all.push_back({.id = "g", .what = "runner read-modify-write on the game's C=0x4: keeps the timer opt-out",
                 .timer = true, .action = Action::kRmw, .exp_c = 4, .exp_events = {Call(4)},
                 .act_c = 5});
  all.push_back({.id = "g2", .what = "runner read-modify-write on a game that set nothing",
                 .action = Action::kRmw, .act_c = 1});
  all.push_back({.id = "g3", .what = "runner read-modify-write clears an EcoQoS opt-in (C=0x1 S=0x1)",
                 .preset = true, .preset_c = 1, .preset_s = 1, .action = Action::kRmw, .exp_c = 1,
                 .exp_s = 1, .act_c = 1});
  all.push_back({.id = "k", .what = "access rights a runner's handle needs", .action = Action::kAccess,
                 .act_c = 1});
  for (const Scenario& sc : all) {
    RunScenario(sc);
  }
  std::printf("\nRESULT: %s (%d checks, %d failed; %d child processes)\n", g_failed ? "FAIL" : "PASS",
              g_checks, g_failed, g_index);
  std::fflush(stdout);
  return g_failed ? 1 : 0;
}

}  // namespace

int wmain(int argc, wchar_t** argv) {
  if (argc > 1 && std::wstring_view(argv[1]) == L"child") {
    return ChildMain(argc, argv);
  }
  return ParentMain(argc, argv);
}
