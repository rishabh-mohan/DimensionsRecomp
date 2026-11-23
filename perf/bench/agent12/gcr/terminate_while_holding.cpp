// S4 (Agent 12 / J3, checklist C5, hazards H1 H11): what happens on Windows
// (MSVC STL) when a thread that holds the global critical region dies or is
// suspended:
//   a) TerminateThread while holding std::recursive_mutex (depth 2)
//   b) thread returns while holding it (Exit inside an ENTER section)
//   c) TerminateThread while holding std::shared_mutex shared (A11's T)
//   d) SuspendThread while holding; a "resumer" that needs the lock first
//   e) thread-id reuse: MSVC recursive_mutex ownership is GetCurrentThreadId();
//      can a new thread that recycles the dead owner's TID "re-enter" it?
//   f) release-build unlock by a NON-owner (a stray REX_LEAVE_GLOBAL_LOCK):
//      f1 while another thread holds it, f2 while it is free. Child process.
//   g) TerminateThread on a thread that is BLOCKED waiting for the lock (a
//      guest thread parked in mfmsr/ENTER). The victim first runs user code
//      (so thread start-up, which holds the loader lock, is over) and is then
//      confirmed parked (its cycle counter stops). Child process per variant:
//      g1 next waiter queued after the kill, g2 queued before the kill,
//      g3 no other waiter (fresh acquirer after the unlock).
// Standalone, no SDK. 1 busy thread at a time, < 20 s per mode.
// Usage: terminate_while_holding.exe        (a-g)
//        terminate_while_holding.exe fg     (f and g only)
#define NOMINMAX
#include <windows.h>

#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <shared_mutex>
#include <thread>

using clk = std::chrono::steady_clock;

// Tries to take the lock from a fresh thread for timeout_ms; returns true if it got it.
template <class Lockable>
static bool AcquireFromOtherThread(Lockable* m, int timeout_ms) {
  auto* got = new std::atomic<int>(0);
  std::thread t([m, got] {
    m->lock();
    got->store(1);
    m->unlock();
  });
  const auto deadline = clk::now() + std::chrono::milliseconds(timeout_ms);
  while (clk::now() < deadline && !got->load()) Sleep(5);
  const bool ok = got->load() != 0;
  if (ok) {
    t.join();
    delete got;
  } else {
    t.detach();  // blocked forever; leaked
  }
  return ok;
}

static HANDLE g_ready;
static DWORD g_main_tid;

static DWORD WINAPI HoldRecursiveForever(LPVOID p) {
  auto* m = static_cast<std::recursive_mutex*>(p);
  m->lock();
  m->lock();  // depth 2, like ENTER section -> kernel export
  SetEvent(g_ready);
  Sleep(INFINITE);
  return 0;
}

static DWORD WINAPI HoldRecursiveAndReturn(LPVOID p) {
  auto* m = static_cast<std::recursive_mutex*>(p);
  m->lock();  // never unlocked: thread exits inside the section
  SetEvent(g_ready);
  return 0;
}

static DWORD WINAPI HoldSharedForever(LPVOID p) {
  auto* m = static_cast<std::shared_mutex*>(p);
  m->lock_shared();
  SetEvent(g_ready);
  Sleep(INFINITE);
  return 0;
}

struct SuspendCtx {
  std::recursive_mutex* m;
  std::atomic<int> stop{0};
};
static DWORD WINAPI HoldUntilStop(LPVOID p) {
  auto* c = static_cast<SuspendCtx*>(p);
  c->m->lock();
  SetEvent(g_ready);
  while (!c->stop.load()) Sleep(1);
  c->m->unlock();
  return 0;
}

static std::recursive_mutex* g_tid_mutex;
static DWORD g_dead_tid;
static std::atomic<int> g_tid_hit{0}, g_tid_acquired{0};
static DWORD WINAPI ProbeTid(LPVOID) {
  if (GetCurrentThreadId() == g_dead_tid) {
    g_tid_hit = 1;
    if (g_tid_mutex->try_lock()) {
      g_tid_acquired = 1;
      g_tid_mutex->unlock();
    }
  }
  return 0;
}

