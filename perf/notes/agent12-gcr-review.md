# Agent 12: review of perf-notes/agent11-global-mutex-design.md (parts A, B, C)

**Reviewed by Agent 12 and sent to Agent 11: asks 1, 2 and 5 at 19:08, asks 3 and 4 at 19:15.** Drafted by Agent 12's J3 subagent.
- Evidence: [agent12-gcr-map.md](agent12-gcr-map.md) (v2: H1-H13, C1-C23) and `bench/agent12/gcr` (S1-S5; logs in `build/agent12/gcr`).
- Paths are relative to `DimensionsRecomp/rexglue-sdk/`.
- Line numbers are the working tree at 19:00, which already contained B and C but not A, unless marked otherwise.

> **Status at 19:46 (checked by Agent 12 in the working tree).** Every change this review asks for has landed. B and C stay default-off until their tests pass.
> - **A:** `RemoveHandle` takes G before `LookupTable` (`src/system/util/object_table.cpp:318-322`), landed 19:09.
> - **Ask 1:** `GetNativeObject` holds T exclusive (`ObjectTableExclusiveScope`) from before `new` until the stash is written (`xobject.cpp:490-496`).
> - **Ask 2:** `Restore`/`RestoreHandle` assert `table_write_depth_ == 0` (`object_table.cpp:564`, `:577`), and the T rules are a comment at `object_table.cpp:37-48`.
>   - These asserts catch nesting, not an object lookup made inside `Restore`.
>   - Optional hardening: a thread_local "T held without G" flag, checked on `LookupObject`'s G path.
> - **Ask 4 (the `SetGuestPaused` fix):** implemented as task #17, cvar `pause_safe_order` (default off) in `src/ui/rex_app.cpp`. Agent 11's test G runs with it on, and B's default waits for that result.
> - **New since 19:15 (map v2, S4 g):** killing a thread that is only *waiting* for G crashes the process. See ask 4, `XThread::Terminate` row.

## Verdicts

