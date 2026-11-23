# Pause-order replica stress test (task #17 helper)

Host-thread **replica** of the `ReXApp::SetGuestPaused` ordering in
`DimensionsRecomp/rexglue-sdk/src/ui/rex_app.cpp` (OLD path vs the new `pause_safe_order` path). No SDK
code is used: [pause_stress.cpp](pause_stress.cpp), built and run by [build_run.ps1](build_run.ps1).

## Method

Threads (one process):

| thread | models | loop |
|---|---|---|
| guest 0, guest 1 (busy, suspended by the UI) | guest XThreads | log line: `sink_mutex` + heap `std::string` + `sink_us` spin; `malloc` 64 KB..1 MB (uniform), touch every page, `free` (above the 16 KB LFH limit: process-heap lock); `G` (`std::recursive_mutex`) held `g_us`; `T` (`std::shared_mutex`) held shared `t_us`; `free_us` unlocked spin |
| audio worker (never suspended) | AudioSystem worker | 1 ms high-res timer tick; the "guest callback" enters `G` 4x (5 us held, 30 us work between); pause point after the callback: sees the request -> sets the fence -> waits for the resume event |
| UI (main) | ReXApp UI thread | gap U(0..2 ms) -> pause -> gap U(0..2 ms) -> unpause, N cycles |
| watchdog | - | a UI step older than 200 ms = HANG, counted under the step's name; rescue = `ResumeThread` on both guests every ~1 ms until the step ends (no heap, log or lock use) |

UI steps (`snapshot` = lock `T` exclusive + allocate a 64 KB block, i.e. `GetObjectsByType`):

| mode | pause | unpause |
|---|---|---|
| `old` | snapshot -> `SuspendThread` x2 -> **audio-fence** wait -> **sink** (log line under `sink_mutex`) -> **heap** (log alloc + snapshot free) | **T** (lock exclusive) -> **heap** (alloc under T) -> `ResumeThread` x2 -> audio resume -> log -> free |
| `new` | snapshot, reserve saved list, free snapshot, audio-fence, log -- all **before** suspending; suspend loop only sets flags | `ResumeThread` from the saved list **first**, then audio resume, log, clear list |
| `guard` | `old`, but each `SuspendThread` runs with `G` and `T` (exclusive) held by the UI and waits for the thread to really stop (`GetThreadContext`) -- models Agent 11's part B | as `old` |

Parameters of the reported runs: `g_us=200 t_us=50 sink_us=30 free_us=400`, 1000 cycles per run
(capped at 20 s; capped runs report fewer cycles and are normalised per 1000), modes interleaved
inside each of 5 rounds (old, new, guard), CPU load (`Win32_Processor.LoadPercentage`) sampled before
every run. Built with the repo toolchain exactly like `bench/agent12/build.ps1`
(`toolchain/llvm-23.1.6/bin/clang-cl.exe /O2 -march=x86-64-v2 /std:c++latest /MD`).

## Results

Run 2026-11-21 19:43-19:47, 5 rounds. Raw rows: `build/agent12/pause/runs.csv`, generated tables:
`build/agent12/pause/summary.md`, console log: `build/agent12/pause/run_full.log`.

**Hangs per 1000 cycles**, median [min-max] over 5 runs (one hang = one UI step stalled >= 200 ms):

| mode | cycles/run (median) | cycles with a hang | audio-fence | sink | heap | T | suspend / pre / resume | CPU load before run (median) |
|---|---|---|---|---|---|---|---|---|
| old | 278 (20 s cap) | 298.6 [266.9-334.7] | 151.1 [122.2-225.8] | 74.7 [60.5-96.5] | 36.3 [19.3-50.4] | 28.8 [12.1-29.6] | 0 | 79 % |
| new | 1000 | **0 [0-0]** | 0 | 0 | 0 | 0 | 0 | 96 % |
| guard | 458 (20 s cap) | 172.5 [130.4-180.4] | 31.8 [17.0-45.9] | 63.9 [43.5-69.8] | 73.1 [55.2-83.0] | **0 [0-0]** | 0 | 99 % |

