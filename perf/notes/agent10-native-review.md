# Agent 10: native-only always-on review (#21)

Started 20:10, written 20:25 on 2026-11-21. This is a read-only review. I edited no other agent's files.

**Scope:** the always-on changes that only the `NATIVE_GPU=ON` build compiles, at their default settings. Each change gets a verdict: SAFE, SAFE-IF (with its condition) or UNSAFE.

**Evidence:**
- File:line references point at the live tree, in `DimensionsRecomp/rexlego/src/gpu_native/` unless another path is given.
- The diffs against `baseline/DimensionsRecomp` are in `build/agent10/b2/`, one `.diff` per file. Agent 6's files have the prefix `a6-`. `x-logging-2010.diff` is the 19:54 logging delta.

## Summary

| Owner | Changes reviewed | SAFE | SAFE-IF | UNSAFE |
|---|---|---|---|---|
| Agent 4 (draw path) | items 1, 4, 5, 6, the SSE2 `#else`, the new headers, and the default-off paths | 7 | 0 | 0 |
| Agent 5 (uploads) | items 1-3, split into 6 changes | 6 | 0 | 0 |
| Agent 6 (pipelines) | batch 1 at OFF defaults, plus the async prerequisites | 10 (+1 not compiled) | 0 | 0 |
| Agent 7 | `build/agent7/batch1/perf-csv-rows.patch` | 1 | 0 | 0 |

## 0. Logging question (answered 20:12)

The logsz probe used the 19:54 headers. `new.obj` was built at 19:54:26, after `logging/api.h` (19:54:07) and `logging/macros.h` (19:54:15). So the measured cost (+66-67 B per log site, a compare of two loads) is the cost of the 19:54 version.

My macros.h source read was taken at 19:45, before that edit. I re-read the 19:54 delta (`build/agent10/b2/x-logging-2010.diff`):
- `LogLevelMayBeEnabled` (the floor check) now runs first.
- `BindLogLevelFloor` runs only inside the should_log branch. This is Agent 12's design.
- The NOISY macro checks the floor before `log_noisy`.

The verdict is unchanged: **SAFE**. With `log_level_gate` off the floor stays 0, so the gate never suppresses a line. Nothing changes for Agent 2.

Minor note: `lvl` is now evaluated up to 3 times (4 times in NOISY). Every current call site passes a pure level expression, so this is harmless.

## 1. Agent 4: default-path items (`perf-notes/agent4-draw-path.md` §S2)

Diffs: `draw.cpp.diff`, `queries.cpp.diff`, `long_probe.h.diff`, `draw_cached_flag.h.diff`, `draw_log_throttle.h.diff`, `state_call_diagnostic.h.diff` and `draw_state_shadow.h.diff`. `queries.h` has no diff.

