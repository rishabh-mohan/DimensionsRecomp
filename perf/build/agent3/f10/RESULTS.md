# f10: do the L1-poll hangs (finding 10) happen on a quiet host?

Task #23 (Agent 1, 11-23 05:45; second pair added at 06:23). Agent 3. Status: **done, n = 2 per set.** All four quiet runs pass:

| run | set | ran | s4b_check hint | logdiff vs s4bL0 | P2c |
|---|---|---|---|---|---|
| f10a | s4b20's (M1, C1 off) | 05:58-06:05 | PASS | NEW 0 / MORE 0 | - |
| f10b | gate B's (p2fc) | 06:08-06:16 | PASS | NEW 0 / MORE 0 | PASS |
| f10a2 | s4b20's (M1, C1 off) | 06:32-06:40 | PASS | NEW 0 / MORE 0 | - |
| f10b2 | gate B's (p2fc) | 06:40-06:47 | PASS | NEW 0 / MORE 0 | PASS |

## Answer

**No hang on a quiet host: 0 of 4 runs.** None of the four had a STUCK-LOCK or a dump, and all four reached the level and the end of the L route with 3/3 tags. Under last night's -j8 build, 4 of the 6 runs in the same hour hung (gate A, s4b24, s4b20, gate B); w6s3 and s4b23 did not.

- **How strong this is.** One-sided Fisher exact p = 0.07 (0/4 quiet vs 4/6 loaded; also 0/4 vs 3/4 for the L-route runs only). That fits load as the trigger, but it isn't proof.
- **Worst frames stay under the 5 s threshold.** The STUCK-LOCK detector fires at 5 s ("still not acquired after 5s").
  - Quiet worst frames: 1.79 s (f10a), 1.54 s (f10a2), 2.89 s (f10b), 1.79 s (f10b2).
  - Under the build: 7.98 s (gate B), 9.66 s (gate A), 12.04 s (s4b20), 13.14 s (s4b24).

### GPU or host? The host (Agent 6's question in cp-state S7)

- **Same GPU work.** The 2736-sync cinematic frame has 6262-6313 draws in every run. The ~690-sync frame has 2172 draws in f10b and 2237 in gate B.
- **Time per host<->GPU round trip (ms per wait):**

  | frame | quiet | under the build |
  |---|---|---|
  | ~690-sync | 0.98 (f10b), 0.21 (f10b2) | 6.05 (gate B, hung); 0.33 (s4b23, no hang) |
  | 2736-sync | 0.29 and 0.37 (f10b), 0.18 (f10b2) | 1.79 (gate B, hung), 0.86 (gate A, verify on, hung), 0.64 (w6s3), 0.50 (s4b23) |

- **The submit half stretched too.** The rest of the 2736-sync frame (CP CPU time outside the waits) took 1.30 s (f10b2) and 1.88-1.90 s (f10b) on the quiet host. Under the build it took 2.08-2.27 s (s4b23, gate A, w6s3) and 3.14 s (gate B).
- **Why the host and not the GPU.**
  - The build uses only the CPU. In gate B's stall frames the same GPU work waited 5-30x longer per round trip than on the quiet host, and the CPU-only part of the frame grew 1.7-2.4x.
  - A slower GPU can't account for that. Over the level segment (+60 s..vortex) gate B drew 13.3 frames/s against 16.7-16.8 in f10b and f10b2, about 20 % fewer. And in some frames under the build the waits were faster than quiet (next point).
  - Limit: GPU clocks weren't logged (no `-GpuLog`). This PC is a laptop, where the CPU and GPU may share a power budget, so a busy CPU could slow the GPU a little. That could explain a modest slowdown, not a 5-30x one.
- **Under load the slowdown comes in episodes.**
  - gate B's 1644-sync frame at +60.2 s waited only 0.11 ms per wait (quiet: 0.18-0.29). The build was still running then: the 22:27:13 hostload row had LoadPercentage 100 % with 8 compilers and ninja (busy 9).
  - Its in-level frames at +57..+60 s (the same 12.7k draws) took 78-224 ms, against 95-540 ms on the quiet host.
  - So the slow round trips cluster in the stall window.
- **The quiet host varies too:** 0.18-0.98 ms per wait in the same frames. f10b2, the quietest run (agy 10-17 %), had the fastest waits. f10b ran with a little more in the background: other agents' python up to 4.5 % and powershell up to 7.8 %; its 06:05:53 gate check read 99.9 % and waited.

**Retracted from n = 1:** "under load more draws took the full-path sync".

