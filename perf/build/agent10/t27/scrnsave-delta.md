# SCRNSAVE fix: delta-read (#27 item 1)

Agent 10, Nov 23, 06:30; the install tooling was added at 06:45 (§6) and the post-install check at 07:56 (§5). Read only: no runs, no installs, no registry writes. The test results in §5 come from Agent 5's runs; I read their summaries.

**Verdict: SAFE.** Install it with `install-scrnsave.ps1`, as the "Install" section of `build/agent5/scrnsave-fix/README.md` says (L75-87 in EDA4D4F9…; it was L73-84 in 7B367721…, the version I read first). Findings: 0 BLOCKER, 0 SHOULD, 4 NIT, 3 info. Either half alone fixes the refused GO, so the copy order does not matter (§2, item 4).

**Installed at 07:33:57, checked at 07:56 (§5).** Every hash matches, the tests pass, and N-1 to N-3 are closed. Condition 1 of the day-draft rating is closed.

Package read (`build/agent5/scrnsave-fix/`), sha256, first 16 hex:

| file | sha256 | written |
|---|---|---|
| README.md | EDA4D4F95C3075FF (first read: 7B36772169B17797, 06:16:37) | 06:36:45 |
| scrnsave-fix.diff | 366671D4858ACC2B | 06:14:37 |
| hashes.txt | 07B3A2EF9195C3B0 | 06:14:38 |
| test-scrnsave.ps1 | 4D46A8E28E01B6ED | 06:17:01 |
| e2e-driver.ps1 | 50C9D6DE05DBCC81 | 05:58:49 |
| patch-scrnsave.ps1 | 83140B4A6CD50528 | 06:12:59 |
| install-scrnsave.ps1 | F95A723E58B90692 | 06:36:08 |
| day-update.ps1 | 764306E6FECE5416 | 06:35:39 |
| install-log.txt | F27C488A7E3A05BC | 06:36:22 |
| results/summary-new-061440.txt | 343FED2C78AE8EE8 | 06:15:34 |

I re-read README.md EDA4D4F9… in full at 06:41. It adds the rows for the two new scripts (L32-33), the 06:36 `-Check` note (L77-78) and the day-update sentence (L93-94). Nothing in it contradicts §2-§5. README.md (now 1F0F3EC6…, the N-3 fix) and install-log.txt (the install) have changed since; see §5.

## 1. Scope

| file | goes to | before | after | lines +/- | my diff |
|---|---|---|---|---|---|
| run-matrix.ps1 | bench/agent8/run/ | FEDCEB13… | 1A522CDF… | +3 -3 | same |
| run-night.ps1 | bench/agent5/launch/ | 16B90FA8… | 565D30D4… | +3 -2 | same |
| README.md | bench/agent5/launch/ | 0058C8F6… | B7CEBD63… | +2 -2 | same |
| make-run-day.ps1 | build/agent5/day-draft/ (staged) | 17413F8A… | 4A96B0B9… | +7 -4 | same |
| run-day.ps1 | build/agent5/day-draft/ (generated) | D86F6DE0… | B67EBD6C… | +4 -3 | same |
| README-DAY.md | build/agent5/day-draft/ | 9D131EB1… | A36574ED… | +5 -3 | same |
| RUN-DAY.cmd | build/agent5/day-draft/ | 4B5489B4… | B08645E9… | +1 -1 | same |

- new/day/run-day.diff is F5EC971E…. RUN-NIGHT.cmd (D7A0362B…) does not change.
- At 06:24, and again at 06:38, the live files still had the "before" hashes: run-night.ps1 16B90FA8…, the launch README 0058C8F6…, RUN-NIGHT.cmd D7A0362B…, run-matrix.ps1 FEDCEB13…, common.ps1 A8975D12…. build/agent5/day-draft/ still held the old set (run-day.ps1 D86F6DE0…, run-day.diff 54E35C18…). The night launcher (pid 19960) was still running.

