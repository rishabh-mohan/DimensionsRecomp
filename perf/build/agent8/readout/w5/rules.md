# Read-out rules (w5_rules.py): <workspace>\build\agent8\matrix\20261122-1756

- inputs: results.csv, matrix.json; build\agent8\readout\w5\w5.json (add-on, ref base); build\agent8\readout\w5\phase.json; per run run.json, game*.log, threads.csv; build\agent8\readout\w5\timerq3.txt
- overall: FAIL (worst rule level; N/A < PASS < NOTE < DROP < FAIL; DROP = runs left out, FAIL = no trustworthy verdict; the decision columns of the R5 tables are the result)

## R0 complete and consistent: PASS

- PASS: 16 rows (expected 16), 15 scored, 15 kept by the add-on (kept = scored, frame stats, no real problems, valid timing, not excluded)
- PASS: scored runs per arm: base 3, s0 3, d11 3, d11t 3, d11p 3

## R1 runner exclusions: PASS

- PASS: no scored run excluded

## R2 foreground (fg_share in the window): PASS

- PASS: fg=1 (>= 0.99): 15 of 15 scored runs

## R3 slow state (timerq over the fg=1 runs): DROP

- PASS: fg=1 runs: N=15, with any onset (timerq) M=15 (1757-base-r1 at 87 s, 1800-s0-r1 at 40 s, 1802-d11-r1 at 6 s, 1804-d11t-r1 at 13 s, 1806-d11p-r1 at 3 s, 1808-s0-r2 at 21 s, 1810-d11-r2 at 35 s, 1813-d11t-r2 at 1 s, 1815-d11p-r2 at 2 s, 1817-base-r2 at 4 s, 1819-d11-r3 at 2 s, 1821-d11t-r3 at 4 s, 1823-d11p-r3 at 2 s, 1825-base-r3 at 22 s, 1827-s0-r3 at 2 s), in the window K=15 (1757-base-r1, 1800-s0-r1, 1802-d11-r1, 1804-d11t-r1, 1806-d11p-r1, 1808-s0-r2, 1810-d11-r2, 1813-d11t-r2, 1815-d11p-r2, 1817-base-r2, 1819-d11-r3, 1821-d11t-r3, 1823-d11p-r3, 1825-base-r3, 1827-s0-r3)
- NOTE: the slow state occurs with the game in the foreground: report to Agents 1 and 11
- DROP: dropped: 1757-base-r1 (R3 slow state in the window (87 s / 26% !)); 1800-s0-r1 (R3 slow state in the window (40 s / 68% !)); 1802-d11-r1 (R3 slow state in the window (6 s / 86% !)); 1804-d11t-r1 (R3 slow state in the window (13 s / 94% !)); 1806-d11p-r1 (R3 slow state in the window (3 s / 88% !)); 1808-s0-r2 (R3 slow state in the window (21 s / 94% !)); 1810-d11-r2 (R3 slow state in the window (35 s / 86% !)); 1813-d11t-r2 (R3 slow state in the window (1 s / 76% !)); 1815-d11p-r2 (R3 slow state in the window (2 s / 94% !)); 1817-base-r2 (R3 slow state in the window (4 s / 100% !)); 1819-d11-r3 (R3 slow state in the window (2 s / 76% !)); 1821-d11t-r3 (R3 slow state in the window (4 s / 100% !)); 1823-d11p-r3 (R3 slow state in the window (2 s / 96% !)); 1825-base-r3 (R3 slow state in the window (22 s / 72% !)); 1827-s0-r3 (R3 slow state in the window (2 s / 74% !))
- PASS: scored runs by TimerQueue mode (arm config; precise wins over the env var): spin 9 (onset 9, in the window 9); blocking 3 (onset 3, in the window 3); precise 3 (onset 3, in the window 3)
- PASS: 3-mode timerq mode = arm config on all 15 scored runs

## R4 scene against the pooled base windows: PASS

