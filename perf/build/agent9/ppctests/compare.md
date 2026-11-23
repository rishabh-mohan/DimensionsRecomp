# ppc_tests per-test results: default vs opt vs crso vs opt9

default: 1515 tests: 1514 pass, 1 FAIL, 0 CRASH, 0 excluded
opt: 1515 tests: 1513 pass, 1 FAIL, 0 CRASH, 1 excluded
crso: 1515 tests: 1514 pass, 1 FAIL, 0 CRASH, 0 excluded
opt9: 1515 tests: 1513 pass, 1 FAIL, 0 CRASH, 1 excluded

tests whose result differs between variants: 1; not passing in every variant: 1

| test | default | opt | crso | opt9 | detail |
|---|---|---|---|---|---|
| cr_so_fold.test_call | pass | excluded | pass | excluded | opt: excluded; own run: FAIL line 4666: ctx.r3.u64 == 0x59000030 => 1207959584 (0x48000020)
==
1493172272 (0x59000030) / opt9: excluded; own run: FAIL line 4666: ctx.r3.u64 == 0x59000030 => 1207959584 (0x48000020)
==
1493172272 (0x59000030) |
| vupkd3d128.test_short2_3 | FAIL | FAIL | FAIL | FAIL | default: line 25639: ctx.v3.u32[2] == 0x7FC00000 => 1077903360 (0x403f8000)
==
2143289344 (0x7fc00000) / opt: line 25615: ctx.v3.u32[2] == 0x7FC00000 => 1077903360 (0x403f8000)
==
2143289344 (0x7fc00000) / crso: line 25639: ctx.v3.u32[2] == 0x7FC00000 => 1077903360 (0x403f8000)
==
2143289344 (0x7fc00000) / opt9: line 25615: ctx.v3.u32[2] == 0x7FC00000 => 1077903360 (0x403f8000)
==
2143289344 (0x7fc00000) |
