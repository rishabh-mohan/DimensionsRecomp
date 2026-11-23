# Night logdiffs, 2026-11-23 (task #22 part 2)

Agent 6, written 06:05 on 2026-11-23. Inputs, read-only: the 7 night dirs in `build/agent8/matrix/`. All outputs are under `build/agent6/`. Timing read-outs are Agent 8's (`summary.md` in each dir); this file covers only game.log, run.json and summary.txt.

## Bottom line

- **No FAIL in any of the 7 dirs (135 runs).** All 7 wrappers exited 0 (0 = no FAIL).
- Every arm is PASS or NOTE. The NOTEs come from 7 runs, all with clean exits:
  - 6 runs miss the `Execution complete` line. This is a benign race in the hard-exit path (see "The Execution complete race" below) and hits a different arm each time.
  - 1 run is W9 `0128-off-r2`, where the shutdown watchdog fired 3 s after WM_CLOSE (see "The shutdown watchdog in 0128-off-r2" below). It's a first sighting: 1 of 135 runs.
- **All 135 runs:**
  - status OK, valid timing, exit 0 after one WM_CLOSE, not killed, no WER;
  - 0 STUCK-LOCK, 0 dumps;
  - 0 `Recovered stale physical page protection`, 0 `Unhandled guest physical write fault`, 0 `PhysicalHeap::Protect failed` / `BaseHeap::Protect failed`;
  - warning/error/critical 40/0/0. The one exception is `0128-off-r2` at 41/0/0, and the extra line is the watchdog warning.
  - 35 `[NtCreateFile] FAILED` lines per run, the same as the reference runs.
- **ONLY keys** (lines in an arm and in no reference run) are exactly the switch proof lines, and nothing else is NEW or GONE:
  - p2fc's 3 `C1 keep-watch:` lines;
  - the q arms' back-off init line;
  - d11p's precise-wait line.
