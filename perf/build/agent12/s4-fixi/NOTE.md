# S4.7 fix (i): `physical_protect_hold_global_lock` (default OFF)

Agent 12 staged this on 2026-11-22 at 06:57 (task #27 follow-up; Agent 1, 06:48). **It is not applied and not built.** Agent 10 rates it as part of S4, not tonight.

It is a correctness fix, not an output-identical change: behaviour changes only when the race below actually happens.

## Files

| File | sha256 | Notes |
|---|---|---|
| `orig/xmemory.cpp` = live `src/system/xmemory.cpp` | 6E8FA1BA80EF9271D4433DD1BB2CAD0403360E222B22CED78AA4C7951D811DB4 | 107670 B, LF; SDK perf/opt HEAD c5fe668, git clean, last commit 90e7ccd |
| `new/xmemory.cpp` | 141FB1A947D59156EB40A835B27E64F94EE22A3F5BE0E0F70F17BC85C676C87A | 108907 B, LF |
| `protect-hold-g.diff` | 80CAD795EEEF7AD45DBD9DB52ECFFF38C7C7BAF73969FB5DE6FE275EE2F656D9 | 37 lines, 2 hunks, +19/-0 (pure additions) |

- **Apply check:** `git apply --check` on the live SDK exits 0.
- **Sequential apply:** on scratch copies outside the repo, I applied diag, then P2, then fix (i) with `git -c core.autocrlf=false apply`. All three apply cleanly and reproduce the staged files byte for byte (`HASHES.txt`).
- **Syntax: PASS (07:02).** `bench/agent12/s4fixi_syntax.ps1` compiled the pristine and staged copies with the dev-SDK flags. Both exit 0 with the same single pre-existing warning (unused parameter `global_lock_locked_once`, :2273) and nothing new (`syntax-20261122-070230.txt`).
- **Apply chain:**
  1. s4-diag;
  2. s4-p2;
  3. fix (i), `src/system/xmemory.cpp` 6E8FA1BA... -> 141FB1A9...;
  4. Agent 5's C1, whose `xmemory.cpp` must be based on 141FB1A9... and whose `shared_memory.cpp` must be based on P2's 0BE4BADC....

## Change

1. **Cvar.** A new cvar at global scope, after `scribble_heap`: `REXCVAR_DEFINE_BOOL(physical_protect_hold_global_lock, false, "Memory", ...)`.
2. **Second hold.** In `PhysicalHeap::Protect`, right after `auto global_lock = global_critical_region_.Acquire();` (:2130):

   ```cpp
   std::unique_lock<std::recursive_mutex> hold_global_lock;
   if ((protect & memory::kMemoryProtectWrite) && REXCVAR_GET(physical_protect_hold_global_lock)) {
     hold_global_lock = global_critical_region_.Acquire();
   }
   ```

How the hold behaves:
- G is a recursive mutex. TriggerCallbacks takes `global_lock` by value, so its release drops only the inner count.
- G therefore stays held through `parent_heap_->Protect` and `BaseHeap::Protect`. It is released when the function returns, on the error path too (RAII).
- No existing line changes, and no TriggerCallbacks variant is needed. S4.7's first sketch assumed one would be.

## The race it closes (S4.7 form 1; Agent 10 §19, CONFIRMED)

Two threads are involved:
- **Thread A:** the guest thread in MmSetAddressProtect -> `PhysicalHeap::Protect(RW)`.
- **Thread B:** GPU Commands re-arming a watch (MakeRangeValid -> EnablePhysicalMemoryAccessCallbacks -> `PhysicalHeap::EnableAccessCallbacks`).

The sequence:
1. A takes G (:2130). TriggerCallbacks invalidates the range, clears its watch bits (:2416-2427) and releases G when it returns (by-value lock, :2273).
2. B takes G (:2195). The page table still says RW, because this game's protects are RW -> RW (4 / 0x404, Agent 10 §21). So B sets the watch bit, protects the page RO (:2238-2265) and releases G.
3. A's host protects run without G:
   - first the parent heap's view;
   - then `BaseHeap::Protect` -> VirtualProtect(RW) on the virtual view (:1772);
   - then the page-table write (:1788-).

   On Windows, `AcquireHostPageReconcileLock` returns an empty lock (guest page ≥ host page; :968-973, :2481-2487), so neither call takes G.

-> The page now has its watch bit set but is writable:
- Guest writes don't fault, and the GPU keeps the old bytes.
- EAC skips pages whose watch bit is set (:2238-2239), so nothing re-arms the page until the next TriggerCallbacks over it.
- Today the next lock of that block heals it. Under C1, the RW -> RW fast path removes that heal (Agent 10's residual R1, §21). That is why fix (i) lands with C1.

**With fix (i) on**, B blocks at :2195 until A returns. B then sees the bits cleared and the page RW, and arms the page properly.

## Agent 10 checklist

1. **Off path.** With the cvar off, the only new work is one bool cvar load per Write protect and an empty `unique_lock` (it owns no mutex and its destructor does nothing). Every existing line and the lock sequence are unchanged.
2. **Recursion and release.**
   - `global_critical_region_.Acquire()` returns `std::unique_lock<std::recursive_mutex>`, the type TriggerCallbacks takes.
   - The count goes 1 -> 2 -> 1 (TriggerCallbacks returns) -> 0 (function returns).
   - The early `return false` after a parent-heap failure releases it too.
3. **"locked_once".**
   - TriggerCallbacks (:2273-2430) never unlocks its lock early and never waits on another thread. The compiler agrees: clang warns in both syntax compiles that `global_lock_locked_once` is an unused parameter (:2273). The function body never touches the lock; the lock is only destroyed on return.
   - The invalidation callbacks get no lock argument, so a lock held twice changes nothing inside TriggerCallbacks.
   - The devoff callbacks are SharedMemory and PrimitiveProcessor (S4.8). They take G recursively and `cache_mutex_`, and they already run under G today.
4. **Lock order: no new edge.**
   - Without kMemoryProtectWrite, `global_lock` already spans both `parent_heap_->Protect` and `BaseHeap::Protect` (:2130-2143).
   - Decommit and Release hold G across the parent-heap call (:2089-2095, :2104-2110). `BaseHeap::Protect` documents "Global critical region before heap_mutex_" (:1746-1749, :981-983).
   - Every path that takes both locks takes G first (:1241, :1383, :1484, :1624, :1654, :1748, :1987, :2020, :2056). The sites that take only heap_mutex_ take no other lock: DumpMap, GetUnreservedPageCount and the Query* functions (:1126, :1179, :1808-1919).
   - In Protect the two heap mutexes are taken one after the other, never nested.
   - Why this matters more with the cvar on: suppose a heap_mutex_ -> G path did exist. Today's non-Write protects, Decommit and Release would already risk deadlocking against it. Fix (i) would raise that risk from rare to every Write protect, so please confirm that no such path exists.
5. **Hold time.** G is now also held across both host VirtualProtect calls of every Write protect. Today that happens only for non-Write protects.
6. **Side effect.** The page-table write of a Write protect (`current_protect`, :1788-) now happens under G. EAC (:2228-2229) and TriggerCallbacks (:2391) read that field under G, so this is stricter, not looser.

## Cost

- **ON alone:** G is held across the 2 host protects of every Write protect.
  - On Main, those protects are most of MmSetAddressProtect's 0.54 / 1.02 ms/f (a / b; S4.1, mostly VirtualProtect).
  - GPU Commands waits only when it needs G inside one of those windows (RequestRange, UploadRanges, EAC). So the expected stall is well under that figure; the upper bound is the full hold time.
- **With C1 ON:** RW -> RW protects take C1's fast path, which makes no host protect. The hold then covers only the protects C1 leaves (cache-attribute changes that need a host protect, and the native route), so the cost is about 0.
- **Recommendation:** turn it on only together with C1 (Agent 10's gate B). On its own it is a correctness option for a race nobody has observed.

## Test plan

1. **Syntax:** `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent12\s4fixi_syntax.ps1` on the staged copy, and with `-Live` after an apply. Expect `RESULT: PASS`.
2. **OFF** (no cvar set) behaves as today: logdiff NEW 0 and the same frame hash as the S4 base.
3. **ON** with `--physical_protect_hold_global_lock=true`, functional runs only (title, menu walk, a level load). Expect:
   - logdiff NEW 0;
   - no hang (G is held longer, so watch for stalls);
   - no "PhysicalHeap::Protect failed".
4. **With C1** (Agent 10's gates A-D): fix (i) ON plus C1 in verify mode, with 0 mismatches.
5. **Timing,** only as part of the C1 A/B: with C1 on, fix (i) ON vs OFF should be within noise.

## Form-2 fix: design note only (no code)

**The gap** (upstream; Agent 10 §19):
- EAC never watches RO or NoAccess pages (:2231-2239).
- The GPU can still upload such a page and mark it valid: MakeRangeValid sets the valid bits whether or not the watch arms.
- A later Protect that adds Write finds no watch bit, so TriggerCallbacks returns at :2321-2323 without calling the callbacks. The guest's next writes never reach the GPU copy.
- Fix (i) doesn't help here, because there is no watch to race with.

**Design:**
- **Detect.** In `PhysicalHeap::Protect`, while G is held and before the host protects: if `protect & kMemoryProtectWrite`, check whether any guest page in [address, address + size) currently lacks Write. Read `current_protect` under heap_mutex_, taken after G, which is the legal order.
- **Invalidate.** If one does, run the invalidation callbacks for the exact range even when no watch bit is set. Two ways to do it:
  - a `force_callbacks` flag on TriggerCallbacks that skips the any_watched early-out (:2321), with `unwatch_exact_range = true` and `unprotect = false`;
  - or a helper that runs only the callback loop (:2342-2352).
- **Cost.** Only RO / NoAccess -> RW protects pay: one page-table scan plus one callback pass over the range. RW -> RW protects take the old path, and all of this game's protects are RW -> RW (4 / 0x404).
- **Switch.** It gets its own switch, default OFF, for example `physical_protect_invalidate_on_write_grant`. It is not output-identical: it re-uploads ranges that today stay stale.
- **Priority: low.** There is no known trigger in this game (Agent 10's §21 addendum). It is worth doing for correctness, the way upstream would, but not for S4.
- **For Agent 10 to rate:**
  - the forced pass changes no watch bits and no host protection;
  - the callbacks still run under G;
  - the page-table read takes G, then heap_mutex_ (no inversion).
