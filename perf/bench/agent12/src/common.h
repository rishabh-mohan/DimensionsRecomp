// Agent 12 replica benches: shared helpers (timing, stats, machine load,
// xorshift64 data, SDK-style CreateFileW, X_STATUS values).
#pragma once
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

namespace b12 {

using X_STATUS = uint32_t;
constexpr X_STATUS X_STATUS_SUCCESS = 0x00000000u;
constexpr X_STATUS X_STATUS_ACCESS_VIOLATION = 0xC0000005u;
constexpr X_STATUS X_STATUS_NO_SUCH_FILE = 0xC000000Fu;
constexpr X_STATUS X_STATUS_END_OF_FILE = 0xC0000011u;
constexpr X_STATUS X_STATUS_ACCESS_DENIED = 0xC0000022u;
// Same definitions as the SDK (high bit = failure).
inline bool XSUCCEEDED(X_STATUS s) { return (s & 0x80000000u) == 0; }
inline bool XFAILED(X_STATUS s) { return (s & 0x80000000u) != 0; }

inline uint64_t xorshift64(uint64_t& s) {
  s ^= s << 13;
  s ^= s >> 7;
  s ^= s << 17;
  return s;
}

inline double qpc_seconds() {
  static const double inv_freq = [] {
    LARGE_INTEGER f;
    QueryPerformanceFrequency(&f);
    return 1.0 / double(f.QuadPart);
  }();
  LARGE_INTEGER c;
  QueryPerformanceCounter(&c);
  return double(c.QuadPart) * inv_freq;
}

struct Summary {
  double median = 0, min = 0, max = 0;
};

inline Summary summarize(std::vector<double> v) {
  Summary s;
  if (v.empty()) return s;
  std::sort(v.begin(), v.end());
  size_t n = v.size();
  s.median = (n & 1) ? v[n / 2] : 0.5 * (v[n / 2 - 1] + v[n / 2]);
  s.min = v.front();
  s.max = v.back();
  return s;
}

inline uint64_t filetime_u64(const FILETIME& f) {
  return (uint64_t(f.dwHighDateTime) << 32) | f.dwLowDateTime;
}

// Busy fraction (0..1) of all logical CPUs over `ms` milliseconds, from
// GetSystemTimes (kernel time includes idle time).
inline double sample_machine_load(DWORD ms = 100) {
  FILETIME i0, k0, u0, i1, k1, u1;
  GetSystemTimes(&i0, &k0, &u0);
  Sleep(ms);
  GetSystemTimes(&i1, &k1, &u1);
  double idle = double(filetime_u64(i1) - filetime_u64(i0));
  double total = double(filetime_u64(k1) - filetime_u64(k0)) +
                 double(filetime_u64(u1) - filetime_u64(u0));
  if (total <= 0) return 0;
  return std::clamp((total - idle) / total, 0.0, 1.0);
}

// Creates `path` with `size` bytes of xorshift64(seed) data unless a file of
// exactly that size already exists. Returns false on I/O failure.
inline bool ensure_xorshift_file(const std::wstring& path, uint64_t size, uint64_t seed,
                                 bool force = false) {
  if (!force) {
    WIN32_FILE_ATTRIBUTE_DATA d;
    if (GetFileAttributesExW(path.c_str(), GetFileExInfoStandard, &d)) {
      uint64_t cur = (uint64_t(d.nFileSizeHigh) << 32) | d.nFileSizeLow;
      if (cur == size) return true;
    }
  }
  HANDLE h = CreateFileW(path.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS,
                         FILE_ATTRIBUTE_NORMAL, nullptr);
  if (h == INVALID_HANDLE_VALUE) return false;
  std::vector<uint64_t> buf(1 << 19);  // 4 MB
  uint64_t s = seed ? seed : 0x9E3779B97F4A7C15ull;
  uint64_t left = size;
  bool ok = true;
  while (left && ok) {
    for (auto& w : buf) w = xorshift64(s);
    DWORD chunk = DWORD(std::min<uint64_t>(left, buf.size() * 8));
    DWORD wrote = 0;
    ok = WriteFile(h, buf.data(), chunk, &wrote, nullptr) && wrote == chunk;
    left -= chunk;
  }
  CloseHandle(h);
  return ok;
}

inline uint64_t file_size_of(const std::wstring& path) {
  WIN32_FILE_ATTRIBUTE_DATA d;
  if (!GetFileAttributesExW(path.c_str(), GetFileExInfoStandard, &d)) return 0;
  return (uint64_t(d.nFileSizeHigh) << 32) | d.nFileSizeLow;
}

inline std::string narrow(const std::wstring& w) {
  std::string s;
  for (wchar_t c : w) s.push_back(c < 128 ? char(c) : '?');
  return s;
}

// Directory of the running exe (build/agent12/bench) and the data directory
// next to it (build/agent12/bench-data), independent of the current dir.
inline std::wstring exe_dir() {
  wchar_t buf[MAX_PATH];
  DWORD n = GetModuleFileNameW(nullptr, buf, MAX_PATH);
  std::wstring p(buf, n);
  size_t slash = p.find_last_of(L"\\/");
  return slash == std::wstring::npos ? L"." : p.substr(0, slash);
}
inline std::wstring data_dir() {
  std::wstring d = exe_dir() + L"\\..\\bench-data";
  CreateDirectoryW(d.c_str(), nullptr);
  return d;
}
// Workspace root (exe lives in <root>\build\agent12\bench).
inline std::wstring workspace_root() { return exe_dir() + L"\\..\\..\\.."; }

// One-line machine description for result headers.
inline void print_machine_header(const char* bench) {
  SYSTEM_INFO si;
  GetSystemInfo(&si);
  SYSTEMTIME t;
  GetLocalTime(&t);
  std::printf("# %s  %04u-%02u-%02u %02u:%02u  logical CPUs %lu  load(200ms) %.0f%%\n", bench,
              t.wYear, t.wMonth, t.wDay, t.wHour, t.wMinute, si.dwNumberOfProcessors,
              100.0 * sample_machine_load(200));
}

// FNV-1a 64 over a byte range (used only for in-memory OLD/NEW equality
// checks; never printed or written for game data).
inline uint64_t fnv1a64(const uint8_t* p, size_t n, uint64_t h = 0xcbf29ce484222325ull) {
  for (size_t i = 0; i < n; ++i) {
    h ^= p[i];
    h *= 0x100000001b3ull;
  }
  return h;
}

}  // namespace b12
