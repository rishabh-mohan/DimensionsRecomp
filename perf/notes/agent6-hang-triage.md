# Agent 6: STUCK-LOCK on CS 0x84959edc (task #25)

Status: **written 2026-11-22 ~06:20; §9 revised ~06:35 at Agent 1's request; baseline result (§8, §3.4) added ~07:20.** This covers Part A (native3d) and the re-scoped Q1-Q4; the reverse-order pair is in §7 and the baseline-bin attract run in §8.
Method: read-only analysis. No game runs, builds, git writes or installs; every script is single-threaded. No run dir or dump was moved or changed.

> [!WARNING]
> Every run here is FUNCTIONAL ONLY: hidden desktop, on a laptop with an i7-1255U (12 logical CPUs) and an NVIDIA MX570 (2 GB). The machine was saturated during most of these runs. Treat times as indicative. The stacks, lock states and event order are solid.

## Bottom line

1. **Not a deadlock.** All 7 reports in 4 runs, the baseline-bin run included (§8), are long holds of kGraphicsLock (guest CS 0x84959edc) that ended on their own. Every run closed via WM_CLOSE with exit 0. In the native3d dump the lock is already being handed off (count 0, owner 0), and the main thread takes it 1 ms after the dump is written.
2. **Same waiter and same kind of owner on both GPU paths.** The waiter is always the main thread's scene teardown, which acquires kGraphicsLock through sub_82A2A260. The owner is always the game's render thread, which holds kGraphicsLock while it waits for the GPU:
   - **native3d:** synchronous PSO creation inside DrawIndexedVerticesHookQueued. One frame made 56 pipelines in 4341 ms on a cold NVIDIA driver cache.
   - **devoffB and devoff3-warm (Xenos path):** the guest D3D runtime busy-waits until the emulated CP's read pointer passes a target (sub_83FBF7D0 → sub_83FAF180). In both dumps, the CP thread is meanwhile blocked in a host wait inside rexgpu-xenos.
   - **baseline-bin (base1, Xenos path):** the same render thread (tid 0x17) in a different loop: the game busy-waits on a GPU query, calling the D3D query GetData (sub_83FB09E8) from sub_82BDCFB8 until it stops returning S_FALSE. The query completes only when the CP gets past it, and in the dump the CP thread was compiling a shader in the NVIDIA driver (dxilconv.dll) rather than waiting (§3.4).
3. **Q2: it is a GPU wait.** It is not IO, loader work or a lock cycle. On Xenos the owner burns a full host core and never yields:
   - The loop's Xenon SMT-priority hints (`cctpl`, `db16cyc` ×32, `cctpm`) compile to comments only.
   - The function it calls on every pass (sub_83FA2698) is just two loads.
   - base1's owner (§3.4) polls the D3D query GetData back to back, with no hints at all.
4. **Q3: load makes it worse but doesn't cause it.** All 4 runs with a report ran on a saturated machine: 3 between 05:03 and 05:32, and the baseline run at 06:39.
   - The CPU was 97-100% busy: Defender used 1.2-4.8 cores, PresentMon 1 core and dwm about 1.1 cores (base1: 97.7% busy on average, Defender 1.35 cores, max 3.04).
   - During the waits the game got only 1.3-1.8 cores (1.5-2.8 in base1), and the host GPU sat mostly idle (14-29% utilisation, idle throttle flag set).
   - Two later runs under similar load had no report, but neither is a clean control (§4).