- The quiet host gives very different totals for the same set: f10a 18810 vs f10a2 28030, and f10b 45458 vs f10b2 77236. f10b2's total is more than gate B's 60921.
- Which bursts happen depends on timing. The 1644-sync in-level burst came in f10a2, f10b2 and gate B, but not in f10a or f10b.
- That fits Agent 6's reading of the code: the readback fast path falls back to the full-path sync when the previous slot isn't ready.

Caveats:

- **Sample size.** 2 quiet runs per set against 6 loaded runs (p = 0.07). One more quiet pair with no hang would give p = 0.03 (0/6 vs 4/6).
- **Margin.** The quiet worst frame, 2.89 s (f10b), is not far below 5 s. A busier host or a slower PC could push a 2736-sync frame past it. w6s3 (under the build, no hang) took 3.99 s.
- **The M1 set (f10a, f10a2; C1 off) makes no cinematic bursts.**
  - It had at most 24 (f10a) and 93 (f10a2) syncs per frame at story-load +10..+40 s.
  - Yet s4b20 (the same set, under the build, no slow-frame log) had a 12037 ms frame with 8316 draws from +38.1 to +50.1 s. Its STUCK-LOCK came at +42.0 s.
  - At +20..+50 s the quiet M1 runs had no frame above about 200 ms.
  - Whether s4b20's long frame was syncs is unknown.
- **What "quiet" means here.**
  - Before each launch: no build process, and Processor(_Total) at most 40 % over 10 s.
  - The agent CLIs (agy 10-26 %, electron 4-9 % of the 12 threads) and other agents' scripts (python up to 6.4 %) ran the whole time.
  - LoadPercentage during the runs (55-100 %) is mostly the game's own spin loops.
- **Tags.**
  - gate B had no tags (the sidecar lost them on log rotation; fixed since). The four quiet runs had 3/3.
  - The route content still matches: the loading frame at +8..+10 s, the in-level frames at +54..+58 s, and the draws in the cinematic frames.
  - One exception: gate B's 1644-sync frame had 16012 draws, against 5554-5558 in f10a2 and f10b2.

## Setup

- **Rows.** `f10a`, `f10b` and the second pair `f10a2`, `f10b2` in `build/agent3/s4b/queue.jsonl`. The second pair has the same args and was added by `build/agent3/s4b/add_f10r2_0628.py`. All four use:
  - `build/agent2/devoff4b-bin` through `harness/run-game.ps1` (hidden desktop), untimed, 600 s cap;
  - the vpad L route `build/agent3/toypad/routes/level-l.txt`;
  - the Batman / Gandalf / Wyldstyle tags through `build/agent3/toypad/toypad_sidecar.py` on 127.0.0.1:9191, with the log-rotation fix;
  - `slow_frame_log_ms=1`, which logs a slow-frame line for nearly every frame.
- **The two sets:**
  - **f10a, f10a2** = s4b20's set (C1 OFF): `shared_memory_upload_nontemporal_copy=true`.
  - **f10b, f10b2** = gate B's set (p2fc): `framerate_limit=0`, `shared_memory_single_hold_rearm=true`, `physical_protect_hold_global_lock=true`, `physical_protect_keep_watch=true`, `physical_protect_keep_watch_verify=false`.
- **Quiet-host gate.** New today in `build/agent3/s4b/s4b-queue.ps1`, function `QuietReason`. The queue was run with `-QuietCpuPct 40 -QuietSampleSec 10`. Right before each launch it requires:
  - no build process (clang/cl/ninja/link/cmake/msbuild/...);
  - none of my check scripts running;
  - Processor(_Total) at most 40 % over 10 s.

  Otherwise the queue waits and checks again about every 25 s.
- **During the run.** `build/agent3/s4b/hostload.ps1` writes a row about every 30 s to `build/agent3/s4b/logs/hostload.csv`. Each row has LoadPercentage, compiler process counts, the game pid and the 4 processes using the most CPU.

## Results

