// B1: XFile::ReadScatter throughput, OLD (pristine, one ReadFile + one
// TriggerCallbacks per 4 KB segment) vs NEW (section B coalescing, section A
// lockless watch pre-check), on mock guest memory with real Win32 reads.
//
// Usage: b1_scatter.exe [mb=256] [runs=5] [files=all|synthetic|game]
//   synthetic = build/agent12/bench-data/scatter.bin (256 MB xorshift64, created once)
//   game      = game/disc/GAME.DAT, first `mb` MB, read-only; only timings and
//               pass/fail are printed for it.
// Each call reads 1 MB (256 segments) at file offset i MB, i = 1..mb-1.
#include "xfile_replica.h"

#include <cinttypes>
#include <cstdlib>

using namespace b12;

namespace {

constexpr uint32_t kPage = 4096, kMB = 1u << 20;
constexpr uint32_t HV_BASE = 0x01000000, HV_SIZE = 0x01000000;  // virtual, 4 KB pages
constexpr uint32_t HP_BASE = 0x02000000, HP_SIZE = 0x01000000;  // physical, 0xE0-like
constexpr uint32_t HS_BASE = 0x03000000, HS_SIZE = 0x00100000;  // segment arrays
constexpr int kArrays = 16;
constexpr uint32_t kSegsPerCall = 256;

Layout bench_layout() {
  Layout l;
  l.heaps = {{HeapType::kGuestVirtual, HV_BASE, HV_SIZE, 0x1000},
             {HeapType::kGuestPhysical, HP_BASE, HP_SIZE, 0x1000, true, 0},
             {HeapType::kGuestVirtual, HS_BASE, HS_SIZE, 0x1000}};
  l.virtual_commit = HS_BASE + HS_SIZE;
  l.physical_commit = HP_SIZE + 0x2000;
  return l;
}

enum Pattern { kContig, kRuns64K, kStride2, kNumPatterns };
const char* kPatternNames[kNumPatterns] = {"contiguous 1MB", "16x64KB runs", "stride-2 pages"};

enum Variant { kVirtOld, kVirtNew, kPhysOld, kPhysOldA, kPhysNew, kPhysNewA, kNumVariants };
const char* kVariantNames[kNumVariants] = {"virt OLD",     "virt NEW (B)",    "phys OLD",
                                           "phys OLD+A",   "phys NEW (B, -A)", "phys NEW (A+B)"};
bool variant_phys(int v) { return v >= kPhysOld; }
bool variant_new(int v) { return v == kVirtNew || v == kPhysNew || v == kPhysNewA; }

void set_knobs(XFileReplica& x, int v) {
  x.knobs = XFileKnobs{};
  x.knobs.old_with_precheck = (v == kPhysOldA);
  x.knobs.io_lockless_watch_check = (v != kPhysNew);
  x.knobs.io_coalesce_scatter_reads = true;
  x.knobs.io_unlocked_file_reads = true;
}

uint32_t seg_array_addr(int pattern, int phys, int k) {
  return HS_BASE + uint32_t(((pattern * 2 + phys) * kArrays + k) * kSegsPerCall * 4);
}

std::vector<uint32_t> segs_of(MockMemory& m, uint32_t arr) {
  const uint32_t* a = reinterpret_cast<const uint32_t*>(m.TranslateVirtual(arr));
  std::vector<uint32_t> v(kSegsPerCall);
  for (uint32_t s = 0; s < kSegsPerCall; ++s) v[s] = _byteswap_ulong(a[s]);
  return v;
}

void build_arrays(MockMemory& m) {
  uint64_t rs = 0xB1B1B1B1ull;
  for (int p = 0; p < kNumPatterns; ++p) {
    for (int ph = 0; ph < 2; ++ph) {
      const uint32_t base = ph ? HP_BASE : HV_BASE;
      for (int k = 0; k < kArrays; ++k) {
        uint32_t* a = reinterpret_cast<uint32_t*>(m.TranslateVirtual(seg_array_addr(p, ph, k)));
        std::vector<uint32_t> segs(kSegsPerCall);
        if (p == kContig) {
          const uint32_t b = base + uint32_t(k % 15) * kMB;
          for (uint32_t s = 0; s < kSegsPerCall; ++s) segs[s] = b + s * kPage;
        } else if (p == kStride2) {
          const uint32_t b = base + uint32_t(k % 7) * 2 * kMB;
          for (uint32_t s = 0; s < kSegsPerCall; ++s) segs[s] = b + 2 * s * kPage;
        } else {
          // 16 distinct, mutually non-adjacent 64 KB slots of the 16 MB window.
          std::vector<uint32_t> slots;
          while (slots.size() < 16) {
            const uint32_t sl = uint32_t(xorshift64(rs) % 256);
            bool bad = false;
            for (uint32_t o : slots) bad |= (o == sl || o + 1 == sl || sl + 1 == o);
            if (!bad) slots.push_back(sl);
          }
          for (uint32_t r = 0; r < 16; ++r)
            for (uint32_t j = 0; j < 16; ++j) segs[r * 16 + j] = base + slots[r] * 0x10000 + j * kPage;
        }
        for (uint32_t s = 0; s < kSegsPerCall; ++s) a[s] = _byteswap_ulong(segs[s]);
      }
    }
  }
}

uint8_t* host_of(MockMemory& m, uint32_t guest) {
  const BaseHeap* h = static_cast<const MockMemory&>(m).LookupHeap(guest);
  if (h->heap_type() == HeapType::kGuestPhysical)
    return m.TranslatePhysical(static_cast<const PhysicalHeap*>(h)->GetPhysicalAddress(guest));
  return m.TranslateVirtual(guest);
}

X_STATUS do_call(XFileReplica& x, int v, uint32_t arr, uint64_t off, uint32_t* out) {
  return variant_new(v) ? x.ReadScatterNew(arr, kMB, off, out, 0)
                        : x.ReadScatterOld(arr, kMB, off, out, 0);
}

struct PassResult {
  double seconds = 0;
  uint64_t bytes = 0;
  Counters cnt;
  uint32_t calls = 0;
  bool ok = true;
};

PassResult run_pass(XFileReplica& x, int pattern, int v, uint32_t ncalls) {
  set_knobs(x, v);
  PassResult r;
  tl_counters = {};
  const double t0 = qpc_seconds();
  for (uint32_t i = 1; i <= ncalls; ++i) {
    uint32_t out = 0;
    const X_STATUS st =
        do_call(x, v, seg_array_addr(pattern, variant_phys(v), int(i % kArrays)), uint64_t(i) * kMB, &out);
    r.ok &= (st == X_STATUS_SUCCESS && out == kMB);
    r.bytes += out;
  }
  r.seconds = qpc_seconds() - t0;
  r.cnt = tl_counters;
  r.calls = ncalls;
  return r;
}

// OLD and NEW leave identical guest bytes, status and out value (hashes are
// compared in memory only, never printed).
bool equality_check(MockMemory& m, XFileReplica& x, uint32_t ncalls, int* checked) {
  bool all = true;
  for (int p = 0; p < kNumPatterns; ++p) {
    for (int ph = 0; ph < 2; ++ph) {
      for (uint32_t i : {1u, ncalls / 3, ncalls / 2, ncalls}) {
        if (!i) continue;
        const uint32_t arr = seg_array_addr(p, ph, int(i % kArrays));
        const std::vector<uint32_t> segs = segs_of(m, arr);
        auto run = [&](int v, uint32_t* out) {
          for (uint32_t s : segs) std::memset(host_of(m, s), 0xCD, kPage);
          set_knobs(x, v);
          X_STATUS st = do_call(x, v, arr, uint64_t(i) * kMB, out);
          uint64_t h = 0xcbf29ce484222325ull;
          for (uint32_t s : segs) h = fnv1a64(host_of(m, s), kPage, h);
          return std::make_pair(st, h);
        };
        const int vo = ph ? kPhysOld : kVirtOld;
        uint32_t out_o = 0, out_n = 0, out_n2 = 0;
        auto ro = run(vo, &out_o);
        auto rn = run(ph ? kPhysNewA : kVirtNew, &out_n);
        bool eq = ro == rn && out_o == out_n && ro.first == X_STATUS_SUCCESS;
        if (ph) {
          auto rn2 = run(kPhysNew, &out_n2);
          eq &= (rn2 == ro && out_n2 == out_o);
        }
        all &= eq;
        ++*checked;
      }
    }
  }
  return all;
}

void fixup_like_sdk(const std::string& name, uint64_t, uint8_t*, size_t) {
  // The SDK's only registered fixup (PortalTrailer) returns early for any
  // file but PATCH.DAT; HasFileReadFixups() is therefore true for every read.
  if (name != "PATCH.DAT") return;
}

}  // namespace

