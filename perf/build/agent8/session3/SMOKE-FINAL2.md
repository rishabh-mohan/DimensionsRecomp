# SMOKE-FINAL2: smoke boots of the final2 bin pair (M8, session 3)

Bins (pins: `build/agent2/final2/BIN-PINS.md` 33F74799, §Smoke; built from pushed commits, superproject 2de88ce, SDK a7e79c0):

| bin | role | MANIFEST sha256 | verify-bins |
|---|---|---|---|
| `build/agent2/devfinal2-bin` | Xenos ship | 4A4A13EDFBFF6A5F… | PASS: 7 rows, 0 FAIL (16:13:50, and again 16:26:29 in the kit dry run) |
| `build/agent2/nativefinal2-bin` | native, new SDK DLLs | 4E5E2620F38F7D09… | PASS: 8 rows, 0 FAIL (16:18:18, and again 16:26:30) |

## Part 1: plain boots (no -Cvar, no -Env, no input). Result: everything PASSES except first 3D, which is NOT REACHED on both

Pre-checks before each boot:
- day launcher `waiting-for-go (since 13:34:18)`;
- 0 game processes;
- no builds running;
- Minecraft not touched.

Command: `bench\agent8\run\first-boot.ps1 -BinDir <bin> -Tag <tag> -WatchSeconds 240`. The watch time is 240 s per the Overseer's ruling (a). The checker is `smoke-final2/check_final2.py`.

| check | devfinal2 (xenos) | nativefinal2 (native) |
|---|---|---|
| run dir | `build/agent8/runs/1613-devfinal2-smoke` | `build/agent8/runs/1618-nativefinal2-smoke` |
| launched | 16:13:59 (pid 28184) | 16:18:24 (pid 7904) |
| clean exit | PASS: 0x0, WM_CLOSE, 0.41 s, not killed | PASS: 0x0, WM_CLOSE, 0.52 s, not killed |
| dialogs / WerFault / crash artifacts | PASS: none / no / none | PASS: none / no / none |
| args are harness defaults only | PASS | PASS |
| `d3d12_pipeline_creation_no_wait` lines in game.log | PASS: 0 | PASS: 0 |
| check-defaults | PASS (`--mode xenos`): all 13 keys `default`; full back-off line `GPU wait back-off: ON (quantum 500 us, spin 30 us); stats OFF; GetData hook built.` ×1; no OFF line; 0 bad strings | PASS (`--mode native`): all 11 keys `default`; `Native GPU: shader miss cache ON (build default)` ×1; C1 keep-watch blocked (native) ×1; 1 ms timer ×1; TimerQueue precise ×1; 0 back-off lines; 0 bad strings |
| first 3D | **NOT REACHED**: max 228 draws over 236.8 s (14210 frames); frame time flat at 16.67 ms | **NOT REACHED (PROXY)**: all 47 GPU shader/surface lines fall in the first 20 s, then none; frame time flat at ~4.17 ms |
| info | peak working set 734 MB, sys_busy mean 18.4 % | peak working set 1703 MB, sys_busy mean 35.9 % |

**Why first 3D was not reached:** these boots send no input, so the game waits on the title / front end screen indefinitely. This is a property of the test, not a fault in either bin. Both bins boot, run 240 s and exit cleanly, with their defaults intact.

**The CF1/CF2 matrix route does not reach 3D either.** Every CF1 ship run peaks at 226-228 draws (`maxdraws.py` over `build/agent8/matrix/20261125-1255`), because run-timing has no input step. The CF fps figures therefore measure the uncapped front end; that was already true of the comparisons and does not change their readouts. The Overseer cancelled the planned uncapped route smoke for this reason.

**Native proxy definition.** The native renderer reports no usable draw counts: perf.csv `draw_calls` is 0, and native-frames maxes at 8. The proxy therefore counts new `Native GPU:` shader / surface / adopted-texture / AOT-miss lines in game.log after the front end has gone idle. The Overseer accepted this proxy, labelled as a proxy.

Evidence (all in `smoke-final2/`):

