# NOTE: "white/rainbow portal" 04:28-04:32:40, run 20261126-041246-gpman-native (M16, read-only, Idle/background I/O)

Run: `build\agent3\gameplay\runs\20261126-041246-gpman-native`, native4bp (MANIFEST C5181520…A690), manual session.
Trace on: `build\agent3\gameplay\trace-native-20261126-041241\events.tsv` (370.6 MB). Only the window was read, via a
seek to 04:24 / 04:28:30, in background I/O mode.

Sources:
- frames.csv: LEGO_NATIVE_FRAME_METRICS, `draw_calls` = recorded draws per present. Its time axis is launch + 5.0 s
  first frame + cumulative interval_ms; the last frame lands at 04:32:48, which matches the log close at 04:32:47.
- game.log.
- events.tsv, timed from trace-start unix_ms 1795687971010.
- Scripts and output in my scratch dir: `portal0428.py/.txt`, `portal_trace.py/.txt`, `portal_trace2.py/.txt`.

## 1. Recorded draws per frame, 30 s bins (frames.csv)

| from | fps | draws p10/p50/p90 | min..max | distinct | PSO creations (ms) |
|---|---|---|---|---|---|
| 04:24:00-04:27:30 (cutscenes) | 26-47 | median 447, wide (93..2196) | | 76-245/bin | 0-184/bin |
| 04:27:30 | 46.6 | 197/612/834 | 3..850 | 71 | 42 (12.4) |
| 04:28:00 | 47.9 | 165/225/403 | 4..532 | 84 | 99 (50.4): scene load |
| 04:28:30-04:29:30 | 42-46 | 390/395/404 | 380..404 | 16-17 | 0 |
| 04:30:00 | 48.5 | 390/403/419 | 382..420 | 30 | 1 (0.3) |
| 04:30:30-04:31:30 | 45-47 | 409/414/420 | 401..428 | 12-17 | 0 |
| 04:32:00 | 49.3 | 410/419/448 | 403..460 | 28 | 0 |
| 04:32:30 | 30.3 (close) | 440/447/459 | 433..460 | 16 | 0 |

- There is no zero-draw frame after 04:28:30.
- The count changes every ~3 frames (median run of identical counts 3, longest 50).
- It drifts upward in steps: ~395 → ~414 → ~447.

## 2. game.log

- 04:28:00-04:28:39: a scene load.
  - 83 shader adoptions and 114 texture adoptions.
  - 2 placement-buffer relocations.
  - Pipeline cache saves: +11 and +46.
- After 04:28:39: no adoptions. One pipeline was saved at 04:30:18. **No PSO storm.**
- Only Toypad lines continue:
  - 356 `lit` lines; `FF 00 00` = red.
  - 9 LOAD / 9 REMOVE listener events (the figure swaps).
- Shader warnings: the last ones are at 04:17:31 (VS 0xAC44BC64: 8 placement + 16 unrecognized). After that the
  shader-warning log budget is exhausted, and **game.log goes silent about every later miss**.
- The trace's `shader_miss_cache_insert` rows are capped as well: the last one is at 04:25:22.

## 3. Native trace in the window: every frame drops exactly 3 draws

- 04:28:30-04:32:41: 11,603 trace frames. **All 11,603 have missing draws.**
  - `draw_missing_pixel_shader` = 3 per frame in every frame.
  - `draw_missing_vertex_shader` = 3 per frame (6 in 52 frames).
  - `unrecognized_shader` ≈ 16 per frame.
- Guests, steady from 04:28:00 to the end:

| stage | guest | per frame | vs B48DA281 (024219 story list) |
|---|---|---|---|
| VS | 0xA7FA6E00 (2818207232), paired with PS 0xA7FA6C00 | 2 draws | **NEW** |
| VS | 0xA7FA8990 (2818214288), paired with PS 0xA7FA8750 | 1 draw | **NEW** |
| PS | 0xA8302100 (2821726464) | 1 draw | **NEW** |
| PS | 0xAC53D0AC (2891174060) | 1 draw | known (4,035 frames in 024219) |
| PS | 0xAC49B8F8 (2890512632) | 1 draw | known (the 2nd placement shader, 8,049 frames) |

- So ~3 of ~400 draws are dropped per frame (< 1% by count). The trace carries no primitive or coverage data, so it
  can't say whether one of them is a full-screen pass, such as the portal effect, a composite or a fade.
- Earlier story bins (04:24-04:28) also drop draws: VS 0xAC48E494, 0xA7B65490, PS 0xA81E2BD0, 0xAB88BE30, 0xAC4945A8,
  0xAC5AB248/0xAC5AB10C.

## 4. summary.txt "median draws per 10 s: 0"

The counter comes from `perf.csv` draw_calls, which is **dead on native** (0/0/0 over the whole run; same in the S5
native timing runs). The live counter is frames.csv `draw_calls` (run median 245).

## Verdict

- **The 3D scene was being rendered, not just the HUD.** From 04:28:30 to 04:32:40 there were ~390-450 recorded draws
  per frame at 42-49 fps, with small, steady change (animation) and no PSO creations. It is a fully loaded steady scene
  (loaded 04:28:00-04:28:39), not a stall.
- **But every frame drops exactly 3 draws whose shaders are missing:** VS 0xA7FA6E00 ×2, VS 0xA7FA8990, and PS
  0xA8302100 / 0xAC53D0AC / 0xAC49B8F8. Three of those are NEW versus B48DA281. game.log can't show this: its warning
  budget ran out at 04:17:31.
- Guest logic was alive: it drives the Toypad red blink, the figure LOAD/REMOVE and the HUD head icon. It is consistent
  with a game-side waiting state, for example a portal/figure prompt.
- **The white/static look may come from the 3 dropped draws**, if one is the portal/full-screen pass. That is unproven.
  To settle it: `LEGO_GPU_SNAPSHOT_DIR` at this point, or the same point on the Xenos renderer as a reference image.
- Pack impact: add VS 0xA7FA6E00/PS 0xA7FA6C00, VS 0xA7FA8990/PS 0xA7FA8750 and PS 0xA8302100 to the story-dump target
  list (PLAN-story-dump.md §5). The dump would capture them, since they are well under the 256 cap.
