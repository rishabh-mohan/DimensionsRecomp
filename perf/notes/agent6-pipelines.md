# Agent 6: shader and pipeline compilation stutter (Task #5)

> **RESUME NOTE (01:40, written before the agy-grid relaunch). This is the CURRENT note; read it first.**
> - **State:** idle. No background tasks, no subagents. No live-tree edits since the S2 cut (23:15).
> - **First step after the relaunch:** wait for the new Agent 1's task block. Then, at Agent 1's **GO**, apply S3 native fix **(a)** `build/agent6/fix-a/fix-a.patch` (sha256 `71AEFF3D…`) to the live tree.
>   - Method: a hash-guarded copy of `build/agent6/fix-a/new/*`. No git writes. The exact commands are in the last section of [agent6-crash-triage.md](agent6-crash-triage.md).
>   - `rexlego/src/settings_registry.cpp`: `A3733700…` → `8BA19C5F…`
>   - `rexlego/src/settings_preferences.cpp`: `C78112AA…` → `9CBE6DBF…`
>   - Then re-verify the hashes and report to Agent 1, Agent 2 (S3 input) and Agent 10.
>   - Hunk 3 (`fix-a-commit.patch`) was NOT selected. Option (b) is parked. Agent 7 will help check native3 with (a): frontend on, no throw, bilinear present.
> - **Done since 23:00:**
>   - native-bin crash triage. The WER dump confirms the cause: an uncaught `Native setting is not registered: present_fsr_sharpness_reduction`. The SDK was built with FFX OFF, so those cvars don't exist, and the harness toml sets `native_settings_frontend=true`.
>     - The no-rebuild workaround is `--native_settings_frontend=false`. See [agent6-crash-triage.md](agent6-crash-triage.md).
>   - Fix A was made and checked on scratch copies (`build/agent6/fix-a/make_fix_a.py`, `verify_fix_a.py`).
>     - `git apply` on scratch copies needs `GIT_CEILING_DIRECTORIES`. Otherwise git finds the enclosing `C:/Users/<user>/.vscode/projects` repo and silently skips the paths.
> - **Dropped:** the native-bin capture kit. It would also need `native_settings_frontend=false` or a fixed build.
> - **Rules are unchanged:**
>   - At most 2 threads, pinned to CPU 5 (`0x20`), at Normal priority.
>   - One line per `@@to` message.
>   - During quiet windows: reading and editing only.

