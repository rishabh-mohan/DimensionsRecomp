# Agent 3: game data and run/measure harness (task #2)

> **RESUME (11-23 ~07:10, task #23: wrap-up before the pause, DONE; read `build/agent3/HANDOFF.md` first)**
> - Everything is stopped: no game, queue, postcheck, hostload or sidecar process is running, and `build/agent3/s4b/STOP` exists. No builds and no timed runs were made.
> - f10 (finding 10 on a quiet host): 0 of 4 quiet runs hung, against 4 of 6 under the -j8 build (p = 0.07). The stall is host-side and comes in episodes. Write-up: `build/agent3/f10/RESULTS.md`.
> - Native4b re-pin rows: rpb0 PASS, rpm4 PASS (REPIN section 3b), section 9.2.5.
> - Open items and how to restart the queue: `build/agent3/HANDOFF.md`.
>
> **Older RESUME (17:07, 2026-11-22, board run 2, task #29: the S4b functional queue, IN PROGRESS at the time; section 9)**
> - Agent 7's `build/agent7/s4b-queue/QUEUE.md` (22 agent rows). Tools in `build/agent3/s4b/` (written 17:00-17:06, before 'go', not yet run): `s4b-queue.ps1` (HOLD/PAUSE aware), `holdwatch.ps1` (stops my game if `perf-notes/WINDOW-HOLD.txt` appears), `s4b_check.py` (imports `../s4a/s4a_check.py`), `postcheck.ps1`, `queue.jsonl` (provisional bin names).
> - Window rule: no run_command before Agent 1's 'go'; while `perf-notes/WINDOW-HOLD.txt` exists, no tool calls at all. Rows 7, 20, 23 wait for decision 1 (Toy Pad tags).
> - **WHERE I AM (17:08, agy-grid restart announced by Agent 1):** prep done, nothing run. Not received yet: Agent 1's 'go', Agent 2's S4b bins report, Agent 7's `<N>`, Agent 12's P2 check script. Next, after 'go' (HOLD check before every command): (1) PowerShell parse-check of the 3 scripts and `python -m py_compile s4b_check.py`; dry-test `s4b_check.py --row s4b01 --cand build\agent3\runs\20261122-142514-s4a-r7-fixi-devoff4 --base <R1> --out-dir build\agent3\s4b\tmp-checks` and the joined-log path with RA; (2) Select-String for the C1 verify-mismatch (K) text in `build/agent12/s4-c1v2/new/sdk/src/system/xmemory.cpp` (then set `K_DEFAULT`), the `deferred_counters`/`d3d12_submit_split` formats in Agent 7's `s4-r1r2.diff`, and the debug-layer path in `src/ui/d3d12/d3d12_provider.cpp`; `Test-Path C:\Windows\System32\d3d12SDKLayers.dll` (-> `ready-dbg`); (3) when the bins exist: MANIFEST, new cvar strings in the DLLs/exe, "memexport full-buffer" per bin (decides whether P2's counter comes from row 8 or needs an `s4b08c` row on the CTR bin), fix the bin names in `queue.jsonl`, create the `ready-*` markers, start `s4b-queue.ps1 -LastLaunch/-GamesClosed` and `postcheck.ps1` as background tasks, start 1-2 checker subagents (read/check only); (4) tell Agent 1 about holdwatch's stop-on-HOLD behavior.
>
> **Older RESUME (14:50, 2026-11-22, board run 2, task #5: S4a functional checks, DONE; `@@done 5` sent ~14:52)**
> - Every S4a run is in section 8: tools 8.1, references 8.2, results 8.3, what's left 8.4. Every run exited 0 with no dumps. The one failure was r5 attempt 1, a harness fault (native stderr under EAP Stop), fixed at 14:07.
> - Verdicts:
>   - r1, r3, r4, r5, r7, the #32 runs and r6 all PASS; r6 PASS is Agent 4's verdict, and the checker's C3 is a heap relocation.
>   - r2 and a12at PASS (functional); Agent 12 has them.
>   - #32 fix active: U4/F4 = 5.5×. No hang in 5 of 5 warm boots.
> - **Quiet until Agent 1 says W4b is done:** no launches, no harness/toml/route edits, nothing in W4b's inputs.
> - After W4b: Agent 7's S4b queue runs only on Agent 1's GO (8.4 item 4). Bins come from Agent 2's map in `perf-notes/agent2-baseline.md` S5.
> - Tools are in `build/agent3/s4a/`: `s4a-queue.ps1` (runner, EAP Continue around run-game), `attach.ps1` (sys.csv + threads), `s4a_check.py`, `postcheck.ps1`, `slowstate.ps1`.
>
> **Older RESUME (05:50, 2026-11-22, session 3)**
> - **Task #16 (attract-scene benchmark prep for a later user window, not window 4): done; plan sent to Agents 8 and 1 at ~05:50. Section 7.4.**
>   - `harness/routes/attract-long.txt` and `harness/attract-report.py` (window H0 + 6.5 s for 11 s; a frame of 250 ms or more, or the heavy segment, excludes a run; re-tested 04:38).
>   - The attract pair ran at 05:12 (devoff3) and 05:20 (devoffB), see "attract-long results" in 7.4. The attract started at perf 126-141 s whatever the presses did, it runs once with no loop, and the shot order repeats. All three attract windows (the pair and the warm run) were excluded because the machine was saturated (Defender, NVIDIA FrameView's PresentMon, other agents' searches).
>   - The warm-storage check run (05:29, devoff3 + `-SeedXenos`): the storage loaded 214 pipelines and the pipeline misses fell from 264 to 56 (pm 0 in the window), but stalls with pm 0 still excluded the window on the saturated machine (7.4 item 6).
>   - `route-report.ps1`: native draw counts from `frames.csv`/`native-frames.csv` (tested 04:05-04:11, then on the real nativeB pair); since 05:16 its watchdog check also matches `STUCK-LOCK`, `Minidump written` and `[FATAL]`.
>   - The nativeB route pair (Agent 8's runs 04:59/05:03 with my harness and route): my route-report results went to Agent 10 at 05:20; Agent 10's verdict is PASS.
>   - Open: Agent 8 offered a re-run on a quieter machine at ~06:35-06:52 if Agent 1 agrees (my proposal: devoff3 cold, then devoff3 warm, `attract-long.txt`, `-Seconds 540`). Next session: native anchors for attract-report, the runner `-InputScript` port (Agent 8's file), and a quiet-machine check before any timed run (7.4 item 5).
> - **Done (task #2, `@@done 2` sent ~03:30; Agent 1 closed it):**
>   - section 6.2: both `baseline-bin` runs (`runs/20261122-021532-base` with `-GpuLog`; `runs/20261122-022642-base-prof`, which overlapped Agent 2's build: 0.9 rounds/s);
>   - the virtual XInput pad and input scripts (section 7): `harness/vpad/*`, `run-game.ps1 -InputScript`, `harness/route-report.ps1`, the routes `harness/routes/b-gate-menus.txt`, `b-gate-menus-long.txt` and `selftest-input.txt`, the fake exe's `--input_backend=xinput` and the self-test `input` case;
>   - the dry run on `devoff2-bin` (section 7.1), the B-gate pair and the tie-break pair (section 7.2):
>     - all five runs are clean, and Agent 10 has the data for the verdict;
>     - the one divergence (devoffB left the front-end screen on its own) also happens on devoff2, so it is run-to-run variation;
>     - the long route reaches a heavy 3D attract scene with no figures (section 7.3);
>   - self-test: 23 passed, 0 failed (03:16, section 6.1); since 03:20 `build-vpad.ps1` skips up-to-date builds, and the self-test builds its own pad DLL copy.
> - Follow-ups are in section 7.3.
> - **Rules:** game runs only through Agent 8's slot, one at a time (`harness/guard.ps1` refuses otherwise); no builds or game runs from 08:30; at most 2 threads; never put `xinput1_4.dll` in a staged bin dir; questions go to Agent 1 (the user is asleep until ~10:00).
> - **Background:** Agent 8 owns all boots and timing runs; `run-game.ps1` is the thin functional runner and profile capture (agreed with Agent 1, ~21:20). Since my 22:48 overlap with the user's matrix runs (session 2), `selftest.ps1` and `run-game.ps1` refuse while a game or an Agent 8 runner is active.

## 1. Harness: `harness/run-game.ps1`

```powershell
# functional run of the baseline: 180 s (the first frame came 13-35 s after launch in session 3); stats from 20 s after the first frame
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\baseline-bin -Seconds 180 -StatsWarmup 20 -Tag base
# profile 30 s of the title/attract scene, starting 90 s after launch (PROFILE ONLY, NOT FOR TIMING)
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\baseline-bin -Profile -Warmup 90 -ProfileSeconds 30 -Tag base-prof
# add NVIDIA GPU state once a second (NVML -> gpu.csv; summary.txt gets a 'gpu' line); works with any run
...\run-game.ps1 -BinDir build\baseline-bin -Seconds 180 -StatsWarmup 20 -GpuLog -Tag base
# cvars into the run's toml, extra flags (a '--' is added), env vars; several items separated by ';'
...\run-game.ps1 -BinDir build\agent2\devoff1-bin -Cvar 'vsync=false;resolution_scale=1' -Arg 'input_backend=xinput' -Env 'LEGO_NATIVE_FPS_LIMIT=0'
# medians over runs (the measuring rule: >= 5 runs, same machine, note what else ran)
python harness\runstats.py --aggregate build\agent3\runs\*-base
# set up a run dir (mirror, toml, command line, env) without launching; needs no game slot
...\run-game.ps1 -BinDir build\baseline-bin -DryRun -Tag dry
# drive the game with the virtual XInput pad (section 7; FUNCTIONAL ONLY), then the step-by-step report
...\run-game.ps1 -BinDir build\agent2\devoff2-bin -Seconds 420 -Tag bgate-dry -InputScript harness\routes\b-gate-menus.txt
powershell -NoProfile -ExecutionPolicy Bypass -File harness\route-report.ps1 -RunDir build\agent3\runs\<run>
# warm Xenos shader storage: copy a saved storage into <run>\user before the launch (section 7.4 item 6; FUNCTIONAL ONLY)
...\run-game.ps1 -BinDir build\agent2\devoff3-bin -Seconds 360 -Tag attract-devoff3-warm -InputScript harness\routes\attract-long.txt -SeedXenos build\agent3\seed\devoff2-214
```

What one run does (run dir `build/agent3/runs/<yyyyMMdd-HHmmss>-<tag>`):
1. Refuses to start if a `legodimensions` process is already running (one game at a time), or if one of Agent 8's runners is active (`run-matrix.ps1`, `run-timing.ps1`, `first-boot.ps1`, `RUN-TIMING-MATRIX.cmd`; found by command line, `harness/guard.ps1`). A runner leaves gaps with no game between its runs. `-AllowConcurrent` overrides both checks. `selftest.ps1` makes the same checks (`-Force` overrides).
2. Mirrors `-BinDir` with hard links (no disk cost). It never copies `native-environment.ini` (that file switches on `native_direct_startup.h`, which redirects logs) or a stale toml. It writes `harness/legodimensions.toml` next to the exe with `user_data_root=<run>\user` (fresh per run, or `-UserDir`) and the `-Cvar` overrides. The game reads the toml from the exe dir and writes `profile-*.bin` there, so both stay in the run dir.
3. Starts the exe with CWD = run dir and `--log_file=<run>\game.log --log_flush_interval=1 --perf_log_csv=<run>\perf.csv --native_settings_load=false --discord_rpc=false --audio_mute=true --pause_when_unfocused=false` (Agent 8's first-boot set, plus a 1 s log flush) and `-Arg`. Inherited `LEGO_*`/`PLUME_*` variables are removed; `LEGO_NATIVE_FRAME_METRICS=<run>\frames.csv` is set (only native builds write it); then `-Env`.
4. Samples the process every second into `samples.csv` (CPU s, working set, private MB, threads, handles, sizes of game.log/perf.csv/frames.csv, window count). Every 2 s it looks for a new `WerFault.exe` (cheap `Get-Process`); it checks the command line for `-p <pid>` over WMI once per new WerFault pid, because a WMI query takes up to 6 s when the box is busy. With `-GpuLog` the same pass reads the NVIDIA GPU through NVML (`harness/nvml.cs`: pstate, graphics and memory clocks, temperature, power, utilization, clock-limit reasons) into `gpu.csv`, about 0.1 ms per sample with no extra process. (`nvidia-smi -f <file>` buffers the file until nvidia-smi exits, so a logger that gets killed leaves an empty file; tested 23:27.)
5. `-Profile`: sets `LEGO_SAMPLE_PROFILE=1` and `LEGO_SAMPLE_PROFILE_TRIGGER=<run>\profile.trigger`, creates the trigger at `-Warmup` s after launch and deletes it `-ProfileSeconds` later, waits until `profile-*.bin` has stopped growing (90 s limit), writes `profile-meta.json` (`profile_trigger_start/_end` in epoch seconds, wall clock, QPC) and runs `python DimensionsRecomp\tools\native-cpu\analyze_profile.py <bin> <run>\legodimensions.map --meta profile-meta.json --json -o profile.json` (and a text report, `profile.txt`). It flags `rounds_per_s < 250`. Run mode: `PROFILE ONLY, NOT FOR TIMING`.
6. At `-Seconds`, posts WM_CLOSE to the game's windows from the same script (the hidden desktop allows this only from the launching command), waits `-CloseTimeoutSec` (default 60; the real game can take ~33 s to disappear), then kills it.
7. Records the exit code, Application-log events 1000/1001/1002/1026 for the exe, `*.dmp` in the run dir and `%LOCALAPPDATA%\CrashDumps`, whether the toml changed (`toml_rewritten`), and the desktop name. It writes `run.json` and runs `runstats.py --write` (`summary.txt`, `summary.json`).

With `-InputScript <file>` (section 7) the run also copies the virtual pad DLL (`-VPadDll`, default `build\agent3\vpad\xinput1_4.dll`) into the run dir, never into BinDir (refused if BinDir has its own), sets `AGENT3_VPAD=<run>\vpad-state.bin`, adds `--input_backend=xinput`, and runs the script's steps from the launch on. A `stop` step ends the run early, with WM_CLOSE as at `-Seconds`. `-DryRun -InputScript` only checks the script.

With `-SeedXenos <dir>` the run copies the Xenos shader storage files in that dir (`*.xsh`, `*.xpso`) into `<user>\cache\shaders\shareable` before the launch. They are plain copies, never hard links, because the game appends to these files, so a run never writes into the seed. The run is refused if a copy would overwrite a file (for example in a reused `-UserDir`). `run.json` `seed_xenos` has each file's size and sha256 before the launch, its size after the run (an `.xpso` grows 72 bytes per new pipeline after a 12-byte header), and the game.log lines with 'storage'.

Exit code: 0 = ran and closed; 1 = crash evidence or an early non-zero exit; 2 = bad arguments or refused.

> [!WARNING]
> Agent-launched runs sit on a hidden desktop (`run.json` `desktop` is `exebox-*`, mode `FUNCTIONAL ONLY (hidden desktop ...), NOT FOR TIMING`). The game is never presented there, so its frame times are not timing results. Timing runs are started by the user on the real desktop (`bench\agent8\RUN-TIMING-MATRIX.cmd`, Agent 8). Never take timing from a `-Profile` run.

| file in the run dir | content |
|---|---|
| `run.json` | command line, env, cvars, exit code, close method, crash events, dumps, process peaks, `profile`, `input_script` and `seed_xenos` blocks |
| `game.log` | the game log (flushed every 1 s) |
| `perf.csv` | per-swap counters (OFF and native builds) |
| `frames.csv` | per-present native frame metrics (native builds only) |
| `samples.csv` | 1 s process samples |
| `gpu.csv` | with `-GpuLog`: NVML GPU state, one row per sample (`t_s` on the samples.csv clock, from launch) |
| `summary.txt` / `summary.json` | runstats: boot markers (TU patch, DXGI adapter, shader storage, first frame from samples.csv), log levels, frame stats, scenes, GPU summary from the first frame + warm-up |
| `profile-*.bin`, `profile-meta.json`, `profile.json`, `profile.txt` | with `-Profile` |
| `input.csv` | with `-InputScript`: one row per step (seconds since launch, result, the pad's call counters, perf.csv size `perf_bytes`, game.log position) |
| `xinput1_4.dll`, `vpad-state.bin` | with `-InputScript`: the run's copy of the virtual pad and its 4 KiB state file |
| `route-report.txt` | written by `harness/route-report.ps1` |
| `user\cache\shaders\shareable\5752084B.xsh`, `5752084B.rtv.d3d12.xpso` | the game's Xenos shader storage: empty at the start of every run (so first-use pipeline stalls come back each time) unless `-SeedXenos` |

## 2. Perf signals

| build | signal | how to get it | notes |
|---|---|---|---|
| OFF (emulated Xenos: `baseline-bin`, `devoff1-bin`) | `perf.csv` | `--perf_log_csv=<path>` | 17 integer columns (`frame_time_us,fps,draw_calls,command_buffer_stalls,...,pipeline_cache_misses`), one row per guest swap; `frame_time_us` is the wall time between swaps. Starts at the first guest frame; flushed every 60 rows, so the file can lag up to 60 frames and the last rows can be lost on a kill. |
| native ON | `frames.csv` | `LEGO_NATIVE_FRAME_METRICS=<path>` | `interval_ms` (wall time between presents) plus draw calls, PSO creations, scene/output size, focus, vsync, fps cap; flushed every 120 rows. Agent 7's patch adds perf.csv rows to the native build as well. |
| native ON | timing extras | `LEGO_NATIVE_TIMING`, `LEGO_NATIVE_GPU_TIMESTAMPS`, F10 GPU pass profile (`gpu_pass_profile.h`) | F9/F10 use `GetAsyncKeyState`, so they need the interactive desktop. |
| native ON | pacing knobs | `LEGO_NATIVE_FPS_LIMIT` (default cap 240), `LEGO_NATIVE_NO_FPS_OVERLAY`, `LEGO_NATIVE_ADAPTER` | set the cap and adapter explicitly in A/B runs |
| both | sampling profiler | `LEGO_SAMPLE_PROFILE` (+ `_TRIGGER` or F9) | attribution only (section 5) |

Report median and p99 frame time (ms) over a fixed window, then the median of those over at least 5 runs. Means hide the attract loop's fast and slow stretches (section 3). `runstats.py` prints, for perf.csv:
- one `scene` line per `(draw_calls, vertices_processed)` group, folding together pairs within 2 draws and 5 % vertices (on OFF builds the intro alternates between 218/222 and 219/226, and the attract scene sits at 226/1022);
- fps, median draws and median vertices per 10 s, counted from the first frame.

## 3. Repeatable scene and direct boot

**There is no way to boot straight into a level without input.**
- `native_direct_startup.h` only sets up the environment and collects evidence. It is active only if `<exe dir>\native-environment.ini` exists. Then it:
  - copies the `[renderer]` `LEGO_NATIVE_*`/`PLUME_*` keys into the environment;
  - creates `<exe dir>\logs\<UTC>-<pid>` and points `LEGO_NATIVE_FRAME_METRICS`, `log_file` and `log_flush_interval=1` there;
  - starts `tools\CrashCapture.exe` if it exists.

  It never loads a level. `run-game.ps1` never copies that ini, because it would move game.log and frames.csv out of the run dir.
- `rexlego/src` has no cvar for a level, warp, autoload or benchmark.
- `skip_cutscenes` only makes cutscenes skippable.
- The backtick console has only `threads` and `hangwatch`.

**The only scenes that need no input are the intro and the title/attract loop.** In Agent 8's first OFF boot the first frame came about 61 s after launch: 35 s of that was a gap after `Initializing shader storage` (run `build/agent8/runs/1928-first`; session 3's runs: 11-35 s, sections 6.2 and 7.4). perf.csv then shows two scenes (runs `1928-first` and `2125-devoff1`, checked 22:25):
- **Intro:** first frame + 0 to ~33 s. Its counters alternate, about half and half, between `draw_calls`/`vertices_processed` 218/222 and 219/226. It runs at a median of 57-59 fps, i.e. **at the 60 fps cap** (`runstats.py --warmup 0` on run 1928: 1705 frames over 32.5 s, median 16.95 ms).
- **Title/attract:** from ~33 s on, at 226 draws and 1022 vertices. **The counters stay flat for the rest of the run.** fps still swings between ~16 and ~55 over stretches of 30-170 s. In run 1928 it is slow from 33 to ~145 s, fast from ~150 to ~315 s, and mixed after that; in run 2125 the first slow stretch lasted only ~40 s. The swings showed up only in the first boot of each exe: `1928-first` ran beside a -j10 build, and `2125-devoff1` probably beside the native-bin build. Agent 8's run `2005-dry1` did not show them. **So the cause is open:** build load, or a cost of an exe's first boot. *(Correction, 22:40: `proc.csv` `cpu_pct_machine` is the game's own CPU as a share of the 12 logical CPUs, not machine load, so it can't rule background load in or out.)* From the next boot on, Agent 8's `first-boot.ps1` also logs machine-wide CPU (`sys_busy_pct`, `other_cores`, `build_procs`). Agent 8's timing window, 60-120 s after the first frame, is well past the 33 s scene change.

The run toml (installer defaults) sets:
- `framerate_limit = 60`. The cvar's own default is 0 = unlimited (`rexglue-sdk/src/graphics/command_processor.cpp:64`).
- `frame_rate = '60'`: guest vblank pacing; the default is `'30'` (`graphics_system.cpp:41`).
- `vsync = false`: guest vblank pacing and GPU-thread wait policy, not host vsync.

**Measurement protocol for the attract scene** (Agent 8 runs it; sent to Agents 8 and 1 at 21:25):
1. Window: time it from the **first frame**, not from launch, because shader-storage time varies. Use `runstats.py --warmup 20`, or the same fixed offset, then a 30-60 s window. Use the same `-Seconds` for every run.
2. Runs: at least 5 per build, interleaved A B B A A B... Keep the same power state (on mains, same Windows power mode) and the same quiet machine. Check the `DXGI adapter:` line on every run; it should be the MX570.
3. Results: take median and p99 frame time per run, then the median of those across runs. Report the **intro and the attract scene separately**: `runstats.py` groups frames by `(draw_calls, vertices_processed)` and prints a `scene` line per group. On OFF builds `draw_calls` alone barely moves (218 to 226), so it cannot separate the fast and slow stretches inside the attract scene. Inside the attract scene, compare the same fixed windows from the first frame (`per 10 s` lines) across many runs, because the stretches differ from run to run. *(Correction to the 21:25 note: bucketing by `draw_calls` does not separate the attract phases.)*
4. Headroom: the intro runs at the 60 fps cap, so a faster build can't show up there. For A/B timing, consider `-Cvar framerate_limit=0` (uncapped; Agent 8 decides).
5. Native ON builds: `frames.csv` `interval_ms`, plus perf.csv rows (Agent 7's patch) for a like-for-like comparison with OFF.
6. Timing comes only from user-started runs on the interactive desktop (`bench\agent8\RUN-TIMING-MATRIX.cmd`). Never take it from agent-launched or `-Profile` runs.

The hub and the levels need input: a human on the interactive desktop, or a virtual XInput pad. Gameplay also needs Toy Pad tags (section 4). Once someone has played to a save, later runs can start from it: pass `-UserDir` pointing at a fresh copy of that `user` dir for each run, so autosaves don't make runs drift. "Continue" then shortens the route, but it still needs input.

### 3.1 Headroom, and a heavier no-input scene (for Agent 8, 23:25)

Matrix 1 (22:32-23:02, `build/agent8/matrix/20261121-2232/summary.md`) had both arms locked at the 60 fps cap (median 16.66 ms), so it can't show a speed-up. **What caps the frame rate** (OFF builds, from the code):
- `vsync = false`, the default (the cvar is init-only). The guest vblank then fires every 1 ms (`graphics_system.cpp:164-176`); `frame_rate` matters only when vsync is on. So the guest's vblank doesn't hold it to 60 Hz.
- Host presentation never waits for the display: `Present(0, DXGI_PRESENT_RESTART | ALLOW_TEARING when supported)` (`d3d12_presenter.cpp:1195-1197`).
- **`framerate_limit` is the only cap.** `LimitFramerate()` runs at every guest swap on the GPU thread: it sleeps until 1.5 ms before the deadline, then spins (`command_processor.cpp:1011-1047`).
- Native ON builds also have their own presentation cap: `native_fps_limit`, or the override `LEGO_NATIVE_FPS_LIMIT` (`gpu_native/device.cpp:1788`, clamped to 0..1000; 0 means no cap). Agent 8's native matrices set it to 60.

**Headroom metrics:**

| metric | how | caveats |
|---|---|---|
| uncapped throughput | arm `"cvars": ["framerate_limit=0"]`; native builds also `"env": {"LEGO_NATIVE_FPS_LIMIT": "0"}`; the same window (60 s from the first frame, 60 s long). Headroom = 16.67 ms / median - 1 | **Not run yet.** First check that fps rises above 60 and the title loop stays stable (a functional run in my slot can do this). Uncapped load raises laptop power and heat, so keep interleaving, lengthen the cooldown (>= 30 s) and log GPU clocks. CPU cores are not comparable with capped runs. |
| GPU busy at the cap | `run-game.ps1 -GpuLog`: NVML once a second into `gpu.csv`; `summary.txt` reports util, graphics clock, power, temperature, pstate and the share of samples per clock-limit reason. For Agent 8's runner, use the same NVML calls (`harness/nvml.cs`, ~0.1 ms per sample). **Not `nvidia-smi ... -f <file>`:** nvidia-smi buffers the file until it exits, so a killed logger leaves an empty file (tested 23:27). | Doesn't change the game's behaviour. `utilization.gpu` is relative to the current clock, so read it with the graphics clock and the pstate. Many samples with the `idle` limit reason (GPU idle, clocks dropping) at the cap mean GPU headroom; `power_cap` or `thermal` mean there is none. |
| CPU cost at the cap | `cpu_cores` (already in Agent 8's table), or per frame: cpu_cores / fps | Includes spinning: the limiter spins the last <= 1.5 ms of every frame, and `gpu_thread_fast_wait` spins briefly before it waits. Cheap but noisy. |
| busy share per thread | `run-game.ps1 -Profile`: `analyze_profile.py` classifies samples per thread as busy, wait or io. Samples in `LimitFramerate` on the GPU thread are the limiter's slack. | PROFILE ONLY: attribution, not timing. |
| limiter slack per frame | proposal: a `limiter_wait_us` perf.csv column (time spent in `LimitFramerate` per swap); busy = frame_time - limiter_wait | Needs a small SDK patch from its owner. It is the best long-term metric: headroom at the cap, with no change in behaviour. |

**Heavier no-input scene:** the game content has none.
- The title/attract counters stay flat for 650 s (run 1928), so there is no attract demo.
- There is no level or warp cvar (see above).

Instead, make the same scene heavier:
- CPU and pipeline: uncap it, as above.
- GPU: `resolution_scale=2` (range 1-8, needs a restart; it overrides `draw_resolution_scale_x`/`_y`, `texture/cache.cpp:74,237`) renders 4x the pixels on the emulated Xenos path. Combine it with `framerate_limit=0`. Its effect on native ON builds is untested.

Suggested arms: `base-unc` and `r0-unc` with `["framerate_limit=0"]`; optionally `base-unc-rs2` with `["framerate_limit=0", "resolution_scale=2"]`.

## 4. Toy Pad, menus, and what to ask the user

**Input facts** (from the source; nothing past the title screen has been driven yet):
- **Keyboard (default bindings):**

  | key | pad |
  |---|---|
  | Return or Escape | Start |
  | Plus | Back |
  | J / K / H / U | A / B / X / Y |
  | E / Q | LB / RB |
  | I / O | LT / RT |
  | WASD | left stick |
  | arrows | right stick |

  Keyboard input is read only while the game window has focus, and each key must be held for at least 100 ms. F9 (sampler) and F10 (GPU pass profile) use `GetAsyncKeyState`.
- **Hidden desktop:** agent-launched games run on `WinSta0\exebox-*`. SendInput and screenshots do nothing useful there, so **agents cannot drive the menus**.
- **XInput:** `--input_backend=xinput` (`rexglue-sdk/src/input/input_system.cpp:33`; the default is `sdl`) has no focus gate. A virtual Xbox 360 pad would therefore work from the hidden desktop: the ViGEmBus driver, which needs an admin install, plus a client such as Python `vgamepad`. This is **untested and a proposal only**. ViGEmBus is archived upstream, but its installer still works.
- **Toy Pad emulation:** `toypad_emulation = true` (on in the run toml) listens on TCP `127.0.0.1:9191`. The port can be overridden with `REXGLUE_TOYPAD_PORT`, or `XENIA_TOYPAD_PORT` (`rexglue-sdk/src/input/portal/emulated_toypad.cpp:152`).
  - Each request starts with a 5-byte header: `[cmd, pad (1 centre, 2 left, 3 right), index 0..6, old_pad, old_index]`.
  - Commands:

    | cmd | name | payload |
    |---|---|---|
    | `0x01` | LOAD | a 180-byte NTAG213 dump, then a u16 path length and the path |
    | `0x02` | REMOVE | |
    | `0x03` | MOVE | |
    | `0x04` | GET_LED | none; the reply is 40 bytes |

  - A companion app can be launched with `toypad_app_autostart` / `toypad_app_path` (`rexlego/src/toypad_app.cpp:25`). These are left out of the harness toml.
  - **We have no tag dumps.** The story starts by asking for the starter characters on the pad, so **no gameplay scene can be reached without tags**. Only the title/attract loop and the menus can.

**What to ask the user.** Each of these is copy-paste ready.
1. *Map the menus (one session, about 10 min, on your own desktop):*
   > "Please open PowerShell in `<workspace>` and run
   > `powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\baseline-bin -Seconds 900 -StatsWarmup 20 -Tag human-menu`.
   > The window stays black for about 60 s. When the title screen appears, click once inside the window so it has keyboard focus. Then:
   > - press **Return** (Start) at the title;
   > - press **J** (A) to accept each prompt;
   > - press **K** (B) to go back;
   > - use **WASD** to move in menus.
   >
   > Hold each key for about a quarter of a second. For every screen, write down the time since launch and its text, or take a screenshot with Win+Shift+S. Note especially any 'place a character on the Toy Pad', profile, storage or save prompt. Stop at the first screen you can't get past. The script closes the game at 900 s; Alt+F4 also works. Then tell us the run folder it printed."
2. *Toy Pad tags (needed for any gameplay scene):*
   > "Do you have the LEGO Dimensions starter-pack figures (Batman, Gandalf, Wyldstyle and the Batmobile) and a way to dump their NFC tags to 180-byte NTAG213 files (a USB NFC reader such as an ACR122U, or a phone NFC app)? Or is a tool that makes virtual tags acceptable to you? Without tags, only the title/attract scene can be measured."
3. *Optional, to let agents drive the menus from the hidden desktop:*
   > "May we install the ViGEmBus virtual-gamepad driver (one admin install, about 1 MB)? Agents could then drive the menus through `--input_backend=xinput` without your keyboard."

After step 1 we can script the route, and record it with `-UserDir` pointing at a saved profile. After step 2, tags are placed with the TCP LOAD command above; I can write a small `harness/toypad.py` client for that.

## 5. Profiling: what works headless on this laptop

| option | admin | rebuild | cost per capture | gives |
|---|---|---|---|---|
| 1. built-in sampler + `analyze_profile.py` (`run-game.ps1 -Profile`) | no | no | one run of about 3 min | per-function self and inclusive time from the lld map, per-thread names (LSPX) |
| 2. WPR/ETW + xperf (both installed) | **one elevated prompt per capture** | no (a PDB relink is optional) | ETL ~100-300 MB per minute (estimate); 1-3 % overhead; the first symbol load takes minutes | system-wide CPU samples with stacks, including drivers, the kernel and other processes |
| 3. Tracy v0.13.1 (SDK submodule) | no for zones; yes for its sampling | **yes:** a code change plus a full rebuild (~21 min at -j10) | near zero | today only 9 zones (the xenos command processor) plus frame marks |

**Recommendation:** use option 1 now. Use option 2 when the user can give one elevated prompt per capture. Do Tracy only after someone instruments the hot paths. None of these is timing: label every capture **PROFILE ONLY, NOT FOR TIMING**.

### Option 1: sampler (works now)
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\baseline-bin -Profile -Warmup 90 -ProfileSeconds 30 -Tag base-prof
# re-analyse a run by hand (what the harness runs):
python DimensionsRecomp\tools\native-cpu\analyze_profile.py <run>\profile-<tick>.bin <run>\legodimensions.map --meta <run>\profile-meta.json --json -o <run>\profile.json
```
- Needs `LEGO_SAMPLE_PROFILE=1` and the trigger file (the harness sets both), or F9 on the interactive desktop.
- Recording starts ~150-200 ms after the trigger appears (the analyser has `--trigger-latency 0.175`). The `.bin` is written next to the exe (the run dir) when the trigger is deleted.
- Check `rounds_per_s >= 250`; the harness flags anything lower.
- The **legacy sampler** in the `baseline\` tree supports the trigger file (`baseline/DimensionsRecomp/rexlego/src/sample_profiler.cpp:99-104`, which polls every 50 ms and beeps for 150 ms at start and at stop). So `-Profile` works on `baseline-bin` from the hidden desktop. It calls `timeBeginPeriod(1)` when its thread starts (line 100), so with `LEGO_SAMPLE_PROFILE` set the system timer runs at 1 ms for the **whole run**, not only while recording (the analyser flags it as `timer_observer_effect`). The current tree's sampler (18:18) uses a high-resolution waitable timer (`timer_mode 1`) and an LSPX trailer.

### Option 2: WPR/ETW + xperf
- **Tested 21:56 without elevation:** `wpr -start CPU -filemode` failed with `0xc5585011 Failed to enable the policy to profile system performance`. That error means the profile privilege needs an elevated token.
  - The account is a UAC admin, but Administrators is deny-only in the agents' token. It is also in `Performance Log Users`.
  - So: **the user starts and stops each capture from an elevated prompt.** `wpr` and `xperf` are both installed (WPT 10.0.22621).
- Capture: in an *elevated* PowerShell (Win+X, Terminal (Admin)), on the user's desktop:
  ```powershell
  cd <workspace>
  New-Item -ItemType Directory -Force bench\agent3\etw | Out-Null
  wpr -start CPU -filemode
  #   ...start the game, wait for the scene, let 30-60 s pass...
  wpr -stop bench\agent3\etw\lego-cpu.etl
  ```
- Reading it (headless, no admin):
  ```powershell
  $x = 'C:\Program Files (x86)\Windows Kits\10\Windows Performance Toolkit\xperf.exe'
  $env:_NT_SYMBOL_PATH = 'build\baseline-bin;srv*C:\symbols*https://msdl.microsoft.com/download/symbols'
  & $x -i bench\agent3\etw\lego-cpu.etl -symbols -o bench\agent3\etw\cpu-detail.txt -a profile -detail     # samples by process and function
  & $x -i bench\agent3\etw\lego-cpu.etl -symbols -o bench\agent3\etw\stacks.txt -a stack -butterfly 20 -process legodimensions
  & $x -i bench\agent3\etw\lego-cpu.etl -o bench\agent3\etw\dump.csv -a dumper -add_fieldnames                 # raw SampledProfile IPs
  ```
- **The game's symbols:** the baseline exe has **no PDB**, so xperf shows `legodimensions.exe` plus an offset. There are two ways round this:
  - (a) **Relink with a PDB.** Agent 2 configures with `-DCMAKE_EXE_LINKER_FLAGS="-Xlinker /DEBUG:FULL -Xlinker /OPT:REF -Xlinker /OPT:ICF"` and the same in `CMAKE_SHARED_LINKER_FLAGS`. This is a link-only rebuild that yields public symbols (`sub_8xxxxxxx`), and `/OPT:REF,ICF` keeps Release's layout.
  - (b) **Map the raw IPs** from `dump.csv` with the lld `.map`, as `analyze_profile.py` does. That is a small script, which I can write if option 2 is chosen.
- **Costs:**
  - The first `-symbols` run downloads Windows symbols (about 0.5-1 GB into `C:\symbols`, several minutes); later runs take about 1-2 min.
  - Do not use traced runs as timing results.
- **PresentMon** (not installed): its README says it runs without admin for members of `Performance Log Users`, and this account is one. It would add per-frame present-to-present and display times to the user-started timing runs, independently of the game's own counters. It is a single exe from GitHub releases. **Ask the user before downloading it.**

### Option 3: Tracy (proposed only; nothing started)
- **What exists:**
  - `rexglue-sdk/thirdparty/tracy` is v0.13.1 (protocol 76).
  - `REXGLUE_ENABLE_TRACY` (SDK `CMakeLists.txt:24`, default ON) builds `TracyClient.dll`, which `baseline-bin` already ships. It is built with `TRACY_ENABLE TRACY_ON_DEMAND TRACY_DELAYED_INIT TRACY_MANUAL_LIFETIME TRACY_FIBERS` (`thirdparty/CMakeLists.txt:386-395`).
  - The zones compile in only with `REXGLUE_ENABLE_PROFILING`, and SDK `CMakeLists.txt:28` defines that only for non-Release configs. **So the Release builds contain no zones.**
- **Gaps:**
  1. `TRACY_MANUAL_LIFETIME` needs `tracy::StartupProfiler()`, and no caller exists (grep of SDK `src`/`include` and `rexlego/src`). The client never starts, so a capture would have nothing to connect to.
  2. Only 9 zones exist, all in xenos `command_processor.cpp`, and `FrameMark` is only in `Profiler::Flip`. CPU attribution of guest code would need many more zones.
  3. Tracy's call-stack sampling on Windows uses ETW and needs admin, the same limit as option 2.
- **Proposal, if wanted:**
  - (a) Whoever owns the entry point adds `tracy::StartupProfiler()` at start and `tracy::ShutdownProfiler()` at exit.
  - (b) Agent 2 builds RelWithDebInfo, or Release with `-DCMAKE_CXX_FLAGS=-DREXGLUE_ENABLE_PROFILING` to keep Release codegen. That is a full game rebuild of ~21 min at -j10.
  - (c) The tools, v0.13.1 to match the protocol: the GitHub release `windows-0.13.1.zip` has `tracy-capture.exe` and `tracy-csvexport.exe` (needs network and the user's OK). Or build `thirdparty/tracy/capture` and `csvexport` with CMake; CPM fetches their dependencies, so that also needs network, about 5 min.
  - (d) Headless capture (default port 8086):
    ```powershell
    tracy-capture -o bench\agent3\tracy\run.tracy -a 127.0.0.1 -p 8086 -s 30 -f      # capture.cpp:95: -o -a -p -f -s seconds -m memlimit
    tracy-csvexport -e bench\agent3\tracy\run.tracy > bench\agent3\tracy\zones-self.csv   # -e self times; -u one row per zone event; -g GPU zones
    ```

## 6. Results

### 6.1 Self-test: 24 passed, 0 failed (session 3, 04:13; earlier 23 of 23 at 03:16 and 16 of 16 at 23:34)
`powershell -NoProfile -ExecutionPolicy Bypass -File harness\selftest\selftest.ps1 [-Only normal,profile,crash,kill,input]`

**Session 3 (02:48), `-Only normal,input`: 14 passed, 1 failed.** The new `input` case runs the fake exe with `--input_backend=xinput` and the route `harness/routes/selftest-input.txt`. These passed: the DLL checks (loaded by the run's pid from `<run>\xinput1_4.dll`, mapped once, no DLL in the bin dir, `--input_backend=xinput` and `AGENT3_VPAD` reached the exe), the bad-script refusal (exit 2), the keystroke sequence, `wait_scene`/`wait_change` (900/120000 → 910/120001) and the input.csv checks. The one FAIL was the GetState sequence: after `hold B`, the B release and the stick move fell into one poll. Fixed with `sleep 0.3` in the route.

**Session 3 (03:15-03:16), all five cases, in Agent 8's slot: 23 passed, 0 failed** (80 s). The GetState fix holds; the input case passed all 7 checks.
- Afterwards I found that the input case had rebuilt `build\agent3\vpad\xinput1_4.dll`, the copy the B-gate runs use. Only the PE TimeDateStamp changed (bytes 0x80-0x81; sha256 `0676DD55…` instead of the gate's `309DF316…`). I copied the gate DLL back from `runs/20261122-030752-bgate-b` at 03:16:50, before the next gate run (`bgate-long-devoff2`, 03:17:56).
- Fix (03:20):
  - `build-vpad.ps1` skips the build when the DLL is newer than `xinput1_4.c`/`.def`; `-Force` rebuilds, and it takes `-OutDir`.
  - The self-test builds its own copy (`-OutDir build\agent3\selftest-bin\vpad -Force`), runs the input case with `-VPadDll` pointing at that copy, and checks that the gate DLL's hash is unchanged (8th input check).
  - Tested:
    - `build-vpad.ps1` with no arguments: "up to date", gate hash unchanged;
    - `-OutDir … -Force`: built (`16DF5356…`); the same `-OutDir` without `-Force`: "up to date";
    - `selftest.ps1` and `build-vpad.ps1` parse.
  - **Re-run 04:12:01-04:13:54 in Agent 8's slot (113 s), all five cases: 24 passed, 0 failed.** The input case built its own copy (`616D7C5D…`), and the game loaded it from the run dir (336 reads, 58 with input). The gate DLL stayed `309DF316…` (8th input check). Output: `build\agent3\logs\selftest-0412.txt`.

The 22:50 rerun took 81 s and covered `-DryRun` and the scene lines. After the near-pair fold went into `runstats.py`, the normal case passed again at 22:52 (7 passed, 0 failed). `-DryRun` on `baseline-bin` linked 8 files, found the map and exited 0 (22:49).

The 23:34 run (74 s, no game or runner active) adds an eighth normal check for `-GpuLog`: gpu.csv from NVML with 13 samples, 9 after the first frame + warm-up; MX570 at P3, median 817 MHz, util median 14 %; `close_sent_s` recorded. One fix after it: the profile trigger was deleted one loop tick (~1 s) late, so the window was 5.0 s for a 4 s request. The profile case was rerun at 23:35 with a 4.005 s window (5 passed, 0 failed).

The self-test builds `harness/selftest/fakegame.cs` with the .NET Framework `csc` into `build\agent3\selftest-bin\fakedimensions.exe`. The fake exe:
- writes the real 17-column perf.csv, frames.csv, the log markers (the TU patch line, `DXGI adapter:`, shader storage), and an LSP1 `profile-<tick>.bin` with an LSPX trailer when triggered;
- reads an lld-style map.

The test then runs five cases through `run-game.ps1`. Results are in `build\agent3\selftest-latest.txt`; run dirs are in `build\agent3\selftest-runs`.

| case | checks (all PASS) |
|---|---|
| normal (12 s) | exit 0; closed by WM_CLOSE with exit code 0; verdict RUNNING from the DXGI marker and perf.csv; perf.csv parsed (334 frames measured, median 18.47 ms, p99 38.76 ms); frames.csv via the env var; flags and CWD reached the exe; toml `user_data_root` plus `-Cvar` override and append (including a value with a space); toml not rewritten; 2 files hard-linked; 11 samples; desktop `exebox-*`, so mode FUNCTIONAL ONLY; with `-GpuLog`, gpu.csv from NVML summarised after the first frame |
| profile (4 s trigger) | exit 0; mode PROFILE ONLY; env set; trigger removed; one `profile-*.bin`; `profile-meta.json` window 4.005 s (23:35); analyser ran: top self `sub_82000000` (guest), rounds/s 999.8, duration 3.98 s from the trailer; thread names from LSPX |
| crash (unhandled exception at 4 s) | exit 1; verdict CRASHED; WerFault attachment detected; exit code 0xE0434352; events 1001 (WER), 1000 (Application Error) and 1026 (.NET Runtime) collected |
| kill (`--fake_ignore_close`) | WM_CLOSE ignored, so killed after 4.14 s; `windows_at_close` recorded |
| input (fake exe with `--input_backend=xinput`, route `selftest-input.txt`, 16 steps; 03:16) | `build-vpad.ps1` built the DLL (clang-cl, no CRT); a bad script is refused before the launch (exit 2, file:line); exit 0, 16/16 steps, run ended by the script, WM_CLOSE in 0.07 s; the game loaded the run-dir DLL (its pid, mapped once, none in the bin dir, `--input_backend=xinput` and `AGENT3_VPAD` set); XInputGetState saw the presses, the stick and the releases in order (317 reads, 61 with input); XInputGetKeystroke handed out the 10 key-down/key-up events in order; input.csv: the waits are ok, `wait_change` 900/120000 → 910/120001, 1 TIMEOUT (on purpose). Since 03:20 there is an 8th check: the gate DLL is unchanged and the run used the self-test copy |

The first pass (21:48) found three harness bugs, all fixed:
- `Get-ChildItem -LiteralPath ... -Include *.dmp` returns every file in PowerShell 5.1, which produced false crash verdicts. It now uses `-Filter`.
- The WMI WerFault query took about 6 s on the busy box, so samples were skipped. It now does `Get-Process` first and runs WMI once per new WerFault pid.
- The self-test died on the fake game's stderr (the CLR crash text). It now runs the child with `ErrorActionPreference = Continue`.

### 6.2 Baseline runs (`build/baseline-bin`, session 3, through Agent 8's slot)
Both runs are done. They are FUNCTIONAL ONLY and PROFILE ONLY, on the hidden desktop, so **NOT FOR TIMING**. Console logs: `build\agent3\logs\base-console.txt` and `base-prof-console.txt`.
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\baseline-bin -Seconds 180 -StatsWarmup 20 -GpuLog -Tag base
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\baseline-bin -Profile -Warmup 90 -ProfileSeconds 30 -Tag base-prof
```

| | `runs/20261122-021532-base` (180 s, `-GpuLog`) | `runs/20261122-022642-base-prof` (`-Profile`) |
|---|---|---|
| wall clock | 02:15-02:18 | 02:26:35-02:29:21 |
| exit / close | 0; WM_CLOSE, closed in 11.49 s | 0; WM_CLOSE, closed in 3.05 s |
| `toml_rewritten` | False | False |
| elapsed | 191.6 s | 128.2 s |
| adapter / TU line | MX570 (0x10DE/0x25A6, 1934 MB); TU 0.0.0.3 → 0.0.23.3 at 2.65 s | same; TU at 11.55 s |
| first frame (perf.csv > 1 KiB) | 13.0 s | 35.0 s |
| game.log | 90 lines, 40 warnings, 0 errors, 0 MISSING-FUNCTION | 90 lines, 40 warnings |
| CPU / peak working set / peak private | 342.4 s (1.79 cores) / 689 MB / 1182 MB | 125.6 s (0.98 cores) / 691 MB / 1388 MB |
| frames (measured after the warm-up) | 9902 (8716) | 2616 (2369) |
| frame time mean / median / p95 / p99 / max | 17.07 / 16.67 / 26.21 / 40.08 / 185.5 ms (58.6 fps; 1 % low 24.95 fps) | 34.82 / 17.43 / 118.64 / 173.93 / 338.1 ms (28.7 fps) |
| frames > 50 ms / > 100 ms | 30 / 1 | 549 / 220 |
| scenes (draws/vertices) | pre-title 218/222: 670 frames, 11.2 s; title 226/1022: 8039 frames, 137.3 s, from ~30 s after the first frame | title 226/1022 from ~30-40 s after the first frame |

- **GPU** (NVML, base run): 148 samples; util 39 %, core 1684 MHz, memory 6001 MHz, 16.8 W, 77 °C (max 78); P0 in 99.3 % of samples; no throttle reasons.
- **Profile** (`profile-723184687.bin`, trigger 02:28:14-02:28:44, 30 s): **rounds_per_s 0.9, against ≥ 250 expected.** 2054 samples in ~26 rounds over 79 threads; 53 busy (2.6 %). Busy split: guest 56.6 %, rexruntime 17.0 %, rexlego 9.4 %, d3d12 7.5 %, system 9.4 %. The analyser warns "machine CPU-saturated; sampler held timeBeginPeriod(1)".
  - Cause: Agent 2's B build (ninja from 02:22, 10× clang++) overlapped the whole run. It also explains the 35 s first frame and the frame spikes in that run.
  - Attribution only and too thin to use. If a baseline profile is needed, re-run it on a quiet machine.
- The first frame came at 13.0 s in the quiet run, against 61.1 s in Agent 8's first boot below (which had a 35 s gap after `Initializing shader storage`). Not investigated.

**Reference, Agent 8's first boot** (`build/agent8/runs/1928-first`, `baseline-bin`, hidden desktop):
- TU 0.0.0.3 → 0.0.23.3;
- adapter `NVIDIA GeForce MX570 (vendor 0x10DE, device 0x25A6, 1934 MB dedicated)`;
- first frame at 61.1 s, including a 35 s gap after `Initializing shader storage for title 5752084B`;
- 0 errors, 40 warnings;
- peak working set 708 MB, 79 threads.

### 6.3 Toml rewrite
The only callers of `SaveConfig` are the F4 settings overlay (`settings_overlay.cpp:867,904`) and the mod menu (`mod_menu.cpp:454`), so the game should not rewrite the toml on exit. `run.json` records `toml_rewritten` (the sha256 before and after) to confirm this on the real game. The self-test confirms only the harness side.

## 7. Virtual XInput pad and input scripts (session 3, for the B game gate)

**Why.** Agent-launched runs sit on a hidden desktop, and keyboard input can't reach the game there:
- SDL, the default input backend, reads the keyboard only for a focused window. A hidden-desktop window never gets focus, so `PostMessage`/`SendInput` do nothing (tried).
- ViGEmBus needs a driver and admin, so it is out.
- The game's XInput backend (`--input_backend=xinput`, `rexglue-sdk/src/input/xinput/xinput_input_driver.cpp`, built into `rexruntime.dll`) has no focus check. It loads `xinput1_4.dll` by name, and that is not a KnownDLL, so a copy next to the exe wins.

**Agent 1's conditions (session 3):**
- harness-only tooling; user mode only, no driver, nothing system-wide;
- the DLL exists only as the source in `harness/vpad/`, the build output `build\agent3\vpad\xinput1_4.dll` and copies in run dirs, never in a staged `build/agent2/*-bin`;
- built with clang-cl at ≤ 2 threads;
- each run's saves and profile stay in its run dir;
- no generated Toy Pad tags tonight.

| file | role |
|---|---|
| `harness/vpad/xinput1_4.c` | the DLL (kernel32 only, no CRT). Exports, ordinal base 100: `XInputGetStateEx` @100 (NONAME), `XInputEnable` 101, `XInputGetBatteryInformation` 102, `XInputGetCapabilities` 103, `XInputGetKeystroke` 104, `XInputGetState` 105, `XInputSetState` 106. Without env `AGENT3_VPAD`, or before the state file has its magic, every slot is not connected. Keystrokes are made from button changes; `XInputEnable` is counted, not applied. |
| `harness/vpad/build-vpad.ps1 [-OutDir d] [-Force]` | builds `build\agent3\vpad\xinput1_4.dll` (4608 bytes) with `toolchain\llvm-23.1.6` clang-cl. It skips the build when the DLL is newer than its sources (every link stamps a new PE TimeDateStamp, and the gate runs record the DLL's sha256 `309DF316…`); `-Force` rebuilds |
| `harness/vpad/vpadhost.cs` | `Agent3Input` (C# 5, compiled by run-game with `Add-Type`): parses the script, runs it on a background thread, writes slot 0, logs `input.csv`, fills the `input_script` block of `run.json` |
| `harness/run-game.ps1 -InputScript` | see section 1 |
| `harness/route-report.ps1 -RunDir` | after the run: every step with its scene, the marks, a scene timeline, and checks (exit, crash, script, DLL, pad polled, B-gate fail lines, exit sequence); writes `route-report.txt`. On native builds (perf.csv draws/vertices all 0) the scene is `n<draws>` from `frames.csv` or `native-frames.csv`, matched by its `frame` column (section 7.4). The watchdog/hang check matches `watchdog`, `hang detected`, `STUCK-LOCK`, `Minidump written` and `[FATAL]` (the last three since 05:16: before that only the dumps check caught native3d's stuck lock) |
| `harness/routes/b-gate-menus.txt` | the B-gate route: boot, title, front end (37 steps, ~150 s after the first frame; sha256 `CF803C22…`) |
| `harness/routes/b-gate-menus-long.txt` | the same first 34 steps plus a 90 s idle tail with a mark every 10 s (54 steps; sha256 `1F3559C8…`): the tie-break for the `end`-mark divergence (section 7.2) |
| `harness/routes/selftest-input.txt` | the self-test route for the fake exe |
| `harness/routes/attract-long.txt` | task #16: START, A, A to 220/534 at the same times as `b-gate-menus.txt` steps 1-11, then no input with a mark every 10 s for 380 s, and `stop` at ~472 s after launch (91 steps; sha256 `4D35FAF4…`) |
| `harness/attract-report.py RUN [RUN…]` | task #16: the idle exit, the attract sequence against A0 and H0, stalls, steady stretches, the scored window (default H0 + 6.5 s for 11 s) with its flags, the heavy sub-window (info only), a cross-run table, and `--json` (section 7.4) |
| `harness/run-game.ps1 -SeedXenos dir`, `build/agent3/seed/devoff2-214/` | task #16: a warm-storage run. The seed is the devoff2 tie-break run's storage (214 pipelines), read-only (section 7.4 item 6) |

**State file** (`<run>\vpad-state.bin`, 4096 bytes; the struct `VPAD_SHM` in `xinput1_4.c` is the reference):

| offset | content |
|---|---|
| 0 | magic `PAD1` (0x31444150), written last by the harness |
| 4 | version 1 |
| 8 | connected mask (bit n = slot n; slot 0 is connected) |
| 12 | pid of the process that mapped the file |
| 16 | GetState calls per slot |
| 32 | calls that returned input, per slot |
| 48-68 | GetCapabilities calls, GetKeystroke calls, keystroke events, SetState calls, Enable calls, last Enable argument |
| 72 | last vibration per slot |
| 88 | map count |
| 128 | four 16-byte slots (seqlock `seq`, buttons, LT, RT, LX, LY, RX, RY) |
| 192 | the DLL's path in the process |

**Script commands** (one per line, `#` starts a comment; the header of `harness/vpad/vpadhost.cs` has the details): `wait_first_frame [s]`, `wait_perf_rows N [s]`, `wait_log "regex" [s]`, `wait_scene DRAWS VERTICES [s]`, `wait_change [s]`, `sleep S`, `press BTN[+BTN] [count] [hold_ms] [gap_ms]`, `hold BTN MS`, `stick L|R X Y MS`, `trigger L|R V MS`, `connect MASK`, `mark LABEL`, `stop`. A timed-out wait is logged as TIMEOUT and the script goes on.

> [!IMPORTANT]
> The real game holds perf.csv unshared while it runs (`rexglue-sdk core/perf/counter.cpp` `SetCsvLogPath` → `rex::filesystem::OpenFile(path, "w")` → `_wfopen_s`, `core/filesystem_win.cpp:80`), so the script can't see the scene live.
> - `wait_perf_rows`, `wait_scene` and `wait_change` return `n/a` at once on the real game. They work on the fake exe.
> - `wait_first_frame` falls back to perf.csv > 1 KiB (`GetFileAttributesEx` needs no share access).
> - game.log is shared, so `wait_log` works live.
>
> Routes therefore use fixed sleeps. `route-report.ps1` maps each step's `perf_bytes` onto the final perf.csv. perf.csv is flushed every 60 rows, so a step's scene can lag by up to 60 frames.

**Blind.** There are no screenshots: `PrintWindow` on the hidden desktop returns black. What a route did comes from input.csv (pad counters, perf.csv size, game.log position), game.log, the final perf.csv and the saves in `<run>\user`.

### 7.1 Dry run of the B-gate route (`devoff2-bin`)
`runs/20261122-030135-bgate-dry`, 03:01:35-03:04:13. Agent 8 launched it with my command, with `LEGO_NATIVE_MEMOPS_VALIDATE` removed. FUNCTIONAL ONLY. **It ran without the user.**
- Exit 0; WM_CLOSE in 0.93 s; `Window closing` → `Execution complete` → `Title terminated; hard-exiting process.` in order (game.log lines 158-160).
- 37/37 steps, 0 timeouts, ended by the script's `stop` at 152 s.
- The game loaded the DLL from the run dir (pid 58340, the game) and polled it every frame: 7890 GetState calls (136 with input), 39459 GetCapabilities, 7899 SetState. It made no GetKeystroke or Enable calls.
- perf.csv was held unshared, as expected; 7887 frame rows; first frame (perf.csv > 1 KiB) at 15.1 s.
- 0 lines of "not in any registered module", watchdog, crash guard or unimplemented. game.log: 160 lines, 108 warnings (mostly `INSTALL0_*.DAT` probes), 0 errors.

| mark | s since launch | s of frame time | scene (draws/vertices) |
|---|---|---|---|
| first-frame | 15.1 | 1.1 | 218/222 (intro) |
| title | 65.2 | 50.7 | 226/1022 (title/attract, from ~35 s of frame time) |
| after-start | 74.1 | 59.4 | 226/1022: START did not change the scene |
| after-a1 | 83.1 | 68.6 | 220/528: a front-end screen. game.log shows the Toy Pad LEDs set to white and `INSTALL0_15..18.DAT` probes. |
| after-a2 | 92.2 | 77.5 | 220/534 |
| after-a3, down-1, down-2, up-2, back-1..3, end | 105-152 | 90-138 | 220/534: the game read these presses (active reads went up), but the scene signature did not change |

**Reachable tonight:** boot (export lookups), intro, title, and the front-end screen after A.

**Not covered** (needs figures or the user): Agent 10's level, pause → Options → Back, cutscene, level change, Toy Pad figures, save, achievements and Quit.

### 7.2 B gate
Agent 8 runs `bgate-a` (devoff2-bin, started 03:05), then `bgate-b` (devoffB-bin), with the same route (sha256 `CF803C22…`) and the same harness flags. Agent 10 gives the verdict.
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\agent2\devoff2-bin -Seconds 420 -Tag bgate-a -InputScript harness\routes\b-gate-menus.txt
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\agent2\devoffB-bin -Seconds 420 -Tag bgate-b -InputScript harness\routes\b-gate-menus.txt
python build\agent10\bgate\logdiff.py --base "<bgate-a run dir>" --cand "<bgate-b run dir>"
```
**Results (03:05-03:10, Agent 8, FUNCTIONAL ONLY).** a = `runs/20261122-030511-bgate-a` (devoff2), b = `runs/20261122-030752-bgate-b` (devoffB); each run dir has a `route-report.txt`.
- Both runs are clean on Agent 10's fail list:
  - exit 0 via WM_CLOSE (a 3.1 s, b 0.83 s); the exit sequence in order (a lines 158-160, b 192-194);
  - 37/37 steps, 0 timeouts; the game loaded the pad DLL (sha256 `309DF316…`) and polled every press at least 10 times (active reads a 140, b 133);
  - 0 not-in-module, watchdog, crash-guard or unimplemented lines; no WER, no dumps.
- `logdiff.py` a → b: NEW 0, MORE 0, marker flags 0. GONE: 4 `Toypad[Read]`/`[Write]` keys (random challenge bytes; each log has 12 Toypad R/W lines).
- b had a 28-30 fps dip from ~70 to ~100 s of frame time while a build ran, so it polled the pad less often during those sleeps. The frame rates of a and b are not comparable (FUNCTIONAL ONLY).

| mark | a (devoff2): s of frame time, scene | b (devoffB): s of frame time, scene |
|---|---|---|
| first-frame | 1.1, 218/222 | 1.2, 218/222 |
| title | 50.7, 226/1022 | 50.9, 226/1022 |
| after-start | 59.7, 226/1022 | 59.9, 226/1022 |
| after-a1 | 68.8, 220/528 | 68.5, 220/528 |
| after-a2 … back-3 (9 marks) | 77.0-118.2, 220/534 | 76.9-119.6, 220/534 |
| **end** | **138.3, 220/534** | **139.9, 218/222** |

**The divergence.** b left the 220/534 screen without any input:
- At 134.69 s of frame time it drew 220/540 for 60 frames (+6 vertices, probably a fade quad), then 218/222 from 135.68 s to the end.
- game.log has a 4th front-end load at 03:10:18.675: 34 `INSTALL0_2..18.DAT` probes, lines 158-191, hence 142 warnings against 108.
- That load came 59.2 s after b's 220/534 screen appeared and 19.3 s after its last B.

Both devoff2 runs with the same inputs (a and the dry run) stayed on 220/534 to the end: 65.8 s and 62.6 s on that screen. It is not a frame-count timer: b had 2906 frames on the screen, a had 3421 and stayed.

My guess is the front end's ~60 s idle timeout. In devoff2 the DOWN/UP/B presses would reset it; in devoffB it fired as if they had not. It could also be run-to-run noise. I reported it to Agent 10 at 03:14 with a tie-break.

**Tie-break (03:17-03:25, Agent 8, FUNCTIONAL ONLY).** Route `harness/routes/b-gate-menus-long.txt` (sha256 `1F3559C8…`); the pad DLL is `309DF316…` in both runs. Runs: `runs/20261122-031756-bgate-long-devoff2` and `runs/20261122-032150-bgate-long-devoffB`.
- Both runs are clean:
  - exit 0 via WM_CLOSE (1.18 s / 4.31 s); the exit sequence in order (lines 209-211 / 213-215);
  - 54/54 steps, 0 timeouts, 0 fail lines, no WER or dumps.
- `logdiff.py` devoff2 → devoffB: NEW 0, MORE 0, flags 0; 142 warnings in each log; GONE = 4 Toypad challenge keys.
- **Both builds leave the 220/534 screen on their own**, the same way bgate-b did: 220/540 for 60 frames, then 218/222, plus the 4th INSTALL batch.
  - devoff2 left after 58.0 s on the screen (perf 132.12), devoffB after 62.4 s (perf 132.36); bgate-b left after 59.2 s.
  - bgate-a and the dry run (both devoff2) stayed 65.8 s and 62.6 s without leaving, so the timing varies from run to run. What delays or resets the timer is unknown (blind).
  - **So the `end`-mark divergence in the first pair is not devoffB-specific.**
- **After 218/222, both builds play the same no-input 3D attract sequence**, with the same scene signatures in the same order: 594/2813, 644/2868, 839/31674, 790/31625, 788/31613, 2832/470486 … 8019/1043795, 5265/773966, 4385/821295, 6353/1014219, 5194/879213. That is up to 12.6k draws and 1.7M vertices per frame.
  - The gate's coverage therefore includes 3D rendering, streaming and animation, not just menus.
  - Both builds have frames of 1-5 s there. First-time pipeline creation is the likely cause, but it wasn't measured (hidden desktop, FUNCTIONAL ONLY).

### 7.3 Follow-ups (not tonight)
- **The attract sequence is a heavy 3D scene that needs no figures.** Route: A, A, then about 60 s with no input on the 220/534 screen. Heavy frames start ~170 s after the first frame (5-8k draws, 0.8-1.0M vertices); `b-gate-menus-long.txt` reaches it. It could serve as a perf scene (Agent 8; timing only on the user's desktop, and only with Agent 1's OK). The 1-5 s frames on first view would need a profile. Now task #16: section 7.4.
- Find out why bgate-a and the dry run did not leave the 220/534 screen within 62-66 s. Possible causes: a timer that Toy Pad traffic or a load resets, or one that counts from a different event. A route that waits for the attract sequence needs a margin of 90 s or more.
- A named-pipe tee for `--perf_log_csv=\\.\pipe\...` would give live scenes. Risk: the game blocks if the reader stalls.
- A `--fake_lock_perf` option in the fake exe, to self-test the locked-perf.csv path.
- Toy Pad tag scripts, only with Agent 1's OK.

### 7.4 Attract scene benchmark prep (task #16; all data FUNCTIONAL ONLY)
Prep for a timed attract-scene benchmark in a later user window (not window 4). Every number below comes from hidden-desktop agent runs, so none of it is timing.

**Tools.**
- `harness/routes/attract-long.txt`:
  - the presses: START, A, A, at the same times as `b-gate-menus.txt` steps 1-11. The last press is the A that opens 220/534, ~69 s after the first frame;
  - then no input, with a mark every 10 s up to 380 s, and `stop` at ~472 s after launch;
  - DryRun on `devoff3-bin`: OK (03:39).
- `harness/attract-report.py RUN [RUN…]` (stdlib, one thread). It reports the idle exit, A0 and H0, landmarks, shots, stalls, steady stretches, the scored window with its flags, a cross-run table, and `--json`. The defaults are the proposed window.
- attract-report.py tests (03:45-03:58), on the four session-3 runs:
  - both tie-break runs give a valid window;
  - bgate-a gives `no_exit`, and bgate-b gives `no_anchor` (that run ended 5 s after A0);
  - no arguments, or a missing run, gives exit 2.
- Re-tested 04:38 after the window change (below): the same results on the same four runs. The tie-break windows match the old tool run with `--offset 6.5 --seconds 11 --peak-draws 9800`. `--sub none` drops the sub-window, and the JSON has `args.sub` = [18.2, 2.3] and `window.stall_ms` = 250.
- Its idle values are within 0.2 s of Agent 9's: 18.84 / 18.67 / 20.28 s, against 18.88 / 18.87 / 20.35 s. It takes the release as the row time minus the 0.6 s press gap.
- **Native builds** (found 04:00 in Agent 8's `build/agent8/runs/0256-native3`):
  - perf.csv's `draw_calls` and `vertices_processed` are 0 on every row. The draw calls are only in the native frame metrics (`frames.csv` from run-game, `native-frames.csv` from Agent 8's runner), which have no vertex column;
  - the metrics' `frame` column is the 1-based perf.csv row and starts at 2. `interval_ms` against perf.csv frame time gives r = 0.999 at that offset, and 0.20 if row i is taken as row i;
  - native draw counts are on another scale: that boot has 0/1 draws for ~30 s, then 8 at the title (OFF: 218-226). So the OFF anchors (218/222, 2823/366575) don't apply;
  - `route-report.ps1` now falls back to those files, with scenes shown as `n<draws>`. Tests, 04:05-04:11:
    - a devoff2 run with perf.csv draws zeroed and a native-format `frames.csv` gives the original's draws at all 55 steps;
    - Agent 8's native files give n0/n1, then n8 from 30 s;
    - on the real nativeB route pair (05:11, `runs/20261122-045945-bgate-long-native3d`, `runs/20261122-050343-bgate-long-nativeB`): n0/n1 for 30 s, n8 at the title, n2 in the menus, then n0, n41, n58-60 and the attract at n1k-5k in both. native3d had a 5 s `STUCK-LOCK` on critical section 0x84959edc at launch + 200.9 s in the attract (perf frozen ~10 s, minidump, the game recovered); nativeB was clean (Agent 10: PASS);
    - the original run's report is unchanged apart from the new `scene source` line;
  - `attract-report.py` reads perf.csv only. Native arms would need frames.csv input and their own anchors, from one native attract-long run.

**Item 2: the sequence against A0 and H0.**
- A0 = the first 218/222 frame after the fade.
- H0 = the first 2823/366575 frame after A0.
- Times below are frame start times, from the tie-break runs.

| event | devoff2 | devoffB |
|---|---|---|
| the 218/222 load lasts | 7.06 s | 10.44 s |
| first 3D frame 625/780 (a stall) | A0 + 7.06: 1.90 s, pm 21, tm 10 | A0 + 10.4: 0.62 s |
| load frame (768/5292 in devoff2, 219/226 in devoffB) | A0 + 12.12: 1.30 s, pm 23 | A0 + 17.17: 1.31 s, pm 0 |
| 788/31613 | A0 + 29.99 | A0 + 36.37 |
| **H0 2823/366575** | **A0 + 35.86** | **A0 + 42.22** |
| 8019/1043795 · 5265/773966 · 4385/821295 · 6353/1014219 · 5194/879213 | H0 + 5.45 · 9.83 · 12.86 · 15.19 · 16.51 | H0 + 5.38 · 9.87 · 12.92 · 15.27 · 16.66 |
| 12390/1397564 (devoffB 12393/1412288): stall | H0 + 20.93: 5.61 s, pm 67 | H0 + 21.84: 4.09 s, pm 67 |

**Order and timing.**
- **Same order in both builds, and after H0 the same timing within 0.15 s for 17 s** (19 shots compared): from H0 on, the sequence runs on a clock.
- Before H0, devoffB falls 6.4 s behind. The causes are the longer load and the slower first-view frames (594/2813 lasted 3.09 s against 1.70 s), so the window has to be anchored on H0, not on A0.
- Slow frames hold the clock back: in the slow devoffB run, frames of 290-480 ms from H0 + 17 s pushed the 12.4k shot 0.9 s later.

**Where the 1-5 s frames fall.** Every one of them comes with first-view pipeline misses, except 2520/2522, which has none (streaming?):
- A0 + 7-10 s: the first 3D frame;
- A0 + 12-17 s: the load frame;
- H0 + 20.9-21.8 s: the 12.4k shot (pm 67);
- H0 + 26-37 s: 12398 (1.0 s, tm 33), 2520/2522 (2.4 / 1.6 s, pm 0), 1491/315180 (2.5 s), 5058 (1.2 s, pm 15) and 5118 (2.4 s, pm 31).

**H0 to H0 + 20.9 s has no frame of 1 s or longer.** It has 7 pipeline misses, at H0 + 0.36 (1), + 3.38 (1), + 4.40 (4) and + 12.80 (1). The slowest frame there is 730 ms (devoff2, H0 + 4.63, tm 2).

**First proposal (03:58): H0 + 5.5 s for 15 s.** Content 8019/1043795 → 5620/922665, median 5.3k draws, peak 9.9k; it ends 0.4 s before the 12.4k stall. Functional values: devoff2 252 rows, median 56.2 ms, p95 102.9 ms, max 151.9 ms; devoffB 193 rows, 68.1 / 158.0 / 478.8 ms.

**Revised window (04:30): H0 + 6.5 s for 11 s** (now the `attract-report.py` defaults), after Agent 6's task #18 (`perf-notes/agent6-attract-stalls.md` section 8):
- The 1-5 s frames are pipeline creation on first use. Every run dir starts with an empty Xenos shader storage (`<run>/user`), so they come back in every run, at fixed points around H0: -29…-32 s, -24…-25 s, -1.9 and -1.0 s, +4.4…+5.4 s, +20.9/+21.8 s (the 12.4k shot) and +26…+37 s.
- **Start edge:** the last compile stall ends at H0 + 5.36 s (devoff2: a 730 ms frame from H0 + 4.63), only 0.14 s before the first proposal's start, and the attract timing moves 0.3-0.9 s between runs. So the window starts at H0 + 6.5 s, and a frame of 250 ms or more excludes the run (a 1 s limit would miss that 730 ms frame).
- **End edge:** the heavy segment (9.8k draws or more) starts at H0 + 18.16 s (devoff2) / 18.51 s (devoffB). All five of devoffB's frames over 250 ms (289-479 ms, no pipeline misses) are in it, against 107-152 ms in devoff2: it is throughput, not compiling. So the window ends at H0 + 17.5 s, and a frame with 9800 draws or more excludes the run (its heavy segment came early).
- H0 + 18.2 s for 2.3 s is reported as a heavy sub-window, info only: 7-23 frames are too few to score. Nothing after H0 + 20.9 s is used in cold runs.
- Functional values (tie-break runs; 11.0 s each, no frame of 250 ms or more, peak 8068 draws, pm 1, tm 2):

  | run | rows | median | p95 | p99 | max |
  |---|---|---|---|---|---|
  | devoff2 | 207 | 54.19 ms | 75.11 ms | 84.21 ms | 102.90 ms |
  | devoffB | 168 | 64.45 ms | 103.42 ms | 152.39 ms | 226.45 ms |

  Sub-window: devoff2 23 frames, median 98.0 ms; devoffB 7 frames, median 330 ms.
- The devoffB tie-break run does not show a B cost:
  - from ~H0 + 10 s it got slower: 5271 at 74.6 ms against 50.3 ms, and 5194 at 115 ms against 58 ms;
  - its H0 + 1-3 s shots were faster, at 31 ms against 41-47 ms;
  - it ran the menu at 46.8 fps, against 58.9 fps for devoffB in pair 1;
  - so the cause is the machine state, and these runs can't tell more (no gpu.csv or system log, hidden desktop).

**attract-long results (05:12 devoff3, 05:20 devoffB; Agent 8's slot; FUNCTIONAL ONLY).** Runs `runs/20261122-051201-attract-devoff3` and `runs/20261122-052024-attract-devoffB`; reports in `build/agent3/logs/`: `attract-long.txt` (+ `.json`), `route-attract-devoff3.txt`, `route-attract-devoffB.txt`, `attract-long-passes.txt`. The warm run that followed is in item 6.
- **The machine was saturated** during both runs and the warm run: 97-100% busy, with the CPU at or below its 1.7 GHz base clock (% Processor Performance 65-98%).
  - Defender (`msmpeng`) used 1.2-4.8 cores; NVIDIA FrameView's `PresentMon_x64` (started by `nvfvsdksvc_x64` at 17:36 the day before) used 1.0 core all the time; `dwm` used ~1.1 cores while the game ran; other agents were running recursive searches.
  - Log: `build/agent3/logs/cpu-sampler-0528.csv`, from `build/agent3/test/cpu-sampler.ps1` (read-only counters, 1 thread). Agent 1 has since stopped recursive searches while a game runs. At 05:37, with no game running, Defender still used 0.3-3 cores and PresentMon 1 core.
- **Both routes ran to the end:** 91/91 steps, 0 timeouts, exit 0 via WM_CLOSE (11.8 s / 18 s). The first frame came 18.1 / 15.0 s after launch (11.4-12.5 s in the earlier devoff runs).
- **devoffB had 4 `STUCK-LOCK` reports**, on critical section 0x84959edc: waiter lr=82A2A270, owner tid 0x17 at lr=83FAF200/83FAF188, the GPU thread on PM4 opcode 0x22 at a new read pointer each time. That is the same lock and waiter as native3d's stall, and the warm devoff3 run had one more (item 6).
  - They match devoffB's four frames of 5 s or more: 8.5 s at H0 + 16.4 s (10664 draws), 5.3 s at H0 + 63.6 s, 16.4 s at H0 + 69.5 s (13913 draws), and 5.1 s at H0 + 128.9 s. Those frames have pm 0, so they are not pipeline compiles. devoff2's 5.6 s compile frame in the tie-break run had no report.
  - One minidump (`hang-52704.dmp`); the game recovered each time. devoff3 cold had none (longest frame 3.1 s). With native3d and the warm devoff3 run, three builds have hit it, so it doesn't point at B; it comes with CPU starvation. `baseline-bin` hit it too at 06:39 (**Baseline attract run** below).
- **Idle exit:** 70.87 s (devoff3) and 69.79 s (devoffB) after the last release, 68.4 / 66.6 s after 220/534 appeared.
  - Over the six session-3 runs with this front end, the exit came at perf 132.1, 132.3, 134.7, 138.9 and 140.5 s (perf is about the time since the first frame); the sixth (bgate-a) had not left at perf 139.4 s, when it ended. The warm run left at perf 126.0 s, 55.0 s after its last release.
  - So the exit doesn't follow the last press (18.7-20.3 s after presses at perf 113-114, 55-71 s after presses at perf 69-71); it comes at perf 126-141 s, roughly a time since boot. This replaces the "19 s idle" reading as well as the frame model.
- **No loop:** one attract pass. devoff3 found the anchor once; devoffB never showed 2823/366575 (at 2.6 fps) and used the fallback anchor 2831/406639.
  - From H0 + 177 s (devoff3) / 201 s (devoffB) the game sits in a steady scene of 766-770 draws and ~111k vertices until the stop: 92 / 82 s with no frame of 250 ms or more and no pipeline miss (median 57.7 / 46.0 ms on the saturated machine).
  - A profile-read and Toypad-light sequence like the front-end exit comes just before it.
- **Order:** the shots after H0 come in the same order in all four runs. In the three with the exact anchor, 2838/516686, 8019/1043795 and 4385/821295 start within 0.36 s of devoff3.
- **Windows:** both were excluded, as designed.
  - devoff3: 71 rows, 6.35 fps, median 140 ms, 8 frames of 250 ms or more (few_rows, stall_in_window). Its light scenes were normal (menu 56.9 fps), but the heavy ones ran 2-3x slower than in the tie-break runs, with the GPU at 29% util and 900 MHz: CPU-starved.
  - devoffB: 48 rows, 2.61 fps, an 8.5 s frame (few_rows, stall_in_window, window_reaches_heavy; info anchor_fallback).

**Design (for Agent 8; updated 05:50 with the attract-long and warm runs).**
1. **Window and flags** (the attract-report.py defaults):
   - start = H0 + 6.5 s, length = 11 s of frame time;
   - excluding flags:
     - few_rows: under 110 rows (10 fps);
     - light_window: median draws under 2000;
     - stall_in_window: a frame of 250 ms or more (`--window-stall-ms`);
     - window_reaches_heavy: a frame with 9800 draws or more (`--peak-draws`), i.e. the heavy segment moved into the window;
     - window_before_floor: the window starts less than 60 s after the first frame. It started at perf ~171-191 s in the five session-3 runs with an attract (the warm run included), so this never fires;
     - no_exit, no_anchor, short_window;
   - info flags:
     - pm or tm in the window (expect pm 1, tm 2; more means a different cache state);
     - content_may_lag: a window median above 100 ms;
     - anchor_fallback;
   - info block: the heavy sub-window, H0 + 18.2 s for 2.3 s (`--sub`; `--sub none` drops it), with its own pm/tm and a `contaminated` mark (a frame of 1 s or more, or 12k draws or more).
2. **Score:**
   - command: `python harness\attract-report.py <runs…> --label timing --json <out>`;
   - per run: median, p95 and p99 ms, and fps over the 11 s;
   - per arm: the median of its runs' medians (and p95s), with the min-max of the run medians as the spread;
   - runs with an excluding flag are dropped.
3. **Runner** (`bench/agent8/run/run-timing.ps1`, Agent 8's file):
   - It already launches from a mirrored run dir and has `-Cvar 'input_backend=xinput'` and `-Env 'AGENT3_VPAD=<run>\vpad-state.bin'`.
   - What's missing is a launch-time `-InputScript`. It is ported from `run-game.ps1` (the block under `# -InputScript`, `[Agent3Input]::Go` right after launch, `Halt`/`Finish` at the close; ~15 lines) and does this:
     - parse the route with `[Agent3Input]::Start(route, <run>\vpad-state.bin, <run>\input.csv, <run>\game.log, <run>\perf.csv)`;
     - copy `build\agent3\vpad\xinput1_4.dll` into the run dir, and refuse if the BinDir has its own copy;
     - start the script at launch;
     - write the `Finish()` block into `run.json`.
   - Route: attract-long's presses with no `stop`; the runner closes the game.
   - Runner window: `-WarmupFrom firstframe -Warmup 150 -Seconds 80 -MinWindowAfterFirstFrame 60 -SysCsv`. That window (first frame + 150-230 s) contains the scored window, which started at perf 171-191 s in the five session-3 runs with an attract (the exit came at perf 126-141 s and H0 37-46 s later; perf time stayed within ~2 s of the wall time since the first frame), leaving ~20 s or more at each end. The sys flags still apply, and the pad makes no system input. (Until 05:45 this said first frame + 110-200 s, from a wrong reading of the tie-break runs.)
   - A warm-storage arm (item 6) would also need run-game's `-SeedXenos` copy step in the runner (~15 lines).
4. **Estimates:**
   - one run ≈ 12-18 s to the first frame (devoff builds: launch + 11.4-18.1 s; `baseline-bin` 13.0, 35.0 and 16.0 s in session 3) + 230 s + the close (1-35 s) ≈ 4.5-5 min with the runner's overhead;
   - 3 arms × 4 repeats = 12 runs ≈ 55-60 min (42-45 min with 3 repeats), plus re-runs for excluded runs;
   - an unscored first run only helps after a driver or GPU-path change (for example the first run of a new native build). The NVIDIA driver cache is shared across run dirs and already warm, and nothing but `-SeedXenos` can warm the per-run Xenos storage (Agent 6 section 8).
5. **Risks:**
   - **Idle exit:** it came at perf 126-141 s in 6 of 7 session-3 runs (69.8 / 70.9 s after the last press in the attract-long pair, perf 126.0 s in the warm run); bgate-a ended at perf 139.4 s before it. attract-long waits 380 s, so a late exit only costs time; a run with no exit is flagged `no_exit`.
   - **Machine load:** the 05:12-05:35 runs show what a busy machine does: Defender scanning (1-5 cores), NVIDIA FrameView's PresentMon (1 core, always on), agent searches or builds. Light scenes kept close to their earlier frame rates, but the heavy attract ran 2-3x slower, with 5-16 s frames, and all three attract windows were excluded. Before each timed run: no agent activity, Defender idle (under ~0.2 cores for 30 s), total CPU under ~25% without the game; record `cpu-sampler.ps1` (or the runner's `-SysCsv`) next to each run. PresentMon is the user's NVIDIA App; note it, don't touch it.
   - **Stuck-lock stalls:** on a slow machine, frames of 5 s or more in the attract come with `STUCK-LOCK` on 0x84959edc and a minidump (native3d 05:03, devoffB 05:24, the warm devoff3 run 05:32, and `baseline-bin` 06:39, so it predates the sprint). The game recovers; runstats calls such runs `RECOVERED HANG` (**Harness fixes** below), route-report fails them, and attract-report's 250 ms flag excludes them if they fall in the window.
   - **The pad DLL on the user's desktop:** it is test tooling, copied into run dirs only. In those runs the game ignores a real pad, and nothing is installed system-wide.
   - **First-view stalls:** they recur in every run at fixed points around H0, because each run dir starts with an empty Xenos storage. The window sits between the last one before it (ends H0 + 5.36 s) and the heavy segment (from H0 + 18.2 s), with ~1.1 s of margin at the start and ~0.7 s at the end. The 250 ms and heavy flags catch a run whose timing moved more than that.
   - **The content clock:** see content_may_lag.
   - **Native builds:** perf.csv has no draw counts there, and native draw counts are on another scale (title: 8 against 226), so attract-report can't place A0/H0 on them yet. Before any native arm: add frames.csv input to attract-report.py, run attract-long once on a native build, and pick native anchors from it.
6. **Warm-storage arm** (Agent 6 section 7; optional):
   - `run-game.ps1 -SeedXenos build\agent3\seed\devoff2-214` copies the devoff2 tie-break run's storage into the run's `user\cache\shaders\shareable` before the launch: `5752084B.xsh` (160,232 B, sha256 `EEFC75E4…`) and `5752084B.rtv.d3d12.xpso` (15,420 B = 214 pipelines, sha256 `4D4F514D…`). The seed files are read-only, and every run gets its own copies.
   - Check run (functional; ran 05:29 in Agent 8's slot, `runs/20261122-052901-attract-devoff3-warm`): `...\run-game.ps1 -BinDir build\agent2\devoff3-bin -Seconds 360 -GpuLog -Tag attract-devoff3-warm -InputScript harness\routes\attract-long.txt -SeedXenos build\agent3\seed\devoff2-214`.
   - Result (FUNCTIONAL ONLY, on the saturated machine; `build/agent3/logs/attract-warm.txt` (+ `.json`), `attract-warm-passes.txt`, `route-attract-devoff3-warm.txt`):
     - the storage loaded: "Translated 229 shaders from the storage in 85 ms" and "Created 214 graphics pipelines … from the storage in 2016 ms" (also in `run.json` `seed_xenos.storage_log`). The copies matched the seed's sha256, and the seed dir was unchanged after the run (Agent 8 checked names, sizes, mtimes, read-only flags and sha256);
     - the `.xpso` grew 15,420 → 19,452 B (214 → 270 pipelines), the `.xsh` 160,232 → 210,512 B;
     - pipeline misses: 56 in the whole run against 264 in the cold devoff3 run. pm was 0 in the window, in the heavy sub-window, in every stall, and in every shot up to H0 + 80 s; later misses came at H0 + 80 s (8), +110 (4), +140 (7), +160 (10) and +200 (21);
     - the stalls stayed: a 10.05 s frame at H0 + 3.1 s (6260 draws), 2.0-3.5 s frames at H0 + 20.6, 23.7, 26.5, 29.3 and 33.1 s, and one `STUCK-LOCK` on 0x84959edc at 05:32:12 (owner tid 0x17 at lr=83FBF868) with a minidump (`hang-69196.dmp`). All had pm 0, so they are CPU starvation, not compiles;
     - window excluded: 32 rows, 2.49 fps, 12 frames of 250 ms or more, tm 24 (few_rows, stall_in_window; info anchor_fallback: H0 from 2172/430537 at perf 164.4 s);
     - the exit came at perf 126.0 s (55.0 s after the last release), 6-14 s earlier than in the cold runs, cause unknown; the first frame came 18.0 s after launch;
     - route-report exit 1 for the dump and hang lines, plus "script 63/91 halted": `-Seconds 360` ends the run before attract-long's stop (the route needs ~475 s), so a re-run needs `-Seconds 540`;
     - so the warm storage removes the compile misses, but whether H0 + 5.5…+40 s is stall-free still needs a run on a quiet machine.
   - What to check:
     - game.log "Translated N shaders from the storage" and "Created N graphics pipelines … from the storage" with N ≈ 214 (also in `run.json` `seed_xenos.storage_log`);
     - pm ≈ 0 in the attract;
     - how much the `.xpso` grew (72 B per new pipeline);
     - whether H0 + 5.5…+40 s has no stall. Then a warm arm could score the 12.4k-draw scenes too.
   - A warm arm has to be anchored on H0 (warm boots take longer, because the storage loads at boot) and interleaved with the cold arm (A B A B).
   - Tests (04:42-04:43):
     - a DryRun on `devoff3-bin` made identical, writable copies and left the seed unchanged;
     - a missing seed dir, an empty one, and an existing copy are refused (exit 2);
     - the post-run code, taken from the script's AST and run on mock state, records an `.xpso` grown by 3 pipelines (15,420 → 15,636 B) and the storage log lines;
     - a DryRun without the option has no `seed_xenos` and no cache dir.

**Baseline attract run for the stuck lock (06:35; Agent 8's slot, priority 1 of Agent 1's 06:31-07:15 plan; FUNCTIONAL ONLY).** Run `runs/20261122-063542-attract-base1`: `build/baseline-bin` with `attract-long.txt`; report `build/agent3/logs/base25-attract-base1.txt`.
- The route ran to the end: 91/91 steps, 0 timeouts, exit 0 via WM_CLOSE in 1.74 s. The first frame came 16.0 s after launch, and the game polled the pad 13,324 times (36 with input).
- **One `STUCK-LOCK` on 0x84959edc**, at 06:39:22.996 (launch + 219.0 s, in the attract):
  - owner: guest thread object 0x30111018, tid 0x17 at lr=83FB09F0 (callers 83FB0948 <- 82BDD028 <- 82BDC918 <- 82BAEA7C);
  - waiter: 0x6, with the devoffB/devoff3 chain lr=82A2A270 <- 82AED6BC <- 82B7132C <- 82FB01A0 <- 82B7995C <- 82AB2108 <- 82FEBDE0;
  - minidump `hang-60748.dmp` at launch + 222.6 s; the game recovered. It matches the 8,581 ms frame from first frame + 200.1 s (the run has 18 frames of 1 s or more).
- **So the stuck lock predates the sprint.** Agent 8 skipped the second run, since Agent 6 found one enough.
- Machine (`build/agent3/logs/cpu-sampler-0554.csv`): 97.9% busy on average; Defender 1.33 cores mean / 2.95 max, PresentMon 1.0, dwm 1.1, the game 2.2.
- Idle exit: 220/540 at perf 124.71 s, 55.64 s after the last release; H0 at A0 + 39.95 s.
- **The quiet re-run of the window (priority 3) was not run.** Agent 8's quiet gate never passed: 15 tries from 06:25 to 06:52, with Defender at 1.8-3.7 cores each time and no game running (the limit is 0.2). No game was started.

**Harness fixes, applied 07:02** (Agent 1's OK at 06:28; applied after Agent 8's last run ended at 07:00:02). Both were applied with `git apply` to the working files (harness/ is not tracked by git). Both keep their CRLF line ends, and their content is identical to the tested LF copies in `build/agent3/patches/`.
- `harness/runstats.py` ← `runstats-recovered-hang.patch` (551 → 584 lines; sha256 5B889EFF… → AE6C8B0C…; the LF copy `runstats.py.patched` is 0AF19AD7…):
  - A run gets `result RECOVERED HANG (STUCK-LOCK + dump)` instead of `CRASHED`, plus a `STUCK-LOCK episodes: N; first at T s: …` line, when it meets all of these: the harness closed it with exit code 0; there is no crash event or WER report; every dump is this game's `hang-<pid>.dmp`; game.log has a `STUCK-LOCK` line.
  - Every other case keeps its old verdict. Exit codes don't change: run-game.ps1 still exits 1 for any dump, and route-report.ps1 still fails 'no crash'.
  - Tests (07:05): `test_runstats_applied.py` compares the patch reverse-applied to a copy (orig) with the applied file (new). Result: 0 failures in 37 checks over 5 real runs and 14 mock cases.
    - devoffB 052024 (4 episodes), native3d 045945 and devoff3-warm 052901 are now RECOVERED HANG;
    - nativeB 050343 and devoff3 051201 stay RUNNING with identical text;
    - no run dir changed;
    - `python harness\runstats.py runs\20261122-063542-attract-base1` gives RECOVERED HANG with 1 episode, exit 0.
- `harness/vpad/vpadhost.cs` ← `vpadhost-reset.patch` (515 → 544 lines; sha256 39AA9C46… → 5D929041…; the LF copy `vpadhost.cs.patched` is 2015C374…):
  - `[Agent3Input]::Start` first calls the new `ResetRun()`. It stops a step thread that is still alive (5 s limit), closes the files of a run that never got `Finish()`, and clears every per-run field.
  - So one PowerShell process can run several input scripts in turn (Agent 8's run-matrix.ps1 calls run-timing.ps1 in-process). Before, the second `Start()` ran no steps and reported the first run's counters.
  - Test (07:04): `build/agent3/test/rtpatch-hostB.ps1 -VpadSrc harness\vpad\vpadhost.cs -Label applied`.
    - Runs 1 and 2 were the same: 5/7 steps, last 'halted', stopped by the script, 0 timeouts, 9 input.csv lines.
    - The patched runner, in the same process, then passed its input checks and stopped at the RAM check (exit 3 with `-MinFreeRamGB 999`; nothing was created).
- `harness/legodimensions.toml` was not touched (sha256 B763DABB…; W4b's common.ps1:75 copies it).

### 7.5 1b exit split: host-side check (07:40; read-only; all data FUNCTIONAL ONLY)

Question (Agent 1): nativeB leaves the front end ~12 s earlier than native3d in both run orders.
Result: no host-side cause. I agree with Agent 10's (b) verdict (not a codegen change): the item stays OPEN and goes to S4. No rollback; it is not a fail item.

- **Exit timing (route logs).** Exit = the INSTALL batch of the next front-end load; the fade starts ~60 frames before it.
  - The rev pair reaches the menu INSTALL batch at the same time (72.24 / 72.23 s after launch), then splits. INSTALL to exit: native3d 59.59 / 61.34 s, nativeB 46.50 / 49.70 s (ratio 0.78-0.81).
  - Launch to exit: native3d 130.69 / 133.57 s, nativeB 124.24 / 121.94 s, devoffB 141.18 / 144.51 s, devoff2 143.05 s. 2 of 3 devoff2 runs had not left 62.6 / 65.8 s after E534.
  - Order: nativeB < native3d < devoffB <= devoff2, the same order as guest CPU throughput.
- **Models that fail:** wall time, frame count, D3D callback count, clamped dt (16.7-250 ms caps), last press + N, process CPU-seconds, guest thread start/end (none between perf 40 and 150 s in any run), memory growth, the Toy Pad B1/B3 exchange.
- **Every host clock the guest can read is wall time, identical in OFF, native3d and nativeB:**
  - mftb -> QueryGuestTickCount (50 MHz, scale 1.0);
  - KeQuerySystemTime;
  - KeTimeStampBundle+16 TickCount (1 ms host timer; +0 InterruptTime and +8 SystemTime stay 0);
  - audio buffers, consumed by the real WASAPI endpoint at 48 kHz;
  - KeQueryInterruptTime and xam GetTickCount are stubs.
- **What native mode paces by progress instead (the same for native3d and nativeB):**
  - no vblank interrupts: OnPreSetup resets config.graphics, so there is no GraphicsSystem; interrupt_dispatches is 0 in every native perf.csv;
  - SynchronizeToPresentationInterval (sub_83FB2F20) is a no-op;
  - BlockOnFence / BlockUntilIdle drain all host GPU work;
  - InsertCallback callbacks run when the guest next enters a polling hook after the host GPU has finished;
  - KickOff returns the constant dev+0x6000;
  - the native device (0x6080 bytes) is zeroed and has no ring, so dev+11024 stays 0 (static read, not checked at run time);
  - presents are paced only by `native_fps_limit` (240) and GPU back-pressure (`gpu_native/device.cpp` LimitFrameRate).
- **sub_83FAF088** is a D3D wait-record init (device, *(dev+11024), a PCR field, mftb low word), not a frame clock.
  - Callers: 83FB33E0 (Swap, hooked in native), 83FBF1C8, 83FBF260, 83FBF7D0, 83FCA768, 83FCAD20.
  - Full list: `build/agent3/logs/fe-11024.txt`.
- **Timer gate (Agent 10).** sub_82FD4868 arms only if sub_82FB9020 returns 1:
  - byte 0x848E2EA2 == 0 (via sub_82A75FD8);
  - and, when [[0x849F5640]+180] == 3, bits 3 and 6 of the guest bitset at 0x849004EC are clear. sub_82A832F8 is a plain bit test; its r3 argument is unused.
  - Event 5 counts only while [app]+2288 == 0.
  - No host code in rexlego/src references any of these addresses, so they are guest state only.
- **Model (unverified):** a wall-time timer that counts only while guest background work is idle.
  - Less guest CPU per unit of work (B) or no GPU-emulation load (native) means less busy time and an earlier exit.
  - In OFF something else seems to dominate the busy time, so B moves the exit there by only ~2 s.
- **S4:** find the writers of 0x848E2EA2, of the 0x849004EC bits 3/6 and of [app]+2288. Then run one instrumented arm-time pair: native3d vs nativeB, `harness/routes/b-gate-menus-long.txt`, same cvars. The harness side is ready; nothing runs before window 4.


## 8. S4a functional checks (task #5, board run 2, 2026-11-22 13:05-15:00; ALL FUNCTIONAL ONLY, hidden desktop, never timed)

Bins: Agent 2's devoff4 (S3d + #7 u diag, #8 P2, #5 fix (i), #38 precise wait, all OFF; #32 warm-boot fix always on) and native4 (the same + #2 miss cache, OFF).
Game 08933a7, SDK c5fe668. I was the only agent launching games until 14:50 (Agent 1 moved the times at 13:56: last launch 14:45, games closed 14:50, notes until 15:00; was 14:15/14:20).

### 8.1 Tools (all in `build/agent3/s4a/`, nothing in `harness/` changed)

- `s4a-queue.ps1` + `queue.jsonl`: sequential runner around `harness/run-game.ps1` (standard flags come from run-game). One game at a time; no launch at/after `-LastLaunch` (14:45:00 since 14:06; was 14:15:00) or when now + est passes `-GamesClosed` (14:49:30; recorded as skipped in `queue-state.jsonl`); a `STOP` file ends it; entries wait for `ready-devoff4` / `ready-native4` markers (made when Agent 2 reported each bin). Logs: `logs/<id>.run-game.txt`, `logs/<id>.attach.out.txt`. **Fix 14:07:** the run-game call now runs under `$ErrorActionPreference = 'Continue'`: native builds print to stderr, the game inherits run-game's stderr, and under 'Stop' the first such line killed run-game (r5 attempt 1, below).
- `attach.ps1`: sidecar per run. Finds the new `legodimensions` under `build/agent3/runs`, starts Agent 8's `bench/agent8/run/drivers/sys-csv.ps1` read-only (only while its `LdSys-b452d258.dll` is cached) -> `<run>/sys.csv`, and samples every thread every ~2 s with `S4aThreads.cs` (toolhelp + GetThreadTimes/QueryThreadCycleTime/GetThreadDescription) -> `<run>/threads-s4a.csv` (`t_s,epoch_s,tid,name,cpu_ms,kernel_ms,user_ms,cycles`).
- `s4a_check.py --cand <run> --base <run> [--base ...] [--allow-new REGEX] [--tq-ref <run>]` -> `checks/<run>.{txt,json}` in ~2 s: run.json (exit, dumps, close, cvars/args/env, steps, seed storage lines), summary.json, greps over `game*.log` (S4 families, `PhysicalHeap::Protect failed`, `STUCK-LOCK`, dumps, storage lines and the gap after "Initializing shader storage"), logdiff (`build/agent10/bgate/logdiff.py`, warning level + NEW keys at info level, Toypad challenge lines split out), [error] counts vs the first base, stable scenes (>= 10 identical frames, >= 2 s; OFF perf.csv draws/vertices, native frames.csv draws), the scene at each route mark (input.csv perf_bytes -> median of the last 30 perf rows, the route-report.ps1 method without its 4 min cost), thread CPU % of one core per name (first frame + 20 s .. last sample - 10 s), TimerQueue tick check (cycles must rise in every sample step), sys.csv slow state.
- `slowstate.ps1`: adapter for `bench/agent11/timerq_slowstate.ps1` (unchanged): copies each run's sys.csv into `slowstate/<yyyyMMdd-HHmm>/runs/<run>/` with a run.json holding `ff_signal_epoch_s` (= started_epoch_s + first_frame_s) and `env_set`, then runs the script.
- Route for every menu run: `harness/routes/b-gate-menus-long.txt` (superset of `b-gate-menus.txt`: boot -> title -> start -> menu walk -> back -> idle to attract; same route as the native3d references).

### 8.2 References

- devoff (OFF and ON runs): fresh `runs/20261122-131206-s4a-ref-devoff3` (devoff3, same route/flags; 13:12): exit 0, WM_CLOSE 1.22 s, 54/54 steps, 0 errors/142 warnings; vs devoff2 031756 NEW 0 / MORE 0 / GONE 4 (all Toypad) / FLAG 0; no slow state. ON runs are also compared with the devoff4 OFF run (r1).
- native4: `runs/20261122-055439-bgate-rev-native3d` (clean; `045945-bgate-long-native3d` had a STUCK-LOCK + hang dump, so it is the second base only).
- #32 U2 (Agent 6's devoff3 warm attract run): `runs/20261122-131746-s102-r2-warm-devoff3`: exit 0, WM_CLOSE 2.87 s, 57/91 steps (stopped at 360 s as planned), 0 errors; "Translated 229 shaders from the storage in 25 ms", "Created 214 graphics pipelines ... from the storage in 1521 ms"; seed grew 214 -> 282 pipelines; slow state from 199 s (43 % of samples; Agent 11's script agrees).

### 8.3 Results

Check texts: `build/agent3/s4a/checks/<run>.txt` (auto-run by `postcheck.ps1` as each run ends). Front-end scenes (draws/vertices): 218/222 boot, 226/1022 title, 220/528 + 220/534 menus, 219/226 loading.

- **r1 devoff4 OFF, cold** `runs/20261122-133333-s4a-r1-off-devoff4` (13:33): exit 0, WM_CLOSE 2.35 s, 54/54 steps, no dumps, 0 errors / 142 warnings (ref: 0 / 142). S4 lines 0. logdiff vs ref-devoff3 NEW 0 / MORE 0 / GONE 4 (Toypad) / FLAG 0. Same front-end scenes; marks first-frame .. up-2 identical (9/9), later marks differ by the known idle-exit timing. #32 run 1: no "from the storage" lines (cold), 9 `D3D12 Pipelines` threads. TimerQueue 37.6 % of a core (spin), ticks rise in 108/108 steps. No slow state. **PASS.**
- **r2 devoff4 u diag ON** `runs/20261122-133730-s4a-udiag` (13:37; Agent 12's spec: -Seconds 330 -StatsWarmup 20, no input, `shared_memory_upload_hash_log=true;slow_frame_log_ms=1;framerate_limit=0`): exit 0, WM_CLOSE 1.50 s, no dumps, first frame 9 s. 9 log files (game.8.log has frame 1; rotation at 5 MB, nothing lost). 75013 `S4 upload hash` lines / 75014 perf.csv rows (1.000 per frame), 74714 `slow frame #` lines (0.996 per frame). [error] 0 (r1 0), [warning] 40 = the 5 standard boot families (34 INSTALL DAT NtCreateFile, 2 XFileFsDeviceInformation stub, 2 IoDismountVolumeByFileHandle stub, 1 INSTALL HDR, 1 XamBackgroundDownloadSetMode). `logdiff.py` reads only game.log, so I also ran it on all 9 files joined (`build/agent3/s4a/tmp/r2-alllogs`): vs r1 NEW 0 / MORE 0 / FLAG 0 (GONE = r1's route-only Toypad lines). Title 226/1022 for 294 s (no input, as specified). TimerQueue 39 %. Slow state from 107 s (16.5 %). Run dir sent to Agent 12 (13:47) for `s4_uhash.py` / `s4_slowframe.py`. **PASS (functional).**
- **r3 devoff4 P2 ON** `runs/20261122-134346-s4a-r3-p2-devoff4` (13:43; `shared_memory_single_hold_rearm=true`): exit 0, WM_CLOSE 2.27 s, 54/54 steps, no dumps, 0 errors / 142 warnings. logdiff vs r1 + ref-devoff3 NEW 0 / MORE 0 / GONE 0 / FLAG 0. Same scenes (none missing or extra); marks first-frame .. up-2 identical. Slow state only from 200 s (7.8 %, the idle tail). Fallback count: pending (no counter in S4a). **PASS.**
- **r4 devoff4 precise wait ON** `runs/20261122-134754-s4a-r4-precise-devoff4` (13:47; `timer_queue_precise_wait=true`; Agent 11's spec `build/agent11/s4a/AGENT3-SPEC.md`): exit 0, WM_CLOSE 3.96 s, 54/54 steps, no dumps, 0 errors / 142 warnings. Proof line: exactly 1 `[info] TimerQueue: precise wait (timer_queue_precise_wait)`, 6.3 s before the first frame (r1: 0). logdiff vs r1 NEW 0 / MORE 0 / GONE 4 (Toypad) / FLAG 0; the only non-Toypad NEW info key is the proof line. Ticks: TimerQueue cycles rise in 97/97 sample steps. Same scenes; marks first-frame .. up-2 identical. **TimerQueue thread 1.25 % of one core vs r1 37.65 %** (bench: 1.9 % vs 30.4 %). Slow state from 182 s (14 %, idle tail). **PASS (functional; CPU drop is not a timing number).** Sent to Agent 11 for the verdict.

- **r5 native4 OFF, attempt 1** `runs/20261122-135155-s4a-r5-off-native4` (13:51): **INCONCLUSIVE: harness fault, not the game.** About 14 s after launch native4 prints `Plume D3D12 command state cache: disabled` to stderr. The game inherits run-game's stderr, and my runner called run-game with `*>` under `$ErrorActionPreference = 'Stop'`, so PowerShell turned that line into a terminating NativeCommandError and killed run-game (PID 2636) at ~14 s. Signs: samples.csv stops at 14 s; input.csv has only the start line, so no route step ran and no input was sent; no run.json; no error text in `logs/r5-fail1.run-game.txt`; no crash event. The game kept running orphaned at the title for 14 min with no crash (frames.csv at ~100 fps, 8 draws/frame; perf.csv grew to 3.2 MB). My earlier "perf.csv is 0 B" reading was only a stale directory size. The runner was stuck in the pipe read (the orphan held the inherited pipe) until I killed the game at 14:06:34; WM_CLOSE can't reach it from another desktop; game exit -1. The runner was fixed at 14:07 (8.1) and r5 runs again after a12at.
- **a12at devoff4 u diag ON, attract** `runs/20261122-140637-s4a-udiag-attract` (14:06). Agent 12's attract spec: `harness/routes/attract-long.txt`, -Seconds 420 -StatsWarmup 20, the same u-diag cvars as r2.
  - Exit 0, WM_CLOSE 2.53 s, no dumps, 79/91 steps (stopped at 420 s as planned), first frame 10.0 s.
  - 4 log files (game.3.log has frame 1). 28809 `S4 upload hash` lines for 28810 perf rows (1.000 per frame); 28704 `slow frame` lines (0.996).
  - [error] 0, [warning] 143.
  - logdiff (all 4 logs) vs r1 + r2 (all logs): NEW 1 / MORE 0 / GONE 0 / FLAG 0. The NEW line is `XNetLogonGetTitleID STUB`, the attract's line; it is also in the 05:12, 05:20, 05:29 and 06:35 attract runs on devoff3, devoffB and baseline.
  - attract-report (`checks/a12at-attract-report.txt`), perf s (perf.csv row):
    - EXIT 133.43 (21445), 65.1 s idle after the last press;
    - A0 134.43 (21595);
    - H0 175.67 (24596);
    - H0 + 150 s = 325.78 (26324);
    - last row 410.92 (28810).
  - Stalls of 1 s or more after H0: +20.95 s (pm 67, the heavy shot), +87.7, +89.5 and +114.7 s (pm 0).
  - TimerQueue 35.3 %.
  - Slow state from 216.9 s after the first frame (about H0 + 41 s), 25.9 % of rows.
  - Sent to Agent 12 at 14:16. **PASS (functional).**
- **r5 native4 OFF, cold, attempt 2** `runs/20261122-141355-s4a-r5-off-native4` (14:13).
  - Exit 0, WM_CLOSE 1.22 s, 54/54 steps, no dumps, first frame 15.0 s.
  - 0 errors / 184 warnings (native3d: 0 / 186). S4 lines 0, miss-cache lines 0.
  - logdiff vs native3d 055439: NEW 0 / MORE 0 / GONE 9 / FLAG 0. The GONE lines are 8 Toypad lines and `Native GPU: completion callback GPU wait took # ms`, a timing warning.
  - Same native scenes (frames.csv draws 2, 8, 0, 1, 59, 58, 57, 40, 41, 3649; none missing or extra).
  - Marks first-frame .. back-2 are identical (11 of 11), plus idle-30. back-3 and the other idle marks differ because of the idle-exit timing.
  - TimerQueue 30.8 %; ticks rise in 108/108 steps. No slow state.
  - The stderr line `Plume D3D12 command state cache: disabled` is now harmless; it lands in `logs/r5.run-game.txt`. **PASS.**
- **r6 native4 #2 miss cache, ON vs OFF, both arms traced** (Agent 4's `build/agent4/r2t6/miss-cache-on-smoke-spec.md`; the b-gate-menus-long route, which its §2 allows; fresh absolute trace dirs `build/agent3/s4a/trace/r6on-t` and `r6off-t`).
  - r6on `runs/20261122-141746-s4a-r6on-mc-trace-native4` (14:17; `LEGO_NATIVE_SHADER_MISS_CACHE=1` + trace): exit 0, WM_CLOSE 1.06 s, 54/54 steps, no dumps, first frame 11 s, 0 errors / 184 warnings.
  - r6off `runs/20261122-142131-s4a-r6off-trace-native4` (14:21; trace only): exit 0, WM_CLOSE 1.05 s, 54/54 steps, no dumps, first frame 10 s, 0 / 184.
  - logdiff ON vs OFF: NEW 0 / MORE 0 / GONE 11 (all Toypad) / FLAG 0. Each arm vs r5 (no trace, so only indicative): NEW 0 / MORE 0; the extra GONE are the 2 `Native geometry content cache` info lines (the trace dir turns reuse off).
  - warntypes (`logs/r6-warntypes.txt`): 184 lines / 19 types in both arms, every count equal.
  - `mc_smoke_check.py` (`logs/r6-mc_smoke_check.txt`, exit 1):
    - C1 PASS (26/26 exact warning lines); C2 SAME (draws p10/p50/p90 1/2/59 in both, max 5979);
    - C4: OFF 0 insert rows; ON 64 rows (= the probe cap), VS 0xAC449538 and PS 0xAC448F28 armed "as expected" at 1.7 s, 53 distinct keys; re-inserts: VS 0xAC449538 ×2, PS 0xAC448F28 ×2, PS 0xABB69980 ×8 (median gap 0.2 s). The cap was reached at ~150 s, so no THRASH (rule: within 60 s); no NO-ARM;
    - **C3 FAIL:** 99 (guest, stage) keys per arm, 91 common. The 8 OFF-only and 8 ON-only keys look like the same shaders at other heap addresses (`checks/r6-c3-detail.txt`, from `tmp/c3_detail.py`): VS A7E1F740 / A7E3F0F0 / A7E41410 + PS A7E3E180 / A7E3EE30 / A7E40190 / A7E41180 (OFF 178.8-190.8 s, 19 frames) ↔ VS A7E44490 / A7E45840 / A7E47800 + PS A7E43EB0 / A7E45590 / A7E46810 / A7E3F570 (ON 174.3-186.0 s, 23 frames), same rows per frame (2.00, 4.00, 3.50 vs 3.48); PS 0xAB13F250 (OFF, 128 frames at 117.7-124.8 s) ↔ PS 0xABB69980 (ON, 379 frames at 114.5-120.7 s), in exactly the frames of its partners VS 0xAC4AF3A4 / 0xAC5AFEBC and PS 0xAC4AF1C8 / 0xAC5AFDE0 (128 OFF / 379 ON).
  - Verdict: the checker says FAIL on its C3 rule, but my reading was heap relocation between runs, not a cache effect (logdiff, warntypes, C1, C2 and C4 all pass). I sent both dirs to Agent 4 at 14:33. **Agent 4's verdict (14:39): PASS.** C3 matches shaders by guest address, and the 8 + 8 heap keys pair one to one by stage, rows per frame and time window. A stale-miss replay would show an ON-only key with no OFF twin plus fewer draws, and neither is there. The 8 re-inserts of PS 0xABB69980 are real lookups after drops, the opposite of a stale replay. 128 vs 379 frames is ON running that scene faster in a traced run (a hint, not a timing). Notes for W8a: the 64-row cap fills at ~150 s with 53 keys, and heap shaders churn, so the cache gains little on them. No OFF-vs-OFF run is needed. Agent 4 may change C3 to heap-aware matching after W4b.
- **r7 devoff4 fix (i) ON** `runs/20261122-142514-s4a-r7-fixi-devoff4` (14:25; `physical_protect_hold_global_lock=true`; title + menu walk, no level load, no Toy Pad tags).
  - Exit 0, WM_CLOSE 1.46 s, 54/54 steps, no dumps, first frame 8 s, 0 errors / 142 warnings (r1: 0 / 142).
  - `PhysicalHeap::Protect failed` 0, STUCK-LOCK 0, no hang.
  - logdiff vs r1 + ref-devoff3: NEW 0 / MORE 0 / GONE 0 / FLAG 0.
  - Same front-end scenes; only r1's 4 s idle scene `790/31625` is missing, and the idle marks differ by the idle-exit timing.
  - TimerQueue 30.5 %; ticks rise in 106/106 steps. No slow state. **PASS.**
- **#32 run 4, the positive control: U4 vs F4, back to back** (Agent 6's `build/agent6/s10-2/spec.md`: `-Seconds 90 -Arg d3d12_pipeline_creation_threads=0 -SeedXenos build\agent3\seed\devoff2-214`, no input; Agent 6's read-only `s102_read.py` output is in `checks/s102-read-1.txt`).
  - U4 devoff3 `runs/20261122-142856-s102-r4-t0-devoff3` (14:28): exit 0, WM_CLOSE 0.79 s, exit line, no dumps, seed OK. Translated 229 in 23 ms, **Created 214 in 6516 ms**. Gap init → guest 7387 ms (created → guest 844 ms), not a hang suspect. First frame 19.0 s, pm 0. logdiff vs U2: NEW 0 / MORE 0 (GONE = U2's attract-route lines). devoff3-bin untouched (newest file 02:44); the seed goes into the run's own fresh user dir.
  - F4 devoff4 `runs/20261122-143031-s102-r4-t0-devoff4` (14:30): exit 0, WM_CLOSE, exit line, no dumps, seed OK. Translated 229 in 20 ms, **Created 214 in 1191 ms**. Gap 1293 ms (created → guest 78 ms). First frame 10.0 s, pm 0.
  - Created U4/F4 = 5.5× (6516 / 1191). F4 is close to the default-thread U2 (1521 ms), and its first frame comes 9 s earlier. **PASS: the fix is active.** Functional only; nothing else of mine ran between the two, and the ms are not timing numbers.
- **#32 run 3, boots 1-2: F3a and F3b** (devoff4, default threads, `-Seconds 60 -SeedXenos build\agent3\seed\devoff2-214`, no input; `checks/s102-read-2.txt`).
  - F3a `runs/20261122-143207-s102-r3-boot-devoff4` (14:32): exit 0, WM_CLOSE 0.77 s, exit line, no dumps, seed OK. 229 in 10 ms, 214 in 881 ms. Gap init → guest 944 ms (created → guest 50 ms). First frame 9.0 s, pm 0.
  - F3b `runs/20261122-143310-s102-r3-boot-devoff4` (14:33): exit 0, WM_CLOSE 0.83 s, exit line, no dumps, seed OK. 229 in 11 ms, 214 in 647 ms. Gap 690 ms (created → guest 29 ms). First frame 8.0 s, pm 0.
  - Both: logdiff vs U2 NEW 0 / MORE 0 (GONE = U2's attract-route lines), 0 errors, no STUCK-LOCK.
  - With F4 this is Agent 6's minimum for a hang verdict: **no hang in 3 of 3 warm boots.**
- **#32 run 2: F2 vs U2** (devoff4; the U2 command exactly: `-Seconds 360 -GpuLog -InputScript harness\routes\attract-long.txt -SeedXenos build\agent3\seed\devoff2-214`; `checks/s102-read-3.txt`).
  - F2 `runs/20261122-143414-s102-r2-warm-devoff4` (14:34): exit 0, WM_CLOSE 1.69 s, exit line, no dumps, 67/91 steps (360 s, as planned), seed OK.
  - Storage: 229 in 12 ms and 214 in 575 ms (U2: 229 in 25 ms, 214 in 1521 ms). Gap init → guest 636 ms (created → guest 46 ms); not a hang suspect.
  - First frame 10.0 s (U2 13.0 s). **pm 68 and xpso +68 pipelines, the same as U2** (68 / 68). Max frame over the first 30 frames: 34.5 ms (U2 32.6 ms). STUCK-LOCK 0 in both.
  - Agent 6's logdiff (`--min-level warning`, `checks/F2-vs-U2-logdiff-warning.txt`): NEW 0 / MORE 0 / marker flags 0. GONE 33, all `[info] Toypad` lines (4 `Toypad[Read ]` + 29 `Toypad[Write]`; GONE counts any level), from the route timing: r1 vs ref shows the same kind. 0 errors / 142 warnings (U2: 0 / 142).
  - Attract scenes: 766/110956 for 23 s (U2: 20 s). U2's 790/31625 and 8127/762167 don't show (timing of the attract shots).
  - TimerQueue 34.1 %. Slow state from 209.8 s (40.5 %; U2: from 199 s, 43 %).
  - **PASS.**
- **#32 run 3, boots 4-5: F3c and F3d, plus the optional F1t** (devoff4, `-Seconds 60 -SeedXenos build\agent3\seed\devoff2-214`, no input; `checks/s102-read-4.txt`, `s102-read-5.txt`).
  - F3c `runs/20261122-144024-s102-r3-boot-devoff4` (14:40): exit 0, WM_CLOSE 0.77 s, exit line, no dumps, seed OK. 229 in 28 ms, 214 in 1715 ms. Gap 1832 ms (created → guest 86 ms). First frame 16.0 s, pm 0. The slower boot (storage init at 3.24 s) overlapped my postcheck of F2 (14:40:25), so it says nothing about the fix.
  - F3d `runs/20261122-144129-s102-r3-boot-devoff4` (14:41): exit 0, WM_CLOSE 0.89 s, exit line, no dumps, seed OK. 229 in 10 ms, 214 in 740 ms. Gap 805 ms (created → guest 53 ms). First frame 9.0 s, pm 0.
  - F1t (threads=1) `runs/20261122-144234-s102-t1-devoff4` (14:42): exit 0, WM_CLOSE 1.24 s, exit line, no dumps, seed OK. 229 in 9 ms, **214 in 551 ms**, close to the default-thread boots. Gap 596 ms. First frame 8.0 s, pm 0. **PASS.**
  - All three: logdiff vs U2 NEW 0 / MORE 0 (GONE = U2's route lines), 0 errors, no STUCK-LOCK, no slow state.
  - **Run 3, boots 1-5 (F3a, F3b, F2, F3c, F3d): no hang suspect in 5 of 5.** Created 881 / 647 / 575 / 1715 / 740 ms, gaps init → guest 944 / 690 / 636 / 1832 / 805 ms (every gap is below Created + 5 s), all exit 0 with the exit line. **PASS.**

- **r3n native4 P2 ON** (an extra run, after Agent 1's queue) `runs/20261122-144342-s4a-r3n-p2-native4` (14:43; `native_settings_frontend=false;shared_memory_single_hold_rearm=true`, b-gate-menus-long).
  - Exit 0, WM_CLOSE 1.03 s, 54/54 steps, no dumps, first frame 16 s, 0 errors / 184 warnings.
  - logdiff vs r5: NEW 0 / MORE 0 / GONE 9 (8 Toypad + the info line `Native GPU: re-registered placement shader`) / FLAG 0.
  - Same native scenes, none missing or extra.
  - TimerQueue 30.1 %; no slow state.
  - **PASS** (functional only; S4a has no fallback counter).
- **Slow state over all 20 runs since 13:00**, from Agent 11's `bench/agent11/timerq_slowstate.ps1` via `slowstate.ps1` (14:47; copies in `build/agent3/s4a/slowstate/`).
  - 0 blocking runs. 20 spin runs, 6 of them with slow state (E-cores below 800 MHz for 3+ samples).
  - All 6 are long runs: U2 from 199 s (43 %), r2 from 107 s (16 %), r3 from 200 s (8 %), r4 from 182 s (14 %), a12at from 217 s (26 %), F2 from 210 s (40 %).
  - No slow state in ref, r1, r5, r6on, r6off, r7, r3n or the 60-90 s boots.
  - r5 attempt 1 was skipped (no run.json).
- No game was running after r3n (checked 14:47:38); the runner ended at 14:47:30 ("past the last launch 14:45:00").

### 8.4 Left for after W4b (nothing runs until Agent 1 says W4b is done)

- **Agent 1's queue is complete:** runs 1-8, Agent 12's attract u-diag run (a12at) and all of Agent 6's #32 runs (U4, U2, F4, F3a-F3d, F2, the optional F1t). I added one extra: r3n (P2 on native4). Nothing was skipped. The last launch was r3n at 14:43:39.
- **Open items:**
  1. **P2 fallback count:** r3 (and r3n) are functional passes only, because S4a has no counter. Agent 7's S4b row 8 (the P2 counter, `<S4B-CTR>`) covers it.
  2. **fix (i) with a level load:** r7 covered only the title and the menu walk, as specified. A level load needs Toy Pad tags, so it needs the user (Agent 7's S4b user rows 7, 20 and 23).
  3. **More #32 warm boots,** if Agent 6 wants more than the 5 boots in 8.3.
  4. **Agent 7's S4b queue** (`build/agent7/s4b-queue/QUEUE.md` and `queue-s4b.jsonl`; 22 agent rows, ~109 min; the ~30 min subset is rows 1 → 4 → 10 → 8 → 2 → 5) runs only on Agent 1's GO after W4b.
     - **Bins:** from Agent 2's provisional map (`perf-notes/agent2-baseline.md` S5).
       - S3d line: `<S4B-OFF>` = `build/agent2/devoff4b-bin`, `<S4B-NAT>` = `native4b-bin`, `<S4B-CTR>` = `devoff4b-ctr-bin` (the OFF bin with only rexgpu-xenos.dll swapped), `<S4B-CG26>` = `devoff4b-cg26-bin` (only after Agent 10's rating).
       - B line: `devoffB4b-bin`, `nativeB4b-bin`, `devoffB4b-ctr-bin`, `devoffB4b-cg26-bin`.
     - **`<N>`:** Agent 7 posts it after row 9; use 64 if row 9 can't run.
     - **`needs`:** set to my own ready markers.
     - **kInitOnly cvars:** set at launch only, never from the dev console.
     - **Row 17 depends on Agent 2's G3 alias count:**
       - 31 aliases: l1_waits, l1_polls, l2_tries and kicks must all be > 0. l2_tries = 0 means the bin was built with skip_lr.
       - 29 aliases: only l1_waits and l1_polls > 0 count.
  5. Agent 4 may make mc_smoke_check's C3 heap-aware after W4b. Agent 4's pack visual check (`build/agent4/r2t6/VISUAL-CHECK.md`, ~12 min in a game slot) needs Agent 1's decision.
- **Housekeeping:**
  - `build/agent3/s4a/tmp/r2-alllogs` (43 MB) can be deleted.
  - Keep `build/agent3/s4a/trace/r6on-t` and `r6off-t` (84 + 52 MB) until Agent 4 is done with them.
  - `postcheck.ps1` stops on its own at 14:55; the runner ended after r3n.

## 9. S4b functional queue (task #29, from 16:48)

Source: Agent 7's `build/agent7/s4b-queue/QUEUE.md` and `queue-s4b.jsonl` (22 agent rows: 1-6, 8-19, 21, 22, 24, 25).
Rows 7, 20, 23 need a level load (decision 1, Toy Pad tags) and are skipped for now; row 26 is optional, after 4-24 pass.

### 9.1 Tools (`build/agent3/s4b/`)

- `s4b-queue.ps1`: the S4a runner plus:
  - no launch while `perf-notes/WINDOW-HOLD.txt` or `build/agent3/s4b/PAUSE` exists (it waits); checked again right before each launch;
  - `needs` as a list; `<N>` = first line of `ready-N`; rows with an unresolved `<...>` wait;
  - a `holdwatch.ps1` sidecar per launch.
- `holdwatch.ps1`: if the HOLD file appears while my game runs, it writes `logs/<id>.hold-abort.txt` and stops the game (Stop-Process; a timing window beats a functional run). The record gets `"aborted":"hold"` and the row runs again after the hold.
- `s4b_check.py`: S4b families with counts and first/last lines (C1 keep-watch init/first/kept/blocked, K = verify mismatch, c1_other; split init + fields; deferred_counters + last block; GPU wait stats fields + back-off; memexport full-buffer Nx/total; S4a families; fail lines), logdiff on joined logs (`checks/joined/<run>/game.log` when a run has rotated logs), BASE items as a miss list, per-row PROOF lines, a verdict hint.
- `postcheck.ps1`: per row base + allowed NEW (row 1: R1+REF; 2: RN+N3D; 3: RA; 4/6/24: row 1 + `C1 keep-watch`; 5: row 2; 8: row 3 + `slow frame|memexport full-buffer`; 9: row 1 + `deferred_counters`; 10/11/13: row 1 + split; 12: row 3 + split; 14: row 1; 15: row 14 + split; 16: row 9 + split/counters; 17: row 3 + `GPU wait`; 18: row 1 + `GPU wait`; 19/21/22: row 1; 25: RT + split). No python while HOLD exists.
- Markers: `ready-s4b-off`, `ready-s4b-nat`, `ready-s4b-ctr`, `ready-s4b-cg26` (after the bin checks), `ready-N`, `ready-dbg` (d3d12SDKLayers.dll present: rows 14-15), `ready-m1` (Agent 5's G4: row 19).

### 9.2 Run 2 (task #2 = old #29; 'go' 19:31; Agent 1's target ~22:50; ALL FUNCTIONAL ONLY, hidden desktop)

- **Tag tool** `build/agent3/toypad/` (decision 1 = YES, user 17:27; the 02:11 rules: user-mode only, 127.0.0.1:9191, nothing in a `*-bin`): `ldtag.py`, `toypad_client.py`, `fake_listener.py`, `toypad_sidecar.py` (`--trigger-mark`, `--then-mark/--then-delay/--then-action`); `tags/` batman, gandalf, wyldstyle (.bin + tags.json). Self-tests: `selftest_toypad.py --cpp` 45/45 PASS, `selftest_sidecar.py` PASS.
- **Exploration** (devoff4, before devoff4b): lx1 `runs/20261122-195210-lx1-devoff4`; lx2 `runs/20261122-201420-lx2-devoff4` (exit 0, 683 s, 181/364 steps at the cap, clean close; one NEW `[krnl] [NtCreateFile] FAILED: path='ttappdat...'` = a save path, benign). The level load is reached; the post-load scene is static but rendering (766/110956 + rainbow LEDs; START then A gives 785/123950). Gameplay after the load is not confirmed.
- **L route** `build/agent3/toypad/routes/level-l.txt` (made by `gen_route_l.py`): 119 steps, ends with `stop`, ~430-500 s (`-Seconds 600` is a cap); marks first-frame, title, pads-white, tags-placed, m01-m10, story-load, vortex, v-idle.
- **Queue** (`build/agent3/s4b/queue.jsonl`, file order = priority): the W6 untimed runs and rows 7/20/23 first, then the re-pin, then the W7+ rows (cut by -GamesClosed).
  - s4bL0 = OFF on the L route, uncapped (gate A's s0 for the G8 logdiff); w6gA = gate A (p2fc set + verify + slow frame, L route); w6s1 / w6s2 = side 1 / 2 (title, 260 s, hash log + slow frame); w6s3 = side 3 (attract-long).
  - g3q = W6 G3's -Quick pass, a matrix row on `build/agent3/s4b/g3/matrix-g3.json` (= Agent 5's matrix-w6.json with the placeholder bin replaced by `build/agent2/devoff4b-bin`, 7x, like finalize-w6.ps1; `-PlanOnly -Quick -NoCold -Only s0,p2,p2f,p2fc` exit 0 at 20:53: 4 runs, ~5 min). It doesn't wait for the finalized matrix-window6.json.
  - rpb0 / rpm4 = REPIN.md section 3 (a) / (b); they wait for `ready-repin` (Agent 4's go).
- **New tools**:
  - `s4b-queue.ps1`: matrix rows (`"matrix"` + `"matrix_args"`: run-matrix with `-OutDir build\agent3\runs\<id>-<stamp>`, never build\agent8\matrix; `holdwatch-m.ps1` stops run-matrix and its games if the HOLD file appears); its lines also go to `logs\queue.out.txt`.
  - `postcheck.ps1`: Below Normal (python inherits it); its lines go to `logs\postcheck.out.txt`; P2c = Agent 12's `p2c_check.py` on s4b08*, s4b23 and w6* (`logs\<id>.p2c.txt/.json`); bases for the L rows (s4bL0 vs lx2; rows 7/20/23 and gate A vs s4bL0), the side runs vs RT/w6s1, side 3 vs row 3.
  - `s4b_check.py`: G5 (no `C1 verify F` lines) and the kept count rises (s4b07, w6gA).
  - `wait-event.ps1`: wakes the agent on queue/postcheck lines, a new or re-staged bin, the W6 matrix, or a HOLD change (`logs\wait-event.pos.json`).
  - `bincheck.py`: the S4b cvar and log-line needles in a bin. `framerate_limit` is never a literal (devoff4 neither), yet `framerate_limit = 0` in the toml works (S4a udiag perf.csv fps 374-424).
- **Bins**: devoff4b-bin staged 20:49:02 (S4b = S4a + C1 v3 + M1 + P2c + r1r2 + #26 tool, all OFF; S4c #24/#30 OFF). bincheck 20:53: every S4b needle is present. Agent 12: it has s4-p2c. Markers made: ready-dbg, ready-s4b-off, ready-g3. The queue started 20:52 (LastLaunch 23:10, GamesClosed 23:25); s4b01 launched 20:53:54.
- **Resume**: read `build/agent3/s4b/queue-state.jsonl` and `logs\queue.out.txt` / `postcheck.out.txt`, then restart `wait-event.ps1`. The queue and postcheck re-read their files, so a restart continues where they stopped.

#### 9.2.1 Queue fixes and results (20:57-21:50)

- **REFUSED fix (20:57)**: s4bL0's first launch was refused by `harness\guard.ps1` (`Get-ActiveRunners` saw a short-lived run-matrix process, pid 8152, owner unknown) and the old queue recorded the row as done. Now: a runner pre-check before each launch, `"aborted":"refused"` in the state record, and the row retries. **Never type the runner script names in my own shell commands while the queue may launch**: the guard matches any powershell/cmd command line.
- **Results** (devoff4b-bin, run dirs under `build/agent3/runs/`; checks in `build/agent3/s4b/logs/<id>.check.txt`, P2c in `<id>.p2c.txt`):

| row | run | result |
|---|---|---|
| s4b01 | 20261122-205356-s4b-01-off | PASS: exit 0, 54/54 steps, NEW/MORE/GONE 0 vs R1+REF, families 0 |
| s4bL0 | 20261122-210059-s4b-L0-off-level | PASS (base for gate A and rows 7/20/23): exit 0, 119/119, NEW 0 / MORE 0 vs lx2, tags 3/3, level reached (5-8k draws, ~1M vertices), then 785/123950 at 32 fps. WM_CLOSE 19.4 s |
| w6gA | 20261122-210906-w6-gateA-p2fcv-level | RECOVERED HANG at 21:18:17 (STUCK-LOCK x5, owner lr=83FAF188 in sub_83FAF180 = L1 poll = finding 10 → WARN per Agent 1, 21:29) + hang-36276.dmp; 104/119 steps at the 600 s cap (stopped at story-load); ~10x slow from boot. G5 PASS (verify on, first kept, K 0 / F 0; partial: no level load). G8 lines OK; NEW 6 = the STUCK-LOCK/FATAL lines. P2c PASS total 0 |
| w6s2 | 20261122-211914-w6-side2-p2fc | PASS: exit 0, 287 s, NEW 0 / MORE 0 vs RT (C1 lines allowed), all PROOF ok (init x1, first kept, kept 69632, verify off, gate D 0, no hold-off line, W6 cvars as W6-GATES v2). P2c PASS total 0 (35027 lines) |
| w6s1 | 20261122-212406-w6-side1-p2f | exit 0, 290 s, err/crit/STUCK-LOCK 0, no C1 lines (correct for p2f). P2c PASS total 0 (33692 lines). Logdiff check still running at 21:50 |
| g3q | g3q-20261122-2128 | G3 PASS: matrix-g3.json = byte copy of `build/agent5/w6-draft/matrix-window6.json` (sha256 E50D791B…); s0/p2/p2f/p2fc 4/4 OK, exit 0, first frame, clean close; logdiff NEW 0 / MORE 0 vs s0; p2fc init + first kept |
| s4b23 | 20261122-213421-s4b-23-w6-p2fi-level | Row 23 PASS: exit 0, 119/119, level reached (785/123950 at 29.5 fps), WM_CLOSE 10.3 s, NEW 0 / MORE 0 vs s4bL0 (GONE "unexpected" 1 = a Toypad lit-colour line, route timing), stuck_lock/minidump 0, G8 bad lines 0, P2 total 0 in the level (last line `memexport full-buffer 0x (total 0)`) |

- **Verify mode is slow on this bin**: w6gA ran 12-17 fps in the front end (s4bL0 112-345), and the time is kernel mode (GPU Commands 91% kernel vs 20% in s4bL0; subagent). s4b07 (verify) runs ~10 fps vs 50-60 for s4b23 at the same route step, so it can't reach the level inside 600 s. Keep-watch without verify (w6s2) is fine. A `ninja -j 8 legodimensions` (8 clang++, Below Normal) had the host at 100% CPU from ~21:38.
- **Teardown**: WM_CLOSE 4.7-19.4 s on level runs. The cause is a lingering "D3D Background Thread" in kernel/driver code after "hard-exiting", not guest code. Above 60 s the harness would kill the game and the row would be a false FAIL.
- **Watch item**: on devoff4b the post-title 220/528 menu phase took 16.6-17.3 s in 2 of 2 runs, against ≤8.7 s in 6 of 6 devoff4 runs. These were functional runs under host load, so it's unconfirmed.
- **Queue edits**: w6gB (gate B: p2fc, verify off, slow frame, L route, 600 s) after rpm4. 21:46: s4b18 moved right after s4b24 (Agent 1: W9's functional rows are s4b24 + s4b18; W9 uses SPIN_US=30, the default). s4b17 moved to the end (not needed). Backup: `queue.jsonl.bak-2146`.
- **postcheck** restarted 21:49 (task with the w6gB case). It skips an id when `logs\<id>.check.txt` exists (and then skips P2c too), so when I check a row by hand I also run p2c by hand. s4b_check on rotated logs vs the 9-log RT base took ~24 min under the build load.
- Python from the WindowsApps alias runs as `python3.11.exe`: filter processes with `Name like 'python%'`.

#### 9.2.2 Rows 7 and side 1, rulings, tools (21:50-22:00)

- **w6s1** logdiff done 21:51: NEW 0 / MORE 0 vs RT, all PROOF ok → **PASS**.
- **s4b07 (row 7)** `20261122-214221-s4b-07-c1v-level`: exit 0 at the 600 s cap (611 s), WM_CLOSE 1.08 s, errors 0, STUCK-LOCK 0. 104/119 steps; last mark story-load@202 s; the level was loading (8131 draws) when the cap hit (~11 fps under verify). Verify armed x1, first kept, **K 0**, kept rises 2→32768, gate D 0, Protect failed 0. **C1 verify F = 92** (first 21:42:43, 5 s after verify on). Gate A (same C1 cvars + P2 `shared_memory_single_hold_rearm`) had F 0. **Naming fix (22:20; Agents 10/12 caught it):** fix (i) = `physical_protect_hold_global_lock`, P2 = `shared_memory_single_hold_rearm`. Row 7 HAS fix (i) but NOT P2, so F 92 is not the R1 race (fix (i) closes R1); earlier messages that called the rearm cvar "fix (i)" were wrong. Agent 12's reading: the s4bV0 control (row 7 with keep_watch=false, verify on) decides: last F "(N so far)" near 92 = the old path's baseline; near 0 = C1 without P2 misses writes ("C1 verify: on." must be in the log). Agent 10 treats C1 without P2 as not cleared. There is no C1-OFF verify baseline yet (s4bV0 is gated on Agent 1's OK). QUEUE.md row 7's rule needs K only → **PASS (capped, partial coverage accepted by Agent 1)**, with an F-line note. Not a W6 blocker: every W6 C1 arm has fix (i). Verify rows: the 220/528 phase was 46 s, which isn't comparable (verify cost).
- **Agent 1's rulings**: (21:29) a STUCK-LOCK owned by sub_83FAF180 (lr 83FAF188) = finding 10 = WARN; any other owner = FAIL, tell Agents 8 and 1 at once. (21:45) W9 functional rows = s4b24 + s4b18 (BACKOFF_US=250 + STATS, sleep_fail 0). (21:54) w6gB = the C1 level-load coverage; row 7 stays capped; flag any devoff4b row run WITHOUT the compile load whose 220/528 phase is > 17.4 s (devoff4 ≤ 8.7 s).
- **hostload sampler** (`build/agent3/s4b/hostload.ps1`, started 21:58, BelowNormal, until 23:40): every 30 s writes `logs\hostload.csv` (time, clang++/cl/ninja/link counts, CPU %, game pid). A row counts as "without the compile load" only if clang++ = 0 for its whole run.
- **s4b_check GONE fix**: `GONE_OK_DEFAULT` now also covers `Toypad: pad # mode` (LED colour lines, route timing) and `slow frame #`. py_compile OK 21:58. It applies to checks run after 21:58.

#### 9.2.3 Run-2 S4b queue, 22:00-22:25 (Agent 3)

- **Naming fix:** fix (i) = `physical_protect_hold_global_lock`; P2 = `shared_memory_single_hold_rearm`. The row-7 entry in 9.2.2 was corrected at 22:20.
- **w6s3 (side 3)** `20261122-215230-w6-side3-p2fc-attract`: **PASS**.
  - logdiff vs RA (`20261122-140637-s4a-udiag-attract`): NEW 0 / MORE 0 / GONE 29 (0 unexpected).
  - PROOF all OK: C1 keep-watch on x1, first kept, kept rises to 114688. Verify off; K, F and gate D are 0; no STUCK-LOCK.
  - P2c total 0 (36388 counter lines; Agent 12 agrees).
  - 77/91 steps at the 420 s cap. RA stopped the same way at 79/91, and the floor is base-2.
  - Max frame 3987 ms at the start of the attract demo (a memexport sync burst: 2736 syncs, host-gpu wait 1716 ms). Demo-phase fps is 14.1 vs RA's 11.6. 220/528 = 13.5 s (RA 11.9 s).
  - WM_CLOSE 25.37 s, but "Title terminated; hard-exiting process." came 0.12 s after WM_CLOSE. The remaining ~25 s is OS teardown of the process (the same pattern as s4bL0).
- **s4b22** `20261122-220009-s4b-22-w6-p2fi`: **PASS**. NEW 0 / MORE 0 vs s4b01, 54/54 steps. 220/528 = 16.6 s. WM_CLOSE 26.36 s (C1 off).
- **s4b24 (W9)** `20261122-220520-s4b-24-w6-c1`: **RECOVERED HANG** at 22:07:54 (STUCK-LOCK x5 + hang-31952.dmp). run-game exit 1, 54/54 steps.
  - The owner is tid 0x17 at lr=83FAF200, inside sub_83FAF180 (83FAF180-83FAF25F). That makes it finding 10 by function, but not the known lr 83FAF188.
  - Owner's callers: 83FBF7B4 <- 83FBFA98 <- 83FBF868 <- 83FBFBDC <- 83FC0CA8 <- 83FB3AC8 <- 83FBF698 <- 83FBFA98 <- 82BD6BA4. The waiter's callers and the GPU thread (PM4 0x22) match gate A.
  - First finding-10 STUCK-LOCK without verify.
  - PROOF all OK (init, first kept, kept 40960, gate D 0). 220/528 = 9.9 s. WM_CLOSE 1.64 s.
- **s4b18 (W9)** `20261122-220947-s4b-18-gw-q250`: **PASS**.
  - exit 0, 54/54 steps.
  - One "GPU wait back-off: ON (quantum 250 us, spin 30 us); stats ON; GetData hook built." line; 41 stats lines, sleep_fail 0.
  - No STUCK-LOCK. NEW 0 / MORE 0 vs s4b01 (only the allowed GPU wait lines).
  - 220/528 = 14.8 s. WM_CLOSE 40.14 s (C1 off), the highest so far (limit 60 s).
- **s4b20 (row 20, M1 `shared_memory_upload_nontemporal_copy=true`, L route + tags)** `20261122-221447-s4b-20-m1-level`: **PASS with a finding-10 WARN**.
  - Level reached: 119/119 steps (vortex at 369 s .. end at 462 s).
  - M1 cvar in run.json (M1 logs nothing). crash_events 0, WM_CLOSE 1.36 s.
  - RECOVERED HANG at 209 s (22:18:20, level load). It is the same finding-10 STUCK-LOCK as s4b24: owner tid 0x17 lr=83FAF200, identical owner and waiter callers, GPU in PM4 0x22 (read 0x102b / write 0x1206). Dump: hang-13236.dmp.
  - **C1 was OFF**, so the 83FAF200 variant is not caused by C1.
  - TimerQueue cycles were non-rising at 200.2-202.2 s, so the process was starved just before the hang.
  - logdiff vs s4bL0: NEW 6 (only the STUCK-LOCK/FATAL lines) / MORE 0 / GONE 79 (0 unexpected), FLAG fatal=1.
  - 220/528 = 19 s (base 17 s; under the build load).
- **Host load:** `cmake --build build\agent2\snap1-on --target legodimensions -j 8` (8 clang++) has held the CPU at 100% since ~21:38 (hostload.csv from 21:59: clang 7-8, cpu 100).
  - Both finding-10 hangs without verify (s4b24, s4b20) ran under it.
  - No row has run without the compile load since then, so the 528 flag (>17.4 s without load) can't fire.
- **WM_CLOSE by row, with C1 state** (asked by Agent 1 at 22:0x):

  | row | WM_CLOSE | C1 |
  |---|---|---|
  | s4b01 | 4.96 s | off |
  | s4bL0 | 19.43 s | off |
  | w6gA | 0.89 s | on |
  | w6s2 | 6.74 s | on |
  | w6s1 | 11.58 s | off |
  | s4b23 | 10.25 s | off |
  | s4b07 | 1.08 s | on |
  | w6s3 | 25.37 s | on |
  | s4b22 | 26.36 s | off |
  | s4b24 | 1.64 s | on |
  | s4b18 | 40.14 s | off |
  | s4b20 | 1.36 s | off |

  The long closes don't follow C1. They come after the game's own hard exit, while the host is under the build load.
- **REFUSED/held launches, 22:04-22:23:** Agent 5's launcher dry-run tests start `-PlanOnly` runner children. The guard counts them as active runners, so my launches get refused or held, and the queue retries them automatically.
- **Queue changes:**
  - Reorder at 22:10 (`build/agent3/s4b/reorder_2210.py`, backup `queue.jsonl.bak-2210`).
  - s4bV0 at 22:16 (`fix_v0_2216.py`, backup `.bak-2216`) now follows Agent 12's spec: row 7 with keep_watch=false. It is gated on `ready-v0`, which waits for Agent 1's OK.
  - `ready-m1` at 22:11, on Agent 5's go (M1 copybench --check-only PASS).
- **s4b_check label fix (for Agent 10):** the K and "kept count rises" labels now state the route coverage. They say "through the level load (last mark X)" if the run reached `vortex`, otherwise "to route mark X only, no level load".

#### 9.2.4 s4b17, gate B tag loss and the sidecar fix, finding 10, f10 rows, morning plan (22:25-23:00, Agent 3)

- **s4b17 (W9 third gate)** `20261122-223103-s4b-17-gw-p1`: **PASS**.
  - exit 0; 79/91 steps (cap); dumps 0; STUCK-LOCK 0. NEW 0 / MORE 0 vs RA; GONE 46 (0 unexpected).
  - Init line x1: "back-off OFF (quantum 0 us, spin 30 us); stats ON; GetData hook built". 81 stats lines. Sums: l1_waits 21926, l1_polls 2.82e9, l2_tries 21524, kicks 87247, sleep_fail 0.
  - L1 histogram: <50us 6983, <200us 5, <1ms 46, <4ms 395, >=4ms 14497. L1 sum 314.5 s, max 663 ms. L2: 23 waits, sum 2.75 s, max 1077 ms.
  - 220/528 = 9 s; TimerQueue non-rising 0/209. WM_CLOSE 40.75 s (C1 off): the new max, still < 60 s. Ran under Agent 2's -j 8 build.
  - Stats JSON `build/agent3/s4b/logs/s4b17.gw.json`, made by `build/agent3/s4b/gw_stats.py`. Agent 9: L1 is bimodal; S = 30 us covers the short mode; Q comes from its quiet-machine sweep.
- **w6gB (gate B)** `20261122-222313-w6-gateB-p2fc-level`: PASS on proofs (C1 init, first kept, kept 2 -> 114688 through the level load, verify off, gate D 0, P2c 0, level reached) + finding-10 WARN (STUCK-LOCK 22:26:29, owner tid 0x17 lr=83FAF200, hang-38764.dmp). WM_CLOSE 1.51 s (C1 on).
  - **Tags were NOT placed (0/3).** Agent 1 (22:44): gate B counts for W6 as "level load without tags".
  - Root cause: spdlog rotated game.log at 22:23:58 (game.log -> game.1.log, new game.log). My sidecar kept reading the old file's handle, so it never saw the trigger line in the new game.log. (run-game's own wait_log followed the rotation.)
  - **Fix (22:50)** in `build/agent3/toypad/toypad_sidecar.py`: a `Tail` class follows rotation by file id (st_dev, st_ino). It drains the renamed old file (game.N.log), reads any newer copies, then reads the new file from 0. It also handles in-place truncation. An `on_rotate` callback writes a "log-rotated" row to toypad-events.csv. Pre-fix copy: `toypad_sidecar.py.bak-2245` (hash 8636B6191E5893FC).
  - **Tests (no game):** `build/agent3/toypad/selftest_rotation.py` part A (9 unit checks) PASS. Part B (end to end with fake_listener, two rotations, trigger only in the new, shorter game.log) PASS, through the drain path. The old copy with `--expect-fail` FAILs part B as expected (0 loads, trigger=False), which reproduces w6gB. `selftest_sidecar.py` still PASS.
  - Agent 8's matrix doesn't use my sidecar (grep), so the W6-W10 timed runs are unaffected.
  - **Risk for s4bLV (1800 s):** spdlog keeps at least 8 rotated logs (s4a-udiag had game.1..8.log). A long slow-frame run may roll the boot lines (the C1 init proof) off the end. After s4bLV, check for game.8.log and whether the boot lines survived.
- **WM_CLOSE table, continued:** w6gB 1.51 s (on); s4b17 40.75 s (off). Max over the 14 game runs: 40.75 s (< 60 s).
- **Tags per run (sidecar result rows, 23:00):** 3/3 LOADs in s4bL0, w6gA, s4b23 (row 23), s4b07 (row 7) and s4b20 (row 20); 0/3 in w6gB (rotation bug).
- **Finding 10:** 4 hits in 14 game runs (w6gA, s4b24, s4b20, w6gB), all recovered. Every owner lr is in sub_83FAF180 (83FAF188 or 83FAF200).
  - Subagent job (E): it appears where a run reaches the start of the in-engine cinematic (a ~4-5 s frame, then an 8-13 s frame), whatever the route. w6gB: hang frame #33131 was 7979 ms (2736 syncs, GPU wait 4836 ms). s4b24: the b-gate-menus-long idle tail, frame 13141 ms. w6gA: the verify CPU storm, frame 9658 ms.
  - Runs that reached the cinematic with no STUCK: s4b01, s4bL0 and s4b23 (all before the ~21:38 build load), and w6s3 and s4b17 (under load).
  - W5's 16 runs (~113 s at the title) never reached the cinematic (0 frames over 200k vertices). So W5/W6's 0 STUCK is not a load-only test (Agent 6 agrees).
  - Per-sync cost (w6gB, under load): cinematic 1.58 ms GPU wait per sync, 19.6 KB, frame-time slope 1.82 ms/sync. After the vortex: 1.38 ms/sync, 7.2 KB, slope 1.48.
  - Host CPU at the hangs (from the new hang_scan): w6gB sys.csv cpu_util_pct 85-95 % over [-10, +2] s, s4b20 82-84 %. hostload.csv showed clang 8, ninja 1, CPU 100 % within 60 s of both.
  - Agent 6 (`build/agent6/hang/cp-state-s4b24-s4b20.md`): the CP waits in AwaitAllQueueOperationsCompletion, the memexport readback full-path sync (IssueDraw -> full path -> CheckSubmissionFence -> WaitForSingleObject INFINITE). Meanwhile render tid 0x17 holds CS 0x84959EDC while it polls a GPU fence. The CP is not hashing, not doing K-checks and not waiting on hold_global_lock. Verify adds kernel load (gate A 75-86 %), but the hang doesn't need verify. All 3 dumps were taken under the -j8 build.
- **Agent 1's rulings:**
  - 22:27: s4b24 = WARN, not a C1 fail; finding 10 is load-related. ready-v0 is approved, but s4bV0 waits until after the windows.
  - 22:32: launch nothing after s4b17.
  - 22:44: gate B = "level load without tags". W6's timed runs are title + attract only. Gate A covered tags + C1 up to story-load. C1 default-ON needs s4bLV with the fixed sidecar, 3/3 LOADs and the level reached with verify on. The sidecar fix (tested without the game) is fine tonight. Morning order is below.
  - 22:54: confirm the queue is empty and stop the daemons before 23:50.
- **Daemons stopped at 22:56:** the s4b queue (pid 31480), postcheck (pid 25688) and the hostload sampler (pid 3956), via task kill. A CIM check found no s4b-queue/postcheck/hostload/toypad_sidecar/holdwatch process of mine left. No game was running and no clang/cl/ninja/link were running.
- **f10 rows (22:56)**, added by `build/agent3/s4b/patch_f10_2255.py`. Backups: `.bak-2255` of s4b_check.py, postcheck.ps1 and queue.jsonl.
  - queue.jsonl: f10a (`f10a-m1-sfl-level`: s4b20's set, nontemporal_copy=true, + slow_frame_log_ms=1, C1 OFF) and f10b (`f10b-p2fc-level`: w6gB's set, which already has slow_frame_log_ms=1). Both are 600 s on the L route `build/agent3/toypad/routes/level-l.txt` with toypad on. Both need ready-s4b-off + ready-later + ready-quiet. They are inserted before rpb0.
  - s4b_check.py: `hang_scan()` collects STUCK-LOCK events (lines <= 3 s apart). For each it reads the owner lr from the "parked at lr=" line, sys.csv cpu_util_pct/e_eff_mhz over [-10, +2] s, and hostload.csv rows within +-60 s. It also counts the quiet-host rows during the run and the Toy Pad LOAD lines + the sidecar's result row, and prints "hang N:" lines. f10 proofs: cvars, C1 off (f10a), slow-frame lines (f10a), tags >= 3 LOAD lines, level reached (vortex), the finding-10 count, quiet host (0 busy hostload rows) and G8. f10b also gets the C1 proofs and P2c (P2_ROWS).
  - postcheck.ps1: f10a/f10b are checked vs s4bL0 (allow-new 'slow frame|memexport full-buffer', plus 'C1 keep-watch' for f10b). P2c also runs on f10b.
  - **Tests:** py_compile OK; postcheck parse 0 errors; queue order ... s4b17 f10a f10b rpb0 rpm4 ... Smoke tests went to `build/agent3/s4b/checks/retest-2255/` (the logs/*.check.txt files are untouched):
    - The first smoke run showed the lr regex also caught the waiter's `lr=82A2A270`, so "finding 10" read False. At 22:58 I limited the regex to the owner's "parked at lr=" and re-ran.
    - w6gB checked as f10b: hang 1 at 22:26:29.586, lr 83FAF200, finding 10 True, CPU max 94.7 %, clang 8. Tags MISS (0/3, trigger=False), as expected. Level reached; P2c 0; cvars all as planned; quiet-host MISS (5/5 busy rows), as expected.
    - s4b20 checked as f10a: hang 1 at 22:18:20.260, lr 83FAF200, finding 10 True, CPU max 84.4 %. Tags 3/3; level reached. The cvar DIFFER (no slow_frame_log_ms) and the 0 slow-frame lines are expected, and so is the quiet-host MISS.
- **Agent 4's re-pin handoff (22:46), after the f10 rows.** Pin record `build/agent4/repin/pin-native4b-2243.txt` (fingerprint 9b40acbbef4c57b3). Never send output to build\agent8\matrix.
  - (a) Boot (rpb0): matrix `build\agent4\repin\matrix-repin-native4b-boot.json`, `-OutDir build\agent3\runs\repin-boot-<yyyyMMdd-HHmm>`. Then run `python bench\agent7\native3_boot_check.py <dir>\runs\<HHMM>-b0-r1 --bin-dir build\agent2\native4b-bin`. Pass = exit 0, no FAIL in A/B/C, D "PASS native GPU fingerprint: MANIFEST 9b40acbbef4c57b3, game.log 9b40acbbef4c57b3", both fix (a) MANIFEST rows PASS, VERDICT D=PASS. Send any D WARN to Agent 4.
  - (b) Matrix (rpm4): `build\agent4\repin\matrix-repin-native4b.json` (4 runs), `-OutDir build\agent3\runs\repin-<stamp>`. Pass = all of: logdiff `--base <n0old> --cand <n0>` NEW 0 / MORE 0 except the Native GPU [fp] line and the P2c suffix; no C1 keep-watch, d3d12_submit_split, deferred_counters or GPU wait back-off lines; n0's draws p10/p50/p90 equal n0old's; a clean WM_CLOSE on all 4; n2 shows 'parallel workers=2'; n3 has no batches line; no hash=0 lines; `python bench\agent4\check_n_rows.py --baseline <n0> --rows n2=<dir> n3=<dir>` exits 0. Report to Agents 1 and 4; on a fail, send the run dirs to Agents 4 and 2. Full criteria: `build/agent4/repin/REPIN.md` section 3.
  - **Agent 2 (22:55):** native4b's native GPU fingerprint changed (9b40acbbef4c57b3; native4 was 5e3ff55d...). So it rejects the native-pso-recipes.bin / native-pso-seed.bin that native4-bin recorded (pipeline_recipes.h:247-256), and its first start prepares PSOs cold until they are re-recorded. Warm it up before any A/B. Subagent job (F) is checking where those files live and whether a warm-up would write into the staged bin.
- **Agent 12's s4bV0 read-out:** (1) no "C1 verify: on." line = void; (2) F = the last "(N so far)" (row 7: 92); (3) distinct pages, and how many fall in 01AE8000-022BF000; (4) the F thread's name in threads-s4a.csv; (5) F split by the 3 INSTALL0_2.DAT bursts (row 7: 18/20/54). If F = 0, tell Agents 10 and 12. s4bV0 has no postcheck case: hand-run s4b_check with base = s4b07's run and `--allow-new 'C1 verify'`. Agent 1 (22:27): agree row 7's L route with Agent 12 first (Agent 10's request).
- **Morning checklist (Agent 1 wakes me ~03:30; builds wait for me):**
  1. Check the HOLD file. Confirm no game and no clang/cl/ninja/link are running.
  2. Start hostload.ps1, then postcheck.ps1, then s4b-queue.ps1 (window times from Agent 1). Create `ready-later` and `ready-quiet` (only while hostload runs and no compiler is running). The queue runs f10a, then f10b.
  3. Read the "hang N:" lines and the f10 proofs. Send PASS/WARN, STUCK-LOCK counts and the host CPU at any hang to Agents 1, 6, 10 and 12.
  4. Re-pin: settle the PSO warm-up question first (job F). Then create `ready-repin` for rpb0, then rpm4, and check against section (a)/(b) above. Report to Agents 1 and 4.
  5. Create `ready-v0`: s4bV0 (read-out above), s4b04, s4b08, s4bLV (fixed sidecar, 3/3 LOADs, level reached with verify on, cap 1800 s, then the game.8.log/boot-line check), s4b19.
  6. Then s4b02, s4b05, s4b06, s4b03, s4b09-16, s4b21, s4b25. The P2 counter from a devoff4b-ctr run (task step 3) runs when the CTR bin lands.

#### 9.2.5 Task #23 (11-23, 05:45-12:30): quiet-host f10 rows, native4b re-pin, wrap-up (Agent 3)

- **Task (Agent 1, 05:45):** run f10a/f10b on a quiet host, starting after Agent 6 posts that dumpstacks are done, or at 06:20 at the latest. Before each row, check that no build or other heavy process is running. Results go in `build/agent3/f10/RESULTS.md`. Then the native4b re-pin rows if time allows. All games end by 12:00; `build/agent3/HANDOFF.md` is due by 12:30. No builds and no timed runs. The project pauses from ~13:00.
- **PSO warm-up (9.2.4 checklist item 4): resolved.** Agent 1 (23:00): no warm-up is needed. The PSO files live in each run's own exe folder, run-timing makes a fresh run folder every time, and no re-pin matrix sets seed_cache, so native4 and native4b rows start equally PSO-cold.
- **Agent 6, 05:52:** gate B's dumpstacks (hang-38764) are done. It's the same hang as the other three: owner XThread9038 spins in the H1 fence poll (sub_83FAF180+0x3F); the CP is in the full-path memexport readback sync. At the dump the CP was in the submit half (EndSubmission -> D3D12Core -> nvwgf2umx), not in the fence wait. Agent 6's write-up is `build/agent6/hang/cp-state-s4b24-s4b20.md` section 7.3. It is still open whether the GPU or the starved host was the bottleneck; the quiet-host rows are meant to settle that.
- **Prep (05:45-05:57):**
  - `build/agent3/f10/prep_0550.py` (backup `build/agent3/s4b/queue.jsonl.bak-0550`) leaves only f10a, f10b, rpb0 and rpm4 active. The other 19 pending rows are commented out with `#`. rpm4 now also needs `ready-rpm4`, which I create only after rpb0's boot check passes.
  - **Quiet-host gate:** `build/agent3/f10/patch_queue_quiet.py` (backup `s4b-queue.ps1.bak-0550`) adds `QuietReason` plus the `-QuietCpuPct` / `-QuietSampleSec` parameters to `s4b-queue.ps1`. Right before each launch it checks for build processes, for my check scripts, and for Processor(_Total) above the limit. If the host is busy, the queue waits and checks again about every 25 s. At launch it writes `logs/<id>.quiet.txt` and a "quiet host before <id>" line.
    - Tested with `build/agent3/f10/test_quiet.ps1`, which takes the function from the file's AST: parse errors 0; on the real host it returned busy at 66.5 % and 30.9 %; with limit 0 it returned busy.
    - The queue runs with `-QuietCpuPct 40 -QuietSampleSec 10`. Reasons: the other agents' baseline is 25-45 % (agy about 14.5 %, about 1.7 threads; electron about 5 %), their analysis scripts push it to 60-90 %, and last night's -j8 build held it at 100 %.
  - **hostload.ps1:** a new `top` column holds the 4 process names using the most CPU over each 30 s interval. A file with the old header is renamed first, so last night's rows are now in `logs/hostload-20261122.csv`. s4b_check's per-hang hostload lines and f10_results both show the column.
  - **`build/agent3/f10/f10_results.py`**, per run: hang and owner lr, slow-frame buckets, host-gpu wait per frame, ms per wait, memexport syncs, P2 full-buffer, tags, vortex, sys.csv cpu, and hostload rows (busy count, cpu median/max, and the rows within 60 s of each hang). Last night's runs are in `build/agent3/f10/compare-lastnight.md` / `.json`.
  - **Daemons started at 05:57:**
    - hostload with `-Until 12:05`;
    - postcheck with `-Until 12:30`;
    - the queue with `-LastLaunch 11:40 -GamesClosed 12:00 -QuietCpuPct 40 -QuietSampleSec 10`.
    `ready-later`, `ready-quiet` and `ready-repin` were created at 05:57:26.
  - **f10a** launched at 05:58:08 after a quiet check of 23.5 % over 10 s. The first gate attempt, at 05:57:42, read 41.3 % and waited.
  - **f10a result:** DONE 06:05:41, exit 0, 453 s. Hint PASS (logdiff vs s4bL0 NEW 0 / MORE 0), 0 STUCK-LOCK, tags 3/3, reached `end`. 2 frames >= 1 s, max 1790.8 ms (a loading frame, gpu idle). Memexport syncs 18810 in total, max 350 per frame, and at most 24 per frame through the cinematic.
  - **f10b result:** the gate waited at 06:05:53 (99.9 %, other agents' python) and launched at 06:08:45 at 39.8 %. DONE 06:16:14, exit 0, 449 s. Hint PASS and P2c PASS, 0 STUCK-LOCK, tags 3/3. 7 frames >= 1 s, max 2886.5 ms. The two 2736-sync frames took 2657.6 and 2886.5 ms at 0.29 and 0.37 ms per wait. In gate B under the build the same frames took 4873.3 and 7978.6 ms at 6.05 and 1.79 ms per wait.
  - **Answer, in `build/agent3/f10/RESULTS.md`:** no hang on a quiet host (n = 1 per set). The STUCK-LOCK detector fires at 5 s ("still not acquired after 5s"). New scratch tools in `build/agent3/f10/`: `sync_profile.py` (syncs per route segment), `align.py` (perf.csv long frames relative to story-load) and `cine.py`. s4b20's hang frame was a 12037 ms frame with 8316 draws, story-load +38.1..+50.1 s.
  - **rpb0** launched at 06:17:17 (gate 16.9 %) and was DONE at 06:19:31 (135 s). `native3_boot_check.py` gave A/B/C/D PASS and exit 0. The MANIFEST and game.log fingerprints are both 9b40acbbef4c57b3; fix (a) is 4EC71328... and 9CBE6DBF... Output: `build/agent3/s4b/logs/rpb0.boot.txt`. I created `ready-rpm4` at 06:20:31. rpm4 launched at 06:20:42 (gate 15.3 %), output in `build/agent3/runs/rpm4-20261123-0620`.
  - **rpm4 result:** DONE 06:29:54, exit 0, 551 s. The runs are in `build/agent3/runs/rpm4-20261123-0620/runs/` (0620-n0old, 0623-n0, 0625-n2, 0627-n3). Every REPIN section 3b check passes (`build/agent3/s4b/rpm4_3b_check.ps1` -> `logs/rpm4.3b.txt`; `rpm4_draws.py` -> `logs/rpm4.draws.txt`):
    - logdiff n0old -> n0: NEW 0, MORE 0, marker flags 0. The only GONE lines are info-level Toypad lines.
    - No forbidden-family lines on any arm.
    - n2 has `Native draw batches: parallel workers=2` and no hash=0 lines. n3 has no batches line and no hash=0 lines.
    - Draws p10/p50/p90 are 8/8/8 for both n0 and n0old (equal).
    - WM_CLOSE was clean on all 4 runs (killed False, exit 0). `check_n_rows` exit 0 (n2 PASS, n3 PASS).

    Sent to Agents 1 and 4; the pin decision is theirs.
  - **Second f10 pair (Agent 1, 06:23; every game had to end by 07:20):**
    - `build/agent3/s4b/add_f10r2_0628.py` (backup `queue.jsonl.bak-0628`) appended `f10a2` and `f10b2`. They have the same args as f10a / f10b and also need `ready-f10r2`.
    - `s4b_check.py` maps them to the f10a / f10b row rules (L428-429). `postcheck.ps1` gives them the same bases and the P2c check. Both files have `.bak-0628` backups.
    - f10a2 ran 06:32:44-06:40:01 (gate 28.2 %) and f10b2 06:40:14-06:47:26 (gate 29.0 %). Both: hint PASS, logdiff vs s4bL0 NEW 0 / MORE 0, STUCK-LOCK 0, tags 3/3, reached `end`. f10b2 P2c PASS. No hostload row had a compiler.
  - **Shutdown:**
    - At 06:47:46 I created the STOP file; the queue ended itself. Then I stopped postcheck and hostload.
    - At 06:59 no game, queue, postcheck, hostload, holdwatch, wait-event or sidecar process was left.
    - Also at 06:59 I removed `ready-later`, `ready-quiet`, `ready-repin`, `ready-rpm4` and `ready-f10r2`. `ready-s4b-off`, `ready-dbg`, `ready-g3` and `ready-m1` stay; they come from run-2 checks on 11-22, so re-check before reuse. The STOP file stays.
  - **n = 2 answer** in `build/agent3/f10/RESULTS.md`. `build/agent3/f10/run_n2.ps1` re-made the tables; the n = 1 versions are `*.n1.*`.
    - 0 of 4 quiet runs hung, against 4 of 6 under the -j8 build (one-sided Fisher p = 0.07). The worst quiet frame was 2.89 s, under the 5 s threshold.
    - The stall is host-side and comes in episodes. The same GPU work waited 0.18-0.98 ms per round trip on the quiet host and 1.79-6.05 ms in gate B's stall frames. Yet gate B's 1644-sync frame at +60 s, still under the build, waited only 0.11 ms per round trip.
    - Retracted the n = 1 point "under load more draws took the full-path sync": f10b2 had 77236 syncs, more than gate B's 60921.
  - **Handoff:** `build/agent3/HANDOFF.md`.
