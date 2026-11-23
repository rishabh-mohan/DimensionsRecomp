# Session 2: subagent-sized jobs

Written by the orchestrator (Agent 1) at 16:45 on 2026-11-21. Read `SESSION2.md` first; its rules apply here too.

The orchestrator can't start subagents (the agy-grid hook blocks it), so each job below goes to a worker as a task with `subagents=N`. The worker may hand a whole job to a subagent, but it reviews the result before reporting `@@done`. Subagents follow the same rules as workers:

- Only write the files the task names.
- No git commands that change a repo.
- Stay within the CPU and disk limits below.
- Never write game data, or anything derived from it, into a git-tracked path.

Shared limits:

- **CPU:** at most 2 threads while Agent 2 is building. Ask the orchestrator before using more than about 2 CPU-minutes at once.
- **Disk:** about 23 GB free and falling. Estimate the size before writing more than 2 GB. Keep intermediates under `build/agentN/` so they can be deleted later.

---

## J1: Rebuild the native AOT shader pipeline (Agent 6, 2 subagents)

**Why this matters.** Agents 4 to 7 are optimising the native D3D12 renderer, which needs `-DLEGODIMENSIONS_NATIVE_GPU=ON`. That build depends on offline inputs that are not in the repo. Without them, the only build possible is the documented emulated-Xenos one (OFF), so no native-renderer change can be A/B tested in game. Agent 2 is building the OFF baseline first.

**Inputs the ON build is missing** (see `DimensionsRecomp/rexlego/CMakeLists.txt` lines 181 to 540):

1. **Temporal shader bank.** The `LEGO_TEMPORAL_SHADER_BANK` folder must contain `temporal-bank.obj` and `temporal-bank.cpp`. Produced by `tools/gpu-aot/build_temporal_shader_bank.py`.
2. **Float-blend-indices bank.** `rexlego/out/native-gpu/float-blend-indices-bank/*.obj` and `*.cpp`. Produced by `build_float_blend_indices_bank.py`.
3. **Instanced-constants bank.** Optional. If it is absent, instanced draws are disabled. Note in your report whether we can build it.
4. **FSR3.** Four pieces (CMakeLists lines 236 to 248):
   - Headers in `rexglue-sdk/thirdparty/FidelityFX-SDK/sdk/include`. That gitlink is not initialised yet and Agent 2 owns it, so ask Agent 2 to initialise it, or ask me to move the claim to you.
   - `rexglue-sdk/bin/ffx_sdk/ffx_backend_dx12_x64.lib`.
   - `rexglue-sdk/bin/ffx_sdk/ffx_fsr3upscaler_x64.lib`.
   - `amd_fidelityfx_dx12.dll`, which CMake looks for in `rexglue-sdk/bin`.

   The SDK's own optional FidelityFX fetch is `https://github.com/rexglue/FidelityFX-SDK.git` at `eee08db1688ac3d1275a70b728f4a8ba22914213` (see `rexglue-sdk/cmake/rexglue_fidelityfx.cmake` lines 50 to 55).
5. **RenderDoc header target.** Check what it needs; `renderdoc_app.h` is public.
6. **`rexlego/out/native-gpu/lego-dxil-cache.cpp`.** This is XenosRecomp's DXIL output for the shaders extracted from disc plus TU23 (`gpu-shader-extract inventory/extract`, see `README.md` lines 285 to 343). Run it with `XENOS_RECOMP_DXIL_ONLY=1`, and use the `gradient_compiler` target for both main and runtime containers.
7. **`lego-microcode-index.cpp`.** Built by the `lego_gpu_microcode_index` target, whose input path is hard-coded. Point it at our extraction without changing shipped behaviour; a CMake cache variable is fine.
8. **`runtime-cache.cpp`.** The original corpus of 255 runtime containers was captured privately in game. Plan for a stub or empty runtime cache, then capture runs: the native renderer records missing shaders as it runs. Expect black or partial output until those shaders exist.
9. **Prelink outputs.** `lego-linked-dxil-cache.cpp` and `runtime-linked-dxil-cache.cpp`. The prelink DXC must match the compiler's version; official DXC 1.9.2609 worked.
10. **DXC** in `research/reblue/thirdparty/XenosRecomp/thirdparty/dxc-bin`.

**Recipe** (`DimensionsRecomp/tools/gpu-aot/COLLABORATION.md` lines 212 to 343). Run these from `DimensionsRecomp/`:

- Clone `https://github.com/zolaware/reblue-XenosRecomp.git` into `research/reblue/thirdparty/XenosRecomp`.
- Check out `339af41df2c23dbe3256c1c377716b81a0e0fe6b`.
- Run `submodule update --init --recursive`.
- Apply `tools/gpu-aot/patches/xenosrecomp-lego.patch`.
- Run `python tools/gpu-aot/prepare_native_compiler.py research/reblue/thirdparty/XenosRecomp rexlego/out/native-gpu/current-compiler`.
- The compiler needs xxhash, zstd_static and fmt already built in `out/build/lego-release` (COLLABORATION.md line 333). Build them in your own build folder if you can; otherwise ask me.

For comparison, the original setup compiled 9,601 shaders from disc plus TU23 and prelinked 19,064 variants. `research/` is git-ignored in DimensionsRecomp. The shader banks, DXIL caches and extracted microcode are all derived from game data, so never commit them.

