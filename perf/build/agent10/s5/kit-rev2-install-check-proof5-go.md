# Kit rev 2 install/dryrun check + proof5 GO

- Who/when: M10, 2026-11-26 06:41. Read-only check against I2/I5 of `s5/kit-rev2-proof5v2-rating.md` 18509DEB; proof5 per `s5/proof5v3-rerate.md` 63A96A74.
- Base: M3's report via the Overseer, 12:39Z.

## Files (sha256/16, hashed by M10)

| File | sha256/16 |
|---|---|
| build\agent3\gameplay\gameplay-run.ps1 (live) | 691B70ADA6C55839 |
| build\agent3\gameplay\gameplay-watch.ps1 (live) | 4BE7E90E16F08AAA |
| build\agent3\gameplay\prompt_sidecar.py (live) | 1D9A6EB54B3C300A |
| build\agent3\gameplay\selftest_prompt.py (live) | A48065480D3299B5 |
| build\agent3\gameplay\RUN-EXPLORE.cmd (live) | 5B05E10FEF89EF56 |
| build\agent3\gameplay\RUN-GAMEPLAY.cmd (live) | B2B2BE248085E167 |
| build\agent3\gameplay\RUN-MANUAL.cmd (live) | 6A0AEECAF97BF643 |
| build\agent3\gameplay\gameplay-route.txt (unchanged) | 705A3A504BF6B669 |
| logs\gameplay-dryrun-20261126-063112.txt (EXPLORE zone) | 5C88D6C3C626FBE4 |
| logs\gameplay-dryrun-20261126-063246.txt (EXPLORE) | 48CFE7C94705AB7D |
| logs\gameplay-dryrun-20261126-063409.txt (GAMEPLAY nativeonly zone) | 1BE29C1108C25CCF |
| logs\gameplay-dryrun-20261126-063532.txt (MANUAL) | D2D09601438E284F |
| logs\gameplay-dryrun-20261126-063709.txt (GAMEPLAY nativeonly cand5) | 785B236FB111EC35 |
| bin-native\MANIFEST | C518152026695279 |
| bin-native5\MANIFEST | 787CD694F0B884D9 |
| drafts\zone-20261126\ZONE-DRAFT.md (rev, K-N1/K-N2) | 4A4FB245ED9FEA49 |
| drafts\zone-20261126\PROBE-RED18.md (unchanged) | 7A7A2D528803FBD6 |
| drafts\zone-20261126\zone.diff (unchanged) | 27A33CB3EA815373 |

## Verdict

- Install/pins/tamper/dryruns (I2, I4, I5): **CONFIRMED**.
- proof5 real run `RUN-GAMEPLAY.cmd nativeonly cand5`: **GO**, under G1-G7 below.

GO line:

```
RUN-GAMEPLAY.cmd|B2B2BE248085E167FD1F2131F40871F380627F4D02599B28B33059FEE54C17EF|nativeonly cand5
```

## What I checked

- I2: the 7 live files hash equal to the 7 b\ files and to the rated shas. Pins, parse and tamper results are M3's (not re-run by me: the slot was M3's and the tamper test writes to live files); my own 18509DEB scratch tests of the same ps1 sha stand.
- I4: 5 dryrun logs read. Each ends `dryrun-runs removed` and `DRY RUN ALL PASS (1 refusal note(s): a real run now would refuse)`; the one note is the hidden-desktop refusal.
  - 063112 / 063409: `ZONE: prompt sidecar --zone --zone-delay 45 on`, so Z-S1 is live; the sidecar self-test A-F PASS (0 failed) inside each dryrun.
  - 063246 / 063532: no ZONE line; MANUAL dryrun has `route none (manual: no -InputScript ...)`.
  - 063709 (cand5): `CAND5: native arm = WS\build\agent16\pack\native5pack-bin (MANIFEST 787CD694F0B884D9), copy WS\build\agent3\gameplay\bin-native5, tag gp5-native, trace trace-native5-20261126-063709, post --expect-fp a349d5292f67b127`; verify-bins PASS on both native5pack-bin and bin-native5 (8 rows, 0 FAIL); copy 9 files, all sha256 = source; run-game `-BinDir ...bin-native5 -Tag gp5-native`; no ZONE line.
  - The `FAIL native toypad tags` / `FAIL st0 clean exit` lines are inside the post wiring/self-test fixtures (post-native-wiring 5011E01B and post-selftest 4C87D20D are byte-identical across all 5 dryruns) and are expected there.
  - The 4 must-exit-2 combos leave no logs by design; my scratch run of the same ps1 (18509DEB) showed all of them exit 2 with 0 files.
