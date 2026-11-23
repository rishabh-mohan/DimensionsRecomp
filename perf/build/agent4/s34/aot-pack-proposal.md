# Task #12 (b): AOT-pack proposal for placement VS 0xAC449538 / PS 0xAC448F28

Agent 4, 2026-11-22 ~06:05. **Proposal only.** There is no compile, build or apply tonight. Agent 1's gates are:

- Agent 7 checks the dumped PS words before anything is packed.
- The change alters the image, so it needs a native vs Xenos screenshot check, which goes on the later-window list.
- It is a content fix, so Agent 10's §15.1 items 1-5 apply, including the user's visual check.

## Why, and what changes

- **Cost.** In n-prof, `BindShader` takes 6.10 of 12.36 ms/f of render-thread CPU (49 %). The cause is that these two
  placement shaders miss the AOT index on every bind (Agent 7, `perf-notes/agent7-present.md` §3).
- **Image.** The draws that bind them are dropped today through `binding_failed` (draw.cpp:2712-2725). Packing them
  makes those draws render, **so the image changes**.
- **Root cause.** native3d-bin is built with the **stub runtime cache (0 shaders)**: `build/agent2/snap1-on/CMakeCache.txt`
  `LEGO_NATIVE_RUNTIME_SHADER_CACHE=…/rexlego/out/native-gpu/stubs/runtime-cache.cpp`. The capture→compile→index round
  for placement containers has never been run.
- **What fixes the cost.** Packing the shaders makes `FindShaderByMicrocode` hit, so binds register and stop
  repeating the full lookup. This also makes the (c) stopgap moot.

## Inputs (already captured: Agent 8's run `0509-sd-r1`, 05:09)

Directory: `build/agent8/matrix/20261122-0509/runs/0509-sd-r1/shader-dumps/` (9 files). Agent 7's check is in
`build/agent7/sd/shader-dump-check.txt`: dumped 9, failed 0, every container "container OK", and the raw and container
physical sections agree.

| File (`placement-containers/` unless noted) | Bytes | sha256/16 | Physical | First words | Pack? |
|---|---|---|---|---|---|
| `vs-ACAF01F01E1C03D2.bin`: **VS 0xAC449538** (backing 0xED23D3E0) | 1,304 | 6C4F65C3161DF6BE | 324 B | F2556004 600A1200 12000000 00006010 (= game.log words) | yes |
| `ps-75A4D1ABA62F7594.bin`: **PS 0xAC448F28** (backing 0xED23D540) | 1,716 | 09D05274AFBC26A2 | 208 B | words 0-11 zero, then constants | **after Agent 7's PS check** |
| `vs-CCD7655302B54D80.bin`: second placement VS (prefix 98D43959C65B882A) | 944 | F4EE30B28DEE9E4A | 288 B | 70956004 600A1200 12000000 00005010 | yes |
| `ps-E81FD692C3AB35E1.bin`: second placement PS | 1,640 | 58B4FA21E3550052 | 184 B | words zero at start | after Agent 7's check |
| `vs-A58EBA123EFB541C.bin` (top level): start-up VS (CreateShaderResource miss) | 704 | FD947EBF69C161EE | | 102A1111 … | optional |
| `ps-93B9F93B535E7CCA.bin` (top level): start-up PS | 156 | D63867294038BB52 | | 102A1100 … | optional |
| `placement-raw/*` (3 files) | | | | page-bounded raw reads, **not containers** | **never** |

**Open question for Agent 7.** Is a PS physical section that starts with 12 zero words real microcode, or a
partly-written copy? The stability run below gives the cross-check: the same container hash from a second boot.

## Path A (recommended): runtime cache plus index entry, no compiler changes

