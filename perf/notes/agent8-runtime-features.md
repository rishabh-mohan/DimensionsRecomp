# Agent 8 / task 7: per-frame overhead in rexlego/src feature code (analysis only)

Stopped early by Agent 1's STOP ORDER (no toolchain, no builds). **I made no source edits.**
`git -C DimensionsRecomp status --short -- rexlego/src` prints nothing, so the tree is clean.
All paths are relative to `DimensionsRecomp/rexlego/src`. Line numbers are from the `perf/opt` tree as read on 2026-11-21.

## Ranked findings (highest value first)

### 1. cheat_menu.cpp:192-215 plus cheat_engine.cpp:362-378: the results list rescans the whole bitmap every frame
- **What is slow:** `DrawResults()` runs every frame while the DEL menu is open and calls
  `engine->TakeResults(kMaxListed)`. That call walks `mask_` from word 0 until it has collected 200 hits.
  The bitmap is `kPhysicalSize / ValueTypeSize / 64` words: 2 Mi words (16 MiB) for a 32-bit scan and
  8 Mi words (64 MiB) for an 8-bit scan. If the remaining hits are few or sit high in memory, the walk
  reads up to 16 to 64 MiB **per frame**, which is milliseconds on the UI thread. The 200 listed rows add
  `ReadValue()`, which does a `VirtualQuery` syscall per row (`IsReadableAddress`, line 182), and
  `IsFrozen()`, which takes `apply_mutex_` and does a linear scan per row (line 416).
- **Proposed change:** the mask only changes inside `RunScan` (on the scan thread, while `scanning_` is
  true). At the end of `RunScan`, before `scanning_ = false`, build the first `kMaxListed` addresses once
  into a `std::vector<uint32_t> cached_results_` with the same loop. `TakeResults(limit)` then returns
  `cached_results_` truncated to `limit` when `limit <= cached size`, and falls back to the old walk
  otherwise. The existing `scanning_` publish/acquire covers the hand-off exactly as it covers `mask_` now.
  `ResetMask()` and the kScanNew path clear the cache. Optional extra: take the `frozen_` set once per
  frame and test rows against that copy, instead of locking once per row.
- **Risk:** low. It shows the same addresses in the same order, because the cache is derived from the
  same mask at the only point the mask changes. It only affects the debug overlay.
- **Verify once a build exists:** run a standalone test that copies `RunScan` and `TakeResults` with a
  fake 512 MiB membase (or a scaled `kPhysicalSize`), randomises masks and value types, and checks the
  old walk against the cached list. Microbench `TakeResults(200)` with hits placed at the top of memory:
  the old cost scales with the bitmap size, the new cost is a copy of 200 entries.

### 2. cheat_engine.cpp:461-484 `FreezeMain`: wakes 20 times a second forever, even with nothing frozen
- **What is slow:** once the engine exists (it is created lazily on the first DEL-menu open,
  cheat_menu.cpp:39-49, and then lives until `Shutdown()`), the freeze thread loops
  `lock(apply_mutex_); walk frozen_ and cheats_; sleep_for(50ms)` until shutdown, whether or not any value
  is frozen or any cheat is enabled. Each applied write also costs a `VirtualQuery` syscall
  (`IsWritableAddress`, line 199) on every tick. The idle cost is 20 wakeups/s plus mutex traffic for
  the rest of the session. The destructor (line 128) also blocks for up to 50 ms waiting for the sleep
  to end.
- **Proposed change (sketch):**
  ```cpp
  // header: std::condition_variable freeze_cv_;
  void CheatEngine::FreezeMain() {
    std::unique_lock<std::mutex> lock(apply_mutex_);
    while (freeze_running_) {
      const bool work = !frozen_.empty() ||
          std::any_of(cheats_.begin(), cheats_.end(), [](const Cheat& c) { return c.enabled && !c.writes.empty(); });
      if (!work) { freeze_cv_.wait(lock); continue; }          // idle: block, no polling
      /* same apply loop as today */
      freeze_cv_.wait_for(lock, std::chrono::milliseconds(50)); // same cadence while active
    }
  }
  ```
  Call `freeze_cv_.notify_one()` after `SetFrozen`, `AddCheat`, `SetCheatEnabled`, `Load`, and in the
  destructor after `freeze_running_ = false` (set the flag under `apply_mutex_`, or notify while
  holding it, so the wakeup cannot be lost). Note that the apply loop then runs with the lock held across
  the wait. That is fine because `wait` releases the lock, and it matches today's behaviour, where the
  loop body holds the lock.
