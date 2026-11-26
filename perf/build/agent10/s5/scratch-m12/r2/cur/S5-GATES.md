# S5 gameplay-run validity gates (Phase 0.2/0.3) - M12, 2026-11-25

Tool: `build/agent12/s5/s5_gates.py` (stdlib only; `python -B s5_gates.py RUN_DIR... --span S --cap 60|none|auto --route harness/routes/attract-long.txt --json OUT`; `--selftest`: 35 synthetic cases + 2 set rules + the `--runs-root` filter, all pass). `--runs-root <matrix out>\runs` adds every run dir whose run.json tag matches `--scored-tag` (default `^(?!cold-|warm\d+-).+-r\d+$`, the run-matrix scored tags `<arm>-r<k>`) and lists the skipped dirs in the header.
Read-out: `s5_readout.py` (CF1 method), plan in `READOUT-PLAN-P03.md`.
Run the gates **once over the whole set** so the set rules (host-busy median, thermal outlier per arm) see every run.

Statuses: each gate gives PASS / FLAG / VOID / NODATA. Run verdict = VOID if any gate is VOID, else FLAG if any gate is FLAG or NODATA, else PASS.
- VOID runs are dropped from the read-out.
- FLAG runs stay in the primary read-out and drop out of the sensitivity variant.

## Time axis and draws (shared by all gates)

- **Time:** t(row i) = input.csv `wait_first_frame` t_s + Σ perf.csv frame_time_us[0..i], in seconds from launch.
  - Checked against close_sent_s (axis − close: xenos +0.97 s, native +0.51 s on smoke) and against input.csv perf_rows (≤0.5 s).
  - `align` gate: FLAG if either check is off by more than 3 s, or the wait_first_frame row is missing.
- **gpu.csv t_s** is taken as seconds from launch.
- **sys.csv** is placed by epoch_s − run.json started_epoch_s.
- **Draws:**
  - xenos: perf.csv draw_calls.
  - native: native-frames.csv (run-timing.ps1 `-Frames native`), else frames.csv (run-game.ps1), because native perf.csv draw_calls is always 0. The frames↔perf row offset is fitted on interval_ms vs frame_time; it came out +1 on smoke, with a median difference of 0.001 ms. Without perf.csv rows, frame times come from interval_ms (offset 0).
- **Arms:** keyed by (bin dir basename, cap arm), so 2 or 3 bins all work (e.g. native4bp next to nativefinal2).

## Gates

