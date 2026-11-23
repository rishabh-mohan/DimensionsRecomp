# rfinal.py - perf-notes/RESUME.md final pass (Agent 11, task #25).
# Dry run by default (writes rfinal-diff.txt only); --apply --t=HH:MM writes the doc after a hashed backup.
# Gate: draft 2 sha B12032E6..., 360 LF, no CR, no BOM. Every edit is keyed to a draft-2 line number and
# checks that line's prefix (set/del/after) or that its old text occurs exactly once in the line (sub).
import datetime
import difflib
import hashlib
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
P = 'perf-notes/RESUME.md'
EXP = 'B12032E61CF0D1E1C14AA13FE9DE40D08452768699AFC33AEB1D5A61128729F8'
OUTDIR = 'build/agent11/resume'
APPLY = '--apply' in sys.argv
T = None
for a in sys.argv[1:]:
    if a.startswith('--t='):
        T = a[4:]
if APPLY and not T:
    print('ABORT: --apply needs --t=HH:MM')
    sys.exit(1)
if not T:
    T = datetime.datetime.now().strftime('%H:%M')

raw = open(P, 'rb').read()
sha = hashlib.sha256(raw).hexdigest().upper()
fails = []
if sha != EXP:
    fails.append('GATE sha ' + sha)
if raw.count(b'\r'):
    fails.append('GATE CR')
if raw.startswith(b'\xef\xbb\xbf'):
    fails.append('GATE BOM')
if raw.count(b'\n') != 360:
    fails.append('GATE LF %d' % raw.count(b'\n'))
if fails:
    print('ABORT', fails)
    sys.exit(1)
print('GATE OK', sha[:8], len(raw), 'B, 360 LF')
lines = raw.decode('utf-8').split('\n')
assert lines[-1] == '' and len(lines) == 361

E = {}


def op(n, kind, a, b=None):
    E.setdefault(n, []).append((kind, a, b))


op(5, 'set', "This is draft 2 (Nov 23, 07:10).",
   """This is the final version (Nov 23, {T}). It has all four formal read-outs of the night, each final and cross-checked: W6 and W4c by Agent 8, W9 and W5b by Agent 7. It also has Agent 12's gates, Agent 6's logdiffs, Agent 3's four finding-10 rows, Agent 10's ratings of #21 and #33, and the SCRNSAVE install of 07:33 with its post-install tests, which Agent 10 checked at 07:56.""")

op(7, 'after', "**Numbering:**", """
**Findings:** FINDINGS-AND-CHANGES.md numbers the problems found on the way. Finding 9 is the missing native shaders (item #1, with #2 as the stopgap). Finding 10 is the stuck game lock (§6, item 3). Finding 11 is a gap in the emulator's write tracking: after the game changes a page's protection, the GPU can draw from stale data. It predates the sprint (it is upstream and in v0.2.0), and its first fix is #5 fix (i), which C1 needs (FINDINGS L141; §2, switches).""")

op(14, 'sub', "(git, switches, bins, launcher, host values, each with file:line).",
   "(git, switches, bins, launcher, host values, each with file:line), compiled on Nov 23 at 05:45-06:20; its launcher section was updated after the SCRNSAVE install. Where it differs from this doc, this doc is newer.")

op(108, 'sub', "its proofs P1-P10 pass; not rated yet, and no rate request is written;",
   "its proofs P1-P10 pass; not rated yet. Its rate request is task #32 for Agent 7 (docs only, due 11:30 on Nov 23), and Agent 10 rates it after the break;")

op(23, 'set', "    - the precise timer wait (d11p):",
   """    - the precise timer wait (d11p): −0.20 core [−0.23, −0.17] (−8%), with fps −0.7% [−1.8, +0.3] and no p99 or 1% low change. Agent 7's formal read-out of W5b picks it narrowly over the blocking wait (d11t), which saves about the same (−0.22 core) but costs about 1% fps (−1.1% [−2.1, −0.0]) and had the window's only stutter cluster.""")

op(24, 'after', "  - **Codegen B:**",
   """  - **Cross-checks:** Agent 7 recomputed Agent 8's W6 and W4c headlines (114 of 116 agree; the other 2 differ by rounding), and Agent 8 recomputed Agent 7's W9 and W5b from results.csv (880 of 912 claims agree, 0 sign flips). None of the differences changes a verdict.""")

