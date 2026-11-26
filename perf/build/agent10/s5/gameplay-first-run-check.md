# Check: first RUN-GAMEPLAY nativeonly post (M3) against evidence; G5 on the gameplay route

Who/when: M10, 2026-11-26 ~06:05 local. Read-only: evidence re-hashed, run log, input.csv, sidecar.out and toypad-events.csv read. No kit run.

## Files (sha256/16) - WS\build\agent3\gameplay\

| file | sha256/16 | note |
|---|---|---|
| post\gameplay-route-20261126-054546.md | 808D307C299DFD11 | M3 post, items 1-6 |
| logs\gameplay-20261126-054546.txt | B7FEFD7D5AAB30EF | run log |
| logs\20261126-054546-native.sidecar.out.txt | 0654BEDB5BC3B8C0 | sidecar |
| runs\20261126-054551-gp-native\game.log | 4A53519F48B29F04 | game log |
| runs\20261126-054551-gp-native\toypad-events.csv | 9FEEBC28B085067F | toypad events |
| runs\20261126-054551-gp-native\frames.csv | 372B0F8EC9155F45 | frames |
| post\gameplay-20261126-054546.txt | BEF25BD73FB4124A | auto post |

All six evidence shas match the post's table (re-hashed by me).

Base: m3-s1-rating 0B4BBE79 (G5); gameplay-first-run-go 3EFB0F15 (GO, R1-R5, post items 1-6).

## Verdict: CONFIRMED. G5 CLOSED for the gameplay route (705A3A50)

With explore3-check C06543D6 this closes G5 for both S1 routes. S1 open items now: G1 (scope: native only) and SHOULD S1 (the cmd header).

## What I checked

1. Title gate: input.csv L33 fe 12 ok after 136.6 s at t=235.47 (game_ts 05:49:47.380); L37 `press START` at t=251.31 = try 1, +15.8 s; L38 fe 13 ok after 0.0 s (05:50:02.839). Run log L61: gate check L55 `current=5 pending=0` ok after 0.0 s (05:51:04.524). HIT.
2. Prompts: L88 / L92 / L96 LOAD ok after 0.0 / 46.3 / 127.3 s (05:51:39.502 / 05:52:37.226 / 05:54:54.526). Sidecar result: `prompts=batman:1/1 gandalf:1/1 wyldstyle:1/1`, load-confirms 6, remove-confirms 3; no failsafe and no fire 2/4+ line. Final slots b2 g3 w1.
3. Stop: input.csv L310 `stop requested` at t=879.80 (< 1500 s). Run log L45: steps 302/302, timeouts 10 (lines 19 23 25 27 29 40 42 44 46 48), stopped by the script True. Exits: run-game 0 (WM_CLOSE 0.89 s, 0x00000000), sidecar 0, holdwatch 0, watcher 0; clean exit PASS, no WER, 0 dumps. Exe FA761654.
4. Zone step (toypad-events game_ts):
   - pad 3 `FF 00 18` speed 15: 05:57:34.304 .. 05:59:34.507, 99 pad-3 rows (on and off); no load/remove/ctl after 05:54:54.526.
   - pad 2 `FF 6E 18` speed 15: 05:59:35.619 .. 06:00:31.300 (last event), 47 rows. Pad 3 timeout at T0 + 121.3 s; pad 2 open at stop; pad 1 only one `00 00 00` row.
   - speed-18 rows in the whole file: 0. No red state.
5. Auto post RESULT `PASS-WITH-CHECKS: native missing draws (native trace, whole run)`; verify-bins 0 FAIL x2, MANIFEST C5181520.
6. X1: run log L46 `keystrokes 0`; sidecar `ctl=0 done/0 err route=0 ok/0 err`, `then=not triggered`.

R1-R5 held as far as the evidence shows: interactive desktop (Default), no ctl, cap respected, missing-draws caveat in RESULT, kit unchanged (exe and MANIFEST as pinned).

## Findings

- SHOULD (zone model): here pad 3 had gandalf on it (wrong figure) and wyldstyle sat on pad 1, yet pad 3 showed the slow `FF 00 18` hint, not the fast red `FF 00 00` speed 15 seen in EXPLORE3. My earlier reading ("fast red = wrong figure on the wanted pad while the wanted figure is elsewhere") is not the whole story. The sidecar zone rule must not depend on telling red from the hint colour; key it on pad + timing, and accept both colours, as M3's draft already says.
- NIT: title tries 2-6 always run out their 10 s waits after try 1 hits (~50 s of route time). This is by design. An early exit would shorten the route, but it would change the route pin and need a re-rate; not needed now.
- NIT: perf.csv draw_calls is dead on native (known); use frames.csv draws (median 393) for draw counts.
