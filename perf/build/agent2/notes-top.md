# Agent 2: build pipeline - RESUME NOTE (task #1 re-issued after the agy-grid restart; updated 01:27)

**Task #1 steps 1-6 are DONE and verified (`@@done 1` sent about 19:57-20:00); step 6 (the PPC map fix) is below.
Batch 1 (S1) and batch 2 (S2) are DONE and announced. Window 3 is over (19/19 OK, 00:13-01:16). Since 01:16 Agent 1
has paused everyone for the agy-grid relaunch: no builds, no game runs, no new work. Nothing of mine is running.
Next: build B (Agent 9's codegen option) and S3, in the order Agent 1 sets.**

**Checkpoint for the relaunch (01:22-01:27, hashing only)**
- **Live vs S2 (`snap1/STATE-S2-2315.tsv`):** `python build\agent2\snap-patch.py plan CHK build\agent2\CHK-rules.txt`.
  The only rule is `!**`, so nothing is selected and nothing is copied. Output `snap1/PLAN-CHK-0122.txt`, sha256
  8E133F630804C2AD....
  - Counts: the live walk has 23843 files: 23821 same, 22 differ, 0 new since the cut, 0 deleted.
  - The 48 native inputs (rexlego/out, research/dxc) are all the same, and nothing under rexlego/out or research is
    newer than 23:15.
  - Method: size+mtime are checked against STATE's live columns, and changed files are re-hashed (2 were).
  - **Changed since the cut** (2, both at 00:06:15, not mine): `rexglue-sdk/src/kernel/xam/xam_ui.cpp` (live
    0a314946fdb9fe1e) and `rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_hal.cpp` (live ab359e1d6c4da1b9).
  - **Held back at S2 and unchanged since** (20 files: the A9 #15 codegen EXCLUDE rows, all in rexglue-sdk): 17
    modified, plus 3 untracked new files (`src/codegen/builders/flush_mode.h`, `tests/ppc/asm/instr_cr_so_fold.s`,
    `tests/ppc/opt_config.toml`). The full list is in the PLAN file.
  - **Already in S2:** the other untracked files git shows have the same hash in S2: `include/rex/threading_*.h`,
    `rotate_mask.h`, 2 ppc asm tests, 9 gpu_native headers, `plume-winsdk-compat.patch` and the tools/native-cpu
    files.
  - **Not in STATE:** `rexlego/generated`, a junction to the baseline (887 files, newest 11-21 18:15:54).
- **plume:** HEAD is e0c8871b930d..., `prepare_plume.py`'s `PIN` (line 9).
  - The superproject's gitlink ceaeeee0f7e9... is not in the public zolaware/plume clone (`git cat-file`: not a valid
    object).
  - The clone was made on 11-21 at 16:06:38 and checked out to the pin at 16:20:43 (reflog). That was my task #1
    setup, before the sprint.
  - The dirty files `plume_d3d12.h` (16:21:37, 2F8B444C...) and `plume_vulkan.cpp` (16:21:36, 71938A4C...) come from
    prepare_plume's patches during that setup.
  - `plume_d3d12.cpp` (564568D4...) is S1+p2, my sprint edit: the live copy was made at 21:57:57 and keeps snap1's
    mtime, 21:34:50. It equals S2.
- **My live-tree edits since the cut:** none in `DimensionsRecomp/`. Outside it:
  - `perf-notes/agent7-s3-proposal.md` §(b) at 00:33 (459145C2...). Its owner has edited it since (AAAF51FB... at
    01:22:09).
  - These notes, and `build/agent2/**` (B tools, `CHK-rules.txt`, `snap1/PLAN-CHK-0122.txt`).
- **First step after the relaunch:** re-read this block, then finish the B tool prep:
  - compile `codegen-frozen2.exe`;
  - run `patch-b-tools.py` and diff the results against `*.pre-B`;
  - run gen-check and snap-gate in default mode on snap1.
  None of that builds anything. After it, run B (from batch-nolr) or S3, in the order Agent 1 sets.

**Staged bins** (in `build/agent2/`; file counts exclude MANIFEST.txt; run details are in "Batches 1 and 2: run
details" below)

| Dir | Staged | Files, size | MANIFEST | exe sha256 | Notes |
|---|---|---|---|---|---|
| `devoff1-bin` | 21:08 | 7, 214.2 MB | all PASS, 1E81AA5E... | D95273C9... | S1 OFF |
| `native-bin` | 21:48 | 8, 363.5 MB | 48/48, 91F2F817... | 3B329E95... | S1 native, fingerprint `befeb1184e6c7abc` |
| `devoff2-bin` | 23:18:53 | 7, 214.3 MB | 49/49, B87DC2D2CA22379F... | 7F0B1C1C84BC66FF... | S2 OFF; map 3A7BEEF03A527FC4... |
| `native2-bin` | 23:22:38 | 8, 363.7 MB | 72/72, D6E7F14F23373FA7... | 5D1B2DC655616027... | S2 native, fingerprint `b7cc74f980e016c3`; map 1FFB7EA997DFCBE7... |

- Both S2 bins: rexruntime.dll 1C45C86977EC594C... (has `audio_shutdown_detach_worker`), rexgpu-xenos.dll
  77A5300B885C5274.... Both S1 bins: rexruntime FDB315DC..., rexgpu-xenos BFE1DF8B.... The staged bins carry no PDBs.
- S2 = Agent 10's `build/agent10/b3/S2-include.tsv` (E1FF0497...; 19 INCLUDE, 20 EXCLUDE = A9 #15 B files), applied
  23:15:03, verify PASS. devoff2 run 218.9 s; native2 run 209.9 s (build 124 s, 23 edges).

**Live tree edit (my only one)**
- 21:57:57: live `DimensionsRecomp/thirdparty/plume/plume_d3d12.cpp` B88E4E86... -> 564568D4... (Agent 1's step 1).
  It is a hash-checked copy of `build/agent2/snap1` S1+p2; the backup is
  `build/agent2/live-backup/plume_d3d12.cpp.B88E4E86`. Agent 6 was told at about 22:44 that this is my final live
  edit.

**Build B (Agent 9's codegen option): prepared, NOT run**
- **Inputs: only `build/agent9/install/batch-nolr`** (Agents 9 and 10 confirmed). Never `install/batch`: its skip_lr
  is unsafe (Agent 10, Review 4). Config sha256 E60EAF1CEB575572...; SHA256SUMS.txt sha256 24CE1493FB8DAE37... (872
  files, 481,074,943 B); 430 TUs (last `legodimensions_recomp.429.cpp`), so the snap gate expects 432. Recipe:
  `perf-notes/agent9-codegen.md`, "Session 2: regen+build recipe", steps 2-6. Agent 10's diff: only LR writes differ
  from the 23:28 tree.
- **Design:** snapB = a full copy of snap1 at S2 in `build/agent2/snapB`; its `rexlego\generated` is a real dir and
  every write stays under snapB. Apply batch-nolr; gate it (SHA256SUMS 872/872, config hash, 432 TUs); run
  `gen-check.py --base build/agent9/install/batch-nolr/generated`; build snapB-off against `snap1-sdk/install` (the
  SDK stays on snap1); stage `build/agent2/snapB-bin`; compare with devoff2-bin. B is timed or merged only after
  Agent 10's review clears it.
- **Tool state (23:39-23:47):** originals backed up as `build/agent2/*.pre-B` (gen-check.py D7F76B8A..., snap-gate.py
  BB2E4A80..., build-snap.ps1 01B075B7..., stage-snap-bin.ps1 0C5F0C76..., stop-snap.ps1 14A36888...).
  - Rewritten: `gen-check.py` (adds `--base/--snap/--snap-rex/--base-rex`; defaults unchanged), `snap-gate.py` (TU
    count from the generated `default/sources.cmake`; it was a hardcoded 440), `stop-snap.ps1` (also stops run-b.ps1,
    prep-b.py and snapB work).
  - New: `prep-b.py`, `run-b.ps1`, `codegen-frozen/codegen_frozen2.c` (checks every TU listed in sources.cmake; NOT
    compiled yet), `patch-b-tools.py` (NOT run yet; adds `-SnapDir/-GameBin/-CodegenExe/-GenBase` to build-snap.ps1
    and `-GameTree/-OutDir/-GameSnap/-CodegenNote/-ManifestNotesFile/-CompareBin` to stage-snap-bin.ps1).
  - py_compile passes for the 4 .py files; nothing has been run. snapB, snapB-off and snapB-bin don't exist (checked
    00:42).
- **After the window, before B:** compile `codegen-frozen2.exe`; run `patch-b-tools.py` and diff both scripts against
  `*.pre-B`; run gen-check.py and snap-gate.py in default mode against snap1 (expect PASS, gate 440).
- Promised: Agent 1, no I/O in window 3, then re-sync snapB from snap1 (S2), apply batch-nolr, gate, and build B only
  when scheduled; Agent 9, B only from batch-nolr.

**S3 (Agent 1 plans it after the window)**
- Candidates: Agent 11's #27; the native startup fix; Agent 12's #22 default-ON flip; B. Agent 10's intrinsics.h and
  math.h edits and Agent 12's closure headers (xmemory.h, logging/api.h, logging/macros.h) force a full SDK and game
  rebuild.
- Same pipeline as S2: owner TSV -> `make-rules-from-tsv.py` -> `snap-patch.py plan|apply|verify S3` -> SDK (with a
  configure) -> devoff3 -> native3, with the same gates and staging; report sha, fingerprint and checks for each.
- **Native startup fix.** Native throws at boot on the unregistered `present_fsr_*` keys when
  `native_settings_frontend=true`, because every SDK build here has FidelityFX off; window 3 runs native with
  `--native_settings_frontend=false`. Agent 7's `perf-notes/agent7-s3-proposal.md` now (00:20) recommends (a),
  Agent 6's Fix A (a rexlego source patch), for S3. (b), an FFX-headers rexruntime for native only, stays available.
- **(b), if Agent 1 picks it:** my corrected build plan is §(b) of that file (spliced 00:33; file sha256
  459145C2D0FB4059...):
  - reuse `snap1-sdk`, adding one `-DREXGLUE_FIDELITYFX_SOURCE_DIR=<abs snap1>/DimensionsRecomp/rexglue-sdk/
    thirdparty/FidelityFX-SDK`;
  - build `--target rexruntime` only and never install; save the DLL/PDB pair to `build/agent2/ffx3-rt/`;
  - stage `native3ffx-bin` as a copy of native3-bin with only the runtime swapped;
  - ~2-3 min (the reconfigure is unmeasured; budget 30-60 s).
  - Before it, `build-snap.ps1` must pass `-UREXGLUE_FIDELITYFX_SOURCE_DIR` on every OFF SDK configure and refuse to
    install while CMakeCache has a non-empty value, so S4 must reconfigure.

**Scripts** (all in `build/agent2/`)
- `snap.py` (full snapshot); `snap-patch.py` (plan, apply, verify and revert of hash-logged patches onto snap1);
  `make-rules-from-tsv.py` (owner TSV -> rules); `build-snap.ps1` (-Phase sdk|game|all, -Native, -Tag, -Jobs,
  -Affinity, -SkipConfigure, -KeepGoing, -PrelinkJobs, -NoBuild; runs gen-check and the gate; a step fails on FAILED
  or ninja error lines); `run-s2.ps1 -Stage off|native`; `gen-check.py`; `codegen-frozen/codegen-frozen.exe` (the
  pinned 0.0.23.3 codegen stand-in); `snap-gate.py`; `stage-snap-bin.ps1` (-Variant off|native; -ExeStrings and
  -RuntimeStrings take comma lists); `snap-native-inputs.py`; `stop-snap.ps1`; `splice-notes-top.py`; the B tools.
- If Agent 1 opens a window mid-build, run `powershell -NoProfile -ExecutionPolicy Bypass -File
  build\agent2\stop-snap.ps1` within about 2 min, then re-run the same stage later; ninja resumes.
- Keep every intermediate (snap1, snap1-sdk, snap1-off, snap1-on, the backups, the staged bins and any `*.pre-S2` or
  `*.pre-B`) until Agent 1 says otherwise. Free C: 258.9 GB at 00:42.
- agy-grid delivers only the `@@to` line itself, so every message is ONE line; the
  details live in this file.
