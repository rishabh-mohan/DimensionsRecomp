# Agent 12: session-2 working plan (task #11, plus #14 queued), checkpoint 16:55

Purpose: this file preserves the final designs across the agy-grid restart. The report itself goes into `agent12-io-memory.md` as "Session 2".

**State at pause:** design is final. **No SDK source edits have been made yet,** so both repos are untouched and consistent. The bench subagent was checkpointed; see `bench/agent12/STATUS.md` for what it built and ran and how to resume. Paths below are relative to `DimensionsRecomp/rexglue-sdk`. Line numbers are at `2897c31`.

## Edit order and exact designs

### A. Item 2: lockless physical watch pre-check (`xmemory.h/.cpp` + `xfile.cpp`)
- **`xmemory.h`:** add a public method after `TriggerCallbacks` (h:323):
  - signature: `bool MayHaveWriteWatches(uint32_t virtual_address, uint32_t length) const;`
  - comment: lockless; call it after writing the data; false means there are no watches and TriggerCallbacks would be a no-op;
  - add `#include <atomic>`.
- **`xmemory.cpp`, the new method:**
  1. `std::atomic_thread_fence(seq_cst)` first.
  2. The same clamp as TriggerCallbacks (cpp:2265-2285): heap_base_ adjust, `rel >= heap_size_` → false, `min`, `length == 0` → false.
  3. `system_page_first/last` with `host_address_offset()`, clamped to `system_page_count_-1`.
  4. A block scan with the same masks as cpp:2291-2303, but each load is `std::atomic_ref<uint64_t>(const_cast<uint64_t&>(...notify_on_invalidation)).load(relaxed)`. Don't use `atomic_ref<const T>`, which is C++26.
- **Writer side, all under the global lock already:**
  - cpp:2233: replace the `|=` with an atomic_ref relaxed store of `old | bit`. Track `any_bit_set` and, after the loop, `if (any_bit_set) std::atomic_thread_fence(seq_cst);`.
  - cpp:2408: replace the `&= mask` with an atomic_ref relaxed store.
  - Other readers (2227, 2292, 2369, 2428, 2510) are plain reads under the lock. That's fine because no plain write races with them.
- **`xfile.cpp`:**
  - add `REXCVAR_DEFINE_BOOL(io_lockless_watch_check, true, "Kernel", "...")`;
  - call `TriggerCallbacks(AcquireDirect(), ...)` only if `!REXCVAR_GET(io_lockless_watch_check) || heap->MayHaveWriteWatches(addr, len)`.
- **Proof** (put it in the report):
  - The IO side writes data, does an SC fence, then loads the bit.
  - The watcher side stores the bit under the lock, does an SC fence, then copies.
  - Store buffering with SC fences on both sides forbids the outcome where the IO side sees the old bit and the watcher sees the old data. For the data side this relies on the fences also being full compiler and hardware barriers (MFENCE / DMB ISH).
  - Clears happen only after their callbacks have run.
  - When the pre-check sees a bit, the old locked path runs unchanged, and the predicate is identical to TriggerCallbacks' early exit.
  - Watch-before-copy holds in every watcher: D3D12 `UploadRanges`→`MakeRangeValid`, and rexlego `memory_watch.cpp` arms before it hashes.

### B. Items 1 and 5: `xfile.h/.cpp`
- **Split** `X_STATUS ReadData(uint32_t addr, uint32_t len, uint64_t offset, size_t* bytes_read)` out of `ReadInternal` (cpp:151-221 minus the position update). Declare it private in the .h.
  - `ReadInternal` becomes: resolve -1 → ReadData → `if (XSUCCEEDED && len) { if (byte_offset) position_ = byte_offset; position_ += bytes_read; }` → out → notify. Keep the quirk exactly.
- **New member** `bool lockless_reads_ok_ = false;`, set in the ctor and in `Restore` after `file_ = vfs_file`. It is true iff:
  - `dynamic_cast` shows `file_` is a `HostPathFile` or a `DiscImageFile` (`include/rex/filesystem/devices/{host_path_file,disc_image_file}.h`). **Not STFS:** its ReadSync does Seek+fread on a shared FILE*;
  - and `file_access()` has none of `FileAccess::kGenericWrite | kFileWriteData | kFileAppendData` (from `include/rex/filesystem.h:73`).
- **`Read()`:** if eligible and the offset is explicit (not -1/-2), call ReadData with no `file_lock_` held. Then, under `file_lock_`, do the position update with the quirk, the out value, and the notify plus `async_event_->Set()`. Otherwise use the old locked path.
- **`ReadScatter`:** coalesce only for explicit offsets (`byte_offset != 0, -1, -2`; offset 0 means the current position).
  - A run is consecutive `segments[k] == segments[0] + k*4096` while `k*4096 < read_remain`, and requires `LookupHeap(start) == LookupHeap(end)`.
  - One ReadData per run. On a full read, advance. On a failure or a short read, redo that run with the old per-page code. That's idempotent: fixups are re-applied and extra invalidation is harmless.
  - Preserve: break on the first failure; `read_remain -= requested`; `out = read_total`; final position `byte_offset + read_total` (only if at least one segment succeeded); one notify plus Set at the end.
  - Eligible files run unlocked, then do one locked bookkeeping step. Others hold `file_lock_` throughout, as now.
