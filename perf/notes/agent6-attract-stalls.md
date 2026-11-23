# Agent 6: first-view stalls in the attract sequence (task #18)

Status: **analysis done, 2026-11-22 ~04:30. §10 (S4 items table, for Agent 10) and §11 (diagnostic-run spec) added ~05:05 at Agent 1's request; §11.1 (results of both §11 arms: skip §10.1) added ~06:25.** No game runs, no builds, no git writes; all scripts are single-threaded and read-only.
Input data: Agent 3's tie-break runs `build/agent3/runs/20261122-031756-bgate-long-devoff2` and `build/agent3/runs/20261122-032150-bgate-long-devoffB`. Both are OFF builds on the standard emulated-Xenos D3D12 path.

> [!WARNING]
> Both runs are FUNCTIONAL ONLY: hidden desktop, laptop i7-1255U (12 logical CPUs) plus an NVIDIA dGPU. Treat absolute times as indicative. The *attribution* (which frames, what they coincide with) is robust; the milliseconds are not timing-grade.

## Bottom line

1. **The stalls are first-use pipeline creation on the GPU thread.** With `async_shader_compilation` on (the default), a draw whose pipeline isn't built yet is skipped. The GPU thread still **waits for every queued pipeline at the next EndSubmission**, which is normally the swap. The cost therefore lands in the row with the misses (sync or mid-frame waits) or in the row after it (wait at swap). It is not hidden.
2. **Attribution of frames >250 ms:**
   - devoff2: 21 frames, 25.9 s. **96% are on a miss row or the row after one.**
   - devoffB: 26 frames, 17.3 s. **72%** are; the other 28% are 7 heavy-draw frames with no misses (2.7 s) and 4 frames that come *before* their misses (2.2 s).
   - If the two frames dominated by host-GPU fence waits (cb ≈120) are counted as not-compile, the shares are 87% and 62%.
3. **Caches:**
   - The Xenos shader storage (`.xsh`/`.xpso`) is **on by default but cold in every harness run**, because each run gets a fresh `<run>\user`. The `.xpso` holds exactly one 72-byte record per pipeline miss.
   - The **NVIDIA driver cache is shared across run dirs and is warm** since devoff2 (the first run to reach the attract). Going cold→warm halved the cost per miss: 116 → 58 ms per miss.
   - There is no D3D12 PSO library, and textures are not persisted.