| run | host | hang (owner lr) | dumps | slow-frame lines | >=100 ms / >=1 s / >=4 s | max frame ms | host-gpu wait per frame ms (median / p99 / max) | ms per wait (median / max) | memexport syncs total / max per frame | tags LOAD | last mark | hostload rows with compilers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **f10a** (s4b20's set) | quiet | **no** | 0 | 15263 | 353 / 2 / 0 | 1790.8 | 0.0 / 32.0 / 235.0 | 0.38 / 1.25 | 18810 / 350 | 3 | end | 0 of 12 |
| **f10a2** (s4b20's set) | quiet | **no** | 0 | 16489 | 228 / 3 / 0 | 1540.7 | 0.0 / 28.9 / 466.7 | 0.29 / 0.64 | 28030 / 1644 | 3 | end | 0 of 14 |
| **f10b** (gate B's set) | quiet | **no** | 0 | 38492 | 272 / 7 / 0 | 2886.5 | 0.0 / 26.5 / 990.4 | 0.33 / 2.32 | 45458 / 2736 | 3 | end | 0 of 13 |
| **f10b2** (gate B's set) | quiet | **no** | 0 | 39936 | 318 / 3 / 0 | 1793.8 | 0.0 / 29.2 / 493.8 | 0.25 / 0.81 | 77236 / 2736 | 3 | end | 0 of 13 |
| gate B (w6gB, p2fc) | -j8 build | YES 22:26:29.586, 83FAF200 | hang-38764 | 36553 | 506 / 10 / 2 | 7978.6 | 0.0 / 41.9 / 4836.2 | 0.32 / 7.5 | 60921 / 2736 | 0 | end | 6 of 6 |
| gate A (w6gA, p2fcv) | -j8 build | YES 21:18:17.497, 83FAF188 | hang-36276 | 7271 | 1005 / 11 / 3 | 9657.9 | 0.0 / 22.7 / 2280.7 | 0.45 / 2.46 | 9101 / 2736 | 3 | story-load | no sampler yet |
| s4b20 (C1 off) | -j8 build | YES 22:18:20.260, 83FAF200 | hang-13236 | none logged | - | 12037.2 (perf.csv) | - | - | - | 3 | end | 5 of 5 |
| s4b24 | -j8 build | YES 22:07:59.791, 83FAF200 | hang-31952 | none logged | - | 13140.8 (perf.csv) | - | - | - | 0 | (other route) | 5 of 5 |
| s4b23 (p2fi) | 21:34, build window, no load record | no | 0 | 14063 | 497 / 7 / 0 | 3406.9 | 0.0 / 43.9 / 1327.8 | 0.37 / 1.8 | 44281 / 2750 | 3 | end | no sampler yet |
| w6s3 (p2fc, attract) | -j8 build | no | 0 | 36388 | 379 / 6 / 0 | 3987.3 | 0.0 / 22.8 / 1715.8 | 0.33 / 2.21 | 30450 / 2736 | 0 | idle-320 | 1 of 1 |

ms per wait is taken over frames with at least 100 waits. Last night's numbers come from the same script; see `compare-lastnight.md`.

### Stall frames: the same set (p2fc), quiet vs loaded

Times are from story-load. Bold = ms per wait.

| frame | f10b, quiet | f10b2, quiet | gate B, -j8 build |
|---|---|---|---|
| ~690-sync | #32489 at +20.2 s: 1176.9 ms; wait 653.7 ms over 670 = **0.98** | #33714 at +15.1 s: 481.9 ms; wait 143.8 ms over 683 = **0.21** | #33127 at +30.7 s: 4873.3 ms; wait 4212.5 ms over 696 = **6.05** |
| first 2736-sync | #32493 at +23.0 s: 2657.6 ms; wait 773.8 ms over 2688 = **0.29**; rest of frame 1884 ms | #33718 at +17.3 s: 1793.8 ms; wait 493.8 ms over 2724 = **0.18**; rest of frame 1300 ms | #33131 at +39.0 s: 7978.6 ms; wait 4836.2 ms over 2708 = **1.79**; rest of frame 3142 ms. The STUCK-LOCK (+35.7 s) falls inside this frame |
| second 2736-sync | #32528 at +29.8 s: 2886.5 ms; wait 990.4 ms over 2666 = **0.37**; rest of frame 1896 ms | - | - |
| 1644-sync (in level) | - | #34738 at +58.1 s: 1197.7 ms; wait 295.2 ms over 1633 = **0.18** | #33455 at +60.2 s: 811.6 ms; wait 184.6 ms over 1637 = **0.11** (16012 draws) |

f10a2 (M1 set) also has the 1644-sync frame: #10487 at +60.2 s, 1540.7 ms, wait 466.7 ms over 1616 = 0.29.

Other 2736/2750-sync frames:

| run | frame ms | wait | ms per wait | hang |
|---|---|---|---|---|
| s4b23 | 3406.9 | 1327.8 ms over 2650 | 0.50 | no |
| w6s3 | 3987.3 | 1715.8 ms over 2661 | 0.64 | no |
| gate A (verify on) | 4365.4 | 2280.7 ms over 2657 | 0.86 | yes (its 9657.9 ms frame was mostly CP CPU, 482 ms of wait) |

The loaded runs reached the cinematic later: gate B's 2736-sync frame came at +39.0 s, against +17.3 to +29.8 s on the quiet host.

### Memexport syncs per route segment (`sync_profile.py`)

| run | pre-story | story-load..+60 s (max per frame) | +60 s..vortex | vortex..end | total | frames/s, +60 s..vortex |
|---|---|---|---|---|---|---|
| f10a | 5 | 1170 (256) | 10839 | 6796 | 18810 | 14.3 |
| f10a2 | 5 | 3698 (1644) | 18583 | 5744 | 28030 | 16.4 |
| f10b | 5 | 21481 (2736) | 16092 | 7880 | 45458 | 16.8 |
| f10b2 | 5 | 14984 (2736) | 19818 | 42429 | 77236 | 16.7 |
| gate B | 5 | 13313 (2736) | 19372 | 28231 | 60921 | 13.3 |
| s4b23 | 5 | 12272 (2750) | 30002 | 2002 | 44281 | 11.3 |

frames/s = slow-frame lines in the segment divided by its length; with `slow_frame_log_ms=1` nearly every frame is logged. Through the cinematic the M1 set had at most 24 (f10a) and 93 (f10a2) syncs per frame (story-load +10..+40 s).

### Around s4b20's hang (`align.py`, `cine.py`; perf.csv has frame times, no clock)

Story-load +15..+65 s:

| run | frames | median frame | frames >= 1 s | max frame |
|---|---|---|---|---|
| s4b20 (loaded) | 241 | 71.9 ms | 8 (21.5 s in total) | 12037.2 ms |
| f10a (quiet) | 1250 | 26.8 ms | 1 (1.5 s) | 1500.9 ms (in level, +56.3 s) |
| f10a2 (quiet) | 1252 | 27.6 ms | 2 (2.8 s) | 1540.7 ms (the 1644-sync frame, +60.2 s) |
| f10b (quiet) | 523 | 49.6 ms | 6 (10.1 s) | 2886.5 ms |
| f10b2 (quiet) | 1150 | 30.5 ms | 3 (4.1 s) | 1793.8 ms |
| gate B (loaded) | 637 | 37.7 ms | 3 (14.0 s) | 7978.6 ms |

s4b20's 12037 ms frame (8316 draws) ran from +38.1 s to +50.1 s, and its STUCK-LOCK came at +42.0 s.

## Quiet-host evidence

- **Gate values before launch** (`build/agent3/s4b/logs/<id>.quiet.txt`). Build processes 0 and check scripts 0 every time.
  - f10a launched at 05:58:08 at 23.5 %. The 05:57:42 check read 41.3 % and waited.
  - f10b launched at 06:08:45 at 39.8 %. The 06:05:53 check read 99.9 % (other agents' python scripts) and waited until 06:08:45.
  - f10a2 launched at 06:32:44 at 28.2 % (sampled over 12 s).
  - f10b2 launched at 06:40:14 at 29.0 %.
- **During the runs** (`hostload.csv`): 0 rows with clang/cl/ninja/link (f10a 0 of 12, f10b 0 of 13, f10a2 0 of 14, f10b2 0 of 13). The top processes, as % of 12 threads:
  - legodimensions 16-35 %;
  - agy 10-26 %;
  - electron 4-9 %;
  - powershell <= 8 %;
  - python3.11 <= 6.4 %.
- **The loaded runs for comparison.** The hostload rows within 60 s of gate B, s4b20 and s4b24 had LoadPercentage 100 with 8 clang + 1 ninja ("busy 9"). Agent 6's ninja_log check shows 8 compile edges running at the hang times.

## Files

- Runs, all under `build/agent3/runs/`:
  - `20261123-055810-f10a-m1-sfl-level`
  - `20261123-060847-f10b-p2fc-level`
  - `20261123-063244-f10a2-m1-sfl-level`
  - `20261123-064014-f10b2-p2fc-level`
- Checks, all under `build/agent3/s4b/logs/`: `f10a.check.txt`, `f10b.check.txt`, `f10a2.check.txt`, `f10b2.check.txt`, `f10b.p2c.txt`, `f10b2.p2c.txt`, and `<id>.quiet.txt`.
- Tables, all in `build/agent3/f10/`. `run_n2.ps1` runs every script on all eight runs at Below Normal. Each script is run as `python -B <script> label=<run dir> ...`. Files named `*.n1.*` are the n = 1 versions.

  | output | script |
  |---|---|
  | `f10-table.md`, `f10.json` | `f10_results.py` |
  | `sync.out.txt` | `sync_profile.py` |
  | `align.out.txt` | `align.py` |
  | `cine.out.txt` | `cine.py` |

## Possible next steps (none run; each needs Agent 1's OK)

- **A third quiet pair.** If it doesn't hang either, p = 0.03.
- **A controlled-load repeat.** f10a and f10b with a user-mode CPU load of about 8 busy threads, with no build, would test the cause directly.
- **An s4b20-style row under load with `slow_frame_log_ms=1`**, to see whether the M1 set's 12 s frame is memexport syncs.
- **`-GpuLog`** (NVML clocks) on any of these rows, to settle the laptop power-budget question.
