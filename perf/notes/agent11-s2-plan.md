# Agent 11: Session 2 implementation plan for task #10 (resume file)

Written at 16:55 for the agy-grid restart pause. SDK paths are relative to `DimensionsRecomp/rexglue-sdk/`, and line numbers are as of `2897c31`.

## Ground rules (from the task and from Agent 1)

- **Owned files only.**
- **Do not edit headers in the generated-code PCH closure.** They are `rex/thread.h`, `rex/system/xobject.h`, `rex/system/util/object_table.h`, `rex/system/kernel_state.h`, `rex/chrono/clock.h`, `rex/thread/mutex.h` and `thread_state.h`. Leave `rex/system/xthread.h` alone too.
- **Not owned:** `include/rex/codegen/*` and `src/codegen/*`. Another agent has those modified.
- **Item 7 (global mutex).** Before landing anything:
  - Write `perf-notes/agent11-global-mutex-design.md`.
  - Message Agent 12 (job J3 reviewer) and Agent 1.
  - The toggle stays OFF by default.
- **Benches:** in `bench/agent11`, at most 2 threads, median of at least 5 runs. Outputs go only to `build/agent11/`.
- **Compile-check:** `powershell -NoProfile -File env\compile-one.ps1 <src> -OutDir build\agent11\obj -SyntaxOnly`. Exit code 2 means the file lookup failed.
- **Bench build:** `. .\env\devshell.ps1; cl /nologo /O2 /std:c++20 /EHsc /W3 X.cpp /Fe:build\agent11\X.exe /Fo:build\agent11\ winmm.lib`
- **Subagent split:**
  - Subagent B owns items 3 and 4: `src/kernel/xboxkrnl/xboxkrnl_rtl.cpp` and `xboxkrnl_threading.cpp`, plus `bench_cs.cpp`, `bench_spinlock.cpp` and `perf-notes/agent11-s2-cs-spinlock.md`.
  - Subagent A owns the benches: `bench_sleep.cpp`, `timer_highres_check.cpp`, `bench_clock.cpp`, `bench_waitsignal.cpp`, plus `perf-notes/agent11-s2-benches.md`.
  - Both may be gone after the restart. Read their RESUME blocks and redo the work if needed.

## Done

- `include/rex/threading_timeout.h`: constexpr NT-timeout helpers.
  - `NtTimeoutToRelative100ns`
  - `Relative100nsToMillis`: rounds up and saturates at 0xFFFFFFFE.
  - `Relative100nsToMicros`: rounds up.
  - `NtTimeoutToMillis`
- `include/rex/threading_timing.h`:
  - `HostTimingConfig`
  - `ConfigureHostTiming` and `RestoreHostTiming`
  - `AlertableSleepPrecise`
- Nothing includes either header yet.

## Steps (in order)

### 1. `src/core/threading_win.cpp`

**Includes.** Add `#include <rex/threading_timing.h>` after `<rex/thread.h>`, and `<algorithm>` and `<atomic>` before spdlog. After `platform_win.h` add:

```cpp
#ifndef PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION
#define PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION 0x4
#endif
```

**Replace L104-127** (`SleepPrecise` and `AlertableSleep`) with the following.

An anonymous namespace holding:
- `std::atomic<bool> high_resolution_timers_`
- `std::atomic<uint32_t> timer_period_ms_`
- `GetTimePeriodFn(name)`: a static `LoadLibraryExW(L"winmm.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32)` plus `GetProcAddress`. This way there is no new link dependency.
- `GetThreadSleepTimer()`: a thread_local RAII struct holding a `CREATE_WAITABLE_TIMER_HIGH_RESOLUTION` timer, with `CloseHandle` in its destructor. The old code leaked one handle per thread.
- `ArmSleepTimer(timer, us)`: sets `due = -clamp(us, 0, INT64_MAX/10)*10`.

Then the functions:
- `SleepPrecise`: same semantics as before.
- `AlertableSleep`: unchanged.
- `AlertableSleepPrecise`:
  - Fall back to `AlertableSleep` when us ≤ 0, there is no timer, or arming fails.
  - Otherwise `WaitForSingleObjectEx(timer, INFINITE, TRUE)`.
  - On `WAIT_IO_COMPLETION`, call `CancelWaitableTimer` and return `kAlerted`.
- `ConfigureHostTiming`:
  - Store the high-res flag.
  - When the opt-out is requested: `SetProcessInformation(ProcessPowerThrottling, {Version=CURRENT, ControlMask=IGNORE_TIMER_RESOLUTION, StateMask=0})`. On failure, log at debug level only.
  - `timeBeginPeriod(period)==0`, then CAS into `timer_period_ms_`. If the CAS loses, call `timeEndPeriod`.
- `RestoreHostTiming`: `exchange(0)`, then `timeEndPeriod`.

