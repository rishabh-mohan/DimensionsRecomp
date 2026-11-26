# S5 3D-only summary

- source: <workspace>\build\agent16\natcmp\matrix\20261126-015410\06-s4-ship60\results.csv
- per arm: medians over scored runs with s3d_status OK and no excluding flag; VOID and excluded runs are counted, never averaged
- this table is descriptive; A/B claims come from the readout (bootstrap CIs), quoted as "not shown different" unless the CI excludes 0

| arm | scored | OK | VOID | excl | fps | median ms | p99 ms | 1% low fps | 3D start s | thermal share | powercap share | temp med C | gr MHz med | cap exp/seen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ship60 | 1 | 1 | 0 | 0 | 44.94 | 21.18 | 51.63 | 11.51 | 105.02 | 0.94 | 0.05 | 87.00 | 1252.00 | 60/60 |

## Runs

| # | round | arm | status | 3D | reached s | start s | span s | fps | median | p99 | 1% low fps | thermal | temp | cooldown s | flags | void reason |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | ship60 | OK | OK | 79.37 | 105.02 | 120.017 | 44.935 | 21.184 | 51.633 | 11.506 | 0.9417 | 87.0 | 0 |  |  |
