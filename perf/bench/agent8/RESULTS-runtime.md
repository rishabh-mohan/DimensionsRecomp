# Agent 8: rexlego runtime edits, old vs new microbenchmarks

- **Run:** 2026-11-21, 18:47:45 to 18:50:06 local. `runs=5`, `take_budget_ms=150`.
- **Machine:** 12th Gen Intel Core i7-1255U (hybrid: 2 P-cores + 8 E-cores, 12 logical threads), Windows.
- **Outcome:** 318 CHECK PASS, 0 FAIL. Every bench process exited with code 0.
- **Raw data:** `build/agent8/bench/logs/`. It holds `summary.txt` and `summary.md` (generated), `load.txt`, `build.log`, and one `<bench>_<variant>_r<k>.out.txt` / `.err.txt` per run.

> [!WARNING]
> Other agents were compiling the whole time. CPU load was 82–100% (mostly 97–100%), with 0–4 clang/ninja/cl processes running. The numbers are noisy: use the medians, and treat the max columns as scheduling noise.

## Re-run

From the repo root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\build-runtime-benches.ps1
```

Options:

| Option | Effect |
|---|---|
| `-Runs N` | Number of runs (default 5) |
| `-TakeBudgetMs N` | Time budget per TakeResults scenario (default 150) |
| `-Targets cheat_old,cheat_new,discord_old,discord_new,atomics` | Comma-separated subset to build and run (default: all five) |
| `-NoBuild` | Reuse the existing exes |
| `-NoRun` | Build only |

What the script does:
1. Dot-sources `env\devshell.ps1`.
2. Builds sequentially into `build\agent8\bench\{obj,bin}`, one compiler process at a time, with lld `/threads:1`.
3. Runs every bench, then writes the summaries.

CPU cost of one full run: about 31 CPU-seconds in total. That splits into roughly 20 s for cheat TakeResults, 8.2 s for atomics timing and 2.6 s for the idle group. No more than 2 threads are ever busy; only the contended atomics phase uses 2.

## What is compiled

| Bench | OLD exe | NEW exe |
|---|---|---|
| cheat | `bench/agent8/cheat/old/cheat_engine.{h,cpp}` (pre-edit copy) + `cheat/bench_cheat.cpp -DBENCH_OLD` | `DimensionsRecomp/rexlego/src/cheat_engine.{h,cpp}` (real source, unchanged) + `cheat/bench_cheat.cpp` |
| discord | `bench/agent8/discord/old/discord_presence.cpp` + `discord/bench_discord.cpp -DBENCH_OLD` | `DimensionsRecomp/rexlego/src/discord_presence.cpp` (unchanged) + `discord/bench_discord.cpp` |
| atomics | `atomics/bench_atomics.cpp`: a single exe holding both variants (see below) | (same exe) |

The atomics exe contains:
- both `Enabled()` bodies, copied verbatim from `build/agent8/orig/native_atomics.cpp` (old: function-local `static const bool`) and from `rexlego/src/native_atomics.cpp` (new: latched `std::atomic<int8_t>`);
- a noinline big-endian CAS `Add()` (`std::atomic_ref<uint32_t>`, bswap, `compare_exchange_weak` seq_cst) behind three hooks: old check, new check, and no check.

Stubs live in `bench/agent8/stubs/`:
- `rex/logging.h`: REXLOG_* calls are counted.
- `rex/cvar.h`: REXCVAR_DEFINE_BOOL/STRING and REXCVAR_GET, backed by plain globals.
- `rex/system/xmemory.h`: `rex::memory::Memory`/`physical_membase()` over a VirtualAlloc'd 512 MiB reservation. `REX_RAW_ADDR` is `base + uint32_t(addr)`, with a minimal `PPCContext`.

All other headers, including `discord_presence.h` and `area_watch.h`, are the real ones resolved from `rexlego/src`. The real sources compiled unchanged under `-Wall` with no errors.

Toolchain: LLVM clang 23.1.6 (GNU driver, MSVC target) plus the VS 2022 x64 environment, loaded with `. .\env\devshell.ps1 -Quiet`. The CRT is the clang++ driver default.

```text
compile: clang++ -O3 -std=c++23 -march=x86-64-v3 -DNOMINMAX -DWIN32_LEAN_AND_MEAN -D_CRT_SECURE_NO_WARNINGS -Wall
         -I bench/agent8/stubs [-I DimensionsRecomp/rexlego/src] [-DBENCH_OLD] -c <src> -o build/agent8/bench/obj/<name>.o
discord_presence.cpp TUs additionally:
         -I DimensionsRecomp/rexglue-sdk/thirdparty/fmt/include -DFMT_HEADER_ONLY -include bench/agent8/discord/no_real_discord.h
