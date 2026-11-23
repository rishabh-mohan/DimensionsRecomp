# S4 P2: `shared_memory_single_hold_rearm` (Agent 12, task #27 item 4)

**Status:** staged only; not applied, not built. The cvar defaults to OFF.

**Build:** Agent 2 builds it only when Agent 1 schedules it, after the user agrees to the S4 plan, together with C1 (P1) and the u diagnostic.

## Files

| file | what |
|---|---|
| `single-hold-rearm.diff` | Diff against the live `DimensionsRecomp/rexglue-sdk/src/graphics/shared_memory.cpp`. 3 hunks, +30/-0, paths relative to the SDK root. `git -C DimensionsRecomp/rexglue-sdk apply --check` passes (06:41). |
| `orig/shared_memory.cpp` | Copy of the live file (24698 B, LF, git clean; last commit 33470b5; SDK HEAD c5fe668). |
| `new/shared_memory.cpp` | Patched copy (26439 B, LF). |
| `HASHES.txt` | sha256 of all three, the apply order and the sequential apply check. |
| `syntax-20261122-070217.txt` | clang `-fsyntax-only`, pristine vs staged: **PASS** (07:02). Both exit 0 with the same 3 pre-existing warnings and nothing new. |

**sha256:**
- live = orig: `15C89EDB4B197C17487A9D45208D5CE624DE98ABE416F86942C5D14ED43EB282`
- new: `0BE4BADCAC666BEE80F656669D072EDA8B55C2D25D25C448BC4C29E12BD503F4`
- diff: `77BEB64E1325B85451941EA87E33D4371F6EAFB98F7C5E7A37DAE95D29A2F745`

## Apply order (Agent 1, 06:36; C1 is Agent 5's, in `build/agent5/s4-c1/`)

1. **s4-diag:** `src/graphics/d3d12/shared_memory.cpp` B120D07C... -> BB0838CE... (`build/agent12/s4-diag/upload-hash-log.diff`).
2. **s4-p2 (this):** `src/graphics/shared_memory.cpp` 15C89EDB... -> 0BE4BADC....
3. **C1:** its `src/graphics/shared_memory.cpp` is based on P2's `new/shared_memory.cpp` (0BE4BADC...); its other files on the live tree.

The diagnostic and P2 touch different files. Applied in that order to scratch copies outside any repo, both apply cleanly and reproduce the staged files byte for byte. Inside the SDK, `.gitattributes` gives both files `text=auto eol=lf`, so `git apply` writes LF there. Outside a repo, Git's system-wide `core.autocrlf=true` would write CRLF, so the scratch check passes `-c core.autocrlf=false`.

## Change

All three hunks are pure additions; no original line is changed, moved or removed.

1. **Top of file:** `#include <rex/cvar.h>` and `REXCVAR_DEFINE_BOOL(shared_memory_single_hold_rearm, false, "GPU", ...)` at global scope, before `namespace rex::graphics {`. This is the form `primitive_processor.cpp:30` uses.
2. **`RangeWrittenByGpu`** (live :277-293): after the bounds checks, if the cvar is on, take G once (`single_hold_lock`) before `FireWatches` (:288). G is held through `MakeRangeValid` (:292) and released at return.
3. **`MakeRangeValid`** (live :303-336): after the bounds checks, if the cvar is on, take G once before the valid-bit scope (:314-329). G is held through `EnablePhysicalMemoryAccessCallbacks` (:331-335) and released at return.

**Off path:** a `std::unique_lock<std::recursive_mutex>` with no mutex (default-constructed: no lock operation, and its destructor does nothing), one cvar load and one untaken branch per call. The original statements then run unchanged. Early returns (empty or out-of-range calls) come before the addition, so they don't even reach the cvar load.

## Why it saves time