- PASS: reference draws/frame p50 226 (expected 226), add-on threshold 0.020 (floor 0.02, factor 2.0, largest LOO 0.000), light max 0.01, draws tol 2
- PASS: base (reference, leave-one-out): 3 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226, light in window max 0.0%, off-scene 0
- PASS: s0 vs base: 3 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226, light in window max 0.0%, off-scene 0
- PASS: d11 vs base: 3 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226, light in window max 0.0%, off-scene 0
- PASS: d11t vs base: 3 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226, light in window max 0.0%, off-scene 0
- PASS: d11p vs base: 3 kept runs, scene distance median 0.000 (max 0.000) vs threshold 0.020, draws p50 226/226/226, light in window max 0.0%, off-scene 0

## R5 result (runs left after R1, R3, R4, R6; proof from R7): FAIL

- PASS: 0 runs left of 15 kept; dropped from the kept runs 15: 1757-base-r1 (R3 slow state in the window (87 s / 26% !)); 1800-s0-r1 (R3 slow state in the window (40 s / 68% !)); 1802-d11-r1 (R3 slow state in the window (6 s / 86% !)); 1804-d11t-r1 (R3 slow state in the window (13 s / 94% !)); 1806-d11p-r1 (R3 slow state in the window (3 s / 88% !)); 1808-s0-r2 (R3 slow state in the window (21 s / 94% !)); 1810-d11-r2 (R3 slow state in the window (35 s / 86% !)); 1813-d11t-r2 (R3 slow state in the window (1 s / 76% !)); 1815-d11p-r2 (R3 slow state in the window (2 s / 94% !)); 1817-base-r2 (R3 slow state in the window (4 s / 100% !)); 1819-d11-r3 (R3 slow state in the window (2 s / 76% !)); 1821-d11t-r3 (R3 slow state in the window (4 s / 100% !)); 1823-d11p-r3 (R3 slow state in the window (2 s / 96% !)); 1825-base-r3 (R3 slow state in the window (22 s / 72% !)); 1827-s0-r3 (R3 slow state in the window (2 s / 74% !))
- PASS: the runs left are the add-on's clean set
- FAIL: reference arm base has 0 runs left (< 3): no verdict against it
- PASS: pairs: 6, same decision rule with the second arm as the reference (table below the main one)

| arm | n | fps | p50 ms | p99 ms | 1% low fps | >33 ms/min | vs base: fps / p50 / p99 / 1% low / >33 | paired fps by round (up / rounds) | decision |
|---|---|---|---|---|---|---|---|---|---|
| base | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| s0 | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| d11 | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| d11t | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |
| d11p | 0 | - | - | - | - | - | - | - | no verdict (no runs left) |

| pair (arm vs against) | n vs n | fps / p50 / p99 / 1% low / >33: arm median vs against | paired fps by round (up / rounds) | decision |
|---|---|---|---|---|
| d11 vs s0 | 0 vs 0 | - | - | no verdict (no runs left) |
| d11t vs s0 | 0 vs 0 | - | - | no verdict (no runs left) |
| d11p vs s0 | 0 vs 0 | - | - | no verdict (no runs left) |
| d11t vs d11 | 0 vs 0 | - | - | no verdict (no runs left) |
| d11p vs d11t | 0 vs 0 | - | - | no verdict (no runs left) |
| d11p vs d11 | 0 vs 0 | - | - | no verdict (no runs left) |

## R6 background CPU in the window (add-on BG+ / SAT): DROP

