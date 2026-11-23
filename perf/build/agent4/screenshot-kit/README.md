# Screenshot check kit: native4 vs the standard GPU path (the "before" half of #1)

Agent 4, task #29, 2026-11-23. One page for you and Agent 1, about 25 minutes. It uses only bins that exist today; nothing is built.

**Why.** Native drops every draw whose shader is missing from its AOT index. The #1 pack adds 4 such shaders, but its bin (native4bp) isn't built, so the pack's yes/no can't happen today. This kit records the "before": five moments on the standard GPU path and on today's native. The MISSING areas you find become the "look here" list for the pack check after the break. That check repeats only the native run, with the pack bin and the same steps.

## 0. Before you start (Agent 1)

- `perf-notes/WINDOW-HOLD.txt` doesn't exist, Agent 3's queue is paused (it may launch games until 11:40 and closes them by 12:00), and `Get-Process legodimensions -ErrorAction SilentlyContinue` prints nothing.
- **You** start the runs, in your own PowerShell window, in the repo root. An agent's shell sits on a hidden desktop, so a game it starts can't be seen.
- Test the screenshot key once: press **Win+PrtScn**. The screen dims briefly, and a new PNG appears in Pictures\Screenshots. If nothing happens, try Fn+Win+PrtScn. If the PNGs land in another folder, give that folder to collect-shots with `-ShotDir`. The test shot is older than the runs, so collect-shots ignores it.
- The game window opens on your desktop. Keep it fully visible: move your PowerShell window aside, never the game. Don't click into the game or press keys in it (F4 opens a settings overlay). The pad is virtual; a real pad is ignored.

## 1. Bins, settings and commands

| Run | Bin | Renderer | Extra flag |
|---|---|---|---|
| A, reference | `build/agent2/devoff4-bin` | standard GPU path | none |
| B, native | `build/agent2/native4-bin` | native, fingerprint `5e3ff55de10f4f64` | `-Cvar 'native_settings_frontend=false'` (first-boot crash workaround) |

- Both bins come from the same S4a source snapshot; only the renderer differs.
- Settings are the harness defaults (`harness/legodimensions.toml`): windowed, 60 fps limit, FSR quality, resolution scale 1, audio muted, a fresh user folder per run, `--pause_when_unfocused=false`. Set no `LEGO_*` variables.
- Input: Agent 3's virtual pad plays `harness/routes/attract-long.txt`. It presses START, A, A about 51, 60 and 69 s after the first frame and then nothing, so the game idles into its 3D attract. Without input the attract never starts.

Run these one at a time. Each run closes itself 360 s after launch (about 6.5 min in all). Keep `"$PWD\..."` as written: `-RunsRoot` must be a full path, or the game can't find its log and pad files.

```
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\agent2\devoff4-bin -Seconds 360 -Tag sc-ref -RunsRoot "$PWD\build\agent4\screenshot-kit\runs" -InputScript harness\routes\attract-long.txt
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\agent2\native4-bin -Seconds 360 -Tag sc-native -RunsRoot "$PWD\build\agent4\screenshot-kit\runs" -InputScript harness\routes\attract-long.txt -Cvar 'native_settings_frontend=false'
```

- Optional check before the hour; no game starts, so Agent 1 can run it. Take command A, change `-Tag sc-ref` to `-Tag sc-dry` and add `-DryRun`. The `command` and `env` lines it prints must show full paths, with a drive letter, for `--log_file`, `--perf_log_csv` and `AGENT3_VPAD`.
- The console's `mode` line reads `FUNCTIONAL (interactive desktop)`. After the run, `$LASTEXITCODE` is 0; 1 means a crash, or the game quit early with an error code.
- `REFUSED: already running` means a game is still open: wait until it has closed, then repeat the command. If you see any other `REFUSED` line or exit code 2, stop and tell Agent 1.

## 2. The five moments, and what to capture

Press **Win+PrtScn** once at each moment: exactly five shots per run, in this order. Go by what is on screen, not by the clock; the times are counted from the first frame.

