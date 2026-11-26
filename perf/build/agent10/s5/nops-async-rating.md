# Rating: M2 S5 Phase 2.1 nops-async (async creation of depth-only pipelines)

M10, 2026-11-25 ~18:15. Static review only (FREEZE: no compile, no run).

## Files

| File | sha256/16 | Bytes |
|---|---|---|
| build/agent2/s5/nops-async/nops-async.diff | AB149BE627194953 | 3681 |
| README.md | D8FA6DEB99CB43EF | 11478 |
| check.py | 9B7685094A3586D1 | 8771 |
| check.txt | CE64728E16ECFEC3 | 2598 |
| mkdiff.py | 6765DDDEDD310B7F | 1694 |
| base/pipeline_cache.cpp | C4CB51CC (git blob 8aae522 = a7e79c0 blob) | |
| ov/src/graphics/d3d12/pipeline_cache.cpp | CA7096E7 | |
| stk/src/graphics/d3d12/pipeline_cache.cpp | 9B92AAF9 | |

## Base

rexglue-sdk a7e79c0 (working tree at a7e79c0, no local changes in src/graphics/d3d12). Command processor read at a7e79c0.

## Verdict

- **Code: SAFE.** OFF is HEAD behaviour; the opt-in path is race-free and keeps the root signature final.
- **Test-only bin devs5nops-bin: SAFE-IF N1-N4.**
- The opt-in must not go into a pinned/timed/ship config yet (N4, S1).

## What I checked

1. **Diff integrity.** The +/- lines of `git diff --no-index base ov` equal the diff's (0 differences). The diff is LF only and touches one file. `ov` vs `stk` = exactly the sync-log hunks (rated 6968138A: chrono include, cvar, counters, Initialize line, timed else-branch). check.txt PASS (apply-check, both compose orders → 9B92AAF9, needles, kRequiresRestart, the latch's only use).
2. **Q1, OFF == HEAD: yes.**
   - With the cvar false, `async_depth_only_pipelines` is false. `create_async = use_async || (false && ...)` short-circuits to `use_async`. `use_async` (:988-989) is unchanged.
   - Initialize adds one REXCVAR_GET and logs nothing when off.
   - No header change, and no other line on the draw path changes.
3. **Q2, the e6407f3 hazard: impossible on this path.**
   - A no-PS draw still has `use_async == false`. So the VS is translated on the command thread under `translation_request_lock_` (:1004-1025), and an invalid VS returns false (:1026-1029) before anything is queued.
   - `GetCurrentStateDescription(..., use_async=false)` builds the root signature from the translated VS with `for_placeholder` false (:1360-1364). With PS null there is nothing left to rebuild.
   - On the worker, `PrepareRuntimeDescriptionForQueuedCreation`: `pending_vertex_shader` is already translated, so `translate_pending_shader` only returns `is_valid()` (:3230, :3252). `pending_pixel_shader` is null, so the root-signature rebuild (:3263-3280) is skipped, correctly.
   - Same shape as the storage replay path (:698-705), which already queues no-PS pipelines.
4. **Q3, race-free: yes.**
   - The latch is a file-static, written once in Initialize (after the creation threads start, but no thread reads it). It is read only in ConfigurePipeline on the command thread.
   - The worker never reads the latch. `pending_vertex_shader`/`pending_pixel_shader` are written before the push under `creation_request_lock_`, and the worker pops under the same lock (:3292-3311), so it sees them.
   - The VS translation is complete before the push. The worker's unlocked `is_translated()` read is the existing HEAD pattern.
   - Null-PS handling on the worker:
     - priority: z_write_enable (:1102-1103);
     - CreateD3D12Pipeline names and logs with VS only (:3114-3132);
     - a failed create stores nullptr (:3316/:3347), the same as the sync path's failure result.
