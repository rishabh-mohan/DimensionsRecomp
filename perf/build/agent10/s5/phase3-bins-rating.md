# M2 S5 Phase 3 bins rating (devs5toml, natives5fsr1)

- Who/when: M10, 2026-11-25 21:07 (static; nothing launched)
- Request: Overseer 03:03Z (from M2)

## Files

| file | sha256/16 | bytes | note |
|---|---|---|---|
| build/agent2/s5/devs5toml-bin/MANIFEST.txt | 87DF5ED9E863ED77 | 2794 | = pin |
| devs5toml-bin/rexruntime.dll | 2954AF77379AD3AF | 10924032 | = b-toml/rt/link-on output |
| build/agent2/s5/natives5fsr1-bin/MANIFEST.txt | 102AAD905209F57F | 2972 | = pin |
| natives5fsr1-bin/rexruntime.dll | DF527CBC259B7700 | 10918912 | = b-fsr1/rt/link-on output |
| build/agent2/s5/rt-bin/build-s5rt.py | 4728BF5F3EC8867F | 23047 | = the tools line in both logs |
| rt-bin/BIN-PINS-devs5toml.md | 83224502 | 2432 | |
| rt-bin/BIN-PINS-natives5fsr1.md | C2597F4B | 2657 | |
| rt-bin/b-toml/build-leg.txt | D30656F5 | 22299 | RESULT PASS; stage log 54C3EA08 RESULT PASS |
| rt-bin/b-fsr1/build-leg.txt | F6CF98DD | 20880 | RESULT PASS; stage log 28C70D5B RESULT PASS |
| native-fsr1/perf-bilinear.toml | FA47B1E31787B24D | 3293 | F1 |
| native-fsr1/f2/native3_boot_check-f2.diff | F521848B1A836EEE | 5436 | F2, not applied |
| native-fsr1/f2/native3_boot_check.py | A0A8D2A7 | 25837 | patched copy |
| native-fsr1/f2/test.txt | 078D6782 | 4602 | RESULT PASS |

Base: toml-reject-native-fsr1-rating E3D652D7 (toml-reject SAFE-IF T1-T2, native-fsr1 SAFE-IF F1-F3). Sources: toml-reject/ov cvar.cpp 4C967C64, logging.cpp FBA29918 (diff 31C19232); native-fsr1/ov presenter.cpp 944B98E5 (diff 4579F090). The b-* overlay copies have the same shas.

## Verdict

**SAFE-IF P1-P5.** Provenance is clean, the pinned bins are untouched, and the F2 logic is correct.

## What I checked

1. **The bins equal base + one DLL** (my own hashes, scratch-p3/binchk.ps1).
   - devs5toml-bin: 7 files, the same file set as devfinal2-bin (4A4A13ED). 6 files equal the devfinal2 MANIFEST (exe 6C8E2811, rexgpu 9A7CC3F4, map, Tracy, ttf, wav). rexruntime 2954AF77 equals the link-on output and its own MANIFEST.
   - natives5fsr1-bin: 8 files, the same file set as nativefinal2-bin (4E5E2620). 7 files equal the base (exe 090A420B, amd_fidelityfx_dx12 12A50812, rexgpu 9A7CC3F4, ...). rexruntime DF527CBC equals the link-on output.
   - The base rexruntime is 641BD225 in both devfinal2 and nativefinal2, so the fsr1 CTL compare against devfinal2's DLL is valid.