0. **Stability capture** (Agent 8's slot, functional, about 8 min). Use the same route as `0509-sd-r1` with
   `LEGO_DUMP_MISSING_SHADERS=<abs dir>` and `LEGO_NATIVE_TRACE_DIR=<abs dir>`. Run 1 had no trace dir, so the
   `missing_placement_shader_identity` events (container_hash/physical_hash) appear only in run 2.
   - **Pass:** the same 4 placement-container file names (the dedupe hash is the name) and identical bytes.
   - Note: with the dump on, the (c) cache is forced OFF, so (c) can't interfere.
1. **Stage the inputs** (scratch, for example `build/agent4/s35/runtime-input/`): the 4 placement containers, plus the
   2 start-up files if wanted.
2. **Compile** with Agent 6's tooling, ≤2 threads, about 2 min:
   `$env:XENOS_RECOMP_DXIL_ONLY='1'; $env:XENOS_RECOMP_HLSL_DUMP='build\agent4\s35\hlsl'; build\agent6\aot\gradient-build\gradient_compiler.exe build\agent4\s35\runtime-input build\agent4\s35\runtime-cache.cpp current-compiler\gradients\source\shader_common.h`
   - Confirm that the output contains the specialization variants the draws use: VS 0x1 (R11G11B10 normal) and PS 0x2
     (alpha test).
3. **Index.** Either rebuild it, about 12 s:
   `build\agent6\aot\microcode-index\lego_gpu_microcode_index.exe build\agent4\s35\lego-microcode-index.cpp <shader-assets> build\agent4\s35\runtime-input`
   or merge into the current index:
   `python DimensionsRecomp\tools\gpu-aot\merge_microcode_index.py <current index> <addition> <output> --report`.
   **Never write `rexlego/out/native-gpu` directly**; Agent 2 swaps the file in.
4. **Offline check** (no game):
   `python DimensionsRecomp\tools\gpu-aot\test_placement_capture_lookup.py <captures> <new index> <new cache> <out> [--main-cache]`.
   - Each captured container must resolve to a new index entry that has a compiled cache shader.
   - The old index must still resolve everything it resolved before (`--report` lists the added entries only).
5. **Agent 2:** run `python build\agent2\snap-native-inputs.py`, reconfigure with
   `-DLEGO_NATIVE_RUNTIME_SHADER_CACHE=<new runtime-cache.cpp>` and the new index, then do an incremental build. The
   result has a new fingerprint; stage it as the next native bin.
6. **Functional n-rows** (Agent 8): n0/n2/n3 checked with `check_n_rows.py` against the native3d rows. Pass rule:
   - `draw_missing_*` = 0, and no "missing from AOT index" or "unrecognized … resource" lines for the packed addresses;
   - draws/frame ≥ before (the dropped draws now render), with the other marks unchanged;
   - no new shader, PSO or hash=0 lines.

## Screenshot check (needed because the image changes)

- **Native:** set `LEGO_GPU_SNAPSHOT_DIR=<dir>` (device.cpp:2497-2571), with `LEGO_GPU_SNAPSHOT_TIME_WINDOWS=1` or
  `MANUAL_ONLY` plus `capture-next-frame`. Inspect with `inspect_gpu_snapshot.py <x.dds> --image`.
  - Take the same scene on native3d-bin (before) and on the new bin (after), so that the only difference is the new
    draws.
- **Xenos reference:** needs the user's visible desktop, so window 4 / the later-window list (Agent 1).
- **Pass:** the new geometry matches Xenos (placement, colour, alpha-test edges), and nothing else in the frame
  changes.

## Rollback

- Bin: native3d-bin stays staged (exe `B90DF683…`).
- Source: the stub cache plus the old index. The CMake `LEGO_NATIVE_SHADER_CACHE` keeps older caches
  (rexlego/CMakeLists.txt:264-266).

## Path B (LEGODX1 precompiled pack): blocked

- The COMMON header doesn't match.
- `XENOS_RECOMP_LEGO_NATIVE_SCALE` is never set.
- There is no provenance generator.
- Packs are fingerprint-bound.

Not worth it for 2-4 shaders.

## Effort and order

| Step | Who | Time | Machine |
|---|---|---|---|
| Stability capture | Agent 8 | about 8 min | game slot |
| PS-word check | Agent 7 | about 10 min | read-only |
| Compile, index, offline check | Agent 6 or Agent 4 (Agent 1 decides) | about 10 min | ≤2 threads |
| Build and stage | Agent 2 | about 5 min | builder |
| n-rows | Agent 8 | about 8 min | game slot |
| Screenshot check | user + Agent 8 | window 4 | visible desktop |

That is about 45 min of agent time, plus the window-4 screenshot.

**Recommendation:** pack all 4 placement containers in one round, since the second pair uses the same mechanism.
Add the 2 start-up files only if the offline check shows they resolve through this path.