## 2. What I checked

1. **Diffs.** For each of the 7 files, my own `git diff --no-index` of base/ against new/ equals the matching part of scrnsave-fix.diff. base/ equals copies I took of the live and staged files before the fix. Nothing else changed.
2. **run-matrix.ps1 (new).**
   - L416 still reads the key with `-ErrorAction SilentlyContinue`, so `$scr` may be `$null`.
   - L417-419 read SCRNSAVE.EXE, ScreenSaveActive, ScreenSaveTimeOut and ScreenSaverIsSecure through Get-P (L65-71). Get-P returns the default for a `$null` object, a non-PSCustomObject, a missing property or a `$null` value. That removes the StrictMode 2 throw ("The property 'SCRNSAVE.EXE' cannot be found") that refused the first GO at 00:03:40.
   - `$scr` has no other use. The block only adds preflight text. `-PlanOnly` exits at L434-437, and nothing is written before that.
3. **run-night.ps1 (new).**
   - Set-ScreensaverNone (L461-468): SPI_SETSCREENSAVEACTIVE FALSE (L464), then `try { Set-ItemProperty … 'SCRNSAVE.EXE' -Value '' -Type String } catch { Log '!!! …' }` (L465) instead of deleting the value.
   - Restore-Screensaver (L469-481): it restores the saved value if there was one (L473). Otherwise it deletes the value, but only if it exists now (L474). The SPI restore follows (L475). All of it is inside the existing try/catch (L472, L480).
   - The catch works: EAP is 'Stop' at script level (L29), with StrictMode 2 (L30). The 'Continue' at L331 and L816 is local to those functions. Even under 'Continue', a failed write would only log an error and would not stop the launcher.
   - Set-ScreensaverNone is called at L980. The restore runs in the finally path through Try-Step (L1009). `$DeskKey` is set at L442.
4. **Install order.** Either half alone fixes the refusal:
   - old run-matrix.ps1 with the new launcher: the value exists ('');
   - new run-matrix.ps1 with the old launcher: Get-P handles the missing value.
5. **Day draft.**
   - The new run-night.ps1 and the new run-day.ps1 differ by the same 13 lines as before. Only the pinned sha in the header moved (16B90FA8 to 565D30D4).
   - There are still 7 `# DAY:` lines (L1, 65, 68, 187, 545, 939, 967). The screensaver functions are the same in both launchers.
   - make-run-day.ps1 pins 565D30D4 and writes repo-relative diff headers (N1). README-DAY.md has the N2 text, and RUN-DAY.cmd L25 the N3 text.
6. **Test safety.**
   - test-scrnsave.ps1 writes only `HKCU:\Software\Agent5-scrnsave-test` (L2-3, L21) and deletes it (L50, L249).
   - SystemParametersInfo goes to a fake [LdNight] class in the test's own process. The function cut-outs are dot-sourced, with `$DeskKey` set to the scratch key.
   - `-E2E` runs run-matrix.ps1 -PlanOnly in two sandbox copies, which are deleted at L250 (I checked that they are gone). e2e-driver.ps1 redirects only exact reads of the real desktop key to the scratch key, one redirect per case.
   - The real key was the same before and after: "SCRNSAVE.EXE present '' String; ScreenSaveActive 0".
   - results/summary-new-061440.txt: 45/45 PASS, including the old-code controls that reproduce the throw.
7. **File format.** The new .ps1 files are LF and ASCII, with no BOM. RUN-DAY.cmd is CRLF, 38 lines, ASCII. README.md adds no non-ASCII bytes (15 before and after).
8. **Public safety.** scrnsave-fix/ has no user name and no absolute user path. The e2e case files are redacted to `<repo>` (test-scrnsave.ps1 L233). The headers in new/day/run-day.diff are relative (`a/scrnsave-fix/new/run-night.ps1`).
9. **Other readers.** In bench/agent8/run (its scripts and drivers/) and bench/agent5/launch, only run-matrix.ps1 and run-night.ps1 name SCRNSAVE.EXE or the desktop key. drivers/LdSys.cs reads the screensaver state with SPI_GETSCREENSAVERRUNNING (L96, L671), not from the registry.

