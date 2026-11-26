# PLAN-dump6 rating + CG7 report cross-check

- Who/when: M10, 2026-11-26 08:15. Read-only (no runs, no images viewed).
- Base: `s5/cand5zone-result-review.md` 39F51CF5 (C5-S1, C5-S2); `s5/z2-review-cand5zone-go.md` BB58D08E (CG1-CG8); `s5/proof5v3-rerate.md` 63A96A74; the native5pack after-check 2FF1CCE5 (N4/N6).

## Files (sha256/16, hashed by M10)

| File | sha256/16 |
|---|---|
| build\agent16\cg7\PLAN-dump6.md | FAB4A6B3940A45A5 |
| build\agent16\cg7\CG7-report.md | AF18189D8808A312 |
| build\agent16\cg7\data\cg7_scan.py / cg7_win.py | 2E5336DF35BD65B2 / ABED9380249CAF99 |
| build\agent16\proof5\post-20261126-073150-p0info\proof5_post.txt | 11149BB0ED3B7DBF |
| build\agent16\proof5\proof5_post.py (v3) | B2B920DC... |
| build\agent3\gameplay\gameplay-run.ps1 (live) | 691B70ADA6C55839 |
| build\agent2\snap1\...\gpu_native\shaders.cpp (the source native5pack-bin was built from: snap1-on objects) | 9567FE3F3B63637D |
| DimensionsRecomp\...\gpu_native\shaders.cpp (main tree, the one the report cites by line) | 4B8250E976A38401 |
| shader_archive.cpp (snap1 = main) | 1C5B1767B8F6871D |
| build\agent3\gameplay\shader-dumps-native-20261126-051154\vs-A58EBA123EFB541C.bin | FD947EBF69C161EE |

## Verdict

| Step | Rating | Gate |
|---|---|---|
| A kit change `nativeonly cand5 zone dump` | **SAFE-IF** A-C1..A-C6 | M3 edit -> M10 rates the diff -> install (pins/tamper as I2) -> dryruns (A-C5) |
| B one DIAGNOSTIC dump run | **SAFE-IF** B-C1..B-C7 | only after A installed + dryrun ALL PASS **and** C self-test PASS + rated |
| C dump6_post.py | **SAFE-IF** C-C1..C-C5 | self-test, then M10 rating; may be written in parallel with A |
| D native6pack | **SAFE-IF at plan level** D-C1..D-C5 | its own P1 package and rating; build GO only after the B post says COVERED or PARTIAL |
| E cand6 zone proof | **SAFE-IF at plan level** E-C1..E-C5 | its own kit-word rating + dryrun + GO |

Report claims: zero-bucket CONFIRMED; "not in any packed dump" CONFIRMED-WITH-CHANGES; O2 plausible, open; O3 CONFIRMED-WITH-CHANGES; O4 CONFIRMED-WITH-CHANGES (wording). Details below.

Time budget (now ~08:15, PC wanted ~10:00): **A, C, B and the B post fit** (estimate: A + rating + dryruns ~08:50, C + rating ~08:55 in parallel, B 16 min, post + review ~09:35). **Latest GO for B: 09:30** (END by ~09:46). **D build and E do not fit**: D needs a new P1 package rating and E a kit-word rating, dryrun and a 16 min run. M16 may prepare the D package statically (copies + diff under build\agent16, no build) during the window; D build and E go after the user's slot.

## What I checked

