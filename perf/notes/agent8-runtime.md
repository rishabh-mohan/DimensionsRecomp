# Agent 8 — runtime: native CPU replacements and always-on overhead (task #7)

Status: **partial, analysis only.** Agent 1 stopped builds at 12:24. I edited no source files, built nothing and ran nothing.
`git status --short` is clean in `DimensionsRecomp` and in `DimensionsRecomp/rexglue-sdk` (checked 12:30).
Part 2 (always-on overhead) went to two helpers. Their findings are in
[agent8-runtime-diag.md](agent8-runtime-diag.md) and [agent8-runtime-features.md](agent8-runtime-features.md); see §2.

**Measurement caveat.** I have no call counts or profile yet: `rexlego/generated` is missing and clang isn't installed.
The ranking below multiplies the saving per call (from reading the code) by how often I *guess* each function runs.
Before changing anything, the resume session should count calls per frame (§3, step 2). Items 1 and 2 are close and could swap places.

> [!IMPORTANT]
> Agent 9 proposes codegen flags that overlap items 1.1 and 1.2 ([agent9-codegen.md](agent9-codegen.md) L49-L79). Whoever picks this up should agree the order with Agent 9 first.
> - `skip_msr = true` turns `mfmsr/mtmsrd` into no-ops everywhere. That removes the global lock and the fences from all code, and would make `native_lock_elide.cpp` redundant.
>   The generator's validator would then match nothing, so the generator would also need retiring or adapting.
> - `non_volatile_as_local = true` (Agent 9's Stage C) makes the SDK drop the `__save*/__rest*` helpers, which would make `native_saverest.cpp` dead code.
>
> 1.1 and 1.2 are the low-risk fallback if those flags are delayed or rejected. They are local to files we own and need no SDK or config change.
> 1.1 is also narrower than `skip_msr`: it only touches the 7 functions whose regions the validator proved to be pure `lwarx/stwcx.`.

SDK facts this relies on (from `rexglue-sdk/resources/templates/codegen/pch_h.inja` and `src/codegen/builders/helpers.h`):
- `REX_LOAD/STORE_Un` are volatile, byte-swapped accesses at `base + ea (+0x1000 if ea >= 0xE0000000)`.
- `lwarx` is a plain, non-volatile load into `ctx.reserved`. `stwcx.` becomes `__sync_bool_compare_and_swap` (a `lock cmpxchg`: a full barrier on x86).
- `mfmsr` becomes a seq_cst fence + `REX_CHECK_GLOBAL_LOCK()`. `mtmsrd r13,1` becomes a fence + `REX_ENTER_GLOBAL_LOCK()`, and `mtmsrd rX,1` becomes a fence + `REX_LEAVE_GLOBAL_LOCK()`.
- `lwsync` produces no code.
- Hooks replace the guest function through a strong symbol (direct call). `r14..r31` and `f14..f31` are contiguous in `PPCContext`.

## 1. Part 1 — native replacements, ranked by expected win

### 1.1 Remove the 3 leftover hardware fences in every lock-elided `lwarx/stwcx.` region (native_lock_elide.cpp, generator-driven)

- **Where:** [native_lock_elide.cpp](../DimensionsRecomp/rexlego/src/native_lock_elide.cpp) has 94 `std::atomic_thread_fence(seq_cst)`. That is exactly 26 `mfmsr` plus 68 `mtmsrd` fences; these bodies contain no `sync` instructions. Example: the region at L72-L94 (`sub_82A2CAB0`, the freelist pop) with fences at L73, L76 and L93, plus L107 on the second exit.
  The file is generated, so the fix goes in [gen_lock_elide.py](../DimensionsRecomp/tools/native-cpu/gen_lock_elide.py): `elide()` at L104-L110 and the preamble at L121-L125.
- **What is slow:** the elision already removed the global mutex but kept the fences. Each region runs on its success path:
  `mfence`, acquire load, `mfence`, plain load + bswap, `lock cmpxchg`, `mfence`.
  That is 3 serialising fences (each ~20-40+ cycles plus a store-buffer drain) around 1 locked op, so roughly 4-5× the cost of the CAS alone.
  The hooked functions are the allocator's hot paths: freelist pop/push (`82A2CAB0`, `82A2CC20`), small-block alloc/free (`82A34E28`, `82A34FE8`, `82A4CA18`), string interning (`82A35D28`) and the XAPI queue (`83F99CB8`).
- **Why it is equivalent:**
  - On Xenon, `mfmsr` and `mtmsrd L=1` are not storage barriers; they only toggle EE (interrupt enable).
  - Once the lock is gone, fence 3 sits right after a `lock cmpxchg`. The validator enforces this: `code[j-4]` must be the CAS (gen L83). So fence 3 adds nothing on x86.
  - Fences 1 and 2 only stop earlier stores from passing the `lwarx` plain load (x86 store→load reordering). PPC allows that reordering too when there is no `sync`.
  - Using `atomic_signal_fence` keeps exactly the same *compiler* ordering and emits zero instructions.
- **Proposed change (generator only, then regenerate):**
  ```diff
   def elide(body):
       out = []
  -    for line in body.split('\n'):
  +    lines = body.split('\n')
  +    for i, line in enumerate(lines):
           s = line.strip()
           if s in (ENTER, LEAVE): continue
  +        if s == FENCE and i and lines[i - 1].strip().startswith(('// mfmsr', '// mtmsrd')):
  +            out.append(line.replace(FENCE, 'LOCK_ELIDED_FENCE();'))
  +            continue
           out.append(line.replace('REX_CHECK_GLOBAL_LOCK()', 'LockElidedMsr()'))
  ```
  ```cpp
  // emitted preamble
  #if defined(__x86_64__) || defined(_M_X64)
  // mfmsr/mtmsrd don't order storage on PPC; x86 TSO plus the locked cmpxchg give what the guest relied on.
  #define LOCK_ELIDED_FENCE() std::atomic_signal_fence(std::memory_order_seq_cst)
  #else
  #define LOCK_ELIDED_FENCE() std::atomic_thread_fence(std::memory_order_seq_cst)
  #endif
  ```
  The same generator edit should also fix the per-call `Enabled()` (L26-L32): its function-local static runs the MSVC-ABI thread-safe-static epoch check on every call, which is a TLS load plus a compare.
  Replace it with `const bool g_enabled = ReadEnabled();` at namespace scope; `native_memops.cpp` already uses this pattern for `g_mode`.
- **Risk:** low. It depends on the barrier analysis above, which the stress test should confirm.
  The ABA exposure (loads before `lwarx`) already exists and this change neither adds nor fixes it.
  `LEGO_NATIVE_LOCK_ELIDE=0` still runs the original `__imp__` code, so A/B comparison stays easy.
- **How to verify:**
  1. Offline, no toolchain needed. Rebuild each original body from the current file: put `REX_ENTER/LEAVE_GLOBAL_LOCK();` back after the msr line of each `mtmsrd` and turn `LockElidedMsr()` back into `REX_CHECK_GLOBAL_LOCK()`.
     The `sha256[:16]` digests in the comments must match. Then put the rebuilt bodies in a mock GEN dir, run the old generator and check it reproduces the current file byte for byte; run the new generator and check the diff touches only fence lines and the preamble.
  2. Check the asm (`clang -S`): count the remaining `mfence` (or `lock or`) instructions. Expected: 0 in the `Elided_*` functions.
  3. Single-threaded old-vs-new differential on `Elided_82A2CAB0`/`82A2CC20`, using a 4 GB reserved arena and random freelists. Compare `ctx` and memory.
  4. Multi-threaded stress: 4-8 threads doing pop/push on one freelist, 1e8 ops, checking node conservation, for both old and new.
  5. Microbenchmark of uncontended and contended ns/op in `bench/agent8/native`. In game, A/B with `LEGO_NATIVE_LOCK_ELIDE` under the sample profiler, plus a soak run.

### 1.2 `__savegprlr/__restgprlr/__savefpr/__restfpr` hot path (native_saverest.cpp)

- **Where:** [native_saverest.cpp](../DimensionsRecomp/rexlego/src/native_saverest.cpp): helpers at L60-L88, `FastFrame` at L57, gate macros at L139-L166. They run in every non-leaf guest prologue and epilogue, which is probably the most frequently called native code in the game.
- **What is slow:**
  - Each call checks `g_mode == kOff`, then `FastFrame` (2 compares), then `g_mode == kValidate`.
  - The copy is one *volatile* bswapped 8-byte access per register: 18 load/bswap/store triples for N=14. `volatile` blocks vectorisation and store merging.
- **Proposed change:**
  - (a) Use a single gate: `const u32 g_span = g_mode == Mode::kOn ? 0xE0000000u - 0x100u + 1u : 0u;` with `FastFrame(f) = f - 0x100u < g_span`.
    Off and validate both fail the gate and take a cold slow path, which still validates when the old `FastFrame` holds.
  - (b) Make the copy non-volatile. First just drop `volatile` and check clang emits `pshufb` (SSSE3 is part of the x86-64-v2 baseline).
    Otherwise use explicit `_mm_shuffle_epi8(_mm_loadu_si128(src), kSwap64)` with 2 registers per 16 bytes and a scalar tail for odd counts.
  - Address translation doesn't change: frames ≤ 0xE0000000 never need the +0x1000 adjustment, and stacks are never MMIO.
- **Risk:** low. Store granularity and tearing are only visible to other threads that read a private stack frame. On an unmapped stack the fault point may land on a different register's slot.
- **How to verify:**
  - Run `tools/native-cpu/check_saverest.py` (needs generated code).
  - Randomised old-vs-new over N=14..31 comparing memory plus all of `ctx`. Include boundary frames 0xFF, 0x100, 0x7F000000, 0xE0000000 and 0xE0000001, and all three modes.
  - Microbenchmark ns/call per helper.
  - In game, run with `LEGO_NATIVE_SAVEREST_VALIDATE=1`.

### 1.3 `Enabled()` static guard in native_atomics.cpp

- **Where:** [native_atomics.cpp](../DimensionsRecomp/rexlego/src/native_atomics.cpp) L13-L18, called from hooks `82A2A160`, `82A2A138` and `82A2A0E8` (L45-L60).
- **What is slow:** the same thread-safe-static check on every call. The CAS loop itself is fine: the value is big-endian, so `xadd` isn't possible, and seq_cst matches the guest semantics.
- **Change:** use a namespace-scope `const bool`.
- **Risk:** none known.
- **How to verify:** randomised equivalence on r3, cr0 and memory, plus a microbenchmark.

### 1.4 Inline small sizes in native_memops.cpp

- **Where:** [native_memops.cpp](../DimensionsRecomp/rexlego/src/native_memops.cpp) L66 (`memset`) and L88 (`memcpy`), gated at L166-L177.
- **Current cost:** the gate is already a single load of the const `g_mode`.
- **Possible change:** handle n ≤ 32 inline with overlapping SSE head/tail stores (`MemcpyFast`, L91, already proves the ranges are disjoint) to avoid the vcruntime call.
  The register side effects must stay exactly as they are: memset sets r0, r4-r6, ctr and cr0; memcpy spills r1-r8.
- **Priority:** medium/low. Whether it pays depends on the size distribution, so that needs a histogram first.
- **How to verify:** randomised old-vs-new, then in game with `LEGO_NATIVE_MEMOPS_VALIDATE=1`.

### 1.5 native_constants.cpp — no change needed by default

- **Current cost:** `PollNativeConstantPublisher` (L33-L50) runs once per present ([gpu_native/device.cpp](../DimensionsRecomp/rexlego/src/gpu_native/device.cpp) L2087). Without `LEGO_NATIVE_CONSTANT_PUBLISHER_FILE` it costs a static guard plus a null check.
- **Debug mode only:** with the file variable set, it calls `steady_clock::now()` every present and opens an `ifstream` every 500 ms on the present thread.
  If that ever matters, check the file's mtime instead or poll from a worker thread. Low priority.
- **Test:** [test_native_constants.cpp](../DimensionsRecomp/tools/gpu-aot/test_native_constants.cpp) needs `native_constants_oracles.inc` from generated code.

### 1.6 native_slot_growth.cpp / slot_growth.h / heap_shape.h — low priority

- These only build under `LEGODIMENSIONS_NATIVE_GPU` and run at load time / slot growth, not every frame.
- `ValidateShape` ([heap_shape.h](../DimensionsRecomp/rexlego/src/heap_shape.h) L21-L75) builds `unordered_map`/`unordered_set` on every Grow, Release and Shape call, walking up to 262144 blocks and 960 bins.
- **Possible change:** `reserve()`, or sorted vectors. Only worth it if load-time profiling shows it.

## 2. Part 2 — always-on overhead (delegated)

- Diagnostics (sample_profiler, tt_lock_trace*, name_trace, crash_guards/VEH, crash_popup, native_skin_diagnostics, native_heap_journal, discord_presence, toypad_app): [agent8-runtime-diag.md](agent8-runtime-diag.md).
- Per-frame features (cheat_engine, cheat_menu, main_menu_extras, scene_distance, settings_*): [agent8-runtime-features.md](agent8-runtime-features.md).
- Both helpers were told at 12:29 to stop editing, keep the repo clean and write ranked findings in the same format as §1. Their summaries are in §2.1, if they arrived before the deadline.

### 2.1 Helper summaries

**Per-frame features** (helper reported 12:36; repo clean; nothing built). Details, diffs and tests are in [agent8-runtime-features.md](agent8-runtime-features.md).
1. `cheat_menu.cpp:192` / `cheat_engine.cpp:362`: while the DEL menu is open, `TakeResults(200)` rescans the candidate bitmap from word 0 every frame.
   That reads up to 16 MiB per frame for a 32-bit scan and 64 MiB for an 8-bit one, likely milliseconds each frame. Each listed row also costs a `VirtualQuery` plus a mutex.
   Fix: build the result list once at the end of `RunScan` and reuse it.
2. `cheat_engine.cpp:461` `FreezeMain`: once the menu has been opened, it wakes 20 times a second for the rest of the session, even with nothing frozen; shutdown can stall up to 50 ms.
   Fix: block on a condition variable when nothing is frozen.
3. `settings_revision.cpp:231` `PendingForRenderer`: takes a mutex every frame on the render thread, and the UI thread locks the same mutex every frame. Fix: check an atomic "commit ready" flag before locking.
4. `scene_distance.cpp:57`: every scene-instance load locks a mutex and does two hash lookups, even at the default scale. Fix: add an `empty()` guard like the level hook's.
- Already cheap when off: the Localise/SetText hooks. The settings config/registry/transaction code runs only at startup or on Apply.
- Not reviewed fully: `settings_frontend.cpp` and most of `settings_native_bridge.cpp`.
- Follow-up for the gpu_native owner: `gpu_native/settings_runtime.cpp:137` `Active()` does three locked atomic operations per call; check whether it runs per draw.

**Diagnostics** (helper reported 12:36; its 13 files are clean; nothing built). Details are in [agent8-runtime-diag.md](agent8-runtime-diag.md).
1. **Biggest always-on item found.** `native_scene_diagnostics` defaults to *true* in the Native GPU build (`native_skin_diagnostics.cpp:14`).
   - Every guest alloc/free (`sub_82A33D28` / `sub_82A34208`) then pays a bucket spinlock plus a `lock xadd` on one global atomic shared by all threads (`native_heap_journal.h:49-59`).
   - Free also saves and restores a TLS struct. Level unloads log about 16 ostringstream-formatted lines per skin.
   - Proposals: default false in release (needs owner sign-off); a byte-identical fmt-based `HexWords`; `alignas(64)` on the sequence counter.
   - This probably costs more than item 1.1, because it runs on the same allocator paths.
2. `discord_presence.cpp:387-391`: the thread (on by default) wakes 10 times a second. Fix: `condition_variable::wait_for(2s)` with a notify in `Stop()`. Same cadence, 0.5 wake-ups/s, and Stop returns immediately.
3. Slow first Toy Pad placement: the cause is not in `toypad_app.cpp`, which only launches.
   - The SDK listener (`emulated_toypad.cpp`) has no lazy init. The likely cause is first-use asset streaming plus shader/PSO compilation, which needs a game run to confirm.
   - The SDK's `PickerWatchRun` polls every 50 ms all session (SDK owner).
4. Smaller items:
   - `name_trace`: return early when off, to skip the string build.
   - `tt_lock_trace`: not in the default build.
   - `sample_profiler`: zero cost when off; when on it holds `timeBeginPeriod(1)` and takes a system-wide thread snapshot every sample.
   - `crash_guards`: has no vectored handler and is already minimal. The only vectored handler is the SDK's `exception_handler_win.cpp:305`, which nobody audited.
- Not read: the SDK vectored handler, the rest of `emulated_toypad.cpp`, `CopyNativeGuestMetadata`, `AllocationAttemptScope`.

## 3. Resume plan (once the toolchain and Agent 3's harness exist)

1. Build the unmodified game once and check the elided-function asm for fences (decides 1.1).
2. Count calls per frame for the saverest helpers, the elided functions, atomics and memops, using the sample profiler or a temporary counter build in `build/agent8`. Re-rank 1.1 and 1.2 from the result.
3. Implement 1.1 through the generator with the offline digest round-trip, then run tests and benchmarks in `bench/agent8/native`.
4. Implement 1.2 and 1.3, then 1.4 if the size histogram justifies it. Each needs an old-vs-new randomised test and a microbenchmark.
5. Part 2 items, ordered from the helper reports. Start with the `native_scene_diagnostics` default (§2.1 diag 1, needs owner sign-off), then the cheat-menu rescan, then the Discord and FreezeMain wake-ups.

Constraints: baseline `-march=x86-64-v2` (no AVX without runtime dispatch); at most one heavy build, `ninja -j` ≤ 4.

## 4. Not read / not done

- `native_lock_elide.cpp` L200-L2315 in detail: the bodies of `82A2CC20`, `82A34E28`, `82A34FE8`, `82A4CA18`, `82A35D28` and `83F99CB8`. I only grepped their structure.
- `native_markers.cpp`, `native_effects.cpp`, and the other top-level `rexlego/src` files not on the task list.
- `README-dev.md`, `docs/native-gpu-known-bugs.md`, the `tools/gpu-aot` notes.
- The SDK's global critical region implementation and how codegen lowers `sync`.
- No asm inspected: I haven't checked whether the fences lower to `mfence` or `lock or`.
- No call counts and no game profile.
- No tests or benchmarks written in `bench/agent8` yet.
- Part 2 files beyond what the helpers covered (see their "not read" lists).
