# dump6 - B final (a) and D build GO conditions (native6pack)

M10, 2026-11-26 08:53. Follows dump6-B-review 2090CDB5 and dump6-stepD-rating EEE8B6A5. Read-only checks, no runs.

## Base

| File (WS) | sha256/16 |
|---|---|
| build\agent3\gameplay\post\gameplay-route-20261126-082648.md (M3 DIAGNOSTIC post) | 18913AF101DDF6B8 |
| build\agent3\gameplay\post\dump-SHA256SUMS-20261126-082648.txt (9 rows) | 074295AF23B8E3E9 |
| build\agent16\dump\stage6-20261126-084753.txt | CF13CF8BB6124560 |
| build\agent16\dump\pack-input-combined6-20261126-084753\SHA256SUMS.txt (144 files + SUMS) | 02E536923B153AF5 |
| build\agent16\pack\plan-20261126-084800.txt | 338D213CB70C14A1 |
| build\agent16\pack\native6pack.py / .ps1 | 2B755B55E07C8C12 / 7C97F0DE9658260D |
| build\agent16\pack\native6pack_check.py | A9D12AA1D7A37484 |
| build\agent16\pack\stage6_inputs.py | 11E42639C5878E68 |
| build\agent16\fixture6\native6pack_check_fixture.py | C32B53923FFAC3EF |
| build\agent16\fixture6\fixture6.diff | E1EECDDA78C1AF7F |

All shas computed by me; the post, sums, stage6 report and plan match the Overseer's relay.

## Verdict

- **(a) B run 082648: VALID (DIAGNOSTIC only).** The "PENDING M3 post" part of 2090CDB5 is cleared.
- **Real stage6 and plan: CONFIRMED.**
- **D build (fixture -> pack -> bin -> check into a new native6pack-bin): GO-OK now, as a candidate bin only**, under the conditions and order below. No promotion, no LATEST, no pin, no launch.

## What I checked

**M3 post 18913AF1:**
- Header and body say DIAGNOSTIC ONLY: timing invalid, no proof5 RESULT, no promotion, never a proof base. Proof base stays 064143.
- B-C4: L3 DIAGNOSTIC line, L4 ZONE args, L5 CAND5 pin 787CD694, verify-bins 0 FAIL (x2), L58 fp a349d529 PASS, game.log L122 "miss cache OFF". The SIDECAR-line gap is the known one; the sidecar.out header shows the zone args.
- Gate HIT on try 1 (L55 current=5). Prompts batman/gandalf/wyldstyle 1/1, failsafe 0. Steps 302/302, exit 0.
- zone=done, red speed-18, stop red+104.7 s (>= red+80 s). These match my scan in 2090CDB5.
- X1: keystrokes 0, sidecar ctl=0. The 9 post-boot toypad actions are all the sidecar's own (3 prompts + 6 zone).
- B-C7 / G7 at 08:46 unchanged: C5181520, 787CD694 x2, exe 90BF6B45, AC7B9053, 76D0EFB9. Kit files = the Step A install.

**dump-SHA256SUMS 074295AF:** 9 rows = 2 roots + 5 containers + 2 raw. The 5 container shas (98E17056, 18439A7B, CFD5F3E4, 6D75E47B, 4A14CC86) equal my D4 list and the stage6 NEW list.

**stage6 CF13CF8B:**
- Pinned script 11E42639. Base 141 files, SUMS FA99EB7D. The 2 root files are dropped (D-C2).
- 5 NEW, 0 already in base, 0 renamed duplicates; names, shas and sizes (404-728 B) as above.
- combined6 has 144 files; SUMS 02E53692 (re-hashed live). `RESULT PASS`.
- D-S1 holds: every NEW name is a B identity container.

**plan 338D213C:**
- Pinned native6pack.py 2B755B55; all PINs ok or logd; `PLAN OK (bad pins 0, input failures 0, clang++ found)`.
- L45: 148 selected (4 s35 pinned + 144 from combined6-084753), 0 excluded, 0 failures.
- Staged bin target `build\agent16\pack\native6pack-bin`; base nativefinal2-bin; no LATEST-pack.txt.
- `native6pack-bin` does not exist yet. No `native6pack-check-*` or `fixture6-check-*` dirs yet.

