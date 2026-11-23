// Shared by test_untile_runs.cpp and bench_untile.cpp: the previous 2D/cube
// copy (CopyTextureVolumeBlocks + the textures.cpp offset callback, calling
// the SDK GetTiledOffset2D out of line) and the new CopyTexture2DBlocks call.
#pragma once

#include <bit>
#include <cstdint>
#include <span>

#include "gpu_native/texture_volume_upload.h"

namespace rex::graphics::texture_util {
int32_t GetTiledOffset2D(int32_t x, int32_t y, uint32_t pitch, uint32_t bytes_per_block_log2);
}  // namespace rex::graphics::texture_util

namespace agent5 {
using u8 = uint8_t;
using u32 = uint32_t;
using u64 = uint64_t;

// rex::log2_floor<uint32_t>: 31 - lzcnt(v).
inline u32 Log2Floor(u32 v) { return 31u - u32(std::countl_zero(v)); }

struct Slice2D {
  u32 width_blocks = 1, height_blocks = 1, block_bytes = 4, row_pitch = 256, endian_xor = 0;
  bool tiled = false;
  u32 offset_x = 0, offset_y = 0, guest_pitch = 0;  // guest_level.row_pitch_bytes
};

// textures.cpp UploadTextureResourceStorage, 2D/cube callback, verbatim apart
// from the captured names.
inline auto Callback(const Slice2D& s) {
  namespace tu = rex::graphics::texture_util;
  return [&s](u32 x, u32 y, u32) -> int64_t {
    const u32 offset_x = s.offset_x, offset_y = s.offset_y, block_bytes = s.block_bytes;
    if (s.tiled)
      return tu::GetTiledOffset2D(x + offset_x, y + offset_y,
          s.guest_pitch / block_bytes, Log2Floor(block_bytes));
    return u64(y + offset_y) * s.guest_pitch +
           u64(x + offset_x) * block_bytes;
  };
}

inline bool CopyOld(const Slice2D& s, std::span<const u8> source, std::span<u8> destination) {
  return legodimensions::gpu_native::CopyTextureVolumeBlocks(source, destination,
      s.width_blocks, s.height_blocks, 1, s.block_bytes, s.row_pitch, s.endian_xor, Callback(s));
}

inline bool CopyNew(const Slice2D& s, std::span<const u8> source, std::span<u8> destination) {
  return legodimensions::gpu_native::CopyTexture2DBlocks(source, destination,
      s.width_blocks, s.height_blocks, s.block_bytes, s.row_pitch, s.endian_xor,
      {s.tiled, s.offset_x, s.offset_y, s.guest_pitch}, Callback(s));
}

// Smallest source size for which the old copy succeeds; 0 if no size does
// (negative offset or an invalid slice).
inline u64 RequiredSourceBytes(const Slice2D& s) {
  if (!s.width_blocks || !s.height_blocks || !s.block_bytes || s.endian_xor > 3) return 0;
  const auto offset = Callback(s);
  u64 need = 0;
  for (u32 y = 0; y < s.height_blocks; ++y)
    for (u32 x = 0; x < s.width_blocks; ++x) {
      const int64_t at = offset(x, y, 0);
      if (at < 0) return 0;
      for (u32 byte = 0; byte < s.block_bytes; ++byte) {
        const u64 src = (u64(at) + byte) ^ s.endian_xor;
        if (src + 1 > need) need = src + 1;
      }
    }
  return need;
}
}  // namespace agent5
