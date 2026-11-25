# s33: opt-in non-blocking pipeline creation (D3D12), design note

- **Status: staged only.** Not applied, not built, not run. Written by the helper for Agent 6 (item #33) on 2026-11-23.
  - **Rated by Agent 10** at 07:24-07:36 (`build/agent10/t27/r33-popin.md`): OFF SAFE, ON SAFE-IF, no blocker.
  - §10 is the dated rating block, with what was done for each item.
- **Base:** the live tree `DimensionsRecomp/rexglue-sdk` at HEAD `5350b1d` ("S4b: C1 v3 keep-watch, ...").
  - The 4 target files are clean against HEAD and use LF line endings.
  - Line numbers below are from the live tree before the patch, unless marked "patched".
- **Patch:** `s33-popin.patch`. It touches 4 files with 10 hunks, +105/-24. `git apply --check` passes with no offsets; see `CHECK.txt`. Hunks are numbered #1-#10 in patch order, as listed in `CHECK.txt`.
  - Build the first test bin without hunk #5 (Agent 10 S1). §10 says which lines to drop.
- **Notes:** `perf-notes/agent6-attract-stalls.md`:
  - §2: how a miss becomes a stall;
  - §6 L215: the idea;
  - §10 L301: the cvar;
  - §10.3 L437-464: the change, the risks and the 5-row test table.
  - The notes' line numbers are from an older HEAD. Everything below was re-located in 5350b1d.

## 1. Current behaviour (5350b1d)

`async_shader_compilation` defaults to true and is hot-reloadable (`src/graphics/command_processor.cpp:126`). With it on:

1. **A miss is queued.**
   - `PipelineCache::ConfigurePipeline` (`src/graphics/d3d12/pipeline_cache.cpp:928`) sets `use_async = async_shader_compilation && !creation_threads_.empty() && pixel_shader != nullptr` (L942-943).
   - On a cache miss it counts `kPipelineMiss` (L1043) and makes a `Pipeline` whose `state` is null (L1045-1048).
   - An async pipeline is pushed onto `creation_queue_` under `creation_request_lock_`, and one worker is woken (L1051-1068).
   - Every other pipeline (no PS, no creation threads, or async off) is created synchronously and timed as `kPipelineCreate` (L1070-1071).
2. **The draw is dropped.**
   - `D3D12CommandProcessor::IssueDraw` (`src/graphics/d3d12/command_processor.cpp:2757-2760`) checks `GetD3D12PipelineByHandle(handle)`, an acquire load (`include/rex/graphics/d3d12/pipeline_cache.h:101-103`).
   - If async is on and that returns null, it does `return true;`. Nothing counts this.
   - The drop comes before texture requests, before any binding, before memexport bookkeeping and before the draw itself.
3. **The submission waits.**
   - `D3D12CommandProcessor::EndSubmission` calls `pipeline_cache_->EndSubmission()` at L4282, before the deferred command list is replayed at L4299.
   - `PipelineCache::EndSubmission` (pipeline_cache.cpp:780-815) first requests the storage flushes (L781-794).
   - Then, if there are creation threads (L795-814):
     - it drains the queue on the GPU thread with `CreateQueuedPipelinesOnProcessorThread` (L3287-3309);
     - if a worker is still busy, it resets `creation_completion_event_` (manual-reset, L149) and sets `creation_completion_set_event_` under the lock;
     - it blocks in `rex::thread::Wait` until the last busy worker sets the event (L3247-3252).
   - This is the stall from notes §2: the submission pays, on the GPU thread, for creating everything that is queued.
4. **No early submissions while creating.**
   - `CanEndSubmissionImmediately()` (L4370-4372) is false while anything is queued or busy.
   - So `OnPrimaryBufferEnd` (L2587-2592) keeps the submission open, and `MaybeSplitSubmission` counts `held_pipelines` (L4392-4393).
5. **Net effect:** pop-in covers the draws after a miss in the same submission. The creation cost becomes a stall at that submission's end, usually the swap.

**Why the wait exists.** The replay resolves each handle at execute time, and skips `SetPipelineState` when the state is null (`src/graphics/d3d12/deferred_command_list.cpp:398-401`, `620-625`).
- With async on, IssueDraw never records a pending pipeline. For those draws the wait is a policy (pop-in limited to one submission), not a correctness requirement. Notes §10.3 says the same.
- The wait is still required for draws recorded while async is off whose handle is still pending. Examples:
  - pipelines queued before async was turned off at runtime;
  - stored pipelines from the storage loader (L668-675 queues them whenever there are threads, whatever async is set to).
- The patch keeps these cases covered (§3).

## 2. The cvar

```
REXCVAR_DEFINE_BOOL(d3d12_pipeline_creation_no_wait, false, "GPU/D3D12", "<help>")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
```

- **Name:** `d3d12_pipeline_creation_no_wait`.
  - It is defined in `pipeline_cache.cpp` right after `d3d12_pipeline_creation_threads` (L58-61). The two sort together.
  - The notes suggested `d3d12_async_pipeline_no_wait`. Renaming touches the define, two `REXCVAR_GET`s and two log strings.
- **Default:** false. Lifecycle `kRequiresRestart` (the same chain `d3d12_bindless` uses, command_processor.cpp:47-48).
- **Help text:** "Don't wait at the end of a submission for pipelines still being created: their draws stay skipped until ready (pop-in for a few frames instead of a stall; memexport and occlusion-query draws still wait). Needs async_shader_compilation, pipeline creation threads and bindless resources"
- **Latch.** At the end of `PipelineCache::Initialize`, after the creation threads exist:
  `creation_no_wait_ = cvar && async_shader_compilation && !creation_threads_.empty() && bindless_resources_used_`
  - When the latch is set, one INFO line: `d3d12_pipeline_creation_no_wait: not waiting for pipeline creation at the end of submissions; draws stay skipped until their pipeline is ready`
  - When the cvar is set but the latch isn't, one WARN line: `d3d12_pipeline_creation_no_wait ignored: it needs async_shader_compilation, pipeline creation threads and bindless resources`
  - When the cvar is false: no line.
- **Why latch, and why restart:** EndSubmission (which skips the wait) and IssueDraw (which never records a pending pipeline) must agree for the whole run. `async_shader_compilation` can change at runtime, so after Initialize the patch never reads it to decide ON or OFF.
- **Why bindless only:** see risk R6 in §7.

## 3. ON and OFF behaviour

| Where | OFF (default, same as today) | ON (latched) |
|---|---|---|
| IssueDraw drop check (#4) | `async && state == null` → drop. New: counts `kDroppedDraw`. | `(async \|\| no_wait) && state == null`. If the draw memexports or a host occlusion query is active: `AwaitPipelineCreation()`, timed as `kPipelineAwait`, then re-check. Still null → drop and count. |
| `PipelineCache::EndSubmission` (#9) | storage flush, then `AwaitPipelineCreation()`, which is old L795-814 verbatim | storage flush only. Queue and workers are left alone. |
| `CanEndSubmissionImmediately` (#5) | `!submission_open_ \|\| !IsCreatingPipelines()`, unchanged | true |
| `ShutdownShaderStorage` (#8) | unchanged | `AwaitPipelineCreation()` first |
| Log | slow-frame line has 3 more fields (#3) | the same, plus the INFO line once (#7) |

**`AwaitPipelineCreation()`** is today's EndSubmission wait block, moved out unchanged:
1. return if there are no creation threads;
2. drain the queue on the calling thread;
3. wait for the busy workers.

**The ON invariant: no draw is ever recorded with a null pipeline state.**
- IssueDraw keeps its drop check active even if `async_shader_compilation` is later turned off (`|| IsCreationNoWait()`).
- So the replay at L4299 never needs the wait.
- Side effect, ON only: a draw whose pipeline failed to create is also dropped when async is off. With OFF it is recorded without `SetPipelineState`, which is upstream behaviour.

**Differences from notes §10.3:**
- The `ShutdownShaderStorage` wait (#8) runs only with ON, so OFF is unchanged. With OFF the race it closes is pre-existing and narrow.
- #4 also forces a wait for memexport and in-query draws (§7). The notes listed those draws only as a risk.

### Why OFF is identical

`creation_no_wait_` is initialized to `false` in the class (#2) and only set when the cvar is true (#7). With it false:
- **#4 (IssueDraw):** `(async || false) && null` is the old condition, evaluated in the same order. When async is on, `IsCreationNoWait()` isn't even called. Inside the branch, `skip_draw` stays `true`, the guard is skipped, and the function returns `true` as before. The only addition is `frame_stats::Add`: two relaxed `fetch_add`s on atomics.
- **#9 (EndSubmission):** `AwaitPipelineCreation()` runs the old body unchanged. Its early `return` when `creation_threads_` is empty is the old `if (!creation_threads_.empty()) {...}`.
- **#5:** `!open || false || !creating` equals `!open || !creating`.
- **#8:** the new block is skipped.
- **#6 and #7:** the cvar is registered. The latch is false, and the `else if` logs only when the cvar is true.
- **#1, #2:** an inline getter, a public method and one `bool` member.
- **#10:** two ids before `kCount`. The only code that walks the counters loops to `kCount` (command_processor.cpp:269-275). Nothing stores counters by index.
- **#3** is the only visible change: three fields are appended to the slow-frame line. That line prints only when `slow_frame_log_ms` > 0 (default 0) and a frame exceeds it.

## 4. Thread safety

**The pipeline pointer, `Pipeline::state` (`std::atomic<ID3D12PipelineState*>`).** Each pipeline's pointer is written once with a release store, from null to its final value. It stays null if creation fails. The writers are:
- creation workers: pipeline_cache.cpp:3270 and 3272;
- the GPU thread, in `CreateQueuedPipelinesOnProcessorThread`: L3301 and L3305;
- the synchronous path in `ConfigurePipeline`: L1071;
- the storage loader when there are no threads: L677.

The reader is `GetD3D12PipelineByHandle`, an acquire load (pipeline_cache.h:101-103). It is used by the IssueDraw drop check and re-check, and again during the replay (`deferred_command_list.cpp:400`, `622`).
- Acquire/release guarantees that a non-null pointer refers to a fully created PSO.
- A pointer never goes back to null, so a draw that was non-null when recorded is non-null when replayed.
- ON relies on exactly this. No new atomics are needed.

**Root signature, `Pipeline::root_signature`.** It is stored at the miss with a release store (L1047). Once the PS is translated, the worker replaces it (L3226-3233). With bindless, `GetRootSignature` returns a fixed signature (command_processor.cpp:548-549), so it never changes. This is why the latch requires bindless (R6).

**Locks and events.** All already exist; the patch doesn't change them.
- `creation_request_lock_` guards `creation_queue_`, `creation_threads_busy_`, `creation_completion_set_event_` and `creation_threads_shutdown_from_`.
  - It also hands `pending_vertex_shader`/`pending_pixel_shader` from the GPU thread to the worker that pops the pipeline. They are written at L1060-1061, before the locked push. They are read after the locked pop, at L3209-3220.
- `creation_request_cond_` wakes the workers.
- `creation_completion_event_` (manual-reset): the waiter resets it under the lock. The worker that finds the queue empty, `busy == 0` and the flag set signals it (L3247-3252).
- `translation_request_lock_` serializes shader translation between the GPU thread (L959, L986) and the workers (L3185).

**The new flag, `creation_no_wait_`.** It is a plain `bool`.
- It is written once, at the end of `Initialize`, on the GPU thread (`SetupContext`).
- After that it is only read:
  - on the GPU thread by IssueDraw, EndSubmission, `CanEndSubmissionImmediately` and `ShutdownShaderStorage` (which reaches the GPU thread through `CallInThread`);
  - by another thread that runs `InitializeShaderStorage` while the command processor is paused (`src/graphics/graphics_system.cpp:378-382`). The pause handshake orders that read.
- Workers never read it.

**Who calls `AwaitPipelineCreation`.** Only the thread that drives pipeline creation: the GPU thread, or the thread acting for it while it is paused. Today's EndSubmission makes the same assumption, so there are never two waiters at once.
- **No deadlock:** at the forced wait in IssueDraw, the GPU thread holds none of the locks the workers take (`creation_request_lock_`, `translation_request_lock_`, `storage_write_request_lock_`, `compile_progress_mutex_`).
- The sync path (L958-1007, L1070-1071) already translates and creates pipelines on the GPU thread inside IssueDraw, so doing it there is nothing new.

## 5. Pending pipelines at each point

| Point | OFF | ON |
|---|---|---|
| End of a submission | drained and awaited (L795-814) | left queued or with the workers. They carry over. |
| Frame end (`IssueSwap` → `EndSubmission(true)`) | same as above | carry over across frames. Their draws stay dropped until each `state` is published. |
| A draw that memexports or is inside a query | dropped for the rest of the submission | forced drain-and-wait, then recorded. Dropped only if creation failed. |
| `InitializeShaderStorage` → `ShutdownShaderStorage` (L224) | no wait (pre-existing) | drained and awaited first (#8). The loader then starts with an empty queue, as it assumes at L689-690. No worker reads `shader_storage_file_`/`shader_storage_index_` unlocked (L3193-3195) while the shader queue is cleared (L761), the files are closed and nulled (L764-772), or the index is bumped (L346). |
| Storage-load tail (L683-716, when non-blocking or no extra threads) | awaited at the next EndSubmission | finishes in the background. At most a few draws are dropped for a few ms. |
| `Shutdown` (L172-220) | usually nothing pending, because the last EndSubmission waited | see below |
| Cache clear (`cache_clear_requested_`, command_processor.cpp:4333-4364) | pipelines and root signatures are not touched (L4356-4357) | same; nothing to do |
| Device removal | `BeginSubmission` fails before `ConfigurePipeline` (L2686). Creating on a removed device gives null, so the draw is dropped. | same. A pending pipeline that ends up null is just a dropped draw. |

**`Shutdown` with ON:**
- Each worker finishes the pipeline it holds and exits at its next loop check (`creation_threads_shutdown_from_ = 0` at L178; joined, then cleared at L184).
- Pipelines that never started keep a null state and are deleted with the rest. No recorded draw refers to them.
- Their descriptions were queued for the storage writer at the miss (L1074-1085), so the next boot creates them from storage.
- `ShutdownShaderStorage` runs at L189, after the threads are cleared, so the #8 wait returns immediately.

## 6. Counters

Two new ids in `src/graphics/frame_stats.h`, placed before `kCount` (#10):
- **`kDroppedDraw`** (count only).
  - Incremented in IssueDraw once per skipped draw, in both modes, after any forced wait, through `frame_stats::Add(kDroppedDraw, 0)`.
  - It includes draws whose pipeline failed to create.
  - This is the pop-in measure notes §10.3 asked for. Counting it doesn't change behaviour.
- **`kPipelineAwait`** (time and count).
  - A `frame_stats::Scope` around the forced wait in IssueDraw only, so it is always 0 with OFF.
  - Today's EndSubmission wait is deliberately not timed, to keep OFF unchanged. Timing it in both modes is a possible follow-up.
- **Reset:** on every swap, `ReportSlowFrame` (called from `IssueSwap`, command_processor.cpp:2224) exchanges all `kCount` counters to 0 (L269-275), whether or not the line prints.
- **Printed:** appended to the slow-frame line (#3, patched L296-298):
  `... | memexport full-buffer {}x (total {}) | dropped draws {} | forced pipeline waits {:.1f} ({}x)`
  The line has 28 placeholders and 28 arguments.
- **Parsers:**
  - In `build/agent6/attract-stalls/slowframe_join.py`, SLOW_RE matches only a prefix (up to "stalled"), so it is unaffected.
  - In `build/agent6/w6/log_diff.py`, the FULLBUF regex isn't anchored, so it is unaffected.
  - logdiff keys are number-normalized, so the new text makes one new key (§8).

## 7. Risks

### Draws that must not be skipped

| Draw class | What skipping it does | Today (OFF) | ON |
|---|---|---|---|
| **memexport** (`memexport_used`, L2684: the VS or PS writes `eM`) | **Corruption, not pop-in.** The guest reads stale exported data (GPU-written vertex or particle data, readbacks), and effects that feed later frames glitch. | dropped for the rest of the miss's submission | **waits** (forced drain-and-wait), then draws. Dropped only if creation failed. |
| **inside a host occlusion query** (`active_occlusion_query_.valid`: set at L5840, cleared at L4279 and L5852) | The query counts too few samples, so the game may hide or cull things (flares, visibility-based LOD). | dropped for the submission | **waits**, as above |
| **depth-only / no PS** | — | never pending: `use_async` needs a PS (L942-943), and the PS is nulled when it isn't needed (L2642-2643) | unchanged. Their synchronous creation stalls remain, as notes §10.3 item 5 says. |
| **alpha-tested depth prepass, shadow casters** (they have a PS) | pop-in: missing depth or shadows, transient | dropped for the submission | dropped until ready, so a multi-frame flicker. Not guarded. |
| **EDRAM resolve sources** (render-to-texture that `IssueCopy` later resolves) | If the pass runs only once, the texture stays **wrong until the game renders it again**, possibly for the whole scene. Examples: environment or reflection captures, UI and portrait render-to-textures, menu backgrounds captured once, luminance or exposure chains. | lost only if the pass falls in the miss's own submission | lost if the pass runs at any time while its pipeline is still being created (a multi-frame window). **Not guarded.** At draw time nothing says the target will be resolved, and a dropped draw can't be replayed. |
| **clears done with a draw** | stale contents for the drop window | one submission | several frames |

**How the diff handles these: option (a).** It forces a wait for memexport and in-query draws, and accepts pop-in for the rest. VS-only memexport passes (rasterization off, so no PS) are created synchronously and never pending in either mode. Depth-only query proxies usually have their PS nulled too. So the forced wait only affects such draws that keep a PS.

Alternatives:
- **(b) Drop the draw and set a flag so EndSubmission still waits.** This keeps today's one-submission loss for exactly the draws that corrupt state, at the same stall cost. Rejected.
- **(c) A per-pipeline wait.** Create just this pipeline on the GPU thread if it is still queued; otherwise wait for its worker. This needs a per-pipeline done flag or event, and a way to remove an entry from the `priority_queue`. It is the right follow-up if the full drain in (a) shows up in `forced pipeline waits`.
- **(d) Guard resolve sources.** This needs replay, or per-render-target tracking of "draws dropped since the last resolve". A cheap first step is a diagnostic: count resolves issued in a frame after a dropped draw. That measures the exposure before anyone trusts ON.

### Other risks

- **R1. The forced wait is a full drain.**
  - `AwaitPipelineCreation` creates everything queued and waits for every busy worker, not just the one pipeline. It costs the same as today's EndSubmission wait.
  - In scenes heavy on memexport or queries that hit new pipelines, the stall comes back. It shows as `forced pipeline waits` in the slow-frame line.
- **R2. A failed pipeline on a memexport or query draw.** Each such draw calls `AwaitPipelineCreation` again.
  - When nothing is pending it is cheap (two lock round-trips). While a burst is in flight it is a stall.
  - This should be rare: creation failures already log errors.
- **R3. Longer bursts and CPU contention.**
  - The GPU thread no longer helps drain at EndSubmission, so bursts run with one creation thread fewer. Bursts last longer, and so does the pop-in.
  - The workers run at normal priority and compete with the game's threads during bursts.
  - The compile notice (`GetCompileProgress`) stays up longer.
- **R4. Hunk #5 is optional.** With it, `CanEndSubmissionImmediately()` is true during bursts too.
  - `OnPrimaryBufferEnd` (`d3d12_submit_on_primary_buffer_end`, default true) then ends submissions during bursts as it does in the steady state. That means more, smaller submissions, and `held_pipelines` stays 0.
  - Pre-existing exposure: `OnPrimaryBufferEnd` doesn't check `active_occlusion_query_`. A guest query that spans a primary-buffer end is ended early (L4276-4280). #5 extends that from the steady state to bursts.
  - #5 is the last hunk and independent of the others, so it can be deleted. Notes §10.3 item 4: leaving it out is safe.
- **R5. Pre-existing races get wider windows.** Workers now stay active across EndSubmission.
  - `shader_storage_file_flush_needed_` is a plain bool. Workers set it (L3197) and the GPU thread clears it (L792). Losing a set only delays an fflush.
  - Workers read the storage pointer and index without a lock (L3193-3195). #8 covers the close and reopen path with ON.
- **R6. Bindful root signature (the reason for the bindless gate).**
  - With bindful resources, an async pipeline's root signature is first computed without the PS's bindings, then replaced by the worker (L3226-3233).
  - IssueDraw takes the root signature from `ConfigurePipeline` and only afterwards loads `state`. If the pipeline completes between those two loads, the draw is recorded with the stale root signature and the final PSO. That pairing is invalid: debug-layer error, possibly device removal.
  - The worker also calls the command processor's `GetRootSignature`, whose bindful map has no lock.
  - Both races exist today, but only within the miss's submission. ON would widen them to many frames.
  - Bindless (`d3d12_bindless`, default true) has neither race, so the latch requires it.
- **R7. Pop-in on first appearance.** The first 3D frame, load transitions and new areas lose draws for several frames instead of one submission.
- **R8. Untested.** Nothing has been built or run. Compile risk was checked by reading only:
  - the names used exist: `frame_stats::Add`/`Scope`, `active_occlusion_query_.valid`, `bindless_resources_used_`;
  - none of the new names collide;
  - BOOL `.lifecycle()` chaining and argument-less `REXGPU_INFO`/`REXGPU_WARN` calls are used elsewhere;
  - lines are at most 100 columns.

## 8. Test plan

Build one patched bin and use it for every arm. The base bin is only needed for row 1.
- Build it without hunk #5 (Agent 10 S1; §10 says which lines to drop). Without #5, `CanEndSubmissionImmediately()` stays false during bursts, as it does with OFF.
- Hunk #5 can become its own arm once row 2 is in.
- **Session 3 (M6, 2026-11-25):** staged as `s33-popin-nohunk5.patch` (sha256 57CFA8ADF1E90079…, apply check PASS in `APPLY-CHECK.txt`). Diagnostic (d) staged, unrated: `s33-diagd-on-nohunk5.patch`. The exact runs, arms and commands are in `TESTPLAN.md`, which supersedes this table where they differ (harness arms use `slow_frame_log_ms=1`; arm ids are alphanumeric for the w6 kit).

| # | Run | Pass | Watch for |
|---|---|---|---|
| 1 | Cvar off (patched) vs the S4b base bin, cold attract | The same code path (§3). Counters within noise. The same storage record sets. W/E/C 40/0/0. No `d3d12_pipeline_creation_no_wait` line. | With `slow_frame_log_ms` > 0, the slow-frame key changes (appended text): an ONLY/NEW key plus a GONE key against an unpatched ref. Expected; a NOTE only. |
| 2 | Cvar on, cold attract | The INFO line exactly once. Frames over 250 ms at the §8 scene points drop to the non-compile residue (PRE, heavy, fence-wait and depth-only frames). pm unchanged. `dropped draws` > 0 in frames after misses. `forced pipeline waits` ≈ 0. | `forced pipeline waits` > 0, meaning memexport or query pipelines in the burst. `dropped draws` long after a burst (a failed pipeline). Any DXGI or device-removed error. |
| 3 | Cvar on, the user on a visible desktop | The user judges the pop-in at the first 3D frame, the load transition and the 12.4k shot. Hidden-desktop runs can't judge this. | **Persistent** wrong textures (UI panels, reflections, portraits, minimap) mean a resolve source was lost (§7). If seen: stop and keep the cvar off. |
| 4 | Cvar on, route stopped during the 67-miss burst, 5 runs | Clean exit, no dump. | A hang in the `Shutdown` join; WER. |
| 5 | Cvar on, warm storage | Same as warm with the cvar off, apart from at most a few dropped draws right after the storage load. | — |
| 6 | Gate arms: cvar on with `d3d12_pipeline_creation_threads=0`, or `async_shader_compilation=false`, or `d3d12_bindless=false` | Exactly one WARN line, so W total is 41 (a NOTE). Otherwise row-1 behaviour. | — |
| 7 | Optional: cvar on with the D3D12 debug layer | No messages about root-signature/PSO mismatches or draws without a PSO. | R6-type messages. |

- Rows 1-5 are notes §10.3's table. Rows 6-7 are new.
- On the ON arms, use `slow_frame_log_ms=1` (or 17) to see the pop-in tail as per-frame `dropped draws`.
- Read `forced pipeline waits` by its ms, not its count (Agent 10 N2). The count includes cheap calls made with nothing pending, e.g. R2.

**logdiff with the w6 kit:**
- Use the patched cvar-off arm as `--ref`. The slow-frame text is then the same in every arm and only the counts move.
- MORE or GONE slow-frame keys between ON and OFF are the measurement, not a regression.
- The kit treats unknown lines as NEW/ONLY (a NOTE), so add these rules to the window's expect file:
  - ON arms: `exact` 1 for `d3d12_pipeline_creation_no_wait: not waiting for pipeline creation`;
  - OFF arms: `forbid` `d3d12_pipeline_creation_no_wait`;
  - gate arms: `exact` 1 for `d3d12_pipeline_creation_no_wait ignored`.
- Rule texts are matched after number normalization.
- **Agent 3's s4b kit** (`build/agent3/s4b/postcheck.ps1` / `s4b_check.py`; Agent 10 N3): if an ON or gate arm goes through it, add `d3d12_pipeline_creation_no_wait` to that row's `--allow-new`. Keep it unexpected for OFF arms.

## 9. Rollout

- **Opt-in only.** Default false, `kRequiresRestart`. The storage format doesn't change and nothing new is persisted. To revert, turn the cvar off and restart.
- Don't make it the default this round. Before recommending it, all of these need to hold:
  1. Row 1 shows identity in a window.
  2. Row 2 shows the stall gain.
  3. The user's row-3 review accepts the pop-in, with no persistent artifacts.
  4. Row 4 is clean.
  5. The resolve-after-drop diagnostic (d) has run on the ON arms and shows how big the exposure is (Agent 10 S2). It isn't needed for the opt-in test bin.
- Possible follow-ups:
  - the per-pipeline wait (c);
  - the resolve-after-drop diagnostic (d), which is now precondition 5;
  - timing the OFF-mode EndSubmission wait.

## 10. Agent 10 rating (2026-11-23, 07:24-07:36)

Agent 10 rated the files as staged at 06:47 (`build/agent10/t27/r33-popin.md`). The sha256 prefixes were: patch 0D23024484CCDEE1, DESIGN.md 611B62F510948253, CHECK.txt 43A4F21167FE5823.
- **OFF: SAFE.** The control flow is the same as at 5350b1d.
  - The only visible change is the 3 slow-frame fields.
  - Agent 10 checked 7 log parsers, and none anchors that line at its end.
- **ON, as an opt-in test: SAFE-IF**, under 4 conditions:
  1. the default stays false, with `kRequiresRestart`;
  2. row 1 shows identity first;
  3. the user's row-3 review gates any recommendation;
  4. the first bin leaves out hunk #5.
- No blocker.

**The items, and what was done (Agent 6, 07:37-07:40).** This round is docs only, per Agent 1 at 07:38. The rated `s33-popin.patch` is unchanged (sha256 0D23024484CCDEE1…).
- **S1 SHOULD: build the first test bin without hunk #5.**
  - Why: with #5, `OnPrimaryBufferEnd` (on by default) also ends submissions during bursts. That also ends any guest occlusion query that spans a primary-buffer end, which adds a second variable to rows 2 and 3.
  - How: delete patch L82-93, from the `@@ -4368,7 +4388,10 @@` line up to, but not including, the `diff --git a/src/graphics/d3d12/pipeline_cache.cpp` line. #5 is the last hunk in command_processor.cpp, so no other header changes.
  - Checked at 07:37: a copy without hunk #5 (and with N1's comment) passed `git apply --check` on 5350b1d, with exit 0 and no offsets. I withdrew the copy at 07:40 to keep this round docs-only; see `CHECK.txt`.
  - #5 can become its own arm once row 2 is in. §8 now says to build without it.
- **S2 SHOULD: run diagnostic (d) before #33 is suggested to anyone as a setting.** It's now precondition 5 in §9. It isn't needed for the opt-in test bin.
- **N1 NIT: state the threading rule in the header comment for `AwaitPipelineCreation()`** (patch L9-12).
  - Suggested text for the next edit of the patch: "Call it only from the thread that drives pipeline creation: the GPU thread, or the thread acting for it while the command processor is paused. Never from two threads at once: the completion event has one waiter."
  - Not applied, so the rated hash stays valid.
- **N2 NIT: `forced pipeline waits (Nx)` counts calls, not stalls.** Read-outs should use the ms. Added as a note in §8.
- **N3 NIT: Agent 3's s4b kit needs `--allow-new d3d12_pipeline_creation_no_wait` for the ON and gate arms.** Added as a note in §8.
- **N4 NIT: `build/agent2/PENDING-DIFFS.md` L39-40, L65 and L130 are out of date for #33 and #34.** That file is Agent 2's, so it isn't changed here.
