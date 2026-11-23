# Restart prompt: perf sprint session 3 (after the agy-grid relaunch)

Written by Agent 1 at the session-2 pause (01:30-01:45, 2026-11-22). The Git checkpoint was committed and pushed at 01:50 (§B.1).

## A. Prompt to paste into Agent 1 after the relaunch

```text
You are Agent 1, the agy-grid orchestrator for Agents 2-12. You are resuming the Dimensions Recompiled
perf sprint (session 3) after an agy-grid relaunch. Workspace:
<workspace>

Before doing anything else, read (read-only):
1. perf-notes/RESTART-PROMPT-S3.md, all of it: state, builds, results, decisions, first steps, the task
   blocks to re-issue, rules.
2. perf-notes/SESSION2.md, the last ~250 lines.
3. perf-notes/FINDINGS-AND-CHANGES.md, the user-facing report. Copy it into your artifact directory as
   findings-and-changes.md and keep it updated there.

Then, in this order:
1. Check the state with light commands only. Run git status / git log -1 in DimensionsRecomp and in
   DimensionsRecomp/rexglue-sdk; compare with §B. Check that no build or game processes are running.
   Check that build/agent2/devoff2-bin and native2-bin exist, and that build/agent9/install/batch-nolr
   exists.
2. Re-issue the task blocks in §F to Agents 2-12 in ONE reply. In the same reply, add one directive line
   addressed to all of Agents 2-12 (format in §G) asking each agent for "RESUMED + ETA". agy-grid may
   renumber the tasks: record the new numbers in SESSION2.md.
3. Git: the session-2 checkpoint is already committed and pushed (§B.1). From now on, commit at
   milestones (for example when a worker reports a task done), following the Git rule in §G.
4. Run the plan in §E: the B (codegen-option) build first, on S2; the S3 inputs in parallel; then the S3
   build. Then plan timing window 4 with me: give a clear ETA, and tell me exactly when to be at the desk
   and what to double-click.

Follow the rules in §G strictly. Keep replies concise, use github markdown with file:// links, and put
questions to me in plain text.
```

---

## B. Where things stand

- **Repos:** `DimensionsRecomp` (game) and its SDK submodule `DimensionsRecomp/rexglue-sdk`. Both are on branch `perf/opt`.
  - Sprint base: v0.2.0, game `127e04b`, SDK `2897c31`.
  - **Checkpoint:** committed and pushed at 01:50: game `a0bdaa7`, SDK `90e7ccd` (§B.1).
- **Live tree = S2 + #27 + Agent 9's codegen sources.** Agent 2 verified this at 01:22 (`build/agent2/snap1/PLAN-CHK-0122.txt`, 8E133F63): 23,843 files, 22 differ from S2, 0 new, 0 deleted.
  - #27 is Agent 11's exit fix: `rexglue-sdk/src/kernel/xam/xam_ui.cpp` 0a314946 and `rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_hal.cpp` ab359e1d. Always on, rated SAFE.
  - Agent 9's 20 codegen source files: 17 modified and 3 new. Every option defaults to OFF, and the output is identical to the pin at defaults (off4). S2 held these files at S1.
  - Nothing else changed after the S2 cut (23:15). Every agent reported "running: none" at 01:21-01:40.
- **`thirdparty/plume`** is checked out at `e0c8871`, the `prepare_plume.py` pin (line 9), with 3 dirty files.
  - The superproject records `ceaeeee`, which is not fetchable from the public repo. This predates the sprint.
  - **Never commit the plume pointer.**
- `DimensionsRecomp\rexlego\generated` is a **junction to baseline's generated code. Never write into it.**

### B.1 Checkpoint

