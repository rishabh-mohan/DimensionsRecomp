# nops-async: opt-in async creation of depth-only (no pixel shader) pipelines on Xenos

S5 Phase 2.1, M2. Staged only: nothing has been built yet. The fsyntax/compile check is deferred until the timed-window freeze is lifted.
Base: rexglue-sdk a7e79c0, `src/graphics/d3d12/pipeline_cache.cpp` (blob C4CB51CC…86C6).

| File | What |
|---|---|
| `nops-async.diff` | the change: 1 file, 3 hunks, +38/-1, LF |
| `ov/src/graphics/d3d12/pipeline_cache.cpp` | a7e79c0 + nops-async.diff |
| `stk/src/graphics/d3d12/pipeline_cache.cpp` | a7e79c0 + sync-log.diff + nops-async.diff: the TU for the test bin |
| `base/pipeline_cache.cpp` | the a7e79c0 blob |
| `mkdiff.py` | builds the diff from base/ and ov/, and checks LF and 100 columns |
| `check.py` | static checks (default) and `--compile` (fsyntax + -c, run after the freeze) |
| `check.txt` | static result |

## 1. The change

- **New cvar** `d3d12_async_depth_only_pipelines`: bool, default **false**, "GPU/D3D12", `kRequiresRestart`.
  - `PipelineCache::Initialize` latches it into a file-static, but only if there are creation threads.
  - When on, Initialize logs one INFO line: `d3d12_async_depth_only_pipelines: creating pipelines without a pixel shader on the creation threads (...)`.
  - When it is set but there are no creation threads, Initialize logs a WARN instead.
- **ConfigurePipeline**: `if (use_async)` becomes `if (create_async)`, where:
  ```cpp
  bool create_async =
      use_async || (async_depth_only_pipelines && pixel_shader == nullptr &&
                    REXCVAR_GET(async_shader_compilation) &&
                    !vertex_shader->shader().memexport_eM_written() &&
                    render_target_cache_.GetPath() == RenderTargetCache::Path::kHostRenderTargets);
  ```
  - `use_async` (:988-989) is unchanged. A no-PS draw still has `use_async == false`. So, exactly as at HEAD:
    - its VS is translated on the command thread (:1004-1029);
    - `GetCurrentStateDescription(..., for_placeholder=false)` builds the final root signature (:1360-1364).
  - Only the `CreateD3D12Pipeline` call moves. It used to run inline on the command thread (:1115-1118). Now the pipeline goes into the existing async block (:1097-1114), which already handles `pixel_shader == nullptr`: colour targets 0, depth write from `z_write_enable`, `pending_pixel_shader = nullptr`.
- **OFF == HEAD**: the latch is false, so `create_async == use_async` (short-circuit, nothing else is evaluated). No other line on the draw path changes. The header is unchanged, so this TU is the only one to rebuild (relink rexgpu-xenos.dll).

## 2. Why HEAD forces sync for no-PS draws

- **Where:** `pipeline_cache.cpp:988-989`, `use_async = async_shader_compilation && !creation_threads_.empty() && pixel_shader != nullptr`. The sync else-branch is :1115-1118.
- **git blame:** both come from **e6407f3** (Ryan Fisher, 2026-03-01, "graphics/d3d12: port backend pipeline and command runtime updates"). That commit changed 377 lines of pipeline_cache.cpp, and no comment explains the `pixel_shader != nullptr` term.
- **Before e6407f3** (`e6407f3~1`, ConfigurePipeline ~:979-987), *every* new pipeline, no-PS included, went to the creation threads whenever there were any (the Xenia behaviour). Both shaders were always translated on the command thread first.
- **e6407f3 added deferred translation:**
  - With `use_async`, the VS and PS are translated on the worker, in `PrepareRuntimeDescriptionForQueuedCreation` (:3219-3283).
  - The root signature is built from a placeholder (`for_placeholder`, :1360-1364).
  - The worker rebuilds the root signature **only in the `pending_pixel_shader` branch** (:3263-3280).