- **Risk:** low. While anything is frozen, the writes are identical at the same 50 ms cadence. The first
  application after a toggle can happen earlier (immediately on notify, rather than within 50 ms), which
  is inside the old jitter window. Shutdown gets faster.
- **Verify:** run a standalone test with a heap buffer standing in for the membase and an injected
  writability check. Count loop iterations over 2 s idle (old about 40, new 0). Measure the time from
  `SetFrozen` to the first store (old up to 50 ms, new well under 1 ms) and destructor latency (old up
  to 50 ms, new about 0). Also check that the bytes written match old vs new over a randomised sequence
  of SetFrozen, AddCheat and SetCheatEnabled calls.

### 3. gpu_native/settings_runtime.cpp:139 to settings_revision.cpp:231-235 `PendingForRenderer()`: mutex every frame on the render thread
- **What is slow:** `NativeSettingsRuntime::CommitFrameBoundary()` calls
  `coordinator_->PendingForRenderer()` every frame. That call takes `State::mutex`. The UI thread takes the
  same mutex every frame in `SettingsRevisionCoordinator::AdvanceFromUI()` (line 175, reached from
  legodimensions_app.h:293 and 397), and also in `Observe()`. When nothing is pending (almost always),
  the call costs an uncontended lock/unlock (about 20 ns) with a small chance of render/UI contention.
- **Proposed change:** add `std::atomic<bool> commit_ready` to `State`. Recompute it under `mutex` wherever
  `sealed`, `failure`, `acknowledged` or `stopped` change: AdvanceFromUI (line 207), Submit (lines 69-72),
  Failed (line 78), TryCommit (lines 264 and 268), and StopFromUI. Store it with release ordering. At the top
  of `PendingForRenderer` add `if (!state_->commit_ready.load(std::memory_order_acquire)) return {};` and
  keep the locked path as is. A stale `true` falls through to the locked check (exact result). A stale
  `false` delays the commit by at most one frame.
- **Risk:** low to medium (it touches a concurrency protocol). The benefit is small unless a profile shows
  contention, so ranked below items 1 and 2.
- **Verify:** run a standalone two-thread test that drives Submit, AdvanceFromUI, TryCommit and Acknowledge
  through randomised interleavings, asserting the same final ack/active state and no commit of a
  superseded ticket. Microbench the idle `PendingForRenderer` (old lock about 20 ns, new about 1 ns).

### 4. scene_distance.cpp:54-58: lock plus two hash lookups per scene instance at load, even at the default scale
- **What is slow:** the `sub_82C6F428` hook (the NuSceneInstance serializer, which runs once per instance
  during level load, possibly thousands of times) always locks `distance_mutex` and calls `Restore()`. That
  does `records.find` followed by `records.erase(address)` (two hash probes) even when
  `instance_distances` is empty, which is always the case at the default scale 1.0. The level hook
  (line 73) already guards with `!level_distances.empty()`.
- **Proposed change:** use the same guard,
  `if(!instance_distances.empty())Restore(instance_distances,instance,base);`, still under the lock. It is
  behaviour-identical because `Restore` on an empty map finds nothing, and `erase` of an absent key is a
  no-op. Inside `Restore`, `records.erase(it)` (when found) instead of `erase(address)` saves a second probe.
- **Risk:** negligible. **Value:** small, tens of microseconds per level load. It is a trivially safe tidy-up.
- **Verify:** run a randomised old-vs-new test of the Restore/Remember sequence on byte buffers, then a
  microbench of 10k serializer calls with an empty map.

### 5. settings_native_hooks.cpp:222-238 Localise and SetText hooks: fine when off, mutex per call when the experimental frontend is on
- **Off (default, `native_settings_frontend=false`, kInitOnly):** each call does one acquire load of
  `literal_bridge` (a plain `mov` on x86) and a branch. That is already the "one predictable branch" ideal,
  so no change is needed.
