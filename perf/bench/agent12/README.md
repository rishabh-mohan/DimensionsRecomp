# bench/agent12: I/O, memory and logging replicas (Agent 12, task #11)

These are standalone differential tests and microbenchmarks for Agent 12's SDK changes §A-§D (designs: `perf-notes/agent12-session2-plan.md`).
- **OLD** is transcribed from pristine `git show HEAD:` SDK sources.
- **NEW** is transcribed from the working-tree edits.
- Nothing here links against the SDK. Every cvar is toggled explicitly (the SDK defaults are all false).

Results: [RESULTS.md](RESULTS.md). Progress and resume notes: [STATUS.md](STATUS.md).

## What each program replicates

| program | SDK change | what it does |
|---|---|---|
| `t1_scatter_test` | §B `XFile::ReadScatter` / `ReadScatterPositional` / `ReadData` / `CompleteRead` | Differential test, OLD vs NEW, on randomized scatter lists over mock guest memory. Compares status, out bytes, position, guest bytes, notifies and invalidated ranges. |
| `t2_watch_test` | §A `PhysicalHeap::MayHaveWriteWatches`, the atomic_ref watch-bit stores, the seq_cst fences | Checks that the lockless check equals the locked one, plus a store-buffering litmus test (with no-fence controls). |
| `b1_scatter` | §A + §B | Scatter-read throughput: virtual/physical heap × contiguous / 64 KB runs / stride-2, over synthetic data and, read-only, GAME.DAT. |
| `b2_watch` | §A | Latency of a locked TriggerCallbacks vs a lockless MayHaveWriteWatches, with and without a thread holding the global lock. |
| `b3_open` | §C `VirtualFileSystem::OpenFile` (vfs_defer_open_exists_check) | Cost of open+close with the eager `std::filesystem::exists` vs the deferred one, for both hits and misses. |
| `b4_samefile` | §B unlocked `XFile::Read` | 1 vs 2 threads reading through one XFile/handle. Variants: OLD, NEW, and OPT (overlapped handle, not SDK). |
| `b5_log` | §D logging level floor (log_level_gate) | ns per disabled / filtered / enabled log call, OLD vs NEW (NEW = v1', the SDK macro since 19:54). `ablate` compares macro variants: v0 is the superseded draft, v1 is the SDK macro from 19:27 to 19:54, v1' = NEW, and v2-v5 are bench-only. `only=` picks cases. |

Sources (`src/`):
- `xfile_replica.h`: OLD/NEW XFile.
- `mock_memory.h`: heaps, LookupHeap, page protection, watch bits, global_critical_region.
- `b5_log_shared.h` and `b5_log_registry.cpp`: the api.h/macros.h/logging.cpp parts.
- `common.h`: timing, stats, load sampling, synthetic files.

If the SDK files change, re-sync the replicas and re-run T1/T2:
- `src/system/xfile.cpp` → `xfile_replica.h`.
- `src/system/xmemory.cpp` → `mock_memory.h`.
- `src/filesystem/virtual_file_system.cpp` → `b3_open.cpp`.
- `include/rex/logging/{api,macros}.h` → `b5_log_shared.h`.

## Build

From the workspace root (PowerShell):

```
powershell -ExecutionPolicy Bypass -File bench/agent12/build.ps1 [t1_scatter_test t2_watch_test b1_scatter b2_watch b3_open b4_samefile b5_log]
```

- The build dot-sources `env/devshell.ps1` and compiles one target at a time with clang-cl `/O2 -march=x86-64-v2 /std:c++latest /EHsc /MD` and lld.
- Outputs:
  - executables: `build/agent12/bench/<target>.exe`;
  - objects: `build/agent12/bench/obj_<target>/`;
  - logs: `build/agent12/bench/logs/build_<target>.log`.

## Run

Run everything: `powershell -ExecutionPolicy Bypass -File bench/agent12/run_all.ps1`.
- That builds, then runs every program sequentially, with logs in `build/agent12/bench/logs/`.
- It is estimated at ~7-8 min of wall time on the loaded shared machine; it has not been run end to end yet. Ask the parent first, since it is well over 2 CPU-minutes.
- It never uses more than 2 threads.

Individual programs (defaults shown):

```
t1_scatter_test.exe [cases=6000] [seed=0x7E57AB1E]
t2_watch_test.exe   [equiv_iters=400000] [sb_iters=2000000]
b1_scatter.exe      [mb=256] [runs=5] [files=all|synthetic|game]
b2_watch.exe        [runs=5] [samples=100000]
b3_open.exe         [runs=5] [files=1000] [passes=3]
b4_samefile.exe     [runs=5] [mb_per_thread=128]
b5_log.exe          [runs=5] [disabled_calls=100000000] [ablate | only=<digits>]
                    # only= cases: 0 disabled trace, 1 disabled debug, 2 filtered, 3 enabled warn (e.g. only=02)
```

Invoke them as `cmd /c "exe args > out.md 2> out.err"`. A PowerShell `2>&1` wraps stderr in NativeCommandError records.

## Data

Everything lives under `build/agent12/bench-data/`, which is never under bench/:
- `scatter.bin`: 256 MB of synthetic xorshift data, used by B1 and B4. It is created on first use.
- `t1/`: synthetic T1 files.
- `open/`: 1000 temporary 4 KB files, created and deleted by B3.

`game/disc/GAME.DAT` is opened read-only, by B1 only (`files=all|game`).

> [!IMPORTANT]
> Never write game bytes, hashes or anything derived from game data into `bench/`. The programs print only timings, counters and pass/fail for game-file runs.
