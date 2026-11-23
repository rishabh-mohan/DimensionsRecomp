# Agent 12: SDK memory, file I/O, audio and logging (task #11)

> **RESUME (06:30, session 3). #11, #14, #17, #21 and #22 are done; #27 (S4 follow-up, staging only) is in progress.**
> - **#27 (Agent 1, 05:58): analysis and staging only (no builds, game runs, live-tree edits or git writes).**
>   - u diagnostic staged in `build/agent12/s4-diag/` (cvar `shared_memory_upload_hash_log`, default OFF; diff D2905301...; `git apply --check` and clang syntax PASS), with Agent 10 for a rating. Parser `bench/agent12/s4_uhash.py`. See S4.9.
>   - P1's fault side: S4.8. devoff: 5-15 µs per written 256 KB block, F_max = V / 256 KB + L. The native route stays on the old path, because rexlego's callback would make faults 4 KB.
>   - Waiting for Agent 8's a-vol run (Agent 5's `bench/agent5/matrix-s4-invalvol.json`, 06:33-07:15 slot) to fill in S4.6 step 1. Then optional P2 staging in `build/agent12/s4-p2/`, and the report to Agent 1 by ~07:45.
> - **#21 (S4: the write-tracking re-arm on GPU Commands; Agent 1, 04:54): done, analysis only (no builds, runs or source edits).** See section "S4 (#21)" at the end of this file.
>   - Cause: the guest's handle-heap Lock/Unlock calls `MmSetAddressProtect` over the whole block (RW -> RW; only the cache attribute changes). That invalidates and unwatches the block every frame, so the next draw re-uploads and re-arms it. `clear_memory_page_state` is false in every run, so it isn't the cause.
>   - Proposals, ranked: P1, keep watches on RW -> RW protects (one combined proposal with Agent 5, who calls it C1 and writes the combined S4 entry; medium risk; up to u x 42% of GPU Commands busy); P2, one G hold per re-arm (low risk, ~6%, counted only on the re-arms P1 leaves); then P3 and P4. The batch-1 fence costs ~0.
>   - Next: a counter run with `--slow_frame_log_ms=1` via Agent 8, then Agent 2 builds P1 and P2 behind cvars (both OFF).
>   - Tool: `bench/agent12/s4_waits.py`. Outputs: `build/agent12/s4/`.
> - **S3 landed on Agent 1's GO (02:04), live SDK tree only (SDK HEAD 90e7ccd plus these 2 files; B builds from snapB/S2 and is unaffected):**
> - **`src/ui/rex_app.cpp`:** E1569868E15761D9766A263FC80846A044D253FB6DE39ED0BAA5281C818B12EE -> 11DE333FA4C0541FDBA0B2909BFA7C6C44A8AE90AAE8834321BBE33EDAECDA8D (`pause_safe_order` default ON, mtime 02:04:38). Diff `build/agent11/safeorder/safeorder.diff` 569528763341D890... (-5/+7, 2 hunks). `safeorder_stage.ps1 -Check` = "staged (applied)".
> - **`src/audio/audio_system.cpp`:** C281FA8625435EFE352DD4E62043837063BA84D523831ED629A994759A861260 -> 4331A312A9FE8F15E87A8CEDECD553A878B8E9F5DC576A47A453A3FB0DFAC638 (`audio_shutdown_detach_worker` default ON, line 48, mtime 02:04:39). Diff `build/agent12/s3flip/audio-default-on.diff` BF399E597D063846... (-1/+1). `s3flip_stage.ps1 -Check` exits 3 = applied.
> - **Syntax -Live, PASS for both:** s3flip: exit 0 for both copies, only the 2 `decoder.h` warnings (`build/agent12/s3flip/syntax-20261122-020455.txt`; the 02:02 staged dry run also passed). safeorder: exit 0 for both copies, only the 3 known warnings (`build/agent11/safeorder/syntax-20261122-020520.txt`). The -/+ lines of `git diff HEAD` equal the two staged diffs. No header changed. Hashes sent to Agents 1, 2 and 10 at ~02:07. Undo: `s3flip_stage.ps1 -Revert`, `safeorder_stage.ps1 -Revert`. Nothing is built yet (only Agent 2 builds). Agent 10 (02:20): both flips are SAFE together at the live hashes (S8, S11 in `perf-notes/agent10-batch2-review.md`); no toml or runner sets either cvar. Kill switches: `--audio_shutdown_detach_worker=false`, `--pause_safe_order=false`. Task #11 closed and its files released (02:20).
> - **#22 (audio shutdown, batch 2):** live `src/audio/audio_system.cpp` C281FA86... (21:56:43) and `include/rex/audio/audio_system.h` 4836B139... (21:44:35), unchanged since Agent 10's review. Cvar `audio_shutdown_detach_worker`, default false until S3 (live default true since 02:04, 4331A312...). S2 has it at OFF (`build/agent2/devoff2-bin`, `build/agent2/native2-bin`; their rexruntime 1C45C869... contains the cvar). Diff `build/agent12/batch2-audio-shutdown.diff`; pristine copies (= snap1) in `build/agent12/pristine/audio`. The replica gate is met (NEW 0 HUNG / 0 CRASHED in all 6 cases; table at the end of "Batch 2: audio shutdown"). Agent 1 (23:56): the default-ON flip goes into S3 (next bullet).
> - **S3: LANDED at 02:04 (results in the RESUME bullets above).** Original instructions (assigned by Agent 1 at 23:56; timing changed at 01:20): after the agy-grid relaunch, only at Agent 1's GO (after the checkpoint), not before. (0) Until GO, check only: `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent12\s3flip_stage.ps1 -Check` (exit 0 = live still pristine C281FA86...) and `bench\agent11\safeorder_stage.ps1 -Check` (expect "pristine", E1569868...). At GO: (1) Audio flip: `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent12\s3flip_stage.ps1 -Apply` (staged 00:01: pristine C281FA86... -> 4331A312..., diff `build/agent12/s3flip/audio-default-on.diff` BF399E59..., 11/11 PASS; `-Check` exits 0 = pristine, 3 = applied; `-Revert` undoes; both write a fresh mtime). (2) pause_safe_order: Agent 10 rated `build/agent11/safeorder/safeorder.diff` SAFE (`perf-notes/agent10-batch2-review.md` section 11, reviewed 00:00-00:10). Run `bench\agent11\safeorder_stage.ps1 -Apply` (expect pristine E1569868... -> 11DE333F...; since 00:07 the script stamps the mtime itself), then `-Check` (expect "staged (applied)"). (3) Syntax, one compile at a time: `bench\agent12\s3flip_syntax.ps1 -Live` (pristine vs live; the 22:23 baseline for C281FA86 was exit 0 with the 2 decoder.h unused-parameter warnings), then `bench\agent11\safeorder_syntax.ps1 -Live` (3 pre-existing warnings). (4) Send the full hashes, the syntax results and the diff paths to Agents 1, 2 and 10.
> - **#17 follow-up:** both conditions for defaulting `pause_safe_order` to true are met (the Decision list just above "Batch 2"). Agent 10 rated it SAFE (00:10), so it lands in S3 with the audio flip (S3 bullet).
> - **Window-3 ON bundle (sent to Agent 8 at ~23:23):** `io_lockless_watch_check`, `io_coalesce_scatter_reads`, `io_unlocked_file_reads`, `vfs_defer_open_exists_check`, `log_level_gate` (kInitOnly), all true.
> - **Replica:** `powershell -NoProfile -ExecutionPolicy Bypass -File bench/agent12/gcr/run_audio_shutdown_replica.ps1 -Cases "new h,old h,new p,old p,new b,old b" -Runs 1000` (exe EFEF2094..., build with `bench/agent12/gcr/build_audio_shutdown_replica.cmd`).
> - **Compile:** `powershell -NoProfile -File env\compile-one.ps1 <src.cpp> -OutDir build\agent12\obj -SyntaxOnly`. Read the final `exit=` line.

**Session 1 status (historical): partial, analysis only.** Session 2 implemented all five items behind cvars; see "Session 2" at the end of this file. The toolchain wasn't ready, so on Agent 1's instruction (12:24) there were no builds and no source edits this session. I left both repos untouched. **No numbers were measured.** Every "expected" figure below is an estimate from reading the code, and the benches in §3 have to confirm it. 12 agents share this machine (i7-1255U), so when measuring, take the median of at least 5 runs and record the machine load.

SDK = `games/lego-dimensions-recomp/DimensionsRecomp/rexglue-sdk`, branch `perf/opt` at `2897c31`. Paths are relative to the SDK unless noted. Line numbers are from that pin.

## 1. Opportunities, ranked by expected win

### 1. ReadScatter does a host read, 2 heap lookups and (for physical memory) a global-lock round trip for every 4 KB page

- **Where:** `src/system/xfile.cpp:241-295` (loop at 257-279) → `ReadInternal` at `xfile.cpp:139-239` → `HostPathFile::ReadSync` → `Win32FileHandle::Read` at `src/core/filesystem_win.cpp:126-133`, which makes one `ReadFile` call per call.
- **Evidence:** the loop clamps every read to `page_size = 4096` (`xfile.cpp:253-263`). Archives come through NtReadFileScatter (`src/kernel/xboxkrnl/xboxkrnl_io.cpp:352`, call at :374). For each 4 KB segment the code does:
  - 2× `LookupHeap` (`xfile.cpp:166-168`);
  - `QueryRangeAccess` under `heap_mutex_` (`xfile.cpp:180`, `xmemory.cpp:1908-1937`);
  - one `ReadFile` syscall;
  - one `std::function` fixup call (rexlego registers one, `rexlego/src/mod_menu.cpp:104`);
  - for physical heaps, `TriggerCallbacks(global_critical_region::AcquireDirect(), ...)` (`xfile.cpp:207-211`). This locks the process-wide recursive mutex *before* it checks whether anything is watched (`xmemory.cpp:2289-2306`).

  So a 1 MB archive read costs 256 syscalls and 256 global-lock acquisitions.
- **Change:** coalesce runs of guest-contiguous segments that sit in one heap into a single `ReadInternal`, for explicit offsets only. If a run fails or comes back short, redo just that run with the existing per-segment code. Positional reads are idempotent, so status, `position_`, bytes read and EOF behaviour stay identical. On a synchronous handle, `ReadFile` with an OVERLAPPED offset at EOF fails with `ERROR_HANDLE_EOF`, which becomes `X_STATUS_END_OF_FILE`; the redo reproduces that.

```cpp
// xfile.cpp ReadScatter - untested sketch
const bool explicit_offset =
    byte_offset && byte_offset != uint64_t(-1) && byte_offset != uint64_t(-2);
while (read_remain) {
  uint32_t read_buffer = *segments;
  // One host read for a run of guest-contiguous segments in one heap.
  if (explicit_offset && read_remain > page_size) {
    uint32_t run_segments = 1;
    while (uint64_t(run_segments) * page_size < read_remain &&
           uint32_t(segments[run_segments]) == read_buffer + run_segments * page_size) {
      ++run_segments;
    }
    uint32_t run_length =
        uint32_t(std::min<uint64_t>(uint64_t(run_segments) * page_size, read_remain));
    if (run_segments > 1 &&
        memory()->LookupHeap(read_buffer) == memory()->LookupHeap(read_buffer + run_length - 1)) {
      uint32_t bytes_read = 0;
      if (ReadInternal(read_buffer, run_length, byte_offset + read_total, &bytes_read,
                       apc_context, false) == X_STATUS_SUCCESS &&
          bytes_read == run_length) {
        read_total += bytes_read;
        read_remain -= run_length;
        segments += run_segments;
        continue;
      }
      // Failed or short (EOF): redo this run page by page below so results match the old loop.
    }
  }
  ... existing per-segment body, unchanged ...
}
```

  `segments[run_segments]` is only read when the old loop would also read it: there is one element for every started 4 KB of `length`.
- **Expected win:** up to N× fewer syscalls and global-lock acquisitions, where N is the average contiguous run (16 for 64 KB). A cached `ReadFile` costs about 1-3 µs, which dominates a 4 KB-per-call stream. My guess is 2-5× scatter throughput from the page cache, but this must be measured.
- **Risk (low-medium):**
  - (a) Invalidation callbacks get one call covering the run instead of one call per page. The range is the same and `unwatch_exact_range = true`.
  - (b) The redo path for a failed or short run triggers callbacks one extra time for that run. The extra invalidation is harmless. It also re-applies fixups, but to freshly re-read data.
  - (c) Fixups see one larger range. The only registered fixup (`mod_menu.cpp:109-111`) needs both patched bytes inside one read. So coalescing can only make it match where a scatter read that isn't 4 KB-aligned used to split those bytes (a latent miss today). Otherwise behaviour is identical.
  - (d) Offsets 0, -1 and -2 keep the old loop.
- **Verify:** a unit test in bench/agent12 with a synthetic file, `Memory`, and `XFile` over a HostPathDevice. Compare buffer contents, status, `position_` and bytes read against the old loop (kept behind a test flag) for these cases: contiguous, non-contiguous, cross-heap, EOF inside a run, EOF on a segment boundary, offset past EOF, and a read-only page in a physical heap. Bench: scatter MB/s, old vs coalesced, sequential and random. Game: count segments per call and run lengths during a level load.

### 2. Handle lookups serialise on the global recursive mutex (not my files; needs a claim)

