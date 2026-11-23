# #21 code read for task #27 (read-only helper of Agent 10)

Status: complete, except the UNCLEAR items in section 6. No builds, runs or git writes. Written 2026-11-23, about 06:05 local; updated about 06:40 local (U2 and U4 resolved, U1 narrowed to U1a, one new pre-existing th2 finding F-CA in section 6).

Authority: snap1 = `build/agent2/snap1/DimensionsRecomp/rexlego/src/`. Every `gpu_native/...` and `src/...` citation uses snap1 line numbers. The #21 change was read from `build/agent7/s4-t1/s4-t1.diff`. One file outside snap1 was opened (plume, section 3); it is marked there.

Roles raised by #21 (values 1 and 3 raise the priority; values 2 and 3 opt out of EcoQoS):
- **recorder** = RecorderMain (native_worker.cpp:152-194). th3 only; created at :346.
- **coordinator** = CoordinatorMain (:198-257). th3; WorkerMain hands off to it at :260. Already ABOVE_NORMAL from :349.
- **worker** = WorkerMain (:259-297). th2. Already ABOVE_NORMAL from :349.
- **recording queue** = RecordingQueue::Run (native_recording.cpp:111-136). th2.
- **prepare** x2 = NativePreparationQueue::Run (native_preparation.h:24-38). th2 and th3.
- n0: StartNativeWorker returns at native_worker.cpp:339, so no chain thread exists.

Where the present runs (used in sections 2 and 3):
- SwapHookQueued submits SwapHook as a kRecorderBarrier task (draw.cpp:5448).
- th3: CoordinatorMain forwards non-capture tasks to the recorder (native_worker.cpp:240-243). So SwapHook, PresentTexture and LimitFrameRate run on RecorderMain.
- th2: they run on WorkerMain.
- FSR3 on: CoordinatorMain forwards every task to the recorder (:221-234).

## 1. MP3: GPU->CPU paths the guest can observe

Only three readback-heap allocations exist in snap1 src:
- texture_readback.h:66 (row R1)
- queries.cpp:263 (queries)
- device.cpp:2597 (diagnostic snapshot)

gpu_timestamps.h reads back a query pool, for profiling only. The other `map()` hits read or write UPLOAD buffers, so they are not GPU->CPU paths. Examples: draw.cpp:3257/3279/3321/3562-3563, created as UPLOAD at :3560.

