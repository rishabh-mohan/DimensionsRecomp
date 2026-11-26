# Check: EXPLORE3 post (M3) against evidence; T4/T5, G5, X1-X3

M10, 2026-11-26 05:17. Read-only. The live MANUAL+dump session was running, and I touched nothing in it.

## Files

| file | sha256/16 | role |
|---|---|---|
| build/agent3/gameplay/post/explore3-20261126-045401.md | EDFD7B4E246DDC28 | M3 post (replaces 202B82A0) |
| build/agent3/gameplay/logs/gameplay-20261126-045401.txt | F2F9E654D29DEBB8 | run log |
| build/agent3/gameplay/logs/20261126-045401-native.sidecar.out.txt | 859E9B0FB8C7E5A8 | sidecar |
| build/agent3/gameplay/runs/20261126-045407-gpexp-native/game.log | 47FBCFD834B4DE9F | game log |
| …/toypad-events.csv | 570B967F1DE41F71 | LED and listener events |
| …/input.csv | 1A2E45580AEF3674 | vpad input |
| …/frames.csv | 9F6C9FED5128F8F9 | frames |
| build/agent3/gameplay/post/gameplay-20261126-045401.txt | 296BD104B05FCC7D | auto post |

All shas match the post's evidence table. Base:
- s5/m3-titlegate-rating.md 4AD1E9BC (T4/T5);
- s5/m3-s1-rating.md 0B4BBE79 (G5);
- s5/m3-zone-ctl-dump-rating.md C78F02DE (X1-X3).

## Verdict

**CONFIRMED-WITH-CHANGES** (one timing correction, below).
- **T4/T5: CLOSED.**
  - T4: try 1 was accepted, with 13 at 04:58:20.6, 15.1-15.6 s after fe 12.
  - T5: the gate check (L56 `current=5 pending=0`) HIT at 04:59:22.3.
- **G5: CLOSED for the explore route**, the first real run on the S1 kit:
  - prompts: s-* ×3 LOAD;
  - `stop` at 875 s, before 1500 s;
  - run-game, sidecar and holdwatch all exit 0.
  - The same G5 report is still owed on the first RUN-GAMEPLAY run (route 705A3A50). G5 names that route explicitly.
- **X1-X3: met.**
  - X1: keystrokes 0 (input L46); sidecar ctl=0.
  - X2: everything reported.
  - X3: the blind steps around the zone step are as expected.

## What I checked

- **Run log:**
  - The waits match post §1/§2.
  - The 10 TIMEOUTs are L20-30 (install-prompt A loop, 6 s) and L41-49 (spare START tries at 13, 10 s). All are <20 s, and long waits are "10 of 10 ok".
  - Steps 246/246, stopped by the script.
- **sidecar.out:**
  - Three `fire 1/4` lines (04:59:55.264, 05:00:53.328, 05:03:10.996), each with prompt-done ok about 2 s later.
  - The result line has prompts 1/1 ×3, load-confirms 9, remove-confirms 6.
- **game.log:** 0 failsafe; 0 `[error]`/`[critical]` lines.
- **toypad-events, zone step:**
  - all-pad amber at game 05:05:24.089;
  - T0 = pad 3 `FF 00 18` speed 15 at game 05:05:52.989;
  - the route's replace: removes at 05:06:43.6-45.6, loads batman 2 / gandalf 1 / wyldstyle 3 at 47.6-49.6;
  - pad 3's last `FF 00 18` at game 05:06:49.239, with no pad-3 line after it;
  - pad 2 fast red `FF 00 00` from game 05:06:49.712 until 05:08:43.2.
  - The handoff came at T0+56.7 s, far from the 120 s timer. The reading "wyldstyle on pad 3 = ACCEPT; pad 2 wants gandalf (batman = red)" holds.

## Changes

- **Timing correction (SHOULD):** "ACCEPT 2 ms after the load-confirm" and "the game read them in one batch" come from the `wall` column. That is when the sidecar read game.log; its tail was blocked about 6 s while it ran the then-replace sequence.
  - The `game_ts` column shows the game handled each event in real time: removes at 43.574 / 44.587 / 45.593, loads at 47.617 / 48.629 / 49.643.
  - The pad-2 handoff came **69 ms** after the wyldstyle LOAD confirm (game_ts 49.643 → 49.712), not 2 ms.
  - The conclusion is unchanged, but the post should cite game_ts.
- **For the live session (C3/B5):** judge ACCEPT vs TIMEOUT on `game_ts`, not on `wall`. The rule is a handoff within ~1 s of the right figure's confirm and well before that pad's 120 s mark. While the sidecar runs a multi-step command, its wall stamps can lag by seconds.
- **NIT:** the 13→35→8→11→17 menu chain differs from 041246's. The route still lined up, so no action is needed.
