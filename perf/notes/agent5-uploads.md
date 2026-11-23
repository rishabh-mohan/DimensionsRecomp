# Agent 5: native renderer texture, buffer, vertex and index uploads (task #4)

> **RESUME (session 3, task #20, updated 06:31). Status: DONE. The S4 entry is written (below), the summary went to Agent 1 at 06:11 (Agent 1, 06:14: "#20 is good"), u is defined once (S4.8), Agent 8 ran a-vol (06:20-06:24) and its numbers are in S4.8, and `@@done 20` went to Agent 1 at 06:31. Nothing of mine is running.**
> - **Task #20 (Agent 1, ~05:00):** S4, the memcpy on the devoff GPU Commands thread. Analysis only: read-only on source trees, no builds, no game runs, at most 2 threads, at most 1 subagent (none used), notes only from 08:30. Files: `bench/agent5/**`, `build/agent5/**`, this file. Deliverables: the callers; bytes per frame and whether all of it is needed; ranked proposals (ms/f, output-identical argument, files, risk, default OFF, test plan, what Agent 10 rates); a 6-10 line summary to Agent 1 by ~07:00, then `@@done 20`.
> - **Later rules from Agent 1:** `clear_memory_page_state` stays as it is (05:31). One combined S4 entry with Agent 12's #21, written by me, savings counted once: C1 = Agent 12's P1 (05:45, 05:58). Agent 12 prepares, but doesn't build, the logging-only diagnostic for u: don't duplicate it. Show both sides of C1 (the saving and the write-fault cost if u is low). Send C1 to Agent 10 for an output-identical rating. While a game runs: targeted single-file reads only; 06:33-07:15: 1 thread, no recursive searches, no builds, batch tool calls.
> - **New files:** `bench/agent5/s4_slowframe.py` (parses the ReportSlowFrame lines; `--selftest` OK) and `bench/agent5/matrix-s4-invalvol.json` (sha256 9D6A6F2C9C018293BD399FBA0F0E3EFCBB1E995661B662AD49F211FD00055A0B; one arm, a-vol; `-PlanOnly` exit 0, 1 run, about 5 min, bin ok). Agent 1's GO (05:58): priority 2 in Agent 8's 06:33-07:15 slot, functional only, if it fits, and only after Agent 12 confirms the parser reports invalidations per frame (asked 06:05; confirmed 06:16, "exactly my metric"; my OK went to Agent 8 at 06:19 with the full sha256).
> - **Corrections (sent 05:39):** my 05:22 claim that `clear_memory_page_state` causes the re-uploads was wrong (it is false in the run toml), and Agent 6's fixture-slowframe logs are synthetic, so they are no evidence. Both were retracted to Agents 1 and 12.
> - **a-vol (06:20-06:24, `build/agent8/matrix/20261122-0620/runs/0620-a-vol-r1`):** 1.87 invalidations and 3847 KB per frame (p50 2 and 3848 KB), almost all from one 3844 KB buffer locked whole about once per frame, plus 4 KB events. Not falsified, but the count is below Agent 12's 5-15; F_max 16.9. Details in S4.8. `s4_slowframe.py` now reads rotated logs. Also done since the summary: u is defined once, in S4.8, as in Agent 12's diagnostic (Agent 1's fix, 06:14); `bench/agent5/matrix-native-uploads-x5.json` is written (a new file, sha256 62F58F2B...; `-PlanOnly` 11 runs, about 28 min; not run tonight, Agent 1 06:14; uploads-45 114A0242 unchanged), see "x5 uploads matrix" at the end of this file.
> - Details: "Session 3, task #20" at the end of this file.
>
> **RESUME (session 3, task #15, updated 04:12). Status: DONE. The user-window matrix, the load-phase script and the hand-off to Agents 8 and 1 are done. Nothing of mine is running.**
> - **Task #15 (Agent 1, 03:07):** make the uploads matrix worth a user window. Planning only: no game runs, no builds, at most 2 threads, no subagents. Files: `bench/agent5/**` and this file.
> - **Done (03:07-03:40):**
>   - `bench/agent5/matrix-native-uploads-45.json` (sha256 114A024244C75EC956D12B170511CCA2B5BEBB437C449432EB4617E9EE6FBD02): u0/u1/u2 x5 with 60 s windows plus the cold u0, 16 runs. `-PlanOnly` (03:36): exit 0, about 41 min, no matrix errors, bin ok, warm-up 10 s not raised. Its three arms are byte-identical to the original's u0/u1/u2.
>   - **sys_csv (03:56; Agent 8 asked, Agent 1 OK'd at 03:55):** the matrix got `"sys_csv": true` (after `min_window_after_ff_s`) and one sentence at the end of its QUIET MACHINE note, so every run logs sys.csv and sys.json and gets disturbance flags (input, foreground loss, screensaver, power). Nothing else changed. The sha256 above is the new file; the old one was C59DB350... (Agent 8's first staged copy, without sys.csv). Checks: byte-identical to the checked scratch copy, JSON parses, LF, ASCII, no BOM; `-PlanOnly` on the repo file (03:56): exit 0, sys.csv ON, 16 runs (1 cold), about 41 min, bin ok, no SKIP. Agent 8 re-copied it (04:11): its staged copy `bench/agent8/run/matrix-native-uploads-45.json` matches (114A0242..., checked), and its own `-PlanOnly` agrees (16 runs, about 41 min, sys.csv ON). The s-rows still come from the 15BB7822 file (hash checked by Agent 8), ETA about 04:35-04:55, after Agent 2's nativeB build.
>   - `bench/agent5/load_phase.py` scores the first 60 s after the first frame. It was tested on window 3's n0 runs, verify3b, S3 n1-n3 and 0256-native3; the outputs are `bench/agent5/load-phase-test.{md,csv,json}`.
>   - The original `bench/agent5/matrix-native-uploads.json` is unchanged (15BB7822...). Its s-rows are final, and Agent 8 runs them tonight in its own slot with `-Only s0,s1,s2`.
>   - Details: "Session 3, task #15" at the end of this file.
> - The task #4 block below is kept for reference.
>
> **RESUME (session 3, updated 03:06; task #4 re-issued at the S3 relaunch, 02:01). Status: DONE at 03:06. The matrix points at native3 and went to Agent 8 for a later window (not window 4). Nothing of mine is running.**
> - **Done (03:02-03:06).** Gates passed: Agent 8's boot PASS (`build/agent8/runs/0256-native3`), Agent 7's check A-D PASS, and Agent 1's GO (03:02).
>   - All 6 `bin` fields point at `build/agent2/native3-bin`. The BIN DIR note names its exe (7F7F8586D219465C), MANIFEST (B50FE8D4A16565DA) and fingerprint (8f849b69907d4006).
>   - Notes updated for Agent 8's runner of 02:53:
>     - Its 60 s floor (`min_window_after_ff_s`, default 60) is met exactly by settle 50 + warm-up 10, so no warm-up is raised.
>     - New run sizes.
>     - Agent 8's boot run had no cvars and logged `native_fps_limit_cvar` 240 in all 13642 rows, so that column does show the cap in force.
>     - Agent 1: run it in a later window, not window 4.
>   - Checks:
>     - The JSON parses (6 arms, 11 notes). LF, ASCII only, no BOM, no placeholder left. The only `native_settings_frontend=false` is in the note that says no arm sets it.
>     - `-PlanOnly` (03:04): exit 0, no SKIP, no errors or warnings, bin `ok (MANIFEST.txt)`, warm-up 10 s not raised.
>     - Run sizes: all 19 runs (1 cold) about 66 min; `-Only u0,u1,u2 -Repeats 3` 10 runs, about 35 min; `-Only s0,s1,s2` 4 runs, about 13 min.
>   - Final matrix sha256: 15BB78223A30379E524BEAE0EC65A78642200B3FAAE4CC0AA5FBBAE7AF4C32F0. Agent 8's copy `bench/agent8/run/matrix-native-uploads.json` is stale; they should run `bench/agent5/matrix-native-uploads.json`.
>   - The bullets below are from the hold period, kept for reference. Their hashes and run sizes are superseded.
> - **Task #4 (S3):** hold until native3 boots clean. Then point the 6 `bin` fields of `bench/agent5/matrix-native-uploads.json` at native3, re-check with `-PlanOnly`, send it to Agent 8 and reply `@@done 4`. No subagents. Files: `bench/agent5/**` and this file.
> - **S3 check (02:02-02:05):**
>   - The 8 source files in "Hashes for the S2 review" still match their live sha256 (last written 21:13; `upload_legacy_paths.h` 20:55). I have edited no source file since 21:13.
>   - The matrix was 777DB0D7 (21:53:59), and Agent 8's copy `bench/agent8/run/matrix-native-uploads.json` was byte-identical to it. That copy is stale after the edits below.
>   - `run-matrix.ps1` (23:33 version) `-PlanOnly`: exit 0, no matrix errors, 6/6 arms skipped on the placeholder bin, 19 runs (about 66 min) once staged.
>   - No `native3-bin` yet (02:05; still none at 02:16).
> - **Agent 1's answers (02:09):**
>   1. Yes: add `native_fps_limit=0 framerate_limit=0` to all 6 arms (SG uncapped rule). Keep the standard flags, including `--native_settings_load=false`.
>   2. Every window must start ≥ 60 s after the first frame (window-4 rule), because window 3 switched from the light to the heavy title phase 30-40 s after the first frame. Say so in the hand-off to Agent 8.
> - **Matrix now (02:16; sha256 111D7A7B…; LF, ASCII only; bins not touched):**
>   - `settle_s` 50 + `warmup_s` 10, so every window covers 60-180 s after the first-frame signal (`run-timing.ps1:212-213`). The split is on purpose: the cold run caps warm-up at 10 s and its window at 30 s, but not settle (`run-matrix.ps1:416-417`), so the cold run also starts at 60 s (60-90 s). With `warmup_s` 60 instead, it would start at 10 s. This replaces my 02:10 fix (`settle_s` 20 → 0, window from the first frame).
>   - All 6 arms have `"cvars": ["native_fps_limit=0", "framerate_limit=0"]`. The runner adds the standard flags itself (`common.ps1:99-100`). No arm sets `native_settings_frontend=false`.
>   - Rewritten notes: WINDOW; UNCAPPED; SCORING (the 120 s window is scored as usual and measures the steady-state upload cost, so expect small differences, and a tie is valid); UNSCORED DIAGNOSTIC (first-load hitches from row 0 of `native-frames.csv` with `frame_summary.py --seconds 30`, then `--skip-seconds 30 --seconds 30`, leaving out light-phase-flagged runs); sizes.
>   - `-PlanOnly` (02:15): exit 0, no matrix errors, settle 50 s, warm-up 10 s, 6/6 arms SKIP (placeholder bin). Once staged: all 19 runs about 79 min; `-Only u0,u1,u2 -Repeats 3` 10 runs, about 41 min; `-Only s0,s1,s2` 4 runs, about 16 min. Each count includes 1 cold run.
> - **Uncapped check (code read, 02:13):**
>   - With the frontend on, the cap is `LEGO_NATIVE_FPS_LIMIT` if that env is set, else the `native_fps_limit` cvar (`gpu_native/settings_snapshot.cpp:64-65`). The frontend only reads that env (`gpu_native/settings_runtime.cpp:38`, `settings_registry.cpp:146`) and never writes it, and `--native_settings_load=false` keeps saved settings out. So the cvar alone uncaps the build, and no env is needed. Without the frontend, `device.cpp:1786-1795` gives the same result.
>   - The `native_fps_limit_cvar` column of `native-frames.csv` logs the cap in force (`device.cpp:2211`, `:2346`), so it must be 0 in every row.
>   - The `texture_ms` column stays 0 without texture timing (`textures.cpp:466`), so it is no use in the timing arms.
> - **Batch-2 check for a bin:** `findstr /m /c:"LEGO_NATIVE_TEXTURE_STAGING_POOL" <bin>\legodimensions.exe`, then the same for `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD` and `Native texture staging pool: enabled`. native2-bin has all three; native-bin (S1) has none (checked 02:04).
> - **native3-bin staged (Agent 2, 02:50; MANIFEST says staged 02:45:57).** Read-only checks at 02:50 passed:
>   - sha256 prefixes match Agent 2's message: exe 7F7F8586D219465C, rexruntime.dll D1D66AC3716835AC, MANIFEST.txt B50FE8D4A16565DA. Native GPU fingerprint 8f849b69907d4006.
>   - All three batch-2 strings are present in the exe.
>   - MANIFEST: S3 (STATE-S3-0241.tsv), NATIVE_GPU=ON, with my 8 S2 files at their live hashes and fix-a (settings_registry.cpp 4EC71328, settings_preferences.cpp 9CBE6DBF).
>   - Matrix not repointed yet: that waits for Agents 7 and 8 to report a clean boot (Agent 1, 02:47).
> - **Next, when native3 boots clean** (Agent 8 boots it without `--native_settings_frontend=false`; Agent 7 checks: frontend on, no throw, bilinear present):
>   1. Check that `build/agent2/native3-bin\MANIFEST.txt` exists, then run the batch-2 check on that bin.
>   2. Change the 6 `bin` fields and the BIN DIR note to it.
>   3. Re-run `-PlanOnly`: expect exit 0, no SKIP, 19 runs (about 79 min).
>   4. Send it to Agent 8 with the window note (≥ 60 s per Agent 1, cold run included), the uncapped cvars, the scoring and the unscored diagnostic. Then reply `@@done 4`.
> - **Agent 8:** at 02:08 I asked them to treat the ≥ 60 s floor as an overridable default and exempt this matrix. Agent 1 overruled that, and I withdrew it at 02:17: the matrix complies, so no override is needed. Their copy `bench/agent8/run/matrix-native-uploads.json` is stale.
> - **Fix-a and native3:** with the frontend on, native3 defaults to a bilinear present (Agent 7). The runner always passes `--native_settings_load=false` (`common.ps1:99`).
>
> **Session-2 RESUME (01:25), kept for reference. Its status line ("done") is superseded by the session-3 block above.**
> - **Items 1-3** (SSSE3 untile, staging zero-fills, byte swaps) are in S1 (Agent 2's snapshot, MANIFEST-S1-2041.tsv, 20:41), so `build/agent2/native-bin` (21:48) already runs them.
> - **Batch 2** (every switch default OFF): the `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD` A/B switch, item 4 (`LEGO_NATIVE_TEXTURE_STAGING_POOL`) and Agent 4's edit (a). It is in S2. Agent 10 cleared it at 22:15 (§9 of `perf-notes/agent10-batch2-review.md`; the one nit was withdrawn), and `build/agent2/native2-bin` (NATIVE_GPU=ON, 23:22) contains both switches. `build/agent2/devoff2-bin` is NATIVE_GPU=OFF, so it has none of my code. Files and hashes are in "Batch-2 listing" in the session-2 report. Pre-batch-2 copies (identical to S1) are in `build/agent5/pre-batch2/`. I have edited no source file since 21:13.
> - **Not done:** Agent 4's (b) `LookupBorrowed`. It is reviewed and deferred; see the report. If it is picked up, gate it with a new `LEGO_NATIVE_BORROWED_LOOKUP=1` (default OFF). Leave `LEGO_NATIVE_RESOURCE_LOOKUP_CACHE` alone: it controls the existing `Lookup` TLS cache, which is on unless set to `0` (Agent 4, 21:56).
> - **Native boot (Agents 8 and 6 own it):** `native-bin` and `native2-bin` throw a C++ exception at startup. In `build/agent8/runs/2315-native/game.log`, the last line before the crash comes from `device.cpp:918`, the end of `HostDevice::Create`, after `StartTextureResources()` has returned. So the throw is in `legodimensions_app.h:154-168` or later, before the guest starts, and no upload code has run yet. The minidump failed.
> - **Next, after the agy-grid relaunch:** on hold. When the first native build boots clean (likely S3's), Agent 1 gives back `bench/agent5/matrix-native-uploads.json`. Then change its 6 `bin` fields and the BIN DIR note from `build/agent2/native-batch2-bin` to that build (`run-matrix.ps1` has no bin override), re-check with `-PlanOnly` (no game launch), and tell Agent 8.
>   - Sizes, at about 3.5 min per run: `-Only u0,u1,u2 -Repeats 3` is 9 runs plus 1 cold run, about 35 min. The timing arms at 5 repeats take about 56 min. Everything is 19 runs, about 66 min.
>   - Agent 10 rated u2 (the staging pool) SAFE-IF the A/B shows no corruption.
>   - Matrix 1 (emulated builds) ran locked at 60 fps. If the native build is capped too, expect the timing arms to tie, and rely on the s0/s1/s2 slow-operation lines.

**Session 1 status (12:24): partial, analysis only.** The session-2 report is at the end of this file. Per the STOP PLAN (12:24), I edited no source files and ran no builds (the toolchain isn't ready). Every cost below is an estimate from reading the code; nothing is measured yet. Both repos were left untouched.

- **Paths:** unless noted, they are relative to `DimensionsRecomp/rexlego/src/gpu_native/`. The SDK lives at `DimensionsRecomp/rexglue-sdk/`.
- **Truncated task text:** the task text arrived cut off (`Scope: textures.cpp (195 KB), b` … `itten transform`). I took the scope from my owned-file list.
- **Target bugs:** two Open bugs in `docs/native-gpu-known-bugs.md`, TEST-20 (world/vehicle stalls) and the slow first Toy Pad placement. Both look like first-use upload work on the render thread. On a content miss, `UploadTextureResourceStorage` (textures.cpp:~1957-2440) runs these steps in order:
  1. source hash (`:2150-2180`);
  2. full untile into a zeroed vector (`:2191-2280`);
  3. XXH3 of the decoded bytes (`:2285`);
  4. a new UPLOAD buffer, map and memcpy (`:2300-2306`).

## Existing switches and timers to use when resuming

- **Texture upload timing:** `NativeTextureTimingEnabled()` and `TextureUploadTiming g_upload_timing` (textures.cpp:387), with `UploadTimer` at `:411-422`, drained at `:1492`.
  - Slow-stage marks: `source-validation-hash` (`:2180`), `decode-content-hash` (`:2286`), `allocate-map-stage` (`:2307`).
  - **Use these first** to split untile, hash and allocation at the first Toy Pad placement and in TEST-20.
- **A/B env switches:**

  | Switch | Location |
  |---|---|
  | `LEGO_NATIVE_UPLOAD_POOL` | buffers.cpp:308 |
  | `LEGO_NATIVE_GEOMETRY_REUSE` | buffers.cpp:441 |
  | `LEGO_NATIVE_INDEX_SNAPSHOT_CACHE` | buffers.cpp:569 |
  | `LEGO_NATIVE_LOCAL_GEOMETRY` | buffers.cpp:328 |
  | `LEGO_NATIVE_NO_SURFACE_POOL` | textures.cpp:301 |
  | `LEGO_NATIVE_REUSE_TEXTURE_LOOKUP` | textures.cpp:519 |

## Ranked opportunities

### 1. Run-based untile for small texels: RGBA8, R8, RG8, R5G6B5 (block_bytes < 8)

- **Where:**
  - `texture_volume_upload.h:50-52` sends every block_bytes < 8 case to `texture_copy_detail::CopyBytewise` (`:13-35`).
  - Callers:
    - 2D/cube slices at `textures.cpp:2265-2277`;
    - volumes at `textures.cpp:2243-2257`.
  - **Lambda details:**
    - The source span starts at the level/face base (`:2200-2213`).
    - Packed-mip `offset_x/offset_y` are added before tiling (`:2214-2218`).
    - pitch is `row_pitch_bytes / block_bytes` and L is `log2_floor(block_bytes)`.
    - Linear (untiled) layouts use `(y+oy)*row_pitch_bytes + (x+ox)*bpb`.
- **What is slow:** the code does a lot of fixed work for every texel and every byte:
  - **Per texel:** it calls the offset lambda, which runs the full `tu::GetTiledOffset2D` with its shifts, adds and multiply.
  - **Per byte:** it does an add, an XOR, a bounds compare and a byte store (`:28-32`). RGBA8 costs four checked byte copies per texel.
  - Nothing vectorizes, because each address depends on the XOR.
  - **Estimate:** about 6-10 ns per texel. A 1024² RGBA8 texture with mips (about 1.4 M texels) costs about 8-14 ms on one thread at first use.
  - **Existing comment:** the note at `:48-49` says a per-block word-copy dispatch "regressed this case". That fits this analysis: the cost is the per-texel offset call and the loop overhead, not the byte moves, and a per-block branch removes neither.
- **Why runs work (checked against `rexglue-sdk/src/graphics/pipeline/texture/util.cpp:424-436`, which is the Xenia/UModel formula):**
  - In `micro = ((x&7) + ((y&0xE)<<2)) << L`, the low 4 bits of the offset are `((x&7)<<L) & 0xF`, plus y bit 1 at bit 3 when L == 0.
  - Every other term (macro, `(micro&~0xF)<<1`, `(y&1)<<4`) sets only bits ≥ 4, so there is no carry.
  - The final mix passes bits 0-5 through unchanged (`offset & 0x3F`), and its x term uses only `x>>3`.
  - So for a tiled x (`x+ox`) aligned to `run = run_bytes >> L` texels, with `run_bytes = (L ? 16 : 8)`:
    - `off(x0+i) == off(x0) + i*bpb`, and `off(x0) % run_bytes == 0`;
    - that gives runs of 8 texels for R8, 8 for RG8/R16, 4 for RGBA8, 2 for 8-byte BC and 1 for 16-byte BC.
  - `endian_xor` (≤ 3) only flips address bits 0-1. So for a 4-aligned run start, `(off+k)^e == off+(k^e)`, and a run is one load, one `pshufb` with `mask[k] = k^e`, and one store.
- **Proposed change:** a new owned header, `texture_untile.h`, called for the 2D/cube slice path. The volume and alpha4 paths keep the existing loops.
  ```cpp
  // Byte-identical to CopyBytewise with the textures.cpp:2271-2277 lambda.
  for (uint32_t y = 0; y < h; ++y) {
    uint32_t x = 0;
    for (; x < w && ((x + ox) & (run - 1)); ++x) if (!CopyTexelChecked(x, y)) return false;  // head
    for (; x + run <= w; x += run) {
      const int64_t off = tu::GetTiledOffset2D(x + ox, y + oy, pitch, L);
      if (off < 0 || uint64_t(off) + run_bytes > src.size()) return false;  // same bool
      StoreSwapped(dst + y * row_pitch + x * bpb, src.data() + off, run_bytes, e);  // pshufb / movq
    }
    for (; x < w; ++x) if (!CopyTexelChecked(x, y)) return false;  // tail
  }
  // Linear: a row is one run. Use 16-byte pshufb chunks when (off & 3) == 0 || e == 0,
  // and the exact per-byte XOR loop for the last < 16 bytes (or the whole row otherwise).
  ```
  - **Same failure result:**
    - A run covers exactly `off..off+run_bytes-1`, so the fast path fails for exactly the inputs where `CopyBytewise` fails.
    - The run's first texel has the lowest offset, so `off < 0` in a run means `CopyBytewise` fails at that same texel.
    - Only the bool matters: on failure, `:2278` returns false and the local `decoded` is discarded.
  - **Preconditions:** keep `CopyBytewise`'s checks unchanged (`:17-20`).
  - **SSSE3 only:** this is within the x86-64-v2 baseline. Keep a scalar run loop under `#if !defined(__SSSE3__)`. It is still a large win, because the offset call and bounds check move from per texel/byte to per run.
  - **Later options:**
    - apply runs to L = 3 BC blocks (2 blocks per run) in place of the scalar word swap at `:76-83`;
    - GetTiledOffset3D probably has the same x&7 structure (not checked);
    - the depth path's own lambda at `textures.cpp:1354` may be able to reuse the run copier.
- **Expected win:**
  - About 4-8x on uncompressed tiled untile: 4x fewer offset calls for RGBA8, 8x for R8, and 16x fewer bounds checks.
  - Linear textures should drop to near memcpy speed.
  - **Unknown:** the mix of uncompressed and BC textures at Toy Pad placement. Character textures are likely BC, which this change mostly doesn't speed up, so measure with the timers above before claiming the win.
- **Risk:** low.
  - The output is byte-identical by construction, and a differential test pins it down.
  - Misaligned packed-mip offsets are handled by the head/tail loop.
- **Verify:**
  - **Differential test** at `bench/agent5/test_untile_runs.cpp`. Compare the new copier with `CopyBytewise` plus the SDK `GetTiledOffset2D`:
    - bpb 1/2/4/8/16, endian 0-3, tiled and linear layouts;
    - widths 1-300 (odd included), with 32-aligned and unaligned pitches;
    - ox/oy from 0 to 31;
    - sources truncated by 0-64 bytes.
    - It must produce the same bool and the same bytes.
  - **Existing tests:** extend `tools/gpu-aot/test_texture_2d_upload.cpp` and `test_texture_volume_upload.cpp`.
  - **Benchmark** at `bench/agent5/bench_untile.cpp`: 256², 1024² and 2048² in RGBA8 and R8, median of 7 runs.
  - **In game:**
    - Log the decoded XXH3 (`textures.cpp:2285`) per upload in old and new builds for the same scene. The hash streams must match exactly.
    - Compare the `decode-content-hash` stage time before and after.

### 2. Every texture upload creates a new committed UPLOAD buffer

- **Where:**
  - main path at `textures.cpp:2300-2306`;
  - depth path at `:1363-1364`;
  - mirror path at `:2371`.
  - Each runs `createBuffer(RenderBufferDesc::UploadBuffer(size))`, then map, memcpy and unmap.
  - It is skipped only when the decoded hash matches the previous upload (`:2293-2299`), so every first use pays it.
- **What is slow:**
  - Each call is a D3D12MA allocation, plus fresh OS pages the kernel must zero, plus a map, all on the render thread.
  - `buffers.cpp` already avoids this for geometry with `g_upload_pool` (`buffers.cpp:76`, `Acquire` at `:312`, `Reset` at `:858`).
  - The vsync note recorded that pooling surfaces removed about 40% of render-thread CreateResource time. This is the same class of cost.
- **Proposed change:** take texture staging from an `UploadBufferPool` (`upload_buffer_pool.h`), either the shared one or a second instance with its own budget.
  - **Ownership:** `TextureUploadPublication` keeps the staging buffer for replay (`textures.cpp:188-191`; LRU budget 128 MB, `texture_upload_publication.h:~174`). The publication must own the pooled lease and give it back only when it evicts **and** the last copy's fence has retired. Reuse the pool's existing retire path.
  - **Budget:** the 128 MB budget should count pooled (power-of-two) capacity, not `upload_size`.
  - **A/B:** gate it with a default-off env switch until it is checked in game, following `LEGO_NATIVE_UPLOAD_POOL`.
- **Risk:** medium.
  - Lifetime: giving back a buffer still read by an in-flight copy corrupts textures.
  - Device reset: `UploadBufferPool::Reset` already covers it.
  - Memory: power-of-two rounding wastes up to 2x.
- **Verify:**
  - extend `tools/gpu-aot/test_upload_buffer_pool.cpp` (retire ordering, reuse after eviction);
  - extend `test_texture_publication_lru.cpp` (replay after pooled reuse);
  - run `test_texture_load_gpu.cpp`;
  - count `createBuffer` calls per frame with a counting device wrapper;
  - **in game:** the `allocate-map-stage` time at first placement and in TEST-20, with the XXH3 streams identical.

### 3. Zero-fills and extra passes in texture staging

- **Where:**
  - `std::vector<u8> decoded(upload_size)` (`textures.cpp:2191`) zero-fills the whole decode buffer. The untile then overwrites almost all of it, and `:2305` copies it into the UPLOAD buffer.
  - `TextureUploadSource::Capture` (`texture_upload_source.h:26`, `base_.resize(); mips_.resize();`) zero-fills and then copies the guest source.
  - Each large vector is a fresh allocation, so every upload pays page faults: about 1,400 faults for 5.6 MB.
- **Proposed change:**
  1. In `Capture`, use `assign(src, src + n)` or `make_unique_for_overwrite`, which removes one full write pass.
  2. Make `decoded` a grow-only, thread-local scratch buffer (capped, e.g. free it above 64 MB) that is **not** zero-filled.
  3. Explicitly zero only the bytes the copy never writes:
     - row-pitch padding past `width_blocks*bpb`;
     - the gaps from 512-byte level alignment (`:2197`).

     Those bytes go into the XXH3 key (`:2285`), so they must stay byte-identical. They don't affect the image, but they do affect cache hits.
  - Keep decoding in cacheable memory, not UPLOAD: `:2189-2190` and `texture_volume_upload.h:38-40` say so.
- **Expected win:** about 0.5-1.5 ms per large texture (a memset plus page faults). It is small for small textures.
- **Risk:** low-medium. Missing one padding region changes the cache-key bytes, not the image. The XXH3 stream comparison catches that.
- **Verify:** compare the XXH3 streams as in #1; run `test_texture_2d_upload.cpp`, `test_texture_upload_cache.cpp` and `test_texture_alpha4_upload.cpp`.

### 4. Scalar `ByteSwapElements` on index and plain-vertex uploads

- **Where:** `buffers.cpp:151-172` (`ByteSwapElements(void* destination, const void* source, size_t size, element_size)`). It is called at `buffers.cpp:505`, writing straight into mapped UPLOAD (write-combined) memory, for index buffers and for vertex buffers without packed fields.
- **What is slow:** one byte per iteration, with a runtime element size, so clang probably doesn't vectorize it. **Check the -O3 disassembly first**; if it is already vectorized, drop this item.
- **Proposed change:** keep the trailing partial-element behaviour and the scalar loop for other sizes.
  ```cpp
  #if defined(__SSSE3__)
    if (element_size == 2 || element_size == 4) {
      const __m128i m = element_size == 2
          ? _mm_setr_epi8(1,0,3,2,5,4,7,6,9,8,11,10,13,12,15,14)
          : _mm_setr_epi8(3,2,1,0,7,6,5,4,11,10,9,8,15,14,13,12);
      for (; i + 16 <= size; i += 16)
        _mm_storeu_si128((__m128i*)(dst + i),
            _mm_shuffle_epi8(_mm_loadu_si128((const __m128i*)(src + i)), m));
    }
  #endif
    // existing scalar loop finishes the tail
  ```
  The full 16-byte stores are also better for WC memory than byte stores.
- **Expected win:** about 8-16x on this loop. The size of the frame-level win depends on per-frame dynamic geometry volume (TEST-20 streaming, particles, UI), which is unknown.
- **Risk:** low; the output is byte-identical by construction.
- **Verify:**
  - a differential test against the scalar loop over random sizes, offsets and element sizes 1/2/4/8, at `bench/agent5/test_byteswap.cpp`;
  - a benchmark modeled on `tools/gpu-aot/benchmark_vertex_upload.cpp`;
  - `test_vertex_upload.cpp` and `test_buffer_header.cpp`.

### 5. Lower-value items, recommended only

- **Geometry reuse copy:** `buffers.cpp:450-460` copies the whole guest buffer into `reuse_bytes` on every non-volatile content change (`assign` at `:455`), and `GeometryContentCache::Find` memcmps it.
  - A possible gain is to convert from `source` (`:492`) and copy lazily, only on `Remember` (`:529`).
  - This is low priority; `LEGO_NATIVE_GEOMETRY_REUSE` is the A/B switch.
- **`PromoteImmutableGeometry`** (`buffers.cpp:322-364`, called at `:522`): every non-volatile vertex upload adds a DEFAULT-heap copy. This is GPU-side; measure it with GPU timestamps in TEST-20 before changing anything (A/B with `LEGO_NATIVE_LOCAL_GEOMETRY`).
- **Decoded hash on a cache miss** (`textures.cpp:2285`): needed for the publication/cache semantics. Skipping it when only the source key changed and the layout is identical is risky and needs the game. Not proposed now.

### Rejected

- `vertex_upload.h:14-68` rebuilds its fused-path mask table, with a `binary_search`, on every call. That is ≤ 64 blocks, so it is negligible.
- `InvalidatePoolCopyBuffers` (`buffers.cpp:223-246`) does a linear scan, but only on pool copies, and `FootprintIndex` already gates it.
- `ResolveBufferWindowCached` is off by default (`LEGO_NATIVE_BUFFER_STREAM_CACHE=1`).
- `UploadBufferPool` power-of-two waste (192 MB / 4096 buffers) costs memory, not time.

## Order for the next session

Prerequisites: the toolchain is ready, Agent 3's harness compiles `gpu_native`, and the tests build into `build/agent5` with `ninja -j4`.

1. **Measure first.** Bench the current `CopyBytewise` and `ByteSwapElements`. In game, enable the texture upload timing and take a render-thread sample of the first Toy Pad placement and TEST-20. That gives the real split between untile, `createBuffer`, hashing and promotion, plus the format mix.
2. Do #1 (untile runs) with its differential test and benchmark.
3. Do #4 (`ByteSwapElements`), if the disassembly shows it is scalar.
4. Do #3 (scratch buffer and no zero-fill).
5. Do #2 (pooled staging). It has the most lifetime risk, so do it last, behind a default-off env switch.

## Follow-ups that need the game or a profiler

- How time at first placement and at TEST-20 stalls splits across stages, from the timers above.
- The uncompressed vs BC texture mix at placement, which decides how much #1 is worth.
- D3D12MA allocation counts per frame.
- GPU cost of the immutable-geometry promotion copies.

## What I didn't get to read

- `textures.cpp`:
  - lines 260-1280: surface pool, `CreateHostTexture` (~372/~1017), `AdoptTexture` (~535), capture code;
  - lines 1480-1957;
  - lines 2312-3925: footprint/copy recording after staging, `PrepareTextureResource` (~2539-2620), `RegistryFreeTextureUpload` (~2529-2930), pool-copy/writeback/materialize (~3299-3925), and the tiled fetch at `:3674`.
- `textures.h`, `hooks_texture.cpp`, `hooks_buffer.cpp`, `buffers.h`, `format.cpp/.h`.
- `texture_alpha4_upload.h` (its copier at `textures.cpp:2223` may have the same per-byte cost), `texture_depth_upload.h`, `texture_swizzle.h`, `texture_readback*.h`, `texture_writeback*.h`.
- `vertex_declarations.cpp`, `vertex_fetch_plan.h`, `vertex_binding_cache.h`, `vertex_layout_plan.h`, `vertex_fetch_range.h`, `vertex_texture_read.h`.
- `index_snapshot_cache.h`, `index_draw.h`, `quad_index_cache.h`, `stream_source_shadow.h`, `device_snapshot_pool.h`, `pool_copy.h`, `buffer_window.h`, `buffer_header.h`, `buffer_alloc_diagnostic.h`, `geometry_upload.h`.
- `draw.cpp` (callers), `tools/gpu-aot/native-buffer-watch-20261003.md`, `native-work-20261004.md`.
- The SDK `GetTiledOffset3D` body (`util.cpp:438`). The 2D body was checked.
- Whether clang already vectorizes `ByteSwapElements`.
- Where `NativeTextureTimingEnabled()` is switched on (it is defined outside `textures.cpp`).
- Line numbers marked `~` came from earlier reading and were not re-checked; all the others were confirmed by grep.

## Session 2 report (task #4, re-issued 17:52; written 21:58)

**Status: done.**
- Items 1-3 are in S1 and on by default.
- Batch 2 adds two default-OFF switches and Agent 4's edit (a).
- Nothing was run on the GPU or in game: no native ON bin with batch 2 exists yet, and the GPU tests need the plume lib from a full build. The in-game A/B plan and a matrix for Agent 8 are below.

Paths are relative to `DimensionsRecomp/rexlego/src/gpu_native/`. Line numbers are for the live tree at 21:50.

### What changed

| Item | Where | In | Default |
|---|---|---|---|
| 1. SSSE3 run-based untile | `texture_volume_upload.h:103-289`, called at `textures.cpp:2332` | S1 | on |
| 2. No staging zero-fills | `texture_scratch.h`; `ZeroTextureRowPadding` (`texture_volume_upload.h:296`); `texture_upload_source.h:46`; `buffers.cpp:492` | S1 | on |
| 3. SIMD byte swaps | `SwapUploadElementBytes` (`vertex_upload.h:105`), called by `ByteSwapElements` (`buffers.cpp:152`) | S1 | on |
| A/B switch for items 1-3 | `upload_legacy_paths.h` (new), plus one check at each item-1-3 site | batch 2 | off. `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD=1` restores the old paths |
| 4. Texture staging pool | `textures.cpp:179-227`, `:2368`, `:2440`, `:3329`, `:3336`; `upload_buffer_pool.h` | batch 2 | off. `LEGO_NATIVE_TEXTURE_STAGING_POOL=1` turns it on |
| Agent 4's (a) | `textures.cpp:3148`, `:3155` | batch 2 | always on; output is identical |

#### Item 1: run-based untile (S1)

- **What it replaces:** `CopyTexture2DBlocks` (`texture_volume_upload.h:265-289`) replaces the per-byte `CopyBytewise` loop for 2D and cube slices.
- **Coverage:** every power-of-two block size from 1 to 16 bytes, tiled and linear, endian modes 0-3. That covers R8, RG8, R5G6B5, RGBA8 and the 8- and 16-byte BC formats.
- **Helpers** (in `texture_copy_detail`):
  - `CopyTiledRows<8|16>` (`:164`) computes one Xenos tile offset per 8- or 16-byte run, which is 8 R8 texels, 8 RG8, 4 RGBA8, 2 BC1 blocks or 1 BC3 block. It then does one load, one `pshufb` for the endian swap and one store.
  - `CopyLinearRows` (`:217`) computes one offset per row and copies it in 16-byte chunks.
  - `TiledRowsFit` and `LinearRowsFit` (`:124`, `:134`) check once per slice that the rows are in bounds.
- **Fallback:** a slice outside the fast domain keeps the old per-block path, so a failing slice returns the same `false`. That covers non-power-of-two blocks, slices that fail the bounds check, address maths that could overflow, and every slice when the legacy switch is on.
- **Builds:** without SSSE3, the same run structure uses a scalar word swap (`CopySwappedWords`, `:143`). The x86-64-v2 build uses SSSE3 only, so no runtime dispatch is needed.
- **Unchanged:** volumes and alpha4 slices keep their existing loops.

#### Item 2: staging zero-fills (S1)

- **Decode buffer:** `TextureDecodeScratch` (`texture_scratch.h:18`) replaces `std::vector<u8> decoded(upload_size)` at `textures.cpp:2247`.
  - Requests up to 16 MB lease a grow-only block owned by the calling thread. Its capacity is a power of two, at least 64 KB, and it is not zeroed.
  - Larger requests, and nested requests on the same thread, get a one-off uninitialised block.
- **Every hashed or staged byte is still written:**
  - the copy writes each row's payload;
  - `ZeroTextureRowPadding` zeroes the row-pitch padding and the rest of the level after each successful copy (`textures.cpp:2281`, `:2303`, `:2325`);
  - the decode loop zeroes the 512-byte level-alignment gaps.

  So the decoded bytes, and the XXH3 content key computed from them, are unchanged.
- **Capture vectors:** in `texture_upload_source.h:46` they use a default-init allocator, so `resize` no longer zero-fills before the reader fills them. A failed read discards the capture.
- **Conversion buffer:** at `buffers.cpp:492`, `converted` is `new u8[len]`, no longer `new u8[len]()`. `ByteSwapElements` writes every byte (whole elements plus the copied tail) before `ApplyVertexByteOrder` permutes within the range.
- **Test anchor:** `tools/gpu-aot/test_texture_upload_retention_sdk.py:14-15` now accepts either `TextureDecodeScratch decoded(upload_size)` or the old `std::vector<u8> decoded(upload_size)`. It extracts the same decode loop and checks the same property. It passed before and after item 2, and again after batch 2.

#### Item 3: byte swaps (S1)

- **New loop:** `SwapUploadElementBytes` (`vertex_upload.h:105`) swaps 16-bit or 32-bit elements with 32-byte AVX2 chunks (v3 build) and 16-byte SSSE3 `pshufb` chunks. The old scalar loop handles the remaining whole elements, and a trailing partial element is copied unchanged. The semantics match the old loop: `element_size` 2 swaps 16-bit halves, and any other size swaps 32-bit words.
- **Caller:** `ByteSwapElements` (`buffers.cpp:152`) keeps its signature and calls the new loop, because 5 gpu-aot tests extract its body.

#### Batch 2: `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD` (A/B switch for items 1-3)

- **Switch:** `LegacyUploadPathsEnabled()` (`upload_legacy_paths.h:14`) reads the variable once. It is on when the value is set, non-empty and doesn't start with `0`.
- **When it is on:**
  - `texture_volume_upload.h:279`: `CopyTexture2DBlocks` goes back to `CopyTextureVolumeBlocks`, the scalar untile.
  - `texture_scratch.h:23`: each upload allocates a one-off zeroed block, as `std::vector<u8>(n)` did.
  - `texture_upload_source.h:47-50`: the capture vectors are zero-filled before the copy.
  - `vertex_upload.h:107`: `SwapUploadElementBytesLegacy` (`:77`) runs, which is the old loop verbatim.
  - `buffers.cpp:492`: `converted` is zero-filled.
- **Still runs with it on:** `ZeroTextureRowPadding` and the level-gap memset. They touch padding only, so the cost is negligible.
- **Output is identical in both modes:** every test below passes with the switch on.
- **The switch takes effect:** the benches give new ≈ old in every cell with it on (see Numbers). That shows the switch reaches the production functions.

#### Batch 2: item 4, texture staging pool (`LEGO_NATIVE_TEXTURE_STAGING_POOL`)

- **Code:** `textures.cpp:179-227` holds:
  - `kTextureStagingPoolBudget` (64 MB);
  - `g_texture_staging_pool`, a second `UploadBufferPool<plume::RenderBuffer>` with a 64 MB budget;
  - `g_texture_staging_pool_mutex`, a `std::shared_mutex`;
  - `TextureStagingPoolEnabled()`, which logs `Native texture staging pool: enabled, 64 MB idle budget` once;
  - `UseTextureStagingPool(bytes)`: true when the pool is enabled, `bytes` is nonzero and at most 64 MB;
  - `AcquireTextureStaging()`: takes a shared lock, uses pool kind 0 and creates `UploadBuffer(capacity)`. Every 256 calls it logs `hits=... misses=... idle_bytes=... idle_buffers=...`;
  - `ResetTextureStagingPool()`: takes a unique lock, then calls `Reset`.
- **Sites:** the main staging buffer (`:2368-2371`) and the mirror upload (`:2440-2443`). The depth staging path (`:1417`) is unchanged.
- **Lifetime:**
  - A pooled buffer returns to the pool only when its last `shared_ptr` owner releases it.
  - The owners are the same as before: the publication LRU (`g_texture_upload_publications`, for replay) and the fence slots of `RetireResource`.
  - So the pool gets a buffer exactly where the default path destroys it, after the GPU copies that read it have retired.
  - If any path released staging before its copies retired, the default path would already be a use-after-free. With the pool it would show up as texture corruption, so the A/B plan watches for that.
- **Content:** each use maps the buffer and writes the whole decoded upload, which covers every byte its copy footprints read. The power-of-two slack past the requested size is never read.
- **Memory:**
  - At most 64 MB stays idle in the pool.
  - Each pooled buffer is charged at least 64 KB, and capacities round up to a power of two (at most 2x).
  - Uploads over 64 MB keep a dedicated buffer: the pool would never keep them, and this avoids the 2x rounding and a u32 truncation.
  - The publication LRU charges the requested size, not the pooled capacity. So LRU-held staging can use up to 2x its accounted bytes, on top of the 64 MB idle.
- **Concurrency:**
  - Unlocked draw-preparation uploads (`UnlockedTextureUploadEnabled() && CurrentDrawPreparation()`, `textures.cpp:2626`) stage without the recording lock, so `Acquire`, which reads the pool state, could race with `Reset`, which swaps it.
  - The shared/unique lock orders them. It is taken only when the pool is enabled.
- **Reset order:**
  - `StartTextureResources` (`:3329`) and `ResetTextureResources` (`:3336`) reset the pool.
  - In `ResetTextureResources`, the reset runs before `g_texture_upload_publications.Reset()`. Buffers the publications release after that see the retired pool state and are destroyed, not kept for a dead device.
  - `HostDevice::Shutdown` (device.cpp:923-955) calls `ResetTextureResources` after `WaitForSubmittedFrames` and before it destroys the device.
- **Header:** `upload_buffer_pool.h` now takes the budget as a constructor argument, `explicit UploadBufferPool(uint64_t budget)` (`:21`).
  - The default constructor uses `kDefaultBudget` = 192 MB (`:18-20`), so `g_upload_pool` in `buffers.cpp` behaves exactly as before.
  - `Reset` keeps the budget.

#### Batch 2: Agent 4's edit (a)

This is Agent 4's §S2.9 diff in `ResolveFramebuffer`, which was at lines 3092/3099 before batch 2 added lines above it.
- **`textures.cpp:3148`:** the depth texture is looked up only when `depth_stencil` is nonzero. `FindTexture(0)` already returned `{}`.
- **`textures.cpp:3155`:** `owner` is a `const&` to `depth` or `colors[0]`, not a copy, which saves 2 locked RMWs per call. Neither variable is modified before the function returns, and both stay alive until then.

### Batch-2 listing (for Agents 1, 2 and 10)

| File | Change | Default behaviour |
|---|---|---|
| `upload_legacy_paths.h` | **New file**: `LegacyUploadPathsEnabled()`. It uses LF line endings and matches no claim glob; it is mine (Agent 5) | n/a |
| `texture_volume_upload.h` | include, plus the legacy check at `:279` | unchanged |
| `texture_scratch.h` | include, plus the legacy zeroed block at `:23` | unchanged |
| `texture_upload_source.h` | include, plus the legacy memsets at `:47-50` | unchanged |
| `vertex_upload.h` | include, `SwapUploadElementBytesLegacy` (`:77`), and the legacy check at `:107` | unchanged |
| `buffers.cpp` | include, plus the legacy `new u8[len]()` at `:492` | unchanged |
| `upload_buffer_pool.h` | budget constructor; `kDefaultBudget` = 192 MB; the default constructor is unchanged | unchanged |
| `textures.cpp` | includes `<shared_mutex>` and `upload_buffer_pool.h`; the staging pool (`:179-227`); 2 acquire sites (`:2368`, `:2440`); 2 resets (`:3329`, `:3336`); Agent 4's (a) (`:3148`, `:3155`) | unchanged, except (a), whose output is identical |

**Env vars.** Both are default OFF and read once, at first use. A restart is needed to change them.
- `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD=1`: the old upload CPU paths, with the same output bytes.
- `LEGO_NATIVE_TEXTURE_STAGING_POOL=1`: pooled texture staging buffers.

**Hashes for the S2 review** (sent to Agent 10 at about 22:00). Files are in `DimensionsRecomp/rexlego/src/gpu_native/`. "Live" is the tree as of 21:58; these files were last written at 21:13 (`upload_legacy_paths.h` at 20:55), before every test in "Tests and checks" ran. "S1" is from `build/agent2/snap1/MANIFEST-S1-2041.tsv`. The copies in `build/agent5/pre-batch2/` match S1 exactly, so diffing them against the live files gives exactly the batch-2 change. Every other file I own matches S1, including `resource_registry.h` and `tools/gpu-aot/test_texture_upload_retention_sdk.py`.

| File | Live sha256 | S1 sha256 |
|---|---|---|
| `upload_legacy_paths.h` | `5c823f13b067c93a921864ed49ddd1718a74ecf30ea5b5d7d72f5273e478e968` | new file |
| `texture_volume_upload.h` | `d0601ecf0150df8fbd410a310df783161bb8cded06ad0558480cfd84005d2f73` | `328dfcec476599c24979edf135f23872c5f354e21bf10792a711bf7e485e8207` |
| `texture_scratch.h` | `8f6a12ae70994065f94e6a133c730c1176524107519cc99e083ec38a46bbdfb2` | `d1f0a5c3bb8427d60da41396b40e2f31bf61696b58b2ee22b2351526f6970416` |
| `texture_upload_source.h` | `ff9e11417227a8bae81002989b99bab66a5ae4b22228374967c2ff51442ade43` | `e8bd27d3713ffe28d47559c06a840a544ca4e08e9173ff0656c0e7f41b1d23ea` |
| `vertex_upload.h` | `ffd2b023ac4cc6d55a696c8dd99db22d9927b2cb726ccfbc7b9efd14bc06d5a5` | `7fc6952362ff4b8e9c69412b06f8d57f260a5b8e9548c25f1622d93fd6abc6e6` |
| `buffers.cpp` | `75025044c39ff91023628a1a8ca7179bb48da484bec3cf732c1893c739e4cf79` | `db8fe4864dbaf207f68e2232012b0b856b7bcf168a521e00aeec99dab2a2d1d8` |
| `upload_buffer_pool.h` | `853e6c16be4082b9ecd638cbecae0f6fe2f366028ed11530b040fb6425fdf867` | `3ede3afc0f6a368eaef377c3f3d37b6a0145dc4041bd851463dfa1ef7447bbf4` |
| `textures.cpp` | `3011add45516123f6db56f93aba824261142569a388c4cc56198eec0094f9e43` | `a6b45772d017f8d4b124ec02d11fce0ae6bb1f809052d5ba3639513e46eeb0b9` |

### Tests and checks

| Check | Default | Legacy switch on | Log (`build/agent5/`) |
|---|---|---|---|
| Untile differential (`bench/agent5/test_untile_runs.cpp`; v3, v2 and no-SSSE3 builds) | PASS: 3,964,537 copies; 713,682 succeeded, 3,250,855 failed identically; 174,741 slices in the fast-path domain | PASS, same counts | `b2-tests-default.log`, `b2-tests-legacy.log` |
| Byte-swap differential (`bench/agent5/test_byteswap.cpp`; v3, v2, scalar) | PASS: 542,348 cases, no out-of-range writes | PASS | same |
| Staging pool unit test (`bench/agent5/test_texture_staging_pool.cpp`, v3) | PASS, 0 failures | n/a | `b2-staging-pool.log` |
| Retention test (`tools/gpu-aot/test_texture_upload_retention_sdk.py`) | PASS: 1,440 decode cases; 4 broken variants rejected | same | `retention-b2.log`, `retention-b2-legacy.log` |
| Decode poison test (`bench/agent5/test_decode_poison_sdk.py`) | PASS: 13,200 decode cases; both mutants caught | same | `poison-b2.log`, `poison-b2-legacy.log` |
| `env/compile-one.ps1 -SyntaxOnly` (build/dev DB) | `textures.cpp` and `buffers.cpp` exit 0; getenv deprecation warnings only | n/a | step output |
| gpu-aot CPU checks (`bench/agent5/run_gpuaot_cpu.ps1 -Tag b2fix`) | 17 pass; 7 fail, all 7 pre-existing | n/a | `gpuaot-b2fix/` |

- **Untile differential:** it compares the old per-block path with the new one: `CopyTextureVolumeBlocks` with the `textures.cpp` callback and the SDK `GetTiledOffset2D`, extracted verbatim. It covers random data, every block size, endian 0-3, tiled and linear, odd and non-multiple sizes, aligned and unaligned pitches, packed-mip offsets and truncated sources. Every case must return the same bool and, on success, the same destination bytes, including padding.
- **Poison test:** it feeds its own 0xCD-poisoned buffers through the production loop and compares them with zero-filled ones. It checks that the loop writes every byte, whatever the allocation does. That is why it gives the same result with the legacy switch on.
- **Staging pool unit test** covers:
  - the default budget is unchanged (3 × 64 MB pooled, the 4th destroyed);
  - a 64 MB pool keeps 2 × 32 MB and destroys the 3rd;
  - a 65 MB request rounds to 128 MB and is never pooled;
  - every buffer is charged at least 64 KB;
  - no reuse while a buffer is held;
  - power-of-two classes, kinds, zero length, and the per-class cap of 256;
  - `Reset` semantics, and the budget kept after `Reset`;
  - a buffer that outlives its pool;
  - 300,000 acquires on 2 threads through the same shared-lock pattern, with a concurrent `Reset` thread (31 resets): no buffer handed out twice, no short capacity, nothing leaked.

**gpu-aot CPU checks (b2fix):**

| Check | Exit | Note |
|---|---|---|
| texture_volume_upload, texture_alpha4_upload, texture_2d_upload, vertex_upload, vertex_byte_order, pool_copy, each built for x86-64 and v3 | 0 (12 runs) | |
| test_buffer_variants, test_texture_depth_upload, test_texture_publication_lru, test_texture_source_residency | 0 | |
| test_upload_buffer_pool_64mb | 0 | A copy of test_upload_buffer_pool built with `pool(64*1024*1024)`, the budget its asserts were written for |
| test_upload_buffer_pool | 0xC0000409 | Pre-existing. The line-34 assert expects a 64 MB budget, and the test fails the same way against the pre-batch-2 header (192 MB) |
| test_buffer_view_generation, test_quad_buffer_windows | 1 | Pre-existing: stale mocks, so they don't compile |
| test_texture_prepare, test_texture_binding_failures | 1 | Pre-existing: their mocks lack `bloom` and `pixel_texture_mask` |
| test_framebuffer_owners | 1 | Pre-existing: missing anchor `void InvalidateFramebufferReferences(u32 guest_address)`. Its `ResetTextureResources` slice now also calls `ResetTextureStagingPool()`, so its mock will need that symbol once the anchor is fixed |
| test_texture_upload_capture | 1 | Pre-existing. Case filter-3 sets `LEGO_DUMP_TEXTURE_UPLOADS_PIXEL_SHADER` to an empty value, and on Windows `_putenv_s(name, "")` deletes the variable, so the capture isn't filtered and the case exits 20. The slice it extracts is byte-identical in the live, pre-batch-2 and pre-session-2 `textures.cpp` |

- **Runner bug, now fixed:** before 21:35, `run_gpuaot_cpu.ps1` reported each step's exit code one step late, because a `.GetNewClosure()` script block captured a stale `$LASTEXITCODE`. It now uses plain functions, and b2fix is the first correct summary. Older summaries are unreliable, but their per-step logs are fine.
- **Suggested fixes for the test owners:**
  - test_upload_buffer_pool: construct the pool with `pool(64*1024*1024)` (that version passes), or update lines 34 and 37 for the 192 MB default.
  - test_texture_upload_capture: set filter-3's empty value some other way on Windows, or skip that case there.

### Numbers

- **Setup:** one thread, devshell clang `-O2`, 7 samples per cell, median. "Old" is the previous code, verbatim, compiled into the same binary.
- **Noise:** other agents' builds were running on the machine, so expect up to ±30% per cell. The ratios are large enough to survive that.

**Untile** (`bench/agent5/bench_untile.cpp`), ms per slice, old → new. Full tables: `build/agent5/bench_untile_v3.txt` and `bench_untile_v2.txt`.

| Format | Size | Layout | v3 (AVX2 build) | v3 speedup | v2 (SSSE3 build) | v2 speedup |
|---|---|---|---:|---:|---:|---:|
| R8 | 1024² | tiled | 23.63 → 1.57 | 15.1x | 25.28 → 1.95 | 13.0x |
| R8 | 1024² | linear | 7.40 → 0.13 | 55.7x | 8.29 → 0.25 | 33.0x |
| RG8/R5G6B5 | 1024² | tiled | 23.28 → 1.71 | 13.6x | 27.32 → 1.82 | 15.0x |
| RGBA8 | 256² | tiled | 0.93 → 0.09 | 10.6x | 0.91 → 0.09 | 10.7x |
| RGBA8 | 1024² | tiled | 13.97 → 1.77 | 7.9x | 33.31 → 4.02 | 8.3x |
| RGBA8 | 1024² | linear | 12.88 → 1.17 | 11.0x | 21.51 → 1.55 | 13.9x |
| RGBA8 | 2048² | tiled | 117.47 → 15.96 | 7.4x | 140.47 → 17.05 | 8.2x |
| RGBA8, endian 0 | 1024² | tiled | 28.08 → 2.97 | 9.5x | 15.30 → 1.98 | 7.7x |
| BC1 | 1024² | tiled | 1.95 → 0.46 | 4.2x | 1.07 → 0.18 | 6.0x |
| BC3 | 1024² | tiled | 2.31 → 0.84 | 2.7x | 1.24 → 0.46 | 2.7x |
| BC3 | 2048² | tiled | 8.81 → 4.24 | 2.1x | 10.99 → 4.02 | 2.7x |

**Byte swap** (`bench/agent5/bench_byteswap.cpp`), ns per call, old → new. Full tables: `build/agent5/bench_byteswap_v3.txt` and `bench_byteswap_v2.txt`.

| Size | Element bytes | v3 (AVX2 build) | v3 speedup | v2 (SSSE3 build) | v2 speedup |
|---|---:|---:|---:|---:|---:|
| 96 B | 2 | 81 → 9 | 8.8x | 112 → 6 | 18.2x |
| 4 KB | 2 | 3,675 → 168 | 21.9x | 2,598 → 155 | 16.8x |
| 4 KB | 4 | 2,622 → 178 | 14.8x | 2,247 → 144 | 15.6x |
| 64 KB | 2 | 52,529 → 6,486 | 8.1x | 44,621 → 6,071 | 7.4x |
| 1 MB | 4 | 705,584 → 237,103 | 3.0x | 724,202 → 176,439 | 4.1x |
| 8 MB | 2 | 8,431,975 → 2,513,788 | 3.4x | 6,138,938 → 2,149,200 | 2.9x |

- **Large buffers:** from 1 MB up, the new loop runs at 3-6 GB/s, which is memory-bound on this loaded machine. In game it writes to write-combined UPLOAD memory, where whole 16- and 32-byte stores also help.
- **Legacy switch check:** with `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD=1`, the same benches give new ≈ old in every cell: 0.9x-1.4x for the untile and 0.8x-1.1x for the byte swap. See `build/agent5/bench_untile_v3_legacy.txt` and `bench_byteswap_v3_legacy.txt`.
- **No microbench for items 2 and 4:** their costs only show in game. Those costs are page faults, memsets of fresh pages, and the D3D12MA allocation of a committed UPLOAD buffer per upload. My session-1 estimate for item 2 was 0.5-1.5 ms per large texture.

### In-game A/B plan

> Session 3: the bin, window and sizes in this section are superseded. See the RESUME blocks at the top and "Session 3, task #15" at the end.

#### Automated runs (Agent 8)

The matrix is `bench/agent5/matrix-native-uploads.json`. Run it with `bench/agent8/run/run-matrix.ps1 -Matrix bench\agent5\matrix-native-uploads.json`. It passes `-PlanOnly` with no matrix errors; the arms are skipped there only because the bin isn't staged.

| Arm | Env, on top of `LEGO_NATIVE_FRAME_METRICS` | Repeats | Purpose |
|---|---|---|---|
| u0 (reference) | none | 5 | batch-2 defaults |
| u1 | `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD=1` | 5 | the old CPU paths for items 1-3 |
| u2 | `LEGO_NATIVE_TEXTURE_STAGING_POOL=1` | 5 | item 4 |
| s0, s1, s2 | `LEGO_NATIVE_SLOW_OPERATIONS=1`, plus the u0, u1 and u2 env | 1 each | diagnostics only; frame times are not scored |

- **Bin:** it must be a native ON build that contains batch 2; the placeholder is `build/agent2/native-batch2-bin`. `build/agent2/native-bin` (21:48) is S1 only: it already runs items 1-3 but has neither switch, so u1 and u2 would equal u0 there. The u2 log line is the check.
- **Window:** 120 s from the first frame (`warmup_s` 0) in the title/attract loop, with no input. Every run is a fresh process, so every texture is a first-use upload, and that is where the first-load hitches are.
- **Cost:** all arms take 19 runs, about 66 minutes. The timing arms alone (`-Only u0,u1,u2`) take 15 runs, and `-Repeats 3` cuts that to 9.

#### What to compare

- **Frame times:**
  - In the first 30 s after the first frame: the number of intervals over 33 ms and over 100 ms, the longest interval, and p99.
  - Over the whole window: mean fps, p50 and p99.
- **u1 vs u0:** expect u0 ≤ u1. The untile is 7-17x faster on tiled uncompressed slices and 2-8x on tiled BC, but the share of uncompressed textures at boot is unknown.
- **u2 vs u0:** expect u2 ≤ u0, or a tie.
- **s0, s1, s2:** compare the `Native slow CPU operation: texture-upload total_ms=...` lines (operations of 4 ms or more, at most 128 lines) and their stage marks. Expect `decode-content-hash` to be longer in s1 than in s0, and `allocate-map-stage` to be shorter in s2 than in s0.
- **u2 memory:**
  - commit and peak commit against u0 (at most 64 MB idle plus the power-of-two slack);
  - the pool's `hits=... misses=... idle_bytes=...` lines, logged every 256 staged uploads. A high hit rate is the point.
- **Correctness:** watch u2 for texture corruption, such as wrong or flickering textures or garbage on first load. If you see any, stop and report it to Agent 5.

#### Manual scenes (the user, on the interactive desktop)

Both open bugs (TEST-20 and the slow first Toy Pad placement) are first-use upload stalls, and checking them needs input:
1. The first Toy Pad placement of a character not yet seen this session.
2. The first level load from the hub.
3. TEST-20: drive into new areas of the world.

Repeat the same steps in each of the three modes (default, legacy switch, staging pool), restarting the game between modes:
- Set `LEGO_NATIVE_FRAME_METRICS=<dir>\native-frames.csv` and `LEGO_NATIVE_SLOW_OPERATIONS=1`.
- Compare the longest frame at the placement or load, and the slow-operation stage lines.

`build/agent2/native-bin` already runs items 1-3, so any texture corruption seen there in the tier-1 runs should be reported to me too.

### Agent 4's (b): reviewed, not applied

- **What it is:** Agent 4's `LookupBorrowed` (§S2.9 of `perf-notes/agent4-draw-path.md`). It was to be gated by a new `LEGO_NATIVE_BORROWED_LOOKUP=1`, default OFF. `LEGO_NATIVE_RESOURCE_LOOKUP_CACHE` would keep controlling the existing `Lookup` TLS cache, which stays on unless set to `0`.
- **Why not applied:** time. It needs a per-caller lifetime proof, a unit test and a compile check, and the quiet window from about 21:50 leaves no compile slot before the batch-2 cut-off. The saving is 2 hits (4 locked RMWs, about 100-200 ns) per draw with depth.
- **What a later session must check, in addition to Agent 4's list:**
  - `FindTexture` (`textures.cpp:539`) tries `FindPinnedOwner(kPinTexture, ...)` first. The borrowed path must return the same object in every mode, or be limited to `!CurrentDrawPreparation()`.
  - The full-preparation deferred release erases under `g_textures_mutex` only, so the gate must also require `!NativeFullDrawPreparationEnabled()`, and the caller must hold `LockRecording`.
  - Nothing between the borrowed lookups and `owner->framebuffers.find` may erase: no `FindTextureAtUse` and no pool-copy invalidation. On a miss, fall through to today's shared lookups unchanged.
  - Tests: Agent 4's bench unit tests, plus a mutant that erases between the lookup and the use.

### Follow-ups

- The depth staging path (`textures.cpp:1417`) still creates a buffer per upload. It can use the same pool once u2 is proven in game.
- BC slices gain the least (BC3 is 2-4x tiled), and volumes and alpha4 slices still use the old per-byte loop. If s0 shows `decode-content-hash` still dominating, extend the run copier to volumes (`GetTiledOffset3D`) next.
- The test owners should fix the pre-existing gpu-aot failures listed above.
- Once the A/B has settled, `upload_legacy_paths.h` and both switches can be removed.

## Session 3, task #15: user-window uploads matrix and load-phase score (03:07-03:40)

The task: make the uploads matrix worth a user window (45 min or less, the most signal, the same native3-bin, cvars and 60 s floor); score the load phase in a script under `bench/agent5/` without touching Agent 8's runner; test it on existing native runs; run `-PlanOnly`; send the plan to Agents 8 and 1. Planning only.

### The matrix: `bench/agent5/matrix-native-uploads-45.json`

- **Design:**
  - u0/u1/u2, 5 runs each, with a 60 s scored window, plus the unscored cold u0: 16 runs.
  - Settle 50 + warm-up 10 from the first-frame signal, with `min_window_after_ff_s` 60 set explicitly. Cooldown 10. Round-robin: u0 u1 u2 | u1 u2 u0 | u2 u0 u1 | u0 u1 u2 | u1 u2 u0.
  - Same bin, cvars (`native_fps_limit=0`, `framerate_limit=0`) and env as the original. The three arms are byte-identical to it.
- **Why:**
  - The signal is in the load phase, and every run pays it, so the number of runs matters more than the window length. At 5v5 the smallest exact p is 0.008, or 0.029 if one run is lost. 4v4 can never go below 0.029, and 3v3 never below 0.10.
  - The scored window drops from 120 to 60 s. On the quiet window-3 runs no frame after 5 s took more than 25 ms, so the steady-state window is expected to tie. At 60 s it stays as a check at half the cost.
  - The s-rows are diagnostics that need no user window. They stay final and unchanged in `matrix-native-uploads.json` (15BB7822...), and Agent 8 runs them in its own slot with `-Only s0,s1,s2`.
  - The cold run stays. It absorbs the first-launch file-cache cost, which would otherwise land in round 1's load phase.
- **Size:**
  - `-PlanOnly` (03:33, re-checked at 03:36 on the final file and at 03:56 after the sys_csv key; Agent 8's runner, last written at 03:15, not the 02:53 version I first noted): 16 runs, about 41 min. Exit 0, no SKIP, no matrix errors, bin `ok (MANIFEST.txt)`, warm-up 10 s not raised. The only `!!!` lines were preflight ones that don't apply to the user's run: a running legodimensions.exe at 03:33, and at 03:36 "FUNCTIONAL ONLY", because an agent shell is not the interactive desktop.
  - Realistic, from the S3 runs:
    - close + post-processing + cooldown took 21 s, against the planned 20 s;
    - launch to window start took launch-to-first-frame (13-21 s, against the planner's 12 s) + settle + warm-up + 0.3-0.5 s.
  - So expect 41-42 min on a quiet machine, and at most about 44 min if every boot is slow.
  - `-Repeats 4`: 13 runs, about 33 min.
- **File:** sha256 114A024244C75EC956D12B170511CCA2B5BEBB437C449432EB4617E9EE6FBD02. LF, ASCII, no BOM, 3 arms, 13 notes. `"sys_csv": true` since 03:56 (Agent 8's request): every run logs sys.csv and sys.json, so input, foreground loss, screensaver and power changes get flagged. The only other change is one sentence in the QUIET MACHINE note. Previous sha256: C59DB350...

### The script: `bench/agent5/load_phase.py`

- **Use:** `python bench/agent5/load_phase.py <matrix output dir> --ref u0 --md <dir>/load-phase.md --csv <dir>/load-phase.csv --json <dir>/load-phase.json`. Stdlib Python, one thread, read-only on the run dirs. It writes only the files it is asked for.
- **Per run, over the first 60 s after the first frame (from row 0 of `native-frames.csv`):**
  - frames over 33, 50 and 100 ms; hitch ms (the summed excess over 33 ms); max frame; p99 and p50 (nearest rank, as the runner computes them); fps;
  - launch to first frame: the runner's process start mark to the game.log line `Native presentation: frame=0`;
  - first frame to title (the draw-count switch, 0-1 to 8 draws) and launch to title;
  - title max: the max frame from 2 s before to 5 s after the switch;
  - o20 5s+: frames over 20 ms after 5 s, flagged `noisy` above 20;
  - ff->win s: the start of the runner's scored window on the frame clock, flagged `win<60s` if it starts early. It checks the floor; it is not a load-phase metric;
  - perf.csv as a cross-check, flagged `perf_mismatch` if it disagrees.
- **Left out of the arm numbers:** cold, short, no frames, no title, light phase (fewer than 30 INSTALL*.DAT FAILED lines), status not OK, and any runner excluding flag except `window_before_floor`, which is about the scored window.
- **Comparison:** each arm gets median [min..max]. Each arm is compared with `--ref` by the difference of medians and an exact two-sided permutation p on the rank sum.
- **Self-checks:**
  - perm p: 0.0079 for a fully separated 5v5, 0.1 for 3v3, 0.0286 for 4v4, and 1.0 when every value ties;
  - arm/rep parsing works;
  - Agent 8's fake-bin selftest runs come out as `short no_title light_phase`;
  - a path with no runs exits 1.

### Test runs (03:31; `--ref n0`)

Window-3 n0 = native2-bin, frontend off, uncapped, quiet user window (`build/agent8/matrix/20261122-0013`).

| run | launch->ff s | ff->title s | title max ms | o33/o50/o100 | max ms | p99 ms | o20 5s+ | ff->win s | note |
|---|---|---|---|---|---|---|---|---|---|
| 0016-cold-n0 | 12.97 | 31.03 | 14.7 | 3/1/1 | 154.4 | 10.53 | 0 | 31.4 | cold (excluded) |
| 0030-n0-r1 | 12.74 | 31.18 | 12.9 | 4/1/1 | 117.9 | 10.00 | 0 | 65.2 | |
| 0042-n0-r2 | 13.58 | 30.97 | 16.0 | 3/0/0 | 49.5 | 12.01 | 1 | 79.7 | |
| 0054-n0-r3 | 13.20 | 30.94 | 13.8 | 3/2/1 | 117.0 | 10.08 | 2 | 65.7 | |
| 0104-n0-r4 | 17.17 | 30.63 | 14.0 | 3/2/1 | 119.1 | 11.10 | 0 | 53.0 | window 3 had no floor |
| verify3b 2346-n0-r1 | 16.02 | 31.48 | 36.8 | 32/3/1 | 294.2 | 29.61 | 295 | 41.1 | busy |
| S3 0205-n1-r1 | 20.87 | 32.40 | 70.2 | 88/21/0 | 86.8 | 34.50 | 234 | 30.4 | hidden desktop |
| S3 0208-n3-r1 | 15.87 | 32.07 | 31.8 | 27/8/1 | 119.8 | 23.55 | 117 | 30.2 | hidden desktop |
| S3 0210-n2-r1 | 13.26 | 32.55 | 41.5 | 39/8/1 | 130.7 | 23.02 | 112 | 30.4 | ff from tail (no frame=0 line) |
| 0256-native3 | 14.38 | 31.61 | 27.2 | 2/1/1 | 261.4 | 17.86 | 44 | - | boot run, cap 240, 94% busy |

Every run had 34 INSTALL*.DAT FAILED lines, no perf mismatch, and draws 0 to 8.

### Findings

- **Quiet load phase:**
  - Every frame over 33 ms falls in the first 1.4 s: a startup burst with a 117-119 ms spike at 1.1-1.4 s. Each run compiles its PSOs fresh.
  - After 5 s the max frame is 13.5-25 ms.
  - Around the title switch the max is 12.9-16.0 ms, so on native2-bin the title's first-use uploads cause no hitch.
- **Title switch:** 30.63-31.48 s after the first frame (SD about 0.3 s), even on a busy machine (0256: 31.61). The S3 threaded variants were 1.1-1.6 s later. It follows a timed intro, so upload speed should not move it.
- **Window placement:**
  - On the frame clock, the S3 runs started their windows 0.2-0.4 s after settle + warm-up (30.2-30.4 s for a nominal 30). The wall clock agrees: start mark to measure start = launch-to-first-frame + 30 + 0.3-0.5 s.
  - So settle 50 + warm-up 10 puts the window about 60.3 s after the real first frame.
  - Window 3's older runner started windows 13-40 s late (53-80 s for a nominal 40).
  - `first_frame_signal_s` is not counted from the process start mark: it reads 3-5 s below the game.log first frame on S3, and -4..+9 s off on window 3. Don't compare it with launch times. (My working note "windows start 55-69 s after the first frame" was wrong and was never sent.)
- **Noise:** busy runs give 27-88 frames over 33 ms and 112-295 over 20 ms after 5 s. Quiet runs give 3-4 and 0-2. The user window needs an idle machine.
- **No upload-volume data in timing runs:** `texture_ms`, `texture_hash_bytes`, `pipeline_creations` and `detailed_timing_enabled` are 0, and perf.csv `draw_calls` is 0 on native runs.

### Expected results and separability

- **u0:** the window-3 n0 pattern: o33 3-4, o50 0-2, o100 0-1, max 50-154 ms (startup), p99 10-12 ms, title max 13-16 ms, first frame to title about 31 s, launch to first frame 12.7-17.2 s. native3-bin with the frontend on may shift the absolute values.
- **u1** (the old CPU paths, same output bytes):
  - Load phase: a bigger startup burst, and maybe frames over 20-33 ms at the title switch. At 5v5 it separates from u0 only if the effect is large and consistent, for example 2 or more extra frames over 33 ms, or a title max above 20 ms, in every run. First frame to title should not move.
  - Scored window: a tie, unless the attract loop streams textures.
- **u2** (the staging pool): a tie with u0 on every load-phase and window metric. Saving one createBuffer per staged upload is far below the run-to-run noise. A tie is the useful answer: there is no speed reason to turn the pool on by default. Its checks are functional: the pool lines, commit (64 MB idle at most, plus power-of-two rounding), no corruption, and `allocate-map-stage` in Agent 8's s2-vs-s0 diagnostic.

### Corruption checks (Agent 8: nobody watches the screen)

- A staging buffer reused before its copy retired would draw wrong textures with no log line. Only a person or a screenshot can rule that out.
- Per-run log counts (game*.log). Each must be 0, or the same in u2 as in u0:
  - `texture upload allocation failed` (`textures.cpp:2446`);
  - `texture allocation failed` (`textures.cpp:1107`);
  - `failed to allocate` (`buffers.cpp:467`);
  - `cannot wait for submission after device removal` (`device.cpp:657`);
  - `Native texture binding:` and `Native texture binding totals: unavailable= upload_rejected= view_lost=` (`draw.cpp:928/932`; the first 32 distinct problems, then totals every 4096).
- The pool lines `Native texture staging pool: enabled, 64 MB idle budget` (`textures.cpp:198`) and `... hits= misses= idle_bytes= idle_buffers=` (every 256 acquires, `textures.cpp:217`) must appear in u2/s2 only.
- Baseline: 0 `[error]` lines and 31 non-INSTALL `[warning]` lines in both `0030-n0-r1` and `0256-native3`.
- `Native texture watch stale` fires only with the texture-watch audit on, so it doesn't help here.

## Session 3, task #20: S4, the memcpy on the devoff GPU Commands thread (05:00-06:31)

Task (Agent 1, ~05:00): name the callers of the memcpy that the devoff profiles put on the GPU Commands thread, size the bytes per frame and how much of it is needed, and rank proposals. Analysis only. Agent 1 (05:45, 05:58): one combined entry with Agent 12's #21, counted once. Agent 12's full design text, output-identical argument and Agent 10 checklist are in `perf-notes/agent12-io-memory.md`, "S4 (#21)" (S4.4 P1, S4.7 race); they are summarised here, not repeated.

### S4.0 Summary

- **Who copies:** `D3D12SharedMemory::UploadRanges` (`graphics/d3d12/shared_memory.cpp:304-339`, memcpy at :328) copies guest vertex buffers into the D3D12 upload heap. Every sampled copy comes from the vertex-buffer `RequestRange` in `IssueDraw` (`graphics/d3d12/command_processor.cpp:2848`). Memexport and textures have 0 samples.
- **Why every frame:** the game's buffer Lock calls `MmSetAddressProtect` on the whole buffer with READWRITE (0x4) or READWRITE|WRITECOMBINE (0x404). `PhysicalHeap::Protect` treats any protect that includes Write as a CPU write: it invalidates and unwatches the whole range in SharedMemory, so the next draw re-uploads and re-arms the whole buffer, whether the game wrote it or not. The protect itself never changes host access (`ToPageAccess` ignores WC); only the invalidation bundled with it does work.
- **Cost (slow state):** UploadRanges 3.64 (a) / 3.85 (b) ms/f of GPU Commands' 8.43 / 9.42 (memcpy 3.09 / 2.91, re-arm 0.54 / 0.94). The protects cost Main 0.54 / 1.02 ms/f.
- **Bytes:** at most 3.76 MB/frame (a-vol, S4.8): the lock-time invalidated volume, 3847 KB per frame on average, almost all from one 3844 KB buffer locked whole about once per frame. My earlier estimate was 3-9 MB/frame.
- **Proposal:** C1 = Agent 12's P1 (`physical_protect_keep_watch`, default OFF): keep the watches on protects that don't change access. It saves up to u x 3.64 / 3.85 ms/f on GPU Commands plus 0.54 / 1.02 on Main, where u is the unchanged share of the re-uploaded bytes (defined once in S4.8, as in Agent 12's diagnostic; C1 uses u_block). If u is low, write faults and 256 KB neighbour invalidations replace the bulk invalidation (sized in S4.5). Next: Agent 12's P2 (one G hold per re-arm), then my M1 (non-temporal copy).

### S4.1 Callers

Host side (RVAs in `rexgpu-xenos.dll`; the devoff2 DLL's .text is identical to native3's):

| RVA | Function | Source |
|---|---|---|
| fn_11930 | CP worker | |
| fn_11F40 | ExecutePrimaryBuffer | |
| fn_130F0 | ExecutePacket | |
| fn_13B50 | ExecutePacketType3 (fn_133F0 = ExecuteIndirectBuffer) | |
| fn_157C0 | DRAW_INDX | |
| fn_166A0 | ExecutePacketType3Draw | |
| fn_B8070 | IssueDraw | `d3d12/command_processor.cpp`, VB RequestRange at :2848 |
| fn_428F0 | RequestRange | `graphics/shared_memory.cpp` |
| fn_41F30 | RequestRanges | `graphics/shared_memory.cpp:360-489` |
| fn_F3B40 | D3D12SharedMemory::UploadRanges | `d3d12/shared_memory.cpp:304-339`, memcpy at :328 |
| fn_11200 / fn_10E40 | memcpy (vcruntime) / rep movsb stub | |

- 100% of the upload samples return to 0xB92D8 (a 47, b 47) or 0xB911B (a 2, b 4). Both are the VB RequestRange at :2848.
- Re-arm: MakeRangeValid fn_41B10 (`shared_memory.cpp:303-336`) -> EnablePhysicalMemoryAccessCallbacks (`system/xmemory.cpp:702-711`) -> VirtualProtect read-only on the A/C/E views.
- `vertex_buffers_in_sync_` is cleared at IssueSwap (:2194-2195) and by InvalidateAllVertexBufferResidency (:377-379), so the VB RequestRange runs again every frame. It uploads only invalid pages, so the invalidations decide the volume. ReportSlowFrame runs once per swap (:2193).

Guest side (`rexlego/generated/default/legodimensions_recomp.N.cpp`): main loop sub_82FEB7B8 -> sub_82AB2040 -> sub_82B79938 -> sub_82CBC968 -> sub_82CBC020 (166.cpp:8849) -> sub_82B590E8 -> sub_82B55588 -> sub_82BD2808 -> sub_83F9F4D8 (87.cpp:36256; returns if the size is 0) -> `__imp__MmSetAddressProtect`.
- **sub_82B590E8** (160.cpp:7097), buffer Lock by handle: takes one of 32 critical sections (handle & 31); entry = table[handle-1] (52-byte entries); calls sub_82B55588(entry, 1, flags, -1); then polls up to 80 times until the GPU fence is more than 2 past the entry's fence (entry+48), unless flags & 0x1000 (D3DLOCK_NOOVERWRITE) or entry+24 & 0x80; returns the data pointer at entry+28.
- **sub_82B55588** (18.cpp:7192): Lock CAS-sets bit 30 of entry+4 and calls sub_82BD2808(entry+0, the whole buffer when r6 < 0, flags from entry+24 and the lock flags, 1). Unlock calls it with (e24>>4)|(flags&0x200), then clears bit 30.
- **sub_82BD2808** (397.cpp:7481): returns if the size is 0; skips the protect when flags & 0x8 and not flags & 0x200; otherwise calls MmSetAddressProtect(addr, size, flags & 0x10 ? 0x404 : 0x4). **So the protect is always PAGE_READWRITE, with or without WRITECOMBINE, never read-only.**

### S4.2 Cost

Profiles `build/agent8/matrix/20261122-0357/runs/{0357-a-prof-r1,0401-b-prof-r1}` (a = devoff2, b = devoffB), window 70-220 s, 0.077385 (a) / 0.078485 (b) ms/f per sample. Both ran in the slow state (a-prof: mean 67.7 fps, p99 78 ms); at normal clocks the times are ~3-4 times smaller. Rows overlap; Agent 12's S4.1 has the full split.

| Item (ms/f) | a | b |
|---|---|---|
| GPU Commands busy | 8.43 | 9.42 |
| IssueDraw | 4.95 | 5.26 |
| RequestRange | 3.64 | 3.92 |
| UploadRanges | 3.64 | 3.85 |
| memcpy | 3.09 | 2.91 |
| MakeRangeValid re-arm | 0.54 | 0.94 |
| write-watch frames | 0.62 | 1.26 |
| of which the resolve path (fn_C0230 > fn_D6CB0 > fn_41B10) | 0.15 | 0.31 |
| Main thread total | 3.64 | 3.53 |
| Main: guest sub_82B55588 | 0.54 (7 samples: 6 VirtualProtect, 1 TriggerCallbacks -> fn_42920) | 1.02 (13 samples, all VirtualProtect) |

### S4.3 Mechanism, step by step

1. Lock -> sub_82BD2808 -> `MmSetAddressProtect(addr, whole buffer, 0x4 or 0x404)`.
2. `MmSetAddressProtect_entry` (`kernel/xboxkrnl/xboxkrnl_memory.cpp:484-501`): FromXdkProtectFlags (:47-61) maps READWRITE to Read|Write and WRITECOMBINE to WriteCombine, then calls `heap->Protect` without an old_protect pointer.
3. `PhysicalHeap::Protect` (`system/xmemory.cpp:2128-2144`): with Write in the protect, it calls TriggerCallbacks(exact range, unprotect false) -> `SharedMemory::MemoryInvalidationCallback` (`graphics/shared_memory.cpp:502-575`), which counts kMemoryInvalidate (+1 and + length, :509), clears the valid and valid_and_gpu_written bits (:561-562) and fires the texture watches (:571). TriggerCallbacks then clears the watch bits. Next, the parent's Protect and `BaseHeap::Protect` (:1713-1799) set the host pages RW (:1779-1781). SyncHostPageAccess returns at once for heaps whose pages are at least the host page size (:977-979).
4. The game writes. Nothing faults, because the range is host-RW and unwatched.
5. The draw: IssueDraw -> VB RequestRange (:2848) -> RequestRanges -> UploadRanges: a memcpy from guest physical memory (`TranslatePhysical`) into the upload heap (:328), a CopyBufferRegion into the shared-memory buffer, then MakeRangeValid -> EnablePhysicalMemoryAccessCallbacks -> VirtualProtect RO (the re-arm).
6. The next frame's Lock repeats steps 1-5.

`ToPageAccess` (`xmemory.cpp:930-941`) maps 0x4 and 0x404 to the same host access, so the protect in step 3 changes nothing by itself. The cost is the invalidation bundled with it, which covers the whole buffer however much of it the game writes.

**Not the cause: `clear_memory_page_state`.** It is false in the run toml (a-prof `legodimensions.toml` line 58, next to the exe; the installer forces it, `rexlego-installer/TomlConfig.cs:139`). My 05:22 claim that it caused the re-uploads was wrong and was retracted at 05:39, together with the use of Agent 6's fixture-slowframe logs (synthetic). SetSystemPageBlocksValidWithGpuDataWritten has no attributable samples (weak evidence: its copy is 16 KB per call, about 0.003 ms/f).

### S4.4 Bytes per frame, and how much is needed

- **From where to where:** guest physical memory, read through the host view (`TranslatePhysical`), into the D3D12 upload heap. The GPU then copies it into the shared-memory buffer.
- **How much:** no counter gives upload bytes. At ~1-3 GB/s in the slow state, the memcpy's 2.9-3.1 ms/f means ~3-9 MB/frame (estimate). a-vol (S4.8) bounds it: at most 3.76 MB/frame is invalidated, so at most that much is re-uploaded in steady state (first uploads aside).
- **How much is needed:** only the bytes that changed since their last upload, the share 1-u. Each Lock invalidates the whole buffer, so the unchanged rest, the share u, is re-uploaded and re-armed for nothing. u is defined once, in S4.8. Agent 12's logging-only diagnostic measures it (staged in `build/agent12/s4-diag/`, not built), so I don't duplicate it.
- **a-vol (no build):** `bench/agent5/matrix-s4-invalvol.json` (sha256 9D6A6F2C9C018293BD399FBA0F0E3EFCBB1E995661B662AD49F211FD00055A0B): devoff2-bin, framerate_limit=0, slow_frame_log_ms=1, warm-up 60 s from the first frame, settle 10, measure 150, sys.csv.
  - `bench/agent5/s4_slowframe.py <run dir>` reads the "cpu-write invalidations Nx K KB" field of each ReportSlowFrame line: kMemoryInvalidate's count and extra/1024, which the d3d12 cp reads and zeroes at every swap (`d3d12/command_processor.cpp:248-258, 274, 280`). With the 1 ms threshold every frame of 1 ms or more is logged, and #N gaps are counted.
  - What the counter counts: 1 per SharedMemory invalidation callback, plus its page-rounded requested length. A lock-time protect adds the whole locked range, a write fault 4 KB. TriggerCallbacks returns before any callback when no page of the range is watched (`xmemory.cpp:2306-2323`), so locks of buffers that weren't re-armed since their last lock add nothing.
  - Agent 12's falsification test: ~5-15 per frame confirms the chain, ~0 falsifies it. KB/frame bounds the volume this path re-uploads. Results go in S4.8.

### S4.5 Proposals, ranked and counted once

All are new cvars, default OFF. With the cvar off, the code path is unchanged.

| Rank | Item | Saving (slow state, ms/f) | Risk | Files |
|---|---|---|---|---|
| 1 | **C1 = Agent 12's P1**, keep the watches on access-unchanged protects | GPU Commands u x 3.64 (a) / 3.85 (b); Main 0.54 / 1.02; minus the costs below when u is low | medium | `system/xmemory.cpp/.h`, `graphics/shared_memory.cpp/.h`, `graphics/primitive_processor.cpp`; optional frame_stats ids |
| 2 | **P2** (Agent 12), one G hold per re-arm | alone 0.23 / 0.82; after C1, only the re-arms that are left | low | `graphics/shared_memory.cpp` |
| 3 | **M1**, non-temporal copy at :328 | at most (1-u) x 2.9-3.1 x 10-30% (unmeasured) | low | `graphics/d3d12/shared_memory.cpp` |
| 4 | **P3** (Agent 12), arm once per UploadRanges | only ranges over 2 MiB | low-medium | `graphics/d3d12/shared_memory.cpp` |
| 5 | **P4** (Agent 12), hot-range demotion | only if C1 is rated unsafe | medium | `graphics/shared_memory.cpp/.h` |
| 6 | **M2**, hash-skip of unchanged re-uploads | only if C1 is rated unsafe: at most u_page x memcpy, minus the hashing | medium | `graphics/d3d12/shared_memory.cpp`, `graphics/shared_memory.cpp/.h` |
| 7 | **G1**, game-side protect filter | fallback, only if an SDK change is refused | high | `rexlego/src/gpu_native/hooks_buffer.cpp` |

**Counted once:** C1 takes u of the UploadRanges bucket (memcpy plus re-arm) and Main's protect bucket. M1 can only speed up the (1-u) that C1 still copies. P2 only acts on the re-arms that are left. Together they can't exceed the UploadRanges bucket plus the resolve-path re-arms (0.15 / 0.31).

#### C1 (= P1): keep the watches on protects that don't change access

*Change* (Agent 12's S4.4 P1 has the full text): a fast path at the top of `PhysicalHeap::Protect`, under G and then both `heap_mutex_`. It only writes `current_protect` in the view's and the parent's page tables, so protection queries return what they return today: no TriggerCallbacks and no VirtualProtect. Otherwise the old path runs unchanged. All conditions must hold:
1. The cvar is on and `old_protect == nullptr`. MmSetAddressProtect (`xboxkrnl_memory.cpp:502`) qualifies. NtProtectVirtualMemory (:282) passes an old-protect pointer, whose value today comes from the parent's host VirtualProtect (`xmemory.cpp:2138`), so it keeps the old path.
2. Every page of the range, in the view and in the parent, is committed, in one region, and has `ToPageAccess(current_protect) == ToPageAccess(protect)` (here always RW -> RW).
3. No page of the range is `valid_and_gpu_written` in SharedMemory: there the old path's invalidation re-uploads guest memory over GPU-written data, so skipping it could change the output. SharedMemory registers a guard hook with its invalidation callback; PrimitiveProcessor (`primitive_processor.cpp:1364`) gets an always-allow hook; any callback without a hook forces the old path.
4. **New (mine, 06:05):** no page of the range has `provide_data` set (its data is still on the GPU).
   - Today `BaseHeap::Protect` sets such pages host-RW directly (`xmemory.cpp:1779-1781`). SyncHostPageAccess would keep them NoAccess (:1047-1054), but it returns at :977-979 for these heaps. So the guest then reads guest memory without the data being delivered.
   - C1 would leave them NoAccess, and the next access would fetch the GPU data first (:566-578): different bytes.
   - It is probably a subset of condition 3, but it costs one bit test per page.

*Output-identical argument* (short form; Agent 12's S4.4 states the invariant):
- If the game doesn't write a kept block before the next draw that reads it, the old path only re-uploads the same bytes, so skipping that is invisible. GPU-written and data-provided pages are excluded by conditions 3-4.
- If it writes, the first write to each watched block faults. `AccessViolationCallback` -> TriggerCallbacks(unwatch not exact, unprotect) (`xmemory.cpp:579-580`) invalidates and fires the watches before the write retires, so before the guest can submit the draw that reads it: the same ordering the lock-time invalidation gives. The fault path makes the page writable when `ToPageAccess(current_protect) == kReadWrite` (:2391-2394), so RW|WC pages don't fault forever.
- What changes: invalidation moves from lock time to write time, and it covers the 256 KB block around each written page instead of the exact locked range. SharedMemory widens to 256 KB, stopping at GPU-written pages (`shared_memory.cpp:531-551`). PrimitiveProcessor's unwatch range is its 256 KB bucket (`primitive_processor.cpp:1435-1440, 1559-1561`; `kCacheBucketSizeBytesLog2 = 18`). TriggerCallbacks unwatches the intersection (`xmemory.cpp:2342-2377`). Neighbours re-upload the same bytes, and the kMemoryInvalidate counts fall.

*Both sides (Agent 1, 05:58):*
- **Saving:** GPU Commands up to u x 3.64 / 3.85 ms/f (the whole UploadRanges bucket at u = 1, ~42% of busy); Main 0.54 / 1.02 ms/f (the lock-time protects, mostly VirtualProtect).
- **Cost, which grows as u falls:**
  - (a) Main: one fault per first write to each watched 256 KB block, F per frame, each ~10 us (Agent 12) to ~40 us (slow state: AV dispatch, G, the callbacks, FireWatches, one or more VirtualProtect). F <= written bytes / 256 KB + 1 per written range.
  - (b) GPU Commands: drawn but unwritten neighbour pages in the same 256 KB blocks re-upload (up to 256-512 KB per written range; ~0 for ranges that fill whole blocks).
  - (c) Texture re-decodes: the fault path fires the texture watches over the same 256 KB (`shared_memory.cpp:571`), while the lock-time call fires only the exact range.
  - (d) G hold: the fault path's VirtualProtect runs under G (`xmemory.cpp:2380-2414`), while today's lock path drops G before its two VirtualProtects (Agent 12's S4.7). GPU Commands' re-arms wait on G: F x ~2-10 us of extra hold per frame.
  - (b) and (c) are new, but still output-identical: the same bytes.
- **Worst case, u = 0** (every re-uploaded 256 KB block changed since its last upload): GPU Commands saves nothing and pays (b)-(d); Main nets 0.54 / 1.02 - F x 10-40 us. Break-even is F = 14-100 faults per frame. With 3-9 MB/frame in a few large buffers, F ~ 17-51 and Main lands between +0.85 and -1.5 ms/f. With many small buffers in separate blocks, (b) and (c) dominate.
- **Best case, u = 1 and no identical rewrites:** -3.64 / -3.85 on GPU Commands and -0.54 / -1.02 on Main, with no faults.
- **What a-vol tells us before any build:** count/frame = locks of armed buffers (the bulk calls C1 removes); KB/frame = the locked volume (the most C1 can save); F_max = KB/frame / 256 + count/frame; the mean locked size = KB/count.
  - F_max <= 13: C1 can't lose on Main even at u = 0.
  - F_max >= 100: turn C1 on only after Agent 12's u diagnostic shows u_block is high. Agent 12's guide: u_block >= ~0.5 saves 1.8 ms/f or more on GPU Commands, which pays for the faults; u_block <= ~0.2 saves little upload time, and C1 then rests on Main's lock-time savings.
  - Mean locked size under 256 KB: expect (b) and (c); watch the texture-load counts and upload bytes in the C1-ON run.
- **Knob, if (b) or (c) show up:** a size floor (fast path only for ranges of at least N KB; cvar, default 0). It only narrows the fast path, so it stays output-identical. A later option, C1b (not ranked): remember each kept range and invalidate exactly that range at its first fault (F <= count, no neighbours). It needs its own rating, because a page can become GPU-written between the protect and the fault.
- **Side effect:** it closes the S4.7 race for RW -> RW protects.
- **Verify mode (debug, optional):** at fast-path time, hash the kept range; at the next RequestRange that finds its pages still valid, hash it again. A mismatch means a bypass writer; log it once with the range.
- **Test plan:**
  1. The a-vol baseline (now).
  2. Agent 2 builds C1 and P2 (both OFF) with counters: protects kept, fault invalidations and their bytes, upload bytes and chunks per frame (Agent 12's S4.6).
  3. Functional C1-ON runs (title, Agent 3's menu walk, one level load) with `--slow_frame_log_ms=1` and the verify mode. Pass: logdiff NEW 0, frame hash or screenshot matches, invalidations per frame down, texture loads per frame not up.
  4. Agent 8's ABBAAB pairs with a profile each, 60 s floor, sys.csv.
- **Agent 10 rates:** Agent 12's checklist (S4.4 P1, items 1-4: the bypass writers, including my list; the callback hooks; condition 3 and the old_protect restriction; no lock-time side effects beyond diagnostics), plus condition 4 (provide_data) and the RW|WC unprotect at :2391-2394.

Bypass writers (my audit; Agent 12 copied it into the checklist). Host code that writes guest physical memory through an unwatched view, without TriggerCallbacks, relies on the next Lock to invalidate:

| Writer | Where | Note |
|---|---|---|
| CP small writes | `graphics/command_processor.cpp` :315, :437, :1289, :1305, :1368, :1415, :1444, :1465; d3d12 occlusion query :426 | small; check whether any lands in a locked VB |
| XMA PCM output | `xma_context.cpp:337` | audio buffers |
| cheat_engine StoreValue | :419, :502 | debug only |
| rexlego PoolCopyHook memmove | `rexlego/src/gpu_native/hooks_buffer.cpp:197-198, 343-345` | replaces the guest pool copy (sub_82BD2868); its InvalidateCpuPhysicalMemory notifies only rexlego's own watch (`memory_watch.cpp:151-154`). Native path only (0 "CPU pool copy" lines in the devoff logs). The likeliest real risk |
| rexlego textures | rexlego `textures.cpp:3758-3760` | native path |

Covered: xfile reads (`xfile.cpp:266-296`), Alloc/Release/Decommit/Protect, guest writes through the fault path, memexport and resolve (`d3d12/command_processor.cpp` :3053, :3063; readbacks :3272, :3481, :3559, :3656, :3911-3915). rexlego also hooks the D3D VB/IB Lock functions (sub_83FC60D8, sub_83FC6128; `hooks_buffer.cpp:381-385`).

#### P2-P4 (Agent 12; text in `perf-notes/agent12-io-memory.md`, S4.4)

- **P2** (`shared_memory_single_hold_rearm`): keep G from MakeRangeValid through EnablePhysicalMemoryAccessCallbacks, and hold it once around FireWatches + MakeRangeValid in RangeWrittenByGpu. Releases per chunk go from 4 to 1. It removes ~3/4 of the wake samples: 0.23 / 0.82 ms/f. Low risk.
- **P3** (`shared_memory_batch_arm`): one arm per UploadRanges. It only helps ranges over 2 MiB.
- **P4** (hot-range demotion): only if C1 is rated unsafe. It removes the re-arm but can add memcpy.

#### My items (renamed so they don't collide with P2-P4)

- **M1, non-temporal copy** into the upload heap at `d3d12/shared_memory.cpp:328` (cvar, default OFF).
  - Output-identical: the same bytes, and the GPU copy is recorded in the same order.
  - The upload heap is write-combined, and vcruntime's memcpy uses rep movsb (fn_10E40), which may already stream. So the gain is unmeasured: at most (1-u) x 2.9-3.1 x 10-30%.
  - Test: a bench in `bench/agent5` (copy rate into a write-combined upload buffer, sizes from a-vol), then functional runs and ABBAAB.
  - Agent 10 rates: alignment and tail handling, and an sfence after the streaming stores, before the GPU can read.
- **M2, hash-skip** (only if C1 is rated unsafe): hash each range before the copy. If it matches the hash stored at the last upload, mark it valid and re-arm without copying. Output identity is only probabilistic (64-bit hash), so Agent 10 rates the collision risk. It reuses the hashing of Agent 12's u diagnostic. It saves at most u_page x memcpy (S4.8), minus the hashing; the re-arm stays.
- **M3, async copy worker:** not recommended. The copy follows the arm, so moving it to another thread widens the window in which a guest write lands in the copy, and it adds a busy thread in the slow state.
- **G1, game-side filter** in rexlego (hook sub_82BD2808 and skip access-unchanged protects): fallback only. Without conditions 3-4 and the `current_protect` update, it isn't output-identical.
- **Rejected:** narrowing the VB upload to the indexed span (it needs an index scan, and shaders may read outside it); my own counter item (Agent 12's u diagnostic and the P1 counters cover it).

### S4.6 Landing order and runs

Landing (from Agent 12):
1. Build C1 and P2 together, both OFF.
2. Turn on P2 first.
3. Turn on C1 after Agent 10's rating, the a-vol and C1-ON counter runs, and an A/B.
4. P3 only if the counters show uploads of several chunks.
5. P4 or M2 only if C1 is rated unsafe. M1 independently, after its bench.

Agent 8 runs:
- **Done:** a-vol (`matrix-s4-invalvol.json`), functional only, run by Agent 8 at 06:20-06:24 after Agent 12's OK of the parser (06:16) and mine (06:19). Results in S4.8.
- **After the build:** devoff vs devoff+P2 vs devoff+P2+C1.
  - Functional (title, menu walk, level load) with `--slow_frame_log_ms=1` and Agent 12's u diagnostic.
  - One profile per arm.
  - Timing as ABBAAB with the 60 s floor and sys.csv, in a user window only.

### S4.7 How this was tested

- Profile attribution, folded and raw, on the 0357 a/b/n-prof runs (scratch `upl_fold.py`, `rr_callsite.py`, `protect_fold.py`; `legodimensions.map` from n-prof).
- Disassembly of fn_42920 and the call sites (`dis_rva.py`); reads of the generated code (`legodimensions_recomp.{18,87,160,166,397}.cpp`); targeted source reads at the file:line refs above; the run toml.
- Re-check at 06:00-06:05 (single-file reads): ReportSlowFrame, MemoryInvalidationCallback, `frame_stats::Add`, AccessViolationCallback, TriggerCallbacks, SyncHostPageAccess, and PrimitiveProcessor's callback and bucket size.
- `s4_slowframe.py --selftest` OK; a format test on Agent 6's synthetic fixtures (305 frames each, gaps as expected; no evidence).
- `matrix-s4-invalvol.json`: JSON parses, LF, no BOM; `-PlanOnly` exit 0, 1 run, about 5 min, bin ok (MANIFEST.txt).
- 06:17: the u definition checked against Agent 12's `build/agent12/s4-diag/DESIGN.md` (u_page, u_block and the cost bounds) and its S4.6 formula. Agent 12 confirmed the parser and accepted condition 4 (06:16).
- 06:28: `s4_slowframe.py` extended: a run dir's rotated logs are read oldest first (game.N.log ... game.1.log, game.log), explicit files in the order given, with a count of index backsteps; it adds the texture-load fields, KB per invalidation, F_max, the top KB and count values and Agent 12's test. `--selftest` OK (it now covers a two-file rotation and the wrong order). Run on the a-vol run dir; outputs `build/agent5/s4/avol-70-220.json` and `build/agent5/s4/avol-0-70.json`.

### S4.8 u, and the a-vol results

**u, one definition** (Agent 1's fix, 06:14; the same as Agent 12's diagnostic, `build/agent12/s4-diag/DESIGN.md`): u is the unchanged share, the share of the re-uploaded bytes that are unchanged since that page's previous upload, so the GPU already has them. 1-u is the changed share, the only part that has to be re-uploaded.
- Agent 12's `shared_memory_upload_hash_log` (staged in `build/agent12/s4-diag/`, not built, default off; functional runs only, because its hashing adds ~1-3 ms/f) hashes every uploaded 4 KB page and logs per frame:
  - `u_page` = unchanged / (pages - first): the most any page-granular write-watch scheme could skip;
  - `u_block` = 1 - pages_in_changed_blocks / (pages - first): the same at C1's 256 KB fault granularity. **This is the u in every C1 formula in this entry:** C1 saves up to u_block x 3.64 / 3.85 ms/f on GPU Commands.
- Both are upper bounds: a rewrite with identical bytes counts as unchanged, but under C1 it still faults, invalidates its block and re-uploads.
- Window value: sum(unchanged) / sum(pages - first) over 70-220 s, weighted by pages (`bench/agent12/s4_uhash.py`), not the mean of the per-frame values.
- The same lines bound C1's costs: faults per frame from changed_blocks (lower) to blocks (upper); re-upload per frame from pages_in_changed_blocks (lower) to changed_blocks x 256 KB (upper).
- After the build, Agent 12's u = 1 - (upload bytes with P1 on) / (upload bytes with P1 off) (S4.6 of its notes) gives the realised share, net of the neighbour re-uploads (b).
- Correction: my 06:11 summary to Agent 1 said "only the bytes written after each Lock are needed; their share u is unknown". That share is 1-u, not u, and "written" should read "changed since their last upload".

**a-vol results** (Agent 8, 06:20:03-06:24:11, `build/agent8/matrix/20261122-0620/runs/0620-a-vol-r1`): devoff2-bin, framerate_limit=0, slow_frame_log_ms=1. Status OK, clean WM_CLOSE (exit 0 after 1.14 s), [error] 0, no dump. Functional only: hidden desktop, and sys.csv shows a slow state (eff 1219 MHz).
- The log rotated (game.1.log #2-#15196, game.log #15197-#26025), so `s4_slowframe.py` now reads a run dir's rotated logs oldest first.
- 25800 frames logged; 224 index gaps (frames under 1 ms, at most 0.22 s of the clock); no backsteps.
- Window 70-220 s after the first logged frame: 13160 frames in 149.98 s, 87.7 fps (Agent 8's runner: 13148 frames, 87.65 fps).

| per frame (70-220 s) | mean | p50 | p90 | p99 | max |
|---|---|---|---|---|---|
| invalidations (count) | 1.87 | 2 | 3 | 4 | 5 |
| invalidated KB | 3847 | 3848 | 3852 | 7696 | 7700 |
| frame ms | 11.4 | 6.0 | 28.2 | 62.9 | 128.7 |

- 329.7 MB/s invalidated; 6.0% of frames have no invalidation; memexport pages 0.
- The KB values cluster: 3848 KB in 65% of frames (count 2 in 66%), 3844 in 14%, 3852 in 6%, 7688-7696 in 7.3%, 0 in 6%, 4 in 1.3%.
  - So almost every frame has one lock of the same 3844 KB buffer (961 pages, the whole buffer), plus 0-2 events of 4 KB (a write fault or a small lock; this counter can't tell which).
  - Frames with two big locks balance the frames with none: the game locks it about once per game frame, not once per swap.
- KB per invalidation: 2057.5, the mix of 3844 KB locks and 4 KB events. It is far from ~4 KB, so the volume is lock-driven, not fault-driven.
- F_max = 3847 / 256 + 1.87 = 16.9 per frame.
- Texture loads (the baseline for cost (c) in the C1-ON run): 0.02 ms per frame on average; the count field is 1 in every frame.
- Frame ms in the lowest vs the highest KB quartile: 10.5 vs 11.7.
- Boot and title (0-70 s): 178.9 fps; 1.59 invalidations and 2760 KB per frame (15% of frames with none; max 15936 KB); F_max 12.4.

**What it means:**
- **Agent 12's test:** not falsified (mean 1.87, p50 2), and the chain holds. But the count is below the expected 5-15 per frame: the volume comes from one large buffer locked whole about once per frame, not from many small ones.
- **Volume:** at most 3.76 MB per frame is invalidated, so in steady state at most that much is re-uploaded (first uploads aside).
  - That is inside my 3-9 MB/f estimate and 4-8 times below the 15-30 MB/f in Agent 12's DESIGN.md; its hashing-cost estimate (+1-3 ms/f) scales down with it.
  - With the a-prof memcpy time (3.09 ms/f; another run, also in a slow state), the copy runs at no more than ~1.2 GB/s.
- **C1's decision rules (S4.5):** F_max 16.9 lies between 13 and 100.
  - At u = 0, Main nets 0.54 - 16.9 x 10-40 us = +0.37 to -0.14 ms/f (a) and +0.85 to +0.34 (b). That is at worst a small loss on Main, and a gain unless a fault costs more than ~32 us (a) / ~60 us (b). Cost (d) adds at most 16.9 x 2-10 us = 0.03-0.17 ms/f of G hold.
  - So there is no reason to wait for the u diagnostic before building C1 (OFF) with its counters. u_block still decides the GPU Commands saving.
- **Neighbours:** the locked range is 3844 KB, far above 256 KB, so costs (b) and (c) are small: at most the 2 edge blocks per written range. The texture-load numbers above are the reference for (c).
- **What u will show:** if the game appends to this buffer as a ring (writing only part of it per frame) while the draws fetch the whole buffer, u_block is high and C1 saves most of the 3.64 / 3.85 ms/f. If it rewrites all 3.75 MB every frame, u_block is ~0 and C1 gives only the Main side. Agent 12's u diagnostic tells which.

### s-rows of the original uploads matrix (Agent 8, 04:38-04:51)

Matrix `build/agent8/matrix/20261122-0438` (runs 0439-cold-s0, 0441-s0-r1, 0444-s1-r1, 0447-s2-r1): idle machine, functional only, no sys.csv.
- All 4 are OK: exit 0, clean WM_CLOSE in 0.6-1.1 s, window 60.0 s after the first frame, no flags. [error] 0 and non-INSTALL [warning] 31 in all 4 (the baseline); native_fps_limit_cvar 0 in every row; the six grep strings 0.
- The pool line ("Native texture staging pool: enabled, 64 MB idle budget") is in s2 only. It comes from init (`textures.cpp:3329/3336`).
- No "hits=" line in any run. It is printed every 256 pooled acquires (`textures.cpp:209-221`), not at shutdown, so fewer than 256 acquires went through the pool. It is evidence neither for nor against the pool.
- Slow ops: no texture-upload op crossed the 4.0 ms threshold (`slow_operation.h:37`; only cold s0 has one, pool-copy 5.55 ms), so decode-content-hash vs allocate-map-stage can't be compared.
- Frames in the first 30 s from row 0: s0 1 frame over 33 ms (max 90 ms), s1 1 (max 300 ms, the bigger legacy startup burst), s2 4 (max 111 ms), cold s0 2 (max 742 ms).
- Scored window (60-180 s): fps 109 / 94.6 / 110, p99 23.9 / 42.3 / 23.3 ms, frames over 33 ms 30 / 241 / 27. s1 is worse in this single run, but n = 1 and there is no sys.csv, so the slow state isn't ruled out. Expected for uploads-45 or x5: u2 ties u0; u1 vs u0 is small, and a tie is valid.

### x5 uploads matrix: u0/u1 x5 (Agent 1, 05:31 and 06:14; a new file, plan-only check, not run tonight)

- `bench/agent5/matrix-native-uploads-x5.json`, sha256 62F58F2BDC259CBA27B09FAD051E1817293AFEE35ED2A94981730FCF3DB340AA (8802 bytes, 13 notes; ASCII, LF, no BOM).
- It is the two-arm cut of uploads-45: its u0 and u1 arms byte for byte, and every other key the same (native3-bin; native_fps_limit=0 framerate_limit=0; settle 50 + warm-up 10, the 60 s floor; 60 s windows; sys_csv on; cold run on). u2 is left out: it is expected to tie u0, and s2 passed its functional checks. The script that wrote it asserts all of this.
- Why: in the s-rows above (n = 1, no sys.csv), s1 (u1) was worse than s0 in the scored window. x5 repeats u0 vs u1 five times each, interleaved (u0 u1 | u1 u0 | u0 u1 | u1 u0 | u0 u1), with sys.csv on, so a slow CPU state gets flagged.
- `-PlanOnly` (06:14; both exit 0): 11 runs (1 unscored cold u0, then 5 rounds), about 28 min; with `-Repeats 4`, 9 runs, about 23 min (smallest exact p 0.029, against 0.008 at 5 v 5). sys.csv ON, native3-bin ok (MANIFEST.txt), no SKIP. The FATAL line ("legodimensions.exe is running") only reflects the game that was running then; PlanOnly starts nothing.
- Expected: u1 worse in all 5 runs if s1's deficit is real (exact p 0.008), otherwise a tie, which is also valid. The load phase (`load_phase.py`) separates them only if the effect is large and consistent. The corruption and log checks are in the matrix notes.
- uploads-45 (114A0242...) and the original (15BB7822...) are unchanged. Not scheduled: Agent 1 decides when it runs, and not tonight.

### S4 M1 staged (task #7, board run 2, 13:05-13:30)

- **Diff:** `build/agent5/s4-m1/m1-nontemporal-copy.diff`, sha EBECE86E68369C88464F5837ED4882680E712184273FE61F802CD939CEBF30CD (5589 B, LF), 5 hunks, +72 -3.
  - It is against SDK `src/graphics/d3d12/shared_memory.cpp` **after #7**: base BB0838CE..., which is live B120D07C... plus `build/agent12/s4-diag/upload-hash-log.diff` (D2905301...).
  - Result: `new/shared_memory.cpp`, 2A5ADF13B5E433F1F10B5C6AF9C14F8812527C4E155A5146B166723457B6EBB4 (24190 B).
  - Hashes and checks are in `build/agent5/s4-m1/HASHES.txt`; the switch, change and test plan are in `NOTE.md`.
- **Switch:** `shared_memory_upload_nontemporal_copy`: bool, default false, GPU/D3D12, hot reload, read once per UploadRanges call. This is the name missing from S4-DRAFT row 11 (L347).
- **Code:**
  - A helper, `CopyToUploadBufferNonTemporal`, in the anonymous namespace. On x86-64 it does a plain head copy up to dst's next 64-byte boundary, then 64-byte steps of 4 x `_mm_loadu_si128` + 4 x `_mm_stream_si128`, then a plain tail of size % 64, then one `_mm_sfence()`. Elsewhere it is `std::memcpy`.
  - The call site keeps the original memcpy in the else branch.
  - In practice only the body runs: dst is 4 KB-aligned and the size is a multiple of 4 KB.
- **Checks (13:13-13:26):**
  - Scratch applies, outside any work tree, with `git -c core.autocrlf=false apply`:
    - live + #7 = BB0838CE (= Agent 12's new);
    - live -> #7 -> M1 = new, byte for byte;
    - M1 --check on base: OK;
    - M1 on live without #7 doesn't apply (expected).
  - #7 --check on the live SDK (c5fe668): OK.
  - Syntax-only clang (`bench/agent5/s4m1_syntax.ps1`, Agent 12's method: dev-SDK Release flags, PCH dropped): base exit 0, new exit 0, 12 diagnostics each (the same header warnings), no new diagnostics, RESULT: PASS. Report `build/agent5/s4-m1/syntax-20261122-132054.txt` (AA8952C4...). The machine was loaded, so the compiles took 250 s and 42 s.
- **Tools:** `bench/agent5/s4m1_mkdiff.py` (stages orig/base/new, makes the diff, runs the chain checks) and `bench/agent5/s4m1_syntax.ps1`.
- **Gain:** not measured.
  - a-prof's copy rate (≤ 1.2 GB/s, ~1 byte/cycle in the slow state) is low enough that the store pattern may matter.
  - The S4.5 bound stays: at most (1-u) x 2.9-3.1 ms/f. Plan on 10-30% of that until the microbench in NOTE.md's test plan says otherwise.
- **Order:** S4-DRAFT L166 lists #9 P3 before #11 M1 in this file. If P3 lands first, M1's UploadRanges hunks need a rebase.
- Sent to Agent 10 for rating (alignment/head, tail, sfence placement) and to Agent 11 for the switch name.

### C1 call (task #7, board run 2, 13:44-13:53)

**Call: A/B.** u_block = 0.934 over the 70-220 s window. S4-DRAFT row 4's rule is no-go below 0.1 and A/B at 0.25 or more, so this clears the bar by far. The value holds in every part of the run, so no window choice changes the call.

- **Run:** Agent 3's `build/agent3/runs/20261122-133730-s4a-udiag`, 13:37:30-13:43:04 (333 s).
  - Bin and switches: devoff4-bin (S4a), `shared_memory_upload_hash_log = true`, `slow_frame_log_ms = 1`, `framerate_limit = 0`, no input script.
  - Outcome: closed by WM_CLOSE, exit 0, 0 errors, 40 warnings.
  - Functional only (hidden desktop). Title scene: 226 draws / 1022 vertices for 294 s, on the NVIDIA GeForce MX570.
- **Parser:** `bench/agent12/s4_uhash.py <run dir>`, which weights the window sums by pages. I ran it read-only at 13:44 as a cross-check.
  - Input: 9 logs (game.8.log ... game.log), 75013 S4 lines.
  - First slow-frame index 2: no logs were lost, so the time base holds.
  - **Agent 12's own reading (13:50) agrees:** u_block 0.9336, the same as mine. See the confirmation at the end of this section.

| window (s) | frames | KB/f uploaded | u_page | u_block | blocks/f | changed blocks/f | C1 re-upload KB/f |
|---|---|---|---|---|---|---|---|
| 0-70 (boot, title) | 19422 | 2770 | 0.9983 | 0.949 | 12.3 | 1.18 | 140-302 |
| **70-220 (the S4 window)** | 32787 | 3844 | 0.9983 | **0.934** | 16.7 | 1.59 | 255-407 |
| 220-end | 22803 | 3844 | 0.9983 | 0.934 | 16.7 | 1.59 | 255-408 |

- **Per frame, 70-220 s:**
  - u_block p10/p50/p90: 0.932/0.933/0.934.
  - 2.03 UploadRanges calls (and ranges) per frame.
  - 961 pages: the 3844 KB buffer that a-vol saw locked whole about once per frame.
  - First-upload share 0.
- **What it means:** this is the ring case from S4.8.
  - Per frame, the game changes about 1.6 pages in about 1.6 of the buffer's 17 blocks of 256 KB.
  - The lock-time protect still makes the whole 3844 KB re-upload every frame.
  - C1 keeps the watch over the lock, so only the written blocks fault and re-upload.
  - This also fits a-vol's "one 3844 KB lock + 0-2 events of 4 KB" per frame.

**Expected effect.** These are upper bounds: an identical rewrite counts as unchanged here, but still faults under C1. The ms figures come from S4.2's slow-state profiles (a = devoff2, b = devoffB); at normal clocks they are ~3-4 times smaller.
- **GPU Commands:** saves up to u_block x 3.64 / 3.85 = **3.40 / 3.59 ms/f**. Block widening raises the re-upload to 255-407 KB/f (against 3844 today), which gives 3.25-3.40 / 3.44-3.59.
- **Main:** the lock-time protects (0.54 / 1.02 ms/f) go away, and the faults come back at F x 10-40 us each.
  - F runs from 1.59 per frame (changed blocks, lower bound) to 16.7 (all blocks, upper bound).
  - Net at the lower F: +0.48 to +0.52 (a) / +0.96 to +1.00 (b) ms/f.
  - Net at the upper F: +0.37 to -0.13 / +0.85 to +0.35, the same as S4.8's u = 0 figures.
  - With Agent 12's 5-15 us per fault, the faults cost 0.01-0.25 ms/f.
- **Cost (d), the G hold:** F x 2-10 us = 0.003-0.17 ms/f.

**What the call sets in motion** (per S4-DRAFT; nothing more is built tonight, because builds ended at 14:00):
- **S4b goes ahead** as the one full rebuild: ~37-46 min, +3-4 min with the regen.
  - Contents: C1 v2, applied on top of S4a as `keep-watch.diff` alone and then the rexlego diff (b2r §28); #26 bundled; whatever else is rated by then.
  - native3d and nativeB are re-pinned after the apply.
- **C1 v2 is now needed** (Agent 12, ~20-30 min). It comes after window 4 and P2's fallback counter, and before S4b. Agent 10 rates the v1 -> v2 interdiff.
- **Before any ON run:** §21 A-D, with #5 ON (gate B is enforced in code) and both cvars set at launch. Gate A needs a level load, which needs Toy Pad figures or the user.
- **W6 runs its full form:** s0 / #8 / #8 + #5 / #8 + #5 + #4, 13 runs, ~33 min.
  - Realised u = 1 - (upload bytes with C1 on / with C1 off) (Agent 12's S4.6).
  - v2's kept-protect counter is read per frame.

**Caveats:**
- **Title screen only** (no input script). A level with figures may write more of the buffer per frame. Gate A's level load gives the first in-game look; a u-diag run inside a level would settle it.
- **Identical rewrites:** if the game rewrites unchanged bytes, C1's realised share falls below u_block. W6's upload bytes and kept-protect counts will show it. Faults per frame tell which case applies: ~1.6 means the ring, ~17 means a full rewrite.

**M1 (#11) after this call:**
- If C1 delivers, only 255-407 KB/f is left to copy. M1's bound then falls from 2.9-3.1 ms/f to ~0.2-0.3, or to at most 0.1 at the 10-30% planning figure.
- So M1 moves behind C1. It stays staged as the fallback if C1 fails its gates, and for scenes that write more of their buffers.
- Its rating can wait until after C1 v2's interdiff.
- Its microbench is staged too: `bench/agent5/m1_copybench.cpp` (AA313906..., 715 lines). Syntax PASS at 13:43: 0 diagnostics, and the helper text matches `new/shared_memory.cpp`. The report is `build/agent5/s4-m1/copybench-syntax-20261122-134316.txt`, and the files are listed in HASHES.txt. Not built or run.

**Agent 12's confirmation (13:50; `build/agent12/s4/uhash-devoff4.txt` and `.json`):**
- u_block 0.9336 (pages-weighted, 70-220 s, 32787 frames), the same as my cross-parse. Per-frame p10/p50/p90: 0.932/0.933/0.934.
- It holds across the run:
  - Sub-windows 70-120 / 120-170 / 170-220 s: 0.9336 / 0.9336 / 0.9335.
  - Fifteen 10 s buckets: 0.9335-0.9337. 220-330 s: 0.9336.
  - Only boot differs: 0-30 s gives 0.986-0.990 at 1.4-1.8 MB/f.
- The CPU slow state from 107 s doesn't move u: the buckets before and after it match.
- The other figures match the table: u_page 0.9983, first-upload share 0, 3844.2 KB/f and 961 pages/f (all re-upload), 1.59 changed and 16.67 touched blocks/f, C1 re-upload 255-407 KB/f (89-93% less).
- Fault cost at 8 us each: 0.013-0.133 ms/f. At 15 us: 0.024-0.25 ms/f.
- **Call unchanged: A/B.**

### Task #18 (board run 2, 14:02-14:25): M1 correctness gate, W6 draft, C1 v2 read

**M1 correctness gate: PASS.** This was a functional check with no timing, and it is Agent 10's condition before M1 is ever ON (b2r row 34, §33 addendum).
- **Bench:** `bench/agent5/m1_copybench.cpp` gained `--check-only`, which allocates no rate buffers, runs no rate part and prints one PASS/FAIL line per case group.
  - The source is now F98B935A… (764 lines). The diff is `build/agent5/s4-m1/copybench-checkonly.diff` (41E6A488…, +83 -34), and the old version is in `bench-prev/`.
  - The helper's syntax re-check passed at 14:10: MATCH with `new/shared_memory.cpp` L189-L219, 0 diagnostics.
- **Build:** one single-file clang++ compile at BelowNormal through `bench/agent5/m1_copybench_check.ps1` (DF475848…).
  - Command: `toolchain\llvm-23.1.6\bin\clang++.exe -std=c++23 -O3 -march=x86-64-v2 -fno-strict-aliasing -fms-runtime-lib=dll bench\agent5\m1_copybench.cpp -o build\agent5\m1_copybench.exe`.
  - Result: exit 0, 0 diagnostics. The exe is **92C5FF6E201DBEE1…** (40,960 B).
- **Run:** `build\agent5\m1_copybench.exe --check-only` exited 0 in 7.9 s. It used adapter 0, the NVIDIA GeForce MX570. The upload heap is WRITE_COMBINE, pool L0.
  - **Normal memory: 22/22 groups PASS.** 4 source offsets (0/1/15/33) × dst 0-63 × sizes 0-300, plus 7 large sizes (4095, 4096, 4097, 65553, 2 MiB, 2 MiB + 33, 3,936,256) × dst 0/1/16/63 × src 0/1. Each group ran with guard bytes 0xCD and 0x32: 154,224 cases, 0 failures, 0 skipped.
  - **Upload buffer: 18/18 groups PASS.** Source offsets 0/1 and the same large sizes, both guards: 77,168 cases, 0 failures, 0 skipped.
  - Result line: `# RESULT: PASS`.
- **Report:** `build/agent5/s4-m1/copybench-check-20261122-141100.txt` (2B5E54B7…). Hashes are in `HASHES.txt`, keys `bench18`, `cdiff`, `bsyntax18`, `checkps1`, `exe` and `check`. NOTE.md test plan steps 1-2 are updated.
- **Not done:** the rate part. The machine was loaded, so no GB/s number would be valid. Next for M1 is the OFF/ON functional pair. M1 comes after C1, and needs a rebase if P3 lands first.

**W6 draft:** `build/agent5/w6-draft/`, for Agent 8 after W4b.
- **Matrix:** `matrix-w6.json` (2B75DFDE…) uses window 4's format and timing keys. Validated: it parses, has the same keys as `matrix-window4.json`, and that file is unchanged at 6CA4AC6E….
- **Arms:**
  - s0 = framerate_limit=0 only;
  - p2 = + `shared_memory_single_hold_rearm`;
  - p2f = + `physical_protect_hold_global_lock`;
  - p2fc = + `physical_protect_keep_watch`, with `physical_protect_keep_watch_verify=false`.
- **Bin:** the placeholder `build/agent2/S4b-bin-TBD`.
- **Run:** `-Only s0,p2,p2f,p2fc -Repeats 3 -ColdShared -NoPrompt` = 13 runs, ~33 min.
- **README:** `README.md` (FB96C21D…) covers the gates, the read-out, the expected effect and the caveats.
- **Upload KB/f:** two untimed side runs, p2f and p2fc, each with `shared_memory_upload_hash_log=true` and `slow_frame_log_ms=1`, parsed with `s4_uhash.py`. Realised u = 1 − ratio of the two. The same runs give P2's full-buffer counter (gate 4) and p2fc's kept count.
- **P2's counter is not a KB/f source.** It counts full-buffer memexport fallbacks. The slow-frame line's `cpu-write invalidations … KB` field is the in-log cross-check.

**C1 v2 (item 3):** I read `build/agent12/s4-c1v2/NOTE.md` and `v1-to-v2.diff` against my C1 design and found nothing off.
- Watches are kept only under fix (i)'s double G hold (gate B, in code). The OFF path is unchanged. The counter and the first-kept and init lines give gate D and gate A's positive control.
- Agent 10's rating (row 35, §34) agrees: SAFE at the default, ON SAFE to test. The test rule is to set both cvars at launch and never touch them mid-run. Agent 12's init latch comes before default-ON.

## Task #27: overnight launcher (in progress; checkpoint 16:58 before the agy-grid restart)

Status: reading is done; nothing written yet in `bench/agent5/launch/`. No commands have been run (W5 rule: file tools only until 'go').

Inputs read:
- `bench/agent8/run/` run-matrix.ps1 (all 731 lines), run-timing.ps1 (all), common.ps1, timing-env.ps1, README.md and matrix-window4.json.

What the runner loads, which is the pin set:
- run-matrix.ps1, which dot-sources common.ps1 and timing-env.ps1;
- run-timing.ps1, called in-process;
- winhelper.cs, through Add-Type in Import-LdHelper;
- drivers\sys-csv.ps1, when sys_csv is set;
- python frame_summary.py and sys_summary.py;
- the arm drivers. Find-Script looks in the matrix dir, then the run dir, then the repo root.

Pins: those files plus all `run/*.py`, `run/*.cs`, `run/drivers/**`, run-night.ps1 and RUN-NIGHT.cmd.

Runner facts:
- `-PlanOnly` writes nothing and prints `estimate N runs (C cold), about M min`. It exits 2 on matrix or plan errors.
- `-Only` is split on `[,;\s]+`.
- A missing bin only skips its arm, so the launcher's bin check is stricter on purpose.
- Exit codes: 0 all OK, 1 some run not OK, 2 matrix or preflight error.
- Output goes to `build\agent8\matrix\<yyyyMMdd-HHmm>[-n]`, with summary.md written in `finally`.
- Arm env is an object `{NAME: value}`. `driver` is a path or `{script, args}`.

Design decisions:
- GO parse: exactly 6 tokens, strict.
- Arm checks cover every arm in the JSON, not just `only=`, because of -ColdShared.
- Refuse arms that use menu, profile, seed_cache, triggers or toml. This is a launcher rule (unattended, pinned files only).
- Remove both allowed env keys from the inherited env and log which were present.
- HOLD gets a token and is deleted only if it is still ours.
- Re-hash the pins right before the runner starts and again after it exits. A change after the run marks the result suspect.
- CPU per process comes from CIM Win32_Process kernel+user time, with Win32_PerfRawData as the fallback. An unreadable process fails the gate.
- RAM uses the same VisualBasic ComputerInfo the runner uses.
- Build regex: the runner's list plus legodimensions.
- Screensaver: set to None at start, restored in `finally`. Keep-awake at start, released in `finally`.
- Dry-run hooks: -SampleSeconds, -GiveUpMinutes, -StopAt, -MatrixDir, -PollSeconds and -MaxGo. All are refused in real mode.

Next:
1. Write run-night.ps1 in 4 appends (output limit).
2. Write RUN-NIGHT.cmd and README.md.
3. Write fixtures in `build/agent5/launch-test/`.
4. Finalize W6, merging Agent 12's `build/agent12/w6-gates/W6-GATES.md` (task #32: C1 v3 SAFE b2r row 36, gates G2-G4, p2c_check.py, noise rule).
5. After 'go', run the dry-run tests and ask for reviews (11 and 10).

## Task #4 (run 2, 19:31-23:00): overnight launcher, final (replaces the task #27 checkpoint above)

Files in `bench/agent5/launch/` (the user double-clicks RUN-NIGHT.cmd at ~23:45; the pins are hashed then):
- `run-night.ps1`: final candidate 16B90FA8… (1017 lines, LF). Earlier versions: B0902106 (Agent 10's delta read 21:48), 3EFC5312, v3 163D7659, v2 924321AE. Copies are in `build/agent11/launcher-review/`.
- `RUN-NIGHT.cmd` D7A0362B… (19 lines, CRLF, ASCII). Line 15 explains any other exit code (Ctrl+C).
- `README.md`: the user part first, then "For the agents".
- Tests: `build/agent5/launch-test/run-tests.ps1 -Group go|gate|hold|run|pin` with `fake-runner.ps1` and `send-ctrlc.ps1`. Results are in `build/agent5/launch-test/results/`.
- Diffs for the reviewers: `build/agent5/launch-review/run-night-diff-v2-924321AE-to-B0902106.diff` and `...-3EFC5312-to-B0902106.diff`.

Change after B0902106 (22:11): in Stop-One, a process that refuses the kill but is gone within 3 s is logged as `(ended on its own)` instead of `NOT killed`. In t-run-deadline (22:08) the walk caught a conhost.exe in the middle of exiting (its powershell had just been killed), and TerminateProcess said "Access is denied". In the other run tests the conhost was already `(already gone)`. Every process was gone either way. All groups were re-run on the new hash.

W6: final at 21:16 (Agent 1 acknowledged it). `build/agent5/w6-draft/matrix-window6.json` E50D791B…, `RUN-WINDOW6.cmd` 3F31CBA8…, bin `build/agent2/devoff4b-bin`. Sent to Agent 8 at 22:08. `finalize-w6.ps1` now also checks the launcher's driver allowlist (42B1F265…; `-Check -NoPlan`: OK). The finalized files were not rewritten.

M1 G4 (Agent 3's `ready-m1`): passed at 14:12 (`build/agent5/s4-m1/copybench-check-20261122-141100.txt`; bench F98B935A…, exe 92C5FF6E…, both unchanged). Go sent to Agent 3 at 22:08.

Test results on 16B90FA8 (filled in after the re-run):

- go 16/16 PASS (22:18): t-good, t-badhash, t-badbin, t-badenv, t-driver (x5), t-unknownarg, t-14h, t-latest-go, t-badgo (x7), t-startref, t-hooks, t-mutex, t-deadline-go, t-deadline-gate, t-deadline-wait, t-latest-gate.
- gate 13/13 PASS: t-build, t-build-giveup and t-build-start (the three build refusals), t-close, t-stop-start, t-stop-wait, t-stop-gate, t-unstable, t-toohigh, t-lowres, t-json, t-real (22:23). t-relaxed failed in that run: the test's 0.25-min strict phase had already passed when the gate had its first 3 samples (machine under load; the launcher relaxed correctly). It passed in a solo re-run at 22:28 with a 1-min strict phase, gap counted from "HOLD written" (run-tests.ps1 034F2E1F06C1EEEED25500A0B9245EB8EE4C67FCB1B233F60F5F36B4B202CADE; results/summary-gate-relaxed-rerun.txt; the full run is in results/summary-gate-full-16B90FA8.txt).
- hold 4/4 PASS (22:14): t-hold-foreign, t-hold-keep, t-hold-gone, t-hold-taken.
- run 5/5 PASS (22:22):
  - t-run-ok: normal end.
  - t-run-stop: STOP mid-window. The runner (pid 35200) and its child powershell.exe:9144 were killed.
  - t-run-deadline: the end time was -StopAt 22:36 with -GraceMinutes -17.69, so the kill came at 22:18:18 while the runner was still running. The runner (pid 30816) and its child powershell.exe:38252 were killed; conhost.exe:14256 showed "(ended on its own)". END says "stopped early".
  - t-run-error: -TestFailAfter 25 made a simulated launcher error 26 s into the run. The runner (pid 25208) and its child powershell.exe:12624 were killed, END was written, and the launcher exited 0.
  - t-run-ctrlc: the same Ctrl+C had already ended the runner; the walk killed its child powershell.exe:26464.
- pin 2/2 PASS (22:33, run alone): t-pin-go, t-pin-gate. RUN-NIGHT.cmd was unchanged afterwards (D7A0362B...).
- smoke (22:34): with perf-notes/WINDOW-STOP.txt present, `RUN-NIGHT.cmd < nul` exited 2 after 7 s with START REFUSED (hidden desktop; "WINDOW-STOP.txt exists: delete it first") and "The launcher did not start ... Nothing was changed." The STOP file and status/ were removed afterwards (copy in build/agent5/launch-test/results/smoke-status-2235/). No launcher, fake runner or Start-Sleep of mine was left running.
- Reviews: Agent 11 SAFE (22:31; build/agent11/launcher-review/REVIEW.md D956C24C...). Agent 10 SAFE (22:33; b2r row 41/section 40). Night set final: run-night.ps1 16B90FA8..., RUN-NIGHT.cmd D7A0362B..., README.md 0058C8F6....

Daytime session (Agent 1, 22:27 and 22:34): the drafts go in build/agent5/day-draft/ and stay out of bench/agent5/launch tonight. -StopAt is a dry-run-only hook in run-night.ps1 (lines 65-67), so the draft has run-day.ps1: a generated copy of run-night.ps1 16B90FA8 with only marked lines changed.

Daytime session draft, final for review (23:14). Agent 1's spec came at 22:27 and 22:34 and was approved at 22:40 with these conditions:
- Nothing in bench/agent5/launch changes tonight.
- Dry runs are done by 23:30.
- After Agents 10 and 11 rate it, it goes into a new folder, bench/agent5/day/.
- Hashes go to Agents 1, 10 and 11 by 23:35. Stop at 23:50.

Files in build/agent5/day-draft/ (sha256):
- RUN-DAY.cmd 4B5489B4C1021038C44D2C97A18B19E675AB278CCC43D5CD1B11B21F5039CAD9 (CRLF)
- STOP-LAUNCHER.cmd CE27332F354B1DBB253678189A7070D8AB3C79010D1584C9DE204BB160C8E1B3 (CRLF)
- launcher-ctl.ps1 6DDE3150B72D6B0D849B17788098F9C10C1E96CBF5CF3BBC395C95C935C34895 (276 lines, LF)
- run-day.ps1 D86F6DE04B3EDA47A4811CD7139B9BEE21B43E0E368AAB4287143F45B8C59E98. make-run-day.ps1 generates it from run-night.ps1 16B90FA8. Seven lines end in "# DAY:":
  - L1: header.
  - L65: StopAt removed from the hook list.
  - L68 (new): -StopAt is required, otherwise exit 2.
  - L187: pins RUN-DAY.cmd.
  - L544: the HOLD text.
  - L938: the refusal text.
  - L966: the 14 h text.
- run-day.diff 54E35C180DBF4B164DB86CC5B61D71952F132C7149E69D909634DAE0B60EC12F
- make-run-day.ps1 17413F8A566E79BF0721BF77DA64BACEA629DBAB7D70887A6AA75CBAA2827780
- README-DAY.md 9D131EB14B89DBBBB642D0C40AA0103FB7742BD95B1BA143E7F8E6A8CE308FCB
- test-day.ps1 D7DBC6EA94ADC48D684357B8B8004E002A69CE1792E9FF6984CED72322AD2DA7

Test runs (test-day.ps1 -Name all):

| time | result | notes |
|---|---|---|
| 22:51 | 24/25 | leftovers failed as a false positive: pid 19932 was another process reading the files. The filter is fixed. |
| 22:54 | 25/25 | |
| 23:11:52 | 27/27 PASS | After the review fixes (results/summary-all-231151.txt). |

The 23:11 run covered: d-return-1..5, d-stale-1/2, d-none, d-unknown-1/2, d-real-1..4, d-cmd, d-cmd-nul, d-stopcmd-none, d-between, d-stop-n/y, d-dl, d-window-0..3, real-files and leftovers. Each run makes 2 -PlanOnly calls. The real-files check confirmed that nothing was written under bench/agent5/launch or perf-notes. Night files re-hashed at 23:12: 16B90FA8 / D7A0362B / 0058C8F6. launch/status is absent.

Subagent C's spec read (23:04) found no blockers. Fixed at 23:10:
- SHOULD 1: an unknown state now asks, in both modes.
- SHOULD 2: day mode reads the state again after the answer.
- SHOULD 3: the time check runs before anything is stopped.
- SHOULD 4: the folder, the files and AC power are checked first.
- SHOULD 5: README-DAY and the ctl text say Ctrl+C, not the X.
- NIT 6: the CreateNew race.
- NIT 7: the header.
- NIT 8: [0-9] in launcher-ctl.
- NIT 9: the RUN-DAY exit text.
- NIT 10/11: README wording.
- NIT 12: real day mode refuses outside bench\agent5\day\.
- NIT 13: test guard for WinSta0\Default.

Still open:
- NIT 14: the day launcher does not see the screensaver setting saved by a night launcher that was closed with the X.
- run-day.ps1 L68 still uses \d: an odd -StopAt typed by hand can exit 3 instead of 2.

Install plan (after Agents 10 and 11 rate it, not tonight):
1. Copy RUN-DAY.cmd, STOP-LAUNCHER.cmd, launcher-ctl.ps1, run-day.ps1 and README-DAY.md to bench/agent5/day/. make-run-day.ps1, run-day.diff and test-day.ps1 are optional. Do not copy status/.
2. Compare the hashes.

The night launcher ignores new files under bench/agent5/. Day status goes to bench/agent5/day/status, so Agent 12's read-out should look there.
