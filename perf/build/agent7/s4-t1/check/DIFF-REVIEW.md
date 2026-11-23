# DIFF-REVIEW: S4-T1 (#21) LEGO_NATIVE_CHAIN_PRIORITY

> **Addendum by Agent 7 (22:50): diff revision 2 fixes S1 with option (a).**
> - native_preparation.h now holds `inline void (*g_native_chain_priority)(const char* role) = nullptr;` and an inline
>   `ApplyNativeChainPriority` that calls the hook only when it is set (after :15-22).
> - native_worker.cpp defines `static void ApplyNativeChainPriorityImpl` and installs the hook from a namespace-scope
>   initializer (after :333-369).
> - make_s4t1.py PROOF 6 checks the link closure. The new hashes are in SHA256SUMS.txt.
> - Line numbers below are from revision 1. Revision 2 mapping:
>   - native_preparation.h: :15-18 → :15-22, and :31 → :35;
>   - native_worker.cpp: :332-361 → :333-369 (Impl :337, installer :366-369); every line after :361 moves by +7
>     (:373 → :380, :383 → :390);
>   - lines before :332 and all of native_recording.cpp are unchanged.
> - N1-N6 still apply.
> - Agent 7 (23:26), after Agent 9's pre-read P1: the in-text cites of the creator's `SetThreadPriority` (:383) now
>   carry the rev-2 number (:390). N2's :360 (`GetThreadPriority(self)`) is already the rev-2 line.

**Verdict: no BLOCKER for the legodimensions / native4b build. One SHOULD-FIX: the offline gpu-aot fixtures that link
native_recording.cpp (or native_preparation.h) without native_worker.cpp will fail with LNK2019 on the new symbol. The
rest is NITs.**

Checker: Agent 7's read-only checker, 2026-11-22 ~22:45 local. Nothing was compiled or run.

Inputs:
- `build/agent7/s4-t1/s4-t1.diff`
- `before/` and `after/` under `build/agent7/s4-t1/`
- `SHA256SUMS.txt`
- the snapshot `build/agent2/snap1/DimensionsRecomp/rexlego/` (opened by explicit path)

I verified everything independently with my own script, `check/verify_diff.py` (python -B, stdlib, BelowNormal), and
did not rely on make_s4t1.py.

## Ranked findings

### BLOCKER
None.

### SHOULD-FIX
**S1. The offline fixtures lose their link closure (ODR / link, check 5).**

- `ApplyNativeChainPriority` is declared in `native_preparation.h:15-17` and called from the inline
  `NativePreparationQueue::Run` (`native_preparation.h:31`) and from `RecordingQueue::Run`
  (`native_recording.cpp:113`). It is defined only in `native_worker.cpp:337-361`.
- Every standalone build that compiles native_recording.cpp, or instantiates NativePreparationQueue, without
  native_worker.cpp now fails with `LNK2019: unresolved external symbol legodimensions::gpu_native::ApplyNativeChainPriority(const char*)`.
- Affected fixtures (DimensionsRecomp/tools/gpu-aot):
  - These compile `rexlego/src/gpu_native/native_recording.cpp` + fixture with clang-cl:
    `test_draw_preparation_gpu.py:25`, `test_geometry_content_gpu.py:32`, `test_geometry_content_sdk_gpu.py:71`,
    `test_graphics_shader_reads_gpu.py:41`, `test_texture_depth_publication_gpu.py:38`,
    `test_vertex_texture_read_gpu.py:22`.
  - `test_texture_upload_publication_gpu.py:35-39` compiles an instrumented copy of native_recording.cpp.
  - `test_draw_preparation_gpu.cpp:122/202` calls `PostNativePreparation`, so the queue ctor and Run are definitely
    live there.
  - `test_native_preparation.cpp:2,14` constructs `NativePreparationQueue queue(3)` directly. I found no runner for it
    in tools/gpu-aot.
- These fixtures already hand-stub other out-of-TU symbols (e.g. `test_geometry_content_gpu.cpp:53`
  `bool NativeTextureTimingEnabled(){return true;}`), but none stubs the new symbol.
