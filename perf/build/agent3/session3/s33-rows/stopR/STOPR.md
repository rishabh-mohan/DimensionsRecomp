# STOPR: re-timed #33 row 4 (s33stop3..7), option (iii), rev 3

> rev 3 (M3, 10:42) is a doc-only edit made after M10's rating (build/agent10/session3/stopR-rating.md B67F3E2C, SAFE-IF R1-R5).
> - §6 now holds the R1 procedure as installed, and §7 holds the pinned hashes.
> - Nothing else changed. The rated rev 2 text is kept as STOPR.md.rev2 (583C40E2).

M3, 2026-11-25 10:30. For M10 to rate; the Overseer forwards it. Orders: Overseer 16:17Z, 16:20Z and 16:25Z.
- rev 2 corrects §2 (M12's finding) and replaces the S set using the 140-160 s scan (§3).
- Nothing is installed. Row 4 is held: go-s33stop3..7 are absent, and rows 5, 6 and (d) run meanwhile.

## 1. Why re-time
- s33stop1 (-Seconds 203) and s33stop2 (205) both returned s33_onstop **exit 3** (DOES NOT COUNT):
  - stop1: last_miss_gap_s 12.307;
  - stop2: last_miss_gap_s 4.124.
- M10 S1 tally: **2**. One more exit 3 under the old rule means stop and ask.
- The planned closes 207/209/211/206/210 sit in quiet gaps (§2).

## 2. Finding: the miss pattern is locked to the 67-miss burst (H0), not to wall time
Method: t = log timestamp minus run.json `started`; a miss = a slow-frame line with `new N` > 0. Scratch tools, all read-only:
- `stopr_timeline.py`
- `stopr_cover.py`
- `stopr_sim.py` (`STOPR_OFF` env var = shift of the close line)

They live in the M3 brain scratch dir. M12 confirms this independently in build\agent12\session3\s33\:
- s33-h0 B5DA7B49
- s33-ssim 18364E5D
- s33_h0.py BFF4FCA8
- s33_ssim.py 0DD586D6

The burst (`new 67`, the H0 / 12.4k-shot event) lands at a different time in each run:

| run | ON/OFF | H0 (s) |
|---|---|---|
| 20261125-095932-s33-onsf | ON | 132.67 |
| 20261125-100935-s33-stop1 | ON | 134.27 |
| 20261125-070859-s33-basesf | base | 134.93 |
| 20261125-101423-s33-stop2 | ON | 144.72 |
| 20261125-071741-s33-offsf | OFF | 148.94 |

The whole pattern moves with H0, before H0 as well as after. The offsets repeat within about ±0.3 s in all 5 runs:

| offset | misses |
|---|---|
| H0-23.4..-17.1 | n1, n1, n1, n1, n4 (at 109.6-115.8 s in onsf, 121.2-127.5 s in stop2) |
| H0-8.7 | n1 |
| H0+0 | n67, n8 |
| H0+2..+19 | dense burst: about 18 miss frames in onsf with gaps of up to ~4 s |
| H0+46.1 | n4 |
| H0+56.4 | n1 |
| H0+76.6 | n5, then n1 |
| H0+80.3 | n1 |
| H0+93.6..97.5 | n1, n2, (n1), n6 |

- **Correction to rev 1:** the ~121-131 s sequence is **not** a route variant. It is the H0-23..-17 s group, present in all 5 runs. In the early runs it simply falls at 109-118 s.
- The +15 s offsf shift is the H0 time itself moving between runs (132.7 to 148.9 s). It is not an ON/OFF effect (stop2 is ON and moved +12 s against onsf) and not a cold/warm effect (all five runs are cold, with no seed_xenos).
- So the ON runs do **not** reliably track onsf: a fixed -Seconds sees a random H0 within at least a 16 s range.

## 3. Choice of -Seconds
Constraints:
- harness\run-game.ps1:43 takes `[int]$Seconds`, so S must be a whole number.
- The close line comes at S+0.09..0.11 s (stop1 203.09, stop2 205.11), so the counting window is **[S-1.9, S+0.1]** s after start.

Scoring:
- Each run's H0-relative pattern was replayed at each of the 5 observed H0 times (25 pairs; short runs only up to their close).
- "share" = the fraction of pairs with a miss in the window.
- "±1 s" = the share with the close line moved -1.0/-0.5/0/+0.5/+1.0 s, a robustness check for H0 or close jitter.
- "observed" = the real runs (onsf, basesf, offsf, stop1, stop2) with a miss in the window (- = the run had ended).

Scan, integer S from 136 to 250 (excerpt; the full tables are reproducible with the tools):

| S | share | ±1 s shift (-1, -0.5, 0, +0.5, +1) | observed | note |
|---|---|---|---|---|
| 145 | 80% | 60 60 80 80 80 | 4/5 | dense burst |
| 146 | 80% | 80 80 80 80 68 | 4/5 | dense burst; the flattest |
| 149 | 84% | 60 60 84 72 52 | 4/5 | M12's #2 (149.2) |
| 152 | 76% | 68 64 76 100 100 | 4/5 | |
| **153** | **100%** | **76 100 100 92 68** | **5/5** | M12's best (152.7) |
| 154 | 68% | 100 92 68 64 60 | 4/5 | |
| 191 | 52% | 20 36 52 60 60 | 3/5 | rev 1 |
| 192 | 60% | 52 60 60 44 21 | 3/5 | H0+56.4 n1 (H0≈134) / H0+46.1 n4 (H0≈145) |
| 229 | 67% | 33 47 67 80 73 | 3/3 | rev 1 |
| 230 | 73% | 67 80 73 80 73 | 2/3 | H0+93.6..97.5 cluster (H0≈133-135) / H0+80.3 n1 (H0≈149) |
| 231 | 73% | 73 80 73 53 40 | 2/3 | same cluster |
| 181 / 212 / 215 | 32% / 35% / 31% | | | Overseer's first examples, for reference |

- **The dense burst scores clearly better than 230/231** (153: 100% vs 73%; mean over ±1 s, 87% vs 75%), so the set is revised.
- Margins at 153 are thin at both ends:
  - offsf hits only through one n1 at H0+2.25;
  - onsf hits through the last burst miss at H0+19.2;
  - an H0 earlier than ~132 s or later than ~150 s would miss.
- That is why the set keeps two late-cluster rows and 192. If the dense-burst model is wrong, it fails on 153/146 together, not on all five.

**rev 2 set** (run order = best first, to reach 3 counted runs early):

| row | was | **S** | window (s) | share | ±1 s mean | what it targets |
|---|---|---|---|---|---|---|
| s33stop3 | 207 | **153** | 151.1-153.1 | 100% | 87% | dense burst H0+2..19 (H0 133-149) |
| s33stop4 | 209 | **146** | 144.1-146.1 | 80% | 78% | dense burst; flat under shift |
| s33stop5 | 211 | **230** | 228.1-230.1 | 73% | 75% | H0+93.6..97.5 cluster / H0+80.3 n1 |
| s33stop6 | 206 | **231** | 229.1-231.1 | 73% | 64% | same cluster |
| s33stop7 | 210 | **192** | 190.1-192.1 | 60% | 47% | H0+56.4 n1 / H0+46.1 n4; this is the only S that hits a stop2-like H0 (≈145) outside the burst |

Odds, assuming independent runs (each run draws its own H0):

| set | p values | expected counted | P(≥3) | P(≥4) | P(5) |
|---|---|---|---|---|---|
| rev 2, central shares | 1.0/.80/.73/.73/.60 | 3.86 | **0.93** | 0.68 | 0.26 |
| rev 2, ±1 s means | .87/.78/.75/.64/.47 | 3.51 | 0.85 | 0.53 | 0.15 |
| rev 1 (230/192/231/229/191), central shares | | 3.25 | 0.77 | | |
| rev 1, ±1 s means | | 2.90 | 0.65 | | |

- Caveat: n = 5 source runs and 5 H0 values only.
- est = S + 30, as the old rows had.

## 4. Budget rule (for M10 to rate)
- Run s33stop3, 4, 5, 6, 7 in that order; I write each go-<id> by hand after reading the previous row.
- **Stop row 4 after 3 counted runs (exit 0) or after all 5 re-timed runs.**
- Exit 1 = FAIL: stop at once.
- stop1/2 stay on record as exit 3. They do not count and they do not use up the budget.
- **Conflicts to rate:**
  - (a) M10 S1 / READING-S33 line 46 says "more than 2 exit-3 runs → stop and ask; no new -Seconds". The tally is already 2. Under this proposal the budget replaces S1 for the re-timed runs. Otherwise the first re-timed exit 3 stops row 4.
  - (b) TESTPLAN row 4 says `onstop ×5`. The budget accepts 3 counted runs as the row reading, with 5 as the cap.
  - (c) Every run is read for a clean shutdown whether it counts or not. A clean shutdown is exit 0, wm_close, no dump, no WER, close_seconds < timeout, plus the W9 wedge NOTE.
  - (d) S 146/153 close the game during the dense H0 burst. That is a harsher shutdown point than the old 203-211, which is in the spirit of row 4 (misses right before the close). The short-row reading in s4b_check is unchanged: `short` is set, and GONE keys / steps are notes.

## 5. Change set: data only, no code changes
Option (iii): re-time the held lines in place and keep their ids.
- Places where the stop seconds are hard-coded, and what each needs:

| place | encodes stop seconds? | change |
|---|---|---|
| build\agent3\s4b\queue.jsonl lines 93-97 (s33stop3..7) | yes (-Seconds, est, note) | **re-time** (the only change) |
| build\agent6\s33-popin\harness-s33.json, onstop `seconds` [203..211] | yes | none. It is not M3's file and nothing reads it at runtime: w6_kit doesn't read seconds; only check_queue_s33 SPEC and make_test_s33 use it. |
| build\agent3\session3\s33-rows\check_queue_s33.py SPEC (line 23) | yes | none. It is the pre-install checker and is no longer run (it would now FAIL the re-timed lines). check_queue_stopR.py replaces it for this change. |
| build\agent3\s4b\s4b_check.py S33X / POSTWIN | no: only mode/cvars/short/seed and the bin (lines 452-455) | none. A comment at line 439 says "203-211 s" (comment only). `short` stays true (S < 540). |
| build\agent3\s4b\postcheck.ps1 | no: id routing only, `^s33stop\d$` (lines 272, 301) | none |
| build\agent3\session3\s33-rows\s33_onstop.py | no: it reads seconds_requested from run.json | none |
| S33-ROWS-PLAN.md row table, TESTPLAN row 4 | doc text 203/205/... | correct after the sprint |

- Live s4b_check.py 3DDF1A55 and postcheck.ps1 36DC0E05 stay as they are.
- Files (build\agent3\session3\s33-rows\stopR\):
  - `make_stopR.py`: builds the draft from the live queue; changes only -Seconds, est and note on the 5 lines.
  - `queue.jsonl.stopR`: the full replacement queue (sha in §7).
  - `check_queue_stopR.py`: checks the draft against the live queue (or, with --installed, against the .bak):
    - the old file is the #33-install queue 69C77DA7;
    - only lines 93-97 differ;
    - same line count and line endings;
    - needs and every other arg are unchanged;
    - -Seconds matches the table, and est = S+30;
    - the onstop arm values (bin, cvars, route, cold);
    - go-s33stop3..7 are absent;
    - no re-timed id is in queue-state, and stop1/2 are there;
    - the live postcheck routes `^s33stop\d$`;
    - the live s4b_check S33X/POSTWIN cover the ids;
    - the live tool pins;
    - `--dryrun`: run-game -DryRun per re-timed row, then checks run.json seconds_requested, bin_dir, cvars, cold start, and the input script sha.
  - `check-queue-stopR.out.txt`: the result of the plain run on rev 2: **ALL CHECKS PASS (60 ok)**.
  - Negative test (on rev 1): a draft with one unrelated row's -Seconds changed gave `CHECKS FAILED: 1`; the draft was then restored.
  - The `--dryrun` result is pending. It runs in the gap after s33offw, so it can't disturb a measured run.

## 6. Install (M10 R1; done 10:39-10:40 at the s33onw boundary)
This procedure replaces the rev 2 Move-Item step. Under PS 5.1, Move-Item is delete-then-move, and s4b-queue re-reads queue.jsonl on every pass with no try/catch. It uses absolute paths throughout, and no step runs while a legodimensions process runs.
1. Preconditions:
   - `build\agent3\s4b\PAUSE` is absent. If it exists, stop and ask.
   - The live queue is 69C77DA7.
   - No queue.jsonl.bak-stopR exists.
   - `check_queue_stopR.py --dryrun` (r3, 9F993FE4) reports ALL PASS.
2. Create PAUSE (empty file).
3. queue.out.txt shows `HOLD or PAUSE file: no launch; waiting`, timestamped at or after the PAUSE creation.
4. Copy queue.jsonl.stopR to `build\agent3\s4b\queue.jsonl.tmp-stopR`; its sha = CB502E8C.
5. `[IO.File]::Replace(tmp-stopR, queue.jsonl, queue.jsonl.bak-stopR)`. If it throws, stop and report, with no Move-Item fallback. Script: install-stopR.ps1 (steps 4-6).
6. Check queue.jsonl = CB502E8C and .bak-stopR = 69C77DA7. Then `--installed` must report ALL PASS.
7. Remove PAUSE. queue.out.txt then shows `idle; waiting for: [...]` listing s33stop3..7.
8. Write go-s33stop3 by hand, then each next go marker after reading the previous row, under §4 / M10 R3-R4.

Done:
- PAUSE created 10:39:36.438; HOLD line 10:39:39.
- Replace at 10:39:58.
- queue.jsonl CB502E8C, .bak-stopR 69C77DA7, `--installed` ALL PASS (61 ok).
- PAUSE removed 10:40:08.364; idle/waiting line 10:40:09.
- go-s33stop3 written at 10:42, after the Overseer ruled s33onw PASS?.

## 7. Hashes (pinned by M10's rating and addendum)

| file | sha8 |
|---|---|
| queue.jsonl.stopR = live queue.jsonl | CB502E8C |
| queue.jsonl.bak-stopR (old live) | 69C77DA7 |
| make_stopR.py | 5381B78B |
| check_queue_stopR.py r3 | 9F993FE4 |
| check_queue_stopR.py.bak-r2 | 72AC507F |
| check-queue-stopR.out.txt | 95CBAB6E |
| check-queue-stopR.dryrun.out.txt | 9C0B033C |
| check-queue-stopR.dryrun2.out.txt (R1 step 1) | 9120D8B0 |
| check-queue-stopR.installed.out.txt | 748AD695 |
| install-stopR.ps1 | 640AF853 |
| STOPR.md.rev2 (rated) | 583C40E2 |

## 8. Post-sprint item
A route-end trigger would make the close deterministic, unlike any fixed -Seconds. For example, close N s after the H0 burst, or at a scene mark from the input script; run-game already breaks on `$inputStop`. That is a harness/route change and is outside this sprint.