| # | Path | GPU copy issued by | Made guest-visible by | Completion mechanism | Timing dependency | Class |
|---|---|---|---|---|---|---|
| R1 | LockRect: hooks_texture.cpp:31-36 -> MaterializeTextureForCpuRead textures.cpp:3872-3907 -> MaterializeResolvedTextures :3771-3834 -> ReadbackTexturesRaw texture_readback.h:36-107 | The guest thread calling LockRect (NORMAL), holding LockRecording (textures.cpp:3873). LockRecording first drains the chain (device.cpp:777 -> NativeWorkerDrain native_worker.cpp:507-548). | The same guest thread: map+copy at texture_readback.h:97-105, then PublishResolvedTextureWriteback textures.cpp:3755-3769 under LockPhysicalWriteback. | HostDevice::Synchronize(kResource) device.cpp:1256-1320 -> WaitForSubmissionLocked :648-680. That function checks for UINT64_MAX (:652), waits on the fence (:661) and then checks completed >= value (:669). On failure the writeback is dropped and a warning is logged (textures.cpp:3903-3905). | None. th3 drains by waiting on a CV for a marker (:510-527). th2 drains with a try_lock + 200 us timed-CV re-poll that exits only when the queue is idle (:534-546); there is no timeout fallback. Synchronize refuses inside a preparation scope (device.cpp:1258-1262); the code path decides this, not scheduling. | FENCED + SYNC |
| R2a | Inline pool copy: hooks_buffer.cpp:320 -> MaterializePoolCopyTextureDependencies textures.cpp:3840-3857 -> the R1 machinery | Guest thread | Same guest thread | As R1 | None | FENCED + SYNC |
| R2b | Ordered pool copy (th3). This is also the "on-demand memexport readback" named at hooks_buffer.cpp:160-162. | RecorderMain: the barrier task at hooks_buffer.cpp:173-175 runs R1's copy, fence wait and publish. It runs inline if the caller is already the recorder (:168-171). | RecorderMain publishes the guest bytes. The capture thread (coordinator) first waits with WaitAllPreparation (:165, job.ready.wait at draw.cpp:5650), then with NativeRecorderWaitExecuted (:176, a CV wait). It then reads the atomic result with acquire (:178). | Fence as in R1, plus a CV barrier hand-off | None. A failed materialize logs an error and skips the copy (:178-182). The outcome is deterministic except at shutdown, where NativeRecorderWaitExecuted also returns on g_stop (native_worker.cpp:465-471). | FENCED + SYNC |
| R3 | Completion callbacks (InsertCallback): hooks_device.cpp:292-324 -> EnqueueCompletionCallback device.cpp:1327-1338 | No copy. The callback is tagged with submission = last + open list (:1334), under LockRecording (which drains first). | The guest thread that polls: PollCompletionCallbacks device.cpp:1340-1381, called from SwapHook (draw.cpp:5380/5436/5456) and from BlockUntil*/BlockOnFence (hooks_device.cpp:189/199/222/228/263; the blocking ones call Synchronize first at :188/197/260). Never runs on a chain thread (:1342; OnNativeWorkerThread at native_worker.cpp:333-335). | GetCompletedValue in RefreshCompletedSubmissionsLocked device.cpp:621-639 (ignores UINT64_MAX), then PopReady(completed) at completion_queue.h:17 | Only the delivery point. The poll does recording.try_lock and returns if the gate is busy (device.cpp:1363). It does a blocking lock only with LEGO_NATIVE_BATCH_COMPLETION_CALLBACKS=1, which is not in the F1 allow-list. Scheduling can change which poll delivers a callback, but a callback never runs before its fence. | FENCED |
| R4 | Occlusion queries (queries.cpp ~150-199) | - | Guest poll (GetData) | Not ready until GetCompletedValue >= value. UINT64_MAX gives a failure (:176). Map at :186. | The number of polls varies; the value does not. | Covered by row F3; not re-rated here |

Not guest-visible (listed for completeness):
- Diagnostic snapshot and long-probe readbacks (device.cpp:122-187, 2597-2612; opt-in, device.h:188).
- GPU timestamps (gpu_timestamps.h).
- Present throttle (device.cpp:1730-1753): an event with a 1000 ms timeout, skipped on UINT64_MAX. It carries no data.
- Latency waitable (device.cpp:2439, 1000 ms timeout).

Memexport has no separate GPU->guest path. The word appears only in comments (hooks_buffer.cpp:101/161/271, pool_copy.h:37, texture_writeback_merge.h:14).

Helper headers:
- texture_readback.h and texture_writeback.h are included only by textures.cpp:56-57.
- texture_readback_format.h, texture_writeback_coverage.h and texture_writeback_merge.h are included only through those two.
- completion_queue.h is included only by device.cpp:9.

Resolve results reach guest memory only through R1/R2, via the state `resolved_on_host && !guest_backing_current` (textures.cpp:3847/3894).

**MP3 result: no TIMING-DEPENDENT readback.** No path reads results N frames later without a fence, falls back to stale data on a timeout, or busy-waits.

## 2. Spin-waits and waits on raised threads (input to (b))

Greps over all of snap1 src:
- Sleep(0), SwitchToThread, this_thread::yield, YieldProcessor, _mm_pause
- `while(...)` loops on load, exchange, test_and_set or GetCompletedValue; compare_exchange; `for(;;)`
- wait_for / wait_until; WaitFor*

