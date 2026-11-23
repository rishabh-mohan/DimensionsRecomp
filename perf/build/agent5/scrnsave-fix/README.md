# SCRNSAVE.EXE / StrictMode fix (Agent 5, task #26)

Status: **installed on 23 Nov at 07:33:57** by `install-scrnsave.ps1` (`install-log.txt`). That was after the night
launcher (pid 19960) had ended at 07:30:14 (deadline, exit 0) and put the screensaver back (`restored 2026-11-23
07:30:14`), and after Agent 8 (owner of run-matrix.ps1: OK) and Agent 10 (SAFE, `build/agent10/t27/scrnsave-delta.md`)
had read this delta. The day draft in `build/agent5/day-draft/` was updated at 07:34:10 (`day-update.ps1`). It stays
staged: nothing goes to `bench/agent5/day/` before the break.

## What went wrong

- 23:47: the night launcher started. Its `Set-ScreensaverNone` *deleted* `SCRNSAVE.EXE` from
  `HKCU\Control Panel\Desktop` (the value was there and empty).
- 00:03:40: the launcher refused the W6 GO. Its `run-matrix.ps1 -PlanOnly` check threw under StrictMode at L417,
  `[string]$scr.'SCRNSAVE.EXE'`: "The property 'SCRNSAVE.EXE' cannot be found on this object."
- 00:05:37: Agent 1 set the value back to '' by hand. Later GOs ran (the last one W5b, runner exit 0).

## The change

