# S5 3D-only summary

- source: <workspace>\build\agent16\natcmp\matrix\20261126-015410\02-prime-n4bp60\results.csv
- per arm: medians over scored runs with s3d_status OK and no excluding flag; VOID and excluded runs are counted, never averaged
- this table is descriptive; A/B claims come from the readout (bootstrap CIs), quoted as "not shown different" unless the CI excludes 0

| arm | scored | OK | VOID | excl | fps | median ms | p99 ms | 1% low fps | 3D start s | thermal share | powercap share | temp med C | gr MHz med | cap exp/seen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n4bp60 | 1 | 1 | 0 | 0 | 47.04 | 16.78 | 69.47 | 11.31 | 108.63 | 0.35 | 0.13 | 86.00 | 1642.00 | 60/60 |

## Runs

| # | round | arm | status | 3D | reached s | start s | span s | fps | median | p99 | 1% low fps | thermal | temp | cooldown s | flags | void reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | n4bp60 | OK | OK | 105.28 | 108.63 | 120.027 | 47.04 | 16.7762 | 69.4685 | 11.309 | 0.35 | 86.0 | 20 |  |  |
