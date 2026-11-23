// exit_test.cpp - task #27 unit test (no game needed). What does each way of
// ending the process do when it is called from a NON-main thread (as a guest
// thread calls HalReturnToFirmware / XamShowDirtyDiscErrorUI) while other
// threads are still running and the main thread is blocked (like the UI
// thread in its message loop)?
//
//   exit_test.exe <mode> <marker_dir> [exit_test_dll.dll]
//   mode: exit0 exit1           old code: log line (no flush), CRT exit(code)
//         _Exit0 _Exit1         new code: log line, fflush (= rex::FlushLogging),
//                               std::_Exit(code)
//         _Exit1_noflush        std::_Exit(1) without the flush (info only)
//         terminate1            log line, fflush, TerminateProcess(self, 1)
//
// Files written to <marker_dir> (markers via raw Win32 calls, no CRT state):
//   atexit.marker          an atexit() handler registered by main ran
//   static_dtor.marker     the destructor of an EXE global object ran
//   dtor_raced.marker      ...and the heartbeat thread was STILL RUNNING
//                          during it (the #27 hazard: EXE teardown racing
//                          live threads)
//   dll_dtor.marker        the destructor of a global in exit_test_dll.dll ran
//                          (DLL_PROCESS_DETACH; the SDK lives in rexruntime.dll)
//   dll_dtor_raced.marker  ...and the heartbeat thread was still running then
//   log.txt                fully buffered FILE*, written by the exiting thread
//   csv.txt                fully buffered FILE*, row written, never flushed
//                          (stand-in for the last perf.csv rows)
//   exit_call.txt          UTC FILETIME taken right before the exit call
//   returned.marker        the exit call returned (must never happen)
//   main_timeout.marker    nothing ended the process within 8 s
// bench\agent11\exitfix_test.ps1 builds this (/MD and /MT), runs every mode
// and checks the exit code and the markers.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace {

wchar_t g_dir[MAX_PATH];        // plain arrays: no destructors of their own
volatile long g_heartbeat = 0;  // bumped by the heartbeat thread every ~1 tick
FILE* g_log = nullptr;
FILE* g_csv = nullptr;
HANDLE g_never = nullptr;       // never signaled

enum class Mode { kExit, kQuickExit, kQuickExitNoFlush, kTerminate };
Mode g_mode = Mode::kExit;
int g_code = 0;

void MarkerPath(wchar_t* out, const wchar_t* name) {
  lstrcpynW(out, g_dir, MAX_PATH);
  lstrcatW(out, L"\\");
  lstrcatW(out, name);
}

// Raw Win32 only, so it works inside DLL detach and late CRT teardown.
void WriteMarker(const wchar_t* name, const char* text) {
  if (!g_dir[0]) return;
  wchar_t path[MAX_PATH * 2];
  MarkerPath(path, name);
  HANDLE h = CreateFileW(path, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS,
                         FILE_ATTRIBUTE_NORMAL, nullptr);
  if (h == INVALID_HANDLE_VALUE) return;
  DWORD n = 0;
  WriteFile(h, text, static_cast<DWORD>(lstrlenA(text)), &n, nullptr);
  CloseHandle(h);
}

bool HeartbeatAlive() {
  long a = g_heartbeat;
  Sleep(100);  // the heartbeat thread ticks every timer period (<= 15.6 ms)
  return g_heartbeat != a;
}

// An EXE global with a destructor: stands in for any EXE-side static (a
// function-local static std::ofstream such as the native frames.csv, a
// registry, a std::thread member, ...).
struct StaticProbe {
  ~StaticProbe() {
    WriteMarker(L"static_dtor.marker", "EXE static destructor ran\r\n");
    if (HeartbeatAlive()) {
      WriteMarker(L"dtor_raced.marker",
                  "heartbeat thread still running during the EXE static destructor\r\n");
    }
  }
};
StaticProbe g_static_probe;

DWORD WINAPI HeartbeatThread(void*) {
  for (;;) {
    InterlockedIncrement(&g_heartbeat);
    Sleep(1);
  }
}

DWORD WINAPI BlockedThread(void*) {
  WaitForSingleObject(g_never, INFINITE);
  return 0;
}

