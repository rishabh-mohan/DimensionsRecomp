# PLAN-proof5: miss-count proof run on the candidate native5pack-bin (M16, S5): DRAFT for a later GO

**Question:** does the 143-container pack remove the missing-shader draws it targets, and which misses remain? The remaining set is the 22 no-identity stage+guests from the 051159 dump session, including VS A7FA6EA0 (formerly A7FA6E00).

**Status:** draft. It needs these, in order:
1. ~~the native5pack-bin build to PASS~~ **DONE 06:11**: bin-log 9FEF87D2 VERDICT PASS; check A357A041 RESULT PASS;
2. an M3 kit opt-in (section 2);
3. M10's rating;
4. an Overseer slot.

**Candidate pins:**

| item | value |
|---|---|
| bin dir | `build\agent16\pack\native5pack-bin` |
| MANIFEST.txt | `787CD694F0B884D99D1D1E3C807642B33CBA22D79A8F9253C071A8898D1446A1` |
| legodimensions.exe | `90BF6B4552217E71E437D2BA7976D49EEA30AB3D8EE42B21B6A20E58A2F7EE7D` |
| fp5 (native GPU fingerprint) | `a349d5292f67b127`; the game.log line reads `Native GPU [a349d5292f67b127]` |

## 1. Design: A/B against an existing baseline

The baseline already exists: M3's scripted gameplay route on native4bp at 05:45, with the miss cache ON, no dump, native trace and a fresh user sandbox.

| item | value |
|---|---|
| run | `build\agent3\gameplay\runs\20261126-054551-gp-native` (game.log 4A53519F…, fingerprint 39129c4c059be5f0 present) |
| trace | `build\agent3\gameplay\trace-native-20261126-054546\events.tsv` F98BF46E… (268 MB) |
| baseline numbers | 40881 frames; **220710 missing draws** (VS 134404, PS 86306) = 5398.8 per 1000 frames; 46 missed guests; 64 miss-cache inserts |

The route covers the story scenes: 14 of the 16 STABLE story targets miss in it, for example VS AC44BC64 38316 draws, VS AC48E494 30604 and the portal PS AC53D0AC 12997 / AC49B8F8 9095. The other two, PS AC493354 and AC5AB10C, have few or no draws anyway.

**Candidate run:** the SAME scripted route (gameplay-route.txt 705A3A50, unattended, self-closing, ~15 min, cap 25 min), native arm only, with the bin swapped to native5pack-bin. Everything else is identical: trace on, `native_fps_limit=60`, a fresh `<run>\user`, the toypad sidecar, and no dump. A dump would turn the miss cache off and change the events.

## 2. Dependency: M3 kit opt-in (M3 writes it; M16 does not touch M3's files)

M3's `gameplay-run.ps1` hard-codes the native arm at line 112: pinned `build\agent16\pack\native4bp-bin`, MANIFEST C5181520, copy `bin-native`. Requested change: an opt-in word, e.g. `cand5`, allowed only with `nativeonly` and not with manual, explore or dump. It would:
- set the native arm's pinned dir to `build\agent16\pack\native5pack-bin`, with MANIFEST `787CD694F0B884D99D1D1E3C807642B33CBA22D79A8F9253C071A8898D1446A1`;
- use copy dir `bin-native5`, so `bin-native` (= native4bp) is not overwritten;
- use tag `gp5`, so the run dirs read `<stamp>-gp5-native`, plus the trace dir `trace-native5-<stamp>`;
- in M3's post, expect the native fingerprint a349d5292f67b127 instead of 39129c4c059be5f0, if the post checks it.

After that come a new kit pin set, M3's selftest/dryrun, and M10's re-rate of the M3 kit diff. The dryrun copies and hashes about 365 MB, so it is heavy I/O and needs a slot.

**Cold-boot note:** fp5 is a new fingerprint, and the PSO recipes are keyed by it. The baseline also ran with a fresh `<run>\user` sandbox, so both arms start from the same state. Any timing difference from the driver shader cache is irrelevant here, because this is a **functional miss-count proof**. It is not a timing claim.

## 3. Post: `build\agent16\proof5\proof5_post.py` (read-only; writes only a NEW dir under build\agent16\proof5)

