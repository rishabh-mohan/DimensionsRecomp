# #19 `d3d12_async_submit`: queue-op ordering, flush callers, locks, native lists (E7.1)

Read-only review. Base = `build/agent2/snap1/DimensionsRecomp/rexglue-sdk` (== 5350b1d; the snap1 copy has no
`.git`, so the orig/ files were hash-checked against snap1 instead). Candidate = `build/agent7/s4-r1s2/`.
Line numbers: `new/sdk/...` = after-file in the candidate; anything else = base path under the SDK root.

| file | sha256[0:16] |
|---|---|
| s4-r1s2.diff | 06b0d371686cd384 |
| new/sdk/include/rex/graphics/d3d12/command_processor.h | ef0dc13da29703c7 |
| new/sdk/include/rex/graphics/d3d12/deferred_command_list.h | e7512824d8e6f967 |
| new/sdk/src/graphics/d3d12/command_processor.cpp (cp) | 05bbce8b7e3fb27d |
| new/sdk/src/graphics/d3d12/shared_memory.cpp | 9e908d31e6f64a31 |
| new/sdk/src/graphics/d3d12/texture_cache.cpp | 4183887c9d625b97 |
| src/graphics/d3d12/deferred_command_list.cpp (unchanged; orig == snap1) | 30ff57446efb5d76 |

All 6 match `SHA256SUMS.txt`; orig/ == snap1 for all 6.

## Q1: every D3D12 queue op, which thread, and ordered after queued splits?

**Verdict: CONFIRMED.** Every direct-queue op the GPU Commands thread does comes after a drain/flush on every path,
except the two §6 exceptions, and both are harmless. §6 misses a few ops (below), none unsafe. No BLOCKER.

Queue inventory (non-vulkan `src/` + `include/`, recursive grep for `GetDirectQueue|ID3D12CommandQueue|ExecuteCommandLists|
->Signal(|->Wait(|UpdateTileMappings|CopyTileMappings|Present(|CreateSwapChain`):
- There is only one queue: `D3D12Provider` creates the direct queue (`src/ui/d3d12/d3d12_provider.cpp:421,430`), getter
  `include/rex/ui/d3d12/d3d12_provider.h:38`. There is no copy or compute queue, and no second CreateCommandQueue in the SDK.
- App code (outside the SDK) also has queues: `DimensionsRecomp/rexlego/src/gpu_native/device.cpp:849` creates its own
  plume DIRECT queue (ECL at 1278/1400/1948/2172), and the `tools/gpu-aot/test_*` files make their own queues. Neither is
  the SDK direct queue or `submission_fence_`, so they are out of scope for split ordering.