| file | sha8 |
|---|---|
| console-devfinal2.txt | 47871F93 |
| console-nativefinal2.txt | B92989A7 |
| check-devfinal2.txt | 90BD9587 |
| check-nativefinal2.txt | 684E6F79 |
| verify-devfinal2.txt | 5EFF3048 |
| verify-nativefinal2.txt | E5B567D5 |
| check_final2.py | 151A8E4C |

## Part 2: first-3D kit `smoke-final2/RUN-SMOKE3D.cmd`. Result: ALL PASS, both arms reached first 3D (native by proxy)

The Overseer opened the kit on the visible desktop at 16:47:52 (user approved). Results are at the end of this part.

The kit is modelled on M3's #33 row 3 kit (`RUN-ROW3.cmd` / `row3-run.ps1`). That kit reached first 3D (A3D) with the virtual-pad attract route.

Kit files:

| file | role | sha8 |
|---|---|---|
| `RUN-SMOKE3D.cmd` | entry point | B0B52007 |
| `smoke3d-run.ps1` | runs both arms and the post-check | EB00943F |
| `smoke3d_post.py` | post-check | 2D84A9ED |

Route: `harness\routes\attract-long.txt`, sha8 4D35FAF4, 91 steps:
1. `wait_first_frame`;
2. sleep 50 s;
3. START, A, A (8 s apart);
4. idle marks every 10 s.

**Preconditions.** A real run refuses with exit 3 on any of:
- verify-bins FAIL;
- a MANIFEST sha256 that does not match the pin;
- `perf-notes\WINDOW-HOLD.txt` present;
- day launcher state `waiting-for-quiet` or `running`;
- a game already running;
- an Agent 8 runner active;
- a hidden desktop, unless the word `allowhidden` is given.

**Arms.** Two arms run in sequence, with a 20 s settle between them:
1. `final2-3d-xenos` on `devfinal2-bin`;
2. `final2-3d-native` on `nativefinal2-bin`.

Each arm runs `harness\run-game.ps1 -BinDir <bin> -Seconds 240 -GpuLog -Tag <tag> -RunsRoot smoke-final2\runs -InputScript attract-long.txt`, with no -Cvar and no -Env:
- the harness itself sets only `LEGO_NATIVE_FRAME_METRICS` and `AGENT3_VPAD`, plus `--input_backend=xinput`;
- `-GpuLog` only reads NVML into gpu.csv;
- the game is closed with WM_CLOSE at 240 s;
- the kit stops after any arm whose exit code is not 0.

**Post-check.** `smoke3d_post.py` writes `smoke-final2\post\smoke3d-post-<stamp>.txt`. Pass criteria, per arm:
- clean exit: exit 0, WM_CLOSE, no WER, crash events or dumps;
- plain default: no cvars, env only the harness's own;
- no extra game args;
- route:
  - the pad dll was loaded by the game pid;
  - no error and 0 timeouts;
  - first frame, then START/A/A, all OK;
  - pad reads > 0;
  - a step ran within 12 s of the close;
- first 3D:
  - xenos: perf.csv draws ≥ 600, then ≥ 60 s more run;
  - native PROXY: ≥ 5 new Native GPU shader/surface/texture lines after the `idle-10` mark, then ≥ 60 s more run; gpu.csv utilisation before/after is reported as info;
- 0 `d3d12_pipeline_creation_no_wait` lines;
- check-defaults (`--mode xenos` / `--mode native`) PASS. Rotated logs are joined first.

**Expected timing.**
- Xenos A3D comes ~86-105 s after launch (s33 attract runs: perf 82-101 s).
- Native shows new GPU activity from ~142 s (the earlier bgate-rev-native3d attract run).
- 240 s covers native up to ~180 s plus 60 s.
- Total: about 2 × (240 s + ~30 s close/teardown/analysis) + 20 s settle + post ≈ **10 min**.

