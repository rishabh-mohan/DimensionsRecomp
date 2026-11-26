# Building the SDK with FidelityFX: feasibility (Task 3.1, plan only)

Read-only. SDK = `DimensionsRecomp/rexglue-sdk` @ `a7e79c0`. Superproject = `DimensionsRecomp` @ `a8e8dc8`. Paths are commit-relative unless they are prefixed `WS\`.

## 1. Submodule state

### `.gitmodules` (a7e79c0)
- It lists 24 submodules.
- **There is no entry for `thirdparty/FidelityFX-SDK`, and none for `thirdparty/snapdragon-gsr`.**

### `git ls-tree a7e79c0 thirdparty/` (the relevant lines)
```
160000 commit eee08db1688ac3d1275a70b728f4a8ba22914213	thirdparty/FidelityFX-SDK
160000 commit d926f074bcb9d714e179f1ce0fcb9ee2eeb5074e	thirdparty/snapdragon-gsr
```
- Both are orphan gitlinks.
- `git submodule status` fails with `fatal: no submodule mapping found in .gitmodules for path 'thirdparty/FidelityFX-SDK'`.

### History
- `efcdbc5` (2026-03-18, "deps(ffx): make AMD FidelityFX submodule opt-in") removed `[submodule "thirdparty/FidelityFX"] url = https://github.com/rexglue/FidelityFX-SDK.git`. FFX moved to FetchContent at that point.
- `7bdae77` (2026-09-04, "Baseline before the in-game toypad UI") added the `FidelityFX-SDK` and `snapdragon-gsr` gitlinks without any `.gitmodules` entries. Most likely a `git add` of populated directories.

### Upstream URL
- `cmake/rexglue_fidelityfx.cmake:50-55`: `FetchContent_Declare(... GIT_REPOSITORY https://github.com/rexglue/FidelityFX-SDK.git GIT_TAG eee08db… GIT_SHALLOW OFF)`. This is the **same sha as the gitlink**.
- The snapdragon-gsr URL cannot be inferred from the repo.

### Working tree
`rexglue-sdk/thirdparty/FidelityFX-SDK` **is populated**:
- HEAD is `eee08db` ("Linux fix"), origin is rexglue/FidelityFX-SDK.git.
- It contains `sdk/include`, `ffx-api/include`, and `PrebuiltSignedDLL/`. The prebuilt files are `amd_fidelityfx_dx12.dll` (6,675,664 B), the matching .lib (2,760 B) and the vk DLL (9,332,432 B).
- `LICENSE.txt` is MIT-style (AMD 2024, "Permission is hereby granted, free of charge…").

### Optional `.gitmodules` fix
Not needed for the build: CMake uses FetchContent or `REXGLUE_FIDELITYFX_SOURCE_DIR`.
```
[submodule "thirdparty/FidelityFX-SDK"]
	path = thirdparty/FidelityFX-SDK
	url = https://github.com/rexglue/FidelityFX-SDK.git
```
snapdragon-gsr would need the same kind of entry, but its URL is unknown.

## 2. The parked native3ffx work (earlier notes)
- `WS\perf-notes\agent7-s3-proposal.md`
  - `:3`: S3 shipped option (a), `fix-a.patch`: native settings read their catalog defaults when a cvar is unregistered. Option (b), "FFX headers on rexui", was **parked**.
  - `:28` gives the plan, and `:76-167` the detailed build plan:
    - configure `:86-91`
    - why not ENABLE=ON `:106-112`
    - rebuild scope `:114-124`
    - timing `:126-135`
    - staging as `build\agent2\ffx3-rt` → `native3ffx-bin` = native3-bin with `rexruntime.dll`/pdb swapped, with an automatic revert via `-UREXGLUE_FIDELITYFX_SOURCE_DIR` in build-snap.ps1 (`:137-157`)
    - risks `:159-167`
