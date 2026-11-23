# Read-out rules (w5_rules.py --no-drop, sensitivity pass): <workspace>\build\agent8\matrix\20261122-1541

- inputs: results.csv, matrix.json; build\agent8\readout\w5-dry-1541\w5.json (add-on, ref d0); build\agent8\readout\w5-dry-1541\phase.json; per run run.json, game*.log, threads.csv; build\agent8\readout\w5-dry-1541\timerq3.txt
- overall: DROP (worst rule level; N/A < PASS < NOTE < DROP < FAIL; DROP = runs left out, FAIL = no trustworthy verdict; the decision columns of the R5 tables are the result)

## R0 complete and consistent: DROP

- PASS: 17 rows (expected 17), 16 scored, 15 kept by the add-on (kept = scored, frame stats, no real problems, valid timing, not excluded)
- PASS: scored runs per arm: d0 4, B 4, d3 4, d11t 4
- DROP: scored runs the add-on did not keep: 1551-B-r2 (not timing)

## R1 runner exclusions: PASS

- PASS: no scored run excluded

## R2 foreground (fg_share in the window): PASS

- PASS: fg=1 (>= 0.99): 16 of 16 scored runs

## R3 slow state (timerq over the fg=1 runs): DROP

- PASS: fg=1 runs: N=16, with any onset (timerq) M=16 (1542-d0-r1 at 93 s, 1545-B-r1 at 94 s, 1547-d3-r1 at 76 s, 1549-d11t-r1 at 61 s, 1551-B-r2 at 1 s, 1553-d3-r2 at 84 s, 1556-d11t-r2 at 63 s, 1558-d0-r2 at 72 s, 1600-d3-r3 at 54 s, 1602-d11t-r3 at 1 s, 1604-d0-r3 at 2 s, 1606-B-r3 at 4 s, 1608-d11t-r4 at 1 s, 1611-d0-r4 at 4 s, 1613-B-r4 at 3 s, 1615-d3-r4 at 1 s), in the window K=16 (1542-d0-r1, 1545-B-r1, 1547-d3-r1, 1549-d11t-r1, 1551-B-r2, 1553-d3-r2, 1556-d11t-r2, 1558-d0-r2, 1600-d3-r3, 1602-d11t-r3, 1604-d0-r3, 1606-B-r3, 1608-d11t-r4, 1611-d0-r4, 1613-B-r4, 1615-d3-r4)
- NOTE: the slow state occurs with the game in the foreground: report to Agents 1 and 11
- DROP: dropped: 1542-d0-r1 (R3 slow state in the window (93 s / 35% !)); 1545-B-r1 (R3 slow state in the window (94 s / 32% !)); 1547-d3-r1 (R3 slow state in the window (76 s / 70% !)); 1549-d11t-r1 (R3 slow state in the window (61 s / 96% !)); 1551-B-r2 (R3 slow state in the window (1 s / 64% !)); 1553-d3-r2 (R3 slow state in the window (84 s / 54% !)); 1556-d11t-r2 (R3 slow state in the window (63 s / 96% !)); 1558-d0-r2 (R3 slow state in the window (72 s / 76% !)); 1600-d3-r3 (R3 slow state in the window (54 s / 100% !)); 1602-d11t-r3 (R3 slow state in the window (1 s / 96% !)); 1604-d0-r3 (R3 slow state in the window (2 s / 100% !)); 1606-B-r3 (R3 slow state in the window (4 s / 100% !)); 1608-d11t-r4 (R3 slow state in the window (1 s / 100% !)); 1611-d0-r4 (R3 slow state in the window (4 s / 100% !)); 1613-B-r4 (R3 slow state in the window (3 s / 90% !)); 1615-d3-r4 (R3 slow state in the window (1 s / 98% !))
- PASS: scored runs by TimerQueue mode (arm config; precise wins over the env var): spin 12 (onset 12, in the window 12); blocking 4 (onset 4, in the window 4)
- PASS: 3-mode timerq mode = arm config on all 16 scored runs

## R4 scene against the pooled d0 windows: PASS

- PASS: reference draws/frame p50 226 (expected 226), add-on threshold 0.020 (floor 0.02, factor 2.0, largest LOO 0.000), light max 0.01, draws tol 2
- PASS: d0 (reference, leave-one-out): 4 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226/226, light in window max 0.0%, off-scene 0
- PASS: B vs d0: 3 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226, light in window max 0.0%, off-scene 0
- PASS: d3 vs d0: 4 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226/226, light in window max 0.0%, off-scene 0
- PASS: d11t vs d0: 4 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226/226, light in window max 0.0%, off-scene 0

