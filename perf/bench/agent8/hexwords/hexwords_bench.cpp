// Agent 8 session 2: HexWords bench (native_skin_diagnostics.cpp).
//
// old_impl::HexWords is the session-1 ostringstream version (hex, setfill('0'),
// setw(8)); new_impl::HexWords is the current manual writer. Both are extracted
// verbatim from the sources by build-journal-hexwords.ps1 into
// build/agent8/hexwords/hexwords_extracted.h, so this tests the real code.
//
//   1. Equality: identical strings for edge counts (0, 1, ... 2048 words), the
//      extreme values (0, 0xFFFFFFFF, ...) and 200k random cases whose words
//      have 0-8 significant hex digits (so leading-zero padding is exercised).
//   2. Timing: ns per call for the word counts the diagnostics log (8, 16, 32,
//      48, 64, 84), median/min/max of --runs interleaved runs. Times are thread
//      CPU time (bench_clock.h: QueryThreadCycleTime, so preemption by other
//      agents' builds is excluded); the wall-clock median is printed alongside.
//
// Usage: hexwords_bench.exe [--runs N] [--quick] [--normal-priority]
#include "hexwords_extracted.h"
#include "../journal/bench_clock.h"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>

namespace {

uint32_t RandomWord(std::mt19937_64& rng) {
  const uint32_t digits = uint32_t(rng() % 9);
  return digits ? uint32_t(rng()) >> (32 - 4 * digits) : 0u;
}

template <class F>
bench::Measure NsPerCall(F&& f, const std::vector<uint32_t>& words, uint32_t count, int calls,
                         uint64_t& sink) {
  const bench::Stopwatch watch;
  for (int i = 0; i < calls; ++i) sink += f(words.data(), count).size();
  return watch.PerOp(calls);
}

}  // namespace

int main(int argc, char** argv) {
  int runs = 7;
  bool quick = false, raise_priority = true;
  for (int i = 1; i < argc; ++i) {
    if (!std::strcmp(argv[i], "--runs") && i + 1 < argc) runs = std::atoi(argv[++i]);
    else if (!std::strcmp(argv[i], "--quick")) quick = true;
    else if (!std::strcmp(argv[i], "--normal-priority")) raise_priority = false;
  }
  std::printf("priority: %s\n", bench::SetBenchPriority(raise_priority));
  bench::PrintCalibration();
  std::mt19937_64 rng(0x4e5c2026);
  std::vector<uint32_t> words(2048);
  uint64_t cases = 0, mismatches = 0, chars = 0;
  auto check = [&](uint32_t count) {
    const std::string a = old_impl::HexWords(words.data(), count);
    const std::string b = new_impl::HexWords(words.data(), count);
    ++cases;
    chars += a.size();
    if (a != b && mismatches++ < 5) {
      std::printf("  MISMATCH count=%u\n    old=%.80s\n    new=%.80s\n", count, a.c_str(),
                  b.c_str());
    }
  };
  const uint32_t edge_counts[] = {0, 1, 2, 3, 7, 8, 9, 16, 32, 48, 64, 84, 255, 1024, 2048};
  const uint32_t special[] = {0u,          0xFFFFFFFFu, 0xFu,        0xF0000000u, 0x80000000u,
                              0x00000001u, 0x0000FFFFu, 0x12345678u, 0x9ABCDEF0u, 0x0F0F0F0Fu};
  for (uint32_t count : edge_counts) {
    for (uint32_t i = 0; i < count; ++i) words[i] = special[i % std::size(special)];
    check(count);
    for (uint32_t i = 0; i < count; ++i) words[i] = RandomWord(rng);
    check(count);
  }
  const int random_cases = quick ? 20000 : 200000;
  for (int c = 0; c < random_cases; ++c) {
    const uint32_t count = (c % 1000 == 0) ? uint32_t(rng() % 2049) : uint32_t(rng() % 101);
    for (uint32_t i = 0; i < count; ++i) words[i] = RandomWord(rng);
    check(count);
  }
  std::printf("EQUALITY %s: cases=%llu chars=%llu mismatches=%llu\n", mismatches ? "FAIL" : "PASS",
              (unsigned long long)cases, (unsigned long long)chars,
              (unsigned long long)mismatches);

  uint64_t sink = 0;
  for (uint32_t i = 0; i < 2048; ++i) words[i] = uint32_t(rng());
  std::printf("\n%-24s %10s %10s %10s %11s %8s %5s\n", "HexWords (cpu ns/call)", "median", "min",
              "max", "wall median", "speedup", "runs");
  const int old_calls = quick ? 2000 : 20000;
  const int new_calls = quick ? 20000 : 200000;
  for (uint32_t count : {8u, 16u, 32u, 48u, 64u, 84u}) {
    std::vector<double> old_cpu, new_cpu, old_wall, new_wall;
    auto run = [&](bool is_new) {
      const bench::Measure m =
          is_new ? NsPerCall(new_impl::HexWords, words, count, new_calls, sink)
                 : NsPerCall(old_impl::HexWords, words, count, old_calls, sink);
      (is_new ? new_cpu : old_cpu).push_back(m.cpu);
      (is_new ? new_wall : old_wall).push_back(m.wall);
    };
    for (int r = 0; r < runs; ++r) {
      run((r & 1) != 0);  // interleaved, alternating which goes first
      run((r & 1) == 0);
    }
    const double om = bench::Median(old_cpu), nm = bench::Median(new_cpu);
    std::printf("old  %3u words %13.1f %10.1f %10.1f %11.1f %8s %5d\n", count, om,
                bench::Min(old_cpu), bench::Max(old_cpu), bench::Median(old_wall), "", runs);
    std::printf("new  %3u words %13.1f %10.1f %10.1f %11.1f %7.1fx %5d\n", count, nm,
                bench::Min(new_cpu), bench::Max(new_cpu), bench::Median(new_wall), om / nm, runs);
  }
  std::printf("\n(sink %llu)\nRESULT %s\n", (unsigned long long)sink, mismatches ? "FAIL" : "PASS");
  return mismatches ? 1 : 0;
}