| file | what changes |
|---|---|
| `bench/agent8/run/run-matrix.ps1` (Agent 8's) | L417-419 only. SCRNSAVE.EXE, ScreenSaveActive, ScreenSaveTimeOut and ScreenSaverIsSecure are read with the existing `Get-P` (L65, reads through `PSObject.Properties`). A missing value reads as '' (the timeout as '?'). The task named L417; L418-419 had the same plain reads of the other three values, so they get the same treatment. When the values are there, the printed line is the same as before (tests `m-*-same`). |
| `bench/agent5/launch/run-night.ps1` | `Set-ScreensaverNone` sets SCRNSAVE.EXE to '' (REG_SZ) instead of deleting it, inside a try/catch that logs a yellow `!!!` line. Its log line now shows the value. `Restore-Screensaver`: if SCRNSAVE.EXE was missing at the start, it is deleted again, so the end state equals the start state, including "missing". That is the only `Remove-ItemProperty` left. |
| `bench/agent5/launch/README.md` | the screensaver row of the "what it changes" table, and the hand-restore note ("empty or missing"). |
| day draft, `build/agent5/day-draft/` (staged in `new/`; **not** installed to `bench/agent5/day/` before the break) | `make-run-day.ps1`: pins the fixed night launcher `565D30D4...` instead of `16B90FA8...` (Agent 10's condition 1) and writes `run-day.diff` with repo-relative paths (N1). `run-day.ps1` regenerated from the fixed night launcher, so it gets the same screensaver change. `README-DAY.md`: new sha, N2 (L57: use the installed STOP-LAUNCHER), a note on this fix. `RUN-DAY.cmd` L25: the exit-2 line no longer says "Nothing was changed" (N3). |

Not changed: anything else in run-matrix.ps1 (it reads the Desktop key once, at L416; no other file in
`bench/agent8/run` reads that key), RUN-NIGHT.cmd, the runner, the drivers, the matrix files.

## Files in this folder

| file | what |
|---|---|
| `patch-scrnsave.ps1` | Checks the sha256 of the 8 source files, copies them to `base/`, makes `new/` by literal edits (each old text must occur exactly once), regenerates `new/day/run-day.ps1` with the new make-run-day.ps1, checks that the new run-day.diff names no absolute path, writes `scrnsave-fix.diff` and `hashes.txt`. It writes only in this folder and refuses once a source has changed. |
| `test-scrnsave.ps1`, `e2e-driver.ps1` | the tests below |
| `install-scrnsave.ps1` | the install, steps 1-3 below: the checks, then the copy and the hash comparison. `-Check` runs the checks only. It appends to `install-log.txt`. |
| `day-update.ps1` | the day-draft part: copies the three day files from `new/` into `build/agent5/day-draft/`, runs make-run-day.ps1 there and checks the result. `-Check` runs the checks only. |
| `base/` | the files before the fix. The old run-day.diff is not copied (it names absolute paths); its sha was checked. |
| `new/` | the files after the fix. `new/day/` holds the regenerated run-day.ps1 and run-day.diff. Its diff paths are relative to `build/agent5`, because this copy sits two levels deeper than the day-draft folder; the copy made in `build/agent5/day-draft/` has repo-relative paths. |
| `scrnsave-fix.diff` | `base/` -> `new/`, for reading. RUN-DAY.cmd lines appear without their CR there; install by copying files from `new/`, not by applying the diff. |
| `hashes.txt` | sha256 of everything in `base/` and `new/` |
| `results/` | test summaries |

## Hashes (sha256)

| file | before | after |
|---|---|---|
| bench/agent8/run/run-matrix.ps1 | FEDCEB13AB46FE790598EEFD97B5EF5FF545D5D24FADFB3BA03B1CE1CA0CBB89 | 1A522CDFE9DC36F8F976D374D020D8EB3102AAB4327BF10BAED31B0F369358CB |
| bench/agent5/launch/run-night.ps1 | 16B90FA8654FAC088FE5A1248DE1754918AACC7667A2126AD14723BFBF939B31 | 565D30D40DC5025AD63FD9B9F606724BABC167BC81FCB6FBEB6362B603977112 |
| bench/agent5/launch/README.md | 0058C8F61EEAA9F2529145B034433E2FB67344012D114E4103CE8E3A0EB43274 | B7CEBD635D847D4CB89D900B9E002B87526D487C971A03A4563EC6807B2A7965 |
| build/agent5/day-draft/make-run-day.ps1 | 17413F8A566E79BF0721BF77DA64BACEA629DBAB7D70887A6AA75CBAA2827780 | 4A96B0B947D0796B7C65539C35648C50DB4F61E43B7191B58C8816B69E968D4C |
| build/agent5/day-draft/run-day.ps1 | D86F6DE04B3EDA47A4811CD7139B9BEE21B43E0E368AAB4287143F45B8C59E98 | B67EBD6C2C9A378C8897558DD71AD383DCC85015952601F3EDF2FAED415ADC65 |
| build/agent5/day-draft/README-DAY.md | 9D131EB14B89DBBBB642D0C40AA0103FB7742BD95B1BA143E7F8E6A8CE308FCB | A36574ED620880809AC504C387B8AF923E1B490120A378B1A19E742B594DF517 (as staged; the day-draft copy was edited after the regen, L57, L130, L134, L138: 9739BCF8952146D9258E7A843A4CC0F07451FBE81AE0A3FC795C35F05356EECB) |
| build/agent5/day-draft/RUN-DAY.cmd | 4B5489B4C1021038C44D2C97A18B19E675AB278CCC43D5CD1B11B21F5039CAD9 | B08645E9D4296AC1623E65EBBB3ECCB532EC5C49837569D3AD8F7A7F671DD736 |
| build/agent5/day-draft/run-day.diff | 54E35C180DBF4B164DB86CC5B61D71952F132C7149E69D909634DAE0B60EC12F | 3D0E8753683A17AAAC3FD5B85377DC930FDF1CE6E9F338F8C2891E74C23082D2 (repo-relative headers; the copy in `new/day/` is F5EC971E..., relative to `build/agent5`) |

RUN-NIGHT.cmd (D7A0362B...) is unchanged. None of the launcher files (RUN-NIGHT.cmd, run-night.ps1, and in the day
draft run-day.ps1, RUN-DAY.cmd, launcher-ctl.ps1) holds a hard-coded hash. The only hard-coded pin is make-run-day.ps1's
`$Want`, which this change moves to `565D30D4...`.

**`bench/agent5/launch/status/pins.txt` re-pins itself at the next start.** That file (written 22 Nov 23:47:20) still
lists run-matrix.ps1 FEDCEB13 and run-night.ps1 16B90FA8. It is the record of that start: run-night.ps1 writes it once
(L973) and never reads it back. At each start the launcher hashes the runner files, itself and RUN-NIGHT.cmd again (L967,
`Get-Pins`, L195), and the checks before and after each window (L688, L739, L900) compare with those in-memory hashes.
So the next RUN-NIGHT.cmd start pins run-matrix.ps1 1A522CDF and run-night.ps1 565D30D4, and it rewrites pins.txt once
its start checks pass. Nobody has to re-pin by hand. A start that is refused leaves the old pins.txt as it is. The day
launcher does the same with its own `status\pins.txt`.

## Tests

`powershell -NoProfile -ExecutionPolicy Bypass -File build\agent5\scrnsave-fix\test-scrnsave.ps1 -Set new -E2E`
(`-Set installed` runs the same checks on the installed files and the day-draft run-day.ps1).

Results:

- Before the install, `-Set new -E2E`, 23 Nov 06:14:40: **45/45 PASS** (`results/summary-new-061440.txt`). The real
  Desktop key read `SCRNSAVE.EXE present '' REG_SZ, ScreenSaveActive 0` before and after the run. test-scrnsave.ps1
  was changed after that run (06:17:01); the post-install run below used the changed file.
- After the install, `-Set installed -E2E`, 07:34:45, with test-scrnsave.ps1
  4D46A8E28E01B6ED4E40A489D6D2C5A79DA35D3C77E2D31ABBBCB0E666CC8DBF (Agent 10's N-1): **45/45 PASS**
  (`results/summary-installed-073444.txt`), on run-matrix.ps1 1A522CDF, run-night.ps1 565D30D4 and the regenerated
  run-day.ps1 B67EBD6C. The real Desktop key read `SCRNSAVE.EXE present '' String, ScreenSaveActive 0` before and
  after.
- After the install, `build/agent5/day-draft/test-day.ps1 -Name all`: at 07:35:58 26/27. Only d-real-4 failed, on a
  stale condition of the test: it required that `bench/agent5/launch/status` not exist, which stopped being true at
  23:47. The launcher's answer was right. The test now compares that folder before and after the case (test-day.ps1
  D7DBC6EA -> 410FB2EC, test only). At 07:47:14: **27/27 PASS** (`build/agent5/day-draft/results/summary-all-074714.txt`).
- After the install, the night launcher's dry-run go group, `build/agent5/launch-test/run-tests.ps1 -Group go`: at
  07:35:58 every case was refused at start, because after 07:30 a launcher's default end (the next 07:30) is more than
  14 h away. run-tests.ps1 got a `-StopAt` option for daytime runs (034F2E1F -> DD96C0E1, test only). With
  `-StopAt '2026-11-23 11:00'`, started 07:47:15: **16/16 PASS** at 07:52:00 on run-night.ps1 565D30D4 (`build/agent5/launch-test/results/summary-go.txt`;
  the 22 Nov 22:18 run, 16/16 on 16B90FA8, is kept as `summary-go-20261122-2218.txt`). Afterwards: no test process
  left, no real GO/HOLD/STOP file, the real launcher mutex not held.

Safety: the tests write only a scratch key, `HKCU:\Software\Agent5-scrnsave-test\Desktop` (created and deleted),
and never `HKCU:\Control Panel\Desktop`; `SystemParametersInfo` is replaced by a fake class that records the calls.
The last check (`real-untouched`) compares the real Desktop key before and after. No game, runner, launcher or build.

| group | checks |
|---|---|
| `s-*` static | parse, ASCII and LF; no plain `$scr.<name>` read left in run-matrix.ps1; `Remove-ItemProperty` only in `Restore-Screensaver` (night and day); the day launcher's screensaver functions are identical to the night launcher's, 7 `# DAY:` lines, header names `565D30D4`; run-day.diff names no absolute path |
| `m-*` run-matrix block | run-matrix's screensaver block (L416-420) under StrictMode 2 on the scratch key, with SCRNSAVE.EXE **missing**, empty, active, active without timeout, screensaver off, no values, no key: all print one line, no throw. Old and new print the same line when the value exists. Control: the old block throws with SCRNSAVE.EXE missing, with the 00:03:40 message |
| `night-*`, `day-*` launchers | the real `Save-Screensaver`/`Set-ScreensaverNone`/`Restore-Screensaver` functions (cut out of run-night.ps1 and run-day.ps1) for SCRNSAVE.EXE **missing**, empty and active: set -> '' REG_SZ; the run-matrix block (old and new) is fine while it is set; restore -> missing / '' / the .scr path again, with the right SystemParametersInfo calls and a `restored` line; dry run changes nothing. Control `old-night-empty`: the old launcher deletes the value and the old block then throws (the 23:47 deletion plus the 00:03:40 refusal, reproduced) |
| `e2e-*` | `run-matrix.ps1 -PlanOnly` end to end with the launcher's W6 arguments (`matrix-window6.json -Only s0,p2,p2f,p2fc -Repeats 5 -ColdShared -NoPrompt`), in sandbox copies of `bench/agent8/run` (`build/agent5/sfx-base`, `sfx-new`, deleted afterwards), with `Get-ItemProperty` of the Desktop key redirected to the scratch key (it is read once). Old + missing: throws (control). New + missing / empty: exit 0, "screensaver none", "PlanOnly: nothing started." New + active: the screensaver warning line |

## Install (done on 23 Nov at 07:33:57)

`install-scrnsave.ps1` does steps 1-3 and copies nothing if a check fails. At 06:36, with the launcher still
running, `-Check` refused on all four launcher checks (mutex, process, state, no `restored` line). The process check
also refuses while any other PowerShell command line names run-night.ps1 or run-day.ps1 (an agent's search, say);
that fails safe, just run it again (Agent 10's N-4). That happened at 07:33:42: my own command line named
run-night.ps1. Nothing was copied, and the run at 07:33:57 installed all three files at the "after" hashes.

1. Check: pid 19960 is gone, `bench/agent5/launch/status/state.txt` shows the launcher ended,
   `status/screensaver-saved.txt` has a `restored` line, no `perf-notes/WINDOW-HOLD.txt`.
2. Check that the three installed files still have the "before" hashes above.
3. Copy `new/run-matrix.ps1` to `bench/agent8/run/`, and `new/run-night.ps1` and `new/README.md` to
   `bench/agent5/launch/`. Compare the hashes with the "after" column.
4. Run `test-scrnsave.ps1 -Set installed -E2E` and the night launcher's dry-run tests
   (`build/agent5/launch-test/run-tests.ps1 -Group go`). Done: see Tests (in the daytime the go group needs `-StopAt`).
5. Post the new hashes to Agents 1, 8 and 10.

Undo: copy the files in `base/` back (same names, same folders).

## Day draft (second priority, staged only)

After the install, the three changed day files from `new/` go to `build/agent5/day-draft/`, and `make-run-day.ps1`
is run there (default source: the installed run-night.ps1); `day-update.ps1` does this and the checks. The result must
equal `new/day/run-day.ps1`; then
`test-day.ps1 -Name all` and `test-scrnsave.ps1 -Set installed` run again. Nothing goes to `bench/agent5/day/`
before the break. Agent 10 delta-reads it (condition 1); Agent 11 still has to rate the day draft.

Done at 07:34:10: run-day.ps1 = B67EBD6C (1020 lines, 7 `# DAY:` lines, parse OK), the same file as `new/day/`.
run-day.diff = 3D0E8753 (58 lines), with the headers `diff --git a/bench/agent5/launch/run-night.ps1
b/build/agent5/day-draft/run-day.ps1`, `--- a/bench/agent5/launch/run-night.ps1` and
`+++ b/build/agent5/day-draft/run-day.ps1`. The hashes of all day-draft files are in `install-log.txt`.

## For the reviewers

- Agent 8: in run-matrix.ps1 only L417-419 change. `Get-P` returns the default for a `$null` object (no key) and
  for a missing or `$null` property, so the `if ($scr)` / `$scr -and` guards are no longer needed.
- The launcher now *creates* SCRNSAVE.EXE = '' when it was missing at the start, and deletes it again at the end.
  If the launcher is closed with the X before the end, the value stays ''. Windows treats that as "(None)" (it is the
  same state as Agent 1's hand fix at 00:05:37), and run-matrix.ps1 reads it fine.
- `-Type String`: SCRNSAVE.EXE is normally REG_SZ. An original REG_EXPAND_SZ value would come back as REG_SZ with the
  expanded path. That was already so before the fix (the old code deleted the value and created it again).
