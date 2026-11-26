# M8 S5 gameplay runner (final package 18:01): rating

M10, 2026-11-25 18:05. Read-only review: no runner, matrix, window or game process was started.

## Files

| file | sha256/16 | bytes |
|---|---|---|
| build/agent8/s5/RUN-WINDOW-S5.cmd | 2B22FD0063C1F502 | 2237 |
| build/agent8/s5/PINS-S5.txt | BE96CED74291A7AB | 1485 |
| build/agent8/s5/window-s5.ps1 | 112FD18346F1E985 | 6853 |
| build/agent8/s5/matrix-s5-baseline.json | 5725579072D4F9DC | 2879 |
| build/agent8/s5/run-timing.ps1 (diff BBF5265F) | 72B8C69CF96CED7F | 67059 |
| build/agent8/s5/run-matrix.ps1 (diff EDEAD1E9) | 8D64791873696776 | 65607 |
| build/agent8/s5/score3d.py | 94612E3E6DAAFEE4 | 21205 |
| build/agent8/s5/SHA256SUMS.txt | E7D9AB5B (sha8) | 1649 |
| build/agent8/s5/README-S5.md | 3F83745F (sha8) | 4397 |
| build/agent8/s5/TEST-OUTPUT.txt / TEST-OUTPUT-2.txt | D9D3979C / D905976D (sha8) | 24151 / 4018 |

Base: bench/agent8/run (run-timing, run-matrix). The copies common.ps1 A8975D12, timing-env.ps1 8090AE11, winhelper.cs E5C2B44C, frame_summary.py, sys_summary.py and drivers\* are byte-identical to bench/agent8/run, and all are listed in PINS-S5.

## Verdict

**SAFE-IF C1-C5.** All four conditions are operator checks before GO; none needs a code change.

- The runner kills only processes it started.
- It never writes to the pinned bins.
- Caps are passed explicitly.
- Cooldown problems are flagged, never VOIDed.
- The 20:00 launcher exit cannot abort, VOID or refuse anything once the window has started.

## What I checked

- **Kills:** there are no new kill sites.
  - The existing ones are `$p.Kill()` of its own game after WM_CLOSE plus a 60 s timeout (timing-env L66-95), and `$drv`/`$sysDrv.Kill()`, which are its own driver and sampler children.
  - window-s5.ps1 and score3d.py contain no kills.
  - run-matrix's per-run guard (L739-747) only waits up to 90 s for a running legodimensions.exe, then marks that run SKIPPED. It never kills.
- **Pinned bins:**
  - New-RunDir hard-links the exe/dll/map files into the run dir and copies everything else. The game starts from `<run>\legodimensions.exe` with cwd = run (rt L320).
  - The vpad DLL is copied, never linked. The bin dir is refused if it holds its own xinput1_4.dll.
  - Nothing writes through the links. score3d's `--write-runjson` uses tmp + os.replace on `<run>\run.json` only.
- **Rated-file gate:**
  - RUN-WINDOW-S5.cmd hard-codes the PINS-S5 sha256 (BE96CED7…). It checks 17 files (≥17 required) and exits 3 on any change or missing file before window-s5 starts. window-s5 L37-46 repeats the per-file check for direct starts.
  - TEST-OUTPUT-2 §2 shows all 7 cases: pass; tamper of run-matrix, the json and the external route → 3; missing driver → 3; PINS edited or missing → 3.
  - The PINS lines match the hashes I computed for every package file.
- **Bin pins:** window-s5 L27-30 pins devfinal2 4A4A13ED, nativefinal2 4E5E2620 and native4bp C5181520 (MANIFEST sha256), plus verify-bins for each bin. All three bins are present.
- **Caps:**
  - The matrix gives every arm an explicit cap: ship60 → `framerate_limit=60`; nat60/n4bp60 → `native_fps_limit=60`; natU → `native_fps_limit=0`.
  - run-matrix refuses non-integer caps, caps outside 0-1000, and caps combined with a framerate_limit/native_fps_limit cvar or the LEGO_NATIVE_FPS_LIMIT env (TEST-OUTPUT §F).
  - score3d VOIDs a cap mismatch on native from the frames.csv cvar column. On Xenos, "seen" is the args only (NIT N3).
- **Cooldown:**
  - It runs before the RAM check and before New-RunDir, so no run dir exists during the wait.
  - Set point < 72 C. **The timeout is 90 s in the final matrix, not 120 s**; the 106 min worst-case estimate assumes 90.
  - No sensor → `cooldown_no_sensor`; timeout → `cooldown_timeout`. Both go to flags_info only, never VOID or excluded.
- **New run.json fields (rt L619-627, L856-865):**
  - `crash_events` comes from a read-only Get-WinEvent query on the Application log, ids 1000/1001/1002/1026, StartTime = run start - 2 s, filtered on `legodimensions.exe` or the decimal pid, inside try{}. A failure gives an empty list.
  - `close_method` maps Close-GameTimed's `clean` (posted, not killed, exited) to wm_close; killed gives killed.
  - `close_sent_s` parses with the same format and culture that wrote it (timing-env L72).
  - `dumps` lists every collected .dmp, foreign ones included. M12's gates B98369FB L200-206 subtract foreign_crash_dumps, so foreign dumps no longer VOID a run.
  - None of these fields affects run control; they are written after the game has exited.
- **Timing:**
  - Each run ends at first frame + 270 s. The sustained 3D anchor came at frame-clock 104-124 s in the smoke and offsf runs, so anchor + 120 s ≤ ~244 s, a margin of about 26 s.
  - Each cold run (ff + 160 s) passes the anchor.
  - The plan is 17 runs (3 cold), 93.5 min, worst case 106 min; with GO at 18:40 it ends ~20:14-20:26. The Overseer accepts running past 20:00.
