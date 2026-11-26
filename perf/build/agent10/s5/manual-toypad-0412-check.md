# Manual Toypad session 04:12 (RUN-MANUAL 2B60C24F): evidence check

M10, 2026-11-26 04:40. Read-only check of the Overseer's 10:34 report.

## Files

| file | sha256/16 | bytes |
|---|---|---|
| build/agent3/gameplay/logs/gameplay-20261126-041241.txt | 517804DEF744441A | 7515 |
| build/agent3/gameplay/logs/20261126-041241-native.sidecar.out.txt | 4E2F4F27372B7036 | 130075 |
| build/agent3/gameplay/runs/20261126-041246-gpman-native/game.log | 0B573C2F700712EC | 1924091 |
| Overseer scratch ctl-seq.log | FBC0AE7F4AB5CA8F | 5178 |
| Overseer scratch manual-keys.log | 0096A79D301E9221 | 1949 |

All four shas in the report match.

## Verdict

**CONFIRMED.** The session ran within manual-kit M2-M5 and ctl rules (a)-(i). It is functional only (M5); timing is void. **mapfix G4 is CLOSED**, and the mapfix NIT is confirmed.

## What I checked

- **Run:**
  - The bin is native4bp: MANIFEST C5181520 = pin, verify-bins 0 FAIL ×2. exe FA761654, rexruntime 641BD225.
  - Fresh run dir.
  - The full 1200 s ran, then WM_CLOSE with exit 0. The sidecar and holdwatch also exited 0.
  - game.log: 0 errors, 0 critical, 0 MISSING-FUNCTION.
  - The only warnings are the known stubs, NtCreateFile INSTALL*, and 8 "placement vertex shader … missing from AOT" (the known 0xAC44BC64 class).
- **FE path (native transitions):**
  - 7 (04:13:19), 0 (04:14:06), 12 (04:17:12), then 34/39/58/40, 13 (04:17:31), 35/8/11/17/0 (04:19:44), 5 (04:20:28), 10/17 (04:20:37).
  - Then 34…55 (04:21:06-04:21:52), and 0 at 04:22:16 (scene teardown). The story level was loaded.
- **Prompts:**
  - batman fired 04:22:17 and was replaced on pad 2.
  - gandalf fired 04:23:15 and moved to pad 3.
  - wyldstyle fired 04:25:32 and moved to pad 1.
  - Each fired once (fire 1/4), with remove/load confirms. No fire 2/4, no failsafe.
  - Sidecar result: prompts 1/1 ×3, ctl=16 done/0 err, load-confirms 17, remove-confirms 14.
- **ctl rules (a)-(i):**
  - (a) The dir is the run's toypad-ctl from the ctl-dir line.
  - (b) The commands came after the listener (04:12:47) and before the end.
  - (c) The files are 001-016, all .done, with no .err and no .tmp left.
  - (e)/(f) Every verb and tag is valid.
  - (g) The run dir has no input.csv and no extra files.
  - (h) ctl-seq.log shows each DONE before the next send. Gaps are 3.5-11 s (min 016-015 = 3.5 s).
  - (i) The first ctl command (04:26:48) came 73 s after the last prompt was done (04:25:35).
- **Swaps:**
  - The swaps 010/011 had 2 figures off for about 1.0 s each (04:28:20.3-21.3 and 04:28:30.4-31.4).
  - That is how the `swap` verb works, and (e) allows it. The "≤1 off" statement holds for 013-016 only.
- **Keys (M3):**
  - manual-keys.log has 18 keys since 04:13 (j/k/return, then d×3 and s×3 at 04:29:30-35).
  - game.log has exactly 18 "Native input audit" lines, all window_focus=true. The keys reached the game only.
  - ctl-seq.log has a computer-cli shot after each ctl command 002-011. I did not open the images.

## Findings

- **SHOULD: the "freeze" is not a hang.**
  - Frames kept presenting to the end: 54577 frames, 43-50 fps in the last 2 min.
  - The game kept driving Toy Pad LEDs:
    - pad 3 blinked FF 00 18 (speed 15) from 04:28:14, 4 s after ctl 009 put gandalf back on pad 3;
    - pad 2 blinked FF 00 00 from 04:30:15;
    - pad 1 blinked FF 00 00 from 04:32:15 until the close.
  - So the game waited on a Toy Pad step and moved the hint to another pad about every 2 min. Neither the re-seats 013-016 nor d/s cleared it.
  - Neither pattern is one of the 3 prompt triggers. Before EXPLORE2/S1 relies on this scene, M3 should identify that step (screens 04:28-04:32) and add a trigger or route step for it.
  - The ctl shuffles 008-011 just before the blink may have caused it. That is unproven.
- **NIT:** GPU throttling showed thermal in 0.34 of samples (85-87 C). That doesn't matter here (M5), but note it for any timed run right after.