| # | Change | Verdict | Evidence |
|---|---|---|---|
| 1 | `QueryDrawScope` skips the mutex when `active_queries == 0` (queries.cpp) | **SAFE** | Declared as `std::atomic<size_t> active_queries` (queries.cpp:40). The fast path is an acquire load (:230), and the count is re-checked under `mutex` (:234). `IssueQuery` holds `HostDevice::LockRecording()` for BEGIN and END (:95). On the inline path, draws also record under LockRecording, so every BEGIN/END happens-before the next draw's load. The count is exact at every transition: BEGIN increments only if the slot was absent or inactive (:113-115); END decrements only if the map still holds this query (:122-125); ReleaseQuery (:210-213); Reset stores 0 (:310-311); CreateQuery inserts inactive entries (:77, :89, `active=false` at :26); FailActiveQueries sets only `failed` (:298-305). In threaded mode, `IssueQueryQueued` (:142-157) is ordered by `kRecorderBarrier` under full preparation (comment at :146). These are the same edges baseline relied on. |
| 4 | `Select_g_*()` TLS accessors (draw.cpp) | **SAFE** | `t_draw_preparation` is written only by the `DrawPreparationScope` constructor and destructor (device.cpp:763-770, an RAII exchange and restore). The scopes open at draw.cpp:4368, 4438, 4458, 4889 and 5639. All of these are outside `DispatchDraw` (2455-~3667) and `BindNativeDrawVertexBuffers` (881-905), and a nested scope restores before it returns. The no-argument `Select_g_*()` forwards to the one-argument overload, so each `thread_local` still exists exactly once (draw.cpp:131-145, 317-322, 425-430). The `[&]` lambdas run synchronously, and the deferred `RecordNativeCommand` lambda captures `mark_writes` by value. |
| 5 | `TakeLogBudget` log throttle (new `draw_log_throttle.h`) | **SAFE** | draw_log_throttle.h:18-20 does a relaxed load, then a `fetch_add` while under budget, so exactly the first N lines print under any concurrency. Call sites: draw.cpp:2746 (budget 32), 2844 (16) and 3638 (8). The only behaviour change is that nothing re-prints after the 2^32 wrap, which STATUS decision 5 accepted. |
| 6 | `CachedProcessFlag` (new `draw_cached_flag.h`) | **SAFE** | draw_cached_flag.h:19-28 holds a constant-initialised `std::atomic<uint8_t>`, where 2 means unread. Threads that race on the first read each call `Read` and store the same value, because every `Read` is process-constant: `NativeTextureTimingEnabled` (textures.cpp:1479-1489, static const), `PortraitProbeEnabled` (hooks_portrait.cpp:57-63), `LongProbeDirectorySet` (long_probe.h:14-26, static path), `NativeFullDrawPreparationEnabled` (native_recording.cpp:497-503, static const, used only by the opt-in elision) and `ReadElideStateCalls` (environment). Uses: draw.cpp:437-438, 2481 and 4760, plus DrawTimer and ConstantTimer, where the `&&` operands were reordered but have no side effects. long_probe.h is included by 7 TUs, and a COMDAT static per instantiation is fine. |
| - | `SnapshotDevice` SSE2 `#else` (draw.cpp, around 3861, 3921 and 3955) | **SAFE** | It is dead in the native ON build: `build/dev/compile_commands.json` compiles draw.cpp with `-march=x86-64-v3`, so `__AVX2__` is defined and the original AVX2 text ships. At v2 it is equivalent. The AVX2 equal loop (3926-3929) and the SSE2 loop over `[begin*2, end*2)` in steps of four 16-B lanes both work at 64-B granularity, and a static_assert keeps sizes to 64-B multiples. `_mm_stream_si128` needs only 16-B alignment, where AVX2 needed 32-B. Agent 4's `test_snapshot_simd.py` reports byte-identical output and identical v3 codegen. |
| - | Default-off paths: state-call elision, the diagnostic columns, SwapHook pacing | **SAFE** | `InlineDrawStateShadow` returns nullptr when `LEGO_NATIVE_ELIDE_STATE_CALLS` is unset. With both arguments null, `SameDraw*` returns false, so `setIndexBuffer` and `SetNativeBlendFactor` are always called. The diagnostic columns run only under `if (state_calls)`. `PaceFrameBeforeLock` (draw.cpp:5344, device.cpp:1855) returns before taking any lock when `LEGO_NATIVE_UNLOCKED_PACING` is unset (reviewed in #18 D6). |
| - | New headers `draw_log_throttle.h` and `draw_cached_flag.h` | **SAFE** | Header-only. They contain no dynamic initialisation and start no threads, and every state variable is a constant-initialised atomic. |

**Concurrency answer for Agent 1.** Only `active_queries` depends on memory ordering. Its ordering comes from `LockRecording()` (queries.cpp:95), not from the inline path being single-threaded. In threaded mode the recorder barrier provides it instead. On x86 a locked RMW is globally visible, so this is no weaker than baseline's check under the lock. `TakeLogBudget` and `CachedProcessFlag` are correct under any concurrency. The TLS accessors are per-thread by construction.

**Already in baseline, not new:** in full-preparation plus queue mode, `ReleaseQuery` runs without the recording lock (queries.cpp:202-203). It can race a BEGIN that re-inserts the entry through `queries[address]`. Baseline has the same race. This is for the record only, not a batch-1 blocker.

**Owner's tests relied on:**
- The fixtures pass 9/26, the same failing set as base.
- `run_patched.py` passes 3/3, with 8/8 mutants caught.
- The snapshot SIMD output is byte-identical.
- The benches are in §S2.4.

## 2. Agent 5: upload items 1-3 (`perf-notes/agent5-uploads.md` RESUME block)

Agent 5 did not respond, so I reviewed this from the code and Agent 5's differential tests in `build/agent5`. A research subagent helped; I spot-checked the riskiest claims myself (marked "verified").

Diffs: `textures.cpp.diff` (+21/-5), `buffers.cpp.diff` (+11/-23), `vertex_upload.h.diff` (+45), `texture_volume_upload.h.diff` (+209), `texture_upload_source.h.diff` (+19/-1), and `texture_scratch.h.diff` (a new file).

| Item | Change | Verdict | Evidence |
|---|---|---|---|
| 1 | `CopyTexture2DBlocks`, tiled runs (texture_volume_upload.h:163-212, 264-287) | **SAFE** | By the TiledOffset2D math (a copy of SDK util.cpp:424), each run starts aligned to `kRunBytes` and its bytes are contiguous, so the endian XOR (at most 3) stays inside the run. The head and tail blocks keep CopyBytewise's per-byte check (:183), and every run checks `offset+kRunBytes>size` (:194). Memory access uses only loadu/loadl/storeu/storel. Writes stay within `row_pitch*h <= dst.size()` (:273). |
| 1 | `CopyTexture2DBlocks`, linear rows and fallback (:216-253, 271-279) | **SAFE** | Rows are bounds-checked (:231, :237). Unaligned offsets and tails use the exact per-byte XOR loop (:246-249). The fallback is the unchanged baseline call with depth=1. It handles block sizes that are not a power of 2, w or h of 0, endian values above 3, pitch smaller than the row, a short destination, and the int32/u64 overflow guards (`TiledRowsFit`/`LinearRowsFit`). The 8-B and 16-B block sizes now go through `CopyTiledRows<16>` or the linear path rather than the old code. The test covers them. On failure only the bool matters: textures.cpp:2294 returns and the buffer is discarded. |
| 2 | Decode scratch without zero-fill (new texture_scratch.h; textures.cpp:2195-2203; texture_volume_upload.h:294-305) | **SAFE** | Verified: `TextureDecodeScratch` (texture_scratch.h:18-39) leases a grow-only `thread_local` block of up to 16 MiB (:16, :54). A nested call on the same thread gets its own block, because `leased` is checked at :20, so a nested decode cannot alias. Also verified: `ZeroTextureRowPadding` (:294-305) zeroes `[r*pitch+row_bytes, (r+1)*pitch)` for each row, clamped to the level, and then the tail. The 512-B alignment gaps are zeroed at textures.cpp:2202. The subagent checked that each of the three copiers (2D, volume and alpha4, texture_alpha4_upload.h:28-33) writes exactly the remaining bytes on success. So all `upload_size` bytes are deterministic before the XXH3 hash (:2301) and the staging copy (:2321). Every `return false` drops the buffer. A zero `upload_size` is rejected at :2188. |
| 2 | Capture vectors default-initialised (texture_upload_source.h:14-24, 44-46, 66) | **SAFE** | The vectors are resized and then read only by `CopyTextureUploadSpan` (textures.cpp:473-479), which memcpys the whole span or returns false (the capture is dropped). All 3 callers (:1319, :2143, :2399) use that reader. |
| 3 | `converted` buffer not zeroed (buffers.cpp:484-503) | **SAFE** | `ByteSwapElements` writes all `length` bytes (whole elements plus the memcpy tail) before `ApplyVertexByteOrder` permutes within that range. `length == 0` behaves the same because the memcpy is guarded. |
| 3 | `SwapUploadElementBytes` SIMD (vertex_upload.h:78-113; buffers.cpp:151-158) | **SAFE** | The loop guards (`size-offset >= 32` and `>= 16`) cannot overrun either buffer, and access is loadu/storeu only. Every chunk starts at a multiple of 16, so it holds whole 2-B or 4-B elements, and the scalar tail is the baseline code. The only caller passes element size 2 or 4, with source and destination in separate buffers. |

**ISA dispatch:** chosen at compile time only, through `#if __SSSE3__` / `__AVX2__`, with every intrinsic under its guard (texture_volume_upload.h:8-10, 152, 172, 196, 222, 238; vertex_upload.h:7-12, 82-98). x86-64-v2 gets the SSSE3 path. rexlego/CMakeLists.txt:835 already requires at least v2, so there is no new ISA requirement.

**Does the byte-identical claim hold against the tests? Yes, for all three items.**
- **Item 1, `test_untile`:** it compares the live `CopyTexture2DBlocks` against `CopyTextureVolumeBlocks`, which is unchanged from baseline. Destinations are pre-filled with random bytes, so a missing or stray write would show. It passed on v3, v2 and sse2: 3,964,537 copies, of which 713,682 succeeded and 3,250,855 failed identically. Verified: the exes were built at 17:57-17:59, and the only header change after that (18:12) is +18/-0 lines appending `ZeroTextureRowPadding`. `git diff --no-index --numstat` against `build/agent5/pre-item2/texture_volume_upload.h` shows a single hunk `@@ -286,4 +286,22 @@`. So the test covers the shipped copier.
- **Item 2, decode-poison (18:19):** it runs after the last item-2 edit (18:13:53), extracts the live loop, and kills both mutants. The scratch class itself has no test, but I read it, above.
- **Item 3, `test_byteswap`:** its reference matches the removed baseline lines exactly, and it includes the live `vertex_upload.h` and `ByteSwapElements` body. The exes (18:40:46-18:41:01) postdate the last edit (18:39:18).
- **Compile check (20:24):** Agent 5's `cc-*.log` runs were syntax-only, so I ran a full object compile (`-c`, Release entry from `build/dev/compile_commands.json`, through `env/compile-one.ps1`, one process at a time). textures.cpp exited 0 in 26.2 s with 23 warnings, the same count as Agent 5's syntax-only run. buffers.cpp exited 0 in 20.8 s with 15 warnings. Every warning is a `getenv` deprecation. The objects are in `build/agent10/b2/obj/` and the summary is in `build/agent10/b2/cc-a5-full.log`. So 20:50 is not the first codegen of these TUs.

**Not blockers, for Agent 1 and Agent 5:**
- No runtime OFF switch exists for any of the three items. The emergency reverts are:
  - item 1: put back the baseline `CopyTextureVolumeBlocks(..., 1, block_bytes, pitch, endian_xor, cb)` call at textures.cpp:2280-2286;
  - item 2: change `TextureDecodeScratch decoded(upload_size)` (:2195) back to `std::vector<u8> decoded(upload_size)`, which leaves the zeroing harmless;
  - item 3: restore the scalar body of `ByteSwapElements` in buffers.cpp.
- Each uploading thread now keeps a block of up to 16 MiB for its lifetime, by design.
- `gpuaot-tex-run` (18:49) has 4 failures and no before-run. They look unrelated to this diff: an undeclared `bloom`, an extraction "substring not found", and a capture-filter case outside the edited region. In `gpuaot-after`, every upload test passes, and the 2 failures match `gpuaot-before`.
- No in-game A/B of the per-upload XXH3 stream exists. The textures.cpp call-site arguments are checked only by reading.

## 3. Agent 6: batch 1 at OFF defaults (`agent6-pipelines.md` "Batch 1" and "Session 2")

All of these files compile only with `LEGODIMENSIONS_NATIVE_GPU` (rexlego/CMakeLists.txt:61 and :107). `pipeline_library.cpp`, `pipeline_stats.h` and `pipeline_parallel.h` were last written at 19:11:02.

| Change | Verdict | Evidence |
|---|---|---|
| `pipeline_snapshot.h` (new): `SnapshotPipelineLibrary` | **SAFE** | It allocates a zero-filled buffer outside the mutex, using `new (std::nothrow) uint8_t[n]()` (:60) with capacity `wanted + wanted/16 + 64 KiB` (:56). It runs `query()` under the lock (:87). If the size grew beyond capacity, it loops (:72-77), and the last pass allocates under the lock, which is the old algorithm. `copy()` always gets exactly the size `query()` returned, so the file is byte-identical (owner's `save_lock_hold.cpp` PASS). An allocation failure returns `kNoMemory` (:82, :114) instead of throwing. |
| `pipeline_library.cpp` `Save()` | **SAFE** | Save() (:556) calls the snapshot at :562. The `unsaved_` semantics are preserved: the size bounds of 1024 and `kMaxLibraryBytes` reset it (:569-570, :578). On `kNoMemory` it logs a warning and sets `last_store_` (:586-592), which postpones the save. Before, the detached thread threw `bad_alloc` here, so this is strictly safer. |
| Stats hooks in `load()`, `store()` and auxiliary | **SAFE** | Each dispatches on `pso_stats::Enabled() ? X<true> : X<false>` (:307, :311, :321). The `<false>` bodies match the old bodies line for line. With stats off, `CreateUncached` is the old direct call. Cost with stats off: the owner's `stats_off_cost.cpp` PASS shows `load()` going from 168.9 to 158.0 ns and present gaining +0.81 ns. |
| `Prepare()` and the `RunOrdered` path | **SAFE** | `PreparationThreads()` returns 1 when `LEGO_NATIVE_PSO_PREPARE_THREADS` is unset or empty, and clamps any value to [1, min(hw, 8)] (:109-115). The parallel path runs only when `threads > 1` (:249), and so does its log line (:207-209). The serial path (:255) commits `PrepareOne<stats>` in the old order. `PrepareOne` still checks `GetDeviceRemovedReason` after a failed compile (:445). Owner's test: `prepare_order_test.cpp` PASS. |
| `pipeline_parallel.h` (new) | **SAFE** | It is a template only, with no globals. The thread pool is local to `RunOrdered` (:85) and joined on every path (:101-103). It is reached only through `PrepareParallel` (pipeline_library.cpp:249) when `threads > 1`. |
| `pipeline_stats.h` (new) | **SAFE** | `g_enabled{false}` (:40), and `Enabled()` is a relaxed load (:43). `ReadEnvironment()` (:544-550) stores false when `LEGO_NATIVE_PSO_STATS` is unset, empty or "0". The `pso-stats.now` poll (:526-535) is inside `OnFrameAt`, and `f.trigger` stays empty unless `Configure` ran. The inline globals (`g_totals`, `g_startup`, `g_frames`, `g_log_mutex`) have no initialisation side effects, and the header starts no threads. |
| `StartPipelineLibrary`, frame and stop hooks | **SAFE** | `ReadEnvironment()` runs first. `Configure` and the counting cache run only when stats are on (:665-687). The frame hook calls `OnFrame` only when stats are enabled (:695). On stop, `g_counting_cache.exchange(false)` is false when stats are off, so the cache is not reset (:719), and the summary is gated (:720, :728). `LogPipelineStats` is gated too (:735-736). |
| `pipeline_library.h` | **SAFE** | It adds only the declaration `LogPipelineStats();` and a comment. |
| `pipeline_creation_gate.h` `Lease::Release()` (+8) | **SAFE** | It is additive and nothing calls it: a grep of gpu_native finds no `Release()` call on a Lease. The body is also correct for future use. It unlocks if the lease owns the lock, empties `lock_`, then resets `mutex_`, so the lock goes before its mutex owner. A second call does nothing, and so does the destructor afterwards. |
| `shaders.h` / `shaders.cpp` `CurrentShaderOwners()` (+4/+6) | **SAFE** | It is additive. The only hits are the declaration (shaders.h:40) and the definition (shaders.cpp:634), so nothing calls it. It takes `g_registry_mutex` only when called. |
| `pipeline_async.h` (new, 20:02) | n/a | Nothing includes it, so it is not compiled into the snapshot. The only mentions are comments in pipeline_stats.h:14 and :115. |

Owner's compile checks: compile-one exited 0 at 19:11 and again at 20:03 (shaders.cpp and draw.cpp).

## 4. Agent 7: `build/agent7/batch1/perf-csv-rows.patch` (native-only, 2 lines)

| Change | Verdict | Evidence |
|---|---|---|
| Adds `rex::perf::WriteCsvFrame();` after `ResetFrameCounters()` in `HostDevice::PresentTexture` | **SAFE** | **It does nothing without the flag.** `WriteCsvFrame` returns at once when `g_csv_file` is null (rexglue-sdk/src/core/perf/counter.cpp:156-158). Only `SetCsvLogPath` sets that pointer (counter.cpp:128-140), and the only caller is runtime.cpp:122-123, when `--perf_log_csv` is non-empty. The cost is one global load and a branch per present. **There are no duplicate rows.** The patch sits inside `if (presented)` (device.cpp:2256-2265), which runs once per successful present. The other writer, `Profiler::Flip()`, is called only from `CommandProcessor::ExecutePacketType3_XE_SWAP` (command_processor.cpp:1068). In native mode `OnPreSetup` clears `config.graphics` and `gpu_plugin` (legodimensions_app.h:114-115), so that path never runs, as the existing comment at device.cpp:2260-2261 notes. PM4-reference mode creates no HostDevice. **The order matches** `Profiler::Flip`, which does Reset then Write (include/rex/perf/counter.h:109-112). Both functions are declared and defined without `#ifdef` (counter.h:69 and :79), so it links in every configuration. The hunk context matches live device.cpp:2262-2267, so the patch applies cleanly. |

A note for CSV runs only, not a blocker: `FlushCsv` runs from `Runtime::Shutdown` (runtime.cpp:323), after `kernel_state_.reset()` (:307) has stopped the guest threads. So a present cannot race the fclose in an orderly shutdown. The `std::_Exit` path skips the flush, which loses at most 59 buffered rows (the flush runs every 60 frames, counter.cpp:168-170).