### Code path (snap1 shaders.cpp 9567FE3F, the native5pack source)
- `CaptureMissingPlacementShader` L146-207 is called only in the placement miss branch (L503-505, after `FindShaderByMicrocode` returns null). Enabled by `LEGO_DUMP_MISSING_SHADERS` (L148-156). Validation L175-180; dedup by (container hash, stage) and the 256 cap L190-193; the identity event L197-201 is emitted only on the first insert of a container. So the plan's "targeted by construction" holds: on native5pack-bin only misses are captured.
- `ShaderMissCacheEnabled` L222-225: dump ON forces the miss cache OFF, so a dump run has **no `shader_miss_cache_insert` events** (dump6_post must not rely on them) and every miss bind takes the full lookup path.
- `DumpMissingShader` L562-598 writes `<root>\<category>\{vs,ps}-<hash>.bin` and **returns early if the file exists**. The `placement-raw` dump is keyed by `XXH3_64bits(microcode, 8)` (L202-204), i.e. by the prefix hash. All 6 targets are in the zero bucket, so **at most one raw file per stage** is written for all of them (the first one bound). This affects D7 and R3 (findings S2, S3).
- Root dumps (the 2 boot files) come from `CreateShaderResource` -> `DumpMissingShader(container, ..., hash)` (snap1 L721), keyed by the full-container hash, with no marker. That is a different path from placement capture.
- shader_archive.cpp L341: "Thousands of physical shader sections share eight zero prefix bytes." (snap1 = main, 1C5B1767.)

### Kit (gameplay-run.ps1 691B70AD)
- L65 `dump` only with `manual`; L66 not with `xenosonly`; L70 `cand5` refuses `manual`/`explore`/`dump`; L71 `cand5` needs `nativeonly`.
- L206-207: with `$Dump` the env becomes `LEGO_NATIVE_TRACE_DIR=...;LEGO_DUMP_MISSING_SHADERS=<kit>\shader-dumps-<arm>-<stamp>`. The arm name stays `native` under cand5 (L133), so the dir is `shader-dumps-native-<stamp>` as A3 says.
- L229-230: the dryrun fails if it left a dump dir. L259: the must-exit-2 list today: `zone manual`, `cand5 manual nativeonly`, `cand5 explore nativeonly`, `cand5 manual dump nativeonly`, `cand5`, `cand5 nativeonly xenosonly`, `dump`, `bogusword`.
- A1 as written ("allow dump when manual or (cand5 and nativeonly)") would also allow `nativeonly cand5 dump` **without zone**. That is not "exactly one new combination" (A-C1).
- A3 says the post header gets a DIAGNOSTIC label; A5 says no change to the post. These conflict (A-C3).
- The RUN-GAMEPLAY.cmd pins the ps1 sha, so a ps1 change gives a new .cmd sha and a new GO line.

### Data I reproduced
- vs-A58EBA12 root dump: 704 B; header `10 2A 11 11`, virtual_size 0x130 = 304, physical_size 0x190 = 400; bytes 304-327 are all zero. So the physical section starts with >= 16 zero bytes (zero bucket) and is 400 B (within the <= 544/576 B bounds). Matches the report.
- 070554 trace (my own scan, red = 772919 ms): VS A7F79FA0 1040 draws, red +72.07 -> +104.90 s; AB219D40 249, +44.01 -> +46.99 s; AB0FA4E0 66, +45.04 -> +46.83 s. Matches report §3.
- 073150 per-window counts (476 / 166 / 1007) and red-relative timings match my review 39F51CF5.
- p0info: 1649 / 37536 x 1000 = 43.9, as printed. Its `RESULT: PASS` with REMAIN 1 shows what the v3 PASS rule means for a 073150 base (E-C2).
- No python `xxhash` module is installed, so I couldn't recompute XXH3(8 zero bytes) = 0xC77B3ABB6F87ACD9. The zero-bucket reading rests on the L341 comment plus the 6 shared-prefix inserts plus the zero-prefix bytes. That is enough.

## Report claims (CG7-report AF18189D)

