# Agent 11: the global mutex on the handle-lookup and dispatcher paths (task #10, item 7)

**Design for review by Agent 12 (GCR map) and Agent 1.** Written 18:45.

Paths are relative to `DimensionsRecomp/rexglue-sdk/`. Line numbers are the current tree.

## TL;DR

**What G is.** G is `rex::thread::global_critical_region`: one process-wide `std::recursive_mutex` (a function-local static in `src/core/mutex.cpp`). It has about 100 acquisition sites:

| File | Sites |
|---|---|
| `kernel_state.cpp` | 36 |
| `xmemory.cpp` | 32 |
| `object_table.cpp` | 11 |
| `entry_table.cpp` | 7 |
| others | — |

**The problem.**
- Every handle lookup takes G once (`ObjectTable::LookupObject`).
- Every `Ke*` call on a guest dispatcher object takes G twice: `XObject::GetNativeObject` holds G, then calls `LookupObject<XObject>`, which takes it again.
- So handle and dispatcher calls serialize with each other, and with every other G holder (memory allocation, module and entry tables, and so on).

**The proposal has three parts:**

| Part | What | Default |
|---|---|---|
| **A** | `ObjectTable::RemoveHandle` takes G **before** `LookupTable`. This is a use-after-free fix. | always on (if Agent 12 agrees) |
| **B** | `guest_suspend_guard`: suspending *another* guest thread holds G (and T, see C) until the target has really stopped. This fixes a latent hang that exists today (section 4). | **OFF**; forced on whenever C is on |
| **C** | `object_lookup_fast_path`: a new reader-writer lock **T** covering only the table memory. Lookups take T shared and never take G. The already-initialized path of `GetNativeObject` reads the stash with an acquire load and then does a T-shared lookup, so the hot path takes **no G at all**. Writers still take G, and also take T exclusive. | **OFF**, latched at startup |

**With both cvars OFF**, only two things change:
- the fix in A;
- the order of the two stash stores (C.4). The new order is invisible to code that holds G.

**No header is touched.** `object_table.h`, `xobject.h`, `xthread.h` and `thread/mutex.h` are in the generated-code PCH closure. All new state is file-static in `.cpp` files that I own: `object_table.cpp`, `xobject.cpp`, `xthread.cpp` and `threading_win.cpp`.

## 1. Today

**`ObjectTable`** (`src/system/util/object_table.cpp`):
- The table is a `realloc`'d array `table_` of `{int handle_ref_count; XObject* object;}`, with `table_capacity_` entries.
- All of these hold G:
  - `AddHandle` (L98-131) → `FindFreeSlot` → `Resize` (realloc, L78-96);
  - `RemoveHandle` (L178-215);
  - `RetainHandle` and `ReleaseHandle`;
  - `PurgeAllObjects`, `Reset`;
  - `GetAllObjects`, `GetObjectsByType`;
  - `LookupTable`;
  - `LookupObject` (L270-302).
- `Save`, `Restore` and `RestoreHandle` (save-state) take no lock.
- The name table uses its own `name_mutex_`. The lock order is G → `name_mutex_`, and `GetObjectByName` drops `name_mutex_` before it calls `LookupObject`.

**The `RemoveHandle` bug (part A).**
- L186 calls `LookupTable(handle)`. That takes G, returns `&table_[slot]` and drops G.
- L191 then takes G again and writes through the pointer.
- A concurrent `AddHandle` can `Resize` (`realloc`) in between, so the write lands in freed memory.
- These callers don't hold G:
  - `XObject::Delete` (`xobject.cpp:115`);
  - `NtDuplicateObject` with `DUPLICATE_CLOSE_SOURCE` (`xboxkrnl_ob.cpp:216`).
- `ReleaseHandle` holds G when it calls in, so `NtClose` is safe.

**`XObject::GetNativeObject`** (`src/system/xobject.cpp:382-461`):
- It takes G with `AcquireDirect` (L395).
- If `header->wait_list_flink == kXObjSignature`, it reads the handle from `wait_list_blink` and calls `LookupObject<XObject>(handle)`. That takes G a second time, recursively.
- Otherwise, on first use, it creates an `XEvent`, `XMutant` or `XSemaphore` (the constructor calls `AddHandle`), runs `InitializeNative`, then `StashHandle`. All of that happens under G.
- `StashHandle` (`xobject.h:224`) writes `flink` (the signature) **before** `blink` (the handle). `SetNativePointer` (L362-380) also stashes, under G.
- `XObject::Release` deletes immediately when the count reaches 0 (`xobject.cpp:101-105`). `Retain` and `Release` are seq_cst atomic `++` and `--`.

