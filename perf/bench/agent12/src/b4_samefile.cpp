// B4: same-file reads from 1 vs 2 threads through XFile::Read.
//   OLD = pristine: file_lock_ held across ReadSync/ReadFile.
//   NEW = section B fast path: shared unlocked_read_lock_ around ReadData,
//         file_lock_ only for CompleteRead (cvar io_unlocked_file_reads on).
//   OPT = NEW over a FILE_FLAG_OVERLAPPED handle + per-thread event (the
//         rejected option; the SDK's Win32FileHandle is synchronous).
// All threads share one XFileReplica / one host handle (one guest file
// handle read by several guest threads), each thread reading random aligned
// blocks of build/agent12/bench-data/scatter.bin into its own guest buffer.
//
// Usage: b4_samefile.exe [runs=5] [mb_per_thread=128]
#include "xfile_replica.h"

#include <atomic>
#include <cinttypes>
#include <cstdlib>
#include <thread>

using namespace b12;

namespace {

constexpr uint32_t kMB = 1u << 20;
constexpr uint32_t HV_BASE = 0x01000000, HV_SIZE = 0x01000000;  // 4 MB per thread

Layout bench_layout() {
  Layout l;
  l.heaps = {{HeapType::kGuestVirtual, HV_BASE, HV_SIZE, 0x1000}};
  l.virtual_commit = HV_BASE + HV_SIZE;
  l.physical_commit = 0x10000;
  return l;
}

enum Variant { kOld, kNew, kOpt, kNumVariants };
const char* kVariantNames[kNumVariants] = {"OLD (locked ReadFile)", "NEW (unlocked ReadFile)",
                                           "OPT (NEW + overlapped handle)"};

struct RunResult {
  double seconds = 0;
  uint64_t bytes = 0;
  bool ok = true;
};

RunResult run_once(XFileReplica& x, int v, int nthreads, uint32_t block, uint64_t bytes_per_thread,
                   uint64_t file_size, uint64_t seed) {
  x.knobs = XFileKnobs{};
  x.knobs.io_unlocked_file_reads = (v != kOld);
  std::atomic<int> ready{0};
  std::atomic<bool> go{false};
  std::vector<double> end(nthreads);
  std::vector<uint64_t> got(nthreads);
  std::vector<int> okv(nthreads, 1);
  double start = 0;
  std::vector<std::thread> th;
  for (int t = 0; t < nthreads; ++t) {
    th.emplace_back([&, t] {
      uint64_t s = seed * 0x9E3779B97F4A7C15ull + uint64_t(t) * 0x1234567ull + 1;
      const uint32_t buf = HV_BASE + uint32_t(t) * 4 * kMB;
      const uint64_t nblocks = file_size / block - 1;
      const uint64_t reads = bytes_per_thread / block;
      ready.fetch_add(1);
      while (!go.load(std::memory_order_acquire)) {
      }
      uint64_t total = 0;
      for (uint64_t i = 0; i < reads; ++i) {
        const uint64_t off = (1 + xorshift64(s) % nblocks) * block;
        const uint32_t dst = buf + uint32_t((xorshift64(s) % ((4 * kMB) / block)) * block);
        uint32_t out = 0;
        X_STATUS st = v == kOld ? x.ReadOld(dst, block, off, &out, 0, true)
                                : x.ReadNew(dst, block, off, &out, 0, true);
        if (st != X_STATUS_SUCCESS || out != block) okv[t] = 0;
        total += out;
      }
      end[t] = qpc_seconds();
      got[t] = total;
    });
  }
  while (ready.load() != nthreads) {
  }
  start = qpc_seconds();
  go.store(true, std::memory_order_release);
  for (auto& t : th) t.join();
  RunResult r;
  r.seconds = *std::max_element(end.begin(), end.end()) - start;
  for (int t = 0; t < nthreads; ++t) {
    r.bytes += got[t];
    r.ok &= okv[t] != 0;
  }
  return r;
}

}  // namespace

int main(int argc, char** argv) {
  const int runs = argc > 1 ? std::atoi(argv[1]) : 5;
  const uint64_t mb_per_thread = argc > 2 ? std::strtoull(argv[2], nullptr, 0) : 128;
  setvbuf(stdout, nullptr, _IONBF, 0);
  print_machine_header("B4 same-file reads, 1 vs 2 threads");

  const std::wstring path = data_dir() + L"\\scatter.bin";
  if (!ensure_xorshift_file(path, 256ull * kMB, 0x5CA77E2B1ull)) {
    std::printf("FAIL: cannot create scatter.bin\n");
    return 2;
  }
  const uint64_t fsize = file_size_of(path);
  MockMemory mem(bench_layout());
  auto fsync = HostFile::OpenExisting(path, FileAccess::kGenericRead);
  auto fovl = HostFile::OpenExisting(path, FileAccess::kGenericRead, false, true);
  if (!fsync || !fovl) {
    std::printf("FAIL: cannot open scatter.bin\n");
    return 2;
  }
  XFileReplica xs(&mem, fsync.get(), "scatter.bin");
  XFileReplica xo(&mem, fovl.get(), "scatter.bin");

  struct Cfg {
    uint32_t block;
    uint64_t bytes_per_thread;
  };
  const Cfg cfgs[] = {{64 * 1024, mb_per_thread * kMB}, {4096, (mb_per_thread / 4) * kMB}};

  std::printf("| block | threads | variant | MB/s median | min | max | load median [min-max] | ok |\n");
  std::printf("|---:|---:|---|---:|---:|---:|---|---|\n");
  for (const Cfg& c : cfgs) {
    // warm-up (also pulls the file into the cache)
    for (int v = 0; v < kNumVariants; ++v)
      for (int nt : {1, 2}) run_once(v == kOpt ? xo : xs, v, nt, c.block, c.bytes_per_thread, fsize, 7);
    std::vector<double> mbps[kNumVariants][2], load[kNumVariants][2];
    bool ok[kNumVariants][2] = {};
    for (auto& row : ok) row[0] = row[1] = true;
    for (int r = 0; r < runs; ++r) {
      for (int v = 0; v < kNumVariants; ++v) {
        for (int nt : {1, 2}) {
          load[v][nt - 1].push_back(100.0 * sample_machine_load(30));
          RunResult rr = run_once(v == kOpt ? xo : xs, v, nt, c.block, c.bytes_per_thread, fsize,
                                  uint64_t(r) * 31 + nt);
          mbps[v][nt - 1].push_back(double(rr.bytes) / kMB / rr.seconds);
          ok[v][nt - 1] &= rr.ok;
        }
      }
    }
    for (int v = 0; v < kNumVariants; ++v) {
      for (int nt : {1, 2}) {
        const Summary s = summarize(mbps[v][nt - 1]);
        const Summary l = summarize(load[v][nt - 1]);
        std::printf("| %u KB | %d | %s | %.0f | %.0f | %.0f | %.0f%% [%.0f-%.0f] | %s |\n",
                    c.block / 1024, nt, kVariantNames[v], s.median, s.min, s.max, l.median, l.min,
                    l.max, ok[v][nt - 1] ? "yes" : "NO");
      }
    }
  }
  std::printf("\n(n=%d timed runs per row after a warm-up; 64 KB rows read %" PRIu64
              " MB per thread per run, 4 KB rows %" PRIu64 " MB)\n",
              runs, mb_per_thread, mb_per_thread / 4);
  return 0;
}
