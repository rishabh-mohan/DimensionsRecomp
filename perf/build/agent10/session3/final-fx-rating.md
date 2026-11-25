# final_gate v3 + M3 F1-F7 install draft r2: rating

M10, 2026-11-25 ~08:05 (Overseer request 13:59Z). Read-only review: no builds, game runs, markers or GO files.

## Files rated

| file | sha256 (16) | bytes |
|---|---|---|
| build/agent12/session3/final_gate.py (v3) | 73F946E70D586060 | 39017 |
| build/agent12/session3/final_gate-v3.diff | 769BB1848276DE57 | 12460 |
| build/agent12/session3/FINAL-F-GATES.md | 1BDC0E5A6096F8D2 | 7442 |
| build/agent12/session3/final/selftest.txt (56/56, 0 BAD) | B77C06B5DD765A5B | 3102 |
| build/agent3/final-fx/FX-PLAN.md | E202228A74D069B4 | 7320 |
| build/agent3/final-fx/queue-final-fx.jsonl | 72DF558A6B3D459E | 4112 |
| build/agent3/final-fx/postcheck.ps1 (draft) | B2EA4A3EB6E15C1D | 20357 |
| build/agent3/final-fx/postcheck.diff (vs live 1025D1F6) | 3330A2E8648CA9DB | 8559 |
| build/agent3/final-fx/check_queue_fx.py | 8D2FBE296CC98E79 | 13766 |
| build/agent3/final-fx/check-queue-fx.out.txt | 05883A271174C417 | 10719 |
| build/agent3/final-fx/matrix-fx5.json | 822E2D65A94694EA | 2437 |
| build/agent3/final-fx/level-l-tail.txt | BE08A7908005B3B6 | 3347 |

All hashes re-checked at 08:04; unchanged since review.

## Base

- final-gate-rating.md 2B9A8464 (v1 SAFE-IF G1-G4; v2 CONFORMS)
- final-defaults-rating.md C20B6FDB (D1-D7, F1-F7 functional set)
- postcheck-0706-rating.md 6783F5AB (Q1/Q2; live postcheck 1025D1F6)
- BIN-PINS FE4CD4FF; run-timing.ps1 9CCE9827; run-matrix.ps1 72370A1E; s4b-queue.ps1 CCA391CA

## Verdict

**SAFE-IF.** Pin **final_gate.py 73F946E70D586060 (sha8 73F946E7)** for the whole F1-F7 chain.

- (A) final_gate v3: SAFE. The by-design timeout acceptance is narrow and fails closed.
- (B) M3 draft r2: SAFE-IF conditions C1-C4 below. The marker logic fails closed on every non-PASS path I traced.

## What I checked

### (A) final_gate v3

