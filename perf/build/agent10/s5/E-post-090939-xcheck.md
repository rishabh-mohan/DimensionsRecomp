# M3 E post cross-check: gameplay-route-20261126-090939.md

- Who/when: M10, 2026-11-26 ~09:32
- Base: E-run-090939-review.md DA29A2B9 (E-C2..E-C6, E-R1..E-R4, NIT E-N1)

## Files

| File | sha256/16 |
|---|---|
| WS\build\agent3\gameplay\post\gameplay-route-20261126-090939.md | 7AB741C508D2EA22 |

## Verdict

CONFIRMED-WITH-CHANGES. The figures agree with my review and with my own reads. One scope sentence needs rewording (P-S1). It does not change the result: E 090939 is VALID and PASS, route-only.

## What I checked

- Every evidence sha I computed in DA29A2B9 matches the post's table (kit log, sidecar, game.log, kit post, trace, MANIFEST, exe). The G7-after table also matches my 09:28 recheck.
- Its trace event-kind counts are identical to my scratch count: frame 37232, resolve 111, texture_color_authority 180085, texture_fetch_changed 915442, texture_header_refresh 4155, texture_upload_changed 2249, and 0 for every shader or miss kind.
- E-N1 is addressed: all three clocks are given.
  - I re-read the base sidecar: zone-done 07:44:35.346 to alert 07:44:52.729 = 17.383 s, as the post says.
  - The post is right that my review compared the cand sidecar figure (17.149) with the base game_ts figure (17.295).
  - Like for like, the gaps are −0.234 s (sidecar), −0.125 s (zone-done to game.log red) and −0.124 s (game_ts). All are inside ±1 s, so the E-C3 outcome is unchanged.
- E-C6 items match the kit log: gate HIT, prompts 1/1 ×3, 302/302 with the same 10 timeouts as the baselines, exit 0x0, keystrokes 0, ctl 0, miss cache ON, no DIAGNOSTIC or LEGO_DUMP.
- E-C5: the wording is quoted verbatim. The cold-boot PSO and fps figures are labelled functional only, with no timing claim, which is acceptable.
- M3-N1 (no pre-T0 amber row) and M3-N2 (red-18 88/88 instead of 88/87) are accepted as notes, not faults. T0 is keyed on pad 3 `FF 00 18`, and the stop is still past red + 80 s.

## Changes

- P-S1 (SHOULD): in §3, "W1a role ABA99710: the VS that had no identity in B, which is also covered here" should read: "no misses on this route; covered by key C77B3ABB (inference), not by identity; the 22 stay open by identity".
- NIT P-N1: in §3, "M16's e6 TOTAL should be 0, matching proof5's late count (E-R1)" should say E-R2. M16's e6 output D9A20145 shows TOTAL 0, so the sentence can state it as a fact.