link:    clang++ -fuse-ld=lld -Wl,/threads:1 <objs> -o build/agent8/bench/bin/<name>.exe
```

`build/agent8/bench/logs/build.log` has the full command lines.

## Method

**Run order and statistics**
- The cheat TakeResults runs alternate old and new in ABBA order (old, new, new, old, old, new, ...), 5 runs each.
- The idle-dominated benches (freeze thread old/new, discord old/new) run as a group of 4 concurrent processes per round. Each uses about 0 CPU. The launch order alternates between rounds.
- Each run prints one value per metric. Every table shows the median of the 5 per-run values, with [min–max] across runs.
- For TakeResults, the per-run value is the median of up to 5000 timed calls within the 150 ms budget, with at least 15 calls.
- For the destructor and Stop(), each run reports both the median and the max of its own samples.

**Wake-ups and cycles**
- A wake-up is the delta of the thread's `ContextSwitches`, read from `NtQuerySystemInformation(SystemProcessInformation)` at the start and end of the window (`common/wake_count.h`).
- Cycles come from `QueryThreadCycleTime`.
- Context switches also count preemptions, so under load the counts run slightly above the pure wake-up count.

**Identifying the bench thread**
- Windows starts an extra thread-pool worker at the same moment as the bench thread (2 new threads were seen), so the bench thread is identified explicitly:
  - The **discord thread** is the thread that called `CreateFileA`; the shim records its thread id.
  - The **freeze thread** is the new thread with the most context switches during a 400 ms freeze/unfreeze probe.

**Discord safety**
- `no_real_discord.h` is force-included into both `discord_presence.cpp` TUs. It `#define`s `CreateFileA` to a shim.
- The shim rewrites `\\.\pipe\discord-ipc-N` to `\\.\pipe\agent8-bench-absent-ipc-N`, a pipe that never exists, and counts the calls.
- `llvm-nm` confirmed that neither discord object references the raw API.
- The check `no_real_discord_connection` requires redirected == calls, refused = 0 and opened = 0.

**Cheat memory**
- The engine's `kPhysicalSize` is 512 MiB (0x20000000). The bench reserves all of it and commits 40 MiB: 8 MiB at 0, 1 MiB at every 16 MiB boundary, and the last 1 MiB. Everything else is PAGE_NOACCESS.
- The candidate bitmaps are full size: 16 MiB for 32-bit scans and 64 MiB for 8-bit scans.
- The engine's save path points to a directory that does not exist (`<exe dir>\agent8-no-such-dir`). The destructor's `Save()` therefore fails fast, and nothing is written.

**Cheat scenarios**

Each scenario plants values, then runs StartNewScan, waits, runs StartScanExact, waits, and times `TakeResults(200)`. The driver waits by polling `scanning()` every 200 µs on a high-resolution waitable timer.

| Scenario | Type | What is planted |
|---|---|---|
| a | u32 exact (0x13572468) | 200 hits spread over all committed chunks of the 512 MiB |
| b | u32 exact | 5 hits in the last MiB |
| c | u8 exact (0xA5) | 5 hits in the last MiB |
| d | u32 exact | 1,000,000 hits, dense from address 0 |

**Timer granularity**
- The engine's 50 ms waits and Discord's 100 ms sleeps run on the default Windows timer. The observed period of a 50 ms wait is about 61 ms, which matches a 15.6 ms tick.
- As a result, restores of a frozen value run at about 33 per 2 s rather than 40, and the old idle loop wakes about 17 times per second rather than 20.

## 1. cheat_engine: cached scan results

### `TakeResults(200)`: ns per call (the UI calls it every frame while the menu is open)

| Scenario | Old median [min–max] | New median [min–max] | Old/new | Old cost at 60 fps | New cost at 60 fps |
|---|---:|---:|---:|---:|---:|
| a: u32, 200 hits spread | 6.04 ms [5.31–15.6 ms] | 126 ns [110–206] | 47,955× | 362 ms/s = 36.2% of a 16.67 ms frame | 0.0076 ms/s |
| b: u32, 5 hits at the end | 6.30 ms [5.42–11.1 ms] | 95 ns [63–163] | 66,499× | 378 ms/s = 37.8% of a frame | 0.0057 ms/s |
| c: u8, 5 hits at the end | **30.3 ms** [20.4–56.7 ms] | 94 ns [51–153] | 321,763× | 1,818 ms/s = **182% of a frame** (the game can no longer hold 60 fps) | 0.0056 ms/s |
| d: u32, 1M dense hits | 679 ns [549–1,077] | 100 ns [67–187] | 6.8× | 0.041 ms/s | 0.0060 ms/s |

The fastest single call per run (median over runs) tells the same story:

