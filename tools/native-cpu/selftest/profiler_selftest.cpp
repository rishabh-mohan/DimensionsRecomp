// Self-test workload for rexlego/src/sample_profiler.cpp (linked in unchanged).
// Built and run by tools/native-cpu/run_selftest.ps1, which sets
// LEGO_SAMPLE_PROFILE=1 and LEGO_SAMPLE_PROFILE_TRIGGER=<file> before start.
//
//   main thread : lsp_selftest_outer() -> lsp_selftest_hot()   (busy, ~N s)
//   guest thread: sub_8200BEEF (weak alias of __imp__sub_8200BEEF, the same
//                 shape DEFINE_REX_FUNC produces) + a "hooked" sub_8200CAFE
//                 that calls its original __imp__sub_8200CAFE  (busy)
//   waiter      : selftest::Waiter -> WaitForSingleObject(never signalled)
//   sleeper     : selftest::Sleeper -> Sleep(20) loop
//
// Usage: profiler_selftest.exe <roles.json> [record_seconds]
// Creates the trigger file, records for N s, deletes it, waits for the new
// profile-*.bin next to the exe, then writes the thread roles as JSON.
#include <windows.h>

#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <set>
#include <string>
#include <thread>

extern "C" {
volatile uint64_t g_lsp_sink;

__declspec(noinline) uint64_t lsp_selftest_hot(uint64_t seed, int iters) {
  uint64_t x = seed | 1;
  for (int i = 0; i < iters; ++i) {
    x = x * 6364136223846793005ull + 1442695040888963407ull;
    x ^= x >> 29;
  }
  g_lsp_sink = x;
  return x;
}

__declspec(noinline) uint64_t lsp_selftest_outer(double seconds) {
  LARGE_INTEGER freq, start, now;
  QueryPerformanceFrequency(&freq);
  QueryPerformanceCounter(&start);
  const LONGLONG limit = static_cast<LONGLONG>(seconds * double(freq.QuadPart));
  uint64_t acc = 0;
  do {
    for (int i = 0; i < 8; ++i) acc += lsp_selftest_hot(acc + i, 20000);
    QueryPerformanceCounter(&now);
  } while (now.QuadPart - start.QuadPart < limit);
  return acc;
}

// Guest-shaped functions: extern "C", no C++ decoration, like the codegen.
__declspec(noinline) void __imp__sub_8200BEEF(uint64_t* state, uint8_t* base) {
  uint64_t x = *state + reinterpret_cast<uintptr_t>(base);
  for (int i = 0; i < 20000; ++i) {
    x = (x ^ (x << 13)) * 0x9E3779B97F4A7C15ull;
    x ^= x >> 7;
  }
  *state = x;
  g_lsp_sink = x;
}
__attribute__((alias("__imp__sub_8200BEEF"))) __attribute__((weak, noinline)) void sub_8200BEEF(
    uint64_t* state, uint8_t* base);

// A hooked guest function after linking: __imp__ is the original body and
// sub_8200CAFE is a separate host function that calls it.
__declspec(noinline) void __imp__sub_8200CAFE(uint64_t* state, uint8_t* base) {
  uint64_t x = *state ^ reinterpret_cast<uintptr_t>(base);
  for (int i = 0; i < 4000; ++i) x = x * 2862933555777941757ull + 3037000493ull;
  *state = x;
  g_lsp_sink = x;
}
__declspec(noinline) void sub_8200CAFE(uint64_t* state, uint8_t* base) {
  ++*state;
  __imp__sub_8200CAFE(state, base);
}
}  // extern "C"

namespace selftest {

std::atomic<bool> g_stop_guest{false};
std::atomic<bool> g_stop_sleeper{false};

__declspec(noinline) void GuestLoop() {
  uint64_t state = 1;
  uint8_t* base = reinterpret_cast<uint8_t*>(&state);
  for (uint32_t n = 0; !g_stop_guest.load(std::memory_order_relaxed); ++n) {
    sub_8200BEEF(&state, base);
    if ((n & 15) == 0) sub_8200CAFE(&state, base);
  }
}

// Uses the wait result afterwards so the call is not compiled as a tail call
// (a `jmp WaitForSingleObject` would leave no Waiter frame on the stack).
__declspec(noinline) void Waiter(HANDLE event) {
  volatile DWORD r = WaitForSingleObject(event, INFINITE);
  (void)r;
}

__declspec(noinline) void Sleeper() {
  while (!g_stop_sleeper.load()) Sleep(20);
}

}  // namespace selftest