- **Inference** (undocumented, but it is the only thing that breaks): a no-PS pipeline with a deferred VS would keep a root signature built from the untranslated VS, and nothing would ever rebuild it. The term avoids that. As a side effect, it also turned off async *creation* for no-PS pipelines, which Xenia had and which is where the stall comes from.
- **The opt-in keeps that safety.** It doesn't defer translation for no-PS pipelines, so the root signature is final when the pipeline is queued.
- **HEAD already creates no-PS pipelines on the creation threads**, when it loads them from the pipeline storage (:698-705): same queue, same priority formula. Two existing pieces already handle a null PS:
  - `CreateD3D12Pipeline` (:3114-3132);
  - `PrepareRuntimeDescriptionForQueuedCreation` (`translate_pending_shader(nullptr)` returns true, :3227-3229).

## 3. A depth-only draw while its pipeline is pending

The draw is **dropped, with no placeholder**. See `command_processor.cpp:2759-2780` (a7e79c0): when `async_shader_compilation` is on (or no-wait mode) and `GetD3D12PipelineByHandle() == nullptr`, the draw counts as `kDroppedDraw` and returns. This is the same thing HEAD already does to pending pipelines that have a PS: frame #7601 had 137 dropped draws.

**How long the drops last:**
- **Default** (`d3d12_pipeline_creation_no_wait=false`, as in the sync smoke):
  - `EndSubmission` waits for every pipeline in creation (:834-835), so drops last at most the rest of that submission (about one frame).
  - The stall doesn't go away. It becomes a wait at the end of the submission on creates that run in parallel (3/4 of the logical cores, :170), overlapped with command-thread recording.
  - The 8 no-PS creates in #7601 total 458.5 ms on the command thread, and the largest is 135.1 ms. The new wait is therefore between about 135 ms and 458 ms, depending on how busy the threads are with the 59 other new pipelines of that frame.
  - This wait isn't counted in `kPipelineAwait`. Only the frame time shows it.
- **No-wait** (`d3d12_pipeline_creation_no_wait=true`, the s33 config):
  - There is no end-of-submission wait. Draws stay dropped until the pipeline is ready, which may take a few frames.
  - IssueDraw still waits (`kPipelineAwait`) for memexport and active-occlusion-query draws (:2766-2775). That applies to any pending pipeline, including the opt-in ones.

**Possible visible effects, for the frames while a pipeline is pending:**
- **Depth pre-pass draw missing.**
  - If the later colour draws use LEQUAL/LESS, they draw against a depth buffer without the pre-pass: extra overdraw, and maybe something behind shows through for a frame.
  - If they use EQUAL against the pre-pass depth, that object's colour fails the test and the object is missing for the frame.
  - Z-fighting isn't expected: nothing writes a slightly different depth.
- **Shadow-map caster draw missing:** the shadow from that caster is missing for the frame (shadow pop-in).
- **Stencil-only draw missing** (no PS, stencil write): wrong masking for that frame.
- **Occlusion-query proxy draw** (a typical depth-only draw inside a query):
  - In default mode it is dropped. The query counts fewer or no samples, so the guest may treat the object as occluded and cull it (or a lens flare/corona) for a frame or more.
  - HEAD already does this to pending PS draws in default mode, but depth-only boxes are the classic query proxy. **Watch item.**
  - In no-wait mode the existing IssueDraw wait covers it.
- **Hi-Z / EDRAM:**
  - The d3d12 backend keeps no separate Hi-Z state that a skipped draw could desync: `git grep -i hiz` in src/graphics/d3d12 finds nothing. The host GPU's own Hi-Z follows the depth buffer.
  - The render-target cache bind/ownership update happens before ConfigurePipeline (`GetLastUpdateBoundRenderTargets`, command_processor.cpp:2744-2747), so EDRAM ownership stays consistent. Only that draw's depth/stencil content is missing.

## 4. Memexport VS: excluded (it stays sync)

