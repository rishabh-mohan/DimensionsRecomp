# RUN-DAY: install procedure (condition 2) and when the user must be away (S3T-5, M5, 2026-11-25)

## State now (checked 01:17-01:18, read only)

- Night set at its post-SCRNSAVE hashes: run-night.ps1 565D30D4, launch README B7CEBD63, RUN-NIGHT.cmd D7A0362B,
  bench/agent8/run/run-matrix.ps1 1A522CDF.
- Day draft at its rated hashes: run-day.ps1 B67EBD6C, README-DAY 9739BCF8, RUN-DAY.cmd B08645E9, test-day.ps1
  410FB2EC, run-day.diff 3D0E8753, plus make-run-day.ps1 4A96B0B9, launcher-ctl.ps1 6DDE3150, STOP-LAUNCHER.cmd CE27332F.
- `bench\agent5\day\` does not exist. No launcher process; no `perf-notes\WINDOW-HOLD.txt`.
- `HKCU\Control Panel\Desktop`: ScreenSaveActive '0', SCRNSAVE.EXE present and '' (REG_SZ), ScreenSaveTimeOut '120',
  ScreenSaverIsSecure '0'. Sane: the value exists (run-matrix's StrictMode read can't throw, and the fixed reader
  copes anyway), and it is the state the night launcher restored on 23 Nov 07:30:14.

## Conditions (RESUME §6 item 6)

1. Regenerated + tested + Agent 10 delta: closed 23 Nov 07:56.
2. Install into `bench\agent5\day\` while no launcher runs, then compare hashes: **ready, not done** (below).
3. M11's rating: **owed**. The Overseer relays it. Install only after it is SAFE / SAFE-IF and the Overseer says go.

## Install procedure (condition 2)

Tool: `build\agent5\session3\install-day.ps1` (writes only `bench\agent5\day\` and its own log
`build\agent5\session3\install-day-log.txt`; never starts a launcher, never touches the registry, `perf-notes\` or
`bench\agent5\launch\`).

1. Preconditions: M11's rating relayed; no night/day launcher running; no WINDOW-HOLD; nobody else changing
   `bench\agent5\` or `build\agent5\day-draft\`.
2. Plan check (read only):
   `powershell -NoProfile -ExecutionPolicy Bypass -File build\agent5\session3\install-day.ps1`
   Expect "checks OK" and exit 0. Exit 2 = refused, lists why, nothing written.
3. Install: same command with `-Install`. It re-runs every check, copies the 5 required files (RUN-DAY.cmd,
   STOP-LAUNCHER.cmd, launcher-ctl.ps1, run-day.ps1, README-DAY.md) and the 3 optional ones (make-run-day.ps1,
   run-day.diff, test-day.ps1; skip with `-NoOptional`), re-hashes every target file against the rated hash, checks for
   extra files, and re-checks the 4 night files. Exit 0 = all equal; 1 = a mismatch (target left for inspection, do not
   start RUN-DAY); 2 = refused.
4. After a clean install: tell M12 day windows log to `bench\agent5\day\status\` (N6; `N6-NOTE-M12.md`), and record
   the result in RESUME via M11.
5. Undo: delete `bench\agent5\day\` (nothing else is touched). Only while no day launcher runs.

The script refuses if: a draft file is off its rated hash; any night file changed; the mutex
`Local\Agent5RunNight-real` exists; a powershell runs `run-night.ps1`/`run-day.ps1` with `-File` (this also matches
test-day's dry-run launchers: fail-safe, just wait and retry); WINDOW-HOLD exists; the target exists and isn't empty.

Tested 01:20 (test target only): plan check on the real target: exit 0, nothing written; `-Install -Target
build\agent5\session3\test-install`: 8/8 hashes equal, exit 0; the same again: refused (target not empty; it also
caught a test-day dry-run launcher), exit 2; `-Target %TEMP%\x`: refused, exit 2. `bench\agent5\day\` still absent.

## Is RUN-DAY usable while the user is around? No.

The night rules (no window start at or after 06:45, exit 07:30) are **not** RUN-DAY's: with `-StopAt` the end time is
the user's return − 15 min, the latest window start is that same time, and the hard stop is at it (run-day.ps1 L614-619,
L852; GraceMinutes 0). What RUN-DAY enforces:

- Return time typed as HH:mm: at least 90 min and less than 14 h away; end = return − 15 min; at least 1 h must be
  left before the end when it starts (launcher-ctl).
- A window starts only if its estimate + 10 min ends by the end time; a running window is killed at the end time.
- Start checks: the user's own desktop (WinSta0\Default), **unlocked** (LogonUI running refuses the start and fails the
  quiet gate), on AC power, no other launcher.

Why the user has to be away for the **whole** session (start to return − 15 min):

- The quiet gate only watches MsMpEng, OfficeClickToRun and CrossDeviceService CPU, RAM/disk, lock and AC
  (run-day.ps1 L48, L402-436). It does **not** see the user or Minecraft, so a window would start while they play and
  its timings would be contaminated (RESUME §7 step 0: timing counts only with nobody at the PC).
- At GO accept and again right before a window it closes ChatGPT, Copilot, Roblox player, Task Manager and Wallpaper
  Engine (L54-55). It does not close Minecraft (not in the list), but the game window would open on the user's desktop.
- It sets the screensaver to None and keeps the PC awake until the end.
- The PC must stay unlocked: the user can't lock it and walk away.

Rough minimum: RUN-DAY itself refuses a return less than 90 min away. One 13-run window (~27-34 min, + GPU warm-up
5-13 min of discarded runs, + 10 min slack, + quiet-gate wait, + 15 min before the return) needs about 1.5-2 h away;
two windows about 2.5-3 h. Someone must also write the GO lines during the session (BRIEF rule 2: not now; the
Overseer decides who, once the user agrees to a day session).
