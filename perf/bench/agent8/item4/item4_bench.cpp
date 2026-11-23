// Agent 8 session 2, item 4: the two off-path guards.
//
//   scene_distance.cpp sub_82C6F428: at the default scale nothing is ever
//   recorded, so instance_distances stays empty. Old: lock, Restore (find +
//   erase on the empty map), unlock. New: lock, empty() check, unlock.
//
//   name_trace.cpp sub_82A3D980 (TT's path hash): trace_file_names is empty by
//   default. Old: build an empty std::string, call the original, test it, destroy
//   it. New: return right after calling the original (a tail call).
//
// Restore/Remember and both hook bodies are copied from the sources (old from
// build/agent8/orig, new from the working copy); the guest call is a noinline
// stub. Checks: identical memory/map results over random sequences with the map
// sometimes non-empty, identical log lines for random names and filters. Then
// thread-CPU ns per call (bench_clock.h), median/min/max of --runs.
//
// Usage: item4_bench.exe [--runs N] [--quick] [--normal-priority]
#include "../journal/bench_clock.h"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <random>
#include <string>
#include <unordered_map>
#include <vector>

using u8 = uint8_t;
using u32 = uint32_t;

namespace {

// ---- scene_distance.cpp (verbatim helpers) ---------------------------------
struct AppliedDistance {
  std::array<u8,32> baseline{},scaled{};
  size_t size=0;
};
void Restore(std::unordered_map<u32,AppliedDistance>& records,u32 address,u8* base){
  if(!address)return;
  auto it=records.find(address);
  if(it!=records.end()&&!std::memcmp(base+address,it->second.scaled.data(),it->second.size))
    std::memcpy(base+address,it->second.baseline.data(),it->second.size);
  records.erase(address);
}
void Remember(std::unordered_map<u32,AppliedDistance>& records,u32 address,
    const AppliedDistance& record){
  if(records.size()>=1024)records.erase(records.begin());
  records[address]=record;
}

struct SceneState {
  std::mutex distance_mutex;
  std::unordered_map<u32,AppliedDistance> instance_distances;
};

__declspec(noinline) void SceneOld(SceneState& s,u32 instance,u8* base){
  std::unique_lock lock(s.distance_mutex);
  Restore(s.instance_distances,instance,base);
  lock.unlock();
}
__declspec(noinline) void SceneNew(SceneState& s,u32 instance,u8* base){
  std::unique_lock lock(s.distance_mutex);
  // Nothing is recorded at the default scale; skip the two hash lookups.
  if(!s.instance_distances.empty())Restore(s.instance_distances,instance,base);
  lock.unlock();
}

// ---- name_trace.cpp ----------------------------------------------------------
struct Ctx { uint64_t r3; };
std::vector<std::string>* g_log = nullptr;
std::string& FilterStorage() {
  static std::string storage;
  return storage;
}
__declspec(noinline) void ImpHash(Ctx& ctx, u8* base) {  // stands in for __imp__sub_82A3D980
  (void)base;
  ctx.r3 = ctx.r3 * 0x199933u + 1;
}
void Log(u32 hash, const std::string& name) {
  if (g_log) g_log->push_back(std::to_string(hash) + " " + name);
}

__declspec(noinline) void NameOld(Ctx& ctx, u8* base) {
  const std::string& filter = FilterStorage();
  std::string name;
  if (!filter.empty()) {
    uint32_t record = uint32_t(ctx.r3);
    uint32_t ptr;
    uint16_t len;
    std::memcpy(&ptr, base + record, 4);
    std::memcpy(&len, base + record + 6, 2);
    ptr = __builtin_bswap32(ptr);
    len = __builtin_bswap16(len);
    if (ptr && len > 0 && len < 512) {
      name.assign(reinterpret_cast<const char*>(base + ptr), len);
      std::transform(name.begin(), name.end(), name.begin(),
                     [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    }
  }
  ImpHash(ctx, base);
  if (name.empty()) return;
  size_t at = 0;
  while (at <= filter.size()) {
    size_t comma = filter.find(',', at);
    if (comma == std::string::npos) comma = filter.size();
    std::string token = filter.substr(at, comma - at);
    std::transform(token.begin(), token.end(), token.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (!token.empty() && name.find(token) != std::string::npos) {
      Log(uint32_t(ctx.r3), name);
      return;
    }
    at = comma + 1;
  }
}

__declspec(noinline) void NameNew(Ctx& ctx, u8* base) {
  const std::string& filter = FilterStorage();
  if (filter.empty()) {  // off (the default): no name to build or match
    ImpHash(ctx, base);
    return;
  }
  std::string name;
  {
    uint32_t record = uint32_t(ctx.r3);
    uint32_t ptr;
    uint16_t len;
    std::memcpy(&ptr, base + record, 4);
    std::memcpy(&len, base + record + 6, 2);
    ptr = __builtin_bswap32(ptr);
    len = __builtin_bswap16(len);
    if (ptr && len > 0 && len < 512) {
      name.assign(reinterpret_cast<const char*>(base + ptr), len);
      std::transform(name.begin(), name.end(), name.begin(),
                     [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    }
  }
  ImpHash(ctx, base);
  if (name.empty()) return;
  size_t at = 0;
  while (at <= filter.size()) {
    size_t comma = filter.find(',', at);
    if (comma == std::string::npos) comma = filter.size();
    std::string token = filter.substr(at, comma - at);
    std::transform(token.begin(), token.end(), token.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (!token.empty() && name.find(token) != std::string::npos) {
      Log(uint32_t(ctx.r3), name);
      return;
    }
    at = comma + 1;
  }
}

void PutBE32(u8* p, u32 v) { v = __builtin_bswap32(v); std::memcpy(p, &v, 4); }
void PutBE16(u8* p, uint16_t v) { v = __builtin_bswap16(v); std::memcpy(p, &v, 2); }

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
  std::mt19937_64 rng(0x17e4a2026);
  uint64_t failures = 0;

  // ---- scene_distance equivalence: two arenas, same operations ----
  {
    constexpr u32 kArena = 1u << 16;
    std::vector<u8> mem_old(kArena), mem_new(kArena);
    for (auto& b : mem_old) b = u8(rng());
    mem_new = mem_old;
    SceneState so, sn;
    const int ops = quick ? 20000 : 200000;
    uint64_t restores_nonempty = 0;
    for (int i = 0; i < ops; ++i) {
      const u32 addr = (rng() % 8 == 0) ? 0u : u32(rng() % 64) * 512u;  // 0 = null instance
      if (rng() % 3 == 0 && addr) {  // a scaled load: remember a record in both
        AppliedDistance rec; rec.size = 32;
        std::memcpy(rec.baseline.data(), mem_old.data() + addr, 32);
        for (auto& b : rec.scaled) b = u8(rng());
        std::memcpy(mem_old.data() + addr, rec.scaled.data(), 32);
        std::memcpy(mem_new.data() + addr, rec.scaled.data(), 32);
        Remember(so.instance_distances, addr, rec);
        Remember(sn.instance_distances, addr, rec);
      }
      if (rng() % 5 == 0 && addr) {  // the game rewrites the instance meanwhile
        const u8 v = u8(rng());
        mem_old[addr + 3] = v; mem_new[addr + 3] = v;
      }
      restores_nonempty += !so.instance_distances.empty();
      SceneOld(so, addr, mem_old.data());
      SceneNew(sn, addr, mem_new.data());
      if (rng() % 64 == 0) { so.instance_distances.clear(); sn.instance_distances.clear(); }
    }
    const bool same = mem_old == mem_new && so.instance_distances.size() == sn.instance_distances.size();
    failures += !same;
    std::printf("scene_distance EQUIVALENCE %s: %d calls (%llu with records), final map size %zu/%zu\n",
                same ? "PASS" : "FAIL", ops, (unsigned long long)restores_nonempty,
                so.instance_distances.size(), sn.instance_distances.size());
  }

  // ---- name_trace equivalence: random names and filters ----
  {
    std::vector<u8> mem(1u << 16, 0);
    const char* words[] = {"Fern", "FINN", "chars\\batman", "levels/Oz", "Gimli", "wyldstyle",
                           "audio\\vo", "ui", "Lord_Vortech", ""};
    std::vector<std::string> log_old, log_new;
    const int cases = quick ? 5000 : 50000;
    for (int c = 0; c < cases; ++c) {
      std::string filter;
      const int tokens = int(rng() % 4);
      for (int t = 0; t < tokens; ++t) {
        if (t) filter += ',';
        filter += words[rng() % std::size(words)];
      }
      FilterStorage() = filter;
      std::string path;
      const int parts = int(rng() % 3);
      for (int p = 0; p < parts; ++p) path += words[rng() % std::size(words)];
      const u32 record = 0x100, str = 0x200;
      PutBE32(mem.data() + record, (rng() % 16) ? str : 0u);
      PutBE16(mem.data() + record + 6, uint16_t(path.size()));
      std::memcpy(mem.data() + str, path.data(), path.size());
      Ctx a{record}, b{record};
      g_log = &log_old; NameOld(a, mem.data());
      g_log = &log_new; NameNew(b, mem.data());
      if (a.r3 != b.r3) ++failures;
    }
    g_log = nullptr;
    FilterStorage().clear();
    const bool same = log_old == log_new;
    failures += !same;
    std::printf("name_trace EQUIVALENCE %s: %d calls, %zu/%zu log lines\n", same ? "PASS" : "FAIL",
                cases, log_old.size(), log_new.size());
  }

  // ---- timing (default config: empty map, empty filter) ----
  std::printf("\n%-34s %9s %9s %9s %11s %5s\n", "case (cpu ns/call)", "median", "min", "max",
              "wall median", "runs");
  const int calls = quick ? 200000 : 2000000;
  auto report = [&](const char* label, auto&& body) {
    std::vector<double> cpu, wall;
    for (int r = 0; r < runs; ++r) {
      const bench::Stopwatch watch;
      body();
      const bench::Measure m = watch.PerOp(calls);
      cpu.push_back(m.cpu);
      wall.push_back(m.wall);
    }
    std::printf("%-34s %9.2f %9.2f %9.2f %11.2f %5d\n", label, bench::Median(cpu), bench::Min(cpu),
                bench::Max(cpu), bench::Median(wall), runs);
  };
  std::vector<u8> arena(1u << 20, 0);
  SceneState s;
  for (int pass = 0; pass < 2; ++pass) {  // two interleaved passes
    report("scene instance hook, old", [&] {
      for (int i = 0; i < calls; ++i) SceneOld(s, 0x1000u + u32(i & 1023) * 32u, arena.data());
    });
    report("scene instance hook, new", [&] {
      for (int i = 0; i < calls; ++i) SceneNew(s, 0x1000u + u32(i & 1023) * 32u, arena.data());
    });
    Ctx ctx{0x100};
    report("path hash hook (filter off), old", [&] {
      for (int i = 0; i < calls; ++i) NameOld(ctx, arena.data());
    });
    report("path hash hook (filter off), new", [&] {
      for (int i = 0; i < calls; ++i) NameNew(ctx, arena.data());
    });
    report("guest stub only (floor)", [&] {
      for (int i = 0; i < calls; ++i) ImpHash(ctx, arena.data());
    });
    std::printf("(sink %llu)\n", (unsigned long long)ctx.r3);
  }
  std::printf("\nRESULT %s\n", failures ? "FAIL" : "PASS");
  return failures ? 1 : 0;
}