- `WS\perf-notes\FINDINGS-AND-CHANGES.md:263`: "(b), parked for later … formally an ODR violation, Agent 10 noted 2 hazards".
- `WS\perf-notes\RESTART-PROMPT-S3.md:284`: parked for S4.
- `WS\perf-notes\agent1-tracker-s2.md`:
  - `:250`: the original motivation was a native crash, "Native setting is not registered: present_fsr_sharpness_reduction", with FFX OFF.
  - `:292`: ODR concern. The `d3d12_presenter.h:135/151` root-signature array count changes from 1 to 5.
  - See also `:321`.
- `WS\perf-notes\agent7-odr-ffx.md` (layout check, `:28-35`, `:121-134`) and `WS\perf-notes\agent10-batch2-review.md` (`:25` AGREE; hazards at `:468-475` and `:488-490`):
  - hazard (6): COMDAT copy selection
  - hazard (7): LTO
- **Never built.** Neither `WS\build\agent2\ffx3-rt` nor `WS\build\agent2\native3ffx-bin` exists.
- `WS\build\agent6\ffx\LOG-B.md` is a separate, completed effort. It built the *native* static libs (FFX 1.1 DX12 backend + FSR3 upscaler) from a copy of `sdk/`:
  - phase 1 (shaders) took 520 s wall; phase 2 (libs) took 65 s at -j1
  - the libs were staged into `rexglue-sdk/bin/ffx_sdk/` (gitignored by `.gitignore:38 **/[Bb]in/*`)
  - linkcheck PASS
  - `sdk/` is 179 MB, of which `tools/` is 160.9 MB (FidelityFX_SC.exe + DXC)

## 3. What enables it, and what it links or copies

| Knob | Effect |
|---|---|
| `CMakeLists.txt:23` `option(REXGLUE_ENABLE_FIDELITYFX … OFF)` (and `:49-53`, status `:315`); `thirdparty/CMakeLists.txt:228-230` includes `cmake/rexglue_fidelityfx.cmake` | Full integration (see below) |
| `REXGLUE_FIDELITYFX_SOURCE_DIR` (CACHE INTERNAL, set at `rexglue_fidelityfx.cmake:61-62`; can be passed with `-D`) | `src/ui/CMakeLists.txt:122-128` → `REX_HAS_FIDELITYFX_SDK=1` + FFX include dirs, **PRIVATE to `rexui` only** |
| `amd_fidelityfx_dx12`/`_vk` targets exist (ENABLE=ON only) | `src/ui/CMakeLists.txt:130-141` → rexui links the target PRIVATE + `REX_HAS_FIDELITYFX_RUNTIME` |

### What `REXGLUE_ENABLE_FIDELITYFX=ON` does (`cmake/rexglue_fidelityfx.cmake`)
- `:7-9`: returns immediately if OFF.
- `:12-46`: off Windows, it requires Vulkan SDK ≥1.3.250 and glslc.
- `:50-55`: FetchContent full clone (not shallow). Set `FETCHCONTENT_SOURCE_DIR_FIDELITYFX=<populated tree>` to skip the download.
- `:65-99`: on WIN32 with D3D12, the backend auto-resolves to dx12.
- `:107-112`: `FFX_API_ENABLE_FRAMEGEN_PROVIDER OFF`, `FFX_API_AUTO_COMPILE_SHADERS ON` on WIN32, so it compiles shaders through FidelityFX_SC/DXC at build time.
- `:113`: `add_subdirectory(ffx-api … EXCLUDE_FROM_ALL)`.
- `:130-133`: clears `CMAKE_GENERATOR_PLATFORM`.
- `cmake/rexglue_helpers.cmake:130-143`: a POST_BUILD step copies the **self-built** `amd_fidelityfx_dx12.dll` next to the game exe.
- `/DELAYLOAD` (`src/rexglue/CMakeLists.txt:29-42`) is attached to the `rexglue` codegen executable (`:44`). I found no matching delay-load for `rexruntime` (SHARED, `src/system/CMakeLists.txt:51`), which pulls in rexui through `src/kernel/CMakeLists.txt:69`. So under ENABLE=ON, rexruntime.dll *may* hard-import the DLL. **Not verified.** `agent7-s3-proposal.md:109` assumes delay-load.

