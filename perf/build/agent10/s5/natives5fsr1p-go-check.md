# natives5fsr1p GO noshots F3A,F3B (04:38): P5 check

M10, 2026-11-26 04:50. Read-only check of the Overseer's 10:48 report.

## Files

| file | sha256/16 |
|---|---|
| build/agent2/s5/rt-smoke/logs/rt-smoke-run-20261126-043853.txt | E193D2DF4AB89493 |
| build/agent2/s5/rt-smoke/post/rt-smoke-post-20261126-043853.txt | 6B67A3F559360D3E |
| rt-smoke/runs/20261126-043856-s5rt-f3a/game.log | A39F954C5BBB0ACE |
| rt-smoke/runs/20261126-044323-s5rt-f3b/game.log | DC7D53FAD9A77C22 |
| rt-smoke/manual/20261126-043901-f3a/capture-log.txt | 03B89613 |
| rt-smoke/manual/20261126-044329-f3b/capture-log.txt | C7D961F8 |

Base: s5/natives5fsr1p-rating.md D3E2EF03 (P1-P6); s5/natives5fsr1p-p2-check.md 6969527A; rt-noshots-rating 7AFF48CC (N1-N6); capture-check 9FEEFB50 (K1-K4).

## Verdict

**CONFIRMED: P5 PASS on both arms.** The black-scene fix works: natives5fsr1p is native4bp's exe/pack with natives5fsr1's rexruntime. **P3/P4 CLOSED, P5 CLOSED.** The 2 post FAILs are the two screenshot gates, which fail by design in noshots mode (rt-noshots-rating, N6).

## What I checked

- **Post:**
  - 35 PASS, FAIL(2) = "F3A screenshots" and "F3B screenshots" only (0 kit shots, "-> NONE"); there is no other FAIL.
  - bin_dir = natives5fsr1p-bin on both arms.
  - F3A has spatial_fsr_presented=1 on 11157/11157 rows (100%); F3B has it on 0/11854. fsr_enabled stays 0.
- **P5 from game.log** (times since the first log line):

  | check | F3A | F3B |
  |---|---|---|
  | fingerprint 39129c4c059be5f0 | +1.8 s | +2.4 s |
  | adopted VS 0xAC449538 (hash ACAF01F0…) | +5.2 s | +9.4 s |
  | adopted PS 0xAC448F28 (hash 75A4D1AB…) | +5.2 s | +9.4 s |
  | "failed draw" lines, whole run | 0 | 0 |
  | "unrecognized" / "missing from AOT" | 0 | 0 |
  | error/critical | 0 | 0 |

  In the no-pack 04:03 run, F3A had 16 "query invalidated by failed draw" lines.
- **N5 / K1-K4 (capture logs):**
  - N2 is OK on both arms.
  - F3A: T=122.25 was skipped as late (125.4 s); the skip is fail-safe. The first capture, at 146.75 s, was 1:1 with 90.2% non-black, so N5 OK at ≥120 s. 201.5 s: 95.9%.
  - F3B: 122.25 s 97.6%, 146.75 s 91.7%, 201.5 s 96.3%.
  - Every zoom line lists `windows above the game: []`.
  - desktop-LOCAL-ONLY.png stays local.
- **P6:** perf from this bin may only be compared within natives5fsr1p (or against native4bp, which has the same exe/pack). The older natives5fsr1 arms stay invalid (M16 NOTE-nopack-runs D8395A37).

## Findings

- **SHOULD (N4):** the zoom pairs were posted to the user's webhook. N4 requires M2 to view each image first and confirm it shows only game content; K1's "[] above" check alone doesn't cover toasts. Please record that this view happened, or have M2 do it now for the posted images.
- **NIT:** F3A's first slot ran 3.15 s late, the second time in a row. Starting manual-capture a few seconds earlier, or letting it accept up to 5 s of lag, would keep the 122.25 s capture.
