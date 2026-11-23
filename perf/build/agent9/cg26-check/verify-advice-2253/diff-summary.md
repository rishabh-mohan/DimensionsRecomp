# CG26 generated-diff summary (Agent 9 cg26_check.py, task #18)

2026-11-22 22:53:48, arm A. gen `build\agent2\cg26\DimensionsRecomp\rexlego\generated`, ref `build\agent2\snap1\DimensionsRecomp\rexlego\generated`. **RESULT: FAIL (16)**

Expected: each of the 10 TUs gains exactly one line, `\tsimde_mm_pause();`, right after each `\t// db16cyc ` line, and nothing else changes. Elsewhere only codegen.stamp, codegen.build.stamp and codegen.d may differ.

## Per TU

| TU | function | pauses expected | lines inserted | db16cyc sites without a pause | rest identical | ref lines | gen lines | ref sha256 | gen sha256 |
|---|---|---|---|---|---|---|---|---|---|
| 107 | sub_83FAF180 | 8 | 0 | 8 | yes | 39058 | 39058 | 1935C617D52623C4 | 1935C617D52623C4 |
| 116 | sub_83F99F80 | 2 | 0 | 2 | yes | 37996 | 37996 | F836F1E9401320CB | F836F1E9401320CB |
| 125 | sub_83E64900 | 1 | 0 | 1 | yes | 37375 | 37375 | 5DB107FDD8749EA5 | 5DB107FDD8749EA5 |
| 153 | sub_83EA90D0 | 1 | 0 | 1 | yes | 37986 | 37986 | 042C3006278FB300 | 042C3006278FB300 |
| 169 | sub_83E66CD8 | 1 | 0 | 1 | yes | 39003 | 39003 | F6B96AEFA2E7F25C | F6B96AEFA2E7F25C |
| 205 | sub_83FCB608 | 2 | 0 | 2 | yes | 38418 | 38418 | 22204F697ED424E9 | 22204F697ED424E9 |
| 284 | sub_83E70320 | 1 | 0 | 1 | yes | 38771 | 38771 | E078620CA3B01BE5 | E078620CA3B01BE5 |
| 304 | sub_83E96348 | 1 | 0 | 1 | yes | 61812 | 61812 | 05F5A896C33276F4 | 05F5A896C33276F4 |
| 321 | sub_83F9A5B0 | 2 | 0 | 2 | yes | 39046 | 39046 | 0B55B6E995517096 | 0B55B6E995517096 |
| 432 | sub_83E63F38 | 1 | 0 | 1 | yes | 38971 | 38971 | 83DFEFB6FC229CCF | 83DFEFB6FC229CCF |

## Per site (0 inserted pause lines in the 10 TUs; 0 pause lines in the whole tree)

| # | TU | function | label | gen line | ref line of the db16cyc comment | after a db16cyc line | expected place |
|---|---|---|---|---|---|---|---|

## Context (gen lines: 3 before each pause, the pause, 1 after)


## Other differences

- codegen.stamp is identical to the reference.
- codegen.build.stamp is identical to the reference.
- codegen.d is identical to the reference.
- None.
