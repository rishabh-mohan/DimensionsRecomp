# Check: MANUAL+dump session 20261126-051154 (zone step via ctl, story-shader dump)

M10, 2026-11-26 05:37. Read-only. Base:
- s5/m3-zone-ctl-dump-rating.md C78F02DE (C1-C9, D4);
- s5/m3-next-session-package-check.md 980A1325 (B1);
- s5/dump-post-story-rating.md 3A08F6D4 (E1-E3);
- s5/explore3-check.md C06543D6 (judge ACCEPT on game_ts);
- s5/m3-prompt-explore2-rating.md 28C92370 (ctl (a)-(i)).

## Files

| file | sha256/16 |
|---|---|
| build/agent3/gameplay/logs/gameplay-20261126-051154.txt | 796071993541D5F9 |
| build/agent3/gameplay/logs/20261126-051154-native.sidecar.out.txt | BFC224E38C6F1E27 |
| build/agent3/gameplay/logs/20261126-051154-native.sidecar.err.txt | E3B0C44298FC1C14 (empty) |
| build/agent3/gameplay/runs/20261126-051159-gpman-native/game.log | 316B7F4FF1453B23 |
| …/toypad-events.csv | 67B070F67AA419C2 |
| Overseer scratch ctl-seq2.log | B5B35726F7583071 |
| Overseer scratch manual-keys.log | 39642F59DEE9A069 |
| build/agent16/dump/post-story-20261126-053310/dump_post_story.txt | F1DDEBD0D899AC93 |
| build/agent16/dump/pack-input-story-20261126-053310/SHA256SUMS.txt | 757379E2 (61 files = 60 containers + sums) |

All shas match the Overseer's list.

## Verdict

**Zone-step part: CONFIRMED.** The Toy Pad zone step was solved through the emulated pad by three ctl-driven figure changes: one `move`, one `remove`, and two `place`s. All three handoffs were figure-triggered ACCEPTs. Under D4(c) a positive result counts in a dump session.

**Dump part: CONFIRMED, complete within the cap (E2).** Of the 82 missed stage+guests, 22 have no identity event. These are probably dedup by container or validation refusals, not cap or loss.

## What I checked: session and rules

- **Run:**
  - 1205 s; WM_CLOSE; run-game, sidecar and holdwatch exit 0.
  - DIAGNOSTIC line L3; fingerprint 39129c4c; dump mode line present.
  - game.log: 0 `[error]`/`[critical]`, 0 failsafe.
- **Prompts:**
  - batman 05:19:44.245 → pad 2, gandalf 05:20:42.266 → pad 3, wyldstyle 05:22:59.529 → pad 1. All on fire 1/4, each with prompt-done ok about 2 s later.
  - The result line has prompts 1/1 ×3, ctl=6 done / 0 err, load-confirms 9, remove-confirms 6.
- **ctl rules (a)-(i):**
  - Only after `listener port 9191` (05:11:59.881).
  - 001-006 in order; each `.done` matches ctl-seq2.log; 0 `.err`.
  - Only the 3 tags; verbs status/remove/move/place.
  - Gaps from `.done` to the next send: 29.7 / 2.1 / 16.4 / 3.1 / 6.2 s, all ≥2 s (h).
  - The first ctl came 3 min after the last prompt-done (05:23:01.574), so (i)/C2 hold.
- **C1:** 001 status returned `batman pad=2, gandalf pad=3, wyldstyle pad=1` = b2 g3 w1.
- **C2 (load):**
  - Scene-load activity (adoptions, teardown, dumps) ends by 05:25:45 in game.log. The next non-Toypad line is a periodic pool stat at 05:26:19.
  - 002 was sent at 05:26:37.0. The load had ended.
- **C3:** before each next file, the listener confirm (game_ts) and the expected LED were in:
  - 002 remove-confirm 37.511;
  - 004 remove-confirm 58.513;
  - 005 confirm and the pad 1 blink at 02.383 before 006.
