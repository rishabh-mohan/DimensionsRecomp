# Agent 2: build pipeline - RESUME NOTE (task #1 re-issued after the agy-grid restart; updated 21:50)

**Task #1 steps 1-6 are DONE and verified, and `@@done 1` was sent at about 19:57-20:00.** Step 6 (the PPC map fix)
is described below. On Agent 1's schedule, both batch-1 builds from **S1** are now built and staged
(`build/agent2/devoff1-bin` and `build/agent2/native-bin`). I am waiting for Agent 1's next step.
- **S1** was taken at 20:41:57 (`python build\agent2\snap.py S1`). Manifest: `build/agent2/snap1/MANIFEST-S1-2041.tsv`,
  sha256 f81b1499481ee903428b1ef4c292e54d3ad1035e551ce95a12076785b87535e2. Agent 1 confirmed no live edits after
  20:15. Batch 1 = S1 plus explicit patches. Each patch is logged with its before/after sha256 in
  `build/agent2/snap1/PATCHES-S1.tsv` (sha256 74655029...), and I never re-copy the live tree for batch 1.
  - **S1+p1** (20:55): `rexlego/src/gpu_native/device.cpp` 4C15043E... -> 4DC63FA0.... This is Agent 7's
    perf-csv-rows patch (Option A), for the native build only.
  - **S1+p2** (21:34): `thirdparty/plume/plume_d3d12.cpp` B88E4E86... -> 564568D4.... Line 505
    `return D3D12_HEAP_TYPE_GPU_UPLOAD;` became `return static_cast<D3D12_HEAP_TYPE>(5);` (problem 27). Agent 1 asked
    for it, and Agent 6 makes the same change in the live tree. `prepare_plume.py --check` still passes on the
    snapshot.
  - Native inputs, whose hashes match Agent 6's table: N1 (11 files), N1i (4 files) and N1d
    (`research/dxc-1.9.2609`, 33 files). Lists: `build/agent2/snap1/NATIVE-INPUTS-*-2055.tsv`.
  - S1 already has Agent 12's closure-header edits: `xmemory.h`, `logging/api.h` and `logging/macros.h` are
    hash-identical to the live tree (checked 21:37).
- **SDK** (`build/agent2/snap1-sdk`, incremental from S0d): build 269.6 s at -j10, [264/264], exit 0. Install
  50.9 s into `build/agent2/snap1-sdk/install`.
- **Dev OFF build 1: DONE.** In `build/agent2/snap1-off`: configure 3 s, gate PASS, game 789.6 s at -j10 (479 edges,
  0 errors). **Staged at 21:08 to `build/agent2/devoff1-bin`**: 7 files, 214.2 MB, all checks PASS.
  - MANIFEST.txt sha256 1E81AA5E0C8A4309D15511EFA790BAC65D51532137A1165477466699BB83EE09.
  - exe: 170,334,720 B, sha256 D95273C99370D46B....
  - Announced to all.
- **Native ON build: DONE.** Built in the fresh `build/agent2/snap1-on` (snap1-off is kept for Agent 6).
  - Configured at 20:58: 38 s, gate PASS, instanced bank enabled.
  - Run 1 (21:07:46-21:28:50, 1263.6 s) stopped at [459/553]. Only plume_d3d12.cpp failed; log
    `snap1-native-build-1.log`. Every rexlego/src TU waited behind plume, so none of them compiled in run 1.
  - Run 2, after S1+p2 and with no reconfigure: 21:36:54-21:44:14, 438.8 s, 96 edges, exit 0, 0 errors. Its 206
    warnings are 202 -Wdeprecated-declarations (native renderer) and 4 -Wunused-value (thirdparty miniz.h). Log:
    `snap1-native-build.log`.
  - **Staged at 21:48 to `build/agent2/native-bin`**: 8 files, 363.5 MB, 48/48 checks PASS. A first staging at
    21:45 had the same files; the re-stage only added MANIFEST lines (all native-input lists, the patches) and the
    fingerprint check.
    - MANIFEST.txt sha256 91F2F817B0D6D205396818FB32D5846DBE374BB81E2D31BE9EE770837451BBC1.
    - exe: 315,745,280 B, sha256 3B329E9550A1178C.... It contains this build's native GPU fingerprint
      `befeb1184e6c7abc`.
    - map: 43,576,778 B, sha256 48428DB0....
    - amd_fidelityfx_dx12.dll: sha256 12A50812..., equal to the snapshot's PrebuiltSignedDLL copy.
    - rexruntime.dll (FDB315DC...) and rexgpu-xenos.dll (BFE1DF8B...) are the same files as in devoff1-bin.
  - Announced to all at about 21:50.
- **Quiet window from about 21:50 (Agent 1).** No compiles, tests, benches or codegen from me until Agent 1 announces
  its end; nothing of mine is running. If a build of mine is running when a window opens, `build\agent2\stop-snap.ps1`
  kills the build-snap tree, and ninja redoes any interrupted edge.
- **Scripts** (all in `build/agent2/`):
  - `snap.py`: snapshot refresh.
  - `build-snap.ps1`: switches -Phase sdk|game, -Native, -SkipConfigure and -NoBuild; runs the gen-check and gate
    steps. A step fails when its log has FAILED or ninja error lines.
  - `gen-check.py`: checks that snap1's generated output equals the baseline's (886/886 files).
  - `codegen-frozen/codegen-frozen.exe`: the stand-in for REXGLUE_HOST_CODEGEN_EXECUTABLE. It keeps the pinned
    0.0.23.3 output.
  - `snap-gate.py`: the compile DB and include-dir gate.
  - `stage-snap-bin.ps1` (-Variant off|native), `snap-native-inputs.py`, `stop-snap.ps1`.
  - `splice-notes-top.py`: replaces this RESUME block safely.
- Keep every intermediate (snap1, snap1-sdk, snap1-off, snap1-on and the build dirs) until Agent 1 says otherwise.
- Free C: about 264.8 GB at 21:48. agy-grid delivers only the `@@to` line itself, so every message is ONE line; the
  details live in this file.

