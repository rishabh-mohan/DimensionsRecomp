# Agent 11 helper B: CS spin (Task #10 item 3) + kernel spinlock TTAS (item 4)

## RESUME (final, 19:05, session 4)

**State: DONE. Both SDK edits are in and pass compile-one -SyntaxOnly. Every new cvar defaults OFF (orchestrator rule, 18:50). Benches done. These notes are final. The summary went to Agent 11.**
- Files written:
  - `DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_rtl.cpp` (+66 lines)
  - `DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_threading.cpp` (+55 lines)
  - Both edits are purely additive: `git diff --stat` shows 121 insertions and 0 deletions.
  - `bench/agent11/bench_cs.cpp`, `bench/agent11/bench_spinlock.cpp`, `build/agent11/b/*` and this file.
- Cvars:
  - `cs_spin` = false
  - `cs_spin_ns` = 5000 (only read when `cs_spin` is on)
  - `spinlock_pause_spin` = false
  - Recommended for Agent 3's A/B: `cs_spin=true` and `spinlock_pause_spin=true`.
- Compile check after the edits (defaults OFF; logs `build/agent11/b/after2_*.log`):
  - rtl: exit 0 in 20.9 s;
  - threading: exit 0 in 30.2 s;
  - only the baseline warnings, at shifted lines.
- Bench CPU in total: about 240 CPU-s (4 CPU-min), against a budget of about 10 CPU-min.
- If resumed: nothing is pending. Do not run benches or compiles between 20:12 and Agent 11's "quiet window over" message.

## What changed and why

### Item 3: RtlEnterCriticalSection spin (`cs_spin`, `cs_spin_ns`)

Before this change, a contended Enter with the default guest spin count of 0 went straight to `atomic_inc` and a kernel wait. That path takes the global critical region twice, retains the object and waits on a Win32 event; the Leave side does the matching set. Even a 50 ns hold therefore paid a full kernel sleep/wake round trip on every collision.

With `cs_spin` on, `SpinForCriticalSection` runs first:
1. One CAS -1 -> 0. This is the same CAS the original guest-spin loop does.
2. Then, until the time bound and the guest spin count are both used up:
   - `_mm_pause`;
   - a plain read;
   - the CAS again, only when the read shows -1.
3. If the spin fails, the original loop runs with `spin_count = 0` (a no-op), followed by the unchanged `atomic_inc` / wait path.

Design points:
- **Hand-off is intact.** After a Leave with waiters, `lock_count` stays >= 0 until the woken waiter runs. The only operation a spinner tries is the -1 -> 0 CAS, so it cannot barge past a handed-off lock.
- **Time bound instead of an iteration count (`cs_spin_ns` replaces the planned `cs_spin_count`).**
  - Measured cost of one pause+read iteration: 129-149 ns on the P-cores and on E cluster 0 (cpu4: 134 ns), but 54-61 ns on E cluster 1.
  - That spread (2.4-2.8x) comes on top of load-dependent clocks, so an iteration count would give a very different spin time per core.
  - The deadline uses `std::chrono::steady_clock` (QPC on MSVC STL; 40-114 ns per call) and is checked every 16 pauses, which adds 7% or less to the spin.
  - steady_clock was chosen over `rex::chrono::Clock` so there is no link or export dependency (rexcore is an OBJECT library, rexruntime is SHARED).
- **5000 ns:** the top of the target range of about 2-5 us. Round 2 showed 5000 beating 2000 and 3000, and round 3 showed `time:3000` clearly worse at 2000/5000 ns holds.
- **Guest spin count: the larger of the two.** The spin ends only when `i >= header.absolute*256` and the deadline has passed. With `cs_spin` on, the guest count is spent on pause iterations instead of tight CAS attempts.
- **CAS first, not read first (a deviation from "CAS only after a read shows -1").**
  - The read-only rule applies inside the loop.
  - The single up-front CAS is hand-off safe, because it fails on a handed-off lock.
  - The read-first alternative (`time:` in `cs_contended_3.txt`) had 3-25x more kernel waits. A stale "free" read on a contended line commits the thread to `atomic_inc` and then to a kernel wait. Examples: none/50 had 13847 vs 529 kernel waits per 1M acquires; ee/50 had 45048 vs 3570.
  - Read-first also cost +2.4-2.6 ns per uncontended pair on the P-cores.