op(27, 'after', "  - whether C1 goes on by default",
   """  - what the night didn't test: a C1-only arm, p2fc with verification on, and the three winners timed together (§5, caveats);""")

op(28, 'set', "  - installing the SCRNSAVE fix",
   """  - the day launcher (the SCRNSAVE fix was installed at 07:33 on Nov 23);""")

op(110, 'sub', "with a dropped-draw counter on the slow-frame line (#34's idea); not built or applied.",
   "with a dropped-draw counter on the slow-frame line (#34's idea). Agent 10 rated it (§6, item 10); it isn't built or applied, and no bin is staged.")

op(111, 'sub', "Its status column dates from 06:30, so it predates #21's rating and the staged #33.",
   "Agent 2 refreshed it at 07:49 on Nov 23 (task #31, after N4 of Agent 10's #33 rating): #21's rating, #33 and #34 (staged together and rated) and codegen B's drop are in; #19 is still not rated.")

op(159, 'sub', "the rest are Agent 1's runner summaries, with second-pass figures in brackets.",
   "the W4b and W5 rows come from Agent 1's runner summaries and Agent 8's Nov 22 read-outs (`build/agent8/readout/w4b/` and `w5/`).")

op(167, 'set', "| W5b, Nov 23 01:55 and 04:51",
   """| W5b, Nov 23 01:55 and 04:51 (`20261123-0155`, `-0451`; 19 runs each) | timer wait: d11 (spin) / d11t (blocking) / d11p (precise) (devoff4) | **Formal (Agent 7, 36 kept runs, both passes): d11p, narrowly over d11t. d11p −0.20 core [−0.23, −0.17] (−8.0%); median frame time +0.5% [−0.9, +1.9], fps −0.7% [−1.8, +0.3]; no p99 or 1% low change.** d11t saves about the same (−0.22 core [−0.25, −0.19], −8.6%), but its fps is −1.1% [−2.1, −0.0], its raw median frame time was higher in 11 of 12 rounds, and it had the window's only stutter cluster (run 0221-d11t-r5: all 6 of its frames over 16.7 ms fall between T 30.8 and 33.3 s, while host CPU rose to 69%; cause unknown, 1 event in 36 runs). Both cut the TimerQueue thread's busy time from 23% to ~2%. Without the 7 flagged runs the frame times don't separate the arms; the pick then rests on the loaded runs (fps −3.0% for d11t against −1.1% for d11p, n = 4 each; post hoc, p = 0.083) and on 0221. W5's d11t tail lead didn't repeat (p99 +0.3% [−0.3, +1.0], against W5's +8.2%); its CPU saving did, smaller (−8.6% against d11; W5: −13.7% against its base) | **d11p** |""")

op(170, 'set', "**Read-outs:**",
   """**Read-outs, all final and cross-checked:** W6 and W4c by Agent 8 (`build/agent8/readout/w-followup/W6.md` and `W4c.md`, 06:39 and 06:40); W9 and W5b by Agent 7 (`build/agent7/readout/W9.md` 8C58CAD1… and `W5b.md` 6479A611…, both rev 1 of 07:45, which apply the checks' fixes; no verdict changed). Agent 7's supporting files are in the same folder: `pool-W9.md`, `pool-W5b.md`, `load-check.md`, `tail-check.md` and `cluster-0221.txt`. Cross-checks: Agent 7 recomputed Agent 8's W6 and W4c headlines (`build/agent7/readout/headlines-W6-W4c.md`: 114 of 116 agree, 2 differ by rounding), and Agent 8 recomputed W9 and W5b from results.csv with separate code (`build/agent8/readout/w-followup/a7check/W9-W5b-check.md`: 880 of 912 claims agree, 0 sign flips). The other 32 are 21 rounding ties, 9 light-share definition differences and 2 from one misread figure, fixed in rev 1: 0221-d11t-r5's non-game load is 2.56 cores, not 2.31, still below the 2.8 flag.""")

op(183, 'sub', "(W9's set has 7: Agent 9's low-clock runs plus Agent 8's audit flags, W9.md §1).",
   "(W9's set has 7: Agent 9's low-clock runs plus Agent 8's audit flags, W9.md §1; W5b's has 7 too: Agent 8's audit flags plus the runner's slow d11t r1-r2, W5b.md §1).")

