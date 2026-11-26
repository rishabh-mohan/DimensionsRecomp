# CG7: late-scene misses on cand5+zone run 073150 (M16, read-only analysis)

Scope: static analysis only. No runs, builds or kit edits. Scans ran at BelowNormal. Writes went only to `build\agent16\cg7` and `build\agent16\proof5\post-20261126-073150-p0info`.
Paths are relative to WS = `games\lego-dimensions-recomp`. Times are trace ms unless marked otherwise.

## 0. Inputs (sha256 verified before use)

| Input | sha256 |
|---|---|
| 073150 post `build\agent3\gameplay\post\gameplay-20261126-073150.txt` | 590FB347974DD70B6390E73B5947C135FFAD1296C1457B8C5F940BC5C2343871 |
| 073150 runlog `...\logs\gameplay-20261126-073150.txt` | E04C6695A98304B9744E16902E64009A991C55735B7C55063011F90857882F42 |
| 073150 sidecar `...\logs\20261126-073150-native.sidecar.out.txt` | B1F9FB5F661F0CCEF0F2EAFDA27A688308213075F269923DEF0A9FB41AB08A69 |
| 073150 trace `...\trace-native5-20261126-073150\events.tsv` | 40060326FA9A2E860705AA60BCE9DAE6A0D2CC72A674F2BC90CB8962C2AB31CA |
| 073150 game.log `...\runs\20261126-073156-gp5-native\game.log` | 52574F8573C1943F8BD9AFF21B82818D9647D5D0258D25CC400C322307C57B5C |
| 073150 M3 route post `...\post\gameplay-route-20261126-073150.md` | CB800C87… (matches the brief) |
| 070554 trace `...\trace-native-20261126-070554\events.tsv` (native4bp zone) | 10AAA5D03BF0424CAE8874413A7D1B45EED3222BFBAEB8F093A7898583A39DD4 |
| 070554 game.log `...\runs\20261126-070559-gp-native\game.log` (the run dir is 070559, not *070554*) | BB0B888E88B463234082EF1CD4CC6B1988F60C58637FC163EC29D3A65E2619FE |
| 070554 M3 route post `...\post\gameplay-route-20261126-070554.md` | E8AD7774BB9C1E964320B3EB7768464BE2FFBE10B4F04EA704268CDB1CF43E88 |
| 051154 dump-session trace `...\trace-native-20261126-051154\events.tsv` | 6DC402F444B7FD83F429D9F73CA9F356D78560F42A96E2FA65620EFCB7371306 |
| 051154 M3 manual post `...\post\manual-dump-20261126-051154.md` | 94174B07BF3DF3DBB3CE9D21AC7E2E993CDDD9055207FB680344147D8A56B4FD |
| M10 review `build\agent10\s5\cand5zone-result-review.md` | 39F51CF5A3AA0727A05CED72591FEBAE6E194D718290618EB13ED2E67AC5FDD8 |

