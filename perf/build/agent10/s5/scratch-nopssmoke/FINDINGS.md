# E10.2 static safety review: M2 RUN-NOPS-SMOKE kit

Read-only, done during the FREEZE (nothing from the kit was run). Reviewed 2026-11-25 18:30-18:40.

Kit location: the scripts sit directly in `build\agent2\s5\`, not in a subfolder. Output goes to `build\agent2\s5\nops-smoke\`. synth_post.py is in `nops-smoke\synth\`.

## Hashes reviewed (sha256/16)
| file | sha256/16 | note |
|---|---|---|
| RUN-NOPS-SMOKE.cmd | C89D405504A2A1B8 | = M10's C89D4055; no helper-sha pinning yet |
| nops-smoke-run.ps1 | 88C1ABBC7163B835 | = 88C1ABBC |
| nops_smoke_post.py | CA5222707A8465FD | = CA522270 |
| nops-smoke\synth\synth_post.py | 3C433752D4363B39 | = 3C433752 |

Helpers read: harness\run-game.ps1 C2533FDFE9A3A494, harness\guard.ps1 7A71E72057A0C87F, harness\winhelper.cs 37619E3DA38CE249
(same versions as in the M3 review), build\agent2\session3\verify-bins.py and build\agent2\final\check-defaults.py (write sites only).

State now: `build\agent2\s5\devs5nops-bin` does NOT exist, and `$pin = 'TBD-SET-AFTER-BUILD'` (run L41). A real run therefore always refuses (L76-77, L83). That is a safe latch, but the kit cannot be used until both are set.

## 1. Kill sites
| site | what | target |
|---|---|---|
| nops-smoke-run.ps1 L190-192 | Stop-Job / Remove-Job | its own shot job ($job from Start-Job L187) |
| run-game.ps1 L302-304 (helper) | WM_CLOSE via CloseAll(gamePid), CloseMainWindow, Kill | its own `$p = Process.Start` (L233) |
| shot job (run L116-135) | none: only Get-Process + winhelper.Shot | - |
| nops_smoke_post.py, synth_post.py, check-defaults.py | none | - |
Result: no Stop-Process, taskkill, or kill by name or title. OK.

## 2. Write paths
- nops-smoke\logs, nops-smoke\post (run L42-44); runs into nops-smoke\runs or nops-smoke\dryrun-runs (L37-38). run-game writes only inside its run dir.
- Recursive Remove-Item of nops-smoke\dryrun-runs after a reparse-point check (L166-168).
- nops_smoke_post.py: --out (L357-359) and joined logs to `<kit>\nops-smoke\post\joined-<run>.log` (L86-89). check-defaults.py is run as a subprocess and only reads the log (check-defaults L89).
- synth_post.py: creates and rmtrees the fixed path nops-smoke\synth\fake-run (synth L6-9, L33).
- Shot job: `<dir of the found game's exe>\kit-shots\` (run L124-125, L130, L133). Normally that is our run dir. The process match is NOT path-filtered (L120), so a foreign game started within 180 s after t0 would get kit-shots\ written next to ITS exe, possibly in a pinned bin. -> SHOULD S2.

## 3. Pinned bin (devs5nops-bin)
- Checks: verify-bins on the bin (L79; writes only with --out, which is not passed). MANIFEST sha256 must equal $pin (L81-83). Both are refusals for a real run (L102-104).
- There is NO work copy. run-game gets `-BinDir <pinned bin>` (L40, L108) and mirrors it by HARD LINKS (run-game L104-111). Every run dir shares its inodes with the pinned bin.
  - Evidence from M16's smoke run on the same harness: the game does not rewrite mirrored files. legodimensions.toml and native-environment.ini are never linked (run-game L106). The vpad DLL is a fresh copy (L174), and run-game refuses if the bin has its own xinput1_4.dll (L168).
  - Gap: verify-bins runs only before the first arm, never after the last one. Any later edit or attribute change in a run dir (e.g. `Remove-Item -Force` clearing ReadOnly) lands in the pinned bin. -> SHOULD S4.

## 4. User dir
- The kit never passes -UserDir or -SeedXenos (L108). run-game uses `<run>\user` (run-game L117-119, L148).
- The post gates it: seed_xenos empty, user_data_root = <run>\user, no storage file older than the run (post L230-242).
- Inherited LEGO_*/PLUME_* env vars are removed by run-game (L185). No APPDATA/USERPROFILE/registry writes anywhere in the kit.

## 5. Shots
- winhelper.Shot (winhelper L129-158): PrintWindow(PW_RENDERFULLCONTENT) first. The CopyFromScreen fallback runs only when the PrintWindow result is black AND the game window is in front (L146-153). Otherwise it saves the black image and says so. Other windows are never captured. Good.
- Target = the largest visible window of the found PID (MainWindow L81-93). The PID comes from `Get-Process legodimensions | StartTime >= t0-2 | first` (run L120): no path filter (see S2).
- Shots are taken 60/120/146/152/200 s after game start, T1/T2/N1/N2 only (L51, L187).

