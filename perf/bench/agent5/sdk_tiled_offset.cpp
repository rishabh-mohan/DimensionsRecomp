// Out-of-line rex::graphics::texture_util::GetTiledOffset2D/3D. build.ps1
// extracts the bodies verbatim from rexglue-sdk/src/graphics/pipeline/texture/
// util.cpp into gen/sdk_tiled_offset.inc. Separate TU and no LTO, as in the
// game (ThinLTO off: the SDK function is an out-of-line call there too).
#include <cstdint>

namespace rex {
// rexglue-sdk include/rex/math.h
template <typename T>
constexpr T align(T value, T alignment) {
  return (value + alignment - 1) & ~(alignment - 1);
}
}  // namespace rex

namespace rex::graphics::xenos {
// rexglue-sdk include/rex/graphics/xenos.h
constexpr uint32_t kTextureTileWidthHeightLog2 = 5;
constexpr uint32_t kTextureTileWidthHeight = 1 << kTextureTileWidthHeightLog2;
}  // namespace rex::graphics::xenos

namespace rex::graphics::texture_util {
#include "sdk_tiled_offset.inc"
}  // namespace rex::graphics::texture_util
