## 10. S4 items (for Agent 10)

Added ~05:05 at Agent 1's request. Nothing here is implemented yet. For each item there is a design note, a review checklist and a test plan. The rule applied is OFF by default unless the change is output-identical.

Line numbers refer to rexglue-sdk HEAD c5fe668; these files are clean against HEAD. Base hashes for a hash-guarded review:

| file | sha256 (first 16) | bytes |
|---|---|---|
| `src/graphics/d3d12/pipeline_cache.cpp` | 5DBED81F611E25B1 | 161,305 |
| `include/rex/graphics/d3d12/pipeline_cache.h` | 9322AD374BF4BBEC | 17,587 |
| `src/graphics/d3d12/command_processor.cpp` | 3AB3AA5360D4E987 | 269,215 |

| item | output-identical | files touched | user-visible effect | test plan |
|---|---|---|---|---|
| **(a)** per-thread DXBC translators for the gameplay creation threads | **Yes.** Each (shader, modification) gives the same DXBC; only the completion order changes. Cold first-view frames already differ run to run, because which draws get dropped depends on timing. So compare dumps and storage record sets, not frames. | `pipeline_cache.cpp`, `pipeline_cache.h` | Shorter cold first-view stalls, if translation is a large share of a burst (§11 arm B decides). The gain is at most ~9-10× on that share of a burst like the 67-miss shot. Single-miss frames, depth-only draws and warm-storage runs don't change. | §10.1 |
| **(b)** `pipeline_cache.cpp:564` fix (`original` → `needed`) | **Yes** for cold runs, which never reach the code, and in steady state. On a warm boot the first frames can be *more* complete. | `pipeline_cache.cpp` (1 line) | Only with a warm storage (players from their 2nd launch, or a seeded harness arm). Every stored pipeline is built before the guest resumes, so there is no creation tail at the first EndSubmission and no dropped first-use draws of stored pipelines. Today's cold harness runs don't change. | §10.2 |
| **(c)** non-blocking async mode | **No.** Draws stay dropped for several frames instead of one submission. It is a new cvar, OFF by default. | `pipeline_cache.cpp`, `pipeline_cache.h`; optionally `d3d12/command_processor.cpp` | Compile hitches become multi-frame pop-in: objects or effects are missing until they are built, and the shader-compile notice shows meanwhile. Depth-only (no-PS) creation still blocks. | §10.3 |

Suggested order:
- (b) with or before the first warm-storage arm, since it makes warm boots deterministic.
- (a) only if §11 arm B shows translation is ≥ ~40% of the 67-miss burst.
- (c) only as an opt-in, after the user has seen it on a visible desktop.

### 10.1 (a) Per-thread DXBC translators

**Today:**
- With async on, gameplay shaders are translated on the "D3D12 Pipelines" threads in `PrepareRuntimeDescriptionForQueuedCreation` (:3173-3237). That happens under the global `translation_request_lock_` (:3185), with the shared `shader_translator_` (:99-103) and the GPU thread's DXIL objects (:118-138). So translation is serial; only `CreateD3D12Pipeline` (:3272) overlaps.
- The GPU thread also translates in two places:
  - the sync path for depth-only draws (:955-1007, under the same lock);
  - draining the queue in EndSubmission (:796 → :3287-3309).
- Ucode analysis always runs on the GPU thread before a pipeline is queued (`AnalyzeShaderUcode`, `d3d12/command_processor.cpp:2592/2610`, h:77). So the `AnalyzeUcode` call at :3187 returns early, and the shared `ucode_disasm_buffer_` isn't really shared.
- The shader-level parts are already thread-safe. Storage load translates on up to 11 threads with per-thread translators (:384-403), and the shared state is guarded:
  - binding setup by `bindings_setup_entered_` (`pipeline/shader/dxbc.h:76`, `dxbc_translator.cpp:1237`);
  - layout UIDs by `EnterBindingLayoutUserUIDSetup` (`d3d12/shader.h:46`, used at :1141);
  - the layout maps by `layouts_mutex_` (:1180, h:327).

**Change:**
1. Each `CreationThread` (:3239) gets its own `DxbcShaderTranslator`, built with the same 8 constructor arguments as :99-103, and its own `StringBuffer`. It also gets its own DXIL objects, but only when `d3d12_dxbc_disasm_dxilconv` is set (as at :393-403).
   - Create them lazily on the first translation, so the 2 temporary storage threads of (b) pay nothing.
   - They die with the thread, which is joined at :181-183 and :693-696.