- I5: bin-native MANIFEST C5181520...AA690 (unchanged); bin-native5 MANIFEST 787CD694...1446A1, 382,516,369 B; LATEST-pack AC7B9053, LATEST-bin 76D0EFB9 (unchanged). No `dryrun-runs` dir and no trace-native5 dir left behind.
- Baseline inputs for proof5_post: trace-native-20261126-054546\events.tsv F98BF46E, runs\20261126-054551-gp-native\game.log 4A53519F (as in the PLAN). C: free 152.5 GB.
- No legodimensions process at 06:40.

## Conditions (proof5 GO)

- G1 Preflight (Overseer, as announced, plus PLAN section 5): no legodimensions process; no GO.txt; no HOLD file; the waiter's last status line is END; bin-native5 MANIFEST still 787CD694; native5pack-check A357A041 RESULT PASS.
- G2 Exactly the GO line above, through the waiter on the interactive desktop. No `zone`, no other word. X1 hands off (0 keystrokes), so ctl=0. The kit's own refusals (lock held, hidden desktop) are a stop, not a retry.
- G3 Exclusive window: no build, dryrun, pack or heavy I/O by anyone until the waiter END.
- G4 Order after END: (1) M3's G5 post for the run; (2) then proof5_post with a fresh `--out`; (3) then M16's report. No proof5_post before M3's post exists.
- G5 M3's G5 post must contain the same items 1-6 as the 054546 G5 post (title gate, prompts, stop/steps/exits, zone-step outcome per pad on `game_ts`, X1/ctl, waiter END) plus, for cand5: the CAND5 line; verify-bins PASS on bin-native5 787CD694; `PASS native fingerprint: a349d5292f67b127`; the trace-native5 dir name; and a side-by-side of the pad 3 / pad 2 outcome against 054546 (P5).
- G6 proof5_post command (fill the stamps; `--out` must not exist):

```
python -B build\agent16\proof5\proof5_post.py ^
  --base-trace   build\agent3\gameplay\trace-native-20261126-054546\events.tsv ^
  --base-log     build\agent3\gameplay\runs\20261126-054551-gp-native\game.log ^
  --cand-trace   build\agent3\gameplay\trace-native5-<stamp>\events.tsv ^
  --cand-log     build\agent3\gameplay\runs\<stamp>-gp5-native\game.log ^
  --cand-post    build\agent3\gameplay\post\gameplay-<stamp>.txt ^
  --cand-runlog  build\agent3\gameplay\logs\gameplay-<stamp>.txt ^
  --cand-sidecar build\agent3\gameplay\logs\<stamp>-native.sidecar.out.txt ^
  --cand-fp a349d5292f67b127 --out build\agent16\proof5\post-<fresh stamp>
```

  The report must state the base input shas F98BF46E / 4A53519F.
- G7 After the run: bin-native MANIFEST C5181520, LATEST-pack AC7B9053, LATEST-bin 76D0EFB9 unchanged; bin-native5 787CD694. RESULT counts only under P1-P6 (same route outcome as 054546, frames within +-10% of 40881). No promotion of native5pack-bin (N4). A crash, a title-gate miss or an INCONCLUSIVE is reported as is; any re-run needs a new GO.

## Findings

- NIT C-N1: the 4 must-exit-2 dryrun combos leave no evidence file. A one-line `word combo ... exit 2` log, like the in-dryrun self-runs, would make I4 step 1 checkable after the fact.
