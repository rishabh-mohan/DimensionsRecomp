# Agent 11 — Kernel HLE, threading, sync and timing (Task #10)

> **RESUME (Session 3; updated 07:59).**
> - **Task #35 (Agent 1, 07:47): S4-DRAFT upkeep, notes only. Final version and `@@done 35` by 09:30. No subagents. Files: `perf-notes/S4-DRAFT.md` and this file.** Standing quiet from 08:30: light, batched reads only.
>   - Pass 3 (07:53): Agent 1's five §4b answers (#37 staged, not S4, in §1d and §1f; #7 both cost numbers; #32 a switch unless rated output-identical; #8's memexport count is an S4 gate; #18/#20 GO deferred to the S4 kickoff). nativeB closed as (a); its root cause is new row #41 in a new §1h. Harness relabel done (§5). #24's 07:45 style pass and Q ≤ 2000. A "Changed since 07:44" list at the top.
>   - Pass 4 (07:58): fix (i) rated SAFE OFF and ON (b2r row 24, §23; item 4 PASS; C1 may nest the heap mutexes only view → parent). C1 staged at 07:51 (`build/agent12/s4-c1/`, HASHES.txt RESULT PASS; cvars `physical_protect_keep_watch` and `physical_protect_keep_watch_verify`; NOTE.md pending), folded into row 4. b2r row 23's path corrected at 07:55. Form 2 isn't rated until code exists. §6's b2r ranges re-read.
>   - Check after each pass: 9 tables, one pipe count each; the leftover strings 0; LF, no BOM. 368 lines / 61,318 B after pass 4. The backups (`S4-DRAFT.before-0743/0752/0758.md`) and the edit scripts are in this conversation's scratch dir.
>   - Waiting for: A12's C1 NOTE.md and syntax check (due 08:25); A10's #34 (the C1 rating, #24's review, #32's output-identical check, the R1/R2 summary, its check of the draft); any change to A9's S5.2 after 07:45.
> - **Status at 07:45 (nothing of mine is running):**
>   - **Package-power sys.csv columns: staged, tested and reported to Agent 1 (~07:26).**
>     - Test 58/58 PASS (07:22, 3+3 runs), compat PASS, both diffs pass `git apply --check`.
>     - Adoption: Agent 8 applies `LdSys.cs.diff` (and optionally `sys_summary.py.diff`) after window 4.
>     - Details: the section "Package-power sys.csv columns" at the end, and the README.
>   - **Task #30 DONE (`@@done 30` sent ~07:46). `perf-notes/S4-DRAFT.md`: rewritten 07:17, row 40 at 07:23, updated 07:40-07:45 (342 lines).**
>     - Contents: 40 rows in 6 groups, drops, shared files and apply order; S4a/S4b builds, functional checks and timing windows W5-W10; Agent 2's estimates; user questions; items for Agents 1, 10 and 12.
>     - The 07:40-07:45 update ran as two scripted passes, and every edit matched exactly once:
>       - #8 P2 is rated SAFE (b2r row 23, §22), with the memexport-fallback caveat for A12.
>       - Fix (i) is still unrated (its checklist item 4 is deferred to S4, b2r L1118).
>       - #24, #25 and #28 were rewritten from Agent 9's merged S5.2 (Xenos-only hooks H0-H3, `LEGO_GPU_WAIT_*` env), and W9 is now devoff-only.
>       - Agent 7's "Task #33" results went into #22 (inconclusive: the slow state), and the window-3 d11 correction (−3.1%) went into #39.
>     - Check: 8 tables, each with a single pipe count; no leftover "pending" text.
>     - Still open in the draft: fix (i)'s rating, A10's R1/R2 summary, C1's staging (A12, 08:25) and the nativeB check. From 08:30: notes only.
>   - **File grants (Agent 1, 07:27):** `bench/agent11/syscsv-pkg/` and its README section were outside #30's grant. Agent 1 accepted it this time (new files only; nothing W4b uses changed). From now on, ask Agent 1 before writing outside a task's file list. Agent 1 also said: don't tell Agent 8 about the adoption tonight; it is S4-DRAFT row 40 (a measurement row).
> - **Open at 06:45 (history; both are notes / bench only):**
>   1. **Task #30 (Agent 1, 06:38): draft the S4 plan in `perf-notes/S4-DRAFT.md`, report by 08:15 with `@@done 30`.**
>      - Rules: notes only; light reads until Agent 8 posts "@@to all: last run ended", then ≤2 threads; no decisions (a draft for the user and Agent 1).
>      - One subagent is allowed. The research subagent `00412268-d061-4108-bea8-9f6ec20f6a34` (launched 06:40) extracts the S4 items from the other agents' notes: an interim item list around 07:00, the full table by 07:35.
>      - Then ask Agent 2 for build-time and disk estimates (no builds). Files: `perf-notes/S4-DRAFT.md` and this file.
>   2. **Package-power sys.csv column (Agent 1, 06:28; no task number): staged in `bench/agent11/syscsv-pkg/`.**
>      - Copies of Agent 8's `LdSys.cs` and `sys-csv.ps1`; the originals' hashes are in `originals-0631.txt`.
>      - Edits done at 06:35: 4 columns `pkg_w,pp0_w,pp1_w,dram_w` from `\Energy Meter(*)\Power`. The PS copy changes only the repo depth and the cache dir (`build\agent11\cache`).
>      - The test `test_syscsv_pkg.ps1 -Compare` was written at 06:38 and has NOT run yet. Run it only after Agent 8's "last run ended" and before 08:30; it compiles once into `build\agent11\cache`.
>      - Then: the diffs (`git diff --no-index`), a line-ending and ASCII check, a check that the sys.csv consumers (run-timing.ps1, sys_summary.py) read columns by name, the docs (README and a section here), and an `@@to 1` report.
>      - Don't touch `timerq_slowstate.ps1` tonight: Agent 8 uses it for the W4b read-out. A timer fires at ~07:18.
> - **Task #24 (Agent 1, 04:54): done. Summary and `@@done 24` sent at ~06:27. Result: NO EFFECT. The opt-out was held and the ~550 MHz E-core state still came in 3/3 d0e runs, as in 3/3 d0 runs.** Agent 1 (06:28) agreed to drop `host_execution_throttling_optout` and the runner switch from S4. Details are in "Result (task #24)" at the end. Recommendation: drop `host_execution_throttling_optout` and the runner switch (Agent 10's rule). PL1 can be measured next time with `\Energy Meter(RAPL_Package0_PKG)\Power`.
>   - Agent 8 ran it 06:00:46-06:19:09: stamp `20261122-0600`, full length, window-4b hashes 53/53 equal. Exit 1 was the teardown artifact in the sidecar's `ok`; read-out v2 gives NO EFFECT.
>   - Command: `bench\agent11\pthrottle_pairs.ps1`, about 19 min (`-MeasureS 50`: about 14.5 min). Agent 8 decides whether it runs after the shader dump; it must end by 07:15.
>   - Out: `build/agent11/pthrottle/pairs/<stamp>` and `<stamp>-meta/report.txt`.
>   - Self-tests: `-DryRun` PASS at 05:28; `-PlanOnly` exit 0. The window-4b hashes are equal, also against the 05:16 baseline.
>   - Sent at ~06:27: the summary to Agent 1, `@@done 24`, and a no-re-run note to Agent 8. Nothing is pending for #24. Attract window 06:33-07:15: no compiles, no reads over ~100 MB, 1 thread. From 08:30: notes only.
>   - Agent 1, 05:31: while games run, no recursive scans of the SDK, DimensionsRecomp or build trees; ≤2 threads.
>   - Agent 10, 05:24: both S4 cvars rated SAFE as default-off candidates.
> - **Task #19 (S4 staging, Agent 1, 04:07): done; `@@done 19` sent at ~04:50.** Scratch copies only: no live-tree edits, no builds, no game runs, ≤2 threads, no subagents, and only notes from 08:30. Details are in "S4 staging (task #19)" at the end.
>   1. `host_execution_throttling_optout` (OFF) is staged in `build/agent11/pthrottle/stage/`. Stage 35/35, syntax PASS, read-back test 129/129. The rating request went to Agent 10 at ~04:50. Applying it needs SAFE and Agent 1's GO (S4).
>   2. The runner proposal for Agent 8 (next session) is written; its helper passed the probe, 6/6.
>   3. The user-facing timer summary is written.
> - **Task #10 (S3, Agent 1, 02:01): done (Agent 1 marked it done).** I own `bench/agent11/**`, `build/agent11/**` and this file. One subagent is allowed (0 used). Finish with `@@done 10: …`.
>   1. **S3 default check: done, PASS.** The `default` run is in `testg_session.ps1`. Its self-tests passed: 24/24 at 02:04, and 0 failed with `-Devoff3` at 02:49. Agent 8 ran `-Only default` on devoff3 at 02:59-03:01: PASS, 50/50 (see "S3 default check" → "Result"). Reported to Agents 1 and 10 at ~03:08.
>   2. **TimerQueue lead: done.** The cause is found and the fix is staged (see "S3 TimerQueue" at the end). The stage bench passed at 03:10: precise uses 1.9% CPU, against 30.4% for today's spin. Agent 1 (03:10): no build tonight; the fix waits for S4. In-game, blocking cut the TimerQueue thread from 31-44% to 0.3-0.5% of a core in all 4 runs. Every hidden-desktop run tonight can fall into a "slow state" (E cores at minimum clock), so fps can't be compared there (see "The slow state"). The cause report went to Agent 1 at ~04:05, recommending W4b with d11t, with `@@done 10`. Tools: `timerq_pair.ps1` and `timerq_slowstate.ps1`. Still pending:
>      - Agent 1's window-4 decision: made at ~04:07, W4b with d11t (final);
>      - Agent 10's rating of `timer_queue_precise_wait` (requested at ~03:08).
> - **Rules tonight:**
>   - Only Agent 2 builds (≤ -j10); I use ≤2 threads.
>   - Game runs are functional only, in Agent 8's slot. No builds or game runs from 08:30 (window 4 waits for the user).
>   - No `DimensionsRecomp/**` edits: `timer_queue_precise_wait` stays staged (an S4 candidate).
>   - Questions go to Agent 1; the user is asleep until ~10:00.
>
> **Session 2 (as of 01:25; history):**
> - **RELAUNCH (Agent 1, 01:20):** window 3 ended at 01:16 (19/19 OK). Until the agy-grid relaunch: no builds, no game runs, no new work. My state line went to Agent 1 at ~01:27. Nothing of mine is running.
> - **First step after the restart:** first wait for the new Agent 1's task block (Agent 1, 01:38: stay idle until the relaunch, then follow these notes). Then do the S3 default check, which Agent 1 approved at 01:20. Add the opt-in `default` run to `bench/agent11/testg_session.ps1` exactly as written in "S3 default check" at the end, and self-test it with `-CheckOnly`. Then run it in Agent 8's slot right after the devoff3 boot. It needs safeorder landed in S3 by Agent 12 first: `rex_app.cpp` was still pristine at 01:21.
> - #10 and #19 are closed.
> - #23 (test G on `build/agent2/devoff1-bin` with the #19 driver, in watch mode plus Agent 12's `debug_pause_cycle_ms` / `debug_pause_cycle_count`) is **done**. Halves 1 and 2 passed 50/50 at 21:32-21:38. The control re-run with a dump (23:21-23:23) failed as intended, and the dump shows the deadlock. The slot went back to Agent 8 at ~23:25, and `@@done 23` went out with this update (~23:35).
> - #27 (the SDK exit-path fix, batch 3) **landed in the live tree at 23:19**, after S2 (23:15:03) and Agent 10's SAFE. `@@done 27` was sent at ~23:26. See the "#27" block below and the "#27 exit-path fix" section at the end.
>
> **#19, done:**
> - The A/B pointer went to Agent 8 at 19:31.
> - The driver, self-test and probe are in "Session 2 → Test G driver (#19)" below.
> - The probe on `build/baseline-bin` came out INCONCLUSIVE, as predicted: SDL 3.5 ignores posted focus messages. So test G uses Agent 12's `debug_pause_cycle_ms` / `debug_pause_cycle_count` (20:15 batch) with the driver in watch mode.
>
> **#23** (details in "Session 2 → Test G results (#23)"):
> - **Ran 21:32-21:38** in one `testg_session.ps1` command, after Agent 8's devoff1 boot.
>   - Half 1 (safe order, B OFF): PASS, 50/50.
>   - Half 2 (safe order, B ON): PASS, 50/50.
>   - The control (old order) hung after 4 cycles. The driver called it INCONCLUSIVE and took no dump, because two of its rules raced. Fixed at 21:45 and self-tested at 21:51.
> - **21:41:** slot back to Agent 8; verdicts and paths to Agent 1; the B ON runner line (R4 = R3 + `object_lookup_fast_path=true guest_suspend_guard=true`) to Agent 8. Agent 1 (21:56): B goes into the next timing window.
> - **The control re-run with a dump ran 23:21-23:23** in Agent 8's slot, after quiet window 2, with `testg_session.ps1 -Only control -ForceControl`:
>   - **FAIL, as intended.** It hung at the 1st pause (0/50 cycles). The UI rule fired after 10 s, and the driver took a thread list, a dump and a stack report. The game ignored WM_CLOSE and was killed.
>   - **The dump:** UI thread 76036 is in `SetGuestPaused` → `AudioSystem::Pause` → `pause_fence_.Wait()`. The Audio Worker (59800) is inside the game's audio callback, blocked in `KeWaitForMultipleObjects`. All 20 guest threads are suspended. B can't fix this; the safe order does.
>   - **~23:25:** slot back to Agent 8. Then reported to Agent 1, and to Agent 12 (#17 owner), with `@@done 23`.
>
> **#27** (the SDK exit-path fix; details in "#27 exit-path fix" at the end):
> - **Decision:** both exports end with `rex::FlushLogging(); std::_Exit(code)`, with codes 0 and 1, like OnClosing. No TerminateTitle, no OnShutdown, no cvar.
> - **Staged at 22:27** in `build/agent11/exitfix/` (`exitfix.diff`, `HASHES.txt`, `pristine/`). The live tree is untouched.
> - **Left to do:**
>   1. **Done: every pre-apply check passed.**
>      - Lint: at 22:46, and again after the window at 23:17. The staged copies passed 12/12, and `-Pristine` exited 1 with the 6 expected FAILs.
>      - Syntax at 23:14: no new diagnostics.
>      - Unit test at 23:15: `RESULT: PASS` in all 12 cases.
>      - The live files were still pristine at 23:17.
>   2. **Done at 23:19.** Applied with `exitfix_stage.ps1 -Apply`, then `exitfix_check.ps1 -Live` and `exitfix_syntax.ps1 -Live` passed (details in "Landing (batch 3)"). To undo: `exitfix_stage.ps1 -Revert`.
> - **Agent 10 rated #27 SAFE at ~22:43** (#25 item 10; details in `perf-notes/agent10-batch2-review.md` S10). Its staged-vs-live diffs match `exitfix.diff` (B2C1FE21) exactly, LF and no BOM are kept, and the live files were still pristine at 22:38. Leaving out TerminateTitle is correct, and nothing in #22 depends on the change. Its condition is the same as step 2: apply only after S2 is taken and the post-window checks pass.
> - **Messages (22:31):** the #25 listing went to Agent 10 and a #22 heads-up to Agent 12. Agent 1 gets the result with `@@done 27`.
> - **mtime fix (00:06), Agent 12's catch:** `Copy-Item` keeps the source's LastWriteTime, so the 23:19 apply left both live files stamped 22:27:02 (when the staged copies were written). Both are now stamped 00:06:15, content unchanged (`build/agent11/exitfix/touch-0006.txt`). Both stage scripts now stamp the copy time on `-Apply` / `-Revert`. Details at the end of "Landing (batch 3)".
>
> **S3 proposal (Agent 1, 23:41): `pause_safe_order` default ON** (details in "S3 proposal" at the end):
> - **Staged at 23:48** in `build/agent11/safeorder/` (`safeorder.diff` 56952876…, `HASHES.txt`, `pristine/`): L71 `false` → `true`, plus the description and the `SetGuestPaused` comment. Stage self-checks 11/11 and syntax PASS. The live tree is untouched (`E1569868E157` = pristine).
> - **Sent to Agent 10 for a rating at ~23:55**, as text only. B stays OFF. **Agent 1 (23:55):** if it's rated SAFE, Agent 12 (the `rex_app.cpp` owner) lands it with `safeorder_stage.ps1 -Apply` after window 3 ends and before S3 is cut. Nothing more is needed from me until then. Since 00:09, `-Apply` also stamps the live file with the copy time (Agent 12's catch; see the #27 mtime fix).
> - **Agent 10 rated it SAFE at ~00:13** (`perf-notes/agent10-batch2-review.md` §11; see "Rating" in the S3 section). I told Agent 12 and Agent 1 at ~00:16. Agent 10 says the optional test G half 1 on the S3 build (with no explicit `--pause_safe_order`) is worth doing, so I asked Agent 1 for a go. **Agent 1 (01:20): yes**, on devoff3 after the relaunch (see "S3 default check" at the end).
>
> **Rules:**
> - Games launched by an agent run on that command's hidden desktop, so launch and drive in ONE command (`testg_launch.ps1`).
> - One game at a time, and only in an assigned slot. Outputs go in `build/agent11/`.
> - SDK edits: none pending. #27 landed at 23:19 (`exitfix_stage.ps1 -Revert` undoes it). The S3 proposal is staged only.
> - **Window 3** ran 00:13-01:16 (19/19 OK). **Relaunch pause from 01:20:** no builds, game runs or new work until the relaunch.
>
> **#10 history:** items 1-6 and item 7 (A always on; B `guest_suspend_guard` and C `object_lookup_fast_path` OFF) are described in "Session 2" below. Agent 10's #18 review (20:01) found 0 UNSAFE.

**Status (session 1): partial, analysis only.** This follows the 12:24 STOP PLAN:
- No source edits.
- No builds.
- No benches compiled.

Both repos are git-clean: SDK at `2897c31`, game on `perf/opt`. This file is the plan for resuming.

Paths are relative to `DimensionsRecomp/rexglue-sdk/` unless noted. Line numbers are as of `2897c31`.

## Evidence measured on this host

**Host:** i7-1255U (2 P-cores + 8 E-cores, 12 logical CPUs), Windows NT 10.0.26300.

**Method:** a PowerShell `Add-Type` P/Invoke harness timed with QPC. This is not a build. Each row has 40 samples.

**Caveat:** the machine was heavily loaded by 11 other agents and may have been on battery. Treat the absolute numbers as pessimistic. The ratios are what matter.

**Timer resolution:** `NtQueryTimerResolution` returned min 15.625 ms, max 0.5 ms, and **current 15.625 ms**, so nothing has raised it. Since Windows 10 2004, `timeBeginPeriod` is per-process, so another app raising the resolution does not help us.

| Wait primitive (1 ms requested unless noted) | median | p90 | max |
|---|---|---|---|
| `Sleep(1)`: what non-alertable guest sleeps use | **15.03 ms** | 16.66 | 19.0 |
| `SleepEx(1, TRUE)`: what alertable guest sleeps use | **14.69 ms** | 16.51 | 18.65 |
| High-res waitable timer at 1000 µs + alertable `WaitForSingleObjectEx` | **2.63 ms** | 4.45 | 7.73 |
| High-res timer at 500 µs | 1.22 ms | 2.99 | 6.05 |
| High-res timer at 2000 µs | 3.50 ms | 6.80 | 9.60 |

- `CreateWaitableTimerExW(..., CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_ALL_ACCESS)` works on this OS. Its ~1.5 ms overshoot is attributed to load. Expect about 1.05 ms when idle; re-measure with bench (d).
- Yield cost under load, 200k calls each:
  - `SwitchToThread`: 15,086 ns/call.
  - `Sleep(0)`: 3,315 ns/call.

## Ranked opportunities

| # | Opportunity | Main location | Expected win | Risk | Owned |
|---|---|---|---|---|---|
| 1 | Process timer resolution is 15.6 ms; no power-throttling opt-out | new function in `src/core/threading_win.cpp` | **High.** Every ms-level sleep, wait or timer goes from 15.6 ms to about 1-2 ms | low (power) | yes; the call site needs a claim or an owned alternative |
| 2 | `KeDelayExecutionThread`: ms truncation, absolute time unsupported, `::Sleep` | `src/system/xthread.cpp:1000-1040` | **High** for guest Sleep(1..15); sub-ms sleeps become correct | low-med | yes |
| 3 | Wait timeouts truncated to ms; absolute timeouts become 0 | `src/system/xobject.cpp:189-216` | Med-High (timed waits, poll loops) | low | **claim** |
| 4 | Contended `RtlEnterCriticalSection`: no spin, goes straight to the kernel | `src/kernel/xboxkrnl/xboxkrnl_rtl.cpp:395-484` | Med-High under contention | med | yes |
| 5 | Global recursive mutex taken twice on every Ke* dispatcher call | `src/system/xobject.cpp:370-449`, `src/system/util/object_table.cpp:270-298` | Med (multi-thread scaling) | med | **claim** |
| 6 | Kernel spinlock calls `SwitchToThread` after every failed CAS | `src/kernel/xboxkrnl/xboxkrnl_threading.cpp:967-976` | Med under contention | low | yes |
| 7 | Guest timers (XTimer) are not high-res | `src/core/threading_win.cpp:363-381` | Med (periodic timer pacing) | low-med | yes |
| 8 | Hybrid CPU: no per-thread EcoQoS opt-out; one priority call bypasses its cvar | `src/system/xthread.cpp:40-43, 473-475, 880-904` | Med when the window is occluded or on battery | low | yes |
| 9 | Guest clock mutex on every time query | `src/core/clock.cpp:43-89` | Low-Med (depends on the mftb path) | low-med | yes |
| 10 | TLS get/set bounds bug (correctness) | `src/system/xthread.cpp:905-920` | correctness | low | yes |
| 11 | Per-call `std::vector` in the multi-object wait paths | `src/system/xobject.cpp:265` and others | Low | low | partly |
| 12 | Keep the NtYieldExecution mapping; the rest of this row is not hot | — | — | — | — |

---

### 1. The host timer resolution stays at 15.625 ms

**Where:**
- There is no `timeBeginPeriod` call anywhere in the SDK.
- The only call in the game is [rexlego/src/sample_profiler.cpp:100](<workspace>/DimensionsRecomp/rexlego/src/sample_profiler.cpp#L100), and it runs only when the profiler is on.

**What is slow:** every host wait with a ms timeout is rounded up to the next 15.625 ms tick. That covers:
- `Sleep` and `SleepEx` (item 2)
- `WaitForSingleObjectEx(timeout_ms)` (item 3)
- non-high-res waitable timers (item 7)

Measured: `Sleep(1)` has a median of 15.0 ms.

> [!WARNING]
> Turning on the sample profiler raises the timer resolution to 1 ms. Frame-time profiles taken with it on therefore hide this stutter. Measure pacing with the profiler off.

**Change** (sketch, not compiled):
```cpp
// src/core/threading_win.cpp (new) + declaration in include/rex/thread.h
void ConfigureHostTiming(uint32_t timer_resolution_ms, bool disable_power_throttling) {
  if (disable_power_throttling) {
    PROCESS_POWER_THROTTLING_STATE s{};
    s.Version = PROCESS_POWER_THROTTLING_CURRENT_VERSION;
    s.ControlMask = PROCESS_POWER_THROTTLING_EXECUTION_SPEED |
                    PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION;
    s.StateMask = 0;  // no EcoQoS; keep our timer resolution when occluded (Win11)
    SetProcessInformation(GetCurrentProcess(), ProcessPowerThrottling, &s, sizeof(s));
  }
  if (timer_resolution_ms) timeBeginPeriod(timer_resolution_ms);  // timeEndPeriod at shutdown
}
```

Implementation notes:
- `timeBeginPeriod` needs `winmm.lib`. To avoid a CMake change, resolve `NtSetTimerResolution` from ntdll with `GetProcAddress` instead. That route also allows 0.5 ms.
- Call site options:
  - Next to `thread::EnableAffinityConfiguration()` at [src/system/runtime.cpp:124](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/runtime.cpp#L124). Not owned, so it needs `@@claim`.
  - Owned alternative: the xboxkrnl module init under `src/kernel/xboxkrnl/`. I have not read that code yet.

**Cvars:**
- `host_timer_resolution_ms`: int, default 1. 0 keeps the OS default, which is today's behaviour.
- `host_disable_power_throttling`: bool, default true.

**Risk:** a little more idle power on battery. Since Windows 10 2004 the effect is per-process. No functional change.

**Verify:**
- Bench (d) before and after. `Sleep(1)` should drop to a median of about 2 ms or less.
- While the game runs, `NtQueryTimerResolution` should report a current value of 10000 or less.
- In-game frame-time trace with the profiler **off**.

### 2. `KeDelayExecutionThread` (`XThread::Delay`)

**Where:**
- [xthread.cpp:1000-1040](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xthread.cpp#L1000-L1040).
- Entered from `KeDelayExecutionThread_entry` at [xboxkrnl_threading.cpp:376](<workspace>/DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_threading.cpp#L376).
- Host helpers at [threading_win.cpp:96-127](<workspace>/DimensionsRecomp/rexglue-sdk/src/core/threading_win.cpp#L96-L127).

**What is slow** (evidence in the code):
- **L1010:** `timeout_ms = -ticks / 10000` truncates.
  - 0.5 ms becomes 0. The thread yields instead of sleeping, so it spins.
  - 1.9 ms becomes 1 ms, which the timer then rounds up to 15.6 ms (item 1).
- **L1006:** absolute (positive) intervals hit `assert_always()` and are treated as 0. A sleep until a deadline becomes a yield or spin loop.
- **Alertable path (L1017):** calls `AlertableSleep`, which calls `SleepEx(ms, TRUE)` (L122-127).
- **Non-alertable path (L1034):** calls `thread::Sleep`, which calls `::Sleep(ms)` (L96-102).
- **Timeout-0 path for low-priority threads** (`priority_ <= kBelowNormal`):
  - It calls `Sleep(100us)`, which on Windows becomes `::Sleep(0)` because 100/1000 = 0.
  - `priority_` holds the guest increment but is compared against a host enum.
- **A precise helper already exists but is unused here.** `SleepPrecise` ([threading_win.cpp:104-120](<workspace>/DimensionsRecomp/rexglue-sdk/src/core/threading_win.cpp#L104-L120)) keeps a thread_local high-res timer. The GPU command processor uses it (`command_processor.cpp:1185`); guest sleeps do not.

**Change** (sketch):
```cpp
// include/rex/thread.h + src/core/threading_win.cpp (POSIX: clock_nanosleep fallback)
SleepResult AlertableSleepPrecise(int64_t duration_100ns) {
  thread_local HANDLE t = CreateWaitableTimerExW(nullptr, nullptr,
      CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_ALL_ACCESS);
  if (!t)  // pre-1803 fallback: old behaviour, rounded up
    return AlertableSleep(std::chrono::milliseconds((duration_100ns + 9999) / 10000));
  LARGE_INTEGER due;
  due.QuadPart = -duration_100ns;  // relative
  SetWaitableTimer(t, &due, 0, nullptr, nullptr, FALSE);
  return WaitForSingleObjectEx(t, INFINITE, TRUE) == WAIT_IO_COMPLETION
             ? SleepResult::kAlerted : SleepResult::kSuccess;
}

// src/system/xthread.cpp XThread::Delay: new branch when precise_guest_sleep is on
int64_t ticks = static_cast<int64_t>(interval);
if (ticks > 0)  // absolute FILETIME -> relative (was assert_always + 0)
  ticks = std::min<int64_t>(0, int64_t(Clock::QueryGuestSystemTime()) - ticks);
int64_t hns = ScaleGuestDuration100ns(-ticks);  // positive 100 ns, keeps guest time scaling
if (hns == 0) { /* unchanged: SleepEx(0, TRUE) / MaybeYield */ }
else if (alertable)
  return thread::AlertableSleepPrecise(hns) == thread::SleepResult::kAlerted
             ? X_STATUS_USER_APC : X_STATUS_SUCCESS;
else { thread::SleepPrecise(/* hns * 100 ns */); return X_STATUS_SUCCESS; }
```

Notes:
- Check how the clock's `ScaleGuestDuration*` helpers handle the sign of relative (negative) inputs before reusing them. Pass a positive duration.
- The thread_local timer handle is never closed, so each guest thread holds one handle. `SleepPrecise` already does the same. An RAII wrapper is optional.
- Under the same cvar, the low-priority timeout-0 path can call `SleepPrecise(100 µs)`, which is what its comment intends.

**Cvar:** `precise_guest_sleep`, bool, default true. With it off, the current code path runs unchanged.

**Risk:**
- Threads that poll with Sleep(1) now wake about 15× more often. That costs more CPU and power, but matches the console.
- APC handling stays the same: `WAIT_IO_COMPLETION` maps to `X_STATUS_USER_APC`, as the `SleepEx` path does today.
- The absolute-time conversion assumes `QueryGuestSystemTime` uses the same epoch as the guest FILETIME. It is what `KeQuerySystemTime` returns.

**Verify:**
- New unit test (owned, `tests/unit/kernel/`) for the ticks-to-duration conversion. Cases: relative, absolute in the past, absolute in the future, sub-ms, 0.
- Bench (d): `Delay(-10000)` should take about 1.0-1.1 ms when idle.
- An in-game counter of `KeDelayExecutionThread` calls per second and their intervals, to see which threads hit this.

### 3. Wait timeouts are truncated to ms; absolute timeouts are unsupported (needs a claim)

**Where:**
- [xobject.cpp:189-216](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xobject.cpp#L189-L216), `TimeoutTicksToMs`:
  - Absolute timeouts hit an assert and become 0 (L190-194).
  - Relative timeouts are truncated: `-ticks/10000` (L195-201).
- The result goes to `thread::Wait`, which calls `WaitForSingleObjectEx(handle, ms, alertable)` ([threading_win.cpp:160-176](<workspace>/DimensionsRecomp/rexglue-sdk/src/core/threading_win.cpp#L160-L176)).
- The same helper feeds WaitMultiple and SignalAndWait (L232-370, not read in detail).

**What is slow:**
- A guest `KeWaitForSingleObject` with a 0.5 ms timeout becomes a 0 ms poll, so the guest loops and spins.
- A 1-2 ms timeout becomes 15.6 ms (item 1).
- An absolute deadline becomes a 0 ms poll, which spins until the event fires.

**Change:**
- Round up instead of truncating: `(-ticks + 9999) / 10000`.
- Convert absolute timeouts to relative with `QueryGuestSystemTime()`.
- Gate both with `wait_timeout_round_up`, default true.

Together with item 1 this gives about 1 ms resolution. Sub-ms precision would need a multi-wait on the object plus a high-res timer, which is not worth it now.

**Risk:** low. Rounding up matches NT semantics: a wait never times out early.

**Verify:**
- A unit test for `TimeoutTicksToMs`.
- `test_timer_wait.py` covers TimerQueue only, so add a kernel wait-timeout case.

### 4. A contended critical section never spins and blocks in the kernel at once

**Where:**
- Enter: [xboxkrnl_rtl.cpp:395-484](<workspace>/DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_rtl.cpp#L395-L484).
- Leave: [L600-660](<workspace>/DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_rtl.cpp#L600-L660).
- Init: [L351-358](<workspace>/DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_rtl.cpp#L351-L358).

**Already fine:**
- The uncontended path (thread_local current thread + atomic CAS) takes no global lock.
- The asserts in Leave (L622-627) compile out in release.

**What is slow** (evidence in the code):
- **No spin by default.** The spin count is `header.absolute * 256`, and `xeRtlInitializeCriticalSection` sets it to 0 (L351-358). Nearly every CS therefore has **no spin at all**.
- **The spin that does exist is poor.** When a CS has a spin count (L407-414), every iteration is a CAS with no `_mm_pause` and no read first. That bounces the cache line back and forth with the owner.
- **The contended path is expensive.** On contention, Enter calls `xeKeWaitForSingleObject` (L428). That goes through `GetNativeObject` (global recursive mutex taken twice, plus Retain/Release; see item 5), then a host event wait: a kernel transition and a context switch.
- **Leave pays the same.** With waiters, Leave calls `xeKeSetEvent` (L637), which takes the same global-mutex path and then calls `SetEvent`.

The result: a short critical section that would have been free within about 1 µs costs several µs plus a reschedule on both sides.

**Change** (sketch):
```cpp
// xboxkrnl_rtl.cpp RtlEnterCriticalSection: replaces the loop at L407-414
uint32_t spin = spin_count;  // header.absolute * 256, usually 0
if (!spin && REXCVAR_GET(cs_adaptive_spin)) spin = REXCVAR_GET(cs_spin_count);  // e.g. 1000
while (spin--) {
  if (cs->lock_count == -1 &&                     // read first: no RFO while owned
      rex::atomic_cas(-1, 0, &cs->lock_count)) {  // -1 and 0 are byte-order neutral
    /* acquired: same bookkeeping as the existing spin-success branch */
    return;
  }
  _mm_pause();  // x86-64-v2 is fine; guard non-x86 builds
}
```

`pause` latency differs a lot between P-cores and E-cores. Prefer a time bound for the spin (`__rdtsc()`, about 2-4 µs), or tune `cs_spin_count` with bench (a) on both core types.

**Cvars:**
- `cs_adaptive_spin`: default true once the bench confirms it.
- `cs_spin_count`: default 1000.

**Risk:**
- If the owner is preempted, we burn up to the spin bound before blocking. This box has 12 logical CPUs, often more busy threads than that, and E-cores. The spin is bounded, so the cost is small.
- Semantics are unchanged: the spin only tries the same `-1 → 0` CAS that the existing loop does.
- Check that this does not double up with the game-side lock elision (`rexlego/src/native_lock_elide.cpp`, `crash_guards.cpp`, not read).

**Verify:** bench (a).
- Uncontended: must be unchanged.
- Contended: 2 and 4 threads with a 50-500 ns hold.
- Report the number of kernel waits per 1M acquires.

### 5. A global recursive mutex is taken on every dispatcher call (needs a claim)

**Where:**
- `GetNativeObject` at [xobject.cpp:370-449](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xobject.cpp#L370-L449):
  - It takes `global_critical_region::AcquireDirect()` (L383).
  - Then it calls `object_table()->LookupObject` (L395), which locks the **same** mutex again ([object_table.cpp:270-298](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/util/object_table.cpp#L270-L298), L278).
  - It also does a Retain/Release pair.
- The mutex is a single static `std::recursive_mutex` ([mutex.cpp:16-17](<workspace>/DimensionsRecomp/rexglue-sdk/src/core/mutex.cpp#L16-L17)). All other kernel state shares it: thread creation, the DPC queue, the object table.

**Callers on hot paths:**
- `KeSetEvent` (xboxkrnl_threading.cpp:465/475)
- `KePulseEvent` (479)
- `KeResetEvent` (489)
- `xeKeWaitForSingleObject` (820)
- `KeReleaseSemaphore` (597/614)
- `KeWaitForMultipleObjects` (871)
- every contended CS (item 4)

**What is slow:** every guest event signal or wait serializes on this one lock, and takes it twice. That includes all 6 guest threads plus the host workers. When the lock is contended, MSVC's `recursive_mutex` blocks in the kernel.

**Change, in two stages:**
1. **Lock-free fast path.**
   - Read `header->wait_list_flink == kXObjSignature` with acquire ordering, and read the handle from `wait_list_blink`.
   - Look the handle up under the **table's own** lock, not the global one.
   - Take the global lock only to create the object on first use, and check the signature again under that lock.
   - `StashHandle` must write blink first and then flink with release ordering. Check `xobject.h`.
2. **Separate table lock.** Give `ObjectTable` its own `std::shared_mutex` instead of `global_critical_region`: shared for lookups, exclusive for add and remove.

Also fix a race: `RemoveHandle` calls `LookupTable` (L186) before it takes the lock (L191).

**Cvar:** `object_lookup_fast_path`, default false until a stress test passes.

**Risk:** medium, because this is concurrency code. Today the global lock also orders object creation against lookup.

**Verify:**
- `tests/unit/kernel/object_table_test`.
- New stress test: N threads doing first-use init, then Set and Wait on the same native event.
- Bench (c): wait/signal ping-pong with no lock, with the global `recursive_mutex` taken twice, and with a `shared_mutex`.

### 6. The kernel spinlock yields after every failed CAS

**Where:** `xeKeKfAcquireSpinLock` at [xboxkrnl_threading.cpp:967-976](<workspace>/DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_threading.cpp#L967-L976).
- Each failed CAS calls `thread::MaybeYield()`, which is `SwitchToThread` + `MemoryBarrier`. That is a syscall; it measured 15 µs under load.
- Guest spinlocks are usually held for under 1 µs.
- Raising and lowering IRQL (L951-963) are plain PCR byte writes, which is fine.

**Change** (sketch):
```cpp
uint32_t n = 0;
while (!rex::atomic_cas(0, value, lock)) {  // value as today
  do {                                      // test-and-test-and-set
    if (++n < REXCVAR_GET(spinlock_spin_count)) _mm_pause();  // e.g. 4096
    else { thread::MaybeYield(); n = 0; }
  } while (*reinterpret_cast<volatile uint32_t*>(lock) != 0);
}
```
Apply the same change to the `KeAcquireSpinLockAtRaisedIrql` variant.

**Cvar:** `spinlock_pause_spin`, default true.

**Risk:** low.

**Verify:** bench (e) with 2, 4 and 6 threads and a short hold.

### 7. Guest timers use non-high-resolution waitable timers

**Where:** `Win32Timer` at [threading_win.cpp:363-381](<workspace>/DimensionsRecomp/rexglue-sdk/src/core/threading_win.cpp#L363-L381) creates its timers with `CreateWaitableTimer`.

**What is slow:**
- XTimer (`KeSetTimer(Ex)` / `NtSetTimerEx`, [xtimer.cpp](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xtimer.cpp)) is built on `Win32Timer`.
- Due times therefore snap to the 15.6 ms grid (1 ms after item 1).
- Guest periodic timers used for pacing jitter as a result.

**Change** (sketch):
```cpp
HANDLE h = nullptr;
if (g_high_res_timers)  // flag set at startup; core code may not see cvars
  h = CreateWaitableTimerExW(nullptr, nullptr,
        (manual_reset ? CREATE_WAITABLE_TIMER_MANUAL_RESET : 0) |
        CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_ALL_ACCESS);
if (!h) h = CreateWaitableTimer(nullptr, manual_reset, nullptr);  // old path
```

**Cvar:** `high_res_guest_timers`, default true.

> **Session 2: dropped.** A HIGH_RESOLUTION timer rejects a completion routine (error 87), and `Win32Timer` needs one. `host_timer_resolution_ms=1` already puts standard timers on a 1 ms grid. See Item 1 under Session 2.
**Risk:** low-med.
- Confirm that these still behave the same with high-res timers:
  - APC completion routines
  - the periodic `lPeriod` (still in ms)
  - absolute due times
- High-res timers cannot be named, which is fine here.

**Verify:** new unit test in `tests/unit/kernel/`:
- 2 ms one-shot: median error under 0.5 ms when idle.
- 16 ms periodic over 100 ticks.
- The APC fires.

### 8. Host threading on the hybrid i7-1255U

**Facts:**
- **Hard affinity is off by default.** `ignore_thread_affinities` defaults to true ([xthread.cpp:43](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xthread.cpp#L40-L43)), so no hard masks are applied. **Keep that.**
- **Turning it off would be harmful on this CPU.**
  - If set to false, `SetActiveCpu` ([L880-904](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xthread.cpp#L880-L904)) pins guest hardware thread n to logical CPU n with `SetThreadAffinityMask(1<<n)`.
  - On the 1255U, logical CPUs 0-3 are the two P-cores' SMT siblings and 4-5 are E-cores.
  - Guest threads 4 and 5 would be locked to E-cores, and threads 0/1 and 2/3 would each share one physical core.
- **One priority call bypasses its cvar.**
  - `ignore_thread_priorities` defaults to true (L40).
  - `XThread::Create` ([L473-475](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xthread.cpp#L473-L475)) still calls the host `set_priority(1 or 0)` from `creation_flags & 0x60`, **ignoring the cvar**.
  - That is inconsistent. It is harmless or even helpful (ABOVE_NORMAL for flag 0x20), but it should be gated or documented.
- **`GetFakeCpuNumber` only affects what the guest sees.** It round-robins over 0-5 (L186-204).
- **No scheduling hints anywhere.**
  - The SDK has no `SetThreadIdealProcessor(Ex)`, no CPU Sets and no EcoQoS opt-out.
  - `rexlego/src/gpu_native/native_worker.cpp:349` sets ABOVE_NORMAL for the GPU worker.

**Change:**
- At thread start in `threading_win.cpp`, opt every guest thread out of EcoQoS. Do the same for the GPU and audio workers. Gate it with `host_disable_power_throttling` (item 1).
```cpp
THREAD_POWER_THROTTLING_STATE s{};
s.Version = THREAD_POWER_THROTTLING_CURRENT_VERSION;
s.ControlMask = THREAD_POWER_THROTTLING_EXECUTION_SPEED;
s.StateMask = 0;  // never EcoQoS
SetThreadInformation(GetCurrentThread(), ThreadPowerThrottling, &s, sizeof(s));
```
- If affinities are ever honoured, replace the hard masks with something softer, and let Thread Director still migrate threads:
  - `SetThreadSelectedCpuSets`, choosing sets by `EfficiencyClass` from `GetSystemCpuSetInformation` (the highest class is the P-cores), or
  - `SetThreadIdealProcessorEx` hints.
- Either gate the priority call at L473-475 with `ignore_thread_priorities` or document it as intentional.

**Risk:** low.

**Verify:**
- Run with the window occluded and on battery.
- Task Manager's "Efficiency mode" column, or Process Explorer, should show no EcoQoS.
- An ETW CPU-usage trace (WPR) should show the main and render threads mostly on P-cores.
- Compare frame times with the window focused and unfocused.

### 9. Guest clock mutex

**Where:** `UpdateGuestClock` at [clock.cpp:43-89](<workspace>/DimensionsRecomp/rexglue-sdk/src/core/clock.cpp#L43-L89). When `clock_no_scaling=false` (the default), every `QueryGuestTickCount` and `QueryGuestSystemTime` does a `try_lock` on the global `tick_mutex_`. If that fails, it does a blocking `lock()` just to read the value another thread is updating.

**What is slow:** time queries from several threads serialize and can block in the kernel.

How hot this is depends on whether `mftb` → `REX_QUERY_TIMEBASE()` ends up here. I could not find that macro's definition; it is probably in a generated header.

**Change:**
- Make reads lock-free. Publish `{host_base, guest_base, scalar}` with a seqlock (atomic 64-bit fields), updated only when the scalar changes.
- Readers compute `guest_base + (host_now - host_base) * scalar`. This stays monotonic because QPC is.
- With the default scalar of 1.0, this degenerates to the `clock_no_scaling` fast path.

**Cvar:** `clock_lockfree`, default true.

**Risk:** low-med. Monotonicity and scalar changes need a test.

**Verify:**
- `tests/unit/core/chrono_test`. Not owned, so run it only.
- Bench (f): ns/call at 1, 2 and 6 threads.

### 10. TLS is cheap, but has a bounds bug

**Performance is fine.** `KeTlsGetValue` ([xboxkrnl_threading.cpp:428](<workspace>/DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_threading.cpp#L428)) is a thread_local lookup plus a byteswap, with no lock.

**The bug:**
- **Off by one.** `XThread::GetTLSValue` ([xthread.cpp:907](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xthread.cpp#L905-L920)) checks `slot*4 > tls_total_size_`; it should be `>=`.
- **Wrong bound.** Get (L907) and Set (L917) both check against `tls_total_size_`, which covers the slots plus the extended data. But they index from `tls_dynamic_address_ = tls_static_address_ + tls_extended_size`. Slot indices past `tls_slots` therefore read or write past the end of the allocation.
- **Fix:** bound by the slot area: `tls_total_size_ - tls_extended_size`, or store `tls_slots_`. It is a correctness fix and needs no cvar.
- **Also check:** whether the maximum slot from `KernelState::AllocateTLS` can exceed the XEX's `tls_slots` (not read).

**Possible logging cost (unverified).**
- `KeTlsSetValue` (L440) runs `REXKRNL_IMPORT_TRACE/RESULT`, which expands to `REX_LOG_NOISY_IMPL` (`include/rex/logging/macros.h:45`).
- I did not check whether that compiles out in release. If it does not, compile it out for these hot entries.

### 11. Per-call heap allocations in multi-object waits

**Where:** `std::vector` allocations at:
- [xobject.cpp:265](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xobject.cpp#L265)
- [threading_win.cpp:202](<workspace>/DimensionsRecomp/rexglue-sdk/src/core/threading_win.cpp#L202)
- the `KeWaitForMultipleObjects` and `NtWaitForMultipleObjectsEx` entries (xboxkrnl_threading.cpp:871, 897, 920)

**Change:** replace them with a fixed `std::array<…, 64>` (`MAXIMUM_WAIT_OBJECTS`) plus a count.

Small win, about 100-300 ns per call; low risk. The `xobject.cpp` part needs a claim.

### 12. Leave as is / not hot

- **NtYieldExecution / KeYieldProcessor: keep.**
  - [xboxkrnl_threading.cpp:392-393](<workspace>/DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_threading.cpp#L392-L393) calls `MaybeYield`, i.e. `SwitchToThread`.
  - `SwitchToThread` yields only to a thread that is ready on the same CPU, and returns at once if there is none. `Sleep(0)` is not clearly better.
  - The loaded-machine numbers (15 µs vs 3.3 µs) are not representative.
- **Not exported:** `KeQueryPerformanceCounter`.
- **Not hot:**
  - `KeQueryPerformanceFrequency` (L371) just returns `guest_tick_frequency()`.
  - `KeInsertQueueDpc` (L1178) takes the global lock, but is not on a hot path.
- **Already fine:** the uncontended `RtlEnterCriticalSection` path (see item 4).

## Proposed cvars

With a cvar off, the current code runs unchanged.

> **Session 1 proposal.** The cvars that actually landed, all default OFF, are in "Session 2 → Batch-1 change list".

| cvar | default | item |
|---|---|---|
| `host_timer_resolution_ms` | 1 (0 = off) | 1 |
| `host_disable_power_throttling` | true | 1, 8 |
| `precise_guest_sleep` | true | 2 |
| `wait_timeout_round_up` | true | 3 (claim) |
| `cs_adaptive_spin` / `cs_spin_count` | true / 1000 (tune) | 4 |
| `object_lookup_fast_path` | false until the stress test passes | 5 (claim) |
| `spinlock_pause_spin` / `spinlock_spin_count` | true / 4096 | 6 |
| `high_res_guest_timers` | true (dropped in session 2) | 7 |
| `clock_lockfree` | true | 9 |

Code under `src/core/*` may not see cvars. Pass flags in at startup, the way `EnableAffinityConfiguration()` is called.

## Verification plan for next session

1. **Toolchain.**
   - Use Agent 2's `env/devshell.ps1` and `env/compile-one.ps1`. They did not exist at 12:30.
   - Fallback: VS 2022 17.10 (MSVC 14.40), with CMake and Ninja from VS CommonExtensions.
2. **Unit tests.** Build the `unit_tests` target (`tests/unit/CMakeLists.txt`):
   - existing: `kernel/object_table_test`, `core/chrono_test`, `core/fiber_test`
   - new: the kernel tests from items 2, 3 and 7
3. **Regression scripts.** `tests/regression/test_timer_wait.py`, `test_timer_lifecycle.py`, `test_interrupt_tls.py`.
   - They are Linux-oriented (clang++, `resource`, `os.killpg`, `sched_getaffinity`) and need a Windows port.
   - They exercise TimerQueue, not Win32Timer.
4. **Benches to add in `bench/agent11/`.**
   - Setup: standalone C++, built with `cl /O2 /std:c++20 /EHsc` into `build/agent11/`. Report the median of 5 runs, and note AC vs battery and idle vs loaded.
   - (a) `bench_cs`:
     - Guest-style CS: big-endian `lock_count` CAS with an event fallback.
     - Uncontended, then 2 and 4 threads at 50/500 ns hold.
     - Spin 0 vs pause-spin.
     - Report ns/acquire and kernel waits per acquire.
   - (b) `bench_tls`: thread_local lookup plus byteswap, get and set.
   - (c) `bench_waitsignal`:
     - Two threads ping-ponging on auto-reset events.
     - Variants: no lock; plus the global `recursive_mutex` taken twice (today); plus a `shared_mutex` (proposed).
   - (d) `bench_sleep`:
     - `Sleep(1)`, `SleepEx(1, TRUE)`, and high-res timers at 0.5, 1 and 2 ms, each with and without `timeBeginPeriod(1)`.
     - `SwitchToThread` vs `Sleep(0)`.
     - The table at the top is the "before".
   - (e) `bench_spinlock`: `SwitchToThread` on every failed CAS vs TTAS + pause, at 2, 4 and 6 threads.
   - (f) `bench_clock`: a replica of the mutex-based `UpdateGuestClock` vs a seqlock, at 1, 2 and 6 threads.
5. **In-game.**
   - Take frame-time traces with the sample profiler **off**, since it raises the timer resolution itself.
   - Toggle each cvar on its own.
   - Count per second: `KeDelayExecutionThread` calls and their intervals, and contended-CS kernel waits.

## Files that need `@@claim` (not owned by me)

- `src/system/xobject.cpp` (items 3, 5, 11) and `include/rex/system/xobject.h` (StashHandle ordering)
- `src/system/util/object_table.cpp` and its header (item 5)
- `src/system/runtime.cpp`: the item 1 call site at L124, unless the xboxkrnl module init is used instead
- `src/system/kernel_state.cpp`: review of TLS slot allocation
- CMake: link `winmm`, only if we use `timeBeginPeriod` rather than `NtSetTimerResolution`

## Not read (for next session)

- **`REX_QUERY_TIMEBASE` definition.** Probably in a generated header; I skipped the generated and recompiled dirs to save battery. It decides how hot item 9 is.
- **`REX_LOG_NOISY_IMPL` behaviour in release** (`include/rex/logging/macros.h`).
- **`src/system/`:**
  - `xsemaphore.cpp`, `xmutant.cpp`, `thread.cpp`, `thread_state.cpp`
  - `kernel_state.cpp`: AllocateTLS and the other users of the global lock
  - `xobject.cpp` L232-370 in detail: the WaitMultiple and SignalAndWait bodies
- **`src/core/` and the atomics header:**
  - `include/rex/thread/atomic.h`, `src/core/atomic_win.cpp`
  - `src/core/timer_queue.cpp`, `src/core/threading_posix.cpp`, `src/core/fiber_*`
- **`src/kernel/`:**
  - `src/kernel/crt/threading.cpp`
  - the rest of `xboxkrnl_threading.cpp`; only the hot entries were read
  - `xboxkrnl_module.cpp`, the candidate call site for item 1
- **`include/rex/hook.h`:** the per-import cost of REX_EXPORT marshalling.
- **Game-side callers of `__imp__RtlEnterCriticalSection`** in rexlego (`native_lock_elide.cpp`, `crash_guards.cpp`).
- **`tools/gpu-aot` frame-pacing notes**, and the `tests/regression/` scripts other than the three listed.


---

## Session 2 (task #10, re-issued 17:52)

Paths are relative to `DimensionsRecomp/rexglue-sdk/`. Line numbers are the current tree (19:25).

### Batch-1 change list (dev OFF build 1, cut-off 20:15)

**Rule (18:50):** OFF by default unless proven identical. Every behaviour change below is behind a cvar that defaults OFF.

**What still differs from the baseline with every cvar at its default:**
1. **C.4 stash order** in `xobject.cpp`: write the handle first, then the signature with a release store. Approved always-on by Agent 1 at 18:50. Every current reader holds G, so it can't observe the new order.
2. **Part A** in `object_table.cpp`: `RemoveHandle` takes G before `LookupTable` (a use-after-free fix). Approved always-on by Agent 1; **landed 19:09** after Agent 12's review ([agent12-gcr-review.md](agent12-gcr-review.md), ask 5: safe, no new lock edge; in its S2 replica the old order made 153 writes into freed table blocks in 3 s, A's order 0).
3. **`SleepPrecise`** (an existing function) now keeps its per-thread high-res timer in a thread_local RAII holder, which closes the handle at thread exit. Same timer flags, same arm, same wait: proven identical, minus a handle leak.

**No existing header was edited.** Three new headers are included only by the `.cpp` files below, so none is in the generated-code PCH closure:
- `include/rex/threading_timeout.h`
- `include/rex/threading_timing.h`
- `include/rex/threading_suspend.h`

| File | Change | Cvar = default | Identical when OFF |
|---|---|---|---|
| [threading_win.cpp](<workspace>/DimensionsRecomp/rexglue-sdk/src/core/threading_win.cpp#L124-L280) | `ConfigureHostTiming` / `RestoreHostTiming` (L226, L256): `timeBeginPeriod` through winmm loaded with `LoadLibraryExW(SEARCH_SYSTEM32)`, so no link change; the EcoQoS opt-out through `SetProcessInformation(ProcessPowerThrottling, IGNORE_TIMER_RESOLUTION)`; on success it logs `Host timer resolution set to N ms (background opt-out on/off)` (L252), which is the R1 check. `AlertableSleepPrecise` (L207). `WaitUntilSuspended` (L266). `Timer::Create*Timer` (L518, L528) stay standard timers: see "High-res `Win32Timer`" below. | the runtime.cpp cvars below | yes: every new branch is skipped at the defaults |
| [threading_posix.cpp](<workspace>/DimensionsRecomp/rexglue-sdk/src/core/threading_posix.cpp) | no-op stubs for the new functions (checked by eye; Windows can't compile it) | — | n/a |
| [runtime.cpp](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/runtime.cpp#L38-L43) | cvars (L38-43); `ConfigureHostTiming` in `Setup` when not in tool mode (L144); `RestoreHostTiming` in `Shutdown` (L320) | `host_timer_resolution_ms=0`, `host_timer_throttling_optout=false` | yes |
| [xthread.cpp](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xthread.cpp#L1069-L1095) | `Delay`: precise path (L1071); TLS fix (L378, L928, L945); suspend guard (L1028) | `precise_guest_sleep=false`, `tls_bounds_fix=false`, `guest_suspend_guard=false` | yes: old code verbatim in every `else` branch |
| [xobject.cpp](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/xobject.cpp#L35-L104) | `TimeoutTicksToMs` → `NtTimeoutToMillis` (L263); `StashHandleOrdered` (L74, used at L445 and L539); `GetNativeObject` fast path (L463); `ObjectTableExclusiveScope` (L53) held across the first-use create branch (L495), Agent 12's condition for C | `wait_timeout_round_up=false`, `object_lookup_fast_path=false` | yes, apart from C.4 (the scope is a no-op with the fast path off) |
| [clock.cpp](<workspace>/DimensionsRecomp/rexglue-sdk/src/core/clock.cpp#L26-L160) | seqlock guest clock: `SetGuestTickRatioLocked` (L67), `ReadGuestClockLockFree` (L107), `UpdateGuestClock` (L154) | `clock_lockfree=false` (applied when the rate is set) | yes: `clock_den_` stays 0, so the lock-free read returns false at once |
| [object_table.cpp](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/util/object_table.cpp#L27-L119) | lock T, with its rules in a comment (L37-49), plus `TableWriteLock` (L80); lookup fast path (L436); writers (`Reset`, `Resize`, `AddHandle`, `RemoveHandle`, `PurgeAllObjects`, `Restore`, `RestoreHandle`); part A in `RemoveHandle` (L318-321); `table_write_depth_ == 0` asserts in `Restore` / `RestoreHandle` (L561, L576) | `object_lookup_fast_path=false` (latched at `ObjectTable` construction) | yes, apart from part A (the asserts always hold with the fast path off) |
| `src/kernel/xboxkrnl/xboxkrnl_rtl.cpp` (helper B) | bounded, time-limited spin in contended `RtlEnterCriticalSection`: cvars L50-61, `CpuRelax` + `SpinForCriticalSection` L412-449, hook in `RtlEnterCriticalSection_entry` L464-472 | `cs_spin=false`, `cs_spin_ns=5000` | yes: purely additive diff, old loop verbatim after the hook (I reviewed the diff read-only) |
| `src/kernel/xboxkrnl/xboxkrnl_threading.cpp` (helper B) | TTAS pause loop in `xeKeKfAcquireSpinLock` instead of `SwitchToThread` on every failed CAS; yields only after 10 us: cvar L48-54, `AcquireSpinLockPauseSpin` L978-1014, hook L1023-1026 | `spinlock_pause_spin=false` | yes: purely additive, old loop verbatim (reviewed) |

**Compile checks:** every file above passes `env\compile-one.ps1 <file> -SyntaxOnly` with exit 0; the only warnings are ones already in the untouched code. Most recent checks:
- threading_win.cpp at 19:21, after adding the R1 log line;
- object_table.cpp at 19:18, after the `Restore` asserts and lock-order comments;
- xobject.cpp at 19:10, after part A and the create-branch scope;
- runtime.cpp at 19:07, after removing the high-res `Win32Timer`;
- helper B's two files at 19:03;
- xthread.cpp and clock.cpp at 18:52-18:56.

**Recommended ON set** for A/B and for a later default flip:
- `host_timer_resolution_ms=1`
- `host_timer_throttling_optout=true`
- `precise_guest_sleep=true`
- `wait_timeout_round_up=true`
- `clock_lockfree=true`
- `tls_bounds_fix=true`
- `cs_spin=true`
- `spinlock_pause_spin=true`

**Experimental, keep OFF:**
- `object_lookup_fast_path`: also forces the suspend guard on.
- `guest_suspend_guard`: Agent 12 judged it safe (19:13). It stays OFF until Agent 3's test G (50 pause cycles) passes, then can default ON. Ship it together with the `SetGuestPaused` fix below.

### What each change does, and why

**Item 1: host timer resolution.**
- Session 1 measured the process timer at 15.625 ms; `Sleep(1)` has a median of 15.03 ms.
- `timeBeginPeriod(1)` runs once at `Runtime::Setup`, paired with `timeEndPeriod` at `Shutdown`.
- The EcoQoS opt-out keeps the resolution on Windows 11 while the window is minimized or occluded.
- **High-res `Win32Timer`: not possible as specified, so removed (19:06).** `SetWaitableTimer` rejects a completion routine on a `CREATE_WAITABLE_TIMER_HIGH_RESOLUTION` timer with `ERROR_INVALID_PARAMETER` (87), for relative and absolute due times, with and without a period (`bench/agent11/probe_hr_timer.cpp`, Windows build 26300; output `build/agent11/probe_hr_timer.txt`). `Win32Timer` passes a completion routine whenever a callback is set, and `XTimer` sets one for every guest timer with a DPC/APC routine. With the `high_res_guest_timers` cvar on, those timers would never have fired (helper A's `timer_highres_check` check 1: 0/10 APCs; check 4: no periodic ticks). The cvar and `CreateWin32WaitableTimer` are gone; guest timers are standard waitable timers again, byte-identical to the baseline. With `host_timer_resolution_ms=1`, standard timers already fire on a 1 ms grid (check 3 below). A real high-res guest timer needs a second design: an APC-less high-res timer plus a dispatcher thread that queues the callback, and an auto-reset timer must not have its signal consumed by that thread. Next batch.
- High-res timers without a completion routine work (relative, absolute, periodic, manual-reset), so `SleepPrecise` / `AlertableSleepPrecise` (no completion routine) are unaffected.
- Risk: a little more idle power, per-process since Windows 10 2004.
- Before/after numbers: see "Bench results".

**Item 2: timeouts.** Two fixes:
- `KeDelayExecutionThread` and timed waits truncated to ms: 0.5 ms became a yield or spin, and 1.9 ms became 1 ms, which then rounded up to 15.6 ms.
- Absolute (positive) NT timeouts became 0.

`include/rex/threading_timeout.h` does the conversion in constexpr code:
- relative times round up;
- absolute times are measured against guest system time, and a deadline in the past gives 0;
- finite waits saturate at `0xFFFFFFFE`, so a finite timeout never becomes `INFINITE`.

`Delay` scales guest to host time in 100 ns units, then sleeps on the thread's high-res timer (alertable variant: `AlertableSleepPrecise`, which reports APCs as `X_STATUS_USER_APC`). A 0 interval keeps the old yield path. Tested by `bench/agent11/test_timeouts.cpp`: 0 failures.

**Item 5: lock-free guest clock.** A seqlock over `{host_base, guest_base, num, den}`, written only under `tick_mutex_` in `SetGuestTickRatioLocked`.

Memory-model argument:
- **Writer:** `seq+1` (relaxed), release fence, parameter stores (relaxed), then `seq+2` with a release store.
- **Reader:** acquire load of `seq`, relaxed parameter loads, the host tick, an acquire fence, then a relaxed re-load of `seq`. It accepts only an even, unchanged `seq`.
- If the reader sees any store from a newer writer section, fence-to-fence synchronization makes that writer's odd `seq` visible to the re-load, so the reader retries.
- If the first load saw a completed section's `seq`, all of that section's stores are visible.
- Every field is a `std::atomic`, so there is no data race.
- The rate change rebases at "now", so the clock is continuous.
- Exactness: `(d/den)*num + (d%den)*num/den`; the publisher checks `num*den < 2^64`. With the usual 50 MHz guest clock and 10 MHz QPC, the ratio is 5/1 and exact.
- After 16 failed tries, the reader falls back to the locked path.
- It also fixes the old locked clock's drift: with two readers the old clock ran about 6% fast, because a stale host sample moved `last_host_tick_count_` backwards; with non-integer ratios it ran slow. See "Bench results".

**Item 6: TLS bounds.**
- `GetTLSValue` checked `slot*4 > tls_total_size_`, which is both off by one and against the wrong bound. `SetTLSValue` used `>=` against the same wrong bound. Both index from `tls_dynamic_address_`, which comes after the extended data, so out-of-range slots read and wrote past the block.
- `KeTlsAlloc`'s bitmap is padded to groups of 4 (`SetProcessTLSVars`), but the per-thread block was not.
- With `tls_bounds_fix`: round the slot count up to a multiple of 4, and bound by the slot area in 64-bit arithmetic.
- It is a cvar only because of the batch rule. For in-range slots the behaviour is identical.

**Items 3 and 4** (helper B): see [agent11-s2-cs-spinlock.md](agent11-s2-cs-spinlock.md) for the diff, tables and risks. 2 threads, medians of 5-9 interleaved reps, machine load 62-100%:
- **CS spin** (`cs_spin`): one CAS, then pause + read with a CAS only when the lock reads free, for up to `cs_spin_ns` (5 us, steady_clock checked every 16 pauses; time-based because a pause costs 54-149 ns depending on P/E core) and at least the guest spin count. Hand-off safe: a woken waiter keeps `lock_count >= 0`, so the -1 → 0 CAS can't barge.
  - Contended, 50 and 500 ns holds: 9-106x less wall time per acquire, kernel waits cut 100-1500x, less CPU per op.
  - 2000 ns holds: 1.7-6x faster, less CPU. 5000 ns holds: 1.35-2x faster, CPU -15% to +19%.
  - Uncontended Enter+Leave: cvar on -1.6 to +1.3 ns, cvar off +0.3 (P) / +1.9 ns (E), against an A/A noise of ±0.24 ns (layout effects of the MSVC replica).
- **Spinlock TTAS** (`spinlock_pause_spin`): contended acquire wait p50 588-686 ns and p99 1.4-2.8 us, against p50 0.15-8 ms for the old SwitchToThread loop (none/ee/pe affinities); throughput 5-26% better, CPU per acquire 0-20% higher. Uncontended: identical within noise.
- Risks: a spinner burns up to 5 us per contended Enter if the owner is preempted; a huge guest spin count (max 65280) with `cs_spin` on can spin for milliseconds, the same order as the old tight CAS loop.

**Item 7: global mutex.** The design and memory-model argument are in [agent11-global-mutex-design.md](agent11-global-mutex-design.md); Agent 12 reviewed it against its GCR map in [agent12-gcr-review.md](agent12-gcr-review.md): A safe, always-on; B safe, default ON after test G; C safe once the create branch holds T (done). Implemented:
- **A:** always on, landed 19:09.
- **B:** `guest_suspend_guard`. Hold G (and T) across `SuspendThread` + `GetThreadContext(CONTEXT_CONTROL)` when suspending another thread.
- **C:** `object_lookup_fast_path`, plus the always-on C.4 stash order. T is a file-static SRW `std::shared_mutex`, re-entrant for writers through a thread_local depth. No `Release` or destructor ever runs under T. Per Agent 12's ask 1, `GetNativeObject`'s first-use branch now holds T exclusive from before `new XEvent/XMutant/XSemaphore` until the stash is written (G → T order, nests with `AddHandle`'s T section), so a stale handle that aliases the reused slot can't get a half-built object.
- **Agent 12's other C conditions (done 19:16, `object_table.cpp`):**
  - `Restore` and `RestoreHandle` assert `table_write_depth_ == 0`. They hold T without G, so a lookup inside them would take G after T. The assert is always true with the fast path off.
  - A comment at `table_lock_` records the rules: T shared is a leaf (never taken twice; in Agent 12's S1 a recursive shared acquire deadlocks once a writer is queued), and G or U (`XFile::unlocked_read_lock_`) is never taken under T.

### Found along the way: a latent pause hang

- With `pause_when_unfocused=true` (default false), `ReXApp::SetGuestPaused` (`src/ui/rex_app.cpp:627-675`) suspends every guest thread asynchronously.
- If a thread stops inside any G region, focus regain blocks forever in `GetObjectsByType`, which needs G. A guest `NtSuspendThread` followed by any G-taking call can hang the same way.
- `guest_suspend_guard` fixes it. Agent 3's test G below verifies it.
- **A second hazard, found by Agent 12 (its ask 4). This exists with the guard on or off, and `rex_app.cpp` is not my file, so it is reported here, not fixed:**
  - `SetGuestPaused(true)` logs and pauses audio after it has suspended every guest thread.
  - `SetGuestPaused(false)` allocates in `GetObjectsByType` while every guest thread is still stopped, so the UI thread can block on a heap or log lock that a stopped thread holds.
  - Fix: keep the `object_ref`s collected at pause time and resume from that list first, before anything that logs or allocates. This matters for test G: a hang there does not by itself implicate the guard.
  - Agent 12 is fixing it as task #17. Per Agent 1 (19:20), test G runs with that fix ON, and B goes ON only after test G passes.
  - **Confirmed by the dump from test G's control re-run (23:22):** with the old order, the UI thread deadlocks in `AudioSystem::Pause`'s fence wait. The audio worker sits in a guest callback, waiting on guest threads that have just been suspended. Details in "Test G results (#23) → Control re-run with a dump".
  - Agent 12's new rule: no G or T region may call into the UI thread synchronously, because the guard adds a UI thread → G edge.

### Bench results

Run 19:10-19:17 by `bench/agent11/run_s2.ps1`, using helper A's exes in `build/agent11/a/`; raw output is in `build/agent11/a/<bench>.txt`. 5 runs each, at most 2 threads.

> [!WARNING]
> Other agents kept the machine at 94-100% CPU load for the whole run (each bench logs `GetSystemTimes`). Absolute latencies are inflated, so compare OLD with NEW, not with session 1.

**Sleep and timed waits** (`bench_sleep 5 40`). Each value is the median of the 5 run medians, in ms; brackets give the range of the run medians.

| Call | OLD (no tBP) | NEW (tBP 1 + opt-out) |
|---|---|---|
| `Sleep(1)` | 16.08 [14.84..22.03] | 4.65 [1.52..23.01] |
| `SleepEx(1, TRUE)` | 17.54 | 4.00 |
| `WaitForSingleObjectEx(ev, 1, FALSE)` | 15.96 | 2.47 |
| normal waitable timer, 1000 us | 15.39 | 3.79 |
| high-res waitable timer, 1000 us | 5.12 | 5.42 |

- **Session 1,** on a quieter machine, measured `Sleep(1)` at 15.03 ms and a high-res timer at 2.63 ms.
- **Spread:** NEW `Sleep(1)` was 1.80 ms in run 1 and 1.52 ms in run 2. In run 5, at 100% load, OLD and NEW were both about 22 ms: CPU starvation, not the timer, dominated.
- **Guest paths** (OLD rows from the OLD phase, NEW rows from the NEW phase):
  - `Delay(1 ms)`: 16.08 → 5.42 ms.
  - A 1.5 ms wait timeout: 15.96 → 5.31 ms. OLD truncates it to 1 ms; NEW rounds it up to 2 ms.
- **Sub-ms `Delay(0.5 ms)`:**
  - OLD yields: `SwitchToThread` / `SleepEx(0)` took 1.76 / 2.17 ms under this load, and microseconds when the machine is idle.
  - NEW sleeps on the high-res timer: 3.59 ms here, 1.21 ms in runs 1-2.
  - This is by design. The guest asked for 0.5 ms, and the old yield turns polling loops into spin loops. Watch for it in R2.
- **The timer resolution is per process.** `NtQueryTimerResolution` reported a current resolution of 1.0 ms during the OLD phase (another process had raised it), yet OLD `Sleep(1)` still took 16 ms.
  - Since Windows 10 2004, one process's request doesn't apply to another, so the game must call `timeBeginPeriod` itself.
  - For the same reason, `NtQueryTimerResolution` can't serve as the R1 check (see the A/B plan).

**Timer behaviour** (`timer_highres_check 5`). Exit code 1 is the expected result.
- **Check 1:** high-res timers with a completion routine delivered 0/10 APCs (FAIL). This is the finding behind removing the high-res `Win32Timer`. Normal timers delivered 10/10.
- **Checks 2 and 5:** PASS. They cover manual-reset high-res timers, and cancelling after `WAIT_IO_COMPLETION` (the `AlertableSleepPrecise` path).
- **Check 3,** 2 ms one-shot error, given as median (p90):
  - With tBP on, normal timers are as accurate as high-res ones:
    - relative: +0.20 ms (+0.58);
    - absolute, on the SDK's coarse clock: +0.25 (+1.79);
    - absolute, on the precise clock: +0.34 (+1.13).
  - With tBP off, normal timers are late by +6.7 ms (relative) and +13.2 ms (absolute).
  - So R1 alone fixes guest timers.
- **d2** (`QueryHostSystemTime`, coarse vs precise): the medians are about equal, but the coarse base fires up to 0.9 ms early (min -0.92 ms) and has the wider p90. Low value; see "Rejected ideas".
- **Check 4,** 16 ms periodic (normal timer with an APC): the mean period was 28-29 ms with tBP off and on.
  - Ticks were lost to wake-up latency under this load: only one timer APC can be queued at a time.
  - It is the same with and without tBP, and the high-res variant (nan) went with the removal.
  - Re-measure in a quiet window.

**Guest clock** (`bench_clock 5`). ns per read, median of 5 runs:

| Config | OLD (mutex) | NEW (seqlock) |
|---|---|---|
| 1 thread, ratio 1/1 | 138 | 117 |
| 1 thread, ratio 5/3 | 193 | 156 |
| 2 threads, 1/1 (T1 / T2) | 385 / 287 | 112 / 118 |
| 2 threads, 5/3 (T1 / T2) | 383 / 329 | 108 / 112 |

- For reference, a bare `QueryPerformanceCounter` cost 53-65 ns in the same runs. NEW cost 41-47 ns in the quieter smoke run.
- **New finding: the OLD clock is inaccurate.** Drift = guest elapsed / (host elapsed × ratio). NEW is exactly 1.0000 in every run. OLD is wrong in two ways:
  - **Slow, at 0.83, with a 5/3 ratio.** Each call truncates `delta*num/den`, losing the fractional guest tick every time. The default 5/1 ratio divides exactly, so this needs a non-default `guest_time_scalar`.
  - **Fast with two readers: drift 1.08 at 1/1 and 1.06 at the real 5/1 ratio (medians; max 1.39).**
    - A reader samples the host clock before it takes the lock (`clock.cpp` L162).
    - If another thread updates in between, the first reader then sets `last_host_tick_count_` backwards (L172-174), and the next update counts that interval twice.
    - In the bench's tight loop the guest clock ran about 6% fast. In the game, the error grows with how often two threads read the clock at once.
  - `clock_lockfree=true` fixes both.
- **Monotonicity,** with a writer rebasing concurrently: the SDK reader had 0 step-backs in every mode. The late-QPC positive control stepped back 17 times, so the check can detect step-backs.

**Wait/signal round trip** (`bench_waitsignal 5 3`; 4 guarded calls per round trip).
- p50 per round trip: NONE 22,670 ns, OLD 23,647 ns, NEW 23,251 ns.
- The guarded calls are invisible next to the ~23 µs wake-up under this load. The means (46-58 µs) are dominated by outliers.
- Signature mismatches: 0.

**Handle lookup** (`bench_lookup 5 100000`). Thread 1, ns per lookup + Release, median of 5 runs:

| Mode | OLD mean / p50 / p99 / p99.9 | NEW mean / p50 / p99 / p99.9 |
|---|---|---|
| 1 thread | 150 / 87 / 127 / 435 | 77 / 66 / 104 / 306 |
| 2 threads, same handle | 158 / 80 / 3,184 / 63,283 | 180 / 77 / 1,935 / 13,929 |
| 2 threads, different handles | 206 / 82 / 1,204 / 50,973 | 117 / 78 / 2,584 / 31,297 |
| 2 threads, T2 holds G 2 us of every 20 us | 112 / 79 / 146 / 3,727 | 89 / 64 / 130 / 313 |

- The fast path halves the uncontended mean.
- It removes the wait for G holders: p99.9 drops from 3.7 µs to 0.31 µs, and lookups over 1 µs from 0.33% to 0.036%.
- Two threads on handles in the same table are mixed:
  - p99.9 is better (4.5x on the same handle, 1.6x on different handles);
  - but p99 on different handles is worse (2.6 vs 1.2 µs), and so is the share of lookups over 1 µs on the same handle (3.1% vs 1.5%), from SRW cache-line traffic.
- This is why C stays experimental: R4 decides it.

### In-game A/B plan for Agent 3 (frame pacing and stalls)

**Every run:**
- One binary: dev OFF build 1.
- Pass cvars as `--name=value` (harness `-Cvar`).
- Sample profiler **off**: `rexlego/src/sample_profiler.cpp:100` calls `timeBeginPeriod(1)` itself and would hide item 1.
- `pause_when_unfocused=false`, except in test G.
- AC power, inside an announced quiet window, with the same scene, route and length as the baseline.
- At least 3 runs per configuration; report the median across runs.
- **Metrics:** from `perf.csv`:
  - frame-time median, p99, p99.9 and max;
  - stalls: count of frames over 33.3 ms and over 100 ms;
  - process CPU %, as a power proxy for R1 and R3.

**Runs** (cumulative, so each step isolates one group):

| Run | Cvars added on top of the previous run | Expect |
|---|---|---|
| R0 | none (defaults) | baseline |
| R1 | `host_timer_resolution_ms=1 host_timer_throttling_optout=true` | biggest effect: fewer long frames if pacing uses `Sleep` or timed waits; CPU a little higher |
| R2 | `precise_guest_sleep=true wait_timeout_round_up=true` | no sub-ms spin-yields, no absolute-timeout polling; tighter pacing |
| R3 | `cs_spin=true spinlock_pause_spin=true clock_lockfree=true tls_bounds_fix=true` | fewer kernel waits under contention; watch CPU % (spin). `clock_lockfree` also makes the guest clock exact, where the old one could run fast under concurrent reads (see "Bench results"), so anything paced by the guest clock may shift slightly |
| R4 | `object_lookup_fast_path=true` (forces the suspend guard) | less serialization on `Ke*` and handle calls |

- **If time allows:** each cvar alone against R0, in this order: `host_timer_resolution_ms`, `precise_guest_sleep`, `cs_spin`, `wait_timeout_round_up`, `object_lookup_fast_path`, `spinlock_pause_spin`, `clock_lockfree`.
- **Check for R1:** the game log must contain `Host timer resolution set to 1 ms (background opt-out on)`. `ConfigureHostTiming` logs it at info level, and logs a warning instead if the request fails.
  - Don't use `NtQueryTimerResolution` for this check. It reports the system-wide value, not this process's: it read 1 ms during the OLD phase of `bench_sleep`, while `Sleep(1)` still took 16 ms.
- **Test G** (functional, not timed; the driver and the exact commands are in "Test G driver (#19)" below):
  - Agent 12's `rex_app.cpp` pause fix (task #17, `pause_safe_order=true`) ON in both halves, plus `pause_when_unfocused=true`;
  - the game pauses and unpauses itself through `--debug_pause_cycle_ms=1000 --debug_pause_cycle_count=50` (Agent 12, 20:15 batch), because posted focus messages can't move SDL's focus state;
  - 50 cycles with `guest_suspend_guard=false`, then 50 with `=true`;
  - a hang is a pause that hasn't ended within `PeriodMs` + 5 s, the UI thread silent for 10 s, or a crash; count hangs.
  - The guard must show 0 hangs before it can default ON.
- **Abort rule:** if a configuration crashes or hangs, record the cvars and the log tail, and skip that configuration.

### Test G driver (#19)

**Status (22:00): done.** The driver was written, self-tested and probed on `build/baseline-bin` by 20:08. Test G ran on devoff1-bin at 21:32 (#23; see "Test G results (#23)" below). The early-stop rule was fixed after that run (21:45).

**Files** (`bench/agent11/`, usage in its README):

| File | What it does |
|---|---|
| `testg_launch.ps1` | Starts one game in `build/agent11/runs/<time>-<name>/`. The bin dir is hard-linked, the harness toml is copied with `user_data_root` inside the run dir, and `--log_file` points into the run dir. It passes `--pause_when_unfocused=true` plus `-Cvar "a=1,b=2"`, runs the driver, then always closes the game: WM_CLOSE, a kill after 30 s, from a `finally`. `cvars.txt` records which binary defines each cvar. It refuses to start while another `legodimensions.exe` runs. |
| `testg_driver.ps1` | Cycles and verdicts. `watch`: the game toggles itself and the driver reads `game.log`. `post`: the driver posts the focus messages. Exit 0 PASS, 1 FAIL, 2 setup error, 3 INCONCLUSIVE. It writes `testg_report.txt` and a `.csv`. On a hang, or when the cycles stop early, it also writes `hang-<time>-threads.txt` (state and wait reason per thread) and a minidump. |
| `testg_win.cs` | Win32 helpers (Add-Type): window lookup, PostMessage, WM_NULL ping, log tailer, MiniDumpWriteDump. |
| `testg_selftest.ps1` | Runs the driver's verdict logic on synthetic logs. No game needed. |
| `testg_check.ps1` | Compiles `testg_win.cs` and parses the scripts. |
| `testg_session.ps1` | (#23) The whole test G session in one command; see "Test G results (#23)". |
| `testg_dump.ps1`, `testg_dump.cs` | (#23) An offline reader for the driver's minidumps; see "Test G results (#23)". |

**Hang rules (watch mode):**
- A cycle is one "Guest suspended" line followed by "Guest resumed".
- **LATE:** the pause lasted longer than `PeriodMs` + 5 s, by log timestamps.
- **HANG:** no resume within that time, by the driver's clock.
- **NO-RESUME:** a second suspend arrives before the resume.
- Also a FAIL: the UI thread doesn't answer WM_NULL for 10 s (the unpause runs on that thread), or the game exits.
- **INCONCLUSIVE:**
  - there was no first pause within 180 s;
  - or the cycles stopped short of `-Cycles` (no new pause within `PeriodMs` + 10 s of the last resume) while the UI thread still answers. The driver writes the threads file and a dump in this case too.
- **Since 21:45:** if the cycles stop while the UI thread is silent, the driver waits for the 10 s UI rule (FAIL) instead of calling the run INCONCLUSIVE. Before the fix, the stop rule could win the race, and in the #23 control run it did.

**Why posted focus messages can't drive test G** (SDL 3.5.0, `thirdparty/sdl3/src/video/windows/SDL_windowsevents.c`):
- WM_NCACTIVATE (L1204), WM_ACTIVATE (L1216), WM_SETFOCUS (L1239) and WM_KILLFOCUS (L1245) all end in `WIN_UpdateFocus` (L324-333).
- That function recomputes focus as `GetForegroundWindow() == hwnd`. It acts only when the result differs from SDL's keyboard focus and points the way the message does.
- So a posted message never changes SDL's focus state, and only a real foreground change pauses or resumes the game:

  | Where the game window is | had | has | Posted loss | Posted gain |
  |---|---|---|---|---|
  | Hidden desktop (never foreground) | false | false | ignored | ignored |
  | Visible desktop, game in front | true | true | ignored | ignored |

**Probe** (20:00:30 on `build/baseline-bin`; run dir `build/agent11/runs/20261121-200030-probe-post/`):
- **Command:** `testg_launch.ps1 -BinDir build\baseline-bin -Name probe-post -Driver post -Cycles 5 -BootSec 40`. The launch and the posting happen in one command, as the hidden-desktop rule requires.
- **Setup seen by the driver:**
  - window `SDL_app` 1295x757, found 2 s after start, "not foreground";
  - foreground window 0x0, which is the hidden desktop;
  - input desktop `Default`.
- **Cycles 1 and 2:** all 6 `PostMessage` calls returned ok, and the log has 0 "Guest suspended/resumed" lines. Both cycles were `ignored`, so the driver gave up after 2 in a row: **INCONCLUSIVE (exit 3), as the SDL analysis predicts.**
- **Health:**
  - the UI thread answered 23/23 WM_NULL pings (slowest 506 ms);
  - 0 error/critical log lines;
  - WM_CLOSE reached 3 windows, and the game exited cleanly ("Title terminated; hard-exiting process.").
- **First attempt, 19:54:49** (run dir `...-195449-probe-post`), hit a driver bug:
  - PowerShell variable names are case-insensitive, so the result list `$cycles` was the `[int]$Cycles` parameter, and the driver threw before cycle 1.
  - The launcher then exited without closing the game. The game had exited by 19:58, because a game dies with the command that started it.
  - Fixed: the list is now `$results`, and the launcher closes the game in a `finally`.

**Self-test** (20:01:52; `build/agent11/selftest/20261121-200152/`): all 8 scenarios and all 6 log-tailer checks pass.

| Scenario | Exit | Driver verdict |
|---|---|---|
| pass | 0 | PASS |
| late | 1 | LATE (paused 2000 ms against a 1300 ms limit) |
| hang | 1 | HANG; a minidump of the stand-in process is written |
| second suspend | 1 | NO-RESUME |
| stopped | 3 | INCONCLUSIVE |
| idle | 3 | INCONCLUSIVE |
| dead pid | 2 | setup error |
| post mode, no window | 2 | setup error |
| stopped, UI silent (added 21:51) | 1 | FAIL: the UI thread is silent for 8 s while the guest runs; the threads file and a dump are written |

**Self-test re-run** (21:51:03; `build/agent11/selftest/20261121-215103/`), after the race fix: all 9 scenarios and the 6 log-tailer checks pass.
- In `stopped, UI silent`, the "game" is a WinForms window that stops pumping messages, with ghosting disabled. The driver waits past the stop rule (6.3 s) and fails at the 8 s UI limit; the whole scenario took 10.8 s.
- `hang` now also checks the threads file.

**Decision: test G uses watch mode with Agent 12's default-OFF cvars** (`src/ui/rex_app.cpp` L77-83 and L643-673, in the 20:15 batch):
- **`debug_pause_cycle_ms`** (0 = off): 15 s after the guest starts, a host thread asks the UI thread for `SetGuestPaused(true)`, waits N ms, asks for `SetGuestPaused(false)`, and waits N ms again.
  - This goes through the normal path, so `pause_safe_order` and `guest_suspend_guard` apply.
  - The game logs `Debug pause cycle: every N ms, M cycles (0 = unlimited), first pause in 15 s`.
- **`debug_pause_cycle_count`** (0 = unlimited): stops after N full cycles, ending unpaused.
- **Watch mode works on a hidden desktop:** it needs only the log and the process, and the WM_NULL ping needs the window, which the launching command can see.
- **Real focus changes during a run are harmless.** They go through the same `SetGuestPaused`, so they only shift pauses: a focus-loss pause ends at the next timer unpause, within 2 x `PeriodMs`.

**Test G commands** (devoff1-bin; one game at a time; each half is one command of about 2.5 min):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_launch.ps1 -BinDir <devoff1-bin> -Name testg-b-off -Driver watch -Cycles 50 -PeriodMs 1000 -Cvar "pause_safe_order=true,guest_suspend_guard=false,debug_pause_cycle_ms=1000,debug_pause_cycle_count=50"
powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_launch.ps1 -BinDir <devoff1-bin> -Name testg-b-on -Driver watch -Cycles 50 -PeriodMs 1000 -Cvar "pause_safe_order=true,guest_suspend_guard=true,debug_pause_cycle_ms=1000,debug_pause_cycle_count=50"
```

- **Before trusting a run:**
  - `cvars.txt` must list all four cvars as found. In devoff1-bin, `pause_safe_order` and `debug_pause_cycle_*` are in the exe (ReXApp is linked into it), and `guest_suspend_guard` is in `rexruntime.dll`. If any is NOT FOUND, the build predates the batch.
  - `game.log` must contain the `Debug pause cycle: every 1000 ms, 50 cycles` line.
- **Pass:** exit 0 and `VERDICT: PASS - 50 cycles, every one resumed in time`.
- **On a FAIL:**
  - `testg_report.txt` holds the per-cycle table and the last 40 log lines;
  - `hang-*.dmp` holds every thread's stack (no PDBs: resolve with `legodimensions.map`).
- **On a game the runner started** (user-started, visible desktop): pass the same four cvars and a `--log_file`, then run the driver alone: `testg_driver.ps1 -GamePid <pid> -Log <game.log> -Mode watch -Cycles 50 -PeriodMs 1000 -FromStart`.
- **Reading the two halves:**

  | b-off | b-on | Meaning |
  |---|---|---|
  | any | PASS | B may default ON |
  | HANG | PASS | the hang B fixes |
  | HANG | HANG | look at #17 or the dump first, not at B |

### Test G results (#23)

**Run:** 21:32:06-21:38:42, one command (`testg_session.ps1` with its defaults), after Agent 8's devoff1 functional boot freed the slot at 21:29. Session file: `build/agent11/runs/testg-session-20261121-213206.txt`.
- **Binary:** `build/agent2/devoff1-bin`, which is dev OFF build 1 (NATIVE_GPU=OFF). Agent 2 built it from the S1 snapshot (the 20:15 batch) and staged it at 21:08. The exe and `rexruntime.dll` are dated 21:07; MANIFEST sha256 1E81AA5E… (per Agent 2).
- **Pre-check:** the build defines all four cvars. `pause_safe_order` and `debug_pause_cycle_*` are in the exe (ReXApp is linked into it); `guest_suspend_guard` is in `rexruntime.dll`.
- **Every run:**
  - hidden desktop, so no real focus changes;
  - `--pause_when_unfocused=true --debug_pause_cycle_ms=1000 --debug_pause_cycle_count=50`;
  - the driver in watch mode with `-Cycles 50 -PeriodMs 1000`, so a pause may last 6 s and the UI thread may stay silent for 10 s.

| Run | Cvars | Verdict | Cycles | Paused ms (min / median / max) | Guest threads | UI thread (WM_NULL pings) | End |
|---|---|---|---|---|---|---|---|
| Half 1 | `pause_safe_order=true guest_suspend_guard=false` | **PASS** | 50 ok | 891 / 1006 / 1484 | 24, then 25 | 105, 1 unanswered; slowest answer 1.7 s; longest silence 2.1 s | WM_CLOSE; exited |
| Half 2 | `pause_safe_order=true guest_suspend_guard=true` | **PASS** | 50 ok | 685 / 1006 / 1316 | 25 | 96, 1 unanswered; slowest answer 1.8 s; longest silence 2.2 s | WM_CLOSE; exited |
| Control | `pause_safe_order=false guest_suspend_guard=false` | INCONCLUSIVE by the driver's rules; in fact a **hang** | 4 ok, then none | 1002 / 1004 / 1015 | 29, then 30 | 30, 8 unanswered; longest silence 9.5 s | ignored WM_CLOSE; killed after 30 s |
| Control re-run (23:21) | `pause_safe_order=false guest_suspend_guard=false` | **FAIL**, as intended: the hang, now with a dump | 0: hung in the 1st pause | - | 20 suspended (thread list) | 25, 9 unanswered; slowest answer 1.6 s; longest silence 10.0 s | ignored WM_CLOSE; killed after 30 s |

- **Run dirs** (`build/agent11/runs/`): `20261121-213209-testg-b-off` (pid 34356), `20261121-213432-testg-b-on` (pid 97256) and `20261121-213718-testg-control` (pid 24852). Each holds `game.log`, `testg_report.txt` and `.csv`, `cvars.txt`, `cmdline.txt`, `stop.txt` and `summary.txt`.
- **Both halves:** one `Debug pause cycle: every 1000 ms, 50 cycles` line, 50 "Guest suspended" and 50 "Guest resumed" lines, 0 stray resumes and 0 error/critical lines. Every pause ran on the UI thread (one tid per run).
- **Margins:**
  - The spread around 1000 ms is queueing on the UI thread, which runs both requests.
  - The longest pause (1484 ms) is a quarter of the 6 s limit.
  - The longest UI silence (2.2 s) is about a fifth of the 10 s limit.

**The control, step by step** (from `game.log` and the driver report):
1. 21:37:34.591: the `Debug pause cycle` line. The first pause came 15 s later.
2. Cycles 1-4 were normal (1002-1015 ms, tid 23960). The last "Guest resumed (30 threads)" is at 21:37:56.705.
3. The 5th pause was due about 1 s later. No "Guest suspended" line came, and `game.log` ends there (96 lines, no errors). The UI thread stopped answering about 1.5 s after the last resume. It was still silent when the driver stopped, 9.5 s later.
4. The game ignored WM_CLOSE, and the launcher killed it after 30 s (`stop.txt`).

- **Reading (21:41):** this is consistent with the hazard that #17 removes (Agent 12's ask 4; see "Found along the way" above).
  - The old path (`pause_safe_order=false`, `rex_app.cpp` L790-812) suspends every guest thread first. Only then does it pause audio and log "Guest suspended".
  - Something after the suspend loop blocks forever, before the log line. That matches what we saw: no log line, and a silent UI thread.
  - **The 23:21 re-run's dump pins it down.** The audio pause waits for the audio worker, and the worker is stuck in a guest callback, waiting on the suspended guest. No lock in G, the heap or the log is involved, so B can't fix it. See "Control re-run with a dump" below.
- **The ignored WM_CLOSE** fits a stuck UI thread. `OnDestroy` also joins the debug-cycle thread, which waits on the stuck pause.
- **Why INCONCLUSIVE, with no dump:** two driver rules raced.
  - "Cycles stopped" fires at the last resume + `PeriodMs` + 5 s + 5 s = 11 s.
  - The UI rule needs 10 s of silence. The silence began about 1.5 s after the last resume, so the UI rule would have fired at about 11.5 s.
  - The stop rule won by about 0.5 s, and the driver took dumps only on FAIL.

**Driver fix** (`testg_driver.ps1`, 21:45; see "Self-test re-run" above):
- If the cycles stop while the UI thread is silent, the driver keeps polling.
  - If the silence lasts, the UI rule fails the run. The FAIL reason reads "guest running: no 'Guest suspended' since the last 'Guest resumed' X s ago".
  - If the UI thread answers, the run is INCONCLUSIVE, as before.
- A stop short of `-Cycles` also takes a dump now.
- Before every dump, the driver writes `hang-<time>-threads.txt`: tid, state, wait reason, priority and CPU ms for each thread, from `Process.Threads`.
  - A dbghelp minidump records SuspendCount 0 even for suspended threads, so the wait reason `Suspended` is how to find them.
  - The report gets a `threads:` line with the suspended tids.

**New tools for #23** (`bench/agent11/`, usage in its README):
- **`testg_session.ps1`** runs the session above in one command.
  - It refuses to start if the bin lacks the four cvars or another game runs.
  - It runs half 1, half 2 and the control. The control runs only while no other `*-bin` dir is staged in `build/agent2`, unless `-ForceControl` is given (added at 22:00 for the re-run).
  - It runs `testg_dump.ps1` on any dump, adds the report's `threads:` line, and writes the session file.
- **`testg_dump.ps1` / `testg_dump.cs`** (my subagent, 20:35) are an offline minidump reader.
  - For each thread: name, RIP/RSP, start address and a heuristic stack. Return addresses are checked against a preceding CALL, and named from `legodimensions.map` or the nearest export.
  - Then a summary of the waiting, running and UI threads.
  - Tested on self-test dumps (20:35), then on a game dump at 23:23 (the control re-run below; 1.0 s, 363,104 map symbols). Its "UI thread" guess was wrong there; see below.

**Control re-run with a dump (23:21:31-23:23:05)**, in Agent 8's slot after quiet window 2:
- **Command:** `testg_session.ps1 -Only control -ForceControl`. `-ForceControl` was needed because `native2-bin` was staged by then. Same binary (`devoff1-bin`, 21:07) and settings as above, with `pause_safe_order=false guest_suspend_guard=false`.
- **Verdict: FAIL, as intended.** The driver's reason: "UI thread did not answer WM_NULL for 10000 ms after 0 cycles". So the test sees the hang, and since the 21:45 fix it also takes a dump.
- **Files** (`build/agent11/runs/`):
  - Run dir `20261121-232139-testg-control` (pid 78608): `hang-232215.dmp` (477,538 B), `hang-232215-threads.txt`, `hang-232215.txt` (the `testg_dump.ps1` stack report), `testg_report.txt`, `game.log` and `stop.txt`.
  - Session file: `testg-session-20261121-232134.txt`.
- **Timeline** (`game.log`: 44 lines, 0 error/critical):
  1. 23:21:50.147: the `Debug pause cycle` line, written by t76036. The first pause was due 15 s later, at about 23:22:05.
  2. 23:22:03.073: the audio endpoint opened, and the `SDLAudioP19` thread was created. So audio had started 2 s before the pause.
  3. The last log line is at 23:22:04.532. There is no "Guest suspended" line, so the very first pause hung.
  4. 23:22:15: the UI rule fired after 10 s of silence, and the driver wrote the thread list and the dump.
  5. 23:22:57: the game ignored WM_CLOSE, and the launcher killed it after 30 s.
- **Threads** (`hang-232215-threads.txt`): 77 threads, 20 of them in wait reason `Suspended`. The 20 are `Main XThread` (24648) and the 19 `XThreadNNNN` threads. No host XThread is suspended (XMA Decoder, Audio Worker, GPU Commands, GPU VSync, Kernel Dispatch), which is what the old path intends.
- **Where it hangs: a three-link wait cycle in the dump.** S1 sources: `build/agent2/snap1/.../src/ui/rex_app.cpp`, and `audio_system.cpp` from `build/agent2/snap1-backup-S2/` (S2 has Agent 12's #22 version).
  1. **UI thread 76036**, the main thread (start `wWinMainCRTStartup`), has this stack: `RunMainMessageLoop` → `ExecutePendingFunctionsFromUIThread` → `ReXApp::SetGuestPaused+0x1BC` → `AudioSystem::Pause+0x7B` → `msvcp140!_Cnd_wait` → `SleepConditionVariableSRW`.
     - That is `pause_fence_.Wait()` in `AudioSystem::Pause` (`audio_system.cpp` L370-378). The old path calls `audio->Pause()` (`rex_app.cpp` L804-806) after its suspend loop (L792-802).
     - The `GetObjectsByType+0xE1` and `XThread::Suspend+0x11B` entries between those frames are stale return addresses, left by the earlier calls in the same function.
  2. **Only the Audio Worker (59800) signals that fence**, when it sees `paused_` at the top of its loop (L122-127). It is a host thread, so it isn't suspended. But it is inside a client callback:
     - `AudioSystem::WorkerThreadMain+0x71B` → `FunctionDispatcher::Execute` (L149) → guest `sub_83E99BA8+0x28C` → `KeWaitForMultipleObjects_entry+0x149` → `XObject::WaitMultiple` → `thread::WaitMultiple` → `WaitForMultipleObjectsEx`.
     - So the game's audio callback is waiting on guest dispatcher objects.
     - A `KeSetEvent` thunk return address sits just above that wait. That fits "wake the guest mixer, then wait for it", but a heuristic scan can't prove the frame is live.
  3. **Every guest thread is suspended**, so nothing signals those objects. The callback never returns, the worker never reaches the fence, and the UI thread waits forever.
- **So it is a wait cycle, not a lock held by a stopped thread.** No G, heap or log lock is part of it, so B can't fix it. The "old order with B ON" run isn't needed to classify it.
- **Why the safe order fixes it:** with `pause_safe_order=true`, `audio->Pause()` runs *before* any suspend (`rex_app.cpp` L751-753), while the guest still runs. The callback finishes, the worker signals the fence, and only then are the threads suspended (L767-769). Halves 1 and 2: 100 of 100 pauses, 0 hangs.
- **Why it is intermittent:** it needs the worker to be inside a callback that waits on a guest thread at the moment of the suspend. That happened at the 5th pause at 21:37, and at the 1st pause here, 2 s after the audio endpoint opened.
- **Pre-existing:** the old path is the original order. Both `pause_when_unfocused` and `pause_safe_order` default to false, so a user who turns on `pause_when_unfocused` gets the old order and can hang the game on focus loss.
  - Making the safe order the default, or deleting the old branch, is Agent 12's call (#17) for a later batch. No fix in batch 1. Agent 1 (23:41) asked for an S3 proposal to make it the default; see "S3 proposal" at the end.
- **The analyzer on a game dump:**
  - Its "UI thread" guess (77152, a DXGI vblank waiter) is wrong. 76036 is listed among its candidates, with the `SetGuestPaused` frame. In SDL builds the UI thread is the main thread (start `wWinMainCRTStartup`).
  - A "nearest export" name whose offset is hundreds of KB (for example `HostToGuestFunction<…SwitchToFiber_entry…>+0x22ED2B`) identifies only the module.

**Conclusions:**
- **#17 `pause_safe_order=true`:** 100 cycles in two runs, with 0 hangs. With the old order, the same build hung at the 5th pause (21:37) and at the 1st (23:22). The dump shows the exact wait cycle that the safe order breaks. Test G supports the fix.
- **B `guest_suspend_guard`:** 0 hangs in 50 cycles with the safe order, so it is eligible for ON (decision table: "any | PASS").
  - Agent 1 (21:56): B goes into the next timing window, with `pause_safe_order=true`.
  - B OFF passed too, so in 50 cycles no thread was stopped inside a G region, the hazard that B removes. Test G shows that B is safe, not that it is needed.
- **Sent to Agent 8 (21:41):** R4 = R3 + `--object_lookup_fast_path=true --guest_suspend_guard=true`.
  - In full: `--host_timer_resolution_ms=1 --host_timer_throttling_optout=true --precise_guest_sleep=true --wait_timeout_round_up=true --cs_spin=true --spinlock_pause_spin=true --clock_lockfree=true --tls_bounds_fix=true --object_lookup_fast_path=true --guest_suspend_guard=true`.
  - R0-R3 are unchanged. If time allows, also R0 + `--guest_suspend_guard=true` alone. Profiler off, `--pause_when_unfocused=false`.
- **Not covered:**
  - the native ON build (not staged at 21:32);
  - a user-started game on a visible desktop, with real focus changes;
  - the old order with B ON. That run is no longer needed: the dump shows no G in the cycle, so B can't break it.

### Rejected ideas and caveats

- **`NtSetTimerResolution(0.5 ms)`**: not used. `timeBeginPeriod(1)` through a dynamically loaded winmm is documented and needs no CMake change.
- **Lock-free table reads with no lock at all**: rejected in the design (section 6). They need epoch reclamation.
- **`Clock::QueryHostSystemTime`** uses the coarse `GetSystemTimeAsFileTime` (`src/core/clock_win.cpp:33-37`), so absolute `Win32Timer` due times can be off by up to one tick.
  - d2 measured it. With tBP on, coarse and precise absolute due times have about the same median error (+0.25 vs +0.34 ms), but the coarse base fires up to 0.9 ms early and has a wider p90 (+1.79 vs +1.13 ms).
  - Switching to `GetSystemTimePreciseAsFileTime` is optional, low-value next-batch work.
- **The sample profiler** suspends threads with a raw `SuspendThread`, which the guard doesn't cover. Keep it off for A/B runs.
- **Per-thread EcoQoS opt-out** (session-1 item 8) was not done in this batch.

## #27 exit-path fix (batch 3, assigned 22:02)

**Status:** decided and staged in `build/agent11/exitfix/`. Not yet in the live tree. It goes in only after Agent 2 has taken S2 **and** Agent 10 rates it SAFE (#25). Test results are in "Tests" below.

### The bug

Paths in this section are relative to `DimensionsRecomp/rexglue-sdk/` unless noted.

- **`HalReturnToFirmware_entry`** calls CRT `exit(0)` (`src/kernel/xboxkrnl/xboxkrnl_hal.cpp:34`).
- **`XamShowDirtyDiscErrorUI_entry`** calls `exit(1)` (`src/kernel/xam/xam_ui.cpp:542`), after its dialog or its FATAL log banner.
- Both run on the **guest thread** that called the export. The UI, render, audio and other guest threads are still running.
  - CRT `exit()` first runs the EXE's atexit table on that thread: the static destructors of the EXE (rexlego plus ReXApp, which is linked into the exe), the atexit handlers, and the caller's `thread_local` destructors. It then flushes stdio.
  - Only after that does it call `ExitProcess`.
  - So EXE objects are destroyed while other threads may still use them. Example: the function-local `static std::ofstream` that the native render thread writes `frames.csv` through (`rexlego/src/gpu_native/device.cpp:2298`).
- Neither path runs `OnShutdown`. That is called only from `OnDestroy` (`src/ui/rex_app.cpp:845`).
- **Linkage:** both files are in target rexruntime, which ships as `rexruntime.dll`. `rex::FlushLogging()` is defined in that DLL too. `legodimensions.map` (devoff1-bin) imports `__imp_?FlushLogging@rex@@YAXXZ` from `rexruntime.dll`. So the new call stays inside the DLL and flushes the one logger registry.

### What the window-close path does

`ReXApp::OnClosing` (`src/ui/rex_app.cpp:693-707`), on the UI thread, in order:
1. logs;
2. sets `shutting_down_`;
3. calls `kernel_state()->TerminateTitle()`;
4. logs "Title terminated; hard-exiting process.";
5. calls `rex::FlushLogging(); std::_Exit(0);`.

It never calls `OnShutdown`. Two game-side exits already do the same `FlushLogging` + `_Exit`:
- the update restart (`rexlego/src/legodimensions_app.h:97-100`: `toypad_app::StopIfStarted(); rex::FlushLogging(); std::_Exit(0);`);
- the non-native close watchdog.

### Decision

Both exports end with **`rex::FlushLogging(); std::_Exit(code);`**:
- exit codes 0 and 1 are kept;
- every existing log line is kept, and none is added;
- `#include <cstdlib>` is added;
- the old TODO comments are replaced by a short reason.

No TerminateTitle, no OnShutdown, no cvar: the fix is always on. The diff is `build/agent11/exitfix/exitfix.diff`: +19/-6 lines in two hunks per file.

Rejected alternatives:
- **The full OnClosing sequence including OnShutdown.**
  - `OnShutdown` belongs to the app layer, which the kernel can't reach. It is only reached through `OnDestroy`, whose guest-thread join is known to deadlock (`rexlego/src/legodimensions_app.h:283-284`, owner V20 dump). That is why the game's Quit goes through RequestClose → OnClosing.
  - It also tears down the runtime that the calling guest thread is running on.
- **TerminateTitle, then `_Exit`** (OnClosing without the UI parts).
  - `KernelState::TerminateTitle()` (`src/system/kernel_state.cpp:1009-1067`) ends a **guest** caller's own thread at L1059-1066 (`XThread::GetCurrentThread()->Terminate(0)`) and never returns. So the `_Exit` after it would never run, and the process would not exit. `XamLoaderTerminateTitle` (`src/kernel/xam/xam_info.cpp:291-294`) relies on exactly that.
  - Working around it needs a `kernel_state.cpp` change or a helper thread.
  - It adds the 200 ms drain. The drain wakes guest waits, so a straggler could fault into the crash popup, whose `ExitProcess(0)` would lose exit code 1.
  - `ExitProcess` ends the stragglers anyway.
- **`TerminateProcess`.**
  - The game's Quit Game (`ExitNativeGameNow`, `rexlego/src/native_process_exit.h`) and the native close watchdog (`legodimensions_app.h:409-428`) use it. It also skips DLL_PROCESS_DETACH.
  - Not chosen, so that SDK hard exits stay uniform with OnClosing and the update restart.
  - Agent 8 saw a non-native process linger 14-34 s after OnClosing's `_Exit(0)` (`perf-notes/agent8-first-boot.md:232-243`). If a trace shows that the linger is DLL detach, revisit all SDK hard exits together.

### What changes, exactly (UCRT, desktop app; confirmed by the unit test below)

| Phase | Old `exit(code)` | New `FlushLogging` + `std::_Exit(code)` |
|---|---|---|
| Log flush | via the CRT stdio flush in phase 2 | explicit, before anything else |
| EXE atexit table: EXE static destructors and atexit handlers, on the guest thread **while the other threads run** | yes (the hazard) | **no** |
| Caller's `thread_local` destructors, and the CRT stdio flush inside `exit` | yes | no |
| `ExitProcess`: other threads killed, then DLL_PROCESS_DETACH on the caller (statics of `rexruntime.dll`, SDL and drivers) | yes | yes |
| Within that detach, `ucrtbase.dll` flushes every open `FILE*` (dynamic CRT, as in the game; the static `/MT` CRT does not) | yes (little left by then) | **yes**: the unit test's unflushed CSV row survived `_Exit` under `/MD` and was lost under `/MT` |

The new path is a **strict subset** of the old one. The removed phase is exactly the hazardous one. It is what OnClosing does after TerminateTitle, and what the update restart does.

### Does anything rely on atexit handlers or static destructors?

No. The details:

| What | Owner / where | On these paths before | After the fix |
|---|---|---|---|
| atexit registrations | grep of `rexlego/src`, `rexglue-sdk/src` and `include`, 22:24 | none. Only a commented-out `atexit` (`src/core/threading_posix.cpp:1513`) and `std::set_terminate` (`src/core/exception_handler_win.cpp:294`), which neither path triggers | same |
| Logs | spdlog with synchronous sinks; `log_flush_interval` 0, so no flusher thread | flushed by the CRT stdio flush | flushed by `rex::FlushLogging()` (`src/core/logging.cpp:327-332`) |
| Guest saves | Win32 `WriteFile`, unbuffered (`filesystem_win.cpp:154`) | durable | durable |
| Achievements | `SaveUnlockState` at unlock time, local ofstream plus temp file (`achievement_manager.cpp:151,265`) | not exit-dependent | same |
| Toypad figures | `ToypadFigure::Save()` with a local ofstream (`emulated_toypad.cpp:167-171`) | not exit-dependent | same |
| Settings / config | `SaveConfig` / `SaveConfigPatch` on user action (`mod_menu.cpp:454`, `settings_registry.cpp:204`, `settings_overlay.cpp:867/904`) | nothing at exit | same |
| perf CSV | `g_csv_file` FILE*, flushed every 60 frames; `FlushCsv` only from `Runtime::Shutdown` (`runtime.cpp:323`) | stdio flush kept the tail rows, while the render thread could still be writing | the tail rows (up to 59, ~1 s) should still be written by `ucrtbase.dll`'s detach flush, after the render thread is gone (unit test, `/MD`), as on window close. If a killed thread held that stream's lock, Windows ends the process at the flush instead, and the tail is lost |
| Native `frames.csv` | EXE function-local `static std::ofstream` (`device.cpp:2298`) | its destructor ran on the guest thread while the render thread could still write to it | the destructor no longer runs. The tail probably still reaches the disk through the same detach flush, because MSVC's `filebuf` writes into its `FILE*`'s buffer (not tested). Same as window close. The native watchdog's `TerminateProcess` loses it |
| Audio (#22) | `AudioSystem::Shutdown` runs only from `OnDestroy` (`agent12-io-memory.md:502`) | not reached | not reached; `ExitProcess` ends a parked worker |
| Tracy | manual lifetime, shut down only on the Shutdown path (`perf/counter.h:86-118`) | in-flight data lost | same |
| Timer resolution (#10) | `RestoreHostTiming` / `timeEndPeriod` only in `runtime.cpp:320` | released by the OS at exit | same |
| Toypad helper process | job object with KILL_ON_JOB_CLOSE (`toypad_app.cpp:131-155`) | killed with the game; LegoToypad.ini session changes lost (written only on its WM_CLOSE) | same |
| Discord | IPC pipe | closed with the process; presence clears | same |
| Tools | `bench/agent8/run/timing-env.ps1:50` uses OnClosing's 'hard-exiting' line as the clean-close cue; nothing parses the HalReturnToFirmware / DirtyDisc lines | — | log lines unchanged; no 'hard-exiting' line added |

Notes on the table:
- **Calling `FlushCsv` here is unsafe.** It `fclose`s the file while the render thread may still be writing to it. Under the dynamic CRT the unit test shows the tail is flushed at DLL detach anyway, so a flush-only API in `counter.cpp` (not my file) would only matter for a static-CRT build.
- **Why `rex::FlushLogging()` is still needed:** under `/MD` the detach flush would also have kept the log line (`_Exit1_noflush`, `/MD`: log 1), but under `/MT` it was lost (log 0). The explicit flush also writes the log before the process starts dying, so a crash or the orphaned-lock termination during DLL detach can't eat the last lines.
- **PGO** is not in the tree. If a PGO GEN build lands, note that the profile is written from atexit (`agent3-build.md:244`). Every hard exit would then need `__llvm_profile_write_file()` first: OnClosing, the update restart, and these two.

### Tests (no game)

All four scripts are in `bench/agent11/`. Their results are recorded in `build/agent11/exitfix/`.

- **`exitfix_stage.ps1`** does the staging:
  - Pristine copies go to `pristine/`.
  - Each exact text edit must match exactly once, and line endings are preserved.
  - Outputs: `HASHES.txt`, plus `exitfix.diff` with repo-path headers, so `git apply` also works from the repo root.
  - `-Apply` copies staged → live. It refuses unless both live files still equal their pristine hash.
  - `-Revert` copies pristine → live.
  - Staged at 22:27. Hashes:

    | File | Pristine | Staged |
    |---|---|---|
    | hal | `4A0F84AE84BC…` | `AB359E1D6C4D…` |
    | xam_ui | `03E89D1119CB…` | `0A314946FDB9…` |

- **`exitfix_check.ps1`** is a source lint. Per file it checks:
  - no CRT `exit(` outside comments;
  - `#include <cstdlib>`;
  - the export's last two statements are `rex::FlushLogging(); std::_Exit(<code>);`;
  - all of the export's original `REXKRNL_ERROR` lines are still there (1 and 7);
  - no 'hard-exiting' text;
  - the hash matches `HASHES.txt`.

  `-Pristine` is the negative control and must fail.
- **`exitfix_syntax.ps1`** runs clang `-fsyntax-only` with the exact dev-SDK flags: `-Wall -Wextra`, Release entry from `env/compile-one.ps1 -PrintOnly`, PCH dropped. It compiles the pristine copy and the candidate and diffs the diagnostics. `-Live` checks the live tree instead.
- **`exitfix_test.ps1`** builds `exit_test.cpp` twice (`/MD` like the game, and `/MT`) and `exit_test_dll.cpp` (`/MD /LD`).
  - Each mode calls the exit from a non-main thread. A heartbeat thread runs, one thread is blocked, and the main thread waits like a UI thread.
  - Markers record each of these: an atexit handler, an EXE static destructor, the same destructor running while the heartbeat was still alive ("raced", the hazard), a DLL static destructor (DLL detach), a log FILE* flushed before the exit, and an unflushed CSV FILE*.
  - It asserts the exit code and the markers for `exit0`, `exit1`, `_Exit0`, `_Exit1` and `terminate1`. `_Exit1_noflush` and the CSV column are informational.

Results:

- **Lint, 22:46.** It only reads the two files, so it ran during quiet window 2.
  - `exitfix_check.ps1`: exit 0, 12/12 PASS (6 per file). Report: `build/agent11/exitfix/check-staged-2247.txt`.
  - `exitfix_check.ps1 -Pristine` (the negative control): exit 1, with exactly the expected 6 FAILs (`check-pristine-2247.txt`):
    - a CRT `exit(` call at hal line 34 and xam_ui line 542;
    - no `#include <cstdlib>` in either file;
    - the last statements are `exit(0);` and `exit(1);`, not `rex::FlushLogging(); std::_Exit(n);`.

    The other checks pass on pristine, as they should: the `REXKRNL_ERROR` counts (1 and 7), no "hard-exiting" text, and the hashes.
- **Syntax, 23:14** (Agent 1 ended quiet window 2 at 23:09). `exitfix_syntax.ps1`: exit 0, `RESULT: PASS`. Report: `build/agent11/exitfix/syntax-20261121-231400.txt`.
  - clang `-fsyntax-only` with the dev-SDK Release flags (`-Wall -Wextra`, PCH dropped), one compile at a time, 8-20 s each.
  - hal: pristine and candidate both exit 0 with 0 diagnostics.
  - xam_ui: pristine and candidate both exit 0 with the same 8 pre-existing warnings (6 `-Wunused-parameter`, 2 `-Wunused-private-field`, none in the edited code). Only their line numbers move: +2 from the include block, and +6 after the edited export. No new diagnostics.
- **Unit test, 23:15.** `exitfix_test.ps1`: exit 0, `RESULT: PASS (all asserted cells match)` in all 12 cases (6 modes × 2 CRTs). The three binaries built without warnings. Report: `build/agent11/exitfix/test-20261121-231514.txt`.

  | crt | mode | code | atexit | static | raced | dll | dllraced | log | csv (info) | exit_ms |
  |---|---|---|---|---|---|---|---|---|---|---|
  | md | exit0 / exit1 | 0 / 1 | 1 | 1 | **1** | 1 | 0 | 1 | 1 | 257 / 254 |
  | md | _Exit0 / _Exit1 | 0 / 1 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 128 / 132 |
  | md | _Exit1_noflush | 1 | 0 | 0 | 0 | 1 | 0 | 1 (info) | 1 | 126 |
  | md | terminate1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 34 |
  | mt | exit0 / exit1 | 0 / 1 | 1 | 1 | **1** | 1 | 0 | 1 | 1 | 230 / 226 |
  | mt | _Exit0 / _Exit1 | 0 / 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 113 / 120 |
  | mt | _Exit1_noflush | 1 | 0 | 0 | 0 | 1 | 0 | 0 (info) | 0 | 112 |
  | mt | terminate1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 |

  What it shows:
  - **The hazard is real.** With `exit()`, the EXE static destructor ran on the calling thread while the heartbeat thread was still alive (`raced` = 1), under both CRTs.
  - **`std::_Exit` removes exactly that phase.** The exit codes are kept, the atexit handler and the EXE static destructor don't run, and DLL_PROCESS_DETACH still runs (`dll` = 1), after the other threads are gone (`dllraced` = 0).
  - **Stdio under `/MD`, the game's CRT.** `ucrtbase.dll`'s detach flushes open `FILE*` streams, so the unflushed CSV row survived `_Exit`. Even `_Exit1_noflush` kept its log line. Under `/MT` both were lost. This corrects the perf CSV and `frames.csv` rows of the reliance table above, which first said the tail is lost.
  - **`TerminateProcess`** skips DLL detach (`dll` = 0) and loses the CSV row under both CRTs.
  - **`exit_ms` is not a real-world cost.** It includes the test's own 100 ms liveness probes, one in the EXE static destructor and one in the DLL destructor.
- **Lint re-run, 23:17**, after the window, as Agent 10's condition asks: staged exit 0, all checks passed (`check-staged-2317.txt`). `-Pristine` exit 1 with the same 6 FAILs (`check-pristine-2317.txt`). The live files were still pristine (`4A0F84AE84BC` / `03E89D1119CB`), and git status showed them clean.

### Landing (batch 3)

1. Wait for (a) Agent 2's S2 snapshot (the batch-2 cut-off) and (b) Agent 10's SAFE rating for #25. (b) came at ~22:43: SAFE, #25 item 10, `perf-notes/agent10-batch2-review.md` S10, with the same condition (apply after S2 and after the post-window checks pass).
2. Run `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\exitfix_stage.ps1 -Apply`. It refuses if either live file changed since 22:27.
3. Run `exitfix_check.ps1 -Live` and `exitfix_syntax.ps1 -Live`.
4. Record the result here, then send `@@done 27`.

**Landed at 23:19.** Both conditions were met: Agent 10 rated the fix SAFE at ~22:43, and `perf-notes/agent2-baseline.md` records S2 as applied at 23:15:03, `verify S2` PASS. S2 copies only the 18 files on Agent 10's include list, which doesn't contain these two, and devoff2 was built from that snapshot (staged 23:18:53). So the change is in neither devoff2 nor native2, and it goes out with batch 3.
- `exitfix_stage.ps1 -Apply`: exit 0. Both live files equalled their pristine hashes before the copy (`apply-2319.txt`).
- After the apply:
  - The live hashes equal the staged ones: `AB359E1D6C4D` (hal) and `0A314946FDB9` (xam_ui).
  - `git status` shows only these two files modified. `git diff --stat`: 19 insertions and 6 deletions, which matches `exitfix.diff`.
- `exitfix_check.ps1 -Live`: exit 0, all 12 checks passed (`check-live-2319.txt`).
- `exitfix_syntax.ps1 -Live`: exit 0, `RESULT: PASS` (`syntax-20261121-231918.txt`).
  - hal: 0 diagnostics in both the pristine copy and the live file.
  - xam_ui: the same 8 pre-existing warnings in both. No new diagnostics.
- **To undo:** run `exitfix_stage.ps1 -Revert`, which restores the pristine copies.
- **mtime fix (00:06), Agent 12's catch.** `Copy-Item` keeps the source's LastWriteTime, so the 23:19 apply left both live files stamped 22:27:02, the time the staged copies were written.
  - **Why it matters:** ninja compares timestamps, not content. An object for either file built from the old text after 22:27 would have looked up to date. An mtime scan for edits since S2 (23:15:03) would also have missed the landing.
  - **Fix:** both live files were stamped 00:06:15 (`LastWriteTime = Get-Date`). Their hashes stayed `AB359E1D6C4D` / `0A314946FDB9`, equal to the staged copies (`touch-0006.txt`).
  - **S2 isn't affected.** It doesn't contain these two files. Agent 2's snapshot step also already stamps its copies with the apply time: snap1's `audio_system.cpp`, which S2 copied in, says 23:15:02, while the live file (same hash) says 21:56:43.
  - **Scripts:** `exitfix_stage.ps1` and `safeorder_stage.ps1` now stamp the live file with the copy time on `-Apply` and `-Revert`, then check the hash.
  - **Test:** `stage_stamp_test.ps1` runs byte-for-byte copies of both scripts in a sandbox under `build/agent11/stamptest/` and checks the hash and the stamp after each step. Result at 00:09: 17/17 PASS (`stamptest/20261122-000920/report.txt`). It also reproduces the hazard: a bare `Copy-Item` kept a 21:01 stamp.

## S3 proposal: `pause_safe_order` default ON (Agent 1, 23:41)

**The ask (23:41):** propose `pause_safe_order` default ON for S3 (today `false` at `rexglue-sdk/src/ui/rex_app.cpp:71`). Send Agent 10 the rationale and the diff for a rating, text only, with no tree edits. `guest_suspend_guard` (B) stays OFF.

**Status:** staged and checked at 23:48-23:50 in `build/agent11/safeorder/`. Nothing under `DimensionsRecomp/**` was edited. Sent to Agent 10 for a rating with this update (~23:55). **Rated SAFE at ~00:13** (see "Rating" below). Agent 12 lands it after window 3 and before S3 is cut (`rex_app.cpp` is Agent 12's #17 file).

### The diff

`build/agent11/safeorder/safeorder.diff` (sha256 `56952876…`): 2 hunks, -5/+7 lines, LF, no BOM. The default is the only code change.
1. **L71-75, the cvar:** `REXCVAR_DEFINE_BOOL(pause_safe_order, false, …)` becomes `true`. The description's last sentence, "Off: the original order", becomes "Off: the original order, which can hang when the guest pauses".
2. **L741-743, the comment** at the top of the safe-order branch in `SetGuestPaused`, grows from 3 lines to 5. It now says "default on" and why:
   ```
   // pause_safe_order (default on; task #17 in perf-notes/agent12-io-memory.md). The original
   // order below can deadlock: in test G (#23, perf-notes/agent11-kernel.md) the audio pause
   // waited on a worker stuck in a guest callback that needed the just-suspended guest threads.
   // The pause picks the path and its unpause follows it, so turning the cvar on or off while
   // the guest is paused cannot strand a thread.
   ```
- **Not changed:** the original branch (L790-812) stays, as the kill switch. No new cvar. B and the rest of #17 are untouched.
- **Hashes** (`HASHES.txt`): live = pristine `E1569868E157…`, staged `11DE333FA4C0…`.
- **Same file test G ran:** the live file equals the S2 copy in `build/agent2/snap1` (last written 19:46:45, before the 20:15 cut-off). `snap1-backup-S2` has no copy, so S2 didn't replace it, and S1 has the same file. `devoff1-bin`, the build test G ran, is S1.

### Rationale

1. **The original order deadlocks, and test G caught it** (see "Test G results (#23)" above). On `devoff1-bin` with `pause_safe_order=false`, 2 of 2 runs hung: at the 5th pause (21:37) and at the 1st (23:22). The 23:22 dump shows a three-link wait cycle:
   - the UI thread is in `AudioSystem::Pause`, in `pause_fence_.Wait()`;
   - the Audio Worker, a host thread that isn't suspended, is inside the game's audio callback (`sub_83E99BA8`), blocked in `KeWaitForMultipleObjects`;
   - every guest thread is suspended, so nothing signals those objects.

   The game then ignores WM_CLOSE and has to be killed.
2. **The safe order breaks that cycle by construction.** `audio->Pause()` runs before any suspend (L751-753), while the guest still runs. So the callback returns and the worker reaches the fence, and only then are the threads suspended (L767-769).
   - Same build and settings: 100 of 100 pauses, 0 hangs (50 with B OFF, 50 with B ON).
   - Paused time was 685-1484 ms, against a 6 s limit. The UI thread's longest silence was 2.2 s, against 10 s.
3. **It also stops the original order's other work while the guest is stopped.** This comes from reading the code, not from a run.
   - The audio worker takes the global critical region G before it reads a client callback (S1 `audio_system.cpp` L137; `AcquireDirect` in S2). A guest thread suspended inside G would block the worker, which gives the same fence deadlock. The safe order pauses audio before any suspend.
   - `XmaDecoder::Pause` runs inside `AudioSystem::Pause` (L380), so it also moves before the suspends.
   - The original pause logs after its suspend loop. The original unpause calls `GetObjectsByType` (an allocation, plus the object-table lock T) while every guest thread is still stopped.
   - The safe pause logs before it suspends. The safe unpause resumes first, from its own list, and only then logs.
4. **Who it affects:** only users who turn on "Pause when the window is in the background". That is `pause_when_unfocused`, default false (`window.cpp:43`), shown in the settings UI at `rexlego/src/ui_theme.cpp:99`. Those are exactly the users who can hit the hang today.
   - `SetGuestPaused` has three callers, all in `rex_app.cpp`:
     - `OnLostFocus` (L825), only when `pause_when_unfocused` is on;
     - `OnGotFocus` (L818), which does nothing unless the guest is paused;
     - the debug cycle (L664), only when `debug_pause_cycle_ms` (default 0) is set.
   - `pause_safe_order` is read only at L745. rexlego never calls `SetGuestPaused`, and no config under `game/` or `harness/` sets either cvar.
5. **No effect on the measurements.** Every runner passes `--pause_when_unfocused=false` (`harness/run-game.ps1:125`, `bench/agent8/run/common.ps1:100`). The matrix files say so, and `matrix-io-level.json:23` says `pause_safe_order` is not part of the A/B. No timing run ever pauses, under either default.
6. **Kill switch and runtime safety:**
   - The cvar stays, so `--pause_safe_order=false` (or the toml) brings back the original order.
   - The unpause follows the path its pause took (`safe_order.active`, L745), so flipping the cvar while paused can't strand a thread.
   - `SafeOrderPause` is never destroyed, so exiting while paused is safe.
   - The cvar isn't in the settings UI, so a user can't turn it off by accident.
7. **B stays OFF, and that's fine.** The cycle involves no lock, so B can't fix it, and the safe order passed with B OFF (half 1, 50 of 50).

### What it doesn't fix (in either order)

- **Host locks held by a stopped thread:** a guest thread can be stopped while it holds a host lock (G, T, the CRT heap or the logger) that the UI thread, or a host thread the UI thread waits on, needs before the unpause.
  - Inside `SetGuestPaused`, the safe order allocates, logs and locks nothing while threads are stopped.
  - The UI thread's other work while the game is paused (the message loop) is the same in both orders.
  - B would cover G and T, but it stays OFF.
  - This was not seen in 100 safe-order cycles.
- **Test conditions:** test G drove the pause with the debug cycle on a hidden desktop, not with real focus changes. It ran on S1, not S3.

### Interactions

- **#22** (Agent 12, in S2) changed `AudioSystem::WorkerThreadMain` and `Shutdown`.
  - `Pause()` and `Resume()` are unchanged.
  - The worker's pause handshake (`paused_` → `pause_fence_.Signal()` → wait for the resume) means the same.
  - Its new `leave()` / `reenter()` calls do nothing unless `audio_shutdown_detach_worker` (default false) is on.
  - So test G's result carries over to S2 and S3.
- **#27** (live since 23:19) touches other files. No interaction.

### Checks (23:48-23:50; no game)

- **`safeorder_stage.ps1`:** `RESULT: PASS`, 11 of 11 (`stage-2348.txt`):
  - BOM and LF unchanged, and no CR added;
  - -5/+7 lines in 2 hunks;
  - added lines at most 100 columns (longest 95);
  - the new default present exactly once, and the old default and "default off" gone;
  - the file 2 lines longer;
  - the live file untouched.
- **`safeorder_stage.ps1 -Check`:** live `E1569868E157` = pristine.
- **`safeorder_syntax.ps1`** (`exitfix_syntax.ps1` adapted; clang `-fsyntax-only` with the dev-SDK flags, PCH dropped): pristine and staged both exit 0 with the same 3 pre-existing header warnings (unused parameters in `xmemory.h` and `rex_app.h`). No new diagnostics (`syntax-20261121-234946.txt`).

### Rating (Agent 10, ~00:13)

**SAFE** (`perf-notes/agent10-batch2-review.md` §11, reviewed 00:00-00:10). Agent 10 checked it against `safeorder.diff` 56952876…, with the live file still pristine.
- **Why:** only the default and the text change, and the kill switch (`--pause_safe_order=false`) stays.
  - The safe pause does the audio pause, the thread snapshot (a lock and an allocation) and the log line while the guest still runs, and then only suspends.
  - The safe unpause resumes first, and only the threads its pause suspended.
- **Three notes that need no change:**
  - `Suspend` raises the guest count before the host call. If that call fails, the safe unpause skips the entry, so the count stays one higher (the original unpause decremented it). Only an exiting or exited thread fails there.
  - "Guest suspended" is logged just before the threads actually stop. This is cosmetic.
  - The risk of a stopped thread holding a host lock is the same in both orders (see "What it doesn't fix" above).
- **#22's ON flip in S3** (per Agent 10): `Pause()` / `Resume()` don't change. The worker's `leave()` / `reenter()` are uncontended CAS operations unless Shutdown runs, so test G's result carries over.
- **Worth doing:** step 5 below, so that the default itself gets tested.
- **Messages (~00:16):** Agent 12 got the rating along with my reply to its mtime note. Agent 1 got the rating, the #27 mtime FYI and a question about the step 5 run.

### Landing, if rated SAFE

1. Agent 10 rates it: **SAFE at ~00:13** (see "Rating" above). **Agent 1 (23:55):** if it's SAFE, Agent 12 (the `rex_app.cpp` owner) lands it after window 3 ends and before S3 is cut.
2. Run `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\safeorder_stage.ps1 -Apply`. It refuses unless the live file still equals pristine `E1569868E157…`. Since 00:09 it also stamps the live file with the copy time, so ninja rebuilds it (Agent 12's catch; see the #27 mtime fix).
3. Then run `safeorder_stage.ps1 -Check`, which should say `staged (applied)`, and `safeorder_syntax.ps1 -Live`. The syntax check is a compile, so not during a quiet window.
4. To undo: `safeorder_stage.ps1 -Revert`.
5. **Optional confirmation on the S3 build:** test G half 1 without an explicit `--pause_safe_order`, so that the default is what gets tested (about 2 min in a game slot). `testg_session.ps1` passes the cvar explicitly today, so this needs a small option in `bench/agent11`. I'll add it if asked. **Agent 10 (~00:13): worth doing.** I asked Agent 1 at ~00:16 for a go and a slot. **Agent 1 (01:20): yes**, on devoff3, in Agent 8's slot right after the devoff3 boot, after the relaunch. The option, self-test and run are written up in "S3 default check" below.

## S3 default check: test G half 1 on devoff3 without `--pause_safe_order` (Agent 1, 01:20)

**The ask (01:20):** Agent 1 said yes to Agent 10's recommendation: test G half 1 on devoff3 (the S3 dev-OFF build), with no explicit `--pause_safe_order`, so that the default itself is tested. It runs **after the agy-grid relaunch**, in Agent 8's slot, right after the devoff3 boot. Until the relaunch: no builds, no game runs, no new work. So the option below is written up here, but it isn't in the script yet.

### State at the relaunch (01:21, read-only checks)

- Nothing of mine is running: no background tasks, and no game since 23:23.
- Live-tree files I changed since the S2 cut (23:15:03). Both are #27, landed at 23:19 and re-stamped at 00:06:15:
  - `DimensionsRecomp/rexglue-sdk/src/kernel/xboxkrnl/xboxkrnl_hal.cpp`: sha256 `AB359E1D6C4DA1B9F2FBE6E3B67094B8D4044E01B21A8B953F8F9F4E2C58D05B`
  - `DimensionsRecomp/rexglue-sdk/src/kernel/xam/xam_ui.cpp`: sha256 `0A314946FDB9FE1ED875483592A22F70E24E62C420A1141E135A8569A6F65311`
- `rex_app.cpp` (Agent 12's file) is still pristine `E1569868E15761D9…` (19:43:51), so safeorder hasn't landed yet. It has to land before S3 is cut, or devoff3 keeps the default OFF.
- Agent 2's staged builds: devoff1, devoff2, native and native2. There's no devoff3 yet.

### The option (to add to `bench/agent11/testg_session.ps1` after the relaunch)

The option is a fourth run, `testg-default`: half 1's settings without `--pause_safe_order`, so the build's default picks the order.
- **Opt-in:** it runs only with `-Only default`.
- **Refuses (exit 2) unless the build has the default-ON change.** On a default-OFF build the run would be the control, which hangs.
- **The marker** is the new help text from `safeorder.diff`, `which can hang when the guest pauses`, which is compiled into the cvar's description.
- `-NoMarkerCheck` skips that check (see self-test step 3).

1. **Header:** under the control's description, add:
   ```
       default  guest_suspend_guard=false and NO --pause_safe_order, so the build's default picks the
                order (the S3 default-ON check). Opt-in: runs only with -Only default, and only on a build
                that carries the default-ON help text (unless -NoMarkerCheck).
   ```
   Under `.EXAMPLE`, add: `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_session.ps1 -BinDir build\agent2\devoff3-bin -Only default`
2. **param:** add a comma after `[switch]$CheckOnly`, then `[switch]$NoMarkerCheck   # 'default' run: skip the default-ON check (only after checking S3's rex_app.cpp hash)`.
3. **After** `Say 'the build defines pause_safe_order, …'` (L62), before the running-game check:
   ```powershell
   # 'default' passes no --pause_safe_order, so the build's own default picks the pause order. On a
   # default-OFF build that is the original order, which hangs (the control), so it needs the S3
   # default-ON change. Its marker is the new help text, compiled into the cvar's description.
   $marker = 'which can hang when the guest pauses'
   if ((($Only -contains 'default') -or ($Only -contains 'testg-default')) -and -not $NoMarkerCheck) {
       $hasMarker = $false
       if (Test-Path -LiteralPath $dll) { $hasMarker = [TestGWin]::ContainsAscii($dll, $marker) }
       if (-not $hasMarker) { $hasMarker = [TestGWin]::ContainsAscii($exe, $marker) }
       if (-not $hasMarker) { Say "NOT STARTED: the 'default' run needs a pause_safe_order default-ON build, and this one lacks its help text ('$marker')"; Save; exit 2 }
       Say "the build carries the pause_safe_order default-ON help text ('$marker')"
   }
   ```
4. **`$runs`:** add a comma after the control entry, then:
   ```powershell
       @{ Name = 'testg-default'; Label = 'half 1 on the build default (no --pause_safe_order, B off)'; Cvar = 'guest_suspend_guard=false'; Control = $false; OptIn = $true }
   ```
5. **Loop:** right after the `-Only` filter (L82), add:
   ```powershell
       if ($r.OptIn -and ($Only -notcontains $r.Name) -and ($Only -notcontains $short)) { continue }
   ```
   Without `-Only`, the session still runs half 1, half 2 and the control, as before.

### Self-test (after the relaunch, before the slot; no game)

1. The script parses with 0 errors. Set `$tk=$null; $er=$null` first, then call `Parser::ParseFile`.
2. Run `testg_session.ps1 -BinDir build\agent2\devoff2-bin -Only default -CheckOnly`. devoff2 is S2, with the default OFF, so it must refuse: exit 2 and "NOT STARTED: the 'default' run needs …".
3. Check that the description is in the binary at all:
   - Run `[TestGWin]::ContainsAscii(<devoff2 rexruntime.dll, then the exe>, 'the unpause resumes them first. Off: the original order')` with full paths (.NET doesn't use PowerShell's location). Expect True.
   - If it's False, the descriptions aren't compiled in, so the marker can't work. Confirm instead that S3's `rex_app.cpp` is the staged `11DE333FA4C0…` (from Agent 2's S3 manifest or the snapshot copy), and run with `-NoMarkerCheck`.
4. `testg_session.ps1 -BinDir build\agent2\devoff2-bin -CheckOnly` (no `-Only`) still exits 0 as before, provided no game is running.
5. Once devoff3 is staged, run `-BinDir build\agent2\devoff3-bin -Only default -CheckOnly`. It should print "the build carries the pause_safe_order default-ON help text". If Agent 8's boot is up, it may then add that another game is running. That's fine.

### The run (Agent 8's slot, right after the devoff3 boot)

- **Command:** `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent11\testg_session.ps1 -BinDir build\agent2\devoff3-bin -Only default`.
  - Run it as one command, because the game lives on that command's hidden desktop.
  - It takes about 3 min: the boot, the 15 s delay, 50 cycles of 1 s paused plus 1 s running, and the close.
- **PASS:**
  - VERDICT PASS, exit 0, 50 of 50 cycles;
  - in the log, 50 suspended and 50 resumed, and no more error/critical lines than half 1 at 21:32;
  - no dump;
  - the run's `cmdline.txt` has no `--pause_safe_order`, so the default picked the order.
- **Afterwards:** give the slot back to Agent 8 at once, report to Agents 1 and 10, and record the result here.
- **If it hangs:** the driver takes the thread list, the dump and the stack report itself. First check the marker line and `cmdline.txt`, because an old build hangs exactly like the control. Then tell Agents 1, 10 and 12 at once.

### Result (02:59-03:01): PASS

Agent 8 ran the command in its slot right after the devoff3 boot, and sent me the paths at ~03:03.
- **Files:** session `build/agent11/runs/testg-session-20261122-025913.txt`, run dir `build/agent11/runs/20261122-025916-testg-default/`.
- **Build:** devoff3 (exe 02:43, `rexruntime.dll` 02:44). The marker check found the default-ON help text.
- **VERDICT: PASS, exit 0, 50 of 50 cycles ok**, with 0 stray resumes. Paused time per cycle: median 1001 ms, max 1019 ms.
- **Log:** 187 lines. 'Debug pause cycle' once, suspended 50, resumed 50, error/critical 0 (half 1 at 21:32 also had 0).
- **UI thread:** 111 WM_NULL pings, 0 unanswered, slowest answer 579 ms.
- **No dump.** It closed cleanly: WM_CLOSE to 3 windows at 03:01:18, then "Title terminated; hard-exiting process".
- **`cmdline.txt` has no `--pause_safe_order`.** It has `--guest_suspend_guard=false --debug_pause_cycle_ms=1000 --debug_pause_cycle_count=50`, plus the usual log, Discord, settings and `pause_when_unfocused` flags. `legodimensions.toml` doesn't set it either, so the build default picked the order.
- **Reading:** S3's default gives the safe order. The old order hung within 4 cycles in both control runs (21:3x and 23:21), so 50 clean cycles with no flag fit a default of ON.
- **Afterwards:** it was Agent 8's own run, so there was no slot for me to hand back. Reported to Agents 1 and 10 at ~03:08.

## S3 TimerQueue: the host timer thread's CPU (task #10 lead, Agent 1, 02:01)

**The ask (02:01):** the `rex::thread::TimerQueue` thread uses 62% of a core in devoff2 and 52% in native2 (window 3; Agent 8's per-thread table, `perf-notes/agent8-window3.md` L121-134). Find out why, and propose a fix behind an OFF cvar.
- **Agent 1 (02:08):** `REX_TIMER_WAIT_BLOCKING` already exists, so devoff2 plus that env var could be a window-4 arm with no rebuild. Check the blocking path at ≤2 threads, get one functional run from Agent 8 (d0t), and send Agent 8 the optional arm spec. No tree edits.
- **Agent 1 (02:55):** keep `timer_queue_precise_wait` staged only. Applying it needs Agent 10's rating and Agent 1's GO. It's an S4 candidate: no build tonight unless the ~04:00 cause report makes a strong case. Put the stage-bench numbers in that report.

### Cause

Paths are relative to `DimensionsRecomp/rexglue-sdk/`.
1. **One timer, 1000 waits a second.** The only TimerQueue user on Windows is `HighResolutionTimer::CreateRepeating(1 ms)` at `src/kernel/xboxkrnl/xboxkrnl_module.cpp:195`, which advances KeTimeStampBundle's TickCount. Each tick is one timed wait in `TimerWaitStrategy` (`src/core/timer_queue.cpp`).
2. **The default spin wait burns a busy phase before every tick.** Each wait makes a fresh `dp::spin_wait`, and checks its deadline only when `next_spin_will_yield()`, which comes after a busy phase of 4092 `_mm_pause`. On this host that phase is about 395 µs on a P core and 236 µs on an E core (bench `spin`). A deadline that has already passed still costs the whole phase.
3. **Then it oversleeps.** After the busy phase come 19 `SwitchToThread` calls, then `sleep_for(1 ms)`, which takes a median 15.4 ms at the default timer resolution (6.9 ms with `timeBeginPeriod(1)`). The ticks missed meanwhile fire back to back, each after its own busy phase: the median gap between callbacks is 0.31-0.38 ms, one busy phase.
4. **So the CPU is about 1000 busy phases a second:** 21-34% of a core in the bench, depending on the core type. The game's 52-62% fits the same loop with a longer busy phase, from lower clocks under load on this 15 W part, or from a busy hyperthread sibling on a P core. That part is a hypothesis; I haven't measured it. d11 (1 ms resolution) was also 62%, which fits, because the busy phase doesn't depend on the timer resolution.
5. **TickCount is stale too:** more than 2 ms behind for about half the time in the bench (22% with `timeBeginPeriod(1)`).

### First bench (02:18, game-free; `build/agent11/timerq/results-20261122-021755.txt`)

`bench/agent11/timerq_bench.ps1` builds `bench/agent11/bench_timerq.cpp` against the live `timer_queue.cpp` (single-threaded `cl`), then runs a 1 ms repeating timer for 10 s per row. "Stale" is the share of the time TickCount spends more than 2 ms behind.

| live code | timer thread CPU | callback gap p50 / p99 | stale |
|---|---|---|---|
| spin, default resolution | 30.6% | 0.381 / 13.3 ms | 49.5% |
| blocking, default resolution | 0.5% | 0.001 / 16.2 ms | 83.0% |
| spin, `timeBeginPeriod(1)` | 28.1% | 0.402 / 6.9 ms | 22.1% |
| blocking, `timeBeginPeriod(1)` | 1.4% | 1.105 / 3.4 ms | 4.7% |
| spin, P cores only | 33.7% | 0.387 / 13.2 ms | 49.3% |
| spin, E cores only | 21.1% | 0.242 / 14.0 ms | 51.1% |

### The blocking path (`REX_TIMER_WAIT_BLOCKING`, already in the tree)

- **Sound** (read at ≤2 threads): publishers notify under the same mutex that guards the predicate, `Stop()` takes the lock and notifies, and the idle wait (no timer queued) is `cv_.wait` with no timeout.
- **Its catch:** `cv_.wait_until` ends on an OS timer tick, so at the default resolution TickCount moves in ~16 ms bursts (83-85% stale). At 1 ms resolution it's good: 1.4% CPU, 4.7% stale.
- **d0t** (devoff2 + `REX_TIMER_WAIT_BLOCKING=1`, `framerate_limit=0`, the thread-cpu driver). I sent Agent 8 the spec at 02:30. It's in `bench/agent8/run/matrix-s3-functional.json` as the pair d0f (devoff2, same settings) then d0t, after the B gate, ~03:30.
  - **Pass:** TimerQueue busy ≤ ~3% in `threads.csv` (window 3's d0: 62%), no more >100 ms frames than d0f, a clean close, no dump.
  - **Result:** pending.
- **The window-4 arm (decided at 03:13, after Agent 1's 03:10 ask): d0t**, already in `matrix-window4.json` as the optional arm (see "The arm for tonight and window 4" below). `d11t` (d11's cvars + `REX_TIMER_WAIT_BLOCKING=1`) keeps TickCount fresh, because blocking at 1 ms resolution matches the staged fix in the bench (1.4% CPU, 4.7% stale). But it differs from window 4's reference d0 in 9 settings.

### The proposal: `timer_queue_precise_wait` (default off; staged only)

- **Files:** `build/agent11/timerq/stage/`: the staged `timer_queue.cpp`, `pristine/timer_queue.cpp`, `timerq.diff` and `HASHES.txt`.
  - `src/core/timer_queue.cpp`: pristine `D8724B29C432…` → staged `015C04A22DAC…` (344 → 411 lines). `timerq.diff`: `D07A2DC4878D…`, -6 +73.
  - Script: `bench/agent11/timerq_stage.ps1` writes the stage and runs 17 self-checks. `-Check` reports the live file's state. `-Apply` (only after Agent 10's SAFE and Agent 1's GO) and `-Revert` both stamp the copy time.
- **What it does:** it adds `REXCVAR_DEFINE_BOOL(timer_queue_precise_wait, false, "Runtime", …)` with `kInitOnly`. `TimerWaitStrategy` gets a mode: kSpin (today's default), kBlocking (`REX_TIMER_WAIT_BLOCKING`, as today) or kPrecise (the cvar).
  - kPrecise waits on the condition variable until 20 ms before the deadline. It then sleeps the rest with `rex::thread::SleepPrecise` (a high-resolution waitable timer; `include/rex/thread.h:119`, `src/core/threading_win.cpp:190`), in slices of at most 1 ms with the lock released, and rechecks `ready()` after each slice.
  - Idle waits (no timer queued) stay `cv_.wait` with no timeout, as in kBlocking. Publications and `Stop()` notify as in kBlocking.
- **When the mode is picked:** the queue is a static, constructed before cvars are parsed. So `SelectMode()` runs under `std::call_once` at the start of the first `QueueTimer`, before that call publishes. On Windows that first call is `CreateRepeating` in the XboxkrnlModule constructor. It comes after `cvar::Init` + `ApplyEnvironment` (`windowed_app_main_sdl.cpp:40-41`), `LoadConfig` (`rex_app.cpp:224/277`) and `InitLogging`.
- **Why no wake-up is lost at the switch:** the first publication ever comes from the first `QueueTimer`, after its `call_once`. So every publisher sees kPrecise (call_once synchronizes) and notifies. The consumer notifies only after consuming a publication made after the switch (acquire chain), so it sees kPrecise too. In kSpin nothing ever waits on the condition variable, so no skipped notify can strand a waiter.
- **Cvar off:** every path is the same as today (kSpin, or kBlocking with the env var). With both the env var and the cvar on, precise wins and the log line says so.
- **Caveats:**
  - A publication or `Stop()` during a slice is seen when the slice ends, ≤1 ms later. In the bench this shows only as a longer `QueueTimer` call when 2000 one-shots overflow the 512-slot ring (longest 0.9-1.7 ms, against ≤0.6 ms in the other modes). The game queues one timer, once.
  - Before Windows 10 1803 there's no high-resolution waitable timer. `SleepPrecise` then falls back to `rex::thread::Sleep`: `::Sleep(0)` for slices under 1 ms, so a yield loop, and `::Sleep(1)` (15.6 ms) for a full 1 ms slice. That's as bad as today: 32.7% CPU and 48% stale ("no high-res" row below). A later version could fall back to kBlocking when the high-resolution timer is missing.
  - The first call decides. A `QueueTimer` made before cvars are parsed would leave the cvar ignored. That doesn't happen on Windows. It could on other platforms' paths.

### Tests (no game, ≤2 threads, single-threaded `cl`)

- **Stage:** `timerq_stage.ps1`: 17/17 self-checks. `-Check` exits 0 with the live file still pristine.
- **Syntax:** `bench/agent11/timerq_syntax.ps1`: RESULT PASS, no new diagnostics. The one warning (C4996 on `getenv`) is in both copies. Report: `build/agent11/timerq/stage/syntax-20261122-025049.txt`.
- **Stage bench:** `bench/agent11/timerq_stage_bench.ps1` builds `bench_timerq.exe` against the live and the staged file, with shim headers from `bench/agent11/timerq_shim/rex/`. It runs 7 modes: live spin, live blocking, staged spin and staged blocking (cvar off), staged precise, staged precise + env var, and staged precise with the high-resolution timer forced off (`TIMERQ_NO_HIRES=1`).
  - **Correctness in every mode:**
    - `stress 2000 50`: 2000 one-shots over 50 ms with the 1 ms timer running.
    - `stress 40 2000 0`: 40 one-shots over 2 s with nothing else queued, which exercises the precise stretch.
    - `exit`: return from main with both timers armed; must exit in < 3 s.
    - Each must fire all, none twice, none early, report the right mode, and log the precise line only in precise modes.
  - **Perf:** 10 s game-free `run`s, discarded and retried if a game starts.
  - **First run** (02:54, `stage-bench-20261122-025438.txt`): every correctness check passed in all 7 modes. A game was booting, though, so the numbers are noisy, and the precise perf row was contaminated: a game started mid-run.
  - **Clean rerun** (03:00-03:10:53, `stage-bench-20261122-030019.txt`): **RESULT: PASS**, exit 0. Every correctness check passed in all 7 modes again, game-free (03:01-03:04). The perf rows ran in gaps between Agent 8's games (03:04:37-03:10:52). A game start overlapped 3 runs, which were discarded and retried.

Lateness of the one-shots in the clean rerun, p50 / p99 ms. Every mode fired all, none twice, none early, and exited in 0.35-0.45 s.

| mode | `stress 2000 50` (with the 1 ms timer) | `stress 40 2000 0` (nothing else queued) |
|---|---|---|
| live spin | 0.174 / 7.95 | 4.28 / 17.1 |
| live blocking | 7.23 / 18.1 | 12.19 / 15.2 |
| staged spin (cvar off) | 0.080 / 12.2 | 10.69 / 14.0 |
| staged blocking (cvar off) | 7.58 / 15.1 | 12.19 / 17.3 |
| **staged precise** | **0.340 / 3.19** | **0.681 / 7.57** |
| staged precise + env var | 0.380 / 3.56 | 0.413 / 2.51 |
| staged precise, no high-res | 0.000 / 0.36 | 9.33 / 15.6 |

The 1 ms timer for 10 s, game-free, at the default resolution (`run 10 0`) unless noted:

| mode | timer thread CPU (thread times / cycles) | gap p50 / p90 / p99 / max ms | stale | SleepPrecise/s |
|---|---|---|---|---|
| live spin (today) | 30.4% / 28.3% | 0.308 / 1.43 / 13.4 / 81.5 | 49.7% | - |
| staged, cvar off | 28.4% / 26.6% | 0.259 / 0.75 / 14.3 / 26.8 | 57.5% | 0 |
| **staged precise** | **1.9% / 1.8%** | **1.069 / 1.36 / 3.77 / 11.5** | **5.4%** | 889 |
| live blocking (env var) | 0.3% / 0.5% | 0.001 / 0.004 / 17.2 / 31.7 | 84.5% | - |
| staged precise, no high-res | 32.7% / 31.1% | 0.004 / 1.04 / 13.2 / 17.0 | 48.0% | 986,031 |
| staged precise, at `timeBeginPeriod(1)` | 1.7% / 1.7% | 1.045 / 1.59 / 5.70 / 17.9 | 14.0% | 767 |

- **Cvar off = today:** 28.4% against 30.4% CPU, and 57.5% against 49.7% stale. These are within run-to-run noise: the spin rows ranged 28-31% and 49-60% across the three runs tonight.
- **Precise:** 1.9% CPU (all kernel time), a median gap of 1.07 ms, p99 3.8 ms and 5.4% stale, at the default timer resolution. Both soft checks passed (< 5% CPU, median gap < 1.5 ms), also at `timeBeginPeriod(1)`. That row takes the same path, because the high-resolution timer doesn't depend on the resolution. Its 14% stale and 17.9 ms max are probably scheduling noise from the machine's load at 03:10.

### In-game TimerQueue CPU so far (Agent 8's `threads.csv`, before the pair)

TimerQueue busy % of one core in the driver window, from every `threads.csv` under `build/agent8/matrix/`:

| runs | where | TimerQueue busy | all threads |
|---|---|---|---|
| window 3, OFF builds: d0, base, d11 (4 each), 00:18-01:16 | interactive desktop, timing | 60.4-63.6% | 3.46-3.54 cores |
| window 3, native n0 (4), same window | interactive desktop, timing | 52.0-52.7% | 2.42-2.45 cores |
| verify3b/3c: d0, n0, base, d11, 23:46-00:07 | hidden desktop, functional | 31.4-36.0% | 1.96-2.73 cores |
| S3 functional n1, n3, n2, 02:05-02:12 | hidden desktop, functional | 28.6-33.5% | 1.76-1.98 cores |

- **Reading:** the thread's share grows with the game's total load. That fits the busy-phase model: under load this 15 W part clocks down, so a fixed 4092-pause busy phase takes longer. On the hidden desktop it matches the bench (~30%). In window 3 it's about 18% of the game's whole CPU time (0.62 of 3.5 cores).
- **For the pair:** d0f on the hidden desktop should read ~30-35% (verify3b's d0: 32.9%), not window 3's 62%. d0t's pass rule (≤ ~3%) is absolute, so it still applies.

### The arm for tonight and window 4 (Agent 1, 03:10)

**Agent 1 (03:10):** no build tonight; `timer_queue_precise_wait` stays staged for S4. Choose the arm for tonight's functional pair (d0t or d11t) and tell Agent 8 now. By ~04:05, send the cause report with one recommended window-4 timer arm, including the in-game TimerQueue CPU from the pair's `threads.csv` against d0.

**Choice: d0t for both.** I told Agent 8 at ~03:20 to keep the queued d0f → d0t pair unchanged.
1. Window 4's reference is d0 (devoff2). d0t is the same bin plus one env var, so window 4 would measure the TimerQueue change alone. d11 isn't in window 4, so d11t would have no like-for-like reference there.
2. d0t is already in `matrix-window4.json` as the optional arm. `-Only d0,B,d3,d0t -Repeats 4` is 19 runs, about 44 min by Agent 8's `-PlanOnly` at 02:55. Tonight's pair already compares it with d0f.
3. **Its cost:** at the default resolution (`host_timer_resolution_ms` defaults to 0), blocking moves TickCount in ~16 ms steps (bench: 84.5% stale, against 49.7% today). Today's spin already leaves TickCount more than 2 ms behind half the time, through its 15.6 ms oversleeps, so the guest already lives with a bursty TickCount. Window 4 is where a timing effect would show.
4. d11t (blocking at 1 ms) is the better configuration in the bench, but it differs from d0 in 9 settings. The S4 cvar keeps ticks fresh with no resolution change at all.

### The pair (d0f/d0t, 03:30-03:34; Agent 8's `build/agent8/matrix/20261122-0330`)

The runs are on the hidden desktop and functional only: devoff2 with `framerate_limit=0`, and the window is 60-110 s after the first frame. `timerq_pair.ps1` output is in `build/agent11/timerq/pair-20261122-034639.txt`:

| run | TimerQueue busy (max over 1 s) | process cores | fps | >33 ms | >100 ms | window eff MHz P / E | utility % P / E |
|---|---|---|---|---|---|---|---|
| d0f `0330-d0f-r1` | 39.1% (52.0) | 2.40 | 145.2 | 163 | 1 | 1690 / 1309 | 98.8 / 78.2 |
| d0t `0332-d0t-r1` (+ `REX_TIMER_WAIT_BLOCKING=1`) | 0.4% (2.9) | 2.06 | 90.9 | 298 | 2 | 1944 / 738 | 112.4 / 44.3 |

- **TimerQueue:** 39.1% → 0.4% of a core, which frees 0.39 cores. For comparison, window 3's d0 had 62.0% on the interactive desktop.
- **Checks:** TimerQueue, close, dump and env pass. Two checks fail:
  - >100 ms frames: 2 against 1, a one-frame difference;
  - fps: −37.4% against the 10% limit. I added this check at 03:45, after seeing this run.

Per 10 s from the first frame (the window is 60-110 s):

| s | 0 | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100 | 110 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0f fps | 254 | 310 | 279 | 222 | 176 | 146 | 145 | 183 | 194 | 154 | 57 | 43 |
| d0f E MHz | 1792 | 1960 | 1701 | 1933 | 1510 | 1493 | 1494 | 1492 | 1484 | 1430 | 646 | 763 |
| d0t fps | 216 | 281 | 197 | 163 | 67 | 62 | 53 | 56 | 101 | 139 | 106 | 73 |
| d0t E MHz | 1595 | 1480 | 1478 | 1148 | 549 | 553 | 552 | 554 | 792 | 951 | 839 | 597 |

- **fps follows the E-core clock in both runs.** I call the low phase the "slow state":
  - E cores at 550-760 MHz with 33-46% utility, 43-67 fps, and ~25-28 interrupt dispatches per frame.
  - It occurs in **both** arms: d0t at 40-80 s, and d0f at 100-120 s.
  - The scene is the same throughout: 218 → 226 draw calls per frame from 40 s in both, and no pipeline or texture cache misses.
  - So each window mean mostly measures how much slow state fell inside it: about 2.5 of d0t's 5 buckets, and 1 of d0f's.
- **The same signature without any timer change:** Agent 8's d3-r1 (03:41, devoff3) ran at E 828 MHz with 49.5% E utility and 61.4 fps.
- **Likely cause (a hypothesis; there is no EcoQoS readout):** Windows' background power management. On the hidden desktop the game is never in the foreground, and the power overlay is `best_efficiency`. Window 4 runs in the foreground.
- **Thread shift:** F80001A8 went 46 → 75% busy and Main XThread 49 → 30%. That fits the slow state: the same work done at ~550 MHz.
- **Open: does the missing spinner make the slow state likelier or earlier?** d0t's E cores were already slower in its first 40 s (1148-1595 MHz against 1701-1960). There are two candidate explanations:
  - (a) TickCount staleness. Blocking at the default resolution moves TickCount in ~16 ms steps (bench: 84.5% of samples more than 2 ms stale). However, d0t's 40-80 s frame times show no peaks at multiples of 15.6 ms (long frames are spread over 20-70 ms), which weakens the simple form of (a).
  - (b) The spinner's own E-core load kept the E cluster's clock up.
- **Next:** Agent 1 asked Agent 8 for d0t, d11t and d0f at ~03:53. d0t runs first to test the order effect.
  - d11t is d11's cvars (including `host_timer_resolution_ms=1` and `host_timer_throttling_optout=true`) plus the env var. That is blocking with fresh ticks (bench: 1.4% CPU, 4.7% stale).
  - Agent 1's rule: W4b needs d11t's fps within noise of d0f and the TimerQueue drop confirmed; otherwise window 4 is W4a, and the timer work goes to S4. The report is due by ~04:15.

### The re-check set (d0t, d11t, d0f; 03:49-03:57; Agent 8's `build/agent8/matrix/20261122-0349`)

Agent 1 (03:39) asked Agent 8 for d0t, d11t and d0f, in that order. Same conditions as the pair: hidden desktop, functional only, devoff2 with `framerate_limit=0`, window 60-110 s after the first frame. `timerq_pair.ps1` log with d0f as the reference: `build/agent11/timerq/pair-20261122-035818.txt`.

| run | TimerQueue busy (max over 1 s) | window cores | window fps | >33 ms | >100 ms | window E MHz | slow-state samples (onset) |
|---|---|---|---|---|---|---|---|
| d0f `0354-d0f-r1` | 44.1% (61.3) | 2.23 | 52.2 | 588 | 8 | 594 | 48% (61 s) |
| d11t `0352-d11t-r1` (d11 cvars + env) | 0.3% (1.7) | 1.77 | 62.0 | 573 | 2 | 785 | 34% (42 s) |
| d0t `0349-d0t-r1` (+ env) | 0.5% (2.6) | 2.00 | 78.0 | 403 | 12 | 699 | 47% (69 s) |

- **Checks against d0f:** d11t passes all six (TimerQueue, >100 ms, fps +18.8%, close, dump, env). d0t fails only >100 ms (12 against 8).
- **d11t's game.log** has "Host timer resolution set to 1 ms (background opt-out on)". Otherwise it matches d0f's: 91 against 90 lines, 40 warnings and 0 errors each, and only the Toypad crypto bytes differ.
- **Agent 8's report (~04:00)** gives the same numbers. Share of 1 s bins in the 53-67 fps band: d0t 32%, d11t 20%, d0f 24%. Its conclusion: "fps can't be compared on the hidden desktop" (d0f went from 145 fps at 03:30 to 52 fps at 03:54). Details are in `perf-notes/agent8-window3.md` → "Timer arm checks".

Per 10 s from the first frame (the window is 60-110 s):

| s | 0 | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100 | 110 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0f fps | 230 | 214 | 200 | 162 | 201 | 167 | 46 | 42 | 68 | 50 | 54 | 49 |
| d0f E MHz | 1632 | 1722 | 1488 | 1488 | 1475 | 1438 | 555 | 554 | 601 | 639 | 622 | 692 |
| d11t fps | 238 | 256 | 258 | 163 | 67 | 57 | 60 | 36 | 78 | 74 | 64 | 41 |
| d11t E MHz | 1492 | 1502 | 1490 | 1511 | 665 | 551 | 553 | 550 | 871 | 965 | 986 | 1449 |
| d0t fps | 262 | 253 | 231 | 154 | 117 | 186 | 161 | 79 | 62 | 54 | 38 | 45 |
| d0t E MHz | 1749 | 1502 | 1489 | 1505 | 1499 | 1499 | 1274 | 552 | 555 | 557 | 557 | 555 |

- **All three hit the slow state, d0f included.** So the window means measure how much slow state fell inside each window, not the timer.
- **Matched fast-state buckets** (both runs at E 1440-1750 MHz, in the same seconds after the first frame):
  - d11t against d0f, 0-30 s: 915 against 806 (sum of the four bucket fps), +13.5%.
  - d0t against d0f, 0-50 s: 1203 against 1174, +2.5%.
  - Agent 8's 0342 rehearsal (quick mode, 20 s windows): d0t-r1 (03:47) passed every check against d0-r1 (03:43), at 166.3 against 172.1 fps (−3.4%), with TimerQueue 0.4% against 31.0% (`build/agent11/timerq/pair-20261122-035026.txt`). d0t-r1 had no slow state, and d0-r1 had 27% of its samples in it.
- **In-game TimerQueue CPU, every run tonight (hidden desktop):** blocking 0.3-0.5% of a core in all 4 runs (0332 d0t 0.4, 0347 d0t 0.4, 0349 d0t 0.5, 0352 d11t 0.3); spin 31.0-44.1% (0343 d0 31.0, 0330 d0f 39.1, 0354 d0f 44.1). Window 3's d0 on the interactive desktop: 62.0%.
- **Not the 15.6 ms tick:** d11t, with 1 ms ticks, hit the same slow state, and so did d0f with the spinner. d0t's frame times show no peaks at multiples of 15.6 ms.

### The slow state (every run with `sys.csv`, 03:30-03:57)

`bench/agent11/timerq_slowstate.ps1` (read-only, pure ASCII, 0 parse errors) flags 3+ `sys.csv` samples in a row with the E cores below 800 MHz:

| arms | runs | with the slow state | onset after the first frame | share of samples after the first frame |
|---|---|---|---|---|
| spin (d0f, d0, B, d3, cold) | 12 | 9 | 27-100 s | 14-50% |
| blocking (d0t, d11t) | 4 | 3 | 37-69 s | 34-50% |

- The runs without it are short: the three spin runs are ~31 s cold runs (cold-d3 has it at 27 s), and the blocking one is the 45 s 0347 d0t-r1. **So the blocking timer doesn't cause it; it hits every arm.**
- **Signature:**
  - An abrupt step. In 0349 d0t it came at 03:50:50.9 (67.8 s after the first frame): E 1506 → 550 MHz within two samples, and system utility 97 → 60%.
  - The E cores stay busy at their minimum clock (E utility ≈ 33%), while the P cores stay at ~1800-1950 MHz and fully busy.
  - The scene doesn't change (226 draws per frame). Agent 8 sees F80001A8 at 75-80% busy.
  - Every sample has `fg_game=0` (never in the foreground). AC power, Balanced scheme with the `best_efficiency` overlay; there is no thermal readout.
- **Consequence:** fps verdicts from tonight's hidden-desktop runs are unreliable. That includes Agent 8's 0336/0342 B and d3 "SLOWER" verdicts: the slow state covers 0339-d0 34%, 0340-B 27%, 0341-d3 42%, 0343-d0 27%, 0344-B 50% and 0346-d3 25% of their samples.
- **Hypothesis (unproven):** Windows' power management of a background process (a lower QoS, with an efficiency-biased EPP), arbitrated under the 15 W package limit so that the E cluster drops to its minimum first. `host_timer_throttling_optout` sets only IGNORE_TIMER_RESOLUTION (`src/core/threading_win.cpp:136-157`), not EXECUTION_SPEED, and d11t, which has it on, still hit the slow state at 42 s.
- **Possible follow-up (not tonight; needs Agent 1's OK):** an OFF cvar that opts the process out of execution-speed throttling (`SetProcessInformation(ProcessPowerThrottling)` with ControlMask = EXECUTION_SPEED and StateMask = 0), tested with a hidden-desktop pair. Window 4 runs in the foreground, where window 3's d0 was steady (161.5-167.3 fps).

### Recommendation for window 4 (cause report to Agent 1, ~04:05)

**W4b with d11t.** Agent 1's rule (03:39): W4b needs d11t's fps within noise of d0f and the TimerQueue drop confirmed; otherwise W4a, and the timer work goes to S4.
1. **TimerQueue drop: confirmed.** 0.3% (max 1.7) against d0f's 44.1% (max 61.3) in the same set, and 0.3-0.5% in all 4 blocking runs. Window cores 2.23 → 1.77.
2. **fps: d11t is not slower by any measure tonight.** Its window fps is +18.8%, the matched fast-state buckets are +13.5%, and it had 2 frames over 100 ms against 8. The noise (the slow state) is large, so this shows no regression, not a gain. Window 4 is where the fps gets measured properly.
3. **Functional:** exit 0, no dump, a clean WM_CLOSE, and the same game.log as d0f plus the 1 ms line.
4. **Why d11t rather than d0t:** ticks stay fresh (bench: 4.7% of samples more than 2 ms stale, against d0t's 84.5%). Its cost is that 9 settings differ from d0, so window 4 measures "d11 + blocking". Window 3's d11 (157.5-160.3 fps, against d0's 161.5-167.3) is the cross-window reference for the cvars alone.
- **Fallback,** if Agent 1 judges hidden-desktop fps unusable for the rule: W4a, with the timer work in S4 (`timer_queue_precise_wait`, staged; rating pending).
- **For window 4:** keep Agent 8's sys sampler on, and run `timerq_slowstate.ps1 -Since <window 4 matrix>` before reading any fps.

### Status

- **Staged only**; the live `timer_queue.cpp` is pristine. It's an S4 candidate (Agent 1, 02:55), and applying it needs Agent 10's rating and Agent 1's GO.
- **Tonight:** no build (Agent 1 agreed at 03:10). Window-4 recommendation: W4b with d11t (see above). The cvar is the better long-term fix, because it keeps TickCount fresh without a 1 ms timer resolution.
- **Slow-state scan:** `bench/agent11/timerq_slowstate.ps1` (see "The slow state"). Run at 03:58 over 16 runs, 03:30-03:57.
- **Rating request:** sent to Agent 10 at ~03:08 (text only, low priority).
- **Pair summarizer:** `bench/agent11/timerq_pair.ps1 -RunDirs <d0f>,<d0t>` is read-only and applies d0t's pass rule. It reads `threads.csv`, `summary.txt`, `run.json` and any `*.dmp`, and its log goes to `build/agent11/timerq/pair-<time>.txt`. Self-test at 03:18: it parses with 0 errors and is pure ASCII. On two d0 runs (window 3 `0106-d0-r4` as the reference, verify3b `2344-d0-r1` as the test arm) it printed the table and failed only the TimerQueue check (32.9% > 3%) and the env check, exit 1, with `a,b`, `"a, b"` and split arguments alike. With `-MaxTimerQueuePct 99`, only the env check failed. No arguments (no pair yet), one dir or a missing dir gave exit 2.
- **Window 4:** Agent 1 (~04:07) made W4b with d11t final. The cause report and `@@done 10` went to Agent 1 at ~04:05, and Agent 1 marked task #10 done.
- **Pending:** Agent 10's rating (requested at ~03:08).

## S4 staging (task #19, Agent 1, 04:07)

Agent 1 (04:07) asked for S4 staging on scratch copies only: no live-tree edits, no builds, no game runs, ≤2 threads, no subagents, and only notes from 08:30. There are three parts:
1. An OFF cvar for the execution-speed opt-out, staged like timerq and sent to Agent 10 for a rating.
2. A proposal for Agent 8's runner to apply the same opt-out to the game it launches.
3. A user-facing summary of the timer finding.

The summary to Agent 1 is due by ~06:30.

### 1. `host_execution_throttling_optout` (staged, OFF)

**What it does.** With the cvar on, `ConfigureHostTiming` opts the process out of `PROCESS_POWER_THROTTLING_EXECUTION_SPEED` (EcoQoS). It runs once, from `Runtime::Setup`, and makes the call `SetProcessInformation(GetCurrentProcess(), ProcessPowerThrottling, {Version 1, ControlMask 0x1, StateMask 0})`. Off is the default: no new call and no new log line, i.e. today's behavior.

The staged copies are in `build/agent11/pthrottle/stage/` (diff `pthrottle.diff`, −4/+37, 7 hunks, sha256 `75756E8DCB04…`):

| file (`DimensionsRecomp/rexglue-sdk/`) | pristine | staged | change |
|---|---|---|---|
| `include/rex/threading_timing.h` | `043FFE289935` | `72EAB2800912` | +4: field `keep_execution_speed_in_background = false` |
| `src/core/threading_win.cpp` | `C0EBD864B9D2` | `8A7F7E24289A` | +27/−4 (see below) |
| `src/system/runtime.cpp` | `306B692BC091` | `27F4BC105FD3` | +6 (see below) |

- **runtime.cpp:**
  - Defines the cvar: `REXCVAR_DEFINE_BOOL(host_execution_throttling_optout, false, "Runtime", …)`.
  - `Runtime::Setup` passes it into `HostTimingConfig`.
  - The cvar keeps the default lifecycle, like its sibling `host_timer_throttling_optout`.
- **threading_win.cpp:**
  - `KeepTimerResolutionInBackground()` becomes `OptOutOfPowerThrottling(ULONG control_mask)`, and StateMask is always 0.
  - New constant `kPowerThrottlingExecutionSpeed = 0x1`.
  - `ConfigureHostTiming` changes as below.
- **Timer opt-out on (`host_timer_throttling_optout`), new cvar off:** the same single call as today, ControlMask 0x4.
- **Both on: ONE call, ControlMask 0x5.** Each Set replaces the whole state (probe at 04:11; test f; runner probe step 6), so with two calls only the second would survive.
- **New cvar only:** one call, ControlMask 0x1.
- **New cvar on, and the combined call failed:** retry 0x1 alone. Windows 10 has EXECUTION_SPEED but rejects IGNORE_TIMER_RESOLUTION (a Windows 11 flag) with error 87. Today's code already expects that failure (its debug line).
- **Log:**
  - New: `info "Execution speed power throttling opt-out on"` or `warn "Execution speed power throttling opt-out failed (0x…)"`.
  - Unchanged: "Host timer resolution set to {} ms (background opt-out {})", which still reports only the timer opt-out, and the timer debug line.

**Tests (scratch copies only; the live files stayed pristine):**
- **Stage, `bench/agent11/pthrottle_stage.ps1` (04:25): PASS, 35/35 self-checks.**
  - Per file (×3): BOM and newline style kept, no CR, live file untouched.
  - 5 diff checks: −4/+37, 7 hunks (within 4-8), 3 files, ≤100 columns, ASCII.
  - 3 line deltas.
  - 18 content checks: the cvar is defined once with default false and read once; the field defaults to false; the old function is gone, and the new one has a definition and 2 calls; StateMask is only ever 0; there is one `SetProcessInformation` call site, on the own process; the field is read 3 times, all in `ConfigureHostTiming`; the "Host timer resolution set to" line and the timer debug line are unchanged; the new info and warn lines are present.
- **Syntax, `bench/agent11/pthrottle_syntax.ps1` (04:37): PASS.** It runs clang `-fsyntax-only` with the dev-SDK flags.
  - `threading_win.cpp`: the same 3 pre-existing warnings in both copies (no `override` on `SetRepeatingAt`; unused `timer_low`/`timer_high`).
  - `runtime.cpp`: no diagnostics in either copy.
  - The control compile (the staged `threading_win.cpp` with the pristine header) fails as it should: "no member named 'keep_execution_speed_in_background'".
  - Report: `build/agent11/pthrottle/stage/syntax-20261122-043717.txt`.
- **Read-back test, `bench/agent11/pthrottle_test.ps1` + `pthrottle_test.cpp` (04:36): PASS, 129 checks, 0 failed, 33 child processes (Windows build 26300).**
  - It extracts `HostTimingConfig` and the two code blocks of `threading_win.cpp` verbatim from both copies, with `#line` so errors point at the copies, and compiles them side by side with `cl /W4` (0 warnings).
  - Each scenario runs in a fresh child: `ConfigureHostTiming`, then `GetProcessInformation` inside the child and through the parent's handle, then `RestoreHostTiming`.
  - A hook records the calls and log lines, which are compared with pristine.
  - Report: `build/agent11/pthrottle/test-20261122-043649.txt`.

| scenario | config | staged | against pristine |
|---|---|---|---|
| a, a1 | both off (period 0 / 1 ms) | no call; C=0x0 S=0x0 | identical |
| a2 | both off; EcoQoS preset at launch (C=0x1 S=0x1) | left untouched | identical |
| b, b1 | timer opt-out only | one call, C=0x4 | identical |
| c, c1 | new cvar only | one call, C=0x1; "opt-out on" | pristine's log lines unchanged, in order |
| d, e | both on | ONE call, C=0x5; "opt-out on" | the same |
| i0 | timer only, simulated Windows 10 | 0x4 fails (87); debug line | identical |
| i | both on, simulated Windows 10 | 0x5 fails (87), debug line; 0x1 retry ok; final C=0x1 | the same |
| j, j1 | no `SetProcessInformation` export (simulated) | warn "failed (0x0000007F)" | the same |
| h | C=0x1 set at launch, then the game's timer opt-out | replaced by C=0x4 | identical |
| f | a plain Set of 0x1 after the game's 0x4 | C=0x1: replaced, not merged | n/a |
| g, g2, g3 | the runner's read-modify-write | C 0x4→0x5; 0x0→0x1; C=0x1 S=0x1 → S=0x0 | n/a |
| k | handle rights | QUERY_LIMITED only: Get ok, Set error 5. SET_INFORMATION only: Set ok, Get error 5 | n/a |

- **Live tree (04:37):** `pthrottle_stage.ps1 -Check` exit 0 (all 3 files pristine); `timerq_stage.ps1 -Check` exit 0.
- **Other users of the API:** a read-only `git grep` finds `ProcessPowerThrottling`/`SetProcessInformation` only in the SDK's `src/core/threading_win.cpp`, and nothing in the game repo.
- **Limit:** the read-back shows that the policy is set, not what the scheduler does with it. Whether it ends the slow state needs a hidden-desktop pair (part 2). Window 4 runs in the foreground, so it won't show this. The docs describe this opt-out as HighQoS, but the effect here is unverified.
- **Rating:** requested from Agent 10 at ~04:50. It's an S4 candidate, not tonight; `-Apply` comes only after SAFE and Agent 1's GO.

### 2. Proposal for the next session: the runner applies the opt-out (no game rebuild)

Agent 8's runner could apply the same opt-out to the game process it launched, using the documented API on its own child handle. It needs no rebuild, works with any bin (devoff2, devoff3, native) and leaves the game unchanged. This is a proposal only: nothing in `bench/agent8` was edited.

- **Where:**
  - `bench/agent8/run/run-timing.ps1` already holds a full-access handle: L222 `$p = Start-Process … -PassThru` and L226 `$null = $p.Handle`.
  - Apply right after the first-frame signal (L292), not at launch. With `host_timer_throttling_optout=true` (the d11 arms), the game's own call in `Runtime::Setup` replaces anything set before it (test h).
  - After `Runtime::Setup` the game makes no further call: there's no other call site, and `RestoreHostTiming` makes none.
  - The slow state starts 27-100 s after the first frame, so applying it at the first frame is early enough.
- **How:** read-modify-write, because each Set replaces the whole state.
  1. Get.
  2. ControlMask |= 0x1; StateMask &= ~0x1.
  3. Set.
  4. Get again to verify.

  This keeps the game's 0x4 (C=0x4 → 0x5) and also clears an EcoQoS opt-in (C=0x1 S=0x1 → S=0x0).
- **Rights:**
  - `$p.Handle` has full access.
  - A narrower `OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION)` handle also works. Get needs QUERY_LIMITED, and Set needs SET_INFORMATION (test k; probe step 4).
  - Same user, so no elevation is needed.
- **Helper:**
  - The C# class in `bench/agent11/pthrottle_runner_probe.ps1` (`PowerThrottle.Read/Write/OptOutExecutionSpeed/Str`) is C# 5 and compiles with Windows PowerShell 5.1's `Add-Type`.
  - It could go into `winhelper.cs`, which `common.ps1` L16 loads with `Add-Type`. There are no name clashes (no `PowerThrottl`/`SetProcessInformation` in `bench/agent8/run`).
- **Probe (04:42): PASS 6/6** on a hidden PING.EXE child started the same way as the game:

  | step | result |
  |---|---|
  | start | C=0x0 S=0x0 |
  | the game's C=0x4 | reads back |
  | opt-out via `$p.Handle` | C=0x4 → 0x5 |
  | the same via the narrow handle | unchanged (idempotent) |
  | an EcoQoS opt-in | C=0x1 S=0x1 → S=0x0 |
  | a plain Set of 0x1 on 0x4 | leaves C=0x1 |

  Report: `build/agent11/pthrottle/runner-probe-20261122-044234.txt`.
- **Switch and record:**
  - Off by default, and set per arm (an arm field or a runner switch), so one matrix can hold both arms.
  - run.json gets `power_throttling: {applied_at_s, before, after, at_close, ok, error}`, where `at_close` is a second read just before WM_CLOSE to confirm the state held through the window. summary.txt gets one line. Then `timerq_slowstate.ps1` and `timerq_pair.ps1` can tell the arms apart.
  - If the read-back doesn't show the opt-out, log it and carry on: a functional run shouldn't fail over it.
- **Test plan:**
  - Hidden desktop; d0 against d0 with the opt-out.
  - 3 pairs in alternating order (ABBAAB), each lasting to 110+ s after the first frame, with sys.csv on.
  - Then run `timerq_slowstate.ps1 -Since <matrix>`.
  - Reading the result: tonight 12 of 16 runs hit the slow state. If the opt-out runs stay out of it while the plain ones fall in, the opt-out works, and both the runner switch and the cvar are worth applying. If they still fall in, the cause is elsewhere (see the risks), and both are dropped.
- **Risks and limits:**
  - The slow state may not be EcoQoS. The 15 W package limit (PL1), or the lower QoS that Windows gives a process with no visible window, could be the cause, and this flag may not override either. The read-back proves only the policy.
  - Under the same 15 W limit, more power for the E cores may come out of the P cores' budget, so fps may not rise even if the slow state ends.
  - fps from runs with and without the switch aren't comparable; label the arms.
  - Window 4 runs in the foreground, where window 3's d0 was steady (161.5-167.3 fps), so it doesn't need the switch. The switch is for hidden-desktop functional runs.
  - Windows also has a per-executable setting (`powercfg /powerthrottling`). It is persistent and machine-wide, so it isn't proposed.
- **Runner switch or cvar:** the switch is a test tool for Agent 8's runs; the cvar is the shipped form, for players who leave the game in the background. A positive pair supports rating and applying both.

### 3. Morning summary: the TimerQueue finding (user-facing)

**In short:**
- The `rex::thread::TimerQueue` thread used half a core or more (62% in window 3) just to keep the game's millisecond tick count running, mostly by busy-waiting.
- Switching it to blocking waits (`REX_TIMER_WAIT_BLOCKING=1`) cuts that to under 1% of a core in game. Combined with a 1 ms timer resolution (`host_timer_resolution_ms=1`), the tick count also stays fresh.
- Window 4's d11t arm tests exactly that, together with d11's other settings.
- A cleaner fix, `timer_queue_precise_wait` (off by default), is staged for the next session.

**Cause.**
- On Windows, the TimerQueue's only user is a 1 ms repeating timer (`xboxkrnl_module.cpp:195`) that updates the tick count in the guest's KeTimeStampBundle.
- Before each tick, the queue's wait loop spins:
  1. 4092 `_mm_pause` instructions (~395 µs on a P core, ~236 µs on an E core), even when the deadline has already passed;
  2. then 19 `SwitchToThread` calls;
  3. then `sleep_for(1 ms)`.
- At Windows' default timer resolution that sleep takes ~15.4 ms. The ticks it missed then fire back to back, each with its own spin, which adds up to about 1000 busy phases a second.

**Bench (no game; one 1 ms timer):**

| mode | timer thread CPU | samples with the tick count >2 ms stale |
|---|---|---|
| spin (today's default) | 30.4% | 49.7% |
| blocking (`REX_TIMER_WAIT_BLOCKING=1`) | 0.3% | 84.5% (16 ms steps) |
| blocking + 1 ms timer resolution (as in d11t) | 1.4% | 4.7% |
| staged `timer_queue_precise_wait` | 1.9% | 5.4% |
| precise, without the high-resolution timer | 32.7% | 48% |

**In game (the TimerQueue thread, % of one core):**

| arm | runs | TimerQueue CPU |
|---|---|---|
| spin, hidden desktop (tonight) | 3 | 31.0-44.1% |
| spin, window 3 d0 (interactive desktop) | 1 | 62% |
| spin, native | 1 | 52% |
| blocking (tonight) | 4 | 0.3-0.5% |

In the 03:49 set, the whole process went from 2.23 cores (d0f) to 1.77 (d11t) over the 60-110 s window.

**Why tonight's runs can't settle the fps question:**
- 12 of 16 hidden-desktop runs fell into a "slow state" 27-100 s after the first frame, in every arm.
- In it, the E cores drop to ~550 MHz, and fps falls to roughly 35-70 (from 150-260 before).
- The likely cause is Windows' power management of a background process (unproven). Part 1 stages a test for that.

**What window 4's d11t arm will tell us:**
- Foreground fps and frame times for d11's settings plus the blocking timer at 1 ms resolution, against d0.
- Whether freeing the 0.3-0.6 of a core that the spinning used helps.
- Stability: clean exit, no dumps.

**What it won't tell us:**
- The timer's effect on its own. d11 changes 9 settings; window 3's d11 (157.5-160.3 fps against d0's 161.5-167.3) is only a cross-window reference.
- Anything about `timer_queue_precise_wait`, which is staged and not built.
- Anything about the slow state, because window 4 runs in the foreground.
- Differences smaller than the run-to-run noise.

**Next session (S4):**
- Rate and apply `timer_queue_precise_wait`: fresh ticks at 1.9% CPU, without a 1 ms system timer resolution.
- Rate and apply `host_execution_throttling_optout`.
- Both are off by default.
- Decide on the runner switch (part 2).

### Status (task #19)

- **Done at ~04:50.** All three parts are written. Nothing live was edited, built or run; my only child processes were the test's 33 children and the probe's PING.EXE.
- **Pending:**
  - Agent 10's rating of `host_execution_throttling_optout` (requested ~04:50);
  - Agent 10's rating of `timer_queue_precise_wait` (requested ~03:08).

  Applying either needs SAFE and Agent 1's GO (S4).

## Task #24: execution-speed opt-out pairs (Agent 1, 04:54)

**The task.**
- Turn #19 part 2 (the runner-side opt-out) into a standalone wrapper in `bench/agent11/`.
- Edit nothing in `bench/agent8/**`, `harness/**` or any file window 4b uses.
- Hash `RUN-WINDOW4B.cmd` and everything it calls, before and after the runs. The hashes must match.
- Spec 3 alternating devoff2 d0 pairs (opt-out on/off) to Agent 8. They go after the shader dump run, only if they end by 07:15, and Agent 8 decides.
- Read the result: summary to Agent 1 by 07:30, then `@@done 24`.

**Design (05:00-05:31).**
- **No runner copy.** Agent 8's `run-matrix.ps1` runs unchanged, with a generated matrix and an out dir under `build/agent11/pthrottle/pairs/<stamp>`.
  - run-matrix appends `-2` to an out dir that already exists. So the wrapper passes a new one and keeps its own files in `<stamp>-meta`.
- **Arms.** `d0` and `d0e` are identical: devoff2, `framerate_limit=0`, perf frames, the thread-cpu driver.
  - `roundrobin` with 3 repeats gives d0 d0e | d0e d0 | d0 d0e. `-NoCold`, sys.csv on.
  - Settle 5 s, then 55 s of warm-up from the first frame, then a 90 s window. So each run covers 0-150 s after the first frame; tonight's onsets were 27-100 s.
- **The opt-out comes from a sidecar, not the runner.** run-timing's `-Driver` only starts at the window, ≥60 s after the first frame, which is too late.
  - The sidecar (`pthrottle_sidecar.ps1`) polls every 0.5 s. It checks each `legodimensions` process's image path (`QueryFullProcessImageName`) and creation time through a query-limited handle that it closes straight away.
  - Only processes under the pairs' own `runs\` dir get a SET_INFORMATION | QUERY_LIMITED | SYNCHRONIZE handle. On d0e it does a read-modify-write: EXECUTION_SPEED controlled and off, other bits kept. On d0 it only reads.
  - It re-reads every poll. On d0e it re-applies if the game's own startup call replaces the state, which covers Agent 10's "after Runtime::Setup" caveat.
  - Each run gets a JSON record, merged into run.json as `"power_throttling"` (BOM kept, then re-parsed).
- **Window-4b hash (`pthrottle_w4b_hash.ps1`): 53 files.**
  - `RUN-WINDOW4B.cmd`.
  - In `bench/agent8/run/`: run-matrix, run-timing, common, timing-env, first-boot, `winhelper.cs`, `frame_summary.py`, `sys_summary.py`, `matrix_recheck.py`, `matrix-window4.json`, and in `drivers/`: sys-csv, `LdSys.cs`, thread-cpu.
  - In `harness/`: `nvml.cs`, `winhelper.cs`, `legodimensions.toml`.
  - `analyze_profile.py`, the 10 dlls in `build/agent8/cache`, and the 3 bins (8 files each).
  - Game data is not hashed.

**Tests (no game).**
- **Static.** All 5 scripts are pure ASCII with LF line endings and 0 parse errors.
- **`-PlanOnly` through Agent 8's run-matrix** (05:23 and 05:32): exit 0. The matrix is valid, the order is d0 d0e | d0e d0 | d0 d0e, and the estimate is "6 runs, about 18 min".
- **`-DryRun` at 05:24: FAIL.** It found 2 bugs:
  1. `Process.Path` was empty for a process caught 0.1 s after it started. That process was ignored for good, so d0e-r3 was missed. Fixed with `Probe` (`QueryFullProcessImageName` plus creation time), which retries while the path is empty.
  2. The read-out's helper `R` is PowerShell's alias for `Invoke-History`, and aliases win over functions. Renamed to `Rnd`.
  - The hashes were equal.
- **`-DryRun` at 05:28: PASS** (exit 0, 97 s).
  - d0e: the sidecar took C=0x0 to C=0x1. After the game-like Set to C=0x4 it re-applied, giving C=0x5 (3/3).
  - d0: read only, ending at C=0x4 (3/3).
  - One process seen 0.06 s after it started was handled correctly.
  - The stand-in started outside the runs dir stayed at C=0x0 and was ignored.
  - 6/6 runs merged, BOM kept.
  - The read-out matches `timerq_slowstate.ps1`. On the synthetic data, d0 reached the slow state in 2/3 runs (at 40 and 80 s) and d0e in 0/3, so the verdict is OPT-OUT HELPS.
  - The closure hashes are equal (53/53), and equal to the 05:16 baseline (53/53).
- **Cost.** Each hash takes about 6 s with `SHA256CryptoServiceProvider`. The first baseline, at 05:16 with `Get-FileHash`, took 70 s of one thread.
- **Dry and plan runs** go to `build/agent11/pthrottle/pairs-dry/`. `pairs/` is for real runs only.

**Reading the result.**
- **d0e 0/3 slow and d0 ≥2/3 slow.** The opt-out keeps the E cores out of the ~550 MHz state. The state then follows the process QoS decision (window-visibility Low QoS or EcoQoS; explicit non-EcoQoS tagging gives High QoS), not a hard PL1 cap alone.
  - It does not show an fps gain, because these are hidden-desktop functional runs.
  - PL1 may still bind once the E cores clock up.
- **Both arms slow at similar rates.** Process-level EXECUTION_SPEED throttling is not the cause. What's left: PL1 / package power (sys.csv has no package-power column, so it can't be measured), thread-level or visibility QoS that the process flag doesn't override, and the power-mode overlay / EPP. In that case Agent 10 says to drop the cvar and the runner switch.
- **d0 never slow.** Inconclusive.

**Status (task #24).**
- The wrapper is ready and spec'd to Agent 8 (see the RESUME block). Agent 8 (05:38) slotted it for ~06:11-06:31 at full length; its own `-PlanOnly` exited 0. The result is pending.
- Agent 10 (05:24) rated both `host_execution_throttling_optout` and `timer_queue_precise_wait` SAFE as default-off candidates. Applying either needs Agent 1's GO.
- 05:58, read-out hardened before the real run. `pthrottle_readout.ps1` now counts a run only with a verified arm state (on arm: opt-out applied and sidecar record ok; off arm: never applied) and with sys.csv data: either the slow state was seen, or there are at least `-MinSpanS` (100) s after the first frame. Before, a run without data counted as "not slow". Each excluded run is listed as "not counted: <run>: <reason>". Tests:
  - Agent 8's real 0330 d0f/d0t pair (as off/on, no records): real sys.csv parses, d0f onset 100 s / 14 %, d0t onset 37 s / 50 %; the on arm is not counted, so the verdict is INCOMPLETE.
  - The 05:28 dry run: OPT-OUT HELPS, unchanged, with `-MinSpanS 0` too.
  - The `-MinSpanS 200` span gate: the 3 d0e runs and d0-r3 (no slow state, 150 s spans) are not counted, so the verdict is INCOMPLETE, as intended.
- Agent 1, 05:55: Agent 8's attract scenes run 06:33-07:15 and need an idle machine. In that window: no builds or compiles, no recursive searches, no reads over ~100 MB, batched tool calls, 1 thread. The pairs wrapper (Agent 8's slot, ~06:11-06:31) does its sidecar compile at the start and its 658 MB hash at the end, before it exits. When the stamp arrives, read `report.txt` with targeted reads only.

**Result (task #24), read 06:22-06:27.** Agent 8 ran `pthrottle_pairs.ps1` at full length: stamp `20261122-0600`, 06:00:46-06:19:09, exit 1 (bad 3). The window-4b closure was 53/53 equal before and after. Report: `build/agent11/pthrottle/pairs/20261122-0600-meta/report.txt`; corrected read-out: `readout-v2.txt` next to it.

| run | onset after first frame (s) | slow share | E MHz in slow rows | E MHz median | P MHz median |
|---|---|---|---|---|---|
| d0 r1 / r2 / r3 | 103 / 71 / 37 | 24 / 37 / 41 % | 555 / 756 / 558 | 1455 / 1156 / 988 | 1946 / 1692 / 1949 |
| d0e r1 / r2 / r3 | 40 / 49 / 47 | 40 / 12 / 34 % | 596 / 697 / 619 | 938 / 1448 / 1003 | 1947 / 1693 / 1897 |

- **The cross-check agrees.** `timerq_slowstate.ps1`: 6 spin runs, all 6 slow; fg 0 in all runs (hidden desktop).
- **The opt-out was really on in d0e.**
  - Applied 0.14-0.36 s after process start: C=0x0 -> C=0x1 S=0x0, apply_error 0.
  - Read back every 0.5 s as held in 99.6-99.7 % of reads (256-291 reads).
  - The only miss is the last poll, 0.55-0.57 s before exit. There the state reads C=0x0 and the re-set fails (-1): process teardown. That cleared the sidecar's `ok`, so the wrapper reported FAIL (bad 3) and the read-out INCOMPLETE.
  - d0 read C=0x0 throughout: the game itself never set the state in these devoff2 runs.
- **Read-out v2 (06:24).** An on-arm run now counts as verified when it was applied, has no errors, and either its record is ok or its only loss came within `-TeardownS` (1.5) s of exit. New columns: `ver`, `lost_s`. On this run the verdict is NO EFFECT. Regressions: the 05:28 dry run still gives OPT-OUT HELPS; the 0330 pair without records still gives INCOMPLETE. The sidecar is left as is: the runner switch is to be dropped, and the read-out handles teardown afterwards.
- **Answer: no.** The opt-out does not keep the E cores out of the ~550 MHz state.
  - **Ruled out:** process-level EXECUTION_SPEED / EcoQoS throttling as the cause, including EcoQoS the system applies to the process automatically. Per Agent 10's caveat, drop `host_execution_throttling_optout` from S4 and the runner switch (#19 part 2).
  - **Not ruled out:**
    - PL1 / package power: not in sys.csv.
    - Visibility or foreground QoS applied per thread or by the scheduler, which the process flag doesn't override. The effective QoS level can't be read back.
    - The best-efficiency overlay / EPP.
- **PL1 can be measured next time.** `\Energy Meter(RAPL_Package0_PKG)\Power` exists, in mW. One sample at 06:25 with no game running: PKG 12255 (12.3 W), PP0 6307, PP1 0.1. Power Meter reports 0. S4 proposals:
  - A pkg / PP0 power column in the sys.csv sampler (Agent 8's), or a 1 Hz sampler next to it. A slow state at a power plateau points to PL1; a slow state well below any plateau rules PL1 out.
  - For visibility: run `timerq_slowstate.ps1` over window 4's visible-desktop runs (fg 1).

## Package-power sys.csv columns (Agent 1, 06:28; staged for after window 4)

**The ask.** Stage the package-power sys.csv column as new sampler files for after window 4, with no W4b file change. Why: task #24 ruled out process-level EcoQoS, and PL1 is still open. A slow state on a package-power plateau points to PL1; a slow state well below any plateau rules PL1 out.

**What is staged.** Everything is in `bench/agent11/syscsv-pkg/` (new files only). Agent 8's files are untouched: their hashes are recorded in `originals-0631.txt` (06:31) and were checked again by every test.

| file | sha256 (16) | what |
|---|---|---|
| `LdSys.cs` | 3D995E1DF9FD0288 | Agent 8's sampler core plus one PDH counter, `\Energy Meter(*)\Power` (`C_POWER=5`, `NC=6`), and 4 columns at the end of each row |
| `LdSys.cs.diff` | 1B5C608502E72686 | the adoption diff (+25/-4), with Agent 8's path on both sides |
| `sys_summary.py` | 1C482668045B2B96 | a copy of Agent 8's, with one line changed (L70): `header_ok` allows extra columns after the known ones |
| `sys_summary.py.diff` | C0406E46789532D8 | the optional adoption diff (+1/-1, cosmetic) |
| `sys-csv.ps1` | 001C25E40952F5BC | test copy only: the repo depth and the DLL cache (`build\agent11\cache`) changed. Not for adoption; `sys-csv.ps1.diff` (D3AE5C4B93EECDDF) is for reference |
| `test_syscsv_pkg.ps1` | 163E0D024127C60A | the staged and the original sampler, alternating, with no game (`-Compare -Rounds N`) |
| `test_sys_summary_compat.py` | 9592237C3EF97524 | the original and the staged `sys_summary.py` on the newest new-format and old-format sys.csv |
| `make_diffs.ps1` | 1A1711F489BA4C57 | writes the 3 diffs and runs `git -c core.autocrlf=false apply --check` on the 2 adoption diffs (read-only) |

**The change.**
- The new columns are `pkg_w,pp0_w,pp1_w,dram_w`, in W with format `0.000`. Their sources are the instances `RAPL_Package0_PKG`, `_PP0`, `_PP1` and `_DRAM`; the counter gives mW, as the mean over the last interval.
- A column is blank when the counter set is missing (non-Intel or a VM: then `counters=5/6` and `failed=[power:0x...]`) or when a channel has no valid value.
- Nothing else changes: the 24 original columns keep their order and values.

**Consumers (all read by name).**
- `sys_summary.py` looks columns up by name and checks each row's field count against the file's own header.
  - Its `header_ok = header == COLUMNS` becomes False when extra columns are present, but nothing acts on sys.json's `header_ok`. `run-timing.ps1:633` checks the frame summary's flag, not this one.
  - The 1-line diff turns it into a prefix check.
- `matrix_recheck.py` uses `DictReader`.
- My `timerq_slowstate.ps1` and `pthrottle_readout.ps1` use `Import-Csv`.

**Tests (07:17-07:23, no game, ≤2 threads).**
- **`test_syscsv_pkg.ps1 -Compare -Rounds 3`, 07:21:14-07:22:40: RESULT PASS, 58/58 checks.**
  - Output: `build/agent11/syscsv-pkg/test/20261122-072114/`.
  - Setup: 3 staged and 3 original runs, alternating. Each uses the test's own PID as `-GamePid` and `-MaxSec 12`, and each exits 0 with `reason=max_sec`.
  - Staged runs: counters 6/6, 12 rows, and 28 fields in every row. The header is the 24 original columns plus the 4 new ones. `pkg_w` is in (0.5, 400) W in every row after the first, and `pp0_w` ≤ `pkg_w`.
  - Both arms fill the same 22 of the 24 original columns. `tz_passive_min_pct` and `tz_temp_max_c` are blank in both, because this laptop's thermal-zone counters have no data: `failed=[tz_temp:no_data tz_passive:no_data]` in both arms.
  - Agent 8's `LdSys.cs` and `sys-csv.ps1` equal the 06:31 record and were not changed by the test. The `build/agent8/cache` listing is unchanged: the original ran from its cached DLL. The staged DLL compiled into `build/agent11/cache/LdSys-3d995e1d.dll` (33,792 B).
- **The first run, at 07:17:42 with 1 round, failed 1 of 23 checks.** The test expected `failed=[]`, but the thermal-zone counters fail at init in both arms on this machine. This was a test fault, not a sampler fault. The check now requires that `failed` has no `power:*` entry and is the same list in both arms.
- **`test_sys_summary_compat.py`, 07:22:41: PASS** (`build/agent11/syscsv-pkg/compat/20261122-072241/`).
  - New-format file (28 columns): the original gives `header_ok` False, the staged copy True.
  - Old-format file (24 columns): both give True.
  - `missing_columns` is empty, and the JSON is otherwise identical.
- **`make_diffs.ps1`, 07:18:16:** both adoption diffs pass `git apply --check` against Agent 8's current files.
- **Static:** every staged file is ASCII and LF, without a BOM; PowerShell parse errors 0.

**Readings (idle desktop, rows after the first, 4 staged runs).**
- `pkg_w`: median 13.0-13.9 W (min 9.3, max 26.2).
- `pp0_w`: median 7.0-7.5 W.
- `pp1_w`: 0.000-0.003 W.
- `dram_w`: always 0.000, so treat the DRAM channel as unsupported on this laptop.
- **The first row (10.7-22.2 W) is not meaningful:** its rate covers the time since the query was opened.

**Cost (3 runs per arm, medians).**
- The CPU is the same within noise:
  - sampling thread: 1.17 ms per sample staged vs 1.15 ms original;
  - `steady_cpu_pct`: 0.445 vs 0.437 % of one core.
- At 07:17 one round showed 0.458 vs 0.116 %. That was noise: the 3-round runs range from 0.13 to 0.48 % in both arms.
- **Wall time per sample:** 4.46 vs 2.76 ms (runs 2.9-7.7 vs 2.4-3.0 ms).
  - The Energy Meter read waits inside `PdhCollectQueryData` (collect 2.5-6.6 ms vs 1.9-2.5 ms) without using CPU.
  - At 1 Hz that is under 1 % of the interval.

**Adoption after window 4 (Agent 8's call; I apply nothing).**
```
git -c core.autocrlf=false apply --check bench/agent11/syscsv-pkg/LdSys.cs.diff bench/agent11/syscsv-pkg/sys_summary.py.diff
git -c core.autocrlf=false apply bench/agent11/syscsv-pkg/LdSys.cs.diff
git -c core.autocrlf=false apply bench/agent11/syscsv-pkg/sys_summary.py.diff     # optional (sys.json header_ok only)
```
- **The DLL cache key is the content hash of `LdSys.cs`.** So the first sampler start after adoption compiles a new DLL (a few seconds of `csc` CPU). Do that start outside a timed run, for example with one functional run or a short `-MaxSec 3` sampler call.
- **`pthrottle_w4b_hash.ps1` will flag `LdSys.cs` and `sys_summary.py` once they are adopted.** Both are in its 53-file closure, so this is expected after window 4.

**S4 follow-up (not written tonight).**
- A read-out next to `timerq_slowstate.ps1`, for example `pkg_slowstate.ps1`. It would compare `pkg_w` 10 s before and after each slow-state onset and look for a package-power plateau.
- Outcomes:
  - slow state on a plateau: PL1;
  - slow state well below any plateau: PL1 ruled out, which leaves visibility QoS and EPP / the overlay.
- `timerq_slowstate.ps1` stays unchanged tonight (W4b read-out).

## Task #14 (board run 2): #38 `timer_queue_precise_wait` in S4a, and its ON smoke (verdict written 13:56)

- **Spec:** `build/agent11/s4a/AGENT3-SPEC.md` (13:28, 1DA33FD3…, 48 lines), sent to Agent 3 at 13:28: r4 = devoff4 with the cvar ON, against the OFF run r1 on the same bin and route; one functional run, never timed.
- **Apply check (item 2): clean, no mismatch.** Agent 2's `build/agent2/s4a-prep-apply.txt` (13:25:04) L31-38 and L60: `git apply --check` and `git apply` PASS, `timer_queue.cpp` D8724B29C43286B0 → 015C04A22DACC592 (12,839 → 16,091 B); RESULT PASS (L69). Agent 2's S4a table (`perf-notes/agent2-baseline.md` L372, 13:42) gives the same hashes, with `build/agent11/timerq/stage/timerq.diff` (D07A2DC4…) as the source. My re-hash (13:30, again at 13:56): snap1's copy = `stage/timer_queue.cpp` = 015C04A2…; live is still D8724B29…. Agent 10's own check agrees (b2r row 30, §29: ALL PASS).
- **Bin:** `build/agent2/devoff4-bin` (MANIFEST 16DCC939…; r4's run.json: exe_sha256 6BE3C713…; `rexruntime.dll` 870276A6…, which contains the cvar name, MANIFEST L212).
- **Runs:** r4 `build/agent3/runs/20261122-134754-s4a-r4-precise-devoff4` (ON, tag `s4a-r4-precise-devoff4`, 420 s requested, route `harness/routes/b-gate-menus-long.txt`, hidden desktop, "FUNCTIONAL ONLY ... NOT FOR TIMING") against r1 `build/agent3/runs/20261122-133333-s4a-r1-off-devoff4` (OFF). Check text: `build/agent3/s4a/checks/20261122-134754-s4a-r4-precise-devoff4.txt` (`s4a_check.py --cand r4 --base r1 --tq-ref r1`).
- **Flags:** Agent 3's standard flags plus `timer_queue_precise_wait=true` (run.json cvars: only this one); r1 set no cvar.
- **Log line seen:** exactly one, `[2026-11-22 13:48:00.193] [info] [core] [t32016] TimerQueue: precise wait (timer_queue_precise_wait)` (r4 game.log L21), 6.29 s before the first frame. r1 has none.
- **Functional:** exit 0, no dumps, no crash events; 54 of 54 route steps; WM_CLOSE in 3.96 s (r1: 2.35 s). [error] 0 and [warning] 142 in both runs. logdiff vs r1 at warning: NEW 0, MORE 0, FLAG 0, GONE 4 (all Toypad); at info, 6 NEW keys, of which the only non-Toypad one is the proof line. fatal, stuck_lock, minidump and protect_failed greps 0. Scenes of 2 s or more: the same set as r1. The route marks match r1 from the first frame to up-2; later idle marks differ by the usual idle-exit timing, as they also do between r1 and r3 (Agent 3).
- **Ticks:** `rex::thread::TimerQueue` (tid 2448) has rising cycles in 97 of 97 steps (98 samples, median step 2.0 s).
- **Thread CPU, % of one core** (from the first frame + 20 s to the end − 10 s, 183.5 s in r4; a share of one core, not a timing number):

  | Run | `timer_queue_precise_wait` | `rex::thread::TimerQueue` |
  |---|---|---|
  | r1 (13:33:33) | false (default) | 37.65% |
  | r4 (13:47:54) | true | 1.25% |

  That is about 30× lower. The spec's "effect seen" bar (r4 at most ~5% and at most 1/5 of r1) is met. The bench predicted ~30-45% → a few % (L1831-1837; in game L1839-1846).
- **Caveats:** one run per arm on the hidden desktop. r4's E cores were in the slow state from 181.5 s (14% of sys.csv rows; Agent 3: the idle tail); r1 never entered it. Both runs fall after the Windows Update changes between windows 3 and 4, so they compare with each other, not with window-3 numbers.
- **Verdict: PASS.** The switch turns on (one proof line), behaviour at warning level is unchanged against r1, the ticks still advance, and the TimerQueue thread drops from 37.65% to 1.25% of a core. The default stays OFF; any timing claim waits for W5 (S4-DRAFT §2c).
