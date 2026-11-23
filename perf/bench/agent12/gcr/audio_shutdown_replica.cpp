// Task #22 (Agent 12): replica of AudioSystem::Shutdown's timeout path, on top of S4
// (terminate_while_holding.cpp). Standalone, Windows, MSVC STL; no SDK.
//
//   OLD = audio_system.cpp before batch 2: wait kWorkerShutdownTimeout, then TerminateThread.
//   NEW = audio_shutdown_detach_worker: never terminate. Detach through WorkerControl (copied
//         verbatim from audio_system.cpp) and leak everything the worker can still reach.
//
// Each run is one child process:
//   1. A worker thread mirrors AudioSystem::WorkerThreadMain: WaitAny(client semaphore,
//      shutdown event), read the client under G, run the "guest callback", sleep when idle.
//      G is a std::recursive_mutex, like rex::thread::global_critical_region.
//   2. A straggler guest thread contends for G (kernel exports, mfmsr ENTER sections).
//   3. After a varying delay the main thread runs Shutdown() (OLD or NEW), then the runtime
//      teardown: the AudioSystem storage and (unless leaked) the driver are made PAGE_NOACCESS,
//      so any later access by the worker faults; then main and a fresh thread take G
//      (KernelState teardown, the next waiter). Then main returns (CRT exit, ExitProcess).
// Scenarios: h = guest callback takes G for ~1 ms at a time, 40 to 220 times depending on the
//                run, so some runs exit during the exit grace and others detach (the hazard);
//            p = Shutdown while paused (worker parked in the resume wait). The callback takes G
//                twice and does not re-release the client semaphore, so the 8 queued frames
//                drain and WaitAny can report the shutdown event that Pause() sets. In the SDK
//                the driver releases one count per played frame, so the count drains between
//                frames; an instant re-release starves the shutdown event, because
//                WaitForMultipleObjects reports the lowest signaled index (23:19 rev: every
//                p run hung in Pause());
//            b = guest callback blocked in a wait that never ends, not holding G.
// Times are scaled 1/25: timeout 20 ms (500), exit grace 80 ms (2000), detach grace 80 ms
// (2000), WaitAny 20 ms (500).
// Build: bench/agent12/gcr/build_audio_shutdown_replica.cmd (output in build/agent12/gcr).
//
// Usage: audio_shutdown_replica.exe <old|new> <h|p|b> <runs> [parallel<=2]
// Child exit code: 0x1000 | flags when it finished; 0xDEAD when Shutdown + teardown did not
// finish in time (self-watchdog) or the process did not exit (parent watchdog); 0xBAD0 when
// Pause() did not return within 3 s (scenario p); otherwise the exception code of a crash.
#define NOMINMAX
#include <windows.h>

#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <thread>
#include <vector>

using clk = std::chrono::steady_clock;

static std::recursive_mutex& G() {
  static std::recursive_mutex m;
  return m;
}

// ---- copied from audio_system.cpp (AudioSystem::WorkerControl), unchanged ----
struct WorkerControl {
  enum : uint32_t { kInside = 0, kOutside = 1, kDetached = 2 };
  std::atomic<uint32_t> phase{kInside};

  void Leave() {
    uint32_t expected = kInside;
    if (!phase.compare_exchange_strong(expected, kOutside)) {
      Park();
    }
  }
  bool Reenter() {
    uint32_t expected = kOutside;
    return phase.compare_exchange_strong(expected, kInside);
  }
  bool TryDetach() {
    uint32_t expected = kOutside;
    return phase.compare_exchange_strong(expected, kDetached);
  }
  void ForceDetach() { phase.store(kDetached); }

  [[noreturn]] static void Park() {
    for (;;) {
      std::this_thread::sleep_for(std::chrono::hours(1));
    }
  }
};
// ---- end of copy ----

