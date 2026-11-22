// Opt-in sampling profiler, enabled when LEGO_SAMPLE_PROFILE is set. F9 starts
// recording, F9 again stops it and writes profile-<tick>.bin next to the exe
// (with LEGO_SAMPLE_PROFILE_TRIGGER=<path>, it records while that file exists).
// Every ~1 ms each other thread is suspended, its stack is unwound with the x64
// unwind tables (up to 24 frames) and resumed. Addresses are resolved offline
// against legodimensions.map (tools/native-cpu/analyze_profile.py); the file
// header lists the loaded modules.
//
// Layout: "LSP1", u32 module count, per module {u64 base, u32 size, u32 name
// length, name}, u64 sample count, per sample {u32 tid, u32 depth, u64
// frames[depth]}. An "LSPX" trailer follows the samples: u32 version (1), u32
// payload bytes, then u64 QPC frequency, u64 QPC start, u64 QPC end, u64
// sampling rounds, u32 timer mode (0 = timeBeginPeriod(1) + Sleep, 1 =
// high-resolution waitable timer), u32 thread count, per thread {u32 tid, u32
// name length, UTF-8 name}. Later versions only append payload fields.
//
// The sampler paces itself with a high-resolution waitable timer, so it does
// not raise the process timer resolution. Only if that timer is unavailable
// (before Windows 10 1803) does it fall back to timeBeginPeriod(1) + Sleep,
// which makes guest Sleep() calls ~1 ms granular while the profiler is enabled.
#if defined(_WIN32)
#include <windows.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <timeapi.h>

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cwchar>
#include <string>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>

#pragma comment(lib, "psapi.lib")
#pragma comment(lib, "winmm.lib")

#ifndef CREATE_WAITABLE_TIMER_HIGH_RESOLUTION
#define CREATE_WAITABLE_TIMER_HIGH_RESOLUTION 0x00000002
#endif

namespace {

constexpr int kMaxFrames = 24;

struct Sample {
  uint32_t tid;
  uint32_t depth;
  uint64_t frames[kMaxFrames];
};

// Per-recording metadata for the LSPX trailer.
struct Recording {
  uint64_t qpc_start = 0;
  uint64_t qpc_end = 0;
  uint64_t rounds = 0;
  std::unordered_map<uint32_t, std::string> names;  // every sampled thread
};

// Paces the sampler. A high-resolution waitable timer gives ~1 ms waits
// without changing the process timer resolution; timeBeginPeriod(1) + Sleep is
// the fallback.
class Pacer {
 public:
  Pacer() {
    timer_ = CreateWaitableTimerExW(nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,
                                    TIMER_MODIFY_STATE | SYNCHRONIZE);
    if (!timer_) timeBeginPeriod(1);
  }

  // 0 = timeBeginPeriod(1) + Sleep, 1 = high-resolution waitable timer.
  uint32_t mode() const { return timer_ ? 1u : 0u; }

  void Wait(DWORD ms) {
    if (timer_) {
      LARGE_INTEGER due{};
      due.QuadPart = -LONGLONG(ms) * 10000;  // relative, in 100 ns units
      if (SetWaitableTimer(timer_, &due, 0, nullptr, nullptr, FALSE) &&
          WaitForSingleObject(timer_, INFINITE) == WAIT_OBJECT_0) {
        return;
      }
      // Not expected; fall back to the legacy mode for good.
      CloseHandle(timer_);
      timer_ = nullptr;
      timeBeginPeriod(1);
    }
    Sleep(ms);
  }