| Step | Result | Wall | Evidence |
|---|---|---|---|
| 1 SIMDe | `prepare_simde.py --check` PASS (dev + baseline share it via the junction) | - | - |
| 2 rexglue target | build/sdk `--target rexglue`; frozen copy `build/agent2/codegen-tool/rexglue.exe` (sha256 FA9EE64C...) == install/bin | 103.3 s | - |
| 2 codegen | "XEX patch applied successfully ... new version: 0.0.23.3"; 887 files, 467.3 MB, 438 `legodimensions_recomp.N.cpp` + init + register | 129.8 s | `build/agent2/gen-noflag/`, codegen logs |
| 2 codegen `--pointer_table_scan --ignore-stamp` | 0 written, 883 unchanged: the flag changes nothing for this XEX | 100.6 s | `codegen-pts.log` |
| 2 junction | `DimensionsRecomp\rexlego\generated -> baseline\DimensionsRecomp\rexlego\generated` | - | announced ~19:10 |
| 2 SDK header list | 101 headers (64 `include/rex`, 37 thirdparty fmt/simde/spdlog), identical in all 5 scanned generated TUs | 7 s | `build/agent2/sdk-headers-dev.txt`, list below |
| 3 SDK | run 2 (after SIMDe) exit 1 only from the 7 PPC `.map` nm edges; install 30 s; ctest **216/216 pass**, 4 skipped (BitStream), excl. `ppc_tests_NOT_BUILT` and `^ppc\.` | 90.2 s + 30 s + 6.7 s | `build/agent2/sdk-*.log` |
| 4 OFF game | `build-game-baseline.ps1`: run 1 FAIL (partition coupling, below), run 2 `-k 0` all other 450 edges OK, run 3 shim TU + link | 196.9 s / ~17.7 min / 18 s | `game-build-run1/run2.log`, `game-build.log` |
| 4 staged | `build/baseline-bin` re-staged 19:01:22 with TracyClient.dll: 7 files, 214.0 MB; `MANIFEST.txt` has sha256, import tables, 37 PASS checks | 8 s | `stage-baseline-bin.ps1` |
| 5 ON configure | build/dev, NATIVE_GPU=ON, Agent 6 stubs, shim, frozen codegen; 1292 DB entries (70 rexlego/src .cpp TUs, 440 generated, the rest SDK + plume) | 369.9 s, re-run 24.1 s | `dev-on-configure.log` |
| 5 generated headers | 12 build/dev headers (9 `gpu_native/shaders/*.h` incl. `copy_color_ps.h`, `native_gpu_build_info.h`, 2 overlay) from each edge's OWN command | ~6 s | `dev-gen-headers.ps1/.log` |
| 5 compile-one sweep | **70/70** rexlego/src TUs pass `compile-one -SyntaxOnly -Db build\dev\compile_commands.json` (6 jobs) | 276 s | `build/agent2/c1-sweep/summary.txt` |
| 6 PPC map fix | `rexglue-sdk/cmake/ppc_test_pipeline.cmake`: nm runs under `cmake -P` with stdout on a pipe and the map is written byte-exact. **166/166** script-mode and **168/168** ninja-built maps are byte-identical to nm's stdout | 18 s + 49 s | `build/agent2/ppcmap-test/test_ppcmap3.log` |

## Step 6: PPC .map fix (19:49; Agent 9 needs it for the dev PPC suite)
- File: `DimensionsRecomp/rexglue-sdk/cmake/ppc_test_pipeline.cmake` (sha256 `a807021ed5b0d377...`). Two hunks:
  1. **The symbol-map rule** is now `${CMAKE_COMMAND} -DPPC_NM=<nm> -DPPC_NM_INPUT=<obj, cygwin path>
     -DPPC_NM_OUTPUT=<map> -P ${CMAKE_CURRENT_FUNCTION_LIST_FILE}`, with `DEPENDS <obj> <this file>` and the same
     COMMENT and VERBATIM. Before, it was `nm --numeric-sort <obj> > <map>`, which crashes the bundled Cygwin nm
     with 0xC0000005 because its stdout is a file.
  2. **A script-mode block at the top of the same file** (`if(CMAKE_SCRIPT_MODE_FILE AND DEFINED PPC_NM_OUTPUT)`)
     runs `execute_process(COMMAND nm --numeric-sort <obj> OUTPUT_VARIABLE ...)`, so stdout is a pipe. A non-zero
     exit is a FATAL_ERROR; otherwise the block writes the map. When the file is included normally (configure),
     the block is skipped.
- **Writing the map byte-exact.** `file(WRITE)` opens its file in text mode, so on Windows every LF became CRLF. The
  first test got 0/166 identical, with one extra byte per line. The map is now written with
  `file(CONFIGURE OUTPUT <map> CONTENT <nm output> @ONLY NEWLINE_STYLE LF)`, which writes in binary mode.
  - With @ONLY, file(CONFIGURE) changes only `@VAR@` references and `#cmakedefine` lines. The step fails
    (FATAL_ERROR) if nm's output contains `@` or `#cmakedefine`; the output for these objects has neither.
  - Empty output gives an empty map, as `nm > map` would. That happens for an all-commented test such as
    `instr_vpkpx.s`.
  - `execute_process` drops only NUL bytes and the CR of CR-LF pairs. nm's stdout has neither: 0 CR in 42,373 bytes
    over 166 objects.
- **Tests** (`build/agent2/ppcmap-test/test_ppcmap.py`). Everything is written in that scratch dir: build/sdk is only
  read, the baseline and `rexglue-sdk/out` are untouched, and no `.ninja_log` is edited.
  - (a) Script mode on all 166 `build/sdk/tests/ppc/obj/*.o`: **166/166 maps are byte-identical** to nm's stdout
    captured on a pipe (2 are empty, matching empty output), with 0 CR bytes. A missing input fails the step
    (exit 1) and writes no map.
  - (b) Control: `nm --numeric-sort <obj> > file` still crashes with 0xC0000005 and leaves a 0-byte file.
  - (c) Configure mode: a scratch project includes the pipeline and calls `ppc_add_test_binary()` for all 168
    `tests/ppc/asm/*.s`, as `tests/ppc/CMakeLists.txt` does.
    - The clean Ninja build runs 168 assemble, 168 link and 168 map edges, exit 0. **168/168 maps are
      byte-identical**, and the `.bin` files match build/sdk for the 166 tests both have.
    - A second build reports "no work to do".
    - An incremental build after the pipeline edit re-ran CMake and exactly the 168 map edges.
  - (d) The frozen 0.0.23.3 `rexglue.exe recompile-tests` on those maps: exit 0, 1496 TEST_CASEs.
- **Effect on the trees.** In `rexglue-sdk/out`, the first build after this change re-runs every map edge (the
  command is new) and then `recompile-tests`. The PPC suite no longer needs excluding for the nm crash. build/sdk
  (the baseline) keeps the original pipeline from its own snapshot and is not rebuilt.

## Answers for Agent 1 (19:10)

### Staging: build/baseline-bin
- **Files:**
  - legodimensions.exe (170,414,080 B, sha256 `FB922AC9E29D68F6...`);
  - legodimensions.map (39,101,836 B, `FDFE9965C6D918C1...`);
  - rexruntime.dll (`E01D461823AE3647...`);
  - rexgpu-xenos.dll (`49825FC8326614D6...`), from build/sdk/install/bin, identical to the SDK out tree;
  - TracyClient.dll, from install/bin; nothing imports it;
  - achievement_unlocked.wav and FiraSans-Regular.ttf.

  Full hashes, import tables and checks are in `build/baseline-bin/MANIFEST.txt`.
- README-dev's runtime list is covered (exe, rexruntime.dll, wav, rexgpu-xenos.dll, font). Its `mods` folder row is
  for the installer package, not for running the game.
