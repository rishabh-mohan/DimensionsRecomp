# CG26 generated-diff summary (Agent 9 cg26_check.py, task #18)

2026-11-22 22:32:02, arm A. gen `build\agent9\cg26-check\mock\rexlego\generated`, ref `build\agent2\snap1\DimensionsRecomp\rexlego\generated`. **RESULT: FAIL (3)**

Expected: each of the 10 TUs gains exactly one line, `\tsimde_mm_pause();`, right after each `\t// db16cyc ` line, and nothing else changes. Elsewhere only codegen.stamp, codegen.build.stamp and codegen.d may differ.

## Per TU

| TU | function | pauses expected | lines inserted | db16cyc sites without a pause | rest identical | ref lines | gen lines | ref sha256 | gen sha256 |
|---|---|---|---|---|---|---|---|---|---|
| 107 | sub_83FAF180 | 8 | 8 | 0 | yes | 39058 | 39066 | 1935C617D52623C4 | 1245188F16F9C89E |
| 116 | sub_83F99F80 | 2 | 2 | 0 | yes | 37996 | 37998 | F836F1E9401320CB | D3A7D20F9FF18D9F |
| 125 | sub_83E64900 | 1 | 1 | 1 | yes | 37375 | 37376 | 5DB107FDD8749EA5 | F42B76D1458D58BB |
| 153 | sub_83EA90D0 | 1 | 1 | 0 | yes | 37986 | 37987 | 042C3006278FB300 | 470A3AF1DE47DAD1 |
| 169 | sub_83E66CD8 | 1 | 1 | 0 | yes | 39003 | 39004 | F6B96AEFA2E7F25C | AAAE9178569FA12F |
| 205 | sub_83FCB608 | 2 | 2 | 0 | yes | 38418 | 38420 | 22204F697ED424E9 | AD51029B69408BC1 |
| 284 | sub_83E70320 | 1 | 1 | 0 | yes | 38771 | 38772 | E078620CA3B01BE5 | 632685E3C7060216 |
| 304 | sub_83E96348 | 1 | 1 | 0 | yes | 61812 | 61813 | 05F5A896C33276F4 | 6E8102D39DAC3726 |
| 321 | sub_83F9A5B0 | 2 | 2 | 0 | yes | 39046 | 39048 | 0B55B6E995517096 | 3754AD8890625636 |
| 432 | sub_83E63F38 | 1 | 1 | 0 | yes | 38971 | 38972 | 83DFEFB6FC229CCF | FCADF61F01C2D1C3 |

## Per site (20 inserted pause lines in the 10 TUs; 20 pause lines in the whole tree)

| # | TU | function | label | gen line | ref line of the db16cyc comment | after a db16cyc line | expected place |
|---|---|---|---|---|---|---|---|
| 1 | 107 | sub_83FAF180 | loc_83FAF1A0 | 36800 | 36799 | yes | yes |
| 2 | 107 | sub_83FAF180 | loc_83FAF1A0 | 36802 | 36800 | yes | yes |
| 3 | 107 | sub_83FAF180 | loc_83FAF1A0 | 36804 | 36801 | yes | yes |
| 4 | 107 | sub_83FAF180 | loc_83FAF1A0 | 36806 | 36802 | yes | yes |
| 5 | 107 | sub_83FAF180 | loc_83FAF1A0 | 36808 | 36803 | yes | yes |
| 6 | 107 | sub_83FAF180 | loc_83FAF1A0 | 36810 | 36804 | yes | yes |
| 7 | 107 | sub_83FAF180 | loc_83FAF1A0 | 36812 | 36805 | yes | yes |
| 8 | 107 | sub_83FAF180 | loc_83FAF1A0 | 36814 | 36806 | yes | yes |
| 9 | 116 | sub_83F99F80 | loc_83F9A194 | 36289 | 36288 | yes | yes |
| 10 | 116 | sub_83F99F80 | loc_83F9A240 | 36404 | 36402 | yes | yes |
| 11 | 125 | sub_83E64900 | loc_83E64978 | 33896 | 33895 | **NO** | yes |
| 12 | 153 | sub_83EA90D0 | loc_83EA9140 | 35180 | 35179 | yes | yes |
| 13 | 169 | sub_83E66CD8 | loc_83E66D48 | 34893 | 34892 | yes | yes |
| 14 | 205 | sub_83FCB608 | loc_83FCB624 | 36914 | 36913 | yes | yes |
| 15 | 205 | sub_83FCB608 | loc_83FCB854 | 37221 | 37219 | yes | yes |
| 16 | 284 | sub_83E70320 | loc_83E70390 | 35079 | 35078 | yes | yes |
| 17 | 304 | sub_83E96348 | loc_83E9640C | 34384 | 34383 | yes | yes |
| 18 | 321 | sub_83F9A5B0 | loc_83F9A614 | 36202 | 36201 | yes | yes |
| 19 | 321 | sub_83F9A5B0 | loc_83F9A694 | 36288 | 36286 | yes | yes |
| 20 | 432 | sub_83E63F38 | loc_83E63F94 | 35010 | 35009 | yes | yes |