```
python build\agent16\proof5\proof5_post.py ^
  --base-trace build\agent3\gameplay\trace-native-20261126-054546\events.tsv ^
  --base-log   build\agent3\gameplay\runs\20261126-054551-gp-native\game.log ^
  --cand-trace build\agent3\gameplay\trace-native5-<stamp>\events.tsv ^
  --cand-log   build\agent3\gameplay\runs\<stamp>-gp5-native\game.log ^
  --cand-fp a349d5292f67b127 --out build\agent16\proof5\post-<fresh stamp>
```

What it does:
- Runs in background mode (Idle plus low I/O) and streams both traces, about 2 s each.
- Counts frames and `draw_missing_{vertex,pixel}_shader` per (stage, guest).
- Maps each guest to its microcode prefix through `shader_miss_cache_insert` (prefix = XXH3 of the first 8 bytes; stage 6 = VS, 7 = PS). Keys are (stage, prefix), so heap guests that move between runs still match. A guest without a unique prefix is keyed by address (`@guest`).
- Compares the STABLE targets of DUMP-TARGETS-story (9C185250) by address.

Report sections:
- per-run totals;
- the STABLE table (FIXED / REMAINS / not-in-base);
- key lists: FIXED (gone in cand), REMAIN (in both, with the guest addresses of each run) and NEW (cand only).

| RESULT | condition |
|---|---|
| INVALID | fp5 not found in the cand game.log, or 39129c4c not found in the base log |
| PASS | missing draws per 1000 frames are lower, and every STABLE target that missed in base has 0 in cand |
| PASS-WITH-CHECKS | the rate is lower, but some STABLE targets remain |
| FAIL | the rate is not lower |

**Self-tests:**
- Fixture (scratch `p5_selftest.py`): PASS, PASS-WITH-CHECKS, FAIL and INVALID each came out as expected. A heap guest that moved (same prefix, new address) matched as REMAIN. The refusals for out-of-tree `--out` and for an fp equal to the base fp both exit 2. Reports are in `proof5\selftest-{pass,pwc,fail,invalid}`.
- Real data (`proof5\selftest-real-054546`, BBC9E692…): baseline vs itself gives identical totals, 0 FIXED and 0 NEW. The result is INVALID by design, since the cand log was not given.

> [!NOTE]
> Prefix keying is coarse. The 46 baseline guests fold into 16 keys: many shaders share their first 8 bytes, and 10 guests had no insert event, so they are keyed by address. A key counts as FIXED only when every guest under it is gone. The headline evidence is therefore:
> 1. total missing draws per 1000 frames;
> 2. the STABLE targets by address, which is exact;
> 3. the REMAIN/NEW guest lists. These are the misses the pack does not cover, which settles the 22 no-identity question empirically.

## 4. Expected outcome (not a claim)

- **Fixed by the pack:** the STABLE story targets, all 16 of which were DUMPED and are in the pack, and most heap story guests. Expect a large drop in missing draws per 1000 frames.
- **Remain:** guests in the 22 no-identity class. They were never dumped, so they cannot be in the pack. The top ones in 051159 were VS A7FA6EA0 (7458 draws) and PS A81DF240 (6379). In this route, their likely analogs are heap VS A7FA6480 (17056) and PS AAE1D4C0 (8579). The REMAIN list gives their addresses and prefixes in this run.
- **Next step for the remainder (not part of this proof):** a targeted dump session on native5pack-bin. Its dedup only fires for containers that are still missing, so it would capture exactly the remainder, if the hook's silent validation refusals are not the cause. If they are the cause, the dump stays empty for them, and that would be the evidence.

## 5. Safety

- **Writes:** M3's kit writes its own run, trace and copy dirs under build\agent3\gameplay. proof5_post writes only `build\agent16\proof5\post-<stamp>`.
- **Untouched:** pins, LATEST files, defaults, native4bp-bin and nativefinal2-bin.
- **Preflight before the run:**
  - no legodimensions process;
  - s5wait status ends in an END line;
  - no HOLD file;
  - native5pack_check RESULT PASS.
- **Rollback:** delete the gp5 run dir, `trace-native5-<stamp>`, `bin-native5` and `proof5\post-<stamp>`.
- None of M10's D1 strings appear in any command here.