## R5 result, sensitivity pass (--no-drop: every kept run, the R3/R4/R6 drops ignored; proof from R7): NOTE

- NOTE: sensitivity pass: 15 kept runs used; the normal pass drops 15 of them: 1542-d0-r1 (R3 slow state in the window (93 s / 35% !)); 1545-B-r1 (R3 slow state in the window (94 s / 32% !)); 1547-d3-r1 (R3 slow state in the window (76 s / 70% !)); 1549-d11t-r1 (R3 slow state in the window (61 s / 96% !)); 1553-d3-r2 (R3 slow state in the window (84 s / 54% !)); 1556-d11t-r2 (R3 slow state in the window (63 s / 96% !)); 1558-d0-r2 (R3 slow state in the window (72 s / 76% !)); 1600-d3-r3 (R3 slow state in the window (54 s / 100% !)); 1602-d11t-r3 (R3 slow state in the window (1 s / 96% !)); 1604-d0-r3 (R3 slow state in the window (2 s / 100% !)); 1606-B-r3 (R3 slow state in the window (4 s / 100% !)); 1608-d11t-r4 (R3 slow state in the window (1 s / 100% !)); 1611-d0-r4 (R3 slow state in the window (4 s / 100% !)); 1613-B-r4 (R3 slow state in the window (3 s / 90% !)); 1615-d3-r4 (R3 slow state in the window (1 s / 98% !))
- NOTE: left here but not in the add-on's clean set: 1542-d0-r1, 1545-B-r1, 1547-d3-r1, 1549-d11t-r1, 1553-d3-r2, 1556-d11t-r2, 1558-d0-r2, 1600-d3-r3, 1602-d11t-r3, 1604-d0-r3, 1606-B-r3, 1608-d11t-r4, 1611-d0-r4, 1613-B-r4, 1615-d3-r4
- NOTE: B: round-1 run 1545-B-r1 fps 317.1 is more than 1% outside rounds 2+ (230.8..275.8)
- NOTE: d11t: round-1 run 1549-d11t-r1 fps 206.4 is more than 1% outside rounds 2+ (220.6..277.2)
- NOTE: pairs skipped (arm not in this matrix): d11:s0, d11t:s0, d11p:s0, d11t:d11, d11p:d11t, d11p:d11

| arm | n | fps | p50 ms | p99 ms | 1% low fps | >33 ms/min | vs d0: fps / p50 / p99 / 1% low / >33 | paired fps by round (up / rounds) | decision |
|---|---|---|---|---|---|---|---|---|---|
| d0 | 4 | 239.7 (213.9..270.4) | 3.399 (3.069..3.734) | 10.73 (9.92..10.96) | 83.4 (82.5..85.9) | 0.0 (0.0..0.0) | - | - | reference |
| B | 3 | 275.8 (230.8..317.1) | 3.033 (2.884..3.435) | 10.01 (9.40..10.99) | 89.7 (83.5..93.4) | 0.0 (0.0..0.0) | +15.1% overlap / -10.8% overlap / -6.7% overlap / +7.5% overlap / +0.0/min overlap | +23.7% (3 / 3) | verdict: fps +15.1% overlap |
| d3 | 4 | 248.9 (198.4..298.6) | 3.215 (2.894..4.264) | 10.49 (9.71..12.90) | 85.2 (70.6..90.5) | 0.0 (0.0..0.0) | +3.8% overlap / -5.4% overlap / -2.3% overlap / +2.1% overlap / +0.0/min overlap | +0.3% (2 / 4) | verdict: fps +3.8% overlap |
| d11t | 4 | 237.7 (206.4..277.2) | 3.363 (3.025..3.857) | 10.94 (9.87..12.17) | 82.1 (72.7..87.3) | 0.0 (0.0..0.0) | -0.8% overlap / -1.1% overlap / +1.9% overlap / -1.6% overlap / +0.0/min overlap | +0.4% (2 / 4) | verdict: fps -0.8% overlap |

## R6 background CPU in the window (add-on BG+ / SAT): DROP

