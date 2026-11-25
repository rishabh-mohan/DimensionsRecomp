build/agent6/wnight/ : logdiff rules and one-command wrappers for the night windows W9, W5b and W4c
Agent 6, task #19 (brief 22:54). Written and tested 23:00-23:10, 2026-11-22. Read-only on every matrix folder.

The kit is build\agent6\w6\w6_kit.py (task #16), unchanged; build\agent6\w6\README.txt says what it checks.
This folder adds only the per-window rules (expect-*.json) and the wrappers.

COMMANDS (run only on Agent 1's word; each refuses with exit 3 while perf-notes\WINDOW-HOLD.txt exists,
runs the kit at below-normal priority, and takes about 1 s)
  build\agent6\wnight\RUN-W9-LOGDIFF.cmd  build\agent8\matrix\<W9 folder>     expect-w9.json,  reference off
  build\agent6\wnight\RUN-W5B-LOGDIFF.cmd build\agent8\matrix\<W5b folder>    expect-w5b.json, reference d11
  build\agent6\wnight\RUN-W4C-LOGDIFF.cmd build\agent8\matrix\<W4c folder>    expect-w4c.json, reference d0
Output: build\agent6\wnight\out-<W9|W5B|W4C>-<folder>\ : w6-summary.txt (also printed), w6-data.json, logdiff\, extra.txt.
Exit: 0 = no FAIL, 1 = at least one FAIL, 2 = usage error, 3 = HOLD file exists.
Options after the folder override the defaults (--out <dir>, --skip-logdiff, --top N). The arms come from the
folder's matrix.json; bench\agent8\run\matrix-window9/5b/4c.json is passed only as the fallback.

RULES (arms, bins, cvars and env read from bench/agent8/run/matrix-window9.json, -5b.json, -4c.json;
cmp_arms.py: W5b's d11/d11t/d11p and W4c's d0/B have the same bin, cvars and env as the W5 / W4b folder arms)
Every window:
  - forbid_all: Recovered stale physical page protection, Unhandled guest physical write fault,
    PhysicalHeap::Protect failed, BaseHeap::Protect failed (W9 also: "is not a plain number").
  - STUCK-LOCK and "Minidump written to" are NOTEs; the kit FAILs a run only when a stall overlaps the measured
    window. Levels expected 40/0/0. "Reserving the guest memory arena" required (the log starts at boot).
W9 (reference off; all five arms bin devoff4b-bin, cvars framerate_limit=0):
  - q0, q125, q250, q500 (env LEGO_GPU_WAIT_BACKOFF_US=N, LEGO_GPU_WAIT_SPIN_US=30): exactly one
      GPU wait back-off: ON (quantum N us, spin 30 us); stats OFF; GetData hook built.
    with that arm's N, exactly one line containing "GPU wait back-off:" (so no warning), no "GPU wait stats".
    q0 is ON with quantum 0: ParseUs accepts "0" (gpu_wait_backoff.cpp L110-117, L124).
  - off (no LEGO_GPU_WAIT_* key): NO "GPU wait back-off" line. The source prints the init line only when back-off or
    stats is on (L141), so the brief's "each arm's init line once" holds for the q arms only. matrix-window9's
    notes say the same. A line in off would mean an env leak.
  - No arm sets LEGO_GPU_WAIT_STATS, so "GPU wait stats" is forbidden in all five. The stats-on form is in two
    gate-only arms (NOT W9 arms): p1 = s4b17 (stats only) and q250s = s4b18 (Q 250 + stats). They need the
    "stats ON" init line once and "GPU wait stats (5 s):", so the kit names those lines instead of calling them NEW.
    "sleep_fail N" must stay 0, but a substring rule can't say that (s4b18's gate checks it).
  - Source: build/agent2/snap1/DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp, SHA256 01D9F8F3464C8614...,
    which is the hash in devoff4b's MANIFEST (S4b A9). Its only log calls are L135, L138 (warnings), L142 (init)
    and L237 (STATS, every 5 s).
W5b (reference d11; all bin devoff4-bin; framerate_limit=0 + the 8 timer cvars; d11p adds
     timer_queue_precise_wait=true; d11t has env REX_TIMER_WAIT_BLOCKING=1):
  - every arm: exactly one "Host timer resolution set to 1 ms (background opt-out on)".
  - d11p: exactly one "TimerQueue: precise wait (timer_queue_precise_wait)". d11 and d11t: none.
  - d11t has no line of its own. Its proof is env_set, which the kit checks against matrix.json.
  - base and s0 rules are only for the test on the W5 folder.
W4c (reference d0; d0 = devoff2-bin, B = devoffB-bin; framerate_limit=0, env {}):
  - boot line required. No timer, precise-wait, C1, S4 hash, slow-frame or GPU wait line. B must log like d0.
  - d3 and d11t rules are only for the test on the W4b folder.

