# RT-SMOKE kit (S5 Phase 3: T2 + F3) - rating packet for M10 (M2, 2026-11-25 21:18)
Answers phase3-bins-rating.md (3F84C0DB) P1-P5 + N1. Static work only (user pause): no dryrun yet.

## Files (sha256)
| file | sha256 |
|---|---|
| RUN-RT-SMOKE.cmd (waiter pins this) | 0F33351CB7097B88E135DA6A2E42BEA55E8E737C480A3420E08E5DD098E5FA69 |
| rt-smoke-run.ps1 | 630D1F00644E659295946E4FDC633AA76D86403102510022BB789CA3C8B832EC |
| rt_smoke_post.py | 0419882CC71BAB844A753D0B8FABA1A5DE2B58C07B539C7BFEED1F3EC7939250 |
| mkpins_rt.py (writes the .cmd) | 6A9B01A3439F1594073A21D62CEB61116DD52D661FEDD514BEEF885C65063576 |
| pins-test/tamper_test_rt.py | 207988FABD3A234BD317F554E1E12FB3F453B6B4DD53E38BCA28695DE58BE16E |
| pins-test/tamper-test-rt.txt | DC0A356DAE5589E902A58F02C27452822240C5C67CD6FD6CE4FDA5B00F367114 |
| pins-test/guard_regex_test.ps1 (+ -KitPs1 param, + rt case) | 608DE47ED01ABDF7EAE8C90900B4ECA300C2597F0AD9CC62A09E59345C877D91 |
| pins-test/guard-regex-test-rt.txt | 6ECBC50E333D838E6F22504AC11BA8DEB6A5CD8F69EB3CF0938ACE546629FC13 |
| pins-test/rt-post-selftest.txt | 761A1A58E1735FCF644463623EE30066A39157F391FC8C8DBF1963C27E5A9D62 |

## Arms (one approval, order T2 F3A F3B, 240 s each, attract-long pad route, 20 s settle, fresh run dir each)
| arm | bin (MANIFEST pin) | toml | -Cvar | shots |
|---|---|---|---|---|
| T2 | s5/devs5toml-bin (87DF5ED9) | harness legodimensions.toml (B763DABB) | framerate_limit=60 (= toml value; as devfinal2 refs) | none |
| F3A | s5/natives5fsr1-bin (102AAD90) | harness toml (present_effect='fsr') | native_fps_limit=60 (as nativefinal2 refs) | 60 120 146 200 s |
| F3B | s5/natives5fsr1-bin | -Toml native-fsr1/perf-bilinear.toml (FA47B1E3, pinned in the .cmd AND checked by the ps1) | native_fps_limit=60 | 60 120 146 200 s |

## P-mapping
- **P1** (T2 never timed): post gates exactly one warning-level `present_effect 'fsr' ... rejected` line with the
  '(reported before logging started)' suffix, 0 FFX-fallback INFO lines, 0 new error/critical vs devfinal2 (refs
  1805-cold-ship60 0FB3DC8A, 1815-ship60-r1 850B9BE0, sha-pinned in the post), runstats markers of the refs all present,
  0 new unknown cvars, check-defaults --mode xenos PASS. No timing output.
- **P2** (F3 untimed): F3A/F3B gates are functional only (clean exit, no dumps/WER, markers, 0 new error vs nativefinal2
  refs 1809-cold-nat60 F2F652C2 / 1820-nat60-r1 6F17177F, check-defaults --mode native, 4 ok non-black shots). No perf verdict.
- **P4**: frames.csv (>= 2000 rows): F3A spatial_fsr_presented=1 on >= 90% of rows; F3B 0 rows with 1; both fsr_enabled=0
  on every row and 0 'Native FSR 1:' log lines. Run-dir toml present_effect checked ('fsr' / 'bilinear'), toml not rewritten.
- **P5**: bin MANIFEST = pin + verify-bins before the run (refuse exit 3) and after every arm (FAIL stops the kit,
  results invalid); one kit at a time (refuses on a running game, Agent 8 runner, timed-window kit (D1 v2 -File regex),
  WINDOW-HOLD/GO, day launcher busy); interactive desktop only unless allowhidden; hold watch closes only our game.
- **P3**: f2/native3_boot_check-f2.diff C7BF17A0 applied to DimensionsRecomp perf/opt (working tree, not committed):
  `perf/bench/agent7/native3_boot_check.py` = 334716D5288E640BF10923CBDE8F34F1B9C8163256D5E2A7A698AF958019E90C
  (blob e7bd7fe4, numstat +41/-11, apply --check rc 0). test_f2 RESULT PASS before and after the apply.
- **N1**: make_patch.py (7A992CB4) strips a trailing `# comment` before comparing the present_effect value; test_f2
  (5A89BBBA) has the harness-comment.toml case; test.txt AEAC70FC: N1 PASS. ORIG now comes from `git show HEAD:`.

## Side-by-sides (Phase 4 visual review)
The post pairs F3A/F3B kit-shots by time -> `rt-smoke/post/sbs-<stamp>/sbs-NNNs.png` (FSR 1 left, bilinear right, full
frame) and `sbs-NNNs-crop2x.png` (2x centre crop), labelled; a detail number is info only (different frames).

## .cmd conventions
CRLF, ASCII, certutil sha256 of 14 files before anything else, fail closed (`PINOK == 14` required before the launch),
`powershell -NoProfile -ExecutionPolicy Bypass -File "%KIT%rt-smoke-run.ps1" %*`, words dryrun / pinsonly /
allowhidden / arms=. No D1 names anywhere in the .cmd; the ps1 has them only inside the D1 v2 predicate (as the nops kit).

## Static tests (all no game)
- `RUN-RT-SMOKE.cmd pinsonly`: `pins OK: 14 files`, rc 0.
- tamper test: ALL PASS (21 checks): clean, each of 14 pins tampered -> rc 3 naming the file, check-defaults.py and
  perf-bilinear.toml deleted -> rc 3 MISSING, tampered ps1 + dryrun word -> rc 3 and the ps1 never ran, one pin line
  removed -> `REFUSED: 13 of 14 pins verified` rc 3 (pinsonly and dryrun), stub ps1 pass-through rc 7 with
  `dryrun arms=F3A,F3B`.
- guard regex test (-KitPs1 rt-smoke-run.ps1): ALL PASS; also still ALL PASS on nops-smoke-run.ps1. New case: the rt
  kit's own -File command line does not trip the guard.
- PowerShell parser on rt-smoke-run.ps1: 0 errors.
- post --selftest on the ref runs (parse only): rc 0; T2 reject lines 0 on devfinal2 (expected: refs predate the
  rejection), F3A nat60-r1 14092 rows spatial=1 on 0, F3B nat60-r2 14150 rows, 4 side-by-sides from the nops kit-shots.
  The dryrun repeats this and requires the needles.

## Open / not in the kit
- P4 "overlay/settings toggles work" is a manual user check; not automated.
- The dryrun waits for the Overseer slot (user pause).
- Known selftest-only notes: on the agent8 ref run the run-dir toml lacks the -Cvar line (older run path); current
  run-game Set-Toml appends it, so the real-run gate is unaffected.
