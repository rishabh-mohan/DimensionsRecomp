#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <span>
#include "gpu_native/texture_endian.h"
#include "gpu_native/upload_legacy_paths.h"
#if defined(__SSSE3__)
#include <tmmintrin.h>
#endif

namespace legodimensions::gpu_native {

namespace texture_copy_detail {
template <typename SourceOffset>
bool CopyBytewise(std::span<const uint8_t> source, std::span<uint8_t> destination,
                  uint32_t width_blocks, uint32_t height_blocks, uint32_t depth,
                  uint32_t block_bytes, uint32_t row_pitch, uint32_t endian_xor,
                  SourceOffset source_offset) {
  if (!width_blocks || !height_blocks || !depth || !block_bytes || endian_xor > 3 ||
      uint64_t(width_blocks) * block_bytes > row_pitch) return false;
  const uint64_t slice_pitch = uint64_t(row_pitch) * height_blocks;
  if (slice_pitch > destination.size() / depth) return false;
  for (uint32_t z = 0; z < depth; ++z)
    for (uint32_t y = 0; y < height_blocks; ++y)
      for (uint32_t x = 0; x < width_blocks; ++x) {
        const int64_t offset = source_offset(x, y, z);
        if (offset < 0) return false;
        const uint64_t dst = z * slice_pitch + uint64_t(y) * row_pitch +
                             uint64_t(x) * block_bytes;
        for (uint32_t byte = 0; byte < block_bytes; ++byte) {
          const uint64_t src = (uint64_t(offset) + byte) ^ endian_xor;
          if (src >= source.size()) return false;
          destination[size_t(dst + byte)] = source[size_t(src)];
        }
      }
  return true;
}
}  // namespace texture_copy_detail

// Source addressing comes from the guest layout (including 3D tiling and mip
// tail offsets). D3D12 upload slices use the actual block-row count, not the
// guest's tile-aligned Z stride. Keep decoding in cacheable CPU memory.
template <typename SourceOffset>
bool CopyTextureVolumeBlocks(std::span<const uint8_t> source,
                             std::span<uint8_t> destination,
                             uint32_t width_blocks, uint32_t height_blocks,
                             uint32_t depth, uint32_t block_bytes,
                             uint32_t row_pitch, uint32_t endian_xor,
                             SourceOffset source_offset) {
  // Keep small texels on the old loop: measured RGBA word-copy dispatch
  // regressed this case, whereas 8/16-byte compressed blocks benefit.
  if (block_bytes < 8)
    return texture_copy_detail::CopyBytewise(source, destination, width_blocks,
        height_blocks, depth, block_bytes, row_pitch, endian_xor, source_offset);
  if (!width_blocks || !height_blocks || !depth || !block_bytes || endian_xor > 3 ||
      uint64_t(width_blocks) * block_bytes > row_pitch) return false;
  const uint64_t slice_pitch = uint64_t(row_pitch) * height_blocks;
  if (slice_pitch > destination.size() / depth) return false;
  for (uint32_t z = 0; z < depth; ++z) {
    for (uint32_t y = 0; y < height_blocks; ++y) {
      for (uint32_t x = 0; x < width_blocks; ++x) {
        const int64_t offset = source_offset(x, y, z);
        if (offset < 0) return false;
        const uint64_t dst = z * slice_pitch + uint64_t(y) * row_pitch +
                             uint64_t(x) * block_bytes;
        // The usual tiled BC blocks are word aligned. Validate their
        // complete span once, then convert whole words instead of checking
        // and XOR-addressing every byte. Unaligned / sub-word blocks retain
        // the exact absolute-address XOR path below.
        if (!endian_xor || (!(uint64_t(offset) & 3) && !(block_bytes & 3))) {
          const uint64_t src = uint64_t(offset);
          if (src > source.size() || block_bytes > source.size() - src) return false;
          auto* out = destination.data() + size_t(dst);
          const auto* in = source.data() + size_t(src);
          if (!endian_xor) {
            std::memcpy(out, in, block_bytes);
          } else {
            for (uint32_t byte = 0; byte < block_bytes; byte += 4) {
              uint32_t word;
              std::memcpy(&word, in + byte, sizeof(word));
              if (endian_xor & 1)
                word = ((word & 0xFF00FF00u) >> 8) | ((word & 0x00FF00FFu) << 8);
              if (endian_xor & 2) word = (word >> 16) | (word << 16);
              std::memcpy(out + byte, &word, sizeof(word));
            }
          }
          continue;
        }
        for (uint32_t byte = 0; byte < block_bytes; ++byte) {
          const uint64_t src = (uint64_t(offset) + byte) ^ endian_xor;
          if (src >= source.size()) return false;
          destination[size_t(dst + byte)] = source[size_t(src)];
        }
      }
    }
  }
  return true;
}

// Guest addressing of one 2D/cube slice, in blocks (see CopyTexture2DBlocks).
struct Texture2DSourceLayout {
  bool tiled = false;
  uint32_t offset_x = 0, offset_y = 0;  // packed-mip offset
  uint32_t row_pitch_bytes = 0;         // guest row pitch
};

namespace texture_copy_detail {
// rex::graphics::texture_util::GetTiledOffset2D (rexglue-sdk util.cpp), copied
// so the run loop can inline it. Only used where TiledRowsFit holds.
inline int32_t TiledOffset2D(int32_t x, int32_t y, uint32_t pitch,
                             uint32_t bytes_per_block_log2) {
  pitch = (pitch + 31u) & ~31u;
  int32_t macro = ((x >> 5) + (y >> 5) * int32_t(pitch >> 5)) << (bytes_per_block_log2 + 7);
  int32_t micro = ((x & 7) + ((y & 0xE) << 2)) << bytes_per_block_log2;
  int32_t offset = macro + ((micro & ~0xF) << 1) + (micro & 0xF) + ((y & 1) << 4);
  return ((offset & ~0x1FF) << 3) + ((y & 16) << 7) + ((offset & 0x1C0) << 2) +
         (((((y & 8) >> 2) + (x >> 3)) & 3) << 6) + (offset & 0x3F);
}

// Every TiledOffset2D term for the slice is non-negative and below 2^31:
// the result is < ((macro + 1) << (log2 + 10)) + 4096.
inline bool TiledRowsFit(uint32_t width_blocks, uint32_t height_blocks,
                         const Texture2DSourceLayout& layout, uint32_t pitch, uint32_t log2) {
  const uint64_t last_x = uint64_t(layout.offset_x) + width_blocks - 1;
  const uint64_t last_y = uint64_t(layout.offset_y) + height_blocks - 1;
  if (last_x >= (1u << 30) || last_y >= (1u << 30)) return false;
  const uint64_t macro = (last_x >> 5) + (last_y >> 5) * (((pitch + 31u) & ~31u) >> 5);
  return macro < (1u << 21) && ((macro + 1) << (log2 + 10)) + 4096 <= 0x7FFFFFFFu;
}

// No u32 wrap in x/y + offset, and every offset + block is below 2^63.
inline bool LinearRowsFit(uint32_t width_blocks, uint32_t height_blocks,
                          uint32_t block_bytes, const Texture2DSourceLayout& layout) {
  const uint64_t last_x = uint64_t(layout.offset_x) + width_blocks - 1;
  const uint64_t last_y = uint64_t(layout.offset_y) + height_blocks - 1;
  return last_x <= UINT32_MAX && last_y <= UINT32_MAX && block_bytes <= 16 &&
         last_y * layout.row_pitch_bytes < (uint64_t(1) << 62);
}

// dst[k] = src[k ^ endian_xor] for whole words.
inline void CopySwappedWords(uint8_t* dst, const uint8_t* src, size_t bytes, uint32_t endian_xor) {
  for (size_t byte = 0; byte < bytes; byte += 4) {
    uint32_t word;
    std::memcpy(&word, src + byte, sizeof(word));
    if (endian_xor & 1) word = ((word & 0xFF00FF00u) >> 8) | ((word & 0x00FF00FFu) << 8);
    if (endian_xor & 2) word = (word >> 16) | (word << 16);
    std::memcpy(dst + byte, &word, sizeof(word));
  }
}

#if defined(__SSSE3__)
inline __m128i EndianShuffle(uint32_t endian_xor) {
  return _mm_xor_si128(_mm_setr_epi8(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15),
                       _mm_set1_epi8(char(endian_xor)));
}
#endif

// Tiled offsets advance by block_bytes over x-aligned runs of kRunBytes >>
// log2 blocks (8/8/4/2/1 for 1/2/4/8/16-byte blocks), and each run starts
// kRunBytes-aligned, so the endian XOR permutes bytes within the run.
// Unaligned row ends use the exact per-byte copy of CopyBytewise.
template <uint32_t kRunBytes>
bool CopyTiledRows(std::span<const uint8_t> source, std::span<uint8_t> destination,
                   uint32_t width_blocks, uint32_t height_blocks, uint32_t block_bytes,
                   uint32_t log2, uint32_t row_pitch, uint32_t endian_xor,
                   const Texture2DSourceLayout& layout) {
  const uint32_t run_blocks = kRunBytes >> log2;
  const uint32_t pitch = layout.row_pitch_bytes / block_bytes;
  const uint8_t* in = source.data();
  const uint64_t size = source.size();
#if defined(__SSSE3__)
  const __m128i shuffle = EndianShuffle(endian_xor);
#endif
  for (uint32_t y = 0; y < height_blocks; ++y) {
    const int32_t guest_y = int32_t(y + layout.offset_y);
    uint8_t* out = destination.data() + size_t(y) * row_pitch;
    const auto block = [&](uint32_t x) {
      const uint64_t offset =
          uint32_t(TiledOffset2D(int32_t(x + layout.offset_x), guest_y, pitch, log2));
      for (uint32_t byte = 0; byte < block_bytes; ++byte) {
        const uint64_t src = (offset + byte) ^ endian_xor;
        if (src >= size) return false;
        out[size_t(x) * block_bytes + byte] = in[src];
      }
      return true;
    };
    uint32_t x = 0;
    for (; x < width_blocks && ((x + layout.offset_x) & (run_blocks - 1)); ++x)
      if (!block(x)) return false;
    for (; width_blocks - x >= run_blocks; x += run_blocks) {
      const uint32_t offset =
          uint32_t(TiledOffset2D(int32_t(x + layout.offset_x), guest_y, pitch, log2));
      if (uint64_t(offset) + kRunBytes > size) return false;
      uint8_t* dst = out + size_t(x) * block_bytes;
#if defined(__SSSE3__)
      if constexpr (kRunBytes == 16)
        _mm_storeu_si128(reinterpret_cast<__m128i*>(dst), _mm_shuffle_epi8(
            _mm_loadu_si128(reinterpret_cast<const __m128i*>(in + offset)), shuffle));
      else
        _mm_storel_epi64(reinterpret_cast<__m128i*>(dst), _mm_shuffle_epi8(
            _mm_loadl_epi64(reinterpret_cast<const __m128i*>(in + offset)), shuffle));
#else
      if (!endian_xor) std::memcpy(dst, in + offset, kRunBytes);
      else CopySwappedWords(dst, in + offset, kRunBytes, endian_xor);
#endif
    }
    for (; x < width_blocks; ++x)
      if (!block(x)) return false;
  }
  return true;
}

// Linear rows are contiguous guest bytes. From a word-aligned offset the
// endian XOR stays within words; other rows use the exact per-byte copy.
inline bool CopyLinearRows(std::span<const uint8_t> source, std::span<uint8_t> destination,
                           uint32_t width_blocks, uint32_t height_blocks, uint32_t block_bytes,
                           uint32_t row_pitch, uint32_t endian_xor,
                           const Texture2DSourceLayout& layout) {
  const uint8_t* in = source.data();
  const uint64_t size = source.size(), row_bytes = uint64_t(width_blocks) * block_bytes;
#if defined(__SSSE3__)
  const __m128i shuffle = EndianShuffle(endian_xor);
#endif
  for (uint32_t y = 0; y < height_blocks; ++y) {
    const uint64_t offset = uint64_t(y + layout.offset_y) * layout.row_pitch_bytes +
                            uint64_t(layout.offset_x) * block_bytes;
    uint8_t* out = destination.data() + size_t(y) * row_pitch;
    uint64_t byte = 0;
    if (!endian_xor) {
      if (offset + row_bytes > size) return false;
      std::memcpy(out, in + offset, size_t(row_bytes));
      continue;
    }
    if (!(offset & 3)) {
      const uint64_t words = row_bytes & ~uint64_t(3);
      if (offset + words > size) return false;
#if defined(__SSSE3__)
      for (; byte + 16 <= words; byte += 16)
        _mm_storeu_si128(reinterpret_cast<__m128i*>(out + byte), _mm_shuffle_epi8(
            _mm_loadu_si128(reinterpret_cast<const __m128i*>(in + offset + byte)), shuffle));
#endif
      CopySwappedWords(out + byte, in + offset + byte, size_t(words - byte), endian_xor);
      byte = words;
    }
    for (; byte < row_bytes; ++byte) {
      const uint64_t src = (offset + byte) ^ endian_xor;
      if (src >= size) return false;
      out[size_t(byte)] = in[size_t(src)];
    }
  }
  return true;
}
}  // namespace texture_copy_detail

// One 2D/cube slice: the result of CopyTextureVolumeBlocks(source, destination,
// width_blocks, height_blocks, 1, ..., source_offset) when source_offset is the
// guest addressing that layout describes, i.e. GetTiledOffset2D(x + offset_x,
// y + offset_y, row_pitch_bytes / block_bytes, log2(block_bytes)) when tiled,
// else (y + offset_y) * row_pitch_bytes + (x + offset_x) * block_bytes. Copies
// whole runs/rows instead of single bytes. Non power-of-two blocks, or inputs
// whose address arithmetic could overflow, keep the per-block source_offset path,
// as does every slice when LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD=1 (in-game A/B).
template <typename SourceOffset>
bool CopyTexture2DBlocks(std::span<const uint8_t> source, std::span<uint8_t> destination,
                         uint32_t width_blocks, uint32_t height_blocks, uint32_t block_bytes,
                         uint32_t row_pitch, uint32_t endian_xor,
                         const Texture2DSourceLayout& layout, SourceOffset source_offset) {
  using namespace texture_copy_detail;
  const uint32_t log2 = block_bytes == 1 ? 0 : block_bytes == 2 ? 1 : block_bytes == 4 ? 2
      : block_bytes == 8 ? 3 : block_bytes == 16 ? 4 : 5;
  const bool fast = log2 < 5 && width_blocks && height_blocks && endian_xor <= 3 &&
      uint64_t(width_blocks) * block_bytes <= row_pitch &&
      uint64_t(row_pitch) * height_blocks <= destination.size() &&
      (layout.tiled ? TiledRowsFit(width_blocks, height_blocks, layout,
                                   layout.row_pitch_bytes / block_bytes, log2)
                    : LinearRowsFit(width_blocks, height_blocks, block_bytes, layout));
  if (!fast || LegacyUploadPathsEnabled())
    return CopyTextureVolumeBlocks(source, destination, width_blocks, height_blocks, 1,
                                   block_bytes, row_pitch, endian_xor, source_offset);
  if (!layout.tiled)
    return CopyLinearRows(source, destination, width_blocks, height_blocks, block_bytes,
                          row_pitch, endian_xor, layout);
  return log2 ? CopyTiledRows<16>(source, destination, width_blocks, height_blocks,
                                  block_bytes, log2, row_pitch, endian_xor, layout)
              : CopyTiledRows<8>(source, destination, width_blocks, height_blocks,
                                 block_bytes, log2, row_pitch, endian_xor, layout);
}

// After a successful CopyTexture2DBlocks / CopyTextureVolumeBlocks /
// CopyTextureAlpha4Blocks, every byte of rows [0, rows) except each row's pitch
// padding is written. Zero the rest of the level: [r * row_pitch + row_bytes,
// (r + 1) * row_pitch) for r < rows, then [rows * row_pitch, level.size()).
// Lets the decode buffer start uninitialised. Clamped to the level.
inline void ZeroTextureRowPadding(std::span<uint8_t> level, uint32_t row_pitch,
                                  uint64_t row_bytes, uint64_t rows) {
  const uint64_t size = level.size();
  const uint64_t written = !row_pitch ? 0 : rows <= size / row_pitch ? rows * row_pitch : size;
  if (row_bytes < row_pitch)
    for (uint64_t at = row_bytes; at < written; at += row_pitch) {
      const uint64_t padding = row_pitch - row_bytes;
      std::memset(level.data() + size_t(at), 0,
                  size_t(padding < written - at ? padding : written - at));
    }
  std::memset(level.data() + size_t(written), 0, size_t(size - written));
}

}  // namespace legodimensions::gpu_native