- **No PDBs exist.** The exe links without `/DEBUG`, and the SDK install and out trees have none. Symbols are in
  legodimensions.map. On request I can make a symbolized relink twin from the same objects
  (`/DEBUG /OPT:REF /OPT:ICF`, so the optimised layout is kept) into `build/agent2/sym` in about 1-2 min.

### (a) Tracy: not active in anything we build (Release)
- `build/sdk` is Ninja Multi-Config (Debug;Release;RelWithDebInfo) and its compile DB lists all three configs.
  The Release entries are 887 SDK TUs with neither `TRACY_ENABLE` nor `REXGLUE_ENABLE_PROFILING`. The only Release
  TU with `TRACY_ENABLE` is `thirdparty/tracy/public/TracyClient.cpp` itself. The 639 hits I saw first were the
  Debug and RelWithDebInfo entries.
- Why: `src/core/CMakeLists.txt:126-131` and `src/system/CMakeLists.txt:96-103` link `TracyClient` and define
  `REXGLUE_ENABLE_PROFILING` only for `$<NOT:$<CONFIG:Release>>`. TracyClient's PUBLIC definitions are
  TRACY_ENABLE, TRACY_ON_DEMAND, TRACY_DELAYED_INIT, TRACY_MANUAL_LIFETIME and TRACY_FIBERS.
- Game TUs in build/baseline: none. build/dev (in-tree SDK, Release): only TracyClient.cpp.
- llvm-readobj: neither the exe, rexruntime.dll nor rexgpu-xenos.dll imports TracyClient.dll, and rexruntime.dll has
  no Tracy strings.
- Project default: `option(REXGLUE_ENABLE_TRACY ... ON)` (SDK `CMakeLists.txt:24`). In Release that only builds and
  installs TracyClient.dll; Debug and RelWithDebInfo builds would be instrumented (on demand).

### (b) Dev OFF build 1 (from a snapshot; mirrors the baseline, so only the sources differ)
- **The snapshot** `build/agent2/snap1/DimensionsRecomp` holds real copies of the live
  `DimensionsRecomp/{rexglue-sdk,rexlego,thirdparty,tools}` and the top-level files.
  - Excluded: `rexglue-sdk/out`, `rexlego/out`, `research/` and `.git` directories. The submodule `.git` files are
    kept (problem 16).
  - `rexlego/generated` was copied once from the pristine 0.0.23.3 output.
  - `game_root` in the manifest is re-pointed for the deeper path.
- **`build\agent2\snap.py <TAG>` refreshes the snapshot.** It copies changed files with mtime = now, so ninja
  rebuilds whatever depends on them. It also re-copies tampered files and deletes removed ones. It writes
  `snap1/MANIFEST-<TAG>-<HHMM>.tsv` (size, mtime and sha256 per file) and `snap1/DIFF-<TAG>-<HHMM>.txt`, which flags
  changed closure headers.

| Tag | Time | Files | Change | Wall |
|---|---|---|---|---|
| S0 | 19:16-19:20 | 23,738 | first copy; generated 887 files | 269.5 s |
| S0b | 19:23 | +20 | 19 file symlinks copied by content (libmspack sources the SDK compiles); new `tests/ppc/asm/seq_tailcall_musttail.s`; changed `src/core/threading_win.cpp` | 6.6 s |
| S0c | 19:26 | +31 | the submodule `.git` files; Agent 6's FSR3 libs (`rexglue-sdk/bin/ffx_sdk/*.lib`); changed `rexlego/src/gpu_native/draw.cpp` and the pipeline | 8.2 s |
| S0d | 19:46 | 23,789 | changed `include/rex/logging/macros.h` (closure; Agent 12, 19:27), `src/ui/rex_app.cpp` (Agent 12) and the pipeline | 8.2 s |

- **`build\agent2\build-snap.ps1 -Phase sdk|game|all [-Jobs N] [-Affinity F] [-SkipConfigure] [-KeepGoing]`**
  - **SDK:** `cmake --preset win-amd64` (Ninja Multi-Config, FidelityFX OFF, x86-64-v2) in
    `build/agent2/snap1-sdk`, with `REXGLUE_BUILD_TESTS=OFF`. Release build, then install to `snap1-sdk/install`.
    build/sdk/install is never touched.
  - **Game:** `build/agent2/snap1-off`: NATIVE_GPU=OFF, Release, x86-64-v3, `CMAKE_PREFIX_PATH=snap1-sdk/install`,
    the frozen codegen tool, and no shim.
  - **Gate:** `snap-gate.py` must pass before the game build. It checks that every include dir is inside snap1*,
    that there are 440 generated TUs, that rexglue_DIR is right, and that the installed rex, fmt, spdlog and simde
    headers hash-equal the snapshot.
  - Step log: `build/agent2/snap1-steps.txt`. Logs: `snap1-*.log`. `-Affinity F` pins every step to CPUs 0-3.
- **History:**
  - SDK configure attempt 1 (19:23) failed in 5 s because the submodule `.git` files were missing (problem 16).
  - Attempt 2 (19:26) was still in its try_compile checks at 19:41 under the load. It then died with its task
    (problem 18), so -j10 never started.
  - Attempt 3, from S0d and pinned to CPUs 0-3: the configure ran 19:46:51-19:51:04 (252.6 s, exit 0), and the SDK
    build at -j3 started at 19:51:04.
- **Timeline from here:** see the top of this note.

### (c) ON build: the same tree (recommended) or its own tree
- The generated TUs' compile commands are flag-identical in OFF build/baseline and ON build/dev; only tree paths and
  the PCH location differ. Only the rexlego/src TUs gain `-DLEGODIMENSIONS_NATIVE_GPU=1` and the two metadata defines.
- The ON block works in find_package mode: `probe-toggle.ps1` configured one find_package tree OFF (11.5 s) and then
  ON (7.8 s), both exit 0. The install exports `rex::renderdoc`, the FidelityFX runtime is passed explicitly,
  and the FSR3 libs are read from `<snapshot>/rexglue-sdk/bin/ffx_sdk/`.
- **Probe result (19:07, `build/agent2/probe-toggle.log`):** one find_package tree (dev rexlego against
  build/sdk/install) was configured OFF (9.8 s) and then ON with Agent 6's stub flags (10.5 s), both exit 0.
  Compile DB diff OFF -> ON:
  - **generated: 440/440 identical; PCH identical;**
  - rexlego/src: 33 changed + 38 ON-only;
  - other, changed (3): `share/rexglue/rex_app.cpp`, `share/rexglue/windowed_app_main_sdl.cpp`,
    `res/legodimensions.rc`;
  - other, ON-only (18): SDK `texture/{util,info}.cpp`, plume_d3d12 + D3D12MA, miniz, zstd,
    `gpu-aot/generate_microcode_index.cpp` and `prelink_shader_cache.cpp`, and the 4 `rexlego/out/native-gpu`
    cache/index TUs.

  `compile-one -SyntaxOnly` of SDK `texture/util.cpp` and `info.cpp` with that DB: exit 0 (6-7 s each). So toggling
  ON in the OFF tree recompiles no generated TU. Still unknown until Agent 6's real inputs land: the compile time of
  the real bank TUs (embedded caches).
