# W4b read-out add-on (Agent 7, task #29): <workspace>\build\agent8\matrix\20261122-0349

Session 3 functional checks (agent slot, hidden desktop, NOT timing): d0t = devoff2 + REX_TIMER_WAIT_BLOCKING=1, d11t = window 3's d11 + REX_TIMER_WAIT_BLOCKING=1 (Agent 11), d0f = devoff2

- command: `python bench\agent7\w4b_readout\w4b_readout.py build\agent8\matrix\20261122-0349 --all --scene-floor 0.02 -o build\agent8\readout\dry\0349\w4b.md --json build\agent8\readout\dry\0349\w4b.json`
- reference arm: d0f; 3 result rows, 3 scored, 3 kept (kept = scored, frame stats, no real problems, valid timing or not (--all), not excluded)
- window: each run's scored window as the runner cut it (frames.json window.first_row / rows of the frame csv it names); frames with a frame time <= 0 left out
- fps = frames / summed frame time; p50, p99 nearest-rank; 1% low = 1000 / mean of the slowest max(1, n // 100) frame times, in fps; >33 ms/min = frames over 33 ms per minute of summed frame time; arm cells = median (min..max) across the kept runs; n<3! = fewer than 3 kept runs

> **FUNCTIONAL ONLY**: 3 of 3 kept runs are not valid timing (kept by --all). Do not use these numbers as timing results.

> **CPU SATURATED**: 3 of 3 kept runs with sys.csv had a median busy share >= 0.97 in the window (SAT): the game shared the CPU with >= 9.9 cores of other work (median). More load (Defender) cannot raise that reading; it takes CPU from the game. Treat the timing of SAT runs as contended; every kept run is SAT, so SAT drops no run from the clean table.

## Arms (kept runs)

| arm | ref | n | fps | fps spread % | p50 ms | p99 ms | 1% low fps | >33 ms/min | slow state in window | scene flags | background cores (BG+ / SAT runs) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| d0t |  | 1 n<3! | 78.0 (78.0..78.0) | 0.0 | 7.622 (7.622..7.622) | 73.72 (73.72..73.72) | 10.5 (10.5..10.5) | 483.5 (483.5..483.5) | 1 of 1 | 0 | 9.9 (9.9..9.9) (0 / 1) |
| d11t |  | 1 n<3! | 62.0 (62.0..62.0) | 0.0 | 7.167 (7.167..7.167) | 71.31 (71.31..71.31) | 12.0 (12.0..12.0) | 687.6 (687.6..687.6) | 1 of 1 | 0 | 10.2 (10.2..10.2) (0 / 1) |
| d0f | * | 1 n<3! | 52.2 (52.2..52.2) | 0.0 | 9.405 (9.405..9.405) | 80.93 (80.93..80.93) | 10.0 (10.0..10.0) | 705.3 (705.3..705.3) | 1 of 1 | 0 | 9.7 (9.7..9.7) (0 / 1) |

Deltas against d0f: arm median vs d0f median; better / worse only when every run of the arm lies outside the d0f range, else overlap.

| arm | n vs n | d fps | d p50 | d p99 | d 1% low | d >33 ms/min | paired d fps by round: median (rounds up / rounds) |
|---|---|---|---|---|---|---|---|
| d0t | 1 vs 1 | +49.6% better | -19.0% better | -8.9% better | +4.6% better | -221.8/min better | +49.6% (1 / 1) |
| d11t | 1 vs 1 | +18.8% better | -23.8% better | -11.9% better | +20.0% better | -17.7/min better | +18.8% (1 / 1) |

## Arms without runs that have the slow state in the window, a scene flag or a background flag

(no kept runs)

## Runs

| seq | round | arm | rep | kept | fps | p50 ms | p99 ms | 1% low fps | >33 ms/min | window s | check | draws/frame p50 (mean) | scene | phase | slow (recheck) | slow (timerq) | game cores | background cores (p90; busy %) | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | d0t | 1 | yes | 78.0 | 7.622 | 73.72 | 10.5 | 483.5 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.32) | 69 s / 84% ! | 69 s / 47% | 2.00 | >=9.9 (p90 10.2; busy 99%) SAT | not timing (kept: --all) |
| 2 | 1 | d11t | 1 | yes | 62.0 | 7.167 | 71.31 | 12.0 | 687.6 | 50.0 | ok | 226 (226) | 0.000 | normal (DAT fails 34, <4.5 ms 0.18) | 42 s / 44% ! | 42 s / 34% | 1.77 | >=10.2 (p90 10.4; busy 100%) SAT | not timing (kept: --all) |
| 3 | 1 | d0f | 1 | yes | 52.2 | 9.405 | 80.93 | 10.0 | 705.3 | 50.0 | ok | 226 (226) | ref (only run) | normal (DAT fails 34, <4.5 ms 0.12) | 61 s / 100% ! | 61 s / 48% | 2.23~ | >=9.7 (p90 10.0; busy 100%) SAT | not timing (kept: --all) |

