# CP state in the 83FAF200-class hangs: s4b-24 and s4b-20, compared with gate A (Agent 6, 22:40)

Read-only. Same method as gate A ([cp-state-gateA.md](cp-state-gateA.md)): dumpstacks.py on the dumps, run at BelowNormal; handleinfo.py on the waited handle; threadcpu tables; source in Agent 2's snap1 tree.

| run | dir (build/agent3/runs/) | dump | cvars that matter |
|---|---|---|---|
| gate A | 20261122-210906-w6-gateA-p2fcv-level | hang-36276.dmp | p2fc + **verify** + slow_frame_log_ms=1 |
| s4b-24 | 20261122-220520-s4b-24-w6-c1 | hang-31952.dmp | rearm, hold_global_lock, keep_watch; **no verify** |
| s4b-20 | 20261122-221447-s4b-20-m1-level | hang-13236.dmp | only shared_memory_upload_nontemporal_copy (M1); **no C1, no hold_global_lock, no verify** |

All three were taken while Agent 2's -j8 build held the host at 100 % CPU.

Raw output: [dumpstacks-s4b24.txt](dumpstacks-s4b24.txt), [dumpstacks-s4b20.txt](dumpstacks-s4b20.txt), [cpwait-s4b24-s4b20.txt](cpwait-s4b24-s4b20.txt), [grep-cpwait.txt](grep-cpwait.txt).

## 1. CP thread "GPU Commands (F8000018)" (s4b-24 tid 38280, s4b-20 tid 37436)

The stack is the same in both dumps:

```
ntdll!ZwWaitForSingleObject+0x14
KernelBase!WaitForSingleObjectEx+0xAF        rbx=handle  rsi=0xFFFFFFFF (INFINITE)  rdi=0 (not alertable)
rexgpu-xenos +0xC2044   fn +0xC1E70 +0x1D4   = CheckSubmissionFence (inferred, see 2)
             +0xC16E6   fn +0xC1570 +0x176   = memexport readback, full path (inferred)
             +0xBC2EB   fn +0xBA3B0 +0x1F3B  = IssueDraw (the ~8 KB function, at its tail)
             +0x16B2C   fn +0x166A0
             +0x15808   fn +0x157C0
             +0x14071   fn +0x13B50 +0x521   type-3 packet dispatcher, DRAW case
             +0x1331A   fn +0x130F0          ExecutePacket
             +0x13453   fn +0x133F0          indirect buffer
             +0x13DBB / +0x1331A / +0x11FC3 / +0x11C5C (worker main) / +0x187DD / XHostThread::Execute
stale frames from the EndSubmission call just before the wait: +0xB9E83 (fn +0xB9BF0), +0x10922E, +0x109298
```