op(192, 'sub', "and fps follows the GPU clock (Agent 8's audit, §5.5).",
   "and fps follows the GPU clock (W6.md L222-223, which cite Agent 8's audit, §5.5).")
op(192, 'sub', "is withdrawn.",
   "is withdrawn. In W5b, only pass 1's round 1 stood out (W5b.md §2).")

op(194, 'set', "- **What W6 didn't test.**",
   """- **What the night didn't test.** p2fc ran with verification off; no window had a C1-without-P2 arm (§6, item 2); and the three winners were never timed together: W5b ran on devoff4 (S4a), W6 and W9 on devoff4b (§7, step 9).""")

op(198, 'set', "1. **Keep or drop each lean**",
   """1. **Keep or drop each lean**, after a confirmation window (all four read-outs are in):""")

op(200, 'sub', "Agent 7's W9 read-out picks it; Agent 8's is pending.",
   "Agent 7's W9 read-out picks it, and Agent 8's recompute agrees.")
op(200, 'sub', "Agent 9's design for making it a default: `build/agent9/BACKOFF-DEFAULT-ON.md`.",
   "Agent 9's design for making it a default: `build/agent9/BACKOFF-DEFAULT-ON.md`. An optional follow-up window: off / q500 / q750 / q1000, with the round-1 order rotated (`build/agent7/HANDOFF.md`, open item 3).")

op(201, 'set', "   - **d11p:**",
   """   - **d11p:** Agent 7's W5b read-out picks it narrowly over d11t (§5), Agent 8's recompute agrees, and the gates and logdiffs are clean. Before its default flips, clear caveats (a)-(d) and (f) in S4-DRAFT row 38. If d11t is still a candidate, W5b.md §8 suggests an optional test of d11 / d11t / d11p under a controlled background load.""")

op(211, 'sub', "3. **Finding 10** (a load-only stuck-lock WARN, not C1's).",
   "3. **Finding 10, the stuck game lock** (a load-only stuck-lock WARN, not C1's). It predates the sprint: v0.2.0 hit the same stuck lock (the same lock, owner and waiting thread), then recovered and finished (FINDINGS L142, L146). In v0.2.0's run the lock's owner polled a GPU query result back to back; #24's query-poll hook is S4's answer to that loop (FINDINGS L146).")

op(220, 'set', "   1. **`run-day.ps1` regenerated",
   """   1. **`run-day.ps1` regenerated from the fixed `run-night.ps1`, `test-day.ps1` re-run, and Agent 10's delta read.** Closed at 07:56 on Nov 23. After the SCRNSAVE install, `day-update.ps1` (07:34) copied the fixed files into `build/agent5/day-draft/` and regenerated `run-day.ps1` there (B67EBD6C…, from run-night 565D30D4…). `test-day.ps1 -Name all` passed 27 of 27 at 07:47 (`build/agent5/day-draft/results/summary-all-074714.txt`). Its 07:35 run had one FAIL, d-real-4: the case still expected the night launcher's status folder not to exist, which stopped being true at the real start at 23:47; a test-only fix to `test-day.ps1` (now 410FB2EC…) compares that folder before and after the case. Agent 10 had rated the delta SAFE, and at 07:56 it checked the final hashes, the `run-day.diff` headers and the test results (`build/agent10/t27/scrnsave-delta.md` §4-§5).""")

op(221, 'set', "   2. **Installed into `bench/agent5/day/`",
   """   2. **Installed into `bench/agent5/day/` only after both ratings and while no night launcher runs, then the hashes compared** (README-DAY's install section, L138-141 in the current 9739BCF8…).""")

op(222, 'sub', "owed.", "owed (not done before the break; Agent 1 assigns it as a board task).")

op(225, 'set', "   - N1 is fixed in the generator:",
   """   - N1 is fixed: `day-update.ps1` regenerated `build/agent5/day-draft/run-day.diff` (3D0E8753…) with repo-relative headers, and its L59-61 refuse any header that isn't relative; Agent 10 checked the headers at 07:56.""")

op(226, 'set', "   - N2 and N3 are fixed in the staged README-DAY",
   """   - N2 and N3 are fixed in `build/agent5/day-draft/` (README-DAY 9739BCF8…, RUN-DAY.cmd B08645E9…). README-DAY's results line (L130) now quotes the 07:47 run; that closes N-2 of Agent 10's SCRNSAVE rating, a separate list (`build/agent10/t27/scrnsave-delta.md` §3).""")

