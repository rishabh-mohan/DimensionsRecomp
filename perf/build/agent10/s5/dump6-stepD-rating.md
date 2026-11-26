# dump6 Step D (native6pack P1 package, static): rating

- Who/when: M10, 2026-11-26 08:36 (light reads only, during dump run B's exclusive window)
- Base: dump6-plan-rating.md 5749F60E (D-C1..D-C5); dump6-stepC-rating.md B0A9B0C6 (C-S1); dump6-B-go-check.md 517729C4

## Files (sha256/16, computed by M10)

| File | sha256/16 |
|---|---|
| pack\P1-native6pack.md | A71E4F266251D34F |
| pack\native6pack.py | 2B755B55E07C8C12 |
| pack\native6pack.ps1 | 7C97F0DE9658260D |
| pack\native6pack_check.py | A9D12AA1D7A37484 |
| pack\native6pack.diff | FF10A3C036A951CA |
| pack\stage6_inputs.py | 11E42639C5878E68 |
| pack\selftest6\selftest_stage6.py | EB58C376AC374B29 |
| pack\selftest6\selftest-stage6.log (7/7 ALL PASS) | 51BA103E222FD399 |
| frozen native5pack.py / .ps1 / _check.py | 7DDFB8B9 / 22245C44 / F57713CE (unchanged) |
| dump\pack-input-combined-20261126-053440\SHA256SUMS.txt | FA99EB7D (141 rows) |

## Verdict

SAFE-IF at package level. No BLOCKER; one SHOULD (D-S1). This rating readies D only. Each step (stage6, plan,
pack, bin, check) still needs its own GO, after B is reviewed and after the user's review (~10:00+).

## What I checked

- D-C3 diff: copied the 3 frozen files to my scratch, ran `git -c core.autocrlf=false apply native6pack.diff`
  (exit 0), and got byte-identical 2B755B55 / 7C97F0DE / A9D12AA1. The diff has 0 CR bytes. Its content is only:
  - names;
  - N1 header text;
  - N3 `$W` from `$PSScriptRoot` in the ps1;
  - S1: `before = listing(WATCH)` at L559, after the pre-build fail return and before bin_plan, in the
    non-plan branch only; `after` + diff + PINS_BIN re-check + 2 gates + raise after verify-bins, before
    STAGED / LATEST lines;
  - FP_N5 gates (fp6 != a349d529; exe lacks a349d529);
  - check-script additions (native5pack-bin in C2/C3/C4/C6, a349d529 in C5).

  The FP_N5 gates and check additions go beyond the D-C3 list, but they only tighten. Accepted.
- D-C4: no LATEST write, no pin change. The "LATEST-… not written" lines are kept. PINS_PACK/PINS_BIN, WATCH,
  HOLD, in_pack, DEFAULT_EXCLUDE, CTL gates and jobs/Idle are all outside the diff.
- S1 soundness: WATCH (20 dirs, L109-119) does not include build\agent16\pack, so binwork and native6pack-bin
  do not trip it. Listing = top-level name|size|mtime_ns. Any other agent creating or deleting an entry directly
  under a watched dir (build\agent2, build\agent9, build\agent16\dump, ...) during the bin fails the gate. That
  is a safe failure and the reason for N1.
- D-C2 stage6_inputs.py:
  - reads only `<dump>\placement-containers\{vs,ps}-<16 hex>.bin`; any other entry FAILs;
  - NEW = name not in base and bytes not in base; same name with different bytes = FAIL; 0 NEW = exit 3 with no dirs;
  - base SUMS prefix and every base file are re-hashed;
  - copies are re-verified and the dump source re-hashed after the copy;
  - existing out dirs are refused.
  The real base marks exactly the 2 root rows `(root; ...)`: ps-93B9F93B535E7CCA, vs-A58EBA123EFB541C. So
  combined6 = 139 + k, and the plan's "0 excluded" is consistent. Self-test 7/7 covers pass, dry, collision,
  nothing-new, bad-base-sums, bad-name and refuse.
- D-C1 build gate in P1 §0 matches the plan: COVERED, or PARTIAL with ≥1 NEW, plus stage6 RESULT PASS.
- Rollback (§8) deletes only M16-created dirs. The 3 existing bins stay.

## Conditions

1. Build gate = my B review verdict (with C-S1 applied), not the raw dump6_post RESULT. PARTIAL counts only if
   ≥1 of the 6 targets is genuinely covered.
2. D-S1 (SHOULD, as a condition): stage6 does not check container structure. Before the pack GO:
   - dump6_post D4 = PASS;
   - every NEW name in stage6 is the container_hash of a B identity event, listed in D4 with size OK and marker OK;
   - a NEW name not in B's identity table is a stop.

   The target cross-check in P1 §2 becomes a hard gate: list target -> NEW container, and NEW containers that
   match no target, by name.
3. stage6 runs with the default `--out-root` (build\agent16\dump). Run `--dry` first; it must list the same NEW
   set as the real run.
4. "Light" post-B steps:
   - stage6 `--dry` and `native6pack.ps1 plan` are light and may run after B's END, outside any exclusive window.
   - The check-script fixture (scratch n6check_test.py against native5pack-bin) runs verify-bins over about 4 bins
     (~1.5 GB of reads), so it is not light: it needs a free window, with no run or build in progress.
   - That scratch copy must differ from native6pack_check.py only in the NEW path and out-dir name (diff
     shown), and write only under build\agent16\pack.
   - Expected: RESULT FAIL(4) = C5 fp-not-new, C5 exe-has-a349d529, C6 exe, C6 map; exit 1.
   - Refusal test: exit 2, nothing written.
5. Build preflight as P1 §3, and runs alone (N1). Steps go in order, each on PLAN OK / VERDICT PASS. Any FAIL
   stops (N5). A bin that ends VERDICT FAIL after stage-variant (possible on an S1 gate) is deleted per §8 and
   never launched or checked.
6. The MANIFEST, exe and fp6 are reported, never written to a pin, LATEST or default. E (cand6 word + proof) is
   separate, with its own ratings (E-C1..E-C5). If coverage is only PARTIAL, expect E-C2 (0 misses ≥ red+40 s)
   to fail.

## Findings

- SHOULD D-S1: stage6 does not validate container layout (size == vb+4+pb, marker) or link NEW files to B
  identity events. Covered by Condition 2.
- NIT D-N1: stage6 `--out-root` is not confined to build\agent16. Use the default (Condition 3).
- NIT D-N2: P1 §1.3 calls the check fixture "light"; it hashes ~1.5 GB (Condition 4).
