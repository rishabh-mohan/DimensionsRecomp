// Shim for bench_timerq (Agent 11): REXLOG_INFO for the staged timer_queue.cpp. The staged code
// logs one fixed string (no format arguments); the bench prints it so the run log shows it.
#pragma once
#include <cstdio>
#define REXLOG_INFO(...) (std::printf("[log info] %s\n", __VA_ARGS__), std::fflush(stdout))
