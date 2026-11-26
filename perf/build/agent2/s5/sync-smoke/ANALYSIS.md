# S5 sync-pipeline smoke: analysis (M2)

Kit: `s5/RUN-SYNC-SMOKE.cmd`, started by the Overseer in the waiter at 17:49:29. Bin: devs5sync-bin (MANIFEST 2235E6DE). Interactive desktop. Both arms exit 0. Post report: `post/sync-smoke-post-20261125-174930.txt`, RESULT PASS.
- **off:** `runs/20261125-174932-s5sync-off`, plain default.
- **on:** `runs/20261125-175402-s5sync-on`, `d3d12_log_sync_pipeline_creation=true;slow_frame_log_ms=1`.

## Gates
| | off | on |
|---|---|---|
| exit / close | 0x0 / wm_close | 0x0 / wm_close |
| WER / crash events / dumps | none / 0 / 0 | none / 0 / 0 |
| route START/A/A, steps to the close | PASS | (same route; not gated) |
| first 3D (draws >= 600) | perf row 5423, 90.7 s | perf row 5883, 98.4 s |
| check-defaults xenos | PASS | PASS |
| D3: Initialize line | 0 | 1 ("async_shader_compilation true, 9 creation threads") |
| D3: 'sync pipeline #' lines | 0 | 45 (0 suppressed) |

There is no functional difference between the arms. The on arm reaches first 3D about 8 s later and has a higher median frame time after 3D (33.2 vs 28.1 ms). The cause is the log volume: 9429 vs 244 game.log lines. D2 applies: the on arm is not a timing result.

## Attribution (on arm; counts and joins only)
- **All 45 sync creations are "no pixel shader".**
  - Every one is on the host-RT path and color mask 0, i.e. depth-only (z/shadow-type) draws.
  - Only 1 has a vs memexport.
  - 45 distinct pipelines, from 27 distinct vertex shaders.
  - Host prim: 4 = 34, 1 = 6, 8 = 5.
- **Time:** the logged total is 879.9 ms. Per create: median 8.4 ms, p90 56.9 ms, max 135.1 ms.
- **Every sync line joins a slow frame with pipeline create > 0** (0 unjoined). The frame's Nx equals the number of joined sync lines in every frame with create >= 100 ms.
- **The s33 stall is reproduced:**
  - on arm, frame #7601: 945.7 ms, `pipeline create 458.5 (8x), new 67`, joined to 8 sync lines totalling 458.6 ms, all no-PS (#15-#22, the largest 135.1 ms).
  - s33 frame #7366 had the identical signature: `322.0 (8x), new 67`, dropped draws 141 vs 137 here.
  - The 322 ms of 8 sync creates is therefore 8 no-pixel-shader (depth-only) pipelines that skip the async path. The predicted count (8) and reason both hold.
- **Other frames with sync creates:**
  - #7760: 118 ms, 10x
  - #7720: 86 ms, 2x
  - #7723: 60 ms, 3x
  - #8970: 42 ms, 1x
  - #1736: 37 ms, 1x
  - #6239: 29 ms, 4x
  - #5884: 18 ms, 4x
  - the rest are under 25 ms.

## Off arm: the same spike exists without logging
- perf.csv row 7545: 940.1 ms, pipeline_cache_misses 67. This is the same scene point as on row 7600 (945.7 ms, misses 67, 12392/12395 draws).
- The neighbours match as well (rows 7546-7550 vs 7601-7605).
- So the stall is a property of the bin, not of the logging.
- It is at about 143 s after the first perf row, about 17:51:57-17:52:00 wall clock, so it is **outside** M16's I/O window (17:51:00-17:51:40).

## Possibly I/O-disturbed (M16 hashed ~760 MB at 17:51:00-17:51:40; do not attribute these)
- The off arm's perf rows at about 86-126 s fall in that window:
  - row 5423 (first 3D, 259 ms);
  - rows 5778-5780 (1229.6 / 323.0 / 157.4 ms);
  - row 7210 (155.8 ms).
- They have counterparts in the on arm at the same scene points (rows 5883: 333 ms, 6237: 918 ms, 7295: 172 ms), so they look like scene/load features. Still, their off-arm sizes are not clean.

## On-arm spikes that are not pipeline creation
These frames have `pipeline create 0.0 (0x)` and large `host-gpu wait` counts:
- #6553: 369 ms, 685x
- #6557: 1438.6 ms, 2704x / 308.7 ms
- #6603: 592 ms
- #6609: 740 ms
- #6615: 926 ms
- #7620: 1281.8 ms, 1632x
- #7627: 561 ms

They also have memexport syncs. Most have no off-arm counterpart of that size; #7620 matches off row 7567 (972.5 ms). They are host-GPU-wait / memexport stalls, possibly made worse by the logging. They are out of scope for the sync-pipeline log.
