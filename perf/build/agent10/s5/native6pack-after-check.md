# native6pack build: D after-check

M10, 2026-11-26 09:00. Read-only: hashes and log reads only. I ran nobody's scripts.

Base: s5/dump6-stepD-rating.md (EEE8B6A5, SAFE-IF Cond 1-6) and s5/dump6-B-final-and-D-go.md (44372F67, order 1-7).

## Files

| File (WS\build\agent16) | sha256/16 |
|---|---|
| fixture6\fixture6-run.log | A9283E543B1A49EA |
| pack\fixture6-check-20261126-085407\native6pack-check.txt (FIXTURE) | B9255A56D67A9722 |
| pack\fixture6-check-20261126-085407\FIXTURE-LABEL.txt | 27719B558792E2AC |
| pack\run-20261126-085430\pack-log.txt | 81FD8C20B0FE7C35 |
| pack\run-20261126-085430\STAGED.tsv | 3B5E03BE465FE0D1 |
| pack\run-20261126-085430\SHA256SUMS.txt | D5EE1EC857352876 |
| pack\binwork-20261126-085606\bin-log.txt | 4AD57FDE7A536A95 |
| pack\binwork-20261126-085606\verify-bins.txt | B34D08D8713F2349 |
| pack\native6pack-check-20261126-085733\native6pack-check.txt | 2F4C4723DB848B09 |
| pack\native6pack-bin\MANIFEST.txt | 6D841C1E7D03B8A4 |
| pack\native6pack-bin\legodimensions.exe | F5816ABE79CAD936 |
| pack\native6pack-bin\legodimensions.map | 21ACBA162501DE3B |
| pack\native6pack.py / .ps1 / _check.py (unchanged since rating) | 2B755B55 / 7C97F0DE / A9D12AA1 |

## Verdict

**CONFIRMED.** Steps 1-7 PASS as reported, and my own re-hashes agree. native6pack-bin (MANIFEST 6D841C1E, fp e5c874ca2b87a59d) is a valid **candidate bin**. It may be pinned by a rated cand6 kit for the E run. It is not promoted.

## What I checked

**Fixture (Cond 4):**
- Report B9255A56: `RESULT: FAIL (4)`, which is exactly the expected set:
  - C5 "fingerprint a349d529 is new";
  - C5 "exe lacks a349d529";
  - C6 exe;
  - C6 map.
- Every other line is PASS.
- FIXTURE-LABEL.txt says "not a native6pack check", with stand-in native5pack-bin and script C32B5392. The run log tail shows the same report sha.

**Pack (pack-log 81FD8C20):**
- L17: staged 148 (4 s35 + 144), 0 excluded.
- L28/L53: 746/748 checks, 0 FAIL, index 19116 -> 19394 (+278); runtime cache 148 entries.
- L35 `side effects: none`; side-effects.txt says the top level of all 20 watched dirs is unchanged.
- L56 `LATEST-pack.txt not written`.
- L57 `VERDICT PASS (... side effects: 0; pins changed after: 0; wall 13.2 s)`.
- STAGED.tsv has 148 rows. All 5 NEW containers are present with the B shas (98E17056, 18439A7B, CFD5F3E4, 6D75E47B, 4A14CC86) and source pack-input-zone-084753. The 2 boot root files are absent (D-C2).

**Bin (bin-log 4AD57FDE):**
- Fingerprints:
  - L53-55: CTL fp 1616ce65e973c583, cmake == python over 271 inputs; header and txt identical to final2.
  - L103-106: ON fp e5c874ca2b87a59d, cmake == python; it differs from 1616ce65 and from a349d529.
- Exe content:
  - L132-134: the exe contains e5c874ca and lacks both old fps.
  - L135: no overlay path bytes.
- L140 pe-check PASS; L143 mapcheck --mode same PASS.
- L149-150: side effects none (20 watched dirs).
- PIN lines: 54 in total, all ok/logd, 0 bad. L178: pins unchanged after stage + verify-bins.
- L179-181: STAGED MANIFEST 6D841C1E, exe F5816ABE, map 21ACBA16; `LATEST-bin.txt not written`; `VERDICT PASS (wall 64.4 s)`.
- verify-bins.txt: 8 rows, 8 files, 0 FAIL, MANIFEST 6D841C1E.

**Check (2F4C4723), `RESULT: PASS`:**
- C1: verify-bins on the new bin, 0 FAIL.
- C2: verify-bins on native4bp, nf2 and native5pack, 0 FAIL.
- C3: pins hold (C5181520, FA761654, 787CD694, 90BF6B45, 4E5E2620, AC7B9053, 76D0EFB9).
- C4: pe-check PASS against all 3 references.
- C5: e5c874ca is new; the exe contains it and lacks 1616ce65, 39129c4c and a349d529.
- C6: same 8-file set as nf2. exe and map differ from nf2, native4bp and native5pack; the other 6 files are identical to nf2.

**My own re-hashes:**
- native6pack-bin: all 8 files match the MANIFEST rows and the C6 HASH lines.
- MANIFEST header: base nf2 4E5E2620, pack run-085430, fp e5c874ca. It also states "native-pso-recipes.bin / seed are keyed by it, first boot is cold".

**G7 after, all unchanged:**
- bin-native MANIFEST C5181520; bin-native5 MANIFEST 787CD694.
- native5pack-bin MANIFEST 787CD694 and exe 90BF6B45.
- LATEST-pack AC7B9053 and LATEST-bin 76D0EFB9, both still dated 2026-11-25 17:40/17:39.
- Kit: ps1 DE16A2D2, RUN-GAMEPLAY 603916BB, EXPLORE B6E8DAD4, MANUAL 6B5C3FC6.

**Side effects:**
- build\agent2\snap1-on: 0 entries newer than 08:50.
- No lego process. The last s5wait line is still END 08:42:07.

## Conditions (still open)

- **N4: no promotion.** native6pack-bin is not in any kit, pin, LATEST file or default. Promotion is the user's call.
- **E-C1:** the cand6 kit must pin MANIFEST 6D841C1E, exe F5816ABE and `--expect-fp e5c874ca2b87a59d`. It needs its own rating and dryruns before any GO.
- **The first E boot is cold**, because the PSO recipes are keyed by the new fp. E judges misses, not timing (E-C2..C4).
- **E-C2 is at risk:** ABA99710 has no container. A miss that remains means E FAIL, and it must be reported by role.
- **Re-rate** if native6pack-bin changes.

## Findings

None new. NITs D-N1..D-N3 stay open, and none blocks E.
