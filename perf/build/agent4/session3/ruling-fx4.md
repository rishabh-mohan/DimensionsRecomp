# Overseer ruling: fx4 (F4) final_gate FAIL → ACCEPTED (2026-11-25 08:25)

- **Run:** build/agent3/runs/20261125-081835-fx4-devfinal-env500.
- **Pair:** 20261125-081000-fx1-devfinal-plain.
- **Gate:** final_gate v3 73F946E70D586060 (frozen) exit 1. The only FAIL is `proof lines = F1 run (61 vs 65)`, from the L330-337 compare.
- **I verified this independently** (Overseer scan of both game.log files):
  - Excluding the periodic `C1 keep-watch: N protects kept so far` lines leaves 7 proof lines in each run.
  - These are identical except for tid and timestamp: Host timer 1 ms, Final defaults (all 11 default), C1 keep-watch on, TimerQueue precise, Final defaults (GPU), first kept protect ED19F000 299892736 bytes, and GPU wait back-off ON (quantum 500 us, spin 30 us).
  - The periodic progress lines are 54 vs 58. That is a run-activity count, not config proof. The compare's `C1 keep-watch` prefix pulls them in by mistake.
  - Miss counts: 0 config-proof misses, 0 differing startup proof lines.
- **Ruling:** F4 PASS on this diagnosis. The gate stays frozen (no edit before fx7). Post-sprint gate fix: exclude `protects kept so far` from the F4 compare.
- q500 R3 NOTE stands: F4's proof that env=500 was applied is run.json env, not the log.
- go-fx may be restored. fx-ok-fx4 may be written by M3, citing this file.
