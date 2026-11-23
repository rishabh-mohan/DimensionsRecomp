# W4b read-out rules: <workspace>\build\agent8\matrix\20261122-0349

- inputs: results.csv; build\agent8\readout\dry\0349\w4b.json (add-on, ref d0f); build\agent8\readout\dry\0349\phase.json
- overall: FAIL (worst rule level; N/A < PASS < NOTE < DROP < FAIL; DROP = runs left out, FAIL = no trustworthy verdict; the decision column of the R5 table is the result)

## R0 complete and consistent: NOTE

- PASS: 3 rows (expected 3), 3 scored, 3 kept by the add-on (kept = scored, frame stats, no real problems, valid timing or not (--all), not excluded)
- NOTE: kept although not valid timing (functional matrix, --all): 0349-d0t-r1, 0352-d11t-r1, 0354-d0f-r1

## R1 runner exclusions: PASS

- PASS: no scored run excluded

## R2 foreground (fg_share in the window): NOTE

- PASS: fg=1 (>= 0.99): 0 of 3 scored runs
- NOTE: never foreground (runner: info only; kept only without any slow-state onset, R3): 0349-d0t-r1, 0352-d11t-r1, 0354-d0f-r1

## R3 slow state (timerq over the fg=1 runs): DROP

- PASS: fg=1 runs: N=0, with any onset (timerq) M=0, in the window K=0
- DROP: dropped: 0349-d0t-r1 (R3 slow state in the window (69 s / 84% !)); 0352-d11t-r1 (R3 slow state in the window (42 s / 44% !)); 0354-d0f-r1 (R3 slow state in the window (61 s / 100% !))

## R4 scene against the pooled d0f windows: PASS

- PASS: reference draws/frame p50 226 (window 3: 226), add-on threshold 0.020 (floor 0.02, factor 2.0, largest LOO -), light max 0.01, draws tol 2
- PASS: d0t vs d0f: 1 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226, light in window max 0.0%, off-scene 0
- PASS: d11t vs d0f: 1 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226, light in window max 0.0%, off-scene 0
- PASS: d0f (reference, leave-one-out): 1 kept runs, scene distance median - (max -) vs threshold 0.020, draws p50 226, light in window max 0.0%, off-scene 0

## R5 result (runs left after R1, R3, R4, R6): FAIL

- PASS: 0 runs left of 3 kept; dropped from the kept runs 3: 0349-d0t-r1 (R3 slow state in the window (69 s / 84% !)); 0352-d11t-r1 (R3 slow state in the window (42 s / 44% !)); 0354-d0f-r1 (R3 slow state in the window (61 s / 100% !))
- PASS: the runs left are the add-on's clean set
- FAIL: reference arm d0f has 0 runs left (< 3): no verdict for any arm
- FAIL: R6 failed (every kept run CPU-saturated): no verdict for any arm

| arm | n | fps | p50 ms | p99 ms | 1% low fps | >33 ms/min | vs d0f: fps / p50 / p99 / 1% low / >33 | paired fps by round (up / rounds) | decision |
|---|---|---|---|---|---|---|---|---|---|
| d0t | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| d11t | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| d0f | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |

## R6 background CPU in the window (add-on BG+ / SAT): FAIL

- PASS: background cores (median per window) over 3 scored runs: median 9.94, max 10.17; BG+ reference - (none (no unsaturated scored run with sys.csv here or in 20261122-0013)), margin 1.0
- NOTE: no background reference, so no BG+ test: check the background column of w4b.md by hand
- FAIL: every kept run is CPU-saturated (median busy share >= 0.97): the background value is only a floor; no verdict

## R7 d11t arm configuration: PASS

- PASS: 0352-d11t-r1: 1 ms lines 1, REX_TIMER_WAIT_BLOCKING=1

