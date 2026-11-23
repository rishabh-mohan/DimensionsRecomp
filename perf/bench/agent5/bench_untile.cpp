// Benchmark: previous 2D/cube copy (CopyTextureVolumeBlocks + callback with
// the out-of-line SDK GetTiledOffset2D) vs CopyTexture2DBlocks. One thread.
// Each sample times `iters` copies; old/new samples are interleaved; reports
// the median of the samples in ms per copy.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>

#include "untile_reference.h"

using namespace agent5;

namespace {
u32 AlignUp(u32 v, u32 a) { return (v + a - 1) / a * a; }

double Median(std::vector<double> v) {
  std::sort(v.begin(), v.end());
  return v.size() & 1 ? v[v.size() / 2] : 0.5 * (v[v.size() / 2 - 1] + v[v.size() / 2]);
}

struct Format { const char* name; u32 block_bytes, block_width, endian_xor; };
}  // namespace

int main(int argc, char** argv) {
  const int samples = argc > 1 ? std::max(5, std::atoi(argv[1])) : 7;
  // Typical guest endianness: k8in32 (XOR 3) for 32-bit texels, k8in16
  // (XOR 1) for 16-bit texels and DXT blocks.
  const std::array<Format, 6> formats{{{"R8", 1, 1, 1}, {"RG8/565", 2, 1, 1},
                                       {"RGBA8", 4, 1, 3}, {"BC1", 8, 4, 1},
                                       {"BC3", 16, 4, 1}, {"RGBA8-noswap", 4, 1, 0}}};
  const std::array<u32, 3> sizes{256, 1024, 2048};
  std::mt19937_64 rng(1121);
  std::printf("| format | texels | layout | endian | old ms | new ms | speedup |\n");
  std::printf("|---|---|---|---|---:|---:|---:|\n");
  volatile u32 sink = 0;
  for (const auto& f : formats)
    for (u32 size : sizes)
      for (bool tiled : {true, false}) {
        Slice2D s;
        s.block_bytes = f.block_bytes;
        s.width_blocks = s.height_blocks = size / f.block_width;
        s.endian_xor = f.endian_xor;
        s.tiled = tiled;
        s.row_pitch = AlignUp(s.width_blocks * s.block_bytes, 256);
        s.guest_pitch = AlignUp(s.width_blocks * s.block_bytes, tiled ? 32 * s.block_bytes : 256);
        const u64 need = RequiredSourceBytes(s);
        std::vector<u8> source(static_cast<size_t>(need));
        std::vector<u8> a(static_cast<size_t>(u64(s.row_pitch) * s.height_blocks)), b(a.size());
        for (auto& byte : source) byte = u8(rng());
        // Warm up and check equality once.
        if (!CopyOld(s, source, a) || !CopyNew(s, source, b) || a != b) {
          std::fprintf(stderr, "mismatch %s %u\n", f.name, size);
          return 1;
        }
        const u64 texels = u64(size) * size;
        const int iters = int(std::max<u64>(1, (u64(8) << 20) / texels));
        std::vector<double> old_ms, new_ms;
        for (int sample = 0; sample < samples; ++sample) {
          for (int which = 0; which < 2; ++which) {
            const auto start = std::chrono::steady_clock::now();
            for (int i = 0; i < iters; ++i)
              sink = sink + (which ? CopyNew(s, source, b) : CopyOld(s, source, a));
            const double ms = std::chrono::duration<double, std::milli>(
                std::chrono::steady_clock::now() - start).count() / iters;
            (which ? new_ms : old_ms).push_back(ms);
          }
        }
        const double o = Median(old_ms), n = Median(new_ms);
        std::printf("| %s | %ux%u | %s | %u | %.3f | %.3f | %.1fx |\n", f.name, size, size,
                    tiled ? "tiled" : "linear", f.endian_xor, o, n, o / n);
      }
  std::printf("\n%d samples per cell, median; %s\n", samples,
#if defined(__AVX2__)
              "built with AVX2 (x86-64-v3)"
#elif defined(__SSSE3__)
              "built with SSSE3"
#else
              "built without SSSE3"
#endif
  );
  return sink == 0xFFFFFFFFu;
}
