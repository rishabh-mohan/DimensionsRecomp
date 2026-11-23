# Agent 6 / subagent B: FidelityFX FSR3 static libs (DX12 backend and FSR3 upscaler)

All paths are relative to the workspace root `<workspace>`.
Each command runs in a fresh PowerShell session. Build commands start with `. .\env\devshell.ps1 -Jobs 1`.

## 0. Inputs and findings (read-only inspection)

- FFX SDK checkout: `DimensionsRecomp/rexglue-sdk/thirdparty/FidelityFX-SDK` at eee08db1688ac3d1275a70b728f4a8ba22914213 ("Linux fix"). `git status` is clean. Treated as READ-ONLY because it is owned by Agent 2.
- Game consumer: `DimensionsRecomp/rexlego/CMakeLists.txt`
  - Line 236 sets `LEGO_FSR3_SDK = ${CMAKE_CURRENT_SOURCE_DIR}/../rexglue-sdk`.
  - Lines 239-241 link `${LEGO_FSR3_SDK}/bin/ffx_sdk/ffx_backend_dx12_x64.lib` and `ffx_fsr3upscaler_x64.lib`. The staging target is therefore `DimensionsRecomp/rexglue-sdk/bin/ffx_sdk/`, which is git-ignored by `.gitignore:38 **/[Bb]in/*`.
  - Lines 242-248 run `find_file(LEGO_NATIVE_FIDELITYFX_RUNTIME amd_fidelityfx_dx12.dll HINTS ${rexglue_DIR}/../../../bin ${LEGO_FSR3_SDK}/bin ../../runtime NO_DEFAULT_PATH)`. This lookup is fatal if the file is not found and the variable is not set.
- API used by the game (`rexlego/src/gpu_native/fsr3_upscaler.cpp`): the native FFX 1.1 host API with the DX12 backend only. It does not use ffx-api. It calls:
  - ffxGetScratchMemorySizeDX12
  - ffxGetInterfaceDX12
  - ffxGetDeviceDX12
  - ffxGetResourceDX12
  - ffxGetResourceDescriptionDX12
  - ffxGetCommandListDX12
  - ffxFsr3UpscalerContextCreate, ffxFsr3UpscalerContextDispatch, ffxFsr3UpscalerContextDestroy
  - ffxFsr3UpscalerGetSharedResourceDescriptions
  - ffxFsr3UpscalerGetJitterPhaseCount, ffxFsr3UpscalerGetJitterOffset
- Game compile settings (`build/baseline/build.ninja`, Release, Ninja):
  - Compiler: llvm-23.1.6 `clang++`, the GNU driver with MSVC ABI (not clang-cl). Link with lld-link, archive with llvm-ar.
  - Flags: `-O3 -DNDEBUG -std=gnu++23 -D_DLL -D_MT -Xclang --dependent-lib=msvcrt -msse4.1 -march=x86-64-v3 -DNOMINMAX -DWIN32_LEAN_AND_MEAN ...`
  - CRT: no MSVC_RUNTIME_LIBRARY is set anywhere, so CMake's default MultiThreadedDLL (/MD) applies, with _ITERATOR_DEBUG_LEVEL=0 in Release.
- The FFX CMake writes into its own source tree:
  - `CMAKE_ARCHIVE_OUTPUT_DIRECTORY_* = ${CMAKE_HOME_DIRECTORY}/bin/ffx_sdk`
  - `FFX_BIN_PATH = sdk/bin/ffx_sdk` (a WinPixEventRuntime.dll copy is made at build time)
  - So the build runs from a COPY of `sdk/` under `build/agent6/ffx/src/sdk`, driven by a wrapper project (`build/agent6/ffx/src/wrapper`).

## 1. Disk estimate

- Size of `sdk/`: 864 files, 179,234,343 bytes. Of that, `tools/` is 160.9 MB (binary_store with FidelityFX_SC.exe and DXC, plus ffx_shader_compiler libs).
- Free space on C: about 280 GB.
- Expected total: about 180 MB for the copy plus a build tree of roughly 0.5 GB or less. This is far below the 5 GB limit.


## Takeover by Agent 6 (19:23)

- Subagent B had been stuck since 18:33, waiting for approval of a command ('Game link rule inspection'). Agent 6 killed it at 19:23. Phase 1 (shader permutations) had already finished at 18:40:36: rc 0, 520 s wall, 169.7 CPU-s.
- Phase 2 (Agent 6): cmake --build build/agent6/ffx/build-release -j 1 --target ffx_backend_dx12_x64 ffx_fsr3upscaler_x64. Result: rc 0, 65 s wall, 35.7 CPU-s (log build-phase2-libs.log). Flags: -march=x86-64-v2 -O3 -DNDEBUG -std=gnu++17 -D_DLL -D_MT -Xclang --dependent-lib=msvcrt (/MD CRT, IDL 0).
- Staged in DimensionsRecomp/rexglue-sdk/bin/ffx_sdk/:
  - ffx_backend_dx12_x64.lib: 2,994,184 B, sha256 6465B950...F260D4
  - ffx_fsr3upscaler_x64.lib: 97,734 B, sha256 348E6113...B05D67
  amd_fidelityfx_dx12.dll is NOT copied; use -DLEGO_NATIVE_FIDELITYFX_RUNTIME.
- Link check: build/agent6/ffx/linkcheck/run_linkcheck.ps1 -Device builds with the game's flags (gnu++23, x86-64-v3, /MD) and links with lld-link. Result: PASS. All 12 entry points resolved; jitter 32 phases; FSR3 context create/shared-resources/destroy rc 0 on the real device; context create took 1403 ms (it builds every FSR3 PSO). Output: linkcheck/linkcheck.txt.
