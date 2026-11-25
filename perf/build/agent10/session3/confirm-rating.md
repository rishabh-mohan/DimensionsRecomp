# Confirmation windows CF1 / CF2 (M8 drafts): rating

M10, session 3, 2026-11-25 07:56. Requested by the Overseer at 13:52Z.

## Files rated

| file | sha256 (16) | bytes |
|---|---|---|
| build/agent8/session3/confirm/README.md | C741C76FBE191818 | 4301 |
| matrix-windowCF1.json | D36A40CA5277CC7C | 7213 |
| matrix-windowCF2.json | DF8A2D3B7D0ACA14 | 5974 |
| stage-confirm.ps1 | 448D6FAD5B1B486B | 35121 |
| make-stage-confirm.ps1 | 4762808DC14BB66E | 2056 |
| stage/stage-CF1-075114.txt, stage-CF2-075130.txt, stage-CF1-075138.txt | read | - |

Base:
- bench/agent8/run/matrix-windowC.json 00E3EE97A18A3B31 (WC);
- bench/agent8/run/matrix-window8a.json A06E5E3AAEE25B07 (W8a, = build/agent8/matrix/20261125-0359/matrix.json);
- build/agent2/final/BIN-PINS.md FE4CD4FF (D7);
- final-defaults-rating.md C20B6FDB (F1-F7 before a confirmation window);
- final-gate-rating.md 2B9A8464;
- READOUT-NIGHT xcheck 25BF9B1C.

## Verdict: SAFE-IF (K1-K5)

Recommended GO lines (the sha256 is unchanged; the matrices must first be promoted per K2):

- CF1, if the slot allows ~45 min: `GO CF1 matrix-windowCF1.json D36A40CA5277CC7C3E127E10D5367DD892E43160D7AA834D04E2A936EE63D44F only=ship,s0,win3 repeats=6`. That's 1 cold + 18 runs, and it needs a TEST -PlanOnly first (K3).
- CF1, if the slot is ~30 min: `GO CF1 matrix-windowCF1.json D36A40CA5277CC7C3E127E10D5367DD892E43160D7AA834D04E2A936EE63D44F only=ship,s0 repeats=6` (staged, OK).
- CF2: `GO CF2 matrix-windowCF2.json DF8A2D3B7D0ACA1428F3B41AC2F5E587741BA8D1C5D390CD68C3646900AE0F60 only=nf,mc repeats=6` (staged, OK).
- Don't use the 4-arm CF1 alternative (`only=ship,s0,win3,dfoff repeats=4`). Its 3 scored rounds per arm are too few for a bootstrap CI, and dfoff vs s0 is a parity check that F3 and the D7 off-arm proof already cover. If you want the WC anchor, add win3 at repeats=6 as above; don't trade rounds for dfoff.

## What I checked

- **Reference arms byte for byte:** a script loads both JSONs and compares each arm with only note/group/repeats/ref ignored.
  - CF1 s0 = WC s0 and CF1 win3 = WC win3: EQUAL. That covers bin, frames, all 14 cvars incl. keep_watch_verify=false, env 500/30, and driver.
  - CF2 mc = W8a mc (native4b, the 3 W8a cvars, FRAME_METRICS + MISS_CACHE=1) and CF2 n0 = W8a n0: EQUAL.
  - Top-level timing fields: CF2 = W8a exactly. CF1 = WC except repeats 6 vs 4, which the GO overrides anyway.
- **Default arms (D7):**
  - ship = devfinal, cvars framerate_limit=0 only, env {}. That's F1's switch set, and BIN-PINS' "plain" column.
  - nf = nativefinal, W8a's cvars plus FRAME_METRICS only, MISS_CACHE unset.
  - The MANIFEST/exe hashes in the stage reports match BIN-PINS: devfinal F9C2BE72/545D28B9, devoff4b DE11A914/DFBE1D43, nativefinal D7C7B706/5C21941D, native4b B63769FE. Every listed file matches.
- **dfoff (D7 off-arm rule):** its 12 cvars equal final_gate's OFF_SET (DEFAULTS-TABLE L92) exactly, plus framerate_limit=0 and env LEGO_GPU_WAIT_BACKOFF_US=off (lowercase).
- **stage-confirm.ps1:** I reran make-stage-confirm.ps1 from a scratch copy, reading build/agent8/w-followup/stage-window.ps1 959636DC. It reproduces 448D6FAD byte for byte.
  - The 8 single-hit replacements add `-Launcher` (run-day B67EBD6C), and they move the dir/report paths to confirm/ and confirm/stage.
  - `-Promote` is refused (TEST/RECHECK only). The stage reports show "no bench writes", matrix folders 33/33, and "PlanOnly: nothing started".
