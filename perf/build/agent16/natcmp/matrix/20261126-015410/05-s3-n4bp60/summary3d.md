# S5 3D-only summary

- source: <workspace>\build\agent16\natcmp\matrix\20261126-015410\05-s3-n4bp60\results.csv
- per arm: medians over scored runs with s3d_status OK and no excluding flag; VOID and excluded runs are counted, never averaged
- this table is descriptive; A/B claims come from the readout (bootstrap CIs), quoted as "not shown different" unless the CI excludes 0

| arm | scored | OK | VOID | excl | fps | median ms | p99 ms | 1% low fps | 3D start s | thermal share | powercap share | temp med C | gr MHz med | cap exp/seen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n4bp60 | 1 | 1 | 0 | 0 | 46.83 | 16.80 | 65.26 | 11.54 | 108.89 | 0.33 | 0.13 | 86.00 | 1687.00 | 60/60 |

## Runs

| # | round | arm | status | 3D | reached s | start s | span s | fps | median | p99 | 1% low fps | thermal | temp | cooldown s | flags | void reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | n4bp60 | OK | OK | 105.54 | 108.89 | 120.04 | 46.834 | 16.8037 | 65.2617 | 11.538 | 0.325 | 86.0 | 0 |  |  |
