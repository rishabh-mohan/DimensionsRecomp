// The pre-item-3 buffers.cpp ByteSwapElements, verbatim (anonymous namespace,
// buffers.cpp:151-172), as the differential-test and bench reference.
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace agent5_reference {
using u8 = uint8_t;
using u32 = uint32_t;
inline void ByteSwapElements(void* destination, const void* source, size_t size,
                             u32 element_size) {
  auto* dst = static_cast<u8*>(destination);
  const auto* src = static_cast<const u8*>(source);
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
}  // namespace agent5_reference
