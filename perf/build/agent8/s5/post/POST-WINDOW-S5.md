# S5 Phase 0.3 window 20261125-1804: post-window check (M8, 19:35)

Inputs: build/agent8/s5/matrix/20261125-1804 (window-s5 exit 0, 17 runs, 18:05-19:24). Tools: M12 s5_gates.py
(sha D8D17C86), s5_readout.py, s5_confound.py, run with idle priority, outputs here: p03-gates.txt/.json,
p03-readout.txt/.json, p03-confound.txt/.json (all .err.txt empty). runcheck.txt = per-run run.json check
(scratch post_check.py, read-only). No game, no runner process.

## Gates (span 120, cap auto, sustained anchor, route attract-long)
- 14 scored, 3 cold skipped. PASS 9, FLAG 4, VOID 1.
- FLAG: ship60-r1 (host-busy nongame 5.53; thermal outlier 0.64 vs arm 0.91), nat60-r1 (host-busy 3.01),
  n4bp60-r1 (host-busy 5.28; thermal outlier 0.00 vs arm 0.28), nat60-r2 (host-busy 3.68).
- VOID: natU-r1. span SHORT (perf ends 278.6 s < window end 288.2 + 2; the anchor came late, 168.2 s), host VOID
  (game not foreground 3/113 rows, not alive at window end), 3d FLAG (anchor 92.1 s after last press).
  Also LIGHTLY DISTURBED: M16's 4 low-priority python CSV reads 18:31-18:33 (Overseer note); nongame 6.30 cores.
- summary3d.md (score3d) agrees: natU-r1 VOID short_span 110.4 s, all other scored runs OK; colds VOID short by
  design (they end at first frame + 160 s).

## run.json fields (all 17 runs; runcheck.txt)
- Every compat field present (started_epoch_s, elapsed_s, close_method, close_seconds, close_sent_s, wer_seen,
  crash_events, dumps, seed_xenos, cvars, window_start_s, window_span_s, effective_cap(+_source), cooldown, sys).
- status OK, valid_timing True (no build tools) in all 17; close wm_close, exit 0, 0.5-2.0 s; no WER, crash events
  or dumps.
- effective_cap 60 on ship60 (source args) and nat60/n4bp60 (source frames_csv), 0 on natU (frames_csv);
  cvars framerate_limit=60 / native_fps_limit=60 / native_fps_limit=0 as planned.
- window_start_s (launch clock) = results.csv s3d_window_start_s in every run. (summary3d's "start s" column is the
  frame clock = window_start_s minus the first-frame offset, ~4-5 s; label only.)
- cooldown met in all 17, no timeout; waited 0-20 s (cold-ship60 60.1 s).
- route: 51 steps done, 0 timeouts in every scored run (29/0 in colds); vpad dll loaded by the game pid each run.
- bins: every run's MANIFEST matches its pin (4A4A13ED / 4E5E2620 / C5181520).

## nongame_load per run (run.json flags; sys.json window)
| run | start | flag | nongame cores | MsMpEng | eff CPU MHz |
|---|---|---|---|---|---|
| cold-ship60 | 18:05 | nongame_load | 5.22 | 1.17 | 1960 |
| cold-nat60 | 18:09 | nongame_load | 3.48 | 0.93 | 2783 |
| cold-n4bp60 | 18:12 | nongame_load | 5.06 | 1.11 | 2208 |
| ship60-r1 | 18:15 | nongame_load | 5.69 | 1.28 | 1814 |
| nat60-r1 | 18:20 | nongame_load | 3.19 | 0.91 | 2621 |
| n4bp60-r1 | 18:25 | nongame_load | 5.04 | 1.30 | 1798 |
| natU-r1 | 18:30 | nongame_load | 6.87 | 1.78 | 1892 |
| nat60-r2 | 18:35 | nongame_load | 4.06 | 1.10 | 2664 |
| n4bp60-r2 | 18:39 | - | 2.15 | 0.19 | 2233 |
| natU-r2 | 18:44 | - | 1.63 | 0 | 2161 |
| ship60-r2 | 18:49 | - | 1.44 | 0 | 2391 |
| n4bp60-r3 | 18:54 | - | 2.13 | 0.13 | 2349 |
| ship60-r3 | 18:59 | - | 2.06 | 0.14 | 2278 |
| nat60-r3 | 19:04 | - | 1.28 | 0 | 2925 |
| ship60-r4 | 19:09 | - | 1.70 | 0 | 2454 |
| nat60-r4 | 19:14 | - | 1.22 | 0 | 3035 |
| n4bp60-r4 | 19:19 | - | 1.57 | 0 | 2511 |

