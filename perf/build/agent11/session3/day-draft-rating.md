# Day-mode draft launcher + installer: rating (S3T-11)

M11, 2026-11-25 01:46-01:55. Read-only review plus one documented read-only dry run (installer plan mode). No `-Install`,
no launcher, no test-day run, no game, no build.

## Verdict: SAFE-IF

No BLOCKER. No kill pattern can hit a user process: every kill is either one of the README's close-list programs
(same session, and path-checked for the names other programs share) or a process the launcher's own runner started.

Conditions:

1. **Only after the night launcher has ended.** Run `-Install` only after the night launcher (pid 38660) has exited:
   `bench\agent5\launch\status\state.txt` says `ended`, pid 38660 is gone, and the plan check (no `-Install`) prints
   `checks OK` with exit 0. The script refuses on its own while the mutex or the process is there: this was tested live at 01:47
   (see "Dry run").
2. **Operator checks for games and builds by hand.** Just before `-Install`, check that no `legodimensions.exe`, no
   build process (M2) and no test-day dry run is running. The installer does not check games or builds (I-N1).
3. **Install with `-NoOptional`.** That installs only the 5 runtime files. The 3 optional files have no runtime role,
   and two of them write next to themselves (D-N5).
4. **Accept only a clean result.** Accept only exit 0 with every `target OK` line and `installed: ... night set
   unchanged`. Any other result (exit 1, exit 2, or a PowerShell error text) means don't start RUN-DAY and report to the
   Overseer. If `bench\agent5\day\` was partly written, delete only that folder, and only while no day launcher runs
   (I-N2, I-N3).
5. **Use (not install).** Start a day session only when the user confirms they will be away for the whole session.
   Only the Overseer writes GO lines during it (BRIEF rule 2). The launcher has no user-presence sensor (D-N2).

## Files reviewed (sha256)

| file | sha256 | how |
|---|---|---|
| build/agent5/session3/install-day.ps1 | B79061A207BEAC1E52BA5F8CE7550B45ED0A03442F97D47E635A818A2FEA1DAA | read in full, plan-mode run |
| build/agent5/session3/INSTALL-DAY.md | 827B13CC08519AE4970502A8BB9E60858D729DF88513EA4C652316B14A6F9C9D | read in full |
| build/agent5/session3/install-day-test-log.txt | A3D063BCBE97B2A6EB089D120986BF7D788D3B5033C41B986D0863958186F3C3 | read |
| build/agent5/day-draft/run-day.ps1 | B67EBD6C2C9A378C8897558DD71AD383DCC85015952601F3EDF2FAED415ADC65 | read in full + own diff vs night |
| build/agent5/day-draft/launcher-ctl.ps1 | 6DDE3150B72D6B0D849B17788098F9C10C1E96CBF5CF3BBC395C95C935C34895 | read in full |
| build/agent5/day-draft/RUN-DAY.cmd | B08645E9D4296AC1623E65EBBB3ECCB532EC5C49837569D3AD8F7A7F671DD736 | read in full |
| build/agent5/day-draft/STOP-LAUNCHER.cmd | CE27332F354B1DBB253678189A7070D8AB3C79010D1584C9DE204BB160C8E1B3 | read in full |
| build/agent5/day-draft/README-DAY.md | 9739BCF8952146D9258E7A843A4CC0F07451FBE81AE0A3FC795C35F05356EECB | read in full |
| build/agent5/day-draft/run-day.diff | 3D0E8753683A17AAAC3FD5B85377DC930FDF1CE6E9F338F8C2891E74C23082D2 | read; matches my own diff |
| build/agent5/day-draft/make-run-day.ps1 | 4A96B0B947D0796B7C65539C35648C50DB4F61E43B7191B58C8816B69E968D4C | L1-40 (paths, source pin) |
| build/agent5/day-draft/test-day.ps1 | 410FB2ECBA7B72B9530B6DD50B7AB8F0FEDEE0A5650D0A1F705F201EA137118E | grepped kills/writes |
| build/agent5/day-draft/results/summary-s3dry-012200.txt | BD3456508AD4EDA1622D01F6936700295EB577EC4E4EBE596191EA1DEDE26523 | read (20/20 PASS) |
| bench/agent5/launch/run-night.ps1 | 565D30D40DC5025AD63FD9B9F606724BABC167BC81FCB6FBEB6362B603977112 | diff base |
| bench/agent5/launch/README.md | B7CEBD635D847D4CB89D900B9E002B87526D487C971A03A4563EC6807B2A7965 | read in full (close list, rules) |
| bench/agent5/launch/RUN-NIGHT.cmd | D7A0362BE90C12B4F027116B9A5146D1F4C8D109110F885EE8CF62E6769DE6D5 | read |
| bench/agent8/run/run-matrix.ps1 | 1A522CDFE9DC36F8F976D374D020D8EB3102AAB4327BF10BAED31B0F369358CB | hash only (night set) |
| build/agent10/t27/day-draft-rating.md | 0FD65482DE70468BFA32CB5B66206C4E234A6DE26B10D09CA96341AC3FE17217 | read (prior rating) |

All draft files and install-day.ps1 are pure ASCII. The .ps1/.md files use LF; the .cmd files use CRLF. Every draft hash
equals the installer's rated list (install-day.ps1 L26-37).

## Dry run (read-only)

I read install-day.ps1 first. Without `-Install`, it only hashes files, opens the mutex for reading and lists processes.
The log is written only with `-Install` (L53), and nothing is created before L79. Run at BelowNormal priority, at 01:47:47:
`powershell -NoProfile -ExecutionPolicy Bypass -File build\agent5\session3\install-day.ps1`:

- 8/8 `source OK`;
- `REFUSED: a launcher holds Local\Agent5RunNight-real`;
- `REFUSED: a launcher process runs: pid 38660`;
- `Nothing was written.`, `exit 2`.

Afterwards `bench\agent5\day\` and `install-day-log.txt` still don't exist. The agents' desktop shares the user's
session, so the `Local\` mutex check works from there.

## Findings: installer (install-day.ps1)

- **I-OK1 Writes only what it lists.** It copies only the listed files (L45-46) into the target (L79-80), and writes its
  log only with `-Install` (L53). It refuses when the target exists and is not empty (L74), so it never replaces a file
  and needs no backups. Undo = delete `bench\agent5\day\`. A test `-Target` must be under `build\agent5\session3\`
  (L20).
- **I-OK2 Refusals.** It refuses if:
  - a draft file is not at its rated hash (L59-63);
  - the 4 night files changed (L64-67);
  - the mutex is held (L69);
  - a powershell runs run-night/run-day with `-File` (L70-72);
  - WINDOW-HOLD exists (L73).

  It hashes again after the copy and checks for extra files and the night set (L82-88). It never touches the registry,
  `perf-notes\` or `bench\agent5\launch\`.
- **I-OK3 Pins.** None of the 19 files in `bench\agent5\launch\status\pins.txt` (pinned 01:37:06 by pid 38660) is
  under `bench\agent5\day\` or `build\agent5\session3\`. The installer never touches a pinned file, and it refuses to
  run while that launcher is alive anyway.
- **I-N1 No game/build check.** It doesn't check for `legodimensions`, the build list or game runs, which the brief asks
  for. Copying 8 small files can't disturb a timed window (one needs a launcher, which is checked), but the rule needs
  the operator to check by hand (condition 2).
- **I-N2 Mutex read can abort.** If the mutex exists but its ACL denies opening it, `TryOpenExisting` (L69) throws.
  Under `$ErrorActionPreference = 'Stop'` the script then aborts with PowerShell's exit 1, before anything is written.
  That code reads as "copied, hash differs" (L8). The error is fail-safe but the exit code is misleading. launcher-ctl
  handles the same case (launcher-ctl L92). Covered by condition 4.
- **I-N3 Copy failure leaves a partial folder.** If a copy fails part-way (L80), the script throws: no log, and a partial
  `bench\agent5\day\`. A re-run then refuses ("not empty"). Covered by condition 4.
- **I-N4 Process match needs a full path.** The process regex (L71) needs a `\` before the script name, so a launcher
  started with a bare relative `-File run-night.ps1` isn't matched. The mutex check (L69) covers that case: both run-night
  and run-day take the mutex at their start (run-day L943-951).

## Findings: day launcher

- **D-OK1 Only 7 lines differ from the night launcher.** I recomputed the diff myself (python difflib) between
  `bench\agent5\launch\run-night.ps1` 565D30D4 (the running night launcher) and run-day.ps1 B67EBD6C. Exactly the 7
  `# DAY:` changes differ: L1 header, L65 hook list without `StopAt`, L68 new `-StopAt` required, L187 pins RUN-DAY.cmd,
  L545 HOLD text, L939 and L967 messages. This equals run-day.diff. Every safety code path is byte-identical to the night
  launcher.
