| bench | case | median ns/op | run medians |
|---|---|---:|---|
| log_throttle | 1T old fetch_add, 3 sites/draw | 31.055 | 31.055-31.055 |
| log_throttle | 1T new TakeLogBudget, 3 sites/draw | 1.690 | 1.690-1.690 |
| log_throttle | 2T old fetch_add, 3 sites/draw | 147.822 | 147.822-147.822 |
| log_throttle | 2T new TakeLogBudget, 3 sites/draw | 1.572 | 1.572-1.572 |
| cached_flag | per draw old: 5 flag calls + 20 guarded LongProbe | 54.984 | 54.984-54.984 |
| cached_flag | per draw new: 25 cached-flag checks | 18.009 | 18.009-18.009 |
| cached_flag | one check old NativeTextureTimingEnabled() | 2.651 | 2.651-2.651 |
| cached_flag | one check new TimingEnabled() | 0.992 | 0.992-0.992 |
| cached_flag | one check old LongProbeEnabled() | 1.702 | 1.702-1.702 |
| cached_flag | one check new LongProbeEnabled() | 0.904 | 0.904-0.904 |
| tls_accessor | no preparation: old 12 accessor calls | 36.553 | 36.553-36.553 |
| tls_accessor | no preparation: new 3 accessor calls | 11.149 | 11.149-11.149 |
| tls_accessor | no preparation: old sequence, inline accessor | 23.825 | 23.825-23.825 |
| tls_accessor | preparation: old 14 accessor calls | 40.513 | 40.513-40.513 |
| tls_accessor | preparation: new 3 accessor calls | 18.750 | 18.750-18.750 |
| tls_accessor | preparation: old sequence, inline accessor | 31.245 | 31.245-31.245 |
| query_scope | N=0 1T old lock+none_of | 47.537 | 47.537-47.537 |
| query_scope | N=0 1T new atomic count | 2.310 | 2.310-2.310 |
| query_scope | N=0 2T old lock+none_of | 92.556 | 92.556-92.556 |
| query_scope | N=0 2T new atomic count | 2.720 | 2.720-2.720 |
| query_scope | N=16 1T old lock+none_of | 74.536 | 74.536-74.536 |
| query_scope | N=16 1T new atomic count | 3.059 | 3.059-3.059 |
| query_scope | N=16 2T old lock+none_of | 144.871 | 144.871-144.871 |
| query_scope | N=16 2T new atomic count | 2.922 | 2.922-2.922 |
| query_scope | N=64 1T old lock+none_of | 239.542 | 239.542-239.542 |
| query_scope | N=64 1T new atomic count | 2.844 | 2.844-2.844 |
| query_scope | N=64 2T old lock+none_of | 462.540 | 462.540-462.540 |
| query_scope | N=64 2T new atomic count | 3.070 | 3.070-3.070 |
| query_scope | N=256 1T old lock+none_of | 961.024 | 961.024-961.024 |
| query_scope | N=256 1T new atomic count | 2.577 | 2.577-2.577 |
| query_scope | N=256 2T old lock+none_of | 1924.586 | 1924.586-1924.586 |
| query_scope | N=256 2T new atomic count | 2.810 | 2.810-2.810 |