int main(int argc, char** argv) {
  const uint32_t mb = argc > 1 ? uint32_t(std::strtoul(argv[1], nullptr, 0)) : 256;
  const int runs = argc > 2 ? std::atoi(argv[2]) : 5;
  const std::string which = argc > 3 ? argv[3] : "all";
  setvbuf(stdout, nullptr, _IONBF, 0);
  print_machine_header("B1 scatter OLD vs NEW");

  struct FileSpec {
    const char* label;
    std::wstring path;
    const char* xname;
  };
  std::vector<FileSpec> files;
  const std::wstring synth = data_dir() + L"\\scatter.bin";
  if (which == "all" || which == "synthetic") {
    if (!ensure_xorshift_file(synth, 256ull * kMB, 0x5CA77E2B1ull)) {
      std::printf("FAIL: cannot create scatter.bin\n");
      return 2;
    }
    files.push_back({"synthetic", synth, "scatter.bin"});
  }
  if (which == "all" || which == "game") {
    files.push_back({"GAME.DAT", workspace_root() + L"\\game\\disc\\GAME.DAT", "GAME.DAT"});
  }

  MockMemory mem(bench_layout());
  build_arrays(mem);
  RegisterFileReadFixup(fixup_like_sdk);

  std::printf("| file | pattern | variant | MB/s median | min | max | ReadFile/call | global-lock/call | heap-lock/call | load median [min-max] | ok |\n");
  std::printf("|---|---|---|---:|---:|---:|---:|---:|---:|---|---|\n");
  for (const FileSpec& fs : files) {
    auto file = HostFile::OpenExisting(fs.path, FileAccess::kGenericRead);
    if (!file) {
      std::printf("| %s | (cannot open) |\n", fs.label);
      continue;
    }
    const uint64_t fsize = file_size_of(fs.path);
    const uint32_t ncalls = uint32_t(std::min<uint64_t>(mb, fsize / kMB)) - 1;
    XFileReplica x(&mem, file.get(), fs.xname);

    int checked = 0;
    const bool eq = equality_check(mem, x, ncalls, &checked);
    std::fprintf(stderr, "[B1] %s: OLD/NEW equality %s (%d calls compared)\n", fs.label,
                 eq ? "PASS" : "FAIL", checked);

    // Warm-up: one untimed pass of everything (also warms the file cache).
    for (int p = 0; p < kNumPatterns; ++p)
      for (int v = 0; v < kNumVariants; ++v) run_pass(x, p, v, ncalls);

    std::vector<double> mbps[kNumPatterns][kNumVariants], load[kNumPatterns][kNumVariants];
    PassResult last[kNumPatterns][kNumVariants];
    bool ok[kNumPatterns][kNumVariants];
    for (auto& row : ok)
      for (bool& b : row) b = eq;
    for (int r = 0; r < runs; ++r) {
      for (int p = 0; p < kNumPatterns; ++p) {
        for (int v = 0; v < kNumVariants; ++v) {
          load[p][v].push_back(100.0 * sample_machine_load(30));
          PassResult pr = run_pass(x, p, v, ncalls);
          mbps[p][v].push_back(double(pr.bytes) / double(kMB) / pr.seconds);
          ok[p][v] &= pr.ok;
          last[p][v] = pr;
        }
      }
      std::fprintf(stderr, "[B1] %s: run %d/%d done\n", fs.label, r + 1, runs);
    }
    for (int p = 0; p < kNumPatterns; ++p) {
      for (int v = 0; v < kNumVariants; ++v) {
        const Summary s = summarize(mbps[p][v]);
        const Summary l = summarize(load[p][v]);
        const PassResult& pr = last[p][v];
        std::printf("| %s | %s | %s | %.0f | %.0f | %.0f | %.2f | %.2f | %.2f | %.0f%% [%.0f-%.0f] | %s |\n",
                    fs.label, kPatternNames[p], kVariantNames[v], s.median, s.min, s.max,
                    double(pr.cnt.readfile_calls) / pr.calls, double(pr.cnt.global_lock) / pr.calls,
                    double(pr.cnt.heap_lock) / pr.calls, l.median, l.min, l.max,
                    ok[p][v] ? "yes" : "NO");
      }
    }
  }
  std::printf("\n(n=%d timed runs per row after one warm-up pass; %u calls x 1 MB per run)\n", runs,
              mb - 1);
  return 0;
}
