# Agent 6: native AOT shader pipeline (task #12, job J1)

> **RESUME NOTE (22:28), task #26 (Plume Windows SDK compat patch, batch 2): DONE.** `@@done 26` was sent at about 22:28. Details are in section 8.
> - **Changes:** the new patch `tools/gpu-aot/patches/plume-winsdk-compat.patch` (sha256 `E03D29D0...47EF`), its entry in `prepare_plume.py`, and a new fixture in `test_prepare_plume.py`.
> - **Verified (8.4):**
>   - a scratch clone at the pin plus the 7 patches is byte-identical to the snapshot and live `plume_d3d12.cpp` (`564568D4...`);
>   - the test prints "PASS: 18 ...";
>   - the live `--check` passes;
>   - S1's six-patch preparer also passes on the p2 tree.
> - **Identifier scan (8.5):** nothing else that SDK 22621 lacks is compiled.
> - **Messages:** Agent 10 got the listing for #25 at about 22:20 and the results at about 22:28. Agent 1 confirmed Agent 2's live edit at 22:22.
> - **Re-run:** `$p=[Diagnostics.Process]::GetCurrentProcess(); $p.ProcessorAffinity=[IntPtr]0x20; $env:GIT_OPTIONAL_LOCKS='0'; & .\build\agent6\plume26\verify26.ps1` takes about 150 s on one CPU. Don't re-run `make_patch.ps1`: it refuses to overwrite the patch.

> **RESUME NOTE (20:31), task #12: DONE.**
> - **(a) DONE 18:13. (b) DONE 18:20. (d) DONE 20:00** (section 6). **(c) DONE 20:23**: every input is staged, including the optional instanced bank. Section 5 has the copy list with sizes and sha256, the exact `snap-native-inputs.py` commands (base `N1` and instanced add-on `N1i`) and the configure flags. Agent 2 got the section 5 pointer at 20:23 and the `N1i` add-on at about 20:28.
> - **(c) items** (under `DimensionsRecomp/rexlego/out/native-gpu/` unless noted):
>   - FSR3 libs: DONE 19:25, in `DimensionsRecomp/rexglue-sdk/bin/ffx_sdk/`. Already in Agent 2's snapshot since S0c.
>   - Microcode index: the real file has been at the fixed path `lego-microcode-index.cpp` since 19:53.
>   - Main DXIL cache `aot/lego-dxil-cache.cpp`: DONE 19:59:56, 9,601 entries.
>   - HLSL dump `aot/hlsl-dump/`: DONE 20:02, 9,588 files.
>   - Float-blend bank `aot/float-blend-indices-bank/`: DONE 20:12:47, 193 VS, 386 variants.
>   - Instanced bank `aot/instanced-constants-bank/`: DONE 20:23:29, 2,473 variants for 1,271 of 1,272 VS. One shader is skipped (section 7). Log: `build/agent6/aot/logs/banks-inst.log`.
>   - Runtime cache and temporal bank: **stubs by design** (6.2 and 6.3).
> - **Real-cache prelink smoke test: PASS** at 20:29 (section 7): 19,064 linked variants, 263 CPU-s at 1 job, 65.7 MB embedded bank.
> - **`@@done 12` sent at about 20:31.**
> - **Next:**
>   1. Support the first native boot and the capture rounds (section 6).
>   2. Optional clean-up, once Agent 2 has copied the bank files: the test and sample directories under `aot/` (`fbtest-*`, `sample-50*`, `scan`), the per-shader intermediates in the two bank directories, and `build/agent6/prelink_smoke/real/` (about 0.68 GB).

## 1. Summary

All ten inputs can be rebuilt from public sources, the disc and TU23. **None needs private data.** The one exception is the *coverage* of the runtime shader cache: the 255 privately captured runtime containers are gone, so the native renderer starts with an empty runtime cache. Until capture runs refill it, output will be black or partial in places (see (d)).

There are three real costs:

1. **CPU.** The main DXIL compile (~9.6k shaders), the prelink inside the build (~19k variants) and the banks together come to an estimated **1.5-6 CPU-hours**. A bigger slot changes the wall time from hours to tens of minutes (section 3).
2. **Tooling gaps on this machine:**
   - There is no .NET SDK. The extractor needs it, so it will be installed locally under `research/tools/dotnet`, with no admin rights and no PATH change.
   - There is no Vulkan SDK. This only matters if the FidelityFX build insists on glslc; subagent B is checking.
3. **Two scripts hard-code 6 worker threads** (`build_temporal_shader_bank.py`, `build_float_blend_indices_bank.py`). Under the 2-thread rule they have to run in a 1-2 CPU affinity mask. Child processes inherit the mask on Windows.

**Disk:** about 5-10 GB in total, all in git-ignored owned paths. That is under the 20 GB ask threshold.

## 2. The ten inputs

Paths are relative to `DimensionsRecomp/`. "Stub" means (a) already covers the input for compile-only work.

