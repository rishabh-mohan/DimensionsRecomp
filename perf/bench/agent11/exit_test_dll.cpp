// exit_test_dll.cpp - task #27 unit test helper (see exit_test.cpp). A DLL
// global whose destructor runs at DLL_PROCESS_DETACH, like the statics of
// rexruntime.dll (the SDK, including the logging registry) and of the other
// DLLs in the game folder. It writes dll_dtor.marker, plus
// dll_dtor_raced.marker if exit_test.exe's heartbeat thread was still running
// at that point. Built with: cl /LD /MD exit_test_dll.cpp
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

namespace {

wchar_t g_dir[MAX_PATH];
const volatile long* g_heartbeat = nullptr;

void WriteMarker(const wchar_t* name, const char* text) {
  if (!g_dir[0]) return;
  wchar_t path[MAX_PATH * 2];
  lstrcpynW(path, g_dir, MAX_PATH);
  lstrcatW(path, L"\\");
  lstrcatW(path, name);
  HANDLE h = CreateFileW(path, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS,
                         FILE_ATTRIBUTE_NORMAL, nullptr);
  if (h == INVALID_HANDLE_VALUE) return;
  DWORD n = 0;
  WriteFile(h, text, static_cast<DWORD>(lstrlenA(text)), &n, nullptr);
  CloseHandle(h);
}

struct DllProbe {
  ~DllProbe() {
    WriteMarker(L"dll_dtor.marker", "DLL static destructor ran (DLL_PROCESS_DETACH)\r\n");
    if (g_heartbeat) {
      long a = *g_heartbeat;
      Sleep(100);
      if (*g_heartbeat != a) {
        WriteMarker(L"dll_dtor_raced.marker",
                    "heartbeat thread still running during the DLL static destructor\r\n");
      }
    }
  }
};
DllProbe g_probe;

}  // namespace

extern "C" __declspec(dllexport) void exit_test_dll_init(const wchar_t* dir,
                                                         const volatile long* heartbeat) {
  lstrcpynW(g_dir, dir, MAX_PATH);
  g_heartbeat = heartbeat;
}