- **Zero bucket (C5-S2): CONFIRMED.** 0xC77B3ABB6F87ACD9 is the shared prefix of zero-first-8-byte shaders. A REMAIN under that key is a new bucket member, not a regression.
- **"The 6 are not in any packed dump": CONFIRMED-WITH-CHANGES.** The logic is sound: native5pack-bin misses all 6, and every placement container of 172422 and 051154 is in its input (FA99EB7D; M16's statement, I did not re-list it). Scope it as "not among the packed placement containers". The unpacked root VS (and the raw files) are not excluded, so "not in any dump" would overclaim. The report's table already says "(placement containers)": keep that wording.
- **O2 root vs-A58EBA12: plausible, open.** The bytes are verified (above). It is a candidate only: it was dumped at boot by the create path, so a match would mean the same physical code is later placed. D6 settles it, but see D-C2: pack only placement captures.
- **O3 native4bp analogs: CONFIRMED-WITH-CHANGES.** The counts and timings reproduce. Overclaim: "the same red-relative times" should be "similar": W1 lasts ~3 s on native4bp vs ~8 s on native5pack; W2 starts at +72.1 vs +75.7 s. The match is by shape, not by key (event caps), so it supports "native4bp missed these scenes too" and nothing quantitative.
- **O4 the 22 no-identity guests: CONFIRMED-WITH-CHANGES (wording).** The solid fact is 0 missing draws and 0 unrecognized rows on the whole 073150 route before red + 43.5 s. Placing the 22 into those scenes rests on analogies (heap neighbourhood, count ratios ~1.6x, 12 identical stable guests across 051154/070554). Required wording: "the zone route's analog scenes render clean on native5pack; the identity of the 22 is not proven". Any promotion package lists the 22 as open-by-identity, not as closed. The dedup explanation (L190-193: no second event for an already captured container) is code-correct and labelled "likely": fine.
- **NIT R-N1 line refs:** the report cites main-tree line numbers (4B8250E9). native5pack-bin was built from snap1 (9567FE3F). L146-207, L175-180 and L190-193 coincide; L363 -> snap1 L346 (insert cap 64), L523 -> L506 (warning cap 16), L520-531 -> L503-514 (miss branch). Cite the snap1 file in future reports.

## Conditions

### Step A (kit)
- A-C1 Exact gate: `dump` is allowed only with `manual`, or with **all of** `cand5` + `zone` + `nativeonly` (L71 keeps `xenosonly` out). Suggested L65: `if ($Dump -and -not ($Manual -or ($Cand5 -and $Zone)))`. A2 (drop `$Dump` from L70) as proposed.
- A-C2 Must-exit-2 list (self-test L259): keep all 8 current cases, and add `nativeonly cand5 dump` (no zone), `nativeonly zone dump` (no cand5), `cand5 zone dump` (no nativeonly), `nativeonly cand5 zone dump xenosonly`, `cand5 explore zone dump nativeonly`. Every one must exit 2 before the lock.
- A-C3 DIAGNOSTIC label: a `Say` line in the run log (e.g. `DIAGNOSTIC: dump run, timing invalid, miss cache OFF`) and M3's route post header. No change to gameplay_post.py (A5 wins over A3). If the LATEST.txt line is written by the ps1, label it there too; otherwise leave LATEST.txt alone.
- A-C4 SHOULD: a distinct tag for the dump run (L199, e.g. `gp5d` -> run dir `<stamp>-gp5d-native`), so a dump run can't be mistaken for a cand5 proof run or base. If M3 keeps `gp5`, the DIAGNOSTIC Say line is mandatory and the M3 post must name the run as DIAGNOSTIC in its title.
- A-C5 Dryruns after install, in one slot (each re-hashes ~380 MB):
  1. `dryrun nativeonly cand5 zone dump`: COMMAND line env shows `LEGO_DUMP_MISSING_SHADERS=<kit>\shader-dumps-native-<stamp>`; the ZONE, CAND5 and DIAGNOSTIC lines; verify-bins PASS on native5pack-bin and bin-native5 (787CD694); SIDECAR line `--tag <tag>-native ... --led-shots --zone --zone-delay 45`, no `--then-mark`; prompt self-test A-F ok; no dump dir left; every A-C2 case `(expected 2: ok)`; `dryrun-runs removed`; `DRY RUN ALL PASS` (refusal note only for the hidden desktop).
  2. `dryrun nativeonly cand5 zone`: identical to 072938 except the stamp; **no** `LEGO_DUMP_MISSING_SHADERS` in the env.
  3. `dryrun manual dump nativeonly`: still passes, with the dump env (the existing manual dump path is unchanged).
- A-C6 Install as for kit rev 2 (I2): the rated ps1 and new .cmd shas live, pins ok, PS 5.1 parse 0 errors, tamper x3 exit 3 then restore, backup of 691B70AD / B2B2BE24 in M3 scratch. Rollback = restore these two.

### Step B (dump run)
- B-C1 GO only after A-C5 ALL PASS and C rated. The GO line carries the new RUN-GAMEPLAY.cmd sha: `RUN-GAMEPLAY.cmd|<new sha>|nativeonly cand5 zone dump`.
- B-C2 Preflight as CG2 (no legodimensions process, no GO.txt/HOLD, waiter END, live kit = rated shas, native5pack-bin MANIFEST 787CD694 and exe 90BF6B45, bin-native5 787CD694, bin-native C5181520). Not started after 09:30.
- B-C3 Hands off as CG3 (X1: 0 keystrokes, no external ctl writes; the only toypad actions are the sidecar's). Exclusive window until the waiter END. A kit refusal is a stop, not a retry.
- B-C4 Real-run log: the DIAGNOSTIC, ZONE and CAND5 lines; pinned MANIFEST 787CD694; verify-bins 0 FAIL; `PASS native fingerprint: a349d5292f67b127`; the env carries the dump dir. sidecar.out header as CG4.
- B-C5 Outputs stay in M3's kit dir. M16 reads them only; any copy for D goes to build\agent16 with a SHA256SUMS. Post scans at BelowNormal after END.
- B-C6 Claims: functional and DIAGNOSTIC only. No timing claim, no proof5 RESULT. Never use this run as a proof base or candidate. A crash, gate miss, prompts other than 1/1 or a zone stop are reported as is; any re-run needs a new GO.
- B-C7 After: bin-native C5181520, bin-native5 787CD694, native5pack-bin 787CD694 / 90BF6B45, LATEST-pack AC7B9053, LATEST-bin 76D0EFB9 unchanged.

### Step C (dump6_post.py)
- C-C1 Static and read-only: `python -B`, writes only under build\agent16, refuses (exit 2) on a missing input. Inputs pinned by sha in its output.
- C-C2 D1: keep the proof5 v3 anchors (gate regex `wait line 55 current=5 pending=0 \d+ +ok after`, anchored `prompts=batman:1/1 gandalf:1/1 wyldstyle:1/1`, 302/302, exit 0), plus zone=done and a red-18 start. Set the reach threshold to stop >= red + 80 s (W2 starts at +72..76 s, and one bind is enough to capture), not +100 s; report W2 coverage seconds separately. Fewer than 80 s -> W2 NOT-REACHED (W1 can still be COVERED).
- C-C3 D3 join key: draw_missing carries only the VS guest, so match target guests to identity events by guest address, or by physical (backing) address from the unrecognized rows in the same window. physical_hash may only join identity events to each other; it must not be used to "cover" a miss row that has no physical address. COVERED needs every VS **and** PS target guest in W1/W2 matched.
- C-C4 D7: raw files are keyed by prefix hash with no overwrite, so the expected count is unique (stage, prefix) pairs, i.e. <= 1 per stage for the zero bucket, not one per identity. Root files: expect the 2 boot files; any other root file is listed. D4: no xxhash module is installed, so state which check ran (size = virtual_bytes + 4 + physical_bytes, plus the file name = container_hash, plus the sha256 of each file). A container_hash recompute needs a sanctioned xxhash; don't pip-install for this.
- C-C5 Self-test fixtures, at least: COVERED; PARTIAL (one PS guest without identity); NOT-REACHED (stop < red + 80 s); INCONCLUSIVE (gate L56; prompts 1/10); a false-cover case (a matching physical_hash on an unrelated guest must not cover); the raw-dedup count; D6 match and no-match. Plus a real-data run on 051154 (expect its known identities) and on 073150 (no dump: expect 0 identities -> PARTIAL/uncovered listing, exit as designed).

### Step D (native6pack, plan level)
- D-C1 Only if the B post is COVERED, or PARTIAL with >= 1 new placement container. NOT-REACHED / INCONCLUSIVE -> no D.
- D-C2 Pack input = placement-containers only (copies + SHA256SUMS). **No root file** in the pack input, even on a D6 match: the root dump has a different format (no marker, create path), and the placement capture of the same code, if it missed, is in the dump anyway. A D6 match is reported, not packed.
- D-C3 Scripts: copies of the frozen native5pack scripts (N6: originals untouched). Hand in a diff vs native5pack that has only name/path changes plus the four listed NIT fixes (S1, N1, N2, N3), each called out. The same CTL/ON gates as native5pack bin; ON fp must differ from a349d529; new bin dir only.
- D-C4 No pin, LATEST-pack, LATEST-bin or default change; no promotion (N4).
- D-C5 Own P1 package rating before the build GO; exclusive slot (no overlap with any run or dryrun).

### Step E (cand6 proof, plan level)
- E-C1 The kit word (e.g. `cand6`) gets its own rating, built like cand5 (pinned MANIFEST, own copy dir, tag, expect-fp), with `cand6` excluded from `dump`/`manual`/`explore` and a full must-exit-2 list; plus dryrun before GO.
- E-C2 proof5_post v3's RESULT is **not sufficient** with base 073150: its STABLE targets (from DUMP-TARGETS-story) did not miss in 073150, so PASS reduces to "rate lower" (the p0info run printed PASS with REMAIN 1). The success criteria for E are: cand missing draws at >= red + 40 s = 0; REMAIN 0, NEW 0, NEW-@ 0; route 7/7; frames ratio within +-10 %; fp of the new build.
- E-C3 Reach evidence is required, because 0 misses could also mean "not reached": zone=done, red-18 start, stop >= red + 80 s, and zone/red timings within +-1 s of 073150 (per the C5 review table). If the late scenes aren't shown reached, the result is INCONCLUSIVE, not PASS.
- E-C4 Per-window counts (W1a, W1b, W2) in the E post, because the prefix key can't tell the 6 shaders apart.
- E-C5 Wording: FIXED is route-only (C5-S2); no generalization of FIXED-by-prefix; no promotion (N4 stays the user's Phase 4 call).

## Findings

- SHOULD S1 (A1): as written it opens `nativeonly cand5 dump` without zone. Fixed by A-C1.
- SHOULD S2 (D7): the raw-dump count formula is wrong for the zero bucket (one raw file per stage and prefix). Fixed by C-C4.
- SHOULD S3 (R3 plan B): `placement-raw` can't size or identify the zero-bucket targets individually: only the first bound target per stage gets a raw file. Plan B needs another source (e.g. a guarded capture log line), which is out of scope here and needs its own rating.
- SHOULD S4 (D1): +100 s makes a fine W1/W2 capture INCONCLUSIVE for no reason; capture needs one bind. Use +80 s for W2 reach (C-C2).
- SHOULD S5 (E): the v3 PASS rule is vacuous for a 073150 base. Fixed by E-C2 and E-C3.
- NIT N1 (A3 vs A5): DIAGNOSTIC labelling conflicts with "no post change". Resolved by A-C3.
- NIT N2: R1 overstates the slowdown risk somewhat. 051154's 41.75 fps was on native4bp with many missing guests on the full path; on native5pack only the 6 targets take the full path after red + 43 s. D1 still guards it.
- NIT R-N1: the report's line refs use the main tree; cite snap1 (above).