### Item 4: kernel spinlock TTAS (`spinlock_pause_spin`)

Before this change, `xeKeKfAcquireSpinLock` ran `while (!cas(0, self)) MaybeYield();`, which calls SwitchToThread after every failed CAS. On a loaded machine SwitchToThread gives the core away for 0.3 us to 0.7 ms (`cs_info.txt`), so a waiter could come back milliseconds after the lock was freed.

With `spinlock_pause_spin` on, `AcquireSpinLockPauseSpin` runs instead:
1. One CAS.
2. Then a loop of pause and plain read until the lock reads free, followed by the CAS again.
3. `MaybeYield` is called only after 10 us of pausing (`kSpinLockYieldAfter`, a constexpr; steady_clock is checked every 32 pauses), and then again after each further 10 us.

Coverage:
- `xeKeKfAcquireSpinLock` is the only acquire loop of the CAS+MaybeYield shape. It serves KfAcquireSpinLock, KeAcquireSpinLockAtRaisedIrql, InsertQueueApc and the ExReadWriteLock code, plus its callers in kernel_state.cpp and xthread.cpp.
- Left alone:
  - KeTryToAcquireSpinLockAtRaisedIrql (L1119-1123) and the ExTryToAcquireReadWriteLock* functions (L1314, L1347): single tries;
  - NtYieldExecution (L405-406);
  - the SList CAS loops (L1416, L1439, L1457).

The 10 us yield bound sits at the top of the 5-10 us range. In round 4, 5 us and 10 us were mixed: 5 us gave a better average wait in none/ee/pe, 10 us gave fewer yields and better pp throughput. 10 us was kept as a constexpr to keep the cvar surface small.

### Game side: no double spin

- `rexlego/src/native_lock_elide.cpp` only elides the guest global lock around lwarx/stwcx. Its CS calls go straight to `__imp__RtlEnterCriticalSection` / `__imp__RtlLeaveCriticalSection`.
- `crash_guards.cpp` (L218, L343) does the same.
- Nothing game-side hooks KfAcquireSpinLock.
- `native_heap_journal.h` has its own unrelated `_mm_pause` lock.

## Diff summary (post-edit line numbers)

`xboxkrnl_rtl.cpp`:
- L16: `#include <chrono>`.
- L18-22: `<immintrin.h>` on x86/x64, otherwise `<thread>`.
- L50-61: `REXCVAR_DEFINE_BOOL(cs_spin, false, "Kernel", ...)` and `REXCVAR_DEFINE_UINT32(cs_spin_ns, 5000, "Kernel", ...)`.
- L412-449, in the existing anonymous namespace: `CpuRelax()` and `SpinForCriticalSection(cs, spin_count)`.
- L464-472, in `RtlEnterCriticalSection_entry` before the original `while (spin_count--)`:
  `if (REXCVAR_GET(cs_spin)) { if (SpinForCriticalSection(...)) { set owner; recursion_count = 1; return; } spin_count = 0; }`.
- The original loop, the wait path, TryEnter and Leave are untouched.

`xboxkrnl_threading.cpp`:
- L20-24: `<immintrin.h>` or `<thread>`.
- L27: `#include <rex/cvar.h>`.
- L48-54: `REXCVAR_DEFINE_BOOL(spinlock_pause_spin, false, "Kernel", ...)`.
- L978-1014, in a new anonymous namespace: `CpuRelax()`, `kSpinLockYieldAfter{10000}` and `AcquireSpinLockPauseSpin(owner, self)`.
- L1023-1026, in `xeKeKfAcquireSpinLock` after the self-deadlock assert:
  `if (REXCVAR_GET(spinlock_pause_spin)) { AcquireSpinLockPauseSpin(...); return old_irql; }`.