- **C4:** no retry was needed. **C5:** b and g were both off from 05:26:58.513 to 05:27:02.319 (3.8 s ≤ 15 s). In 003, g and w were both off for 1.0 s.
- **C7:** T0 at run +822 s, under +1050 s.
- **Keys:** 12 keys in this session (05:13:45-05:19:44), the B3 path. None after story start, and none during the step.
- **ACCEPTs on toypad-events `game_ts`** (T0 = pad 3 `FF 00 18` speed 15 at 05:25:41.272):

| step | confirm (game_ts) | handoff (game_ts) | delay | pad active for |
|---|---|---|---|---|
| 003 wyldstyle → pad 3 | LOAD pad 3 05:26:41.333 | pad 2 slow `FF 6E 18` 41.398 (pad 3's last `FF 00 18` 41.377, then none) | 65 ms | pad 3: 60.1 s |
| 005 gandalf → pad 2 | LOAD pad 2 05:27:02.319 | pad 1 slow `00 00 18` 02.383 | 64 ms | pad 2: 21.0 s |
| 006 batman → pad 1 | LOAD pad 1 05:27:09.140 | all pads amber `99 42 0E` 09.275 | 135 ms | pad 1: 6.9 s |

  - Every handoff came within 0.14 s of the right figure's confirm and far from the 120 s timer.
  - Target layout w3 / g2 / b1 is confirmed on all three pads. Colour → figure is confirmed: `FF 00 18` = wyldstyle, `FF 6E 18` = gandalf, `00 00 18` = batman.

## What I checked: dump (E1-E3, C9)

- **E1:** fresh stamp 053310, after END (05:32:17). Script D0CBA7CC and targets 9C185250 are as recorded in the report header.
- **E2:**
  - identity events 60 (60 stage+guest), far under the 256 cap, with no cap WARNING;
  - `identity events without a placement-containers file: 0`;
  - dump mode line seen; "dumped missing shader" ×71;
  - files root 2 / placement-containers 60 / placement-raw 9 = 71 = the dump-dir count;
  - root files are flagged (both IN-ATTRACT-INPUT) and not staged;
  - 60 NEW containers staged, plus SHA256SUMS.
- **E3:**
  - STABLE 16/16 DUMPED, including VS AC44BC64 (pack candidate) and PS AC53D0AC / AC49B8F8 (portal frame).
  - The 5 HEAP portal guests are NOT-SEEN as rows. That is expected: heap addresses move. The untargeted section has 3 guests in A7FAxxxx and 2 in A81Exxxx, which are likely the same shaders at shifted addresses. This is informational only, not a match.
  - 44 untargeted identities.
- 82 missed stage+guests vs 60 identities: 22 MISSING-NO-IDENTITY guests. They are not lost files (0) and not the cap. Read them as "dumped under another guest's container, or refused by validation". M16 should confirm before packing.

## Conditions and findings

- **SHOULD (scope of the claim):** this is direct evidence for one scripted Toy Pad puzzle in story chapter 1: mid-game remove, move and place through the emulated pad, read and acted on by the game. It is not yet evidence for:
  - free play;
  - character swap at the pad as a player action;
  - later zone steps.
  A repeat without `dump` is not needed for this result (D4c), but the next manual session should repeat the step once as a regression check.
- **SHOULD:** player control after the step was not hand-checked (the B5 006 row's "try a hand move" was not done). All-amber shows the step resolved, not that control returned. Record that from the screenshots or the next session.
- **NIT:** 003 was sent 2.1 s after 002's `.done`; the plan said 5 s. That is within rule (h), and there was no effect.
- **NIT:** manual-keys.log is shared across sessions (it still has the 04:1x-04:29 lines). Start a fresh log per session, or cite the line range.
- **Pack:** the 60 staged containers are pack input only. Packing them into a bin is a separate step that needs its own P1-style rating (new bin MANIFEST, verify-bins, pe check), as for natives5fsr1p.
