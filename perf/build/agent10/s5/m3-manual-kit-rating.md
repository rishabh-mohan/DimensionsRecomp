# M3 RUN-MANUAL kit rating

- Who/when: M10, 2026-11-25 20:25 (static review; the dryrun follows after M2's nops smoke ENDs)
- Request: Overseer 02:22Z (items 1-5)

## Files

| file | sha256/16 | bytes | note |
|---|---|---|---|
| build/agent3/gameplay/RUN-MANUAL.cmd | 9AF552191B4C6069 | 5126 | CRLF 52/52; = Overseer sha |
| build/agent3/gameplay/gameplay-run.ps1 | 06C4134C2EDFF833 | 23778 | LF; = Overseer sha |
| build/agent3/gameplay/RUN-EXPLORE.cmd | 6C45B98086EEA0AE | 5009 | re-pinned 20:21 (was 73C56B77) for the ps1 change |
| build/agent3/gameplay/RUN-GAMEPLAY.cmd | 4BE200A257DE008D | 4832 | re-pinned 20:21 |

Base: RUN-EXPLORE 73C56B77 / gameplay-run 0ED94A54 (P4 hash match, dryrun B8DF058A). The old ps1 was not kept, so no byte diff; I read 06C4134C in full.

## Verdict

**SAFE-IF** M1-M6.

## What I checked

1. **cmd vs RUN-EXPLORE (Compare-Object):** only the rem header, the "[gameplay manual]" echo labels and the launch word `manual` differ. Same pincheck block: exactly 22 GPPINs, exit 3 on mismatch, missing file or count != 22.
2. **Pins:** all 22 re-hashed, 22/22 OK. GPPIN_01 = 06C4134C; the other 21 equal my rated values (watch 2950A447, post B12A7E11, gen 6353647F, routes 249CD939/D491FF7F, tags 798ECC30/44E16868/6ED54B85, sidecar F7905A90, client E6CBE1F9, ldtag 3777FFFA, holdwatch A4A591FC, run-game C2533FDF, guard 7A71E720, winhelper 37619E3D, vpadhost 5D929041, toml B763DABB, nvml 9F6E6E3B, runstats AE6C8B0C, verify-bins 80FF4C5F, xinput 309DF316).
3. **Scratch tamper** (my copy at the same depth, launch line replaced by an echo, deleted after): untouched rc=0 "pins ok: 22"; bad hash rc=3; missing file rc=3; stray GPPIN_23 env rc=3 (PIN COUNT 23). 4/4 correct.
4. **Item 1, lock and Stop-Ours/finally can't be skipped:**
   - L44: `manual` + `explore` exits 2 before anything else.
   - L69: logs\gameplay.lock (FileShare None) is taken before any manual branch and held to process exit.
   - Refusals L106-147 are unchanged and not gated on $Manual: WINDOW-HOLD, WINDOW-GO, the D1 -File guard L124-125, the day launcher, a running game, Get-ActiveRunners, the hidden desktop, RAM < 6 GB. Route gen --check, work-copy sha checks and verify-bins still run.
   - The arm loop sits in the same try/finally (L240-283); the finally runs Stop-Ours when !$armsDone. Stop-Ours is unchanged (Path under runsRoot, StartTime >= runStart-2 s, CloseMainWindow, 30 s, Kill; helpers via held handles).
   - Manual only changes: $Seconds=1200 (L45), native arm by default (L100), tagBase gpman (L158), no -InputScript (L162), no sidecar then-mark/replace (L171), no watcher (L258), and the exit branch L284-288 (LATEST.txt, exit $rcAll, no post).
5. **Item 2, 1200 s self-close:** run-game `-Seconds` has no range cap. At the deadline it sends WM_CLOSE (LdHarness.CloseAll / CloseMainWindow) and kills after CloseTimeoutSec (L297-303). With no -InputScript, run-game copies no vpad DLL and adds no --input_backend (L164-175 run only with $InputScript), so the game uses default SDL input from the focused window. The sidecar --timeout is Seconds+240 = 1440; the post-arm sidecar wait is 240 s.
6. **Item 3, WINDOW-HOLD:** holdwatch (A4A591FC) finds the game within FindTimeoutSec 300 and then watches until the game exits, with no fixed lifetime, so it covers the full 1200 s. On HOLD it writes the marker, Stop-Process -Force, exit 2; gameplay-run sees the marker and sets rcAll=3. The loop also checks HOLD before each arm (L242).
7. **Item 4:** `manual explore` gives exit 2 (L44), before the lock or any process work.
8. **Item 5, D1 guard strings:** no new process name or command line contains window-s5, run-matrix or RUN-WINDOW-S5. The launcher is RUN-MANUAL.cmd and the tag is gpman-native, so neither the M3/M2 `-File ...(window-s5|run-matrix).ps1` regex nor the cmd-only `RUN-WINDOW-S5[^\s"]*\.cmd` regex matches. Manual also can't false-trip its own guard.

## Conditions

- **M1** After M2's smoke ENDs: `RUN-MANUAL.cmd dryrun` ALL PASS. Send me the log sha before the first real session.
- **M2** One kit at a time. Interactive desktop, no allowhidden.
- **M3** computer-cli input: before each key/click burst, take a screenshot and check that the game window is in the foreground, because keys go to the focused window. Never type into other windows. No input that changes the user's files or settings outside the run sandbox.
- **M4** Don't close the console mid-session. Closing it kills run-game and holdwatch and leaves the game running without the 1200 s close. If that happens, close the game by hand (only the process under gameplay\runs).
- **M5** Untimed/functional only: no timing or perf comparisons from manual runs. Fresh run\user sandbox per session.
- **M6** If any pinned file or the cmd changes, re-hash and send the shas. RUN-EXPLORE (6C45B980) and RUN-GAMEPLAY (4BE200A2) were re-pinned and need their own P4 re-match/dryrun before the next run.

## Findings

- NIT N1: there is no byte diff because the old ps1 (0ED94A54) wasn't kept. Keep the previous copy next time.
- NIT N2: `manual xenosonly` is accepted (xenos manual session). That's fine, but say which arm in the session note.
- NIT N3: Ctrl-C during the 1200 s goes through the finally and Stop-Ours. That's OK and better than closing the console (M4).
- NIT N4: manual mode has no post and no shots, so the run dir plus the Overseer's screenshots are the only record.
- NIT N5: Sync-Copy re-hashes ~382 MB at every start, which adds a little startup delay.