- **D-OK2 Close list.** The close list (L54-61, Close-Programs L492-526) is ChatGPT, Copilot, Roblox player/Store,
  Taskmgr and Wallpaper Engine. That equals night README L21/L55.
  - Only this session's processes are closed (L501).
  - Names that other programs share are closed only when the exe path matches (L502-506).
  - It tries CloseMainWindow first, then Kill after 10 s (L517-519).
  - Minecraft, Roblox Studio and every other program are not on the list.
- **D-OK3 Kills only the runner and what it started.**
  - Stop-Tree (L816-842) kills the runner through its own handle.
  - Then it kills the runner's descendants. A process counts only if it was created at or after its parent (L775-795),
    and Stop-One checks the start time again before the kill (L801).
  - It then kills `legodimensions` only when it is in the same session, started after the window began and runs from
    under `build\agent2\` (L830-838).
  - No taskkill, no name-only kill.
  - launcher-ctl.ps1, RUN-DAY.cmd and STOP-LAUNCHER.cmd kill nothing. They only write or delete
    `perf-notes\WINDOW-STOP.txt` (launcher-ctl L159-189, L209, L238) and RUN-DAY's own `%TEMP%` file (RUN-DAY.cmd L10-17).
  - test-day.ps1 kills only processes it started itself (L55, L76, L270).
- **D-OK4 Env allowlist.** The allowlist has the 11 keys (L41-43), checked case-exact (L276). All 11 are removed at start
  (L978) and again right before the runner starts (L711). RUN-DAY.cmd L7-8 clears 2 of them.
- **D-OK5 Bins.** Each bin must be `build/agent2/<name>-bin` with MANIFEST.txt and legodimensions.exe (L268-272). The bin
  hashes are taken at the GO, checked again before the start (L691) and after the run (L742). Drivers are allowlisted
  and must be pinned (L284-296).
- **D-OK6 GO/HOLD/STOP.**
  - GO: a strict 6-token line (L226-244), deleted when read (L894).
  - HOLD: owned by its token (L543-600); a foreign HOLD is never touched.
  - STOP: checked while waiting, during the gate and every second during a run (L987, L647, L863).
  - Same perf-notes files and the same mutex `Local\Agent5RunNight-real` (L79), so a night and a day launcher never
    overlap.
- **D-OK7 Session checks.** At start it checks desktop `WinSta0\Default`, LogonUI and AC (L958-971), and nothing
  changes before those checks pass (screensaver and keep-awake come only at L981-982). It checks again right before each
  window (L695-700), and the gate checks every sample (L408-413). launcher-ctl also checks the folder (L194) and AC
  (L197-202).
- **D-OK8 End time.** `-StopAt` is required (L68).
  - The deadline is `-StopAt` (L614), and so is the latest start (L619).
  - The hard stop is at `-StopAt`: GraceMinutes is 0, and it is a hook that real mode refuses (L65-67, L852).
  - It keeps the 14 h cap (L967). A window starts only if its estimate + 10 min fits (L692, L908).
  - launcher-ctl allows a return 90 min to 14 h away (L82-83) and needs at least 1 h left, checked before any stop
    (L220) and again before it writes the end time (L240).
- **D-N1 Game sweep can hit an agent's game.** The `legodimensions` sweep (L831-835) would also kill a game that an
  agent started from `build\agent2` during a window, in the same session. That isn't a user process, and policy forbids
  game runs during a window. The night launcher does the same. Not a blocker.
- **D-N2 No user-presence sensor.** The gate sees only MsMpEng, Office and CrossDevice CPU, builds/games, RAM/disk,
  lock and AC (L404-440). It doesn't see user input or Minecraft (same as the night launcher; INSTALL-DAY.md L60-68 says
  so). So "no window while the user is active unless GO says so" holds only through the process: windows start only from
  a GO, and only the Overseer writes GO lines (condition 5). Suggestion for later: a GetLastInputInfo idle check in the
  gate. That would change run-night's lineage and need a new review.
- **D-N3 Close list can lose unsaved work.** Close-Programs kills ChatGPT, Copilot or Taskmgr 10 s after
  CloseMainWindow, so unsaved state there may be lost. README-DAY L38 documents this. Acceptable.
- **D-N4 Agent 10's NITs.** N3 is fixed: RUN-DAY.cmd L25 now says a night launcher that was stopped stays stopped.
  N5(a) is still open and documented (README-DAY L33, L134): after a night launcher is closed with the X, the day launcher
  doesn't see its saved screensaver file. N5(b) is harmless.
- **D-N5 Optional files write next to themselves.** make-run-day.ps1 writes `run-day.ps1` and `run-day.diff` in its own
  folder (L12-13, L107, L117). In `bench\agent5\day\` that would rewrite the pinned launcher. The bytes would be the same
  while the source pin holds, but it is still a write to a pinned file. test-day.ps1 creates `results\` and
  `status-dryrun\` in its own folder. Hence condition 3.

## Tests looked at

- `results\summary-s3dry-012200.txt` (BD345650): 20/20 PASS at 01:22 on run-day B67EBD6C and launcher-ctl 6DDE3150.
  It ran before the night launcher started at 01:37.
- install-day-test-log.txt: test target 8/8 equal, exit 0; the second run refused (target not empty, plus a live test
  launcher), exit 2.
- My plan-mode run above.
