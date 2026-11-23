# S4-T1 (#21) independent pre-read for Agent 10

Agent 9, task #18 item 3, 2026-11-22 23:10. This is a read-only check of Agent 7's S4-T1 staging (`build/agent7/s4-t1/`, rev 2, 22:48). Nothing was built, run or edited outside `build/agent9/`. It covers four questions: is the OFF path unchanged, is the priority set and undone, is the change native-only, and are there no new lock edges? It does not cover verdict (c) (MP4 and the §9 code reads), the compile, or the runtime.

**Inputs (re-hashed at 23:02, sha256 prefix, bytes):**

| file | before/ = snap1 = live tree | after/ |
|---|---|---|
| src/gpu_native/native_worker.cpp | 7157E8F2, 22262 | 071E2F4B, 24595 |
| src/gpu_native/native_recording.cpp | 48F0C429, 27848 | 00F03D84, 27898 |
| src/gpu_native/native_preparation.h | 889F3FA6, 2651 | 88C57831, 3198 |
| s4-t1.diff | | 46FFD2E9, 5165 |

- "before = snap1 = live" means `build/agent7/s4-t1/before/`, `build/agent2/snap1/DimensionsRecomp/rexlego/` and `DimensionsRecomp/rexlego/` hold the same bytes. All values match SHA256SUMS.txt and RATE-REQUEST §2.
- The diff only adds lines: +51/-0 in 8 hunks.
  - native_worker.cpp, 5 hunks: the include, 3 hooks and the impl block (+37).
  - native_recording.cpp, 1 hunk: the hook.
  - native_preparation.h, 2 hunks: the hook block (+8) and the pool hook.
- The added lines contain no process-wide API (SetPriorityClass, SetProcessInformation, timeBeginPeriod, affinity, CPU sets or priority boost). They also contain no `mutex` or `lock` (grep of the 48 non-blank `+` lines).

**Abbreviations:** nw = `after/src/gpu_native/native_worker.cpp`, nr = `after/src/gpu_native/native_recording.cpp`, np = `after/src/gpu_native/native_preparation.h` (all under `build/agent7/s4-t1/`). "before :N" means the snap1 numbering.

**Citations:** `build/agent9/s4-t1-preread-cites.ps1` checks all 144 file:line citations in this file against the files. Result: 0 bad (23:10).

## Verdict

| # | check | result | key evidence |
|---|---|---|---|
| 1 | The OFF path is unchanged | **PASS** | When unset: getenv returns null and `return 0u` (nw:340) runs with no log, then `if (mode == 0) return;` (nw:346) runs before any Win32 call. n0 starts no chain thread, so the hook is never called. |
| 2 | The priority is set and undone | **PASS** | Each thread changes only itself, through the `GetCurrentThread()` pseudo-handle (nw:347-355). Nothing is process-wide. The settings end when the thread is joined (nw:637-639, np:48-52, nr:140-144). |
| 3 | The change is native-only | **PASS** | It touches only gpu_native files. native_preparation.h is included only by nr:2 and nw:6. There is no CMake change, and the sources sit inside `if(LEGODIMENSIONS_NATIVE_GPU)` (snap1 CMakeLists L61, L108-109). The native fingerprint changes, so the re-pin is expected. |
| 4 | There are no new lock edges | **PASS** | No caller holds a lock at the hook. Inside, the only locks are leaves: the getenv environment lock (once, inside the magic static) and the logger. The hook pointer is written before main. |

**Suggested input to your verdict:**
- (a) Default-off test bed: SAFE as far as this read goes.
- (b) Value 3 in F1/F3/W1/W8b: I found nothing against it in the code. What remains are the runtime risks Agent 7 lists (RATE-REQUEST §10, risks 1-2). F1 MP1 and W8b's guards cover them.
- None of the notes in §5 blocks either verdict.

## 1. The OFF path is unchanged

**The 5 call sites.** Each one is placed between the thread naming itself and its loop:

| site | role | hook | first lock after the hook | idle wait |
|---|---|---|---|---|
| RecorderMain | `recorder` | nw:156 | nw:160 g_queue_mutex | nw:161 |
| CoordinatorMain | `coordinator` | nw:202 | nw:205 g_queue_mutex | nw:206 |
| WorkerMain | `worker` | nw:265 | nw:268 g_queue_mutex, then nw:274 NativeRecordingMutex | nw:269 |
| RecordingQueue::Run | `recording queue` | nr:113 | nr:117 mutex_ | nr:118 |
| NativePreparationQueue::Run | `prepare` | np:35 | np:39 mutex_ | np:40 |

