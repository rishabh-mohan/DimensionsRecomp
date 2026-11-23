# RESUME: the perf sprint, paused on Nov 23

**Status:** paused on Monday, Nov 23, at ~13:00, for a few days to a week. Start again from this doc. All paths are relative to the workspace root, the folder that holds `DimensionsRecomp/`, `perf-notes/`, `bench/` and `build/`.

More detail:
- `perf-notes/S4-DRAFT.md`: the S4 plan, with every item, rating, window and its history.
- `perf-notes/FINDINGS-AND-CHANGES.md`: the summary for the user.
- `perf-notes/SESSION2.md`: the session log.
- `build/agent<N>/HANDOFF.md`: each agent's last notes.

## 1. In one minute

- **Code:** in both repos, branch `perf/opt` on the remote `mine` holds S4a plus the S4b + S4c build. Every new switch is off by default.
- **Measured on the night of Nov 22-23** (runner summaries; {{READOUTS}}):
  - **One frame-time win, p2fc** (P2 + fix (i) + C1 v3, verification off): median frame time −12 to −14%, fps +21-22%, ~0.25 core less.
  - **Two CPU savers that leave fps unchanged:**
    - the render thread's GPU-wait back-off at 500 µs (q500): 0.70-0.79 core less;
    - the precise timer wait (d11p): ~0.2 core less.
  - **Codegen B:** no gain, so drop it.
- **Still open:**
  - keep or drop each of the four;
  - whether C1 goes on by default (two verify-mode runs);
  - the day launcher;
  - where the notes go.
- **Next:**
  - first, the leftovers from the morning of Nov 23 (§6, step 1);
  - then W7, W8a/W8b, CG26 and W10;
  - the pop-in opt-in and the user's screenshot check;
  - a confirmation window and the keep/drop calls;
  - a final build with the kept switches on by default, and the write-up.
- **New PC:** measure new baselines before comparing anything (§8).

## 2. What's committed on `perf/opt`

| repo (path) | commit | on top of S4a |
|---|---|---|
| SDK, `DimensionsRecomp/rexglue-sdk` | `5350b1d` | the 13 S4b/S4c SDK files; its upstream is `mine/perf/opt` |
| game, `DimensionsRecomp` | `b0bd3b4` | `memory_watch.cpp`, `CMakeLists.txt`, the new `gpu_wait_backoff.cpp` and the SDK pointer |

Both commits were pushed without force on Nov 23 (SESSION2 05:44). The 16 files and their hashes are in `build/agent2/s4b/HASHES.txt`. {{S4A-COMMITS}}