### The native path already has its own, separate FFX integration
- `rexlego/CMakeLists.txt:256-274`: static FFX 1.1 libs from `rexglue-sdk/bin/ffx_sdk`, plus `thirdparty/FidelityFX-SDK/sdk/include`.
- `fsr3_upscaler.cpp:11-12,98-185`: the FSR3 upscaler built on those libs.
- `fsr1_present.h:16-19`: its own FSR1 presenter, using the SDK's precompiled EASU/RCAS bytecode headers.
- `amd_fidelityfx_dx12.dll` is only POST_BUILD-copied (`:271-274`). It is neither imported nor delay-loaded (PE check in `fsr-fallback.md` §b).
- **Native needs only option A** (below), so that `present_effect="fsr"` is accepted and the `present_fsr_*` cvars exist. It does not need the SDK runtime.

## 4. Options

| | A: headers only (the parked "(b)") | B: `REXGLUE_ENABLE_FIDELITYFX=ON` |
|---|---|---|
| Configure flag | `-DREXGLUE_FIDELITYFX_SOURCE_DIR=<snap1>/rexglue-sdk/thirdparty/FidelityFX-SDK` | `-DREXGLUE_ENABLE_FIDELITYFX=ON [-DFETCHCONTENT_SOURCE_DIR_FIDELITYFX=…]` |
| Defines | `REX_HAS_FIDELITYFX_SDK` | `_SDK` + `_RUNTIME` |
| Unlocks | Xenos cas/fsr (spatial, precompiled shaders), the `present_fsr_*`/`cas` cvars, native FSR1 via `present_effect=fsr` | + fsr2/fsr3 temporal via ffx-api (`presenter.cpp` ~230-237 falls back to a fixed ratio without RUNTIME) |
| New binaries | none | ffx-api `amd_fidelityfx_dx12.dll` (self-built, unsigned), POST_BUILD-copied over the signed prebuilt |
| Rebuild | rexui 35 TUs + PCH, rexruntime.dll relink | the same + ffx-api build + shader autocompile (not measured) |

## 5. Risks
- **ODR/layout (both options).** `include/rex/ui/presenter.h` changes layout under the define. The `presenter.h:276-302,317-322` members and the `d3d12_presenter.h` root-signature array (1→5) are seen by TUs outside rexui:
  - `include/rex/graphics/command_processor.h`, `graphics_system.h`, `ui/window.h`
  - `src/graphics/d3d12/command_processor.cpp` (rexgpu-xenos)

  Those TUs compile without the define. This is formally IFNDR. `agent7-odr-ffx.md` checked it clean in practice (only rexui touches the moved members). The open hazards are (6) COMDAT copy selection and (7) LTO (`agent10-batch2-review.md:468-490`). The cleanest fix is to make the define PUBLIC/global, but that forces a broad rebuild.
- **DLL versioning (B).**
  - The self-built ffx-api DLL would overwrite the AMD-signed `12A5081257EC95B0` that native ships.
  - The native exe doesn't import it today, so nothing breaks right away. But two producers would write one filename.
  - A hard import from rexruntime.dll would make a missing DLL fatal at load time.
  - Check the export set and the import or delay-load status with a PE dump after the build.
- **Shader compiler (B, or rebuilding the native libs).** On Windows, FidelityFX_SC.exe + DXC from `sdk/tools` (160.9 MB). Off Windows, glslc + Vulkan SDK ≥1.3.250 (`rexglue_fidelityfx.cmake:12-46`). Option A needs neither, because the bytecode is pre-generated in the SDK under `src/ui/shaders/bytecode/`.
- **License.** FidelityFX SDK is MIT-style (`thirdparty/FidelityFX-SDK/LICENSE.txt`). Redistribution needs the notice.
- **Binary size.** A: a few KB of extra code and shaders in rexruntime.dll (estimate). B: +6.7 MB DLL. On disk, a full clone plus tools is about 180 MB+.
- **Rebuild scope.** The define is per target (rexui PRIVATE), **not global**, so there is no full SDK rebuild. But any reconfigure regenerates `rex/version.h` (timestamp; `agent7-s3-proposal.md:122-124`), which can dirty more TUs. A fresh configure measured 235.5 s (`:126-135`).
- **Untested compile.** The `#if REX_HAS_FIDELITYFX_SDK` code at a7e79c0 has never been compiled in this tree.