| # | op (site) | thread(s) | ordered after queued splits? |
|---|---|---|---|
| 1 | Submit thread `Reset/Execute/Close/ECL/Signal(submission_fence_)` cp:4626-4632 | D3D12 Submit | this *is* the split; FIFO via ring `async_submit_first_` cp:4622,4640 |
| 2 | EndSubmission `ECL` cp:4364, `Signal` cp:4378 | GPU Commands | yes: `DrainAsyncSubmissions` cp:4306-4308 is the first statement, before the allocator-fail `return` cp:4318; no other exit sits between them |
| 3 | CheckSubmissionFence (>=) `Signal` cp:4037 | GPU Commands | yes: drain cp:4024-4026 inside the same `>=` branch, then `EndSubmission` cp:4028 (which also drains); no split can be queued in between (only MaybeSplit on this thread queues one) |
| 4 | shared_memory `UpdateTileMappings` new/sdk/src/graphics/d3d12/shared_memory.cpp:493 | GPU Commands (Q2) | yes: `FlushAsyncSubmissions()` :492 comes right before it; the only earlier returns (:459 zero length, :476 CreateHeap fail) do no queue op |
| 5 | texture_cache `UpdateTileMappings` new/sdk/src/graphics/d3d12/texture_cache.cpp:1264 | GPU Commands (Q2) | yes: flush :1255 runs every heap iteration before the inner loop; the `break` at :1259 only leaves the inner loop; earlier returns :1163/:1168/:1213/:1235 do no queue op |
| 6 | PublishOnDemandMemexport cp:3257 | GPU Commands | no queue op of its own; `EndSubmission(false)` cp:3264 drains internally, then the explicit drain cp:3268-3270; early return cp:3258-3259 happens before any work |
| 7 | IssueSwap → presenter `RefreshGuestOutput` → tracker `NextSubmission`/`Signal` src/ui/d3d12/d3d12_presenter.cpp:565-567 (→ src/ui/d3d12/d3d12_submission_tracker.cpp:97-116) | GPU Commands | normal path: yes, the refresher calls `EndSubmission(true)` cp:2624 (drain) before returning. Early returns cp:2470/2564: no drain. That is §6 exception 1, see below |
| 8 | blank guest output: ui/presenter.cpp:580-587, then paint ui/presenter.cpp:638-641 (`kGuestOutputThreadImmediately`) → d3d12_presenter.cpp paint ECL ~1173, trackers 1175/1177, `Present` 1195, present tracker 1202 | GPU Commands (or the UI thread for on-request paint, ui/presenter.cpp:496) | not drained. §6 exception 2, see below |
| 9 | tracker `AwaitSubmissionCompletion` retry Signal d3d12_submission_tracker.cpp:69-71 (callers e.g. d3d12_presenter.cpp:531, 591) | GPU Commands / paint thread | not drained; signals only the presenter's own trackers. **not in §6** (NIT) |
| 10 | `CaptureGuestOutput` local list, ECL d3d12_presenter.cpp:309 + tracker Signal 310 + CPU wait | caller's thread (no caller in SDK or app grep) | not drained; reads only the guest-output resource. **not in §6** (NIT) |
| 11 | swap chain `CreateSwapChainForHwnd(direct_queue)` d3d12_presenter.cpp:451, `ResizeBuffers` 392 | UI thread | not ordered, no submission_fence_ or split resource involved; same as base |
| 12 | SetupContext `GetDirectQueue` cp:1160, list Close/QI cp:1203/1205 | GPU Commands, before the Submit thread starts (cp:~1952-1955) | n/a (submit_async_ is set to true at cp:1955 only after setup) |
| 13 | ShutdownContext `AwaitAllQueueOperationsCompletion` cp:1971 → CheckSubmissionFence (row 3), then `ShutdownAsyncSubmit` cp:~1974/4646 | GPU Commands | yes |
| 14 | occlusion paths `EndSubmission` cp:6055, 6111, `CheckSubmissionFence` cp:6116 | GPU Commands | yes: they go through rows 2/3 |
| 15 | non-`>=` CheckSubmissionFence wait (cp:~4040+), BeginSubmission throttle cp:4206, RetireOnDemandMemexport fence wait cp:3322-3326 | GPU Commands / guest thread (Retire) | CPU waits only, no queue op. Waiting on a queued split's fence value can't deadlock: the Submit thread never waits on anyone (cp:4611-4612, it only takes `async_submit_mutex_`) |

Exceptions in §6 "Presenter":
- **Exception 1 (refresher early returns cp:2470/2564, then tracker Signal at d3d12_presenter.cpp:567): CONFIRMED harmless.**
  On those returns the refresher records nothing that touches the guest output. `RefreshGuestOutputImpl` still bumps and
  signals the guest-output tracker (565-567), and `RefreshGuestOutput` then returns without painting (ui/presenter.cpp:577).
  Queued splits never reference the guest-output resource, so a tracker value that lands on the queue before them guards
  nothing they touch. In base the same signal also comes before the fallback copy, which is submitted at cp:2630.
- **Exception 2 (blank paint ui/presenter.cpp:580-587): CONFIRMED harmless.** The blank path takes mailbox index
  `UINT32_MAX` (d3d12_presenter.cpp:623-624) and draws only into the swap-chain back buffer, using the presenter's own
  paint list and trackers. No split resource or `submission_fence_` is involved. Paint-before-split on the queue only
  reorders independent work.

Things §6 misses (none unsafe):
- NIT: table omits rows 9-11 (tracker retry Signals, `CaptureGuestOutput`, swap-chain creation/resize/`Present`). All use
  presenter-owned resources/fences only; worth listing so a future reviewer doesn't re-derive it.
- NIT: no ImGui/debug-overlay or immediate-drawer queue access exists (immediate drawer records into the paint list,
  no `GetDirectQueue` use); no readback path touches the queue directly (memexport readback goes through the deferred
  list + `AwaitAllQueueOperationsCompletion`, cp:3540 → row 3).

## Q2: FlushAsyncSubmissions callers are GPU-Commands-only?

**Verdict: CONFIRMED.** There are exactly two call sites (grep `FlushAsyncSubmissions|DrainAsyncSubmissions` over new/ + base):
new/sdk/src/graphics/d3d12/shared_memory.cpp:492 and new/sdk/src/graphics/d3d12/texture_cache.cpp:1255. Drain is also called directly at
cp:3269, 4025, 4307 (all GPU Commands, rows 2/3/6).

