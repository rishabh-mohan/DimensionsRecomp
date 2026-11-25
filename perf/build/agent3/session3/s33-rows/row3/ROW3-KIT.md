# #33 row 3 kit: the user's visible-desktop eye review (M3, session 3)

Folder: `build\agent3\session3\s33-rows\row3\`. One approval: `computer-cli open RUN-ROW3.cmd` runs both arms back to back. Each arm closes itself; then the post step runs.

## 1. What row 3 asks for (`build\agent6\s33-popin\TESTPLAN.md`)

- L43: "All rows below are FUNCTIONAL (hidden desktop) except row 3, and need RUN GO."
- L60, row 3: "user, visible desktop, `onsf` then `offsf` | The user judges pop-in at the first 3D frame, the load transition and the 12.4k shot; no **persistent** wrong textures. | Persistent wrong UI panel / reflection / portrait / minimap = lost resolve source (DESIGN §7): stop, keep the cvar off."
- L69-77 ("Row 3 at the visible desktop"):
  - "Only with the user present and agreeing, after rows 1-2 pass."
  - The command: `-BinDir build\agent2\devoff4b-s33-bin -Seconds 540 -Tag s33-row3-on ... -InputScript harness\routes\attract-long.txt -Cvar "slow_frame_log_ms=1;d3d12_pipeline_creation_no_wait=true"`, "then the same with `-Tag s33-row3-off -Cvar "slow_frame_log_ms=1"`".
  - "Record the user's verdict verbatim in `SESSION3.md`. Never run while the user is playing Minecraft without asking."
- L115, §4 condition 3: "The user's row-3 review gates any recommendation."
- The same row-3 text is in `DESIGN.md` L241.

## 2. Arms (same bin and cvars as TESTPLAN L71-77; same arms as rows 2/5)

| arm | tag | cvars | run-dir reference |
|---|---|---|---|
| OFF | `s33-row3-off` | `slow_frame_log_ms=1` | offsf `build\agent3\runs\20261125-071741-s33-offsf` |
| ON | `s33-row3-on` | `slow_frame_log_ms=1;d3d12_pipeline_creation_no_wait=true` | onsf `build\agent3\runs\20261125-095932-s33-onsf` |

Common settings:
- Bin: `build\agent2\devoff4b-s33-bin`. The exe sha256 DFBE1D43B28861A6… must match its MANIFEST, or the kit refuses.
- Route: `harness\routes\attract-long.txt`, run with `-Seconds 540 -GpuLog`. The `-GpuLog` flag is the same as every row arm in `harness-s33.json`.
- Cold Xenos storage (no `-SeedXenos`), so the drops happen.
- RunsRoot: `...\row3\runs` (full path).
- Time: about 9.5 min per arm, plus a 20 s settle and the post step, so about 20 min in total.

**Order:** the default is OFF then ON (your brief). TESTPLAN L60 says ON then OFF; the word `onfirst` gives that order.

**No resolve-after-drop lines:** this bin has no `d3d12_resolve_after_drop_log`. That cvar is only in the (d) bin, used for offd/ond. So the per-moment number is the slow-frame `dropped draws` field.

## 3. Route and moments: why the times are anchored on the first 3D frame

Source: `moments.txt`, from `row3_moments.py` over offsf, onsf, offd, ond, stop5, onwarm and gthr0.

- The first 3D frame (A3D) moves 16 s against the first frame (FF), and the shift does not depend on the arm:
  - FF+82 in onsf and ond;
  - FF+98..101 in offsf, offd, stop5 (an ON run) and gthr0.
- Measured from A3D, every drop cluster sits at the same offset within ±1.3 s in all five cold runs.
- So **times are A3D-relative**. The watcher finds A3D live in game.log. A3D = the first slow-frame line with `new >= 15` more than 60 s after FF.
- Anchors vs A3D:
  - load transition: +2.2..3.5;
  - the 12.4k shot: +47.0..48.7 (gthr0 +50.1).
- Runs end at about A3D+357..376.
- The attract route has no HUD or minimap. The persistence check therefore covers scene textures, reflections and portraits only.

## 4. Screenshot schedule (`row3-schedule.json`)

The FF columns are the typical values, for orientation only, because A3D drifts ±16 s.

| n | window | kind | A3D+s | what to look for |
|---|---|---|---|---|
| 1 | w01-first3d-load | burst | -0.5..4.5 | first 3D frame (ON drops 38-39 in 4-5 frames) + load transition (23 new) |
| 2 | w02-drop576 | burst | 24.0..27.0 | one pipeline, 576 draws: OFF drops 576 in 1 frame, ON 1152-1728 in 2-3 frames |
| 3 | w03-drop75 | burst | 29.7..32.0 | 75 dropped in 1-2 frames |
| 4 | w04-shot12k | burst | 46.3..49.5 | **the 12.4k shot**: 67-75 new; OFF stalls 0.9 s, ON drops 176-182 |
| 5 | w05-burst57 | burst | 56.7..62.0 | densest ON clusters: 233-275 in 6-8 frames, then 70 in 4-5 frames |
| 6 | w06-drop93 | burst | 93.0..95.0 | 20-24 dropped in 1 frame |
| 7 | w07-drop104 | burst | 103.2..105.4 | OFF 154 in 1 frame, ON 462 in 3 frames |
| 8 | w08-drop145 | burst | 144.3..146.5 | 20 (OFF) / 52 (ON) |
| 9 | w09-drop182 | burst | 181.3..182.6 | ON 56-61 in 7-8 frames |
| 10-16 | s10..s16 | still | 12, 40, 75, 130, 220, 300, 340 | persistence: no wrong texture that stays |

Typical FF+s for A3D: OFF about 98, ON about 82, but stop5 (ON) was 98, so this is not reliable.

**Manual shots (you):**
1. After `ARM <X> FIRST 3D FRAME`, read `row3\live\<arm>.txt`. It lists every window above in wall-clock time.
2. Call `node C:\Users\<user>\.vscode\projects\agy-grid\src\computer-cli.js screenshot` at those times.
3. Copy each shot to `row3\shots\<arm>-<n>.png`, using `off`/`on` and the n from the table. Copy-Item keeps the mtime, and the post step uses the mtime as the shot time.
4. Optionally, `row3\shots\times.csv` (`name,time` with `HH:MM:SS.fff` or a full date) overrides the mtime.

You will mostly miss the drop moments by hand: each cluster lasts at most 0.3 s (1-8 frames), and a manual shot takes about 1 s. Window 1 cannot be hit by hand at all, because A3D shows in the log about 1 s late.

**Automatic burst capture (default):**
- `row3-watch.ps1` captures the **game window client area only** (not the whole desktop) as JPEG q85, up to 15 fps, during the burst windows. Stills are 3 captures 0.3 s apart.
- A 3 s pre-roll ring starts at FF+70, so window 1 includes A3D.
- Files go to `row3\shots\auto\<arm>\` with `index.csv` (file, time, a3d_s, window).
- The game window must stay uncovered and not minimised, because the screen copy takes whatever is on top.
- The word `noauto` turns this off.
- If no A3D line appears by FF+150, the watcher uses an estimate of FF+90 and marks it ESTIMATED.

## 5. Files and use

| file | role |
|---|---|
| `RUN-ROW3.cmd` | The one launcher. Words: `dryrun`, `noauto`, `onfirst` (`allowhidden` is test only). Real run: `RUN-ROW3.cmd`; test: `RUN-ROW3.cmd dryrun`. |
| `row3-run.ps1` | Preconditions, then for each arm: start the watcher, then run-game; stop after an arm whose exit is not 0; then `row3_post.py`. |
| `row3-watch.ps1` | Per arm: finds `runs\*-<tag>` and tails game.log (handles rotation). Prints `ARM <X> FIRST FRAME` / `ARM <X> FIRST 3D FRAME`, writes `live\<arm>.txt` and does the auto captures. `-SelfTestRun <run>` replays an old run. |
| `row3_post.py` | Pairs every shot with the arm's log. Outputs below. |
| `row3_log.py`, `row3_moments.py`, `moments.txt` | Shared log parser; the analysis that picked the windows. |
| `row3-schedule.json` | The windows. |

**Real-run refusals** (exit 3, no game started):
- `perf-notes\WINDOW-HOLD.txt` exists;
- `bench\agent5\day\status\state.txt` says waiting-for-quiet or running;
- legodimensions is already running;
- an Agent 8 runner is active;
- the process is not on the interactive desktop (`Default`);
- the exe is not in the MANIFEST.

**Exit codes:** 0 = both arms exited 0; 1 = an arm failed or fewer than 2 arms ran; 2 = a file is missing.

**Your hidden shell can follow the run** through:
- `row3\logs\row3-run-*.txt`
- `row3\logs\watch-<ARM>-*.txt`
- `row3\live\<arm>.txt`

**Post outputs** (`row3\post\`):
- `captions.txt`: one caption per shot, e.g. "dropped draws at this moment: k". k = the dropped draws of the last frame at or before the shot. The caption also gives the max over the preceding 0.1 s and the ±0.5 s totals.
- `shots.csv`: the same data, machine-readable.
- `sbs-<window>.jpg` / `sbs-manual-<n>.jpg`: OFF and ON side by side, for Discord.
- `pairs.txt`.

To redo the post step by hand: `python -B row3_post.py --row3 <row3> --arm off=<run> --arm on=<run>`.

## 6. Before and after

- The user must be present and agree, and must not be playing Minecraft (L69, L77).
- Rows 1-2 have passed.
- Check `state.txt` and WINDOW-HOLD (the kit checks both too).
- Record the user's verdict **verbatim** in `SESSION3.md`.
- Fail rule (L60): a persistent wrong UI panel, reflection or portrait = stop, keep the cvar off.
- An s4b check of the row-3 runs is optional. They are cold attract runs like offsf/onsf, so they can be read like row 2.
- Untested: the live path, i.e. the watcher picking up a run dir that appears after it starts, and the screen copy of a real window. The DryRun covers the command lines, run-game -DryRun, a replay of the log parser and schedule, and the post pairing.
