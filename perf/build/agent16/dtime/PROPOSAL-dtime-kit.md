# Proposal: small detailed-timing kit (RUN-DTIME), diagnostic only

Goal: attribute the scene-switch frames on the attract-long route (see psorows\NOTE-worst-frame-t90.md, sha 9B9C8B3E):
- the 1-draw stall frame, 330-406 ms uncapped;
- the follow-up frame, 74-109 ms with 59 draws and 29 pipeline creations.

This is a DIAGNOSTIC run: its numbers are never scored as timing.

## Switches (found by a read-only search of DimensionsRecomp/rexlego)

- **`LEGO_NATIVE_TIMING`** (any non-empty value): `NativeTextureTimingEnabled()`, rexlego/src/gpu_native/textures.cpp:1531.
  - It sets `detailed_timing_enabled=1` in frames.csv (device.cpp ~L2311 header, L1889 present path).
  - It fills texture_ms, bindings/begin/pipeline/issue/tail_ms, constants_*, sync_*, frame_slot_wait_ms, acquire/present_submit_cpu_ms.
  - It also logs `Native timing: frame=... interval=...` plus the draw, constants, buffer and sync timing lines for frames over 40 ms (the first 16, then every 30th).
  - Agent 8's tier2 matrix note: it "turns on texture timing, which perturbs frame times: DIAGNOSTIC ONLY".
- **`LEGO_NATIVE_SLOW_OPERATIONS=1`**: rexlego/src/gpu_native/slow_operation.h.
  - It logs `Native slow CPU operation: <label> total_ms=... <phase>=...` for operations of 4 ms or more.
  - It is capped at the **first 128** such operations, and boot may use up the budget before t≈97 s. That's why it gets its own arm.
- Both are passed with `harness\run-game.ps1 -Env "NAME=v;..."`. run-game already sets LEGO_NATIVE_FRAME_METRICS.

## Kit shape (copies the RUN-PSO-ROWS / psorows pattern; no new mechanisms)

- `build\agent16\dtime\RUN-DTIME.cmd`, saved as CRLF.
  - Fail-closed pins: count PINOK and require the exact number before launch.
  - It pins: run-game.ps1, the route attract-long.txt, the native4bp-bin MANIFEST (C5181520…A690, verify-bins 0 FAIL), the kit ps1 and the post script.
  - Modes: `dryrun` (default when no argument is given) and `run`. It refuses to run off the interactive desktop.
  - The D1 strings never appear.
- Bin: `build/agent16/pack/native4bp-bin`, used read-only. run-game mirrors it into the run dir by hard links, as psorows does. There is no PSO cache copy, so every arm runs cold (same as s0-ref-cold).
- Arms: attract-long, 150 s each, uncapped (the same settings as the psorows runs, so they compare with their 330-406 ms):
  1. `d-timing`: `LEGO_NATIVE_TIMING=1`
  2. `d-slowops`: `LEGO_NATIVE_SLOW_OPERATIONS=1`
  3. Optional `d-both`, if the slow-op budget survives boot in arm 2.
- Run length: about 2 × (150 s + boot and close) ≈ 7 min, plus a 10 s cooldown between arms.
- `dtime_post.py` (read-only over the run dirs):
  - finds the switch: the largest interval at t 70-115 s with the draw step 41 > 1 > 59;
  - prints every frames.csv column for frames -2..+4 around it;
  - lists the `Native timing` and `Native slow CPU operation` lines whose game.log timestamps fall within ±1.5 s of the switch;
  - flags the "switch" as found or not found; a selftest runs on synthetic rows.
  - Output: post\dtime-<stamp>.txt plus SHA256SUMS.
- Dryrun checks:
  - pins and verify-bins;
  - run-game -DryRun for each arm;
  - post selftest;
  - a check that native4bp's legodimensions.exe contains the strings `LEGO_NATIVE_TIMING` and `LEGO_NATIVE_SLOW_OPERATIONS`, which shows the pinned bin has both switches. This is one read of the 170 MB exe, done in the dryrun slot only.

## What it answers

- Whether the 1-draw stall frame has any renderer-side time once timing is on. If it doesn't, the stall is the guest's own load: confirmed, with xenos showing the same stall in the window.
- How the ~70-85 ms of the follow-up frame left after pipeline creation splits between texture upload, bindings, issue and sync, and which slow-op label and phase dominates (for example texture-upload stages).

## Not in scope

- No change to any rated kit (natcmp, psorows, the window).
- No xenos arm: the window already covers it.
- No WPR/ETW profiling: that would be a separate request.

Needs: Overseer OK to build it (static), then an M10 rating, a dryrun slot, and a run slot.