- A no-PS draw whose VS memexports is typically a stream-out/compute-like draw, often with rasterization disabled (:3103-3108). Its whole purpose is the data the guest reads back.
- In default mode, a pending pipeline is dropped without a wait (the IssueDraw wait is only in no-wait mode), so the exported data would be lost.
- The exclusion uses `vertex_shader->shader().memexport_eM_written()`: ucode analysis (:1001-1003), the same field the command processor reads (command_processor.cpp:2626).
- In the sync smoke this is 1 of the 45 creates. Draws that have a PS and memexport are unchanged (HEAD behaviour).
- **ROV is excluded too.** It is untested, and this game runs host render targets (all 45 smoke creates were host RT).

## 5. Composition with sync-log.diff and the test bin

- `nops-async.diff` applies to a7e79c0 on its own (`git apply --check --cached`).
- It composes with `../sync-log/sync-log.diff` in either order, and both orders give the same file: `stk/…/pipeline_cache.cpp` 9B92AAF9…AE9E, LF.
- **Test bin (after the freeze, on the Overseer's GO): `s5/devs5nops-bin`** = devs5sync-bin with the stacked TU.
  - Same method as devs5sync (final2 gpu leg, only this TU changed, `-fmacro-prefix-map` kept).
  - CTL = the reference except the TDS; pe-check exports NEW==REF; MANIFEST, verify-bins, BIN-PINS.
  - The pinned bins are never touched.
- With the opt-in on, sync-log still logs what stays sync on the command thread, under the reason "no pixel shader": only memexport-VS or ROV pipelines.

## 6. Test plan (after the window; the Overseer starts it via the waiter)

**Setup:** a `RUN-NOPS-SMOKE.cmd` kit modelled on RUN-SYNC-SMOKE: attract-long, ~240 s per arm, devs5nops-bin, unattended, it closes only its own PIDs.

| Arm | `d3d12_log_sync_pipeline_creation` | `d3d12_async_depth_only_pipelines` | Purpose |
|---|---|---|---|
| A1 | true | false | attribution baseline (= the sync-smoke on arm) |
| A2 | true | true | attribution with the opt-in |
| T1 | false | false | timing baseline |
| T2 | false | true | timing with the opt-in |
| (N1/N2, optional) | false | false / true, with `d3d12_pipeline_creation_no_wait=true` | the s33 config, where the full stall removal shows |

**Checks:**
- **Initialize lines:**
  - A2/T2: the `d3d12_async_depth_only_pipelines: creating …` line exactly once.
  - A1/T1: no such line.
  - A1/A2: the sync-log Initialize line once.
  - T1/T2: no sync-log Initialize line, and 0 `sync pipeline #` lines.
- **A2:** 0 `sync pipeline #` lines with `ps none`, `memexport vs 0` and host RT. Only memexport-VS lines may remain (expect about 1).
- **Every arm:** exit 0, 0 dumps, no new `Failed to create graphics pipeline` errors.
- **Timing (T2 vs T1, A2 vs A1 for the per-frame join):**
  - The slow frame of the segment (#7601 on / perf row 7545 off, about 945 ms) must no longer show `pipeline create … (8x)` on the command thread.
  - **Success:** the command-thread no-PS create time is about 0 ms in that segment. The frame time drops, by less than 458 ms in default mode (see section 3); the full gain is expected only in N2.
  - Report the dropped-draw counts and the worst frames.
- **Visual (user's review):**
  - Screenshots at the same attract points in T1 and T2: shadows, depth-tested geometry, flares/coronas (occlusion), stencil effects.
  - Any element that is missing or flickers only in T2 is a regression.

## 7. Risks

- **Dropped depth-only draws** (section 3). In default mode they last one submission at most. The occlusion-query proxy case is the main watch item.
- **Creation-thread contention:** depth-only pipelines now share the queue with the PS pipelines. In no-wait mode a depth-only pipeline can stay pending for more frames.
- **Off path:** byte-for-byte HEAD behaviour. The risk is confined to the opt-in.
