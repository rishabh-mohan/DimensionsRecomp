#pragma once
#include <algorithm>
#include <array>
#include <cstring>
#include <numeric>
#include "gpu_native/vertex_byte_order.h"
#include "gpu_native/upload_legacy_paths.h"
#if defined(__SSSE3__)
#include <tmmintrin.h>
#endif
#if defined(__AVX2__)
#include <immintrin.h>
#endif

namespace legodimensions::gpu_native {
// Fuse DWORD endian conversion and the packed-field reversal into one
// sequential, write-only upload. Unsupported layouts retain the old path.
inline bool WriteAlignedVertexUpload(uint8_t* destination, const uint8_t* source,
                                    size_t size, const VertexByteOrder& order) {
  if (order.reversed_elements.empty() || order.stride < 4 || order.stride > 256 ||
      order.stride % 4 || order.stream_offset % 4 || order.stream_offset > size)
    return false;
  uint32_t previous = 0;
  bool first = true;
  for (uint32_t field : order.reversed_elements) {
    const uint32_t offset = VertexFieldOffset(field);
    if (offset % 4 || offset > order.stride - 4 || (!first && field <= previous)) return false;
    previous = field; first = false;
  }
  // 0 = plain DWORD swap, 1 = packed WZYX field (bytes stay), 2 = 16-bit halves.
  const auto packed = [&](size_t offset) -> int {
    if (offset < order.stream_offset) return 0;
    const auto field = uint32_t((offset - order.stream_offset) % order.stride);
    const auto& fields = order.reversed_elements;
    if (std::binary_search(fields.begin(), fields.end(), field)) return 1;
    return std::binary_search(fields.begin(), fields.end(), field | kHalfSwapField) ? 2 : 0;
  };
  static constexpr uint8_t kSource[3][4] = {{3, 2, 1, 0}, {0, 1, 2, 3}, {1, 0, 3, 2}};
  size_t offset = 0;
#if defined(__SSSE3__)
  // The stride and sixteen-byte SIMD chunks repeat after their LCM. Bound
  // this small table to64 chunks; every shuffle stays inside its own DWORD.
  const size_t blocks = order.stride / std::gcd(order.stride, 16u);
  alignas(16) std::array<std::array<uint8_t, 16>, 64> masks{};
  const size_t first_vector = (size_t(order.stream_offset) + 15) / 16 * 16;
  for (size_t b = 0; b < blocks; ++b)
    for (size_t lane = 0; lane < 16; lane += 4) {
      const int kind = packed(first_vector + b * 16 + lane);
      for (size_t byte = 0; byte < 4; ++byte)
        masks[b][lane + byte] = uint8_t(lane + kSource[kind][byte]);
    }
  // A non-canonical caller may leave a long unconverted prefix. Handle it
  // before the repeating phase, without applying packed fields too early.
  for (; offset < std::min(first_vector, size / 4 * 4); offset += 4) {
    const int kind = packed(offset);
    for (size_t byte = 0; byte < 4; ++byte) destination[offset + byte] = source[offset + kSource[kind][byte]];
  }
  size_t block = 0;
  for (; size - offset >= 16; offset += 16) {
    const auto value = _mm_loadu_si128(reinterpret_cast<const __m128i*>(source + offset));
    const auto mask = _mm_load_si128(reinterpret_cast<const __m128i*>(masks[block].data()));
    _mm_storeu_si128(reinterpret_cast<__m128i*>(destination + offset), _mm_shuffle_epi8(value, mask));
    if (++block == blocks) block = 0;
  }
#endif
  for (; size - offset >= 4; offset += 4) {
    const int kind = packed(offset);
    for (size_t byte = 0; byte < 4; ++byte) destination[offset + byte] = source[offset + kSource[kind][byte]];
  }
  if (offset != size) std::memcpy(destination + offset, source + offset, size - offset);
  return true;
}

// The previous buffers.cpp ByteSwapElements loop, verbatim. SwapUploadElementBytes
// runs it instead of its shuffles when LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD=1
// (in-game A/B); the output bytes are the same.
inline void SwapUploadElementBytesLegacy(uint8_t* destination, const uint8_t* source,
                                         size_t size, uint32_t element_size) {
  auto* dst = destination;
  const auto* src = source;
  size_t offset = 0;
  if (element_size == 2) {
    for (; offset + 2 <= size; offset += 2) {
      dst[offset + 0] = src[offset + 1];
      dst[offset + 1] = src[offset + 0];
    }
  } else {
    for (; offset + 4 <= size; offset += 4) {
      dst[offset + 0] = src[offset + 3];
      dst[offset + 1] = src[offset + 2];
      dst[offset + 2] = src[offset + 1];
      dst[offset + 3] = src[offset + 0];
    }
  }
  if (offset != size) {
    std::memcpy(dst + offset, src + offset, size - offset);
  }
}

// Swap whole 16-bit elements (element_size == 2) or 32-bit elements (any
// other element_size) from source into destination, and copy a trailing
// partial element unchanged. Byte-identical to the old buffers.cpp scalar
// loop: every 32- or 16-byte shuffle chunk holds whole elements of either
// width. source and destination must not overlap.
inline void SwapUploadElementBytes(uint8_t* destination, const uint8_t* source, size_t size,
                                   uint32_t element_size) {
  if (LegacyUploadPathsEnabled())
    return SwapUploadElementBytesLegacy(destination, source, size, element_size);
  const bool halves = element_size == 2;
  size_t offset = 0;
#if defined(__SSSE3__)
  const __m128i mask = halves
      ? _mm_setr_epi8(1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10, 13, 12, 15, 14)
      : _mm_setr_epi8(3, 2, 1, 0, 7, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12);
#if defined(__AVX2__)
  const __m256i wide_mask = _mm256_broadcastsi128_si256(mask);
  for (; size - offset >= 32; offset += 32) {
    const auto value = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(source + offset));
    _mm256_storeu_si256(reinterpret_cast<__m256i*>(destination + offset),
                        _mm256_shuffle_epi8(value, wide_mask));
  }
#endif
  for (; size - offset >= 16; offset += 16) {
    const auto value = _mm_loadu_si128(reinterpret_cast<const __m128i*>(source + offset));
    _mm_storeu_si128(reinterpret_cast<__m128i*>(destination + offset), _mm_shuffle_epi8(value, mask));
  }
#endif
  if (halves) {
    for (; size - offset >= 2; offset += 2) {
      destination[offset + 0] = source[offset + 1];
      destination[offset + 1] = source[offset + 0];
    }
  } else {
    for (; size - offset >= 4; offset += 4) {
      destination[offset + 0] = source[offset + 3];
      destination[offset + 1] = source[offset + 2];
      destination[offset + 2] = source[offset + 1];
      destination[offset + 3] = source[offset + 0];
    }
  }
  if (offset != size) std::memcpy(destination + offset, source + offset, size - offset);
}
} // namespace legodimensions::gpu_native
