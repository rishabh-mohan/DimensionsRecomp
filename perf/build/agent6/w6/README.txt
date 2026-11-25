W6 logdiff kit (Agent 6, task #16 part 2). Staged and tested 22:39-22:47, 2026-11-22. Read-only, stdlib Python only.

MORNING COMMAND (only on Agent 1's word; it checks perf-notes\WINDOW-HOLD.txt itself and refuses while it exists)
  build\agent6\w6\RUN-W6-LOGDIFF.cmd build\agent8\matrix\<W6 folder>
Same thing by hand, from the repo root:
  python -B build\agent6\w6\w6_kit.py build\agent8\matrix\<W6 folder> --expect build\agent6\w6\expect-w6.json --ref s0
- Runtime: about 1 s for 16 runs (W5: 0.8-1.3 s, including both child tools).
- Exit codes: 0 = no FAIL; 1 = at least one FAIL; 2 = usage error; 3 = HOLD file exists (.cmd only).
- Options after the folder override the defaults (--expect, --ref, --out, --matrix-json, --skip-logdiff, --top N).
- Nothing is written into the matrix folder (the kit refuses an --out inside it).

OUTPUT: build\agent6\w6\out-<folder>\
- w6-summary.txt: also printed. Contains the per-arm table, per-run table, STUCK-LOCK episodes, reasons (FAIL first), counts per arm and ONLY keys.
- w6-data.json: everything above as data.
- logdiff\: build\agent6\w4b\w4b_logdiff.py vs s0. Has gate_logdiff FAIL findings, NEW/MORE/GONE warning keys and ONLY keys (summary.txt, report-<arm>.txt, data.json).
- extra.txt: build\agent6\w4b\w4b_extra.py. Has the exact-text diff vs s0, close fields and per-run counts.
- logdiff.log, extra.log: the two child tools' console output. Both run at below-normal priority, one after the other.

WHAT IT CHECKS (details: the docstring at the top of w6_kit.py)
FAIL:
- A rule in expect-w6.json is broken: a missing 'require' text, a 'forbid' / 'forbid_all' text present, or an 'exact' count off.
- A STUCK-LOCK stall overlaps run.json's measured window ("timing invalid").
- A *.dmp file that no STUCK episode names.
- run.json: status != OK, valid_timing false, runner_error, exit code != 0, unclean WM_CLOSE, killed, exited early, or WER.
- cvars, env_set or bin_dir differ from the arm in the folder's matrix.json (else build\agent5\w6-draft\matrix-window6.json).
- logdiff: a gate FAIL finding or a NEW error/critical key that is not a STUCK episode's own line.
NOTE:
- A STUCK-LOCK episode outside the window, and its hang dump. Finding 10 is pre-existing.
- W/E/C line totals other than 40/0/0.
- Error/critical lines outside episodes.
- No clean-exit tail.
- Dialogs, runner exclusion, free RAM < 6 GB.
- logdiff NEW warning / MORE / GONE keys, and ONLY keys that no text of the arm's rules matches.
PASS: neither of the above.
Episode details: each STUCK-LOCK episode is listed with its CS, owner tid, lr and site (H1 = owner in sub_83FAF180, the L1 fence poll, finding 10; H2 = the function holding 83FB09F0, i.e. sub_83FB09E8; else 'other'), the waiter's function, the PM4 opcode, the dump, and the stall start against the measured window. Functions are looked up in the bin's legodimensions.map.
Slow state: Agent 11's math (E-core effective MHz < 800 for 3+ sys.csv rows from the first frame). This is information only, not part of the verdict.

EXPECTED W6 RESULT PER ARM (from Agent 3's devoff4b functional runs + source; see expect-w6.json 'notes' and expected-lines.md)
- s0, p2, p2f, f:
  - No line of their own. P2 and fix (i) print nothing; their only ON proof is the run.json cvar check.
  - 40/0/0, no C1 lines, and 0 NEW/MORE/GONE/ONLY keys vs s0. Toypad frame counts are run-varying and ignored.
- p2fc, fc:
  - 'C1 keep-watch: on (with physical_protect_hold_global_lock)' exactly once, 'C1 keep-watch: first kept protect at' once, and some 'N protects kept so far' lines.
  - These show as ONLY keys vs s0 but are named by the rules, so they give no NOTE.
  - No 'C1 verify', 'on, but' or 'blocked' lines. 40/0/0.
  - fc has no functional run; it is derived from source plus p2fc.
- Every arm: 0 'Recovered stale', 'Unhandled guest physical write fault' and 'Protect failed' lines (forbid_all -> FAIL).
- STUCK-LOCK is expected to be 0:
  - Finding 10 has only been seen on the vpad L route under host load.
  - W6's timed runs have no input script (title + attract, as in W4/W5).
  - If one does appear, the kit reports it, and it is a FAIL only inside the window.
- If the folder's matrix.json uses the old draft matrix-w6.json (bin 'S4b-bin-TBD'), every run FAILs the bin_dir check. In that case check which file the runner used.

TESTS (all exit codes as expected)
1. W5 (build\agent8\matrix\20261122-1756, 16 runs), --expect expect-w5.json --ref s0 -> out-test-w5\:
   - Verdict, exit 0. All 6 arms PASS; 40/0/0 in 16/16; STUCK 0; dumps 0.
   - cvars, env and bin match matrix.json; logdiff vs s0 F/N/M/G = 0.
   - ONLY keys: d11/d11t have the 1 ms timer line and d11p also the precise-wait line, all named by the rules.
   - Slow onset/pct per run and per-arm means equal Agent 11's numbers.
   - Runtime 0.8-1.3 s.
   - Bug found and fixed: logdiff keys are number-normalized ('1 ms' -> '# ms', 'C1' -> 'C#'), so rule texts are now matched normalized too (key_norm, via gate_logdiff.norm).
2. W5 with the default expect-w6.json -> out-test-w5-negative\:
   - Exit 0, "arms in the expect file with no run here: f, fc, p2, p2f, p2fc".
   - "no rules" NOTEs for base/d11/d11p/d11t; s0 PASS.
3. test_stuck_parse.py, a parser unit test on the 3 real hang logs (gate A, s4b-24, s4b-20): PASS.
   - 1 episode each, 6 lines, all fields.
   - gate A: owner lr 83FAF188 = H1 sub_83FAF180+0x8. s4b-24 and s4b-20: 83FAF200 = H1 +0x80.
   - Waiter lr 82A2A270, PM4 0x22, dump names right.
   - 83FB09F0 is in sub_83FB09E8; the no-map fallback works.
4. make_synth.py builds test-synth\W6SYNTH: 3 W5 s0 runs plus 3 'p2fc' runs with s4b-24's real C1 lines. Kit on it -> out-test-synth\, exit 1 as designed:
   - r1: gate A's real STUCK lines placed inside the window -> FAIL "timing invalid".
   - r2: the same lines placed after the window -> NOTE.
   - r3: clean -> PASS.
   - Hang dumps -> NOTE. The episode's NEW/critical logdiff keys did not FAIL. C1 ONLY keys were named by the rules.
5. RUN-W6-LOGDIFF.cmd on W5 with an --expect override -> out-test-w5-cmd\: same result, exit 0. With no argument: usage, exit 2.

FILES
- w6_kit.py: the kit.
- expect-w6.json: W6 rules.
- expect-w5.json: W5 rules, used for the test.
- RUN-W6-LOGDIFF.cmd: one-command wrapper.
- test_stuck_parse.py, make_synth.py: tests.
- expected-lines.md: the per-arm expected lines, from Agent 3's runs.
- Older: log_diff.py, log-diff.txt, src_grep.py, src-grep.txt.
- Night windows W9 / W5b / W4c (task #19): rules and wrappers for this kit are in build\agent6\wnight\ (see README.txt there).

2026-11-25 CHANGES (task s3, E5.1 for M6). w6_kit.py sha256 before 7BAA4486ADC18C85AA83554DEF61A76953ABCDD49DED652B9BD3CD684331A917
(copy: build\agent6\wnight\s3-regress\w6_kit.before.py); after: see build\agent6\wnight\s3-regress\SHA256.txt.
- A. Execution complete race: a run with no "[info] [core] Execution complete" line whose game.log ends with
  "Title terminated; hard-exiting process." and exit code 0 is INFO, not NOTE (logdiff GONE "Execution complete"
  limited to such runs is INFO too). Otherwise still NOTE. INFO never changes a verdict.
  Summary line "Execution complete race runs: N"; w6-data.json race_runs and per-run race/info.
- B. Shutdown watchdog: a game.log with "Shutdown wedged past the close request; hard-exiting." gets one NOTE
  "WATCHDOG: shutdown watchdog fired (3 s after WM_CLOSE)", which also explains the 41/0/0 total and the missing tail
  that come from that one warning line. Not a FAIL. Summary line "watchdog runs: N"; data watchdog_runs, per-run watchdog.
- Per-arm "levels" in an expect file override the global W/E/C level. A NEW warning key whose text the arm's
  require/exact rules name is not a NOTE.
- Arm ids in an expect file (and --ref) must match [A-Za-z0-9]+, else usage error exit 2. The run-dir arm regex
  reads "1234-off-sf-r1" as arm "off", so hyphenated ids cannot work.
- Harness mode: --run ARM=DIR (repeatable) instead of <matrix_dir> (both or neither -> exit 2). DIR is an Agent 3
  harness run dir (run.json with exit_code, exited_early, close_method, wer_seen, dumps, cvars{}, env{}).
  status OK iff exit_code 0, not exited_early, close_method wm_close, not wer_seen; valid_timing not checked
  ("functional only"); slow state skipped (INFO). cvars/env/bin are checked against --matrix-json: only the keys the
  arm lists, plus a FAIL for an unlisted s33 key (d3d12_pipeline_creation_no_wait, d3d12_resolve_after_drop_log,
  slow_frame_log_ms, d3d12_pipeline_creation_threads, async_shader_compilation, d3d12_bindless). The logdiff tools
  read a staging copy (game*.log + run.json only) in <out>\staging\runs\NNNN-<arm>-rK; nothing is written into the
  run dirs. Default --out build\agent6\w6\out-harness. Relative DIRs are relative to the repo root.
- Wrappers (RUN-W6/W9/W5B/W4C-LOGDIFF.cmd): KITROOT is set before any shift (shift also moved %0, so %~dp0 broke when
  options followed the folder).
- #33 pop-in: build\agent6\s33-popin\expect-s33.json + RUN-S33-LOGDIFF.cmd (see the notes in the expect file).
  Tests: make_test_s33.py, run by build\agent6\wnight\s3-regress\run_test_s33.ps1.
TESTS 2026-11-25 (all at below-normal priority; outputs in build\agent6\wnight\s3-regress\)
- 7 night dirs re-run with the wrapper rules (run_regress.ps1: 7/7 exit 0), diff_night.py -> DIFF.txt, exit 0:
  only A (0009-cold-s0, 0345-p2f-r4, 0429-off-r3, 0215-d11-r4, 0528-d11t-r6: NOTE -> INFO/PASS, their arms
  NOTE -> PASS) and B (W9 0108 0128-off-r2: one WATCHDOG NOTE, arm off stays NOTE; the only watchdog run).
- run_d2.ps1 (d2-*.out.txt): test_stuck_parse PASS exit 0; make_synth + kit exit 1 (same verdicts as out-test-synth);
  W9 test-s4b17 exit 1 and test-s4b17-neg exit 1 (same as stored); make_test_w9env 9/9 exit 0; wrappers without
  args exit 2. Summaries differ from the stored ones only by the two new header lines, paths and runtimes.
- run_test_s33.ps1: matrix 0, matrix-neg 1, harness 0, harness-neg 1, hyphen expect id 2, hyphen --run 2,
  mixed 2, none 2, no args 2; --check RESULT: PASS (test_s33.check.txt).