- **On:** `LookupLiteral` (settings_native_bridge.cpp:136-155) locks `literal_mutex_` and probes
  `literal_value_aliases_` for **every** title string, before the cheap 16-byte prefix test. A cheaper
  order is: if `literal_value_aliases_` is empty, skip the lock; otherwise keep the lock. Or publish the
  alias map as an immutable snapshot (`std::atomic<std::shared_ptr<const Map>>`, copy-on-insert, since
  inserts are rare and happen at layout build time). Only worth doing if a profile shows Localise as hot
  with the option on, so it stays a recommendation.

### 6. settings_native_hooks.cpp:60-64 `Enabled()`: function-local static on hot-ish hooks
- `static const bool enabled = REXCVAR_GET(...)` has dynamic init. Under the MSVC ABI (clang-cl too),
  every call does the thread-safe-static check: it loads the guard and compares it with the TLS
  `_Init_thread_epoch`. That runs per call from `GetBridge()` in the per-frame frontend hook
  `sub_82FEA350`, in the pause-menu hooks `sub_839D08A0`, `sub_839C4D08` and `sub_839D4020`, and in the
  input and sound hooks. The cost is about 1 to 2 ns per call, so the total is negligible.
- **Possible change:** use a namespace-scope `std::atomic<int8_t>` tri-state, latched on first call with
  relaxed ordering (the cvar is kInitOnly). **Rejected for now:** the gain is not measurable at frame level.

### 7. main_menu_extras.cpp:210-211 `MenuExtrasDialog::OnDraw`: atomic exchange every frame
- `g_request.exchange(kNone)` is a locked `xchg` (about 20 cycles) every frame while idle. Doing
  `if (g_request.load(std::memory_order_relaxed) == kNone) return;` first would be equivalent. Ignoring a
  request stored concurrently is safe either way, because the next frame sees it. **Rejected as
  cosmetic** (about 10 ns per frame).

## Looked at and rejected (not per frame, or already cheap)
- **settings_service.cpp:116-121 `QueuedSettings::AdvanceFromUI` (per UI frame):** a thread-id compare, an
  atomic load and two enum compares. Already minimal.
- **settings_revision.cpp:168-179 `AdvanceFromUI` (per UI frame):** an `atomic_flag` RMW plus a mutex to see
  that `queued` is empty, about 40 to 60 ns per frame. An atomic "queued" flag could skip both, but the
  gain is tiny. It could be combined with item 3 if that lands.
- **settings_config.cpp, settings_preferences.cpp, settings_registry.cpp, settings_transaction.cpp:** these
  run only at startup or on menu Apply/Save. `getenv` in `NativeSettingOverrideReason` runs only on
  edit/persist, never per frame.
- **settings_native_bridge.cpp:1007-1055 BeforeFrame/AfterFrame and :81-89 `Text()`:** these run only with the
  experimental frontend on (`GetBridge` returns null otherwise). `TraceTransition` builds strings only when
  the state changes.
- **main_menu_extras.cpp:125-176 hooks:** AboutToShow and the "A pressed" handler are event-driven, and
  `sub_82F03C40` is a pure pass-through.
- **cheat_menu.cpp:319-324 `InstallGraphicsToggles`:** a one-shot plus a change callback. Not hot.

## Follow-ups that need the game or a profiler
1. Confirm how often Localise (`sub_82A435C8`) and SetText (`sub_82EFEFA0`) are called per frame. That
   decides whether item 5 matters with the experimental frontend on.
2. **For the gpu_native owner:** `NativeSettingsRuntime::Active()` (gpu_native/settings_runtime.cpp:137) is
   `std::atomic<std::shared_ptr>::load()`. In the MSVC STL that is a lock-bit spin plus refcount inc/dec,
   which is three locked RMWs per call. Grep its callers. If it is called per draw or per pass, hoist it to
   once per frame.
3. Check render/UI contention on `SettingsRevisionCoordinator::State::mutex` (item 3) in a Tracy or ETW
   capture.

## Files I did not get to (fully)
- settings_frontend.cpp: `FrontendController::Poll` runs per frame only when the frontend is on; I read the
  header only.
- settings_native_bridge.cpp: I read only lines 78-160 and 1005-1057.
- legodimensions_app.h: grep only, for the per-frame heartbeat call sites (lines 293-294 and 397).
- No benchmarks or tests were written (stop order). The verification plans above are the intended
  bench/agent8/features contents.
