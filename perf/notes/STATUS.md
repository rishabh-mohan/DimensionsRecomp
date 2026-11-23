# Dimensions Recompiled perf work: status and resume plan

_Session 1, 2026-11-21, 11:50 to 12:45. Stopped early because the laptop battery was running out. All 11 worker reports are in._

## Where things stand
- **Repos:** both are clean, with no source edits this session.
  - `DimensionsRecomp` is on `perf/opt` at `127e04b` (tag `v0.2.0`, the final "Native GPU" release).
  - `DimensionsRecomp/rexglue-sdk` is a plain nested clone on `perf/opt` at `2897c31` (the v0.2.0 SDK pin).
- **Nothing has been built or measured yet.** The one exception is Agent 11's timer test (below). All other numbers in the reports are estimates from reading the code.
- **Toolchain:**
  - `env/devshell.ps1` is done and tested (VS 2022 x64, CMake 3.28.3, Ninja, jobs capped at 4).
  - The LLVM 23.1.6 download is **11.5%** done and can be resumed with `toolchain/segdl.ps1`.
  - The submodules are not initialized.
  - See [agent2-baseline.md](agent2-baseline.md).
- **Network:** about 70-90 KB/s, apparently because the agents' own API traffic fills the uplink. Next time, download LLVM (232 MB left) before starting the other agents, or use a faster network.
- **What needs the game:** profiling, PGO, and anything in the generated code need a build of the game. That covers the codegen options (Agent 9) and the guest helper headers (Agent 10). Building the game needs the user's **own** Xbox 360 dump plus Title Update 23, to run `rexglue codegen`. That question is still open with the user. Without it we can only run unit tests, microbenchmarks and compile checks.

## Decisions made this session
1. **Submodule init uses `--depth 1 --jobs 4`, with explicit paths.**
   - The SDK has a FidelityFX-SDK gitlink that has no `.gitmodules` entry; see Agent 2's report.
   - If a submodule can't fetch its pin shallowly, retry only that one without `--depth`.
2. **Redundant D3D12 state calls (Agent 4 §1.3) can be dropped** if the GPU-visible state at every draw stays identical.
   - The shadow state must be invalidated when a command list begins or resets, when the root signature changes and on `SetDescriptorHeaps`.
   - Measure the redundancy ratio first (`LEGO_NATIVE_STATE_CALLS=1`).
   - Ship behind a toggle that is OFF by default, until a PIX or RenderDoc capture diff and the debug layer show no difference.
3. **Baseline correction to BRIEF.md.**
   - The game exe ships at **x86-64-v3** (`rexlego/CMakeLists.txt:840`). The SDK defaults to v2 (`rexglue-sdk/CMakeLists.txt:71`).
   - The AVX2 code in draw.cpp (`SnapshotDevice` :3741, `SnapshotDrawDevice` :3792) is consistent with the shipped default. However, it breaks the documented `-DLEGODIMENSIONS_X86_BASELINE=x86-64-v2` build. Low priority fix: an `#ifdef __AVX2__` fallback.
   - Do not change the shipped defaults.
4. **`skip_msr` stays OFF**, because it removes the global-lock emulation (Agent 9).
   - Agent 8's removal of the lock_elide fences (§1.1) needs a written memory-model argument plus litmus tests, and stays OFF by default.
   - Agent 9's register-localization work goes first.
5. **The log-only difference is accepted:** the draw log-throttle counter no longer re-prints after 2^32 draws (Agent 4 §1.5).

