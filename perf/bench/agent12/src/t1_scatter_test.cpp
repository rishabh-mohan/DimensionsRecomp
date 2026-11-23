// T1: differential test of XFile::ReadScatter (and XFile::Read), OLD
// (pristine HEAD) vs NEW (working tree, sections A + B), on mock guest memory
// with real Win32 reads of synthetic files in build/agent12/bench-data/t1.
//
// Usage: t1_scatter_test.exe [cases=6000] [seed=0x7E57AB1E]
// Exit code 0 = PASS, 1 = FAIL.
#include "xfile_replica.h"

#include <cinttypes>
#include <cstdlib>

using namespace b12;

namespace {

constexpr uint32_t kPage = 4096;
// Guest layout. H0/H1 and H2/H3 are adjacent so runs can cross heaps.
constexpr uint32_t H0_BASE = 0x000000, H0_SIZE = 0x100000;  // virtual, 4 KB pages
constexpr uint32_t H1_BASE = 0x100000, H1_SIZE = 0x100000;  // virtual, 64 KB pages
constexpr uint32_t GAP_BASE = 0x200000;                      // 0x200000-0x23FFFF: no heap
constexpr uint32_t H2_BASE = 0x240000, H2_SIZE = 0x100000;  // physical, 64 KB pages, hao 0
constexpr uint32_t H3_BASE = 0x340000, H3_SIZE = 0x100000;  // physical, 4 KB pages, hao 0x1000
constexpr uint32_t GAP2_BASE = 0x440000;                     // 0x440000-0x47FFFF: no heap
constexpr uint32_t H4_BASE = 0x480000, H4_SIZE = 0x40000;   // virtual, segment arrays only
constexpr uint32_t VIRT_COMMIT = 0x4C0000;                   // = end of H4
constexpr uint32_t PHYS_COMMIT = 0x210000;

Layout t1_layout() {
  Layout l;
  l.heaps = {
      {HeapType::kGuestVirtual, H0_BASE, H0_SIZE, 0x1000},
      {HeapType::kGuestVirtual, H1_BASE, H1_SIZE, 0x10000},
      {HeapType::kGuestPhysical, H2_BASE, H2_SIZE, 0x10000, false, 0x000000},
      {HeapType::kGuestPhysical, H3_BASE, H3_SIZE, 0x1000, true, 0x100000},
      {HeapType::kGuestVirtual, H4_BASE, H4_SIZE, 0x1000},
  };
  l.virtual_commit = VIRT_COMMIT;
  l.physical_commit = PHYS_COMMIT;
  return l;
}

struct HeapRange {
  uint32_t base, size;
};
constexpr HeapRange kDestHeaps[4] = {
    {H0_BASE, H0_SIZE}, {H1_BASE, H1_SIZE}, {H2_BASE, H2_SIZE}, {H3_BASE, H3_SIZE}};

struct Rng {
  uint64_t s;
  uint64_t next() { return xorshift64(s); }
  uint32_t below(uint64_t n) { return n ? uint32_t(next() % n) : 0; }
  bool chance(uint32_t pct) { return below(100) < pct; }
};

using Ranges = std::vector<std::pair<uint64_t, uint64_t>>;  // (start, length)

struct Recorder {
  Ranges fired;   // invalidation callbacks: physical (start, length)
  Ranges fixups;  // fixup calls: file (offset, length)
};
Recorder* g_rec = nullptr;

std::pair<uint32_t, uint32_t> invalidation_cb(void* ctx, uint32_t start, uint32_t length,
                                              bool /*exact*/) {
  static_cast<Recorder*>(ctx)->fired.push_back({start, length});
  return {start, length};
}

// Byte-local, non-idempotent fixup: XOR 0x5A at file offsets o % 1543 == 7.
// Applied twice or to stale bytes, it leaves a visible difference. Index
// based, so offsets near 2^64 (-2 reads) cannot run off the buffer.
void t1_fixup(const std::string& name, uint64_t offset, uint8_t* data, size_t length) {
  if (name != "T1.BIN") return;
  if (g_rec) g_rec->fixups.push_back({offset, length});
  for (uint64_t i = (7 + 1543 - offset % 1543) % 1543; i < length; i += 1543) data[i] ^= 0x5A;
}

// PortalTrailer-style 2-byte fixup at file offset kStraddle (crosses a 4 KB
// boundary for page-aligned reads). Used only by the informational sub-test.
constexpr uint64_t kStraddle = 16 * 4096 - 1;
void straddle_fixup(const std::string& name, uint64_t offset, uint8_t* data, size_t length) {
  if (name != "T1.BIN") return;
  if (offset <= kStraddle && kStraddle + 2 <= offset + length) {
    data[kStraddle - offset] = 0x20;
    data[kStraddle - offset + 1] = 0x20;
  }
}

enum Cls {
  kContig, kContigPhys, kRandom, kMixed, kCross, kEofInRun, kEofBoundary, kPastEof, kProtected,
  kNullSeg, kOddLength, kSpecial, kNearWrap, kUnaligned, kAddrWrap, kDenied, kTinyFile, kRead,
  kNumCls
};
const char* kClsNames[kNumCls] = {
    "contiguous-virt", "contiguous-phys", "random-pages", "mixed-runs", "cross-heap",
    "eof-in-run", "eof-at-boundary", "offset-past-eof", "protected-page", "null-heap-seg",
    "odd-length", "offset-0/-1/-2", "offset-near-wrap", "unaligned-segs", "addr-wrap",
    "access-denied", "tiny-file", "single-Read"};

struct Case {
  bool scatter = true;
  int cls = 0;
  int file = 0;
  uint64_t offset = 0;
  uint32_t length = 0;
  std::vector<uint32_t> segs;  // scatter entries; for Read, segs[0] = buffer
  uint64_t position = 0;
  FileKind kind = FileKind::kHostPath;
  bool deny = false;
  XFileKnobs knobs;
  std::vector<std::pair<uint32_t, uint32_t>> protects;  // (guest address, protect)
  int watch_density = 0;
  uint64_t watch_seed = 0;
  uint64_t poison_seed = 0;
};

uint32_t nseg_of(uint32_t length) { return length ? (length + kPage - 1) / kPage : 1; }
uint32_t seg_array_addr(const Case& c) { return VIRT_COMMIT - uint32_t(c.segs.size()) * 4; }

uint32_t page_in(Rng& r, int h, uint32_t pages) {
  uint32_t npages = kDestHeaps[h].size / kPage;
  if (pages > npages) pages = npages;
  return kDestHeaps[h].base + r.below(npages - pages + 1) * kPage;
}
uint32_t gap_page(Rng& r) {
  switch (r.below(4)) {
    case 0: return GAP_BASE + r.below(0x40) * kPage;
    case 1: return GAP2_BASE + r.below(0x40) * kPage;
    case 2: return 0xFFFFF000u;
    default: return 0x7F000000u + r.below(16) * kPage;
  }
}

void fill_contig(Case& c, uint32_t base) {
  for (size_t k = 0; k < c.segs.size(); ++k) c.segs[k] = base + uint32_t(k) * kPage;
}
void fill_mixed(Rng& r, Case& c) {
  size_t k = 0;
  uint32_t prev_end = 0;
  while (k < c.segs.size()) {
    uint32_t run = 1 + r.below(std::min<size_t>(8, c.segs.size() - k));
    uint32_t base;
    if (k && r.chance(20)) {
      base = prev_end;  // accidental continuation
    } else {
      base = page_in(r, int(r.below(4)), run);
    }
    for (uint32_t j = 0; j < run; ++j) c.segs[k + j] = base + j * kPage;
    prev_end = base + run * kPage;
    k += run;
  }
}
void add_protects(Rng& r, Case& c, uint32_t count) {
  static const uint32_t kProt[] = {kMemoryProtectRead, 0,
                                   kMemoryProtectRead | kMemoryProtectWriteCombine,
                                   kMemoryProtectRead | kMemoryProtectWrite | kMemoryProtectNoCache};
  for (uint32_t i = 0; i < count; ++i) {
    // Prefer pages the case actually touches.
    uint32_t addr;
    if (!c.segs.empty() && r.chance(80)) {
      addr = c.segs[r.below(c.segs.size())] + r.below(2) * kPage;
    } else {
      addr = page_in(r, 2 + int(r.below(2)), 1);
    }
    c.protects.push_back({addr, kProt[r.below(4)]});
  }
}

uint64_t gen_bits(Rng& r, int d) {
  switch (d) {
    case 0: return 0;
    case 1: return r.next() & r.next() & r.next() & r.next() & r.next();
    case 2: return r.next() & r.next();
    case 3: return ~0ull;
    default: return r.chance(30) ? (1ull << r.below(64)) : 0;
  }
}

Case gen_case(Rng& r, uint64_t idx, const std::vector<uint64_t>& sizes) {
  Case c;
  c.cls = int(idx % kNumCls);
  if (r.chance(50)) {
    c.knobs = XFileKnobs{};
  } else {
    uint32_t b = r.below(8);
    c.knobs.io_coalesce_scatter_reads = b & 1;
    c.knobs.io_unlocked_file_reads = (b >> 1) & 1;
    c.knobs.io_lockless_watch_check = (b >> 2) & 1;
  }
  uint32_t k = r.below(4);
  c.kind = k == 0 ? FileKind::kStfs : (k == 1 ? FileKind::kDiscImage : FileKind::kHostPath);
  c.file = r.chance(70) ? (r.chance(50) ? 0 : 4) : 1;
  uint64_t size = sizes[c.file];
  c.position = r.chance(30) ? 0 : r.below(size + 8192);
  c.watch_density = int(r.below(5));
  c.watch_seed = r.next();
  c.poison_seed = r.next();

  auto rand_len = [&]() -> uint32_t {
    switch (r.below(6)) {
      case 0: return (1 + r.below(48)) * kPage;
      case 1: return (1 + r.below(48)) * kPage + 1 + r.below(kPage - 1);
      case 2: return 1 + r.below(kPage);
      case 3: return kPage;
      case 4: return kPage + 1;
      default: return (2 + r.below(15)) * kPage;
    }
  };
  auto rand_off = [&]() -> uint64_t {
    uint64_t o = r.chance(60) ? uint64_t(r.below(size / kPage + 1)) * kPage : r.below(size + 1);
    return o ? o : kPage;
  };
  c.length = rand_len();
  c.offset = rand_off();
  auto make_segs = [&]() { c.segs.assign(nseg_of(c.length), 0); };
  make_segs();
  fill_mixed(r, c);

  switch (c.cls) {
    case kContig:
      fill_contig(c, page_in(r, int(r.below(2)), uint32_t(c.segs.size())));
      break;
    case kContigPhys:
      fill_contig(c, page_in(r, 2 + int(r.below(2)), uint32_t(c.segs.size())));
      if (c.watch_density == 0) c.watch_density = 1 + int(r.below(4));
      break;
    case kRandom:
      for (auto& s : c.segs) s = page_in(r, int(r.below(4)), 1);
      break;
    case kMixed:
      break;
    case kCross: {
      static const uint32_t kBounds[] = {H1_BASE, H3_BASE, GAP_BASE, H2_BASE, GAP2_BASE};
      if (c.length <= kPage) c.length = (2 + r.below(12)) * kPage + r.below(kPage);
      make_segs();
      uint32_t j = 1 + r.below(uint32_t(c.segs.size()) - 1);
      fill_contig(c, kBounds[r.below(5)] - j * kPage);
      break;
    }
    case kEofInRun: {
      if (c.length <= kPage) c.length = (2 + r.below(20)) * kPage + r.below(kPage);
      make_segs();
      fill_contig(c, page_in(r, int(r.below(4)), uint32_t(c.segs.size())));
      uint64_t span = std::min<uint64_t>(c.length, size);
      uint64_t back = 1 + r.below(span > 1 ? span - 1 : 1);
      c.offset = size > back ? size - back : 1;
      break;
    }
    case kEofBoundary: {
      if (c.length <= kPage) c.length = (2 + r.below(20)) * kPage + r.below(2) * r.below(kPage);
      make_segs();
      fill_contig(c, page_in(r, int(r.below(4)), uint32_t(c.segs.size())));
      uint64_t j = 1 + r.below(c.segs.size() - 1);
      c.offset = size > j * kPage ? size - j * kPage : 1;
      break;
    }
    case kPastEof:
      switch (r.below(3)) {
        case 0: c.offset = size ? size : 1; break;
        case 1: c.offset = size + 1 + r.below(3 * kPage); break;
        default: c.offset = 1ull << 40; break;
      }
      break;
    case kProtected:
      fill_contig(c, page_in(r, 2 + int(r.below(2)), uint32_t(c.segs.size())));
      add_protects(r, c, 1 + r.below(3));
      break;
    case kNullSeg: {
      if (r.chance(50)) fill_contig(c, page_in(r, int(r.below(4)), uint32_t(c.segs.size())));
      uint32_t n = 1 + r.below(2);
      for (uint32_t i = 0; i < n; ++i) c.segs[r.below(c.segs.size())] = gap_page(r);
      break;
    }
    case kOddLength:
      c.length = r.chance(30) ? 1 + r.below(kPage - 1)
                              : (1 + r.below(40)) * kPage + 1 + r.below(kPage - 1);
      make_segs();
      fill_mixed(r, c);
      break;
    case kSpecial: {
      static const uint64_t kSpecialOffsets[] = {0, uint64_t(-1), uint64_t(-2)};
      c.offset = kSpecialOffsets[r.below(3)];
      if (r.chance(50)) fill_contig(c, page_in(r, int(r.below(4)), uint32_t(c.segs.size())));
      break;
    }
    case kNearWrap: {
      // byte_offset < uint64_t(-2) - length takes the positional path.
      int64_t d = int64_t(r.below(5)) - 3;  // -3..+1
      c.offset = uint64_t(-2) - c.length + uint64_t(d);
      if (r.chance(20)) c.offset = (1ull << 63) + r.below(1000);
      fill_contig(c, page_in(r, int(r.below(4)), uint32_t(c.segs.size())));
      break;
    }
    case kUnaligned: {
      uint32_t delta = 1 + r.below(kPage - 1);
      if (r.chance(40)) {
        static const uint32_t kBounds[] = {H1_BASE, H3_BASE, GAP_BASE, H2_BASE, GAP2_BASE};
        uint32_t j = r.below(uint32_t(c.segs.size()));
        fill_contig(c, kBounds[r.below(5)] - (j + 1) * kPage + delta);
      } else {
        fill_contig(c, page_in(r, int(r.below(4)), uint32_t(c.segs.size()) + 1) + delta);
      }
      break;
    }
    case kAddrWrap: {
      uint32_t j = r.below(uint32_t(c.segs.size()));
      fill_contig(c, 0xFFFFF000u - j * kPage + (r.chance(30) ? r.below(kPage) : 0));
      if (r.chance(50)) c.segs[0] = page_in(r, 0, 1);
      break;
    }
    case kDenied:
      c.deny = true;
      break;
    case kTinyFile: {
      c.file = 2 + int(r.below(2));
      size = sizes[c.file];
      static const uint64_t kTinyOffsets[] = {0, 1, 2, 3, 4, uint64_t(-1), 4096};
      c.offset = kTinyOffsets[r.below(7)];
      c.position = r.below(6);
      break;
    }
    case kRead: {
      c.scatter = false;
      c.length = r.chance(10) ? 0 : r.below(3 * kPage + 1);
      uint32_t addr;
      if (r.chance(25)) {
        static const uint32_t kBounds[] = {H1_BASE, H3_BASE, GAP_BASE, H2_BASE, GAP2_BASE,
                                           0xFFFFF000u};
        addr = kBounds[r.below(6)] - r.below(2 * kPage);
      } else if (r.chance(10)) {
        addr = gap_page(r);
      } else {
        int h = int(r.below(4));
        addr = kDestHeaps[h].base + r.below(kDestHeaps[h].size);
      }
      c.segs.assign(1, addr);
      static const uint64_t kReadOffsets[] = {0, uint64_t(-1), uint64_t(-2)};
      switch (r.below(5)) {
        case 0: c.offset = kReadOffsets[r.below(3)]; break;
        case 1: c.offset = size > 100 ? size - r.below(100) : 1; break;
        case 2: c.offset = size + r.below(kPage); break;
        default: break;  // explicit offset from above
      }
      if (r.chance(20)) add_protects(r, c, 1 + r.below(2));
      break;
    }
  }
  // Some random protections everywhere, and some unaligned segments.
  if (c.cls != kProtected && c.cls != kRead && r.chance(10)) add_protects(r, c, 1 + r.below(2));
  return c;
}

uint8_t* host_page(MockMemory& m, uint32_t page) {
  const BaseHeap* h = static_cast<const MockMemory&>(m).LookupHeap(page);
  if (!h) return nullptr;
  if (h->heap_type() == HeapType::kGuestPhysical) {
    return m.TranslatePhysical(static_cast<const PhysicalHeap*>(h)->GetPhysicalAddress(page));
  }
  return m.TranslateVirtual(page);
}

std::vector<uint32_t> window_pages(const Case& c) {
  std::vector<uint32_t> pages;
  if (c.scatter) {
    for (uint32_t s : c.segs) {
      uint32_t p = s & ~(kPage - 1);
      pages.push_back(p);
      if (p != 0xFFFFF000u) pages.push_back(p + kPage);
    }
  } else if (c.length) {
    uint64_t first = c.segs[0] & ~uint64_t(kPage - 1);
    uint64_t last = std::min<uint64_t>(uint64_t(c.segs[0]) + c.length, 0xFFFFFFFFull);
    for (uint64_t p = first; p <= last; p += kPage) pages.push_back(uint32_t(p));
  }
  std::sort(pages.begin(), pages.end());
  pages.erase(std::unique(pages.begin(), pages.end()), pages.end());
  // H4 holds the segment arrays: never poison it.
  pages.erase(std::remove_if(pages.begin(), pages.end(),
                             [](uint32_t p) { return p >= H4_BASE && p < H4_BASE + H4_SIZE; }),
              pages.end());
  return pages;
}

uint8_t poison_byte(uint64_t seed, uint32_t page) {
  uint64_t x = seed ^ (uint64_t(page) * 0x9E3779B97F4A7C15ull);
  return uint8_t(xorshift64(x) >> 56) | 1;
}

void setup_memory(MockMemory& m, const Case& c, const std::vector<uint32_t>& pages) {
  for (int h : {2, 3}) m.physical_heap(h)->ResetGuestProtect();
  for (auto [addr, prot] : c.protects) {
    BaseHeap* h = m.LookupHeap(addr);
    if (h) h->SetGuestProtect(addr, 1, prot);
  }
  Rng wr{c.watch_seed | 1};
  for (int h : {2, 3}) {
    for (auto& b : m.physical_heap(h)->flags()) {
      b.notify_on_invalidation = gen_bits(wr, c.watch_density);
      b.provide_data = 0;
    }
  }
  if (c.scatter) {
    uint32_t* p = reinterpret_cast<uint32_t*>(m.TranslateVirtual(seg_array_addr(c)));
    for (size_t k = 0; k < c.segs.size(); ++k) p[k] = _byteswap_ulong(c.segs[k]);
  }
  for (uint32_t pg : pages) {
    if (uint8_t* hp = host_page(m, pg)) std::memset(hp, poison_byte(c.poison_seed, pg), kPage);
  }
}

struct RunOut {
  X_STATUS status;
  uint32_t out;
  uint64_t position;
  IONotification notif;
  Counters cnt;
  ScatterPath path;
};

RunOut run_one(MockMemory& /*m*/, XFileReplica& x, const Case& c, bool is_new, Recorder& rec) {
  rec.fired.clear();
  rec.fixups.clear();
  g_rec = &rec;
  x.position_ = c.position;
  x.last_notification = {};
  x.last_path = ScatterPath::kNone;
  x.knobs = is_new ? c.knobs : XFileKnobs{};
  uint32_t out = 0xDEADBEEF;
  const uint32_t apc = 0xA5C00000u ^ uint32_t(c.poison_seed);
  tl_counters = {};
  X_STATUS st;
  if (c.scatter) {
    st = is_new ? x.ReadScatterNew(seg_array_addr(c), c.length, c.offset, &out, apc)
                : x.ReadScatterOld(seg_array_addr(c), c.length, c.offset, &out, apc);
  } else {
    st = is_new ? x.ReadNew(c.segs[0], c.length, c.offset, &out, apc, true)
                : x.ReadOld(c.segs[0], c.length, c.offset, &out, apc, true);
  }
  RunOut r{st, out, x.position_, x.last_notification, tl_counters, x.last_path};
  g_rec = nullptr;
  return r;
}

Ranges merged(Ranges v) {
  Ranges iv;  // (start, end)
  for (auto [s, l] : v)
    if (l) iv.push_back({s, s + l});
  std::sort(iv.begin(), iv.end());
  Ranges out;
  for (auto [s, e] : iv) {
    if (!out.empty() && s <= out.back().second) {
      out.back().second = std::max(out.back().second, e);
    } else {
      out.push_back({s, e});
    }
  }
  return out;
}
// Every byte of union(a) is in union(b).
bool covered(const Ranges& a, const Ranges& b) {
  Ranges mb = merged(b);
  for (auto [s, l] : a) {
    if (!l) continue;
    uint64_t e = s + l;
    auto it = std::upper_bound(mb.begin(), mb.end(), std::make_pair(s, UINT64_MAX));
    if (it == mb.begin()) return false;
    --it;
    if (!(it->first <= s && e <= it->second)) return false;
  }
  return true;
}

struct ClsStats {
  uint64_t cases = 0, fails = 0, ok_status = 0, bytes = 0, positional = 0, rf_old = 0, rf_new = 0;
};

const char* path_name(ScatterPath p) {
  return p == ScatterPath::kOld ? "old" : p == ScatterPath::kPositional ? "positional" : "-";
}

// Crash reporting: which case / side was running when a fault happened.
const Case* g_cur_case = nullptr;
uint64_t g_cur_idx = 0;
const char* g_cur_side = "setup";
LONG WINAPI crash_filter(EXCEPTION_POINTERS* ep) {
  const EXCEPTION_RECORD* er = ep->ExceptionRecord;
  std::printf("\nCRASH 0x%08lX at %p (access %s 0x%p) in case %" PRIu64 " side=%s\n",
              er->ExceptionCode, er->ExceptionAddress,
              er->NumberParameters > 1 ? (er->ExceptionInformation[0] ? "write" : "read") : "?",
              er->NumberParameters > 1 ? (void*)er->ExceptionInformation[1] : nullptr, g_cur_idx,
              g_cur_side);
  if (const Case* c = g_cur_case) {
    std::printf("  cls=%s scatter=%d file=%d off=0x%" PRIX64 " len=0x%X pos=0x%" PRIX64
                " kind=%d deny=%d knobs=%d%d%d nseg=%zu\n  segs:",
                kClsNames[c->cls], int(c->scatter), c->file, c->offset, c->length, c->position,
                int(c->kind), int(c->deny), int(c->knobs.io_coalesce_scatter_reads),
                int(c->knobs.io_unlocked_file_reads), int(c->knobs.io_lockless_watch_check),
                c->segs.size());
    for (size_t k = 0; k < c->segs.size() && k < 64; ++k) std::printf(" %08X", c->segs[k]);
    std::printf("\n  protects:");
    for (auto [a, p] : c->protects) std::printf(" %08X:%X", a, p);
    std::printf("\n");
  }
  std::fflush(stdout);
  return EXCEPTION_EXECUTE_HANDLER;
}

}  // namespace

