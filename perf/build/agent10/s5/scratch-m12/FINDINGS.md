# E10.2 pre-read of M12 S5 gates + read-out (for M10)

Hashes (first 8): S5-GATES.md 65B9073D, s5_gates.py FCC073A2, s5-gates-selftest.txt 79C348D8,
READOUT-PLAN-P03.md 7BF8437C, s5_readout.py 8FCFDDB1, s5-readout-selftest.txt F55AC6AD: all match.

Runner reviewed: build/agent8/s5/run-timing.ps1 at 909 lines, sha256 72B8C69C (17:44 local; M8 is
editing it live and added an "S5 compat" block at L856-865 and cooldown met/timed_out at L227-228).

## BLOCKER
- B1 native draws: s5_gates.py:137 reads only frames.csv; run-timing -Frames native writes
  native-frames.csv (run-timing.ps1:274-275; matrix nat60/natU use frames "native"). Draws fall back to
  perf.csv (0 on native) -> 3d VOID "no frame >= 600 draws", span VOID, cap NODATA on every native run.
  Reproduced: out-gates-synth-native.txt (smoke native run, frames.csv renamed native-frames.csv).
  Native cap column (native_fps_limit_cvar, L456) lost too. score3d.py:114 already tries both names.

## SHOULD
- S1 foreign dumps VOID clean: run.json dumps = every .dmp in $artifacts (run-timing.ps1:863), which
  includes foreign dumps (L758-761, "not a problem" L823); Save-CrashArtifacts copies them into the run
  dir, so s5_gates.py:187 and :193 VOID. Use dumps minus foreign_crash_dumps, and own-pid .dmp only at :193.
- S2 runner verdict ignored: gates never read status (PROBLEM: dialogs, stall, not responding, kill),
  valid_timing, excluded/flags_excluding (run-timing.ps1:852-853, 900). score3d VOIDs on status != OK.
- S3 GPU covariates: READOUT-PLAN-P03.md section 3 says median of 1 Hz NVML samples; s5_gates.py:392-398
  computes means.
- S4 input alive check: s5_gates.py:337 max t_s over all input.csv rows includes vpadhost's 'end'/'error'
  row written at Finish() after close (harness/vpad/vpadhost.cs:533). Exclude those cmds.
- S5 crash: frame_metrics returns fps None when window frame-time sum is 0 (s5_gates.py:92); cap gate then
  compares None > float (s5_gates.py:477, 486): TypeError.
- S6 plan vs matrix: plan run list has a xenos uncapped arm (X60 N60 Xu Nu); matrix-s5-baseline.json has
  ship60, nat60, natU only. Uncapped arm then has no devfinal2 reference -> no bin-vs-ref contrast uncapped.

## NIT
- cap-auto tolerance +-0.5 around 60 (s5_gates.py:470) not in S5-GATES.md.
- cap-auto edges: "60"/60.0 -> cap60; None/0 -> uncapped; non-numeric string -> uncapped, never VOID
  (rep_n None, :484); True -> fnum 1.0 -> uncapped VOID; 240 -> VOID unless --native-default-ok.
- cvcap = cv.get('framerate_limit', cv.get('native_fps_limit')) (:453) prefers the xenos key.
- ncap window mapping hard-codes +1 (:456) instead of the fitted offset.
- `close_sent_s or elapsed_s` (:493): 0.0 falls through.
- started_epoch_s / close_sent_s are taken from $start (run-timing.ps1:310), before Start-Process (L320)
  and the launch stopwatch (L325): host window and align drift offset by the Start-Process latency.
- hidden-desktop test looks for 'hidden desktop' in mode (:430); runner mode is TIMING/PROFILE ONLY;
  desktop is timing_env.desktop / on_timing_desktop. window-s5 refuses hidden desktops, so low impact.
- set rules include VOID runs in the host median (:516).
- doc uses PASS/FLAG/VOID/NODATA (no FAIL/WARN); NODATA rolls up to FLAG.
- gates selftest writes scratch/ next to the script (:670), i.e. into agent12's folder.
- score3d span includes the frame crossing T1; gates use tend <= T1 (one-frame difference).
- plan VOID list omits game_alive=0.
- readout: paired() drops 0 values via truthiness (s5_readout.py:66-67), so thermal_share 0 gives no
  paired CI; T975 falls back to 2.0 for df > 15 (:73); duplicate round numbers overwrite silently;
  pct CI = diff CI / point median of B (not a ratio CI). Bootstrap index math symmetric, fixed seed: OK.
  VOID exclusion and CI-excludes-0 wording match the plan.

## Resolved by M8's live edits (were blockers against the 889-line runner)
close_method/close_seconds/close_sent_s/elapsed_s/started_epoch_s/wer_seen/crash_events/dumps/seed_xenos
(run-timing.ps1:857-864), cvars dict (L865), cooldown met/timed_out (L228). Close-GameTimed returns
clean (timing-env.ps1:91), so close_method maps correctly.

## Selftests and test runs
Gates selftest PASS (all cases + host-set + thermal-set); readout selftest PASS (6 checks). All 8 test
invocations reproduce M12's reference outputs line for line (path lines excluded); no stderr.
