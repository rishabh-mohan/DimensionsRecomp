# rlwinm lowering: status (2026-11-21 19:11) - DONE, reported to Agent 9

## State
- DONE: src/codegen/builders/rotate_mask.h (std-only; classify / rotMaskExpr / lowerRlwinm / lowerRlwnm /
  lowerRlwimi; wrap masks mb>me return nullopt).
- DONE: logical.cpp: `#include "rotate_mask.h"` + flag branch at the top of build_rlwimi / build_rlwinm /
  build_rlwnm (old code untouched below; +28 lines). Syntax check: exit=0 errors=0.
- DONE: exhaustive test: 66,560 configurations, 408,680,448 evaluations, 0 mismatches; sensitivity 33792/33792
  per instruction (results.txt).
- DONE: x64 table (x64_table.md; count_x64.ps1 fixed to exclude `retq`). rlwimi keeps `(expr) | (ra.u64 & K)`.
- DONE: tests/ppc/asm/instr_rlw_lowering.s (35 tests), assembles with exit 0 (ppc/objdump.txt).
- DONE: README.md with rules, commands, numbers, x64 table, open items.
- NOT DONE BY ME (by rule): building rexglue / ppc_tests / ctest. That is Agent 9's job, with the flag default ON.

## Re-run everything (one cpu2 slot each)
powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/rlwinm/build.ps1 -Steps gen,cases,driver,run"
powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/rlwinm/build.ps1 -Steps x64,asm"
powershell -NoProfile -File bench/agent9/cpu2.ps1 -Command "powershell -NoProfile -File bench/agent9/syntax-check.ps1 src/codegen/builders/logical.cpp"