- **Plans:** -ColdShared puts the single unscored cold run (55 s + 30 s) on the new bin: ship for CF1, nf for CF2. The rounds alternate their start arm. The other bin's first launch is the scored round-1 run, which the read-out drops.
- **Proof per run (plain devfinal vs win3-by-cvars):** this is enough.
  - check-defaults `--mode xenos` (hash-pinned D9936C56) requires every key with source "(default)". A devfinal launched with the win3 cvars shows "(cmdline)" and FAILs.
  - win3 on devoff4b has no "Final defaults" lines at all (legacy mode).
  - env_set separates the GPU_WAIT 500/30 env from the built-in back-off.
  - The bin MANIFEST sha separates the bins.
- **Cold/warm fairness:** this is fair if round 1 is dropped.
  - The new bins start without cache/ (and nativefinal's fingerprint 1616 rejects old recipes anyway).
  - The unscored cold run covers only 85 s after the first frame. A scored run reaches about 110 s (5 + 55 + 50). So the new bin's round-1 run still compiles whatever first appears between 85 and 110 s. That's one more reason, besides the GPU clock, to drop round 1 on every arm.
  - From round 2 on, both arms run warm on their own caches. The old bins' caches are a superset for this route.
  - Nothing copies or seeds a cache, which is correct.

## Conditions

- **K1 (order):**
  - CF1 GO only after F1, F2 and F4 have a PASS, or a HOLD the Overseer has ruled, from final_gate 9DCC72EE on devfinal-bin. CF2 GO only after F5, F5w and F7 do the same on nativefinal-bin.
  - F3/F6 (OFF bins) don't gate the windows, but they still have to pass before shipping (final-defaults F).
  - Write no GO while a functional row is running on the same bin.
- **K2 (promotion):** the Overseer byte-copies the matrix into bench/agent8/run/ (hash = the GO sha256). Then run `stage-confirm.ps1 -Recheck` and get result OK. Only after that goes the GO into WINDOW-GO.txt. Don't add the file while a launcher is checking its pins at startup.
- **K3 (3-arm CF1):** before using `only=ship,s0,win3 repeats=6`, run stage-confirm in TEST -PlanOnly on exactly that GO. Check that result is OK and that the cold run is on ship. Check the estimate (~44 min) against the day launcher's -StopAt.
- **K4 (read-out):**
  - The headline scores rounds 2-6 only. The "with round 1" verdict is a side note and is biased against the new bins (cold caches), so it never decides.
  - Each run counts only if:
    - its proof passes (ship: xenos; nf: native-old; s0/mc/win3: as in the notes);
    - its exit and functional check are clean;
    - its sys.csv has 31 columns.
  - A failed devfinal/nativefinal proof voids that run. A second one voids the arm, and the window is rerun.
  - nf exception, the same as final_gate S1: a run whose only native-old FAIL is the absent miss-cache ON line with 0 shader-miss warnings is listed but not voided. With >0 misses it is voided. (Every W8a run logged 26 misses, so I expect the line in every nf run.)
- **K5 (window rules):**
  - Timing only from the user's unlocked, idle desktop through run-day. Agent -Quick or hidden-desktop runs are functional only.
  - No M3 queue row, build or other launcher runs during the window. The preflight "builds none" line and the queue log both go into the read-out.
  - perf-notes/WINDOW-HOLD.txt was absent at 07:55.

## Findings

- **SHOULD S1 (equivalence claims):** CF2 asks whether nf ≈ mc within about ±3 %, and the 3-arm CF1 asks the same of ship vs win3. Write the equivalence margin down before the run. Claim "equal" only if the whole bootstrap CI lies inside the margin. A CI that crosses the margin is "not shown different", not "equal". With 5 scored runs per arm, the CI may well be wider than ±3 %.
- **SHOULD S2 (WC comparison):** compare ship vs s0 with WC's pooled win3 vs s0 (+7.7 % fps mean [+6.3, +8.7], cores -38.7 %) as a direction-and-size check only. Different windows don't pool. That's exactly why the in-window win3 anchor (3-arm CF1) is worth ~14 minutes if the slot allows.
- **NIT N1 (position balance):** with round 1 dropped, rounds 2-6 put the reference first 3 times and the new arm 2 times. repeats=7 (scored 2-7, balanced 3/3) would cost ~4.5 min more. It's optional; report the order with the result.
- **NIT N2:** the stage reports' "latest start 06:45" line uses the night rule (the README says so). For the day launcher, only its -StopAt check counts.
- **NIT N3:** the CF2 n0 arm isn't needed. W8a already timed mc vs n0, and CF2's question is nf vs mc.

## Read / sent

- Read: the 5 confirm files, 3 stage reports, WC/W8a matrices, BIN-PINS, final_gate OFF_SET, stage-window.ps1 (hash only, via the reproduction).
- Scratch: build/agent10/session3/scratch-final/cmp_confirm.py (arm compare). The make-stage-confirm reproduction output was deleted after the hash check.
- Sent: verdict + sha8 to the Overseer.
