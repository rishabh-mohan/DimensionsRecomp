# Agent 12 replica benches: STATUS

## RESUME (updated 2026-11-21 20:10)

### Done
- **Sources:** all in `bench/agent12/src/`. Build with `bench/agent12/build.ps1`, run with `bench/agent12/run_all.ps1`; docs in `README.md`.
- **Builds:** every target builds cleanly into `build/agent12/bench/`. `b5_log` was last rebuilt at 19:59 (v1' sync).
- **Re-sync:** NEW replicas are synced to the working tree:
  - §A+§B at 18:40, §C/§D at ~19:05.
  - The §D macro at 19:30, after the SDK macros.h change at 19:27 that dropped the outer `[[unlikely]]` (= ablation v1).
  - The §D macro again at 19:57, after the SDK change at 19:54 (= **v1'**). REX_LOG_IMPL is now `if (LogLevelMayBeEnabled) { p = GetLoggerRaw(cat); if (p && p->should_log) { BindLogLevelFloor(); p->log(...); } }`, and GetLoggerRawAndBindFloor is gone from api.h. The bench keeps a copy (`b12abl::GetLoggerRawAndBindFloorV1` in b5_log.cpp) for v0/v1/v5.
- **T1:** PASS (6000 and 30000 cases). **T2:** PASS.
- **Benches:** B1-B5 have run with n=5, and RESULTS.md holds every table.
- **B5 final (v1' macro, SDK since 19:54):**
  - Logs: `build/agent12/bench/logs/b5_v1p.md` (main table, 19:59-20:01, 100% load) and `b5_v1p_filtered2.md` (filtered confirmation, 20:03).
  - Gate off (the default; floor 0, so every disabled call is "filtered"): **at OLD parity**, 1.0x in all four measurements (e.g. 17.06→16.33 and 12.36→12.44 ns at 1 thread).
  - Gate on (floor=warn): disabled trace/debug calls are 4.2-5.1x cheaper (e.g. 10.34→2.26 ns).
  - Enabled calls: 0.8-1.2x, within the noise at 100% load.
- **B5 v1 (19:27-19:54) and v0 tables:** superseded, kept in RESULTS.md (logs `b5_final*.md`, `b5_run{1,2}.md`).
- **B5 ablation:** v0-v5 plus v1', four runs.
  - Logs: `b5_ablate{1,2}.md` (ablation build), `b5_ablate3.md` (v1 build) and `b5_ablate4.md` (v1' build, 20:01).
  - Codegen check: `build/agent12/bench/asm/b5_variant_codegen_v3.txt`, instructions per filtered loop: OLD 79, v1 95, v1' 92, v3 83. In v1', the category function is inlined, and the bound-flag refs appear only in the logged branch. Older files: `b5_variant_codegen.txt` and `_v2.txt`.
- **Messages to the parent:** T1/T2 (19:02), RESULTS (19:17), B5 diagnosis (19:20), ablation (19:26), B5 v1 table (19:47), summary (19:49), B5 v1' table + verdict (20:06), final summary (20:12).

### In progress
- Nothing is running; all deliverables are done. I'm waiting for the parent. Two optional items need its go-ahead first: (a) a lighter-load B5 v1' re-run after Agent 2's build; (b) run_all end to end.

### Constraints
- Quiet window 1 (20:15-20:45) was cancelled at 19:55. Agent 2's -j10 build starts at ~20:16, so don't run builds or benches around then unless the parent asks.
- Write only under `bench/agent12/**` (not `gcr/`) and `build/agent12/**` (not `obj/` or `gcr/`). At most 2 threads; compile one TU at a time.

### Exact next commands
- Re-sync check, if the SDK changes again:
  ```
  cmd /c "git -C DimensionsRecomp/rexglue-sdk diff -- include/rex/logging src/system/xfile.cpp src/system/xmemory.cpp src/filesystem/virtual_file_system.cpp"
  ```
- Rebuild and re-run B5 (~1 min build plus ~1.5 min per run, at 2 threads at most):
  ```
  powershell -ExecutionPolicy Bypass -File bench/agent12/build.ps1 b5_log
  cmd /c "build\agent12\bench\b5_log.exe 5 100000000 > build\agent12\bench\logs\b5_v1p2.md 2> build\agent12\bench\logs\b5_v1p2.err"
  cmd /c "build\agent12\bench\b5_log.exe 5 100000000 ablate > build\agent12\bench\logs\b5_ablate5.md 2> build\agent12\bench\logs\b5_ablate5.err"
  ```
- Everything:
  - `powershell -ExecutionPolicy Bypass -File bench/agent12/run_all.ps1 -Tag rerun`.
  - It has never been run. It needs more than 2 CPU-minutes, so ask the parent first.

# Historical: predecessor research checkpoint (2026-11-21 ~16:56; superseded, kept for reference)

## Done (as of 16:56)
- Research only. No bench sources had been written and nothing had been built yet. Everything since then is listed in the RESUME block above.

## SDK facts gathered (needed so the replicas match the real call sequence)
- `XFile::ReadScatter` (src/system/xfile.cpp:241): holds `file_lock_` (std::mutex) for the whole call;
  per 4 KB segment (big-endian guest ptr, `segments++` only while `read_remain > 4096`) calls
  `ReadInternal(..., notify_completion=false)`; at the end `NotifyIOCompletionPorts()` (locks
  `completion_port_lock_`, a std::mutex, every call, list normally empty) + `async_event_->Set()` (auto-reset).
- `XFile::ReadInternal` (xfile.cpp:139): 2x `Memory::LookupHeap` (out-of-line compare chain,
  xmemory.cpp) -> heap-type checks -> `BaseHeap::QueryRangeAccess` (xmemory.cpp:1908, out-of-line,
  locks `heap_mutex_` which is a **std::recursive_mutex**, not std::mutex, loops page_table_ current_protect)
  -> `file_->ReadSync` (vfs virtual -> `Win32FileHandle::Read` = ReadFile with OVERLAPPED.Pointer=offset,
  hEvent=NULL on the synchronous handle) -> `HasFileReadFixups()`/`ApplyFileReadFixups(name(), ...)`
  (function-local static `std::vector<std::function<void(const std::string&,uint64_t,uint8_t*,size_t)>>`;
  one fixup is registered by rexlego/src/mod_menu.cpp:104; `name()` returns const std::string&, no copy)
  -> `PhysicalHeap::TriggerCallbacks(global_critical_region::AcquireDirect(), ...)` (xmemory.cpp:2256;
  `AcquireDirect` = unique_lock on a static std::recursive_mutex; scans
  `system_page_flags_[i].notify_on_invalidation`, 64 system pages per uint64 word, returns false if 0)
  -> position_ update.
- `XFile::Read` (B4 OLD) = `lock_guard(file_lock_)` + `ReadInternal(notify=true)` (so per read also
  completion_port_lock_ + SetEvent, all under file_lock_).
- Logging: `REX_LOG_IMPL` = `GetLoggerRaw(cat)` (src/core/logging.cpp:359: `if(!g_initialized && !g_early_initialized) InitLoggingEarly();` bounds check `g_registry`, `.logger.get()`) then `should_log(lvl)`.
  `REX_LOG_NOISY_IMPL` calls `FLAGS_log_noisy_storage_()` first (REXCVAR_DEFINE_BOOL = out-of-line fn
  returning a ref to a constant-initialized static bool). Categories via `REXLOG_DEFINE_CATEGORY`
  (inline fn with `static const LogCategoryId id = RegisterLogCategory(#name)` -> thread-safe static,
  i.e. TLS epoch check per call on the MSVC ABI).
- spdlog 1.17.0 header-only (bundled fmt 12.1.0, FMT_VERSION 120100; thirdparty/fmt is also 12.1.0).
- VFS uses the throwing `std::filesystem::exists(path)` (virtual_file_system.cpp:242, host_path_device.cpp:36).
- SDK builds as C++23; MSVC STL 14.40.33807 -> `std::atomic_ref<const T>` probably unavailable; plan:
  CMake `check_cxx_source_compiles`, fallback `std::atomic_ref<uint64_t>(const_cast<...>)` (same codegen: plain mov).
- xxHash available at DimensionsRecomp/rexglue-sdk/thirdparty/xxHash/xxhash.h (use XXH_INLINE_ALL, XXH3 streaming) for the byte-equality check.
- Machine at 16:47: i7-1255U, 32 GB RAM (4.7 GB free), C: 23.7 GB free. game/disc/GAME.DAT = 425,590,241 bytes.

## Planned layout (not yet created)
```
bench/agent12/CMakeLists.txt     Release, CMAKE_CXX_FLAGS_RELEASE="-O2 -DNDEBUG", -march=x86-64-v2, C++23
bench/agent12/src/common.h       timing, median/min/max, p50/p99, GetSystemTimes load, xorshift64, data gen, SDK-flag CreateFileW
bench/agent12/src/memory_replica.{h,cpp}  LookupHeap, BaseHeap::QueryRangeAccess(recursive heap_mutex), global mutex(),
                                          TriggerCallbacks (locked scan), new TriggerCallbacksIfWatched (seq_cst fence + atomic_ref relaxed scan)
bench/agent12/src/xfile_replica.{h,cpp}   ReadScatterOld/New, ReadOld/New/Opt, fixups vector, completion lock, SetEvent; IoCounters
bench/agent12/src/bench_scatter.cpp  B1 (seq 64K/256K/1M, random 2000x64K, fragmented stride-2 pages; synthetic + GAME.DAT first 256 MB; warm pass, poisoned hash-verify pass, 7 interleaved timed runs)
bench/agent12/src/bench_watch.cpp    B2 (lfence+rdtsc per-check latency, paced 5 us; holder thread 50 us held / 150 us free; B1 old/new under contention)
bench/agent12/src/bench_open.cpp     B3 (1000 x 4 KB files in build/agent12/bench-data/open, hit + miss paths)
bench/agent12/src/bench_samefile.cpp B4 (1 vs 2 threads, OLD/NEW/OPT(FILE_FLAG_OVERLAPPED + per-thread manual-reset event))
bench/agent12/src/bench_log.cpp + log_registry.cpp  B5 (100M disabled TRACE, 10M enabled WARN->null_sink, noisy false/true)
bench/agent12/run_all.ps1, README.md, RESULTS.md
```
Data: build/agent12/bench-data/scatter.bin (256 MB xorshift64, fixed seed; reused by B4), open/ (1000 x 4 KB; delete at end).

## Exact commands to resume (once sources exist)
```powershell
cd <workspace>
. .\env\devshell.ps1
cmake -S bench\agent12 -B build\agent12\bench -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build\agent12\bench -j 4
# data is generated on first run by the exes (planned); then:
powershell -File bench\agent12\run_all.ps1   # records Get-Counter load before each bench, logs to build\agent12\bench\logs
```
Pending: everything above (write sources, build, generate data, run B1-B5, RESULTS.md, cleanup of open/ set).