## 6. Guards
| guard | where | status |
|---|---|---|
| WINDOW-HOLD | run L85-86 (start), L182 (between arms) | refuse. NOT watched during an arm (no holdwatch) -> S3 |
| WINDOW-GO | - | missing -> S1 |
| Agent 8 runners | guard.ps1 via run L95-97 (and run-game L90-94) | run-matrix/run-timing/first-boot/RUN-TIMING-MATRIX only. window-s5.ps1 / RUN-WINDOW-S5.cmd missing -> S1. A live check at 18:22 saw `run-matrix.ps1` pid 9196, so a run now would refuse |
| any game running | run L93-94, L180-181 (before every arm); run-game L84-88 | refuse |
| hidden desktop | run L98-101 unless allowhidden | refuse |
| day launcher | run L87-92 (waiting-for-quiet / running) | refuse (state now `waiting-for-go`, which does not refuse) |
| RAM / compile running | - | missing (NIT) |
| dryrun | L102-104 | refusals are only reported. The dryrun proceeds anyway |

## 7. Helper lifetime / Ctrl-C
- There is no try/finally anywhere in nops-smoke-run.ps1. The only helper is the shot job (Start-Job, its own powershell process). It is bounded: 180 s to find the game (L187, L118-123), then the last shot at 200 s after game start. After each arm it gets Wait-Job 30 s, then Stop-Job and Remove-Job (L189-193).
- Ctrl-C or console close mid-arm: run-game dies before its close block (run-game L297-306, no finally). The game (GUI) is ORPHANED and nothing closes it. The job process exits with its parent session or at its own bound. -> SHOULD S3.
- WINDOW-HOLD during an arm is honoured only at the next arm boundary. That is up to 240 s + 60 s close + 20 s settle, about 5 min late. -> SHOULD S3.

## 8. Helper-sha pinning in the .cmd
- NOT present in C89D4055. The .cmd (L13-21) only forwards the args to powershell.
- Nothing pins run-game.ps1, guard.ps1, winhelper.cs, vpad\vpadhost.cs, routes\attract-long.txt, verify-bins.py, check-defaults.py, nops_smoke_post.py or nops-smoke-run.ps1 itself. Re-review when M2 adds it: it should hash all of these and refuse (exit 3) on a mismatch BEFORE launching powershell, or as the first step in the .ps1.

## 9. Is the dryrun heavy?
Moderate. It is lighter than M3's (no bin copies), but not freeze-safe:
- verify-bins hashes the whole bin (devs5sync-bin is 8 files, 214 MB, so expect similar). L79 runs even when refused.
- 6 x run-game -DryRun, each running Add-Type (C# compile of winhelper.cs + vpadhost.cs via csc) and building a hard-link mirror.
- The shot-job self-test starts a powershell job and runs Add-Type again (L152-155).
- The post self-test parses the two sync-smoke runs' logs and writes joined logs (L156-165).
- Right now the bin is missing, so the dryrun FAILs at L150 and still runs the rest.
Do not run it during the FREEZE.

## Findings
BLOCKER: none. A real run is impossible today: no bin and a placeholder pin.

SHOULD
- S1 run L85-101: no WINDOW-GO check, and guard.ps1 L14 misses window-s5.ps1 / RUN-WINDOW-S5.cmd. The S5 window is only caught while run-matrix.ps1 is alive.
- S2 run L120, L124: the shot job takes the first legodimensions started after t0-2 without a path filter, then creates kit-shots\ next to that process's exe. Filter on `Path -like "$runsRoot\*"` (as holdwatch does) and write to our run dir only.
- S3 run L177-200: no try/finally and no holdwatch. Ctrl-C orphans the game, and WINDOW-HOLD waits up to ~5 min. Add holdwatch (build\agent3\s4b\holdwatch.ps1 -RunsRoot nops-smoke\runs) or poll WINDOW-HOLD in the job. Add a finally that closes a game under nops-smoke\runs.
- S4 run L40/L108 + run-game L104-111: run dirs hard-link the pinned bin. Re-run verify-bins and the MANIFEST check after the last arm (and report in post), or use a sha-checked work copy as M3's kit does. Never delete runs with `Remove-Item -Force` on read-only files.
- S5 .cmd: helper-sha pinning is not there yet (item 8).

NIT
- N1 run L41: `$pin` is a placeholder. Set it from nops-bin\BIN-PINS.md together with staging devs5nops-bin, and re-review then.
- N2 run L72: check-defaults.py is required by the preconditions and is used by post L31/L270. OK, but it is not pinned (S5).
- N3 no RAM, compile or lock checks. Two instances would race (both pass L93).
- N4 dryrun: refusals are not enforced (L102-104), so verify-bins and the mirrors run even while a runner is active.
- N5 synth_post.py rmtrees a fixed in-kit path (synth L7, L33). Fine, but it is not run by the kit.

## Proposed verdict: SAFE-IF
1. devs5nops-bin is staged and `$pin` is set to the BIN-PINS value (until then a real run refuses by design).
2. The helper-sha pinning M2 is adding is re-reviewed and refuses on a mismatch.
3. Started only after the S5 window, on explicit clearance. No dryrun during the FREEZE.
4. Either S3 is fixed (holdwatch plus a close in finally), or the operator accepts that WINDOW-HOLD is honoured only between arms (up to ~5 min) and that Ctrl-C needs a manual game close.
5. S2 is fixed, or no other launcher is running (already required by the guards).