op(229, 'set', "7. **The SCRNSAVE fix**",
   """7. **The SCRNSAVE fix** for both launchers: rated SAFE, installed at 07:33:57 on Nov 23, and all its post-install tests passed (§8).""")

op(232, 'set', "   - Agent 7 records it under MP4 gap 2",
   """   - Agent 7 recorded it under MP4 gap 2 (`build/agent7/s4-t1/check/MP4-STATIC.md`, FEB0FF3E…). None of the 4 earlier th2 runs hung: about 8.4 minutes on one route, weak evidence (`build/agent7/HANDOFF.md` §3).""")

op(242, 'set', "   - (c) the MP4 restatement:",
   """   - (c) the MP4 restatement: ACCEPTED, with one wording fix and one addition. Agent 7's rev 2a made both (docs only), and Agent 10 closed them at 07:49 (`r21-s4t1.md`, follow-up).""")

op(243, 'after', "   - native4b must be pinned before any timing comparison.",
   """10. **#33, the pop-in opt-in, rated** (Agent 10, `build/agent10/t27/r33-popin.md`, 07:36; no BLOCKER):
    - OFF, the default: SAFE.
    - ON, as an opt-in test: SAFE-IF all 4 conditions hold:
      1. the default stays false, with kRequiresRestart;
      2. row 1 (cvar off, the patched bin against the base bin) shows identity before anyone reads ON timings;
      3. the user's row-3 review at the visible desktop gates any recommendation;
      4. the first test bin leaves out hunk #5 (S1).
    - S1 (SHOULD): with hunk #5, ON also changes where submissions end during bursts, a second variable. S2 (SHOULD): run diagnostic (d), a resolve after a dropped draw, before #33 is suggested to anyone.
    - NITs N1-N4. N4 (PENDING-DIFFS was stale on #33 and #34) is done: Agent 2 refreshed it at 07:49 (task #31).
    - Agent 6 recorded the rating in `build/agent6/s33-popin/DESIGN.md` §10 (07:40): §8 now builds without hunk #5, and §9 item 5 is S2. The rated patch is unchanged (0D230244…), and nothing is staged for a bin.""")

op(250, 'set', "   - the SCRNSAVE fix installed",
   """   - the SCRNSAVE fix still installed (the hashes in §8);""")

op(252, 'set', "   - `build/agent1/HANDOFF.md` read, then every other agent's",
   """   - `build/agent1/HANDOFF.md` read, then every other agent's (`build/agent<N>/HANDOFF.md`, N = 1-12; Agent 11's is short and points here).""")

op(256, 'after', "   - **GPU warm-up for every window:**",
   """   - **Window hygiene** (`build/agent7/readout/W5b.md` §7): re-check the quiet gate's processes before each run, and wait or flag the run if one uses 0.1 core or more; log the top CPU processes once a second; flag or re-run any run with a non-game load (ng_t) of 2.8 cores or more; rotate the round-1 order or add unscored warm-up runs. The launcher's quiet gate checks only at the window start: in W5b's second pass, load rose again ~6 minutes after it passed and hit the first 4 scored runs. Agent 8's HANDOFF (open item 4) adds runner changes: per-process CPU and disk I/O, counts of frames over 8, 10 and 16.7 ms in results.csv, and `light_share` at full precision.""")

op(257, 'sub', "Finding 10's stall is host-side: 0 of 4 quiet runs hung, against 4 of 6 under a -j8 build (§6, item 3;",
   "Finding 10's stall is host-side, and load is the likely trigger: 0 of 4 quiet runs hung, against 4 of 6 under a -j8 build (p = 0.07; §6, item 3;")

op(259, 'del', "   - Agent 8's W9 read-out and the W5b read-outs;")

op(260, 'set', "   - the SCRNSAVE install after the night launcher exits",
   """   - #19's rate request: task #32 for Agent 7 (docs only, due 11:30 on Nov 23); Agent 10 rates it after the break (step 3);""")