2. **Build provenance** (logs D30656F5 / F6CF98DD).
   - The overlay starts as the a7e79c0 blob, with the snap1 copy == blob.
   - **BASE** compiles the snap1 sources in place with outputs redirected to rt-bin/b-*/rt/obj-base (recompile-commands shows the `-o` rewrite). Each object equals the snap1-sdk object except the COFF TimeDateStamp: cvar 4932B14E, logging 67130CC2, presenter EA0B4167. Those snap1-sdk objects still hash to those values, with mtimes of 11-21, so they weren't written.
   - **CTL** relink (final2's 8 rt objects + BASE) equals devfinal2 rexruntime except 1 TimeDateStamp.
   - **ON** compiles the patched overlay with -fmacro-prefix-map. It has the needles in ON and absent from devfinal2 (toml: 4, fsr1: 4), keeps 'Final defaults:{}', and has no overlay path bytes. Pch/error logs are clean, the imports equal devfinal2, the shared DLL is E3CB99CF before and after, and HOLD was checked at both steps.
   - The tools are the ones from final2 (recompile 855BCC79, relink F3C6EEAF, stage-variant D2BD1C63, verify-bins 80FF4C5F). The script header says it writes only build/agent2/s5/, which matches what I saw.
   - Method point 1 (BASE in place, not from an overlay copy) is the right way to get a byte-equal BASE. ON's different anon-namespace hashes only affect internal symbols.
3. **Exports (method point 2, a T1 deviation, accepted).**
   - NEW == REF at 10467, none added and none removed, because relink keeps snap1-sdk exports.def. FlushDeferredConfigWarnings stays internal; its only caller is logging.cpp in the same DLL.
   - The imports of devfinal2 legodimensions.exe (406) and nativefinal2 (453) are all exported by ON.
   - rexgpu-xenos is unchanged and linked against the old import lib, and since no export was removed it still resolves.
   - This is stricter than my +1 expectation, and it's fine.
4. **The pinned bins are untouched.** devfinal2 4A4A13ED, nativefinal2 4E5E2620, native4bp C5181520, devs5nops 8A8B2E77, native4b B63769FE, devoff4b DE11A914, devoff4b-cg26 917AE86E, devs5sync 2235E6DE:
   - every MANIFEST equals its pin;
   - every file size equals its MANIFEST entry;
   - rexruntime and rexgpu-xenos re-hashed against the MANIFEST;
   - the newest file in each is older than the 20:57 build start.
   M2's verify-bins in both stage logs: 0 FAIL on the new bin plus 7 pinned bins.
5. **F1:** perf-bilinear.toml differs from harness B763DABB in exactly one line (`present_effect = 'fsr'` → `'bilinear'`). natives5fsr1's MANIFEST carries the S1 note ("timing only with the bilinear perf toml, never against S5 or earlier native numbers") and the F2 note.
6. **F2 diff logic.**
   - The base is right: HEAD blob 3827c0f (hash-object, clean status), `git apply --check` 0, and the numstat of HEAD vs the patched copy is +41/-11, equal to the diff.
   - The old code read present_fsr_sharpness_reduction/max_upsampling_passes as "FFX SDK" and would wrongly WARN on a native-fsr1 bin. The new code uses present_fsr_quality_mode / present_cas_additional_sharpness as the FFX-only markers, the two FSR 1 names as native-fsr1, and present_effect alone as non-FFX.
   - I checked the overlay presenter.cpp: the FFX-only cvar definitions (L49, L70) and the only other quality_mode string (L277) sit inside `#if defined(REX_HAS_FIDELITYFX_SDK)` (L43-74, L141-291). The #else branch (L88/L93) defines only the two FSR 1 cvars.
   - I scanned the real DLLs myself, not the obj stand-in:
     - natives5fsr1 rexruntime: effect 1, FFX-only 0/0, FSR1 1/1, ffx runtime 0, so it classifies as native-fsr1;
     - devs5toml and nativefinal2: effect only, so they classify as non-FFX.
   - The order of checks is right: FFX first, then FSR1, then effect only. FSR1 with the harness toml (fsr) gives WARN; with perf-bilinear it gives INFO. An FFX runtime reference is INFO only.
   - The classifier is WARN/INFO only. The C group's gate on spatial_fsr_presented / fsr_enabled == 0 per native row is unchanged, so a misclassification can't hide FSR 1 actually being presented.
   - test.txt covers ORIG vs F2 x {harness, bilinear} on nativefinal2, the native-fsr1 obj and an FFX synthetic.

## Conditions

- **P1 (T2)** devs5toml is a test bin only and is never timed. Its first smoke must show the one `present_effect = 'fsr' ... rejected` line, no new ERROR vs devfinal2, and the wait_log patterns still matching.
- **P2 (F1)** natives5fsr1 timing only with perf-bilinear.toml FA47B1E3 pinned in the kit, never against S5 or earlier native numbers. With the harness toml (FSR 1 on) it is a separate arm: untimed, or re-baselined. Say which in the plan.
- **P3 (F2)** apply the F2 diff (Overseer's OK, since it's a DimensionsRecomp file; re-run apply --check first) before native3_boot_check runs on natives5fsr1. Until then, don't run native3_boot_check on that bin.
- **P4 (F3)** visual check on the native FSR 1 arm: spatial_fsr_presented=1 with the harness toml and 0 with perf-bilinear, no artefacts, and the overlay/settings toggles work.
- **P5** any kit that launches these bins pins MANIFEST 87DF5ED9 / 102AAD90 fail-closed, one kit at a time, interactive desktop. No builds during a timed run.

## Findings

- NIT N1: F2's `toml_fsr` parse (`split('=')[1].strip().strip("'\"")`) misses `present_effect = 'fsr'  # comment` and gives INFO instead of WARN. The harness line has no comment, and the presented-FSR gate still catches the real effect.
- NIT N2: test_f2 used the presenter obj as a stand-in DLL. My string scan of the real ON DLL closes that gap; M2's classify_real.py says the same.
- NIT N3: the build ran 20:57-21:02 (idle/BelowNormal) during the untimed manual session. That's OK only because manual is functional-only; keep builds out of timed windows (P5).
