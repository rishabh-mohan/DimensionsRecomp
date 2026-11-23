// Microbench for rexlego/src/cheat_engine.{h,cpp}: the old copy
// (bench/agent8/cheat/old, namespace cheats_old) against the current source,
// with this same driver compiled into one exe per variant (-DBENCH_OLD).
//
//   bench_cheat_<v>.exe take [budget_ms]
//     TakeResults(200) per call in four scenarios, correctness of every
//     TakeResults against a brute-force walk of the same memory, cache refresh
//     after a narrowing scan, and the per-row cost ImGuiListClipper avoids.
//   bench_cheat_<v>.exe freeze
//     Freeze-thread wake-ups idle (5 s) and with one frozen value (2 s), how
//     often the frozen value is re-applied, and destructor latency.
//
// Guest memory: a 512 MiB reservation (the engine's kPhysicalSize) with 40 MiB
// committed: 8 MiB at 0, 1 MiB at every 16 MiB boundary, and the last 1 MiB.
// The candidate bitmap always covers all 512 MiB (16 MiB of bitmap for 32-bit
// scans, 64 MiB for 8-bit), so a walk of it costs what it costs in the game;
// only the scans themselves are cheaper than over fully committed RAM.
#include <windows.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <random>
#include <string>
#include <thread>
#include <vector>

#include <rex/logging.h>  // bench stub: rexbench::g_log_calls
#include <rex/system/xmemory.h>

#ifdef BENCH_OLD
#include "old/cheat_engine.h"
namespace ce = legodimensions::cheats_old;
static const char* const kVariant = "old";
#else
#include "cheat_engine.h"
namespace ce = legodimensions::cheats;
static const char* const kVariant = "new";
#endif

#include "../common/bench_util.h"
#include "../common/wake_count.h"

using benchutil::NowNs;
using Engine = ce::CheatEngine;
using VT = Engine::ValueType;

