# Rating: M3 zone-step ctl plan (post §5) and the manual + dump combination; S1 G4 closure; EXPLORE3 clearance

M10, 2026-11-26 04:55. Static review. I ran nothing.

## Files

| file | sha256/16 | role |
|---|---|---|
| build/agent3/gameplay/post/manual-toypad-debug-20261126-041246.md | A6CA97C5CE610ABB | M3 post; §5 = the ctl plan |
| build/agent3/gameplay/logs/gameplay-dryrun-20261126-044830.txt | DAC1FDC92C68F7DF | G4 dryrun 1, RUN-GAMEPLAY dryrun nativeonly |
| build/agent3/gameplay/logs/gameplay-dryrun-20261126-044916.txt | 4414F34B26EB9659 | G4 dryrun 2, RUN-EXPLORE dryrun |
| build/agent3/gameplay/logs/gameplay-dryrun-20261126-045001.txt | F78B3A9975C31FE1 | G4 dryrun 3, RUN-MANUAL dryrun |
| build/agent3/gameplay/gameplay-run.ps1 | 28F7785B | live (S1); dump word L47/L53-55/L121/L184/L206-207/L314 |

Base:
- s5/m3-s1-rating.md 0B4BBE79 (G1-G5);
- s5/m3-titlegate-rating.md 4AD1E9BC (T4/T5);
- s5/story-dump-plan-rating.md 65431D30 (D4-D6);
- s5/m3-prompt-explore2-rating.md 28C92370 (ctl rules (a)-(i));
- s5/m3-manual-kit-rating.md 6A70CF8A (M2-M6);
- s5/manual-toypad-0412-check.md 98FD9EB0.

## Verdicts

1. **S1 G4: CLOSED.**
   - All three dryruns are DRY RUN ALL PASS.
   - Each launches only the native arm (one COMMAND line).
   - Headers: route 705A3A50 = "same 302/57" with -Seconds 1500 (GAMEPLAY); explore 246/66 with -Seconds 1500 (EXPLORE); manual -Seconds 1200, no LEGO_DUMP.
   - The only FAIL lines are the post self-test (st0) and the stand-in "native toypad tags".
2. **EXPLORE3 (`RUN-EXPLORE.cmd`, real, native default, 5B4A31A9): CLEARED,** under X1-X3.
3. **ctl plan §5: SAFE-IF C1-C6.**
4. **Manual + `dump` in one session: SAFE-IF D4 (unchanged) + C7-C9.** Before the GO I need the items listed under "Packet".

## What I checked

- **ctl plan vs rules (a)-(i):**
  - Every verb and tag is valid (e)/(f).
  - One file per command, waits of 3-15 s, all ≥2 s (h).
  - It starts with `status` and has a one-retry stop rule, which addresses the churn in 008-011 last time.
- **Layout walk from b2 g3 w1:**
  - 002 leaves b2 w1 (g off).
  - 003 `move wyldstyle 3` leaves b2 w3. During the move, g and w are both off for about 1 s.
  - 004 leaves w3 only (b and g off for about 10 s, until 005).
  - 005 gives g2 w3; 006 gives b1 g2 w3, which is the hypothesis target.
  - The sequence is consistent.
- **Dump word, live ps1 28F7785B:**
  - It is refused without `manual` and with `xenosonly` (exit 2).
  - It logs DIAGNOSTIC and writes LATEST "dump on, timing invalid".
  - Dryrun counts a leftover dump dir as bad.
  - tamper-s1 C6AAE0FD showed the three refused combos exit 2 with 0 fs changes.
- **Not shown yet:** a `RUN-MANUAL.cmd dryrun dump` on the S1 ps1. D3 last checked that on D97C9228.

## Conditions

**EXPLORE3:**
- **X1:**
  - Native only (the default); no `xenosonly` (G1).
  - One kit at a time; interactive desktop.
  - No hand input at all during the run: no keys, no ctl files, no clicks into the game. The vpad route is the only input. Screenshots are fine.
- **X2: report.**
  - T4/T5: title try number, its delay after fe(12), and the gate-check result. A gate-check TIMEOUT is a FAIL; ignore the tail after it.
  - The three s-* prompt waits (LOAD vs TIMEOUT).
  - Whether `stop` came before 1500 s.
  - Whether the speed-15 zone step appeared (pad / colour / time). Nothing in the route answers it.
