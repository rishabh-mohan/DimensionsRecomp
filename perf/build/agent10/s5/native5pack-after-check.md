# native5pack build: N3 after-check

M10, 2026-11-26 06:13. Read-only.

Base: s5/native5pack-p1-rating.md (843AD409, SAFE-IF N1-N6).

## Files

| File | sha256/16 |
|---|---|
| build/agent16/pack/run-20261126-060922/pack-log.txt | 6258ECD24F0103C5 |
| build/agent16/pack/binwork-20261126-060953/bin-log.txt | 9FEF87D2ACCD6683 |
| build/agent16/pack/native5pack-check-20261126-061122/native5pack-check.txt | A357A0419EC56D44 |
| build/agent16/pack/native5pack-bin/MANIFEST.txt | 787CD694F0B884D9 |
| build/agent16/pack/native5pack-bin/legodimensions.exe | 90BF6B4552217E71 |
| build/agent16/pack/native5pack-bin/legodimensions.map | DE47220B (sha8) |
| build/agent16/pack/native5pack.py (unchanged since rating) | 7DDFB8B9 (sha8) |

## Verdict

CONFIRMED. Pack, bin and check PASS as reported. My after-check is clean, so N1 is released from my side: M3's install can start.

## What I checked

- pack-log:
  - L59 `VERDICT PASS (tools: ok; check exit: 0; side effects: 0; pins changed after: 0; wall 12.9 s)`;
  - L37 `side effects: none`;
  - L19 143 staged (4 s35 + 139), 2 excluded;
  - L55 723 checks, 0 FAIL, index 19116 -> 19384 (+268);
  - L58 `LATEST-pack.txt not written`.
- bin-log:
  - L149 `VERDICT PASS (wall 68.0 s)`;
  - the four build phases each report 0 failures;
  - L147 STAGED MANIFEST 787CD694, exe 90BF6B45;
  - L148 `LATEST-bin.txt not written`, fingerprint a349d529.
- check: `RESULT: PASS`.
  - C1/C2: verify-bins 0 FAIL on the new bin, on native4bp-bin and on nativefinal2-bin.
  - C3: the pins hold (C5181520, FA761654, 4E5E2620, AC7B9053, 76D0EFB9).
  - C4: pe-check PASS against both references.
  - C5: fingerprint a349d5292f67b127 is new; the exe contains it and lacks both old fingerprints.
  - C6: same 8-file set as nf2; exe and map differ; the other 6 files are identical to nf2.
- My own re-hashes:
  - native5pack-bin MANIFEST, exe and map match the reported values.
  - LATEST-pack.txt is AC7B9053 and LATEST-bin.txt is 76D0EFB9, both still dated 2026-11-25 17:39/17:40. Not written.
  - native4bp-bin MANIFEST is C5181520, the live S1 bin-native MANIFEST is C5181520 and nativefinal2-bin MANIFEST is 4E5E2620.
- PINS_BIN (native5pack.py L76-L101): I re-hashed all 26 path pins myself: 26 ok, 0 bad. cmake is included. This closes SHOULD S1 for this run.
- snap1-on: a recursive walk finds 0 entries newer than 2026-11-25 17:00. .ninja_deps and .ninja_log are still dated 2026-11-22 22:39. Relink left it untouched.

## Conditions (still open)

- N4: no promotion. native5pack-bin is not in any kit, pin, LATEST file or default. The proof5 run needs its own rating; its kit must pin MANIFEST 787CD694. Its first boot is cold (new fingerprint a349d529), so it gives no timing data.
- N6: re-rate if native5pack-bin changes.

## Findings

None new.