Caller chains, all ending in CommandProcessor packet handlers on the worker `XHostThread` (src/graphics/command_processor.cpp:188-190,
`WorkerThreadMain` 249; `CallInThread` 209 also runs there):
- shared_memory flush :492 ← `AllocateSparseHostGpuMemoryRange` ← `SharedMemory::EnsureHostGpuMemoryAllocated`
  (src/graphics/shared_memory.cpp:764) ← only `RequestRanges` (:455) ← `RequestRange` (:539-541) and texture-cache batches. Callers:
  - IssueDraw: cp:2925, 2949, 2959; `primitive_processor_->Process` cp:2738 → src/graphics/primitive_processor.cpp:921.
  - IssueDraw `RequestTextures` cp:2812 → new/sdk/.../texture_cache.cpp:728 → src/graphics/pipeline/texture/cache.cpp:580
    (batched) / :591→:956 (`LoadTextureData`).
  - IssueSwap `RequestSwapTexture` cp:2294 → new/sdk/.../texture_cache.cpp:1426 → `LoadTextureData`.
  - 3D-as-2D wrapper new/sdk/.../texture_cache.cpp:2072 (reached from texture binding on the draw path) → `LoadTextureData`.
  - IssueCopy `Resolve` cp:3769, 3784 → src/graphics/d3d12/render_target_cache.cpp:1237.
- texture_cache flush :1255 ← `EnsureScaledResolveMemoryCommitted` ← src/graphics/d3d12/render_target_cache.cpp:1230 (Resolve, IssueCopy)
  and src/graphics/pipeline/texture/cache.cpp:428/432 (`CommitPreparedTextureLoad` ← :586 RequestTextures / :960 LoadTextureData).
- Not reachable from other threads:
  - `ProvideOnDemandMemexportThunk` (cp:3430-3440, guest threads via xmemory.cpp:608-611 under the global lock) only calls `RetireOnDemandMemexport` (cp:3307), with no RequestRange or flush.
  - `MemexportCpuWriteWatchThunk` (cp:3491) only pushes to a vector under a mutex.
  - Watch/invalidation callbacks (shared_memory `MemoryInvalidationCallbackThunk` :544, texture `WatchCallback` cache.cpp:739-760, primitive processor :1432/:1568) only mark ranges.
  - `GraphicsSystem::ClearCaches/InvalidateGpuMemory` go through `CallInThread` (graphics_system.cpp:366, 370).
  - The UI thread never calls the texture cache or shared memory.
- NIT: `DrainAsyncSubmissions`' correctness argument ("splits are queued only by this thread", cp:4591-4593) is a
  thread-affinity assumption with no assert. A `assert(IsInWorkerThread())`-style check in `FlushAsyncSubmissions` would make
  any future off-thread caller fail loudly.

## Q3: locks held around the flush; what the Submit thread touches

**Verdict: CONFIRMED (no lock-order hazard).** Two NITs.
- The global critical region is **not** held when the flush can run:
  - `RequestRanges` calls `EnsureHostGpuMemoryAllocated` at src/graphics/shared_memory.cpp:455 and only takes `global_critical_region_.Acquire()` later, at :475, in its own scope.
  - Texture path: `PrepareTextureLoad` takes and drops the global lock in a block scope (pipeline/texture/cache.cpp:379-387). `CommitPreparedTextureLoad` calls `EnsureScaledResolveMemoryCommitted` (:428/:432) with no lock and only takes the lock afterwards (:447).
  - Resolve (render_target_cache.cpp:1162-1240) takes no lock around :1230/:1237.
  - IssueDraw/IssueSwap/IssueCopy hold no mutex at these calls.
- Even if a guest thread held the global lock, the drain can't deadlock: the Submit thread's loop (cp:4614-4643) takes only
  `async_submit_mutex_`, releases it around the D3D12 work (cp:4623/4638), and never takes the global lock or any CP mutex.
  `async_submit_mutex_` is used only at cp:4518, 4577, 4594, 4614, 4654.
