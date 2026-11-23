# #32 warm-boot fix: run spec for a6 §10.2 runs 2-4, plus the optional threads=1 run (Agent 6, task #8, 13:15)

This is for Agent 3, who launches every game until 14:20. Agent 6 reads the results (read-only). Every run is FUNCTIONAL ONLY (hidden desktop). Run 1, the cold regression run, is Agent 3's own devoff4 OFF cold run and isn't listed here.

## Bins and seed
- **F = fixed:** devoff4, Agent 2's new bin folder `build\agent2\devoff4-bin` (name confirmed by Agent 1 at 13:30). Its `pipeline_cache.cpp` passed the one-line check at 13:31 (`linecheck-1331.txt`).
- **U = unfixed:** `build\agent2\devoff3-bin` (exe 02:43:57). Its `rexgpu-xenos.dll` contains `d3d12_pipeline_creation_threads` (checked 13:10).
- **Seed:** `build\agent3\seed\devoff2-214` (xsh 160,232 B; xpso 15,420 B = 214 pipelines). Every run below passes `-SeedXenos` and gets its own fresh run dir. That is the harness default; never reuse a user dir.
- The thread cvar goes on the command line with `-Arg`, as in S11 arm B (§11.1). The toml isn't touched.

## Runs (in priority order)
Prefix for every row: `powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1`

| id | a6 §10.2 run | arguments after the prefix | ~min |
|---|---|---|---|
| U4 | 4, unfixed | `-BinDir build\agent2\devoff3-bin -Seconds 90 -Tag s102-r4-t0-devoff3 -Arg 'd3d12_pipeline_creation_threads=0' -SeedXenos build\agent3\seed\devoff2-214` | 2.5 |
| U2 | 2, unfixed | `-BinDir build\agent2\devoff3-bin -Seconds 360 -GpuLog -Tag s102-r2-warm-devoff3 -InputScript harness\routes\attract-long.txt -SeedXenos build\agent3\seed\devoff2-214` | 7 |
| F4 | 4, fixed | `-BinDir build\agent2\devoff4-bin -Seconds 90 -Tag s102-r4-t0-devoff4 -Arg 'd3d12_pipeline_creation_threads=0' -SeedXenos build\agent3\seed\devoff2-214` | 2.5 |
| F3a, F3b | 3, boots 1-2 | `-BinDir build\agent2\devoff4-bin -Seconds 60 -Tag s102-r3-boot-devoff4 -SeedXenos build\agent3\seed\devoff2-214` | 2 each |
| F2 | 2, fixed (also boot 3 of run 3) | `-BinDir build\agent2\devoff4-bin -Seconds 360 -GpuLog -Tag s102-r2-warm-devoff4 -InputScript harness\routes\attract-long.txt -SeedXenos build\agent3\seed\devoff2-214` | 7 |
| F3c, F3d | 3, boots 4-5 | same as F3a | 2 each |
| F1t | optional: threads=1 | `-BinDir build\agent2\devoff4-bin -Seconds 60 -Tag s102-t1-devoff4 -Arg 'd3d12_pipeline_creation_threads=1' -SeedXenos build\agent3\seed\devoff2-214` | 2 |

**Order**
- U4 and U2 don't need devoff4, so they can run in any gap before it's ready.
- If you can, run U4 right next to F4 so both see the same machine load. The run-4 ratio is the only ms comparison. If they can't be adjacent, note what else was running (e.g. Agent 2's build).
- After devoff4 is ready, run 1 goes wherever Agent 3 wants it. Then: F4, F3a, F3b, F2, F3c, F3d, F1t.
- The last launch is at 14:45 (Agent 1, 13:56; it was 14:15). Anything left over waits until after W4b.
- **The minimum for a hang verdict** is F4 plus two default-thread boots (F3a and F3b).
- If U2 can't run, the 05:29 run `build\agent3\runs\20261122-052901-attract-devoff3-warm` stands in as the unfixed reference. It used the same command, but on a saturated machine.
- U2 and F2 copy the 05:29 command exactly, including `-GpuLog`.

**Collect:** leave the run dirs as they are, dumps included, and send Agent 6 the run dir names plus any run-game exit code other than 0. Nothing else is needed.

## What Agent 6 checks (read-only, `build\agent6\s10-2\s102_read.py`)

**Validity (every run)**
- The seed copies match the seed's sha256 (run.json `seed_xenos`).
- game.log has `Translated 229 shaders from the storage in X milliseconds` and `Created 214 graphics pipelines (not including reading the descriptions) from the storage in X milliseconds`.
- Other counts or missing lines mean the seed was rejected. That makes the run invalid; it isn't a failure of the fix.

**Hang (every run)**
- Measure the gap from `Initializing shader storage for title 5752084B...` to the next guest line, `SetInterruptCallback(…)`. Expected: Translated + Created + < 1 s. The 05:29 reference is 2.40 s for 85 + 2,016 ms.
- A gap over Created + 5 s is a hang suspect.
- Exit: WM_CLOSE, exit code 0, `Title terminated; hard-exiting process.`, no dump, no crash event.
- The fix runs the never-run block at `pipeline_cache.cpp:685-715`. At default threads it shuts down from index 9, joins 2 temporary threads, then waits for the busy regular threads. With threads=0 it shuts down from 0, joins 11, and has no wait. With threads=1 it shuts down from 1 and joins 10.

**Run 2 (F2 vs U2)**
- The same log lines apart from the value in "Created … in X ms" (Agent 10). Check with `python build\agent10\bgate\logdiff.py --base <U2> --cand <F2> --min-level warning`: NEW 0 / MORE 0 / GONE 0 / no marker. logdiff normalizes numbers, so the Created key matches.
- Differences that run 1 also shows between cold devoff4 and devoff3 come from the other S4a items (#7, #8, #5, #38, all OFF) and don't count against #32.
- Both storage lines appear with the same N.
- The pipeline-miss totals and the xpso growth are similar. The 05:29 reference has pm 56 and xpso +4,032 B = 56 pipelines.
- Info only:
  - the max frame time over the first 30 frames;
  - STUCK-LOCK episodes (pre-existing and load-dependent; `agent6-hang-triage.md`).

**Run 4 (F4 vs U4): the positive control that the fix is active**
- U4 creates all 214 pipelines one after another on one thread. F4 uses 11 temporary threads.
- So U4's Created time should be several times F4's, and F4's should be close to a default-thread boot (~2 s).
- F4's first frame (summary.txt "frames first written") should also come earlier than U4's.
- F4 may show the host shader-compile notice during boot. That is host UI only and isn't captured on the hidden desktop.

**F1t:** the Created time is close to the default-thread value, with a clean exit.

> **Correction to a6 §10.2 run 2 (and b2r §27 L1483).** "The fixed Created time is ≥ the unfixed one" isn't a reliable pass criterion. The fix adds the in-flight tail of ≤ 9 pipelines, about one creation time. It also adds 2 workers: 12 counting the GPU thread's drain, against 10. So the value can come out either way, and at default threads it is **info only**. The fix's visible effect is at threads=0 (run 4). At the default thread count the tail finishes long before the first frame: storage is done by ~6 s, the first frame comes at ~18 s, so no first-frame spike is expected in either arm.

The run-4 ratio is the only ms comparison. Everything else is functional, so record the machine load and don't read the ms as timing.
