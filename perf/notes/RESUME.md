# RESUME: the perf sprint, paused on Nov 23

> **Session 3 update (Nov 25, 15:50). Read this first; the rest of this doc is the Nov 23 state.**
> - **Structure:** agy-grid now runs one Overseer (grid Agent 4, the old orchestrator "Agent 1") with Managers as subagents (TypeName `agy-grid-manager`, at most 6 direct reports): M3 functional rows/queue, M12 gates, M10 safety reviewer, M8 runner/matrices, M2 builds. Managers write only in `build/agentN/`. Only the Overseer writes GO lines, edits perf-notes and commits.
> - **Log:** `perf-notes/SESSION3.md` (everything since Nov 25 01:14). Night read-out: `build/agent8/session3/READOUT-NIGHT.md`.
> - **Confirmed by day windows:**
>   - CF1 (`build/agent8/session3/confirm/READOUT-CF1.md` D4D13F23, M10 CONFIRMED-WITH-CHANGES): win3 vs s0 fps +10.0%, p99 −16.1%, 1% low −17.7%, cores −38.5%; ship vs s0 same sign on all four; ship vs win3 not shown different (weak form).
>   - CF2 (`READOUT-CF2.md` 888DEB9B, M10 CONFIRMED): nf ≈ mc (weak form).
> - **User decisions (Nov 25, SESSION3 "14:31-15:05" and "15:28-15:46"):**
>   1. win3 settings as the shipped defaults (P2): KEEP;
>   2. native renderer (mc) as the default: KEEP;
>   3. CG26: stays OFF;
>   4. #33 pop-in (`d3d12_pipeline_creation_no_wait`): a SUGGESTED opt-in setting, default OFF (verdict "a" after the row 3 side-by-sides).
> - **Done:** the final defaults build (devfinal/nativefinal, pins in `build/agent2/BIN-PINS.md`); F1-F7 8/8 PASS; #19 14/14 PASS; #33 rows 1-6 and (d) PASS (row 3 = the visual review, `build/agent3/session3/s33-rows/row3/`).
> - **Open:**
>   - notes export refreshed and committed after the code (see SESSION3 for the hash);
>   - builds: #21 (s4-t1.diff 46FFD2E9) + F1/F3/W1, the InfoQueue drain patch;
>   - the screenshot kit (native4 vs standard, needs native4bp);
>   - gate reviews PS1-PS4; doc fixes (full open list: SESSION3 "15:46-15:55");
>   - the code is committed and pushed (Nov 25, 15:57): SDK perf/opt a7e79c0 (1ba3cdb final defaults + a7e79c0 #33 opt-in), superproject perf/opt 2de88ce. Bins built from exactly that source: `build/agent2/final2/BIN-PINS.md` (devfinal2 4A4A13ED, nativefinal2 4E5E2620), smoke PASS incl. first 3D (`build/agent8/session3/SMOKE-FINAL2.md`). The final2 bins are smoke-tested only, not timed;
>   - queued rows r19eL, f10aL/f10bL (never run);
>   - next sprint idea: upscaling/GPU + async PSO (no_wait still lets pipeline creation hit the frame path, e.g. 322 ms).

**Status:** paused on Monday, Nov 23, for a few days to a week. Start again from this doc. All paths are relative to the workspace root, the folder that holds `DimensionsRecomp/`, `perf-notes/`, `bench/` and `build/`.

This is the final version (Nov 23, 08:09; updated at 08:18 for #19's rate request and at 08:39 for Agent 10's review). It has all four formal read-outs of the night, each final and cross-checked: W6 and W4c by Agent 8, W9 and W5b by Agent 7. It also has Agent 12's gates, Agent 6's logdiffs, Agent 3's four finding-10 rows, Agent 10's ratings of #21 and #33, and the SCRNSAVE install of 07:33 with its post-install tests, which Agent 10 checked at 07:56.

**Numbering:** "#N" is an S4 item (the item table in `perf-notes/S4-DRAFT.md`). Grid tasks are written "task #N". For example, README-DAY and the SCRNSAVE README call the SCRNSAVE fix "task #26", which is not item #26.

**Findings:** FINDINGS-AND-CHANGES.md numbers the problems found on the way. Finding 9 is the missing native shaders (item #1, with #2 as the stopgap). Finding 10 is the stuck game lock (§6, item 3). Finding 11 is a gap in the emulator's write tracking: after the game changes a page's protection, the GPU can draw from stale data. It predates the sprint (it is upstream and in v0.2.0), and its first fix is #5 fix (i), which C1 needs (FINDINGS L141; §2, switches).

More detail:
- `perf-notes/S4-DRAFT.md`: the S4 plan, with every item, rating and window, and their history.
- `perf-notes/FINDINGS-AND-CHANGES.md`: the summary for the user.
- `perf-notes/SESSION2.md`: the session log.
- `build/agent<N>/HANDOFF.md`: each agent's last notes before the pause. Read Agent 1's first: the git rules, the fresh-clone steps and the notes export.
- `build/agent11/resume/facts-perfopt.md`: the fact sheet behind §2-§4 and §9 (git, switches, bins, launcher, host values, each with file:line), compiled on Nov 23 at 05:45-06:20; its launcher section was updated after the SCRNSAVE install. Where it differs from this doc, this doc is newer.

## 1. In one minute

- **Code:** in both repos, branch `perf/opt` on the remote `mine` holds S4a plus the S4b + S4c build. **Every new switch is off by default.**
- **Measured on the night of Nov 22-23** (Agent 12's gates: all 7 windows PASS; Agent 6's logdiffs: 135 runs, no FAIL):
  - **One frame-time win, p2fc** (P2 + fix (i) + C1 v3, verification off). Agent 8's formal read-out of W6: median frame time −10.3% [95% CI −13.6, −6.9], fps +18.0% [+14.1, +22.0], 0.25 core less. All of it comes from C1.
  - **Two CPU savers that leave fps unchanged:**
    - the render thread's GPU-wait back-off at 500 µs (q500). Agent 7's formal read-out of W9: −0.75 core [−0.86, −0.64] (−30%), with no loss in p99 or 1% low;
    - the precise timer wait (d11p): −0.20 core [−0.23, −0.17] (−8%), with fps −0.7% [−1.8, +0.3] and no p99 or 1% low change. Agent 7's formal read-out of W5b picks it narrowly over the blocking wait (d11t), which saves about the same (−0.22 core) but costs about 1% fps (−1.1% [−2.1, −0.0]) and had the window's only stutter cluster.
  - **Codegen B:** no gain (Agent 8's formal read-out of W4c: median +2.6% [−1.2, +6.5], fps −1.7% [−4.9, +1.7]), so drop it.
  - **Cross-checks:** Agent 7 recomputed Agent 8's W6 and W4c headlines (114 of 116 agree; the other 2 differ by rounding), and Agent 8 recomputed Agent 7's W9 and W5b from results.csv (880 of 912 claims agree, 0 sign flips). None of the differences changes a verdict.
- **Still open:**
  - keep or drop each of the four;
  - whether C1 goes on by default (two verify-mode runs);
  - what the night didn't test: a C1-only arm, p2fc with verification on, and the three winners timed together (§5, caveats);
  - the day launcher (the SCRNSAVE fix was installed at 07:33 on Nov 23);
  - F-CA, a deadlock path in threaded mode th2 (§6, item 8);
  - the simde patch;
  - where the notes go.
- **Next, in order (§7):**
  1. finish the leftovers from Nov 23's morning;
  2. W7, W8a/W8b, CG26 and W10;
  3. the pop-in opt-in and the user's screenshot check;
  4. a confirmation window and the keep/drop calls;
  5. a final build with the kept switches on by default;
  6. the write-up.
- **New PC:** rebuild, then measure new baselines before comparing anything (§9).

## 2. What's committed

### Commits on `perf/opt`

Both branches are on the remote `mine`, pushed without force, 0 ahead and 0 behind on Nov 23. If Agent 1 commits again at the end of the grace period (SESSION2 L3300), `git log` wins over this table.

| step | game, `DimensionsRecomp` | SDK, `DimensionsRecomp/rexglue-sdk` |
|---|---|---|
| **S4b + S4c** (Nov 23, 05:40) | **`b0bd3b4`**: `rexlego/CMakeLists.txt`, `rexlego/src/gpu_native/memory_watch.cpp`, the new `rexlego/src/gpu_wait_backoff.cpp` and the SDK pointer | **`5350b1d`**: 13 files (C1 v3, M1, P2's counter, R1/R2 step 1, `db16cyc_pause`) |
| S4a (Nov 22, 14:56) | `1bd322e` (#2 miss cache, SDK pointer) | `3bb65bb` (#7, #8, #5, #38, #32) |
| S3d | `08933a7` (native `draw.cpp`) | none |
| S3 | `001336f` | `c5fe668` (S3 default flips) |
| checkpoint, batches 1-2 | `a0bdaa7` | `90e7ccd` |
| last commit before the sprint | `127e04b` | `2897c31` |

- The 16 S4b/S4c files and their hashes are in `build/agent2/s4b/HASHES.txt`; all 16 match the commits.
- Agent 2's commit check, `build/agent2/COMMIT-CHECK.md`: PASS, and its extended checks PASS too. The SDK's `thirdparty/moltenvk` passes with a note: the `build/agent2/snap1` copy didn't keep its symlinks.
- Other local branches: the game's `main` (`895a529`, the same as `origin/main`) and the SDK's `toypad-ui` (`516e631`).

### What S4 contains

- **S4a** (live and committed at 14:56 on Nov 22):
  - off by default: the upload-hash diagnostic (#7), P2 (#8), fix (i) (#5) and the precise timer wait (#38);
  - always on: the warm-boot pipeline fix (#32), which Agent 10 rated output-identical;
  - native builds only, off by default: the miss-cache stopgap (#2).
- **S4b + S4c** (built on the evening of Nov 22, committed on Nov 23):
  - the re-upload fix C1 v3 (#4): a keep-watch switch and a verify switch, with a counter and a log line. A latch in `memory_watch.cpp` keeps C1 off in native builds.
  - P2's fallback counter: always on, printed on the slow-frame line only with `slow_frame_log_ms`.
  - the non-temporal upload copy M1 (#11);
  - the end-of-frame submit split (#18, R1 stage 1);
  - the deferred-command-list counters (#20 step 1, a compile macro);
  - the codegen pause option (#26; the CG26 build turns it on);
  - the render thread's GPU-wait back-off (#24): pass-through hooks on the fence and query polls, in Xenos builds only. While `LEGO_GPU_WAIT_BACKOFF_US` is unset, every hook calls straight through.
  - **#30, the scene-walk probe: only its CMake option is in, off.** The probe source, `rexlego/src/scene_walk_probe.cpp`, isn't written yet, so turning the option on stops at configure, by design.

  Agent 10 rated the combined change SAFE to build, landing off (Nov 22, 19:47; `perf-notes/agent10-batch2-review.md` row 39: "PASS: SAFE to build", default OFF). Agent 2's compose check is `build/agent2/s4b-compose-1932-c1v3.txt`.

### Switches

No S4 switch is on by default. "Turned on in" names the arms (`bench/agent8/run/matrix-window*.json`).

| item | switch | kind, default | turned on in | lean / status |
|---|---|---|---|---|
| #8 P2 | `shared_memory_single_hold_rearm` | cvar, false | W6 p2, p2f, p2fc | keep, as part of p2fc |
| #5 fix (i) | `physical_protect_hold_global_lock` | cvar, false | W6 p2f, p2fc | keep, as part of p2fc |
| #4 C1 v3 | `physical_protect_keep_watch` (needs #5 on) | cvar, false, kInitOnly | W6 p2fc | keep, as part of p2fc; on by default needs s4bLV and s4bV0 (§6) |
| #4 C1 verify | `physical_protect_keep_watch_verify` | cvar, false, kRequiresRestart | functional runs only (false in p2fc) | stays off; never flip it at runtime (§6, item 2) |
| #24 back-off | env `LEGO_GPU_WAIT_BACKOFF_US`: unset = off, 0 = yield, Q > 0 = sleep Q µs (max 2000); env `LEGO_GPU_WAIT_SPIN_US` (30, max 200) | env, unset | W9 q0-q500 (spin 30) | Q = 500 µs (Agent 7's read-out); drop q0 |
| #24 stats | env `LEGO_GPU_WAIT_STATS` | env, unset | functional runs | diagnostic |
| #38 precise wait | `timer_queue_precise_wait` | cvar, false, kInitOnly | W5 and W5b d11p | keep (d11p); clear caveats (a)-(d) and (f) in S4-DRAFT row 38 before its default flips |
| timer bundle (batches 1-2) | `host_timer_resolution_ms=1`, plus `host_timer_throttling_optout`, `precise_guest_sleep`, `wait_timeout_round_up`, `cs_spin`, `spinlock_pause_spin`, `clock_lockfree` and `tls_bounds_fix` set to true | cvars, off / 0 | W4b d11t; W5 and W5b d11, d11t, d11p | keep, as part of d11p |
| blocking wait | env `REX_TIMER_WAIT_BLOCKING=1` | env, presence-only | W4b, W5 and W5b d11t | not chosen |
| #7 upload-hash log | `shared_memory_upload_hash_log` | cvar, false | functional runs only | diagnostic |
| #11 M1 | `shared_memory_upload_nontemporal_copy` | cvar, false | not timed | open |
| #18 submit split | `d3d12_submit_split_kb` | cvar, 0 = off, kInitOnly | W7 (not run) | open; stays off on native builds |
| #20 step 1 | `REX_D3D12_DEFERRED_COUNTERS` | compile macro, 0 | the CTR build (not built; partial work in `build/agent2/ctr/`) | diagnostic |
| #26 codegen pause | `db16cyc_pause` in `rexlego/legodimensions_config.toml` | codegen option, false (needs a regen) | the CG26 build (partial work in `build/agent2/cg26/`), W10 (not run) | open |
| #30 scene-walk probe | `LEGODIMENSIONS_SCENE_WALK_PROBE` | CMake option, OFF | none | the probe source isn't written |
| #2 miss cache (native) | env `LEGO_NATIVE_SHADER_MISS_CACHE` | env, unset = off | W8a mc (not run) | moot if #1 lands |

- **Always on, no switch:**
  - #32;
  - P2's counter;
  - C1's native latch;
  - #24's pass-through hooks.
- **Two older S3 cvars default on** (`c5fe668`): `pause_safe_order` and `audio_shutdown_detach_worker`.
- **Not committed yet:**
  - #19 (R1 stage 2, cvar `d3d12_async_submit`, off, kInitOnly): staged in `build/agent7/s4-r1s2/` (SDK, 5 files, +320/−1); diff sha256 06B0D371…; its proofs P1-P10 pass; not compiled, syntax-checked or rated yet. Its rate request is written (`build/agent7/s4-r1s2/RATE-REQUEST.md`, task #32, 08:12 on Nov 23), and Agent 10 rates it after the break;
  - #21, S4-T1, staged in `build/agent7/s4-t1/`: env `LEGO_NATIVE_CHAIN_PRIORITY` = 1 (ABOVE_NORMAL priority on the native chain threads), 2 (EcoQoS opt-out) or 3 (both); unset = no call. Rated by Agent 10 (§6, item 9), not built;
  - #33, the pop-in opt-in: staged in `build/agent6/s33-popin/` as cvar `d3d12_pipeline_creation_no_wait` (default false, kRequiresRestart; SDK, 4 files, +105/−24), with a dropped-draw counter on the slow-frame line (#34's idea). Agent 10 rated it (§6, item 10); it isn't built or applied, and no bin is staged.
  - Agent 2's list of the unbuilt diffs, with apply checks against HEAD: `build/agent2/PENDING-DIFFS.md`. Agent 2 refreshed it at 07:49 on Nov 23 (task #31, after N4 of Agent 10's #33 rating): #21's rating, #33 and #34 (staged together and rated) and codegen B's drop are in; #19 is still not rated.

### Not committed

- **The third-party trees** (plume and simde): §3.
- **`perf-notes/`, `bench/`, `build/` and `harness/`** (notes, scripts, matrices, results and bins). They travel only through the notes export or a copy of the workspace.
  - The user decides where they go: a public `perf/` folder, a private repo, or local only.
  - Agent 1's export (`build/agent1/HANDOFF.md` §5): `python build/agent1/export/export_perf.py` is a dry run, and `--copy` writes `build/agent1/perf-export/perf/`. It replaces the workspace path, other profile paths and the account name with placeholders (07:02 run: 4529 files, 0 leftovers). About 47 exported files mention the user's schedule, which is part of the same decision (SESSION2 L3327). Nothing has been pushed.

## 3. Rebuilding from git

1. **Check out `perf/opt` in both repos.**
   - The remote `mine` is the user's own remote. On a fresh clone, add it back with `git remote add mine <url>`; the URL is left out of these notes on purpose.
   - `DimensionsRecomp/rexglue-sdk` is a standalone clone at the submodule path, not an initialized submodule.
   - **A fresh clone works** (Agent 1, Nov 23, 07:04; the commands are in `build/agent1/HANDOFF.md` §3): clone `perf/opt` from the user's forks, init `rexglue-sdk` (its fork, `perf/opt` at 5350b1d), then fetch plume's pin and run the two prepare scripts as in steps 2-3. `git status` then matches the live workspace, and the 4 patched files are byte-identical to the live ones.
   - The SDK's `.gitmodules` has no mapping for `thirdparty/FidelityFX-SDK` or `thirdparty/snapdragon-gsr`, so `git submodule status` fails there. Agent 1's test initialized only `thirdparty/simde` of the SDK's third-party trees; a full recursive init is untested and probably fails too (this predates the sprint).
2. **plume.** The game's gitlink (`ceaeeee`) is in neither the local plume clone nor the public plume repo, so `git submodule update` fails ("not our ref"). Keep the gitlink as it is; don't commit a new plume pointer.
   - Fetch the prepare script's pin, `e0c8871`, by sha and check it out in `DimensionsRecomp/thirdparty/plume`.
   - Then, in `DimensionsRecomp/`, run `python tools/gpu-aot/prepare_plume.py`, then the same command with `--check`.
   - The script applies the 7 plume patches in `tools/gpu-aot/patches/`. `plume-winsdk-compat.patch` (S1 + p2) works around this host's Windows SDK 10.0.22621.
3. **simde.** In `DimensionsRecomp/rexglue-sdk/`, run `python scripts/prepare_simde.py`, then the same command with `--check`.
   - Its pin, `71fd833`, is the SDK's gitlink, and it applies `patches/simde-native-m64-stream.patch`.
   - Whether to keep this patch is question 2, still open.
4. **Line endings.** Both repos use `core.autocrlf=true`.
   - The native fingerprint hashes the worktree bytes of 271 inputs, including the CRLF copies of `memory_watch.cpp` and `rexlego/CMakeLists.txt`.
   - So a clone with other line-ending settings gets a different fingerprint, and the native bin then needs a re-pin.
5. **Build.** Release; the game for x86-64-v3, the SDK for x86-64-v2. The game also needs the game files and a recompile to regenerate `rexlego/generated`, which isn't in git (`perf-notes/agent3-build.md`). Each staged bin in `build/agent2/<name>-bin/` has a `MANIFEST.txt`.

Both `--check` runs passed on Nov 23 (06:01-06:04).

## 4. Bins (local only, `build/agent2/<name>-bin/`)

| bin | content | used in |
|---|---|---|
| devoff2 | S2 | W4b d0 and d11t; W4c d0 |
| devoffB | codegen B, built from S2 | W4b and W4c B |
| devoff3 | S3 (the Xenos bin of the S3d line) | W4b d3, W5 base |
| devoff4 | S4a: S3d + #7, #8, #5 and #38 (off) + #32 | W5 s0, d11, d11t, d11p; **W5b** |
| devoff4b | S4b + S4c, every switch off | **W6, W9**; the finding-10 rows |
| native3d | S3 + `draw.cpp`, fingerprint `335ff2d47268f3a1` (a frozen pin) | the native baseline (n-rows) |
| native4 | S4a + #2 (off), fingerprint `5e3ff55de10f4f64` (**the current pin**) | W8a4, the fallback |
| native4b | S4b + C1's latch + the S4c CMake, fingerprint `9b40acbbef4c57b3`, staged 11-22 22:40 | W8a, W8b. **Not pinned yet:** its re-pin checks passed, and Agent 1's announcement is the last step (§7, step 2) |
| nativeB | S3d + codegen B, fingerprint `81d1c3a71be3c096` | none planned |

Planned, not staged: `devoff4b-ctr-bin` (#20's counters) and `devoff4b-cg26-bin` (#26 on) (`build/agent4/repin/REPIN.md` L20).

## 5. Results

Medians of run medians, on the uncapped title screen, with the quiet-host gate. Compare arms within a window; across windows, see the caveats below. Rows marked **Formal** are the read-outs; the W4b and W5 rows come from Agent 1's runner summaries and Agent 8's Nov 22 read-outs (`build/agent8/readout/w4b/` and `w5/`). Formal intervals are 95% CIs.

| window (results in `build/agent8/matrix/`) | compared | result | lean |
|---|---|---|---|
| W4b, Nov 22 15:41-16:17 (`20261122-1541`, 17 runs) | d0 (devoff2) / B (devoffB) / d3 (devoff3) / d11t (devoff2) | No frame-time change clears the noise band (±19.6%). d11t holds frame time with ~0.5 core less CPU (2.91 against 3.44 cores, −15%). B: fps +6.0% (n = 3, Agent 8's interim read-out; the runner summary says +6.4%) | W4c retests B; W5 retests the timer |
| W5, Nov 22 17:56-18:29 (`20261122-1756`, 16 runs) | base (devoff3) / s0, d11, d11t, d11p (devoff4) | Every arm is within the noise band (±20.4%). d11t and d11p use ~0.4 core (~13%) less game CPU at about the same frame time | W5b retests the wait modes |
| W6, Nov 23 00:09 and 03:13 (`20261123-0009`, `-0313`; 21 runs each) | s0 / p2 / p2f / p2fc (devoff4b) | **Formal (Agent 8, both passes pooled as 10 rounds): p2fc median −10.3% [−13.6, −6.9], lower in 9 of 10 rounds; fps +18.0% [+14.1, +22.0]; −0.249 core [−0.303, −0.195].** C1 alone (p2fc against p2f): −10.7% [−13.1, −8.3], lower in 10 of 10 rounds. p2 and p2f: no change. The runner's pass-2 figures were −14%, fps +22%, −0.27 core. Tails: no paired tail difference excludes 0, and pass 2's p99.9 tail (6.49 against 5.74 ms) comes from an episode that hit all four arms, not from p2fc. Lead: frames of 4.5 ms or more may be ~2-3% slower | **keep p2fc** |
| W9, Nov 23 01:08 and 04:01 (`20261123-0108`, `-0401`; 21 runs each) | #24's back-off: off / Q = 0 / 125 / 250 / 500 µs (devoff4b) | **Formal (Agent 7, 40 kept runs): q500 −0.75 core [−0.86, −0.64] (−30%), with no p99 or 1% low loss.** Without its 7 flagged runs: −0.79 core [−0.84, −0.73], and p99 (−0.8%) and 1% low (+2.2%) are both better than off. The runner's pass-2 figures (−0.70 core, fps +1.1%) agree. q0 saves nothing, so drop it. q125 and q250 slowed only during two host load bursts in pass 2; without the flagged runs they sit next to q500 (−0.72 core each) | **q500** |
| W5b, Nov 23 01:55 and 04:51 (`20261123-0155`, `-0451`; 19 runs each) | timer wait: d11 (spin) / d11t (blocking) / d11p (precise) (devoff4) | **Formal (Agent 7, 36 kept runs, both passes): d11p, narrowly over d11t. d11p −0.20 core [−0.23, −0.17] (−8.0%); median frame time +0.5% [−0.9, +1.9], fps −0.7% [−1.8, +0.3]; no p99 or 1% low change.** d11t saves about the same (−0.22 core [−0.25, −0.19], −8.6%), but its fps is −1.1% [−2.1, −0.0], its raw median frame time was higher in 11 of 12 rounds, and it had the window's only stutter cluster (run 0221-d11t-r5: all 6 of its frames over 16.7 ms fall between T 30.8 and 33.3 s, while host CPU rose to 69%; cause unknown, 1 event in 36 runs). Both cut the TimerQueue thread's busy time from 23% to ~2%. Without the 7 flagged runs the frame times don't separate the arms; the pick then rests on the loaded runs (fps −3.0% for d11t against −1.1% for d11p, n = 4 each; post hoc, p = 0.083) and on 0221. W5's d11t tail lead didn't repeat (p99 +0.3% [−0.3, +1.0], against W5's +8.2%); its CPU saving did, smaller (−8.6% against d11; W5: −13.7% against its base) | **d11p** |
| W4c, Nov 23 02:39 (`20261123-0239`, 13 runs) | d0 (devoff2) / B (devoffB) | **Formal (Agent 8): B median +2.6% [−1.2, +6.5], lower in 1 of 6 rounds; fps −1.7% [−4.9, +1.7]; +0.063 core [−0.007, +0.133].** W4b's hint (fps +6.4%, +15.1% without its run 6) didn't repeat; this refutes it only for the night's host state. No second pass; telling a 1% effect from 0 would need one, with a GPU warm-up | **drop B** |

**Read-outs, all final and cross-checked:** W6 and W4c by Agent 8 (`build/agent8/readout/w-followup/W6.md` and `W4c.md`, 06:39 and 06:40); W9 and W5b by Agent 7 (`build/agent7/readout/W9.md` 8C58CAD1… and `W5b.md` 6479A611…, both rev 1 of 07:45, which apply the checks' fixes; no verdict changed). Agent 7's supporting files are in the same folder: `pool-W9.md`, `pool-W5b.md`, `load-check.md`, `tail-check.md` and `cluster-0221.txt`. Cross-checks: Agent 7 recomputed Agent 8's W6 and W4c headlines (`build/agent7/readout/headlines-W6-W4c.md`: 114 of 116 agree, 2 differ by rounding), and Agent 8 recomputed W9 and W5b from results.csv with separate code (`build/agent8/readout/w-followup/a7check/W9-W5b-check.md`: 880 of 912 claims agree, 0 sign flips). The other 32 are 21 rounding ties, 9 light-share definition differences and 2 from one misread figure, fixed in rev 1: 0221-d11t-r5's non-game load is 2.56 cores, not 2.31, still below the 2.8 flag.

**Logs (Agent 6, `build/agent6/wnight/RESULTS.md`):** 135 runs in the 7 night dirs, no FAIL, 0 STUCK-LOCK, 0 dumps.
- The only lines that appear in an arm and in no reference run are the switch proof lines: p2fc's 3 `C1 keep-watch:` lines, the q arms' back-off init line (exactly once per run, with its Q) and d11p's precise-wait line.
- W9's env and quantum proof: 42 of 42 runs.
- NOTEs: 6 runs lack `Execution complete`, a benign exit race; W9 `0128-off-r2` hit the 3 s shutdown watchdog after WM_CLOSE (exit 0; the first sighting; an off run, so not #24). Watch for it in later logdiffs.

**Gates (Agent 12, `build/agent12/w6-gates/NIGHT-RESULTS.md`): all 7 night windows PASS.**
- Every run was OK and exited 0.
- The logdiffs against each window's reference arm found 0 FAIL and 0 NEW.
- The quiet gate was STRICT, with the antivirus at 0.00 cores.
- No process was left over after any window.
- W6's raw G8 FAIL comes from one source: gate A's finding-10 minidump from Nov 22, waived by Agent 1 at 22:25. W6's timed runs are clean.
- Three runs are flagged for high non-game load: p2fc r2 in W6's first pass, and q125 r1 and r3 in W9's second pass. Each read-out gives its verdicts with and without its flagged runs (W9's set has 7: Agent 9's low-clock runs plus Agent 8's audit flags, W9.md §1; W5b's has 7 too: Agent 8's audit flags plus the runner's slow d11t r1-r2, W5b.md §1).

**Caveats:**
- **Windows Update, Nov 22.** It brought new Intel DTT/IPF extensions and OS updates. Window 3 and earlier aren't comparable with W4b and later.
- **An antivirus exclusion for `build/`** (added ~23:16 on Nov 22). The night windows ran with it; W4b, W5 and older windows didn't.
- **Power overlay.** All the night windows (W6, W9, W5b, W4c) ran under `best_performance` (scheme Balanced, on AC, battery saver off), with no change inside any window. W4b and W5 ran under `best_efficiency`. Compare the night windows with each other, but not their absolute numbers with W4b's or W5's (this matters for W5b against W5).
- **The laptop's slow state.** During a run, the laptop can fall into a slow state, with the E-cores below 800 MHz; its onset tracks run order, not the arm.
  - Every scored W5 run reached it (under `best_efficiency`).
  - No scored run of the night windows did (Agent 12's G10).
- **GPU warm-up biases round 1.** Round 1 of each pass was fast for every arm: the GPU was still cool and ran above its steady, heat-limited clock (832 MHz) for the first 5-13 minutes of game load, and fps follows the GPU clock (W6.md L222-223, which cite Agent 8's audit, §5.5). This widened s0's band in W6's first pass to ±21.4%. An earlier reading that tied round 1 to C1 or to a fast host state is withdrawn. In W5b, only pass 1's round 1 stood out (W5b.md §2).
- **The host looks GPU-limited (a lead).** After round 1, s0, p2 and p2f ran at 97-100% GPU utilisation, while p2fc ran at 86-89% with 18% more fps: roughly 27% less GPU-busy time per frame. So p2fc probably cuts GPU-side work too, and a change that saves only CPU shows up as fewer cores, not more fps (W6.md L224).
- **What the night didn't test.** p2fc ran with verification off; no window had a C1-without-P2 arm (§6, item 2); and the three winners were never timed together: W5b ran on devoff4 (S4a), W6 and W9 on devoff4b (§7, step 9).

## 6. Decisions pending

1. **Keep or drop each lean**, after a confirmation window (all four read-outs are in):
   - **p2fc:** W6's read-out confirms it. Its tail check is done: no paired tail difference excludes 0, and pass 2's p99.9 tail hit all four arms. A lead to watch: at a fixed mix of light and heavy frames, p99 is +1.7% [+0.9, +2.6] and frames of 4.5 ms or more are +2.9% [+2.3, +3.5] slower; the raw p99 isn't higher, because p2fc has fewer heavy frames (W6.md L21). Agent 7's mix guard warns, but the light frames (97-98% of all frames) carry the gain, so it isn't a mix artefact (W6.md L108).
   - **q500:** Agent 7's W9 read-out picks it, and Agent 8's recompute agrees. Still to do: one functional (untimed) Q = 500 run with `LEGO_GPU_WAIT_STATS` must show `sleep_fail == 0`. Timed arms never run with stats, and the stats row s4b18 checked only Q = 250, so sleep_fail at Q = 500 has never been looked at (`build/agent9/HANDOFF.md` L151-154). Agent 9's design for making it a default: `build/agent9/BACKOFF-DEFAULT-ON.md`. An optional follow-up window: off / q500 / q750 / q1000, with the round-1 order rotated (`build/agent7/HANDOFF.md`, open item 3).
   - **d11p:** Agent 7's W5b read-out picks it narrowly over d11t (§5), Agent 8's recompute agrees, and the gates and logdiffs are clean. Before its default flips, clear caveats (a)-(d) and (f) in S4-DRAFT row 38. If d11t is still a candidate, W5b.md §8 suggests an optional test of d11 / d11t / d11p under a controlled background load.
   - **drop B:** W4c's read-out confirms it. B4 stays deferred.
2. **C1 on by default** needs both of these:
   - **s4bLV:** p2fc + verify, cap 1800 s, fixed sidecar, on a quiet host. It passes with 3 of 3 LOADs, reaching the level and K 0 / F 0 over the whole run, rated with the finding-10 rule (item 3). It hasn't run.
   - **C1 without P2 is unverified, not failed.** Agent 12 explained row 7's F 92: without P2, verify's F check races MakeRangeValid's re-hash. Two ways to settle it:
     - (a) s4bV0 (C1 off). Agent 12 predicts F > 0 on the same pages and thread; F = 0 there would refute the race.
     - (b) A verify-only fix that clears `keep_watch_verify_hashes_[page]` inside the valid-bit scope, then a re-run of row 7, expecting F 0 if C1 is clean.

     Until (a) or (b) is done, C1 ships only as p2fc (`perf-notes/agent10-batch2-review.md` §41, L2473-2476).
   - **Never turn the verify cvar off at runtime.** Record is gated on the cvar but the F check on the hash pointer, so a runtime flip gives false F as well as false K (L2470, L2483). Setting it at launch is fine.
3. **Finding 10, the stuck game lock** (a load-only stuck-lock WARN, not C1's). It predates the sprint: v0.2.0 hit the same stuck lock (the same lock, owner and waiting thread), then recovered and finished (FINDINGS L142, L146). In v0.2.0's run the lock's owner polled a GPU query result back to back; #24's query-poll hook is S4's answer to that loop (FINDINGS L146). Agent 3's quiet-host rows f10a, f10b, f10a2 and f10b2 (n = 2 per set) all PASS: no STUCK-LOCK, 3 of 3 tags, K 0 / F 0, no dumps or crashes. So finding 10 stays a load-only WARN (Agent 10, `build/agent10/t27/f10-rating.md`; Agent 3, `build/agent3/f10/RESULTS.md`).
   - 0 of 4 quiet runs hung, against 4 of 6 under Agent 2's -j8 build (p = 0.07). Load is the likely trigger, not proven: the stall is host-side and episodic, and the same GPU work waited 5-30 times longer per round trip under load.
   - The margin is small: the worst quiet frame was 2.89 s against the 5 s detector.
   - Not reproducing the hang doesn't fix it. The memexport full-path sync is still there, and it is a perf candidate after S4.
   - Follow-ups, each needing Agent 1's OK: a third quiet pair, a controlled-load repeat, and a loaded M1 row with the slow-frame log (`build/agent3/HANDOFF.md`).
   - **The rule for any new STUCK-LOCK** (SESSION2 L3128-3132): it counts as "WARN, finding 10" only if CS 0x84959EDC, with the owner (the render thread) parked in sub_83FAF180 at lr 83FAF188 or 83FAF200 and the waiter at lr 82A2A270; it recovers by itself, with no crash or WER; and the run still reaches the level. Anything else is FAIL.
4. **The simde patch** (question 2): open.
5. **Where the notes, scripts and results go:** a public `perf/` folder, a private repo, or local only. The user decides.
6. **The day launcher (RUN-DAY).** No day session until all three conditions hold:
   1. **`run-day.ps1` regenerated from the fixed `run-night.ps1`, `test-day.ps1` re-run, and Agent 10's delta read.** Closed at 07:56 on Nov 23. After the SCRNSAVE install, `day-update.ps1` (07:34) copied the fixed files into `build/agent5/day-draft/` and regenerated `run-day.ps1` there (B67EBD6C…, from run-night 565D30D4…). `test-day.ps1 -Name all` passed 27 of 27 at 07:47 (`build/agent5/day-draft/results/summary-all-074714.txt`). Its 07:35 run had one FAIL, d-real-4: the case still expected the night launcher's status folder not to exist, which stopped being true at the real start at 23:47; a test-only fix to `test-day.ps1` (now 410FB2EC…) compares that folder before and after the case. Agent 10 had rated the delta SAFE, and at 07:56 it checked the final hashes, the `run-day.diff` headers and the test results (`build/agent10/t27/scrnsave-delta.md` §4-§5).
   2. **Installed into `bench/agent5/day/` only after both ratings and while no night launcher runs, then the hashes compared** (README-DAY's install section, L138-141 in the current 9739BCF8…).
   3. **Agent 11's rating**, owed (not done before the break; Agent 1 assigns it as a board task). Agent 10's rating is SAFE-IF (`build/agent10/t27/day-draft-rating.md`).

   Conditions 2 and 3 wait until after the break. The NITs:
   - N1 is fixed: `day-update.ps1` regenerated `build/agent5/day-draft/run-day.diff` (3D0E8753…) with repo-relative headers, and its L59-61 refuse any header that isn't relative; Agent 10 checked the headers at 07:56.
   - N2 and N3 are fixed in `build/agent5/day-draft/` (README-DAY 9739BCF8…, RUN-DAY.cmd B08645E9…). README-DAY's results line (L130) now quotes the 07:47 run; that closes N-2 of Agent 10's SCRNSAVE rating, a separate list (`build/agent10/t27/scrnsave-delta.md` §3).
   - N4 (the DST-naive time math, `launcher-ctl.ps1` L79-81) and N5 (README-DAY L134) are harmless.
   - N6 is open: Agent 12's read-out has to look in `bench/agent5/day/status` for day windows.
7. **The SCRNSAVE fix** for both launchers: rated SAFE, installed at 07:33:57 on Nov 23, and all its post-install tests passed (§8).
8. **F-CA** (new, Agent 10, `build/agent10/t27/r21-s4t1.md` (b) item 5; the code read is `build/agent10/t27/sub-r21-coderead.md` §6). A deadlock path in the color-alias retire handoff, in threaded mode th2 only. It exists without #21 and hasn't been seen at runtime.
   - During tape play on the recording-queue thread, a color-alias handoff's Complete() calls HostDevice::RetireResource, which takes LockRecording, while the worker holds the gate and waits in RecordingQueue::Wait.
   - Agent 7 recorded it under MP4 gap 2 (`build/agent7/s4-t1/check/MP4-STATIC.md`, FEB0FF3E…). None of the 4 earlier th2 runs hung: about 8.4 minutes on one route, weak evidence (`build/agent7/HANDOFF.md` §3).
   - Any th2 hang in a #21 row is checked against F-CA first.
9. **#21 (S4-T1), rated** (`build/agent10/t27/r21-s4t1.md`):
   - (a) the default-off test bed: SAFE;
   - (b) value 3 in F1, F3, W1 and W8b: SAFE-IF all 5 conditions hold:
     1. `host_execution_throttling_optout` stays at its default (false);
     2. the order F1 → W1 → W8b, with F1's rule 3;
     3. an idle host;
     4. never copy `cache/` or seeds between bin dirs, and read F1 (b) on r2;
     5. any th2 hang is checked against F-CA first.
   - (c) the MP4 restatement: ACCEPTED, with one wording fix and one addition. Agent 7's rev 2a made both (docs only), and Agent 10 closed them at 07:49 (`r21-s4t1.md`, follow-up).
   - native4b must be pinned before any timing comparison. The EcoQoS half of value 3 depends on the power plan, so W8b's read-out should quote the power scheme the launcher logs. Values 1 and 2 run only if 3 helps.
10. **#33, the pop-in opt-in, rated** (Agent 10, `build/agent10/t27/r33-popin.md`, 07:36; no BLOCKER):
    - OFF, the default: SAFE.
    - ON, as an opt-in test: SAFE-IF all 4 conditions hold:
      1. the default stays false, with kRequiresRestart;
      2. row 1 (cvar off, the patched bin against the base bin) shows identity before anyone reads ON timings;
      3. the user's row-3 review at the visible desktop gates any recommendation;
      4. the first test bin leaves out hunk #5 (S1).
    - S1 (SHOULD): with hunk #5, ON also changes where submissions end during bursts, a second variable. S2 (SHOULD): run diagnostic (d), a resolve after a dropped draw, before #33 is suggested to anyone.
    - NITs N1-N4. N4 (PENDING-DIFFS was stale on #33 and #34) is done: Agent 2 refreshed it at 07:49 (task #31).
    - Agent 6 recorded the rating in `build/agent6/s33-popin/DESIGN.md` §10 (07:40): §8 now builds without hunk #5, and §9 item 5 is S2. The rated patch is unchanged (0D230244…), and nothing is staged for a bin.

## 7. Next steps, in order

0. **Restart checks:**
   - both repos on `perf/opt` and equal to `mine/perf/opt`;
   - the bins' `MANIFEST.txt` hashes unchanged;
   - the SCRNSAVE fix still installed (the hashes in §8);
   - the native pin (native4, or native4b once Agent 1 has announced it);
   - `build/agent1/HANDOFF.md` read, then every other agent's (`build/agent<N>/HANDOFF.md`, N = 1-12; Agent 11's is short and points here).
   - **Timing counts only** on the user's own desktop (`WinSta0\Default`), not locked, on AC power, with nobody at the PC (`bench/agent5/launch/README.md` L7, L16, L157, L192-194).
   - **Caches.** After any rebuild or re-pin, re-record the PSO and seed caches. A seed must match its bin; never copy `cache/` or seeds between bin dirs.
   - **Cold runs** (`bench/agent8/run/run-matrix.ps1` L14-19, L39, L332-334): by default, one unscored cold run per bin. `-ColdShared` makes one shared cold run, and the other bins' first launches are scored round-1 runs. `-NoCold` makes none. The trap (Agent 9, `build/agent9/s4-t1-preread.md` L168): under `-NoCold` with the bin dirs used in place, n0 r1 and th3old r1 start with an empty cache, while th3 r1 follows n0 r1 on the same bin and starts warm.
   - **GPU warm-up for every window:** add discarded runs until `gpu.csv` shows the steady clock (5-13 minutes on this laptop), and rotate the first arm across rounds (W6.md L226).
   - **Window hygiene** (`build/agent7/readout/W5b.md` §7): re-check the quiet gate's processes before each run, and wait or flag the run if one uses 0.1 core or more; log the top CPU processes once a second; flag or re-run any run with a non-game load (ng_t) of 2.8 cores or more; rotate the round-1 order or add unscored warm-up runs. The launcher's quiet gate checks only at the window start: in W5b's second pass, load rose again ~6 minutes after it passed and hit the first 4 scored runs. Agent 8's HANDOFF (open item 4) adds runner changes: per-process CPU and disk I/O, counts of frames over 8, 10 and 16.7 ms in results.csv, and `light_share` at full precision.
   - **No builds on the machine during timed or hang-sensitive runs.** Finding 10's stall is host-side, and load is the likely trigger: 0 of 4 quiet runs hung, against 4 of 6 under a -j8 build (p = 0.07; §6, item 3; `build/agent1/HANDOFF.md` §6).
1. **Leftovers from Nov 23's morning:**
   - #19's rating: Agent 10 rates it after the break from its rate request (`build/agent7/s4-r1s2/RATE-REQUEST.md`, written at 08:12 on Nov 23; step 3);
   - the native4b pin announcement (step 2);
   - before any window on the day: re-run the plan-only staging (`build/agent8/w-followup/stage-window.ps1`), because the Nov 22 stage files predate the runner change (`build/agent8/HANDOFF.md`, open item 1). No manual re-pin: the launcher pins the current files at its next start (§8).
2. **The post-window rows and builds:**
   - s4bV0 and s4bLV (§6, item 2);
   - **the native4b re-pin.** Steps 0-3 passed (`build/agent4/repin/pin-native4b-2243.txt`: 0 FAIL, 0 WARN). Step 4 passed: the 1-run boot check rpb0 (`build/agent3/runs/rpb0-20261123-0617`, fingerprint 9b40acbbef4c57b3) and the 4-run matrix rpm4 (`build/agent3/runs/rpm4-20261123-0620`; check log `build/agent3/s4b/logs/rpm4.3b.txt`), PASS on every section 3(b) check (`build/agent4/HANDOFF.md` L18). Step 5, Agent 1's announcement, is left; until then the pin stays native4. Then fix `build/agent4/repin/repin_check.ps1` in Agent 4's order (`build/agent4/HANDOFF.md` L29-32): first key check [4]'s old-pin FAIL on the pack state (`$cacheState` 'pack', L291), then add `build/agent2/native4b-bin` to `$oldBins` (L390), and only then add native4b's fingerprint to `$PINS` (L130). Never add the `$PINS` line alone, as REPIN.md L53 suggests: every check of `snap1-on` and `native4b-bin` would then FAIL. The re-pin also closes gate 4 of b2r row 40.
   - the CTR build (#20's counters; partial work in `build/agent2/ctr/`);
   - **the CG26 build** (#26 on; partial work in `build/agent2/cg26/`). Order: Agent 2 regenerates, recompiles, relinks and stages `build/agent2/devoff4b-cg26-bin` (not staged yet) → Agent 9's check kit passes → Agent 10 rates #26 → W10. For the kit (`build/agent9/cg26-check/README.md`), use its one-line command at L12 (checker `cg26_check.py`, DDBA731CC22D74BD…; exit 0 PASS, 1 FAIL, 2 INCOMPLETE, 3 HELD), not a `cmd /c start` wrapper, which always reports exit 0.
3. **W7 / item #19** (R1 stage 2: hand the submit to a worker, `d3d12_async_submit`). Staged in `build/agent7/s4-r1s2/` with its proofs, functional rows, soak plan and a draft W7 matrix; not rated yet. Its rate request (`build/agent7/s4-r1s2/RATE-REQUEST.md`, §16) asks Agent 10, after the break: (a) is it SAFE to build into devoff4b as a default-off test bed; (b) is it SAFE to test ON (`d3d12_submit_split_kb=<N>` plus `d3d12_async_submit=true`) in the rows, the soak and W7; (c) are the threading and ownership rules and the code reads accepted (its §6 and §11). Its `<N>` (the #18 split size) waits for Agent 3's ready-N gate, which wasn't there at 08:10 (RATE-REQUEST §10; `build/agent7/HANDOFF.md` §4).
   - Steps: the `clang -fsyntax-only` check once compiles are allowed (RATE-REQUEST §10), Agent 10's rating, then Agent 2's build at ≤ 2 threads. Apply by copying `build/agent7/s4-r1s2/new/sdk/` or with the `--directory` form in RATE-REQUEST §2: the snap1 SDK has no `.git`, so `git -C <sdk root> apply` uses a repository outside the workspace, prints "Skipped patch" for all 5 files and exits 0 without applying anything. Then the 9 functional rows (~41 min of runs plus ~10 min of checks; `build/agent7/s4-r1s2/FUNCTIONAL-ROWS.md`) and the 10-minute soak (`build/agent7/s4-r1s2/SOAK.md`), whose counter-line checker isn't written yet.
   - W7 itself, as Agent 7's draft (`build/agent7/s4-r1s2/matrix-w7-draft.json`, RATE-REQUEST §14; Agent 8 owns the final): s0 / s18 (#18 at `<N>`) / s19 (#18 + #19), all on one bin, 1 cold + 3 × 4 = 13 runs, ~30-34 min; with the optional s19h (`<N/2>`) 17 runs, ~39-45 min. S4-DRAFT's 4th arm (#18 + #19 + #20) is dropped, because #20's step 2 isn't staged. s18 should tie s0; s19 should lower the GPU Commands thread's ms/f by about the "D3D12 Submit" thread's ms/f, less the drains. W7 runs only after (b) is rated SAFE and the rows and the soak pass.
4. **W8a** (native shaders), as staged in `build/agent8/w-followup/matrix-window8a.json`: n0 (miss cache off) against mc (`LEGO_NATIVE_SHADER_MISS_CACHE=1`), both on native4b-bin. GO line `only=n0,mc repeats=6`: 13 runs, 27.4 min (runner 30) (`build/agent8/w-followup/PROPOSAL.md` L78). It needs the native4b pin. The fallback, W8a4, is the same comparison on native4 (`only=n4,n4mc`, L79). S4-DRAFT's older plan row says native3d against n-S4a.
5. **#21 and W8b** (native threading).
   - #21 is rated (§6, item 9). It still needs the threaded-mode proofs and a build, then F1 → W1 → W8b. W1 still needs a matrix file (`build/agent7/HANDOFF.md` §3).
   - W8b: n0 / the best threaded mode / threaded + #21, 13 runs, ~33 min. It needs a reference arm and busy < 0.97. Agent 4's parked threaded-modes plan: `bench/agent4/matrix-native-threaded.json` (`build/agent4/HANDOFF.md` L20).
6. **CG26 and W10** (the codegen pause, #26): s0 / #26, 13 runs, ~33 min, after the order in step 2.
7. **Item #33, the pop-in opt-in** (the user said yes: opt-in, off by default).
   - Agent 6 staged it in `build/agent6/s33-popin/` (DESIGN.md with its risks and test plan, `s33-popin.patch`, CHECK.txt), not built or applied (`build/agent6/HANDOFF.md`, open item 7). Its dropped-draw counter covers #34.
   - Agent 10 rated it (§6, item 10). Steps: stage the first test bin without hunk #5 (DESIGN.md §8), build it, and run DESIGN.md's test plan with row 1's identity check first; then the user judges the pop-in by eye at the visible desktop (row 3). Run diagnostic (d) before #33 is suggested as a setting (DESIGN.md §9, item 5).
8. **The screenshot check for item #1** (the AOT shader pack). The user said yes, for a one-hour slot at the visible desktop.
   - Native and Xenos screenshots go through `LEGO_GPU_SNAPSHOT_DIR`. The Xenos reference needs the user's desktop.
   - Agent 4's kit is ready: `build/agent4/screenshot-kit/README.md`.
   - **The pack's state.** Agent 4's scratch pack of the 4 missing shaders passed (Nov 22, 07:16; `build/agent4/s35/`), but no pack bin is built (`build/agent4/HANDOFF.md` L16). First dump the attract's shaders: in the 3D attract, native drops draws that use 46 more vertex-shader and 3 pixel-shader objects, so the 4-shader pack may not cover them. Run once with `LEGO_DUMP_MISSING_SHADERS=1` on `harness/routes/attract-long.txt` (HANDOFF L24-26).
   - The pack bin, native4bp, needs the shader-preparation step re-run in its build (FINDINGS L147). The pack changes the native fingerprint again, so native4bp needs its own re-pin (REPIN.md §4.2, steps 3-4) and its own PSO and seed recording (HANDOFF L27, L31, L33).
9. **A confirmation window** for the kept switches. Its arms aren't planned yet: FINDINGS names only "a confirmation window", and the older plan (SESSION2 L2943) compared against S3d. A suggestion: the kept switches together (the three winners were never timed together) against s0, two passes, with the GPU warm-up and the window hygiene of step 0. Two arms the night lacked are worth adding: C1 without P2, and a verify-on p2fc.
10. **Keep/drop**, with the user.
11. **A final build with the kept defaults on.**
    - With today's leans, the defaults to flip are:
      - p2fc's three cvars;
      - the timer bundle plus `timer_queue_precise_wait` (d11p);
      - the back-off at 500 µs. It is an env var today, so it needs a default in code or a config entry (Agent 9's design, §6 item 1).
    - Then: rebuild, run the functional set again, re-pin, and run one more confirmation pass.
12. **The write-up.**

## 8. Launchers

- **The night launcher**, `bench/agent5/launch/RUN-NIGHT.cmd` (D7A0362B…). It runs `run-night.ps1`, 565D30D4… since the SCRNSAVE install (16B90FA8… during the night); the README is B7CEBD63… (0058C8F6… during the night).
  - Agents 10 and 11 rated it SAFE (Nov 22, 22:31-22:33), and it was frozen at 23:24:43.
  - The user double-clicks it and leaves the PC.
  - At the double-click it pins 19 files in `bench/agent5/launch/status/pins.txt`: its own two, the runner and driver scripts in `bench/agent8/run/`, and two harness files. Any change to a pinned file refuses the next window of that launcher run. `pins.txt` is only a record: it still lists the 23:47 start's hashes (`run-matrix.ps1` FEDCEB13…, `run-night.ps1` 16B90FA8…), and nothing reads it back. Each start re-hashes the files (`bench/agent5/launch/run-night.ps1` L967) and rewrites `pins.txt` once its start checks pass (L973), so nobody re-pins by hand after the SCRNSAVE install (`build/agent5/HANDOFF.md` §1; `build/agent8/HANDOFF.md` L13; read from the code, not tested by a start).
  - It runs each window when its GO line is in, starts nothing after 06:45 and exits at 07:30. Window logs go to `bench/agent5/launch/status/`. On Nov 23 it ended at 07:30:14 at its deadline (exit 0), restored the screensaver and released keep-awake; the hold manager's log is clean for all 7 windows (SESSION2 L3339).
- **SCRNSAVE.** On Nov 23 the first GO was refused at 00:03:40:
  - The launcher's `Set-ScreensaverNone` (`run-night.ps1` L461-467 in the night's 16B90FA8…) deleted the empty `SCRNSAVE.EXE` value under `HKCU\Control Panel\Desktop` instead of leaving it empty.
  - `run-matrix.ps1` L417 reads that value under StrictMode 2, so the plan check failed. Dry runs never touch the screensaver, so the tests missed it.
  - Agent 1 re-created the empty value at 00:05:37 (the screensaver stayed off), and the night ran.
- **The SCRNSAVE fix**, staged in `build/agent5/scrnsave-fix/` at 06:14 on Nov 23 and installed at 07:33:57:
  - `run-matrix.ps1` reads the screensaver values through `PSObject.Properties`, so a missing value reads as ''.
  - `run-night.ps1` sets '' instead of deleting the value. Its restore deletes the value again only if it was missing at the start.
  - The day draft is regenerated from the fixed night launcher; `day-update.ps1` copied it into `build/agent5/day-draft/` at 07:34 (§6, item 6).
  - Tests before the install: `test-scrnsave.ps1 -Set new -E2E`, 45 of 45 PASS at 06:14:40 (`build/agent5/scrnsave-fix/results/summary-new-061440.txt`).
  - Agent 10 rated the delta SAFE (06:30) and the install tooling SAFE (06:45) (`build/agent10/t27/scrnsave-delta.md`).
  - The installer refused at 06:36, while the night launcher was still waiting for GO, as designed, and at 07:33:42, when its process check matched pid 33304, not the launcher, which had ended at 07:30:14 (Agent 10's N-4 in `build/agent10/t27/scrnsave-delta.md`: the check matches any PowerShell whose command line names run-night.ps1 or run-day.ps1, so it fails safe; just run it again). At 07:33:57 it installed the three files, all at their "after" hashes (`build/agent5/scrnsave-fix/install-log.txt`).
  - Agent 8 read the runner hunk first: OK (`build/agent8/HANDOFF.md` L12). After the install, all tests passed:
    - `test-scrnsave.ps1 -Set installed -E2E`: 45 of 45 at 07:34:45, on the script revision Agent 10 read (4D46A8E2…; `build/agent5/scrnsave-fix/results/summary-installed-073444.txt`);
    - `build/agent5/launch-test/run-tests.ps1 -Group go`: 16 of 16 at 07:52 on run-night 565D30D4… (`build/agent5/launch-test/results/summary-go.txt`). It ran with the new test-only `-StopAt '2026-11-23 11:00'`: after 07:30, a launcher start needs `-StopAt`, because its default end (the next 07:30) would be more than 14 h away (`build/agent5/HANDOFF.md` §1);
    - `test-day.ps1 -Name all`: 27 of 27 at 07:47 (§6, item 6).
  - Agent 10 checked the install, the hashes and the three test results at 07:56 (`build/agent10/t27/scrnsave-delta.md` §5).
  - The installed hashes: `run-night.ps1` 565D30D4…, the README B7CEBD63…, `RUN-NIGHT.cmd` unchanged (D7A0362B…) and `bench/agent8/run/run-matrix.ps1` 1A522CDF… (was FEDCEB13…). Two pinned files changed, so the next launch pins new hashes.
- **The day launcher (RUN-DAY):** §6, item 6.

## 9. On a new, stronger PC

Every number in §5 is relative to this laptop:
- CPU: i7-1255U, 15 W, 2 P-cores + 8 E-cores, 12 logical. In W5 its P-cores ran flat at 1.92-1.95 GHz.
- GPU: GeForce MX570. At steady state the night's arms looked GPU-limited (§5, caveats).

A stronger PC can change both the size and the sign of the CPU savings, so "a new PC needs new baselines" (SESSION2 L3303):

1. **Rebuild** (§3), or copy the bins and check their MANIFESTs. The matrices hard-code bin paths and accept only `build/agent2/<name>-bin` bins that have a `MANIFEST.txt`; the GO lines pin each matrix's sha256.
2. **New baselines:**
   - re-measure the S3d and S4 baselines (devoff3 and native3d; s0 on devoff4 and devoff4b) and every arm against them, with the GPU warm-up, a cold run per bin, and at least 3 timed runs per arm (the read-outs' minimum for a timing verdict, W9.md §1);
   - derive new noise bands;
   - re-run W6, W9 and W5b before keeping anything on these results.
3. **Native pins.** A fingerprint carries over only if all 271 inputs are byte-identical (§3, step 4). Otherwise re-pin with `build/agent4/repin/REPIN.md` (`repin_check.ps1` is a dry run by default). Re-record the PSO/seed caches too; a seed must match its bin.
4. **Launcher pins.** The night launcher pins 19 files at each double-click (`bench/agent5/launch/status/pins.txt`) and refuses a window if one changes. Copying or editing the scripts is fine before a launch; the next launch pins the new hashes. Re-pin the read-out kits too: their pins include binary and script hashes (`build/agent1/HANDOFF.md` §3).
5. **Host values to re-check** (file:line in the fact sheet, §6):
   - the quiet-gate process list (MsMpEng, OfficeClickToRun, CrossDeviceService) and its thresholds;
   - the RAM and disk gates (6 GB each);
   - the slow-state rule, an E-core clock under 800 MHz. A CPU without E-cores never trips it.
   - the P/E core classes and the best_efficiency GUID;
   - NVML GPU 0. Without an NVIDIA GPU there is a warning and no gpu.csv.
   - the launcher's times (no start after 06:45, exit 07:30) and its disk check on the C: drive;
   - the Windows SDK 10.0.22621 workaround in `plume-winsdk-compat.patch`.

   `run-day.ps1` repeats the launcher's values.
6. **Host settings:** the antivirus exclusion for `build/`, the power scheme and overlay, the screensaver, and the -j8/-j10 Below Normal build limits. The build times in S4-DRAFT §3 belong to this host.

## 10. Where things are

| what | where |
|---|---|
| plan, findings, log, this doc | `perf-notes/` |
| window matrices, GO lines | `bench/agent8/run/matrix-window*.json`; `build/agent8/w-followup/` (PROPOSAL.md, the W8a matrices) |
| timing results | `build/agent8/matrix/<YYYYMMDD-HHMM>/` |
| read-outs, cross-checks, gates, logdiffs | `build/agent8/readout/w-followup/` (W6.md, W4c.md, `a7check/W9-W5b-check.md`); `build/agent7/readout/` (W9.md, W5b.md, `headlines-W6-W4c.md`); `build/agent12/w6-gates/`; `build/agent6/wnight/RESULTS.md` |
| finding-10 and re-pin runs, the finding-10 results | `build/agent3/runs/`; `build/agent3/s4b/logs/`; `build/agent3/f10/` (RESULTS.md, f10-table.md) |
| night launcher, its window logs | `bench/agent5/launch/`; `bench/agent5/launch/status/` |
| the day draft, the SCRNSAVE fix | `build/agent5/day-draft/`; `build/agent5/scrnsave-fix/` |
| bins, the S4b file list, the commit check | `build/agent2/<name>-bin/`; `build/agent2/s4b/HASHES.txt`; `build/agent2/COMMIT-CHECK.md` |
| CTR and CG26 work, the CG26 check kit | `build/agent2/ctr/`, `build/agent2/cg26/`; `build/agent9/cg26-check/` |
| #21 (S4-T1) | `build/agent7/s4-t1/`; `build/agent10/t27/r21-s4t1.md` |
| #19 (R1 stage 2); #33 (the pop-in opt-in) and its rating | `build/agent7/s4-r1s2/` (with `RATE-REQUEST.md`); `build/agent6/s33-popin/`, `build/agent10/t27/r33-popin.md` |
| unbuilt diffs, with apply checks against HEAD | `build/agent2/PENDING-DIFFS.md` |
| q500 as a default | `build/agent9/BACKOFF-DEFAULT-ON.md`; `build/agent9/HANDOFF.md` |
| screenshot kit | `build/agent4/screenshot-kit/README.md` |
| native re-pin | `build/agent4/repin/` (REPIN.md, `repin_check.ps1`) |
| reviews and ratings (Agent 10) | `build/agent10/`; the Nov 23 ratings are in `build/agent10/t27/` |
| per-agent handoffs (Agent 1's first) | `build/agent<N>/HANDOFF.md` |