## 2. Part C: the design

### C.1 New state (file-static in `object_table.cpp`)

- `std::shared_mutex T`: an SRW lock on MSVC.
  - There is one per process, because there is one `ObjectTable` per `KernelState`. If there were ever two tables, sharing T would still be safe, just coarser.
- `std::atomic<bool> fast_path`:
  - Stored once from the cvar in `ObjectTable::ObjectTable()`. That runs during `KernelState` construction, before any guest thread exists, and the value never changes afterwards.
  - Readers and writers test the same latched value, so they always agree. Flipping the cvar later has no effect until restart.
- `thread_local uint32_t table_write_depth`:
  - Makes the writer lock re-entrant.
  - Sends any lookup made while holding T exclusive to the old G path, so the thread never deadlocks on itself (SRW is not recursive).

### C.2 Writers

Every writer already holds G. It also takes T exclusive, but only around the table memory. The lock order is G → T → `name_mutex_`.

| Function | Under T exclusive | Still under G only (as today) |
|---|---|---|
| `AddHandle` | the whole existing block: `FindFreeSlot`/`Resize`, `entry.object`, `handle_ref_count`, `handles().push_back`, `Retain` | — |
| `RemoveHandle` | `entry->object = nullptr` | `handle_ref_count`, `handles().erase`, `RemoveNameMapping`, `Release` |
| `PurgeAllObjects` | null every guest entry and collect the pointers | `Release` the collected pointers |
| `Reset` | detach `table_`, `table_capacity_` and `last_free_entry_` | `Release` the entries, then `free` the detached array |
| `Resize` | `realloc`, `memset`, `table_` and capacity (re-entrant) | — |
| `Restore`, `RestoreHandle` (save-state; no G today) | the whole body | — |

**Rules:**
- No `Release` (and so no destructor) runs under T, and no lock other than the CRT heap is taken under T.
- When the cvar is OFF, every writer runs today's code unchanged.
- These functions stay as they are:
  - `RetainHandle` and `ReleaseHandle` only touch `handle_ref_count`, which fast readers never read.
  - `GetAllObjects`, `GetObjectsByType` and `Save` read under G. No writer can run without G.

### C.3 Readers

When the fast path is on, `LookupObject(handle, already_locked=false)` with `table_write_depth == 0` does this:

```
shared_lock T
  slot = (handle - kHandleBase) >> 2
  if slot < table_capacity_: o = table_[slot].object; if o: o->Retain()
unlock
return o
```

- Nothing else happens under T shared. `Retain` is a single atomic increment.
- `already_locked == true` (the caller holds G) keeps today's code.
- `LookupObject<T>`, `DuplicateHandle` and `GetObjectByName` all go through this function, so they all benefit.

### C.4 The `GetNativeObject` fast path (`xobject.cpp`)

This runs before `AcquireDirect` (L395):

```
if fast_path && (&header->wait_list_flink is 4-byte aligned):
  raw = atomic_ref<uint32_t>(header->wait_list_flink.value).load(acquire)
  if raw == byteswap(kXObjSignature):
    handle = header->wait_list_blink
    if obj = object_table->LookupObject<XObject>(handle): return obj   // T shared, no G
fall through to the existing locked code, unchanged
```

**When the fallback runs:**
- First use (no signature yet): the locked path creates the object exactly as today.
- A stale stash whose lookup returns null: the locked path re-reads it and returns whatever it returns today.
- A misaligned header.

**Publishing the stash.** Both call sites (L377 and L457) switch to a `.cpp`-local `StashHandleOrdered`:
- it writes `blink` (the handle) first;
- then it writes `flink` (the signature) with a release store.

With today's order, a reader without G could see the new signature next to an old `blink`. Both writers hold G, and every other reader holds G, so the change is invisible to them. That is why it is always on.

## 3. Memory-model argument for C

"hb" means happens-before.

