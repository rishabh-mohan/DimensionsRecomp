# Overseer ruling (d): #19 ref 1, r19r11 scene-id LOOK → ACCEPTED (2026-11-25 09:03)

- **Run:** build/agent3/runs/20261125-085516-r19r11-s4b11-split16 (devoff4b-bin, split 16, b-gate-menus-long 1F3559C8, 54/54).
- **Gates:** row_gate COMMON OK; r19_gate --row i --n 16 exit 0 (0 failed / 0 incomplete / 0 flags). Gated by M3, and by M12 from WS with --bin.
- **LOOK:** s4b_check reports 1 BASE miss: mark scene ids differ vs s4b01 (20261122-205356-s4b-01-off).
- **M12's read:** presses are fixed sleeps after wait_first_frame. r19r11 was one menu screen ahead at after-a1, so the 3rd A left the front end into gameplay scenes. This is non-deterministic menu drift; the same shape was seen in cg26b0 (01:51), recorded as coverage.
- **Miss counts:** proof 0, FLAG 0, NEW 0 (beyond the allowed split lines), unexpected GONE 0, errors 0.
- **Ruling:** ref 1 PASS. The scene-id difference is route coverage, not a defect.

## Standing rule (d) for the remaining #19 rows
A s4b_check LOOK whose only BASE miss is mark scene ids counts as route coverage (PASS?) when **all** of these hold:
1. The mark names and order are identical, and the route completed (steps n/n).
2. The differing ids are explained by menu drift, i.e. one or both runs left the front end (in-game ids) or sit one screen apart. M3 states which, quoting the ids.
3. NEW 0 beyond the row's --allow-new lines, MORE 0, FLAG 0, 0 proof misses, 0 unexpected GONE, [error]/[critical] 0.
4. r19_gate for the row is exit 0 with 0 failed / 0 incomplete / 0 flags.

If any of these fails, it is a HOLD for the Overseer. The row's marker may cite this file.