- **Not affected:**
  - legodimensions: it compiles both native_worker.cpp and native_recording.cpp (snapshot CMakeLists.txt:108-109).
  - The CMake tool targets at L406-440 (lego_gpu_microcode_index / lego_gpu_prelink / lego_gpu_prelink_runtime)
    compile neither TU and do not include native_preparation.h.
  - `test_temporal_worker.py:12-31` should still build. It compiles the real native_worker.cpp with a stub
    `rex/logging.h` (`#define REXLOG_INFO(...) ((void)0)`). The new include resolves to the real
    native_preparation.h, and the definition is in the same TU.
  - The `LEGO_NATIVE_WORKER_STUB` fixtures include only native_worker.h.
- Impact: this becomes a BLOCKER only if an S4-T1 acceptance row re-runs one of those fixtures against the after
  tree.
- Fix options, smallest scope first:
  - (a) Keep native_preparation.h link-free and stay within the same 3 files. Add a hook in the header,
    `inline void (*g_native_chain_priority)(const char*) = nullptr;`, and call it as
    `if (auto f = g_native_chain_priority) f("prepare");`. native_worker.cpp sets the hook with a namespace-scope
    initializer, which runs before any chain thread exists. Fixtures then get a no-op.
  - (b) Add a one-line stub `void ApplyNativeChainPriority(const char*) {}` to each affected fixture. This touches
    tools/ and is outside the 3-file scope.
  - Moving the definition into native_recording.cpp is not a good option: the fixtures have no rex include path, so
    REXLOG would not be available there.

### NIT
- **N1. Value 1 is a no-op for the worker/coordinator thread.**
  - The untouched creator-side `SetThreadPriority(g_thread.native_handle(), THREAD_PRIORITY_ABOVE_NORMAL)` (before
    :349, after :383, rev 2 :390) already raises that thread in every threaded mode.
  - So `=1/3` raises only RecorderMain (th3), the RecordingQueue thread (th2) and the 2 prepare threads.
  - Read the experiment's "priority" factor accordingly.
- **N2. The logged `priority=` for worker/coordinator is racy in mode 2.** The thread's own `GetThreadPriority`
  (after :360) can run before or after the creator's :383 (rev 2 :390), so it logs 0 or 1. This is cosmetic. In modes 1/3 it
  always logs 1.
- **N3. The THREAD_POWER_THROTTLING_* types are visible only because `_WIN32_WINNT_WIN10_RS3` is undefined.**
  - SDK 10.0.22621 guards them with `#if (_WIN32_WINNT >= _WIN32_WINNT_WIN10_RS3)` (processthreadsapi.h:1074-1088).
    sdkddkver.h defines only up to `_WIN32_WINNT_WIN10 0x0A00` (:43). In `#if`, an undefined identifier evaluates to
    0, so the block is always compiled with this SDK.
  - `-Wundef` is not in the flag set, and it would warn inside the SDK header anyway, not in S4-T1 code.
  - SetThreadInformation needs `_WIN32_WINNT >= 0x0602` (:1046-1072), and the default is 0x0A00 (sdkddkver.h:224).
    I found no `_WIN32_WINNT` / `WINVER` / `NTDDI_VERSION` in the snapshot CMakeLists, in rexlego/src (repo copy), in
    the rexglue-sdk CMakeLists / *.cmake (thirdparty, external, out and build excluded), or in the supplied flags.
  - Residual: a check of the real native4b compile command for `-D_WIN32_WINNT` would close this completely.
- **N4. The log cap of 16 is process-wide.** In th2 the RecordingQueue is held via weak_ptr
  (native_recording.cpp:173-180), so it can be destroyed and recreated. Each new "recording queue" thread correctly
  re-applies the settings, but once 16 applications have happened the later ones are not logged.
- **N5. `LEGO_NATIVE_CHAIN_PRIORITY=0` (or any malformed value) is not silent.** It logs one "mode 0: off" line. This
  matches the comment at :335 ("Any other value: off, with one log line"). Only an unset variable is fully silent.
- **N6. Thread descriptions collide.** RecorderMain (after :155), RecordingQueue (native_recording.cpp:112) and th2
  WorkerMain when `!NativePrepareEnabled()` (after :264) are all named "Native GPU recording". The new role strings
  plus `tid=` are the only way to tell them apart. That is a reason to keep the log line.

## Check 1: additive only, CRLF, ASCII

- before/ matches the snapshot byte for byte (SHA256 by path, and it matches SHA256SUMS.txt):

  | File | SHA256 (prefix) | Bytes |
  |---|---|---|
  | native_worker.cpp | 7157E8F2... | 22262 |
  | native_recording.cpp | 48F0C429... | 27848 |
  | native_preparation.h | 889F3FA6... | 2651 |

