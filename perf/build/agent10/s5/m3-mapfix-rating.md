# Rating: M3 Toypad map fix ("Fix 1", kit only)

M10 (Agent 10 successor), 2026-11-26 03:09. Static review only. I ran no game, kit script or generator.

## Files

| file | sha256/16 | bytes | role |
|---|---|---|---|
| kit.fix191-to-mapfix.diff | 046227862BD7339C | 3493 | the delta, 3 files |
| cand-map/gameplay-run.ps1 | 7204852317BAFE96 | 25724 | candidate; live is 8B07F5D7 |
| cand-map/gen_gameplay_route.py | 40D9316A8FB61B78 | 11867 | candidate; live is 92629EF3 |
| cand-map/explore-route.txt | 4C9B82D6D1053698 | 7491 | candidate; live is D2D7D26D |
| cand-map/gameplay-route.txt | D491FF7FC07A6C38 | 9989 | unchanged (= live) |
| post/manual-20261126-024219-notes.md | F4B118EE | - | the evidence |

The candidates are in M3's brain scratch\cand-map, not in build\agent3\gameplay\scratch\ as the brief said. All four hashes match the brief.

## Base

The live kit as of fix191: ps1 8B07F5D7, cmds RUN-MANUAL 429729A2 / RUN-EXPLORE 6449B0FC / RUN-GAMEPLAY 706CA1E7 (m3-fix191-rating 3017D129). All three cmds pin the ps1, the gen, explore-route.txt and gameplay-route.txt, so all three need new pins after the install.

## Verdict

**SAFE-IF G1-G4.**

## What I checked

- **The diff is complete.** I compared each live file with its candidate using `git diff --no-index --stat`:
  - ps1: +2/-2 (L61-62 only)
  - gen: +2/-2 (L154-155 only)
  - explore-route: +5/-5
  - gameplay-route: no change
  - This matches the diff file hunk for hunk.
- **The ps1 change.** Only the targets of two `$onSpecs` entries are swapped:
  - `F4 69 16|3D 1A 05` now goes to gandalf@*
  - `F4 00 16|3D 00 05` now goes to wyldstyle@*
  - The regexes, the pad capture group, the batman entry and all other code are byte-identical.
  - Both colour codes of each figure (the 16 and 05 forms) moved together, so there is no half-swap.
- **Parse and compile.**
  - PS 5.1.26100 ParseFile on the candidate ps1: 0 errors.
  - `python -B` ast.parse on the candidate gen: OK, no cache written.
- **Line endings.** The candidate ps1 and gen are LF (0 CR), like the live files. explore-route.txt has 248 CRs in both the live file and the candidate, so it is unchanged.
- **The route change is labels only.** The pad order stays 2, 3, 1 with the same `wait_log "Toypad listener: LOAD -> pad=N" 240` waits; only the mark names move: pad 3 = s-gandalf, pad 1 = s-wyldstyle. The regenerated explore-route.txt matches the gen change line for line. Nothing in gameplay-route.txt changed.
- **No new risk surface.** I found:
  - no new process starts, paths, writes or input actions;
  - no change to the boot layout (ldtag.STARTER: gandalf pad 1, wyldstyle pad 3, read-only), the guard, the lock, the cleanup or the 1200 s cap.
  - The sidecar still only REMOVEs/LOADs a known tag on the pad that is prompting.
- **The evidence is coherent (notes F4B118EE).**
  - Batman (pad 2, `00 00 16`) was accepted: the game stopped the pulse 39 ms after the sidecar LOAD at 02:52:14.305. So post-boot events do reach the game.
  - wyldstyle@pad3 ×5 and gandalf@pad1 ×5 were all ignored until the ~120 s failsafe.
  - The user rule "Wyldstyle in the centre" (pad 1 = centre) fits the swap.
  - "Nothing in game.log after boot" is explained by emulated_toypad.cpp logging only the first 64 reads and 256 writes (caps hit at 02:49:08 and 02:53:25).
- **Not re-run by me:** M3's gen `--check`, routecheck, and the spec replay over the two game.logs.

## Conditions

- **G1 (install exactly this):**
  - Install exactly ps1 72048523, gen 40D9316A and explore-route 4C9B82D6; gameplay-route stays D491FF7F.
  - In the new RUN-MANUAL, RUN-EXPLORE and RUN-GAMEPLAY, only those three pin values may change. Prove it with the swap-back: putting the old three shas back must reproduce 429729A2 / 6449B0FC / 706CA1E7 exactly.
  - Send me the new cmd shas.
- **G2 (checks before any GO):**
  - pincheck ×3 OK, tamper ALL PASS, preflight-parse under 5.1 with 0 errors.
  - Then both dryruns (RUN-MANUAL and RUN-EXPLORE) ALL PASS, with their log shas sent to me.
  - No GO before that.
- **G3 (EXPLORE2 waits; Overseer's question):** Yes, EXPLORE2 waits for this fix.
  - Never GO the old RUN-EXPLORE 6449B0FC again. Its prompt answers are known to be wrong, and after the install its pins fail closed anyway.
  - The C1-C3 conditions of the m3-prompt-explore2 rating (28C92370) and ctl rules (a)-(i) carry over to the new cmd.
  - RUN-GAMEPLAY still needs its route refresh and the P4 re-match before it is rated for a GO; this fix does not cover that.
- **G4 (if a prompt is still ignored, stop):** If a gandalf (pad 3) or wyldstyle (pad 1) prompt still runs into its failsafe on the next run, record it and stop.
  - Don't change the mapping again without a rating.
  - The notes' proposed emulated_toypad 0x56 logging diff belongs to another owner (rexglue-sdk) and is not covered by this rating.

## Findings

- **NIT:** Only Batman's acceptance has been seen. That the swap is correct is still an inference, from 10 ignored answers plus the user's rule; the first EXPLORE2 run will confirm it (see G4).
- **NIT:** The brief gave the candidate path as build\agent3\gameplay\scratch\cand-map\. The candidates are actually in M3's brain scratch. Install from there, by sha.
- **NIT:** The brief gave the ps1 candidate as "72048528...5A82". The actual sha256 is 7204852317BAFE96...5A82, so its sha8 is 72048523. The tail matches, so this is a typo in the brief. Use 72048523 in the pins.