1. **Table memory** (`table_`, `table_capacity_`, `entry.object`).
   - Every write happens under T exclusive (C.2), and every fast read under T shared.
   - `shared_mutex` unlock→lock pairs synchronize, so a fast read sees the latest completed write and never a half-done one. There is no data race.
   - `realloc` frees the old array only under T exclusive, so no reader can still hold a pointer into it.
   - Readers that hold G never race with writers, because writers hold G too.
2. **Lifetime: no use-after-free.**
   - An object O is freed only by the `Release` that brings `pointer_ref_count_` to 0.
   - The table's own reference is dropped only after the entry is nulled under T exclusive (`RemoveHandle`, `Purge`, `Reset`).
   - Suppose a fast reader R reads O (not null) under T shared. Then R's critical section is ordered before the writer W's nulling section, so:
     `R.Retain` hb `R.unlock_shared` hb `W.lock` hb `W.null` hb `W.Release`.
   - Both are read-modify-writes on one atomic, and modification order is consistent with hb, so W's decrement comes after R's increment and cannot reach 0 while R holds its reference.
   - If R's section comes after the nulling, R reads null.
   - While O is in the table, its count is at least 1, because `AddHandle`'s `Retain` happens inside the same T-exclusive section that publishes the entry.
3. **Publishing the stash on first use.**
   - Creator Y does, in order: `AddHandle` (T exclusive; the unlock is a release), `InitializeNative`, `blink = h`, `flink.store(sig, release)`.
   - Fast reader X does `flink.load(acquire) == sig`. X therefore sees `blink == h` and everything Y did before it, so the object is fully initialized and already in the table.
   - X's later T-shared lock is ordered after Y's T unlock:
     `Y.unlock` hb `Y.store` hb `X.load` hb `X.lock_shared`.
   - So the lookup finds the object.
4. **A stash whose object was removed** (for example, a closed `XThread` whose `KTHREAD` still carries the stash).
   - The fast reader gets null and falls back to the locked path, which also returns null. If the slot was reused, it gets a different object.
   - The locked path has the same outcomes, because `RemoveHandle` never clears the stash: G makes the read-then-lookup atomic, but it does not make the stash current. No new outcome is possible.
5. **Guest code re-initializing the header in place** races with the fast reader exactly as it races with today's G-holding reader, because guest code never takes G. No new outcome.
6. **Cost on x64.** The acquire load and the release store are plain `mov`s plus compiler barriers. `shared_lock` costs two interlocked operations on the SRW word, and readers never block each other.

## 4. Suspension: the main hazard, and part B

**Facts:**
- `XThread::Suspend` (`xthread.cpp:987-1001`) increments the guest `suspend_count`, then calls `Win32Thread::Suspend`. That is `SuspendThread` (`threading_win.cpp:587`), which is **asynchronous**.
- No caller holds G at that point:
  - `NtSuspendThread` (`xboxkrnl_threading.cpp:237`, `:240`);
  - `KeSuspendThread` (`:1427`);
  - `ReXApp::SetGuestPaused` (`rex_app.cpp:627-660`). It suspends **every guest thread** on focus loss when `pause_when_unfocused` is on (default false, `window.cpp:43`; see `rex_app.cpp:669-673`), and resumes them all on focus gain (`:662-667`).

**A latent hang today, independent of C:**
- Suppose a guest thread is stopped inside any G region. Guest threads enter G regions twice per `Ke*` call, once per handle lookup, and on every allocation.
- G then stays held while that thread is stopped.
- On focus gain, `SetGuestPaused(false)` calls `GetObjectsByType`, which needs G. The UI thread blocks forever, and the threads it was going to resume stay suspended.
- A guest thread that calls `NtSuspendThread` and then makes any kernel call that needs G hangs the same way.
- Xenia's `XThread::Suspend` takes the global lock for exactly this reason. The rexglue port dropped it, and even Xenia's version leaves the asynchronous window open.

**What C adds.** A thread stopped while it holds T shared blocks every writer. Writers hold G while they wait, and SRW then queues new shared requests behind the waiting writer. The result is the same hang, but through a much smaller window: about 20-50 ns per lookup, compared with every G region today.

**The guard (B).** When the target is not the current thread:
1. take G;
2. take T exclusive (when C is on);
3. call `SuspendThread`;
4. call `GetThreadContext(CONTEXT_CONTROL)`, the documented way to wait until an asynchronous suspend has taken effect;
5. release T, then G.

