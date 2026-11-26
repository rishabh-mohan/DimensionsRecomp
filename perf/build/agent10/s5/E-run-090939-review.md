# E run review: cand6 zone 090939

- Who/when: M10, 2026-11-26 ~09:29
- Base: cand6-kit-rating-E-go.md 07629957 (E-C2..E-C6), cand6-E-go-check.md 03CDFBA4 (G1-G4), e6-roles-rating.md BEF90016 (E-R1..E-R4)
- Base run: 073150 (trace-native5 40060326, game.log 52574F85)

## Files (WS\build)

| File | sha256/16 |
|---|---|
| agent16\proof5\post-090939\proof5_post.txt (proof5_post v3 B2B920DC) | 48FBC72A8018D715 |
| agent16\cg7\roles-090939\e6_roles.txt (e6_roles CD2EDB82) | D9A20145EF2794A8 |
| agent3\gameplay\logs\gameplay-20261126-090939.txt (kit log) | D80BF3B21B039F09 |
| agent3\gameplay\post\gameplay-20261126-090939.txt (kit post) | 6C2A8CE3450EB92A |
| agent3\gameplay\logs\20261126-090939-native.sidecar.out.txt | 485D346132640414 |
| agent3\gameplay\trace-native6-20261126-090939\events.tsv | E485AC67B69CB6FD |
| agent3\gameplay\runs\20261126-090944-gp6-native\game.log | C4C9C851DE7FF013 |
| run dir MANIFEST.txt / legodimensions.exe / .map | 6D841C1E / F5816ABE / 21ACBA16 |

## Verdict

E 090939: VALID and PASS (route-only).

Wording (E-C5): on the zone route, the cand6 candidate bin (native6pack-bin, MANIFEST 6D841C1E, fp e5c874ca2b87a59d) produced 0 missing draws in the trace (base 073150: 1649, 43.9 per 1000 frames). The one base key, VS C77B3ABB6F87ACD9, is FIXED; REMAIN, NEW and NEW-@ are all 0. This is a single route-only run. It makes no timing or performance claim and promotes nothing. The bin stays a candidate.

## What I checked (recomputed or read myself)

- E-C2 (misses):
  - proof5_post RESULT PASS: cand 0 missing draws (VS 0, PS 0) over 37232 frames; FIXED 1 key, base 1649 to cand 0; REMAIN/NEW/NEW-@ 0.
  - Route 7/7 OK (exit 0, 302/302, stop at done, gate HIT, prompts 3/3, ctl 0, kit exits 0).
  - Both fps are True in their game.logs; the cand game.log L44 reads `Native GPU [e5c874ca2b87a59d]`.
  - The run dir MANIFEST 6D841C1E equals native6pack-bin, and the exe is F5816ABE.
  - Frames ratio 0.992, inside ±10 %, so no cold-boot CHECK is needed.
- Independent trace count (own scratch script, idle priority). Event kinds in the cand trace: frame 37232, texture_* and resolve only. There are 0 `draw_missing_*`, 0 `unrecognized_shader` and 0 `shader_miss_cache_insert` rows. The base trace, counted with the same script, has draw_missing_vertex_shader 1649, unrecognized_shader 5732 and insert 6. The cand game.log has 0 `missing` and 0 `unrecognized` lines (base: 8 and 16).
- The trace is live: event volume is close to base (frames -0.8 %, texture_fetch_changed -1.6 %, texture_color_authority +5.3 %).
- E-C3 (route timing gate):
  - zone-done 09:22:24.433 (T0 + 56.2 s). Red (sidecar) is 09:22:41.582, so done to red = 17.149 s, against 073150's +17.295, inside ±1 s.
  - Red in game.log is 09:22:41.448, and stop is red + 105.2 s, past the red + 80 s minimum.
- E-C4 / E-R1..E-R4:
  - e6_roles (pinned CD2EDB82) shows W1a/W1b/W2 0/0/0 and TOTAL 0, which equals the proof5 late count of 0 (E-R2).
  - Roles A/U/C/OTHER are all 0, so E-R1 and E-R3 are not triggered. PRE is 0 and FLAGS none.
- E-C6 (hygiene):
  - Clean exit 0x0 (WM_CLOSE 0.9 s, no WER, 0 dumps); keystrokes 0; ctl 0; prompts batman, gandalf and wyldstyle 1/1 each; no failsafe.
  - The game.log has `shader miss cache ON (build default)`. The kit log has no DIAGNOSTIC or LEGO_DUMP lines.
  - The kit log shows `timeouts 10` on lines 19..48. 073150 and 082648 show the same 10, so this is not new.
- AOT warnings: the 2 boot-time hashes, A58EBA123EFB541C and 93B9F93B535E7CCA, are byte-identical to 073150 L47-48 and come before trace start. 073150's other AOT-matching lines were in-run miss lines, which are absent in the cand run.
- G7 after:
  - kit unchanged: ps1 82EBF1BC, RUN-GAMEPLAY B1F4BF65, EXPLORE 5800E81B, MANUAL 9C4B18D4;
  - native6pack-bin 6D841C1E / F5816ABE;
  - bin-native6 6D841C1E, bin-native5 787CD694, bin-native C5181520;
  - no lego process.

## Scope and open items

- The 22 guests stay open by identity. This run shows that the C77B3ABB key no longer misses on this route. It does not prove an identity for each guest.
- U-ABA99710 VS had no identity in B, yet showed 0 misses here. In the base log all misses share prefix C77B3ABB6F87ACD9 (073150 L9001+), so the most likely explanation is that a dumped container covers the same microcode. That is an inference: count ABA99710 as covered by key on this route, not by identity.
- Promotion of native6pack (N4) remains the user's call. Nothing here changes LATEST-pack or LATEST-bin.
- Still open: K6-N1, K6-N2, E6-N1..N3, V2-N1, V2-N2, D-N1..D-N3.

## Findings

- NIT E-N1: M3's post should quote the done-to-red figure from both clocks (sidecar 17.149 s, game.log 17.015 s) and give 073150 as the reference.
