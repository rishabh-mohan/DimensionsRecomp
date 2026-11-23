// B3: VirtualFileSystem::OpenFile host cost for a cached HostPathEntry child.
//   OLD = pristine: std::filesystem::exists(host_path() / name) before every
//         open, then HostPathEntry::Open -> CreateFileW (SDK flags) [+ close].
//         Miss: exists() == false -> NO_SUCH_FILE, no CreateFileW.
//   NEW = section C (cvar vfs_defer_open_exists_check on, read-only kOpen):
//         CreateFileW only; exists() only after a failed open.
// 1000 x 4 KB files in build/agent12/bench-data/open (deleted afterwards).
//
// Usage: b3_open.exe [runs=5] [files=1000] [passes=3]
#include "xfile_replica.h"

#include <cstdlib>
#include <filesystem>

using namespace b12;
namespace fs = std::filesystem;

namespace {

enum Variant { kOldHit, kNewHit, kOldMiss, kNewMiss, kNumVariants };
const char* kVariantNames[kNumVariants] = {"hit: exists + CreateFileW (OLD)",
                                           "hit: CreateFileW only (NEW)",
                                           "miss: exists only (OLD)",
                                           "miss: CreateFileW fails + exists (NEW)"};

// One OpenFile's host work; returns true if the file was opened.
bool open_one(int v, const fs::path& dir, const std::wstring& name, const std::wstring& full) {
  if (v == kOldHit || v == kOldMiss) {
    const fs::path file_path = dir / fs::path(name);
    if (!fs::exists(file_path)) return false;  // entry->Delete(); NO_SUCH_FILE
    auto f = HostFile::OpenExisting(full, FileAccess::kGenericRead);
    return f != nullptr;
  }
  auto f = HostFile::OpenExisting(full, FileAccess::kGenericRead);
  if (f) return true;
  const fs::path file_path = dir / fs::path(name);
  if (!fs::exists(file_path)) return false;  // NO_SUCH_FILE
  return false;
}

}  // namespace

int main(int argc, char** argv) {
  const int runs = argc > 1 ? std::atoi(argv[1]) : 5;
  const int nfiles = argc > 2 ? std::atoi(argv[2]) : 1000;
  const int passes = argc > 3 ? std::atoi(argv[3]) : 3;
  setvbuf(stdout, nullptr, _IONBF, 0);
  print_machine_header("B3 open: exists + CreateFileW vs CreateFileW");

  const fs::path dir = fs::path(data_dir()) / L"open";
  fs::create_directories(dir);
  std::vector<std::wstring> names, fulls, miss_names, miss_fulls;
  for (int i = 0; i < nfiles; ++i) {
    wchar_t b[32];
    swprintf(b, 32, L"f%04d.bin", i);
    names.push_back(b);
    fulls.push_back((dir / b).wstring());
    if (!ensure_xorshift_file(fulls.back(), 4096, 0xF11E0000ull + i)) {
      std::printf("FAIL: cannot create %s\n", narrow(fulls.back()).c_str());
      return 2;
    }
    swprintf(b, 32, L"m%04d.bin", i);
    miss_names.push_back(b);
    miss_fulls.push_back((dir / b).wstring());
  }

  std::printf("| variant | us/open median | min | max | opened | load median [min-max] |\n");
  std::printf("|---|---:|---:|---:|---:|---|\n");
  std::vector<double> us[kNumVariants], ld[kNumVariants];
  int opened[kNumVariants] = {};
  for (int r = -1; r < runs; ++r) {  // r = -1: warm-up
    for (int v = 0; v < kNumVariants; ++v) {
      const bool miss = (v == kOldMiss || v == kNewMiss);
      if (r >= 0) ld[v].push_back(100.0 * sample_machine_load(30));
      int ok = 0;
      const double t0 = qpc_seconds();
      for (int p = 0; p < passes; ++p)
        for (int i = 0; i < nfiles; ++i)
          ok += open_one(v, dir, miss ? miss_names[i] : names[i], miss ? miss_fulls[i] : fulls[i]);
      const double dt = qpc_seconds() - t0;
      if (r >= 0) {
        us[v].push_back(dt * 1e6 / double(passes * nfiles));
        opened[v] = ok / passes;
      }
    }
  }
  for (int v = 0; v < kNumVariants; ++v) {
    const Summary s = summarize(us[v]), l = summarize(ld[v]);
    std::printf("| %s | %.2f | %.2f | %.2f | %d/%d | %.0f%% [%.0f-%.0f] |\n", kVariantNames[v],
                s.median, s.min, s.max, opened[v], nfiles, l.median, l.min, l.max);
  }
  std::error_code ec;
  fs::remove_all(dir, ec);
  std::printf("\n(n=%d runs x %d passes x %d files per row after a warm-up; files deleted: %s)\n",
              runs, passes, nfiles, ec ? "NO" : "yes");
  return 0;
}