- `DeferredCommandList::Execute` (src/graphics/d3d12/deferred_command_list.cpp:228-658) takes no lock. Besides the
  recorded stream and the two native lists, it reads only:
  - `command_processor_.GetD3D12PipelineByHandle` (dcl.cpp:622; :400 is counters-only), which leads to cp.h:200-201, then `pipeline_cache_`, then
    pipeline_cache.h:101-102. That is an atomic acquire load of `Pipeline::state` (pipeline_cache.h:352), published by the
    pipeline-creation path. Pipeline objects are destroyed only by `pipeline_cache_.reset()` in ShutdownContext (cp:2067), which runs after
    `ShutdownAsyncSubmit` (cp:~1974). The cache-clear block doesn't touch them. Safe.
  - `command_list_`, `command_list_1_` (owned by the Submit thread while a split is queued; GPU Commands touches them only
    after a drain, rows 2/12/13).
  - Static counters dcl.cpp:91-103, compiled out (`REX_D3D12_DEFERRED_COUNTERS` 0, dcl.cpp:26-27). **NIT**: they race
    only in a counters build; this is already §11.6.
  - The Submit thread also reads `submission_fence_` (set once in SetupContext) and `GetD3D12Provider()` (immutable).
    `chunk.deferred_command_list.Reset()` (cp:4633) works on the slot's own list, which GPU Commands no longer touches after
    EndSubmissionAsync handed it off.
- **NIT (latent, no current race):** Execute passes *CPU* descriptor handles to calls that read the descriptor contents at
  call time:
  - `OMSetRenderTargets` dcl.cpp:518-520, `ClearRenderTargetView` :431-433, `ClearDepthStencilView` :425-427, `ClearUnorderedAccessViewUint` :437-442.
  - Async, that read happens while GPU Commands records N+1..N+k, not before it.
  - Current sources are immutable for the descriptor's lifetime:
    - Per-RT `descriptor_draw()/descriptor_load_separate()` (render_target_cache.cpp:4114, 4120-4123, 4574, 4655-4658, 4743) are written once at RT creation. They are freed only via `RenderTargetCache::ClearCache/DestroyAllRenderTargets` (pipeline/render_target/cache.cpp:343-381), which run only from cp:4395+ (after the drain at cp:4307 and `AwaitAllQueueOperationsCompletion`) or at shutdown.
    - The null RTVs (render_target_cache.cpp:4738-4740) are created once at init.
    - No d3d12 code records `D3DClearUnorderedAccessViewUint` at all.
  - Any future recorder that rewrites or recycles a CPU descriptor within the in-flight window would race. Worth a comment in
    deferred_command_list.h next to these recorders.
- Resource/heap pointers in the stream are kept alive by submission-number retirement (deletion waits for
  `submission_completed_ >=` the split's number, which the Submit thread signals at cp:4632). So the split value covers
  them the same way as in sync mode.

## Q4: other native command lists recorded by GPU Commands during an open submission?

**Verdict: CONFIRMED (none).**
- In the SDK's d3d12 graphics code, `command_list_`/`command_list_1_` are the only native `ID3D12GraphicsCommandList` the CP uses
  (created cp:~1185-1205). All recording during a submission goes through `GetDeferredCommandList()`. Examples:
  shared_memory `UploadRanges` new/sdk/.../shared_memory.cpp:505-507, render_target_cache.cpp:4745 and others.
  GPU Commands calls `command_list_` natively only in EndSubmission (after the drain, cp:4307), SetupContext
  (before the thread starts) and Shutdown (after `ShutdownAsyncSubmit` joins).
- The other native lists are the presenter's own: `CaptureGuestOutput` local list (d3d12_presenter.cpp:260) and
  `paint_context_.command_list` (d3d12_presenter.cpp:1501), with their own allocators and trackers. Neither is ever handed to
  `DeferredCommandList::Execute` or to the Submit thread, so a split can't execute them. Their queue ordering is in Q1 rows 7-10.
- There is no `GetCommandList()` accessor anywhere in the SDK. Outside cp.cpp/.h, the only non-vulkan `command_list_`
  member is the presenter's UI draw context (include/rex/ui/d3d12/d3d12_presenter.h:32-41), which is the paint list.

## Findings summary

- NIT: §6 table doesn't list the tracker retry Signal (d3d12_submission_tracker.cpp:69-71), `CaptureGuestOutput`
  (d3d12_presenter.cpp:309-310) or swap-chain create/resize/Present. All are presenter-owned and harmless.
- NIT: `FlushAsyncSubmissions`/`DrainAsyncSubmissions` depend on GPU-Commands-only callers (cp:4591-4593) but don't assert it.
- NIT: Execute reads CPU descriptors at Submit-thread time (dcl.cpp:425-442, 518-520). Safe today because the
  descriptors are immutable until a drained cache clear, but fragile and undocumented.
- NIT: dcl.cpp:91-103 counters race in counters builds only (already §11.6).
- No BLOCKER, no SHOULD: every SDK direct-queue op on GPU Commands that can touch split-visible resources or
  `submission_fence_` comes after a dominating drain/flush. Flush callers are GPU-Commands-only and hold no lock.
  The Submit thread takes only `async_submit_mutex_`.
