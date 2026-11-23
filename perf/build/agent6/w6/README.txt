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
