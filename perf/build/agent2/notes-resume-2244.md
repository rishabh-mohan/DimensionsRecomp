# Agent 2: build pipeline - RESUME NOTE (task #1 re-issued after the agy-grid restart; updated 22:44)

**Task #1 steps 1-6 are DONE and verified (`@@done 1` sent about 19:57-20:00); step 6 (the PPC map fix) is below.
Batch 1 is DONE (`build/agent2/devoff1-bin` 21:08, `build/agent2/native-bin` 21:48; Agent 1 confirmed both).
Batch 2 (S2) is PREPARED and waits for the end of QUIET WINDOW 2 (Agent 1, from 22:28): no plan, apply or builds
until Agent 1 announces the end. Nothing of mine is running.**

**Batch 2 (S2): what runs when window 2 ends**
- **Scope = Agent 10's owner list only**: `build/agent10/b3/S2-include.tsv` (22:31, sha256 E1FF0497...). 19 INCLUDE
  rows: A7 #20 `device.cpp` (contains p1), `device.h`, `fps_counter.h`; A6 `draw.cpp`, `pipeline_snapshot.h`;
  A5 batch 2 `buffers.cpp`, `textures.cpp` and 6 headers incl. the NEW `upload_legacy_paths.h` (all of these in
  `rexlego/src/gpu_native/`); A12 #22 `rexglue-sdk/src/audio/audio_system.cpp` and
  `rexglue-sdk/include/rex/audio/audio_system.h`; A6 #26 `tools/gpu-aot/prepare_plume.py`, `test_prepare_plume.py`
  and the NEW `patches/plume-winsdk-compat.patch`; A2 p2 `thirdparty/plume/plume_d3d12.cpp` (live already equals
  snap1 S1+p2, so it is a hash pin, not a copy). The 20 EXCLUDE rows (A9 #15 B codegen files, not final) stay at
  S1, and so does every file not on the list (S1 plus p1/p2).
- Rules: `build/agent2/S2-rules.txt`, generated 22:40:14 by `python build\agent2\make-rules-from-tsv.py
  build\agent10\b3\S2-include.tsv e1ff04974373119b build\agent2\S2-rules.txt` (include = `owner | rel | live
  sha256`, exclude = `!owner | rel`). All 15 pre-checked files matched their live hashes. The new literals
  (`LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD`, `LEGO_NATIVE_FPS_CELL_RECTS`, `LEGO_NATIVE_TEXTURE_STAGING_POOL`,
  `audio_shutdown_detach_worker`) are in live and absent from snap1.
- Commands, in order (from R):
  1. `python build\agent2\snap-patch.py plan S2 build\agent2\S2-rules.txt`. Expect COPY 18, HELD BACK 20 (all
     'excluded') and 0 errors. A 'not selected' file is an unexpected live change: it stays at S1; tell Agent 1.
  2. `python build\agent2\snap-patch.py apply S2 build\agent2\S2-rules.txt`, then `... verify S2` (RESULT: PASS).
     Replaced S1 files are backed up in `build/agent2/snap1-backup-S2/`; the log is `snap1/PATCHES-S2.tsv` plus
     `STATE-S2-*.tsv` and `DIFF-S2-*.txt`.
  3. Background: `powershell -NoProfile -ExecutionPolicy Bypass -File build\agent2\run-s2.ps1 -Stage off`. This
     builds and installs the SDK in snap1-sdk, builds the game in snap1-off with -SkipConfigure, and stages
     `build/agent2/devoff2-bin`.
  4. Then `... run-s2.ps1 -Stage native`: snap1-on WITH configure, staged to `build/agent2/native2-bin`.
  Logs: `build/agent2/snap2-run.txt`, `snap2-steps.txt`, `snap2-stage-<stage>.log`. run-s2 exit codes: 0 done,
  10 build failed, 11 relink failed, 12 rexruntime.dll still differs, 13 stage failed.
- **Why native2 re-configures:** snap1-on has a CONFIGURE_DEPENDS glob on `rexlego/src/gpu_native/*.h`
  (rexlego/CMakeLists.txt:731), and S2 adds a header. The configure runs the new 7-patch `prepare_plume.py --check`
  (FATAL_ERROR on failure), which nobody has run with p2 yet. If it fails (build-snap exit 21, so run-s2 exit 10;
  see `snap2-native-configure.log`), tell Agents 6 and 1 at once and do not edit Agent 6's files. devoff2 is
  unaffected.
- **rexruntime contingency:** the audio change lands in rexruntime.dll, which reaches a game dir only through the
  exe's POST_BUILD copy. If `<tree>\rexruntime.dll` differs from `snap1-sdk\install\bin\rexruntime.dll` after the
  game phase, run-s2 renames the exe and map to `*.pre-S2` and re-runs the game phase as tag `snap2r`, which
  relinks and re-copies.
- Stage checks: both stages pass `-RuntimeStrings` (the audio cvar name and its description); native also passes
  `-ExeStrings` (the 3 LEGO_NATIVE_* names). The native fingerprint WILL change from S1's `befeb1184e6c7abc`,
  because device.h, device.cpp, draw.cpp and prepare_plume.py are fingerprint inputs.
- If Agent 1 opens a new window mid-build, run `powershell -NoProfile -ExecutionPolicy Bypass -File
  build\agent2\stop-snap.ps1` within about 2 min (it also kills run-s2), then re-run the same stage later; ninja
  resumes.
- ETAs from the end of the window: applied +3 min, SDK installed +8, devoff2 staged +15, native2 staged +30.

**Live tree edit (my only one)**
- 21:57:57: live `DimensionsRecomp/thirdparty/plume/plume_d3d12.cpp` B88E4E86... -> 564568D4... (Agent 1's step 1).
  It is a hash-checked copy of `build/agent2/snap1` S1+p2; the backup is
  `build/agent2/live-backup/plume_d3d12.cpp.B88E4E86`. Agent 6 was told at about 22:44 that this is my final live
  edit.

**Batch 1 (S1): done**
- **S1** was taken at 20:41:57 (`python build\agent2\snap.py S1`). Manifest: `build/agent2/snap1/MANIFEST-S1-2041.tsv`,
  sha256 f81b1499481ee903.... Patches are logged in `snap1/PATCHES-S1.tsv`:
  - **p1** (20:55): Agent 7's perf-csv-rows `device.cpp` 4C15043E -> 4DC63FA0, for the native build only.
  - **p2** (21:34): `plume_d3d12.cpp` B88E4E86 -> 564568D4. Line 505 becomes `static_cast<D3D12_HEAP_TYPE>(5)`
    (problem 27).
  - Native inputs N1 (11 files), N1i (4) and N1d (`research/dxc-1.9.2609`, 33) match Agent 6's table
    (`snap1/NATIVE-INPUTS-*-2055.tsv`). S1 has Agent 12's closure headers (checked 21:37).
- SDK (`snap1-sdk`, incremental): 269.6 s at -j10; install 50.9 s into `snap1-sdk/install`.
- devoff1 (`snap1-off`): game 789.6 s at -j10, 0 errors. Staged at 21:08 to `devoff1-bin`: 7 files, 214.2 MB, all
  PASS; MANIFEST sha256 1E81AA5E...; exe 170,334,720 B, D95273C9....
- native (`snap1-on`, configured 20:58): run 1 stopped at [459/553], on plume only. Run 2 after p2: 438.8 s, exit 0
  (202 -Wdeprecated-declarations, 4 -Wunused-value). Staged at 21:48 to `native-bin`: 8 files, 363.5 MB, 48/48 PASS;
  MANIFEST 91F2F817...; exe 315,745,280 B, 3B329E95..., fingerprint `befeb1184e6c7abc`; map 48428DB0...;
  rexruntime FDB315DC... and rexgpu-xenos BFE1DF8B..., the same files as in devoff1-bin.

**Scripts** (all in `build/agent2/`)
- `snap.py` (full snapshot); `snap-patch.py` (plan, apply, verify and revert of hash-logged patches onto snap1);
  `make-rules-from-tsv.py` (owner TSV -> rules); `build-snap.ps1` (-Phase sdk|game|all, -Native, -SkipConfigure,
  -NoBuild; runs the gen-check and gate steps; a step fails on FAILED or ninja error lines); `run-s2.ps1` (one S2
  stage end to end); `gen-check.py` (886/886 generated files equal the baseline's); `codegen-frozen/codegen-frozen.exe`
  (the pinned 0.0.23.3 codegen stand-in); `snap-gate.py`; `stage-snap-bin.ps1` (-Variant off|native;
  -ExeStrings/-RuntimeStrings take comma lists); `snap-native-inputs.py`; `stop-snap.ps1`; `splice-notes-top.py`.
- Keep every intermediate (snap1, snap1-sdk, snap1-off, snap1-on, the backups, the staged bins and any `*.pre-S2`)
  until Agent 1 says otherwise. Free C: about 264 GB at 22:41.
- agy-grid delivers only the `@@to` line itself, so every message is ONE line; the
  details live in this file.
