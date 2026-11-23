# W4b read-out rules: <workspace>\build\agent8\matrix\20261122-1541

- inputs: results.csv; build\agent8\readout\w4b\w4b.json (add-on, ref d0); build\agent8\readout\w4b\phase.json
- overall: FAIL (worst rule level; N/A < PASS < NOTE < DROP < FAIL; DROP = runs left out, FAIL = no trustworthy verdict; the decision column of the R5 table is the result)

## R0 complete and consistent: DROP

- PASS: 17 rows (expected 17), 16 scored, 15 kept by the add-on (kept = scored, frame stats, no real problems, valid timing, not excluded)
- DROP: scored runs the add-on did not keep: 1551-B-r2 (not timing)

## R1 runner exclusions: PASS

- PASS: no scored run excluded

## R2 foreground (fg_share in the window): PASS

- PASS: fg=1 (>= 0.99): 16 of 16 scored runs

## R3 slow state (timerq over the fg=1 runs): DROP

- PASS: fg=1 runs: N=16, with any onset (timerq) M=16 (1542-d0-r1 at 93 s, 1545-B-r1 at 94 s, 1547-d3-r1 at 76 s, 1549-d11t-r1 at 61 s, 1551-B-r2 at 1 s, 1553-d3-r2 at 84 s, 1556-d11t-r2 at 63 s, 1558-d0-r2 at 72 s, 1600-d3-r3 at 54 s, 1602-d11t-r3 at 1 s, 1604-d0-r3 at 2 s, 1606-B-r3 at 4 s, 1608-d11t-r4 at 1 s, 1611-d0-r4 at 4 s, 1613-B-r4 at 3 s, 1615-d3-r4 at 1 s), in the window K=16 (1542-d0-r1, 1545-B-r1, 1547-d3-r1, 1549-d11t-r1, 1551-B-r2, 1553-d3-r2, 1556-d11t-r2, 1558-d0-r2, 1600-d3-r3, 1602-d11t-r3, 1604-d0-r3, 1606-B-r3, 1608-d11t-r4, 1611-d0-r4, 1613-B-r4, 1615-d3-r4)
- NOTE: the slow state occurs with the game in the foreground: report to Agents 1 and 11
- DROP: dropped: 1542-d0-r1 (R3 slow state in the window (93 s / 35% !)); 1545-B-r1 (R3 slow state in the window (94 s / 32% !)); 1547-d3-r1 (R3 slow state in the window (76 s / 70% !)); 1549-d11t-r1 (R3 slow state in the window (61 s / 96% !)); 1551-B-r2 (R3 slow state in the window (1 s / 64% !)); 1553-d3-r2 (R3 slow state in the window (84 s / 54% !)); 1556-d11t-r2 (R3 slow state in the window (63 s / 96% !)); 1558-d0-r2 (R3 slow state in the window (72 s / 76% !)); 1600-d3-r3 (R3 slow state in the window (54 s / 100% !)); 1602-d11t-r3 (R3 slow state in the window (1 s / 96% !)); 1604-d0-r3 (R3 slow state in the window (2 s / 100% !)); 1606-B-r3 (R3 slow state in the window (4 s / 100% !)); 1608-d11t-r4 (R3 slow state in the window (1 s / 100% !)); 1611-d0-r4 (R3 slow state in the window (4 s / 100% !)); 1613-B-r4 (R3 slow state in the window (3 s / 90% !)); 1615-d3-r4 (R3 slow state in the window (1 s / 98% !))

## R4 scene against the pooled d0 windows: PASS

- PASS: reference draws/frame p50 226 (window 3: 226), add-on threshold 0.020 (floor 0.02, factor 2.0, largest LOO 0.000), light max 0.01, draws tol 2
- PASS: d0 (reference, leave-one-out): 4 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226/226, light in window max 0.0%, off-scene 0
- PASS: B vs d0: 3 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226, light in window max 0.0%, off-scene 0
- PASS: d3 vs d0: 4 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226/226, light in window max 0.0%, off-scene 0
- PASS: d11t vs d0: 4 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226/226, light in window max 0.0%, off-scene 0

## R5 result (runs left after R1, R3, R4, R6): FAIL

- PASS: 0 runs left of 15 kept; dropped from the kept runs 15: 1542-d0-r1 (R3 slow state in the window (93 s / 35% !)); 1545-B-r1 (R3 slow state in the window (94 s / 32% !)); 1547-d3-r1 (R3 slow state in the window (76 s / 70% !)); 1549-d11t-r1 (R3 slow state in the window (61 s / 96% !)); 1553-d3-r2 (R3 slow state in the window (84 s / 54% !)); 1556-d11t-r2 (R3 slow state in the window (63 s / 96% !)); 1558-d0-r2 (R3 slow state in the window (72 s / 76% !)); 1600-d3-r3 (R3 slow state in the window (54 s / 100% !)); 1602-d11t-r3 (R3 slow state in the window (1 s / 96% !)); 1604-d0-r3 (R3 slow state in the window (2 s / 100% !)); 1606-B-r3 (R3 slow state in the window (4 s / 100% !)); 1608-d11t-r4 (R3 slow state in the window (1 s / 100% !)); 1611-d0-r4 (R3 slow state in the window (4 s / 100% !)); 1613-B-r4 (R3 slow state in the window (3 s / 90% !)); 1615-d3-r4 (R3 slow state in the window (1 s / 98% !))
- PASS: the runs left are the add-on's clean set
- FAIL: reference arm d0 has 0 runs left (< 3): no verdict for any arm

| arm | n | fps | p50 ms | p99 ms | 1% low fps | >33 ms/min | vs d0: fps / p50 / p99 / 1% low / >33 | paired fps by round (up / rounds) | decision |
|---|---|---|---|---|---|---|---|---|---|
| d0 | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| B | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| d3 | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| d11t | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |

## R6 background CPU in the window (add-on BG+ / SAT): DROP

- PASS: background cores (median per window) over 16 scored runs: median 8.14, max 8.67; BG+ reference 7.94 (median of this matrix's 10 unsaturated scored runs (20261122-0013 has none)), margin 1.0
- DROP: dropped (left out of the add-on's clean table too): 1542-d0-r1 SAT 8.41; 1547-d3-r1 SAT 8.13; 1549-d11t-r1 SAT 8.59; 1600-d3-r3 SAT 8.20; 1611-d0-r4 SAT 8.15

## R7 d11t arm configuration: PASS

- PASS: 1549-d11t-r1: 1 ms lines 1, REX_TIMER_WAIT_BLOCKING=1
- PASS: 1556-d11t-r2: 1 ms lines 1, REX_TIMER_WAIT_BLOCKING=1
- PASS: 1602-d11t-r3: 1 ms lines 1, REX_TIMER_WAIT_BLOCKING=1
- PASS: 1608-d11t-r4: 1 ms lines 1, REX_TIMER_WAIT_BLOCKING=1