constexpr DWORD kShutdownTimeoutMs = 20;  // kWorkerShutdownTimeout / 25
constexpr DWORD kExitGraceMs = 80;        // kWorkerExitGrace / 25
constexpr int kDetachGraceMs = 80;        // kWorkerDetachGrace / 25
constexpr DWORD kWaitAnyMs = 20;          // WaitAny timeout / 25
constexpr DWORD kWatchdogMs = 1000;       // Shutdown + teardown must finish within this

struct Driver {  // stands in for SDLAudioDriver: SubmitFrame from guest code
  std::atomic<uint64_t> frames{0};
};

// The AudioSystem members the worker touches.
struct Model {
  std::atomic<bool> worker_running{false};
  HANDLE client_semaphore = nullptr;
  HANDLE shutdown_event = nullptr;  // auto-reset
  HANDLE resume_event = nullptr;    // auto-reset
  HANDLE wait_handles[2] = {};
  bool paused = false;
  HANDLE pause_fence = nullptr;     // rex::thread::Fence
  Driver* driver = nullptr;         // clients_[0].driver
  uint32_t callback = 1;            // clients_[0].callback
  WorkerControl* ctl = nullptr;     // null = cvar off (OLD)
};

static void* PageAlloc(size_t n) {
  return VirtualAlloc(nullptr, n, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
}
static void PagePoison(void* p, size_t n) {  // "delete": every later access faults
  DWORD old = 0;
  VirtualProtect(p, n, PAGE_NOACCESS, &old);
}

static char g_scenario = 'h';
static int g_callback_iters = 40;    // scenario h: G holds per guest callback (set per run)
static std::atomic<int> g_where{0};  // worker: 0 elsewhere, 1 waiting for G, 2 holding G
static HANDLE g_never = nullptr;     // scenario b: never signaled

static void LockG() {
  g_where.store(1);
  G().lock();
  g_where.store(2);
}
static void UnlockG() {
  G().unlock();
  g_where.store(0);
}

// Guest callback: touches no Model member, only the driver and the semaphore it was given
// (in the SDK those are reached through leaked objects or guest memory).
static void GuestCallback(Driver* driver, HANDLE client_semaphore) {
  if (g_scenario == 'b') {
    WaitForSingleObject(g_never, INFINITE);  // a guest wait nobody will satisfy
    return;
  }
  for (int i = 0; i < g_callback_iters; ++i) {  // >= ~40 ms, longer than the shutdown timeout
    LockG();                      // a kernel export / ENTER section
    Sleep(1);
    driver->frames.fetch_add(1);  // SubmitFrame takes G and touches the driver
    UnlockG();
    Sleep(0);
  }
  if (g_scenario != 'p') {  // p: the queued frames drain (see the scenario list at the top)
    ReleaseSemaphore(client_semaphore, 1, nullptr);  // the driver's playback thread
  }
}

// Mirrors AudioSystem::WorkerThreadMain after batch 2 (ctl == null: the OLD loop).
static DWORD WINAPI WorkerMain(LPVOID p) {
  Model* self = static_cast<Model*>(p);
  WorkerControl* ctl = self->ctl;
  const auto leave = [ctl] {
    if (ctl) ctl->Leave();
  };
  const auto reenter = [ctl] {
    if (ctl && !ctl->Reenter()) WorkerControl::Park();
  };
  while (self->worker_running) {
    HANDLE wait_handles[2];
    std::memcpy(wait_handles, self->wait_handles, sizeof(wait_handles));
    leave();
    const DWORD r = WaitForMultipleObjectsEx(2, wait_handles, FALSE, kWaitAnyMs, TRUE);
    reenter();
    if (r == WAIT_FAILED) continue;
    if (r == WAIT_OBJECT_0 + 1) {  // shutdown event
      if (self->paused) {
        SetEvent(self->pause_fence);
        HANDLE resume_event = self->resume_event;
        leave();
        WaitForSingleObject(resume_event, INFINITE);
        reenter();
      }
      continue;
    }
    bool pumped = false;
    if (r == WAIT_OBJECT_0) {
      leave();
      LockG();
      if (ctl && !ctl->Reenter()) {
        UnlockG();
        WorkerControl::Park();
      }
      const uint32_t callback = self->callback;
      Driver* driver = self->driver;
      HANDLE client_semaphore = self->client_semaphore;
      UnlockG();
      if (callback) {
        leave();
        GuestCallback(driver, client_semaphore);
        reenter();
      }
      pumped = true;
    }
    if (!self->worker_running) break;
    if (!pumped) {
      leave();
      Sleep(kWaitAnyMs);
      reenter();
    }
  }
  self->worker_running = false;
  leave();
  return 0;
}

static std::atomic<bool> g_straggler_run{true};
static DWORD WINAPI StragglerMain(LPVOID) {  // a guest thread TerminateTitle left running
  while (g_straggler_run.load()) {
    G().lock();
    Sleep(1);
    G().unlock();
    Sleep(0);
  }
  return 0;
}

static HANDLE g_teardown_done = nullptr;
static DWORD WINAPI WatchdogMain(LPVOID) {
  if (WaitForSingleObject(g_teardown_done, kWatchdogMs) == WAIT_TIMEOUT) {
    printf("    child: Shutdown + teardown did not finish within %lu ms (worker where=%d)\n",
           kWatchdogMs, g_where.load());
    fflush(stdout);
    TerminateProcess(GetCurrentProcess(), 0xDEAD);
  }
  return 0;
}

static LONG WINAPI CrashFilter(EXCEPTION_POINTERS* e) {
  const EXCEPTION_RECORD* r = e->ExceptionRecord;
  HMODULE mod = nullptr;
  char name[MAX_PATH] = "?";
  GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                     static_cast<LPCSTR>(r->ExceptionAddress), &mod);
  if (mod) GetModuleFileNameA(mod, name, MAX_PATH);
  const char* base = strrchr(name, '\\') ? strrchr(name, '\\') + 1 : name;
  printf("    child: EXCEPTION 0x%08lX in %s (worker where=%d)\n", r->ExceptionCode, base, g_where.load());
  fflush(stdout);
  TerminateProcess(GetCurrentProcess(), r->ExceptionCode);
  return EXCEPTION_EXECUTE_HANDLER;
}