2. `PrepareRuntimeDescriptionForQueuedCreation` takes them as a parameter. The GPU thread keeps using the existing members. `shader_translator_` thus becomes GPU-thread-only; it also serves the default-modification queries at :855/:885.
3. Replace the global lock with a **per-shader claim**. That is a set of the `Shader*` currently being translated, guarded by a small mutex plus a condition variable and held via RAII.
   - A thread waits while another thread holds the claim for the same `Shader`. It then re-checks `is_translated()`, claims, translates, releases and notifies.
   - The claim is per *shader*, not per translation. Two modifications of one shader must not be translated at once, for two reasons:
     - The first translation writes the shader-level bindings and layout UIDs without a lock. A second translation skips that step via the atomic flags, so it could publish a usable pipeline while those fields are still being written.
     - The storage-index check-and-set plus the push to `storage_write_shader_queue_` (:3193-3203) happens per shader. Without the claim, one shader could be written to `.xsh` twice.
4. The GPU thread's sync path (:958-979, :985-1007) takes the same claim. At worst it waits for one translation of that shader, which can also happen today on the global lock.
5. Make `shader_storage_file_flush_needed_` (h:383) a `std::atomic<bool>`. Workers set it (:3197) and the GPU thread reads and clears it (:781-793) without a common lock. This race exists today.
6. Add a kill switch: a bool cvar, e.g. `d3d12_parallel_queued_translation` (restart required).
   - Off keeps today's code: shared translator and global lock.
   - Land it OFF and flip it ON after the tests below, as was done for S8/S11. Because the change is output-identical, ON by default is allowed.

**Review checklist:**
- Nothing off the GPU thread still touches `shader_translator_`, `ucode_disasm_buffer_` or `dxbc_converter_`/`dxc_utils_`/`dxc_compiler_`.
- The claim is released on every path, including translation failure, and waiters re-check after waking. A failed translation still ends up translated but invalid (`pipeline/shader/translator.cpp:657-671`), so nobody retries it.
- `GetRootSignature` (:3226) still runs outside any lock.
  - With `d3d12_bindless` (default true, `d3d12/command_processor.cpp:47`) it returns a fixed signature.
  - The bindful map has no lock, but several workers already call it concurrently today. That issue predates this change and is out of scope.
- Memory: up to 9 more translator instances. Storage load already creates up to 11 temporarily.

**Test plan:**

| # | run | pass |
|---|---|---|
| 1 | Cold attract route, kill switch off vs on (same bin), each with `--dump_shaders=<run>\dump` | Same file names; byte-identical files (sha256 per file) |
| 2 | The same runs: `.xsh` and `.xpso` | Same record *sets*: sort the 72-byte xpso records and key the xsh records by ucode hash. The order may differ |
| 3 | ABAB cold attract in a timing slot, no dumps | With attrib.py per §8 scene point, the P0+P1 excess on the 67-miss shot and the H0+26…37 cluster drops by roughly the §11 translate share. Single-miss rows don't change |
| 4 | On, with `d3d12_pipeline_creation_threads` = 1, 2 and default | No hang; no "Failed to translate queued" errors; same record sets |
| 5 | On, route stopped during the 67-miss burst (~H0+21) | Clean WM_CLOSE exit, no dump |

`dump_shaders` adds file I/O, so runs 1-2 are identity checks, not timing runs.

### 10.2 (b) The `pipeline_cache.cpp:564` fix

```cpp
while (creation_threads_.size() < creation_thread_original_count) {  // today: never true
while (creation_threads_.size() < creation_thread_needed_count) {    // fix
```

- **When it matters:** only when the storage has pipelines, i.e. a warm boot. Every harness run so far has been cold, so `pipeline_stored_descriptions` is empty and :555-729 is never reached.
- **A warm boot today:**
  - No extra threads start, and :685-715 (join the extra threads, then the blocking wait) is skipped.
  - The guest resumes (`rex_app.cpp:626-632`) while up to 9 stored pipelines are still being created on the regular threads. They are awaited at the first EndSubmission.
  - With async on, a first-use draw that hits one of them is dropped until it completes.
  - "Created N graphics pipelines … in X ms" (:718-723) leaves out that tail.
- **With the fix:**
  - needed = max(min(N, 12) − 1, 9) = 11 on this laptop (12 logical CPUs), so 2 temporary threads start.
  - The GPU thread drains the queue (:684), joins the temporary threads (:686-696), then waits for the busy ones (:697-714; `blocking` is true).
  - The INFO time then covers all of the creation.
- **`d3d12_pipeline_creation_threads=0` with a warm storage:**
  - Today every stored pipeline is created serially on the GPU thread (:677).
  - With the fix, 11 temporary threads create them and are all joined (shutdown_from = 0), so gameplay stays synchronous.
  - Boot gets faster and the output doesn't change.
