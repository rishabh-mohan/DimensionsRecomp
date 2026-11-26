# S5 3D-only summary

- source: <workspace>\build\agent8\s5\matrix\20261125-1804\results.csv
- per arm: medians over scored runs with s3d_status OK and no excluding flag; VOID and excluded runs are counted, never averaged
- this table is descriptive; A/B claims come from the readout (bootstrap CIs), quoted as "not shown different" unless the CI excludes 0

| arm | scored | OK | VOID | excl | fps | median ms | p99 ms | 1% low fps | 3D start s | thermal share | powercap share | temp med C | gr MHz med | cap exp/seen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ship60 | 4 | 4 | 0 | 0 | 42.37 | 21.31 | 68.53 | 9.80 | 105.00 | 0.91 | 0.03 | 86.50 | 1267.00 | 60/60 |
| nat60 | 4 | 4 | 0 | 0 | 50.02 | 16.72 | 56.61 | 15.00 | 109.59 | 0.00 | 0.00 | 76.00 | 1031.00 | 60/60 |
| n4bp60 | 4 | 4 | 0 | 0 | 45.65 | 16.85 | 71.06 | 11.67 | 109.36 | 0.28 | 0.10 | 85.50 | 1666.75 | 60/60 |
| natU | 2 | 1 | 1 | 0 | 67.70 | 10.57 | 59.14 | 12.80 | 131.75 | 0.00 | 0.00 | 79.00 | 1732.00 | 0/0 |

## Runs

| # | round | arm | status | 3D | reached s | start s | span s | fps | median | p99 | 1% low fps | thermal | temp | cooldown s | flags | void reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0 | ship60 | OK | VOID | 102.39 | 128.38 | 33.663 | 30.745 | 27.253 | 118.536 | 3.627 | 0.0 | 86.0 | 60.1 | nongame_load | short_span: 33.7 s of frames after the 3D start (< 120 s) |
| 2 | 0 | nat60 | OK | VOID | 108.69 | 112.03 | 49.287 | 45.732 | 17.5507 | 58.0762 | 13.43 | 0.0 | 76.0 | 15 | nongame_load | short_span: 49.3 s of frames after the 3D start (< 120 s) |
| 3 | 0 | n4bp60 | OK | VOID | 107.54 | 110.87 | 49.919 | 21.855 | 36.1736 | 177.261 | 4.43 | 0.0 | 76.0 | 0 | nongame_load | short_span: 49.9 s of frames after the 3D start (< 120 s) |
| 4 | 1 | ship60 | OK | OK | 88.79 | 114.98 | 120.022 | 31.803 | 27.334 | 113.335 | 4.733 | 0.6417 | 86.0 | 0 | nongame_load |  |
| 5 | 1 | nat60 | OK | OK | 106.72 | 110.07 | 120.041 | 46.376 | 16.757 | 68.5097 | 12.067 | 0.0 | 75.0 | 20 | nongame_load |  |
| 6 | 1 | n4bp60 | OK | OK | 106.47 | 109.85 | 120.047 | 34.587 | 17.9109 | 136.251 | 5.728 | 0.0 | 79.0 | 0 | nongame_load |  |
| 7 | 1 | natU | OK | VOID | 157.3 | 160.66 | 110.422 | 49.247 | 14.5038 | 101.621 | 7.638 | 0.0 | 76.0 | 10 | nongame_load | short_span: 110.4 s of frames after the 3D start (< 120 s) |
| 8 | 2 | nat60 | OK | OK | 110.17 | 113.52 | 120.01 | 48.988 | 16.7261 | 70.5067 | 10.102 | 0.0 | 76.0 | 0 | nongame_load |  |
| 9 | 2 | n4bp60 | OK | OK | 107.06 | 110.41 | 120.04 | 44.444 | 16.8855 | 76.4106 | 10.604 | 0.1917 | 85.0 | 0 |  |  |
| 10 | 2 | natU | OK | OK | 128.38 | 131.75 | 120.047 | 67.698 | 10.5735 | 59.1352 | 12.803 | 0.0 | 79.0 | 10 |  |  |
| 11 | 2 | ship60 | OK | OK | 79.21 | 104.87 | 120.016 | 44.952 | 20.397 | 53.898 | 11.049 | 0.9333 | 87.0 | 0 |  |  |
| 12 | 3 | n4bp60 | OK | OK | 105.53 | 108.87 | 120.031 | 46.855 | 16.8105 | 65.7063 | 12.741 | 0.4417 | 86.0 | 15 |  |  |
| 13 | 3 | ship60 | OK | OK | 79.37 | 105.0 | 120.008 | 42.139 | 21.376 | 72.338 | 9.086 | 0.8917 | 86.0 | 5 |  |  |
| 14 | 3 | nat60 | OK | OK | 105.77 | 109.11 | 120.015 | 51.06 | 16.716 | 44.7145 | 17.928 | 0.0 | 76.5 | 15 |  |  |
| 15 | 4 | ship60 | OK | OK | 79.36 | 105.01 | 120.001 | 42.608 | 21.245 | 64.732 | 10.513 | 0.95 | 87.0 | 0 |  |  |
| 16 | 4 | nat60 | OK | OK | 105.4 | 108.75 | 120.008 | 51.855 | 16.7064 | 40.794 | 18.683 | 0.0 | 76.0 | 15 |  |  |
| 17 | 4 | n4bp60 | OK | OK | 105.26 | 108.6 | 120.021 | 48.325 | 16.8041 | 55.348 | 13.468 | 0.3667 | 86.0 | 0 |  |  |
