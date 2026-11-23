# LOG-A: J1 part A (XenosRecomp chain -> base DXIL cache, microcode index, HLSL dumps, offline banks)

Subagent A of Agent 6. Started 2026-11-21 18:12 local (00:12Z).
All paths relative to the workspace root `<workspace>`
unless noted; `DR` = `DimensionsRecomp`.

Rules followed: writes only in DR/research/**, DR/rexlego/out/native-gpu/{aot,current-compiler,shader-assets}/**,
DR/out/build/lego-release/**, build/agent6/aot/**. Heavy work at 1 thread (ninja -j1 / CPU affinity mask 0x1
for tools with hard-coded thread pools). Game data read-only from game/disc and game/tu23.

## Step 0: inspection (18:12-18:16)

- Read perf-notes/SESSION2-jobs.md (J1), DR/tools/gpu-aot/COLLABORATION.md 195-350, README.md 270-350,
  prepare_native_compiler.py, prepare_alpha_candidate.py, prepare_viewport_candidate.py,
  prepare_gradients_candidate.py, generate_microcode_index.cpp, rexlego/CMakeLists.txt 170-560,
  build_temporal_shader_bank.py, build_float_blend_indices_bank.py, build_instanced_constants_bank.py,
  tools/gpu-shader-extract/{csproj,Program.cs,README.md}.
- DXC: recipe names "official DXC 1.9.2609" (COLLABORATION.md 257-262). GitHub release v1.9.2609
  ("DX Compiler Release for September 2026", 2026-09-29): asset dxc_2026_09_29.zip (32,287,592 bytes).
- gradient_compiler's generated CMakeLists (prepare_alpha_candidate.py lines 69-84) hard-codes:
  - DEP  = <checkout>/thirdparty  (smol-v/source, xxHash, zstd/lib, fmt/include, dxc-bin/inc, dxc-bin/lib/x64/dxcompiler.lib,
           dxc-bin/bin/x64/{dxcompiler,dxil}.dll)
  - BUILD = <checkout>/out/build/lego-release  -> thirdparty/xxHash/cmake_unofficial/xxhash.lib,
           thirdparty/zstd/build/cmake/lib/zstd_static.lib, thirdparty/fmt/fmt.lib, thirdparty/fmt/bin/fmt.dll
  NOTE: BUILD is under the *XenosRecomp checkout* (research/reblue/thirdparty/XenosRecomp/out/build/lego-release),
  not DR/out/build/lego-release.
- Bank scripts: build_temporal_shader_bank.py and build_float_blend_indices_bank.py hard-code
  ThreadPoolExecutor(max_workers=6); build_instanced_constants_bank.py has --jobs. Tools must not be edited,
  so the two fixed-pool scripts are run under a 1-CPU affinity mask (children inherit it).
- float-blend bank --source expects prepared `*-vs-0-input.hlsl` (spec already resolved to 0), which is exactly
  what build_temporal_shader_bank.py writes into its output dir.
