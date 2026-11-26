# Phase 2.4: A/B plan for native async PSO (`LEGO_NATIVE_PSO_ASYNC=1`) and #35 (seeded-boot pre-build)

M16, S5, 2026-11-25. This is a plan only: no diff, nothing applied. Both features are **already in HEAD a8e8dc8** and in nativefinal2-bin, so no code change is needed. Every arm is an env change or a bin-dir variant.

## 1. What is being tested

| Item | Code (HEAD) | Default | Output-identical? |
|---|---|---|---|
| Async PSO | `pipeline_async.h` L329-334 (env), draw.cpp L426 `g_async_pipelines`, L1705/L1713 in-flight checks, L1864 `CompilePipelineAsync`, L5732 clear | off | **No.** A missing PSO skips the draw until the compile lands (agent6-hang-triage.md L284) |
| #35 seeded-boot pre-build (S4-DRAFT row 35, a6h §9 lead (a)) | `PipelineLibrary::Prepare` (pipeline_library.cpp L196-304). It replays `cache\native-pso-recipes.bin` plus seeds (`<exe dir>\native-pso-seed.bin` and the seed dir, L483) into the driver library `cache\native-pso.bin`. `LEGO_NATIVE_PSO_PREPARE_THREADS` (L107-115) already picks the parallel path (`PrepareParallel`) | on whenever recipes exist (`LEGO_NATIVE_PSO_PRECOMPILE` unset) | Yes |

**Why #35 needs only a bin variant, not a harness change:**
- `CachePath()` is `<exe dir>\cache\native-pso.bin` (L99-105).
- run-game.ps1 hard-links BinDir into the run dir (L102-111), so the exe dir is the run dir.
- Both saves write a temp file and then rename it (L540-546, L600-614). That breaks the hard link, so a run never writes into the source bin dir.
- So a **warm bin** = a copy of the bin plus `cache\native-pso.bin` and `cache\native-pso-recipes.bin` taken from one cold run of that same bin. S4-DRAFT's "harness change (A3/A8)" isn't needed. The design doc's `-SeedCache` switch doesn't exist in run-game.ps1, so don't use it.

## 2. Which bin

