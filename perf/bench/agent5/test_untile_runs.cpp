// Differential test for CopyTexture2DBlocks (texture_volume_upload.h) against
// the previous per-block path: CopyTextureVolumeBlocks with the textures.cpp
// callback and the SDK GetTiledOffset2D (extracted verbatim, out of line).
// Every case must return the same bool; on success every destination byte
// (including row padding and slack left untouched) must match.
#include <algorithm>
#include <array>
#include <chrono>
#include <cinttypes>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <vector>

#include "untile_reference.h"

using namespace agent5;
namespace detail = legodimensions::gpu_native::texture_copy_detail;
namespace tu = rex::graphics::texture_util;

namespace {
std::mt19937_64 rng(0xA5E5'2026'1121ull);
u64 cases = 0, successes = 0, failures_matched = 0, fast_cases = 0;

u32 Rand(u32 below) { return below ? u32(rng() % below) : 0; }

[[noreturn]] void Fail(const char* what, const Slice2D& s, u64 source_size, size_t dst_size) {
  std::fprintf(stderr,
      "FAIL %s: w=%u h=%u bpb=%u pitch=%u e=%u tiled=%d ox=%u oy=%u guest_pitch=%u "
      "source=%" PRIu64 " dst=%zu\n",
      what, s.width_blocks, s.height_blocks, s.block_bytes, s.row_pitch, s.endian_xor,
      int(s.tiled), s.offset_x, s.offset_y, s.guest_pitch, source_size, dst_size);
  std::exit(1);
}

std::vector<u8> RandomBytes(size_t n) {
  std::vector<u8> bytes(n);
  for (size_t i = 0; i < n; i += 8) {
    const u64 v = rng();
    std::memcpy(bytes.data() + i, &v, std::min<size_t>(8, n - i));
  }
  return bytes;
}

bool InFastDomain(const Slice2D& s) {
  const u32 log2 = s.block_bytes == 1 ? 0 : s.block_bytes == 2 ? 1 : s.block_bytes == 4 ? 2
      : s.block_bytes == 8 ? 3 : s.block_bytes == 16 ? 4 : 5;
  if (log2 == 5) return false;
  const legodimensions::gpu_native::Texture2DSourceLayout layout{s.tiled, s.offset_x,
                                                                s.offset_y, s.guest_pitch};
  return s.tiled ? detail::TiledRowsFit(s.width_blocks, s.height_blocks, layout,
                                        s.guest_pitch / s.block_bytes, log2)
                 : detail::LinearRowsFit(s.width_blocks, s.height_blocks, s.block_bytes, layout);
}

// One slice against one source size and one destination size. Both
// destinations start with the same random fill byte, so a stray or missing
// write shows up as a difference (the source bytes are random).
void Compare(const Slice2D& s, std::span<const u8> source, size_t dst_size) {
  std::vector<u8> expected(dst_size, u8(rng())), actual = expected;
  const bool old_ok = CopyOld(s, source, expected);
  const bool new_ok = CopyNew(s, source, actual);
  ++cases;
  if (old_ok != new_ok) Fail(old_ok ? "new rejected" : "new accepted", s, source.size(), dst_size);
  if (old_ok) {
    ++successes;
    if (expected != actual) Fail("bytes differ", s, source.size(), dst_size);
  } else {
    ++failures_matched;
  }
}

// Exact-size source, truncated sources and a longer source; exact and short
// destinations.
void CompareSizes(const Slice2D& s, u32 extra_truncations = 0) {
  if (InFastDomain(s)) ++fast_cases;
  const u64 need = RequiredSourceBytes(s);
  const u64 cap = std::max<u64>(need, 64) + 96;
  if (cap > (64u << 20)) Fail("test source too large", s, need, 0);
  const auto source = RandomBytes(size_t(cap));
  const size_t dst = size_t(u64(s.row_pitch) * s.height_blocks);
  std::vector<u64> sizes{need, need + 1, need + 77, cap};
  for (u64 shorter : {1, 2, 3, 4, 5, 7, 8, 9, 15, 16, 17, 31, 32, 33, 63, 64})
    if (shorter <= need) sizes.push_back(need - shorter);
  for (u32 i = 0; i < extra_truncations && need; ++i) sizes.push_back(Rand(u32(need)));
  for (u64 size : sizes)
    Compare(s, std::span<const u8>(source).first(size_t(size)), dst + Rand(9));
  // A destination one row-pitch short, and one byte short.
  if (dst) {
    Compare(s, std::span<const u8>(source).first(size_t(need)), dst - 1);
    Compare(s, std::span<const u8>(source).first(size_t(need)), dst - std::min<size_t>(dst, s.row_pitch));
  }
}

u32 AlignUp(u32 v, u32 a) { return (v + a - 1) / a * a; }

// Wide reference of GetTiledOffset2D; shows the int32 copy did not overflow.
int64_t WideTiledOffset2D(int64_t x, int64_t y, uint32_t pitch, uint32_t log2) {
  const int64_t aligned = int64_t((pitch + 31u) & ~31u);
  const int64_t macro = ((x >> 5) + (y >> 5) * (aligned >> 5)) * (int64_t(1) << (log2 + 7));
  const int64_t micro = ((x & 7) + ((y & 0xE) << 2)) << log2;
  const int64_t offset = macro + ((micro & ~int64_t(0xF)) << 1) + (micro & 0xF) + ((y & 1) << 4);
  return (offset & ~int64_t(0x1FF)) * 8 + ((y & 16) << 7) + ((offset & 0x1C0) << 2) +
         (((((y & 8) >> 2) + (x >> 3)) & 3) << 6) + (offset & 0x3F);
}

void TestFormula() {
  // Inline copy == SDK (extracted) wherever the fast path may use it.
  const std::array<u32, 14> pitches{0, 1, 2, 31, 32, 33, 64, 100, 256, 1000, 1024, 4096,
                                    0xFFFFFFE0u, 0xFFFFFFFFu};
  u64 checked = 0;
  for (u32 log2 = 0; log2 <= 4; ++log2)
    for (u32 pitch : pitches)
      for (u32 y = 0; y < 256; ++y)
        for (u32 x = 0; x < 256; ++x) {
          const legodimensions::gpu_native::Texture2DSourceLayout layout{true, x, y, 0};
          if (!detail::TiledRowsFit(1, 1, layout, pitch, log2)) continue;
          const int32_t sdk = tu::GetTiledOffset2D(int32_t(x), int32_t(y), pitch, log2);
          const int32_t inl = detail::TiledOffset2D(int32_t(x), int32_t(y), pitch, log2);
          if (sdk != inl || int64_t(inl) != WideTiledOffset2D(x, y, pitch, log2) || inl < 0) {
            std::fprintf(stderr, "FAIL formula x=%u y=%u pitch=%u log2=%u sdk=%d inline=%d\n",
                         x, y, pitch, log2, sdk, inl);
            std::exit(1);
          }
          ++checked;
        }
  // Random slices accepted by TiledRowsFit: corners and random points stay
  // within int32 and match the SDK.
  u64 accepted = 0;
  for (u32 i = 0; i < 400000; ++i) {
    const u32 log2 = Rand(5);
    const u32 scale = 1u << Rand(31);
    const u32 w = 1 + Rand(scale < 2 ? 2 : scale), h = 1 + Rand(1u << Rand(31));
    const legodimensions::gpu_native::Texture2DSourceLayout layout{true, Rand(1u << Rand(31)),
                                                                  Rand(1u << Rand(31)), 0};
    const u32 pitch = Rand(4) ? Rand(1u << Rand(31)) : u32(rng());
    if (!detail::TiledRowsFit(w, h, layout, pitch, log2)) continue;
    ++accepted;
    for (u32 k = 0; k < 6; ++k) {
      const u32 x = layout.offset_x + (k == 0 ? 0 : k == 1 ? w - 1 : Rand(w));
      const u32 y = layout.offset_y + (k == 0 ? 0 : k == 1 ? h - 1 : Rand(h));
      const int64_t wide = WideTiledOffset2D(x, y, pitch, log2);
      const int32_t sdk = tu::GetTiledOffset2D(int32_t(x), int32_t(y), pitch, log2);
      const int32_t inl = detail::TiledOffset2D(int32_t(x), int32_t(y), pitch, log2);
      if (wide < 0 || wide > INT32_MAX || sdk != inl || int64_t(inl) != wide) {
        std::fprintf(stderr, "FAIL domain x=%u y=%u pitch=%u log2=%u wide=%" PRId64 "\n",
                     x, y, pitch, log2, wide);
        std::exit(1);
      }
    }
  }
  std::printf("formula: %" PRIu64 " exhaustive points, %" PRIu64 " random in-domain slices\n",
              checked, accepted);
}

void TestSweep() {
  const std::array<u32, 5> blocks{1, 2, 4, 8, 16};
  const std::array<u32, 22> widths{1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 15, 16, 17, 23, 31, 32, 33,
                                   47, 63, 64, 65, 129};
  const std::array<u32, 5> heights{1, 2, 3, 8, 33};
  const std::array<u32, 9> offsets_x{0, 1, 2, 3, 4, 7, 8, 16, 31};
  const std::array<u32, 4> offsets_y{0, 1, 9, 31};
  for (u32 block_bytes : blocks)
    for (u32 endian = 0; endian < 4; ++endian)
      for (bool tiled : {false, true})
        for (u32 w : widths)
          for (u32 h : heights)
            for (u32 ox : offsets_x)
              for (u32 oy : offsets_y) {
                Slice2D s;
                s.width_blocks = w; s.height_blocks = h; s.block_bytes = block_bytes;
                s.endian_xor = endian; s.tiled = tiled; s.offset_x = ox; s.offset_y = oy;
                // Production: host pitch is 256-aligned; guest tiled pitch is
                // 32-block aligned, linear 256-byte aligned. Alternate with
                // tight / unaligned pitches.
                const bool odd = (w + h + ox + oy) & 1;
                s.row_pitch = odd ? w * block_bytes : AlignUp(w * block_bytes, 256);
                const u32 extent = (ox + w) * block_bytes;
                s.guest_pitch = tiled ? (odd ? extent + 3 * block_bytes : AlignUp(extent, 32 * block_bytes))
                                      : (odd ? extent + 1 + Rand(5) : AlignUp(extent, 256));
                CompareSizes(s);
              }
}

void TestRandom(u32 count) {
  for (u32 i = 0; i < count; ++i) {
    Slice2D s;
    const u32 pick = Rand(16);
    s.block_bytes = pick < 13 ? 1u << (pick % 5) : pick == 13 ? 3 : pick == 14 ? 12 : 6;
    s.width_blocks = 1 + Rand(Rand(4) ? 40 : 300);
    s.height_blocks = 1 + Rand(Rand(4) ? 6 : 40);
    s.endian_xor = Rand(4);
    s.tiled = Rand(2);
    s.offset_x = Rand(4) ? Rand(32) : Rand(200);
    s.offset_y = Rand(4) ? Rand(32) : Rand(200);
    s.row_pitch = s.width_blocks * s.block_bytes + (Rand(2) ? 0 : Rand(300));
    const u32 extent = (s.offset_x + s.width_blocks) * s.block_bytes;
    switch (Rand(4)) {
      case 0: s.guest_pitch = AlignUp(extent, s.tiled ? 32 * s.block_bytes : 256); break;
      case 1: s.guest_pitch = extent + Rand(64); break;
      case 2: s.guest_pitch = Rand(extent + 1); break;  // overlapping rows
      default: s.guest_pitch = Rand(1u << 14); break;
    }
    CompareSizes(s, 3);
  }
}

void TestLarge() {
  struct Large { u32 w, h, bpb, endian; bool tiled; u32 ox, oy; };
  const std::array<Large, 12> large{{
      {256, 256, 4, 3, true, 0, 0}, {1024, 1024, 4, 3, true, 0, 0}, {512, 512, 1, 1, true, 0, 0},
      {512, 256, 2, 1, true, 0, 0}, {256, 256, 8, 1, true, 0, 0}, {256, 256, 16, 1, true, 0, 0},
      {1000, 333, 4, 2, true, 5, 17}, {640, 480, 4, 3, false, 0, 0}, {333, 77, 2, 1, false, 3, 9},
      {1024, 64, 1, 0, true, 16, 0}, {2048, 8, 4, 0, true, 0, 0}, {130, 130, 4, 3, true, 2, 30}}};
  for (const auto& l : large) {
    Slice2D s;
    s.width_blocks = l.w; s.height_blocks = l.h; s.block_bytes = l.bpb; s.endian_xor = l.endian;
    s.tiled = l.tiled; s.offset_x = l.ox; s.offset_y = l.oy;
    s.row_pitch = AlignUp(l.w * l.bpb, 256);
    s.guest_pitch = AlignUp((l.ox + l.w) * l.bpb, l.tiled ? 32 * l.bpb : 256);
    CompareSizes(s);
  }
}

// Inputs outside the fast-path domain or failing preconditions take the old
// path or fail identically.
void TestEdges() {
  std::vector<Slice2D> edges;
  auto add = [&](u32 w, u32 h, u32 bpb, u32 pitch, u32 e, bool tiled, u32 ox, u32 oy, u32 gp) {
    Slice2D s;
    s.width_blocks = w; s.height_blocks = h; s.block_bytes = bpb; s.row_pitch = pitch;
    s.endian_xor = e; s.tiled = tiled; s.offset_x = ox; s.offset_y = oy; s.guest_pitch = gp;
    edges.push_back(s);
  };
  for (bool tiled : {false, true})
    for (u32 bpb : {1u, 2u, 4u, 8u, 16u}) {
      add(0, 4, bpb, 256, 0, tiled, 0, 0, 256);           // empty width
      add(4, 0, bpb, 256, 0, tiled, 0, 0, 256);           // empty height
      add(4, 4, bpb, 256, 4, tiled, 0, 0, 256);           // invalid endian
      add(64, 2, bpb, 64 * bpb - 1, 0, tiled, 0, 0, 4096);  // pitch below the row
      add(8, 8, bpb, 256, 3, tiled, (1u << 30) - 8, 0, 256);  // at the int32 guard
      add(8, 8, bpb, 256, 3, tiled, (1u << 30) - 7, 0, 256);
      add(8, 8, bpb, 256, 1, tiled, 0x80000000u, 0, 256);  // negative x
      add(8, 8, bpb, 256, 1, tiled, 0xFFFFFFF8u, 0xFFFFFFFCu, 256);  // u32 wrap
      add(8, 8, bpb, 256, 2, tiled, 0, 0, 0xFFFFFFF0u);    // align(pitch) wraps
      add(8, 8, bpb, 256, 2, tiled, 0, 0, 0xFFFFFFFFu);
      add(8, 4, bpb, 256, 2, tiled, 0, (1u << 20), 1u << 16);  // macro bound
      add(8, 4, bpb, 256, 0, tiled, 4, 3, 0);              // zero guest pitch
    }
  for (const auto& s : edges) {
    const auto source = RandomBytes(4096);
    for (size_t size : {size_t(0), size_t(1), size_t(64), size_t(4096)})
      for (size_t dst : {size_t(0), size_t(u64(s.row_pitch) * s.height_blocks)})
        Compare(s, std::span<const u8>(source).first(size), dst);
  }
}
}  // namespace

template <class F>
void Phase(const char* name, F&& run) {
  const u64 before = cases;
  const auto start = std::chrono::steady_clock::now();
  run();
  std::printf("  %-8s %9" PRIu64 " copies %6.1f s\n", name, cases - before,
              std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count());
}

int main(int argc, char** argv) {
  const u32 random_cases = argc > 1 ? u32(std::strtoul(argv[1], nullptr, 10)) : 20000;
  Phase("formula", TestFormula);
  Phase("edges", TestEdges);
  Phase("large", TestLarge);
  Phase("sweep", TestSweep);
  Phase("random", [&] { TestRandom(random_cases); });
  std::printf("PASS %" PRIu64 " copies (%" PRIu64 " succeeded, %" PRIu64
              " failed identically); %" PRIu64 " slices in the fast-path domain; %s\n",
              cases, successes, failures_matched, fast_cases,
#if defined(__AVX2__)
              "AVX2+SSSE3 build"
#elif defined(__SSSE3__)
              "SSSE3 build"
#else
              "scalar (no SSSE3) build"
#endif
  );
  return 0;
}
