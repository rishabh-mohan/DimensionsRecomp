# HANDOFF: Agent 2 (snapshot builds and staged bins) at the project pause

Agent 2 wrote this on 2026-11-23 for board task #28, before the pause that starts around 13:00 and lasts a few days to a week. Every path is relative to the workspace root. `<R>` stands for the workspace root as an absolute path, which appears only where a tool needs an absolute path. Companion files:

- `build/agent2/COMMIT-CHECK.md`: shows that the committed trees equal the snap4b source (PASS).
- `build/agent2/PENDING-DIFFS.md`: lists the candidate diffs that are not in the committed trees. Its detailed annex, with sources, is `build/agent2/pending/PENDING-DIFFS-draft.md`.

## 1. What I own

- **`build/agent2/**`:** the snapshot trees, their build dirs, the staged bins, my scripts, checks, logs and notes backups.
- **`perf-notes/agent2-baseline.md`:** my running notes, with the newest entries at the top. Its RESUME block (lines 1-38) dates from 11-22 22:56 and is partly stale; see 4.6.
- **`build/baseline` and `build/baseline-bin`:** made by my scripts (`build/agent2/build-game-baseline.ps1` and `build/agent2/stage-baseline-bin.ps1`). They are the unpatched reference build (game 127e04b + SDK 2897c31). Keep them.
- **Not mine:**
  - the live repos `DimensionsRecomp/` and `DimensionsRecomp/rexglue-sdk/`: I never write them, and only Agent 1 commits or pushes;
  - every other agent's `build/agentN/`.

## 2. State at the pause

### 2.1 Committed trees

- **Commits:** `DimensionsRecomp` b0bd3b4 (parent 1bd322e) pins `rexglue-sdk` 5350b1d (parent 3bb65bb). Together they hold S4b + S4c with C1 v3: the 16 files listed in `build/agent2/s4b/HASHES.txt`. Agent 1 copied them from snap1 at 05:40 on 11-23 and committed them.
- **COMMIT-CHECK (11-23 06:06): PASS.**
  - Every tracked file in scope (773 game + 1347 SDK) is identical in the working tree, in HEAD, in the index and in `build/agent2/snap1`.
  - `diff-tree HEAD^ HEAD` changes exactly the 16 HASHES rows plus the SDK gitlink.
  - 71 tracked files sit in top-level dirs that snap1 never copied (installers, docs, .github, ...). They are untouched and clean.
- **Re-checked at 06:29-06:33:** both HEADs are unchanged. `git status --untracked-files=no` lists only the submodule entries. Porcelain v2 flags `rexglue-sdk` S.M., `thirdparty/plume` SCM. and `thirdparty/simde` S.M. Inside the submodules, only the plume and simde files below are modified.
- **Submodule edits, uncommitted by design** (Agent 1, `perf-notes/SESSION2.md` L3310). Every snapshot build since S3 used them, and both can be rebuilt from tracked files:
  - `DimensionsRecomp/thirdparty/plume`: 3 files on e0c8871.
    - The tracked `DimensionsRecomp/tools/gpu-aot/prepare_plume.py` (PIN e0c8871) rebuilds them from the 7 tracked `tools/gpu-aot/patches/plume-*.patch`.
    - On 11-23, `prepare_plume.py --check` passed (06:24), and `build/agent2/plume-rebuild-check.py` showed that the PIN plus the 7 patches give exactly the 3 live files (06:27).
    - The game's plume gitlink is ceaeeee0, which is not in the local clone; the checkout is at e0c8871. Agent 1's note `perf-notes/agent1-pause-state-lines.md` L128-130 says "Do NOT commit the plume pointer".
  - `DimensionsRecomp/rexglue-sdk/thirdparty/simde`: 1 file (`simde/x86/sse.h`). The edit is byte-identical to the tracked `rexglue-sdk/patches/simde-native-m64-stream.patch`, which `rexglue-sdk/scripts/prepare_simde.py` applies.
  - Reference copies of both patches are in `build/agent2/pending/` (PENDING-DIFFS.md §3).

### 2.2 Staged bins

Each bin is `build/agent2/<bin>/`. Its `MANIFEST.txt` rows are name, size, mtime, sha256 and source; the header names the snapshot STATE file and the patch tags.