4. **A warm Xenos storage** (seeded files) would move about 214 pipelines into the blocking boot phase. My estimate is +1-3 s of boot (unmeasured). It should remove the miss-coincident stalls in the attract, which is most of the stall time. It won't fix the heavy shots, the load-frame stall that comes before its misses, the host-GPU waits, or texture loads.
5. **S4: no code change needed.** The `cache_root` cvar already exists. The simplest option needs no cvar: copy the two seed files into `<run>\user\cache\shaders\shareable\`. What Agent 8's runner needs is in §7.
6. **Benchmark window (task #16):** Agent 3's window H0+5.5…+20.5 s is **compile-free even with a cold storage** (1 miss, no visible cost). Its edges need care:
   - the last compile stall before it ends at H0+5.36 s;
   - its last ~2 s are the heavy-draw segment (≥9.8k draws from H0+18.2 s), which is throughput-bound.

   Details are in §8.

## 1. Method and scripts (`build/agent6/attract-stalls/`)

| script | what it does | output |
|---|---|---|
| `analyze_stalls.py` | Per frame >250 ms: perf.csv counters ±2 rows, game.log lines ±2 s with thread ids, samples.csv cores/private MB, and wall-clock alignment from perf.csv flush marks (±0.04-0.7 s). Groups frames into events. | `report-250ms.txt`, `out/*.stalls.{json,csv}` |
| `attrib.py` | Directional attribution using the SDK row semantics (below) plus benchmark-window stats. | `attrib-250ms.txt`, `attrib-100ms.txt` |
| `residual.py` | Splits all frames into pipeline-adjacent, texture-only, heavy and other, to estimate what a warm storage leaves. | `residual.txt` |
| `scan_runs.py` | Cross-run scan of ~70 agent3/agent8 run dirs: boot gap after "Initializing shader storage", storage file sizes/seeding, cost per miss. | `scan-runs.txt`, `out/scan_runs.json` |

**Row semantics** (verified in the SDK; see §2):
- perf.csv row k is host wall time on the GPU thread from XE_SWAP k−1 entry to XE_SWAP k entry. Its counters cover the same span: `Profiler::Flip()` runs at swap entry, before `IssueSwap`.
- Misses in row k come from frame k's draws.
- Classes for a slow frame k:
  - **P0** = misses on row k (sync creation, a mid-frame EndSubmission, or the GPU thread draining the queue itself);
  - **P1** = misses on row k−1 only (async creation awaited in IssueSwap(k−1));
  - **PRE** = misses on k+1/k+2 but none on k or k−1, so the stall *precedes* the misses and the compile mechanism doesn't explain it;
  - **heavy** = ≥5000 draws and no misses within ±2 rows.
- H0 is the first 2823-draw/366,575-vertex row, the same anchor as agent3-run-harness.md §7.4. H0+s is the row's start time relative to H0's start.
- Launch→H0 is ~180.3 s in devoff2 and ~187.4 s in devoffB. The first 3D frame is at launch+151.5 s and +155.6 s.

## 2. How a miss becomes a stall (SDK, rexglue-sdk HEAD c5fe668e)

The research subagent read the code; I re-checked the starred lines myself.

| fact | where |
|---|---|
| ★ The frame time is taken at XE_SWAP entry, then `Profiler::Flip()`, then `IssueSwap`, then `LimitFramerate`. | `src/graphics/command_processor.cpp:1051-1087` |
| ★ With async on, a draw with an unbuilt pipeline returns early (the draw is dropped). | `src/graphics/d3d12/command_processor.cpp:2726-2729` |
| ★ `PipelineCache::EndSubmission` first drains the creation queue on the GPU thread, then **waits for all busy creation threads**. It is called from every `D3D12CommandProcessor::EndSubmission` (swap, readback fence waits, memexport, occlusion queries). | `src/graphics/d3d12/pipeline_cache.cpp:795-813`; call at `d3d12/command_processor.cpp:4236` |
| ★ Queued creation translates the shaders with **one shared `shader_translator_` under `translation_request_lock_`**, so gameplay translation is serial. Only `CreateGraphicsPipelineState` runs in parallel on the "D3D12 Pipelines" threads. | `pipeline_cache.cpp:3173-3237` |
| Draws with no pixel shader (depth-only) are created synchronously on the GPU thread (`use_async` requires a PS). | `pipeline_cache.cpp:942-943, 1069-1071` |
| Creation threads: `d3d12_pipeline_creation_threads` = −1, which means max(¾ of logical CPUs, 1) = **9 here**. | `pipeline_cache.cpp:58, 153-167` |
| `pipeline_cache_misses` = the first time this process sees a pipeline description, which means exactly one new PSO. Pipelines preloaded from storage count as hits. | `pipeline_cache.cpp:1035/1042` |
| `texture_cache_misses` = a new SRV *descriptor*, not a texture load. Loads are timed separately (`kTextureLoad`). | `d3d12/texture_cache.cpp:2092/2095, 1605` |
| `command_buffer_stalls` = waits on a D3D12 fence (host GPU behind, including frame latency). It **does not** count compile waits. | `d3d12/command_processor.cpp:3938, 3960` |
| ★ Storage init runs **blocking**, before the guest main thread resumes (`InitializeShaderStorage(cache_root, title, true)`, then `Resume()`). | `src/ui/rex_app.cpp:626-632` |
| Storage path: `cache_root` cvar, else `<user_data_root>\cache`; then `shaders\shareable\5752084B.xsh` and `5752084B.rtv.d3d12.xpso`. A header or version mismatch truncates the file. | `rex_app.cpp:233-256`; `pipeline_cache.cpp:222-337, 730-737` |
| ★ Startup quirk: the extra-thread loop tests `< creation_thread_original_count` (it should test `needed`). So no extra threads start, and the blocking wait at 685-715 never runs. Pipelines still building after boot are awaited at the first EndSubmission. This only matters for warm boots. | `pipeline_cache.cpp:560-571, 683-716` |
| ★ `slow_frame_log_ms` (default 0) logs, for every frame over the threshold, gpu-thread idle, host-gpu wait, translate/create (sync path only), texture load, readback and memexport, over the same window as a perf.csv row. "Idle time is the tell: … slow on the game's side". | `d3d12/command_processor.cpp:79, 236-284` |
| No `ID3D12PipelineLibrary` or CachedPSO anywhere. Only the guest ucode (.xsh) and pipeline descriptions (.xpso) persist, so a warm boot still translates and creates every PSO, just at boot. | `src/ui/d3d12/d3d12_util.cpp:50-51`; `pipeline_cache.cpp:227-232` |

Overrides:
- Our runs set no shader, cache or log cvars. The run.json command line is `--log_file … --log_flush_interval=1 --perf_log_csv … --native_settings_load=false --discord_rpc=false --audio_mute=true --pause_when_unfocused=false --input_backend=xinput`. The toml only sets texture-cache limits and `primitive_processor_cache_min_indices`.
- Nothing in DimensionsRecomp overrides `store_shaders`, `cache_root` or `async_shader_compilation`. The F4 menu only displays them.
- The installer sets `user_data_root` to a persistent content root, so **real players have a warm storage from their 2nd launch**. Harness runs are always the first-launch case.

## 3. Frames over 250 ms

game.log at info level has **no shader, pipeline or texture lines at all**.

Within ±2 s of the stall frames there are only two kinds of line:
- the Toypad LED write `… 01 0F 01 99 42 0E …` that starts the attract, logged at the first 3D frame: devoff2 −0.38 s on t76784/t37768; devoffB −0.03 s on t47716/t78192;
- "Window closing" at the end of the run.

The following come *before* the stalls, not during them:
- INSTALL0_N.DAT probe batches (0xC000000F): devoff2 t97048, last at 03:20:21.4 (8.4 s before the first 3D frame); devoffB t28160, last at 03:24:13.7 (14.4 s before).
- XamUserReadProfileSettings: devoff2 t8356, devoffB t94028, both ~3 s before the first 3D frame.

The log has thread ids but no thread names. By the SDK mechanics, the stalled thread is the GPU thread ("GPU Commands"), waiting on the "D3D12 Pipelines" workers or doing the creation itself. During the stall frames, samples.csv shows CPU at 1.8-4.7 cores and private memory +110-200 MB per first-view event.

**devoff2** (pm/tm = pipeline/texture misses, pm₋₁ = misses on the previous row, cb = command_buffer_stalls):

| row | H0+s | ms | class | draws | verts | pm | pm₋₁ | tm | cb | note |
|---|---|---|---|---|---|---|---|---|---|---|
| 8140 | −28.80 | 1902 | P0 | 625 | 780 | 21 | 0 | 10 | 10 | first 3D frame (Toypad attract write) |
| 8141 | −26.90 | 524 | P1 | 594 | 2,813 | 0 | 21 | 8 | 0 | |
| 8274 | −24.18 | 440 | PRE | 219 | 226 | 0 | 0 | 0 | 0 | load frame; misses on the next row |
| 8275 | −23.74 | 1297 | P0 | 768 | 5,292 | 23 | 0 | 2 | 4 | |
| 8276 | −22.44 | 662 | P1 | 789 | 31,617 | 0 | 23 | 30 | 0 | +30 new texture descriptors |
| 9259 | −1.91 | 797 | P1 | 790 | 43,673 | 0 | 1 | 5 | 0 | a single new pipeline |
| 9268 | −0.98 | 644 | P1 | 1,370 | 118,865 | 0 | 1 | 2 | 0 | a single new pipeline |
| 9370 | +4.63 | 730 | P1 | 8,066 | 1,043,741 | 0 | 4 | 2 | 0 | ends at H0+5.36 |
| 9630 | +20.93 | 5609 | P0 | 12,390 | 1,397,564 | 67 | 0 | 2 | 1 | the 12.4k-draw shot |
| 9631 | +26.54 | 477 | P1 | 12,398 | 1,593,275 | 0 | 67 | 38 | 0 | |
| 9633 | +27.24 | 2387 | P1 | 2,520 | 502,000 | 0 | 10 | 0 | **120** | mostly host-GPU fence waits? |
| 9635 | +29.68 | 632 | PRE | 1,822 | 447,648 | 0 | 0 | 0 | **231** | host-GPU fence waits |
| 9637 | +30.42 | 2489 | P0 | 1,491 | 315,180 | 1 | 6 | 7 | 27 | |
| 9638 | +32.91 | 319 | P1 | 1,383 | 290,514 | 0 | 1 | 2 | 2 | |
| 9639 | +33.23 | 949 | P0 | 4,660 | 821,440 | 12 | 0 | 0 | 13 | |
| 9640 | +34.18 | 703 | P0 | 4,701 | 949,403 | 4 | 12 | 1 | 15 | |
| 9641 | +34.88 | 1194 | P0 | 5,058 | 995,486 | 15 | 4 | 1 | 2 | |
| 9642 | +36.07 | 2353 | P0 | 5,118 | 1,348,763 | 31 | 15 | 1 | 15 | |
| 9643 | +38.43 | 547 | P1 | 5,156 | 1,455,048 | 0 | 31 | 1 | 2 | |
| 9647 | +39.28 | 410 | P0 | 10,625 | 1,325,876 | 3 | 0 | 1 | 2 | |
| 9648 | +39.69 | 805 | P0 | 10,883 | 1,416,241 | 2 | 3 | 0 | 6 | last row (WM_CLOSE) |

By class: P0 10 frames 17.71 s (68%), P1 9 frames 7.09 s (27%), PRE 2 frames 1.07 s (4%).

**devoffB:**

| row | H0+s | ms | class | draws | verts | pm | pm₋₁ | tm | cb | note |
|---|---|---|---|---|---|---|---|---|---|---|
| 1892 | −143.37 | 270 | P0 | 221 | 11,970 | 3 | 0 | 1 | 1 | menu |
| 7822 | −31.78 | 624 | P0 | 625 | 780 | 21 | 0 | 10 | 10 | first 3D frame (Toypad attract write) |
| 8130 | −25.05 | 1305 | PRE | 219 | 226 | 0 | 0 | 0 | 0 | load frame; misses on the next row |
| 8131 | −23.74 | 357 | P0 | 768 | 5,292 | 23 | 0 | 2 | 4 | |
| 8132 | −23.38 | 281 | P1 | 789 | 31,617 | 0 | 23 | 30 | 0 | |
| 9522-9528 | +18.73…+21.06 | 289-479 | heavy | 9,872 / 7,594 / 5,620 | 0.92-1.36 M | 0 | 0 | 0 | 0 | 7 frames, 2.67 s, no misses |
| 9529 | +21.40 | 366 | PRE | 5,624 | 922,989 | 0 | 0 | 0 | 0 | heavy; 67 misses two rows later |
| 9531 | +21.84 | 4092 | P0 | 12,393 | 1,412,288 | 67 | 0 | 7 | 1 | the 12.4k-draw shot |
| 9532 | +25.93 | 1008 | P1 | 12,398 | 1,593,275 | 0 | 67 | 33 | 0 | |
| 9534 | +27.09 | 1598 | P1 | 2,522 | 526,240 | 0 | 7 | 0 | **119** | mostly host-GPU fence waits? |
| 9545 | +30.02 | 515 | P0 | 1,440 | 302,216 | 2 | 5 | 7 | 2 | |
| 9557 | +31.72 | 267 | PRE | 1,323 | 294,260 | 0 | 0 | 0 | 4 | |
| 9558 | +31.99 | 340 | P0 | 1,327 | 304,503 | 15 | 0 | 0 | 2 | |
| 9559 | +32.33 | 486 | P0 | 1,364 | 407,802 | 4 | 15 | 0 | 3 | |
| 9560 | +32.82 | 897 | P0 | 1,442 | 377,479 | 12 | 4 | 1 | 2 | |
| 9564 | +34.33 | 528 | P1 | 5,099 | 1,044,721 | 0 | 3 | 1 | 2 | |
| 9565 | +34.85 | 299 | PRE | 5,103 | 1,047,409 | 0 | 0 | 0 | 4 | |
| 9566 | +35.15 | 293 | P0 | 5,108 | 1,183,161 | 2 | 0 | 0 | 2 | |
| 9567 | +35.44 | 751 | P0 | 5,089 | 1,306,803 | 30 | 2 | 0 | 2 | |
| 9568 | +36.20 | 337 | P1 | 5,132 | 1,357,872 | 0 | 30 | 0 | 2 | last row (WM_CLOSE) |

By class: P0 10 frames 8.62 s (50%), P1 5 frames 3.75 s (22%), PRE 4 frames 2.24 s (13%), heavy 7 frames 2.67 s (15%).

**Frames over 100 ms** (`attrib-100ms.txt`):
- devoff2: P0+P1 = 25.9 of 29.1 s (89%); heavy 13 frames 1.6 s; PRE/none 5 frames 1.5 s; P2 1 frame 0.1 s.
- devoffB: P0+P1 = 13.9 of 24.9 s (56%); heavy 24 frames 5.2 s; PRE/none 27 frames 5.5 s; P2 2 frames 0.3 s.
- P2 = misses only two rows earlier, which the wait mechanism doesn't explain. "none" = <5000 draws and no misses within ±2 rows.

**What the non-compile frames are, as far as perf.csv can tell:**
- **PRE load frame** (8274 / 8130; 219 draws, 226 vertices): 0.44 s and 1.31 s. The three-row sum for the load transition is similar in both runs (2.40 s vs 1.94 s), but the split between rows differs. That points to work the counters can't see: guest-side loading, or texture loads (`kTextureLoad` isn't in perf.csv). The guest dispatch rate during it (~1.2 functions/ms) equals the rate in the compile-stall frames, so this doesn't decide it. `slow_frame_log_ms` would: gpu-thread idle means the game side.
- **Host-GPU waits:** devoff2 9633/9635 and devoffB 9534 have cb 119-231. These are fence waits on the GPU itself, right after a 67-miss burst. Possibly driver-side work on first use of new PSOs, or heavy GPU passes. Unattributed.
- **Heavy shots** (devoffB 9522-9529, pm 0): draw throughput. The same frames were 107-152 ms in devoff2, so expect large run-to-run spread there.
- **Texture misses alone never made a slow frame.** Frames with texture misses but no pipeline miss within ±2 rows had max 76 ms (devoff2, 31 frames) and 185 ms (devoffB, 46 frames) (`residual.txt`).

## 4. Caches across launches

| cache | location | persists across our runs? | evidence |
|---|---|---|---|
| Xenos shader storage | `<run>\user\cache\shaders\shareable\5752084B.xsh` + `.rtv.d3d12.xpso` | **No.** It is cold every run (fresh `user_data_root`). On for players. | `.xpso` = 12 B header + 72 B × pipelines. Record count = the run's total misses: devoff2 15,420 B = 214 = pm 214; devoffB 15,132 B = 210 = pm 210; menu runs 732 B = 10 = pm 10; short runs 516 B = 7, 588 B = 8. No run in ~70 had a pre-existing file. |
| NVIDIA DXCache | `%LOCALAPPDATA%\NVIDIA\DXCache\{fc52,0002}a9d86c51791d.nvph` (16 MiB each) | **Yes.** It is shared by all run dirs. | Created 11/21 19:29:03 by `build/agent8/runs/1928-first`; written by later runs (last 04:09:47). |
| D3D shader cache | `%LOCALAPPDATA%\D3DSCache\<hash>\` | **No.** There is one new dir per exe path, so every run gets its own. | 135 dirs / 293 MB; 83 created since 11/21 19:00. Holds an `F4EB2D6C-…dxcache` (~5.6 MB) and an NVIDIA-adapter file. Owner and contents unverified. |
| PSO library / texture cache | none | n/a | No `ID3D12PipelineLibrary`; textures are rebuilt each launch. |

**The 35 s first-boot gap was the cold driver cache, not Xenos storage.**
- `1928-first` (the first launch ever on this box) has 34.9 s between "Initializing shader storage" and the next log line. Its storage files were *created at the end* of that gap (19:29:46). It paid 390 ms per miss in the menus.
- Every later run (60+, all with fresh user dirs) has a 0.03-0.48 s gap and 18-130 ms per miss.
- Storage init runs on the GPU thread via a blocking `CallInThread`. So it can only start once the GPU thread has finished its own startup work. On the first-ever launch that work hit a cold NVIDIA cache.

**The NVIDIA cache warming for the attract** (devoff2 was the first run to reach the attract; devoffB ran right after it):

| event | devoff2 (NV cold) | devoffB (NV warm) |
|---|---|---|
| whole run (pm; excess s; ms per miss) | 214; 24.73 s; 115.6 | 210; 12.16 s; 57.9 |
| first 3D frame, 21 pm | 2.43 s | 0.62 s |
| load transition, 23 pm (3 rows) | 2.40 s | 1.94 s |
| single-miss rows at H0−1.9 / −1.0 | 797 / 644 ms | 122 / 94 ms |
| 4 pm at H0+4.4 | 730 ms | 172 ms |
| 12.4k shot, 67 pm (+ next row) | 5.61 s (+0.48 s) | 4.09 s (+1.01 s) |

With the driver cache warm, the 67-miss burst still costs ~61 ms per miss. That residue is not driver compile time: it is serial DXBC translation (one translator, one lock) plus PSO creation and runtime work. Warm Xenos storage moves that residue to boot, where translation runs in parallel. The serial-translation share is a **hypothesis**; §6 has the diagnostic.

## 5. Would a warm cache remove these stalls on a second launch?

**Mostly, for the attract content.**
- With a seeded storage, all ~214 pipelines (and their shaders) are created during the blocking boot phase.
- In gameplay they count as hits, so P0/P1 frames should vanish: devoff2 19 of 21 frames >250 ms (24.8 s), devoffB 15 of 26 (12.4 s).
- These stay:

| residue | devoff2 | devoffB |
|---|---|---|
| heavy-draw frames >250 ms | 0 | 7 frames, 2.67 s |
| PRE (load frame, host-GPU waits) | 2 frames, 1.07 s | 4 frames, 2.24 s |
| P1 rows dominated by fence waits (may also stay) | 9633, 2.39 s | 9534, 1.60 s |
| texture loads inside first-view rows | not separable; ~1-3 s per run by the texture-only cost | same |

**Boot cost:**
- Shaders are translated at boot on ≤11 "Shader Translation" threads, and the pipelines are created on 9 workers plus the GPU thread.
- My estimate is **+1-3 s at boot** with a warm driver cache. The worst case without parallel speed-up is ~12 s (214 × 58 ms).
- It is printed in game.log (gpu, INFO): `Translated N shaders from the storage in X ms` and `Created N graphics pipelines … from the storage in X ms`.
- Because of the startup quirk (§2), up to ~9 pipelines can still be building when the guest resumes. Their wait lands in the first menu frames, far from the attract.

**Side effect worth knowing:** with async on, cold first-view frames are drawn with the not-yet-built draws missing. That content depends on timing, so frame or pixel comparisons over the attract should skip miss rows (or use the warm arm).

## 6. S4 proposal

**No code change.** Everything a warm-cache arm needs exists today (`cache_root`, or a copy into the default path). For players, the storage is already persistent.

Follow-ups, smallest first. None of them is needed for task #16. §10 turns items 2-4 into an S4 table for Agent 10, and §11 is the run spec for item 1.
1. **Diagnostic run, cvars only** (spec in §11). `slow_frame_log_ms=50` is output-identical (it only adds INFO log lines).
   - Its gpu-thread-idle number settles the PRE load frame (game side or emulator side).
   - Its host-gpu-wait number settles the cb≈120 frames.
   - A second variant with `d3d12_pipeline_creation_threads=0` makes creation synchronous, so the translate/create timers split the burst cost (async waits are untimed). That variant moves stalls into the same row and drops no draws, so its frames are not output-identical to the default.
   - `[log.levels]` with `gpu = "debug"` adds a per-pipeline `Creating graphics pipeline with VS…, PS…` line with the thread id. The harness's Set-Toml appends keys, so that table must be the last thing in the toml.
2. **Later slot, if (1) shows translation dominates:** give each creation thread its own `DxbcShaderTranslator` and replace the global lock at `pipeline_cache.cpp:3185` with a per-shader claim (§10.1). This would be output-identical (same DXBC; check with `dump_shaders` hashes), so it could be ON by default once proven. It would cut cold first-view bursts like the 67-miss shot.
3. A one-line fix at `pipeline_cache.cpp:564` (`original` → `needed` count). It only matters for warm boots, so it is minor here (§10.2).
4. Not for S4 by default: a non-blocking async mode (don't await creation at EndSubmission; keep dropping draws until ready). It swaps stalls for multi-frame pop-in, so it is not output-identical and can only be an opt-in cvar, OFF by default. In async mode the deferred command list never sees an unbuilt pipeline, so the change is small (§10.3).

## 7. What Agent 8's runner would need for a warm-cache arm

> [!NOTE]
> **Proposal for after window 4** (Agent 1, 04:36: no runner changes before window 4 has run); sent to Agent 8 as such at ~05:10. For the functional harness, Agent 3's `harness/run-game.ps1 -SeedXenos <dir>` (04:42) already does steps 2-3 for a given seed dir: it copies `*.xsh`/`*.xpso` into `<user>\cache\shaders\shareable`, refuses to overwrite, records sha256 and sizes in run.json `seed_xenos`, captures the storage lines and prints the xpso pipeline count before and after. Seed dir: `build\agent3\seed\devoff2-214` (xsh 160,232 B, xpso 15,420 B = 214 pipelines).

1. **Seed:**
   - Make one cold run of the target bin that runs to ≥ H0+40 s (past the 12.4k shot and the H0+26…37 s events).
   - Freeze `<seed>\user\cache\shaders\shareable\5752084B.xsh` and `5752084B.rtv.d3d12.xpso` into a read-only seed dir, recording sha256, size and pipeline count = (xpso − 12) / 72.
   - The devoff2 run dir already holds a 214-pipeline seed (xsh 160,232 B, xpso 15,420 B), which is usable for builds with the same GPU path.
2. **Per warm run:**
   - Copy both files into `<run>\user\cache\shaders\shareable\` before launch. No cvar is needed, since `cache_root` defaults to `<user_data_root>\cache`.
   - Alternatively, copy them to `<run>\xcache\shaders\shareable\` and pass `-Cvar cache_root=<run>\xcache`.
   - **Never** point concurrent runs at one live dir: the files are opened in append mode with no locking. Never let runs write into the seed.
   - The existing `-SeedCache` only copies the native-GPU `native-pso*.bin`, so it doesn't cover this.
3. **Checks per run:**
   - The two INFO lines in game.log, with N ≈ 214. Missing lines or N = 0 mean the seed was rejected (version or rtv/rov mismatch truncates it), and the run is cold.
   - pm in the scored window = 0 and pm for the attract ≈ 0.
   - Log xpso growth (72 B per new pipeline) as a seed-completeness check.
4. **Arms:**
   - Interleave cold and warm arms (A B A B).
   - Warm boots are longer (blocking pre-creation, and a shader-compile notice overlay shows meanwhile). Anchor scoring on H0, not launch or first frame.
   - The unscored cold run only re-warms the NVIDIA cache. It matters after a driver update or a GPU-path change, not per run.
5. **Re-seed** whenever the bin changes the GPU path (rtv/rov), the pipeline or translator storage versions, or the shader translator code.
6. Optional: a separate diagnostic arm with `slow_frame_log_ms=50` (§6 item 1; spec in §11).
7. D3DSCache stays cold per run unless the exe runs from a fixed path. Leave it as it is. It grows by one dir per run (293 MB so far).

## 8. What this means for the attract benchmark warm-up (task #16, Agent 3)

**First-view compile stalls recur in every harness run** (cold Xenos storage), at fixed scene points:

| scene point (H0-relative) | stall |
|---|---|
| first 3D frame, −29…−32 s | 0.6-2.4 s |
| load transition, −24…−25 s | 1.9-2.4 s |
| −1.9 and −1.0 s | ≤0.8 s |
| +4.4…+5.4 s | 0.17-0.73 s |
| 12.4k shot, +20.9 / +21.8 s | 4-5.6 s |
| +26…+37 s | several 0.3-2.5 s frames |

**Window H0+5.5…+20.5 s:**

| | devoff2 | devoffB |
|---|---|---|
| frames | 252 | 193 |
| median | 56 ms | 68 ms |
| p99 | 132 ms | 396 ms |
| max | 152 ms | 479 ms |
| frames >250 ms | 0 | 5 |
| misses inside | 1 (r9505, 60 ms, no visible cost) | 1 (r9452, no visible cost) |
| texture misses | 2 | 2 |

So the window is compile-free even cold. Keep pm/tm as info flags.

- **Start edge:** the last compile stall before the window (4 misses at H0+4.4; its wait row runs H0+4.63→5.36 in devoff2) ends **0.14 s** before the window opens. The attract timing jitters by ~0.3-0.9 s between runs, so it can slide in. A stall flag at ≥1 s would miss it (730 ms). Use a ≥250 ms flag, or start at ≥H0+6.5.
- **End edge:** the heavy segment (≥9.8k draws) starts at H0+18.16 s (devoff2) and +18.51 s (devoffB). The last ~2 s of the window are therefore throughput-bound: devoffB has 5 frames of 289-479 ms with pm 0; devoff2 has 107-152 ms. They are also sensitive to where the cut falls.
  - For a steady-scene metric, end at H0+17.5 (a 12 s window).
  - Alternatively, score H0+18.2…+20.5 as a separate heavy sub-window; it is compile-free when cold too.
  - Don't extend past H0+20.9 in cold runs.
- **With a warm-storage arm**, H0+5.5…+40 s should become compile-free (expected; untested). That would allow scoring the 12.4k-draw scenes, the heaviest content. The host-GPU-wait frames around H0+27…30 may remain.
- **Warm-up:** the NVIDIA cache is already warm for these builds, and no per-run warm-up can warm the Xenos storage (fresh run dir). If any scoring is anchored on first frame + N s instead of H0, note that the first-view events sit at launch+151…165 s.

## 9. Caveats

- FUNCTIONAL ONLY data: hidden desktop, two runs, and other agents' work on the same laptop. Absolute ms and the devoff2/devoffB differences (heavy shots 107-152 vs 289-479 ms) are not timing-grade.
- The P0/P1 attribution is by row adjacency plus the SDK mechanics. Within a P0/P1 row, compile, texture loads and fence waits can't be separated without `slow_frame_log_ms`.
- The warm-cache effect is an inference from the code and the cold/warm driver-cache comparison. No seeded run exists yet. The boot-cost figure is an estimate.
- The owner of the D3DSCache `F4EB2D6C-…` file and its effect on PSO creation are unverified.

## 10. S4 items (for Agent 10)

Added ~05:05 at Agent 1's request. Nothing here is implemented yet. For each item there is a design note, a review checklist and a test plan. The rule applied is OFF by default unless the change is output-identical.

Line numbers refer to rexglue-sdk HEAD c5fe668; these files are clean against HEAD. Base hashes for a hash-guarded review:

| file | sha256 (first 16) | bytes |
|---|---|---|
| `src/graphics/d3d12/pipeline_cache.cpp` | 5DBED81F611E25B1 | 161,305 |
| `include/rex/graphics/d3d12/pipeline_cache.h` | 9322AD374BF4BBEC | 17,587 |
| `src/graphics/d3d12/command_processor.cpp` | 3AB3AA5360D4E987 | 269,215 |

| item | output-identical | files touched | user-visible effect | test plan |
|---|---|---|---|---|
| **(a)** per-thread DXBC translators for the gameplay creation threads | **Yes.** Each (shader, modification) gives the same DXBC; only the completion order changes. Cold first-view frames already differ run to run, because which draws get dropped depends on timing. So compare dumps and storage record sets, not frames. | `pipeline_cache.cpp`, `pipeline_cache.h` | Shorter cold first-view stalls, if translation is a large share of a burst (it isn't: §11.1 measured a translate share of 0.01-0.03, so skip (a)). The gain is at most ~9-10× on that share of a burst like the 67-miss shot. Single-miss frames, depth-only draws and warm-storage runs don't change. | §10.1 |
| **(b)** `pipeline_cache.cpp:564` fix (`original` → `needed`) | **Yes** for cold runs, which never reach the code, and in steady state. On a warm boot the first frames can be *more* complete. | `pipeline_cache.cpp` (1 line) | Only with a warm storage (players from their 2nd launch, or a seeded harness arm). Every stored pipeline is built before the guest resumes, so there is no creation tail at the first EndSubmission and no dropped first-use draws of stored pipelines. Today's cold harness runs don't change. | §10.2 |
| **(c)** non-blocking async mode | **No.** Draws stay dropped for several frames instead of one submission. It is a new cvar, OFF by default. | `pipeline_cache.cpp`, `pipeline_cache.h`; optionally `d3d12/command_processor.cpp` | Compile hitches become multi-frame pop-in: objects or effects are missing until they are built, and the shader-compile notice shows meanwhile. Depth-only (no-PS) creation still blocks. | §10.3 |

Suggested order:
- (b) with or before the first warm-storage arm, since it makes warm boots deterministic.
- (a) only if §11 arm B shows translation is ≥ ~40% of the 67-miss burst. §11.1: it showed 1-3% on the bursts it reached, so skip (a).
- (c) only as an opt-in, after the user has seen it on a visible desktop.

### 10.1 (a) Per-thread DXBC translators

**Today:**
- With async on, gameplay shaders are translated on the "D3D12 Pipelines" threads in `PrepareRuntimeDescriptionForQueuedCreation` (:3173-3237). That happens under the global `translation_request_lock_` (:3185), with the shared `shader_translator_` (:99-103) and the GPU thread's DXIL objects (:118-138). So translation is serial; only `CreateD3D12Pipeline` (:3272) overlaps.
- The GPU thread also translates in two places:
  - the sync path for depth-only draws (:955-1007, under the same lock);
  - draining the queue in EndSubmission (:796 → :3287-3309).
- Ucode analysis always runs on the GPU thread before a pipeline is queued (`AnalyzeShaderUcode`, `d3d12/command_processor.cpp:2592/2610`, h:77). So the `AnalyzeUcode` call at :3187 returns early, and the shared `ucode_disasm_buffer_` isn't really shared.
- The shader-level parts are already thread-safe. Storage load translates on up to 11 threads with per-thread translators (:384-403), and the shared state is guarded:
  - binding setup by `bindings_setup_entered_` (`pipeline/shader/dxbc.h:76`, `dxbc_translator.cpp:1237`);
  - layout UIDs by `EnterBindingLayoutUserUIDSetup` (`d3d12/shader.h:46`, used at :1141);
  - the layout maps by `layouts_mutex_` (:1180, h:327).

**Change:**
1. Each `CreationThread` (:3239) gets its own `DxbcShaderTranslator`, built with the same 8 constructor arguments as :99-103, and its own `StringBuffer`. It also gets its own DXIL objects, but only when `d3d12_dxbc_disasm_dxilconv` is set (as at :393-403).
   - Create them lazily on the first translation, so the 2 temporary storage threads of (b) pay nothing.
   - They die with the thread, which is joined at :181-183 and :693-696.
2. `PrepareRuntimeDescriptionForQueuedCreation` takes them as a parameter. The GPU thread keeps using the existing members. `shader_translator_` thus becomes GPU-thread-only; it also serves the default-modification queries at :855/:885.
3. Replace the global lock with a **per-shader claim**. That is a set of the `Shader*` currently being translated, guarded by a small mutex plus a condition variable and held via RAII.
   - A thread waits while another thread holds the claim for the same `Shader`. It then re-checks `is_translated()`, claims, translates, releases and notifies.
   - The claim is per *shader*, not per translation. Two modifications of one shader must not be translated at once, for two reasons:
     - The first translation writes the shader-level bindings and layout UIDs without a lock. A second translation skips that step via the atomic flags, so it could publish a usable pipeline while those fields are still being written.
     - The storage-index check-and-set plus the push to `storage_write_shader_queue_` (:3193-3203) happens per shader. Without the claim, one shader could be written to `.xsh` twice.
4. The GPU thread's sync path (:958-979, :985-1007) takes the same claim. At worst it waits for one translation of that shader, which can also happen today on the global lock.
5. Make `shader_storage_file_flush_needed_` (h:383) a `std::atomic<bool>`. Workers set it (:3197) and the GPU thread reads and clears it (:781-793) without a common lock. This race exists today.
6. Add a kill switch: a bool cvar, e.g. `d3d12_parallel_queued_translation` (restart required).
   - Off keeps today's code: shared translator and global lock.
   - Land it OFF and flip it ON after the tests below, as was done for S8/S11. Because the change is output-identical, ON by default is allowed.

**Review checklist:**
- Nothing off the GPU thread still touches `shader_translator_`, `ucode_disasm_buffer_` or `dxbc_converter_`/`dxc_utils_`/`dxc_compiler_`.
- The claim is released on every path, including translation failure, and waiters re-check after waking. A failed translation still ends up translated but invalid (`pipeline/shader/translator.cpp:657-671`), so nobody retries it.
- `GetRootSignature` (:3226) still runs outside any lock.
  - With `d3d12_bindless` (default true, `d3d12/command_processor.cpp:47`) it returns a fixed signature.
  - The bindful map has no lock, but several workers already call it concurrently today. That issue predates this change and is out of scope.
- Memory: up to 9 more translator instances. Storage load already creates up to 11 temporarily.

**Test plan:**

| # | run | pass |
|---|---|---|
| 1 | Cold attract route, kill switch off vs on (same bin), each with `--dump_shaders=<run>\dump` | Same file names; byte-identical files (sha256 per file) |
| 2 | The same runs: `.xsh` and `.xpso` | Same record *sets*: sort the 72-byte xpso records and key the xsh records by ucode hash. The order may differ |
| 3 | ABAB cold attract in a timing slot, no dumps | With attrib.py per §8 scene point, the P0+P1 excess on the 67-miss shot and the H0+26…37 cluster drops by roughly the §11 translate share. Single-miss rows don't change |
| 4 | On, with `d3d12_pipeline_creation_threads` = 1, 2 and default | No hang; no "Failed to translate queued" errors; same record sets |
| 5 | On, route stopped during the 67-miss burst (~H0+21) | Clean WM_CLOSE exit, no dump |

`dump_shaders` adds file I/O, so runs 1-2 are identity checks, not timing runs.

### 10.2 (b) The `pipeline_cache.cpp:564` fix

```cpp
while (creation_threads_.size() < creation_thread_original_count) {  // today: never true
while (creation_threads_.size() < creation_thread_needed_count) {    // fix
```

- **When it matters:** only when the storage has pipelines, i.e. a warm boot. Every harness run so far has been cold, so `pipeline_stored_descriptions` is empty and :555-729 is never reached.
- **A warm boot today:**
  - No extra threads start, and :685-715 (join the extra threads, then the blocking wait) is skipped.
  - The guest resumes (`rex_app.cpp:626-632`) while up to 9 stored pipelines are still being created on the regular threads. They are awaited at the first EndSubmission.
  - With async on, a first-use draw that hits one of them is dropped until it completes.
  - "Created N graphics pipelines … in X ms" (:718-723) leaves out that tail.
- **With the fix:**
  - needed = max(min(N, 12) − 1, 9) = 11 on this laptop (12 logical CPUs), so 2 temporary threads start.
  - The GPU thread drains the queue (:684), joins the temporary threads (:686-696), then waits for the busy ones (:697-714; `blocking` is true).
  - The INFO time then covers all of the creation.
- **`d3d12_pipeline_creation_threads=0` with a warm storage:**
  - Today every stored pipeline is created serially on the GPU thread (:677).
  - With the fix, 11 temporary threads create them and are all joined (shutdown_from = 0), so gameplay stays synchronous.
  - Boot gets faster and the output doesn't change.
- **Origin:** the same line is in `baseline\DimensionsRecomp\rexglue-sdk\src\graphics\d3d12\pipeline_cache.cpp:564`, so our patches didn't introduce it. Whether upstream Xenia has it is unverified.
- **Risk:** the fix turns on :685-715, which has never run in this fork.
  - I traced the handshake (`creation_threads_shutdown_from_`, the busy count and the completion event; :3245-3266, :3279-3282) and found no deadlock. A temporary thread finishes its current pipeline and exits at :3253-3254, and the event is only requested after the joins.
  - A warm-boot test is still required.
- **Kill switch:** not needed for a line that cold runs never reach. If Agent 10 wants one, gate the loop on a bool cvar (default on; off = today's behaviour).

| # | run | pass |
|---|---|---|
| 1 | Cold run, fixed vs unfixed | No "from the storage" lines; counters within noise |
| 2 | Warm boot (`-SeedXenos build\agent3\seed\devoff2-214`), fixed vs unfixed | Both INFO lines present, N ≈ 214. In the fixed bin the "Created" value is info only (corrected 13:15, see 10.2.1). No spike in the first frames after boot in either arm (info). pm and xpso growth similar in both (the 05:29 unfixed reference has pm 56 and xpso +56 pipelines) |
| 3 | 5 warm boots ending in WM_CLOSE, fixed | No hang between "Initializing shader storage" and the next guest log line; clean exits |
| 4 | Warm boot with `d3d12_pipeline_creation_threads=0`, fixed vs unfixed | Boots; the "Created" time is several times shorter with the fix. This is the positive control: unfixed creates all 214 serially on the GPU thread, fixed uses 11 temporary threads |

> [!NOTE]
> **Rated 12:40 (b2r §27, S4-DRAFT #32):** output-identical (timing only) and SAFE, so it may ship without a switch. Runs 1-4 above are its landing gate. Agent 10 adds three things. Run 2 should log the same lines, except for the value in "Created … in X ms". An optional run with `d3d12_pipeline_creation_threads=1` is worth doing. With threads=0, the host shader-compile notice may show during boot (host UI only). Re-take any warm-boot baseline taken without the fix (#36).

#### 10.2.1 Results (task #8, Agent 6; updated as runs land)

- **Spec (13:15):** [spec.md](../build/agent6/s10-2/spec.md), sent to Agent 3, who launches every run. The reader is [s102_read.py](../build/agent6/s10-2/s102_read.py). On the 05:29 unfixed warm run it gives 229 shaders in 85 ms, 214 pipelines in 2,016 ms, a 2,397 ms gap from storage init to the next guest line, and exit 0 via WM_CLOSE.
- **Line check (13:31): PASS.** Record: [linecheck-1331.txt](../build/agent6/s10-2/linecheck-1331.txt). Script: [linecheck.py](../build/agent6/s10-2/linecheck.py).
  - Live `DimensionsRecomp/rexglue-sdk/src/graphics/d3d12/pipeline_cache.cpp`: 161,305 B, sha256 `5DBED81F611E25B1…`, LF, 3,335 lines. Same hash as the `baseline/` copy.
  - Snap `build/agent2/snap1/DimensionsRecomp/rexglue-sdk/src/graphics/d3d12/pipeline_cache.cpp`: 161,303 B, sha256 `DA77744302CFC149…`, LF, 3,335 lines.
  - Exactly one hunk: L564 `creation_thread_original_count` → `creation_thread_needed_count`. The −2 B is that rename.
  - Cross-check (13:33): Agent 2's `build/agent2/s4a/pc-warmboot.diff` and `HASHES.txt` show the same one-line change and the same before and after hashes. The `rexgpu-xenos.dll` in devoff4-bin hashes to `59662F767F8B9C7C…`, as Agent 2 announced (MANIFEST sha256 `16DCC939…`, 81 PASS / 0 FAIL).
  - Edge case (13:58): the line now in use can't underflow and spawn threads without limit.
    - L555 skips the whole block when there are no stored descriptions (cold boot).
    - L326-329 set `logical_processor_count` to 6 if the query returns 0.
    - So `min(N, lpc) − 1` is ≥ 0, and with N = 214 on 12 logical CPUs, needed = max(11, original) = 11.
    - Run 1 (cold, fixed) confirms the cold path: 82 threads at 30 s, the same as devoff3.
- **Bins:**
  - fixed (F) = `build/agent2/devoff4-bin`, which is the S3d line + #7, #8, #5, #38 (all OFF) + #32;
  - unfixed (U) = `build/agent2/devoff3-bin`.
  - native4 (`build/agent2/native4-bin`, 13:38) ships the same `rexgpu-xenos.dll` (`59662F767F8B9C7C…`, per Agent 2), so the source check covers native4 too. The runs below use devoff4 only.
  - Every run uses `-SeedXenos build/agent3/seed/devoff2-214`.
- **Correction (13:15) to run 2 above and to b2r §27 (Agent 10 struck the line there at 13:20; it's now L1492-1493, row 28):** "fixed Created ≥ unfixed" isn't a reliable pass criterion.
  - The fix adds the in-flight tail of ≤ 9 pipelines, about one creation time.
  - It also adds 2 workers: 12 counting the GPU thread's drain, against 10. So the value can go either way.
  - At default threads it's info only. Run 4 is the positive control.

| id | §10.2 run | run dir | verdict |
|---|---|---|---|
| R1 | 1, cold, devoff4 OFF (Agent 3's run) | `20261122-133333-s4a-r1-off-devoff4` vs `20261122-131206-s4a-ref-devoff3` | **PASS** (13:57). Neither run logs a "from the storage" line. Both exit 0 via WM_CLOSE with no dump and no STUCK-LOCK. pm 235 vs 235; frames 9,687 vs 9,537; first frame 14 s in both; 82 threads at 30 s in both. Agent 3's S4a gate owns the logdiff |
| U4 | 4, unfixed, threads=0 | `20261122-142856-s102-r4-t0-devoff3` (run right before F4) | **Valid reference.** Seed OK; 229 shaders in 23 ms; **214 pipelines in 6,516 ms**, all created serially on the GPU thread; gap from init to guest 7,387 ms, 844 ms of it from Created to the guest line. First frame 19.0 s. Exit 0 via WM_CLOSE, no dump, no STUCK-LOCK. 75 threads at 30 s |
| U2 | 2, unfixed, warm (fallback: `20261122-052901-attract-devoff3-warm`) | `20261122-131746-s102-r2-warm-devoff3` (13:17:51, 360 s; no game ran at the same time) | **Valid reference** (13:57). Seed OK; 229 shaders in 25 ms; 214 pipelines in 1,521 ms; gap from init to guest 1,624 ms. Exit 0 via WM_CLOSE (close took 2.9 s), no dump, no STUCK-LOCK. pm 68, xpso +68; first frame 13.0 s; worst of the first 30 frames 32.6 ms |
| F4 | 4, fixed, threads=0 | `20261122-143031-s102-r4-t0-devoff4` (run right after U4) | **PASS: the positive control.** **214 pipelines in 1,191 ms**, 5.5× faster than U4. Gap 1,293 ms (78 ms from Created to guest). First frame 10.0 s, against 19.0 s for U4. Exit 0 via WM_CLOSE, no dump, no STUCK-LOCK. 75 threads at 30 s, the same as U4, so all 11 temporary threads were joined |
| F3a-F3d | 3, fixed, boots 1-2 and 4-5 | `20261122-143207-`, `-143310-`, `-144024-`, `-144129-s102-r3-boot-devoff4` | **PASS, 5 of 5 boots including F2.** Created 881, 647, 1,715 and 740 ms (F2: 575). Gap from init to guest 944, 690, 1,832 and 805 ms (F2: 636). That is Translated + Created + ≤ 90 ms every time, so no hang. Every boot exits 0 via WM_CLOSE with the exit line and has no dump, no crash event and no STUCK-LOCK. 84 threads at 30 s = 75 + 9 regular creation threads, so the 2 temporary threads are gone. F3c's init was slower because it overlapped Agent 3's F2 postcheck |
| F2 | 2, fixed, warm (also boot 3 of run 3) | `20261122-143414-s102-r2-warm-devoff4` | **PASS** (logdiff clean, 14:54). Seed OK; the same storage lines with the same N (229 and 214); pm 68 vs 68; xpso +68 vs +68; 82 threads at 30 s in both; clean exit, no dump, no STUCK-LOCK. Agent 3 ran the logdiff with `--min-level warning` (`build/agent3/s4a/checks/F2-vs-U2-logdiff-warning.txt`, read 14:54): NEW 0 / MORE 0 / marker flags 0, with 142 warnings and a clean exit in both. Its GONE 33 are all info-level `[core] Toypad[Read ]` (4) and `Toypad[Write]` (29) packet lines whose payloads change with route timing. Info only: Created 575 vs 1,521 ms (U2 ran during Agent 2's devoff4 build); first frame 10 vs 13 s; worst of the first 30 frames 34.5 vs 32.6 ms; frames 12,595 vs 15,153. These are hidden-desktop functional runs, and per Agent 3 sys.csv shows the slow state in both runs (F2 from ~210 s). #32 only touches boot (done by ~2.5 s), and R1 shows no devoff4 frame change cold |
| F1t | optional, fixed, threads=1 | `20261122-144234-s102-t1-devoff4` | **PASS.** Created 551 ms, within the default-thread range. That fits: the fix gives 1 regular + 10 temporary threads, the same 11 workers plus the GPU thread. Gap 596 ms; first frame 8.0 s; clean exit; 76 threads at 30 s = 75 + 1 regular |

Results above are read from Agent 3's s102_read output (`build/agent3/s4a/checks/s102-read-1.txt` to `-5.txt`). Every run-game exit code was 0, and no run left a dump.

**Verdict (14:55): the #32 gate passes on every run.**
- The line check, R1, run 2, run 3 (5 of 5), run 4 and F1t pass. Run 2's logdiff (by Agent 3) is NEW 0 / MORE 0 / marker flags 0.
- The block at :685-715 had never run here. It has now run on 7 fixed warm boots (5 at default threads, threads=0 and threads=1). Every join and wait finished: Created was always logged, ≤ 86 ms before the guest line. The 30-s thread counts match U4/F4 and U2/F2, so no threads leaked.
- The run-4 control shows the fix is active: Created 6,516 → 1,191 ms, first frame 19 → 10 s.
- Next: landing in the live repo is Agent 1's call. Re-take warm-boot baselines on fixed bins (#36).

The last launch was 14:15 until Agent 1 moved it to 14:45 at 13:56. Agent 6 writes notes until 15:00, then stays idle until W4b is done.

### 10.3 (c) Non-blocking async mode

**Why async mode doesn't need the wait for correctness:**
- A draw whose pipeline is still null is dropped at record time (`d3d12/command_processor.cpp:2726-2729`), before `SetPipelineStateHandle` (:2749). So no recorded draw refers to an unbuilt pipeline.
- The wait in `PipelineCache::EndSubmission` (:795-813) therefore only limits pop-in to one submission.
- With async off the wait is required. Stored pipelines still in flight get recorded and are resolved at execute time, and `deferred_command_list.cpp:239-244` just skips `SetPipelineState` when the state is null.

**Change:**
1. Add a bool cvar, default false, e.g. `d3d12_async_pipeline_no_wait`, next to `d3d12_pipeline_creation_threads` (:58). It only takes effect with `async_shader_compilation` on and creation threads present.
2. In `EndSubmission` (:780-815), when the mode is in effect, keep the storage-flush part (:781-794) but skip both `CreateQueuedPipelinesOnProcessorThread()` and the wait.
3. Move today's wait (:795-813) into an `AwaitPipelineCreation()` helper. Call it at the top of `ShutdownShaderStorage` (:751), which `InitializeShaderStorage` also runs first (:224) before it bumps `shader_storage_index_` (:346).
   - Without it, workers that are still translating race with `storage_write_shader_queue_.clear()` (:761), with closing and nulling the storage files (:764-774), and with the index change.
   - `Shutdown` (:172-185) is fine as it is: threads stop at their next dequeue, and queued pipelines are deleted with a null state.
4. Optional: `CanEndSubmissionImmediately` (`d3d12/command_processor.cpp:4324-4326`) may return true during creation when the mode is on. `d3d12_submit_on_primary_buffer_end` (:2556-2561) then keeps ending submissions early. Leaving it unchanged is safe; it only means fewer early submissions while compiling.
5. Not covered: depth-only draws (no PS) are still created synchronously (:942-943, :1069-1071), so those stalls remain.

**Risks to review:**
- A one-shot render-to-texture pass drawn while its pipeline builds stays wrong. That already happens today, but only for one submission.
- Skipped memexport draws (GPU-written vertex data) can make effects that feed later frames glitch for longer.
- Pop-in length can't be measured today. An output-identical dropped-draw counter would measure it in both modes: a frame_stats counter at `d3d12/command_processor.cpp:2727`, printed in the slow-frame line.

| # | run | pass |
|---|---|---|
| 1 | Cvar off vs base, cold attract | Same code path by inspection; counters within noise; same storage record sets |
| 2 | Cvar on, cold attract | Frames > 250 ms at the §8 scene points drop to the non-compile residue (PRE, heavy, fence-wait and depth-only frames); pm unchanged |
| 3 | Cvar on, user on a visible desktop | The user judges the pop-in at the first 3D frame, the load transition and the 12.4k shot. Hidden-desktop runs can't judge this |
| 4 | Cvar on, route stopped during the 67-miss burst, 5 runs | Clean exit, no dump |
| 5 | Cvar on, with a warm storage | Same as warm with the cvar off (nothing to compile) |

## 11. Diagnostic run spec (§6 item 1), next-session slot

The run needs cvars only, no build. It fits Agent 8's slot or Agent 3's harness. The hidden desktop is fine, because the questions are about attribution, not timing.

**Questions**
- **Q1.** The PRE load frame (devoff2 r8274, devoffB r8130): is the GPU thread idle, meaning the cost is on the guest side (game code, file loading)? Or is it busy (texture loads, other emulation)?
- **Q2.** The cb ≈ 120 rows after the 67-miss burst (r9633 / r9534): how much of them is host-GPU fence wait?
- **Q3.** The 67-miss shot (r9630 / r9531): what share is DXBC translation and what share is PSO creation? This decides §10.1.
- **Q4.** The heavy rows (devoffB r9522-9529): guest side (idle) or GPU-thread throughput?

**Arms.** Both are cold (no seed) and use the same bin and route.

| arm | how | output-identical | answers |
|---|---|---|---|
| A | `-Arg 'slow_frame_log_ms=50'` | **Yes.** The counters are swapped every frame anyway (`d3d12/command_processor.cpp:253-258`), and the cvar only adds INFO lines (:265-283). The toml and its hash don't change. | Q1, Q2 and Q4. Q3 only as a remainder, because the async wait is untimed |
| B | `-Arg 'slow_frame_log_ms=50;d3d12_pipeline_creation_threads=0'` | **No.** All creation runs synchronously on the GPU thread, so no draws are dropped and stalls land in the miss row. Use it for attribution only, never as a perf comparison. | Q3: translate (:961/:989) and create (:1070) are timed per frame |
| C (optional) | toml `[log.levels]` `gpu = "debug"`, as the last table (Set-Toml appends) | Yes, but it logs more and changes the toml hash | Per-pipeline `Creating graphics pipeline with VS…, PS…` lines (:2718/:2722) with thread ids. Only needed if A and B leave Q3 open |

In Agent 8's runner the same cvars go in through `run-timing.ps1 -Cvar 'slow_frame_log_ms=50;d3d12_pipeline_creation_threads=0'`; its `common.ps1:94-101` turns them into `--name=value`.

**Setup**
- Bin: `build\agent2\devoff2-bin`, for comparability with the tie-break run. Its `rexgpu-xenos.dll` contains both cvar names (checked 04:50). If an S4 candidate OFF bin is used instead, also run arm A once on devoff2-bin to tie the results back.
- Command: `harness/run-game.ps1 -Seconds 420 -Warmup 60`, route `harness/routes/b-gate-menus-long.txt`, which ends the run at ~221 s (about H0+40). No `-SeedXenos`.
- Order: A, B, then A, B again if the slot allows; the repeat checks stability. Each run takes about 4.5 min, so 10-20 min in total.
- Collect: game.log, perf.csv, samples.csv, run.json and the `.xpso` size.

**Validity**
- The run reaches about H0+40: the H0 anchor row (2823 draws / 366,575 vertices) is present and the run gets to the 12.4k shot.
- Every perf.csv row > 50 ms has a slow-frame line within ±1 row whose ms matches within max(1 ms, 2%). Both measure from one swap entry to the next: perf.csv at XE_SWAP entry, and the slow-frame line at `IssueSwap` entry right after `Profiler::Flip`.
- At 50 ms the devoff2 and devoffB perf.csv files predict about 260-300 lines from the first 3D frame and 300-450 per run. That log volume is negligible.
- `.xpso` holds about 210-214 records in both arms; no crash; clean WM_CLOSE.

**Analysis:** run `python build\agent6\attract-stalls\slowframe_join.py <run dir>`.
- What it does:
  - finds the frame-number offset;
  - joins each line to its perf.csv row;
  - classes rows as in §1;
  - prints remainder = frame − idle − host-gpu wait − translate − create − texture load.
- In arm A, the remainder on P0/P1 rows is mostly the untimed async wait, i.e. compile time.
- Its decision hints:
  - **Q1:** idle ≥ 60% means the game side; neither warm storage nor S4 helps. Texture load ≥ 40% means uploads.
  - **Q2:** host-gpu wait ≥ 60% confirms GPU-side work: the driver's first use of new PSOs, or heavy passes.
  - **Q3 (arm B):** translate share = translate / (translate + create), over the 67-miss row and the row after it.
    - ≥ 0.4: do §10.1.
    - ≤ 0.2: skip it; creation dominates, and the remedy is warm storage (§7).
    - In between, (a) saves at most about share × burst.
  - **Q4:** high idle means the guest side; low idle with low waits means GPU-thread draw processing.
- Testing so far: `--selftest` builds synthetic arm A/B fixtures from the devoff2 perf.csv and checks the offset recovery, the joins and each verdict. The script hasn't seen a real slow-frame log yet.

### 11.1 Results (S11 arms A/B)

Added ~06:25. Agent 3 ran both arms at 05:40-05:50: cold, `build\agent2\devoff2-bin` (exe 7F0B1C1C), `harness/run-game.ps1 -Seconds 420 -Warmup 60`, route `b-gate-menus-long`. Joins: `python build\agent6\attract-stalls\slowframe_join.py <run dir> --out <file>`, saved as `build/agent6/attract-stalls/out/join-s11-armA.txt` and `join-s11-armB.txt`. This was the script's first real input, and it found the frame offset (0) by itself in both runs.

| arm | run dir under `build/agent3/runs/` | cvars added | health | slow-frame lines / matched / offset | H0 anchor | `.xpso` | load |
|---|---|---|---|---|---|---|---|
| A | `20261122-053957-s11-armA` | `slow_frame_log_ms=50` | exit 0, 54/54 steps, no dump, no STUCK | 541 / 541 / 0 | row 8656; the run ends ~H0+14.6 s | 4,548 B = 63 records | system 98.0% busy, MsMpEng 1.66 cores (max 3.44), game 1.94 cores |
| B | `20261122-054621-s11-armB` | also `d3d12_pipeline_creation_threads=0` | exit 0, 54/54 steps, WM_CLOSE 1.2 s, no dump, no STUCK or FATAL | 285 / 284 / 0 (unmatched: r9384 at 51.1 ms) | not found; the heavy scene starts at r9436 (4,220 draws) and the run ends ~14 s later | 4,548 B = 63 records | game 2.18 cores (samples.csv). No system sampler covered B; 05:44-05:46, with no game running, was 75% busy (MsMpEng 1.69, PresentMon 1.01 cores) |

**Validity**
- Both runs are FUNCTIONAL ONLY (hidden desktop) on a saturated machine. The attribution holds; the milliseconds don't.
- The §11 match rule holds: every perf.csv row over 50 ms has its line, except one 51.1 ms row in B at the threshold.
- Neither arm reached the 67-miss shot (~H0+21) or H0+40, and both stored 63 pipelines where the spec expected 210-214. Q2 and Q3 are therefore answered on what the runs did reach: one 21-miss and one 23-miss burst in each arm, plus 4-miss rows in both and a 1-miss row in B.
- B has no H0 signature row (2,823 draws / 366,575 vertices), so its rows are lined up by the bursts. A likely cause is that synchronous creation draws what async creation drops, which changes the draw count (unverified).
- B is for attribution only, never a perf comparison. For scale: on the same two bursts A's frames were 1,073 and 895 ms, against 2,611 and 1,284 ms in B.

**Q1: the PRE load frame is guest side.**
- A r8499: 1,473 ms, idle 1,279.7 ms (87%). B r9173: 1,529 ms, idle 1,523.4 ms (100%). Each is the frame right before the 23-miss burst.
- Neither warm storage nor S4 helps these frames.
- The other PRE rows are fence-dominated: A r8649 (485 ms, fence 329), B r9417 (449 / 362) and r9438 (334 / 222).
- The early boot load frames (A rows 279-280, B rows 346-355; 52-157 ms) are untimed GPU-thread work. They don't matter for the attract stalls.

**Q2: the cb ≈ 120 rows after the 67-miss burst were not reached.** The high-cb rows the runs did reach are mostly host-GPU fence wait, clearly in A and at the 60% threshold in B:

| arm | row | cb | frame | fence | fence share |
|---|---|---|---|---|---|
| A | 8543 | 163 | 1,753 ms | 1,594.8 ms | 91% |
| A | 8555 | 171 | 1,889 ms | 1,677.6 ms | 89% |
| A | 8731 | 134 | 1,576 ms | 1,388.1 ms | 88% |
| B | 9436 | 586 | 1,750 ms | 1,056.4 ms | 60% |
| B | 9440 | 2,438 | 4,456 ms | 2,577.7 ms | 58% |

- The `none` class (no miss, not heavy) is fence-dominated too: A 23 rows / 13.5 s at 86%, B 21 rows / 10.4 s at 79%. It is the largest block of slow-frame time in both arms.
- So this is GPU-side work, as §11 expected: the driver's first use of new PSOs, or heavy passes. Neither run has a gpu.csv, so GPU execution and driver work can't be split. On the hang runs the GPU was only 17-29% busy during long waits (`agent6-hang-triage.md`), so driver work starved of CPU is a real possibility.

**Q3: translation is 1-3% of the miss cost, so creation dominates.** Arm B, rows with misses:

| row | misses | frame | translate | create | remainder | translate share |
|---|---|---|---|---|---|---|
| 8994 | 21 | 2,611 ms | 12.9 ms | 1,175.6 ms | 1,281.6 ms (49%) | 0.011 |
| 9174 (+9175) | 23 | 1,284 ms (burst 1,348) | 13.4 ms | 741.5 ms | 480.5 ms (37%) | 0.018 |
| 9419 | 1 | 1,088 ms | 3.4 ms | 133.9 ms | 339.3 ms (fence 611.0) | 0.025 |
| 9442 | 4 | 763 ms | 1.7 ms | 118.3 ms | 298.7 ms (fence 344.2) | 0.014 |
| all | 49 | | 31.4 ms | 2,169.3 ms | | 0.014 |

- Per miss, translation costs 0.4-0.6 ms on the multi-miss rows (3.4 ms on the 1-miss row) and creation 30-134 ms.
- **Decision: skip §10.1, item (a).** The share is far below the 0.2 skip threshold. Creation dominates; the remedies are warm storage (§7) and (b), the `:564` fix (§10.2), which matters once storage is warm.
- The remainder doesn't hide translation. In arm B `use_async` is false (`pipeline_cache.cpp:942`), so `TranslateAnalyzedShader` runs entirely inside the `kShaderTranslate` scopes (:961, :989). The only shader work outside those scopes is ucode analysis (:956, :988), which stays on the GPU thread with or without (a).
- Caveat: the 67-miss shot wasn't reached. To land even in the 0.2-0.4 gray zone there, translation per miss would have to cost 14-23× more than on the two measured bursts (37-61× to reach 0.4).
- **Open:** B's two burst rows still have a 37-49% remainder, and B has no async wait. Candidates: ucode analysis and description or root-signature setup around each miss, the driver's first use of the new PSOs at submit, and CPU starvation on the saturated machine. Arm C would only time-stamp each creation; resolving this needs a CPU profile (ETW or Tracy) on an idle machine.

**Q4: the heavy rows are GPU-thread throughput.**
- A: 35 heavy rows with a line, 7.2 s, idle 23%, fence 36%. B: 29 rows, 5.2 s, idle 3%, fence 31%.
- The rest is untimed GPU-thread draw processing. It isn't guest side, and none of the §10 items address it.

**What this changes**
- §10 (a): skip. (b): unchanged; it goes in with or before the first warm-storage arm, after window 4. (c): unchanged; it stays opt-in.
- Neither arm hit the kGraphicsLock STUCK-LOCK (`agent6-hang-triage.md`).
- If another slot comes up, a warm-storage arm (§7) is worth more than rerunning §11 to H0+40.


## Agent 6 status note (updated 2026-11-23 06:50; first written 17:08, before the agy-grid restart)

- **Task #22 (wrap-up before the project pause, 2026-11-23): see §17 and `build/agent6/HANDOFF.md`.**
  - Gate B dumpstacks: done.
  - Night logdiffs on 7 dirs: no FAIL. The summary is `build/agent6/wnight/RESULTS.md`.
  - W9 env/quantum proof: 42 of 42 runs OK.
  - #33 (pop-in, opt-in): the design note and an unbuilt diff are in `build/agent6/s33-popin/`. They were staged at 06:42 and reviewed at 06:46. The cvar is `d3d12_pipeline_creation_no_wait`, default OFF. `git apply --check` passes on 5350b1d. Agent 10 rated it at 07:36 (OFF SAFE, ON SAFE-IF); the first bin should leave out hunk #5.
- **Task #19 (night-window logdiff rules for W9, W5b and W4c; paperwork only): DONE 23:12.** See §16.
  - Wrappers: `build\agent6\wnight\RUN-W9-LOGDIFF.cmd`, `RUN-W5B-LOGDIFF.cmd` and `RUN-W4C-LOGDIFF.cmd`, each taking `<matrix folder>`. Run only on Agent 1's word.
  - Accepted by Agent 1 at 23:11, including the off-arm deviation. Stop all work by 23:50.
- **Morning batch (Agent 1, 23:11). Done in task #22, 05:45-06:05; see §17.** Gate B was the only dump; Agent 3's quiet-host rows (f10a/f10b) start after the gate B result. The original brief: run dumpstacks on gate B's hang-38764.dmp together with any f10a/f10b dumps. The command is in `build/agent6/hang/cp-state-s4b24-s4b20.md` §7.2. Agent 12 has already matched gate B's owner/waiter callers and PM4 0x22 GPU state to the other three hangs. f10a/f10b on a quiet host will settle GPU-bound vs starved host. Run the logdiff wrappers (W6/W9/W5b/W4c) on Agent 1's word.
- **Task #16 (W6 prep, read-only): DONE 22:50.**
  - Part 1 (gate A hang check) and the CP-state follow-ups: §14.
  - Part 2 (W6 logdiff kit, staged and tested): §15.
  - The morning run on the W6 folder waits for Agent 1's word: `build\agent6\w6\RUN-W6-LOGDIFF.cmd build\agent8\matrix\<W6 folder>`.
  - Next after the windows: if Agent 3's quiet-host vpad L-route rows hang, read the dump the same way (CP state, kernel/user per 2 s).
- **Task #13 (W5 game.log logdiff for Agent 8's W5 read-out, matrix `20261122-1756`): DONE 21:30. Results in §13 below; checkers A and B found 0 disagreements.**
- **Task #31 (W4b game.log logdiff, every arm against d0, for Agent 8 and Agent 1): DONE as task #5 after the relaunch (go 19:31, run 19:32-19:47). Results in §12 below.**
  - **Rules:**
    - Wait for Agent 1's 'go'. Until then, file tools only.
    - While `perf-notes/WINDOW-HOLD.txt` exists, no tool calls at all.
    - After 'go', check the HOLD file before every command. Subagents (up to 2, one per arm) only read, stage and check.
  - **Driver:** `build/agent6/w4b/w4b_logdiff.py`, written 16:52 and not run yet. It imports `bench/agent8/run/gate_logdiff.py` read-only and writes no bytecode under bench/agent8.
  - **Next, after 'go':**
    1. Check HOLD.
    2. Run `python -B build\agent6\w4b\w4b_logdiff.py build\agent8\matrix\20261122-1541 --list` to see the arms.
    3. Do the full run. It writes `build/agent6/w4b/out-20261122-1541/` (summary.txt, report-<arm>.txt, data.json).
    4. Start one read-only checker subagent per arm. Each verifies its arm with gate_logdiff.py and classifies the NEW and ONLY lines.
    5. Send the per-arm findings to Agent 8 and Agent 1, then send `@@done 31`.
- **#32:** landed live with S4a (SDK 3bb65bb; Agent 1, 15:35). The warm-boot baselines on fixed bins (#36) go in a later quiet slot. §10.2.1 is final. Task #8 is done.


## 12. W4b game.log logdiff, every arm vs d0 (task #5 = old #31; 2026-11-22 19:32-19:40)

Input: Agent 8's W4b matrix `build/agent8/matrix/20261122-1541` (desktop timing window 15:41-16:17, 17 runs, all OK). Arms: d0 = devoff2 x4 (+ the unscored `1541-cold-d0`), B = devoffB x4, d3 = devoff3 x4, d11t = devoff2 + Agent 11's timer bundle + `REX_TIMER_WAIT_BLOCKING=1` x4. Read-only; no game runs, no builds.

**How:**
- `build/agent6/w4b/w4b_logdiff.py` (imports `bench/agent8/run/gate_logdiff.py` read-only). Base = the 4 warm d0 runs; the cold run is its own "arm". Its default arm grouping misses single-letter arms (B lands in "runs"), so run it with `--arm-regex '^runs/\d{4}-(cold-d0|[A-Za-z0-9]+)(?:-|$)'`. Re-run with the cold run pooled into the base (`--base '^(cold-)?d0$'`): same result.
- `build/agent6/w4b/w4b_extra.py`: run.json close/crash fields, an exact-text diff (timestamps, `[tNNN]` and run-dir names dropped, numbers and hex kept), the Toypad command sequence and challenge cadence, and boot milestones.
- Two read-only checker subagents (d11t; B + d3) redid each arm with gate_logdiff.py pairwise (arm run x each d0 run) and their own exact-text diff. Their output is in `build/agent6/w4b/check-*/`.
- Output: `build/agent6/w4b/out-20261122-1541/` (`summary.txt`, `report-{b,d3,d11t,cold-d0}.txt`, `data.json`, `extra.txt`) and `out-20261122-1541-base5/`.

**Common to all 17 runs:**
- Close and crash fields: status OK, exit 0x00000000 after a single WM_CLOSE (exit seen 0.74-1.13 s later), never killed or reposted. No WER, no dialogs, no not-responding samples, perf.csv never stalled, no `.dmp`, no foreign crash dumps.
- Every game.log ends with `Window closing` → `Execution complete` → `Title terminated; hard-exiting process.`
- gate_logdiff gives 0 FAIL findings across all 52 pairs (13 runs x 4 d0 runs). There are no [error] or [critical] lines, no STUCK lines and no unimplemented-instruction lines.
- Every run logs the same 40 warnings: the krnl stubs plus the INSTALL0_2.HDR and 34 INSTALL*.DAT NtCreateFile fails, so the light phase is normal.

| arm | NEW warn | MORE | GONE | ONLY (any level) | exact-text diff (no number normalisation) | Toypad R/W per run (d0: 10,10,10,8) |
|---|---|---|---|---|---|---|
| B | 0 | 0 | 0 | 0 | identical to d0 | 10, 8, 8, 8 |
| d3 | 0 | 0 | 0 | 0 | 1600-d3-r3: `IoDismountVolumeByFileHandle(0xf8000164)` x2 instead of `(0xf8000160)` x2 (benign, below) | 8, 10, 10, 10 |
| d11t | 0 | 0 | 0 | **1:** `[info] [core] Host timer resolution set to 1 ms (background opt-out on)` in 4/4 runs and in no other arm | only that line | 8, 10, 8, 8 |
| cold-d0 | 0 | 0 | 0 | 0 | identical | 8 |

**Notes:**
- **d11t's only extra line is the one Agent 8's plan requires** in every d11t log. Nothing else differs, even in the exact text, so the timer bundle and blocking timer waits add no warnings and remove no lines.
- **d3 handle value:** same message, level and count (2). The guest file handle is one slot higher (+4) in 1 of 17 runs, which is a handle-allocation race at boot; gate_logdiff's hex normalisation hides it on purpose. It is not tied to the early-C0 Toypad order: d0-r3 and d3-r4 have that order too and still log 0xf8000160.
- **Toypad:** no non-info Toypad line, and no frame header or command that d0 lacks. Commands are B0 wake, C0 LED, then B1/B3 challenge pairs. The 8 vs 10 line counts are not an arm effect:
  - a 3rd B1/B3 pair (+2 W, +2 R) lands only if it comes before the WM_CLOSE. The close is 112-117 s after the first Toypad write, and the challenge intervals are 26-52 s (mean: d0 37.5, B 36.1, d3 35.5, d11t 36.8 s);
  - or there is an alternate startup order, `C0 B0 B0 C0` (+1 B0, +1 C0), in d0-r3, d3-r3 and d3-r4.
- **Boot milestones** (game.log time after the first line, medians): `launching the module` 1.21 s (d0), 1.21 (d11t), 1.29 (B), 1.73 (d3, range 1.16-2.54); first INSTALL DAT fail 6.97 / 7.45 / 7.24 / 8.85 s. These are timing-only observations with wide ranges and no log signal (the d3 and B spread is in the host load step before the guest starts).
- Checker subagents (19:36-19:46, read-only, no HOLD seen) **confirm all of the above**:
  - **d11t:** gate PASS in all 16 pairs (0 findings, 0 new/gone/changed). Their own exact-text diff (68 keys) finds only the host-timer line: 4/4 d11t runs and none of the other 13 logs. Warning counts match d0 exactly (40 lines over 21 exact kinds).
  - **B:** gate PASS x16. The exact text matches d0, including line order and the address lines: function table `82620000-84113BAC`, `SetInterruptCallback(83FBF508, 40009A00)`, N0CUT5 flag at `AD0EDE54`.
  - **d3:** gate PASS x16. In exact text the only difference is the 1600-d3-r3 handle value.
  - **Toypad:**
    - The frame headers are the same in all 17 runs, and every write gets a read.
    - Challenges per run: d0 4,4,3,3; B 4,3,3,3; d3 3,4,3,3; d11t 3,4,3,3.
    - The doubled C0-first handshake has byte-identical payloads in d0-r3, d3-r3 and d3-r4. It recovers to `pad 0 mode 1 lit FF FF FF`.
    - 1606-B-r3's first challenge gap (41.3 s) is the longest of the 17 runs. It is one run, so noise.
  - Their files: `build/agent6/w4b/check-d11t/` (23 files), `build/agent6/w4b/check-b-d3/` (40 files).


## 13. W5 game.log logdiff and perf read-out support (task #13; 2026-11-22 19:49-21:30)

Input: Agent 8's W5 matrix `build/agent8/matrix/20261122-1756` (desktop timing window 17:56-18:29, 16 runs, all OK, every run `--framerate_limit=0`). Arms:
- base = `devoff3-bin` (S3d) x3, plus `1756-cold-base` (seconds=30).
- s0 = `devoff4-bin` (S4a) x3.
- d11 = s0 + 8 timer cvars x3: host_timer_resolution_ms=1, host_timer_throttling_optout, precise_guest_sleep, wait_timeout_round_up, cs_spin, spinlock_pause_spin, clock_lockfree, tls_bounds_fix.
- d11p = d11 + `timer_queue_precise_wait=true` x3.
- d11t = d11 + env `REX_TIMER_WAIT_BLOCKING=1` x3.

Read-only; no game runs, no builds. Slow runs: s0-r2 (18:08), base-r2 (18:17), d11t-r3 (18:21).

**How:**
- `w4b_logdiff.py` (imports `bench/agent8/run/gate_logdiff.py` read-only) twice: base = s0 → `build/agent6/w4b/out-20261122-1756-vs-s0/`, and base = base → `out-20261122-1756-vs-base/`. Always run it with `--arm-regex '^runs/\d{4}-(cold-[A-Za-z0-9]+|[A-Za-z0-9]+)(?:-|$)'`.
- `w4b_extra.py`, generalised with `--base` (any base arm) and `--count` (literal-count columns) → `extra-vs-s0.txt`, `extra-vs-base.txt`. Its run.json close/WER fields replace w4b_logdiff's `close=?`/`wer=?`, which are field-mapping limits.
- Source check of the timer-mode log lines: `core/threading_win.cpp:252` (via `runtime.cpp:144`), `timer_queue.cpp:59` and `:71`, against §29 of `agent10-batch2-review.md`. Only `:71` (#38) is new in S4a. The host-timer line and the `REX_TIMER_WAIT_BLOCKING` getenv predate S4a: their strings are already in devoff3's `rexruntime.dll` (checker B).
- New `build/agent6/w4b/w5_perfthreads.py` (v2) → `out-20261122-1756-vs-s0/perf-threads.{txt,json}`. Per run it reads run.json, headroom.json, threads.csv, gpu.csv and the perf.csv window. The window rows are matched to run.json `frames.window`, where `first_row` is a 0-based data-row index; this reproduces run.json mean and median in 16/16 runs. The report has content constancy, a fixed-rate fit, 10-s bins, slow-vs-rest separation, Spearman correlations and per-arm ranges.
- Two read-only checker subagents: A (timer-mode lines, s0 vs d11/d11t/d11p) and B (S3d→S4a, cold vs warm, slow-run logs, perf spot-check). Their output is in `build/agent6/w4b/check-1756-{a,b}/`.

**Common to all 16 runs:**
- Close and crash fields: status OK, exit 0x00000000 after a single WM_CLOSE (exit seen 0.67-0.91 s later), never killed or reposted. No WER, no dialogs, no not-responding samples, perf.csv never stalled, no `.dmp`, no foreign crash dumps. STUCK = 0 (run dirs, the matrix top level and `logs/`, case-insensitive). In run.json, `problems` is empty, `valid_timing` is true and `ticks_skipped_window` is 0 in all 16. The flag `light_share_high` is in every run, so it separates nothing.
- Every game.log ends with `Window closing` → `Execution complete` → `Title terminated; hard-exiting process.`
- Every log has the same 40 [warning] lines (as in W4b) and 0 [error] lines. gate_logdiff FAIL/NEW/MORE/GONE = 0 for every arm, both against s0 and against base.
- 65 of the 70 exact-text keys are in all 16 logs. The other 5 are the 2 timer-mode lines and 3 IoDismount handle variants.

| arm | bin | lines per run | ONLY lines (exact text) | other exact-text differences | Toypad R/W per run |
|---|---|---|---|---|---|
| base | devoff3 (S3d) | 98, 98, 102 | 0 | base-r1: `IoDismountVolumeByFileHandle(0xf8000158)` x2 instead of `(0xf8000160)`; base-r3: doubled handshake | 10, 10, 12 |
| cold-base | devoff3 | 98 | 0 | none (exact text identical) | 10 |
| s0 | devoff4 (S4a) | 98, 98, 98 | 0 | s0-r1: handle `0xf8000164` x2 | 10, 10, 10 |
| d11 | devoff4 | 99 x3 | **1:** `[info] [core] Host timer resolution set to 1 ms (background opt-out on)` 3/3 | none | 10, 10, 10 |
| d11p | devoff4 | 100 x3 | **2:** the host-timer line and `[info] [core] TimerQueue: precise wait (timer_queue_precise_wait)`, 3/3 each | none | 10, 10, 10 |
| d11t | devoff4 | 103, 103, 95 | **1:** the host-timer line 3/3 | d11t-r2: handle `0xf8000158`; r1 and r2 doubled handshake; r3 only 3 challenges | 12, 12, 8 |

**Notes:**
- **(a) Timer modes.** The host-timer line is in 9/9 d11, d11p and d11t runs and in none of the other 7. The precise-wait line is in d11p 3/3 and nowhere else. d11t's blocking mode logs nothing (`timer_queue.cpp:59` reads the env var silently); run.json `env_set` shows `REX_TIMER_WAIT_BLOCKING` in 3/3 d11t runs and in no other run. The warning `Could not set the host timer resolution` is in no log.
- **(b) S3d→S4a: no line difference at all.** base and s0 match in exact text, apart from the run-varying handle and Toypad lines. This fits S4a's 6 files (§29 of `agent10-batch2-review.md`): only #7 (default off) and #38 add log lines, #2 is native-only, and #8, #5(i) and #32 add none. Checker B's bin strings agree: the only new log-format strings in devoff4 are #38's TimerQueue line and #7's `S4 upload hash` line (0 of 16 logs; its cvar is default off). Today's snap1 `xmemory.cpp` also has C1 keep-watch logging, but no devoff4 binary contains it (§29 lists C1 as not in S4a).
- **(c) Cold vs warm base.** The exact text is identical; only the boot is slower (game.log time after the first line, cold vs warm-base median and range):

  | milestone | cold | warm median | warm range |
  |---|---|---|---|
  | `launching the module` | 1.46 s | 1.20 s | 1.16-1.21 s |
  | audio | 4.86 s | 3.31 s | 2.79-3.54 s |
  | first Toypad B0 | 5.55 s | 4.24 s | 3.26-4.29 s |
  | first INSTALL DAT fail | 8.70 s | 6.75 s | 6.67-7.64 s |

  run.json `boot` is 6.01 s cold vs 4.02-5.01 s warm (1-s resolution).

  Checker B found more before the first log line. That line comes 5.37 s after run.json's `process_start_mark` cold vs 2.11 s warm (2.08-2.29), and the first frame comes 11.12 s vs 5.82-7.00 s after process start. 1800-s0-r1, the first devoff4-bin run of the matrix, also started slowly (5.42 s to the first line, first frame at 10.13 s) but had normal in-log times. So the pre-log delay looks like a cost of the first launch from each bin dir (most likely its exe and DLLs weren't in the file cache yet). Only the in-log delays are cold-only. run.json `boot` doesn't include the pre-log part (s0-r1 has 5.01 like the warm runs).
- **IoDismount handle:** 0xf8000158 in base-r1 and d11t-r2, 0xf8000164 in s0-r1, 0xf8000160 in the other 13 runs. This is the same boot handle-allocation race as in §12 (same message, level and count). s0-r1's busy XThread is `F80001AC` instead of `F80001A8` for the same +4 reason; w5_perfthreads aliases it.
- **Toypad:** the commands and frame headers are the same everywhere. 12/12 is the doubled C0-first handshake (`C0 B0 B0 C0`) plus 4 challenges, in base-r3, d11t-r1 and d11t-r2. d11t-r3's 8/8 is 3 challenges: its B1 intervals were 34.9 and 42.5 s, so a 4th B1 didn't land before the close at 112.4 s. Mean B1 intervals per arm are within 28.5-32.5 s (base 31.0, d11 32.0, d11p 31.6, d11t 32.5, s0 31.9, cold 28.5). The B1 challenge is paced by frames, not seconds. Every B1→B1 interval after boot spans 11981-12032 perf.csv frames in all 16 runs (checker B), so longer intervals (base-r2, d11t-r3) only mean lower fps. d11t-r3's 4th challenge would have come ~60 s after measure_start, after the close. d11t-r3 was already slow in its first interval (341.8 fps vs 421-458 in the other 15 runs). None of this is an arm effect.
- **Clock step in base-r1:** its measure window is 50.007 s by QPC but 58.306 s by the wall clock (+8.30 s). Every other run is within 0.003 s. sys.csv puts the step between rows 103 and 104 (epoch 17:59:39.661 → 17:59:48.949 while t_s advances 0.99 s), inside the measure window. base-r1's game.log uses the wall clock but shows the step only indirectly, because no line falls inside it (17:59:22.752, then `Window closing` at 18:00:01.487). The close comes 121.2 s after the first Toypad write (121.2 − 8.3 = 112.9), vs 111.7-113.5 s in the other warm runs. The frame stats use QPC (window 50.001 s), so they are unaffected.
- **Slow runs' logs show nothing different:** 98/95/98 lines, 40 warnings, no stall lines (checker B's stall-word regex finds 0 hits), Toypad 10/10, 8/8 (d11t-r3: one challenge fewer because of its lower fps, above) and 10/10.

**Perf/threads/GPU (w5_perfthreads v2):**
- **Same work in every frame:** in all 16 runs, every window frame has draw_calls 226, vertices 1022, texture hits 2, pipeline hits 7, 0 cache misses and active_threads 30.
- **Fixed-rate dispatch fit** (fps = frames/window_s; R² 1.000000, max |residual| 0.24/s, 0.2446 in base-r2):
  - intr/s = 9.000 × fps + 1000.4/s;
  - funcs/s = intr/s + 187.5/s (187.50-187.56) in every run.
  - So the higher per-frame funcs/intr in the slow runs (12.83-13.29 vs 12.00-12.56) is the fixed ~1 kHz part spread over fewer frames, not extra work.
  - perf.csv's `fps` column averages instantaneous fps and reads high (e.g. 368.6 vs 277.1 for d11t-r3).
- **The slow runs are slow in every 10-s bin:** base-r2 3.22-3.65 ms, d11t-r3 3.12-3.88, s0-r2 2.95-3.82, vs 2.7-3.0 typical (the first bin is often higher). The last bin is a 1-frame remainder.
- **Metrics where all 3 slow runs fall outside every other run's range:**
  - P-core util 91.4-98.5% vs ≤86.4.
  - E-core effective MHz 551-597 vs ≥609.
  - buffer_queue_depth 3.17-3.52 vs ≤2.96.
  - Main XThread busy 72.5-77.1% vs ≥82.5.
  - XThread F80001A8 53.3-61.9% vs ≤46.7.
  - X144 18.5-19.3% vs ≤16.3.
  - GPU VSync thread 5.3-6.8% vs ≤5.2.
  - `0xc0550001` thread 3.9-6.0% vs ≥6.2.
  - GPU memory util 19.6-20.6% vs ≥22.5.
  - GPU util p90 71-76% vs ≥77.
  - Near-separating: GPU Commands 76.4-84.3% vs 70.3-77.0.
  - Spearman correlation with median frame time: buffer_queue_depth +0.96, GPU Commands +0.93, P util +0.91, X144 +0.91, E MHz −0.91.
  - In the slow runs the game also uses 0.12-0.56 more cores than its arm peers while making fewer frames, and the GPU is less busy.
  - **Reading:** the same work runs slower per CPU-second, which points to CPU placement or contention (P-cores saturated, E-cores at their lowest clocks), not content, bin or arm. s0, base and d11t each had 1 slow run of 3.
- **TimerQueue thread busy, by timer mode:**
  - base, s0 and d11: 39.5-60.5%. d11 (47.5-51.1) matches s0 (46.5-55.4), so host_timer_resolution alone changes nothing.
  - d11t: 4.0-4.5%. d11p: 4.2-5.9%.
  - Game cores: d11t 2.67-2.84 and d11p 2.69-2.78, vs d11 3.16-3.19, s0 3.08-3.38 and base 2.90-3.46. That is about 0.4 cores saved.
  - Frame time is unchanged. Mean ms without the slow runs: d11 2.846, d11t 2.871, d11p 2.899, s0 2.889, base 2.706.
- **Run order and time:**
  - GPU software-thermal throttle (NVML 0x20; gpu.csv matches headroom's count in 15/15 runs) hit 6 runs, all from 18:13 on. Samples of 50: d11t-r2 18, d11p-r2 18, d11-r3 8, d11p-r3 13, base-r3 20, s0-r3 22. grMin was 1410-1650 MHz. The slow runs base-r2 and d11t-r3 had none. base-r3 and s0-r3 throttled most yet are among the fastest runs (355.6/360.0 fps), so the throttle doesn't track frame time.
  - The two earliest runs (cold 17:56, base-r1 17:57) had E-core effective MHz of 1683/1174 and E util of 70.9/51.3%, vs 551-749 MHz and 32-41% later. They were also the fastest (395.8/384.6 fps). So base's mean includes one early-state run; base-r3 alone is 2.812 ms.
- Sent to Agent 8: the main logdiff findings, then this perf/threads update (20:53), then checker B's deltas (21:30).

**Checkers:**
- **A** (`check-1756-a/`, read-only, no HOLD seen): all 4 checks PASS, 0 DISAGREE.
  - Close and crash fields clean in 16/16; STUCK is 0 under a case-insensitive scan.
  - The timer-mode lines match the env, cvars and bins, and there are no other "timer" lines.
  - gate compare on all 27 pairs (s0 x d11/d11t/d11p) gives 0 findings; the normalised and exact diffs show only the timer, Toypad and IoDismount lines.
  - 146 items AGREE.
- **B** (`check-1756-b/`, read-only, no HOLD seen, finished 21:20): 7 AGREE (B1-B6, B8), 1 NOTE (B7), 0 DISAGREE. It used its own scripts (`logcheck.py`, `perfcheck.py`, `bincheck.py`) and reused only `gate_logdiff.compare/scan`.
  - B1: no key separates base from s0 at any normalisation level, and gate gives 0 findings in all 18 ordered pairs.
  - B2: S4a adds no default-on log line, by source and by bin strings (see (b)).
  - B3: cold and warm have the same line sets, and gate is 0 in 6 pairs. It found the pre-log delay in (c).
  - B4: the slow runs show no log-visible difference beyond fps-driven Toypad timing. It found the frame-paced B1 cadence.
  - B5: the +8.30 s step is in base-r1 only (the other 15 runs are within 0.0011 s).
  - B6: the perf-threads.txt spot-check (base-r2, base-r3, d11t-r3; window, mean, median, fps and constancy in all 16) matches.
  - B7: the fit is right, but the max |residual| is 0.2446/s, so 0.24 rather than 0.25 (fixed above).
  - B8: every separation claim holds, including GPU Commands not separating (d11t-r3 76.4 < s0-r1 77.0).


## 14. Finding-10 hangs: gate A check and CP state in gate A, s4b-24 and s4b-20 (task #16 part 1 + follow-ups; 21:30-22:45)

Write-ups:
- `build/agent6/hang/cp-state-gateA.md`
- `build/agent6/hang/cp-state-s4b24-s4b20.md`

Tools (in `build/agent6/hang/`):
- `dumpstacks.py`: stacks from a minidump plus the map.
- `handleinfo.py`: minidump handle stream; event type and state.
- `threadcpu.py`: kernel/user per thread per 2 s.
- `grep_src.py`.

All runs were at BelowNormal, one process at a time.

**Gate A** (Agent 3's `20261122-210906-w6-gateA-p2fcv-level`, p2fc + verify + slow_frame_log_ms=1, vpad L route, -j8 build running):
- Finding 10 confirmed, H1 variant. Same CS 0x84959EDC, same waiter path (Main, sub_82FEB7B8 … sub_83FF2EE8) and same owner callers (sub_83FB33E0+0x2390 → sub_83FBFB30+0x395 → sub_83FBF7D0 → sub_83FAF180 fence poll).
- Sent ~21:52 to Agents 3, 8 and 1. CP-state follow-up sent 22:11.

**s4b-24 / s4b-20** (`hang-31952.dmp`, `hang-13236.dmp`; sent 22:42 to Agents 3, 1, 8, 10 and 12):
- **CP thread:**
  - Same stack in both: `WaitForSingleObjectEx(INFINITE)` on an unnamed auto-reset Event (s4b-20: unsignaled).
  - Call path: rexgpu-xenos +0xC1E70 ← +0xC1570 ← IssueDraw (+0xBA3B0 at +0x1F3B) ← type-3 DRAW case.
  - Gate A was at the same site one step earlier, in the D3D12 submit (~85 % kernel).
- **Source** (snap1 `d3d12/command_processor.cpp`): this is the memexport readback full-path sync.
  - The fast path falls back to `IssueDraw_MemexportReadbackFullPath` when the other slot isn't complete.
  - That calls `AwaitAllQueueOperationsCompletion` → `CheckSubmissionFence(submission_current_)` = EndSubmission, then `WaitForSingleObject(fence_completion_event_, INFINITE)`.
  - Names are inferred; there are no rexgpu-xenos symbols.
  - The CP was not hashing, not doing K-checks, and not waiting on hold_global_lock.
- **(a)** Without verify the CP's kernel time stays at baseline through the stall: s4b-24 3-8 %, s4b-20 5-11 % per 2 s, vs 75-86 % in gate A. Gate A's kernel load comes with verify (VirtualQuery not ruled out). The hang doesn't need verify.
- **(b) Mechanism:**
  - The render thread holds the CS while it polls a GPU fence.
  - The fence passes only after the CP gets through every draw before it, at one submit plus round trip per full-path memexport draw.
  - The detector fires at 5 s.
  - It needs a slow CP: verify, a starved host (all 3 hangs were under the -j8 build), or a huge number of syncs.
  - Without starvation: not shown and not ruled out. W5 and W6 timed runs have no input script, so they never reach the L route.
- **Agent 1 (22:45):** agreed that W6 doesn't test finding 10.
  - After the windows, Agent 3 runs the direct test on the quiet host: two vpad L-route rows with slow_frame_log_ms=1 (s4b-20's set with C1 off, and w6gB's set, p2fc).
  - If either hangs, I read its dump the same way.
  - The write-up went to Agent 11 for FINDINGS, with the full-path sync as a perf candidate after S4 (§6 of the write-up).


## 15. W6 logdiff kit (task #16 part 2; staged and tested 22:39-22:47)

Everything is in `build/agent6/w6/`; see `README.txt` there.

**Morning command** (on Agent 1's word): `build\agent6\w6\RUN-W6-LOGDIFF.cmd build\agent8\matrix\<W6 folder>`
- It runs `w6_kit.py --expect expect-w6.json --ref s0` at below-normal priority and refuses while the HOLD file exists.
- Output goes to `build/agent6/w6/out-<folder>/`: w6-summary.txt, w6-data.json, logdiff/ (w4b_logdiff vs s0) and extra.txt (w4b_extra).
- Runtime is about 1 s.

**Per run:**
- expect-w6.json rules: require/forbid/exact → FAIL.
- STUCK-LOCK episodes with owner site (H1 = sub_83FAF180, H2 = sub_83FB09E8). FAIL only when the stall overlaps the measured window, otherwise NOTE.
- Dumps not named by an episode → FAIL.
- run.json status/exit/close/WER, and cvars/env/bin vs matrix.json → FAIL.
- Agent 11's slow-state math (information only).

**Per arm:** w4b_logdiff vs s0. Gate FAIL findings and NEW error/critical keys → FAIL (except the STUCK episode's own lines). NEW warning, MORE, GONE and unnamed ONLY keys → NOTE.

**Tests:**
- W5 with expect-w5.json: all PASS. 40/0/0, STUCK 0, logdiff 0; the slow numbers equal §13's; 1.3 s.
- Bug fixed: rule texts are now matched number-normalized like the logdiff keys ('1 ms' → '# ms', 'C1' → 'C#').
- W5 with expect-w6.json (negative test): the expected NOTEs, exit 0.
- `test_stuck_parse.py` on the 3 real hang logs: PASS (H1 +0x8 / +0x80 / +0x80, all fields).
- `make_synth.py` synthetic W6 folder, kit exit 1 as designed: STUCK in the window → FAIL; after the window → NOTE; clean → PASS; hang dumps → NOTE; C1 keys named by the rules.
- The wrapper: same W5 result, and usage/exit 2 with no argument.

## 16. Night-window logdiff rules: W9, W5b, W4c (task #19; written and tested 23:00-23:12)

Everything is in `build/agent6/wnight/`; see `README.txt` there. The kit is §15's `w6_kit.py`, unchanged.

**Commands** (on Agent 1's word). Each refuses while the HOLD file exists and takes about 1 s. Output goes to `build/agent6/wnight/out-<W9|W5B|W4C>-<folder>/`.
- `build\agent6\wnight\RUN-W9-LOGDIFF.cmd build\agent8\matrix\<W9 folder>`: expect-w9.json, ref off.
- `build\agent6\wnight\RUN-W5B-LOGDIFF.cmd build\agent8\matrix\<W5b folder>`: expect-w5b.json, ref d11.
- `build\agent6\wnight\RUN-W4C-LOGDIFF.cmd build\agent8\matrix\<W4c folder>`: expect-w4c.json, ref d0.

**Rules.** Arms and cvars come from bench/agent8/run/matrix-window9/5b/4c.json. `cmp_arms.py` shows that W5b's and W4c's arms have the same bin, cvars and env as W5's and W4b's arms of the same name.
- **W9, q0-q500:**
  - exactly one `GPU wait back-off: ON (quantum N us, spin 30 us); stats OFF; GetData hook built.`
  - exactly one line with `GPU wait back-off:`
  - no `GPU wait stats`
- **W9, off:** NO `GPU wait back-off` line. gpu_wait_backoff.cpp L141 prints the init line only when back-off or stats is on. q0 is ON, because ParseUs accepts "0". This deviates from the brief's "each arm's init line once", and it matches matrix-window9's notes.
- **W9, every arm:** `is not a plain number` is forbidden.
- **W9, gate-only arms p1 (s4b17) and q250s (s4b18):** these carry the stats-ON form. `GPU wait stats (5 s):` is required, so STATS lines are named, not NEW.
- **W5b:**
  - The 1 ms line appears exactly once in every arm.
  - The precise-wait line appears exactly once in d11p and never in d11 or d11t.
  - d11t's proof is env_set.
- **W4c:**
  - The boot line is required.
  - Forbidden: timer, precise-wait, C1, S4, slow-frame and GPU wait lines.
  - B must log like d0.
- **Test-only rules:** base/s0 (W5) and d3/d11t (W4b), so the tests cover every run.

**Tests:**
- **W5 with the W5b rules:** exit 0.
  - d11, d11t and d11p PASS.
  - d11p's ONLY line is the precise-wait line.
  - base and s0 get a NOTE because the 1 ms line is GONE vs d11.
  - Same as task #13 (§13), slow state included.
- **W4b with the W4c rules:** exit 1.
  - The only FAIL is 1551-B-r2, valid_timing false (clang++ build processes; known).
  - B, d3 and cold-d0: logdiff 0.
  - d11t's ONLY line is the 1 ms line.
  - Same as task #5 (§12).
- **W9 rules on test-s4b17** (copies: s4b17 = p1, s4b18 = q250s, s4b-01-off = off):
  - Every rule check passes.
  - The FAILs are artifacts: status None ×3, because Agent 3's run.json has no status field.
  - The NOTEs are levels and route artifacts.
  - The env/cvar checks can't be exercised, because Agent 3 stores env under `env`.
- **Negative test:** s4b18 labelled q250 and s4b17 labelled q0 each FAIL 3 rule checks, as designed.
- **Wrapper with no argument:** usage message, exit 2.


## 17. Task #22: wrap-up before the pause (2026-11-23, 05:45-06:50)

**Brief** (Agent 1, 05:45):
1. Dumpstacks on gate B's dump, added to cp-state §7, and a post to Agents 3 and 1.
2. Logdiffs on the 7 night dirs, with a summary in `build/agent6/wnight/RESULTS.md`.
3. `build/agent6/HANDOFF.md`.
4. Optional: #33.

No builds, timed runs or git writes; finish by 12:30.

**(1) Gate B dumpstacks: done 05:50, posted to Agents 3 and 1 at 05:51.**
- Command: `python -B build/agent6/hang/dumpstacks.py build/agent3/runs/20261122-222313-w6-gateB-p2fc-level/hang-38764.dmp build/agent6/hang/dumpstacks-gateB.txt '32624,36920,27760'`. Exit 0 in 0.7 s. The verdict is in `build/agent6/hang/cp-state-s4b24-s4b20.md` §7.3.
- It's the same hang as gate A and s4b-24/20:
  - CS 0x84959EDC;
  - owner XThread9038 (host tid 36920), spinning in sub_83FAF180+0x3F, the L1 fence-wait poll;
  - waiter Main XThread (tid 27760), in RtlEnterCriticalSection.
- **The CP** (tid 32624) was running in the submit half at the dump instant: EndSubmission ← CheckSubmissionFence ← full-path memexport readback ← IssueDraw. Gate A looked the same. s4b-24/20 were caught inside the INFINITE fence wait instead.
- The dump falls inside slow frame #33131 (7979 ms, 2736 memexport syncs, 4836 ms of host-gpu wait), so most of the stall was spent waiting.
- P2 on doesn't avoid the full-path sync.
- GPU-bound vs starved host: answered by Agent 3's quiet-host runs (06:20, then n = 2 per set at 06:59; `build/agent3/f10/RESULTS.md`). 0 of 4 quiet runs hung, against 4 of 6 under -j8 (p = 0.07). For the same GPU work, round trips were 5-30x faster, so it's a starved host. The margin is small (2.89 s worst vs the 5 s detector). Total syncs depend on timing, not load. See cp-state §7.4-§7.5.

**(2) Night logdiffs: done 05:30-06:05.** The full summary is `build/agent6/wnight/RESULTS.md`.
- **Totals:** 7 dirs, 135 runs, and all 7 wrappers exited 0, so no FAIL. 0 STUCK-LOCK and 0 dumps. Levels are 40/0/0 everywhere except one run at 41/0/0.
- **ONLY keys:** only the switch proof lines: p2fc's 3 C1 keep-watch lines, the q-arm back-off init line and d11p's precise-wait line.
- **6 runs (on 5 arms) miss `Execution complete`.** It's a race between `module_thread_`'s log line and `OnClosing`'s `_Exit(0)` (rex_app.cpp:634-641 vs :693-707). Benign; NOTE only.
- **W9 `0128-off-r2`:** the 3 s shutdown watchdog fired, logging `Shutdown wedged past the close request; hard-exiting.` (legodimensions_app.h:407-428).
  - `OnClosing` didn't run within 3 s of WM_CLOSE.
  - Exit 0, timing valid. It's the first sighting in 135 runs.
  - Back-off isn't the cause: it's the off arm.
- **W9 env/quantum proof (new):** `build/agent6/wnight/w9_envcheck.py` → `w9-envcheck.txt`: 42 of 42 runs OK. The negative test `make_test_w9env.py` gives 9/9.

**(3) Handoff:** `build/agent6/HANDOFF.md`.

**#33 (pop-in as an opt-in, default OFF): staged 06:42 and reviewed 06:46. Not built and not applied.** The files are in `build/agent6/s33-popin/`: `DESIGN.md`, `s33-popin.patch` and `CHECK.txt`.
- **The cvar:** `d3d12_pipeline_creation_no_wait` (bool, default false, `kRequiresRestart`).
  - It's latched in `PipelineCache::Initialize`, and takes effect only when `async_shader_compilation`, the creation threads and bindless are all on.
  - It logs an INFO line when it takes effect and a WARN line when it's set but ignored.
- **ON:**
  - EndSubmission stops waiting for pipelines that are still being created, and their draws stay skipped until ready.
  - Memexport and in-query draws still force the wait, through `AwaitPipelineCreation()`, which is the old EndSubmission block moved out.
- **The patch:** 4 files, 10 hunks, +105/-24. Hunk #5 (`CanEndSubmissionImmediately`) is optional.
  - With the cvar OFF the path is unchanged, apart from 3 new slow-frame fields: `dropped draws {} | forced pipeline waits {:.1f} ({}x)`. The line then has 28 placeholders for 28 args.
- **Apply check:** `git apply --check --verbose` on rexglue-sdk 5350b1d exited 0 with no offsets. The subagent ran it at 06:31 and I re-ran it at 06:45; the tree stayed clean.
- **Main risk:** EDRAM resolve sources aren't guarded, so the gate is the user's review on a visible desktop (DESIGN.md §8 row 3). The test plan and the logdiff expect rules are in DESIGN.md §8.
- **How it differs from §10.3:**
  - the cvar name (§10 had `d3d12_async_pipeline_no_wait`);
  - the `ShutdownShaderStorage` wait runs only with ON;
  - memexport and query draws force a wait, where §10.3 only listed them as a risk.
- **Rated by Agent 10 at 07:36** (`build/agent10/t27/r33-popin.md`): OFF SAFE, ON SAFE-IF, no blocker.
  - S1: build the first bin without hunk #5. S2: run diagnostic (d) before any recommendation; it is now DESIGN.md §9 precondition 5. N1-N3 are notes for the next patch edit, the build and the read-out.
  - Docs only, per Agent 1 (07:38): the rated patch (0D230244…) is unchanged. A no-#5 copy I staged at 07:37 passed `git apply --check`, and I withdrew it at 07:40.
  - The dated rating block is DESIGN.md §10.