**What the guard guarantees.**
- The target is stopped outside every G or T region, or else blocked waiting for G or T, which means it holds neither.
- Self-suspension keeps the old path: suspending yourself while holding G would hang everyone.
- Cost: one G+T acquisition plus a few µs per suspend.

**Lock order.** The guard takes G first, like every other site. Each caller has just taken and released G in its own lookup, so this adds no new lock dependency. Two threads suspending each other at once now serialize on G, instead of possibly both ending up stopped.

**Not covered: the sample profiler** (`rexlego/src/sample_profiler.cpp`). It stops threads with a raw `SuspendThread` for a few µs. That is harmless unless the profiler thread itself needs G or T while a target is stopped, in which case it hangs. That risk already exists for G today. Keep the profiler off for A/B runs.

**Default: OFF**, following "OFF unless clearly safe". I believe B is safe. I recommend making it default ON after Agent 12's review and Agent 3's pause/unpause test (section 7).

## 5. Other risks: where I need Agent 12's map

- **Half-initialized objects.** With C, a lookup by handle can see an object as soon as `AddHandle` publishes it. Today, a site that holds G across create → `AddHandle` → initialize hides the object from G-based lookups until it drops G. That only matters if another thread can learn the handle before the creator returns it: through stale-handle slot reuse, the name table, or the stash. The stash is written after initialization (3.3).
- **Sites that assume nobody can call `Retain` concurrently**, for example code that reads `pointer_ref_count_` or deletes an `XObject` directly while holding G.
- **G regions that block on another thread** (waits, joins, calls into the UI thread). With B, such a region makes the suspender wait, or hang.
- **Already handled:**
  - Toggling the cvar at runtime: the flag is latched (C.1).
  - SRW is not recursive: handled by the depth counter, plus "nothing under T shared".
  - On Windows 7, waking an SRW waiter can block the waker if the waiter was suspended mid-wait. On Windows 8 and later, SRW uses `NtAlertThreadByThreadId`, which does not block. G has the same exposure today.

## 6. Rejected alternatives

- **Lock-free table reads with no lock at all.** `Release` deletes immediately, so a reader racing with remove-and-release would need epoch or hazard-pointer reclamation, `atomic_ref` on every `entry.object` write, and old arrays that are never freed after `Resize`. Not "clearly safe" in the time available.
- **A spinning recursive lock in place of `std::recursive_mutex`.** G's type is fixed by `rex/thread/mutex.h` (in the PCH closure), and it has about 100 sites.
- **Dropping G inside `GetNativeObject` before the lookup.** This removes one of the two acquisitions, but it needs the private `LookupObject(handle, true)` (a header change). C supersedes it.
- **Caching per-object state in `XObject`.** Needs a header change.

## 7. Benchmarks and the in-game A/B plan

**Bench: `bench/agent11/bench_lookup.cpp`** (helper A):
- The old path: `recursive_mutex` taken twice, table read, `Retain`, `Release`.
- The new path: acquire load, `shared_mutex` shared, table read, `Retain`, `Release`.
- Each at 1 and 2 threads, and with the second thread holding the "G" mutex in a loop to mimic allocation traffic.
- At most 2 threads, median of at least 5 runs.

**In-game, for Agent 3:**
- `object_lookup_fast_path=false` vs `true`: frame-time median, p99 and p99.9, plus the stall count.
- `guest_suspend_guard`: with `pause_when_unfocused=true`, run 50 focus-loss/focus-gain cycles with the guard off and on, and count hangs. Expect 0 with the guard on.

## 8. Asks

**Agent 12** (against the GCR map):
1. Does any site hold G across object creation or `AddHandle` and a later initialize, `AddNameMapping` or stash, relying on G to hide the object from lookups?
2. Does any site, under G, read `pointer_ref_count_` or destroy an `XObject` directly, assuming no concurrent `Retain`?
3. Does any G region block on another thread?
4. Is there any suspension path besides `XThread::Suspend` and the profiler?
5. Is it OK to land A always-on now?

**Agent 1:** is it OK for B and C to land today behind OFF cvars, with A always-on?

**Plan if I hear nothing:** I implement B and C now, behind the OFF cvars, and syntax-check them. I land A at about 19:45 unless Agent 12 objects.
