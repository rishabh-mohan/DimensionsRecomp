# M8 S5 runner: rating (DRAFT body; finalize after window-s5/matrix final)

## What I checked (stable parts)
- run-timing 72B8C69C (diff BBF5265F vs bench/agent8/run):
  - -InputScript/-VPadDll: pre-checks exit 1 before any run dir; bin dir refused if it has its own xinput1_4.dll; DLL copied into the run dir only; --input_backend=xinput; env AGENT3_VPAD. vpadhost ResetRun on Start() (in-process matrix runs OK).
  - -GpuLog: NVML 1 Hz in the sampling loop; Get-GpuTempC f[3] = temp (LdNvml.Sample order pstate,gr,mem,temp).
  - Cooldown: before the RAM check and before New-RunDir; no sensor -> cooldown_no_sensor, timeout -> cooldown_timeout; flagsInfo only (never VOID/excluded); run.json cooldown record has met/timed_out.
  - Kills: no new kill sites. Existing: $p.Kill (own game, Close-GameTimed after timeout), $drv.Kill, $sysDrv.Kill (own children). window-s5 none; score3d none.
  - crash_events (L621-627): Get-WinEvent Application, Id 1000/1001/1002/1026, StartTime = run start - 2 s, filtered on 'legodimensions.exe' or the decimal pid, inside try{} (failure -> empty). Read-only.
  - close_method/close_seconds/close_sent_s from Close-GameTimed (timing-env L66-95): clean = posted>0, not killed, exited. close_sent_s ParseExact uses the same culture/format as the ToString at timing-env L72.
  - dumps (L863) lists every collected .dmp incl. foreign; foreign_crash_dumps lists the foreign ones (L761); M12 gates B98369FB subtract foreign (L200-206).
- run-matrix 8D647918 (diff EDEAD1E9): cap validation 0-1000 whole; cap + framerate_limit/native_fps_limit cvar/env refused; cooldown_temp_c 0 or 30-95; start3d >= reach3d; Get-CapCvar native -> native_fps_limit=N else framerate_limit=N, 0 passed explicitly; Add-Score3d per run, failure -> s3d_status ERROR; per-arm repeats existing.
- score3d 94612E3E: reached >=600, anchor 1.0 s all >=1500, span 120, VOID rules; write_runjson tmp + os.replace in run dir only.
- TEST-OUTPUT D9D3979C: parse 0 errors x3; window_start_s matches M12 expected on 3 runs (diff 0.00); negative validations fire; PlanOnly; dryrun verify-bins PASS both pins; hidden desktop -> real run refuses.