// Flags in the child's exit code.
enum : int {
  kFinished = 0x1000,
  kTerminated = 0x1,       // OLD: TerminateThread was called
  kWhereShift = 1,         // OLD: g_where at the kill, 2 bits (0 elsewhere, 1 waiting, 2 holding)
  kDetached = 0x8,         // NEW: detached through TryDetach
  kForced = 0x10,          // NEW: detached through ForceDetach (grace expired)
  kExitedNormally = 0x20,  // the worker exited by itself within the timeout (or a grace)
  kExitedInGrace = 0x40,   // NEW: ... during the exit grace (the bounded cooperative wait)
};

static int Child(bool new_mode, char scenario, int seed) {
  SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
  SetUnhandledExceptionFilter(CrashFilter);
  g_scenario = scenario;
  g_callback_iters = scenario == 'p' ? 2 : 40 + (seed % 4) * 60;  // h: 40, 100, 160, 220
  g_never = CreateEventW(nullptr, TRUE, FALSE, nullptr);
  g_teardown_done = CreateEventW(nullptr, TRUE, FALSE, nullptr);

  // AudioSystem::AudioSystem + Setup + RegisterClient.
  void* model_mem = PageAlloc(sizeof(Model));
  Model* m = new (model_mem) Model();
  void* driver_mem = PageAlloc(sizeof(Driver));
  m->driver = new (driver_mem) Driver();
  m->client_semaphore = CreateSemaphoreW(nullptr, 0, 64, nullptr);
  m->shutdown_event = CreateEventW(nullptr, FALSE, FALSE, nullptr);
  m->resume_event = CreateEventW(nullptr, FALSE, FALSE, nullptr);
  m->pause_fence = CreateEventW(nullptr, FALSE, FALSE, nullptr);
  m->wait_handles[0] = m->client_semaphore;
  m->wait_handles[1] = m->shutdown_event;
  WorkerControl* ctl = new_mode ? new WorkerControl() : nullptr;  // leaked like the shared_ptr
  m->ctl = ctl;
  m->worker_running = true;
  HANDLE worker = CreateThread(nullptr, 0, WorkerMain, m, 0, nullptr);
  HANDLE straggler = CreateThread(nullptr, 0, StragglerMain, nullptr, 0, nullptr);
  ReleaseSemaphore(m->client_semaphore, 8, nullptr);  // queued_frames_

  Sleep(10 + static_cast<DWORD>((seed * 7919u) % 37u));  // vary where the worker is at shutdown

  if (scenario == 'p') {  // AudioSystem::Pause
    m->paused = true;
    SetEvent(m->shutdown_event);
    if (WaitForSingleObject(m->pause_fence, 3000) != WAIT_OBJECT_0) {
      printf("    child: Pause() did not return within 3000 ms (worker where=%d)\n", g_where.load());
      fflush(stdout);
      TerminateProcess(GetCurrentProcess(), 0xBAD0);
    }
  }

  HANDLE watchdog = CreateThread(nullptr, 0, WatchdogMain, nullptr, 0, nullptr);
  int flags = kFinished;

  // ---- AudioSystem::Shutdown ----
  m->worker_running = false;
  const bool detach_mode = ctl != nullptr;
  if (detach_mode && m->paused) SetEvent(m->resume_event);
  SetEvent(m->shutdown_event);
  bool detached = false;
  const bool exited = WaitForSingleObject(worker, kShutdownTimeoutMs) == WAIT_OBJECT_0;
  if (exited) {
    flags |= kExitedNormally;
  } else if (detach_mode && WaitForSingleObject(worker, kExitGraceMs) == WAIT_OBJECT_0) {
    flags |= kExitedNormally | kExitedInGrace;  // DetachWorker: bounded cooperative wait
  } else if (detach_mode) {                     // DetachWorker: detach
    const auto deadline = clk::now() + std::chrono::milliseconds(kDetachGraceMs);
    detached = true;
    while (!ctl->TryDetach()) {
      if (WaitForSingleObject(worker, 1) == WAIT_OBJECT_0) {
        detached = false;
        flags |= kExitedNormally;
        break;
      }
      if (clk::now() >= deadline) {
        ctl->ForceDetach();
        flags |= kForced;
        break;
      }
    }
    if (detached && !(flags & kForced)) flags |= kDetached;
  } else {
    const int where = g_where.load();
    TerminateThread(worker, 0);
    WaitForSingleObject(worker, INFINITE);
    flags |= kTerminated | (where << kWhereShift);
  }
  if (!detached) {
    // Old teardown: DestroyDriver, SystemHeapFree, then ~AudioSystem closes the handles.
    PagePoison(driver_mem, sizeof(Driver));
    CloseHandle(m->client_semaphore);
    CloseHandle(m->shutdown_event);
    CloseHandle(m->resume_event);
  }  // detached: leak the driver and the handles (and the worker's thread handle)
  // ---- Runtime::Shutdown: audio_system_.reset() (in both modes) ----
  PagePoison(model_mem, sizeof(Model));
  // ---- KernelState teardown takes G; so does the next waiter ----
  G().lock();
  G().unlock();
  std::thread next_waiter([] {
    G().lock();
    G().unlock();
  });
  next_waiter.join();
  SetEvent(g_teardown_done);
  WaitForSingleObject(watchdog, INFINITE);
  (void)straggler;  // left running, like a guest straggler; process exit reaps it
  return flags;     // CRT exit + ExitProcess with the worker parked or still running
}