- PASS: background cores (median per window) over 15 scored runs: median 7.16, max 8.17; BG+ reference 7.16 (median of this matrix's 15 unsaturated scored runs (20261122-0013 has none)), margin 1.0
- DROP: dropped (left out of the add-on's clean table too): 1821-d11t-r3 BG+ 8.17

## R7 proof per run (matrix.json arm config; TimerQueue: spin > 20%, blocking / precise < 15% of a core, NOTE from 5%): NOTE

- PASS: unscored: 1756-cold-base (base, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue -% (max 1 s -%), bin devoff3-bin
- NOTE: 1756-cold-base: TimerQueue CPU unknown (no threads.csv)
- PASS: 1757-base-r1 (base, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 39.5% (max 1 s 69.3%), bin devoff3-bin
- PASS: 1800-s0-r1 (s0, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 50.6% (max 1 s 71.4%), bin devoff4-bin
- PASS: 1802-d11-r1 (d11, spin wait): 1 ms lines 1, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 49.0% (max 1 s 66.1%), bin devoff4-bin
- PASS: 1804-d11t-r1 (d11t, blocking wait): 1 ms lines 1, precise lines 0, REX_TIMER_WAIT_BLOCKING =1, TimerQueue 4.5% (max 1 s 10.0%), bin devoff4-bin
- PASS: 1806-d11p-r1 (d11p, precise wait): 1 ms lines 1, precise lines 1, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 5.2% (max 1 s 11.5%), bin devoff4-bin
- NOTE: 1806-d11p-r1: TimerQueue 5.2% is at or above the README gate 5% (read-out gate 15%; W4b d11t 5.0-6.0%)
- PASS: 1808-s0-r2 (s0, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 55.4% (max 1 s 67.5%), bin devoff4-bin
- PASS: 1810-d11-r2 (d11, spin wait): 1 ms lines 1, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 51.1% (max 1 s 64.9%), bin devoff4-bin
- PASS: 1813-d11t-r2 (d11t, blocking wait): 1 ms lines 1, precise lines 0, REX_TIMER_WAIT_BLOCKING =1, TimerQueue 4.0% (max 1 s 8.9%), bin devoff4-bin
- PASS: 1815-d11p-r2 (d11p, precise wait): 1 ms lines 1, precise lines 1, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 4.2% (max 1 s 11.3%), bin devoff4-bin
- PASS: 1817-base-r2 (base, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 60.5% (max 1 s 72.3%), bin devoff3-bin
- PASS: 1819-d11-r3 (d11, spin wait): 1 ms lines 1, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 47.5% (max 1 s 73.4%), bin devoff4-bin
- PASS: 1821-d11t-r3 (d11t, blocking wait): 1 ms lines 1, precise lines 0, REX_TIMER_WAIT_BLOCKING =1, TimerQueue 4.5% (max 1 s 14.2%), bin devoff4-bin
- PASS: 1823-d11p-r3 (d11p, precise wait): 1 ms lines 1, precise lines 1, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 5.9% (max 1 s 13.7%), bin devoff4-bin
- NOTE: 1823-d11p-r3: TimerQueue 5.9% is at or above the README gate 5% (read-out gate 15%; W4b d11t 5.0-6.0%)
- PASS: 1825-base-r3 (base, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 49.0% (max 1 s 75.6%), bin devoff3-bin
- PASS: 1827-s0-r3 (s0, spin wait): 1 ms lines 0, precise lines 0, REX_TIMER_WAIT_BLOCKING absent, TimerQueue 46.5% (max 1 s 64.0%), bin devoff4-bin

| arm | mode | scored runs | 1 ms lines | precise lines | REX_TIMER_WAIT_BLOCKING | TimerQueue % of a core: median (min..max) | max 1 s | proof |
|---|---|---|---|---|---|---|---|---|
| base | spin | 3 | 0/0/0 | 0/0/0 | absent/absent/absent | 49.0 (39.5..60.5) | 75.6 | ok |
| s0 | spin | 3 | 0/0/0 | 0/0/0 | absent/absent/absent | 50.6 (46.5..55.4) | 71.4 | ok |
| d11 | spin | 3 | 1/1/1 | 0/0/0 | absent/absent/absent | 49.0 (47.5..51.1) | 73.4 | ok |
| d11t | blocking | 3 | 1/1/1 | 0/0/0 | 1/1/1 | 4.5 (4.0..4.5) | 14.2 | ok |
| d11p | precise | 3 | 1/1/1 | 1/1/1 | absent/absent/absent | 5.2 (4.2..5.9) | 13.7 | ok |

