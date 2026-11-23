# Gate A hang: what the CP did during frame #7124 (task #16 follow-up, 22:12)

Run: `build/agent3/runs/20261122-210906-w6-gateA-p2fcv-level` (devoff4b; p2fc + verify + slow_frame_log_ms=1, L route).
All reads were read-only and nothing was written into the run dir.
- Sources: `hang-36276.dmp` read with `build/agent6/hang/dumpstacks.py`, output in [dumpstacks-gateA.txt](dumpstacks-gateA.txt).
- `threads-s4a.csv` read with `build/agent6/hang/threadcpu.py`.
- `game.log`.
- rexglue-sdk source in `build/agent2/snap1` (it matches the S4b manifest hashes).

## Verdict

**The CP fits none of the three proposed states. It was running, and the time went to kernel mode: about 85 % of a core in kernel and about 6 % in user mode.**

- **It was not waiting on physical_protect_hold_global_lock (G).** A lock wait uses no CPU. From 21:18:12.5 to 21:18:16.5 the CP used 1.66 to 1.72 s of kernel CPU per 2 s. In the dump the CP is running, with RIP in nvwgf2umx.dll, and no wait frame is on its stack.
- **It was not hashing.** XXH3 runs in user mode, and the CP's user CPU was only 0.11 to 0.14 s per 2 s.
- **The kernel load comes with verify.** In both verify runs the CP's median kernel share is 47 to 49 %. In all five runs without verify it is 6 to 16 % (see the table).
  - Source: verify's only work on the CP is `KeepWatchVerifyRecord`, called from `MakeRangeValid` after each CPU upload (graphics/shared_memory.cpp L379-383, L684-705).
  - For each page it first runs `KeepWatchVerifyReadable`, which calls `memory::QueryProtect`. That function is `VirtualQuery` (core/memory_win.cpp L157-171). The result is cached through `readable_end` only for the rest of the same range.
  - After that it runs XXH3 on the page.
  - **Likely sink: the VirtualQuery syscall.** VirtualQuery sizes the region by walking its PTEs, so it costs more in long runs of pages with the same protection. This is an inference from the source and the CPU split. There was no ETW trace.
- **K and F checks run on guest threads, not the CP.**
  - K is `MemoryKeepWatchGuard`, run at a guest protect from `PhysicalHeap::ProtectKeepWatch`.
  - F runs in the write-fault path.
  - Both also call QueryProtect.
  - This matches the render thread F80001A8: its median kernel share is 29 to 35 % in verify runs, against 1.6 to 3.1 % in side1, side2 and s4b-23.

## Dump snapshot (dump stamped 03:18:20 UTC = 21:18:20 local, inside #7124)

**CP: host tid 17104 "GPU Commands (F8000018)"**
- Cumulative CPU: user 22.2 s, kernel 263.3 s.
- RIP: `nvwgf2umx.dll+0x81C5F0` ← `D3D12Core.dll+0x2041F2` ← `rexgpu-xenos+0x10905C`.
- Unwound chain:
  - the ring buffer, then two nested indirect buffers (+0x130F0 / +0x13B50 / +0x133F0 recurse twice);
  - then the draw-sized function at +0xBA3B0 (at offset +0x1F3B);
  - then +0xC1570 → +0xC1E70 → +0xB9BF0 → +0x109000 → D3D12 / NV driver.
- So it was inside a D3D12 call on a draw path.
- This is one sample, and the rexgpu-xenos functions have no names: peinfo.py found no PDB path in the DLLs, and no symbolizer, dumpbin or cdb is installed.

**Owner: host tid 33924 "XThread8484 (F80001A8)"**
- Cumulative CPU: user 70.7 s, kernel 175.5 s.
- RIP: `__imp__sub_83FAF180+0x235`.
- Guest chain: `__imp__sub_83FBF7D0+0x39A` ← `sub_83FBFB30+0x395` ← `sub_83FB33E0+0x2390`.
- So it was polling the fence (H1 inside H0's loop) and using 55-81 % of a core in user mode during the stall.
- Guest CS 0x84959EDC shows owner 0x30111018, recursion 1.

**Waiter: host tid 8520 "Main XThread (F800002C)"**
- Stack: `RtlEnterCriticalSection_entry+0xBAF` → `ExceptionHandler::WriteDump`, so the waiter wrote the dump itself.
- Guest chain: `sub_82A2A260+0x6F` ← `sub_82B71308` ← `sub_82B79938` ← `sub_82AB2040` ← `sub_82FEB7B8`. This is the finding-10 waiter path.
- Its CPU is about 0 % from 21:18:08 to 21:18:16, while it was blocked.

## threads-s4a.csv, CP (tid 17104), 2-s samples

| interval end | kernel % | user % |
|---|---|---|
| 21:18:06.5 | 75.9 | 6.3 |
| 21:18:08.5 | 82.9 | 7.0 |
| 21:18:10.6 | 78.0 | 6.2 |
| 21:18:12.5 | 48.9 | 17.3 |
| 21:18:14.5 | 82.8 | 5.5 |
| 21:18:16.5 | 86.0 | 7.0 |
| 21:18:18.5 | 43.1 | 2.4 |
| 21:18:20.5 | 14.1 | 2.3 |
| 21:18:22.5 | 62.2 | 9.3 |

- The 21:18:18 and 21:18:20 rows are low because the dump suspended the threads.
- Over the whole run the CP used 289 s of kernel CPU and 27 s of user CPU (91 % kernel).

## CP CPU in each run (median per 2-s sample)

| run | verify | CP kernel % | CP user % | F80001A8 kernel % |
|---|---|---|---|---|
| gate A (p2 + f + keep_watch + verify), L | on | 47.1 | 3.1 | 35.0 |
| s4b-07 c1v (f + keep_watch + verify), L | on | 49.3 | 3.1 | 29.0 |
| s4b-L0 off, L | off | 10.9 | 42.3 | n/a |
| s4b-23 p2fi (p2 + f), L | off | 9.4 | 36.1 | 3.1 |
| side2 p2fc (keep_watch, verify=false) | off | 11.7 | 21.8 | 1.6 |
| side1 p2f | off | 15.7 | 46.7 | 2.3 |
| s4b-01 off | off | 6.2 | 18.0 | 10.2 |

Keep-watch without verify (side2) looks like the other runs without verify. The extra kernel time comes with verify.

## Frame #7124 (game.log L7383)

`9657.9 ms | gpu-thread idle 21.9 | host-gpu wait 482.0 (1224x) | shader translate 0 | pipeline create 0, new 9 | texture load 0.9 (44x) | readback 25x 2048 KB | cpu-write invalidations 10x 40 KB | memexport syncs 1244 (4976 KB), on demand 0`

- **CP work per sync:** remove the dump (3.13 s), the GPU wait and the idle time, and about 6.0 s of CP work is left. Spread over 1244 syncs, that is about 4.8 ms per sync.
- **Control run:** s4b-23 (p2fi, same L route, no verify, slow_frame_log_ms=1) logged 805 frames. All of them had 0 memexport syncs, and the longest frame was 212 ms.
- The logs can't say whether the sync bursts are caused by verify or by where the route was at the time.

## For W6

- The W6 arms run without verify, so this CP load is not present in them.
- Gate A's STUCK-LOCK is finding 10: the owner polls the fence while holding CS 0x84959EDC, and the CP is slowed by verify plus the -j8 compile.
- Each STUCK-LOCK in W6 will be tagged by owner site (H1 vs H2) by the W6 logdiff kit.