5. **Q4, drops while pending, and the exclusions.**
   - IssueDraw (command_processor.cpp:2763-2779) drops a draw whose pipeline state is null when `async_shader_compilation` is on or in no-wait mode.
   - Default mode: EndSubmission (:4302) awaits all creation before `deferred_command_list_.Execute` (:4319). So a recorded draw never runs with an unresolved handle, even if `async_shader_compilation` is turned off at runtime mid-submission (the HEAD property, unchanged).
   - The memexport-VS exclusion is right and needed: in default mode there is no IssueDraw wait, so exported data would be lost. The ROV exclusion is conservative.
   - `kDisableRasterization` no-PS draws without memexport have no visible output, so dropping them is harmless.
   - **Not covered: occlusion queries in default mode** (S1). `occlusion_query_enable` defaults true (graphics/command_processor.cpp:94). The IssueDraw wait for `active_occlusion_query_.valid` exists only in no-wait mode (:2766). A depth-only query proxy that is dropped in default mode under-counts samples, and the guest may cull the object or flare.
     - HEAD already has this gap for pending PS pipelines. The opt-in widens it to the classic proxy shape.
     - A creation-time exclusion can't fix it, since the query state belongs to the draw, not the pipeline. The fix belongs in IssueDraw, outside this diff.
   - Depth pre-pass, shadow caster and stencil drops are pop-in. In default mode they last at most the rest of the submission; in no-wait mode, until the pipeline is ready (possibly several frames). That matches README §3.
6. **Q5, test plan (README §6): adequate for a smoke, with N2/N3 added.**
   - Good: the A/T split keeps the logging cost out of timing, and the checks are specific: Initialize lines, `ps none` sync lines to ~0, exit, dumps, `Failed to create graphics pipeline`, the #7601 segment.
   - Gap: cache state. If the pipeline storage already holds these no-PS pipelines, they come in through the storage path (already async) in both arms, and the A/B shows nothing. Each arm needs the same cold storage state (N2).
   - Gap: the no-wait pair is optional, yet it is where the full stall removal and the longest drops show (N3).
   - One run per arm is a smoke, not a perf result (S2).

## Conditions (test bin devs5nops-bin)

- **N1:** Build only after the window, with the FREEZE lifted, on the Overseer's GO.
  - First run `check.py --compile` (fsyntax + -c) on the stk TU 9B92AAF9 and require PASS.
  - Same method as devs5sync: final2 gpu leg, only this TU changes, `-fmacro-prefix-map` kept. pe-check exports NEW==REF; MANIFEST/verify-bins/BIN-PINS.
  - Pinned bins untouched.
- **N2:** The smoke kit gives every arm the same cold pipeline/shader storage state (fresh run dir or emptied cache dir, recorded in the kit log), and closes only its own PIDs.
- **N3:** Make N1/N2 (`d3d12_pipeline_creation_no_wait=true`) mandatory if any result is meant for the s33/no-wait config. Take the visual screenshots in N2 too, not only in T2.
- **N4:** The opt-in stays default false and test-only. It must not go into any pinned, timed or ship configuration until the user's visual review passes and S1 is resolved.

## Findings

- **S1 (SHOULD, before any promotion):** occlusion-query proxies dropped in default mode.
  - Fix option: extend the IssueDraw wait (command_processor.cpp:2766) to default mode when `active_occlusion_query_.valid`, at least for pending no-PS pipelines.
  - Alternative: show that the tested scenes issue no ZPD queries.
  - Until then, flares/coronas and pop-in of query-culled objects are the main visual watch item in T2/N2.
- **S2 (SHOULD):** treat the T1/T2 timing as a smoke. A perf claim needs the S5 matrix method (repeats, cold cache per run, gates).
- **n1 (NIT):** A file-static latch instead of a member, chosen to avoid a header change. Fine with one PipelineCache per process; Initialize rewrites it on re-init.
- **n2 (NIT):** In the stacked TU, sync-log's reason "no pixel shader" now means "no PS and (memexport VS or ROV or opt-in off)". The `memexport vs` and path fields disambiguate it; a clearer label would help.
- **n3 (NIT):** README §3's wait estimate (135-458 ms) is the right bound to report against. The new end-of-submission wait isn't in kPipelineAwait, so read it from frame time, as the README says.
