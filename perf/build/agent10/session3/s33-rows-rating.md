# #33 rows 2-7 + (d) queue draft (M3): rating

M10, 2026-11-25 ~08:20 (Overseer request 14:12Z). Read-only review: no builds, game runs, markers or GO files.

## Files rated

| file | sha256 (16) | bytes |
|---|---|---|
| build/agent3/session3/s33-rows/S33-ROWS-PLAN.md | FDB7E425AF63A180 | 4514 |
| build/agent3/session3/s33-rows/queue-s33-rows.jsonl (15 rows) | EA5C866C98750294 | 8231 |
| build/agent3/session3/s33-rows/check_queue_s33.py | 9C35A3D4BCD8654D | 10084 |
| build/agent3/session3/s33-rows/check-queue-s33.out.txt (338 ok) | 6162ABECD4BCA86E | 20739 |
| build/agent3/session3/s33-rows/s4b_check.py (draft) | 3DDF1A5523617530 | 61334 |
| build/agent3/session3/s33-rows/s4b_check.diff (vs live 09DBCABC) | FAF8E21E8BF7178E | 8573 |
| build/agent3/session3/s33-rows/s33_onstop.py | 43D4DA7345A50CF3 | 4953 |
| build/agent3/session3/s33-rows/postcheck.ps1 (draft) | 2F8F24A8ED259D88 | 27881 |
| build/agent3/session3/s33-rows/postcheck.diff (vs installed D204503F) | F2D6E84DE078F1A7 | 7828 |

The Overseer's message cited S33-ROWS-PLAN.md 2C71C4AF. The file on disk is FDB7E425 (08:12), and it already carries the (a3) ruling. I rated FDB7E425.

## Base

- build/agent6/s33-popin/TESTPLAN.md 90DF23DE (section 2 rows, section 3 checks, section 4 conditions)
- harness-s33.json 4E30E135 (arm table)
- build/agent12/session3/ROWS-RESULTS.md, now 20B87F79 (it grew; the row-1 baseline is L109-121): offsf 1286 dropped draws in 48 frames, last #12707, late 0, forced waits 0 ms / 0 calls; row 1a/1b PASS
- r33-nohunk5-diagd.md B24EE8E2 ((d) code, N3)
- postcheck-0706-rating.md 6783F5AB (Q1/Q2)
- final-fx-rating.md (C1/S1/S2, now in installed postcheck D204503F)

## Verdict

**SAFE-IF C1-C5.**

The rows, bins, cvars, seconds and seeds match TESTPLAN and harness-s33.json, and the new proofs fail closed. The F hooks survive in the postcheck draft. The (a3) ruling is sound and errs toward STOP, but M3's reading method for it is wrong (C1). Rows 5 and 6 also lack the s33_fields reading that TESTPLAN needs (C2).

## What I checked

