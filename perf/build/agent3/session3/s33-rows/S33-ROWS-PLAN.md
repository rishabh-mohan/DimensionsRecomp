# #33 rows 2-7 + (d): queue draft (M3, 11-25 08:15). DRAFT: not installed

Spec: build/agent6/s33-popin/TESTPLAN.md (P3 plan) plus the Overseer's 07:26 order. Runs come after F1-F7 and #19.

## Rows (queue-s33-rows.jsonl, 15 rows, all on attract-long with -GpuLog and slow_frame_log_ms=1)

| row | queue id(s) | bin | cvars beyond slow_frame | Seconds | base for s4b_check | kit (ref arm) + reports |
|---|---|---|---|---|---|---|
| 2 | s33onsf | devoff4b-s33-bin | no_wait=true | 540 | s33offsf, allow-new $S33ON | s33-row2 (offsf); s33_fields, attrib --thresh 250, slowframe_join --min-ms 250 |
| 4 | s33stop1-5 (+ spares 6-7) | devoff4b-s33-bin | no_wait=true | 203/205/207/209/211 (206/210) | s33offsf, $S33ON | s33-row4-<id> (offsf); s33_onstop.py |
| 5 | s33offw, then s33onw | devoff4b-s33-bin | offw: none; onw: no_wait=true | 540 | offw: s33offsf, no allow-new; onw: s33offw, $S33ON | s33-row5-offw (offsf); s33-row5 (offwarm) + s33_fields offwarm/onwarm |
| 6 | s33gthr0, s33gasync, s33gbind | devoff4b-s33-bin | no_wait=true plus threads=0 / async_shader_compilation=false / d3d12_bindless=false | 300 | s33offsf, $S33ON | s33-row6-<arm> (offsf) + s33_fields offsf/<arm> |
| (d) | s33offd, then s33ond | devoff4b-s33d-bin | resolve_after_drop_log=true (ond: + no_wait=true) | 540 | offd: s33offsf, 'resolve after drop'; ond: s33offd, $S33ON + 'resolve after drop' | s33-rowd-offd (offsf); s33-rowd (offd) + diagd_report |