Spins (burn CPU):
- **S1** gpu_native/device.cpp:1817 `while (clock::now() < next) YieldProcessor();` in LimitFrameRate (:1797-1822).
  - It spins at most 0.5 ms, after a high-resolution timer wait (:1811-1815), and only when fps_limit > 0 (:1802).
  - It runs on the present thread: the recorder in th3, the worker in th2, a guest thread in n0.
  - It waits on the clock, not on another thread, so it is **not an inversion**.
  - It is off in F1, F3 and W8b (U2 resolved). Every arm of those matrices sets the cvars `native_settings_frontend=false`, `native_fps_limit=0` and `framerate_limit=0` (first arms: matrix-s4t1-f1.json:40-42, matrix-s4t1-f3.json:39-41, matrix-w8b-draft.json:41-43). No matrix sets the env LEGO_NATIVE_FPS_LIMIT.
  - With the settings frontend off, no NativeSettingsRuntime is published (src/legodimensions_app.h:155-159). AcquireNativeSettingsRuntime (gpu_native/settings_runtime.cpp:179) then returns null, so PresentTexture uses LegacyFrameRateLimit (device.cpp:1881): the env override, else the cvar (device.cpp:1788-1795), here 0. LimitFrameRate returns at :1802.
  - With the runtime active, the value would come from the same cvar (src/settings_registry.cpp:100-113, gpu_native/settings_snapshot.cpp:64-65) unless the env overrides it (settings_runtime.cpp:38, :66).
  - W1 is not verified: build/agent7/s4-t1/ has no W1 matrix file. Its row is in queue-s4t1.jsonl, which I did not open.
- **S2** src/native_heap_journal.h:49-61: a per-bucket CAS spin with _mm_pause. Only src/native_skin_diagnostics.cpp includes it. No gpu_native file does, and chain threads run no guest code, so no chain role can reach it.
- **S3** src/gpu_wait_backoff.cpp:261/265/277 (_mm_pause, SwitchToThread). It is compiled only under `if(NOT LEGODIMENSIONS_NATIVE_GPU)` (rexlego/CMakeLists.txt:184-188) and it hooks guest functions. It is not in native builds.
- Not counted: the bounded library spin that std::mutex/recursive_mutex do before blocking.

Sleep or timed polls (they block; they do not spin):
- **P1** pipeline_library.cpp:342 `while (saving_.load()) sleep_for(5ms)` in Stop() (:341). It waits for a detached save thread (:334-338), and it sleeps. Its only caller is StopPipelineLibrary (:716-729, call at :724). That runs only in the HostDevice::Create failure path (device.cpp:876, before the worker exists) and in HostDevice::Shutdown (device.cpp:949, after StopNativeWorker at :925). No chain role runs it (U4 resolved).
- **P2** native_worker.cpp:534-546 (th2 NativeWorkerDrain): try_lock, then a 200 us timed CV wait. It returns at :508 for t_running_task or the worker thread, so the worker, recorder and coordinator never run it. :508 does not exclude the prepare and recording-queue threads. The th2 pool job does not reach it under the allowed envs (U1a). The th2 recording-queue thread does reach it, through color-alias handoff completion (F-CA, section 6).
- **P3** pipeline_async.h:61-66: the drawing thread waits up to LEGO_NATIVE_PSO_ASYNC_WAIT_US on a NORMAL PSO compile thread, then skips the draw (pipeline_async.h:4-6). This is off by default, and LEGO_NATIVE_PSO_ASYNC is not in the allow-list (build/agent8/w8w9/ENV-KEYS-F1.txt:19).

What each raised role blocks on. Every wait is kernel-blocking; none spins.

