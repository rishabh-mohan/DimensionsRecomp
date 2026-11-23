# Agent 6, session 2: design notes for task #5 (PSO stutter) and the task #12 plan

This file is a working note. I wrote it at the 16:55 pause so the design survives an agy-grid restart. The final write-up goes in `agent6-pipelines.md` (Session 2).

Paths are relative to `DimensionsRecomp/rexlego/src/gpu_native/` unless stated otherwise. Files use CRLF and 2-space indent. CMake lists the .cpp files explicitly, so I add **no new .cpp**. Headers are globbed (CONFIGURE_DEPENDS). The toolchain is C++23, clang with the MSVC STL.

## Facts the design depends on
- **plume `D3D12GraphicsPipeline` ctor:**
  - It calls `cache->load(desc)`. On null it runs `CreateGraphicsPipelineState`, then `cache->store(desc, d3d)` (only if d3d is non-null), on the same thread and in that order.
  - So compile time = the gap from a load miss to the store call. I measure it with a thread_local timestamp.
- **ID3D12PipelineLibrary is free-threaded** (MS spec). The one exception: don't load the same name concurrently. So a parallel Prepare with distinct names is fine.
  - Store and Serialize are synchronized inside the driver, so "variant B" (Serialize without `mutex_`) probably gains little. The prober data decides.
- **draw.cpp, Agent 4's file** (line numbers as of 16:40):
  - Globals: `g_pipeline_mutex` :417, `g_pipeline_creation` :418, `g_pipelines` :420.
  - `GetPipeline` is :1593-1770. It releases the lock around `device->createGraphicsPipeline(desc)` at :1745-1751.
  - `ResetDrawResources` is :5545. It does `g_pipelines.clear()` then `g_pipeline_creation.ClearAfterDrain()`.
  - `g_draw_timing` is a thread-selected macro. **Async jobs must not touch it.**
- **shaders.cpp:**
  - `ShaderBindingsSnapshot{owners[2] shared_ptr<void>, addresses[2]}`.
  - `ShaderBindingsScope` sets the thread_local `t_shader_bindings`.
  - `CaptureShaderBindings()` has side effects, so it can't be used in GetPipeline.
  - `ShaderResource::variants` is never erased, so holding an owner keeps its variant shaders alive.
- **device.cpp:**
  - Shutdown order: `ResetDrawResources` :938, `ResetShaderResources` :940, `StopPipelineLibrary` :946.
  - `PipelineLibraryFrame()` runs every present (:2091), even when `g_library` is null.
  - `CurrentDrawPreparation()` is declared in device.h:93.

## Task #5 items
### 1. Save lock hold (report #1). New `pipeline_snapshot.h` (variant A)
- **API:**
  - `PipelineSnapshot{Status kNothing/kFailed/kNoMemory/kCopied; unique_ptr<uint8_t[]> data; size, wanted; retries; lock_us, max_lock_us, copy_us}`.
  - `SnapshotPipelineLibrary(mutex, query, copy, unlocked_attempts=3)`. `query()` returns the size under the lock (0 means stop). `copy(dst, size)` runs under the same lock hold.
- **Allocation:**
  - Allocate outside the lock with `new (std::nothrow) uint8_t[n]()`, zero-filled like the old vector.
  - Capacity = wanted + wanted/16 + 64 KiB. Free the old buffer before reallocating.
  - Attempts ≥3 allocate under the lock (the old behaviour), so a save is never skipped.
- **Save():**
  - Calls SaveRecipes, then the snapshot.
  - The query keeps the old `!unsaved_` and bounds logic (`size<=1024||size>kMaxLibraryBytes` sets `unsaved_=0` and returns 0).
  - The copy calls `Serialize`, then `saved=unsaved_; unsaved_=0; ++stats_.saves`.
  - kNoMemory: warn, set `last_store_=now`, keep `unsaved_`.
  - It writes exactly `snapshot.size` bytes with the same tmp+rename and the same log text.
- **Bench:** `bench/agent6/save_lock_hold.cpp` compares the old algorithm with the snapshot at 64/256/512 MiB. It measures the lock hold and a concurrent loader's max and p99 wait, and checks byte identity and the growth/retry path.

### 2. Instrumentation (report #8). New `pipeline_stats.h`
- **Gating:** `LEGO_NATIVE_PSO_STATS=1`. When off, `load`/`store`/`CreateAuxiliary` dispatch `g_pso_stats ? X<true> : X<false>` with `if constexpr` timing, so the cost is one predictable branch.
- **Counters:**
  - warm/library hits, misses, lock waits, stores;
  - compiles by thread (recording / preparation / async), with a stall histogram at 1/4/16/64 ms;
  - aux hits and compiles;
  - save lock holds, serialize, write, bytes and retries;
  - async posted / failed / ready / skipped / waits;
  - startup: Open bytes, read and create time, and Prepare loaded/compiled/failed/load/compile/elapsed/threads.
- **Per frame:** `Frame()` runs on present through `PipelineLibraryFrame` (`if (g_pso_frame_hooks)`). It keeps a frame-stall histogram, the worst frame, and a per-minute ring (cap 240) of fps, hitch frames ≥4 ms, blocking compiles, compile ms, hits, misses and skipped.
- **Output:**
  - `LEGO_NATIVE_PSO_STATS_INTERVAL=<s>` logs deltas.
  - `LogPipelineStats()` gives the summary on demand, and it is printed at Stop.
- **Library off:** `CountingPipelineCache` (load counts a miss, store counts a compile) is registered when stats are on but the library is off (cache=0, capture layer, Open failed).
- **Bench:** `bench/agent6/stats_off_cost.cpp` measures ns/call for the baseline, stats off, and stats on.

