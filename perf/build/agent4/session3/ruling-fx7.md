# Overseer ruling: fx7 (F7) final_gate FAIL + s4b LOOK → ACCEPTED (2026-11-25 08:55)

- **Run:** build/agent3/runs/20261125-084301-fx7-nativefinal-level (nativefinal-bin, level-l-tail BE08A790, toypad).
- **Finding 1, the elapsed floor:** final_gate (73F946E7, frozen) exit 1. The only FAIL is `elapsed 574.91 s (590 s floor)`. The route completed (121/121, stopped_by_script, vortex reached; 28 timeouts, all by-design). This is covered by ruling-fx2.md (the floor is a calibration error).
- **Finding 2, s4b_check HINT LOOK, 1 BASE miss:** the base is 20261122-141355-s4a-r5-off-native4. That is a menu-route run (scenario M), the only native4 base. NEW x1: `[warning] [krnl] [NtCreateFile] FAILED: path='ttappdata:\GUI3\CONFIG.XML' -> 0xc000000f`. 0 proof misses, MORE 0, FLAG 0, GONE 9 (all expected).
- **What I checked myself:** a scan of every level-route run in build/agent3/runs:
  - The line appears exactly once in 21 of 24 level runs, on both backends and every bin (devoff4/4b/4bv/cg26, devfinal, nativefinal).
  - That includes the xenos level base s4b-L0 and today's accepted fx2. The 3 runs without it are lx1, w6-gateA and s4b-07, all from 11-22; every level run since 11-23 has it once.
  - It appears 0 times in all 10 native menu runs, including the base.
  - So it is a guest file-not-found probe reached in the level, an expected title behavior. It is not a native-backend or final-defaults regression. The BASE miss comes from the route mismatch with the menu-only native base.
- **Miss counts:** BASE 1 (explained above), proof 0, FLAG 0, unexpected GONE 0, bad strings 0.
- **Ruling:** F7 PASS. With this, F1-F7 are complete (F2/F4/F7 by ruling).
  - Post-sprint fix PS3: add a native level-route s4b base, or add the CONFIG.XML probe to the expected-NEW list for level routes vs menu bases.