## 3. Findings

- **N-1 (NIT).** test-scrnsave.ps1 (06:17:01) and the e2e case files (06:17:02) are newer than the 06:14:40 run and its summary (06:15:34). So the 45/45 came from an earlier revision of the script; the `<repo>` redaction (L233) was probably added afterwards. The post-install `-Set installed -E2E` run closes this. Please quote the script's sha (now 4D46A8E28E01B6ED) with that result. **Closed (§5):** 45/45 on 4D46A8E2… at 07:34:45.
- **N-2 (NIT).** README-DAY.md L130 still says "27/27 PASS on run-day.ps1 D86F6DE0". Update it after test-day.ps1 -Name all is re-run on B67EBD6C. **Closed (§5):** L130 now has the 27/27 of 07:47:14 on B67EBD6C.
- **N-3 (NIT).** README.md L104-105 calls the empty value "Agent 1's 00:03:40 workaround". 00:03:40 is the refusal (SESSION2 L3215); Agent 1 re-created the value at 00:05:37 (L3218). Cosmetic. **Closed (§5):** README.md 1F0F3EC6… L13, L15 and L143.
- **N-4 (NIT).** install-scrnsave.ps1 L34 refuses on any powershell.exe or pwsh.exe, other than itself, whose command line names run-night.ps1 or run-day.ps1. That includes another agent's read-only command, such as a hash check, running at the same moment. It fails safe (nothing is copied); just run it again. **Seen once (§5):** at 07:33:42 it refused on pid 33304 and copied nothing; the re-run at 07:33:56 installed.
- **I-1 (info).** If the launcher is closed with the X before the end, SCRNSAVE.EXE stays ''. Windows reads that as "(None)", and run-matrix.ps1 reads it fine (README L103-105). This is harmless. The installer then refuses (no `ended` state, no `restored` line) until a launcher has finished normally.
- **I-2 (info).** An original REG_EXPAND_SZ value comes back as REG_SZ, with the path expanded. That was already so before the fix (README L106-107).
- **I-3 (info).** install-log.txt records the lines of screensaver-saved.txt and the live SCRNSAVE.EXE value (install-scrnsave.ps1 L47, L53). Today the value is '', so nothing personal is logged. A screensaver path under a user profile would put the user name into the log; keep that in mind for any export.

## 4. Day draft, condition 1

**Closed at 07:56 (§5).** It was met in staged form at 06:30: new/day/run-day.ps1 (B67EBD6C…) is generated from run-night.ps1 565D30D4…, which make-run-day.ps1 (4A96B0B9…) pins.

Asked of Agent 5 after the install (all done, §5):
- run day-update.ps1. It copies the three changed files into build/agent5/day-draft/, runs make-run-day.ps1 there, and checks that run-day.ps1 is B67EBD6C… and that run-day.diff has the repo-relative headers (§6);
- re-run test-day.ps1 -Name all and test-scrnsave.ps1 -Set installed;
- send the final day-draft hashes.

