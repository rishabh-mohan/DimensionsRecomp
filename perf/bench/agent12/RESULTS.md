# Agent 12 (task #11) I/O, memory and logging: test and bench results

- Date: 2026-11-21, 19:00-20:03 local.
- Machine: Intel i7-1255U (2P+8E cores, 12 logical CPUs), Windows. **Shared by 12 agents.**
  - The 200 ms load samples were 40-100% (usually ~90-100%) during every run.
  - Absolute numbers are therefore noisy; compare OLD vs NEW only within a table.
- Build: clang-cl (LLVM 23) `/O2 -march=x86-64-v2 /std:c++latest /EHsc /MD`, lld, Release, no AVX. Built by `bench/agent12/build.ps1`.
- Sampling: every bench row is n=5 timed runs after one warm-up run, reported as median [min-max]. Benches use at most 2 threads.
- Code under test:
  - OLD is a transcription of pristine `git show HEAD:` SDK sources.
  - NEW is a transcription of the working-tree §A-§D edits (synced 18:40-19:10). The §D macro was re-synced at 19:30, after the 19:27 SDK change that dropped the outer `[[unlikely]]` (v1), and again at 19:57, after the 19:54 change that moved the bind behind `should_log` (v1', the final macro).
  - Every cvar is toggled explicitly in the replicas; the SDK defaults are all false.
- Game data: `game/disc/GAME.DAT` was only read, by B1. Only timings and pass/fail are reported for it.
- Logs: `build/agent12/bench/logs/` (`b1_run1.md` … `b4_run1.md`, `b5_v1p*.md` (final B5), `b5_final*.md` (superseded v1), `b5_ablate*.md`, `t1_*.txt`, `t2_default.txt`). `b5_run1.md` and `b5_run2.md` measured the superseded v0 macro.

## Headlines

| Item | Result |
|---|---|
| T1 scatter differential (§B) | **PASS**: 6000 cases (seed 0x7E57AB1E) and 30000 cases (seed 0xC0FFEE); 0 mismatches. |
| T2 watch-bit ordering (§A) | **PASS**: T2a 400k checks with 0 mismatches. T2b litmus test with 2M iterations and 0 forbidden outcomes (the controls do detect the bug). |
| B1 scatter coalescing (§B) | Contiguous and 64 KB-run scatter reads are **3.4-5.7x faster** (ReadFile calls per 1 MB drop from 256 to 1 or 16). Stride-2 is unchanged, within noise. |
| B2 lockless watch check (§A) | Uncontended p50 drops from 124 to 63 ns (4 KB range). While another thread holds the global lock 25% of the time: mean **8.9 us → 55 ns**, p99 **60 us → 0.18 us**. |
| B4 unlocked same-file reads (§B) | **No 2-thread scaling**: 64 KB, 2 threads: NEW 1711 vs OLD 1612 MB/s, within noise. The synchronous handle is serialized by the kernel; an overlapped handle (OPT) scales 1.44x. |
| B3 deferred exists on open (§C) | Opening an existing file: **184 → 92 us** (2.0x faster). Opening a missing file: **55 → 133 us** (2.4x slower). NEW comes out ahead overall while fewer than ~54% of eligible opens miss. |
| B5 logging level floor (§D) | Final SDK macro (19:54, which binds the floor only on logged lines): with the gate on, a disabled trace/debug call is **4.2-5.1x cheaper** on 1 and 2 threads (4.5-6.3x in lighter-load runs of the same floor test). With the gate off (**log_level_gate=false, the current default**, floor 0) or any category at trace, a disabled call is **at OLD parity**: 0.96-1.05x in two runs, and v1' ≈ v3 in the ablation. Earlier drafts cost more: +3-5 ns for v0, whose `[[unlikely]]` blocked inlining, and +1.1-2.1 ns for v1, which bound before should_log. Enabled calls are unchanged within noise (0.8-1.2x). |

## T1: scatter differential test (§B), PASS

- Source: `src/t1_scatter_test.cpp` with `src/xfile_replica.h` and `src/mock_memory.h`.
- Method:
  - Random scatter reads go through the OLD ReadScatter/ReadInternal (per-4 KB page) and the NEW ReadScatterPositional (coalesced runs plus per-page redo), each on its own handle to the same synthetic file.
  - The mock guest memory has a virtual heap, a physical heap with per-page protection and watch bits, an unmapped gap, adjacent heaps, and short reads/failures injected at the file end.
  - Each case compares: status, out bytes, `position_`, final guest bytes, notify count, and the union of invalidated ranges.
  - Allowed difference: on a short or failed run, NEW also invalidates the rest of that run before redoing it per page.
- 6000 cases, seed 0x7E57AB1E: PASS (1.08 s). Counter totals, OLD vs NEW:

  | Counter | OLD | NEW |
  |---|---:|---:|
  | ReadFile calls | 35727 | 25660 |
  | Global-lock acquisitions | 17637 | 5447 |
  | Callbacks fired | 4389 | 2535 |
  | Fixup calls | 33898 | 23509 |

  - NEW also did 8259 lockless pre-checks.
  - 852 cases took the redo path, giving 607 extra cleared watch bits (the allowed difference).
- 30000 cases, seed 0xC0FFEE: PASS. Log: `build/agent12/bench/logs/t1_30000_c0ffee.txt`.
- Informational findings, already reported:
  - A multi-byte fixup that straddles a page boundary inside one guest-contiguous run is applied by NEW (32/32 cases) but never by OLD (0/32). When the run is split, neither applies it (0/32).
  - Offset -2 reaches ReadFile unchanged in both versions, and Windows reads at the handle's file pointer. The Win32 probe confirmed this.
- Not covered: a destination buffer that overlaps its own segment array is excluded from the generator.

## T2: watch-bit ordering (§A), PASS

- Source: `src/t2_watch_test.cpp`. Log: `build/agent12/bench/logs/t2_default.txt`.
- T2a: `MayHaveWriteWatches` was compared with the locked reference over 400k random ranges plus a boundary sweep: 0 mismatches.
- T2b store-buffering litmus test, using the real fences: the EnableAccessCallbacks store plus its seq_cst fence, against the I/O-side fence plus the relaxed watch-bit load.
  - 2M iterations: **0 forbidden outcomes**.
  - Control with no fences: 47786 forbidden outcomes.
  - Control without the I/O-side fence: 17421 forbidden outcomes.

## B1: scatter reads, OLD vs NEW (§A, §B)

- Source: `src/b1_scatter.cpp`. Log: `build/agent12/bench/logs/b1_run1.md` (19:03, wall 148 s).
- Each run makes 255 ReadScatter calls of 1 MB, each at a different 1 MB file offset.
- Guest heaps:
  - HV: virtual, 16 MB at 0x01000000.
  - HP: physical, "e_like", 16 MB at 0x02000000.
  - HS: the segment arrays, at 0x03000000.
- Variants:
  - "phys OLD+A" is OLD with the §A lockless check.
  - "NEW (B, -A)" is §B with the lockless check disabled.
- Inputs:
  - "synthetic" is `build/agent12/bench-data/scatter.bin` (256 MB of xorshift data).
  - "GAME.DAT" is the real disc file, read only.
- An in-memory OLD/NEW byte-equality check passed on both files.
- MB/s, higher is better. The per-call counters are exact.

| file | pattern | variant | MB/s median | min | max | ReadFile/call | global-lock/call | heap-lock/call | load median [min-max] |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| synthetic | contiguous 1MB | virt OLD | 353 | 249 | 469 | 256 | 0 | 0 | 100% [36-100] |
| synthetic | contiguous 1MB | virt NEW (B) | 1183 | 1034 | 2152 | 1 | 0 | 0 | 100% [94-100] |
| synthetic | contiguous 1MB | phys OLD | 236 | 224 | 485 | 256 | 256 | 256 | 100% [81-100] |
| synthetic | contiguous 1MB | phys OLD+A | 335 | 176 | 451 | 256 | 0 | 256 | 100% [82-100] |
| synthetic | contiguous 1MB | phys NEW (B, -A) | 1592 | 851 | 2027 | 1 | 1 | 1 | 100% [89-100] |
| synthetic | contiguous 1MB | phys NEW (A+B) | 1241 | 1119 | 2195 | 1 | 0 | 1 | 100% [76-100] |
| synthetic | 16x64KB runs | virt OLD | 319 | 230 | 547 | 256 | 0 | 0 | 100% [72-100] |
| synthetic | 16x64KB runs | virt NEW (B) | 1308 | 753 | 1804 | 16 | 0 | 0 | 100% [83-100] |
| synthetic | 16x64KB runs | phys OLD | 355 | 239 | 477 | 256 | 256 | 256 | 100% [67-100] |
| synthetic | 16x64KB runs | phys OLD+A | 375 | 251 | 432 | 256 | 0 | 256 | 100% [75-100] |
| synthetic | 16x64KB runs | phys NEW (B, -A) | 1368 | 1115 | 1443 | 16 | 16 | 16 | 100% [64-100] |
| synthetic | 16x64KB runs | phys NEW (A+B) | 1392 | 1024 | 1741 | 16 | 0 | 16 | 92% [67-100] |
| synthetic | stride-2 pages | virt OLD | 416 | 190 | 514 | 256 | 0 | 0 | 100% [89-100] |
| synthetic | stride-2 pages | virt NEW (B) | 408 | 164 | 504 | 256 | 0 | 0 | 100% [62-100] |
| synthetic | stride-2 pages | phys OLD | 378 | 220 | 515 | 256 | 256 | 256 | 100% [79-100] |
| synthetic | stride-2 pages | phys OLD+A | 359 | 231 | 488 | 256 | 0 | 256 | 100% [69-100] |
| synthetic | stride-2 pages | phys NEW (B, -A) | 367 | 166 | 513 | 256 | 256 | 256 | 100% [67-100] |
| synthetic | stride-2 pages | phys NEW (A+B) | 345 | 154 | 542 | 256 | 0 | 256 | 94% [56-100] |
| GAME.DAT | contiguous 1MB | virt OLD | 381 | 237 | 517 | 256 | 0 | 0 | 100% [56-100] |
| GAME.DAT | contiguous 1MB | virt NEW (B) | 1600 | 823 | 2151 | 1 | 0 | 0 | 100% [62-100] |
| GAME.DAT | contiguous 1MB | phys OLD | 406 | 182 | 515 | 256 | 256 | 256 | 100% [62-100] |
| GAME.DAT | contiguous 1MB | phys OLD+A | 344 | 236 | 503 | 256 | 0 | 256 | 96% [67-100] |
| GAME.DAT | contiguous 1MB | phys NEW (B, -A) | 2148 | 1176 | 2470 | 1 | 1 | 1 | 92% [62-100] |
| GAME.DAT | contiguous 1MB | phys NEW (A+B) | 2308 | 700 | 2408 | 1 | 0 | 1 | 88% [62-100] |
| GAME.DAT | 16x64KB runs | virt OLD | 438 | 237 | 588 | 256 | 0 | 0 | 94% [50-100] |
| GAME.DAT | 16x64KB runs | virt NEW (B) | 1076 | 905 | 2284 | 16 | 0 | 0 | 100% [50-100] |
| GAME.DAT | 16x64KB runs | phys OLD | 382 | 185 | 611 | 256 | 256 | 256 | 100% [61-100] |
| GAME.DAT | 16x64KB runs | phys OLD+A | 523 | 189 | 657 | 256 | 0 | 256 | 69% [47-100] |
| GAME.DAT | 16x64KB runs | phys NEW (B, -A) | 2123 | 802 | 2749 | 16 | 16 | 16 | 79% [38-100] |
| GAME.DAT | 16x64KB runs | phys NEW (A+B) | 2005 | 514 | 2266 | 16 | 0 | 16 | 70% [38-100] |
| GAME.DAT | stride-2 pages | virt OLD | 441 | 149 | 673 | 256 | 0 | 0 | 100% [33-100] |
| GAME.DAT | stride-2 pages | virt NEW (B) | 542 | 170 | 629 | 256 | 0 | 0 | 88% [33-100] |
| GAME.DAT | stride-2 pages | phys OLD | 514 | 167 | 564 | 256 | 256 | 256 | 97% [52-100] |
| GAME.DAT | stride-2 pages | phys OLD+A | 493 | 162 | 540 | 256 | 0 | 256 | 67% [56-100] |
| GAME.DAT | stride-2 pages | phys NEW (B, -A) | 506 | 136 | 528 | 256 | 256 | 256 | 79% [61-100] |
| GAME.DAT | stride-2 pages | phys NEW (A+B) | 480 | 163 | 584 | 256 | 0 | 256 | 69% [58-100] |

Reading the table:
- §B coalescing, NEW(A+B) vs OLD on the physical heap:
  - contiguous: 5.3x (synthetic), 5.7x (GAME.DAT);
  - 16x64KB runs: 3.9x, 5.2x;
  - stride-2: 0.91x, 0.93x, inside the min-max overlap, so no change.
- On the virtual heap the same ratios are 3.4x, 4.2x, 4.1x, 2.5x, and ~1.0x for stride-2.
- §A takes the global lock out of the physical-heap read path entirely (global-lock/call goes to 0).
  - Its single-thread throughput effect is lost in the noise: OLD+A vs OLD is 0.85x-1.42x.
  - Its benefit is latency under contention; see B2.

## B2: watch-check latency, locked TriggerCallbacks vs lockless MayHaveWriteWatches (§A)

- Source: `src/b2_watch.cpp`. Log: `build/agent12/bench/logs/b2_run1.md` (19:11).
- Setup:
  - The heap is a 64 MB "e_like" physical heap with no watched page in the range (the common case).
  - OLD takes the global recursive mutex and then scans.
  - NEW does the lockless `MayHaveWriteWatches` scan.
- Timing method:
  - Each call is timed by rdtsc (lfence-serialized), calibrated at 2.611 ticks/ns, with the 42.9 ns measurement overhead subtracted.
  - Calls are paced ~5 us apart.
  - "25% held" means a second thread owns the global mutex for 50 us of every 200 us.
- Each run takes 100000 samples. The table shows the median over 5 runs of each statistic.
- The max column is dominated by preemption on the 100%-loaded machine (milliseconds, for both OLD and NEW), so ignore it.

| check | range | holder | mean ns median [min-max] | p50 ns | p99 ns median [min-max] | max ns (worst run) | load |
|---|---:|---|---|---:|---|---:|---:|
| locked TriggerCallbacks (OLD) | 4 KB | none | 231.7 [214.6-474.6] | 124.1 | 494.0 [483.3-599.0] | 29072548 | 100% |
| lockless MayHaveWriteWatches (NEW) | 4 KB | none | 124.0 [84.3-559.6] | 62.8 | 287.2 [251.2-340.1] | 43143432 | 100% |
| locked TriggerCallbacks (OLD) | 1024 KB | none | 144.2 [92.6-366.5] | 98.8 | 411.3 [374.5-445.0] | 22209051 | 100% |
| lockless MayHaveWriteWatches (NEW) | 1024 KB | none | 77.2 [69.5-311.5] | 52.8 | 222.9 [206.8-226.7] | 19708698 | 100% |
| locked TriggerCallbacks (OLD) | 4 KB | 25% held | 8877.2 [7868.8-11719.4] | 50.6 | 59927.9 [59626.1-60395.1] | 101078386 | 100% |
| lockless MayHaveWriteWatches (NEW) | 4 KB | 25% held | 54.6 [38.9-424.3] | 35.2 | 182.3 [163.9-193.8] | 38533588 | 100% |
| locked TriggerCallbacks (OLD) | 1024 KB | 25% held | 9079.9 [8279.5-12549.6] | 75.1 | 62028.8 [60021.3-63165.5] | 60508097 | 100% |
| lockless MayHaveWriteWatches (NEW) | 1024 KB | 25% held | 91.2 [66.8-132.6] | 62.0 | 216.0 [203.0-257.4] | 5033449 | 100% |

Reading the table:
- Uncontended, NEW roughly halves the per-check cost (p50 124 → 63 ns at 4 KB, 99 → 53 ns at 1 MB).
- With a lock holder, OLD calls that land inside a hold wait up to 50 us (p99 ≈ 60 us, mean ≈ 9 us). NEW never waits (p99 ≈ 0.2 us).
- The row order is fixed, so the first row includes some residual warm-up. That is why OLD at 4 KB shows a higher mean than OLD at 1 MB.

## B4: same-handle reads from 1 vs 2 threads (§B unlocked Read)

- Source: `src/b4_samefile.cpp`. Log: `build/agent12/bench/logs/b4_run1.md` (19:06).
- Setup:
  - Both threads share one XFile replica and one host handle on the synthetic `scatter.bin` (256 MB).
  - Each thread reads its own blocks into its own guest buffer.
- Variants:
  - OLD: the whole ReadFile runs under `file_lock_`.
  - NEW: the fast path, with a shared `unlocked_read_lock_` held around ReadData and `file_lock_` held only for CompleteRead.
  - OPT: NEW on a handle opened with FILE_FLAG_OVERLAPPED, with an explicit OVERLAPPED offset per read. This variant is **not** in the SDK.
- MB/s, higher is better.

| block | threads | variant | MB/s median | min | max | load median [min-max] |
|---:|---:|---|---:|---:|---:|---|
| 64 KB | 1 | OLD (locked ReadFile) | 1991 | 1238 | 2816 | 81% [29-86] |
| 64 KB | 2 | OLD (locked ReadFile) | 1612 | 1471 | 2145 | 79% [61-100] |
| 64 KB | 1 | NEW (unlocked ReadFile) | 1688 | 1202 | 2133 | 92% [75-100] |
| 64 KB | 2 | NEW (unlocked ReadFile) | 1711 | 1617 | 1984 | 67% [58-100] |
| 64 KB | 1 | OPT (NEW + overlapped handle) | 1784 | 1378 | 2003 | 75% [52-100] |
| 64 KB | 2 | OPT (NEW + overlapped handle) | 2567 | 2102 | 2760 | 88% [50-100] |
| 4 KB | 1 | OLD (locked ReadFile) | 293 | 221 | 357 | 72% [61-100] |
| 4 KB | 2 | OLD (locked ReadFile) | 257 | 229 | 293 | 86% [56-100] |
| 4 KB | 1 | NEW (unlocked ReadFile) | 239 | 230 | 365 | 83% [54-100] |
| 4 KB | 2 | NEW (unlocked ReadFile) | 220 | 189 | 252 | 100% [50-100] |
| 4 KB | 1 | OPT (NEW + overlapped handle) | 193 | 159 | 246 | 100% [58-100] |
| 4 KB | 2 | OPT (NEW + overlapped handle) | 278 | 180 | 341 | 81% [75-100] |

Reading the table:
- With two threads, NEW is no faster than OLD (64 KB: 1711 vs 1612; 4 KB: 220 vs 257), all within noise.
- The likely cause:
  - The SDK opens host files without FILE_FLAG_OVERLAPPED, so the I/O manager serializes every I/O on that file object (the FO_SYNCHRONOUS_IO file-object lock).
  - Removing `file_lock_` therefore cannot make reads on the same handle run in parallel.
- Only the overlapped handle scaled: 1.44x at 64 KB, and 1.44x at 4 KB (from a lower 1-thread baseline).
- §B's unlocked path can still help when the reader would otherwise wait on `file_lock_` behind non-read work. That case is not measured here.
- To get real same-file parallelism, the SDK would need an overlapped (or per-thread) handle. That is outside the current §B change.

## B3: open of existing / missing files, eager exists() vs deferred (§C)

- Source: `src/b3_open.cpp`. Log: `build/agent12/bench/logs/b3_run1.md` (19:14, wall 21 s).
- Setup:
  - 1000 small files (4 KB each) are created in `build/agent12/bench-data/open` and deleted at the end (deletion confirmed).
  - Every open uses the SDK's CreateFileW flags, followed by CloseHandle.
- Variants:
  - hit OLD: `std::filesystem::exists(dir/name)`, then CreateFileW.
  - hit NEW (§C, kOpen with no write access): CreateFileW only.
  - miss OLD: exists() fails and the open returns NO_SUCH_FILE without calling CreateFileW.
  - miss NEW: CreateFileW fails, then exists() runs, then NO_SUCH_FILE.
  - The in-memory entry create/Delete in the VFS is not included.
- Each run is 3 passes over the 1000 files, so the metadata is warm in the OS cache.
- Cost per open in us, lower is better:

| variant | us/open median | min | max | opened | load median [min-max] |
|---|---:|---:|---:|---:|---|
| hit: exists + CreateFileW (OLD) | 184.24 | 145.80 | 215.65 | 1000/1000 | 100% [92-100] |
| hit: CreateFileW only (NEW) | 91.95 | 79.27 | 97.47 | 1000/1000 | 100% [61-100] |
| miss: exists only (OLD) | 54.98 | 48.68 | 85.09 | 0/1000 | 100% [61-100] |
| miss: CreateFileW fails + exists (NEW) | 132.91 | 121.34 | 139.48 | 0/1000 | 100% [42-100] |

Reading the table:
- On a hit, NEW saves one metadata query (−92 us, 2.0x faster).
- On a miss, NEW adds one failed CreateFileW (+78 us, 2.4x slower).
- Break-even: NEW wins while fewer than 92/(92+78) ≈ **54%** of eligible kOpen opens miss.
- The absolute costs are inflated by the 100% load and probably by antivirus filter drivers, so per-call times on an idle machine will be lower. The structure (one fewer query per hit, one more per miss) still holds.

## B5: log-call cost (§D)

- Sources: `src/b5_log.cpp`, `src/b5_log_shared.h` and `src/b5_log_registry.cpp`.
- Logs in `build/agent12/bench/logs/`:
  - Final v1' macro (build ~20:00): `b5_v1p.md` and `b5_ablate4.md`.
  - Superseded v1 macro (build 19:38): `b5_final.md` (19:38), `b5_final_rerun.md` (19:42; disabled trace and filtered only) and `b5_final2.md` (19:44).
  - Superseded v0 runs: `b5_run1.md` (19:14) and `b5_run2.md` (19:26).
- OLD: the pristine macro, i.e. `GetLoggerRaw(cat())` then `should_log`.
- NEW: the working-tree §D macro with the gate on (macros.h of 19:54, ablation variant v1'):
  - `LogLevelMayBeEnabled` (two dependent relaxed loads plus a compare), with no `[[unlikely]]`.
  - Only above the floor: `GetLoggerRaw(cat())` then `should_log`, exactly as in OLD.
  - `BindLogLevelFloor()` (the bound-flag check) runs only for a line that passes `should_log` and is logged.
  - The replica is a verbatim transcription of the working-tree api.h/macros.h, re-synced at 19:57.
  - The bench is a single module, and its registry updates the module's own floor. Binding therefore does not change which floor the macro reads, and the disabled rows hold whether or not the module is bound.
  - In the SDK, a module that has not yet logged an enabled line reads its own floor (0), so its disabled calls cost what the filtered rows show.
- Modelling:
  - GetLoggerRaw and the shared-floor getter are `noinline` in a separate TU and are called through `const` function pointers, to model the DLL import.
  - The loggers write to `spdlog::null_sink_mt`.
  - The category functions use the real `REXLOG_DEFINE_CATEGORY` pattern (a function-local static).
- Cases:
  - "disabled": every level is warn, so the floor is warn; the bench logs trace or debug.
  - "filtered by logger": one other category is set to trace, which drops the floor to trace. The measured category stays at warn, so the call passes the floor check and is then rejected by `should_log`.
  - "enabled": a warn call with 2 format args, into the null sink.
- OLD and NEW are interleaved within each run. With 2 threads, both threads log to the same categories.

### B5 final: SDK macro since 19:54 (v1', bind only on logged lines)

`b5_v1p.md`, 19:59-20:01. The load was 100% throughout, so the absolute numbers are ~2-4x higher than in the 19:44 run; compare only within a row. Cost per call in ns, lower is better:

| case | threads | calls/thread | OLD ns/call median [min-max] | NEW ns/call median [min-max] | OLD/NEW | load median |
|---|---:|---:|---|---|---:|---:|
| disabled trace (level=warn) | 1 | 100000000 | 10.34 [8.81-11.63] | 2.26 [1.50-2.44] | 4.6x | 100% |
| disabled trace (level=warn) | 2 | 100000000 | 11.02 [10.28-12.30] | 2.54 [2.34-2.78] | 4.3x | 100% |
| disabled debug (level=warn) | 1 | 100000000 | 12.37 [10.55-13.54] | 2.44 [2.32-2.67] | 5.1x | 100% |
| disabled debug (level=warn) | 2 | 100000000 | 15.78 [10.85-17.15] | 3.72 [2.29-4.52] | 4.2x | 100% |
| trace filtered by logger (floor=trace) | 1 | 50000000 | 17.06 [14.66-18.15] | 16.33 [13.74-22.86] | 1.0x | 100% |
| trace filtered by logger (floor=trace) | 2 | 50000000 | 14.31 [10.98-19.84] | 14.83 [12.80-20.65] | 1.0x | 100% |
| enabled warn -> null_sink_mt | 1 | 2000000 | 763.79 [503.73-938.69] | 663.19 [643.16-785.52] | 1.2x | 100% |
| enabled warn -> null_sink_mt | 2 | 2000000 | 576.39 [535.20-891.34] | 702.26 [484.15-963.96] | 0.8x | 100% |

Confirmation run, filtered only: `b5_v1p_filtered2.md`, 20:03, load 100%.

| case | threads | OLD | NEW | OLD/NEW |
|---|---:|---|---|---:|
| trace filtered by logger (floor=trace) | 1 | 12.36 [10.51-14.60] | 12.44 [11.01-13.57] | 1.0x |
| trace filtered by logger (floor=trace) | 2 | 11.29 [10.68-13.36] | 11.88 [11.79-13.37] | 1.0x |

- Ablation run 4 (`b5_ablate4.md`, 20:01, 100% load; table below), filtered at floor 0: OLD 12.27, v1 15.20, **v1' 13.83**, v3 13.50 ns.
- Codegen (`build/agent12/bench/asm/b5_variant_codegen_v3.txt`, instructions per filtered loop): OLD 79, v1 95, v1' 92, v3 83.
  - v1' inlines the category function.
  - Its bound-flag references sit inside the logged branch, so the filtered path does not execute them.

**Verdict (final):**
- The filtered case (gate off, the default) **is at OLD parity within noise**: NEW/OLD is 0.96-1.05x on 1 and 2 threads in both runs, and the ranges overlap. In the ablation, v1' ≈ v3.
- With the gate on, disabled calls are **4.2-5.1x cheaper** in this run. The lighter-load v1 runs measured 4.5-6.3x; the disabled path is the same floor test in v1 and v1'.
- Enabled calls are 0.8-1.2x, i.e. noise. The bind check now runs on these calls: one load and a predicted branch per logged line, next to ~500-700 ns of formatting.

### B5 superseded: v1 macro (SDK 19:27-19:54, bind before `should_log`)

`b5_final2.md`, 19:44, load 40-100%: the lightest of the three v1 runs. Cost per call in ns, lower is better:

| case | threads | calls/thread | OLD ns/call median [min-max] | NEW ns/call median [min-max] | OLD/NEW | load median |
|---|---:|---:|---|---|---:|---:|
| disabled trace (level=warn) | 1 | 100000000 | 2.72 [2.57-2.84] | 0.47 [0.40-0.55] | 5.8x | 40% |
| disabled trace (level=warn) | 2 | 100000000 | 3.61 [3.13-3.69] | 0.76 [0.57-0.80] | 4.8x | 42% |
| disabled debug (level=warn) | 1 | 100000000 | 3.64 [3.37-3.90] | 0.66 [0.59-0.78] | 5.5x | 62% |
| disabled debug (level=warn) | 2 | 100000000 | 4.31 [3.63-4.94] | 0.96 [0.70-1.00] | 4.5x | 47% |
| trace filtered by logger (floor=trace) | 1 | 50000000 | 5.58 [5.01-5.69] | 7.39 [5.86-7.73] | 0.8x | 64% |
| trace filtered by logger (floor=trace) | 2 | 50000000 | 9.80 [6.27-10.70] | 11.93 [8.32-15.15] | 0.8x | 86% |
| enabled warn -> null_sink_mt | 1 | 2000000 | 560.98 [510.53-606.02] | 524.78 [439.90-664.29] | 1.1x | 100% |
| enabled warn -> null_sink_mt | 2 | 2000000 | 533.15 [404.45-599.66] | 554.31 [357.02-606.65] | 1.0x | 96% |

All three v1 runs, OLD → NEW (v1) in ns/call (OLD/NEW):

| run | load | disabled trace, 1 thr | disabled trace, 2 thr | filtered (floor 0), 1 thr | filtered (floor 0), 2 thr |
|---|---|---|---|---|---|
| `b5_final.md`, 19:38 | 100% | 17.47 → 3.07 (5.7x) | 19.75 → 3.31 (6.0x) | 19.43 → 26.37 (0.7x) | 25.97 → 31.45 (0.8x) |
| `b5_final_rerun.md`, 19:42 | 75-100% | 5.36 → 1.07 (5.0x) | 5.43 → 1.09 (5.0x) | 4.77 → 5.87 (0.8x) | 4.70 → 6.02 (0.8x) |
| `b5_final2.md`, 19:44 | 40-86% | 2.72 → 0.47 (5.8x) | 3.61 → 0.76 (4.8x) | 5.58 → 7.39 (0.8x) | 9.80 → 11.93 (0.8x) |

- `b5_final.md` ran at 100% load throughout, so all its absolute numbers are ~3-4x inflated. Its ratios match the other two runs. Its disabled-debug and enabled rows are 6.3x / 4.8x and 1.0x / 0.9x (1 / 2 threads).
- The OLD-disabled outlier of ablation runs 1-2 (see below) did not recur.
  - In the v1 runs, OLD disabled is 0.5-1.1x OLD filtered, never 2-3x as it was there.
  - The two loops are byte-identical, so the spread is load drift from phase to phase.
  - The 17-20 ns in `b5_final.md` came from the whole run being inflated by load.

**Verdict (v1, superseded):**
- With the gate on, a disabled call is **4.5-6.3x cheaper** (OLD 2.7-5.4 → NEW 0.5-1.1 ns at moderate load).
- With the gate off (the default, floor 0), the v1 macro still costs **+1.1-2.1 ns per disabled call** (+21-36%; 0.7-0.8x in all three runs). This is down from +3-5 ns (+67-76%) with the v0 draft. The ablation attributes the remainder to the bound-flag check in GetLoggerRawAndBindFloor.
- Enabled calls are unchanged (0.9-1.1x).

### B5 superseded: v0 draft macro (outer `[[unlikely]]`, SDK until 19:27)

The two tables below measured the v0 draft. They are kept for the record; the final numbers are above.

First sample: `build/agent12/bench/logs/b5_run1.md`, 19:14, wall 41 s. Cost per call in ns, lower is better:

| case | threads | calls/thread | OLD ns/call median [min-max] | NEW ns/call median [min-max] | OLD/NEW | load median |
|---|---:|---:|---|---|---:|---:|
| disabled trace (level=warn) | 1 | 100000000 | 5.61 [4.69-6.40] | 1.20 [0.98-1.40] | 4.7x | 97% |
| disabled trace (level=warn) | 2 | 100000000 | 5.92 [5.66-6.37] | 1.23 [1.21-1.34] | 4.8x | 71% |
| disabled debug (level=warn) | 1 | 100000000 | 4.87 [4.68-5.46] | 1.04 [0.92-1.15] | 4.7x | 54% |
| disabled debug (level=warn) | 2 | 100000000 | 5.82 [5.33-6.15] | 1.27 [1.19-1.32] | 4.6x | 33% |
| trace filtered by logger (floor=trace) | 1 | 50000000 | 6.91 [5.43-8.38] | 12.16 [11.52-13.85] | 0.6x | 67% |
| trace filtered by logger (floor=trace) | 2 | 50000000 | 8.10 [7.16-8.59] | 13.52 [12.69-15.97] | 0.6x | 67% |
| enabled warn -> null_sink_mt | 1 | 2000000 | 311.67 [283.11-359.96] | 315.72 [300.93-450.90] | 1.0x | 72% |
| enabled warn -> null_sink_mt | 2 | 2000000 | 353.57 [290.70-426.99] | 372.18 [277.68-499.21] | 0.9x | 75% |

Second sample: `build/agent12/bench/logs/b5_run2.md`, 19:26, lighter load ~50-70%. This is the same OLD and v0 code, rebuilt with the ablation variants.

| case | threads | calls/thread | OLD ns/call median [min-max] | NEW ns/call median [min-max] | OLD/NEW | load median |
|---|---:|---:|---|---|---:|---:|
| disabled trace (level=warn) | 1 | 100000000 | 3.26 [2.89-3.45] | 0.61 [0.56-0.73] | 5.4x | 62% |
| disabled trace (level=warn) | 2 | 100000000 | 4.68 [3.76-5.78] | 0.96 [0.80-1.01] | 4.9x | 72% |
| disabled debug (level=warn) | 1 | 100000000 | 4.10 [3.77-4.32] | 0.89 [0.72-0.95] | 4.6x | 53% |
| disabled debug (level=warn) | 2 | 100000000 | 4.05 [3.97-4.47] | 0.90 [0.85-1.01] | 4.5x | 46% |
| trace filtered by logger (floor=trace) | 1 | 50000000 | 4.26 [4.02-5.16] | 7.36 [6.61-8.69] | 0.6x | 64% |
| trace filtered by logger (floor=trace) | 2 | 50000000 | 4.90 [4.81-5.84] | 8.55 [8.28-9.15] | 0.6x | 50% |
| enabled warn -> null_sink_mt | 1 | 2000000 | 223.53 [189.32-234.44] | 207.50 [181.83-224.49] | 1.1x | 83% |
| enabled warn -> null_sink_mt | 2 | 2000000 | 290.67 [199.07-304.95] | 278.17 [257.75-282.96] | 1.0x | 100% |

Both v0 samples agree on the ratios: 4.5-5.4x on the disabled path, 0.6x on the filtered path, and ~1.0x for enabled calls. Absolute numbers move with the machine load.

Reading the v0 tables:
- With the gate on and no category below the floor, a disabled call drops from ~3-6 ns to ~0.6-1.3 ns. It scales perfectly to 2 threads, since nothing shared is written. The final build confirms this.
- When the floor is lowered, every trace/debug call that passes the floor but is filtered by its own logger cost **+3-5 ns** with v0. The ranges did not overlap in any sample: 12.2 vs 6.9 ns (run 1), 7.4 vs 4.3 (run 2), 10.3-11.4 vs 6.3-7.8 (ablation). The v1 macro cut this to +1.1-2.1 ns, and the final v1' macro to parity. The floor is lowered when:
  - any category is at trace or debug, **or**
  - `log_level_gate=false`, which is the current default: the floor then stays 0, so **every** disabled call takes this path.
- Cause, from the disassembly: under `[[unlikely]]`, clang treats the block as a cold call site and does not inline the category function. The call becomes an out-of-line call that returns LogCategoryId through a hidden pointer, since it has a user-provided constructor (MSVC ABI). OLD and v1 inline it. See the ablation below.
- Enabled calls are dominated by formatting and the sink: no difference.

### B5 ablation: which part of the macro costs what

- Logs:
  - `build/agent12/bench/logs/b5_ablate1.md` and `b5_ablate2.md` (19:22 and 19:24, ablation build).
  - `b5_ablate3.md` (19:43, v1 build; its v1 is compiled from the re-synced 19:27 SDK macro).
  - `b5_ablate4.md` (20:01, v1' build; adds the v1' column).
- Codegen check: `build/agent12/bench/asm/b5_variant_codegen.txt`, `b5_variant_codegen_v2.txt` (v1 build) and `b5_variant_codegen_v3.txt` (v1' build). All are llvm-objdump of `b5_log.obj`. v2 counts the category-function calls and bound-flag references in each loop; v3 also counts instructions per loop.
- Variants:
  - v0 is the superseded SDK draft: an outer `[[unlikely]]` plus the bind. It was the SDK macro until 19:27.
  - v1 drops the outer `[[unlikely]]`. It was the SDK macro from 19:27 to 19:54.
  - v1' is v1 with the bind moved behind `should_log`, so it runs only for logged lines. **This is the SDK macro since 19:54.**
  - The other variants are bench-only, not SDK code:
    - v2 keeps `[[unlikely]]` but calls GetLoggerRaw directly, so there is no bound-flag load.
    - v3 is v1+v2.
    - v4 is v3 with a one-load floor: a per-module constinit `atomic<int>` compared directly, with no pointer.
    - v4h is v2 with the one-load floor.
    - v5 is v0 with the category function `__forceinline`.
- Setup:
  - 1 thread, variants interleaved in rotating order, n=5 per run.
  - Four independent runs: runs 1-2 at load 88-100%, run 3 at 42-64%, run 4 (v1' build) at 100%.

| case | OLD | v0 (SDK until 19:27) | v1 (SDK 19:27-19:54) | v1' (SDK since 19:54) | v2 | v3 | v4 | v4h | v5 |
|---|---|---|---|---|---|---|---|---|---|
| filtered, floor 0 (= gate-off default), run 1 | 7.67 | 10.27 | 7.30 | – | 10.03 | 6.28 | 6.47 | 9.60 | 8.31 |
| filtered, floor 0 (= gate-off default), run 2 | 6.34 | 11.01 | 7.69 | – | 11.43 | 6.44 | 6.36 | 9.94 | 8.35 |
| filtered, floor 0 (= gate-off default), run 3 | 7.81 | 11.39 | 8.64 | – | 11.16 | 7.32 | 7.51 | 13.41 | 8.86 |
| filtered, floor 0 (= gate-off default), run 4 (100% load) | 12.27 | 21.96 | 15.20 | **13.83** | 27.10 | 13.50 | 15.19 | 20.47 | 16.95 |
| disabled, floor warn, run 1 | (17.56)* | 2.30 | 2.26 | – | 2.15 | 2.58 | 2.15 | 2.19 | 2.27 |
| disabled, floor warn, run 2 | (14.18)* | 2.80 | 3.06 | – | 2.61 | 2.77 | 2.55 | 2.51 | 3.45 |
| disabled, floor warn, run 3 | 4.96 | 1.06 | 1.08 | – | 0.98 | 0.72 | 0.76 | 0.80 | 0.92 |
| disabled, floor warn, run 4 (100% load) | 15.50 | 3.78 | 4.19 | 3.93 | 3.39 | 2.43 | 2.39 | 2.51 | 3.47 |
| category function inlined? | yes | **no** | yes | yes | **no** | yes | yes | **no** | yes |
| bound-flag load in path? | – | yes | yes | only on logged lines | no | no | no | no | yes |

Values are ns/call medians; the min-max ranges are in the logs.

\* OLD in the disabled phase of ablation runs 1 and 2 measured 14-18 ns. Elsewhere the same code is much faster:
- Ablation run 3 measured 4.96 ns. In every main-mode run (v0 and final builds), OLD disabled was 0.5-1.1x OLD filtered.
- The OLD loop body for the disabled case is byte-identical to the filtered one (checked with objdump), and it measures 6-8 ns in the filtered phase of the same runs.

So the outlier comes from the run structure of ablation runs 1-2 or from the environment, possibly hybrid-core scheduling. It did not recur, the cause is not understood, and the NEW ranking does not depend on it.

Reading the ablation:
- `[[unlikely]]` causes the large filtered-path regression (+3-5 ns): v2 and v4h, which keep it, are as slow as v0 in all four runs.
- Once `[[unlikely]]` is gone, the bound-flag check accounts for what is left:
  - v1 is 1.0-1.7 ns slower than v3 in every run: 7.30 vs 6.28, 7.69 vs 6.44, 8.64 vs 7.32, and 15.20 vs 13.50 (run 4, 100% load).
  - The v1 loop is 16 objdump lines longer than v3 (118 vs 102, counting relocation lines; `b5_variant_codegen_v2.txt`). Counting instructions only (`b5_variant_codegen_v3.txt`): v1 95, v1' 92, v3 83, OLD 79.
  - v3 and v4 match OLD within noise in runs 1-3. In run 4 (100% load) they measured 1.10x and 1.24x OLD.
  - The 19:26 reading, based on two runs, called this "≤ ~1 ns, within noise". With four runs it is a consistent 1.0-1.7 ns.
- The floor-pointer indirection costs nothing measurable: v3 ≈ v4.
- On the disabled path all NEW variants are within noise of each other (0.7-1.1 ns in run 3, 2.4-4.2 ns in run 4), about 4-6x below OLD.
- **Outcome:**
  - Agent 12 adopted v1 at 19:27, on the 19:26 recommendation to drop `[[unlikely]]`.
  - At 19:54 Agent 12 moved the bind behind `should_log` (v1'), so it runs only for logged lines.
  - In run 4, v1' ≈ v3 on the filtered path (13.83 vs 13.50 ns), while v1 measured 15.20: the bound-flag cost is gone, as intended.
  - v1' is 1.13x OLD in run 4, but the ranges overlap (OLD 10.68-14.60, v1' 11.91-20.77), and the main table shows 1.0x.

## Caveats

- **Noise:** every run shared the CPU with 11 other agents (load 40-100%). The min-max spread is often ±30-50%, so only differences much larger than the spread (B1 coalescing, B2 contention) are conclusive.
- **B5 final load:** the final v1' runs (`b5_v1p*.md`, `b5_ablate4.md`) were all taken at 100% load, and their absolute ns are up to ~2x those of the lighter-load v1 runs. Only the OLD/NEW ratios carry over. There was no lighter-load v1' re-run.
- **B5 module binding:** the bench is a single module, so it cannot show the SDK's per-module floor binding. In the SDK, a module that has never logged an enabled line reads its own floor (0) and pays the filtered-row cost, which is now at OLD parity.
- **Mocks:**
  - Guest memory, LookupHeap, the heap locks and the fixup registry are simplified mocks that follow the SDK call sequence. Host file I/O, however, is real Win32 (CreateFileW/ReadFile with the SDK flags).
  - B5 models the DLL import of GetLoggerRaw as a call through a function pointer defined in another TU.
- **Behaviour differences found by T1** (the allowed ones, plus the straddling fixup listed above) were reported to Agent 12. T1 found no other differences.
- **Re-sync:** if xfile.cpp, xmemory.cpp, virtual_file_system.cpp or the logging headers change again, re-sync `src/xfile_replica.h` and `src/mock_memory.h` (§A/§B), `src/b3_open.cpp` (§C) and `src/b5_log_shared.h` (§D), and re-run T1 and T2.