| Scenario | Old fastest call | New fastest call |
|---|---:|---:|
| a | 4.79 ms | 60–80 ns |
| b | 5.44 ms | 60–80 ns |
| c | 20.0 ms | 60–80 ns |
| d | 405 ns | 60–80 ns |

Even its fastest call in the 8-bit case is longer than a whole frame. Samples per run: old 15–27 calls (the 150 ms budget); new 5000 calls, falling to 2031 on the busiest run.

### Scan time (ms, median [min–max]; very noisy)

| Scenario | StartNewScan old | StartNewScan new | StartScanExact old | StartScanExact new |
|---|---:|---:|---:|---:|
| a | 219 [186–378] | 218 [157–610] | 49.8 [42.4–103] | 42.7 [33.4–156] |
| b | 28.2 [21.0–36.2] | 12.7 [8.8–35.8] | 64.6 [42.9–89.2] | 50.7 [43.8–115] |
| c | 68.6 [45.7–186] | 47.4 [27.1–261] | 143 [112–504] | 201 [110–1016] |
| d | 38.2 [10.9–100] | 31.3 [11.5–103] | 67.7 [34.1–164] | 44.9 [39.8–277] |

The new filtering scan ends with one `CollectResults(1024)` bitmap walk. That walk costs about one old TakeResults call (around 5–6 ms for 32-bit scans, 20–30 ms for 8-bit), paid once per scan instead of every frame. The c exact-scan medians (143 → 201 ms) fit that, but the noise is too large to pin the extra cost down.

### Per-row cost avoided by ImGuiListClipper (`cheat_menu.cpp` DrawResults)

Each row calls `ReadValue(address, type)` and `IsFrozen(address)`.

| | ns per row | 200 rows per frame | 8 visible rows per frame | + snprintf: ns per row | + snprintf: 200 rows | + snprintf: 8 rows |
|---|---:|---:|---:|---:|---:|---:|
| old | 7,560 [6,813–14,907] | 1.51 ms | 60 µs | 8,599 | 1.72 ms | 69 µs |
| new | 7,680 [7,183–13,456] | 1.54 ms | 61 µs | 8,704 | 1.74 ms | 70 µs |

- The engine edit leaves this cost unchanged; the saving comes from the clipper. Drawing about 8 rows instead of 200 saves about 1.45 ms per frame (about 1.65 ms including snprintf).
- The cost is dominated by `VirtualQuery` in the readable-address check. The bench's sparse reservation of 35 separate regions probably makes `VirtualQuery` dearer than in the game, so treat these numbers as an upper estimate.

### Freeze thread

| Metric | Old median [min–max] | New median [min–max] |
|---|---:|---:|
| Idle (no frozen values, no cheats): wake-ups per 5 s | **85** [79–93] (16.8/s) | **0** [0–0] |
| Idle: thread cycles | 711 kcycles/s | 0 |
| One frozen value: restores per 2 s (value corrupted by the driver) | 32.8 [27.5–33.8] | 32.8 [29.5–33.7] |
| One frozen value: wake-ups per 2 s | 45.4 [33.4–52.7] | 37.8 [31.5–49.3] |
| One frozen value: thread cycles | 3,786 kcycles/s | 3,536 kcycles/s |
| Destructor latency, idle: per-run median | **33.6 ms** [20.5–50.6] | **1.19 ms** [1.14–2.30] |
| Destructor latency, idle: per-run max | 76.6 ms [41.0–105] | 16.7 ms [9.9–63.2] |
| Destructor latency, one frozen value: per-run median | **46.5 ms** [34.5–62.3] | **1.90 ms** [0.53–2.94] |
| Destructor latency, one frozen value: per-run max | 89.4 ms [61.4–263] | 18.1 ms [7.2–26.5] |

- Each destructor sample is a construct → random 5–125 ms delay → destroy cycle, run both idle and with one frozen value. The timed span includes `Save()`, which fails fast.
- The new destructor's maxima are most likely scheduling latency on the nearly fully loaded machine: the woken thread has to get a time slice.

## 2. discord_presence: event-driven wait

Discord was not running (absent pipe). Each run calls `Start()`, measures a 10 s window, then does 11 `Stop()` samples: the first right after the window, then 10 Start → random 60–360 ms → Stop cycles.

| Metric | Old median [min–max] | New median [min–max] |
|---|---:|---:|
| Wake-ups per 10 s | **97.8** [92.8–102.9] (9.8/s) | **6.0** [5.0–10.0] (0.6/s) |
| Thread cycles | 543 kcycles/s | 248 kcycles/s |
| CreateFileA pipe probes per 10 s | 39.9 | 49.9 |
| `Stop()` latency, per-run median | **76.6 ms** [51.1–93.6] | **1.59 ms** [0.16–12.8] |
| `Stop()` latency, first call | 23.6 ms [1.2–138] | 0.151 ms [0.137–0.311] |
| `Stop()` latency, per-run min | 20.6 ms [1.2–39.5] | 0.115 ms [0.100–0.172] |
| `Stop()` latency, per-run max | 123 ms [109–219] | 32.6 ms [16.2–47.6] |