| # | Input | How it is produced | CPU (estimate) | Disk (estimate) | Status / blocker |
|---|---|---|---|---|---|
| 1 | Temporal shader bank (`temporal-bank.{cpp,bin,obj}`) | `tools/gpu-aot/build_temporal_shader_bank.py out --source <HLSL dumps> --dxc <DXC> --llvm-mc <llvm-mc>`. It compiles prepared and motion variants of the dumped shaders and embeds them with llvm-mc. | 5-30 CPU-min | < 0.5 GB | Stub. Needs the HLSL dumps from #6. The script uses 6 threads, so run it under an affinity mask. |
| 2 | Float-blend-indices bank | `build_float_blend_indices_bank.py out --source <dumps> --dxc --llvm-mc`. Input is the `*-vs-0-input.hlsl` VS dumps only. | 2-15 CPU-min | < 0.3 GB | Stub. Same dependency and the same 6-thread issue. |
| 3 | Instanced-constants bank (optional) | `build_instanced_constants_bank.py out --source <dumps> --dxc --llvm-mc --jobs 1`. | 5-30 CPU-min | < 0.5 GB | **Buildable**, with `--jobs` honoured. Without it, CMake logs "instanced draws disabled" and draws stay non-instanced, which is today's behaviour. |
| 4 | FSR3: headers, 2 libs, DLL | Headers: FidelityFX-SDK at eee08db, already initialised. DLL: already in `rexglue-sdk/thirdparty/FidelityFX-SDK/PrebuiltSignedDLL/`. **Libs** (`rexglue-sdk/bin/ffx_sdk/ffx_backend_dx12_x64.lib`, `ffx_fsr3upscaler_x64.lib`): build the DX12 backend and the FSR3 upscaler from the SDK sources, out of tree under `build/agent6/ffx`. A copy of the sources is used if the SDK CMake writes into its own tree; Agent 2's checkout stays read-only. | C++ 1-3 CPU-min, plus shader permutations 5-30 CPU-min (FidelityFX_SC + DXC) | 1-2 GB build tree, ~50-150 MB libs | Subagent B. Not needed at configure; needed at link. Risks: a CRT or iterator-level mismatch with the clang/MSVC-STL game build, and a glslc requirement (no Vulkan SDK). The DLL is found via `LEGO_NATIVE_FIDELITYFX_RUNTIME`, or copied into `rexglue-sdk/bin`. |
| 5 | RenderDoc header target | Already in the SDK: `rexglue-sdk/thirdparty/renderdoc/renderdoc_app.h` and the INTERFACE target `renderdoc` (`rexglue-sdk/thirdparty/CMakeLists.txt:91`). Installed SDKs export `rex::renderdoc`. | 0 | 0 | **Agent 2's side.** It only needs the SDK that rexlego configures against to export the target. Nothing to build. |
| 6 | `lego-dxil-cache.cpp` (main DXIL cache) | Clone reblue-XenosRecomp @339af41, apply the patch, then `prepare_native_compiler.py` to `current-compiler`, then build `gradient_compiler`. Extract with `gpu-shader-extract inventory/extract` from disc + TU23 into `rexlego/out/native-gpu/shader-assets`. Then `XENOS_RECOMP_DXIL_ONLY=1 XENOS_RECOMP_HLSL_DUMP=<dir> gradient_compiler shader-assets lego-dxil-cache.cpp <shader_common.h>`. | **30-240 CPU-min** for ~9,601 shaders at an assumed 0.2-1.5 s each, **to be measured** on a 50-shader sample. Compiler and dependency builds: 3-10 CPU-min. | Assets 0.1-0.3 GB; HLSL dumps 1-3 GB; cache .cpp 0.3-1 GB | Subagent A. **Blocker:** the .NET SDK for the extractor (local install). **CPU:** needs a bigger slot (section 3). Build dependencies: `xxhash.lib`, `zstd_static.lib`, `fmt.lib`, `fmt.dll` in `out/build/lego-release` (owned). |
| 7 | `lego-microcode-index.cpp` | Build `lego_gpu_microcode_index` (`tools/gpu-aot/generate_microcode_index.cpp` + xxhash) standalone, then run `lego_gpu_microcode_index out.cpp shader-assets [runtime-missing]`. | < 2 CPU-min | ~5-50 MB | Stub at the hard-coded path. **No CMake change is needed:** the real file is written to the same hard-coded path `rexlego/out/native-gpu/lego-microcode-index.cpp`, which is inside the owned out-dir, so shipped behaviour does not change. A cache variable would be nicer, but `rexlego/CMakeLists.txt` is not mine. |
| 8 | `runtime-cache.cpp` (runtime containers) | Today: the stub (0 runtime shaders, valid empty archives). Later: capture runs record missing shader containers in game. Each batch goes through the **same** `gradient_compiler`, then this file, then the build's runtime prelink. | 0 now; ~1-5 CPU-min per capture batch (tens to ~100 shaders) | < 50 MB | Stub = **expect black or partial output** for runtime-generated shaders until capture runs happen. The original 255-container corpus is private and gone. Plan in (d). |
| 9 | Prelink outputs (`lego-linked-dxil-cache.cpp`, `runtime-linked-dxil-cache.cpp`) | **Produced by the ON build itself** (`lego_gpu_prelink` and `lego_gpu_prelink_runtime` custom commands) from #6, #7 and #8, linking every (shader, spec-mask) variant with `LEGO_DXC_ROOT`'s dxcompiler. Threads: `LEGO_GPU_PRELINK_JOBS`. | **15-90 CPU-min** for ~19k variants, inside Agent 2's build | 0.3-2 GB in the build tree (less with `LEGO_NATIVE_BINARY_CACHE=ON`, the default) | Stubs at the hard-coded paths. Ninja regenerates them on the first real build, because the stub outputs have no log entry. Needs #10. Agent 2 should size `LEGO_GPU_PRELINK_JOBS` to the slot. |
| 10 | DXC (`LEGO_DXC_ROOT`, default `research/reblue/thirdparty/XenosRecomp/thirdparty/dxc-bin`) | Official DXC **1.9.2609** release zip from github.com/microsoft/DirectXShaderCompiler. Its layout `bin/x64`, `lib/x64`, `inc` already matches. The **same** DXC drives `gradient_compiler`, the banks and the prelinkers; the recipe notes that an older pinned DXC failed to link the newer libraries. | ~0 (download ~30 MB) | ~0.1 GB | Subagent A. If XenosRecomp's own `dxc-bin` holds another version, the official one goes in `research/dxc-1.9.2609` and `-DLEGO_DXC_ROOT` points there. |

Prerequisites, not counted above:
- XenosRecomp clone with submodules: ~0.3-1 GB.
- Local .NET SDK: ~0.8 GB.
- The `out/build/lego-release` dependency libs: < 0.2 GB.

## 3. CPU plan and the asks