- **X3:** route steps that run blind during an unanswered zone step are expected. They are not a kit fault and not a reason to change the route without a rating.

**ctl plan:**
- **C1 (gate on status):**
  - Run 002-006 only if 001 `status` shows b2 g3 w1.
  - If the layout differs, stop the ctl part and report. Don't improvise a new mapping during the session.
- **C2 (timing):**
  - No ctl while a load or cutscene is running.
  - The start signal is the speed-15 slow blink on a pad after the all-pad amber.
  - Never send ctl within 10 s of a story prompt fire or before its prompt-done (rule (i)). The `--on` triggers stay live.
- **C3 (verify each step):**
  - Before the next file, check the `.done` and the listener confirm, plus the LED line in game.log (`Toypad: pad P …`), not only the screen.
  - Any `.err` → stop the ctl part.
- **C4 (retry and stop):**
  - Exactly one retry at 003 (`remove wyldstyle` + `place wyldstyle 3`, ≥5 s apart).
  - If pad 3 still doesn't change, stop the ctl part and record it. The same rule applies at 005 and 006: one retry, then stop.
  - No other commands until control returns.
- **C5 (two figures off):** the 004→005 window, with b and g both off, is fine. Keep it ≤15 s: send 005 as soon as 004's confirm is in.
- **C6 (scope):**
  - §5.4 free-play tests come only after the step is resolved, with ≥10 s between files.
  - §5.5, the sidecar rule for the zone step, needs its own rating after a confirmed layout.
  - M2-M6 still hold (M3: a foreground screenshot before each key burst).

**Manual + dump:**
- **D4 still applies.**
  - (a) is now met: mapfix G4 was closed at 04:40.
  - (b) The zone verdict rests on ctl/listener/LED evidence only.
  - (c) If the step is not accepted in a dump session, that result is **not conclusive**: re-test without `dump` before §5.5 or any mapping change. A positive result (an accept on all three pads) does count.
  - (d) DIAGNOSTIC: all frames/fps/missing-draw counts are void.
- **C7 (cap):**
  - The dump slows frames (miss cache off), and last time the step started at +928 s of 1200.
  - Use the §1 key path with no detours.
  - If the step hasn't started by about +1050 s, skip the ctl plan for this session and keep the dump.
  - No cap change without a rating.
- **C8 (pre-GO dryrun):** `RUN-MANUAL.cmd dryrun dump` on the live S1 kit must show:
  - `LEGO_DUMP_MISSING_SHADERS=<abs path, no ';'>` in the env line, plus the DIAGNOSTIC line;
  - no dump dir left behind;
  - DRY RUN ALL PASS.
- **C9 (post):**
  - D6 applies: M16's dump_post is read-only on M3's dirs and writes only under build/agent16/dump/.
  - If there are ≥256 identity events, report the capture as capped.
  - Root create-path files are flagged and not packed.
  - The hit list reports which target hashes (M16's list + the white-portal ones) were dumped and which were not.

## Packet (before the combined GO)

1. The C8 dryrun log sha.
2. M16: the target hash list, as a file with sha. It should include the white-portal set. M3's post §4 names 5 (VS A7FA6E00 / A7FA8990, PS A7FA6C00 / A7FA8750 / A8302100) plus AC53D0AC / AC49B8F8. Say which "5" is meant.
3. M16: the dump_post.py sha and its output dir.
4. The Overseer: confirmation that the session follows §1 + §5 under C1-C7, with the key and ctl logs kept as in the 04:12 session.

## Findings

- **SHOULD:** the plan rests on a medium-confidence layout. With `dump` on, a miss is not conclusive (D4c). If the zone result is the priority, run the ctl plan in a session without `dump`; if the shader dump is the priority, combine them and accept the possible no-dump re-test.
- **NIT:** in 003, use `move wyldstyle 3`, not `swap`. A swap would put gandalf back on a zone.
- **NIT:** the M16 render-note figure "3 dropped draws per frame" in the portal scene is relevant for P6-type comparisons. Native4bp perf in that scene is slightly flattered, too.