## Top items across all areas (suggested order next session)
| # | Item | Owner report | Why first |
|---|---|---|---|
| 1 | **Host timer resolution stuck at 15.6 ms.** Guest `Sleep(1)` measured **15.0 ms** median vs 2.6 ms with a high-res timer. Fix: `timeBeginPeriod(1)`, high-res waitable timers and the EcoQoS timer-resolution opt-out. | [agent11-kernel.md](agent11-kernel.md) #1-2 | The only measured finding. Likely affects pacing and stalls; low risk. |
| 2 | **No-code checks on the laptop:** which GPU the game uses (MX570 vs Iris Xe), and an A/B test with `LEGO_NATIVE_COMMAND_SLOTS=12`. | [agent7-present.md](agent7-present.md) "Quick checks" | 5 minutes once the game runs, and possibly the biggest win. |
| 3 | **PSO autosave holds the library mutex** across a serialize of up to 512 MiB. Plus instrumentation. | [agent6-pipelines.md](agent6-pipelines.md) #1, #8 | Stutter fix; on by default today, low risk. |
| 4 | **The frame ring counts submissions, not frames.** Also, guest fence and idle waits drain the whole GPU. | [agent7-present.md](agent7-present.md) #1-2 | The render thread spends about 16% of its time in `WaitForSubmissionLocked` (upstream notes). |
| 5 | **Per-draw overhead:** log-throttle atomics, diagnostics that cost more than one branch when off, 56 TLS accessors, and a QueryDrawScope mutex plus an O(n) walk per draw. | [agent4-draw-path.md](agent4-draw-path.md) do-first order 5→6→4→1 | Behaviour-identical; no game needed for compile checks. |
| 6 | **Loading:** `ReadScatter` does a host read, 2 heap lookups and a global lock for **every 4 KB page**. Physical-memory reads always take the global lock. | [agent12-io-memory.md](agent12-io-memory.md) #1, #4 | Loading time; testable with synthetic files. |
| 7 | **Global recursive mutex:** handle lookups and every Ke* dispatcher call take it (twice for the dispatcher). | agent12 #2 + agent11 #5 | Needs a joint owner (cross-claim). |
| 8 | **Register localization:** the biggest codegen lever. `skip_lr` can be enabled now; the `*_as_local` options need a per-function fallback for 7 interior `body=` entries. | [agent9-codegen.md](agent9-codegen.md) #1 | Large CPU win, but needs the game files to regenerate the code. |
| 9 | **Texture uploads:** an SSSE3 run-based untile for RGBA8, R8, RG8 and R5G6B5; staging zero-fills; byte swaps. | [agent5-uploads.md](agent5-uploads.md) #1, #3, #4 | Differential tests are possible without the game. |
| 10 | **Guest helpers:** `vslo`/`vsro` LUT shuffle and SSE4.1 variable shifts. Also elide redundant `REX_SET_FLUSH_MODE` at 77 sites (with Agent 9). | [agent10-helpers.md](agent10-helpers.md) #1-4 | Equivalence tests are possible; the gain shows only in game. |

## Per-area summary (details, diffs, risks and verify plans are in each report)
- **Agent 2, toolchain:** [agent2-baseline.md](agent2-baseline.md).
  - The SDK needs Clang ≥ 18.
  - SDK outputs always land in `rexglue-sdk/out/win-amd64/<Config>/` regardless of `-B`, so only one agent may link SDK targets at a time.
  - `REXGLUE_BUILD_TESTS=ON` is needed for the tests.
  - The resume commands are in §"Resume plan".
- **Agent 3, build:** [agent3-build.md](agent3-build.md).
  - The design for the stubbed `rexlego/generated/` harness is §1; implement it first. A draft `harness/check-rexlego.ps1` exists; it parses but has never been run.
  - Proposals:
    - a v3/CPUID launcher variant;
    - `-ffp-contract=off`;
    - a Release debug-info trim;
    - PGO `OFF|GEN|USE`;
    - a ThinLTO lld fix;
    - ICF.
  - `LEGODIMENSIONS_NATIVE_GPU` defaults to OFF but 0.2.0 ships as Native GPU, so both configs must compile.
- **Agent 4, draw path:** [agent4-draw-path.md](agent4-draw-path.md). It has 6 default-path items and 13 threaded-path items (those apply only with `LEGO_NATIVE_THREADED=1`). Registry lookups use 2 locked RMWs each; fixing that needs the textures.cpp owner. Inlining `CurrentDrawPreparation()` needs the device.cpp owner.
- **Agent 5, uploads:** [agent5-uploads.md](agent5-uploads.md). Every texture upload creates a new committed UPLOAD buffer. Pooling them is the riskiest item, so do it last.
- **Agent 6, pipelines:** [agent6-pipelines.md](agent6-pipelines.md).
  - There is no runtime DXC; everything is prelinked.
  - Synchronous PSO compiles on a miss are the cause of the "FPS improves the longer you play" symptom. An opt-in async compile with a skip-draw fallback is the biggest stutter win; keep it OFF by default.
  - Library loads are serialized behind one mutex; any concurrency change must be gated.
  - Startup `Prepare()` is single-threaded.