The loop bodies are unchanged: each hunk has 6 context lines and adds 1 line.

**Trace when unset:**
1. The wrapper `ApplyNativeChainPriority` (np:19-21) loads the hook pointer and calls `ApplyNativeChainPriorityImpl` (nw:337).
2. The first call runs the magic static (nw:338-345). `std::getenv` (nw:339) returns null, so `return 0u;` (nw:340) runs. The mode log line (nw:343) comes after that return, so nothing is logged.
3. `if (mode == 0) return;` (nw:346) comes before GetCurrentThread (nw:347), SetThreadPriority (nw:348), SetThreadInformation (nw:355) and the per-thread log (nw:358-360).
4. Result: no Win32 call and no log line. The cost is one indirect call and one static-guard check per chain-thread start. That is once per thread, not per job or frame: 4 thread starts in th3, at least 4 in th2.

**n0 (THREADED unset) never calls the hook:**
- StartNativeWorker returns at nw:380.
- With PREPARE_THREADS unset, the count is 0 (nr:522-528), so the function-static pool (nr:510-513) has no threads.
- PrepareNativeCommandList returns the list unchanged (nr:531). So no PreparedCommandList exists, and no RecordingQueue either (nr:174-181, created only from nr:257).

**Code that stays the same:**
- The creator-side `SetThreadPriority(g_thread, ABOVE_NORMAL)` (nw:390, before :349).
- All thread names: nw:155, nw:201, nw:264, nr:112, np:33-34.
- The thread creation order (nw:387-388).

**Values other than 1-3, including `0`:** these log one "mode 0: off" line and make no Win32 call. This is N5, as the comment at nw:335 says.

This agrees with DIFF-REVIEW Check 2 (`check/DIFF-REVIEW.md` L135-146) and with RATE-REQUEST L147. The runtime proof is F1 (b): th3 vs th3old should give NEW 0.

## 2. The priority is set and undone

**Set:**
- **Modes 1 and 3** set `THREAD_PRIORITY_ABOVE_NORMAL` (nw:348).
- **Modes 2 and 3** call `SetThreadInformation(ThreadPowerThrottling)` with ControlMask EXECUTION_SPEED and StateMask 0 (nw:350-355). This puts the thread under explicit control with execution-speed throttling off, which opts it out of EcoQoS.
- Both calls go through the thread's own pseudo-handle (nw:347).

**Once per thread:**
- Every hook sits before its thread's loop.
- WorkerMain hands off to CoordinatorMain at nw:263, before its own hook at nw:265. So in th3, the worker thread applies the setting once, as `coordinator`.

**Effect by thread:**

| thread (mode) | today | value 1 or 3 |
|---|---|---|
| RecorderMain (th3) | NORMAL: created at nw:387, and the creator doesn't raise it | ABOVE_NORMAL |
| WorkerMain → CoordinatorMain (th3) | ABOVE_NORMAL (nw:390) | no change (N1) |
| WorkerMain (th2) | ABOVE_NORMAL (nw:390) | no change (N1) |
| RecordingQueue thread (th2) | NORMAL | ABOVE_NORMAL |
| prepare pool threads (th2/th3) | NORMAL | ABOVE_NORMAL |

When the creator (nw:390) and the thread itself (nw:348) both set ABOVE_NORMAL, they race on the same value, so the race is harmless. In mode 2 only the logged `priority=` is racy (N2, cosmetic).

**Logging:** each thread logs its role, tid, priority, `(set failed)` and `opt-out failed` (nw:358-360). The cap is 16 lines per process (N4). FUNCTIONAL-ROWS L100-103 checks exactly these lines.

**Undone:**
- **Nothing process-wide is touched:** no SetPriorityClass, SetProcessInformation, timeBeginPeriod, affinity or CPU sets (diff grep above). No thread outside the chain is touched.
- **The settings belong to the thread and end with it:**
  - StopNativeWorker joins the worker/coordinator thread (nw:637) and the recorder (nw:638).
  - In full-draw mode the pool shuts down at nw:639 (nr:514 → np:59 → np:48-52, join at np:51). Otherwise the function-static pool's destructor (np:58) runs at exit.
  - The RecordingQueue destructor joins (nr:140-144) when the last PreparedCommandList lets go of the weak_ptr singleton (nr:174-181). A later instance is a new thread, and it applies the setting again.