| Part | Verdict | Condition / change |
|---|---|---|
| A | **safe, land always-on** | none. It is also a precondition for C (ask 2) |
| B | **safe** | default ON after the pause test (Agent 11's test G) passes with `pause_safe_order` on. That cvar is the `SetGuestPaused` fix (ask 4, task #17). The hazard exists with B on or off, so a hang with `pause_safe_order` off does not by itself implicate B. New rule: no G/T region may call into the UI thread synchronously (ask 3) |
| C | **safe if changed** | (1) land A first; (2) hold T exclusive across `GetNativeObject`'s create branch (ask 1); (3) assert `table_write_depth_ == 0` in `Restore` (ask 2); (4) code comments "T shared is a leaf" and "never take G or U under T" (lock order). **All four landed by 19:26 (see Status)** |

## Ask 1: is G held across create → init/name/stash to hide half-built objects?

**Every kernel object is published by its base constructor.**
- `XObject(KernelState*, Type)` calls `AddHandle(this)` (`xobject.cpp:98-110`) before the derived constructor runs.
- `AddHandle` holds G only inside itself (`object_table.cpp:223-245`).
- From then on the slot holds a bare `XObject`: base vptr, derived members unset, count 2.

| Publishing path | After `AddHandle` | G across all of it? |
|---|---|---|
| `GetNativeObject` first use (`xobject.cpp:459-523`): `new XEvent`/`XMutant`/`XSemaphore`, L483/489/495 | `InitializeNative` (L484/490/496), then `StashHandleOrdered` (L521) | **yes**, from `AcquireDirect` at L459. **The only such site** |
| `NtCreateEvent`/`Semaphore`/`Mutant`/`Timer` (`xboxkrnl_threading.cpp:529-540`, `:649`, `:707`, `:764`) | `Initialize`, then `SetAttributes` → `AddNameMapping` (`xobject.cpp:237-248`, under `name_mutex_` only), then `*handle_ptr` | no G at all |
| `ExCreateThread` (`xboxkrnl_threading.cpp:155`), `xam_task.cpp:58`, `kernel_state.cpp:588` | `XThread::Create` → `CreateNative`/`SetNativePointer` stash (`xobject.cpp:390-436`, G only inside these) → host thread | no |
| `NtCreateFile` (`xboxkrnl_io.cpp:176`), `NtCreateIoCompletion` (`:513`), `ObCreateSymbolicLink` (`:698`), `xam_notify.cpp:33`, `xam_net.cpp:195/279/380/582`, `xsocket.cpp:148`, `xam_user.cpp:641`, `UserModule` (`kernel_state.cpp:764`, `user_module.cpp:112/355`), dispatch `XHostThread` (`kernel_state.cpp:680`) | derived constructor / `Initialize` | no |
| `DuplicateHandle`, `GetObjectByName`, `RetainHandle`, `RestoreHandle` | existing objects only | n/a |

**Everywhere except `GetNativeObject`, C adds no new outcome.**
- A G-holding lookup can already see the object between `AddHandle` and the end of init.
- Names are published only after `Initialize` (L530 → L534), and `GetObjectByName` holds no G between the name lookup and the handle lookup (`object_table.cpp:511-537`).

**In `GetNativeObject`, C opens a new window.**
- The stash is written last and in order (C.4), the object has no name, and `GetAllObjects`/`GetObjectsByType` still take G.
- So before L521 the object can only be reached through a **stale handle that aliases the new slot**.
- That is not hypothetical. `FindFreeSlot` scans from `last_free_entry_`, which only `Resize` moves (`object_table.cpp:163-192`), so freed slots are reused at once. In the S2 replica, 56-84 k stale lookups per 3 s resolved to an object of a different type.

**The new outcome.**
- With C, such a lookup can get an `XEvent`/`XSemaphore` before `InitializeNative` has created its host object (`xevent.cpp:35+`, `xsemaphore.cpp:32-37`).
- `XObject::Wait` then sees `GetWaitHandle() == null` and returns SUCCESS without waiting (`xobject.cpp:273-277`). Set/Release dereferences a null host object.
- Today the same lookup blocks on G and gets an initialised object.

**Change (needed for C).** When the fast path is on, hold T exclusive from before `new` to after `InitializeNative` (`xobject.cpp:479-517`), for example with the existing `LockObjectTableForSuspend()`.
- It nests: `AddHandle`'s `TableWriteLock` goes through `table_write_depth_`, and `AddHandle`'s G is a recursive re-entry (G is held from L459).
- The region has no `Release` and takes no other lock; it only creates host objects.
- It runs on first use only, so the cost is negligible.

## Ask 2: `pointer_ref_count_` readers, direct deletes, and what a T-shared lookup can race with

**Reference-count readers.** `pointer_ref_count_` (`xobject.h:237`) is touched only by:
- the constructors, which set it to 1 (`xobject.cpp:94`, `:101`);
- `Retain` (L153-155);
- `Release` (L157-161), which does `delete this` at 0.

The only assert that reads it is commented out (L115). rexlego/src never touches XObjects or the object table.

**Direct deletes.** No XObject is `delete`d directly anywhere in `src/` or rexlego/src.
- The `delete`s found are of vfs files, fibers and dialogs.
- The one XObject-like case is `delete file` in `XFile::Restore` (`xfile.cpp:587-590`), on an XFile built with the kernel-less constructor, which is never in the table.

**Destructors already run without G today.** If a lookup's reference is the last one after a concurrent `NtClose`, these run on that thread:
- `~XThread` (`UnregisterThread` takes G itself);
- `~XFile` (host close);
- `~XObject` (`SystemHeapFree`).

C adds no new destructor context.

**Agent 11's lifetime argument (§3.2) holds, with one exception.**
- Every site that drops the table's reference first nulls the slot under T: `RemoveHandle` L314-338, `PurgeAllObjects` L362-379, `Reset` L126-146.
- No T section contains a `Release`: `AddHandle` (L223-245) and `RestoreHandle` (L561-573) only `Retain`.
- **The exception is today's `RemoveHandle`.** It gets `entry` from `LookupTable` without G (L309), so the nulling at L320 can land in a block that `Resize` has already freed.
- The live slot then still points at O after the table's reference is gone, and the next lookup, through T or G, `Retain`s a freed object.
- **Part A is required before C.**

**Remaining races for T-shared readers (none new):**
- `Restore`/`RestoreHandle` (L549-573) take T but not G. G-holding readers (`GetAllObjects`, `GetObjectsByType`, `Save`, `LookupObject(already_locked)`) race with them. Pre-existing, and save-state only.
- `XObject::handles_` is written under G (`AddHandle` push_back, `RemoveHandle` erase) but read without G by:
  - `handle()`;
  - `RetainHandle`/`ReleaseHandle` (`xobject.cpp:145`, `:150`);
  - `Delete` (L171) and `SetAttributes` (L247);
  - `*handle_ptr = x->handle()` in every NtCreate* (H8).

  C makes `DuplicateHandle` faster but adds no writer.
- A lookup made while `table_write_depth_ > 0` takes the G path. Inside `Restore` (T without G) that would be T → G, which inverts G → T. No such call exists today (`Restore` calls only `Resize`). Add an assert.
- Type confusion from slot reuse is unchanged. `LookupObject<T>` type-checks (`object_table.h:48-59`), but `GetNativeObject` and `LookupObject<XObject>` do not, in either path (C8).

## Ask 5: is part A safe always-on?

**Callers of `RemoveHandle`** (git grep over the SDK and rexlego):
- `ReleaseHandle` (`object_table.cpp:283-299`): holds G. This is `NtClose`.
- `NtDuplicateObject` with `DUPLICATE_CLOSE_SOURCE` (`xboxkrnl_ob.cpp:214-217`): guest export, no lock held.
- `XObject::Delete` (`xobject.cpp:163-173`): **no callers**.

**No new lock edge.** `LookupTable` already takes G (L399) on every call, so every caller already has a caller → G edge. A extends the same region back over `TranslateHandle` (a TLS read for -2, no lock) and `LookupTable`.

**No caller holds a lock that must not be held when acquiring G (H5).**
- `NtDuplicateObject` holds only an `object_ref`.
- The `ReleaseHandle` path holds only G.
- Generated ENTER sections never call exports: all 242 are lwarx/stwcx.-only (`build/agent12/gcr/enter_leave_scan.log`).

**Recursion.** `NtClose` → `ReleaseHandle` → `RemoveHandle` → `LookupTable` reaches depth 3 on one thread, which `std::recursive_mutex` allows. `Release()` and destructors under G (L338, H6) are unchanged from today.

**Perf.**
- Today: two top-level G acquisitions (L309 via `LookupTable`, then L314).
- With A: one top-level acquisition plus one recursive re-entry (an owner-TID compare and `++count`, no interlocked op).
- `NtClose` is unchanged, since it already holds G.
- Net: neutral to slightly faster, with one fewer gap in which another thread can take G.

**Bench (S2, 3 s per scheme, 2 threads):**

| Scheme | Result | Resizes |
|---|---|---|
| G, today's order | 153 stale-entry reads + 153 writes into freed table blocks | 4516 |
| G, A's order | 0 | 6109 |
| G+T, A's order | 0 | — |
| G+T, release first | 2 use-after-free, 2 double-free | — |

**Verdict: safe, land always-on.**

Pre-existing issues in the same function, not blockers for A:
- `DUPLICATE_CLOSE_SOURCE` removes the slot whatever its `handle_ref_count`; `assert_zero` at L322 fires on it in debug builds.
- `NtDuplicateObject(-2, …, CLOSE_SOURCE)` removes the caller's real thread handle (`TranslateHandle` L480-491). NT treats closing a pseudo-handle as a no-op.
- `XObject::Delete` reads `handles_[0]` without G.

## Ask 3: G regions that block on another thread

| G region | Waits for | Does the producer need G? | Effect with B/C |
|---|---|---|---|
| MMIO fault (`mmio_handler.cpp:408`) → data provider → `RetireOnDemandMemexport(true)` (`graphics/d3d12/command_processor.cpp:3219-3237`), H2 | GPU fence, INFINITE | **no**: publish ends the submission first (L3178-3181, comment L3226) | stall only. A B suspender waits for the GPU |
| rexlego `PhysicalDependencyProvider`: cv waits (L111, L115, L229) and `Deliver`'s unlock → settle → relock (L166-188), H3 | the thread producing the data | **yes, at depth ≥ 2**: these drop only one level, so the waiter keeps G (S5: deadlock at depth 2) | already a deadlock. B adds a blocked suspender (the UI thread, if `pause_when_unfocused`) |
| `AudioSystem` Register/Unregister: SDL open/close (`audio_system.cpp:233`, `:282`) | joins the SDL thread | no (the callback takes only `frames_mutex_`) | bounded stall |
| dispatch thread `dispatch_cond_.wait(G)` (`kernel_state.cpp:681-695`) | cv; releases G (depth 1, host thread) | — | safe |
| guest ISR under G (`function_dispatcher.cpp:193`, from vsync `graphics_system.cpp:354` and CP `command_processor.cpp:999`) | whatever the ISR calls | only if an ISR waits (illegal on hardware; not seen) | a B suspender waits for the ISR |
| H7 host I/O and syscalls (`entry.cpp:94/113`, `virtual_file_system.cpp:106`, `content_manager.cpp:344/363/378`, `xmemory.cpp:2130/2195`, rexlego `physical_write_scope.h:15/39`) | disk / kernel | no | stall only |
| generated ENTER sections | — | — | none: 0 of 242 contain a call |

- No G region waits on a guest object: `XObject::Wait`, `WaitMultiple` and `SignalAndWait` take no G (`xobject.cpp:271-388`).
- No G region waits on the UI thread. **B adds a new edge, UI thread → G** (`SetGuestPaused` → guarded `Suspend`), so "never call into the UI thread synchronously while holding G or T" must become a checklist rule.
- C changes none of these regions.

## Ask 4: other suspension and stop paths

| Path | Can it stop a thread inside G or T? | Status |
|---|---|---|
| `NtSuspendThread` (`xboxkrnl_threading.cpp:253`), `KeSuspendThread` (`:1475-1483`), `SetGuestPaused` (`rex_app.cpp:639-648`; at 19:46 the old path is `src/ui/rex_app.cpp:790-813`) → `XThread::Suspend` | not when B is on and target ≠ self | covered by B |
| self-suspend through `NtSuspendThread(current)` (Win32 path) | no: it is called from an export entry, and ENTER sections make no calls | ok |
| `CommandProcessor::Pause` (`graphics/command_processor.cpp:326-339`): the CP host thread suspends itself inside a `CallInThread` callback | no: top of the CP loop, not a guest thread | ok; B does not apply |
| rexlego `sample_profiler.cpp:285-305`: raw `SuspendThread` on **every** thread in the process, then `GetThreadContext` + `Unwind` while it is stopped | yes, for µs. The profiler never takes G or T itself | only lengthens holds. Keep it off for A/B runs (as Agent 11 says) |
| `XThread::Terminate`, non-self (`xthread.cpp:584-587`, `TerminateThread`): only from `AudioSystem::Shutdown` after a timeout (`audio_system.cpp:207-213`) | yes: the worker takes G (L137-140) and runs guest callbacks, which take G or T inside exports | H1: can orphan G, or orphan T held shared (S4 c: writers then block forever). Shutdown only. **S4 g (19:40): killing a thread that is only *waiting* for G also crashes the process.** The next unlock or waiter faults inside ntdll (3 of 3 variants), because the SRW wait block lived on the killed thread's freed stack. Every mfmsr waits on G, so killing this worker can crash the process even when it holds nothing. Follow-up for the audio owner: never `TerminateThread` a thread that uses G. Signal it and wait, or leave it running at exit (C5) |
| `TerminateTitle`: no force-kill any more (`kernel_state.cpp:1038-1040`); self-terminate happens after G is dropped (L1060-1065). Exit from inside G: impossible (no calls in ENTER sections; the ISR runs on a host thread). APCs: user APCs run only in alertable waits, and none happen under G | no | ok |

**H11 (resume needs G)** is fixed for guarded suspends: the target never holds G, so `NtResumeThread` (`LookupObject`) and `KeResumeThread` (`GetNativeObject`) can always take G; with C both need only T shared. Only the profiler (µs) remains.

**Remaining hazard, pre-existing (B on or off): suspend-all, then allocate or log.** B frees only G and T.
- A stopped target can still hold the CRT heap lock, a logging sink mutex, `heap_mutex_`, `file_lock_` or `XFile::unlocked_read_lock_`.
- `SetGuestPaused(true)` logs (L659) and pauses audio (L651-657) after suspending everyone.
- `SetGuestPaused(false)` allocates in `GetObjectsByType` (L639) while every guest thread is still stopped. The UI thread can hang there before it has resumed anyone.
- The profiler already avoids this (`sample_profiler.cpp:306`).
- **Fix:** keep the `object_ref`s from the pause in a member, resume from that list first, then log and handle audio.
- **Implemented (task #17, 19:44)** as cvar `pause_safe_order` (default off) in `src/ui/rex_app.cpp:741-788`. The old path is unchanged at L790-813.
  - Pause: pause audio, snapshot the guest threads (this allocates and takes T), free the snapshot buffer and the non-guest refs, log. Only then run a loop that does nothing but `Suspend`.
  - Unpause: `Resume` the threads that the pause suspended, from the kept list. Then resume audio, log, and drop the refs.
  - The pause picks the path and its unpause follows it, so flipping the cvar mid-pause is safe.
  - Failed suspends keep their refs: a release while threads are stopped could run an `XThread` destructor.
  - Replica stress test: `bench/agent12/pause/`.
  - Debug cvars for test G: `debug_pause_cycle_ms` and `debug_pause_cycle_count`, both 0 = off.
- A guest that suspends another thread can still block on a lock the target holds. That is inherent to host `SuspendThread` (the fully safe answer is cooperative suspension at kernel-call boundaries, as the Linux `SelfSuspend` path does) and unchanged by B.

**B's own window.** The guard holds G and T until `GetThreadContext(CONTEXT_CONTROL)` returns (`threading_win.cpp:260-270`); a target in a kernel path with normal kernel APCs disabled stops late and every mfmsr stalls meanwhile. Acceptable: suspends are rare.

**MSVC facts** (S4 + STL `mutex.cpp:78-160`), unchanged by B: no owner-death detection; the owner is a TID compare (a recycled TID would "own" an orphaned G); a non-owner unlock in release silently decrements the count and can release another thread's SRW lock, so a stray LEAVE breaks exclusion (S4 f: a third thread gets in), and on a free G the next lock/unlock leaves G locked forever.

## Lock order with A+B+C (U = `XFile::unlocked_read_lock_`, see the last section)

- G → T (exclusive) → CRT heap only, plus B's `SuspendThread`/`GetThreadContext`. `name_mutex_` is never taken under T (`RemoveHandle` drops T at L321 before L335), so the order is G → {T, `name_mutex_`}.
- T shared is a leaf (slot read + `Retain`) and must stay one: in S1, Agent 11's write-depth scheme deadlocks on R → R with a queued writer.
- U shared → G (`xfile.cpp:200-201` → `ReadData` → `TriggerCallbacks` `:288-296`; `ReadScatterPositional` `:402-415`); `file_lock_` → U exclusive (`Rename` `:545-549`). **Rule: never take U, in either mode, while holding G or T**: a shared acquire queues behind a waiting `Rename`, which waits for a reader that waits for G. A B-suspended reader can stall a `Rename` but not deadlock (resume never takes `file_lock_`).
- `MayHaveWriteWatches` (`xmemory.cpp:2432`) stays correct only while every watch-bit writer keeps its seq_cst fence before its first data read (`:2147`, `:2267`). A G narrowing must keep all watch-bit writers under one lock.

## Interaction with Agent 12's task #11 changes (all behind cvars that default to false)

- **`XFile::unlocked_read_lock_` ("U", a `std::shared_mutex`, cvar `io_unlocked_file_reads`).**
  - An unlocked positional read takes U shared, then G inside `TriggerCallbacks` (U → G). It releases U before it takes `file_lock_`.
  - `XFile::Rename` takes `file_lock_`, then U exclusive.
  - Nothing takes U while holding G:
    - `xboxkrnl_io*.cpp` never takes G;
    - the only `Rename` caller, `NtSetInformationFile` (`xboxkrnl_io_info.cpp:305`), holds no lock;
    - ENTER sections never call exports.
  - So U adds no cycle with G or T. The existing order `file_lock_` → G (`XFile::Read` → `TriggerCallbacks`) is unchanged.
- **`PhysicalHeap::MayHaveWriteWatches` (cvar `io_lockless_watch_check`)** is a lock-free reader (a seq_cst fence on each side; proof in [agent12-io-memory.md](agent12-io-memory.md), Session 2).
  - It adds no lock edge. It only removes G acquisitions from file reads when no page is watched.
  - The writer-side fence at the end of `EnableAccessCallbacks` is always on and runs under G, as before.
