// bench/agent12/pause/pause_stress.cpp -- task #17 helper (Agent 12).
//
// Host-thread REPLICA of the ReXApp::SetGuestPaused ordering (src/ui/rex_app.cpp). No SDK code.
//   * 2 "guest" threads (busy loop): log line under sink_mutex (heap string), malloc+touch+free of
//     64 KB..1 MB (above the LFH limit -> process heap lock), G (recursive_mutex) briefly,
//     T (shared_mutex) shared briefly, then unlocked work.
//   * 1 "audio worker" host thread, never suspended: every ~1 ms a guest callback that enters G
//     a few times; pause handshake like AudioSystem::Pause (request + wake event, fence back,
//     resume event).
//   * main thread = UI thread: pause/unpause cycles with random 0..gap_us gaps.
//       old   : snapshot(T excl + alloc) -> SuspendThread each -> audio fence -> log (sink) ->
//               log alloc + snapshot free (heap).  unpause: T excl + alloc -> ResumeThread each ->
//               audio resume -> log -> free.
//       new   : snapshot + saved list + audio fence + log BEFORE suspending; suspend loop sets flags
//               only.  unpause: ResumeThread from the saved list FIRST, then audio resume, log, clear.
//       guard : old, but each SuspendThread runs with G and T (exclusive) held by the UI and waits
//               for the thread to really stop (GetThreadContext) -- models Agent 11's part B.
//   * watchdog: a UI step older than hang_ms is a HANG (counted per step); it then rescues by
//     ResumeThread on the guests until the step completes, so the run continues.
//
//   pause_stress.exe mode=old|new|guard cycles=N [seed=S] [max_s=20] [hang_ms=200] [gap_us=2000]
//                    [sink_us=..] [g_us=..] [t_us=..] [free_us=..] [audio_entries=..]
//                    [audio_g_us=..] [audio_work_us=..]
// Prints one "RESULT key=value ..." line.
#include <windows.h>

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <shared_mutex>
#include <string>
#include <vector>

