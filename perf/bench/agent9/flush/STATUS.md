# flush-mode elision: STATUS (Agent 9 subagent B)

Updated 2026-11-21 21:41.

## State: DONE. SDK edits are in, waiting for Agent 9 to rebuild the tool, run T1 and regen
- **Harness:** `flush_harness.cpp` gives RESULT PASS.
  - Sites: elide 23 (0 failures), control 5 (all detected), keep 47 (all dependent).
  - 368,252,256 case evals plus exhaustive exponent-0 sweeps. Run time 644 s. Output in `results.txt`.
- **Scanner:** `scan_baseline.cpp` validation PASS.
  - The 23 builders cover 113,605 baseline instructions.
  - The flag removes 30,554 of 136,802 switch lines. Output in `baseline_scan.txt`.
- **SDK edits** (all done with edit_file, gated on `cfg.flushModeElision`):
  - `flush_mode.h` (new).
  - The `#include "flush_mode.h"` line (13) in floating_point.cpp, memory.cpp and vector.cpp.
  - 23 call sites changed to `emitFlushModeUnlessIndependent(ctx, X)`; 52 sites untouched. Checked by grep.
- **Syntax check:** floating_point.cpp, memory.cpp and vector.cpp all pass (exit 0, 0 errors) at 21:31-21:36.
- **README.md** has the full site table, the method, the baseline numbers and the non-equivalence argument.

## Commands
- `powershell -NoProfile -File bench/agent9/cpu2.ps1 -File bench/agent9/flush/build.ps1` builds and runs
  the harness and the scanner.
- Syntax check, one file per run:
  `powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/syntax-check.ps1 src/codegen/builders/<f>.cpp"`

## Open / not done
- Optional asm test `tests/ppc/asm/instr_flush_independent.s`: not written.
- Never built any SDK target. Agent 9 owns the tool rebuild, T1 and the regen.
- Pre-existing bug: vpkd3d128 type 4, shift 3 writes u16[8..9], which is out of bounds.