| Role | Blocks on | Whose progress (priority with #21 = 3) |
|---|---|---|
| recorder (th3) | g_record_ready CV native_worker.cpp:159; job.ready.wait draw.cpp:4604; NativeReplayLock draw.cpp:4605 and LockRecording inside tasks; fence wait device.cpp:661; present throttle :1740; latency waitable :2439; timers :1815/:1872 (opt-in) | Coordinator and prepare (raised); a guest thread holding the recording gate (NORMAL); GPU; clock |
| coordinator (th3) | g_queue_ready CV :203; NativeRecorderWaitExecuted :220 and hooks_buffer.cpp:176; job.ready.wait draw.cpp:5626/5650, after stealing unclaimed chunks (:4356-4364) | Recorder and prepare (raised) |
| worker (th2) | g_queue_ready CV; recording gate :270; job.get() draw.cpp:5695; RecordingQueue backpressure and Wait (native_recording.cpp:151, 166-170, 302-305); fence and present waits as for the recorder | Prepare and recording queue (raised); a guest thread holding the gate (NORMAL); GPU |
| recording queue (th2) | Work CV native_recording.cpp:117; work.prepared.get() :123; during tape play, LockRecording from color-alias handoff completion (F-CA): P2 polling, then the gate | Prepare (raised); the gate holder, which is the worker (raised) or a guest thread (NORMAL) |
| prepare x2 | Queue CV native_preparation.h:24-38; in th3, NativeRecorderWaitExecuted(batch.barrier) draw.cpp:4463; job.ready.wait preparation_dependencies.h:81 | Recorder and other prepare jobs (raised) |

**Priority-inversion cases (an ABOVE_NORMAL thread spinning with Sleep(0), yield or pause on a NORMAL thread): none found.**

Raised threads block on NORMAL threads in only two places:
- (a) A guest thread holding the recording gate (draw.cpp:4605, native_worker.cpp:270, LockRecording inside tasks). In th2 this also covers the recording-queue thread in F-CA, which polls every 200 us and does not spin.
- (b) The PSO_ASYNC wait, which is off.

A blocked raised thread is not runnable, so it takes no CPU from the holder. The holder could only be delayed if the other raised threads kept every core busy. They do not sustain that, because they wait on the same chain: the coordinator waits on the recorder (:220) and prepare waits on the recorder barrier (draw.cpp:4463).

## 3. MP5b: device loss

**GetDeviceRemovedReason call.** A grep of snap1 src for GetDeviceRemovedReason, DXGI_ERROR_DEVICE_REMOVED/HUNG/RESET and DEVICE_REMOVED finds one call: gpu_native/pipeline_library.cpp:445, in PrepareOne (:430-447).
- PrepareOne runs on the PSO prepare worker threads during startup PSO recipe preparation.
- When CreateGraphicsPipelineState fails, it returns PrepareResult::kRemoved if the device reports removal, otherwise kFailed.
- That is classification only: no recovery and no wait.

**DXGI_ERROR_DEVICE_* constants.** None appear in src. A failed Present is logged (device.cpp:2253-2255, at most 8 times) and the frame continues.

**Wording of §9.2.** "pipeline_library.cpp:445 is the only device-removed handling" holds for GetDeviceRemovedReason calls only. Device loss is also handled by these UINT64_MAX checks:
- device.cpp:631-637: RefreshCompletedSubmissionsLocked ignores the value.
- device.cpp:652-659: WaitForSubmissionLocked refuses and logs "cannot wait for submission after device removal".
- device.cpp:669-672: check after the wait.
- device.cpp:1736: the present throttle is skipped.
- queries.cpp:176: GetData returns failure.
- gpu_timestamps.h:107-111: timestamps are disabled ("device_removed").

**Chain-thread waits on a lost device.** The GPU-dependent waits a chain role can run are:
- (1) Synchronize -> WaitForSubmissionLocked -> plume `waitForCommandFence`, on the recorder (th3), the worker (th2) or a guest thread.
  - Live tree, outside snap1: DimensionsRecomp/thirdparty/plume/plume_d3d12.cpp:2856-2873.
  - The loop returns when completed == UINT64_MAX or completed >= target. Otherwise it waits on the fence event with INFINITE, and it also returns if that wait fails.
  - D3D12 sets every fence to UINT64_MAX on removal, and that satisfies pending SetEventOnCompletion registrations (documented D3D12 behaviour), so the wait wakes and returns.
  - The pre-check at device.cpp:652 stops new waits after removal.
- (2) Present throttle: 1000 ms timeout, plus the UINT64_MAX skip.
- (3) Latency waitable: 1000 ms timeout. A lost swap chain costs at most 1 s per present; it does not hang.

All other chain-thread waits are CV or future waits on another chain thread's progress. That progress continues because (1)-(3) return. I found no INFINITE wait on an object that device loss would leave unsignaled, and no spin on GetCompletedValue.

**#21 adds no device call.**
- s4-t1.diff adds 51 lines. A token scan of the added lines finds only these calls: getenv, GetCurrentThread, SetThreadPriority, SetThreadInformation (ThreadPowerThrottling), GetThreadPriority, GetCurrentThreadId and REXLOG_INFO, plus the ApplyNativeChainPriority/Impl hook and an atomic counter.
- It makes no D3D12, DXGI, plume or device call.
- Call sites: native_worker.cpp recorder, coordinator and worker (after :154/:199/:261 in before/ numbering), native_recording.cpp after :112, native_preparation.h after :26.

## 4. MP4 spot-check (build/agent7/s4-t1/check/MP4-STATIC.md against snap1)

| MP4 citation | snap1 finding | Verdict |
|---|---|---|
| native_worker.cpp:238 capture run | `if (task.capture) task.run();` on CoordinatorMain/WorkerMain | AGREE |
| native_worker.cpp:221-234 FSR3 forward | Every task goes to NativeRecorderSubmit; the barrier flag is set for present/kRecorderBarrier (:231) | AGREE |
| draw.cpp:5181-5194 | DrawVerticesHookQueued lambda: full-prep branch :5182-5185 (CaptureFullDraw :5183); FSR3 branch :5187-5194 (CaptureShaderBindings :5190) | AGREE |
| draw.cpp:5209-5221 | Indexed twin: :5211-5214 and :5216-5221 (CaptureShaderBindings :5217) | AGREE |
| draw.cpp:4949 in CaptureFullDraw :4838 | thread_local captured_pairs :4929. The only callers are :5183 and :5212 (grep). | AGREE |
| draw.cpp:5111 in CaptureParallelDraw :5102 | The only callers are :5197 (guarded by :5195) and :5222. Early return at :5104-5105. | AGREE |
| Pool posters native_recording.cpp:158, draw.cpp:5093, draw.cpp:4594 | Exactly these three. A grep of all src finds no other caller of PostNativePreparation, PostNativePreparationDetached or PreparationQueueInstance. The other hits are definitions (native_recording.cpp:509-519, including StopNativePreparation :513) and declarations (native_recording.h:75-76). | AGREE |
| FlushNativeDrawBatch draw.cpp:5687-5711 | job.get() at :5695; DispatchDraw at :5704 on the flushing thread | AGREE |
| PrepareFullDrawChunk draw.cpp:4462-4506 | DrawPreparationScope :4475; PrepareDrawWork :4482; DispatchDraw :4486; PrepareFollowers :4492 (defined :4429) -> PrepareFollowerFull :4385 (scope :4405, DispatchDraw :4410). It first blocks in NativeRecorderWaitExecuted(batch.barrier) at :4463, which MP4 does not cite. | AGREE |
| RunPreparationChunkHere draw.cpp:4356-4364; t_on_coordinator :4266, set :5677-5679 | It runs only while t_on_coordinator is set, which happens only in RecordDeferredNativeTask (called on the coordinator at :239) | AGREE |
| REX_HOOK entries draw.cpp:5747/5748 | sub_83FC6640/sub_83FC6A58 -> Draw*HookQueued | AGREE |
| device.cpp:774-777, :755, :762-768 | The drain condition is at :777 (the function spans :774-779) | AGREE |
| native_worker.cpp:260, :270/:289/:290, :108-134, :510-527, :528-546, :310-312, :333-336 | As cited | AGREE |
| MP4 line 51: the capture "pushes onto g_queue" | Staged by default: NativeWorkerSubmitCapture :392-408, then FlushStagedCapturesLocked pushes one capture=true kDeferred task (:355-366). With LEGO_NATIVE_STAGED_CAPTURES=0 it pushes directly (:393-395). Either way it runs at :238. | AGREE (nuance) |

Numbering note: RATE-REQUEST §6 says "StartNativeWorker returns early at :380". That is after/ numbering; snap1 (before/) has the return at :339. Cosmetic only.

## 5. Verdict input

**(b) "value 3 is SAFE in F1/F3/W1/W8b": nothing found that #21 introduces. One pre-existing th2 hazard should be watched (F-CA).**
- No raised chain thread spins on a NORMAL thread.
- The only spin a chain role can run is S1. It waits on the clock, and it is off in the F1/F3/W8b matrices (U2 resolved). W1's settings were not verified from a file.
- Every chain wait is kernel-blocking or a sleeping poll (P2).
- Every guest-visible readback is fence-gated and synchronous. Raising priority can only move *which* guest poll first sees completion (R3, R4), never the value.
- On device loss no chain thread is left in an endless wait.
- The th2 pool job does not take the recording gate under the allowed envs (U1a).
- Pre-existing th2 hazard (F-CA, section 6). By this read, color-alias handoff completion can deadlock the th2 recording-queue thread against the worker.
  - #21 does not create it, and no spin is involved.
  - If the handoff is in the tape that Immediate() flushes, it deadlocks at any priority. Only the case of a tape posted earlier depends on scheduling, so #21 could change how often that case hangs, in either direction.
  - If th2 arms already complete without hangs, the path is not being reached in those scenes. #21 does not decide whether a handoff happens.
  - Suggested guard: treat any th2 hang or timeout in a #21 arm as possibly F-CA, and compare with the #21-off arm.
- Caveats, which are performance or opt-in matters rather than safety:
  - Under CPU saturation, NORMAL guest threads may get less CPU (pacing, light share). The W8b guards cover this.
  - P3 can skip draws when timing changes, but PSO_ASYNC is not allowed in these rows.
  - With FSR3 on, every task runs on the recorder. The analysis above still applies.
  - U1a holds only while LEGO_NATIVE_RETAINED_DRAW_STATE, LEGO_NATIVE_VIEWPORT, LEGO_NATIVE_NO_DRAW_ARENA and LEGO_NATIVE_SHADER_PACK(+_TRIGGER) stay at their defaults. None of them is in the allow-list.

**(c) accept the MP4 restatement and the §9 reads: supported, with one wording fix and one addition.**
- 14 MP4 citations agree with snap1.
- §9.1: no TIMING-DEPENDENT readback.
- §9.2: replace "only device-removed handling" with "only GetDeviceRemovedReason call". Also list the UINT64_MAX guards from section 3. This is a wording fix, not a safety issue.
- MP4 gap 2 (pool callees and tape External closures):
  - The pool side is closed (U1a).
  - On the tape side, one closure family takes LockRecording on the th2 recording-queue thread (F-CA). Record it as a known pre-existing th2 issue, not as lock-free.

## 6. UNCLEAR items and follow-up findings

- **U1a (resolved for the allowed envs): the th2 pool PrepareDrawWork path does not reach LockRecording.**
  - The pool job (draw.cpp:5093-5096) runs PrepareDrawWork, which spans draw.cpp:1660-1673. The earlier range ":1660-1882" was wrong; :1675-1881 are FinishPipeline and GetPipeline.
  - The job has no DrawPreparationScope. t_preparing_draw is set, commands is nullptr and resolve_misses is false.
  - Why it matters: in th2 the worker holds the whole gate (native_worker.cpp:270) while FlushNativeDrawBatch waits for these jobs (draw.cpp:5695). A LockRecording call from a job would stall th2, with or without #21.
  - A name-level call graph over snap1 src found these candidate paths. Each is guarded on the pool thread:
    - PrepareCachedTexture (textures.cpp:2561-2582) -> QueuePreparedTextureUpload returns false at textures.cpp:233 when commands is null, so RetireResource is not reached.
    - BindConstants (draw.cpp:982-1290):
      - BindPreparedConstants needs t_recording_draw (:990-991), which is set only on the flushing thread (:5703).
      - NativeTextureExtent and SurfaceColorOutputScale (:1046-1047, :1080-1081) and PrepareTextureBinding (:1116-1126) are skipped when t_preparing_draw is set.
      - ResolveTextureResource (:1051-1060) needs LEGO_NATIVE_VIEWPORT.
      - The allocation at :1252-1254 uses t_preparing_draw->allocation.
      - :1259-1273 call AllocateDrawUpload (which locks at device.cpp:1229) only when LEGO_NATIVE_RETAINED_DRAW_STATE=0 (draw.cpp:303-310; on by default).
      - RetireResource at :1287 needs LEGO_NATIVE_NO_DRAW_ARENA.
    - PrepareDrawGeometry (draw.cpp:1498-1658) and PrepareDrawGeometryLegacy (:1293-1496):
      - Every Resolve* call is behind resolve_misses (:1624-1653, :1460-1491).
      - BoundShaderAddress returns early while t_shader_bindings is set (shaders.cpp:889-894; ShaderBindingsScope at draw.cpp:1661).
      - PollPrecompiledShaders locks only with LEGO_NATIVE_SHADER_PACK and _TRIGGER (shaders.cpp:601-609).
  - None of those envs is in the allow-list (build/agent8/w8w9/ENV-KEYS-F1.txt:19).
  - Limit: the graph is name-level. It does not model virtual calls, function pointers or methods defined inside classes, so this is strong evidence, not a proof.
- **F-CA (new, pre-existing, th2 only): color-alias handoff completion takes LockRecording on the recording-queue thread.**
  - In th2 the frame command lists are PreparedCommandList (device.cpp:485 -> native_recording.cpp:529-531), and BeginFrameCommandsLocked returns them (device.cpp:705/743). Their tapes play on the recording-queue thread (native_recording.cpp:124).
  - DecideSurfaceColorAlias creates a handoff with retire_ = HostDevice::RetireResource (textures.cpp:1699-1705).
  - Two paths put the handoff on the frame list:
    - ApplySurfaceColorAliases (:1718-1732), called directly or via PrepareSurfaceColorAlias (:1734-1738). Callers are draw.cpp:2644, draw.cpp:3745 and textures.cpp:2738; draw.cpp:4477 is the th3 preparation path.
    - MarkSurfaceWritten (:1769-1770).
  - On a deferred list both record a ResourceCommand (color_alias_publication.h:37-38, :81-82; native_recording.cpp:310-316).
  - At play the closure gets the raw list and runs Complete() (color_alias_publication.h:51 or :83), which calls retire_(source) (:32).
  - In th2, RetireResource reaches LockRecording at device.cpp:1416; the queue branch at :1412 needs FULL_DRAW_PREPARATION. LockRecording runs NativeWorkerDrain (device.cpp:777 -> native_worker.cpp:528-546, P2) and then takes the gate.
  - Case 1, by this read a deadlock:
    - The worker holds the gate (:270) and waits for the recording queue. That wait is Immediate() -> RecordingQueue::Wait (native_recording.cpp:302-305, 166-170), reached from Synchronize (device.cpp:1278), submit (:1400) and the other NativeImmediateCommands sites, or Post backpressure (:151).
    - The recording-queue thread keeps polling every 200 us, because g_executing stays true. Neither thread can proceed.
  - Case 2:
    - The recording-queue thread wins try_lock between worker batches and runs the queued tasks inline (native_worker.cpp:535-538, 108-134).
    - A task that reaches Immediate() there waits for pending_ == 0 while its own tape is still counted (native_recording.cpp:131). That is also a deadlock.
  - It gets through only if the worker is idle with an empty queue (native_worker.cpp:530, :544), or if it wins try_lock and no inline task reaches Immediate() or backpressure.
  - Every other External closure is lock-free:
    - queries.cpp:252/281/289 (Begin/EndQuery, ResolveQueryData)
    - textures.cpp:2869 (CopyResource)
    - texture_readback.h:87 and device.cpp:2615 (CopyTextureRegion)
    - native_recording.cpp:541 (blend factor)
    - buffers.cpp:343-345 (atomic store)
    - texture_upload_publication.h:27-37 and :54-60 (replay a copy, set a version)
    - draw.cpp:3703 and device.cpp:2467 are recorded only inside a th3 preparation scope and play on the recorder.
  - UNCLEAR, because I could not run anything:
    - whether handoffs happen in the F1/F3/W1/W8b scenes. A handoff needs a single-sample RGBA8 surface taking over another surface's identical eDRAM layout (textures.cpp:1655-1662, color_alias_decision.h:55-59);
    - whether th2 baseline runs have hung.
  - Relation to #21:
    - Not created by #21, and no spin is involved.
    - Whether a handoff happens follows the guest's draw order and surface layouts, not host thread scheduling.
    - If the handoff is in the tape that Immediate() flushes, it deadlocks at any priority.
    - For a tape posted earlier (256 KB flush, native_recording.cpp:231), the outcome depends on the race between the worker's re-lock (native_worker.cpp:270) and the recording-queue try_lock (:535).
- **U2 (resolved).** See S1 in section 2.
- **U3.** plume `waitForCommandFence` was read in the live tree (DimensionsRecomp/thirdparty/plume/plume_d3d12.cpp), not in a snapshot. plume is outside snap1.
- **U4 (resolved).** See P1 in section 2.