**L363-381, the `Timer::Create*Timer` functions.** Replace them with a static `CreateWin32WaitableTimer(bool manual)`:
- When high-res is on, call `CreateWaitableTimerExW(nullptr, nullptr, HIGH_RESOLUTION | (manual ? MANUAL_RESET : 0), TIMER_ALL_ACCESS)`.
- Fall back to `CreateWaitableTimer(NULL, manual, NULL)`.

### 2. `src/core/threading_posix.cpp`

- Add `#include <rex/threading_timing.h>` after L10.
- Before `TlsHandle AllocateTlsHandle()` (L232), add:
  - `AlertableSleepPrecise`, which calls `AlertableSleep`;
  - a no-op `ConfigureHostTiming`;
  - a no-op `RestoreHostTiming`.

### 3. `src/system/runtime.cpp`

**Include.** Add `#include <rex/threading_timing.h>`.

**Cvars, after L35:**
- `REXCVAR_DEFINE_UINT32(host_timer_resolution_ms, 1, "Runtime", ...)`
- `REXCVAR_DEFINE_BOOL(host_timer_throttling_optout, true, "Runtime", ...)`
- `REXCVAR_DEFINE_BOOL(high_res_guest_timers, true, "Runtime", ...)`

**Owner pointer.** Add a file-static `Runtime* host_timing_owner_` inside `namespace rex`.

**Setup.** After `thread::EnableAffinityConfiguration();` (L124):
- Build the config from the cvars.
- Call `thread::ConfigureHostTiming(cfg)`.
- Set `host_timing_owner_ = this`.

**Shutdown.** Before `setup_complete_ = false;` (L300), add:

```cpp
if (host_timing_owner_ == this) { thread::RestoreHostTiming(); host_timing_owner_ = nullptr; }
```

### 4. `src/system/xthread.cpp`

**Includes and cvar.**
- Add `<rex/threading_timeout.h>` and `<rex/threading_timing.h>`.
- Add `REXCVAR_DEFINE_BOOL(precise_guest_sleep, true, "Kernel", ...)`.

**Scaling helper.** Add a static `ScaleGuestRelative100ns(rel)`:
- If the scalar is 1.0 or rel is 0, return rel.
- Otherwise multiply by the scalar as a double, saturating below 1.8e19.

**TLS (always on; this is a bug fix).**
- After L360, pad `tls_slots = (tls_slots + 3) & ~3u`, because `SetProcessTLSVars` marks the padded slots as allocatable.
- In Get/SetTLSValue (L906-924), check `uint64_t(slot)*4 + 4 > tls_total_size_ - (tls_dynamic_address_ - tls_static_address_)` and return false if it holds. The old checks overran by the extended size and could wrap in uint32.

**`Delay` (L1000-1040).** When the cvar is on:
1. `now = ticks > 0 ? QueryGuestSystemTime() : 0`
2. `us = Relative100nsToMicros(Scale(NtTimeoutToRelative100ns(ticks, now)))`
3. Call `CheckTitleTermination()`.
4. Alertable:
   - Call `us ? AlertableSleepPrecise(us) : AlertableSleep(0)`.
   - Call `CheckTitleTermination()`.
   - Return `X_STATUS_USER_APC` if alerted, else success.
5. Non-alertable:
   - If `us`, call `SleepPrecise(us)`.
   - Otherwise do the old priority yield: if `priority_ <= kBelowNormal`, `Sleep(100us)`, else `MaybeYield`.
   - Call `CheckTitleTermination()` and return success.

When the cvar is off, the old code runs unchanged.

### 5. `src/system/xobject.cpp`

**Includes and cvars.**
- Add `<rex/cvar.h>`, `<rex/threading_timeout.h>`, `<atomic>` and `<bit>`.
- Add `REXCVAR_DEFINE_BOOL(wait_timeout_round_up, true, "Kernel", ...)`.
- Add `REXCVAR_DECLARE(bool, object_lookup_fast_path)`.

**`TimeoutTicksToMs` (L189-201).** When the cvar is on:

```cpp
return NtTimeoutToMillis(t, t > 0 ? chrono::Clock::QueryGuestSystemTime() : 0);
```

When it is off, the old code runs.

**Item 7 (OFF by default).**
- `StashHandleOrdered`: write blink first, then flink with a release `std::atomic_ref` store (if the address is 4-aligned). This replaces both `StashHandle` calls (L365 and L445).
- In `GetNativeObject`, add a fast path before `AcquireDirect` (L383):
  - Acquire-load flink.
  - If it equals the byte-swapped `kXObjSignature`, relaxed-load blink and call `LookupObject<XObject>(handle)`.
  - Return the result if it is non-null; otherwise fall through to the locked path.

### 6. `src/system/util/object_table.cpp`

**Includes and cvar.**
- Add `<shared_mutex>` and `<rex/cvar.h>`.
- Add `REXCVAR_DEFINE_BOOL(object_lookup_fast_path, false, "Kernel", ...)`.

**Anonymous namespace.**
- A latched `FastLookupEnabled()`.
- A leaked `std::shared_mutex` table lock.
- `thread_local uint32_t table_write_depth`.
- RAII `TableWriteLock`. It takes the lock only when the feature is enabled and the depth goes from 0 to 1.