namespace {

enum Mode { kOld = 0, kNew = 1, kGuard = 2 };
const char* const kModeName[] = {"old", "new", "guard"};

enum Step : int { kIdle, kPre, kSuspend, kAudio, kSink, kHeap, kT, kResume, kStepCount };
const char* const kStepName[kStepCount] = {"idle", "pre",  "suspend", "audio_fence",
                                           "sink", "heap", "T",       "resume"};

constexpr int kGuests = 2;
constexpr size_t kUiBlock = 64 * 1024;  // UI-side heap block: above the LFH limit (see RESULTS.md)

struct Params {
  int mode = kOld;
  int cycles = 1000;
  uint64_t seed = 1;
  double max_s = 20;
  double hang_ms = 200;
  int gap_us = 2000;
  double sink_us = 4, g_us = 40, t_us = 4, free_us = 400;
  int audio_entries = 4;
  double audio_g_us = 5, audio_work_us = 30;
} P;

double g_ticks_per_us = 1;
inline uint64_t Now() {
  LARGE_INTEGER t;
  QueryPerformanceCounter(&t);
  return uint64_t(t.QuadPart);
}
inline void SpinUs(double us) {
  if (us <= 0) return;
  const uint64_t end = Now() + uint64_t(us * g_ticks_per_us);
  while (Now() < end) YieldProcessor();
}

struct Rng {
  uint64_t s;
  uint64_t Next() {
    s ^= s << 13;
    s ^= s >> 7;
    s ^= s << 17;
    return s;
  }
  uint32_t Below(uint32_t n) { return n ? uint32_t((Next() >> 11) % n) : 0; }
};

std::mutex g_sink_mutex;   // the log sink mutex
std::recursive_mutex g_G;  // the global critical region
std::shared_mutex g_T;     // the object table lock
char g_ring[1 << 16];      // the sink's "file" (guarded by g_sink_mutex)
size_t g_ring_pos = 0;
std::atomic<void*> g_escape{nullptr};  // keeps malloc/free pairs from being elided

HANDLE g_guest[kGuests];
std::atomic<bool> g_stop{false};
std::atomic<uint64_t> g_guest_iters{0};

void SinkWrite(const char* s, size_t n) {  // caller holds g_sink_mutex
  if (n > 256) n = 256;
  if (g_ring_pos + n > sizeof(g_ring)) g_ring_pos = 0;
  memcpy(g_ring + g_ring_pos, s, n);
  g_ring_pos += n;
}

// ---------------------------------------------------------------- guest threads
DWORD WINAPI GuestMain(void* arg) {
  const int idx = int(intptr_t(arg));
  Rng rng{(0x9E3779B97F4A7C15ull * uint64_t(idx + 1)) ^ (P.seed * 0xD1B54A32D192ED03ull) ^ 1};
  uint64_t n = 0;
  while (!g_stop.load(std::memory_order_relaxed)) {
    {  // a log line: sink mutex + a heap-allocated string
      std::lock_guard<std::mutex> lk(g_sink_mutex);
      std::string line = "guest ";
      line += std::to_string(idx);
      line += " iteration ";
      line += std::to_string(n);
      line += ": a log line long enough to leave the small-string buffer";
      SinkWrite(line.data(), line.size());
      SpinUs(P.sink_us);
    }
    {  // a large heap block: bypasses the LFH, takes the process heap lock
      const size_t sz = (64u << 10) + rng.Below((1u << 20) - (64u << 10) + 1);
      char* b = static_cast<char*>(malloc(sz));
      if (b) {
        g_escape.store(b, std::memory_order_relaxed);
        volatile char* vb = b;
        for (size_t i = 0; i < sz; i += 4096) vb[i] = char(i >> 12);
        vb[sz - 1] = 1;
        free(b);
      }
    }
    {  // the global critical region
      std::lock_guard<std::recursive_mutex> lk(g_G);
      SpinUs(P.g_us);
    }
    {  // the object table, shared
      std::shared_lock<std::shared_mutex> lk(g_T);
      SpinUs(P.t_us);
    }
    SpinUs(P.free_us);  // unlocked guest work
    g_guest_iters.fetch_add(1, std::memory_order_relaxed);
    ++n;
  }
  return 0;
}

// ---------------------------------------------------------------- audio worker
HANDLE g_audio_wake, g_audio_fence, g_audio_resume, g_audio_timer;
std::atomic<bool> g_audio_pause_req{false};
std::atomic<uint64_t> g_audio_ticks{0};

void ArmTimer(HANDLE t, int64_t us) {
  LARGE_INTEGER due;
  due.QuadPart = -us * 10;
  SetWaitableTimer(t, &due, 0, nullptr, nullptr, FALSE);
}

DWORD WINAPI AudioMain(void*) {
  HANDLE h[2] = {g_audio_wake, g_audio_timer};
  ArmTimer(g_audio_timer, 1000);
  while (!g_stop.load(std::memory_order_relaxed)) {
    const DWORD r = WaitForMultipleObjects(2, h, FALSE, 20);
    if (r == WAIT_OBJECT_0 + 1) {
      // An audio frame: the guest callback, which enters G a few times.
      for (int k = 0; k < P.audio_entries; ++k) {
        {
          std::lock_guard<std::recursive_mutex> lk(g_G);
          SpinUs(P.audio_g_us);
        }
        SpinUs(P.audio_work_us);
      }
      g_audio_ticks.fetch_add(1, std::memory_order_relaxed);
      ArmTimer(g_audio_timer, 1000);
    }
    if (g_audio_pause_req.load(std::memory_order_acquire)) {  // AudioSystem pause point
      SetEvent(g_audio_fence);
      WaitForSingleObject(g_audio_resume, INFINITE);
    }
  }
  return 0;
}

void AudioPause() {  // AudioSystem::Pause: request, wake the worker, wait for its fence
  g_audio_pause_req.store(true, std::memory_order_release);
  SetEvent(g_audio_wake);
  WaitForSingleObject(g_audio_fence, INFINITE);
}
void AudioResume() {
  g_audio_pause_req.store(false, std::memory_order_release);
  SetEvent(g_audio_resume);
}

// ---------------------------------------------------------------- UI step tracking + watchdog
std::atomic<uint64_t> g_step_word{0};  // (seq << 8) | step
std::atomic<uint64_t> g_step_t0{0};
uint64_t g_seq = 0;  // UI thread only
std::atomic<uint32_t> g_hangs[kStepCount];
std::atomic<uint64_t> g_hang_epoch{0};
std::atomic<bool> g_rescuing{false};

inline void SetStep(int s) {
  g_step_t0.store(Now(), std::memory_order_relaxed);
  ++g_seq;
  g_step_word.store((g_seq << 8) | uint64_t(s), std::memory_order_release);
}

DWORD WINAPI WatchdogMain(void*) {
  uint64_t handled = 0;
  const uint64_t limit = uint64_t(P.hang_ms * 1000.0 * g_ticks_per_us);
  while (!g_stop.load(std::memory_order_acquire)) {
    Sleep(2);
    const uint64_t w = g_step_word.load(std::memory_order_acquire);
    const int step = int(w & 0xff);
    if (step == kIdle || w == handled) continue;
    const uint64_t t0 = g_step_t0.load(std::memory_order_relaxed);
    const uint64_t now = Now();
    if (now < t0 || now - t0 < limit) continue;
    if (g_step_word.load(std::memory_order_acquire) != w) continue;
    // HANG. Uses no heap, no log, no lock: the guests may hold all of them.
    handled = w;
    g_rescuing.store(true, std::memory_order_release);
    g_hangs[step].fetch_add(1, std::memory_order_relaxed);
    g_hang_epoch.fetch_add(1, std::memory_order_release);
    while (g_step_word.load(std::memory_order_acquire) == w && !g_stop.load()) {
      for (int i = 0; i < kGuests; ++i) ResumeThread(g_guest[i]);  // no-op once at count 0
      Sleep(1);
    }
    g_rescuing.store(false, std::memory_order_release);
  }
  return 0;
}

// ---------------------------------------------------------------- UI side
void* UiAlloc() {
  void* p = malloc(kUiBlock);
  if (p) {
    static_cast<volatile char*>(p)[0] = 1;
    g_escape.store(p, std::memory_order_relaxed);
  }
  return p;
}
void UiFree(void* p) { free(p); }

void UiLog(const char* what) {  // the sink half of REXLOG_INFO: formatted in a stack buffer
  char buf[128];
  static const char prefix[] = "[ui] guest ";
  size_t n = sizeof(prefix) - 1;
  memcpy(buf, prefix, n);
  const size_t w = std::min(strlen(what), sizeof(buf) - n);
  memcpy(buf + n, what, w);
  n += w;
  std::lock_guard<std::mutex> lk(g_sink_mutex);
  SinkWrite(buf, n);
}

void* Snapshot() {  // GetObjectsByType: object table lock + vector allocation
  std::unique_lock<std::shared_mutex> lk(g_T);
  return UiAlloc();
}

void PauseOld(bool guard) {
  SetStep(kPre);
  void* snap = Snapshot();
  SetStep(kSuspend);
  for (int i = 0; i < kGuests; ++i) {
    if (guard) {  // part B: G + T held across SuspendThread until the thread has stopped
      std::lock_guard<std::recursive_mutex> g(g_G);
      std::unique_lock<std::shared_mutex> t(g_T);
      SuspendThread(g_guest[i]);
      CONTEXT ctx = {};
      ctx.ContextFlags = CONTEXT_INTEGER;
      GetThreadContext(g_guest[i], &ctx);
    } else {
      SuspendThread(g_guest[i]);
    }
  }
  SetStep(kAudio);
  AudioPause();
  SetStep(kSink);
  UiLog("suspended");
  SetStep(kHeap);
  UiFree(UiAlloc());  // the log line's heap buffer
  UiFree(snap);       // the snapshot vector dies at scope exit
  SetStep(kIdle);
}

void UnpauseOld() {
  void* snap;
  SetStep(kT);
  {
    std::unique_lock<std::shared_mutex> lk(g_T);
    SetStep(kHeap);
    snap = UiAlloc();
  }
  SetStep(kResume);
  for (int i = 0; i < kGuests; ++i) ResumeThread(g_guest[i]);
  AudioResume();
  UiLog("resumed");
  UiFree(UiAlloc());
  UiFree(snap);
  SetStep(kIdle);
}

struct SavedEntry {
  HANDLE h;
  bool suspended;
};
std::vector<SavedEntry> g_saved;

void PauseNew() {
  SetStep(kPre);
  void* snap = Snapshot();
  g_saved.clear();
  g_saved.reserve(kGuests);
  for (int i = 0; i < kGuests; ++i) g_saved.push_back({g_guest[i], false});
  UiFree(snap);  // released before the suspend loop
  AudioPause();
  UiLog("suspended");
  UiFree(UiAlloc());
  SetStep(kSuspend);  // from here to the unpause: no alloc, free, log or lock
  for (auto& e : g_saved) e.suspended = SuspendThread(e.h) != DWORD(-1);
  SetStep(kIdle);
}

void UnpauseNew() {
  SetStep(kResume);
  for (auto& e : g_saved) {
    if (e.suspended) ResumeThread(e.h);
  }
  AudioResume();
  UiLog("resumed");
  UiFree(UiAlloc());
  g_saved.clear();
  SetStep(kIdle);
}

void Gap(HANDLE timer, uint32_t us) {
  if (!us) return;
  ArmTimer(timer, us);
  WaitForSingleObject(timer, INFINITE);
}

HANDLE MakeTimer() {
  HANDLE t = CreateWaitableTimerExW(nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,
                                    TIMER_ALL_ACCESS);
  if (!t) t = CreateWaitableTimerExW(nullptr, nullptr, 0, TIMER_ALL_ACCESS);
  return t;
}

double Pct(std::vector<float>& v, int n, double p) {
  if (n <= 0) return 0;
  std::sort(v.begin(), v.begin() + n);
  size_t k = size_t(p * double(n - 1) + 0.5);
  if (k >= size_t(n)) k = size_t(n) - 1;
  return v[k];
}

}  // namespace