 private:
  HANDLE timer_ = nullptr;
};

using GetThreadDescriptionFn = HRESULT(WINAPI*)(HANDLE, PWSTR*);

// GetThreadDescription needs Windows 10 1607, so it is resolved at run time.
GetThreadDescriptionFn ResolveGetThreadDescription() {
  for (const wchar_t* dll : {L"kernel32.dll", L"kernelbase.dll"}) {
    HMODULE module = GetModuleHandleW(dll);
    if (!module) continue;
    if (FARPROC proc = GetProcAddress(module, "GetThreadDescription")) {
      return reinterpret_cast<GetThreadDescriptionFn>(reinterpret_cast<void*>(proc));
    }
  }
  return nullptr;
}

// UTF-8 thread name, or empty if unnamed or unavailable. Allocates, so call it
// only while the thread is running.
std::string ThreadName(GetThreadDescriptionFn get_description, HANDLE thread) {
  std::string name;
  PWSTR wide = nullptr;
  if (get_description && SUCCEEDED(get_description(thread, &wide)) && wide) {
    const int length = int(std::wcslen(wide));
    const int bytes =
        WideCharToMultiByte(CP_UTF8, 0, wide, length, nullptr, 0, nullptr, nullptr);
    if (bytes > 0) {
      name.resize(size_t(bytes));
      WideCharToMultiByte(CP_UTF8, 0, wide, length, name.data(), bytes, nullptr, nullptr);
    }
  }
  if (wide) LocalFree(wide);
  return name;
}

// Threads often name themselves after they start, so re-read the names of
// sampled threads that are still alive when the recording ends.
void RefreshNames(GetThreadDescriptionFn get_description, Recording& recording) {
  if (!get_description) return;
  const DWORD pid = GetCurrentProcessId();
  for (auto& [tid, name] : recording.names) {
    HANDLE thread = OpenThread(THREAD_QUERY_LIMITED_INFORMATION, FALSE, tid);
    if (!thread) continue;
    if (GetProcessIdOfThread(thread) == pid) {
      std::string current = ThreadName(get_description, thread);
      if (!current.empty()) name = std::move(current);
    }
    CloseHandle(thread);
  }
}

uint64_t QpcNow() {
  LARGE_INTEGER now{};
  QueryPerformanceCounter(&now);
  return uint64_t(now.QuadPart);
}

template <typename T>
void Append(std::string& out, const T& value) {
  out.append(reinterpret_cast<const char*>(&value), sizeof(value));
}

void WriteProfile(const std::vector<Sample>& samples, const Recording& recording,
                  uint32_t timer_mode) {
  wchar_t exe[MAX_PATH];
  GetModuleFileNameW(nullptr, exe, MAX_PATH);
  std::wstring path(exe);
  path = path.substr(0, path.find_last_of(L"\\/") + 1) + L"profile-" +
         std::to_wstring(GetTickCount64()) + L".bin";
  FILE* f = _wfopen(path.c_str(), L"wb");
  if (!f) return;
  HMODULE modules[1024];
  DWORD needed = 0;
  EnumProcessModules(GetCurrentProcess(), modules, sizeof(modules), &needed);
  const uint32_t count = needed / sizeof(HMODULE);
  std::fwrite("LSP1", 1, 4, f);
  std::fwrite(&count, 4, 1, f);
  for (uint32_t i = 0; i < count; ++i) {
    MODULEINFO info{};
    GetModuleInformation(GetCurrentProcess(), modules[i], &info, sizeof(info));
    char name[MAX_PATH] = {};
    GetModuleBaseNameA(GetCurrentProcess(), modules[i], name, MAX_PATH);
    const uint64_t base = reinterpret_cast<uint64_t>(info.lpBaseOfDll);
    const uint32_t size = info.SizeOfImage;
    const uint32_t length = uint32_t(std::strlen(name));
    std::fwrite(&base, 8, 1, f);
    std::fwrite(&size, 4, 1, f);
    std::fwrite(&length, 4, 1, f);
    std::fwrite(name, 1, length, f);
  }
  const uint64_t total = samples.size();
  std::fwrite(&total, 8, 1, f);
  for (const auto& s : samples) {
    std::fwrite(&s.tid, 4, 1, f);
    std::fwrite(&s.depth, 4, 1, f);
    std::fwrite(s.frames, 8, s.depth, f);
  }
  // LSPX trailer, appended after the samples (see the header comment).
  LARGE_INTEGER frequency{};
  QueryPerformanceFrequency(&frequency);
  std::vector<std::pair<uint32_t, const std::string*>> threads;
  threads.reserve(recording.names.size());
  for (const auto& [tid, name] : recording.names) threads.emplace_back(tid, &name);
  std::sort(threads.begin(), threads.end(),
            [](const auto& a, const auto& b) { return a.first < b.first; });
  std::string payload;
  Append(payload, uint64_t(frequency.QuadPart));
  Append(payload, recording.qpc_start);
  Append(payload, recording.qpc_end);
  Append(payload, recording.rounds);
  Append(payload, timer_mode);
  Append(payload, uint32_t(threads.size()));
  for (const auto& [tid, name] : threads) {
    Append(payload, tid);
    Append(payload, uint32_t(name->size()));
    payload.append(*name);
  }
  const uint32_t version = 1;
  const uint32_t payload_bytes = uint32_t(payload.size());
  std::fwrite("LSPX", 1, 4, f);
  std::fwrite(&version, 4, 1, f);
  std::fwrite(&payload_bytes, 4, 1, f);
  std::fwrite(payload.data(), 1, payload.size(), f);
  std::fclose(f);
  Beep(880, 150);
}

// Unwind a suspended thread from its captured context. Reads only the stack
// and the static unwind tables, and never allocates.
uint32_t Unwind(CONTEXT context, uint64_t* frames) {
  uint32_t depth = 0;
  while (depth < kMaxFrames && context.Rip) {
    frames[depth++] = context.Rip;
    DWORD64 image_base = 0;
    auto* entry = RtlLookupFunctionEntry(context.Rip, &image_base, nullptr);
    if (!entry) {
      if (IsBadReadPtr(reinterpret_cast<void*>(context.Rsp), 8)) break;
      context.Rip = *reinterpret_cast<DWORD64*>(context.Rsp);
      context.Rsp += 8;
      continue;
    }
    void* handler_data = nullptr;
    DWORD64 establisher = 0;
    RtlVirtualUnwind(UNW_FLAG_NHANDLER, image_base, context.Rip, entry, &context,
                     &handler_data, &establisher, nullptr);
  }
  return depth;
}

void SamplerThread() {
  const DWORD self = GetCurrentThreadId();
  const DWORD pid = GetCurrentProcessId();
  const GetThreadDescriptionFn get_description = ResolveGetThreadDescription();
  std::vector<Sample> samples;
  Recording info;
  bool recording = false;
  bool key_was_down = false;
  const char* trigger = std::getenv("LEGO_SAMPLE_PROFILE_TRIGGER");
  Pacer pacer;
  auto finish = [&] {
    info.qpc_end = QpcNow();
    RefreshNames(get_description, info);
    WriteProfile(samples, info, pacer.mode());
  };
  for (;;) {
    const bool key_down = trigger ? GetFileAttributesA(trigger) != INVALID_FILE_ATTRIBUTES
                                 : (GetAsyncKeyState(VK_F9) & 0x8000) != 0;
    if (trigger && recording && !key_down && key_was_down) {
      finish();
      samples.clear();
      recording = false;
    }
    if (key_down && !key_was_down) {
      if (recording) {
        finish();
        samples.clear();
        samples.shrink_to_fit();
      } else {
        samples.reserve(1u << 20);
        Beep(440, 150);
        info = Recording{};
        info.qpc_start = QpcNow();
      }
      recording = !recording;
    }
    key_was_down = key_down;
    if (!recording) {
      pacer.Wait(50);
      continue;
    }
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    ++info.rounds;
    THREADENTRY32 entry{};
    entry.dwSize = sizeof(entry);
    for (BOOL ok = Thread32First(snapshot, &entry); ok; ok = Thread32Next(snapshot, &entry)) {
      if (entry.th32OwnerProcessID != pid || entry.th32ThreadID == self) continue;
      HANDLE thread = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT |
                                 THREAD_QUERY_INFORMATION, FALSE, entry.th32ThreadID);
      if (!thread) continue;
      Sample sample{};
      bool captured = false;
      if (SuspendThread(thread) != DWORD(-1)) {
        CONTEXT context{};
        context.ContextFlags = CONTEXT_FULL;
        if (GetThreadContext(thread, &context)) {
          sample.tid = entry.th32ThreadID;
          sample.depth = Unwind(context, sample.frames);
          captured = true;
        }
        ResumeThread(thread);
      }
      // Allocate only after the thread runs again: it may hold the heap lock.
      if (captured && info.names.find(sample.tid) == info.names.end()) {
        info.names.emplace(sample.tid, ThreadName(get_description, thread));
      }
      CloseHandle(thread);
      if (captured) samples.push_back(sample);
    }
    CloseHandle(snapshot);
    pacer.Wait(1);
  }
}

struct AutoStart {
  AutoStart() {
    if (!std::getenv("LEGO_SAMPLE_PROFILE")) return;
    std::thread(SamplerThread).detach();
  }
} g_auto_start;

}  // namespace
#endif  // _WIN32
