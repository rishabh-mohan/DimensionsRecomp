# Agent 7: native renderer device, present, frame pacing and post-processing (task #6)

> **RESUME (session-2 Task #6, paused 16:53).**
> - **Done:** Plume swap-chain and adapter verification, the session-2 design, and the baseline fixture run (6 pass, 11 already failing because the fixtures are stale; see `build/agent7/tests-baseline/summary.txt`).
> - **Not started:** no game code has been edited, and nothing is running.
> - **Next:** apply edits (a)–(h) from [agent7-session2-plan.md](agent7-session2-plan.md), run `powershell -NoProfile -File bench\agent7\run_tests.ps1 after`, and compare with baseline. Once Agent 2 announces `build/dev`, compile-check with `powershell -NoProfile -File env\compile-one.ps1 DimensionsRecomp\rexlego\src\gpu_native\device.cpp -OutDir build\agent7\obj -Db build\dev\compile_commands.json`.

**Status: PARTIAL. Analysis only.** Agent 1's STOP PLAN (12:24) said no source edits, so I edited nothing, built nothing and ran no benchmarks. The toolchain and Agent 3's harness weren't ready, and the Plume submodule isn't checked out anywhere on disk. Both repos are clean. Use this file as the plan for resuming the work.

Paths are relative to `games/lego-dimensions-recomp/DimensionsRecomp/rexlego/src/gpu_native/` unless noted otherwise. Line numbers are from branch `perf/opt` @ v0.2.0, read on 2026-11-21.

## Changes made
None.

## Quick checks to do first (no code, about 5 minutes on the user's laptop)
1. **Which adapter is in use?** Check the startup log if it prints one. If not, look at the GPU engine column in Task Manager. If it shows Iris Xe instead of the MX570, item 11 becomes the biggest win by far.
2. **`LEGO_NATIVE_COMMAND_SLOTS=12` A/B test** (item 1). Compare FPS and `frame_slot_wait` ms in the main menu and the hub.
3. Turn on texture timing and count **submissions per frame** and **sync calls per frame by reason**. These numbers decide whether items 1 and 2 matter.

## Opportunities, ranked by expected win

### 1. The frame ring counts submissions, not frames, so the CPU can't get a frame ahead
- **Where:** device.cpp:206-212 `NativeCommandSlotCount()` returns 3. The env var `LEGO_NATIVE_COMMAND_SLOTS` only accepts 3 or 12. The comment at device.cpp:221-222 says "Guest kickoffs consume slots independently of swap-chain presentation". Also `SubmitRecordedWork()` at device.cpp:1380-1401 and `BeginFrameCommandsLocked` at device.cpp:699-747. The latter calls `WaitForSubmissionLocked` (device.cpp:644-676), which calls `queue->waitForCommandFence` at line 657.
- **What's slow:** Every guest kickoff ends and submits the open command list and advances `frame_slot`. `Synchronize` (1268-1276), the acquire-failure path (1779-1788) and present (1974-1988, 2206) also use up slots. Opening the next list waits on the fence from 3 submissions ago. With 3 or more submissions per displayed frame, that fence belongs to the current or previous frame. The CPU then blocks on the GPU mid-frame, so CPU and GPU take turns instead of overlapping.
- **Evidence:** tools/gpu-aot/native-performance-vsync-20261010.md reports the render thread spending about 16% of its time in `WaitForSubmissionLocked` in the main menu.
- **Proposed change:** Measure first, then put it behind a cvar whose default keeps the exact old path (use the same cvar macro as `native_fps_limit` at device.cpp:75):
  ```cpp
  // device.cpp ~206 (sketch)
  // cvar native_frame_slots, default 3 (= legacy), clamp 3..16
  uint32_t NativeCommandSlotCount() {
    /* existing env override (3 / 12) first */
    return std::clamp<int32_t>(cvar_native_frame_slots, 3, 16);
  }
  ```
  A better long-term fix: keep the per-slot fences, but make `BeginFrameCommandsLocked` wait on "N presented frames ago" (for example N=2) instead of "3 submissions ago". Track the submission serial at each present and wait for that serial's fence.
- **Risk:** Medium. This changes pacing and latency, because more queued work means more latency, so the cvar must be OFF by default. Upload pages (4 MB per slot, `AllocateDrawUpload` 1206-1240), descriptor heaps and semaphores are all per slot, so memory grows with the slot count. Resource lifetimes are safe in the "more slots" direction.
- **How to verify:** tools/gpu-aot `test_resize_fences.py`, `test_temporal_worker*`, `test_native_vsync.py`. At runtime, use `LEGO_NATIVE_GPU_TIMESTAMPS=<csv>` and `LEGO_NATIVE_FRAME_METRICS`. Compare `frame_slot_wait` ms, FPS and PresentMon latency.

### 2. Every guest fence or idle wait drains the whole GPU
- **Where:** `HostDevice::Synchronize` at device.cpp:1253-1310 submits the open list, then waits on **all** slots. Callers:
  - hooks_device.cpp:187-190, `BlockUntilIdle` (kIdle)
  - hooks_device.cpp:196-200, `BlockOnFence` (kFence). Its comment says a "full host drain is conservative".
  - hooks_device.cpp:260, `BlockUntilNotBusy` (kResource), after skipping non-native resources at lines 218 and 245-249
  - textures.cpp:3728 (kResource)
  - gpu_pass_profile.h:76 (diagnostics only)
- **What's slow:** Each call empties the GPU pipeline. The CPU waits for all queued GPU work, then the GPU sits idle while the CPU records the next batch. One such call per frame is enough to remove all CPU/GPU overlap.
- **Proposed change** (cvar `native_targeted_sync`, OFF by default):
  - `BlockOnFence`: when the guest inserts the fence, record the host submission serial, then wait only on that serial's slot fence.
  - `BlockUntilNotBusy`: track the last submission serial that referenced the resource and wait only on that.
  - `BlockUntilIdle` keeps the full drain.
- **Risk:** Medium to high. Wrong ordering would break the title's CPU readbacks (locks on render targets, queries). The old path must stay exact when the cvar is off.
- **How to verify:** Use the per-reason sync counters (`sync_calls` / `sync_ms` by reason in the texture-timing log) and the long-wait log line "completion callback GPU wait took". **Count first:** if the hub and levels show about 0 kFence/kResource syncs per frame, move this item down.

### 3. The frame-latency waitable is never used, and the swap-chain config is unverified
- **Where:** device.cpp:854-855 creates the swap chain through Plume with `RenderSwapChainDesc(hwnd, B8G8R8A8_UNORM, 3)`. device.cpp never waits on the swap chain or its waitable object (no `wait(` call). The comment near device.cpp:679 mentions the latency object.
- **Already known:** tools/gpu-aot/test_native_vsync.py and patches/plume-lego.patch show how Present is called:
  - SyncInterval is `vsync && !enablePresentWait ? 1 : 0`.
  - With vsync off and tearing supported, it passes `DXGI_PRESENT_ALLOW_TEARING` (device.cpp:2031-2035 logs `tearing=`).
  - So tearing with VSync off looks handled already.
- **Unverified** without Plume source (prepare_plume.py pins e0c8871b930dc1a6544bf457f2348c456b9d7e13):
  - FLIP_DISCARD vs FLIP_SEQUENTIAL
  - whether `DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT` is set
  - the `SetMaximumFrameLatency` value (the DXGI default is 3)
- **Proposed change** (cvar `native_latency_wait`, OFF by default): if the swap chain has the waitable, call `SetMaximumFrameLatency(1 or 2)` when it's created. Then call `WaitForSingleObjectEx(waitable, 1000, TRUE)` at frame start, before `LimitFrameRate` and `LockRecording`. This cuts input latency by up to 1-2 frames and lets the limiter sleep instead of spin. It probably needs a new Plume patch under tools/gpu-aot/patches, which I don't own, so coordinate with whoever does.
- **Risk:** Medium (pacing).
- **How to verify:** PresentMon (MsBetweenPresents, display latency), `test_native_vsync.py`, `test_presentation_metrics.py`, `test_window_mode.*`.

### 4. The frame limiter busy-spins while holding the recording lock
- **Where:** `LimitFrameRate` at device.cpp:1691-1716 uses a high-res waitable timer, then a `YieldProcessor` spin for the last ~0.5 ms. `native_fps_limit` defaults to 240 (device.cpp:75). It's called at the top of `PresentTexture` (device.cpp:1736), **after** `LockRecording()` (device.cpp:1731).
- **What's slow:**
  - A core spins on every frame of a battery-powered laptop, where the MX570 and Iris Xe share power and thermal headroom.
  - While the limiter sleeps, it holds the recording lock, which blocks the temporal worker and other recorders.
- **Proposed change:** Move `LimitFrameRate()` ahead of `LockRecording()`. This changes lock order and timing, so put it behind a cvar that's OFF by default. Also try a shorter spin window (about 0.25 ms) on the high-res timer.
- **Risk:** Low to medium (jitter at high caps).
- **How to verify:** Frame-time stddev in PresentMon at 60/120/240 caps, and per-thread CPU% (ETW / Process Explorer).

### 5. The display gamma compute pass runs every present once a ramp is set, even an identity ramp
- **Where:** The pass is at device.cpp:1804-1871. It's controlled by `gamma_table_valid`, which is set by the SetGammaRamp hook (hooks_device.cpp:346-369) and by `SetDisplayGamma` (device.cpp:1719-1727). Also `DisplayGammaGpu::Apply` in display_gamma_gpu.h (~55-86).
- **What's slow:** Every present runs a full-res compute dispatch with a UAV surface and barriers, so the whole output is read and written once more. That's about 16 MB of traffic per frame at 1080p RGBA8. `Apply` also does a Map/memcpy/Unmap of the 1 KB ramp and recreates 3 descriptors for every frame and slot. If the title sets an identity ramp, which is common, all of this is wasted work.
- **Proposed change** (pure efficiency, output stays exact, so it can be ON):
  ```cpp
  // SetDisplayGamma (device.cpp ~1719)
  gamma_table_valid = true;
  gamma_identity = IsIdentityRamp(table);  // exact under the shader's quantisation
  // PresentTexture (device.cpp ~1804)
  if (gamma_table_valid && !gamma_identity) { /* existing pass */ }
  ```
  Also cache the ramp upload and descriptors per slot with a generation counter, so `Apply` only rewrites them when they change. Later, fold the LUT into the final copy or FSR1 RCAS shader to remove the pass entirely.
- **Risk:** Low, as long as the identity test exactly matches how the shader samples the LUT. If the shader interpolates, identity must hold under interpolation too, so check the shader.
- **How to verify:** The `test_display_gamma*` fixtures in tools/gpu-aot, plus a readback compare of old vs new output for identity and non-identity ramps. Use GPU timestamps around the pass.

### 6. The whole back buffer is cleared every present
- **Where:** device.cpp:1880, a `clearColor` on the acquired swap-chain image each present.
- **What's slow:** The clear covers the full screen even when `present_rect` already covers the whole output. The copy or FSR pass then overwrites every pixel anyway. With the flip model the buffer contents are undefined, so only the letterbox bars actually need clearing.
- **Proposed change** (pure efficiency): skip the clear when `present_rect` equals the full output. Otherwise, clear only the 2 bar rects, using separate single-rect clears, since multi-rect clears crashed nvwgf2umx.dll before.
- **Risk:** Low. Keep the clear whenever the image isn't fully covered: integer scaling, aspect bars, or rounding in present_rect.h.
- **How to verify:** `test_present_rect.cpp`, `test_window_mode.*`, and screenshot compares at 16:9, 21:9 and 4:3 windows.

### 7. Win32 window and monitor queries on every present, under g_mutex
- **Where:** device.cpp:2001-2015 calls `GetForegroundWindow`, `GetWindowLongPtrW` and `MonitorFromWindow`, plus a linear vector search, on every present. `GetFullscreenState` and `EnumDisplaySettingsW` only run on a change (2027-2049).
- **Proposed change** (pure efficiency): cache the results and refresh every N presents, or on WM_SIZE / WM_MOVE / WM_DISPLAYCHANGE / activation. The win is small (µs per present, plus win32k locking), and the risk is trivial.
- **How to verify:** `test_window_mode.*`, `test_presentation_metrics.py`.

### 8. FSR1 presenter barriers
- **Where:** device.cpp:1882-1901. In fsr1_present.h:172-199, each pass has a PIXEL_SHADER_RESOURCE ↔ RENDER_TARGET barrier pair on the intermediates, and there are per-slot heaps (12 slots).
- **Proposed change:** Batch the transitions into one barrier call at each pass boundary. Leave intermediates in the state the next frame expects, which saves one transition. Minor win.
- **How to verify:** `test_fsr1_present_gpu.cpp`, GPU timestamps.

### 9. FPS overlay does up to 120 single-rect clears per present (only when show_fps is on)
- **Where:** device.cpp:1924-1961. The batched path is behind `LEGO_NATIVE_FPS_OVERLAY_BATCHED`, because multi-rect clears crashed nvwgf2umx.dll on 2026-10-10.
- **Proposed change:** Draw the digits with one textured quad from a digit atlas, or with one compute pass. This only matters when the counter is visible, so priority is low.

### 10. Hidden overlay still costs a CPU post per present
- **Where:** native_overlay.cpp:169-180. `QueueNativeOverlayFrame` posts a `CallInUIThreadDeferred` lambda (capturing a shared_ptr) every present, even with no dialogs open. The GPU side already returns early (native_overlay_gpu.cpp:147-151).
- **Proposed change:** Skip the post when no dialogs or ImGui windows are visible. This needs a thread-safe `HasDialogs()`, for example an atomic flag. It saves one allocation and one cross-thread post per frame.
- **How to verify:** `test_native_overlay*.{py,cpp}`.

### 11. Adapter selection on the hybrid laptop (MX570 + Iris Xe). Worth a lot if the wrong GPU is picked
- **Where:** device.cpp:824-826. The env var `LEGO_NATIVE_ADAPTER` picks an adapter by name. Otherwise Plume chooses; the comment says "most video memory". tools/gpu-aot/patches/plume-adapter-query.patch exists.
- **Analysis:**
  - If Plume compares `DedicatedVideoMemory`, the MX570 (2 GB) wins. If it compares shared or total memory, Iris Xe could win. I can't tell without the Plume source.
  - On Optimus laptops the display is attached to the iGPU, so a cross-adapter copy at present can't be avoided.
- **Proposed change:**
  - Plume patch: enumerate with `IDXGIFactory6::EnumAdapterByGpuPreference(DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE)`, falling back to `EnumAdapters1`. Keep the env override.
  - Log the chosen adapter's name and `DedicatedVideoMemory` at startup.
  - Add a cvar for the preference.
  - Check whether the exe exports `NvOptimusEnablement` / `AmdPowerXpressRequestHighPerformance`.
- **Risk:** Low.
- **How to verify:** Startup log, the GPU engine column in Task Manager, FPS on the user's laptop.

### 12. Minor items, no action needed
- GPU timestamps are off unless `LEGO_NATIVE_GPU_TIMESTAMPS` is set (device.cpp:886-899). Readback is mapped after fence completion (gpu_timestamps.h:101-130), so there's no stall.
- `RefreshCompletedSubmissionsLocked` (617-635) calls GetCompletedValue once per slot, which is cheap.
- `RebuildSwapChain` (688-697) waits on all frames, but only on resize.
- temporal_present.cpp:319-331, `RejectTemporalMotion`, creates a framebuffer and does 2 clears per call when motion is rejected. Caching the framebuffer per target would help a little (low priority).
- `AllocateDrawUpload` (1206-1240) uses 4 MB upload pages per slot. Fine.

## Rejected, with reason
- Overlay GPU cost when hidden: already zero (early return).
- Timestamp and query readback stalls: none in the timestamp path, since readback happens after the fence. The F10 pass profile (gpu_pass_profile.h:76) drains the GPU on purpose and is diagnostics only.
- VSync-off tearing support: already present (ALLOW_TEARING flag plus SyncInterval 0, per test_native_vsync.py), pending confirmation in the Plume source.

## Order for resuming
1. Run `python tools/gpu-aot/prepare_plume.py` to check out Plume at the pinned commit. Read the D3D12 swap-chain creation (flags, FLIP model, waitable, MaxFrameLatency) and the adapter enumeration to confirm items 3 and 11.
2. Do the quick checks above on the user's laptop.
3. Do the pure-efficiency, output-exact items first, defaulting to ON: 5 (identity gamma skip and caching), 6 (conditional clear), 7 (cached Win32 queries), 10 (skip the overlay post). Compile-check each one with Agent 3's harness and run the fixtures listed for it.
4. Put items 1, 2, 3 and 4 behind OFF-by-default cvars, with the old path exact. A/B them with PresentMon, GPU timestamps and the frame metrics CSV.
5. Later: fold the gamma LUT into the final shader (removes a full-screen pass), batch the FSR1 barriers, and replace the FPS-overlay clears.

## What I didn't get to read or verify
- **Plume D3D12 source.** It isn't checked out anywhere on disk. Unread: swap-chain flags, FLIP model, waitable object, MaxFrameLatency, adapter enumeration.
- temporal_* files other than temporal_present.cpp: temporal_shaders.h, temporal_texture_history.h, and the temporal camera, composition and worker sources.
- FSR3 upscaler sources (fsr3_settings.*, Fsr3Upscaler) and the FSR1 shader bodies.
- depth_resample.*, depth_alias*, color_alias_*, scaled_resolve.h, resolve_region.h, render_extent.h, present_rect.h.
- visual_effects.h, tonemap_dof.h, fps_counter.h, settings_runtime.*, settings_snapshot.*, hooks_portrait.cpp, crash_*, renderdoc_probe.h, portrait_probe.h, build_info.h.in, shaders/**.
- native_overlay.cpp outside lines 160-185, and native_overlay_gpu.cpp outside lines 145-195.
- device.cpp: only skimmed the ResolveHdrColor / resolve section (~1420-1560) and CreateFrameRing (~440-500).
- Callers of kickoff and Synchronize in draw.cpp, queries.cpp and gpu_pass_profile.h aren't traced. **The submissions-per-frame count is inferred, not measured.**
- No fixtures built or run, and no microbenchmarks (no toolchain or harness was available).