- The diff (LF, headers rewritten) applied to v2 9DCC72EE reproduces 73F946E7 exactly: nothing else changed.
- `ROUTE_TIMEOUTS`: level-l 6F9E6009 maps to lines {55, 58..116 even} (31 lines). level-l-tail BE08A790 maps to the same set shifted by -7. `route_timeouts()` returns FAIL when:
  - the script sha is unknown;
  - `timeouts != len(timeout_lines)`;
  - any line falls outside the by-design set.
  Fewer than 31 timeouts gives a NOTE (Overseer ruling; M12's scan of clean runs shows 27-31).
- F2/F7 also require `steps_done == steps_total` (not None) and `stopped_by_script` True.
- The selftest covers:
  - route files on disk match their shas;
  - tail = level-l lines -7 with the same wait text, and the 240 s orange wait is not in the set;
  - FAIL controls: extra line, wrong numbering on the tail, count mismatch, unknown sha, steps 120/121;
  - real runs: s4b-V0f/07f PASS, w6-gateB line 22 FAIL, cg26L 27/31 PASS + NOTE.
- A non-int in timeout_lines raises, and main exits 2, so it fails closed. A missing `timeouts` counts as 0, which is caught if timeout_lines is non-empty.

### (B) draft r2

- postcheck draft = live 1025D1F6 + exactly postcheck.diff (equal modulo CR; 85+/1-, the param line gains `[switch]$FxAuto`). Q1/Q2 and the S33 exit lines are untouched. The PowerShell parser reports 0 errors.
- `FX` (L104-113):
  - waits for WINDOW-HOLD;
  - runs final_gate with all streams redirected to `logs\<id>.fx.txt`;
  - appends `final_gate exit N`;
  - returns a scalar. Say uses Write-Host, so `$x` is not polluted by pipeline output.
- `FxMark` (L115-121) writes `fx-ok-<id>` only if `-FxAuto` AND exit 0 AND ok. Otherwise it logs "M3 decides". This holds for every non-PASS outcome: HOLD (4), FAIL (1), usage or exception (2), traceback, SKIP.
- `HintOk`: a missing check.txt means false.
- Harness rows: a restart between Check and FX skips the row (L153), so there is no marker. Fails closed.
- Matrix branch (L229-253):
  - needs exactly one `*-fx5-r1` and one `*-fx5w-r1`, else SKIP and no marker;
  - fx5 is gated `--ref` n0 0400-n0-r1;
  - fx5w is gated `--first fx5 --ref n0` plus SeedOk;
  - a crash after fx5.fx.txt leaves fx5w without a marker, so fx6 (which needs fx-ok-fx5w) does not start.
- `SeedOk` checks:
  - source_dir == fx5 `cache`;
  - not recipes_only;
  - exactly native-pso.bin and native-pso-recipes.bin;
  - each recorded sha == fx5's cache file now;
  - any exception returns an error string, so no marker.
- run-timing `-SeedCache` (L138-173):
  - copies only the 2 seed names;
  - refuses with exit 1 before the run dir exists if one is missing;
  - records the source sha.
  run-matrix 72370A1E seeds from the seed arm's latest OK run_dir and skips the arm with no source.
- Run dirs (harness and matrix) both hold exe, DLLs and a MANIFEST.txt copy, so final_gate's bin checks apply.
- My `check_queue_fx.py --fg-sha8 73F946E7` run (read-only, no --dryrun): exit 0, ALL CHECKS PASS (135 ok). It confirmed:
  - ROW_BIN = queue bins (F3 devfinal-off, F6 nativefinal-off, F5/F5w nativefinal);
  - all 4 FINAL bins have no `cache\`;
  - no markers present;
  - level-l-tail = level-l L13-130 + `sleep 180` / `mark tail` / `stop`;
  - matrix checks pass.
- Chain order: fx1 -> fx3 -> fx2 -> fx5 (F5 + F5w) -> fx6 -> fx7. Each row needs `ready-s4b-off` + `go-fx` + the previous fx-ok marker. fx4 is optional (go-fx-opt + fx-ok-fx1).

## Conditions

- **C1 (pin final_gate).** postcheck calls final_gate.py unpinned. Before each FX call, hash final_gate.py and refuse (no marker, a line in fx.txt) unless it is 73F946E70D586060. Alternative: the Overseer freezes the file for the chain (M12 makes no edits until fx7 is gated), and each fx.txt records the sha. Any v4 needs a rating before it gates a row.
- **C2 (install checks).** At install, re-run `check_queue_fx.py --fg-sha8 73F946E7` (and `--dryrun` per FX-PLAN) and keep the output. Back up live postcheck (1025D1F6) and the queue first. Install only between rows, with no postcheck or launcher mid-row.
- **C3 (G3).** Show the first F1 PASS and the first F5 PASS fx.txt in full before relying on auto markers for later rows.
- **C4 (hand markers).** Without an auto marker (HOLD, SKIP, s4b hint not PASS?), M3 writes a marker only after an Overseer ruling. A HOLD ruling cites the miss counts (0 vs >0) and the gate line it overrides (G4).

## Findings

- **S1 (SHOULD): stale `$LASTEXITCODE`.** If `& python` fails to start inside FX, `$x` keeps the s4b_check exit from the Check call just before, which may be 0. Low risk: the same python ran a moment earlier. Fix: set `$global:LASTEXITCODE = -1` before the call, and/or also require the last `F-GATE <row> ...: PASS` line in fx.txt.
- **S2 (SHOULD): fx5 cache at start.** nativefinal-bin must still have no `cache\` when fx5 launches. check_queue_fx checks this at install; re-check it if anything runs on nativefinal-bin before fx5.
- **N1 (NIT):** leftover regex alternatives `3e`/`6e` in L210/L212 match no queue id.
- **N2 (NIT):** the level-l-tail elapsed margin is thin. The shortest level-l (~430 s) + 180 s ≈ 610 s, vs the 590 s floor. The -Seconds 840 cap is fine.
- **N3 (NIT):** duplicate line numbers in timeout_lines are not deduplicated. They would still have to be by-design lines and match the count.
- **N4 (NIT):** FX-PLAN says "199 ok". The out file shows 166 (vs an intermediate final_gate 166495DD), and my read-only run shows 135. Regenerate the out file against 73F946E7 at install (C2).
- **N5 (NIT):** fx5w's dest `cache\` is not re-hashed after the copy. Acceptable: the game rewrites it, and final_gate checks loaded vs saved (v2 N6).

## Read / Sent

Read: the files above, live postcheck 1025D1F6, run-timing 9CCE9827 L138-173, run-matrix 72370A1E, s4b-queue CCA391CA. Ran: diff reproduction in scratch-final/v3chk, postcheck apply in scratch-final/fxchk, check_queue_fx read-only. Sent: verdict + sha8 to the Overseer.

## G3/C3: first F1 PASS (08:17)

**OK, a real positive.** Run 20261125-081000-fx1-devfinal-plain; fx1.fx.txt 42C7317507CCD162 (final_gate 73F946E7 pin match, exit 0, `F-GATE F1 ...: PASS`).

- The log is one game.log (21388 B, not rotated), so the joined log = game.log. final_gate says 187 lines.
- My own `check-defaults.py --mode xenos` run on that game.log gives RESULT PASS, exit 0.
  - All 13 keys read source `default`: 11 on the `Final defaults:` line, 2 on `Final defaults (GPU):`.
  - The 4 proof lines appear x1 each: 1 ms timer, C1 keep-watch on, TimerQueue precise, back-off ON 500/30 + GetData hook. back-off OFF x0; bad strings x0.
- Pins match the devfinal BIN-PINS: MANIFEST F9C2BE72, exe 545D28B9, rt C5BC627B, gpu CB3A2CC9. cvars are only framerate_limit=0, and env is empty.
- F1 is the WC light route at 240 s and has no elapsed floor (FINAL-F-GATES L43). The floor applies to F2/F7 only.
- fx-ok-fx1 is present (auto marker). C3's F5 half is still open.

## Addendum 08:41: G3/C3 F5 half: first F5 and F5w PASS are real positives

M10, 2026-11-25 08:41. Overseer request 14:39Z.

| file | sha256 (16) |
|---|---|
| build/agent3/s4b/logs/fx5.fx.txt | 81548F7D58FAE5C8 |
| build/agent3/s4b/logs/fx5w.fx.txt | AFEE6B2736E030AB |

Runs: build/agent3/runs/fx5-20261125-0834/runs/0834-fx5-r1 (F5) and 0836-fx5w-r1 (F5w). Ref: build/agent8/matrix/20261125-0359/runs/0400-n0-r1. Both were gated by final_gate 73F946E70D586060 (pin match), exit 0.

**Verdict: CONFIRMED.** Both PASSes are real positives. C3 is now closed (F1 half in the G3 section above, F5 half here).

### What I checked (game.log and run.json read directly, not only the fx.txt)

- **Miss cache ON with env unset.**
  - fx5 run.json `env_set` holds only LEGO_NATIVE_FRAME_METRICS, so LEGO_NATIVE_SHADER_MISS_CACHE is not set. W8a mc-r1 set it to 1, and n0 did not set it.
  - game.log has `Native GPU: shader miss cache ON (build default)` exactly once (L114, 08:34:18.227). It comes after the first two AOT misses and before the placement-miss block. That is the N1 placement: the line is printed by the enable decision on the miss path, with the build-default source.
  - The old bins (n0, mc-r1, mc-r2) have 0 such lines, as expected for the old code. So the line can only come from the new shaders.cpp hunk.
  - check-defaults native-old requires that line exactly once, and it PASSed. F6, still to come, is the OFF counterpart. F5 and F6 together prove the switch in both directions.
- **What F5 cannot show (INFO, not a defect).** The cache's effect is not visible in game.log. The warning mix is identical in n0, mc-r1, mc-r2, fx5 and fx5w:

  | warning | count |
  |---|---|
  | not present in AOT cache | 2 |
  | missing from AOT index | 8 |
  | unrecognized vertex | 8 |
  | unrecognized pixel | 8 |

  So "26 <= ref 26" is a no-regression check, not proof that the cache did anything. The proof chain is:
  - the code rating (new ON path = W8a mc behaviour, final-defaults-rating);
  - the ON line here;
  - the timing in the confirmation window CF2 (nf vs mc).

  No change is needed to F5.
- **Route.** Same W8a matrix shape as n0: elapsed 114.8 s (n0 ~115.5 s, mc-r1 ~116 s), the same AOT-miss hashes 0xA58EBA12... and 0x93B9F93B..., and the same placement shaders 0xAC449538 and 0xAC448F28. The route reaches the miss path, so N1 does not apply.
- **Warm path (F5w):**
  - run.json seed_cache: source = fx5 cache\, recipes_only false. Files copied: native-pso.bin (10456 B, 393B88FB) and native-pso-recipes.bin (8289 B, 12EB0519).
  - fx5w game.log starts at 08:36:17 (fx5 ended at 08:36:08), so it contains no first-launch lines.
  - In fx5w: `pipeline cache ... opened (10456 bytes)` (fx5 opened 0 bytes), then `startup pipelines loaded=1 compiled=0 failed=0 resident=1`. There are 0 "no startup pipeline recipes yet" lines and 0 "ignoring invalid or incompatible" lines. So the recipe file and the PSO blob written under fingerprint 1616ce65e973c583 were accepted by the same fingerprint.
  - Stronger signal than the recipe count: fx5 logged `pipeline cache saved, 12 new pipelines, 10456 bytes`, and fx5w logged **no** pipeline-cache save. All 12 pipelines came from the seeded cache; none were new.
- **Is N6 (1 vs 1) meaningful?** Yes, within limits. Every first launch on this route saves exactly 1 recipe and 12 pipelines (n0, mc-r1, mc-r2 and fx5 all agree), so 1 is the route's full set, not a truncation.
  - With N = 1, the check only tells 1 from 0. That still covers what F5w is for: a fingerprint or format mismatch would give loaded=0 or an "ignoring invalid" line, and the gate FAILs on either.
  - It cannot detect partial loss of a larger recipe set. That case does not arise on this route.

### Findings
- INFO: the miss-cache effect is proven by code identity with W8a mc plus the CF2 timing, not by F5's logs. State this in the F-results write-up so "26 <= 26" isn't read as proof that the cache works.
- NIT: final_gate could also report "pipeline cache saved" absent / N new on F5w as a NOTE (warm = 0 new). It is optional, not needed for this PASS.

C3 is closed. Auto markers can be trusted for the later F rows (fx6, fx7), subject to the other final-fx conditions.