| Step | CPU | At 1 thread | At 8 threads |
|---|---|---|---|
| Compiler, extractor and dependency builds | 5-15 CPU-min | 5-15 min | (keep at 1-2) |
| Main DXIL compile (#6) | 30-240 CPU-min | 0.5-4 h | 4-30 min |
| Banks (#1-#3) | 10-75 CPU-min | 10-75 min | 2-10 min |
| FSR3 libs (#4) | 6-33 CPU-min | 6-33 min | (keep at 1) |
| Prelink, inside Agent 2's ON build (#9) | 15-90 CPU-min | 15-90 min | 2-12 min |

- **Ask 1 (to Agent 1, after measuring):** an 8-thread slot of about 30 minutes for #6 plus the banks, once subagent A has measured seconds per shader. Until then everything runs at 1 thread per subagent.
- **Ask 2 (Agent 2):** for the real ON build, set `LEGO_GPU_PRELINK_JOBS` to the slot. The prelink is a large CPU step that a stub configure never showed.

## 4. Blockers and risks

1. **.NET SDK missing** (extractor). Fix: a local `dotnet-install.ps1` install under `research/tools/dotnet`, with no admin rights. Agent 1 was told at 18:13.
2. **Runtime corpus missing** (#8). This is not fixable offline; only in-game capture runs refill it (see (d)). Until then, scenes that use runtime-generated shaders render black or partially. That includes part of the menus and cinematics: the original effort needed about 6 capture rounds and about 110 runtime shaders to reach in-game.
3. **DXC version coupling** (#10 with #6, #9 and #1-#3). One DXC everywhere. A mismatch shows up as prelink failures.
4. **FSR3 ABI** (#4). The libs must match the game's CRT and iterator level; subagent B link-checks them with the game's flags. If FFX can't be built, the fallback is to ask the owner of `rexlego/CMakeLists.txt` for an FSR-off switch. None exists today.
5. **DLC.** The original "expanded candidate" (12,141 shaders) also used 30 DLC packages. We have disc + TU23 only, so the baseline is the 9,601-shader set. DLC levels would be runtime-capture territory.
6. **Hard-coded paths** (#7, #9). These are handled by writing to the hard-coded locations in the owned out-dir. Placing real files there changes what Agent 2's `build/dev` compiles, so I tell Agent 2 before each swap.

## 5. Deliverable (c): native ON inputs and configure flags (final, 20:20)

- `<DR>` = the live tree, `<workspace>/DimensionsRecomp`.
- `<SNAP>` = Agent 2's snapshot, `<workspace>/build/agent2/snap1/DimensionsRecomp`.

### 5.1 Copy into the snapshot

`snap.py` excludes `rexlego/out` and `research/`, so these inputs go in with Agent 2's `build/agent2/snap-native-inputs.py`.

Copy the bank **files**, not the whole bank directories. The directories also hold the per-shader `.hlsl` and `.dxil` intermediates: 772 files (about 24 MB) for float-blend, and 4,948 files (149 MB) for instanced.

| relpath under `DimensionsRecomp/` | bytes | sha256 | role |
|---|---|---|---|
| `rexlego/out/native-gpu/aot/lego-dxil-cache.cpp` | 35,058,115 | `FF9386C1CD435E7EE12781F43A6F42F97AED7062A4147D4E649AF2450157A819` | Main DXIL cache, 9,601 shaders. |
| `rexlego/out/native-gpu/lego-microcode-index.cpp` | 1,652,630 | `2DB859177B4656477D2858B87F37E7F068CABA420362FA21AFA1B3C8C6DD13A2` | Fixed path (no flag), 19,116 records. |
| `rexlego/out/native-gpu/aot/float-blend-indices-bank/float-blend-indices-bank.cpp` | 16,989 | `E29DDC974F5121F3E8DCFECBD9CF50C677194D3254CA6C547C7C6C81C35AB3B7` | Float-blend bank. |
| `…/float-blend-indices-bank/float-blend-indices-bank.bin` | 7,392,792 | `6ADD1DF3D0C195A07D51759C5E9C2B2E4B11359D702F48A0426026E1742DE3DE` | |
| `…/float-blend-indices-bank/float-blend-indices-bank.obj` | 7,393,162 | `AB64F9C98F1A6A293B8664CE2AABBFB92D64F4F56E5B25CE861A6C88A9D10440` | |
| `…/float-blend-indices-bank/verification.json` | 174,574 | `C865526E362C3DCE655120B7A395ED5F02A5D5E691ED72875FF9230E393580CF` | Record only. |
| `rexlego/out/native-gpu/stubs/runtime-cache.cpp` | 869 | `E66C9AA34C301C60003F18AE62B6496041F59123DC1372DAC5C393C7BE88053D` | **Stub**: 0 runtime shaders. |
| `rexlego/out/native-gpu/stubs/temporal-bank/` (4 files) | 1,016 | `.cpp` `3FAF0CC7926E232422C9B42142DB1EA7BAE8A4FE49325620B3603A97B279CDDC`, `.obj` `09D4F1811FAE82B28B7428A56BEF6206A10239CE12C0C9874A273FFDE0A75AB5` | **Stub**. |
| `rexlego/out/native-gpu/aot/instanced-constants-bank/instanced-constants-bank.cpp` | 108,716 | `E395C0262AB95257EAA489BF49E31CCC4316743B7ECBF7B1BE0D9DBFAC276354` | Instanced-constants bank (optional), 2,473 variants. Copied by the `N1i` add-on below. |
| `…/instanced-constants-bank/instanced-constants-bank.bin` | 44,360,984 | `8B32B4DD1611C39D0C894778819D81593D4B95A0B4517A0C51498EF7C930B302` | |
| `…/instanced-constants-bank/instanced-constants-bank.obj` | 44,361,355 | `8214DC7B4A3881D753D7F513EBE34FBD309CF876AFD001BC545963717089E569` | |
| `…/instanced-constants-bank/verification.json` | 1,069,568 | `791FAB0FF74BDD1ADF61C670886D08396301024F37DC9918CEB8F7CFC83685C4` | Record only. |

**Base command** (one line, from the workspace root):

```
python build\agent2\snap-native-inputs.py N1 rexlego/out/native-gpu/aot/lego-dxil-cache.cpp rexlego/out/native-gpu/lego-microcode-index.cpp rexlego/out/native-gpu/aot/float-blend-indices-bank/float-blend-indices-bank.cpp rexlego/out/native-gpu/aot/float-blend-indices-bank/float-blend-indices-bank.bin rexlego/out/native-gpu/aot/float-blend-indices-bank/float-blend-indices-bank.obj rexlego/out/native-gpu/aot/float-blend-indices-bank/verification.json rexlego/out/native-gpu/stubs/runtime-cache.cpp rexlego/out/native-gpu/stubs/temporal-bank
```

**Instanced add-on.** The bank was staged at 20:23:29, so this can run now. If `N1` has not run yet, you can append these four paths to it instead.

```
python build\agent2\snap-native-inputs.py N1i rexlego/out/native-gpu/aot/instanced-constants-bank/instanced-constants-bank.cpp rexlego/out/native-gpu/aot/instanced-constants-bank/instanced-constants-bank.bin rexlego/out/native-gpu/aot/instanced-constants-bank/instanced-constants-bank.obj rexlego/out/native-gpu/aot/instanced-constants-bank/verification.json
```

CMake checks for the instanced bank only at configure time. If the add-on is copied after the ON configure, reconfigure so that instancing is enabled.

The FFX libs and the DLL are already in the snapshot (`rexglue-sdk/bin/ffx_sdk/` and `rexglue-sdk/thirdparty/FidelityFX-SDK/PrebuiltSignedDLL/`). Checked at 20:14.

### 5.2 Configure flags

Use a **fresh build dir**, for example `build/agent2/snap1-on`:
- `snap1-off` stays the bootable OFF baseline.
- `build/dev`'s CMakeCache holds compile-only values:
  - `LEGO_NATIVE_BINARY_CACHE=OFF`;
  - `LEGO_HOST_DXC_EXECUTABLE` = the WinSDK dxc;
  - stub paths;
  - `LEGO_DXC_ROOT` = XenosRecomp's `dxc-bin`, which is DXC **1.8.2407.7**.

Start from `snap1-off`'s configure line (generator, compilers, `LEGODIMENSIONS_X86_BASELINE`, `CMAKE_PREFIX_PATH`, `REXGLUE_HOST_CODEGEN_EXECUTABLE`, `CMAKE_EXPORT_COMPILE_COMMANDS`). Replace `LEGODIMENSIONS_NATIVE_GPU=OFF` with these:

| Flag | Value | Why |
|---|---|---|
| `LEGODIMENSIONS_NATIVE_GPU` | `ON` | |
| `LEGO_NATIVE_SHADER_CACHE` | `<SNAP>/rexlego/out/native-gpu/aot/lego-dxil-cache.cpp` | The real main cache. |
| `LEGO_NATIVE_RUNTIME_SHADER_CACHE` | `<SNAP>/rexlego/out/native-gpu/stubs/runtime-cache.cpp` | Empty until the capture runs (6.2). The runtime prelink accepts it (section 7). |
| `LEGO_TEMPORAL_SHADER_BANK` | `<SNAP>/rexlego/out/native-gpu/stubs/temporal-bank` | Deferred (6.3). Shaders missing from the bank fall back to a reactive mask. |
| `LEGO_FLOAT_BLEND_INDICES_BANK` | `<SNAP>/rexlego/out/native-gpu/aot/float-blend-indices-bank` | Real. |
| `LEGO_INSTANCED_CONSTANTS_BANK` | `<SNAP>/rexlego/out/native-gpu/aot/instanced-constants-bank` | Real (staged 20:23), optional. Without the files, CMake logs "instanced draws disabled" and still configures. |
| `LEGO_DXC_ROOT` | `<DR>/research/dxc-1.9.2609` (the **live** path) | **Must** be the DXC that built the cache (dxcompiler 1.9.2609.5); the default root is 1.8.2407. `research/` is not in the snapshot, and nothing writes to it any more. |
| `LEGO_HOST_DXC_EXECUTABLE` | empty | Host shader passes then use `LEGO_DXC_ROOT`'s `dxc.exe`. |
| `LEGO_HOST_LLVM_MC` | `<workspace>/toolchain/llvm-23.1.6/bin/llvm-mc.exe` | The llvm-mc used by the smoke test and the banks, and the one `build/dev` found. `find_program` would otherwise take the first `llvm-mc` or `clang` on PATH. |
| `LEGO_NATIVE_BINARY_CACHE` | `ON` | Supported here: Clang with the MSVC ABI, x64, llvm-mc, and Python 3.12.4 (found by `build/dev`). With it OFF, the linked cache becomes about 0.5 GB of C++ initializers (section 7). |
| `LEGO_NATIVE_FIDELITYFX_RUNTIME` | `<SNAP>/rexglue-sdk/thirdparty/FidelityFX-SDK/PrebuiltSignedDLL/amd_fidelityfx_dx12.dll` | Not on the `find_file` hints, which are `rexglue-sdk/bin` and the SDK install's `bin`. |

**Build-time environment:** `LEGO_GPU_PRELINK_JOBS=<threads>`. The prelink tool reads it while the build runs (`tools/gpu-aot/prelink_shader_cache.cpp:209-210`). If it is unset, the tool uses all 12 logical CPUs.

**Fixed paths (no flag):**
- `rexlego/out/native-gpu/lego-microcode-index.cpp` is resolved against the configured source tree, so it must be in the snapshot; it is in the base command. In the live tree it has been the real file since 19:53.
- `rexlego/out/native-gpu/lego-linked-dxil-cache.cpp` and `runtime-linked-dxil-cache.cpp` are outputs of the build's prelink commands and have no existence check. The first ON build creates them under `<SNAP>/rexlego/out/native-gpu/`.

### 5.3 What to expect from the ON build

- `lego-dxil-cache.cpp` (35 MB) is compiled twice, once for the game and once for `lego_gpu_prelink`. Each compile took 62 s at 1 thread with clang++ -O3 in the smoke test.
- The main-cache prelink passed a full smoke test (section 7): 19,064 variants from 9,532 shaders in 263 CPU-s at 1 job, writing about 502 MB of linked C++. With `LEGO_NATIVE_BINARY_CACHE=ON`, `embed_linked_bank.py` (82 s) turns that into a 65.7 MB object. At `LEGO_GPU_PRELINK_JOBS=N`, plan on roughly 263/N s for the prelink itself.
- The first boot will show black or partial surfaces wherever runtime-generated shaders are used, because the runtime cache is a stub. Section 6 has the capture loop that fixes it.

## 6. (d) First native boot and capture runs

### 6.1 First boot (Agent 3 or the user drives; needs the native ON exe)

- **Game layout:** the same as the OFF baseline (`game/disc` and `game/tu23`).
- **Environment for capture runs.** These settings add CPU work, so these are not perf runs:
  - `LEGO_DUMP_MISSING_SHADERS=<DR>/rexlego/out/native-gpu/runtime-missing/run-NN` (git-ignored, owned by Agent 6). It writes:
    - `vs-<hash>.bin` and `ps-<hash>.bin`: whole containers that are missing from the AOT cache (`shaders.cpp:509-515`);
    - `placement-containers/`: compiler inputs, at most 256 per process;
    - `placement-raw/`: diagnostic fragments only, **not** inputs.
    
    It also hashes buffer copies (`hooks_buffer.cpp:330-340`).
  - `LEGO_NATIVE_MESH_TRACE=1` (draw.cpp:2365) writes `Native mesh: … VS=<hex> PS=<hex>` lines (draw.cpp:2425). These are the temporal-pair input.
  - `LEGO_NATIVE_PSO_STATS=1` (task 5) turns on the PSO miss/compile counters.
- **Expect:**
  - "shader not present in AOT cache, hash=0x…" warnings.
  - Black or partial surfaces wherever runtime-generated shaders are used (menus, cinematics).
  - One FSR3 context build of about 1.4 s.
- **Pass:** the title screen is reached without a device removal. Record the count of missing-shader warnings and of dumped files.

### 6.2 Capture loop

Run it per area: title and menus, then the hub, then the first level. The original effort needed about 6 rounds and about 110 runtime shaders.

1. Merge every run's `vs-*.bin`, `ps-*.bin` and `placement-containers/*.bin` into `out/native-gpu/runtime-input/`. File names are content hashes, so merging is a copy with no overwrite.
2. Compile the merged inputs: `XENOS_RECOMP_DXIL_ONLY=1 XENOS_RECOMP_HLSL_DUMP=<runtime-hlsl> gradient_compiler runtime-input runtime-cache.cpp <shader_common.h>`. Use A's build in `build/agent6/aot/gradient-build/` (DXC 1.9.2609). It takes 0.05-0.1 CPU-s per shader, so seconds per round.
3. Rebuild the index: `lego_gpu_microcode_index out.cpp shader-assets runtime-input`, then copy the result over `out/native-gpu/lego-microcode-index.cpp`. Tell Agent 2 first.
4. Reconfigure with `-DLEGO_NATIVE_RUNTIME_SHADER_CACHE=<new runtime-cache.cpp>`. The rebuild is the runtime prelink, 2 TUs and a relink: minutes.
5. Re-run the same route. Repeat until the route logs zero missing shaders.

### 6.3 Real temporal bank (after the first capture rounds)

1. Run `audit_temporal_coverage.py --bank <stub temporal-bank> --capture <mesh-trace log> [--capture …] --output temporal-audit.json`. It lists every captured color pair. Against the stub bank, every pair is `missing_companion`.
2. For each hash in `missing_programs`, copy its `<HASH>*` HLSL from A's main `hlsl-dump` (plus the runtime HLSL dump) into a subset directory.
3. Run the unmodified `build_temporal_shader_bank.py` on the subset, with the same DXC and llvm-mc arguments as A's sample run (LOG-A), under a 1-2 CPU affinity mask (the tool has 6 fixed workers).
   - The original bank came from 112 PSOs. At about 0.48 s per variant that is minutes, not the 30-60 min of the full dump.
4. Point `LEGO_TEMPORAL_SHADER_BANK` at the new bank. `audit_temporal_coverage.py … --require-complete` should then pass for the captured route.

### 6.4 Owners and order

| Owner | Role |
|---|---|
| Agent 2 | Native ON build (section 5 flags). |
| Agent 3 | Drives the boots and capture routes, and collects the logs and `runtime-missing/run-NN`. |
| Agent 6 | Merges the captures and builds the runtime cache, microcode index and temporal bank. Tells Agent 2 before swapping any fixed-path file. |

The first native in-game A/B (task 5 counters) waits until the first-level route is capture-complete. Until then, black surfaces skew both fps and PSO counts.

## 7. Measured numbers (19:19, subagent A, 1 CPU on a loaded machine)

- **Corpus:** 9,601 unique shaders from the disc plus TU23 (1,272 VS, 8,329 PS). This matches the original.
- **gradient_compiler:** 0.04-0.09 CPU-s per shader.
  - 50-shader sample, cold: 4.66 CPU-s, 10.97 s wall.
  - Two warm 25-shader shards: 0.92 and 0.95 CPU-s, 2.0 s wall each.
- **Sharding (a documented deviation):** run with `run_shards.py`, then merge with `build/agent6/aot/merge/merge_dxil_cache.exe`.
  - The merged result is byte-identical to a single run: `lego-dxil-cache.cpp` sha256 646479C8…9968, and the HLSL dump matches 50/50.
  - Each shard is resumable (`done.json`).
- **Projections on CPUs 4-11 at 80% scaling:**

  | Step | Time | Output |
  |---|---|---|
  | Main compile | 2-5 min | `lego-dxil-cache.cpp` about 77 MB |
  | Merge (single-thread zstd-22) | 1-3 min | hlsl-dump about 410 MB, 9,588 files |
  | Instanced bank (about 2,400 VS jobs at 0.65 s each, `--jobs 8`) | 2-4 min | about 240 MB |
  | Temporal bank from the full dump (35,860 variants at 0.48 s each, 6 fixed workers) | 30-60 min, not resumable | about 5.6 GB with intermediates. Deferred, see the RESUME note. |

  13 `sourceName`s collide. The larger hash wins, as in a single run.
- **Microcode index:** generator built in 25 s, ran in 11.8 s wall (3.5 CPU-s), 19,116 records.
- **FSR3:**
  - FFX shader permutations: 520 s wall, 169.7 CPU-s.
  - Libs: 65 s wall, 35.7 CPU-s.
- **Prelink smoke test (19:46, Agent 6, 1 thread).** Script: `build/agent6/prelink_smoke/run_smoke.ps1`. Logs: `build/agent6/prelink_smoke/<name>/smoke.txt`. It uses the same sources and flags as `build/dev`'s `lego_gpu_prelink` entries, but with DXC 1.9.2609.
  - Sample-50 cache: 98 linked variants in 0.7 CPU-s; linked `.cpp` 2,657,922 B.
  - `embed_linked_bank.py` with llvm-mc 23: 348 KB COFF object, `numeric_and_literal_identical: true`.
  - Runtime prelink on the stub `runtime-cache.cpp`: exit 0, 639 B output. The empty runtime cache is safe.
  - **Extrapolated to 9,601 shaders (about 18.8k variants):**
    - about 2-3 CPU-min, replacing the 15-90 CPU-min estimate for #9;
    - about 510 MB of linked C++ text;
    - about 67 MB of compressed payload in the exe.
    
    So `LEGO_NATIVE_BINARY_CACHE=ON` is required in practice.

- **Slot run (19:51-20:11, CPUs 4-11, with the whole machine at 100% CPU).** Script: `build/agent6/aot/scripts/run-slot.ps1`. Log: `build/agent6/aot/logs/slot.log`. The two banks started after the slot script's 20:10 no-new-step cut-off, so they ran from `build/agent6/aot/scripts/run-banks-after.ps1`. That script uses the slot mask until 20:14:30 and then 1 CPU. Logs: `logs/banks-fb.log` and `logs/banks-inst.log`.

  | Step | Wall | CPU | Result |
  |---|---|---|---|
  | 32 shards, 8 at a time | 323.6 s | 8 CPUs | 32/32, 0 failures. |
  | Merge (`merge_dxil_cache.exe`, 1 CPU) | 182.5 s | 86.5 s | `lego-dxil-cache.cpp` 35,058,115 B. Merged entries 9,601 = sum of the shards. |
  | HLSL dump merge (1 CPU) | 136.0 s | 55.8 s | 9,588 files, 410,650,046 B. 13 name collisions resolved. |
  | Float-blend inputs (1 CPU) | 487.8 s | 29.6 s | 1,272 VS written. Precheck: 193 VS selected, 386 jobs, 0 problems. CPU-starved: the scan alone took 405 s. |
  | Float-blend bank (6 CPUs) | 74.3 s | | 386 variants, 7,392,792 B blob. |
  | Instanced bank (`--jobs 8` on 8 CPUs, then 1 CPU from 20:14:30) | 672.6 s | 132.0 s (Python only; DXC children not counted) | 2,473 variants for 1,271 of 1,272 VS; 2,542 entries; 44,360,984 B blob. The bank directory is 239 MB, of which 149 MB is 4,948 per-shader intermediates. Two variants of one VS (`1E13090CD0FA6780`, from `1wizardofoza_nxg.6`) were skipped: DXC reports `undeclared identifier 'iLegoInstanceId'` in the tool's rewritten HLSL, so the bank has no entry for that shader. A missing entry makes `ResolveInstancedConstantsShader` return null, and `draw.cpp:4401` then keeps that shader's draws on the non-instanced path. |
  | Delete the shard intermediates | | | 19,333 files, 496 MB freed. Logs, `done.json` and `manifest.tsv` are kept. |

  The main cache is 35 MB against the 77 MB projected from the 50-shader sample: 67.9 MB of DXIL compresses to 9.7 MB.

- **Real-cache prelink smoke test (20:15-20:29, 1 thread on CPU 5).** Until 20:23 it shared that CPU with the instanced bank's 8 DXC workers, so the wall time is inflated. Result: `SMOKE PASS`. Log: `build/agent6/prelink_smoke/real/smoke.txt`.

  | Step | Wall | Result |
  |---|---|---|
  | Compile the cache TU (clang++ -O3) | 62.0 s | `cache.obj` 10,045,470 B |
  | Link `prelink.exe` | 0.6 s | |
  | Run the prelink, 1 job | 692.5 s (263.2 CPU-s) | 19,064 variants from 9,532 spec-constant shaders. `linked-dxil-cache.cpp` 501,838,026 B. |
  | `embed_linked_bank.py` (llvm-mc 23) | 82.4 s | 199,603,972 B of DXIL compressed to 65,737,941 B. `linked-bank.obj` 65,738,323 B. `numeric_and_literal_identical: true`, `metadata_preserved: true`. |

  Compared with the sample-50 extrapolation: 502 MB of linked C++ (projected about 510 MB) and 65.7 MB of payload (projected about 67 MB), but 4.4 CPU-min instead of 2-3.

## 8. Task #26: Plume Windows SDK compatibility patch (batch 2, 22:20)

**Problem.** The only error in the native ON build was `thirdparty/plume/plume_d3d12.cpp:505`, where `D3D12_HEAP_TYPE_GPU_UPLOAD` is undeclared. This machine has Windows SDK 10.0.22621. Its `d3d12.h` has `D3D12_SDK_VERSION` 602 and lacks the enumerator, which is 5 in SDK 10.0.26100 and in the Agility SDK (the copy bundled with FidelityFX is version 614). Agent 2 fixed the snapshot copy as S1+p2 (`B88E4E86...` to `564568D4...`, see `build/agent2/snap1/PATCHES-S1.tsv`). This task puts the same fix into the public recipe: pinned Plume `e0c8871` plus the patch list in `prepare_plume.py`.

### 8.1 The patch

- File: `DimensionsRecomp/tools/gpu-aot/patches/plume-winsdk-compat.patch`. It is 640 B, CRLF like the other patches, sha256 `E03D29D0758E615004BA86CECA95F9CE446785508C43E22F6E26805E558747EF`. The name follows the existing `plume-<topic>.patch` pattern, and the patch goes last in the chain.
- It has one hunk, `@@ -502,7 +502,7 @@`, in `toD3D12(RenderHeapType)`:

  ```diff
  -            return D3D12_HEAP_TYPE_GPU_UPLOAD;
  +            return static_cast<D3D12_HEAP_TYPE>(5); // = D3D12_HEAP_TYPE_GPU_UPLOAD, declared only by Windows SDK >= 10.0.26100 or the Agility SDK; this machine has 10.0.22621 (Agent 2 snapshot patch S1+p2)
  ```

  The new line is Agent 2's p2 line verbatim, comment included, because the result must be byte-identical to the snapshot file.
- `build/agent6/plume26/make_patch.ps1` generated the patch from the snapshot and the pinned source. It checked that:
  - the snapshot and live `plume_d3d12.cpp` both hash `564568D4...`;
  - the six context lines around pinned line 487 (pinned lines 484-490) match snapshot lines 502-508, and pinned line 487 is the old line;
  - undoing the hunk in memory on the snapshot bytes gives `B88E4E86...`, the pre-p2 hash recorded in `PATCHES-S1.tsv`.
- None of the six earlier patches has a `plume_d3d12.cpp` hunk in lines 480-530 or mentions a heap-type enumerator. The new hunk therefore can't break their reverse checks.
- **Behaviour is unchanged:** 5 is the value the newer headers give the enumerator. The game shouldn't reach the line anyway:
  - with the Agility SDK off, `capabilities.gpuUploadHeap` and `gpuUploadHeapFallback` are both `uma` (`plume_d3d12.cpp:3953-3954`);
  - on UMA, `createBuffer` (`:4113`) and `D3D12Pool` (`:3087`) use a custom upload heap and don't call `toD3D12(GPU_UPLOAD)`;
  - nothing outside Plume asks for `GPU_UPLOAD` or reads `gpuUploadHeap`: `git grep` finds no match in the tracked files of `DimensionsRecomp` (rexlego included) or `rexglue-sdk`.

### 8.2 Preparer and test

- `prepare_plume.py` (sha256 `B3C87737...6957`): the new patch is the last entry in the patch list (line 77), described as "Native Plume Windows SDK compatibility fixes". The success messages are unchanged, so existing oracles still match.
- `test_prepare_plume.py` (sha256 `DA360ABA...8F76`):
  - the independently git-applied expected chain now includes the new patch (line 97), so `expected_sha` is the pin plus all 7 patches;
  - a new fixture (lines 289-308) applies the first six patches and then checks three things:
    - `--check` fails with "Native Plume Windows SDK compatibility fixes are missing or incomplete" and writes nothing;
    - a fake-git wrapper limited to the new patch is rejected with "missing patched hunk" in both the already-applied and the no-op-apply modes;
    - a real prepare upgrades the checkout to exactly `expected_sha`, and `--check` then passes;
  - the report gains `winsdk_compat_patch_sha256`;
  - the expected output is now `PASS: 18 actual-public-source Plume preparation checks` (was 17).
- No other tool lists the patch files. `test_plume_*.py` and `COLLABORATION.md:219-220` only call `prepare_plume.py`.

### 8.3 Effect on the ON configure

`rexlego/CMakeLists.txt:79-88` runs `prepare_plume.py --check` at every ON configure and stops with FATAL_ERROR if it fails. With the new list entry:

| Checkout | Result |
|---|---|
| Live `thirdparty/plume`, already p2 (`564568D4`) | `--check` passes (22:23, 8.4). |
| Fresh clone at the pin | As before, run `prepare_plume.py` once without `--check`. It now applies 7 patches. |
| Older checkout prepared with the six-patch list | `--check` fails with "Native Plume Windows SDK compatibility fixes are missing or incomplete" (the test's new fixture covers this). Running `prepare_plume.py` once without `--check` upgrades it. |
| Agent 2's S1 snapshot | Unaffected. Its own `prepare_plume.py` has the six-patch list, and that list passes `--check` on the p2 tree (tested at 22:26, 8.4) because no earlier hunk overlaps line 505. The new list passes on p2 too. |

Optional, for Agent 2 or Agent 1 (`CMakeLists.txt` isn't mine): `LEGO_NATIVE_GPU_FINGERPRINT_INPUTS` (`rexlego/CMakeLists.txt:599-603`) lists `plume_d3d12.cpp`, `plume_d3d12.h`, `prepare_plume.py` and only two of the patches. Both changed files are already inputs, so adding the new patch there would be cosmetic.

### 8.4 Verification (22:23-22:26, CPU 5, normal priority)

Everything ran with `GIT_OPTIONAL_LOCKS=0`, so `git status` didn't rewrite the live Plume index. The log is `build/agent6/plume26/verify26.log`, and the test report is `build/agent6/plume26/test-out/verification.json`.

| Check | How | Result |
|---|---|---|
| Live `prepare_plume.py --check` (check only) | `python DimensionsRecomp\tools\gpu-aot\prepare_plume.py --check` | **PASS**, exit 0. Afterwards the live `plume_d3d12.cpp` still hashes `564568D4...`, HEAD is the pin, and `git status` shows only the three patched files. |
| Scratch clone at the pin; `prepare_plume.py` applies the 7 patches | `build/agent6/plume26/verify26.ps1` | **PASS**: "Applied native fence/resize/command-allocation fixes...", exit 0. |
| Scratch `plume_d3d12.cpp` sha256 equals `564568D4...` (snapshot and live) | same script | **PASS**: byte-identical. |
| Scratch `plume_d3d12.h` and `plume_vulkan.cpp` equal the live files | same script | **PASS** (`2F8B444C...` and `71938A4C...`). |
| Scratch `--check` passes, and a repeat prepare reports PASS | same script | **PASS**, both exit 0. |
| `test_prepare_plume.py` | same script | **PASS: 18 actual-public-source Plume preparation checks; original checkout unchanged**, exit 0. Its independently git-applied chain also gives `patched_source_sha256` `564568d4...`. The whole script took 149 s wall. |
| S1's six-patch `prepare_plume.py` (`CED19F81...`) with `--check` on the live p2 tree | `python build\agent2\snap1\DimensionsRecomp\tools\gpu-aot\prepare_plume.py DimensionsRecomp\thirdparty\plume --check` | **PASS**, exit 0. The snapshot's six patches are byte-identical to the live ones. |

The scratch clone was deleted afterwards. The script's informational `HEAD =` line failed because of a quoting bug, which is now fixed; git's own "HEAD is now at e0c8871" line confirms the pin.

### 8.5 Other D3D12 identifiers that SDK 10.0.22621 lacks

**Method.** `build/agent6/plume26/missing_d3d12_ids.py` (output: `missing_d3d12_ids.txt` next to it):

1. Collect every identifier in the 7 FidelityFX-bundled Agility headers (`rexglue-sdk/thirdparty/FidelityFX-SDK/framework/cauldron/framework/libs/agilitysdk/include`, `D3D12_SDK_VERSION` 614) that doesn't appear in the 18 related headers under `Windows Kits/10/Include/10.0.22621.0` (`D3D12_SDK_VERSION` 602). That gives 1,806 identifiers.
2. Search the 387 source files in `thirdparty/plume` (including `contrib/`) and `rexlego/src/gpu_native` for them. 35 are referenced.
3. Check each hit by hand for guards, build membership and comments.

**Result: apart from line 505, which this patch fixes, nothing that the 22621 headers lack is compiled.** Every other hit is behind a guard that is false in this build, in a file that isn't built, or in a comment:

| Where | Identifiers | Why it isn't compiled |
|---|---|---|
| `plume_d3d12.h:186` | `ID3D12GraphicsCommandList9` | `#ifdef PLUME_D3D12_AGILITY_SDK_ENABLED`. `rexlego/CMakeLists.txt:89` forces the option OFF, Plume's `CMakeLists.txt:102-103` defines the macro only when it is ON, and the snap1-on compile DB has no such define for `plume_d3d12.cpp` or `D3D12MemAlloc.cpp`. |
| `plume_d3d12.cpp:574`, `:2346`, `:3264`, `:3900-3911` | `D3D_PRIMITIVE_TOPOLOGY_TRIANGLEFAN`, `RSSetDepthBias`, `D3D12_PIPELINE_STATE_FLAG_DYNAMIC_DEPTH_BIAS`, `D3D12_FEATURE(_DATA)_D3D12_OPTIONS15/16`, `TriangleFanSupported`, `DynamicDepthBiasSupported`, `GPUUploadHeapSupported` | Same guard. |
| `contrib/D3D12MemoryAllocator/src/D3D12MemAlloc.cpp:6238-6242` | `D3D12_FEATURE(_DATA)_D3D12_OPTIONS16`, `GPUUploadHeapSupported` | `#if D3D12MA_OPTIONS16_SUPPORTED`, defined at `:129-135` as `D3D12_SDK_VERSION >= 610` (602 here). |
| `D3D12MemAlloc.cpp:5954`, `:6065`, `:7704`, `:7708` | `ID3D12Device12`, `GetResourceAllocationInfo3` | `#ifdef __ID3D12Device12_INTERFACE_DEFINED__` (blocks open at `:5953`, `:6064`, `:6137`, `:6217`, `:6293`, `:7694` and `:7737`). The 22621 headers never define that macro. |
| D3D12MA `src/Tests.cpp:3156-3344`, `src/D3D12Sample.cpp:608-609` | several | Not built: Plume's `CMakeLists.txt:74` compiles only `D3D12MemAlloc.cpp`. They are guarded as well. |
| `D3D12MemAlloc.h:445`, `:457`, `:1187`, `:1189`, `:1271`, `:1362`, `:2651-2683`; `D3D12MemAlloc.cpp:5971-5984`, `:6941`; `plume_d3d12.cpp:505` after the patch | several | Comments only. |

- **`rexlego/src/gpu_native`: none.** Its hits are unrelated names that happen to match: `RowCount` (`textures.cpp:842`, a local helper), `Records` (`device.h:185`, in a comment), `f4` (`hooks_state.cpp:334`, a PPC register) and `_WIN32` (`crash_memory.h:2`, `crash_reporter.h:3`).
- The other hits are noise: Vulkan-Headers names (AV1/H.265 std fields, `LineRasterizationMode`, `e16`) and fragments of hex literals (`x2d`, `x2f`, `x100000000ull`).
- **Limitation:** the scan matches names only and doesn't run the preprocessor. For the files that are compiled, the real proof is that native-bin (S1+p1+p2) built at 21:48.