Totals: old 414 hangs in 1388 cycles (audio-fence 222, sink 111, heap 48, T 33); new **0 in 5000
cycles**; guard 394 in 2460 cycles (audio-fence 77, sink 148, heap 169, T 0). Every hung cycle had
exactly one hang (`hang_cycles == hangs` in all runs).

**UI-step latency**, cycles without a hang, us: median [min-max] over the 5 runs of each run's percentile:

| mode | pause p50 | pause p99 | unpause p50 | unpause p99 |
|---|---|---|---|---|
| old | 169 [112-223] | 1171 [544-1878] | 53 [37-73] | 490 [436-588] |
| new | 263 [194-330] | 3933 [732-5646] | 40 [24-52] | 571 [383-1740] |
| guard | 455 [330-685] | 5449 [1068-7596] | 76 [43-101] | 691 [491-841] |

Pilot with the default hold times (`g_us=40 t_us=4 sink_us=4`, 300 cycles, one run each): old 5 hangs
(heap 4, sink 1), new 0, guard 27 (audio-fence 13, heap 11, sink 3) -- same picture at lower rates.

### Findings

1. **old hangs in every hazard step** (audio-fence, sink, heap, T); **new never hangs** (0 in 5000
   cycles): after its suspend loop the UI calls only `SuspendThread`/`ResumeThread`/`SetEvent` until
   every guest runs again.
2. **guard removes the T hangs but not the audio-fence hangs** (32 vs 151 per 1000). There were no
   `suspend`-step hangs, so the UI always got `G` back: the lock is *free*, not handed to a suspended
   thread. The likely mechanism: while the UI holds `G` (through the `GetThreadContext` wait) a guest
   queues on `G` and is suspended in that wait; the UI's unlock wakes that waiter, which cannot run, and
   the SRW lock wakes no one else, so the audio worker queued behind it sleeps on a free lock. In the
   real app that clears only when some other running thread cycles `G`; nothing does in the replica.
3. **Per-step counts mask each other.** The rescue resumes the guests, so a cycle can hang only at its
   first hazardous step; pause steps run audio-fence -> sink -> heap. Rates of later steps are lower
   bounds. That is why guard shows *more* sink/heap hangs than old: fewer cycles stop at the audio fence.
4. **guard makes the pause slower** (p50 455 vs 169 us, p99 5.4 vs 1.2 ms): `GetThreadContext` waits
   until the target thread is scheduled to take the suspend, and `G` and `T` are held for that long.
5. **new costs some pause latency** (p50 263 vs 169 us, p99 3.9 vs 1.2 ms): the audio fence, the log
   line and the heap calls now run against live guests (contention on `G`, the heap lock and the sink).
   Unpause is a little faster (p50 40 vs 53 us). The new runs also saw higher machine load (96 % vs
   79 %), and the old figures exclude its 30 % hung cycles.

## Reproduce

```powershell
# build + 5 interleaved rounds + summary (build/agent12/pause/{runs.csv,summary.md})
powershell -ExecutionPolicy Bypass -File bench/agent12/pause/build_run.ps1 -Runs 5 -Cycles 1000 -MaxSeconds 20 -Extra "g_us=200 t_us=50 sink_us=30"
# one run
build/agent12/pause/pause_stress.exe mode=old cycles=1000 seed=1 g_us=200 t_us=50 sink_us=30
```

Other knobs: `hang_ms` (200), `gap_us` (2000), `free_us` (400), `audio_entries` (4), `audio_g_us` (5),
`audio_work_us` (30), `max_s` (20).

## Caveats

- A replica of the **ordering**, not the real ReXApp: no XThread/object_ref, no real AudioSystem,
  spdlog or rexglue global lock. Rates depend entirely on the chosen hold times; the table shows which
  steps **can** hang and that the new order removes them, not how often the real app hangs.
- The UI's heap block is 64 KB so every UI heap call takes the process-heap lock. The real snapshot
  vector and log buffers are small and normally come from the LFH, which takes the heap lock only to
  refill or release a subsegment, so the real heap hazard is rarer (but not zero).
- A "hang" is a UI step stalled >= 200 ms. Without the rescue these stalls would be permanent in the
  replica (nothing else releases the lock). Cycles with a hang are excluded from the latency figures.
- The machine is shared with other agents; preemption stretches lock hold times and the time
  `GetThreadContext` waits for the target thread to be scheduled.