op(261, 'sub', "(step 2).", "(step 2);")
op(261, 'after', "   - the native4b pin announcement (step 2).",
   """   - before any window on the day: re-run the plan-only staging (`build/agent8/w-followup/stage-window.ps1`), because the Nov 22 stage files predate the runner change (`build/agent8/HANDOFF.md`, open item 1). No manual re-pin: the launcher pins the current files at its next start (§8).""")

op(264, 'sub', "Then come the `$PINS` line and the pack-state keying (REPIN.md L53; Agent 4's HANDOFF, open item 3).",
   "Then fix `build/agent4/repin/repin_check.ps1` in Agent 4's order (`build/agent4/HANDOFF.md` L29-32): first key check [4]'s old-pin FAIL on the pack state (`$cacheState` 'pack', L291), then add `build/agent2/native4b-bin` to `$oldBins` (L390), and only then add native4b's fingerprint to `$PINS` (L130). Never add the `$PINS` line alone, as REPIN.md L53 suggests: every check of `snap1-on` and `native4b-bin` would then FAIL.")

op(267, 'sub', "Staged in `build/agent7/s4-r1s2/` with its proofs, functional rows, soak plan and a draft W7 matrix; not rated yet.",
   "Staged in `build/agent7/s4-r1s2/` with its proofs, functional rows, soak plan and a draft W7 matrix; not rated yet. Its rate request is task #32 for Agent 7 (docs only, due 11:30 on Nov 23), and Agent 10 rates it after the break. Its `<N>` (the #18 split size) waits for Agent 3's ready-N gate (`build/agent7/HANDOFF.md` §4).")

op(268, 'sub', "Steps: a rate request, Agent 10's rating,",
   "Steps: a rate request and a `clang -fsyntax-only` check, Agent 10's rating,")

op(272, 'sub', "then F1 → W1 → W8b.",
   "then F1 → W1 → W8b. W1 still needs a matrix file (`build/agent7/HANDOFF.md` §3).")

op(277, 'set', "   - Steps: Agent 10's rating, a build and the functional runs",
   """   - Agent 10 rated it (§6, item 10). Steps: stage the first test bin without hunk #5 (DESIGN.md §8), build it, and run DESIGN.md's test plan with row 1's identity check first; then the user judges the pop-in by eye at the visible desktop (row 3). Run diagnostic (d) before #33 is suggested as a setting (DESIGN.md §9, item 5).""")

op(280, 'after', "   - Agent 4's kit is ready:",
   """   - **The pack's state.** Agent 4's scratch pack of the 4 missing shaders passed (Nov 22, 07:16; `build/agent4/s35/`), but no pack bin is built (`build/agent4/HANDOFF.md` L16). First dump the attract's shaders: in the 3D attract, native drops draws that use 46 more vertex-shader and 3 pixel-shader objects, so the 4-shader pack may not cover them. Run once with `LEGO_DUMP_MISSING_SHADERS=1` on `harness/routes/attract-long.txt` (HANDOFF L24-26).
   - The pack bin, native4bp, needs the shader-preparation step re-run in its build (FINDINGS L147). The pack changes the native fingerprint again, so native4bp needs its own re-pin (REPIN.md §4.2, steps 3-4) and its own PSO and seed recording (HANDOFF L27, L31, L33).""")

op(281, 'sub', "A suggestion: the kept switches together against s0, two passes, with the GPU warm-up.",
   "A suggestion: the kept switches together (the three winners were never timed together) against s0, two passes, with the GPU warm-up and the window hygiene of step 0.")

op(293, 'set', "- **The night launcher**, `bench/agent5/launch/RUN-NIGHT.cmd`",
   """- **The night launcher**, `bench/agent5/launch/RUN-NIGHT.cmd` (D7A0362B…). It runs `run-night.ps1`, 565D30D4… since the SCRNSAVE install (16B90FA8… during the night); the README is B7CEBD63… (0058C8F6… during the night).""")

op(296, 'sub', "Any change to a pinned file refuses the next window.",
   "Any change to a pinned file refuses the next window of that launcher run. `pins.txt` is only a record: it still lists the 23:47 start's hashes (`run-matrix.ps1` FEDCEB13…, `run-night.ps1` 16B90FA8…), and nothing reads it back. Each start re-hashes the files (`bench/agent5/launch/run-night.ps1` L967) and rewrites `pins.txt` once its start checks pass (L973), so nobody re-pins by hand after the SCRNSAVE install (`build/agent5/HANDOFF.md` §1; `build/agent8/HANDOFF.md` L13; read from the code, not tested by a start).")

