# S5 1.2 rating: sync pipeline creation log (M2)

M10, 2026-11-25 ~17:32 local. Rates M2's debug cvar d3d12_log_sync_pipeline_creation, a diff to rexglue-sdk src/graphics/d3d12/pipeline_cache.cpp against SDK a7e79c0.

## Files

| file | sha256 (16) | bytes |
|---|---|---|
| build/agent2/s5/sync-log/sync-log.diff | A8CD7FEFD0A05E59 | 6068 |
| build/agent2/s5/sync-log/SYNC-LOG.md | 5CA7CD1F7C45AA87 | 3820 |
| build/agent2/s5/sync-log/check.py | 4C883E41FFB18CAA | 5738 |
| build/agent2/s5/sync-log/check.txt | 702F3FCE787C8EF9 | 1836 |
| build/agent2/s5/sync-log/compile.log | 4442D9F29C68DB82 | 13487 |
| obj d3d12__pipeline_cache.cpp.obj (check build) | E4C1413571D8D981 | 585922 |

Base: a7e79c0 blob C4CB51CC -> patched BEA5C260 (check.txt), both LF.

## Verdict

**Code SAFE. Diag bin SAFE-IF D1-D3.** With the cvar off, behaviour is the same as a7e79c0 apart from one predictable branch on the synchronous-creation path. The async path, the cache-hit path, the frame_stats accounting, the #33 no_wait logic and every header are untouched.

## What I checked

- **Scope:** one file and four hunks: `#include <chrono>`, the cvar definition, an anonymous-namespace counter block, the latch plus an INFO line in Initialize, and the timed sync branch. No header change, so B2 PCH reuse is unaffected and only d3d12__pipeline_cache.cpp.obj changes in the gpu leg.
- **Default:** `REXCVAR_DEFINE_BOOL(d3d12_log_sync_pipeline_creation, false, ...)` with `Lifecycle::kRequiresRestart`. It is latched once in PipelineCache::Initialize into a file-static bool, after the existing no_wait block and before `return true`. With the cvar off: no INFO line, no now() calls, no counters touched.
- **frame_stats unchanged:** in a7e79c0 the else branch (base L1114-1117) was `frame_stats::Scope create_scope(kPipelineCreate); state.store(CreateD3D12Pipeline(...));`. The diff wraps exactly those two statements in an inner block, so the Scope ends at the same point (nothing followed it in the else branch). The steady_clock timing sits outside the Scope and the log is emitted after it, so "pipeline create X (Nx)" in slow-frame lines is unchanged with the cvar on or off.
- **Reason string matches the real condition:** base L988 `use_async = async_shader_compilation && !creation_threads_.empty() && pixel_shader != nullptr`. The ternary tests async off, then no threads, then no pixel shader: the same order, and complete (the else branch is reached only when one of the three is false).
- **Field safety:** vertex_shader is dereferenced earlier in the function (non-null); pixel_shader is null-checked before ->shader(); hash, primitive_processing_result, normalized_depth_control, normalized_color_mask and bound_depth_and_color_render_target_bits are all in scope at that point; a failed creation prints "FAILED" instead of being dereferenced. fmt::format into a temporary std::string is fine.
- **Threading:** ConfigurePipeline's synchronous branch runs only on the GPU command thread, so the unlocked file-static counters are acceptable. Creation threads use CreateD3D12Pipeline from the async queue, not this branch.
- **Rate limit:** per steady-clock second, 32 lines. Suppressed creations still count in #n and total, and the suppressed count prints on the next logged line. Correct.
- **Check build:** check.txt reports git apply --check against the a7e79c0 index (tree untouched), plus fsyntax and compile with final2 gpu-leg flags + PCH: exit 0. The one -Wpessimizing-move warning already exists in base (shifted L120 -> L166). Both needles are in the obj.

## Conditions for the diag bin

- **D1:** build it as a separate bin dir (for example `devfinal2-synclog-bin`) with the rated final2 method: gpu leg only, this single TU changed, the CTL equal to the final2 reference except the TDS, pe-check exports unchanged. Keep the normal final2 flags, including the `-fmacro-prefix-map` that the check build dropped. Never write into or restage devfinal2-bin, nativefinal2-bin or any other pinned bin; record the new bin's MANIFEST sha.
- **D2:** runs with the cvar ON are attribution data only, not timing data. The INFO formatting and log write happen on the command thread inside the frame, so fps or frame-time numbers from those runs must not be compared with the timing windows.
- **D3:** one OFF smoke on the diag bin (the cvar unset) must show neither the "d3d12_log_sync_pipeline_creation:" Initialize line nor any "sync pipeline #" line. The ON run must show the Initialize line once, with the async/thread values.

## Findings

- NIT N1: the reason is re-evaluated at log time with a live `REXCVAR_GET(async_shader_compilation)`. base L183 notes that this cvar can change at runtime, so a change between L988 and the log would mislabel one line. This is negligible for a diag run with fixed cvars.
- NIT N2: the counters are file-static, not PipelineCache members, so they would carry over if a PipelineCache were ever re-created in one process. Harmless for this diagnostic.
- NIT N3: SYNC-LOG.md's prediction (8 "no pixel shader" lines of ~40 ms in slow frame #7366) is a fair falsifiable test. The read-out should say plainly that "no pixel shader" covers both depth-only and memexport-only draws, and the follow-up async-for-no-PS idea needs its own correctness rating.