- The original loop follows untouched.

With a cvar off, the only difference from the old code is one read of the cvar storage and one branch per call. That is the same pattern as every other cvar.

## Cvars

| cvar | type | default | meaning | recommended for the A/B |
|---|---|---|---|---|
| `cs_spin` | bool | **false** | Spin before a contended RtlEnterCriticalSection blocks | true |
| `cs_spin_ns` | uint32 | 5000 | Spin time bound in ns, used with `cs_spin`; 0 = spin for the guest's spin count only | 5000 |
| `spinlock_pause_spin` | bool | **false** | TTAS pause loop for guest kernel spinlocks; yield only after 10 us | true |

All three are hot-reload cvars and are read on every call, so flipping them at runtime is safe. Both settings use the same lock protocol, so on and off can mix.

The defaults were true until the 18:50 orchestrator rule: every new cvar defaults OFF unless proven identical. `cs_spin_ns` keeps 5000 because it has no effect while `cs_spin` is off.

## Bench method

- Benches are single-file replicas of the SDK code, built with `cl /O2`:
  - the CS: Enter/Leave, plus the kernel wait/set path with GetNativeObject's global critical region, object retain/release, an auto-reset event and 5 s wait slices;
  - the spinlock: byte-swapped PCR owner and a fake-PCR IRQL raise/lower;
  - the interlocked helpers are out of line, as in `src/core/atomic_win.cpp`.
- Variants with a `:N` suffix carry a parameter; a `#tag` suffix makes an A/A copy of a variant.
  - `old`: the current code.
  - `timecas:NS` / `ttast:NS`: the exact SDK shape with the cvar on.
  - `off:NS` / `off`: the SDK shape with the cvar off.
- **paired** (uncontended): one pinned thread runs batches of every variant, interleaved over 300 rounds of 20000 pairs per variant per core class. It reports the median and the median paired difference against `old`. This holds up on a loaded machine.
- **contended**: 2 threads, 100 ms (CS) or 150 ms (spinlock) per run, runs interleaved rep-major, medians of 5-9 reps.
  - Affinities:
    - none = scheduler's choice;
    - pp = P-core 0 vs P-core 1 (0x3/0xC);
    - ee = E cluster 0 vs E cluster 1 (0xF0/0xF00);
    - pe = any P vs any E (0xF/0xFF0).
  - Mutual exclusion is checked in every contended run (OK in all of them).
- Environment for every run: on AC (BatteryStatus=2, ACLineStatus=1, battery 100%), CPU load 62-100% from the other agents, TSC 2.611 GHz, QPC 10 MHz, timer resolution 1 ms. Absolute numbers are inflated by the load; the paired and A/A design is there to cope with it.
- At most 2 threads, one bench at a time (the named mutex in bench_common.h).

## Results

### info (`cs_info.txt`): cost of a single operation per core

| cpu | type | pause | pause+read | QPC | SwitchToThread (under load) |
|---|---|---|---|---|---|
| 0 | P0 | 100 ns | 149 ns | 40 ns | 10.8 us |
| 1 | P0 (SMT) | 114 ns | 132 ns | 44 ns | 45 us |
| 2 | P1 | 126 ns | 129 ns | 50 ns | 0.3 us |
| 4 | E cluster 0 | 92 ns | 134 ns | 114 ns | 100 us |
| 8 | E cluster 1 | 53 ns | 54 ns | 65 ns | 312 us |
| 11 | E cluster 1 | 64 ns | 61 ns | 61 ns | 672 us |

### Uncontended cost (paired; ns per Enter+Leave or acquire+release)

The difference columns show the median paired difference against `old`. **CS (must be unchanged):**

