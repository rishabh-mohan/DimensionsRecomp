# proof5 result review + Z2 zone-rule GO

- Who/when: M10, 2026-11-26 07:05. Read-only.
- Base: `s5/kit-rev2-install-check-proof5-go.md` 1456CB47 (proof5 GO, G1-G7); `s5/proof5v3-rerate.md` 63A96A74 (P1-P6); `s5/m3-zone-draft-rating.md` 89D0B10B (Z1-Z4); `s5/kit-rev2-proof5v2-rating.md` 18509DEB (I6).

## Files (sha256/16, hashed by M10)

| File | sha256/16 |
|---|---|
| build\agent16\proof5\post-20261126-070100\proof5_post.txt | ED075282833221EA |
| build\agent16\proof5\evhist-20261126-070100.txt | 27AB212A9493DAB8 |
| build\agent3\gameplay\post\gameplay-route-20261126-064143.md | F4E30C05468BE160 |
| build\agent3\gameplay\post\gameplay-20261126-064143.txt | 1ED727366AB563D2 |
| build\agent3\gameplay\logs\gameplay-20261126-064143.txt | E2CAF368E0DA8381 |
| build\agent3\gameplay\logs\20261126-064143-native.sidecar.out.txt | 9774E2AE30FFBCE6 |
| build\agent3\gameplay\runs\20261126-064148-gp5-native\game.log | 28268F5E2A4B7787 |
| build\agent3\gameplay\trace-native5-20261126-064143\events.tsv (261,322,924 B) | 5D10B042DA824CE3 |
| build\agent3\gameplay\trace-native-20261126-054546\events.tsv (base) | F98BF46E04364572 |
| build\agent3\gameplay\RUN-GAMEPLAY.cmd (live) | B2B2BE248085E167 |
| build\agent3\gameplay\gameplay-run.ps1 (live) | 691B70ADA6C55839 |
| build\agent3\gameplay\prompt_sidecar.py (live) | 1D9A6EB54B3C300A |

## Verdict

- proof5 result: **CONFIRMED**. RESULT PASS stands under P1-P6. Route-scoped; no promotion.
- Z2 zone-rule real run: **GO** for `RUN-GAMEPLAY.cmd nativeonly zone`, under ZG1-ZG7. I agree with the Overseer's choice over `RUN-EXPLORE.cmd zone` (reasons below).

GO line:

```
RUN-GAMEPLAY.cmd|B2B2BE248085E167FD1F2131F40871F380627F4D02599B28B33059FEE54C17EF|nativeonly zone
```

## What I checked (proof5)

- Every input sha in the proof5_post header equals my hash of the file (cand trace, cand log, cand post, run log, sidecar, base trace F98BF46E, base log 4A53519F); script sha B2B920DC is the rated v3.
- Independent count (my own streaming pass over both events.tsv): cand has 0 `draw_missing_vertex_shader`, 0 `draw_missing_pixel_shader`, 0 `shader_miss_cache_insert`, 38979 `frame` events; base has 134404 / 86306 / 64 / 40881. The cand trace is not empty (261 MB, 926685 texture_fetch_changed), so "0 missing" is a real 0, not a dead trace. Matches evhist 27AB212A (unrecognized_shader 307745 -> 0; texture_color_authority 169649 -> 340831).
- P1-P6:
  - P1/P3: run was exactly `nativeonly cand5`, no zone (`zone off; led shots on`); CAND5 line, verify-bins PASS on native5pack-bin and bin-native5 787CD694; fp a349d5292f67b127 PASS.
  - P2/P5 route outcome: gate HIT try 1 (L55, +15.83 s), prompts exactly 1/1 each, 302/302 stop at L310 (t=879.37), 10/10 long waits, same 10 non-gate TIMEOUTs, all exits 0, X1 0 keystrokes, ctl=0. Zone step: pad 3 120 s hint TIMEOUT, pad 2 open at stop, both within ~1 s and 1 row of 054546. Same outcome.
  - frames 38979 / 40881 = 0.953, inside +-10%.
  - P4 order: waiter END 06:56:52 -> M3 post -> proof5_post 07:01.
  - P6 / G7: bin-native C5181520, bin-native5 787CD694, LATEST-pack AC7B9053, LATEST-bin 76D0EFB9 (re-hashed by me at 07:03). No legodimensions process.