- **Agent 7, present:** [agent7-present.md](agent7-present.md).
  - The frame-latency waitable is unused.
  - The limiter busy-spins under the recording lock.
  - The gamma pass runs even for an identity ramp.
  - The whole back buffer is cleared every present.
  - Win32 queries run on every present under `g_mutex`.
  - Plume isn't checked out, so the swap-chain flags and adapter selection are unverified.
- **Agent 8, runtime:** [agent8-runtime.md](agent8-runtime.md), [agent8-runtime-diag.md](agent8-runtime-diag.md), [agent8-runtime-features.md](agent8-runtime-features.md).
  - `native_scene_diagnostics` is ON by default in the Native GPU build: a spinlock plus an atomic on every guest alloc and free. Changing the default needs owner sign-off.
  - The cheat menu rescans up to 64 MiB per frame while it is open.
  - The Discord thread wakes 10 times a second and the cheat freeze thread 20 times a second.
  - The slow first Toy Pad placement is not caused by `toypad_app.cpp`.
- **Agent 9, codegen:** [agent9-codegen.md](agent9-codegen.md).
  - CR compare does 4 byte stores plus an XER.SO load per compare.
  - XER.CA is computed eagerly.
  - The `rlwinm` lowering can be proven correct with an exhaustive test, so it can be default ON.
  - MXCSR flush-mode churn.
  - `musttail`.
  - VMX scalar fallbacks.
- **Agent 10, helpers:** [agent10-helpers.md](agent10-helpers.md). It ranks 7 helper changes, and its "Bugs noticed" section lists non-perf issues.
- **Agent 11, kernel:** [agent11-kernel.md](agent11-kernel.md).
  - Wait timeouts are truncated, and absolute timeouts become 0. The fix is in xobject.cpp and needs a claim.
  - Contended `RtlEnterCriticalSection` never spins.
  - The spinlock calls `SwitchToThread` on every failed CAS.
  - `Win32Timer` is not high-res.
  - The clock takes a mutex.
  - There is a TLS bounds bug.
- **Agent 12, I/O and memory:** [agent12-io-memory.md](agent12-io-memory.md).
  - A disabled log call still pays for a guarded static, an out-of-line call and a bounds check before the level test.
  - Opening a file costs an extra stat.
  - Reads of the same file are serialized twice.
  - xmemory large-range operations are fine.

## Cross-owner work to assign explicitly next time
- Agent 11 needs `src/system/xobject.cpp` (wait timeouts), and Agent 12 needs `kernel_state` handle locking. Both are in the global recursive mutex area, so give it to one owner.
- Agent 4 needs the textures.cpp owner (Agent 5) for the registry RMWs, and the device.cpp owner (Agent 7) for the inline accessor.
- `REX_SET_FLUSH_MODE` elision is codegen work (Agent 9), not helpers (Agent 10).

## How to resume
1. **Agent 2, alone on the network first:**
   1. Resume the LLVM download, then extract it and rename it to `toolchain/llvm-23.1.6`.
   2. `. env/devshell.ps1`.
   3. Init the submodules (shallow, explicit paths).
   4. SDK Release build plus tests: preset `win-amd64`, `-B build/sdk`, `-DREXGLUE_BUILD_TESTS=ON`.
   5. Write `env/compile-one.ps1`.
   6. Run the gpu-aot portable checks.
   
   The exact commands are in [agent2-baseline.md](agent2-baseline.md) §"Resume plan".
2. **Agent 3:** implement the harness from §1 of its report.
3. **Owners:** implement the low-risk items in the order above. Each change needs a bench in `bench/agentN` (median of at least 5 runs) and the existing tests passing. Anything risky stays OFF by default.
4. **With the user's game dump plus TU23** (if confirmed):
   - codegen plus a full build;
   - Agent 7's quick checks;
   - a profile;
   - then the codegen options, PGO and the async PSO option.