**Where the write lock goes.**
- Take it after the global lock in `Reset`, `AddHandle` and `PurgeAllObjects`.
- Take it alone in `Restore` and `RestoreHandle`.

**`RemoveHandle` (always on; this is a bug fix).** Take the global lock BEFORE `LookupTable`. Today it is taken at L191, after the lookup at L186. Then take `TableWriteLock`.

**`LookupObject(h, false)`, when enabled.**
- Take a `shared_lock`, unless the depth is above 0.
- Read the slot.
- `Retain`.
- Return.

**Design doc.** Lock order is G → T → name_mutex. Readers never block while holding T.

### 7. `src/core/clock.cpp` (lock-free reads, cvar `clock_lockfree`, default true)

**Seqlock state.** Atomics `clock_host_base_`, `clock_guest_base_`, `clock_num_` and `clock_den_` (a den of 0 means invalid), plus `clock_seq_`. Also a packed `guest_system_time_ratio_`.

**Writer.** `PublishGuestClockLocked(frac, enable)` is called in `RecomputeGuestTickScalar` under `tick_mutex_`:
1. Set seq odd.
2. seq_cst fence.
3. Read QPC.
4. Compute `guest_now` from the old snapshot, or from `last_*`.
5. Update `last_*`.
6. Store the fields, then store seq+2 with release.

**Reader.** `LoadGuestClockParams`:
- Up to 16 tries.
- Acquire-load seq. If it is odd, pause and retry.
- Relaxed loads of the fields.
- Acquire fence, then re-check seq.

**`UpdateGuestClock`.** Keep the no_scaling path. Otherwise return `guest_base + (d/den)*num + (d%den)*num/den`. If the params are invalid, use the old locked code.

**`QueryGuestSystemTimeOffset`.** Use the cached reduced ratio.

**Subagent A's notes (RESUME block of `agent11-s2-benches.md`).**
- **(a) Rebase step-back.** With a non-integer ratio, a rebase can step the clock back by 1 tick, because floor(a)+floor(b) ≤ floor(a+b). Fix it by aligning the rebase: round the delta up to a multiple of `den_old`. Then `G0' = g_old + ceil(d/den)*num` exactly and `h0' = h_old + ceil(d/den)*den`, and readers with h < h0' clamp to G0'.
- **(b) Old clock runs fast.** The old locked `UpdateGuestClock` can count time twice: when a thread holding an older QPC sample wins `try_lock`, `last_host` goes backwards. The clock still stays monotonic. Cite this as an old-code bug that the seqlock removes, using A's bench (f) for the drift numbers.
- **(c) Absolute due times.** `Win32Timer` always uses absolute due times, so the high-res timer check must cover absolute-due periodic timers.

### 8. `bench/agent11/test_timeouts.cpp`

**Contents.** Static asserts, plus a runtime table that compares the new conversion with a replica of the old one. Cases:
- 0, -1, -5000, -9999, -10000, -10001, -15000 and -1e6;
- INT64_MIN gives 0xFFFFFFFE;
- -(0xFFFFFFFF*10000) gives 0xFFFFFFFE (the old code gave INFINITE);
- -(2^32*10000) gives 0xFFFFFFFE (the old code gave 0);
- absolute values: +10000, +1, ==, -1, 1 and +5 s.

**Build and run:**

```
cl /nologo /O2 /std:c++20 /EHsc /W4 /I DimensionsRecomp\rexglue-sdk\include bench\agent11\test_timeouts.cpp /Fe:build\agent11\test_timeouts.exe /Fo:build\agent11\
```

### 9. Compile-check every edited `.cpp`

Run `env\compile-one.ps1 -SyntaxOnly` on each of:
- `core/threading_win.cpp`
- `core/clock.cpp`
- `system/runtime.cpp`
- `system/xthread.cpp`
- `system/xobject.cpp`
- `system/util/object_table.cpp`
- B's two kernel files

`threading_posix.cpp` cannot be compiled here, so review it by eye.

### 10. Integrate the subagents' results

- Read B's diff and notes.
- Read A's numbers: Sleep before and after, the high-res timer APC check, the clock bench and the lookup bench.

### 11. Write the Session 2 section in `perf-notes/agent11-kernel.md`

It covers:
- each change, with file:line, why, risk, cvar and default, and how it was verified;
- the memory-model arguments;
- rejected ideas;
- caveats;
- the in-game A/B plan for Agent 3's harness. Run it with the profiler OFF, because `rexlego/src/sample_profiler.cpp:100` calls `timeBeginPeriod`. Toggle each cvar, and report frame-time median, p99 and p99.9 plus stall counts.

### 12. Clean up

Delete the large objects in `build/agent11/obj`.

### 13. Report

Send `@@done 10: ...`, 3-6 lines with the headline numbers. Flag the headers: none in the closure; only the two new headers were added.
