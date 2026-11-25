# SESSION3.md: M3 (successor of old Agent 3), session 3 log

Overseer: Agent 4 (fbf754e5). Task S3T-3. Paper only until LOAD GO, no game runs, no builds, no commits.

## 11-25 01:00-01:35, S3T-3 paper work
- Read BRIEF-COMMON, RESUME §6-7, agent3 HANDOFF, f10/RESULTS.md, the queue, postcheck, s4b-queue, run-game close path, holdwatch*, s4b_check, agent7 RATE-REQUEST §10, agent7 HANDOFF §4, QUEUE.md, agent9 HANDOFF §5.
- Employee E2.1 → `session3/KILL-AUDIT.md`: SAFE-IF, risks R1 and R2, which apply only to matrix rows / HOLD files. M3 re-read the key sites.
- Employee E2.2 → `session3/DRAW-BYTES.md`: title ≈ 47 KiB/frame, so N = 64 won't split the title. M3 checked the cites and had §7 item 4 fixed (a split = 0 run prints no split line).
- Wrote:
  - `session3/RUNPLANS.md`
  - `session3/READY-N.md`
  - `session3/queue-s3.jsonl` (9 rows, not appended)
  - `session3/f10_rule.py`
  - `session3/cpuload.ps1` (never run)
- Edited:
  - `s4b/s4b_check.py`: aliases for the new ids, quantum 500 for s4bQ5, the s4bV0 branch.
  - `s4b/postcheck.ps1`: cases for the new ids, P2c, F10.
  - Neither script is running.
- Dry tests on existing runs (BelowNormal):
  - f10_rule matches RESULTS.md (s4b20 and w6gB WARN, quiet f10 runs PASS).
  - s4b_check gives the same s4b18 result as before.
- Not done (by rule): no `go-*` / `ready-N` / `ready-later` markers, STOP still in place, nothing appended to `queue.jsonl`.
- Waiting for the Overseer's LOAD GO and a ready-N decision (READY-N.md §4: A / B / C).

## 11-25 01:36 onward, RUN GO (night, quiet host, no builds)
Queue: `s4b-queue.ps1 -LastLaunch 04:15 -GamesClosed 04:18:30`. Also running: `postcheck.ps1 -Until 04:30`, `hostload.ps1`. ready-N = option C (s4bN16). go-load is never created, so f10aL/bL are skipped.

| row | result | run dir (build/agent3/runs) | key numbers |
|---|---|---|---|
| s4bQ5 | PASS | 20261125-013748-s4b-Q5-gw-q500 | ON x1 (q500), 41 stats lines, sleep_fail 0, STUCK-LOCK 0 |
| s4bN16 | INCOMPLETE | 20261125-014239-s4b-N16-title-split16 | exit 0, 0 `d3d12_submit_split:` lines (nothing reached 16 KiB) → s4bN4 added |
| cg26b0 | PASS | 20261125-014556-cg26b0-boot-menus | exit 0 in 223 s, logdiff NEW 0 / MORE 0, gate_logdiff PASS, wc cg26 10/10, bin 45952D17 |
| win3f | PASS | 20261125-015006-win3f-level | exit 0 in 425 s, vortex reached, wc win3 15/15, NEW 0, f10 PASS, p2c NO DATA (expected) |
| c1npf | PASS | 20261125-015722-c1npf-level | exit 0 in 421 s, NEW 0 / MORE 0, f10 PASS, wc c1np 12/12, kept 159744 |
| s4b07r | PASS | 20261125-020440-s4b-07r-c1v-level | exit 0 in 566 s, K 0, **F 51** (quiet host; row 7 under load: 92), kept 61440, f10 PASS; hint LOOK only for the verify-F warning NEW |
| s4bV0 | PASS | 20261125-021419-s4b-V0-c1off-verify-level | exit 0 in 564 s, C1 off, verify on x1, K 0, **F 70**, so Agent 12's F>0 is confirmed; f10 PASS; LOOK: verify-F NEW + pads-white timing |
| s4bLV | PASS | 20261125-022357-s4b-LV-p2fcv-level-long | exit 0 in 555 s of 1800 s (the route ended), all 6 w6gA cvars, K 0, **F 0** (G5), kept 61440, P2 memexport full-buffer total 0 (p2c PASS), slow-frame lines 12045, STUCK-LOCK 0, f10 PASS, NEW 0 |
| f10a3 | PASS (f10), hint LOOK | 20261125-023326-f10a3-m1-sfl-level | exit 0 in 394 s, STUCK-LOCK 0, level, tags 3/3; LOOK: 1/12 hostload samples had ninja (02:36:03), pads-white timing, GONE XNetLogon stub |
| f10b3 | PASS (f10, p2c), hint LOOK | 20261125-025013-f10b3-p2fc-level | exit 0 in 398 s (route ended), 6 cvars as planned, STUCK-LOCK 0, level, tags 3/3, quiet host 0/12, kept 192512, K 0, P2 total 0, NEW 0; LOOK: GONE XNetLogon stub. Quiet f10 tally tonight 0 hangs (f10a3 + f10b3) |
| cg26L | PASS (wc 10/10, f10), hint LOOK | 20261125-025738-cg26L-level | devoff4b-cg26-bin (exe 45952D17), no cvars; exit 0 in 393 s (route ended), level, tags 3/3, STUCK-LOCK 0, NEW 0; LOOK: pads-white timing, GONE XNetLogon stub |
| s4bN4 | PASS? (M12: PASS) | 20261125-030425-s4b-N4-title-split4 | split 4 KB: 18 split lines, per frame submission 3.113 / splits 1.889 / failed 0, so K 1.225, ~10 KiB/frame (~8.2 KiB per natural submission, hence 0 splits at 16), proposed N = 4; no fallback A |

