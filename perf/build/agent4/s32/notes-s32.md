### S3.2 hash=0 shader cache misses (N2, N3): cause and fix (task #12)

**Status (03:15): step 1 is done, on scratch copies only. It waits for Agent 10's rating, then Agent 1's GO for the live write (step 2). Live draw.cpp is still `50AA3B1D…`.**

Every run with `LEGO_NATIVE_PREPARE_THREADS=2` logs `Native GPU shader cache miss: hash=0x0000000000000000` (shader_archive.cpp:432). N2 logs about 760 lines/s. N3's rate goes up 4.7× at the light-to-heavy title switch, about 37 s after the first frame. N1 and n0 log none.

How it happens (line numbers from the live file):
1. The preparation paths capture shader bindings without the failed-bind check. N2 captures in CaptureParallelDraw (`CaptureShaderBindings()`, 5106). N3 captures in full preparation (`CaptureShaderBindings(vertex, pixel)`, 4944), once per frame for each shader pair.
2. Preparation runs under those bindings.
   - A worker's `PrepareDrawWork` installs them (`ShaderBindingsScope`, 1656) and calls `PrepareDrawGeometry` (1498) at 1667, unless the geometry is already done.
   - In N3, `CaptureDrawGeometry` (4654) also calls `PrepareDrawGeometry(work, true)` (4674). Each of its callers holds a scope over the same bindings (scope/call at 4718/4729, 4961/4962, 4974/4987 and 5120/5137).
3. `BoundShaderHash(kVertex)` is 0 when the captured vertex shader address is set but has no owner (`addresses[0] && !owners[0]`). Placement shaders that are missing from the AOT index are one example.
4. PrepareDrawGeometry then looks up hash 0 up to three times per draw, and every failed lookup warns.
   - The vertex-fetch planner looks it up first (`FindDxil`, 1533). No shader means no plan, so it falls back to `PrepareDrawGeometryLegacy` (1551 → 1293).
   - Legacy's input-usage lambda looks it up twice more (1368, 1380).
   - With the planner off, 1507 goes straight to Legacy.
   - Failed lookups aren't cached.
5. The recorder drops the same draw at 2713. `vertex_binding_failed` comes from `BoundShaderAddress` (2707-2708; shaders.cpp:682-686), on the same bindings. The serial path drops it in the same place, before its own geometry lookups (3108, 3120).

So the image doesn't change. The cost is wasted preparation and the log spam (about 760 lines/s). In long runs the spam also rotates game.log past its boot lines. This keeps th2's timing provisional and th3 out of the matrix.

