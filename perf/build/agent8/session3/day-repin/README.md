# Day installer re-pin after M8's runner install (25 Nov 07:30)

M8's runner install (m8-runner-rating.md C08604D8, C1/C2) changed six files in `bench\agent8\run\`. The day installer `build\agent5\session3\install-day.ps1` (B79061A2) hard-codes one of them in its `$Night` set, so it now refuses. Nothing in `build\agent5` was edited.

## Files M8 changed (install log: `build\agent8\session3\install\install-log.txt`, originals in `build\agent8\session3\backup\20261125-073031\`)

| File (bench\agent8\run\) | old sha256 | new sha256 |
|---|---|---|
| run-matrix.ps1 | 1A522CDFE9DC36F8F976D374D020D8EB3102AAB4327BF10BAED31B0F369358CB | 72370A1E737A3A34399E78D6D8C670F8B5789F0B49212A53F4846D89EF790C04 |
| frame_summary.py | 0A7D35873E88E50E... | 987E0EC03456D5DC... |
| sys_summary.py | C95767DE04CB95E4... | 6FCE3630B13134D5... |
| drivers\sys-csv.ps1 | 017A4F3EB6252983... | F3F06AB013F2423E... |
| drivers\LdSys.cs | B452D25872E76ACC... | 4EFD5C91B5DF3F68... |
| selftest\sys_selftest.ps1 | 216DE7F4D91A69EF... | 5C2D20389BF8714D... (C2 header patch + the $r/$R row-count fix) |

## Where these files are pinned in build\agent5\session3\install-day.ps1 and build\agent5\day-draft\*

| Place | Kind | Files | Needs a re-pin? |
|---|---|---|---|
| `install-day.ps1` L43 (`$Night`) | hard-coded sha256, checked before and after the install (L64-67, L88) | run-matrix.ps1 | **yes**: 1A522CDF... -> 72370A1E... (the only hard-coded pin) |
| `day-draft\run-day.ps1` L184-203 `Get-PinFiles`/`Get-Pins`, L968-975 | hashed **at launcher start** and compared before and after every window (L689, L740, L901) | run-matrix.ps1, all `*.py`/`*.cs` in run\, everything under run\drivers\ (so frame_summary, sys_summary, sys-csv, LdSys); not selftest\ | no: there are no stored hashes. It just pins whatever is installed when RUN-DAY starts. Don't install anything into bench\agent8\run while it runs. |
| `day-draft\launcher-ctl.ps1`, `RUN-DAY.cmd`, `STOP-LAUNCHER.cmd`, `make-run-day.ps1`, `test-day.ps1` | no hash of a bench\agent8\run file (grep for the 6 old hashes and file names) | none | no |
| `day-draft\README-DAY.md` L145 | prose ("it pins only run-night.ps1, RUN-NIGHT.cmd and the bench\agent8\run files") | none | no |
| `day-draft\run-day.diff` L24-29 | the same Get-PinFiles text as run-day.ps1 | none | no |
| `day-draft\status-dryrun\*\pins.txt`, `day-draft\results\*` | old **outputs** of dry runs (the old hashes appear in them) | none | no (records, not checks) |

The night launcher `bench\agent5\launch\run-night.ps1` uses the same pin-at-start logic (L184-193), so it needs no change either.

## Re-pinned copy

- `install-day.ps1` (sha256 D2D1D11F8BD6D3133582DEB3BDBF90292FD06946BE5E87D844BB31E156479075): a drop-in for `build\agent5\session3\install-day.ps1`. Only L38 (comment, now two lines) and L43 (run-matrix pin) changed; see `install-day.diff`. It parses cleanly, and its encoding and line endings are unchanged.
- I did not add the other five changed files to `$Night`, since that would change what the installer checks. If that's wanted, add them with the new hashes above.

## Test

- I did **not** run the copy, as instructed. It derives `$Repo` from `$PSScriptRoot\..\..\..`, which only works from `build\agent5\session3\`; from `day-repin\` that path resolves to `build\`. Its `-Target` must also be under `build\agent5\session3\`. So no plan-mode run is possible from here.
- Instead I ran a read-only hash check of every pin in the copy (all 8 draft files + the 4 `$Night` files) against the disk at 07:33: **12/12 OK**, `bench\agent5\day` absent. That means the copy's hash checks would pass. Its other refusals (launcher running, WINDOW-HOLD) are runtime conditions.