**Fixture copy (Stage D Cond 4):** Compare-Object between native6pack_check.py A9D12AA1 and the fixture C32B5392 gives exactly 2 lines: `NEW = native5pack-bin` and the out-dir prefix `fixture6-check-`. This matches fixture6.diff. Its W resolves to WS (same depth as pack\), and it writes only under pack\fixture6-check-<stamp>.

**Live state at 08:52:** no lego process; s5wait last line is END 08:42:07 exit=0; native4bp-bin and nativefinal2-bin exist.

## Conditions and order

The user's limits: candidate bin only, no promotion without the user. The PC is free until about 11:00, with about an hour's notice. The whole chain is expected to take about 10-15 min (native5pack reference: pack 12.9 s, bin 68.0 s, plus about 1.5 GB of verify reads per check).

1. **Preflight (P1 §3), right before step 2:**
   - no lego process;
   - s5wait last line is END, no new GO;
   - no WINDOW-HOLD;
   - `native6pack-bin` is absent;
   - nothing else runs or builds. Tell every agent to stop writing in the native6pack WATCH dirs (build\agent2, build\agent9, build\agent16\dump, the snap1 dirs, and so on) until step 6 ends, or S1 fails.
2. **Refusal test:** `python -B native6pack_check.py` with native6pack-bin still absent. It must print `REFUSED: ... missing`, exit 2, and write nothing.
3. **Fixture:** `python -B build\agent16\fixture6\native6pack_check_fixture.py`. Expect exactly FAIL(4) and exit 1:
   - C5 fp;
   - C5 exe-has-a349d529;
   - C6 exe;
   - C6 map.

   Any other set is a STOP. Keep the `fixture6-check-<stamp>` dir, labelled as the fixture. It is never a check result.
4. **Pack:** `native6pack pack --input build\agent16\dump\pack-input-combined6-20261126-084753`. Expect VERDICT PASS with:
   - 148 STAGED rows;
   - side-effects "none";
   - pins unchanged;
   - "LATEST-pack.txt not written";
   - index count > 19384.

   Report the run dir, SHA256SUMS and the log sha.
5. **Bin:** `native6pack bin --pack-run run-<S1> --bin-out native6pack-bin`. Expect VERDICT PASS with:
   - every CTL/ON gate PASS;
   - FP_N5 gates PASS;
   - verify-bins 0 FAIL;
   - PINS_BIN 0 bad;
   - S1 side-effects none;
   - "LATEST-bin.txt not written".

   Report the MANIFEST, the exe and fp6.
6. **Check:** `python -B native6pack_check.py`. Expect `RESULT PASS` (C1-C6), in a new `native6pack-check-<stamp>` dir.
7. **G7 after:** these must be unchanged:
   - bin-native MANIFEST C5181520;
   - bin-native5 MANIFEST and native5pack-bin MANIFEST 787CD694;
   - native5pack-bin exe 90BF6B45;
   - LATEST-pack AC7B9053;
   - LATEST-bin 76D0EFB9;
   - nativefinal2-bin MANIFEST 4E5E2620;
   - kit files DE16A2D2 / 603916BB / B6E8DAD4 / 6B5C3FC6.

**Rules for the whole chain:**
- Run each step alone and in order. Stop at the first FAIL or unexpected result: no retry, no edits, and report it to the Overseer.
- A bin that ends VERDICT FAIL after staging is deleted per P1 §8 and never launched.
- If the user messages, finish the current step only, then stop.
- No launch of native6pack-bin, no kit pin and no LATEST until I have done the after-check and rated E (`cand6 zone`, E-C1..C5).
- Promotion of any bin stays the user's call (N4).
- Send me every step's log/report sha for the after-check. Expect E-C2 to be at risk: coverage is PARTIAL (ABA99710 has no container).

## Findings

- **NIT D-N3:** the fixture dir is build\agent16\fixture6 (outside pack\), while its output goes to pack\fixture6-check-*. That is harmless, since it is not watched by S1 and not read by the pack. Keep it as is; just don't move it into a WATCH dir.
- The D-N1 and D-N2 NITs from EEE8B6A5 stay open. Neither blocks the build.
