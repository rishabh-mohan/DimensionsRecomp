# M3 gameplay kit: P4 final hash match, RUN-EXPLORE only

M10, 2026-11-25 19:37. This closes G5/P1-P4 of m3-gameplay-kit-delta-rating.md DC9F8DB2 for RUN-EXPLORE. RUN-GAMEPLAY gets its own P4 after the route refinement.

## Verdict

**CONFIRMED.** RUN-EXPLORE is SAFE-IF G1-G4 (from 1431C7E3), plus the run window the Overseer set (19:40-19:55).

## Hash match

**RUN-EXPLORE.cmd:** 73C56B77A1837D784FD1DEE9634CC9FD3D2DEAFA964CBC6639E285FEFBAC9B9F, 5009 B, CRLF (51 CR / 51 LF).

I recomputed every GPPIN value from the real files, and all 22 match. Each row gives sha256/8, then the WS-relative path.

| # | sha256/8 | WS-relative path |
|---|---|---|
| 01 | 0ED94A54 | build/agent3/gameplay/gameplay-run.ps1 |
| 02 | 2950A447 | build/agent3/gameplay/gameplay-watch.ps1 |
| 03 | B12A7E11 | build/agent3/gameplay/gameplay_post.py |
| 04 | 6353647F | build/agent3/gameplay/gen_gameplay_route.py |
| 05 | 249CD939 | build/agent3/gameplay/explore-route.txt |
| 06 | D491FF7F | build/agent3/gameplay/gameplay-route.txt |
| 07 | 798ECC30 | build/agent3/gameplay/tags/batman.bin |
| 08 | 44E16868 | build/agent3/gameplay/tags/gandalf.bin |
| 09 | 6ED54B85 | build/agent3/gameplay/tags/wyldstyle.bin |
| 10 | F7905A90 | build/agent3/toypad/toypad_sidecar.py |
| 11 | E6CBE1F9 | build/agent3/toypad/toypad_client.py |
| 12 | 3777FFFA | build/agent3/toypad/ldtag.py |
| 13 | A4A591FC | build/agent3/s4b/holdwatch.ps1 |
| 14 | C2533FDF | harness/run-game.ps1 |
| 15 | 7A71E720 | harness/guard.ps1 |
| 16 | 37619E3D | harness/winhelper.cs |
| 17 | 5D929041 | harness/vpad/vpadhost.cs |
| 18 | B763DABB | harness/legodimensions.toml |
| 19 | 9F6E6E3B | harness/nvml.cs |
| 20 | AE6C8B0C | harness/runstats.py |
| 21 | 80FF4C5F | build/agent2/session3/verify-bins.py |
| 22 | 309DF316 | build/agent3/vpad/xinput1_4.dll |

## Conditions P1-P4

- **P1:** dryrun log B8DF058A says "same" for explore-route.txt (287 steps, 69 marks) and gameplay-route.txt (322 steps, 56 marks).
- **P2 and P3:** I made scratch copies of the .cmd in build/agent10/gpchk/ at the same depth, so the WS resolves the same way. The launch line is replaced by `echo` + `exit /b 99`. I ran each with `pincheck`:

  | case | rc | output |
  |---|---|---|
  | untouched | 0 | "kit pins ok: 22 files" |
  | GPPIN_05 hash zeroed | 3 | PIN MISMATCH |
  | ldtag path to a missing file | 3 | "is MISSING" |
  | stray inherited GPPIN_23 | 3 | "PIN COUNT 23 not 22 (a stray GPPIN_* variable…)" |

- **P4:** the dryrun says "DRY RUN ALL PASS (1 refusal note(s))". The note is the hidden desktop: the dryrun ran in an exebox desktop. The FAIL lines in the log are the post self-tests on stand-in runs, and they are expected.

## Re-check of M3's edits (1)-(3)

1. There are 22 pins and the count check is 22. The 9 helper and harness pins are at my rated values.
2. The L117-120 guard checks only powershell/pwsh/cmd processes whose command line matches `-File "...(window-s5|run-matrix).ps1"` or `RUN-WINDOW-S5*.cmd`. At 18:40 I verified that pattern against the live window: it matched all 3 real processes and not a grep shell.
3. The count message names the stray variables.

Stop-Ours (L211-231) is unchanged: Path under runsRoot, the StartTime re-check, then the helpers through their held handles.

## Notes

- **N1:** logs/gameplay.lock (0 B) is left over from the dryrun. It is harmless: L64 opens it with OpenOrCreate, and the lock is the FileShare None handle, not whether the file exists.
