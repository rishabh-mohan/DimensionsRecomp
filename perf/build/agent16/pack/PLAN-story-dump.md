# PLAN: story-miss shader dump (M16, S5). DRAFT, static, nothing run

Goal: capture the bytes of the shaders native4bp misses on the story route: PS 0xA81E1C30 / 0xA81E6820, PS 0xAC49B8F8,
the other ~46 story guests, and VS 0xAC44BC64 again. With those bytes, ONE pack rebuild (AC44BC64 + story) can be
built later as the user's Phase 4 call (note `NOTE-story-misses-024219.md` B48DA281). M3's 024219 trace is not enough
to build a pack: `shader_miss_cache_insert` carries physical/span/prefix, but not the container bytes.

## 1. Mechanism (read from source, rexlego/src/gpu_native)

- `LEGO_DUMP_MISSING_SHADERS=<ABS dump root>`. This is a root path, NOT a switch: any value longer than 1 char enables it,
  and a relative value would write into the game's cwd.
- shaders.cpp:146-207 `CaptureMissingPlacementShader`, called at :521 on a placement miss of the AOT index:
  - It validates the header and the ranges.
  - It dedups by XXH3 of the full container, per stage.
  - It writes `<root>\placement-containers\{vs,ps}-<16hex>.bin` (the virtual header + 4 + physical bytes) and
    `<root>\placement-raw\...` (≤ 2048 B; refused by the pack pipeline).
  - It emits one `missing_placement_shader_identity` event per container into events.tsv when the trace is on.
  - **Cap: 256 containers per process.** Past the cap, captures are skipped silently.
- shaders.cpp:738: create-path misses go to the root dir (`<root>\{vs,ps}-*.bin`). The pack pipeline excludes these by
  default. The 19 story guests that have no insert event may land here; flag them, don't pack them.
- shaders.cpp:579-617 `DumpMissingShader`: if a file already exists it is skipped, otherwise it is written once and logs
  one `REXLOG_INFO "dumped missing shader"` line.

## 2. Side effects: FUNCTIONAL ONLY, never timed

- shaders.cpp:236: the miss cache is forced OFF, so every bind of a missed shader takes the full
  ReadableGuestSpan + FindShaderByMicrocode path. S4 estimate: up to ~6 ms/f on the render thread in the slow state,
  ~2-2.5 ms/f in the foreground.
- hooks_buffer.cpp:331-345: an XXH3 byte check that hashes every pool copy twice (src + dst). It adds CPU cost and can
  log `pool copy byte verification failed` lines (a finding if they appear, not a failure of the dump).
- The trace (LEGO_NATIVE_TRACE_DIR) is already on in M3's native arm, so its overhead does not change.
- Result: story frames run slower than in 024219. The run's frames.csv / fps must not be used for perf. Mark the run
  DIAGNOSTIC in its log and in LATEST.
- Precedent: S5 0.4a `build\agent16\dump\run-dump.ps1` (nf2 bin, attract-long, 300 s) ended exit 0 with no crash.

## 3. Piggyback on EXPLORE2? NO

- `gameplay-run.ps1` hard-codes the env (Rg-Args L175: `-Env "LEGO_NATIVE_TRACE_DIR=$trace"`). run-game strips
  inherited LEGO_* vars (L185), so the variable can't be passed from outside.