int main(int argc, char** argv) {
  uint64_t ncases = argc > 1 ? std::strtoull(argv[1], nullptr, 0) : 6000;
  uint64_t seed = argc > 2 ? std::strtoull(argv[2], nullptr, 0) : 0x7E57AB1Eull;
  setvbuf(stdout, nullptr, _IONBF, 0);
  SetUnhandledExceptionFilter(crash_filter);

  std::wstring dir = data_dir() + L"\\t1";
  CreateDirectoryW(dir.c_str(), nullptr);
  const std::vector<uint64_t> sizes = {1048576 + 1234, 262144, 3, 0, 3145728};
  std::vector<std::unique_ptr<HostFile>> fa, fb;
  for (size_t i = 0; i < sizes.size(); ++i) {
    std::wstring p = dir + L"\\f" + std::to_wstring(i) + L".bin";
    if (!ensure_xorshift_file(p, sizes[i], 0x1111ull * (i + 1))) {
      std::printf("FAIL: cannot create %s\n", narrow(p).c_str());
      return 2;
    }
    fa.push_back(HostFile::OpenExisting(p, FileAccess::kGenericRead));
    fb.push_back(HostFile::OpenExisting(p, FileAccess::kGenericRead));
    if (!fa.back() || !fb.back()) {
      std::printf("FAIL: cannot open %s\n", narrow(p).c_str());
      return 2;
    }
  }

  // Win32 semantics the replicas rely on (synchronous handle, OVERLAPPED
  // offset): reading at/after EOF fails with ERROR_HANDLE_EOF, a read across
  // EOF is short.
  {
    std::vector<uint8_t> buf(8192);
    size_t br = 0;
    HostFile& f = *fa[0];
    X_STATUS s1 = f.ReadSync({buf.data(), 4096}, sizes[0], &br);
    DWORD e1 = f.last_error_;
    size_t br1 = br;
    X_STATUS s2 = f.ReadSync({buf.data(), 4096}, sizes[0] - 10, &br);
    size_t br2 = br;
    X_STATUS s3 = f.ReadSync({buf.data(), 4096}, 1ull << 40, &br);
    DWORD e3 = f.last_error_;
    X_STATUS s4 = f.ReadSync({buf.data(), 4096}, size_t(-2), &br);
    DWORD e4 = f.last_error_;
    X_STATUS s5 = fa[3]->ReadSync({buf.data(), 4096}, 0, &br);
    DWORD e5 = fa[3]->last_error_;
    std::printf("win32: read@EOF -> status 0x%08X err %lu bytes %zu | read@EOF-10 -> 0x%08X bytes %zu |"
                " read@2^40 -> 0x%08X err %lu | read@-2 -> 0x%08X err %lu | empty file@0 -> 0x%08X err %lu\n",
                s1, e1, br1, s2, br2, s3, e3, s4, e4, s5, e5);
    bool ok = s1 == X_STATUS_END_OF_FILE && e1 == ERROR_HANDLE_EOF && s2 == X_STATUS_SUCCESS &&
              br2 == 10 && s3 == X_STATUS_END_OF_FILE;
    std::printf("win32 EOF semantics as assumed: %s\n", ok ? "yes" : "NO");
    // Offset -2 = FILE_USE_FILE_POINTER_POSITION: the read happens at the
    // handle's current file pointer (both OLD and NEW pass -2 through).
    std::vector<uint8_t> ref(16), got(16);
    f.ReadSync({ref.data(), 16}, 100, &br);
    LARGE_INTEGER fp;
    fp.QuadPart = 100;
    SetFilePointerEx(f.handle(), fp, nullptr, FILE_BEGIN);
    X_STATUS s6 = f.ReadSync({got.data(), 16}, size_t(-2), &br);
    std::printf("win32 read@-2 after SetFilePointerEx(100): status 0x%08X bytes %zu, same bytes as "
                "read@100: %s\n",
                s6, br, (s6 == 0 && br == 16 && ref == got) ? "yes" : "no");
  }

  MockMemory A(t1_layout()), B(t1_layout());
  Recorder recA, recB;
  std::pair<PhysicalMemoryInvalidationCallback, void*> cbA{invalidation_cb, &recA},
      cbB{invalidation_cb, &recB};
  A.physical_memory_invalidation_callbacks_.push_back(&cbA);
  B.physical_memory_invalidation_callbacks_.push_back(&cbB);
  RegisterFileReadFixup(t1_fixup);

  std::vector<std::unique_ptr<XFileReplica>> ra, rb;
  for (size_t i = 0; i < sizes.size(); ++i) {
    ra.push_back(std::make_unique<XFileReplica>(&A, fa[i].get(), "T1.BIN"));
    rb.push_back(std::make_unique<XFileReplica>(&B, fb[i].get(), "T1.BIN"));
  }

  ClsStats st[kNumCls];
  uint64_t fails = 0, extra_bits = 0, fired_a = 0, fired_b = 0, fix_a = 0, fix_b = 0;
  uint64_t rf_a = 0, rf_b = 0, gl_a = 0, gl_b = 0, pre_b = 0, full_compares = 0;
  uint64_t redo_cases = 0;
  Rng rng{seed};
  double t0 = qpc_seconds();

  for (uint64_t idx = 0; idx < ncases; ++idx) {
    Case c = gen_case(rng, idx, sizes);
    for (auto* f : {fa[c.file].get(), fb[c.file].get()}) {
      f->kind = c.kind;
      f->set_file_access_for_test(c.deny ? FileAccess::kGenericExecute : FileAccess::kGenericRead);
      // Offset -2 reaches ReadFile and NT reads at the handle's file pointer
      // (FILE_USE_FILE_POINTER_POSITION); give both handles the same one.
      LARGE_INTEGER fp;
      fp.QuadPart = LONGLONG(c.position & 0xFFFFFFFFull);
      SetFilePointerEx(f->handle(), fp, nullptr, FILE_BEGIN);
    }
    XFileReplica& xa = *ra[c.file];
    XFileReplica& xb = *rb[c.file];
    xa.RefreshUnlockedReadsOk();
    xb.RefreshUnlockedReadsOk();
    g_cur_case = &c;
    g_cur_idx = idx;
    g_cur_side = "setup";
    std::vector<uint32_t> pages = window_pages(c);
    setup_memory(A, c, pages);
    setup_memory(B, c, pages);

    g_cur_side = "OLD";
    RunOut oa = run_one(A, xa, c, false, recA);
    g_cur_side = "NEW";
    RunOut ob = run_one(B, xb, c, true, recB);
    g_cur_side = "compare";

    std::string why;
    auto fail = [&](const std::string& s) {
      if (why.empty()) why = s;
    };
    if (oa.status != ob.status) fail("status");
    if (oa.out != ob.out) fail("out_bytes");
    if (oa.position != ob.position) fail("position_");
    if (oa.notif.num_bytes != ob.notif.num_bytes || oa.notif.status != ob.notif.status ||
        oa.notif.apc_context != ob.notif.apc_context)
      fail("notification");
    if (oa.cnt.notify_calls != 1 || ob.cnt.notify_calls != 1 || oa.cnt.event_sets != 1 ||
        ob.cnt.event_sets != 1)
      fail("notify/Set count");
    for (uint32_t pg : pages) {
      uint8_t* pa = host_page(A, pg);
      uint8_t* pb = host_page(B, pg);
      if (pa && std::memcmp(pa, pb, kPage) != 0) {
        char b[64];
        std::snprintf(b, sizeof(b), "guest bytes @page 0x%08X", pg);
        fail(b);
        break;
      }
    }
    for (int h : {2, 3}) {
      auto& fa_ = A.physical_heap(h)->flags();
      auto& fb_ = B.physical_heap(h)->flags();
      for (size_t i = 0; i < fa_.size(); ++i) {
        uint64_t ba = fa_[i].notify_on_invalidation, bb = fb_[i].notify_on_invalidation;
        if (bb & ~ba) fail("NEW kept a watch bit OLD cleared");
        extra_bits += std::popcount(ba & ~bb);
      }
    }
    if (!covered(recA.fired, recB.fired)) fail("invalidated range not covered by NEW");
    if (!covered(recA.fixups, recB.fixups)) fail("fixup range not covered by NEW");
    if (c.scatter) {
      bool positional_offset = c.offset && c.offset < uint64_t(-2) - c.length;
      bool unlocked_ok = AllowsUnlockedReads(fb[c.file].get());
      bool expect_positional =
          positional_offset &&
          (c.knobs.io_coalesce_scatter_reads || (unlocked_ok && c.knobs.io_unlocked_file_reads));
      if (expect_positional != (ob.path == ScatterPath::kPositional)) fail("dispatch path");
      if (!expect_positional && ob.cnt.readfile_calls != oa.cnt.readfile_calls)
        fail("old path ReadFile count");
      if (expect_positional && !c.knobs.io_coalesce_scatter_reads &&
          ob.cnt.readfile_calls != oa.cnt.readfile_calls)
        fail("uncoalesced ReadFile count");
      if (ob.cnt.readfile_calls > oa.cnt.readfile_calls) ++redo_cases;
    } else {
      bool fast = AllowsUnlockedReads(fb[c.file].get()) && c.offset != uint64_t(-1) &&
                  c.offset != uint64_t(-2) && c.knobs.io_unlocked_file_reads;
      if (ob.cnt.shared_lock != (fast ? 1u : 0u)) fail("Read dispatch path");
    }
    // Every few cases, the whole of both arenas must still be identical.
    if ((idx & 31) == 31 || idx + 1 == ncases) {
      ++full_compares;
      if (std::memcmp(A.virtual_membase(), B.virtual_membase(), VIRT_COMMIT) != 0 ||
          std::memcmp(A.physical_membase(), B.physical_membase(), PHYS_COMMIT) != 0)
        fail("full arena compare");
    }

    ClsStats& s = st[c.cls];
    ++s.cases;
    if (oa.status == X_STATUS_SUCCESS) ++s.ok_status;
    s.bytes += oa.out == 0xDEADBEEF ? 0 : oa.out;
    if (ob.path == ScatterPath::kPositional) ++s.positional;
    s.rf_old += oa.cnt.readfile_calls;
    s.rf_new += ob.cnt.readfile_calls;
    rf_a += oa.cnt.readfile_calls;
    rf_b += ob.cnt.readfile_calls;
    gl_a += oa.cnt.global_lock;
    gl_b += ob.cnt.global_lock;
    pre_b += ob.cnt.precheck_calls;
    fired_a += recA.fired.size();
    fired_b += recB.fired.size();
    fix_a += recA.fixups.size();
    fix_b += recB.fixups.size();
    if (!why.empty()) {
      ++s.fails;
      if (++fails <= 12) {
        std::printf(
            "FAIL case %" PRIu64 " [%s] %s: file=%d off=0x%" PRIX64 " len=0x%X nseg=%zu seg0=0x%08X "
            "pos=0x%" PRIX64 " kind=%d deny=%d knobs=%d%d%d | OLD st=0x%08X out=0x%X pos=0x%" PRIX64
            " | NEW st=0x%08X out=0x%X pos=0x%" PRIX64 " path=%s rf %" PRIu64 "/%" PRIu64 "\n",
            idx, kClsNames[c.cls], why.c_str(), c.file, c.offset, c.length, c.segs.size(),
            c.segs[0], c.position, int(c.kind), int(c.deny), int(c.knobs.io_coalesce_scatter_reads),
            int(c.knobs.io_unlocked_file_reads), int(c.knobs.io_lockless_watch_check), oa.status,
            oa.out, oa.position, ob.status, ob.out, ob.position, path_name(ob.path),
            oa.cnt.readfile_calls, ob.cnt.readfile_calls);
      }
    }
  }
  double t1 = qpc_seconds();

  std::printf("\nT1 scatter/read differential: %" PRIu64 " cases, seed 0x%" PRIX64 ", %.2f s\n",
              ncases, seed, t1 - t0);
  std::printf("%-18s %6s %6s %8s %10s %11s %9s %9s\n", "class", "cases", "fails", "status0",
              "bytes(OLD)", "positional", "RF old", "RF new");
  for (int i = 0; i < kNumCls; ++i) {
    const ClsStats& s = st[i];
    std::printf("%-18s %6" PRIu64 " %6" PRIu64 " %8" PRIu64 " %10" PRIu64 " %11" PRIu64
                " %9" PRIu64 " %9" PRIu64 "\n",
                kClsNames[i], s.cases, s.fails, s.ok_status, s.bytes, s.positional, s.rf_old,
                s.rf_new);
  }
  std::printf("totals: ReadFile OLD %" PRIu64 " NEW %" PRIu64 " | global-lock OLD %" PRIu64
              " NEW %" PRIu64 " (NEW prechecks %" PRIu64 ") | callbacks fired OLD %" PRIu64
              " NEW %" PRIu64 " | fixup calls OLD %" PRIu64 " NEW %" PRIu64 "\n",
              rf_a, rf_b, gl_a, gl_b, pre_b, fired_a, fired_b, fix_a, fix_b);
  std::printf("info: cases where NEW issued more ReadFile calls than OLD (run redone page by "
              "page): %" PRIu64 "; watch bits NEW cleared beyond OLD: %" PRIu64
              "; full-arena compares: %" PRIu64 "\n",
              redo_cases, extra_bits, full_compares);

  // ---- T1-straddle (informational): a 2-byte fixup across a 4 KB boundary.
  ClearFileReadFixups();
  RegisterFileReadFixup(straddle_fixup);
  uint64_t contig_n = 0, contig_new = 0, contig_old = 0, broken_n = 0, broken_new = 0,
           broken_old = 0;
  for (int i = 0; i < 64; ++i) {
    Case c;
    c.cls = kContig;
    c.file = 4;
    uint32_t n = 2 + uint32_t(i % 7);
    c.length = n * kPage;
    c.segs.assign(n, 0);
    uint32_t j = 1 + uint32_t(i % (n - 1));  // boundary between pages j-1 and j
    c.offset = kStraddle + 1 - uint64_t(j) * kPage;
    fill_contig(c, H0_BASE + 0x40000 + uint32_t(i) * 0x2000);
    bool broken = (i & 1) != 0;
    if (broken)
      for (uint32_t k = j; k < n; ++k) c.segs[k] += kPage * 16;
    c.poison_seed = 0x5700 + i;
    std::vector<uint32_t> pages = window_pages(c);
    setup_memory(A, c, pages);
    setup_memory(B, c, pages);
    fa[4]->kind = fb[4]->kind = FileKind::kHostPath;
    fa[4]->set_file_access_for_test(FileAccess::kGenericRead);
    fb[4]->set_file_access_for_test(FileAccess::kGenericRead);
    ra[4]->RefreshUnlockedReadsOk();
    rb[4]->RefreshUnlockedReadsOk();
    run_one(A, *ra[4], c, false, recA);
    run_one(B, *rb[4], c, true, recB);
    auto applied = [&](MockMemory& m) {
      uint32_t a0 = c.segs[j - 1] + kPage - 1, a1 = c.segs[j];
      return *m.TranslateVirtual(a0) == 0x20 && *m.TranslateVirtual(a1) == 0x20;
    };
    if (broken) {
      ++broken_n;
      broken_old += applied(A);
      broken_new += applied(B);
    } else {
      ++contig_n;
      contig_old += applied(A);
      contig_new += applied(B);
    }
  }
  ClearFileReadFixups();
  std::printf("T1-straddle (info, not a FAIL): 2-byte fixup across a 4 KB file boundary: "
              "contiguous runs OLD applied %" PRIu64 "/%" PRIu64 ", NEW %" PRIu64 "/%" PRIu64
              "; split runs OLD %" PRIu64 "/%" PRIu64 ", NEW %" PRIu64 "/%" PRIu64 "\n",
              contig_old, contig_n, contig_new, contig_n, broken_old, broken_n, broken_new,
              broken_n);

  std::printf("\nT1 RESULT: %s (%" PRIu64 " failing cases of %" PRIu64 ")\n",
              fails ? "FAIL" : "PASS", fails, ncases);
  return fails ? 1 : 0;
}