// Child processes report crashes themselves (no WER delay).
static LONG WINAPI CrashFilter(EXCEPTION_POINTERS* e) {
  const EXCEPTION_RECORD* r = e->ExceptionRecord;
  HMODULE mod = nullptr;
  char name[MAX_PATH] = "?";
  GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                     static_cast<LPCSTR>(r->ExceptionAddress), &mod);
  if (mod) GetModuleFileNameA(mod, name, MAX_PATH);
  const char* base = strrchr(name, '\\') ? strrchr(name, '\\') + 1 : name;
  printf("    EXCEPTION 0x%08lX at %s+0x%llX on the %s thread; access type %llu at %p\n", r->ExceptionCode, base,
         static_cast<unsigned long long>(static_cast<const char*>(r->ExceptionAddress) - reinterpret_cast<const char*>(mod)),
         GetCurrentThreadId() == g_main_tid ? "main (releasing)" : "other",
         r->NumberParameters > 0 ? static_cast<unsigned long long>(r->ExceptionInformation[0]) : 0ull,
         r->NumberParameters > 1 ? reinterpret_cast<void*>(r->ExceptionInformation[1]) : nullptr);
  fflush(stdout);
  TerminateProcess(GetCurrentProcess(), r->ExceptionCode);
  return EXCEPTION_EXECUTE_HANDLER;
}

// ---------------------------------------------------------------- f) children
// Exit code 0x100 | bits when the child completes.
static int ChildF1() {  // stray unlock by a non-owner while another thread holds depth 1
  auto* c = new SuspendCtx();
  c->m = new std::recursive_mutex();
  HANDLE th = CreateThread(nullptr, 0, HoldUntilStop, c, 0, nullptr);
  WaitForSingleObject(g_ready, INFINITE);
  c->m->unlock();  // main never locked it
  int bits = 1;    // bit0: the stray unlock returned (no owner check / abort)
  if (AcquireFromOtherThread(c->m, 300)) bits |= 2;  // bit1: a third thread got it while the owner still "holds" it
  c->stop = 1;     // the real owner now unlocks a mutex it no longer owns
  WaitForSingleObject(th, 1000);
  const bool first = AcquireFromOtherThread(c->m, 300);
  const bool second = AcquireFromOtherThread(c->m, 300);
  if (first) bits |= 4;    // bit2: the next lock/unlock pair still succeeds ...
  if (!second) bits |= 8;  // bit3: ... but leaves it held forever (count went negative)
  return 0x100 | bits;
}

static int ChildF2() {  // stray unlock of a free mutex
  auto* m = new std::recursive_mutex();
  m->unlock();
  int bits = 1;  // bit0: returned
  const bool first = AcquireFromOtherThread(m, 300);
  const bool second = AcquireFromOtherThread(m, 300);
  if (first) bits |= 2;    // bit1: next lock/unlock pair succeeds ...
  if (!second) bits |= 4;  // bit2: ... and leaves the mutex held forever
  return 0x100 | bits;
}

// ---------------------------------------------------------------- g) children
struct WaiterCtx {
  std::recursive_mutex* m;
  std::atomic<int> at_lock{0};
  std::atomic<int> got{0};
};
static DWORD WINAPI LockFlag(LPVOID p) {
  auto* c = static_cast<WaiterCtx*>(p);
  c->at_lock = 1;  // user code reached: thread start-up (loader lock) is over
  c->m->lock();
  c->got = 1;
  c->m->unlock();
  return 0;
}
static bool WaitFlag(std::atomic<int>* f, int ms) {
  const auto deadline = clk::now() + std::chrono::milliseconds(ms);
  while (clk::now() < deadline) {
    if (f->load()) return true;
    Sleep(2);
  }
  return f->load() != 0;
}
static bool TryLockFor(std::recursive_mutex* m, int ms) {
  const auto deadline = clk::now() + std::chrono::milliseconds(ms);
  while (clk::now() < deadline) {
    if (m->try_lock()) return true;
    Sleep(2);
  }
  return false;
}
// Starts a waiter and returns once it is parked in the lock (cycle counter stopped).
static HANDLE StartParkedWaiter(WaiterCtx* c, bool* parked) {
  HANDLE h = CreateThread(nullptr, 0, LockFlag, c, 0, nullptr);
  WaitFlag(&c->at_lock, 2000);
  *parked = false;
  for (int k = 0; k < 20 && !*parked; ++k) {
    ULONG64 a = 0, b = 0;
    QueryThreadCycleTime(h, &a);
    Sleep(10);
    QueryThreadCycleTime(h, &b);
    *parked = (a == b) && !c->got.load();
  }
  return h;
}

