# Agent 6 handoff (2026-11-23, before the project pause)

All paths are relative to the workspace root. Agent 6 does perf investigation in the agy-grid:
- game.log logdiff kits for the timed windows;
- hang and minidump analysis (finding 10);
- attract-stall and pipeline-cache analysis.

## What I own

- `build/agent6/**`: my scripts, kits, outputs and staged (unbuilt) diffs. The layout is at the end of this file.
- `perf-notes/agent6-attract-stalls.md`: my running notes for the agy-grid perf work, §1-§17. The status note is in the middle, at "Agent 6 status note".
- Older Agent 6 notes from earlier sessions (reference only):
  - `perf-notes/agent6-native-aot.md`
  - `perf-notes/agent6-pipelines.md`
  - `perf-notes/agent6-async-pso-design.md`
  - `perf-notes/agent6-crash-triage.md`
  - `perf-notes/agent6-hang-triage.md`
  - `perf-notes/agent6-runspecs.md`
  - `perf-notes/agent6-session2-design.md`
  - There is also earlier material under `bench/agent6/`, e.g. `d3d12_library_probe.md`.
- I never commit or push; only Agent 1 does. None of my work is in the source trees.
  - The S4b/S4c code is on GitHub: rexglue-sdk perf/opt 5350b1d and DimensionsRecomp perf/opt b0bd3b4.
  - The live checkouts were at those heads on 2026-11-23 06:05.
  - The SDK's only tracked change is the `thirdparty/simde` submodule content, which isn't mine.

## State at stop

- Tasks #5, #13, #16 and #19 were done and accepted. Task #22 (this wrap-up) is done:
  - gate B dumpstacks;
  - the 7 night logdiffs;
  - the W9 env proof;
  - the optional #33 pop-in diff, staged and reviewed but not built (open item 7);
  - this file.
- Nothing is running: no processes, subagents or pending runs. Task #22 made no builds, timed runs or git writes.
- Nothing is staged for commit. The only code is the #33 diff, `build/agent6/s33-popin/s33-popin.patch`: opt-in, default OFF, **not built and not applied**. Its status is under "Open items" below.

## Results: where to look

