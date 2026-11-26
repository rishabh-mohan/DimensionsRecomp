# S5 0.4c — native4bp check (M16)

Run: `RUN-NATIVE4BP-SMOKE.cmd withref` (nf2 ref arm + native4bp arm, attract-long, 300 s each, -GpuLog).
Judged by `smoke4bp/smoke_post.py` → `smoke4bp/post/smoke-<stamp>.txt`, `smoke4bp/LATEST.txt`.

## Hard (FAIL if not met)
- Clean exit of every arm. The route runs through to the -Seconds stop with no crash or hang.
- Fingerprint of the 4bp arm is not 1616ce65e973c583 (nf2), and equals `fp=` in `smoke4bp/PIN-native4bp.txt`.
- The bin's MANIFEST sha256 equals `manifest=` in the PIN file (checked before launch).
- First 3D (first frame with draw_calls >= 300) by 200 s, with at least 60 s of run after it.

## Main metric
- Missing draws in the 3D window, before (nf2 ref arm) vs after (native4bp).
  - Dump-run baseline (nf2, 3D window from 132.9 s): missing median 98/frame, p90 127, total 423,838, about 13% of submitted draws.
  - Target after: 0. Expected residual: draws using the 2 root dumps that the pack tool can't take (memexport VS A58EBA123EFB541C, non-placement PS 93B9F93B535E7CCA).
- AOT-miss lines in game.log (`shader not present in AOT cache`, `... missing from AOT index`): count and unique hashes, before vs after.

## Soft (WARN)
- Draws per frame in the 3D window, after >= before. Draws that are no longer skipped should raise it.
- New warning or error types in game.log compared with the ref arm.
- At least 3 game-window screenshots at the idle-60/120/180 marks (≈141/201/261 s), for both arms, for the user's eye check.

## Fingerprint / cache implications
- The AOT pack is compiled into the exe, so any pack change gives a new native fingerprint. Recipes, seeds and `cache\native-pso*.bin` from nf2 are rejected, so the first native4bp boot is cold. Each smoke arm uses a fresh bin copy, so both arms are cold: a fair comparison, but not a warm-performance number.
- Never copy PSO caches or recipes between bins. Warm rows for native4bp need their own unscored seeding run.
- Perf rows: the extra ~13% of draws now actually rendered raise native's GPU load. Compare native4bp only with native4bp; nf2 numbers understated the work.
- Repin trap (PLAN-S3T4 §2): change the harness repin rule before adding the native4bp fingerprint to `$PINS`.
