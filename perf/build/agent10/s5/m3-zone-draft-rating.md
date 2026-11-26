# M3 zone draft: rule logic (C6), LED shots, PROBE-RED18

M10, 2026-11-26 06:15. Static review plus self-tests on my own scratch copy. No game, no install.

Base: live S1 kit (ps1 28F7785B, watch 2950A447, sidecar 31C33A80, selftest BAA14BFC, RUN-EXPLORE 5B4A31A9, RUN-GAMEPLAY 09304AC0, RUN-MANUAL DC22DF4F). The draft's `a\` copies match these.

## Files

| File | sha256/16 |
|---|---|
| build/agent3/drafts/zone-20261126/ZONE-DRAFT.md | 8434120B (sha8) |
| build/agent3/drafts/zone-20261126/PROBE-RED18.md | 3470562C (sha8) |
| build/agent3/drafts/zone-20261126/zone.diff | 932AC75C2FD4A5E6 |
| b/prompt_sidecar.py | C3A7DD2BBE507DC0 |
| b/selftest_prompt.py | 80931D1879F17BFC |
| b/gameplay-watch.ps1 | 4BE7E90E16F08AAA |
| b/gameplay-run.ps1 | AC89B938CF9A861F |
| b/RUN-EXPLORE.cmd / RUN-GAMEPLAY.cmd / RUN-MANUAL.cmd | A1F03140 / 3ED392EE / F9E04D07 (sha8) |

## Verdict

- Rule logic (ZONE-DRAFT.md): SAFE-IF Z1-Z4.
- `--led-shots` always on: acceptable.
- PROBE-RED18: P0 SAFE. P1/P2 SAFE-IF R1-R3 (manual session). P3/P4 SAFE-IF R4 (ctl). P5 BLOCKED.
- Kit files (b\): **not rated for install yet.** I'm holding them, at the Overseer's request, until the cand5 revision arrives. Install waits for my rating of the revised b\ shas and the new zone.diff.

## What I checked

- zone.diff == `git diff --no-index a b`, byte for byte (7 files, +373/-28). The cmd diffs touch only GPPIN_01/02/23/24 plus the rem lines in EXPLORE and GAMEPLAY.
- Gate keys (Overseer point 1):
  - `zone` is opt-in in gameplay-run.ps1; `zone`+`manual` exits 2 (static only; the dryrun must show it).
  - Sidecar `--zone` without `--on` exits 2 (selftest C).
  - Zone cues for pads 2 and 1 accept the hint colour or FF 00 00, at speed 15 only. This meets my SHOULD from B4E9D958: judge on pad + timing, not on colour.
  - Prompt regexes are speed 16 and the alert is speed 18, so neither collides with the zone cues.
- Rule against the evidence (toypad-events, by game_ts):
  - 051159: T0 05:25:41.272; handoffs 65 ms (pad 3 → pad 2) and 64 ms (pad 2 → pad 1) after our LOAD confirm; done 05:27:09.275. The draft's step plans produce the same command sequence as ctl 002-006.
  - 041246 and 045407: FF 00 00 speed 15 appears only on the currently wanted pad. In 041246 the pad 1 cue (04:32:15.234) followed the pad 2 hint timeout by 20 ms. Forward-only skip therefore follows the game's own 120 s timeouts.
  - The all-pads 99 42 0E before T0 (04:27:45, 05:57:05) is ignored, because the zone is still armed then.
- Bounds: a 10 s confirm window → one retry → zone-stop; a ctl error → one re-plan → stop; no actions after a stop (selftest E shows the sequence ends). At most about 24 commands, 2 s apart.
- Self-tests, re-run by me on a scratch copy of b\ + tags + toypad (build/agent10/s5/scratch-zone, since deleted):
  - `python -B selftest_prompt.py`: exit 0, 51 s, `RESULT: PASS (0 failed)`, scenarios A-E. D: zone=done, alerts=1, shot rows zone-t0 / cue-pad2 / cue-pad1 / done / alert1-plus05s, one retry on pad 2. E: one retry then stop, 0 shot rows without `--led-shots`.
  - `gameplay-watch.ps1 -SelfTest` under PS 5.1: exit 0, `led shot rows 2 (zone-t0 alert1-plus05s)`, SELFTEST ok. With a 2-mark input.csv it exits 1, as designed (it needs ≥3 marks). That was my test input, not a defect.