- **Queue vs TESTPLAN / harness-s33.json:**
  - Row 2 onsf: 540 s, `slow_frame_log_ms=1;no_wait=true`.
  - Row 4 stop1-5: 203/205/207/209/211, plus spares 206/210.
  - Row 5 offw/onw: 540 s, `-SeedXenos` = the row-1b offsf run's `user\cache\shaders\shareable`. That's the same bin, and the dir holds 2 files (5752084B.xsh, .rtv.d3d12.xpso).
  - Row 6 gthr0/gasync/gbind: 300 s, with threads=0 / async off / bindless off.
  - (d) offd/ond: on devoff4b-s33d-bin (MANIFEST 0B1CD3C2, gpu 962D88D6), 540 s.
  - All rows run attract-long + -GpuLog.
  - Every row needs ready-s4b-off + go-s33r + its own go-<id>. postcheck writes no #33 marker; M3 writes each go by hand.
  - Neither bin has a `cache\` dir.
- **My `check_queue_s33.py` run** (read-only, no --dryrun): exit 0, ALL CHECKS PASS (263 ok). M3's --dryrun out file shows 338 ok.
- **s4b_check diff** (only S33X, the row proofs, and the `short` handling):
  - Mode proofs match the patch's log text exactly. I read s33-popin-nohunk5-diagd.patch L215/L219/L88-105:
    - on = INFO `d3d12_pipeline_creation_no_wait: not waiting` x1 and `... ignored` x0;
    - gate = `ignored` x1 and INFO x0;
    - off = no `d3d12_pipeline_creation_no_wait` text and the cvar unset.
  - The cvar values must equal run.json.
  - `resolve after drop:` is a reading on the (d) bin and must be 0 elsewhere.
  - Seed: seed_xenos.source_dir must end in the offsf shareable path. Cold rows must have no seed_xenos; the real offsf run.json has null there.
  - Also required: WM_CLOSE, slow-frame lines > 0, no WER/dump. run.json has `wer_seen` and `dumps`, so the check isn't vacuous.
  - M3's test/ runs the draft on the row-1b run under the new ids. The expected proof MISSes show up: cvar missing, INFO x0, `ignored` x0, seed source `.`, (d) bin/gpu mismatch. Each hint is LOOK.
  - offsf-draft vs offsf-live differs only in out-dir paths and the hostload row count (14 vs 0). That count comes from a time-dependent host-log read, not from the diff (N4).
- **`short` (rows 4 and 6):** only GONE-beyond-Toypad and the attract step count become notes.
  - The judged route marks (first-frame..after-a2) sit at 4.9-~81 s in offsf (input.csv), well before 203 s, so a short run can't turn them into `missing` misses.
  - Front-end scenes stay hard misses.
  - [error]/[critical], STUCK-LOCK, exit and close are unchanged.
- **postcheck draft:**
  - The git no-index diff (ignore CR) vs installed D204503F is 69 insertions and 0 deletions, equal to postcheck.diff. The parser reports 0 errors.
  - The F hooks are kept: the $FgPin 73F946E7 pin, `$global:LASTEXITCODE = -1` before each tool, the F-GATE PASS line check (S1), and the S2 nativefinal cache STOP.
  - S33K follows Q1/Q2:
    - it clears %TEMP%\m3-s33\<row> and checks\<row> per row (unique names per id);
    - LASTEXITCODE is reset;
    - a `kit exit N` line is written;
    - the output is copied only on 0/1;
    - a copy failure appends `COPY FAILED` and returns `N/copy FAIL`;
    - a missing arm run gives SKIP.
  - S33R writes `<tool> exit N` after a reset.
  - Check bases: ON/gate rows on s33offsf with allow-new `$S33ON`; offw on offsf with no allow-new; onw on offw; offd on offsf with `resolve after drop`; ond on offd. s33offsf is in queue-state as 20261125-071741-s33-offsf, so B() won't fall back to $RA.
- **s33_onstop.py** (row 4):
  - counts = a slow-frame line with `new N>0` in the 2.0 s before the first `Window closing, shutting down`;
  - clean = exit 0, wm_close, no dump, no WER, close_seconds < close_timeout;
  - the watchdog `Shutdown wedged` line is a NOTE;
  - no close line → FAIL;
  - exit 0/1/3/2 as in the plan.
  This matches TESTPLAN row 4.
- **(a3)** (Overseer ruling; my rating):
  - Rationale: with no_wait, load frames end sooner, so the 30-row perf.csv median sampled at a mark can land in the neighbouring scene.
  - The conditions (same marks, same order, each within 1 s, both ids present in both runs, no NEW/FLAG/proof/other BASE miss) limit it to such boundary shifts.
  - If no_wait changes the draw counts themselves (dropped draws), the ON id won't exist in offsf, and (a3) gives STOP. That errs closed.
  - **But** the scene ids are not log text. s4a_check `marks()` builds them as median `draw_calls/vertices_processed` of perf.csv rows (e.g. `766/110956`), and grepping offsf's game.log for `110956` finds nothing. So M3's "grep both runs' game.log for both ids" would STOP every time, or invite an improvised reading. See C1.

## Conditions

- **C1 ((a3) method and scope).**
  - "Occurs in a run" means the id is a key of `s4a_check.scenes(run, 'off')` (perf.csv runs of ≥ 10 identical frames) for both runs.
  - For each differing mark, the reading records: the mark name, base id → cand id, t_s in both runs (input.csv), and the seconds of each id in each run.
  - Any id missing from either run's scenes means STOP.
  - Apply (a3) only to ON rows: s33onsf, s33stop1-7, s33onw, s33ond. Never to gate rows (row 6 ignores the cvar and must behave like row 1) or OFF rows (offw, offd); there, any mark difference stops #33.
  - SHOULD: the cand id is the base's scene immediately before or after it in the base's scene order.
- **C2 (s33_fields on rows 5 and 6).** Add an S33R `s33_fields` call to s33onw (offwarm + onwarm) and to each gate row (offsf + the gate arm), or M3 runs it read-only by hand before the next go. Read:
  - row 6: `forced pipeline waits 0.0 (0x)` on every line, and drops only in miss frames as in the baseline;
  - row 5: late drops 0, and onwarm drops only right after the storage load (TESTPLAN row 5 stop: drops long after boot).
  s33_fields exits 0 even with late drops (exit 1 = parse error only), so these numbers must be read by hand.
- **C3 (explicit row-2 reading before go-s33stop1).** M3 writes for s33onsf:
  - the INFO x1 proof;
  - s33_fields late drops: > 0 means STOP (failed pipeline);
  - forced waits ms total/max: > 0 means hold for an Overseer ruling (TESTPLAN watch: memexport/query pipelines in a burst);
  - dropped draws vs the row-1 baseline 1286/48/last #12707;
  - attrib ≥ 250 ms frames at the scene points;
  - [error]/[critical] 0 (DXGI / device removed);
  - pm unchanged.
- **C4 (install).** Install only after F1-F7 and #19 are done, between rows, with no postcheck mid-row.
  - Make the `.bak-s33r` backups first.
  - Run `check_queue_s33.py --dryrun` → ALL CHECKS PASS.
  - Just before the copy, confirm live postcheck is still D204503F and live s4b_check still 09DBCABC. If either changed (e.g. an F fix), rebase the draft and send it back for a conformance check.
- **C5 (scope of the result).** Row 3 (the user at the visible desktop) still gates any recommendation (TESTPLAN section 4, condition 3). Rows 2-6 + (d) alone can't make #33 a suggested setting. Leaving row 7 out (no D3D12 messages in game.log) is accepted; TESTPLAN marks it optional.

## Findings

- **S1 (SHOULD): spares.** There are only 2 spares (206/210). If more than 2 of stop1-5 return 3, stop and ask; don't pick new -Seconds ad hoc. Record each run's `last_miss_gap_s` and `misses_in_window` from onstop.json in the reading.
- **N1 (NIT):** S33X checks the listed cvars but not the absence of others. check_queue_s33 covers this on the queue side (arg cvars = arm cvars).
- **N2 (NIT):** on mode doesn't require the total of `no_wait` mentions to equal the INFO count. Logdiff NEW covers other new text.
- **N3 (NIT):** the seed proof checks the source path only. run.json seed_xenos also has each file's sha256, which could be compared with the source dir (a finished run, unchanged).
- **N4 (NIT):** the plan says the draft on offsf is "identical to live". It differs in out-dir paths and the hostload row count (time-dependent), not in any verdict line.
- **N5 (NIT):** for the short rows, the reading should note that the noted GONE keys first appear in base after the short run's length (route timing, not loss).
- **N6 (NIT):** `$S33ON` allows `memexport full-buffer` as new on ON rows. Give its count in the row-2 reading next to forced waits ms (C3).

## Read / Sent

Read: the files above, TESTPLAN 90DF23DE, harness-s33.json, s33-popin-nohunk5-diagd.patch (log strings), s4a_check `marks()`/`scenes()`, ROWS-RESULTS L109-121, the offsf run.json/input.csv/perf.csv and s33offsf.check.txt, queue-state, M3's test/ outputs.

Ran: check_queue_s33 read-only (output in scratch-final/s33chk/cq.txt), a git no-index diff of the postcheck draft vs installed, the PowerShell parser.

Sent: verdict + sha8 to the Overseer.

## Addendum 08:20: M3's (a3) fix (S33-ROWS-PLAN.md E6D3238D87A65D51, s33_sceneids.py BD344A9D837B1046)

**C1 partly met.** The source is right now: perf.csv `draw_calls/vertices_processed`, the same keys as s4a_check marks()/scenes(). The tool is read-only, and its exit 2/1 paths fail closed. Three points are still open:

- **The tool's PASS bar is lower than C1.** Exit 0 needs only `rows > 0`, so a single perf.csv frame with that key would count. C1 asks for a stable scene (≥ 10 identical frames). Fix: the reading requires `stable > 0.0s` for every id in both runs (the tool already prints it), or the tool's exit 0 requires it. A row-count-only match means STOP.
- **Scope is not in the plan.** (a3) applies to ON rows only: s33onsf, s33stop1-7, s33onw, s33ond. It never applies to gate rows (s33gthr0/gasync/gbind) or OFF rows (s33offw/offd), where any mark scene difference stops #33.
- **Record per differing mark:** the mark name, base id → cand id, t_s in both runs, and the tool's rows/stable output.

C2-C5 and S1 are unchanged.

## Addendum 08:30: conformance of M3's C1-C5/S1 fixes

M10, 2026-11-25 08:30. Overseer request 14:25Z. Changed files only, all in build/agent3/session3/s33-rows/.

| file | sha256 (16) |
|---|---|
| s33_sceneids.py | FA78C672D3777D29 |
| postcheck.ps1 | 36DC0E057381F2B4 |
| postcheck.diff | AFAEBBC62DB2858E |
| READING-S33.md | 976818B4FC979512 |
| S33-ROWS-PLAN.md | 37CF0E8210222D4C |

Unchanged (hashes re-checked): queue EA5C866C, s4b_check 3DDF1A55, s33_onstop 43D4DA73, check_queue_s33 9C35A3D4. Live postcheck is still D204503F.

**Verdict: CONFORMS.** C1 is now fully met (was partly met at 08:20). C2-C5 and S1 are met.

### What I checked
- **C1, s33_sceneids.py:**
  - Call form `--row <id> <base> <cand>`. Judged marks match s4b_check: up to up-2, else the non-idle marks except end. Scene ids come from perf.csv via s4a_check marks(). The tool is read-only.
  - It STOPs (exit 1) on any of these: names or order differ; any mark has |dt| >= 1 s; any id of a differing mark has stable <= 0.0 s in either run; any differing mark on a row that is not ON. ON_ROWS = s33onsf, s33stop1-7, s33onw, s33ond, which is correct. Exit 2 = usage error.
  - It prints, for each differing mark: the ids, t_s and rows/stable seconds in both runs, plus the SHOULD neighbour note.
  - Real pair basesf vs offsf: 0 differing marks, exit 0. No --row: exit 2.
  - My mutation test (scratch-final/s33chk/t_sceneids.py, which patches marks() on the cand):

    | case | rc |
    |---|---|
    | ON, stable neighbour | 0 (SHOULD yes) |
    | ON, stable non-neighbour | 0 (SHOULD NO, printed) |
    | ON, unstable id | 1 |
    | gate row | 1 |
    | OFF row | 1 |
    | mark +1.2 s | 1 |
    | missing mark | 1 |

  - NEW/FLAG/proof/other BASE misses are not checked by the tool. READING-S33.md step 1 covers them from check.txt (any of them → STOP). That split is fine.
- **C2, postcheck.ps1:**
  - Against the installed D204503F: +81 / -0, and postcheck.diff counts the same (81 plus, 0 minus). Parser: 0 errors. The F hooks (C1/S1/S2) are untouched.
  - s33onw runs s33_fields with offwarm = s33offw and onwarm = cand, else SKIP. Each gate row runs it with offsf = s33offsf and the gate arm = cand.
  - Reports go to logs\<id>.s33fields.report.txt, and exit lines to <id>.s33.txt.
- **C3, READING-S33.md:**
  - The row-2 template is explicit: late drops > 0 STOP; forced waits ms > 0 HOLD; drops vs 1286 / 48 / #12707; attrib >= 250 ms frames; [error]/[critical] = 0; pm onsf vs offsf 271, where 260-290 outside → HOLD; s33_fields misses vs 269; the tool exits.
  - Rows 4, 5, 6 and (d) also have hand readings.
- **C4, PLAN Install:** it happens after F1-F7 and #19, between rows, on go-s33r. Before the copy, live D204503F / 09DBCABC are checked; if either changed, rebase and come back to M10. Then --dryrun ALL CHECKS PASS and .bak-s33r backups of s4b_check, postcheck and queue.
- **C5:** row 3 gates any recommendation; rows 2-6 + (d) alone cannot make #33 a suggested setting; leaving out row 7 is accepted.
- **S1:** more than 2 exit-3 stop runs → stop and ask; no ad hoc -Seconds.
- **N4/N5:** both carried (N4: the test/ output differs only in paths and hostload count; N5: the GONE-timing note for short rows).
- **(a3) text** in PLAN L36-57 matches the tool, including the stable > 0.0 s rule and the ON-only scope.

### Findings
- NIT: the neighbour check is advisory only: an ON non-neighbour id still exits 0. PLAN L52 says the reading quotes the tool output, so make sure the quoted SHOULD line is part of each ON-row reading. A "SHOULD NO" line deserves a sentence in the reading. It does not stop the row.

Nothing in this addendum changes the C4 timing: nothing is installed before F1-F7 and #19.
