# cand6 kit draft rating, install conditions and E GO

M10, 2026-11-26 09:03. A diff rating of M3's cand6 draft. Read-only: I applied the diff in my own scratch, parsed the draft and hashed the files. I ran no kit command.

Base:
- dump6-plan-rating 5749F60E (E-C1..E-C5);
- dump6-stepA-rating F7E38737, the install pattern;
- native6pack-after-check A14D36F3, the bin.

## Files

| File (WS\build\agent3\drafts\cand6-20261126) | sha256/16 |
|---|---|
| a\gameplay-run.ps1 (= live) | DE16A2D29C0F040A |
| a\RUN-GAMEPLAY.cmd (= live) | 603916BBDD6710C0 |
| a\RUN-EXPLORE.cmd (= live) | B6E8DAD4DB9E51C1 |
| a\RUN-MANUAL.cmd (= live) | 6B5C3FC6D0271D82 |
| b\gameplay-run.ps1 | 82EBF1BCE9E64346 |
| b\RUN-GAMEPLAY.cmd | B1F4BF65145298BE |
| b\RUN-EXPLORE.cmd | 5800E81B0BC73451 |
| b\RUN-MANUAL.cmd | 9C4B18D40817CBF9 |
| cand6.diff | 3C3EFE962CA2AD9B |

## Verdict

**SAFE-IF** for the install of b\ (all 4 files together) and the dryruns below. **E GO** follows once install conditions I1-I4 pass and G1-G4 hold. The E run is judged only by E-C2..E-C6 below.

## What I checked

**Diff fidelity:**
- I copied a\ and cand6.diff into my scratch and ran `git -c core.autocrlf=false apply`. The 4 results are byte-identical to b\ (82EBF1BC / B1F4BF65 / 5800E81B / 9C4B18D4).
- Line endings: the ps1 stays LF, as a\ is (0 CR). The 3 cmds stay CRLF (61/57/57 lines).
- The b\ ps1 parses with 0 errors and has no TBD or placeholder text.

**RUN-EXPLORE / RUN-MANUAL:** the only change is the GPPIN_01 line, to 82EBF1BC.

**RUN-GAMEPLAY:** 3 new `rem` lines for cand6, plus GPPIN_01 = 82EBF1BC. The pin-check code and the `%*` pass-through are unchanged.

**gameplay-run.ps1:**
- **L64:** `cand6` is added to `$known`.
- **L78-81:** `$Cand6`, which exits 2 in four cases:
  - with cand5;
  - with manual, explore or dump;
  - without nativeonly;
  - with xenosonly.

  `$Dump` is set at L70, before it is used at L80.
- **Dump gate L71 is unchanged**, so `dump` still needs manual or cand5 + zone. `nativeonly cand6 zone dump` exits 2, at L71 or L80.
- **L147-150:** the native arm becomes `build\agent16\pack\native6pack-bin`, copied to `bin-native6`. The MANIFEST pin is `6D841C1E7D03B8A40B595E6ABDBBA02ACA4F478587623F6CC530FFA5E5BFD9A6`, which equals the after-check, and `tr = native6`.
  - The generic L170-173 refuses if the MANIFEST is not the pin, and runs verify-bins on the pinned dir.
  - L209 runs verify-bins on the copy.
  - So the exe (F5816ABE) is covered through the MANIFEST rows.
- **L153:** `$nativeFp` = `e5c874ca2b87a59d` under cand6. It feeds `--expect-fp` (L289).
- **Labels:**
  - L159: the CAND6 Say line.
  - L214: tag `gp6`, so the run dir is `-gp6-native`.
  - L238/L316: trace `trace-native6-<stamp>`.
  - L371: the LATEST.txt suffix is ` cand6`.
- **No other `native5` or `gp5` text is hard-coded** outside the cand5 branches. Without cand5 or cand6 the default path is unchanged.
- **L274-276, the exit-2 list goes from 13 to 20.** The 7 new cases:
  - `cand6`;
  - `cand6 nativeonly xenosonly`;
  - `cand6 manual nativeonly`;
  - `cand6 explore nativeonly`;
  - `cand6 nativeonly zone dump`;
  - `cand6 manual dump nativeonly`;
  - `cand5 cand6 nativeonly zone`.

  Together they reach every new exit-2 branch.
- `bin-native6` does not exist yet, so the first dryrun will create it with a full copy and hash.

## Install conditions (I)

- **I1. Install like Step A.**
  - Back up the live 4 to M3 scratch; a\ is the rollback.
  - Install all 4 files at once. Live shas must then equal b\ exactly.
  - Never leave a mixed state. If any check fails, restore all 4 from a\ and report.
- **I2. Checks after install:**
  - `pincheck` exits 0 on all 3 cmds ("kit pins ok").
  - ParseFile reports 0 errors.
  - Tamper test: add 1 byte to the ps1, and all 3 cmds must exit 3. Restore it, and all 3 must exit 0. Hash after the restore: 82EBF1BC.
