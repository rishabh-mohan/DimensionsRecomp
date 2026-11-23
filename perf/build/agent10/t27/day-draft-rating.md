# Day-session draft (Agent 5): rating

Agent 10, 2026-11-23 05:57. This rating keeps my promise to Agent 5 (Agent 11 rates it too). Read-only: no launcher, test or game was run.

**Verdict: SAFE-IF**
1. run-day.ps1 is regenerated from the SCRNSAVE-fixed run-night.ps1. make-run-day.ps1's source pin moves from 16B90FA8 to the new sha, test-day.ps1 is re-run (27/27 plus the new screensaver test), and I delta-read the regenerated run-day.ps1 together with the SCRNSAVE fix. The current run-day.ps1 (D86F6DE0…) inherits the night bug: Set-ScreensaverNone removes `SCRNSAVE.EXE`, so run-matrix.ps1 L417 throws under StrictMode and the first GO of a day session would be refused. That makes it non-functional, not unsafe.
2. It is installed as README-DAY L136-139 says: only after the night launcher has exited, then the hashes are compared.
3. Agent 11 also rates it (README-DAY L57).

## Scope (hashes re-checked 05:54; all match Agent 5's list of 23:19)

| file | sha256 | lines | notes |
|---|---|---|---|
| launcher-ctl.ps1 | 6DDE3150… | 276 | read in full |
| RUN-DAY.cmd | 4B5489B4… | 38 | read in full; CRLF, ASCII |
| STOP-LAUNCHER.cmd | CE27332F… | 11 | read in full; CRLF, ASCII |
| run-day.ps1 | D86F6DE0… | 1018 | read the 7 `# DAY:` lines (run-day.diff) and grepped StopAt/StartBy/GraceMinutes/MaxRunHours/mutex |
| run-day.diff | 54E35C18… | 58 | read in full |
| README-DAY.md | 9D131EB1… | 147 | read in full |
| test-day.ps1 | D7DBC6EA… | 279 | results only: `results/summary-all-231151.txt`, 27/27 PASS on these hashes |
| make-run-day.ps1 | 17413F8A… | 116 | not read (the generator; its output was checked through run-day.diff) |

All 6 text files are pure ASCII. The .cmd files use CRLF.

## What I checked

- **Fail-closed entry.** RUN-DAY.cmd starts run-day.ps1 only when launcher-ctl exits 0 *and* wrote a non-empty end time (RUN-DAY.cmd L13-18). launcher-ctl runs with `$ErrorActionPreference = 'Stop'` and StrictMode 2 (L29-30), so an unhandled error exits non-zero, which means nothing starts. Unknown arguments are refused (L31). Test hooks are refused without `-DryRunTag` (L34-35), and a tag redirects the STOP file and the mutex to `status-dryrun\<tag>` (L37-43).
- **Folder gate.** A real day session runs only from `bench\agent5\day` (L194). The draft copy refuses (test d-cmd-nul).
- **Questions default to N.** Ask-YN treats EOF, no answer and 3 bad answers as N (L59-68). The return time must be ASCII `H:mm`/`HH:mm` (L77), at least 90 min and less than 14 h away (L82-83). The end time is the return time minus 15 min. The "too late" check runs before anything is stopped (L220) and again before the end time is written (L240).
- **Stopping a running launcher.** A launcher waiting for a GO is stopped without a question. When a window is running, about to start, or the state is unknown, it asks (Confirm-Stop L142-156). After the answer it reads the state again and asks again if a window has just started (L227-231, L269-273). The STOP file is written with CreateNew, so an existing one is never overwritten (L161-171). It is removed again only if it is ours, unchanged, and the launcher has ended (L185-187). The wait is capped at 5 min, and the STOP stays if the launcher hasn't ended (L177-179).
- **Mutual exclusion.** The mutex `Local\Agent5RunNight-real` is shared with the night launcher (run-day.ps1 L79), so a night and a day launcher never overlap.
- **Choosing the state.** The newest non-ended state.txt with a live pid wins (L108-119). A live launcher rewrites its `heartbeat` line every poll (the night state.txt showed heartbeat 05:55:29), so a stale state file can't win over a live one. The keys in state.txt (`state`, `heartbeat`, `mode`, `go_file`, `gos_read`, plus the window keys) don't collide with the hashtable's own `name`/`pid`/`time`/`file`.
- **End time in run-day.ps1.** `-StopAt` is required, with the format checked at L68. Deadline = `-StopAt` (L613). The latest start is the `-StopAt` time (L618). GraceMinutes is 0, so the hard stop is at `-StopAt` (L24, L851-852). A window also needs its estimate + 10 min to fit. The 14 h check is kept (L966). Test d-real-3 shows "ends at = latest start = -StopAt".
- **Other `# DAY:` lines** (run-day.diff): the header, the RUN-DAY.cmd pin, the HOLD text naming the day launcher (HOLD ownership is still by token) and 2 messages. No other change.

## NITs (none blocks)

- N1. **Public safety:** run-day.diff L1-4 has absolute paths that include the Windows user name (`git diff --no-index` of absolute paths). Make them relative before any of this is published.
- N2. STOP-LAUNCHER.cmd run from a folder other than `bench\agent5\day` can't see a day launcher's state.txt (`<own folder>\status`, L47). It then says "state unknown, a window may be running" and asks. That is the safe direction, but README-DAY L57 ("works from any folder") should say to use the installed copy.
- N3. If run-day.ps1 refuses at start after RUN-DAY has already stopped a night launcher, RUN-DAY.cmd L25 still says "Nothing was changed". The night launcher is gone at that point (it isn't restarted). This is rare, since launcher-ctl has already checked AC, the STOP file and the folder, but the message could say so.
- N4. launcher-ctl L79-81 uses naive local time, so on a DST-change day the 90 min / 14 h bounds can be off by an hour. Harmless: run-day.ps1 gets an absolute `yyyy-MM-dd HH:mm`.
- N5. Already known (README-DAY L134): (a) a night launcher closed with the X leaves its screensaver-saved.txt where the day launcher doesn't look. The user section points to the night README. (b) `\d` at run-day.ps1 L68 can give exit 3 instead of 2 for odd hand-typed input.
- N6. For the agents: Agent 12's read-out has to look in `bench\agent5\day\status\` for day windows (README-DAY L87).

## Read / sent

- Read: README-DAY.md, launcher-ctl.ps1, RUN-DAY.cmd, STOP-LAUNCHER.cmd and run-day.diff in full; run-day.ps1 by grep; the 27/27 summary; the night launcher's state.txt (format only).
- Sent: a note to Agents 5 and 11 (and 1).
