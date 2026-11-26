# nops-smoke kit D1 v2 + PINOK addendum (M2, after 51B6688E)

M10, 2026-11-25 19:55. A cross-check of build/agent2/s5/kit-d1-delta.diff (CFE0AF0720935358, 6076 B).

## Files

| file | sha256/16 | bytes | notes |
|---|---|---|---|
| build/agent2/s5/nops-smoke-run.ps1 | 4885AE6DA29A26BD | 21619 | LF; only the guard block changed vs pins-test/ps1-1D93442E.ps1 (= 1D93442E) |
| build/agent2/s5/RUN-NOPS-SMOKE.cmd | 51E7A02EABC6F576 | 4410 | CRLF 73/73 |
| build/agent2/s5/mkpins.py | E338841B385C7C97 | 4999 | template = the .cmd change |
| build/agent2/s5/pins-test/tamper-test.txt | 8403425E947D99C9 | 6154 | 19/19 PASS |
| build/agent2/s5/pins-test/guard_regex_test.ps1 | A064DE576AA356B0 | 2305 | not run by me |

## Verdict

**CONFIRMED.** D1 of 51B6688E and NIT N1 are both closed. The other conditions of 51B6688E stand: K3-K7, Z3-Z5 and D2.

## What I checked

**ps1 guard (D1 v2).**
- Compare-Object against the old copy shows that only the 3 comment lines and the Where-Object guard block changed.
- The new guard looks only at powershell/pwsh/cmd. It matches `-File\s+"?[^"]*(window-s5|run-matrix)\.ps1` (the same as M3 and natcmp L97), or cmd.exe whose command line has `RUN-WINDOW-S5[^\s"]*\.cmd`.
- I tested it with the name + command-line pairs below:

| process | command line | match |
|---|---|---|
| cmd.exe | `cmd.exe /c ""…\RUN-WINDOW-S5.cmd" "` (the waiter's form, as seen live at 18:40) | yes |
| cmd.exe | `cmd /c …\RUN-WINDOW-S5-v2.cmd` | yes |
| powershell.exe | `-File "…\window-s5.ps1"` | yes |
| powershell.exe | `-File …\run-matrix.ps1` (unquoted, as window-s5 launches it) | yes |
| powershell.exe | `Select-String -Path '…\window-s5.ps1'` | no |
| powershell.exe | `Get-Content …\RUN-WINDOW-S5.cmd` | no |
| python.exe | `x.py …\window-s5.ps1` | no |

- The cmd-only restriction on the .cmd alternative loses nothing. A .cmd always runs in a cmd.exe whose command line names it, even when a powershell launches it.

**.cmd fail-closed (N1).** PINOK starts at 0 and `:pin` increments it in the else branch. The launch requires BAD==0 and then PINOK==13. Tamper tests on my own scratch copy (same depth, so WS resolves the same; the launch line replaced by `echo WOULD-LAUNCH`; deleted afterwards):

| case | rc | output |
|---|---|---|
| untouched (real WS, 13 pins) | 0 | WOULD-LAUNCH |
| bad hash (post) | 3 | 1 changed |
| missing file (guard renamed) | 3 | 1 changed or missing |
| `:pin` label renamed | 3 | 0 of 13 verified |
| converted to LF | 3 | 1 of 13 / 12 of 13 verified (mis-seek caught) |
| one pin line dropped | 3 | 12 of 13 verified |

M2's own log: 19/19 PASS, including "pin line removed" with the pinsonly and dryrun words.