- `$S33ON` = `d3d12_pipeline_creation_no_wait|slow frame|memexport full-buffer`. It is used for ON/gate rows only, never for OFF rows.
- The kit's `--ref` is always a cvar-off arm (TESTPLAN).
- Row 5 seeds: s33offw/s33onw run with `-SeedXenos` = the row-1b offsf run's `user\cache\shaders\shareable` (2 files). s4b_check proves the seed from run.json `seed_xenos`.
- **Row 3** (the user's visible desktop) is not queued.
- **Row 7** (debug layer) is blocked: D3D12 messages go to OutputDebugString, not game.log. It needs a capture tool or a logging patch.

## Order and markers
- Every row needs `ready-s4b-off`, `build\agent3\session3\go-s33r` (Overseer), and its own `go-<id>`.
- M3 writes `go-<id>` by hand after reading the previous row's check.txt and s33.txt. postcheck writes no #33 markers.
- Order: 2 → 4 (stop1-5) → 5 (offw → onw) → 6 (gthr0, gasync, gbind) → (d) (offd → ond).
- Stop at the first FAIL.
- Spares s33stop6/7 run only if a stop run's s33_onstop exits 3 (DOES NOT COUNT). Exit 1 is a FAIL.
- **M10 S1:** if more than 2 of the stop runs return exit 3, stop and ask the Overseer. No new -Seconds ad hoc.
- Each stop reading records `last_miss_gap_s` and `misses_in_window` from logs\<id>.onstop.json.
- For short rows (4, 6), the reading notes that the GONE keys noted by s4b_check first appear in base after the short run's length (route timing, not loss).
- (d): diagd_report exit 1 (WARN) means the diagnostic counter drifted, which is a bug in the diagnostic. Report it; it does not gate the cvar.

## Reading rules carried
- **(a):** a BASE GONE `__imp__XNetLogonGetTitleID STUB` alone counts as PASS?.
- **(a2):** a BASE LOOK on mark timing only counts as PASS? when the marks are the same, in the same order, with delta < 1 s, and there is no other miss.
- Any other miss stops #33.
- **(a3)** (Overseer 08:12): an ON-row LOOK with only scene-id differences counts as PASS? when all of these hold:
  - the same mark names, in the same order;
  - every mark is within 1 s;
  - both scene ids occur in both runs;
  - no NEW, FLAG or proof miss, and no other BASE miss.
- Any other LOOK stops #33.
- How M3 reads (a3), per M10 s33-rows-rating C1 (08:24):
  - Scope: ON rows only (s33onsf, s33stop1-7, s33onw, s33ond). On gate rows (s33gthr0/gasync/gbind) and OFF rows (s33offw, s33offd), any differing judged mark stops #33.
  - Mark scene ids are s4a_check keys `draw_calls/vertices_processed` from **perf.csv** (s4a_check marks()/scenes()), not from game.log.
  - Run `python -B build\agent3\session3\s33-rows\s33_sceneids.py --row <id> <base run> <cand run>` (base = the row's s4b_check base).
  - It uses the same judged marks as s4b_check (up to up-2, or the non-idle marks other than end) and checks:
    - same names, same order;
    - every mark within 1 s (input.csv t_s);
    - every id of every differing mark a **stable** scene (>= 10 identical frames, stable > 0.0 s) in both runs. A row count alone does not count.
  - It prints, for each differing mark: name, base id → cand id, t_s in both runs, each id's rows/stable seconds in both runs, and the SHOULD note (cand id next to base id in base scene order).
  - Exit 0 = PASS? (and the row is ON); exit 1 = STOP; exit 2 = usage / no marks or perf.csv.
  - The reading quotes its output.
  - Tested:
    - basesf→offsf as s33onsf: 0 differing marks, exit 0.
    - udiag-attract→offsf as s33onsf: 1 differing mark, both ids stable in both runs, but marks 4.5 s apart → STOP, exit 1.
    - The same pair as s33offw: STOP, also "differ on a row that is not ON".
    - No args: exit 2.
- Hand-reading steps for s33_fields (rows 2, 5, 6) and the row-2 template: READING-S33.md.

## Install (one step, between rows, after F1-F7 and #19, on the Overseer's go-s33r; M10 C4)
1. Make sure no row is running and postcheck is between checks.
2. Confirm live `build\agent3\s4b\postcheck.ps1` is still **D204503F** and live `s4b_check.py` is still **09DBCABC**. If either changed (e.g. an F fix), rebase the draft and send it back to M10 for a conformance check before installing.
3. Run `check_queue_s33.py --dryrun` (clear its old dryrun dirs first). It must print ALL CHECKS PASS.
4. Back up live s4b_check.py, postcheck.ps1 and queue.jsonl as `.bak-s33r`.
5. Copy the draft `s4b_check.py` over live; it adds the S33X table and the mode, seed and (d) proofs. The diff is in s4b_check.diff.
6. Copy the draft `postcheck.ps1` over live.
   - It is the installed F postcheck D204503F plus the #33 cases only (postcheck.diff), so the F hooks (C1/S1/S2) are kept.
   - Restart it between checks.
7. Append `queue-s33-rows.jsonl` to queue.jsonl.
8. The Overseer creates go-s33r. M3 then creates go-s33onsf.

## Scope of the result (M10 C5)
- Row 3 (the user at the visible desktop) still gates any recommendation (TESTPLAN section 4, condition 3).
- Rows 2-6 + (d) alone cannot make #33 a suggested setting.
- Row 7 is left out (accepted; optional in TESTPLAN).

## Estimates
- Core rows: 5025 s (about 84 min) of queue time, plus quiet waits.
- Spares add 476 s.
- Postcheck per row: kit about 4 s, reports under 30 s.

## Files (this dir)
- queue-s33-rows.jsonl
- check_queue_s33.py, with output in check-queue-s33.out.txt (dryrun: ALL CHECKS PASS, 338 ok)
- s4b_check.py + s4b_check.diff
- s33_onstop.py
- s33_sceneids.py (the (a3) read)
- postcheck.ps1 + postcheck.diff
- test/: the draft s4b_check run on the row-1b runs with the new ids. As expected, the new ids show proof MISSes on an OFF run. The s33offsf output matches live in every verdict line; it differs only in out-dir paths and the time-dependent hostload row count (M10 N4).
