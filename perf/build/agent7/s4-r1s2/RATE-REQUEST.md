# Rate request: S4 #19 (R1 stage 2) `d3d12_async_submit` (Agent 7, task #32, Nov 23 08:12; rev 1 08:40)

For **Agent 10, after the break. No rating is requested now.** cc Agents 1, 2, 3 and 8.
**Staged only:** nothing has been built, compiled or run, and there is no syntax check yet (§10).
Base: the S4b SDK = snap1, `build/agent2/snap1/DimensionsRecomp/rexglue-sdk`, with C1 v3, M1, P2c, r1r2 (#18/#20)
and #26 applied in that order (`build/agent2/snap1/PATCHES-S4b.tsv`).
The change: [s4-r1s2.diff](s4-r1s2.diff), sha256 `06B0D371686CD384193DF30E8509BC4DA586E8EDD0F45F4122D5911483E33AD7`
([SHA256SUMS.txt](SHA256SUMS.txt) L12), +320/-1 over 5 files. This request does not change it or any other staged file.
Line numbers are after-file (`new/sdk/...`) numbers unless marked "base". [NOTE.md](NOTE.md) is the design; this file
asks the questions and maps the evidence to them.

**Rev 1 (08:40):** an independent read found 3 errors, 2 gaps and 8 nits, now fixed in §5, §6 (the presenter,
RetireOnDemandMemexport, the `>=` branch's callers), §9 (S2-2, S2-4, P4, P6, P8, CHECKS), §10.8, §11.1, §12.3, §13
(rows e and f), §14 and §15.

**Corrected 11-23 09:39 (task #33):** the task #33 read found that paint (d3d12_presenter.cpp:1173) runs on GPU
Commands in the default paint mode, not only on the UI thread, and that the refresher has a second early return
(L2470); fixing them turned up a second harmless exception, a blank paint when the guest output turns inactive. Fixed
in §6 (threads, queue order, scope, "Presenter"), §9 (S2-2, P5) and §11.1; §13 row e also cites L6055. Task #33's
other edits (09:04, 09:59) are listed in §15.

**Asks (for after the break)**
- **(a)** Is it SAFE to build into devoff4b as a default-off test bed? With the cvar at its default (false) it should
  run exactly as S4b.
- **(b)** Is it SAFE to test it ON (`d3d12_submit_split_kb=<N>` plus `d3d12_async_submit=true`) in the rows and the soak
  (§13) and in W7 (§14)?
- **(c)** Do you accept the threading and ownership rules (§6) and the code-read items (§11)?

Suggested reading order: §6, §11, then cp.cpp:4456 and :4483-4666. Index of all files: [README.md](README.md).

## 1. Candidate

- #18 (R1 stage 1, `d3d12_submit_split_kb`, part of S4b) ends the open submission mid-frame once the deferred list
  passes N KB. Each split is submitted on the GPU Commands thread: allocator Reset, list Reset,
  `DeferredCommandList::Execute` (the replay into the native list), Close, ExecuteCommandLists and Signal.
- #19 hands that submit work, for splits only, to a new thread, "D3D12 Submit". The GPU Commands thread queues the
  split and goes on recording the rest of the frame. Fence values are still given out on the GPU Commands thread, in
  order. Every other submit stays on the GPU Commands thread, after a drain.
- Why: b2r §17 rated stage 1 SAFE under conds 1-6. Cond 6 (L799) expects no win from stage 1 alone, since each split
  adds a Close plus ExecuteCommandLists ("0.54 ms/f for one per frame"). Its value is to validate the split rules for
  stage 2, which "is not rated here; it is the risky part". b2r L1363 lists #19 as not rated. b2r's line numbers
  shift (L1361), so cite §17 by condition.
- Expected effect: the GPU Commands thread's CPU ms/f drops by about the "D3D12 Submit" thread's ms/f, less what the
  drains give back (risk 1). fps rises only if GPU Commands is the limiter.
- `perf-notes/S4-DRAFT.md`: row 19 (L236) asks for "functional + a 10-min soak, then a timing A/B"; W7 is L416.
- Owners: Agent 7 stages it, Agent 10 rates it, Agent 2 builds it (after the user OKs it), Agent 3 runs the rows and
  the soak, Agent 8 owns W7, and Agent 1 commits.

## 2. Files and apply

| file (SDK-relative) | before sha256, S4b (bytes / lines) | after sha256 (bytes / lines) | +/- |
|---|---|---|---|
| `include/rex/graphics/d3d12/command_processor.h` | `67F4E8380C879377F06B6E3DD879EE737A82BBBE9682F123247ED5D0671FF325` (41218 / 875) | `EF0DC13DA29703C7FEDC13FE7C8542E592FB82460817F1B88C4930D92F12CD4C` (43860 / 934) | +59 / -0 |
| `include/rex/graphics/d3d12/deferred_command_list.h` | `9F6CC70A6922232D4FF7A32303E8B785A01D1C7A3CF54373369EF6B23F8AF0F0` (26607 / 652) | `E7512824D8E6F9673C59457CD28FA34DD7795E4D495B3BAB76D07774AEA60650` (26921 / 659) | +7 / -0 |
| `src/graphics/d3d12/command_processor.cpp` | `027204B53A271D69275FCC6FEC6B2222905155E1FD67808F88A79329F4022C0E` (273790 / 5933) | `05BBCE8B7E3FB27D43F364031082F73DFCD5BD223307DB794FB3C6DD6E91807C` (284643 / 6180) | +248 / -1 |
| `src/graphics/d3d12/shared_memory.cpp` | `2A5ADF13B5E433F1F10B5C6AF9C14F8812527C4E155A5146B166723457B6EBB4` (24190 / 555) | `9E908D31E6F64A31A55126CB0E97B37F1DD1A677B7026872A839FAE53A8FEB8A` (24373 / 558) | +3 / -0 |
| `src/graphics/d3d12/texture_cache.cpp` | `949CCF4F4D80975D4DF3E833604BDBEC8C1442D787E2492085F0FA966E7F8C99` (114404 / 2251) | `4183887C9D625B97D8DDB7B5D2BF5F28D2B9B122DBF3488BDA1753100CB9BAB4` (114595 / 2254) | +3 / -0 |
| [s4-r1s2.diff](s4-r1s2.diff) | | `06B0D371686CD384193DF30E8509BC4DA586E8EDD0F45F4122D5911483E33AD7` (20060 B) | +320 / -1 |

- All of these are in SHA256SUMS.txt; I re-checked its 12 entries with Get-FileHash today at 07:51 (0 mismatches).
  The files are LF only with a final newline (P9).
- Every change is an insertion except one line: MaybeSplitSubmission's `} else if (EndSubmission(false)) {` (P3, §5).
- `src/graphics/d3d12/deferred_command_list.cpp` (`30FF57446EFB5D7643EC71024CE1D04884C210831053DEE39EAAB611FD346872`)
  is copied to orig/ for reference and is unchanged. Its `Execute` now also runs on the new thread (§11.6).
- P1: each orig/ file equals the snap1 bytes and the S4b after-hash in PATCHES-S4b.tsv; texture_cache.cpp is not
  patched in S4b. So cp.cpp is P2c + r1r2, not `build/agent7/s4-r1r2/new/` (`760833A5...`, which has no P2c).

Apply (Agent 2, after the rating and the user's OK):
1. Check the 5 before hashes in the tree devoff4b is rebuilt from.
2. **Primary:** copy `new/sdk/*` (the 5 files) over the SDK root.
   **Alternative:** `git apply` with a repo-relative `--directory`, run from the workspace root:
   `cmd /c "git apply --check --verbose --directory=games/lego-dimensions-recomp/build/agent2/snap1/DimensionsRecomp/rexglue-sdk build/agent7/s4-r1s2/s4-r1s2.diff"`,
   then the same without `--check`.
   - **Pitfall (found today, 07:58):** the SDK root has no `.git`, and `DimensionsRecomp/.git` is not used either; git
     uses the parent repo two levels above the workspace. So [CHECKS.txt](CHECKS.txt) L22-23's form
     `git -C <sdk root> apply --check --verbose <diff>` prints "Skipped patch" for all 5 files and exits 0, applying
     nothing. `git -C <DimensionsRecomp> apply --directory=rexglue-sdk` does the same.
   - Before the real apply, confirm 5 "Checking patch" lines and no "Skipped patch". CHECKS.txt L24 warns (task #33).
3. Check the 5 after hashes. Do a full SDK rebuild (the cp.h layout changes) at ≤ 2 threads, write MANIFEST.txt, and
   run bincheck for the 3 needles (§8, FUNCTIONAL-ROWS.md §0).

Checked read-only:
- CHECKS.txt (Nov 22, 23:12): forward on orig/sdk exits 0 with 5 files; `-R` on new/sdk exits 0; the negative control
  (forward on new/sdk) exits 1 with "patch does not apply" (cp.h:15, dcl.h:37, cp.cpp:109, shared_memory.cpp:487,
  texture_cache.cpp:1250).
- Today, 07:58-07:59: the `--directory` form above against the snap1 SDK itself gives 5 "Checking patch" lines and
  exit 0. The negative control on new/sdk again gives "patch does not apply".

## 3. Switch

`d3d12_async_submit`: cvar, GPU/D3D12, bool, default false, **kInitOnly** (cp.cpp:122-124). It is read once, at the
end of SetupContext (L1942), and cached in `submit_async_` (cp.h:897). That member is true only if the split is on
and the thread started.

| `d3d12_submit_split_kb` | `d3d12_async_submit` | behaviour | #19 log lines |
|---|---|---|---|
| 0 (default) | false (default) | S4b | none |
| 0 | true | S4b | 1 WARN (L1944) |
| N > 0 | false | stage 1 (#18), as in S4b | none |
| N > 0 | true | splits submitted on "D3D12 Submit" | 1 INFO (L1956), counter lines (L4581) |
| N > 0 | true, thread creation failed | stage 1 | 1 ERROR (L1959) |

- Set it at launch. A runtime change does nothing until the next start.
- Native builds: leave it off (S2-6). The native path never calls EndSubmission, and the cvar is inert while the split
  is 0 (cvar comment, cp.cpp:114-121).

## 4. What changed

| file | after lines | change |
|---|---|---|
| cp.cpp | 114-124 | the cvar and its ordering comment |
| cp.cpp | 1936-1965 | end of SetupContext, just before `return true`: reset, cvar test, WARN; or 3 slots, thread create and name, INFO; or ERROR and slots freed |
| cp.cpp | 1972-1974 | ShutdownContext: `ShutdownAsyncSubmit()` right after `AwaitAllQueueOperationsCompletion()` (L1971) |
| cp.cpp | 3266-3270 | PublishOnDemandMemexport: drain after its `EndSubmission(false)` (L3264), before the global lock (L3271) |
| cp.cpp | 4022-4026 | CheckSubmissionFence: drain at the top of the `>=` branch (L4021), before EndSubmission (L4028) and the queue-operations Signal (L4037) |
| cp.cpp | 4304-4308 | EndSubmission: drain at its top |
| cp.cpp | 4456 | MaybeSplitSubmission's only changed line (below) |
| cp.cpp | 4483-4588 | `EndSubmissionAsync()` |
| cp.cpp | 4590-4605 | `DrainAsyncSubmissions()`: waits until the thread has issued every queued split (not until the GPU ran them) |
| cp.cpp | 4607-4644 | `AsyncSubmitThread()` |
| cp.cpp | 4646-4666 | `ShutdownAsyncSubmit()` |
| cp.h | 18, 43 | `#include <condition_variable>`, `#include <rex/thread.h>` |
| cp.h | 88-96 | public inline `FlushAsyncSubmissions()`: drains when on, does nothing otherwise |
| cp.h | 368-376 | the 4 private declarations |
| cp.h | 894-931 | the members (§6) |
| dcl.h | 41-46 | `Swap(DeferredCommandList&)`: asserts the same command processor, swaps `command_stream_` |
| shared_memory.cpp | 490-492 | `command_processor_.FlushAsyncSubmissions()` before UpdateTileMappings (L493) |
| texture_cache.cpp | 1253-1255 | the same, before UpdateTileMappings (L1264) |

The split call, L4456 (base: `} else if (EndSubmission(false)) {`):
```cpp
  } else if (submit_async_ ? EndSubmissionAsync() : EndSubmission(false)) {
```

`EndSubmissionAsync()` is `EndSubmission(false)` for a split (base L4245-4323 with `is_swap` false), with the submit
handed off:
1. If there is no writable allocator, it creates one as EndSubmission does. On failure it returns false before
   changing anything (L4490-4497), so the submission stays open (cond 3) and MaybeSplitSubmission counts `failed`
   (L4463-4466).
2. Asserts (L4505-4507), `pipeline_cache_->EndSubmission()` (L4509), `SubmitBarriers()` (L4513).
3. Under the mutex (L4518-4542): if all 3 slots are taken, it waits for one (`full_waits`, L4519-4529). It swaps the
   open submission's commands into the next slot's empty list (L4535), stores the allocator and `submission_current_`
   (L4536-4537) and counts the slot (L4538). Then it notifies the thread (L4543).
4. EndSubmission's bookkeeping: the allocator moves to the submitted list with this fence value (L4548-4559),
   `++submission_current_` (L4561), `submission_open_ = false` (L4563) and
   `queue_operations_done_since_submission_signal_ = false` (L4568).
5. The counter line, at most every 10 s (L4572-4586).

The thread's submit (L4626-4632) keeps EndSubmission's order (base L4297-4316) and runs outside the lock:
```cpp
    chunk.command_allocator->Reset();
    command_list_->Reset(chunk.command_allocator, nullptr);
    chunk.deferred_command_list.Execute(command_list_, command_list_1_);
    command_list_->Close();
    ID3D12CommandList* execute_command_lists[] = {command_list_};
    direct_queue->ExecuteCommandLists(1, execute_command_lists);
    direct_queue->Signal(submission_fence_, chunk.submission);
```
Then it resets the slot (L4633-4634) and, under the lock, adds the time, advances the ring and notifies (L4638-4642).

## 5. OFF keeps the old behaviour (= S4b at run time)

- Proofs ([PROOFS.txt](PROOFS.txt), ALL PASS, Nov 22 23:10):
  - P3: the only removed line is `} else if (EndSubmission(false)) {`, and the false arm of its replacement is that
    call.
  - P8: MaybeSplitSubmission is 45 lines, 1 differs, so stage 1's guards and holds are unchanged.
  - P4: the call-site edits (E3 cp.h FlushAsyncSubmissions, E9 the ShutdownAsyncSubmit call, E10-E12 the 3 drains in
    cp.cpp, E15/E16 the 2 tile flushes) add, besides comments, only lines from an allowed set:
    `if (submit_async_) {`, `DrainAsyncSubmissions();`, `}`, `ShutdownAsyncSubmit();` and
    `command_processor_.FlushAsyncSubmissions();`. E3's definition line, `void FlushAsyncSubmissions() {`, is exempted
    separately (make_s4r1s2.py L608-609). The last two calls are unconditional, and their bodies are inert when off
    (L4649-4652, cp.h:92-96).
  - P10: EndSubmission is the base plus the guarded drain only (123 → 129 lines).
- What still runs with OFF:
  - SetupContext: 3 resets and the cvar test (L1939-1942), plus the WARN if the cvar is on with split 0.
  - One `if (submit_async_)` test at each drain or flush site: L3268, L4024, L4306 and cp.h:93 (reached from
    shared_memory.cpp:492 and texture_cache.cpp:1255).
  - The ternary's test, only when the split is on and a split is due (L4456).
  - ShutdownContext's `ShutdownAsyncSubmit()` call, which sets `submit_async_ = false` and returns, since there is no
    thread (L4649-4652).
- No thread, no slots (the 3 `unique_ptr`s stay null; they are made only when ON, L1946-1948) and no log line.
- The cost when off: those tests, and the cp.h layout change (new members), which needs a full SDK rebuild, as stage 1
  did.
- Runtime proof after the break: row a (OFF vs s4b01: logdiff NEW 0, MORE 0, GONE 0), row i (split only vs s4b10:
  stage 1 unchanged, NEW 0, GONE 0) and row b (cvar on with split 0: exactly 1 WARN).

## 6. Threads and ownership

| thread | with #19 ON | S4b today |
|---|---|---|
| GPU Commands | records; queues each split (EndSubmissionAsync); every other submit stays here, after a drain; every other queue operation comes after a drain or flush, with two harmless exceptions ("Presenter" below); also runs the presenter's guest-output refresher (IssueSwap's lambda, presenter:560), the tracker Signal after it (presenter:567) and, in the default paint mode, paint (presenter:1173, through ui/presenter.cpp:641) | records and submits everything |
| "D3D12 Submit" (new, default priority) | submits the queued splits in FIFO order (L4607-4644); takes only its own mutex | - |
| UI (presenter paint, d3d12_presenter.cpp:1173, in the kUIThreadOnRequest paint mode: ui/presenter.cpp:1316-1339, :473-475) | unchanged; ordered against GPU Commands by fences, as today | same |
| the thread that reads a memexport page (ProvideOnDemandMemexportThunk, L3430-3436) | RetireOnDemandMemexport's fence wait, for published batches only (L3322-3326), under the global lock; no split is involved ("Waits that do not drain" below) | same |

- **Life:** created last in SetupContext (L1952-1955), so a failed setup leaves no thread (L1936-1938). Joined in
  ShutdownContext (L1974, `rex::thread::Wait` at L4658) after `AwaitAllQueueOperationsCompletion()` (L1971). It uses
  the same thread API as the pipeline cache (base `pipeline_cache.cpp:163`, `:165`, `:182`).

**Ownership rules**
1. **Ring.** One producer (GPU Commands, EndSubmissionAsync) and one consumer (the thread). There are 3 slots
   (cp.h:902), the oldest at `async_submit_first_`. The ring head and count, the stop flag and the stats are guarded
   by `async_submit_mutex_` (cp.h:912, :917-929). `async_submit_last_log_` is GPU Commands only (cp.h:930-931).
2. **Slots.** GPU Commands fills a free slot under the mutex (L4530-4538) and notifies. The thread uses only the
   oldest counted slot, outside the lock. It resets the slot's list (L4633-4634) and gives the slot back under the
   lock (L4638-4642). A slot stays counted until its Signal is issued, so GPU Commands is at most 3 splits ahead of
   the queue.
3. **Native command lists.** While splits are queued, only the thread touches `command_list_` and `command_list_1_`.
   On GPU Commands only EndSubmission (after its drain), SetupContext (before the thread starts) and ShutdownContext
   (after the join) use them. P6 checks the member names used in the thread body.
4. **Allocators.** A split takes `command_allocator_writable_first_`, which holds only allocators the GPU is done with,
   or new ones. It moves to the submitted list at once with the split's fence value (L4548-4559), so reclaim
   (CheckSubmissionFence L4079-4094) waits until the GPU has passed the thread's Signal. Two queued splits never share
   an allocator. Cache clears run inside EndSubmission, after its drain.
5. **Fence values.** Given out on GPU Commands, in order, when a split is queued (L4537, L4561). The thread signals the
   oldest slot first (L4622, L4632). So `submission_fence_` values reach the queue in order (S2-3).
6. **Retirement.** Everything a split references (upload, readback and descriptor pools; texture, render-target and
   shared-memory state) is tagged at record time with the split's submission number and retired from the fence
   (`submission_completed_`). Nothing is freed before the thread's Signal has completed on the GPU.
7. **Pipelines.** Execute resolves handles with an atomic acquire load (`pipeline_cache.h:101-102`). A split happens
   only when `CanEndSubmissionImmediately()` holds (L4454), so every pipeline in it exists. Pipelines live until
   shutdown.
8. **Deferred lists.** `Swap` (dcl.h:41-46) moves the open submission's stream into the slot. Recording goes on in the
   slot's old, empty stream after BeginSubmission's Reset.

**Queue order (S2-2, P5).** Every queue operation of the GPU Commands thread comes after the queued splits, with two
harmless exceptions (in the last two rows):

| site | function | operation | ordered by |
|---|---|---|---|
| cp.cpp:4037 | CheckSubmissionFence (`>=` branch) | queue-operations fence Signal | the drain at L4024-4026 |
| cp.cpp:4364, :4378 | EndSubmission | ExecuteCommandLists, Signal | the drain at L4306-4308 |
| cp.cpp:4631, :4632 | AsyncSubmitThread | ExecuteCommandLists, Signal | FIFO on the thread |
| shared_memory.cpp:493 | AllocateSparseHostGpuMemoryRange | UpdateTileMappings | the flush at L492 |
| texture_cache.cpp:1264 | EnsureScaledResolveMemoryCommitted | UpdateTileMappings | the flush at L1255 |
| d3d12_presenter.cpp:567 (`NextSubmission`, d3d12_submission_tracker.cpp:97-111) | RefreshGuestOutputImpl (presenter:517), after IssueSwap's refresher returns (:560) | the refresher tracker's Signal | the refresher's `EndSubmission(true)` drain (L2624); none after either early return (L2470, L2564), see "Presenter" |
| d3d12_presenter.cpp:1173-1202 | Presenter::PaintAndPresent (ui/presenter.cpp:1507), called in RefreshGuestOutput (:641), default paint mode only | paint's ExecuteCommandLists, the paint tracker's Signal, Present and the present tracker's Signal | the refresher's drain (L2624) after a successful refresh; none for the blank frame when the guest output turns inactive (ui/presenter.cpp:580-587), see "Presenter" |

- EndSubmission's callers are all drained by its top: IssueSwap L2624/L2630 (true), OnPrimaryBufferEnd L2636,
  PublishOnDemandMemexport L3264, CheckSubmissionFence L4028, the sync arm of L4456, and the occlusion paths L6055 and
  L6111.
- Scope (non-recursive grep in snap1, today 07:55): in `src/graphics/d3d12/` only cp.cpp, shared_memory.cpp and
  texture_cache.cpp call `GetDirectQueue()` (the 3 files P5 scans). In `src/ui/d3d12/` only d3d12_presenter.cpp does:
  paint's ExecuteCommandLists (:1173) runs on GPU Commands in the default paint mode and on the UI thread otherwise,
  and the refresher tracker's Signal (:567, through d3d12_submission_tracker.cpp:111) runs on GPU Commands. P5 does
  not scan the presenter.
- The tile flushes are needed. Tile heaps are created not zeroed (`GetHeapFlagCreateNotZeroed()`), so mapping a range
  ahead of an older pending split is not provably harmless.
- Presenter (corrected in rev 1 and in task #33): the guest-output refresher is IssueSwap's lambda (L2364-2626). The
  presenter calls it synchronously on GPU Commands (presenter:560). It ends with `EndSubmission(true)` (L2624), which
  drains, so the tracker Signal that follows (presenter:565-567) comes after the frame's splits. Paint
  (presenter:1173) follows the paint mode (ui/presenter.cpp:1316-1339). In the default mode,
  kGuestOutputThreadImmediately (`host_present_from_non_ui_thread` defaults to true, ui/presenter.cpp:29; D3D12
  reports no implicit vsync, presenter:381, :509; no UI drawer), paint runs on GPU Commands inside RefreshGuestOutput,
  right after a successful refresh (ui/presenter.cpp:638-641), so after the same drain. In kUIThreadOnRequest, which
  the UI thread also switches to while it paints itself (ui/presenter.cpp:473-475; back to the desired mode at
  ui/presenter.cpp:522), paint runs on the UI thread, ordered by fences, as today. Exception 1: either early return of
  the refresher (L2470, or the FXAA-descriptor fallback's `return false` at L2564) skips L2624. The presenter still
  signals (presenter:565-567; comment :561-564), so splits still queued reach the queue after that Signal (they drain
  at L2630), and the failed refresh paints nothing (ui/presenter.cpp:572-577). This is harmless: the tracker's value
  guards the guest output resource, and splits never reference it. The only commands that do, the fallback's copy and
  its barriers (L2555-2563), reach the queue at L2630, after the Signal, with #19 off as well. Exception 2: when the
  guest output turns inactive, RefreshGuestOutput paints one blank frame without calling the refresher
  (ui/presenter.cpp:580-587), so in the default mode that paint can reach the queue before splits still queued. This
  is harmless: the blank frame uses no guest output resource (presenter:623-624; the mailbox index is UINT32_MAX,
  ui/presenter.cpp:856), and splits never touch the swap chain.

**Waits that do not drain (risk 6).** `CheckSubmissionFence(N)` with N < `submission_current_`: the frame pacing in
BeginSubmission (L4206), the occlusion query wait (L6116) and `CheckSubmissionFence(0)` (L3731). They wait on
`submission_fence_`. The thread signals a queued split's value right after its ExecuteCommandLists and never waits on
anyone, so the wait ends when the thread and then the GPU get there. A drain here would put a full drain into every
BeginSubmission after a split, which is the cost stage 2 removes. The `>=` branch keeps its clamp
(`await_submission = submission_current_ - 1`, L4052-4054). It is reached only through
AwaitAllQueueOperationsCompletion (cp.h:377-378): memexport readback (L3540, L3634, L3692), readback resolves (L3986,
L3995), the cache clear (L4395) and shutdown (L1971).
- RetireOnDemandMemexport (L3307) is a different wait (corrected in rev 1). It waits on `submission_fence_` directly
  (SetEventOnCompletion + WaitForSingleObject, L3322-3326), under the global lock (L3308), on the thread that reads a
  memexport page (ProvideOnDemandMemexportThunk, L3430-3436). It waits only for published batches (L3310,
  L3317-3321), and PublishOnDemandMemexport drains before it publishes (L3268-3270; comment L3315), so no queued split
  is involved.

**No deadlock.** The thread blocks only on its own mutex and work condition variable (L4616-4617). It never waits for
GPU Commands, the GPU, a fence or another lock, and ExecuteCommandLists and Signal only enqueue. So every GPU Commands
wait (full ring L4519-4529, drain L4590-4605) ends after bounded CPU work on the thread. PublishOnDemandMemexport
drains before it takes the global lock (L3266-3271), so cp.h:735-737 ("every pending copy is already submitted, so its
completion does not depend on any thread") still holds.

## 7. Failure modes and shutdown

| case | where | what happens |
|---|---|---|
| cvar on, split 0 | L1943-1944 | 1 WARN; stays off = S4b |
| thread creation fails | L1958-1963 | 1 ERROR; slots freed; stays off = stage 1 |
| SetupContext fails earlier | block placed last, L1936-1938 | no thread is created |
| no command allocator for a split | L4490-4497; L4463-4466 | returns false before touching the ring; the submission stays open and recording goes on in it; `failed` is counted (cond 3, as in stage 1) |
| a D3D12 call fails on the thread | L4626-4632 | HRESULTs are ignored, as EndSubmission does; the Signal is always issued, so waits end |
| device removed | BeginSubmission L4181-4183, L4190-4201 (unchanged) | `GetCompletedValue` returns UINT64_MAX and fence events fire, so waits end; the thread's calls fail fast; no special code, as in the sync path |
| shutdown | L1971-1974; L4646-4666 | AwaitAllQueueOperationsCompletion drains (through CheckSubmissionFence's `>=` branch) and waits for the GPU; ShutdownAsyncSubmit then joins a thread whose ring is empty; the rest of ShutdownContext runs synchronously (`submit_async_` false) |
| stop with splits still queued | L4618-4621 | the thread submits them all before it exits (not reachable through ShutdownContext, which drains first) |

- Every ON setup failure falls back to stage 1 (thread) or to S4b (split 0).
- OFF never creates the thread, so none of the thread's paths can run with the default (§5).

## 8. Log lines

| line | when | where |
|---|---|---|
| `d3d12_async_submit: submitting splits on the submit thread (3 slots)` (INFO) | once at init, when the cvar and the split are both on | L1956 |
| `d3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off` (WARN) | once at init, cvar on and split 0 | L1944 |
| `d3d12_async_submit: failed to create the submit thread, staying off` (ERROR) | init, thread creation failed | L1959 |
| `d3d12_async_submit: frame= submission= chunks= queued_max= full_waits= full_wait_us= drains_waited= drain_wait_us= worker_us=` (INFO) | at an async split, at most every 10 s (the first split logs at once); totals since start | L4581-4582 |
| stage 1's `d3d12_submit_split: frame= submission= splits= failed= held_query= held_scratch= held_pipelines=` | unchanged; `splits` counts async splits too | L4475-4476 |

- Reading the counter line: Δchunks/Δframe is async splits per frame. worker_us/chunks is the submit cost moved off
  GPU Commands. drain_wait_us and full_wait_us are what GPU Commands still waits. queued_max is at most 3.
- Frame stats do not include the drain and full-ring waits (risk 2).
- Bincheck needles (FUNCTIONAL-ROWS.md §0): the strings at L1944 and L1956, and the counter format's prefix at L4581.

## 9. Proofs P1-P10: what each covers

[make_s4r1s2.py](make_s4r1s2.py) rebuilds new/ from orig/ with exact-once edits E1-E16 and writes nothing if an anchor
is not found exactly once. Its output, PROOFS.txt, is ALL PASS (Nov 22, 23:10).

| proof | checks | covers |
|---|---|---|
| P1 | each orig/ file == the snap1 bytes and == the S4b after-hash in PATCHES-S4b.tsv (texture_cache.cpp: not patched in S4b) | the base is S4b |
| P2 | each anchor E1-E16 is found exactly once in the base, and once before applying | the edits land where intended |
| P3 | the only removed line is MaybeSplitSubmission's `} else if (EndSubmission(false)) {`; its replacement's false arm is the same call | S2-1, S2-5 |
| P4 | the call-site edits E3, E9, E10, E11, E12, E15 and E16 add only allowed guarded lines (§5; E3's definition line is exempted) | S2-5 (OFF) |
| P5 | each queue operation (ExecuteCommandLists, Signal, UpdateTileMappings, Wait) in cp.cpp, shared_memory.cpp and texture_cache.cpp has a drain or flush earlier in the same function, or is in AsyncSubmitThread: 7 sites | S2-2 |
| P6 | the members named in AsyncSubmitThread's body are within the allowed set (the `async_submit_*` ring, slots, mutex, condition variables and stats; `command_list_`, `command_list_1_`, `submission_fence_`); it does not follow calls (Execute's pipeline lookups, rule 7; `GetD3D12Provider().GetDirectQueue()`, L4613) | S2-4, in part |
| P7 | balanced `{}`, `()` and `[]` in the added lines, per file | a weak syntax proxy only |
| P8 | MaybeSplitSubmission: 45 lines, 1 differs | its stage-1 guards and holds are unchanged (cond 3 on the async arm rests on the L4490-4497 code read; cond 6 is not a code property) |
| P9 | LF only and a final newline, 5 files | apply hygiene |
| P10 | EndSubmission == base + the guarded drain only (123 → 129 lines) | S2-1, S2-5 |
| CHECKS | `git apply --check`: forward on orig 0, `-R` on new 0, forward on new 1 | the diff applies to orig (= S4b by P1), new = orig + diff, and it does not apply twice |

Conditions proposed for stage 2 (NOTE.md "Conditions"), with their evidence:

| cond | static evidence (now) | runtime evidence (after the break) |
|---|---|---|
| S2-1: the thread takes only splits; every other submit stays synchronous after a drain | P3, P10; L4456 is the only call site of EndSubmissionAsync | c, d: NEW = the async keys only |
| S2-2: every queue operation of the GPU Commands thread comes after the queued splits | P5 (3 files); §6 table and scope grep; two harmless exceptions outside P5's files: the presenter's tracker Signal after either early return of the refresher, and the blank default-mode paint when the guest output turns inactive (§6 "Presenter") | e (queries), f (the memexport drains), g (debug layer), every async row's shutdown (L1971 → L4022-4026); the tile flushes are not shown (§10.8) |
| S2-3: fence values given out in order on GPU Commands, signalled in FIFO order | code read: L4537, L4561, L4622, L4632 | no direct check; g, j and e can only catch its effects (debug-layer messages, hangs) |
| S2-4: the thread touches only its own state, the native lists, the fence, the direct queue (L4613) and, through Execute, the pipeline handles (rule 7); it waits only on its mutex | P6 (names in the thread body only); code read L4607-4644 and Execute's lookups (dcl.cpp:400, :622 → cp.h:200-201 → pipeline_cache.h:101-102) | j (full ring), e (soak) |
| S2-5: off = stage 1 (S4b), byte for byte at run time | P3, P4, P10 | a, i, b |
| S2-6: native builds off | default false; nothing sets it; inert while the split is 0 | none (no native row) |
| S2-7: joined at shutdown, after all queue operations have completed | ShutdownContext order, L1971-1974 | every async row's close (pass rule 1; no "D3D12 Submit" thread left) |

What the proofs do not show:
- P5 is textual. It sees a drain earlier in the same function, not that the drain dominates the queue operation on
  every path (§11.1). It scans only cp.cpp, shared_memory.cpp and texture_cache.cpp, so it misses the presenter's
  tracker Signal and its default-mode paint (§6).
- P6 checks the names in the thread body, not races and not what its calls touch (Execute's pipeline lookups, rule
  7). The race argument is the mutex hand-off in §6, for your code read (§11).
- P4 checks a line set, not where the lines sit.
- P7 is not a compile (§10.1). None of P1-P10 runs anything.

## 10. What is NOT proven yet

1. **No compile and no syntax check.** The staging rules this morning allow no compiles. When they do: the
   `bench/agent7/s4r1r2_syntax.ps1` method (clang `-fsyntax-only` with the dev SDK flags, control vs candidate, one
   compile at a time at BelowNormal) on cp.cpp, shared_memory.cpp and texture_cache.cpp, plus the other TUs that
   include cp.h or dcl.h (graphics_system, pipeline_cache, primitive_processor, render_target_cache,
   deferred_command_list). The new code uses only APIs the SDK already uses (NOTE.md "Syntax check").
2. **`<N>` is not chosen.** It waits for Agent 3's ready-N gate (from the s4b10/s4b16 counters);
   `build/agent3/s4b/ready-N` is absent (checked 08:10 today). Rows a, b and j don't need it. Rows i, c, d, f, e, g and
   W7's s18/s19 do (s19h uses `<N/2>`).
3. **Nothing has run.** There is no bin (`build/agent2/devoff4b-s4r1s2-bin` is absent) and no
   `build/agent3/s4b/ready-s4r1s2` (both checked 08:10).
4. **Device loss with splits queued** is a code read only; there is no safe way to cause it (§7, §11.8).
5. **The gain is unmeasured.** The drains may eat it (risk 1).
6. **The rows and the soak are first drafts** (Nov 22, 23:33 and 23:35). The soak's counter-line checker (monotonic
   counters, per-frame rates) is not written.
7. **W7's matrix is a draft.** Agent 8 owns the final.
8. **The tile flushes are not shown at run time.** texture_cache.cpp:1255 runs only with resolution scaling, which no
   row sets. shared_memory.cpp:492 runs only when a new tiled range is mapped, and the counter line does not tell the
   drain and flush sites apart. Both rest on the code read (§11.2).

## 11. Code-read items for Agent 10

1. **Ordering completeness (S2-2).** P5 is textual. Please confirm that each drain or flush dominates its queue
   operation on every path, and that the GPU Commands thread has no queue operation outside the §6 table (for example
   through a queue pointer obtained some other way). The independent read found one, the presenter's tracker Signal,
   and the task #33 read a second, the presenter's default-mode paint; they are now the last two rows of that table.
2. **Flush callers.** `FlushAsyncSubmissions()` gives ordering only on the producer thread. Its callers are
   shared_memory.cpp:492 (AllocateSparseHostGpuMemoryRange, reached from EnsureHostGpuMemoryAllocated in
   RequestRanges, base `graphics/shared_memory.cpp:455`) and texture_cache.cpp:1255 (EnsureScaledResolveMemoryCommitted,
   once per new scaled-resolve heap, only with resolution scaling). Please confirm both run only on the GPU Commands
   thread.
3. **Global lock (risk 5).** The shared-memory flush runs before RequestRanges takes the global lock (base :455 vs
   :475). Please confirm that no caller of EnsureHostGpuMemoryAllocated holds it. If one did, it would cost time
   only, since the thread never takes the global lock.
4. **Non-draining waits (risk 6).** Only CheckSubmissionFence's `>=` branch drains, because it issues a queue
   operation. Please confirm that the plain fence waits in §6 end without a drain.
5. **L4568,** `queue_operations_done_since_submission_signal_ = false` in EndSubmissionAsync. A queue operation done
   before this point was issued before the thread's Signal of this submission (the drains make sure of that), so
   awaiting the submission awaits it too.
6. **Execute on another thread.** `DeferredCommandList::Execute` now runs on "D3D12 Submit" for splits. Executes stay
   serialized: a synchronous Execute runs only in EndSubmission after a drain, and the mutex orders the hand-offs.
   NIT: the comment on the R2 counters at dcl.cpp:89-90 ("Touched only by Execute, which runs only inside
   D3D12CommandProcessor::EndSubmission on the GPU Commands thread") is stale when #19 is on. The counters are
   compiled out by default (`REX_D3D12_DEFERRED_COUNTERS`, dcl.cpp:19-28), no #19 row or W7 arm uses the counters
   build, and dcl.cpp is not in the diff.
7. **3 slots and the default thread priority** (risks 3 and 4).
8. **Device loss with splits queued** (§7): waits end on UINT64_MAX, the thread's calls fail fast, and shutdown still
   joins.

## 12. Risks (NOTE.md "Risks and open questions")

1. **The drains may eat the gain.** OnPrimaryBufferEnd (L2633-2636, `d3d12_submit_on_primary_buffer_end`, default
   true) submits synchronously at each primary-buffer end, which drains. In this title that is about once per frame,
   just before the swap. `drain_wait_us` measures it. A later "stage 2b" could make that submit async too; it is not
   staged.
2. **Frame stats** do not include the drain and full-ring waits (`kFenceWait` is untouched); only the counter line
   shows them. W7's read-out (fps, median ms) is not affected.
3. **3 slots** let GPU Commands run up to 3 splits ahead; `full_waits` shows if that is too few. Memory, only when ON:
   3 more deferred-list streams. Each starts with a 1 MiB reserve (dcl.cpp:221) and keeps its capacity across Reset
   (`clear()`, dcl.cpp:225). Streams rotate through Swap, so the extra is between 3 MiB and 3 x the largest list held.
4. **Thread priority** is the default. The thread competes with GPU Commands for P-cores (W5's slow runs were P-thread
   saturation), so check sys.csv for the slow state in each row.
5. **Locks held during a flush** (§11.3).
6. **A difference from my design note:** the note had every CheckSubmissionFence wait drain. The staged code drains
   only the `>=` branch (§6).

## 13. Functional rows and soak after the break

Full commands and pass rules: [FUNCTIONAL-ROWS.md](FUNCTIONAL-ROWS.md); queue rows
[queue-s4r1s2.jsonl](queue-s4r1s2.jsonl) (s4r1s2-a, -b, -i, -j, -c, -d, -f, -e, -g); soak [SOAK.md](SOAK.md).

Before any row (FUNCTIONAL-ROWS.md §0):
1. Agent 2 applies the diff (§2), builds at ≤ 2 threads and stages `build/agent2/devoff4b-s4r1s2-bin` with
   MANIFEST.txt.
2. bincheck finds the 3 needles (§8) in that bin and none in `build/agent2/devoff4b-bin`.
3. Agent 3 creates `build/agent3/s4b/ready-s4r1s2`. Every row also needs `ready-later`, the `<N>` rows (i, c, d, f, e,
   g) need `ready-N`, and row g needs `ready-dbg` (present at 08:10).
4. Idle host only: no window running, HOLD absent, hostload.csv clang++ = 0.

Pass rules for every row (FUNCTIONAL-ROWS.md §1):
- clean exit, no fail marker, no .dmp, no hang;
- a logdiff against the named reference in which only the row's keys are NEW and there is no new WARN or ERROR key;
- the #19 lines: INIT once when on, counter chunks rising, queued_max ≤ 3, #18 `failed=0`, never the ERROR;
- busy < 0.97 where the row has frame stats, and the sys.csv slow-state check.

| row | cvars on the #19 bin | reference (devoff4b-bin) | proves | `<N>` | min |
|---|---|---|---|---|---|
| a | none | s4b01 | OFF = S4b: NEW 0, MORE 0, GONE 0; no #18/#19 line (S2-5) | no | 4.4 |
| b | async on, split 0, 90 s | - | exactly 1 WARN (L1944), no other #18/#19 line (S2-5) | no | 1.9 |
| i | split `<N>` | s4b10 | stage 1 unchanged by the diff: NEW 0, GONE 0, failed 0 (S2-5, P8) | yes | 4.4 |
| j | split 16 + async | s4b11 | stress: queued_max ≤ 3, full_waits > 0 expected, failed 0, no hang (S2-4) | no | 4.4 |
| c | split `<N>` + async | s4b10 | ON identity: NEW = the INIT and counter keys only; chunks > 0 (S2-1) | yes | 4.4 |
| d | split `<N>` + async + `framerate_limit=0`, 180 s | s4b25 | W7's s19 arm: proof lines, submissions and chunks per frame (functional only) | yes | 3.4 |
| f | split `<N>` + async + `d3d12_readback_memexport=true` | s4b13 | the memexport drains: PublishOnDemandMemexport's (L3266-3270) and, where the readback waits, the `>=` branch's (L4022-4026, through AwaitAllQueueOperationsCompletion at L3540, L3634, L3692) | yes | 4.4 |
| e | split `<N>` + async + `framerate_limit=0`, level route (toypad), 600 s | s4bL0 | 10-min soak: queries (held_query > 0; their EndSubmission calls at L6055 and L6111 drain at L4306-4308), the shared-memory tile flush if a new tiled range is mapped (not counted), monotonic counters (S2-2, S2-7) | yes | 9.3 |
| g | split `<N>` + async + `d3d12_debug=true` | s4b15 | no new debug-layer message keys (S2-2, S2-3) | yes | 4.4 |

- Order: a, b, i, j; then c, d, f, e; g last. Stop at the first FAIL.
- Row e needs the toypad (queue `"toypad": true`, route `build/agent3/toypad/routes/level-l.txt`).
- Corrected in rev 1: queries do not take the L4022-4026 drain (row f and every shutdown do), and no row sets
  resolution scaling, so the texture-cache flush does not run (§10.8). FUNCTIONAL-ROWS.md row e and SOAK.md's soak
  bullet now say the same (corrected in task #33, §15).
- About 41 min of runs plus about 10 min of checks. Without `<N>` (a, b, j): about 11 min.
- b2r §17's stage 1 tests, carried over: query-guard suppressions (held_query > 0 in e); cold-PSO suppressions
  (optional row k: c with a cold pipeline cache, held_pipelines > 0); one pass with `d3d12_readback_memexport=true`
  (f); a clean ON-vs-OFF logdiff with the counter line allowed (c, i).
- Submissions per frame and the drain cost come from the counter lines of c, d and e.
- Shutdown with splits queued (S2-7): every async row closes while splits may be queued. ShutdownContext's
  AwaitAllQueueOperationsCompletion (L1971) takes the L4022-4026 drain. Pass rule 1 applies, plus no "D3D12 Submit"
  thread left.
- Soak = e + j (SOAK.md). The manual add-ons (resize, minimize, alt-tab, close button) run only with a person at the
  desktop.

## 14. W7 arms (draft; Agent 8 owns the final matrix): [matrix-w7-draft.json](matrix-w7-draft.json)

| arm | cvars (every arm on `<DEVOFF4B-S4R1S2>`) | x |
|---|---|---|
| s0 (ref) | `framerate_limit=0`, `d3d12_submit_split_kb=0` | 4 |
| s18 | `framerate_limit=0`, `d3d12_submit_split_kb=<N>` | 4 |
| s19 | `framerate_limit=0`, `d3d12_submit_split_kb=<N>`, `d3d12_async_submit=true` | 4 |
| s19h (optional) | as s19, with `<N/2>` | 4 |

- One bin for every arm, so the arms differ only in kInitOnly cvars. No env keys (`env {}`).
- Runs: 1 cold + 3 x 4 = 13 runs, about 30-34 min; with s19h, 17 runs, about 39-45 min. S4-DRAFT's 4th arm
  (#18 + #19 + #20) is dropped because #20 step 2 is not staged.
- Proof per run (game.log, before any fps is read): s0 has no split or async line; s18 has the split lines and no
  async line; s19/s19h add the async INIT and counter lines (chunks > 0, queued_max ≤ 3) and no async WARN or ERROR.
  threads.csv shows "D3D12 Submit" in s19/s19h only.
- Read-out: GPU Commands CPU ms/f (threads.csv) and fps first, then median ms and p99. Paired within-round deltas vs
  s0 come from `bench/agent7/w4b_readout/w4b_readout.py <dir> --all`, and T-std / B-block with its guards from
  `build/agent7/w4b-noise/readout.py <dir>`. Expected: s18 ties s0 (cond 6); s19 lowers GPU Commands ms/f by about
  the "D3D12 Submit" thread's ms/f, less the drains.
- Validity: busy < 0.97 in the scored runs; slow-state runs are dropped or scored only up to the onset; light-phase runs
  are excluded as in W5.
- Gate: only after (b) is rated SAFE and the rows and the soak pass. Timing comes only from the user's double-click
  run; agent runs are functional only.
- For Agent 8's final copy: the draft's source note cited "S4-DRAFT.md L391" (W7 is L416 now), and s18's note
  (L37) said "S4-DRAFT section 17 cond 6" (it is b2r's, L799). Both are fixed in the draft (task #33).

## 15. Open items

- Agent 10's rating of (a)-(c), after the break.
- The syntax check (§10.1), then Agent 2's build, MANIFEST and bincheck.
- `<N>` from Agent 3's ready-N gate; then replace `<N>` and `<N/2>` in the queue rows and in Agent 8's final W7.
- Re-check the rows' busy and slow-state commands and their minutes; write the soak's counter-line checker.
- Corrected 11-23 09:04 (task #33): rev 1's corrections are now in FUNCTIONAL-ROWS.md (row e, L60), SOAK.md (the
  soak bullet, L17-21) and NOTE.md (the presenter paragraph, L161-178; RetireOnDemandMemexport's wait, L188-191; S2-2,
  L233; S2-4, L235). CHECKS.txt L24 warns about L22-23's apply form, and matrix-w7-draft.json's cites are fixed (§14).
- Corrected 11-23 09:39 (task #33): the task #33 read found that paint runs on GPU Commands in the default paint mode
  (not only on the UI thread) and a second early return of the refresher (L2470); fixing them turned up a second
  harmless exception, a blank paint when the guest output turns inactive. Fixed here (§6, §9, §11.1) and in NOTE.md
  (the presenter paragraph and S2-2, at the lines above). Row e's query drains also cite L6055 (§13,
  FUNCTIONAL-ROWS.md, SOAK.md), and CHECKS.txt L24 is scoped to SDK roots without their own .git, such as snap1.
- Corrected 11-23 09:59 (task #33), after a re-read of the 09:39 edits: the 09:39 notes (above, the header, README.md,
  HANDOFF.md) now credit the read with the default-mode paint and the L2470 early return; the blank paint was found
  while fixing them. §6's paint row covers the whole paint (d3d12_presenter.cpp:1173-1202: ExecuteCommandLists, the
  paint tracker's Signal, Present, the present tracker's Signal, all on the direct queue), and "Presenter" cites the
  Signal (presenter:565-567) and the UI thread's switch back to the desired paint mode (ui/presenter.cpp:522).
  NOTE.md's 09:04 note is restored as written (its 09:39 note supersedes it), and its presenter paragraph says the
  same (ui/presenter.cpp:522). CHECKS.txt L24 has one full tag per time.
- Still open, not owned by task #33: queue-s4r1s2.jsonl row e's note still says "level load (tile-mapping
  flushes)"; this file's §13 table is the corrected reading.
- Optional: a row with resolution scaling on, to run the texture-cache flush (it needs an S4b reference at the same
  scale).
- CHECKS.txt L22-23's apply form skips every file (§2; its L24 warns). Agent 2 should copy new/sdk/ or use the §2 form.
- Stage 2b (an async OnPrimaryBufferEnd submit) is not staged.

## 16. Verdict asked (after the break)

- (a) Default-off test bed in devoff4b: SAFE / SAFE WITH CHANGES / NOT SAFE.
- (b) ON (split `<N>` + async) in the rows, the soak and W7: SAFE / SAFE WITH CHANGES / NOT SAFE.
- (c) The threading and ownership rules (§6) and the §11 code reads: accepted, or what is missing.
