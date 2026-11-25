# Day-installer re-pin + sys_selftest fix: rating

M10, 2026-11-25 ~07:37 (request 13:35Z). Read-only review. I ran neither the installer nor the selftest.

## Files rated

| file | sha256/16 | bytes |
|---|---|---|
| build/agent8/session3/day-repin/install-day.ps1 | D2D1D11F8BD6D313 | 6799 |
| build/agent8/session3/day-repin/install-day.diff | D7F81F97F2EA4A68 | 1081 |
| build/agent8/session3/day-repin/README.md | 13006CF7941B40E3 | 3698 |
| bench/agent8/run/selftest/sys_selftest.ps1 (live) | 5C2D20389BF8714D | 32334 |

Base:
- live `build/agent5/session3/install-day.ps1` B79061A207BEAC1E, the version M11 rated in day-draft-rating.md 430E8049;
- the selftest original `build/agent8/session3/backup/20261125-073031/selftest/sys_selftest.ps1` 216DE7F4D91A69EF;
- the install log `build/agent8/session3/install/install-log.txt` (staged and installed C9E2CD42).

## Verdict

- **(1) install-day re-pin: SAFE.** The diff is exactly the pin plus the comment. M11's rating and its conditions 1-5 carry over unchanged.
- **(2) sys_selftest fix: SAFE.** The fix is correct, and no check logic changed.

## (1) What I checked

- **Line diff of live B79061A2 against the copy D2D1D11F.**
  - Removed: the L38 comment line and the L43 `run-matrix.ps1` pin `1A522CDF…`.
  - Added: the two-line comment and the pin `72370A1E737A3A34399E78D6D8C670F8B5789F0B49212A53F4846D89EF790C04`.
  - Nothing else changed. `install-day.diff` shows the same.
- **The new pin is correct.** It equals the live `bench/agent8/run/run-matrix.ps1` (72370A1E) and the install log's "installed 72370A1E OK" line.
- **The copy is clean.** It parses with 0 PowerShell parse errors and is pure ASCII.
- **The rest of the night set is unchanged:** run-night.ps1 565D30D4, README B7CEBD63, RUN-NIGHT.cmd D7A0362B, each matching M11's table.
- **Carry-over.** M11 rated B79061A2 and listed run-matrix as "hash only (night set)". The re-pin changes only that expected hash. The plan-mode run, the `-Install -NoOptional` path and conditions 1-5 apply unchanged.
- **The rest of the day draft needs no re-pin, as M8 claims.** I agree with the README's analysis:
  - run-day.ps1 and run-night.ps1 hash the run/ files at launcher start (`Get-PinFiles`/`Get-Pins`) and compare them around every window.
  - There are no stored hashes, so they pick up the new files automatically.
  - Operator rule that follows: install nothing into `bench/agent8/run` while a launcher runs.

**Should the other 5 changed files join `$Night`? No, not needed.**
- `$Night` only proves that the day install leaves the night launcher set alone.
- install-day writes only its own targets (the bench/agent5 day dir and its log), never `bench/agent8/run`.
- The 5 files are covered at runtime by the launchers' pin-at-start check.
- M11 rated the narrower set (run-matrix only, no `.py`/`.cs`/drivers).
- Adding them would make every future M8 fix of a summary or driver file another installer re-pin, with no safety gain for the install itself.
- Optional, if you want belt-and-braces: add them with the README's new hashes. That would need a fresh plan-mode run.

**Findings (1)**
- **NIT N1:** the new comment line L38 ends in CRLF (1 CR in an otherwise LF file).
  - It is harmless to PowerShell: inside a comment, 0 parse errors.
  - But the README says "line endings unchanged", and M11 noted the file was LF.
  - Cosmetic. Fix it only if a re-copy happens anyway.

## (2) What I checked

**Diff of the original 216DE7F4 against live 5C2D2038**
- **C2 header patch (L27).** `$Header` gains the 7 columns `nongame_cores,game_cores,proc_nongame_cores,nongame_io_MBps,disk_MBps,top_cpu,top_io` (31 total). That matches the tail of `drivers/LdSys.cs` L32-35. This is my m8-runner C2 condition, and it was already in C9E2CD42.
- **The `$r`/`$R` fix.**
  - One line was added at L357: `$nCsv = $R.Count`. It sits after the last use of `$R` (L356) and before the first `$r = Run-Py` of section g (L365).
  - Four lines in section g's two `Check` calls swap `$R.Count` for `$nCsv`.
  - So the request's "4 lines changed" is 4 changed lines plus 1 added line. No condition, threshold or other check changed.