5. **Q4: pre-existing: yes.** baseline-bin (game 127e04b + SDK 2897c31, from before tonight's changes) hit the same STUCK-LOCK in attract-base1, 34.5 s into the attract (H0+34.45 s), with the CPU 97.7% busy (§8). It has the same CS, the same waiter chain and the same owner thread as devoffB. No run before 05:03 had reached these scenes under load, which is why the 89-log history scan found nothing earlier.
6. **08933a7 is cleared, and so is native3d's exe.** In the reverse-order pair, the same native3d exe (B90DF683) ran warm with no report: 187 pipelines in 282.9 ms, and 151.7 ms for the 56-pipeline frame. That matches nativeB's 284.4 ms. The 7753.6 ms in the 04:59 run came from a cold NVIDIA driver cache.
7. **The hang dump makes every first report worse.** At the first report, the SDK writes a minidump in-process, which freezes the game for another 1.7-3.6 s. native3d's 3658 ms frame 16324 *is* that dump. Recommendations are in §9.

## 1. Data and scripts

| item | location / purpose |
|---|---|
| runs | `build/agent3/runs/`: `20261122-045945-bgate-long-native3d` (exe B90DF683), `…050343-bgate-long-nativeB` (01C4D5A3), `…052024-attract-devoffB` (C3F8686E), `…052901-attract-devoff3-warm` (2522D436, seeded storage devoff2-214), the reverse pair `…055041-bgate-rev-nativeB` and `…055439-bgate-rev-native3d`, and the baseline run `…063542-attract-base1` (baseline-bin, exe FB922AC9) |
| dumps (read only) | hang-63248.dmp (native3d), hang-52704.dmp (devoffB), hang-69196.dmp (devoff3-warm), hang-60748.dmp (base1, read with dumpstacks.py) |
| [align.py](<workspace>/build/agent6/hang/align.py) | Joins frames.csv, perf.csv, samples.csv and game.log on launch-relative time. T0 comes from log-flush brackets 7-29 ms wide. Output: `align-native3d.txt`, `align-nativeB.txt` |
| [dumpstacks.py](<workspace>/build/agent6/hang/dumpstacks.py) | Minidump reader: lists threads, decodes the guest CS and walks guest back-chains using each run's own map. Output: `dumpstacks-native3d.txt`, `-devoffB.txt`, `-devoff3warm.txt`, `-base1.txt`, `-base1-focus.txt`. Note 1: the guest-sub offsets it prints for host RIPs are host offsets. Note 2: it prints lock_count byte-swapped (16777216 means 1) |
| [scan_native.py](<workspace>/build/agent6/hang/scan_native.py) | Scans 22 native runs for frames with >2 s of creation and for STUCK-LOCKs. Output: `scan-native.txt` |
| [revpair.py](<workspace>/build/agent6/hang/revpair.py) | For named native runs: totals and top frames. Output: [revpair.txt](<workspace>/build/agent6/hang/revpair.txt) |
| [base_check.py](<workspace>/build/agent6/hang/base_check.py) | One run dir: the STUCK lines, run.json, frames of 4.5 s or more with their H0 offset, and the sampler, samples.csv and gpu.csv rows around the report. Used for base1 (§8) |
| [base_owner.py](<workspace>/build/agent6/hang/base_owner.py) | Resolves report addresses to guest functions with one map read and prints their generated code: call sites, backward branches. Output: [base1-owner.txt](<workspace>/build/agent6/hang/base1-owner.txt) |

## 2. The seven reports (Q1)

| # | run | report (wall) | owner tid / object | owner lr | r3 | SDK GPU line: PM4, rptr / wptr | dump written |
|---|---|---|---|---|---|---|---|
| N1 | native3d | 05:03:06.929 | 0x13 / 0x30107018 | 82BCE244 | 300BE000 | none (the native path has no PM4 CP) | 05:03:10.478, hang-63248.dmp (+3.55 s) |
| X1 | devoffB | 05:24:05.288 | 0x17 / 0x30111018 | 83FAF200 | 1 | 0x22, 0x161 / 0x35a | 05:24:07.073, hang-52704.dmp (+1.79 s) |
| X2 | devoffB | 05:24:52.471 | same | 83FAF200 | 0x17 | 0x22, 0x2bc3 / 0x2c72 | none (only the first report dumps) |
| X3 | devoffB | 05:24:58.445 | same | 83FAF188 | 7048F7E0 | 0x22, 0x2dbb / 0x2fe4 | none |
| X4 | devoffB | 05:25:57.839 | same | 83FAF200 | 1 | 0x22, 0x369f / 0x372d | none |
| W1 | devoff3-warm | 05:32:12.361 | 0x17 / 0x30111018 | 83FBF868 | 1 | 0x22, 0x26d7 / 0x28a9 | 05:32:14.077, hang-69196.dmp (+1.72 s) |
| B1 | base1 (baseline-bin) | 06:39:22.996 | 0x17 / 0x30111018 | 83FB09F0 | 1 | 0x22, 0x27e / 0x30c | 06:39:26.534, hang-60748.dmp (+3.54 s) |

Agent 3 matched X1-X4 to frames of 8.5 s (H0+16.4), 5.3 s (+63.6), 16.4 s (+69.5) and 5.1 s (+128.9): perf.csv rows 8117, 8367, 8371 and 8518, in that order (rechecked 06:24). All four had pm 0. W1's frame is devoff3-warm perf row 6707, 10.05 s, and B1's is base1 perf row 9726, 8.58 s (H0+34.45 s, §8). PM4 type-3 opcode 0x22 is DRAW_INDX, and rptr < wptr in every report, so commands were always queued.

**Waiter: the same functions in all 4 runs.** It is always the Main XThread: guest tid 0x4 in native3d, 0x6 in the three Xenos-path runs. Outermost first:

`sub_82FEB7B8 (82FEBDE0) → sub_82AB2040 (82AB2108) → sub_82B79938 (82B7995C) → sub_82FB0180 → sub_82B71308 (82B7132C) → sub_82AED5A0 (82AED6BC) → sub_82A2A260 (lr 82A2A270, the kGraphicsLock acquire wrapper)`

Only native3d differs, in two ways:
- the call site inside sub_82FB0180 is +0x68 (82FB01E8), against +0x20 (82FB01A0) on Xenos;
- there is one extra frame, 82FB0140 = sub_82FB0068+0xD8, between 82AED6BC and the acquire.

In native3d the wait sits between the NuCpuSkin teardown of skin 7 and skin 8.

**Owner: the same loop in devoffB and devoff3-warm, a game-side query poll in base1, and a different path on native.**
- **Xenos.** 83FAF188 is sub_83FAF180+0x8, 83FAF200 is +0x80, and 83FBF868 is sub_83FBF7D0+0x98. These are snapshots of one loop (§3.1).
  - X1/X2 callers: `83FBFBDC (sub_83FBFB30+0xAC) ← 83FC0CA8 (sub_83FC0C10+0x98) ← 83FB3AC8 (sub_83FB33E0+0x6E8) ← 83FBF698 (sub_83FBF5A0+0xF8) ← 83FBFA98 (sub_83FBFA48+0x50) ← 82BD6BA4 (sub_82BD6B80+0x24)`.
  - X3/X4/W1 add three inner frames (`83FBF7B4 ← 83FBFA98 ← 83FBF868`), so the wait was re-entered from a nested submit.
- **base1 (B1).** lr 83FB09F0 is sub_83FB09E8+0x8, the return from the prologue's `bl __savegprlr_14`, like X3's 83FAF188. sub_83FB09E8 is the D3D query GetData, and r3 1 is its S_FALSE (not ready). 82BDD028 is the polling call in sub_82BDCFB8, called from 82BDC918 (sub_82BDC8E8+0x30) ← 82BAEA7C (sub_82BAE968+0x114). 83FB0948 (sub_83FB0738+0x210, in the query-issue code) is a stale stack slot: the dump's host stack goes straight from sub_83FB09E8 to sub_82BDCFB8 (§3.4).
- **Native.** lr 82BCE244 is the return from the `bl` at sub_82BCE1F8+0x48 (§3.2). Callers: `82BCDB60 ← 82B7AC0C ← 82BA0D20 ← 82BCF9D8 ← 82B7AC0C ← 82B753E8 ← 82B7DAD0 ← 82BACCC4 ← 82BD6CD0 (sub_82BD6C80+0x50)`.

**No lock cycle.** The owner's lr is never an RtlEnterCriticalSection site. In all 7 reports the owner was making progress and later released the lock.

## 3. What the owner is doing (Q2)

### 3.1 Xenos path: a busy-wait on the CP read pointer

Simplified from the generated code: sub_83FBF7D0 is at `DimensionsRecomp/rexlego/generated/default/legodimensions_recomp.248.cpp:35181`, sub_83FAF180 at `.107.cpp:36777`, sub_83FA2698 at `.429.cpp:35196` and sub_83FC91D0 at `.190.cpp:35191`. These are tonight's generated sources, which use the native3d map partitioning.

```text
sub_83FBF7D0(dev, target, ...)            // wait until the CP has consumed the ring up to target
  rptr = *(dev+11024)                     // points at the CP read-pointer writeback
  if target already consumed: return      // ring-distance test against dev+11036
  if *(dev+13600) == 0: sub_83FC0C10(dev) // kick off pending commands
  sub_83FAF088(&w)                        // wait state init
  loop (loc_83FBF860):
    if sub_83FAF180(&w) == 0: break       // lr 83FBF868
    re-read *rptr; repeat while target not consumed
  sub_83FAF0B8(&w)

sub_83FAF180(w)                           // one spin step; returns 1 = keep waiting
  cctpl; 4 x 8 db16cyc; cctpm             // Xenon SMT-priority hints: comments in the C++
  if *(dev+11069) & 2: return 0           // abort flag
  if *rptr != w.rptr: w.rptr = *rptr; w.t = now   // progress restarts the timeout
  sub_83FA2698()                          // lr 83FAF200; body: lwz r11,256(r13); lwz r3,332(r11)
  if now - w.t >= *(0x83809AC0):          // no progress for too long
    if sub_83FC91D0(dev) != 0: return 0   // DbgPrint + the D3D GPU-hang path
  return 1
```

- **What the owner does.** The render thread holds kGraphicsLock and spins until the emulated GPU has consumed enough of the ring.
  - On Xenon, `db16cyc` lowers the hardware thread's priority. The recompiled loop has no such effect: no pause, no yield, no syscall. So it burns a full host core at normal priority.
  - The two dumps show it: the owner thread had used 144 s of user CPU (devoffB) and 88 s (devoff3-warm).
- **Why the timeout never fired.** The timeout counts from the *last progress*. The CP kept moving the read pointer, slowly, so the GPU-hang path never ran.
- **The varying lr and r3 values.** The SDK reports the last `ctx.lr` the generated code stored, i.e. the most recent `bl` site, not the current instruction. So 83FAF188 (just after the prologue's `__savegprlr_29` call), 83FAF200 and 83FBF868 are all the same loop. r3 is live in the loop, which is why it changes.

**Dump states** (from dumpstacks):

| | devoffB, X1 | devoff3-warm, W1 |
|---|---|---|
| guest CS 0x84959edc | **held**: lock_count 1, recursion 1, owner 0x30111018 (REX object 0xF8000270) | **held**: same values (0xF8000274) |
| owner host thread | TID 43012 "XThreadA804 (F80001A8)", running guest code in sub_83FBF7D0. Guest stack sub_83FBFB30 ← sub_83FB33E0 ← sub_82B66AC0. User CPU 144 s | TID 33740 "XThread83CC (F80001AC)", same function and stack. User CPU 88 s |
| CP thread "GPU Commands" | TID 33632, blocked in NtWaitForSingleObject at rexgpu-xenos+0xBF9C4 (function +0xBF7F0). Called through rexruntime+0x276668 from rexgpu-xenos+0xFC820. User CPU 28 s | TID 94944, in the same wait |
| "D3D12 Pipelines" threads | 9, all idle | not checked |
| waiter | Main XThread, inside RtlEnterCriticalSection, writing the dump | same |

**What the CP is waiting for is unknown.** The CP's wait has no symbols: the run dirs have no PDB for rexgpu-xenos. Two dumps 8 minutes apart caught it in the same wait while commands were queued, so the CP wasn't short of input.
- **Best guess:** a host-fence wait. In S11 arm A (same Xenos path, same machine, `slow_frame_log_ms=50`), the CP's host-GPU fence wait makes up 58-86% of the slow frames in this phase (classes "heavy" and "none").
- **Against it:** the GPU looked idle during the holds (§4). A long fence wait on a GPU that looks idle points away from shader throughput, towards residency/paging on the 2 GB card or present/compositor contention on the hidden desktop. That is a question for later, not a finding.
- **To settle it:** resolve rexgpu-xenos+0xBF7F0 with the matching SDK PDB.
- **base1 differs (§3.4):** its CP thread was compiling a shader in the NVIDIA driver (dxilconv.dll) at the snapshot, not waiting.

### 3.2 Native path: synchronous PSO creation

- **The owner's call.** lr 82BCE244 is the return from `bl sub_83FC6A58` at sub_82BCE1F8+0x48. gpu_native hooks that function: DrawIndexedVerticesHookQueued → DrawIndexedVerticesHook (inline) → LockRecording → GetPipeline → synchronous createGraphicsPipeline. Agent 10 agrees (`build/agent10/nb/genfunc-82BCE1F8-snap1.txt`, `mapwhere-stucklock.txt`).
- **The slow frame.** Frame 16323 made 56 pipelines in 4341.2 ms, 77.5 ms each. The same frame in nativeB took 126.0 ms, 2.25 ms each.
- **The dump caught the handoff.** The CS shows lock_count 0, recursion 0, owner 0. The owner, TID 74100 "XThread12174 (F800018C)" (user 92 s, kernel 33 s), was already in a guest NtWaitForSingleObjectEx (sub_83FA6020 ← sub_82B74258 ← sub_82A32950), with a stale KickOffHook frame on its stack. So it released the lock between the report (200.848) and the snapshot (≥200.934). The waiter couldn't take it until it had finished writing the dump.

### 3.3 Why not IO or a loader

- The owner's top frames are the D3D draw/submit path on both GPU paths: the ring-buffer wait on Xenos, PSO creation on native. In base1 they are the D3D query GetData, polled by the game until the CP catches up (§3.4), which is a GPU wait too.
- On Xenos the CP advanced between reports, and every SDK GPU line shows a draw packet (0x22).
- The PRE load frames, which are guest-side file and loading work (`agent6-attract-stalls.md` §11.1), are a different stall class, and none of them coincides with a report.

### 3.4 base1: a game-side poll on a GPU query

Simplified from the generated code, found with [base_owner.py](<workspace>/build/agent6/hang/base_owner.py) on the base1 map, whose partition matches tonight's generated sources: sub_82BDCFB8 is at `legodimensions_recomp.429.cpp:7890` and sub_83FB09E8 at `.422.cpp:37230`. Output: [base1-owner.txt](<workspace>/build/agent6/hang/base1-owner.txt).

```text
sub_82BDCFB8(this, out, wait)                  // the game's "get query result"
  q = this->query; if !q: *out = 0; return 1
  if GetData(q, out, 4, 0) != 1: goto done     // lr 82BDD000: one non-blocking try
  loop (loc_82BDD00C):
    if !wait: return 0
    if GetData(q, out, 4, 0) == 1: goto loop   // lr 82BDD028: the blocking poll
  done: release q (sub_83FB05B0); this[0] = 0; this[1] = -1; return 1

sub_83FB09E8(q, out, size, flags)              // D3D query GetData: EVENT, OCCLUSION, TIMESTAMP
  if *(dev+11069) & 2: zero *out; return 0     // abort flag
  if q was never issued (q+20 & 0x40 clear): return 0x8876086A   // D3DERR_NOTAVAILABLE
  if the CP hasn't consumed the ring up to q+24:    // same ring-distance test as sub_83FBF7D0
    if q+24 == dev+11036: sub_83FC0C10(dev)         // kick pending commands
    return 1                                        // S_FALSE: not ready
  OCCLUSION: if a tile slot still holds the -275 marker written at issue: return 1
  sum the per-tile counts into *out; q+20 |= 0x80; return 0   // S_OK
```

- **The loop.** With the wait flag set, sub_82BDCFB8 calls GetData back to back, with no yield, sleep or SMT hint. Like the ring wait in §3.1, it burns a host core. GetData never calls sub_83FAF180 or sub_83FBF7D0, so the §9 item 4 hook on sub_83FAF180 would not touch this loop.
- **Callers.** 82BDC918 is sub_82BDC8E8+0x30, a cached getter that passes the wait flag through and stores the result at +12. 82BAEA7C is sub_82BAE968+0x114 (`.300.cpp:7375`), which reads two queries per item (+16 and +32) and compares each result with -1. The 4-byte result and the per-item pairs point to occlusion queries. EVENT queries also return 4 bytes, so the type is inferred, not proven.
- **83FB0948 is a stale slot.** It is sub_83FB0738+0x210, the return from `bl sub_83FCBF00`. sub_83FB0738 issues queries (PM4 packets, the -275 markers, q+24) and never calls GetData. The dump agrees: the owner's host stack goes straight from GetData to sub_82BDCFB8.
- **Dump state** (`dumpstacks-base1.txt`, `dumpstacks-base1-focus.txt`):
  - CS 0x84959edc **held**: lock_count 1, recursion 1, owner 0x30111018 (REX object 0xF8000270), the same values as in devoffB and devoff3-warm.
  - Owner: host TID 4620 "XThread120C (F80001A8)", the same REX object as devoffB's owner. Its RIP is in sub_83FB09E8. Its host stack unwinds sub_82BDCFB8 ← sub_82BDC8E8 ← sub_82BAE968 ← sub_82BAF2B8 ← … ← sub_82B74258 ← sub_82A32950, the render-thread entry also seen in native3d (§3.2). User CPU 145.6 s in a 222 s process.
  - CP thread "GPU Commands" (TID 96200, user CPU 43.5 s): **not waiting**, unlike devoffB and devoff3-warm. Its RIP is in dxilconv.dll, Microsoft's DXBC→DXIL converter, with unverified NVIDIA driver frames (nvwgf2umx.dll) between it and verified rexgpu-xenos frames. The run's toml sets no `d3d12_*` options, so the SDK's own dxilconv disassembly (`d3d12_dxbc_disasm_dxilconv`) is off: the driver was compiling a shader on the GPU thread. That fits `PipelineCache::EndSubmission`, which creates queued pipelines on the GPU thread before it waits, at every submission end, occlusion queries included (`agent6-attract-stalls.md` §2, read on SDK HEAD). With no rexgpu-xenos PDB, the calling SDK function can't be named.
  - "D3D12 Pipelines": 9 threads; 8 idle, 1 in D3DSCache.dll.
- **Reading.** The owner waits for the CP to pass the query while the CP compiles, on a saturated machine. So base1 sits between native3d and devoffB: pipeline creation behind kGraphicsLock as on native, but one step removed, because the CP thread compiles while the render thread polls.

## 4. Machine load (Q3)

| run (wall) | reports | CPU busy | Defender (MsMpEng) cores | PresentMon cores | game cores | host GPU during the waits | sources |
|---|---|---|---|---|---|---|---|
| native3d 04:59-05:03 | 1 | not sampled | not sampled | not sampled | 1.3-2.3 in the hold, 0.3-0.8 during the dump | no gpu.csv | samples.csv |
| devoffB 05:20-05:29 | 4 | 97-100% (Agent 3, 05:12-05:35) | 1.2-4.8 (Agent 3) | 1 | 1.28-1.35 in all 4 waits | util mostly 17-27% (single samples up to 58%), throttle 0x1 (GPU idle), 8-15 W; 21 W at other times; P0 with dips to P3/P5 | samples.csv, gpu.csv |
| devoff3-warm 05:29-05:35 | 1 | 99.8% avg | 2.20 avg (max 3.77) | 1.00 | 1.78 avg, 1.29-1.43 at the wait | util 22-29%, throttle 0x1, 10-13 W; 19 W at other times | cpu-sampler-0528.csv, gpu.csv |
| S11 arm A 05:39-05:43 | 0 | 98.0% | 1.66 (max 3.44) | 1.01 | 1.94 | – | cpu-sampler-0528.csv |
| rev-native3d 05:54-05:58 | 0 | 93.4% | 1.60 (max 3.93) | 1.01 | 1.78 | – | cpu-sampler-0554.csv |
| base1 (baseline-bin) 06:35-06:43 | 1 | 97.7% avg, 96.4-99.8% around the report | 1.35 avg (max 3.04) | 1.01 | 2.21 avg, 1.53-2.78 in the hold | util 14-22%, throttle 0x1 (GPU idle), 10.3-11.4 W; P0 with a P5 dip | cpu-sampler-0554.csv (Agent 8's summary), samples.csv, gpu.csv |

- **Saturation is common to all four runs with a report.** During the waits the game got 1.3-1.8 cores (1.5-2.8 in base1), and one of those went to the owner: PSO creation in native3d, the ring wait in devoffB and devoff3-warm, the query poll in base1. The CP thread shared the rest with the guest's other threads, Defender, PresentMon and dwm.
- **The host GPU was not the bottleneck by its own counters:** about 14-29% utilisation, the idle throttle reason set, and power well below what the same runs drew at other times.
- **Load alone is not enough.** S11 arm A (98% busy) and rev-native3d (93%) had no report, but neither is a clean control:
  - arm A's route (b-gate-menus-long) ends at about H0+15 s, before the attract stretch where devoffB reported (H0+16…+129);
  - rev-native3d had a warm driver cache.

  devoff3 cold (05:12, in the same busy period) also had no report; its longest frame was 3.1 s.
- **Reading:** the trigger is a long GPU-side wait under kGraphicsLock: cold PSO compiles on native, a slow CP on Xenos. CPU saturation stretches that wait past the 5 s threshold.

## 5. Did it happen before tonight? (Q4)

- **History scan.** I checked 89 game.logs (`build/agent3/runs/*`, `build/agent8/runs/*`, `build/agent8/matrix/*/runs/*`). Only 3 have STUCK-LOCK lines: native3d (1 report, 4 lines), devoffB (4 reports, 20 lines) and devoff3-warm (1 report, 5 lines). All are from 05:03-05:32 tonight.
- **No earlier run is comparable.** The earlier baseline runs (`20261122-021532-base`, `-022642-base-prof`) were short menu runs that never reached the attract. No earlier run reached these scenes under comparable load.
- **The baseline bin can show a report.** baseline-bin is 127e04b + SDK 2897c31 (exe FB922AC9…, rexruntime E01D4618…). Its rexruntime contains the reporter strings (`critical_section_stuck_seconds`, `STUCK-LOCK`, `Minidump written`) and `input_backend`, so the virtual pad works and a report would be logged. Agent 3 confirmed that its first frame comes at 13.0 s and that attract-report parses it.
- **The baseline spec.** Sent to Agent 8 and Agent 3, and both confirmed it:
  - attract-base1: `harness\run-game.ps1 -BinDir build\baseline-bin -Seconds 600 -GpuLog -Tag attract-base1 -InputScript harness\routes\attract-long.txt`. Cold, no `-SeedXenos`, default 5 s threshold.
  - attract-base2 is identical. Skip it if base1 has a report or never reaches the attract.
  - Load comes from Agent 3's sampler, `build/agent3/logs/cpu-sampler-0554.csv` (until ~07:16).
- **How to read the result:**
  - A report in a baseline run means **pre-existing: yes**.
  - No report on a quiet machine means **not observed (load X)**, which is not proof.
- **Result: pre-existing: yes (§8).** attract-base1 had one report, so attract-base2 was skipped by the rule above.

## 6. native3d in detail (Part A)

### 6.1 Timeline, launch-relative (align.py)

| t (s) | thread | event |
|---|---|---|
| 195.613 | render | frame 16323 starts |
| 195.802 | main (t31544) | skin 7 teardown completes; the next step needs kGraphicsLock |
| 196-201 | process | 1.3-2.3 cores; log grows 4.2-5.4 KB/s |
| 200.811 | render | frame 16323 ends: 5198.0 ms, 56 pipelines, 4341.2 ms of creation |
| 200.848 | main | STUCK-LOCK report, 5.05 s after 195.802; owner at lr 82BCE244 |
| 200.848-204.397 | main | in-process minidump: 3.55 s with the process frozen (0.3-0.8 cores) |
| 204.398 | main | lock acquired; skin 8 teardown starts |
| 204.469 | render | frame 16324 ends: 3657.8 ms, 42 pipelines in 1.3 ms |

- **Q1: a long hold that ended on its own.** The owner held the lock through one 5.2 s frame of synchronous PSO creation, just past the 5 s threshold.
- **The 3658 ms frame 16324 is the dump.** The frame spans 200.811-204.469, the dump runs 200.848-204.397, and the frame's own 42 pipelines took 1.3 ms. Agent 10 reached the same conclusion independently: their row 16322 is this frame.
- **nativeB at the same point:** the main thread waited 1.08 s between skin 7 and skin 8.

### 6.2 Cold vs warm driver cache

| run | order | pipelines | creation ms | 56-pipeline frame (creation / frame ms) | longest frame | reports |
|---|---|---|---|---|---|---|
| native3d 04:59 | 1st | 187 | 7753.6 | 4341.2 / 5198 | 5198 ms | 1 |
| nativeB 05:03 | 2nd | 188 | 277.6 | 126.0 / 608 | 1000 ms | 0 |
| rev-nativeB 05:50 | 3rd | 187 | 284.4 | 177.8 / 854 | 854 ms | 0 |
| rev-native3d 05:54 | 4th | 187 | 282.9 | 151.7 / 614 | 1450 ms | 0 |

- **The difference is the driver cache.** All four runs started with an empty app cache: each logs "no startup pipeline recipes yet" and saves 113-119 recipes at exit. So the 27× difference comes from the NVIDIA driver's shader cache, which persists across run dirs. native3d at 04:59 was the first native run to reach this scene.
- **The build is not the cause.** The same exe, B90DF683, took 7753.6 ms cold and 282.9 ms warm.
- **The 1.45 s frame in rev-native3d** (frame 14631, no pipelines) is the load frame just before the 13-pipeline frame. All four runs have it: 1.20 s, 1.00 s, 0.82 s and 1.45 s.

### 6.3 08933a7 (the guard)

Agent 1 cleared it at ~05:45: the guard needs threaded recording, which was off, and devoffB predates the commit. The reverse pair confirms this from the other side: the same exe is clean once the driver cache is warm.

## 7. Reverse-order pair (addendum)

- **Runs.** Both pair runs used b-gate-menus-long with the frontend off (`native_settings_frontend=false`). Both exited 0 via WM_CLOSE (1.2 s and 4.0 s) after 54/54 steps, with no dumps and no STUCK-LOCK. The CPU was 93.4% busy during rev-native3d, with MsMpEng at 1.60 cores.
- **Result.** The numbers are in §6.2. With the order reversed, both exes create the same 187 pipelines in about 283 ms, and the 56-pipeline frame stays under 180 ms. The 04:59 result needed a cold driver cache, and can't be reproduced on purpose without touching host state, which is out of bounds.

## 8. Baseline-bin attract run (Q4 result)

**Result: pre-existing: yes.** baseline-bin is from before tonight's changes, and it hit the same STUCK-LOCK in the attract.

- **Run.** `build/agent3/runs/20261122-063542-attract-base1`, run by Agent 8 to the §5 spec at 06:35:44-06:43:48.
  - Bin: `build\baseline-bin`, game 127e04b + SDK 2897c31 (exe FB922AC9, rexruntime E01D4618). Route attract-long.txt (4D35FAF4), 600 s cap, `-GpuLog`, cold, no args.
  - 91/91 steps with 0 timeouts. The game exited 0 via WM_CLOSE in 1.74 s, 478.9 s after launch.
  - The harness exit is 1 only because of the `[FATAL] Minidump` line. Since Agent 3's runstats.py change (07:02) the run reads RECOVERED HANG (STUCK-LOCK + dump) instead of CRASHED (§9 item 6).
  - attract-base2 was skipped by the §5 rule, because base1 had a report.
- **The report (B1 in §2).** game.log L209-214, at 06:39:22.996 (launch+219.03 s):
  - CS 0x84959edc after 5 s. The owner is guest thread object 0x30111018, tid 0x17, with lock_count 1 and recursion 1: the same object and tid as in devoffB and devoff3-warm. The waiter is 0x6, the Main XThread.
  - The waiter's chain is identical to devoffB's and devoff3-warm's, frame for frame: `82A2A270 ← 82AED6BC ← 82B7132C ← 82FB01A0 ← 82B7995C ← 82AB2108 ← 82FEBDE0`.
  - The owner is at lr 83FB09F0 with r3 1. Its callers are `83FB0948 ← 82BDD028 ← 82BDC918 ← 82BAEA7C`, a different site from X1-X4 and W1. It is the game's busy-wait on a GPU query: sub_82BDCFB8 calls the D3D query GetData (sub_83FB09E8) until it stops returning S_FALSE, with no yield (§3.4).
  - SDK GPU line: PM4 0x22 (DRAW_INDX), rptr 0x27e < wptr 0x30c, so commands were queued.
  - `[FATAL] Minidump written to hang-60748.dmp` followed at 06:39:26.534, 3.54 s later. The dump (49,377,574 B) is kept. dumpstacks shows the CS still held (lock_count 1, recursion 1, owner 0x30111018), the owner thread (host TID 4620, REX object F80001A8 as in devoffB) running GetData with 145.6 s of user CPU, and the CP thread compiling in dxilconv.dll rather than waiting (§3.4).
- **Where it falls.** perf.csv has 13,321 rows. H0, the first 2823-draw / 366,575-vertex frame, is row 9371 at perf 165.66 s.
  - The report falls in row 9726, an 8.58 s frame at perf 200.11-208.69 s (H0+34.45 s): the 5 s hold plus the 3.54 s dump.
  - Row 9718 (4.78 s, H0+25.60 s) had no report. Agent 3 counts 18 frames of 1 s or more, and Agent 8's 10 s fps buckets drop to 0.8 at the report.
  - For comparison, devoffB reported at H0+16.4, +63.6, +69.5 and +128.9 s.
- **Load: the same saturated machine as in §4.**
  - The CPU was 96.4-99.8% busy around the report (cpu-sampler-0554.csv, 06:39:12-06:39:32). Over the whole run: 97.7% on average, MsMpEng 1.35 cores (max 3.04), PresentMon 1.01, dwm 1.09 and the game 2.21 (Agent 8).
  - In the hold the game got 1.53-2.78 cores (samples.csv, t 214-219 s), then 0.48-0.53 during the dump.
- **GPU: mostly idle in the hold.** gpu.csv at t 214-219 s: utilisation 14-22%, throttle 0x1 (GPU idle), 10.3-11.4 W, P0 with a P5 dip at 219.1 s. Over the whole run: median utilisation 38%, max 86 °C, power cap in 5.3% of samples, no thermal or hardware slowdown (Agent 8).
- **What it settles.**
  - Q4: the hold predates tonight's changes. Reaching the attract scenes on a saturated machine is enough to get it.
  - The 89-log history scan (§5) found no earlier report because no earlier run reached these scenes under load.
  - For §9 item 4: the merged hook on sub_83FAF180 alone would not have covered B1, so the S4 item now adds the same back-off for this query poll.
  - In base1 the CP thread was compiling a shader in the NVIDIA driver at the snapshot, not waiting as in devoffB and devoff3-warm (§3.4). So on the Xenos path too, pipeline creation on the CP thread can hold up the render thread while it waits under kGraphicsLock. That links this hold to the #18 creation stalls (`agent6-attract-stalls.md`).

## 9. Recommendations (Q5)

1. **No code change is needed for correctness.** Every hold ended on its own, and 08933a7 stays.
2. **Stop the dump from freezing a game that recovers (SDK, diagnostics only). Staged only, not an S4 item (Agent 1, 06:28).**
   - Keep the 5 s report line, but write the minidump only if the lock is still held at a second, longer threshold (for example 30 s). That threshold separates real deadlocks from long holds.
   - This is output-identical: it only changes when diagnostics happen.
   - User-visible effect: no added 1.7-3.6 s freeze on the first long hold of a session.
   - Today's kill switch is `--critical_section_stuck_seconds=0`, but it also drops the report.
   - For Agent 10. The exact SDK file still needs to be located (the krnl RtlEnterCriticalSection stuck path).
3. **Native path: S4 lead (a).** A seeded boot pre-create through the existing recipe and seed files (`cache\native-pso-recipes.bin` / `native-pso-seed.bin` via PreparePipelineLibrary, `LEGO_NATIVE_PSO_PREPARE_THREADS`) moves creation to boot. It is output-identical.
   - Players get this from their second launch.
   - The harness needs a warm-recipes arm, which is only allowed *after* window 4.
   - `LEGO_NATIVE_PSO_ASYNC` is **not** output-identical (draws get skipped): keep it off.
4. **Xenos path: one S4 item with Agent 9, the GPU-wait hook on sub_83FAF180** (merged at Agent 1's request, 06:28). The lever is CPU time for the CP, not compile work. The holds had pm 0 and a GPU that looked idle, and the owner's spin took one of the 1.3-1.8 cores the game got.
   - **Design: Agent 9's (a1)/(a2)** in `agent9-codegen.md` S4.1.3, items 2-3. Both hook the poll step with `REX_HOOK_RAW`, gated by an env var that is OFF by default, and then call the original unchanged.
     - (a1) sleeps on a CP sequence counter (`WaitOnAddress`, 1 ms timeout) that the SDK bumps after every guest-visible CP store. It needs rexlego plus an SDK change.
     - (a2) backs off in the hook alone: pause for ~20-50 us, then `SwitchToThread`, then a ~250 us sleep on a high-resolution timer. rexlego only.
   - My earlier (e), a pause plus `SwitchToThread` on each pass, is (a2) with a zero quantum. Agent 9's window-4 sweep (0/125/250/500 us) covers it, so it is no longer a separate item.
   - Output-identical by Agent 9's argument: the loop, its completion test and its exit conditions stay the same; only the poll timing changes. The only guest-visible differences are wall-clock values (dev+22008/22016 and the elapsed value), which already vary run to run.
   - What the hang triage adds to the test plan: a loaded-machine arm, devoffB-bin with attract-long, hook off vs on. Count STUCK-LOCK reports and frames ≥ 5 s, and check that waits whose fence has already passed go straight to the original. The 5 s STUCK-LOCK report stays on as the detector.
   - **Coverage gap found in base1 (§3.4).** The owner there spun in a second loop, the game's query poll (sub_82BDCFB8 → GetData, sub_83FB09E8), which never calls sub_83FAF180. So the S4 item also needs a back-off on that loop, under the same OFF-by-default env var. It is output-identical by the same argument (only the poll timing changes), and the test arm should count reports by owner site (83FAF188/83FAF200/83FBF868 vs 83FB09F0). Two ways to hook it:
     - `REX_HOOK_RAW` on sub_83FB09E8, backing off only when it was called from the blocking site (lr 0x82BDD028) and the original returned 1 (S_FALSE);
     - or a hook on sub_82BDCFB8 itself.
   - A recompiler-wide `db16cyc` → pause mapping (Agent 9's (b)/(c)) would also touch every guest spinlock. Agent 9 ranks both below the hook.
5. **Machine: user question 3 (Agent 1, 06:28).** Excluding the run dirs from Defender and stopping FrameView/PresentMon during timing windows is the user's call, and nobody touches either. Together they used about 2-6 cores during these runs.
6. **Harness.**
   - Label "STUCK-LOCK + dump + exit 0" as RECOVERED HANG. **Done by Agent 3 at 07:02** (runstats.py, `agent3-run-harness.md` §7.4): native3d, devoffB, devoff3-warm and base1 now read "RECOVERED HANG (STUCK-LOCK + dump)", with a "STUCK-LOCK episodes: N; first at T s" line. Exit codes are unchanged: run-game still exits 1 for a dump, and route-report still fails "no crash".
   - Keep the per-run sampler data.
   - Optional repro, only on Agent 1's GO: devoffB-bin, attract-long, `LEGO_TT_LOCK_TRACE=<run>\locktrace.csv` plus `-Arg 'critical_section_stuck_seconds=30'`. This measures hold lengths without the dump freeze.