- The after/ hashes match SHA256SUMS.txt:

  | File | SHA256 (prefix) | Bytes |
  |---|---|---|
  | native_worker.cpp | CE2DBFFB... | 24254 |
  | native_recording.cpp | 00F03D84... | 27898 |
  | native_preparation.h | 87486A90... | 2963 |

- difflib opcodes are insert-only: +34 / +1 / +5 = **+40 / -0**, with no replaced line. Stripping the inserted lines
  from after gives exactly the before bytes. The diff file has 0 `-` lines and 40 `+` lines.
- All 6 files use CRLF only (0 bare LF, 0 bare CR), are pure ASCII, contain no tabs and end with a newline.
- Inserted lines (after numbering):

  | File | Inserted | Content |
  |---|---|---|
  | native_worker.cpp | :6 | `#include "gpu_native/native_preparation.h"` |
  | native_worker.cpp | :156, :202, :265 | the call sites |
  | native_worker.cpp | :332-361 | comment and definition, at namespace scope `legodimensions::gpu_native`, outside the anonymous namespace |
  | native_recording.cpp | :113 | the call site |
  | native_preparation.h | :15-18 | the declaration |
  | native_preparation.h | :31 | the call site |

## Check 2: with LEGO_NATIVE_CHAIN_PRIORITY unset

- All 5 call sites pass string literals (`"recorder"`, `"coordinator"`, `"worker"`, `"recording queue"`,
  `"prepare"`), so nothing extra is evaluated at the call sites.
- Inside the function, the first call runs the magic-static lambda (after :338-345). It calls `std::getenv` (CRT
  table, not Win32), gets `!value`, and returns `0u` (:340) **before** the REXLOG at :343. Later calls cost only the
  static-guard check.
- `if (mode == 0) return;` (:346) comes before `GetCurrentThread` (:347), `SetThreadPriority` (:348),
  `SetThreadInformation` (:355), and the second REXLOG and `GetThreadPriority` / `GetCurrentThreadId` (:359-360).
  **Unset therefore means no Win32 call and no log line.**
- The existing `SetThreadPriority(g_thread.native_handle(), THREAD_PRIORITY_ABOVE_NORMAL)` is byte-identical and
  untouched (before :349, after :383 (rev 2 :390), with 0 removed lines).

## Check 3: compile plausibility (by reading)

- **Declarations are visible before use.**
  - native_worker.cpp gets the declaration from native_preparation.h at :6. The call sites at :156/:202/:265 are
    inside the anonymous namespace, nested in `legodimensions::gpu_native`, so unqualified lookup finds the
    enclosing-namespace declaration.
  - native_recording.cpp already includes native_preparation.h at :2 (unchanged, before the call at :113).
  - Declaration and definition have the same signature, `void ApplyNativeChainPriority(const char* role)`, in the
    same namespace.
- **SDK symbols** (processthreadsapi.h, 10.0.22621):
  - `ThreadPowerThrottling` is in `THREAD_INFORMATION_CLASS` (:1038-1044), unguarded.
  - `SetThreadInformation(HANDLE, THREAD_INFORMATION_CLASS, LPVOID, DWORD)` is under the WIN8 guard (:1046-1072).
  - `THREAD_POWER_THROTTLING_STATE`, `_CURRENT_VERSION` and `_EXECUTION_SPEED` are under the RS3 guard (:1074-1088);
    see N3.
  - `WIN32_LEAN_AND_MEAN` does not drop processthreadsapi.h.
  - `&state` converts to LPVOID implicitly. `sizeof(state)` narrows to DWORD as an ordinary argument conversion, which
    is not an error.
  - Everything is in kernel32, a default lib.
- **windows.h macro state is unchanged.**
  - In native_worker.cpp, `<windows.h>` is now first reached through native_preparation.h:3 at :6. That is after the
    same project headers as the old first windows.h. None of them (native_worker.h, pool_copy.h,
    native_recording.h -> plume_render_interface.h, draw_batch.h, fsr3_settings.h -> fsr3_upscaler.h, render_extent.h
    -> resolve_region.h) defines `_WIN32_WINNT`, `WINVER` or `NTDDI_VERSION`.
  - native_recording.cpp's include order is unchanged.
- **REXLOG_INFO (fmt-style):**
  - :343 has 3 `{}` and 3 args (`unsigned`, `const char*`, `const char*`).
  - :359-360 has 5 `{}` and 5 args (`const char*`, `DWORD`, `int`, `const char*`, `const char*`).
  - Every type is formattable by fmt, so the compile-time format check passes.