- **No guest or host thread is ever raised:**
  - Pool threads only run queued jobs (np:36-46).
  - Inline fallbacks ("Runs inline when the queue is full", np:60) run on the caller, at the caller's own priority.
  - No chain thread is reused for other work after its loop exits.

## 3. The change is native-only

- **Files:** only `src/gpu_native/`.
  - native_preparation.h is included only by nr:2 in the live tree (recursive grep of `DimensionsRecomp/rexlego/src` at 23:08). After the change it is also included by nw:6.
  - `ApplyNativeChainPriorityImpl` is `static` and exists only in native_worker.cpp (RATE-REQUEST L209, PROOF 6).
- **Build:** there is no CMake change.
  - native_worker.cpp and native_recording.cpp are listed at snap1 CMakeLists L108-109 (live L108-109). That is inside `if(LEGODIMENSIONS_NATIVE_GPU)` (L61), and no endif of that block comes before L109.
  - L62-63 make that block Windows/D3D12-only.
  - Targets that link native_recording.cpp without native_worker.cpp keep the hook null, so the call does nothing and needs nothing at link time (np:15-21). This is rev 2's fix for DIFF-REVIEW S1.
- **Guest code:** the change has no generated code, no toml and no SDK change, and it doesn't touch codegen inputs, so `codegen.stamp` is not affected.
- **Native fingerprint:** it changes.
  - All three files are inputs: the .cpp files at snap1 CMakeLists L780-781, the headers through `GLOB_RECURSE src/gpu_native/*.h` at L753-754, and the SHA256 material, which is cut to 16 hex at L798 and written at L802. The live CMakeLists has the same lines 22 earlier (L758-759, L731, L776, L780).
  - This is the re-pin that RATE-REQUEST L216-217 and §13 already list. See note P2 for what the fingerprint keys at run time.

## 4. There are no new lock edges

- **At the call:** no caller holds a lock (table in §1). The first lock is always taken after the hook returns.
  - The threads are created inside StartNativeWorker's `call_once` (nw:381-392), but the hook runs on the new threads, which never touch the once-flag.
  - The `g_queue_mutex` scope at nw:384-386 closes before the threads are created.
- **Inside the impl:**
  1. The magic-static guard for `mode`. With MSVC thread-safe statics, the guard's internal lock is not held while the initializer runs. Other threads wait on its in-progress state.
  2. `std::getenv`, which takes the UCRT environment lock. This happens only inside that initializer, once per process.
  3. REXLOG_INFO, which takes the logger. It is a leaf.
  4. The `logged` counter (nw:357), which is atomic and lock-free.
  5. The kernel calls, which take no user-mode lock.
- **The only nesting** is static-init(mode) → environment lock and static-init(mode) → logger. Neither the environment lock nor the logger calls back into the hook, so there can be no cycle.
- **The same nesting already exists** in NativeWorkerEnabled (nw:324-329), NativeFullDrawPreparationEnabled (nr:498-504) and NativePreparationWorkerCount (nr:522-528).
- **The hook pointer:**
  - It is an `inline` pointer, constant-initialized to nullptr (np:18).
  - It is written once by the static initializer at nw:365-368, before main.
  - It is read only by threads created later; the std::thread start synchronizes-with the write. So there is no data race and no lock is needed.
- **Raised threads don't spin:**
  - Every chain thread idles in a condition-variable wait (nw:161, nw:206, nw:269, nr:118, np:40).
  - The existing back-pressure waits (nw:417, nr:152, nr:169) are unchanged.
  - g_queue_mutex and NativeRecordingMutex are already shared with an ABOVE_NORMAL worker today (nw:390).
  - So a raised thread that waits on a NORMAL lock holder sleeps instead of spinning. This adds no lock edge; the preemption question is runtime risk 1 (below).

## 5. Notes (none blocking)

