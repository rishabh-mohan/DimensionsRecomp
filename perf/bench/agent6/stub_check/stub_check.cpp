// Agent 6, J1(a): checks that the native-GPU STUB banks/caches compile in the same
// context as their consumers, link (blob symbols from the stub .obj files), and that
// the archive decoders used by shader_archive.cpp accept the empty archives.
// Build/run: powershell -File bench/agent6/stub_check/run_stub_check.ps1
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <iterator>
#include <memory>
#include <tuple>

#define MINIZ_HEADER_FILE_ONLY  // as shader_archive.cpp; the implementation comes from miniz.cpp
#include <miniz.h>
#include <zstd.h>

#include "gpu_native/linked_shader_cache.h"
#include "gpu_native/shader_archive.h"

namespace legodimensions::gpu_native {
namespace {
// Same struct/lookup as temporal_shaders.cpp.
struct TemporalShaderEntry {uint64_t hash;uint32_t stage,spec,offset,size,camera;};
#include LEGO_TEMPORAL_SHADER_METADATA
extern "C" const unsigned char g_temporalShaderBlob[];
using TKey = std::tuple<uint64_t, uint32_t, uint32_t>;
const TemporalShaderEntry* FindTemporal(TKey key) {
  auto found = std::lower_bound(std::begin(g_temporal_entries), std::end(g_temporal_entries), key,
      [](const auto& entry, const auto& value) { return TKey{entry.hash, entry.stage, entry.spec} < value; });
  return found != std::end(g_temporal_entries) && TKey{found->hash, found->stage, found->spec} == key ? found : nullptr;
}
// Same struct/lookup as float_blend_indices.cpp.
struct FloatBlendIndicesEntry { uint64_t hash; uint32_t spec, offset, size, kind; };
#include LEGO_FLOAT_BLEND_INDICES_METADATA
extern "C" const unsigned char g_floatBlendIndicesBlob[];
const FloatBlendIndicesEntry* FindFloat(TKey key) {
  const auto found = std::lower_bound(std::begin(g_float_blend_indices_entries),
      std::end(g_float_blend_indices_entries), key,
      [](const auto& entry, const auto& value) { return TKey{entry.hash, entry.spec, entry.kind} < value; });
  return found != std::end(g_float_blend_indices_entries) &&
      TKey{found->hash, found->spec, found->kind} == key ? found : nullptr;
}
}  // namespace
}  // namespace legodimensions::gpu_native

namespace {
int g_failures = 0;
void Expect(bool ok, const char* what) {
  std::printf("%s %s\n", ok ? "PASS" : "FAIL", what);
  if (!ok) ++g_failures;
}
// Mirrors shader_archive.cpp BaseDxilArchive.
bool InflateBase(const uint8_t* src, size_t src_size, size_t dst_size) {
  auto data = std::make_unique<uint8_t[]>(dst_size);
  const size_t result = ZSTD_decompress(data.get(), dst_size, src, src_size);
  return !ZSTD_isError(result) && result == dst_size && data;
}
// Mirrors shader_archive.cpp LinkedDxilArchive.
bool InflateLinked(const uint8_t* src, size_t src_size, size_t dst_size) {
  auto data = std::make_unique<uint8_t[]>(dst_size);
  mz_ulong size = static_cast<mz_ulong>(dst_size);
  const int result = mz_uncompress(data.get(), &size, src, static_cast<mz_ulong>(src_size));
  return result == MZ_OK && size == dst_size;
}
}  // namespace

int main() {
  using namespace legodimensions::gpu_native;
  const uint64_t hashes[] = {0, 1, 0x4DE8C1F0EFCC722Eull, ~0ull};
  bool temporal_miss = true, float_miss = true;
  for (uint64_t h : hashes)
    for (uint32_t stage = 0; stage < 8; ++stage)
      for (uint32_t spec = 0; spec < 4; ++spec) {
        temporal_miss &= FindTemporal({h, stage, spec}) == nullptr;
        float_miss &= FindFloat({h, spec & 1u, stage & 1u}) == nullptr;
      }
  Expect(temporal_miss, "temporal stub: every lookup misses");
  Expect(float_miss, "float-blend-indices stub: every lookup misses");
  Expect(g_temporalShaderBlob[0] == 0 && g_floatBlendIndicesBlob[0] == 0, "bank blob symbols link from stub .obj");

  Expect(g_shaderCacheEntryCount == 0 && g_runtimeShaderCacheEntryCount == 0, "dxil caches: 0 entries");
  Expect(g_shaderMicrocodeEntryCount == 0, "microcode index: 0 records");
  Expect(g_linkedShaderCacheEntryCount == 0 && g_runtimeLinkedShaderCacheEntryCount == 0, "linked caches: 0 variants");
  Expect(InflateBase(g_compressedDxilCache, g_dxilCacheCompressedSize, g_dxilCacheDecompressedSize),
         "main dxil archive inflates (zstd)");
  Expect(InflateBase(g_runtimeCompressedDxilCache, g_runtimeDxilCacheCompressedSize, g_runtimeDxilCacheDecompressedSize),
         "runtime dxil archive inflates (zstd)");
  Expect(InflateLinked(g_compressedLinkedDxilCache, g_linkedDxilCacheCompressedSize, g_linkedDxilCacheDecompressedSize),
         "main linked archive inflates (miniz)");
  Expect(InflateLinked(g_runtimeCompressedLinkedDxilCache, g_runtimeLinkedDxilCacheCompressedSize,
                       g_runtimeLinkedDxilCacheDecompressedSize),
         "runtime linked archive inflates (miniz)");
  std::printf("%s\n", g_failures ? "STUB CHECK FAILED" : "STUB CHECK OK");
  return g_failures ? 1 : 0;
}