- Scope (carry into any promotion package):
  - The proof covers this route only. The 22 no-identity guests of the 051159 manual session are not proven fixed outside it (M16's caveat).
  - Functional only: frames ratio is a gate, not a timing claim. texture_color_authority doubling means more draws execute; any perf effect needs a timed run.
  - N4 holds: native5pack-bin is not promoted by this PASS. Promotion needs its own package and rating.

## Z2: why GAMEPLAY rather than EXPLORE

- Same route as 054546 and 064143, so pad 3 / pad 2 timing compares directly against two no-zone runs with identical outcomes (T0 at t~702, stop at t~879 = T0+178 s).
- Window fits: with `--zone-delay 45`, done is expected at ~T0+55-65 s, red-18 ~18 s later, its +60 s shot at ~T0+135-145 s, all before T0+178.
- EXPLORE stopped ~T0+170 and loses its v-replace mark under `zone`; it adds nothing over GAMEPLAY for this question.

## Conditions (Z2 GO)

- ZG1 Preflight: no legodimensions process; no GO.txt; no HOLD file; the waiter's last status line is END; live RUN-GAMEPLAY.cmd B2B2BE24, gameplay-run.ps1 691B70AD, prompt_sidecar.py 1D9A6EB5; bin-native MANIFEST C5181520.
- ZG2 Exactly the GO line: `nativeonly zone`, no `cand5`, no other word. Default native4bp bin (bin-native, fp 39129c4c, tag gp-native). X1 hands off: 0 keystrokes and no external ctl writes. The only ctl actions allowed are the sidecar's own (prompt answers and the zone rule). A kit refusal is a stop, not a retry.
- ZG3 Run log must show what the dryrun 063409 showed: `ZONE: prompt sidecar --zone --zone-delay 45 on`; the SIDECAR line has `--led-shots --zone --zone-delay 45` and no `--then-mark`; native pinned MANIFEST C5181520; verify-bins PASS. If any of these differ, the run is void for Z2.
- ZG4 Exclusive window until the waiter END: no build, dryrun, pack or heavy I/O by anyone.
- ZG5 M3 post (G5 items 1-6 as in 054546/064143, plus Z3):
  - title gate (L55), prompts (exactly 1/1 each), stop/steps/exits, X1;
  - T0 game_ts;
  - per zone step: the commands with wall time, the cue/confirm game_ts, handoff latency, any retry, skip or stop;
  - the full sidecar result line (`zone=`, `zone-skips=`, `alerts=`, `shots=`, `ctl=` with done/err);
  - red-18: first and last speed-18 game_ts per pad, and done -> red-18 delta;
  - shot rows from index.csv with jpg names (names only; nobody views or hands over images unless the Overseer asks);
  - side-by-side pad 3 / pad 2 / pad 1 timeline against 054546 and 064143;
  - what the route did after the zone step (its inputs are scripted for the no-zone outcome; note any changed FE path, waits or TIMEOUTs after T0);
  - G7 hashes after the run.
- ZG6 After the run: bin-native C5181520, bin-native5 787CD694, LATEST-pack AC7B9053, LATEST-bin 76D0EFB9 unchanged.
- ZG7 Outcomes: a zone-stop, a hint timeout or a step-1 stop counts as a result, not a run failure; a step-1 stop is INCONCLUSIVE for the delay (Z-S1). A crash, a title-gate miss or prompts other than 1/1 are reported as is. Any re-run, and any change to the 7 files or the route, needs a new GO (Z4). The hand-check of control return and the PROBE P1-P4 stay with the next manual session.

## Findings

- NIT V-N1: M3's §0 says the cand run had 2 startup `shader not present in AOT cache` warnings, the same 2 hashes as the baseline. They are outside the miss-count (not draw_missing events) and harmless here; keep them listed in any promotion package.
