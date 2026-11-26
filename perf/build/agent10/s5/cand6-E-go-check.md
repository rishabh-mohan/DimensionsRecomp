# cand6 E GO check (M3 I4 report)

- Who/when: M10, 2026-11-26 ~09:09
- Base: cand6-kit-rating-E-go.md 07629957 (I1-I4, G1-G4, E-C2..E-C6)

## Files

| File | sha256/16 |
|---|---|
| gameplay-run.ps1 (live) | 82EBF1BC (= b\) |
| RUN-GAMEPLAY.cmd (live) | B1F4BF65145298BE |
| RUN-EXPLORE.cmd (live) | 5800E81B (= b\) |
| RUN-MANUAL.cmd (live) | 9C4B18D4 (= b\) |
| logs\gameplay-dryrun-20261126-090355.txt (I3.1 cand6) | 2506562B370EA219 |
| logs\gameplay-dryrun-20261126-090529.txt (I3.2 cand5 regression) | 22A14F6C |

## Verdict

GO-OK for exactly one E run: `RUN-GAMEPLAY.cmd nativeonly cand6 zone`, GO line pin B1F4BF65..., written by M3 only after M16's e6_roles real check has finished.

## What I checked (read-only)

- Live kit hashes recomputed: all 4 = b\ of the rated cand6 draft.
- G7 unchanged: bin-native C5181520, bin-native5 787CD694, bin-native6 MANIFEST 6D841C1E / exe F5816ABE, native6pack-bin 6D841C1E / F5816ABE, native5pack-bin 787CD694, LATEST-pack AC7B9053, LATEST-bin 76D0EFB9, nf2 4E5E2620.
- Dryrun 090355: L4 CAND6 line (native6pack-bin, bin-native6, gp6-native, trace-native6, expect-fp e5c874ca2b87a59d); L7 `6D841C1E7D03B8A4 = pin`; verify-bins 0 FAIL on both bins; L15 copy 9 files, sha = source; L20 SIDECAR has `--zone --zone-delay 45`, tag gp6-native, no `--then-mark` (the only then-mark hit is L28, the `--help` flag-presence check); 0 hits for `DIAGNOSTIC|LEGO_DUMP`; 20 "expected 2: ok"; `DRY RUN ALL PASS` with the usual hidden-desktop refusal note.
- Dryrun 090529: cand5 regression ALL PASS, 20 ok.
- No lego process running; dump run B window closed (END 08:42:07).

## Conditions

- G1: run from the user's visible desktop; the hidden-desktop refusal must not be bypassed.
- G2: one attempt only. Any refusal, abort or INCONCLUSIVE comes back to me before a retry.
- G3: no kit, bin or pin edits between this check and the run; M3 rechecks the 4 live hashes in the GO line.
- G4: candidate bin only, no promotion; the post is rated against E-C2..E-C6 (07629957) with e6_roles and proof5_post `--cand-fp e5c874ca2b87a59d` against base 073150.

## Findings

None new. K6-N1, K6-N2 stay open.