- 03:08 M3 IDLE: STOP file (queue ended 03:08:07), postcheck/hostload killed, go-quiet/go-n/go-user deleted, no processes left. f10aL/f10bL skipped (Overseer). Post-window drafts (s4bV0f/s4b07f on devoff4bv, #33 rows 1a/1b): `build/agent3/session3/post-window/POSTWIN-PLAN.md`, for M10's rating.
- 06:28 post-window:
  - M10 rated the drafts SAFE-IF (`build/agent10/session3/postwin-rating.md`); its S1 deps scan passed.
  - The drafts were installed live: s4b_check.py 09DBCABC, postcheck.ps1 8B60EBC3; backups `*.bak-postwin`.
  - The rows came from `post-window/queue-postwin-live.jsonl`, with per-row #33 gate markers go-s33off / go-s33-1b / go-s33offsf.
  - **N2: the #33 runs are in `build/agent3/runs`, not M6's `runs-s33`.**
  - s4bV0f launched 06:29:31.

- 02:33 Overseer plan change: morning builds run tonight. f10a3 was already running (launched 02:33:24) and finished. f10b3, cg26L and s4bN4 now also need `build\agent1\night\ROWS-RESUME.txt` (queue.jsonl backup `.bak-0233`). At 02:40 the queue was restarted with `-LastLaunch 04:50 -GamesClosed 05:00`, and postcheck/hostload with `-Until 05:15`. Sent M3 HOLD 02:40.

Tool edits tonight (backups `*.bak-0158`):
- `s4b/s4b_check.py` B8014B04: the s4bV0 branch needs c1_verify_on == 1 (M10 S1); N-row aliases.
- `s4b/postcheck.ps1` 03822B00: new rows, plus a WC step that runs wc_proof.
- `session3/f10_rule.py` F6B47350: recovery needs perf.csv to grow ≥10 s after the event (M10 S2).
- `session3/wc_proof.py` 6CFD8F3D: new. Checks the bin hash and the leaked-cvar lines (M10 S3 / NIT1 / NIT3).
- 02:10 `session3/f10_rule.py` D049928C (backup `.bak-0210`), for M12: new perf_frames() fallback for when no input.csv step pair follows the event (route inside a wait_log). Frames are mapped to time with perf.csv frame_time_us from the last step's perf_bytes. Recovered = the rows after the frame in progress at the event cover ≥10 s, with ≥ max(2, half the pre-event 10 s) frames. Result: w6gA's event is now finding 10 (9 frames vs 4 before it), but the run is still FAIL on level=False. Other runs unchanged.


## 07:26 post-window #33 results (M3)
- s4bV0f PASS (K 0 F 0), s4b07f PASS (K 0 F 0): devoff4bv verify fix holds on level-l.
- s33base LOOK → PASS? (ruling a: only GONE XNetLogonGetTitleID STUB); s33off LOOK → PASS? (ruling a2: mark timing after-a1, 44/44 same order, max 0.34 s); M12 gated PASS?. Row 1a kit re-run by hand: exit 0 (checks/s33-row1a).
- s33basesf LOOK → PASS? (a2: after-a1 220/528->220/534, 44/44 same order, max 0.35 s); s33offsf PASS?. Row 1b kit exit 0 ref offsf, no_wait x0 both arms, s33_fields exit 0 (dropped draws 1286 in 48 frames, last frame 12707, late 0; forced waits 0). checks/s33-row1b.
- Runs are in build/agent3/runs (N2).
- postcheck.ps1: 8B60EBC3 (06:28) → 123FD6D0 (07:06, TEMP out + copy) → 4ED8202B (07:08, kit/fields exit lines) → 1025D1F6 (07:10, M10 Q1/Q2: clear dirs, copy -ErrorAction Stop, COPY FAILED). Backups .bak-postwin/.bak-0706/.bak-0709; diffs in session3/post-window/.
