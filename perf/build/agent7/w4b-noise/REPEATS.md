# Repeats note for the GO lines (W6-W10), from W5 (20261122-1756)

Agent 7, task #14, 2026-11-22 21:34. Made by `python -B build\agent7\w4b-noise\repeats.py -o build\agent7\w4b-noise\REPEATS.md --json build\agent7\w4b-noise\repeats.json`; read-only on `<workspace>\build\agent8\matrix\20261122-1756` (ref base; 15 kept runs; its read-out: T-std).

"Arms" = arms in the window, the ref included: 2-6 arms = 1-5 arms vs the ref (W6's draft has 6: s0 + 5). "±" = the 95 % CI half-width of one arm's GM delta vs the ref, as the read-out kit prints it, when every arm keeps all its runs. Minutes = the window itself (cold run + scored runs), not the gates before it.

## Short answer (Power mode as in W5)

- **repeats=3:** median ms ±3.8 % (6 arms) to ±4.9 % (2 arms); fps ±3.3 to ±4.2 %; 15 min (2 arms) to 40 min (6 arms).
- **repeats=4:** median ms ±3.2 % (6 arms) to ±3.7 % (2 arms); fps ±2.7 to ±3.2 %; 19 min (2 arms) to 53 min (6 arms).
- **repeats=5:** median ms ±2.8 % (6 arms) to ±3.1 % (2 arms); fps ±2.4 to ±2.7 %; 23 min (2 arms) to 66 min (6 arms).
- Each repeat adds A runs of 2.14 min. From 3 to 4 repeats the ± narrows by 17 % (6 arms) to 24 % (2 arms); from 4 to 5 by 11-16 %.
- An arm's true delta must be about 1.35-1.42 x its ± to give a `*` 80 % of the time: with 6 arms that is 5.3 / 4.5 / 4.0 % on median ms for 3 / 4 / 5 repeats.
- W5's CV is itself an estimate on df 10: another window on the same Power mode can give 0.70-1.75 x these ± (95 %). W4b (same overlay) had T-std CV 2.3 % on median ms, against W5's 2.1 %.
- Best performance: the CV is unknown; the formula and a guess are in the last section.

## 1. ± per arm, T-std (no round effect, as W5)

± = 100 (exp(t975(df) s sqrt(2/n)) - 1) %, df = A (n - 1); t975 = the kit's table (between entries the smaller df: df 24 uses 2.086). s = W5's T-std pooled SD of ln(value) over its 15 kept runs (df 10): median ms 2.1 %, fps 1.8 %, p99 4.1 %, 1 % low 5.0 %. A left-out run (invalid timing, excluded) lowers n for its arm and widens its ±.

**median ms** (± %, df):

| repeats | 2 arms (1 vs ref) | 3 arms (2 vs ref) | 4 arms (3 vs ref) | 5 arms (4 vs ref) | 6 arms (5 vs ref) |
|---|---|---|---|---|---|
| 3 | ±4.9 (4) | ±4.3 (6) | ±4.0 (8) | ±3.9 (10) | ±3.8 (12) |
| 4 | ±3.7 (6) | ±3.4 (9) | ±3.3 (12) | ±3.2 (15) | ±3.2 (18) |
| 5 | ±3.1 (8) | ±2.9 (12) | ±2.8 (16) | ±2.8 (20) | ±2.8 (24) |

**fps** (± %, df):

| repeats | 2 arms (1 vs ref) | 3 arms (2 vs ref) | 4 arms (3 vs ref) | 5 arms (4 vs ref) | 6 arms (5 vs ref) |
|---|---|---|---|---|---|
| 3 | ±4.2 (4) | ±3.7 (6) | ±3.5 (8) | ±3.4 (10) | ±3.3 (12) |
| 4 | ±3.2 (6) | ±3.0 (9) | ±2.8 (12) | ±2.8 (15) | ±2.7 (18) |
| 5 | ±2.7 (8) | ±2.5 (12) | ±2.5 (16) | ±2.4 (20) | ±2.4 (24) |

**Tails** (± %, p99 ms / 1 % low fps):

| repeats | 2 arms (1 vs ref) | 3 arms (2 vs ref) | 4 arms (3 vs ref) | 5 arms (4 vs ref) | 6 arms (5 vs ref) |
|---|---|---|---|---|---|
| 3 | ±9.7 / ±12.0 | ±8.5 / ±10.5 | ±8.0 / ±9.9 | ±7.7 / ±9.5 | ±7.6 / ±9.3 |
| 4 | ±7.3 / ±9.1 | ±6.8 / ±8.3 | ±6.5 / ±8.0 | ±6.4 / ±7.8 | ±6.3 / ±7.7 |
| 5 | ±6.2 / ±7.6 | ±5.8 / ±7.2 | ±5.6 / ±7.0 | ±5.6 / ±6.8 | ±5.6 / ±6.8 |

## 2. Minutes per window

From W5's run.json start/end: the cold run's slot 1.85 min, then one slot of 2.14 min per scored run (start to start; a run lasts 120 s on average, the gap is 9 s), and the last run 1.99 min. Window = cold slot + (A n - 1) slots + the last run = 1.70 + 2.14 x A n min. For W5's own 15 runs that is its measured 33.9 min (17:56:02-18:29:54), by construction. Not included: the quiet gate and the other gates before the cold run, and the read-out.

Minutes (scored runs):

| repeats | 2 arms (1 vs ref) | 3 arms (2 vs ref) | 4 arms (3 vs ref) | 5 arms (4 vs ref) | 6 arms (5 vs ref) |
|---|---|---|---|---|---|
| 3 | 14.6 (6) | 21.0 (9) | 27.4 (12) | 33.9 (15) | 40.3 (18) |
| 4 | 18.9 (8) | 27.4 (12) | 36.0 (16) | 44.6 (20) | 53.2 (24) |
| 5 | 23.1 (10) | 33.9 (15) | 44.6 (20) | 55.3 (25) | 66.0 (30) |

## 3. If a window has a round effect (B-block T-std)

B-block spends rounds - 1 df on the rounds: df = (A - 1)(n - 1). It pays when the round effect is large (W4b: CV 2.3 -> 1.4 % on median ms); with few arms the df cost is large. Median ms at W5's T-std s (± %, df):

| repeats | 2 arms (1 vs ref) | 3 arms (2 vs ref) | 4 arms (3 vs ref) | 5 arms (4 vs ref) | 6 arms (5 vs ref) |
|---|---|---|---|---|---|
| 3 | ±7.6 (2) | ±4.9 (4) | ±4.3 (6) | ±4.0 (8) | ±3.9 (10) |
| 4 | ±4.8 (3) | ±3.7 (6) | ±3.4 (9) | ±3.3 (12) | ±3.2 (15) |
| 5 | ±3.7 (4) | ±3.1 (8) | ±2.9 (12) | ±2.8 (16) | ±2.8 (20) |

In W5 (no round effect) B-block's own s was 2.3 % on median ms (df 8), so there T-std applies.

## 4. Smallest true delta seen 80 % of the time (median ms, T-std)

100 (exp((t975 + t0.80) s sqrt(2/n)) - 1) %, with t0.80 the 80 % t quantile on the same df. Smaller true deltas are mostly read as "not shown", not as "no effect".

| repeats | 2 arms (1 vs ref) | 3 arms (2 vs ref) | 4 arms (3 vs ref) | 5 arms (4 vs ref) | 6 arms (5 vs ref) |
|---|---|---|---|---|---|
| 3 | 6.6 | 5.9 | 5.6 | 5.4 | 5.3 |
| 4 | 5.1 | 4.8 | 4.6 | 4.5 | 4.5 |
| 5 | 4.3 | 4.1 | 4.0 | 4.0 | 4.0 |

## 5. How sure the CV is

- W5's s comes from df 10. Its 95 % range is 0.70-1.75 x s (chi-square), and every ± above scales with s (nearly in proportion): for median ms, s could be 1.5-3.7 %.
- W4b, on the same overlay, had T-std CV 2.3 % (median ms, df 11) and 4.1 % (fps); W5 has 2.1 % and 1.8 %. So about 2 % on median ms looks typical for this Power mode.
- W5's 12 kept runs without the host flag (guard c: s0-r2, base-r2, d11t-r3) have s = 1.5 % on median ms and 1.2 % on fps (df 7). That is the CV when no run hits the P-thread / E-core clock state.

## 6. Best performance (CV unknown)

If the user switches Power mode to Best performance, W5's CV no longer applies: the clocks, E-core parking and heat change, and no window has been measured on it.

- Formula: ± = 100 (exp(t975(A (n - 1)) CV sqrt(2/n)) - 1) %, CV = the T-std pooled SD of ln(value) as a fraction (the kit's "pooled CV %" column / 100). Minutes as in section 2.
- Guess: CV 1-3 % on median ms. Low end: no host-flag runs (W5's unflagged runs: 1.5 %; W4b B-block T-std: 1.4 %). High end: W5's 2.1 % plus heat or turbo swings. The first Best-performance window measures it.

± % at CV 1 / 2 / 3 % (T-std df):

| repeats | 2 arms (1 vs ref) | 3 arms (2 vs ref) | 4 arms (3 vs ref) | 5 arms (4 vs ref) | 6 arms (5 vs ref) |
|---|---|---|---|---|---|
| 3 | 2.3 / 4.6 / 7.0 | 2.0 / 4.1 / 6.2 | 1.9 / 3.8 / 5.8 | 1.8 / 3.7 / 5.6 | 1.8 / 3.6 / 5.5 |
| 4 | 1.7 / 3.5 / 5.3 | 1.6 / 3.3 / 4.9 | 1.6 / 3.1 / 4.7 | 1.5 / 3.1 / 4.6 | 1.5 / 3.0 / 4.6 |
| 5 | 1.5 / 3.0 / 4.5 | 1.4 / 2.8 / 4.2 | 1.3 / 2.7 / 4.1 | 1.3 / 2.7 / 4.0 | 1.3 / 2.7 / 4.0 |