- **Ordering argument:**
  - The kernel's synchronous-handle lock still serializes host reads, so ordering is unchanged.
  - Bookkeeping is linearizable in lock order, and notifications go out in position-update order.
  - Writable and STFS files keep full atomicity.

### C. Item 4: `virtual_file_system.cpp` OpenFile (cpp:237-247)
- **Deferral rule:** defer the stale `exists()` only when `creation_disposition == kOpen && !(desired_access & (kFileWriteData|kFileAppendData))` (after the cleanup at :203-211). In that case the read-only WARN can't trigger.
- **Deferred path:** remember the host path. After `entry->Open` fails, if `!exists(path)`, call `entry->Delete()`, set `*out_action = kDoesNotExist`, and return `X_STATUS_NO_SUCH_FILE`. That gives the same result as before.
- All other dispositions, and write opens, keep the eager check.

### D. Item 3: logging (`api.h`, `macros.h`, `logging.cpp`). The headers are generated-code-visible; flag them.
- **`api.h`:**
  - `#include <atomic>`;
  - `namespace rex::detail { inline constinit std::atomic<int> g_log_level_floor{0}; }`. 0 = trace is conservative, and a per-DLL copy just stays at 0;
  - public `void RefreshLogLevelFloor();`, for anyone who calls `set_level` directly on a spdlog logger.
- **`macros.h`:**
  - `REX_LOG_IMPL` = `if (lvl >= floor.load(relaxed)) [[unlikely]] { GetLoggerRaw(cat) ... should_log ... }`. `cat` is now evaluated only past the floor.
  - `REX_LOG_NOISY_IMPL` checks the floor first, then `REXCVAR_GET(log_noisy)`. The api.h `<span>` include already requires C++20, so `constinit` and `[[unlikely]]` are fine.
- **`logging.cpp`:**
  - Add `RecomputeFloorLocked()`. The floor is 0 if not initialized. Otherwise it is the min of `g_config.default_level`, all `g_config.category_levels` values, and every logger's `level()`.
  - Call it at the end of InitLoggingEarly and of both InitLogging branches.
  - In SetCategoryLevel, SetAllLevels and SetRootLevel, take `g_mutex` just for the recompute. Never take it inside a function that already holds `g_mutex`.
  - In ShutdownLogging, set the floor to 0.
  - `RefreshLogLevelFloor()` locks and recomputes.
- **New finding: lazy `cat` evaluation changes registration timing.** Runtime level changes (the `log_level` cvar callback → SetRootLevel on registered roots) only reach categories that are already registered. Fix: register the built-in categories (core, cpu, apu, gpu, krnl, sys, fs) eagerly at the top of `InitLoggingEarly()` and `InitLogging(const LogConfig&)`, **before** taking `g_mutex`, by calling the inline category functions. With that, the built-ins are always registered, which is equal to or better than before.
  - The only other category is `codegen`, in the codegen tool only. There are no REXLOG_DEFINE_SUBCATEGORY users, and rexlego defines no categories.
  - This also keeps `spdlog::set_default_logger(core)` working.

### E. Compile checks (do not run a full build)
`powershell -NoProfile -File env\compile-one.ps1 <sdk-relative-or-abs path> -OutDir build\agent12\obj` for:
- `src/system/xmemory.cpp`, `src/system/xfile.cpp`, `src/filesystem/virtual_file_system.cpp`, `src/core/logging.cpp`;
- `src/kernel/xboxkrnl/xboxkrnl_io.cpp` (a heavy macro user);
- one codegen TU.

### F. Then
- Integrate the bench results (`bench/agent12/RESULTS.md`).
- Append "Session 2" to `agent12-io-memory.md`: per item, file:line, the change, the proof, and the numbers; the rejected options (overlapped handle, with B4's OPT number; per-category gates; STFS); the header flag; the in-game A/B plan.
- Send the `@@done 11` line, flagging `macros.h` and `api.h` (a full rebuild of about 720 TUs).

## Task #14 (J3, GCR safety net): not started
- Plan: one subagent maps the global-critical-region acquisition sites and writes the checklist and stress tests into `perf-notes/agent12-gcr-map.md` and `bench/agent12/gcr/`.
- I write `perf-notes/agent12-gcr-review.md` once `perf-notes/agent11-global-mutex-design.md` appears.
- The job text is in `perf-notes/SESSION2-jobs.md` §J3.