| Shot | Moment | Native drops here (traced native4 run) |
|---|---|---|
| S1 | The title screen, ~10 s after it appears. It appears ~33 s in and stays until the pad's first A (~60 s); START at ~51 s changes nothing. | 8 draws per frame (pack shaders: 7 for sure, 1 probably) |
| S2 | The front-end menu, 20-40 s after the title goes away. The pad's second A (~69 s) changes the menu once more; then the pad stops. | 2 draws per frame (pack shaders) |
| S3 | The 3D attract, ~10 s after its first 3D picture. About a minute after the pad's last press the menu fades; after a ~10 s load the 3D starts, ~135-150 s in. | ~43 of ~59 draws per frame |
| S4 | ~2 s after the first cut to a much busier shot, ~30-40 s after the attract's first 3D picture. | ~45 draws per frame, more later |
| S5 | ~2 s after the next camera cut, about 5 s later. | ~45 draws per frame, more later |

- Run A may show a black window for up to ~60 s at start-up while its shaders compile; native shows a picture within ~15 s. Short stalls on first use are normal on both.
- After S5, let the run close itself; don't close the window. A missed or extra shot is fine: tell Agent 1 which one. compare.html then pairs the shots by order, so the pairs after it are shifted; re-pair them by the ff seconds in the file names.

## 3. Collect, compare, pass

```
powershell -NoProfile -ExecutionPolicy Bypass -File build\agent4\screenshot-kit\collect-shots.ps1
```

It copies each run's PNGs (matched by time) into `build/agent4/screenshot-kit/shots/` as `S1-ref-ff043.png`, `S1-native-ff044.png` and so on (ff = seconds after the first frame). It checks both runs: no crash or early exit, your desktop, and a connected pad. Then it writes `shots/compare.html`. Open it: the pairs are side by side, and "flip view" shows one large image that switches between reference and native on each click.

Mark each pair:
- **SAME:** no difference beyond the ignore list.
- **MISSING:** something in the reference is absent on native. Note where. The pack's shaders probably draw grey or washed-out 3D shapes with cut-out edges; nobody has seen them yet.
- **OTHER:** anything else: wrong colour or brightness, texture, geometry, flicker, or a black or frozen picture.
- **Ignore:** animation phase and camera position (the moments never match exactly), FSR sharpness, window position, the start-up black window and first-use stalls.

**Pass today:** collect-shots ends with `COMPLETE` (both runs OK, five shots each), and every pair is SAME or MISSING. MISSING is expected and is the result: it shows where the pack must restore something. An OTHER is a native rendering finding for Agent 1; it blocks nothing today. If S1 and S2 show no MISSING at all, the pack's draws aren't visible in these scenes. The pack check then needs another scene, or you decide to land the pack on the agent checks alone.

| Shot | SAME / MISSING / OTHER | Where / note |
|---|---|---|
| S1 title | | |
| S2 menu | | |
| S3 attract | | |
| S4 busy shot | | |
| S5 next shot | | |

> **Local only.** `shots/`, `runs/` and the originals in Pictures\Screenshots show game assets. Never commit or export them. If Pictures syncs to OneDrive, delete the originals there afterwards.

## 4. Not in this kit

- **The pack yes/no.** After the break, Agent 2 builds a pack bin and the agents run their checks (`build/agent4/r2t6/VISUAL-CHECK.md` sections 2-3). Then you repeat only command B with the pack bin and compare against these reference shots. After your yes, the pack bin becomes the pinned native line (`build/agent4/repin/REPIN.md` section 4.2).
- **The attract's drops are an open question.** They come from 46 more vertex-shader objects (and 3 pixel-shader objects), first bound from the attract's load on (117.7-188 s in the traced run). The only shader dump so far (`0509-sd-r1`, no input) never reached the attract, so nobody knows yet whether the pack covers them. One dump run with this route comes first after the break.
- **Not covered:** pop-in (#33) needs its option built, and these runs are functional only, so no timing. native4b-bin (the re-pin bin) has the same shader set, so it should look like native4.

Sources: `harness/run-game.ps1`, `harness/routes/attract-long.txt`, `perf-notes/agent3-run-harness.md` sections 3 and 7.4, and `build/agent4/r2t6/VISUAL-CHECK.md`. Route and scene times come from 34 no-input and 41 route runs. The drops per frame come from `native4-drops-r6off.txt` here, which is built from the trace `build/agent3/s4a/trace/r6off-t/events.tsv` (native4, b-gate route). Native's `draw_calls` counts the dropped draws too (draw.cpp 2499 and 2712-2725).
