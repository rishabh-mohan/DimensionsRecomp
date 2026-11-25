# STOPR rev 2 rating: re-timed #33 row 4 (s33stop3..7)

M10, 2026-11-25 10:31. Request: Overseer 16:17Z, 16:24Z, 16:25Z, 16:28Z.

| file | sha256 (16) | bytes |
|---|---|---|
| build/agent3/session3/s33-rows/stopR/STOPR.md (rev 2) | 583C40E2ABBB1DBE | 10821 |
| build/agent3/session3/s33-rows/stopR/queue.jsonl.stopR | CB502E8C56089BF2 | 51244 |
| build/agent3/session3/s33-rows/stopR/make_stopR.py | 5381B78B88409D01 | 2101 |
| build/agent3/session3/s33-rows/stopR/check_queue_stopR.py | 72AC507F1D792114 | 8742 |
| build/agent3/session3/s33-rows/stopR/check-queue-stopR.out.txt | 95CBAB6EE1853E6A | 3579 |
| build/agent3/s4b/queue.jsonl (live, unchanged) | 69C77DA7 | |
| build/agent3/s4b/s4b-queue.ps1 (live queue runner, read only) | CCA391CA | |

Base:
- my s33-rows-rating.md (S1: more than 2 exit-3 runs → stop and ask, no ad hoc -Seconds; N5);
- S33-ROWS-PLAN / READING-S33 line 46;
- M12's H0 confirmation: s33-h0 B5DA7B49, s33-ssim 18364E5D.

## Verdict: SAFE-IF R1-R5

The re-timing is a principled replacement for S1's "no ad hoc -Seconds", as long as it is frozen as written (R2) and the outcomes are fixed up front (R3). The install must use the R1 procedure, not STOPR §6 step 3 (Move-Item).

## What I checked
1. **Queue diff.** `git diff --no-index` live 69C77DA7 vs CB502E8C:
   - exactly 5 lines change, 93-97;
   - per line, only -Seconds, est and note differ;
   - S/est: stop3 153/183, stop4 146/176, stop5 230/260, stop6 231/261, stop7 192/222 (were 207/209/211/206/210).
   - Every other line is byte-identical. check-queue-stopR.out.txt says ALL PASS 60, consistent with that diff. I did not run it.
2. **make_stopR.py.** It reads the live queue read-only and rewrites only those three fields on the 5 ids, keeping the CR per line. The JSON re-serialisation matches the original formatting (the diff shows no other byte change).
3. **H0 lock, spot check.** `new 67` lines:
   - stop2: 10:16:49.036, minus started 10:14:24.319 = **144.72 s**, matching §2;
   - onsf and offsf: the lines are present (game.2.log / game.1.log).
   - M12 confirms the pattern independently, so **(d) is met**.
   - Independent support: the attract-long.txt header (4D35FAF4) already records that "the exit came ~19-20 s after the last press in 3 of 5 runs, and not within 26 s in the other 2". That idle-exit jitter is the H0 drift, so a fixed wall-clock -Seconds was bound to land in quiet gaps.
4. **Log rotation.** At 230/231 s a run is near the 5 MB rotation point: stop2 was 4.0 MB at 205 s, and the first rotation came at ~258 s in onsf and ~275 s in offsf. s33_onstop joins game*.log oldest first (ROT_RE, L24-32), and s4b_check reads rotated logs, so rotation is safe.
5. **Short-row reading at 146/153.**
   - The judged route marks (first-frame..after-a2) all fall before ~92 s, since after-a2 is ~380 s before the ~472 s first input.
   - So at S = 146 every judged mark is still inside the run. Idle marks, attract steps and logdiff GONE stay notes under `short` (stop1 check.txt: GONE 124, 0 unexpected; steps 37/91; BASE items missed: none).
   - No s4b_check change is needed.
6. **Queue runner (for (c)).**
   - s4b-queue.ps1 runs under Windows PowerShell 5.1 (powershell.exe) with `$ErrorActionPreference = 'Stop'` (L35).
   - The main loop (L113-172) re-reads queue.jsonl on every pass (L128-131), with no try/catch around `Get-Content` / `ConvertFrom-Json`.
   - In PS 5.1, `Move-Item -Force` over an existing file is delete-then-move. A read that lands in that gap throws, and with 'Stop' **ends the queue script**.
   - The `Held` check (L115) comes **before** the queue read. With a PAUSE file present the loop only sleeps 5 s and never opens queue.jsonl.
   - holdwatch.ps1 and holdwatch-m.ps1 watch only perf-notes/WINDOW-HOLD.txt, so **PAUSE never aborts a running game**.
   - Current state (10:30): no PAUSE and no queue.jsonl.bak-stopR exist; the queue is idle after s33offw (DONE 10:27:45).

