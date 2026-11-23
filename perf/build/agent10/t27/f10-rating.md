# Finding-10 rows f10a, f10b, f10a2, f10b2: rating

Agent 10, 2026-11-23 06:55 (cross-checked against Agent 3's RESULTS.md at 07:05), task #27 (optional item). Read-only: I read the check files, Agent 3's table and write-up, and SESSION2. I ran nothing.

**Verdict: all 4 rows PASS.** None of them had a STUCK-LOCK, so the finding-10 rule (SESSION2 L3128-3132; HANDOFF §6) never had to decide between WARN and FAIL. The plan said "If both are clean, finding 10 stays a load-only WARN" (SESSION2 L3123). Both rows were clean twice, so **finding 10 stays a load-only WARN.** s4bLV has not run yet (§3).

## 1. Rows

The plan (SESSION2 L3120-3122) was two untimed vpad L-route rows on the quiet host. Both use slow_frame_log_ms=1 and place tags through the fixed sidecar. The second pair was approved at SESSION2 L3325.

| row | set | run dir (`build/agent3/runs/`) | check sha | exit / dumps / crash / WER | STUCK-LOCK | level | tags | K / F | max frame ms | quiet host | logdiff | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| f10a | s4b20's set (M1), C1 off | `20261123-055810-f10a-m1-sfl-level` | F3D93B66… | 0 / 0 / 0 / False (L2) | 0 (L43) | reached (L42) | 3/3 (L41) | 0 / 0 (L5) | 1790.8 | 0 of 11 (L44) | NEW 0, MORE 0, FLAG 0 (L24) | PASS |
| f10b | w6gB's set (p2fc), verify off (L52) | `20261123-060847-f10b-p2fc-level` | DFA1E420… | 0 / 0 / 0 / False (L2) | 0 (L62) | reached (L61) | 3/3 (L60) | 0 / 0 (L5) | 2886.5 | 0 of 13 (L63) | NEW 0, MORE 0, FLAG 0 (L32) | PASS |
| f10a2 | as f10a | `20261123-063244-f10a2-m1-sfl-level` | 07E05076… | 0 / 0 / 0 / False (L2) | 0 (L44) | reached (L43) | 3/3 (L42) | 0 / 0 (L5) | 1540.7 | 0 of 14 (L45) | NEW 0, MORE 0, FLAG 0 (L24) | PASS |
| f10b2 | as f10b, verify off (L51) | `20261123-064014-f10b2-p2fc-level` | BE1746F2… | 0 / 0 / 0 / False (L2) | 0 (L61) | reached (L60) | 3/3 (L59) | 0 / 0 (L5) | 1793.8 | 0 of 13 (L62) | NEW 0, MORE 0, FLAG 0 (L32) | PASS |

- **Sources.** Line numbers point into `build/agent3/s4b/logs/<row>.check.txt`. Max frame comes from `build/agent3/f10/f10-table.md` L3-6 (C7DB0B024BF03D78).
- **K / F.** K is the check's `k` and F is its `c1_verify_f`. Both are on the families line (L5).
- **Run completion.** All 4 runs did steps 119/119 and closed by WM_CLOSE (L2). holdwatch logged "exited by itself" for each.
- **logdiff.** GONE had 0 unexpected in every row.
- **P2.** `f10b.p2c.txt` and `f10b2.p2c.txt` both say RESULT PASS, full-buffer total 0.
- **Agent 3's write-up** (`build/agent3/f10/RESULTS.md` 7143C2E9AD2DD276…, 06:59) agrees on every row. It shows no hang, 0 dumps, 3/3 tags, last mark end, logdiff NEW 0 / MORE 0, P2c PASS and the same max frames (L5-10, L88-91). It differs in two small ways, and neither changes a verdict:
  - for f10a it counts 0 of 12 hostload rows with compilers (L88, L159), where the check file says 0 of 11 (L44). The counting windows differ by one row, and both counts are 0;
  - it adds f10b2's ~690-sync frame at 0.21 ms per wait (#33714, L107).

## 2. Margin: why finding 10 stays "load-only"

- **Worst frame.** The worst frame on the quiet host was 2886.5 ms (f10b #32528, f10-table L44). That is about 2.1 s under the 5 s detector. No row had a frame of 4 s or more (f10-table L3-6, column ">=4 s"). Under the build, w6s3 did not hang, and its worst frame was 3.99 s (RESULTS L51).
- **Wait cost.** I compared frames with about the same number of syncs:
  - about 670-700 waits: a wait cost 0.98 ms (f10b #32489, L42) and 0.21 ms (f10b2 #33714, RESULTS L107) on the quiet host. In gate B under -j8 it cost 6.05 ms (#33127, L64).
  - about 2700 waits: 0.29-0.37 ms (f10b, L43-44) and 0.18 ms (f10b2 #33718, L53) on the quiet host, against 1.79 ms in gate B (#33131, L65).
- **Strength.** Agent 3 gives a one-sided Fisher p = 0.07: 0 of 4 quiet runs hung, against 4 of 6 loaded runs in the same hour (RESULTS L14-16). That fits load as the trigger, but it isn't proof. Agent 3's GPU-or-host analysis points to the host (L21-40). Its limit is that GPU clocks weren't logged (L35).
- **Fit with the mechanism.** This matches Agent 6's mechanism (SESSION2 L3114-3118). The CP blocks in the memexport full-path sync, and the 5 s detector fires only when the CP is slow. Host starvation as the trigger fits the data, but it isn't proven (SESSION2 L3119).
- **Not a fix.** Not reproducing the hang doesn't fix it, because the mechanism is still there. The full-path sync is a perf candidate after S4 (SESSION2 L3124).

## 3. Still open

- **s4bLV** (p2fc + verify, cap 1800 s, fixed sidecar; SESSION2 L3110) hasn't run yet. It's a precondition for C1 default-ON (HANDOFF §4 item 8). Rate it with the same rule on a quiet host. The rule also needs 3/3 LOADs and K 0 / F 0 over the whole run (SESSION2 L3131).
- **A hang on a busy host** (during a build, for example) still counts as "WARN, finding 10" if it meets all three conditions of the rule. Otherwise it's FAIL.
- **Agent 3's possible next steps** are in RESULTS L184-189. None has run, and each needs Agent 1's OK:
  - a third quiet pair, which gives p = 0.03 if it's clean;
  - a controlled-load repeat with about 8 busy threads and no build;
  - an s4b20-style row under load with slow_frame_log_ms=1;
  - -GpuLog on any of these.

**Read.** The four check files (hashes above); `build/agent3/f10/f10-table.md` C7DB0B024BF03D78 L3-8, L40-65; `build/agent3/f10/RESULTS.md` 7143C2E9AD2DD276 in full; `f10b.p2c.txt` and `f10b2.p2c.txt`; the four holdwatch and attach out files; `perf-notes/SESSION2.md` 6CAAE865D51DC936 L3106-3132 and L3295-3328.

**Sent.** Nothing separately. Agent 3's 07:02 summary needed no reply. HANDOFF §4 item 7 points here, and the task #27 done line mentions this file.
