# S5 rating: M2 RUN-NOPS-SMOKE kit

M10, 2026-11-25 18:38. Static review only (FREEZE active; nothing run). E10.2 did the full read (scratch-nopssmoke/FINDINGS.md 3F87CBC8, on cmd C89D4055). I re-checked the shot job, the bin path, the pins and the new .cmd myself.

| File | sha256/16 | Bytes | Note |
|---|---|---|---|
| build/agent2/s5/RUN-NOPS-SMOKE.cmd | 90013FDBA58A0CE7 | 3975 | new: 13 sha pins (mkpins.py), read by me |
| build/agent2/s5/nops-smoke-run.ps1 | 88C1ABBC7163B835 | 14796 | reviewed |
| build/agent2/s5/nops_smoke_post.py | CA5222707A8465FD | 20160 | reviewed; **changed at 18:34 to 54BA5CF9D85418DF (21304 B), not reviewed** |
| build/agent2/s5/synth_post.py | 3C433752D4363B39 | - | standalone, not run by the kit |

Helpers (all pinned by the .cmd and matching at 18:35): run-game C2533FDF, guard 7A71E720, winhelper 37619E3D, nvml 9F6E6E3B, runstats AE6C8B0C, vpadhost 5D929041, toml B763DABB, attract-long 4D35FAF4, xinput1_4.dll 309DF316, verify-bins 80FF4C5F, check-defaults D9936C56.

## Verdict

**SAFE-IF K1-K7.** No BLOCKER.
- **Kills.** The kit's only "kill" is Stop-Job/Remove-Job on its own shot job. run-game closes only its own PID.
- **Writes.** Everything goes under build/agent2/s5/nops-smoke/. The exception is the shot job's kit-shots dir (S2).
- **Pins.** The pin set is complete for the real-run, dryrun and post paths. Today the kit cannot start a real run anyway: devs5nops-bin does not exist, the bin pin is `TBD-SET-AFTER-BUILD`, and the .cmd's post pin no longer matches (both fail-safe).

## What I checked

- **.cmd pins (90013FDB).**
  - The 13 files are pinned by full sha256 via certutil. A missing file or a mismatch counts in BAD, which means exit 3 before the ps1 runs. `pinsonly` checks the pins only.
  - Completeness: the ps1 runs run-game, guard, winhelper, verify-bins and post, and checks for check-defaults. run-game loads vpadhost, nvml, runstats, the toml, the route and the vpad DLL. post runs check-defaults via sys.executable (post L270). All of them are pinned.
  - At 18:35, 12 of 13 matched. nops_smoke_post.py is now 54BA5CF9 versus pin CA522270, so the kit refuses until mkpins is re-run.
- **Shot job (L113-133, verified).**
  - It matches `legodimensions` by name with StartTime >= t0-2 s and no path filter (L120). It writes `<that exe's dir>\kit-shots` (L124).
  - Shots go through winhelper.Shot: PrintWindow, with CopyFromScreen only when the image is black and the game is foreground.
  - It is bounded: 180 s to find the game, then the shot times. After run-game returns it gets 30 s, then Stop-Job and Remove-Job.
- **Bin (L40, L108, verified).** BinDir is the pinned devs5nops-bin itself, with no work copy. run-game hard-links it into each run dir and skips the toml, ini, profile, dmp and logs. verify-bins and MANIFEST==pin are checked only at start (L79-83).
- **User data.** `<run>\user`. The kit passes neither -UserDir nor -SeedXenos, and post gates a fresh user dir.
- **Guards.** WINDOW-HOLD (at start and between arms only), day launcher, a running game, Agent 8 runners (guard.ps1), hidden desktop. Missing: WINDOW-GO and window-s5/RUN-WINDOW-S5. There is no try/finally and no holdwatch.

## Conditions

- **K1.** Stage the bin first: devs5nops-bin with its own MANIFEST, verify-bins PASS, and the real pin in L41.
  - If the bin stacks zpd-log, it must meet Z1-Z5 (68813034).
  - If it is the single-TU nops bin, run with `nozpd` (the zpd cvar would otherwise be unknown to the bin), and N1-N4 of 6487C0EB apply.
- **K2.** Re-run mkpins after M2's last edit, and send me a delta for nops_smoke_post.py (CA522270 -> 54BA5CF9 now) and for any other changed file. Re-check `pinsonly` = exit 0.
- **K3.** Start only after the S5 window has fully ended (no window-s5, RUN-WINDOW-S5 or run-matrix process, no WINDOW-GO.txt) and the FREEZE is lifted, on the Overseer's GO. That includes dryrun (verify-bins over ~214 MB plus 6 Add-Type compiles).
- **K4.** One kit at a time, with no other launcher active during the session. The shot job would otherwise latch onto a foreign game started mid-arm and write kit-shots into that game's exe dir (S2).
- **K5.** WINDOW-HOLD only takes effect between arms, up to ~4.5 min late. If a hold is needed mid-arm, someone must close the game under nops-smoke\runs by hand. No Ctrl-C or console close mid-arm (S3).
- **K6.** After the session, run verify-bins on devs5nops-bin, because the pinned bin is hard-linked into the run dirs (S4). A FAIL invalidates the bin and its results.
- **K7.** Shots and timings are functional or smoke only: single-run timing (S2 of 6487C0EB).

## Findings

- **S1 (SHOULD).** Add WINDOW-GO and window-s5/RUN-WINDOW-S5 to the refusals (L85-101), as M16 and M3 did. Beware the any-command-line false refusals (D1 of F4EE7FC8).
- **S2 (SHOULD).** Shot job: filter on `Path` under `$runsRoot` (L120) so it can neither shoot nor write next to a foreign exe.
- **S3 (SHOULD).** Add try/finally cleanup that closes our game by path under runsRoot and stops the job, and poll WINDOW-HOLD during the arm (or start holdwatch).
- **S4 (SHOULD).** Use a sha-checked work copy of the bin (as the M16 and M3 kits do), or at least re-run verify-bins after each arm.
- **N1.** The placeholder pin refuses today (fail-safe).
- **N2.** dryrun skips the refusals; acceptable only under K3.
- **N3.** No RAM, compile or lock checks.
- **N4.** synth_post deletes a fixed in-kit path (safe).
