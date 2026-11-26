# M3 gameplay kit: delta rating (G5 of m3-gameplay-kit-rating.md 1431C7E3)

M10, 2026-11-25 18:40. Static review only (FREEZE + QUIET MODE): file reads plus hashes of small kit files. Nothing was run.

## Files (build/agent3/gameplay/, hashed 18:36; all match the Overseer's provisional list)

| file | sha256/16 | bytes | state |
|---|---|---|---|
| gameplay-run.ps1 | A9B7C1268E765A83 | 22121 | changed, read in full (280 lines) |
| gameplay-watch.ps1 | 2950A4471C1271BC | 7743 | changed, read in full (117 lines) |
| RUN-EXPLORE.cmd | 7AE1F684B6CACD63 | 3195 | changed, read in full |
| RUN-GAMEPLAY.cmd | 27B2CC42A527C8AD | 3018 | changed, read in full |
| gameplay_post.py | B12A7E11CBB1A9B2 | 15811 | unchanged since 1431C7E3 |
| gen_gameplay_route.py | 6353647F0906AD2E | 7011 | unchanged since 1431C7E3 |
| tags/batman.bin | 798ECC30B1920F38 | 180 | new kit copy |
| tags/gandalf.bin | 44E16868B3B5AD6F | 180 | new kit copy |
| tags/wyldstyle.bin | 6ED54B855D8624BC | 180 | new kit copy |
| tags/tags.json | 013BD0D72A8B6B51 | 986 | not read at run time (only `ldtag.py make` writes it), so no pin needed |

explore-route.txt and gameplay-route.txt don't exist yet; M3 regenerates them after the freeze.

## Verdict

**SAFE-IF**: G1-G4 from 1431C7E3 still apply. G5 is now P1-P4 below. Every pin is currently UNSET and the route files are missing, so both .cmd files refuse with exit 3 as they stand. That's the right failure mode.

## What I checked

**gameplay-watch.ps1 (S1 is fixed):**
- At each mark it compares GetForegroundWindow() with the game's MainWindowHandle (L102). When the game isn't foreground it logs "game not foreground: no shot" and moves on (L105), so it never saves another window's pixels.
- It also skips a minimised window or an empty area (L103).
- It finds the game with `legodimensions` and `Path -like "<run>\*"`. The run dir must be under -RunsRoot, match `*-<Tag>*` and have been created at or after the watcher's start minus 5 s (L90-93).
- It kills nothing and starts no processes.
- It writes only to -OutDir: watch-<arm>.log, index.csv and the JPEGs. It reads input.csv with FileShare ReadWrite|Delete.
- It exits 5 s after the game is gone, or at -Seconds+240.

**gameplay-run.ps1 (S2-S4, N1-N3):**
- **Lock:** logs\gameplay.lock is held with FileShare None (L64-65), so a second instance exits 3.
- **Sync-Copy:** it does real copies and FAILs on extra subdirs instead of deleting them (L72-87).
- **Guards (L113-136):** WINDOW-HOLD, WINDOW-GO, the CIM command-line guard (L118), the day-launcher state, a running game, guard.ps1, a hidden desktop and RAM < 6 GB.
- **Tags:** the sidecar gets the kit's tags dir via `--tags-dir` (L160).
- **holdwatch:** started with -FindTimeoutSec 300 (L242).
- **Helpers:** held through their process handles; the reap Kill()s those handles (L258).
- **Stop-Ours (L209-229)** runs in finally, only when `$armsDone` is false (L267-268):
  - It only touches `legodimensions` whose Path is `-like "$runsRoot\*"`. `$runsRoot` comes from $PSScriptRoot, so it is absolute, and the `\*` stops a sibling dir from matching by prefix.
  - It takes the handle, re-checks StartTime >= run start - 2 s, calls CloseMainWindow, waits 30 s, then Kills.
  - It then Kills holdwatch, the sidecar and the watcher through their held handles.
- **Dryrun:** reads M16 smoke4bp runs and old agent3 runs read-only. It deletes dryrun-runs only after a reparse-point check.

**RUN-EXPLORE.cmd / RUN-GAMEPLAY.cmd pin check:**
- Both files carry the same 13 GPPIN entries, as `<sha>|<WS-relative path>`. The WS is `%~dp0..\..\..`, resolved with Resolve-Path.
- It is fail-safe in every case I checked:
  - `UNSET` never matches a hash.
  - A missing file hashes as `MISSING`.
  - The count must be exactly 13, so a stray inherited GPPIN_xx also refuses.
  - Any PowerShell error exits non-zero, `if errorlevel 1` catches it, and the .cmd exits 3.
- `pincheck` exits right after the check (0 or 3) and launches nothing.
- `dryrun` and `pincheck` skip the 15 s timeout.
- The pinned gameplay-run.ps1 is the same file that `%GP%gameplay-run.ps1` then runs. The gap between check and run is negligible.
- The -Command string has no `%` or `!`, and it isn't inside a parenthesised block, so cmd parsing is safe.

## Conditions (replace G5)

- **P1:** routes regenerated after the freeze, and `gen_gameplay_route.py --check` exits 0.
- **P2:** the pins are filled in (both .cmd files identical, including the additions in S1), and `pincheck` exits 0 for both.
- **P3:** tamper tests on a scratch copy: untouched gives 0; one byte appended to a pinned file gives 3; a missing ldtag.py gives 3.
- **P4:** dryrun is ALL PASS, with its refusal notes logged. The pinned set is re-hashed and sent to me for a final hash match before the GO.

## Findings

- **S1 (SHOULD), pin coverage.** The waiter pins only the .cmd, but gameplay-run also runs or loads these unpinned files:
  - harness\run-game.ps1 (L43)
  - harness\guard.ps1 (L127, dot-sourced)
  - harness\winhelper.cs (L130, Add-Type)
  - build\agent2\session3\verify-bins.py (L44)
  - build\agent3\vpad\xinput1_4.dll (L16)
  - run-game's own vpad host and the toml it reads

  Add them as GPPIN_14+ at the values in my earlier ratings: run-game C2533FDF, guard 7A71E720, winhelper 37619E3D, vpadhost 5D929041, toml B763DABB, verify-bins 80FF4C5F, xinput1_4.dll 309DF316. Add nvml/runstats too if run-game loads them, as M16 and M2 do. Bump the count check to match.
- **D1 (SHOULD, carried from F4EE7FC8):** the L118 guard matches `window-s5.ps1|RUN-WINDOW-S5|run-matrix` in ANY process command line, except its own pid. An agent shell that greps those names refuses the run. That fails safe but is a nuisance. Run when no agent shell is doing so, or narrow the guard to powershell/cmd processes whose command line has `-File`/`.cmd` plus the name.
- **N1 (NIT):** the `foreground` column in index.csv is now always True. It's harmless.
- **N2 (NIT):** a mark skipped as not foreground is never retried. gameplay_post.py should count those as "no shot" from watch-<arm>.log, not treat them as a failure. That is unchanged and not re-verified.
- **N3 (NIT):** an inherited GPPIN_* env var makes the count check refuse with a message that doesn't name the cause. That fails safe.
