# cand5+zone run 073150 review

- Who/when: M10, 2026-11-26 07:55. Read-only (no runs, no images viewed).
- Base: `s5/z2-review-cand5zone-go.md` BB58D08E (CG1-CG8); `s5/proof5-result-zone-go.md` EE9C2C33 (proof5 PASS on 064143, V-N1); `s5/proof5v3-rerate.md` 63A96A74.
- Inputs: M3 post CB800C87; the Overseer's shot addendum (description only, counted as evidence, not as proof of control).

## Files (sha256/16, hashed by M10)

| File | sha256/16 |
|---|---|
| build\agent3\gameplay\post\gameplay-route-20261126-073150.md | CB800C8708E441CA |
| build\agent3\gameplay\logs\gameplay-20261126-073150.txt | E04C6695A98304B9 |
| build\agent3\gameplay\logs\gameplay-dryrun-20261126-072938.txt (CG1) | FCBCA4B35B1131C9 |
| sidecar.out (073150) | B1F9FB5F661F0CCE |
| auto post (073150) | 590FB347974DD70B |
| SHA256SUMS (073150) | FF8917F2EB2C26DB |
| runs\20261126-073156-gp5-native\toypad-events.csv | 5CC02D3CB6BA1295 |
| bin-native\MANIFEST.txt | C518152026695279 |
| bin-native5\MANIFEST.txt | 787CD694F0B884D9 |
| build\agent16\pack\LATEST-pack.txt | AC7B9053C05BB53A |
| build\agent16\pack\LATEST-bin.txt | 76D0EFB9F59DD267 |

## Verdict

- (a) CG1-CG8: **hold**. The run is valid as a P0+ functional run (second functional cand5 run, first cand5 zone run).
- (b) PASS-WITH-CHECKS: **CONFIRMED as new coverage, not a regression** of proof5's route claim. All 1649 missing draws fall after the red-18 state began (first one at red + 43.5 s); the shared pre-zone segment has 0, as in 064143.
- (c) Overclaims: none that change the verdict. Four scope corrections, listed under Findings (C5-S1, C5-S2, C5-N1, C5-N2).
- No proof5 RESULT, no timing claim, no promotion from this run (CG7). The proof5 baseline stays 064143.

## What I checked

### CG1 (dryrun 072938)
- ZONE line `--zone --zone-delay 45`; CAND5 line (native5pack-bin MANIFEST 787CD694F0B884D9, copy bin-native5, tag gp5-native, trace trace-native5-STAMP, expect-fp a349d529).
- verify-bins PASS on native5pack-bin and bin-native5, 0 copied.
- SIDECAR line: `--tag gp5-native` ... `--led-shots --zone --zone-delay 45`, no `--then-mark` (tail read by me).
- Prompt self-test A-F ok, `dryrun-runs removed`, `DRY RUN ALL PASS (1 refusal note)`, note = hidden desktop.

### CG2/CG3/CG5 (from the run log, not observed live)
- REAL RUN on desktop Default (interactive: visible); START `-BinDir bin-native5 -Tag gp5-native`; keystrokes 0; sidecar result `ctl=0 done/0 err`. The toypad actions in toypad-events.csv are the 3 boot loads, the 3 prompt answers and the 6 zone commands only.
- Preflight items (no GO.txt/HOLD, waiter END) rest on M3's post; nothing in the logs contradicts them.

### CG4 (real-run log E04C6695, sidecar.out B1F9FB5F)
- ZONE and CAND5 lines as in CG1; pinned MANIFEST 787CD694; verify-bins 0 FAIL on both bins; `PASS native clean exit`; `PASS native fingerprint: a349d5292f67b127`.
- sidecar.out header: tag gp5-native, trigger `mark ''`, `zone ON (delay 45 s ...); led shots on`. Result: `prompts=batman:1/1 gandalf:1/1 wyldstyle:1/1 ctl=0 ... then=off ... zone=done zone-skips=0 alerts=1 shots=7`, load-confirms 9, remove-confirms 6.
- Exits: run-game, sidecar, holdwatch and watcher all 0.
- No SIDECAR line in the real log: same dryrun-only gap as 070554 (Z2-S1), covered by CG1 plus the header.

### CG6 (Z3, my own extraction from toypad-events.csv, game_ts)

