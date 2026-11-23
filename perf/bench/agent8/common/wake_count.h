// Per-thread wake-up counting for the agent8 runtime benches.
//
// NtQuerySystemInformation(SystemProcessInformation = 5) reports, for every
// thread, ContextSwitches: how many times the thread has been switched onto a
// CPU. A thread that sleeps and wakes N times gains about N (plus one for each
// preemption while it runs, rare for threads that run microseconds), so the
// delta over a window is the wake-up count. Only this process's own threads
// are read. The struct layouts are the documented x64 ones (winternl.h names
// ContextSwitches "Reserved3"); the static_asserts pin the offsets.
//
//   std::vector<wake::ThreadSample> before, after;
//   wake::QueryThreads(before);  start the thread under test;  wake::QueryThreads(after);
//   DWORD tid = wake::NewThreadIds(before, after).front();
//   uint32_t cs0 = wake::ContextSwitches(tid); ... wait ...; cs1 - cs0 = wake-ups
#pragma once

#include <windows.h>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace wake {

struct ThreadSample {
  DWORD tid = 0;
  uint32_t context_switches = 0;
  int64_t kernel_100ns = 0;
  int64_t user_100ns = 0;
  uint32_t state = 0;
  uint32_t wait_reason = 0;
};

namespace detail {

struct ClientIdT {
  HANDLE process;
  HANDLE thread;
};

struct SystemThreadInformation {
  LARGE_INTEGER kernel_time;
  LARGE_INTEGER user_time;
  LARGE_INTEGER create_time;
  ULONG wait_time;
  PVOID start_address;
  ClientIdT client_id;
  LONG priority;
  LONG base_priority;
  ULONG context_switches;
  ULONG thread_state;
  ULONG wait_reason;
};

struct UnicodeStringT {
  USHORT length;
  USHORT maximum_length;
  PWSTR buffer;
};

struct SystemProcessInformation {
  ULONG next_entry_offset;
  ULONG number_of_threads;
  BYTE reserved1[48];
  UnicodeStringT image_name;
  LONG base_priority;
  HANDLE unique_process_id;
  BYTE reserved2[0x100 - 0x58];
};

static_assert(sizeof(void*) == 8, "x64 layouts only");
static_assert(sizeof(SystemThreadInformation) == 0x50);
static_assert(offsetof(SystemThreadInformation, client_id) == 0x28);
static_assert(offsetof(SystemThreadInformation, context_switches) == 0x40);
static_assert(sizeof(SystemProcessInformation) == 0x100);
static_assert(offsetof(SystemProcessInformation, unique_process_id) == 0x50);

using NtQuerySystemInformationFn = LONG(NTAPI*)(ULONG, PVOID, ULONG, PULONG);

}  // namespace detail

// Snapshot of every thread of |pid| (default: this process). Not thread-safe
// (one shared buffer); call it from one thread.
inline bool QueryThreads(std::vector<ThreadSample>& out, DWORD pid = GetCurrentProcessId()) {
  static const auto query = reinterpret_cast<detail::NtQuerySystemInformationFn>(
      reinterpret_cast<void*>(GetProcAddress(GetModuleHandleW(L"ntdll.dll"), "NtQuerySystemInformation")));
  static std::vector<uint64_t> buffer(size_t(1) << 18);  // 2 MiB, 8-byte aligned
  out.clear();
  if (!query) {
    return false;
  }
  for (int attempt = 0; attempt < 8; ++attempt) {
    ULONG needed = 0;
    const LONG status =
        query(5, buffer.data(), ULONG(buffer.size() * sizeof(uint64_t)), &needed);
    if (status == LONG(0xC0000004)) {  // STATUS_INFO_LENGTH_MISMATCH
      buffer.resize(std::max<size_t>(buffer.size() * 2, needed / sizeof(uint64_t) + 8192));
      continue;
    }
    if (status < 0) {
      return false;
    }
    const auto* p = reinterpret_cast<const uint8_t*>(buffer.data());
    for (;;) {
      const auto* proc = reinterpret_cast<const detail::SystemProcessInformation*>(p);
      if (DWORD(uintptr_t(proc->unique_process_id)) == pid) {
        const auto* threads = reinterpret_cast<const detail::SystemThreadInformation*>(
            p + sizeof(detail::SystemProcessInformation));
        for (ULONG i = 0; i < proc->number_of_threads; ++i) {
          ThreadSample s;
          s.tid = DWORD(uintptr_t(threads[i].client_id.thread));
          s.context_switches = threads[i].context_switches;
          s.kernel_100ns = threads[i].kernel_time.QuadPart;
          s.user_100ns = threads[i].user_time.QuadPart;
          s.state = threads[i].thread_state;
          s.wait_reason = threads[i].wait_reason;
          out.push_back(s);
        }
        return true;
      }
      if (!proc->next_entry_offset) {
        break;
      }
      p += proc->next_entry_offset;
    }
    return false;
  }
  return false;
}

inline bool SampleThread(DWORD tid, ThreadSample& out) {
  std::vector<ThreadSample> all;
  if (!QueryThreads(all)) {
    return false;
  }
  for (const ThreadSample& s : all) {
    if (s.tid == tid) {
      out = s;
      return true;
    }
  }
  return false;
}

// Context switches of thread |tid| so far, or UINT32_MAX if it is gone.
inline uint32_t ContextSwitches(DWORD tid) {
  ThreadSample s;
  return SampleThread(tid, s) ? s.context_switches : UINT32_MAX;
}

// Thread ids present in |after| but not in |before|.
inline std::vector<DWORD> NewThreadIds(const std::vector<ThreadSample>& before,
                                       const std::vector<ThreadSample>& after) {
  std::vector<DWORD> fresh;
  for (const ThreadSample& a : after) {
    const bool existed = std::any_of(before.begin(), before.end(),
                                     [&](const ThreadSample& b) { return b.tid == a.tid; });
    if (!existed) {
      fresh.push_back(a.tid);
    }
  }
  return fresh;
}

// CPU cycles charged to thread |tid| so far (QueryThreadCycleTime), 0 on error.
inline uint64_t ThreadCycles(DWORD tid) {
  HANDLE h = OpenThread(THREAD_QUERY_LIMITED_INFORMATION, FALSE, tid);
  if (!h) {
    return 0;
  }
  ULONG64 cycles = 0;
  QueryThreadCycleTime(h, &cycles);
  CloseHandle(h);
  return uint64_t(cycles);
}

}  // namespace wake
