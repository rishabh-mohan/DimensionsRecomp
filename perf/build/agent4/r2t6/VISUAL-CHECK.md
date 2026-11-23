# Visual check: the 4 packed native shaders (#1 AOT pack)

> **Correction (Agent 4, 2026-11-23, task #29).** Without input the game never reaches the 3D attract: none of the 34 no-input runs checked on 2026-11-23 shows it. So the last "When they appear" point in section 1 and the no-input attract shots in section 4 are wrong, and section 3.1's no-input n-rows see only the start-up screens. The user's look now follows `build/agent4/screenshot-kit/README.md`: the same bins and flag, plus the virtual-pad route `harness/routes/attract-long.txt`, 360 s per run and 5 shots. After the break, the pack check repeats the kit's native command with the pack bin. The trace also shows that from the attract on, native drops draws from 46 more VS objects and 3 PS objects whose shaders were never dumped, so the pack may not cover the attract (kit section 4; `build/agent4/screenshot-kit/native4-drops-r6off.txt`).

1. The #1 pack lets the native renderer draw some objects that it drops today (4 shaders, packed and checked offline at 07:16). This changes the picture on purpose, so it needs one look from you, compared against the standard GPU path.
2. After W4b, Agent 2 builds one pack bin (~3 min build plus ~15 min prep, ~364 MiB, in a new folder), and the agents run the n-row check. Then you need ~15 min at your desktop: two 5-minute no-input runs (the standard path, then the pack), with 3 screenshots in each.
3. You decide whether and when to do it. After looking: yes (the pack goes into the native builds) or no (it stays out, and native keeps the #2 miss cache, which changes nothing on screen).

Agent 4, board run 2, task #16, 2026-11-22. Notes only: nothing was built or run for this file. It answers S4-DRAFT §4a question 4 and covers b2r §15.1 items 3-5 (`perf-notes/agent10-batch2-review.md`).

## 1. What changes, and where it shows

- **The 4 shaders:** placement VS `0xAC449538` and PS `0xAC448F28`, plus a second pair (VS `CCD76553…`, PS `E81FD692…`).
  - Today native drops every draw that binds them (draw.cpp:2712-2725, the `binding_failed` path). The standard GPU path draws them.
  - In a traced run, every dropped draw is a `draw_missing_vertex_shader` or `draw_missing_pixel_shader` event. With the pack, these draws render.
- **What they probably draw.** This is my inference from Agent 7's decode; nobody has seen it on screen:
  - The VSs read packed R11G11B10 normals, so the objects are 3D geometry.
  - The PSs alpha-test, and their constants are the Rec.601 luma weights (0.299 / 0.587 / 0.114). So expect grey or desaturated cut-out shapes.
- **When they appear.** No Toy Pad tags or input are needed:
  - On native, the first pair is bound about 12 s after launch, as soon as the start-up screens draw. In `0452-n0-r1` the log starts at 04:52:07 and the first miss lines are at 04:52:19.
  - The second pair is first bound about 27 s later (`0509-sd-r1`: 05:09:34, then 05:10:01).
  - They are still bound in Agent 7's later native profile window (n-prof), where their misses are 49 % of render-thread CPU.
  - So both the title/front-end screens and the no-input 3D attract include them.
- **Where on screen:** not known yet. Step 3.3 finds it before you look.

## 2. What has to be built first (Agent 2, after W4b and Agent 1's GO)

| | |
|---|---|
| **Tree** | Agent 2's S4a snapshot: source `build/agent2/snap1`, native build dir `build/agent2/snap1-on`. This is the tree behind native4-bin (MANIFEST: `STATE-S4a-1325.tsv`), so the pack bin differs from native4 only by the pack, and native4 is a clean "before". |
| **Inputs** | From `build/agent4/s35/run-071627/` (VERDICT PASS 07:16:50; SHA256SUMS 34/34), copied with sha checks. `snap-native-inputs.py` copies only from live, so it can't be used here. **(a)** `runtime-cache.cpp` (`AEA36683…A734`, 33,765 B, 4 DXIL entries) goes in as a snapshot copy. Point the CACHE FILEPATH `LEGO_NATIVE_RUNTIME_SHADER_CACHE` (rexlego/CMakeLists.txt:283-285) at that copy instead of `…/out/native-gpu/stubs/runtime-cache.cpp`. **(b)** `lego-microcode-index.cpp` (`E4C05782…0617`, 1,672,272 B, 19,122 rows) replaces `snap1/DimensionsRecomp/rexlego/out/native-gpu/lego-microcode-index.cpp` (CMake 274-275), but only if that copy is still the merge base `2DB85917…13A2` (it was at 14:03, 1,652,630 B, so today a plain copy works). Otherwise, re-merge `index-addition.cpp` (6 rows) with `merge_microcode_index.py`, which refuses conflicts. Back up both files and the cache entry first, as for S4a. |
| **Prelink step** | `LEGO_NATIVE_RUNTIME_PRELINKED_BANK` is empty, so the build re-runs `lego_gpu_prelink_runtime` (CMake 408-426 and 511-519). It writes `snap1/DimensionsRecomp/rexlego/out/native-gpu/runtime-linked-dxil-cache.cpp`. This step is required: the 4 entries are DXIL libraries (spec mask 1 for the VSs, 2 for the PSs), and they resolve only through that prelinked cache. Check afterwards that the file holds the 4 containers and that the build log has no new warnings (§15.1 item 2). |
| **Time** | Agent 2's estimate (S4-DRAFT §3, 07:08, ±30 %): ~2-3 min at -j10 for the incremental native build, plus ~10-15 min of prep (copies, reconfigure, MANIFEST, gates). The 4-entry prelink isn't timed separately. |
| **Disk** | ~364 MiB for the new bin folder (native4-bin is 0.36 GB). The tree grows by < 1 MB. C: had 267 GB free at 13:53. |
| **Output** | A **new folder**, for example `build/agent2/native4p-bin` (Agent 2 picks the name), with a MANIFEST that lists both input hashes. The native GPU fingerprint changes, because the cache and the index are fingerprint inputs. native4-bin and every frozen bin stay untouched. |
| **Rollback** | Restore the stub cache path and the old index from the backup. native4-bin stays staged. |

## 3. Agent checks before you look (hidden desktop, functional only)

These take ~25 min, or ~17 min if 3.1 and 3.3 share runs.

1. **The n-row rule** (§15.1 items 3 and 5; the rule is in §5 below). Run n0 on native4 and on the pack bin: 300 s each, no input.
   - Both arms get `LEGO_NATIVE_TRACE_DIR`. A trace changes render paths, so traced runs pair only with traced runs.
   - Cvars: `-Cvar 'native_settings_frontend=false;native_fps_limit=0;framerate_limit=0'`.
   - About 12 min in Agent 8's or Agent 3's slot.
2. **Stability capture** (§15.1 item 1). One more n0 dump run on native4, with both `LEGO_DUMP_MISSING_SHADERS` and `LEGO_NATIVE_TRACE_DIR`.
   - Pass: the same 4 container names and bytes as `0509-sd-r1`.
   - About 6 min. It's needed before the pack lands, but not before your look, so it can run afterwards.
3. **Where to look.** Run the same two native bins with `LEGO_GPU_SNAPSHOT_DIR=<abs dir>` and `LEGO_GPU_SNAPSHOT_FSR_ONLY=1`.
   - For the first 48 s after the first HDR frame, add `LEGO_GPU_SNAPSHOT_TIME_WINDOWS=1`. It saves present frames at 0, 8, 16, 24, 32 and 48 s (device.cpp:2516-2562).
   - For later scenes, use `LEGO_GPU_SNAPSHOT_MANUAL_ONLY=1` instead, and create `<dir>\capture-next-frame` at the moment you want (the game checks for it twice a second).
   - Convert each frame with `DimensionsRecomp/tools/gpu-aot/inspect_gpu_snapshot.py <x.dds> --image`, then diff pack against native4.
   - The trace from 3.1 says *when* (the frames with `draw_missing_*` rows). The diff says *where*.
   - Output: marked PNGs in `build/agent4/vc/`, plus the scene names for §4.
   - The snapshot dir also turns on extra traces (draw.cpp:1085 and 4796), so these runs are functional only, and both arms must get the same env.
   - With the trace dir on, the game also saves a present frame every 5 s by itself (device.cpp:2533-2548, at most 128 files). So 3.3 can share 3.1's two runs if Agent 8 is fine with snapshots in the n-rows.

## 4. Your check on the visible desktop (~15 min)

**When:** after W4b, once Agent 1 says the pack bin and step 3.1 have passed and no agent runs are going.

**Bins:**
- Reference, the standard GPU path: `build/agent2/devoff4-bin`. It is the same S4a snapshot, built without the native renderer: the MANIFEST says OFF builds compile no gpu_native file.
- Pack: `build/agent2/native4p-bin`, or whatever Agent 2 names it.
- Optional "before": `build/agent2/native4-bin`. Only needed if step 3.3's pictures aren't clear.

**Commands.** Use PowerShell in the repo root, one run at a time. Each run closes itself at 300 s. `-RunsRoot` must be a full path (hence `$PWD`): run-game.ps1 doesn't resolve it, and the game, which runs in the run dir, would miss its log and pad paths (fixed 2026-11-23):

```
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\agent2\devoff4-bin -Seconds 300 -Tag vc-ref -RunsRoot "$PWD\build\agent4\vc\runs"
powershell -NoProfile -ExecutionPolicy Bypass -File harness\run-game.ps1 -BinDir build\agent2\native4p-bin -Seconds 300 -Tag vc-pack -RunsRoot "$PWD\build\agent4\vc\runs" -Cvar 'native_settings_frontend=false'
```

The game window opens on your desktop. Each run's `run.json` should then record the mode `FUNCTIONAL (interactive desktop)`; agents' runs use a hidden desktop instead (run-game.ps1:198-199).

**Flags:**
- Native needs only `native_settings_frontend=false` (§S2.13 of `perf-notes/agent4-draw-path.md`).
- Everything else is the harness default: a fresh user folder, audio muted, `--pause_when_unfocused=false`, inherited `LEGO_*` variables dropped and the default frame limit.
- Don't set any `LEGO_*` variables yourself. This is a look, not a timing.

**Where in the game.** No input and no Toy Pad tags. The standard path shows a black window for up to ~60 s at start-up (cold shader storage); native shows its first screen within ~15 s. Take a screenshot at each of three moments in each run:
- **S1:** the title/front-end screen, once it has been static for ~15 s.
- **S2:** the 3D attract, ~10 s after it starts. It starts by itself, ~2-2.5 min after the first frame.
- **S3:** the 3D attract, ~40 s after it starts.

If step 3.3 names a different scene, use that instead.

**Screenshots:**
- The harness doesn't take timed screenshots: `harness/winhelper.cs` has a `Shot` helper, but `run-game.ps1` never calls it.
- So press **Win+PrtScn** at each moment. Windows saves a PNG to Pictures\Screenshots.
- Keep the game window in front, and don't click into it.
- To compare, flip between the reference and pack images in Photos, or tell Agent 1 and I'll lay them out side by side in `build/agent4/vc/`.

**How long:** 5 min per run, so 10 min for both, plus ~3 min to compare. Add 5 min for the optional native4 run.

## 5. What to compare, the pass/fail rule, and what happens on a fail

**Compare** the pack image with the reference at the same moment: first in step 3.3's marked region, then over the whole frame.
- The objects native4 lacks should be present in the pack image and match the reference: position, shape, grey level or colour, and cut-out edges.
- Nothing else should differ from native4. Step 3.3's diff should show changes only in that region.
- Ignore differences in animation phase or camera position between runs, and the standard path's known look differences from native outside the marked region.

**Pass rule.** This is the n-row rule (proposal §6 in `build/agent4/s34/aot-pack-proposal.md`, and "Not done here (S4)" in `build/agent4/s35/README.md`). Both parts must pass:
- **Agents, pack vs native4 (step 3.1):**
  1. events.tsv has 0 `draw_missing_vertex_shader` or `draw_missing_pixel_shader` rows.
  2. game.log has no "placement vertex/pixel shader … missing from AOT index" lines and no "unrecognized … resource" lines for the packed addresses.
  3. Draws per frame (frames.csv `draw_calls`, p10/p50/p90) are ≥ native4's, and the other marks are unchanged.
  4. There is no new shader, PSO or hash=0 warning type (`bench/agent4/check_n_rows.py`).
- **You:** yes if the restored objects match the reference and nothing else changed; no otherwise.

**What happens on a fail:**
- **Step 3.1 fails:** you aren't asked to look.
  - Agent 2 checks that the prelinked cache holds the 4 entries.
  - I re-run the offline lookup check (`test_placement_capture_lookup.py`) on the bin's inputs.
  - The pack bin is parked, and native stays on native4 (plus the #2 miss cache if Agent 1 gives the GO).
- **You say no:** the pack doesn't land.
  - The snapshot goes back to the stub cache and the old index (from the backup).
  - The pack bin is deleted, or kept for diagnosis (your call).
  - Native stays on native4, plus #2.
  - Follow-up, with no time from you: Agent 7 and I compare the 4 HLSL translations (`build/agent4/s35/run-071627/hlsl/`) and their spec variants with the standard path's handling of the same shaders.
  - A new pack means a new check.
- **Nothing visible changes anywhere** (step 3.3's diff is empty and you see no difference): the draws are off-screen or fully cut out in these scenes. Then it's your call: land on the n-rows alone, or wait for a scene that shows them, for example a level with Toy Pad tags (S4-DRAFT question 1).

## 6. What you must decide

1. **Will you do this check, and when?** The earliest is ~35-40 min after W4b ends (build ~20 min, agent checks ~17-25 min). Until then, native keeps the #2 miss cache, which changes nothing on screen.
2. **After looking:** yes or no.
3. **Only if nothing visible changes:** land on the n-rows alone, or wait.

## Sources

- The pack: `build/agent4/s35/README.md` and `run-071627/` (pack-log VERDICT PASS; SHA256SUMS 34/34; gradient 4 of 4; index 19,116 → 19,122).
- The proposal: `build/agent4/s34/aot-pack-proposal.md`: §6 (the n-row rule), "Screenshot check" and "Rollback".
- Build time and disk: `perf-notes/S4-DRAFT.md` §3 (Agent 2, 07:08). Agent 2's MANIFEST: `build/agent2/native4-bin/MANIFEST.txt` (lines 2-7, 72).
- The harness: `harness/run-game.ps1` header (lines 1-39; desktop mode at 198-199) and `perf-notes/agent3-run-harness.md` (the black window at start-up, and the attract starting at perf 126-141 s).
- Native snapshots: `DimensionsRecomp/rexlego/src/gpu_native/device.cpp` 2478-2571. Dropped draws: `draw.cpp` 2712-2725.
- Shader facts: `perf-notes/agent7-present.md` (the dump table and decode, 590-626); `build/agent8/matrix/20261122-0452/runs/0452-n0-r1/game.log` (lines 410-421).
