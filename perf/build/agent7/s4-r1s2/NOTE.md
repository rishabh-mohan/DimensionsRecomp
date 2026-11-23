# S4 #19 (R1 stage 2, `d3d12_async_submit`): staging only (Agent 7)

Not applied, not built, not run. Base: the S4b SDK, i.e. snap1 (`build/agent2/snap1/DimensionsRecomp/rexglue-sdk`), with
patches applied in the order C1 v3, M1, P2c, r1r2 (#18/#20), #26 (`build/agent2/snap1/PATCHES-S4b.tsv`). So cp.cpp is P2c
+ r1r2 (`027204B5...`), not `build/agent7/s4-r1r2/new/` (`760833A5...`, which has no P2c).

What it follows: b2r §17 (`perf-notes/agent10-batch2-review.md` L781-806) rated stage 1 SAFE under conds 1-6. Cond 6
says stage 2 "is not rated here; it is the risky part", and b2r L1363 has #19 as not rated. The design is from my notes
(`perf-notes/agent7-present.md`, R1, "Stage 2, submit worker"). This file is the design; `RATE-REQUEST.md` asks the
questions.

All line numbers below are **after-file** (`new/sdk/...`) lines unless marked "base".

Corrected 11-23 09:04 (task #33), as in `RATE-REQUEST.md` rev 1 (§6, §9): the presenter paragraph (the guest-output
refresher runs on the GPU Commands thread, with one harmless exception), `RetireOnDemandMemexport`'s wait, S2-2, S2-4.
Corrected 11-23 09:39 (task #33): the presenter paragraph now says where paint runs (the GPU Commands thread in the
default paint mode, not only the UI thread) and gives two harmless exceptions, not one; S2-2 matches.
Corrected 11-23 09:59 (task #33): the 09:04 note above is restored as written at 09:04 (the 09:39 note supersedes it),
and the presenter paragraph says that the UI thread's own switch to `kUIThreadOnRequest` lasts only while it paints
(`ui/presenter.cpp:522`).

## Files

| file | what |
|---|---|
| `s4-r1s2.diff` | the change: cp.h +59, dcl.h +7, cp.cpp +248/-1, shared_memory.cpp +3, texture_cache.cpp +3 (total +320/-1). Paths `a/`, `b/` + SDK-relative |
| `orig/sdk/...` | byte copies of the 6 S4b files read (the 5 above plus dcl.cpp, unchanged) |
| `new/sdk/...` | the 5 staged files |
| `make_s4r1s2.py` | rebuilds `new/` from `orig/` with exact-once edits E1-E16 and writes the diff, `SHA256SUMS.txt` and `PROOFS.txt`. It writes nothing if any anchor is not found exactly once |
| `SHA256SUMS.txt` | full before/after sha256 per file, plus the diff |
| `PROOFS.txt` | P1-P10, all PASS (23:10) |
| `CHECKS.txt` | `git apply --check`: forward on orig 0, `-R` on new 0, forward on new 1 (23:12) |

| file | before (S4b) | after |
|---|---|---|
| `include/rex/graphics/d3d12/command_processor.h` | `67F4E838...` | `EF0DC13D...` |
| `include/rex/graphics/d3d12/deferred_command_list.h` | `9F6CC70A...` | `E7512824...` |
| `src/graphics/d3d12/command_processor.cpp` | `027204B5...` | `05BBCE8B...` |
| `src/graphics/d3d12/shared_memory.cpp` | `2A5ADF13...` (M1) | `9E908D31...` |
| `src/graphics/d3d12/texture_cache.cpp` | `949CCF4F...` (not patched in S4b) | `4183887C...` |
| `s4-r1s2.diff` | - | `06B0D371...` |

## Switch (default off)

| switch | kind | default | effect |
|---|---|---|---|
| `d3d12_async_submit` | cvar, GPU/D3D12, bool, **kInitOnly** | false | true, with `d3d12_submit_split_kb` > 0: the submit of each mid-frame split (Reset, Execute, Close, ExecuteCommandLists, Signal) runs on a new thread, "D3D12 Submit" |

- It is read once, at the end of `SetupContext`, and cached in `submit_async_`. That is true only if the split is on and
  the thread started.
- Off (or split 0): `submit_async_` stays false. No thread, no slots, no log line apart from the one WARN below. Every
  added statement is behind `if (submit_async_)` or the ternary's true arm (P3, P4, P10).
- The cost when off: one bool test at each drain site, and the cp.h layout change (a full SDK rebuild, as with stage 1).
- Set it at launch. Changing it at runtime does nothing until the next start.
- Native builds: leave it off. The native path never calls `EndSubmission`, and it is inert while the split is 0.

## What changed

### `src/graphics/d3d12/command_processor.cpp`

- L114-124: the cvar, `.lifecycle(rex::cvar::Lifecycle::kInitOnly)`, with a comment on the ordering rule.
- L1936-1965, at the end of `SetupContext` just before `return true`, so a failed setup leaves no thread behind:
  - sets `submit_async_ = false` and resets the stats and the log clock;
  - cvar on and split 0: one WARN, stays off;
  - cvar on and split on: makes 3 slots, then `rex::thread::Thread::Create({}, ...)` and `set_name("D3D12 Submit")`.
    These are the same calls the pipeline cache uses (base `pipeline_cache.cpp:163`, `:165`). On success it sets
    `submit_async_ = true` and logs one INFO line. If thread creation fails it logs an ERROR, frees the slots and stays
    off.
- L1972-1974: `ShutdownContext` calls `ShutdownAsyncSubmit()` right after `AwaitAllQueueOperationsCompletion()`, before
  the publish/retire and the release of the command list and allocators.
- L3266-3270: `PublishOnDemandMemexport` drains after its `EndSubmission(false)` and before it takes the global lock,
  so "everything published is submitted" still holds when the batch's last split went to the thread.
- L4022-4026: `CheckSubmissionFence` drains at the top of its `await_submission >= submission_current_` branch, before
  the `EndSubmission(false)` and the queue-operations `Signal` (L4037).
- L4304-4308: `EndSubmission` drains at its top. So every synchronous submit (swap, primary-buffer end, memexport,
  occlusion paths, cache clear) comes after the queued splits.
- L4456: `MaybeSplitSubmission`'s only changed line:
  `} else if (submit_async_ ? EndSubmissionAsync() : EndSubmission(false)) {`. Its false arm is the removed call, and
  the rest of the function is byte-identical (P3, P8). The stage 1 guards and holds are unchanged.
- L4483-4588: `EndSubmissionAsync()`. It is `EndSubmission(false)` for a split (base L4245-4323 with `is_swap` false,
  so `is_closing_frame` is false), with the execute and submit handed to the thread:
  1. If there is no writable allocator, it creates one, as EndSubmission does. On failure it returns false before
     changing anything, so the submission stays open (cond 3) and MaybeSplitSubmission counts `failed`.
  2. It asserts `submission_open_`, `!scratch_buffer_used_` and `!active_occlusion_query_.valid` (MaybeSplitSubmission
     guarantees all three; the last is why EndSubmission's query end, base L4276-4280, is not needed). Then
     `pipeline_cache_->EndSubmission()` and `SubmitBarriers()`, as EndSubmission does.
  3. Under the mutex: if all 3 slots are taken, it waits for the oldest (`full_waits`). It swaps the open submission's
     commands into the next slot's empty list (`DeferredCommandList::Swap`), stores the allocator and the fence value
     `submission_current_`, and counts the slot. Then it notifies the thread.
  4. EndSubmission's bookkeeping: the allocator moves to the submitted list with `last_usage_submission =
     submission_current_`, `++submission_current_`, `submission_open_ = false`, and
     `queue_operations_done_since_submission_signal_ = false`. That last one is still right: a queue operation done
     before this point was issued before the thread's Signal of this submission.
  5. The counter line, at most every 10 s.
- L4590-4605: `DrainAsyncSubmissions()`. It waits until the ring is empty, i.e. until the thread has issued every
  queued ExecuteCommandLists and Signal (not until the GPU has run them). Only the GPU Commands thread queues, so
  nothing can be added while it waits. It counts `drains_waited` and the wait time.
- L4607-4644: `AsyncSubmitThread()`. For the oldest slot, outside the lock: allocator `Reset`, `command_list_->Reset`,
  `Execute`, `Close`, `ExecuteCommandLists`, `Signal(submission_fence_, chunk.submission)`. That is EndSubmission's
  order (base L4297-4316). It ignores HRESULTs as EndSubmission does, and always issues the Signal. Then it resets the
  slot's list and, under the lock, adds the time, advances the ring and notifies. It exits only when asked to stop and
  the ring is empty.
- L4646-4666: `ShutdownAsyncSubmit()`. It sets `submit_async_ = false` and the stop flag, notifies, and joins with
  `rex::thread::Wait(thread, false)` (as base `pipeline_cache.cpp:182` does). Then it frees the slots.

### `include/rex/graphics/d3d12/command_processor.h`

- L18 `#include <condition_variable>`, L43 `#include <rex/thread.h>`.
- L88-96: public inline `FlushAsyncSubmissions()`, which drains when on and does nothing otherwise. It is for code
  outside the class that issues queue operations directly.
- L368-376: the four private declarations.
- L894-931: members at the class end: `submit_async_`, `kAsyncSubmitSlots = 3`, `struct AsyncSubmission`
  (`DeferredCommandList`, allocator, fence value), the slots, the thread, the mutex, the work and idle condition
  variables, the ring head and count, the stop flag, `async_submit_stats_` (all protected by the mutex), and
  `async_submit_last_log_` (GPU Commands thread only).

### `include/rex/graphics/d3d12/deferred_command_list.h`

- L41-46: `void Swap(DeferredCommandList& other)` asserts that both lists belong to the same command processor and
  swaps `command_stream_`, the class's only data member besides the processor reference (base L649). `assert_true`
  comes from `<rex/assert.h>` (dcl.h:19).

### `src/graphics/d3d12/shared_memory.cpp` L490-492, `texture_cache.cpp` L1253-1255

- `command_processor_.FlushAsyncSubmissions()` just before `UpdateTileMappings`. Shared memory: in
  `AllocateSparseHostGpuMemoryRange`, reached from `EnsureHostGpuMemoryAllocated` (base `graphics/shared_memory.cpp:455`,
  in `RequestRanges` before it takes the global lock at :475). Texture cache: in `EnsureScaledResolveMemoryCommitted`,
  once per new scaled-resolve heap, which is used only with resolution scaling.

## Threading model

- One producer, the GPU Commands thread (`EndSubmissionAsync`), and one consumer, "D3D12 Submit". A FIFO ring of 3
  slots. A slot stays counted until the thread has issued its Signal, so the GPU Commands thread runs at most 3 splits
  ahead of the queue.
- Fence values are given out on the GPU Commands thread when a split is queued, in order. The thread signals them in
  the same order.
- The thread blocks only on its own mutex and work condition variable. It never waits for the GPU Commands thread, the
  GPU, a fence or any other lock, and ExecuteCommandLists and Signal only enqueue. So every wait on the GPU Commands
  side (full ring, drain) ends after a bounded amount of CPU work on the thread: no deadlock.
- The mutex gives the hand-offs their ordering: slot contents (GPU Commands to the thread), and the slot reset, stats and
  the R2 counters inside `Execute` (the thread back to GPU Commands).

### Every queue operation of the GPU Commands thread (P5)

| after-file site | function | operation | ordered after the queued splits by |
|---|---|---|---|
| cp.cpp:4037 | CheckSubmissionFence (`>=` branch) | queue-operations fence Signal | the drain at L4024-4026, same branch |
| cp.cpp:4364, :4378 | EndSubmission | ExecuteCommandLists, Signal | the drain at L4306-4308 |
| cp.cpp:4631, :4632 | AsyncSubmitThread | ExecuteCommandLists, Signal | FIFO on the thread itself |
| shared_memory.cpp:493 | AllocateSparseHostGpuMemoryRange | UpdateTileMappings | `FlushAsyncSubmissions()` at L492 |
| texture_cache.cpp:1264 | EnsureScaledResolveMemoryCommitted | UpdateTileMappings | `FlushAsyncSubmissions()` at L1255 |

So the queue sees the GPU Commands thread's operations in program order, and `submission_fence_` values are monotonic.
The tile-mapping flushes are needed: tile heaps are created with `GetHeapFlagCreateNotZeroed()`, so mapping a range
ahead of an older pending split is not provably harmless.

`EndSubmission` callers, all drained by its top: `IssueSwap` L2624/L2630 (true), `OnPrimaryBufferEnd` L2636,
`PublishOnDemandMemexport` L3264, `CheckSubmissionFence` L4028, the sync arm of L4456, and the occlusion paths L6055 and
L6111.

Other users of the direct queue are the presenter's. Paint (`d3d12_presenter.cpp:1173`) runs where the paint mode says
(`ui/presenter.cpp:1316-1339`). In the default mode, `kGuestOutputThreadImmediately`
(`host_present_from_non_ui_thread` true, no implicit vsync in D3D12, no UI drawer), it runs on the GPU Commands thread
inside `RefreshGuestOutput`, right after a successful refresh (`ui/presenter.cpp:638-641`), so after L2624's drain
(below). In `kUIThreadOnRequest`, which the UI thread also switches to while it paints itself
(`ui/presenter.cpp:473-475`, back to the desired mode at `ui/presenter.cpp:522`), paint runs on the UI thread and is
ordered against the GPU Commands thread only by fences, as today. The guest-output refresher's `NextSubmission` (:567)
runs on the GPU Commands thread: the presenter calls `IssueSwap`'s refresher lambda (L2364-2626) synchronously at :560
and signals after it returns. The guest-output refresh ends with `EndSubmission(true)` (L2624), which drains, so the
refresher's signal still comes after the frame's splits. Splits queued after that belong to the next frame and never
write the guest output resource. Two harmless exceptions. First, either early return of the refresher (L2470, or the
FXAA-descriptor fallback at L2564) skips L2624, and the presenter still signals (:565-567), so splits still queued
reach the queue after that signal (they drain at L2630); a failed refresh paints nothing (`ui/presenter.cpp:572-577`).
Splits never reference the guest output resource, and the fallback's copy and its barriers (L2555-2563), the only
commands that do, also reach the queue at L2630, after the signal, with #19 off as well. Second, when the guest output
turns inactive, `RefreshGuestOutput` paints one blank frame without calling the refresher
(`ui/presenter.cpp:580-587`), so in the default mode that paint can reach the queue before splits still queued. The
blank frame uses no guest output resource (`d3d12_presenter.cpp:623-624`), and splits never touch the swap chain.

### Waits that do not drain, and why they still end

- `CheckSubmissionFence(N)` with N < `submission_current_`: the frame pacing in `BeginSubmission` (L4206), the occlusion
  query wait (L6116, after a synchronous `EndSubmission(false)`) and `CheckSubmissionFence(0)` (L3731). They wait on
  `submission_fence_`. A queued split's value is signalled by the
  thread right after its ExecuteCommandLists, and the thread never waits on anyone, so the wait ends when the thread
  and then the GPU get there. Draining here would put a full drain into every `BeginSubmission` after a split, which is
  the cost stage 2 is meant to remove.
- `RetireOnDemandMemexport` (L3307) is a different wait. It waits on `submission_fence_` directly
  (`SetEventOnCompletion` and `WaitForSingleObject`, L3322-3326), under the global lock (L3308), on the thread that
  reads a memexport page (`ProvideOnDemandMemexportThunk`, L3430-3436), and only for published batches (L3310,
  L3317-3321). `PublishOnDemandMemexport` drains before it publishes (L3266-3270), so no queued split is involved.
- Device removal: `GetCompletedValue` returns UINT64_MAX and fence events fire, so waits end, and the thread's calls
  fail fast. There is no special code, as in the sync path.

## Lifetimes

- **Allocators.** A split takes `command_allocator_writable_first_`. The writable list holds only allocators the GPU is
  done with (reclaimed at fence >= their last use) or new ones. The split's allocator moves to the submitted list at once
  with the split's fence value, so it is reclaimed only after the GPU has run the thread's submit. Two queued splits
  always have different allocators. Cache clears (`ClearCommandAllocatorCache`, base L4336) run inside EndSubmission
  after the drain and `AwaitAllQueueOperationsCompletion`.
- **`command_list_` and `command_list_1_`.** On the GPU Commands thread only `EndSubmission` (after its drain),
  `SetupContext` (before the thread starts) and `ShutdownContext` (after it stops) touch them, so the thread has them to
  itself while splits are queued. Resetting a list right after ExecuteCommandLists is allowed. The sync path does that
  every submission.
- **Deferred lists.** The open submission's stream goes into a slot. Recording goes on in the slot's old, empty stream
  (with the 1 MiB reserve) after `BeginSubmission`'s `Reset`. The thread resets the slot's list after its submit.
- **Everything a split references** (upload, readback and descriptor pools, texture, render-target and shared-memory
  state) is tagged at record time with the split's submission number, and is retired by `submission_completed_` from
  the fence. So nothing is freed before the thread's Signal has completed on the GPU.
- **Pipelines.** `Execute` resolves handles through `GetD3D12PipelineByHandle` (`pipeline_cache.h:101-102`, an atomic
  acquire load). Splits happen only when `CanEndSubmissionImmediately()` holds, i.e. no pipeline is still being created,
  so every pipeline in a split exists. Pipelines live until shutdown.

## Shutdown and failure paths

- **Shutdown.** `AwaitAllQueueOperationsCompletion()` drains, through `CheckSubmissionFence(submission_current_)`, and
  waits for the GPU. Then `ShutdownAsyncSubmit()` joins the thread, which finds the ring empty. After that the existing
  publish/retire and releases run with `submit_async_` false, i.e. synchronously.
- **Thread creation fails:** ERROR line, slots freed, sync path.
- **Allocator creation fails in a split:** returns false before touching the ring; the submission stays open.
- **Stop with splits still queued** (not reachable through ShutdownContext, which drains first): the thread submits
  them all before it exits.

## Conditions

Stage 1's six conditions (b2r §17) still hold: MaybeSplitSubmission's guards and holds are unchanged (P8). Proposed for
stage 2:

| cond | how it is met | where |
|---|---|---|
| S2-1: the thread takes only splits; every other submit stays synchronous after a drain | the ternary is the only call site of `EndSubmissionAsync`; `EndSubmission` drains first | L4456; L4304-4308 (P10) |
| S2-2: every queue operation of the GPU Commands thread comes after the queued splits | the drain table above; two harmless exceptions outside P5's files: the presenter's refresher signal after either early return of the refresher (L2470, L2564), and the blank default-mode paint when the guest output turns inactive (the presenter paragraph above) | P5 |
| S2-3: fence values given out in order, on the GPU Commands thread; signalled in FIFO order | the value is stored when the split is queued; the thread takes the oldest slot | L4537, L4622, L4632 |
| S2-4: the thread touches only its own state, the native lists, the fence, the direct queue (L4613) and, through `Execute`, the pipeline handles (Lifetimes, "Pipelines"), and never waits on anything but its mutex | worker body; `Execute`'s pipeline lookups (dcl.cpp:400, :622 → cp.h:200-201 → `pipeline_cache.h:101-102`) | P6 (names in the worker body only); L4607-4644 |
| S2-5: off = stage 1, byte for byte at run time | kInitOnly cvar cached in `submit_async_`; every added statement behind it | P3, P4, P10 |
| S2-6: native builds off | default false; nothing sets it; inert while the split is 0 | - |
| S2-7: the thread is joined at shutdown, after all queue operations have completed | ShutdownContext order | L1971-1974 |

## Log lines

| line | when |
|---|---|
| `d3d12_async_submit: submitting splits on the submit thread (3 slots)` (INFO) | once at init, when the cvar and the split are both on |
| `d3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off` (WARN) | once at init, cvar on and split 0 |
| `d3d12_async_submit: failed to create the submit thread, staying off` (ERROR) | init, thread creation failed |
| `d3d12_async_submit: frame= submission= chunks= queued_max= full_waits= full_wait_us= drains_waited= drain_wait_us= worker_us=` (INFO) | at a split, at most every 10 s (the first split logs at once). Totals since start |
| stage 1's `d3d12_submit_split: ...` | unchanged; `splits` counts async splits too |

How to read the counter line: Δchunks/Δframe is async splits per frame. worker_us/chunks is the submit cost moved off the
GPU Commands thread. drain_wait_us and full_wait_us are what the GPU Commands thread still waits. queued_max is at
most 3.

## Syntax check

None tonight (staging rules: no compiles). When allowed: the `bench/agent7/s4r1r2_syntax.ps1` method (clang
`-fsyntax-only` with the dev SDK flags, control vs candidate, one compile at a time at BelowNormal) on cp.cpp,
shared_memory.cpp, texture_cache.cpp and the other TUs that include cp.h or dcl.h (graphics_system, pipeline_cache,
primitive_processor, render_target_cache, deferred_command_list). The new code uses only APIs already used in the SDK:
`rex::thread::Thread::Create({}, ...)`, `set_name` and `rex::thread::Wait(..., false)` (base `pipeline_cache.cpp:163`,
`:165`, `:182`); `REXGPU_WARN`/`REXGPU_INFO`/`REXGPU_ERROR`; `assert_true` (dcl.h includes `<rex/assert.h>`); `std::max`
(cp.cpp includes `<algorithm>`); `<condition_variable>` and `<rex/thread.h>` are now included explicitly in cp.h.

## Risks and open questions

1. **The drains may eat the gain.** `OnPrimaryBufferEnd` (L2633-2636, `d3d12_submit_on_primary_buffer_end`, default
   true) submits synchronously at each primary-buffer end, which drains. In this title a frame arrives as one primary
   buffer (b2r §17), so that is about one drain per frame, just before the swap. `drain_wait_us` measures it. A later
   "stage 2b" could make that submit async too. Not staged.
2. **Frame stats.** Drain and full-ring waits are not in frame_stats (`kFenceWait` is untouched). They show only in the
   counter line. W7's read-out (fps, median ms) is not affected.
3. **3 slots** let the GPU Commands thread run up to 3 splits ahead. `full_waits` shows if that is too few. Memory: 3 x
   1 MiB reserved for the slot lists (the default `DeferredCommandList` reserve).
4. **Thread priority** is the default. The thread competes with GPU Commands for P-cores (W5's slow runs were P-thread
   saturation), so check `sys.csv` for the slow state in each row.
5. **Locks held during a flush.** The shared-memory flush runs before `RequestRanges` takes the global lock (base
   :455 vs :475). The reviewer should confirm that no caller of `EnsureHostGpuMemoryAllocated` holds it. If one did,
   it would cost only time, not correctness, since the thread never takes the global lock.
6. **Difference from my design note.** The note had every `CheckSubmissionFence` wait drain. The staged code drains
   only the `>=` branch, which issues a queue operation. Plain fence waits end without a drain (see above).

## Test plan

Agent 2 builds, after the user OKs it: devoff4b + this diff, a full SDK rebuild. Functional rows first, then the soak,
then timing. See `FUNCTIONAL-ROWS.md`, `SOAK.md` and `matrix-w7-draft.json` (to be written Monday morning).