op(297, 'sub', "Window logs go to `bench/agent5/launch/status/`.",
   "Window logs go to `bench/agent5/launch/status/`. On Nov 23 it ended at 07:30:14 at its deadline (exit 0), restored the screensaver and released keep-awake; the hold manager's log is clean for all 7 windows (SESSION2 L3339).")

op(302, 'set', "- **The SCRNSAVE fix**, staged in",
   """- **The SCRNSAVE fix**, staged in `build/agent5/scrnsave-fix/` at 06:14 on Nov 23 and installed at 07:33:57:""")

op(305, 'set', "  - The day draft is regenerated",
   """  - The day draft is regenerated from the fixed night launcher; `day-update.ps1` copied it into `build/agent5/day-draft/` at 07:34 (§6, item 6).""")

op(306, 'set', "  - Tests: `test-scrnsave.ps1 -Set new -E2E`",
   """  - Tests before the install: `test-scrnsave.ps1 -Set new -E2E`, 45 of 45 PASS at 06:14:40 (`build/agent5/scrnsave-fix/results/summary-new-061440.txt`).""")

op(308, 'set', "  - `install-scrnsave.ps1 -Check` refused at 06:36",
   """  - The installer refused at 06:36 and at 07:33:41, while a launcher process was still running, as designed. At 07:33:57 it installed the three files, all at their "after" hashes (`build/agent5/scrnsave-fix/install-log.txt`).""")

op(309, 'set', "  - Pending: Agent 8's read of the delta;",
   """  - Agent 8 read the runner hunk first: OK (`build/agent8/HANDOFF.md` L12). After the install, all tests passed:
    - `test-scrnsave.ps1 -Set installed -E2E`: 45 of 45 at 07:34:45, on the script revision Agent 10 read (4D46A8E2…; `build/agent5/scrnsave-fix/results/summary-installed-073444.txt`);
    - `build/agent5/launch-test/run-tests.ps1 -Group go`: 16 of 16 at 07:52 on run-night 565D30D4… (`build/agent5/launch-test/results/summary-go.txt`). It ran with the new test-only `-StopAt '2026-11-23 11:00'`: after 07:30, a launcher start needs `-StopAt`, because its default end (the next 07:30) would be more than 14 h away (`build/agent5/HANDOFF.md` §1);
    - `test-day.ps1 -Name all`: 27 of 27 at 07:47 (§6, item 6).
  - Agent 10 checked the install, the hashes and the three test results at 07:56 (`build/agent10/t27/scrnsave-delta.md` §5).""")

op(310, 'set', "  - After the install, the hashes become:",
   """  - The installed hashes: `run-night.ps1` 565D30D4…, the README B7CEBD63…, `RUN-NIGHT.cmd` unchanged (D7A0362B…) and `bench/agent8/run/run-matrix.ps1` 1A522CDF… (was FEDCEB13…). Two pinned files changed, so the next launch pins new hashes.""")

op(347, 'set', "| read-outs, gates, logdiffs |",
   """| read-outs, cross-checks, gates, logdiffs | `build/agent8/readout/w-followup/` (W6.md, W4c.md, `a7check/W9-W5b-check.md`); `build/agent7/readout/` (W9.md, W5b.md, `headlines-W6-W4c.md`); `build/agent12/w6-gates/`; `build/agent6/wnight/RESULTS.md` |""")

op(354, 'set', "| #19 (R1 stage 2), #33 (the pop-in opt-in) |",
   """| #19 (R1 stage 2); #33 (the pop-in opt-in) and its rating | `build/agent7/s4-r1s2/`; `build/agent6/s33-popin/`, `build/agent10/t27/r33-popin.md` |""")

op(359, 'set', "| reviews (Agent 10) |",
   """| reviews and ratings (Agent 10) | `build/agent10/`; the Nov 23 ratings are in `build/agent10/t27/` |""")