## Rated points
- **(a) The budget replacing S1.** Yes, for these 5 runs only, because the reasons S1 existed are met:
  - S1 was against hunting: picking a new -Seconds after each miss until something counts. STOPR instead derives one set from all prior runs by a stated method, gets it confirmed independently (M12), fixes it before any re-timed run, and caps it at 5.
  - Selecting close times to satisfy the *precondition* (a miss in flight at the close) does not bias the *outcome* being measured (a clean shutdown).
  - S1 stays in force in this form: no further re-time after any stopR result without a new rating (R2).
- **(b) 3 vs onstop x5.** 3 counted is enough for the row-4 reading, provided it is reported as a reduction and not as x5. The required wording is in R4.
  - Reason: row 4 is a qualitative shutdown check. Clean shutdown is also exercised on every other ON row (onsf, onw, gate rows, ond), though at quiet points.
  - Cost: lower power against an intermittent shutdown fault. If each run fails with probability p, the chance of seeing it at least once is 1-(1-p)^3 instead of 1-(1-p)^5.
- **(c) Queue replacement.** SAFE only with the R1 procedure. Atomic Move-Item is not atomic in PS 5.1 (see check 6).
- **(d) M12 agreeing.** Met. It is not a condition any more.
- **(e) Base comparison and N5 at 146/153 and 230/231.**
  - No change to s4b_check, the base (s33offsf) or the (a3) rule (check 5).
  - The N5 note must compare against **each run's own close** (seconds_requested + ~0.1 s), not "203-211".
  - Under the H0 lock, if the cand's H0 is later than the base's (offsf 148.94 s), a base key up to (H0_cand - H0_base) seconds before the close may be GONE for route-timing reasons. Read N5 H0-relative in that case (S2).
  - 146/153 is a harsher close point (dense H0 burst, heavy-scene load). That is in the spirit of row 4, but it affects how an exit 1 is attributed (S1 below).

## Conditions
- **R1, install procedure (replaces STOPR §6 steps 2-4).** All paths absolute: .NET resolves relative paths against the process cwd, not `$PWD`.
  1. Check the preconditions:
     - `build\agent3\s4b\PAUSE` does **not** exist. If it does, someone else holds the queue: stop and ask, and do not remove it.
     - Live queue.jsonl sha = 69C77DA7.
     - queue.jsonl.bak-stopR does not exist.
     - `check_queue_stopR.py --dryrun` reports ALL PASS. Run the dryrun only while no game runs.
  2. Create `build\agent3\s4b\PAUSE` (empty file).
  3. **Confirm the queue saw it:** `build\agent3\s4b\logs\queue.out.txt` must show a new line `HH:mm:ss HOLD or PAUSE file: no launch; waiting`, timestamped at or after the PAUSE creation time.
     - The line is printed only on the transition into the held state. If a game was running, it appears only after that run and its postcheck end; wait for it, since that moment is the row boundary.
     - If WINDOW-HOLD was already active, the line may predate PAUSE. Then accept it only if it is the last line in queue.out.txt and no legodimensions process runs.
     - Once the line is seen, every later pass checks Held before reading the queue, so the swap cannot race.
  4. Copy queue.jsonl.stopR to `build\agent3\s4b\queue.jsonl.tmp-stopR` (same directory and volume), and check its sha = CB502E8C.
  5. `[IO.File]::Replace('<abs>\build\agent3\s4b\queue.jsonl.tmp-stopR', '<abs>\build\agent3\s4b\queue.jsonl', '<abs>\build\agent3\s4b\queue.jsonl.bak-stopR')`
     - This is one ReplaceFile call; it keeps the old file as .bak in the same step.
     - If it throws, the old queue.jsonl is intact: stop and report, and do not retry with Move-Item.
  6. Check the shas: queue.jsonl = CB502E8C, queue.jsonl.bak-stopR = 69C77DA7. Then `check_queue_stopR.py --installed` must report ALL PASS.
  7. Remove PAUSE. Confirm that queue.out.txt then shows `idle; waiting for: [...]` listing s33stop3..7.
  8. Only after step 7, write go-s33stop3 by hand. Report the new queue sha, the .bak sha and the PAUSE create/remove times.
  - Never do any step while a legodimensions process runs.
- **R2, frozen set.**
  - S set and order exactly as in CB502E8C: stop3 153, stop4 146, stop5 230, stop6 231, stop7 192, run in that order.
  - No rev 3, no re-ordering and no extra stop rows after any stopR result without a new rating.
  - S1 is replaced only for these 5 runs.
- **R3, outcomes fixed up front:**
  - **3 counted (exit 0), all runs clean** → row 4 reads PASS (as worded in R4); stop row 4 there.
  - **Any exit 1** (unclean shutdown) → FAIL; stop #33 at once (S1 covers attribution).
  - **All 5 run and fewer than 3 count, with no exit 1** → row 4 is **INCONCLUSIVE (HOLD)**: not PASS, not FAIL. Ask the Overseer. It must not be read as PASS, and there is no further re-time under R2.
  - **Exit 2 from s33_onstop** (a tool or usage error) → stop and ask. It neither counts nor uses budget until it is resolved.
  - stop1/2 stay recorded as exit 3 (clean, not counted). They are outside the budget.
