STATUS: DONE 20:34 (2026-11-21). Built, piloted and run on the real driver; results below.
CPU used: about 150 CPU-s in total. The main run took 122.4 s, slightly over the 2-minute target; the pilots plus the debug run took about 28 s. Don't rerun it unless the driver or the save code changes.

# D3D12 pipeline-library probe (Agent 6, task #5)

The probe is a standalone program, [d3d12_library_probe.cpp](d3d12_library_probe.cpp). It exercises `ID3D12PipelineLibrary` on the real GPU the same way `gpu_native/pipeline_library.cpp` does, and it answers five questions:

- **(b, c)** How long does autosave hold the library mutex, comparing the old `Save()` with the new snapshot (report #1, item 1)?
- **(d)** Does the `Serialize` output depend on what the buffer held before? This decides whether item 1 keeps the file byte-identical.
- **(e)** What do library opens and loads cost, and do loads scale across threads (report #2)?
- How does driver PSO creation scale with threads (item 3, parallel `Prepare()`; item 4, the async pool)?
- Can `LoadGraphicsPipeline` and `StorePipeline` run while another thread is inside `Serialize` (variant B of report #1)?

## Machine

| | |
|---|---|
| OS | Windows 10.0.26300.9974 |
| CPU / RAM | Intel Core i7-1255U, 12 logical processors, 31.7 GiB |
| GPU | NVIDIA GeForce MX570 (0x10DE / 0x25A6), 1.9 GiB VRAM |
| UMD driver | 32.0.16.1088 |
| `D3D12_SHADER_CACHE_SUPPORT` | 0x7F (LIBRARY bit set) |
| D3D12 debug layer | installed |
| Load | 81-100% busy with other agents' builds during every run. Wall times are therefore pessimistic and noisy; the ratios are what count. |

## Commands

- **Build** (about 10 s): `powershell -File bench/agent6/build_d3d12_probe.ps1` → `build/agent6/d3d12_library_probe.exe`, log in `build/agent6/probe_build.log`.
- **Pilot** (CPU 5 only): `cmd /c "start "" /b /wait /affinity 20 build\agent6\d3d12_library_probe.exe --pilot"`, plus `--ops 40`, `--ops 12` and `--ops 40 --skipopt`. The ops-200 pilot is saved in `build/agent6/probe_pilot.txt`.
- **Main run** (CPUs 4-5): `cmd /c "start "" /b /wait /affinity 30 build\agent6\d3d12_library_probe.exe --n 800 --m 80 --k 300 --ops 40 --probe 2.5"` → `build/agent6/probe_out.txt` (97 lines, ending in a markdown table).
- **Debug-layer run:** `--debug --n 60 --m 20 --ops 40 --probe 0.5` → `build/agent6/probe_debug.txt` (18.8 CPU-s). The timings from this run are not meaningful.
- **Flags:**
  - `--n`: library size, in distinct PSOs.
  - `--k`: number of loads timed in (e), capped at N/4. It was 200 here.
  - `--m`: PSOs per point in the create and load scaling tests.
  - `--ops`: pixel-shader arithmetic count, which sets the shader size.
  - `--probe`: seconds per concurrency phase.
  - `--reps`: repetitions for (a)-(e). The default is 7.

## Pilot: cost per PSO by shader size (CPU 5 only)

| PS ops | fxc compile | `CreateGraphicsPipelineState` | Cached blob |
|---|---|---|---|
| 200 | 539-717 ms | 224-295 ms | 50,562 B |
| 40 | 41-94 ms | 22-43 ms | 15,698 B |
| 40, `--skipopt` | 20-50 ms | 24-60 ms (not faster) | |
| 12 | | | 9,538 B |

- **Library size steps:**
  - an empty library serializes to 900 B;
  - the first PSO adds the blob size;
  - storing the same PSO under a second name adds only 160 B, because identical PSOs are deduplicated;
  - storing a name that already exists returns `0x80070057`.

## Results (main run: N = 800 PSOs at ops 40, so S = 9,696,176 B = 9.70 MB, or 12.1 KB per PSO)

| Measurement | Median | Notes |
|---|---|---|
| Library build, 800 PSOs on 2 threads | 61.4 s wall, 90.2 CPU-s | D3DCompile 102 ms per PSO, create 52 ms per PSO, `StorePipeline` 0.06 ms |
| (a) `GetSerializedSize` | 0.0001 ms | |
| (b) OLD: `vector::resize(S)` under the lock | 2.42 ms | allocation, zero-fill and first-touch page faults |
| (b) OLD: `Serialize` into that warm buffer | 3.83 ms | 2,531 MB/s |
| (b) `Serialize` into a cold `new[]` buffer | 5.29 ms | 1,832 MB/s |
| **(b) OLD lock hold** (a + resize + `Serialize`) | **6.25 ms** | |
| (c) NEW: pre-fault outside the lock | 1.48 ms | 10.37 MB capacity |
| **(c) NEW lock hold** (re-query + `Serialize` into the pre-faulted buffer) | **3.65 ms** (max 7.3) | **42% lower** |
| (e) `CreatePipelineLibrary` on the 9.7 MB blob | 2.39 ms | |
| (e) `LoadGraphicsPipeline` from the reopened library | 0.59 ms | p99 2.85 ms, max 5.4 ms (n = 200) |

**Scaled linearly to the 512 MiB cap**, the old hold is about 346 ms per save and the new hold about 202 ms. That is about 55 times the 9.70 MB measurement.

**Scaling.** The process was pinned to 2 CPUs and the machine was 81-100% busy.

| Threads | Create 80 new PSOs | Speedup | Load 80 PSOs from the library | Speedup |
|---|---|---|---|---|
| 1 | 4,111 ms (51.4 ms per PSO) | 1.00x | 218 ms (2.7 ms per PSO) | 1.00x |
| 2 | 1,812 ms | **2.27x** | 205 ms | 1.07x |
| 4 (on 2 CPUs) | 3,672 ms | 1.12x (oversubscribed) | 160 ms | 1.36x |

**Concurrency.** Thread A runs `Serialize` back to back. Thread B loads existing PSOs and stores new ones. No application lock is held.

| B's calls | Without A | Started inside an A `Serialize` |
|---|---|---|
| `LoadGraphicsPipeline` | median 0.0057 ms, p99 0.096, max 24.7 (n = 134,685) | **median 0.0062 ms, p99 0.017**, max 36.5 (n = 50,906) |
| `StorePipeline` | median 0.25 ms, p99 2.8, max 6.5 (n = 120) | **p99 = max = 115 ms** (n = 94). The longest store overall took 204 ms. |
| A's `Serialize` | | median 7.7 ms, p99 36.5, max 39.1 (n = 332). One call failed with `0x80070057`. |

## Conclusions

1. **Item 1, the snapshot, is confirmed on the real driver.**
   - Taking the allocation and page faults out of the lock cuts the hold from 6.25 to 3.65 ms (−42%) at 9.7 MB. That is about 346 → 202 ms at the 512 MiB cap.
   - What is left is the `Serialize` copy itself, at about 2.6 GB/s.
   - The CPU-only bench `save_lock_hold` models `Serialize` as a `memcpy`. It measured 1,288 → 279 ms at 512 MiB, because its old path includes a cold 512 MiB zero-fill.

2. **(d): the buffer MUST be zero-filled before each `Serialize`.**
   - On this driver, `Serialize` leaves some bytes in [0, S) unwritten.
   - Into a buffer prefilled with 0xCD, the output differs from the old zero-filled `std::vector`, both with size = S and with size = capacity.
   - Into zeroed memory (fresh pages), the output is identical.
   - `Serialize` never writes past `size`. It rejects size < S (S−1, S/2 and 0 were tested) with `0x80070057` and leaves the buffer untouched.
   - `pipeline_snapshot.h` already meets this requirement:
     - `Allocate()` uses `new (std::nothrow) uint8_t[n]()`, which value-initialises, so the memory is zeroed.
     - Every save allocates a new buffer.
     - A retry frees the old buffer before allocating another zeroed one.
     - `copy()` always receives exactly the queried size.
   - **So the file stays byte-identical.** Never replace this with an uninitialised `new[]`, `make_unique_for_overwrite` or a reused buffer: the file would change (and heap garbage would leak into it).

3. **Variant B of report #1** (calling `Serialize` without our mutex) is only safe with stores still excluded.
   - The runtime already lets loads through during a `Serialize`: their latency doesn't change.
   - Stores wait inside the driver for up to 115-204 ms. That is longer than any single `Serialize`, which suggests the writer is starved behind back-to-back serializes.
   - A store between `GetSerializedSize` and `Serialize` makes `Serialize` fail with `E_INVALIDARG`, because the size grew in between.
   - So variant B needs a split lock: loads shared, stores and `Serialize` exclusive. The only gain would be loads that currently queue on our mutex behind a `Serialize` (about 3.6 ms at 9.7 MB, about 200 ms at the cap).
   - It is not done in session 2. The in-game `pso_stats` lock-wait counters should show that this wait matters first.

4. **Report #2, striped library loads, is low value on this driver.**
   - Loads scale 1.07x on 2 threads and 1.36x on 4, so they are mostly serialised inside the runtime or driver anyway.
   - A load costs about 0.6-2.7 ms.

5. **Driver compiles scale with real cores:** 2.27x on 2 threads (the super-linear part is noise from the shared machine). This supports item 3 (`LEGO_NATIVE_PSO_PREPARE_THREADS`) and item 4's default pool of 2 threads. More threads than free cores gives nothing (1.12x).

6. **What a synchronous PSO miss costs:**
   - A library hit takes about 0.6 ms.
   - A driver compile takes about 20-50 ms at ops 40 and about 220-400 ms at ops 200, which is 30 to 600 times longer.
   - This gap is the "FPS improves the longer you play" mechanism that the `pso_stats` counters measure in-game.

7. **Debug-layer run: the API usage is clean.**
   - The (d) results are the same.
   - There are exactly 4 messages, all from deliberate misuse in (d) and the pilot:
     - one "a pipeline with name "c" already exists" (severity 2), from the duplicate-name test;
     - three "Serialize: An insufficient amount of memory was provided" (severity 1), from the S−1, S/2 and 0 calls.