# ---- apply to the draft-2 line array
out = []
nops = 0
for i, line in enumerate(lines[:-1], start=1):
    cur = line
    extra = []
    delete = False
    for kind, a, b in E.get(i, []):
        nops += 1
        if kind == 'sub':
            c = cur.count(a)
            if c != 1:
                fails.append('SUB L%d count %d: %s' % (i, c, a[:70]))
                continue
            cur = cur.replace(a, b)
        elif kind == 'set':
            if not line.startswith(a):
                fails.append('SET L%d prefix: %s | line: %s' % (i, a[:70], line[:70]))
                continue
            cur = b
        elif kind == 'del':
            if not line.startswith(a):
                fails.append('DEL L%d prefix: %s' % (i, a[:70]))
                continue
            delete = True
        elif kind == 'after':
            if not line.startswith(a):
                fails.append('AFTER L%d prefix: %s | line: %s' % (i, a[:70], line[:70]))
                continue
            extra.extend(b.split('\n'))
    if not delete:
        out.extend(cur.split('\n'))
    out.extend(extra)
for n in E:
    if not 1 <= n <= 360:
        fails.append('BAD LINE %d' % n)
new = '\n'.join(out) + '\n'
new = new.replace('{T}', T)
nb = new.encode('utf-8')

# ---- checks
if '{T}' in new:
    fails.append('PLACEHOLDER left')
if '\r' in new or new.startswith('\ufeff'):
    fails.append('CR/BOM in output')
pers = re.findall(r'<user>|rishabh', new, re.I)
pub = re.findall(r'github|https?://|file:///|[A-Za-z]:\\|\\Users\\|/Users/', new, re.I)
if pers:
    fails.append('PERSONAL %d' % len(pers))
if pub:
    fails.append('PUBLIC %r' % pub[:5])
stale = ['draft 2', 'are due', '~10:00', "Agent 8's is pending", 'the verdicts are pending', 'not installed yet',
         'Pending:', 'at 07:10', "Agent 8's W9 read-out", 'until day-update runs', 'W6 didn',
         'asks Agent 5 to confirm', 'A36574ED', '9D131EB1', '54E35C18', 'dates from 06:30',
         "rate request isn't written", 'no rate request is written', 'closes once', 'is stale on #33',
         'went to Agent 2', 'Met in staged form', 'in the staged README-DAY']
for s in stale:
    if s in new:
        fails.append('STALE %r' % s)
newlines = new.split('\n')[:-1]
print('OPS', nops, 'lines', len(lines) - 1, '->', len(newlines))
for k, l in enumerate(newlines, start=1):
    if re.search(r'pending|not yet|isn\'t written|owed', l, re.I):
        print('  REVIEW L%d: %s' % (k, l[:150]))

# backticked repo paths that should exist (report only)
miss = set()
for m in re.finditer(r'`((?:build|bench|perf-notes|harness)/[^`\s]*)`', new):
    pth = m.group(1)
    if '<' in pth:
        continue
    if not os.path.exists(pth):
        miss.add(pth)
for pth in sorted(miss):
    print('  PATH missing (check): ' + pth)

diff = difflib.unified_diff(lines[:-1], newlines, 'RESUME.md draft2', 'RESUME.md final', lineterm='', n=0)
with open(os.path.join(OUTDIR, 'rfinal-diff.txt'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(diff) + '\n')
nsha = hashlib.sha256(nb).hexdigest().upper()
print('NEW', nsha, len(nb), 'B', nb.count(b'\n'), 'LF')
if fails:
    for x in fails:
        print('FAIL', x)
    print('ABORT (nothing written)')
    sys.exit(2)
if not APPLY:
    print('DRY OK (diff in build/agent11/resume/rfinal-diff.txt)')
    sys.exit(0)
bk = os.path.join(OUTDIR, 'RESUME.%s-%s.md' % (datetime.datetime.now().strftime('%H%M'), EXP[:8]))
if os.path.exists(bk):
    print('ABORT backup exists', bk)
    sys.exit(3)
with open(bk, 'wb') as f:
    f.write(raw)
if hashlib.sha256(open(bk, 'rb').read()).hexdigest().upper() != EXP:
    print('ABORT backup mismatch')
    sys.exit(3)
with open(P, 'wb') as f:
    f.write(nb)
chk = open(P, 'rb').read()
if hashlib.sha256(chk).hexdigest().upper() != nsha:
    print('ABORT write mismatch')
    sys.exit(4)
print('WROTE', P, nsha, len(chk), 'B', chk.count(b'\n'), 'LF; backup', bk)