- **Preferred: native4bp** (0.4b/0.4c passed 2026-11-25: `build\agent16\pack\native4bp-bin`, MANIFEST C5181520…A690, fingerprint 39129c4c059be5f0, 0 missing draws in 3D attract). On nativefinal2, about 43 of 59 3D-attract draws are dropped before pipeline lookup because their shaders are missing. Their PSOs are never requested, so both the async and the pre-build effects would be undercounted.
- **Acceptable now: nativefinal2-bin** (fingerprint 1616ce65e973c583) as a first read. Re-run on native4bp before any default decision.
- A warm cache works only with the bin that wrote it. Recipes are keyed by the fingerprint, and the driver blob by the driver and adapter. Never reuse nativefinal2's warm cache for native4bp, or the reverse (PLAN-S3T4 §2).
- **P-C1 (M10, pso-native-r2-rating.md 5EA81E27): reference arm for the 2.2/2.3 PSO bin.** `build\agent16\psobin\native4bp-pso-bin` is native4bp plus diffs 2.2 and 2.3 r2. Any A/B of that bin must use **native4bp-bin (the matrix's n4bp60 arm) as the reference, never nativefinal2 / nat60**. Otherwise the 79 new pack shaders get mixed into the PSO result.
  - Both bins share fingerprint 39129c4c059be5f0 and the cache format, because pipeline_library.cpp is not a fingerprint input.
  - So both arms must start from the same cache state: both cold, or both seeded from the same unscored seeding run of native4bp.
  - Envs for the PSO bin's own rows: `LEGO_NATIVE_PSO_PREPARE_THREADS` (2.2), `LEGO_NATIVE_PSO_SAVE_UNLOCKED=1` and `LEGO_NATIVE_PSO_AUX_UNLOCKED=1` (2.3). All are default off.

## 3. Arms

Every arm uses the same route: `harness\routes\attract-long.txt`, `-Seconds 300 -GpuLog`. The env always includes `LEGO_NATIVE_PSO_STATS=1;LEGO_NATIVE_PSO_STATS_INTERVAL=10`.

| Arm | BinDir | Extra env | Question |
|---|---|---|---|
| C0 cold-off | bin (no `cache\`) | none | the baseline (= P1 pso-cold) |
| C1 cold-async | bin | `LEGO_NATIVE_PSO_ASYNC=1` | Does async remove cold hitches (= P5)? |
| W0 warm-off (#35) | warm bin | none | Does a seeded boot move creation to boot? |
| W1 warm-async | warm bin | `LEGO_NATIVE_PSO_ASYNC=1` | Is async still worth it once warm? |
| W2 warm-prep4 | warm bin | `LEGO_NATIVE_PSO_PREPARE_THREADS=4` | What does parallel replay do to boot cost? (This links to 2.2.) |

**Optional second round,** only if C1 shows pop-in:
- C1 with `LEGO_NATIVE_PSO_ASYNC_WAIT_US=0`;
- C1 with `LEGO_NATIVE_PSO_ASYNC_THREADS=1`.

**Building the warm bin:**
1. Copy the bin to `build\agent16\pso-async\warm-<bin>\`.
2. Copy `cache\native-pso.bin` and `cache\native-pso-recipes.bin` from the **first** (unscored) C0 run dir into its `cache\`.
3. Record the sha256s.

The game writes the cache at exit, and possibly during the run (the save thread). The source must therefore be a run that exited 0 with the log line `saved N startup pipeline recipes`.

**Order and n:**
- The NVIDIA driver keeps its own shader cache under the user profile. After the first boot of a bin, no run is truly cold. Don't clear that cache: it is user data and outside our rules.
- So "cold" here means **app cache cold**, and the plan works around the confound:
  1. **Run 0:** C0, unscored. It primes the driver cache and is the warm-bin source.
  2. **Then interleave:** C0 C1 W0 W1 | C1 C0 W1 W0 | C0 C1 W0 W1, i.e. n=3 per arm in an ABBA-style order, then W2 ×2.
- **Run time:** about 15 runs × ~6.5 min ≈ **100 min** of visible-desktop time.
- **Minimum useful set:** run 0, then C0 C1 W0 W1 ×2, ≈ 60 min.
- **Timing rule:**
  - Timing only counts on the visible desktop, which the Overseer opens with computer use. Hidden-desktop runs are functional only.
  - No builds may run during the window.
  - Minecraft must be closed, or else noted as host load.

## 4. Metrics, from game.log and runstats

| Metric | Source | Expected |
|---|---|---|
| hitches ≥50 ms, frames with ≥4 ms blocking compile, worst frame | `PSO frames:` (pipeline_stats.h L470) | C1 well below C0. W0 well below C0 |
| compile thread split | `PSO compiles by thread: present … async … other …` (L449) | in C1/W1, GetPipeline compiles move to `async` |
| async health | `PSO async: N posted, N ready, N failed, N skipped draws, N waits (ms), N timeouts` (L466) | failed = 0. Skips cluster at the first 3D and at area entries. Waits ≤ FRAME_US per 16.7 ms |
| per-minute `comp`, `block_ms`, `cfrm`, `hitch`, `skip` | `PSO minute` table (L477) | down with async or warm |
| boot cost of #35 | `Native GPU: startup pipelines loaded=… compiled=… failed=… resident=… elapsed_ms=…` (L301), plus time to the first frame (run.json/perf.csv) | W0: loaded+compiled > 0, failed = 0. Note elapsed_ms against the hitch time it saves. W2 elapsed_ms < W0 |
| cache acceptance | `pipeline cache … opened (N bytes)` vs `rejected by the driver`, plus `ignoring invalid or incompatible pipeline recipes` | W*: opened with N > 0, no rejects or ignores |
| frame pacing | runstats.py: fps, p99, 1% low (from the first frame + StatsWarmup) | C1 p99 and 1% low better than C0, with fps equal |
| draws actually drawn | a separate traced functional run (`LEGO_NATIVE_TRACE_DIR`): `draw_missing_*` per frame via `dump_post.py --trace-only`. Not timed: the trace has overhead | C1 = C0 except short skip bursts |

Use `PSO minute` and runstats for the comparison. FRAME_METRICS `pipeline_creations` falls to about 0 with async on because async compiles aren't counted there, so don't read it as a win.

## 5. What a functional row must show

**Every arm:**
- exit 0;
- no WER events 1000/1001/1002/1026 and no `.dmp`;
- the input script completes every step;
- the fingerprint line equals the bin's;
- no new WARN types compared with C0 (in particular no `invalidated by failed draw` and no `pipeline cache unavailable`).

**Async arms (C1, W1):**
- `PSO async` failed = 0, timeouts no higher than the C0 hitch count;
- skipped draws all within ≤0.3 s bursts at first entries, as in #33 row 3;
- `DrainAsyncPipelineJobs` at reset gives no hang. Reset is the menu/area reload, which the route crosses;
- a screenshot pair set against C0 at the same input steps. It must not show permanently missing one-shot render-to-texture content (portraits, UI renders) or flickering occlusion.

**Warm arms (W0, W1, W2):**
- a startup line with failed = 0;
- the cache opened, not rejected;
- recipes saved at exit;
- frames identical to C0 by eye (#35 is output-identical).

## 6. Decision rule

- **#35:** if W0 cuts hitches ≥50 ms by ≥50% against C0 and the boot cost (elapsed_ms) stays under about 3 s, then it is already the shipped behaviour for a second boot. The action is to document it and, optionally, to ship a portable seed (`native-pso-seed.bin`) next to the exe. Shipping a seed changes the release bin, so it needs a rating.
- **Async:** it isn't output-identical, so the most it can become is a **suggested setting with the default off**, the same treatment #33 got. That needs:
  - C1 to beat C0 on hitches and p99 with an interval excluding 0;
  - the functional row to pass;
  - **the user's eye review** of the pop-in screenshots (same form as #33 row 3: a) acceptable, b) keep off, c) something is wrong).
- **Stop rule:** any crash, hang, `failed` > 0 or permanently missing content stops the async arms.

## 7. Risks

- **Async pop-in or missing content:** draws are skipped while a compile is pending. One-shot render-to-texture draws can be lost for good. This is a design risk (agent6-async-pso-design.md §6), and the user has to sign off on how it looks.
- **CPU cost:** 2 extra compile threads (`_THREADS` 1..4). On a busy host, consider THREADS=1.
- **Shutdown and reset:** async jobs drain at `ResetDrawResources`. M10/A10 rated it SAFE when ON (agent10-batch2-review.md row 5, §5), but it has never been run on the 3D route with native4bp.
- **Warm-cache confound:** the driver's own cache makes every run after run 0 partly warm, so the C0 vs W0 difference understates a true first-install cold start.
- **A stale warm cache** after a driver update or a fingerprint change is rejected and rebuilt silently. Check the log lines.
- **Low PSO load on nativefinal2:** dropped draws hide it (§2). Re-run on native4bp before any decision.

## 8. Commands (for the Overseer's runner, visible desktop, not run by M16)

```powershell
$WS='<workspace>'
$B="$WS\build\agent16\pack\native4bp-bin"   # preferred (0.4c passed); nativefinal2-bin only as a first read. PSO-bin A/B: reference = this native4bp-bin (P-C1)
$base="LEGO_NATIVE_PSO_STATS=1;LEGO_NATIVE_PSO_STATS_INTERVAL=10"
$R="$WS\build\agent16\pso-async\runs"
# run 0 (unscored), then the arms; the Tag names the arm
powershell -NoProfile -ExecutionPolicy Bypass -File "$WS\harness\run-game.ps1" -BinDir $B -Seconds 300 -GpuLog -RunsRoot $R -InputScript "$WS\harness\routes\attract-long.txt" -Tag c0-prime -Env $base
powershell ... -BinDir $B     -Tag c1 -Env "$base;LEGO_NATIVE_PSO_ASYNC=1"
powershell ... -BinDir $WARM  -Tag w0 -Env $base
powershell ... -BinDir $WARM  -Tag w1 -Env "$base;LEGO_NATIVE_PSO_ASYNC=1"
powershell ... -BinDir $WARM  -Tag w2 -Env "$base;LEGO_NATIVE_PSO_PREPARE_THREADS=4"
```

If the Overseer wants it, M16 can wrap this as `RUN-PSOAB.cmd`, with the same refusals and pin checks as RUN-DUMP.cmd and a post script that parses the `PSO *` lines into one table.