- **W9 q-arm env and quantum proof** (the check that couldn't be run before W9): 42 of 42 runs OK, with 0 mismatches. See "W9 env and quantum proof" below.

## Per dir

| Window | Dir | Runs | Arms (runs) | Verdict per arm | NOTE runs (reason) | Kit output |
|---|---|---|---|---|---|---|
| W6 | `20261123-0009` | 21 | s0 5, cold-s0 1, p2 5, p2f 5, p2fc 5 | s0, p2, p2f, p2fc PASS; cold-s0 NOTE | `0009-cold-s0` (no `Execution complete`; GONE vs s0) | `build/agent6/w6/night-W6-0009.out.txt`, `build/agent6/w6/out-20261123-0009/` |
| W6 | `20261123-0313` | 21 | same | s0, cold-s0, p2, p2fc PASS; p2f NOTE | `0345-p2f-r4` (no `Execution complete`) | `build/agent6/w6/night-W6-0313.out.txt`, `build/agent6/w6/out-20261123-0313/` |
| W9 | `20261123-0108` | 21 | off 4, cold-off 1, q0 4, q125 4, q250 4, q500 4 | q0-q500 and cold-off PASS; off NOTE | `0128-off-r2` (41/0/0; the log ends with the watchdog line) | `build/agent6/wnight/night-W9-0108.out.txt`, `build/agent6/wnight/out-W9-20261123-0108/` |
| W9 | `20261123-0401` | 21 | same | q0-q500 and cold-off PASS; off NOTE | `0429-off-r3` (no `Execution complete`) | `build/agent6/wnight/night-W9-0401.out.txt`, `build/agent6/wnight/out-W9-20261123-0401/` |
| W5b | `20261123-0155` | 19 | d11 6, cold-d11 1, d11p 6, d11t 6 | d11p, d11t, cold-d11 PASS; d11 NOTE | `0215-d11-r4` (no `Execution complete`) | `build/agent6/wnight/night-W5B-0155.out.txt`, `build/agent6/wnight/out-W5B-20261123-0155/` |
| W5b | `20261123-0451` | 19 | same | d11, d11p, cold-d11 PASS; d11t NOTE | `0528-d11t-r6` (no `Execution complete`; GONE) | `build/agent6/wnight/night-W5B-0451.out.txt`, `build/agent6/wnight/out-W5B-20261123-0451/` |
| W4c | `20261123-0239` | 13 | d0 6, b 6, cold-d0 1 | all PASS; no reasons | none | `build/agent6/wnight/night-W4C-0239.out.txt`, `build/agent6/wnight/out-W4C-20261123-0239/` |

**Arm details, from each dir's matrix.json:**
- **W6:** all arms use devoff4b. p2 sets `shared_memory_single_hold_rearm`. p2f adds `physical_protect_hold_global_lock`. p2fc adds `physical_protect_keep_watch=true` and `physical_protect_keep_watch_verify=false`.
- **W9:** all arms use devoff4b. off sets no env. Each q arm sets `LEGO_GPU_WAIT_BACKOFF_US=<Q>` and `LEGO_GPU_WAIT_SPIN_US=30`.
- **W5b:** all arms use devoff4 with the 8 timer cvars. d11t adds env `REX_TIMER_WAIT_BLOCKING=1`; d11p adds `timer_queue_precise_wait=true`.
- **W4c:** d0 uses devoff2 and B uses devoffB. The kit lowercases the arm name, so B appears as `b`.

**Arms in matrix.json or the expect file with no night runs:**
- W6: f and fc are in both night matrix.json files but have no runs.
- W9: p1 and q250s are only in `expect-w9.json`.
- W5b: base and s0 are in `expect-w5b.json` only for the W5 test.
- W4c: d11t and d3 are only in `expect-w4c.json`.

## ONLY keys and proof lines

| Window | Arm | ONLY keys vs the reference | Counts per run |
|---|---|---|---|
| W6 (both dirs) | p2fc | `C1 keep-watch: on (with physical_protect_hold_global_lock)`, `C1 keep-watch: first kept protect at #`, `C1 keep-watch: # protects kept so far` | `C1 keep-watch:` 37-38 lines: `on (with ...)` 1, `first kept protect at` 1, `protects kept so far` 35-36. p2fc logs are 140-144 lines long; the other arms' are 98-102. |
| W6 | p2, p2f | 0 | No log line of their own. Their proof is the cvars in run.json, which the kit checks against matrix.json: 0 mismatches. |
| W6 (all arms) | - | - | 0 each of `C1 verify`, `S4 upload hash:`, `slow frame #` and the memexport full-buffer/flush reasons. |
| W9 (both dirs) | q0, q125, q250, q500 | `GPU wait back-off: ON (quantum # us, spin # us); stats OFF; GetData hook built.` | 1 per run, with the arm's Q (see the next section). off has none. |
| W5b (both dirs) | d11p | `TimerQueue: precise wait (timer_queue_precise_wait)` | 1 per d11p run, 0 in d11 and d11t (an exact rule plus forbid rules, all passed). |
| W5b | d11, d11t, d11p | - | `Host timer resolution set to 1 ms (background opt-out on)`: 1 per run in every arm, including cold-d11 (exact rule). |
| W5b | d11t | 0 | No log line of its own. Its proof is `REX_TIMER_WAIT_BLOCKING=1` in run.json env_set, which the kit checks against matrix.json: 0 mismatches. |
| W4c | b, cold-d0 | 0 | 0 NEW, GONE or ONLY keys. |

## W9 env and quantum proof

This is the q-arm check that couldn't be run before W9. Matrix rule (W9 matrix.json notes[4]):
- Every q game.log has exactly one `GPU wait back-off: ON (quantum <Q> us, spin 30 us); stats OFF; GetData hook built.` with the arm's Q.
- Every q run's run.json env_set holds `LEGO_GPU_WAIT_BACKOFF_US=<Q>` and `LEGO_GPU_WAIT_SPIN_US=30`.
- The off arm has no back-off line and no `LEGO_GPU_WAIT_*` key.
- No run logs `is not a plain number`.

**Tools:**
- Script: `build/agent6/wnight/w9_envcheck.py`, read-only.
- Output: `build/agent6/wnight/w9-envcheck.txt`.
- Command: `python -B build/agent6/wnight/w9_envcheck.py --out build/agent6/wnight/w9-envcheck.txt build/agent8/matrix/20261123-0108 build/agent8/matrix/20261123-0401` → exit 0.

**Results: 42 runs, 0 mismatches.**
- **q arms** (4 runs per Q per dir, 32 runs): env_set and params.env both hold exactly `LEGO_GPU_WAIT_BACKOFF_US=<Q>` and `LEGO_GPU_WAIT_SPIN_US=30`, equal to matrix.json. Every run has exactly 1 init line, and it parses to `<Q>/30/OFF` with the tail `GetData hook built.`:
  - q0 → 0
  - q125 → 125
  - q250 → 250
  - q500 → 500
- **off and cold-off** (5 runs per dir): no `LEGO_GPU_WAIT_*` key in env_set or params.env, and no `GPU wait back-off` line.
- **All 42 runs:**
  - 0 `GPU wait stats` lines, so no STATS ran in a timed arm;
  - 0 `is not a plain number`;
  - 0 STUCK-LOCK. Per owner site (L1 83FAF188 / 83FAF200 / 83FBF868, L2 83FB09F0), that's 0/0/0/0 in every arm.
- The kit's own env check gives the same answer: it compares run.json env_set with matrix.json for every arm and found no FAIL.

**Negative test:** `python -B build/agent6/wnight/make_test_w9env.py` → 9/9 verdicts as expected, exit 0. It builds a synthetic dir in the night layout, `build/agent6/wnight/test-w9env/`, rebuilt on every run, with 3 good runs (including `cold-q125`) and 6 bad ones:
- env_set Q 250 in a q125 run;
- init quantum 250 with env 125;
- 2 init lines;
- an init line in off;
- `is not a plain number`;
- a stray `LEGO_GPU_WAIT_STATS=1` in off.

## The "Execution complete" race (6 runs, NOTE only)

**Runs:** `0009-cold-s0` (W6), `0345-p2f-r4` (W6), `0429-off-r3` (W9), `0215-d11-r4` (W5b), `0528-d11t-r6` (W5b), plus none in W4c. Each one ends with `Window closing, shutting down...` and then `Title terminated; hard-exiting process.`, with no `[info] [core] Execution complete` line. All of them have exit 0 and a clean close.

**Cause, from the source** (`build/agent2/snap1/DimensionsRecomp/rexglue-sdk/src/ui/rex_app.cpp`; snap1 can be older than devoff4b, but the strings match):
- `OnClosing` (L693-707) logs `Window closing, shutting down...` and calls `TerminateTitle()`. It then logs `Title terminated; hard-exiting process.`, flushes and calls `std::_Exit(0)`.
- `Execution complete` comes from `module_thread_` (L634-641), after the guest main thread's `Wait` returns.
- The normal order, from W9 `0110-off-r1`:
  - `Window closing` at 01:12:30.715;
  - `Execution complete` at .719, on the module thread;
  - `Title terminated` at .917.
- If `_Exit(0)` runs before the module thread logs, the line is lost.
- 6 of 135 runs (4.4 %) are hit, on 5 different arms, so the race isn't tied to any arm.

**Suggestion for the kit:** treat a missing `Execution complete` as INFO when `Title terminated; hard-exiting process.` is present and exit is 0.

## The shutdown watchdog in 0128-off-r2 (first sighting)

**Run:** W9 `20261123-0108/runs/0128-off-r2`, off arm (back-off OFF, the S4b default). Timeline:
- WM_CLOSE posted at 01:30:52.442 (summary.txt).
- **No** `Window closing, shutting down...` line was logged.
- At 01:30:55.443, 3.001 s later: `[warning] [core] [t12748] Shutdown wedged past the close request; hard-exiting.`
- The exit was seen after 3.2 s: exit 0x0, killed False. run.json has status OK, valid_timing true, close.clean true and werfault_seen false.
- The measured window was valid (19291 frames, median 2.463 ms). The stall came after it, during the close.

**Source** (`build/agent2/snap1/DimensionsRecomp/rexlego/src/legodimensions_app.h`):
- `OnWindowCloseRequested()` (L181-190) arms `StartShutdownWatchdog()` (L407-428) first.
- In the non-native-GPU branch, the watchdog sleeps 3 s, logs this warning, flushes and calls `std::_Exit(0)`.
- The native-GPU branch is 250 ms followed by `TerminateProcess`, with no log line. So the line shows which branch this bin has.
- The comment at L176-180 says it exists because "the window layer between close requested and OnClosing can wedge too".
- **So the backstop did its job:** the close request reached `OnWindowCloseRequested`, but `OnClosing` didn't run within 3 s.

**Where it stalled can't be read from the log.** What runs between the two:
- `toypad_app::StopIfStarted()` (`rexlego/src/toypad_app.cpp:233-257`) was a no-op. Neither this run nor `0110-off-r1` has a `Toypad app:` line, so the companion app was never started.
- Then the rest of `Window::SendCloseRequestToListeners` (`rexglue-sdk/src/ui/window.cpp:617-635`).
- Then the platform close, and `Window::OnBeforeClose` → `OnFocusUpdate(false)` (OnLostFocus listeners) → `OnClosing` (window.cpp:517-548).

**Comparison runs.** In the 3 other W9 runs checked (`0110-off-r1`, `0137-off-r3`, `0126-q500-r2`):
- `Window closing` follows WM_CLOSE within 1-14 ms, and the exit is seen after about 0.5 s.
- A gap of about 21 s between the last Toypad line and WM_CLOSE is normal: `0137-off-r3` has the same gap.

**Scope:**
- `Select-String` over every `build/agent8/matrix/*/runs/*/game.log` finds `Shutdown wedged` only in this run (line 100).
- It isn't caused by back-off: the off arm has no `LEGO_GPU_WAIT_*` env and no init line (w9_envcheck).

**Open:** if it happens again, a dump at about WM_CLOSE + 2 s would show where the UI thread is.

## How it was run

The commands, one at a time at BelowNormal, all exit 0:

```
cmd /c "build\agent6\w6\RUN-W6-LOGDIFF.cmd build\agent8\matrix\20261123-0009 > build\agent6\w6\night-W6-0009.out.txt 2>&1"
cmd /c "build\agent6\w6\RUN-W6-LOGDIFF.cmd build\agent8\matrix\20261123-0313 > build\agent6\w6\night-W6-0313.out.txt 2>&1"
cmd /c "build\agent6\wnight\RUN-W9-LOGDIFF.cmd build\agent8\matrix\20261123-0108 > build\agent6\wnight\night-W9-0108.out.txt 2>&1"
cmd /c "build\agent6\wnight\RUN-W9-LOGDIFF.cmd build\agent8\matrix\20261123-0401 > build\agent6\wnight\night-W9-0401.out.txt 2>&1"
cmd /c "build\agent6\wnight\RUN-W5B-LOGDIFF.cmd build\agent8\matrix\20261123-0155 > build\agent6\wnight\night-W5B-0155.out.txt 2>&1"
cmd /c "build\agent6\wnight\RUN-W5B-LOGDIFF.cmd build\agent8\matrix\20261123-0451 > build\agent6\wnight\night-W5B-0451.out.txt 2>&1"
cmd /c "build\agent6\wnight\RUN-W4C-LOGDIFF.cmd build\agent8\matrix\20261123-0239 > build\agent6\wnight\night-W4C-0239.out.txt 2>&1"
python -B build/agent6/wnight/w9_envcheck.py --out build/agent6/wnight/w9-envcheck.txt build/agent8/matrix/20261123-0108 build/agent8/matrix/20261123-0401
python -B build/agent6/wnight/make_test_w9env.py
```

Each `night-*.out.txt` has these sections:
- the run table (verdict, status, exit, close, levels, STUCK, dumps);
- "Reasons, FAIL first";
- "Counts per arm";
- "ONLY keys per arm";
- the w4b_logdiff and w4b_extra exits.

The full logdiff and exact-text outputs are in the matching `out-*` dir.