I checked the hashes, the run-day.diff headers and the test results at 07:56 (§5). **Condition 1 is closed.** Conditions 2 (install into bench/agent5/day/) and 3 (Agent 11's rating) wait until after the break.

## 5. After the install

**Done, checked at 07:56.** Everything Agent 5 posted matches.

- **Install** (`install-log.txt`):
  - The night launcher ended at 07:30:14 and wrote its `restored` line. At 07:33:57 the Desktop key read "SCRNSAVE.EXE present ''; ScreenSaveActive 0".
  - 07:33:42: "REFUSED: a launcher process is running: pid 33304", and nothing was copied. That is N-4; it failed safe.
  - 07:33:56-57: the re-run copied the three files. Live now: `bench/agent8/run/run-matrix.ps1` 1A522CDFE9DC36F8, `bench/agent5/launch/run-night.ps1` 565D30D40DC5025A and `bench/agent5/launch/README.md` B7CEBD635D847D4C. RUN-NIGHT.cmd is unchanged (D7A0362BE90C12B4).
- **day-update.ps1** (07:34:07-10) copied make-run-day.ps1, README-DAY.md and RUN-DAY.cmd into `build/agent5/day-draft/` and regenerated run-day.ps1 there (7 `# DAY:` lines; it parses).
- **`build/agent5/day-draft/`** holds exactly these 8 files, each with the hash Agent 5 posted:

| file | sha256 (first 16) |
|---|---|
| run-day.ps1 | B67EBD6C2C9A378C |
| run-day.diff | 3D0E8753683A17AA |
| make-run-day.ps1 | 4A96B0B947D0796B |
| launcher-ctl.ps1 | 6DDE3150B72D6B0D |
| RUN-DAY.cmd | B08645E9D4296AC1 |
| STOP-LAUNCHER.cmd | CE27332F354B1DBB |
| test-day.ps1 | 410FB2ECBA7B72B9 |
| README-DAY.md | 9739BCF8952146D9 |

- **run-day.diff** (58 lines, 7 DAY lines) has exactly these headers: `diff --git a/bench/agent5/launch/run-night.ps1 b/build/agent5/day-draft/run-day.ps1`, `--- a/bench/agent5/launch/run-night.ps1` and `+++ b/build/agent5/day-draft/run-day.ps1`. It has no user name and no absolute path, so day-draft N1 is closed.
- **Tests** (Agent 5's runs; I read the summaries):
  - `test-scrnsave.ps1 -Set installed -E2E` at 07:34:45, script 4D46A8E28E01B6ED (the revision I read): 45/45 PASS (`build/agent5/scrnsave-fix/results/summary-installed-073444.txt`). The real Desktop key was the same before and after. N-1 is closed.
  - `test-day.ps1 -Name all` at 07:35:58: 26/27. d-real-4 still required that `bench\agent5\launch\status` not exist, and that folder has existed since the real night run at 23:47. The launcher's own answer was right: exit 2, refusing `-StopAt` without `-DryRun`. d-real-4 now compares that folder before and after the case (test-day.ps1 L161-167). The re-run at 07:47:14 with test-day.ps1 410FB2EC…: 27/27 PASS (`build/agent5/day-draft/results/summary-all-074714.txt`).
  - `build/agent5/launch-test/run-tests.ps1 -Group go -StopAt '2026-11-23 11:00'` at 07:52:00: 16/16 PASS on run-night.ps1 565D30D4… (`build/agent5/launch-test/results/summary-go.txt`).
- **Test-only changes:**
  - run-tests.ps1 034F2E1F… to DD96C0E124BE4D91 (563 lines). The new `-StopAt` parameter (L18, usage L15-17) is passed on only if it is set, the case is not `-NoDry` and the case has no `-StopAt` of its own (L101). The summary header records it (L559). So it reaches dry runs only, which fits run-night.ps1: it refuses `-StopAt` without `-DryRun`.
  - test-day.ps1 D7DBC6EA… to 410FB2EC…: d-real-4 only, per Agent 5.
  - Limitation: no old copy of either file is left, and neither is tracked in git. I read the new lines only and rely on Agent 5 that nothing else changed. Low risk: both are test harnesses.
- **README-DAY.md** A36574ED… to 9739BCF8… (149 lines each), 4 one-line changes:
  - L57: the draft stays staged and is not installed before the break; the N2 text ("Use the installed copy") is kept;
  - L130: the 27/27 of 07:47:14, why 07:35:58 was 26/27, and the 45/45. N-2 is closed;
  - L134: my SAFE-IF rating of 05:57; Agent 11 has not rated it yet;
  - L138: install only after both ratings, while no night launcher runs, and not before the break.
- **N-3 is closed:** `build/agent5/scrnsave-fix/README.md` is now 1F0F3EC6C244925F. L13 calls 00:03:40 the refused W6 GO, and L15 and L143 date Agent 1's hand fix to 00:05:37. The word "workaround" is gone.
- **Public safety:** no user name and no absolute path in README-DAY.md, run-tests.ps1, test-day.ps1 or run-day.diff.

**Day-draft conditions:** condition 1 is closed. Condition 2 (install into `bench/agent5/day/`) and condition 3 (Agent 11's rating) wait until after the break.

## 6. Install tooling (added 06:45)

**Verdict: SAFE.** Both scripts copy nothing unless every check passes, and they enforce the order: install-scrnsave.ps1, then day-update.ps1, then the tests (README L85-86, L96).

- **install-scrnsave.ps1** (77 lines).
  1. No window or launcher: no `perf-notes/WINDOW-HOLD.txt` (L31), the mutex `Local\Agent5RunNight-real` is free (L33), and no run-night or run-day PowerShell process other than itself (L34-35; see N-4).
  2. The night launcher ended and put the screensaver back. The first line of state.txt must match `^state\s+ended\b` (L43); the launcher writes that through `Set-State 'ended'` (run-night.ps1 L1012). screensaver-saved.txt must have a `^restored ` line (L46-48); Restore-Screensaver writes `restored <time>` (run-night.ps1 L477). The Desktop key is only read (L50-54).
  3. The files: each staged file must have its "after" sha (L61), and each live file its "before" or "after" sha (L62-64). Anything else refuses, so a change by somebody else is caught.
  - Any failure: nothing is copied, exit 2 (L66). `-Check` stops before the copy (L67). Each copy is re-hashed, with exit 3 on a mismatch (L70-75). A partial copy can be finished by running it again, because installed files are skipped (L62).
- **day-update.ps1** (64 lines).
  - It refuses unless the installed run-night.ps1 is 565D30D4… (L37-38), and unless the draft files are the old or the staged ones (L40-48).
  - It copies the three files, runs make-run-day.ps1 in build/agent5/day-draft/ (L52-56), and then requires run-day.ps1 = B67EBD6C… (L57-58) and exactly the three repo-relative diff header lines (L59-61). So N1 is closed in day-draft/ once it has run.
  - It writes only in build/agent5/day-draft/ and to the log. Nothing goes to bench/agent5/day/.
- **Observed, install-log.txt.** At 06:36:00 day-update refused, because run-night.ps1 was still 16B90FA8…. At 06:36:20-22 `install-scrnsave.ps1 -Check` refused on the four launcher checks (the mutex, pid 19960, state waiting-for-go, no `restored` line) and copied nothing. The Desktop key read "SCRNSAVE.EXE present ''; ScreenSaveActive 0".

## Read / sent

- Read: the package files above; base/ and new/ (7 files each); the live files in §1; scrnsave-fix.diff against my own diffs; test-scrnsave.ps1 and e2e-driver.ps1 in full; the results summary and the e2e case files. At 06:39-06:45: install-scrnsave.ps1, day-update.ps1, install-log.txt and README.md EDA4D4F9… in full, plus run-night.ps1 (16B90FA8…) L446-481 and L1012. At 07:34-07:56 (§5): install-log.txt again; the live and day-draft hashes; run-day.diff; README-DAY.md 9739BCF8… against A36574ED…; the new lines of run-tests.ps1 and test-day.ps1; the three test summaries; scrnsave-fix/README.md 1F0F3EC6….
- Sent: to Agents 5, 8 and 1 at 06:33 (§1-§5); to Agents 5 and 1 after §6 was added; to Agents 5 and 1 after §5 was filled in.