Waited object (handleinfo.py, from the dump's handle stream):

| run | handle | object | state at dump |
|---|---|---|---|
| s4b-24 | 0x1064 | unnamed auto-reset (synchronization) Event | 1 (signaled; most likely set while the dump writer had the thread suspended) |
| s4b-20 | 0x1070 | unnamed auto-reset Event | 0 (not signaled: the CP was blocked on it) |

Gate A's CP was at the same call site (IssueDraw +0x1F3B → +0xC1570 → +0xC1E70) but one step earlier: inside +0xB9BF0 → +0x109000 → D3D12Core → nvwgf2umx (the submit), running, ~85 % kernel.

## 2. What +0xC1E70 is (source: build/agent2/snap1/.../src/graphics/d3d12/command_processor.cpp)

- The D3D12 CP has only 3 INFINITE waits: `CheckSubmissionFence` L3987 and L4009 (`fence_completion_event_`), and `RetireOnDemandMemexport` L3275 (`on_demand_fence_event_`). The last needs `readback_memexport_on_demand` (default off) and isn't on the IssueDraw path.
- `IssueDraw` L3097-3113: after a draw with memexport ranges, `readback_memexport` (default on) takes the fast path (default). The fast path calls `CheckSubmissionFence(0)`, which never waits. When the previous readback slot isn't ready (first use, size change, not yet complete) it falls back to `IssueDraw_MemexportReadbackFullPath` (L3561). That calls `AwaitAllQueueOperationsCompletion()` (L3583), i.e. `CheckSubmissionFence(submission_current_)`: `EndSubmission(false)` first (the D3D12 submit, where gate A's CP was), then `WaitForSingleObject(fence_completion_event_, INFINITE)` (L4009, where s4b-24/20's CP was).
- So: +0xBA3B0 = IssueDraw, +0xC1570 = full-path memexport readback (maybe with the fast path inlined), +0xC1E70 = CheckSubmissionFence, +0xB9BF0 = EndSubmission. This is inferred from structure: there are no symbols for rexgpu-xenos. Confidence is high: it is the only submit-then-wait-INFINITE pattern reachable from IssueDraw.
- That full-path call is what the slow-frame log counts as "memexport syncs" (`kMemexportFlush`, L3562), and its wait is the "host-gpu wait" (`kFenceWait` scope). Gate A's 9.7 s frame #7124: 1244 syncs, host-gpu wait 482 ms (1224x), so about 0.39 ms per wait. The other ~9.2 s was CP CPU time (kernel-heavy, verify).

**What the CP was doing during the stall:** one host↔GPU round trip per memexport draw: submit all recorded work, then block until the GPU fence passes. It was **not** hashing (verify was off in both runs), **not** doing K-checks, and **not** waiting on physical_protect_hold_global_lock (off in s4b-20, and the CP was waiting on an Event, not a lock).

## 3. Owner and waiter: the same as gate A (finding 10)

- Owner: guest render thread (tid 0x17; s4b-24 XThread8EB8 F80001A8 tid 36536; s4b-20 XThread5540 F80001AC tid 21824). It holds CS 0x84959EDC (owner 0x30111018, recursion 1 in all 3 dumps) and spins in user code:
  - s4b-24: `__imp__sub_83FBF7D0+0x31F`;
  - s4b-20: `__chkstk+0x25` ← `__imp__sub_83FBF7D0+0x39A`;
  - both: r15 = 83FBF868, rbx = 83FBF7D8.
  - Callers: sub_83FBFB30+0x395 ← sub_83FB33E0+0x2390 ← sub_82B66AC0 ← … ← sub_83FAEB78 (thread entry).
  - Gate A: `__imp__sub_83FAF180+0x235` with the same callers. So this is the same fence poll (H1 inside H0's loop) in all three.
  - Cumulative CPU: user 115.7 s / kernel 5.4 s (s4b-24); user 114.4 s / kernel 7.5 s (s4b-20).
- Waiter: Main XThread (F800002C), sub_82FEB7B8 → sub_82AB2040 → sub_82B79938 → sub_82B71308 → sub_82A2A260+0x6F → sub_83FFF940+0x3DA → sub_83FF2EE8+0xB93 → RtlEnterCriticalSection. This is gate A's waiter path; the dump was written from this thread.
- Other threads: all idle in waits, including the D3D12/NV driver threads and the 9 "D3D12 Pipelines" threads.

## 4. CP CPU during the stall (threadcpu, per 2 s)

| run | CP kernel | CP user | CP whole run | busy guest thread |
|---|---|---|---|---|
| gate A (verify) | **75-86 %** | – | verify runs: kernel median 47-49 % | – |
| s4b-24 | 3-8 % (22:07:44-58) | 8-14 % | median k 3.9 % / u 8.8 % | F80001A8 (owner) user 56-85 % |
| s4b-20 | 5-11 % (22:18:00-20) | 11-24 % | – | – |

Runs without verify have a CP kernel median of 6-16 %. Neither s4b run has slow-frame lines (no slow_frame_log_ms), so their sync and wait counts are unknown.

## 5. Answers

**(a) Is the CP's kernel time there without verify?** No. In s4b-24 and s4b-20 the CP stays at its normal 3-11 % kernel through the stall and is idle (waiting, or runnable but not scheduled) 65-90 % of the time. Gate A's kernel load comes with verify (47-49 % kernel median over the whole verify run, vs 6-16 % without). So KeepWatchVerifyRecord's VirtualQuery is **not** excluded; it is still the likeliest source of gate A's kernel time. But the hang does not need verify: the CP stalls at the same IssueDraw memexport sync, waiting instead of computing.

**(b) Mechanism.**
1. The render thread (guest tid 0x17) takes CS 0x84959EDC and, still holding it, polls a GPU fence (H0/H1) until the CP reaches a fence packet. This is game design; on real hardware the wait is brief.
2. The Main thread blocks on the CS (finding-10 waiter path).
3. The CP is executing a DRAW_INDX (PM4 0x22) whose memexport readback took the full-path sync: EndSubmission, then an INFINITE wait on the D3D12 fence event.
4. The owner's fence advances only after the CP has worked through every draw before the fence packet. Each full-path memexport draw costs a submit, a GPU round trip and a thread wake-up.
5. The STUCK detector fires when the sequence takes over 5 s. That needs a slow CP: CPU work per draw (verify, gate A), or slow round trips (a starved host delays the submit, the driver and the CP's wake-up), or a very large number of syncs.

**Can it happen without CPU starvation?** Not shown, and not excluded:
- All 3 hangs were under the 100 % -j8 build. In s4b-24/20 the CP was mostly not running during the stall, which fits round trips and wake-ups slowed by contention.
- W5 (16 runs, quiet desktop) had 0 STUCK-LOCK, but that is weak evidence. W5's run.json has no input script (title + attract only). Agent 3's hang runs use the vpad input script (menu walk + level load).
- W6's timed runs are "as in windows 4 and 5" (matrix-window6.json notes: same runner and driver, no input), so **W6 will not exercise the L route either**.
- At gate A's 0.39 ms per wait, a quiet host would need over 12,000 syncs before one fence to reach 5 s, against 1244 in gate A's worst frame.
- The direct test is an untimed vpad L-route run (s4b-20's set, or p2fc's set) on a quiet host with no build running, with slow_frame_log_ms=1 so the per-frame sync and host-gpu-wait counts are logged.

**Caveat:** the function names in 2 are inferred (no symbols for rexgpu-xenos). The snap1 source may differ slightly from devoff4b.

## 6. Perf candidate after S4: the memexport readback full-path sync (source reading, not measured)

Every IssueDraw with memexport ranges reads the exported bytes back (`readback_memexport` is on by default). The fast path (`IssueDraw_MemexportReadbackFastPath`, L3607-3700) double-buffers per key (base address + size). It only avoids a sync when the *other* slot's submission has already completed on the GPU (`submission_written[read_index] <= submission_completed_`, L3681-3685; `CheckSubmissionFence(0)` only polls). Otherwise it calls `IssueDraw_MemexportReadbackFullPath`, which copies into a separate readback buffer, ends the open submission, and waits INFINITE for the GPU (L3583 → L3969-4013).

Tracing the code:
- Same-key memexport draws inside one submission alternate between the fast path and a full sync. The slot written by the previous call is in the still-open submission.
- Once per frame per key, the fast path succeeds only if the GPU has caught up with the previous submission. A GPU running a frame or more behind makes nearly every memexport draw a full sync.
- Each full sync costs a D3D12 submit (EndSubmission), a host↔GPU round trip, a thread wake-up, and a second copy.
- Gate A's 9.7 s frame #7124 logged 1244 such syncs (host-gpu wait 482 ms, 1224 waits).

Possible directions, all for after S4 and none tested: more slots per key; waiting on the older, already-submitted submission (CheckSubmissionFence(submission_written[read_index])) instead of ending the current one; or deferring the copy-back to the next guest-visible sync point (the batched / on-demand modes that exist behind `readback_memexport_batched` / `readback_memexport_on_demand`).

Data needed first: per-frame "memexport syncs" counts from normal-speed frames. Agent 3's two planned quiet-host vpad L-route rows with slow_frame_log_ms=1 will provide them.

## 7. Additions from Agent 12 (22:51) and gate B (Agent 6, 23:12; gate B dump read 05:50; quiet-host answer 06:20, n = 2 at 06:59)

### 7.1 Verify itself drives the CP's kernel time (Agent 12's data)
- Row 7 `20261122-214221-s4b-07-c1v-level` matches gate A. It has verify on but no P2, fr0 or slow-log, on the L route.
  - Kernel share of GPU Commands CPU: 91 % in both runs.
  - Per-2 s kernel % median: 49 vs 47.
- The 10 non-verify runs Agent 12 checked show 20-36 % share and a median of 4-16. They include C1-on gate B on the same route, s4b-24 and s4b-20.
- User time is only ~9 % of the CP's CPU, so hashing is not the cost.
- Suspect, read from the code and not profiled. The chain:
  1. KeepWatchVerifyRecord (s4-c1v3 shared_memory.cpp L684-705; holds G from L686) calls
  2. KeepWatchVerifyReadable (L668-679), which calls
  3. memory::QueryProtect, i.e. VirtualQuery + RegionSize (rexglue-sdk src/core/memory_win.cpp L157-171).
- That chain runs at least once per MakeRangeValid, because readable_end is local (L694). RegionSize walks the PTEs of the whole uniform region.
- Row 7 had no STUCK in 600 s.
- This agrees with the gate A CP read (perf-notes/agent6-attract-stalls.md §14): in gate A's 9.7 s frame the CP burned ~9.2 s of CPU, mostly kernel. Verify's cost is kernel VirtualQuery work under G, not hashing.

### 7.2 Gate B: a 4th hang with the owner at 83FAF200, verify off
- **Run:** `20261122-222313-w6-gateB-p2fc-level` (p2fc + fr0 + slow_frame_log_ms=1, verify off, L route).
  - STUCK-LOCK on CS 0x84959edc at 22:26:29.586; owner tid 0x17 at lr=83FAF200; hang-38764.dmp.
  - It recovered and ran to 22:30:41.
- **CP during the stall** (GPU Commands F8000018, host tid 32624): 8-23 % CPU per 2 s (kernel 2-11 %, user 6-14 %). So it was waiting, as in s4b-24 and s4b-20.
  - Before 22:26:01 it was 40-73 % busy; it stayed low until ~22:26:31.
  - Other host tids: owner XThread9038 (F80001A8) 36920, Main XThread 27760.
- **Host load (answers Agent 12's question):** gate B ran under the full -j8 load, like gate A, s4b-24 and s4b-20.
  - Agent 2's native -j8 build ran 20:53:30-22:39:52 (build/agent2/snap4b-steps.txt L20-21).
  - build/agent2/snap1-on/.ninja_log shows 8 compile edges in flight at 22:23:13, 22:25:50, 22:26:01, 22:26:24 and 22:26:29.
  - From 22:25:50 these were legodimensions_recomp.423-430.cpp.obj, at 180-330 s each.
- **Slow frames** (game.log, verify off): other_ms ≈ 13.3 + 0.819 × syncs (r 0.82).

  | frame | time | length | syncs | host-gpu wait | per wait | notes |
  |---|---|---|---|---|---|---|
  | #32879 | 22:26:04 | – | 0 | – | – | 2445 ms of GPU-thread idle |
  | #33127 | 22:26:24.251 | 4873 ms | 698 | 4212 ms over 696 waits | ≈6.1 ms | |
  | #33131 | 22:26:32.530 | 7979 ms | 2736 | 4836 ms over 2708 waits | ≈1.8 ms | other 3142 ms |
  | later frames | 22:26:37-41 | – | 514-1154 | – | 0.16-0.3 ms | build still at 8 edges |
  | gate A, for comparison | – | 9.7 s | 1244 | – | 0.39 ms | ~9.2 s of CP CPU (verify) |

- **Read:** without verify, the stall time is spent in fence waits, not CP CPU.
  - Two causes are possible: a busy GPU, or round trips slowed by the starved host. I can't separate them, because the scene got heavy right after the stall (5.3-5.7 k draws, 0.86-0.92 M vertices per frame).
  - sys.csv can't help: cpu_util_pct ≈ cpu_perf_pct in every row.
- **Dumpstacks on hang-38764.dmp:** deferred overnight, done at 05:45 in task #22. The result is in 7.3.
  - Agent 1 (23:11): not tonight. It goes in the morning batch with any f10a/f10b dumps. Agent 12 has already matched gate B's owner/waiter callers and PM4 0x22 GPU state to the other three hangs. f10a/f10b on a quiet host will settle GPU-bound vs starved host.
  - Agent 12 (23:12) doesn't need it. Gate B is waived by name (Agent 1, 22:55), and its STUCK lines meet Agent 1's final finding-10 rule.
- **Owner caller chains from the STUCK lines (Agent 12, for S7):**
  - Gate B's chain matches gate A's exactly: 83FBFBDC <- 83FC0CA8 <- 83FB3AC8 <- 83FBF698 <- 83FBFA98 <- 82BD6BA4.
  - s4b-24 and s4b-20 share a deeper chain: 83FBF7B4 <- 83FBFA98 <- 83FBF868 <- 83FBFBDC ...
  - Owner lr: 83FAF188 in gate A; 83FAF200 in the other three.
  - All four have the same waiter, at lr=82A2A270, and the GPU thread on PM4 opcode 0x22.
- **Waits vs memexport syncs (Agent 3, 23:11, for S7; gate B game.log L5472 and L5482):**
  - Host-gpu waits match the memexport syncs almost one for one: #33127 had 696 waits vs 698 syncs; #33131 had 2708 waits vs 2736 syncs (10948 KB).
  - "memexport full-buffer" was 0x in both frames and in all 36553 slow-frame lines.
  - So the stall is one fence wait per memexport sync. P2's counter (P2c = 0) doesn't count these syncs, so 0 does not mean "no syncs".
  - This matches the slow-frame fit above (other_ms grows with syncs) and §6's memexport readback full-path sync candidate.
  - Agent 3 asked for dumpstacks on hang-38764 tonight, as the only dump with P2 on and verify off. Agent 1 had already deferred it to the morning batch (23:11), so it waits for Agent 1's word.
- **So:** all four L1-poll hangs (gate A, s4b-24, s4b-20 and gate B) happened while the -j8 build ran. Agent 3's quiet-host vpad L-route rows are the test.

### 7.3 Gate B dump (hang-38764.dmp): dumpstacks at 05:45, task #22 (Agent 6)

- **Run:** `python -B build/agent6/hang/dumpstacks.py build/agent3/runs/20261122-222313-w6-gateB-p2fc-level/hang-38764.dmp build/agent6/hang/dumpstacks-gateB.txt 32624,36920,27760` at BelowNormal, 0.7 s, exit 0. Guest symbols came from the run dir's legodimensions.map. Raw output: [dumpstacks-gateB.txt](dumpstacks-gateB.txt).
- **When:** the dump is stamped 04:26:30 UTC (22:26:30 local). That is ~0.4 s after the STUCK-LOCK line (22:26:29.586) and 196 s after process start.
  - It falls inside slow frame #33131 (logged 22:26:32.530, 7979 ms long, so it began ~22:26:24.55): the frame with 2736 syncs and 4836 ms of host-gpu wait.
  - The dump write (all other threads suspended) is part of that frame's time.

| | gate B (hang-38764) | gate A (hang-36276) | s4b-24 / s4b-20 |
|---|---|---|---|
| CS 0x84959EDC | owner 0x30111018, recursion 1 | same | same |
| CP state at the dump | **running**, user mode (no syscall at RIP) | running | **blocked** in WaitForSingleObjectEx(INFINITE) |
| CP top frames | nvwgf2umx+0x7FFE20 ← D3D12Core +0x234F51 / +0x23ED64 / +0x207EC6 (unverifiable) ← +0x109000+0x5C ← **+0xB9BF0+0x1CC** (EndSubmission) | nvwgf2umx+0x81C5F0 ← D3D12Core+0x2041F2 ← +0x109000+0x5C ← **+0xB9BF0+0x1F3** (EndSubmission) | ntdll ← KernelBase ← **+0xC1E70+0x1D4** (the wait in CheckSubmissionFence) |
| CP lower frames | +0xC1E70+0x47 (CheckSubmissionFence) ← +0xC1570+0x176 (full-path memexport readback) ← +0xBA3B0+0x1F3B (IssueDraw) ← +0x13B50+0x521 (DRAW case) ← … ← XHostThread::Execute | same | same from +0xC1570 down |
| CP cumulative CPU | user 45.2 s, kernel 20.9 s (32 % kernel) | user 22.2 s, kernel 263.3 s (92 % kernel, verify) | user 14.5 s, kernel 5.6 s (s4b-24) |
| owner (guest tid 0x17) | XThread9038 (F80001A8), host tid 36920, spinning: RIP `sub_83FAF180+0x3F` [gpu_wait_backoff.cpp.obj] ← `__imp__sub_83FBF7D0+0x39A` ← sub_83FBFB30+0x395 ← sub_83FB33E0+0x2390 ← sub_82B66AC0+0xBF6 ← … ← sub_83FAEB78+0x110 (thread entry); rbx = 83FBF7D8, r15 = 83FBF868; user 88.0 s, kernel 6.3 s | RIP `__imp__sub_83FAF180+0x235`, same callers | RIP in `__imp__sub_83FBF7D0` (+0x31F; `__chkstk` ← +0x39A), same rbx/r15 |
| waiter | Main XThread (F800002C), host tid 27760: RtlEnterCriticalSection_entry+0xBAF → ExceptionHandler::WriteDump (the dump writer); guest sub_82A2A260+0x6F ← sub_82B71308+0xBC ← sub_82B79938+0xE6 ← sub_82AB2040+0x41F ← sub_82FEB7B8+0x200D ← … ← xstart+0x833 | same | same |
| other threads | all in waits, including the 9 "D3D12 Pipelines" threads and the NV driver threads | same | same |

**Verdict (Agent 3's question: did the CP sit in the same fence wait?):**
1. **Same hang as the other three.** Same lock and owner, same waiter path, same owner callers. This time the owner snapshot lands in the native override `sub_83FAF180` rather than in `__imp__`; both are the H1 fence poll inside H0's loop. The CP is in the same IssueDraw → full-path memexport readback → CheckSubmissionFence sequence.
2. **At the moment of the dump the CP was not in the fence wait.** It was in the submit half of the full-path sync (EndSubmission → D3D12 → NV user-mode driver), like gate A. The D3D12 call inside EndSubmission differs from gate A's (+0x1CC vs +0x1F3); they can't be named without symbols. s4b-24 and s4b-20 were caught in the wait half.
   - One snapshot can't give the split between the two halves. The threadcpu data (CP at 8-23 % CPU per 2 s during the stall, 7.2) and #33131's 4836 ms of host-gpu wait in 7979 ms both say most of the stall was spent in the wait half.
3. **P2 on doesn't avoid the sync.** With P2 on and verify off, the CP still reaches IssueDraw_MemexportReadbackFullPath. This agrees with Agent 3's game.log read (waits ≈ syncs, P2c = 0).
4. **No verify-style CP load.** The CP's kernel share is 32 %, inside the non-verify band (20-36 %, 7.1); gate A's was 92 %.
5. **Still open:** whether the round trips were slow because of the GPU or because of the -j8-starved host. The dump can't tell; Agent 3's quiet-host rows (f10a/f10b) will.

Caveats: the rexgpu-xenos function names are inferred (section 2). The D3D12Core frames can't be checked for a CALL before them, because that module's code isn't in the dump.

### 7.4 Quiet-host answer: Agent 3's f10a/f10b (reported 06:20)

**Setup.** Agent 3 ran both sets untimed: devoff4b-bin, vpad L route, tags placed through the fixed sidecar, slow_frame_log_ms=1.
- **The host was quiet.**
  - Before launch: 23.5 % CPU (f10a) and 39.8 % (f10b) over 10 s.
  - No build or compiler processes during the runs.
  - Background: the agent CLIs at 15-26 %, and other agents' python at 8 % or less.

**Both runs PASS, with no hang.**
- logdiff vs s4bL0: NEW 0 / MORE 0. f10b's P2c check passed.
- STUCK-LOCK 0, no dumps.
- Both reached the end of the route with 3/3 tags.

**f10a (s4b20's set, C1 OFF).**
- 2 frames of 1 s or more. The max, 1.79 s, was a loading frame.
- Syncs: 18810 in total, max 350 per frame, and at most 24 per frame through the cinematic. This set never makes the 2736-sync bursts.
- Every P2-family run did make them: f10b, gate A, gate B, w6s3, and s4b23 (which hit 2750).
- Under the build, s4b20 still had a 12.0 s frame (8316 draws) at story-load +38..+50 s, with its STUCK-LOCK at +42.0 s. s4b20 had no slow-frame log, so it's unknown whether that frame was syncs.

**f10b (gate B's set).** The same frames, quiet vs gate B under -j8:

| Frame | Quiet (f10b) | Loaded (gate B, -j8) |
|---|---|---|
| 691/698-sync frame | 1.18 s, 0.98 ms per wait | 4.87 s, 6.05 ms per wait |
| 2736-sync frames | 2.66 s and 2.89 s, 0.29 and 0.37 ms per wait | 7.98 s, 1.79 ms per wait |
| rest of the frame | about 1.9 s | about 3.1 s |
| syncs in the whole run | 45.5k | 60.9k |

**What this answers.**
- **7.3 point 5:** the GPU work is the same, but each round trip was slower under load: about 5-6x in the frames above, and Agent 3 gives 5-20x overall. That points at the -j8-starved host, not the GPU. There was one run per set (n = 2 in 7.5).
- **The margin is small.** The STUCK-LOCK detector fires at 5 s. The worst quiet frame was 2.9 s, and w6s3 reached 3.99 s under the build without a hang. So a P2-family run on a busy host can still cross 5 s. The second f10a/f10b pair is in 7.5.
- **For the fix side:** the long frames still come from the full-path memexport sync (section 6), with one fence wait per sync. Cutting the number of round trips helps on any host, and most on a busy one.

### 7.5 Second quiet pair: n = 2 per set (Agent 3, 06:59; `build/agent3/f10/RESULTS.md`)

- **0 of 4 quiet runs hung.** These were f10a and f10a2 (s4b20's set) and f10b and f10b2 (gate B's set).
  - None had a STUCK-LOCK or a dump. All PASS (logdiff vs s4bL0 NEW 0 / MORE 0), with 3/3 tags.
  - Under the -j8 build, 4 of the 6 runs in the same hour hung. One-sided Fisher exact p = 0.07; one more clean quiet pair would make it 0.03.
- **Quiet worst frames:** 1.79, 1.54, 2.89 and 1.79 s, all under the 5 s detector. The hung runs under the build reached 7.98-13.14 s.
- **The same GPU work, slower round trips.**
  - The 2736-sync frame has 6262-6313 draws in every run.
  - Per wait in that frame: 0.18-0.37 ms quiet vs 1.79 ms in gate B. In the ~690-sync frame: 0.21-0.98 ms vs 6.05 ms.
  - The CPU-only rest of the 2736-sync frame: 1.30-1.90 s quiet vs 3.14 s in gate B.
- **Why the host.**
  - The build uses only the CPU.
  - Over +60 s..vortex, gate B drew about 20 % fewer frames/s (13.3 vs 16.7-16.8). That can't account for 5-30x per wait.
  - The slowdown comes in episodes. Gate B's 1644-sync frame at +60 s, with the build still at 100 % (busy 9), took 0.11 ms per wait (quiet: 0.18-0.29).
  - Limit: GPU clocks weren't logged. On this laptop the CPU and GPU may share a power budget, which could explain a modest slowdown, not 5-30x.
- **Correction to the last row of the 7.4 table: total syncs depend on timing, not on load.**
  - The quiet runs alone range from 45.5k to 77.2k for gate B's set; f10b2's 77.2k is more than gate B's 60.9k. For s4b20's set they range from 18.8k to 28.0k.
  - Which bursts happen depends on whether the readback fast path's previous slot is ready (section 6).
  - Agent 3 retracted the n = 1 point "under load more draws took the full-path sync".
- **Reading.**
  - Load is the likely trigger (p = 0.07, not proof): the -j8 build stretches each memexport full-path round trip until a 2736-sync frame crosses the 5 s STUCK-LOCK detector.
  - The quiet margin is still small: 2.89 s worst, and w6s3 reached 3.99 s under the build without a hang. So cutting the round trips (section 6) is the fix; a no-build-during-runs rule only lowers the odds.