- Adding it means editing `gameplay-run.ps1` (M3's file). RUN-EXPLORE.cmd, RUN-MANUAL.cmd and RUN-GAMEPLAY.cmd all pin
  that file as GPPIN_01 = 7204852317BAFE96C12CC4FB95789E04E441960B62D564532761188C90AF5A82, so all three need a re-pin
  and an M10 re-rate.
- The dump's slowdown (§2) would also risk the explore route's timed steps and confound EXPLORE2's own read-out.
- **Decision proposed: run EXPLORE2 unchanged, as rated. Don't hold it.**

## 4. Options after EXPLORE2

### A (recommended): M3's next native MANUAL session with a `dump` word (M3 edits, M10 re-rates)

The manual session is untimed and hand-driven, so the slowdown matters least. It already reached the story (02:52:12 in
024219). Exact diff for `build\agent3\gameplay\gameplay-run.ps1`, to be applied by M3 (sketch against 7204852…):

```diff
-$known = @('explore', 'manual', 'nativeonly', 'xenosonly', 'dryrun', 'allowhidden')
+$known = @('explore', 'manual', 'nativeonly', 'xenosonly', 'dryrun', 'allowhidden', 'dump')
 ...
 $Manual = $words -contains 'manual'
+$Dump = $words -contains 'dump'   # FUNCTIONAL ONLY: LEGO_DUMP_MISSING_SHADERS (miss cache OFF, pool-copy hash check)
+if ($Dump -and -not $Manual) { Write-Host "'dump' is allowed only with 'manual' (functional, untimed)"; exit 2 }
 ...
-    if ($arm.trace) { $x += @('-Env', "LEGO_NATIVE_TRACE_DIR=$trace") }
+    if ($arm.trace) {
+        $e = "LEGO_NATIVE_TRACE_DIR=$trace"
+        if ($Dump) { $e += ";LEGO_DUMP_MISSING_SHADERS=$(Join-Path $kit "shader-dumps-$($arm.name)-$stamp")" }
+        $x += @('-Env', $e)
+    }
```

Plus, in the dryrun branch: the dump dir must NOT exist after a dryrun (count as bad if it does). Plus a log line
`Say "DIAGNOSTIC: dump on, timing invalid"`.

- Use: `RUN-MANUAL.cmd dump` (RUN-MANUAL L53 passes `%*` through).
- Then re-pin GPPIN_01 in all 3 RUN-*.cmd, rerun the pincheck + dryrun, and get M10's re-rate.
- The paths contain no `;`, which run-game's `-Env` splitter would break on (the kit dir is under `build\agent3`).

### B: separate M16 kit (not recommended)

It would duplicate M3's toypad sidecar, tags, holdwatch and route: about 12 more pinned files to reach the story
without a human. Too much for a diagnostic.

## 5. Output: size and location

- Dumps: `build\agent3\gameplay\shader-dumps-native-<stamp>\{placement-containers,placement-raw}\` plus root create-path
  files.
- Expected size: 0.4a attract gave 101 files / 124 KB. Story + menus: about 50 menu + 46 story + AC44BC64 → ~100-150
  containers → ~200-300 files, **< 1 MB**. That is under the 256 cap, but the post must check that the identity-event
  count is < 256; if it equals 256, the cap was hit and the capture is incomplete.
- The trace is the same as now: ~314 MB events.tsv for 1200 s (M3's 024219), plus ≤ 256 identity rows.
- game.log gets ≤ ~512 extra INFO lines.
- Post-processing is M16's job, read-only on M3's dirs. The existing `build\agent16\dump\dump_post.py` (`--run --dumps
  --trace --stage --out`) stages NEW containers into `build\agent16\dump\pack-input-story-<stamp>` with SHA256SUMS.
  Then `native4bp.ps1 plan` runs over both input dirs (attract 20261125-172422 + story) to give ONE pack candidate
  list.
- Check the targets: 0xAC44BC64, 0xA81E1C30, 0xA81E6820 and 0xAC49B8F8 are each present as a `placement-containers`
  file and an identity event.

## 6. Preconditions and risks

- P1: the native4bp exe must contain the string `LEGO_DUMP_MISSING_SHADERS`. That is expected, since it is the same
  source lineage as nf2 where 0.4a worked. M16 verifies it with one Idle-priority exe scan (~316 MB read) when no game
  is running, before M10 rates.
- P2: one kit at a time, interactive desktop, never within ~6 min of a timed window (as D2).
- R1: the cap is hit (menus use slots first). Mitigated by the post check; if it is hit, a second session can start
  past the menus.
- R2: a slower story could change pacing in the manual session. A human drives it, so the risk is low.
- R3: pool-copy verification errors in game.log. Report them as a finding; they don't block the dump.
- R4: no pinned bin is written. The dump root is outside the bin copy, and run-game uses M3's bin copy as today.
- Timing impact on anything rated: none. The dump env is only set in that one manual session.