- **I3. Dryruns, one at a time, each with exit 0 and `DRY RUN ALL PASS`:**
  1. `dryrun nativeonly cand6 zone`. Required lines:
     - `CAND6: native arm = ...native6pack-bin (MANIFEST 6D841C1E7D03B8A4), copy ...bin-native6, tag gp6-native, trace trace-native6-<stamp>, post --expect-fp e5c874ca2b87a59d`;
     - `native pinned MANIFEST sha256 6D841C1E7D03B8A4 = pin`;
     - verify-bins PASS on native6pack-bin and on bin-native6 (8 rows, 0 FAIL);
     - the copy line shows every sha256 = source;
     - ZONE line and SIDECAR zone args (`--zone --zone-delay 45`) with no `--then-mark`;
     - all 20 word combos `(expected 2: ok)`;
     - the wiring stand-in 39129c4c note is allowed, as before.
  2. Regression: `dryrun nativeonly cand5 zone`. It must give the same CAND5 line as 081845/082021 (MANIFEST 787CD694), verify-bins PASS, and 20/20.
  3. RUN-EXPLORE and RUN-MANUAL: `pincheck` exit 0 on each. No separate dryrun is needed, because those files change only the pin line.

  `dryrun nativeonly cand6` without zone is optional; E doesn't use it. The dryruns are HEAVY I/O (pinned bin copy and hash), so run them in an exclusive window and never during another run or build.
- **I4. Report to me:**
  - the 4 live shas;
  - every dryrun log sha;
  - the grep of the CAND6 / pin / verify-bins / SIDECAR lines;
  - the 20/20 count.

  I check these before the E GO.

## E GO conditions (G)

- **G1. Preflight:**
  - live kit = b\;
  - I3 is all PASS;
  - no lego process;
  - s5wait END, with no pending GO;
  - no WINDOW-HOLD;
  - no other run, build or dryrun.
  - The user's PC window applies: free until about 11:00, with an hour's notice; the run takes about 16 min.
- **G2. G7 before must be unchanged:**
  - native6pack-bin MANIFEST 6D841C1E and exe F5816ABE;
  - bin-native C5181520;
  - bin-native5 and native5pack-bin 787CD694;
  - LATEST-pack AC7B9053, LATEST-bin 76D0EFB9;
  - nf2 4E5E2620.
- **G3. Command:** exactly `RUN-GAMEPLAY.cmd nativeonly cand6 zone`, through the waiter. No `dump`, no `allowhidden`, no manual input; the user stays hands-off.
- **G4. No automatic retry.**
  - If the gate misses, the run fails D1-type checks, or the result is INCONCLUSIVE, stop and send it to me.
  - At most one re-run, after my review.
  - The first boot is cold: PSO recipes are keyed by fp e5c874ca. That is expected, and it is not a fault.

## E post criteria (E-C2..E-C6)

Sources:
- proof5_post v3 B2B920DC with `--cand-fp e5c874ca2b87a59d`, base 073150;
- the kit's auto post;
- the M3 route post;
- e6_roles.py (info only; rated separately).

**E-C2, misses.** The base is a clean run (E-C6). E is **PASS** only if all of these hold:
- cand missing draws at ≥ red + 40 s = **0**;
- REMAIN 0, NEW 0, NEW-@ 0;
- route 7/7;
- the game.log fp line reads `e5c874ca2b87a59d`;
- the run dir MANIFEST is 6D841C1E.

proof5's own RESULT alone is not enough (S5): with a 073150 base, its PASS can stand with REMAIN 1.

Frames ratio against 073150 within ±10 %. Because of the cold first boot, a ratio outside the band is a **CHECK** that I rate. It is not an automatic FAIL. It is never a timing claim.

**E-C3, reach.** All of these are required:
- zone=done;
- red speed-18 started;
- stop ≥ red + 80 s;
- done → red within ±1 s of 073150 (+17.295 s; B had +17.185 s);
- zone/red wall times within ±1 s of 073150 relative to T0.

If reach isn't shown, the result is **INCONCLUSIVE**, not PASS. If 0 misses come with reach missing, the result is also INCONCLUSIVE.

**E-C4, per-window counts.** The post must give these counts:
- W1a, red+40..+59 s (the AB7D1200 / AB854C80 / ABB41A90 / ABA99710 analogs);
- W1b, red+59..+65 s;
- W2, ≥ red+65 s (the A7F79FD0 / A7F79DA0 analogs).

e6_roles reports each remaining or new miss by role, against the 6 073150 targets and the B analogs. A miss in the ABA99710 role (the VS with no container) is expected-risk, but it is still an **E FAIL**: report it as "known uncovered VS, no identity in B". Any miss in a covered role is a FAIL with high priority, because it would point at a pack or lookup problem.

**E-C5, wording.**
- "FIXED" is route-only: the zone route on this build.
- No generalization by prefix.
- No timing or fps claim (cold boot).
- No promotion. N4 is the user's call. The 22 no-identity guests stay open-by-identity (O4).

**E-C6, run hygiene.** All must match 073150/082648:
- title gate HIT;
- prompts 1/1 ×3, failsafe 0;
- 302/302 steps, clean exit 0;
- X1: keystrokes 0, sidecar ctl=0;
- verify-bins 0 FAIL ×2;
- fp PASS;
- no `DIAGNOSTIC` line, and game.log must NOT say "miss cache OFF". This is the normal miss cache, as in 073150.

A failure here makes the result INVALID or INCONCLUSIVE, whatever the miss counts say.

**After the run:**
- G7 again: kit files 82EBF1BC / B1F4BF65 / 5800E81B / 9C4B18D4 unchanged, and the native6pack-bin MANIFEST unchanged.
- Send me the runlog, auto post, proof5_post, e6_roles output and M3 post shas for the review.

## Findings

- **NIT K6-N1:** the exit-2 list could also cover `cand6 zone` (no nativeonly) and `nativeonly cand6 explore zone`. Both go through branches that the existing cases already test, so this is optional.
- **NIT K6-N2:** the ps1 header L14 and the cmd L11 still describe `dump` as cand5-only. That is correct, but you could add "not with cand6" to make it explicit. Optional; it would change the shas.
- No BLOCKER or SHOULD.
