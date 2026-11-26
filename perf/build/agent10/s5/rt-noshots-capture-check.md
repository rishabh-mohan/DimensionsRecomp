# Check: M2 manual-capture.ps1 against rt-noshots N2-N5

M10 (Agent 10 successor), 2026-11-26 03:47. Static review of the script; I did not run it.

## Files

| file | sha256/16 | bytes | role |
|---|---|---|---|
| M2 brain scratch/manual-capture.ps1 | E893368ADBE182C6 | 4929 | the capture driver (one arm per call) |
| build/agent2/s5/rt-mark.ps1 | 80589B0D (per N1) | 2131 | timing helper it calls |

## Base

rt-noshots-rating 7AFF48CC (SAFE-IF N1-N6). N4 was confirmed by the Overseer at 03:26: the user's webhook, images plus a short header, posted by the Overseer only.

## Verdict

**CONFIRMED** (it complies with N2-N5), with operating notes K1-K4.

## What I checked

- **Parse.** PS 5.1 ParseFile: 0 errors.
- **N3, read-only screen use.**
  - The only computer-cli actions are `screenshot` (once), `windows` and `zoom`. There is no focus, click, key, type, scroll, mouse or drag; `status` isn't called either.
  - Before each zoom it requires the game window (matched by the pid from rt-mark) to be listed, focused and not minimized. Otherwise it logs "SKIPPED (N3)" and moves on; it never activates anything.
- **N2, the word check.** Before any capture it requires the newest real-run log (`rt-smoke-run-2*.txt`, so dryrun logs don't match) to contain `shots NONE (noshots: manual capture)`. Otherwise it exits 4 with no capture. M2 tested this offline on the 03:03 log: rc 4.
- **N4, what leaves the machine.** The one full-desktop screenshot is saved as `desktop-LOCAL-ONLY.png`. The zooms cover only the region 266,172-1099,660. Each zoom's log line lists the windows above the game.
- **N5, the stop rule.** If the first F3A zoom is not 1366x800 or is under 2% non-black (the same R+G+B>24 rule as the kit), it exits 5 with no further captures.
- **Write scope.** It writes only to build\agent2\s5\rt-smoke\manual\<stamp>-<arm>\ (M2's dir), plus computer-cli's own PNG folder. No game, kit or bin file is touched. Timing is read-only via rt-mark.

## Operating notes

- **K1 (N4):** never hand over a zoom whose log line lists any window above the game, unless M2 has viewed it and confirmed it shows only game content. `desktop-LOCAL-ONLY.png` is never handed over.
- **K2 (N5, 1:1):** 1366x800 alone doesn't prove 1:1, because a capped zoom would also give 1366 wide. Confirm from the logged screenshot `scale` that 833 × scale ≈ 1366 (±2 px), i.e. a 2240 px wide screen. If not, treat it as an N5 stop, even if the script said OK.
- **K3:** if the F3A call exits 5 (N5 stop) or 4 (N2), don't start the F3B call.
- **K4:** start each call only after the kit's real-run log exists for this GO; otherwise the N2 check reads an older log and refuses, which is fail-safe. The windows check runs ~1 s before the zoom, so a focus change in that gap is caught by the K1 visual check, not by the script.

## Findings

- **NIT:** the script hard-codes the absolute WS and agy-grid paths. That's fine for this machine-local helper.
- **NIT:** `$Times` adds 62 s to the rated times. That's harmless: one more read-only capture.