- **Agent 6's inputs.** The FSR3 libs are in the live tree and in S0c. Between 20:00 and 20:30 Agent 6 replaces the
  stub `lego-microcode-index.cpp` with the real index (19,116 records) and stages the DXIL cache and the instanced
  and float-blend banks in `rexlego/out/native-gpu/aot/`; the temporal bank stays a stub. The final flags arrive at
  about 20:30 in `perf-notes/agent6-native-aot.md` section 5. I copy the inputs into the snapshot and hash them.
- **Same tree:** stage the OFF outputs first, then reconfigure `snap1-off` with NATIVE_GPU=ON and Agent 6's final
  flags, and build. That is about 70 src TUs, the ON-only TUs, 12 shader headers and the link: **about 6-10 min,
  with no generated-TU recompile** (ninja reruns an edge only if its command or inputs change). Toggling back for a
  later OFF build costs the same few minutes.
- **Own tree** (README-dev style, `REXSDK_DIR=<snapshot>/rexglue-sdk`): about 30 min cold (in-tree SDK about 9 min,
  440 TUs about 18, the rest about 3), and there is no CPU to pre-build it before 20:45.

### Junction warning (step 2)
`DimensionsRecomp\rexlego\generated` is a junction into the pristine baseline output. Never run codegen into it.
Every tree pins `-DREXGLUE_HOST_CODEGEN_EXECUTABLE=build/agent2/codegen-tool/rexglue.exe` (the frozen 0.0.23.3
tool, == build/sdk/install/bin/rexglue.exe), so its in-build codegen edge rewrites nothing (0 written). For codegen
experiments, use a copy of the manifest whose output directory is under your own build/agentN.

### SDK headers in the generated-code closure (step 2)
Editing ANY of these forces a rebuild of all 440 generated TUs (about 17-18 min at -j10), plus every SDK library that
includes them.
- **How they were found:** `clang -M` on `legodimensions_recomp.{0,219,437}.cpp`, `legodimensions_init.cpp` and
  `legodimensions_register.cpp`, using build/dev's real compile commands (`build/agent2/sdk-headers.py`). All five
  include the identical set.
- Paths are relative to `DimensionsRecomp/rexglue-sdk/` (the dev tree you edit). In the find_package trees the same
  files arrive as installed copies under `<install>/include/`.

The list:
- `include/rex/` (64): assert.h, chrono/chrono.h, chrono/clock.h, cvar.h, filesystem.h, filesystem/device.h,
  filesystem/entry.h, filesystem/file.h, filesystem/vfs.h, filesystem/wildcard.h, hook.h, image_info.h, literals.h,
  logging.h, logging/api.h, logging/assert.h, logging/format.h, logging/macros.h, logging/types.h, math.h, memory.h,
  memory/arena.h, memory/mapped_memory.h, memory/ring_buffer.h, memory/utils.h, perf/counter.h, platform.h,
  platform/dynlib.h, platform/fpscr.h, ppc.h, ppc/context.h, ppc/func.h, ppc/function.h, ppc/intrinsics.h,
  ppc/stack.h, stream.h, string.h, string/buffer.h, string/key.h, string/numeric.h, string/utf8.h,
  system/achievement_manager.h, system/achievement_store.h, system/export_resolver.h, system/function_dispatcher.h,
  system/kernel_state.h, system/mmio_handler.h, system/thread_state.h, system/util/native_list.h,
  system/util/object_table.h, system/util/xdbf_utils.h, system/xam/app_manager.h, system/xam/content_manager.h,
  system/xam/user_profile.h, system/xcontent.h, system/xmemory.h, system/xobject.h, system/xtypes.h, thread.h,
  thread/fiber.h, thread/mutex.h, thread/timer_queue.h, types.h, vec128.h
- `thirdparty/fmt/include/fmt/` (2): base.h, format.h
- `thirdparty/simde/simde/` (21): check.h, debug-trap.h, hedley.h, simde-align.h, simde-arch.h, simde-common.h,
  simde-constify.h, simde-detect-clang.h, simde-diagnostic.h, simde-f16.h, simde-features.h, simde-math.h,
  x86/avx.h, x86/avx2.h, x86/mmx.h, x86/sse.h, x86/sse2.h, x86/sse3.h, x86/sse4.1.h, x86/sse4.2.h, x86/ssse3.h
- `thirdparty/spdlog/include/spdlog/` (14): common.h, details/backtracer.h, details/circular_q.h, details/log_msg.h,
  details/log_msg_buffer.h, details/null_mutex.h, details/periodic_worker.h, details/registry.h,
  details/synchronous_factory.h, fmt/fmt.h, logger.h, spdlog.h, tweakme.h, version.h
- Also in the closure, not SDK: `generated/default/legodimensions_{pch,init,funcs}.h` plus the TU's own
  `legodimensions_funcs.N.h`, and the tree's `cmake_pch.hxx`.

Closure headers already edited for batch 1:
- `include/rex/ppc/intrinsics.h` and `include/rex/math.h` (Agent 10).
- `include/rex/system/xmemory.h`, `include/rex/logging/api.h` and `include/rex/logging/macros.h` (Agent 12,
  18:50). Agent 12 changed `macros.h` again at 19:27 (in S0d) and plans no more closure edits.

Problems and fixes (session 3):

1. **Partition coupling (repo bug at 127e04b).** `rexlego/src/native_lock_elide.cpp` is the only src file that
   includes partition headers, `legodimensions_funcs.{154,254,302,389,393,395,410}.h`, chosen to match the
   author's history-dependent `generated/default/codegen.partition.json` (not in the repo). A fresh codegen
   partitions differently, so `sub_83F99290` and `sub_83F9ABE0` are undeclared (3 errors). Fix without touching
   the snapshot or the generated tree: `build/agent2/compat/` (`native_lock_elide_compat.h` = PCH +
   2x `DECLARE_REX_FUNC`, force-included into that TU only by `project-include.cmake` through
   `-DCMAKE_PROJECT_INCLUDE`), in build/baseline and build/dev. Proper fix belongs in the source.
2. CMake 3.28 does **not** honour `SHELL:` in the per-source `COMPILE_OPTIONS` property (clang got
   `'SHELL:-include "..."'` as one file name). Use the joined `-include<path>` form (clang JoinedOrSeparate).
3. `CMAKE_PROJECT_INCLUDE` runs for every `project()`; in build/dev that includes the SDK + thirdparty, so the
   shim is guarded on `PROJECT_NAME STREQUAL legodimensions`.