(sys.json 180 s window, run-timing threshold 2.8 cores; s5_confound's gate-window values differ slightly.)

Reading:
- The heavy load is a TIME effect: every run 18:05-18:39 is loaded (MsMpEng 0.9-1.8 cores + agy.exe 0.3-0.9 +
  electron), every run from 18:39 is not (1.2-2.3 cores, MsMpEng ~0). Inside the loaded period ship/n4bp were higher
  than nat (5.0-5.7 vs 3.2-4.1 cores), as M16 saw; in the quiet period the gap is small (ship 1.4-2.1, n4bp 1.6-2.2,
  nat 1.2-1.3).
- The CPU clock gap stays in the quiet period: nat60 2925-3035 MHz vs ship60 2278-2454 and n4bp60 2233-2511. GPU
  power per arm: nat60 10.8 W vs ship60 25.0 W and n4bp60 25.0 W (readout). On this laptop the CPU and GPU share the
  cooling/power budget, so the lower CPU clock on ship/n4bp most likely follows from their GPU load: a mediator of the
  renderer effect, not an outside confounder (inference; not tested).

## exe staging per arm
- Every arm is staged the same way (common.ps1:33, 63-64: .exe/.dll/.map hardlinked, the rest copied).
- Every run's legodimensions.exe is the same file (same file id) as its bin's exe: hardlinks, no copies.
  Link counts: devfinal2 8, nativefinal2 10, native4bp 6. Each run dir is a new path for every arm alike, so the exe
  path cannot explain an arm difference. MsMpEng was busy on all arms in 18:05-18:39 (nat60 0.83-1.10) and ~0 after.

## Read-out (s5_readout, VOID dropped; quote only with the confound caveat)
- PRIMARY nat60 vs ship60: fps 50.03 vs 42.38, +18.0% CI [8.9, 43.0] (paired by round +23.7% [2.1, 49.9]);
  max ms -71.9% CI [-154.2, -39.0]; p99 not resolved. nat60 sits on its cap (median 16.72 ms), ship60 never does
  (21.3 ms, GPU-bound, thermal share 0.91), so under cap60 this is a lower bound on the native gap.
  Post-hoc low-load seconds: +17.7% CI [8.2, 23.7].
- SECONDARY n4bp60 vs nat60: fps -8.7% CI [-30.8, 0.0] not resolved (paired -12.8% [-26.2, +3.1]); max ms +50.3%
  CI [24.4, 96.0]; n4bp60 runs the GPU harder at the same cap (util 53 vs 38%, clock 1667 vs 1031 MHz, 25.0 vs
  10.8 W, thermal share 0.28 vs 0). Post-hoc low-load fps -10.4% CI [-15.2, -1.4]. Worth a look by M16.
- natU vs nat60: n 1 (natU-r2 67.7 fps), info only.

## Open
- Uncapped native reaches the 3D anchor later (natU 135.7 / 168.2 s vs nat60 113.6-120.3 s): a natU arm needs
  measure_s >= ~210 (-Seconds >= ~300) next time.
- r1 of every capped arm sits in the loaded period; the readout without flagged runs (--exclude-flagged) leaves
  n=3/3/2 per capped arm.
