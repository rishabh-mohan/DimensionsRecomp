#pragma once

#include <cstdlib>

namespace legodimensions::gpu_native {

// In-game A/B switch for the session-2 upload changes. Default OFF.
// LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD=1 (any value not starting with '0')
// restores the previous paths in the same binary: the per-block untile of 2D
// and cube slices (CopyTextureVolumeBlocks), zero-filled texture decode and
// capture buffers and vertex conversion buffers, and the scalar element byte
// swap. The uploaded bytes are the same in both modes; only the CPU cost
// differs. Read once per process.
inline bool LegacyUploadPathsEnabled() {
  static const bool enabled = [] {
#if defined(__clang__)
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
#elif defined(_MSC_VER)
#pragma warning(push)
#pragma warning(disable : 4996)
#endif
    const char* value = std::getenv("LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD");
#if defined(__clang__)
#pragma clang diagnostic pop
#elif defined(_MSC_VER)
#pragma warning(pop)
#endif
    return value && value[0] && value[0] != '0';
  }();
  return enabled;
}

}  // namespace legodimensions::gpu_native