- **R4, reading wording for (b).**
  - The row-4 line says "N counted of 5 planned (TESTPLAN onstop x5, reduced to >= 3 by the STOPR budget, Overseer 16:17Z)". It never says "onstop x5".
  - It lists **every** stop run, stop1 and stop2 included, with: S, exit, `last_miss_gap_s`, `misses_in_window`, close_method, close duration, and `watchdog_wedge_lines` (W9 NOTE).
- **R5, provenance.**
  - Install exactly CB502E8C; the live queue must still be 69C77DA7 at the swap.
  - If either sha differs, re-run `check_queue_stopR.py`, and send the diff to me before installing.

## Findings
- **S1 (SHOULD), attribution of an exit 1 at 146/153.**
  - A FAIL there stops #33 as written. But the close lands during the dense H0 burst / heavy-scene load, and no OFF stop control exists at those S values (row 4 was ON-only by design).
  - The read-out should therefore say "unclean shutdown under no_wait during the H0 burst; attribution open". It should say that until the Overseer decides whether to run one OFF control at the same S, with the s33offsf args (devoff4b-s33-bin, `slow_frame_log_ms=1` only, cold) and `-Seconds <S>`.
  - That control is diagnostic only; it is not a gate.
- **S2 (SHOULD), N5 reading.** Compare against the run's own close, and read H0-relative when H0_cand > H0_base (see (e)).
- **S3 (SHOULD), close duration.** Record WM_CLOSE → exit for each re-timed run next to stop1/2 (quiet closes), so the "harsher point" claim in (d) is shown, not assumed. A close duration far above stop1/2 with exit 0 is a NOTE, not a FAIL.
- **N1 (NIT).** The odds in §3 (P(>=3) 0.93 / 0.85) come from 5 runs and 5 H0 values. The route header suggests the idle exit can come more than 26 s after the last press, so H0 may fall outside 132.7-148.9 s, and 146/153 would then miss together (as §3 notes). Treat the odds as optimistic. R3's HOLD outcome covers it.
- **N2 (NIT).** STOPR §6 step 3 ("Move-Item it over queue.jsonl in one step") is superseded by R1. Also correct, after the sprint: the s4b_check L439 comment "203-211 s", the S33-ROWS-PLAN row table and TESTPLAN row 4.
- **N3 (NIT).** STOPR §7 defers the hashes to the M3 report. This rating pins them (table above).

## Addendum 10:32: checker r3 (Overseer 16:31Z)

| file | sha256 (16) | bytes |
|---|---|---|
| check_queue_stopR.py (r3, now the rated checker) | 9F993FE48B53B6F3 | 8997 |
| check_queue_stopR.py.bak-r2 (= the r2 checker above) | 72AC507F1D792114 | 8742 |
| check-queue-stopR.dryrun.out.txt | 9C0B033C5A67DBAB | 5119 |

Rated data unchanged: STOPR.md 583C40E2, queue.jsonl.stopR CB502E8C, live queue 69C77DA7 (re-hashed 10:31).

**Diff r2 → r3** (`git diff --no-index --ignore-cr-at-eol`): one hunk at L150-156, +4/-1.
- The `--dryrun` check `rj.get('seconds_requested') == S` is replaced by:
  - `'seconds_requested' not in rj`;
  - `-Seconds` in the queue args is all digits and `int == S`.
- `re` is already imported (L10). `args_map` is defined (L55).
- The preceding check is unchanged: `cp.returncode == 0` and exactly one new dir (L149).

**Assessment: CONFORMS. The fix is correct.**
- harness/run-game.ps1 (C2533FDF) writes `seconds_requested` only in the real-run run.json (L367). The DryRun branch (L206) does not, so the old check could never pass.
- The new check plus the exit-0 check proves that the value is an integer S and that `[int]$Seconds` binding succeeded. That is all a dryrun can prove.
- The dryrun output shows 90 ok, ALL PASS, for each of the 5 rows: exit 0, one new dir under stopR/dryrun, -Seconds 153/146/230/231/192, bin_dir devoff4b-s33-bin, ON cvars, cold, input script 91 steps.

**Added to R4:** since the dryrun cannot see seconds_requested, each real stopR run's reading also confirms run.json `seconds_requested == S` (s33_onstop reads it). A mismatch means stop and ask.

R1 step 1 now reads: `check_queue_stopR.py --dryrun` (r3, 9F993FE4) ALL PASS. The verdict is unchanged: **SAFE-IF R1-R5**.
