# Rating: M16 dtime kit (RUN-DTIME, detailed-timing diagnostic)

Who/when: M10, 2026-11-26 ~02:40 local. Static review, PS 5.1 ParseFile, and a scratch tamper of a .cmd copy (launch replaced by echo). No kit run.

## Files (sha256/16, bytes) - WS\build\agent16\

| file | sha256/16 | bytes |
|---|---|---|
| RUN-DTIME.cmd | 0DA3D55426022C10 | 2999 (CRLF 55/55) |
| dtime\dtime-run.ps1 | 412898CBCCF38DD6 | 16060 (read in full; ParseFile 0 errors) |
| dtime\dtime_post.py | F69B5F27CFEF2A24 | 17203 (compiles) |
| dtime\PROPOSAL-dtime-kit.md | 81788D15157A0266 | 4104 |

Base: natcmp cmp-run.ps1 (rated 4635DA35 + delta), D1 v2 guard regex, native4bp-bin MANIFEST C5181520.

## Verdict: SAFE-IF (D1-D4)

## What I checked

- .cmd: 12 pins via certutil: ps1, post, verify-bins, run-game, guard, winhelper, nvml, runstats, harness toml B763DABB, attract-long, vpadhost, xinput1_4. It launches only when PINFAIL==0 and PINOK==12; otherwise exit 3. `WS=%~dp0..\..`. Words go to the ps1 with `%*`.
  My scratch tamper (copy at the same depth, deleted afterwards): untouched -> "pins OK (12/12)" + launch; post modified -> rc 3 MISMATCH; ps1 missing -> rc 3 MISSING; nvml pin line removed -> rc 3 "11/12 matched". 4/4.
- ps1 words: no mode word = dryrun; `run` is explicit; `run dryrun` or any unknown word -> usage exit 2.
- Bin: native4bp-bin MANIFEST must equal C5181520 (full sha in the ps1), and verify-bins must pass. The real run refuses on a mismatch (exit 3).
  - The work copy (dtime\work\n4bp) is sha256-synced from the pinned dir, and only read.
  - verify-bins runs on the copy before every arm and after the arms.
  - The pinned dir is never written.
- Refusals (Get-Refusals, re-checked before every arm): WINDOW-HOLD, WINDOW-GO, day launcher busy, any legodimensions running, Get-ActiveRunners, the D1 v2 regex (powershell/pwsh/cmd only; `-File ...(window-s5|run-matrix).ps1` or `RUN-WINDOW-S5*.cmd`), hidden desktop (unless allowhidden).
- Arms: run-game -BinDir <copy> -Seconds 150 -GpuLog -RunsRoot dtime\runs -InputScript attract-long -Env <switch>=1.
  - run-game strips inherited LEGO_/PLUME_ variables (L185) before applying -Env, so each arm has exactly one switch.
  - run-game closes only its own PID.
- Cleanup: try/catch/finally Stop-Ours, active only during an arm. It kills legodimensions.exe whose ExecutablePath is under our runs root, plus our own child run-game powershell. Nothing else.
- Dryrun:
  - run-game -DryRun per arm;
  - one read-only sequential scan of the copy's exe for both switch strings;
  - post selftest;
  - dryrun-runs deleted only if it has no reparse points.
- post: reads frames.csv and game.log of the given run dirs and writes only --out. The selftest builds fake runs in a tempfile.mkdtemp and rmtrees only that. No subprocess or network.
- Writes overall: only under build\agent16\dtime (logs, post, work, runs, dryrun-runs, LATEST.txt).

## Conditions

- D1: before the first run, a dryrun ALL PASS on cmd 0DA3D554, showing both exe strings present; send me the log sha. The dryrun is heavy I/O (~500 MB copy sync + a ~316 MB exe scan), so don't run it during a timed window or a build.
- D2: interactive desktop (no allowhidden). One kit at a time. Never during or within ~6 min of a timed window: there's no in-arm WINDOW-HOLD watch (see S1).
- D3: diagnostic only: no number from these arms is used as timing or perf (LEGO_NATIVE_TIMING perturbs frame times; the arms are uncapped and run with the harness toml as is).
- D4: any file change -> re-hash, re-pin, re-rate the delta.

## Findings

- SHOULD S1: no WINDOW-HOLD watch during an arm. A HOLD that appears mid-arm is only seen before the next arm, so our game can keep running up to ~150 s after a HOLD. The RT, nops and gameplay kits have a hold job that WM_CLOSEs our game. The natcmp base doesn't, so this is consistent with the earlier SAFE-IF rating; D2 covers it. Adding the RT kit's hold job would close it.
- NIT N1: Sync-Copy removes any subdirectory of work\n4bp with `Remove-Item -Recurse -Force` and no reparse-point check. In PS 5.1, -Recurse through a junction can delete the target's contents. Nothing creates subdirs there (run-game hard-links the files into the run dir), so the risk is low. The dryrun-runs deletion already has the check; reuse it here.
- NIT N2: Stop-Ours kills with Stop-Process -Force (no WM_CLOSE first). It only runs on error or Ctrl-C during an arm. Acceptable.
- NIT N3: the post's switch window (t 70-115 s, >= 150 ms) and the BeginTiling anchor are tuned on the psorows runs. A miss gives PASS-WITH-CHECKS, not a false PASS.
