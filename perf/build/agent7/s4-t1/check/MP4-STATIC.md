# MP4-STATIC: b2r S15.4 must-prove 4 (static check)

Claim under test: "CaptureShaderBindings callers (draw.cpp:4949, :5111, :5190, :5217) run only on the
single capture worker, never on PREPARE_THREADS workers."

Authority: the S4b snapshot `build/agent2/snap1/DimensionsRecomp/rexlego/` (every file opened by explicit path).
I found candidates by searching `DimensionsRecomp/rexlego/src` recursively, then confirmed each hit in the snapshot.
Checker: Agent 7's read-only checker, 2026-11-22 ~22:40 local. Nothing was built or run.

## Verdict

- **PROVEN (static), "never on PREPARE_THREADS workers": holds in n0, th2 and th3.** None of the jobs posted to
  the NativePreparationQueue ("Native GPU prepare N") can reach CaptureShaderBindings, directly or indirectly.
- **"only on the single capture worker" is REFUTED as worded. It needs restating.**
  (a) In th2, a capture task can run *inline on whichever thread drains the queue*. That thread is typically a guest
  thread in `HostDevice::LockRecording -> NativeWorkerDrain -> RunQueuedInline`. Execution stays serialized under the
  recording gate and in FIFO order.
  (b) In th3 with FSR3 enabled, CoordinatorMain forwards every task, captures included, to **RecorderMain**, so
  :5190/:5217 run on "Native GPU recording", not on the coordinator.
  (c) In n0, none of the four call sites ever runs (the claim holds vacuously).
- Suggested wording that the source does support: *"The four CaptureShaderBindings call sites run only inside g_queue
  capture tasks. One task runs at a time under the recording gate: WorkerMain or an inline drainer in th2;
  CoordinatorMain in th3, or RecorderMain when FSR3 is on. They never run on a NativePreparationQueue thread. In n0
  they do not run at all."*
- Residual gaps (UNCLEAR, low risk): see the last section. Gap 2 now records F-CA (Nov 23 update).

## Definitions and call sites (snapshot line numbers match the claim)

- `CaptureShaderBindings()` at shaders.cpp:815. It calls PollPrecompiledShaders and RefreshBoundShaderResources;
  the latter takes `HostDevice::LockRecording` at shaders.cpp:794 unless `t_shader_bindings` is set.
- `CaptureShaderBindings(vertex, pixel)` at shaders.cpp:822. It takes LockRecording at :831, but only when a program
  changed. The declarations are at shaders.h:35-36.
- The only call sites in src are draw.cpp **4949, 5111, 5190, 5217**. Repo-wide grep found no other caller, and the
  snapshot was confirmed by path.

## Per-caller table

| Caller | Enclosing function | How it is reached | n0 | th2 (THREADED=1, PREPARE_THREADS=2, SNAPSHOT_STATE=1) | th3 (THREADED=1, PREPARE_THREADS=2, FULL_DRAW_PREPARATION=1) | Evidence |
|---|---|---|---|---|---|---|
| draw.cpp:4949 | `CaptureFullDraw` (draw.cpp:4838) | Only from the capture lambdas at :5183 / :5212, when `NativeFullDrawPreparationEnabled() && !NativeFsr3Enabled()` (:5182, :5211) | never (lambda never built) | never (full-draw preparation off) | **CoordinatorMain** (`if (task.capture) task.run();` native_worker.cpp:238) | draw.cpp:5181-5185, 5209-5214; native_worker.cpp:198-257, 260; per-thread memo `static thread_local captured_pairs` draw.cpp:4929 |
| draw.cpp:5111 | `CaptureParallelDraw` (draw.cpp:5102) | Only from the lambdas at :5197 (guarded by `NativeParallelDrawsEnabled()` :5195) and :5222. Returns early at :5104 when parallel draws are off, a TemporalInputsCandidate is present, LongProbe is on, or pass_profile is capturing | never | **WorkerMain** (native_worker.cpp:259-297, gate held :270..:290), or **an inline drainer** (`RunQueuedInline` native_worker.cpp:108-134 via NativeWorkerDrain non-full path :528-546), only with FSR3 off | never (FULL_DRAW_PREPARATION routes to :5183/:5212; with FSR3 on the FSR3 branch returns at :5193/:5220 first) | draw.cpp:5186-5200, 5215-5225 |
| draw.cpp:5190 | lambda inside `DrawVerticesHookQueued` (draw.cpp:5176), submitted at :5181 | FSR3 branch :5187-5193 | never | WorkerMain or inline drainer, only if `NativeFsr3Enabled()` | **RecorderMain** (CoordinatorMain forwards all tasks to NativeRecorderSubmit when FSR3 is on, native_worker.cpp:221-234; RecorderMain :152, created :346), only if FSR3 is on | draw.cpp:5181-5194 |
| draw.cpp:5217 | lambda inside `DrawIndexedVerticesHookQueued` (draw.cpp:5205), submitted at :5209 | FSR3 branch :5216-5221 | never | same as :5190 | same as :5190 | draw.cpp:5209-5221 |

