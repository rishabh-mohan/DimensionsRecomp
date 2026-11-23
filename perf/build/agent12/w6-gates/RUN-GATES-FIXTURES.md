# run_gates fixtures: W5 and W4b (task #15)

Agent 12, 2026-11-22 21:55.
- Kit: `build/agent12/w6-gates/run_gates.py`. The wrapper `run_gates.ps1` adds the HOLD check and Below Normal.
- Fixtures: `fixture-w5.json` and `fixture-w4b.json`.
- Outputs: `out-selftest.txt`, `out-w5.txt` / `gates-w5.json`, `out-w4b.txt` / `gates-w4b.json`.

## How to check

```
python -B build\agent12\w6-gates\run_gates.py --selftest
python -B build\agent12\w6-gates\run_gates.py build\agent8\matrix\20261122-1756 --gate-log build\agent1\w5\quiet-1731.log --expect build\agent12\w6-gates\fixture-w5.json
python -B build\agent12\w6-gates\run_gates.py build\agent8\matrix\20261122-1541 --expect build\agent12\w6-gates\fixture-w4b.json
```

`run_gates.ps1` takes the same arguments. Each command prints the usual output, then `EXPECT: OK (n/n checks; fixture-*.json)`
and exits 0 when the fixture holds. Otherwise it prints one `EXPECT FAIL: ...` line per broken expectation and exits 5.

What `--expect` checks, from the fixture:
- `exit`: the run's own exit code (0, 1 or 3);
- for each gate:
  - `status` is equal;
  - every `key` substring is in the key;
  - every `details` substring is in some detail line;
  - no detail line has a `not_details` substring;
- `record`: the RECORD line is equal.

## Results (21:50; re-run 21:52 with the SHA-256 details: same tables)

| | W5 `20261122-1756` (17:56-18:29) | W4b `20261122-1541` (15:41-16:19) |
|---|---|---|
| extra argument | `--gate-log build\agent1\w5\quiet-1731.log` | none: W4b has no quiet-gate log |
| run exit (GATES line) | 0 | 1: G10, #6 B r2 had build processes |
| EXPECT | OK 57/57 | OK 53/53 |
| time (Below Normal; SHA-256 of every exe/dll copy) | 24 s; 83 s with the PC busy | 24-43 s |
| RECORD | `overlay best_efficiency (16/16, no change); quiet gate RELAXED; non-game load 3.01-4.14 cores` | `overlay best_efficiency (17/17, no change); quiet gate NOT RECORDED; non-game load 3.07-6.30 cores` |

### W5 table (out-w5.txt)

| gate | status | key number |
|---|---|---|
| G1 every switch rated | MANUAL | 5 arms; switches beyond the common set (framerate_limit=0): base 0, s0 0, d11 8, d11t 8+1 env, d11p 9 |
| G2 one bin per arm, as built | PASS | 16/16 runs on their arm's bin (MANIFEST + exe/dll SHA-256); 2 bins |
| G3 every planned run completed | PASS | 16/16 runs OK, exit 0x00000000, wm_close, runner exit 0; plan.txt 16 runs (1 cold); arms 5/5 as planned; no launcher log |
| G4 P2's fallback never runs | n/a | no run arm sets shared_memory_single_hold_rearm=true |
| G5 C1 verify on gate A | n/a | no run arm sets physical_protect_keep_watch=true |
| G6 keep only under G | n/a | no run arm sets physical_protect_keep_watch=true |
| G7 inert on native | n/a | no run arm sets physical_protect_keep_watch=true |
| G8 nothing stale, no new errors | PASS | stale/fault/Protect-failed lines in 0/16 runs; logdiff vs base (x4): FAIL findings in 0, NEW messages in 0/16 runs (0 kinds) |
| G9 launch-only switches as planned | PASS | 16/16 runs: params.cvar, args, env_set and toml_set = the arm's |
| G10 per-run validity | PASS | 15/15 scored runs valid; proof lines ok in 16/16 runs; free RAM >= 6 GB in 16/16; slow state 15/15 scored (info) |
| G11 power overlay | PASS | overlay best_efficiency in 16/16 runs, no change inside any window; scheme Balanced; AC 1; saver 0 |
| G12 quiet gate | PASS | RELAXED (NOT QUIET after 20 min) at 17:51:55 [quiet-1731.log]; Defender 0.77-1.14 cores over 20 one-min samples; non-game load 3.01-4.14 cores (median 3.30), 0 flagged |

### W4b table (out-w4b.txt)

