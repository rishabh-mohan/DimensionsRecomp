# S5 3D-only summary

- source: <workspace>\build\agent16\natcmp\matrix\20261126-015410\01-prime-ship60\results.csv
- per arm: medians over scored runs with s3d_status OK and no excluding flag; VOID and excluded runs are counted, never averaged
- this table is descriptive; A/B claims come from the readout (bootstrap CIs), quoted as "not shown different" unless the CI excludes 0

| arm | scored | OK | VOID | excl | fps | median ms | p99 ms | 1% low fps | 3D start s | thermal share | powercap share | temp med C | gr MHz med | cap exp/seen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ship60 | 1 | 1 | 0 | 0 | 46.35 | 19.55 | 52.95 | 12.18 | 104.45 | 0.92 | 0.04 | 87.00 | 1320.00 | 60/60 |

## Runs

| # | round | arm | status | 3D | reached s | start s | span s | fps | median | p99 | 1% low fps | thermal | temp | cooldown s | flags | void reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | ship60 | OK | OK | 78.78 | 104.45 | 120.016 | 46.352 | 19.549 | 52.945 | 12.182 | 0.9167 | 87.0 | 0 |  |  |
