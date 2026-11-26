# S5 runner (M8) - staged in build/agent8/s5/, not promoted

Files vs bench/agent8/run: run-timing.ps1 and run-matrix.ps1 changed (diff-run-timing.diff, diff-run-matrix.diff);
common.ps1, timing-env.ps1, winhelper.cs, frame_summary.py, sys_summary.py, drivers\* are identical copies.
New: score3d.py, matrix-s5-baseline.json, window-s5.ps1, RUN-WINDOW-S5.cmd, PINS-S5.txt. Tests: TEST-OUTPUT.txt,
TEST-OUTPUT-2.txt (static only, no game, no runner process).

## Window (matrix-s5-baseline.json, 17:53 revision)
- Arms keyed by (bin, cap): ship60 devfinal2-bin cap 60, nat60 nativefinal2-bin cap 60, n4bp60 agent16 native4bp-bin
  cap 60 (x4 each), natU nativefinal2-bin native_fps_limit=0 (x2, info). Rotating order per round.
- One unscored cold run per bin first (no -ColdShared): every run gets its own user_data_root (common.ps1), so the game's
  shader/PSO cache is empty at every launch; the cold runs (first frame + 160 s, past the 3D anchor) only warm the OS and
  driver-level caches.
- measure_s 180 (run ends ~274 s after launch, >= 270), cooldown 72 C, timeout 90 s, estimate 45 s.
- 17 runs, ~93.5 min, worst ~106 min (every cooldown times out). Static plan, no run-matrix process started.
- Rated files: PINS-S5.txt lists sha256 + path (relative to this folder) for every kit file and the external inputs
  (route, nvml.cs, vpad dll, verify-bins.py). RUN-WINDOW-S5.cmd pins PINS-S5.txt by sha256 and checks every line before
  window-s5.ps1 starts; window-s5.ps1 repeats the check. Any mismatch refuses (exit 3).

## What changed
- run-timing.ps1: -InputScript/-VPadDll (port of build/agent3/rtpatch/run-timing.ps1; virtual pad, input.csv t_s on the
  runner clock, 0 = process start); -GpuLog (gpu.csv 1 Hz via harness\nvml.cs: t_s, pstate, gr_mhz, temp_c, power_w,
  util_gpu, throttle, epoch_s); -CooldownTempC/-CooldownTimeoutSec/-CooldownPollSec (wait before launch until the GPU
  is below the set point; timeout = flag cooldown_timeout, not a failure); run.json cooldown{}, gpu_log{}, plus the
  run-game style compat fields below.
- run-matrix.ps1: matrix keys input_script, gpu_log, cooldown_temp_c, cooldown_timeout_s, cooldown_est_s,
  start3d_draws (1500), reach3d_draws (600), span3d_s (120); arm keys input_script, cap (cap -> framerate_limit=N on
  perf/xenos arms, native_fps_limit=N on native arms; 0 = uncapped, passed explicitly). Each run is scored by
  score3d.py (s3d_* columns + gpu_* covariates in results.csv, summary3d.md), and score3d writes window_start_s,
  window_span_s, effective_cap, effective_cap_source, score3d{} into run.json.
- score3d.py: 3D reached = first frame >= 600 draws, else VOID; anchor = first frame that starts >= 1.0 s of frames
  all >= 1500 draws (sustained, as M12's S5-GATES); window = 120 s of frames from the anchor; short = VOID;
  cap mismatch (expected cap vs args / frames.csv native_fps_limit_cvar) = VOID. Times are frame starts; the launch
  clock = input.csv wait_first_frame t_s + sum of perf frame_time (same axis as s5_gates.py).

## run.json fields read by build/agent12/s5/s5_gates.py, as run-timing.ps1 now writes them
| gate field | run-timing source |
|---|---|
| exit_code | close.exit_code (numeric; the game's exit code after WM_CLOSE) |
| close_method | 'wm_close' if close.clean (posted, not killed, exited), 'killed' if killed, else 'none' |
| close_seconds | close.exit_seen_s |
| close_sent_s | close.wm_close_post_wall - process start (launch clock) |
| elapsed_s | end - start |
| wer_seen | werfault_seen (WerFault for the game pid seen during the run) |
| dumps | artifacts that end in .dmp (Save-CrashArtifacts) |
| crash_events | Application log ids 1000/1001/1002/1026 naming legodimensions.exe or the pid (same query as harness\run-game.ps1) |
| seed_xenos | -SeedCache value, null when not seeded (the matrix never seeds) |
| started_epoch_s | process start, Unix s (sys.csv epoch_s - this = launch clock) |
| pid | game pid (unchanged) |
| cvars | {name: value} from -Cvar (the cap cvar is in it) |
| input_script.dll_loaded_by_pid | [Agent3Input]::Finish() (unchanged rtpatch port) |
| cooldown.met / .timed_out | cooldown{} (also target_c, start_c, end_c, waited_s, flag) |
| window_start_s, effective_cap | score3d.py --write-runjson (run-matrix calls it per run) |
| mode | 'TIMING' (run-timing's own field; window-s5 refuses a hidden desktop, so the gate's hidden check never applies) |
