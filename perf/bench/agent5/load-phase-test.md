# Load-phase score: first 60 s after the first frame

Frames over 33/50/100 ms, hitch ms = sum of (frame - 33 ms) over those frames, max and p99 (nearest rank) from native-frames.csv; launch = runner process start; ff = first frame (game.log "Native presentation: frame=0"); title = draw-count switch; title max = max frame from 2 s before to 5 s after the switch; o20 5s+ = frames > 20 ms from 5 s to the window end (busy-machine indicator); ff->win s = first frame to the start of the runner's scored window on the frame clock (info flag win<60s below the floor). Excluded runs are listed but left out of the arm numbers.

## Runs

| run | arm | rep | bin | launch->ff s | ff src | ff->title s | launch->title s | draws | title max ms | frames | o33 | o50 | o100 | hitch ms | max ms | p99 ms | fps | o20 5s+ | ff->win s | excluded by | info |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0016-cold-n0 | n0 | cold | native2-bin | 12.97 | log | 31.03 | 44.00 | 0->8 | 14.7 | 11574 | 3 | 1 | 1 | 131 | 154.4 | 10.53 | 193 | 0 | 31.4 | cold | win<60s |
| 0030-n0-r1 | n0 | 1 | native2-bin | 12.74 | log | 31.18 | 43.91 | 0->8 | 12.9 | 11494 | 4 | 1 | 1 | 109 | 117.9 | 10.00 | 192 | 0 | 65.2 |  |  |
| 0042-n0-r2 | n0 | 2 | native2-bin | 13.58 | log | 30.97 | 44.55 | 0->8 | 16.0 | 11146 | 3 | 0 | 0 | 29 | 49.5 | 12.01 | 186 | 1 | 79.7 |  |  |
| 0054-n0-r3 | n0 | 3 | native2-bin | 13.20 | log | 30.94 | 44.14 | 0->8 | 13.8 | 11631 | 3 | 2 | 1 | 138 | 117.0 | 10.08 | 194 | 2 | 65.7 |  |  |
| 0104-n0-r4 | n0 | 4 | native2-bin | 17.17 | log | 30.63 | 47.80 | 0->8 | 14.0 | 11101 | 3 | 2 | 1 | 137 | 119.1 | 11.10 | 185 | 0 | 53.0 |  | win<60s |
| 2346-n0-r1 | n0 | 1 | native2-bin | 16.02 | log | 31.48 | 47.50 | 0->8 | 36.8 | 6695 | 32 | 3 | 1 | 465 | 294.2 | 29.61 | 112 | 295 | 41.1 |  | noisy win<60s |
| 0205-n1-r1 | n1 | 1 | native2-bin | 20.87 | log | 32.40 | 53.26 | 0->8 | 70.2 | 7987 | 88 | 21 | 0 | 984 | 86.8 | 34.50 | 133 | 234 | 30.4 |  | noisy win<60s |
| 0208-n3-r1 | n3 | 1 | native2-bin | 15.87 | log | 32.07 | 47.94 | 0->8 | 31.8 | 7658 | 27 | 8 | 1 | 426 | 119.8 | 23.55 | 128 | 117 | 30.2 |  | noisy win<60s |
| 0210-n2-r1 | n2 | 1 | native2-bin | 13.26 | tail | 32.55 | 45.81 | 0->8 | 41.5 | 9212 | 39 | 8 | 1 | 543 | 130.7 | 23.02 | 154 | 112 | 30.4 |  | noisy win<60s ff_tail |
| 0256-native3 | native3 | - | native3-bin | 14.38 | log | 31.61 | 45.98 | 0->8 | 27.2 | 8561 | 2 | 1 | 1 | 231 | 261.4 | 17.86 | 143 | 44 | - |  | cap240 noisy mode:boot |

## Arms (median [min..max] over the included runs)

| arm | n | excl | launch->ff s | ff->title s | launch->title s | title max ms | o33 | o50 | o100 | hitch ms | max ms | p99 ms | fps | o20 5s+ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n0 | 5 | 1 | 13.58 [12.74..17.17] | 30.97 [30.63..31.48] | 44.55 [43.91..47.80] | 14.0 [12.9..36.8] | 3 [3..32] | 2 [0..3] | 1 [0..1] | 137 [29..465] | 117.9 [49.5..294.2] | 11.10 [10.00..29.61] | 186 [112..194] | 1 [0..295] |
| n1 | 1 | 0 | 20.87 | 32.40 | 53.26 | 70.2 | 88 | 21 | 0 | 984 | 86.8 | 34.50 | 133 | 234 |
| n3 | 1 | 0 | 15.87 | 32.07 | 47.94 | 31.8 | 27 | 8 | 1 | 426 | 119.8 | 23.55 | 128 | 117 |
| n2 | 1 | 0 | 13.26 | 32.55 | 45.81 | 41.5 | 39 | 8 | 1 | 543 | 130.7 | 23.02 | 154 | 112 |
| native3 | 1 | 0 | 14.38 | 31.61 | 45.98 | 27.2 | 2 | 1 | 1 | 231 | 261.4 | 17.86 | 143 | 44 |

## Versus n0 (difference of medians; exact two-sided rank-sum p)

| arm | n vs n_ref | launch->ff s | ff->title s | launch->title s | title max ms | o33 | o50 | o100 | hitch ms | max ms | p99 ms | fps | o20 5s+ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n1 | 1 vs 5 | +7.29 (p -) | +1.43 (p -) | +8.71 (p -) | +56.3 (p -) | +85.0 (p -) | +19.0 (p -) | -1.0 (p -) | +846.5 (p -) | -31.1 (p -) | +23.41 (p -) | -52.6 (p -) | +233.0 (p -) |
| n3 | 1 vs 5 | +2.29 (p -) | +1.11 (p -) | +3.40 (p -) | +17.8 (p -) | +24.0 (p -) | +6.0 (p -) | +0.0 (p -) | +289.3 (p -) | +1.9 (p -) | +12.45 (p -) | -58.1 (p -) | +116.0 (p -) |
| n2 | 1 vs 5 | -0.32 (p -) | +1.58 (p -) | +1.26 (p -) | +27.5 (p -) | +36.0 (p -) | +6.0 (p -) | +0.0 (p -) | +406.3 (p -) | +12.9 (p -) | +11.93 (p -) | -32.2 (p -) | +111.0 (p -) |
| native3 | 1 vs 5 | +0.80 (p -) | +0.64 (p -) | +1.44 (p -) | +13.2 (p -) | -1.0 (p -) | -1.0 (p -) | +0.0 (p -) | +93.6 (p -) | +143.5 (p -) | +6.77 (p -) | -43.1 (p -) | +43.0 (p -) |

p is "-" below 2 runs per side. Smallest possible p: 0.10 at 3 vs 3, 0.029 at 4 vs 4, 0.008 at 5 vs 5. Small counts (o50, o100) tie often; ties give large p.