- **Committed and pushed at 01:50** on branch `perf/opt`, to the `mine` remotes (the user's forks). Author: Rishabh Mohan, from each repo's local git config.
  - **SDK** (`DimensionsRecomp/rexglue-sdk`): `90e7ccd` "Perf sprint checkpoint: batches 1-2, exit fix, codegen options" (51 files, +3652/-344). Pushed with `git -C rexglue-sdk push mine perf/opt` to `git@github.com:rishabh-mohan/rexglue-sdk.git` (new branch; no upstream is set in the SDK).
  - **Game** (`DimensionsRecomp`): `a0bdaa7` "Perf sprint checkpoint: batches 1-2, SDK on perf/opt" (52 files, +5336/-300). Pushed with `git push -u mine perf/opt` to `git@github.com:rishabh-mohan/DimensionsRecomp.git` (new branch; tracks `mine/perf/opt`).
    - It records the SDK pointer `90e7ccd`, the user's `.gitmodules` change (rexglue-sdk url -> `https://github.com/rishabh-mohan/rexglue-sdk.git`, branch `perf/opt`) and `__pycache__/` in `.gitignore`.
  - The commits hold exactly the live tree in §B (S2 + #27 + Agent 9's codegen sources). Committing changed one file on disk: `DimensionsRecomp/.gitignore` (+3 lines; not a build input, but Agent 2's plan checks may list it). The live hashes the agents use are unchanged (rex_app.cpp E1569868, audio_system.cpp C281FA86, draw.cpp 50AA3B1D, settings_registry.cpp A3733700, settings_preferences.cpp C78112AA).
  - Both remote heads matched the local HEADs after the push.
- **Expected `git status` now:** game ` m rexglue-sdk` (only because of simde, below) and ` M thirdparty/plume`; SDK ` m thirdparty/simde`. Nothing else, and nothing untracked.
- **Left out on purpose:**
  - `thirdparty/plume`: never commit its pointer. Its changes are patches in `tools/gpu-aot/patches/`.
  - `thirdparty/simde` (inside the SDK): a small local edit to `simde/x86/sse.h` (+9/-1, a Windows Clang fix in `simde_mm_stream_pi`, dated 11-21 17:57). It is in no commit and not in the patch export. Backed up as `build/agent1/simde-dirty-1122.diff` (SHA256 2A6DE738). Ask the user before committing it anywhere (for example as a patch file).
- **Patch export** (01:27, kept as a second copy): `build/agent1/checkpoint-1122-0127/`, SHA256SUMS.txt 3BAD4CC8: `game.diff`, `sdk.diff`, `plume-dirty.diff`, the 24 untracked files and a README with restore steps. It predates the `.gitmodules` and `.gitignore` changes.
- **Further commits:** at milestones, per the Git rule in §G.

## C. Builds (all staged and manifest-checked)

| Folder | What | Hashes |
|---|---|---|
| `build/baseline-bin` | v0.2.0 reference (standard GPU path). Pristine. | |
| `build/sdk/install` | Baseline SDK install. Pristine. | |
| `build/agent2/devoff1-bin` | S1, standard GPU path | MANIFEST 1E81AA5E |
| `build/agent2/native-bin` | S1+p1+p2, native GPU path | exe 3B329E95 |
| `build/agent2/devoff2-bin` | S2, standard GPU path | exe 7F0B1C1C, MANIFEST B87DC2D2, 49/49 |
| `build/agent2/native2-bin` | S2, native GPU path | exe 5D1B2DC6, MANIFEST D6E7F14F, 72/72, fingerprint b7cc74f980e016c3 |

- devoff2 and native2 share the same DLLs: rexruntime 1C45C869 and rexgpu-xenos 77A5300B.
- **Snapshot trees:** `build/agent2/snap1` holds the S2 sources (PATCHES-S2 b2554716, STATE-S2-2315 48869f6b). Its build dirs are `snap1-sdk`, `snap1-off` and `snap1-on`. snapB doesn't exist yet.
- **Input for the B build:** `build/agent9/install/batch-nolr`, with config `build/agent9/configs/batch-nolr.toml` (E60EAF1C).
  - Contents: 872 files, 430 TUs, gate 432, SHA256SUMS 24CE1493. Generated by tool `build/agent9/bin/rexglue.exe` (37B32713).
  - **NEVER build `build/agent9/install/batch`**: it is the skip_lr tree, which is UNSAFE because host code reads ctx.lr.
- **Native builds crash at startup without a flag.**
  - Cause: our SDK builds have FidelityFX OFF, so `present_fsr_*` is never registered, and `native_settings_frontend=true` makes `ReadRegistryValues` throw (`rexlego/src/settings_registry.cpp:104`).
  - Until S3: run native with `--native_settings_frontend=false`.

## D. Results so far

- **Matrix 1** (window 2, title screen, 60 fps cap), baseline vs devoff1:
  - Median 16.66 vs 16.67 ms.
  - devoff1 used +0.09 cores in 5/5 pairs (p≈0.03).
  - Cold start 9.0 vs 10.0 s.
- **Window 3** (`build/agent8/matrix/20261122-0013`, 00:13-01:16, uncapped title loop, 19/19 OK, 16 scored, noise band ±1.7%):

  | arm | median ms | p99 ms | fps | CPU cores | vs d0 |
  |---|---|---|---|---|---|
  | d0 = devoff2 (ref) | 7.07 | 12.23 | 162.9 | 3.52 | |
  | base = baseline | 7.12 | 12.35 | 160.8 | 3.50 | +0.8%, noise |
  | d11 = devoff2 + Agent 11's R3 timer bundle | 7.14 | 12.25 | 159.0 | 3.59 | +1.0%, noise |
  | n0 = native2 (flag, native_fps_limit=0) | 6.71* | 11.34* | 143.2 | 2.45 | 12% fewer frames, -30% CPU |

  - \* n0's frame times come from `native-frames.csv`, while the other arms use `perf.csv`, so they aren't comparable (Agent 4). By frame count native2 is 12% slower, at 30% less CPU (~21% less per frame). It is CPU-bound on Main XThread (74-77%), not the GPU (43-50%).
  - devoff2 = baseline within noise, at the same CPU. The d11 bundle gives no gain and stays OFF.
  - **The 2x split is game state, not clocks** (Agent 8: `perf-notes/agent8-window3.md` "Window 3: results", and `recheck.md` in the matrix dir).
    - Every run, n0 included, starts in a light title phase and switches to a heavy one 30-40 s after the first frame.
    - The clocks are the same in both phases (GPU at P0 ~1732 MHz, 3.5 cores). The heavy phase costs 2x the CPU per frame (GPU Commands 2.8→5.4 ms, main 1.3→3.0 ms) and 2.4x the GPU per frame (1.4→3.4 ms).
    - cold-d0 (3.18 ms) and cold-base (3.87 ms) only looked fast because their 30 s windows began ~13 s after the first frame. The short hidden-desktop checks (~3.7 ms) were in the light phase too.
    - d11-r1 (3.40 ms) alone stayed light for all 300 s, and it is the only run without the 34 failed `NtCreateFile d:\INSTALL#_#.DAT` lines.
      - It ran 00:25-00:30, while the user was at the desk. But d0-r1 and base-r1 (00:18-00:25) didn't diverge.
      - Open: user input or a Toypad race.
    - d0, base and d11 share the same phase pattern and windows, so their within-noise verdicts hold. Native vs standard medians mislead: n0 vs d0 is -5.1% by median but -12.1% by mean fps.
  - **Per-thread busy, % of one core** (main XThread / GPU Commands / TimerQueue / audio):
    - d0: 48.4 / 86.8 / 62.0 / 6.1
    - base: 48.2 / 87.2 / 62.5 / 6.0
    - d11 r2-r4: 49.4 / 86.4 / 61.7 / 6.0 (d11-r1: 38.2 / 82.1 / 60.4 / 6.7)
    - n0: 75.7 / none / 52.4 / 3.3

## E. Plan after the restart (in order)

1. **Agent 2: B tool prep, then the B build, on snap1 = S2.** This is a clean A/B against devoff2-bin, and it is exactly Agent 10's gate baseline ("an S2 build with S1 codegen").
   - Prep without building: compile codegen-frozen2.exe, run patch-b-tools.py and diff against `*.pre-B`, then a default-mode gen-check and snap-gate on snap1.
   - Then snapB = snap1 + batch-nolr. Its `generated` folder must be a real dir, and every write must resolve under snapB.
   - Then gen-check, a fresh OFF configure, the gate, and the build (~15-20 min at -j10, all TUs). Stage it as `build/agent2/devoffB-bin` with a manifest.
   - Rollback: Agent 9's recipe step 9.
2. **In parallel (light edits only, no builds): the S3 inputs land in the live tree, each at Agent 1's GO.**
   - **Agent 6:** the native fix (a), applied as hash-guarded copies of `build/agent6/fix-a/new/*`, in the **game repo**: `rexlego/src/settings_registry.cpp` A3733700→8BA19C5F and `rexlego/src/settings_preferences.cpp` C78112AA→9CBE6DBF.
     - Also **fix-a-commit.patch**, which Agent 10 rated SAFE and recommends (§12): it stops Save from overwriting FFX-saved FSR1 values. The resulting hash is 4EC71328; confirm with Agents 6 and 10.
     - OFF builds compile these files but never run the changed lines: the only callers, at `legodimensions_app.h:128,133`, are under `#ifdef LEGODIMENSIONS_NATIVE_GPU`.
   - **Agent 12:** two default flips, both pre-staged with `-Check`/`-Apply`/`-Revert`:
     - `pause_safe_order` ON with `bench/agent11/safeorder_stage.ps1 -Apply` (file `rexglue-sdk/src/ui/rex_app.cpp`, pristine E1569868).
     - `audio_shutdown_detach_worker` ON with `bench/agent12/s3flip_stage.ps1 -Apply` (`src/audio/audio_system.cpp` C281FA86→4331A312).
     - Then `s3flip_syntax.ps1 -Live` and `safeorder_syntax.ps1 -Live`, and send the hashes to Agents 1, 2 and 10.
   - **Agent 10:** re-hash the live files, rate the flips (audio ON vs §8, safeorder vs §11), and send the S3 TSV (file list and owners) to Agent 2.
3. **Agent 8's functional slot queue** (functional runs may overlap a build; timing never does):
   - Agent 4's N1-N3 commands on native2-bin with the flag.
   - Agent 3's 2 baseline-bin runs (180 s with -GpuLog, then -Profile, ~7 min).
4. **The B game gate, after B is staged:** Agent 10's route (last section of `perf-notes/agent10-codegen-review.md`), B vs devoff2.
   - Covers: boot export lookups, the LR-gated slot-heap Grow, the pause-menu Options Back row, the cel-shading/dialogue/Adventure Time mid-asm hooks, and a level change (the sub_83FC49E8 relocation at lr=83F9B660).
   - It needs menu input, from Agent 3's harness or from the user. Agents 9 and 8 support it.
5. **Agent 2 cuts S3 and builds it**, after B: a hash-verified copy into snap1, PATCHES/STATE files, gen-check with codegen-frozen, and the gate.
   - Contents: S2 + #27 + Agent 9's 20 codegen files (OFF, output identical) + fix-a (+ fix-a-commit) + the two flips.
   - Optional cosmetic: fingerprint inputs (`rexlego/CMakeLists.txt:599-603`).
   - Build devoff3 (OFF), then native3 (ON). Stage both with manifests.
6. **After S3, in Agent 8's slot:**
   - Boot devoff3, then boot native3 **without** the workaround flag, to prove the fix. Agent 7 checks: frontend on, no throw, bilinear present.
   - Then Agent 11's default check: `bench/agent11/testg_session.ps1 -BinDir build\agent2\devoff3-bin -Only default` (~3 min). It refuses unless the default-ON safeorder is in the build.
   - Agent 5 then repoints its uploads A/B to native3.
7. **Timing window 4** with the user, ≤45 min. Agent 8 composes it and provides `RUN-WINDOW4.cmd`, a dry run and a GO line.
   - Primary: **B vs devoff2**.
   - Optional: devoff3 vs devoff2 (should be neutral); native arms **with one frame source for every arm**.
   - Candidates for later windows:
     - Agent 4's `matrix-native-threaded.json` (21 runs, ~63 min, so trim it to ≤45 min)
     - Agent 5's uploads A/B (u0-u2 ×3 ≈ 35 min)
     - the d12 bundle
     - `matrix-native-tier1/pso.json`
     - Agent 7's arm i1
   - Every S3 arm keeps `--native_settings_load=false`: with fix-a, non-FFX builds now apply a saved native-settings.toml.
   - Agent 8's window-4 driver logs a 1 s sys.csv: input idle time, whether the game is in the foreground, effective CPU MHz (P/E split), thermal limit, power mode, and AC at start and end.
   - The runner starts every measurement window ≥ 60 s after the first frame, cold runs too, and flags light-phase runs (INSTALL count, share of frames < 4.5 ms).
   - The user sets the screensaver to (None), stays on AC power and unlocked, and doesn't touch the PC during the window. d11-r1's light phase may have come from user input.

## F. Task blocks to re-issue (send all in ONE reply)

Each block below points to the agent's notes. Most notes files have a RESUME block at the top. Agent 6's commands are in the last section of its crash-triage notes, and Agent 8's state is in agent8-window3.md.

````text
```agy-task to=2 subagents=1 files=build/agent2/**, perf-notes/agent2-baseline.md
Builds (you are the only full builder, <= -j10). Read the RESUME block in perf-notes/agent2-baseline.md.
1. B tool prep without building (codegen-frozen2.exe, patch-b-tools.py diffed against *.pre-B,
   default-mode gen-check and snap-gate on snap1).
2. At GO: B on snap1 = S2 + build/agent9/install/batch-nolr (verify SHA256SUMS 24CE1493). generated must be
   a real dir and every write must resolve under snapB. Then gen-check, OFF configure, gate, build -j10,
   stage build/agent2/devoffB-bin with a manifest, and post the hashes.
   NEVER use build/agent9/install/batch.
3. After B, at GO: cut S3 from Agent 10's TSV and build devoff3, then native3. Stage both and post the hashes.
```
```agy-task to=3 subagents=1 files=game/**, harness/**, perf-notes/agent3-run-harness.md
Run harness. Read the RESUME block in perf-notes/agent3-run-harness.md and check the guard.
1. On Agent 8's ping: the 2 baseline-bin runs (180 s with -GpuLog, then -Profile). Fill in 6.2 and send
   @@done.
2. Prepare the B game-gate route as a menu-input script (Agent 10's route, last section of
   agent10-codegen-review.md: boot, pause menu Options -> Back, a level change). Dry-run it on devoff2-bin
   (functional only). Report whether it runs without the user.
```
```agy-task to=4 subagents=1 files=bench/agent4/**, perf-notes/agent4-draw-path.md
Native draw path. Read the RESUME block in perf-notes/agent4-draw-path.md. Confirm draw.cpp is still
50AA3B1D. Check Agent 8's N1-N3 game.logs against 2.12. Trim matrix-native-threaded.json to <= 45 min, with
one frame source for every arm, and send it to Agent 8 for a later window.
```
```agy-task to=5 subagents=0 files=bench/agent5/**, perf-notes/agent5-uploads.md
Native uploads. Read the RESUME block in perf-notes/agent5-uploads.md. Hold until native3 boots clean. Then
point the 6 bin fields of bench/agent5/matrix-native-uploads.json at native3, re-check with -PlanOnly, and
send it to Agent 8.
```
```agy-task to=6 subagents=0 files=build/agent6/**, perf-notes/agent6-crash-triage.md, DimensionsRecomp/rexlego/src/settings_registry.cpp, DimensionsRecomp/rexlego/src/settings_preferences.cpp
Native fix (a). Read the last section of perf-notes/agent6-crash-triage.md. At GO only: apply fix-a plus
fix-a-commit (Agent 10 §12) as hash-guarded copies into the live game repo, re-verify the hashes, and
report to Agents 1, 2 and 10. No git writes.
```
```agy-task to=7 subagents=1 files=bench/agent7/**, build/agent7/**, perf-notes/agent7-present.md, perf-notes/agent7-s3-proposal.md, perf-notes/agent7-odr-ffx.md
Present path. Read the RESUME block in perf-notes/agent7-present.md. At <= 2 threads, summarise the
window-3 native run dirs with bench/agent7/native_frames_summary.py (unless Agent 8 already has). Then help
Agents 6 and 2 check native3 with (a): frontend on, no throw, bilinear present. Lead: native2 renders 12%
fewer frames at 30% less CPU, CPU-bound on Main XThread.
```
```agy-task to=8 subagents=1 files=bench/agent8/**, build/agent8/**, perf-notes/agent8-session2.md, perf-notes/agent8-window3.md, perf-notes/agent8-first-boot.md
Timing runner and slot queue. Read perf-notes/agent8-window3.md ("Window 3: results" and "Proposal for
window 4").
Slot queue: Agent 4's N1-N3 on native2-bin (matrix-native-functional.json -Only n1,n2,n3, with the flag),
then Agent 3's 2 runs, then the B gate (with Agents 3, 9 and 10), then the devoff3 and native3 boots
(native3 without the flag), then Agent 11's default check. Fix Get-BuildProcs (it misses clang++ and
rexglue). Window 4: B vs devoff2 (primary), one frame source for every arm, the 1 s sys.csv driver, every
measurement window >= 60 s after the first frame (cold runs too), light-phase runs flagged, <= 45 min,
RUN-WINDOW4.cmd, a dry run and GO.
```
```agy-task to=9 subagents=1 files=build/agent9/**, bench/agent9/**, perf-notes/agent9-codegen.md
Codegen. Read the RESUME block in perf-notes/agent9-codegen.md and delete bench/agent9/QUIET. Support
Agent 2's B build and the B game gate (rollback = recipe step 9). Optional: a 9-key T8 run at <= 2
threads. No new codegen changes until B passes the gate.
```
```agy-task to=10 subagents=1 files=build/agent10/**, perf-notes/agent10-batch2-review.md, perf-notes/agent10-codegen-review.md, perf-notes/agent10-helpers.md
Safety reviews. Read the RESUME block in perf-notes/agent10-helpers.md. Re-hash the fix-a live files after
Agent 6 applies them. Rate Agent 12's two flips (audio ON vs section 8, safeorder vs section 11). Send the
S3 TSV (files, hashes, owners) to Agent 2. Give the B game-gate verdict against your route.
```
```agy-task to=11 subagents=1 files=bench/agent11/**, build/agent11/**, perf-notes/agent11-kernel.md
Kernel and threading. Read perf-notes/agent11-kernel.md "S3 default check". Add the opt-in 'default' run
to bench/agent11/testg_session.ps1 and self-test it with -CheckOnly (devoff2 must refuse). Run -BinDir
build\agent2\devoff3-bin -Only default in Agent 8's slot after the devoff3 boot. Lead: the
rex::thread::TimerQueue thread uses 62% of a core in devoff2 and 52% in native2 (window 3, Agent 8's
per-thread table). Find out why and propose a fix behind an OFF cvar.
```
```agy-task to=12 subagents=0 files=bench/agent12/**, build/agent12/**, perf-notes/agent12-io-memory.md, DimensionsRecomp/rexglue-sdk/src/ui/rex_app.cpp, DimensionsRecomp/rexglue-sdk/src/audio/audio_system.cpp
I/O and audio. Read the RESUME block in perf-notes/agent12-io-memory.md and run both -Check (expect
pristine). At GO: safeorder_stage.ps1 -Apply and s3flip_stage.ps1 -Apply, -Check, s3flip_syntax.ps1 -Live
and safeorder_syntax.ps1 -Live. Send the hashes to Agents 1, 2 and 10.
```
````

## G. Rules (unchanged, except Git: updated at 01:50)

- **Builds and threads:** only Agent 2 runs full builds (≤ -j10). Everyone else uses ≤2 threads.
- **Disk:** ask before writing more than ~20 GB.
- **File ownership:** only Agent 3 writes `game/` and `harness/`. Agents edit only the files in their claims.
- **Git** (the user's rules, 01:38-01:44):
  - Only Agent 1 commits and pushes. Workers never run repo-changing git.
  - Commit at milestones, for example when a worker reports `@@done` or a build input lands (fix-a, the S3 flips, the B result).
  - Order: the SDK first (commit in `DimensionsRecomp/rexglue-sdk`, then run `git -C rexglue-sdk push mine perf/opt` from `DimensionsRecomp`), then the game repo with the new SDK pointer (`git push -u mine perf/opt`).
  - Push only to the `mine` remotes (rishabh-mohan's forks), branch `perf/opt` in both. `origin` is the upstream original: never push there.
  - Stage specific files by path. Never `git add -A`.
  - Never commit `thirdparty/plume` (its changes live as patches in `tools/gpu-aot/patches/`) or `thirdparty/simde`. `__pycache__/` is in `.gitignore`.
  - The author is configured in both repos: check with `git remote -v` and `git config user.name`, and don't change git config. GitHub works over SSH with the user's key: don't look for tokens or credentials.
  - `GIT_EDITOR=false` here, so commit with `-m` or `-F`.
- **Pristine:** `build/sdk/install` and the baseline stay untouched. Never write into the live `rexlego\generated` junction.
- **Behaviour changes:** OFF by default unless proven output-identical. Always-on only when Agent 10 rates them SAFE.
- **Timing:**
  - Timing comes only from user-started (double-click) runs in quiet windows. Agent runs on the hidden desktop are functional only.
  - Never time `-Profile` runs. One game at a time.
  - Uncapped runs use `framerate_limit=0`, plus `native_fps_limit=0` on native.
  - Standard flags: `--audio_mute=true --pause_when_unfocused=false --native_settings_load=false --discord_rpc=false`.
  - Compare arms only on the same frame source.
- **Quiet windows:**
  - Heavy work stops 5 min before.
  - Agents only read files and edit notes.
  - Agent 1 holds non-urgent replies, since agent turns cost CPU on the timed machine.
  - The user sets the screensaver to (None), stays on AC power and unlocked, and keeps hands off.
- **Never:**
  - Bypass the agy-grid hook, approval prompts, the hidden desktop or access controls. Retry hook failures.
  - Run worker scripts with unknown flags.
  - Run Agent 2's builds yourself.
  - Kill other agents' processes. Ask the owner.
- **Protected processes, leave alone:** the long-running python processes (session-2 PIDs 1912, 22084, 47720, 52964, 55340, 70536; python3.11 41488, 38284; they may differ after a reboot), MSPCManagerCore and Defender.
- **Directives:** one line each at the end of a reply, as `@@to N: msg` or `@@to 2,3,4: msg`. Agents only see `@@to` lines. Task blocks use ```` ```agy-task to=N subagents=N files=a, b ````.
- **Defaults assumed** (the user never answered): agy-grid rules unchanged, keep the ISO, no private shader banks.

## H. Leads and open questions

- Why d11-r1 stayed in the light title phase for its whole run: user input at the desk, or a Toypad race. Window 4 flags light-phase runs (Agent 8).
- TimerQueue at 52-62% of a core in window 3 (Agent 11).
- On the standard path the GPU Commands thread is the busiest (87% of a core). native2 shows no GPU Commands thread, and its main XThread is at 76%.
- native renders 12% fewer frames at 30% less CPU, CPU-bound on Main XThread (Agents 4, 6, 7).
- Not yet profiled: the `PPCContext` memset in GuestToHostFunction, the `GetFunction` recursive_mutex, and overlapped handles.
- Option (b), FidelityFX for native only (restores FSR 1), is parked for S4. Agent 10 noted 2 S4 hazards. Agent 2 can build it as `native3ffx-bin` about 2-3 min after native3.
- Optional human steps:
  - Agent 6's native capture runs.
  - An elevated WPR profile (`perf-notes/agent3-run-harness.md` §Option 2).
  - Windows SDK 26100. Not needed: the p2 cast covers 22621.

## I. Pause log (filled in by Agent 1)

- State lines (01:21-01:33): all 11 agents reported "running: none" and no live-tree edits beyond the plan. The full lines are in `perf-notes/agent1-pause-state-lines.md`. SESSION2.md has the summary (01:20-01:40).
- Agent 8's 2x-split analysis (01:33): game state, not clocks (§D).
- Git: the checkpoint was committed and pushed at 01:50: SDK `90e7ccd`, game `a0bdaa7` (§B.1). The patch export is a second copy.
- Agent 1's session-2 tracker: `perf-notes/agent1-tracker-s2.md`.
- Paused at ~01:40: no builds, no game runs, no timers.