// Exit code 0x10000 | imm | late<<4 | hung<<8 | stuck<<12 (4 trials each).
static int ChildG(int variant) {
  SetUnhandledExceptionFilter(CrashFilter);
  int imm = 0, late = 0, hung = 0, stuck = 0;
  for (int i = 0; i < 4; ++i) {
    auto* m = new std::recursive_mutex();  // leaked on purpose
    m->lock();                             // this thread is the holder
    auto* w = new WaiterCtx();
    w->m = m;
    bool w_parked = false, x_parked = false;
    HANDLE wh = StartParkedWaiter(w, &w_parked);
    auto* x = new WaiterCtx();
    x->m = m;
    HANDLE xh = nullptr;
    if (variant == 2) xh = StartParkedWaiter(x, &x_parked);
    TerminateThread(wh, 1);
    WaitForSingleObject(wh, INFINITE);
    CloseHandle(wh);
    printf("    g%d.%d victim parked=%d, killed%s\n", variant, i, w_parked, variant == 2 ? " (second waiter queued before)" : "");
    if (variant == 1) {
      xh = StartParkedWaiter(x, &x_parked);
      printf("    g%d.%d second waiter started after the kill, parked=%d\n", variant, i, x_parked);
    }
    printf("    g%d.%d holder unlock() ...\n", variant, i);
    m->unlock();
    printf("    g%d.%d holder unlock() returned\n", variant, i);
    if (variant == 3) {  // no queued waiter: can a fresh thread take it?
      if (AcquireFromOtherThread(m, 200)) {
        ++imm;
      } else if (TryLockFor(m, 100)) {
        m->unlock();
        ++late;
      } else {
        ++stuck;
      }
      printf("    g%d.%d fresh acquirer done (imm=%d late=%d stuck=%d)\n", variant, i, imm, late, stuck);
      continue;
    }
    if (WaitFlag(&x->got, 200)) {
      ++imm;
    } else {
      // Lost wake-up or lock stuck? One more release cycle by this thread.
      const bool relock = TryLockFor(m, 200);
      if (relock) m->unlock();
      if (WaitFlag(&x->got, 200)) {
        ++late;
      } else if (!relock) {
        ++stuck;
      } else {
        ++hung;
      }
    }
    printf("    g%d.%d second waiter: imm=%d late=%d hung=%d stuck=%d\n", variant, i, imm, late, hung, stuck);
    if (x->got.load() && xh) {
      WaitForSingleObject(xh, 1000);
      CloseHandle(xh);
    }
  }
  return 0x10000 | imm | (late << 4) | (hung << 8) | (stuck << 12);
}