- **S4a** (live and committed at 14:56 on Nov 22):
  - off by default: the upload-hash diagnostic (#7), P2 (#8), fix (i) (#5) and the precise timer wait (#38);
  - always on: the warm-boot pipeline fix (#32), which Agent 10 rated output-identical;
  - native builds only, off by default: the miss-cache stopgap (#2).
- **S4b + S4c** (built on the evening of Nov 22, committed on Nov 23):
  - the re-upload fix C1 v3 (#4), with its counter and log line;
  - P2's fallback counter (no switch; rated output-identical);
  - the non-temporal upload copy M1 (#11);
  - the end-of-frame submit split (#18, R1 stage 1);
  - the deferred-command-list counters (#20 step 1, a compile macro);
  - the codegen pause option (#26; the CG26 build turns it on);
  - the render thread's GPU-wait back-off (#24, hooks H0-H3);
  - the scene-walk probe (#30, a CMake option).

  Agent 10 rated the combined change SAFE to build, landing off (compose check, Nov 22 19:47, `build/agent2/s4b-compose-1932-c1v3.txt`).
- **Third-party trees (not committed).** They are rebuilt from tracked files:
  - plume: `DimensionsRecomp/tools/gpu-aot/prepare_plume.py` applies the patches in `DimensionsRecomp/tools/gpu-aot/patches/` (`plume-winsdk-compat.patch` holds S1 + p2).
  - simde: `DimensionsRecomp/rexglue-sdk/scripts/prepare_simde.py` applies `DimensionsRecomp/rexglue-sdk/patches/simde-native-m64-stream.patch`.
- **Not pushed:** `perf-notes/`, `bench/` and `build/` (notes, scripts, matrices, results and bins). The user decides where they go: a public `perf/` folder, a private repo, or local only.

### Switches

{{SWITCH-TABLE}}

## 3. Bins (local only)

{{BINS}}

## 4. Results

Medians of run medians, on the uncapped title screen, with the quiet-host gate. Compare arms within a window; across windows, see the caveats below the table. Second-pass figures are in brackets.

| window (results in `build/agent8/matrix/`) | compared | result | lean |
|---|---|---|---|
| W4b, Nov 22 15:41-16:17 (`20261122-1541`, 17 runs) | d0 (devoff2) / B (devoffB) / d3 (devoff3) / d11t | No frame-time change clears the noise band (±19.6%). d11t holds frame time with ~0.5 core less CPU (2.91 against 3.44 cores, −15%). B: fps +6.0% (n = 3, Agent 8's interim read-out) | W4c retests B; W5 retests the timer |
| W5, Nov 22 17:56-18:29 (`20261122-1756`, 16 runs) | base (devoff3, S3d) / s0 (devoff4, S4a) / d11 / d11t / d11p | Every arm is within the noise band (±20.4%). d11t and d11p use ~0.4 core (~13%) less game CPU at about the same frame time | W5b retests the wait modes |
| W6, Nov 23 00:09 and 03:13 (`20261123-0009`, `-0313`; 21 runs each) | s0 / p2 / p2f / p2fc on devoff4b | **p2fc: median −11.8% [−14%], fps +21% [+22%], 0.22 [0.27] core less**, faster in 10 of 10 rounds. p2 and p2f: no change. Tail in the second pass: p99 flat (5.04 against 5.00 ms), p99.9 6.49 against 5.74 ms; p2f's p99.9 was 6.40 too, with one frame over 33 ms | **keep p2fc** |
| W9, Nov 23 01:08 and 04:01 (`20261123-0108`, `-0401`; 21 runs each) | #24 back-off: off / Q = 0 / 125 / 250 / 500 µs on devoff4b | **q500: 0.79 [0.70] core less (−31% [−28%]), fps +1%, p99 better than off** (4.62 [4.68] against 4.98 [4.99] ms). q125 and q250 save a little less and were unsteady in the second pass | **q500** |
| W5b, Nov 23 01:55 and 04:51 (`20261123-0155`, `-0451`; 19 runs each) | timer wait: d11 (spin) / d11t (blocking) / d11p (precise) on devoff4-bin | **d11p: 0.20 [0.21] core less (−8%), fps unchanged in both passes.** d11t saves about the same but lost 0.8% fps in the second pass | **d11p** |
| W4c, Nov 23 02:39 (`20261123-0239`, 13 runs) | d0 (devoff2) / B (devoffB) | B: median +1.3%, fps −0.4%, +0.07 core, slower in 5 of 6 rounds. W4b's hint didn't repeat. No second pass | **drop B** |

{{READOUT-VERDICTS}}

**Gates (Agent 12, `build/agent12/w6-gates/NIGHT-RESULTS.md`): all 7 night windows PASS.**
- Every run was OK and exited 0.
- The logdiffs against each window's reference arm found 0 FAIL and 0 NEW.
- The quiet gate was STRICT, with Defender at 0.00 cores.
- No process was left over after any window.
- W6's raw G8 FAIL comes from one source: gate A's finding-10 minidump from Nov 22, waived by Agent 1 at 22:25. W6's timed runs are clean.
- Three runs are flagged for high non-game load: p2fc r2 in W6's first pass, and q125 r1 and r3 in W9's second pass. The read-out has to give each verdict both with and without their rounds.

Caveats:
- **Windows Update, Nov 22.** It brought new Intel DTT/IPF extensions and OS updates. Window 3 and earlier aren't comparable with W4b and later.
- **Defender exclusion for `build/`** (added ~23:16 on Nov 22). W6, W9, W5b and W4c ran with it; W4b, W5 and older windows didn't.
- **Power overlay.** All the night windows (W6, W9, W5b, W4c) ran under `best_performance` (scheme Balanced, on AC, battery saver off), with no change inside any window. W5 ran under `best_efficiency`. Compare the night windows with each other, but not their absolute numbers with W5's (this matters for W5b against W5).
- **The laptop's slow state.** During a run, the laptop can fall into a slow state, with the E-cores at ~0.6 GHz; its onset tracks run order, not the arm. Every scored W5 run reached it (under `best_efficiency`). No scored run of the night windows did (Agent 12's G10).
- **Cold rounds.** In W6's first pass, round 1 was fast for every arm, which widened s0's band to ±21.4%. The second pass rated p2fc FASTER (outside noise).

## 5. Decisions pending

1. **Keep or drop each lean**, after the formal read-outs and a confirmation window:
   - p2fc: check its p99.9 first, to see whether fix (i) or C1 adds rare slow frames;
   - q500: confirm with Agent 6's W9 logdiff (no back-off init line in off, exactly one ON line per Q arm);
   - d11p: confirm with Agent 6's W5b logdiff;
   - drop B: B4 stays deferred.
2. **C1 on by default** needs two runs:
   - s4bLV: p2fc + verify, cap 1800 s, fixed sidecar, 3 of 3 LOADs and reaching the level;
   - s4bV0: the C1-OFF verify control. C1 without P2 stays uncleared until s4bV0 runs or Agent 12 explains row 7's F 92.
3. **Finding 10** (a load-only stuck-lock WARN, not C1's): Agent 3's quiet-host rows f10a and f10b are the direct test. {{F10}}
4. **The simde patch** (question 2): open.
5. **Where the notes, scripts and results go:** a public `perf/` folder, a private repo, or local only. The user decides; Agent 1 holds a staged export.
6. **The day launcher (RUN-DAY)**, staged in `build/agent5/day-draft/`:
   - Agent 10 rated it SAFE-IF (`build/agent10/t27/day-draft-rating.md`).
   - Agent 5 rebuilds `run-day.ps1` from the SCRNSAVE-fixed `run-night.ps1`, staged only.
   - Agent 11's rating is still owed.
   - After the break, install it only once the night launcher has exited, then compare the hashes.
   - Two NITs to fix: N1, `run-day.diff` L1-4 has absolute paths with the user name (fix before publishing); N6, Agent 12's read-out has to look in `bench/agent5/day/status` for day windows.
7. **The SCRNSAVE fix** for both launchers: {{SCRNSAVE-STATUS}}

## 6. Next steps, in order

1. **Leftovers from Nov 23's morning** (check each agent's HANDOFF.md):
   - the formal read-outs (Agents 7 and 8), Agent 6's logdiffs and dumpstacks, Agent 12's gates, Agent 3's f10a/f10b;
   - the SCRNSAVE fix and its reviews;
   - Agent 2's commit check.
2. **The post-window rows and builds:**
   - s4bV0 and s4bLV (for C1 on by default);
   - the native4b re-pin rows rpb0 and rpm4. native4b-bin is staged and Agent 4's dry-run check passed (`build/agent4/repin/pin-native4b-2243.txt`), but it is **not pinned**;
   - the CTR build (#20's counters) and the CG26 build (#26 on).
3. **W7 / item #19** (R1 stage 2, the submit worker, `d3d12_async_submit`). Its design isn't rated yet. Steps: staging, Agent 10's rating, a build, then functional runs and a 10-minute soak. W7 itself: s0 / #18 / #18 + #19 / #18 + #19 + #20, 17 runs, ~43 min. #18 alone should tie.
4. **W8a** (native shaders): native3d against native4b with #2 on (or the #1 pack), ABBAAB × 2 + 1 = 13 runs, ~33 min. It needs the native4b pin; W8a4 is the fallback.
5. **Item #21 and W8b** (native threading). #21 = `LEGO_NATIVE_CHAIN_PRIORITY=1`, not rated. It needs Agent 10's rating, the threaded-mode proofs and a build. W8b: n0 / the best threaded mode / threaded + #21, 13 runs, ~33 min, with a reference arm and busy < 0.97.
6. **CG26 and W10** (codegen pause #26): s0 / #26, 13 runs, ~33 min.
7. **Item #33, the pop-in opt-in** (the user said yes, opt-in, off by default). Placeholder cvar: `d3d12_async_pipeline_no_wait`. Steps: implementation (Agent 6 proposed it), Agent 10's rating, a build, functional runs, then the user judges the pop-in by eye. #34, a dropped-draw counter, is optional.
8. **The screenshot check for item #1** (the AOT shader pack). The user said yes, for a one-hour slot at the visible desktop. Native and Xenos screenshots go through `LEGO_GPU_SNAPSHOT_DIR`. Agent 4 stages the kit.
9. **A confirmation window:** the kept switches together against s0, two passes.
10. **Keep/drop**, with the user.
11. **A final build with the kept defaults on:**
    - flip the defaults in source;
    - rebuild;
    - run the functional set again;
    - re-pin;
    - run one more confirmation pass.
12. **The write-up.**

## 7. Launchers

- **The night launcher**, `bench/agent5/launch/RUN-NIGHT.cmd` (D7A0362B…). It runs `run-night.ps1` (16B90FA8…); the README is 0058C8F6….
  - Agents 10 and 11 rated it SAFE (Nov 22, 22:31-22:33), and it was frozen at 23:24:43.
  - The user double-clicks it and leaves the PC. It takes its pins at the double-click, runs each window when its GO line is in, and stops hard at 07:30.
- **SCRNSAVE.** On Nov 23 the first GO was refused at 00:03:40:
  - The launcher's `Set-ScreensaverNone` (`run-night.ps1` L461-467) deleted the empty `SCRNSAVE.EXE` value under `HKCU\Control Panel\Desktop` instead of leaving it empty.
  - `run-matrix.ps1` L417 reads that value under StrictMode 2, so the plan check failed. Dry runs never touch the screensaver, so the tests missed it.
  - Agent 1 re-created the empty value at 00:05:37 (the screensaver stayed off), and the night ran.
  - The fix: the launcher sets '' instead of deleting the value, or the runner reads it through `PSObject.Properties`. `run-day.ps1` has the same code. {{SCRNSAVE-STATUS}}
- **The day launcher (RUN-DAY):** see §5, item 6.

## 8. On a new, stronger PC

Every number in §4 is relative to this laptop. It has a 15 W i7-1255U; in W5 its P-cores ran flat at 1.92-1.95 GHz, and its E-cores fall into the slow state. A stronger PC can shift both the size and the sign of the CPU savings, so:

1. **Rebuild from git:**
   - clone `perf/opt` in both repos;
   - run `prepare_plume.py` and `prepare_simde.py`;
   - build the bins at the new core count;
   - run the functional set again.
2. **New baselines:**
   - re-measure the S3d line (base) and the S4 line (s0) with a cold run and at least 3 rounds;
   - derive new noise bands;
   - then re-run W6, W9 and W5b before keeping anything on these results.
3. **Re-pin the native bins** with the re-pin procedure. {{REPIN}}
4. **Launcher and runner pins:**
   - the pinned hashes and paths;
   - the quiet-gate thresholds;
   - the driver/process allowlist;
   - the screensaver and power settings;
   - the Defender exclusion.

   {{HOST-VALUES}}

## 9. Where things are

| what | where |
|---|---|
| plan, findings, log, this doc | `perf-notes/` |
| window matrices | `bench/agent8/run/matrix-window*.json` |
| timing results | `build/agent8/matrix/<YYYYMMDD-HHMM>/` |
| night launcher / day draft | `bench/agent5/launch/` / `build/agent5/day-draft/` |
| bins and the S4b file list | `build/agent2/*-bin`, `build/agent2/s4b/HASHES.txt` |
| native re-pin checks | `build/agent4/repin/` |
| reviews (Agent 10) | `build/agent10/` |
| per-agent handoffs | `build/agent<N>/HANDOFF.md` |
