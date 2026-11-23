# Matrix recheck: <workspace>\build\agent8\matrix\20261122-0336

Window 4 (Agent 8, session 3): B = devoffB (codegen B) vs d0 = devoff2 (primary), then d3 = devoff3; optional d0t = devoff2 + REX_TIMER_WAIT_BLOCKING=1

6 result rows; 3 scored runs kept (0 of them with only benign problems); min window cover 90%; valid_timing ignored (--all); 0 scored runs flagged excluded (dropped).

## Runs

| seq | round | arm | rep | status | kept | median ms | fps | p99 ms | >33 | >100 | window s | marks s | ff->win s | light | cpu cores | top1 thread busy % (name) | gpu util % | flags | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | d0 | 0 | OK | no | 2.89 | 295.2 | 14.1 | 0 | 0 | 10.0 | 10.0 | 20.0 | 0.838 | 2.47 | - | - | light_share_high never_foreground | unscored (cold); not timing (desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default) |
| 2 | 0 | B | 0 | OK | no | 3.29 | 212.1 | 21.6 | 4 | 0 | 10.0 | 10.0 | 20.0 | 0.704 | 2.21 | - | - | light_share_high never_foreground | unscored (cold); not timing (desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default) |
| 3 | 0 | d3 | 0 | OK | no | 5.02 | 125.3 | 40.1 | 22 | 0 | 10.0 | 10.0 | 20.0 | 0.421 | 2.28 | - | - | never_foreground | unscored (cold); not timing (desktop WinSta0\exebox-DMTARMUBZWO2RQC7CO33E3NBBO is not WinSta0\Default) |
| 4 | 1 | d0 | 1 | OK | yes | 4.06 | 129.7 | 44.3 | 72 | 1 | 20.0 | 20.0 | 20.0 | 0.542 | 2.25 | 68.4 (XThread6940 (F80001AC)) | 39 | never_foreground |  |
| 5 | 1 | B | 1 | OK | yes | 3.37 | 190.2 | 34.6 | 48 | 1 | 20.0 | 20.0 | 20.0 | 0.714 | 2.45 | 67.7 (XThread159B8 (F80001A8)) | 47 | light_share_high never_foreground |  |
| 6 | 1 | d3 | 1 | OK | yes | 6.81 | 61.4 | 95.6 | 206 | 9 | 20.0 | 20.0 | 20.0 | 0.353 | 2.03 | 77.9 (XThread10CC (F80001A8)) | 27 | never_foreground |  |

`marks s` is the wall time between the measure marks (summary.txt `align` line); it should be close to the planned window. `ff->win s` is first-frame signal to window start (floor: min_window_after_ff_s); `light` is the share of window frames under light_ms; flags ending in `!` are excluding flags.

## Arms (kept runs)

| group | arm | ref | n | median of medians (min..max) ms | p99 ms | p99.9 ms | >33 ms per min | >100 ms per min | cpu cores (min..max) | boot s | fps | top1 thread busy % (min..max), n | thread cores | gpu util % mean (p90) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| w4 | d0 | * | 1 | 4.057 (4.057..4.057) | 44.3 | 69.0 | 215.6 | 2.99 | 2.25 (2.25..2.25) | 11.0 | 129.7 | 68.4 (68.4..68.4), 1 | 2.28 | 39 (55) |
| w4 | B |  | 1 | 3.374 (3.374..3.374) | 34.6 | 48.9 | 144.0 | 3.00 | 2.45 (2.45..2.45) | 11.0 | 190.2 | 67.7 (67.7..67.7), 1 | 2.44 | 47 (68) |
| w4 | d3 |  | 1 | 6.814 (6.814..6.814) | 95.6 | 253.5 | 617.3 | 26.97 | 2.03 (2.03..2.03) | 10.0 | 61.4 | 77.9 (77.9..77.9), 1 | 2.04 | 27 (34) |

## Deltas against each group reference

| group | arm | vs | delta median ms (%) | paired by round: median delta (min..max), rounds faster | delta p99 ms | delta >33/min | delta cpu cores | delta fps % | paired delta top1 busy pts (n) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| w4 | B | d0 | -0.683 (-16.8%) | -0.683 (-0.683..-0.683), 1 of 1 | -9.7 | -71.6 | 0.20 | 46.7 | -0.7 (1) | FASTER: every run below the reference range |
| w4 | d3 | d0 | 2.757 (68.0%) | 2.757 (2.757..2.757), 0 of 1 | 51.2 | 401.7 | -0.22 | -52.7 | 9.5 (1) | SLOWER: every run above the reference range |

## One-line results

- B vs d0: median 3.37 vs 4.06 ms (delta -0.68, -16.8%; paired -0.68, 1/1 rounds faster), fps 190.2 vs 129.7 (46.7%), p99 34.6 vs 44.3, >33/min 144.0 vs 215.6, >100/min 3.00 vs 2.99, cpu 2.45 vs 2.25 cores, top1 thread busy 67.7 vs 68.4 % (paired -0.7); ref range 4.06..4.06; n 1/1; FASTER: every run below the reference range
- d3 vs d0: median 6.81 vs 4.06 ms (delta 2.76, 68.0%; paired 2.76, 0/1 rounds faster), fps 61.4 vs 129.7 (-52.7%), p99 95.6 vs 44.3, >33/min 617.3 vs 215.6, >100/min 26.97 vs 2.99, cpu 2.03 vs 2.25 cores, top1 thread busy 77.9 vs 68.4 % (paired 9.5); ref range 4.06..4.06; n 1/1; SLOWER: every run above the reference range