- **The cause is real.** PowerShell variable names are case-insensitive, so `$r = Run-Py` (L365, L379, …) overwrote the CSV rows that were assigned to `$R` at L224.
- **No other instance of the bug.**
  - The only `$r` assignment before L224 is L200, and `$R` is assigned after it.
  - L78 is inside a helper function.
  - Every case-sensitive `$R` use from L224 to L356 comes before the first section g `$r`.
- **The result is credible.** `install/selftest2-out.txt` ends `SELFTEST OK: pass=28 fail=0 info=11`.
- **Copies.** The staged copy `staged/selftest/sys_selftest.ps1` equals live (5C2D2038).
- **Missing backup.** The C9E2CD42 intermediate has no saved copy or diff under `build/agent8/session3` (`staged/` was overwritten), so I diffed against the 216DE7F4 original instead. The full delta is the C2 header plus the fix above, which covers both steps.

**Findings (2)**
- **NIT N2:** keep a copy of an intermediate installed version (here C9E2CD42) before overwriting `staged/`, so that a "fix after install" diff can be checked against what was actually installed.
- **NIT N3:** the README table lists only old → new (216DE7F4 → 5C2D2038). Add the C9E2CD42 step for the record.

## Read / Sent

- **Read:**
  - the 3 day-repin files;
  - the live installer (full line compare);
  - day-draft-rating.md 430E8049 (conditions, files table);
  - install-log.txt;
  - sys_selftest.ps1 (original and live) L27, L78, L200, L224-287, L345-404;
  - LdSys.cs header;
  - selftest2-out.txt tail.
- **Sent:** both verdicts to the Overseer.

## Addendum (M10, ~07:48; request 13:46Z): run-timing.ps1 stop_line fix: SAFE-IF

- **Files:**
  - `build/agent8/session3/run-timing-fix/run-timing.ps1` 9CCE982737C773D0 replaces the installed `bench/agent8/run/run-timing.ps1` 75F4B5278BD75C14;
  - `run-timing.diff` 76117F39;
  - `README.md` 98808A83.
- **Checked:**
  - **The diff is complete.** The full line compare shows exactly one changed line, L503: `'^sys-csv: stop'` → `'(^|\s)sys-csv: stop '`. Both files are LF with no CR, and the new file parses with 0 errors.
  - **The cause is real.** Every sys.out line carries the `HH:MM:SS.mmm +N.NNs ` prefix. I checked the 0315 matrix runs, and their prefixed stop lines never matched the old anchored pattern.
  - **The new pattern matches every real stop line.** That covers sys-csv.ps1 L161 and the L153 `reason=error` form. The trailing space excludes the `stop_file=`/`stop_watch=` start-line fields.
  - **The effect is text only.** L503-504 fill `sys_sampler.stop_line`, which is printed at L506 (run log) and L673 (summary). Timing, flags, exclusion and sys_summary are untouched.
  - **Readers of `stop_line`:**
    - sys_selftest reads the driver output (`$r.last`), not run.json.
    - The only run.json reader is M8's own `smoke/check_smoke.py` item 7, and it *expects* the field. So the fix makes that check pass; it doesn't change any production gate.
    - No `stop_line` reader exists in M12's gates, M3's s4b/post-window scripts or the bench/agent5 launchers.
- **Condition R1:** install only while no launcher (night/day) and no run-matrix/run-timing process runs. The launchers pin run-timing.ps1 at start, so installing mid-session would trip the pin compare at the next window. After installing, the installed hash must be 9CCE9827. The day launcher was installed at 07:46: if a day session has started, wait until it ends.
- **NIT:** the README's "no script reads stop_line" misses check_smoke.py. That's harmless.
- **ProcEvery=5 (FYI):** no objection, given:
  - the P0 runs show the same 80-108 ms host stalls;
  - the 719 ms case is a file-write stall;
  - the cost is ~10 ms CPU every 5 s.
  The re-check on the first idle timed window stays the gate for this.