## 6. Build-time estimate
- snap1-sdk compile_commands (Release config): **759 TUs**.
  - Per target: SDL3-static 261, rexruntime 95, libavutil 81, rexcore 42, rexcodegen 39, rexgpu-xenos 38, **rexui 36 (35 TUs + `cmake_pch.hxx.cxx`)**, rexfilesystem 16, …
  - The define touches **rexui only, about 4.7% of TUs**.
- Option A, from the earlier measurement (`agent7-s3-proposal.md:126-135`):
  - reconfigure 30-60 s
  - rexui ~35-40 s at -j10 (PCH 13.3 s + 266 CPU-s)
  - rexruntime link 10.8 s
  - **≈2-3 min total**, plus ≈1.5 min to revert
  - Compare: our single-TU flow did 10 TUs in ~20 s.
- Option B: A + the ffx-api/shader build. Not measured. The FFX 1.1 native static-lib build (a comparable workload) took 520 s for shaders + 65 s for libs (`build\agent6\ffx\LOG-B.md`), so budget **~10 min+**. Add FetchContent clone time unless `FETCHCONTENT_SOURCE_DIR_FIDELITYFX` points at the populated tree.

## 7. Concrete steps (option A recommended; B only if fsr2/fsr3 on Xenos is needed)
1. Pre-check:
   - `git -C <snap1>/DimensionsRecomp/rexglue-sdk/thirdparty/FidelityFX-SDK rev-parse HEAD` == `eee08db…`
   - `sdk/include` exists
2. Configure snap1-sdk in place:
   `cmake -S <snap1 sdk src> -B WS\build\agent2\snap1-sdk -DREXGLUE_FIDELITYFX_SOURCE_DIR=<…>/thirdparty/FidelityFX-SDK`
   Leave `REXGLUE_ENABLE_FIDELITYFX=OFF`.
3. Verify that compile_commands now shows `-DREX_HAS_FIDELITYFX_SDK=1` on exactly 36 rexui entries per config, and on nothing else.
4. `cmake --build … --config Release --target rexruntime`. Expect rexui (35 TUs + PCH) to rebuild and rexruntime.dll to relink. Note any extra TUs that version.h dirties.
5. Stage `build\agent2\ffx3-rt\rexruntime.dll/.pdb`, then `native3ffx-bin` = copy of the current native bin with only rexruntime swapped (`agent7-s3-proposal.md:137-157`). Check:
   - the export superset vs. the old rexruntime (for the exe and rexgpu-xenos imports)
   - the string `"present_fsr_sharpness_reduction"` is present
   - there is still no `amd_fidelityfx` import
6. Revert the cache with `-UREXGLUE_FIDELITYFX_SOURCE_DIR` and rebuild, so that the shipped snap1 stays bit-identical.
7. Smoke test, with the user's or Overseer's approval to launch:
   - Xenos with `present_effect='fsr'`: expect no "not in allowed values" warning (check with a debugger sink).
   - Native with `native_fsr3=false`: expect `spatial_fsr_presented>0` in frames.csv.
8. Option B only:
   - add `-DREXGLUE_ENABLE_FIDELITYFX=ON -DFETCHCONTENT_SOURCE_DIR_FIDELITYFX=<populated tree>`
   - build with `FidelityFX_SC` available
   - PE-check rexruntime.dll for a hard vs. delay import of `amd_fidelityfx_dx12.dll`
   - decide which DLL (signed prebuilt vs. self-built) ships, and stop the two POST_BUILD copies (`rexglue_helpers.cmake:130-143`, `rexlego/CMakeLists.txt:271-274`) from fighting over it
9. Optional: add the `.gitmodules` entry from §1 for FidelityFX-SDK, and resolve or remove the snapdragon-gsr gitlink.

## Could not determine
- Whether rexruntime.dll would hard-import or delay-load `amd_fidelityfx_dx12.dll` under ENABLE=ON.
- The ffx-api plus shader-autocompile build time.
- Whether the FFX `#if` branch compiles cleanly at a7e79c0.
- The snapdragon-gsr upstream URL.