int main(int argc, char** argv) {
  for (int i = 1; i < argc; ++i) {
    const char* eq = strchr(argv[i], '=');
    if (!eq) continue;
    const std::string k(argv[i], size_t(eq - argv[i])), v(eq + 1);
    if (k == "mode") P.mode = v == "new" ? kNew : v == "guard" ? kGuard : kOld;
    else if (k == "cycles") P.cycles = atoi(v.c_str());
    else if (k == "seed") P.seed = strtoull(v.c_str(), nullptr, 10);
    else if (k == "max_s") P.max_s = atof(v.c_str());
    else if (k == "hang_ms") P.hang_ms = atof(v.c_str());
    else if (k == "gap_us") P.gap_us = atoi(v.c_str());
    else if (k == "sink_us") P.sink_us = atof(v.c_str());
    else if (k == "g_us") P.g_us = atof(v.c_str());
    else if (k == "t_us") P.t_us = atof(v.c_str());
    else if (k == "free_us") P.free_us = atof(v.c_str());
    else if (k == "audio_entries") P.audio_entries = atoi(v.c_str());
    else if (k == "audio_g_us") P.audio_g_us = atof(v.c_str());
    else if (k == "audio_work_us") P.audio_work_us = atof(v.c_str());
    else fprintf(stderr, "unknown arg %s\n", argv[i]);
  }
  LARGE_INTEGER f;
  QueryPerformanceFrequency(&f);
  g_ticks_per_us = double(f.QuadPart) / 1e6;

  g_audio_wake = CreateEventW(nullptr, FALSE, FALSE, nullptr);
  g_audio_fence = CreateEventW(nullptr, FALSE, FALSE, nullptr);
  g_audio_resume = CreateEventW(nullptr, FALSE, FALSE, nullptr);
  g_audio_timer = MakeTimer();
  HANDLE ui_timer = MakeTimer();

  std::vector<float> pause_us(size_t(std::max(P.cycles, 1))), unpause_us(pause_us.size());
  float max_pause_ok = 0, max_unpause_ok = 0;
  g_saved.reserve(kGuests);
  UiLog("start");  // warm the CRT / sink paths on this thread
  UiFree(UiAlloc());

  for (int i = 0; i < kGuests; ++i)
    g_guest[i] = CreateThread(nullptr, 0, GuestMain, reinterpret_cast<void*>(intptr_t(i)), 0, nullptr);
  HANDLE audio = CreateThread(nullptr, 0, AudioMain, nullptr, 0, nullptr);
  HANDLE wd = CreateThread(nullptr, 0, WatchdogMain, nullptr, 0, nullptr);
  Sleep(300);

  Rng rng{P.seed * 0x2545F4914F6CDD1Dull + 7};
  const uint64_t t_start = Now();
  const uint64_t iters0 = g_guest_iters.load();
  const uint64_t ticks0 = g_audio_ticks.load();
  int done = 0, ok = 0, hang_cycles = 0;
  while (done < P.cycles) {
    while (g_rescuing.load(std::memory_order_acquire)) Sleep(1);
    Gap(ui_timer, rng.Below(uint32_t(P.gap_us) + 1));
    const uint64_t epoch0 = g_hang_epoch.load(std::memory_order_acquire);
    const uint64_t a = Now();
    if (P.mode == kNew) PauseNew();
    else PauseOld(P.mode == kGuard);
    const uint64_t b = Now();
    Gap(ui_timer, rng.Below(uint32_t(P.gap_us) + 1));
    const uint64_t c = Now();
    if (P.mode == kNew) UnpauseNew();
    else UnpauseOld();
    const uint64_t d = Now();
    if (g_hang_epoch.load(std::memory_order_acquire) != epoch0) {
      ++hang_cycles;
    } else {
      pause_us[ok] = float(double(b - a) / g_ticks_per_us);
      unpause_us[ok] = float(double(d - c) / g_ticks_per_us);
      max_pause_ok = std::max(max_pause_ok, pause_us[ok]);
      max_unpause_ok = std::max(max_unpause_ok, unpause_us[ok]);
      ++ok;
    }
    ++done;
    if (double(Now() - t_start) / g_ticks_per_us / 1e6 > P.max_s) break;
  }
  const double elapsed = double(Now() - t_start) / g_ticks_per_us / 1e6;
  const uint64_t iters = g_guest_iters.load() - iters0;
  const uint64_t ticks = g_audio_ticks.load() - ticks0;

  g_stop.store(true, std::memory_order_release);
  for (int i = 0; i < kGuests; ++i) {
    DWORD r;
    do { r = ResumeThread(g_guest[i]); } while (r != DWORD(-1) && r > 1);
  }
  g_audio_pause_req.store(false);
  SetEvent(g_audio_resume);
  SetEvent(g_audio_wake);
  WaitForMultipleObjects(kGuests, g_guest, TRUE, 10000);
  WaitForSingleObject(audio, 5000);
  WaitForSingleObject(wd, 5000);

  uint32_t total = 0;
  for (int s = 0; s < kStepCount; ++s) total += g_hangs[s].load();
  printf("RESULT mode=%s cycles=%d hang_cycles=%d hangs=%u", kModeName[P.mode], done, hang_cycles,
         total);
  for (int s = 1; s < kStepCount; ++s) printf(" h_%s=%u", kStepName[s], g_hangs[s].load());
  printf(" pause_p50_us=%.1f pause_p99_us=%.1f pause_max_us=%.1f unpause_p50_us=%.1f"
         " unpause_p99_us=%.1f unpause_max_us=%.1f elapsed_s=%.2f guest_iters_per_s=%.0f"
         " audio_ticks_per_s=%.0f\n",
         Pct(pause_us, ok, 0.50), Pct(pause_us, ok, 0.99), double(max_pause_ok),
         Pct(unpause_us, ok, 0.50), Pct(unpause_us, ok, 0.99), double(max_unpause_ok), elapsed,
         double(iters) / elapsed, double(ticks) / elapsed);
  return 0;
}