**Game data.** Read-only, from `game/` (Agent 3's extraction). Ask Agent 3 for the paths.

**Deliverables, in order:**

- **(a) Stubs first.** These are cheap, and they let Agent 2 run a NATIVE_GPU=ON configure in `build/dev` to produce the `compile_commands.json` that Agents 4 to 7 need. Session 1's `perf-notes/agent3-build.md` (lines 101 to 102 and section 1.4) gives the method: build an empty COFF object with `clang -c -x c NUL -o temporal-bank.obj` and pair it with a `.cpp` holding the declarations. Put the stubs under `rexlego/out/native-gpu/stubs/` and send Agent 2 the exact `-D` flags.
- **(b) Feasibility report within about 45 minutes**, in `perf-notes/agent6-native-aot.md`. Cover each missing input: how to produce it, CPU-time and disk estimates, and any blockers.
- **(c) The real inputs.** Banks, DXIL caches and FSR3 libs, staged where CMake expects them, plus the exact configure flags for Agent 2's native dev build.
- **(d) First native boot plan.** Include the capture runs for runtime shaders, and what the user will need to do in game, if anything.

---

## J2: Native CPU profile analyser (Agent 8, 1 subagent)

**The producer** is `rexlego/src/sample_profiler.cpp` (Agent 8's file):

- `LEGO_SAMPLE_PROFILE=1` starts the sampler thread.
- Recording toggles with F9, or with `LEGO_SAMPLE_PROFILE_TRIGGER` set to a file path: it records while that file exists and writes when the file is deleted.
- It samples every 1 ms or so by suspending threads, and unwinds up to 24 frames with RtlVirtualUnwind.
- It writes `profile-TICK.bin` next to the exe in format "LSP1", laid out as follows (check this against the source):
  - the 4 bytes `LSP1`;
  - u32 module count;
  - for each module: u64 base, u32 size, u32 name length, then the name bytes;
  - u64 sample count;
  - for each sample: u32 tid, u32 depth, then `u64 frames[depth]`.

**Symbols.** The exe links with `LINKER:/MAP:legodimensions.map` (rexlego/CMakeLists.txt lines 176 to 179). The path is relative, so the map lands in the build folder; Agent 2 will copy it next to every exe it stages.

**Write `DimensionsRecomp/tools/native-cpu/analyze_profile.py`** (Python 3.11 or later, standard library only):

- **Parsing.**
  - Parse LSP1.
  - Parse the lld-link map (Publics by Value: Address, Publics, Rva+Base, Lib:Object) into a sorted RVA table for `legodimensions.exe`.
  - Attribute every other address to its module (`rexruntime.dll`, drivers, system DLLs). For system DLLs, read the PE export table from disk to get names.
- **Guest code.** Keep the guest address of recompiled functions; check how `rexlego/generated` names them. Add an option to fold them all into one "guest" entry.
- **Waiting vs running.** Classify each sample by its leaf frame: ntdll `NtWait*` / `NtDelay*` / `NtRemoveIoCompletion*`, `NtUserGetMessage`, and so on. Report busy samples separately from waiting ones.
- **Reports:**
  - a per-thread table (samples, percent running, top functions);
  - top N by self time and by inclusive time;
  - `--by module`;
  - `--focus FUNC` (callers and callees);
  - category totals: guest, rexruntime, native-gpu, d3d12 plus driver, system, unknown;
  - `--folded` (folded stacks for flame graphs);
  - `--diff A.bin A.map B.bin B.map` (per-function delta, normalised to samples per second);
  - `--json`.
- **Self-test.** Build a tiny C++ target that compiles `sample_profiler.cpp` unchanged and has known hot functions. Use clang-cl and `lld-link /MAP` through `env/devshell.ps1`, with 1 thread. Run it with the trigger file, then check that at least 80% of busy samples land on the expected function.
  - Script: `tools/native-cpu/run_selftest.ps1`.
  - Outputs: `bench/agent8/profiler/` and `build/agent8/profiler/`.
- **Docs.** `tools/native-cpu/README.md`: how to capture (env vars, trigger file, where the `.bin` and `.map` files land) and example commands.

When it works, tell Agent 3 so the harness can add its `-Profile` switch, and tell me.

---

## J3: Global critical region map and cross-review (Agent 12, 1 subagent)

Agent 11's task #10, item 7, changes the kernel's global mutex (the global critical region). That is the riskiest change of the session: a mistake there causes deadlocks, races or guest-visible ordering changes. Build an independent safety net. Read-only, except for the files named below.

1. **Map** every acquisition site of the global critical region or global mutex: SDK kernel and xam code, threading, any path reachable from generated guest code, and rexlego. For each site, record what the lock protects (which data and invariants), whether it can be held across a guest callback, an APC, a wait or I/O, and how it nests with other locks.
2. **Write a checklist and stress tests** that any narrowing of the lock must pass: lock-order rules, recursion, waits while holding it, a thread terminating while holding it, and APC delivery. Put them in `perf-notes/agent12-gcr-map.md`. Small test programs may go in `bench/agent12/gcr/`.
3. **Review.** When Agent 11 posts `perf-notes/agent11-global-mutex-design.md`, review it against the map and write `perf-notes/agent12-gcr-review.md` with verdicts: safe, safe if changed in a stated way, or unsafe. Send Agent 11 and me a short summary.

---

## J4: Codegen cross-review (Agent 10, 1 subagent)

Agent 9 (task #8) is changing SDK codegen. A miscompile there is silent, and it affects the 720 or so generated translation units.

1. Read Agent 9's session-1 report, `perf-notes/agent9-codegen.md`, and each diff Agent 9 posts. For every change, check that PPC semantics are preserved: flags and CR/XER/FPSCR side effects, rounding, NaN handling, signed and unsigned edge cases, byte order, and memory ordering.
2. Design differential tests (old codegen against new on the same functions; ask Agent 9 to put them in `tests/ppc`, since Agent 9 owns that folder). List any change to headers that every generated unit includes: those force the 1 to 2 hour rebuild, so they are batched.
3. Write `perf-notes/agent10-codegen-review.md` with verdicts, and send Agent 9 and me a short summary each time a change is reviewed.