4. The 9 dxc shader-header edges in build/dev have order-only deps on SDK targets (`ninja -t commands` closure:
   1140 commands, 1131 non-dxc), so they are NOT built through ninja; `ninja -t commands -s` gives each own command.
5. README-dev string check: short literals (<= 15 chars) can be absent from a binary built by clang -O3 (MSVC SSO
   `std::string` built from instruction immediates). `d3d12_bindless` and `GPU/D3D12` are absent from a FRESH
   rexgpu-xenos.dll (DLL 18:02:58 newer than its obj 18:02:48, which has them). Check 16+ char strings.
6. No PDBs in this configuration: the exe links without `/DEBUG`; SDK install/out have none. Symbols = .map.
7. No copy rule for rexgpu-xenos.dll into build/baseline in find_package mode; staged from build/sdk/install/bin
   (== SDK out tree, sha256 49825FC8...). exe/rexruntime.dll need only system DLLs (VC++ runtime in System32).
8. PowerShell: `H` is the `Get-History` alias (my function was shadowed); `$r` is `$R`; `Start-Process -PassThru`
   needs `$p.Handle` cached or `ExitCode` is null.
9. The in-build codegen edge ran its 109.5 s analysis once in build/baseline (0 written); stamp now current.
10. x86: SDK x86-64-v2 + game x86-64-v3 kept (README-dev's documented pair; build/dev gives the same pair).
11. **Correction (Tracy):** my 18:5x note that the baseline SDK libraries were compiled with Tracy on was wrong. The
    639 `TRACY_ENABLE` hits were the Debug and RelWithDebInfo entries of build/sdk's multi-config compile DB; in
    Release only TracyClient.cpp has it. See (a) above.
12. PowerShell 5.1: `Tee-Object -Append` writes UTF-16LE into an existing UTF-8 log, and pipeline output inside a
    function leaks into its return value (the probe's `$c1 -ne 0` became an array test and printed a bogus
    "configure failed"). Fix: `filter Log { $_ | Out-File -Append -Encoding utf8 $log; Write-Host $_ }`.
13. agy-grid delivers only the text on the `@@to` line itself; every message is one line and details live here.
14. Agent 8 (19:0x) fixed the dev tree's `native_lock_elide.cpp`: it declares its 21 callees with
    `DECLARE_REX_FUNC` and compiles with or without the shim. The shim is now only needed for build/baseline
    (snapshot 127e04b). build/dev still carries it (harmless); it goes at the next build/dev reconfigure. New trees
    (snap1-*) are configured without it.
15. Snapshot copies: the libmspack sources the SDK compiles are file symlinks, and moltenvk has 8 directory links.
    S0 skipped all 27 reparse points. snap.py now copies file symlinks by content (19) and skips the directory links
    (moltenvk is macOS-only).
16. The SDK configure needs each submodule's `.git` FILE: `thirdparty/CMakeLists.txt:72` checks
    `EXISTS <submodule>/.git` and fails with "Git submodule 'cli11' is not initialized". snap.py keeps the `.git`
    files (31) and skips `.git` directories. git itself is not needed: the version falls back to
    0.10.0.0-dev.unknown, as in the baseline.
17. The first snapshot copy took 269.5 s (23.7k files, about 1.5 GB, through `\\?\` paths). Refreshes take 6-9 s.
18. Processes started under a run_command task die with it. At 19:40 I killed only the build-snap.ps1 PowerShell, so
    that the slow SDK configure could finish without a -j10 build following it. That ended task-398, and its
    process tree took the configure with it. CMake writes CMakeCache.txt only at the end of a configure, so every
    check result was lost and attempt 3 started from scratch. To stop a build, kill its task or run
    `build/agent2/stop-snap.ps1`; to keep a child alive, don't end its task.
19. Step 6: CMake `file(WRITE)` writes in text mode on Windows, so LF becomes CRLF. Use
    `file(CONFIGURE ... NEWLINE_STYLE LF)` (binary mode) when the bytes matter. `execute_process` drops NUL bytes and
    the CR of CR-LF pairs from captured output.
20. PowerShell: `[IO.File]` methods resolve relative paths against the process cwd, not the `Set-Location`
    directory, so use full paths.

# Session 2 resume note (16:55, superseded by the block above)

**Paused 16:55 for the agy-grid restart. Nothing of mine is running. All trees are consistent, and
Ninja resumes incrementally.** Free C: 23.57 GB at 16:48.

Problems and fixes (session 4, 19:57-21:50):

21. **The notes were wiped at 19:59:40.** `open(p,'wb').write(open(p,'rb').read()...)` truncated this file before it
    read it. A subagent replayed my transcript into `build/agent2/recovered/` (`recover-notes.py`; REPORT.txt has
    19/19 checks passing), and I copied the 19:57 state back. Rule: never read and write the same file in one
    expression. `build/agent2/splice-notes-top.py` reads the file first, backs it up, writes `.new` and then
    `os.replace`s it.
22. **`start "" /b /wait /affinity F` hides exit codes.** The S0d pre-build ran under it, so both the S0d gate (which
    had in fact failed on version.h, item 24) and the SDK -j3 build looked like exit 0. Fix: `build-snap.ps1`'s
    Step() also fails a step (exit 98) when its log has `^ninja: build stopped`, `^ninja: error`, `^FAILED: ` or
    `^CMake Error`. The -j10 runs don't use -Affinity.
23. **A fresh build dir re-runs codegen, and `snap.py` rewrites only `game_root`, not `[entrypoint] file_path`.**
    The S0d game build failed at 20:11:25 with "Entrypoint XEX not found .../snap1/.../rexlego/../../game/disc/Default.xex".
    The fix has two parts:
    - `REXGLUE_HOST_CODEGEN_EXECUTABLE=build/agent2/codegen-frozen/codegen-frozen.exe`, a stand-in that keeps the
      pinned 0.0.23.3 output and writes nothing.
    - `gen-check.py`, a build-snap step before the gate: snap1's generated output == baseline, 886/886.
    The codegen edge re-runs on every build because its stamp is older than the snapshot manifest. Restat means
    nothing downstream rebuilds.
24. **The gate rejected `include/rex/version.h`.** That header is configure-generated (configure_file from
    `version.h.in` into `snap1-sdk/include/rex`). `snap-gate.py` now passes it when the snapshot has `<rel>.in` and
    the installed copy hash-equals the configured one.
25. **I missed the 20:15 S1 deadline** because the timer was delivered late. S1 was taken at 20:41:57, and Agent 1
    confirmed there were no live edits after 20:15.
26. **`snap-native-inputs.py` N1d exited 1** because `| Select-Object -First 4` closed the pipe while it printed rows
    (BrokenPipe). The copy and its TSV had already completed (33 rows). Don't truncate its output with a pipe.
27. **Plume needs a newer d3d12.h** (native build run 1, 21:07-21:28).
    - `thirdparty/plume/plume_d3d12.cpp:505` returns `D3D12_HEAP_TYPE_GPU_UPLOAD` unconditionally in
      `toD3D12(RenderHeapType)`.
    - This machine has only Windows SDK 10.0.22621.0, whose d3d12.h lacks that enumerator. Its value is 5 in WinSDK
      >= 10.0.26100, the Agility SDK and DirectX-Headers. Plume configures with "D3D12 Agility SDK: OFF".
    - Nobody had compiled plume_d3d12.cpp on this machine before: the step-5 compile-one sweep covered only
      rexlego/src. Every rexlego/src TU waits behind plume, so run 1 stopped at [459/553] with only this error.
    - Fix S1+p2 (Agent 1's spec): `return static_cast<D3D12_HEAP_TYPE>(5);` on the same line, so the line count is
      unchanged. `prepare_plume.py --check` still passes, because no patch hunk is near line 505.
    - Behaviour is unchanged. Without the Agility SDK, plume never queries OPTIONS16, so
      `capabilities.gpuUploadHeap = uma`, and UMA devices take the custom-pool fallback (`gpuUploadHeapFallback`).
    - Agent 6 makes the same change in the live tree.
    - Run 2 (21:36:54-21:44:14): 438.8 s, 96 edges, exit 0, 0 errors. 206 warnings: 202 -Wdeprecated-declarations
      (native renderer) and 4 -Wunused-value (thirdparty miniz.h).
28. **The orchestrator's PreToolUse hook rejected one run_command** (exit 1, no reason given). It grepped
    plume_d3d12.cpp and `prepare_plume.py`, probably with a git subcommand string in the pattern. Simpler commands
    without such strings passed. Never bypass the hook.
29. **edit_file did not match a target that contained text with double backslashes** (the old RESUME block). Python
    splices (`splice-notes-top.py`) avoid that, and new notes use forward slashes in paths.

## Done (session 2)

1. devshell: clang 23.1.6, MSVC 14.40.33807, WinSDK 10.0.22621.0, CMake 3.28.3, Ninja 1.11.0.
   Deleted `toolchain/_downloads/*.tar.zst` (276 MB) and the stale `.parts/` (31.6 MB).
2. plume: gitlink `ceaeeee` is unfetchable, so it is on public pin `e0c8871` with 6 patches from
   `tools/gpu-aot/prepare_plume.py`. `--check` **PASS**. Plume submodules use `--depth 1` (100 s).
3. SDK `thirdparty/FidelityFX-SDK` is **initialised** at `eee08db` ("Linux fix"). Shallow fetch took
   983 s at ~115 KB/s. Agent 6 can use the FSR3 headers now (`sdk/include`); prebuilt DLLs are in
   `PrebuiltSignedDLL/`.
4. Snapshot `baseline/DimensionsRecomp` = `git archive` of 127e04b + SDK 2897c31, verified at 832 + 1338
   files. 24 SDK gitlinks and plume are junctions to the dev checkouts, so **simde, plume and
   FidelityFX are shared with dev**. `thirdparty/snapdragon-gsr` is empty: no URL, and nothing
   references it at 2897c31.
5. `build/sdk-dev` configured (configure-only; FidelityFX OFF; tests ON; 339 s; 2664 DB entries).
   `env/compile-one.ps1` is written and tested:
   - `clock.cpp` to an obj: 8.4 s
   - `-SyntaxOnly`: 3.5 s
   - fallback when the PCH is missing: 10.1 s
   Usage: `powershell -NoProfile -File env\compile-one.ps1 <file.cpp> -OutDir build\agentN\obj [-SyntaxOnly] [-Db <compile_commands.json>] [-Config Release] [-Target <obj-substr>] [-PrintOnly] [extra clang flags]`.
6. `build/sdk` configured (322.5 s; FidelityFX OFF, the same as dev, per Agent 1 16:48 (5)).
   **Build run 1 stopped at [929/1410] after 456.9 s.** The bundled Cygwin `tools/binutils/powerpc-none-elf-nm.exe`
   crashes with 0xC0000005 whenever its stdout is a *file* (cmd `>`, as in `cmake/ppc_test_pipeline.cmake`).
   Into a pipe it works. As a result, 7 `tests/ppc/bin/instr_*.map` edges failed. This is environmental
   (likely an old `cygwin1.dll` on Windows 26100); `as` and `ld` work.
7. Manifests are written: `baseline/DimensionsRecomp/rexlego/legodimensions_manifest.toml`
   (game_root `../../../game/disc`) and a dev copy. Agent 3 has `game/disc/Default.xex` + `.xexp` in place.

## Not done / found at the pause

- `python DimensionsRecomp/rexglue-sdk/scripts/prepare_simde.py --check` **FAILS** ("Native __m64
  streaming-store fix is missing", exit 2). Build run 1 compiled against unpatched SIMDe, so apply
  the fix before resuming. simde is not in my claim list, so `@@claim DimensionsRecomp/rexglue-sdk/thirdparty/simde/**` first.
  Ninja then recompiles the SIMDe users on its own.
- Plan change (Agent 1 16:48): the baseline game is **NATIVE_GPU=OFF** (README-dev step 4). The native ON
  inputs come from Agent 6 (J1) for a compile-only ON configure in `build/dev`. Copy
  `legodimensions.map` next to every staged exe.

## Exact next commands

```powershell
$R = '<workspace>'; Set-Location $R
# 0. SIMDe fix (after @@claim). simde is shared with baseline through the junction.
python DimensionsRecomp\rexglue-sdk\scripts\prepare_simde.py; python DimensionsRecomp\rexglue-sdk\scripts\prepare_simde.py --check
# 1. keep the run-1 logs (the codegen watcher keys on "END   build" in the steps file)
Rename-Item build\agent2\sdk-baseline-steps.txt sdk-baseline-steps-run1.txt; Rename-Item build\agent2\sdk-build.log sdk-build-run1.log
# 2. resume the SDK build past the PPC nm failures (run_command background task, NOT Start-Process)
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\build-sdk-baseline.ps1 -SkipConfigure -KeepGoing -CtestExclude '<ppc test regex from sdk-ctest-list.log>'
# 3. codegen watcher (second background task): waits for rexglue.exe, then runs codegen.
#    The log must show "XEX patch applied successfully ... new version: 0.0.23.3".
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\codegen-watch.ps1
New-Item -ItemType Junction DimensionsRecomp\rexlego\generated -Target $R\baseline\DimensionsRecomp\rexlego\generated
# 4. baseline game, NATIVE_GPU=OFF, x86-64-v3, Release, from baseline\DimensionsRecomp\rexlego into build\baseline.
#    Then stage the exe, rexruntime.dll, rexgpu-xenos.dll, PDBs and legodimensions.map into build\baseline-bin.
```

PPC follow-up, off the critical path: produce the 7 maps through a pipe, then add matching
`.ninja_log` entries (MurmurHash64A of the edge command), or report the PPC suite as blocked.

---

# Session 1 report (history): toolchain + baseline builds (PARTIAL)

Status at 12:35: **partial, stopped on the orchestrator's battery stop-plan.** The LLVM download
could not finish by 12:45, so per the plan nothing was built and the SDK submodule init was not
started. `env/devshell.ps1` is written and tested (VS x64 env, CMake, Ninja), but **clang is not
installed yet**. Do not announce the devshell until LLVM is extracted.

## What is installed and where

All paths relative to `games/lego-dimensions-recomp/`.

| Item | State | Notes |
|---|---|---|
| `env/devshell.ps1` | done, tested | VS 2022 x64 env (cached), CMake + Ninja on PATH, picks up `toolchain/llvm-*` automatically once extracted |
| `env/.cache/vsenv-x64.json` | generated | cached `vcvars64.bat` delta, machine-specific, rebuilt automatically if VS/MSVC changes (or `-Refresh`) |
| `toolchain/segdl.ps1` | done | resumable multi-connection curl downloader (range requests, numbered chunks, join plus SHA256 check) |
| `toolchain/_downloads/clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst.parts/` | **11.5%** | 13 chunk files, 31,652,927 of 276,226,344 bytes. Resume with the command below; keep `-Segments 10` |
| `toolchain/llvm-23.1.6/` | **missing** | extract after the download completes |
| `env/compile-one.ps1` | not written | needs `build/sdk/compile_commands.json` |
| `build/sdk`, `build/agent2/gpu-aot` | not created | no builds this session (stop-plan) |
| SDK submodules / `thirdparty/plume` | not initialised | stop-plan: init is heavy and the network is very slow (see below) |

## Versions on the machine (checked)

| Tool | Version | Path |
|---|---|---|
| Visual Studio 2022 Community | 17.10.35004.147 | `C:\Program Files\Microsoft Visual Studio\2022\Community` |
| MSVC | 14.40.33807 | `...\VC\Tools\MSVC\14.40.33807\bin\HostX64\x64` |
| Windows SDK | 10.0.22621.0 | `C:\Program Files (x86)\Windows Kits\10` (rc.exe, mt.exe x64) |
| CMake | 3.28.3-msvc11 | VS bundled `...\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin` |
| Ninja | 1.11.0 | VS bundled `...\CommonExtensions\Microsoft\CMake\Ninja` |
| git | 2.56.1.windows.1 | `C:\Program Files\Git\cmd` |
| tar | bsdtar 3.8.9 (libarchive, has zstd and xz) | `C:\Windows\System32\tar.exe` |
| PowerShell | Windows PowerShell 5.1.26100 | agents' shell |
| clang | **none on PATH**. `VC\Tools\Llvm` exists but holds no `clang.exe` (VS clang component not installed) | |
| Free disk on C: | 63.3 GB | |

CMake 3.28 satisfies the SDK (`cmake_minimum_required(3.25)`, presets v6). The SDK requires
**Clang >= 18** (`rexglue-sdk/CMakeLists.txt:119-122`), stricter than the 17 in README-dev.

## LLVM choice

- Latest stable per the GitHub API (`releases/latest`): **LLVM 23.1.6**, published 2026-11-17.
- Chosen archive: `clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst`, 276,226,344 bytes,
  sha256 `7623f582089983c1cb51030cf1996514b19464e5669099571b399e8543770155` (GitHub asset digest).
- Alternatives: `.tar.xz` 901,284,676 bytes, sha256 `16af05919cf36958dfb4ddaa4fc4d9d4ff577f5daeb76bc112ea49cd8ced82b2`;
  `LLVM-23.1.6-win64.msi` 639,686,385 bytes.
- The zst is 3.3x smaller, and the system tar can unpack it. That gap is bigger than compression
  alone would explain, so after extracting, **check** that `bin/` has clang, clang++, clang-cl,
  lld-link, llvm-ar, llvm-ranlib, llvm-rc, llvm-mt and clang-scan-deps, and that
  `lib/clang/23/include` and `lib/clang/23/lib/windows/clang_rt.builtins-x86_64.lib` exist.
  If anything is missing, use the `.tar.xz` instead.

## Network (why the download did not finish)

| Measurement | Result |
|---|---|
| Wi-Fi link speed | 866.7 Mbps |
| Single curl, GitHub release asset | 66 KB/s (8 s sample); 23.1 MB in 695 s (about 33 KB/s average) |
| Cloudflare speed test, run at the same time | 21.6 KB/s |
| Interface counters | rx 94 KB/s, **tx 113 KB/s** (12 agents' API traffic) |
| 10 parallel range connections (segdl) | about 75 KB/s in total, 0.7 MB in 4 min: **no gain** |

The bottleneck is the shared link (probably the busy uplink), not one connection. At this rate the
remaining 232 MB of LLVM takes about 55 min. Full clones of the SDK submodules (FFmpeg, SDL3,
tracy, imgui, glslang, spirv-tools, ...) would take many hours. Next session, either use a
faster or quieter network, or allow `--depth 1` for the submodule clones (needs orchestrator OK,
because the granted command is `git submodule update --init --recursive`).

## devshell.ps1: test results

Command: `powershell -NoProfile -Command ". games/lego-dimensions-recomp/env/devshell.ps1; ..."`, run from the workspace root.

- First load (cache miss, runs `vcvars64.bat`): 16.05 s wall for the whole child PowerShell (bare startup 1.32 s).
  With `-Refresh -Jobs 3`, after the final edit: 13.47 s.
- Cached load: 3.01 s wall including startup. After the final edit, which skips `vswhere` when the cache is valid,
  it measured 3.24 s and 3.48 s against a bare startup of 1.15 s. No measurable gain: the shared CPU is noisy and
  the PS 5.1 JSON parse dominates.
- Tested on Windows PowerShell 5.1 only. `pwsh` (PowerShell 7) is not installed.
- Resolves `cl`/`link` from MSVC 14.40.33807 HostX64\x64, `rc`/`mt` from WinSDK 10.0.22621.0 x64,
  and `cmake`/`ninja` from VS. INCLUDE has 8 entries.
- Sets `CMAKE_GENERATOR=Ninja` and `CMAKE_BUILD_PARALLEL_LEVEL=4` (`-Jobs N` overrides; verified with `-Jobs 2`),
  plus `LEGO_ROOT`, `LEGO_GAME`, `LEGO_SDK`, `LEGO_SDK_BUILD` and `LEGO_LLVM`.
- Sourcing it again in the same session does not grow PATH (43 entries before and after).
- With no LLVM present it prints a warning and leaves `CC`/`CXX` unset (observed). Once
  `toolchain/llvm-<ver>/bin/clang.exe` exists it puts that `bin` first and sets `CC=clang`, `CXX=clang++`
  (not yet exercised).
- Only environment variables change. The script runs in its own scope, so no variables or functions leak into the caller.

## Exact commands run (in order)

```powershell
# latest release + asset digests
Invoke-RestMethod https://api.github.com/repos/llvm/llvm-project/releases/latest
Invoke-RestMethod https://api.github.com/repos/llvm/llvm-project/releases/tags/llvmorg-23.1.6
# single-connection download (killed after 695 s, 23,097,344 bytes kept as chunk seg000_000)
curl.exe -L --fail --retry 3 -s -S -o clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst https://github.com/llvm/llvm-project/releases/download/llvmorg-23.1.6/clang%2Bllvm-23.1.6-x86_64-pc-windows-msvc.tar.zst
# segmented download (stopped at 12:30 on the stop-plan)
powershell -NoProfile -ExecutionPolicy Bypass -File toolchain\segdl.ps1 -Url <same url> -Size 276226344 -OutFile toolchain\_downloads\clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst -Segments 10 -Sha256 7623f582...0155
# devshell test (see above)
```

Read-only inspection: `git log`/`git describe`/`git submodule status`/`git ls-files -s` in both repos, plus `vswhere`.

## Failures and fixes

1. **Slow network** (see table). Fix tried: the segmented downloader, which did not help. Stopped on the stop-plan;
   partial data is kept and resumes.
2. **My cleanup command killed its own shell**: a `CommandLine -like '*segdl.ps1*'` filter matched the
   cleanup command itself. Re-ran it excluding `$PID`. No other effect.
3. **Predicted, not yet hit:** in `rexglue-sdk`, `git submodule status` fails with
   `fatal: no submodule mapping found in .gitmodules for path 'thirdparty/FidelityFX-SDK'`. The index has a
   gitlink (`160000 eee08db1688ac3d1275a70b728f4a8ba22914213`) with no `.gitmodules` entry. A bare
   `git submodule update --init --recursive` will very likely die on it ("No url found for submodule path").
   Fix: pass the mapped paths explicitly (command below). FidelityFX is optional (`REXGLUE_ENABLE_FIDELITYFX=OFF`).

## Findings that affect the next session

- **SDK artifacts ignore the binary dir.** `rexglue-sdk/CMakeLists.txt:258-260` sets
  `CMAKE_{RUNTIME,LIBRARY,ARCHIVE}_OUTPUT_DIRECTORY` to `${REXGLUE_ROOT}/out/${REX_PLATFORM}` as normal
  variables, so a `-D` on the command line cannot override them. Even with `-B build/sdk`, the libs, exes and DLLs land
  in `DimensionsRecomp/rexglue-sdk/out/win-amd64/<Config>/` (git-ignored). Consequences: claim
  `DimensionsRecomp/rexglue-sdk/out/**` for the baseline build, and **other agents must not link SDK
  targets in their own trees at the same time**, because they would overwrite the same files. Object-only
  checks through `compile-one.ps1` are safe.
- The preset sets `binaryDir` and `CMAKE_INSTALL_PREFIX` inside the source tree. Override both on the command line (below).
- `REXGLUE_BUILD_TESTS` is OFF by default. The tests are `tests/unit` and `tests/ppc` (PPC asm, bundled `tools/binutils`);
  `tests/regression` is Linux-only.
- `thirdparty/CMakeLists.txt` adds xxHash, disasm, fmt, spdlog, utfcpp, vulkan-headers, VMA,
  vulkan-loader (EXCLUDE_FROM_ALL), moltenvk, sdl3, spirv-headers, glslang and catch2, plus FidelityFX through a guarded include.
- gpu-aot: all 19 checks listed in its `CMakeLists.txt` have sources present. The folder has 102 `test_*.cpp`;
  the rest are not in the portable list. It only needs a C++20 compiler, no SDK or submodules.
- To verify next session: whether CMake 3.28 writes a usable `compile_commands.json` for **Ninja Multi-Config**
  and which config's flags it holds. `compile-one.ps1` must select the Release entries (`/Release/` object
  paths, `-O3`). If 3.28 falls short, drop a newer portable CMake into `toolchain/cmake-*`; devshell prefers it automatically.

## Resume plan (next session, in order)

```powershell
$R = "<workspace>"
# 1. resume the LLVM download (absolute paths; must keep -Segments 10)
powershell -NoProfile -ExecutionPolicy Bypass -File $R\toolchain\segdl.ps1 `
  -Url "https://github.com/llvm/llvm-project/releases/download/llvmorg-23.1.6/clang%2Bllvm-23.1.6-x86_64-pc-windows-msvc.tar.zst" `
  -Size 276226344 -OutFile "$R\toolchain\_downloads\clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst" `
  -Segments 10 -Sha256 7623f582089983c1cb51030cf1996514b19464e5669099571b399e8543770155
# 2. extract, rename (no '+' in the path), check the file list from "LLVM choice"
Set-Location $R\toolchain; tar -xf _downloads\clang+llvm-23.1.6-x86_64-pc-windows-msvc.tar.zst
Rename-Item clang+llvm-23.1.6-x86_64-pc-windows-msvc llvm-23.1.6
. $R\env\devshell.ps1; clang++ --version      # then post "devshell ready"
# 3. submodules (explicit paths because of the unmapped FidelityFX-SDK gitlink)
Set-Location $R\DimensionsRecomp\rexglue-sdk
$paths = git config -f .gitmodules --get-regexp '\.path$' | ForEach-Object { ($_ -split ' ', 2)[1] }
git submodule update --init --recursive --jobs 8 -- $paths
Set-Location $R\DimensionsRecomp; git submodule update --init thirdparty/plume
# 4. SDK baseline (claim DimensionsRecomp/rexglue-sdk/out/** first)
. $R\env\devshell.ps1
cmake --preset win-amd64 -S $R\DimensionsRecomp\rexglue-sdk -B $R\build\sdk `
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DREXGLUE_BUILD_TESTS=ON -DCMAKE_INSTALL_PREFIX=$R/build/sdk/install
cmake --build $R\build\sdk --config Release -j 12
cmake --install $R\build\sdk --config Release
ctest --test-dir $R\build\sdk -C Release --output-on-failure
# 5. env/compile-one.ps1 <source> -OutDir <dir> [-SyntaxOnly]: look up the Release entry for <source> in
#    build/sdk/compile_commands.json, rewrite -o (and any -MF/-MD dep file) into -OutDir, and for
#    -SyntaxOnly replace "-c ... -o ..." with -fsyntax-only. Then post "SDK built; compile-one ready".
# 6. gpu-aot portable checks
cmake -S $R\DimensionsRecomp\tools\gpu-aot -B $R\build\agent2\gpu-aot -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=clang++
cmake --build $R\build\agent2\gpu-aot -j 4
ctest --test-dir $R\build\agent2\gpu-aot --output-on-failure
```

## What is left

LLVM download (88.5%) and extract; the "devshell ready" announcement; SDK submodule init plus `thirdparty/plume`;
the SDK configure, build, install and tests (unit plus PPC asm) with timings; `env/compile-one.ps1`; the gpu-aot
portable checks; and filling this report in with build times and test results.