| file (load) | core | old | off:5000 (cvar off) | timecas:5000 (cvar on) | time:5000 (read-first) | old#aa (A/A) |
|---|---|---|---|---|---|---|
| cs_paired_3 (100%) | P | 33.43 | - | +0.32 | +2.55 | -0.00 |
| cs_paired_3 (100%) | E | 34.75 | - | -1.57 | +0.42 | -0.15 |
| cs_paired_4 (71%) | P | 30.49 | +0.29 | +1.28 | - | -0.03 |
| cs_paired_4 (71%) | E | 34.06 | +1.90 | -1.56 | - | -0.24 |

- The A/A controls stay within 0.24 ns.
- **Cvar on vs old:** -1.6 to +1.3 ns per pair. The E-core result is -1.6 ns in all three rounds (round 3, `cs_paired_2`: P +0.35, E -1.58). This is a stable code-layout effect of a separate function body, not extra work: the on path swaps `lock xadd` for `lock cmpxchg`.
- **Cvar off vs old:** +0.3 ns (P) and +1.9 ns (E) per pair, i.e. 1-6%. The off path executes one extra load and one predictable branch. The replica cannot resolve layout effects of about ±2 ns between paths, and clang's code generation in the SDK will differ from this MSVC replica in any case.

**Spinlock:**

| file (load) | core | old | off (cvar off) | ttast:10000 (cvar on) | old#aa (A/A) |
|---|---|---|---|---|---|
| sl_paired_3 (100%) | P | 27.82 | - | -0.08 | +0.12 |
| sl_paired_3 (100%) | E | 29.28 | - | -0.02 | +0.02 |
| sl_paired_4 (62%) | P | 39.12 | -0.23 | -0.38 | -0.10 |
| sl_paired_4 (62%) | E | 37.67 | +0.03 | +0.11 | -0.12 |

The spinlock's uncontended cost is identical within the A/A noise, both on and off.

### CS contended: 2 threads, old -> timecas:5000 (the SDK shape with `cs_spin` on)

ns/op is wall time per acquire, both threads combined. Kernel waits are counted per 1M acquires. CPU is thread cycle time per op.

Round 4 (`cs_contended_4.txt`: 5 reps × 100 ms, gap 200 ns, load 100 -> 85%; 19.2 CPU-s):

| aff / hold | ns/op old -> new | speed-up | kernel waits/1M old -> new | cpu ns/op old -> new |
|---|---|---|---|---|
| none / 50 | 5834 -> 260 | 22x | 257457 -> 254 | 4110 -> 454 |
| none / 500 | 14776 -> 1025 | 14x | 826331 -> 1601 | 12200 -> 1268 |
| none / 2000 | 17272 -> 4504 | 3.8x | 835220 -> 78771 | 11752 -> 5598 |
| none / 5000 | 20817 -> 15388 | 1.35x | 972333 -> 496446 | 16454 -> 15683 |
| pp / 50 | 34776 -> 1316 | 26x | 376393 -> 162 | 3029 -> 413 |
| pp / 500 | 10413 -> 1120 | 9.3x | 750000 -> 2067 | 7123 -> 1352 |
| pp / 2000 | 21265 -> 12737 | 1.7x | 885962 -> 23051 | 7632 -> 4424 |
| pp / 5000 | 52606 -> 100908 | 0.52x (outlier, see round 5) | 741030 -> 472441 | 9292 -> 13587 |
| ee / 50 | 38739 -> 367 | 106x | 837412 -> 2029 | 13333 -> 523 |
| ee / 500 | 23646 -> 1388 | 17x | 945293 -> 18794 | 14658 -> 1933 |
| ee / 2000 | 28977 -> 5281 | 5.5x | 900327 -> 132814 | 14441 -> 6758 |
| ee / 5000 | 32964 -> 19236 | 1.7x | 949746 -> 644860 | 18241 -> 20246 |
| pe / 50 | 12799 -> 336 | 38x | 698541 -> 194 | 8197 -> 432 |
| pe / 500 | 12117 -> 973 | 12x | 419699 -> 1644 | 6153 -> 1290 |
| pe / 2000 | 18043 -> 4839 | 3.7x | 693450 -> 8203 | 9813 -> 4541 |
| pe / 5000 | 21797 -> 11920 | 1.8x | 978338 -> 356285 | 15698 -> 14014 |