- **Where:** `src/system/util/object_table.cpp:270-302` (`LookupObject`, lock/unlock at :278/:298), `LookupTable` at :245-260, writers `AddHandle` :98, `ReleaseHandle` :160 and `RemoveHandle` :178. `object_table.{h,cpp}` are unowned, and `global_critical_region` is in Agent 11's area, so this needs `@@claim` plus agreement first.
- **Evidence:** every `LookupObject` locks `global_critical_region::mutex()`. That is one process-wide `std::recursive_mutex`, also taken by:
  - VFS (`src/filesystem/virtual_file_system.cpp:106`) and `Entry::GetChild` (`src/filesystem/entry.cpp:54`);
  - the XObject native-object helpers;
  - the MMIO fault path (`src/system/mmio_handler.cpp:408`);
  - every physical-heap file read (#1).

  NtReadFile and NtReadFileScatter each do two lookups (event + file, `xboxkrnl_io.cpp:222,227,341,346`), and waits, events and threads do the same. With 4 threads this forms a convoy.
- **Change:** give the table its own `std::shared_mutex table_mutex_` (SRW).
  - `LookupObject` (not `already_locked`) takes it shared only.
  - Writers keep the global lock and also take it exclusively, only around table/slot mutation.
  - Writers drop it before `object->Release()`: Release can delete and re-enter the table, and `shared_mutex` is not recursive.
  - Lock order: global → table.

```cpp
// LookupObject, already_locked == false - untested sketch
std::shared_lock table_lock(table_mutex_);
uint32_t slot = GetHandleSlot(handle);
if (slot < table_capacity_ && table_[slot].object) {
  object = table_[slot].object;
  object->Retain();
}
```

- **Expected win:** small with 1 thread (SRW shared vs recursive mutex, maybe 10-30%). Large with 4 threads, because lookups stop queueing behind VFS, memory and invalidation users. Must be measured.
- **Risk (medium):**
  - Every writer of `table_`/`table_capacity_` needs the exclusive lock: resize/realloc, reset, slot changes from name mappings, and `GetObjectsByType`.
  - `LookupTable` already returns a raw entry pointer after unlocking. That is an existing hazard if the table is realloc'd; keep its callers under the global lock as they are now.
  - Any writer path that calls Release() while holding `table_mutex_` deadlocks.
- **Verify:** bench lookups/s with 1 thread and 4 threads, plus 4 threads alongside one Add/Release writer thread. Stress test: 4 readers and 1 writer for 10 s, then check every refcount returns to its baseline. There is no TSAN on Windows clang.

### 3. A disabled log call pays for a guarded static, an out-of-line call and a vector bounds check before the level test

- **Where:** `include/rex/logging/macros.h:18-23` (`REX_LOG_IMPL`), `macros.h:145-151` (the `REXLOG_DEFINE_CATEGORY` Meyers singleton), `src/core/logging.cpp:359-366` (`GetLoggerRaw`).
- **Evidence:** each disabled call does:
  1. the thread-safe static guard check for the category id;
  2. a call into logging.cpp, which tests `g_initialized`/`g_early_initialized`, bounds-checks `g_registry` and loads the `shared_ptr`;
  3. `spdlog::logger::should_log` (an atomic load).

  Kernel import traces go through `REX_LOG_NOISY_IMPL` (`macros.h:25-30`, `include/rex/system/kernel_state.h:56-58`), so they already stop at the `log_noisy` cvar. The cost is in plain `REX*_TRACE/DEBUG` calls inside hot loops.
- **Change:** a header-inline, per-category level cache, checked before `GetLoggerRaw`. logging.cpp refreshes it wherever levels change: `SetCategoryLevel`, `SetAllLevels`, `SetRootLevel`, `InitLogging(Early)`, `RegisterLogCategory`/`RegisterLogSubcategory` and `ShutdownLogging`. The cache starts at 0 (trace), so calls before init still take the slow path that runs `InitLoggingEarly()`. The off path is byte-identical.

```cpp
// api.h - untested sketch
namespace rex::detail {
inline constexpr uint16_t kLevelCacheSize = 256;
inline std::atomic<uint8_t> g_level_cache[kLevelCacheSize]{};  // 0 = always take slow path
inline bool MaybeEnabled(LogCategoryId c, spdlog::level::level_enum l) {
  return c.id >= kLevelCacheSize ||
         uint8_t(l) >= g_level_cache[c.id].load(std::memory_order_relaxed);
}
}  // namespace rex::detail
// macros.h, REX_LOG_IMPL:
//   const auto rex_log_cat_ = (cat);
//   if (::rex::detail::MaybeEnabled(rex_log_cat_, lvl)) { auto* p = ::rex::GetLoggerRaw(rex_log_cat_); ... }
```

- **Expected win:** from a few ns down to about 1 ns per disabled call. This only matters if hot paths log at trace/debug, so size it with a profiler before spending time on it.
- **Risk (low-medium):** any code that calls spdlog `set_level` directly on a category logger would desync the cache. Grep for that first and route it through `SetCategoryLevel`. Editing macros.h rebuilds everything that includes it, including generated code.
- **Verify:** bench ns/call for disabled TRACE/DEBUG (level = warn), and check the enabled path is unchanged. Unit test: change levels via `SetCategoryLevel`/`SetAllLevels`/`SetRootLevel` and check that messages appear and disappear in a test sink.

### 4. Every read into physical memory takes the global lock, even when nothing is watched

- **Where:** `src/system/xfile.cpp:207-211`, `src/system/xmemory.cpp:2256-2306`.
- **Evidence:** `AcquireDirect()` is evaluated before `TriggerCallbacks` runs its `any_watched` scan, so every read into physical memory locks the global recursive mutex.
- **Change (off by default, behind a cvar):** scan the `notify_on_invalidation` bits first, after a `std::atomic_thread_fence(seq_cst)`. Only take the lock and call `TriggerCallbacks` if a bit is set.
- **Risk (medium-high):** correctness depends on the GPU side setting watch bits *before* it copies guest data. Xenia's shared memory does this (MakeRangeValid, then upload), but I haven't confirmed it in this SDK's GPU code. Getting it wrong gives stale textures or vertices, which only the game can show. #1 already divides the number of acquisitions by the run length, so do #1 first.
- **Verify:** bench reads into a physical heap with no watches. Game: look for texture corruption while streaming.

### 5. Opening a file costs an extra stat and gives no access-pattern hint

- **Where:** `src/filesystem/virtual_file_system.cpp:242` (`std::filesystem::exists` before the open), `:105-106` (`ResolvePath` under the global lock), `src/core/filesystem_win.cpp:210-211` (`CreateFileW(..., FILE_ATTRIBUTE_NORMAL | FILE_FLAG_BACKUP_SEMANTICS)`).
- **Evidence:** every open makes one extra attribute-query syscall. But the game opens each DAT once and then reads by offset (comment in `xboxkrnl_io.cpp` near line 33), so opens aren't a loading hotspot. There are no `FILE_FLAG_SEQUENTIAL_SCAN`/`FILE_FLAG_RANDOM_ACCESS` hints.
- **Change:** drop the `exists()` call and rely on CreateFileW's not-found result, keeping the same X_STATUS mapping. Add the hints only behind an off-by-default cvar.
- **Expected win:** small.
- **Risk:** low for removing `exists()` (only the status mapping can change). The hints only change cache policy.
- **Verify:** filesystem_test, plus a bench of opens and closes per second. The cold-cache effect of the hints can only be measured with the game on a real disk.

### 6. Reads of the same file serialise twice

- **Where:** `xfile.cpp:134` and `:243` hold `file_lock_` for the whole synchronous read. The host handle is synchronous (no `FILE_FLAG_OVERLAPPED`, `filesystem_win.cpp:210`), and Windows serialises I/O on a synchronous file object anyway.
- **Change:** none without evidence. If the game reads one DAT from several threads at once, an overlapped handle plus a narrower lock would allow parallel reads. Only the game can show this: count `file_lock_` contention (`try_lock` misses) during loads.

### 7. xmemory large-range operations are O(pages), which looks fine

- **Where:**
  - `BaseHeap::Protect`, `xmemory.cpp:1712-1798` (validate loop at :1752, update loop at :1788);
  - `QueryRegionInfo`, :1800-1851 (the free-region scan at :1840 walks to the next allocated page);
  - `AllocRange`, :1453 (top-down scan at :1496/:1534 with skip-ahead);
  - `Release`, :1650;
  - `QueryRangeAccess`, :1908.
- **Evidence:**
  - All of these are linear in the pages of the range, under `heap_mutex_`.
  - `AcquireHostPageReconcileLock` (:967) only takes the global lock when a guest page is smaller than a host page. `system_page_size_` = `dwPageSize` = 4 KB (`xmemory.cpp:96`, `src/core/memory_win.cpp:29`), so that never happens for these heaps.
  - 256 MB in a 4 KB heap is 65536 entries per operation, which I estimate at tens of µs. Allocations are rare outside loads.
- **Change:** none until the bench shows a problem. If it does, one candidate: NtAllocateVirtualMemory calls Protect twice when the requested protection lacks write (`xboxkrnl_memory.cpp`, Agent 11's file); fold that into one call.
- **Verify:** bench alloc + protect + query + release on 16, 64 and 256 MB ranges, in both the 4 KB and 64 KB heaps.

## 2. Looked at and rejected

- **MMIO range lookup** (`src/system/mmio_handler.cpp:96-124`, fault path :396-402): a linear scan of `mapped_ranges_`. Ranges are registered only through `Memory::AddVirtualMappedRange` (`xmemory.cpp:532`), so there are only a handful, and a sorted structure or tree can't beat that. The real cost of an MMIO access is the trap (VEH plus `TryDecodeLoadStore`), not the lookup. I recommend counting traps per frame in the game. The bench is still planned, to back this up with a number.
- **`Memory::LookupHeap`** (`xmemory.cpp:403-423`): a compare chain, about 1 ns.
- **Fixup cost per read** (`xfile.cpp:44-50` + `mod_menu.cpp:106`): one `std::function` call, a cvar check and a string compare per read. This only matters at 4 KB granularity and goes away with #1.
- **`trace_file_reads` logging** in NtReadFile/NtReadFileScatter (`xboxkrnl_io.cpp:233-248`, `353-370`): gated on a cvar string that is empty by default, so it costs nothing when off.
- **The per-read `async_event_->Set()` and `NotifyIOCompletionPorts`** (`xfile.cpp:227-236`, `285-292`): one SetEvent per read. Skipping it would change wait semantics for guests that wait on the file object. Leave it alone; ReadScatter already notifies once per call, not once per page.

## 3. Bench and test plan for next session (bench/agent12, standalone CMake)

1. **Build:** `cmake -S <SDK> --preset win-amd64 -B games/lego-dimensions-recomp/build/agent12/sdk`, then build the Release configuration with `-j 4`. Check `CMAKE_BUILD_TYPE` after any failed reconfigure (README-dev pitfall). Check whether the SDK exports a CMake package; if not, bench/agent12 imports the static libraries and include directories by hand.
2. **Baseline tests before any edit:** `ctest --test-dir build/agent12/sdk -C Release -R "filesystem|stream|memory|heap"`. I haven't checked the exact target names in `tests/CMakeLists`.
3. **Benches** (Release, x86-64-v2; at least 5 runs, report median plus min and max; record CPU load before each run; pin single-thread benches with `start /affinity`):
   - `bench_vfs`:
     - Generate 64 MB and 256 MB files from a fixed-seed xorshift into `build/agent12/bench-data`. Never use game data.
     - Do one warm pass, so the bench measures the CPU and syscall path rather than the disk.
     - Sequential `ReadSync` at 4 KB, 64 KB and 1 MB; random reads at 4 KB and 64 KB with fixed-seed aligned offsets. Checksum the results against the generator.
     - Scatter: use `XFile::ReadScatter` if an `XFile` plus `Memory` can be built without a full KernelState (`XFile()` uses `XObject(kObjectType)`, `xfile.cpp:59`, but `memory()` goes through the kernel state). Otherwise, emulate it with a 4 KB loop vs a coalesced read to bound the win.
   - `bench_handles`: an `ObjectTable` plus 1024 dummy XObjects. Run 1 and 4 threads doing a random-handle `LookupObject<XObject>` and dropping the ref, for 2 s; report total lookups/s. Add a variant with a concurrent add/release writer.
   - `bench_log`: set krnl to warn, run 100M `REXKRNL_TRACE("x {}", i)` calls and report ns/call. Also time `REXKRNL_IMPORT_TRACE` with `log_noisy` off.
   - `bench_xmemory`: initialise `Memory`. In v00000000 (4 KB pages) and v40000000 (64 KB pages), loop Alloc(reserve|commit, RW) → Protect(RO) → QueryRegionInfo → Release for 16, 64 and 256 MB, and report µs per iteration.
   - `bench_mmio`: register 1, 2 and 4 ranges and measure ns per `LookupRange`/`CheckLoad`, for a hit and for a miss.
4. **Order of work:** #1 first (owned, biggest, testable without the game), then #3 (owned), then #2 once it's claimed and agreed with Agent 11 and Agent 1. #4 and #5's hints only behind off-by-default cvars.

## 4. What only the game can validate

- **#1:** segments per scatter call and run lengths (temporary counter); load-time stopwatch (boot→hub, hub→level) before and after; no texture or vertex corruption in streamed areas (invalidation semantics); the PortalTrailer fix still applies (it logs "Fix: PortalTrailer enabled").
- **#2:** frame-time spikes while streaming; watch for deadlocks when handles close during heavy loads.
- **#3:** what share of hot-thread time logging takes, from a profiler.
- **#4:** rendering correctness (stale textures or vertex buffers).
- **#5:** the effect of the access-pattern hints on cold-cache loads from a real disk.
- **#6:** whether one DAT is read from several threads at once.
- **Audio:** XMA decode-thread CPU use and underruns. I didn't analyse audio at all.

## 5. Not read this session

- `src/audio/**` (`xma_context.cpp`, `xma_decoder.cpp`, `audio_system.cpp`, `sdl_audio_driver.cpp`): no audio analysis was done.
- `src/system/kernel_state.cpp`, `runtime.cpp`, `xiocompletion.cpp` (the cost of `NotifyIOCompletionPorts` per read is unknown).
- `src/core/memory.cpp`, `memory_win.cpp` beyond `page_size`, `mapped_memory_win.cpp`, `ring_buffer.cpp`.
- The rest of `xmemory.cpp`: the Alloc/AllocFixed/Release bodies, the PhysicalHeap protect/watch code (:2127-2255, :2330-2526) and `EnablePhysicalMemoryAccessCallbacks` (:701). Also `include/rex/system/xmemory.h` and the mmio_handler decoder (:126-366).
- The tests: `tests/unit/core/filesystem_test.cpp`, `stream_test.cpp`, `tests/unit/memory/*`, and the tests CMake wiring.
- `src/kernel/xboxkrnl/xboxkrnl_ob.cpp` (ObReferenceObjectByHandle/NtClose), and the GPU shared-memory watch code, which #4 depends on.
- The `REXCVAR_GET` implementation (how much the `log_noisy` check costs).


## Session 2 (18:05-): implementation

**Status at 20:04:** all five items are implemented and compile-checked (`env/compile-one.ps1`, exit=0), and so is task #17 (the `SetGuestPaused` order, plus the debug cvars for Agent 11's test G). Each change is behind a cvar that defaults to **false** (or 0), following the 18:50 rule. With every cvar off the code takes the old path; the always-on residue is listed below the table. Bench numbers are in "Tests and benches".

### Batch-1 listing (dev OFF build 1, cut-off 20:15)

| # | Change | Files (SDK-relative, current line numbers) | Cvar (default) |
|---|---|---|---|
| 2 | Physical-memory reads skip the global lock G when no page in the buffer is write-watched | **`include/rex/system/xmemory.h:329` (header in the generated-code PCH)**; `src/system/xmemory.cpp:2147-2157, 2245, 2267-2270, 2425, 2432-2470`; `src/system/xfile.cpp:31, 285-295` | `io_lockless_watch_check` (false) |
| 1 | ReadScatter at an explicit offset reads each run of contiguous pages with one host read; a run that fails or comes back short is redone page by page | `include/rex/system/xfile.h:16, 135-168` (not in the PCH closure); `src/system/xfile.cpp:35, 58-95, 335-544` | `io_coalesce_scatter_reads` (false) |
| 5 | Reads at an explicit offset from read-only HostPathFile/DiscImageFile handles skip `file_lock_` for the host read (taking `unlocked_read_lock_` shared); position and completion are still published under `file_lock_` | `src/system/xfile.cpp:39, 58-67, 115, 191-334, 545, 613`; `xfile.h` as above | `io_unlocked_file_reads` (false) |
| 4 | A read-only open of a cached host file skips the `exists()` stat; it is checked only if the open fails | `src/filesystem/virtual_file_system.cpp:23-26, 236-258, 345-350` | `vfs_defer_open_exists_check` (false) |
| 3 | A log call below the global level floor is one inline compare and does not evaluate its category. Above the floor the macro runs the old sequence (`GetLoggerRaw`, `should_log`), and the floor is bound (`BindLogLevelFloor`) only by a line that is logged. Two fixes for the gate-off filtered path (floor 0), both found by B5: 19:27 dropped `[[unlikely]]` from the floor test (it cost ~4 ns per call); 19:54 moved the bind check out of the filtered path (it cost ~1-2 ns) | **`include/rex/logging/api.h:16, 128-167` and `include/rex/logging/macros.h:16-41` (both headers in the generated-code PCH)**; `src/core/logging.cpp:59-61, 146-162, 199-211, 224, 292, 324, 417-455` | `log_level_gate` (false, kInitOnly) |
| 17 | `SetGuestPaused` in a safe order (task #17). The pause pauses audio, takes the thread snapshot (allocates, takes T), frees the snapshot buffer and logs while the guest still runs; then the suspend loop does nothing else. The unpause resumes from the pause's own list first, then resumes audio, logs and drops the refs. The pause picks the path, and its unpause follows it | `src/ui/rex_app.cpp:51-59` (std includes), `71-75, 87-107, 731-788`. Not in the closure: `rex_app.cpp` is compiled into the app, and no header changed | `pause_safe_order` (false) |
| 17 | Debug, for Agent 11's pause test G: from 15 s after the guest starts, a host thread posts pause/unpause toggles to the UI thread every N ms through `SetGuestPaused`. It stops after N full cycles, ending unpaused. `OnDestroy` stops and joins it | `src/ui/rex_app.cpp:77-83, 109-135, 643-673, 841-842` | `debug_pause_cycle_ms` (0 = off), `debug_pause_cycle_count` (0 = unlimited) |

**Header edits (flagged):** `rex/system/xmemory.h`, `rex/logging/api.h` and `rex/logging/macros.h` are in the generated-code closure (Agent 2's list, `perf-notes/agent2-baseline.md` "SDK headers in the generated-code closure"), so batch 1 is a full rebuild of the generated code. `rex/system/xfile.h` is not on that list. The last closure edits were `api.h` and `macros.h` at 19:54 (the bind fix in row 3), compile-checked and reported to Agent 2 at 20:00; none are planned after them. S0d has the 19:27 version of both, and S1 (20:15) takes the 19:54 version. Agent 10's #18 check (`perf-notes/agent10-batch1-review.md` §4) found every task #11 edit SAFE with the cvars at their defaults, and measured +66-67 bytes per log call site, with 0 log call sites in the generated TUs.
- **`src/ui/rex_app.cpp`:** `build/dev` compiles it from the SDK source tree. The installed copy at `build/sdk/install/share/rexglue/rex_app.cpp` changes only when Agent 2 reinstalls the SDK.

**Always-on residue with every cvar false** (no behaviour change):
- The watch-bit stores in `EnableAccessCallbacks` and the `TriggerCallbacks` clear loop are relaxed `atomic_ref` stores, which compile to the same plain stores. `EnableAccessCallbacks` ends with one seq_cst fence per call.
- `XFile::Read` is split into `ReadData` and `CompleteRead` and runs the same sequence under `file_lock_`. `XFile::Rename` also takes `unlocked_read_lock_` exclusively, which is uncontended.
- Each log macro does one extra compare (two loads) against a floor that stays 0. It is inline, with no `[[unlikely]]` (see row 3).
- `SetGuestPaused`: one cvar read per pause and one flag test per unpause. `LaunchModule` reads `debug_pause_cycle_ms` once. `OnDestroy` calls `StopDebugPauseCycle`: an atomic store, a mutex lock and a notify, and no join when the thread never started.

**Compile checks (19:00):** `xmemory.cpp` (18:14), `xboxkrnl_io.cpp` (18:35), `xfile.cpp` (18.6 s), `logging.cpp` (32.2 s), `virtual_file_system.cpp` (7.9 s), `xam_notify.cpp` (7.5 s; uses the NOISY macros), all against `build/sdk-dev`, plus the rexlego `skip_cutscenes.cpp` against `build/dev`, whose include path is the SDK source tree. The remaining warnings are all pre-existing:
- sign-compare at `xfile.cpp:374` (old ReadScatter path);
- unused `created` at `virtual_file_system.cpp:296`;
- unused parameters in `xam_notify.cpp`.

**Compile checks (19:28-19:57), after the `macros.h`/`api.h` edits and task #17:** all exit=0, with no new warnings.
- **`macros.h` + `api.h`, final (19:54):**
  - against `build/sdk-dev`: `logging.cpp` (58 s) and `src/kernel/xam/xam_notify.cpp` (27 s; it uses the NOISY macros);
  - against `build/dev`: `rex_app.cpp` (56 s) and rexlego `skip_cutscenes.cpp` (29 s).
  - The 19:27 version passed the same four, plus `rex_app.cpp -Target rexapp_compile_test`.
- **`rex_app.cpp` with #17, final (19:44):** `build/dev` (11.9 s) and `build/sdk-dev -Target rexapp_compile_test` (14.8 s). The latter shows 3 pre-existing unused-parameter warnings: `rex_app.h:99`, `rex_app.h:102` and `xmemory.h:260` (that line is unchanged since the pin).

### What changes when a cvar is turned on

- **`io_lockless_watch_check`:** results are identical. This is store-buffering with a seq_cst fence on each side:
  - The reader writes the data, fences, then does a relaxed load of the watch bits in `MayHaveWriteWatches`.
  - Every bit writer holds G, sets the bits, then fences at the end of `EnableAccessCallbacks`, and the watchers copy only after that.
  - So either the reader sees the bit and invalidates under G as before, or the watcher's later copy sees the new data.
  - The three watchers all enable before they copy: `d3d12/shared_memory.cpp:326` (Vulkan `:303`), `primitive_processor.cpp:1367` and rexlego `gpu_native/memory_watch.cpp:120`.
  - With no bit set, `TriggerCallbacks` has no side effects, so skipping it is exact.
- **`io_coalesce_scatter_reads`:** data, status, bytes read and the final position are the same. The differences are on errors and short reads only:
  - after a short run, the rest of that run is also invalidated (conservative);
  - a page redone after a failed run can log ERROR_NOACCESS twice;
  - patch fixups can run twice on a redo (idempotent);
  - the rexlego PortalTrailer patch (`mod_menu.cpp:104-124`, 2 bytes at PATCH.DAT 0x7010E70) is now applied when those bytes straddle a 4 KB segment boundary. The old per-page path missed it there.
  - Offsets 0, -1 and -2, and offsets that could wrap into them, keep the old path.
- **`io_unlocked_file_reads`:** applies only to read-only handles on host or disc-image files, at an explicit offset.
  - Concurrent reads on one handle overlap in the host. Each read publishes its position and completion under `file_lock_` in the order it reaches that lock; positional reads don't depend on the position.
  - Lock order: `unlocked_read_lock_` (shared), then G inside `TriggerCallbacks`. It is released before `file_lock_` is taken. `Rename` takes `file_lock_`, then `unlocked_read_lock_` exclusively.
- **`vfs_defer_open_exists_check`:** the status and `out_action` are the same.
  - A hit saves one stat. A miss costs a failed open plus one stat, where it used to cost one stat.
  - It also closes the old race where a file deleted between the stat and the open left a stale entry.
- **`log_level_gate`:** the output is the same. The floor is the minimum of the default level, every configured category level and every live logger's level. It is recomputed under the logging mutex by `InitLogging`, `Set{Category,All,Root}Level` and `ShutdownLogging` (back to 0).
  - **Built-in categories:** `core`, `cpu`, `apu`, `gpu`, `krnl`, `sys` and `fs` are registered in `InitLogging`. A runtime `log_level` change therefore reaches them as before, even if they have never logged.
  - **Cross-DLL binding:** `rexruntime` exports functions only (WINDOWS_EXPORT_ALL_SYMBOLS), so each module reads the floor through a per-module pointer. That pointer is bound to the logging module's floor on the module's first full-path call.
  - **Residual difference:** a custom category that has only ever made disabled calls is registered later. Today the only one is `codegen`, in the codegen tool.

### Tests and benches

Sources are in `bench/agent12/src`, built by `bench/agent12/build.ps1` (clang-cl `-O2`, x86-64-v2). The replicas compile the working-tree SDK code paths and toggle each cvar explicitly. Full tables are in `bench/agent12/RESULTS.md`.

- **T1, ReadScatter/Read differential (old vs new, same inputs): PASS, 0 failures** in 6,000 cases (seed `0x7E57AB1E`) and 30,000 cases (seed `0xC0FFEE`).
  - **Coverage:** 18 case classes, among them:
    - EOF inside a run, at a run boundary and past EOF;
    - a protected page, a null-heap segment and a cross-heap run;
    - offsets 0/-1/-2, near-wrap offsets and address wrap;
    - access denied, a tiny or empty file, and plain `Read` on the fast path.
  - **Inputs:** each case picks a random cvar combination and a random file kind. STFS takes the locked path.
  - **Checks per case:**
    - status, bytes read, `position_`, the notification fields, and exactly one Notify + Set;
    - guest bytes, with a full-arena compare every 32 cases;
    - new watch bits ⊆ old watch bits;
    - old invalidated ranges ⊆ new ranges, and old fixup ranges ⊆ new ones.
  - **Counts over the 6,000 cases (random layouts, not a game workload):**
    - host `ReadFile` calls: 35,727 old vs 25,660 new;
    - global-lock acquisitions: 17,637 old vs 5,447 new.
  - **Allowed short-run difference:** 852 cases redid a run page by page, and the new code cleared 607 more watch bits than the old.
  - **Win32 probe:** a read at or past EOF returns END_OF_FILE, and a read across EOF comes back short, as assumed. Offset -2 reads at the handle's own file pointer in both versions, so T1 resets both handles' pointers per case.
  - **Fixup that straddles a 4 KB segment boundary:** a coalesced run applies it (32/32); the old code (0/32) and a split new run do not. This is the PortalTrailer note above.
- **T2, `MayHaveWriteWatches`: PASS.**
  - **(a)** It agreed with the locked `TriggerCallbacks` "any watched" result in 400k random checks, plus a boundary sweep over 4 heaps (heap address offset 0 and 0x1000, a partial last block, 64 KB pages): 0 mismatches.
  - **(b)** Store-buffering stress on the real code: 2 threads, 2M iterations, `EnableAccessCallbacks` against a data store followed by `MayHaveWriteWatches`. 0 forbidden outcomes.
  - **Controls:** the same stress gives 47,786 forbidden outcomes per 1M iterations with no fences, and 17,421 with only the I/O-side fence removed. So the test can see the bug.
- **B1-B5:** medians of 5 runs, machine load 65-100% (other agents were busy). Full tables are in `bench/agent12/RESULTS.md`.
  - **B1, scatter coalescing (`io_coalesce_scatter_reads`), 1 thread:**
    - a fully contiguous scatter: 5.3x on a synthetic file and 5.7x on GAME.DAT (2308 vs 406 MB/s);
    - 16 runs of 64 KB: 3.9x and 5.2x;
    - stride 2 (no two pages adjacent): unchanged, as expected;
    - host `ReadFile` calls per MB drop from 256 to 1 (contiguous) or 16 (64 KB runs).
  - **B2, lockless watch check (`io_lockless_watch_check`):**
    - uncontended p50 124 → 63 ns per read;
    - with another thread holding G 25% of the time, the mean drops from 8.9 µs to 55 ns and p99 from 60 µs to 0.18 µs.
  - **B3, deferred exists check (`vfs_defer_open_exists_check`):**
    - a hit takes 184 → 92 µs;
    - a miss takes 55 → 133 µs;
    - break-even is at 54% misses. In game, eligible misses are about 0%: a miss needs a cached entry whose host file has since been deleted.
  - **B4, unlocked same-file reads (`io_unlocked_file_reads`), 2 threads on one handle:**
    - no gain: 64 KB reads at 1711 MB/s new vs 1612 MB/s old;
    - the kernel serializes a synchronous handle (FO_SYNCHRONOUS_IO), so removing `file_lock_` alone does not overlap the reads;
    - an overlapped handle (not in the SDK) reaches 2567 MB/s (1.44x). See "Rejected options".
  - **B5, disabled log call (`log_level_gate`), ns per call:**
    - Gate on (floor = warn), a call below the floor (b5_final2, 19:44, load 40-100%):
      - trace: 2.72 → 0.47 ns (5.8x) on 1 thread and 3.61 → 0.76 ns (4.8x) on 2 threads;
      - debug: 3.64 → 0.66 ns (5.5x) on 1 thread and 4.31 → 0.96 ns (4.5x) on 2 threads;
      - two more runs agree: 4.8-6.3x.
    - Enabled calls (warn, about 530 ns): unchanged, 0.9-1.1x.
    - Gate off (floor 0, a call that fails `should_log`), the default:
      - The 19:27 macro was still 0.7-0.8x: 5.58 → 7.39 ns on 1 thread and 9.80 → 11.93 ns on 2 threads.
      - The ablation runs traced the gap to the bound-flag check: it is 1.0-1.3 ns slower than the same macro without it (v3) in all 3 runs, while v3 matches OLD (ablate3: 7.32 vs 7.81 ns).
      - 19:54: the check moved into the branch for lines that are logged, so the filtered path is now v3.
      - The earlier draft had been ~4 ns slower (10.27/11.01 vs 7.67/6.34 ns), because `[[unlikely]]` made clang call the category function out of line; that was fixed at 19:27.
    - **Rerun of the 19:54 macro** (`b5_v1p`, 19:59-20:01, OLD and NEW interleaved). Load was 100% throughout, so absolute values are ~2-4x those of the 19:44 run:
      - filtered (floor 0, the gate-off default): 17.06 → 16.33 ns on 1 thread and 14.31 → 14.83 ns on 2 threads, both 1.0x with overlapping ranges. A filtered-only confirmation run (20:03) agrees: 12.36 vs 12.44 ns and 11.29 vs 11.88 ns;
      - gate on, below the floor: trace 10.34 → 2.26 ns (4.6x) on 1 thread and 11.02 → 2.54 ns (4.3x) on 2 threads; debug 12.37 → 2.44 ns (5.1x) and 15.78 → 3.72 ns (4.2x);
      - enabled warn: 0.8-1.2x, which is noise;
      - ablation run 4 (filtered, 1 thread): OLD 12.27, v3 13.50, 19:54 macro 13.83, 19:27 macro 15.20 ns. v3 and the 19:54 macro are within 3% of each other. The sign of the OLD-v3 gap varies between runs: in ablate3, v3 was faster (7.32 vs 7.81 ns);
      - static instructions per filtered loop: OLD 79, v3 83, 19:54 macro 92, 19:27 macro 95. The 19:54 macro inlines the category function, and its bound-flag code is only in the logged branch.
      - **Verdict:** the gate-off filtered path is at OLD parity within noise: NEW/OLD is 0.96-1.05x on 1 and 2 threads in both runs.

### Design notes (choices made while implementing)

- **§A:**
  - The lock-free check only decides whether `TriggerCallbacks` runs. If any page in the range may be watched, the old locked call runs unchanged.
  - The fence at the end of `EnableAccessCallbacks` is unconditional, so the writer side never depends on when the cvar is read. It costs one fence per watch setup, which already runs under G.
- **§B coalescing:**
  - It covers only runs whose guest pages map to one contiguous host span in one heap (`IsSingleHostBuffer`), so the single host read lands exactly where the per-page reads would have. Cross-heap runs, protected pages and null-heap segments read page by page as before.
  - A run that fails or comes back short is redone page by page with the old code. The error status, the byte count and the final position therefore come from the old code.
  - Offsets 0, -1 and -2, and offsets that could wrap into them, take the old path.
- **§B unlocked reads:**
  - `unlocked_reads_ok_` is computed in the constructor and in `Restore`. It is set for read-only handles on host-path or disc-image files, never STFS.
  - Only the host read and the watch handling run outside `file_lock_`. Position and completion are published under `file_lock_` as before.
  - `Rename` takes `unlocked_read_lock_` exclusively (after `file_lock_`), so a rename never swaps the entry under an in-flight read. The lock analysis is in [agent12-gcr-review.md](agent12-gcr-review.md), last section.
- **§C:** a failed deferred open does the `exists()` check that was skipped, removes the stale entry and returns NO_SUCH_FILE, as the old order would have.
- **§D:**
  - **Per-module pointer.** `rexruntime` exports functions only: WINDOWS_EXPORT_ALL_SYMBOLS exports no data, and a header `inline` variable would get one copy per DLL. So each module reads the floor through a pointer that is bound on its first full-path call. Until then the module reads its own floor, which stays 0.
  - **When the floor is non-zero.** It is non-zero only between the end of `InitLogging` and `ShutdownLogging`, so early logging is unaffected.
  - **Registration.** The 7 built-in categories are registered early only when the gate is on, so startup with the gate off is unchanged. A newly registered category needs no recompute: its logger starts at its configured level or at the default level, and both are already in the minimum.

### Rejected options

- **Overlapped host handles (FILE_FLAG_OVERLAPPED).** On a synchronous handle the kernel serializes I/O per file object. So `io_unlocked_file_reads` removes only the SDK-side serialization, and alone it gains nothing (B4: 1711 vs 1612 MB/s). The B4 "overlapped" column measures what the rest would be worth: 2567 MB/s, 1.44x. That is the follow-up if same-file reads turn out to matter in game. I did not make the change because it touches every `HostPathFile` read and write (an event or completion per call) and the handle file-pointer semantics that offset -2 relies on.
- **Per-category level gates in the header.** They would need a fixed category-id table in a header that generated code includes. The single floor already covers the common case: calls below the lowest enabled level.
- **Exported data for the floor (dllimport).** This needs export macros and CMake changes. The per-module pointer gives the same two-load check without build changes.
- **Unlocked STFS reads.** STFS files share block-chain state between reads, and the game reads extracted host files.
- **Lock-free position updates.** Positions stay under `file_lock_` to keep the per-handle ordering guarantee.
- **The `has_explicit_level` handling in `logging.cpp`.** Pre-existing behaviour, left alone. The floor takes every live logger's level into account, so it is correct either way.

### In-game A/B plan (dev OFF build 1; run specs sent to Agent 8, the user starts the runs)

**Setup.**
- Timing runs go through Agent 8, and the user starts them. A game launched by an agent runs on a hidden desktop, so it counts only as a functional check, never as a timing run. Do not work around the hidden desktop.
- Each run uses Agent 3's harness (`harness/run-game.ps1`) with its defaults: a fresh toml per run, audio muted, profiler off (no `LEGO_SAMPLE_PROFILE`). The cvars go on the command line as `-Cvar name=value`.
- Keep the save and the `-Keys` script the same for every run: boot → title menu → load one story level → stand still 20 s → WM_CLOSE.
- If the script can reach Vorton, load it as well. It exercises the PortalTrailer read fixup.

**Configurations.** One binary throughout; the cvars go on the command line.

| Tag | Cvars |
|---|---|
| A | none (all five default to false) |
| B | `io_lockless_watch_check=true io_coalesce_scatter_reads=true io_unlocked_file_reads=true vfs_defer_open_exists_check=true log_level_gate=true` |
| B-io (only if A and B differ) | B without `log_level_gate`, to separate I/O from logging |

`pause_safe_order` and the `debug_pause_cycle_*` cvars are not part of this A/B. They belong to Agent 11's pause test G, which runs with `pause_safe_order=true`; B's default waits for that result. Keep `pause_when_unfocused` off for the timing runs.

**Order and count.**
- Run 5 of each, interleaved A B B A A B B A A B, so cache warm-up and drift hit both configurations equally.
- Discard one warm-up run first. A cold OS file cache measures the disk, not these changes.
- Report the median, min and max per configuration, plus the machine load the harness records.

**Metrics.**
1. **Boot:** process start to the first title-menu frame.
2. **Level load:** from the `-Keys` input that starts the load to the first frame after which the frame time stays at the in-level median for 2 s (`perf.csv`). Cross-check with the length of the read burst in the per-second I/O samples.
3. **Host reads per run:** `Win32_Process.ReadOperationCount` and `ReadTransferCount` at exit (or sampled every second).
   - Expected: bytes equal within noise, and fewer operations in B.
   - If operations do not drop, the game's scatter reads are not contiguous or not at an explicit offset, and §B does nothing in game.

**Correctness checks (B against A).**
- `Fix: PortalTrailer enabled in Vorton's loading script (read-time only)` appears in both configurations whenever Vorton's loading script is read.
- No new error or warning lines in `game.log`. Grep for:
  - `NtReadFile`, `ReadScatter`, `ERROR_NOACCESS`;
  - `access violation`, `invalid handle`, `assert`.
- Screenshots at the same script points match. A missed write watch would show up as stale or corrupt textures after streaming.
- The exit is clean: no WER dialog, no crash dump.

**Decision.**
- **`io_lockless_watch_check`, `vfs_defer_open_exists_check` and `log_level_gate`:** identical by construction, and §A also passes T2. Turn them on after one A/B pass with clean checks, even if the time difference is within noise.
- **`io_coalesce_scatter_reads` and `io_unlocked_file_reads`:** turn them on if the checks are clean and B's median load time is no worse than A's max.
  - `io_unlocked_file_reads` gains nothing by itself (B4). It only removes the SDK half of the same-file serialization.
- **`pause_safe_order`:** turn it on if Agent 11's test G passes with it on, and the replica stress test (`bench/agent12/pause/RESULTS.md`) shows no hang in the new order.
  - **Both conditions are met (23:35).** In the replica, the old order hung 414 times in 1388 cycles and the new order 0 times in 5000 (`RESULTS.md`). In Agent 11's test G (#23), the safe order passed 100/100 pauses, and the old-order control hung again at 23:22 at the audio fence: `AudioSystem::Pause` waits on `pause_fence_` while the Audio Worker sits in the game's audio callback, in `KeWaitForMultipleObjects` on the guest threads that were just suspended (`build/agent11/runs/20261121-232139-testg-control/hang-232215.txt`; `perf-notes/agent11-kernel.md`, "Test G results (#23)"). Recommended for batch 3: default `pause_safe_order` to true (`src/ui/rex_app.cpp:71`, one line). Dropping the old branch can come later.

## Batch 2: audio shutdown (task #22, from 20:15)

**Status (23:53): done.** The code has not changed since Agent 10's review (22:14), and S2 takes it at OFF (`build/agent2/devoff2-bin`, `build/agent2/native2-bin`). Both checks that waited for the quiet windows passed:
- `-SyntaxOnly` on the 21:56 revision of `audio_system.cpp`: exit 0 (22:23);
- the 1000-run replica, OLD vs NEW, scenarios h, p and b: NEW had 0 HUNG / 0 CRASHED in every case, while OLD h hung or crashed in 68.9% (E5DA67F4) and 60.0% (EFEF2094) of runs (the table at the end of this section).

### Listing

| File (SDK) | snap1 = pristine copy (SHA-256) | Live (SHA-256) | Live mtime |
|---|---|---|---|
| `src/audio/audio_system.cpp` | `7E129AF6EA359947D4CD148D59F92C26984666C422E8D616B80FDA005FFE7A07` | `C281FA8625435EFE352DD4E62043837063BA84D523831ED629A994759A861260` | 21:56:43 |
| `include/rex/audio/audio_system.h` | `8F8A2E71A05258B07DD0A2562F668D97C0FE2327100464A1758D0841FD0823C9` | `4836B139802D34384AB8F00021078893260A22041E7BCB16D1263652C824CF89` | 21:44:35 |

- **Diff:** `build/agent12/batch2-audio-shutdown.diff`, live against `build/agent12/pristine/audio/` (the 11:04:43 files, which equal snap1).
- **New cvar:** `audio_shutdown_detach_worker` (category Audio), default **false**. With the harness: `-Cvar audio_shutdown_detach_worker=true`.
- **Not a closure header.** `audio_system.h` is not in Agent 2's generated-code closure. These 6 TUs include it and rebuild:
  - `audio_system.cpp`;
  - `sdl/sdl_audio_system.cpp` and `nop/nop_audio_system.cpp`, through their own headers, which only .cpp files include;
  - `xboxkrnl_audio.cpp` and `xboxkrnl_audio_xma.cpp`;
  - `ui/rex_app.cpp`.

  Nothing in rexlego or `generated/` includes it.
- **`xthread.*`:** untouched.

### The problem

`Shutdown` waited `kWorkerShutdownTimeout` (500 ms). Then it called `worker_thread_->Terminate(0)`, which goes to `XThread::Terminate` and then `TerminateThread` (`xthread.cpp:585`, `threading_win.cpp:607`).

What the worker does:
- it takes G to read `clients_`;
- it runs guest callbacks, which take G (exports, ENTER sections) and T shared (handle lookups).

What can go wrong:
- **Terminated while holding G:** G is orphaned. The next G acquisition (KernelState teardown) waits forever (H1).
- **Terminated while waiting for G:** the next waiter can crash in ntdll (S4 g1).
- **While paused:** the worker sits in the resume wait and never sees the shutdown event. So Shutdown always timed out and terminated it.

### The fix (cvar on only)

1. **Wake a paused worker.** Shutdown sets `resume_event_` before `shutdown_event_`. The worker wakes, sees `worker_running_ == false` and exits.
2. **Same first wait (500 ms).** If the worker exits, the old teardown runs unchanged.
3. **Bounded cooperative wait.** Wait up to `kWorkerExitGrace` (2000 ms) longer. A slow callback usually returns, the worker exits by itself, and the old teardown runs. This was added at 21:56 so that a detached worker almost never resumes guest code during the runtime teardown (see R1).
4. **Detach instead of terminate.** `AudioSystem::WorkerControl` holds one atomic phase: Inside, Outside or Detached.
   - **Worker side.** The worker wraps each blocking call in `Leave()` (Inside to Outside) and `Reenter()` (Outside to Inside). The blocking calls are WaitAny, the resume wait, taking G, the guest callback and the idle sleep.
     - While Outside, the worker touches no AudioSystem member. It copies the handles, the dispatcher and the thread state it needs into locals while Inside.
   - **`TryDetach()`** swaps Outside to Detached, so it can only succeed while the worker is blocked or running guest code.
     - The worker's next `Reenter()` then fails and it calls `Park()`. `Park()` sleeps 1 hour at a time, forever. It holds no lock and is not alertable, so no APC runs guest code on it.
     - A worker that was waiting for G gets G, fails `Reenter()`, unlocks G and parks.
   - **`ForceDetach()`.** The worker is Inside only for short stretches that never block. If `TryDetach` still has not succeeded after `kWorkerDetachGrace` (2000 ms), `ForceDetach()` sets Detached anyway and logs an error. The worker parks at its next `Leave()` or `Reenter()`.
5. **Leak instead of free.** After a detach, Shutdown does the following, and process exit reclaims everything:
   - It releases `worker_thread_` without dropping the reference. This keeps the XThread alive (thread state, guest stack) along with its `host_fn_` lambda, which owns the `WorkerControl` through a `shared_ptr`.
   - It releases the client semaphores, `shutdown_event_` and `resume_event_` without closing them.
   - It skips `DestroyDriver` and the `SystemHeapFree` of `wrapped_callback_arg`, and leaves `clients_` as it is.
   - It logs one WARN.

The XMA decoder already does the same: it abandons a stuck worker after 2 s instead of terminating it.

### Requirement 1: the normal path behaves exactly as now

**Cvar off (default).** `worker_control_` is null, so `leave()` and `reenter()` do nothing. On a timeout, Shutdown takes the old branch (WARN, then Terminate) and runs the old teardown. The other changes in the worker loop are equivalent rewrites:
- `wait_handles_` is copied into a local array before WaitAny. `WaitMultiple` copies the native handles anyway (`threading_win.cpp:351-359`).
- `resume_event_.get()`, `function_dispatcher_` and `worker_thread_->thread_state()` are read into locals just before they are used.
- `global_critical_region::AcquireDirect()` replaces `global_critical_region_.Acquire()`. Both bodies are `return std::unique_lock<std::recursive_mutex>(mutex());` (`mutex.h:64-71`), and the lock covers the same statements.

**Cvar on, worker exits within 500 ms.** Same sequence, plus 2 uncontended atomic CAS operations per blocking call. The teardown is unchanged. Only the timeout path differs, plus the paused case, which always timed out before.

**Default: behind the cvar, OFF.** Requirement 1 holds by construction even with the cvar on, so the fix could be always on if Agent 10 rates it SAFE. **Agent 10 (22:14, `perf-notes/agent10-batch2-review.md` section 8): SAFE at the default OFF (every path traced; matches snap1) and SAFE-IF ON, the condition being R1/R2.** S2 takes it at OFF. Flipping the default would be a one-line batch-3 change, gated on the post-window `-SyntaxOnly` of C281FA86 (passed at 22:23) and the 1000-run old/new h/p/b replica with NEW at 0 HUNG / 0 CRASHED (met at 23:53; see the table at the end of this section).

### Requirement 3: nothing a detached worker can still use is freed

| What the worker or its guest code can still reach | On the detach path |
|---|---|
| XThread: thread state, guest stack, TLS | leaked (`worker_thread_.release()`) |
| `WorkerControl` | owned by the leaked `host_fn_` |
| Client semaphores (WaitAny; the SDL driver's playback thread releases them) | leaked, not closed |
| `shutdown_event_`, `resume_event_` (the worker waits on local copies) | leaked, not closed |
| Client drivers (`XAudioSubmitRenderDriverFrame` calls SubmitFrame) | `DestroyDriver` skipped |
| `wrapped_callback_arg` (guest heap; the callback's argument) | `SystemHeapFree` skipped |
| AudioSystem members (`clients_`, `paused_`, `wait_handles_`, ...) | not reachable. The worker reads them only while Inside, and a detached worker never gets back Inside, so `audio_system_.reset()` can free the object. |

**Residual risks.** These are outside my files, so I document them and don't fix them.
- **R1: guest code after the runtime teardown.**
  - After `audio_system_.reset()`, `Runtime::Shutdown` continues (`runtime.cpp:299-317`): `kernel_state_.reset()`, `instance_ = nullptr`, `function_dispatcher_.reset()`, `memory_.reset()`.
  - A detached worker whose callback resumes after that can fault on freed kernel or guest memory. The audio exports fetch `REX_KERNEL_STATE()->emulator()->audio_system()` again on each call (`xboxkrnl_audio.cpp:69/86/102`).
  - To get there, the callback has to stay stuck for more than 2.5 s, then come back during the teardown. A callback that stays blocked never resumes.
  - TerminateTitle already uses this policy for the guest threads it leaves running (`kernel_state.cpp:1038`).
- **R2: ForceDetach while the worker is Inside.** An Inside stretch (a log call, the fence Signal, a member copy) would have to stall for 2 s and then touch the freed AudioSystem. The replica reports how often it forces (`forced`).
- **R3: process exit.** ExitProcess ends the parked or blocked worker, as it ends any straggler. In the replica a clean NEW child means the process got through ExitProcess with the worker parked or still running.

**When Shutdown actually runs.** `AudioSystem::Shutdown` is called only from `OnDestroy` (which runs `runtime_.reset()`) and from the setup-failure branches. A normal window close calls TerminateTitle, then `std::_Exit(0)`, and never gets here. Agent 11's #27 (22:31) moves HalReturnToFirmware and XamShowDirtyDiscErrorUI from CRT `exit()` to FlushLogging + `std::_Exit`, like OnClosing. Neither ever reached `AudioSystem::Shutdown`, so #22 needs nothing there: the worker is ended by process exit exactly as on a window close. So the change has no performance effect and needs no in-game A/B. With the cvar off the worker loop gains only null checks; with it on, 2 CAS operations per blocking call.

### Side check: the other TerminateThread sites (read only)

- **`kernel_state.cpp:1038`:** no longer a TerminateThread. The comment there says stragglers are left running on purpose and never force-terminated.
- **`kernel_state.cpp:1065`:** `XThread::GetCurrentThread()->Terminate(0)` takes the self branch (`xthread.cpp:577-583`: FreeStack, ReleaseHandle, then `Thread::Exit`, which calls `ExitThread`).
  - It can leave G held only if the calling guest thread still holds G at that point.
  - The code releases its own scope at 1062-1064. An outer ENTER section or an extra recursion level would still be held.
  - S4 b showed that a thread that exits while holding G orphans it.
- **`xboxkrnl_threading.cpp:184`:** `ExTerminateThread` calls `XThread::Exit`, which calls `ExitThread`. This is also a self-exit.
  - It orphans G only if the guest caller holds G when it calls in.
  - `OnThreadExit` takes G and releases it again.
- **`threading_win.cpp:607`:** the raw primitive.
  - Its only caller that stops another thread is the else branch of `XThread::Terminate` (`xthread.cpp:585`). That branch is reached only from `audio_system.cpp`, the site fixed here behind the cvar.
  - `threading_posix.cpp:1520` is the POSIX build only.
- **Answer.** With the cvar on, no site can orphan G by stopping another thread. The 2 self-exit sites (1065 and 184) can leave G held only when the exiting guest thread already holds it (the S4 b hazard). A guard there is Agent 11's call.

### Tests

**Compile.** At 21:45-21:47 the 21:45 revision (`D2CA066A...`) passed `env\compile-one.ps1 -SyntaxOnly` (exit 0) in all 6 includer TUs (`build/agent12/batch2_syntax.log`).
- The only warnings are existing unused-parameter ones in `decoder.h`, `xmemory.h` and `rex_app.h`.
- The 21:56 revision (`C281FA86...`) changes only `audio_system.cpp`:
  - the exit grace, which is one more `rex::thread::Wait(host_thread, false, ms)` call (the same overload as `:305`);
  - one log argument;
  - comments.
- **Re-check (22:23):** `-SyntaxOnly` of `audio_system.cpp` at `C281FA86...` gave exit 0 in 17.9 s, again with only the 2 `decoder.h` warnings (`build/agent12/batch2_syntax_recheck.log`). PASS went to Agent 2 and Agent 10 at ~22:26. The header did not change, so the other 5 TUs keep their 21:45-21:47 results.

**Replica.** The source is `bench/agent12/gcr/audio_shutdown_replica.cpp`. `bench/agent12/gcr/build_audio_shutdown_replica.cmd` builds it into `build/agent12/gcr/`. It is standalone and builds on S4 (`terminate_while_holding.cpp`). `bench/agent12/gcr/run_audio_shutdown_replica.ps1 -Cases "new h,old h,new p,old p,new b,old b" -Runs 1000` runs the cases one after another (one parent, at most 2 children at a time), writes each full output to `build/agent12/gcr/audio_shutdown_replica.<mode>_<scenario>.log` and records the machine CPU load at the start and end. A hung child is ended by its parent, so some of its buffered lines can be lost; the RESULT line is authoritative.
- `WorkerControl` is copied verbatim. The worker loop and Shutdown mirror the SDK code.
- G is a static `std::recursive_mutex`, and a straggler thread keeps contending for it.
- Each run is one child process:
  1. Main runs the OLD or NEW `Shutdown`.
  2. Main makes the model and (unless leaked) the driver `PAGE_NOACCESS`, so any late access faults.
  3. Main takes G, then a fresh thread takes G.
  4. Main returns, which goes through CRT exit and ExitProcess.
- Watchdogs: the child's own is 1 s (Shutdown plus teardown) and the parent's is 10 s (process exit). In p, Pause() is bounded at 3 s (exit 0xBAD0, counted as other).
- All times are scaled to 1/25: timeout 20 ms, exit grace 80 ms, detach grace 80 ms.
- Scenarios:
  - **h:** the callback takes G for about 1 ms at a time, 40 to 220 times depending on the run.
  - **p:** shutdown while paused. Pause() sets the shutdown event and waits for the worker's pause fence, and the worker parks in the resume wait. The callback takes G twice and does not re-release the client semaphore, so the 8 queued frames drain.
  - **b:** the callback blocks forever without holding G.
- Usage: `audio_shutdown_replica.exe <old|new> <h|p|b> <runs> [parallel<=2]`.
- **p fix (23:31).** The first p run (23:19, exe `E5DA67F4...`) hung in every child, inside Pause(), before Shutdown was reached. It logged 68 runs before I stopped it at 23:25 (`build/agent12/gcr/audio_shutdown_replica.new_p.partial-2325.log`); the parent's 10 s timeout reported each one as hung.
  - Cause: that revision re-released the client semaphore at the end of every callback, like a playback thread with no rate limit, so the count never drained. WaitForMultipleObjects reports the lowest signaled index, so the worker never saw the shutdown event that Pause() sets and never signaled the pause fence.
  - A replica bug, not an SDK one: in the SDK the SDL callback releases one count per played frame (`sdl_audio_driver.cpp:222`), so the count drains whenever the guest callback keeps up with playback.
  - The 23:31 revision (source `BA71FE80...`, exe `EFEF2094...`) changes only p: no re-release, 2 G holds per callback, and a 3 s bound on Pause(). The parent's hang message now says "hung" instead of "process exit hung". The h and b code paths are unchanged; h was re-run on the new exe anyway.

| Run | Revision | Result |
|---|---|---|
| old h, 20 runs (smoke, 21:50) | before the exit grace; 40 holds per callback | 7 clean (3 exited, 4 terminated: 1 while waiting for G, 3 elsewhere). **9 HUNG**: the printed watchdog lines show the worker terminated while holding G. **4 CRASHED**: the printed crash is 0xC0000005 in ntdll, with the worker terminated while waiting for G. |
| new h, 20 runs (smoke, 21:50) | before the exit grace; 40 holds per callback | 20 clean (20 detached, 0 forced), 0 HUNG, 0 CRASHED |
| new h, 1000 runs (22:25-22:27, machine CPU load 65-90%) | exe E5DA67F4 | **1000 clean**: 3 exited normally, 997 detached, 0 forced; 0 terminated; 0 HUNG, 0 CRASHED, 0 other (wall 134 s). Log: `audio_shutdown_replica.new_h.E5DA67F4.log`. |
| old h, 1000 runs (23:13-23:19, machine CPU load 88% to 80%) | exe E5DA67F4 | 311 clean: 294 terminated (35 holding G, 91 waiting for G, 168 elsewhere), 17 exited normally; **464 HUNG, 225 CRASHED**, 0 other (wall 323 s). Printed lines: 461 child-watchdog hangs (458 complete lines, all with where=2, i.e. the worker was terminated while holding G; 3 garbled by interleaved output) and 3 parent timeouts; 225 crashes, all 0xC0000005 in ntdll with where=1 (the worker was terminated while waiting for G). An earlier attempt (22:27) was stopped at run ~204 by quiet window 2, with 61 CRASHED and 90 HUNG by then (`audio_shutdown_replica.old_h.partial-2228.log`). Log: `audio_shutdown_replica.old_h.E5DA67F4.log`. |
| new p, 1000 runs requested (23:19) | exe E5DA67F4 | **Invalid (replica bug):** every child hung in Pause() before Shutdown; 68 had been logged when I stopped it at 23:25. See "p fix" above. |
| p and b smoke, 20 runs each (23:31) | exe EFEF2094 | new p: 20 clean (20 exited normally). old p: 20 clean (20 terminated, elsewhere). new b: 20 clean (20 detached, 0 forced). old b: 20 clean (20 terminated, elsewhere). Log: `audio_shutdown_replica.smoke-pb.log`. |
| new h, 1000 runs (23:44-23:47, machine CPU load 68% to 99%) | exe EFEF2094 | **1000 clean**: 16 exited normally (2 of them in the exit grace), 984 detached, 0 forced; 0 terminated; 0 HUNG, 0 CRASHED, 0 other (wall 142 s). |
| old h, 1000 runs (23:47-23:52, machine CPU load 99% to 86%) | exe EFEF2094 | 400 clean: 371 terminated (70 holding G, 71 waiting for G, 230 elsewhere), 29 exited normally; **429 HUNG, 171 CRASHED**, 0 other (wall 312 s). Printed lines: 422 child-watchdog hangs (422 complete lines, all with where=2, i.e. the worker was terminated while holding G); 5 parent timeouts; 171 crashes (170 complete lines reading 0xC0000005 in ntdll with where=1, i.e. the worker was terminated while waiting for G). |
| new p, 1000 runs (23:32-23:36, machine CPU load 36% to 100%) | exe EFEF2094 | **1000 clean**: 1000 exited normally, 0 detached, 0 forced; 0 terminated; 0 HUNG, 0 CRASHED, 0 other (wall 266 s). The resume-first wakes the parked worker, which exits within the timeout. |
| old p, 1000 runs (23:39-23:43, machine CPU load 71% to 68%) | exe EFEF2094 | **1000 clean**: 1000 terminated (0 holding G, 0 waiting for G, 1000 elsewhere), 0 exited normally; 0 HUNG, 0 CRASHED, 0 other (wall 246 s). The worker is parked in the resume wait, so every run waits out the full timeout and then terminates a worker that holds nothing. |
| new b, 1000 runs (23:36-23:39, machine CPU load 100% to 59%) | exe EFEF2094 | **1000 clean**: 73 exited normally (24 of them in the exit grace), 927 detached, 0 forced; 0 terminated; 0 HUNG, 0 CRASHED, 0 other (wall 149 s). TryDetach succeeds at once, because the worker is Outside, blocked in the guest wait. A worker that exited normally had not reached the callback when Shutdown cleared `worker_running` (most likely a late thread start under load). |
| old b, 1000 runs (23:43-23:44, machine CPU load 60% to 65%) | exe EFEF2094 | 998 clean: 998 terminated (0 holding G, 5 waiting for G, 993 elsewhere), 0 exited normally; **0 HUNG, 2 CRASHED**, 0 other (wall 65 s). Printed lines: 2 crashes (2 complete lines reading 0xC0000005 in ntdll with where=1, i.e. the worker was terminated while waiting for G). The worker is normally blocked in the guest wait, without G. Both crashes are runs in which it had not got there yet and was terminated while waiting for G (S4 g1). |

**Verdict.**
- **NEW never terminated the worker and never hung or crashed:** 0 HUNG, 0 CRASHED and 0 other in 4000 runs (1000 each of h, p and b on EFEF2094, plus 1000 h on E5DA67F4). ForceDetach never fired (forced = 0 everywhere), so R2 never came up.
- **OLD h hung or crashed in 68.9% of runs on E5DA67F4 and 60.0% on EFEF2094.** Every complete hang line had the worker terminated while holding G (H1). Every complete crash line was 0xC0000005 in ntdll with the worker terminated while waiting for G (S4 g1).
- **OLD p was clean and OLD b almost clean (2 CRASHED in 1000)**, because the worker they terminate usually holds nothing: it is parked in the resume wait (p) or blocked in the guest wait without G (b). The 2 OLD b crashes are runs in which the worker had not reached the guest wait yet and was terminated while waiting for G (S4 g1).
- **What NEW costs:** when the worker is stuck (b), Shutdown waits the 2 s exit grace on top of the 500 ms timeout before it detaches (scaled: 20 + 80 ms), where OLD terminates after 500 ms. In p it is the other way round: OLD always waits out the timeout, while NEW wakes the worker and it exits at once. Shutdown runs only from OnDestroy, so neither delay reaches a normal window close.
- The RESULT line is authoritative. A few printed lines are lost or garbled when two children print at once or when a parent ends a hung child. The `where` of a clean OLD termination is sampled just before TerminateThread, so it is approximate.

## S4 (#21): the write-tracking re-arm on the devoff GPU Commands thread

Task #21 (Agent 1, 04:54), analysis only: read-only on both source trees, no builds, no game runs, no source edits. S4 is the landing stage after S3. It has nothing to do with the `S4` bench (terminate_while_holding) behind "S4 b" and "S4 g1" in the batch-2 sections. Line numbers are for the live SDK tree (HEAD 90e7ccd plus the 2 S3 files, which don't touch this path). The keep-watch proposal (P1) is one combined proposal with Agent 5 (#20); S4.5 says who writes what.

**Inputs and caveats.**
- Profiles come from Agent 8's matrix `build/agent8/matrix/20261122-0357/runs/`, read with Agent 7's `prof_main_compare` folds:
  - a = `0357-a-prof-r1` (devoff2): 67.66 fps, 191 rounds, 0.077385 ms/f per sample;
  - b = `0401-b-prof-r1` (devoffB): 67.77 fps, 188 rounds, 0.078485 ms/f per sample;
  - `0405-n-prof-r1` (native), for context only.
- Tool: `bench/agent12/s4_waits.py`, which builds on `prof_main_compare` to give the busy/wait split and leaf buckets per thread. Outputs in `build/agent12/s4/`: `a-waits.txt`, `b-waits.txt`, `ab-gpucmd-compare.txt` and `.json`. The `.err` files hold only the sampling warning.
- A bucket of k samples has a standard error of about √k. The re-arm buckets (9 vs 18 samples) differ at p≈0.12. Agent 9 also showed that the host DLLs are byte-identical and that the guest caller makes the same 5 calls in both. So I treat a/b differences as run variation and pool a and b for shares.
- Scene: the static title scene (~226 draws per frame). perf.csv has no upload or invalidation counter, and no run set `slow_frame_log_ms`. The per-frame counts in S4.2 are therefore estimates; step 1 of S4.6 measures them.

### S4.1 Where GPU Commands spends its time

| GPU Commands | a samples | b samples | a ms/f | b ms/f | Share of busy (a+b pooled) |
|---|---|---|---|---|---|
| Busy | 109 | 120 | 8.44 | 9.42 | 100% |
| Wait | 82 | 68 | 6.35 | 5.34 | - |
| UploadRanges (d3d12) | 47 | 49 | 3.64 | 3.85 | 42% |
| -> memcpy (fn_11200 + fn_10E40) | 40 | 37 | 3.10 | 2.90 | 34% |
| -> re-arm (MakeRangeValid -> 3 x EAC) | 7 | 12 | 0.54 | 0.94 | 8% |
| Re-arm on the resolve path (RangeWrittenByGpu) | 2 | 6 | 0.15 | 0.47 | 3.5% |
| **Re-arm total** | **9** | **18** | **0.70** | **1.41** | **11.8% (27/229)** |
| Batch-1 fence in EAC | 0 | 0 | 0 | 0 | 0% |

- **Re-arm by leaf** (a / b samples):
  - an SRW release that wakes a waiter (`_Mtx_unlock > RtlReleaseSRWLockExclusive > NtSetInformationThread`): 4 / 14;
  - VirtualProtect(RO): 3 / 3;
  - the page loop itself: 2 / 1.
- **Waits** (a / b samples): MaybeYield/SwitchToThread 49 / 40, SleepPrecise 26 / 23, WaitForSingleObjectEx 5 / 3, waiting for G 2 / 1, other 0 / 1.
  - GPU Commands seldom waits for G. What it pays is the wake of G's waiters each time it releases G.
  - Those waiters: XThreads and the Audio Worker in GetNativeObject / ObjectTable::LookupObject, VSync and GPU Commands in ExecuteInterrupt, and Main in sub_82C9DB88.
- **Main** (guest XThread): MmSetAddressProtect 7 / 13 samples (0.54 / 1.02 ms/f), mostly VirtualProtect.
  - Main waits 144 / 141 samples (~11.1 ms/f) in a guest RtlEnterCriticalSection and is busy only ~3.6 ms/f, so it isn't on the critical path.
  - Agent 7 (`agent7-present.md:298`): Render spends ~94% of its time in the ring-buffer wait, so the title waits on GPU Commands.
- **Faults:** the VEH (access-violation) bucket has 1 / 0 samples over all threads, so write faults are ≈0 per frame. That fits the chain below, because the Lock unwatches a block before the guest writes it.

### S4.2 What re-arms every frame

**Not `clear_memory_page_state`.**
- All three runs' `legodimensions.toml` have `clear_memory_page_state = false`. Agent 1 checked all 12 matrices and the installer too (`rexlego-installer/TomlConfig.cs:139`; `SESSION2.md:1670-1675`).
- Agent 6's "0 cpu-write invalidations" logs are synthetic fixtures, not measurements: `build/agent6/attract-stalls/fixture-slowframe/{A,B}/game.log`, stamped 03:20:00.000, thread t4242.
- Agent 5 reached the same conclusion independently (~05:39).

**The chain, per frame.** This is read from the source; Agent 5 and Agent 1 agree.
1. **Lock, on guest Main.** sub_82B55588 -> sub_82BD2808 -> `MmSetAddressProtect(base, size, 4)` (PAGE_READWRITE), or 0x404 (READWRITE | WRITECOMBINE) when the lock flags have 0x10. The pages are RW before and after; at most the cache attribute changes.
   - `src/kernel/xboxkrnl/xboxkrnl_memory.cpp:484-503`: FromXdkProtectFlags, then `heap->Protect(...)` at :502 with no old_protect.
   - `PhysicalHeap::Protect` (`src/system/xmemory.cpp:2128-2144`) takes G at :2130. The protect has Write, so :2135 calls `TriggerCallbacks(std::move(global_lock), ..., is_write=true, unwatch_exact_range=true, unprotect=false)`. If any page of the range is watched:
     - `SharedMemory::MemoryInvalidationCallback` (`src/graphics/shared_memory.cpp:502-575`) adds to `kMemoryInvalidate` (:509, every call; this is the "cpu-write invalidations" counter);
     - it clears the valid bits of the exact range (:553-563);
     - it fires the texture watches (`FireWatchesLocked`, :571);
     - PrimitiveProcessor's callback (registered at `primitive_processor.cpp:1364`, body at :1428) runs as well;
     - finally TriggerCallbacks clears the watch bits (:2416-2427) and releases G.
   - Then `parent_heap_->Protect` (:2138, the host-only physical view) and `BaseHeap::Protect` (:2143) each make a VirtualProtect(RW) (:1772), **without G**:
     - `AcquireHostPageReconcileLock` (:968-973) returns an empty lock when the guest page is at least the 4 KB host page;
     - `SyncHostPageAccess` (:975+) returns early for the same reason, so its watch clamp (:1044-1046) never runs on Windows.
2. **Unlock, on guest Main.** It is the same call. Nothing in the range is watched any more, so TriggerCallbacks returns at the any-watched check (:2306-2323). The 2 VirtualProtect(RW) calls run again.
3. **Next draw, on GPU Commands.**
   - `IssueDraw` (`d3d12/command_processor.cpp:2848`) calls `SharedMemory::RequestRanges` (`shared_memory.cpp:360-489`), which collects the invalid runs under one G hold (:427-476).
   - Then `D3D12SharedMemory::UploadRanges` (`d3d12/shared_memory.cpp:304-339`) handles each chunk of up to 2 MiB:
     - `RequestPartial` (:318-321);
     - `MakeRangeValid` (:326 -> `shared_memory.cpp:303-336`). G hold 1 (:314-329) sets the valid bits. Then, with G released, `EnablePhysicalMemoryAccessCallbacks` (:331-335) calls `EnableAccessCallbacks` for each of the 3 physical views vA/vC/vE (`xmemory.cpp:702-711`); those are G holds 2-4 (:2195). Each one walks its pages (:2196-2261), makes one coalesced VirtualProtect(RO) per run of writable, unwatched pages (:2256, :2263), and then runs the fence (:2267-2270). In the views where the block isn't committed, every page is skipped;
     - the memcpy from `TranslatePhysical` (:327-329) and the copy-buffer command (:330-332).
   - So each chunk costs 4 G acquire/release pairs, and every release that has a waiter pays a wake (the 4 / 14 samples above).
   - The arm comes before the copy: a write after the arm faults, and a write before it is in the copy.
4. **Resolves, on GPU Commands.** `RangeWrittenByGpu` (`shared_memory.cpp:277-293`) is `FireWatches` (its own G hold, :231) plus `MakeRangeValid(..., true)`: 5 G pairs.

**Granularity.**
- **Protects:** one exact range in one view, in 4 KB pages. The guest locks whole blocks (see below).
- **Invalidation:**
  - On a protect: the exact range.
  - On a fault: widened to 256 KB blocks, stopping at GPU-written pages (`shared_memory.cpp:531-551`). The unwatch is the intersection of the callbacks' ranges plus the faulting pages, capped to a 4 MB window (`xmemory.cpp:2346-2377`).
  - In both cases the unwatched pages are a subset of the invalidated ones.
- **Re-arm:** one VirtualProtect(RO) per coalesced run (at most 2 MiB) per view. Pages that are already watched, read-only or uncommitted are skipped.

**Who locks what.** My research subagent surveyed the generated code statically.
- sub_82B55588 has 21 call sites, all in one TT-style relocatable handle-heap module (0x82B55xxx-0x82B59xxx): 8 Lock, 13 Unlock. At 20 of the 21, r6 = -1 (whole block).
- sub_82BD2808 has 3 sites, all inside sub_82B55588.
  - When size < 0 it uses the whole block (`[obj+4] & 0x3FFFFFFF`), and it tail-calls MmSetAddressProtect (sub_83F9F4D8) without reading r6.
  - It skips the protect only when (flags & 8) && !(flags & 0x200). The only caller that passes 8 is 301:13132 (through a forwarder), and the block's own attributes must have 8 as well.
- LockHandle (sub_82B590E8): 12 direct sites plus 14 through the forwarders sub_82CBC020 and sub_82BD5C80. Flags are 0, 0x10, 0x1000 (probably "don't wait"), and 0x8 once.
- UnlockHandle (sub_82B56480): 9 direct sites plus 11 through sub_82CEA7D0 and sub_82BD5D20. Size is -1 at all but 2.
- Defrag and Migrate run from the periodic sub_82B592A8 (`37.cpp`).
- Not known: which blocks hold vertex, index or UI data. Indirect calls aren't ruled out.
- Agent 9 (`agent9-codegen.md:379-390`) puts ~1.19 ms/f under sub_82B55588.
- **So nearly every Lock and every Unlock is one MmSetAddressProtect over the whole block. The whole block is invalidated, re-uploaded and re-armed even when only part of it, or none of it, is written.** That is why u (S4.4) is probably large in this scene.

**Counts per frame.** These are estimates from the sample counts and the call structure, not counted events; step 1 of S4.6 measures them.

| Event | Estimate per frame | Thread |
|---|---|---|
| MmSetAddressProtect (Lock + Unlock) | ~10-30 | Main |
| VirtualProtect(RW) from those calls | ~20-60 (2 per call) | Main |
| Invalidating TriggerCallbacks (`kMemoryInvalidate`, "cpu-write invalidations") | ~5-15 (Locks of watched blocks) | Main |
| MakeRangeValid chunks; VirtualProtect(RO) re-arms (1 per coalesced run and view) | ~5-15 | GPU Commands |
| G acquire/release pairs on the re-arm path | ~20-60 (4 per chunk, 5 per resolve) | GPU Commands |
| Write faults | ≈0 (1 sample in 2 runs) | any |

### S4.3 The batch-1 fence in EnableAccessCallbacks

- **What it is:** a seq_cst fence at the end of EAC (`xmemory.cpp:2267-2270`), under G, after the watch bits are set.
  - It pairs with the fence at the top of `MayHaveWriteWatches` (:2432-2437), which only the `io_lockless_watch_check` file-read path uses.
  - Together they guarantee that a lockless writer either sees the new watch bits or wrote its data before the caller's read for the upload.
- **Cost:** it runs 3 times per MakeRangeValid (once per view), well under 2 µs per frame, and has 0 samples in both profiles. It plays no measurable part in this cost.
- Skipping it when EAC set no new bit would be correct, but isn't worth a change. Every proposal below keeps it.

### S4.4 Proposals, ranked

All are new cvars, default OFF. With the cvar off, the code path is unchanged.

**u** is the fraction of each frame's upload that copies unchanged data. It is unknown until steps 3-4 of S4.6 (the S4.9 diagnostic gives an upper bound first), but the whole-block locks suggest it is large in the static title scene.

**The savings aren't additive.** P1 removes u of the uploads together with their re-arms, so P2 then saves only on the rest.

| Rank | Proposal | Saving on GPU Commands (busy 8.4-9.4 ms/f) | Other | Risk | Files |
|---|---|---|---|---|---|
| 1 | **P1, keep watches on RW -> RW protects** (Agent 5 and Agent 12; Agent 5's C1) | u x 3.6-3.8 ms/f (u x 42% of busy), minus block-widening re-uploads (S4.8) | Main saves 0.5-1.0 ms/f and pays 5-15 µs per written 256 KB block (S4.8) | medium | `src/system/xmemory.cpp/.h`, `src/graphics/shared_memory.cpp/.h`, `src/graphics/primitive_processor.cpp`; optional frame_stats ids |
| 2 | **P2, one G hold per re-arm** | alone: 0.23 (a) / 0.82 (b) ms/f, ~6% of busy. After P1: (1-u) x the upload part, plus the resolve part | - | low | `src/graphics/shared_memory.cpp` |
| 3 | **P3, arm once per UploadRanges** | only ranges over 2 MiB (several chunks) | - | low-medium | `src/graphics/d3d12/shared_memory.cpp` (Vulkan optional) |
| 4 | **P4, hot-range demotion** | the re-arm part only; can add memcpy | - | medium | `src/graphics/shared_memory.cpp/.h` |

**P1 (rank 1): `physical_protect_keep_watch`.** This is one combined proposal with Agent 5, whose #20 calls it C1 (at first "S4 P1, watch-preserving Protect"). Agent 5 found independently that the game's protects never change access, and supplied the bypass-writer list for Agent 10. I wrote conditions 1 and 3 below and the output-identical argument.

*Change.* Add a fast path at the top of `PhysicalHeap::Protect`. It runs under G, then under the `heap_mutex_` of the view and of the parent (G before heap_mutex_ is the legal order, `xmemory.cpp:1746-1748`). Take it only when all four conditions hold; otherwise run the old path unchanged.
1. The cvar is on and `old_protect == nullptr`.
   - MmSetAddressProtect (`xboxkrnl_memory.cpp:502`) qualifies.
   - NtProtectVirtualMemory (:282) passes `&tmp_old_protect`, so it keeps the old path. Today its old protect comes from the parent's host VirtualProtect (:2138), which the fast path wouldn't call.
2. Every page of the range, in the view and in the parent, is committed, in one region, and has `ToPageAccess(current_protect) == ToPageAccess(protect)` (Agent 5's form; here it is always RW -> RW).
   - WC and NoCache don't reach `ToPageAccess` (`xmemory.cpp:930-941`), so the game's 4 and 0x404 protects both qualify.
   - A protect without Write never calls TriggerCallbacks, so for it the fast path skips only the 2 VirtualProtect calls, which would change nothing.
   - The commit and region checks are the validation that `BaseHeap::Protect` does (:1752), so a request that would fail still fails the old way.
3. No page of the range is `valid_and_gpu_written` in SharedMemory.
   - Why: for GPU-written pages the old path's invalidation re-uploads guest memory over the resolved data, so skipping it could change the output.
   - This needs a guard hook that SharedMemory registers along with its invalidation callback.
   - Every other registered callback needs a hook too. PrimitiveProcessor (`primitive_processor.cpp:1364`) gets an always-allow hook, and any callback without a hook forces the old path. rexlego's memory-watch callback deliberately gets none, so the native route always takes the old path (S4.8).
4. (Agent 5, #20) No page of the range has `provide_data` set. The old path's host VirtualProtect(RW) over the whole range (`BaseHeap::Protect`, `xmemory.cpp:1772`, run for the parent at :2138 and the view at :2143) also makes data-provided pages host-RW. The fast path would leave them protected, which is a behaviour difference.

The fast path only writes `current_protect` in both page tables: no TriggerCallbacks and no VirtualProtect. Guest-visible protection queries return the same values as today.

*Output-identical argument.*
- **Invariant I:** a valid page is watched in every view where the guest can write it.
  - The one exception is inside MakeRangeValid, between setting the valid bit and arming. The memcpy comes after the arm, so it covers that window.
  - The fast path keeps the valid bits, the watch bits and the host RO protection, so I still holds.
- **If the guest doesn't write the block** before the next draw that reads it, the old path only re-uploads and re-decodes the same bytes, so skipping that is invisible.
  - The exception is GPU-written pages, where the re-upload from guest memory would replace GPU data. Condition 3 sends those to the old path.
- **If the guest writes,** the first write to each watched block faults.
  - The handler invalidates (256 KB extent, unwatch ⊆ invalidated) and fires the texture and PrimitiveProcessor callbacks before the write retires.
  - That is before the guest can submit the draw that reads it: the same ordering the lock-time invalidation gives today.
- **What changes:**
  - Invalidation moves from lock time to write time, and covers 256 KB blocks around the written pages instead of the exact locked range. Neighbours in the same 256 KB may re-upload, with the same bytes.
  - `kMemoryInvalidate` and the "cpu-write invalidations" log count less.

*Expected.*
- GPU Commands saves u x 3.6-3.8 ms/f.
- Main saves 0.5-1.0 ms/f (MmSetAddressProtect is 0.54 / 1.02). Main isn't on the critical path, so this mostly shortens its G holds.
- New cost (S4.8): 5-15 µs (central 8) per first write to each 256 KB block, per view, on the writing thread (fault, TriggerCallbacks, one VirtualProtect, under G). At u_block = 0 that is up to V / 256 KB + L faults per frame, ~0.1-1.1 ms/f for 3-30 MB/f. Faults are ≈0 today because the lock unwatches before the guest writes; with P1, each written block faults about once per frame.
- On the native route rexlego's callback would make it one fault per 4 KB page, so P1 keeps the old path there (condition 3).
- Side effect: it closes the S4.7 race for RW -> RW protects.

*What Agent 10 must rate.*
1. **Bypass writers:** host code that writes guest physical memory into a block the guest locks, through an unwatched host view (`TranslatePhysical` or the parent view) and without calling TriggerCallbacks. Such code relies on the next Lock to invalidate the block. Agent 5's candidates:
   - `graphics/command_processor.cpp` :315, :437, :1289, :1305, :1368, :1415, :1444, :1465, and the d3d12 occlusion-query write at :426;
   - the XMA PCM output, `xma_context.cpp:337`;
   - cheat_engine StoreValue, :419 and :502;
   - rexlego's PoolCopyHook memmove (`hooks_buffer.cpp:197-198`, :343-345). Its `InvalidateCpuPhysicalMemory` notifies only rexlego's own watch (`memory_watch.cpp:151-154`), not SharedMemory. **This is the likeliest real bypass on devoff, if the hook copies handle-heap blocks through the host view;**
   - rexlego `textures.cpp:3758-3760`.

   Known safe: xfile reads (TriggerCallbacks, or MayHaveWriteWatches with `io_lockless_watch_check`), and readback and memexport (their pages are GPU-written, so condition 3 sends them to the old path).
2. The registered invalidation callbacks and their hooks. Always-allow is right for PrimitiveProcessor if it caches only ranges that RequestRange armed first.
3. Condition 3 and the old_protect restriction.
4. That nothing depends on lock-time side effects other than diagnostics.
5. The fault side (S4.8): rexlego's callback stays without a hook, block widening is output-identical, and the fault path's G hold is acceptable at its new rate.

*Test.*
1. Agent 2 builds it with counters: protects kept by P1, fault invalidations, and upload bytes and chunks per frame. The ON runs must show faults per frame inside S4.8's [F_min, F_max], and no "Recovered stale physical page protection" or "Unhandled guest physical write fault" lines.
2. Functional ON runs with `--slow_frame_log_ms=1`; logdiff NEW 0.
3. A frame hash or screenshot of the title scene and of Agent 3's menu walk, plus one level load for the fault path.
4. Agent 8's ABBAAB pair plus a profile.

**P2 (rank 2): `shared_memory_single_hold_rearm`.**
- **Change:**
  - In `MakeRangeValid`, keep the G hold of :314-329 through `EnablePhysicalMemoryAccessCallbacks` (:331-335).
  - In `RangeWrittenByGpu`, hold G once around `FireWatches` and `MakeRangeValid`.
  - G is recursive, so the inner acquires in EAC (:2195) and FireWatches (:231) become uncontended re-entries. Releases go from 4 to 1 per chunk and from 5 to 1 per resolve.
- **Output-identical:** the same work runs in the same order; only release points go. EAC and FireWatches take only G (no `heap_mutex_`), so there is no new lock-order edge.
- **Expected:** ~¾ of the wake samples, 0.23 / 0.82 ms/f (~6% of busy) on its own. G's total hold time is unchanged: its waiters wait for one longer hold instead of four short ones.
- **Agent 10 rates:**
  - the recursion argument;
  - that EAC acquires G once (:2195) and takes no `heap_mutex_`;
  - the longer single hold against G's waiters (object lookups on XThreads and the Audio Worker, interrupts on VSync).
- **Test:** build; functional devoff and native runs; ABBAAB. The EAC > `_Mtx_unlock` samples should drop by about ¾.

**P3 (rank 3): `shared_memory_batch_arm`.**
- **Change:** two passes in d3d12 `UploadRanges`:
  1. `RequestPartial` for every chunk;
  2. one MakeRangeValid (one arm) for the whole range, then the memcpys.
- **Expected:** it saves 3 EAC passes and 4 G pairs per extra chunk, so it helps only ranges over 2 MiB.
- **Failure path:** if a `RequestPartial` fails, the pages already marked valid must still be armed and copied, so mark valid only the chunks that got a buffer.
- Vulkan (`vulkan/shared_memory.cpp:303`) is optional.

**P4 (rank 4): hot-range demotion.**
- **Change:** a range that a protect invalidates on N frames in a row stops being armed, and is re-uploaded at every use without a re-arm.
- Only worth doing if P1 is rated unsafe: it removes the re-arm but can add memcpy.

**Rejected.**
- Set `clear_memory_page_state = false`: it already is, everywhere.
- A lockless "already watched" early-out in EAC:
  - it never fires here: the owning view was just unwatched, and the other views skip the block as uncommitted;
  - reading `page_table_` without G would race.
- Coarser granularity: re-arms are already coalesced runs per view.
- Arming after the memcpy: writes between the copy and the arm would be lost.
- Comparing (memcmp) before uploading: it costs as much as the copy.
- Holding G across the memcpys: it adds ~3 ms/f of G hold for every other thread.
- MEM_WRITE_WATCH / GetWriteWatch: not available for file-mapping views.
- Removing the fence: it costs nothing (S4.3).

**Landing order.**
1. Build P1 and P2 together, both cvars OFF.
2. Turn on P2 first (low risk).
3. Turn on P1 after Agent 10's rating, the counter run, the diagnostic run (S4.8's decision rule) and an A/B.
4. P3 only if the counters show uploads of several chunks.
5. P4 only if P1 is rated unsafe.

### S4.5 Agent 5 (#20): one combined proposal

- **Background:** Agent 5 found the same cause independently and proposed the same change as P1. Agent 1 (05:48) asked for one combined proposal, counted once.
- **Split (Agent 5's proposal, accepted ~05:55):**
  - Agent 5 writes the one combined S4 entry in its notes (by ~06:40). It calls the change C1 (= P1 here) and folds in conditions 1 and 3, the S4.7 race note and P2-P4 with their ms/f, which I sent at ~05:55;
  - this section keeps the full design text, the output-identical argument and the Agent 10 checklist, and the combined entry links here;
  - Agent 5 owns the bypass-writer audit list (copied into P1 above) and the memcpy work, and numbers its items so that they don't collide with P2-P4.
- **Counted once:**
  - P1's saving is u x the UploadRanges bucket (memcpy plus re-arm, 3.6-3.8 ms/f);
  - Agent 5's memcpy speed-ups apply only to the bytes P1 still uploads, at most (1-u) x 2.9-3.1 ms/f;
  - P2 applies only to the re-arms that are left.

  So together they can't exceed the UploadRanges bucket (42% of busy) plus the resolve-path re-arms (3.5%).

### S4.6 Measurement plan

1. **Counter run, no build (#27: Agent 5's arm a-vol).** `bench/agent5/matrix-s4-invalvol.json` runs devoff2 with `--slow_frame_log_ms=1` (~5 min) as priority 2 in Agent 8's 06:33-07:15 slot (functional only). `bench/agent5/s4_slowframe.py` reads it.
   - Every frame over 1 ms logs its frame_stats, including `kMemoryInvalidate` (count, with bytes in extra; `src/graphics/frame_stats.h:29`).
   - Expect ~5-15 invalidations per frame. ≈0 (mean < 1, p50 0) falsifies the chain.
   - KB per invalidation = mean KB / mean count, which is the lock size. ≈4 KB would mean the invalidations are fault-driven, not lock-driven.
   - It gives L and V for S4.8 (F_max = V / 256 KB + L). u comes from steps 3 and 4.
2. **Build.** Agent 2 builds P1, P2 and the u diagnostic (S4.9) behind their cvars (all OFF) in one build, with counters: protects kept by P1, fault (non-exact) invalidations and their bytes, and upload bytes and chunks per frame.
3. **Diagnostic run.** One functional devoff run with the S4.9 cvar ON. Apply S4.8's decision rule before P1 is turned on.
4. **ON runs.**
   - Functional runs with each cvar alone, then both: title scene, Agent 3's menu walk, one level load.
   - Then Agent 8's ABBAAB pairs, with one profile each.
   - Read the GPU Commands busy share, the UploadRanges and re-arm buckets, Main's MmSetAddressProtect bucket, the counters and fps. u = 1 - (upload bytes with P1 on) / (upload bytes with P1 off).

### S4.7 For Agent 10: an existing race in PhysicalHeap::Protect (upstream code)

**The race.** TriggerCallbacks releases G (:2135) before the two VirtualProtect(RW) calls (:2138, :2143). Suppose GPU Commands runs RequestRanges -> MakeRangeValid -> EAC on the same pages in that gap:
1. EAC sees writable, unwatched pages (`current_protect` is still RW), protects them RO and sets their watch bits.
2. Main's VirtualProtect(RW) then makes them writable again.
3. The pages are now valid and marked watched, but host-writable. The guest's writes aren't caught until the next Lock invalidates the block, so up to a frame of data can be stale.

For RO -> RW the gap has a second form: EAC skips the still-RO pages, which then become writable while valid and unwatched.

**When it can happen.** It needs the guest to lock a block that pending draws still read, which whole-block locks of shared blocks make possible. It hasn't been observed, and the profiles can't show it.

**Fixes.**
- P1 removes it for RW -> RW.
- Keeping G through the host protects in `PhysicalHeap::Protect` would close both forms. That needs a TriggerCallbacks variant that hands the lock back (G before heap_mutex_ is legal, :1746-1748). The cost is holding G across 2 VirtualProtect calls.
- That change alters behaviour only when the race hits, so it is a correctness fix, not an output-identical one. Rate it separately.

### S4.8 P1's downside: write-watch faults (#27)

Task #27 item 3 (Agent 1, 05:58): if u is low, P1 turns today's one lock-time invalidation into write-watch faults. This section counts and prices them from the live SDK source and the 03:57 matrix logs. Nothing here was measured.

**Fault extent: which invalidation callbacks are registered.**

| Callback | Registered | What it returns on a fault (non-exact) |
|---|---|---|
| SharedMemory (`src/graphics/shared_memory.cpp:43`, body :502-575) | devoff | the 256 KB block, stopping at GPU-written pages (:531-551) |
| PrimitiveProcessor (`src/graphics/primitive_processor.cpp:1364`, body :1428-1562) | devoff | its 256 KB bucket (`kCacheBucketSizeBytes`, `primitive_processor.h:649-650`) if an entry was invalidated, else (0, UINT32_MAX), i.e. no constraint (:1559-1561) |
| rexlego gpu_native memory watch (`rexlego/src/gpu_native/memory_watch.cpp:115`) | native route only, lazily at the first `WatchCpuMemory` (:99-125) | exactly the notified range (`MemoryWritten`, :69-75: "Unprotect only the notified pages") |

- On a fault, `TriggerCallbacks` intersects the callbacks' returns (max of the firsts, min of the lasts; `xmemory.cpp:2346-2351`), adds the faulting page (:2355-2356) and caps the result at the aligned 4 MB (:2359-2362). It unprotects and unwatches only in the faulting view (`membase_ + heap_base_`, :2380-2427).
- **devoff:** the a and b logs (`build/agent8/matrix/20261122-0357/runs/0357-a-prof-r1/game.log`, `0401-b-prof-r1/game.log`, 90 lines each) have no "Native GPU init" and no "Native write tracking" line. The native n log has "Native write tracking: pixel textures=true buffers=true" at L44. So devoff registers only the first two callbacks, and **one fault invalidates and unwatches one 256 KB block (64 host pages) in one view.**
- **Native route:** rexlego's exact return shrinks the intersection to the faulting 4 KB page: one fault per written page, 64x as many. P1 must not run there. Condition 3 already ensures that: rexlego's callback gets no hook, and a callback without a hook forces the old path. So P1 is a no-op on the native route by design.

**Faults per frame.**
- After a fault the block stays unwatched until a draw re-uploads it and MakeRangeValid re-arms it. So a written block faults at most once per draw that reads it: about once per frame for each view the guest writes through.
- **Upper bound (u_block = 0, the guest writes every block it locks):** with V = locked bytes per frame and L = locks per frame, F_max ≈ V / 256 KB + L (S / 256 KB blocks per lock, +1 for a misaligned start).
- **Lower bound:** F_min = changed_blocks per frame from the u diagnostic (S4.9). A block rewritten with the same bytes still faults, so the truth lies between the two.

| L (locks/frame) | 256 KB locks | 1 MB locks | 4 MB locks |
|---|---|---|---|
| 5 | 10 faults, 0.08 ms/f | 25, 0.20 ms/f | 85, 0.68 ms/f |
| 10 | 20, 0.16 ms/f | 50, 0.40 ms/f | 170, 1.36 ms/f |
| 15 | 30, 0.24 ms/f | 75, 0.60 ms/f | 255, 2.04 ms/f |

(u_block = 0, S / 256 KB + 1 blocks per lock, 8 µs per fault.) L x S can't exceed what is invalidated today, which a-vol measures (S4.6 step 1). The estimates so far are 3-9 MB/f (Agent 5, at 1-3 GB/s in the slow state) and 15-30 MB/f (mine, at 5-10 GB/s). Examples: V = 3 MB/f, L = 5 -> ~17 faults, ~0.14 ms/f; V = 10 MB/f, L = 10 -> ~50, ~0.4 ms/f; V = 30 MB/f, L = 15 -> ~135, ~1.1 ms/f.

**Cost per fault, from the source path.**

| Step | Where | Estimate |
|---|---|---|
| CPU trap, KiUserExceptionDispatcher, VEH dispatch, and NtContinue on the way back | OS | 2-5 µs |
| the handler holds G (it waits if GPU Commands is inside EAC); HostToGuestVirtual, LookupHeap, IsDataProvided | `xmemory.cpp:541-578` | < 0.5 µs when G is free |
| TriggerCallbacks: watch scan; SharedMemory (valid bits, `FireWatchesLocked` on texture watches, counter); PrimitiveProcessor (`cache_mutex_`, bucket walk, map erases) | :2306-2352 | 0.5-2 µs |
| one VirtualProtect(RW) over ≤ 64 pages of the faulting view, under G | :2380-2414 | 1-5 µs, with any TLB-flush IPIs |
| clear the watch bits, return, retry the store | :2416-2427 | ~0 |

- **Low / central / high: 5 / 8 / 15 µs per fault.**
- G is held from the callbacks through the VirtualProtect, 2-7 µs per fault. Today's lock path holds G only for the exact TriggerCallbacks and drops it before its two VirtualProtect calls (S4.7).
- Faults are a new cost class, not a moved one: the VEH bucket has 1 / 0 samples (S4.1), and Agent 7's folds (`build/agent7/prof/{a,b}-{main,gpucmd}.folded`) have no KiUserExceptionDispatcher or AccessViolationCallback frames.

**Both sides, per thread.**

| Thread | P1 removes | P1 adds |
|---|---|---|
| Main (it locks the blocks and probably writes them) | MmSetAddressProtect: 0.54 / 1.02 ms/f (a / b), ~10-30 calls per frame. The fast path costs ~1-2 µs per call. | F x 5-15 µs. Break-even at 8 µs: F ≈ 68-128 faults/frame, i.e. V ≈ 15-30 MB/f of written locked blocks. |
| GPU Commands | u_block x the UploadRanges bucket (3.6-3.8 ms/f) | block widening: a fault invalidates its whole 256 KB block, so neighbours that the draws request, and that stay valid today, re-upload (same bytes) |
| G | the lock path's exact TriggerCallbacks holds | 2-7 µs per fault: 0.1-0.9 ms/f at F = 50-135 |

- **Widening, sized:** for locks of 1 MB or more the extra is at most the two edge blocks (≤ 50% at 1 MB, ≤ 12.5% at 4 MB). For locks of 64 KB or less it can be 4-64x the lock, if the draws read the neighbours in the same frame. From the diagnostic, P1 re-uploads between pages_in_changed_blocks and changed_blocks x 64 pages per frame.
- **Main is off the critical path:** it is busy ~3.6 ms/f and waits ~11.1 ms/f in a guest critical section (S4.1). Faults matter only if they land in a section Render waits for. The A/B and the per-frame fault counter show that.
- **The two ends:** at u_block = 1 nothing is written, so there are no faults, and P1 saves the full 3.6-3.8 ms/f on GPU Commands plus 0.5-1.0 ms/f on Main. At u_block = 0 GPU Commands saves nothing and pays the widening, and Main roughly breaks even up to V ≈ 15-30 MB/f. So P1's downside is bounded, and its upside scales with u.

**Decision rule.** Inputs: L and V from a-vol; u_block, changed_blocks (CB), pages_in_changed_blocks (PCB) and pages (P) per frame from the diagnostic.
- **No-go if u_block < 0.1.** P1 would save under 0.4 ms/f on GPU Commands and add faults. Take P2 and Agent 5's memcpy items instead.
- **Go to the A/B if all three hold:**
  - u_block ≥ 0.25;
  - the worst-case widening, (CB x 64 - PCB) x 3.7 ms/f / P, is under half of u_block x 3.7 ms/f;
  - F_max x 15 µs ≤ 2 ms/f.
- **Otherwise marginal:** build it behind the cvar and let the A/B decide.
- The diagnostic is optimistic for P1 (u_block is an upper bound and CB a lower bound). If P1 fails the rule on these numbers, it fails for real.
- Noted, not proposed: a smaller fault extent (say 64 KB) would cut the widening but give 4x the faults. It is worth a look only if widening dominates.

**For Agent 10 (P1's item 5).**
1. rexlego's callback has no hook, so P1 takes the old path whenever it is registered. Confirm that devoff never registers it (log check above) and registers no other callback.
2. Widening is output-identical. A widened invalidation re-uploads current guest bytes, and SharedMemory's widening stops at GPU-written pages (:531-551), so it never discards resolved data.
3. The fault path is today's code at a new rate (F per frame instead of ≈0), and G is held through the callbacks and the VirtualProtect (:2380-2414). The stale-protect recovery path (:584-638) must stay silent: P1 changes neither host protection nor watch bits.
4. The 5-15 µs is read from code. The P1 build's fault counter and one profile check it: KiUserExceptionDispatcher and AccessViolationCallback samples on Main should come to about F x cost.

### S4.9 The u diagnostic (#27 item 2): staged, not built

- **Files:** `build/agent12/s4-diag/`. Sent to Agent 10 for a rating at ~06:15; the rating is pending.
  - Base: the live `src/graphics/d3d12/shared_memory.cpp`, sha256 B120D07C6709D0D2A7836B532ED06B2032A418CBD4A71808CD318C7E6EB6CFBC (14514 B, LF, git clean at SDK 90e7ccd). Copy in `orig/`.
  - Patched copy: `new/shared_memory.cpp`, BB0838CE3909E18A63099B47B4E852CB9D2307EB2BF2535C3BC8FF38BFD64587 (20888 B).
  - Diff: `upload-hash-log.diff`, D290530197427138029FF34EE8B1BBBEDE26340AA85D0AE4EABB00DC0CEE9CEF (179 lines, 4 hunks). `git apply --check` passes on the live SDK.
  - Syntax: clang `-fsyntax-only` PASS. Pristine and candidate both exit 0 with the same 12 header diagnostics (`syntax-20261122-061249.txt`, from `bench/agent12/s4diag_syntax.ps1`).
  - `DESIGN.md` (cost, log format, how to read u, the Agent 10 checklist, the run plan) and `HASHES.txt`.
- **What it does:** a new cvar `shared_memory_upload_hash_log` (bool, default false, group GPU/D3D12). When it is on, UploadRanges runs its copy loop unchanged, then hashes every uploaded 4 KB page with XXH3-64 (from `<rex/hash.h>`, which pipeline_cache.cpp also uses). It compares each hash with the one from that page's previous upload, and logs once per frame (`GetCurrentFrame()`):
  `S4 upload hash: frame F calls C ranges R pages P (K KB) first N unchanged U changed X blocks B changed_blocks CB pages_in_changed_blocks PCB u_page f u_block f`
- **How to read u:**
  - u_page = U / (P - N): the share of re-uploaded pages whose bytes didn't change. It bounds a content skip (Agent 5's M2).
  - u_block: the share of uploaded pages in 256 KB blocks with no changed page that frame, i.e. what P1 could skip. It is an upper bound, because a write of the same bytes still faults under P1.
  - CB per frame is a lower bound on P1's faults (F_min in S4.8); B per frame is the upper bound.
  - Parser: `python bench/agent12/s4_uhash.py <game.log> [--json <out>]`. It gives pages-weighted u, faults per frame, P1's re-upload bounds and the fault ms/f at 5 / 8 / 15 µs. `--selftest` prints OK.
- **Cost:** with the cvar off, at most one cvar load and branch per UploadRanges call, and nothing is allocated. With it on, XXH3 over every uploaded byte (~0.2-3 ms/f on GPU Commands for 3-30 MB/f) plus 1 MiB of page hashes. Runs with it on are for counting, never for timing.
- **Run plan:** Agent 2 compiles it into the S4 build (cvar OFF). Then one functional devoff title-scene run through Agent 8's slot with `--shared_memory_upload_hash_log=true --slow_frame_log_ms=1` (~5 min). Its u_block and CB feed S4.8's decision rule before the P1 A/B.
