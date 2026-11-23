// Microbench for rexlego/src/discord_presence.cpp: the old background thread
// (20 x sleep_for(100 ms) per 2 s tick) against the new one (a single
// condition_variable::wait_for(2 s) that Stop() wakes). Same driver, one exe
// per variant (-DBENCH_OLD selects the label; the build links the matching
// discord_presence.cpp).
//
//   bench_discord_<v>.exe [window_s=10] [stop_samples=10]
//
// Start(), then count the discord thread's context switches (= wake-ups) over
// the window, then time Stop(); then |stop_samples| more Start() / random
// 60-360 ms / timed Stop() cycles so Stop() lands at random phases.
//
// No real Discord: the discord TU is compiled with -include no_real_discord.h,
// so its CreateFileA calls arrive here and go to a pipe name that cannot exist.
#include <windows.h>

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>

#include "discord_presence.h"

#include "../common/bench_util.h"
#include "../common/wake_count.h"

#ifdef BENCH_OLD
static const char* const kVariant = "old";
#else
static const char* const kVariant = "new";
#endif

namespace {

constexpr const char* kBench = "discord";

std::atomic<uint32_t> g_calls{0};
std::atomic<uint32_t> g_redirected{0};
std::atomic<uint32_t> g_refused{0};
std::atomic<uint32_t> g_opened{0};
std::atomic<DWORD> g_discord_tid{0};

void Result(const std::string& key, double value, const char* unit) {
  benchutil::Result(kBench, kVariant, key, value, unit);
}
void Check(const std::string& name, bool pass, const std::string& detail) {
  benchutil::Check(kBench, kVariant, name, pass, detail);
}

std::string Counters() {
  return "calls=" + std::to_string(g_calls.load()) + " redirected=" +
         std::to_string(g_redirected.load()) + " refused=" + std::to_string(g_refused.load()) +
         " opened=" + std::to_string(g_opened.load());
}

}  // namespace

// Every CreateFileA in discord_presence.cpp lands here (see no_real_discord.h).
extern "C" HANDLE WINAPI bench_CreateFileA(LPCSTR name, DWORD access, DWORD share,
                                           LPSECURITY_ATTRIBUTES security, DWORD disposition,
                                           DWORD flags, HANDLE template_file) {
  g_calls.fetch_add(1, std::memory_order_relaxed);
  g_discord_tid.store(GetCurrentThreadId(), std::memory_order_relaxed);
  static constexpr char kPrefix[] = "\\\\.\\pipe\\discord-ipc-";
  constexpr size_t kPrefixLen = sizeof(kPrefix) - 1;
  if (!name || std::strncmp(name, kPrefix, kPrefixLen) != 0) {
    g_refused.fetch_add(1, std::memory_order_relaxed);
    SetLastError(ERROR_ACCESS_DENIED);
    return INVALID_HANDLE_VALUE;
  }
  const std::string absent = std::string("\\\\.\\pipe\\agent8-bench-absent-ipc-") + (name + kPrefixLen);
  g_redirected.fetch_add(1, std::memory_order_relaxed);
  HANDLE h = CreateFileA(absent.c_str(), access, share, security, disposition, flags, template_file);
  if (h != INVALID_HANDLE_VALUE) {
    // Somebody created our "absent" pipe; never hand it to the source.
    g_opened.fetch_add(1, std::memory_order_relaxed);
    CloseHandle(h);
    SetLastError(ERROR_FILE_NOT_FOUND);
  }
  return INVALID_HANDLE_VALUE;
}