Round 5 (`cs_contended_5.txt`: 7 reps, re-running the long-hold cells; load 68 -> 99%; 8.4 CPU-s):

| aff / hold | ns/op old -> new | speed-up | kernel waits/1M old -> new | cpu ns/op old -> new |
|---|---|---|---|---|
| none / 2000 | 25041 -> 4079 | 6.1x | 982740 -> 72416 | 17115 -> 5945 |
| none / 5000 | 29524 -> 15054 | 2.0x | 989199 -> 325618 | 20518 -> 16061 |
| pp / 2000 | 22434 -> 5013 | 4.5x | 923441 -> 71929 | 9586 -> 5201 |
| pp / 5000 | 25475 -> 14542 | 1.75x | 960791 -> 551265 | 12868 -> 15265 (+19%) |
| ee / 2000 | 31237 -> 5874 | 5.3x | 944198 -> 128640 | 20904 -> 7495 |
| ee / 5000 | 36391 -> 19823 | 1.8x | 993690 -> 569221 | 24796 -> 20791 |

- The round 4 pp/5000 regression did not reproduce. That cell was dominated by machine noise: the old variant's max was 2.8 s and the new one's 0.79 s.
- **50 and 500 ns holds:** 9-106x faster, kernel waits cut 100-1500x, and less CPU per op, because a kernel sleep/wake costs more CPU than a 5 us spin.
- **2000 ns holds:** 1.7-6x faster, with less CPU.
- **5000 ns holds:** 1.35-2x faster, at -15% to +19% CPU.
- Earlier rounds (`cs_contended_1..3.txt`, a QPC deadline) show the same picture.

### Spinlock contended: `sl_contended_3.txt`

Setup: 2 threads, 9 reps × 150 ms, hold 100 ns with every 500th hold 20 us, gap 200 ns; load 80 -> 100%; 17.4 CPU-s.

"Contended" means an acquire that failed at least one CAS. Wait is that acquire's latency. p50 and p99 come from a log2×4 histogram (about ±12%).

| aff | variant | ns/acq | cpu ns/acq | yields/1M | contended/1M | wait avg | wait p50 | wait p99 | fair |
|---|---|---|---|---|---|---|---|---|---|
| none | old | 775 | 635 | 332 | 185 | 3.52 ms | 3.21 ms | 16.1 ms | 0.371 |
| none | ttast:5000 | 643 | 678 | 479 | 63659 | 9.2 us | 588 ns | 1.57 us | 0.474 |
| none | ttast:10000 | 739 | 625 | 254 | 43249 | 17.2 us | 588 ns | 2.35 us | 0.352 |
| pp | old | 1272 | 627 | 84977 | 40475 | 23.7 us | 686 ns | 9.41 us | 0.399 |
| pp | ttast:5000 | 1078 | 659 | 473 | 92943 | 9.0 us | 588 ns | 1.37 us | 0.415 |
| pp | ttast:10000 | 939 | 658 | 484 | 58487 | 12.2 us | 588 ns | 1.57 us | 0.338 |
| ee | old | 814 | 645 | 1417 | 787 | 1.15 ms | 151 us | 16.1 ms | 0.424 |
| ee | ttast:5000 | 771 | 787 | 761 | 113384 | 7.0 us | 686 ns | 1.96 us | 0.460 |
| ee | ttast:10000 | 776 | 773 | 725 | 100014 | 7.9 us | 686 ns | 1.96 us | 0.441 |
| pe | old | 820 | 607 | 157 | 81 | 9.79 ms | 8.03 ms | 38.6 ms | 0.215 |
| pe | ttast:5000 | 807 | 648 | 217 | 22797 | 25.5 us | 588 ns | 2.35 us | 0.254 |
| pe | ttast:10000 | 759 | 622 | 81 | 16757 | 43.2 us | 588 ns | 2.75 us | 0.289 |

