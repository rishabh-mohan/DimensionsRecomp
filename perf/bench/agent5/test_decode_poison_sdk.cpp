// Agent 5 item 2: the production texture decode loop, extracted from textures.cpp by
// test_decode_poison_sdk.py exactly as tools/gpu-aot/test_texture_upload_retention_sdk.py does,
// must give identical bytes whether its decode buffer starts zero-filled (the old
// std::vector<u8> decoded(upload_size)) or poisoned (the uninitialised TextureDecodeScratch).
// Real SDK layouts and guest memory, as in the retention fixture; several odd sizes/mip counts.
#define NOMINMAX
#define XXH_INLINE_ALL
#include "gpu_native/d3d.h"
#include "gpu_native/texture_upload_cache.h"
#include "gpu_native/texture_upload_source.h"
#include "gpu_native/texture_volume_upload.h"
#include "gpu_native/texture_alpha4_upload.h"
#include "plume_render_interface_types.h"
#include <rex/graphics/pipeline/texture/util.h>
#include <rex/system/xmemory.h>
#include <rex/math.h>
#include <windows.h>
#include <algorithm>
#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <vector>
using namespace legodimensions::gpu_native;
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"line %d: %s\n",__LINE__,#x);std::exit(23);}}while(0)
rex::memory::Memory* memory_pointer;
#define REX_KERNEL_MEMORY() memory_pointer
constexpr u32 kPitchAlignment = 256;
struct TextureResource {
  u32 width = 32, height = 16, depth = 1, levels = 3, d3d_type = 3;
  plume::RenderFormat format = plume::RenderFormat::R8G8B8A8_UNORM;
};
bool IsBlockCompressedFormat(plume::RenderFormat);
u32 FormatBlockBytes(plume::RenderFormat);
#include "retained-helpers.inc"
using Fetch = rex::graphics::xenos::xe_gpu_texture_fetch_t;

bool Decode(const std::shared_ptr<TextureResource>& resource, const Fetch& fetch,
            const std::optional<TextureUploadSource>& retained, std::vector<u8>& decoded, u8 fill) {
  namespace tu = rex::graphics::texture_util;
  using rex::graphics::xenos::DataDimension;
  const bool cube = fetch.dimension == DataDimension::kCube, volume = fetch.dimension == DataDimension::k3D;
  const u32 faces = cube ? 6 : 1;
  const auto* format_info = rex::graphics::FormatInfo::Get(fetch.format);
  const bool alpha4 = fetch.format == rex::graphics::xenos::TextureFormat::k_DXT3A;
  const u32 block_bytes = alpha4 ? 8 : plume::RenderFormatSize(resource->format);
  const u32 block_width = alpha4 ? 4 : plume::RenderFormatBlockWidth(resource->format);
  const auto layout = tu::GetGuestTextureLayout(fetch.dimension, fetch.pitch, resource->width, resource->height,
      volume ? resource->depth : 1, fetch.tiled, fetch.format, fetch.packed_mips, true, resource->levels - 1);
  const u32 endian_xor = TextureEndianXor(u32(fetch.endianness));
  u32 upload_size = 0;
  for (u32 face = 0; face < faces; ++face)
    for (u32 level = 0; level < resource->levels; ++level)
      upload_size = AlignUp(upload_size, 512) + LevelSize(*resource, level);
  decoded.assign(upload_size, fill);
  auto* mapped = decoded.data();
#include "retained-decode.inc"
  return true;
}

u32 Physical(u32 address) {
  return address < 0x20000000u ? address : REX_KERNEL_MEMORY()->GetPhysicalAddress(address);
}
void Fill(u32 address, u32 bytes, u8 seed) {
  auto* p = REX_KERNEL_MEMORY()->TranslatePhysical<u8*>(Physical(address));
  for (u32 i = 0; i < bytes; ++i) p[i] = u8(seed + (i * 37) ^ (i >> 4));
}