| gate | status | key number |
|---|---|---|
| G1 every switch rated | MANUAL | 4 arms; switches beyond the common set (framerate_limit=0): d0 0, B 0, d3 0, d11t 8+1 env |
| G2 one bin per arm, as built | PASS | 17/17 runs on their arm's bin (MANIFEST + exe/dll SHA-256); 3 bins |
| G3 every planned run completed | PASS | 17/17 runs OK, exit 0x00000000, wm_close, runner exit 0; plan.txt 17 runs (1 cold); arms 4/4 as planned; no launcher log |
| G4-G7 | n/a | no P2 or keep-watch arm |
| G8 nothing stale, no new errors | PASS | stale/fault/Protect-failed lines in 0/17 runs; logdiff vs d0 (x5): FAIL findings in 0, NEW messages in 0/17 runs (0 kinds) |
| G9 launch-only switches as planned | PASS | 17/17 runs: params.cvar, args, env_set and toml_set = the arm's |
| G10 per-run validity | FAIL | 15/16 scored runs valid; proof lines ok in 17/17 runs; free RAM >= 6 GB in 17/17; slow state 16/16 scored (info) |
| G11 power overlay | PASS | overlay best_efficiency in 17/17 runs, no change inside any window; scheme Balanced; AC 1; saver 0 |
| G12 quiet gate | NOT RECORDED | no gate log; non-game load 3.07-6.30 cores (median 3.67), 2 flagged (#2 d0 r1 6.30, #3 B r1 4.98) |

- The W4b G10 FAIL is real: Agent 8's runner marked #6 B r2 `not timing: build processes: clang++:34584 clang++:36068
  clang++:6544`.
- W5 and W4b ran without the launcher (`no launcher log`). G3's END-line check and G11's launcher scheme line are
  tested only in the selftest.

## Independent sources

`fixture_facts.ps1` re-derives the facts with PowerShell only (no python, no run_gates code). Its run at 21:24-21:26
exited 0, and its output is `out-facts.txt`. It reads:
- results.csv and plan.txt;
- matrix.json and the bins' MANIFEST.txt;
- each run dir's game*.log and sys.json;
- the quiet log.

The exe SHA-256 values come from `Get-FileHash` (21:47). Checker a8f50f28 (21:26) re-ran every command and checked
the facts by hand.

| Gate | What the fixtures expect | Independent source | Agrees |
|---|---|---|---|
| G1 | W5 has 5 arms: base 0, s0 0, d11 8, d11t 8+1 env, d11p 9 switches beyond framerate_limit=0. W4b has 4 arms: d0 0, B 0, d3 0, d11t 8+1 env | The checker listed d11's 8 cvars from matrix.json; d11p = the 8 + timer_queue_precise_wait; d11t = the 8 + env REX_TIMER_WAIT_BLOCKING=1 | yes |
| G2 | W5: 16/16 runs, 2 bins (devoff3: base; devoff4: the rest). W4b: 17/17 runs, 3 bins (devoff2: d0, d11t; devoffB: B; devoff3: d3). MANIFEST SHA-256: devoff2 B87DC2D2CA22379F, devoff3 B9C5175DA1904235, devoff4 16DCC9399239E577, devoffB 8709476FF4778768. exe SHA-256: devoff2 7F0B1C1C84BC66FF, devoff3 2522D43605D8A9BF, devoff4 6BE3C713229232B2, devoffB C3F8686EBDD83340 | out-facts L10-11 and L36-38 (MANIFEST hashes, exe sizes). Get-FileHash 21:47 (exe hashes). The checker found run.json bin_dir = the arm's bin in 16/16 W5 runs | yes |
| G3 | W5: 16/16 OK / 0x00000000 / wm_close / runner exit 0; plan 16 runs (1 cold); 5/5 arms. W4b: 17/17; plan 17 (1 cold); 4/4 | out-facts L3-7 and L28-33 | yes |
| G4-G7 | n/a: no arm sets shared_memory_single_hold_rearm or physical_protect_keep_watch | matrix.json cvars (G1 list above) | yes |
| G8 | 0 stale/fault/Protect-failed lines; logdiff FAIL 0, NEW 0 | out-facts L12 and L39 (0 lines, a game*.log in every run) | the line counts agree. The logdiff is Agent 8's gate_logdiff.py, used as is, not re-derived |
| G9 | 16/16 and 17/17 runs: params.cvar, args, env_set and toml_set = the arm's | The checker compared run.json params.cvar with matrix.json (W5) | yes |
| G10 | W5: 15/15 valid. Proof lines (timer1ms/optout/precise): d11 and d11t 1/1/0, d11p 1/1/1, base and s0 0/0/0. W4b: 15/16 valid (#6 B r2, build processes), d11t 1/1/0, the rest 0 | out-facts L3 and L13-18; L28, L31 and L40-44. The checker found exactly 1 opt-out line in each d11/d11t/d11p run and the precise line only in d11p #6/#10/#14 | yes |
| G11 | overlay best_efficiency in 16/16 (17/17) runs, scheme Balanced, AC 1, saver 0 | out-facts L19-23 and L45-49 (sys.json, both sections) | yes |
| G12 | W5: RELAXED (`NOT QUIET after 20 min` at 17:51:55), Defender 0.77-1.14 cores over 20 samples. W4b: NOT RECORDED. Non-game load 3.01-4.14 (W5) and 3.07-6.30 (W4b) | out-facts L24-25: 20 FAIL lines, L22 `17:51:55 NOT QUIET after 20 min`. W4b: no quiet log | the gate mode agrees. The Defender range and the non-game load come from w6_env_record (also in `w5-env-record.json`) and are not re-derived |

## Selftest: 51 checks (out-selftest.txt)

- **2 checks added by task #24 (2026-11-23), after the G12 gap fix:** a gate line inside the start minute
  (06:50:01, dir `…-0650`) is G12 PASS at 0 min; a gate line 5 min after the window start is CHECK. Before the fix,
  `% 1440` read a gate line inside the start minute as 1439 or 1440 min, so all 7 night windows had G12 CHECK.
  w6_env_record's own selftest gained 4 gap checks (16/16, `out-envrec-selftest.txt`).
- **Re-run 2026-11-23 05:54 (`night/recheck-kit.ps1`):** selftest 51/51; W5 `EXPECT: OK (57/57)`, exit 0; W4b
  `EXPECT: OK (53/53)`, run exit 1 (G10). The tables did not change.

- **29 unit checks:**
  - the END and START line regexes;
  - window-log discovery (END line, runner file, START time, dry runs ignored);
  - plan.txt parsing and the slow state;
  - 13 proof-line cases, kv/env normalising and the timing-forbidden switches;
  - exit codes, and the logdiff against merged reference runs.
- **9 checks: a synthetic W6-like matrix, end to end.**
  - Arms s0/p2/p2f/p2fc on one temp bin with the s4-p2c string, plus side 1, gate A and a launcher window log. The
    log follows run-night.ps1's order: STRICT gate line, power scheme line, START, END.
  - Then a fault variant: a fallback on side 1, `C1 verify K:` on gate A and a stale line make G4, G5 and G8 FAIL
    (exit 1).
- **11 cases from the checker's findings:**
  - a crash inside G9: G9 is ERROR with the exception, and the other 11 gates still run;
  - ERROR alone gives exit 3;
  - a crash outside the gates: traceback, `GATES: ERROR; exit 6`, exit 6;
  - an unknown switch makes G10 CHECK, named in the key;
  - a dll copy of the same size with another SHA-256 makes G2 FAIL;
  - s0 on a second bin: G2 FAILs with `--one-bin` and PASSes without it;
  - G11 PASSes with uniform sys.json, and FAILs when one run has another power scheme and one has AC changing inside
    its window;
  - a gate line 40 min before the window makes G12 CHECK;
  - a side run in the timing runner's format (params.cvar list, no exe_sha256): its cvars are read, and its exe copy
    is checked by SHA-256.

## Checker findings (a8f50f28, 21:26)

The checker found no blockers: 4 should-fix and 9 minor.

| # | Finding | Status |
|---|---|---|
| 1 | A crash in Kit() or G1-G10 exits 1, like a FAIL, and skips `--expect` | **Fixed.** A crash inside a gate makes that gate ERROR (exit 3), and the other gates still run. A crash outside the gates prints the traceback and `GATES: ERROR; exit 6`, and returns 6 (5 with `--expect`). Exit 4 stays HOLD |
| 2 | G11: only the overlay decides | **Fixed.** Power scheme, AC or battery saver that is not one value, or that changes inside a window: FAIL |
| 3 | G2 compares exe/dll copies by size only; 2 bins still PASS | **Fixed.** Copies are compared by SHA-256, and the bin's exe hash is in the details. `--one-bin` FAILs unless the run arms use one bin; W6's read-out command uses it. Comparing with Agent 2's build-note hashes stays by hand |
| 4 | Unknown switches show only in the details | **Fixed.** G10 is CHECK, and the key names them |
| 5 | G4 PASSes with 1 target; WARNs show only in the details | **Partly fixed.** The key counts WARN lines. G4 still checks the dirs it is given (`PASS in n/n` shows how many); W6-GATES.md's read-out command names side 1, side 2 and gate A |
| 6 | G8: logdiff NEW gives CHECK; the reference includes the cold run | **By design.** A new message kind needs a look, not an automatic FAIL. The cold run adds the cold-boot messages to the reference, so a cold boot gives no false NEW |
| 7 | Sides are read only in the harness format | **Fixed.** `cvars` or `params.cvar`, and `env` or `env_set`. Without exe_sha256, G2 checks the side's exe copy by SHA-256, or says it could check only bin_dir and MANIFEST. Selftest case added |
| 8 | G12 gap > 30 min only in the details; ncpu = this PC's | **Fixed (gap):** G12 is CHECK. ncpu: the kit runs on the PC that ran the window, and `--ncpu` overrides |
| 9 | Timer line at least once; forbidden switches checked in matrix.json only | **By design.** W5 shows exactly 1 per run. A forbidden switch in a run but not in its arm already FAILs G9, which needs each run's params.cvar to equal the arm's |
| 10 | G3 is not the R0 pre-flight | **Documented.** G3 checks the finished matrix. The `-PlanOnly` + `-Quick` pre-flight stays with Agents 3 and 8 |
| 11 | The selftest's window log is not in run-night.ps1's order | **Fixed.** The order is now gate, scheme, START, END. Discovery by START time has its own unit check |
| 12 | The wrapper knows only `-Force` | **Fixed.** `-Force` or `--force` |
| 13 | G6/G7 text tied to C1 v3; slow state info only; 8 GB and Defender ~5% by hand | **Documented.** Update G6/G7 if C1 changes in W7+ |