- **Old loop:** contended acquires are rare, but each one waits milliseconds (none/ee/pe: p50 0.15-8 ms). The waiter's SwitchToThread hands the core away, and the waiter returns long after the lock was freed.
- **TTAS:** p50 588-686 ns and p99 1.4-2.8 us.
  - Throughput is the same or better: 5-26% fewer ns per acquire for ttast:10000.
  - CPU per acquire is 0-20% higher.
  - More acquires count as contended, because the waiter stays on the core and competes instead of sleeping.
- wait_max is 14-50 ms for every variant: the owner is preempted on the overloaded machine.
- Round 3 (`sl_contended_2.txt`, a QPC deadline) gave the same direction: yields down 20-170x and p50 waits about 300 ns. One ee p99 was worse for ttast:5000.

## Compile checks (clang via the build/sdk-dev compile database)

Commands:
```
powershell -NoProfile -File env\compile-one.ps1 DimensionsRecomp\rexglue-sdk\src\kernel\xboxkrnl\xboxkrnl_rtl.cpp -OutDir build\agent11\b\obj -SyntaxOnly
powershell -NoProfile -File env\compile-one.ps1 DimensionsRecomp\rexglue-sdk\src\kernel\xboxkrnl\xboxkrnl_threading.cpp -OutDir build\agent11\b\obj -SyntaxOnly
```

| file | baseline (before edits) | after (final, defaults OFF) |
|---|---|---|
| xboxkrnl_rtl.cpp | exit 0, 19.8 s, 2 warnings (L124/L125 `-Wunused-but-set-variable` `len1`/`len2`) | exit 0, 20.9 s, the same 2 warnings at L142/L143 |
| xboxkrnl_threading.cpp | exit 0, 23.3 s, 6 warnings (`-Wmissing-braces` + `-Wmissing-field-initializers` at L1371/L1372/L1394) | exit 0, 30.2 s, the same 6 warnings at L1426/L1427/L1449 |

- There are no new warnings; in particular, no `-Waddress-of-packed-member` on the volatile `lock_count` pointer.
- Logs: `build/agent11/b/baseline_*.log`, `after_*.log` (defaults true) and `after2_*.log` (final).
- The "PCH not built" stderr note that appears in the logs is harmless.

## Risks

1. **Preempted owner (CS).** A spinner burns up to `cs_spin_ns` (5 us) per contended Enter before it blocks, even when the owner is descheduled. The cost is bounded and small next to a kernel sleep/wake.
2. **Long holds of 5 us or more.** The spin often expires, then the original wait follows. Wall time is still 1.35-2x better, but CPU per op ranges from -15% to +19%. At holds well above 5 us the spin is pure overhead, up to 5 us per contended Enter.
3. **Large guest spin counts with `cs_spin` on.** The spin lasts the larger of the guest count (in pause iterations, 54-149 ns each) and `cs_spin_ns`.
   - A guest count of 4096 means about 0.2-0.6 ms of spinning; the maximum, 255*256 = 65280, means about 3.5-9.7 ms.
   - The old tight CAS loop with the same count runs for a similar order of time, about 20-100 ns per failed CAS on a contended line.
   - If this matters, cap the guest count in pause units. The parent asked for "the larger of the two", so there is no cap now.
4. **Oversubscribed host.** Spinning takes CPU from other runnable threads. With TTAS spinlocks this costs 0-20% more CPU per acquire.
5. **steady_clock cost.** It is about 40-114 ns per call here (invariant TSC behind QPC). On hosts without an invariant TSC, QPC can cost microseconds; it is still called only once per 16 or 32 pauses.
6. **Non-x86 builds:** `CpuRelax` falls back to `std::this_thread::yield()`, which is heavier than a pause but correct.
7. The spinlock yield bound (10 us) is a constexpr, not a cvar.
8. All numbers were taken at 62-100% machine load. Agent 3's in-game A/B, flipping the two bool cvars, is the real test.
