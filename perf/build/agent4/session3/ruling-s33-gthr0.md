# Ruling: s33gthr0 (and gasync/gbind) — un-normalised $S33ON allow-new
Overseer, 2026-11-25 11:02 (17:02Z). Applies ruling-r19-e to #33 row 6.

## Facts (M3, 17:01Z)
- Run build\agent3\runs\20261125-105442-s33-gthr0 (--bin build\agent2\devoff4b-s33-bin, no_wait=true, threads=0), base offsf 20261125-071741.
- Live s4b_check: `NEW 1 (+0 allowed)` -> HINT LOOK. The NEW line is the planned gate WARN:
  `[warning] [gpu] d#d#_pipeline_creation_no_wait ignored: it needs async_shader_compilation, pipeline creation threads and bindless resources`
- postcheck passes $S33ON as `d3d12_pipeline_creation_no_wait|...`. s4b_check matches normalised lines (digits -> #), so the pattern cannot match. ON rows never showed it because their line is info level (not counted).
- Read-only re-check with `d#d#_pipeline_creation_no_wait|slow frame|memexport full-buffer`: build\agent3\s4b\s33\checks-norm\s33gthr0.check-norm.txt F47C1579 -> exit 0, NEW 0 (+1 allowed, exactly the WARN), MORE 0, FLAG 0, GONE 103 (0 unexpected), BASE missed none, HINT PASS?.
- Row-6 gate rules all met: latch `INFO not-waiting 0, WARN ignored 1`; forced waits 0 (0 calls); late drops 0; dropped draws 0; no INFO line; 0 judged marks differ; errors 0; PROOF ok; kit exit 0.

## Ruling
1. For the #33 rows, $S33ON is read in normalised form: `d#d#_pipeline_creation_no_wait|slow frame|memexport full-buffer`. The checks-norm output is the row's s4b reading; the allowed NEW line is quoted verbatim.
2. **s33gthr0 = PASS?**, subject to M12 cross-gate.
3. **Pre-authorised for s33gasync and s33gbind**, ONLY IF all hold:
   - the live check's only counted NEW is exactly the WARN line above (byte-identical after normalisation), and the checks-norm re-check gives NEW 0 (+1 allowed), MORE 0, FLAG 0, 0 unexpected GONE, BASE missed none;
   - every row-6 rule holds (latch INFO 0 / WARN 1, forced waits 0, late drops 0, no INFO line, 0 judged marks differ, errors 0, PROOF ok).
   Anything else (any other NEW, an INFO line, a second WARN, a differing mark) = STOP and HOLD for me.
4. M3 may write go-s33gasync now. M12 cross-gates each row; an M12 FAIL stops the chain.
5. postcheck stays untouched mid-run. Post-sprint doc fix: S33-ROWS-PLAN / postcheck $S33ON in normalised form (joins the existing $S33ON doc-fix item).
