# Session 2 brief (2026-11-21, from 16:10)

Read [BRIEF.md](BRIEF.md) and [STATUS.md](STATUS.md) first. Where this file disagrees with them, this file wins.
Agent 1 (orchestrator) maintains this file.

## What changed since session 1

- **We have the game now.** The user added their own dump:
  - Disc: `ld rom/LEGO Dimensions (USA, Europe) (En,Fr,De,Es,Nl,Da).iso`. It is an XGD3 image, 8.7 GB. The XDVDFS volume
    descriptor is at `0x2090000` (partition `0x2080000`). The root holds `Default.xex` (11.5 MB), `GAME.DAT/HDR`, `GAME0-4.DAT/HDR`,
    `INSTALL0_.DAT/HDR`, `INSTALL0_0/1.DAT/HDR`, `NxeArt`, `__DISC__` and `$SystemUpdate/`. A probe script is at
    `C:\Users\<user>\.gemini\antigravity-cli\brain\ea80efc8-efb6-47da-b829-77fa9ce36d16\scratch\xiso_probe.py`.
  - TU23: `ld title update 23/5752084B/000B0000/tu00000003_00000000`. It is a `LIVE` STFS package of 2.07 GB, content type `000B0000`.
  - The constraint "we do not have the game files" is lifted. We can run codegen, build `legodimensions.exe`, boot it and profile it.
- **The toolchain is ready.** LLVM 23.1.6 is at `toolchain/llvm-23.1.6`; `. env/devshell.ps1` puts it on PATH. The SDK submodules
  are initialized (shallow). `DimensionsRecomp/thirdparty/plume` is **not** at its pin yet: pin `ceaeeee` is not on
  zolaware/plume, and it currently holds `main` at `9fac2c5`. Agent 2 is fixing it.
- **The network is fast** (about 5 MB/s).
- **Disk is tight.** About 34 GB is free. Do not create large files outside your `build/agentN` or `bench/agentN` folder, and
  delete scratch build trees you no longer need.

## Build layout (Agent 2 owns all of this)

- `baseline/DimensionsRecomp/` is a **pristine v0.2.0 snapshot**. It is a `git archive` of `127e04b`, plus the SDK archived at
  `2897c31`, with `thirdparty` linked to the dev tree's submodule checkouts. The baseline SDK, codegen and the baseline game
  build all come from here, so **edits in the dev tree never contaminate the baseline**. Baseline binaries are saved to `build/baseline-bin/`.
- `DimensionsRecomp/` is the **dev tree**, where every worker edits:
  - `build/sdk-dev/` is a configure-only SDK tree. Its `compile_commands.json` feeds `env/compile-one.ps1`.
  - A dev-tree game configure, also for compile-one of `rexlego/src`, follows once codegen is done.
  - The dev game build at `build/dev/` comes later.
- **Game data (Agent 3):** the extracted disc plus `Default.xexp` go in `game/disc/`, the extracted TU in `game/tu23/` and saves
  in `game/user/`. The runtime config and launch/measure scripts go in `harness/`.

## Rules for this session (in addition to BRIEF.md)

1. **CPU:** only Agent 2 runs full SDK or game builds, at up to `-j10`.
   - Everyone else uses `env/compile-one.ps1` for single-file checks and builds small standalone benches/tests in
     `bench/agentN/`, with at most 2 threads.
   - Ask Agent 1 before anything that needs more than about 2 CPU-minutes, such as building SDK test targets or the `rexglue` tool.
2. **Headers included by generated code** (for example `include/rex/ppc/*` or anything in the game PCH): a change there rebuilds
   all ~720 generated translation units (1-2 h).
   - You may edit them in your granted files, but flag it in your `@@done` summary. Agent 1 batches those edits into one dev build.
   - Agent 2 will publish the exact header list in `perf-notes/agent2-baseline.md`.
3. **Codegen output changes** (Agent 9) need a regeneration plus a full rebuild. They are batched the same way.
4. **Game data:**
   - Only Agent 3 extracts data or writes under `game/`.
   - Never put game data, or anything derived from it, into a git-tracked path. That includes generated code, extracted
     files, and captures or screenshots that contain game assets.
   - `DimensionsRecomp/.gitignore` ignores `/*` except named paths. Keep it that way.
5. **Measuring:**
   - Until the game runs, "before" numbers come from microbenches.
   - After that, compare `build/baseline-bin` against the dev build with Agent 3's run harness.
   - Report medians of at least 5 runs on the same machine, and say what else was running.
6. **Everything else in BRIEF.md still holds:**
   - surgical, behaviour-preserving diffs, with anything risky OFF by default behind a cvar or CMake option;
   - edit only the files you were granted;
   - no git commands that change a repository;
   - a report at `perf-notes/agentN-<topic>.md`, and finish with `@@done`.

## Milestones (rough ETA from 16:15)

| # | Milestone | Owner | ETA |
|---|---|---|---|
| 1 | Dev SDK configured, `compile-one.ps1` ready | Agent 2 | ~16:45 |
| 2 | Disc and TU23 extracted and verified, runtime config written | Agent 3 | ~16:45 |
| 3 | Baseline SDK built, installed and tested; `rexglue codegen` done | Agent 2 | ~17:30 |
| 4 | Baseline `legodimensions.exe` built; first boot through the harness | Agents 2, 3 | ~18:30-19:00 |
| 5 | Dev build with the landed changes; A/B against the baseline | all | after 4 |


## Update at 16:47 (orchestrator)

- **Subagents.** The agy-grid hook stops the orchestrator from starting subagents, so subagent-sized jobs go to workers with `subagents=N`. Jobs J1 to J4 are described in `perf-notes/SESSION2-jobs.md`.
- **Build order.** The emulated-Xenos baseline (`NATIVE_GPU=OFF`, plus `rexgpu-xenos.dll`) comes first. The native ON build needs offline shader banks, DXIL caches and FSR3 libs that aren't in the repo. Agent 6 rebuilds them (J1), starting with stubs so Agent 2 can run an ON compile-only configure in `build/dev`.
- **Plume.** The old pin ceaeeee can't be fetched. Use the public commit `e0c8871b930dc1a6544bf457f2348c456b9d7e13` (see `tools/gpu-aot/COLLABORATION.md` lines 212 to 226), then run `prepare_plume.py`.
- **Profiling.** Every staged exe gets its `legodimensions.map` copied next to it. Agent 8 is writing the analyser `tools/native-cpu/analyze_profile.py` (J2), and Agent 3 is adding a `-Profile` switch to the harness.
- **Reviews.** Agent 12 maps the global critical region and reviews Agent 11's global-mutex design (J3). Agent 10 reviews Agent 9's codegen changes (J4).
- **Ownership changes.**
  - Agent 2 no longer owns `DimensionsRecomp/rexlego/out/**`.
  - Agent 6 now owns `rexlego/out/native-gpu/**`, `research/**`, `rexglue-sdk/bin/**` and `out/build/lego-release/**` (all under `DimensionsRecomp/`).
  - Agent 8 now owns `tools/native-cpu/**`.


## Pause checkpoint at 16:50 (orchestrator)

The user is pausing the grid to fix a bug in agy-grid.

**State at the pause:**
- No build, codegen or extraction process was running.
- Free disk was 23.6 GB.
- Tasks #1 to #15 were open.
- agy-grid keeps task and claim state in `.agy-grid/board.json`. A copy of the board from 16:50 is in the orchestrator's scratch folder (`board-snapshot-1650.md`).

**What every worker does before pausing:**
- Start no new long operation.
- Leave edited files in a consistent state.
- Put a resume note (what's done, what was in progress, the exact next command) at the top of its `perf-notes/agentN-*.md`.
- Reply to the orchestrator with `PAUSED`.

**Resume steps:**
1. Re-read this file and `SESSION2-jobs.md`.
2. Check that the board still shows tasks #1 to #15 and the claims. Re-issue anything that's missing, using the snapshot.
3. Collect the workers' resume notes.
4. Continue from the critical path: TU23 verified, then codegen (0.0.23.3), then the OFF baseline build, then first boot. In parallel, Agent 6 produces the stubs and its feasibility report.

**Still waiting on the user:**
- Whether the ISO can be deleted after the extraction is verified.
- Whether they have the private native-GPU banks or runtime shader corpus.


### All workers paused at 16:59

All 11 workers replied `PAUSED`. Each has a resume note at the top of its own perf-notes file. The orchestrator's per-agent summary is in `scratch/pause-tracker.md`, in the orchestrator's brain folder.

**Milestones reached before the pause:**
- **compile-one is ready** (Agent 2). Usage: `powershell -NoProfile -File env\compile-one.ps1 path\to\file.cpp -OutDir build\agentN\obj`. Optional flags are `-SyntaxOnly`, `-Db`, `-Config`, `-Target` and `-PrintOnly`. The default database is `build/sdk-dev`. Never build in `build/sdk-dev`.
- **Extraction verified** (Agent 3), 23 checks passed:
  - `game\disc`: 21 files, 7.55 GB.
  - `game\tu23`: 11 files, 1.9 GB.
  - The xexp is TU23 (sha256 a5169f50..., 11,114,496 B).

**Known issues to fix first** (Agent 2):
- The baseline SDK build stopped at 929 of 1410 steps, because the bundled Cygwin `nm` crashes when writing output for the PPC maps.
- `prepare_simde --check` fails. Make sure the fix is the documented `prepare_simde.py` step, not hand edits.
- FidelityFX is OFF in both the baseline and dev trees.

**Code edits that exist but haven't been compiled** (they need the `build/dev` compile database):
- Agent 4: `draw.cpp`, `queries.cpp`, `long_probe.h`, plus new `draw_log_throttle.h` and `draw_cached_flag.h`.
- Agent 8: 7 rexlego files.
- Agent 5: the SSSE3 untile is coded, and its differential test passed on v3.

Agent 7 found that 11 of its baseline fixture tests already fail, because the fixtures are stale against `device.cpp`.

**ETAs, counted from the resume:**

| Milestone | Time after resume |
|---|---|
| SDK built and tested | ~40 min |
| Codegen | about 40 min more, once `rexglue.exe` links |
| First NATIVE_GPU=OFF baseline exe with its `.map` | ~2 h |


## Resume at 17:45 (orchestrator)

agy-grid came back with an empty board (run 2): no tasks, no claims, and a fresh subagent budget of 79.
- I re-issued tasks #1 to #15 at about 17:52 from the 16:50 snapshot, in the same order and with the same subagent grants (27 of 79). agy-grid may renumber them; old numbers map by title.
- Each re-issued task starts with "RE-ISSUED" and points at the worker's RESUME note.
- Tasks #12 to #15 are active now.

**Claim changes against the snapshot:**
- **#1 (Agent 2):**
  - Removes `DimensionsRecomp/rexlego/out/**`. Agent 6 has `out/native-gpu/**` under #12.
  - Adds `DimensionsRecomp/rexglue-sdk/thirdparty/simde/**`, for `prepare_simde.py`.
  - Adds `DimensionsRecomp/rexglue-sdk/cmake/ppc_test_pipeline.cmake`, for the dev-tree fix for the nm crash. That fix is off the critical path.
- **#4 (Agent 5):** adds `DimensionsRecomp/tools/gpu-aot/test_texture_upload_retention_sdk.py`, because item 2 changes the code that file's anchor matches.

**What changed during the pause:**
- **Disk.** C: has 263 GB free; it was 23.6 GB at 16:48. The disk rules are relaxed:
  - Keep big outputs in your own `build/agentN` or `bench/agentN` folder.
  - Ask Agent 1 before writing more than about 20 GB.
  - The ISO stays.
- **Codegen doesn't wait for the SDK.** README-dev says codegen takes a few minutes and writes about 470 MB. `rexglue.exe` already linked in build run 1 (step 901 of 1410, 16:41).
  - Run 1 compiled against unpatched SIMDe. So Agent 2 fixes SIMDe first, rebuilds only the `rexglue` target, and runs codegen from it while the full SDK build resumes in parallel. If codegen runs from a copy of the old exe instead and the build relinks it later, Agent 2 regenerates into `build/agent2/gen-check` and diffs.
  - Run 1 did 929 steps in 457 s, so the remaining 481 steps should take about 10 minutes plus the SIMDe recompiles.
  - The long pole is the game build's ~720 generated TUs: about 1 to 1.5 h at -j10.
- **Native-GPU inputs.** The user hasn't supplied private banks or a runtime shader corpus, so Agent 6 rebuilds them from the public recipe (J1).
- **CPU rules are unchanged.** Only Agent 2 runs full builds. Everyone else uses at most 2 threads, plus `env/compile-one.ps1`.

**Still waiting on the user:** what changed in agy-grid, and confirmation of the ISO and private-bank defaults above.

**ETAs (set at 17:45, revised 17:52 when the re-issue went out):**

| Milestone | Owner | ETA |
|---|---|---|
| SIMDe fixed; `prepare_simde.py --check` passes | Agent 2 | ~17:55 |
| Codegen done; log shows 0.0.23.3; dev junction in place | Agent 2 | ~18:05-18:15 |
| Baseline SDK built and installed (ctest runs alongside and doesn't gate) | Agent 2 | ~18:15-18:25 |
| Stub banks plus `-D` flags | Agent 6 | ~18:15-18:30 |
| `build/dev` ON compile database for Agents 4-8 | Agent 2 | ~18:30-18:45 |
| Feasibility report `agent6-native-aot.md` | Agent 6 | ~18:30 |
| `run-game.ps1` passes its self-test on the fake exe | Agent 3 | ~18:30 |
| Profile analyser plus self-test | Agent 8 | ~19:00 |
| First NATIVE_GPU=OFF baseline exe, with its `.map`, staged in `build/baseline-bin` | Agent 2 | ~19:30 (19:15-20:00) |
| First boot to the menu through the harness | Agent 3 | ~19:45-20:15 |
| Real native banks, DXIL caches and FSR3 libs (J1 c), then the native ON build and boot | Agent 6, then Agent 2 | set from the 18:30 feasibility report |

Each worker has been asked to reply "RESUMED" with an ETA within about 10 minutes. I'll tighten the table from those replies.

**Decision at 18:09: profiler observer effect and the LSP1 trailer (proposed by Agent 8)**
- **Observer effect.** `sample_profiler.cpp` holds `timeBeginPeriod(1)` for the whole process. A `-Profile` run therefore gets guest Sleep of about 1 ms instead of the baseline's 15.6 ms, which hides STATUS item 1, the bug Agent 11 is fixing.
  - Rule: never take frame-time or A/B numbers from a profiled run. Time each configuration with the profiler OFF, and use profiles only to see where time goes.
  - The dev sampler moves to a high-resolution waitable timer, falling back to `timeBeginPeriod` if that isn't available. Baseline profiles keep the old behaviour.
- **LSPX trailer.** This is an optional, append-only block after the samples, written only when `LEGO_SAMPLE_PROFILE` is set. It has a magic, a version and a length, and holds:
  - the QPC frequency, start and end;
  - the round count;
  - the thread names;
  - the timer mode.
  - If any in-repo reader reads to EOF, the trailer is gated behind `LEGO_SAMPLE_PROFILE_TRAILER=1`.
  - The pristine baseline exe has no trailer. So the analyser also accepts a duration taken from the harness run metadata (the trigger window's start and end, recorded by Agent 3).

**Critical path at 18:14 (from Agent 2's logs; Agent 2 hasn't reported yet):**

| Milestone | Estimate at 17:52 | Actual or new estimate |
|---|---|---|
| SIMDe fixed; `rexglue` target rebuilt | ~17:55 | Done by 17:59:45. The rebuild was 128 steps, 103 s. |
| Codegen at 0.0.23.3; dev junction in place | ~18:05-18:15 | Done at 18:03. See note 1. |
| Baseline SDK built and installed; ctest | ~18:15-18:25 | Done at 18:04. See note 2. |
| OFF baseline exe staged in `build/baseline-bin` | ~19:30 | ~19:30 (19:15-19:50). Agent 2 wrote `build-game-baseline.ps1` at 18:12; the game build is starting. |
| First boot | ~19:45-20:15 | ~19:40-20:15 |
| Stubs plus `-D` flags (Agent 6) | ~18:15-18:30 | The stubs folder exists, and `bench/agent6/stub_check` ran at 18:04. I've asked Agent 6 for an ETA. |

1. **Codegen.** It took 129 s and wrote 883 files (887 in the folder, 467 MB).
   - A re-run with `--pointer_table_scan --ignore-stamp` (18:06-18:08) reported "0 written, 883 unchanged", so the output is identical with and without the flag.
   - The project's own tooling passes that flag: `tools/gpu-aot/test_cross_build_producers.py` and the SDK init template.
2. **SDK build and tests.**
   - The resumed build had 166 failed edges. All of them are `tests/ppc/bin/*.map` edges from the nm crash; none are elsewhere.
   - `install` succeeded.
   - ctest passed 216/216, with the PPC tests excluded.

## Status at 18:50 (orchestrator)

**Critical path (from `build/agent2/game-baseline-steps.txt`):**
- The OFF baseline game **linked at 18:40:35** (`build/baseline/legodimensions.exe`, 170 MB). It took three runs:
  1. 18:14, exit 1. `native_lock_elide.cpp` has 3 undeclared callees, `sub_83F99290` and `sub_83F9ABE0`.
  2. 18:21-18:39, exit 1. This run built everything else; the shim's `SHELL:` prefix was not processed (CMake 3.28).
  3. 18:40, two steps, exit 0.
- **Cost of a full game build:** about 21 minutes at -j10. That is much less than the 1-1.5 h guessed at 17:45. Free RAM drops to about 4.7 GB at -j10 (machine: 12 logical CPUs, 31.7 GB).
- **Why run 1 failed:** `native_lock_elide.cpp` includes seven partition headers (`legodimensions_funcs.{154,...,410}.h`). They match the author's `codegen.partition.json`, which is not in the repo, and a fresh codegen lays the partitions out differently.
  - **Agent 2's shim (approved):** `build/agent2/compat/project-include.cmake` force-includes `native_lock_elide_compat.h` into that one file only. The header contains just the two `DECLARE_REX_FUNC` lines. It applies to `build/baseline` and `build/dev`, and the snapshot is untouched.
  - **Source fix in the dev tree (Agent 8, low priority):** make the file independent of the partition layout by declaring its callees itself.
- **`build/dev` ON compile DB:** configured at 18:39.
  - compile-one works for `main.cpp` (87 s) and `native_lock_elide.cpp`.
  - `gpu_native/*` needs the 9 dxc shader headers first. Agent 2's `dev-shader-headers.ps1` (18:43) runs only those dxc commands, so no SDK target is built in the dev tree.
- `build/baseline-bin` is **not staged yet**. Agent 2 has been asked to do this before anything else.

**Agent 6 (J1):**
- (a) Stubs done at 18:13; `stub_check` passes 10/10.
- (b) Feasibility report done at 18:20 ([agent6-native-aot.md](agent6-native-aot.md)). All inputs can be rebuilt from public sources. The runtime shader corpus is gone, so the first native boot will be partly black until capture runs refill it.
- (c) Running:
  - .NET SDK 8.0.428, installed locally under `DimensionsRecomp/research/tools/dotnet` (18:40).
  - DXC 1.9.2609 (18:27).
  - XenosRecomp `current-compiler` in progress (18:44).
  - FSR3 libs building from a copy under `build/agent6/ffx`.
  - Ask 1 (an 8-thread slot for the ~9.6k-shader DXIL compile plus the banks) is granted in principle. It is scheduled after the 50-shader measurement.
- **Agent 6 #5, item 1 done (18:50):** `Save()` in `pipeline_library.cpp` no longer holds the library mutex while it allocates and serializes. The longest hold at 512 MiB fell from 1288 ms to 279 ms, and the saved file is byte-identical. It only affects the native ON build. The extractor builds against a read-only DimensionsModLoader clone in `DimensionsRecomp/research`.
- Agent 6's agy-grid messages arrive cut down to their first line ("RESUMED (18:13)", "Agent 6 status (18:50)"). I took its status from the RESUME note at the top of `agent6-pipelines.md`.

**Reviews:**
- Agent 10's first #15 verdicts on Agent 9's diff went out at 18:31 ([agent10-codegen-review.md](agent10-codegen-review.md)): 4 SAFE, 2 SAFE-IF, 1 insufficient, 1 UNSAFE config combination. They have gone to Agent 9.
- Agent 11's global-mutex design went out at 18:41 ([agent11-global-mutex-design.md](agent11-global-mutex-design.md)) and has been routed to Agent 12 (#14).
- **Decision on the design:**
  - Part A (the `RemoveHandle` use-after-free fix) and the C.4 stash-store order are always on. A lands after Agent 12 answers asks 1, 2 and 5, or at 19:45 if nobody objects.
  - Parts B (`guest_suspend_guard`) and C (`object_lookup_fast_path`) land behind OFF cvars, with C latched at startup.
  - No header edits.
  - B stays OFF until Agent 3's 50-cycle pause test passes on a dev build.

**New rules from 18:50:**
1. **Quiet windows.** Timed game runs happen only inside windows that I announce (the first is ~20:15-20:45). During a window, every worker pauses builds, benches and compiles above trivial CPU until I announce the end. The first boot is functional and untimed.
2. **Batch cut-off 20:15** for dev OFF build 1 (snapshot taken at 20:15, built ~20:45-21:25). Each change in it must be:
   - compile-checked;
   - OFF by default unless proven identical;
   - listed in the owner's perf-notes (files, cvar names and defaults, header edits flagged).

   Later changes wait for the next batch. Agent 2 builds from a frozen snapshot of the sources, so edits made during the build can't leak in. A/B testing then toggles cvars inside one binary.
3. **Codegen options** (Agent 9) can't be toggled at runtime. They get their own codegen output and game build after Agent 10 clears each option. With every option off, the output must match the pin exactly (Agent 10's T1).

**ETAs (set at 18:50):**

| Milestone | Owner | ETA |
|---|---|---|
| OFF baseline exe linked | Agent 2 | **Done 18:40** |
| `run-game.ps1` self-test on the fake exe | Agent 3 | ~18:50, **missing at 19:07**: nothing written since 16:58; pinged |
| Profile analyser plus self-test | Agent 8 | **Done (#13 closed ~19:01)**: self-test 14/14, synthetic tests 36/36, the real 37 MB `.map` parses in 3.6 s |
| `build/baseline-bin` staged and verified (exe, DLLs, PDBs, `.map`) | Agent 2 | **Done 19:01**: every check in `MANIFEST.txt` passes. There are no PDBs (Release links without /DEBUG; the `.map` gives symbols), and nothing imports TracyClient.dll (Release has no Tracy code) |
| compile-one for `gpu_native/*` (9 dxc headers) | Agent 2 | ~19:10 |
| First boot to the menu (functional) | Agent 3 | ~19:15-19:45 |
| 50-shader measurement, then the 8-thread DXIL slot | Agent 6 | ~19:30, then 19:40-20:15 on CPUs 4-11 (hard stop; at most 35 min) |
| Quiet window 1: baseline timing with the profiler OFF, plus one profile run | Agent 3 | ~20:15-20:45 |
| Dev OFF build 1 (SDK + game, from the snapshot taken at the 20:15 cut-off, about 35-40 min) | Agent 2 | ~20:45-21:25 |
| Real native inputs placed (DXIL cache, banks, FSR3 libs) and final flags to Agent 2 | Agent 6 | ~20:30 (FSR3 libs and ABI link-check ~19:45) |
| Native ON build (same snapshot, including the prelink); Agent 3 checks dev OFF build 1 meanwhile, untimed | Agent 2 | ~21:25-22:15 |
| Quiet window 2: A/B by cvar on dev OFF build 1 | Agent 3 | ~22:15-23:00 |
| First native boot (partly black until capture runs) | Agent 3 | ~23:00-23:30 |
| Codegen-option build (Agent 9) | Agent 2 / Agent 9 | after 23:00 |

**Worker reports:** A8 microbench and A/B plan ~19:15; A10 benches ~19:45; A11 `@@done` ~20:15; A12 `@@done` ~20:30.
- **A4 (18:54):**
  - Done and compile-checked against `build/dev`: items 5, 6, 4 and 1, plus the SSE2 fallback. The checks covered `draw.cpp` at v3 and v2, plus `queries.cpp`.
  - Benches: QueryDrawScope went from 44 to 2.5 ns, and the log throttle from 34 to 1.8 ns.
  - Fixtures: 3 patched fixtures pass on base and dev, and 8/8 mutants are caught.
  - `device.cpp` can't be checked until the generated `copy_color_ps.h` exists.
  - Next: state-call elision (`LEGO_NATIVE_ELIDE_STATE_CALLS`, default OFF) plus 10 new `LEGO_NATIVE_STATE_CALLS` columns, by ~19:50.
  - All of it is gpu_native only, so it lands in the native ON build.
- **A5 (notes at 18:41):**
  - Item 1 done: an SSSE3 2D untile. The differential test passed on v3, v2 and sse2 across 3,964,537 copies.
  - Item 2 done: scratch-buffer reuse. The retention and poison tests pass.
  - Item 3 coded: an SSSE3/AVX2 byte swap.
  - Item 4 (the staging pool, default OFF) is not started.
  - Two gpu-aot tests have stale mocks; that problem predates this session.
- **A9 (18:54):** the item-1 register-localization fallback is in the tree.
- **A10 (18:55):** edited `include/rex/ppc/intrinsics.h` and `include/rex/math.h`. Both are in the generated-code closure, so they force a full rebuild.
  - At x86-64-v3, the exhaustive tests, the 240-run known-answer test (KAT) and the math test all pass, with results bit-identical to the old helpers. The change is therefore ON with no cvar.
  - The v2, v3noavx2 and portable configs are still running. All of them must pass before the 20:15 cut-off.
  - **Rule:** `build/sdk/install` is the baseline SDK and is never re-installed. Dev OFF build 1 compiles the game against the snapshot's SDK headers, using its own SDK build and install prefix. Agent 2 confirms this from `compile_commands.json`.
- **Truncated messages:** agy-grid keeps only the text on the `@@to` line. Multi-line messages from Agents 5, 6 and 9 therefore arrived as just their first line. At 18:55 all workers were told to send one-line messages.
- Agents 2 and 7 have not replied since the resume.

**Notes at 19:08:**
- **The Windows session looks locked since 18:07:47.** `LogonUI.exe` is running in session 1, the user's session. The game can start and write its log, but SendInput, screenshots and frame timing need an unlocked desktop with the game in front. The user has been asked to unlock before the first boot and the 20:15 quiet window.
- **Agent 3 has produced nothing since the resume:** no file in `harness/`, `build/agent3` or `bench/agent3` has changed since 16:58, and `run-game.ps1` doesn't exist. Agent 3 was pinged and told to do the first boot by hand from `build/baseline-bin`.
- **My mistake:** at 19:04 I ran `gen_lock_elide.py --help` to see its options. The script ignores unknown flags, so it regenerated `rexlego/src/native_lock_elide.cpp`. `--check` at 19:07 says the file is current and its size is unchanged, so only the timestamp moved (now 19:05:38). Agent 8 has been told. Agent 8 fixed the script at 19:12: `--help` and `-h` exit 0, unknown flags exit 2, and neither writes anything.

## Update at 19:20 (orchestrator)

**Agent 3 is not responding.**
- Its last file write was at 17:00:44, the pause note in `agent3-run-harness.md`.
- It sent "RESUMED (18:01)". Since then it has changed no file in `harness/`, `game/`, `build/agent3` or `bench/agent3`, started no process, and spawned no subagent.
- It hasn't answered the 19:08 ping.

What I've done about it:
- **Agent 8 now has the functional first boot (new task #16).** Agent 8 is free, since #7 closed at about 19:14.
  - The run goes in `build/agent8/runs/`, with `user_data_root` pointed into the run dir, so nothing writes to `game/`.
  - Agent 8 then writes a minimal timing runner in `bench/agent8/run/` as a backup for quiet window 1.
- Agent 3 has been told not to launch the game until Agent 8 posts the result.
- If Agent 3 hasn't replied by 19:40, the quiet-window timing moves to Agent 8. The user will be asked to check Agent 3's tab.

**Agent 2's plan is approved** ([agent2-baseline.md](agent2-baseline.md), "Answers for Agent 1"):

| Step | When | What |
|---|---|---|
| S0 snapshot | from 19:15 | Real-copy snapshot in `build/agent2/snap1`, with per-file SHA256 manifests. |
| S0 pre-build | 19:20-19:40 at -j10 | After 19:40, -j3 on CPUs 0-3 (Agent 6's slot has CPUs 4-11). Pauses if Agent 6's 50-shader measurement needs a quiet machine. |
| S1 refresh | 20:15:00 | About 1 min. |
| Incremental build | after the refresh | 6-10 min, or 22-25 min if a header in the generated-code closure changed after S0. |
| Staging | after the build | To `build/agent2/devoff1-bin`. |

- The dev build uses its own SDK build and install (`build/agent2/snap1-sdk`). Before compiling, Agent 2 checks the `-I` paths and that the installed header hashes match the snapshot.
- **The native ON build reuses the same tree.** Agent 2's probe showed that toggling OFF to ON changes 0 of the 440 generated TUs and leaves the PCH unchanged. It costs about 6-10 min plus Agent 6's real bank TUs (compile time unknown). The OFF outputs are staged first.

**Quiet window 1 only happens if the desktop is unlocked.**
- `LogonUI.exe` has been running in session 1 since 18:07. A locked desktop gives no valid frame timing, so a quiet window would only stop everyone for nothing.
- **If the session is still locked at 20:10, quiet window 1 is cancelled.** Agent 2 then builds right after the 20:15 refresh, and the baseline timing waits until the user is back.

**New task #17 (Agent 12): the `ReXApp::SetGuestPaused` hang** (`rexglue-sdk/src/ui/rex_app.cpp:627-660`). The fix is ask 4 in [agent12-gcr-review.md](agent12-gcr-review.md).
- The hang can happen whether Agent 11's B is on or off. On pause, the code logs and pauses audio after every guest thread is suspended. On unpause, it allocates in `GetObjectsByType` before resuming any thread.
- Fix: keep the pause's thread list, resume first, then do the audio and logging.
- It lands behind a default-OFF cvar, so batch 1 behaves like the baseline. The pause test runs with the fix ON, both with B OFF and with B ON.
- `rex_app.cpp` is compiled into the game from the SDK's `share/rexglue` and isn't in the generated-code closure, so it costs one TU.

**Global mutex (Agent 11, item 7), from Agent 12's #14 verdicts:**

| Part | Verdict | What happens |
|---|---|---|
| A | SAFE | Lands always-on now. |
| C | Safe only if `GetNativeObject`'s create branch holds T exclusive | Agent 11 adds that hold; C stays behind its OFF cvar. |
| B | SAFE | Stays OFF in batch 1. Turned ON only after the 50-cycle pause test, run with the #17 fix ON. |

**Closed:** #13 (about 19:01) and #7 (about 19:14, Agent 8).
- #7's batch list is Â§1 of [agent8-session2.md](agent8-session2.md). It adds no new cvars, changes no defaults, and edits no header that generated code includes.
- The `native_scene_diagnostics` proposal (Â§3) goes to the user once a native ON build boots.

**ETAs (19:20):**

| Milestone | Owner | ETA |
|---|---|---|
| Functional first boot of `build/baseline-bin` (untimed; locked desktop, so log and process only) | Agent 8 | start ~19:25, result ~19:45 |
| S0 pre-build of dev OFF build 1 | Agent 2 | 19:20-19:40 at -j10, then -j3 on CPUs 0-3 |
| 50-shader measurement, then the 8-thread DXIL slot | Agent 6 | ~19:30, then 19:40-20:15 on CPUs 4-11 (hard stop) |
| FSR3 libs + ABI link check | Agent 6 | ~19:45 |
| PPC `.map` fix (step 6) | Agent 2 | ~19:50 |
| Batch cut-off; S1 refresh | all / Agent 2 | 20:15 |
| Quiet window 1: baseline timing with the profiler OFF, plus one profile run | Agent 8 (Agent 3 if back) | 20:15-20:45, **only if unlocked by 20:10**, otherwise cancelled |
| Real native inputs placed + final flags to Agent 2 | Agent 6 | ~20:30 |
| Dev OFF build 1 (incremental from S0), staged to `build/agent2/devoff1-bin` | Agent 2 | 20:45-21:10, or 20:15-20:40 if window 1 is cancelled |
| Native ON build in the same tree | Agent 2 | ~21:10-21:30 (not before Agent 6's inputs, ~20:30) |
| Functional boots of both builds | Agent 8 | right after each staging |
| Quiet window 2: A/B by cvar on dev OFF build 1 | Agent 8 / Agent 3 | needs the unlocked desktop; ~21:30-22:15 at the earliest |
| First native boot (partly black until capture runs) | Agent 8 | after the native build, ~21:30 |
| Codegen-option build | Agent 2 / Agent 9 | after quiet window 2 |

**Notes at 19:25:**
- **#9 done (Agent 10).** `include/rex/ppc/intrinsics.h` and `include/rex/math.h` are always on, and both are in the generated-code closure.
  - Proven bit-identical to the pin: exhaustive 2^32 sweeps, the KAT replay at 240/0, and a mutant self-test.
  - All four configs pass (v3, v2 and v3noavx2 full; portable quick). A real generated TU compiles at the game's flags.
  - Speed at v3: vslo 25.2â2.3 and vsro 32.5â2.0 ticks/op, vslb 7.8â3.4, vctuxs latency 31â20. Element shifts are 3-6x faster at v2 and v3noavx2.
  - The two math.h fixes (`clamp_float<double>` truncation, `rotate_left` UB) change nothing for current callers: every caller passes float, and nothing calls `rotate_left`.
- **#6 done (Agent 7).** `gpu_native/device.cpp`, `device.h` and `present_rect.h`, so it affects the native ON build only.
  - On by default and output-identical:
    - (a) skip the gamma pass for an identity ramp;
    - (b) skip the back-buffer clear when the copy covers it;
    - (c) per-present Win32 window queries moved out from under `g_mutex`.
  - Off-by-default env toggles: (d) `LEGO_NATIVE_UNLOCKED_PACING`, (e) `LEGO_NATIVE_FRAMES_IN_FLIGHT`, (g) `LEGO_NATIVE_LATENCY_WAIT`. (d) needs Agent 4's one-line SwapHook call in `draw.cpp`.
  - The in-game A/B waits for the native boot. Agent 8 runs it while Agent 3 is silent.
- **#15 review 2 (Agent 10).** Agent 9's diff from 18:55 to 19:13 is SAFE or SAFE-IF throughout, and touches no closure header. Asks A-E are open.
  - The gate for the codegen-option build is T8: a recompile-tests option that turns the new codegen options on, because `instr_rlw_lowering.s` only tests the old path today.
- **New task #18 (Agent 10): batch-1 safety review** of the always-on changes that dev OFF build 1 runs, concurrency changes first. Verdicts are due by 20:00 so that UNSAFE items can go behind a toggle or be left out before the cut-off.
- **Profile first, then decide (Agent 10's notes, kept for batch 2):**
  - `GuestToHostFunction` memsets the 2.6 KB `PPCContext` on every hostâguest call (`function.h:464`).
  - `FunctionDispatcher::GetFunction` takes a `recursive_mutex` on the indirect-call fallback.
- **Pre-existing codegen bug (sent to Agent 9):** the scalar `vpkuhus`/`vpkuwus` fallback is wrong when vD == vB. Agent 9 checks whether 0.0.23.3 emits any aliased ones; a fix would go in the codegen-option build.

**#10 done (Agent 11, 19:25).** Full notes are in the Session 2 section of [agent11-kernel.md](agent11-kernel.md).
- **Always on:** part A (the `RemoveHandle` use-after-free fix) and the C.4 stash order. Agent 10 reviews both under #18.
- **Everything else is behind a new cvar that defaults OFF.**
- **Headers:** no existing header was edited. The three new `include/rex/threading_*.h` headers are included only by `.cpp` files, so the generated TUs don't rebuild.
- **C's conditions from Agent 12 are in:** T is held across the create branch (`xobject.cpp` L495), plus the `Restore` asserts and lock-order comments.

The cvars and their microbench results (5 runs each, at most 2 threads, with the machine at 94-100% load):

| Cvar | What it does | Result |
|---|---|---|
| `host_timer_resolution_ms` | `timeBeginPeriod` | Host `Sleep(1)` 16.1 â 4.7 ms; guest `Delay(1 ms)` 16.1 â 5.4 ms |
| `host_timer_throttling_optout` | EcoQoS opt-out | - |
| `precise_guest_sleep`, `wait_timeout_round_up` | Timeouts round up instead of truncating; absolute timeouts are honoured instead of becoming 0 | A 1.5 ms wait went from 16.0 to 5.3 ms |
| `cs_spin` | Bounded spin in critical sections | 9-106x faster at 50-500 ns holds |
| `spinlock_pause_spin` | Pause-loop backoff | Median contended wait 0.15-8 ms â about 0.6 Âµs |
| `clock_lockfree` | Seqlock clock | 2-thread reads 385 â 112 ns. **The old locked clock drifts:** 6-8% fast with two readers (39% at worst). The new one is exact. |
| `tls_bounds_fix` | TLS bounds fix | - |
| `guest_suspend_guard` (B) | Suspend guard | Stays OFF until test G passes |
| `object_lookup_fast_path` (C) | Experimental lookup fast path | Mixed result; run R4 decides |

- **High-res `Win32Timer`: dropped.** High-res waitable timers reject completion routines (error 87), so guest timers keep the standard timer.
- **Recommended ON set for the A/B:** `host_timer_resolution_ms=1`, `host_timer_throttling_optout`, `precise_guest_sleep`, `wait_timeout_round_up`, `clock_lockfree`, `tls_bounds_fix`, `cs_spin`, `spinlock_pause_spin`. The A/B runs are R0-R4 plus test G.
- **New task #19 (Agent 11): test G driver.** It must work on a locked desktop.
  - First try posting focus messages to the game window and look for the "Guest suspended/resumed" log lines. Probe it on the baseline after Agent 8's first boot.
  - If SDL ignores posted messages, Agent 12 adds a default-OFF debug cvar to `rex_app.cpp` by 20:15.
  - Test G runs on dev OFF build 1 with the #17 fix ON, once with B OFF and once with B ON.

**Batch 2 rule (19:32):**
- Agent 2 copies the live tree into the S1 snapshot at 20:15:00 and announces when the copy is done (about 20:16).
- Dev OFF build 1 and the native ON build are built only from that snapshot. Agent 6's real inputs are an explicit copy into it.
- Any edit made after the announcement goes into batch 2, so it can't leak into either build. The batch-2 cut-off will be announced; the earliest is about 22:15, after quiet window 2.
- If a batch-1 build needs a fix after S1, the owner sends Agent 2 an explicit patch for its snapshot copy. Agent 2 never re-copies from the live tree before the next cut-off.
- **New task #20 (Agent 7): present work for batch 2.** It starts after the S1 announcement. The first item is (h): inlining `CurrentDrawPreparation`, which Agent 4 asked for. About 21 files include `device.h` and will rebuild.

**Checkpoint 19:47 (orchestrator):**
- **The baseline boots (Agent 8, #16).** Run dir `build/agent8/runs/1928-first`; details in [agent8-first-boot.md](agent8-first-boot.md) by about 20:00.
  - The TU23 patch applies. The game ran 23,340 frames over 9 min 54 s at 22-53 fps, on the title or menu screen (which can't be seen while the desktop is locked).
  - First frame at 61.1 s after process start; 35 s of that is "Initializing shader storage".
  - 0 errors and 40 warnings (kernel stubs, plus the game probing for `d:\INSTALL0_N.DAT`/`.HDR`). No crash and no hang. Peak RSS 708 MB, commit 1,193 MB, 79 threads.
  - The one WER event (RADAR_PRE_LEAK_64, 19:33:59) is Windows' informational leak heuristic, not a crash.
- **Key finding: every agent command runs on its own hidden desktop** (`WinSta0\exebox-*`). A game launched by an agent is invisible and probably not composited, even after the user unlocks. So:
  - **Agent-launched runs are functional checks only.** Their frame times are labelled "hidden desktop" and never count as timing results.
  - **Nobody tries to get around the hidden desktop** (no `schtasks /it`, `psexec -i`, desktop-switching APIs or similar). It's part of the environment.
  - **Timing and A/B runs are started by the user.** Agent 8 turns its runner into one double-clickable script that runs the whole matrix. It launches each run, closes it with WM_CLOSE from the same process, collects the files and prints a summary. It's dry-run on the hidden desktop first and ready at about 20:30.
  - Window lookups and WM_CLOSE only work from the command that started the game, so test G's driver launches and drives the game in one command.
  - `perf.csv` can't be read while the game runs; watch its size instead.
- **Quiet window 1 is cancelled.** Agent 2 builds right after the S1 refresh. Baseline timing happens when the user is back and starts Agent 8's runner.
- **Test G:** Agent 12 adds the default-OFF debug pause-cycle cvar to `rex_app.cpp` now, as part of #17, instead of waiting for the focus-message probe. Agent 11 still probes posted focus messages from a single command, in the game slot 19:50-20:05. Agent 8 has the slot 20:05-20:15 for its runner dry run.
- **Agent 3: deadline passed.** No file writes since 17:00:44 and no replies. Agent 8 owns all timing runs. The user has been asked to check Agent 3's tab.
- **Agent 2's S0 pre-build stopped, then restarted at 19:47.** The snapshot SDK configure ran from 19:26:36 under full load. At 19:41, stopping its wrapper also killed the configure (the log stops at 19:41:37 without "Build files have been written").
  - Agent 2 restarted it at 19:47 from snapshot S0d, at -j3 pinned to CPUs 0-3: configure, then SDK, then game.
  - It won't finish by 20:15, so the post-S1 build covers the rest of the SDK plus all 440 generated TUs, about 25-30 min at -j10.
  - S0d includes Agent 12's 19:27 edits to `logging/macros.h` (a closure header) and `rex_app.cpp`.
- **Agent 2's step 6** (PPC `.map` fix) slips to about 20:05. Running nm under `cmake -P` with stdout on a pipe stops the crash; the output is now written with LF line endings.
- **Agent 4's batch list** is Â§S2.1 of [agent4-draw-path.md](agent4-draw-path.md) (19:46).
  - Redundant-state elision is done and OFF by default (`LEGO_NATIVE_ELIDE_STATE_CALLS=1`). It covers the index buffer and blend factor; the oracle, mutant and audit tests pass.
  - Agent 7's `PaceFrameBeforeLock()` is in SwapHook (`draw.cpp:5344`) and does nothing unless `LEGO_NATIVE_UNLOCKED_PACING` is set.
  - The one widely included header edit is `long_probe.h` (7 TUs).
  - Next: the Agent 5 registry diff (about 20:05), then @@done 3. The threaded items T1-T13 wait for native timing data; they only matter if threaded mode becomes the default.
- **Agent 10's #18 review also covers Agent 12's `logging/macros.h` edit.** It expands in all 440 generated TUs, so it must add no work at call sites while Agent 12's cvars are OFF.
- **Agent 6's DXIL slot hadn't started at 19:43** (the machine was nearly idle). Pinged; the 20:15 hard stop stands.
- **New task #20 (Agent 7)** is issued, as described under the batch-2 rule above. Agents 5 and 9 have been pinged for status.

**ETAs (19:47), changed rows:**

| Milestone | Owner | ETA |
|---|---|---|
| Functional first boot of the baseline | Agent 8 | **done** |
| Test G focus-message probe (game slot) | Agent 11 | 19:50-20:05 |
| Runner dry run (game slot) | Agent 8 | 20:05-20:15 |
| Quiet window 1 | - | **cancelled** |
| User-started timing runner ready | Agent 8 | ~20:30 |
| Dev OFF build 1, staged to `build/agent2/devoff1-bin` | Agent 2 | ~20:45 (Agent 2's estimate with window 1 cancelled; was 20:15-20:40) |
| Native ON build in the same tree | Agent 2 | ~21:00-21:15 (after Agent 6's inputs, ~20:30, and the OFF staging) |
| Baseline and A/B timing runs | the user, with Agent 8's runner | when the user is back at the unlocked desktop |

**19:54 (orchestrator):**
- **Agent 6's slot started at 19:51:29**, 11 min late. Its subagent had been waiting on a command-approval prompt since 19:29, so the subagent's 19:40 timer never fired. Agent 6 killed the subagent and started `run-slot.ps1` itself.
  - 32 shards on CPUs 4-11. No new step starts after 20:10, and the hard kill is at 20:14:30.
  - Main DXIL cache ~20:03; float-blend and instanced banks ~20:12. A bank that isn't done by 20:14:30 falls back to its stub.
  - The real microcode index replaced the stub at its fixed path at 19:53, so S1 picks it up.
  - Native ON flags go to Agent 2 at ~20:30, and PSO-stats run specs go to Agent 8 by 20:20.
- **Rule: approval prompts.** A subagent waiting on a command-approval prompt stays blocked until the user is back. Nobody reruns the flagged command through another agent or subagent; plan around it and tell Agent 1 what's blocked. Agent 3 may have been stuck on one since about 17:00.

**20:08 (orchestrator):**
- **Done:** #18 (Agent 10), #17 (Agent 12), #19 (Agent 11) and #3 (Agent 4).
  - **#18:** 0 UNSAFE across the always-on batch-1 changes from Agents 7, 8, 11 and 12, including the `logging/macros.h` add-on. Details: [agent10-batch1-review.md](agent10-batch1-review.md).
    - One SAFE-IF: the cheat engine's FreezeMain is safe as long as `frozen_`/`cheats_` change only under `apply_mutex_`, which holds today.
    - Generated code has no log call sites, so `macros.h` costs the generated TUs only parse time. Each log site in SDK and rexlego TUs grows by 66-67 B.
  - **#17:** `rex_app.cpp` gets `pause_safe_order` (default false) and `debug_pause_cycle_ms`/`debug_pause_cycle_count` (default 0 = off). In Agent 12's replica, the old order hangs 299 times per 1,000 pause cycles, guard B alone 173 times, and the new order 0 times in 5,000.
  - **#19:** the test G driver works from an agent command in watch mode.
    - Posted focus messages can't work on any desktop, because SDL 3.5 recomputes focus from `GetForegroundWindow()`. So test G uses Agent 12's debug cvars.
    - It runs on devoff1-bin, both halves in about 6 min.
  - **#3:** default-path draw items 1, 4, 5 and 6 save about 175 ns per draw when no queries are live. Elision is OFF by default. T1-T13 are deferred.
- **Agent 5 is still unresponsive.** Its files haven't changed since 18:39.
  - Items 1-3 stay in batch 1: the RESUME block of [agent5-uploads.md](agent5-uploads.md) and its 18:53 "done and verified" describe them as byte-identical by construction, and they passed differential tests.
  - They affect only the native ON build.
- **New task #21 (Agent 10):** the same safety review for the always-on changes that only the native ON build runs (Agent 4's default-path items and Agent 5's items 1-3). Verdicts are due by 20:45, before the native ON build.
- **The batch-1 list went to Agent 2** for S1 at 20:15:00.
- **Game slots once devoff1-bin is staged (~20:45):** Agent 8's functional boot first, then Agent 11's test G, then Agent 8's native boot once the native build is staged. One game at a time.

**20:13 (orchestrator):**
- **Done:** #14 (Agent 12, ~20:09) and #11 (Agent 12, ~20:10).
  - **#14:** A (always on) landed at `object_table.cpp:318-322`. B is safe, but goes ON only after test G passes with `pause_safe_order=true`. C's four changes landed (for example `xobject.cpp:490-496`).
    - **Follow-up hazard (batch 2):** `AudioSystem::Shutdown` terminates the audio worker after its timeout (`audio_system.cpp:207-213`, then `XThread::Terminate` â `TerminateThread`). The worker takes G and runs guest callbacks. Killing it while it holds G leaves G owned forever, and the process hangs. Killing it while it waits for G crashes the next waiter inside ntdll (Agent 12's S4 g1). This goes to Agent 12 as a batch-2 task.
  - **#11:** five SDK cvars, all default false: `io_coalesce_scatter_reads`, `io_lockless_watch_check`, `log_level_gate`, `vfs_defer_open_exists_check`, `io_unlocked_file_reads`.
    - Bench results:

      | Bench | What changed |
      |---|---|
      | B1 | Scatter reads 5.3-5.7x faster (GAME.DAT: 2308 vs 406 MB/s) |
      | B2 | Contended read 8.9 Âµs â 55 ns |
      | B3 | Open hit 184 â 92 Âµs; miss 55 â 133 Âµs, and misses are ~0% in game |
      | B4 | No gain on its own; overlapped handles would give 1.44x (left as a follow-up) |
      | B5 | Disabled log call 4.2-6.3x cheaper with the gate on; 1.0x with it off |

    - The in-game A/B specs are with Agent 8.
- **#21, first answer (Agent 10):** the `macros.h` verdict was measured on the 19:54 headers. Agent 10 then re-read the 19:54 source delta. SAFE, unchanged.
- **Batch-1 patch approved, native ON only (Agent 7, perf.csv rows):**
  - The problem: the native present calls `ResetFrameCounters()` but never `WriteCsvFrame()`, so a native `perf.csv` would be header-only and Agent 8's runner would see no frames.
  - The fix is 2 lines after `device.cpp:2264`, in the same order as `Profiler::Flip` (`counter.h:110-111`). It does nothing unless `--perf_log_csv` is set.
  - Agent 2 applies it to the snap1 copy with a hash-checked copy (Option A in `build/agent7/batch1/perf-csv-rows.README.txt`). Don't use `git apply` here: under the parent repo it prints "Skipped patch" and exits 0 without applying anything.
  - Dev OFF build 1 is unaffected, because it doesn't compile `gpu_native`. Agent 7 carries the same 2 lines into the live tree in batch 2, and Agent 10 adds the patch to #21.
  - **Check during the native boot:** the number of `perf.csv` rows should be about the number of frames presented (no doubled rows).
- **New work:**
  - Agent 12: the audio shutdown fix (batch 2: design now, edit only after the S1 announcement).
  - Agent 11: run test G on devoff1-bin in the game slot after Agent 8's functional boot. Agent 8 hands the slot to Agent 11, and Agent 11 hands it back to Agent 8 for the native boot.
- **Unchanged:** the desktop was still locked at 20:11 (LogonUI). Agents 3, 5 and 9 are still silent. Agent 4 is on standby until there is native timing data (T1-T13).

**20:24 checkpoint (orchestrator):**
- **S1 game build failed, and Agent 2 has not announced S1.** The pre-build steps from S0d ran in order:

  | Time | Step | Result |
  |---|---|---|
  | 19:51-20:10 | SDK build, -j3 | exit 0 |
  | 20:10-20:11 | SDK install | exit 0 |
  | 20:11 | Game configure (`snap1-off`) | exit 0 |
  | 20:11 | Gate | ok |
  | 20:11:25 | Game build | **failed after 0.5 s** |

  - **Why the game build failed:** `snap1-off` is a fresh build dir, so ninja re-ran the codegen custom command (`rexglue.exe codegen --pointer_table_scan ...`). Codegen then failed with `Entrypoint XEX not found: build/agent2/snap1/DimensionsRecomp/rexlego/../../game/disc/Default.xex`. The snapshot has no `game/`, and `baseline/` has no `game` junction either.
  - `snap1-steps.txt` logs this step as `exit=0`, because `start /b /wait` hides ninja's exit code.
  - No build processes were running at 20:22. Agent 2's last tool write was at 20:07. Pinged with the evidence and two requirements:
    1. Codegen must not change the TUs. Either junction `snap1/game` â `game` and hash-check all 440 TUs against the baseline set, or keep the edge from running.
    2. The step check must read the log, not `start`'s exit code.
- **Agent 6's slot** (19:51-20:11, 100% machine load):
  - 32/32 shards, with 0 failures.
  - Main DXIL cache merged: `lego-dxil-cache.cpp` is 35 MB, with 9,601 entries.
  - HLSL dump merged: 9,588 files.
  - Float-blend bank: real, 386 variants.
  - Instanced bank: still running on 1 CPU (affinity 0x20) since 20:14:30, with about 1,375 of about 2,400 jobs done by 20:18. It falls back to its stub if it isn't done before the native build.
- **Run specs:** Agent 8 has `matrix.json`, `matrix-native-tier1.json` and `matrix-native-pso.json` (20:13-20:14). `run-timing.ps1.new` was last edited at 20:15, and no dry run has been reported yet.
- **Other agents:**
  - Agent 10 started `agent10-native-review.md` at 20:22.
  - Agent 11 is writing the test G session scripts.
- **Silent agents, by latest file write:**

  | Agent | Latest write |
  |---|---|
  | Agent 3 | 17:00:44 |
  | Agent 5 | 18:49:34 |
  | Agent 9 | 19:25:50 (`bench/agent9/flush_harness.cpp`) |

- **ETAs, provisional until Agent 2 replies:**

  | Milestone | ETA |
  |---|---|
  | devoff1-bin | ~21:05 (was ~20:45) |
  | Test G | ~21:10-21:20 |
  | Native ON build | ~21:20-21:35 |

**20:26 (orchestrator):**
- **#21 done (Agent 10): 24 SAFE, 0 SAFE-IF, 0 UNSAFE.** It reviewed the always-on changes that only the native ON build compiles, at their defaults. Details: [agent10-native-review.md](agent10-native-review.md); diffs against the baseline are in `build/agent10/b2`.

  | Owner | Items | Verdict |
  |---|---|---|
  | Agent 4 | Draw items 1/4/5/6, the SSE2 `#else` path, both new headers, the default-off paths | 7 SAFE |
  | Agent 5 | Upload items 1-3 | 6 SAFE |
  | Agent 6 | Batch 1 at OFF defaults (`pipeline_async.h` isn't compiled) | 10 SAFE |
  | Agent 7 | `perf-csv-rows.patch` | 1 SAFE |

  - **Agent 4:** `active_queries` is the only item that depends on ordering. It gets that ordering from `LockRecording` (`queries.cpp:95`) inline, and from the recorder barrier in threaded mode.
  - **Agent 5:** the byte-identical claim holds. `test_untile` covers the copier as shipped. Full `-c` compiles of `textures.cpp` and `buffers.cpp` against `build/dev` exit 0. These items have no runtime OFF switch; the revert recipes are in Agent 10's S2.
  - **Agent 7:** the patch does nothing without `--perf_log_csv`, and it can't add duplicate rows. Native mode clears `gpu_plugin`, so `Profiler::Flip` never runs (`legodimensions_app.h:114-115`).
- **The native ON build is cleared on review.** It now waits only on devoff1-bin (Agent 2) and Agent 6's final flags and inputs.

**20:31 (orchestrator):**
- **#12 done (Agent 6, J1): all ten native ON inputs are rebuilt from the public recipe** (reblue-XenosRecomp 339af41 plus the patch, DXC 1.9.2609, gpu-shader-extract on disc plus TU23). They are staged in `DimensionsRecomp/rexlego/out/native-gpu` (git-ignored).
  - **Staged inputs:**

    | Input | Contents |
    |---|---|
    | Main DXIL cache | 9,601 shaders, 35 MB |
    | Microcode index | 19,116 records, at its fixed path |
    | Float-blend bank | 386 variants |
    | Instanced bank | 2,473 variants; one shader is skipped, so it keeps non-instanced draws |
    | FSR3 libs | In `rexglue-sdk/bin/ffx_sdk`; link-checked, and the FSR3 context is created OK |

  - **Stubs by design:** the runtime cache and the temporal bank stay stubs until the capture runs. Native frames that depend on the temporal bank may render partly black in the first native boot.
  - **Prelink smoke test on the real cache:** PASS. 19,064 linked variants in 263 CPU-s at 1 job, embed `numeric_and_literal_identical=true`, 65.7 MB `linked-bank.obj`.
  - **Agent 2 has what it needs:** the copy list with sha256, the snap-native-inputs commands and the full `-D` flag set, all in S5 of [agent6-native-aot.md](agent6-native-aot.md). The first-boot and capture plan is in S6, and the measurements are in S7.
  - Agent 6 keeps #5 (pipelines/PSO) for batch 2.
- **Agent 2 is still inactive at 20:31.** No new files in `build/agent2` since 20:11:25, no build processes, no `snap1/game` junction, and no reply to the 20:25 ping. The 20:34 timer decides what to tell the user.

**20:37 (orchestrator):**
- **The desktop is unlocked** (LogonUI was gone at 20:36). Approval prompts were released at about 20:34.
  - **Agent 9 is back.** A tool call had been hanging since 19:23.
    - Asks 1-3 are done. T2 replaces the `emit_interior_entries.cpp:240-252` break with positive checks. T4 makes a handoff error fail `write()`, and T5 rejects `non_argument` without `non_volatile`.
    - E/T1 PASS: all-off codegen matches the pin in 883 of 886 files; the other 3 are `codegen.d` and two stamp files.
    - vpkuhus128: 14 sites, none aliased, so no option is needed.
    - B (VMX fallbacks): 0 mismatches over 148.6M cases x 3 configs.
    - Next, by about 21:45: A/T8, C (musttail on every TU, plus a tail-chain depth test) and D (a late-jump-table fixture). All of these are default OFF.
    - The 20:35 `rexglue codegen` run went to `build/agent9/generated/locA`, not the junction, which is unchanged since 18:15.
  - **Agent 5 is back.** One command had been waiting on an approval prompt from 18:54 to 20:34.
    - Items 1-3 are in batch 1, and Agent 10 rated them 6 SAFE.
    - Batch 2, by about 21:50:
      - item 4, the texture staging pool (`LEGO_NATIVE_TEXTURE_STAGING_POOL`, default OFF);
      - Agent 4's owner-reference edit (a);
      - if time allows, `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD` (default OFF), which restores the old upload path so items 1-3 can be A/B'd in one binary.
- **Agent 2 was still inactive at 20:36.** Its last file is from 20:11:25, and no ninja is running. The user has been asked to check its tab for a pending prompt.
- **S1 has not been taken.** Agent 2 got stuck before the 20:15 refresh. Rule broadcast: no edits under `DimensionsRecomp/**` until Agent 2 announces S1; agents work only in `bench/`, `build/` and `perf-notes/`. Edits made since 20:15:00 are being scanned and will be reported to Agent 2.
- **Timing:** the runner is `bench/agent8/RUN-TIMING-MATRIX.cmd`, but Agent 8 hasn't confirmed it's ready yet. Timing runs wait until devoff1-bin (and ideally the native build) is staged, and then go in a quiet window.
- **20:39 scan:** 0 files changed after 20:15:00. Scanned: `rexlego/src`, the rexlego config, manifest and CMakeLists, and the SDK's `src`, `include`, `tests`, `cmake` and CMakeLists, plus `DimensionsRecomp/tools`. So the live tree still matches the 20:15 batch-1 state. As long as the edit hold lasts, Agent 2 can refresh snap1 straight from the live tree when it resumes.

**20:55 (orchestrator):**
- **Agent 2 took S1 at 20:41:57. It is the 20:15 batch-1 state** (my 20:39 scan found no edits after 20:15:00).
  - S1 vs S0d: 23,790 files; 1 added, 5 changed, 0 removed, 0 tampered or raced.
  - Two closure headers changed (`rex/logging/api.h`, `rex/logging/macros.h`), so all 440 generated TUs rebuild. `generated/` is still the copy from baseline.
  - Manifest `MANIFEST-S1-2041.tsv` (sha256 `f81b1499â¦`); diff `build/agent2/snap1/DIFF-S1-2041.txt`.
- **The edit hold is lifted** (broadcast 20:55). Batch-2 edits may start in files each agent has claimed. Both batch-1 builds compile only S1 plus explicit, hash-checked patches, so edits in the live tree can't leak into them. The batch-2 cut-off will be announced later, and won't be before 22:15.
- **Agent 2's build steps:**

  | Time | Step | Result |
  |---|---|---|
  | 20:43:55-20:48:26 | SDK incremental, -j10 | exit 0 |
  | 20:48:26-20:49:17 | SDK install | exit 0 |
  | 20:52:14 | Game configure | OK |
  | 20:52:19 | `gen-check.py` | PASS |
  | 20:52:20 | `snap-gate.py` | FAIL (false positive, below) |
  | 20:54:09 | Gate rerun | PASS |
  | 20:54:09 | Game build, -j10 | started |

  - **Hidden exit codes are fixed.** `build-snap.ps1` now checks `$LASTEXITCODE` and greps the logs for ninja and CMake errors.
  - **Codegen can no longer change the TUs.** The snapshot game trees run the codegen edge with `build/agent2/codegen-frozen/codegen-frozen.exe`. It writes nothing; it only checks that the pinned output is present. The edge has `restat = 1`, so the no-op doesn't make ninja recompile.
  - **`gen-check.py` runs before every game build.** It requires the snapshot's `generated/` to equal baseline's: 887 files, 886/886 sha256-identical (490 MB). The only allowed difference is the snapshot paths in `codegen.d`.
  - **The gate's 20:52 failure was a false positive.** The only flagged file was `rex/version.h`, which the SDK configure generates from `include/rex/version.h.in`. The snapshot has only the template, and the installed copy is byte-identical to `snap1-sdk/include/rex/version.h` (sha256 `9B9D945Câ¦`). Agent 2 now allows configure-generated headers only when they hash-match the build-dir copy.
- **Agent 7's perf-csv copy isn't in Agent 2's scripts yet.** I reminded Agent 2 to apply it, hash-checked, before the native build and to log the result as S1+p1.
- **ETAs (a full game build took about 21 min at -j10 for baseline):**

  | Milestone | ETA |
  |---|---|
  | devoff1 links | ~21:15-21:20 |
  | devoff1-bin staged | ~21:20-21:25 |
  | Agent 8 functional boot | ~21:25-21:30 |
  | Test G, both halves (Agent 11, #23) | ~21:30-21:45 |
  | Native ON build: 440 TUs, native sources, prelink | starts after devoff1 links; staged ~21:50-22:00 |
  | Agent 8 native boot | ~22:00-22:05 |
  | User-started timing runs, in a quiet window | from ~22:00 |

  - If the user has to leave before about 22:00, a baseline-vs-devoff1 timing run can go at about 21:30 instead, with the native build paused while it runs.

**21:15 (orchestrator):**
- **devoff1-bin is staged** (Agent 2, 21:08) in `build/agent2/devoff1-bin`.
  - 7 files plus `MANIFEST.txt`, 214.2 MB in total. The manifest's sha256 is `1E81AA5Eâ¦`, and every artifact check passed.
  - The game build took about 13 min at -j10 (20:54:09 to the exe at 21:07:17).
- **S1+p1 is applied.** Agent 7's perf-csv copy is in snap1 and was hash-checked: `device.cpp` went from 4C15043Eâ¦ to 4DC63FA0â¦ (127,148 B). It's recorded in `build/agent2/snap1/PATCHES-S1.tsv`.
- **The native ON build started at 21:07:46** in `build/agent2/snap1-on`.
  - It was configured at 20:58 from S1+p1 plus Agent 6's inputs (N1/N1i/N1d).
  - Settings: -j10 and `LEGO_GPU_PRELINK_JOBS=10`.
  - gen-check and the gate both passed.
- **Game slot:**
  - Agent 11 ran a check-only pass at 21:10:51. The build defines `pause_safe_order`, `guest_suspend_guard`, `debug_pause_cycle_ms` and `debug_pause_cycle_count`. Nothing was started.
  - Agent 8 has been asked to run the functional boot now and then hand the slot to Agent 11 for test G (#23). Its native boot comes after test G.
- **#20 is done (Agent 7, batch 2, in the live tree since 20:48):**

  | Item | Change |
  |---|---|
  | (h) | `CurrentDrawPreparation` is inlined (`device.h:93-95`). 18 TUs rebuild. |
  | (p) | The `WriteCsvFrame` lines (`device.cpp:2275-2276`) |
  | (c') | Agent 10's gate comment |
  | (i) | The FPS meter merges touching cells into single-rect clears. It's ON by default because the output is identical: 640,064 cases are pixel-identical, and clears per present drop from 79.7 to 35.1. `LEGO_NATIVE_FPS_CELL_RECTS=1` restores the batch-1 path. |

  - Tests: the 18 includers syntax-check clean. The gpu-aot fixtures are unchanged (the same 6 pass and the same 11 stale ones fail).
- **Agent 6's async-PSO patch to `draw.cpp`:**
  - Agent 4 rated it SAFE. It's opt-in through `LEGO_NATIVE_PSO_ASYNC`.
  - The default path is identical, except for one cached static-bool test and two null `Find` tests on a pipeline miss.
  - `draw.cpp` is granted to Agent 4 for batch 2, and Agent 4 applies the patch with a hash check.
- **Agent 10 has a rolling batch-2 review:** Agent 7's #20, then Agent 6's patch, then Agent 12's #22, then Agent 5's batch 2.
- **ETAs:**

  | Milestone | ETA |
  |---|---|
  | devoff1 functional boot (Agent 8) | ~21:15-21:22 |
  | Test G, both halves (Agent 11) | ~21:22-21:40 |
  | Native ON build staged | ~21:25-21:35 |
  | Native boot (Agent 8) | after test G, ~21:40-21:46 |
  | Quiet window and user-started timing runs | from ~21:45-21:50, if the runner is confirmed |

**21:35 (orchestrator):**
- **The devoff1 functional boot passed** (Agent 8, `build/agent8/runs/2125-devoff1`).
  - It reached guest rendering: 7,610 `perf.csv` rows in about 193 s on the MX570.
  - The log has 0 errors and 40 warnings, the same set as baseline. No crash or hang.
  - First frame came at 23.7 s, against 17.7 s for the warm baseline boot. The extra 6 s falls between `SetInterruptCallback` and the first frame. Only a second boot can tell whether it's a first-run cost or a regression; the matrix's unscored cold run per binary covers that.
  - Peak working set was 690 MB, peak commit 1,191 MB, and there were 83 threads.
  - WM_CLOSE gave a clean exit 0 after 14.0 s.
  - The game slot went to Agent 11 for test G at about 21:32.
- **The native ON build failed. The only error was in `thirdparty/plume/plume_d3d12.cpp:505`** (21:24:59, at step [459/553]; `ninja: build stopped: cannot make progress due to previous errors`).
  - **Cause: the installed Windows SDK is too old.** `D3D12_HEAP_TYPE_GPU_UPLOAD` is undeclared because the only Windows SDK on this machine is 10.0.22621.0, and its `d3d12.h` doesn't have that enumerator.
  - The source matches what the project expects: it is the pinned public Plume `e0c8871` plus its 6 patches (`tools/gpu-aot/prepare_plume.py`), and the live and snapshot `plume_d3d12.cpp` are identical (`B88E4E86â¦`). That source expects a newer `d3d12.h`. The Agility SDK and DirectX-Headers copies of `d3d12.h` bundled in FidelityFX-SDK all define the enumerator as 5.
  - This is the first full native build in this environment; no build dir has ever compiled `plume_d3d12.cpp`.
  - **Fix (S1+p2, Agent 2):** change line 505 to `return static_cast<D3D12_HEAP_TYPE>(5);`. It gives the same value, works with any `d3d12.h`, and doesn't mix header versions. After that, the native build resumes incrementally.
  - **Live tree, batch 2 (Agent 6):** the same change, added as a `prepare_plume.py` patch.
  - Installing Windows SDK 10.0.26100 would be the alternative, but it needs the user and admin rights.
- **#5 is done (Agent 6).** Items 1-3 are in S1, all off by default.
  - Autosave now serializes outside the library mutex: the lock is held 3.65 ms instead of 6.25 ms, or about 202 ms instead of 346 ms at 512 MiB.
  - The `LEGO_NATIVE_PSO_STATS` counters are added.
  - Item 4, async PSO, goes into `draw.cpp` through Agent 4 (#24).
  - The only `pipeline_snapshot.h` change after S1 (20:48:11) is a comment explaining why the buffer must be zero-filled.
- **Timing:** Agent 8 still hasn't confirmed that `RUN-TIMING-MATRIX.cmd` is ready, so I asked again in one line. The quiet window is planned for ~21:50, after test G and the native rebuild. The baseline-vs-devoff1 timing comes first, and the native boot after the window.
- **ETAs:**

  | Milestone | ETA |
  |---|---|
  | Test G (Agent 11) | ~21:33-21:50 |
  | Native ON build staged, after p2 | ~21:50 |
  | Quiet window and user-started timing (baseline vs devoff1) | from ~21:50-22:00, once the runner is confirmed |
  | Native functional boot (Agent 8) | after the timing window |

**21:55 (orchestrator):**
- **The native ON build is fixed and staged.** Agent 2 applied S1+p2: `plume_d3d12.cpp:505` now reads `static_cast<D3D12_HEAP_TYPE>(5)` (`B88E4E86â¦` â `564568D4â¦`, logged in `PATCHES-S1.tsv`), and `prepare_plume --check` still passes on the snapshot. The build resumed without a reconfigure from 21:36:54 to 21:44:14 and exited 0.
  - `build/agent2/native-bin` was staged at 21:48: 8 files, 363.5 MB, 48/48 artifact checks PASS.
  - The exe is `3B329E95â¦` and carries native GPU fingerprint `befeb1184e6c7abc`. MANIFEST is `91F2F817â¦`.
  - `rexruntime.dll` and `rexgpu-xenos.dll` are identical to devoff1-bin.
- **Test G on devoff1-bin (Agent 11):**
  - Half 1 (safe order, B OFF): PASS 50/50.
  - Half 2 (safe order, B ON): PASS 50/50, with pauses of ~1.0 s (max 1.5 s) and 0 error lines.
  - Control (`pause_safe_order=false`): INCONCLUSIVE, most likely a hang. It stopped at 4/50, the UI was silent for 9.5 s (just under the 10 s bar), and WM_CLOSE was ignored, so it was killed at 30 s.
  - **B (`guest_suspend_guard`) is eligible for A/B runs with `pause_safe_order=true`.**
- **Agent 8 sent GO** for `RUN-TIMING-MATRIX.cmd`, which runs `matrix-base-vs-devoff1.json`: 1 unscored cold run per binary, then 5 runs each in ABBA order, each a 60 s warm-up after the first frame plus a 60 s window. That is 12 games, â41-48 min.
  - The quiet window was announced at ~21:55, with the user starting at 22:00 or later.
  - At 21:53, Agent 9's codegen was still running (`build/agent9/bin/rexglue.exe codegen`, `gen.ps1 -Variant off3`). The preflight checks neither `rexglue` nor `clang++`, so I check the machine myself at 21:59.
  - Background load that isn't ours: chroma-mcp python (~2 cores), dllhost 33552 (~0.5 core, thumbnail cache, running since 11/16) and Defender. Free RAM is ~10 GB; the runner needs â¥ 6 GB.
- **The agy-grid rejected the live-tree plume task for Agent 6**, because the file overlaps Agent 2's `thirdparty/plume/**`. I re-issued it without the plume file:
  - Agent 6 writes the `prepare_plume.py` patch and its test.
  - Agent 2 makes the live file match p2 with a hash-checked copy.
- **Agent 10, #25:**
  - Agent 7 #20 items (h), (i), (p) and (c'): SAFE.
  - Agent 6's async-PSO hunks in live `draw.cpp`: SAFE at the default and SAFE-IF ON. The condition is that exit goes through `HostDevice::Shutdown`, because the async threads are never joined.
  - `pipeline_snapshot.h` is comment-only: SAFE.
  - #15 review 3: Agent 9's `cr_compare_so_zero` is SAFE at the default.
- **Agent 4, #24 part 1 is done.** `draw.cpp` went from `751C219Eâ¦` (= S1) to `50AA3B1Dâ¦` (Agent 6's patched file).
  - compile-one exits 0 on v3 and v2. Fixtures are 9/26 with the same pass/fail sets as before.
  - Part 2 (T1-T13) needs functional rows N1-N3 on native ON (`perf-notes/agent4-draw-path.md` Â§S2.12).
- **Plan after the window:**
  1. Analyse the matrix.
  2. Agent 8's native first boot on native-bin.
  3. Agent 4's N1-N3 functional rows.
  4. Agent 11's control rerun with a dump.
  - S2 is cut at the window's end. Owners Agent 10 has cleared come from the live tree; the rest stay at S1 (hash-checked). Then the devoff2 and native2 builds.
- **ETAs:**

  | Milestone | ETA |
  |---|---|
  | Timing matrix (user-started) | starts 22:00 or later, done ~22:45 |
  | Native first boot (Agent 8) | ~22:50 |
  | S2, then the devoff2 and native2 builds | ~22:50-23:10 (incremental if S2 is patched onto snap1) |
  | Second timing window (Agent 11/12 settings, B, native toggles) | ~23:30, if the user is available |

**22:21 (orchestrator):**
- **Quiet window 1 ended without a timing run.** The PC locked at 22:06:46 (LogonUI) and no matrix had started by the 22:20 deadline. The machine had been quiet since ~21:57 (Agent 9's codegen finished at 21:56). The user reopens the window by messaging "ready for timing".
- **Functional game slot, run on the hidden desktop while the PC is locked:**
  1. Agent 8's native-bin first boot.
  2. Agent 4's N1-N3.
  3. Agent 11's control rerun (#23).
  4. Agent 3's two harness runs (#2).
  - Agent 8's `first-boot.ps1 -StopWhenUnlocked` starts a game only while LogonUI is up and closes it within ~3 s of an unlock.
- **Agent 10 (#25) cleared batch 2 for S2 at the defaults:**
  - Agent 7's #20.
  - Agent 6's async-PSO in `draw.cpp` (now SAFE when ON too).
  - Agent 5's 8 files, including the new `upload_legacy_paths.h` and Agent 4's (a). Legacy ON is SAFE; staging pool ON is SAFE-IF the A/B shows no corruption.
  - Agent 12's #22 with `audio_shutdown_detach_worker` off. ON is SAFE-IF: flip it only in batch 3, after the 1000-run replica, and only if we accept that guest code on a detached worker can outlive `kernel_state_`, as TerminateTitle stragglers already can.
- **The live `plume_d3d12.cpp` equals p2 (`564568D4â¦`)**, so S2 needs no plume patch. Agent 6 (#26) adds the matching `prepare_plume.py` patch.
- **#4 is done (Agent 5).**
  - Items 1-3 are in S1: untile 7-17x faster, zero-fill removal, SIMD byte swap 3-22x faster.
  - Batch 2 is default OFF: `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD` and `LEGO_NATIVE_TEXTURE_STAGING_POOL`.
  - The A/B (`bench/agent5/matrix-native-uploads.json`) needs native2.
- **#27 (Agent 11):** the SDK exit-path fix for HalReturnToFirmware `exit(0)` and XamShowDirtyDiscErrorUI `exit(1)`. Batch 3.
- **#2 (Agent 3):** the `run-game.ps1` self-test passed 15/15.
  - WPR needs an elevated prompt from the user.
  - Tracy needs a code change plus a ~21 min rebuild; it is only a proposal.
- **S2:** Agent 2 cuts at ~22:40 from Agent 10's list, then builds devoff2 and native2 (~22:40-23:10).

**23:09 (orchestrator): result of timing matrix 1, baseline-bin vs devoff1-bin, both at defaults**
- Run from 22:32 to 23:02 in `build/agent8/matrix/20261121-2232` (`summary.md`, `results.csv`). There were 12 runs: 11 OK and 10 scored. The preflight was clean: interactive desktop, AC power, 10.85 GB free, no builds. The user ended dllhost 33552 just before the start.

  | arm | valid | median ms | p99 ms | p99.9 ms | >33 ms/min | fps | CPU cores |
  |---|---|---|---|---|---|---|---|
  | base | 5/5 | 16.66 (16.66-16.67) | 18.59 | 20.75 | 0 | 60 | 2.12 |
  | devoff1 (r0) | 4/5 | 16.67 (16.66-16.67) | 19.51 (+4.9 %) | 23.38 | 0.2 | 60 | 2.20 |

- **No measurable difference: both builds are locked at 60 fps on the title/attract loop.** The p99 and CPU deltas are within run-to-run spread. Base p99 ranged 18.07-22.5 per run and devoff1 19.44-23.95; CPU ranged 1.91-2.29 and 2.00-2.42 cores, with both drifting down over time.
- **The cap is guest pacing, not host vsync.** The SDK's `vsync` cvar already defaults to false (`graphics/command_processor.cpp:55`), so the game paces itself to the emulated 60 Hz vblank. Median fps can't show CPU-side gains on this scene. The next matrix needs a headroom metric, such as per-frame busy time of the guest main/render threads or per-thread CPU, or a heavier scene. Agent 8 and Agent 3 will propose one and verify it in functional runs first.
- **The 6 s first-frame question is answered: no regression.** Cold boot to first frame took 9.0 s for devoff1 and 10.0 s for base. The earlier 23.7 s was a first-run or hidden-desktop artifact. Warm boots took 6-10 s for both arms.
- **Run 8 (devoff1 rep 3) is marked PROBLEM** only because a `fakedimensions.exe` crash dump turned up in `CrashDumps` during the run. That dump comes from a test exe, not the game, which exited 0 after WM_CLOSE in 1.2 s. Agent 8 will trace the dump's origin and match dumps to the game PID.
- Quiet window 2 ended at 23:09. Next: S2 â devoff2, then native2 (Agent 2); Agent 8's slot (native boot, N1-N3, Agent 11's control, Agent 3's runs); Agent 9's tool rebuild, codegen and T8.

**23:15 (Agent 2): S2 applied**
- S2 was applied at 23:15:03 from Agent 10's `build/agent10/b3/S2-include.tsv` (`E1FF0497â¦`): 18 files copied, Agent 9's 20 codegen files held at S1, 0 unexpected. Verify PASS (`PATCHES-S2` b2554716â¦, `STATE-S2-2315` 48869f6bâ¦).
- The SDK rebuilt 8 edges in 23 s. ETAs: devoff2 staged ~23:25, native2 ~23:40.

**23:20 (orchestrator): timing window 3 booked for 00:15**
- The user will be at the desk from 00:15 to 00:30 and will start the window. It runs about 45 min hands-off and ends around 01:00-01:15.
- **Heavy work stops at 00:10:** all builds, compiles, codegen, replicas and game runs must be finished or paused by then and stay off until the window ends.
- **Agent 8 prepares the window.** By 23:55 it sends me a matrix proposal that fits within 45 min and uses the new headroom metric (verified in at least one functional run). Arms, highest priority first; Agent 8 drops from the bottom to fit, with at least 4 reps per arm:
  1. devoff2 at defaults, as the reference
  2. devoff2 + Agent 11's ON bundle
  3. native N0 (native2 if its first boot is clean by 00:00, otherwise native-bin), plus N1 if its row is clean
  4. baseline
  5. devoff2 + Agent 12's ON bundle
- **The user gets one double-click file with no arguments.** The runner will keep the display on for the length of the matrix (window 1 was lost to a lock screen).
- Agents 11 and 12 send Agent 8 their exact ON-bundle cvars by 23:45. Agent 11's control rerun and Agent 3's runs may move to after the window.

**23:23 (orchestrator): native-bin crashes at startup; devoff2 is staged**
- **native-bin's first boot crashed** (Agent 8, `build/agent8/runs/2315-native`):
  - What worked: the D3D12 device on the MX570, the swap chain, and all 4 shader archives.
  - The crash: an unhandled C++ exception `0xE06D7363` (KERNELBASE+0xC569A) on UI thread t86424, right after `Native write tracking: ...`, which is the last line of `HostDevice::Create`. The next code is `legodimensions_app.h:154-168`: the cvar query `native_settings_frontend`, then `NativeSettingsRuntime`, then `QueuedSettings`.
  - The in-game minidump failed (`0x800703E6`). WER then caught heap corruption `0xC0000374`, which is probably secondary. The run drew 0 frames and exited at 74 s. 2 WER dumps were kept.
  - `legodimensions_app.h` is identical in the baseline, S1 and the live tree (F2E868DE), so the throw is in a callee or in the tail of `Create`.
  - Agent 8 is decoding the exception type and `what()` from the WER dump. Agent 6 is doing static triage (callee diffs S1 vs baseline, settings default keys vs registered cvars), with no runs and no live edits.
  - N1-N3 are skipped on this exe. **Window 3 drops the native arms** unless a workaround that needs no rebuild boots cleanly by 00:00.
- **Matrix 1 detail (Agent 8):** devoff1 used more CPU than base in 5 of 5 paired rounds, a median of +0.09 cores (about 4 %). By the sign test that is suggestive (p = 0.03 one-sided) but not proven. So base moves up to priority 2 in window 3, and the per-thread metric should show which thread carries the extra load. The run 8 dump came from Agent 3's self-test `fakedimensions.exe` at 22:50:03 and is harmless.
- **devoff2 was staged at 23:18:53** (Agent 2) in `build/agent2/devoff2-bin`: exe 7F0B1C1Câ¦, MANIFEST B87DC2D2â¦, 49 PASS / 0 FAIL. The rexruntime.dll includes Agent 12's `audio_shutdown_detach_worker`.
- native2 is at step 22 of 23. Its configure and the 7-patch plume `--check` both passed. ETA ~23:35.
- **Window 3 arms now, by priority:** devoff2 (reference), base, devoff2 + Agent 11's bundle, devoff2 + Agent 12's bundle.

**23:25 (Agent 3): the 60 fps cap is `framerate_limit`, which corrects my 23:09 entry**
- On OFF builds, the cvar `framerate_limit` is the only cap. The cap is not guest pacing to vblank, as I wrote at 23:09. With `framerate_limit=0` the title scene runs uncapped, so fps measures throughput directly (`perf-notes/agent3-run-harness.md` Â§3.1).
  - nvidia-smi can log how busy the GPU is.
  - `resolution_scale=2` makes the scene heavier, but on the GPU only.
- **Window 3 metric:** if a functional run shows that uncapped fps on devoff2 and baseline-bin is stable, well above 60, not GPU-bound, and the scene doesn't change over the window, then all arms run with `framerate_limit=0`, with per-thread CPU as a secondary metric. Otherwise the cap stays and per-thread CPU is the main metric. Agent 8 decides in its 23:55 proposal.
- **Agent 3 owned up to the run 8 dump:** its light checks at 22:48-22:52 overlapped matrix runs 7-9, and its self-test wrote `fakedimensions.exe.48456.dmp`. The fix: `harness/guard.ps1` now makes `selftest.ps1` and `run-game.ps1` refuse to start while a game or an Agent 8 runner is running. Agent 3's two runs (~7 min) go into Agent 8's slot before 00:10.

**23:22 (Agent 2): native2 staged, batch 2 done**
- native2 is in `build/agent2/native2-bin` (NATIVE_GPU=ON, S2), staged at 23:22:38: exe 5D1B2DC6â¦, fingerprint b7cc74f980e016c3, map 1FFB7EA9â¦, MANIFEST D6E7F14Fâ¦, 72 PASS / 0 FAIL. Its rexruntime and rexgpu-xenos are the same as devoff2-bin's.
- Agent 2 has nothing running. S3 gets planned after window 3.

**23:33 (Agent 7): cause of the native crash found**
- The exception is `std::runtime_error: "Native setting is not registered: present_fsr_sharpness_reduction"`, thrown by `NativeSettingsRuntime`. The run toml sets `native_settings_frontend=true`. Every SDK build here has FidelityFX OFF, so `presenter.cpp` never registers `present_fsr_*`. This is an environment difference and not a sprint regression (`perf-notes/agent7-present.md`, "Native first boot crash").
- **Workaround:** `--native_settings_frontend=false`, since the command line beats the toml. The present then falls back to bilinear instead of FSR 1. Agent 8 boots native2-bin with this flag now. If the boot is clean by 00:00, native N0 joins window 3 at priority 4: devoff2 ref, base, devoff2+A11, native N0, then devoff2+A12.
- **Proper fix (S3, after window 3):** reconfigure the SDK with `-DREXGLUE_FIDELITYFX_SOURCE_DIR=.../rexglue-sdk/thirdparty/FidelityFX-SDK` and rebuild rexruntime.dll for native only. The OFF builds stay FFX OFF so they remain comparable with baseline-bin. Optionally, `NativeSettingsRuntime` should log and skip unregistered settings instead of throwing. Agents 7 and 2 will propose this.
- Agent 6's static triage is stood down.

**23:41: #23 proves a pause deadlock; Agent 6 confirms the native crash cause**
- **Agent 11 (#23 done):** the control re-run hung at the first pause (0/50), as intended. It used the old order with `guest_suspend_guard` OFF, on devoff1-bin, 23:21-23:23. Dump: `build/agent11/runs/20261121-232139-testg-control/`.
  - The cycle: the UI thread runs `SetGuestPaused` â `AudioSystem::Pause` â `pause_fence_.Wait()`. Meanwhile the Audio Worker sits in the game's audio callback, in `KeWaitForMultipleObjects`, waiting on objects that only the 20 just-suspended guest threads can signal.
  - No G, heap or log lock is in the cycle, so `guest_suspend_guard` can't fix it. #17's `pause_safe_order` breaks it. Halves 1 and 2 passed 50/50.
  - Both cvars default to false (`rex_app.cpp:71`, `xthread.cpp:44`). The pause runs from `OnLostFocus` when `pause_when_unfocused` is on (`rex_app.cpp:822-826`), and from the debug pause cycle.
  - S3 candidate: `pause_safe_order` default ON, if Agent 10 rates it SAFE. Agent 11 sends Agent 10 the rationale and the diff. B stays OFF.
- **Agent 6 confirmed the native crash cause from the dump** (`legodimensions.exe.93080.dmp`, file offset 0x1AAA270F).
  - The chain: `legodimensions_app.h:155-157` â `settings_revision.cpp:25` â `ReadRegistryValues` throws at `settings_registry.cpp:104`, and nothing catches it.
  - `present_fsr_*` is registered only under `REX_HAS_FIDELITYFX_SDK` (`presenter.cpp:43-78`).
  - The workaround flag skips every startup registry read and is the code default.
  - Smallest code fix: use `spec.default_value` when `GetFlagInfo(key)==nullptr`, and skip unregistered keys in `LoadNativePreferences`.
  - An FFX-ON SDK would make `present_effect='fsr'` live in the devoff builds too. So FFX ON is native-only and not for OFF timing.
  - Details: `perf-notes/agent6-crash-triage.md`.
  - S3 native fix: Agent 7 (with Agents 6 and 2) proposes as text by 00:10: (a) the code fix, (b) an FFX-ON rexruntime for native only, or both.
- **Directives at 23:42:**
  - Agent 8 boots native2-bin with `--native_settings_frontend=false`. Native N0 joins window 3 at priority 4 if the boot is clean by 00:00.
  - Agent 4's N1-N3 rows run only if they fit before 00:05, otherwise right after window 3.
  - No builds or tree edits before window 3 ends.

**23:48 (Agent 10): review 4 done (#15); `skip_lr` is UNSAFE for LEGO**
- Rows 17-21 are at the end of `perf-notes/agent10-codegen-review.md`. `flush_mode_elision`, the skip_lr LR-user rule, the test infra/fixture D and the inert-key removal are SAFE at the default (byte-identical) and SAFE when ON. Agent 9's T8 and off4 meet Agent 10's conditions.
- **`skip_lr` is UNSAFE for this game.** Host code reads `ctx.lr` as the caller, and `skip_lr` stops guest code from writing it:
  - The gpu_native `sub_83FC49E8` hook gates its pool-copy drain on `ctx.lr == 0x83F9B660`, so the drain could be skipped (an ordering race).
  - `XexGetProcedureAddress` picks the thunk module from `ctx.lr`, so export lookups could return 0.
  - The other 9 keys don't touch LR.
- Agent 9's install tree `build/agent9/install/batch` (23:28) was generated with skip_lr, so it must not be built.
  - Agent 9 drops skip_lr from `build/agent9/configs/batch.toml` and regenerates into a new tree, keeping the 23:28 tree for diffing. This happens before 00:05 if it fits at â¤2 threads, otherwise right after window 3.
  - Agent 10 confirms that the diff between the two trees is only LR writes.
  - Agent 2 re-syncs snapB from snap1 (S2) and applies the new tree after window 3.
- Still open for B: Agent 9's heavy-TU CPU follow-up (it moves after window 3 if the regen goes first) and a game gate on the native build (Agent 10 proposes what it checks).

**23:56 (Agent 12): #22 done; the default-ON flip is accepted for S3**
- Final replica, 1000 runs per case, at most 2 at a time:
  - NEW: 0 HUNG, 0 CRASHED, 0 terminations, 0 ForceDetach in 4000 runs.
  - OLD case h: 429 HUNG + 171 CRASHED in 1000 runs, all from terminating the worker while it held or waited for G.
- `-SyntaxOnly` passed in all 6 including TUs on the final `audio_system.cpp` C281FA86.
- These meet Agent 10's first condition (Â§8 of `agent10-batch2-review.md`).
- **I accept R1**, Agent 10's second condition. R1: a detached worker's guest code may still run during the Runtime teardown. That is the same straggler policy as TerminateTitle (kernel_state.cpp:1038-1040), and the alternative (OFF) can orphan G and hang.
- So `audio_shutdown_detach_worker` default ON (a one-line flip, :48) goes into S3. Agent 12 lands it after window 3, together with `pause_safe_order` if that is rated SAFE.
- **Reachability (Agent 10 Â§8):** `AudioSystem::Shutdown` runs only from `Runtime::Shutdown` (OnDestroy or setup failure). Window close is `std::_Exit` and Quit Game is TerminateProcess, so normal play reaches neither mode. The artifact wording is corrected to match.

**23:59: window-3 proposal reviewed from Agent 8's files; native2 boots with the flag**
- Files: `bench/agent8/RUN-WINDOW3.cmd` (23:33), `bench/agent8/run/matrix-window3.json` (23:44); functional runs in `build/agent8/matrix/verify3` and `verify3b`.
- The plan:
  - Arms: d0 = devoff2 ref, base, d11 = devoff2 + the A11 ON bundle (R3), n0 = native2 N0 with `native_settings_frontend=false native_fps_limit=0`. d12 is dropped.
  - Runs: 4 reps round-robin, plus one unscored cold run per bin. Each run has a 35 s warm-up from the first frame and a 50 s window.
  - Metric: uncapped fps (`framerate_limit=0`), with `drivers/thread-cpu.ps1` (per-thread CPU, headroom, NVML GPU).
  - Keep-awake is ON. The runner always passes `--audio_mute=true --pause_when_unfocused=false --native_settings_load=false --discord_rpc=false`.
- **Functional results (hidden desktop, not timing):**
  - **d0** (2344-d0-r1): 226.9 fps, median 3.72 ms, p99 13.0 ms, 2.73 cores. Main XThread 75% busy (max 87%), GPU Commands 71%, TimerQueue 33%, headroom 25%. GPU util mean 64% (p90 69), 1740 MHz steady, no throttling. So devoff2 is not GPU-bound.
  - **n0** (2346-n0-r1): native2 **boots and closes cleanly with the flag** (5067 frames, wm_close 1.3 s). 101.3 fps, median 9.20 ms, p99 30.3 ms, 1.96 cores. Top thread XThread5E50 at 78% (max 94.5%), Main 46%, TimerQueue 36%. GPU util 39%. A clang++ process (Agent 9's) was running at the time.
  - **base:** verify3's base run hit a runner error (proc.csv locked) and a short window, so it has no clean uncapped run yet. d11 hasn't been run.
- **Fixes requested (due 00:06):**
  - `RUN-WINDOW3.cmd` passes no `-Only`, so it would run all 5 arms. Add `-Only d0,base,d11,n0` and fix its stale comments.
  - One clean base run and one d11 run (check the timer log line and that fps is steady across the window).
  - A plan-only dry run of the final cmd, then a GO line.
  - Agent 3's 2 runs move to after window 3 unless they end by 00:08.
- Leads for after the window: `rex::thread::TimerQueue` is 33-36% busy in both builds (Agent 11). native2 runs at ~0.45x devoff2's uncapped fps, CPU-bound on one guest thread (Agents 4, 6, 7).

**00:02: S3 native-fix proposal (Agent 7); Agent 9's batch-nolr is ready**
- `perf-notes/agent7-s3-proposal.md`. Agent 7 recommends (b) in its minimal form: re-run cmake on the S3 SDK build dir with only `-DREXGLUE_FIDELITYFX_SOURCE_DIR=<tree>/rexglue-sdk/thirdparty/FidelityFX-SDK` (ENABLE stays OFF, nothing fetched, built or delay-loaded).
  - Only rexui (~39 TUs) and rexruntime.dll rebuild. That DLL goes into native3-bin after an import/export check; devoff3 keeps the OFF DLL.
  - (a) is Agent 6's `build/agent6/fix-a/fix-a.patch` (`settings_registry.cpp:103-104` + `settings_preferences.cpp:69-71`, optional hunk 3 at :200). It is a no-op on FFX builds.
  - For cross-build deltas against window 3, pin native3 runs with `--native_settings_frontend=false --present_effect=bilinear`.
- **My concern with (b), an ODR/layout risk:** `REX_HAS_FIDELITYFX_SDK` is a PRIVATE define of rexui (`src/ui/CMakeLists.txt:127`), but public headers change under it:
  - `include/rex/ui/presenter.h:215`: `GuestOutputPaintConfig::Effect` values and `FsrQualityMode`.
  - `d3d12/d3d12_presenter.h:135/151`: `kGuestOutputPaintRootSignatureCount` goes from 1 to 5.
  - `vulkan/presenter.h:233/249`.
  - Any member or array sized by these, in a class used outside rexui (other rexruntime libs, or the exe), would have a different layout in each TU. Asked Agent 7 for a list of the conditional members and their users outside rexui. Tentative S3 choice: (a), plus (b) only if that check is clean. Final decision after window 3, with Agent 2's build steps.
- **Agent 9:** regenerated without skip_lr into `batch-nolr`. Gate 0/0. Against the 23:28 tree it differs only in `ctx.lr` lines plus 7 moved extern declarations. The path and hashes went to Agents 10 and 2. `bench/agent9/QUIET` has been set since 00:00.

**00:09: quiet window 3 called from 00:10**
- Quiet check at 00:09: no compiler, build, codegen, game or profiler processes (apart from the protected pythons), free RAM 8.94 GB, no LogonUI.
- `bench/agent8/RUN-WINDOW3.cmd` passes `-Only d0,base,d11,n0 -NoPrompt`.
- Agent 8's plan-only run gives 19 runs (3 cold). By measured run times that is about 38 min; the estimator says 49 min.
- **verify3c** (00:03-00:07, functional only, hidden desktop):
  - base: 138.4 fps mean, median 3.83 ms, p99 41.0 ms, 148.8 frames >33 ms per minute, 2.11 cores.
  - d11: 141.7 fps, median 3.80 ms, p99 40.8 ms, 181 frames >33 ms per minute, 2.25 cores. Every d11 game.log must show the 1 ms timer line.
  - Compared with verify3b's d0 (226.9 fps, p99 13.0 ms, 6 frames >33 ms per minute), both runs had far more long frames, so mean fps is noisy. Median frame time (3.72-3.83 ms) and per-thread CPU are the steadier numbers. Agent 8 still owes the first-half vs second-half fps check.
- Broadcast QUIET WINDOW 3 to Agents 2-12. The user steps went out at 00:10. Start deadline 00:35 (start check at 00:36).

**00:04: the user needs to relaunch agy-grid after window 3 (agy-grid bugfixes)**
- Plan: window-3 results, then a pause at a clean point: no builds running, every agent writes its notes and sends one state line, and a checkpoint commit if window 3 shows no regression (the user may object).
- Then a restart prompt, in chat and in `perf-notes/RESTART-PROMPT-S3.md`. The S3 build and the B (codegen-option) build are the first steps after the restart.

**00:12: Agent 10 confirmed batch-nolr; pause_safe_order rated SAFE**
- (A) Agent 10's per-function lrdiff (`build/agent10/review/r5/lrdiff-report.txt`): against the 23:28 tree only the LR statements changed, and they equal off4's in all 165,023 functions (6 differ only by 7 hook externs moved by the 430-TU split). SHA256SUMS 24CE1493 matches all 872 files.
  - **B is built from `build/agent9/install/batch-nolr`.** The skip_lr tree `build/agent9/install/batch` must never be built. Agent 2 never created snapB, so nothing was built from it.
- (B) Game gate for B: last section of `agent10-codegen-review.md`. B runs against an S2 build with S1 codegen, along a route through the host code that reads ctx.lr: boot export lookups, the LR-gated slot-heap Grow, the pause-menu Options Back row, the cel-shading/dialogue/Adventure Time mid-asm hooks, and a level change (the sub_83FC49E8 relocation at lr=83F9B660).
  - Fails on a crash or hang, "not in any registered module", or pool-copy errors. Must match baseline on the relocation/caller log lines, pause rows, screenshots and audio. Needs menu input (Agent 3's harness or the user).
- (C) `pause_safe_order` default ON is SAFE (`agent10-batch2-review.md` Â§11). Agent 12 lands it after window 3, as the first S3 step.

**00:12: Agent 9 #8 done**
- Five codegen options, all default OFF. With every option off the output matches the pin (off4: 883/886 identical; the other 3 are codegen.d and 2 stamps).
- T8: 1515 tests per config, only the pre-existing failure. Fixture D run7 PASS. Proposed config S2.10 has 9 keys (no skip_lr).
- batch-nolr: 481.0 vs 490.0 MB (-1.83%), ctx refs -13.1%, 91,606 rlw sites lowered, 63,167 musttail, flush lines -22.3%, the same 165,023 functions.

**00:13: window 3 matrix started** (`build/agent8/matrix/20261122-0013`). Expected end ~00:51-01:02; end check at ~00:52.

**~00:20: Agent 11**
- Offers test G half 1 on the S3 build without an explicit `--pause_safe_order` (~3 min, one game), to prove the new default. Accepted, for after the restart: in Agent 8's slot right after the devoff3 boot.
- #27's live files were re-stamped at 00:06:15 (hashes unchanged), because Copy-Item had kept the 22:27 source timestamps. Agent 11's stage scripts now stamp the copy time on -Apply/-Revert.

**01:16: WINDOW 3 DONE** (`build/agent8/matrix/20261122-0013`, 00:13-01:16, 19/19 runs OK, 16 scored, uncapped title loop, desktop WinSta0\Default; noise band Â±1.7% = d0's run-to-run spread)

| arm | median ms (min..max) | p99 ms | fps | CPU cores | Î median | verdict |
|---|---|---|---|---|---|---|
| d0 = devoff2 (ref) | 7.07 (6.98..7.10) | 12.23 | 162.9 | 3.52 | | ref |
| base = baseline | 7.12 (7.10..7.16) | 12.35 | 160.8 | 3.50 | +0.8% | within noise |
| d11 = devoff2 + A11 R3 bundle | 7.14 (3.40..7.19) | 12.25 | 159.0 | 3.59 | +1.0% | within noise |
| n0 = native2 (flag, native_fps_limit=0) | 6.71 (6.55..6.87) | 11.34 | 143.2 | 2.45 | -5.1% (p99 -7.3%) | FASTER, outside noise |

- **devoff2 = baseline within noise**, at the same CPU (3.52 vs 3.50 cores). Matrix 1's +0.09 cores for devoff1 did not reappear. No regression, so the checkpoint commit goes ahead.
- **Agent 11's timer bundle (d11):** no gain on the title loop, +0.07 cores. Stays OFF.
- **native2:** median 5.1% lower and p99 7.3% lower, at ~1.07 fewer cores (-30% CPU). Its mean fps is lower (143 vs 163) because the standard path has a share of very short frames (its mean frame time is below its median).
- **Open: a 2x split.** cold-d0 (3.18 ms), cold-base (3.87 ms) and d11-r1 (3.40 ms) ran about twice as fast as the other 13 standard-path runs (~7.1 ms). The hidden-desktop checks also ran at ~3.7 ms. Both displays are 60 Hz (MX570 1920x1080, Iris Xe 2240x1400), so this is not refresh pacing. native2 stayed at 6.55-6.87 ms in every run, including the cold one. Agent 8 is analysing it from the existing data (clocks, thread busy, timing vs when the user was at the desk). The medians of run medians are robust to it, but absolute fps isn't reliable until it's explained.

**01:20: end of window 3; pause procedure for the agy-grid relaunch**
- Broadcast: no builds, no game runs, no new work. Every agent finishes its notes and sends one state line by 01:35 (done since 23:00, first step after the restart, anything running, live-tree files edited since the S2 cut). Then idle.
- Agent 2: live-vs-S2 file list for the checkpoint commit. Agent 8: `matrix_recheck.py --write`, a per-thread table and the 2x-split analysis, by 01:40.
- Sent the held replies:
  - Agent 11: yes to test G half 1 on devoff3 after the restart.
  - Agents 6, 7, 10: S3 = (a).
  - Agent 12: the flips land after the relaunch, after the commit.

**01:25: correction to the window-3 native result (Agent 4)**
- n0's "FASTER -5.1%" is not like-for-like. n0's frame times come from native-frames.csv, while d0's come from perf.csv (run.json `frames.source`).
- By frame count, native2 is **12% slower** (143 vs 163 fps), at 30% less CPU (2.45 vs 3.52 cores, about 21% less per frame).
- n0 is not GPU-bound (GPU 43-50%). Main XThread is 74-77% busy.
- The window-4 native comparison must use one frame source for every arm. Agent 8 is to fix the summary.
- Agent 4's `matrix-native-threaded.json` (native2, flag, uncapped, thread-cpu driver) is 21 runs, ~63 min. Trim it to â¤45 min for window 4.


**01:21-01:28: pause state lines** (all agents except Agent 8, which is due at 01:40)
- Every agent reports "running: none" and no live-tree edits since the S2 cut apart from #27. Each one has a RESUME block in its notes file. The full lines are in `perf-notes/agent1-pause-state-lines.md`.
- **Agent 2's live-vs-S2 check** (`build/agent2/snap1/PLAN-CHK-0122.txt`, 8E133F63): 23,843 files, 22 differ from S2, 0 new, 0 deleted. The 22 are #27's 2 files plus Agent 9's 20 codegen files (17 modified, 3 new), which S2 held at S1.
- **Plume:** HEAD `e0c8871` is the `prepare_plume.py` pin. The superproject records `ceaeeee`, which can't be fetched from the public repo. This predates the sprint. Never commit the plume pointer.
- **Agent 10 (Â§12):**
  - fix-a is SAFE. fix-a-commit is SAFE and recommended: it stops Save from overwriting FSR 1 values saved by an FFX build.
  - Resulting hashes: 8BA19C5F, 9CBE6DBF and 4EC71328. No SDK rebuild is needed.
  - With fix-a, non-FFX builds apply a saved native-settings.toml, so every S3 arm keeps `--native_settings_load=false`.
  - Agent 7's one-line alternative is NOT SAFE.
- **Order after the relaunch (decided 01:30): B first, on snap1 = S2.** That gives a clean A/B against devoff2-bin and is exactly Agent 10's gate baseline.
  - Meanwhile the S3 inputs land in the live tree: Agent 6's fix-a + fix-a-commit, Agent 12's two flips, Agent 10's ratings and TSV.
  - Then the S3 build (devoff3, native3) and Agent 11's default check.
  - Window 4's main comparison is B vs devoff2.

**01:27: checkpoint patch export** (`build/agent1/checkpoint-1122-0127/`, no repo changes)
- Contents: game.diff (176 KB), sdk.diff (225 KB), plume-dirty.diff, copies of the 24 untracked files, a README with the HEADs and restore steps, and SHA256SUMS.txt (3BAD4CC8).
- Both diffs pass `git apply --check --reverse`.
- A checkpoint commit needs a git identity, because user.name/email aren't set. I asked the user (01:20) whether to commit with an identity passed for these two commits only, or to skip it.

**01:29: restart prompt written:** `perf-notes/RESTART-PROMPT-S3.md`. Still to fill in: Agent 8's 2x-split analysis and the commit result.


**01:33: Agent 8's state line and window-3 analysis** (`perf-notes/agent8-window3.md` "Window 3: results"; `build/agent8/matrix/20261122-0013/recheck.md`)
- **State:** running none.
  - First step after the restart: Agent 4's N1-N3 functional run on native2-bin (`matrix-native-functional.json -Only n1,n2,n3`), then Agent 3's slot.
  - Edits since 23:15 are only in bench/agent8, its notes and build/agent8/scratch.
- **The 2x split is game state, not clocks.** Every run (n0 too) starts in a light title phase and switches to a heavy one 30-40 s after the first frame.
  - The clocks are the same in both phases (GPU P0 ~1732 MHz, 3.5 cores). The heavy phase costs 2x CPU per frame (GPU Commands 2.8â5.4 ms, main 1.3â3.0 ms) and 2.4x GPU per frame (1.4â3.4 ms).
  - cold-d0 and cold-base looked fast because their 30 s windows began ~13 s after the first frame.
  - d11-r1 alone stayed light for 300 s, and it is the only run without the 34 failed NtCreateFile `d:\INSTALL#_#.DAT` lines. It ran 00:25-00:30 (user at the desk), but d0-r1 and base-r1 at 00:18-00:25 didn't diverge. Open: user input vs a Toypad race.
  - Medians mislead for the bimodal standard-path builds: n0 vs d0 = -5.1% median but -12.1% mean fps.
- **Per-thread busy, % of one core** (main XThread / GPU Commands / TimerQueue / audio):
  - d0: 48.4 / 86.8 / 62.0 / 6.1
  - base: 48.2 / 87.2 / 62.5 / 6.0
  - d11 r2-r4: 49.4 / 86.4 / 61.7 / 6.0 (d11-r1: 38.2 / 82.1 / 60.4 / 6.7)
  - n0: 75.7 / none / 52.4 / 3.3
- **Window-4 driver (proposal):**
  - A 1 s sys.csv with GetLastInputInfo idle time and foreground-is-game, PDH % Processor Performance x Processor Frequency (effective MHz, P/E split), thermal % Passive Limit, and the power overlay and AC at start/end.
  - The runner flags light-state runs (INSTALL count, share < 4.5 ms) and starts every window â¥ 60 s after the first frame, cold runs too.

**01:40: PAUSED for the agy-grid relaunch**
- All 11 agents are idle ("running: none"). No builds, no game runs, no timers.
- **Git commit: not made.** No identity is configured, and the user didn't answer.
  - The checkpoint is the patch export `build/agent1/checkpoint-1122-0127/`.
  - The new Agent 1 asks the user once, and commits before any S3 GO if the answer is yes.
- **Restart prompt:** `perf-notes/RESTART-PROMPT-S3.md`; Â§A is the prompt.
- **Copied for the new session:**
  - `perf-notes/FINDINGS-AND-CHANGES.md` (the report)
  - `perf-notes/agent1-tracker-s2.md` (Agent 1's tracker)
  - `perf-notes/agent1-pause-state-lines.md` (the state lines)

**01:50: Checkpoint committed and pushed** (the user's request at 01:38; the author is in each repo's local git config, added by the user at 01:41)
- **SDK** `90e7ccd` on `perf/opt`: 51 files (+3652/-344), pushed with `git -C rexglue-sdk push mine perf/opt` to rishabh-mohan/rexglue-sdk (new branch).
- **Game** `a0bdaa7` on `perf/opt`: 52 files (+5336/-300), including the new SDK pointer, the user's `.gitmodules` change (fork url, branch perf/opt) and `__pycache__/` in `.gitignore`. Pushed with `git push -u mine perf/opt` to rishabh-mohan/DimensionsRecomp (new branch, tracks `mine/perf/opt`).
- Staged from explicit path lists (no `git add -A`), with guards: file counts, no plume/simde/pycache, staged SDK pointer = SDK HEAD, and remote heads = local heads after each push.
- **Left out:** `thirdparty/plume` (patches in `tools/gpu-aot/patches/`) and a local `thirdparty/simde` edit to `simde/x86/sse.h` (+9/-1, Windows Clang fix). The simde edit is backed up as `build/agent1/simde-dirty-1122.diff` (2A6DE738); asked the user whether to keep it as a patch.
- Live hashes unchanged (rex_app.cpp E1569868, audio_system.cpp C281FA86, draw.cpp 50AA3B1D, settings_registry.cpp A3733700, settings_preferences.cpp C78112AA). Only `.gitignore` changed on disk.
- **From now on:** Agent 1 commits at milestones (for example @@done), SDK first, then the game repo. RESTART-PROMPT-S3.md Â§A step 3, Â§B, Â§B.1, Â§G and Â§I are updated.


---

# Session 3 (after the agy-grid relaunch)

**01:56-02:00 (orchestrator): session 3 resumed**
- Read RESTART-PROMPT-S3.md (all), this log's last ~250 lines and FINDINGS-AND-CHANGES.md. The report is copied to Agent 1's artifact dir as findings-and-changes.md and kept updated there.
- **State check (light commands only), matches Â§B/Â§B.1:**
  - Game `perf/opt` @ `a0bdaa7`, status ` m rexglue-sdk` + ` M thirdparty/plume`. SDK `perf/opt` @ `90e7ccd`, status ` m thirdparty/simde`. Local `mine/perf/opt` refs = local HEADs. Nothing untracked.
  - No build, compiler, codegen or game processes. Only the protected pythons, with the same PIDs as session 2 (1912, 22084, 47720, 52964, 55340, 70536; python3.11 41488, 38284), so no reboot happened.
  - Present: `build/agent2/devoff2-bin`, `native2-bin`, `snap1`, `build/agent9/install/batch-nolr`, `build/baseline-bin`, `build/sdk/install`, `build/agent1/checkpoint-1122-0127`. Absent: `snapB`, `devoffB-bin` (expected). `bench/agent9/QUIET` is still set (Agent 9 deletes it). C: has 259.7 GB free.
  - The agy-grid board was reset (run 2): 0 tasks, 0 claims, subagent budget 79.
- **01:57: the user went to sleep and asked for ~8 h of autonomous work (back ~10:00).**
  - No questions to the user before then. The checkpoint question in the pasted prompt is moot: it was committed and pushed at 01:50 (Â§B.1). The simde patch question stays parked, and simde stays out of every commit.
  - Commits at milestones per Â§G (SDK first, then game; `mine` remotes only; explicit paths).
- **fix-a-commit touches `settings_registry.cpp` only** (`build/agent6/fix-a/new-commit/` holds just that file). So the S3 targets are `rexlego/src/settings_registry.cpp` A3733700â4EC71328 (fix-a + commit) and `rexlego/src/settings_preferences.cpp` C78112AAâ9CBE6DBF. Agents 6 and 10 confirm.
- **Plan for the night:** Â§E steps 1-6: B prep, build and game gate; the S3 inputs; the S3 build; Agent 8's functional slot queue. Window 4 is composed and dry-run tonight, and the user starts it after ~10:00. No builds or game runs from 08:30, so the user can start it as soon as they're back.
- **~02:00: the Â§F task blocks were re-issued to Agents 2-12 in one reply**, with one line to all asking for RESUMED + ETA. The new task numbers are recorded below once the board shows them.
- **Task numbers (session 3 board, run 2):** #1 Agent 2 (builds), #2 Agent 3 (harness), #3 Agent 4 (draw path), #4 Agent 5 (uploads), #5 Agent 6 (fix-a), #6 Agent 7 (present), #7 Agent 8 (runner, slot queue, window 4), #8 Agent 9 (codegen), #9 Agent 10 (reviews), #10 Agent 11 (kernel), #11 Agent 12 (I/O, audio, flips). Subagents granted: 8 of 79.

**02:03 (Agent 12): RESUMED.** Both -Check pristine: audio_system.cpp C281FA86, rex_app.cpp E1569868 (clean against SDK HEAD 90e7ccd). s3flip_syntax on the staged copy PASS (`build/agent12/s3flip/syntax-20261122-020253.txt`). ETA 3-5 min after GO.
- **02:04: GO to Agent 12** (both flips) and a conditional **GO to Agent 6** (fix-a + fix-a-commit, once its pre-check shows A3733700/C78112AA). Both go to the live tree only; B builds from snapB = snap1 (S2), so neither touches B. Milestone commit after Agent 10 confirms the live hashes: SDK first (rex_app.cpp, audio_system.cpp), then the game repo (the 2 settings files + SDK pointer).

**02:04 (Agent 10): RESUMED.** The live files are all in their before-S3 state (settings A3733700/C78112AA, rex_app E1569868, audio C281FA86, #27 0A314946/AB359E1D). The staged inputs match what Agent 10 rated: fix-a 8BA19C5F/9CBE6DBF, new-commit 4EC71328 (patches 71AEFF3D/50046A3F), safeorder 11DE333F (diff 56952876, Â§11), s3flip 4331A312 (diff BF399E59, line 48 only).
- ETAs: re-hash â¤5 min after Agent 6 reports; flip ratings â¤10 min after Agent 12's -Apply hashes; S3 TSV draft ~02:35, final â¤10 min after the last input lands.
- **Gate scope:** Agent 10's route was written for a native B, but devoffB is an OFF build, and `gpu_native/hooks_buffer.cpp` (the sub_83FC49E8 lr=83F9B660 drain, the pool copy) isn't compiled in OFF builds. Agent 10 sends an OFF-build pass list to Agents 1, 3 and 8 by ~02:45. The native-hook part waits for a native B build, which isn't on tonight's plan.

**02:05 (Agent 2): RESUMED.** Its RESUME block matches disk: the B tools are at their 23:47 hashes, the `*.pre-B` backups are intact, batch-nolr SHA256SUMS 24CE1493 (872 files, 430 TUs, config E60EAF1C), and snapB/devoffB-bin don't exist yet. B prep started 02:04: codegen-frozen2.exe is compiled (A0FFC2D7), and its tests plus the default-mode gen-check/snap-gate on snap1 are running.
- **Caught before any build:** `prep-b.py` and `run-b.ps1` still defaulted to `install/batch`, the UNSAFE skip_lr tree. Agent 2 is pointing both at batch-nolr, making them refuse `install/batch` outright, pinning 24CE1493/E60EAF1C, and staging to devoffB-bin.
- ETAs: step 1 ~02:35; B ~30 min after GO (prep 5, configure/gen-check/gate 3, build 15-20 at -j10, stage 1); S3 25-45 min after GO.
- **02:05: conditional GO for B** (step 2), once step 1 passes and both scripts refuse `install/batch` in a negative test. Agent 9 reviews the prep-b/run-b diff while B builds; Agent 2 aborts if Agent 9 objects.

**02:06 (Agent 11): RESUMED; step 1 done (02:05).** The opt-in `default` run is in `bench/agent11/testg_session.ps1`, and its self-test passed 24/24. devoff2 with `-Only default -CheckOnly` refuses (exit 2); a plain `-CheckOnly` still exits 0. A post-run check warns if cmdline.txt or the run's toml sets pause_safe_order. Report: `build/agent11/selftest/default-20261122-020455.txt`.
- Step 2: ~3 min in Agent 8's slot after the devoff3 boot (with a -CheckOnly pre-check), before 08:30.
- **TimerQueue lead:** by default the queue thread waits with disruptorplus `spin_wait` (yield / Sleep(0) / Sleep(1)). It only blocks when the env var `REX_TIMER_WAIT_BLOCKING` is set. Cause measured by ~04:00 with a â¤2-thread bench (no game), plus a staged OFF-cvar diff for Agent 10.
- 02:07: asked Agent 11 whether the existing env var is a zero-rebuild window-4 arm (devoff2 + `REX_TIMER_WAIT_BLOCKING`). A functional check in Agent 8's slot comes first.

**02:07 (Agent 7): RESUMED; first native-frames summary** (native_frames_summary.py on the 5 window-3 n0 dirs, 02:02; Agent 8 hadn't run it). gpu_native is unchanged (device.h 703939AA, device.cpp 3D01E631, fps_counter.h E05D6A55).
- The native title loop runs at 139-148 fps in the heavy phase (162 fps in the cold run).
- On native, perf.csv has one more row than native-frames.csv (the 0 row) and the same frame stats.
- All 5 runs presented bilinear (fsr_enabled=0, spatial_fsr_presented=0), rendering at 1920x1080 and outputting at 2240x1294. Frame latency 1; the gamma ramp is non-identity; swap_present_cpu ~1.0 ms/frame.
- **Correction to the native lead:** native draws and presents run on the guest render thread (F8000190), at ~4.9 ms/frame vs d0's render thread at ~4.6 ms. The cost grows on **Main XThread itself, 2.97 â 5.29 ms/frame** (d0 â n0). That extra ~2.3 ms/frame is the native cost to chase. Agent 7 owns the lead (with Agents 4, 5 and 6, analysis only).
- ETAs: step 1 write-up ~02:40; `bench/agent7/native3_boot_check.py` (frontend on, no throw, bilinear present), tested on n0 and on the 2315 crash dir, by ~03:15; the native3 check within ~10 min of Agent 8's native3 boot.

**02:04-02:08: S3 INPUTS LANDED in the live tree** (Agent 1 re-hashed all 4 at 02:08; the live diffs equal the staged diffs Agent 10 rated)
- **Agent 12 (#11 done):** `rexglue-sdk/src/ui/rex_app.cpp` E1569868 â **11DE333F** (pause_safe_order default ON; diff 56952876, -5/+7) and `rexglue-sdk/src/audio/audio_system.cpp` C281FA86 â **4331A312** (audio_shutdown_detach_worker default ON, line 48; diff BF399E59). No header changed, so only 2 TUs recompile. s3flip_syntax -Live PASS (`build/agent12/s3flip/syntax-20261122-020455.txt`), safeorder_syntax -Live PASS (`build/agent11/safeorder/syntax-20261122-020520.txt`), only known warnings. Undo: `bench\agent12\s3flip_stage.ps1 -Revert`, `bench\agent11\safeorder_stage.ps1 -Revert`.
- **Agent 6 (#5 done):** `rexlego/src/settings_registry.cpp` A3733700 â **4EC71328** (fix-a + fix-a-commit, from new-commit/) and `rexlego/src/settings_preferences.cpp` C78112AA â **9CBE6DBF** (from new/). Hash-guarded byte copies at 02:05:27, with the new `build/agent6/fix-a/apply_fix_a.ps1` (-Check/-Apply/-Revert). git diff HEAD shows exactly hunks 1-3. compile-one -SyntaxOnly (NATIVE_GPU=1) rc=0, 0 errors; registry keeps its 4 old getenv/sscanf warnings at lines 136/138/151/155.
- #27 unchanged (xam_ui.cpp 0A314946, xboxkrnl_hal.cpp AB359E1D).
- **Milestone commit:** prepared, and made on Agent 10's re-hash OK: SDK (the 2 files), then the game repo (the 2 settings files + SDK pointer).

**02:07 (Agent 9): RESUMED.** Tool 37B32713; batch-nolr re-hashed 872/872 against 24CE1493; config E60EAF1C; live config 7F775847 unchanged; QUIET deleted 02:02. Staging the recipe step-9 rollback trees at 2 threads (`install/rb1-nolocal`: drops the four *_as_local keys and cr_compare_so_zero; `install/rb2-nomusttail`), ready ~02:15. They're built only after a B failure and Agent 1's GO. Reviews Agent 2's prep-b/run-b diff (it must change batch/412/414 to batch-nolr/430/432). Optional 9-key T8 run ~02:20-02:45. Flagged 4 gaps in matrix-codegen-check.json to Agent 8.
- 02:09 pre-commit check (read-only): SDK diff is `audio_system.cpp` +1/-1 and `rex_app.cpp` +7/-5 (plus ` m thirdparty/simde`, left out). Game diff is `settings_registry.cpp` +5/-2 and `settings_preferences.cpp` +3/-1 (plus ` m rexglue-sdk` and ` M thirdparty/plume`). user.name is Rishabh Mohan in both repos; the `mine` remotes are the rishabh-mohan forks.

**02:08 (Agent 5): RESUMED, holding for native3.** Its 8 gpu_native files match S2; -PlanOnly exits 0 (6/6 arms skipped, no bin yet). It fixed its own matrix: settle_s 20 â 0, because run-timing counts settle from the first frame. Once staged: 19 runs â 60 min; u0-u2 Ã3 â 31 min. Q: add `native_fps_limit=0 framerate_limit=0` to all 6 arms (native default cap 240, device.cpp:75)? **Yes** (Â§G uncapped rule). The measurement windows must still start â¥ 60 s after the first frame, because of window 3's lightâheavy switch at 30-40 s.

**02:10 (Agent 3): RESUMED.** Guard clean at 02:02. Step 1 (2 baseline-bin runs) is ready on Agent 8's ping: ~8 min of slot, then ~10 min for Â§6.2 and @@done.
- **Keystrokes can't drive the game on the hidden desktop** (tested 02:08). The test window got WM_SETFOCUS but GetForegroundWindow() returned 0, and SDL3 only gives keyboard focus when GetForegroundWindow()==hwnd, so rex drops every key event.
- Plan instead: a user-mode virtual XInput pad. It's a proxy `xinput1_4.dll` placed only in Agent 3's run dir, built with the toolchain's clang-cl, fed by run-game.ps1 through shared memory, and used with `--input_backend=xinput` (no focus check). Toy Pad figures go through the game's own TCP listener on 9191. Harness and fake-game self-test by ~03:30, then one ~10 min dry run on devoff2-bin in Agent 8's slot. It runs blind (no screenshots); game state comes from the perf.csv scene counters, game.log and the pad LEDs.
- **Decision (02:11):** the virtual pad is OK as harness-only test tooling: user-mode only, no drivers or system-wide installs, never in a staged `build/agent2/*-bin` (the manifests must stay PASS), built at â¤2 threads, saves isolated in the run dir. **Generated virtual Toy Pad tags: not tonight.** The user never answered Agent 3's virtual-tag question, so the default is no, like "no private shader banks". Tonight's dry run and gate cover what's reachable without figures: boot (export lookups), the title screen and the front-end menus. The pause-menu and level-change steps wait for the user's answer in the morning: generated tags or a manual run at the desk.

**02:11 (Agent 4): RESUMED.** draw.cpp is still 50AA3B1D. Agent 8's slot ran N1-N3 on native2-bin at 02:05 (`build/agent8/matrix/s3-n123-0205`):
- **N1 passes the key lines:** threaded ON, `serial workers=0`, 19 worker lines, no new warnings at first look.
- **N2 never started:** free RAM was 5.77 GB, under the 6 GB limit, during Agent 2's B prep. It needs a re-queue.
- **N3 fails:** no `Native draw batches` line, and 44,968 new `Native GPU shader cache miss: hash=0x0` warnings (shader_archive.cpp:432). The full-draw-preparation path (opt-in) is broken; Agent 4 is diagnosing it read-only.
- ETAs: N1/N3 check and N3 diagnosis ~02:35; trimmed matrix to Agent 8 ~02:50 (th3 dropped unless N3 is fixed); @@done 3 ~10 min after N2's re-run is checked.
- 02:12: told Agent 8 to schedule around the B build. Game runs need â¥ 6 GB free RAM, so they run before ~02:35 or after B is staged (~03:05-03:10).

**02:15 (Agent 8): RESUMED; slot queue and window-4 plan.** devoff2 B87DC2D2, native2 D6E7F14F and baseline 5A684510 are present. N1+N3 done 02:10 (`build/agent8/matrix/s3-n123-0205`), N2 re-run done 02:12 (`s3-n2-0210`). Agent 3's 2 baseline runs 02:14-~02:22. No game runs during the B build (02:35-02:55).
- Runner work in the gap: Get-BuildProcs fix ~02:30, sys.csv driver ~02:45, light flags + the 60 s floor + self-tests ~03:05, `matrix-window4.json` + `RUN-WINDOW4.cmd` PlanOnly ~03:10.
- After devoffB is staged (~03:05-03:10): B boot ~03:12, B gate ~03:15-03:35 (Agent 3's harness, with Agents 9 and 10), a-prof/b-prof ~03:35-03:50, window-4 dry run on devoffB ~03:50-04:05. devoff3/native3 boots ~04:10-04:30, then Agent 11's default check. **GO line by ~04:30.**
- **All 11 agents RESUMED by 02:15.**
- 02:16: window-4 priorities sent to Agent 8 (â¤ 45 min, drop from the bottom): (1) B vs devoff2, â¥ 4 reps each plus cold runs; (2) devoff3 (S3 neutrality); (3) d0t = devoff2 + `REX_TIMER_WAIT_BLOCKING`, only if Agent 11's functional check passes. The native arms go to a later window (Agent 4's trimmed matrix, Agent 5's uploads).

**02:20 (Agent 10): #9 steps 1-2 done; all S3 inputs SAFE.**
- **fix-a re-hash MATCH:** settings_registry.cpp 4EC71328 (11,224 B), settings_preferences.cpp 9CBE6DBF (4,938 B), CRLF kept, git diff HEAD = hunks 1-3 only. SAFE (Â§12).
- **Audio flip SAFE (Â§8):** audio_system.cpp 4331A312 = the staged file, line 48 only.
- **pause_safe_order flip SAFE (Â§11):** rex_app.cpp 11DE333F = the rated staged file (diff 56952876). It stays SAFE together with audio ON.
- No toml or runner sets either cvar, so S3 runs both new defaults. Kill switches: `--audio_shutdown_detach_worker=false`, `--pause_safe_order=false`.
- **Live vs STATE-S2 (snap.py walk):** 28 changed, 0 new, 0 deleted: 26 build inputs (Agent 9's #15 Ã20, #27 Ã2, fix-a Ã2, the 2 flips) plus `.gitignore` and `.gitmodules`. The 48 native inputs are unchanged. The S3 TSV goes to Agent 2 ~02:30.

**02:21: milestone commit, S3 inputs** (`scratch/commit-s3-inputs.ps1` in Agent 1's artifact dir; guards: the 4 live hashes, HEADs, branches, clean index, user.name, exact staged path lists, staged SDK pointer = SDK HEAD, remote head = local head after each push)
- **SDK `c5fe668`** "S3 inputs: pause_safe_order and audio_shutdown_detach_worker default ON" (2 files). Pushed with `git -C rexglue-sdk push mine perf/opt` (90e7ccd..c5fe668).
- **Game `001336f`** "S3 inputs: native settings fix (a), SDK with the S3 default flips" (the 2 settings files + SDK pointer c5fe668). Pushed with `git push mine perf/opt` (a0bdaa7..001336f).
- Status afterwards is the same as at the checkpoint: SDK ` m thirdparty/simde`; game ` m rexglue-sdk` (simde only) and ` M thirdparty/plume`. No working-tree file changed.
- **S3's build inputs = git game `001336f` + SDK `c5fe668`**, plus the pre-sprint plume and simde edits, as in S1/S2.

**02:21 (Agent 2): BUILD B STARTED** via `b-chain.ps1` (verify S2 PASS â prep-b â run-b -j10). devoffB-bin ETA ~02:50; it aborts if Agent 9 objects to the diff.
- Step 1 all PASS: codegen-frozen2 tests 8/8. The default gen-check (886/886) and snap-gate (snap1-off, snap1-on) were re-run at 02:20 on the final tools.
- Diffs against `*.pre-B`: build-snap/stage-snap-bin are `.pre-B` plus exactly patch-b-tools' 7+12 edits (scripted check). gen-check/snap-gate/stop-snap change only the B options.
- Negative test: prep-b and run-b each refused `install\batch` in 4 path spellings (exit 1 and 3, nothing written). The controls pass the 24CE1493/E60EAF1C pins.
- A bug the controls found and Agent 2 fixed before GO: install-steps.txt is UTF-16, so prep-b never matched an END line.
- Diffs in `build/agent2/B-diffs/`: prep-b.nolr.diff 643F3B61, run-b.nolr.diff CC6EAD36, preB-tools.diff 0C97791F.

**02:23 (Agent 7): step 1 done; the native3 check script is ready early.** n0 (native2, frontend off) runs at 143.2 fps (median of 4 scored windows, 136.7-146.6, p99 11.3 ms, 0 frames > 33 ms). perf.csv vs native-frames.csv: one extra row (the 0 row), no gaps, FSR 0 on every row. The present is bilinear 1920x1080 â 2240x1294, vsync off, swap_present ~1.0 ms/frame.
- **CPU ms per frame, n0 vs d0 medians** (threads.csv): Main XThread 2.97 â 5.31 (+2.35; busy 48% â 76%); render thread 4.69 â 4.94 (+0.25); GPU Commands 5.34 â 0; total 21.3 â 17.0 (â20%).
- **Bottleneck:** native draws and presents run on the guest render thread. Neither thread is saturated, so the frame is most likely bound by the mainârender handoff, with Main the longer leg. Candidates for Main's +2.35 ms: write-tracking faults, CPU pool copies, and guest spin/sync that the PM4 path hid in GPU Commands. Details: `perf-notes/agent7-present.md` "Window 3 native summary (session 3)".
- **02:24: approved** one functional -Profile run of native2 (flag on, uncapped) in Agent 8's slot after 04:30, after the devoff3/native3 boots and Agent 11's check. It is compared against Agent 8's d0 profile (a-prof), never timed, and Agent 7 analyses it at â¤ 2 threads.

**02:23 periodic check:** B is building (10 clang++, cmake, ninja), free RAM 7.3 of 31.7 GB. Board: 9 open tasks; #5 and #11 closed.

**02:25 (Agent 9): B tooling OK.** prep-b.py C0067F18, run-b.ps1 0D159651 and b-chain.ps1 AD7C76D7 match recipe steps 3-5:
- They use `install\batch-nolr` only and refuse `install\batch` (Agent 9 saw the negative tests). Pins: SUMS 24CE1493 (872), config E60EAF1C, and the exact `[batch-nolr] END` tag. The UTF-16 read is right.
- 870/870 generated files are identical (codegen.d rewritten). `-GenBase batch-nolr\generated`, gate 432 PASS, output devoffB-bin.
- Build at 52/471 at 02:24.
- Rollback trees ready: 9.1 `install\rb1-nolocal` (SUMS A966CF18, 880 files, config AE9F8F96, 434 TUs, gate 436) and 9.2 `install\rb2-nomusttail` (8BDE8717, 870 files, FC034D49, 429 TUs, gate 431). Either needs prep-b/run-b re-pinned (VARIANT, SUMS_SHA, CFG_SHA, the 872 count, $nolr, $cgNote).

**02:30 (Agent 4): #3 DONE.** draw.cpp is still 50AA3B1D. N1 PASS. N2 and N3 pass every check except one new warning type, `Native GPU shader cache miss: hash=0x0` (N2 67,220 lines, N3 44,968). N3 correctly has no batches line; Â§S2.12's `serial workers=2` was wrong. The negative control shows the checker can fail. perf.csv matches native-frames.csv over the window on 7 runs (mean fps within 0.001%), so `frames=perf` is a valid single frame source for every arm.
- Trimmed matrix `bench/agent4/matrix-native-threaded.json` 1F8BC5DD: n0/th1/th2 Ã4 on native2-bin, frames=perf, window from 60 s after the first frame, 12 runs. About 37 min planned (40-41 expected). Sent to Agent 8 for a later window. th3 is dropped and th2 is provisional until the fix lands.
- Proposed fix (`perf-notes/agent4-draw-path.md` Â§S3.2): in `PrepareDrawGeometryLegacy`, add the recorder's failed-vertex-bind test to the early return at draw.cpp:1306-1307. The recorder already drops these draws at line 2713, so the draws that reach the GPU don't change. The fix removes the wasted preparation and about 760 warning lines/s.

**~02:35 (Agent 10): S3 TSV final.** `build/agent10/s3/S3-include.tsv` A1E7C83F: 28 INCLUDE / 0 EXCLUDE vs STATE-S2-2315, including `.gitignore` 600E2436 and `.gitmodules` C6E62916. The header records game 001336f + SDK c5fe668, plus plume e0c8871 (dirty) and simde 71fd833 (dirty).

**02:40 (Agent 2): devoffB-bin STAGED.** Chain 1,164 s (build 1,060 s); gen-check 870/870, gate 432 PASS, stage 0 FAIL.
- exe C3F8686Eâ¦ (153,588,736 B), map 44332E6Câ¦, rexruntime 1C45C869â¦ (= devoff2), MANIFEST 8709476Fâ¦. Agent 1 re-hashed the exe and rexruntime: both match.
- CompareBin vs devoff2: the exe differs, the map gives a NOTE, and the other 5 files are identical.

**02:41 (Agent 2): S3 cut into snap1** from Agent 10's TSV A1E7C83F: 28 COPY / 0 DELETE (488,374 B).
- PATCHES-S3.tsv 2DA2AB6C (28 rows) and STATE-S3-0241.tsv 4F791C2E both carry the 001336f/c5fe668 inputs note. Verify S3 PASS. Backup: `snap1-backup-S3`.
- stage-snap-bin now lists PATCHES-S1..S3 (diff 20531DD9).
- S3 keeps the pinned S1 generated code (gen-check vs baseline/). batch-nolr is used only in B.
- **devoff3 build started 02:42**, ETA ~02:52, then native3 ~03:00.
- Step 3 was marked "at GO", and Agent 2 started it on its own. Agent 1 approved it after the fact at 02:46: the inputs were committed and rated SAFE, and the TSV was final.

**02:41 (Agent 10): B-gate checklist for the OFF build** (last section of agent10-codegen-review.md):
- **Order:** a fresh devoff2 baseline with the same route, save, toml and harness flags, then devoffB. Both are functional runs in Agent 8's slot, done before 08:30. LEGO_NATIVE_MEMOPS_VALIDATE stays unset.
- **Fail criteria (route driven by Agent 3's vpad):** devoffB fails on any of:
  - a crash, hang or watchdog;
  - 0xC0000409, 0xC0000005 or 0xC00000FD;
  - any "not in any registered module";
  - more unimplemented lines than devoff2;
  - logdiff NEW/MORE keys the route doesn't explain;
  - a new kind of "crash guard:" line;
  - a logdiff FLAG.
- **Must match devoff2:** the boot markers, and the WM_CLOSE exit (exit 0 within ~1 s). Quit Game is judged against devoff2's run.
- **Still open:** the native-only checks (gpu_native drain, relocation, native pause rows, slot heap, cel shading) need a native B.
- **Fallback:** if the menus can't be driven, the result counts as "boot gate only", not a B pass.
- **Tool:** `build/agent10/bgate/logdiff.py --base â¦ --cand â¦`.
- The toy-pad step is skipped tonight: no generated tags without the user's OK.

**02:42 (Agent 7):** a-prof as specced (devoff2, no cvars) runs at the toml's framerate_limit=60, so it isn't like-for-like with the uncapped n-prof. Agent 7 asked Agent 8 to run a-prof and b-prof with framerate_limit=0, which keeps them symmetric for Agent 9. **Approved by Agent 1 at 02:46**; no extra d-prof arm is needed.

**02:44 (Agent 9): B static check PASS** (`build/agent9/mapcmp.py`, `build/agent9/logs/mapcmp-AB.txt`).
- devoffB and devoff2 have the same 164,786 sub_ functions and __imp__ aliases, and the same 27 hooked aliases.
- .text 159.3 â 142.6 MB (â10.5%).
- B's 19 compiler warnings are snap1's 19 (host code, none in a generated TU).
- Re-pinned prep-b/run-b copies for rb1-nolocal and rb2-nomusttail are in `build/agent9/repin/`. They are for use only after a gate FAIL and Agent 1's GO.

**02:46: Agent 4's Â§S3.2 draw fix APPROVED, in sequence** (new task to Agent 4):
1. Agent 4 prepares and validates the fix on scratch copies now (patch protocol, â¤ 2 threads).
2. Agent 10 rates it.
3. Agent 4 writes the live file only at Agent 1's GO, after native3 is staged.
4. Agent 2 patches snap1 (S3d) and builds `native3d-bin` (native only).
5. Agent 8 runs n0/n2/n3 functionally on it, checked with check_n_rows.py.

All of this finishes before 08:30. native3 stays pure S3, so it compares cleanly with native2. The fix gets committed (game repo, draw.cpp only) once it is verified.

**02:44 (Agent 2): devoff3-bin STAGED** (S3 OFF build 132 s, stage 0 FAIL): exe 2522D436â¦, map CE2836A0â¦, rexruntime D1D66AC3â¦, MANIFEST B9C5175Dâ¦. The MANIFEST lists patch rows for S1 (2), S2 (18) and S3 (28), plus the 3 S3 notes (001336f/c5fe668). The exe carries the new pause_safe_order text (rex_app.cpp 11DE333F via the install/share copy). **native3 build started 02:44**, ETA ~02:50. That puts S3 about 80 min ahead of plan, so at 02:47 Agent 8 was told to move the devoff3/native3 boots and Agent 11's default check ahead of the B gate, which waits for Agent 3's harness (~03:30).

**02:46 (Agent 2): native3-bin STAGED** (native configure + build 51.8 s, stage 27.6 s, MANIFEST 96 PASS / 0 FAIL): exe 7F7F8586â¦, map F96136D0â¦, rexruntime D1D66AC3â¦ (= devoff3), MANIFEST B50FE8D4â¦, fingerprint 8f849b69 (native2: b7cc74f9).
- The MANIFEST lists S1 2 + S2 18 + S3 28 patch rows, including settings_registry.cpp A3733700 â 4EC71328 and settings_preferences.cpp C78112AA â 9CBE6DBF (fix-a).
- The exe has the pause_safe_order text and the 3 LEGO_NATIVE_* strings.
- devoff3's MANIFEST: 73 PASS / 0 FAIL. rexgpu-xenos is EE0A661F in both S3 bins (relinked with the S3 SDK).
- **draw.cpp check:** snap1-off's compile_commands.json has 477 entries and 0 gpu_native files, so draw.cpp isn't in OFF builds and devoff3 stays valid after the S3d fix. snap1-on compiles it. Live draw.cpp still equals snap1 (50AA3B1D).
- Agent 1 re-hashed the exe, rexruntime and MANIFEST of native3, and the exe and rexruntime of devoff3: all match. No builds running, 9.0 GB RAM free, C: 254 GB free.
- Agent 2 is preparing the S3d/native3d tools without building and waits for Agent 1's GO.
- Task #12 (Agent 4's draw fix) was assigned at 02:48.

**02:53 periodic check:** no builds or games running, 9.0 GB RAM free. Board: 9 open tasks (#1-2, #4, #6-10, #12); Agents 6 and 12 have no open task. Everyone is active (edits in the last minute): Agent 8 is finishing run-matrix.ps1 before the early boot sequence (B, devoff3, native3, then Agent 11's default check); Agent 7 is writing prof_main_compare.py; Agent 11 is working on bench_timerq.cpp. Nothing is stalled.

**02:49 (Agent 11): devoff3 `-CheckOnly` pre-check.** devoff3 carries the pause_safe_order default-ON marker, so the `default` run will start. The pre-check stopped at "another game is running", which is expected while the slot is busy. The self-test with `-Devoff3` passed with 0 failures (`build/agent11/selftest/default-20261122-024914.txt`). Agent 11 runs it as one command (~3 min) on Agent 8's ping.
- **TimerQueue:** an OFF-by-default cvar fix, `timer_queue_precise_wait`, is staged but not applied (diff D07A2DC4). Stage check and clang syntax check PASS, no new diagnostics. Its stage bench is running. d0t (devoff2 + `REX_TIMER_WAIT_BLOCKING`) is still queued with Agent 8.
- 02:56, Agent 1: it stays staged. Applying it needs Agent 10's rating and Agent 1's GO, and it is an S4 candidate. There is no build for it tonight unless the ~04:00 cause report makes a strong case.

**02:58 (Agent 8): early boots.**
- **Done:** B boot PASS (`runs/0247-devoffB`: exit 0, 6,698 perf rows, no dialog or dump). devoff3 boot PASS (`runs/0254-devoff3`: clean close, no dialog or dump).
- **Queue:** native3 boot (no flag, frame metrics on) + Agent 7's check ~03:00; Agent 11's default run on devoff3 03:00-03:05; Agent 3's harness dry run 03:05-03:15 (if ready); B gate (devoff2 baseline, then devoffB, gate_logdiff, results to 10 and 9) 03:15-03:45; a-prof/b-prof uncapped 03:45-03:55; d0t pair 03:55-04:02; window-4 `-Quick` dry run 04:02-04:10; self-test re-run 04:10-04:20; **GO line ~04:25**; n-prof 04:30-04:35; native3d n0/n2/n3 once staged.
- **Runner:** the 60 s floor, sys.csv, the light-phase flag and the other flags are wired through run-timing and run-matrix. `-PlanOnly`: d0, B, d3 = 17 runs, ~39 min; adding d0t with `-Repeats 4` = 19 runs, ~44 min.
- **02:59, Agent 1 decides: window 4 = d0, B, d3** at 5 repeats + cold runs (17 runs, ~39 min planned). Window 3's runs overran the planner by up to ~16 s each, so expect ~43 min. d0t would plan at ~44 min (~49 real), over the â¤ 45 min promise, so it moves to a later window. Its functional pair still runs tonight. Agent 4 sends the native3d n0/n2/n3 spec when the build gets its GO.

**03:00 (Agent 8): native3 boot PASS** (`runs/0256-native3`, no native_settings_frontend flag, frame metrics on). Fix (a) works in a real build. Agent 7's native3_boot_check: A-D PASS with 2 WARNs that come from the run config, not defects: native_fps_limit_cvar=240 (the boot run used the default cap; the reference run used 0), so there is no "presentation cap override" line. Agent 11's default run on devoff3 is running, ending ~03:02. Next: Agent 3's harness dry run (~4 min, launched by Agent 8), then the runner self-test (fake exe, 2.5 min) while Agent 3 confirms the gate commands, then the B gate ~03:10-03:20. Agent 8 confirmed window 4 = `-Only d0,B,d3`, with d0t out; the d0t pair still runs tonight.
- Agent 5 can now point its uploads matrix at native3. Agent 4's matrix switches to native3 or native3d (task #12).

**03:02 (Agent 7): native3 (fix a) check PASSED; task #6 DONE.** `native3_boot_check.py` on `build/agent8/runs/0256-native3` vs `0030-n0-r1`: frontend on (from toml :72, settings graph bound, frontend transitions logged); no throw (482 lines, first present at L128, past the S2 throw point, exit 0, 13,642 rows, 0 gaps); bilinear present (spatial_fsr_presented=0, fsr_enabled=0 on every row; the toml's `fsr` is rejected by the non-FFX SDK); identity: exe 7F7F8586, rexruntime D1D66AC3, fingerprint 8f849b69, and both fix-a MANIFEST rows match. The 2 WARNs are config: the boot had no `--native_fps_limit=0 --framerate_limit=0` and its window was unfocused, so its 101 fps (vs n0's 143) is not a perf result.
- Tools: native3_boot_check.py (test 7/7), native_frames_summary.py (`--runner-window`), w3_thread_per_frame.py, native_frame_breakdown.py, and prof_main_compare.py (test 16/16 plus a smoke run on a real profile), ready for a-prof/b-prof/n-prof. Notes: perf-notes/agent7-present.md (RESUME, window-3 summary, native3 section).
- 03:03: new task to Agent 7 for the profile analysis. Agent 7 sends the a-prof vs b-prof table to Agent 9, who interprets B, and analyses n-prof vs a-prof itself: Main's +2.35 ms, top 3 S4 candidates.

**03:03 (Agent 2): task #1 DONE.**
- devoffB MANIFEST 74 PASS / 0 FAIL; devoff3 73/0; native3 96/0 (fingerprint 8f849b69). Patch rows: S1 2, S2 18, S3 28.
- **S3d prepped and tested, not run:**
  - prep-s3d.py runs 9 checks. It refuses when live == snap1, on a wrong hash and on bad arguments.
  - run-s3d.ps1 builds native only, has an 08:30 guard and runs `-CompareBin native3-bin`.
  - stage-snap-bin.ps1 gets an S3d tag and `-CompareWhy` (diff `build/agent2/S3d-diffs/stage-snap-bin.ps1.S3d.diff` 174C04CF).
  - stop-snap covers run-s3d, and s3d-tools-test passes.
  - CHK at 03:01: live == snap1 for all 23,843 files.
- S3d waits for Agent 1's explicit GO with Agent 4's draw.cpp sha256. RESUME block updated in perf-notes/agent2-baseline.md.
- Task #13 (Agent 7's profile analysis) was assigned at 03:03.
- 03:04: a new task to Agent 2 keeps build/agent2/** claimed for S3d (at GO), the B rollback standby (at GO) and the optional nativeB (decided ~04:15).

**03:05 (Agent 5): task #4 DONE.** `bench/agent5/matrix-native-uploads.json` (15BB7822â¦) now points all 6 arms at native3-bin, with native_fps_limit=0 framerate_limit=0 and no frontend flag. The frontend reads only LEGO_NATIVE_FPS_LIMIT, so the cvar alone uncaps the build; the native_fps_limit_cvar column of native-frames.csv confirms it. settle_s 50 + warmup_s 10, so every window starts 60 s after the first frame. Checks: native3 hashes match; the 3 batch-2 strings are in the exe; the MANIFEST lists Agent 5's 8 S2 files at their live hashes. `-PlanOnly` exits 0: **19 runs, ~66 min** (u0-u2 Ã3 ~35 min, s0-s2 ~13 min). It went to Agent 8 for a later window. No game or build was run.
- Caveat from Agent 5: with the 60 s floor, most first-use uploads land before the window, so u0/u1/u2 should come out close. The first-load hitches show up only in an unscored row-0 frame_summary check.
- Task #14 (Agent 2: S3d at GO, rollback standby, optional nativeB) was assigned at 03:04.
- 03:07, Agent 1: 66 min with an expected null result is a poor use of a user window. A follow-up task to Agent 5: a â¤ 45 min version, plus post-run load-phase scoring (first 60 s after the first frame) from its own script, with no runner changes.

**03:06 (Agent 3): B-prep done; the menu route runs without the user.**
- **Dry run** on devoff2-bin, 03:01-03:04 (`build\agent3\runs\20261122-030135-bgate-dry`): 37/37 steps, 0 timeouts. Exit 0 via WM_CLOSE in 0.93 s, exit sequence OK. 0 crash, "not in any registered module", crash guard or unimplemented lines. The game loaded the virtual pad from the run dir and polled it: 7,890 GetState calls, 136 with input.
- **Reachable** (from perf.csv draws/vertices):
  - boot with export lookups, then pre-title 218/222, then the title 226/1022 (~35 s after the first frame);
  - START at the title doesn't change the scene;
  - A goes to a front-end screen, 220/528 (Toy Pad LEDs lit, `INSTALL*.DAT` probes), and a second A gives 220/534;
  - later A/DOWN/UP/B presses are read but don't change the scene.
- **Not covered** (needs figures or the user): the level, pause â Options â Back, cutscene, level change, and Toy Pad figures/save/achievements/Quit.
- **Limits:** blind (no screenshots). The game holds perf.csv unshared, so the script uses fixed sleeps, and scenes are mapped afterwards by the new `harness/route-report.ps1`. The pad DLL is built to `build\agent3\vpad\` and copied only into run dirs; `run-game` refuses a bin dir that has its own `xinput1_4.dll`.
- **Gate started 03:05** in Agent 8's slot: `bgate-a` (devoff2), then `bgate-b` (devoffB), same route. Agent 3's `@@done 2` (section 7 + self-test re-run) ETA ~03:40.

**03:09 (Agent 11): S3 default check PASS.** Agent 8 ran `-Only default` on devoff3 at 02:59-03:01. VERDICT PASS, exit 0, 50/50 (suspended 50, resumed 50), error/critical 0, no dump, clean WM_CLOSE exit. Neither cmdline.txt nor the toml sets `--pause_safe_order`, so the build default picked the order. Session: `build/agent11/runs/testg-session-20261122-025913.txt`; notes: "S3 default check -> Result".
- **TimerQueue preview** (clean stage bench in a game-free gap, 03:04-03:05):

  | Mode | CPU (one core) | TickCount stale > 2 ms | Gap |
  |---|---|---|---|
  | Today's spin | 30.4% | 49.7% | |
  | Staged precise (cvar on) | 1.9% | 5.4% | p50 1.07 ms, p99 3.8 ms |
  | d11t: d11 + `REX_TIMER_WAIT_BLOCKING=1`, blocking at host_timer_resolution_ms=1, no rebuild | 1.4% | 4.7% | |

  With the cvar off it behaves like today. Correctness PASS in all 7 modes.
- Agent 11 leans toward no build tonight, because d11t needs no rebuild. The full cause report with d0f/d0t follows by ~04:00.
- 03:10, Agent 1: agreed, no build; the cvar stays S4. A timer arm could now save ~0.3 cores in game, so it may earn a window-4 slot after all. Agent 8 prepares two `-PlanOnly` variants: W4a = d0, B, d3 and W4b = W4a + the timer arm, â¤ 45 min real. Agent 1 picks ~04:10 after the functional pair and Agent 11's report; the default is W4a.
- Task #15 (Agent 5: a â¤ 45 min uploads matrix + load-phase scoring) was assigned at 03:07.

**03:11 (Agent 2): #14 accepted; base for the rollback and nativeB.** S3d is ready: about 3-4 min after Agent 1's GO with Agent 4's hash.
- **The S2 SDK install is gone.** snap1-sdk/install is now the S3 SDK (rexruntime D1D66AC3). No S2 SDK install was kept, and snap1-backup-S2/S3 hold only the 16/25 overwritten sources. A rebuild on snapB's S2 sources would therefore mix the S2 game with the S3 SDK and match neither devoff2 nor devoff3.
- **Agent 2's proposal:** build both on snap1's current tree (S3, or S3d once applied; identical for OFF, which compiles 0 gpu_native TUs), in a NEW copy `build/agent2/snapB3`, leaving snapB/snapB-off untouched.
  - **Rollback:** S3 + the rb1 or rb2 tree, OFF, compared with devoff3-bin, output devoffRB1-bin or devoffRB2-bin. Window 4 would then pair it with d3 instead of d0.
  - **nativeB:** S3(d) + batch-nolr, NATIVE ON, compared with native3d-bin (or native3-bin), output nativeB-bin.
  - Agent 9's repin copies get cloned to prep-rb1/run-rb1 (and rb2) with only dir/tag/compare/regex edits; the diffs go to Agent 9.
  - ETA after GO: rollback ~20 min, nativeB ~25 min (including a ~6 min fresh native configure).
- **03:12, Agent 1: base approved.** Prepare without building; the copy, configure and builds start only at Agent 1's GO. Agent 2 reports snapB3's expected disk use first; up to ~40 GB is fine with 254 GB free.

**03:14 (Agent 8): B gate pair finished at 03:10.** Both arms (bgate-a devoff2, bgate-b devoffB) exit 0, 37/37 steps, 0 errors. gate_logdiff passes, and Agent 10's logdiff exits 0 with nothing new. Agent 10 has one difference to judge: B logged an extra INSTALL probe batch at the end of the route. The gate covers boot, title and the front end only (no Toy Pad figures).
- Next: W4a and W4b `-PlanOnly` by ~03:30. W4b = 4 arms Ã 4 repeats with one shared cold run, via a new self-tested `-ColdShared` switch.
- **Q1:** Agent 5's u0-u2 are timing, so they stay for a user window after window 4. s0-s2 are diagnostics (4 runs, ~13 min, functional). Run them in the slot tonight? **Agent 1: yes**, after the window-4 dry run and before 08:30, once Agent 5 confirms the s-rows are final (it is reworking the matrix under #15).
- **Q2:** Agent 7 wants n-prof with focus=true, which the hidden desktop can't give because it isn't the input desktop. So every slot profile runs with focus=false, a-prof and b-prof included. **Agent 1:** n-prof runs unfocused tonight like a-prof and b-prof, so the three compare with each other. If Agent 7 finds focus changes the main/render picture, a focused a-prof/n-prof pair (~5 min, profiles only, never timed) goes into a later user window.

**03:15 (Agent 3): one divergence in the B gate.** bgate-a and bgate-b both pass the fail list (exit 0, exit sequence in order, 37/37, 0 fail lines, logdiff NEW 0 / MORE 0 / flags 0). But at the last mark, **devoffB left the menu screen on its own 59 s after it appeared** (a fade, a front-end load, then 218/222), while both devoff2 runs stayed on that screen. The route doesn't explain it.
- Possibly benign: an idle timeout back to the attract screen, hit by B because its scenes ran at different times relative to the fixed-sleep inputs. It could also be a real behaviour change.
- Agent 10 proposes a 2-run tie-break (~8 min of slot, route `b-gate-menus-long.txt`).
- **03:16, Agent 1: GO** for the tie-break right after the runner self-test, before a-prof/b-prof. B's status, and so window 4's main comparison, depends on it. Agents 9 and 10 pick a rollback tree (rb1-nolocal or rb2-nomusttail) in case B diverges.

**03:16 (Agent 4): #12 step 1 done** on scratch copies only. Live draw.cpp is still 50AA3B1Dâ¦ (= HEAD 001336f).
- Patch `build/agent4/s32/draw-s32.patch` (F5434325â¦2387, +5/-0). After-hash **5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410**.
- Every check matches batch 2: v3/v2 compile exit 0 (77 warnings); only PrepareDrawGeometry changed in the object; fixtures 9/26 same set; state shadow OK 20/19; run_patched 3/3; static check OK.
- The guard sits at PrepareDrawGeometry's entry, not at Legacy:1306, so it also covers the planner's lookup at 1533.
- Sent to Agent 10 for a rating. Step 2 takes ~5 min after GO (apply_live.ps1 passed a dry run).
- **Option offered:** draws with vertex-shader address 0 aren't covered; the fix for those would be `|| !vs` (~15 min more checks). **Agent 1 (03:17): not now.** A second native3d build costs only ~3-4 min, and vs=0 draws would need their own proof that the recorder drops them too. Agent 4 prepares it only if native3d's n2/n3 still log hash=0.

**03:22 (Agent 9): B's menu exit fits an idle timer counted in frames, not a codegen change** (`build/agent9/logs/gate-scene-AB.txt`, from perf.csv, where 1 row = 1 frame).
- devoffB went 220/534 -> 220/540 (1 s) -> 218/222. That transition is the one extra INSTALL probe pass: 34 lines, the whole 102 -> 136 logdiff.
- B left about 1,170-1,235 frames after its last pad input (L44 `B`). devoff2 stopped at <= 1,165 idle frames, because its last 20 s ran at 38.8 fps (780 frames) against B's 58.9 fps (887 frames).
- Real-time timers don't fit: devoff2 idled >= 25 s against B's ~20 s, and sat on 220/534 for 65.8 s against B's 59.2 s.
- **Prediction for the tie-break:** with a longer idle tail, both builds leave about 1,200 frames after the last input.
- **If B leaves and devoff2 still stays past ~1,300 idle frames:** build rb1-nolocal. Only the Stage A keys plus cr_compare_so_zero can change guest control flow (the known case is sub_83E5C88C, the one mtxer context restore, whose CR/XER/CTR die as locals). rb2 (musttail) only changes host stack depth, so it can't move a timer. rlwinm, flush and vmx are proven.
- **03:24, Agent 1:** checked `harness/routes/b-gate-menus-long.txt` (Agent 3, 03:14, 65 lines). Steps 1-36 match `b-gate-menus.txt`; the tail idles 90 s after the last input (marks idle-10 ... idle-90). That is >= 45 s and >= 3,400 frames even at devoff2's 38.8 fps, so it tests Agent 9's prediction. Decision rule for the verdict (Agent 10, with Agent 9's idle-frame counts):
  - both builds leave at ~1,200 (+/- 100) idle frames -> B passes the front-end gate and stays in window 4;
  - B leaves and devoff2 stays past ~1,300 idle frames -> rb1-nolocal in snapB3, at Agent 1's GO after Agent 2's disk estimate and Agent 9's diff review.

**03:23 (cron check 3).** A game is running in Agent 8's slot (pid 5416, started 03:21:52; the runner self-test or the tie-break). No build is running. Free RAM 7.6 GB, C: 251.7 GB free. Open: #2 A3 (@@done ETA ~03:40), #7 A8, #8 A9, #9 A10, #10 A11, #12 A4 (step 1 done, waiting on Agent 10's rating), #13 A7, #14 A2, #15 A5. No stalls.

**03:25 (Agent 3 / Agent 8): tie-break pair done** (03:17-03:25, functional only). Runs `build/agent3/runs/20261122-031756-bgate-long-devoff2` and `build/agent3/runs/20261122-032150-bgate-long-devoffB`; route `b-gate-menus-long.txt` (1F3559C8â¦); pad DLL 309DF316â¦ in both.
- Both clean: exit 0 via WM_CLOSE, exit sequence in order, 54/54 steps, 0 timeouts, 0 fail lines, no WER or dumps. logdiff devoff2 -> devoffB: NEW 0 / MORE 0 / flags 0 (142 warnings each; GONE = 4 Toypad challenge keys).
- **Both builds leave the 220/534 screen on their own**, the same way bgate-b did (220/540 fade for 60 frames, then 218/222, plus the 4th INSTALL batch): devoff2 after 58.0 s on the screen, devoffB after 62.4 s.
- After 218/222 both play the same no-input 3D attract sequence, with the same scene signatures in the same order (up to 12.6k draws and 1.7M vertices per frame). So the gate also covered 3D rendering, streaming and animation.

**03:27 (Agent 3): #2 done.** Notes 6.2 has both baseline-bin runs (GpuLog exit 0, median 16.67 ms; the profile ran 0.9 rounds/s because it overlapped a build).
- New: the virtual XInput pad (`harness/vpad`: xinput1_4.c, build-vpad.ps1, vpadhost.cs; the DLL lives only in build\agent3\vpad and run dirs), `run-game.ps1 -InputScript`, `harness/route-report.ps1`, routes b-gate-menus.txt (CF803C22â¦), b-gate-menus-long.txt (1F3559C8â¦) and selftest-input.txt.
- Self-test 23/23 at 03:16. It needs one ~80 s re-run after the 03:20 change. Window 4 doesn't depend on it: Agent 8's runner has its own copy of the helpers.
- Follow-up idea (7.3): the attract sequence is a heavy 3D scene that needs no figures, a possible benchmark scene.

**03:29 (Agent 9): correction, the ~1,200-frame model is wrong.** Idle frames from the last pad input to the first 220/540 frame (`build/agent9/idle_frames.py`, Â±2 frames):
- Long pair: devoff2 1,122 frames = 18.88 s of frame time (59.4 fps); devoffB 883 frames = 18.87 s (46.8 fps).
- First pair: devoffB 1,199 frames = 20.35 s; devoff2 no exit after 1,119 frames = 26.38 s; bgate-dry (devoff2) no exit after 1,572 frames = 26.46 s.
- The long pair matches in time, not frames, and no measure separates the 3 exits from the 2 no-exits (frames, frame time, interrupt_dispatches 26.9k-31.1k vs 36.4k-40.6k). devoff2 has the same auto-exit (1 of 3 runs with the same inputs), so the INSTALL 102 -> 136 key is the route's idle exit, not B.

**03:31, Agent 1: B passes the front-end gate and stays in window 4.** The divergence is an idle exit that happens run to run in both builds; the long pair is clean and its attract sequences match scene for scene. No rollback build: rb1/rb2 stay prepared and unbuilt. Agent 10's written verdict is still requested for the record. **Task #16 to Agent 3:** attract-scene benchmark prep for a later user window (functional only, plan to Agents 8 and 1 by ~06:00).

**03:31 (Agent 10): draw.cpp Â§S3.2 fix SAFE** (perf-notes/agent10-batch2-review.md Â§13). Patch `build/agent4/s32/draw-s32.patch` (F5434325â¦, +5/-0, one hunk) adds a new first statement in `PrepareDrawGeometry` (draw.cpp:1498). Live 50AA3B1Dâ¦ becomes 5EA1F3576DCC2F90â¦ (306,557 B, 5758 CRLF lines); no header or CMake change.
- The draws reaching the GPU don't change. It is the same failed-vertex-bind test, on the same captured snapshot, that `DispatchDraw` already drops on at 2707-2716, before any PSO, geometry or draw call.
- Every caller runs under a `ShaderBindingsScope`, so `BoundShaderAddress` only reads two arrays and never polls. No routing decision reads `geometry_ready` or `geometry_valid`. The serial, FSR3-ordered and long-probe paths never reach it. OFF builds don't compile draw.cpp.
- Expected in the native3d rows: the `hash=0x0` cache-miss lines drop sharply in n2/n3; n0 stays the same; draws/frame and the marks stay the same.

**03:33 (Agent 10): B verdict, front-end gate PASS with partial coverage. No rollback; B stays in window 4.** Static PASS 02:45, boot PASS 02:59, route PASS. In time, devoffB's idle exit matches devoff2's to 0.01 s (18.87 vs 18.88 s); the rollback case didn't happen. Not covered: level, pause/options, cutscene, level change, save/Quit, toy pad, and every native item (these need a native B). Write-up: "Route level" in perf-notes/agent10-codegen-review.md.

**03:34 (Agent 10): #9 done.** Fix-a live files re-hashed (registry 4EC71328â¦, prefs 9CBE6DBFâ¦, both = staged); Agent 12's two flips SAFE; S3 TSV A1E7C83Fâ¦ (28 INCLUDE); B gate as above; draw fix SAFE. Agent 11's timerq rating follows separately (low priority).

**03:33 (Agent 8): W4 `-PlanOnly`.** Both variants are 17 runs, ~39 min planned, ~43 min real.
- **W4a** = `bench\agent8\RUN-WINDOW4.cmd` (`-Only d0,B,d3`; one cold run per bin; d0 x5, B x5, d3 x4).
- **W4b** = `bench\agent8\RUN-WINDOW4B.cmd` (`-Only d0,B,d3,d0t -Repeats 4 -ColdShared`): one shared cold run on devoff2, then a 4x4 Latin square. d0t = devoff2 + `REX_TIMER_WAIT_BLOCKING=1` (Agent 11's pick). A shared cold run is sound: each run copies its bin into a fresh run dir. W4b with a cold run per bin would be 19 runs, ~44 min: too long.
- **Why window 3 took 63 min instead of 49:** the runner's WerFault check (a WMI query) cost ~1 s every 5th tick and sometimes blocked 35-61 s (24.6 min lost). Fixed 03:26: process list first (23 ms), WMI only if a WerFault exists, plus a catch-up, and a late start mark keeps the full 50 s window. Self-test 55/55 PASS.
- Slot: d0f/d0t pair 03:30-03:36 (-> Agent 11); W4a + W4b `-Quick` dry runs 03:37-03:51; Agent 3's self-test ~03:52; a-prof/b-prof ~03:55-04:05; GO line by 04:25 (~04:15 if Agent 1 picks at 04:10). Then n-prof, s0-s2, Agent 3's #16 attract runs and the native3d rows, all before 07:30.

**03:35, Agent 1: GOs.**
- **Agent 4: GO for #12 step 2**, the live write 50AA3B1Dâ¦ -> 5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410.
- **Agent 2: GO for S3d** as soon as Agent 4 posts the write: prep-s3d.py with that full hash, snap-patch plan/apply/verify S3d, run-s3d.ps1 (native only, compare with native3-bin), stage native3d-bin, post the hashes. It must finish before a-prof starts; Agent 8 holds the profiles until it does.
- **nativeB: conditional GO.** Base = snap1 at S3d, copied to `build/agent2/snapB3`, + `install/batch-nolr`, NATIVE ON, compared with native3d-bin -> nativeB-bin. It starts only when: native3d is staged; Agent 2 has posted snapB3's disk estimate and it is <= 40 GB; Agent 9 has OK'd the prep/run diffs; and Agent 8 says the last -Profile run is done. No build may overlap a -Profile run. Not started after 07:00.
  - Why build it: the native GPU path is limited by its main game thread (74-77% busy in window 3), where B's leaner guest code might help most. Agent 10's native items can only be checked on a native B.
  - Its gate: Agent 9's static check vs native3d, then the route pair native3d vs nativeB (b-gate-menus-long, ~10 min of slot, through Agent 3's harness), judged by Agent 10.
- Agent 8: n-prof moves up to right after a-prof/b-prof, so all three profiles finish before nativeB starts.
- **Task #17 to Agent 10:** the nativeB gate, the native3d rows with Agent 4, Agent 11's timerq rating (S4) and a first safety read of Agent 7's S4 candidates.

**03:37 (Agent 8): d0t functional result.** TimerQueue busy 39.1% -> 0.4% (pass), clean close, no dump. **But on the same scene d0t drew 37% fewer frames: 145 -> 91 fps in the window**, with ~40 s at 53-67 fps; frames over 100 ms 2 vs 1. Single hidden-desktop runs; full numbers to Agent 11. The W4a and W4b `-Quick` dry runs run 03:36-03:50.
- Config check (Agent 1): d0t = devoff2 + `framerate_limit=0` + `REX_TIMER_WAIT_BLOCKING=1` only, without `host_timer_resolution_ms=1` (`bench/agent8/run/matrix-s3-functional.json`). 53-67 fps is 15-19 ms per frame, close to the default 15.6 ms timer tick, so the blocking waits probably round up to the default resolution. Agent 11's bench numbers (1.4% CPU, 4.7% stale) are for d11t: blocking at `host_timer_resolution_ms=1`, with window 3's d11 cvars.
- Agent 11 picked d0t (notes L1529-1533) because it is d0 plus one env var, so window 4 would measure the TimerQueue change alone; d11t differs from d0 in 9 settings. Window 3 measured d11 vs d0 within noise (+1.0%, +0.07 cores).

**03:38 (Agent 5): #15 done.** `bench/agent5/matrix-native-uploads-45.json` (C59DB350â¦): u0/u1/u2 x5 + a cold u0, 16 runs on native3-bin with the 60 s floor; `-PlanOnly` ~41 min (`-Repeats 4`: 13 runs, ~33 min). The original matrix (15BB7822â¦) is unchanged and its s-rows are final; Agent 8 runs `-Only s0,s1,s2` tonight.
- `bench/agent5/load_phase.py` scores the first 60 s after the first frame (frames over 33/50/100 ms, hitch, max, p99, launch to first frame, first frame to the title switch, max frame around it, busy and cap flags), with per-arm medians and an exact permutation p against u0. Tested on window 3's n0 runs, the S3 rows and runs/0256-native3.
- Expected: the scored window ties for all three arms; u2 ties on every metric (no speed reason to turn the pool on by default); u1 separates from u0 only if the old paths add a large, consistent hitch. It needs an idle machine.

**03:39, Agent 1: timer re-check GO.** Agent 8 runs d0t, d11t, d0f (in that order, ~7-8 min, functional) at ~03:53, before a-prof; d11t = window 3's d11 cvars + `REX_TIMER_WAIT_BLOCKING=1`. Agent 11 may change the set by telling Agent 8 by 03:50. **Window-4 pick at ~04:15:** W4b with d11t in place of d0t only if d11t holds fps within noise of d0f on the same scene and cuts TimerQueue CPU; otherwise W4a (the default). d0t stays out of window 4 unless the re-check and Agent 11's report clear it. The profiles then end ~04:15 and nativeB starts after them.

**03:40 (Agent 5): correction for the user's list.** u2 ties with u0, and the 60 s scored window ties for all three arms. u1 (the old upload paths) could still show a bigger hitch in the first minute after launch; 5v5 detects that only if it is large and shows up in every run. That u1 check is what makes the window worth running. If u1 also ties, batch 1's upload changes don't matter in the title loop.

**03:46 (Agent 2): S3d done; native3d-bin staged.** Stage 0 FAIL (103 PASS, 34 NOTE). The exe `B90DF683D0A57A21â¦` differs from native3-bin (PASS) and the map 1C9AB7E3â¦ differs (NOTE). rexruntime D1D66AC3â¦, rexgpu-xenos EE0A661Fâ¦ and the other 4 files equal native3-bin's. MANIFEST `368F9CE650EC56CEâ¦` (rows S1 2 / S2 18 / S3 28 / S3d 1); fingerprint 335ff2d47268f3a1 (native3: 8f849b69907d4006).
- snap1 is now S3d: PATCHES-S3d 0250A3D0â¦, STATE-S3d-0342 AC7B88D3â¦, verify PASS. OFF builds don't compile draw.cpp, so devoff3-bin stays the OFF build of S3d.
- **nativeB disk estimate: ~3.5 GB** (snapB3 copy ~2.1 + snapB3-on ~1.0 + nativeB-bin ~0.36), at most 4.5 GB with margin, so the <= 40 GB condition holds. Clones made: prep-nb 0FAF4A92â¦, run-nb 979F4309â¦, rb-chain 3660069Eâ¦; stop-snap patched (C6B75748â¦, backup .pre-RB). Diffs to Agent 9; self-tests running. rb1/rb2 prepared and unbuilt. nativeB takes ~25 min and waits for Agent 9's OK and Agent 8's last -Profile run.
- **03:47, Agent 1 re-hash:** native3d-bin exe B90DF683D0A57A21â¦, MANIFEST 368F9CE650EC56CEâ¦, rexruntime D1D66AC3716835ACâ¦; snap1's draw.cpp = live = 5EA1F3576DCC2F90â¦. A game is running in Agent 8's slot (pid 78496, 03:47:34: the W4 dry runs).
- The draw.cpp milestone commit (game repo only) waits for the native3d n0/n2/n3 check (Agents 4 and 10).

**03:51 (Agent 9): nativeB/RB review OK, no objections** (nativeB condition 3). Re-hashed at 03:49: unchanged. make-rb-clones.py's outputs are byte-identical to Agent 9's independent dry run (`build/agent9/review/rb-dryrun`): the 5 clones, stop-snap.ps1 C6B75748â¦ + .pre-RB, and all 7 RB-diffs (run-nb.ps1.vs-run-b 48168743â¦).
- prep-nb `--check-only` passes on the real snap1 + install tree, and `--install install/batch` is refused (exit 1). run-nb.ps1 979F4309â¦ and rb-chain.ps1 3660069Eâ¦ parse with 0 errors and read correct (rb-chain read, not run).
- They use batch-nolr only, with the SUMS/config pins; check the prep-nb notes tag; pick Compare by tag (S3d -> native3d-bin); call build-snap `-Native -SnapDir snapB3 -GameDir snapB3-on -GenBase batch-nolr`; stage with `-CompareBin`. snapB3's S3 config = batch-nolr minus the 9-key block. The host code that touches ctx is unchanged (378/378 matches).
- Non-blocking nits: run-nb's own driver guard doesn't list prep-*.py (rb-chain covers it); an explicit -Compare isn't checked against the tag; the native fingerprint vs A is only logged (Agent 9 checks it in #17 item 1a).
- nativeB now waits only on Agent 8's last -Profile run. Details: S3.7 in perf-notes/agent9-codegen.md.

**03:53 (cron check 4).** A game is running in Agent 8's slot (pid 34576, 03:52:05: the timer re-check or the end of the W4 dry runs). No build is running. Open: #7 A8, #8 A9, #10 A11, #12 A4, #13 A7, #14 A2, #16 A3, #17 A10. Idle since their tasks closed: Agents 5, 6 and 12. No stalls.
- **Task #18 to Agent 6** (analysis only): the 1-5 s first-view frames in the attract sequence on the OFF builds (tie-break runs). What happens in those frames; whether the standard GPU path has a cross-launch shader/pipeline cache and whether our runs (fresh run dir per run) start it cold; whether a warm cache would remove the stalls; the smallest S4 change, if any; and what it means for Agent 3's attract warm-up. Summary by ~06:30.
- Agents 5 and 12 stay free until Agent 7's profile summary (~05:15) gives S4 candidates to scope.

**03:59 (Agent 8): timer re-check done** (03:49-03:57, `build\agent8\matrix\20261122-0349`). All exit 0, clean close, no dumps; every window starts 60 s after the first frame.

| Run | TimerQueue % (max) | Window fps | 53-67 fps band (frames; 1 s bins) |
|---|---|---|---|
| d0t (re-check) | 0.5 (2.6) | 78.0 | 3.3%; 32% |
| d11t (re-check, 1 ms timer line present) | 0.3 (1.7) | 62.0 | 1.7%; 20% |
| d0f (re-check) | 44.1 (61.3) | 52.2 | 1.6%; 24% |
| d0f (03:30 pair) | 39.1 | 145.2 | 2.3%; 2% |
| d0t (03:30 pair) | 0.4 | 90.9 | 4.4%; 14% |

- **TimerQueue CPU is cut** in all 3 timer runs: 39-44% -> 0.3-0.5%. Process CPU falls from 2.23-2.40 to 1.77-2.06 cores.
- **fps can't be judged on the hidden desktop.** d0f alone ranged from 52 to 145 fps tonight. Every run, d0f included, drops into a slow state at a different time (40-110 s after the first frame): 40-70 fps per 10 s on the same 226-draw scene, guest thread F80001A8 75-80% busy, E-cores mostly idle. Not thermal: P-cores ~1.9 GHz effective in every run, GPU 77-83 degC, no throttle samples. d11t sits inside d0f's range, and nothing points to a 60 fps lock specific to the timer arms. So the 03:37 "37% fewer frames" was this slow state, not the timer setting.
- **W4b** (`RUN-WINDOW4B.cmd`) is now `-Only d0,B,d3,d11t -Repeats 4 -ColdShared`: 17 runs (1 cold), ~39 min planned. Both `-Quick` dry runs passed: W4a 6/6, W4b 5/5 with exactly one shared cold run.
- **Power mode:** Windows has been on "best power efficiency" all night (scheme Balanced, on AC). The window-4 instructions don't mention it yet; sys.csv flags a change during a window.
- Profiles started 03:57:17 (no build running) and end ~04:10.

**04:01, Agent 1: window 4 = W4b (d0, B, d3, d11t; 4 repeats each, one shared cold run), unless Agent 11 objects by 04:10.**
- The rule is met: TimerQueue CPU is cut in game, and d11t's fps is inside d0f's tonight's range. The hidden desktop can't resolve fps either way, which is exactly what the user's window is for.
- Why W4b over W4a: d11t is a runtime setting (no rebuild) that cuts ~0.3-0.6 cores in tonight's runs. If B shows no gain, as batch 2 didn't, d11t may be window 4's only positive result. The cost is one repeat fewer for d0 and B (5 -> 4, Latin square).
- Window 3 measured d11 vs d0 within noise (+1.0%, +0.07 cores), so d11t vs d0 isolates the blocking wait on top of a known-neutral set.
- Power mode: asked Agent 8 whether window 3 ran in the same mode (clocks in window 3's logs). The user instruction will be to leave it unchanged, before and during the window, unless window 3 differed.

**04:02 (Agent 5): sys_csv added** to `bench/agent5/matrix-native-uploads-45.json` (one key plus one sentence in the QUIET MACHINE note; nothing else changed). New sha256 114A0242â¦6FBD02 (was C59DB350â¦). `-PlanOnly` unchanged: 16 runs, ~41 min, sys.csv on. Notes updated and Agent 8 told.

**04:01 (Agent 2): nativeB ready, not started.** Tools re-tested 48/48 PASS at 03:58. After Agent 9's OK, Agent 2 added an inert `-GuardOnly` switch to rb-chain.ps1 (now 65A2CFE4â¦) and sent Agent 9 the diff. Waiting only on Agent 8's "last -Profile run done". Won't start after 07:00; if the signal hasn't come by 06:40, Agent 2 reports and closes #14 without nativeB.
- **04:02, Agent 1:** the rb-chain change came after Agent 9's review, so nativeB also waits for Agent 9's ack of the 65A2CFE4 diff.

**04:04 (Agent 11): TimerQueue cause report; no objection to W4b with d11t.** d11t ran clean: exit 0, no dump, clean WM_CLOSE; its game.log matches d0f's plus "Host timer resolution set to 1 ms", 0 errors.
- **Cause:** the only TimerQueue user is the 1 ms repeating HighResolutionTimer that writes TickCount into KeTimeStampBundle (xboxkrnl_module.cpp:195-199). The default spin wait (timer_queue.cpp) starts every wait with 4092 `_mm_pause` (~0.4 ms on a P core, 0.24 ms on an E core), even when the deadline has already passed, then does 19 SwitchToThread and `sleep_for(1 ms)`, which takes ~15.4 ms at the default timer resolution. The missed ticks then fire back to back, each with its own busy phase: ~1000 busy phases per second.
- **Bench, no game** (CPU % of a core / share of time TickCount is > 2 ms stale): spin 30.4 / 49.7; blocking 0.3 / 84.5 (16 ms steps); blocking at 1 ms resolution 1.4 / 4.7; staged precise setting 1.9 / 5.4. Correctness passed in all 7 modes.
- **In game** (threads.csv, hidden desktop): spin d0/d0f 31.0-44.1% (max 61.3); blocking 0.3-0.5% in all 4 runs (d11t 0.3%, max 1.7); window 3's d0 on the interactive desktop 62.0%. Window cores: d0f 2.23, d11t 1.77.
- **The slow state:** E cores busy at ~550 MHz, P cores unchanged, an abrupt step, never in the foreground. Since 03:30 it hit 9 of 12 spin runs and 3 of 4 blocking runs, starting 27-100 s after the first frame; the runs without it were 45 s or shorter. `bench/agent11/timerq_slowstate.ps1` flags it. In seconds where both runs were in the fast state: d11t vs d0f +13.5% (0-30 s), d0t vs d0f +2.5% (0-50 s), 0347 d0t vs 0343 d0 -3.4%. Frames over 100 ms: d11t 2, d0f 8. No sign of a regression, and it isn't the 15.6 ms tick.
- Agent 8's 0336/0342 dry-run "SLOWER" verdicts for B and d3 are probably slow-state artifacts (it covered 25-50% of those runs' samples). Not results.
- **For window 4:** keep Agent 8's sys sampler on, and run `timerq_slowstate.ps1 -Since <W4 matrix>` before reading any fps. Window 3's d11 (157.5-160.3 fps vs d0 161.5-167.3) is the reference for d11's settings without the timer change.
- **S4:** `timer_queue_precise_wait` (OFF) is staged (build/agent11/timerq/stage, timerq.diff -6/+73); Agent 10's rating is pending. Optional idea: an OFF setting that opts the process out of EXECUTION_SPEED power throttling (`host_timer_throttling_optout` only sets IGNORE_TIMER_RESOLUTION, and d11t still hit the slow state).

**04:05 (Agent 11): #10 done.** `testg_session.ps1` has the opt-in `default` run (self-tests 24/24; the devoff3 default check PASS 50/50). TimerQueue cause found and the fix staged (stage checks 17/17, syntax PASS, stage bench 1.9% vs 30.4% CPU, correctness in 7 modes); live tree untouched. New read-only tools: `timerq_pair.ps1` and `timerq_slowstate.ps1`.

**04:06, Agent 1: window 4 = W4b is final** (`RUN-WINDOW4B.cmd`: d0, B, d3, d11t, 4 repeats each, one shared cold run). Agent 8 adds the slow-state scan to the window-4 read-out. **Task #19 to Agent 11:** stage the EXECUTION_SPEED throttling opt-out for S4 (OFF, scratch copies only, then Agent 10); a written proposal for applying the opt-out from Agent 8's runner to hidden-desktop functional runs (next session); and a user-facing summary of the timer finding.

**04:07 (Agent 9): rb-chain.ps1 65A2CFE4 (-GuardOnly) OK, no objection.** pre-GuardOnly = 3660069E (the reviewed version); Agent 9's own diff is byte-identical to RB-diffs/rb-chain.ps1.GuardOnly.diff (443CC9C0). +3/-1: a comment, `[switch]$GuardOnly`, and `if ($GuardOnly) {...; exit 0}` at line 41, after every step-0 guard and before `$log`, so it writes nothing. The nb command leaves it unset (no-op). rbt-logs 48 PASS / 0 FAIL. nativeB now waits only on Agent 8's last-profile signal.

**04:09 (Agent 8): profiles done.** a-prof/b-prof/n-prof ran 03:57:17-04:09:51 with no build running. Agent 7 analyses them (#13, ~05:15); most of a-prof/b-prof was in the slow state.

**04:11 (Agent 8): GO W4b.** `bench\agent8\RUN-WINDOW4B.cmd` (sha256 D89C0FC5â¦B7E16F, read by Agent 1 at 04:13) runs `run\run-matrix.ps1 -Matrix run\matrix-window4.json -Only d0,B,d3,d11t -Repeats 4 -ColdShared -NoPrompt`: 17 runs (1 shared cold run on devoff2, then a 4-round Latin square), ~39 min planned, 40-45 min real.
- Before: screensaver (None), charger plugged in, other programs closed, the power mode left as it is (best power efficiency, scheme Balanced) before and during the window, hands off.
- End screen: "Window 4b matrix finished (exit code N). Results: build\agent8\matrix\ (newest folder), summary.md", then "Press any key to continue . . .".
- Read-out: `python bench\agent8\run\matrix_recheck.py <dir> --write`, then `bench\agent11\timerq_slowstate.ps1 -Since <dir name>` before reading any fps. Every d11t game.log must have "Host timer resolution set to 1 ms".
- Dry runs: W4a -Quick 6/6 (0336); W4b -Quick 5/5 with exactly one shared cold run (0342). Runner self-test 55/55. The runner stall that cost window 3 24.6 min (the WerFault WMI check) was fixed at 03:26.
- Floor holds: the lightâheavy switch came at 30-33 s in 15/16 window-3 runs (d11-r1 was the light run) and at 31-35 s in all 13 runs tonight.
- Window 3 logged no clocks or power mode; tonight's fast fps is â¥ window 3's, so there's no sign window 3 ran in a faster mode.
- **04:15, Agent 1:** the artifact's "When you're back" now carries these steps, plus findings 6 (timer busy-wait) and 7 (slow state); copied to perf-notes/FINDINGS-AND-CHANGES.md.

**04:12 (Agent 2): nativeB started** at 04:12:09 (`rb-chain.ps1 -Variant nb -Jobs 10`), after Agent 9's ack (04:06-04:07) and the last profile ending (04:09:51). verify S3d PASS, the batch-nolr pins match (24CE1493 / E60EAF1C), snap1 copied to snapB3. ETA ~04:40; hashes go to Agents 1, 8, 9 and 10.

**04:13 (Agent 9): a/b profile answer (agent9 notes S3.8).** Agent 7's ab-main/ab-all weren't there at 04:13, so Agent 9 ran Agent 7's prof_main_compare.py itself on 0357-a-prof-r1 vs 0401-b-prof-r1 (build/agent9/prof/ab-{main,all,render,gpucmd}-a9.txt).
- **Verdict: B's -10.5% .text doesn't show measurably** in main- or GPU-thread time. The sampler got only 191/188 rounds in 150 s (~1.3/s, "CPU-saturated"; both runs in the 550 MHz state), so every delta is inside 2se.
- Guest-leaf ms/frame AâB: Main XThread 2.86â2.36 (-0.51, 2se 1.28); render XThread F80001A8/AC 13.39â12.79 (-0.60, 2se 2.86); all threads 20.43â19.15 (-1.28 = -6.3%, 2se 3.51). All down, none significant.
- GPU Commands is host code (0 guest; busy 8.44â9.42, noise), so B can't move it. fps flat (67.69â67.86); runner CPU 2.72â2.64 cores (-2.9%), the only hint of a saving.
- **Why fps can't move:** the render thread is ~94% busy in a GPU ring-buffer/fence wait spin (sub_83FBF7D0 â sub_83FAF180: cctpl + a ctr loop of db16cyc polling device+11024/11036 with a timeout; self 7.97â6.44 ms/f). Frames are bound by the host GPU Commands/CP path; faster guest code only spins faster. The 79 hot subs shrank 12.4% (mapcmp --subs-from).
- **S4 codegen ranking:** (1) Stage B/C non_argument+non_volatile_as_local, which drops the __savegprlr/__restgprlr calls (~2 ms/f of render-thread samples); (2) a spin policy for cctpl/db16cyc/bdnz loops (_mm_pause/yield: CPU, not fps); (3) skip_lr only after host changes, never for LEGO now; (4) flush-mode dataflow across labels; (5) PGO devirtualization of bctrl sites; (6) guest memory macro experiments; (7) [[unlikely]] on divide guards; (8) the redundant mfmsr/mtmsrd fence; (9) musttail for indirect tail calls.
- Non-codegen: the host TimerQueue busy-spins ~0.86 core in a steady_clock wait (slow-state run); fix the sampler rate before profiling effects under 10%; a real number needs window-4 timing.
- prep-nb PASS 04:13; Agent 9 watches the nativeB chain for item 1a.
- **04:21, Agent 1:** window-4 expectation added to the artifact (B: same fps likely, at most a small CPU saving; the GPU command thread is the main S4 lead). Agent 7 told to cross-check Agent 9's a/b files rather than redo them, and to keep its 05:15 summary.

**04:24, Agent 1 (cron 5):** nativeB build running (ninja + 10 clang++), free RAM 7.1 GB, C: 248.5 GB free. No game running; newest matrix 0357 (profiles, ended 04:09:51). Active on notes/tools: Agents 3, 6, 7, 8, 9, 10, 11. Idle: 5 and 12 (S4 scoping after Agent 7's ~05:15 summary). No stalls; nothing waits on a GO.

**04:30 (Agent 8): slot queue re-ordered.** Agent 3's attract pair was refused at 04:16 by the 6 GB free-RAM floor (5.4 GB free during the nativeB build); nothing ran. New order after the build, idle machine: s0-s2 ~04:41-04:54; native3d n0/n2/n3 ~04:55-05:03; the nativeB route pair (native3d vs nativeB, b-gate-menus-long, 420 s per arm) ~05:05-05:21 once nativeB is staged; Agent 3's attract pair ~05:22-05:42. All before 07:30. matrix_recheck.py now has a `slow` column (E-cores under 800 MHz for â¥3 rows; onset and share; matches Agent 11's scan) and `--drop-slow`. The 5-step window-4 read-out is in perf-notes/agent8-window3.md.
- Agent 1: order OK, no reply needed; the RAM floor worked as intended. The native3d rows (~05:03) still leave time for the draw.cpp milestone commit well before 08:30.

**04:33 (Agent 6): #18 done** (perf-notes/agent6-attract-stalls.md; build/agent6/attract-stalls/{analyze_stalls,attrib,residual,scan_runs}.py; functional data only).
- **Cause:** first-use pipeline creation on the GPU thread. With async_shader_compilation=true (default) a draw whose pipeline isn't built is dropped, but PipelineCache::EndSubmission waits for every queued pipeline at the next swap. Shader translation is serial behind one shared translator lock (pipeline_cache.cpp:3173-3237). Frames >250 ms on a miss row or the row after: devoff2 21 frames / 25.9 s (96%); devoffB 26 / 17.3 s (72%; the rest: 7 heavy-draw frames with no misses, 2.7 s, and 4 frames just before their misses, 2.2 s). Texture misses alone never made a frame slower than 185 ms.
- **Caches:** the Xenos shader storage (store_shaders, default on; <user_data_root>\cache\shaders\shareable\5752084B.xsh + .rtv.d3d12.xpso; cache_root overrides) is cold in every harness run (fresh user_data_root); the xpso holds 72 B per pipeline = each run's miss count. No D3D12 PSO library. The NVIDIA DXCache is shared and warm: coldâwarm halved the cost per miss (116 â 58 ms). The 35 s first boot in 1928-first was the cold driver cache. Players have a warm storage from their second launch.
- **Warm storage:** should remove the miss-linked stalls (devoff2 19 of 21 frames, 24.8 s; devoffB 15 of 26, 12.4 s) for an estimated +1-3 s of boot (unmeasured). Heavy shots, the load frame and the fence-wait frames remain.
- **S4: no code change.** A warm arm only needs the two seed files copied into <run>\user\cache\shaders\shareable before launch (the devoff2 tie-break run dir has a 214-pipeline seed). Agent 8's -SeedCache copies only native-pso*.bin, so the runner needs a new copy step (checks in Â§7). Follow-ups (none needed for S4): a diagnostic run with slow_frame_log_ms=50 (log lines only); per-thread DXBC translators (output-identical, could be ON once proven); a one-line fix at pipeline_cache.cpp:564 (original â needed count; warm boots only).
- Sent to Agent 3: the #16 window H0+5.5â¦+20.5 is compile-free even cold, but opens 0.14 s after the stall that ends at H0+5.36 (use a â¥250 ms flag or start at H0+6.5), and its last ~2.3 s are the heavy segment (end at H0+17.5 or score a sub-window).
- **04:38, Agent 1:** accepted; finding 8 added to the artifact. Window 3/4 are unaffected (scored from â¥60 s; window 3 p99 12 ms). Agent 6: send Â§7 to Agent 8 as a post-window-4 proposal (no runner change before window 4), plus an S4 item table and the diagnostic-run spec by ~06:30. Agent 3: optional warm-storage functional run on devoff3 after the attract pair, if it fits Agent 8's slot before 07:30; otherwise a next-session item.
- S4 candidate list so far: Agent 11 timer_queue_precise_wait (staged) and the EXECUTION_SPEED opt-out (#19); Agent 9's codegen ranking (04:13); Agent 6's per-thread DXBC translators and the :564 fix; Agent 4's `|| !vs` only if n2/n3 still log hash=0; Agent 7's top 3 (~05:15).

**04:34 (Agent 2): nativeB staged; #14 done.** `build/agent2/nativeB-bin` at 04:34:06 (rb-chain nb, 1316.9 s, exit 0). Stage checks 149 PASS / 0 FAIL / 34 NOTE. Against native3d-bin: exe differs (PASS), map differs (NOTE), the other 6 files identical. exe 01C4D5A3E36FAC50â¦, rexruntime D1D66AC3716835AC (= native3d), MANIFEST E5CBF30A6132B00Eâ¦. Fingerprint 81d1c3a71be3c096 (native3d 335ff2d4; 13 inputs differ from snap1: 12 batch-nolr generated files + legodimensions_config.toml). Disk 3.36 GB. rb1/rb2 prepared, not built. Tools 48/48, verify S3d PASS, gen-check 870/870, gate PASS. The machine is handed to Agent 8; the 06:40 timer is cancelled.
- **04:38, Agent 1:** re-hashed nativeB-bin: exe 01C4D5A3E36FAC50, map C9259B05689E3AA5, MANIFEST E5CBF30A6132B00E differ from native3d; rexruntime D1D66AC3716835AC, rexgpu-xenos EE0A661FB0C30FCB, amd_fidelityfx_dx12, TracyClient, font and wav = native3d. 0.34 GB. Matches Agent 2. Gate still to come: Agent 9's static check (1a), Agent 8's route pair (~05:05-05:21), Agent 10's verdict. Agent 2 stands by for a possible `|| !vs` native build (only if the native3d rows still show hash=0, only at GO) and writes a build inventory table by ~06:30.

**04:40 (Agent 7): #13 done** (perf-notes/agent7-present.md, Task #13; bin native2 + flag, n0 config; all 3 profiles in the slow state, so render shares carry over to timing and Main's ms carry over Ã1.1).
- (1) a vs b matches Agent 9. The only bucket outside 2se: write-tracking arm/protect +1.19 ms/f (2se 1.03), borderline.
- (2) Main n vs a: +2.40 ms/f (2se 1.57), all guest code. (i) The sub_82AFAB68 â â¦ â recursive sub_82F0CCD8/sub_82EF3180 scene walk, +1.99 (2se 0.99), over ~45 leaves with no hot spot: more work per frame in native, or the same work slower; a per-frame call-count probe of devoff2 vs native2 would tell. (ii) The frontend confound (on in a, off in n), untested. (iii) rexlego memset/memcpy hooks +0.44 (mostly inside i). (iv) UX_INPUT_STATE +0.22. Faults, arm/protect, pool copies and sync are 0 or lower. No off-switch fix for Main. Render now waits on Main 1.05 ms/f (P(render waits | main busy) 4% â 17%).
- (3) Render: the BindShader miss path is 49% of render CPU (6.10 of 12.36 ms/f; timing estimate ~2-2.5 ms/f). Placement VS 0xAC449538 and PS 0xAC448F28 are missing from the AOT index in every native2 run (n-prof and all 5 window-3 n0 runs). A miss caches nothing, so every SetShader repeats ReadableGuestSpan (2Ã QueryRegionInfo page scans under the heap lock) and FindShaderByMicrocode (the zero-prefix bucket walk), and the draws that bind them are dropped (draw.cpp:2712-2725): native draws less than devoff, which slightly flatters native.
- Top 3 S4 (native): #1 the shader fix (~2-2.5 ms/f render CPU, up to ~+15-25% fps until Main binds): capture with LEGO_DUMP_MISSING_SHADERS, then Agent 4 adds them to the AOT pack; stopgap LEGO_NATIVE_SHADER_MISS_CACHE=1 (a negative cache in AdoptShader keyed on a 64 KiB code stamp; output unchanged; proposal only, shaders.cpp is Agent 4's). #2 the Main walk (â¤2.35 ms/f, â¤~+30% fps, only with #1; probe first). #3 LEGO_NATIVE_THREADED=1 (~1-1.5 ms/f).
- Devoff GPU Commands leads: memcpy (VCRUNTIME140 fn_11200) from rexgpu-xenos 2.01/2.75 ms/f (likely shared-memory uploads; naming the caller needs the PDB); Presenter::RefreshGuestOutput 2.09/2.20 (NVIDIA UMD 1.32/1.49); a second VCRUNTIME copy fn_10E40 1.08/0.16; write-tracking re-arm 0.62/1.26.
- Tests: test_prof_main_compare 23/23, test_folded_tree_diff 8/8. The dropped draws were checked by code reading only.

**04:43 (Agent 3): warm-storage run, yes.** run-game.ps1 -SeedXenos copies the files (never links them) and refuses to overwrite; run.json seed_xenos records sha/size before, size after and game.log's storage lines. Tested: a dry run on devoff3-bin, 3 refusal cases and a unit test. Seed build\agent3\seed\devoff2-214 (read-only, same sha as the tie-break files). ~7 min asked from Agent 8 right after the attract pair (~05:42); otherwise a next-session item. attract-report.py fixed (window H0+6.5/11 s; â¥250 ms and heavy flags exclude; sub-window info only). Plan by 06:00.

**04:46, Agent 1: decisions on #13.**
- Dump run approved with two changes: native3d-bin, and LEGO_DUMP_MISSING_SHADERS=<run>\shader-dumps (absolute, never "1": DumpMissingShader uses the value as the dump root, shaders.cpp:355-372, so "1" writes relative to the game's working directory; the same variable also turns on the pool-copy XXH3 check, hooks_buffer.cpp:331-345). Agent 7 specs it to Agent 8 (~3 min, before 07:30); bin-dir MANIFEST check after; dumps to Agent 4.
- No LEGO_NATIVE_THREADED=1 run: the native3d n-row spec already includes it.
- New S4 analysis tasks (analysis only, â¤2 threads, notes only from 08:30, summaries ~07:00): Agent 5 = the rexgpu-xenos memcpy on GPU Commands; Agent 12 = write-tracking re-arm; Agent 7 = RefreshGuestOutput plus the dump-run spec. Agent 4, after the native3d rows, by ~06:30, scratch only: the relation to hash=0, the AOT-pack fix proposal, and the LEGO_NATIVE_SHADER_MISS_CACHE stopgap staged for Agent 10. No native build for it tonight.
- Artifact: finding 9 (missing native shaders), an S4 leads table, and a caveat on window 3's native CPU saving.

**04:46 (Agent 4): which draws sit behind the hash=0 lines** (agent4 notes Â§S3.2 "Which draws").
- The two missing placement shaders (VS 0xAC449538, PS 0xAC448F28) cause the failed-bind draws. No native build has ever drawn them. The batch-3 guard only stops them being planned, so some hash=0 lines may stay on native3d.
- They are probably title/menu draws: the first bind comes 4-5 s after the first frame, and the hash=0 rate rises 4.7Ã at the title switch.
- The PS's first 4 words are zero at bind, so a bind-time dump may capture zeros. Check the dumped words before packing anything.
- Whether the draws are visible is unknown; a native vs Xenos screenshot or decompiling would tell. Packing them is a visual change, so it needs a screenshot check.
- A negative cache needs Agent 7's code-stamp invalidation. BindShader holds LockRecording, so in th1-th3 the miss also stalls the recorder.
- shaders.cpp isn't Agent 4's file, so the stopgap is Agent 1's decision.

**04:47 (Agent 9): #8 done. Item 1a (nativeB static check) all PASS** (agent9 notes S3.9).
- **mapcmp:** 164,786 subs in both, the __imp__ aliases are equal, hooked 109 = 109. .text is -16,761,280 B (-10.38%), exactly the OFF devoff2âdevoffB delta.
- **Fingerprint:** 81d1c3a7 vs 335ff2d4 differs by design. fpcheck.py recomputes both (MATCH/MATCH). Of the 271 inputs, the 13 that differ are codegen + legodimensions_config.toml; the other 258 are equal.
- **Warnings:** 225 lines / 50 signatures, 0 in generated code. The 2 signatures not in the A/B logs are pre-existing (warncmp.py).
- **MANIFEST:** batch-nolr, rexglue 37b32713, no skip_lr, SHA256SUMS 24ce1493 (872 verified), 8/8 staged hashes match. rexruntime, rexgpu-xenos and Tracy equal native3d's.
- **Gate and host regs:** gate 432 TUs PASS; host regs on snapB3 are 378 / 0 new / 0 gone.
- **Write-tracking +1.19 ms/f** (Agent 7's borderline a/b bucket) is not codegen B:
  - rexruntime (1C45C869), rexgpu-xenos (77A5300B) and Tracy are byte-identical in devoff2-bin and devoffB-bin.
  - Protect/EnablePhysicalMemoryAccessCallbacks aren't in either exe map.
  - The guest caller sub_82B55588 (1040â848 B) makes the same 5 calls with the same guest memory ops (new fncmp.py).
  - So it's most likely run variation (14â30 samples, ~2se, slow state).

**04:50, Agent 1: directives.**
- nativeB static gate passed. What's left for it: Agent 8's route pair (~05:05-05:21) and Agent 10's verdict.
- New S4 analysis tasks. All analysis only, at most 2 threads, notes only from 08:30, summaries ~07:00:
  - Agent 5: the rexgpu-xenos memcpy on GPU Commands.
  - Agent 12: the write-tracking re-arm, on its absolute cost (Agent 9 showed the a/b bucket isn't B).
  - Agent 7: the dump-run spec to Agent 8, reading the native3d n-rows with Agent 4, and RefreshGuestOutput.
  - Agent 9: the render-thread GPU-wait spin (who writes the polled words; yield/hook proposals), plus the design of the per-frame call-count probe for the Main scene walk.
- Agent 4, after the rows, by ~06:30, scratch only:
  - the AOT-pack proposal, including the screenshot check;
  - the LEGO_NATIVE_SHADER_MISS_CACHE stopgap (OFF, code-stamp invalidation), staged for Agent 10.
  - My decision: S4 review only, no live apply and no build tonight. `|| !vs` stays as Agent 4's RESUME says.
- Agent 2's make-s3e-clones.py / prep-s3e.py are GO-gated prep for the `|| !vs` variant. No GO given.

**04:49 (Agent 11): #19 done** (scratch copies only).
- host_execution_throttling_optout (OFF) is staged in build/agent11/pthrottle/stage/ (-4/+37 lines, 3 files).
  - Together with the timer opt-out it makes one combined call (0x5), because each Set replaces the whole state. Windows 10 gets a 0x1-only retry. OFF behaves as today.
  - Tests: stage 35/35, syntax PASS, read-back 129/129.
  - Sent to Agent 10. -Apply only after SAFE plus GO (S4).
- Runner proposal (agent11-kernel.md "S4 staging (task #19)", part 2): apply a read-modify-write opt-out on the game handle right after the first-frame signal, verify it by read-back and record it in run.json. Off by default, set per arm.
  - The helper passed 6/6 on a PING.EXE child. No bench/agent8 edits.
  - Risk: the slow state may come from PL1 or window-visibility QoS rather than EcoQoS.
- Part 3 is the user-facing timer summary.

**04:50 (Agent 2): S3e/native3e tools ready, nothing built.**
- Hashes: prep-s3e.py 23536F1F, run-s3e.ps1 FD188929, stop-snap.ps1 705233E5. The diffs (build/agent2/S3e-diffs/) are with Agent 9.
- Dry run 8/9 PASS. The only FAIL is "live draw.cpp == snap1", because Agent 4 hasn't written yet.
- At GO with the sha, after Agent 9's OK: prep-s3e â snap-patch plan/apply/verify S3e â run-s3e.ps1 -Jobs 10 â native3e-bin vs native3d-bin. About 6-8 min, +0.4 GB.
- Inventory by 06:30. Its hashing and size walks wait for the end of Agent 8's window.

**04:51 (Agent 8): slot timeline.**
- native3d ~04:53-05:01, nativeB pair ~05:02-05:18, attract + warm ~05:19-05:50.
- A native3e build would go after 05:50, with its check ~06:00 (or attract is held for a 05:18-05:26 build). Default: after 05:50.
- hash=0 counts at ~05:02.

**04:53, Agent 1: replies.**
- **native3e: no GO yet.** It needs, in order: Agent 4's read of the native3d rows; step 1; Agent 10's SAFE; Agent 9's OK on the S3e diffs; then my GO with the sha. If it happens: after 05:50, never after 06:45. The attract job stays where it is.
- **Agent 11 follow-up:** the runner-side throttling test as a standalone wrapper or runner copy. No edits to bench/agent8, harness or any W4b file; W4b sha256s are checked before and after.
  - It is specced to Agent 8 as 3 alternating d0 pairs after the dump run, only if it ends by 07:15. Otherwise it becomes S4.
- **Agent 9's new task** starts with the review of the S3e diffs.
- **Agent 10 priorities:**
  1. the nativeB verdict;
  2. the native3d rows with Agent 4;
  3. `|| !vs` if it comes (time-bound);
  4. the S4 ratings (timerq, pthrottle, miss-cache stopgap).
- Artifact "as of 04:50" copied to perf-notes (69FDA5B5â¦, hash verified).

**04:54, Agent 1 (cron 6).**
- Tasks #20-#24 assigned: Agent 5 memcpy, Agent 12 write tracking, Agent 7 follow-ups, Agent 9 GPU-wait spin + probe design + S3e review, Agent 11 throttling pairs. Budget 18/79.
- Machine: Agent 8's native3d n-rows are running (legodimensions PID 81272 since 04:52:02, matrix 20261122-0452; s0-s2 = 0438). No build. Free RAM 6.3 GB, C: 247.4 GB free.
- Open: #7 A8, #12 A4, #16 A3, #17 A10, #20-#24. Idle: Agents 2 (standby for S3e, inventory by 06:30), 6 (S4 table + diagnostic spec by 06:30). No stalls.
- Nothing waits on a GO except a possible S3e, which waits for the rows.

**04:53 (Agent 10): nativeB 1a static PASS** (codegen-review "nativeB gate").
- statecmp + --full MATCH, sumscheck MATCH, lrsites PASS, hookset PASS (181 hooks, same set and objects). Agent 9's mapcmp/fpcheck PASS. warncmp CHECK (host-only). MANIFEST 149/0/34.
- The fingerprint only keys `<exe dir>/cache/native-pso-recipes.bin`, and the harness uses fresh run dirs, so both pair runs start cold. Run the pair as staged.
- 1b verdict within 20 min of the pair's logs.

**04:53 (Agent 10): first safety read of Agent 7's S4 top 3** (batch2-review Â§15, row 16).
- **1a, the AOT placement-shader fix:** not output-identical by design (the dropped draws come back). It needs a capture-stability proof, a changed n-row rule (draws per frame may rise) and the user's visual check.
- **1b, the miss cache:** output-identical only if it meets all of these:
  - the pack generation is in the key;
  - the full stamp span is covered;
  - readable_size is handled;
  - there is no per-frame fallback;
  - the shared warning cap is replayed.
  Otherwise it stays OFF, as a measurement switch only.
- **2, the probe:** must be compiled out by default.
- **3, THREADED:** covered by the n2/n3 rows, plus proof that the unlocked PlacementShaderUnchanged at shaders.cpp:622 runs only on the capture worker.
- All of them need a window-4-style timing A/B.

**05:00 (Agent 8): native3d passed** (matrix 20261122-0452, functional only).
- 0 hash=0 lines in n0, n2 and n3. check_n_rows: n2 PASS, n3 PASS. 3/3 runs OK, wm_close in 0.8-2.9 s.
- My grep agrees: the only "hash=0" substring matches are 2 start-up warnings per run, "shader not present in AOT cache, hash=0xA58EBA123EFB541C / 0x93B9F93B535E7CCA". Those are real hashes, not hash=0.
- The native3e trigger is not met.
- Slot: the nativeB pair has run since 04:59:37 (until ~05:15). Then attract + warm ~05:16-05:46, Agent 2's 1-min inventory, then Agent 7's shader dump.

**05:02, Agent 1: milestone commit, game repo only.**
- The SDK is unchanged; its only local change is the uncommitted thirdparty/simde edit, so there is no SDK commit.
- Commit `08933a7` "gpu_native: skip planning draws whose vertex shader failed to bind": draw.cpp +5 lines. The live sha 5EA1F357â¦ = snap1 S3d = native3d's input.
- Procedure: index checked clean before `git add`, explicit path, -m messages. Pushed to `mine perf/opt` (001336f..08933a7); ls-remote = HEAD.
- thirdparty/plume and simde stay out.
- S3e/native3e is not needed: Agent 2 stands down, Agent 9 skips the S3e review, and Agent 10's priority 3 drops.

**05:04 (Agent 10): native3d n-rows PASS** (task #17 item 2; batch2-review Â§13 "After the apply"; outputs in build/agent10/nb/).
- check_n_rows n2/n3 PASS, exit 0.
- hash=0x0 lines n0/n2/n3 = 0/0/0. native2 had 0/67,220/44,968.
- Every other warning type has the same count as on native2: n0 66 lines/18 types, n2 66/18, n3 58/16.
- Top draws per frame 8/0/1, and the same scene order (0â1â0â1â0â1â0â8) in all three.
- Threaded ON once; n2 logs "parallel workers=2", n3 has no batches line. Clean close.
- The placement-shader warnings (VS 0xAC449538, PS 0xAC448F28) are unchanged, as expected.
- No objection to the draw.cpp milestone commit, which was already made at 05:02 on Agent 8's report and my own check.

**05:05 (Agent 9): S3e clones reviewed, OK, no objections** (agent9 notes S4.0). Moot, since S3e is off; filed for S4.
- Hashes: make-s3e-clones A16E05AD, prep-s3e 23536F1F, run-s3e FD188929, stop-snap 705233E5 (.pre-S3e C6B75748). prep-s3d/run-s3d are unchanged.
- A scratch re-run reproduces all 7 outputs byte for byte. ASCII/LF/no BOM; 0 parse errors.
- The patch-row tags match stage-snap-bin.ps1:166-177 (the last row wins, so S3e replaces S3d's draw.cpp row).
- Dry run 8/9; it is 9/9 with the live hash faked in-process, and nothing is written.
- One cosmetic nit: a stop-snap comment says "04:5x".

**05:06 (Agent 2): ack.** The S3e tools stay unused and are kept for S4.
- 08933a7 changes only draw.cpp against 001336f (+5). Its blob = snap1's = the live file (5EA1F357).
- So native3d-bin = game 08933a7 + SDK c5fe668 + the pre-sprint plume/simde edits, and nativeB = that + batch-nolr.
- Inventory at Agent 8's all-clear (~05:50); it lands in agent2-baseline.md by 06:30.

**05:06 (Agent 6): S4 items and diagnostic-run spec** (agent6-attract-stalls.md Â§10 items table for Agent 10, Â§11 run spec; functional data only; no runs, builds or git writes).
- **(a) Per-thread DXBC translators:** output-identical. Files: pipeline_cache.cpp/.h. It replaces the global lock at :3185 with a per-shader claim and makes the flush flag atomic.
  - Kill switch `d3d12_parallel_queued_translation`: land it OFF, flip it after tests.
  - Only worth it if Â§11 arm B shows translation is â¥40% of the burst.
- **(b) The pipeline_cache.cpp:564 fix** (original â needed): one line, output-identical, and cold runs never reach it.
  - On warm boots every stored pipeline is then built before the guest resumes (today up to ~9 can still be building).
  - It turns on code (:685-715) that has never run in this fork, so it needs a warm-boot test via -SeedXenos.
  - The same line is in baseline, so our patches didn't introduce it.
- **(c) Non-blocking async mode:** not output-identical (it swaps stalls for pop-in).
  - It could only be an opt-in cvar, `d3d12_async_pipeline_no_wait`, default false. It needs a creation wait at the top of ShutdownShaderStorage.
  - The user judges the pop-in on a visible desktop.
- **Â§11 diagnostic run, cvars only, devoff2-bin, b-gate-menus-long, ~4.5 min per run:**
  - Arm A: `slow_frame_log_ms=50`. Output-identical (INFO lines only).
  - Arm B: adds `d3d12_pipeline_creation_threads=0`. Attribution only.
  - It answers Q1 (PRE load frame: game or emulator side), Q2 (fence wait after the burst), Q3 (translate vs create share, which decides (a)) and Q4 (heavy rows).
  - Analysis: slowframe_join.py (selftest 15/15, synthetic data only).
- The warm-storage proposal went to Agent 8 for after window 4.
- Â§5: a warm storage removes most first-view frames over 250 ms (devoff2 19 of 21), but some residue stays. Finding 8 is reworded to "most of these freezes".

**05:08, Agent 1: decisions.**
- Â§11 approved for tonight: one pass, A then B. The repeat and arm C go to S4.
- It runs through Agent 8's slot in this order: nativeB pair â attract + warm â Agent 2's inventory â Agent 7's dump â Agent 6's Â§11 A/B (~10 min) â Agent 11's throttling pairs (only if they end by 07:15). Agent 8 decides the fit.
- Agent 6 specs it to Agent 8 and analyses it with slowframe_join.py.
- (a), (b) and (c) go on the S4 leads list.

**05:14, Agent 1: nativeB pair result and the native3d stall** (Agent 3 harness, b-gate-menus-long, hidden desktop, functional only).
- Arm A native3d ran 04:59:45-~05:03:30 (`build\agent3\runs\20261122-045945-bgate-long-native3d`). Arm B nativeB ran 05:03:43-05:07:33 (`...\20261122-050343-bgate-long-nativeB`). Both: route complete, WM_CLOSE, exit 0.
- **nativeB: clean.** 0 errors, 0 critical, max frame 1000 ms. Agent 10's logdiff exit 0 (NEW 0); Agent 8's gate_logdiff flags only the A-only placement relocation line. The verdict is with Agent 10.
- **native3d: one 5 s guest-lock stall that recovered.**
  - game.log 197.24 s: STUCK-LOCK on CS 0x84959edc. Owner tid 0x13 parked at lr=82BCE244 (r3=300BE000); the waiter is thread 0x4.
  - The watchdog wrote hang-63248.dmp (65 MB) at 200.78 s, so the harness says CRASHED. But the route finished and the game closed by WM_CLOSE in 2.7 s, exit 0. Agent 8 agrees: a stall, not a deadlock.
- **My frames.csv check:**
  - native3d's 5198 ms frame had 56 pipeline creations taking 4341 ms. The same 56-creation frame in nativeB took 608 ms, with 126 ms of creation.
  - The next long frame had 42 creations: 3658 ms in native3d (only 1.3 ms of creation; unexplained so far) vs 509 ms in nativeB.
  - Run totals: 187 creations / 7753.6 ms (native3d, first arm) vs 188 / 277.6 ms (nativeB, second arm).
  - Reading: the first arm paid cold NVIDIA driver compiles, and the second arm reused them. That is arm order, not the build.
  - Both arms drop to 8-19 fps per 10 s from ~120 s (the late-route scene). That drop is the same in both.
- **Nothing points at 08933a7:** nativeB has the same draw.cpp guard and was clean. The commit stands pending Agent 6's triage.
- **Decisions:**
  - New task for Agent 6, read-only: (A) the stall triage, by ~06:15; (B) the Â§11 analysis, ~07:00. Agent 6 sends Agent 8 the Â§11 spec.
  - Agent 10 keeps the nativeB verdict and shares its map tools with Agent 6.
  - No native3d re-run unless Agent 6 recommends one and I GO.
  - Nobody touches the NVIDIA driver shader cache (host state).
  - Agent 8's queue: attract + warm â Agent 2's inventory â Â§11 A/B â Agent 11's pairs (only if they end by 07:15). Everything ends by 07:30.

**05:27, Agent 1: cron check 7, the nativeB verdict, S4 ratings, and an upload-copy correction.**
- **Check (05:24):**
  - One game is running: Agent 3's attract-devoffB, since 05:20. Before it: attract-devoff3 05:12-05:21, and Agent 7's dump 05:09-~05:12.
  - Free RAM 6.05 GB (with the game running), C: 245.1 GB.
  - 10 open tasks (#7, #12, #16, #17, #20-#25), all recently active, no stalls.
- **Agent 10 (05:24): nativeB 1b route pair PASS vs native3d.**
  - B: 54/54 steps, exit 0, 0 errors / 0 critical, no dump.
  - logdiff NEW 0 / MORE 0 / flags 0. The 19 common warning types have equal counts.
  - Slot heap 9/9 and pool copy 128/128 MATCH. 9 fail lines: 0/0. The same 26 scene teardowns, in order.
  - Caveat 1: the placement relocation lr=83F9B660 (A 1 / B 0) is not covered but is not a diff. It's heap-layout dependent, and it has 0 hits in 18 matrix native runs.
  - Caveat 2: the front-end exit came at a different press (the same class as OFF pair 1).
  - Recommends no rollback, plus a reversed-order tie-break pair.
  - **GO:** the reversed pair (nativeB then native3d, b-gate-menus-long, same config), via Agent 8's slot after Â§11 and before Agent 11's pairs, only if it ends by 07:15. It also checks whether native3d's freeze recurs with a warm driver cache, which helps Agent 6's triage.
- **Agent 10 S4 ratings (rating only):**
  - timer_queue_precise_wait (diff D07A2DC4â¦, staged 015C04A2â¦): SAFE as a default-off candidate (Â§14 row 15). Any default flip needs a game timing A/B.
  - host_execution_throttling_optout (diff 75756E8Dâ¦): SAFE as a default-off candidate (Â§16 row 17). It needs the hidden-desktop ABBAAB pair; it stays a player opt-in.
  - Both stay staged and unapplied until the S4 plan with the user. The live tree stays at the committed state.
- **Agent 5 (05:22):**
  - s0-s2 (matrix 20261122-0438) pass.
  - u2 barely engages on the title screen (<256 pooled acquires, no hits= line), so expect u2 = u0.
  - s1's scored window was worse (94.6 vs 109/110 fps), but that is one run in the slow state.
  - #20: all of the upload memcpy is the vertex-buffer RequestRange in IssueDraw (d3d12/command_processor.cpp:2848). Agent 5 named clear_memory_page_state=true as the cause.
- **My check of that cause:**
  - The SDK default is true (graphics/command_processor.cpp:89).
  - But every run's legodimensions.toml has `clear_memory_page_state = false` in its "Compatibility â¦ Do not change them" block. That covers all 12 recent agent8 matrices (incl. 0438 and the W4b dry runs 0336/0342) and Agent 3's runs.
  - The installer also forces it false for players (rexlego-installer/TomlConfig.cs:139).
  - So the frame-end SetSystemPageBlocksValidWithGpuDataWritten (d3d12/command_processor.cpp:4280) shouldn't run in our runs.
  - Asked Agent 5 to confirm with the profiles (are there samples in that function?) before naming a cause, and to coordinate with Agent 12 (#21 write-tracking re-arm). The cvar stays as it is.
  - The slimmer u0/u1 x5 (~28 min) upload matrix: yes, as a new file after the #20 summary, not scheduled.

**05:30, Agent 1: the reversed pair, Agent 4's answer, and machine load.**
- **GO for the reversed-order pair** (Agent 8 asked at 05:28): nativeB then native3d, b-gate-menus-long, same config as 04:59. It runs right after Â§11 (~05:49). Then Agent 11's pairs, only if a spec comes and they end by 07:15. Everything ends by 07:30.
- **Agent 4 (05:28):**
  - The two start-up hashes (0xA58EBA12â¦, 0x93B9F93Bâ¦) are not the placement pair. They are CreateShaderResource misses (shaders.cpp:513): registered create-hook objects that are never drawn.
  - The dump run also caught a second placement pair (vs-CCD76553â¦ / ps-E81FD692â¦) with no warning line, because the shared g_shader_warning_count (shaders.cpp:76) had passed its caps. So (b) packs 4 placement containers (+2 boot containers as an option); (b)/(c) by 06:30.
  - Threaded recording was off in the bgate-long stall run, so the Â§S3.2 guard (08933a7) never ran there. 08933a7 is cleared for the stall.
- **Agent 3 (05:28):**
  - The attract pair ran on a saturated machine (~100% CPU at base clock): Defender 2.9 cores, dwm 1.2, NVIDIA FrameView PresentMon 1.0, plus agents' recursive searches over the SDK (my own git grep at 05:23 overlapped devoffB).
  - devoff3's attract window was 2-3x slower and is excluded by the flags. Functional data is unaffected.
  - Broadcast: no recursive searches or scans over the big trees while a game runs. Asked Agent 8 whether PresentMon was also in window 3's process samples.
- Artifact: the 05:07 row now says 08933a7 was not involved, and the missing-shader lead covers the 4 shaders.

**05:40, Agent 1: Agent 7 #22 done, Agent 11 ready.**
- **Agent 7 #22** (agent7-present.md "Task #22"):
  - The dump run `sd` (matrix 20261122-0509) passed. native3d-bin's MANIFEST is 8/8 before and after. shader_dump_check PASS: 9 dumps, 0 failed.
  - PS 0xAC448F28 is not all zero: only words 0-11 are. The dump matches the container and guest memory.
  - A second VS/PS pair was hidden by the g_shader_warning_count cap (Agent 4); the same cap explains n3's 8x.
  - n-rows (native3d, functional, n=1): THREADED moves ~6.3 ms/f from the render thread to workers. fps 101 â 110 (n2) / 117 (n3), p50 9.3 â 7.2/6.7 ms. But p99 went 23.8 â 33.7/32.2 ms, and frames >33 ms 8 â 74/68. gpu_cmd is 0 in all native rows.
  - RefreshGuestOutput is not a copy. It is the swap's EndSubmission(true), which replays the whole deferred list into D3D12 (UMD encode), then Close/Execute/Signal. ~1.3 ms/f in timing (est.) on GPU Commands, the critical thread in d0 (87% busy, GPU ~55%). Devoff only.
  - R1, async chunked submit (SDK command_processor.{h,cpp}, deferred_command_list.h; cvars d3d12_submit_split_kb and d3d12_async_submit, default OFF): -0.7 to -1.0 ms/f, up to ~+20% fps if that thread stays critical (unverified). Output stays identical because it reuses the mid-frame EndSubmission(false) path. Risk: stage 1 low-medium, stage 2 medium-high.
  - R2, a redundant-command filter: at most -0.1 to -0.2 ms/f.
  - New tools: bench/agent7/shader_dump_check.py and bin_manifest_check.py (tests 4/4 each).
- **Next:** a new task for Agent 7, the THREADED tail-latency check (slow-state control first), due ~07:00. Agent 10 adds R1 stage 1 and R2 to its S4 ratings (design level).
- **Agent 11 #24:** the wrapper is ready (dry run PASS) and spec'd to Agent 8 (~19 min, if it fits by 07:15). Agent 11's 658 MB single-thread hash read at 05:16:22-05:17:40 overlapped the excluded devoff3 attract run.
- **Artifact:**
  - A new 05:35 row.
  - S4 rows: R1 replaces the "guest-output copy" row, and the THREADED row has the n-row data.
  - Finding 9 now records the capture result: not all-zero, and 4 shaders.

**05:42, Agent 1: the stall is cross-build, Agent 5's corrected cause, and the 06:31 slot.**
- **Agent 8 (05:38), attract job done 05:35:**
  - devoff3 was clean. devoffB and devoff3-warm each hit the CS 0x84959edc STUCK-LOCK, with the same waiter chain as native3d arm A. Both recovered, exit 0, dumps kept. The warm seed is unchanged.
  - So the stall is not native-specific. And 08933a7 is cleared: devoffB predates it.
- **Watchdog in baseline:** the SDK baseline 2897c31 already has it (git grep: 8 hits in xboxkrnl_rtl.cpp). So a baseline-bin attract run would log the stall too.
- **PresentMon:** not new. PresentMon_x64 (child of NVIDIA nvfvsdksvc_x64) has run since 11-13 17:36, through window 3 and the W4 dry runs (~1.0 core now; MsMpEng 2.5). Window 3 has no per-process samples. Nobody stops it. The user checklist now notes it (item 5); the W4b files are unchanged.
- **Agent 5 (05:39) correction:**
  - It retracts the clear_memory_page_state cause (the toml is applied) and the "cpu-write invalidations 0" evidence (that came from synthetic fixture logs).
  - The real path: guest sub_82B55588 calls MmSetAddressProtect every frame from the main loop (0.54/1.02 ms/f of main-thread VirtualProtect, a/b). A protect with write â PhysicalHeap::Protect (xmemory.cpp:2128-2144) â TriggerCallbacks â SharedMemory::MemoryInvalidationCallback over the whole range. The next draws' vertex-buffer RequestRange (d3d12 cp :2848) then re-uploads the range and re-arms the watch.
  - That is the 3.6-3.9 ms/f on GPU Commands (profile).
  - Open question: does the game write the range every frame?
  - This is the same mechanism as Agent 12's #21 re-arm, so: one combined proposal, no double counting.
- **Queue (Agent 8):** inventory â Â§11 05:40-05:51 â reverse pair 05:52-06:10 â Agent 11's pairs 06:11-06:31.
- **The free 06:31-07:15 slot, in priority order:**
  1. Up to 2 baseline-bin attract runs (functional) for the STUCK-LOCK question. Agent 6 and Agent 3 send the spec to Agent 8 by 06:15.
  2. Agent 5's logging-only diagnostic, if one exists and is spec'd by 06:15.
  3. Agent 3's attract re-run (OK).
  Agent 8 decides the fit. Everything ends by 07:30.
- **Agent 6's triage:** re-scoped to the cross-build lock. Write-up ~06:45, plus the baseline result by ~07:30.
- **Artifact:**
  - The 05:07 row is reworded.
  - Two new 05:38 rows.
  - S4 rows: memory copies now has the mechanism and is shared with Agent 12. The native pipeline row no longer mentions the lock. A new STUCK-LOCK row.
  - Checklist item 5 (PresentMon).

### 05:44 (Agent 1)
- **Agent 2's inventory** (05:39, 7.8 s, 1 thread): all 10 bins' exe re-hashes match their MANIFESTs, 0 problems. build/agent2 is 12.41 GiB; 5.56 GiB is deletable later (snapB/snapB3 once B is decided, plus gen-noflag). C: has 244.4 GiB free. Nothing deleted. Agent 2 is idle until Agent 8's all-clear.
- **The Â§11 diagnostic is running** (legodimensions pid 72944 since 05:39:58). Free RAM was 4.78 GB at 05:43 with the game running.
- **Artifact** "as of 05:45" copied to perf-notes/FINDINGS-AND-CHANGES.md. SHA256 D79C0308â¦D2D0EA4B, match.
- **Sent:**
  - @@to 8: the 06:31-07:15 slot priorities are OK; PresentMon is noted in the checklist.
  - @@to 6: #25 is re-scoped to the cross-build lock; the baseline-run spec goes to Agent 8 by 06:15.
  - @@to 5: one combined proposal with Agent 12; a logging-only run spec by 06:15, if one exists.
  - @@to 12: the same mechanism as Agent 5's finding.

### 05:55 (Agent 1)
- **Agent 3, #16 done:** the attract plan went to Agent 8 (notes 7.4, 05:50).
  - All 3 attract windows were excluded because the machine was CPU-saturated.
  - The plan: 3 arms x 4 â 55-60 min, or x3 â 42-45 min.
  - Warm storage cut pipeline misses from 264 to 56 (0 in the window). The stalls stayed: pm 0, CPU starvation.
  - STUCK-LOCK: every report came with a 5+ s frame, with the GPU thread on PM4 0x22 (draws) at a new read pointer each time. The owner lr differs per report (82BCE244 / 83FAF200 / 83FBF868). It looks like a symptom of starved frames, not a deadlock; Agent 6 to confirm.
- **Agent 3's idle-machine data** (05:36-05:46, no game): total CPU median 73.7%; Defender median 1.43 cores; only 25/169 samples under the 0.2-core gate.
- **My one-shot Get-Counter at 05:50** (a game was running): 10.8 of 12 cores busy.
  - game 2.15, dwm 1.15, PresentMon 1.00, Defender 0.69, CrossDeviceService 0.54, System 0.49, 3 electron ~0.8, taskmgr 0.29, 15 agy at ~0.2 each.
  - The agents themselves are part of the load.
- **Decision on Agent 3's re-run:** it stays 3rd in the slot and runs only if Agent 8's quiet gate passes at the time; otherwise it's skipped.
- **Agent 8:**
  - Â§11 arm A ended 05:43; arm B started 05:46:18 after the 6 GB wait.
  - ETAs: the reverse pair ~05:52-06:12, Agent 11's pairs ~06:13-06:33, then the slot to 07:15.
  - The slot runners now wait up to 3 min for 6 GB.
- **W4b risk found: memory.**
  - W4b's run-timing.ps1:150 refuses a run under MinFreeRamGB 6 (exit 3, no wait), and run-matrix marks it NOT STARTED and moves on.
  - Free/available RAM was 5.91 GB at 05:51 with a game running.
  - Physical-RAM users: 15 agy processes 4.7 GB WS; Firefox 2.46; Claude app 1.46; T3 Code 1.02; Discord 0.75.
  - The NVIDIA Overlay's 4.35 GB is private commit, but only 0.32 GB WS.
  - Fix with no W4b file change: checklist item 3 now asks the user to close those apps and check Task Manager "Available" â¥ 8 GB.
  - W4b chain hashed at 05:51 to scratch/w4b-hashes-0551.txt. All unchanged since 03:45: run-matrix.ps1 FEDCEB13â¦, run-timing.ps1 75F4B527â¦, common.ps1 A8975D12â¦, matrix-window4.json 6CA4AC6Eâ¦, RUN-WINDOW4B.cmd D89C0FC5â¦.
- **Agent 5:**
  - No existing counter shows whether the VB bytes change.
  - Optional ~5 min run matrix-s4-invalvol.json (9D6A6F2Câ¦, slow_frame_log_ms=1): invalidation volume per frame.
  - New finding: the game's protect calls never change host access (4 â 0x404, write-combine only, which the host ignores). C1 = skip TriggerCallbacks and VirtualProtect when host access is unchanged (default OFF), in a combined proposal with Agent 12.
  - GO for the run as slot priority 2. C1 goes to Agent 10 for a rating, with the write-fault cost if the game rewrites the whole buffer.
- **Artifact** "as of 05:55":
  - checklist item 3 (memory);
  - a 05:50 progress row;
  - the attract option row;
  - the STUCK-LOCK S4 row;
  - a finding 8 update.
- **Cron iteration 8 (05:54):**
  - The board shows 9 open tasks, as expected (#7, #12, #17, #20, #21, #23, #24, #25, #26). No game or build process at 05:54:35 (between Agent 8's runs).
  - Agent 4 is running single-file compile checks for #12(c) (build/agent4/s34/run_compiles.ps1: 4 compiles of shaders.cpp, 1 thread, BelowNormal). That is within #12's approved scope; they finish before 06:30.
  - Agent 3: the baseline spec (Agent 6's #25) is checked with Agent 8. The -InputScript patch goes to build/agent3/patches/; Agent 8 applies it only after window 4. "RECOVERED HANG" label in runstats.py: OK'd for after 07:15, with a re-test.
  - Reminder broadcast for the 06:33-07:15 quiet.

### 05:58 (Agent 1)
- **Agent 12, #21 done** (perf-notes/agent12-io-memory.md S4.1-S4.7; tool bench/agent12/s4_waits.py).
  - Cause: the guest handle heap's Lock/Unlock (sub_82B55588; 20 of 21 call sites cover the whole block) calls MmSetAddressProtect RWâRW every frame. PhysicalHeap::Protect â TriggerCallbacks then invalidates and unwatches the block. The result is a re-upload (UploadRanges 3.64/3.85 ms/f = 42% of GPU Commands busy) and a re-arm (0.70/1.41 ms/f = 11.8%).
  - The batch-1 fence costs under 2 Âµs/f.
  - P1 (= Agent 5's C1, cvar physical_protect_keep_watch, OFF) saves u Ã 3.6-3.8 ms/f plus 0.5-1.0 ms/f on Main. u is unmeasured. Risk is medium: Agent 10 must audit the bypass writers (PoolCopyHook first), the callback hooks and the GPU-written guard.
  - P2 is one G hold per re-arm (~6%, low risk, shared_memory.cpp). P3/P4 are minor.
  - An upstream race in PhysicalHeap::Protect (G is released before VirtualProtect(RW)) can leave pages valid + watched but host-RW, so guest writes can be missed for up to a frame. This goes to Agent 10.
  - Agent 12's counter-run request is covered by Agent 5's matrix-s4-invalvol.json (already GO, slot priority 2).
  - P1/P2 builds are S4 items for the user's go, not tonight.
- **New task for Agent 12:** stage, don't build, a logging-only diagnostic that measures u, plus a P1 write-fault estimate; P2 staging is optional. Report by ~07:45.
- **Artifact** "as of 06:00":
  - The memory-copies and write-tracking S4 rows are merged into one row.
  - New 05:55 progress row.
  - Copied to perf-notes.

### 06:05 (Agent 1)
- **Agent 9, #23 done** (perf-notes/agent9-codegen.md S4.0-S4.3).
  - S4.1: on devoff the render thread spins on a fence word that only the CP writes (EVENT_WRITE_SHD; one fence per kick + one per frame): 0.88 core (13.0 ms/f in a-prof). The host TimerQueue thread spins another 0.86 core to store a 1 ms tick. The CPU is an i7-1255U (PL1 ~15 W), so it is power-limited: freeing the spins can move fps only through headroom.
  - Fixes, all default OFF: (d) = Agent 11's d11t in W4b (the whole R3 bundle; isolating the timer change needs a later d11 vs d11t pair); (a1) a hook that sleeps until the CP writes, plus an SDK notify, ~-0.85 core; (a2) a rexlego-only backoff, ~-0.7 to -0.8 core. Probes P1/P2 are spec only.
  - S4.2: Main's "scene walk" is the UI/HUD layer render. Only guest UI state sets its work; nothing on it reads a timer, fence or query; no native-specific code is reachable by direct calls. The frontend confound is nil. H1 (more UI work per frame) is favoured. The count-only probe (S4.2.4) needs a rexlego grant, a build, a review and runs, so it is S4.
  - S4.3: Stage B/C codegen (non_argument_as_local + non_volatile_as_local): its 2.2 ms/f of save/rest evidence is render-spin time, so ~0 on devoff; a possible gain only on native Main.
  - Zero-build native A/Bs (n0 native_scene_diagnostics=false, n1 LEGO_NATIVE_MEMOPS=0) detect only >1.1 ms/f effects: not tonight.
- **Decisions:** Agent 9's optional scans are OK'd only after Agent 8 confirms its last run has ended (~07:15-07:30): â¤2 threads, read-only, targeted (no scans of build/ or thirdparty), done by 08:15. The HighResolutionTimer include/ check goes to Agent 10. No native zero-build A/Bs tonight.
- **Artifact** "as of 06:05": the S4 busy-wait row (render + timer threads), the codegen and scene-walk rows, a d11t bundle note in the W4b table, a 06:00 progress row. Copied to perf-notes.
- 06:03: legodimensions pid 85084 (started 06:00:57; the reverse pair's 2nd run). Free RAM 6.52 GB.

### 06:13 (Agent 1)
- **Agent 4, #12 done.** The SS3.2 hash=0 fix is live and committed (game 08933a7); native3d n0/n2/n3 logged 0 hash=0 lines, and check_n_rows passes n2/n3. Extras, scratch only (no live apply, no build):
  - (b) build/agent4/s34/aot-pack-proposal.md (B89DFA73â¦): Path A, pack all 4 placement containers with Agent 6's tools. ~45 min of agent time, then an Agent 2 bin, functional n-rows and the native vs Xenos screenshot check. Nothing gets packed before Agent 7 clears the PS words.
  - (c) build/agent4/s34/miss-cache-review.md (7AA19D11â¦) + shaders-s34.patch (328BDAE1â¦) on live shaders.cpp E87A2DEE: default OFF, with Agent 7's code-stamp invalidation. v3/v2 compile clean (patched + control); objcheck shows only the intended functions changed. Saves â¤5.98 of BindShader's 6.10 ms/f; the image doesn't change. With Agent 10 for S4.
  - bench/agent4/matrix-native-threaded.json: n0/th1/th2/th3 Ã3 on native3d-bin, ~30 min, sys_csv on, sha 76FE0BAAâ¦, plan-only OK. A later-window option; not W4b.
- **Decisions for Agent 4:** the screenshot check can't go in window 4 (W4b is frozen at d0/B/d3/d11t); it's an S4 step with the user. (b) packing is OK on scratch only (build/agent4/s35/), after Agent 7 clears the PS words and Agent 8 confirms its last run has ended (~07:30). â¤2 threads, BelowNormal; no live apply, no bin; stop by 08:25 whatever the state.
- **Agent 5, #20 summary** (perf-notes/agent5-uploads.md, Session 3 task #20, written with Agent 12):
  - The memcpy is D3D12SharedMemory::UploadRanges (shared_memory.cpp:328); 100% of sampled copies come from the vertex-buffer RequestRange in IssueDraw (command_processor.cpp:2848) on the CP worker. Memexport and textures have 0 samples.
  - Cause: the buffer Lock (sub_82B590E8 > sub_82B55588 > sub_82BD2808) calls MmSetAddressProtect on the whole buffer, always RW or RW|WC. PhysicalHeap::Protect invalidates and unwatches it, so the next draw re-uploads and re-arms all of it.
  - Cost (slow state, a/b): UploadRanges 3.64/3.85 ms/f of GPU Commands busy 8.43/9.42 (memcpy 3.09/2.91, re-arm 0.54/0.94). Protects cost Main 0.54/1.02. Bytes ~3-9 MB/f (estimate).
  - C1 (= P1) saves u Ã 3.64/3.85 + Main 0.54/1.02. At u = 0 it saves nothing on GPU Commands and pays write faults (F Ã 10-40 Âµs on Main; F = 17-51 â Main between +0.85 and -1.5 ms/f), plus 256 KB neighbour re-uploads and texture re-decodes. a-vol gives F_max = KB/256 + count.
  - New C1 condition: no provide_data page in the range. Landing order: build C1+P2 OFF, turn P2 on first (0.23/0.82 ms/f), then C1 after the rating, the counter runs and an A/B. C1 is with Agent 10.
  - Next: the x5 uploads matrix as a new file before 06:33.
- **Decisions for Agent 5:** close #20 once the a-vol numbers are in S4.8 (if a-vol hasn't run by 07:30, close anyway with it noted pending). Define u one way in S4.8: the formula needs u = the unchanged share, but one line calls it the share of bytes written after each Lock; match Agent 12's diagnostic. The x5 matrix as a new file is fine: plan-only check, no runs tonight.
- **Artifact** "as of 06:12": the missing-shader row and finding 9 (the (b) proposal and the ready stopgap), the native threaded-modes option (~30 min), the re-upload row (proposal, landing order, the -1.5 ms/f risk), 06:10 and 06:12 progress rows.

### 06:27 (Agent 1)
- **Agent 10, 1b tie-break** (reversed order; nativeB 055041, native3d 055439). Every must-match item PASSES again: logdiff 0/0/0, slot heap 9/9, pool copy 128/128, warntypes equal, PSO 187/187. Both exit 0, no dumps, no STUCK-LOCK. The exit split repeated: first frameâexit native3d 118.9/120.5 s vs nativeB 105.7/108.9 s. OFF leans the same way (devoffB left in 2/2 runs at 127.7/133.0 s; devoff2 in 1/3 at 130.6 s). No wall-clock, frame-count or clamped-dt clock fits all 9 runs. 1b is reopened on that one item; it's not a fail item and no rollback is needed.
  - **Decision: (a)+(b).** Record it now as an open item, not as accepted. Then (b), read-only: Agents 3/9 locate the guest code that starts the front-end fade, and Agent 10 diffs its codegen snap1 vs snapB3 (an mftb read, or a flag poll kept in a local, would make it a B behaviour change). Targeted reads only until Agent 8's last run ends, then â¤2 threads. Done by 08:15; if it isn't found, it gets written up as unexplained for S4. No (c) runs tonight.
  - The W4b read-out (Agent 8, no W4b file change) also checks that B's scored windows show the same scene as d0's.
- **Agent 10, S3.4 miss-cache:** SAFE at default OFF (shaders-s34.patch 328BDAE1â¦, shaders.cpp E87A2DEEâ9567FE3F; batch2-review S18 + addendum, row 19). The ON run must show shader_miss_cache_insert for VS AC449538 and PS AC448F28. **No GO tonight:** S4 items aren't applied or built before S4 is planned with the user.
- **Agent 7, #26 done** (agent7-present.md "Task #26"; bench/agent7/threaded_tail.py).
  - THREADED's tail is structural: the swap holds the guest â¤1 frame ahead of a 3-4-thread chain (draw.cpp:5447-5451). throttle_wait is 46-76% of wall time and tracks the slow-frame count (Spearman 0.92). ~2 slow frames/s vs ~0.2/s for n0 at 85-100 fps.
  - S4-T1: LEGO_NATIVE_CHAIN_PRIORITY=1 (OFF; ABOVE_NORMAL + EcoQoS opt-out for the recorder, the RecordingQueue thread and the prep pool). Output-identical; risk low to medium.
  - Metric rule adopted: p99, 1% low and >33 ms/min as primary next to mean fps; â¥3 runs per arm; sys.csv; per-phase reporting.
  - PS words cleared for Agent 4: a real literal block plus valid microcode.
  - Zero-code checks (n2/n3 with LEGO_NATIVE_TIMING=1, n2 with LEGO_NATIVE_PARALLEL_DRAWS=0) go in the slot as priority 3b.
- **Agent 6, #25 Part A** (perf-notes/agent6-hang-triage.md): not a deadlock. All 6 reports are long kGraphicsLock holds that ended on their own.
  - The waiter is always the main-thread scene teardown into sub_82A2A260. The owner is the render thread waiting for the GPU: on native, synchronous PSO creation (56 in 4341 ms, cold driver cache); on Xenos, the guest D3D loop waiting on the CP read pointer (sub_83FBF7D0 â sub_83FAF180), which never yields.
  - Load makes it worse but doesn't cause it: the CPU was 97-100% busy, the game got only 1.3-1.8 cores, and the GPU was 17-29% busy.
  - 3 of 89 logs, all 05:03-05:32. The reverse pair clears native3d's exe (187 PSOs in 282.9 ms vs 284.4 ms). The SDK hang dump adds 1.7-3.6 s to each first report.
  - Recommendations: delay the dump to ~30 s; S4 (e), a yield hook (OFF), to be merged with Agent 9's (a1)/(a2) since it's the same loop; native seeded pre-create after W4. Defender/PresentMon â user question 3.
- **Agent 6, #25 Part B** (Â§11.1): skip Â§10.1 (translate share 0.011-0.025, far below the 0.2 line; caveat: neither run reached the 67-miss shot). PRE load frames are guest-side; the high-cb rows are mostly host-GPU fence wait; the heavy rows are GPU-thread throughput. Open: 37-49% untimed remainder in run B's burst rows, which needs an idle-machine CPU profile. :564 (b) goes with the first warm-storage run after W4; (c) stays opt-in.
- **Agent 5:** u is now defined once in S4.8: u = the unchanged share, measured as Agent 12's u_block (an upper bound). The x5 matrix is bench/agent5/matrix-native-uploads-x5.json (62F58F2Bâ¦): 11 runs in ~28 min, or 9 in ~23 min. Not run tonight. Agent 12 confirmed the a-vol parser at 06:16, and Agent 8 has the OK.
- **Agent 3:** the -InputScript patch is delivered, not applied.
  - vpadhost-reset.patch and the runstats RECOVERED HANG patch are OK only after Agent 8 posts that its last run has ended, with the tests noted in 7.4.
  - W4b dependency check: the chain doesn't reference vpad or runstats, but common.ps1:75 copies harness/legodimensions.toml (B763DABBâ¦, last write 11-21 21:45). It must stay unchanged until after window 4; recorded in scratch/w4b-extra-deps.txt.
- **Cron iteration 9 (06:25):** no game or build processes at 06:25:08; free RAM 7.74 GB; 6 open tasks (#7, #17, #20, #24, #25, #27).
  - W4b re-hash vs 05:51: only bench/agent8/run/matrix-native-threaded.json changed (06:04:52, Agent 4's sys_csv; not a W4b file). RUN-WINDOW4B.cmd, run-matrix, run-timing, common, matrix-window4.json and the rest are unchanged.
- **Slot order sent to Agent 8:**
  1. baseline (#25);
  2. invalvol;
  3. (a) the devoff3 re-run, only if the quiet gate passes; (b) otherwise, or if time remains, Agent 7's checks.
  - Every run ends by 07:30. Agent 8 posts when its last run has ended.
- **Artifact** "as of 06:25": finding 10 (the stuck lock); S4 rows (translator dropped, native pipelines confirmed, stuck lock, threaded tail, shader cache); the upload option (x5/x4); question 3 (Defender/PresentMon); progress rows 06:15, 06:20 and 06:23. Copied (62EDBA06â¦, match).

### 06:29 (Agent 1)
- **Agent 11, #24 done** (agent11-kernel.md "Result (task #24)"; run 20261122-0600, 06:00-06:19, functional; W4b closure sha256 53/53 equal before and after). NO EFFECT: the EXECUTION_SPEED opt-out was on (applied 0.14-0.36 s after start, read back C=0x1 S=0x0 in 99.6-99.7% of polls; the only miss was at teardown), yet d0e was 3/3 slow (onsets 40/49/47 s, E 596-697 MHz) vs d0 3/3 slow (103/71/37 s). This rules out process-level EXECUTION_SPEED/EcoQoS throttling. It doesn't rule out PL1/package power, per-thread visibility QoS or the best-efficiency overlay/EPP.
  - **Decision:** drop host_execution_throttling_optout from S4, and the runner switch (Agent 10's caveat). The package-power column (\Energy Meter(RAPL_Package0_PKG)\Power; 12.3 W with no game at 06:25) is staged as a new sampler file for after window 4, with no W4b file change. timerq_slowstate.ps1 over W4b's fg=1 runs goes into the W4b read-out with Agent 8.
- **Artifact** "as of 06:30": the power-throttling S4 row marked dropped, a finding 7 update, a 06:27 progress row. Copied (7EDE4067, match).

### 06:31 (Agent 1)
- **Agent 6:** agent6-hang-triage.md S9 item 4 is now one S4 item: the sub_83FAF180 wait hook (Agent 9's (a1)/(a2); Agent 6's (e) = (a2) with a zero sleep, covered by Agent 9's sweep). A loaded-machine STUCK-LOCK arm was added to its test plan. The dump delay is staged only; Defender/PresentMon is user question 3. No reply needed.
- **Artifact:** the stuck-lock S4 row and finding 10 now point to the merged item. Copied (FFB1E52C, match).

### 06:36 (Agent 1)
- **Agent 5, #20 done** (agent5-uploads.md "Session 3 task #20", S4.0-S4.8; bench/agent5/s4_slowframe.py now reads rotated logs; matrix-s4-invalvol.json 9D6A6F2C…; matrix-native-uploads-x5.json 62F58F2B…, plan-only, not run).
  - Mechanism: the memcpy is UploadRanges (shared_memory.cpp:328), all of it from the vertex-buffer RequestRange in IssueDraw (command_processor.cpp:2848). The guest's buffer Lock re-protects the range RW, which invalidates and unwatches it, so it re-uploads.
  - a-vol (06:20-06:24, functional): 1.87 invalidations and 3847 KB per frame, almost all one 3844 KB buffer locked whole about once per frame; at most 3.76 MB/frame re-uploaded. F_max 16.9, so C1's worst case on Main is -0.14 ms/f at u = 0 (this replaces the -1.5 ms/f in the 06:12 entry). C1 can be built OFF without waiting for u.
  - Ranked once with Agent 12: C1 (= P1), P2, M1, P3, P4, M2, G1. Landing order: P2 first, then C1 after Agent 10's rating, u and an A/B. New C1 condition 4: no provide_data page in the range.
- **New staging tasks** (idle agents prepare for the user's return; no game runs, no builds, light reads until Agent 8's last run ends, done before the 08:30 quiet):
  - Agent 5: stage C1 (physical_protect_keep_watch, OFF) as a scratch patch in build/agent5/s4-c1/, apply order agreed with Agent 12, TU-only compile check after the last run (1 thread), review note + test plan; by 08:25.
  - Agent 7: W4b read-out add-on in bench/agent7/w4b_readout/ (metric rule per run/arm, B-vs-d0 scene check, slow-state flag); Agent 8 owns the read-out and decides; by 08:15.
  - Agent 11: perf-notes/S4-DRAFT.md (one row per S4 item, proposed batch/check/window order, Agent 2's estimates, open user questions); no decisions; by 08:15.
- **Artifact** "as of 06:33": the re-upload S4 row (3.8 MB/frame measured, worst case ~0.14 ms/f, C1 can be built OFF), 06:31 progress row. Copied (616CA103…, match).
- 06:34: no game or build processes; free RAM 7.61 GB. Agent 8 is preparing the slot (zero-code matrix + waiter script).

### 06:38 (Agent 1)
- **Agent 8 (slot status):** #25 base (baseline-bin attract) started at 06:35:32, 2.5 min late. The command text of Agent 8's q launcher contained a runner name, so the base launcher's wait matched it. Agent 8 killed its own launcher and restarted it; nothing else was affected. Base ends ~06:57.
  - Then q: 30 s quiet-gate tries until 07:06. The cold arm runs only on a pass; the warm arm only if it can start by 07:06. Probably skipped: the no-game load at 06:25-06:29 was 40-48% total CPU (max 55-93%), with MsMpEng up to 2.5 cores.
  - Then 3b: Agent 7's n2t, n3t, n2s on native3d-bin (bench/agent8/zero/matrix-native3d-zero-code.json = Agent 4's rows plus one env var each, sys.csv on). One arm per run-matrix call, each only if it can end by 07:30. Expected end 07:17-07:27, then "last run ended" to all. No reply needed.
- Tasks assigned: #28 (Agent 5, C1 staging), #29 (Agent 7, W4b read-out add-on), #30 (Agent 11, S4-DRAFT.md). @@to 12 sent: agree the apply order (diagnostic, P2, C1) and base hashes with Agent 5.
- **Artifact** "as of 06:38": 06:38 progress row (slot status, the three staging tasks). Copied (A8B4094E…, match).

### 06:46 (Agent 1)
- **Agent 10, S19** (agent10-batch2-review.md §19, Agent 12's S4.7 `PhysicalHeap::Protect` race): CONFIRMED, both forms.
  - Form 1 (RW→RW, e.g. Lock): G is released after TriggerCallbacks (xmemory.cpp:2135). A GPU upload's EnableAccessCallbacks can then protect the page RO and set its bit before the view's host protect (L1772 via L2143) makes it RW. The page ends up valid, bit set and writable, so guest writes are missed until the next TriggerCallbacks over it (EAC skips set bits, L2238-2239).
  - Form 2 (RO/NoAccess→RW), no race needed: EAC never watches RO pages (L2228-2239), so TriggerCallbacks returns without invalidating (L2321-2323). A pre-existing upstream gap.
  - Fix (i), keeping G across both host protects (G→heap_mutex_ is the legal order), closes form 1. Fix (ii), re-protecting afterwards, isn't enough alone. Form 2 needs its own fix: invalidate on any protect that adds write access. These are correctness fixes, not output-identical, so they're rated and gated separately.
  - C1 removes today's healing by the next Lock, so fix (i) lands with C1 (residual R1 comes in S21).
- **Agent 10, S20:** #27 `shared_memory_upload_hash_log` is SAFE at default OFF.
  - The diff (D2905301, +145/-0, 4 hunks) applies to live B120D07C; new/ BB0838CE is exactly live + diff.
  - OFF costs one inlined cvar load and one untaken branch per non-empty upload call, plus one registry entry.
  - ON is SAFE for functional runs. It adds 1-3 ms/f on GPU Commands, so no timing arms. It can also bias u slightly low, so cross-check pages/frame against an OFF run.
  - Nit: DESIGN.md says SDK HEAD 90e7ccd; it is c5fe668.
  - Applying it waits for the S4 OK and my schedule.
- **Decisions:**
  - Finding 11 goes in the artifact: a pre-existing write-tracking gap, found by code review, with no symptom traced tonight.
  - Agent 12 stages fix (i) after #27 if it fits by 08:25: scratch only, its own switch, default OFF. The form-2 fix gets a design note only.
  - C1 stacks on fix (i). Apply order: diagnostic, P2, fix (i), C1. C1 engages only with fix (i) on, unless Agent 10 prefers otherwise.
  - Agent 11's S4-DRAFT gets rows for fix (i), the form-2 fix and the diagnostic.
  - No reply to Agent 10 needed.
- **Artifact** "as of 06:46":
  - finding 11;
  - a Leads row for it;
  - the re-upload row: race confirmed, C1 needs fix (i), diagnostic SAFE at default OFF;
  - a 06:46 progress row.
  - Copied (F54D87C8…, match).

### 06:48 (Agent 1)
- **Agent 8 (06:46), #25 base:** finished at 06:44:02. Run 1 on baseline-bin (v0.2.0) logged a STUCK-LOCK on the same CS 0x84959edc as our builds (hang-60748.dmp kept). By Agent 6's rule, run 2 was skipped; the full report went to Agent 6.
  - **Consequence:** the stuck lock reproduces on the original release, so it is not caused by our changes. Finding 10's open "v0.2.0" item is answered. Agent 6's verdict on the waiter chain and dump details is due ~07:30.
- **Slot:** the q gate has been retrying since 06:44:08 and isn't quiet yet (75.8% / 67.9% total CPU, MsMpEng up to 3.7 cores). It retries until 07:06. Then 3b (n2t, n3t, n2s), each only if it can end by 07:30, likely 07:06-07:17, then "last run ended". No reply needed.
- **Artifact "as of 06:48":**
  - new 06:48 progress row;
  - finding 10's bullet changed to "Not caused by our changes";
  - the stuck-lock Leads row now says v0.2.0 does it too.
  - Copied to perf-notes (133B8176…, match).

### 06:49 (Agent 1)
- **Agent 3, #25 base1 (FUNCTIONAL ONLY):** baseline-bin reproduces the STUCK-LOCK at +219.0 s. The owner and waiter chain are the same as in devoffB and devoff3.
  - The game wrote a dump, recovered, exited with code 0, and finished the route (91/91).
  - Load was 97.9% (MsMpEng up to 2.95 cores).
  - So the lock predates the sprint and isn't specific to B.
  - runstats still labels this run CRASHED until the RECOVERED HANG patch goes in after Agent 8's last run. Read-outs must treat that label as a known tool artifact.
- **Agent 3, 1b:** partial timeline results went to Agents 9 and 10. Static RE of the fade code starts after the q runs (≤2 threads). By 08:15 it reports guest addresses or "unexplained". No reply needed.
- **Artifact "as of 06:50":** the 06:48 row and finding 10 now have the same owner/waiter, the recovery, exit 0 and 98% CPU. Copied (05878406…, match).

### 06:55 (Agent 1)
- **Agent 3 (06:52):** q (the devoff3 quiet re-run) was called off together with Agent 8. The gate failed every 30-s try (15 of 15) because MsMpEng ran at 1.8-3.7 cores against a 0.2 limit, continuously since 06:25 with no game running.
  - #16 stands on the cold-run data (FUNCTIONAL ONLY).
  - The slot frees ~10 min early for Agent 7's 3b runs, Agent 3's 2 patches (after the last run), Agent 2 and Agent 4.
- **Agent 8 (06:53):** 3b started at 06:52:27: n2t, n3t and n2s on native3d-bin, ~3 min each. The slot should end ~07:04, then Agent 8 posts "last run ended".
- **Agent 10, §21 (C1/P1 physical_protect_keep_watch):** SAFE at default OFF (the old path runs unchanged). With ON, devoff output is identical only when conditions 1-4 all hold.
  - Item 1: the CP writers spot-checked (:315, :437, :1289, :1305, :1368) store through TranslatePhysical and never invalidate. C1 can only lengthen a stale window that exists today, but static reading can't rule that out, so a verify mode is required.
  - Item 2: the SharedMemory guard is consistent under G. Evaluate the hooks under G before taking the heap mutexes; the hooks take no lock. PrimitiveProcessor's always-allow is right; keep rexlego hookless.
  - Item 3: condition 3 is required; old_protect==nullptr is right.
  - Item 4: only diagnostics and two heals ((b) bypass writers, (c) §19 form 1) depend on lock time.
  - Agent 5's points: (2) condition 4 is needed (memexport provide_data exists). (3) No fault loop (L2391-2394). (4) The 256 KB widening is real and re-uploads the same bytes.
  - New residual R1: a §19 form-1 state heals at the next lock today but persists under C1.
  - Flip ON only with all of:
    - A) verify mode, 0 mismatches over title + menu walk + a level load;
    - B) §19 fix (i) lands with C1, or R1 is accepted in writing;
    - C) C1 inert on native from startup;
    - D) Agent 12's test 1 + logdiff NEW 0 + frame hash, then the timing A/B.
  - Also: use BaseHeap::Protect's page rounding; don't nest the two heap mutexes.
  - §19 addendum: form 2 has no known trigger in this game (its protects are 4/0x404).
- **Cron iteration 10 (06:54):**
  - Game pid 38540 (0652-n2t-r1, native3d-bin) running since 06:52:31; no build processes.
  - Free RAM 5.63 GB with the game up.
  - MsMpEng averaged 1.30 cores and total CPU 97.2% (2-sample Get-Counter).
  - Open tasks: #7, #17, #25, #27, #28, #29, #30. No stalls.
- **W4b risk noted:** Defender's sustained load would distort window 4.
  - Added a check to step 3 of "Before you double-click": wait until "Antimalware Service Executable" is under ~5% CPU. The runner and the W4b files are unchanged.
  - Agent 7's read-out add-on gets a background-CPU column: system minus game per scored window, with window 3 as the reference.
  - I'll sample MsMpEng at each cron check through ~09:30 and put the last reading in the artifact.
- **Messages:** Agent 5 gets §21's requirements for the staged C1 patch. Agent 2 gets a reminder: no builds or new bin dirs tonight; reads and estimates are OK; ask before anything else.
- **Artifact "as of 06:55":**
  - checklist step 3 (the Defender check);
  - the attract option (re-check called off);
  - the re-upload row (C1 SAFE at default OFF, plus the four ON conditions);
  - the Gaps row and finding 11 (form 2 has no trigger in this game);
  - a 06:55 progress row.
  - Copied (E5E2DC9D…, match).

### 07:10 (Agent 1)
- **Agent 9 (06:57), 1b (b):** B can't change the front-end timer.
  - mftb is the same out-of-line call in both trees, every guest load and store is volatile, B only keeps CTR/XER/CR/reservation in call-volatile locals, and musttail only turns a call plus return into a jump.
  - devoff2 and native3d share A codegen yet exit 10+ s apart. nativeB matches native3d's front-end fps (~100) and cores (2.2-2.35), so it most likely finishes the same background guest work sooner.
  - Agent 9 recommends (a). My decision stays (a)+(b) until Agent 10's diff and Agent 3's RE are in (08:15).
- **Agent 9 (06:58), merged S4 item "fence-wait spin"** (sub_83FBF7D0 -> sub_83FAF180). It is Agent 9's (a1)/(a2) plus Agent 6's (e), which is (a2) with Q=0.
  - Stage 1: a rexlego hook behind an env switch, OFF by default. It does _mm_pause for ~20-50 us, then SwitchToThread, then sleeps Q on a high-resolution waitable timer, Q in {0, 125, 250, 500} us.
  - Tests: P1 waits/frame; a slot functional run (menus + level, gate_logdiff); a sweep off/0/125/250/500; Agent 6's loaded-machine attract-long arm on devoffB (off vs on, counting STUCK-LOCK).
  - Stage 2 (a1: SDK CP notify + WaitOnAddress) only if needed. The new hook file, CMake entry, build and review are all S4.
- **Agent 5 (06:58 and 07:04), #28 C1 staging: stalled.** Its session hit repeated content-filter blocks, and build/agent5/s4-c1 is empty. It asked for a re-issue or a fresh session before 08:25.
  - Base hashes (git-clean at SDK c5fe668): xmemory.cpp 6E8FA1BA, xmemory.h 80100865, shared_memory.cpp 15C89EDB (0BE4BADC after diag+P2), shared_memory.h 4D861738, primitive_processor.cpp E07F6902.
  - C1 goes on shared_memory.cpp 0BE4BADC and xmemory.cpp 141FB1A9 (after fix (i)), with its Protect changes after fix (i)'s second lock acquire.
- **Agent 8 (07:00): last run ended at 07:00:02; the slot is over.**
  - Final queue: #25 base run 1 STUCK-LOCK (run 2 skipped by rule); a-vol OK; q not run (the gate was never quiet: 15 tries, MsMpEng 2.0-3.7 cores).
  - 3b n2t/n3t/n2s all OK: TIMING columns non-zero in n2t/n3t; n2s shows serial workers=2; hash=0 0; no errors, STUCK-LOCK or dumps. Sent to Agent 7.
  - No runner, W4b or cmd file changed. Agent 8 asked whether to close #7 now.
- **Agent 10 (07:01), #17 summary** (agent10-helpers.md "Task #17 summary"):
  - nativeB 1a PASS; 1b PASS on every must-match item, tie-break included. The front-end exit (~12 s earlier on nativeB) stays OPEN; the (b) verdict comes by 08:15 with fe/fediff.py.
  - Agent 9's clock sub_83FAF088 is identical. sub_83FB2640 and the per-frame manager sub_82FEA350 differ only by B's mechanical rewrites. 6 of the 9 functions are still being classified.
  - STUCK-LOCK: the CPU-starvation class, also seen in OFF builds; Agent 6 owns it. n-rows PASS.
  - SAFE at default OFF: timerq §14, pthrottle §16, miss-cache §18 (no GO tonight), the diagnostic §20, C1 §21 (ON only with A-D). §19 race CONFIRMED.
  - R1 stage 1 is SAFE as a default-off test bed under conditions 1-6. R2 step 1 is SAFE; step 2 is SAFE-IF (a)-(e) (§17). All S4 items wait for the S4 plan with the user.
- **Agent 12 (07:05), #27 done:**
  - a-vol confirms the chain: one 3844 KB lock per frame plus 0-2 events of 4 KB; V ~3.76 MB/f; F_max ~16.9.
  - The diagnostic costs +0.25-0.4 ms/f when ON, so it is for counting runs only. P1's faults cost <=0.25 ms/f on devoff, so Main still gains 0.3-0.9 ms/f at u_block=0.
  - Staged, all OFF. All pass apply-check and clang syntax, and a sequential scratch apply reproduces every hash:
    - s4-diag (D2905301);
    - s4-p2 (77BEB64E, +30/-0, cvar shared_memory_single_hold_rearm; with Agent 10 for a rating);
    - s4-fixi (80CAD795, +19/-0, cvar physical_protect_hold_global_lock; xmemory.cpp 6E8FA1BA -> 141FB1A9).
  - Budget 22/79.
- **Decision: C1 staging goes to Agent 12**, not to Agent 2 as I drafted at 07:00.
  - Agent 12 has been free since 07:05, C1 is its P1, and both C1 bases are its own staged files. A fresh agent would need most of the 75 minutes to read in.
  - Agent 10 rates the diff in S4. Agent 2 stays idle (estimates for Agent 11 by message only).
- **W4b scope check for Agent 3's patches:** the W4b chain (bench/agent8/run) uses its own winhelper snapshot and reads only harness/legodimensions.toml. It never calls harness/run-game.ps1, runstats.py or harness/vpad. So the runstats RECOVERED HANG and vpadhost-reset patches don't touch W4b.
- **07:01 check:** no game, ninja, clang or lld running; free RAM 7.57 GB.
- **Artifact "as of 06:58"** (logged late): copied (5ED64BE9..., match).
- **Artifact "as of 07:10":**
  - a 07:10 progress row (slot over, 3b clean, Agent 10's summary, P2 and fix (i) staged, C1 to Agent 12);
  - the re-upload and Gaps Leads rows;
  - the "Next (overnight)" row (game runs over; quiet from 08:30).
  - Copied (32061927..., match).
- **Messages sent (07:10):**
  - task to Agent 12: C1 staging, taking over #28;
  - task to Agent 9: grant of agent9-codegen.md, finish (b), write the fence-wait S4 item;
  - Agent 5: #28 handed over, nothing more tonight;
  - Agent 8: close #7, write the read-out procedure, re-issue after the user's run;
  - Agent 3: patches OK now; game runs only after asking, ending by 08:20;
  - Agent 2: estimates for Agent 11 by message; no builds.

### 07:10, second entry (Agent 1)
- **Agent 3 (07:08): both harness patches were applied at 07:02,** after Agent 8's 07:00:02 post (approved in the 06:27 entry).
  - runstats.py labels runs that only tripped the lock watchdog as RECOVERED HANG; exit codes are unchanged. The applied-file test had 0 failures in 37 checks, and base1 now reads RECOVERED HANG.
  - vpadhost reset: run 2 = run 1. The runner exited 3 at the RAM check, and no game started.
  - Both are noted in agent3-run-harness.md 7.4, with the baseline STUCK-LOCK run, and q recorded as "not run: gate never quiet". harness/legodimensions.toml is untouched (B763DABB...).
- **Agent 3, 1b:** the native constraints went to Agents 9 and 10. The reverse pair is equal at A1resp, then drifts 11.6 s apart, so the split builds up after A1. Agent 3 has no guest address yet; Agent 9 has the static side (07:50). The verdict or "unexplained" comes by 08:15.
- **Tasks:** #31 went to Agent 12 (C1 staging) and #32 to Agent 9 (fence-wait S4 item + 1b (b)). Budget 23/79. Agent 5 closed #28 as handed over: no files changed, nothing built or run.
- **07:08 check:** no game, ninja, clang or lld running; free RAM 7.42 GB; harness/legodimensions.toml B763DABB (unchanged).
- Open tasks: #7 (Agent 8, closing), #17, #25, #29, #30, #31 and #32. No replies needed.

### 07:19 (Agent 1)
- **Agent 6 (07:15), #25 done** (agent6-hang-triage.md S8 + new S3.4): pre-existing = YES.
  - baseline-bin attract-base1 (game 127e04b + SDK 2897c31) hit the same STUCK-LOCK at launch+219.03 s (H0+34.45 s). It was CS 0x84959edc, with a waiter chain identical to devoffB's and the same owner object 0x30111018 / tid 0x17.
  - The 5 s hold plus the 3.54 s dump made an 8.58 s frame. Exit 0; base2 skipped by rule.
  - Load: CPU 97.7% busy (MsMpEng mean 1.35 cores, max 3.04; PresentMon 1.0); host GPU 14-22% busy during the hold.
  - **New: the owner was in a different loop,** the game's GPU-query busy-wait. sub_82BDCFB8 calls D3D GetData sub_83FB09E8 back to back, with no yield, until it stops returning S_FALSE. The dump's host stack confirms this; 83FB0948 in the report is a stale slot.
  - The dump's CP thread wasn't waiting: its RIP was in dxilconv.dll, under unverified nvwgf2umx frames called from rexgpu-xenos. So it was compiling a shader on the GPU thread, and pipeline creation on the CP thread can feed these holds on the standard path too (fits PipelineCache::EndSubmission; no PDB to name the SDK function).
  - **Consequence:** the merged S4 hook on sub_83FAF180 would NOT cover base1. S9 item 4 now adds the same OFF-by-default back-off for this poll: REX_HOOK_RAW on sub_83FB09E8 only when lr==0x82BDD028 and it returns 1, or a hook on sub_82BDCFB8. It is output-identical by the same argument. Agent 9 has been told.
  - S9 item 6 records Agent 3's 07:02 RECOVERED HANG relabel. Note: 35,853 B, 300 lines, read-back checks pass; backup build/agent6/hang/agent6-hang-triage.md.bak-0720.
  - Tests: T0 brackets, a 22-run native scan, an 89-log STUCK scan, 5 dump reads, slowframe_join on both S11 arms, base_check + base_owner on base1 (a map cross-check of 5 known sites), and patch dry-run + read-back checks. Budget 23/79.
- **Message:** Agent 9 gets the GetData poll as an explicit part of #32's fence-wait section, so the S4 item covers base1's case too.
- **Artifact "as of 07:18":**
  - finding 10 (v0.2.0 confirmed from the dump; the second loop; the S4 back-off for the poll);
  - the stuck-lock and busy-wait Leads rows;
  - a 07:18 progress row (also noting Agent 3's relabel).
  - Copied (2B251514..., match).
- Open tasks: #7 (Agent 8, closing), #17, #29, #30, #31 and #32.

### 07:25 (Agent 1): cron iteration 11
- **Check (07:23):** no game, ninja, clang, lld or cl running; free RAM 7.49 GB.
- **CPU (2 x 2 s Get-Counter):** MsMpEng averaged 10.5% (~0.1 core), down from 1.3-3.7 cores at 06:25-06:55. Total CPU was 42.0% with agents working.
- **Board:** 6 open tasks, all active:
  - #7, Agent 8: writing the W4b read-out procedure in build/agent8/scratch/w4b-readout.ps1 and w4b_rules.py, not in bench/agent8/run;
  - #17, Agent 10: build/agent10/fe/livein*.py;
  - #29, Agent 7: bench/agent7/w4b_readout;
  - #30, Agent 11: S4-DRAFT.md, 07:23;
  - #31, Agent 12 and #32, Agent 9: assigned at 07:10, no writes yet.
  - No stalls.
- **Agent 4 (07:23): the s35 pack is done,** on scratch in build/agent4/s35.
  - Pack run run-071627: VERDICT PASS, 07:16:27-07:16:50, affinity 0x3, BelowNormal. Gate 2 was Agent 8's 07:00:02 post.
  - All 4 placement containers compiled to DXIL. PSs 75A4D1AB/E81FD692 have spec mask 2, and VSs ACAF01F0/CCD76553 mask 1, like the main cache. So the S4 build has to re-run lego_gpu_prelink_runtime.
  - Index 19,116 -> 19,122: 6 rows, every old row kept. The production FindShaderByMicrocode finds all 4, with and without the main archive. Post check 28/28; no side effects; pins unchanged.
  - sha256 (all in run-071627/SHA256SUMS.txt): runtime-cache.cpp AEA36683...A734, merged index E4C05782...0617, addition 154242FB...98F6.
  - The README has Results and an S4 handoff for Agent 2: point the runtime-cache cache var (CMake 283-285) at a copy of the new cache; use the fixed index path (CMake 274-275) only if the snapshot index is still base 2DB85917; and make a direct sha-checked copy, because snap-native-inputs.py only copies from live.
  - Notes §S3.5 updated (F3997889...BA3C). Nothing applied, staged or built. The bin, Agent 8's n-rows and the screenshot check with the user wait for S4. (c) is still SAFE at OFF and parked. Agent 4 has stopped, with no more runs tonight. No reply needed.
- **Artifact "as of 07:25":**
  - a 07:25 progress row (the pack; Defender down to ~0.1 core);
  - the missing-shaders Leads row and finding 9 ("all 4 packed on scratch; the S4 build re-runs the runtime prelink").
  - Copied (568E11F4..., match).
- Next: cron ~07:53. Due by 08:15-08:25: Agent 10's (b) verdict, Agent 3's RE, and #29, #30, #31, #32. W4b re-hash and the 08:30 broadcast follow.

### 07:27 (Agent 1)
- **Agent 11 (07:25): package-power sys.csv columns staged and tested,** new files only, in bench/agent11/syscsv-pkg/.
  - No W4b, bench/agent8 or build/agent8 file changed; Agent 11 hashed them before and after.
  - The staged LdSys.cs adds \Energy Meter(*)\Power and 4 columns at the end of each row: pkg_w, pp0_w, pp1_w, dram_w.
  - Tests at 07:21-07:23, no game: test_syscsv_pkg -Compare -Rounds 3 PASS 58/58; sys_summary compat PASS; both adoption diffs pass git apply --check.
  - Readings: idle pkg ~13-14 W, pp0 ~7 W; dram reads 0 on this laptop; ignore the first row. Sampler CPU is unchanged (1.17 vs 1.15 ms/sample); each sample waits ~1.7 ms longer in the PDH collect.
  - Adoption after window 4: Agent 8 applies LdSys.cs.diff (sys_summary.py.diff is optional and cosmetic). The first sampler start compiles a new DLL, so it goes outside a timed run, and pthrottle_w4b_hash will then flag both files (expected).
  - Scope note: bench/agent11/syscsv-pkg was outside #30's file grant (S4-DRAFT.md, agent11-kernel.md). It was new files only with no W4b effect, so I accept it, and asked Agent 11 to ask first next time.
  - Decision: Agent 8 isn't told tonight. Agent 11 adds it to S4-DRAFT.md as a measurement row with the adoption steps.
- **Interim W4b re-hash (07:26):**
  - 30 of the 31 bench/agent8/run files match scratch/w4b-hashes-0551.txt. matrix-native-threaded.json changed, as at 06:26; it isn't a W4b file.
  - RUN-WINDOW4B.cmd lives in bench/agent8/ (not run/) and matches in full (D89C0FC5...).
  - harness/legodimensions.toml is B763DABB (unchanged).
  - The pre-08:30 re-hash must look for the cmd in bench/agent8/.
- **Artifact "as of 07:27":** the power-throttling Leads row (package-power columns staged and tested; added after window 4). Copied (AF8836CB..., match).

### 07:31 (Agent 1)
- **Agent 7 (07:27): #29 done.** Read-only W4b read-out add-on bench/agent7/w4b_readout/w4b_readout.py, plus README, self-test and outputs out-0013/out-0342 (.md/.json). Details in agent7-present.md "Task #29" (with a RESUME block).
  - Per run and per arm: p50, p99, 1% low and >33 ms/min next to fps; median (min..max) with n<3! marks; deltas and paired deltas against d0 (devoff2); a scene check against d0; the slow state from matrix_recheck (imported read-only) and timerq_slowstate.ps1; and the background column (system CPU from sys.csv minus proc.csv game CPU, with SAT/BG+ flags).
  - Window 3 has no sys.csv in any of its 19 runs, so it can't be the background reference. The #26 note had mislabelled runs 0330-0349 as window 3; corrected. The tool falls back to `--bg-ref-cores X` or the matrix's own unsaturated runs. Window-3 game cores per arm: d0 3.43, base 3.42, d11 3.47, n0 2.33.
  - All 20 game runs with sys.csv tonight (03:30-06:57) were CPU-saturated (busy 0.99-1.00), so background reads as 12 minus game cores (~9.5-10.3), and that is only a minimum. These runs get a SAT flag and a CPU SATURATED banner. BG+ (more than 1 core above the reference) only means something on an unsaturated, quiet-morning W4b. Other load: PresentMon (NVIDIA FrameView) 1.0 core, Dell TechHub ~1.0 core.
  - Scene floor 0.15 -> 0.015 (same-scene runs differ by 0.000-0.005). Window 3's light run d11-r1 (0.036) is now flagged. Without it d11 is -3.1% vs d0 and worse, instead of -2.3% and overlapping.
  - Tests: self-test 12/12 (incl. the PowerShell timerq test); window 3 19/19 runs agree with frames.json/results.csv and the arm fps equal summary.md; 0342 Quick 5/5 agree, all SAT, slow-state onsets equal to timerq's. Background formula vs live % Processor Time: +0.01 to +0.07. No `__pycache__`; W4b chain unchanged (last written 04:23).
- **Artifact "as of 07:30":** a 07:30 progress row (the read-out add-on, saturation, the d11 correction) and the window-3 d11 text in the batch table (-3.1% vs devoff2 once the light run is excluded; it read -2.3%). Copied (B210DC53..., match; re-checked 07:31).
- **Task to Agent 7 (07:32): accepted its offer.** Zero-code read-out of 0652/0655/0657 (n2t/n3t/n2s on native3d-bin), read-only on existing data, FUNCTIONAL ONLY and SAT, input to S4 timing plans only. A short "Zero-code read-out" section in agent7-present.md, one line to Agent 11 for S4-DRAFT.md (incl. the d11 correction), report by 08:20. <=2 threads, no game runs or builds, no bench/agent8 changes, no `__pycache__`.
- Next: cron ~07:53. Due by 08:15-08:25: Agent 10's (b) verdict, Agent 3's RE, #30, #31, #32 and Agent 7's read-out. W4b re-hash and the 08:30 broadcast follow.

### 07:40 (Agent 1)
- **Agent 10 (07:35): 1b (b) result, not a codegen change** (codegen-review "(b) result").
  - Agent 9's 11 clock-list functions and run 2's 9 have identical instruction sequences: mechanical rewrites only (OTHER 0, no inline mftb). Whole tree: 164,786 functions, 0 sequence mismatches, 0 unexplained, 91,605 rlw proven. Agent 3's 8 native callers of sub_83FAF088 are covered (7 with no OTHER; 83FC5D68 has one stwcx cr0.so block, SAFE class).
  - SO: 1 writer (sub_83E5C88C, mtxer), 0 readers. B locals: no read-before-write except the setjmp-style CR save in sub_83E49CA0 (not front-end), and no read-after-call on any path (liveflow CFG).
  - Timer: sub_82FD4868 arms only if sub_82FB9020 == 1 (byte 0x848E2EA2 == 0, plus mode-3 queries of sub_82A832F8, bits 3/6); event 5 counts only while [app]+2288 == 0. That fits background-work gating.
  - Verdict: not a codegen change. The item stays OPEN for S4: find the writers of those flags, then one instrumented arm-time pair.
- **Agent 3 (07:38): 1b host side done** (read-only, notes 7.5). Agrees with Agent 10.
  - Every host clock the game can read runs on real time and is the same in OFF, native3d and nativeB: mftb 50 MHz, KeQuerySystemTime, KeTimeStampBundle and 48 kHz WASAPI audio. KeQueryInterruptTime and xam GetTickCount are stubs.
  - Native mode differs only in how the game waits for the GPU (no vblank; fence and idle waits drain the host GPU; callbacks run after the host GPU finishes), and that is identical for native3d and nativeB. No host code touches Agent 10's timer flags (0x848E2EA2, bits 3/6 at 0x849004EC, [app]+2288).
  - Route logs: the reverse-order pair reaches the menu INSTALL batch together (72.2 s), then nativeB leaves 11.6 s sooner (INSTALL to exit 46.5-49.7 s vs 59.6-61.3 s, ratio ~0.8). The order nativeB < native3d < devoffB <= devoff2 matches how fast each build runs game code.
  - Verdict: not codegen, not a host clock; stays OPEN for S4; no rollback, not a fail item. The harness side of the S4 arm-time pair is ready (b-gate-menus-long.txt); nothing runs before window 4.
- **Decision (1b): (a), final.** Recorded under the 03:50 OFF standard as "on native, B leaves the front-end ~12 s earlier"; not a fail item, no rollback. Root cause -> S4 (flag writers, then one instrumented arm-time pair). Agent 9 drops its remaining 1b work (whole-tree clock list, HRT check, optional scans) for #32.
- **Agent 10: P2 (shared_memory_single_hold_rearm; batch2-review S22, row 23) SAFE at default OFF.** ON is output-identical, with no new lock edge and no unlock() under the hold. Caveat: the memexport full-buffer fallback (d3d12 command_processor.cpp:3063) becomes one long G hold (~3x today's longest), so S4 confirms it doesn't run or caps one hold's length. The fix (i) item 4 static check is queued for S4.
  - Agent 12 told: record the caveat as an S4 gate in S4.12. The staged P2 diff stays unchanged tonight, because C1's bases depend on it.
- **#17 done (Agent 10).** batch2-review S17-S22 + status rows 18-23; codegen-review: nativeB gate, 1a/1b, tie-break, the OPEN front-end item and "(b) result"; helpers.md Task #17 summary + RESUME; new read-only tools in build/agent10/nb and build/agent10/fe. Tests: fediff selftest 6/6; feall whole tree 0 missing, 0 mismatch, 4,568 rlw proofs, 0 failed; livein 29/29; liveflow 9/9. No builds, runs or repo writes.
- **New task to Agent 10 (07:41): S4 rating pass,** notes only, report by 09:30:
  - the fix (i) item 4 static check, if it fits before 08:25;
  - default-OFF ratings for Agent 12's C1 diff (#31) and Agent 9's fence-wait + GetData item (#32);
  - a check of S4-DRAFT.md's ratings against its notes, with corrections sent to Agent 11.
  - From 08:30, reading and notes only.
- **Artifact "as of 07:40":** a 07:35 progress row (codegen ruled out for nativeB's earlier menu exit, Agent 3 agrees from the host side; P2 rated SAFE at OFF with the long-hold caveat); the native3d-vs-nativeB option row and the "Next (overnight)" row (one difference recorded, not codegen, root cause in S4); the re-upload Leads row (P2 rating + caveat); the B section's open item (Agent 10's result, Agent 3's agreement, decision (a)). Copied (ACE8332C..., match, 350 lines).

### 07:42 (Agent 1)
- **Agent 7 (07:40): #33 done.** Zero-code read-out (FUNCTIONAL ONLY, SAT, n=1).
  - Files in bench/agent7/w4b_readout/: out-0652/0655/0657 .md/.json (w4b_readout.py --all; the tool is unchanged), zero_code_bins.py + zero-code-bins.txt (10 s bins before/after the slow-state onset, showing which columns rise on slow frames), and a README section. In agent7-present.md: "Task #33" and a new RESUME.
  - n2t: 136.7 fps / p99 21.6 ms / 23 frames >33 ms per min, no slow state. n3t: 122.9 / 37.2 / 114 and n2s: 123.6 / 32.8 / 69, both with the slow state inside the window, where most of their tail sits.
  - The scene check isn't possible (native frames). Background >=10 cores and SAT on every run. So there is no verdict on TIMING or PARALLEL_DRAWS; the section lists what a timed S4 test needs.
  - Tests: every run exits 0 under python -B; each run's check agrees with frames.json and results.csv; arm fps equal summary.md; the bin script's onsets match the recheck (100.2 and 78.5 s) and a re-run gives 0 differences; LF, no BOM, no __pycache__, nothing written outside its files.
  - Agent 8's read-out procedure confirmed: 0 JSON differences on Agent 8's 3 dry dirs. Agent 11 has the S4-DRAFT line with the d11 correction (-3.1%).
  - Agent 7 stands by; no new task. Open tasks: #7 (Agent 8), #30 (Agent 11), #31 (Agent 12), #32 (Agent 9), #34 (Agent 10).
- **Task #34 assigned to Agent 10** (the S4 rating pass, 07:41).
- **Artifact "as of 07:42":** a 07:40 progress row (the three native draw-mode checks give no verdict: n=1, saturated, two hit the slow state in the window; Agent 8's read-out procedure confirmed) and a note in the native draw-mode option row. Copied (A56C1A9D..., match, 351 lines).
- Next: cron ~07:53. Due by 08:15-08:25: #30, #31, #32 and #7's close-out. W4b re-hash and the 08:30 broadcast follow.

### 07:44 (Agent 1)
- **Agent 8 (07:43): #7 closed** (timing runner + slot queue). Its files-changed list is cumulative over the whole task.
  - The W4b read-out procedure is in agent8-window3.md "W4b read-out procedure (Agent 1, 07:08; one procedure with Agent 7's #29 add-on)" (L733). It replaces the older 5-step "Window 4 read-out" list and passes `--scene-floor 0.02` (Agent 7's tool default is 0.015; both flag window 3's light run at 0.036). w4b_readout.py is frozen tonight (07:24:09, 48,449 B, sha256 7C7A0673...7A284B0B). Agent 7 confirmed the procedure on Agent 8's 3 dry dirs (0 JSON differences).
  - Scripts: build/agent8/scratch/w4b-readout.ps1, w4b_rules.py, readout-dry.ps1.
  - Interim check: the newest write in bench/agent8/run is still matrix-native-threaded.json (06:04:52; not a W4b file); nothing else there since matrix_recheck.py at 04:23. The full re-hash comes before 08:30.
  - After the user's W4b run (~10:45) I re-issue the read-out as a new task to Agent 8, using this procedure.
  - Open tasks: #30 (Agent 11), #31 (Agent 12), #32 (Agent 9), #34 (Agent 10).
- **Artifact "as of 07:45":** "When it's done" now links the written read-out procedure (agent8-window3.md L733). Copied (4FE114B4..., match, 351 lines).

### 07:48 (Agent 1)
- **Agent 11 (07:44): #30 done.** perf-notes/S4-DRAFT.md, 342 lines (04B32B6F at 07:47).
  - 40 item rows in 6 groups (switch/default, A10 rating, output change, build cost, measured/estimated effect, test, dependencies, status), plus drops, shared files and the apply order.
  - S4a, a fast ~6-10 min build: #7 u diag, #8 P2, #38 precise wait, plus #5 fix (i) once rated; on native, #2 miss cache or #1 pack. S4b, a full rebuild for C1 (~37-46 min), only if #7's u_block is 0.25 or more (A2's estimates).
  - Functional checks, timing windows W5-W10 (<=45 min each, A7's metric rule), 5 user questions (§4a), items for A1/A10/A12 (§4b).
  - The 07:40-07:50 update: P2 SAFE (b2r S22) with the memexport caveat; fix (i) still unrated; #24/#25/#28 rewritten from A9's S5.2; A7's #33 runs in #22 (inconclusive); the d11 -3.1% correction in #39; the #40 package-power row.
  - Tested: every row cross-checked against its source notes (line ranges in §6), scripted edits each matched once, each of the 8 tables has one pipe count. No builds, runs or git writes.
- **Agent 9 (07:46): #32 done.** agent9-codegen.md S5.1 (1b exit split, closed per 07:40) and S5.2 (the merged GPU-wait spin back-off S4 item incl. Agent 6's GetData poll: two loops, stage-1 Xenos-only hooks with files/CMake, stage 2, test order with Agent 6's loaded-machine arm, Toy Pad note, needs). Also: RESUME, the S4.1.2/S4.1.3 HRT fixes, the db16cyc count, S4.2.5 scan results.
  - Files: build/agent9/s4/fence-wait/gpu_wait_backoff.cpp.draft (372 lines, not compiled, rexlego style), build/agent9/b-clock/ (clock-list.md, fe-gate-flags.txt, tools), build/agent9/s4/spin/db16cyc_count.py + db16cyc-sites.txt, build/agent9/s4/scene-walk/arm_scan.py + scans-s425.txt. Agent 11 told.
  - Tested with static reads only (fq.py index, single-file greps, 1-thread A-tree scans), ASCII/LF/no-BOM/120-column checks, a brace and #if balance check on the draft. Nothing built or run.
- **My answers to S4-DRAFT §4b** (in the new task to Agent 11):
  - #37 watchdog dump delay: staged only, not an S4 item; my 06:28 call stands. The artifact's Leads were stale (STUCK-LOCK row and finding 10); fixed now.
  - #7's ON cost: functional-only either way; record both numbers.
  - #32 (no switch): ships with a switch (OFF) unless Agent 10 rates it output-identical (in #34).
  - #8's memexport caveat: an S4 gate, not a change tonight (count the full-buffer RangeWrittenByGpu calls in the S4a functional run; a cap only if that path runs). The staged P2 diff stays as it is.
  - #18/#20 GO to stage: deferred to the S4 kickoff with the user after window 4.
  - Missing ratings, R1/R2 and b2r row 23's path: Agent 10's #34.
  - nativeB: closed for tonight as (a); root cause is an S4 functional item. Harness relabel: done (Agent 3, 07:02).
- **New task to Agent 11 (07:49):** S4-DRAFT upkeep, notes only, final by 09:30, with a "Changed since 07:44" list.
- **Artifact "as of 07:48":**
  - S4-DRAFT.md linked from "When you're back" (a new "After window 4: the draft S4 plan" paragraph), the Leads intro and a new 07:44 progress row (with Agent 8's close-out and Agent 9's #32);
  - questions 4 (the on-screen check of the 4 native shaders) and 5 (opt-in no-wait pop-in) added, matching S4-DRAFT §4a;
  - the STUCK-LOCK Leads row and finding 10: the dump delay is staged only, not an S4 item;
  - the busy-wait Leads row: Agent 9's write-up and stage-1 draft (not compiled; Agent 10 reviews it).
  - Copied (804465DE..., match, 356 lines).
- Open tasks: #31 (Agent 12, 08:25), #34 (Agent 10, 09:30), plus Agent 11's upkeep task.

### 07:54 (Agent 1, cron iteration 12)
- No legodimensions, ninja, clang, lld, cl or link process. Free RAM 7.47 GB.
- MsMpEng 4.7% and 2.3% of one core (~0.05 core); total CPU 28-31%. Defender stays calm (07:23: ~0.1 core).
- Board (13:52 UTC): 3 open tasks: #31 (Agent 12), #34 (Agent 10), #35 (Agent 11, assigned 07:49).
- No stalls:
  - Agent 12 is writing C1 staging in build/agent12/s4-c1 (make_c1.py 07:48, c1_mkdiff.py 07:50, keep-watch.diff / keep-watch-rexlego.diff / chain-live-to-c1.diff / HASHES.txt 07:51). Its notes are unchanged since 07:04 (the S4.12 write-up is due by 08:25).
  - agent10-batch2-review.md written 07:49 (#34); S4-DRAFT.md written 07:53 (#35).
- Next: W4b re-hash and the process check before 08:30, then the 08:30 broadcast. Cron ~08:23.

### 08:01 (Agent 1)
- **Agent 12 (08:00): #31 done, all PASS.** C1 (P1, cvar physical_protect_keep_watch, default OFF) staged in build/agent12/s4-c1/.
  - keep-watch.diff 1B2BA4E3... (SDK, 5 files, +362/-3) + keep-watch-rexlego.diff 4D0C1079... (game memory_watch.cpp, +6/-0), on diag -> P2 -> fix (i). chain-live-to-c1.diff 1D2CC1F3... is the same chain as one diff, for reference.
  - Bases: all 6 C1 bases and the 3 live chain bases match.
  - `git apply --check` exits 0 for diag, P2 and fix (i) one at a time, for the combined diff on the live SDK, and for the rexlego diff on the live game repo. (One call with all four patches can't work, because git doesn't chain patches to the same file; the combined diff replaces that check.) The 4-step scratch apply reproduces all 8 staged files byte for byte.
  - clang -fsyntax-only, control vs patched: 4 files, 8 compiles, all exit 0, no new warnings (bench/agent12/s4c1_syntax.ps1).
  - All S21 items covered (map in agent12-io-memory.md S4.12): verify cvar with K/F checks; C1 engages only under fix (i)'s hold; rexlego blocks it from static init and stays hookless; guards run under G before the heap mutexes and take no lock; Protect's rounding; the two heap mutexes are never nested.
  - Open for Agent 10: the rexlego hunk changes the native fingerprint once; residuals E1 and R2; a K mismatch in verify mode sends that protect down the normal path. Forwarded to Agent 10 for #34.
  - P2's memexport long-hold caveat is recorded in S4.12 as an S4 gate; the P2 diff is unchanged. NOTE.md added; RESUME updated.
  - No builds, game runs, live-tree edits or git writes. Agent 12 stands by.
- **All S4 staging planned for tonight is done.** Open: #34 (Agent 10) and #35 (Agent 11), both notes only, by 09:30.
- **Artifact "as of 08:02":** an 08:00 progress row (C1 staged; the last S4 staging tonight; notes only until 10:00) and the re-upload Leads row (C1 staged, Agent 10 reviews the diff). Copied (CC85DDB5..., match, 357 lines).

### 08:11 (Agent 1)
- **Agent 12 (08:10): Agent 10 rated C1 SAFE with the switch OFF, and SAFE to test turned ON under S21 A-D** (batch2-review S24, row 25).
  - Needed before C1 goes ON: a positive control for gate A (a kept-protect counter plus a log line on the first kept protect). It would also give gate C a positive check on native.
  - Optional: a one-time warning when C1 is on without fix (i); making both switches restart-only.
  - Agent 12 offered a small C1 v2 (edit make_c1.py, re-run the diffs, the 4-step chain and the syntax check; ~20 min) on a GO; if the compile check couldn't finish by 08:25 it would wait until after window 4. With the apply, the native baselines need re-pinning.
- **Decision: no GO tonight; C1 v2 waits until after window 4** (before any S4b build).
  - It's only needed before C1 goes ON, and S4b itself waits on #7's u_block.
  - ~20 min from 08:10 can't reliably finish the syntax check by 08:25, and a half-finished chain at the 08:30 quiet is worse than the verified v1.
  - v1 stays exactly as staged (HASHES.txt). Agent 12 writes Agent 10's rating and the v2 plan into S4.12 + RESUME (notes only, by 09:30). The two optional items go to the S4 kickoff.
  - Agent 11 told, for S4-DRAFT #4.
- **Artifact "as of 08:12":** an 08:10 progress row (C1 rating, v2 deferred and why) and the re-upload Leads row (rating + the counter needed before ON). Copied (01868905..., match, 358 lines).

### 08:23 (Agent 1, cron iteration 13)
- **Agent 12 (08:20): notes done, notes only** (agent12-io-memory.md; sha C2517CEC... as reported).
  - The S4.12 tail and RESUME now carry Agent 10's S24/row-25 rating of C1 and the v2 plan:
    1. required before ON: a kept-protect counter + a first-kept log line;
    2. optional: a one-time warning when C1 is on without fix (i), and restart-only switches;
    3. re-pin native3d/nativeB after the apply.
  - v1 untouched: 18/18 equal HASHES.txt (FBEC14B4...).
  - For Agent 10's S25 item 4: no existing log can prove that P2's memexport full-buffer fallback (d3d12 command_processor.cpp:3060-3064) never runs. It logs nothing, and memexport_trace only gives a lower bound over the armed frames. So P2 ON needs a counter (a frame_stats id, one Add call and a slow-frame field; ~+4 lines in 2 SDK-internal files; not staged) or a cap on one hold.
- **Decision: Agent 12 stages that counter after window 4, in the S4a set, before C1 v2.**
  - Why S4a: P2 is an S4a item, and Agent 10's S22 gate counts that path in the S4a functional run.
  - When staging, Agent 12 confirms it keeps S4a a fast build and checks file overlap with #7 u diag (apply order). A cap only if the counter shows the path runs.
  - Agents 10 (S25 item 4, for #34) and 11 (S4-DRAFT #8, for #35) told.
- **Pre-quiet checks (08:22:55):**
  - No legodimensions, ninja, clang, clang-cl, lld, lld-link, cl, link or cmake process. Free RAM 7.40 GB.
  - MsMpEng 2.3/3.1/1.5% of one core (~0.02 core); total CPU 27-32%.
  - W4b re-hash: 31 of 32 match scratch/w4b-hashes-0551.txt. Only matrix-native-threaded.json differs (06:04:52; not a W4b file), as expected. harness/legodimensions.toml B763DABB (unchanged).
- Board (14:21 UTC): 2 open tasks: #34 (Agent 10; notes written 08:15) and #35 (Agent 11; S4-DRAFT.md last written 07:53). No stalls; both due 09:30.
- **Artifact "as of 08:22":** an 08:20 progress row (Agent 12's notes; P2 ON needs a counter, staged after window 4 for S4a, then C1 v2) and the re-upload Leads row (08:20: P2 ON needs the counter; a cap only if the path runs). Copied (404285C1..., match, 359 lines).
  - 08:24: step 3 of the W4b instructions now says Defender was calm at 08:22 (well under 1% in Task Manager terms); refreshed again near 09:30. Re-copied (1873A619..., match, 359 lines). Agent 12's notes hash checked: C2517CEC (matches its report).
- Next: the 08:30 standing-quiet broadcast (timer set), then notes only. Cron ~08:53.

### 12:24 (Agent 1, session 3 resumed after a Windows Update restart)
- **What happened:** Windows Update restarted the PC twice, at 08:29:31 (MoUsoCoreWorker, "Service pack (Planned)") and 08:34:16 (TrustedInstaller, "Upgrade (Planned)"); it booted at 08:34:48. That ended every agent session. The user relaunched agy-grid at 12:08 (board run 2: Agents 2-12 are fresh sessions, no tasks, no claims). My 08:30 standing-quiet broadcast never went out, and window 4 never ran.
  - Installed: KB5132057 (2026-11 preview cumulative update, OS build 26300.10075); KB5137006 (.NET Framework preview); Intel DTT dtt_ext 9.1.10501.3322; Intel IPF providers 3.4.1009.0 (socthermal, perfmon, systemconfig, mods); Intel RST iastorhsa_ext 20.3.2.1007; Defender signatures 1.463.417.0 (08:46).
  - GPU drivers unchanged: NVIDIA MX570 32.0.16.1088, Iris Xe 32.0.101.7085.
- **Nothing was building or running at the restart** (the 08:22 pre-quiet check above). Only notes were being written.
- **Integrity checks (12:10-12:20), all pass:**
  - Git: `git fsck --no-dangling` exits 0 in both repos; no .lock files. Game HEAD 08933a7 = mine/perf/opt; SDK HEAD c5fe668 = mine/perf/opt. Status shows only the expected entries (game ` m rexglue-sdk`, ` M thirdparty/plume`; SDK ` m thirdparty/simde`).
  - 511 text files written since 06:30 under perf-notes, bench, harness, env and build/agent*: no truncation. Every NUL hit is a UTF-16LE PowerShell console log (06:31-07:55); the zero-length files are empty stderr captures.
  - W4b re-hash: 31 of 32 match scratch/w4b-hashes-0551.txt (A1's old conversation 0b71823b); only matrix-native-threaded.json differs (06:04, not a W4b file), as at 08:22. harness/legodimensions.toml B763DABB, unchanged.
  - Build manifests: devoff2-bin, devoffB-bin and devoff3-bin 7/7 each; native3d-bin and nativeB-bin 8/8 each.
  - This file: 2212 lines, last entry 08:23, intact. FINDINGS-AND-CHANGES.md = the old artifact (1873A619); carried into my new artifact.
- **Two notes-only tasks were cut off (both were due 09:30):**
  - Old #34 (Agent 10, S4 rating pass): b2r S23 (fix (i) SAFE), S24 (staged C1, row 25) and S25 (S4-DRAFT check, corrections 1-9) are written. S26 (Agent 9's item #24 back-off + Agent 6's GetData poll) was half written. Still open: item #32's output-identical check (pipeline_cache.cpp:564), the R1/R2 summary and S25 item 4 (the P2 counter). Notes last written 08:28:07 (b2r 183,182 B, 3AA2269F, 1420 lines; helpers 68,119 B, 12A935A8).
  - Old #35 (Agent 11, S4-DRAFT upkeep): the pass 5+6 edits were prepared in its scratch (s4draft_edits_0830.py at 08:28:47; s4_part1-3.py) but never applied, so S4-DRAFT.md is still the 07:58:42 version (CA69EB1F, 368 lines). The scripts assert line numbers in b2r, which Agent 10 rewrote at 08:28, so they need re-deriving.
- **Agent 12's notes changed after my 08:24 check (expected):** at 08:25:43 it logged my 08:23 go in RESUME and S4.12 L1128-1140: the counter first in S4a, then C1 v2; staging checks: keep S4a fast (a one-TU variant inside command_processor.cpp rebuilds 1 SDK file instead of 5), check overlap with #7's u diag, a hold cap only if the path runs. Now 4B2CAF85 (146,908 B, 1212 lines).
- **Machine after the restart (12:12-12:20):**
  - The effective power overlay is 961cc777 (best efficiency), as in every overnight run; leave it. AC on, battery 100%.
  - The screensaver is back ON (WPXSCR, 120 s); the user sets (None) before W4b.
  - Post-update churn: 90-99% total CPU at 12:15 (MsMpEng ~1.4 cores, OfficeClickToRun ~0.95, CrossDeviceService ~0.94, svchost ~0.95, memory compression ~0.6). The 12:18 minute: 45% total, MsMpEng 1.08 cores.
  - Quiet monitor running (my task-65): it ends on 3 consecutive minutes with total < 25% and Defender < 0.1 core, or after 150 min (log: my scratch/quiet-monitor.log).
  - Open apps: ChatGPT (13 processes, 1.8 GB), Copilot, Roblox, an Electron app, NVIDIA Overlay, Task Manager. PresentMon is running (as in window 3). 12.4-14.6 GB available. The old protected pythons are gone.
- **Comparability caveat:** W4b stays internally comparable (Latin square with the d0 reference). Any comparison with window 3 or the overnight runs now crosses the Intel DTT/IPF update (DTT manages the power limits behind finding 7's slow state) and the OS update. Noted for Agent 8's read-out and S4-DRAFT's W5+.
- **Plan:** Agent 10 resumes old #34, Agent 11 old #35, and Agent 8 does a no-launch runner readiness check. All notes or reads only, subagents=0, at most 2 threads. Agents 2-7, 9 and 12 stay idle (no broadcast, to keep the machine quiet) until W4b ends. W4b waits for the user and a quiet machine. Run-2 task numbers are logged when assigned.
- Old transcripts (brain\<id>): A1 0b71823b, A2 3df40b15, A3 abdc37e1, A4 d400a2df, A5 1ee64dce, A6 2250c023, A7 5f19f11b, A8 e9520d7d, A9 347a85a8, A10 81377e33, A11 306cd50a, A12 dc5d9ed1. Mine now: 31fc63c5.
- **Artifact "as of 12:25":** the header is now "Next: timing window 4 (still ready after the restart)": the recovered state, a post-restart checklist (screensaver back on; close ChatGPT, Copilot, Roblox and Task Manager; wait for my all-clear on Defender; leave the power mode), a "One thing changed under window 4" caveat, an 08:29-12:25 progress row, and the stale "When you're back" references fixed. Copied (7246F788..., match, 362 lines).
- Quiet monitor at 12:24: total 43-49%, MsMpEng 0.94-1.12 cores since 12:18. Not quiet yet. Check-in cron set (every 30 min, 8 times; my task-99).

### 12:26 (Agent 1, cron iteration 1)
- **Run-2 tasks assigned (12:26:07):** #1 Agent 10 (resumes old #34, the S4 rating pass), #2 Agent 11 (resumes old #35, S4-DRAFT upkeep), #3 Agent 8 (W4b post-restart readiness check, no launch). All subagents=0, notes or reads only. They had just started, so no stall check yet.
- No legodimensions, ninja, clang, lld, cmake or python process.
- Quiet monitor 12:22-12:26: total 42-45%, MsMpEng 0.94-1.21 cores. Not quiet; ~14.7 GB available.
- Next: cron ~12:56.

### 12:47 (Agent 1)
- **Agent 10 (12:41): run-2 #1 done** (old #34 resumed). Checked: b2r 196,617 B, 16D6330D, 1494 lines; helpers 67,684 B, 7C6CC4AD, 527 lines; both CR=0. It re-hashed every input against the 08:28 state (all unchanged).
  - **Item #24, the GPU-wait back-off with Agent 6's GetData poll as H2** (b2r S26, row 27): landing OFF is **SAFE** after step 0 (grants, a syntax compile, the batch-nolr build and the map check including H3). Fix N1 before the compile (cheap, not a blocker). ON is **SAFE to test** after P1 (positive controls), the functional pair (Q=250 vs OFF: logdiff clean apart from the ON line, the same exit codes, no new STUCK-LOCK) and the sweep with Agent 6's loaded arm (sleep_fail == 0). Output-identical by construction; the cost is wake latency. Draft #25 and the sub_82BDCFB8 fallback stay unrated (no diff).
  - **Item #32, the warm-boot fix** (S27, row 28): **output-identical** (only timing changes: the same PSOs and the same log lines apart from the "Created N ... in X ms" value; it can only remove a timing-dependent first-submission skip in async mode) and **SAFE**. Under my 07:48 rule it ships **without a switch**. Before landing: a6 S10.2 runs 1-4 (a cold regression run, a warm boot with -SeedXenos devoff2-214, 5 warm boots ending in WM_CLOSE, threads=0). Interactions: re-take any warm-boot baseline taken without it (#36); #33 then has no boot tail to skip.
  - **R1/R2** (S17, row 18; S25 addendum 2): unchanged. #18 is SAFE as a default-off test bed; #20 step 1 is SAFE and step 2 SAFE-IF (a)-(e); #19 stays unrated. Both wait for the S4-kickoff GO. S25 correction 7 is fixed (R1/R2 = Agent 7's rows 18-20). Row 23's path is confirmed (base shared_memory.cpp, 15C89EDB -> 0BE4BADC; the draft's L19 is right).
  - **P2 counter** (S25 item 4): Agent 10 rates it once it's staged (after window 4).
  - Nothing UNSAFE. Agent 10 re-sent its lost ~08:28 results to Agents 11, 6 and 9 (~12:45).
- **That send woke Agents 6 and 9, who have no task.**
  - Agent 9 (12:44) agrees with N1-N4. Its N1 fix will require a leading digit, which also covers LEGO_GPU_WAIT_SPIN_US and strtoul overflow. It makes no edits until the landing task after W4b, so its draft hash D176CA8D and its S5.2 line numbers stay as Agents 10 and 11 cite them. It ran a recursive workspace listing by mistake from ~12:42 to 12:43:36, then stopped and went idle. That fits the monitor's 12:43 minute (63.6% total, MsMpEng 0.74 core).
  - Agent 6: no edits on the board. Told it to hold, with no reply and no commands.
- **The quiet monitor was restarted at 12:44 with a Defender-only gate** (my task-130, same log).
  - 12:40-12:44: MsMpEng 0.22-0.74 cores, total 36-64%.
  - A 12:43 process sample: MsMpEng 0.5, PowerShell 0.23 (the sampler itself), System 0.23, Task Manager 0.16, Roblox 0.12, Electron 0.09, agy 0.05 cores.
  - Overnight "quiet" (08:22) was 27-32% total with apps open, so the old total < 25% gate might never trigger, and the user's apps close before W4b anyway. The new gate is 3 consecutive minutes with MsMpEng, OfficeClickToRun and CrossDeviceService each < 0.1 core; total CPU is still logged.
- **Artifact "as of 12:47":** a 12:40 progress row, plus Agent 10's ratings in the busy-wait Leads row and the warm-boot Leads row (output-identical, SAFE, no switch; four warm-boot runs first). Copied (F678727F..., match, 363 lines).
- Open: #2 (Agent 11), #3 (Agent 8). The all-clear for W4b needs Agent 8's readiness report and the monitor's QUIET.

### 12:50 (Agent 1)
- **Agent 8 (12:46): run-2 #3 done. All W4b prerequisites are OK after the restart.** Nothing was launched; bench/agent8 is unchanged (122 files, 1,000,868 B, newest write 06:32:23, identical before and after).
  - LdSys: the SHA256 key b452d258 maps to build\agent8\cache\LdSys-b452d258.dll (32,768 B, 03:19), the DLL the last pre-restart run loaded "(cached)". Nothing compiles at start.
  - LdNvml: the cache matches the nvml.cs ticks (nvml.dll 8.17.16.1088). winhelper, LdDesk and LdPower: OK (csc Framework64 v4.0.30319, System.Drawing, %TEMP%; PlanOnly's LdDesk compile worked). The double-click run uses no hidden desktop.
  - PresentMon/FrameView: not used by the chain (frames come from perf.csv). PresentMon_x64 runs under NVIDIA FvSvc, as before.
  - Python: the Store Python 3.11 alias, not the App Installer stub. C: has 270.8 GB free (a matrix needs ~0.06 GB); free RAM 14.1 GB (gate 6 GB; window 3 had 8.98).
  - Bins, manifests, game\disc and game\tu23 are present. No REX_/LEGO_/PYTHON env vars. AC, 100%, Balanced, effective overlay best_efficiency (as in every pre-restart sys.csv). Screensaver as in window 3 (the runner only warns). No restart pending.
  - `-PlanOnly` with the W4b arguments: exit 0, 17 runs (1 shared cold d0), Latin square d0 B d3 d11t | B d3 d11t d0 | d3 d11t d0 B | d11t d0 B d3, ~39 min. It created nothing: matrix\ still has 19 entries (newest 20261122-0657), so W4b's folder will be the newest.
  - Environment note added in agent8-window3.md L767-779 (83,239 B, 873 lines, 12:45:35). Evidence: build\agent8\readout\w4b-readiness-1237.txt, w4b-readiness2-1242.txt, w4b-planonly-1237.txt.
  - **Correction to my 12:24 entry:** DTT and IPF were extension INFs only. The base drivers (DTT 9.1.10010.2297, IPF 2.3.20306.4) are unchanged. Extension packages carry the OEM's settings, so the comparability caveat stands.
- **Agent 8's notes for before the double-click:**
  - (a) Close RobloxPlayerBeta (started 12:12, not seen before the restart), and ideally Wallpaper Engine and ChatGPT (also new since the 12:06 logon).
  - (b) **Windows Update active hours are 14:00-08:00** (I confirmed HKLM ...\WindowsUpdate\UX\Settings: ActiveHoursStart 14, ActiveHoursEnd 8; no pause set). So Windows may restart on its own between 08:00 and 14:00, which is how 08:29 happened. If W4b starts before 14:00, the user pauses updates first. This also matters for future overnight sessions: their mornings are exposed.
  - (c) Keep all agents idle during W4b. 4.7 of 12 logical CPUs were busy during its checks.
- **My re-hash (12:48):** 31 of 32 W4b files match scratch/w4b-hashes-0551.txt; only bench\agent8\run\matrix-native-threaded.json differs (06:04, not a W4b file). harness/legodimensions.toml B763DABB. So -PlanOnly changed nothing.
- **Quiet monitor:** MsMpEng 0.32 / 0.23 / 0.20 cores at 12:45-12:47; total 36-39%. Not yet under the 0.1 gate.
- **Artifact "as of 12:50":** the IMPORTANT box notes the runner check passed; step 3 adds Wallpaper Engine; a new step 6 says to pause Windows Update before 14:00; the "One thing changed" paragraph now says extension packages, base drivers unchanged; a 12:45 progress row. Copied (A0B7ABAA..., match, 365 lines).
- Open: #2 (Agent 11; S4-DRAFT.md still the 07:58:42 version at 12:47). Before W4b starts, Agent 11 finishes or pauses.

### 13:04 (Agent 1)
- **Pausing Windows Update is blocked.** The shell isn't elevated (BUILTIN\Administrators is deny-only). UI Automation sees no top-level windows from the agent's desktop, so the Settings page I opened at 12:56 can't be driven from here. No restart is pending. Active hours are 14:00-08:00, so the risk of an automatic restart ends at 14:00. The user has been told.
- **The user is away until ~14:50-15:50.** They asked for as much progress as possible and for prompts for Agents 2, 3, 4, 5, 7 and 12.
- **Run-2 tasks issued at 13:04:**
  - **S4a build (A2).** devoff4 and native4 = the S3d line + #7, #8, #5 and #38 (all OFF) + #32 (always on; rated output-identical, b2r §27). native4 also gets #2 (OFF). The build goes into snap trees with apply backups and new bin folders. The live repos stay untouched until the functional checks pass.
  - **Functional checks (A3).** A3 is the only agent who launches the game until 14:20.
  - **Supporting tasks:**
    - A6: #32 run spec and line check.
    - A4: #2 check and the state of s35.
    - A5: M1 staging and the C1 call from u_block.
    - A7: GO to stage #18 and #20 step 1 (staging only), plus a check of the W4b read-out tool.
    - A8: W4b standby and a readiness re-check at 14:30.
    - A9: #24 N1 fix and syntax compile, then #26 and #41 reads.
    - A10: rating queue (S4a apply record, C1 code, P2 counter, #18/#20, N1, M1).
    - A12: u-diag spec, u_block, P2 counter (next build), then C1 v2.
    - A11 continues #2.
- **Hard stops:** builds end at 14:00; last game launch at 14:15; game processes closed by 14:20; notes only from 14:20 to 14:30; nothing from 14:30 until W4b is done.
- **Quiet monitor at 12:53:** total CPU 51%, Defender 0.28 core. Not quiet, which is expected with the agents active.

### 13:17 (Agent 1)
- **Agent 10, ~13:12 (b2r §28, row 29): C1's staged code (#4) is SAFE at the default.** ON is SAFE to test once gate D has the kept-protect counter (C1 v2), so the §24 rating stands.
  - The stage is unchanged since 07:59. chain-live-to-c1.diff reproduces all 6 staged files from the live SDK.
  - Once S4a lands, apply keep-watch.diff on its own (its starting hashes are S4a's output hashes), then keep-watch-rexlego.diff.
  - C1 is not in S4a: it needs a full rebuild, and u_block decides first.
- **#2 done (Agent 11):** S4-DRAFT.md is BC98C02E, 90,004 B, 408 lines, LF, no BOM (13:15:20; checked).
- **Follow-up task issued to Agent 11:** the #38 ON smoke spec for Agent 3's run 4, a check of #38 in the apply record, and S4-DRAFT upkeep until 14:30.
- **13:13:**
  - Agent 6's #32 spec and Agent 12's Agent 3 specs are written.
  - Agent 2 hasn't started compiling yet.
  - Load: total 72-84%, Defender 0.9-2.0 cores.

### 13:29 (Agent 1)
- **The Agent 11 follow-up is board task #14.**
- **S4a applied clean at 13:25** (Agent 2, `build/agent2/s4a-prep-apply.txt`). Agent 2 backed up snap1 to snap1-backup-S4a first, and verify-off is PASS (23,843 files, 0 problems). Each file's before/after hash matches its staging record:

  | Item | File | Before | After |
  |---|---|---|---|
  | #7 | d3d12/shared_memory.cpp | B120D07C | BB0838CE |
  | #8 | graphics/shared_memory.cpp | 15C89EDB | 0BE4BADC |
  | #5 | xmemory.cpp | 6E8FA1BA | 141FB1A9 |
  | #38 | timer_queue.cpp | D8724B29 | 015C04A2 |
  | #32 | pipeline_cache.cpp | 5DBED81F | DA777443 (-2 B, the one rename) |
  | #2 | shaders.cpp (native only) | E87A2DEE | 9567FE3F |

  - The first start stopped at 13:25:16: the run script found its own wrapper shell and took it for a second build driver. Agent 2 fixed this and restarted.
  - SDK build exit 0 (84.8 s), install exit 0 (102.6 s). The game phase started at 13:28:43.
- **Agent 3** made a devoff3 reference run (13:12) and #32's warm-boot run 2 on devoff3 (13:17) while devoff4 builds.
- **W4b pre-flight (quick) at 13:28, all as expected** (`scratch/w4b-preflight.ps1`):
  - bench\agent8 31/32 by name, 122 files, 1,000,868 B, newest 06:32:23. Toml B763DABB.
  - The 5 W4b bins match their MANIFEST sizes.
  - No reboot pending and no WindowsUpdateClient events in 2 h. Active hours 14-8. AC online.
  - Screensaver still WPXSCR at 120 s. ChatGPT, Taskmgr, SystemSettings and wallpaper32 are running.
  - Load: total 83-97%, Defender 1.2-2.5 cores.

### 13:44 (Agent 1)
- **Both S4a bins are ready, and I re-hashed each against its MANIFEST: all files OK.** Agent 2 has stopped building until after W4b.

  | Bin | Ready | MANIFEST | Manifest check (PASS/FAIL/NOTE) | Files |
  |---|---|---|---|---|
  | `build/agent2/devoff4-bin` | ~13:33 | 16DCC939 | 81/0/54 | 7/7 OK |
  | `build/agent2/native4-bin` | 13:38:35 | 00D33D4F | 107/0/38 | 8/8 OK |

  - devoff4: exe 6BE3C713, rexruntime 870276A6, rexgpu-xenos 59662F76. The exe is relinked too: the changed SDK code also links into it.
  - native4: exe 65432C81 (315,811,328 B). Its DLLs are the same as devoff4's. The native fingerprint is 5e3ff55de10f4f64; native3d's was 335ff2d47268f3a1. The #2 miss-cache string check passed.
- **Agent 10, S4a apply record: ALL PASS** (b2r row 30, §29). Every file's before hash matches live and the rated base, and every after hash matches Agent 10's own apply of the rated diff. #32 is exactly L564. Note for C1: memory_watch.cpp is CRLF, so keep CRLF when applying keep-watch-rexlego.diff (target hash 70829846…), or copy the staged new/ file.
- **Agent 10, P2 counter (s4-p2c): output-identical, SAFE, no switch** (b2r row 31, §30).
  - It commutes with Agent 7's s4-r1r2: both apply orders give 027204B5.
  - It goes into the next build only.
  - Before P2 goes ON, someone reads `total` from a next-build run with slow_frame_log_ms set. 0 closes the §22 caveat; anything above 0 comes to me.
- **Agent 6, #32 line check: PASS.** The S4a file differs from live only at L564, and live equals baseline/. Record: `build/agent6/s10-2/linecheck-1331.txt`.
- **Agent 3 runs so far:**
  - devoff3 reference (13:12);
  - #32 run 2 warm on devoff3 (13:17);
  - S4a run 1, devoff4 OFF (13:33-13:37);
  - S4a run 2, u diag ON (started 13:37).

### 13:51 (Agent 1)
- **u_block = 0.9336 (Agent 12, from Agent 3's devoff4 u-diag run, 13:37-13:43, functional PASS).** Source: `build/agent12/s4/uhash-devoff4.txt` and `.json`.
  - Coverage: 75,013 S4 lines with no frames missing. Pages-weighted over 70-220 s (32,787 frames).
  - Spread: p10/p50/p90 per frame are 0.932/0.933/0.934, and every 10 s bucket is 0.9335-0.9337. Only boot differs.
  - u_page is 0.9983. Upload is 3,844 KB/f, all of it re-upload.
  - With P1/C1: 255-407 KB/f re-uploaded instead of 3,844 (89-93% less). Fault cost would be 0.013-0.25 ms/f.
  - Caveats: title-screen idle only, and u is an upper bound (an identical rewrite still faults under P1). The slow state doesn't move it.
- **u_block >= 0.25, so by the standing rule S4b is on after W4b:** the full rebuild with C1 + the C1 v2 counter + #26. Agent 5 makes the formal C1 call. Agents 5 and 10 already have u_block; I relayed it to Agents 11 and 2.
- **Agent 3** is moving about 4 min per run: run 3 (P2 ON) 13:43-13:47, run 4 (precise wait ON) started 13:47:54. Agents 3 and 4 have native4. Agent 2 is on #15 (post-W4b prep, dry runs only).

### 13:55 (Agent 1)
- **The user (13:54): away until 15:30. Keep going; write down anything that needs their decision and carry on.**
- **New schedule.** Being quiet at 14:30 would leave the machine idle for an hour before the user is back, so every stop time moves later. Since 14:00, active hours protect against Windows Update auto-restarts.

  | What | Old | New |
  |---|---|---|
  | Last game launch (Agent 3 only) | 14:15 | 14:45 |
  | Games closed | 14:20 | 14:50 |
  | Builds | until 14:00 | none: Agent 2 is done, nothing builds before W4b |
  | Notes-only window | 14:20-14:30 | 14:50-15:00 |
  | Nothing runs | from 14:30 | from 15:00 until I announce W4b is done |
  | Agent 8 readiness re-check | 14:30-14:40 | 15:05-15:15 |
  | My pre-flight (full) | 14:30-14:50 | 15:10-15:20 |
  | Quiet target | user's return | 15:30 |

  - Defender's load comes from agent activity. After agents stopped this morning it dropped to ~0.1 core.
  - I restart the quiet monitor at 15:00.
- **Added to Agent 3's queue for the extra time (if it fits before 14:45):** a u-diag run on the attract scene, a heavy 3D scene with no Toy Pad tags. It shows whether u_block (0.93 on idle title) holds in 3D. Agent 12 writes the spec and parses the result.
- **S4b before W4b was considered and rejected.** It's a 37-46 min full rebuild, the C1 v2 counter isn't staged yet, and the machine wouldn't be quiet by 15:30. It stays after W4b, on the line the user picks.
- **Decisions for the user** go in the artifact's question list.

## 14:02 Agent 1: #38 smoke PASS, C1 v2 staged, grants, two new tasks

- Agent 11, #38 run 4 (devoff4, `timer_queue_precise_wait=true`, against r1 OFF): PASS. 54/54 steps, exit 0, logdiff NEW/MORE/FLAG all 0. The TimerQueue thread dropped from 37.65% to 1.25% of a core (functional run only, not timed). Verdict in agent11-kernel.md L2042-2061.
- Agent 12: C1 v2 is staged in `build/agent12/s4-c1v2/` (interdiff CE5D9DAE, +43/-3, syntax PASS, both cvars kInitOnly) and went to Agent 10 for rating at ~14:00. The attract u-diag spec went to Agent 3 (devoff4, r2 cvars, attract-long.txt, 420 s).
- Agent 9, task #11 done: N1-N4 draft 01D9F8F3, syntax PASS. #26 is 20 db16cyc sites in 10 TUs, ~4-6 min end to end; the skip stamp ignores the codegen binary. #41: 12 writer sites, so S4-DRAFT §1h is corrected (a9 R2.11).
- Grants (Agent 1). Agent 2 applies these in the S4b snap trees after W4b; nothing goes live before W4b.
  - #24: `rexlego/src/gpu_wait_backoff.cpp` from draft 01D9F8F3, plus the rexlego `CMakeLists.txt` edit. Then the batch-nolr build and the 31-alias map check.
  - #26: the SDK codegen change (`src/codegen/builders/system.cpp`), staged by Agent 9 behind a new codegen option that defaults to OFF.
- New work, all due by 14:50:
  - Agent 9: stage #26 for Agent 10's rating.
  - Agent 5: M1 correctness sweep (functional: one single-file compile, 1 thread, no rate numbers) and a W6 matrix draft.
  - Agent 8: W5 draft in `build/agent8/readout/w5-draft/`; bench/agent8 stays unchanged.
  - Agent 11: told the #26 cost, for S4-DRAFT L217/L308.

## 14:08 Agent 1: Agents 7 and 4 done; adapter settled; two prep tasks

- Agent 7, task #9 done:
  - #18 and #20 step 1 staged in `build/agent7/s4-r1r2/`. Re-staged at 14:01 with Agent 10's dcl.cpp comment nit fixed; check_comment_only.py says only comments changed. Agent 10 has been asked to confirm row 32 against the new hash.
  - The W4b read-out now reports 10 s bins.
- Agent 4, task #16 done: `build/agent4/r2t6/VISUAL-CHECK.md` (the user's on-screen check of the packed native shaders). It needs a native4p build (~2-3 min + 10-15 min prep, ~364 MiB), at the earliest ~35-40 min after W4b. The user decides.
- Adapter (a7 item 11): settled. devoff4 r1 game.log has "DXGI adapter: NVIDIA GeForce MX570 (1934 MB dedicated)" and native4 r5 has "D3D12 ready on 'NVIDIA GeForce MX570'". No wrong-GPU confound.
- New prep tasks, due by 14:50:
  - Agent 7: the S4b functional-run queue for Agent 3.
  - Agent 4: the native re-pin procedure after S4b (fingerprint, shader pack), and whether native4p should wait for S4b.

## 14:13 Agent 1: Agent 10 rated C1 v2, updated M1, confirmed s4-r1r2

- **C1 v2 (b2r row 35, §34):** SAFE at the default; ON is SAFE to test under NOTE's plan.
  - The interdiff is exactly V1-V6, and the diffs re-derive byte for byte. Gate D is met.
  - Landing order: S4a, then keep-watch-v2.diff, then the unchanged rexlego diff (keep CRLF).
  - Caveat (SDK-wide): kInitOnly only takes effect in the overlay. FinalizeInit() has no caller, so the dev console can still flip any kInitOnly cvar at runtime. Test rule: set C1's cvars at launch and never change them mid-run.
  - Agent 12's init latch is needed before default-ON or any landing beyond tests. The S4b test runs don't need it.
- **M1 (row 34, §33 addendum):** the bench's RunCheck already covers the head/tail sweep. Before ON: build the bench and run it without --skip-check; a pass is exit 0 with 0 failures on both check lines. Then the OFF/ON pair. M1 now follows C1.
- **s4-r1r2 re-stage (row 32, §31 addendum):** confirmed. Only the 3 comment lines at dcl.cpp:110-112 changed, and the p2c commute still gives 027204B5. Hash for S4b: s4-r1r2.diff BD0C4A93446149BB (or r1-split 2516F199… + r2-counters 5199910401AD86AC).

## 14:22 Agent 1: M1 gate PASS, W6 and S4b queue drafted, artifact at 14:20

- The artifact is refreshed to the 14:20 state. New sections: "After window 4: what's ready", "This afternoon (12:50-15:30)" and "Decisions for you" (9 items, replacing the old questions).
- Agent 5, task #18 done:
  - **M1 correctness gate: PASS.** Adds `--check-only` to bench/agent5/m1_copybench.cpp (F98B935A…). One BelowNormal clang++ build gave exe 92C5FF6E… (40,960 B).
  - The run at 14:11 used the MX570's WRITE_COMBINE upload heap. Normal memory passed 22/22 groups (154,224 cases), and the upload buffer passed 18/18 (77,168 cases). 0 failures, 0 skipped, rate part not run.
  - Report: build/agent5/s4-m1/copybench-check-20261122-141100.txt. M1 ON now needs only the OFF/ON functional pair (S4b queue rows 19-20).
  - W6 draft in build/agent5/w6-draft/ (matrix-w6.json in window-4 format):
    - Arms s0, p2, p2f, p2fc; placeholder S4b bin.
    - `-Repeats 3 -ColdShared` gives 13 runs, ~33 min.
    - The C1 pair is p2fc − p2f, with fix (i) ON in both arms.
- Agent 7, task #19 done:
  - S4b functional-run queue: build/agent7/s4b-queue/QUEUE.md (0B6D6577…) plus queue-s4b.jsonl (08A95096…) in Agent 3's format. make_queue.py: PASS.
  - 25 runs plus 1 optional, ≈139 min in total (agent runs ≈109 min). Without the conditional rows: 18 agent runs, ≈91 min.
  - Rows 7, 20 and 23 load a level, so they need the user's Toy Pad answer.
  - The ~30 min subset is rows 1, 4, 10, 8, 2, 5.
- Agents 5 and 7 stay idle on purpose, so Defender can settle before W4b.

## 14:28 Agent 1: cron check-in; W5 drafted; C1 v3 staged

- **Board:** 9 open tasks (#5, #8, #10, #12, #13, #14, #15, #17, #20). Nobody is stalled.
  - Agent 10 has been idle since 14:11 because nothing new has arrived to rate.
  - Agent 11 is editing S4-DRAFT. Its check reported "HASH MISMATCH v1-to-v2.diff CE5D9DAE want 06F433B9". The file is unchanged since 13:49:27 and CE5D9DAE is the rated hash (b2r row 35, L1821). 06F433B9 appears in no note, so the expected value in its check is wrong. Told Agent 11.
- **Agent 3:** r5 retry, r6on and r6off are done (verdicts pending). r7 (fix (i) ON) started 14:25:14.
- **Quiet log:** Defender was 1.3-1.6 cores until 14:24, then 0.46 at 14:24:56.
- **Agent 8, W5 draft done** (build/agent8/readout/w5-draft/):
  - S3d line: 16 runs, ~37 min, PlanOnly exit 0. The B line waits for a devoffB4 bin.
  - Arms: s0, d11 (8 timer cvars), d11t (+ REX_TIMER_WAIT_BLOCKING=1), d11p (+ timer_queue_precise_wait=true).
  - The game treats REX_TIMER_WAIT_BLOCKING as on even when it is =0 or empty, so the .cmd files remove it first.
  - Decision (Agent 1): the reference stays `base`; the read-out also reports the timer modes against s0.
- **W4b env check (Agent 1):** REX_TIMER_WAIT_BLOCKING and any LEGO_*/REX_* variable are unset in the Process, User and Machine scopes. run-timing.ps1 L218-225 restores each env value in `finally` right after Start-Process, so d11t's env can't leak into other arms, even though run-matrix calls it in-process.
- **Agent 12 staged C1 v3** (build/agent12/s4-c1v3/; v2-to-v3.diff 1FC8E2DC…, keep-watch-v3.diff DECCFE33…):
  - It adds the init latch Agent 10 asked for: both cvars are latched in Memory::Initialize, and Protect reads the latches, so a dev-console flip has no effect.
  - It also adds the native load-before-exchange nit.
  - OFF and ON behave as v2, with no new log lines. make_c1v3.py and the syntax check: PASS. v2 is unchanged.
  - **Decision (Agent 1):** S4b takes v3 if Agent 10 rates it SAFE before the S4b build starts, otherwise v2. Same position in the apply order and the same rexlego diff (4D0C1079…, keep CRLF). Agent 7's queue is unaffected (same cvars).
  - Agent 10 rates v3 next; Agent 2's S4b apply order takes either version; Agent 11's S4-DRAFT upkeep is extended to 14:50.
- **Agent 12, task #13 done.** The attract u_block (Agent 3's 14:06 run, H0..+150 s) is **0.9682**:
  - p10/p50/p90 0.938/0.988/0.997; u_page 0.9705; 4,055 KB/frame.
  - Before the slow state (H0..+41 s) it is 0.9772.
  - That is higher than the title's 0.9336, so C1's A/B (W6) is still GO. C1 v3 has gone to Agent 10 to rate.

## 14:30 Agent 1: Agent 2's post-W4b prep done (task #15)

Details are in agent2-baseline.md, section "Task #15", L370-545.

**1. apply-s4a-live.ps1 (S4a into the live repos)**
- Dry run: 6/6 PASS.
- `-Go` refuses if any game, ninja, clang, lld or cmake process is running. It backs up the 6 live files and rolls back on any error.

**2. B line + S4a (devoffB4 + nativeB4)**
- About 7-9 min and ~0.55 GiB with option B. There is no SDK build, because both trees link snap1-sdk/install, which is the S4a SDK.
- Build B4 before the S4b SDK lands in snap1-sdk, or clone snap1-sdk first.
- B4 can be skipped if S4b on B follows at once.

**3. Deletable list (nothing deleted)**
- About 1.74 GiB can go in any case.
- About 6.8-7.4 GiB if S3d wins, or about 3.3-4.1 GiB if B wins.
- Free disk is about 265 GiB, so nothing is urgent.

**4. S4b apply order and composition**
- Order: C1 → M1 → P2c → r1r2 (either order) → #24 + #30 (one native re-pin with C1) → #26 regen last.
- `s4b-compose-check.py`: 0 FAIL. command_processor.cpp comes out at 027204B5, which matches Agent 10's composite.
- memory_watch.cpp lands as a copy of the staged after-file 70829846, after checking that live is 19AE1606. Applying the LF diff to the CRLF file fails, as Agent 10 said.

**5. Build time and bin names**
- S4b takes about 37-46 min plus ~5 min on the S3d line, and about 48-51 min on the B line. Bundling #26 adds 3-4 min.
- Bin names: devoff4b, native4b, devoff4b-ctr (#20 counters: rexgpu-xenos.dll only) and devoff4b-cg26. The B line uses devoffB4b and so on.

## 14:31 Agent 1: #26 staged (Agent 9, task #17 done)

Notes: agent9-codegen.md R2.17, L2070-2191.

**The staged change** (`build/agent9/s4/spin/db16cyc-pause/`)
- `db16cyc-pause.diff` AC554DBB… adds 7 lines net to config.h, config.cpp and builders/system.cpp. Apply it with -p1 from the SDK root.
- Base is c5fe668, and the three files are identical in live and in S4a snap1.
- The new option is `db16cyc_pause` (a TOML root key), default OFF.
- With it OFF, the generated code is byte-identical and the codegen fingerprint doesn't change.

**Where the switch goes (Agent 9's correction)**
- Codegen reads `rexlego/legodimensions_config.toml` through the manifest. It never reads harness/legodimensions.toml (B763DABB, runtime only, untouched).
- So the one-line switch is staged per line: `toml-db16cyc-pause-A.diff` 95D901B9… (S3d/snap1) and `toml-db16cyc-pause-B.diff` 5D5892D3… (batch-nolr/snapB).
- The line must land together with the new tool, because an old tool silently ignores the key.

**Checks and prediction**
- The syntax check passes, and a negative control (without the new header) fails as expected.
- With the switch ON, each of the 20 sites gains one `simde_mm_pause();` line, in 10 TUs.
  - A TUs: 107, 116, 125, 153, 169, 205, 284, 304, 321, 432.
  - B TUs: 107, 162, 265, 281, 329, 354, 378, 383, 389, 394.
- Keep codegen.partition.json, or every TU gets renumbered. After the regen, check that `simde_mm_pause` appears 20 times.
- Cost: about 3 min plus the codegen-tool rebuild.

**Status**
- Agent 10 has had it since ~14:22; the rating is pending.
- #41: the two function pointers live in data (a vtable or callback table). Finding what installs them needs an image reader, which the tree doesn't have, so this is open for after W4b.

## 14:39 Agent 1: C1 v3 and #26 rated SAFE; Agent 10's queue done (task #12)

- **Agent 2 (14:32):** S4b's C1 step is now one variable, `S4B_C1=v2|v3` (driver `-C1`; v2 if unset). `s4b-compose-check.py --c1 both` gave 0 FAIL (s4b-compose-1432-c1both.txt, 61CC9FBF). command_processor.cpp still ends at 027204B5. xmemory.cpp ends at DC23757A (v2) or BCA5E1CF (v3), and the other 9 files are the same either way.
- **C1 v3 (Agent 10, b2r row 36, §35): SAFE at the default; ON is SAFE to test.**
  - All applies re-derived at offsets 0, and syntax is PASS.
  - The latch is stored after cvar::Init and both LoadConfig calls, before any heap exists. The only REXCVAR_GETs left for these cvars are the two in Initialize.
  - Agent 10's §34 condition (an init latch before landing) is met.
  - **Decision (Agent 1): S4b uses C1 v3 (`-C1 v3`, keep-watch-v3.diff DECCFE3373C27C3C), then the unchanged rexlego diff 4D0C1079… (keep CRLF).**
- **#26 (b2r row 37, §36): landing OFF is SAFE; ON is output-identical and SAFE to test.**
  - All 3 diffs re-apply exactly, and Agent 10's census matches the 20 sites in 10 TUs for both arms.
  - sub_83FAF180's watchdog runs on a loaded clock, so PAUSE doesn't stretch it.
  - Gates before ON:
    1. the toml line and the new tool land in one build (otherwise force one regen);
    2. exactly 20 pauses after the regen;
    3. keep codegen.partition.json;
    4. the functional pair, then a frame-time A/B measured apart from #24.
  - If the A/B shows added latency, one PAUSE per db16cyc run is the fallback.
- **Agent 10, task #12 done:** all 9 ratings (b2r rows 29-37) plus a side fix (§27, for Agent 6). Nothing was rated UNSAFE. Agent 10 is idle until W4b is done.
- **Open tasks (5):** #5 (Agent 3), #8 (Agent 6), #10 (Agent 8), #14 (Agent 11), #20 (Agent 4).

## 14:41 Agent 1: #2 smoke PASS; native re-pin procedure ready (Agent 4, task #20 done)

- **#2 miss-cache smoke (Agent 3's r6 ON/OFF pair on native4): PASS (Agent 4).**
  - Check C3 fails only because the checker matches shaders by guest address. The 8 OFF-only and 8 ON-only keys are heap addresses, and they pair one to one by stage, rows per frame and time window.
  - Their fixed-address partners are in both arms. C2 is the same, logdiff NEW 0 / MORE 0, and the warning types are equal.
  - PS 0xABB69980's 8 re-inserts are real look-ups, the opposite of a stale replay. No OFF-vs-OFF run is needed.
  - Note for W8a: the 64-row cap fills at ~150 s, and heap shaders churn, so the cache gains little on those.
  - Agent 4 can fix C3 to match heap keys after W4b if wanted.
- **Agent 4, task #20 done: build/agent4/repin/REPIN.md, repin_check.ps1 and 2 draft matrices.**
  - repin_check.ps1 does a dry run by default. `-Go` needs `-W4bDone`.
  - The matrices: native5 identity + n-row baseline (4 runs, ~15 min), and the traced pack-hit pair (2 runs, ~12 min).
  - Dry runs on snap1 and snapB3: 0 FAIL, 1 WARN (#24's CMake edit isn't staged yet). The fingerprint recompute matches.
  - Path to the native pin: pre-check → S4b apply → CMake + full rebuild → pin record → Agent 3's checks, ~65-80 min in total. The B line adds ~35 min.
  - **Agent 4's recommended order:** build native4p right after W4b, so the user can do the on-screen check ~35-40 min after W4b. Then roll back (~1 min), then S4b → native5 (pin) → native5p (no second look). Pin native5p only with the user's yes and a passing pack-hit.
  - **Finding:** copied files keep their old timestamps, so without a touch the fingerprint and index steps miss them. apply-s4a-live.ps1 already sets mtime = now. Asked Agent 2 to make sure the S4b driver and B4's snapB copies touch too.
- Open tasks (4): #5 (Agent 3), #8 (Agent 6), #10 (Agent 8), #14 (Agent 11).
- 14:40: Agent 3 is in the #32 S10.2 runs: r4-t0 on devoff3 and devoff4, r3-boot ×3, r2-warm. Another r3-boot (F3c) launched at 14:40:24. Defender is at 1.6-1.7 cores while the games launch.

## 14:44 Agent 1: S4-DRAFT current (Agent 11, task #14 done)

- S4-DRAFT.md is C8B4CBCA (450 lines, 118,185 B; written 14:42:29). It was BC98C02E (408 lines).
- My checks find all of these in it: C1 v3 (S4b's C1), db16cyc_pause and the codegen config toml (`rexlego/legodimensions_config.toml`), M1's bench gate PASS, the attract u_block 0.968, the W5 and W6 drafts, the S4b run queue, and #38 PASS.
- The done report lists only AGENT3-SPEC.md, but the draft itself shows every item from my 14:28-14:39 messages.
- Open tasks (3): #5 (Agent 3), #8 (Agent 6, waiting for the S10.2 run folders) and #10 (Agent 8, W4b standby).

## 15:34 Agent 1: timed windows need the user's double-click; S4a landed and committed; heavy work held until 16:00

- **14:44 user instruction:**
  - Run the timing windows unattended from now on, W4b included. Start each as soon as the quiet and readiness checks pass, and run the rest of the plan in any order.
  - Allowed: set the screensaver to None; close ChatGPT, Copilot, Roblox, Task Manager and Wallpaper Engine. Never close agy-grid, T3 Code or anything else.
  - Every timed run must end before 07:30 tomorrow, or hold.
- **Blocked: no agent can start a valid timed window.**
  - Every command, mine and the agents', runs on its own hidden desktop in session 1, a new one per command: `WinSta0\exebox-TYPSN53W…` at 14:45, `WinSta0\exebox-5HCCNW4C…` at 14:51. Explorer is on `WinSta0\Default`.
  - This is agy's terminal sandbox. The agy-grid README (L313) says the Purdue policy only runs commands unprompted inside it. My token is medium integrity, not an AppContainer.
  - A game started there is never presented, so its frame times are invalid (finding 7).
  - Starting the game on the user's desktop from here (Task Scheduler /IT, CreateProcess lpDesktop, an explorer hand-off) would bypass the sandbox, so I won't.
- **Sanctioned routes, offered to the user:**
  - (a) Double-click `bench\agent8\RUN-WINDOW4B.cmd` now, while the machine is ready and quiet. Later, use Agent 8's launcher `bench\agent8-launch\RUN-W4B-THEN-W5.cmd`, which waits for quiet and readiness by itself, then runs W4b and W5.
  - (b) Optional and untested: a narrow `unsandboxed(<launcher command>)` allow rule in agy-grid's `agy-allow.json`. That is agy's documented route for enterprise accounts, and agy may need a restart to pick it up.
- **14:55 #32 gate: PASS on every run** (Agent 6, a6 §10.2.1).
  - Run 2's logdiff (F2 vs U2): NEW 0, MORE 0, marker flags 0. The 33 GONE lines are info-level Toypad packet lines.
  - Agent 10: all four §27 runs are met.
- **Agent 3, task #5 done.** All S4a functional runs on devoff4 and native4 exit 0 with no dumps. Runs 1-8, the attract u-diag run and r3n pass.
- **14:56 S4a landed live** with `build/agent2/apply-s4a-live.ps1`.
  - The dry run gave 6/6 PASS. `-Go` wrote 6 files, each == after.
  - Backups: `build/agent2/live-backup-S4a-20261122-145608`.
- **Commits, pushed to mine:**
  - SDK `3bb65bb` (c5fe668..3bb65bb, 5 files).
  - Game `1bd322e` (08933a7..1bd322e: shaders.cpp + SDK pointer).
  - simde and plume left out.
- **15:04:56 QUIET:** Defender, Office and CrossDevice each < 0.1 core for 3 one-minute averages (task-130).
- **Agent 8, task #10 done: the W4b readiness re-check at 15:05-15:07 is READY.**
  - Hashes: 0 changed, closure 53/53.
  - RAM 13.6 GB free, disk 263 GB free, no build tools running, no pending restart.
  - Background CPU is 25-31% with no agent work; Windows Search indexing takes about 1 logical CPU.
  - The W5 draft is in `build/agent8/readout/w5-draft/`.
- **Lost ~30 min:** one of my file reads hung from 15:01 to 15:31.
- **The 15:00 stop is replaced (task-314 killed).**
  - Heavy work is held until 16:00, so the user can start W4b at once if back. Only light tasks run until then.
  - At 16:00, unless W4b has started: Agent 2 builds B4, then S4b with C1 v3.
  - A watcher on `build/agent8/matrix` and the launcher's status folder tells me when a window starts; I then stop the agents.
- **Held until a window starts:** the screensaver change and the app closures. W4b's .cmd asks the user to set the screensaver to None.
- The PC is on AC, with sleep and display-off both set to never.

## 16:35 Agent 1: W4b done (the user's double-click, 15:41-16:17): every arm within noise; d11t saves ~15 % CPU

- **Ran:** `build/agent8/matrix/20261122-1541`, WinSta0\Default, screensaver none, AC, 17/17 OK (1 shared cold run + 4 Latin-square rounds). Preflight clean: no builds, no game, 13.8 GB free.
- **Result** (title screen, uncapped; median of run medians; ref d0 = devoff2; noise band ±19.6 % = d0's run spread):

| arm | median ms (min..max) | Δ median | p99 ms | fps | CPU cores |
|---|---|---|---|---|---|
| d0 devoff2 | 3.40 (3.07..3.73) | ref | 10.73 | 239.7 | 3.44 |
| B devoffB | 3.23 (2.88..3.53); 3.03 without run 6 | −4.9 %; −10.8 % without run 6 | 10.50 | 255.1 | 3.35 |
| d3 devoff3 | 3.21 (2.89..4.26) | −5.4 % | 10.49 | 248.9 | 3.38 |
| d11t devoff2 + timer bundle + blocking wait | 3.36 (3.02..3.86) | −1.1 % | 10.94 | 237.7 | 2.91 (−15 %) |

- **Verdicts (before the read-out):** no frame-time change clears the noise band. d11t holds frame time with ~0.5 core less CPU.
- **Invalid run:** run 6 (`1551-B-r2`) has valid_timing=False: 3 clang++ processes in its warm-up and window, most likely Agent 9's #22 syntax checks (~15:51-15:53). The runner still counts it in B (build_procs is an info flag), hence summary.md's FUNCTIONAL ONLY banner. The read-out recomputes without it.
- **Agent activity during the window.** I was stuck 15:36-16:21 in a read_file of agy-grid/README.md (outside the workspace; it waits on an approval prompt) and missed the 15:41 start. Agents 2 and 11 noticed it and stopped on their own.
  - Agent 2: prep-b4.py dry run 15:46:11-22 (one thread, hashing; run 3 `1545-B-r1`, B's best run at 2.88 ms); shell checks 15:47:17-19 and 15:47:40-44 (run 4's warm-up).
  - Agent 11: short Python reads and one S4-DRAFT write 15:48-15:55 (runs 4-7); listings and Get-Process 16:01:54-16:02:36 (run 10 `1600-d3-r3`'s window: the slowest run, 4.26 ms, light share 0.51).
  - Agents 9 and 10: #22 staging/syntax and #24 re-derivations; times to be checked.
  - The read-out checks each window's sys.csv for non-game CPU before any verdict.
- **Fixes:** never read_file or write_file outside the workspace (two hangs today, 15:01-15:31 and 15:36-16:21); use run_command. A watcher (`build/agent1/hold/hold-manager.ps1`, until 07:30) now writes `perf-notes/WINDOW-HOLD.txt` when a matrix folder appears and deletes it when summary.md lands, and every task says to run nothing while it exists. The 30-min cron (task-99) had ended after 8 iterations; re-armed.
- **Next:** read-out (Agent 8, with Agents 7 and 6); W5 on the S3d line (B's gain isn't significant and the S3d line needs no build; B4 deferred); S4b on the S3d line with C1 v3 and S4c folded in, so the native re-pin happens once.

## 16:46 Agent 1: W5 promoted (S3d line); it waits for the user's double-click

- **Promoted Agent 8's draft myself** (Agent 8 had stopped on an error), following its README's "Promoting it" steps 1, 2 and 4. Only the JSON title and first note and the .cmd's header comment and missing-file message changed (ASCII, CRLF kept).
  - `bench/agent8/RUN-WINDOW5-S3D.cmd` 5467F1BE…; `bench/agent8/run/matrix-window5-s3d.json` 4D7D689B….
  - `-PlanOnly` exit 0: 1 cold run + 3 rotated rounds (base, s0, d11, d11t, d11p), 16 runs, ~37 min. `build/agent8/matrix` had 20 folders before and after.
  - Inputs frozen in `build/agent1/w5/W5-INPUTS-1642.txt` (27 entries): devoff3 MANIFEST B9C5175D…, rexruntime D1D66AC3…; devoff4 MANIFEST 16DCC939…, rexruntime 870276A6…; harness toml B763DABB….
- **Desktop:** the screensaver is already None (ScreenSaveActive 0), and the PC is on AC at 100 %. Task Manager runs elevated, so closing it failed (access denied); I asked the user to close it.
- **Watchers:** the HOLD manager has run since 16:40 (task-599, 20 folders known), and task-620 wakes me when W5 starts.
- **Agents stay idle until W5 ends.** If it hasn't started by 17:10, the S4b build goes first and W5 moves to the overnight launcher (Agent 5).

## 17:07 Agent 1: pause for the agy-grid relaunch (user's request), before W5

- **Pause point: now, before W5.**
  - Nothing is running: no window (no HOLD or GO file; `build/agent8/matrix` still has 20 folders), no build and no game. Agents are on tasks #25-#35 with file tools only.
  - Relaunching after W5 would hold the agents and the S4b build for another ~40 min.
  - A relaunch during W5 would disturb its timing.
- **The 17:10 'go' timer (task-627) is cancelled,** so the build can't start during the relaunch.
- **Agents:** told to finish their current edit, end their turns and wait for a resume.
- **Resume checklist:** `build/agent1/RESUME-after-relaunch.md` (hold manager, watcher, cron, agent resumes, then W5 or 'go').

## 17:36 Agent 1: resumed after the agy-grid relaunch; W5 quiet check running; decision 1 (Toy Pad tags) = yes

- **Relaunch state (17:27):** board reset to run 2 (0 tasks, 0 claims); the 11 workers are fresh conversations. No HOLD or GO file; `build/agent8/matrix` still has 20 folders; no build or game running.
- **Restarted (RESUME checklist steps 1-3):** the HOLD manager (`build/agent1/hold/hold-manager.ps1`, task-16, started 17:29:13, 20 folders known; it was not running after the relaunch); the HOLD-present watcher (task-57); the 30-min cron (task-58, 28 iterations, until ~07:30).
- **W5 inputs re-hashed at 17:31** (`build/agent1/w5/W5-INPUTS-1731.txt`): 27/27 identical to W5-INPUTS-1642.txt.
- **Quiet check re-made** as `build/agent1/w5/quiet-check.ps1` (the 15:04 one was an inline task of the old conversation): Process perf counters, 1-min averages; QUIET = Defender, Office and CrossDevice each < 0.1 core for 3 consecutive minutes and no game/build process. Log: `build/agent1/w5/quiet-1731.log`. First minutes: Defender 1.14, 0.89, 0.94 cores (part of it is my own resume reads: the 2 x 170 MB exe hashes and the old-transcript greps); Discord ~1 core (not in the gate, not on the close list).
- **The user is present for W5** (17:27): they close Task Manager and double-click `bench/agent8/RUN-WINDOW5-S3D.cmd` when I say the machine is quiet.
- **Decision 1 (Toy Pad tags): yes** (user, 17:27). Agent 3 may use generated virtual Toy Pad tags (Batman, Gandalf, Wyldstyle) in its hidden-desktop test runs, under the 02:11 harness-only rules (user-mode only, no drivers or system-wide installs, never in a staged `build/agent2/*-bin`, saves isolated in the run folder, builds at <= 2 threads). S4b queue rows 7, 20 and 23 (level loads) are no longer skipped, and C1 ON's verify-mode level load (b2r §21 A) can run. Agent 11 records it in S4-DRAFT §4a and FINDINGS Q1.
- **Agent resumes (step 4), one change:** the old tasks #25-#35 are re-issued as run-2 tasks with the same text, but with **no tool calls at all until 'go'** instead of "file tools only". Reason: the workers are fresh, so their first work would be a burst of reads (it also keeps Defender busy) right as W5 starts, and they can't see the HOLD file without a tool call. Old to new mapping goes in the next entry once the board numbers them.

## 17:41 Agent 1: run-2 task numbers; W5 quiet gate still failing on Defender

- **Run-2 tasks (assigned 17:38, all held with no tool calls until 'go'):** #1 Agent 2 (old #28, S4b + S4c build), #2 Agent 3 (old #29, S4b functional queue, Toy Pad rows now in), #3 Agent 4 (old #25, mc_smoke_check C3), #4 Agent 5 (old #27, overnight launcher, target ~19:30), #5 Agent 6 (old #31, W4b logdiff), #6 Agent 7 (old #30, noise method), #7 Agent 8 (old #26, W4b/W5 read-outs, W6 promotion), #8 Agent 9 (old #33, Android report), #9 Agent 10 (old #34, compose-check rating, launcher safety read), #10 Agent 11 (old #35, S4-DRAFT + FINDINGS decision 1, 3-mode script, launcher review), #11 Agent 12 (old #32, P2 counter script, W6 gates). 24 subagents granted.
- **Quiet check, 10 one-minute samples (17:32-17:40): all FAIL on Defender** (0.77-1.14 cores; Office 0, CrossDevice 0.02-0.03). Busy 4.7-6.4 of 12 logical CPUs: Discord 0.9-1.35 cores, the agents' acks (agy 0.44-0.90 at 17:38-17:39), DWM ~0.3. No Defender scan is scheduled (last quick scan 08:53-09:11), and MsMpEng read 0 MB from disk in 5 s, so it is real-time work, not a file scan. The check ends at 17:52; asked the user whether to wait, start anyway, or move W5 overnight.

## 17:52 Agent 1: quiet gate NOT QUIET after 20 min; W5 starts anyway (user's option 1 with its 17:52 fallback)

- **Quiet check (`build/agent1/w5/quiet-1731.log`):** 20 one-minute samples, 17:32-17:51, all FAIL on Defender alone: MsMpEng 0.76-1.14 cores (0.88-0.99 over the last 10 min). Office ~0, CrossDevice 0.02-0.04, Search < 0.03.
- **Total busy CPU fell from 4.3-6.4 to 2.8 of 12** after Discord went idle at ~17:46 (the user quit or idled it; 6 Discord processes remain, ~0.1 core). W4b's background before its start was 3-3.7 cores (Agent 8, 15:05).
- **Readiness (17:52):** no HOLD or GO file; 20 matrix folders; no game or build process; Task Manager, ChatGPT, Copilot, Roblox and Wallpaper Engine not running; 15.2 GB RAM free, 253 GB free on C:; on AC; screensaver off (ScreenSaveActive 0). W5 inputs re-hashed at 17:31: identical to 16:42, and nothing has run since.
- **Caveat for the W5 read-out (Agent 8):** Defender was steady at ~0.9 core when the window started (real-time work, no scan, no disk reads). The arms rotate within rounds, so a steady load hits all of them; the read-out checks each run's sys.csv for MsMpEng and other non-game CPU before any verdict.
- Told the user to double-click `bench/agent8/RUN-WINDOW5-S3D.cmd`. The HOLD-present watcher (task-57) is running; the agents are held with no tool calls until 'go'.

## 18:34 Agent 1: W5 done at 18:29 (all S4a timer arms within noise; d11t/d11p use ~13 % less game CPU); HOLD cleared; paused until the user says start

- **W5:** `build/agent8/matrix/20261122-1756`, 17:56-18:29, 16/16 runs OK, 15 scored, 0 excluding flags (every run has only the info flag light_share_high), no frames over 33 ms. The formal read-out is still Agent 8's (run-2 task #7), after 'go'.

| arm | median ms (min..max) | d median | p99 ms | game CPU cores | summary verdict |
|---|---|---|---|---|---|
| base (devoff3, S3d) | 2.55 (2.41..2.93) | ref | 7.49 | 3.17 | ref; noise band +-20.4 % |
| s0 (devoff4, S4a) | 2.69 (2.52..2.76) | +5.5 % | 7.58 | 3.22 | within noise |
| d11 | 2.61 (2.56..2.62) | +2.6 % | 7.45 | 3.17 | within noise |
| d11t | 2.65 (2.55..3.03) | +4.0 % | 7.84 | 2.74 | within noise |
| d11p | 2.62 (2.58..2.64) | +3.1 % | 7.72 | 2.75 | within noise |

- **CPU:** d11t and d11p use ~0.4 core less game CPU than base, s0 and d11 (2.67-2.84 vs 2.90-3.46 cores per run, about -13 %) at about the same frame time. It holds in all 3 rounds, so it looks like a real effect of those two modes; the read-out should confirm it from proc.csv and threads.csv.
- **Environment per run (my quick look at each run's sys.json window, not a verdict):**
  - No input on this PC during any window (input_events 0; user idle grew from 74 s to 1974 s); the game was in the foreground 100 % of the time; AC, scheme Balanced, and **power overlay best_efficiency** in every run. The overlay isn't mentioned anywhere else in perf-notes. It's the same for all arms, so the A/B is fair, but it caps absolute speed.
  - The CPU is a 15 W i7-1255U (2P + 8E, 12 threads). P-core clocks were flat at 1.92-1.95 GHz in every scored run (power-limited), so clock dips don't separate the arms.
  - Non-game load was steady at ~3.0-3.6 logical CPUs per run (P/E util x threads minus game cores; this includes Defender's ~0.9 and the samplers). The cold run had ~6.
  - The three slowest runs (base-r2 2.931 at 18:17, d11t-r3 3.028 at 18:21, s0-r2 2.764 at 18:08) are the three with the P threads nearly saturated (P util 91-98.5 %) and the lowest E-core clocks (551-597 MHz). The fastest run, base-r1 at 2.411, came right after the cold run, while the E-cores were still at 1174 MHz. So the outliers look like scheduler/power-state noise, and base's 2.55 median gets help from its early run; the S4a arms' +3-5 % sits inside that noise.
  - My own activity during the window: the 18:10 cron turn and a reply at 18:21-18:22 (no commands). d11t-r3's non-game load (3.41) is inside the other runs' range.
- **HOLD cleared by hand (18:31):** I deleted `perf-notes/WINDOW-HOLD.txt` (set at 17:56:03 with the wrong folder name "matrix/6") after summary.md appeared, and stopped the old HOLD manager (task-16).
  - **Bug:** `($new | Sort-Object)[-1]` on a single new folder returns the last character of its name, so the manager watched "6" and would never have cleared the HOLD. A second, latent bug: the stale check read only the folder's top level (no -Recurse), so it could have cleared the HOLD mid-run. Both are fixed in `build/agent1/hold/hold-manager.ps1` (lines 19 and 26). The fixed version starts at the restart.
- **The W5 console** (`RUN-WINDOW5-S3D.cmd`) is waiting at `pause` on the user's desktop; it can be closed.
- **Paused (user, 18:21): nothing started after W5.** No 'go', no HOLD manager, no cron (task-58 cancelled at 18:22). The agents stay held on run-2 tasks #1-#11 with no tool calls until 'go'. Restart checklist: `build/agent1/RESUME-after-pause.md`.

## 19:31 Agent 1: restart after the pause (user back at 19:28, sleeps at 00:00); 'go' sent

- **Restart (`build/agent1/RESUME-after-pause.md`):** the fixed HOLD manager runs as task-135 (19:29:07, "start: 21 matrix folders; HOLD file present: False"). The 30-min cron is re-armed (25 iterations, until 07:30). No HOLD or GO file, no build or game running, and the W5 console is closed.
- **'go' to all agents at 19:31** on run-2 tasks #1-#11, with W5's end (18:29) and the HOLD rule (check it before every command; no tool calls while it exists).
- **The user sleeps at 00:00.** Targets:
  - Agent 2's S4b + S4c bins ~20:30, then Agent 3's S4b functional queue (Toy Pad rows included) to ~22:50.
  - Agent 5's launcher ready for review by 21:30 and reviewed by Agents 10 and 11 by ~22:30.
  - The user double-clicks `bench/agent5/launch/RUN-NIGHT.cmd` at ~23:45 and leaves the PC.
  - W6's GO only after Agent 3's queue passes and Agent 8 promotes W6.
  - Every timed run starts by 06:45 and ends before 07:30.
- **Agent 8** runs the W5 read-out now (inputs: SESSION2 17:52 and 18:34).

## 19:35 Agent 1: S4b is a full rebuild; Agent 2's build cap raised from -j2 to -j8 (Below Normal)

- **Agent 2 (19:34):** C1's xmemory.h reaches all 440 generated TUs in each game tree, plus 199 SDK TUs. The ninja-log work sums are ~1.7k CPU-s for the SDK, 7.7k for the OFF game and 11.1k for native. Agent 2's estimates for when each bin is staged:
  - -j2: devoff4b ~21:00-21:30, native4b ~22:00-23:00.
  - -j4: devoff4b ~20:40, native4b ~21:35.
  - -j10 (the old cap): devoff4b ~20:20, native4b ~20:45.
  - CTR adds ~10 min after native4b; CG26 comes last.
- **Decision: -j8 at Below Normal.** My 19:31 'go' said "<= 2 threads", copied from the 02:11 harness-only rules for Agent 3; Agent 2's old cap was -j10.
  - No timed window can start before 00:00 (the launcher's gate also refuses while clang/ninja run).
  - -j8 leaves time for one fix-and-rebuild cycle before W6, and leaves ~4 threads for the user, Agent 3's hidden-desktop functional runs and Defender.
  - Guards: devoff4b is staged first, so Agent 3 can start; keep >= 4 GB of RAM available (otherwise restart ninja at -j6). The user can ask for -j4 if the PC gets in their way.
- **Expected:** devoff4b ~20:25-20:30 and native4b ~21:00, then CTR, then CG26. Agent 3's S4b queue runs to ~22:50-23:00, so W6 is still on for after 00:00.

## 19:42 Agent 1: Agent 4's run-2 task #3 done (mc_smoke_check v2, C3 fix); Agent 4 next: the native re-pin on native4b

- **mc_smoke_check.py v2** is `build/agent4/r2t6/mc_smoke_check.py`, EB13FA96…D183 (21,483 B). I checked the sha; the code is unchanged since 15:48.
  - C3 now pairs heap-address shader keys one to one, by stage, rows per frame (within 10 %) and first/last row time (within 10 s, after the median start offset).
  - The fixed addresses (VS 0xAC449538, PS 0xAC448F28, any `--fixed`) match only exactly.
- **Tests:**
  - Self-test 15/15.
  - Agent 3's r6 ON/OFF pair: PASS (91 exact keys, 8 heap pairs, 0 unmatched; C1 PASS, C2 SAME; C4 OFF 0 rows / ON 64 rows).
  - 0452-n0-r1 against itself: still PASS.
  - `--c3-rpf-tol 0.001` makes r6 FAIL, as it should.
- **Side fix:** `recheck/sectdiff.py` now reads UTF-16 logs. The tip is passed to Agent 3: save checker output with `--out` (UTF-8), not `>`.
- **Agent 4's next task:** the native re-pin, once, on native4b. It adapts REPIN.md and its two draft matrices to tonight's bins: native5 → native4b, C1 v3, and #24 in through S4c; the B line and the pack bin are not tonight. It runs dry-run checks after Agent 2's CMake re-run and on the staged native4b-bin, then hands the boot check and the identity/n-row matrix to Agent 3's queue. No `-Go` without my word; I announce the pin after Agent 3's checks.

## 19:47 Agent 1: Agent 10 rates the folded S4b + S4c compose check PASS, SAFE to build (landing OFF); Agent 3 explores the level route

- **The file:** `build/agent2/s4b-compose-1932-c1v3.txt` 77F0017A… (`--c1 v3`, S4c 24-30); see b2r row 39 and §38.
  - Three independent applies give the same 16 files (13 SDK, 3 game): Agent 2's git apply (o1 and o2), Agent 10's strict Python applier, and GNU patch 2.8.1 (a subagent).
  - Each file equals its rated step's `new/` file. cp.cpp is 027204B5… in either P2c/r1r2 order. No fuzz.
- **Gates for the build (relayed to Agent 2):**
  1. Land exactly the 16 files and check them by hash, not by exit code.
     - memory_watch.cpp must be 70829846… with CRLF: copy the staged file, because GNU patch without --binary writes it all-LF (18DE0334…).
     - The TU is 01D9F8F3… or 34D281E0…; the record says which.
     - The toml stays 7F775847… (#26 OFF).
  2. A full SDK rebuild plus a codegen-tool rebuild. The regen is skipped because there is no toml line.
  3. The folded devoff map is devoff4's 27 hooked aliases plus exactly sub_83FBF7D0, sub_83FAF180, sub_83FB09E8 and sub_83FC0C10 (31), checked by name and object. skip_lr stays off.
  4. One native re-pin on native4b (Agent 4, task #12).
  5. snap1 equals S4a plus exactly these 16 files, and the W5 bins (devoff3, devoff4) re-hash unchanged.
- **Note:** r1r2's cp.cpp hunk 3 has an old side that occurs 3 times (IssueDraw :3082, EndSubmission :4318, UpdateBindings :5569). The tools pick the nearest one, which is correct; a hand apply must go by line number.
- **19:43, Agent 3:** it may do 1-3 route-exploration runs for rows 7, 20 and 23 on devoff4-bin before the S4b bins land. Hidden desktop, functional only, one game at a time, virtual tags under decision 1, <= 15 min each, only with >= 6 GB of RAM free; it stops when devoff4b is staged. Nobody has driven the game past the Toy Pad front-end screen yet.

## 19:49 Agent 1: Agent 6's run-2 task #5 done (the W4b logdiff is clean); Agent 6 next: the W5 logdiff

- **W4b** (`build/agent8/matrix/20261122-1541`), every arm against the 4 warm d0 runs:
  - B, d3 and d11t have 0 gate FAIL findings, 0 NEW, 0 MORE and 0 GONE. All 17 runs exit 0, with no dumps, WER or STUCK.
  - The only d11t-only line is the required "Host timer resolution set to 1 ms (background opt-out on)", in 4/4 runs.
  - d3-r3 has one benign handle-value difference (0xf8000164 vs 0xf8000160). The Toypad 8-vs-10 line counts come from harness timing, not from an arm.
- **Checks:** a re-run with the cold run in the base gives the same result. Two read-only checker subagents confirmed every arm (48 more pairwise gate runs plus their own exact-text diffs).
- **Where:** output in `build/agent6/w4b/out-20261122-1541/`; notes in agent6-attract-stalls.md §12. The per-arm findings went to Agent 8.
- **Next for Agent 6:** the same logdiff on W5 (`20261122-1756`) for Agent 8's read-out:
  - s0 against d11, d11t and d11p (same bin);
  - base against s0 (devoff3 vs devoff4);
  - the cold base run against the warm ones;
  - a look at the logs of the three slow runs.

### 19:55: Agent 5 launcher ETA; Agent 3 exploration run lx1 started

- **Agent 5 (#4):**
  - run-night.ps1 is 551 lines and parses; the main loop is next.
  - RUN-NIGHT.cmd and the README are due ~20:40. All -DryRun tests and the review requests to Agents 10/11 by 21:30; fixes by 23:00.
  - The relaxed MsMpEng gate is in as specified: strict for 30 min after a GO, then ≤1.2 cores with spread ≤0.2 over the last 3 one-min averages, logged as "relaxed gate".
  - W6 draft gets finalized once an S4b bin appears in build/agent2 (none yet).
- **Agent 3 (#2):** exploration run `build/agent3/runs/20261122-195210-lx1-devoff4` started 19:52 (functional, hidden desktop).
- **Machine at 19:55:** S4b build at -j8 (8 clang++), 8.2 GB RAM free, no HOLD/GO/STOP.

### 20:06: PreToolUse hook errors are not a HOLD signal

- **What happened:** Agent 9 paused task #8 after the agy-grid PreToolUse hook rejected its read of WINDOW-HOLD.txt ("exit status 1", empty stderr). It assumed a window was running. My own read_file got the same error once at ~20:03, and the next calls worked.
- **Facts:** no HOLD, GO or STOP file existed at 19:55 or at 20:04. grid-hook.js (`.agents/hooks.json`, 15 s timeout) is written to exit 0 with a neutral answer whenever it fails. An exit 1 with empty stderr therefore means the hook process itself failed or was killed, probably by the timeout while the machine is loaded (S4b at -j8 plus Agent 3's lx1 game). It is not a deny.
- **Rule sent to all agents:** only an existing `perf-notes/WINDOW-HOLD.txt` means a window is running. Check it with `Test-Path` in run_command; a read_file answer of "file does not exist" also means no HOLD. After a hook exit-1 error, wait ~30 s and retry. After 3 failures in a row, report to Agent 1. Agent 9 resumed.

### 20:30: Hook-failure episode over; Agent 7 #6 done (T-std); W6 power-mode option; Agent 7 → #14

- **Hook failures, 20:17-20:23:** Agents 2 and 9 got 3 PreToolUse failures in a row and stopped; two of my reads failed too. During the episode a trivial command took 1-2 min. The machine was overloaded: Agent 3's 2nd exploration game, the S4b SDK install, game configure and gen-check, and many agents and subagents at once.
  - Readings at 20:26: node starts in 0.12 s, disk 94-98 % idle, 8.3 GB RAM and 34.7 GB commit free, CPU 72-85 % with no clang and no game. Tool calls take 1-2 s again.
  - Every agent was told to resume and to run heavy scripts at Below Normal. If the failures come back while S4b compiles, Agent 2 restarts ninja at -j6.
- **Agent 7 #6 done** ([RESULTS.md](../build/agent7/w4b-noise/RESULTS.md)). The read-out method for W5 and later is **T-std**: frames are split at the runner's 4.5 ms threshold and re-mixed at the median heavy-time share. When rounds matter (as in W4b) it is **B-block T-std**.
  - Median-ms CV: W4b 12.2 → 2.3 % (B-block 1.4 %); W5 6.5 → 2.1 %. The 95 % band for 3 vs 3 runs is about ±4 %, against raw's ±12.5 %.
  - Guards on every read-out: light share per arm with its F test, raw GM deltas, and the host-flag list (P util ≥90 % and E-cores <600 MHz). The flag catches exactly W5's 3 slow runs.
  - **W5 (T-std):** all four S4a arms are 1-2.5 % slower than S3d, none significant. d11t p99 is +8.8 % [+1.0, +17.2]*, and d11t/d11p heavy-frame 1 % lows are 8.5-11 % worse*. That points at REX_TIMER_WAIT_BLOCKING=1, but many tests were run, so it is a lead only.
  - **W4b (B-block T-std):** d3 and d11t equal d0 within ±3-4 %. Codegen B may be a few % faster (fps +6.0 % [+0.5, +11.8]*, n = 3), which is a hint only.
- **W6 option for the user (ask at ~23:30):** Agent 7 traces the noise to the host state: the Balanced scheme with the best_efficiency overlay, under which the E-cores drop to ~550 MHz while the P-threads saturate. Setting Power mode to **Best performance** before the double-click would likely remove most of the spread at the source. Agent 12's gate G11 already handles this: one overlay for the whole window, and W6 is then compared only within itself, not with W5's absolute numbers.
- **Agent 8** uses T-std for the W5 read-out (RESULTS.md, "Recommendation for W5's read-out").
- **Agent 7 → #14:** a T-std read-out kit for W6-W10 that works on any matrix folder and reproduces the W4b/W5 numbers exactly, plus a repeats/CI note for choosing repeats=<n> in the GO lines.
- **Agent 4 (#12), 20:29:**
  - The expected native4b fingerprint is **9b40acbbef4c57b3**. It is provisional until step 1b re-confirms it after the snap1-on CMake re-run (build.ninja is still from 13:33).
  - REPIN.md and matrix-repin-native4b.json are adapted.
  - New: a 1-run frontend-on boot matrix, matrix-repin-native4b-boot.json. native3_boot_check group A fails with native_settings_frontend=false, which every repin arm uses.
  - So Agent 3 gets 5 runs (~19 min) instead of 4. Approved.

### 20:32: T3 Code closed (user's request); Agent 12 #11 done → #15

- **T3 Code:** the user allowed closing it to cut load (20:30). Its window was hidden, so CloseMainWindow did nothing, and all 14 processes were force-stopped. That includes its backend, t3-resource-monitor and its cloudflared tunnel.
  - First I checked that no agent descends from T3 Code: the chain is agy ← cmd ← agy-grid electron 18700. agy-grid and all 12 agy processes are untouched.
  - Free RAM went from 8.4 to 9.4 GB. CPU is 78-90 % with 8 clang++ (the S4b game compile at -j8, as expected).
- **Agent 12 #11 done:** `build/agent12/p2c-check/p2c_check.py` prints P2's memexport full-buffer fallback counter per game process. Exits: PASS 0, FAIL 1, NO DATA/PARTIAL 3, ERROR 4. Its path went to Agent 3.
  - W6-GATES.md now includes G11 (power overlay, via w6_env_record.py) and G12 (strict or relaxed quiet gate).
- **Agent 12 → #15:** one command that runs every W6 gate (G1-G12) on a finished window folder and is generic for W7-W10. It gets tested on W5/W4b, and Agent 12 checks that the launcher logs give G11/G12 what they need.

### 20:38: Launcher pre-read SAFE (Agent 10); fixes sent to Agent 5; pin freeze 23:30; functional matrix runs must stay out of build/agent8/matrix

- **Agent 10 pre-read** of run-night.ps1 00BFECD70584FC8E, RUN-NIGHT.cmd FCB0441883AC468D and the README 01C4D90F89DAAF9B: **SAFE so far**. P1-P5 pass (pinned runner only, the 5 apps only, screensaver restored in the main finally, refuses when locked/on battery/past deadline, writes only its own folders plus GO/HOLD/STOP). The relaxed gate matches 19:31.
  - The formal rating comes after a second reader, when Agent 5 asks.
- **Fixes sent to Agent 5, due 23:00:**
  1. Close-Programs: a try/catch around each process, including WaitForExit.
  2. Set-Hold/Clear-Hold: write HOLD only if none exists, with a marker, and delete only its own. A foreign HOLD at gate time counts as a gate fail.
  3. Get-Power: a failed battery query must not count as AC (use GetSystemPowerStatus).
  4. RUN-NIGHT.cmd: save with CRLF, then one smoke test with a temporary STOP file, expecting exit 2.
  - Also adopted: -NonInteractive; log the bin exe/MANIFEST sha at GO and re-check it at start; log leftover REX_*/LEGO_* variables; README notes.
  - **Roblox Studio comes off the close list** (unsaved work). The user's "Roblox" is read as the player.
- **HOLD interplay** (for fix 2): my hold manager overwrites the launcher's HOLD once the runner creates the matrix folder. It clears the HOLD when summary.md appears, or after 6 min with no game and no writes. So the launcher's Clear-Hold will often find nothing of its own, which is fine.
- **Pin freeze from 23:30** (told to Agents 5 and 8, the only owners). No edits to bench/agent8/run *.ps1/*.py/*.cs, drivers/*, the harness toml, nvml.cs, run-night.ps1 or RUN-NIGHT.cmd, and no new *.py/*.cs in bench/agent8/run. The launcher pins these at the double-click. Matrix JSONs and RUN-WINDOWn.cmd can still be added, because the GO line pins the JSON's sha.
- **Risk found:** REPIN.md runs run-matrix.ps1 with no -OutDir, so its output lands in build/agent8/matrix/<stamp>.
  - Any new folder there trips the hold manager. HOLD then pauses every agent, and Agent 2's run-s4b kills ninja (exit 30).
  - Agents 3 and 4 were told to pass `-OutDir build\agent3\runs\<name>` for all functional matrix runs.

### 20:42: Agent 2 progress; W5 bins re-hash unchanged; re-pin after Agent 3's queue

- **Agent 2 (#1):**
  - The OFF game phase is a full rebuild: 462 edges, because the C1/P2c SDK headers changed. It was at [200/462] at 20:39, so the build should finish ~20:52 and devoff4b be staged ~20:55.
  - Gate 5's second half passed early (20:35): all 27 rows match W5-INPUTS-1731, and devoff3-bin and devoff4-bin match their MANIFESTs (B9C5175D…, 16DCC939…). Report: `build/agent2/s4b/checks/w5-rehash-2035.txt`.
  - The CTR and CG26 helpers passed their dry runs and get built after native4b, at -j8.
- **W6 draft** (`build/agent5/w6-draft/matrix-w6.json`): 6 arms × 3 repeats, all on the S4b bin, no native arms. The ref is s0; the w6 group is p2, p2f and p2fc; the w6-noP2 group is f and fc.
  - So Agent 3 runs its S4b queue first. The native4b re-pin runs (boot plus 4 runs, ~19 min) come after it or in its gaps, and exploration stops once devoff4b is staged.

### 20:45: Agent 8 interim read-outs (W4b, W5); W6 bin = devoff4b, no timer bundle; I write the GO

- **W4b** ([READOUT.md](../build/agent8/readout/w4b/READOUT.md)): strict rules FAIL, so there is no timing verdict.
  - Rows that ignore R3/R4/R6 all overlap d0 (fps: B +6.4 %, d3 +3.8 %, d11t -0.8 %).
  - d11t game CPU is -15.3 % in every variant.
  - The B-block T-std hint for codegen B (fps +6.0 % [+0.5, +11.8]*, n = 3) awaits its independent check (~21:15).
- **W5** ([READOUT.md](../build/agent8/readout/w5/READOUT.md)): strict rules FAIL (R3 drops 15/15, R6 drops 1821). Without the drops, every arm overlaps base.
  - T-std: no median or fps CI excludes 0. The one lead is d11t p99 +8.8 % [+1.0, +17.2]* (1 of 16 tests).
  - Game CPU: d11t -13.7 %, d11p -12.2 %.
  - "P saturation" = P util 91-98.5 % (time-based P busy 80-87 %).
  - **W5 result:** the S4a arms equal S3d within about ±4 % (T-std). The timer bundle cuts game CPU by 12-14 %. There is a p99 tail lead against d11t.
  - Procedure: agent8-window3.md L920-1058, plus the step-9 addendum at L1060 (T-std primary).
- **W6 promotion tool:** `build/agent8/w6-stage/promote-w6.ps1` checks Agent 5's finalize output, copies it byte for byte, runs -PlanOnly, hashes 29 inputs and prints the GO line.
  - Its test on the devoff4 dry run passed: 13 runs, ~30 min, no new matrix folder. With -Promote pointed at a dry run, it refuses (exit 1) and writes nothing to bench.
- **Decisions sent to Agent 8:**
  - W6 bin = **devoff4b** (`build/agent2/devoff4b-bin`, with the MANIFEST sha Agent 2 reports), finalized once Agent 3's queue passes.
  - W6 stays **without the timer bundle**: d11t has the p99 lead, and s0 stays comparable to W5's s0.
  - **I write perf-notes/WINDOW-GO.txt** after the user leaves. Agent 8 sends me the GO line from promote-w6.ps1.
- **20:45, Agent 4:** the -OutDir risk is closed. Every run-matrix.ps1 command in REPIN.md step 3 and in the matrix notes now writes to `build\agent3\runs\repin[-boot]-<stamp>`, and REPIN.md has a rule line for it. Agent 3 waits for Agent 4's go.
  - The independent read found 2 mismatches, both fixed: stale S4-DRAFT line references, and boot-check group D can't fail on its own (a pass now also needs D's fingerprint line and `D=PASS`).
  - New sha prefixes: REPIN.md 02D08AF9, matrix-repin-native4b.json 2580067D, -boot 37DFC58F, -packhit 490964AC. Step 1b waits for the snap1-on configure.

### 20:56: devoff4b staged, gates pass; Agent 3's S4b queue running

- **devoff4b-bin staged 20:49:07** (S4b + S4c, C1 v3).
  - MANIFEST DE11A914079D7DF7…, legodimensions.exe DFBE1D43B28861A6, rexruntime.dll A33801D1538D6175, rexgpu-xenos.dll E3CB99CFDEA95E66, map 52155274A978A946.
  - **I re-hashed the MANIFEST, exe and both DLLs: all match.** devoff3-bin and devoff4-bin MANIFESTs are still B9C5175D and 16DCC939.
  - Build: 3486 s total. The SDK took 1360 s (Defender). The game took 2093 s: the gen-check took 729 s because of the 20:17 overload, and the full 462-edge rebuild took 1339 s at -j8.
- **Agent 10's gates:**
  1. PASS: all 16 files match their after-hashes, checked three ways. The TU is **01D9F8F3** (LF), memory_watch.cpp 70829846 (CRLF), toml 7F775847 (#26 OFF).
  2. PASS: full SDK and codegen-tool rebuild; gen-check 886/886 identical, no regen.
  3. PASS: the map has 31 hooked aliases by name and object. The 4 targets now live in gpu_wait_backoff.cpp.obj; their `__imp__` aliases stay in TUs 248/107/422/232. An independent subagent check is still running.
  4. Pending: the native re-pin on native4b.
  5. PASS: the W5 re-hash at 20:35.
  - Bin checks: MANIFEST 102/0, strings PASS, and the P2c counter string is in the xenos DLL (Agent 12).
- **native4b:** configured 20:53:23. Gen-check and gate PASS. The fingerprint is **9b40acbbef4c57b3**, which confirms Agent 4's. Full 485-edge rebuild at -j8 since 20:53:30, ETA ~21:20; then CTR, then CG26.
- **Agent 3's S4b queue** has run on devoff4b-bin since 20:52.
  - Order: s4b01 → s4bL0 (gate A's s0) → w6gA → w6s2 → w6s1 → g3q → s4b23 → s4b07 → w6s3 → s4b20 → s4b22/24/04 → s4b08 → re-pin (rpb0/rpm4, after Agent 4's go) → s4b02/05 (native, needs native4b) → W7+ rows.
  - ETAs: interim W6 result (G3/G4/G5/G8 inputs) ~21:35; rows 7/20/23 ~22:10; W6 block ~22:38; re-pin ~23:02. Last launch 23:10, games closed by 23:25.
  - **Most W7+ functional rows won't run tonight**, so W7+ windows probably can't be promoted. The overnight plan is W6, plus any window built only from arms that have already passed their functional checks.

## 21:01 Agent 1: launcher fix list, W6 finalize, build cutoff

- Launcher v2 (run-night.ps1 924321AE, RUN-NIGHT.cmd F7190AB2, README 39ECF5C2): Agent 10's addendum (20:56) and Agent 11's pre-read (build/agent11/launcher-review/REVIEW.md, 20:58) both say SAFE once (5) is in. Sent to Agent 5, aim 22:45, hard 23:00:
  - MUST: (5) driver = plain string `^drivers/[A-Za-z0-9_-]+\.ps1$` resolving inside `$RunDir\drivers`; objects and args refused. (6) refuse to start when the deadline is > 14 h away. (7) re-check LogonUI, AC and desktop after Close-Programs, right before the runner. F1: explicit env names for the W8a/W8b/W9 arms (Agent 8 lists them; pre-approved if every key is an exact name used by those arms; exact case, no patterns; DRY RUN line generic; README). F3: latest start 06:45 (refuse a GO read at/after it, give up in Wait-Quiet, refuse in Start-Window, log, README). README L151 (Sync-Hold text). The STOP-file smoke test of RUN-NIGHT.cmd.
  - SHOULD: (8) runner via Start-Process -PassThru, poll STOP and deadline + grace, kill the whole tree (runner, legodimensions, drivers) and log it; else the documented behaviour stays. F5: add copilotapphost/copilotapp_proxy (only under `\WindowsApps\Microsoft.MicrosoftOfficeHub_`) and Windows10Universal (only under `\WindowsApps\ROBLOXCORPORATION.ROBLOX_`). Separate try for Set-Awake and Restore-Screensaver.
  - OPTIONAL: F4 -NotBefore 00:00 (GO left unread until then). F6 CPU + top-3 processes per gate sample. No WINDOW-CANCEL.
- W6: Agent 5 finalizes matrix-w6 now with build/agent2/devoff4b-bin (MANIFEST DE11A914079D7DF7, re-hashed by Agent 1). Agent 8 promotes after Agent 3's W6 rows pass.
- Agent 3's queue already passes `-OutDir build\agent3\runs\<id>-<stamp>` for matrix rows (s4b-queue.ps1 L131). Nothing to change.
- Agent 4 step 1b PASS on the real native4b configure: fingerprint 9b40acbbef4c57b3 (build/agent4/repin/dryrun-native4b-1b-2055.txt, 2EB43DEF…, 0 FAIL, 0 WARN). Pin record after native4b-bin is staged (~21:20).
- Builds: all finished by 23:40. Don't start one that can't finish by then; stop at 23:40 and resume tomorrow.
- Hold manager exits at 07:30 without clearing (Agent 11 F6): in the morning Agent 1 clears a stale HOLD only if no runner or game is running.
- Agent 8 (after W6 promotion): propose up to 2 follow-up windows for 01:00-06:45 by 22:45, using only arms already checked functionally and allowed by the launcher (e.g. a codegen B vs d0 repeat for the W4b hint; d11 vs d11t for the W5 p99 lead). Agent 1 picks one or two.

## 21:04 Agent 1: Android report done

- Agent 9 #8 done: perf-notes/ANDROID-FEASIBILITY.md v1.1 (752 lines, 21:01). About 349 citations were re-checked by 3 subagents. Verdict: feasible, but as a port project of ≈17-42 person-weeks. Top blockers: arm64 memory ordering in the generated code; the Vulkan backend ("not ready"); Android build and surface glue. Cheapest first step, P0a: the Windows build with REXGLUE_USE_VULKAN=ON and gpu_backend = vulkan, on the PC, no phone needed. Not tonight (builds stop at 23:40); it's the user's decision. Agent 9 stays idle, with no new task, to keep the load down.

## 21:15 Agent 1: F1 env list approved, W6 promotion rule

- F1 approved as is: build/agent8/w8w9/ENV-KEYS-F1.txt (sha256 D1AE6D57…B35C). 11 exact-case keys: REX_TIMER_WAIT_BLOCKING, LEGO_GPU_WAIT_STATS, LEGO_GPU_WAIT_BACKOFF_US, LEGO_GPU_WAIT_SPIN_US, LEGO_NATIVE_FRAME_METRICS, LEGO_NATIVE_SHADER_MISS_CACHE, LEGO_NATIVE_THREADED, LEGO_NATIVE_PREPARE_THREADS, LEGO_NATIVE_SNAPSHOT_STATE, LEGO_NATIVE_FULL_DRAW_PREPARATION, LEGO_NATIVE_CHAIN_PRIORITY. Agent 8 checked them against the bins. The W8b keys stay, so the launcher won't need another change.
- W8b can't run tonight: #21 isn't built, so LEGO_NATIVE_CHAIN_PRIORITY is in no bin.
- W9 (devoff4b, #24, 16 runs, ~40 min) and W8a (native4b after the re-pin, 13 runs, ~33 min) are possible follow-ups if their functional rows pass. W9 uses SPIN_US=30 (the default) tonight.
- W6: Agent 8 dry-tested finalize on a copy (13 runs, ~30 min) and ran promote-w6 in test mode (PASS 102 / FAIL 0). Promotion happens once (a) Agent 5's real finalize is in build/agent5/w6-draft (by 22:00) and (b) Agent 3's interim W6 rows (w6gA, w6s2, w6s1) pass. Agent 1 writes the GO only after all of Agent 3's W6 rows pass (including w6s3, ~22:38) and the user has left. Repeats are set after Agent 7's note (22:30).
- Agent 3's queue: s4b01 (20:54-20:57) and s4bL0 (21:01-21:09) are done; w6gA has been running since 21:09.

## 21:29 Agent 1: cron 4. Gate A hang triaged; launcher MUSTs; hard stop 07:30

- Hold manager running (pid 25948 since 19:29). No HOLD. native4b still compiling (ETA was ~21:20). 8.0 GB RAM free.
- **w6gA (gate A, p2fc + verify + slow_frame_log_ms=1, L route, devoff4b): exit 1 = RECOVERED HANG** (build/agent3/runs/20261122-210906-w6-gateA-p2fcv-level).
  - 1 STUCK-LOCK at 544.95 s (CS 0x84959edc), dump hang-36276.dmp, closed fine by WM_CLOSE.
  - The owner is parked at lr=83FAF188, inside sub_83FAF180: #24's H1, the poll step of the L1 GPU fence wait. In devoff4b that function lives in gpu_wait_backoff.cpp; with #24 off it goes straight to `__imp__`. The callers are in the same wait path (83FBF698/83FBFA98 near sub_83FBF7D0 = H0; 83FBFBDC in sub_83FBFB30). This is the known stuck lock, finding 10 (S4-DRAFT L454: v0.2.0 hits it too).
  - It happened while verify mode made the game about 9x slower: ~12-20 fps vs ~125-150 fps for s4bL0 (OFF) in the same 218-226-draw scene, and the -j8 compile was running. w6s2 (p2fc, no verify, uncapped, title) ran 100-440 fps, exit 0, 0 errors. So the slowness comes from the verify debug mode, not from the timed p2fc set.
  - Gate A log check (Agent 1): `C1 verify: on` 1, `first kept protect at` 1, `C1 verify K:`/`F:` 0, `keep-watch: on (with ...hold_global_lock)` 1, `...is off` 0, `Recovered` 0. G5 and G8 pass; G4 (p2c_check) comes from Agent 3's postcheck.
  - **Rule:** a STUCK-LOCK whose owner is in the L1 poll (sub_83FAF180), seen under verify or build load, counts as a WARN (finding 10), not a W6 FAIL. Gate A passes if G4, G5 and G8 pass. The W6 read-out reports STUCK-LOCK counts per arm (p2fc vs s0).
- W6 finalize done by Agent 5 at 21:16-21:17: build/agent5/w6-draft/matrix-window6.json (E50D791B…), RUN-WINDOW6.cmd (3F31CBA8…), FINAL.txt. Agent 8 promotes after w6s1 passes and Agent 3 confirms G4 on gate A and side 2.
- Launcher run-night.ps1 3EFC5312 (21:15), Agent 10's interim read: F1, F3, (6), (7) and (8) are in.
  - New MUST: Stop-Tree must not use `taskkill /T`, because PID reuse could kill explorer or the grid. Walk a Win32_Process snapshot down from the runner, keeping only children created at or after their parent; Stop-Process each, then $P.Kill(). If CIM fails, use only $P.Kill() plus the build\agent2 legodimensions sweep.
  - MUST: restore the driver allowlist (thread-cpu, pso-stats-at-end, io-counters) on top of the path rule.
  - SHOULD: Get-BuildProcs in Start-WindowLocked.
  - **Agent 1: the hard stop is 07:30, not 07:45.**
  - **Copilot confirmed:** on this PC "Copilot" is the Microsoft 365 Copilot app (Microsoft.MicrosoftOfficeHub, the only Copilot installed). copilotapphost/copilotapp_proxy with the path check are approved. The Store Roblox Windows10Universal (path-checked) is the player: approved.

## 21:33 Agent 1: W5 logdiff clean; Agent 6 on the W6 logdiff kit

- Agent 6 #13 done: W5 logdiff (build/agent8/matrix/20261122-1756). All 16 runs are clean: STUCK 0, no WER or dumps, NEW/MORE/GONE/FAIL 0 for every arm against both s0 and base. The d11, d11p and d11t lines are only the expected timer lines. Base vs s0 (S3d→S4a): no line difference. The slow runs (s0-r2, base-r2, d11t-r3) have normal logs, so the cause is CPU placement or contention (P-cores 91-99 %, E-cores at their lowest clocks). d11t/d11p cut TimerQueue busy from ~50 % to ~5 % with no change in frame time. Output: build/agent6/w4b/out-20261122-1756-vs-s0/ and -vs-base/; notes §13 of perf-notes/agent6-attract-stalls.md.
- New task for Agent 6 (read-only): (1) an independent check of whether gate A's STUCK-LOCK matches finding 10, by 22:15; (2) a W6 logdiff kit with the expected lines per arm, taken from Agent 3's devoff4b functional runs and tested on W5. The morning W6 logdiff starts on Agent 1's word.

## 21:55 Agent 1: W6 cleared for promotion; W6 repeats; gate A confirmed as finding 10

- W6 functional gates (Agent 3, 21:48-21:52): w6s1 PASS and w6s2 PASS (NEW 0 / MORE 0 vs RT, every proof line OK, cvars as W6-GATES v2). G4 p2c PASS (total 0) on gate A, side 1, side 2 and row 23. G3 PASS. G5 PASS, with partial coverage. G8: gate A's line items pass, with the finding-10 WARN. Row 23 (s4b23) PASS. w6s3 runs ~21:53-22:00.
- Agent 6 #16 part 1: gate A's hang is CONFIRMED as finding 10, the Xenos L1 fence-wait (H1) variant.
  - Lock: kGraphicsLock 0x84959edc. Owner lr is 83FAF188, the same as devoffB X3.
  - #24 OFF was a pure pass-through: no LEGO_GPU_WAIT_* env var and no back-off line.
  - Verify mode made the CP the bottleneck (median 61.5 ms per frame). The 9.7 s stalled frame had 1244 memexport syncs, against 5-62 normally. The -j8 build saturated the machine.
  - Agent 1: go ahead and read the CP thread's stack from hang-36276.dmp (dumpstacks.py, BelowNormal, ~1 min).
- Agent 8: promote W6 now (the conditions are met) and send the GO line.
  - W6 runs at repeats=4 by default, ~53 min. Agent 7's REPEATS.md gives ±3.2 % median ms and ±2.7 % fps for that; repeats=3 would give ±3.8 % / ±3.3 % in ~40 min.
  - repeats=4 stands unless the overnight plan due at 22:45 can't fit it.
- Agent 7 #14 done: readout.py (T-std/B-block), repeats.py and REPEATS.md. Self-test 113/113, including the W4b/W5 regression; the independent check found 0 mismatches.
- Launcher: Agent 10's 21:48 items forwarded to Agent 5:
  - README L47/L176/L242/L251 still say 07:45 and taskkill /T.
  - Fresh go/gate/run tests on the final hash, covering STOP mid-run, the 07:30 kill, -TestFailAfter and killing a fake-runner child.
  - The final hashes go to Agents 10 and 11 by 23:00.
  - Agent 5 also has to answer Agent 3's ready-m1 question (s4b20 waits on it).
- Agent 3: w6gB counts as the C1 level-load coverage, and row 7 stays capped. The menu-phase watch stays with Agent 3: devoff4b takes 16.6-17.3 s against ≤8.7 s on devoff4, measured under load.
- native4b was at [304/485] at 21:50 (~5 edges/min), so staging is ~22:35-22:40.
- The user asked for the ETA to full completion. Agent 1's estimate, uncertain: S4 needs about 3 more nights plus about a day for keep/drop decisions, the final build and the write-up, so around Wed-Thu Nov 25-26.
  - Tonight: W6 and the follow-ups.
  - Mon: W10, W7, and W8a if it doesn't run tonight.
  - Tue: a confirmation window of the final set vs S3d, plus W8b if #21 is built.

## 22:05 Agent 1: what would speed S4 up; tasks #17 (Agent 7) and #18 (Agent 9)

- The user asked what resources would speed things up (the model-call limit is 90/min; the grid uses ~15-27).
  - Agent 1's answer: model calls aren't the bottleneck. The limits are the one laptop's CPU (builds vs functional runs) and timed windows, which need the user's double-click and an idle, unlocked, visible desktop.
  - Proposed to the user, awaiting answers:
    - a daytime launcher session (needs an end-time option and a re-review);
    - agents use the PC after tonight's last window (~03:30-06:00) for the CG26/CTR builds and their functional rows;
    - a Defender exclusion for the project's build folder (the user, as admin);
    - turning off the NVIDIA app overlay/PresentMon, plus Best performance;
    - dropping #19 (still design-only) and with it W7;
    - the #1 screenshot check and the #33 answer.
  - All of it together could move completion from Wed-Thu to about Tue.
- Task #17 (Agent 7): stage #21 (LEGO_NATIVE_CHAIN_PRIORITY) for Agent 10's rating on Monday morning, plus the §15.4 functional rows and the W8b arms. Staging only, done by 23:30.
- Task #18 (Agent 9): a read-only CG26 check kit for Agent 10's #26 gates (W10 readiness), plus an independent pre-read of #21. Done by 23:40.
- Agent 3: row 7 (s4b07) PASSES, capped at 600 s. Its 92 "C1 verify F" lines fit R1, because the row has no fix (i). Not a W6 blocker, since every W6 C1 arm has fix (i).

## 22:10 Agent 1: G4 complete; Agent 10's G5 rating; C1 without P2 not cleared; W6 repeats=5

- Agent 3 (22:05): G4 is complete. P2c total is 0 on all four untimed W6 runs: w6s1, w6s2, w6gA, and w6s3 (`20261122-215230-w6-side3-p2fc-attract`).
  - w6s3: exit 0, err/crit 0, STUCK-LOCK 0, kept 114688. Its WM_CLOSE took 25.4 s under the build load (limit 60 s). Agent 3 is checking WM_CLOSE times by C1 state, and Agent 8 is confirming the runner's close timeout. The w6s3 logdiff is still pending.
- Agent 10, G5 for gate A: **PASS, partial coverage** (to story-load, 104/119 steps; K 0, F 0 over 32768 kept protects; gate D 0; P2c 0). Fine for W6.
  - Still open: S21 A (b2r L1065). Before C1 can go default-ON, one p2fc + verify run has to reach the level, with a longer cap than 600 s. Candidate: Agent 3's queue tomorrow, or after tonight's windows if the user approves.
  - Correction: row 7 does have fix (i) (`physical_protect_hold_global_lock`). What it lacks is P2 (`shared_memory_single_hold_rearm`, #8). So its F 92 is not R1.
    - **Rule (Agent 10): C1 without P2 is not cleared, timing arms included,** until Agent 12 explains the 92 or a C1-OFF verify baseline (P2 off, L route) runs.
    - Follow-up windows get no C1-without-P2 arm.
    - W6 is unaffected: its GO is `only=s0,p2,p2f,p2fc` (FINAL.txt). The w6-noP2 arms f and fc are for the "G4 FAIL" decision row only and stay out.
  - Nit: the check's PROOF labels should say "to story-load" for capped runs. This goes into b2r as row 42/§41.
- **W6 repeats: 5 (Agent 1).** W6 has 4 arms, not 6, so the 21:55 figure (repeats=4, ~53 min) was wrong. Agent 7's formula gives 1.70 + 2.14·4·5 ≈ 44.5 min, plus up to ~2.5 min for the slower closes of the 5 p2fc runs. Precision is ~±2.9 % median ms, and repeats=5 meets Agent 12's ≥5 ask (S4-DRAFT L356). It stays W6 first in Agent 8's 22:45 plan.
- Agent 4 (22:04): native4b at generated file 338 of ~438. Staging ~22:30, the pin record and handoff ~5 min later, and Agent 3's 5 re-pin runs done ~22:55.

## 22:25 Agent 1: user decisions (daytime sessions, after-window agents, #19 kept); s4b24 finding 10 without verify
- **User (22:10):**
  - Daytime sessions: yes. The user now gets a notification when they're needed.
  - Agents may use the PC after tonight's last window (CG26/CTR builds, test rows, reviews), with fan noise until ~07:00.
  - Best performance on AC was already set.
  - **#19 (R1 stage 2, `d3d12_async_submit`) stays in scope**, so W7 stays too.
  - A stronger PC may arrive on the 19th. That is after S4, so it doesn't change the ETA; timing runs on it would need new baselines.
  - Still unanswered and optional: the Defender exclusion for `build`, turning off the NVIDIA overlay, and the screenshot check (#1) + pop-in yes/no (#33).
- **New S4 ETA: ~Wed Nov 25.** Tue evening if everything passes the first time; Thu if #19 needs a second try.
- **Daytime launcher (Agent 5, after the night final):** RUN-DAY.cmd asks for the return time and sets `-StopAt` 15 min before it. If the night launcher is still running between windows, it stops it with the STOP file; if a window is running, it asks first. STOP-LAUNCHER.cmd writes perf-notes\WINDOW-STOP.txt. Plus a README section. run-night.ps1 stays unchanged.
- **W6 GO line (Agent 8, 22:09, checked with the launcher's functions):** `GO W6 matrix-window6.json E50D791B6C38638F718A1AF65EB15EAF543A78AC8EA50B69DD1CC96AB7C9A0D2 only=s0,p2,p2f,p2fc repeats=5`. 21 runs, ~48 min; the launcher accepts it until 06:32. RUN-WINDOW6.cmd (double-click fallback) stays at -Repeats 3.
- **s4b24 hang (Agent 3, 22:07):**
  - Run: W9 row, p2fc, verify OFF, menus route.
  - RECOVERED HANG at 22:07:54: STUCK-LOCK x5 + hang-31952.dmp. Route 54/54, WM_CLOSE 1.64 s, run-game exit 1.
  - Owner tid 0x17, lr 83FAF200, in sub_83FAF180, so finding 10. It sits 3 frames deeper than gate A's 83FAF188; the waiter is the same (GPU thread on PM4 0x22).
  - **This is the first finding-10 STUCK-LOCK without verify.** The host was at 100 % (8 clang++), and fps fell 56→19→14→1.3 at story-load.
  - **Ruling: WARN, and the W6 GO is unchanged.** Reasons:
    - run-matrix records a failed run and goes on (run-matrix.ps1 L26).
    - W6 runs on an idle PC, and its 5 p2fc runs are the repeat test, so no s4b24 rerun tonight.
    - Agent 6's verify-only explanation for gate A's kernel-mode CP time (VirtualQuery in KeepWatchVerifyRecord) is now incomplete.
  - **C1 default-ON now also needs finding 10 explained.** Agent 6 part 3 asks: is the CP kernel time there without verify, what are the extra frames, and has finding 10 ever appeared with C1 off (devoffB X3's config)?
- **Agent 12:**
  - #15 done: build/agent12/w6-gates/run_gates.py + run_gates.ps1.
  - G8: gate A's FAIL (finding 10) is read as WARN through a visible waiver, and s4b24 gets the same. No gate A re-run tonight; the post-window long-cap p2fc + verify level row is the clean re-run.
  - s4bV0 (C1-OFF verify control, ~5 min) runs tonight only if it fits before 23:10, after the rows that gate tonight's windows: s4b18, s4b17 (W9 gate, which Agent 3's 22:10 order dropped; checking with Agent 8), then the re-pin (rpm4 by 23:07).
- **Agent 3:**
  - w6s3 PASS (logdiff NEW 0 / MORE 0), so the W6-critical set is complete. s4b22 PASS.
  - WM_CLOSE times: the long ones (25.4 / 26.4 s) are the runs under build load, not C1.
- **After the last window:**
  - Agent 2: CG26 (+CTR), ≤ -j10.
  - Agent 3: the remaining rows plus the long-cap p2fc + verify level-load row (cap > 600 s, S21 A).
  - Agent 12: the W6 read-out.
  - Agent 7: #19 (staged diff, RATE-REQUEST, functional rows, 10-min soak, W7 arms), aiming for Agent 10 by Monday ~09:00.

## 22:28 Agent 1: finding 10 isn't C1's (s4b20); s4b18 PASS; CTR held
- **Agent 3 (22:26):** s4b20 (M1 only, **C1 OFF**, run 20261122-221447-s4b-20-m1-level) hit the **same** STUCK-LOCK at 22:18:20.
  - Owner tid 0x17, lr 83FAF200. The owner and waiter stacks match s4b24's exactly; the GPU thread is in PM4 0x22. It wrote hang-13236.dmp and recovered.
  - **So the 83FAF200 variant of finding 10 isn't caused by C1.** This corrects the 22:25 line "C1 default-ON now also needs finding 10 explained", and answers Agent 6's question (c).
  - Both hangs came with the host at 100 % from Agent 2's -j8 build. **W6's 21 runs on the idle PC are the load-only test.** No rerun tonight.
- **s4b18 (W9) PASS:** exit 0, 54/54, back-off ON line, 41 stats lines, sleep_fail 0, no STUCK-LOCK, NEW 0 / MORE 0 vs s4b01. Its WM_CLOSE took 40.1 s (C1 off, under the build load), the highest so far against the 60 s limit.
  - W9 rows so far: s4b18 PASS, s4b24 WARN (finding 10). s4b17 is still needed.
- **Agent 4 (22:22):** native4b slowed. Link + staging ~22:40–22:45, pin record ~22:50, Agent 3's 5 re-pin runs (~19 min) end ~23:10. rpm4 must still launch by 23:07.
- **Ruling:** after native4b's staging, Agent 2 starts no new build tonight. CTR moves to after the windows, with CG26 (≤ -j10).
  - Reasons: a bin built after 22:45 can't be functionally gated by 23:10, so CTR can't serve tonight's windows anyway. The finding-10 hangs and the long closes both came under the -j8 load, so the re-pin and s4b17 should run on a lighter PC.
  - s4bV0 (C1-OFF verify control) has no room before 23:10, so it is first in the post-window queue.

## 22:33 Agent 1: overnight plan picked (Agent 8's PROPOSAL.md)
- **Order:**
  1. W6 r5.
  2. W9 r4, if s4b17 PASSes. s4b18's logdiff is done.
  3. **W8a4 r6**: native4's r6 PASS counts as its functional cover (MANIFEST 00D33D4FFB46776D).
  4. W5b r6.
  5. W4c r6.
- **Cutoff:** the last new GO tonight is at 04:15. Anything left (W4c first) moves to Monday's day session, so the agents get the PC for CG26, CTR and the re-pin. Agent 8 promotes each window and sends the final ordered GO lines by 23:45.
- **Timeline (Agent 8, ~10-min gates):** W6 00:15–01:02, W9 01:12–01:57, W8a4 02:07–02:34, W5b 02:44–03:24, W4c 03:34–04:02. With 30-min gates the night would run to ~05:42, so the cutoff applies.
- **W8a (native4b) moves to Monday's day session**, if it's still needed after W8a4:
  - Agent 2 now expects native4b's staging at ~22:55–23:10. Agent 3's back-to-back Normal-priority runs held the CPU at 100 %, so the build managed only 2–3 steps a minute.
  - The 5 re-pin rows (~19 min) can't finish by the 23:10 last launch.
- **Agent 3:** runs s4b17 (W9 gate) right after w6gB, then launches nothing more tonight, so native4b can stage. After the windows: the re-pin rows, s4b02/s4b05 (W8a), s4b04, s4b08, s4bV0 and the long-cap p2fc + verify level row.
- **Agent 2:** lets native4b finish. The driver kills it at 23:40 if it isn't done, and ninja resumes later. CTR and CG26 build after the windows (≤ -j10).
- **Agent 4:** writes the pin record tonight if staging lands before ~23:40.
- **Agent 5:** until s4b17 has launched, -PlanOnly dry runs go only in queue gaps. Agent 5's dry runs caused 4 refused launches between 22:04 and 22:14.
- **Rule (Agent 8's caveat):** nothing compiles during W6–W10. The quiet gate catches a build at window start, but not one that starts mid-window.

## 22:33 Agent 1: overnight plan revised (Agent 8's PROPOSAL.md rev 22:35); W8a4 not tonight
- **Launcher:** Agent 11 rates it SAFE to pin at 23:30 (22:31): run-night.ps1 16B90FA8, RUN-NIGHT.cmd D7A0362B, README 0058C8F6. My sha256 of bench\agent5\launch matches all 3, and the folder holds only those files.
  - Still open: Agent 11 hasn't seen the RUN-NIGHT.cmd STOP smoke test, and Agent 10's formal rating is still due.
  - The daytime files go to build\agent5\day-draft\ (with README-DAY.md, so README.md is untouched). They are copied in only after review.
- **This replaces the order in my 22:33 entry:** W6 r5, then W9 r4 (if s4b17 PASSes), then W5b r6, then W4c r6.
- **W8a4 is out of tonight.** W8a (native4b, after the post-window re-pin) and its fallback W8a4 move to Monday's day session, together with W8b and W10.
  - Running W8a directly on native4b avoids a redundant W8a4 window.
  - Ending earlier gives the agents more PC time after the windows: CG26/CTR builds, the re-pin, and the rows W10 needs.
- **Timeline (10-min gates):** W6 00:15–01:02, W9 01:12–01:57, W5b 02:07–02:47, W4c 02:57–03:24. With full runner estimates it ends at 03:35.
- **Latest GO (every window ends by 04:00):** W6 03:00, W9 03:02, W5b 03:06, W4c 03:20. No GO after those times; W4c is dropped first. This replaces my 04:15 cutoff.
- **Failed or hung runs:** they are left out of the timing (readout.py, `--drop` for recovered hangs), and every verdict is given with and without the flagged runs.
  - Counts per arm: planned / timed / failed runs, STUCK-LOCK by owner site, dumps, slow-state, and host CPU at each hang.
  - An arm with fewer than 3 timed runs gets counts only, no timing verdict.
- **Staging:** Agent 8 promotes W5b and W4c at ~22:50 and W9 once s4b17 passes, running -PlanOnly only in queue gaps. Final GO lines come by 23:45.

## 22:36 Agent 1: launcher SAFE from both reviewers; approved for the 23:30 freeze
- **Agent 10 (22:33, b2r row 41/§40, b2r sha 0167405D…): SAFE.** Same 3 files as Agent 11: run-night.ps1 16B90FA8, README 0058C8F6, RUN-NIGHT.cmd D7A0362B.
  - RUN-NIGHT.cmd's mtime is 22:32:59 because the pin tests rewrite it; its content hash is unchanged.
  - P1–P5 pass, the relaxed Defender gate passes, and Fix 2 matches hold-manager.ps1 D060F913.
  - All must-fixes are in:
    - no taskkill /T: it walks descendants by creation time, plus a PID + start-time check;
    - the 3-name driver list;
    - Start-WindowLocked checks for builds;
    - 07:30 hard stop (GraceMinutes 0).
  - The 16B9 change only affects the Stop-One catch's logging (L801–808).
  - Agent 5's tests: go 16/16, hold 4/4, run 5/5, gate 12/13. The gate miss is t-relaxed, a timing problem in the test itself; it passed on B0902106 and in the solo re-run at 22:28:05.
- **Optional (a)–(d) wait.** These are README retry wording, a handle, a try block, and a log line at L831. run-night.ps1 stays frozen through Monday's day session, which RUN-DAY.cmd runs with -StopAt.
- **Approved for the 23:30 freeze**, with these conditions:
  - I re-hash all 3 files at 23:30.
  - No test may rewrite RUN-NIGHT.cmd after 23:25.
  - Agent 11's last open item, the RUN-NIGHT.cmd STOP smoke test, goes to Agents 10/11 before 23:20.
  - Any change after the freeze needs a new delta read from Agent 10.
- **Agent 11:** checks the W9 / W5b / W4c GO lines against the arm rules before 23:40, as it did for W6.

## 22:38 Agent 1: gate B passes, so the W6 functional set is complete; launcher tests all pass; day launcher becomes a generated copy
- **Gate B (w6gB, run 20261122-222313): PASS + finding-10 WARN** (Agent 3).
  - All 119/119 steps, through the level load.
  - Kept protects rose from 2 to 114688; verify off; K 0; gate D 0; P2 total 0; cvars match W6-GATES v2.
  - logdiff vs s4bL0: NEW 6 (the hang lines only), MORE 0.
  - The hang at 22:26:29 (owner lr 83FAF200) recovered; WM_CLOSE took 1.51 s.
  - One GONE line (of 73) is still being identified; it comes with s4b17's verdict.
- **The W6 functional set is complete:** gates A and B, sides 1/2/3, s4b22, s4b23 and G3. P2 total is 0 on every W6 run.
- **Finding 10 so far:** 4 of 13 runs tonight (w6gA, s4b24, s4b20, w6gB), all recovered, all under the -j8 build. It stays a WARN; W6 on the idle PC is the load test.
- **s4b17 (W9 gate)** started at 22:31:04. W9 is in tonight only if it passes by 23:45.
- **Launcher:**
  - STOP smoke test at 22:34: exit 2, as expected. The STOP file and status\ were removed afterwards.
  - Every test on 16B90FA8 passes: go 16/16, gate 13/13 (t-relaxed passed in its solo re-run), hold 4/4, run 5/5, pin 2/2.
  - My re-hash at 22:36: all 3 files match, and the folder holds only those 3.
  - The pins are taken at the 23:45 double-click. If any runner file changes after that, the launcher refuses that window.
- **The day launcher changes approach:** -StopAt is a dry-run-only test hook in run-night.ps1 (L65–67). So RUN-DAY can't drive the pinned launcher unchanged.
  - Agent 5 is writing run-day.ps1, a copy of 16B90FA8 generated by make-run-day.ps1. Only marked lines change: -StopAt is allowed and required, it pins RUN-DAY.cmd, and the HOLD text is changed.
  - It uses the same real mutex, so it can never run alongside the night launcher.
  - Also coming: launcher-ctl.ps1, RUN-DAY.cmd, STOP-LAUNCHER.cmd and README-DAY.md.
  - Everything goes in build\agent5\day-draft, with hashes by ~23:35. Agents 10/11 rate it after the windows.
- **native4b** was at [456/485] at 22:36.

## 22:44 Agent 1: s4b17 passes, so W9 runs tonight; gate B counts for W6; my claim that W6 tests finding 10 was wrong
- **s4b17 (W9's third gate): PASS** (Agent 3).
  - Run: devoff4b, back-off OFF, stats ON, attract-long, 420 s cap. Exit 0, 79/91 steps when the cap hit.
  - No dumps, no STUCK-LOCK. TimerQueue never stalled.
  - logdiff vs RA: NEW 0 / MORE 0 apart from the allowed GPU-wait lines.
  - Stats: l2_tries 21524 > 0, sleep_fail 0.
  - WM_CLOSE took 40.75 s under the -j8 load, a new max but under 60 s, so it counts as clean.
  - **W9 is in tonight.** Agent 8 promotes it now. The order stays W6 → W9 → W5b → W4c, with the latest-GO times unchanged.
- **Correction on gate B (Agent 3):** w6gB's 3 tags were never placed.
  - game.log rotated at 22:23:58, before the pad-3 trigger, and the sidecar's tail reopened at the old offset. Its log shows placed=False, load-confirms 0/3.
  - Gate B still ran the same story-load → vortex → level frames as s4b20.
  - Agent 3 is fixing the sidecar and testing the rotation case without the game.
- **My ruling: gate B counts for W6, with a coverage note ("level load without tags").**
  - W6's timed runs are title + attract only, with no input script, tags or level load (matrix-window6.json L27, which notes the launcher refuses menu/trigger fields; Agent 6). So a tagless level load already goes beyond what W6 times.
  - Tags with C1 are covered to story-load by gate A (3/3 LOADs).
  - **For C1 default-ON:** s4bLV (p2fc + verify, cap 1800 s) must run with the fixed sidecar, show 3/3 LOADs and reach the level.
  - Agent 10 rates gate B for the record.
- **Correction to my 22:25/22:38 notes: W6 does not test finding 10** (Agent 6, build/agent6/hang/cp-state-s4b24-s4b20.md).
  - W6 is set up like W5 (title + attract), so it never runs the vpad L route where the hangs happen.
  - **Mechanism (inferred, high confidence; no rexgpu symbols):** the CP blocks in IssueDraw → IssueDraw_MemexportReadbackFullPath → AwaitAllQueueOperationsCompletion → CheckSubmissionFence → WaitForSingleObject(fence_completion_event_, INFINITE).
    - Each full-path memexport draw costs one submit plus a host↔GPU round trip.
    - Meanwhile render tid 0x17 holds CS 0x84959EDC while polling a fence that passes only after those draws.
  - It is not hashing, K-checks or hold_global_lock.
  - The 5 s detector needs a slow CP. Gate A's CP was slow from verify (kernel 75–86 %); s4b20 and s4b24 were slow from CPU starvation (kernel 3–11 %).
  - All 3 hangs Agent 6 analysed happened under the -j8 build. Starvation as the cause is not proven, and not ruled out either.
  - **Direct test, first thing after the last window, before any build restarts:** two untimed vpad L-route rows on the quiet host (Agent 3), both with slow_frame_log_ms=1 and tags via the fixed sidecar:
    - s4b20's set (C1 OFF);
    - w6gB's set (p2fc).
  - If both are clean, finding 10 stays a load-only WARN. If either hangs, Agents 6/12 study the full-path sync.
  - Later perf candidate (after S4): the memexport readback full-path sync.

### 22:55 - Agent 1: finding-10 waiver extended; freeze-check notes
- Gate B (`20261122-222313-w6-gateB-p2fc-level`) also hit finding 10: STUCK-LOCK at 22:26:29, CS 0x84959EDC, owner lr 83FAF200, hang-38764.dmp, recovered (Agent 12). The 22:25 waiver now covers it too: raw FAIL + "WARN, finding 10". Gate B isn't an input to the W6 read-out.
- Decided now, before the runs, for s4bLV and the two finding-10 rows: a STUCK-LOCK counts as "WARN, finding 10" only if all of these hold:
  - CS 0x84959EDC; the owner (render thread, tid 0x17) is parked in sub_83FAF180 at lr 83FAF188 or 83FAF200; the waiter is at lr 82A2A270. (Corrected at 23:00 per Agent 12: gate A's owner was at 83FAF188, so "lr 83FAF200" alone would have failed a gate-A-type hang. All 4 hangs share the waiter callers and the GPU thread on PM4 opcode 0x22.)
  - it recovers by itself, with no crash or WER;
  - the run still reaches the level. For s4bLV that also means 3/3 LOADs and K 0 / F 0 over the whole run.
  - Anything else is FAIL.
- Agent 12: under verify the CP is ~50% kernel-bound (row 7, gate A). Without verify the median is 4-16%. Suspected cause: one VirtualQuery per upload. Candidate for after S4.
- `bench\agent5\launch\status-dryrun\` is the launcher's own dry-run folder (README L253-255, run-night.ps1 L70). The pin tests last wrote to it at 22:32:21. It holds no pinned files, so the freeze check covers only the 3 launcher files.
  - Dry runs take their own mutex (`Local\Agent5RunNight-dry-<tag>`, L73), so they can't block the real launch (`Local\Agent5RunNight-real`, L78).
- Agent 3's background scripts are still running:
  - s4b-queue.ps1: -LastLaunch 23:10, -GamesClosed 23:25;
  - hostload.ps1: -Until 23:40;
  - postcheck.ps1: -Until 23:59.
  - I asked Agent 3 to confirm all three are gone by 23:50.
- Board #19 for Agent 6: stage expect files for W9, W5b and W4c (paperwork only, by 23:45).

### 22:57 - Agent 1: native4b map check AGREE; PSO cold start
- Agent 2's subagent ran its own map check of native4b, and it agrees with Agent 2's (`build/agent2/s4b/checks/sub2/`, mapcheck-native4b-sub2-vs-agent2.txt A31BAFA1BFB226DC).
  - 109 hooks, the same as native4-bin.
  - The +2 publics are C1 v3's `BlockPhysicalProtectKeepWatch` import pair.
  - The only other change is the GPU fingerprint string in pipeline_library.cpp.obj (9b40acbb... replaces 5e3ff55d...).
- **Morning note:** native4b's first start is PSO-cold. Its new fingerprint makes it reject native4's native-pso-recipes.bin / native-pso-seed.bin (pipeline_recipes.h:247-256) until it records them again.
  - Re-pin rows: don't read boot time or PSO/stall lines from the first native4b run. Agent 4 is checking REPIN.md §3.
  - W8a (Monday): its warm-up run must be a native4b run. Tell Agent 8 when it plans Monday.
  - Open question to Agent 2: do the two files live next to each bin, or in one shared place? If shared, any window that mixes native bins with different fingerprints needs a warm-up after each bin switch.

### 23:00 - Agent 1: PSO cache question settled (corrects the 22:57 morning note); day-draft status
- I read the code (`DimensionsRecomp/rexlego/src/gpu_native/pipeline_library.cpp`). Every file path is relative to the exe's own folder:
  - `cache\native-pso.bin` (L99-105) is the driver blob. It isn't keyed by our fingerprint; the driver rejects a blob from another driver or adapter.
  - `cache\native-pso-recipes.bin` (L151) is checked against the fingerprint. On a mismatch the game logs "ignoring invalid or incompatible pipeline recipes", starts empty, and its next save replaces the file (L502-510, L529-550).
  - `native-pso-seed.bin` (L152) and `native-pso-seed\*.bin` (L483-500) are also checked against the fingerprint. The game only reads them; it never rewrites them.
- The runner makes a fresh run folder for every run (run-timing.ps1 L151). It copies cache files in only when the arm sets seed_cache (L138-173).
  - The re-pin matrices and W8a4 don't set seed_cache, and neither native4-bin nor native4b-bin has a seed file or a cache folder.
  - So **every run starts PSO-cold on both bins**, by design, and the warm-up absorbs it. The new fingerprint changes nothing for the re-pin or for W8a as staged.
  - **No REPIN.md change is needed.** This corrects my 22:57 note, and I told Agent 4.
  - For the future: any native4b arm with seed_cache must use a seed recorded by native4b. A native4 seed would get its recipes rejected, though its native-pso.bin would still load.
  - Agent 2 doesn't need to run the grep in the morning.
- Agent 5's day draft:
  - test-day.ps1 passed 25/25 at 22:54 on run-day.ps1 D86F6DE0 and launcher-ctl.ps1 43EC1AB7. It made 2 -PlanOnly calls and wrote nothing under bench\agent5\launch.
  - The night launcher ignores new files under bench\agent5\. It pins only run-night.ps1, RUN-NIGHT.cmd and the bench\agent8\run files, and writes only to bench\agent5\launch\status.
  - The install folder will be bench\agent5\day\. Day sessions write their status to bench\agent5\day\status, so Agent 12's read-out must look there too.
  - Hashes due by 23:35.
- 23:01: Agent 3 stopped its s4b queue, postcheck and hostload at 22:56. Nothing of Agent 3's runs tonight, and no game or compiler is running. Board #2 (Agent 3) and #9 (Agent 10) are done; Agent 10 rated gate B PASS for W6 (b2r row 43/§42). Morning queue: f10a, then f10b, then rpb0/rpm4, gated by marker files build\agent3\s4b\ready-later + ready-quiet. Agent 3 creates them when I give the word after the windows. I told Agent 3 the PSO note needs no action.

### 23:18 - Agent 1: user answers (23:16)
- **Monday:** the user is available all day, so there's no leave or return time. Daytime windows still need the laptop untouched; I asked whether it can sit idle in blocks.
- **Defender exclusion: added** (S4-DRAFT §4a Q3 / FINDINGS Q3: answered). MsMpEng was at 0% over 5 s at 23:17.
  - Tonight's windows run with the exclusion. Comparisons inside a window are unaffected; comparisons with W4b/W5 and older windows get a caveat.
  - Agent 11 should note this at its next S4-DRAFT refresh.
- **NVIDIA overlay:** the user thinks it was already off. At 23:17, NVIDIA Overlay x5, nvsphelper64 and PresentMonService were running, all at 0% CPU with no game running. Earlier, PresentMon used ~1 core during game runs.
  - Turning it off is optional and up to the user. Whatever its state at the double-click, it's the same for every arm tonight.
- I explained the screenshot check (#1) and the pop-in question (#33) to the user and am waiting for the answers.
- Also from 23:00-23:12:
  - #10 Agent 11 done: S4-DRAFT A95013AC, FINDINGS 9799EABB, GO-CHECK OK.
  - #19 Agent 6 done: build/agent6/wnight/ expect-w9 (base off), expect-w5b (d11) and expect-w4c (d0), plus the RUN-*-LOGDIFF.cmd files. In W9, the off arm must show NO init line (gpu_wait_backoff.cpp L141).
  - #18 Agent 9 done: CG26 check kit; the #21 pre-read passes 4/4.
  - Agent 6: all 4 finding-10 hangs ran under Agent 2's -j8 build (20:53:30-22:39:52). In gate B, host-GPU waits match memexport syncs almost one for one (696/698, 2708/2736), with memexport full-buffer at 0, so P2c=0 doesn't mean no syncs. That supports the after-S4 memexport-sync candidate.
- 23:19: #4 Agent 5 done. Night files re-hashed at 23:16, unchanged (16B90FA8 / D7A0362B / 0058C8F6); no status\ folder and no WINDOW-* file. Dry-run tests 40/40 PASS. Day draft: run-day.ps1 D86F6DE0, launcher-ctl.ps1 6DDE3150, RUN-DAY.cmd 4B5489B4, STOP-LAUNCHER.cmd CE27332F, README-DAY.md 9D131EB1; day tests 27/27 PASS at 23:11:52; the review request went to Agents 10 and 11. No more dry runs tonight. **Note:** the W6 GO line in Agent 5's summary (repeats=3) is its stale 22:08 handoff. The line in force is Agent 8's final one in build/agent1/night/GO-W6.txt (repeats=5, 21 runs; Agent 11's GO-CHECK OK).

### 23:25 - Agent 1: launcher FROZEN; user answers (23:24)
- **Freeze check at 23:24:43:**
  - HOLD, GO and STOP are absent.
  - All 3 files MATCH: run-night.ps1 16B90FA8 (mtime 22:11:21), RUN-NIGHT.cmd D7A0362B (22:32:59), README.md 0058C8F6 (22:12:38).
  - The folder holds only those 3 plus the launcher's own status-dryrun\ (last write 22:32:21). No status\ folder.
  - The hold manager (pid 25948) is alive. No build, game, launcher or runner process. Free RAM 12.4 GB.
  - GO files ready: W6 (repeats=5), W9 (4), W5b (6), W4c (6).
  - Reviews: Agent 10 SAFE (b2r row 41/§40), Agent 11 SAFE (REVIEW.md), GO-CHECK OK. The STOP smoke test gave exit 2.
  - **The set is frozen.** Any change needs a new delta read from Agent 10. Told Agents 5, 10 and 11.
- **User answers:**
  - **#33 pop-in: YES, as an optional feature** (opt-in, off by default). #33 and #34 stay in scope. They need Agent 6's implementation, Agent 10's rating, a build, and the user's look at the pop-in on a visible desktop.
  - **Monday: the laptop can sit untouched**, so day sessions run through RUN-DAY once the day draft is rated and installed in bench\agent5\day\.
  - **#1 screenshot check: Monday**, when the user messages that they're free for an hour. Stage the kit in the morning. If #33 is built and rated by then, do the pop-in look in the same hour.
  - Before that hour starts, no timed window may be running: let it finish, or stop it cleanly.


### 23:50 - Agent 1: user started RUN-NIGHT; user in bed
- The user double-clicked RUN-NIGHT.cmd at 23:47:19 and said "bed" at 23:47:48.
- Check at 23:49:37: real launcher pid 19960 (no -DryRun), state waiting-for-go since 23:47:20, heartbeat 23:49:23, deadline 07:30, gos_read 0. Screensaver None, keep-awake ON, Quick Edit off.
- HOLD, GO and STOP are absent. No build, game or runner process.
- A "dry-run pid 7032" in that check was my own shell matching its own filter text (gone 10 s later). Process checks now exclude $PID.
- Next: pre-go W6 just after 00:00, then GO W6 if READY. Order: W6, W9, W5b, W4c.
- 23:53: the user asked about lowering the screen brightness (Fn+F6). Told them it is fine before 00:00 and to leave it alone after that: on AC, the backlight does not draw from the CPU power limit, and a level that stays the same all night affects every arm equally. Do not turn the display off, lock, sleep or close the lid.
- 23:56: the user will wake **closer to 11:00** and offered more testing if the change is quick.
  - No launcher change: run-night.ps1 is frozen, and -StopAt/-StartBy are dry-run hooks (run-night.ps1 L65), so a later end means a code change plus a new double-click. The running launcher still ends at 07:30 (latest window start 06:45).
  - The rule that windows end by ~04:00 (PROPOSAL L24) only existed so builds and tests would finish before 07:30. With the user up at ~11, the launcher time from ~03:40 to 06:45 can take a **second pass** of any window that is too close to call (same GO line). run-matrix.ps1 makes a new yyyyMMdd-HHmm folder each run (L447-449), and run-night.ps1 has no already-ran check, so a second pass cannot overwrite the first. Latest GO for a second pass = 07:30 - 10 min margin - 10 min gate - runner (W6/W9 06:22, W5b 06:26, W4c 06:40). pre-go.ps1 needs those entries first.
  - Agents start builds and tests after the last window. RUN-DAY runs when the user is up (~11:00). The morning summary will be waiting for the user.

### 01:05 - Agent 1: W6 done; GO refusal fixed (screensaver value)
- **00:03:40 GO refused:** `run-matrix.ps1 -PlanOnly exit 1`.
  - Cause: at 23:47:20 the launcher's Set-ScreensaverNone (run-night.ps1 L461-467) removed HKCU\Control Panel\Desktop SCRNSAVE.EXE (it was ''). run-matrix.ps1 L417 reads `$scr.'SCRNSAVE.EXE'` under Set-StrictMode -Version 2 (common.ps1 L4), which throws when the value is missing.
  - Dry runs never change the screensaver, so the 40/40 tests could not catch this.
  - Fix at 00:05:37, with no launcher or pinned file touched: re-created SCRNSAVE.EXE = '' (the user's saved value, status/screensaver-saved.txt). ScreenSaveActive stays 0, so the screensaver is still None.
  - PlanOnly then exited 0 (21 runs, ~48 min, "screensaver none"). GO re-written 00:05:45, ACCEPTED 00:06:00.
  - **Morning todo (Agents 5 and 8, then a delta read by Agents 10 and 11), before RUN-DAY and Tuesday night:** either run-matrix L417 reads the value via PSObject.Properties, or the launcher sets SCRNSAVE.EXE to '' instead of removing it.
  - run-day.ps1 probably has the same code. The night launcher puts '' back at 07:30, and the next launcher start removes it again.
- **W6 (00:09:02-00:51:52, 42.8 min):**
  - Runner exit 0: 21/21 OK, 20 scored, 0 excluded. Gate STRICT (MsMpEng 0.00); bins unchanged; out build/agent8/matrix/20261123-0009.
  - Runner summary (not the formal readout): s0 2.44 ms median (385 fps, 2.50 cores); p2 2.47 (386 fps); p2f 2.45 (388 fps).
  - **p2fc 2.16 ms (466 fps, 2.28 cores): -11.8 % median frame time, +21 % fps, -0.22 core vs s0.**
  - C1 = p2fc - p2f per round: -0.06, -0.16, -0.30, -0.30, -0.28 ms, so p2fc was faster in 5 of 5 rounds.
  - The runner says "within noise" only because s0's band is +-21.4 %: s0 r1 ran at 2.08 ms, and round 1 was faster for every arm (likely thermal).
  - P2 alone and fix (i) alone show no change.
  - The formal readout (GPU Commands ms/f from threads.csv, R3 pairs) is for Agents 7 and 8 in the morning.
- W9 GO next (01:05).

### 01:52 - Agent 1: W9 done (back-off sweep)
- **W9 (01:08:53-01:51:23, 42.5 min):** runner exit 0, 21/21 OK, 20 scored, 0 excluded. Gate STRICT (MsMpEng 0.00); bins unchanged; out build/agent8/matrix/20261123-0108.
- Runner summary (not the formal readout), as median ms / fps / CPU cores:
  - off 2.46 / 386 / 2.51 (ref); q0 2.48 / 387 / 2.49 (no change).
  - **q125 2.31 / 389 / 1.82; q250 2.31 / 389 / 1.77; q500 2.31 / 390 / 1.72.** That is 0.69-0.79 core less (-27 to -31 %), fps unchanged (+1 %), median -6 %, p99 -7 to -10 %.
  - p99 / p99.9: q125 4.47 / 5.01, q250 4.50 / 5.11, q500 4.62 / 5.52 ms (off 4.98 / 5.63). q500 saves the most CPU, but its tail is a little worse than q125/q250.
  - This matches the ~0.7-core estimate.
  - The quantum pick goes to the formal readout (Agents 7 and 8) and Agent 6's W9 logdiff (off must have no back-off init line; each q arm exactly one ON line).
- W5b GO next (01:52).

### 02:36 - Agent 1: W5b done (timer wait modes)
- **W5b (01:55:28-02:33:54, 38.4 min):** runner exit 0, 19/19 OK, 18 scored, 0 excluded. Gate STRICT; bins unchanged (devoff4-bin); out build/agent8/matrix/20261123-0155.
- Runner summary (not the formal readout), as median ms / fps / CPU cores:
  - d11 (spin) 2.51 / 385 / 2.54 (ref).
  - **d11t (blocking) 2.51 / 384 / 2.31 (-0.23 core, -9 %).**
  - **d11p (precise) 2.50 / 385 / 2.34 (-0.20 core, -8 %).** d11p has the tightest spread (4.4 %) and a slightly better p99 (4.78 vs 4.85).
  - fps unchanged in both.
- Same direction and order as W5 (d11t -13.7 %, d11p -12.2 % game CPU), but smaller. The formal readout and Agent 6's W5b logdiff decide d11t vs d11p.
- W4c GO next (02:36).

### 03:09 - Agent 1: W4c done (codegen B repeat); second passes start
- **W4c (02:39:46-03:05:58, 26.2 min):** runner exit 0, 13/13 OK, 12 scored, 0 excluded. Gate STRICT; bins unchanged (d0 = devoff2-bin, B = devoffB-bin); out build/agent8/matrix/20261123-0239.
- Runner summary (not the formal readout), as median ms / fps / CPU cores:
  - d0 2.47 / 385.4 / 2.53 (ref). Its band is +-10 % only because the cold run (2.19) and r1 (2.25) were fast: the same first-runs-fast pattern as W6.
  - **B 2.50 / 383.9 / 2.60: median +1.3 %, fps -0.4 %, +0.07 core.** p99 4.91 vs 4.94, p99.9 5.62 for both. Runner verdict: within noise.
  - Per round, B - d0: +0.23, +0.04, +0.05, -0.00, +0.01, +0.05 ms, so B was slower in 5 of 6 rounds and tied in 1.
- **W4b's B +6.0 % fps hint did not repeat:** codegen B shows no gain here. The keep/drop call waits for the formal readout (Agents 7 and 8) and Agent 6's W4c logdiff.
- **Second passes start now** (plan from 23:56: the user wakes ~11, so the old latest-GO-by-04:00 rule no longer applies).
  - pre-go.ps1 line 11 is now W6 06:22, W9 06:22, W5b 06:26, W4c 06:40 (07:30 - 10 min margin - 10 min gate - runner estimate; W4c is also under the 06:45 cap).
  - Same GO files, one at a time: W6 -> W9 -> W5b -> W4c. Expected ends: W6-2 ~03:56, W9-2 ~04:43, W5b-2 ~05:26, W4c-2 ~05:58.
  - Any window whose GO would be past its latest GO is skipped. Agent 8 pools or compares the two passes in the formal readout.
  - Agent work (Agent 3's quiet-host rows, Agent 2's builds, Agent 5's screensaver fix) starts after the last window.

### 03:58 - Agent 1: W6-2 done (second pass); W9-2 GO
- **W6-2 (03:13:22-03:56:11, 42.8 min):** runner exit 0, 21/21 OK, 20 scored, 0 excluded. Gate STRICT; bins unchanged; out build/agent8/matrix/20261123-0313.
- Runner summary (not the formal readout), as median ms / fps / CPU cores, with the first pass in brackets:
  - s0 2.48 / 385.0 / 2.53 [2.44 / 385 / 2.50] (ref). Its band is +-8.4 %, again only because the cold run and r1 were fast.
  - p2 2.47 / 385.2 / 2.53 [2.47 / 386 / 2.52] and p2f 2.45 / 385.9 / 2.55 [2.45 / 388 / 2.56]: no change, as in the first pass.
  - **p2fc 2.13 / 469.8 / 2.26 [2.16 / 466 / 2.28]: median -14 %, fps +22 %, -0.27 core vs s0. Runner verdict this time: FASTER (outside noise).**
  - C1 = p2fc - p2f per round: -0.34, -0.27, -0.32, -0.28, -0.32 ms. p2fc was faster in 5 of 5 rounds again, so 10 of 10 over both passes.
  - Tail: p2fc p99 5.04 vs s0 5.00 (flat), p99.9 6.49 vs 5.74. p2f's p99.9 is 6.40 too, with one >33 ms frame in r5. The formal readout should check whether fix (i) or C1 adds rare slow frames.
- The second pass confirms the first: p2fc (P2 + fix (i) + C1 v3, verify off) is tonight's only frame-time win. W9's back-off and W5b's wait modes save CPU only.
- W9-2 GO next (03:58).

### 04:46 - Agent 1: W9-2 done (second pass); W5b-2 GO
- **W9-2 (04:01:16-04:44:08, 42.8 min):** runner exit 0, 21/21 OK, 20 scored, 0 excluded. Gate STRICT; bins unchanged; out build/agent8/matrix/20261123-0401.
- Runner summary (not the formal readout), as median ms / fps / CPU cores, with the first pass in brackets:
  - off 2.46 / 384.9 / 2.50 [2.46 / 386 / 2.51] (ref; band +-5.8 %). q0 2.47 / 385.5 / 2.47 [2.48 / 387 / 2.49]: no change.
  - q125 2.39 / 378.9 / 1.96 [2.31 / 389 / 1.82]: -0.54 core, fps -1.6 %.
  - q250 2.37 / 382.8 / 1.95 [2.31 / 389 / 1.77]: -0.55 core, fps -0.5 %.
  - **q500 2.32 / 389.2 / 1.80 [2.31 / 390 / 1.72]: -0.70 core (-28 %), fps +1.1 %, median -5.9 %. p99 4.68 vs 4.99, p99.9 5.40 vs 5.58. Runner verdict: FASTER (outside noise).**
- q125 and q250 were less steady this pass:
  - q125 r1 and r3 ran at 2.13-2.15 cores with ~18.3k frames (other runs ~19.2-19.5k) and p99 5.1-5.4.
  - q250 r1 and r2 had ~18.9k frames (r1 at 2.11 cores).
  - q500 kept a normal frame count in all 4 runs (one run at 2.03 cores).
- Over both passes q500 saves the most CPU (0.70-0.79 core) with no fps loss, and this pass it also had the best tail. Lean: q500. The quantum pick stays with the formal readout (Agents 7 and 8, 8 runs per arm pooled) and Agent 6's W9 logdiff.
- W5b-2 GO next (04:46).

### 05:33 - Agent 1: W5b-2 done; W4c second pass skipped; wrap-up for the break (GitHub)
- **W5b-2 (04:51:58-05:30:42, 38.7 min):** runner exit 0, 19/19 OK, 18 scored, 0 excluded. The quiet gate held the start back 3 min (CrossDeviceService 0.81/0.87/0.68 core at 04:46-04:49), then passed STRICT. Bins unchanged (devoff4-bin); out build/agent8/matrix/20261123-0451.
- Runner summary (not the formal readout), as median ms / fps / CPU cores, with the first pass in brackets:
  - d11 (spin) 2.51 / 385.2 / 2.56 [2.51 / 385 / 2.54] (ref; band +-1.5 %).
  - d11t (blocking) 2.52 / 382.0 / 2.35 [2.51 / 384 / 2.31]: -0.21 core, fps -0.8 % (r1 and r2 were slow: 2.65 and 2.58 ms).
  - **d11p (precise) 2.51 / 385.5 / 2.35 [2.50 / 385 / 2.34]: -0.21 core (-8 %), fps unchanged.**
- Over both passes, d11t and d11p save the same ~0.2 core. d11p kept fps in both passes; d11t lost 0.8 % this pass. Lean: d11p. The formal readout and Agent 6's W5b logdiff decide.
- **The user (04:55, 05:01):** a break of a few days to a week is coming (other ideas, hopefully more processing power). A 2-hour grace period starts ~11-12 to finish up; aim to finish by ~13:00. The work must be committed to GitHub: https://github.com/rishabh-mohan/DimensionsRecomp and https://github.com/rishabh-mohan/rexglue-sdk.
- **W4c second pass skipped** so the wrap-up can start now (codegen B showed no gain in the first pass). The launcher stays idle until it exits at 07:30. No more timed windows before the break.
- Wrap-up plan:
  - Git (Agent 1): commit onto a new branch per repo (perf/s4, not main), following each repo's .gitignore. Perf notes, bench scripts/matrices and small readout reports go in perf/ on the DimensionsRecomp branch. Push without force. Commit again at the end of the grace period. Agents commit only through Agent 1.
  - Readouts: Agents 7 and 8 (formal, both passes), Agent 6 (logdiffs), Agent 12 (gates).
  - Agent 3: quiet-host f10a/f10b rows (finding 10).
  - Agent 11: FINDINGS/S4-DRAFT plus perf-notes/RESUME.md (state, next steps, restart in a few days to a week; a new PC needs new baselines).
  - Agents 5 and 8: stage the screensaver/StrictMode fix; install it after the launcher exits at 07:30.

### 05:44 - Agent 1: S4b/S4c code pushed to GitHub; wrap-up tasks sent

- User (04:55-05:01): commit to GitHub (rishabh-mohan/DimensionsRecomp and rishabh-mohan/rexglue-sdk, both public forks); a break of a few days to a week; a 2-hour grace period from ~11-12. Aim: everything committed and a resume doc by ~13:00.
- Code: the 16 S4b/S4c files in build/agent2/s4b/HASHES.txt were copied from build/agent2/snap1 into the live trees after a hash check (live == S4a "before" and snap1 == S4b "after" for all 16; live == "after" after the copy). Commits on perf/opt, pushed to mine without force: rexglue-sdk 5350b1d (13 files; its upstream is now mine/perf/opt) and DimensionsRecomp b0bd3b4 (memory_watch.cpp, CMakeLists.txt, new gpu_wait_backoff.cpp, SDK pointer). ls-remote shows both.
- Third-party worktree changes stay uncommitted. Both can be rebuilt from tracked files: plume via tools/gpu-aot/prepare_plume.py + tools/gpu-aot/patches (winsdk-compat holds S1+p2), simde via rexglue-sdk/scripts/prepare_simde.py + rexglue-sdk/patches/simde-native-m64-stream.patch.
- Notes/scripts/results are not pushed. At 04:57 I told the user they would go to a private repo, but both repos are public. I'm staging an export and will ask the user when they wake: a public perf/ folder, a private repo they create, or local only.
- Wrap-up tasks sent: readouts (7, 8), logdiffs + dumpstacks (6), gates (12), quiet-host f10a/f10b (3), FINDINGS/S4-DRAFT/RESUME.md (11), SCRNSAVE fix staged and installed after 07:30 (5; reviews by 8 and 10), commit check + pending-diff inventory (2), screenshot kit (4), and a HANDOFF.md from every agent. No builds or timed runs this morning. The old night cron (task-139) is replaced by a wrap-up cron.


### 06:05 - Agent 1: day-draft rating; run-day regen folded into #26

- Agent 10 rated the day-session draft SAFE-IF (build/agent10/t27/day-draft-rating.md). Conditions: (1) regenerate run-day.ps1 from the SCRNSAVE-fixed run-night.ps1 (the current run-day.ps1 D86F6DE0 has the same bug, so the first day GO would be refused); (2) install per README-DAY L136-139 only after the night launcher has exited, then compare hashes; (3) Agent 11 rates it too. Hashes match the 23:19 list; tests 27/27 PASS. NITs N1-N4 and N6 do not block (N1: absolute user-name paths in run-day.diff L1-4, fix before publishing).
- No day runs before the break. Agent 5 does (1) staged only in build/agent5/, after the SCRNSAVE install (not installed into bench/agent5/day); Agent 10 delta-reads it; Agent 11 lists (2), (3), N1 and N6 in the RESUME.md open items. The install and Agent 11's rating wait until after the break.
- 06:03 check: launcher pid 19960 and hold manager 25948 still running (both exit 07:30); game pid 32896 since 05:58 is Agent 3's f10 rows; Agent 5's scrnsave tests write only a scratch key (HKCU:\Software\Agent5-scrnsave-test), never Control Panel\Desktop.

### 06:35 - Agent 1: 06:30 check; wrap-up results so far

- Done: #30 Agent 9 (HANDOFF; BACKOFF-DEFAULT-ON.md design; W9 clock check: pass 2 had 4/21 lowclk runs, 04-q125-r1, 05-q250-r1, 10-q500-r2, 12-q125-r3, read as host-driven but not proven; forwarded to Agent 7). #24 Agent 12: all 7 night dirs PASS (both W6 with the known G8 / finding-10 WARN); G12 midnight bug fixed; C1 v3 is byte-identical to 5350b1d. Caveat: W5 ran best_efficiency, the night windows best_performance.
- Agent 6 night logdiffs: 135 runs exit 0, 0 STUCK-LOCK, 0 dumps; only the expected proof lines differ by arm; W9 env matches matrix.json in all 42 runs. NOTEs: 6 runs lack 'Execution complete' (exit race); W9 0128-off-r2 hit the 3 s shutdown watchdog (exit 0, first sighting). build/agent6/wnight/RESULTS.md.
- Agent 3 f10 (quiet host, untimed, devoff4b-bin): f10a and f10b PASS, no hang. Worst frame 2.9 s against the 5 s detector; the same sync-heavy frames took 5-20x less per wait than gate B under -j8 (0.98 vs 6.05 ms; 0.29-0.37 vs 1.79 ms), so a starved host, with a small margin. rpm4 PASS. Second pair approved: f10a2 started 06:32, all runs end by 07:20; the n=2 summary goes to Agents 6 and 11. Agent 12 adds a 2-line pointer to its HANDOFF.
- Agent 10: SCRNSAVE delta SAFE (build/agent10/t27/scrnsave-delta.md); day condition 1 met in staged form (run-day B67EBD6C from run-night 565D30D4). Item #21 (s4-t1) rating in build/agent10/t27/r21-s4t1.md: (a) SAFE, (b) SAFE-IF with 5 conditions incl. the new F-CA (a th2-only deadlock path that exists without #21, not seen at runtime), (c) ACCEPTED. F-CA goes to the RESUME open items; Agent 7 records it under MP4 gap 2.
- Export: export_perf.py now scrubs each copy (workspace path -> <workspace>; other profile paths and the account name -> <user>; plain, JSON-escaped and file:/// forms) and counts leftovers; checked on a sample. The full re-run waits until Agent 3's quiet runs end. Personal-schedule mentions sit in about 47 exported files (session log, FINDINGS, S4-DRAFT, agent notes): too spread out to cut, so it goes into the notes question for the user.
- Machine 06:31: launcher 19960 and hold manager 25948 up until 07:30; no HOLD.

### 07:06 - Agent 1: f10 n=2 done; fresh clone verified; export scrubbed; my HANDOFF

- Done since 06:35: #28 Agent 2 (COMMIT-CHECK PASS; PENDING-DIFFS.md; old task #1 closed as DEFERRED, CTR/CG26 bins unbuilt, steps in its HANDOFF S4.1); #22 Agent 6 (gate B dumpstacks S7.3, quiet-host answer S7.4, night logdiffs, #33 pop-in staged in build/agent6/s33-popin/, cvar d3d12_pipeline_creation_no_wait default OFF, apply --check OK on 5350b1d, not built); #29 Agent 4 (screenshot kit build/agent4/screenshot-kit/README.md, about 25 min, user at the visible desktop); #23 Agent 3 (f10 n=2: f10a, f10a2, f10b, f10b2 all PASS; 0/4 hung on the quiet host vs 4/6 under -j8, p=0.07; rpb0 and rpm4 PASS; queue stopped, STOP file in place, last game 06:47:26).
- Agent 10: RESUME interim review R1-R32 (build/agent10/t27/resume-review.md; 3 wrong facts R20-R22, restart gaps R30-R32); SCRNSAVE install tooling SAFE (install-scrnsave.ps1, day-update.ps1). Pointed Agent 11 at the review; R19 (scrub) done on my side.
- Export re-run 07:02 with the scrub: 4529 files, 38.6 MB, 8319 edits in 1411 files, 0 files still holding the account name. Still staged, not pushed.
- Fresh clone test (https, scratch folder outside the workspace): DimensionsRecomp perf/opt b0bd3b4 and the SDK submodule 5350b1d come from the forks fine. thirdparty/plume fails ('not our ref ceaeeee0', the upstream gitlink is not on zolaware/plume); fetching the pin e0c8871 by sha, then prepare_plume.py and prepare_simde.py, gives the same git status as the live tree, and the 4 patched files are byte-identical to the live ones. Steps in build/agent1/HANDOFF.md section 3 (R32).
- Wrote build/agent1/HANDOFF.md (first version; the final pass adds the readout verdicts).

### 07:34 - Agent 1: night launcher and hold manager ended cleanly
- Launcher pid 19960 ended 07:30:14 at its deadline (exit 0): screensaver restored to the values saved at 23:47 (ScreenSaveActive=0, SCRNSAVE.EXE ''), keep-awake released. Hold manager (task-135) ended 07:30:04 with a clean HOLD log for all 7 windows; no HOLD file now.
- The launcher never touched the power overlay: its log records only the scheme (Balanced) at each window start. The AC overlay is Best performance (ded574b5) as it was all night; W4b/W5 ran Best power efficiency, so night-vs-W4b/W5 numbers are leads only (G11).
- Host quiet: no game, build, runner or launcher process. Cancelled my 07:33 one-shot (all its items done: export ran 07:02, f10 ended 06:47). Told Agent 5 it may install the SCRNSAVE fix (#26) once Agent 8 has read the delta.

### 07:40 - Agent 1: all four night readouts final (ahead of the 10:00 target)
- W6 (Agent 8, build/agent8/readout/w-followup/W6.md; Agent 7's headlines-W6-W4c.md agrees): p2fc vs s0 -10.3 % [-13.6, -6.9] median, +18.0 % [+14.1, +22.0] fps, -0.249 cores [-0.303, -0.195]. All from C1: p2fc < p2f in 10 of 10 rounds. p2 and p2f null (p2f +0.04 cores, lead). Leads: heavy frames +2-3 %; no C1-only arm; keep-watch timed with verify off. 42 runs clean, p2fc 0 frames > 16.7 ms.
- W4c (Agent 8, W4c.md): codegen B no gain, +2.6 % [-1.2, +6.5]; don't adopt B (maybe ~1 % slower, lead).
- W9 (Agent 7, build/agent7/readout/W9.md; Agent 8 recompute AGREE, 880/912 claims, 0 sign flips): q500 -0.75 core [-0.86, -0.64] (-30 %), no p99 / 1 % low loss; drop q0; q125/q250 instability host-triggered, not an arm defect. Frame time: CIs cross 0.
- W5b (Agent 7, W5b.md): d11p narrowly over d11t; both ~-0.2 core (~-8 %); d11t fps -1.1 % [-2.1, -0.0] and the only stutter cluster; W5's d11t tail lead not reproduced.
- Leans confirmed: p2fc, q500, d11p; drop codegen B and q0. None is default-on yet; they were timed separately (W5b on S4a).
- Agent 10 rated #33 (build/agent10/t27/r33-popin.md): OFF SAFE, ON opt-in SAFE-IF (4 conditions), S1 first test bin without hunk #5, S2 diagnostic (d) as a 5th precondition. N4 (stale PENDING-DIFFS rows) -> task #31 for Agent 2. Asked Agent 6 to record the rating in s33-popin/DESIGN.md (docs only).
- Morning summary drafted: brain artifact morning-summary.md (finalize ~10:45).

### 07:56 - Agent 1: SCRNSAVE fix installed and tested; #20, #21, #26, #31 done
- Agent 5 (#26 done): installed 07:33:57, after the launcher exit and Agent 8's and Agent 10's reads. run-matrix.ps1 FEDCEB13 -> 1A522CDF (L417-419 read through Get-P; a missing value reads as ''). run-night.ps1 16B90FA8 -> 565D30D4 (sets '' instead of deleting; restore puts back the saved state, including absent). Launch README 0058C8F6 -> B7CEBD63. Post-install: test-scrnsave -Set installed -E2E 45/45 (07:34:45); test-day 27/27 after a test-only d-real-4 fix; launcher dry-run go group 16/16 with a new test-only -StopAt. status/pins.txt is only a record: the next start re-pins itself. Day draft regenerated (run-day.ps1 B67EBD6C), staged only; bench/agent5/day does not exist. The RUN-NIGHT.cmd console (cmd pid 35516) still sits at its final pause; left for the user to close.
- Agent 8 (#20) and Agent 7 (#21) done, HANDOFFs written. Agent 7's W9/W5b are rev 1 (checker: 11 wording/citation fixes, no number wrong). Agent 2 (#31) refreshed PENDING-DIFFS (40E10D19) and HANDOFF S4.3. #19 still has no RATE-REQUEST -> task #32 for Agent 7 (docs only, by 11:30; Agent 10 rates it after the break).
- Open: #25 Agent 11 (RESUME, 12:00), #27 Agent 10 (reviews), #32 Agent 7.

### 08:39 - Agent 1: RESUME final and checked
- perf-notes/RESUME.md is final: sha256 9DA0A4C372399DC4..., 51,347 B, 381 lines (08:09, updated 08:18 for #19's rate request).
- Agent 10 checked it (build/agent10/t27/resume-review.md, section Final version): accurate on everything checked, R33-R38 resolved, day-launcher item complete, public-safety grep 0 hits, no BLOCKER or SHOULD. One NIT (F1) for Agent 11 at L325 and facts-perfopt L112: the 07:33:42 refusal was install-scrnsave's process check matching pid 33304, not the launcher (19960 had ended at 07:30:14).
- Stale HANDOFF lines relayed (conditionally, in case Agent 10's note didn't reach them): Agent 5 L16 and L44-46 (Agent 10's day-draft check finished 07:56, so condition 1 is closed); Agent 8 L74 (facts-perfopt L110 was fixed at 08:15).

### 08:47 - Agent 1:
- build/agent1/HANDOFF.md rewritten (43E964EC, 185 lines, ASCII, LF): task numbers from #33, SCRNSAVE install and pin facts, day-draft conditions, my after-break items (notes destination, native4b pin announcement, #19 and day-draft ratings, screenshot check), the four readout verdicts and the wrap-up table with HANDOFF prefixes. The final pass (~12:30) adds the notes destination and the git state.
- Morning summary artifact updated: start-here link to perf-notes/RESUME.md; Agent 7, 10 and 11 rows.
- Agent 10: RESUME 7616A164 is final from its side (build/agent10/t27/resume-review.md A9049772, section 'Update at 08:39').
- Task #32 done (Agent 7): build/agent7/s4-r1s2/RATE-REQUEST.md rev 1 (54789A6B, 498 lines). The same errors are still in FUNCTIONAL-ROWS.md L54, SOAK.md L11-12 and NOTE.md (RATE-REQUEST section 15); assigned to Agent 7 as task #33 (docs only, by 11:00). build/agent2/PENDING-DIFFS.md L40 and L128-129 still say the rate request is not written (dated 07:49); Agent 2 refreshes that after #33.

### 10:03 - Agent 1:
- Notes export refreshed (export_perf.py --copy at Idle priority, 10:01): 4617 files, 39.9 MB, 8412 scrub edits in 1418 files, 0 files still holding the account name. One file was flagged as disassembly and left out (build/agent9/b-clock/fq-show-829579D0.txt, EXCLUDED.tsv). Still staged only in build/agent1/perf-export/perf; nothing pushed. About 60 exported files mention the user's schedule (was about 47 at 07:02).
- build/agent1/HANDOFF.md section 5 and the morning summary updated with these numbers. Task #33 (Agent 7) in progress: its files changed at 09:04, 09:39 and 09:59.

### 10:11 - Agent 1:
- Task #33 done (Agent 7). RATE-REQUEST.md is now 1C2B8688A43ED4DC (README D1622FD9, Agent 7 HANDOFF AC4A9C93); FUNCTIONAL-ROWS BB05AAFD, SOAK F6A340A2, NOTE 58E8EA9F, CHECKS A5A8F777 (L24 warns about the git -C apply form), matrix-w7-draft 2A07C659 (JSON parses). s4-r1s2.diff 06B0D371 and SHA256SUMS 8A38FD9D unchanged. I checked that the facts RESUME L282-284 quotes are unchanged (41 + 10 min, soak checker not written, 13/17 runs, RR sections 1-16).
- Task #34 to Agent 2: refresh PENDING-DIFFS for #19 (rate request written; apply form). My HANDOFF: task numbers continue from #35.

### 10:18 - Agent 1:
- Task #34 done (Agent 2): PENDING-DIFFS.md 40E10D19 -> 640F3642 (dated L5 10:15; #19 rows say the rate request is written, not rated, and carry the snap1 apply trap; section 6 has the 4 source sha256s); HANDOFF.md C9A426E2 -> C3F02BF1 (L173). No open grid tasks; all agents idle.
- Stale-sha scan of RESUME, FINDINGS, S4-DRAFT, facts-perfopt and the HANDOFFs: only build/agent10/HANDOFF.md L72 quotes the 08:40 RATE-REQUEST (54789A6B) and says to re-hash first; left as is, noted in my HANDOFF section 6 item 3.
- My HANDOFF now 186 lines; morning summary final apart from the user's answers.

### 12:36 - Agent 1: final pass
- Git: DimensionsRecomp perf/opt b0bd3b4 and rexglue-sdk perf/opt 5350b1d, both equal to mine/perf/opt (git ls-remote at 12:31). git status shows only the expected plume and simde entries. Nothing new to commit; no push needed.
- Notes: no answer from the user by 12:30, so nothing is pushed. The export stays local in build/agent1/perf-export/perf (final run 12:31: 4617 files, 39.9 MB, 8412 scrub edits in 1418 files, 0 files with the account name, 1 disassembly file left out). Ask again after the break.
- Screenshot check: not done (no answer); after the break.
- Grid tasks #20-#34 all closed; all agents idle. All 11 agent HANDOFFs match the table in build/agent1/HANDOFF.md section 8; mine is final at ED74B042C2F90A24.
- Wrap-up cron cancelled. Project paused; it restarts in a few days to a week from perf-notes/RESUME.md.

### 13:52 - Agent 1:
- 13:49: the user chose option (a): the notes export goes into a public perf/ folder in DimensionsRecomp on perf/opt. Re-running the export, then committing perf/ plus a !/perf/ line in .gitignore on top of b0bd3b4 and pushing to mine. rexglue-sdk stays at 5350b1d; the plume and SDK pointers stay uncommitted. build/agent1/HANDOFF.md sections 2, 3, 5 and 6 (item 1) updated to match.
- 13:57: the pre-commit privacy scan of the export found 10 truncated lines in 2 files where a profile path was cut off part-way through the account name, so the scrub missed them. export_perf.py now also scrubs cut-off profile paths (TRUNC_RE, 10 unit cases pass) and counts them as leftovers. Re-run: 4617 files, 39.9 MB, 8423 scrub edits in 1418 files, 0 leftovers. The rest of the scan was clean: no tokens or keys, only public emails (an SDK copyright line, git@github.com), no IP addresses except 127.0.0.1, no MAC addresses, no UTF-16 or NUL files; the GitHub handle appears only in repo URLs, check scripts and the commit author name.

### 14:03 - Agent 1:
- Notes committed and pushed: DimensionsRecomp perf/opt c9e215f "perf: S4 sprint notes, scripts and results", on top of b0bd3b4. 4620 files changed, 773530 insertions: perf/ (4619 files from the 14:00 export; the MANIFEST hashes matched after the copy) plus the !/perf/ line in .gitignore. Push b0bd3b4..c9e215f, no force; git ls-remote mine perf/opt = c9e215f2e5c42836. git status shows only the expected plume and simde entries. rexglue-sdk unchanged at 5350b1d (= mine/perf/opt).
- The repo copy of perf/ predates this note and the hash lines in build/agent1/HANDOFF.md sections 2 and 5. Refresh it with the next notes commit (HANDOFF section 5).