| Item | 073150 (cand5) | 070554 (native4bp) |
|---|---|---|
| T0 (zone-t0) | 07:43:38.905 | 07:17:42.994 |
| step 1 first command (REMOVE gandalf confirm) | T0+45.48 | T0+45.47 |
| step 1 LOAD wyldstyle pad 3 | T0+49.56, handoff 0.078 s | T0+49.55, 0.076 s |
| step 2 LOAD gandalf pad 2 | T0+53.88, handoff 0.061 s | T0+53.89, 0.065 s |
| step 3 LOAD batman pad 1 | T0+56.18, handoff 0.103 s | T0+56.19, 0.106 s |
| zone-done (all 3 pads 99 42 0E) | T0+56.29 | T0+56.29 |
| done -> red-18 start | 17.295 s (07:44:52.486) | 17.17 s |
| red-18 rows per pad | 88 red + 87 off, all 3 pads | 88 + 87 |

- No retry, skip or stop. Shot rows: zone-t0, zone-cue-pad2, zone-cue-pad1, zone-done, alert1-plus05s/30s/60s (7). Red-18 last row 07:46:36.860, i.e. still blinking at the route stop.
- M3's Z3 numbers match mine to within 0.02 s; the zone behaviour is the same on both bins.

### CG8 (G7, re-hashed by me at 07:54)
- bin-native C5181520, bin-native5 787CD694, LATEST-pack AC7B9053, LATEST-bin 76D0EFB9: unchanged. No lego process running.

### (b) Missing draws, my own scan of the three traces
- Trace start 07:31:59.914; marks in trace time: T0 698991 ms, done 755277 ms, red 772572 ms (= 07:44:52.486, consistent with the csv).

| Trace | Missing draws | Where |
|---|---|---|
| 073150 cand5 zone | 1649 (VS only, 0 PS), 1231 frames (35359-37536) | 0 before red; first 07:45:35.974 (red + 43.5 s, done + 60.8 s), last 07:46:37.002 (route stop) |
| 064143 cand5 proof5 | 0 | whole route; 0 unrecognized, 0 inserts |
| 070554 native4bp zone | 157320 VS + 77846 PS | 166753 before T0, 17355 T0->done, 6026 done->red, 45032 after red (14 guests, none of the 3 below) |

- 073150 VS guests: 0xA7F7A100 x1007, 0xAB80F350 x476, 0xAB64C0E0 x166.
- Each is paired with an unrecognized PS that shows no draw_missing of its own: 0xA7F7A100 / 0xA7F79ED0 (2014 rows each), 0xAB80F350 / 0xAB77B580 (520), 0xAB64C0E0 / 0xABB3F110 (332). unrecognized_shader 5732 in total; miss-cache inserts 6.
- All 6 inserts carry prefix 14374147212387527897 = 0xC77B3ABB6F87ACD9, the same coarse prefix that proof5 counted as FIXED (its largest key).
- Reading: the route segment shared with proof5 (boot to T0, and T0 to red) is clean, so proof5's route claim stands. The late misses come from scenes that 064143 never reached (it had no zone step). The post-red count is 1649 vs 45032 on native4bp; that is functional and informative only (different runs, heap addresses move, different reach).

## Findings

- SHOULD C5-S1 (dump targets): M3's post names only PS 0xAB77B580. All three VS (0xA7F7A100, 0xAB80F350, 0xAB64C0E0) and all three paired PS (0xA7F79ED0, 0xAB77B580, 0xABB3F110) are unrecognized, so all six belong in the dump/pack proposal. M16's proposal gets its own rating.
- SHOULD C5-S2 (proof5 scope): proof5's FIXED key 0xC77B3ABB6F87ACD9 now has new variants that miss. FIXED-by-prefix holds for the route only and must not be generalized. Any native5pack promotion package (N4) must state this next to the route-only scope, the V-N1 AOT warnings and the 22 no-identity guests.
- NIT C5-N1: "all after the red state began" is correct; state it more precisely as ">= red + 43.5 s (done + 60.8 s)", since the first 43 s of red are clean.
- NIT C5-N2 (addendum): "nothing visibly missing" in 055/057 is a visual impression of single frames. It does not offset the counted misses: by my scan all 1007 0xA7F7A100 misses fall in 07:46:08-07:46:37, the window that holds 055 and 057; the other 642 (0xAB80F350, 0xAB64C0E0) fall in the earlier window. The HUD plus the Grapple hint count as P0+ game-progress evidence only: the game advanced to its next tutorial hint by itself. Control return is still unproven (no input was sent); it stays with the manual session (P1-P4 under R1-R4; P5 blocked).
- Carried: Z2-S1 (echo SIDECAR in real runs) and Z2-N2 (Z3 extractor) stay open for the next ps1 revision, which needs a re-rate under Z4.