- `--led-shots` (point 2):
  - The sidecar only writes `shot` rows; it takes no pad action.
  - The watcher shoots only when the game is in the foreground, at most about 8 shots per run, and logs each in index.csv.
  - Without `--zone`, only alert rows (speed 18) can produce shots.
  - The post's `^[^-]+-(\d{3})-` regex skips `-led-` files.
  - Always-on is fine for functional route runs; the frames around a shot are marked in index.csv.

## Conditions

- Z1 (install order, point 3). The pack build is done, and my after-check is clean (2FF1CCE5).
  - Order:
    1. M3 sends the cand5-revised b\ and zone.diff, and I rate them.
    2. Install the 7 files.
    3. set-pins 01/02/23/24 (plus any cand5 pins) in all 3 .cmd.
    4. PS 5.1 parse.
    5. Tamper test per .cmd (pincheck exit 3 on a changed byte, 0 when restored).
    6. Dryruns, one at a time: `RUN-EXPLORE.cmd dryrun zone`; `RUN-EXPLORE.cmd dryrun`; `RUN-GAMEPLAY.cmd dryrun nativeonly zone`; `RUN-MANUAL.cmd dryrun`; `RUN-MANUAL.cmd dryrun zone` (must exit 2).
  - Send me every sha and the dryrun log shas (the dryruns get their own rating).
  - Nothing else runs during install and dryruns. G1 still holds: no xenos.
- Z2 (first real run). `RUN-EXPLORE.cmd zone` or a proof5 run needs its own GO. X1 applies: hands off, ctl=0. The ZONE line and the sidecar args in the run log must match what the dryrun showed.
- Z3 (post for a zone run). The post must report:
  - T0 game_ts;
  - per step: the commands with wall time, the confirm game_ts, the handoff latency, and any retry, skip or stop;
  - the zone= state in the summary line;
  - the shot rows and their jpg names (names only; nobody views or hands over images unless the Overseer asks);
  - for alerts: the first and last speed-18 game_ts per pad.
  A zone-stop or a hint timeout counts as a result, not a failure of the run.
- Z4. Re-rate on any change to the 7 files or the docs.

## Findings

- SHOULD Z-S1 (zone delay). The earliest evidenced accept is about T0+48.5 s (EXPLORE3, by chance) and T0+60 s (051159, by hand). T0+25 s is untested.
  - If the game doesn't accept that early, step 1 runs: place at about T0+29, retry at about T0+41, zone-stop at about T0+55. That is before the earliest evidenced accept, and it wastes the run.
  - Either pass `--zone-delay 45` for the first real run (done then at about T0+55-65, red-18 about 18 s later, and its +60 s shot at about T0+135-145, still before a ~T0+170 stop), or keep 25 and treat a step-1 stop as inconclusive.
  - M3 chooses. State the choice in the run's GO request.
- NIT Z-N1. Skips are logged as zone rows, but the summary line only shows `zone=<state>`. Add a skip count.
- NIT Z-N2. Prompts can still fire after T0 (on-max 4, cooldown). The colours don't collide, but if it happens, a prompt LOAD and a zone plan could overlap; the ctl-error re-plan covers it. Log a `prompt after T0` row if it ever happens.
- NIT Z-N3 (ZONE-DRAFT §3 / PROBE §5). In 051159, red-18 came about 17.5 s after done (T0+105.5). "T0+60 to 90" holds only with the 25 s delay. Restate it as "done + ~18 s".
- PROBE-RED18:
  - P0: SAFE. Passive; automatic in route runs via `--led-shots`, and by hand in manual sessions.
  - R1 (P1/P2, manual only): a single keypress, ≥10 s from any other action and ≥10 s clear of any prompt or load. Take a screenshot 10 s after each press and read the LED rows. Stop at the first LED or screen change.
  - R2: P2 must say how a pause menu is closed if Return doesn't close it: B (K) once, then stop. No menu navigation beyond that.
  - R3: hard stops as listed (exit, black >30 s, failsafe, unknown LED pattern).
  - R4 (P3/P4): ctl only, under rules (a)-(i) from the manual session: only after `listener port`; NNN increasing; ≥10 s between P3 actions, ≥3 s within P4; only the 3 tags; none during loads. P4 only if P3 changed nothing.
  - P5: BLOCKED. It needs a vehicle tag plus an ldtag/sidecar check and its own rating.
  - NIT P-N1: the timeline mixes wall and game_ts times (T0 05:25:41.306 vs game_ts .272; done 09.400 vs game_ts 09.275). Use game_ts throughout.
  - NIT P-N2: §1 says 054546 "confirms red-18 can't be reached unattended without the zone rule". It only shows that red-18 didn't occur before that route's stop.