## Scene check (draws per frame against the pooled d0f windows)

- distance: 1-D Wasserstein distance between the time-weighted distributions of ln(1 + perf.csv draw_calls) over the scored windows (0.10 ~ draws about 10 % apart on average; +-1 draw jitter ~0.005); `loo` = a reference run against the pool of the other reference runs
- reference pool: 1 kept runs (0354-d0f-r1); time-weighted draws/frame p50 226, mean 226
- threshold: max(floor 0.02, 2.0 x largest leave-one-out distance -) = 0.020 (fewer than 2 reference runs: floor only)
- flagged SCENE?: none
- per-run time-weighted mean draws/frame per 10 s of the window are in the --json output (draws_10s)

## Slow state

- slow (recheck): matrix_recheck.slow_state, imported read-only from bench/agent8/run/matrix_recheck.py: E-cores under 800 MHz for 3+ sys.csv samples in a row; onset s after the first-frame signal / share of window samples; `!` = such a stretch overlaps the window (Agent 11: not a result); `no` = never; `-` = no sys.csv
- scored runs with the slow state in the window: 0349-d0t-r1, 0352-d11t-r1, 0354-d0f-r1
- slow (timerq): bench/agent11/timerq_slowstate.ps1, ran `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\timerq_slowstate.ps1 -Root <workspace>\build\agent8\matrix -Since 20261122-0349 -EMhz 800 -MinRows 3`; onset s after the first frame / share of the samples from the first frame to the last sample; 3 of 3 runs matched

## Background load (system CPU minus the game's CPU over the scored window)

- system = logical CPUs x min(1, cpu_util_pct / cpu_perf_pct) per sys.csv sample whose interval centre lies in the window (_Total % Processor Utility / % Processor Performance = the busy share without the frequency scaling); game = the slope of proc.csv cpu_s over the same interval; background = system - game
- game cores = cpu_s over the whole scored window (`~` = run.json window_cpu_cores_mean, where proc.csv does not cover the window); background cell = median (p90; median busy %) over the window samples
- SAT = median busy share >= 0.97: no spare CPU, so the background reading is a floor (`>=`): more load cannot raise it, it takes CPU from the game instead
- BG+ = not SAT and background > reference + 1.0 cores; reference: none (no unsaturated scored run with sys.csv here or in 20261122-0013)
- reference dir 20261122-0013: 16 scored runs, 0 with sys.csv (0 of them SAT), so it gives no background value; game cores there (median per arm, proc.csv over the scored window): d0 3.43 (n=4), base 3.42 (n=4), d11 3.47 (n=4), n0 2.33 (n=4)
- SAT runs: 0349-d0t-r1, 0352-d11t-r1, 0354-d0f-r1
- BG+ runs: none

## Checks

- per run: 3 of 3 runs with a window agree with frames.json (frames, mean fps, p50, p99, >33) and with results.csv fps_mean
- arm fps (median of the kept runs) vs run-matrix summary.md (median of results.csv fps_mean over scored OK runs that are not excluded): d0t 78.008 vs 78.008; d11t 61.959 vs 61.959; d0f 52.159 vs 52.159

