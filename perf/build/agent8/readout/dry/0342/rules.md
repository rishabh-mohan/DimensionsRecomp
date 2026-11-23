# W4b read-out rules: <workspace>\build\agent8\matrix\20261122-0342

- inputs: results.csv; build\agent8\readout\dry\0342\w4b.json (add-on, ref d0); build\agent8\readout\dry\0342\phase.json
- overall: FAIL (worst rule level; N/A < PASS < NOTE < DROP < FAIL; DROP = runs left out, FAIL = no trustworthy verdict; the decision column of the R5 table is the result)

## R0 complete and consistent: NOTE

- PASS: 5 rows (expected 5), 4 scored, 4 kept by the add-on (kept = scored, frame stats, no real problems, valid timing or not (--all), not excluded)
- NOTE: kept although not valid timing (functional matrix, --all): 0343-d0-r1, 0344-B-r1, 0346-d3-r1, 0347-d0t-r1

## R1 runner exclusions: PASS

- PASS: no scored run excluded

## R2 foreground (fg_share in the window): NOTE

- PASS: fg=1 (>= 0.99): 0 of 4 scored runs
- NOTE: never foreground (runner: info only; kept only without any slow-state onset, R3): 0343-d0-r1, 0344-B-r1, 0346-d3-r1, 0347-d0t-r1

## R3 slow state (timerq over the fg=1 runs): DROP

- PASS: fg=1 runs: N=0, with any onset (timerq) M=0, in the window K=0
- DROP: dropped: 0343-d0-r1 (R3 slow state in the window (39 s / 10% !)); 0344-B-r1 (R3 slow state in the window (29 s / 55% !)); 0346-d3-r1 (R3 slow state in the window (37 s / 15% !))

## R4 scene against the pooled d0 windows: DROP

- PASS: reference draws/frame p50 219 (window 3: 226), add-on threshold 0.020 (floor 0.02, factor 2.0, largest LOO -), light max 0.01, draws tol 2
- NOTE: the reference pool is not at window 3's 226 draws/frame: check the d0 windows by hand
- DROP: off-scene, dropped: 0343-d0-r1 (light frames in the window 72.4%); 0344-B-r1 (light frames in the window 84.2%); 0346-d3-r1 (light frames in the window 46.7%); 0347-d0t-r1 (light frames in the window 67.0%)
- NOTE: d0 (reference, leave-one-out): 1 kept runs, scene distance median - (max -) vs threshold 0.020, draws p50 219, light in window max 72.4%, off-scene 1
- NOTE: B vs d0: 1 kept runs, scene distance median 0.002 (max 0.002) vs threshold 0.020, draws p50 219, light in window max 84.2%, off-scene 1
- NOTE: d3 vs d0: 1 kept runs, scene distance median 0.005 (max 0.005) vs threshold 0.020, draws p50 219, light in window max 46.7%, off-scene 1
- NOTE: d0t vs d0: 1 kept runs, scene distance median 0.002 (max 0.002) vs threshold 0.020, draws p50 219, light in window max 67.0%, off-scene 1

## R5 result (runs left after R1, R3, R4, R6): FAIL

- PASS: 0 runs left of 4 kept; dropped from the kept runs 4: 0343-d0-r1 (R3 slow state in the window (39 s / 10% !)); 0344-B-r1 (R3 slow state in the window (29 s / 55% !)); 0346-d3-r1 (R3 slow state in the window (37 s / 15% !)); 0347-d0t-r1 (R4 light frames in the window 67.0%)
- NOTE: in the add-on's clean set but dropped here (R3 never-foreground onset or R4 draws/light): 0347-d0t-r1 (R4 light frames in the window 67.0%)
- FAIL: reference arm d0 has 0 runs left (< 3): no verdict for any arm
- FAIL: R6 failed (every kept run CPU-saturated): no verdict for any arm

| arm | n | fps | p50 ms | p99 ms | 1% low fps | >33 ms/min | vs d0: fps / p50 / p99 / 1% low / >33 | paired fps by round (up / rounds) | decision |
|---|---|---|---|---|---|---|---|---|---|
| d0 | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| B | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| d3 | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| d0t | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |

## R6 background CPU in the window (add-on BG+ / SAT): FAIL

- PASS: background cores (median per window) over 4 scored runs: median 10.04, max 10.30; BG+ reference - (none (no unsaturated scored run with sys.csv here or in 20261122-0013)), margin 1.0
- NOTE: no background reference, so no BG+ test: check the background column of w4b.md by hand
- FAIL: every kept run is CPU-saturated (median busy share >= 0.97): the background value is only a floor; no verdict

## R7 d11t arm configuration: N/A

- N/A: no d11t run