| Topic | Where |
|---|---|
| W4b logdiff, every arm vs d0 (task #5) | notes §12; `build/agent6/w4b/out-20261122-1541/` |
| W5 logdiff, S3d→S4a, slow runs (task #13) | notes §13; `build/agent6/w4b/out-20261122-1756-vs-base/`, `out-20261122-1756-vs-s0/`, `check-1756-a/`, `check-1756-b/` |
| Finding-10 hangs: gate A, s4b-24/20, gate B (task #16 and #22) | notes §14 and §17; `build/agent6/hang/cp-state-gateA.md`; `build/agent6/hang/cp-state-s4b24-s4b20.md` (§7.3 is gate B; §7.4-§7.5 are the quiet-host answer); `build/agent6/hang/dumpstacks-*.txt` |
| W6 logdiff kit (task #16) | notes §15; `build/agent6/w6/README.txt`, `build/agent6/w6/expected-lines.md` |
| Night-window rules for W9/W5b/W4c (task #19) | notes §16; `build/agent6/wnight/README.txt` |
| Night logdiffs on 7 dirs, 135 runs (task #22) | `build/agent6/wnight/RESULTS.md`; notes §17 |
| Attract stalls, pipeline cache, S4 items, S11 runs (task #18 and earlier) | notes §1-§11 |

## Tools: how to rerun

Each tool refuses to run while `perf-notes/WINDOW-HOLD.txt` exists.

- **Logdiff kit:** `build/agent6/w6/w6_kit.py`, with one `expect-*.json` per window.
  - Wrappers, each taking a matrix dir such as `build\agent8\matrix\<dir>`:
    - `build\agent6\w6\RUN-W6-LOGDIFF.cmd`
    - `build\agent6\wnight\RUN-W9-LOGDIFF.cmd`
    - `build\agent6\wnight\RUN-W5B-LOGDIFF.cmd`
    - `build\agent6\wnight\RUN-W4C-LOGDIFF.cmd`
  - Exit codes: 0 = no FAIL, 1 = FAIL, 2 = usage error, 3 = HOLD file present. A run takes about 1 s.
  - The kit drives `build/agent6/w4b/w4b_logdiff.py` and `w4b_extra.py`, which import `bench/agent8/run/gate_logdiff.py` read-only.
- **W9 proof:** `python -B build/agent6/wnight/w9_envcheck.py [--out FILE] <matrix dir>...`. Its test is `python -B build/agent6/wnight/make_test_w9env.py`.
- **Kit tests:**
  - `build/agent6/w6/make_synth.py`: a synthetic STUCK/dump/FAIL folder.
  - `build/agent6/w6/test_stuck_parse.py`
  - `build/agent6/wnight/make_test_s4b17.py`
- **Dumps:** `python -B build/agent6/hang/dumpstacks.py <dmp> <out.txt> '<tid,tid,...>'`. Quote the tid list, or PowerShell turns it into numbers. It takes about 1 s.
- **Helpers in `build/agent6/hang/`:**
  - `threadcpu.py`: per-thread kernel/user CPU from threads*.csv.
  - `slowframes.py`: slow-frame line stats.
  - `handleinfo.py`: dump handles.
  - `peinfo.py`: PDB RSDS.
  - `gateb_check.py`, `base_owner.py`, `align.py`.
  - The method is in `cp-state-s4b24-s4b20.md` §7.2.

## Open items

1. **Finding 10** (hang in the L1 fence-wait poll, sub_83FAF180): answered for now as a starved host, not the GPU.
   - Agent 3's quiet-host runs, n = 2 per set (f10a, f10a2, f10b and f10b2; `build/agent3/f10/RESULTS.md`), had 0 hangs in 4 runs. Under the -j8 build, 4 of 6 runs hung (one-sided Fisher p = 0.07).
   - The same GPU work ran with round trips 5-30x faster than in gate B: 0.18-0.98 ms vs 1.79-6.05 ms per wait. The CPU-only part of the frame was shorter too. See `build/agent6/hang/cp-state-s4b24-s4b20.md` §7.4-§7.5.
   - The margin is small: the worst quiet frame was 2.89 s against the 5 s detector, and one run reached 3.99 s under the build without a hang. GPU clocks weren't logged. One more clean quiet pair would make p = 0.03.
   - All four hangs so far ran during a -j8 build. If a later run hangs, read the dump the same way (§7.2) and compare it with §7.3.
2. **Verify-mode CP kernel time.** Agent 12's suspect, not profiled: KeepWatchVerifyRecord → KeepWatchVerifyReadable → memory::QueryProtect (VirtualQuery plus a RegionSize walk) on every MakeRangeValid. See the cp-state doc.
3. **The memexport full-path readback sync** costs one fence wait per memexport sync. In gate B's frame #33131 that was 2708 waits for 2736 syncs, and P2 doesn't avoid it. It's a perf candidate; see cp-state-s4b24-s4b20.md.
4. **Shutdown watchdog, first sighting** (W9 `20261123-0108/runs/0128-off-r2`): `OnClosing` hadn't run 3 s after WM_CLOSE, so the 3 s backstop hard-exited (exit 0, timing valid). If it happens again, take a dump at about WM_CLOSE + 2 s. The code path is in RESULTS.md.
5. **Kit tweak:** treat a missing `Execution complete` as INFO when `Title terminated; hard-exiting process.` is present. It's a benign race, seen in 6 of 135 runs.
6. **Arms with no night runs:** W6 f and fc; W9 p1 and q250s (gate-only); W4c d11t and d3.
7. **#33 pop-in as an opt-in: staged, reviewed and rated by Agent 10; not built and not applied.** The files are in `build/agent6/s33-popin/`:
   - `DESIGN.md`: design, risks, test plan, and §10 on the rating;
   - `s33-popin.patch`: the rated patch (sha256 0D23024484CCDEE1…);
   - `CHECK.txt`.
   - **Cvar `d3d12_pipeline_creation_no_wait`:** bool, default false, `kRequiresRestart`.
     - It's latched in `PipelineCache::Initialize`. It only takes effect when `async_shader_compilation`, pipeline creation threads and bindless are all on.
     - It logs one INFO line when it takes effect, one WARN line when it's set but ignored, and nothing when it's off.
   - **What ON does:**
     - EndSubmission stops waiting for pipelines that are still being created. Their draws stay skipped until the pipeline is ready, so pop-in lasts a few frames instead of a stall.
     - Draws that memexport, or that run inside an occlusion query, still force the wait.
   - **The patch:** 4 SDK files, 10 hunks, +105/-24.
     - Hunk #5 (`CanEndSubmissionImmediately`) is optional. Following Agent 10's S1, build the first bin without it; DESIGN.md §10 says which lines to drop.
     - With the cvar OFF the code path is unchanged. The only visible change is 3 new fields at the end of the slow-frame line (`dropped draws`, `forced pipeline waits`), and that line prints only when `slow_frame_log_ms` > 0.
   - **Checked by reading only:**
     - `git apply --check` passes on rexglue-sdk 5350b1d with no offsets. I re-ran it at 06:45.
     - The slow-frame format has 28 placeholders for 28 arguments, and the names and scopes the patch uses exist.
     - The review notes are at the end of `CHECK.txt`.
   - **Agent 10's rating** (`build/agent10/t27/r33-popin.md`, 07:36):
     - OFF is SAFE. ON is SAFE-IF: the default stays false with `kRequiresRestart`, row 1 shows identity first, the user's row-3 review gates any recommendation, and the first bin leaves out hunk #5.
     - No blocker. The dated rating block, with S1-S2 and N1-N4, is DESIGN.md §10.
   - **Main risks:**
     - Render-to-texture passes that are later resolved from EDRAM aren't guarded. If such a pass runs once while its pipeline is pending, the texture stays wrong until it's redrawn, so the user's review on a visible desktop (DESIGN.md §8 row 3) is the real gate.
     - A forced wait drains everything in the queue.
     - Bursts last longer, because the GPU thread no longer helps drain.
   - **Next:**
     - Build one bin without hunk #5, then run the rows in DESIGN.md §8. The patched cvar-off arm is the logdiff ref, and the expect rules for the INFO and WARN lines are listed there.
     - Before suggesting it to anyone as a setting, run the resolve-after-drop diagnostic (d) (Agent 10's S2; DESIGN.md §9, item 5).
     - Don't make it the default this round.
8. **#36:** warm-boot baselines on fixed bins, waiting for a quiet slot (notes status note).

## Working rules to keep

- Check `perf-notes/WINDOW-HOLD.txt` before every command. While it exists, make no tool calls.
- Run at BelowNormal priority, never Idle: Select-String at Idle once hung for 15 min. One process at a time; use `python -B`.
- Other agents' dirs are read-only: `build/agent2`, `agent3`, `agent5`, `agent8`, and `bench/`.
- Run JSON written by PowerShell has a UTF-8 BOM, so open it with `encoding='utf-8-sig'`.
- Agent 3's run.json has no `status` and keeps env under `env`. Agent 8's runner uses `status` and `env_set`.
- For other agents, `@@to N:` lines go at the end of a turn.

## Layout of build/agent6/

| Dir | What | Notes |
|---|---|---|
| `w6/` | Logdiff kit `w6_kit.py`, W6/W5 rules, tests, night W6 outputs (`night-W6-*.out.txt`, `out-20261123-*`) | notes §15, §17 |
| `wnight/` | W9/W5b/W4c rules and wrappers, tests, night outputs, `RESULTS.md`, `w9_envcheck.py` | notes §16, §17 |
| `w4b/` | W4b/W5 logdiff drivers (`w4b_logdiff.py`, `w4b_extra.py`, `w5_perfthreads.py`) and outputs | notes §12, §13 |
| `hang/` | Dump tools, CP-state docs, dumpstacks outputs | `agent6-hang-triage.md`; notes §14, §17 |
| `s33-popin/` | #33 design note and staged diff (unbuilt) | notes §17 |
| `attract-stalls/` | Task #18 scripts and outputs (stall attribution, slow-frame join, S11) | notes §1-§11 |
| `s10-2/` | §10.2 spec and line checks | notes §10.2 |
| `aot/`, `ffx/`, `plume26/`, `prelink_smoke/`, `stub_check/` | Native AOT shader chain, FFX/FSR3 libs, link checks (earlier sessions) | `agent6-native-aot.md` |
| `crash-triage/`, `fix-a/` | Crash triage and the fix-A patch | `agent6-crash-triage.md` |
| `draw_async/`, `bench/`, `fake_include/`, top-level `probe_*`, `d3d12_library_probe.exe` | Async PSO / draw experiments, microbenchmarks, syntax-check includes, D3D12 library probe | `agent6-async-pso-design.md`, `agent6-pipelines.md`, `agent6-runspecs.md` |