Scripts and raw outputs are in `build\agent16\cg7\data\`; their shas are in §7.

Trace clocks (from each `trace-start.json`):
- 073150 starts 07:31:59.914. T0 698991, done 755277, red 772572 (M10's values).
- 070554 starts 07:06:03.542. T0 = 07:17:42.994 → 699452; red = 07:18:56.461 → 772919.
- 051154 starts 05:12:03.261. T0 = 05:25:41.272 → 818011; done = 05:27:09.275 → 906014; red = 05:27:26.773 → 923512.

## 1. Task 1: proof5_post v3 on 073150 (INFORMATIONAL; the RESULT does not count)

`build\agent16\proof5\post-20261126-073150-p0info\proof5_post.txt` sha256 **11149BB0ED3B7DBFBD018093FD5ACA91F7512C6298EBD41E54AB994471771AC1**
- Ran `python -B` with proof5_post v3 B2B920DC. Base = 054546 (as in G6).
- The tool printed `RESULT: PASS`: per 1000 frames 5398.8 → 43.9; keys fixed 15, remain 1, new 0, new-@ 0.
  - This is **INFORMATIONAL only**: 073150 is not a proof run, so the RESULT does not count.
- Frames ratio 37536/40881 = 0.918 (inside ±10 %). Route 7/7. ctl 0.
- cand: 1649 missing draws (all VS); 3 guests; 1 key; 6 inserts.
- The single REMAIN key is VS prefix 0xC77B3ABB6F87ACD9, cand guests A7F7A100, AB64C0E0, AB80F350.
- Per C5-S2, "FIXED" here (and in proof5 G6) holds **for the route only**. The FIXED prefix 0xC77B3ABB6F87ACD9 is the shared "first 8 microcode bytes are zero" bucket; shader_archive.cpp L341 says "thousands of physical shader sections share eight zero prefix bytes". The REMAIN entries are new members of that bucket, not a regression.

## 2. Task 2: the 1649 misses by shader

All 6 shaders take the lookup-miss path. Each has its own `shader_miss_cache_insert`, all with prefix 0xC77B3ABB6F87ACD9 (inserts happen only in the `!cache_entry` branch, snap1 shaders.cpp 9567FE3F L503-514, the source native5pack-bin was built from; main tree L520-531). Each missed draw logs about 2 `unrecognized_shader` rows per stage, for both VS and PS. `draw_missing` counts the draw once, as VS, so the PS rows show 0 misses even though the PS is also missing (C5-S1).

| Window | VS guest (backing) | PS guest (backing) | Missing draws | Frames | First → last (trace ms) | Rel. red / game.log |
|---|---|---|---|---|---|---|
| W1a | **AB80F350** (ED25B6A0) | **AB77B580** (ED25B8E0) | 476 | 35359-35667 | 816059.9 → 824416.5 | red +43.49 → +51.84 s; game.log 07:45:35.973 |
| W1b | **AB64C0E0** (ED25BA40) | **ABB3F110** (ED25BC80) | 166 | 35396-35660 | 817067.7 → 824244.8 | red +44.50 → +51.67 s |
| W2 | **A7F7A100** (ED3549C0) | **A7F79ED0** (ED354BE0) | 1007 | 36530-37536 | 848257.5 → 877087.9 | red +75.69 → +104.52 s (route stop); game.log 07:46:08-07:46:37 |

- Totals: 1649 = 476 + 166 + 1007, in 1231 frames. Timing per C5-N1: all are **≥ red + 43.5 s (done + 60.8 s)**; there are 0 misses and 0 unrecognized rows before 816059.9.
  - unrecognized_shader rows per guest (VS/PS): W1a 520/520, W1b 332/332, W2 2014/2014. The total is 2 × (520 + 332 + 2014) = 5732.
- Spans are 2324 for VS and 2024 for PS. These are the *index* max sizes for the zero bucket (ShaderMissSpan), not real sizes. The backing layout bounds the real physical sizes:
  - W1: VS ≤ 0x240 = 576 B, PS ≤ 0x160 = 352 B. W1a and W1b have the identical stride pattern.
  - W2: VS ≤ 0x220 = 544 B.
- So W1a and W1b may be one shader pair placed twice. W2 differs from W1 at least in VS size. This is unproven without container hashes.
- game.log names only the first two (AB80F350 and AB77B580, `words=00000000 ×4 … missing from AOT index`); the warning has a 16-line cap (snap1 shaders.cpp L506).

### Does the key exist in any dump or pack?

| Set | Contains the 6? | Evidence |
|---|---|---|
| native5pack-bin index (LATEST-pack AC7B9053 content + 143 staged, plan 0D10FF36, input FA99EB7D) | **No** | All 6 miss on native5pack-bin: an AOT-index miss plus a miss-cache insert each. The lookup hashes per index entry size (shader_archive.cpp L348-356), so a larger index cannot hide an entry. |
| LATEST-pack AC7B9053 | **No** | It is a subset of the native5pack index. |
| Attract dump set `build\agent16\dump\shader-dumps-20261125-172422` (101 files) and story/zone dump set `build\agent3\gameplay\shader-dumps-native-20261126-051154` (71 files: 60 placement-containers + 9 raw + 2 root) | **No: not among the packed placement containers** | Every placement container from both sets is in native5pack (pack-input-combined FA99EB7D); a dumped one would have been found. |
| | | 051154 is the only dump session that reached the red state (272 s idle red). It **never bound** a W1/W2-like pair (`cg7-win-051154.txt`). Its red-state miss set is a stable set from red+21 s to the end: AB8DC720/AB8DDB50, A8048930, AC4B7828, A7F81CD0. |
| The 2 excluded root dumps (ps-93B9F93B535E7CCA, vs-A58EBA123EFB541C), present in both sets | **PS: no. VS: unknown (a candidate)** | ps-93B9 physical starts `00000000 1001C400`, so it is not in the zero bucket: it can't be AB77B580/ABB3F110/A7F79ED0. |
| | | vs-A58EBA12 physical (400 B, bytes 304-703) **starts with 16 zero bytes**: it is in the zero bucket and within the ≤544/576 B bound. It is a possible match for one VS. The dump run in PLAN-dump6 settles this with a byte compare. |

## 3. Task 3: native4bp 070554 (same route, zone=done, red at T0+73.47 s)

The run dir is `runs\20261126-070559-gp-native`. game.log has only 8 `missing from AOT index` lines (AC44BC64 at 07:06:58), because of the 16-warning cap. All late evidence therefore comes from the trace.

070554 shows the same structure at **similar times, matched by shape not key** (stage pair, timing, 2 unrecognized rows per stage per draw, PS family), not by address; heap addresses move. W1 lasts ~3 s on native4bp vs ~8 s on native5pack; W2 starts at red +72.1 s vs +75.7 s.

| 073150 (native5pack) | 070554 (native4bp) analog | 070554 draws / frames | First → last rel. red |
|---|---|---|---|
| W1a AB80F350 / AB77B580, red +43.49 | **AB219D40 / AB91ACC0** | 249 (+94 VS-only rows) | +44.01 → +46.99 s |
| W1b AB64C0E0 / ABB3F110, red +44.50 | **AB0FA4E0 / ABB3EF40** (PS 0x1D0 from ABB3F110) | 66 | +45.04 → +46.83 s |
| W2 A7F7A100 / A7F79ED0, red +75.69 to stop | **A7F79FA0 / A7F79DA0** (0x160 / 0x130 away) | 1040 in 1040 frames (1 per frame, as in 073150's 1007/1007) | +72.08 → +104.90 s (stop) |

- **Verdict: native4bp also misses these scenes.** It drops the draws (draw_missing), with no other render path. On top of them it misses the whole late set that native5pack fixed:
  - A8048BB0, AC4B7828, A7F81D10, AB7A5BD0, A7FA69E0, AC44BC64, …;
  - M10: 45032 misses after red over 14 guests.
- Caveat: the 070554 prefixes for these analogs can't be read. Miss-cache insert events are capped at 64 per process (snap1 shaders.cpp L346; the last one is at frame 26182) and game.log is capped at 16 warnings. The analog match is therefore strong circumstantial evidence, not a key proof.
- M10's "none of the 3" (R74) compares addresses. It is consistent with the moved addresses above.

## 4. The 22 no-identity guests (051159/051154)

The zone route's analog scenes render clean on native5pack; the identity of the 22 is not proven (route-only scope, C5-S2):

| 051154 no-identity guests | 051154 time | 070554 analog (missed on native4bp) | 073150 |
|---|---|---|---|
| PS A81DF240 (6379) | 465.4 → 655.8 s | PS A81DEFE0 (7243), 346.9 → 536.9 s | 0 misses |
| PS AB625D70, A86EC990 (290 each), PS A7B09700 (0 draws) | 465.6 → 518.3 s | PS AAF3E290, AAD50C20 (395 each), PS A7B096A0 | 0 |
| VS A791C1B0 (552) | 465.2 → 510.2 s | VS A7B0D7C0 / AAC2B870 (754 each), 346.7 → 391.6 s | 0 |
| VS A7B66500, A7B98960, A7B5F240, A7B52390, A7B64000, A7B774F0, A7B5E310, A7B55170 (629/146/73/45/34/8/4/2) + PS 0-draw A7B61510, A7B61C10, A7B5EB40, A7B52C10, A7B566C0, A7B51D20, A7B5DD00, A7B54C20 | 646.5 → 700.5 s | VS A7B66410, A7B98B70, A7B5F150, A7B52460, A7B63F10, A7B77310, A7B5E220, A7B55080 (1095/254/127/79/52/12/6/4: same order, ~1.6× counts), 527.6 → 582.0 s | 0 |
| VS A7FA6EA0 (7458) / PS A7FA6C80 | T0 +3.1 s → red +21 s | VS A7FA69E0 / PS A7FA67C0 (6769), T0 +2.45 s → stop | 0 |

- The scenes line up across runs. Many stable high-heap guests are **identical** in 051154 identity events and 070554 inserts: 2890185828, 2891174060, 2890512632, 2891199100, 2891278876, 2890198848, 2890342168, 2891205436, 2890458260, 2890452096, 2890483112, 2891625032.
- 073150 has **0 draw_missing and 0 unrecognized_shader rows before red+43.5 s**: the 5732 unrecognized rows are exactly the W1/W2 pairs. This covers the boot→T0 story segment and the zone, including the 9 zero-draw PS.
- Likely reason they had no identity event: capture dedups by container hash (snap1 shaders.cpp L190-193; same lines in the main tree). A container already captured at another guest address emits no second event, but it gets packed all the same.
  - Example: PS A7FA6C80 got identity at T0+3.1 s; its VS A7FA6EA0 did not, but VS A7FA8A90 (2818214544) was captured at 460.8 s.
  - The alternative, a capture-validation refusal (snap1 L175-180), can't be excluded statically.
- **O4 wording:** the zone route's analog scenes render clean on native5pack; the identity of the 22 (incl. VS A7FA6EA0) is not proven. A promotion package lists the 22 as open-by-identity.

## 5. Task 4: proposal

See `build\agent16\cg7\PLAN-dump6.md`, a DRAFT for M10 rating; nothing executed. It proposes one DIAGNOSTIC route dump run on the unchanged native5pack-bin with the new word combo `nativeonly cand5 zone dump` (an M3 kit change). Because capture fires only on native5pack misses, it is targeted by construction. After that come a separate native6pack P1 package and a cand6 zone proof run.

## 6. Open items

- O1: W1/W2 trigger. It was reached in 2/2 scripted zone runs (070554, 073150) but not in the manual 051154 idle red state (272 s), so the cause is unknown. The dump run may need M3's exact scripted post-zone sequence.
- O2: root vs-A58EBA12 as a possible W1/W2 VS (zero-bucket, 400 B). To be settled in the dump post.
- O3: the 070554 analogs are similar times, matched by shape not key (event caps).
- O4: the zone route's analog scenes render clean on native5pack; the identity of the 22 is not proven (open-by-identity in any promotion package).
- Source line numbers cite snap1 shaders.cpp 9567FE3F (native5pack-bin's source): miss branch L503-514, insert cap 64 L346, warning cap 16 L506, ShaderMissCacheEnabled L222-225, DumpMissingShader L562-598 (raw dump L202-204, early return L587-589), root create path L721; L146-207 match the main tree.
- Carried: the native5pack M10 NITs (S1, N1, N2, N3); promotion (N4) stays the user's Phase 4 call after visual review; and the C5-S2 wording in any promotion package.

## 7. Data files (`build\agent16\cg7\data\`)

| File | sha256 |
|---|---|
| cg7_scan.py | 2E5336DF35BD65B2CE38B918B2D24C03642691EEE17A2032390E5F92318A7860 |
| cg7_win.py | ABED9380249CAF99C072197796CF890C652970B0B66557B087EC207D41EA80D4 |
| cg7-scan-073150.txt | 2D42011D68EFE2D7D165CADA34C125E1E1674CCDAF6FAB86E4DC5CD109C7E5B6 |
| cg7-scan-070554.txt | F729AF544CC10428F421AE614541C1FD90445D4A8831665BD752F21AB32BDB4D |
| cg7-scan-051154.txt | 3978A6D2A8CD1908561FC0C796915A5AB1D7E8168818B64EB8C0C44E84E1A1EC |
| cg7-win-073150.txt | F05FCC729CD94F58382585591BC20B31BC270FC3E3C638D757CF15A791341217 |
| cg7-win-070554.txt | AF99A6F1D954F5DDADF17B970999362AA2C2E4BF75B804C3BBDDC5F4D3ECB0F1 |
| cg7-win-051154.txt | AA440B40D022C5E1E20017BC17F526B543D5BA84EEF1BA86A7DF59A45D4937C5 |
| noident.txt | 552EE07E99213262F69B4D5DFF1A414C3F900949AC10DDB302161B6E34AD2FA6 |
