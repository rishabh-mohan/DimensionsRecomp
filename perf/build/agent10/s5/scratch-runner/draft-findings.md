draft (pre-final), 17:55
- R-S1 dumps compat field = all .dmp artifacts incl. foreign (rt L863), while rt L761 already splits own/foreign. Gates clean gate VOIDs on dumps -> foreign dump (any app) VOIDs the run. Fix: dumps = $ownArt (one line) OR M12 gate ignores foreign (gates S1). One of the two required.
- R-N crash_events: pid match is decimal \b$gamePid\b; event 1000 prints pid in hex -> pid match is effectively dead code and can false-match other numbers in foreign events (1026 .NET etc). Exe-name match is the real one. No EndTime: a late WER 1001 of the previous run lands in the next run (sequential runs in one matrix). Read-only, bounded by StartTime, inside try{}: safe.
- R-N close_method: kill attempted but failed (kill_error) -> 'none'. Better 'kill_failed'.
- close_sent_s ParseExact same culture as ToString in Close-GameTimed (timing-env L72): round trip OK.
- started_epoch_s from local Get-Date: OK.
- Stop/kill: only $p (own game), $drv, $sysDrv. No new kill sites.
- Timing: plan estimate 13 runs 74 min with 30 s cooldown/run. Final matrix 15 runs (n4bp60 x4, natU x2) and cooldown may hit 120 s timeout every run (idle floor 68-71 C, 3D 77-87 C) -> up to ~+23 min. 18:45 + ~85..108 min = 20:10..20:33. Launcher deadline 20:00, read-out 20:15.

m16 r2 own read 17:55: A1 met (AUX_UNLOCKED env, latched Open(), unset -> HEAD body); S1 fixed (Stop CAS-claims saving_, never released; Frame CAS fails after Stop; Save() itself does not touch saving_ at HEAD L325-337); N3 WARN; N4 documented in comment. Fingerprint: pipeline_library.cpp absent from CMakeLists L604-786 list (only gpu_native/*.h globbed) -> fp unchanged, accept option (a). CachePath = exe dir/cache -> separate bin dir = separate cache file, no cross-bin contamination.

launcher-exit check 17:59 (run-day.ps1 pid 24624, -StopAt 20:00, state waiting-for-go):
- deadline path L988 -> finally L1008-1016: Restore-Screensaver (saved = ScreenSaveActive 0, SCRNSAVE.EXE '' -> restore = no change; ScreenSaverIsSecure 0), Clear-Hold (own-marker HOLD only; none now), Set-Awake false (only its own thread's ES request), state 'ended'. No Stop-Tree (only for a runner it started), no Close-Programs (only at window start / GO accepted), no kills.
- run-matrix holds its own keep-awake continuous+system+display L702-708, released L830 -> launcher release irrelevant. AC standby idle = 0 (never).
- window-s5 checks the launcher only in prechecks (L63-67, refuse on waiting-for-quiet|running; 'ended' passes); guard.ps1 Get-ActiveRunners only in prechecks (L71-72). run-matrix / run-timing: no launcher/guard/state.txt reads -> nothing aborts, VOIDs or refuses mid-run on launcher exit.
- residual: window-s5 does not write a HOLD; a WINDOW-GO written before 20:00 during S5 would be picked up by the launcher (its quiet gate would most likely wait it out). Condition: no WINDOW-GO during S5.
