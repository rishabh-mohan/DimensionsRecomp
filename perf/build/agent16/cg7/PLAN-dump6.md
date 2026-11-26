# PLAN-dump6: targeted dump → pack → proof round for the late zone scenes (M16 DRAFT for M10 rating)

Status: **DRAFT v2, nothing executed** (v2 = M10 rating `build\agent10\s5\dump6-plan-rating.md` 5749F60E applied: S1-S5, N1, N2, A-C1, A-C3, A-C4, D-C2). Every step below needs its own GO. M16 writes only under `build\agent16`. M3 owns any kit change. No pin, LATEST-pack, LATEST-bin, default or promotion change (N4: promotion stays the user's Phase 4 call).
Evidence: `build\agent16\cg7\CG7-report.md` (sha in the M16 report). Source line numbers cite snap1 shaders.cpp 9567FE3F (native5pack-bin's source).

## 1. Targets

- **T-W (must, C5-S1):** 6 shaders, all of them miss on native5pack-bin with prefix 0xC77B3ABB6F87ACD9 (the zero-microcode-prefix bucket):

| Window (073150) | VS | PS | Rel. red |
|---|---|---|---|
| W1a | 0xAB80F350 | 0xAB77B580 | ≥ red + 43.5 s (done + 60.8 s) |
| W1b | 0xAB64C0E0 | 0xABB3F110 | red + 44.5 s |
| W2 | 0xA7F7A100 | 0xA7F79ED0 | red + 75.7 s → route stop |

  Guest addresses move between runs. In the new run, targets are identified **by window and stage**, not by address (070554 had the same pairs at other addresses: AB219D40/AB91ACC0, AB0FA4E0/ABB3EF40, A7F79FA0/A7F79DA0).
- **T-22 (check, not a capture target):** the 22 no-identity guests from 051154. CG7 §4 shows their scenes render with 0 misses on native5pack along the zone route (route-only). The dump run re-checks this for free: any capture **before** red + 40 s is a new target and gets listed.

## 2. Why one route dump run on native5pack-bin

- Capture (`LEGO_DUMP_MISSING_SHADERS`, shaders.cpp L146-207) fires only on an AOT-index miss. On native5pack-bin the only known misses are T-W, so the run is **targeted by construction**: no target list or new code is needed.
  - Expected: about 6 captures (fewer if W1a and W1b share a container), far below the 256-container cap.
- The scenes are reached only by the **scripted** zone route: 2/2 runs (070554, 073150). The manual dump session 051154 sat 272 s in the same idle red state and never bound them. A manual dump session is therefore not proposed.
- Bin: **native5pack-bin unchanged** (MANIFEST 787CD694, exe 90BF6B45, fp a349d529). Capture is a runtime env switch; no build is needed.

## 3. Step A: kit change (M3 owns it; M10 rates it; a dryrun slot is needed)

The kit `build\agent3\gameplay\gameplay-run.ps1` today:
- `dump` is allowed only with `manual` (L65);
- `cand5` refuses `dump` (L70).

Requested change: the minimum to allow **one** new combination, `nativeonly cand5 zone dump`.
- A1 (S1/A-C1). L65: allow `dump` only when `manual`, **or** exactly `cand5` + `zone` + `nativeonly` together. Plain `dump`, `dump zone` without cand5, `cand5 dump` without zone or nativeonly, and `dump xenosonly` stay exit 2.
- A2. L70: drop `$Dump` from the cand5 exclusion. `cand5 manual` and `cand5 explore` stay exit 2.
- A3 (N1/A-C3). The dump dir stays `<kit>\shader-dumps-native-<stamp>` (arm name `native`, L207). The run is labelled DIAGNOSTIC as a `Say` line plus the M3 post header (timing invalid, miss cache OFF); no gameplay_post change.
- A3b (A-C4, suggested). Tag `gp5d`, so the run dir is `<stamp>-gp5d-native`. dump6_post takes the run dir paths as arguments, so either tag works.
- A4. Self-test list (L259):
  - keep `cand5 manual dump nativeonly` and `dump` (both still exit 2);
  - add a positive dryrun for `nativeonly cand5 zone dump` that shows `LEGO_DUMP_MISSING_SHADERS=...shader-dumps-native-<stamp>` in the env line and leaves no dump dir (L229-230).
- A5. No change to the route, the zone sidecar args (`--zone --zone-delay 45 --led-shots`), the stop rule, or the post.

Rollback: M3 reverts the ps1 (sha before and after recorded in its kit rating).

## 4. Step B: the dump run (needs a GO; ~16 min, timed window like 073150: GO 07:31:49 → END 07:47:00)

Preflight (as usual):
1. no `legodimensions*` process;
2. `build\agent1\s5wait\status.txt` ends in END;
3. no other heavy job;
4. kit ps1 sha = the rated one;
5. native5pack-bin MANIFEST/exe shas = 787CD694 / 90BF6B45.

Then run `build\agent3\gameplay\RUN-GAMEPLAY.cmd nativeonly cand5 zone dump`, preceded by its `dryrun` per M3's usual pattern.

Expected outputs (M3 kit; read-only for M16):
- run dir `runs\<stamp>-gp5-native` with game.log;
- trace `trace-native5-<stamp>\events.tsv` (~230-300 MB);
- dump dir `shader-dumps-native-<stamp>\{placement-containers,placement-raw}` plus the 2 root boot dumps (ps-93B9F93B, vs-A58EBA12, as in every dump session);
- sidecar.out, M3 route post.

## 5. Step C: dump post (M16, static; `build\agent16\cg7\dump6_post.py`, self-tested on fixtures + 051154 + 073150 data before its rating)

| Check | Pass rule |
|---|---|
| D1 route | The proof5 v3 anchors unchanged: gate `wait line 55 current=5 pending=0 \d+ +ok after`; prompts batman/gandalf/wyldstyle each exactly 1/1 (anchored regex); 302/302 + `(last: done)`; clean exit 0; all kit exits 0. Plus zone=done in the sidecar result line and a red-18 start. ctl is reported, not gated. Fail → INCONCLUSIVE. |
| D2 reach (S4) | Stop (last trace frame) ≥ red + 80 s. W2 coverage seconds reported apart. Under 80 s → NOT-REACHED (W2 NOT-REACHED; W1 can still be COVERED in the split). No target rows at ≥ red + 40 s → INCONCLUSIVE. |
| D3 coverage | Targets = VS and PS guests of unrecognized_shader / draw_missing rows at ≥ red + 40 s, by window (W1 red+40..65 s, W2 red+65 s..stop) and stage. draw_missing carries only the VS guest. A target is matched by an identity event of the same stage at its guest, or at its backing address (game.log `placement ... backing ... missing from AOT index`, 16-line cap). physical_hash only joins identity events to each other; it never covers a target. |
| D4 files | Every identity event has `placement-containers\{vs,ps}-<container_hash:016X>.bin` with size = virtual_bytes + 4 + physical_bytes and the 4 marker bytes = virtual header bytes 8-11; sha256 listed. No xxhash module is installed, so container_hash is not recomputed (stated in the report). |
| D5 T-22 | Identity events before red + 40 s: expected 0. Any found are listed and flagged against the 22 list. |
| D6 root VS (information) | Byte-compare each new VS physical section with vs-A58EBA12 physical bytes 304-703 (400 B). Information only: the root is never packed (D-C2). |
| D7 sanity (S2, information) | Raw files are keyed by prefix hash and never overwritten (L202-204, L587-589): expect unique (stage, prefix) raw files, ≤ 1 per stage for the zero bucket, not 1 per identity. Root files: the 2 boot files; any other listed. |

RESULT:
- **COVERED**: D1-D4 pass and every VS and PS target is matched;
- **PARTIAL**: some target guests matched (or all matched but D4 failed) → plan B, R3;
- **NOT-COVERED**: no target matched;
- **NOT-REACHED**: D2 failed; **INCONCLUSIVE**: D1 failed or no target rows;
- plus a W1/W2 split line.

## 6. Step D: native6pack round (a separate P1 package for M10, as for native5pack; GO before building)

- Input: `build\agent16\dump\pack-input-zone-<stamp>` = the new placement containers from the dump (copies plus a SHA256SUMS). Never a root file (D-C2), whatever D6 says.
- Gate: the build waits until the dump post says COVERED, or PARTIAL with ≥ 1 new container.
- Combined: `build\agent16\dump\pack-input-combined6-<stamp>` = pack-input-combined FA99EB7D (141 files) + the new ones, deduped by name.
- Plan: the static `native4bp plan` step on the combined input. Report the candidate count (143 + new) and any collisions.
- Build: copies of the frozen native5pack scripts (N6, untouched), renamed native6pack. The only diffs are names and paths, and the copies fix the carried M10 NITs:
  - S1: post-bin pin re-check;
  - N1: header text;
  - N2: LF diff;
  - N3: WS path from the script location.
- Output: `build\agent16\pack\native6pack-run-<stamp>` and `build\agent16\pack\native6pack-bin`. Then verify-bins and the pe check.
- Not touched: pinned bins, `LATEST-pack.txt` AC7B9053, `LATEST-bin.txt` 76D0EFB9, defaults.
- Rollback: delete the native6pack run/bin dirs and the two pack-input dirs.

## 7. Step E: proof run (its own rating)

- The kit needs a word for the new bin (M3; e.g. `cand6`, pinned to the native6pack-bin MANIFEST, tag gp6, fp from the build).
- Run: `RUN-GAMEPLAY.cmd nativeonly cand6 zone`. **Not** with dump: timing stays valid.
- Post: proof5_post v3 (B2B920DC, unchanged), with base = 073150 (cand5 zone: trace 40060326, game.log 52574F85).
- Proof criteria (S5/E-C2..E-C4): cand misses at ≥ red + 40 s = 0; REMAIN, NEW and NEW-@ all 0; route 7/7; frames within ±10 %; the fingerprint of the new build (≠ a349d529); reach evidence with zone-done and red-18 timings within ±1 s of 073150's; per-window counts (W1, W2) listed.
- Wording rules: "FIXED" stays route-only (C5-S2), and FIXED-by-prefix is never generalized beyond the run's reach.

## 8. Risks

- R1 **Dump overhead and timing:** miss cache OFF plus the pool-copy hash check may slow the run (051154: 41.75 fps, a manual session, so the slowdown estimate is uncertain and may be overstated, N2). The run is DIAGNOSTIC and its timing void. Zone answers are LED-triggered, so they are robust to slowdown. A scripted route has never run with dump on (051154 was manual), so the first combined dryrun plus the D1 check guard this.
- R2 **W1/W2 trigger unknown:** they appeared in 2/2 scripted zone runs at similar red-relative times, but not in the manual idle red. If the dump run doesn't reach them, the result is NOT-REACHED: nothing is lost, and nothing is packed.
- R3 **Capture refusal:** validation (flags 0x102A110x, size and readability checks, L175-180) can refuse a container. Such a guest misses with no identity, like the original 22.
  - Plan B (S3, a separate rating): `placement-raw` can't help for zero-bucket targets (one raw file per (stage, prefix), never overwritten, L202-204/L587-589, so the first zero-prefix miss of the run owns the file). It needs a guarded capture log line (a code change, out of scope here, its own rating).
- R4 **Address movement:** handled by matching on window, stage, guest and game.log backing address (D3); physical_hash never covers a target.
- R5 **Zero-prefix bucket:** the miss key prefix is shared by thousands of shaders, so the prefix proves nothing. Only container_hash and physical_hash count.
- R6 **Disk/I/O:** trace ~0.3 GB plus a few KB of dumps, in M3's kit dir. Post scans run at BelowNormal after END.
- R7 **Capture cap 256:** not expected to bind (about 6); the identity count in the post shows it.
- R8 **The same game interactions as 073150** (zone ctl via the sidecar, alerts, LED shots): already rated, no new inputs.
- R9 **Scope creep:** pack/bin and proof are separate packages. No promotion, no repin.

## 9. Order and GOs

1. M10 rates this plan.
2. M3 changes the kit (A1-A5); M10 rates it; dryrun slot.
3. GO: dump run.
4. M16 writes dump6_post (self-test), M10 rates it, then the post runs.
5. P1 native6pack package; M10 rates it; GO: build.
6. M3 adds the cand6 word; M10 rates it; GO: proof run; proof5_post.
7. The user's Phase 4 visual review / promotion call.