- PASS: background cores (median per window) over 16 scored runs: median 8.14, max 8.67; BG+ reference 7.94 (median of this matrix's 10 unsaturated scored runs (20261122-0013 has none)), margin 1.0
- DROP: dropped (left out of the add-on's clean table too): 1542-d0-r1 SAT 8.41; 1547-d3-r1 SAT 8.13; 1549-d11t-r1 SAT 8.59; 1600-d3-r3 SAT 8.20; 1611-d0-r4 SAT 8.15

## R7 proof per run (matrix.json arm config; TimerQueue: spin > 20%, blocking / precise < 15% of a core, NOTE from 5%): NOTE

- PASS: unscored: 1541-cold-d0 (d0, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue -% (max 1 s -%), bin devoff2-bin
- NOTE: 1541-cold-d0: TimerQueue CPU unknown (no threads.csv)
- PASS: 1542-d0-r1 (d0, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 47.2% (max 1 s 75.3%), bin devoff2-bin
- PASS: 1545-B-r1 (B, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 41.4% (max 1 s 78.3%), bin devoffb-bin
- PASS: 1547-d3-r1 (d3, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 55.5% (max 1 s 75.5%), bin devoff3-bin
- PASS: 1549-d11t-r1 (d11t, blocking wait): 1 ms lines 1, precise lines 0, REX_TIMER_WAIT_BLOCKING =1, TimerQueue 6.0% (max 1 s 11.5%), bin devoff2-bin
- NOTE: 1549-d11t-r1: TimerQueue 6.0% is at or above the README gate 5% (read-out gate 15%; W4b d11t 5.0-6.0%)
- PASS: 1551-B-r2 (B, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 55.9% (max 1 s 72.1%), bin devoffb-bin
- PASS: 1553-d3-r2 (d3, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 46.8% (max 1 s 78.6%), bin devoff3-bin
- PASS: 1556-d11t-r2 (d11t, blocking wait): 1 ms lines 1, precise lines 0, REX_TIMER_WAIT_BLOCKING =1, TimerQueue 5.0% (max 1 s 11.7%), bin devoff2-bin
- NOTE: 1556-d11t-r2: TimerQueue 5.0% is at or above the README gate 5% (read-out gate 15%; W4b d11t 5.0-6.0%)
- PASS: 1558-d0-r2 (d0, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 53.6% (max 1 s 74.7%), bin devoff2-bin
- PASS: 1600-d3-r3 (d3, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 61.3% (max 1 s 72.5%), bin devoff3-bin
- PASS: 1602-d11t-r3 (d11t, blocking wait): 1 ms lines 1, precise lines 0, REX_TIMER_WAIT_BLOCKING =1, TimerQueue 5.1% (max 1 s 11.0%), bin devoff2-bin
- NOTE: 1602-d11t-r3: TimerQueue 5.1% is at or above the README gate 5% (read-out gate 15%; W4b d11t 5.0-6.0%)
- PASS: 1604-d0-r3 (d0, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 60.6% (max 1 s 78.3%), bin devoff2-bin
- PASS: 1606-B-r3 (B, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 61.5% (max 1 s 75.9%), bin devoffb-bin
- PASS: 1608-d11t-r4 (d11t, blocking wait): 1 ms lines 1, precise lines 0, REX_TIMER_WAIT_BLOCKING =1, TimerQueue 5.6% (max 1 s 17.8%), bin devoff2-bin
- NOTE: 1608-d11t-r4: TimerQueue 5.6% is at or above the README gate 5% (read-out gate 15%; W4b d11t 5.0-6.0%)
- PASS: 1611-d0-r4 (d0, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 62.6% (max 1 s 82.3%), bin devoff2-bin
- PASS: 1613-B-r4 (B, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 54.3% (max 1 s 69.9%), bin devoffb-bin
- PASS: 1615-d3-r4 (d3, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 56.2% (max 1 s 70.5%), bin devoff3-bin

| arm | mode | scored runs | 1 ms lines | precise lines | REX_TIMER_WAIT_BLOCKING | TimerQueue % of a core: median (min..max) | max 1 s | proof |
|---|---|---|---|---|---|---|---|---|
| d0 | spin | 4 | 0/0/0/0 | 0/0/0/0 | absent/absent/absent/absent | 57.1 (47.2..62.6) | 82.3 | ok |
| B | spin | 4 | 0/0/0/0 | 0/0/0/0 | absent/absent/absent/absent | 55.1 (41.4..61.5) | 78.3 | ok |
| d3 | spin | 4 | 0/0/0/0 | 0/0/0/0 | absent/absent/absent/absent | 55.9 (46.8..61.3) | 78.6 | ok |
| d11t | blocking | 4 | 1/1/1/1 | 0/0/0/0 | 1/1/1/1 | 5.3 (5.0..6.0) | 17.8 | ok |