## Context (gen lines: 3 before each pause, the pause, 1 after)

TU107 (sub_83FAF180):
```
-- gen line 36800, loc_83FAF1A0
	ctx.ctr.u64 = ctx.r11.u64;
loc_83FAF1A0:
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
-- gen line 36802, loc_83FAF1A0
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
-- gen line 36804, loc_83FAF1A0
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
-- gen line 36806, loc_83FAF1A0
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
-- gen line 36808, loc_83FAF1A0
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
-- gen line 36810, loc_83FAF1A0
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
-- gen line 36812, loc_83FAF1A0
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
-- gen line 36814, loc_83FAF1A0
	// db16cyc 
	simde_mm_pause();
	// db16cyc 
	simde_mm_pause();
	// bdnz 0x83faf1a0
```
TU116 (sub_83F99F80):
```
-- gen line 36289, loc_83F9A194
	ctx.r11.u64 = ctx.r30.u64;
loc_83F9A194:
	// db16cyc 
	simde_mm_pause();
	// addic. r11,r11,-1
-- gen line 36404, loc_83F9A240
	ctx.r11.u64 = ctx.r30.u64;
loc_83F9A240:
	// db16cyc 
	simde_mm_pause();
	// addic. r11,r11,-1
```
TU125 (sub_83E64900):
```
-- gen line 33896, loc_83E64978
	if (!ctx.cr6.eq) goto loc_83E64990;
	// db16cyc 
	// b 0x83e6492c
	simde_mm_pause();
	goto loc_83E6492C;
```
TU153 (sub_83EA90D0):
```
-- gen line 35180, loc_83EA9140
	// bne cr6,0x83ea9158
	if (!ctx.cr6.eq) goto loc_83EA9158;
	// db16cyc 
	simde_mm_pause();
	// b 0x83ea90f4
```
TU169 (sub_83E66CD8):
```
-- gen line 34893, loc_83E66D48
	// bne cr6,0x83e66d60
	if (!ctx.cr6.eq) goto loc_83E66D60;
	// db16cyc 
	simde_mm_pause();
	// b 0x83e66cfc
```
TU205 (sub_83FCB608):
```
-- gen line 36914, loc_83FCB624
	// bne 0x83fcb648
	if (!ctx.cr0.eq) goto loc_83FCB648;
	// db16cyc 
	simde_mm_pause();
loc_83FCB63C:
-- gen line 37221, loc_83FCB854
	goto loc_83FCB858;
loc_83FCB854:
	// db16cyc 
	simde_mm_pause();
loc_83FCB858:
```
TU284 (sub_83E70320):
```
-- gen line 35079, loc_83E70390
	// bne cr6,0x83e703a8
	if (!ctx.cr6.eq) goto loc_83E703A8;
	// db16cyc 
	simde_mm_pause();
	// b 0x83e70344
```
TU304 (sub_83E96348):
```
-- gen line 34384, loc_83E9640C
	// bne cr6,0x83e96424
	if (!ctx.cr6.eq) goto loc_83E96424;
	// db16cyc 
	simde_mm_pause();
	// b 0x83e963c0
```
TU321 (sub_83F9A5B0):
```
-- gen line 36202, loc_83F9A614
	ctx.r11.u64 = ctx.r30.u64;
loc_83F9A614:
	// db16cyc 
	simde_mm_pause();
	// addic. r11,r11,-1
-- gen line 36288, loc_83F9A694
	ctx.r11.u64 = ctx.r30.u64;
loc_83F9A694:
	// db16cyc 
	simde_mm_pause();
	// addic. r11,r11,-1
```
TU432 (sub_83E63F38):
```
-- gen line 35010, loc_83E63F94
	// bne cr6,0x83e63fac
	if (!ctx.cr6.eq) goto loc_83E63FAC;
	// db16cyc 
	simde_mm_pause();
	// b 0x83e63f48
```

## Other differences

- codegen.stamp differs: fingerprint 58c23c7e7cdb95afd17a35c5148cb3e9 -> b3bccb3c76fc31afbec121ecee459527.
- codegen.build.stamp differs: fingerprint 58c23c7e7cdb95afd17a35c5148cb3e9 -> b3bccb3c76fc31afbec121ecee459527.
- codegen.d differs (it names the regen tree and toml).
- None.
