// probe_hr_timer.cpp - does SetWaitableTimer accept a completion routine and/or a period on a
// CREATE_WAITABLE_TIMER_HIGH_RESOLUTION timer? (Win32Timer passes both.) 1 thread, trivial CPU.
// Build: cl /nologo /O2 /std:c++20 /EHsc bench\agent11\probe_hr_timer.cpp /Fe:build\agent11\probe_hr_timer.exe /Fo:build\agent11\ (from the repo root)
#include <windows.h>
#include <cstdint>
#include <cstdio>

static int g_apc = 0;
static VOID CALLBACK Apc(LPVOID, DWORD, DWORD) { ++g_apc; }

static void probe(bool hr, bool apc, LONG period, bool absolute) {
  HANDLE t = hr ? CreateWaitableTimerExW(nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_ALL_ACCESS)
                : CreateWaitableTimerW(nullptr, FALSE, nullptr);
  if (!t) {
    printf("%-8s create failed err=%lu\n", hr ? "high-res" : "normal", GetLastError());
    return;
  }
  LARGE_INTEGER due;
  if (absolute) {
    FILETIME ft;
    GetSystemTimePreciseAsFileTime(&ft);
    due.QuadPart = int64_t((uint64_t(ft.dwHighDateTime) << 32) | ft.dwLowDateTime) + 20000;  // now + 2 ms
  } else {
    due.QuadPart = -20000;  // 2 ms relative
  }
  g_apc = 0;
  SetLastError(0);
  BOOL ok = SetWaitableTimer(t, &due, period, apc ? Apc : nullptr, nullptr, FALSE);
  DWORD err = GetLastError();
  DWORD w = WaitForSingleObjectEx(t, 200, TRUE);
  if (apc && g_apc == 0) SleepEx(50, TRUE);
  CancelWaitableTimer(t);
  SleepEx(0, TRUE);
  printf("%-8s due=%-8s apc=%d period=%-3ld -> SetWaitableTimer=%d err=%lu; wait=%s; apc_runs=%d\n",
         hr ? "high-res" : "normal", absolute ? "absolute" : "relative", apc ? 1 : 0, period, ok ? 1 : 0, err,
         w == WAIT_OBJECT_0 ? "SIGNALED" : w == WAIT_IO_COMPLETION ? "IO_COMPLETION" : w == WAIT_TIMEOUT ? "TIMEOUT" : "OTHER",
         g_apc);
  CloseHandle(t);
}

int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  OSVERSIONINFOW v{sizeof(v)};
  typedef LONG(WINAPI * RtlGetVersionFn)(OSVERSIONINFOW*);
  auto rgv = reinterpret_cast<RtlGetVersionFn>(GetProcAddress(GetModuleHandleW(L"ntdll.dll"), "RtlGetVersion"));
  if (rgv) rgv(&v);
  printf("Windows %lu.%lu build %lu\n", v.dwMajorVersion, v.dwMinorVersion, v.dwBuildNumber);
  const LONG kPeriods[2] = {0, 16};
  for (int hr = 1; hr >= 0; --hr) {
    for (int absolute = 0; absolute <= 1; ++absolute) {
      for (int with_apc = 0; with_apc <= 1; ++with_apc) {
        for (int p = 0; p < 2; ++p) {
          probe(hr != 0, with_apc != 0, kPeriods[p], absolute != 0);
        }
      }
    }
  }
  return 0;
}