How the chain enters, all modes:

- The guest calls the REX_HOOK entries at draw.cpp:5747/5748, which lead to `Draw*HookQueued`.
- If `!device || !NativeWorkerShouldQueue()`, the hooks call `DrawVerticesHook` / `DrawIndexedVerticesHook` directly
  (draw.cpp:5179-5180, 5207-5208). Neither of those calls a capture function.
- Otherwise the lambda goes to `NativeWorkerSubmitCapture` (decl native_worker.h:152; the only callers are
  draw.cpp:5181/5209), which pushes it onto g_queue.
- The `LEGO_NATIVE_WORKER_STUB` inline `task()` at native_worker.h:81 exists only in offline fixtures.

How each mode behaves:

- **n0**: `NativeWorkerEnabled()` is false (native_worker.cpp:319-327), so `NativeWorkerShouldQueue()` is false
  (:310-312). The four call sites are unreachable. `StartNativeWorker` returns at :339, so no worker, coordinator or
  recorder exists.
- **th2**: g_queue has two consumers.
  1. WorkerMain holds the recording gate across tasks (:270) and runs FlushNativeDrawBatch at :289 before unlocking
     at :290.
  2. `RunQueuedInline` runs on any thread that calls NativeWorkerDrain in the non-full path and wins
     `recording.try_lock()` (:528-546). It sets `t_running_task = true` and flushes at :128 while still under the
     gate.

  There is no RecorderMain in th2.
- **th3**: WorkerMain hands off to CoordinatorMain (:260). In th3 NativeWorkerDrain always takes the full path
  (:510-527): it pushes a marker and waits, and never runs tasks inline, so RunQueuedInline is unreachable.
  Captures therefore run on CoordinatorMain (FSR3 off) or on RecorderMain (FSR3 on).

## Every job posted to the preparation pool