int main() {
  SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
  rex::memory::Memory memory;
  CHECK(memory.Initialize());
  memory_pointer = &memory;
  CHECK(memory.LookupHeap(0xC0000000)->Protect(0xC0020000, 0x100000,
      rex::memory::kMemoryProtectRead | rex::memory::kMemoryProtectWrite));
  CHECK(memory.LookupHeap(0xC0000000)->AllocFixed(0xD0000000, 0x1000000, 0x1000000,
      rex::memory::kMemoryAllocationReserve | rex::memory::kMemoryAllocationCommit,
      rex::memory::kMemoryProtectRead | rex::memory::kMemoryProtectWrite));
  using TF = rex::graphics::xenos::TextureFormat;
  using RF = plume::RenderFormat;
  using DD = rex::graphics::xenos::DataDimension;
  const std::array formats{std::pair(TF::k_8_8_8_8, RF::R8G8B8A8_UNORM), std::pair(TF::k_16_FLOAT, RF::R16_FLOAT),
      std::pair(TF::k_32_32_32_32_FLOAT, RF::R32G32B32A32_FLOAT), std::pair(TF::k_DXT1, RF::BC1_UNORM),
      std::pair(TF::k_DXT4_5, RF::BC3_UNORM), std::pair(TF::k_DXT3A, RF::R8_UNORM),
      std::pair(TF::k_8, RF::R8_UNORM), std::pair(TF::k_8_8, RF::R8G8_UNORM)};
  struct Size { u32 width, height, depth, levels; };
  const std::array sizes{Size{32, 16, 4, 3}, Size{17, 9, 3, 4}, Size{40, 24, 2, 3}, Size{8, 8, 5, 4},
                         Size{64, 32, 2, 2}, Size{5, 3, 1, 3}, Size{100, 4, 1, 1}};
  unsigned tested = 0, skipped = 0, padded = 0;
  for (const Size& size : sizes)
  for (auto [guest_format, host_format] : formats)
  for (auto dimension : {DD::k2DOrStacked, DD::kCube, DD::k3D})
  for (bool tiled : {false, true}) for (bool packed : {false, true}) for (u32 endian = 0; endian < 4; ++endian)
  for (u32 address : {0x20000u, 0xA0020000u, 0xC0020000u, 0xE001F000u, 0xF001F000u}) {
    auto resource = std::make_shared<TextureResource>();
    resource->width = size.width; resource->height = size.height; resource->levels = size.levels;
    resource->format = host_format;
    resource->d3d_type = dimension == DD::kCube ? 18 : dimension == DD::k3D ? 17 : 3;
    resource->depth = dimension == DD::k3D ? size.depth : 1;
    Fetch fetch{};
    fetch.dimension = dimension; fetch.format = guest_format; fetch.tiled = tiled; fetch.packed_mips = packed;
    fetch.pitch = (size.width + 31) / 32 + (size.width & 1);
    fetch.endianness = decltype(fetch.endianness)(endian);
    fetch.base_address = address >> 12; fetch.mip_address = (address + 0x60000) >> 12;
    const auto layout = rex::graphics::texture_util::GetGuestTextureLayout(dimension, fetch.pitch,
        resource->width, resource->height, resource->depth, tiled, guest_format, packed, true, size.levels - 1);
    const auto base_size = TextureEndianExtent(layout.base.level_data_extent_bytes, TextureEndianXor(endian));
    const auto mip_size = size.levels > 1
        ? TextureEndianExtent(layout.mips_total_extent_bytes, TextureEndianXor(endian)) : 0u;
    if (!base_size || base_size > 0x60000 || mip_size > 0x40000 || (size.levels > 1 && !mip_size)) { ++skipped; continue; }
    Fill(address, base_size, u8(0x12 + tested));
    if (mip_size) Fill(address + 0x60000, mip_size, u8(0x34 + tested));
    const auto retained = TextureUploadSource::Capture(address, base_size, address + 0x60000, mip_size,
                                                       CopyTextureUploadSpan);
    if (!retained) { ++skipped; continue; }
    std::vector<u8> zeroed, poisoned;
    if (!Decode(resource, fetch, retained, zeroed, 0)) { ++skipped; continue; }
    for (u8 poison : {u8(0xCD), u8(0x5A), u8(0xFF)}) {
      CHECK(Decode(resource, fetch, retained, poisoned, poison));
      if (poisoned != zeroed) {
        size_t at = 0;
        while (poisoned[at] == zeroed[at]) ++at;
        std::fprintf(stderr, "mismatch at byte %zu of %zu: %ux%u levels=%u format=%u dim=%u tiled=%u packed=%u "
            "endian=%u address=%08X poison=%02X\n", at, zeroed.size(), size.width, size.height, size.levels,
            u32(guest_format), u32(dimension), tiled, packed, endian, address, poison);
        CHECK(poisoned == zeroed);
      }
    }
    padded += std::count(zeroed.begin(), zeroed.end(), u8(0)) != 0;
    ++tested;
  }
  std::printf("PASS %u decode cases (%u with zero bytes, %u skipped): poisoned and zero-filled decode buffers "
              "give identical bytes through the production textures.cpp loop.\n", tested, padded, skipped);
  CHECK(tested > 1000);
  return 0;
}
