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