static DWORD RunChild(const char* args, int timeout_ms) {
  char exe[MAX_PATH];
  GetModuleFileNameA(nullptr, exe, MAX_PATH);
  char cmd[MAX_PATH + 64];
  snprintf(cmd, sizeof(cmd), "\"%s\" %s", exe, args);
  STARTUPINFOA si{};
  si.cb = sizeof(si);
  si.dwFlags = STARTF_USESTDHANDLES;
  si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
  si.hStdError = si.hStdOutput;
  si.hStdInput = nullptr;
  PROCESS_INFORMATION pi{};
  if (!CreateProcessA(nullptr, cmd, nullptr, nullptr, TRUE, 0, nullptr, nullptr, &si, &pi)) return 0xFFFFFFFF;
  DWORD code = 0;
  if (WaitForSingleObject(pi.hProcess, timeout_ms) == WAIT_TIMEOUT) {
    printf("    parent: child '%s' did not exit within %d ms (hung)\n", args, timeout_ms);
    TerminateProcess(pi.hProcess, 0xDEAD);
    WaitForSingleObject(pi.hProcess, INFINITE);
    code = 0xDEAD;
  } else {
    GetExitCodeProcess(pi.hProcess, &code);
  }
  CloseHandle(pi.hThread);
  CloseHandle(pi.hProcess);
  return code;
}