`PreparationQueueInstance()` is used only in native_recording.cpp:509-518. The pool singleton is created at :510
(`NativePreparationQueue`, ctor native_preparation.h:45-48; its threads run `Run` at :24, named "Native GPU prepare
N"). The full list of posters in src:

| # | Poster (file:line) | Job body | Modes | Can it reach CaptureShaderBindings? |
|---|---|---|---|---|
| 1 | native_recording.cpp:158 `RecordingQueue::Post` | `owned->Prepare()`, which is `CommandTape::Prepare` (native_recording.cpp:77-85). It runs only commands with `preparation=true`, which are Upload memcpys (:327-333) | th2 only (PrepareNativeCommandList :529-532 returns early in n0/th3) | **No**: memcpy only, no device or shader calls |
| 2 | draw.cpp:5093 `QueueNativeDrawBatch` (`PostNativePreparation`) | `PrepareDrawWork` (draw.cpp:1660) per work item. The flushing thread joins it in FlushNativeDrawBatch (draw.cpp:5687-5711, `job.get()` :5695); `DispatchDraw` then runs on the *flushing* thread (:5704), not in the job | th2 (called from CaptureParallelDraw :5147 / flush) | **No**: PrepareDrawWork calls none of CaptureFullDraw / CaptureParallelDraw / NativeWorkerSubmitCapture / CaptureShaderBindings, all of which have no other call sites |
| 3 | draw.cpp:4594 `PrepareFullDrawBatch` (`PostNativePreparationDetached(task->TryRun)`) | `PrepareFullDrawChunk` (draw.cpp:4462-4506): PrepareDrawWork, `DispatchDraw` :4486 under `DrawPreparationScope` :4475, and `PrepareFollowers` :4429, which calls `PrepareFollowerFull` :4385 (PrepareDrawWork / DispatchDraw :4410, BindMergedConstants) | th3 | **No**: same symbol argument as #2 |

The only indirect route from a pool thread back into capture code is the LockRecording drain:

- `HostDevice::LockRecording` (device.cpp:774-777) calls `NativeWorkerDrain(_ReturnAddress())` only when
  `!t_draw_preparation && !NativeRecordingGate::InPreparation()`. `t_draw_preparation` is a thread_local
  (device.cpp:755) set by `DrawPreparationScope` (device.cpp:762-768).
- Through NativeWorkerDrain, `RunQueuedInline` could in principle run a capture task. That route is closed in every
  mode:
  - **th3**: NativeWorkerDrain never runs tasks inline (full path), and job #3 runs DispatchDraw under
    DrawPreparationScope, so the drain is skipped anyway.
  - **th2 job #2**: the job runs entirely while the submitting capture thread holds both halves of the gate. It is
    posted under the gate and joined at :5695 before WorkerMain unlocks (:289-290) or RunQueuedInline returns (:128).
    A pool thread's `try_lock` on the per-thread recursive gate (native_worker.h:38-49) would fail, so it cannot
    become the inline drainer.
  - **th2 job #1** does no LockRecording at all.
- A pool thread cannot submit a capture either. `NativeWorkerSubmitCapture` is reachable only from the guest REX_HOOK
  entries.

Reverse direction (not a violation): pool *jobs* sometimes run on non-pool threads. `RunPreparationChunkHere`
(draw.cpp:4356-4364) runs chunks on the coordinator, and Post/PostDetached run the job inline on the poster when the
queue is full or stopping (native_preparation.h:63, :79).

## Guards present (none of them asserts "not on a prepare thread")

- `t_running_task` (native_worker.cpp:65, set in RunQueuedInline)
- `t_on_recorder` (:66, set :153; `OnNativeRecorderThread()` :336)
- `OnNativeWorkerThread()` (:333-335, compares against g_worker_thread_id)
- `t_inline_scope` (:68)
- `t_on_coordinator` (draw.cpp:4266, set :5677-5679)
- `t_draw_preparation` / `DrawPreparationScope` (device.cpp:755, 762-768)
- `NativeRecordingGate::InPreparation()` (device.cpp:774-777)
- `NativeWorkerShouldQueue()`: a pool thread entering a hook would queue rather than run inline

**There is no assert, counter or thread_local that marks NativePreparationQueue threads.** The property rests on the
call graph alone.

## RecorderMain / RecordingQueue

- **RecorderMain** (th3 only): yes, it runs captures when FSR3 is on (:5190/:5217 via the forward at
  native_worker.cpp:221-234). With FSR3 off it runs no captures.
- **RecordingQueue::Run** (th2 only; native_recording.cpp:111, thread created :138): it only plays tapes. It could
  reach a capture only if a tape External closure called LockRecording and won the inline drain. No such closure was
  found, but closures were not audited exhaustively (see gaps). RecordingQueue is not a PREPARE_THREADS worker, so this
  does not affect the PROVEN part.

## Gaps (UNCLEAR)

1. The call graph comes from grep, not a compiler call graph. Indirect calls are covered only by the facts that
   capture lambdas flow solely through NativeWorkerSubmitCapture into g_queue, and pool jobs are only the three
   posters above.
2. Tape `External` closures executed by RecordingQueue::Run (th2) were not audited one by one for LockRecording.
   This is low risk and outside the PREPARE_THREADS question. **Update (Nov 23): F-CA, see the last section.**
3. Whether `NativeFsr3Enabled()` / `NativeParallelDrawsEnabled()` are on in the actual th2/th3 test configs decides
   *which* of :5111 / :5190 / :5217 / :4949 runs, and on which consumer (coordinator vs recorder). It does not change
   the pool verdict.

## What a functional row could add

- Add `thread_local bool t_on_prepare` set at the top of `NativePreparationQueue::Run` (the line where S4-T1 calls
  `ApplyNativeChainPriority("prepare")`).
- In both `CaptureShaderBindings` overloads (shaders.cpp:815/822), increment atomic counters by thread class:
  `on_prepare` (t_on_prepare), `on_worker` (OnNativeWorkerThread), `on_coordinator` (t_on_coordinator),
  `on_recorder` (OnNativeRecorderThread), `inline_other` (t_running_task on any other thread), and `other`.
- Log the counters once at shutdown or every N frames with REXLOG_INFO. Optionally log the first capture per thread id
  with `GetThreadDescription` (the tids can be matched against the S4-T1 role log lines).
- Acceptance: `on_prepare == 0` in th2 and th3. In th2, also report the `inline_other` share. In th3 with FSR3 on,
  expect `on_recorder > 0` and `on_coordinator == 0` for :5190/:5217.
- A functional row only shows absence on the paths that were exercised. The static proof above covers all paths.

## Update, Nov 23: gap 2 and F-CA

Source: Agent 10's rating `build/agent10/t27/r21-s4t1.md` (c) 4 and (b) 5, and its helper's code read
`build/agent10/t27/sub-r21-coderead.md` §6 (snap1 line numbers). Lines above this section are unchanged, apart from a
pointer on L25 and L133.

- **Pool side: closed for the allowed envs (U1a).** It rests on a name-level call graph, so it is strong evidence, not
  proof. It holds only while LEGO_NATIVE_RETAINED_DRAW_STATE, LEGO_NATIVE_VIEWPORT, LEGO_NATIVE_NO_DRAW_ARENA and
  LEGO_NATIVE_SHADER_PACK stay at their defaults (none is in `build/agent8/w8w9/ENV-KEYS-F1.txt`).
- **Tape side: not lock-free. F-CA is a known th2 issue that predates #21.**
  - A color-alias handoff's Complete() (color_alias_publication.h:31-33, :51, :81-83) runs in a tape ResourceCommand
    on the recording-queue thread (native_recording.cpp:124). It calls HostDevice::RetireResource (the retire lambda,
    textures.cpp:1699-1705), which takes LockRecording (device.cpp:1416) unless FULL_DRAW_PREPARATION queues the
    retire (device.cpp:1412). th3 sets FULL_DRAW_PREPARATION; th2 does not.
  - Case 1: the worker holds the gate (native_worker.cpp:270) and waits in Immediate() → RecordingQueue::Wait
    (native_recording.cpp:302-305, 166-170). The queue thread polls every 200 µs (native_worker.cpp:534-546) and never
    reaches `--pending_` (native_recording.cpp:131). This deadlocks at any thread priority.
  - Case 2: the queue thread wins try_lock (native_worker.cpp:535) and runs queued tasks inline. A task that reaches
    Immediate() there waits while its own tape is still counted. Also a deadlock.
  - #21 does not create it and adds no spin. It can only change which way the race goes for a tape posted earlier.
    Every other External closure is lock-free (sub-r21-coderead.md §6).
  - Not seen at runtime. Whether handoffs happen in the F1/F3/W1/W8b scenes is unknown. A handoff needs a
    single-sample RGBA8 surface taking over another surface's identical eDRAM layout (textures.cpp:1655-1662), and
    game.log has no line for it at info level.
  - Rule for #21 rows (condition 5): any th2 hang, timeout or dump is read for this signature and compared with the
    th2 arm on the same route before it is charged to either side. Re-run th2 if it did not reach the same point. The
    row does not pass meanwhile.
- **Earlier th2 runs: none hung.** I searched every `build/agent8/matrix/*/matrix.json` for n2/th2 arms. All 4
  th2-env runs (LEGO_NATIVE_THREADED=1, PREPARE_THREADS=2, SNAPSHOT_STATE=1) reached the title's normal exit ("Title
  terminated; hard-exiting process."). Each had status OK and exit 0, closed by WM_CLOSE in 1-5 s, with no frame over
  100 ms in the scored window.

  | run (under build/agent8/matrix/) | bin | on top of th2 | game.log span | frames in window | max ms |
  |---|---|---|---|---|---|
  | s3-n2-0210/runs/0210-n2-r1 | native2 | - | 02:10:50-02:12:33 (1:43) | 8125 | 52.8 |
  | 20261122-0452/runs/0454-n2-r1 | native3d | - | 04:54:30-04:56:42 (2:12) | 6578 | 70.8 |
  | 20261122-0652/runs/0652-n2t-r1 | native3d | LEGO_NATIVE_TIMING=1 | 06:52:37-06:54:50 (2:13) | 8204 | 60.9 |
  | 20261122-0657/runs/0657-n2s-r1 | native3d | LEGO_NATIVE_PARALLEL_DRAWS=0 | 06:57:42-06:59:54 (2:13) | 7415 | 65.6 |

  - That is about 8.4 min of th2 on one route, all on Nov 22, on the hidden desktop, before native4b. It is weak
    evidence: no handoff deadlock on this route in these runs, not proof that handoffs never happen.
  - s3-n123-0205's n2 never started (RAM gate), so it is not counted.
  - Sources: each folder's results.csv and game.log; perf-notes/SESSION2.md L1976 (0652 and 0657: no errors,
    STUCK-LOCK or dumps); perf-notes/agent4-draw-path.md L157 and L256.
