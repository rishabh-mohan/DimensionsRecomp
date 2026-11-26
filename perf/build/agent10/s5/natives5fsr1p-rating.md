# Rating: natives5fsr1p bin proposal (black-scene fix) + no-pack flag

M10, 2026-11-26 ~04:19. Read-only review: no launches, and nothing written outside build/agent10. My PE import/export check was a throwaway python -B script in build/agent10, deleted afterwards.

## Files

| file | sha256/16 | bytes |
|---|---|---|
| build/agent2/s5/black-scene-diag.md | 9007EF048746B6EA | 4931 |
| build/agent2/nativefinal2-bin/MANIFEST.txt | 4E5E2620F38F7D09 | 11418 |
| build/agent2/s5/natives5fsr1-bin/MANIFEST.txt | 102AAD905209F57F | 2972 |
| build/agent16/pack/native4bp-bin/MANIFEST.txt | C518152026695279 | 4393 |
| native4bp-bin/legodimensions.exe | FA761654D665BC92 | 316297728 |
| native4bp-bin/legodimensions.map | 493DA6DA6660CC9F | 43745602 |
| natives5fsr1-bin/rexruntime.dll | DF527CBC259B7700 | 10918912 |
| nativefinal2-bin/rexruntime.dll (= native4bp's) | 641BD22519921ACD | 10911744 |
| build/agent16/pack/NOTE-nopack-runs.md | D8395A37 | 4320 |

## Base

- Live RT kit: rt-smoke-run.ps1 02C6C88C, RUN-RT-SMOKE.cmd 34425077, rt_smoke_post.py 6034CA36, rt-mark.ps1 80589B0D, manual-capture.ps1 fix1 26894137.
- Ratings: rt-noshots-rating 7AFF48CC and rt-noshots-capture-check 9FEEFB50 (N2-N6, K1-K4).

## Verdict

**SAFE-IF P1-P6.** The diagnosis holds up on every point I could check offline. The proposed bin composes two changes that each touched different files of nativefinal2, and the PE linkage resolves.

## What I checked

- **Three-way bin compare** (all files, sha256):
  - natives5fsr1 vs nativefinal2: only rexruntime.dll (641BD225 → DF527CBC) and MANIFEST differ. The exe is the same 090A420B.
  - native4bp vs nativefinal2: only the exe (090A420B → FA761654), the map (B669786E → 493DA6DA) and MANIFEST differ. rexruntime is the same 641BD225.
  - The other 6 files are identical in all three.
  - So natives5fsr1p = native4bp with rexruntime ← DF527CBC is exactly "pack exe + FSR runtime", with nothing else mixed in.
- **What each MANIFEST says changed:**
  - natives5fsr1: "only src/ui/presenter.cpp changed", "pe-check imports NEW == REF".
  - native4bp: "CTL relink exe+map = nativefinal2 except TimeDateStamp", "pe-check ON exe vs nativefinal2 (exports/imports equal)", "mapcheck --mode same".
  - presenter.cpp is internal to rexruntime and no header changed, so I see no ABI coupling to the exe.
- **My PE check** (export/import tables parsed directly):
  - rexruntime DF527CBC exports 10467 names, the same set as 641BD225 (0 missing, 0 extra); its imports are equal too.
  - The native4bp exe imports 453 names from rexruntime.dll, and all 453 resolve in DF527CBC.
  - The native4bp exe's import table equals nativefinal2's.
- **AOT index:**
  - snap1 `lego-microcode-index.cpp` 2DB85917: ACAF01F01E1C03D2 0 hits, 75A4D1ABA62F7594 0 hits.
  - Pack `run-20261125-173813/lego-microcode-index.cpp` 401C1801: 1 and 2 hits.
  - The prefix DCD4AD8441398283 is in both (21 / 23 hits), so only the placement row is missing.
- **Logs:**
  - RT 04:03 F3A game.log BC0F007F: `Native GPU [1616ce65e973c583]` (L44); L406-409 "placement vertex shader 0xAC449538 … missing from AOT index", "unrecognized vertex shader resource 0xAC449538", and the same for pixel 0xAC448F28. 16 `unrecognized` and 16 `failed draw` lines.
  - F3B 69C72149: the same at L415-418.
  - gpman 02:42 7F76ED09 (native4bp): `Native GPU [39129c4c059be5f0]` (L46); L417/L418 "adopted vertex shader 0xAC449538, hash=0xACAF01F01E1C03D2" and "adopted pixel shader 0xAC448F28, hash=0x75A4D1ABA62F7594"; 0 `failed draw`.
- **BindShader** (snap1 shaders.cpp L764-789): on an unrecognized resource it resets the bound shader and returns false. The warning stops after 32 lines (`g_shader_warning_count < 32`), so game.log can't give the full count.
- **Kit coupling** (what the "pin-only" change really touches):
  - rt-smoke-run.ps1: L43 bin path, L46 MANIFEST pin.
  - rt_smoke_post.py: the F3A/F3B `bin=` paths (L50/L52), which the post checks against the run's `bin_dir` (L272-273).
  - RUN-RT-SMOKE.cmd: pins and comments.
  - manual-capture.ps1: the N5 time 60 s → ≥120 s.
  - The post's `ref='nativefinal2'` group (REFS L38-42: 1809-cold-nat60, 1820-nat60-r1) is a no-pack bin (S1).

## Conditions

- **P1 (stage).** `s5/natives5fsr1p-bin` must be:
  - 8 files byte-equal to native4bp-bin (exe FA761654, map 493DA6DA, and the 6 shared files);
  - rexruntime.dll = DF527CBC;
  - a MANIFEST that lists sources and copy checks, records the pe-check (imports of exe FA761654 vs exports of DF527CBC: 453/453), and says "native GPU fingerprint 39129c4c059be5f0, first boot cold";
  - verify-bins 0 FAIL on the new dir.
  - Send the MANIFEST sha. Staging must not touch native4bp-bin or natives5fsr1-bin; check their MANIFESTs are unchanged (C5181520 / 102AAD90).
- **P2 (kit diff before install).** Send me one diff of every kit file that changes:
  - the ps1 bin path and pin;
  - the post bin paths (+ S1);
  - the cmd pins;
  - manual-capture's N5 time.
  - No other change. I cross-check it before pinsonly.
- **P3 (install evidence).** pinsonly OK, tamper ALL PASS, and `RUN-RT-SMOKE.cmd dryrun noshots` DRY RUN ALL PASS with "MANIFEST … = pin" for the new bin. Send the log shas.
- **P4 (GO).**
  - Only after the manual Toypad session has ended and the desktop is free.
  - One GO, `noshots arms=F3A,F3B`, with manual-capture: N2-N6 and K1-K4 apply unchanged, and the N5 zoom is at ≥120 s (FE state 0 / intro, not the 60 s install prompt).
  - desktop-LOCAL-ONLY.png stays local.
- **P5 (pass criteria for the fix).** In each arm:
  - `Native GPU [39129c4c059be5f0]` is present;
  - `adopted vertex shader 0xAC449538` and `adopted pixel shader 0xAC448F28` appear, and neither address appears in an `unrecognized` line;
  - there are 0 `invalidated by failed draw` lines in the first 120 s;
  - N5 is ≥2% non-black at ≥120 s.
  - Not a criterion: "no `unrecognized` at all". native4bp itself logs `unrecognized vertex shader resource 0xAC44BC64` (gpman L1397+, 02:45:48).
  - If it's still black: stop. No re-run; the trace-env split needs its own rating.
- **P6 (use of results).**
  - Perf numbers from this bin compare only within this bin (F3A vs F3B), under toml-reject F1 (timing only with the bilinear perf toml).
  - Never compare against nativefinal2 / natives5fsr1 / S5 0.3 numbers.
  - Its fingerprint differs from natives5fsr1's, so the PSO caches are not shared either.

## Findings

- **S1 SHOULD.** Since the post's bin lines change anyway, switch the F3A/F3B `ref` group from nativefinal2 (no-pack, drops draws) to native4bp runs from the same matrix window: `1812-cold-n4bp60` (game.log 93E1754B) and `1825-n4bp60-r1` (5AD5426A). Otherwise "0 new error/critical lines" and "new warning kinds" compare the pack exe against a draw-dropping bin. Include it in the P2 diff.
- **S2 SHOULD.** Expect a cold first boot under 39129c4c. stall-frames (C795B708) shows an 11.97 s frame with 232 PSO creates on native4bp at 20:43. Don't read a long early frame or a late first present as a fault of this fix.
- **N1 NIT.** The diag says "No `unrecognized` at boot". Tighten that to the boot pair (P5), because of the shared warning cap and native4bp's own later 0xAC44BC64 misses.
- **No-pack flag (Overseer's ask).** I agree with M16's NOTE-nopack-runs D8395A37:
  - Any perf/A-B figure on nativefinal*, nativefinal2 or natives5fsr1 may include dropped placement draws and flatter GPU time. That covers the agent8 S5 0.3 nat60/natU rows and every RT F3A/F3B and res-scale/FSR timing.
  - The natives5fsr1 RT runs keep their functional results: present path, `spatial_fsr_presented` 1/0, config/reject checks, 0 new errors vs the nf2 refs. Their perf and visual results are void.
  - Unaffected: NATCMP's native arm (native4bp), the PSO rows and the xenos arms (no native GPU).
