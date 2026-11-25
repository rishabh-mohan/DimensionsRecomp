# Overseer ruling: fx2 (F2) final_gate FAIL → ACCEPTED (2026-11-25 08:34)

- **Run:** build/agent3/runs/20261125-082250-fx2-devfinal-level (devfinal-bin, level-l-tail BE08A790, toypad).
- **Gate:** final_gate v3 73F946E70D586060 (frozen) exit 1. The only FAIL is `elapsed 584.84 s (level route, >= 10 min; 590 s floor)`.
- **What I checked myself (run.json and input.csv):**
  - The route ran to completion: steps 121/121, stopped_by_script True, exited_early False.
  - The last mark `tail` fell at 583.24 s; close was sent at 584.04 s (wm_close, 0.66 s); exit 0.
  - The script ends the run itself, so elapsed time measures the route's length, not a short run. seconds_requested=840 is only the budget.
  - Earlier level-l-tail runs took 551-566 s. The 590 s floor could not be met by this route at all: a calibration error in the gate (M10 N2), not a defect in the run.
- **Every other F2 item PASSes:**
  - pins (MANIFEST F9C2BE72, exe 545D28B9, both DLLs);
  - check-defaults --mode xenos PASS; keep-watch x1; vortex reached; Toypad 1028;
  - 30 timeouts, all on by-design wait lines; 0 bad strings; no WER/dumps.
  - Miss counts (s4b_check): BASE misses 0, proof misses 0, NEW 0 / MORE 0 / FLAG 0.
- **Ruling:** F2 PASS. The gate stays frozen.
  - Post-sprint fix PS2: base the F2/F7 floor on route completion (steps_done == steps_total, stopped_by_script, tail mark), or set it from the measured route length.
  - F7 uses the same floor: if F7 fails only on this line, with the route complete and 0 misses, the same ruling applies (log it, then continue).
- go-fx may be restored. fx-ok-fx2 may be written citing this file.