- G (`global_critical_region_`) is the process-wide `std::recursive_mutex`. That is the type `FireWatchesLocked` takes (`const std::unique_lock<std::recursive_mutex>&`, :235), and the profile's wake leaf runs through `_Mtx_unlock`.
- With MSVC's STL, a re-entry by the owner only checks the owner thread id and increments a count. Only the last unlock calls `ReleaseSRWLockExclusive`, and that is the call that wakes a waiter.
- Today a `MakeRangeValid` chunk makes 4 SRW acquire/release pairs: its own scope, then `EnableAccessCallbacks` in each of the 3 views (`xmemory.cpp:2195`, through `EnablePhysicalMemoryAccessCallbacks` at :702-711). A resolve (`RangeWrittenByGpu`) makes 5, because `FireWatches` (:231) comes first. With P2 each makes 1.
- Profile (S4.1 in `perf-notes/agent12-io-memory.md`): the re-arm's `_Mtx_unlock > RtlReleaseSRWLockExclusive > NtSetInformationThread` wake leaf has 4 / 14 samples (a / b).
- **Expected:** about 3/4 of those wakes go, 0.23 (a) / 0.82 (b) ms/f, ~6% of GPU Commands busy, on its own. After P1 it saves only on the re-arms P1 leaves.

## Output-identical argument

- **Same work, same order.** The calling thread runs the same statements in the same order; only the release points between them go.
- **No new behaviour.** Every execution with P2 on is a possible execution of today's code: the one where no other thread takes G in the gaps. SRW locks aren't fair, so today the releasing thread can re-acquire G before a woken waiter runs. P2 removes interleavings and adds none.
  - The interleavings it removes are other threads' G sections landing between the valid bits and the arm, or between `FireWatches` and `MakeRangeValid`. Today's code must already be correct when they don't happen, so taking them away can't change a correct result.
- **Hold time.** The `VirtualProtect(RO)` calls already run under G inside `EnableAccessCallbacks`. G's single hold now also covers the gaps between those sections, which are call overhead, well under a microsecond. G's waiters wait for one longer hold instead of up to four shorter ones; the total hold time is about the same.
- **With the cvar off,** nothing runs that touches shared state (see "Off path").

## Lock order

- P2 takes G at the point where the first inner acquire would take it, with no lock operation in between. G before `heap_mutex_` is the legal order (`xmemory.cpp:1746-1748`).
- `EnableAccessCallbacks` takes G first (:2195), and `EnablePhysicalMemoryAccessCallbacks` takes no lock. `FireWatches` takes only G; its watch callbacks run under G today as well (`FireWatchesLocked`).
- So every lock edge under P2 already exists today: P2 adds none. Any caller lock X taken before these functions already orders X before G today, because the functions acquire G themselves.

## Agent 10 rating checklist

1. **Off path:** 3 hunks, +30/-0, pure additions. The cvar-off cost is the null `unique_lock`, one cvar load and one branch, and nothing touches shared state.
2. **Recursion:** `global_critical_region_.Acquire()` returns `std::unique_lock<std::recursive_mutex>` on the global mutex, and the acquires in `EnableAccessCallbacks` (:2195) and `FireWatches` (:231) lock the same mutex. Re-entry can't deadlock, and only the outermost release wakes anyone.
3. **Lock order:** no new edge (above). Nothing between P2's acquire and the first inner acquire takes another lock.
4. **Waiters:** the longer single hold against G's waiters: XThreads and the Audio Worker in object lookups, VSync and GPU Commands in `ExecuteInterrupt`, Main in sub_82C9DB88.
5. **Interactions:** C1 applies on top of P2's file (apply order above); its fast path in `PhysicalHeap::Protect` takes G for itself, and P2 touches no state that C1 reads. The diagnostic is in another file.
6. **Kill switch:** the cvar is off by default; `--shared_memory_single_hold_rearm=true` turns it on for one run.

## Test plan

1. Agent 2 builds the S4 set (diag, P2, C1) with all cvars OFF. Functional OFF runs must match the baseline (logdiff NEW 0).
2. P2 ON (`--shared_memory_single_hold_rearm=true`): functional devoff and native runs covering the title scene, Agent 3's menu walk and one level load. logdiff NEW 0, no hang or new warning.
3. Agent 8's ABBAAB pair plus one profile: the `EnableAccessCallbacks > _Mtx_unlock > RtlReleaseSRWLockExclusive` samples should drop by about 3/4, and GPU Commands busy by ~0.2-0.8 ms/f.