**The fix** (approved by Agent 1 at 02:47 as task #12). The recorder's failed-bind test becomes the first statement of `PrepareDrawGeometry`, so a draw that the recorder will drop is never planned. 5 lines are inserted after 1498:

    // DispatchDraw drops a draw whose vertex shader failed to bind, so its geometry is never used.
    // Planning it anyway looks up hash 0 (one shader cache miss warning per lookup).
    bool vertex_binding_failed = false;
    BoundShaderAddress(ShaderStage::kVertex, &vertex_binding_failed);
    if (vertex_binding_failed) return false;

- **Where.** The first proposal put the test in Legacy's early return (1306). That misses the planner lookup at 1533, which runs before Legacy. The entry guard covers 1533, 1368 and 1380.
- **Same test, same bindings.** It is the recorder's own test (2707-2713). Every PrepareDrawGeometry call runs under a `ShaderBindingsScope` over the snapshot that the recorder installs later (4401 `head.shaders`, 4474 `work.shaders`, 5697 `work->shaders`). So exactly the draws the recorder drops skip preparation, and nothing that reaches the GPU changes.
- **Side effects, for failed-bind draws only.** `geometry_ready` stays false, as it does with the existing early returns (1520-1521, Legacy 1306). Then:
  - (a) PrepareDrawWork's `if (!work.geometry_ready)` (1667) runs the guard a second time, which costs two loads.
  - (b) The recorder takes the index metadata (2669-2670) from `InspectBufferResource` instead of the capture. That can only move the drop from 2713 to 2675, and both are drops. The barriers and framebuffer set between them (2691-2704) are per draw, and the next draw sets them again.
  - (c) Full-preparation template qualification sees `use_windows=false`, so it checks whole-buffer watches instead of window watches. That only decides whether a failed-bind capture becomes a template. Its repeats carry the same failed bindings and are dropped too.
  - The default serial path never calls PrepareDrawGeometry, so it is unchanged.
- **Not covered: vertex shader address 0.** Then `binding_failed` is false, so the guard lets the draw through.
  - The serial path drops such a draw at the null pipeline (2883-2895), before its geometry lookups. Its only record there is a long-probe event (`draw_pipeline_unavailable`), so n0's zero count doesn't show whether these draws exist.
  - If native3d's n2/n3 still log hash=0, these draws are the likely source.
  - Possible follow-up, not applied: `const u32 vs = BoundShaderAddress(...); if (vertex_binding_failed || !vs) return false;`. It is safe only if a VS-0 draw can never get a pipeline. `ResolveBoundShader` returns null without a resource (shaders.cpp:653-655), test_shader_binding_failures asserts `!ResolveBoundShader(kVertex, 0)`, and GetPipeline (1691) caches only pipelines it has built.

**Step 1 (03:00–03:12), on scratch copies only; live draw.cpp untouched.** Files are in `build/agent4/s32/`: `make_patch.py`, `compile_copy.ps1`, `static_check.py`, `run_checks.ps1`, `objdiff.py`, and the step logs. The scratch tree `build/agent4/s32tree/DimensionsRecomp/` holds 2,286 files, copied without junctions. Its draw.cpp is the patched copy; the other 183 gpu_native files are byte-identical to live. Everything ran with at most 2 threads, no ninja and no game.

| Check | Result |
|---|---|
| Live draw.cpp | `50AA3B1D…BDD6`, 306,221 B, 5,753 lines, CRLF, mtime 21:24:30 |
| Patched copy (`draw.cpp`) | `5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410`, 306,557 B, 5,758 lines, CRLF |
| Patch (`draw-s32.patch`) | `F54343258029F89A47BDBCC1392461B0B79686219A804A7FAE9473CF51852387`, 787 B. It has 1 hunk, `@@ -1496,6 +1496,11 @@`, +5/−0. `apply_check.py`: MATCH. `git -C DimensionsRecomp apply --check` on live: rc=0 (read-only) |
| Compile v3 / v2 (compile-one full `-c`, 1 thread, scratch tree) | exit 0 each, 77 warnings, 0 errors (same as batch 2). Objects: 2,038,469 / 2,023,089 B (`build/agent4/obj/s32-v3`, `s32-v2`) |
| Object diff against batch 2 (`objdiff.py`, output in `objdiff-v3.txt`/`objdiff-v2.txt`) | Of the 794 functions in `.text`, only `PrepareDrawGeometry` changed: v3 3,712 → 3,536 B, v2 3,760 → 3,584 B. No COMDAT section changed. `.rdata` +21 B is the longer source path (`build/agent4/s32tree/`) |
| Disassembly (v3) | The function now starts with `BoundShaderAddress(6, &flag)`, `cmpb $0`, then `xor eax` and return. Stage 6 is the same `kVertex` value as its existing `BoundShaderHash` call |
| `static_check.py` | OK: the guard is the first statement; the planner and Legacy lookups are reachable only after it; DispatchDraw's lookups come after its drop |
| Fixtures (run_fixtures; live tree, then scratch tree) | 9/26 on both, the same pass set as batch 2 (`compare_fixtures.py`: SAME) |
| State shadow (scratch tree) | OK, 20 runs, 19 audit checks |
| `run_patched.py --trees s32` | 3/3 PASS (constant_timing, query_retirement, query_sample_pool) |
| test_parallel_geometry (not one of the 26; it extracts PrepareDrawGeometry) | Fails on live and patched alike: `dev-assets/sdk-install/include` is missing. With `CPLUS_INCLUDE_PATH=<tree>/rexglue-sdk/include`: live has 16 errors (stale stubs); patched has the same 16 plus `undeclared identifier 'BoundShaderAddress'`. Whoever revives this fixture needs that stub |

**Next:**
- **Step 2, at Agent 1's GO after Agent 10 rates it SAFE:** a hash-guarded `WriteAllBytes` of live draw.cpp, `50AA3B1D…` → `5EA1F357…`; re-hash; log it in §S2.11; tell Agents 1, 2, 8 and 10.
- **Step 3:**
  - Agent 2 builds native3d-bin.
  - Agent 8 runs n0/n2/n3 as functional runs.
  - I check them with `check_n_rows.py`: expect no hash=0 and no new warning type.
  - th3 goes back into the matrix.