int main(int argc, char** argv) {
  setvbuf(stdout, nullptr, _IONBF, 0);
  if (argc >= 5 && strcmp(argv[1], "child") == 0) {
    return Child(strcmp(argv[2], "new") == 0, argv[3][0], atoi(argv[4]));
  }
  if (argc < 4) {
    printf("usage: %s <old|new> <h|p|b> <runs> [parallel<=2]\n", argv[0]);
    return 2;
  }
  const bool new_mode = strcmp(argv[1], "new") == 0;
  const char scenario = argv[2][0];
  const int runs = atoi(argv[3]);
  const int parallel = argc > 4 ? std::max(1, std::min(2, atoi(argv[4]))) : 1;

  std::atomic<int> next{0};
  std::atomic<int> clean{0}, hung{0}, crashed{0}, other{0};
  std::atomic<int> terminated{0}, t_holding{0}, t_waiting{0}, t_elsewhere{0};
  std::atomic<int> detached{0}, forced{0}, exited_normally{0}, exited_in_grace{0};
  const auto t0 = clk::now();
  auto run = [&] {
    for (int i = next++; i < runs; i = next++) {
      char args[64];
      snprintf(args, sizeof(args), "child %s %c %d", new_mode ? "new" : "old", scenario, i);
      const DWORD c = RunChild(args, 10000);
      if (c != 0xDEAD && c != 0xFFFFFFFF && (c & 0xFFFFF000u) == kFinished) {
        ++clean;
        if (c & kTerminated) {
          ++terminated;
          const int where = (c >> kWhereShift) & 3;
          (where == 2 ? t_holding : where == 1 ? t_waiting : t_elsewhere)++;
        }
        if (c & kDetached) ++detached;
        if (c & kForced) ++forced;
        if (c & kExitedNormally) ++exited_normally;
        if (c & kExitedInGrace) ++exited_in_grace;
      } else if (c == 0xDEAD) {
        ++hung;
      } else if (c >= 0xC0000000u) {
        ++crashed;
        printf("    run %d: crash 0x%08lX\n", i, c);
      } else {
        ++other;
        printf("    run %d: exit 0x%lX\n", i, c);
      }
    }
  };
  std::vector<std::thread> pool;
  for (int k = 0; k < parallel; ++k) pool.emplace_back(run);
  for (auto& t : pool) t.join();
  const double secs = std::chrono::duration<double>(clk::now() - t0).count();
  printf("RESULT mode=%s scenario=%c runs=%d parallel=%d wall=%.1fs | clean=%d HUNG=%d CRASHED=%d other=%d | "
         "terminated=%d (holding G %d, waiting for G %d, elsewhere %d) | detached=%d forced=%d exited_normally=%d "
         "(in exit grace %d)\n",
         new_mode ? "new" : "old", scenario, runs, parallel, secs, clean.load(), hung.load(), crashed.load(), other.load(),
         terminated.load(), t_holding.load(), t_waiting.load(), t_elsewhere.load(), detached.load(), forced.load(),
         exited_normally.load(), exited_in_grace.load());
  return (hung.load() || crashed.load() || other.load()) ? 1 : 0;
}
