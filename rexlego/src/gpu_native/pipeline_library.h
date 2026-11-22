#pragma once

#include <cstddef>
#include <cstdint>

struct D3D12_GRAPHICS_PIPELINE_STATE_DESC;
struct ID3D12Device;
struct ID3D12PipelineState;

namespace plume { struct RenderDevice; struct RenderPipelineLayout; }

namespace legodimensions::gpu_native {

// Disk-backed ID3D12PipelineLibrary behind Plume's graphics pipeline cache
// hook. A pipeline the driver already compiled in an earlier session loads
// in well under a millisecond instead of being rebuilt on the render thread.
// LEGO_NATIVE_PSO_CACHE=0 disables it for A/B comparisons.
void StartPipelineLibrary(plume::RenderDevice* device);
// Prepares previously recorded graphics pipelines before the guest starts.
// LEGO_NATIVE_PSO_PREPARE_THREADS=<n> (default 1) runs the loads and compiles
// on n threads; results are still applied in recipe order.
void PreparePipelineLibrary(plume::RenderPipelineLayout* layout);
bool StartupPipelinePreparationEnabled();
// Auxiliary passes describe themselves at startup and have their own roots.
// Include the serialized root in their keys and keep them out of main-root recipes.
bool CreateAuxiliaryPipeline(ID3D12Device* device,
    const D3D12_GRAPHICS_PIPELINE_STATE_DESC& desc, const void* root_data,
    std::size_t root_size, ID3D12PipelineState** pipeline);
// Called once per present: saves new pipelines in the background after a
// quiet period, so an abrupt exit loses at most the latest few seconds.
void PipelineLibraryFrame();
// Final save. Unregisters the cache before the device goes away.
void StopPipelineLibrary();

struct PipelineLibraryStats {
  uint64_t hits = 0, misses = 0, stored = 0, saves = 0;
};
PipelineLibraryStats GetPipelineLibraryStats();
// Logs the PSO stats summary now. A no-op unless LEGO_NATIVE_PSO_STATS=1 (see
// pipeline_stats.h); creating <exe>/cache/pso-stats.now does the same.
void LogPipelineStats();

}  // namespace legodimensions::gpu_native