> **RESUME NOTE (20:55, session 2). Task #5 is DONE: `@@done 5` was sent at about 20:55. Task #12 (native AOT) is also done: `@@done 12` was sent at 20:31.**
> - **S1** was taken at 20:41:57 from the 20:15 state. The live tree is editable again, and every edit now belongs to batch 2.
> - **In S1:** items 1-3, plus the async prerequisites (`Lease::Release()`, `CurrentShaderOwners()`) and `pipeline_async.h`.
> - **Item 4:** I sent Agent 4 [draw-async.patch](../bench/agent6/draw-async.patch) at about 20:55, for Agent 4's batch 2.
>   - Patch sha256: `56D686EB…47A4`. It applies to draw.cpp sha256 `751C219E…0A99`.
>   - `git -C DimensionsRecomp apply --check` passed at 20:47.
>   - If draw.cpp changes before the patch goes in, `powershell -File build\agent6\draw_async\refresh.ps1` rebases the patch. It doesn't change any repo.
> - **Subagent:** `9c7c7090-460a-4028-a6c7-e57345530988` sent its final report at 20:49, and I killed it at 20:49. No subagent is running.
> - **My batch 2:** `gpu_native/pipeline_snapshot.h`, comment only (20:48). The new comment says the zero-fill is required (probe finding (d)).
>   - `save_lock_hold` rebuilt with the change: OK.
>   - A final syntax-only compile-one of `pipeline_library.cpp`, which includes all the headers, passed at 20:51: exit 0 in 13.8 s. The only warnings are the 6 `getenv` deprecations, 3 of them pre-existing.
>   - The `getenv` deprecation warnings stay, matching the 3 existing `getenv` uses.
> - **Probe:** done at 20:34. Results are in [d3d12_library_probe.md](../bench/agent6/d3d12_library_probe.md).
> - **21:24:** Agent 4 applied the async patch. The live draw.cpp sha256 is now `50AA3B1D…`, which matches `build/agent6/draw_async/draw.cpp`.
> - **21:48:** Agent 10 rated the patch (#25) SAFE at the default and SAFE-IF ON, on condition that exit goes through `Shutdown`. I sent Agent 10 the exit-path analysis: every native exit path either drains or ends in `TerminateProcess`/`ExitProcess`, and none of them runs static destructors while compile threads are alive.
> - **21:55, PSO runs:** the native close watchdog calls `TerminateProcess` 250 ms after `WM_CLOSE` (`legodimensions_app.h:409-419`), so the PSO exit summary is usually lost.
>   - I asked Agent 8 to create `<run>\cache\pso-stats.now` after the measurement window and before closing.
>   - The caveat is in [agent6-runspecs.md](agent6-runspecs.md).
> - **Next, if Agent 1 asks:**
>   - Counter runs on the first native ON build: P1 and P2 in [agent6-runspecs.md](agent6-runspecs.md).
>   - P3-P5 after the capture rounds.
>   - Optional cleanup:
>     - `build/agent6/prelink_smoke/real/` (about 0.68 GB, mine);
>     - the #12 intermediates under `DimensionsRecomp/rexlego/out/native-gpu/`. Those were released with #12, so ask Agent 1 first.
> - **Tests:**
>   - Command: `cmd /c "start /b /wait /affinity 20 powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent6\run_benches.ps1 -Only save_lock_hold,stats_off_cost,prepare_order_test,async_table_test"`. This pins the run to CPU 5. Logs go to `build/agent6/bench/<name>.txt`.
>   - **Never write `start ""` inside a PowerShell double-quoted `cmd /c "..."` string.** PowerShell turns `""` into `"`, so `start` opens a stray interactive cmd in a new window and the pipe never closes. This happened at 20:37, and I killed the stray process at 20:43.
> - **Encoding:** Windows PowerShell 5.1 `Get-Content -Raw` reads BOM-less UTF-8 as cp1252.
>   - At 20:45 a `Get-Content`/`Set-Content` round trip double-encoded every non-ASCII character in this file.
>   - I repaired it at 20:50. The backup is `build/agent6/agent6-pipelines.md.mojibake.bak`.
>   - Use `[IO.File]::ReadAllText` and `WriteAllText` with UTF-8, or `edit_file`.
> - **Compile check:** `$inc="-I$PWD\build\agent6\fake_include"; & .\env\compile-one.ps1 <file> -OutDir build\agent6\obj -SyntaxOnly -Db build\dev\compile_commands.json -Extra $inc`. Run it in-process, because `powershell -File` mangles `-Extra`. To pin it to CPU 5, first set `[Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr]0x20`.
> - **#12:** see the RESUME note in [agent6-native-aot.md](agent6-native-aot.md).
> - **#26 (Plume Windows SDK compat patch): DONE at about 22:28.** See the RESUME note and section 8 in [agent6-native-aot.md](agent6-native-aot.md).

## Batch 1 (listed 19:30 for the 20:15 cut-off): OFF by default, compile-checked, NATIVE_GPU=ON only

All five files are compiled only when `LEGODIMENSIONS_NATIVE_GPU` is ON (`rexlego/CMakeLists.txt:61` and `:107`). The OFF baseline build never sees them. Every new behaviour is behind an environment toggle that defaults to off.

| File | Change |
|---|---|
| `gpu_native/pipeline_snapshot.h` (new, 130 lines) | `SnapshotPipelineLibrary` (report #1). Autosave allocates and zero-fills the buffer **outside** the library mutex, and holds the mutex only for `GetSerializedSize` plus `Serialize`. If the library grew in between, it retries with a larger buffer. After the unlocked attempts it allocates under the lock, which is the old algorithm. The saved file is byte-identical. |
| `gpu_native/pipeline_stats.h` (new, 575 lines) | Opt-in PSO counters and timers (report #8). Covers: lookups (warm, library hit, miss); library-mutex waits; library loads; draw-path compiles, timed from the miss to `store()` on the same thread; auxiliary PSOs; the cache open; startup preparation; autosaves; async compiles (item 4); and per-present frame times with a per-minute table. |
| `gpu_native/pipeline_parallel.h` (new, 134 lines) | `RunOrdered` (item 3). Work runs on up to N threads, and commits run in index order on the calling thread, within a bounded window. |
| `gpu_native/pipeline_library.cpp` (739 lines) | `Save()` uses the snapshot. Stats hooks in Open, Prepare, `load()`, `store()`, auxiliary, Save and Frame. `Prepare()` uses `RunOrdered` only when `LEGO_NATIVE_PSO_PREPARE_THREADS` > 1. A counting cache keeps the stats working when the library is off. `StopPipelineLibrary` logs the summary once. New `LogPipelineStats()`. |
| `gpu_native/pipeline_library.h` (43 lines) | Declares `void LogPipelineStats();` and adds a comment about the threads toggle on `PreparePipelineLibrary`. |

Toggles. `StartPipelineLibrary` reads them once.

| Toggle | Default | Effect |
|---|---|---|
| `LEGO_NATIVE_PSO_STATS=1` | off | Counters and timers, plus a summary at exit (`StopPipelineLibrary`). |
| `LEGO_NATIVE_PSO_STATS_INTERVAL=<s>` | 0 (never) | Logs a one-line delta every `s` seconds, capped at 3600. Needs STATS. |
| `<exe>/cache/pso-stats.now` | absent | Create the file to log the full summary on demand. The present thread checks for it every 2 s and then deletes it. Needs STATS. |
| `LEGO_NATIVE_PSO_PREPARE_THREADS=<n>` | 1 (serial) | Runs startup preparation on `n` threads, clamped to [1, min(cores, 8)]. Commits stay in serial order, so the library, `warmed_` and the logs match the serial run. |

What differs on the default path (all toggles off):
- **Save:** the bytes are identical. Three things differ:
  - the mutex is taken twice per save instead of once;
  - the buffer may carry up to about 6% (+64 KiB) of headroom;
  - an allocation failure logs a warning and postpones the save. The old code threw `std::bad_alloc` on the save thread.
- **Hooks:** each `load()`, `store()` and present costs one relaxed atomic load plus one predictable branch. Measured at about 0 ns per `load()` and +0.8 ns per present (table below).
- **Everything else** runs as before: Open, the serial Prepare loop, its logs and its order.

Checks:
- **compile-one** (syntax-only, `build/dev` database): exit 0 at 19:11 for `pipeline_library.cpp`, which includes all four headers. The only warnings are 3 new `getenv` deprecations, the same kind as the 3 that were already there.
- **`bench/agent6/save_lock_hold.cpp`:** PASS, and the saved files are byte-identical. Worst mutex hold, old → new: 1288 → 279 ms at 512 MiB, 664 → 119 ms at 256 MiB, 90 → 37.5 ms at 64 MiB. Worst loader wait at 512 MiB: 1288 → 254 ms.
- **`bench/agent6/stats_off_cost.cpp`:** PASS. It runs 7 behaviour tests plus a cost bench (minimum of 7 runs):

  | Path | Before | Stats off | Stats on |
  |---|---|---|---|
  | `load()`: hash, mutex and map | 168.9 ns | 158.0 ns (no measurable overhead) | 354.3 ns |
  | present hook | 0.90 ns | 1.71 ns (+0.81 ns) | 94.7 ns |

- **`bench/agent6/prepare_order_test.cpp`:** PASS. It covers order, stopping, exceptions, the serial and edge cases, and move-only results. A model of Prepare commits identically on 1, 2, 4 and 8 threads, with and without removed recipes.


## Session 2: the rest of task #5

### Also in S1 (taken 20:41:57 from the 20:15 state): the async prerequisites (additive, nothing calls them yet)

The async subagent's two helpers were in the live tree at 19:58, so they are in S1:

| File | Change |
|---|---|
| `gpu_native/pipeline_creation_gate.h` | +8 lines: `Lease::Release()` unlocks a lease early. A second call, and the destructor afterwards, do nothing. |
| `gpu_native/shaders.h`, `shaders.cpp` | +4 and +6 lines: `CurrentShaderOwners()` returns the bindings snapshot in scope, or else the currently bound shaders, read under `g_registry_mutex`. It has no side effects. |
| `gpu_native/pipeline_async.h` | New and header-only. Nothing includes it yet. |

**Check (20:03):** compile-one syntax-only with the `build/dev` database. `shaders.cpp` exited 0 in 27 s, and `draw.cpp` (the main user of the gate header) exited 0 in 49 s. The only warnings are the `getenv`/`fscanf` deprecations that were already there. All three edited files are CRLF.

### Item 4: async PSO compile (OFF by default)

**Status (20:55): done.** My subagent implemented it and sent its final report at 20:49; I reviewed it. `async_table_test` passes: the subagent ran it at 20:05 and I re-ran it at 20:44 (PASS: 17 checks, 10 with the toggle off and 7 with it on, 0 failures; log in `build/agent6/bench/async_table_test.txt`). The draw.cpp part is a patch for Agent 4, who owns draw.cpp. I sent it at about 20:55. The full design, including the default-identical argument and Agent 4's apply steps, is in [agent6-async-pso-design.md](agent6-async-pso-design.md).

| Piece | Where | Who applies it |
|---|---|---|
| In-flight table, compile pool, per-frame wait budget, settings, owned copy of the desc | `gpu_native/pipeline_async.h` (new, header-only, 466 lines, in S1) | me (done) |
| Hooks in `GetPipeline` and `ResetDrawResources` | [draw-async.patch](../bench/agent6/draw-async.patch): 7 hunks, +48/−14, against draw.cpp sha256 `751C219E…0A99` (still the live file at 20:36) | Agent 4 |
| Test | [async_table_test.cpp](../bench/agent6/async_table_test.cpp), run with `run_benches.ps1 -Only async_table_test` | me |

**Toggles** (read once, through a function-local static):

| Toggle | Default | Range | Effect |
|---|---|---|---|
| `LEGO_NATIVE_PSO_ASYNC=1` | off | | Turns async compile on |
| `LEGO_NATIVE_PSO_ASYNC_THREADS` | 2 | 1-4 | Compile threads |
| `LEGO_NATIVE_PSO_ASYNC_WAIT_US` | 2000 | 0-1,000,000 | Longest wait for one miss |
| `LEGO_NATIVE_PSO_ASYNC_FRAME_US` | 4000 | 0-1,000,000 | Total wait allowed per window of about 16.7 ms |

**With the toggle on,** a `g_pipelines` miss in `GetPipeline` goes like this:
1. It first checks `g_async_pipelines`. If the key is already in flight, it waits for that compile instead of starting another.
2. Under the creation-gate lease it checks again. It then copies the desc and everything it points to (`OwnedPipelineDesc`), and takes shared ownership of the bound shaders (`CurrentShaderOwners()`).
3. It releases the lease and posts the compile to the "PSO compile N" pool.
4. It waits up to `WAIT_US`, within the per-window `FRAME_US` budget:
   - if the PSO is ready in time, the draw uses it;
   - otherwise `GetPipeline` returns null, and the existing "pipeline unavailable" path skips the draw. This is counted as `OnAsyncSkippedDraw`.
5. The job ends in `FinishPipeline()`, which is the old post-create code moved unchanged. It emplaces the result under `g_pipeline_mutex`.

`ResetDrawResources` drains the pool first, and clears the table after `g_pipelines.clear()`.

**With the toggle off,** the code is identical in effect:
- no runtime or threads are created;
- each miss pays one static-bool test plus two `async ? Find(key) : nullptr` tests;
- `FinishPipeline()` runs the same statements in the same order;
- draining a null runtime returns at once.

**My review (20:25-20:35):**
- **Teardown order is safe.** `device.cpp:923-949` calls `ResetDrawResources` (:941), which drains first. Only after that do `ResetShaderResources` and `StopPipelineLibrary` (:949) run.
  - I re-checked this at 20:54, after another agent's 20:48 edit to device.cpp moved the code up one line.
  - The other `StopPipelineLibrary` call (:876) is on the init-failure path, before any draw can run.
  - A job takes no device lock. `SetNativePipelineStencilReference` is lock-free, and `ResetDrawResources` drains before it takes `g_pipeline_mutex`. So draining while `Shutdown` holds `g_mutex` and the recording lock cannot deadlock.
- **Shader lifetime is safe.** `DestroyNativeShader` (`shaders.cpp:837`) erases the registry entry and retires a `shared_ptr`. The job's `owners` keep the `ShaderResource` and its variants alive, and `createGraphicsPipeline` never reads guest memory. The bank shader caches are reset only inside `ResetDrawResources`, after the drain.
- `SetNativePipelineStencilReference` (`draw.cpp:906`) only sets a field on the new PSO.
- **One benign race:** a draw that joins the very first compile can see a null runtime and skip without waiting. That is the same outcome as an exhausted budget.

**The real-driver probe supports the 2-thread default:** driver compiles scaled 2.27x on 2 threads, and more threads than free cores gave nothing (below).

**In-game check:** P5 in [agent6-runspecs.md](agent6-runspecs.md), async on vs off on the same seed.
- `block_ms` and `cfrm` should fall to about 0.
- The cost shows up as the async skipped-draw count. That is geometry missing for a frame or more per new PSO, so look at the screen as well as the numbers.

**Notes for Agent 4** (from the subagent's final report, 20:49):
- **Applying.** Run it from the workspace root as `git -C DimensionsRecomp apply ../bench/agent6/draw-async.patch`. Plain `git apply` from the root silently skips the file, because the root sits inside the outer `C:/Users/<user>/.vscode/projects` repo.
- **If draw.cpp has changed by then:** `powershell -File build\agent6\draw_async\refresh.ps1` regenerates the patch against the live file, then re-runs `apply --check` and `-fsyntax-only`. It changes no repo.
- **With the toggle on**, skipped draws take the existing null-pipeline path, including `FailActiveQueries` and LongProbe `draw_pipeline_unavailable` events.
- **Counting compiles:** `FRAME_METRICS pipeline_creations` does not count async compiles. Use the PSO stats lines "PSO async" and "compiles by thread" instead (design §4 and §6).

### Real-driver probe (20:34): what it changes

Full results are in [d3d12_library_probe.md](../bench/agent6/d3d12_library_probe.md). The run was an NVIDIA MX570 on driver 32.0.16.1088, with a 9.70 MB library of 800 PSOs.

- **Item 1 is confirmed.**
  - The autosave lock hold drops from 6.25 to 3.65 ms (−42%). Linearly that is about 346 → 202 ms at the 512 MiB cap.
  - What is left under the lock is the `Serialize` copy itself, at about 2.6 GB/s.
- **The zero-fill is required, not cosmetic.**
  - On this driver, `Serialize` leaves some bytes unwritten. Into a 0xCD-filled buffer its output differs from the old zero-filled vector; into zeroed memory it is identical.
  - `pipeline_snapshot.h` allocates a new value-initialised (zeroed) buffer on every save and on every retry, so the file stays byte-identical.
  - **Done at 20:48 (batch 2, comment only):** the `Allocate()` comment now says so, so nobody turns it into an uninitialised or reused buffer.
- **A synchronous miss is 30 to 600 times dearer than a library hit:**
  - a library load takes about 0.6 ms (p99 2.9 ms);
  - a driver compile takes about 20-50 ms for small shaders and about 220-400 ms for large ones.
- **Create scaling:** 2.27x on 2 threads. **Load scaling:** 1.07x on 2 threads and 1.36x on 4.
- **`Serialize` concurrency:** loads go through unaffected; stores wait up to 115-204 ms. A store between `GetSerializedSize` and `Serialize` makes the serialize fail with `E_INVALIDARG`.
- **The debug layer reports nothing unexpected.**

### Measuring "FPS improves the longer you play"

- **Turn it on:** `LEGO_NATIVE_PSO_STATS=1`, optionally with `LEGO_NATIVE_PSO_STATS_INTERVAL=10`.
- **On demand:** create `<exe>/cache/pso-stats.now`. The full summary is logged within 2 s.
- **Output in `game.log`:**
  - a `Native GPU PSO stats, last 10 s:` line every 10 s;
  - a 10-line summary at exit;
  - the `PSO minute` table, one row per minute since the first frame (up to 4 hours).

  The exact patterns are in [agent6-runspecs.md](agent6-runspecs.md).
- **The columns that decide it, per minute:**
  - `comp`: driver compiles on the draw paths;
  - `block_ms`: compile time that blocked a draw path;
  - `cfrm`: frames with 4 ms or more of blocking compiles;
  - `hitch`: frames of 50 ms or more;
  - `fps`.
- **How to read them:**
  - **If PSO compiles cause the symptom:** `comp`, `cfrm` and `hitch` are high in the first minutes and on first entry to an area, then decay towards 0. `fps` rises as `comp` falls, and a warm second run (P2) starts where the cold run (P1) ended.
  - **If `fps` keeps rising after `comp` is already about 0,** the cause is elsewhere: texture or asset streaming, guest-side warm-up, or allocator growth.

### In-game A/B plan

- **The matrix for Agent 8's runner** is in [agent6-runspecs.md](agent6-runspecs.md):
  - P1: cold;
  - P2: warm, seeded from P1;
  - P3: cache off;
  - P4a and P4b: prepare threads 1 and 4, on a recipes-only seed;
  - P5: async, later.
- **Manual variant:** the first vs the second visit to one level in one session.
- **Order:**
  1. **The OFF baseline (emulated Xenos)** has no native PSO path, so it has no counters. Task #5 has nothing to run there.
  2. **The first native ON build** (about 21:30, with stub runtime shaders and a stub temporal bank): run P1 and P2 as functional checks on the hidden desktop. The counts are valid there; the frame times are not.
  3. **After capture rounds** make the first-level route capture-complete ([agent6-native-aot.md](agent6-native-aot.md) §6.2), the user starts the timing matrix. Before that, black surfaces skew both fps and the PSO counts.

### Other stutter sources seen this session

- **FSR3 context creation takes 1,403 ms** on the real device (the #12 link check). If the native path recreates the FSR3 context on a resize, a quality change or a device reset, each of those costs a 1.4 s hitch. Check the context-creation call sites before the A/B (not my file).
- **There is no runtime DXC.** The prelink smoke test confirms that every variant is linked at build time ([agent6-native-aot.md](agent6-native-aot.md) §7).

### Not done, and why

- **Variant B of report #1** (`Serialize` without our mutex) was not done. The probe shows that the runtime already lets `LoadGraphicsPipeline` through during a `Serialize`, but stores wait inside the driver for up to 115-204 ms. A store between `GetSerializedSize` and `Serialize` also makes the serialize fail with `E_INVALIDARG`.
  - **So variant B would need a split lock:** loads shared, stores and `Serialize` exclusive.
  - **It would only help loads** that queue on our mutex behind a `Serialize`. That is about 3.6 ms at 9.7 MB and about 200 ms at the 512 MiB cap, after the snapshot change.
  - **Do it only if** the in-game `pso_stats` lock-wait counters (`lock_wait_ns`, `max_lock_wait_ns`, `lock_waits_over_1ms`) show those waits.
- **Report #2** (striped library loads) is deprioritised. Loads scaled only 1.07x on 2 threads and 1.36x on 4, so the runtime mostly serialises them anyway.
- **Report #6** (auxiliary compiles outside the mutex) was not done.
  - It is still valid in principle: an auxiliary compile under `mutex_` blocks every load and store for 20-400 ms.
  - But it only matters if auxiliary PSOs are created during gameplay. The stats count them (`aux_compiles`, `aux_compile_ns`), so the first native runs will show whether that happens.
- **Report #4** (negative cache, mostly in draw.cpp) and **report #7** (the physical-size index) have not been started.

**Session 1 status (12:24): PARTIAL, analysis only.** At 12:24 Agent 1 stopped all builds and edits. I changed no source file (both repos are still clean) and ran no benchmarks or fixtures. Everything below comes from reading the code at `perf/opt` @ `127e04b`. The opportunities are ranked by expected stutter win, and each one has a verification step for when a toolchain exists.

Paths are relative to `DimensionsRecomp/rexlego/src/gpu_native/` unless stated otherwise.

## Answers to the five questions

| Question | Answer | Evidence |
|---|---|---|
| Is a PSO ever compiled synchronously on the render or game thread? | **Yes.** On a `g_pipelines` miss, `GetPipeline` drops `g_pipeline_mutex` and calls `device->createGraphicsPipeline(desc)` inline. That runs on whichever thread is dispatching the draw: the recording thread for direct draws, or a preparation worker for batched work (`PrepareFullDrawChunk` and `QueueNativeDrawBatch` → `PostNativePreparation`). Draws that are not eligible for batching (temporal-input candidates, long probe, pass profiling) always take the recording path. There is no async path and no skip-draw fallback. Startup prepare and auxiliary PSOs also compile synchronously. | draw.cpp:1731-1736 (main), draw.cpp:1958 (temporal), draw.cpp:2759, draw.cpp:4275-4300, draw.cpp:4906-4907, draw.cpp:4917-4918, pipeline_library.cpp:169, pipeline_library.cpp:268 |
| Is there a persistent on-disk PSO cache? | **Yes, two layers.** (1) An `ID3D12PipelineLibrary` blob at `<exe>/cache/native-pso.bin`, capped at 512 MiB. The driver/adapter key is implicit: `CreatePipelineLibrary` rejects a blob from another driver or adapter, the code then starts with an empty library, and the next save replaces the file. (2) Portable recipes at `cache/native-pso-recipes.bin` (keyed by build fingerprint) plus seeds `../native-pso-seed.bin` and `native-pso-seed/*.bin`. At startup these are recompiled or reloaded, and the first 512 PSOs stay resident in `warmed_`. `LEGO_NATIVE_PSO_CACHE=0` turns the cache off and `LEGO_NATIVE_PSO_PRECOMPILE=0` turns off startup prepare. The cache is skipped under RenderDoc. | pipeline_library.cpp:33, :96-137, :143-225, :179-180, :307-334; device.cpp:867-868 |
| Are duplicate in-flight compiles deduplicated? | **Yes, per `PipelineKey`.** A `PipelineCreationGate` lease plus a re-check makes the second thread wait and then reuse the result (fixture: `tools/gpu-aot/test_pipeline_creation_gate.cpp`). It is **not** deduplicated across different `PipelineKey`s that produce the same D3D12 desc. In that case the second compile is wasted and its `StorePipeline` fails harmlessly on the name collision. | draw.cpp:409, :1585-1590; pipeline_library.cpp:337-338 |
| Are startup pre-warm and DXC link results cached? | **Pre-warm:** yes, through the library plus `warmed_`. **DXC:** fully at build time. `tools/gpu-aot/prelink_shader_cache.cpp` links every (shader, spec-mask) variant offline and embeds the result. `CompileSpecConstantLib` and `LinkSpecConstantLib` are referenced only by the prelink tool, and there is no runtime DXC. The archives are decompressed once (`call_once`) and pre-warmed at device init. `createShader` only wraps the bytecode and is cached per resource variant. | device.cpp:840; shaders.cpp:651-673; shader_archive.cpp:406-440 |
| Does PSO creation use worker threads? | **Only incidentally.** Misses compile on whichever preparation worker or recording thread hits them, and different keys can overlap because the global lock is released around the compile (draw.cpp:1726-1731). There is no dedicated compile pool. **Startup `Prepare()` is single-threaded.** | draw.cpp:1726-1733; pipeline_library.cpp:156-181 |
| Is cache lookup cheap? | **At draw level, yes.** A hit costs one global `std::mutex` plus an `unordered_map` find (about 30-field FNV-style hash, field-wise equality), and the per-thread `PreparedValue` skips even that when the key repeats. The library level only runs on a miss: `PipelineName` (XXH3-128 over VS+PS DXIL, `swprintf`, `wstring`) is computed before the lock, which is good. **The real lock problem is that the library's single `mutex_` is held across slow work:** `Serialize` of a blob up to 512 MiB, auxiliary driver compiles, and every `LoadGraphicsPipeline`. See items 1, 2 and 6. | draw.cpp:222-291, :1581-1584; draw_preparation.h:14-32; pipeline_library.cpp:49-90, :227-271, :380-399 |

## Ranked opportunities

### 1. Autosave holds the library mutex across allocation, zero-fill and `Serialize`. On by default; pure efficiency.
- **Where:** pipeline_library.cpp:380-399 (`Save`), triggered from `Frame()` at :273-287 (present thread, device.cpp:2091), which spawns a detached save thread.
- **What is slow:** Under `mutex_`, `Save` calls `GetSerializedSize()`, then `data.resize(size)` (heap allocation, zero-fill and first-touch page faults for up to 512 MiB), then `Serialize`. Every draw-time `load()` (:230) and `store()` (:251) takes the same `mutex_`. The save fires after `kQuietBeforeSave` with no stores (:278-279), which is exactly when the player is entering new content. Any PSO miss during that window waits for the whole serialize, even if the library itself could satisfy it in under 1 ms. `SaveRecipes()` (:353-360) also calls `recipes_.TakeSnapshot()` under the lock. I did not check whether that deep-copies bytecode.
- **Change (output file byte-identical):** allocate and pre-touch outside the lock, and retry if the library grew in the meantime:
  ```cpp
  std::vector<uint8_t> data; SIZE_T size = 0;
  for (;;) {
    { std::lock_guard lock(mutex_);
      if (!unsaved_) return;
      size = library_->GetSerializedSize();
      if (size <= 1024 || size > kMaxLibraryBytes) { unsaved_ = 0; return; }
      if (size <= data.size()) {
        if (FAILED(library_->Serialize(data.data(), size))) return;
        saved = unsaved_; unsaved_ = 0; ++stats_.saves; break; } }
    data.resize(size + size / 8);   // allocation + page faults outside mutex_
  }
  // write data.data(), size bytes (not data.size())
  ```
  Only the `Serialize` memcpy stays inside the lock. A stronger variant (B) drops `mutex_` around `Serialize` entirely and relies on the runtime's internal synchronization (item 2). Gate variant B, because it also has to recount `unsaved_` for stores that land during the serialize.
- **Risk:** low. Keep the exact `Serialize(ptr, size)` call; only the buffer has slack. Check whether `TakeSnapshot` copies.
- **Verify:** bench `bench/agent6/save_lock_hold.cpp` measures lock-hold time and a concurrent waiter's latency for 64, 256 and 512 MiB, old vs new. In game, add `serialize_ms` and `lock_wait_ms` to `PipelineLibraryStats` and log them at `Stop()` (:297). Then compare a new-area walk with saves happening.

### 2. Library loads are serialized behind the global `mutex_`. Pure efficiency, but gate it first because of threading risk.
- **Where:** pipeline_library.cpp:227-247 (`load`). `LoadGraphicsPipeline` runs at :240 while holding `mutex_`, which is also held by `store` (:251-253), `CreateAuxiliary` (:262-269, across a full compile) and `Save` (:385-399).
- **What is slow:** When several preparation workers miss at once (scene entry), they load from the driver library one at a time, and each load waits behind any in-progress store, auxiliary compile or serialize.
- **D3D12 contract:** the `ID3D12PipelineLibrary` remarks say *"The pipeline library is thread-safe to use, and will internally synchronize as necessary, with one exception: multiple threads loading the same PSO … should synchronize themselves."* The draw-level gate does not cover two keys that share one desc (see the dedup answer above), so a per-name lock is still required.
- **Change:**
  ```cpp
  { std::lock_guard lock(mutex_); /* warmed_ lookup/erase, as now (:231-239) */ }
  std::lock_guard name_lock(load_stripes_[std::hash<std::wstring>{}(name) & 63]);  // same-PSO rule
  const bool hit = SUCCEEDED(library_->LoadGraphicsPipeline(name.c_str(), &desc, IID_PPV_ARGS(&pipeline)));
  std::lock_guard lock(mutex_);
  if (hit) { Record(name, desc); ++stats_.hits; return pipeline; }
  ++stats_.misses; return nullptr;
  ```
  `CreateAuxiliary`'s load should use the same stripe.
- **Risk:** medium. It relies on the runtime and driver internal locking, and vkd3d-proton implements the library separately. Ship it behind `LEGO_NATIVE_PSO_CACHE_CONCURRENT=1` (default off), soak-test it on NVIDIA, AMD, Intel and Proton, then flip the default.
- **Verify:** a contention bench with N threads doing sleep-modelled loads, global lock vs striped. In game, compare the `pipeline_creation_ms` sum per scene entry with the cache warm (all misses served by library loads).

### 3. Async PSO compile with skip-draw fallback. Biggest potential win; behaviour change, **OFF by default**; needs the draw.cpp owner.
- **Where:** draw.cpp:1726-1754 (`GetPipeline` miss) and :1958 (temporal).
- **What is slow:** with a cold library (first run, driver update, new content), every miss is a full driver compile on the recording or preparation thread. That is the "FPS improves the longer you play" symptom (`native-performance-vsync-20261010.md`, open item 2).
- **Change sketch:** add `LEGO_NATIVE_PSO_ASYNC=1`; when it is unset the code path is untouched.
  - On a miss, after variant resolution, copy the desc and everything it points to (`slots`, input elements, render-target formats) into a job that holds shared ownership of the VS/PS `RenderShader` owners.
  - Post the job to a 2-4 thread pool and mark the key pending, so the gate lease is released without duplicate posts. Return `nullptr`, which takes the existing "no pipeline" handling that draw.cpp:1608-1610 and :1742 already use, so the draw is skipped.
  - When the compile finishes, emplace the result under `g_pipeline_mutex`.
  - Device teardown (draw.cpp:5531-5545) must drain the pool before it clears anything.
  - Optional middle ground: compile synchronously while this frame's compile budget is under X ms, and defer only after that.
- **Risk:** geometry is missing for one or more frames per new PSO (popping, or flashes in shadow and transparency passes), plus lifetime bugs if the shader owners are not held. That is why it stays opt-in.
- **Verify:** a Simpsons and new-area run with the setting on vs off. `pipeline_creation_ms` on the recording and worker threads should drop to about 0, and "Native slow draw" lines (draw.cpp:454) should disappear. Count skipped draws.

### 4. Failed lookups are never cached, so they are retried and logged on every re-resolve.
- **Where:**
  - draw.cpp:1608-1610 (missing VS/PS) and :1737-1742 (D3D12 rejected the PSO; the log is capped at 16): neither path emplaces anything.
  - shaders.cpp:658-662: a `FindDxil` failure is not stored in `variants`.
  - shader_archive.cpp:432: `REXLOG_WARN("…shader cache miss…")` has no cap.
- **What is slow:** `PreparedValue` only remembers each thread's last key. Every time a failing key comes back, the thread repeats the gate acquire, three variant probes, `FindDxil` and one log line (formatting plus sink I/O). A rejected desc also repeats a **full driver compile attempt**, which stays invisible once the 16-line log cap is reached.
- **Change:**
  - In my files (log-only): cap shader_archive.cpp:432 like the other warnings (an atomic counter below 16, or once per hash).
  - In draw.cpp (owner, behaviour-adjacent): negative-cache a rejected key, invalidated when `g_pack_generation` changes (a published pack can supply the missing shader) or on device reset. Restrict it to non-transient HRESULTs.
- **Risk:** low for the log cap. The negative cache must not hide shaders that appear later.
- **Verify:** in a long session, count `pipeline_creations` vs unique keys and count miss log lines.

### 5. Startup `Prepare()` is single-threaded. Startup time on a cold cache; gate it, default 1 thread.
- **Where:** pipeline_library.cpp:156-181, called at device init (device.cpp:867-868).
- **What is slow:** For each recipe (up to 8192 local recipes plus seeds) it runs, one at a time: `Describe` → `LoadGraphicsPipeline`, otherwise `CreateGraphicsPipelineState` + `Store`. After a driver update the blob is rejected (:122-129), so every recipe becomes a full compile on one thread. D3D12 PSO creation is free-threaded.
- **Change:** `LEGO_NATIVE_PSO_PREPARE_THREADS=N` (default 1 = today's loop, capped at 4).
  - Phase 1 (serial): dedup names across all sources and build the (name, desc) list. Each entry needs its own `inputs` storage, because `Describe` writes into scratch.
  - Phase 2 (parallel): load-or-create into `results[i]`, and stop on device removal.
  - Phase 3 (serial, in recipe order): `Store`, counters, `prepared`, and `warmed_` admission (the first 512 in order, as now).
- **Risk:** driver memory spikes with concurrent compiles. Admission order is kept by Phase 3.
- **Verify:** the existing log line `startup pipelines loaded= compiled= failed= resident= elapsed_ms=` (:222-224), with `cache/native-pso.bin` deleted (cold) and present (warm), for N=1 vs N=4.

### 6. `CreateAuxiliary` compiles while holding `mutex_`.
- **Where:** pipeline_library.cpp:262-270. Callers: depth_resample.cpp:63 and native_overlay_gpu.cpp:103.
- **Change:** do the load under the stripe from item 2, run `CreateGraphicsPipelineState` with no lock held, then take `mutex_` only for `Store`.
- **Risk:** low.
- **Win:** only matters if those callers run lazily during gameplay; I did not verify that (see "Didn't get to read"). Otherwise it only affects startup.

### 7. `FindShaderPhysicalSize` scans the whole table on every shader adoption.
- **Where:** shader_archive.cpp:259-268, called by `AdoptShader` at shaders.cpp:318 on first adoption and on re-adoption after `InvalidatePlacementShader` (:247).
- **What is slow:** each call scans the whole built-in microcode table (an estimated ~19k entries, from an earlier read) and takes `g_pack_mutex`. That is part of the level-load first-use cost; it does not run per draw.
- **Change:** build a lazy static index of the maximum size for each (`containerHash`, `stage`), the same way `FindShaderTextureMask` builds its table (:282-290), and keep the pack scan under the lock. Results are identical.
- **Risk:** low.
- **Win:** small, microseconds per adoption.
- **Verify:** `bench/agent6/physical_size.cpp` (linear vs indexed on a synthetic 20k-entry table), plus an equality check over all built-in hashes.

### 8. Instrumentation to add first. Cheap, and needed to confirm items 1, 2 and 6.
Add `lock_wait_ms` in `load()` and `store()`, plus `serialize_ms` and `save_bytes` in `Save()`, to `PipelineLibraryStats`, and log them in the `Stop()` line (:297).

## Looked at and rejected

| Idea | Why rejected |
|---|---|
| `PipelineKeyHash` and equality (draw.cpp:222-291) | About 30 multiply/xor steps and field compares. `PreparedValue` already skips repeated keys. No evidence it matters. |
| `PipelineName` (pipeline_library.cpp:49-90): drop the `swprintf`/`wstring` | XXH3-128 runs at multiple GB/s, so tens of KB is microseconds. It runs only on a miss and before the lock. The string is a persistent key, so its format must not change. |
| A cache for runtime DXC compile/link | There is no runtime DXC: everything is prelinked at build time. |
| `createShader` per variant (shaders.cpp:663) | Wraps bytecode only, no driver work, and is cached per resource. |
| A first-use archive decompress hitch | Uses `call_once`, and all archives are pre-warmed at device init (device.cpp:840). |
| `FindPixelShaderContainers` (shader_archive.cpp:270-280) | Only runs on a debug filter change. |
| Variant resolution under `g_pipeline_mutex` (draw.cpp:1591-1607) | Holds the lock for microseconds of work, and only on a miss. |
| `PipelineRecipes::Read` recomputing `PipelineName` per recipe (pipeline_recipes.h:283) | Startup only, microseconds each. |

## Benches and tests to run once a toolchain exists
- Existing fixtures, built standalone with `-I DimensionsRecomp/rexlego/src` into `build/agent6/`:
  - `tools/gpu-aot/test_pipeline_creation_gate.cpp`
  - `test_pixel_shader_filter.cpp`
  - `test_shader_constant_range.cpp`
  - `test_shader_texture_usage.cpp`
- A new recipes round-trip test: stub `native_gpu_build_info.h` and provide `PipelineName`.
- Benches to write in `bench/agent6/` (report the median of 5 or more runs):
  - `pipeline_key_lookup`: copy `PipelineKey`/`PipelineKeyHash`, 1-8 threads, hit path.
  - `pipeline_name`: 4, 16 and 64 KB bytecode.
  - `physical_size`.
  - `save_lock_hold`.
  - `library_load_contention`.
- In-game numbers to compare:
  - the `pipeline cache hits/misses/stored/saves` line (pipeline_library.cpp:297)
  - the `startup pipelines … elapsed_ms` line
  - `g_draw_timing.pipeline_creations` and `pipeline_creation_ms`
  - "Native slow draw" lines
- Then compile-check every edited file with Agent 3's harness.

## Didn't get to read
- `native_worker.cpp`: which thread does the recording. That decides whether a miss stalls the guest/game thread directly or only the native recorder.
- plume's `D3D12GraphicsPipelineCache` and `createGraphicsPipeline` (rexglue-sdk thirdparty). The sources were not found within 6 directory levels; the submodule is probably not initialized. I still need the exact load → compile → store order and whether plume holds its own lock around the compile.
- The body of `GetTemporalPipeline` (draw.cpp:1769-1980). If temporal PSOs use a different root signature, `Record` (pipeline_library.cpp:346) skips them, so they are never pre-warmed.
- When `depth_resample.cpp:63` and `native_overlay_gpu.cpp:103` run (startup vs lazy).
- `PipelineRecipes::TakeSnapshot` cost (deep copy?) and pipeline_library.cpp:420-499 (start/stop wrappers, RenderDoc skip), not re-checked this pass.
- The exact `g_shaderMicrocodeEntryCount` (in generated sources).
- The full text of `docs/native-gpu-known-bugs.md` and the LOTR audit.