**Dry run** (`RUN-SMOKE3D.cmd dryrun`, 16:26): ALL PASS, exit 0. It covered:
- verify-bins: both PASS;
- both MANIFESTs match their pins;
- day launcher state `waiting-for-go`, so it would not block a real run;
- run-game `-DryRun` exit 0 for both arms (8 and 9 files linked; virtual pad found; 91-step script parsed);
- `smoke3d_post.py` replayed on the old xenos run `s33-offsf`. Route PASS and first 3D at perf 97.7 s PASS; its expected FAILs are the old run's cvar and the old bin's defaults;
- dryrun-runs removed afterwards.

The dry run's shell was on a hidden desktop. The real run is meant for the visible desktop; `allowhidden` is the only override.

### Results (real run 16:47:52-16:56:27, desktop `Default`): RESULT ALL PASS, kit exit 0

Pre-checks at launch:
- verify-bins PASS for both bins; both MANIFESTs match their pins;
- day launcher `waiting-for-go`;
- no game running;
- desktop `Default` (visible).

| check | xenos (devfinal2-bin) | native (nativefinal2-bin) |
|---|---|---|
| run dir (`smoke-final2/runs/`) | `20261125-164755-final2-3d-xenos` (run.json D7574619) | `20261125-165219-final2-3d-native` (run.json AC451A58) |
| launched | 16:47:54 | 16:52:18 |
| exe sha256 (verify-bins PASS) | 6C8E281156CCE828… | 090A420BA16797A1… |
| clean exit | PASS: 0x0, WM_CLOSE 0.63 s, no WER, 0 crash events, 0 dumps | PASS: 0x0, WM_CLOSE 0.89 s, no WER, 0 crash events, 0 dumps |
| plain default / no extra args | PASS: cvars {}, env = harness's own only | PASS: cvars {}, env = harness's own only |
| route | PASS: pad loaded by the game pid, 0 timeouts, first frame + START/A/A ok, 38 pad reads, a step ran at the close | PASS: same, 152 pad reads |
| first 3D | **PASS**: perf.csv 625 draws at perf 78.9 s (frame 4728, ~83 s after launch); max 15746 draws; 158.6 s more run after it | **PASS (PROXY)**: 199 new Native GPU lines after `idle-10`, the first at 95.0 s after launch; 145.1 s more run after it |
| `d3d12_pipeline_creation_no_wait` lines | PASS: 0 | PASS: 0 |
| check-defaults | PASS (`--mode xenos`): all 13 keys `default`; full back-off line ×1; no OFF line; 0 bad strings | PASS (`--mode native`): all 11 keys `default`; miss cache ON (build default) ×1; C1 blocked (native) ×1; 0 back-off lines; 0 bad strings |

**Native proxy, supporting info.**
- Native GPU activity lines per 20 s after launch: 0-20: 47, 80-100: 70, 100-120: 24, 140-160: 67, then 2-17 per 20 s up to 240.
- perf.csv median frame time stays at 4.16 ms up to 80 s, then rises: 4.40 ms (100-120), 24.25 ms (120-140), then 6.6-12.5 ms. That is consistent with the attract moving from the front end into 3D content.
- gpu.csv utilisation median: 56 % before the proxy point vs 58 % after (info only).
- The plain boot (part 1) showed none of this after 20 s.

**Route coverage.** steps_done is 43/91, "halted", with the last mark at idle-150. This is by design: `-Seconds 240` closes the game during the attract route's idle marks, which run to idle-380. Every step before the close ran, and START/A/A, the only inputs, all ran OK.

**Expected vs actual timing.**
- Xenos first 3D at ~83 s after launch, just under the expected 86-105 s.
- Native first 3D at 95 s, earlier than the expected ~140 s.

**Info only (untimed run).**
- GPU during xenos: P0 in 97.4 % of samples; thermal limit flagged in 45 % of samples, temperature median 86 °C.
- GPU during native: thermal 0 %, median 79 °C.
- There is no timing claim from this run.

Evidence:

| file | sha8 |
|---|---|
| `smoke-final2/post/smoke3d-post-20261125-164752.txt` | 80E2C226 |
| `smoke-final2/logs/smoke3d-run-20261125-164752.txt` | 64CD2804 |

**Verdict:** both final2 bins boot with their defaults intact, take pad input, reach first 3D (native by the accepted proxy), log 0 no_wait lines and exit cleanly.