| bin | level | staged | MANIFEST sha256 (16) | exe sha256 (16) | native GPU fingerprint | checks |
|---|---|---|---|---|---|---|
| devoff4b-bin | S4b + S4c, OFF (#24 GPU wait back-off is in OFF builds only; every new switch OFF) | 11-22 20:49 | DE11A914079D7DF7 | DFBE1D43B28861A6 | n/a | MANIFEST 102 PASS / 0 FAIL; map check PASS (31 hooked, by name and object); W5 inputs re-hashed unchanged |
| native4b-bin | S4b + C1 memory_watch.cpp, native | 11-22 22:40 | B63769FE46CC0459 | DC6484C224585E54 | 9b40acbbef4c57b3 (= Agent 4's step 1b) | MANIFEST 124 PASS / 0 FAIL / 46 NOTE; map check PASS (109 hooked; subagent AGREE) |
| devoff4-bin | S4a, OFF | 11-22 13:31 | 16DCC9399239E577 | 6BE3C713229232B2 | n/a | reference for devoff4b |
| native4-bin | S4a, native | 11-22 13:37 | 00D33D4FFB46776D | 65432C81D8C7D29A | 5e3ff55de10f4f64 | reference for native4b |
| devoff3-bin | S3, OFF | 11-22 02:44 | B9C5175DA1904235 | 2522D43605D8A9BF | n/a | |
| native3d-bin | S3d, native | 11-22 03:46 | 368F9CE650EC56CE | B90DF683D0A57A21 | 335ff2d47268f3a1 | |
| nativeB-bin | S3d + codegen B (Agent 9's batch-nolr), native | 11-22 04:34 | E5CBF30A6132B00E | 01C4D5A3E36FAC50 | 81d1c3a71be3c096 | |
| devoffB-bin | S2 + codegen B, OFF | 11-22 02:40 | 8709476FF4778768 | C3F8686EBDD83340 | n/a | |
| devoff1-bin, devoff2-bin, native-bin, native2-bin, native3-bin | S1 to S3 history | 11-21 / 11-22 | 1E81AA5E0C8A4309, B87DC2D2CA22379F, 91F2F817B0D6D205, D6E7F14F23373FA7, B50FE8D4A16565DA | | | superseded |

- **devoff4b and native4b** share their DLLs: rexruntime.dll A33801D1538D6175 and rexgpu-xenos.dll E3CB99CFDEA95E66, which is the current `snap1-sdk/install`.
- **devoff4b's exe now imports VCRUNTIME140_1.dll** (from the S4c thread_local). rexruntime.dll already imported it in devoff3, devoff4 and native4, so ship the VC++ 2019+ runtime (`build/agent2/s4b/checks/pe-imports-2113.txt`).
- **Never edit a bin file in place.** Many bin files are hardlinked into other agents' run folders.
- **Not built:** devoff4b-ctr-bin (CTR) and devoff4b-cg26-bin (CG26); see 4.1.
- **Checks:** `build/agent2/s4b/checks/`:
  - `mapcheck-devoff4b.txt` and `mapcheck-native4b.txt`;
  - `w5-rehash-2035.txt`;
  - `tree-check-2007.txt`;
  - `pe-imports-2113.txt`;
  - `sub2/`, the subagent's independent map checks.

### 2.3 Trees under build/agent2

| dir | what it is |
|---|---|
| `snap1` | Snapshot of `DimensionsRecomp` at S4b: equal to the committed b0bd3b4 / 5350b1d plus the plume/simde edits. The source of every snapshot build. |
| `snap1-sdk` | SDK build and install of snap1. `install/bin` has been S4b since 11-22 20:10 (rexruntime.dll A33801D1, rexgpu-xenos.dll E3CB99CF, TracyClient.dll 85044850). |
| `snap1-off`, `snap1-on` | OFF and native game build trees of snap1. Their last builds were devoff4b and native4b. |
| `snap1-backup-S2` ... `snap1-backup-S4b` | Apply backups: the snap1 files each level replaced, kept for a revert. |
| `snapB`, `snapB-off` | snap1 at S2 + codegen B: the source and OFF build of devoffB. |
| `snapB3`, `snapB3-on` | snap1 at S3d + codegen B: the source and native build of nativeB. |
| `cg26` | CG26 prep: the S4b codegen tool (`tool/rexglue.exe` 9145166C, `tool/rexruntime.dll` A33801D1) and a copy of rexlego with the ON toml (11707872). Its `generated/` is still the pinned copy; the regen has not run. Also holds `cg26-check.py`, `stage-cg26.py` and the self-test results in `checks/`. |
| `ctr` | CTR prep: recompile lists and dry runs. |
| `s4b` | `HASHES.txt` (the 16 S4b inputs), `checks/`, `logs-off/` and the prep work dirs. |
| `s4a` | S4a prep, history. |
| `pending` | Reference copies of the plume/simde patches, `plume-rebuild-check.txt`, and `PENDING-DIFFS-draft.md` (the detailed annex of PENDING-DIFFS.md). |
| `codegen-frozen`, `codegen-tool`, `compat` | Helpers that every snapshot build uses. Keep. |
| `live-backup`, `live-backup-S4a-20261122-145608` | Backups of my earlier live edits and of the S4a live apply. Keep. |
| others (`gen-noflag`, `c1-sweep`, `nmtest`, `probe-toggle`, `ppcmap-test`, `*-diffs`, ...) | Session-1 test output and review diffs. `build/agent2/inventory.md` lists which could be deleted. That list dates from 11-22 05:39, so re-run `inventory.py` before deleting anything, and delete nothing without Agent 1's or the user's word. |

> **Caveat:** snapB-off and snapB3-on link `snap1-sdk/install`, which is now the S4b SDK. A rebuild of either one now links the S4b DLLs; see 4.2.

## 3. PSO cache files (answer to Agent 1's question of 11-22 22:56)

Source: `build/agent2/snap1/DimensionsRecomp/rexlego/src/gpu_native/pipeline_library.cpp`, the native4b source.

- **Location: next to each exe, not in a shared place.** All paths resolve from the folder of the running `legodimensions.exe` (GetModuleFileNameW, `CachePath()` :99-105):
  - `<exe dir>/cache/native-pso.bin`: the driver pipeline library;
  - `<exe dir>/cache/native-pso-recipes.bin` (:151);
  - seeds, read only: `<exe dir>/native-pso-seed.bin` (:152) and `<exe dir>/native-pso-seed/*.bin` (`SeedPaths` :483-500).
- **Mismatched fingerprint:**
  - At start, a recipes or seed file recorded with another fingerprint is rejected. `ReadRecipes` :502-510 logs "ignoring invalid or incompatible pipeline recipes".
  - The session then records fresh recipes and overwrites `native-pso-recipes.bin` (temp file + MoveFileExW with REPLACE_EXISTING). The first write comes after 3 s with no new pipelines (`kQuietBeforeSave`, `Frame()` :325-339), and it is written again at `Stop()`/exit (:341-351), so the overwrite does not wait for exit.
  - `native-pso.bin` is rewritten when new pipelines were stored and its serialized size is over 1024 B.
  - Seeds are never written.
- **Consequence:**
  - Bins in separate folders keep separate caches. Running two builds from one folder, or copying a cache from one build to another, gives a cold start and clobbers the recipes.
  - Warm up each build in its own folder before an A/B, and keep the folders separate.
  - On 11-23, native4-bin, native4b-bin and nativeB-bin had no `cache/`, seed file or seed dir yet.
  - CG26 is an OFF build relinked from devoff4b objects, so it cannot change a native fingerprint.

## 4. Open items

### 4.1 Run-2 task #1 is unfinished: the CTR and CG26 bins

Agent 1 deferred both builds to "after the windows" on 11-22 22:30, and the pause has now superseded that. `@@done 1` was never sent. Both are prepared and dry-run tested. Build only when Agent 1 says go, at Below Normal, one at a time, with a HOLD check first.

**CTR → `build/agent2/devoff4b-ctr-bin`** (Agent 7's `<S4B-CTR>`; about 10 min)

devoff4b-bin with only `rexgpu-xenos.dll` replaced. In that DLL, `deferred_command_list.cpp` (`rexgpu-xenos.dir`) is recompiled with `-DREX_D3D12_DEFERRED_COUNTERS=1`. There is no source diff.

1. Recompile the control object and the ON object. Use snap1-sdk's ccdb with `--obj-filter /Release/`, because the multi-config ccdb has 3 entries per file:
   - `python build/agent2/recompile.py --ccdb build/agent2/snap1-sdk/compile_commands.json --list build/agent2/ctr/list-ctl.tsv --obj-filter /Release/ --log-dir build/agent2/ctr/log-ctl`
   - The same with `--list build/agent2/ctr/list-on.tsv --define REX_D3D12_DEFERRED_COUNTERS=1 --log-dir build/agent2/ctr/log-on`.
   - The two TSVs hold absolute paths on this machine (snap1's deferred_command_list.cpp → `ctr/obj-ctl|obj-on/deferred_command_list.cpp.obj`). Regenerate them if the workspace moves.
2. Relink the DLL edge twice:
   - `python build/agent2/relink.py --ninja build/agent2/snap1-sdk/build-Release.ninja --target <R>/build/agent2/snap1/DimensionsRecomp/rexglue-sdk/out/win-amd64/Release/rexgpu-xenos.dll --out-dir build/agent2/ctr/link-ctl --replace src/graphics/CMakeFiles/rexgpu-xenos.dir/Release/d3d12/deferred_command_list.cpp.obj=build/agent2/ctr/obj-ctl/deferred_command_list.cpp.obj --compare build/agent2/devoff4b-bin/rexgpu-xenos.dll`
     - The control DLL must equal devoff4b's except for the link timestamps.
   - Then the same with `obj-on` and `--out-dir build/agent2/ctr/link-on`, without `--compare`.
   - The dry run is in `ctr/link-dry/relink-command.txt`: the DLL edge, input 35 replaced, no PRE_LINK and no .def.
3. String check: the ON DLL contains `deferred_counters:` and the control DLL does not.
4. Stage:
   - `python build/agent2/stage-variant.py --base build/agent2/devoff4b-bin --out build/agent2/devoff4b-ctr-bin --replace rexgpu-xenos.dll=build/agent2/ctr/link-on/rexgpu-xenos.dll --title "..." [--dry-run]`
   - Then tell Agents 1, 3 and 7.

**CG26 → `build/agent2/devoff4b-cg26-bin`** (Agent 7's `<S4B-CG26>`; about 25-35 min unloaded, plus 1.5-2.5 min of single-threaded codegen)

devoff4b-bin with #26's codegen option on (`db16cyc_pause = true` in the toml). The regen changes 10 generated TUs, which are then recompiled and the exe relinked. Agent 10's gates are in b2r row 37. Expected result: exactly 20 `simde_mm_pause();` lines:

- TU 107: 8 (sub_83FAF180)
- TUs 116, 205 and 321: 2 each
- TUs 125, 153, 169, 284, 304 and 432: 1 each

Steps:

1. Delete `build/agent2/cg26/DimensionsRecomp/rexlego/generated/default/codegen.stamp`.
   - Touching the toml never forces a regen: the fingerprint hashes only content and names.
   - Gate (a) needs codegen.stamp, codegen.build.stamp and codegen.d from the same regen.
2. Run the regen with the tool's absolute path, so that `stop-snap.ps1` can find it:
   - `python build/agent2/holdrun.py --cwd build/agent2/cg26/DimensionsRecomp/rexlego --log build/agent2/cg26/codegen.log -- <R>\build\agent2\cg26\tool\rexglue.exe codegen legodimensions_manifest.toml`
3. Check the gates and stage the TUs: `python build/agent2/cg26/cg26-check.py --out build/agent2/cg26/checks/gates-<HHMM>.txt --stage`. On PASS this writes:
   - `cg26/tu` and `cg26/tu-ctl`;
   - `cg26/list-on.tsv` and `cg26/list-ctl.tsv`;
   - `cg26/replace-on.txt` and `cg26/replace-ctl.txt`.
4. Recompile twice with snap1-off's ccdb (single config): `python build/agent2/recompile.py --ccdb build/agent2/snap1-off/compile_commands.json --list build/agent2/cg26/list-on.tsv` (and `list-ctl.tsv`).
5. Relink twice:
   - `python build/agent2/relink.py --ninja build/agent2/snap1-off/build.ninja --target legodimensions.exe --out-dir build/agent2/cg26/link-on --replace-file build/agent2/cg26/replace-on.txt`
   - The control relink uses `replace-ctl.txt` and `--out-dir build/agent2/cg26/link-ctl`, plus `--compare build/agent2/snap1-off/legodimensions.exe --compare-map build/agent2/snap1-off/legodimensions.map`.
6. Map check: `python build/agent2/s4b/mapcheck-s4c.py --map build/agent2/cg26/link-on/legodimensions.map --ref build/agent2/devoff4b-bin/legodimensions.map --mode same --out build/agent2/cg26/checks/mapcheck-cg26.txt`
7. Stage: `python build/agent2/cg26/stage-cg26.py --dry-run`, then run it without `--dry-run`. Its MANIFEST notes name the tool, the toml and the 10 ON TU sha256s.
8. Run Agent 9's #18 kit (`build/agent9/cg26-check/README.md` L12, checker `cg26_check.py` DDBA731C) with `--out build\agent2\cg26\checks\kit18`. Exit codes: 0 PASS, 1 FAIL, 2 INCOMPLETE, 3 HELD.
   - Use the README's PowerShell form `(Get-Process -Id $PID).PriorityClass = 'BelowNormal'; python ...; "exit $LASTEXITCODE"`.
   - Don't use `cmd /c start /b /wait`, which always reports exit 0. The usage comment at the top of `stage-cg26.py` still shows that form; run it the PowerShell way instead.
9. Tell Agents 1, 3, 7, 9 and 10, then send `@@done 1` (or whatever task number Agent 1 gives it after the pause).

### 4.2 B4 (codegen B + S4a) is deferred and now stale

- **What was prepared:** the plan is in `perf-notes/agent2-baseline.md` (task #15, section 2: devoffB4 + nativeB4). The scripts are:
  - `build/agent2/b4-dryrun.py` (last run `b4-dryrun-1424.txt`: 0 FAIL / 0 WARN);
  - `build/agent2/prep-b4.py` (its dry run is `prep-b4-1546.txt`);
  - `build/agent2/run-b4.ps1`.
- **Never run.** B4 needed `snap1-sdk/install` at S4a, and the S4b SDK build (11-22 20:10) replaced it.
- **If the B line comes back,** re-plan it as B + S4b (Agent 7's queue already names devoffB4b-* bins), or clone an S4a SDK install first. Re-run the dry runs before building: the install-DLL checks will now fail against S4a.
- Details: PENDING-DIFFS.md.

### 4.3 Pending diffs that are not in git

The full list, with sha256, base and owner, is `build/agent2/PENDING-DIFFS.md`. In short (updated 2026-11-23 07:49 for board task #31):

- **Apply to HEAD, but not built:**
  - CG26 arm A (Agent 9's toml-A.diff, a one-line toml change) is rated SAFE to test after Agent 10's 4 gates.
  - #21 (Agent 7's S4-T1 rev 2) is rated in `build/agent10/t27/r21-s4t1.md`: (a) SAFE, (b) SAFE-IF 5 conditions including F-CA, (c) ACCEPTED.
  - #19 (Agent 7's R1 stage 2) now has its rate request (`build/agent7/s4-r1s2/RATE-REQUEST.md`, 09:59) but is not rated: Agent 10 rates it after the break (re-checked 11-23 10:15). To apply it in snap1, copy `build/agent7/s4-r1s2/new/sdk/` or use the `--directory` form in RATE-REQUEST.md §2. The `git -C <sdk root> apply` form in CHECKS.txt L22-23 skips all 5 files there, because snap1 has no `.git`.
  - #33 and #34 are staged together in `build/agent6/s33-popin/` (Agent 6; cvar `d3d12_pipeline_creation_no_wait`, default OFF) and rated in `build/agent10/t27/r33-popin.md`: OFF SAFE; ON as an opt-in test SAFE-IF 4 conditions. The first test bin leaves out hunk #5 (S1).
- **No tree diff:**
  - CTR is a `-D` define on one SDK TU.
  - Codegen B is a whole-file toml. Its formal read-out says drop (`build/agent8/readout/w-followup/W4c.md`: +2.6 % [−1.2, +6.5], no gain); retire or keep it after the break.
  - B4 is a build plan, and it is stale.
- **plume and simde:** uncommitted by design; see 2.1.
- **Apply checks:** run `git --no-optional-locks -C <repo> apply --check ...` against the repo. The workspace root sits inside an enclosing work tree, so from there git prints "Skipped patch" and exits 0 without checking anything.

### 4.4 Not an open diff

`DimensionsRecomp/rexlego/legodimensions_manifest.toml` in snap1 is the machine-local XEX manifest. It is gitignored by design.

### 4.5 Agent 9's #18 kit and Agent 10's gates

Both are ready for CG26; see 4.1 step 8. Agent 9's codegen budget is 1.5-2.5 min with one thread; it takes longer under build load.

### 4.6 Stale notes

`perf-notes/agent2-baseline.md` lines 1-38 (the RESUME block of 11-22 22:56) still carry two outdated values:

- the kit checker sha256 A179EB13 (now DDBA731C);
- the old `cmd /c start ... /wait /b` kit command (it always exits 0).

Task #28 let me write only `build/agent2/**`, so I left the notes file unedited. This HANDOFF supersedes its RESUME block.

## 5. Key scripts (build/agent2/)

Read-only unless noted. "HOLD" means the script refuses to start, and kills its children, while `perf-notes/WINDOW-HOLD.txt` exists.

| script | use |
|---|---|
| `commit-check.py` | `python build/agent2/commit-check.py --out build/agent2/COMMIT-CHECK.md [--sub stat\|bytes\|skip]`: committed trees vs snap1, read-only git (`--no-optional-locks`). Took 36-380 s depending on load. Re-running overwrites the whole report, including the hand-written summary at its top. |
| `plume-rebuild-check.py` | `python build/agent2/plume-rebuild-check.py --out build/agent2/pending/plume-rebuild-check.txt`: checks that the live plume checkout is exactly PIN e0c8871 plus the 7 tracked patches. It uses read-only git and runs Git's GNU patch on scratch copies in `build/agent2/scratch/plume-rebuild`; delete that folder afterwards. About 1 s. |
| `run-s4b.ps1`, `prep-s4b.py` | The S4b build driver (`-Stage off\|native -C1 v3 -Jobs 8 [-DryRun]`) and the snap1 patch apply (`--dry-run`). Both have been used; re-running rebuilds the snap1 trees. |
| `recompile.py` | Recompile TUs from a ccdb into scratch objects (`--ccdb --list [--define] [--obj-filter] [--jobs<=8] [--log-dir] [--dry-run]`). HOLD, Below Normal. |
| `relink.py` | Re-run one ninja link edge in a scratch dir (`--ninja --target --out-dir [--replace OLD=NEW] [--replace-file] [--compare] [--compare-map] [--dry-run]`). Writes nothing outside `--out-dir`. HOLD. |
| `stage-variant.py` | Stage a bin as a base bin with some files replaced (`--base --out --replace NAME=FILE --title [--note] [--dry-run]`); writes a MANIFEST. |
| `holdrun.py` | Run one command at Below Normal under the HOLD rule (`--cwd --log [--timeout] -- ABSOLUTE-PROGRAM args`); exit 30 means HOLD killed it. |
| `cg26/cg26-check.py`, `cg26/stage-cg26.py` | CG26 gates + TU staging, and the CG26 bin staging (4.1). |
| `s4b/mapcheck-s4c.py` | Link-map check by name and object (`--map --ref --out [--mode s4c\|same]`). |
| `s4b/rehash-w5.py`, `s4b/pe-imports.py` | Re-hash W5's inputs and check that devoff3-bin and devoff4-bin are unchanged; list PE imports. |
| `stop-snap.ps1` | Kill my build drivers, ninja, compilers, codegen and helpers (including ctr/ and cg26/ orphans). |
| `build-snap.ps1`, `stage-snap-bin.ps1`, `snap-patch.py`, `snap-gate.py`, `gen-check.py` | The general snapshot pipeline (build phases, staging with MANIFEST + gates, patch apply/revert, gates, generated-code check). |
| `inventory.py` | Writes `inventory.md`: the bins and dir sizes with a "could be deleted" column. |

## 6. Rules for resuming

- **Before every command:** if `perf-notes/WINDOW-HOLD.txt` exists, stop until Agent 1 says resume.
- **Load:**
  - Builds at Below Normal with at most -j8, or -j6 if `JSON hook ... PreToolUse ... failed` errors appear. Those errors mean the machine is overloaded: wait about 30 s and retry, and after 3 in a row tell Agent 1.
  - Heavy scripts run one at a time, at Below Normal, and need at least 4 GB of free RAM.
  - Finish every build before the cutoff Agent 1 sets.
- **Writes:**
  - Write only `build/agent2/**`.
  - Never write the live trees.
  - Use no git command that writes, and pass `--no-optional-locks` to every git call. Only Agent 1 commits or pushes.
  - Every copy a driver makes gets mtime = now after its hash check.
- **Apply checks:** always `git --no-optional-locks -C <repo> apply --check`. From the workspace root, git skips the patch and exits 0 (4.3).
- **Exit codes:** `cmd /c start ... /wait /b` hides them. Use `(Get-Process -Id $PID).PriorityClass = 'BelowNormal'; python ...; "exit $LASTEXITCODE"`.
