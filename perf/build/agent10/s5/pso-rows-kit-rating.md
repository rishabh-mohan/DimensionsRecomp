# S5 rating: M16 PSO rows / A-B kit (RUN-PSO-ROWS)

M10, 2026-11-25 18:24. Static review only (FREEZE active; nothing run, no dryrun).

| File | sha256/16 | Bytes |
|---|---|---|
| build/agent16/RUN-PSO-ROWS.cmd | 8B9B7701185C14A1 | 551 |
| build/agent16/psorows/rows-run.ps1 | EC5A1CA746D57EA0 | 24963 |
| build/agent16/psorows/pso_post.py | 708AD389C8438177 | 59014 |
| harness/run-game.ps1 (context, unchanged) | C2533FDFE9A3A494 | 28270 |
| harness/guard.ps1 (context, C2 pin) | 7A71E72057A0C87F | 1436 |

Base: rexlego a8e8dc8 (read-only). Bins: pack/native4bp-bin (pin C5181520...), psobin/native4bp-pso-bin (pin CA1FB212..., built from 2.2 36ED6E02 + 2.3 r2 52341EDF).

## Verdict

**SAFE-IF R1-R5.** No kill site in the kit; the only kill is run-game's `$p.Kill()` on the PID it launched (run-game L304). The pinned dirs are only read (sha pin + verify-bins, then real copies). Every write lands under build/agent16/psorows/. The background trigger job only creates `cache/pso-stats.now` in the current arm's run dir and is always removed.

## What I checked

- **Kills / processes.** rows-run has no Stop-Process, taskkill, .Kill or Stop-Job on foreign targets. `Get-Process -Name legodimensions` is used only to refuse (L101-102) and in the trigger job to skip creating the file (L230). harness/guard.ps1 7A71E720 only defines Get-ActiveRunners (detection). run-game refuses if any game or Agent 8 runner is active (L84-94) and closes only its own `$p`.
- **Pinned dirs.** Check-Pin (L80-90): MANIFEST sha equal to the pin, then verify-bins. Sync-Copy (L61-79) makes real sha-checked copies in work/ref and work/pso, so the hard-link chain (work copy -> warm dir -> run dir) never reaches a pinned file. verify-bins re-runs on both copies after the arms (L325).
- **Game writes into linked files.** The PSO saves are temp+rename (pipeline_library.cpp L540-544 MoveFileExW, L600-609 rename), so a save replaces the run dir's link and leaves the warm dir's seed alone. Check-Warm re-hashes both seed files before every reuse of a warm dir (L296). run-game writes a fresh toml and copies the vpad DLL into the run dir only (L155-156, L174); user_data_root is `<run>/user` (L117-148).
- **Removals.** L75 (subdirs of its own cold copy), L125 (its own warm dir, links only), L249/L263 (its own dry-seed / dry-warm), L277 (dryrun-runs, only if it has no reparse point). All of them are under psorows/. None can reach a pinned dir, the real profile or another agent's dir.
- **Trigger job (L219-235, L303, L307).** It matches only `^\d{8}-\d{6}-<tag>$` dirs under psorows/runs created at or after t0-5 s, sleeps to creation+280 s, creates the file only if a game is running, and is ended by `Remove-Job -Force` after run-game returns (10 s wait). A Ctrl+C or close of the host ends the job with the session.
- **Env.** run-game splits `-Env` on ';' (Split-Items L77), strips inherited LEGO_/PLUME_ vars (L185), so arms get exactly base + extra. The env names match the code: LEGO_NATIVE_PSO_SAVE_UNLOCKED / _AUX_UNLOCKED (2.3 r2), LEGO_NATIVE_PSO_PREPARE_THREADS (HEAD L107-110), LEGO_NATIVE_PSO_ASYNC (HEAD pipeline_async.h L329). The w-ref-t4 and w2 arms are therefore real at HEAD, not no-ops.
- **Guards / stops.** Refusals (WINDOW-HOLD, day launcher `waiting-for-quiet|running`, any game, Agent 8 runner, hidden desktop) are checked at start and again before every arm (L298). A refusal or a non-zero run-game exit stops the session; no VOID or destructive action follows. Current launcher state is `waiting-for-go`, which does not match, and a launcher that exits does not refuse unless it leaves `running` in state.txt.
- **Dry run.** run-game -DryRun stops before the launch (L206-214). The kit's dry path does real copies of both bins into work/ and writes only under psorows/.
- **pso_post.py.** It reads run.json, summary.json and game.log. It writes only `--out` (psorows/post) and the selftest dir (psorows/selftest by default; fixtures are created there). No subprocess, kill or delete.

## Conditions

- **R1.** Run only after the S5 window has ended and the FREEZE is lifted, on the Overseer's GO. Run one unattended kit at a time: not alongside the M3 gameplay kit or any other runner. The "game running" refusal is checked only at arm start, so a second kit that starts mid-arm is not caught.
- **R2.** Run `RUN-PSO-ROWS.cmd <mode> dryrun` first, after the freeze (it copies both bins, which is heavy I/O), and require `DRY RUN ALL PASS`. No dryrun log exists yet (psorows/ holds only the scripts and selftest/).
- **R3.** Interactive, unlocked desktop for the whole session. A lock or a hidden desktop refuses the next arm and stops the session (fail-safe, but the session is lost).
- **R4.** P-C1 / P-C2 from 5EA81E27 still hold: ref = native4bp-bin, pso bin built from the rated diffs (pins C5181520 / CA1FB212 checked by the kit).
- **R5.** Before an after-20:00 start, check that bench/agent5/day/status/state.txt does not hold a stale `running` (it would refuse every arm).

## Findings

- **S1 (SHOULD).** The run-dir lookups (L224, L305) accept only `<stamp>-<tag>` and miss run-game's collision suffix `-<k>` (run-game L98-99). On a collision the arm's seed and trigger are lost (arms skipped, post falls back to delta lines). That is harmless but would cost arms. Allow an optional `(-\d+)?`.
- **S2 (SHOULD).** The cold copies are synced and verified only at the start and re-verified at the end (L325). An in-place write into a cold copy during the session would show only at the end (rcAll=1). Results of the arms after it would be suspect. That is unlikely given temp+rename, but re-running verify-bins before each cold arm is cheap.
- **N1 (NIT).** `Remove-Item -Force` on hard links can clear a read-only attribute on the shared file (attributes are per file, not per link). This affects work/ copies only; the content and sha are unchanged.
- **N2 (NIT).** The trigger job's game check is by name, so it would also see a foreign game. That only matters if R1 is broken.
- **N3 (NIT).** The timing arms use harness/legodimensions.toml as is (present_effect fsr, passes 1, sharpness 0.0). That is fine for A/B within one bin, but note it in the read-out if the native-fsr1 diff (E3D652D7, T1/F1) lands first.