// The "guest thread" that asks for the process to end.
DWORD WINAPI GuestThread(void*) {
  fputs("guest: requesting process exit\n", g_log);
  if (g_mode == Mode::kQuickExit || g_mode == Mode::kTerminate) {
    fflush(g_log);  // stand-in for rex::FlushLogging()
  }
  FILETIME ft;
  GetSystemTimePreciseAsFileTime(&ft);
  unsigned long long t =
      (static_cast<unsigned long long>(ft.dwHighDateTime) << 32) | ft.dwLowDateTime;
  char buf[32];
  _ui64toa_s(t, buf, sizeof(buf), 10);
  WriteMarker(L"exit_call.txt", buf);
  switch (g_mode) {
    case Mode::kExit:
      exit(g_code);
    case Mode::kQuickExit:
    case Mode::kQuickExitNoFlush:
      std::_Exit(g_code);
    case Mode::kTerminate:
      TerminateProcess(GetCurrentProcess(), static_cast<UINT>(g_code));
      Sleep(2000);  // TerminateProcess may return before this thread is torn down
      break;
  }
  WriteMarker(L"returned.marker", "the exit call returned\r\n");
  return 0;
}

}  // namespace

int wmain(int argc, wchar_t** argv) {
  if (argc < 3) {
    fputs("usage: exit_test.exe <exit0|exit1|_Exit0|_Exit1|_Exit1_noflush|terminate1> "
          "<marker_dir> [exit_test_dll.dll]\n", stderr);
    return 2;
  }
  const wchar_t* m = argv[1];
  if (!wcscmp(m, L"exit0")) { g_mode = Mode::kExit; g_code = 0; }
  else if (!wcscmp(m, L"exit1")) { g_mode = Mode::kExit; g_code = 1; }
  else if (!wcscmp(m, L"_Exit0")) { g_mode = Mode::kQuickExit; g_code = 0; }
  else if (!wcscmp(m, L"_Exit1")) { g_mode = Mode::kQuickExit; g_code = 1; }
  else if (!wcscmp(m, L"_Exit1_noflush")) { g_mode = Mode::kQuickExitNoFlush; g_code = 1; }
  else if (!wcscmp(m, L"terminate1")) { g_mode = Mode::kTerminate; g_code = 1; }
  else { fputs("unknown mode\n", stderr); return 2; }

  lstrcpynW(g_dir, argv[2], MAX_PATH);
  CreateDirectoryW(g_dir, nullptr);
  atexit([] { WriteMarker(L"atexit.marker", "atexit handler ran\r\n"); });

  wchar_t p[MAX_PATH * 2];
  MarkerPath(p, L"log.txt");
  if (_wfopen_s(&g_log, p, L"wb") || !g_log) return 3;
  setvbuf(g_log, nullptr, _IOFBF, 1 << 16);
  MarkerPath(p, L"csv.txt");
  if (_wfopen_s(&g_csv, p, L"wb") || !g_csv) return 3;
  setvbuf(g_csv, nullptr, _IOFBF, 1 << 16);
  fputs("frame,ms\n1,16.6\n", g_csv);  // stays in the buffer: never flushed here

  if (argc >= 4 && argv[3][0]) {
    HMODULE dll = LoadLibraryW(argv[3]);
    if (!dll) return 4;
    using InitFn = void (*)(const wchar_t*, const volatile long*);
    auto init = reinterpret_cast<InitFn>(GetProcAddress(dll, "exit_test_dll_init"));
    if (!init) return 4;
    init(g_dir, &g_heartbeat);
  }

  g_never = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  CloseHandle(CreateThread(nullptr, 0, HeartbeatThread, nullptr, 0, nullptr));
  CloseHandle(CreateThread(nullptr, 0, BlockedThread, nullptr, 0, nullptr));
  while (g_heartbeat == 0) Sleep(1);
  CloseHandle(CreateThread(nullptr, 0, GuestThread, nullptr, 0, nullptr));

  // The main thread stays blocked, like the UI thread in its message loop.
  if (WaitForSingleObject(g_never, 8000) == WAIT_TIMEOUT) {
    WriteMarker(L"main_timeout.marker", "nothing ended the process within 8 s\r\n");
    TerminateProcess(GetCurrentProcess(), 98);
  }
  return 97;
}