- **Launcher exit (pid 24624, run-day.ps1 -StopAt 20:00, idle in waiting-for-go): CONFIRMED harmless.**
  - window-s5 reads state.txt once, before start (L63-67), and refuses only on waiting-for-quiet or running. guard.ps1 Get-ActiveRunners is also read only before start.
  - run-matrix, run-timing and score3d never read launcher state.
  - On its deadline the launcher only runs its finally block (run-day L1008-1016): Restore-Screensaver, Clear-Hold, keep-awake release, state 'ended'.
    - Screensaver: the saved state is ScreenSaveActive 0 and SCRNSAVE.EXE '', which is the current state, so the restore changes nothing. ScreenSaverIsSecure is 0.
    - Clear-Hold deletes only a HOLD that carries its own marker.
    - The keep-awake release affects only its own request. run-matrix holds its own continuous+system+display request from L702 until L830, and AC standby is "never".
  - Stop-Tree and Close-Programs run only around a window the launcher itself started, so they are not reached.
- **Cache methodology (Overseer's question): ACCEPTED.**
  - Each run gets its own user_data_root (common.ps1 Write-RunToml).
  - The native PSO library sits at `<exe dir>\cache\native-pso.bin` (pipeline_library.cpp CachePath). The exe is started from the run dir, so the native PSO cache is also empty at every launch.
  - Every arm is therefore equally game-cache-cold. Only OS/driver caches carry over.
  - Caveat for the read-out: I don't know whether the NVIDIA driver shader cache is keyed per exe path. If it is, the per-bin cold run does not warm later runs either. Either way all arms are treated alike.
- **Tests:** parse errors 0 in all 5 scripts. window_start_s reproduces M12's expected values on 3 runs (diff 0.00 s). The negative matrix validations fire. The static plan shows 0 errors.

## Conditions (operator checks before GO)

- **C1: start only through `RUN-WINDOW-S5.cmd` (real run) on the interactive desktop.** Before walking away, check that the window log shows:
  - `rated files ok: 17 pins match`;
  - three `MANIFEST sha256 … = pin` lines;
  - `START …`.
- **C2: four harness inputs that the window loads are not in PINS-S5.** Check them right before GO, e.g. with `Get-FileHash <f> | % Hash`, against these values (sha256/16):
  - `harness\legodimensions.toml` B763DABBE2C5FE7A: the base TOML of every run;
  - `harness\vpad\vpadhost.cs` 5D9290416F057B07: Add-Type in rt L188;
  - `harness\guard.ps1` 7A71E72057A0C87F;
  - `harness\winhelper.cs` 37619E3DA38CE249: window-s5 L74.
  - None of them has changed since 11-21/11-22. Any mismatch means hold.
- **C3: during the window, nobody writes `perf-notes\WINDOW-GO.txt` and no agent starts legodimensions.exe.**
  - window-s5 does not write a HOLD. A GO arriving before 20:00 would reach the idle day launcher.
  - A foreign game makes the next run SKIPPED, not killed.
- **C4: read-out.**
  - Runs that are SKIPPED, PROBLEM, VOID or have score3d ERROR are counted and listed, never averaged in.
  - cooldown_timeout / cooldown_no_sensor are covariate flags only.
  - natU is info only (x2).
  - The cache caveat above is stated.

- **C5 (addendum 18:04): no builds and no user input from GO until the window's DONE line.**
  - run-timing sets valid_timing=false when a build tool (clang*, lld*, ninja, cmake, dxc, cl, link, msbuild, rexglue*, codegen*, …) runs at the window marks or in the 5 s checks. Its `excluded` flag covers input_during_window, not_foreground, screensaver and power changes.
  - M12's gates (6CF65B8D L220-230) VOID a run on either one. TEST-OUTPUT-2's "flag, not VOID" is true for score3d only.
  - So psobin, an M2 diag bin, or any other compile must finish before GO or wait until after the window. The user should leave the PC alone during the window.

## Findings

- **NIT N1:** NVML is not closed on the post-run-dir exit 1 when `[Agent3Input]::Start` fails, nor on an exception between Open and the try. nvmlInit is refcounted, so in run-matrix's in-process runs this is only a leak.
- **NIT N2:** the `crash_events` pid match is decimal (`\b$gamePid\b`), but event 1000/1002 messages print the pid in hex. The pid branch rarely matches the game and can, rarely, match an unrelated number in a foreign event; such an event would then VOID the run through the gates' clean check. The exe-name match is what actually works. There is also no EndTime, so a late WER 1001 from the previous run can land in the next run. Better: match on the exe name, or on `0x{pid:x}`.
- **NIT N3:** the Xenos "cap seen" is the launch args only; there is no runtime readout.
- **NIT N4:** `close_method` is 'none' when the kill was attempted but failed (kill_error); 'kill_failed' would be clearer. The gates treat anything but wm_close as not clean, so the outcome is right.
- **NIT N5:** score3d's doc says input-script "timeouts = info", but run-timing turns timeouts and pad_reads 0 into PROBLEM, which score3d then VOIDs. The code is the stricter one; fix the doc.
- **NIT N6:** effective_cap/window_start_s exist only in runs scored through run-matrix (Add-Score3d). Standalone run-timing runs lack them.
- **NIT N7:** the overseer brief says the cooldown timeout is 120 s; the matrix uses 90 s. That is fine, but the read-out should quote 90.
