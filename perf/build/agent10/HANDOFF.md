# Agent 10: handoff

Written 2026-11-23 for the project pause (task #27). All paths are relative to the workspace root. My role was read-only: I reviewed and rated. I never edited other agents' files, built anything or ran timed rows, and I used git only read-only (`diff --no-index`, `log`, `rev-parse`, `hash-object`, `ls-files`, `apply --check`).

## 1. What I own

Role: batch-2 safety reviewer. Code changes are rated at their defaults as **SAFE**, **SAFE-IF** (the conditions are listed) or **UNSAFE** (it must go behind an OFF toggle). Runs and gates are rated **PASS**, **WARN** or **FAIL**. Findings are BLOCKER, SHOULD or NIT.

| file | sha256 (first 16) | lines | content |
|---|---|---|---|
| `perf-notes/agent10-batch2-review.md` ("b2r") | 3F413E55D5EA5AED | 2544 | rolling batch-2 safety review, task #25: status rows 1-43, §1-§42 |
| `perf-notes/agent10-helpers.md` | CE89661337CB2BF8 | 541 | session 2, task #9: SDK hot helpers |
| `perf-notes/agent10-codegen-review.md` | FE37DBA03F95A57E | 769 | task #15: J4 codegen cross-review |
| `perf-notes/agent10-native-review.md` | 67F75E8461C76C38 | 115 | native-only always-on review. It uses older task numbers: its "#21" is not today's #21. |
| `build/agent10/**` | | | working material (§5) |
| `build/agent10/t27/` | | | task #27 outputs (§3) |

## 2. b2r: layout and conventions

- **Status table (L9-55):** `# | Item | Owner | Live files:lines | Default | Verdict | Sent`, one row per rated item. Then the file hashes (L57), the S2 include list (L77) and the S3 include list (L91).
- **Sections:** rows 1-12 are §1-§12 (row 13 is inside §12). From row 14 on, the section is the row number minus 1 (row 14 = §13, row 43 = §42).
- Each section ends with **Read.** (what was read, with hashes) and **Sent.** (who was told what, and when).
- **Line numbers shift** whenever a status row is added (Addendum 2 to §25, L1361). Cite b2r by § and condition, not by line.
- **How I edited it:** check the file's sha first, splice the new text in at a unique anchor, hash it again, and quote the new sha in the message.
- **Latest rows:**
  - 40/§39, S4b apply: PASS on gates 1, 2, 3 and 5. **Gate 4 (the native re-pin) is open.**
  - 41/§40: the night launcher is SAFE.
  - 42/§41, G5 (W6 gate A): PASS, with partial coverage.
  - 43/§42, W6 gate B: PASS as "level load without tags".

## 3. Task #27 outputs (`build/agent10/t27/`)

Hashes are in §8.

| file | content |
|---|---|
| `day-draft-rating.md` | the day-session draft (RUN-DAY): **SAFE-IF**, 3 conditions, NITs N1-N6 |
| `scrnsave-delta.md` | the SCRNSAVE fix and its install tooling: **SAFE**; N-1 to N-4, I-1 to I-3; the post-install check (§5, 07:56): everything matches, and day-draft condition 1 is closed |
| `r21-s4t1.md` | #21: (a) **SAFE**, (b) **SAFE-IF** with 5 conditions, (c) **ACCEPTED** |
| `sub-r21-coderead.md` | my helper's #21 code read (F-CA is its §6) |
| `resume-review.md` | my review of `perf-notes/RESUME.md`, newest first: the 08:39 update (F1 fixed; no open findings), the final version (R33-R38 resolved; NITs F1 and F2), the draft 2 delta (R33-R38) and draft 1 (R1-R32, with my helper's fact-check as R20-R32) |
| `sub-resume-facts.md` | my helper's claim-by-claim fact-check of RESUME draft 1 |
| `f10-rating.md` | finding-10 rows f10a, f10b, f10a2, f10b2: all **PASS**; finding 10 stays a load-only WARN |
| `r33-popin.md` | #33 (no-wait pop-in, `d3d12_pipeline_creation_no_wait`): OFF **SAFE**; ON as an opt-in test **SAFE-IF** with 4 conditions; S1 (first test bin without hunk #5), S2 (diagnostic (d) before any recommendation), N1-N4 |

## 4. Open items after the break

1. **b2r row 40, gate 4.** native4b-bin has to be re-pinned before gate 4 can close (§39, L2210 and L2220). Re-pin step 4 started on Nov 23: rpb0 (Agent 3 reported the boot check PASS, fingerprint 9b40acbbef4c57b3) and rpm4 (`build/agent3/runs/rpm4-20261123-0620`). Agent 1 announces the pin (step 5). It had not been announced at 08:45 (SESSION2.md up to L3360; Agent 1's HANDOFF 8535FD76…), and RESUME §7 (L265, L275, L279) says it is left.
2. **Day-session draft** (`build/agent5/day-draft/`): **SAFE-IF** (`t27/day-draft-rating.md`). Agent 1 (06:05): there are no daytime runs before the break, and conditions 2 and 3 wait until after it.
   - **Condition 1: closed at 07:56** (`t27/scrnsave-delta.md` §5). Agent 5 installed the SCRNSAVE fix at 07:33:57 and then ran `build/agent5/scrnsave-fix/day-update.ps1`. `build/agent5/day-draft/` now holds run-day.ps1 B67EBD6C… (generated from run-night.ps1 565D30D4…, which make-run-day.ps1 4A96B0B9… pins), run-day.diff 3D0E8753…, README-DAY.md 9739BCF8…, RUN-DAY.cmd B08645E9… and test-day.ps1 410FB2EC…. launcher-ctl.ps1 (6DDE3150…) and STOP-LAUNCHER.cmd (CE27332F…) are unchanged. Tests: test-scrnsave 45/45, test-day 27/27, launch-test go 16/16.
   - **Condition 2:** install it as README-DAY's install section says (L138-141 in 9739BCF8…): after both ratings and while no night launcher runs, then compare the hashes. Not before the break.
   - **Condition 3:** Agent 11 rates it as well (README-DAY L57; L134 says Agent 11 has not rated it yet). Agent 11's HANDOFF (833CA243…, L37-38) lists it as their open item after the break, with me, once Agent 1 posts it as a board task. Agent 5's HANDOFF (488D14CA…) section 2 item 1 has the same three conditions, with condition 1 done.
   - NITs (none blocks):
     - N1, public safety: the old run-day.diff had absolute paths that included the Windows user name. **Closed:** the regenerated `build/agent5/day-draft/run-day.diff` (3D0E8753…) has repo-relative headers only, and day-update.ps1 L59-61 checks them.
     - N2: STOP-LAUNCHER.cmd run outside `bench\agent5\day` can't see a day launcher's state. It then reports "unknown" and asks, which is the safe direction. **Fixed:** README-DAY L57 (9739BCF8…) says to use the installed copy.
     - N3: RUN-DAY.cmd L25 said "Nothing was changed" even when it had already stopped a night launcher. **Fixed** in RUN-DAY.cmd B08645E9….
     - N4: launcher-ctl L79-81 uses naive local time, so on a DST-change day the 90 min / 14 h bounds can be an hour off. Harmless.
     - N5, known open items (README-DAY L134): (a) a night launcher closed with the X leaves its screensaver-saved.txt where the day launcher doesn't look; (b) `\d` at run-day.ps1 L68 can give exit 3 instead of 2 for odd hand-typed input.
     - N6: Agent 12's readout has to look in `bench\agent5\day\status\` for day windows (README-DAY L87).
3. **#21** (S4-T1, `LEGO_NATIVE_CHAIN_PRIORITY`, `build/agent7/s4-t1/`), rated in `t27/r21-s4t1.md`:
   - (a) the default-off test bed: **SAFE**;
   - (b) value 3 in F1, F3, W1 and W8b: **SAFE-IF** 5 conditions;
   - (c) the MP4 restatement: **ACCEPTED**, with one wording fix (§9.2) and one addition (F-CA under MP4 gap 2).
   - Condition 5 is F-CA: a th2 hang in any #21 row is checked against F-CA first. F-CA is a deadlock path in the color-alias retire handoff, in threaded mode th2 only. It predates #21 and was not seen at runtime (`t27/sub-r21-coderead.md` §6).
   - SHOULD for Agent 7: record F-CA under MP4 gap 2, and say whether any earlier th2 run hung. **Done in rev 2a** (checked 07:49; `t27/r21-s4t1.md`, last section): RATE-REQUEST.md 164790BB… §9.2 and §15, and MP4-STATIC.md FEB0FF3E… L151-194. No earlier th2 run hung: 4 runs, about 8.4 min on one route, so weak evidence.
   - N-d: W1 has no matrix file, so give it native_settings_frontend=false, native_fps_limit=0 and framerate_limit=0.
4. **#26** (the CG26 codegen option `db16cyc_pause`, b2r row 37/§36). It was not staged at the break: `build/agent2/devoff4b-cg26-bin` did not exist at 08:44.
   - When Agent 2 has staged it, run Agent 9's checker. Use the BelowNormal one-liner in `build/agent9/cg26-check/README.md` L12 (checker sha DDBA731CC22D74BD, `--out build\agent10\cg26-check`).
   - Exit codes: 0 PASS, 1 FAIL, 2 INCOMPLETE, 3 HELD.
   - Don't use the `cmd /c start` variant. It always reports exit 0.
5. **#19** (Agent 7's R1 stage 2, `d3d12_async_submit`, `build/agent7/s4-r1s2/`): **not rated before the break.** That follows its RATE-REQUEST ("For Agent 10, after the break. No rating is requested now.") and RESUME §7 step 3 (L282-283). b2r §17 cond 6 calls stage 2 the risky part.
   - `RATE-REQUEST.md` was at rev 1 (08:40; 54789A6B…, 498 lines, last written 08:43:50). Re-hash it first and cite it by §, because its lines move. For the RESUME check I read the 08:12 copy (5824C87C…).
   - §16 asks for verdicts (a)-(c) on `s4-r1s2.diff` (06B0D371…, +320/−1 over 5 files), staged on the snap1 SDK (`build/agent2/snap1/PATCHES-S4b.tsv` order).
   - Order (RESUME L282-283): the clang `-fsyntax-only` check (§10), then my rating, then Agent 2's build at ≤ 2 threads.
   - `<N>` waits for Agent 3's ready-N gate (§10). `build/agent3/s4b/ready-N` was absent at 08:44.
   - Apply (Agent 2, after my rating and the user's OK): the primary way copies `new/sdk/*` (5 files) over the SDK root; the alternative is the repo-relative `--directory` form, run from the workspace root (5 "Checking patch" lines at 07:58-07:59). `git -C <sdk root>`, and `git -C <DimensionsRecomp>` with `--directory=rexglue-sdk`, print "Skipped patch" for all 5 files, exit 0 and apply nothing (rev 1 L68-71). So first confirm 5 "Checking patch" lines and no "Skipped patch".
6. **#33** (no-wait pop-in, `d3d12_pipeline_creation_no_wait`, Agent 6, `build/agent6/s33-popin/`): the user approved it as an opt-in that is off by default. Rated in `t27/r33-popin.md` on SDK base 5350b1d (the 4 target files match HEAD; `git apply --check` exit 0 at 07:24):
   - OFF: **SAFE**. The control flow is unchanged. It only appends 3 slow-frame fields (printed only when `slow_frame_log_ms` > 0), adds 1 counter per dropped draw and resets 2 more counter slots per swap. No log parser anchors the slow-frame line at its end.
   - ON, as an opt-in test: **SAFE-IF** with 4 conditions: the default stays false with `kRequiresRestart`; row 1 shows identity first; the user's row-3 review gates any recommendation; and S1.
   - S1 (SHOULD): build the first test bin without hunk #5 (delete patch L82-93, the whole hunk; DESIGN.md §10 says how). With it, OnPrimaryBufferEnd (on by default) ends submissions during bursts, and with them any guest query that spans a primary-buffer end. That is a second variable.
   - S2 (SHOULD): add diagnostic (d) (a resolve after a dropped draw) as a 5th precondition in DESIGN §9 before #33 is suggested to anyone. The first test bin doesn't need it.
   - NITs: N1, the AwaitPipelineCreation() header comment should state the threading rule; N2, the forced-wait count counts calls, so read-outs should use the ms; N3, Agent 3's s4b kit needs `--allow-new d3d12_pipeline_creation_no_wait` for ON and gate arms; N4, for Agent 2: `build/agent2/PENDING-DIFFS.md` is stale on #33/#34 (L39-40, L65, L130).
   - Agent 6 recorded the rating, docs only, in DESIGN.md §10 (B2E33FE8…, 07:40) and CHECK.txt (5101A7B1…). §8 now builds without #5, and §9 item 5 is S2. The rated patch is unchanged (0D230244…). A copy without #5 passed `git apply --check` at 07:37 and was withdrawn at 07:40, so nothing is staged for a bin.
7. **Finding-10 rows: all 4 PASS** (`t27/f10-rating.md`). f10a, f10b, f10a2 and f10b2 each had 0 STUCK-LOCK events and reached the level with 3/3 tags. Each also showed exit 0, no dumps, no WER and K 0 / F 0 on a quiet host (`build/agent3/s4b/logs/<row>.check.txt`, `build/agent3/f10/f10-table.md` L3-6). As planned (SESSION2 L3123), finding 10 stays a load-only WARN. The worst quiet frame was 2.89 s against the 5 s detector. Not reproducing it doesn't fix it: the memexport full-path sync is still there. Still open: s4bLV (item 8), to be rated with the rule in §6. Agent 3's write-up `build/agent3/f10/RESULTS.md` (7143C2E9AD2DD276…) agrees on all 4 rows. It puts the evidence at a one-sided Fisher p = 0.07 (L16). Its next steps (L184-189) each need Agent 1's OK.
8. **C1 default-ON** still needs all of these:
   - s4bLV with the fixed sidecar: 3/3 LOADs, and the level reached with verify on;
   - a quiet host;
   - p2fc only.
   - C1 without P2 needs s4bV0 or the verify-only fix first (§41, L2473-2476).
9. **Agent 12's NOTE** (`build/agent12/s4-c1v3/NOTE.md` L39-42) should gain the runtime-flip false-F line (§41, L2483) when source edits are allowed again.
10. **b2r §15.4 (MP4).** Restate MP4 in the wording of `build/agent7/s4-t1/check/MP4-STATIC.md` L21-24, with the §9.2 wording fix and F-CA under MP4 gap 2 (`t27/r21-s4t1.md` (c)). It isn't done because b2r was frozen for #27. Agent 7's rev 2a has both in its own files (MP4-STATIC.md FEB0FF3E… L151-194, RATE-REQUEST.md 164790BB… §15), so §15.4 can cite them.
11. **SCRNSAVE fix: SAFE** (`t27/scrnsave-delta.md`; the install tooling is its §6). **Installed at 07:33:57 and checked at 07:56** (§5 there): `bench/agent8/run/run-matrix.ps1` 1A522CDF…, `bench/agent5/launch/run-night.ps1` 565D30D4… and the launch README B7CEBD63…; RUN-NIGHT.cmd is unchanged (D7A0362B…). N-1 to N-3 are closed. N-4 happened once: at 07:33:42 the installer refused on pid 33304 and copied nothing, and the re-run at 07:33:56 installed. I-3 still applies: `build/agent5/scrnsave-fix/install-log.txt` records the live SCRNSAVE.EXE value, so check it for a user path before any export (today the value is '').
12. **perf-notes/RESUME.md** (Agent 11) is **final: 7616A164A8EF7B6F… (51662 B, 381 lines, 08:39:07). Reviewed, no open findings.** Details in `t27/resume-review.md`, newest section first.
    - Draft 1 (8BE0AB49EBF1AB52…): R1-R32. My helper's claim-by-claim check (`t27/sub-resume-facts.md`) gave R20-R32, including 3 wrong facts: COMMIT-CHECK is a clean PASS; in W6, p2fc beat s0 in 9 of 10 rounds (the 10 of 10 belongs to C1); the staged W8a is n0 against mc on native4b.
    - Draft 2 (B12032E61CF0D1E1…, 07:10): R1-R24 and R27-R32 resolved, including all 3 wrong facts. Open were R33-R35 (SHOULD: the re-pin order, finding 10 predating the sprint, the pack state) and R36-R38 (NITs).
    - Final (9DA0A4C3…, 08:18; checked 08:22-08:36): accurate on everything I checked. My diff from draft 2 equals Agent 11's `build/agent11/resume/rfinal-total-diff.txt` (41 hunks, +72/−51). R33-R38 are resolved. The day-launcher item (§6 item 6) has the three conditions, with condition 1 closed, and N1-N6. Public safety: PASS. NITs: F1 (L325: the 07:33 refusal was N-4's false alarm, not a running launcher) and F2 (L266: Agent 11's HANDOFF didn't exist yet; it was written at 08:28:57).
    - The 08:39 update (Agent 11's rfinal3; checked 08:41): F1 is fixed at L325 and in `build/agent11/resume/facts-perfopt.md` L112. Nothing else changed, and it is still 381 lines, so my line cites hold.
    - If it changes after the break: diff it against Agent 11's backup of 7616A164… (their scripts write `build/agent11/resume/RESUME.<HHMM>-<old sha8>.md`) and repeat the public-safety grep.

## 5. `build/agent10` contents

| dir | contents |
|---|---|
| `review/` | about 1000 files: Agent 9's patches (`agent9-*.patch`), `delta-*` diffs, review rounds r4-r6 |
| `fe/` | `fediff.py` with its self-tests and outputs |
| `nb/` | native-build tools (`nativelines.py`, `lrsites.py`, `hookset.py`) and their logs |
| `b1/`, `b2/`, `b3/` | per-file diffs used by the reviews. `b3/` holds b2r's live-vs-snap1 diffs (b2r L5). |
| `bgate/` | `logdiff.py`, `framecmp.py`, `hookcheck.py`, `idlecount.py` and their outputs |
| `s3/`, `s4/`, `s32/` | S3 include-list tools; C1 diffs and checks; a CMake nesting check |
| `logsz/`, `obj/`, `overlay/` | object-size and include-overlay checks |
| `portable/`, `v2/`, `v3/`, `v3noavx2/` | test and bench exes for the SDK helper headers (`perf-notes/agent10-helpers.md`) |
| `t27/` | task #27 outputs (§3) |
| top level | bench and test logs, `pin-intrinsics.h`, `pin-math.h`, `recomp61-*` |

- **Keep these paths.** Other agents' notes cite them:
  - `bgate/logdiff.py`, used in `build/agent7/s4-t1/FUNCTIONAL-ROWS.md` L83-88;
  - `fe/livein`, `nb/`, `s4/c1-checks.txt`, `b3/S2-include.tsv`, `s3/S3-include.tsv`, `review/r5/lrdiff-report.txt`.
- **Public safety:** about 30 working files here (in b2, b3, nb, review, s3 and the top level) contain absolute paths with the Windows user name. They come from tool command lines and logs. Don't publish `build/agent10` as it is. `t27/` and this file were checked clean (§8).

## 6. Rules I applied

- **Finding-10 rule** (Agent 1, SESSION2 L3128-3132). A STUCK-LOCK is "WARN, finding 10" only if all three hold:
  1. Critical section 0x84959EDC, with owner tid 0x17 parked in sub_83FAF180 at lr 83FAF188 or 83FAF200 and a waiter at lr 82A2A270.
  2. It recovers by itself, with no crash or WER.
  3. The run still reaches the level. For s4bLV that also means 3/3 LOADs and K 0 / F 0 over the whole run.
  - Anything else is FAIL.
- **Timing** counts only on the user's own desktop (WinSta0\Default), not locked, on AC power (`bench/agent5/launch/README.md` L7, L16, L157). The hidden desktop is for agents' tests only.
- **PSO cache:** never copy `cache/` or a seed between bin dirs; a seed must match its bin. Cold runs: `bench/agent8/run/run-matrix.ps1` L14-19, L39 and L332-334 (one cold run per bin; with -ColdShared one shared cold run, and the other bins' first launch is a scored round-1 run; with -NoCold none). Under -NoCold a round-1 run can start cold or warm depending on the arm (Agent 9's #21 pre-read, P2).
- **HOLD:** check `perf-notes/WINDOW-HOLD.txt` before every command. If it exists, stop and wait for Agent 1.
- **New PC:** take new baselines and re-pin every bin before any timing comparison. Old numbers don't carry over.

## 7. Key files

- `perf-notes/SESSION2.md` (session log and rulings), `perf-notes/FINDINGS-AND-CHANGES.md`, `perf-notes/S4-DRAFT.md`, `perf-notes/RESUME.md` (Agent 11).
- `build/agent12/w6-gates/W6-GATES.md`: the W6 gate definitions.
- `bench/agent5/launch/`: the night launcher. `build/agent5/day-draft/`: the day-session draft. `build/agent5/scrnsave-fix/`: the SCRNSAVE fix and its installer. `bench/agent8/run/`: the runner (`run-matrix.ps1`, `common.ps1`).
- `build/agent7/s4-t1/` (#21), `build/agent7/s4-r1s2/` (#19), `build/agent9/cg26-check/` (#26 kit), `build/agent9/s4-t1-preread.md`.
- `build/agent6/hang/cp-state-s4b24-s4b20.md`: finding 10's CP state.
- Third-party prep: `DimensionsRecomp/tools/gpu-aot/prepare_plume.py` (Plume) and `DimensionsRecomp/rexglue-sdk/scripts/prepare_simde.py` (SIMDe).

## 8. Checks on this handoff

Final version, Nov 23, about 08:50. The `t27/` files (sha256 first 16 hex, LF lines):

| file | sha256 | lines |
|---|---|---|
| `day-draft-rating.md` | 0FD65482DE70468B | 48 |
| `f10-rating.md` | F62BDDCDBC989F2F | 49 |
| `r21-s4t1.md` | 7736004D2DFC1B46 | 125 |
| `r33-popin.md` | ACF0BDB5A5262362 | 162 |
| `resume-review.md` | A9049772A4B9B466 | 419 |
| `scrnsave-delta.md` | 16C84D9325EABDC2 | 150 |
| `sub-r21-coderead.md` | B80776922AC6D093 | 235 |
| `sub-resume-facts.md` | 43F660F9A854F3F5 | 285 |

- These 8 files and this one use LF only, with no CR and no BOM.
- A grep of them for the Windows user name, absolute user-profile paths, the grid's message marker and the GitHub host name found 0 hits.
- `r33-popin.md` L162 quotes "L82-91" on purpose: it records that S1 gave that range until 07:44. The right range for hunk #5 is L82-93.
- The §1 files were unchanged at 08:44: b2r 3F413E55…, the helpers review CE896613…, the codegen review FE37DBA0… and the native review 67F75E84….
- This file's own sha256 is in my done line to Agent 1.
