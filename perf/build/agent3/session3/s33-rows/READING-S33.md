# #33 rows 2-6 + (d): hand-reading steps (M3 draft; M10 s33-rows-rating C1-C3, S1, N5, N6)

M3 reads every row by hand before creating the next `go-<id>`. postcheck only collects the outputs listed below.
- Stop at the first STOP.
- A HOLD waits for an Overseer ruling.
- s33_fields exits 0 even with late drops (exit 1 = parse error only), so its numbers are always read from the text.

## Every row (all ids)
1. `logs\<id>.check.txt`: the VERDICT line. Apply rulings (a)/(a2)/(a3) only as written in S33-ROWS-PLAN.md.
   - Any NEW, MORE or FLAG, or a proof miss → STOP.
2. In the same file:
   - the `levels {...}` line: no `error` or `critical` key (offsf: info 23429, warning 142). Any `[error]`/`[critical]` → STOP.
   - `errors 0`;
   - families `stuck_lock=0 minidump=0 fatal=0 debug_layer=0 dred=0 d3d12_msg=0 clean_exit=1`.
3. `logs\<id>.s33.txt`: `kit exit N`. 0 = PASS, 1 = read the kit report in checks\<row>\, anything else = STOP. Also: no `COPY FAILED`, and every `<tool> exit N` line.
4. A mark LOOK on an ON row → (a3): run `s33_sceneids.py --row <id> <base> <cand>` and quote its output. Exit 1 → STOP.
   - Always quote every `SHOULD:` line. Any `SHOULD: ... NO` (cand id is a stable id that is not next to the base id) → HOLD for the Overseer's ruling, not PASS? (Overseer ruling on M10 NIT, s33-rows-rating 9D96775F).
   - On gate/OFF rows, any differing judged mark → STOP.

## Row 2: s33onsf (template; fill in before go-s33stop1, M10 C3)
```
row 2 s33onsf  run <run dir name>  (base/ref s33offsf 20261125-071741-s33-offsf)
check.txt VERDICT: ...                      rulings applied: ...
INFO proof: "d3d12_pipeline_creation_no_wait: not waiting" x? (need 1), "ignored" x? (need 0)
s33_fields onsf (logs\s33onsf.s33fields.report.txt):
  late drops: ?                      -> > 0 = STOP (failed pipeline)
  forced pipeline waits: ? ms total (? calls), max ? ms   -> ms > 0 = HOLD for an Overseer ruling (read ms, not calls)
  dropped draws: ? in ? frames, last at frame ?   (row-1 baseline offsf: 1286 in 48 frames, last #12707; ON should drop
                                                   only after misses)
attrib --thresh 250 (logs\s33onsf.attrib.txt), frames >= 250 ms at the scene points, offsf -> onsf:
  first 3D frame: ? -> ?   H0: ? -> ?   67-miss burst ~H0+21 s: ? -> ?   12.4k shot: ? -> ?
  (expect: only the non-compile residue remains: PRE / heavy / fence-wait / depth-only classes)
slowframe_join (logs\s33onsf.sfjoin.txt): the >= 250 ms frames and their slow-frame lines, quoted where they explain a point
[error]/[critical]: ? (need 0; DXGI / device removed = STOP)
memexport: families memexport=? vs slow_frame=? (offsf 22697/22697, every slow-frame line carries the memexport field);
  lines with "memexport full-buffer" that are not "slow frame #" lines: ? (offsf 0)   (N6: next to forced waits ms)
pm (sum of perf.csv pipeline_cache_misses): onsf ? vs offsf 271 (base 280, basesf 278); outside 260-290 = HOLD
s33_fields "misses": onsf ? vs offsf 269
kit: exit ?   s33_fields/attrib/slowframe_join exits: ?/?/?
result: PASS? / STOP <why> / HOLD <why>
```

## Row 4: s33stop1-7
- `logs\<id>.onstop.txt` + `.onstop.json`. Exit 0 = counts, 3 = does not count (run a spare), 1 = FAIL → STOP.
- Record `last_miss_gap_s` and `misses_in_window` from onstop.json.
- **More than 2 exit-3 runs → stop and ask the Overseer (M10 S1).** No new -Seconds.
- N5: s4b_check's short-row notes (GONE beyond Toypad, attract steps) must be keys that first appear in base after the run's length (route timing, not loss). Check that with the base check.txt timestamps.

## Row 5: s33offw → s33onw (M10 C2)
- s33offw: s4b_check on offsf with no allow-new; seed proof PASS; the kit vs offsf exits 0.
- s33onw: `logs\s33onw.s33fields.report.txt` (arms offwarm, onwarm). Read both arm blocks:
  - `late drops 0` in both arms. Any > 0 → STOP.
  - onwarm `dropped draws ... last at frame N`: drops only right after the storage load. Compare frame N with the frame of the `from the storage` line / first frame. Drops long after boot → STOP (TESTPLAN row 5).
  - `forced pipeline waits 0.0 ms total (0 calls)` in offwarm. In onwarm, ms > 0 → HOLD.
- Both seed proofs PASS (s4b_check).

## Row 6: s33gthr0, s33gasync, s33gbind (M10 C2)
- `logs\<id>.s33fields.report.txt` (arms offsf, <gate arm>). The gate arm must read like row 1:
  - `latch: INFO not-waiting 0, WARN ignored 1`;
  - `forced pipeline waits 0.0 ms total (0 calls), max 0.0 ms in one frame`. Anything else → STOP;
  - `late drops 0`; dropped draws only in miss frames, as in the offsf baseline (1286/48/#12707 order of size).
- An INFO line in a gate arm → STOP.
- (a3) does not apply: any differing judged mark → STOP.

## (d): s33offd → s33ond
- s33offd: s4b_check on offsf (allow-new `resolve after drop` only); the kit vs offsf exits 0.
- s33ond: `logs\s33ond.diagd.report.txt` / `.diagd.json`.
  - Exit 0 = OK; 1 = WARN, i.e. counter drift, which is a bug in the diagnostic. Report it; it does not gate the cvar.
  - The kit vs offd exits 0/1, read as row 2.
