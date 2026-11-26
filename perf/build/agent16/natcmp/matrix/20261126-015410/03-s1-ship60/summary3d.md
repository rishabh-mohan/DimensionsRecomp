# S5 3D-only summary

- source: <workspace>\build\agent16\natcmp\matrix\20261126-015410\03-s1-ship60\results.csv
- per arm: medians over scored runs with s3d_status OK and no excluding flag; VOID and excluded runs are counted, never averaged
- this table is descriptive; A/B claims come from the readout (bootstrap CIs), quoted as "not shown different" unless the CI excludes 0

| arm | scored | OK | VOID | excl | fps | median ms | p99 ms | 1% low fps | 3D start s | thermal share | powercap share | temp med C | gr MHz med | cap exp/seen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ship60 | 1 | 1 | 0 | 0 | 44.20 | 21.29 | 54.01 | 11.10 | 105.00 | 0.96 | 0.02 | 87.00 | 1256.00 | 60/60 |

## Runs

| # | round | arm | status | 3D | reached s | start s | span s | fps | median | p99 | 1% low fps | thermal | temp | cooldown s | flags | void reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | ship60 | OK | OK | 79.38 | 105.0 | 120.007 | 44.197 | 21.287 | 54.011 | 11.102 | 0.9583 | 87.0 | 0 |  |  |