int main(int argc, char** argv) {
  const double window_s = argc > 1 ? std::atof(argv[1]) : 10.0;
  const int stop_samples = argc > 2 ? std::atoi(argv[2]) : 10;
  std::printf("INFO bench=discord variant=%s pid=%lu window_s=%.1f stop_samples=%d\n", kVariant,
              GetCurrentProcessId(), window_s, stop_samples);
  benchutil::HiResWaiter waiter;

  std::vector<wake::ThreadSample> before, after;
  wake::QueryThreads(before);
  legodimensions::discord::Start();
  wake::QueryThreads(after);
  const std::vector<DWORD> fresh = wake::NewThreadIds(before, after);
  std::printf("INFO new_threads=%zu\n", fresh.size());

  // The thread's first Connect() tries all ten pipes at once; it must have
  // gone through the redirect, or nothing below is safe to run.
  int64_t t0 = benchutil::NowNs();
  while (g_redirected.load() < 10 && benchutil::NowNs() - t0 < 1000000000LL) {
    Sleep(1);
  }
  if (g_redirected.load() < 10 || g_refused.load() != 0 || g_opened.load() != 0) {
    legodimensions::discord::Stop();
    Check("no_real_discord_connection", false, "aborted " + Counters());
    return 4;
  }
  // The discord thread is the one that called CreateFileA (the shim records
  // it); the OS sometimes starts a thread-pool worker alongside it.
  const DWORD tid = g_discord_tid.load();
  const bool tid_ok = tid != 0 && tid != GetCurrentThreadId() &&
                      std::find(fresh.begin(), fresh.end(), tid) != fresh.end();
  Check("discord_thread_found", tid_ok,
        "tid=" + std::to_string(tid) + " new_threads=" + std::to_string(fresh.size()));
  if (!tid_ok) {
    legodimensions::discord::Stop();
    return 3;
  }
  Sleep(50);

  const uint32_t calls0 = g_calls.load();
  const uint32_t cs0 = wake::ContextSwitches(tid);
  const uint64_t cy0 = wake::ThreadCycles(tid);
  t0 = benchutil::NowNs();
  waiter.WaitNs(int64_t(window_s * 1e9));
  const uint32_t cs1 = wake::ContextSwitches(tid);
  const uint64_t cy1 = wake::ThreadCycles(tid);
  const int64_t t1 = benchutil::NowNs();
  const uint32_t calls1 = g_calls.load();
  const double secs = double(t1 - t0) / 1e9;
  Result("wakeups_10s", double(cs1 - cs0) * 10.0 / secs, "switches");
  Result("wakeups_per_s", double(cs1 - cs0) / secs, "switches/s");
  Result("kcycles_per_s", double(cy1 - cy0) / secs / 1000.0, "kcycles/s");
  Result("createfile_calls_10s", double(calls1 - calls0) * 10.0 / secs, "calls");

  int64_t s0 = benchutil::NowNs();
  legodimensions::discord::Stop();
  const double first_stop_ms = double(benchutil::NowNs() - s0) / 1e6;
  Result("stop_ms_first", first_stop_ms, "ms");

  std::vector<double> stops{first_stop_ms};
  std::mt19937 rng(GetCurrentProcessId());
  std::uniform_int_distribution<int> delay_us(60000, 360000);
  for (int i = 0; i < stop_samples; ++i) {
    legodimensions::discord::Start();
    waiter.WaitNs(int64_t(delay_us(rng)) * 1000);
    s0 = benchutil::NowNs();
    legodimensions::discord::Stop();
    stops.push_back(double(benchutil::NowNs() - s0) / 1e6);
  }
  const benchutil::Stats st = benchutil::Summarize(stops);
  Result("stop_ms_median", st.median, "ms");
  Result("stop_ms_min", st.min, "ms");
  Result("stop_ms_max", st.max, "ms");
  std::printf("SAMPLES stop_ms");
  for (double v : stops) std::printf(" %.3f", v);
  std::printf("\n");

  const bool safe = g_refused.load() == 0 && g_opened.load() == 0 && g_redirected.load() > 0 &&
                    g_redirected.load() == g_calls.load();
  Check("no_real_discord_connection", safe, Counters());
  std::printf("INFO %s\n", Counters().c_str());
  return safe ? 0 : 5;
}
