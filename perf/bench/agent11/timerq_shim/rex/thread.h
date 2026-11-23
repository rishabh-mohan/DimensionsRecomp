// Shim for bench_timerq (Agent 11): the things timer_queue.cpp takes from rex/thread.h, live
// (set_current_thread_name) and staged (also SleepPrecise, which bench_timerq.cpp defines as the
// SDK's threading_win.cpp does when built with BENCH_STAGED). The real rex/thread/timer_queue.h
// comes from the SDK include dir.
#pragma once
#include <chrono>
#include <string_view>
#include <rex/thread/timer_queue.h>
namespace rex::thread {
void set_current_thread_name(const std::string_view name);
void SleepPrecise(std::chrono::microseconds duration);
}  // namespace rex::thread
