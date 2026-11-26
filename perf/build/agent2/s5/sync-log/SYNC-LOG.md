# S5 1.2: sync-pipeline creation log (M2, 2026-11-25)

The diff is `sync-log.diff` (sha256 A8CD7FEF), +90/-2 lines. It touches only `rexglue-sdk/src/graphics/d3d12/pipeline_cache.cpp`, against a7e79c0. Base blob C4CB51CC, patched file BEA5C260; both are LF.

Run `check.py` to regenerate the diff and repeat the checks. Its output is in `check.txt`.

## What it adds

**New cvar.** `d3d12_log_sync_pipeline_creation` is a bool in GPU/D3D12, default **false**, `Lifecycle::kRequiresRestart`. It is latched once in `PipelineCache::Initialize`, which logs one INFO line when it is on.

**Where it logs.** In `ConfigurePipeline`'s non-async branch (a7e79c0 :1115-1118). This is the only place where `frame_stats::kPipelineCreate` (the slow-frame field "pipeline create X (Nx)") is counted. Each synchronous `CreateD3D12Pipeline` there is timed separately with steady_clock, so the frame_stats Scope is unchanged. Each one logs:

```
sync pipeline #<n> <description hash>: <ms> ms (<reason>) | vs <ucode hash> (host type <HostVertexShaderType>) ps <hash|none> |
memexport vs <eM mask> ps <eM mask> | <host render targets | ROV (EDRAM in the pixel shader)> | rt bits <bound depth+color bits>
color mask <normalized> z <enable> write <z_write> | prim <host PrimitiveType> | ok|FAILED | total <ms>, <n> lines suppressed
```

- **reason:** why the creation was not async. It is one of `async_shader_compilation off`, `no creation threads` or `no pixel shader`. The last is the a7e79c0 :988-989 condition `pixel_shader != nullptr`.
- **Rate limit:** at most 32 lines per steady-clock second. Suppressed creations are still counted in `#n` and `total`, and the suppressed count is printed on the next line that gets through.
- **Threading:** the state is a set of file-static counters, with no locks, because only the command thread creates pipelines synchronously. There is no header change, so PCH reuse (B2) stays valid and only this TU recompiles.
- **Cost when off:** one predictable branch per synchronous creation. The async path and the cache-hit path are untouched.

## Checks

| check | result |
|---|---|
| SDK HEAD == a7e79c0, index clean | PASS |
| `git apply --check --cached` vs the a7e79c0 index (working tree and index not touched) | PASS |
| `clang -fsyntax-only`, final2 gpu-leg flags + PCH | PASS. 0 errors; 1 warning, which already exists in base (:120 → :166 `-Wpessimizing-move`, depth_only_pixel_shader_) |
| `clang -c` to `obj/d3d12__pipeline_cache.cpp.obj` (Idle priority) | PASS, 585922 B, E4C14135. Needles `d3d12_log_sync_pipeline_creation` and `sync pipeline #{} {:016X}` present |

## How it explains game.2.log:7573

The target is `build/agent3/runs/20261125-095932-s33-onsf/game.2.log`, slow frame #7366: 504.7 ms. It reads `pipeline create 322.0 (8x), new 67`, `shader translate 3.2 (7x)` and `dropped draws 141`.

- `new 67` counts pipeline misses, async ones included. The 141 dropped draws are draws whose async pipelines were not ready yet.
- With async and creation threads on, only draws **without a pixel shader** reach the synchronous branch (:988-989). Their vertex shaders are also translated synchronously (:1004 `!use_async`), which matches `translate 7x`.
- The prediction: with the cvar on, that frame shows 8 lines with reason `no pixel shader` and about 40 ms each. They would be depth-only or memexport draws; the log gives the memexport and RT-path fields.
- If any line shows another reason, or a pixel shader present, the hypothesis is wrong.

A follow-up option, not in this diff: allow async creation for no-PS draws that do not memexport. That needs a correctness review, because skipping depth-only draws breaks later depth testing.

A run needs `--d3d12_log_sync_pipeline_creation=true` on a bin that contains this diff. No bin has been built; M10 rates the diff first.