namespace {

constexpr const char* kBench = "cheat";
constexpr uint32_t kPhys = 0x20000000;  // kPhysicalSize in cheat_engine.cpp
constexpr uint32_t kMiB = 1u << 20;

struct Chunk {
  uint32_t start;
  uint32_t size;
};

std::vector<Chunk> g_chunks;
uint8_t* g_base = nullptr;

void Result(const std::string& key, double value, const char* unit) {
  benchutil::Result(kBench, kVariant, key, value, unit);
}
void Check(const std::string& name, bool pass, const std::string& detail) {
  benchutil::Check(kBench, kVariant, name, pass, detail);
}

bool SetupMemory(bool full_layout) {
  g_base = static_cast<uint8_t*>(VirtualAlloc(nullptr, kPhys, MEM_RESERVE, PAGE_NOACCESS));
  if (!g_base) {
    return false;
  }
  g_chunks.clear();
  g_chunks.push_back({0, 8 * kMiB});
  if (full_layout) {
    for (uint32_t k = 1; k < 32; ++k) {
      g_chunks.push_back({k * 16 * kMiB, kMiB});
    }
    g_chunks.push_back({kPhys - kMiB, kMiB});
  }
  for (const Chunk& c : g_chunks) {
    if (!VirtualAlloc(g_base + c.start, c.size, MEM_COMMIT, PAGE_READWRITE)) {
      return false;
    }
  }
  return true;
}

void ClearMemory() {
  for (const Chunk& c : g_chunks) {
    std::memset(g_base + c.start, 0, c.size);
  }
}

void PutBE32(uint32_t addr, uint32_t v) {
  g_base[addr + 0] = uint8_t(v >> 24);
  g_base[addr + 1] = uint8_t(v >> 16);
  g_base[addr + 2] = uint8_t(v >> 8);
  g_base[addr + 3] = uint8_t(v);
}

uint32_t GetBE32(uint32_t addr) {
  return (uint32_t(g_base[addr]) << 24) | (uint32_t(g_base[addr + 1]) << 16) |
         (uint32_t(g_base[addr + 2]) << 8) | uint32_t(g_base[addr + 3]);
}

// Driver-side accesses to a word the freeze thread writes concurrently.
uint32_t AtomicLoadBE32(uint32_t addr) {
  std::atomic_ref<uint32_t> word(*reinterpret_cast<uint32_t*>(g_base + addr));
  return _byteswap_ulong(word.load(std::memory_order_relaxed));
}
void AtomicStoreBE32(uint32_t addr, uint32_t v) {
  std::atomic_ref<uint32_t> word(*reinterpret_cast<uint32_t*>(g_base + addr));
  word.store(_byteswap_ulong(v), std::memory_order_relaxed);
}

std::filesystem::path NoSavePath() {
  // A directory that does not exist: Load() and Save() fail fast instead of
  // adding file I/O to the timings (the save cost is the same old and new).
  wchar_t exe[MAX_PATH];
  GetModuleFileNameW(nullptr, exe, MAX_PATH);
  return std::filesystem::path(exe).parent_path() / L"agent8-no-such-dir" / L"cheats.txt";
}

void WaitScan(const Engine& engine) {
  // Poll every ~0.2 ms on a high-resolution timer: precise enough for scans of
  // tens of ms, without the driver burning a second core next to the worker.
  static benchutil::HiResWaiter waiter;
  while (engine.scanning()) {
    waiter.WaitNs(200000);
  }
}

size_t SlotSize(VT type) { return Engine::ValueTypeSize(type); }

// Every aligned slot of |type| in committed memory whose value equals |value|,
// lowest first: what an exact scan from "everything is a candidate" keeps.
std::vector<uint32_t> BruteForce(VT type, uint32_t value) {
  std::vector<uint32_t> out;
  const uint32_t size = uint32_t(SlotSize(type));
  for (const Chunk& c : g_chunks) {
    for (uint32_t a = c.start; a + size <= c.start + c.size; a += size) {
      const uint32_t v = size == 1 ? g_base[a] : GetBE32(a);
      if (v == value) {
        out.push_back(a);
      }
    }
  }
  return out;
}

bool PrefixEqual(const std::vector<uint32_t>& got, const std::vector<uint32_t>& all, size_t limit) {
  const size_t n = std::min(limit, all.size());
  return got.size() == n && std::equal(got.begin(), got.end(), all.begin());
}

struct Scenario {
  std::string id;
  std::string desc;
  VT type;
  uint32_t value;
  std::vector<uint32_t> hits;
};

std::vector<Scenario> MakeScenarios() {
  std::vector<Scenario> list;
  {
    // 200 hits spread over the whole address space: 6 per committed chunk, 8
    // in the last one, so the 200th sits in the last MiB.
    Scenario s{"a", "32-bit exact, 200 hits spread over 512 MiB", VT::kUInt32, 0x13572468u, {}};
    for (size_t ci = 0; ci < g_chunks.size(); ++ci) {
      const int n = ci + 1 == g_chunks.size() ? 8 : 6;
      for (int t = 0; t < n; ++t) {
        s.hits.push_back(g_chunks[ci].start + uint32_t(t) * 128 * 1024 + 0x40);
      }
    }
    list.push_back(std::move(s));
  }
  {
    Scenario s{"b", "32-bit exact, 5 hits in the last MiB", VT::kUInt32, 0x2468ACE1u, {}};
    for (uint32_t k = 0; k < 5; ++k) {
      s.hits.push_back(kPhys - kMiB + k * 64 * 1024 + 0x80);
    }
    list.push_back(std::move(s));
  }
  {
    Scenario s{"c", "8-bit exact, 5 hits in the last MiB", VT::kUInt8, 0xA5u, {}};
    for (uint32_t k = 0; k < 5; ++k) {
      s.hits.push_back(kPhys - kMiB + k * 64 * 1024 + 0x81 + k);
    }
    list.push_back(std::move(s));
  }
  {
    Scenario s{"d", "32-bit exact, 1,000,000 hits dense from 0", VT::kUInt32, 0x0BADF00Du, {}};
    s.hits.reserve(1000000);
    for (uint32_t i = 0; i < 1000000; ++i) {
      s.hits.push_back(i * 4);
    }
    list.push_back(std::move(s));
  }
  return list;
}

void Plant(const Scenario& s) {
  for (uint32_t a : s.hits) {
    if (s.type == VT::kUInt8) {
      g_base[a] = uint8_t(s.value);
    } else {
      PutBE32(a, s.value);
    }
  }
}

// Per-call cost of TakeResults(limit): batches sized to >= 50 us so the
// 100 ns QPC tick does not dominate fast calls; at least 15 samples, then
// until |budget_ms| is spent.
benchutil::Stats TimeTake(const Engine& engine, size_t limit, double budget_ms, uint64_t& sink) {
  const int64_t w0 = NowNs();
  for (int i = 0; i < 3; ++i) {
    const auto r = engine.TakeResults(limit);
    sink += r.size();
  }
  const double estimate = double(NowNs() - w0) / 3.0;
  const int batch =
      estimate >= 50000.0 ? 1 : int(std::min(4096.0, std::ceil(50000.0 / std::max(estimate, 1.0))));
  std::vector<double> per_call;
  const int64_t start = NowNs();
  while (per_call.size() < 15 ||
         (double(NowNs() - start) < budget_ms * 1e6 && per_call.size() < 5000)) {
    const int64_t a = NowNs();
    for (int i = 0; i < batch; ++i) {
      const auto r = engine.TakeResults(limit);
      sink += r.size() + (r.empty() ? 0 : r.back());
    }
    const int64_t b = NowNs();
    per_call.push_back(double(b - a) / double(batch));
  }
  return benchutil::Summarize(per_call);
}

// What DrawResults does per submitted row, minus ImGui itself: ReadValue
// (VirtualQuery + load) and IsFrozen (freeze lock), and the label snprintf.
void Rows(const Engine& engine, const std::vector<uint32_t>& rows, uint64_t& sink) {
  std::vector<double> plain, labeled;
  char label[64];
  for (int pass = 0; pass < 100; ++pass) {
    int64_t a = NowNs();
    for (uint32_t addr : rows) {
      const double v = engine.ReadValue(addr, engine.scan_type());
      const bool frozen = engine.IsFrozen(addr);
      sink += uint64_t(v) + (frozen ? 1 : 0);
    }
    int64_t b = NowNs();
    plain.push_back(double(b - a) / double(rows.size()));
    a = NowNs();
    for (uint32_t addr : rows) {
      const double current = engine.ReadValue(addr, engine.scan_type());
      std::snprintf(label, sizeof(label), "%08X = %.6g%s", addr, current,
                    engine.IsFrozen(addr) ? "  [frozen]" : "");
      sink += uint8_t(label[9]);
    }
    b = NowNs();
    labeled.push_back(double(b - a) / double(rows.size()));
  }
  const benchutil::Stats p = benchutil::Summarize(plain);
  const benchutil::Stats l = benchutil::Summarize(labeled);
  Result("row_read_isfrozen_ns", p.median, "ns/row");
  Result("row_read_isfrozen_snprintf_ns", l.median, "ns/row");
  Result("rows200_per_frame_us", p.median * 200 / 1000.0, "us/frame");
  Result("rows8_per_frame_us", p.median * 8 / 1000.0, "us/frame");
  Result("rows200_snprintf_per_frame_us", l.median * 200 / 1000.0, "us/frame");
  Result("rows8_snprintf_per_frame_us", l.median * 8 / 1000.0, "us/frame");
}

int RunTake(double budget_ms) {
  if (!SetupMemory(true)) {
    std::fprintf(stderr, "VirtualAlloc failed (%lu)\n", GetLastError());
    return 2;
  }
  rex::memory::Memory memory(g_base);
  uint64_t sink = 0;
  std::vector<Scenario> scenarios = MakeScenarios();
  Engine engine(&memory, NoSavePath());
  bool first = true;
  for (const Scenario& sc : scenarios) {
    ClearMemory();
    Plant(sc);
    const std::vector<uint32_t> all = BruteForce(sc.type, sc.value);
    Check("plant_" + sc.id, all == sc.hits,
          "brute_force=" + std::to_string(all.size()) + " planted=" + std::to_string(sc.hits.size()));

    int64_t t0 = NowNs();
    engine.StartNewScan(sc.type);
    WaitScan(engine);
    const double new_scan_ms = double(NowNs() - t0) / 1e6;
    {
      const auto r200 = engine.TakeResults(200);
      const auto r5000 = engine.TakeResults(5000);
      const bool ok = r200.empty() && r5000.empty() && engine.result_count() == 0 && engine.unfiltered();
      Check("newscan_clears_" + sc.id, ok,
            std::string(first ? "first_scan" : "after_previous_results") + " r200=" +
                std::to_string(r200.size()) + " count=" + std::to_string(engine.result_count()));
    }

    t0 = NowNs();
    engine.StartScanExact(double(sc.value));
    WaitScan(engine);
    const double exact_scan_ms = double(NowNs() - t0) / 1e6;
    Result("scan_new_ms_" + sc.id, new_scan_ms, "ms");
    Result("scan_exact_ms_" + sc.id, exact_scan_ms, "ms");

    const auto r200 = engine.TakeResults(200);
    const auto r5000 = engine.TakeResults(5000);
    Check("take200_" + sc.id, PrefixEqual(r200, all, 200) && engine.result_count() == all.size(),
          "got=" + std::to_string(r200.size()) + " count=" + std::to_string(engine.result_count()) +
              " expected_count=" + std::to_string(all.size()));
    Check("take5000_" + sc.id, PrefixEqual(r5000, all, 5000), "got=" + std::to_string(r5000.size()));
    {
      // Around the 1024-entry cache boundary, both sides.
      bool ok = true;
      std::string bad;
      for (size_t limit : {size_t(1), size_t(199), size_t(1023), size_t(1024), size_t(1025),
                           size_t(4096)}) {
        if (!PrefixEqual(engine.TakeResults(limit), all, limit)) {
          ok = false;
          bad += std::to_string(limit) + ",";
        }
      }
      Check("take_limits_" + sc.id, ok, ok ? "1,199,1023,1024,1025,4096" : "bad=" + bad);
    }

    const benchutil::Stats st = TimeTake(engine, 200, budget_ms, sink);
    Result("take200_ns_" + sc.id, st.median, "ns");
    Result("take200_min_ns_" + sc.id, st.min, "ns");
    Result("take200_samples_" + sc.id, double(st.n), "samples");
    Check("take200_stable_" + sc.id, engine.TakeResults(200) == r200, "");

    if (sc.id == "a") {
      Rows(engine, r200, sink);
      // Narrowing scan: every other hit increases, the rest stay. The results
      // (and so the new cache) must follow.
      std::vector<uint32_t> expect;
      for (size_t i = 0; i < sc.hits.size(); i += 2) {
        PutBE32(sc.hits[i], sc.value + 1);
        expect.push_back(sc.hits[i]);
      }
      engine.StartScanCompare(Engine::CompareOp::kIncreased);
      WaitScan(engine);
      const auto after = engine.TakeResults(200);
      Check("compare_refresh_a", after == expect && engine.result_count() == expect.size(),
            "got=" + std::to_string(after.size()) + " expected=" + std::to_string(expect.size()));
      engine.StartScanCompare(Engine::CompareOp::kUnchanged);
      WaitScan(engine);
      Check("compare_unchanged_a", engine.TakeResults(5000) == expect, "");
    }
    first = false;
  }
  std::printf("SINK %llu log_calls=%u\n", (unsigned long long)sink, rexbench::g_log_calls.load());
  return 0;
}

int RunFreeze() {
  if (!SetupMemory(false)) {
    std::fprintf(stderr, "VirtualAlloc failed (%lu)\n", GetLastError());
    return 2;
  }
  rex::memory::Memory memory(g_base);
  const std::filesystem::path save = NoSavePath();
  benchutil::HiResWaiter waiter;
  Result("hires_timer", waiter.high_res() ? 1 : 0, "bool");

  Sleep(300);  // let start-up thread-pool workers settle before the snapshot
  std::vector<wake::ThreadSample> before, after;
  wake::QueryThreads(before);
  Engine* engine = new Engine(&memory, save);
  wake::QueryThreads(after);
  const std::vector<DWORD> fresh = wake::NewThreadIds(before, after);
  std::printf("INFO new_threads=%zu\n", fresh.size());
  DWORD tid = fresh.size() == 1 ? fresh.front() : 0;
  if (fresh.size() > 1) {
    // The OS started another thread (a thread-pool worker) at the same moment.
    // The freeze thread is the one that wakes every 50 ms while a value is
    // frozen: freeze one briefly to tell them apart, then unfreeze it.
    std::vector<uint32_t> c0;
    for (DWORD t : fresh) c0.push_back(wake::ContextSwitches(t));
    engine->SetFrozen(0x00200000, VT::kUInt32, 1.0, true);
    Sleep(400);
    engine->SetFrozen(0x00200000, VT::kUInt32, 1.0, false);
    uint32_t best = 0;
    for (size_t i = 0; i < fresh.size(); ++i) {
      const uint32_t c1 = wake::ContextSwitches(fresh[i]);
      if (c0[i] != UINT32_MAX && c1 != UINT32_MAX && c1 - c0[i] > best) {
        best = c1 - c0[i];
        tid = fresh[i];
      }
    }
    std::printf("INFO picked tid=%lu by probe (%u switches in 400 ms)\n", tid, best);
  }
  Check("freeze_thread_found", tid != 0, "new_threads=" + std::to_string(fresh.size()));
  if (tid == 0) {
    delete engine;
    return 3;
  }
  Sleep(250);

  // Idle: nothing frozen, no cheats.
  uint32_t cs0 = wake::ContextSwitches(tid);
  uint64_t cy0 = wake::ThreadCycles(tid);
  int64_t t0 = NowNs();
  std::this_thread::sleep_for(std::chrono::seconds(5));
  uint32_t cs1 = wake::ContextSwitches(tid);
  uint64_t cy1 = wake::ThreadCycles(tid);
  int64_t t1 = NowNs();
  double secs = double(t1 - t0) / 1e9;
  Result("idle_wakeups_5s", double(cs1 - cs0), "switches");
  Result("idle_wakeups_per_s", double(cs1 - cs0) / secs, "switches/s");
  Result("idle_kcycles_per_s", double(cy1 - cy0) / secs / 1000.0, "kcycles/s");

  // One frozen value. The driver corrupts it whenever it finds it restored
  // (polling every ~1 ms), so each restore the freeze thread makes is counted.
  const uint32_t kAddr = 0x00100000;
  const uint32_t kFrozen = 0x11223344;
  const uint32_t kCorrupt = 0xDEADBEEF;
  AtomicStoreBE32(kAddr, kCorrupt);
  engine->SetFrozen(kAddr, VT::kUInt32, double(kFrozen), true);
  Sleep(250);
  int restores = 0;
  int polls = 0;
  cs0 = wake::ContextSwitches(tid);
  cy0 = wake::ThreadCycles(tid);
  t0 = NowNs();
  while (NowNs() - t0 < 2000000000LL) {
    if (AtomicLoadBE32(kAddr) == kFrozen) {
      ++restores;
      AtomicStoreBE32(kAddr, kCorrupt);
    }
    ++polls;
    waiter.WaitNs(1000000);
  }
  cs1 = wake::ContextSwitches(tid);
  cy1 = wake::ThreadCycles(tid);
  t1 = NowNs();
  secs = double(t1 - t0) / 1e9;
  Result("frozen_restores_2s", double(restores) * 2.0 / secs, "restores");
  Result("frozen_wakeups_2s", double(cs1 - cs0) * 2.0 / secs, "switches");
  Result("frozen_kcycles_per_s", double(cy1 - cy0) / secs / 1000.0, "kcycles/s");
  Result("frozen_polls_2s", double(polls), "polls");
  Check("frozen_value_reapplied", restores >= 20, "restores=" + std::to_string(restores));

  // Destructor latency at a random phase of the freeze thread's 50 ms cycle.
  std::vector<double> dtor_idle, dtor_frozen;
  int64_t d0 = NowNs();
  delete engine;
  dtor_frozen.push_back(double(NowNs() - d0) / 1e6);
  std::mt19937 rng(GetCurrentProcessId());
  std::uniform_int_distribution<int> delay_us(5000, 125000);
  for (int i = 0; i < 16; ++i) {
    const bool frozen = (i & 1) != 0;
    Engine* e = new Engine(&memory, save);
    if (frozen) {
      e->SetFrozen(kAddr, VT::kUInt32, double(kFrozen), true);
    }
    waiter.WaitNs(int64_t(delay_us(rng)) * 1000);
    d0 = NowNs();
    delete e;
    (frozen ? dtor_frozen : dtor_idle).push_back(double(NowNs() - d0) / 1e6);
  }
  const benchutil::Stats di = benchutil::Summarize(dtor_idle);
  const benchutil::Stats df = benchutil::Summarize(dtor_frozen);
  Result("dtor_idle_ms_median", di.median, "ms");
  Result("dtor_idle_ms_max", di.max, "ms");
  Result("dtor_frozen_ms_median", df.median, "ms");
  Result("dtor_frozen_ms_max", df.max, "ms");
  std::printf("SAMPLES dtor_idle_ms");
  for (double v : dtor_idle) std::printf(" %.3f", v);
  std::printf("\nSAMPLES dtor_frozen_ms");
  for (double v : dtor_frozen) std::printf(" %.3f", v);
  std::printf("\nINFO log_calls=%u\n", rexbench::g_log_calls.load());
  return 0;
}

}  // namespace

int main(int argc, char** argv) {
  const std::string mode = argc > 1 ? argv[1] : "take";
  std::printf("INFO bench=cheat variant=%s mode=%s pid=%lu\n", kVariant, mode.c_str(),
              GetCurrentProcessId());
  if (mode == "take") {
    return RunTake(argc > 2 ? std::atof(argv[2]) : 250.0);
  }
  if (mode == "freeze") {
    return RunFreeze();
  }
  std::fprintf(stderr, "usage: %s take [budget_ms] | freeze\n", argv[0]);
  return 1;
}
