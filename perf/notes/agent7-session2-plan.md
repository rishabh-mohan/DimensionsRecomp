# Agent 7, Task #6 (session 2): working plan and resume aid

State at the 16:52 pause: no game code has been edited, nothing is running, and the baseline fixture run is done.
Paths are relative to `DimensionsRecomp/rexlego/src/gpu_native/`. Line numbers are for `perf/opt` at `127e04b`, before any edits.

## Baseline fixtures

Results are in `build/agent7/tests-baseline/summary.txt`.
To rerun: `powershell -NoProfile -File bench\agent7\run_tests.ps1 <tag>`. It takes about 2.5 min and compiles one fixture at a time.

**Passing (must still pass after the edits):**
- test_submission_waits
- test_native_overlay
- test_resize_fences
- test_completion_callbacks
- test_presentation_metrics
- test_present_rect.cpp

**Already failing at baseline.** The fixtures are stale against the current device.cpp; none of these failures are ours.

| Fixture | Failure |
| --- | --- |
| test_command_slots, test_frame_ring_transaction, test_draw_device_view | Undeclared `PrepareNativeCommandList` / `g_texture_slots_mutex` |
| test_gpu_timestamps | Undeclared `NativeImmediateCommands` |
| test_frame_cadence | The CSV block uses `configured_scene_extent`, `width`, `height` and `presentation_*`, which its harness doesn't define |
| test_cpu_resource_wait | Undeclared `NativeFullDrawPreparationEnabled`, `NativeRecordingGate` |
| test_queued_frame_boundaries, test_threaded_callback | Undeclared `NativeTaskStage`, `WaitPendingPreparationFor` |
| test_frame_rate_settings | Looks for `void LimitFrameRate()`, which no longer exists |
| test_native_vsync | Asserts `const bool requested_vsync = NativeVsyncRequested();`, which is absent |
| test_sampler_live_settings | Exe build fails; reason still to be checked |

After the edits, each failing fixture must report exactly the same compiler errors as at baseline, with nothing new.

## Planned edits (anchors refer to the unedited device.cpp)

**(a) Skip the gamma pass for an identity ramp.** On by default; `LEGO_NATIVE_FORCE_GAMMA_PASS=1` restores the old path.
- Add `bool gamma_identity = false;` to State after `bool gamma_table_valid = false;` (254).
- Add a helper, `DisplayGammaIsIdentity`, before `}  // namespace` at 1717. It checks all 256 entries and all 3 channels (shifts 20, 10 and 0; 10-bit values) and requires `|255*v - 1023*i| <= 409`.
- In SetDisplayGamma (1719-1727), set `gamma_identity` and add `identity=` to the log line.
- Change the gate at 1804 to `state.gamma_table_valid && (!state.gamma_identity || force_gamma_pass)`.

**(b) Skip the full back-buffer clear when it is provably overwritten.** On by default; `LEGO_NATIVE_FULL_PRESENT_CLEAR=1` restores the old path.
- Add `constexpr bool PresentRectCoversTarget(rect, w, h)` to present_rect.h.
- At 1879-1880, clear only when `always_clear`, when the rect doesn't cover the target, or when the back-buffer description differs from `width`/`height`.

**(c) Take the Win32 queries out from under g_mutex.**
- Compute `presentation_window`, `presentation_focused`, `presentation_borderless` and `presentation_monitor` before `std::lock_guard lock(g_mutex);` (1752), from `g_state->swap_chain`. This is safe because the recording lock already excludes Create and Shutdown.
- Keep those names, and keep `presentation_chain` under the lock.
- Cache the `LEGO_NATIVE_GPU_DEBUG` getenv at 2211 in a `static const bool`.

**(d) Two-phase limiter.** Off by default; enabled with `LEGO_NATIVE_UNLOCKED_PACING=1`.
- Move `next` and `previous_limit` to namespace-scope atomics.
- Add `HostDevice::PaceFrameBeforeLock()` (declared in device.h). It sleeps until about `next - 2 ms` without taking the recording lock; the final spin stays in LimitFrameRate.
- Needs Agent 4 to add one line in draw.cpp SwapHook, between `PollCompletionCallbacks()` (5193) and `LockRecording` (5194).

**(e) Report #1: cap frames in flight.** Off by default; enabled with `LEGO_NATIVE_FRAMES_IN_FLIGHT=1..3`.
- After `state.frame_slot = (slot + 1) % ...` (2206), record the present serial in a ring.
- Wait for the present serial from N frames back, using a new helper:
  1. Refresh completed submissions.
  2. Find the slot whose `slot_submission` matches the serial.
  3. Call `WaitForSubmissionLocked`.
  4. Run the same per-slot cleanup as Synchronize (1287-1293).
- Log the wait count and total ms every 600 frames.

**(f) Report #2: guest waits drain the whole GPU.** Documentation only. `KickOffHook` returns a constant marker, and the fixtures compile Synchronize, so it can't change.

**(g) Frame-latency waitable.** Off by default; enabled with `LEGO_NATIVE_LATENCY_WAIT=1..3`.
- Set `SetMaximumFrameLatency(N)` and take `waitableObject` lazily inside PresentTexture.
- Change the `lock_guard` at 1752 to a `unique_lock`.
- Just before `return presented;` (after the GPU-debug block), unlock and call `WaitForSingleObjectEx(h, 1000, FALSE)`.

**(h) Inline `CurrentDrawPreparation`.**
- device.h:93 becomes `extern constinit thread_local DrawPreparationContext* t_draw_preparation;` plus an inline accessor.
- device.cpp:751 gets `constinit`, and 752 is deleted.
- Editing device.h rebuilds about 21 TUs.

## Don't touch (the fixtures extract this text)

**Whole functions:**
- NativeCommandSlotCount, CreateFrameRing
- RefreshCompletedSubmissionsLocked, MarkSubmissionLocked, WaitForSubmissionLocked, WaitForSubmittedFramesLocked
- RebuildSwapChain, BeginFrameCommandsLocked
- SubmitRecordedWork, Synchronize, RetireResource, UnregisterTexture
- EnqueueCompletionCallback, PollCompletionCallbacks, LockRecording, CurrentDrawDeviceView
- HostDevice::Create, HostDevice::Shutdown

**PresentTexture sub-blocks:**
- The acquire-fail block (1778-1789).
- From `if (state.gpu_timestamps)` (1972) to `MarkSubmissionLocked` (1988).
- 2082-2083.
- The CSV block, from 2094 to `state.snapshot_number = 0;`.

**Text order the fixtures assert:**
- The first `drawInstanced(3, 1, 0, 0)` comes before `RenderNativeOverlays(`, which comes before `RenderTextureLayout::PRESENT`.
- `LockRecording` comes before `NativeAnisotropicRequested()`, which comes before `g_anisotropic_override.exchange(`.

## Compile check

Once Agent 2 announces build/dev (the NATIVE_GPU=ON database, which depends on Agent 6's stubs), run:

`powershell -NoProfile -File env\compile-one.ps1 DimensionsRecomp\rexlego\src\gpu_native\device.cpp -OutDir build\agent7\obj -Db build\dev\compile_commands.json`

## Messages still to send

- To Agent 3: the GPU check and the `LEGO_NATIVE_COMMAND_SLOTS` A/B (env vars and which log lines to read), once the code lands.
- To Agent 4: the `PaceFrameBeforeLock` line for SwapHook, and the status of the `CurrentDrawPreparation` inline.
