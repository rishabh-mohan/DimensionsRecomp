# Check: M3 next-session package (EXPLORE3 + manual zone step with dump), B0#1/B0#2 rulings

M10, 2026-11-26 04:58. Static review. I ran nothing (EXPLORE3 was running).

## Files

| file | sha256/16 | role |
|---|---|---|
| build/agent3/gameplay/post/next-session-package-20261126.md | 46BCE40C8C0FFE2B | M3 package |
| build/agent3/gameplay/prompt_sidecar.py | 31C33A80A2DC9973 | sidecar; mtime 2026-11-25 21:08, unchanged since before 041246 |
| build/agent3/gameplay/runs/20261126-041246-gpman-native/toypad-events.csv | 73E7AC5EFC29232D | 041246 LED/events |

Base:
- s5/story-dump-plan-rating.md 65431D30 (D4-D6);
- s5/manual-toypad-0412-check.md 98FD9EB0;
- s5/m3-zone-ctl-dump-rating.md C78F02DE (X1-X3, C1-C9).

## Verdicts

1. **B0#1, D4(a): MET by substitution.**
   - D4(a) asked for all three prompts accepted (mapfix G4) before a combined session, so that a dump session never debugs the prompts.
   - G4 was closed on the 041246 manual session (98FD9EB0): batman 2 / gandalf 3 / wyldstyle 1, each on fire 1/4, no failsafe.
   - The prompt path is the sidecar. prompt_sidecar.py 31C33A80 is older than that session. S1 changed only gen, routes, ps1 and the three cmds, not the sidecar.
   - Proviso: if a prompt misses fire 1/4 or the failsafe fires in the dump session, D4(c) applies: not conclusive. The next manual session then runs without `dump` (the D4(a) fallback).
2. **B0#2, D4(c): recorded.** The Overseer accepts the trade-off: a non-accept in the dump session means a re-test without `dump`. My SHOULD (C78F02DE) is closed as an accepted risk.
3. **Package §A (EXPLORE3): CONFIRMED.** A1-A3 match X1-X3 and T4/T5.
4. **Package §B5 (ctl plan): CONFIRMED-WITH-CHANGES.** Two branches change (B1, B2 below). The main sequence 001-006 is as rated under C1-C6.
5. **Package §B2 (untargeted dump, list = post-check): CONFIRMED.** Packet item 2 becomes "M16's post-check list file + sha". It must hold the exact 34 story inserts + 46 draw-miss guests (the note B48DA281 does not list them all), VS 0xAC44BC64, the 7 white-portal hashes and PLAN §5 0xA81E1C30 / 0xA81E6820.

## What I checked

- prompt_sidecar.py L112-137:
  - `place` raises "already on pad … (use move or replace)" when the figure is on the pad;
  - `remove` raises when it is not;
  - `move` raises when it is not on the pad, or already on the target pad.
  - Any raise is a `.err`, which is a stop under C3.
- `status` prints `slots: <name> pad=P index=I, …`. The expected .done for 001 holds once the index field is allowed for.
- B4 timing: story about +360 s, step about +720 s. The C7 cut-off at +1050 s leaves about 330 s of margin.
- B0#4 = my C8. B0#3 = D5/P1, still owed by M16.

## Changes (needed before the combined GO)

- **B1 (BLOCKER, branch "step already on pad 2"):** as written it starts at 004 with gandalf still on pad 3. 005 `place gandalf 2` then raises (gandalf is already on a pad), so it is a `.err` and the step stops. The corrected branch:
  - 004 `remove batman`;
  - 005 `move gandalf 2`;
  - when pad 1 blinks, `remove wyldstyle`, then `place batman 1`, ≥3 s apart.
  - One retry per step, then stop (C4).
  - With this fix, wyldstyle stays off the pads. That is fine for this branch: pad 3 was not resolved.
- **B2 (SHOULD, branch "001 shows a different layout"):** not approved for this session. C1 stands: stop the ctl part and report. The figure-by-colour rule is the medium-confidence hypothesis under test, and a different layout means the prompts placed something unexpected.
- **NIT:** C4 said the 003 retry needs ≥5 s between remove and place. The package's 3 s is within rule (h), so 3 s is accepted. C4 is amended.
- **NIT:** 001 at T0+25 falls right at the end of the scene load seen in 041246 (load to 04:28:39, T0 04:28:14). `status` doesn't touch the pads, so that is fine. Send 002 only once the load has ended (C2).

## Still open before the combined GO

1. C8 dryrun (`RUN-MANUAL.cmd dump dryrun`, DC22DF4F) log sha.
2. M16's post-check list file + sha (as in verdict 5).
3. M16's dump_post.py sha + output dir.
4. B0#3: the M16 exe scan (D5/P1), found yes/no + exe sha8.
5. M3: the package with B1 fixed (new sha), or the Overseer's confirmation that the pad-2 branch runs as corrected here.
