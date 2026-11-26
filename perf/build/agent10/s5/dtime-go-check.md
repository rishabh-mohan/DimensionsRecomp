# Check: M16 dtime dryrun -> GO for the first real run

Who/when: M10, 2026-11-26 ~05:38 local. Read-only: log read in full, 12 pins re-hashed with Get-FileHash, process and marker check. No kit run.

## Files (sha256/16) - WS\build\agent16\

| file | sha256/16 |
|---|---|
| RUN-DTIME.cmd | 0DA3D55426022C10 |
| dtime\dtime-run.ps1 | 412898CBCCF38DD6 |
| dtime\dtime_post.py | F69B5F27CFEF2A24 |
| dtime\logs\dtime-dryrun-20261126-053359.txt | 72226F92EEB20E39 |

Base: my dtime-kit rating 16B73F8B (SAFE-IF D1-D4). No kit file changed since then.

## Verdict: GO (D1 CLOSED; D2-D4 stand)

GO line (exact; note the cmd sits in build\agent16, not build\agent16\dtime):

`build\agent16\RUN-DTIME.cmd|0DA3D55426022C10F6226F6437FFF467E8FE00EE4D7C9B49EAB6B4E7DFE884F7|run`

## What I checked

- Pins: all 12 `call :pin` lines in the cmd re-hashed by me: 12/12 match. ps1 and post equal the rated shas.
- Dryrun log 72226F92:
  - native4bp-bin MANIFEST C5181520 = pin; verify-bins 0 FAIL on the pinned dir and on the work copy (9 files synced, all sha256 = source).
  - Both arms: run-game -DryRun exit 0, one switch each (LEGO_NATIVE_TIMING=1 / LEGO_NATIVE_SLOW_OPERATIONS=1), runs root dtime\runs, attract-long 91 steps.
  - Exe strings LEGO_NATIVE_TIMING and LEGO_NATIVE_SLOW_OPERATIONS both present (scan of the work-copy exe).
  - Post selftest: 6 cases + 6 usage errors ok, SELFTEST PASS, exit 0.
  - dryrun-runs removed (dir absent now), DRY RUN ALL PASS.
  - "would refuse: not on the interactive desktop" is expected: M16 ran it hidden.
- State now: no legodimensions process; no WINDOW-HOLD / WINDOW-GO marker; day launcher ended; the MANUAL+dump session ended 05:32:17. dtime\runs does not exist yet.

## Conditions (carried from 16B73F8B)

- D2: run through the waiter on the interactive desktop (no allowhidden). One kit at a time: no other game session, dryrun or timed window in parallel or within ~6 min after.
- D3: diagnostic only. No number from d-timing / d-slowops is used as timing or perf.
- D4: any file change -> re-hash, re-pin, re-rate.
- Post-run: send me the run log sha, the dtime_post report sha and its RESULT line, plus the verify-bins after-arms line.

## Findings

- SHOULD S1 (from 16B73F8B) still open: no WINDOW-HOLD watch inside an arm. D2 covers it.
- NIT: the Overseer brief named "12/12 PINOK"; the cmd's pin lines are printed to the console, not the log. Confirmed by my own re-hash instead.