| gate | source | VOID | FLAG / NODATA | PASS |
|---|---|---|---|---|
| **clean** | run.json exit_code, close_method, wer_seen, dumps minus foreign_crash_dumps, crash_events, exited_early; own-pid `legodimensions.exe.<pid>.dmp` in run dir | any of these | – (foreign dumps are info) | exit 0, wm_close, none |
| **runner** | run.json status, valid_timing, excluded / flags_excluding (run-timing.ps1; absent on run-game.ps1 runs → PASS n/a) | status ≠ OK (as score3d); valid_timing false; excluded true | – (flags_info shown) | status OK, valid_timing true, not excluded |
| **cold** | run.json seed_xenos | seeded (unless `--warm`) | – | null |
| **3d** (3D reached, and when) | draws | no frame ≥600 (M8's 3D check), or no anchor | anchor > 90 s after the last press; anchor sustain < 0.5 (share of frames ≥600 in the 10 s after the anchor); runner-reported window start ≠ gate anchor by > 1 s | anchor found. Reported: t3d, anchor t, anchor − last press, anchor − t3d, first ≥600/1000/1500/2000 times |
| **span** (scored span) | perf axis, draws | SHORT: perf ends before anchor + span + 2 s; or the window runs ≥5 s past the end of the attract 3D | window runs 0-5 s past the end of 3D | covered, and the end of 3D falls after the window or is not seen |
| **input** (script completed) | run.json input_script, input.csv | script error; timeouts; pad dll not loaded by the game pid; press not ok; press count ≠ route (3); any press inside the window; script dead before window end − 12 s (script step rows only; vpadhost's `end`/`error` rows are excluded); runner field `input_during_window` | – | all of the above ok. "Completed" means steps_done = total or stop; halted by the close after the window also counts as ok |
| **cooldown** | run.json `cooldown` record (tolerant: met / ok / reached, timed_out) | – | no record; timed_out; met = false | met. Always reported: first gpu.csv temp and temp at the anchor |
| **thermal** | gpu.csv throttle bits in the window | HW brake share (0x8 HwSlowdown, 0x40 HwThermal, 0x80 HwPowerBrake) > 0.05 | set rule: \|thermal share − arm median\| > 0.25; gpu samples < 80 % of span | otherwise. The thermal share (0x20 \| 0x40) is reported as a covariate and labelled `thermal_limited` above 0.10; GPU util / clock / W / temp are medians of the 1 Hz window samples |
| **host** (host-busy, as before) | sys.csv rows in the window | ac = 0, batt_saver = 1, scheme or overlay change, screensaver, fg_game = 0 (interactive desktop), idle_s reset (user input), game_alive = 0 | nongame_cores mean > set median + 1.0 core (≥3 runs; w6/CF1 rule); hidden-desktop mode; NODATA if there is no sys.csv | otherwise |
| **cap** (capped arm near 60) | runner effective cap (run.json `effective_cap` / `fps_cap_effective` / …), else cvars framerate_limit / native_fps_limit, else frames.csv native_fps_limit_cvar; window fps | cap60: reported cap ≠ 60, or fps > 61.5 (cap not applied). Uncapped: reported cap ≠ 0 (`--native-default-ok` accepts the native default 240) | cap60 without any reported cap; uncapped run that looks pinned (59-61 fps with ≥80 % of frames at 16.0-17.4 ms); NODATA if no window frames or window frame-time sum 0 | cap60 at 57-61.5 fps = "at cap"; below 57 = "below cap: GPU-bound", reported as info and **not** a void |
| **align** | see above | – | > 3 s mismatch | ok |

### Anchor: use a sustained ≥1500 anchor, not the first ≥1500 frame

> [!IMPORTANT]
> In offsf (20261125-071741, xenos), single frames with ≥1500 draws appear at 108.6-111 s, inside the 790-draw pre-3D phase (1-5 frames per second). Full 3D starts at **128.5 s**.
> The literal rule "first frame ≥1500" would start the offsf window about 20 s early, in the pre-3D phase, where xenos runs at 60 fps. That biases xenos fps upwards.

- **Gate default:** `--anchor-mode sustained`. The anchor is the first frame that starts ≥1.0 s in which every frame has ≥1500 draws. The literal rule is still available with `--anchor-mode first`.
- **Effect on the runs checked:**
  - smoke xenos, smoke native and ond: no change (107.98, 125.49, 112.30 s);
  - offsf: 108.6 → 128.5 s.
- **Ask for M8:** use the same sustained rule in the runner and write the window start in run.json (e.g. `window_start_s`). The gate then cross-checks it (more than 1 s apart → FLAG).

### End of the attract 3D

- **Detectors** (the earlier one wins):
  1. **Low band:** ≥5 s with every frame below the renderer's low band. Xenos 1000: after the attract, xenos sits at 680-950 draws, then flat at 766. Native 120: native 3D scenes run at 155-700 draws.
  2. **Flat:** ≥20 s with draws max − min ≤ max(10, 5 %).
  - Draw thresholds alone don't work for native, because its 3D scenes go down to 155 draws.
- **Measured from the sustained anchor:** the 3D lasts **155.5 s** in both offsf (128.48 → 283.99 s) and ond (112.30 → 267.78 s).
- **Consequences:**
  - With `--span 120` there is ~35 s of slack after the window.
  - `--span 180` is VOID on both runs (24.5 s past the end).
  - The native end of 3D has not been seen yet (the smoke run closed at 240 s). The first P0.3 native runs will show it.

### Why thermal is a covariate, not a void (and only HW brakes void)

- **Xenos is thermal-limited by its steady state, not by accident.** Xenos is GPU-bound on this MX570 (util 88-91 %). SwThermal (0x20) is set in 52-77 % of window samples on every xenos run checked: smoke 0.77, offsf 0.52, ond 0.62. Native smoke showed 0.00.
  - Voiding on it would void every xenos run.
  - Flagging on an absolute threshold would flag every xenos run, which makes the "without flagged runs" variant empty.
- **So:**
  - the share is reported per run and per arm as a covariate;
  - a run is FLAGged only when it is a within-arm outlier (more than 0.25 from the arm median);
  - the GPU clock, W and temperature medians show the effect directly.
- **HW brakes:**
  - 0x80 HwPowerBrake comes from an external signal (AC adapter/EC);
  - 0x8 and 0x40 are hardware slowdowns.
  - These point to an abnormal host state rather than the load, so a share above 5 % is a VOID. None were seen in any run checked.

### Cap gate

Xenos is GPU-bound in 3D at ~34-46 fps, so it will read "below cap: GPU-bound" in both arms. Cap60 vs uncapped is expected to differ only for native (uncapped native smoke: 75-82 fps).

`--cap auto` (recommended for P0.3, one invocation over all arms): a reported cap of 60 puts the run in the cap60 arm; anything else (none, 0, or the native default 240) puts it in the uncapped arm, where a non-zero cap is a VOID unless `--native-default-ok` is given.

## Runner contract assumptions (for M8 to confirm; the gates parse these tolerantly)

1. **sys.csv** must be written (sys-csv.ps1, with the nongame_cores column). Without it, host-busy, battery, foreground and user input are NODATA, and NODATA gives a FLAG verdict.
2. **Cooldown record** in run.json, e.g. `"cooldown": {"target_c":…, "start_c":…, "end_c":…, "waited_s":…, "timeout_s":…, "met":true|false, "timed_out":true|false}`.
3. **Effective cap per run** in run.json (`effective_cap`: 60 or 0), plus the cvars. For the native uncapped arm, write native_fps_limit=0 explicitly (the native default is 240).
4. **Window start** in run.json (`window_start_s`, seconds from launch), using the sustained ≥1500 anchor.
5. **gpu.csv t_s** zero is at launch, the same as run-game.ps1.
6. **-Seconds** ≥ native anchor (~125 s, up to ~+16 s idle-exit variance) + span + 2 s margin + slack. That is **≥ 270 s for span 120**. Native smoke at 240 s was SHORT for span 120.
7. **Mode:** timing on the interactive desktop (fg_game meaningful). A hidden-desktop mode gives host FLAG.

## (c) Test on the existing runs

Outputs in this folder: `s5-gates-smoke-span{120,110,60}.{txt,json}`, `s5-gates-smoke-span110-cap{auto,60}.{txt,json}`, `s5-gates-offsf-ond-span{120,180}.{txt,json}`, `s5-gates-m10synth-native.{txt,json}`, `s5-gates-selftest.txt`, `s5-readout-selftest.txt`, `s5-readout-smoke-span110.txt`. Regenerate with `scratch/run_all.ps1`.

| run | span | verdict | notes |
|---|---|---|---|
| smoke xenos (devfinal2) | 120 | FLAG | anchor 107.98 s (t3d 82.26, pre-3D 790 plateau); window fps 45.6, p99 51.9 ms, 1 % low 79.6 ms; thermal-limited 0.77; GPU medians util 95.0 %, 1357 MHz, 26.51 W, 87 °C; cooldown no record (58 °C at start); host NODATA (no sys.csv) |
| smoke native (nativefinal2) | 120 | **VOID** | SHORT: perf ends 240.6 s < window end 245.5 + 2 (needs -Seconds ≥ ~249) |
| smoke native | 110 | FLAG | anchor 125.49 s (t3d 122.11); fps 76.8 uncapped (native default cvar 240), p99 52.4, 1 % low 69.6; thermal 0.00; cooldown no record (70 °C at start); host NODATA |
| smoke both | 60 | FLAG | as above |
| smoke, `--cap auto` | 110 | xenos FLAG, native **VOID** | run.json effective_cap 0 (xenos) → uncapped arm; native effective_cap 240 (default) → uncapped arm → VOID "reported cap 240 on uncapped arm" (P0.3 needs native_fps_limit=0 written explicitly; `--native-default-ok` waives this, compared numerically since 18:00) |
| smoke, `--cap 60` | 110 | xenos **VOID**, native **VOID** | xenos: reported cap 0 ≠ 60 (also "below cap: GPU-bound info", 45.95 fps); native: cap 240 ≠ 60 and 76.8 fps > 61.5 → cap not applied |
| M10 synth native (B1 repro: perf.csv + `native-frames.csv` only) | 110 | FLAG | draws from native-frames.csv (offset +1): 3d PASS anchor 125.49, span PASS, cap PASS with `--native-default-ok` (76.79 fps); cooldown no record, host NODATA. Before the B1 fix: 3d VOID / span VOID / cap NODATA |
| offsf (xenos) | 120 | FLAG | sustained anchor 128.48 (first ≥1500 at 108.6 was transient); end of 3D 283.99, 35.5 s after the window; host NODATA (older sys.csv, no nongame_cores) |
| ond (xenos) | 120 | FLAG | anchor 112.30; end of 3D 267.78; host FLAG (hidden-desktop run) |
| offsf, ond | 180 | **VOID** | window runs 24.5 s past the end of 3D |

On these runs every gate fires for the expected reason. None of them is a timing run (functional harness, no sys.csv or older sys.csv, no cooldown, no cap config), so no run reaches PASS.
