// Item 3 differential test for the byte-swap upload path.
// SwapUploadElementBytes (gpu_native/vertex_upload.h) and the production
// buffers.cpp ByteSwapElements body (copied verbatim by build.ps1 into
// gen/buffers_byteswap.inc) must equal the old scalar ByteSwapElements
// (byteswap_reference.h) byte for byte and must not write outside
// [dst, dst + size). Covered: every size 0..300 with element sizes
// 0/1/2/3/4/8/16 (2 = 16-bit swaps, anything else = 32-bit swaps) and
// source/destination misalignment 0..15; sizes around 4 KB, 64 KB and 1 MB;
// 400 random large cases. Build the -march=x86-64-v3 (AVX2), -v2 (SSSE3) and
// -march=x86-64 (scalar) flavours: build.ps1 -Run -Only test_byteswap_v3,...
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <vector>
#include "byteswap_reference.h"
#include "gpu_native/vertex_upload.h"

namespace agent5_production {
using u8 = uint8_t;
using u32 = uint32_t;
using legodimensions::gpu_native::SwapUploadElementBytes;
#include "buffers_byteswap.inc"
}  // namespace agent5_production

#define CHECK(x)                                                \
  do {                                                          \
    if (!(x)) {                                                 \
      std::fprintf(stderr, "line %d: %s\n", __LINE__, #x);      \
      std::exit(23);                                            \
    }                                                           \
  } while (0)

namespace {
constexpr size_t kGuard = 48;
constexpr uint8_t kGuardByte = 0xEE;
std::vector<uint8_t> g_source;
unsigned g_cases = 0;

void Compare(size_t size, uint32_t element_size, size_t source_shift, size_t destination_shift) {
  static std::vector<uint8_t> expected, actual, production;
  const size_t total = kGuard + destination_shift + size + kGuard;
  expected.assign(total, kGuardByte);
  actual.assign(total, kGuardByte);
  production.assign(total, kGuardByte);
  CHECK(source_shift + size <= g_source.size());
  const uint8_t* source = g_source.data() + source_shift;
  const size_t at = kGuard + destination_shift;
  agent5_reference::ByteSwapElements(expected.data() + at, source, size, element_size);
  legodimensions::gpu_native::SwapUploadElementBytes(actual.data() + at, source, size, element_size);
  agent5_production::ByteSwapElements(production.data() + at, source, size, element_size);
  for (const std::vector<uint8_t>* candidate : {&actual, &production}) {
    if (*candidate == expected) continue;
    size_t i = 0;
    while ((*candidate)[i] == expected[i]) ++i;
    std::fprintf(stderr,
                 "%s mismatch: size=%zu element_size=%u src+%zu dst+%zu at byte %td: got %02X want %02X\n",
                 candidate == &actual ? "SwapUploadElementBytes" : "buffers.cpp ByteSwapElements", size,
                 element_size, source_shift, destination_shift, ptrdiff_t(i) - ptrdiff_t(at),
                 (*candidate)[i], expected[i]);
    CHECK(*candidate == expected);
  }
  ++g_cases;
}
}  // namespace

int main() {
  std::mt19937_64 rng(0x5EED0003);
  g_source.resize((size_t(1) << 20) + 4096);
  for (auto& b : g_source) b = uint8_t(rng());
  const uint32_t element_sizes[] = {0, 1, 2, 3, 4, 8, 16};
  // Every split between the 32/16-byte SIMD loops, the scalar remainder and the tail.
  for (uint32_t element_size : element_sizes)
    for (size_t size = 0; size <= 300; ++size)
      for (size_t s = 0; s < 16; ++s)
        for (size_t d = 0; d < 16; ++d) Compare(size, element_size, s, d);
  // Around larger boundaries.
  for (uint32_t element_size : {2u, 4u, 0u})
    for (size_t base : {size_t(4096), size_t(65536), size_t(1) << 20})
      for (size_t delta = 0; delta <= 70; ++delta)
        for (size_t s : {size_t(0), size_t(5)}) {
          Compare(base - delta, element_size, s, (s * 3) & 15);
          Compare(base + delta, element_size, s, 7);
        }
  // Random large cases.
  for (int i = 0; i < 400; ++i) {
    const size_t s = rng() % 64, d = rng() % 64;
    const size_t size = rng() % (g_source.size() - 64);
    Compare(size, element_sizes[rng() % 7], s, d);
  }
  std::printf("PASS %u byte-swap cases: SwapUploadElementBytes and the buffers.cpp ByteSwapElements body equal "
              "the old scalar loop, no out-of-range writes (path=%s)\n",
              g_cases,
#if defined(__AVX2__)
              "AVX2+SSSE3"
#elif defined(__SSSE3__)
              "SSSE3"
#else
              "scalar"
#endif
  );
  CHECK(g_cases > 500000);
  return 0;
}