- **Language details:**
  - The lambda's two `return`s both yield `unsigned`.
  - `value[0] >= '1' && value[0] <= '3' && value[1] == '\0'` short-circuits, so `""` never reads `value[1]`.
  - `kModes[parsed]` has index 0..3, in bounds.
  - `<atomic>` (:10) and `<cstdlib>` (:14) are included.
  - Function-local statics are thread-safe (MSVC ABI `_Init_thread_*`).
- **Collisions:** `ApplyNativeChainPriority`, `ChainPriority`, `SetThreadInformation` and `THREAD_POWER_THROTTLING`
  have no prior use in rexlego/src. The local names (`mode`, `self`, `state`, `ecoqos`, `logged`, `kModes`) shadow no
  macro.
- Flags (clang++ LLVM 23, `-std=gnu++23 -O3 -DNOMINMAX -DWIN32_LEAN_AND_MEAN -D_DLL -D_MT`, MSVC target): no issue
  found.

## Check 4: thread table

Settings are applied by each thread to itself, once, as the **first statement after its SetThreadDescription**:

| Thread | Call | Follows SetThreadDescription at | Note |
|---|---|---|---|
| RecorderMain | :156 | :155 | `t_on_recorder = true;` precedes the name, unchanged |
| CoordinatorMain | :202 | :201 | |
| WorkerMain (th2 path) | :265 | :264 | |
| RecordingQueue::Run | native_recording.cpp:113 | :112 | |
| NativePreparationQueue::Run | native_preparation.h:31 | :30 | |

In every case the next statement is the thread's `for (;;)` loop.

- Settings are per thread. They last until the thread exits (StopNativeWorker, StopNativePreparation, release of the
  RecordingQueue instance, or process exit). Nothing is restored, and nothing process-wide changes (no
  SetPriorityClass or SetProcessInformation).

| Mode | Threads that call it (role) | =1 | =2 | =3 |
|---|---|---|---|---|
| n0 | none: StartNativeWorker returns early (before-file :339 = after :373), PREPARE_THREADS unset means no pool and no RecordingQueue | no effect, no log | same | same |
| th2 | WorkerMain "worker" (named "Native GPU preparation"); RecordingQueue thread(s) "recording queue"; 2x "prepare" | worker unchanged (already ABOVE_NORMAL via :383, rev 2 :390); recording queue + prepare go NORMAL -> ABOVE_NORMAL | EcoQoS opt-out on all of them; priorities unchanged | both |
| th3 | CoordinatorMain "coordinator" (WorkerMain hands off before its own call); RecorderMain "recorder"; 2x "prepare" | coordinator unchanged (:383, rev 2 :390); recorder + prepare go NORMAL -> ABOVE_NORMAL | EcoQoS opt-out on all four | both |

- **Not affected** (no call added):
  - guest threads
  - FullDrawReclaimer "Native GPU reclaim" (draw.cpp:4322 via `NativeNameCurrentThread`, native_worker.cpp after
    :493, untouched)
  - pipeline_async.h:187 PSO / async pipeline threads
  - every other thread
- NativePreparationQueue has only one instance in src (native_recording.cpp:510); the only other instance is in a
  test fixture.
- Expected log lines per run when the variable is set: th2 >= 4 (1 mode line + worker + >= 1 recording queue + 2
  prepare); th3 = 4 (+1 mode line).

## Check 5: ODR / link

- In the snapshot, native_preparation.h is included only by `native_recording.cpp:2` (checked by path in
  native_recording.cpp/.h, native_worker.cpp/.h, draw.cpp, draw_batch.h, shaders.cpp, device.cpp, textures.cpp and
  pool_copy.h; the repo copy, searched recursively, agrees).
- After S4-T1, `native_worker.cpp:6` includes it too. Including it twice is ODR-safe: the class is defined inline in
  the header and is identical in both TUs.
- legodimensions links both TUs. The fixtures do not; see S1.

## Check 6: fingerprint

- CMakeLists.txt:753-754 `file(GLOB_RECURSE ... CONFIGURE_DEPENDS src/gpu_native/*.h)`, appended at :761, covers
  native_preparation.h.
- `native_worker.cpp` (:780) and `native_recording.cpp` (:781) are listed explicitly.
- Each file is hashed with SHA256 (:790-803). **All three changed files are fingerprint inputs.**