namespace {

std::wstring ExeDir() {
  wchar_t exe[MAX_PATH];
  GetModuleFileNameW(nullptr, exe, MAX_PATH);
  std::wstring path(exe);
  return path.substr(0, path.find_last_of(L"\\/") + 1);
}

std::set<std::wstring> ListProfiles(const std::wstring& dir) {
  std::set<std::wstring> names;
  WIN32_FIND_DATAW fd;
  HANDLE h = FindFirstFileW((dir + L"profile-*.bin").c_str(), &fd);
  if (h == INVALID_HANDLE_VALUE) return names;
  do {
    names.insert(fd.cFileName);
  } while (FindNextFileW(h, &fd));
  FindClose(h);
  return names;
}

uint64_t FileSize(const std::wstring& path) {
  WIN32_FILE_ATTRIBUTE_DATA a;
  if (!GetFileAttributesExW(path.c_str(), GetFileExInfoStandard, &a)) return 0;
  return (uint64_t(a.nFileSizeHigh) << 32) | a.nFileSizeLow;
}

std::string Narrow(const std::wstring& w) {
  int n = WideCharToMultiByte(CP_UTF8, 0, w.c_str(), -1, nullptr, 0, nullptr, nullptr);
  std::string s(n > 0 ? n - 1 : 0, '\0');
  if (n > 1) WideCharToMultiByte(CP_UTF8, 0, w.c_str(), -1, s.data(), n, nullptr, nullptr);
  return s;
}

std::string JsonEscape(const std::string& s) {
  std::string out;
  for (char c : s) {
    if (c == '\\' || c == '"') out += '\\';
    out += c;
  }
  return out;
}

}  // namespace

int main(int argc, char** argv) {
  if (argc < 2) {
    std::fprintf(stderr, "usage: profiler_selftest <roles.json> [seconds]\n");
    return 2;
  }
  const double seconds = argc > 2 ? std::atof(argv[2]) : 3.0;
  const char* enabled = std::getenv("LEGO_SAMPLE_PROFILE");
  const char* trigger = std::getenv("LEGO_SAMPLE_PROFILE_TRIGGER");
  if (!enabled || !trigger || !*trigger) {
    std::fprintf(stderr, "selftest: set LEGO_SAMPLE_PROFILE and LEGO_SAMPLE_PROFILE_TRIGGER\n");
    return 2;
  }
  const std::wstring dir = ExeDir();
  const std::set<std::wstring> before = ListProfiles(dir);

  HANDLE never = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  std::atomic<DWORD> guest_tid{0}, waiter_tid{0}, sleeper_tid{0};
  std::thread guest([&] {
    SetThreadDescription(GetCurrentThread(), L"selftest-guest");
    guest_tid = GetCurrentThreadId();
    selftest::GuestLoop();
  });
  std::thread waiter([&] {
    SetThreadDescription(GetCurrentThread(), L"selftest-waiter");
    waiter_tid = GetCurrentThreadId();
    selftest::Waiter(never);
  });
  std::thread sleeper([&] {
    SetThreadDescription(GetCurrentThread(), L"selftest-sleeper");
    sleeper_tid = GetCurrentThreadId();
    selftest::Sleeper();
  });
  SetThreadDescription(GetCurrentThread(), L"selftest-main");

  // Start recording: the sampler polls every 50 ms and beeps for 150 ms.
  HANDLE t = CreateFileA(trigger, GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL,
                         nullptr);
  if (t == INVALID_HANDLE_VALUE) {
    std::fprintf(stderr, "selftest: cannot create trigger file %s\n", trigger);
    return 3;
  }
  CloseHandle(t);
  Sleep(400);
  const uint64_t acc = lsp_selftest_outer(seconds);
  DeleteFileA(trigger);
  selftest::g_stop_guest = true;

  // Wait for the new profile and for its size to settle.
  std::wstring found;
  uint64_t last_size = ~0ull;
  for (int i = 0; i < 100; ++i) {
    Sleep(100);
    if (found.empty()) {
      for (const auto& name : ListProfiles(dir))
        if (!before.count(name)) found = dir + name;
      continue;
    }
    const uint64_t size = FileSize(found);
    if (size != 0 && size == last_size) break;
    last_size = size;
  }

  SetEvent(never);
  selftest::g_stop_sleeper = true;
  guest.join();
  waiter.join();
  sleeper.join();

  FILE* f = std::fopen(argv[1], "w");
  if (!f) return 4;
  std::fprintf(f,
               "{\"main\": %lu, \"guest\": %lu, \"waiter\": %lu, \"sleeper\": %lu, "
               "\"seconds\": %.3f, \"profile\": \"%s\", \"sink\": %llu}\n",
               GetCurrentThreadId(), guest_tid.load(), waiter_tid.load(), sleeper_tid.load(),
               seconds, JsonEscape(Narrow(found)).c_str(),
               static_cast<unsigned long long>(acc & 0xFFFF));
  std::fclose(f);
  if (found.empty()) {
    std::fprintf(stderr, "selftest: no new profile-*.bin appeared in 10 s\n");
    return 5;
  }
  std::printf("selftest: profile %s (%llu bytes)\n", Narrow(found).c_str(),
              static_cast<unsigned long long>(FileSize(found)));
  return 0;
}