- **Pipe probes:** the new code retries the connection on an exact 2 s cadence, which works out to 5 attempts per 10 s. In the old code, every 100 ms sleep slice overshoots to the timer tick, which stretches the period to about 2.5 s (4 attempts per 10 s). The 2 s cadence is the intended behaviour, and a probe of a missing pipe is cheap.
- **New `Stop()` max:** most likely scheduling latency under load.

## 3. native_atomics: `Enabled()` check

Timing: 5 rounds × 2e7 hook calls per variant (1e8 calls per variant in total), single-threaded. The contended run uses 2 threads × 1e6 calls each on one word, per round.

| Metric | Old (`static const bool`) | New (latched `atomic<int8_t>`) | No check (baseline) |
|---|---:|---:|---:|
| Hook + Add, single thread (ns per call) | 29.3 [22.6–49.6] | 31.4 [24.2–33.8] | 32.4 [24.1–49.5] |
| `Enabled()` alone (ns per call) | 3.76 [3.40–6.12] | **2.41** [1.66–6.09] | — |
| Hook + Add, 2 threads contended (ns per call per thread) | 110.7 [66–143] | 78.3 [57–118] | 92.3 [63–146] |

- On its own, the new check is about 1.35 ns per call cheaper: a relaxed byte load replaces the thread-safe-static guard, which checks a TLS epoch.
- Inside a real hook the difference is lost in the noise. The seq_cst `lock cmpxchg` costs about 30 ns, and even the "no check" baseline lands at the same value.
- The contended numbers are dominated by noise. **No meaningful difference.**

## Correctness checks: 318 PASS, 0 FAIL

**cheat**: each check below ran in all 5 runs and passed in all 5, in both the old and the new exe.

| Check | What it verifies |
|---|---|
| `plant_a`–`plant_d` | A brute-force walk of memory finds exactly the planted set |
| `take200_a`–`take200_d` | `TakeResults(200)` equals the brute-force first 200 |
| `take5000_a`–`take5000_d` | `TakeResults(5000)` (longer than the 1024-entry cache) equals the brute-force first 5000 |
| `take_limits_a`–`take_limits_d` | Limits 1, 199, 1023, 1024, 1025 and 4096 all match brute force |
| `take200_stable_a`–`take200_stable_d` | Repeated calls return identical results |
| `newscan_clears_a`–`newscan_clears_d` | A fresh StartNewScan clears the results |
| `compare_refresh_a` | After half the hits change, StartScanCompare refreshes the cached results correctly |
| `compare_unchanged_a` | An unchanged-compare scan returns the correct set |
| `freeze_thread_found` | The freeze thread was identified |
| `frozen_value_reapplied` | The frozen value is restored after the driver corrupts it |

**discord**: 5/5 in both exes for `discord_thread_found` and `no_real_discord_connection`.

**atomics**:
- For `LEGO_NATIVE_ATOMICS` unset, `=0` and `=1` (set with `_putenv_s` before the first call), each of these passes: `old_eq_expected`, `new_eq_expected`, `old_eq_new`, `latched` and `hook_routing`.
- `single_counts`, `contended_counts` and `no_fallback_when_enabled` also pass.

## Observations on the real sources

- **No bugs found in any of the four edits.** I reviewed:
  - the cheat cache publish/clear ordering, and the TakeResults fallback when `limit` is larger than the cache (verified at the 1023/1024/1025 boundaries and at 5000);
  - the freeze-thread condition variable: the stop flag is set under `apply_mutex_` and then `notify_all`; `SetFrozen(true)` notifies; `SetFrozen(false)` erases the entry;
  - Discord `Stop()`: the flag is cleared under `g_wake_mutex`, then notify;
  - the `Enabled()` latch race, which is benign because both racers compute the same value.
- **Biggest win:** with an 8-bit scan open, the old menu spent about 30 ms per frame in `TakeResults`, more than a whole 60 fps frame. With 32-bit scans it was about 6 ms per frame. The new code serves this in about 100 ns.
- **Trade-off:** each filtering scan now pays one extra bitmap walk (about one old TakeResults call). That is acceptable.
- **Remaining per-frame cost:** reading values costs about 7.6 µs per row because of `VirtualQuery`. The clipper is what keeps this to about 60 µs per frame. If the menu ever becomes hot again, caching the readable-region checks would be the next step. This was not done; it is only a suggestion.
