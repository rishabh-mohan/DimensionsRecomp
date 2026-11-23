| bench | case | median ns/op | run medians |
|---|---|---:|---|
| log_throttle | 1T old fetch_add, 3 sites/draw | 34.230 | 31.923-59.850 |
| log_throttle | 1T new TakeLogBudget, 3 sites/draw | 1.753 | 1.345-2.639 |
| log_throttle | 2T old fetch_add, 3 sites/draw | 157.305 | 127.483-173.036 |
| log_throttle | 2T new TakeLogBudget, 3 sites/draw | 1.810 | 1.707-2.592 |
| cached_flag | per draw old: 5 flag calls + 20 guarded LongProbe | 46.967 | 43.481-52.689 |
| cached_flag | per draw new: 25 cached-flag checks | 15.162 | 13.909-18.801 |
| cached_flag | one check old NativeTextureTimingEnabled() | 2.351 | 1.996-2.733 |
| cached_flag | one check new TimingEnabled() | 0.679 | 0.639-0.861 |
| cached_flag | one check old LongProbeEnabled() | 1.404 | 1.315-1.628 |
| cached_flag | one check new LongProbeEnabled() | 0.742 | 0.662-0.856 |
| tls_accessor | no preparation: old 12 accessor calls | 92.583 | 43.102-130.981 |
| tls_accessor | no preparation: new 3 accessor calls | 23.471 | 13.744-41.008 |
| tls_accessor | no preparation: old sequence, inline accessor | 55.092 | 27.090-79.652 |
| tls_accessor | preparation: old 14 accessor calls | 82.374 | 46.290-128.404 |
| tls_accessor | preparation: new 3 accessor calls | 37.204 | 21.249-74.887 |
| tls_accessor | preparation: old sequence, inline accessor | 76.796 | 34.275-89.350 |
| query_scope | N=0 1T old lock+none_of | 44.005 | 32.834-61.688 |
| query_scope | N=0 1T new atomic count | 2.499 | 1.619-2.811 |
| query_scope | N=0 2T old lock+none_of | 90.992 | 75.529-109.856 |
| query_scope | N=0 2T new atomic count | 2.435 | 2.044-2.692 |
| query_scope | N=16 1T old lock+none_of | 65.553 | 43.563-71.848 |
| query_scope | N=16 1T new atomic count | 2.321 | 1.909-2.724 |
| query_scope | N=16 2T old lock+none_of | 114.892 | 100.959-137.355 |
| query_scope | N=16 2T new atomic count | 2.425 | 2.085-2.846 |
| query_scope | N=64 1T old lock+none_of | 164.946 | 145.895-218.793 |
| query_scope | N=64 1T new atomic count | 2.132 | 1.913-2.533 |
| query_scope | N=64 2T old lock+none_of | 285.946 | 275.466-360.760 |
| query_scope | N=64 2T new atomic count | 2.108 | 2.070-2.610 |
| query_scope | N=256 1T old lock+none_of | 1131.398 | 796.142-1327.822 |
| query_scope | N=256 1T new atomic count | 2.248 | 1.990-2.643 |
| query_scope | N=256 2T old lock+none_of | 2476.016 | 1747.110-2950.472 |
| query_scope | N=256 2T new atomic count | 2.348 | 1.984-2.940 |
