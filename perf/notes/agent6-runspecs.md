# Agent 6 run specs for Agent 8's runner: PSO stutter (task #5)

Written 19:58 for `bench/agent8/run/run-timing.ps1` and the user-started matrix. Owner: Agent 6. Code: Batch 1 in [agent6-pipelines.md](agent6-pipelines.md).

## Preconditions

- **Native ON build only.** The PSO counters exist only in `LEGODIMENSIONS_NATIVE_GPU=ON` builds. The OFF baseline (emulated Xenos) has no PSO path and no counters, so task #5 has nothing to run on it.
- **Bin dir:** Agent 2's native ON staging dir (about 21:30). Below it is written `<native-bin>`.
- **Content.** The first native build has stub runtime shaders and a stub temporal bank ([agent6-native-aot.md](agent6-native-aot.md) §6), so some draws are missing. The counters are still valid, because they count real driver work. Repeat P1 and P2 after the capture rebuild.
- **Hidden desktop.** Compile counts and compile milliseconds from agent-launched runs are valid, because they are CPU and driver work. Frame times from those runs are not. Agent 8 may run P1 and P2 on the hidden desktop right after the native build as a functional check of the counters. The timing versions come from the user-started runner.

## One runner change needed: `-SeedCache <dir>`

The runner mirrors only the files listed in `MANIFEST.txt` into a fresh run dir. Every run therefore starts with an empty PSO cache in `<run>\cache\`. That gives P1 for free, but P2 and P4 need a cache from an earlier run.

The PSO cache files are:
- `<exe dir>\cache\native-pso.bin`: the driver library blob, specific to the adapter and driver.
- `<exe dir>\cache\native-pso-recipes.bin`: portable recipes.

The game writes both at a clean exit (`Stop()` calls `Save()`) and after 3 s without new PSOs.

Requested options (Agent 8 owns the runner):
- `-SeedCache <dir>`: after `New-RunDir`, create `<run>\cache\` and copy `native-pso.bin` and `native-pso-recipes.bin` from `<dir>` (whichever exist).
- `-SeedRecipesOnly`: copy only `native-pso-recipes.bin`.

A seed dir is just an earlier run's `<run>\cache\`.

## Matrix

Every run uses `-BinDir <native-bin> -Warmup 60 -Seconds 180`. Every run sets `-Env 'LEGO_NATIVE_PSO_STATS=1;LEGO_NATIVE_PSO_STATS_INTERVAL=10'` (written ENV below), plus any extras. Lists in `-Env` are separated with `;`.

| ID | `-Tag` | Purpose | Extra `-Env` | Seed |
|---|---|---|---|---|
| P1 | `pso-cold` | First run after install or a driver update: empty cache | none | none (the fresh run dir is cold) |
| P2 | `pso-warm` | Second run, same content | none | `-SeedCache <P1 run>\cache` |
| P3 | `pso-nocache` | Control with the cache off: no load, no save | `;LEGO_NATIVE_PSO_CACHE=0` | none |
| P4a | `pso-prep1` | Driver-update model: recipes but no blob, so startup recompiles every recipe. Serial. | `;LEGO_NATIVE_PSO_PREPARE_THREADS=1` | `-SeedCache <P2 run>\cache -SeedRecipesOnly` |
| P4b | `pso-prep4` | Same, startup on 4 threads | `;LEGO_NATIVE_PSO_PREPARE_THREADS=4` | same as P4a |
| P5 | `pso-async` | Async compile with skip-draw. Batch 2, and only after Agent 4 lands the draw.cpp hooks. | `;LEGO_NATIVE_PSO_ASYNC=1` | none (cold, like P1) |

- **Order:** P1, P2, P3, P4a, P4b. P5 comes later.
- **Time:** about 4-5 min per run including boot, so about 25 min in total.
- **Observer cost:** stats ON cost about 95 ns per present and about 190 ns per lookup (`build/agent6/bench/stats_off_cost.txt`). That is noise next to a frame, and every run in the matrix has stats on, so the comparisons stay fair.

## What to collect (all from `game.log`, plus the runner's perf.csv summary)

| Pattern | When | Content |
|---|---|---|
| `Native GPU PSO stats, last 10 s:` | every 10 s | frames, fps, worst ms, hitches (50 ms or more), compile frames (4 ms or more of blocking compiles), compiles, compile ms (blocking ms), misses, hits, skipped draws |
| `Native GPU PSO stats (exit)` through `PSO frames:` | at exit | Full summary: startup cache, startup preparation, lookups, compiles with a histogram, compiles by thread, auxiliary, saves, async, frames |
| `PSO minute` | at exit | One row per minute since the first frame, with the same columns as the 10 s line. This is the table for "FPS improves the longer you play". |
| `Native GPU: startup pipelines loaded= compiled= failed= resident= elapsed_ms=` | startup | Existing line, used for P4 |
| `Native GPU: pipeline cache hits= misses= stored= saves=` | exit | Existing line |
| `Native GPU: pipeline cache saved, <n> new pipelines, <bytes> bytes` | each save | Existing line. It proves the seed for P2 was written. |

> [!IMPORTANT]
> **Exit caveat (found 21:53).** The three "at exit" rows above will usually be missing.
> - In NATIVE_GPU builds, `WM_CLOSE` arms a watchdog that calls `TerminateProcess` 250 ms later (`legodimensions_app.h:409-419`). The Quit Game dialog terminates at once (`native_process_exit.h`).
> - `StopPipelineLibrary` logs the exit summary only after the final save, so it rarely runs before the watchdog fires.
>
> **Runner:** right after the measurement window, do the following (a `-Driver` script works too):
> 1. Create `<run>\cache\` if it is missing. The exact trigger path is printed in the startup line `PSO stats on`.
> 2. Create an empty `<run>\cache\pso-stats.now`.
> 3. Wait about 5 s, until `Native GPU PSO stats (pso-stats.now)` appears in `game.log`.
> 4. Send `WM_CLOSE`.
>
> That summary has the same lines as the exit summary, including the `PSO minute` table. Without it, sum the 10 s lines.
>
> A kill never corrupts the cache, because saves write a temp file and then rename it. The seed for P2 is P1's last idle autosave (written after 3 s without new PSOs).

## How to read the results

**P1 vs P2: is PSO compilation behind the symptom?**
- **If it is:**
  - `PSO compiles` is much higher in P1 than in P2.
  - In P1, the `PSO minute` rows bunch `comp` and `cfrm` into the first minutes and then decay.
  - In P2, `comp` is close to 0 and `hits` is high.
  - The runner's p99.9, max and >100 ms counts fall in P2.
- **If P2 still hitches without compiles,** the stutter source is not PSO creation. Look at the "Native slow draw" lines and Agent 8's profile instead.

**P3 vs P1.** Both should have about the same compile count. That confirms P2's drop comes from the persistent cache.

**P4a vs P4b.**
- Compare `PSO startup preparation: ... threads N, X ms` and `elapsed_ms=`. The time should fall, up to about 4x if the driver compiles in parallel.
- The `loaded/compiled/failed/resident` counts must be equal in both. That is the behaviour-identity check for the threads toggle.

**P5 vs P1.**
- `PSO async: posted/ready/skipped draws` is non-zero.
- `PSO compiles by thread` moves to `async`, and `cfrm` falls.
- Expect a few frames of missing geometry for each new PSO. This is a visual check only, so the user should look.

## Optional manual version (the user plays): first visit vs second visit in one session

Use P1's settings with an empty cache:
1. Enter a level and play 3 min.
2. Leave to the hub.
3. Re-enter the same level and play 3 min.

At each transition, create an empty file `<run>\cache\pso-stats.now`. That logs a full summary within 2 s and is then deleted. Alternatively, note the wall time and use the 10 s lines.

Expect the second visit to have almost no compiles even without the disk cache, because the in-memory pipeline map keeps them. Compare its hitch counts with the first visit.
