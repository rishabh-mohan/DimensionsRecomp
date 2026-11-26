# Rating: M2 T2/F3 RT-smoke kit (RUN-RT-SMOKE)

Who/when: M10, 2026-11-25 ~21:25 local. Static review only (user pause active; nothing launched).

## Files (sha256/16, bytes) - all under WS\build\agent2\s5\

| file | sha256/16 | bytes |
|---|---|---|
| rt-smoke-kit-packet.md | 81D8131081EF0E03 | 5576 |
| RUN-RT-SMOKE.cmd | 0F33351CB7097B88 | 4512 (CRLF 74/74) |
| rt-smoke-run.ps1 | 630D1F00644E6592 | 21348 (LF) |
| rt_smoke_post.py | 0419882CC71BAB84 | 20996 |
| mkpins_rt.py | 6A9B01A3439F1594 | 5104 |
| pins-test/tamper_test_rt.py | 207988FABD3A234B | 3585 |
| pins-test/tamper-test-rt.txt | DC0A356DAE5589E9 | 6873 |
| pins-test/guard_regex_test.ps1 | 608DE47ED01ABDF7 | 2554 |
| pins-test/guard-regex-test-rt.txt | 6ECBC50E333D838E | 1242 |
| pins-test/rt-post-selftest.txt | 761A1A58E1735FCF | 10285 |

Base: my phase3-bins-rating.md 3F84C0DB (P1-P5, N1); bins devs5toml MANIFEST 87DF5ED9, natives5fsr1 MANIFEST 102AAD90; perf-bilinear.toml FA47B1E3; harness toml B763DABB.

## Verdict: SAFE-IF (R1-R5)

## What I checked

- .cmd: CRLF throughout. 14 pins: ps1, post, harness run-game/guard/winhelper/nvml/runstats/vpadhost, harness toml B763DABB, attract-long route, xinput1_4.dll, verify-bins, check-defaults, perf-bilinear FA47B1E3. Fails closed unless PINOK==14. The two bin MANIFEST pins (87DF5ED9, 102AAD90) live in the ps1.
  Scratch tamper (my own copy at the same dir depth, launch line replaced by echo, deleted afterwards): untouched -> rc 0 "pins OK: 14"; perf-bilinear hash changed -> rc 3; route renamed -> rc 3 MISSING; one pin line removed -> rc 3 "13 of 14 pins verified". 4/4.
- ps1 (read in full):
  - Refusals: WINDOW-HOLD/GO present, day launcher, running game, Get-ActiveRunners, D1 v2 guard regex, hidden desktop. Real run exits 3; -DryRun only notes them. Refusals are re-checked before every arm.
  - Pins: perf-bilinear re-hashed in the ps1; MANIFEST pins + verify-bins before the run and after every arm (Check-Bin; FAIL stops the kit).
  - Shot job: only images under runsRoot, process StartTime >= t0-2, read-only.
  - Hold job: polls 2 s, WM_CLOSE then Stop after 15 s, only our game; lifetime Seconds+600 = 840 s.
  - try/finally Stop-Ours kills only games whose path is under runsRoot plus its own child run-game powershell. rc != 0 stops the kit. Post runs after the arms.
  - run-game.ps1 supports -Toml (L55) and -Cvar, as the arms need.
- post (read in full): clean exit; no dumps/WER; bin_dir; exact cvars; run-dir toml == sha-pinned source toml except user_data_root/cvar keys; present_effect value; toml not rewritten; check-defaults; ref game.log sha pins as a gate; runstats markers; 0 new error/critical vs refs; 0 new unknown cvars; 0 'Native FSR 1:' lines.
  - T2: exactly one warning-level 'present_effect fsr ... rejected' line (with suffix).
  - F3A: >= 2000 rows, spatial_fsr_presented=1 on >= 90%, fsr_enabled=0.
  - F3B: 0 rows with spatial=1.
  - Shots: 4 ok; side-by-side PNGs.
  - Writes only under rt-smoke/post (out, joined logs, sbs PNGs). No perf verdicts.
- Phase 3 mapping:
  - P1: T2 is functional only (no timing), and the post gates the single reject line + 0 new ERROR. Met.
  - P2: natives5fsr1 is never timed here; F3B uses perf-bilinear FA47B1E3 pinned. Met.
  - P3: DimensionsRecomp perf/bench/agent7/native3_boot_check.py is now 334716D5 (numstat +41/-11, the only modified file in that dir, uncommitted working tree). F2 dir: diff C7BF17A0, make_patch 7A992CB4, test_f2 5A89BBBA, test.txt AEAC70FC. I take the Overseer's routing of this packet as the P3 OK; flag if that is wrong.
  - N1: L353 now strips trailing `# comment`. Closed.
  - P4: shots + sbs give the visual check; the overlay toggle stays manual (R5).
  - P5: MANIFEST pins fail-closed (ps1, before the run and after each arm; .cmd pins the ps1). Met for this kit.
- M2 evidence files hashed and match the packet (tamper, guard regex, post selftest).

## Conditions

- R1: dryrun ALL PASS after the pause ends; send me the log sha before GO.
- R2: interactive desktop only (no allowhidden); one kit at a time; not during timed windows or builds.
- R3: functional only: no perf numbers are quoted from these arms.
- R4: any file change -> re-hash, re-pin, re-rate the delta.
- R5: the P4 FSR overlay toggle stays a manual user check; the post's spatial share isn't a substitute.

## Findings

- NIT: no exclusive kit lock. Mutual exclusion relies on the game-running/active-runner refusals. In the ~20 s settle gap between arms another kit could start; ours then refuses at the next arm. That's safe, but the run would be lost.
- NIT: the >= 90% F3A spatial-share threshold isn't validated until the first real run. A false FAIL is safe.
- NIT: hold-watch lifetime is 840 s per arm (Seconds+600). Fine, but keep it in mind if Seconds is raised.
- NIT: close_method None is accepted (same as the nops kit). The clean-exit and dump gates still apply.
- NIT: -DryRun doesn't enforce refusals (by design); R1 covers the rest.
