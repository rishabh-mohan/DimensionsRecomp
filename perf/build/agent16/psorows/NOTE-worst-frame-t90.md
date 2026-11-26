# Worst frame at t≈90-100 s (rows run 20261126-004331): note

Static read of the existing frames.csv and game.log files. No runs were made for this note.

## Facts (frames.csv; t = sum of interval_ms)

| arm | worst ms | t s | next frame ms | next pipeline_creation_ms |
|---|---|---|---|---|
| s0-ref-cold | 334.9 | 91.3 | 108.4 | 19.4 |
| c-pso-t1 | 345.0 | 97.6 | 108.7 | 19.8 |
| c-pso-unl | 350.5 | 96.9 | 103.3 | 18.8 |
| w-ref-t1 | 405.7 | 103.2 | 108.7 | 0.49 |
| w-pso-t1 | 345.1 | 96.8 | 78.9 | 0.37 |
| w-ref-t4 | 329.6 | 96.7 | 74.1 | 0.38 |
| w-pso-t2 | 343.8 | 96.8 | 78.1 | 0.38 |
| w-pso-t4 | 345.1 | 96.9 | 86.3 | 0.43 |
| w-pso-unl | 354.2 | 97.4 | 87.1 | 0.43 |

The frame sequence is the same in all 9 arms:
- 41-draw frames at ~5 ms;
- **one 1-draw frame of 330-406 ms**;
- one 59-draw frame with 29 pipeline creations, 74-109 ms;
- a 57-draw frame with 4 creations, 10-19 ms;
- then normal frames.

**This is a scene switch.** In s0, game.log shows the first `BeginTiling ... 1280x720` at 00:45:15.90, at the stall. In the same burst it adopts new textures, including a 4096x4096 and a 1024x1024. It also adopts new VS/PS (8C7CC85B742E60EF / 95F766C384B236CB, D9617D6536D12E0D / ED1814082814AA81). In every arm, the first 1280x720 tiling falls at ~97-103 s after launch.

## What the counters say about the stall frame

- pipeline_creations 1 at 0.04 ms.
- sync_ms 0; frame_slot_wait 2 calls at 0 ms; present/swap CPU time 0.4-0.8 ms.
- callbacks 8/24/5 (enqueued/executed/pending), the same as the neighbouring frames, so there is no fence or callback wait.
- `detailed_timing_enabled = 0`, so texture_ms, bindings, issue and similar are **not measured** (they read 0). frames.csv cannot attribute the time inside the frame.

So nothing the renderer measures is slow. The ~330 ms is most likely the guest's own synchronous scene load on the CPU side between two presents. It is **not PSO**: cold, warm, t1/t2/t4 and unl all match within noise. The w-ref-t1 outlier at 406 ms is a single run.

## Follow-up frame: the one place where PSO does matter

- Cold arms: ~105 ms, of which pipeline_creation_ms is ~19 ms.
- Warm arms: 74-87 ms with pipeline_creation_ms ~0.4 ms. The exception is w-ref-t1 at 108.7 ms.
- The cache removes the ~19 ms of creation. The remaining ~70-85 ms is unmeasured; it is probably the new-texture adoption and upload (4096², 1024² and others), but timing was off.

## Leads from the logs (correlation only)

- In s0, from 00:45:14.57 to 00:45:14.79 (just before the switch), guest thread t41200 logged 128 `CPU pool copy` moves, 4-8 KB each, ~1 MB in total.
  - All are tagged `VS=A58EBA123EFB541C`, which is the excluded memexport root VS (lr 82BD2B44, caller 82B5819C).
  - The logs alone can't show whether this is on the stall's critical path.
- The s0 110 ms frame I flagged earlier: the PSO stats window 00:45:04.65-00:45:14.66 has "worst 110.1 ms, 1 compile frame, 25 compiles (20 ms blocking)".
  - That window opens after the app closures (00:44:30-00:45:00) had ended.
  - So it is s0's cold compile, **not** the closures. This corrects my report, which said it might be either.
- Second-worst frames:
  - 230-263 ms at t≈276 s (61 draws, 10 creations) in 7 arms;
  - 268 ms at t≈136-142 s (5859 draws, 93 creations; a cold compile burst) in s0 and c-pso-t1.

## Addendum: xenos vs native, from the existing window 20261125-1804 (cap 60, attract-long)

The window's raw frame files cover the whole run from launch: perf.csv (frame_time_us) for ship60, native-frames.csv for nat60/n4bp60. All of them contain the same scene switch:

| arm (window runs) | stall frame | t (frame clock) | next frame |
|---|---|---|---|
| ship60 xenos (cold, r1-r4) | 368 / 278 / 231 / 229 / 220 ms (draws 644 > **219** > 768) | 104.7 / 91.3 / 81.2 / 81.3 / 81.3 s | 126 / 125 / 88 / 82 / 87 ms |
| nat60 (cold, r1-r4) | 375 / 285 / 220 / 209 / 201 ms (41 > **1** > 61) | 82-86 s | 162 / 152 / 121 / 100 / 95 ms |
| n4bp60 (cold, r1-r4) | 446 / 215 / 231 / 228 / 196 ms (41 > **1** > 59) | 81.5-83.8 s | 136 / 90 / 93 / 131 / 89 ms |

**Xenos shows the same ~220-280 ms stall plus an ~85-125 ms follow-up at the same switch** (warm runs). Next-step 3 below is therefore answered from existing data:
- The stall is the game's own scene load, not the native renderer.
- At cap 60, native is the same as xenos or slightly shorter (warm medians: xenos ~230 ms; native ~205-230 ms).

**Coverage by the NATCMP arms.** They run the same route and frame logging, so the switch will be in every run's raw files. It falls inside the 90 s warmup, though, so it is not in the 3D score window. A per-run "switch stall" line in the read-out would need either a cmp_post change (a re-rate) or a separate read-only script over the run dirs after the run. I suggest the separate script.

## Suggested next steps (none run; Overseer's call)

1. One attract run with frames.csv detailed timing on (`detailed_timing_enabled = 1`), to split the follow-up frame into texture, bindings and issue time and confirm whether the stall frame really has no renderer time.
2. A CPU sampling profile (ETW/WPR) over t≈85-105 s, to see which guest function holds the main thread during the 1-draw frame.
3. If the stall is guest load I/O, compare it with the xenos (devfinal2) run at the same scene switch. If xenos shows the same ~330 ms, it is the game itself and not the native renderer.