**P1. Line numbering in the request documents.** There is no content error. It's only something to watch when citing lines in the verdict.
- RATE-REQUEST L86 says `native_preparation.h:14-21`. In after/ the content is at np:15-21, and the 8 inserted lines are np:15-22. The hunk `@@ -12,6 +12,14 @@` can place the blank line at either end.
- DIFF-REVIEW N1/N2 (L79, L83) say "after :383". That is rev-1 numbering; in rev 2 it is nw:390.
- These use before/snap1 numbering:

  | where | cited | after/ |
  |---|---|---|
  | FUNCTIONAL-ROWS L40 | :260 | nw:263 |
  | FUNCTIONAL-ROWS L42 | native_recording.cpp:173-178 | nr:174-181 |
  | FUNCTIONAL-ROWS L160 | :596/:597 | nw:637/:638 |
  | matrix-s4t1-f1.json L27 | :349 | nw:390 |
  | matrix-s4t1-f1.json L108 | :260 | nw:263 |

**P2. Fingerprint-keyed files at run time, for the F1 cross-bin comparison.**
- **`kNativeGpuBuildFingerprint` keys:**
  - the pipeline recipe file and the startup seeds: `PipelineRecipes::Read` rejects another fingerprint (pipeline_recipes.h:247-256), and `ReadRecipes` then logs WARN "ignoring invalid or incompatible pipeline recipes" (pipeline_library.cpp:502-510);
  - the precompiled shader pack (shader_archive.cpp:152-158). It is only loaded when `LEGO_NATIVE_SHADER_PACK` and `LEGO_NATIVE_SHADER_PACK_TRIGGER` are both set (shaders.cpp:601-608), and no F1 arm sets them.
- **The caches are per executable directory:** `<exe dir>/cache/native-pso.bin`, `cache/native-pso-recipes.bin` and `<exe dir>/native-pso-seed.bin` (pipeline_library.cpp:99-105, :150-152).
  - So the OLD and S4T1 bins never read each other's files, and there is no cross-bin rejection WARN, unless someone copies `cache/` or a seed between bin dirs. Don't.
  - At 23:07 neither native4b-bin nor native4-bin had `cache/` or a seed. The MANIFESTs of `build/agent2/native*-bin` list no `native-pso` rows.
- **The order is round-robin and runs use `-NoCold`.** If runs use the bin dirs in place, r1 of each bin dir starts with an empty cache: n0 r1 (S4T1) and th3old r1 (OLD) are cold, while th3 r1 follows n0 r1 on the same bin and is warm.
  - If F1 (b) shows MORE/GONE ≠ 0, check for cold-only line types before blaming #21.
  - One warm-up run per bin dir, or reading (b) on r2 only, removes the asymmetry. It is cheap, so it may be worth it.
- **The "ready" line is safe for logdiff:** the startup line `Native GPU [<fingerprint>]: ... ready` (device.cpp:903-906) differs between the two bins, but logdiff masks hex runs of 8 or more (`build/agent10/bgate/logdiff.py` L38). So it is not a NEW key.

**P3. Runtime risks.** I agree with RATE-REQUEST §10, risks 1-2.
- ABOVE_NORMAL (9) chain threads can preempt NORMAL (8) guest and audio threads. F1 MP1 and W8b's light-share and host-flag guards cover this.
- Keep Agent 11's process-level `host_execution_throttling_optout` at its default (false) in every #21 row (RATE-REQUEST L236-239). The per-thread SetThreadInformation and the process-level SetProcessInformation have not been tested together.

**P4. Where the variable is read.** The getenv and the mode line now run on the first chain thread to start, not on main. That is harmless. The variable is read once per process, so it must be in the environment at launch, which is how the matrix sets env per run.

**P5. N3 residual (outside the four checks).** I could not close it from snap1-off: its compile_commands.json has 0 `gpu_native` entries because it is a native-off build. The place to check `-D_WIN32_WINNT` is still Agent 2's native4b compile command.

## 6. Cross-check

- This read agrees with:
  - RATE-REQUEST §3-§8 and §10;
  - make_s4t1 PROOFS 1-6 (`make_s4t1.out.txt`, ALL PROOFS PASS at 22:48);
  - DIFF-REVIEW Checks 2, 4 and 6 and NITs N1-N6, apart from the stale rev-1 line numbers (P1).
- I found no disagreement.
- I did not check: the compile, the runtime, MP4 or §9 (verdict (c)), or the W8b matrix.
