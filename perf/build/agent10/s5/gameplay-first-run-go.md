# GO: first real RUN-GAMEPLAY nativeonly (S1 kit), G5 post contents

Who/when: M10, 2026-11-26 ~05:46 local. Read-only: 25 kit pins re-hashed with Get-FileHash, route read, process check. No kit run.

## Files (sha256/16) - WS\build\agent3\gameplay\

| file | sha256/16 |
|---|---|
| RUN-GAMEPLAY.cmd | 09304AC0606A3EED |
| gameplay-run.ps1 | 28F7785BDB47FBDF |
| gameplay-route.txt | 705A3A504BF6B669 |
| gameplay_post.py | E33DF65402DF053C |
| prompt_sidecar.py | 31C33A80A2DC9973 |
| bin-native\MANIFEST | C518152026695279 |

Base: m3-s1-rating 0B4BBE79 (G1-G5); G4 closed in m3-zone-ctl-dump-rating C78F02DE; explore3-check C06543D6 (G5 closed for the explore route only).

dtime, for the record: run log 060440829AA641A6, post 8AFE4B7DDBC68C4E RESULT: PASS, 2/2 arms on the interactive desktop, verify-bins after the arms 0 FAIL (C5181520), DTIME DONE 05:43:29. Noted under D3 (diagnostic only); not rated as a perf result.

## Verdict: GO, under G1, G5 and R1-R5 below

GO line (exact):

`build\agent3\gameplay\RUN-GAMEPLAY.cmd|09304AC0606A3EED2DE3C66718463CE3C7CD6C72E4D080E3A436D56467436CD6|nativeonly`

`nativeonly` is required (G1). The bare word, `xenosonly` and the default both-arms mode stay NOT approved; the cmd header still advertises "then xenos" (S1 of 0B4BBE79, open).

## What I checked

- All 25 GPPIN lines re-hashed: 25/25 match, incl. ps1 28F7785B, gen 2C1977DE, route 705A3A50, sidecar 31C33A80, post E33DF654, holdwatch, run-game, toml B763DABB.
- Route 705A3A50, 310 lines: the last wait_log is the third `Toypad listener: LOAD -> pad=1` (L96, 240 s). After it: observe, skip probes, walk cycles, `stop` (L310). No wait_log depends on the zone step.
- No legodimensions process now; dtime finished 05:43:29 and its post is written.

## Zone step without ctl: confirmed

- This run has no ctl channel input, so nobody moves figures at the zone step. Pads the sidecar's prompt layout doesn't already satisfy show the slow hint blink and run out their 120 s hint timeout. That is expected and is NOT a failure.
- No route wait depends on it (see above), so it cannot cause a wait TIMEOUT or change RESULT. The walk cycles then run in front of an unsolved puzzle; that limits the scope of the gameplay sample, it does not invalidate the run.
- The all-pad fast-red state (FF 00 00, speed 18) was seen only after the step was solved and its cutscene played (session 051154). It may or may not appear here; either way, record it, don't treat it as a failure.
- Any ACCEPT is judged on toypad-events `game_ts` (load-confirm -> next pad blink within ~1 s), never on sidecar wall stamps.

## Conditions

- G1: native arm only (`nativeonly`).
- R1: through the waiter on the interactive desktop. One kit at a time: no other game run, dryrun, pack build or heavy I/O (copies, exe scans, hashing of bins) in parallel.
- R2 (X1 again): no hand input and no ctl during the run. The harness `mark` screenshots are part of the route; don't hand them on.
- R3: the cap is 1500 s; the kit self-closes. Don't intervene unless the hold job fires or the game hangs past the cap.
- R4: perf numbers from native4bp are labelled with the missing-draws caveat (PASS-WITH-CHECKS, native missing draws), as in EXPLORE3.
- R5: any kit file change before the run -> no GO; re-hash, re-pin, re-rate.

## What the post must contain (G5 on the gameplay route)

1. Title gate (T4/T5): the title try number, its delay after fe(12), and the gate-check line (fe 5 pending=0) as HIT or TIMEOUT. A gate-check TIMEOUT is FAIL; ignore the tail.
2. The three s-* prompt waits (L88/L92/L96): LOAD or TIMEOUT for each, with the wait time and the fire count; any failsafe.
3. Whether `stop` (L310) was reached before 1500 s: run seconds, steps executed / total, every wait TIMEOUT with its route line, and the exit codes of game, sidecar and route.
4. The zone step from toypad-events `game_ts`: T0, then for each pad either ACCEPT (with the delay after its load-confirm) or the 120 s hint timeout; and the red state if present (first/last game_ts, speed, pads).
5. Evidence shas: run log, sidecar.out, game.log, toypad-events.csv, frames.csv, the auto post (gameplay_post RESULT line), and verify-bins lines with MANIFEST C5181520.
6. X1 statement: keystrokes 0 (input line), sidecar ctl=0.

## Findings

- SHOULD (carried, S1 of 0B4BBE79): the RUN-GAMEPLAY header still says "native4bp, then xenos" and "~2 x 15-25 min". Make the GO line's `nativeonly` mandatory until a xenos route exists.
- NIT: the third prompt in EXPLORE3 took 127.6 s; the s-* wait is 240 s, so there is headroom, but a TIMEOUT there should be reported against the fire count, not just as a wait TIMEOUT.
