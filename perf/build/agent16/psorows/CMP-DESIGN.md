# n4bp60 vs nat60 clean re-run: design proposal (M16, S5)

Status: PROPOSAL, not implemented, not rated. Why: matrix 20261125-1804 compared n4bp60 vs nat60 while the
nongame load was 5.3-7.5 cores on the n4bp runs vs 3.0-3.8 on the nat runs (CPU clock 1.6-1.75 vs 2.7 GHz).
PSO compiles explained 0/137 of the hitches. In the low-load seconds, n4bp ran 42.8 fps vs 46.6 for nat.

## Arms
| arm | bin | notes |
|---|---|---|
| nat60 | build/agent2/nativefinal2-bin (pinned) | same cvars/env as M8's window arm (native_fps_limit=60, LEGO_NATIVE_FRAME_METRICS) |
| n4bp60 | build/agent16/pack/native4bp-bin (pinned) | identical args; only BinDir differs |

- Route: attract-long, 300 s. The score uses the same score3d rule as the window (90 s warm-up, 120 s 3D span).
  The args are copied verbatim from the window's run.json, so the numbers stay comparable.
- Both bins are verified with verify-bins before each arm. The pins are hard-coded in the .cmd, as in RUN-PSO-ROWS.

## Order and count
- 1 unscored prime per bin first: P-nat, then P-n4bp.
  - This evens out first-launch effects: the Defender first scan of a new exe path, and the global NVIDIA driver cache.
  - Each scored arm then starts from a fresh run dir, so the per-run-dir PSO cache is cold. This is the window's
    condition and the user's first-session condition.
- Scored: 4 ABBA pairs, i.e. nat n4bp n4bp nat | n4bp nat nat n4bp (8 runs). ABBA cancels the linear drift in
  thermals and background load.
- Time: 10 runs x ~5.3 min + gates ~= 60 min. The short form is 2 pairs, ~35 min.

## Quiet gates (the part the window lacked)
- Agents quiet: the Overseer posts a hold for the agents (no builds, reviews, python or rg sweeps) during the kit. The kit cannot enforce this.
- Pre-launch gate per arm: sample the nongame load (Win32 PerfFormattedData total CPU minus our processes), 1 Hz.
  - Launch only when the last 20 s average < 2.0 cores and no window shows > 3.0.
  - It waits at most 180 s. After that the arm runs and is marked `GATE-TIMEOUT`.
- Also refuse the arm when: another legodimensions.exe or a compiler (cl, link, ninja, msbuild) is running,
  perf-notes\WINDOW-GO.txt exists, or a window-s5/run-matrix process exists. These are the existing guards.
- Cooldown: wait until the GPU is < 72 C before each arm, the same as the window.

## In-run flags and scoring (post)
- Per arm, from sys.csv and native-frames.csv:
  - the window means for nongame cores, eff MHz, MsMpEng cores (top_cpu snaps), game cores, GPU MHz and W;
  - the share of window seconds with nongame >= 4 cores or eff < 2200 MHz -> `CONFOUNDED` if > 25 %.
- Metrics: score3d fps, p99, >100 ms, low1, for all seconds AND for clean seconds only (nongame < 4 and
  eff >= 2200). Also the draw-binned mean ms (bins 0-500, 500-1k, 1-2k, 2-3k, 3-4k, 4-6k) and the PSO
  creation count and ms in the window.
- MsMpEng launch check: MsMpEng cores over launch+0..30 s vs over the window, per arm.
- Verdict: the paired diffs (n4bp - nat) per ABBA pair, as median and range, over the non-CONFOUNDED pairs only.
  - `n4bp slower` requires that all clean pairs agree, with a median fps diff < -5 %.
  - Otherwise the result is `no clear difference` or `inconclusive (confounded)`.

## Delivery options
- (A) A new mode `cmp` in psorows/rows-run.ps1, with its post in a new `cmp_post.py` (reusing the win_* scratch logic).
  - Pro: it reuses the guards, the pins and the cleanup that M10 already rated.
  - Con: it changes the rated rows-run.ps1. M10 must re-rate it and the .cmd pins must be redone.
- (B) A small separate kit, RUN-NATCMP.cmd + natcmp/cmp-run.ps1 + cmp_post.py, with the guards copied in. The rated rows kit stays untouched.
  - Recommended: (B). M10 rates it alone, and the rows/ab kit's ratings stay valid.
- Either option runs only after the window, on the Overseer's GO, one kit at a time, with dryrun first.