### 3. Parallel startup Prepare. New `pipeline_parallel.h`
- `RunOrdered<Result>(count, threads, window, work(i, stop), commit(i, result))`:
  - threads ≤1 runs serially;
  - otherwise it processes windows of `window` items, with workers claiming items from an atomic `next`;
  - commits happen in index order on the caller, so `Store`, `prepared`, the first-512 `warmed_`, progress logs and counts match the serial run.
- **Worker:** builds its own `inputs`, then Describe, then LoadGraphicsPipeline, else CreateGraphicsPipelineState, else `removed = FAILED(GetDeviceRemovedReason())` and stop.
- **Toggle:** `LEGO_NATIVE_PSO_PREPARE_THREADS=N` (default 1, clamped to 1..min(8, hw)).
- **Test:** `bench/agent6/prepare_order_test.cpp`.

### 4. Opt-in async PSO compile with skip-draw. New `pipeline_async.h`, plus a draw.cpp patch for Agent 4
- **Header contents:**
  - `AsyncPipelineCompile`: Finish, WaitFor(budget µs), Succeeded.
  - `AsyncPipelineTable<Key,Hash>`: Find, Begin, End, Clear, Size. The caller holds `g_pipeline_mutex`.
  - `AsyncPipelinePool`: Post, Drain, a stopping dtor, and threads named "PSO compile N".
  - `OwnedPipelineDesc<Desc>`: deep-copies inputSlots, inputElements and specConstants.
- **Glue in pipeline_library.cpp:** `AsyncPipelineCompileEnabled()`, `PostAsyncPipelineJob()`, `WaitForAsyncPipeline()` (budget = clamp(frame_left, 0, wait_us)) and `DrainAsyncPipelineJobs()`.
- **Toggles:** `LEGO_NATIVE_PSO_ASYNC=1`, `_ASYNC_THREADS` (2), `_ASYNC_WAIT_US` (2000), `_ASYNC_FRAME_US` (4000).
- **`pipeline_creation_gate.h`:** add `Lease::Release()` so the async path drops the lease once `Begin` is visible.
- **`shaders.h/.cpp`:** add `ShaderBindingsSnapshot CurrentShaderOwners()`, side-effect free: `t_shader_bindings` if set, else `g_bound_shaders` under `g_registry_mutex`.
- **draw.cpp patch (send to Agent 4; do not edit):**
  - include `pipeline_async.h`, and add `g_async_pipelines` next to `g_pipelines`;
  - add `FinishPipeline()`, a helper for rejection/stencil-ref/MRT logging that the sync path also uses, unchanged;
  - in GetPipeline: when async, a `pending()` wait after both finds; capture owners before variant resolution; at the compile site `Begin`, post a job (create, FinishPipeline, emplace under the lock, End, Finish), Release the lease, unlock, Wait, relock, then return found-or-nullptr (skip draw);
  - `ResetDrawResources`: call `DrainAsyncPipelineJobs()` before taking the lock, and `g_async_pipelines.Clear()` after `g_pipelines.clear()`.
  - Workflow: copy draw.cpp to `build/agent6/draw_async/`, edit it, and `git diff --no-index` the result into `bench/agent6/draw-async.patch`. The design write-up goes in `perf-notes/agent6-async-pso-design.md`.
- **Side effects to document:** missing geometry for ≥1 frame, FailActiveQueries, LongProbe events, possible loss of one-shot RTT content, FRAME_METRICS `pipeline_creations` excludes async, and failed compiles re-post.
- **Test:** `bench/agent6/async_table_test.cpp`.

## Task #12 plan (J1 in `perf-notes/SESSION2-jobs.md`)
- **(a) Stub banks** in `DimensionsRecomp/rexlego/out/native-gpu/stubs/`:
  - temporal-bank and float-blend-indices-bank `.obj` files (`clang -c -x c NUL -o X.obj`) plus a `.cpp` with the declarations the consuming TUs expect;
  - `lego-dxil-cache.cpp`, `runtime-cache.cpp`, `runtime-linked-dxil-cache.cpp`, and a stub FidelityFX dll;
  - `lego-microcode-index.cpp`. Its path is hard-coded in CMake as `rexlego/out/native-gpu/`, so the stub gets a `#pragma message` STUB marker.
  - Send Agent 2 the flags: `-DLEGODIMENSIONS_NATIVE_GPU=ON -DLEGO_TEMPORAL_SHADER_BANK=… -DLEGO_FLOAT_BLEND_INDICES_BANK=… -DLEGO_NATIVE_SHADER_CACHE=… -DLEGO_NATIVE_RUNTIME_SHADER_CACHE=… -DLEGO_NATIVE_FIDELITYFX_RUNTIME=… -DLEGO_NATIVE_BINARY_CACHE=OFF -DLEGO_HOST_DXC_EXECUTABLE=<WinSDK dxc.exe>`.
  - Ask Agent 2 for the FidelityFX-SDK gitlink at eee08db and to confirm the `rex::renderdoc` target.
- **(b)** Feasibility report `perf-notes/agent6-native-aot.md`.
- **(c)** Real inputs. The recipe is in `DimensionsRecomp/tools/gpu-aot/COLLABORATION.md` lines 212-343: XenosRecomp at 339af41 plus the lego patch, DXC 1.9.2609, and `gpu-shader-extract`.
- **(d)** First native boot and capture plan.
- **Game data** (Agent 3, 16:58, read-only, verified 23/23):
  - disc: `game\disc`, 21 files, 7.55 GB, including Default.xex and the TU23 Default.xexp;
  - TU23: `game\tu23`, 11 files, 1.9 GB (Default.xexp, PATCH/PATCH0-2/DLC8 .DAT/.HDR).
  - Only Agent 3 writes under `game/`.