- **Origin:** the same line is in `baseline\DimensionsRecomp\rexglue-sdk\src\graphics\d3d12\pipeline_cache.cpp:564`, so our patches didn't introduce it. Whether upstream Xenia has it is unverified.
- **Risk:** the fix turns on :685-715, which has never run in this fork.
  - I traced the handshake (`creation_threads_shutdown_from_`, the busy count and the completion event; :3245-3266, :3279-3282) and found no deadlock. A temporary thread finishes its current pipeline and exits at :3253-3254, and the event is only requested after the joins.
  - A warm-boot test is still required.
- **Kill switch:** not needed for a line that cold runs never reach. If Agent 10 wants one, gate the loop on a bool cvar (default on; off = today's behaviour).

| # | run | pass |
|---|---|---|
| 1 | Cold run, fixed vs unfixed | No "from the storage" lines; counters within noise |
| 2 | Warm boot (`-SeedXenos build\agent3\seed\devoff2-214`), fixed vs unfixed | Both INFO lines present, N ≈ 214. In the fixed bin the "Created" time is ≥ the unfixed one (it includes the tail) and the first frames after boot show no spike. pm ≈ 0 through the attract in both |
| 3 | 5 warm boots ending in WM_CLOSE, fixed | No hang between "Initializing shader storage" and the next guest log line; clean exits |
| 4 | Warm boot with `d3d12_pipeline_creation_threads=0`, fixed vs unfixed | Boots; the "Created" time is shorter with the fix |

### 10.3 (c) Non-blocking async mode

**Why async mode doesn't need the wait for correctness:**
- A draw whose pipeline is still null is dropped at record time (`d3d12/command_processor.cpp:2726-2729`), before `SetPipelineStateHandle` (:2749). So no recorded draw refers to an unbuilt pipeline.
- The wait in `PipelineCache::EndSubmission` (:795-813) therefore only limits pop-in to one submission.
- With async off the wait is required. Stored pipelines still in flight get recorded and are resolved at execute time, and `deferred_command_list.cpp:239-244` just skips `SetPipelineState` when the state is null.

**Change:**
1. Add a bool cvar, default false, e.g. `d3d12_async_pipeline_no_wait`, next to `d3d12_pipeline_creation_threads` (:58). It only takes effect with `async_shader_compilation` on and creation threads present.
2. In `EndSubmission` (:780-815), when the mode is in effect, keep the storage-flush part (:781-794) but skip both `CreateQueuedPipelinesOnProcessorThread()` and the wait.
3. Move today's wait (:795-813) into an `AwaitPipelineCreation()` helper. Call it at the top of `ShutdownShaderStorage` (:751), which `InitializeShaderStorage` also runs first (:224) before it bumps `shader_storage_index_` (:346).
   - Without it, workers that are still translating race with `storage_write_shader_queue_.clear()` (:761), with closing and nulling the storage files (:764-774), and with the index change.
   - `Shutdown` (:172-185) is fine as it is: threads stop at their next dequeue, and queued pipelines are deleted with a null state.
4. Optional: `CanEndSubmissionImmediately` (`d3d12/command_processor.cpp:4324-4326`) may return true during creation when the mode is on. `d3d12_submit_on_primary_buffer_end` (:2556-2561) then keeps ending submissions early. Leaving it unchanged is safe; it only means fewer early submissions while compiling.
5. Not covered: depth-only draws (no PS) are still created synchronously (:942-943, :1069-1071), so those stalls remain.

**Risks to review:**
- A one-shot render-to-texture pass drawn while its pipeline builds stays wrong. That already happens today, but only for one submission.
- Skipped memexport draws (GPU-written vertex data) can make effects that feed later frames glitch for longer.
- Pop-in length can't be measured today. An output-identical dropped-draw counter would measure it in both modes: a frame_stats counter at `d3d12/command_processor.cpp:2727`, printed in the slow-frame line.

| # | run | pass |
|---|---|---|
| 1 | Cvar off vs base, cold attract | Same code path by inspection; counters within noise; same storage record sets |
| 2 | Cvar on, cold attract | Frames > 250 ms at the §8 scene points drop to the non-compile residue (PRE, heavy, fence-wait and depth-only frames); pm unchanged |
| 3 | Cvar on, user on a visible desktop | The user judges the pop-in at the first 3D frame, the load transition and the 12.4k shot. Hidden-desktop runs can't judge this |
| 4 | Cvar on, route stopped during the 67-miss burst, 5 runs | Clean exit, no dump |
| 5 | Cvar on, with a warm storage | Same as warm with the cvar off (nothing to compile) |

## 11. Diagnostic run spec (§6 item 1), next-session slot

The run needs cvars only, no build. It fits Agent 8's slot or Agent 3's harness. The hidden desktop is fine, because the questions are about attribution, not timing.

**Questions**
- **Q1.** The PRE load frame (devoff2 r8274, devoffB r8130): is the GPU thread idle, meaning the cost is on the guest side (game code, file loading)? Or is it busy (texture loads, other emulation)?
- **Q2.** The cb ≈ 120 rows after the 67-miss burst (r9633 / r9534): how much of them is host-GPU fence wait?
- **Q3.** The 67-miss shot (r9630 / r9531): what share is DXBC translation and what share is PSO creation? This decides §10.1.
- **Q4.** The heavy rows (devoffB r9522-9529): guest side (idle) or GPU-thread throughput?

**Arms.** Both are cold (no seed) and use the same bin and route.

| arm | how | output-identical | answers |
|---|---|---|---|
| A | `-Arg 'slow_frame_log_ms=50'` | **Yes.** The counters are swapped every frame anyway (`d3d12/command_processor.cpp:253-258`), and the cvar only adds INFO lines (:265-283). The toml and its hash don't change. | Q1, Q2 and Q4. Q3 only as a remainder, because the async wait is untimed |
| B | `-Arg 'slow_frame_log_ms=50;d3d12_pipeline_creation_threads=0'` | **No.** All creation runs synchronously on the GPU thread, so no draws are dropped and stalls land in the miss row. Use it for attribution only, never as a perf comparison. | Q3: translate (:961/:989) and create (:1070) are timed per frame |
| C (optional) | toml `[log.levels]` `gpu = "debug"`, as the last table (Set-Toml appends) | Yes, but it logs more and changes the toml hash | Per-pipeline `Creating graphics pipeline with VS…, PS…` lines (:2718/:2722) with thread ids. Only needed if A and B leave Q3 open |

In Agent 8's runner the same cvars go in through `run-timing.ps1 -Cvar 'slow_frame_log_ms=50;d3d12_pipeline_creation_threads=0'`; its `common.ps1:94-101` turns them into `--name=value`.

**Setup**
- Bin: `build\agent2\devoff2-bin`, for comparability with the tie-break run. Its `rexgpu-xenos.dll` contains both cvar names (checked 04:50). If an S4 candidate OFF bin is used instead, also run arm A once on devoff2-bin to tie the results back.
- Command: `harness/run-game.ps1 -Seconds 420 -Warmup 60`, route `harness/routes/b-gate-menus-long.txt`, which ends the run at ~221 s (about H0+40). No `-SeedXenos`.
- Order: A, B, then A, B again if the slot allows; the repeat checks stability. Each run takes about 4.5 min, so 10-20 min in total.
- Collect: game.log, perf.csv, samples.csv, run.json and the `.xpso` size.

**Validity**
- The run reaches about H0+40: the H0 anchor row (2823 draws / 366,575 vertices) is present and the run gets to the 12.4k shot.
- Every perf.csv row > 50 ms has a slow-frame line within ±1 row whose ms matches within max(1 ms, 2%). Both measure from one swap entry to the next: perf.csv at XE_SWAP entry, and the slow-frame line at `IssueSwap` entry right after `Profiler::Flip`.
- At 50 ms the devoff2 and devoffB perf.csv files predict about 260-300 lines from the first 3D frame and 300-450 per run. That log volume is negligible.
- `.xpso` holds about 210-214 records in both arms; no crash; clean WM_CLOSE.

**Analysis:** run `python build\agent6\attract-stalls\slowframe_join.py <run dir>`.
- What it does:
  - finds the frame-number offset;
  - joins each line to its perf.csv row;
  - classes rows as in §1;
  - prints remainder = frame − idle − host-gpu wait − translate − create − texture load.
- In arm A, the remainder on P0/P1 rows is mostly the untimed async wait, i.e. compile time.
- Its decision hints:
  - **Q1:** idle ≥ 60% means the game side; neither warm storage nor S4 helps. Texture load ≥ 40% means uploads.
  - **Q2:** host-gpu wait ≥ 60% confirms GPU-side work: the driver's first use of new PSOs, or heavy passes.
  - **Q3 (arm B):** translate share = translate / (translate + create), over the 67-miss row and the row after it.
    - ≥ 0.4: do §10.1.
    - ≤ 0.2: skip it; creation dominates, and the remedy is warm storage (§7).
    - In between, (a) saves at most about share × burst.
  - **Q4:** high idle means the guest side; low idle with low waits means GPU-thread draw processing.
- Testing so far: `--selftest` builds synthetic arm A/B fixtures from the devoff2 perf.csv and checks the offset recovery, the joins and each verdict. The script hasn't seen a real slow-frame log yet.
