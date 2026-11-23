# W4b read-out rules: <workspace>\build\agent8\matrix\20261122-0013

- inputs: results.csv; build\agent8\readout\dry\0013\w4b.json (add-on, ref d0); build\agent8\readout\dry\0013\phase.json
- overall: DROP (worst rule level; N/A < PASS < NOTE < DROP < FAIL; DROP = runs left out, FAIL = no trustworthy verdict; the decision column of the R5 table is the result)

## R0 complete and consistent: PASS

- PASS: 19 rows (expected 19), 16 scored, 16 kept by the add-on (kept = scored, frame stats, no real problems, valid timing, not excluded)

## R1 runner exclusions: PASS

- PASS: no scored run excluded

## R2 foreground (fg_share in the window): N/A

- N/A: no fg_share (no sys.csv in this matrix)

## R3 slow state (timerq over the fg=1 runs): N/A

- N/A: no sys.csv in any scored run

## R4 scene against the pooled d0 windows: DROP

- PASS: reference draws/frame p50 226 (window 3: 226), add-on threshold 0.020 (floor 0.02, factor 2.0, largest LOO 0.000), light max 0.01, draws tol 2
- NOTE: 0025-d11-r1: phase switch at none (window 3: 30-33 s)
- NOTE: 0030-n0-r1: no guest draws in perf.csv, not compared
- NOTE: 0042-n0-r2: no guest draws in perf.csv, not compared
- NOTE: 0054-n0-r3: no guest draws in perf.csv, not compared
- NOTE: 0104-n0-r4: no guest draws in perf.csv, not compared
- DROP: off-scene, dropped: 0025-d11-r1 (draws p50 218 vs 226; SCENE? 0.036 > 0.020; light frames in the window 100.0%)
- PASS: d0 (reference, leave-one-out): 4 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226/226, light in window max 0.0%, off-scene 0
- PASS: base vs d0: 4 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226/226, light in window max 0.0%, off-scene 0
- NOTE: d11 vs d0: 4 kept runs, scene distance median 0.000 (max 0.036) vs threshold 0.020, draws p50 218/226/226/226, light in window max 100.0%, off-scene 1

## R5 result (runs left after R1, R3, R4, R6): PASS

- PASS: 15 runs left of 16 kept; dropped from the kept runs 1: 0025-d11-r1 (R4 draws p50 218 vs 226; SCENE? 0.036 > 0.020; light frames in the window 100.0%)
- PASS: the runs left are the add-on's clean set

| arm | n | fps | p50 ms | p99 ms | 1% low fps | >33 ms/min | vs d0: fps / p50 / p99 / 1% low / >33 | paired fps by round (up / rounds) | decision |
|---|---|---|---|---|---|---|---|---|---|
| d0 | 4 | 162.9 (161.5..167.3) | 7.067 (6.977..7.100) | 12.23 (11.93..12.39) | 76.2 (73.2..77.6) | 0.0 (0.0..1.2) | - | - | reference |
| base | 4 | 160.8 (160.3..160.9) | 7.123 (7.101..7.155) | 12.35 (12.22..12.48) | 74.9 (74.2..75.1) | 0.0 (0.0..0.0) | -1.3% worse / +0.8% worse / +0.9% overlap / -1.7% overlap / +0.0/min overlap | -1.4% (0 / 4) | verdict: fps -1.3% worse |
| d11 | 3 | 157.8 (157.5..160.3) | 7.156 (7.114..7.187) | 12.29 (12.21..12.57) | 76.0 (73.7..76.0) | 0.0 (0.0..0.0) | -3.1% worse / +1.3% worse / +0.5% overlap / -0.3% overlap / +0.0/min overlap | -2.8% (0 / 3) | verdict: fps -3.1% worse |
| n0 | 4 | 143.2 (136.7..146.6) | 6.707 (6.555..6.875) | 11.34 (10.97..12.59) | 78.9 (73.0..82.9) | 0.0 (0.0..0.0) | -12.1% worse / -5.1% better / -7.3% overlap / +3.5% overlap / +0.0/min overlap | -12.1% (0 / 4) | verdict: fps -12.1% worse |

## R6 background CPU in the window (add-on BG+ / SAT): N/A

- N/A: no run with a background value (no sys.csv)

## R7 d11t arm configuration: N/A

- N/A: no d11t run