TESTS (23:06-23:07)
1. RUN-W5B-LOGDIFF.cmd build\agent8\matrix\20261122-1756 (W5) -> out-W5B-20261122-1756, test-w5b.out.txt.
   Exit 0. d11, d11t and d11p PASS. All 16 runs: status OK, exit 0 after one WM_CLOSE, 40/0/0, STUCK 0, dumps 0.
   1 ms line: 1 per d11/d11t/d11p run. Precise line: 1 per d11p run.
   Logdiff vs d11: d11t 0/0/0/0/0; d11p ONLY 1 = the precise line; base, s0 and cold-base NOTE only for the
   1 ms line GONE (expected: they aren't W5b arms). Slow state is the same as task #13 / timerq3.csv.
   Same result as task #13.
2. RUN-W4C-LOGDIFF.cmd build\agent8\matrix\20261122-1541 (W4b) -> out-W4C-20261122-1541, test-w4c.out.txt.
   Exit 1. The only FAIL is 1551-B-r2 "valid_timing false: build processes clang++", the known W4b flag.
   Every rule check passes in all 17 runs. Logdiff vs d0: B, d3 and cold-d0 0/0/0/0/0; d11t ONLY 1 = the
   1 ms line. Same result as task #5.
3. RUN-W9-LOGDIFF.cmd build\agent6\wnight\test-s4b17 -> out-W9-test-s4b17, test-w9.out.txt.
   make_test_s4b17.py copied Agent 3's s4b17 as p1, s4b18 as q250s and s4b-01-off as off (game*.log,
   run.json, sys.csv only).
   Every rule check passes:
   - p1 has one init line, "OFF (quantum 0 us, spin 30 us); stats ON", and 81 STATS lines.
   - q250s has one init line, "ON (quantum 250 us, spin 30 us); stats ON", and 41 STATS lines.
   - The STATS lines (sleep_fail 0 in both) are named by the rules, not NEW.
   - off has no GPU wait line, and no run has a warning.
   Expected FAILs: "status None" in all 3 runs (Agent 3's run.json has no status field).
   Expected NOTEs: levels 142-143/0/0 (functional routes); p1's "XNetLogonGetTitleID STUB" (attract-long route
   vs off's menus route).
   Not testable on this schema: env/cvars vs matrix (Agent 3 keeps env under "env", not "env_set"; the test
   matrix therefore has cvars [] and env {}), close/timing fields, slow state. No q0, q125 or q500 log exists yet.
4. Negative test: make_test_s4b17.py --neg -> test-s4b17-neg; RUN-W9-LOGDIFF.cmd on it -> out-W9-test-s4b17-neg,
   test-w9-neg.out.txt. s4b18 labelled q250 and s4b17 labelled q0 each FAIL all 3 rule checks: missing
   "ON ... stats OFF" line, forbidden "GPU wait stats" (x41 / x81), exact x0. Exit 1, as designed.
5. RUN-W9-LOGDIFF.cmd with no argument: usage, exit 2 (test-usage.out.txt). The HOLD branch (exit 3) is the same
   code as RUN-W6-LOGDIFF.cmd. I didn't exercise it, because I may not create the HOLD file.

FILES
- expect-w9.json, expect-w5b.json, expect-w4c.json: the rules, with notes.
- RUN-W9-LOGDIFF.cmd, RUN-W5B-LOGDIFF.cmd, RUN-W4C-LOGDIFF.cmd: the wrappers.
- cmp_arms.py: prints the three matrix files' arms and compares W5b/W4c with the W5/W4b folder arms.
- make_test_s4b17.py [--neg]: builds the W9 test folders test-s4b17\ and test-s4b17-neg\ (copies only).
- test-*.out.txt: test outputs. out-*\: kit outputs.
- scan_a3_runs.py: one line per Agent 3 run.json (used to pick the test runs).

2026-11-25 (task s3, E5.1 for M6): the kit changed (A race INFO, B WATCHDOG NOTE, per-arm levels, alnum arm ids,
harness mode --run); details and test results in build\agent6\w6\README.txt "2026-11-25 CHANGES".
- The wrappers here now set KITROOT before any shift; before, options after the folder broke the kit path (exit 2).
- Night re-run vs the stored outputs: build\agent6\wnight\s3-regress\DIFF.txt (only the A/B differences).
  RESULTS.md "The Execution complete race" says 6 runs but names 5; the re-run finds exactly those 5.
- New: build\agent6\s33-popin\RUN-S33-LOGDIFF.cmd (#33 pop-in, expect-s33.json, reference offsf).
    RUN-S33-LOGDIFF.cmd build\agent8\matrix\<folder> [options]   -> build\agent6\s33-popin\out-<folder>\
      (matrix fallback build\agent6\s33-popin\matrix-s33-draft.json)
    RUN-S33-LOGDIFF.cmd --run offsf=<dir> --run onsf=<dir> [--ref offsf] [--out <dir>]   (harness mode)
      (cvars from build\agent6\s33-popin\harness-s33.json; default out build\agent6\s33-popin\out-harness\)
  Exit 0/1/2/3 as above.
