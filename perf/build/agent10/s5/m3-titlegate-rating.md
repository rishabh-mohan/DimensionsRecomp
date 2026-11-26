# M3 title gate (gen_gameplay_route.py boot2): rating

M10, 2026-11-26 04:02. Requested by the Overseer. This rating does not block the noshots GO or the manual Toypad session on the live kit (2B60C24F).

| file | sha256/16 | bytes |
|---|---|---|
| build/agent3/gameplay/kit.dump-to-titlegate.diff | 77144CCBF8A601AC | 10003 |
| build/agent3/gameplay/post/titlegate-evidence.md | EEC54BC821149266 | 2024 |
| M3 scratch cand-title/gen_gameplay_route.py | 3F849107E24BC86B | 13316 |
| M3 scratch cand-title/explore-route.txt | CB271440130C47ED | 8314 |
| M3 scratch cand-title/gameplay-route.txt (unchanged) | D491FF7FC07A6C38 | 9989 |
| M3 scratch cand-title/RUN-MANUAL.cmd | 2960C11B757D3A94 | 5689 |
| M3 scratch cand-title/RUN-EXPLORE.cmd | E0787CC1E2401FFE | 5493 |
| M3 scratch cand-title/RUN-GAMEPLAY.cmd | 1EC3D1424B7E341A | 5193 |

Base: the live dump kit. ps1 D97C9228 (unchanged), gen 40D9316A, explore-route 4C9B82D6, gameplay-route D491FF7F, RUN-MANUAL 2B60C24F, RUN-EXPLORE 6A0FE718, RUN-GAMEPLAY 134CBD48. Earlier ratings: s5/story-dump-plan-rating.md 65431D30, s5/m3-mapfix-rating.md B1D6EE9C (G4 INCONCLUSIVE after EXPLORE2).

## Verdict

SAFE-IF T1-T5.

## What I checked

- **Diff reproduces the candidates.** Applied to scratch copies of the live files (git apply, autocrlf off), the diff gives RUN-MANUAL 2960C11B, RUN-EXPLORE E0787CC1, RUN-GAMEPLAY 1EC3D142 and explore-route CB271440 byte-exactly. The gen hunks only apply after LF normalisation (see NIT N1). After that they give gen 3F849107 from 40D9316A, and they are identical to my own `git diff --no-index` of live vs candidate gen. Stats: gen +19/-8, explore-route +16/-6.
- **Cmds.** In each cmd only 2 lines differ: GPPIN_04 (gen) and GPPIN_05 (explore-route). Both point at the candidate shas. GPPIN_06 (gameplay-route D491FF7F) and GPPIN_01 (ps1 D97C9228) are unchanged. The files stay CRLF (57/55/53 CR). Swapping the two old pins back gives 2B60C24F / 6A0FE718 / 134CBD48 byte-equal.
- **Gen.** `python -B` ast.parse is OK. I ran `gen --check` on a scratch copy holding the candidate gen and both route files: "same" for both, explore-route 246 steps / 66 marks, gameplay-route 322 / 56, exit 0. No files were written; the scratch is mine.
- **Route text.** After the fe(12) wait: sleep 3, mark title, sleep 12, then 6 × (`press START` + `wait_log "current=13 pending=4294967295" 10`), sleep 2, mark press-start, `press B`, sleep 4, mark updates-panel, `press A`, `wait_log "current=5 pending=0" 20` (TITLE GATE CHECK). The constants are fixed (TITLE_SETTLE, TITLE_TRIES, TITLE_WAIT = 12, 6, 10). Inputs are pad presses only. The bound is about 80 s.
- **Evidence (game.log and input.csv read directly):**
  - EXPLORE2 031607: fe(12) at 03:20:04.742. The only route START (input.csv t=240.59, L37) did not move the title. The route then sent only A/B. The probe START at 03:37:52.3 went 12→34/39/58/40→13 in 0.3 s.
  - 195931: fe(12) at 20:03:53.2. About 30 route A presses over the title did nothing. The first START (t=437.9, about +176 s) was taken at 20:06:49.7.
  - Manual 204323: Enter at 20:47:36.37 (+28.6 s) was taken 15 ms later.
  - Manual 024219: Enter at 02:49:15.57 (+53 s) was taken. Its earlier Enters fell in state 0, before the title.
  - So on the title, START is taken at once whenever it is accepted, and the only miss was very early (+3.8 s). Tries at about +15 to +69 s cover the window seen so far (+28.6 s minimum accepted).
- **13 → Updates panel timing.** B at 13 goes 35/8/11/17/0 in 80 ms (EXPLORE2 03:37:58.175-.257). The manual runs show the same path in 0.08-0.3 s. So the blind 4 s after B is plenty, and a START or A landing in 17 (cursor on Credits) during that path is practically impossible.
- **Post.** gameplay_post.py E33DF654 counts only waits with a timeout ≥ 20 s as long waits (L237-250). The five or so expected 10 s START-wait TIMEOUTs are not counted. The gate check (20 s) is counted. It replaces the old 20 s fe(0) wait, so there are still 10 long waits.
- **Cursor semantics.** A timed-out wait leaves the cursor at the log end, and fe(13) appears within about 0.3 s of an accepted START. Later START waits time out harmlessly. The fe(5) gate check can only match after the A that follows B. It can't match on an earlier line.

## Conditions

- T1: install exactly these candidates (gen 3F849107, explore-route CB271440, cmds 2960C11B / E0787CC1 / 1EC3D142). Then set-pins byte-equal, pincheck ×3 exit 0, preflight-parse 0, and swap-back as above. Install only when no gameplay-kit session is live: after the manual Toypad session on 2B60C24F ends, never during it.
- T2: run the tamper pin cases again as in C91BEA02 (exit 0 ×3, exit 3 cases for gen and explore-route), and send me the log sha.
- T3: dryruns `RUN-EXPLORE dryrun` and `RUN-MANUAL dryrun`, both DRY RUN ALL PASS, with no dump var in the manual -Env. Send me the log shas. Only one kit's dryruns at a time, as before.
- T4: the first real run reports the try number that matched fe(13), its delay after fe(12), and the gate-check result. That adds a row to the evidence table.
- T5: if the gate check TIMEOUTs, the run is FAIL for its purpose (G4 / prompts). Any route-tail evidence after the TIMEOUT is not used, because a later route START may take the title out of sync. Record it and stop, with no mapping changes from such a run.

## Findings

- SHOULD S1: gameplay-route.txt (RUN-GAMEPLAY, unchanged D491FF7F) still uses the old prefix: wait_first_frame, a blind `sleep 50`, a single `press START`, sleep 3, `press A`, with no fe waits. It has the same weakness, and worse. Move gameplay() onto boot2 before any RUN-GAMEPLAY GO.
- SHOULD S2: a real early abort on gate failure needs a harness change (vpadhost has no conditional stop). That is the harness owner's call. Until it lands, T5 applies.
- NIT N1: the diff file is CRLF throughout (135 CR). gen_gameplay_route.py is LF, so its hunks don't apply byte-exactly (`git apply`: patch failed at gen:21). They are correct after LF normalisation. Write future kit diffs byte-true (`git -c core.autocrlf=false diff --no-index`, saved without conversion).
- NIT N2: the worst-case explore route (all waits TIMEOUT) goes from about 1901 s to about 1948 s against the -Seconds 1500 cap. This only matters in failed runs. A good run matches its waits early.
- NIT N3: what START does at 13 is still unknown (M3 says so). B converges the known cases, and anything else ends in a gate-check TIMEOUT, so it is visible.