static DWORD RunChild(const char* mode, int timeout_ms) {
  char exe[MAX_PATH];
  GetModuleFileNameA(nullptr, exe, MAX_PATH);
  char cmd[MAX_PATH + 32];
  snprintf(cmd, sizeof(cmd), "\"%s\" %s", exe, mode);
  HANDLE out = GetStdHandle(STD_OUTPUT_HANDLE);
  SetHandleInformation(out, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT);
  STARTUPINFOA si{};
  si.cb = sizeof(si);
  si.dwFlags = STARTF_USESTDHANDLES;
  si.hStdOutput = out;
  si.hStdError = out;
  si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
  PROCESS_INFORMATION pi{};
  if (!CreateProcessA(nullptr, cmd, nullptr, nullptr, TRUE, 0, nullptr, nullptr, &si, &pi)) return 0xFFFFFFFF;
  DWORD code = 0;
  if (WaitForSingleObject(pi.hProcess, timeout_ms) == WAIT_TIMEOUT) {
    FILETIME c0, e0, k, u;
    GetProcessTimes(pi.hProcess, &c0, &e0, &k, &u);
    const auto ms = [](FILETIME f) { return ((static_cast<unsigned long long>(f.dwHighDateTime) << 32) | f.dwLowDateTime) / 10000ull; };
    printf("    child %s still running after %d ms (CPU used: user %llu ms, kernel %llu ms); killing it\n", mode, timeout_ms,
           ms(u), ms(k));
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

static const char* AbnormalExit(DWORD code) {
  switch (code) {
    case 3: return "child aborted (owner check active)";
    case 0xC0000409: return "child fast-failed (owner check active)";
    case 0xC0000005: return "child CRASHED (access violation)";
    case 0xDEAD: return "child HUNG (killed)";
    default: return "child exited abnormally";
  }
}

static void RunF() {
  const DWORD f1 = RunChild("f1", 5000);
  if (f1 & 0x100) {
    printf("f1) non-owner unlock while another thread holds it (depth 1): unlock returned=%s; a third thread then got the lock "
           "while the owner still held it=%s; after the owner's own unlock: next lock/unlock ok=%s, lock held forever after it=%s\n",
           (f1 & 1) ? "yes" : "no", (f1 & 2) ? "YES (exclusion broken)" : "no", (f1 & 4) ? "yes" : "no",
           (f1 & 8) ? "YES (count < 0)" : "no");
  } else {
    printf("f1) non-owner unlock while held: exit 0x%lX: %s\n", f1, AbnormalExit(f1));
  }
  const DWORD f2 = RunChild("f2", 5000);
  if (f2 & 0x100) {
    printf("f2) non-owner unlock of a FREE mutex: unlock returned=%s; next lock/unlock ok=%s; lock held forever after it=%s\n",
           (f2 & 1) ? "yes" : "no", (f2 & 2) ? "yes" : "no", (f2 & 4) ? "YES (count = -1, G dead)" : "no");
  } else {
    printf("f2) non-owner unlock of a free mutex: exit 0x%lX: %s\n", f2, AbnormalExit(f2));
  }
}

static void RunG() {
  static const char* kNames[3] = {"g1) parked waiter killed, next waiter queued AFTER the kill",
                                  "g2) parked waiter killed, next waiter queued BEFORE the kill",
                                  "g3) parked waiter killed, no other waiter, fresh acquirer after unlock"};
  for (int v = 1; v <= 3; ++v) {
    char mode[8];
    snprintf(mode, sizeof(mode), "g%d", v);
    printf("%s:\n", kNames[v - 1]);
    const DWORD c = RunChild(mode, 5000);
    if (c & 0x10000) {
      printf("  -> 4 trials: acquired at once=%lu, only after one more release=%lu, never (hung)=%lu, lock stuck held=%lu\n",
             c & 0xF, (c >> 4) & 0xF, (c >> 8) & 0xF, (c >> 12) & 0xF);
    } else {
      printf("  -> exit 0x%lX: %s\n", c, AbnormalExit(c));
    }
  }
}

int main(int argc, char** argv) {
  setvbuf(stdout, nullptr, _IONBF, 0);
  g_main_tid = GetCurrentThreadId();
  g_ready = CreateEventW(nullptr, FALSE, FALSE, nullptr);
  if (argc > 1 && argv[1][0] == 'f' && argv[1][1] != 'g') {
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
    std::_Exit(strcmp(argv[1], "f1") == 0 ? ChildF1() : ChildF2());
  }
  if (argc > 1 && argv[1][0] == 'g') {
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    const int code = ChildG(argv[1][1] - '0');
    fflush(stdout);
    TerminateProcess(GetCurrentProcess(), code);  // skip DLL detach: dead threads may own loader state
  }
  const bool only_fg = argc > 1 && strcmp(argv[1], "fg") == 0;
  printf("S4 terminate_while_holding (Windows, MSVC STL)%s\n", only_fg ? " [f and g only]" : "");

  if (!only_fg) {
  {  // a)
    auto* m = new std::recursive_mutex();
    DWORD tid = 0;
    HANDLE th = CreateThread(nullptr, 0, HoldRecursiveForever, m, 0, &tid);
    WaitForSingleObject(g_ready, INFINITE);
    TerminateThread(th, 1);
    WaitForSingleObject(th, INFINITE);
    CloseHandle(th);
    const bool try_ok = m->try_lock();
    if (try_ok) m->unlock();
    const bool other_ok = AcquireFromOtherThread(m, 500);
    printf("a) TerminateThread while holding recursive_mutex (depth 2): try_lock=%s, lock from another thread within 500 ms=%s -> %s\n",
           try_ok ? "true" : "false", other_ok ? "yes" : "no",
           (!try_ok && !other_ok) ? "ORPHANED (every later mfmsr/kernel call would hang)" : "recovered");
  }
  {  // b)
    auto* m = new std::recursive_mutex();
    DWORD tid = 0;
    HANDLE th = CreateThread(nullptr, 0, HoldRecursiveAndReturn, m, 0, &tid);
    WaitForSingleObject(g_ready, INFINITE);
    WaitForSingleObject(th, INFINITE);
    CloseHandle(th);
    const bool try_ok = m->try_lock();
    if (try_ok) m->unlock();
    const bool other_ok = AcquireFromOtherThread(m, 500);
    printf("b) thread returned while holding recursive_mutex: try_lock=%s, lock from another thread=%s -> %s\n",
           try_ok ? "true" : "false", other_ok ? "yes" : "no",
           (!try_ok && !other_ok) ? "ORPHANED" : "recovered");
  }
  {  // c)
    auto* m = new std::shared_mutex();
    DWORD tid = 0;
    HANDLE th = CreateThread(nullptr, 0, HoldSharedForever, m, 0, &tid);
    WaitForSingleObject(g_ready, INFINITE);
    TerminateThread(th, 1);
    WaitForSingleObject(th, INFINITE);
    CloseHandle(th);
    const bool excl = m->try_lock();
    if (excl) m->unlock();
    const bool shared = m->try_lock_shared();
    if (shared) m->unlock_shared();
    printf("c) TerminateThread while holding shared_mutex SHARED: writer try_lock=%s, reader try_lock_shared=%s -> %s\n",
           excl ? "true" : "false", shared ? "true" : "false",
           (!excl && shared) ? "readers proceed, WRITERS (AddHandle/RemoveHandle) BLOCKED FOREVER" : "other");
  }
  {  // d)
    auto* c = new SuspendCtx();
    c->m = new std::recursive_mutex();
    DWORD tid = 0;
    HANDLE th = CreateThread(nullptr, 0, HoldUntilStop, c, 0, &tid);
    WaitForSingleObject(g_ready, INFINITE);
    SuspendThread(th);
    c->stop = 1;  // the holder would release now, but it is suspended
    const auto t0 = clk::now();
    bool got = false;
    while (clk::now() - t0 < std::chrono::milliseconds(300)) {
      if (c->m->try_lock()) {
        got = true;
        c->m->unlock();
        break;
      }
      Sleep(5);
    }
    printf("d) SuspendThread while holding: lock obtainable while suspended (300 ms)=%s -> %s\n",
           got ? "yes" : "no", got ? "?" : "all G users stall until resume");
    printf("   a resumer that needs G before ResumeThread (KeResumeThread->GetNativeObject, NtResumeThread->LookupObject) would %s\n",
           got ? "proceed" : "DEADLOCK");
    ResumeThread(th);
    WaitForSingleObject(th, 2000);
    const bool after = AcquireFromOtherThread(c->m, 500);
    printf("   after ResumeThread: lock obtainable=%s\n", after ? "yes" : "no");
    CloseHandle(th);
  }
  {  // e)
    g_tid_mutex = new std::recursive_mutex();
    DWORD tid = 0;
    HANDLE th = CreateThread(nullptr, 0, HoldRecursiveAndReturn, g_tid_mutex, 0, &tid);
    WaitForSingleObject(g_ready, INFINITE);
    WaitForSingleObject(th, INFINITE);
    CloseHandle(th);
    g_dead_tid = tid;
    const auto t0 = clk::now();
    int created = 0;
    while (created < 5000 && clk::now() - t0 < std::chrono::seconds(5) && !g_tid_hit.load()) {
      HANDLE p = CreateThread(nullptr, 0, ProbeTid, nullptr, 0, nullptr);
      if (!p) break;
      WaitForSingleObject(p, INFINITE);
      CloseHandle(p);
      ++created;
    }
    printf("e) TID reuse after the owner died holding (depth 1): recycled TID seen=%s after %d thread creations; "
           "that thread's try_lock on the orphaned mutex=%s\n",
           g_tid_hit.load() ? "yes" : "no", created, g_tid_acquired.load() ? "SUCCEEDED (foreign thread 'owns' G)" : "failed/not reached");
  }
  }
  RunF();
  RunG();
  fflush(stdout);
  std::_Exit(0);
}
