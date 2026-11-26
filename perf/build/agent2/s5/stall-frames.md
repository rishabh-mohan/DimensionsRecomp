# GPU-wait / memexport stall frames (parked for later; M2, from the 2026-11-25 nops smoke)
Source: nops-smoke/post/nops-smoke-post-20261125-201245-z4fix.txt, A1/A2 sync-log + slow_frame_log_ms=1.

| frame | seen in | what is known | next step (later) |
|---|---|---|---|
| #6553-#6615 | earlier S5 attribution (pre-nops) | slow-frame run, not pipeline create | attribute GPU wait vs memexport readback |
| #7539 | A2 burst (opt-in on) | 496 ms, pipeline create 0.0 ms, 67 new pipelines: create stall is off the command thread, the rest is not create | split the 496 ms: forced waits / fence / memexport |
| #7620 | earlier S5 attribution | next stall after the 67-miss burst | same as above |
| #1706 | A2 | the one remaining sync create (42.9 ms), memexport VS: cannot move async | none (by design) |

No work on these until the Overseer asks.

## Stall-frame attribution from the A1/A2 slow-frame logs (2026-11-26 03:22, M2; read-only, Idle priority)
Sources: nops-smoke/runs/20261125-203044-s5nops-a1/game.log (opt-in off) and 20261125-203509-s5nops-a2/game.1.log
(d3d12_async_depth_only_pipelines=true); slow_frame_log_ms=1, same attract route. Frame numbers shift ~30-50 between
the runs; pairs were matched by content (same new-pipeline count, readback size, memexport sync count).
"residual" = frame - (gpu-thread idle + host-gpu wait + translate + create + texture load): time no logged bucket covers.

| event | A1 | A2 | breakdown | class |
|---|---|---|---|---|
| scene-load burst | #7487 637.2 ms | #7539 495.9 ms | 67 new pipelines; A1 has 8 sync depth-only creates = 298.2 ms on the command thread, A2 has 0 (async; dropped draws 140 -> 162). idle 41.0/37.0, host-gpu wait 17.8/17.6 (1x), translate 3.2/2.9; readback 29x 3008 KB with **1 stalled**. Residual 276.5 -> 438.1 ms | PSO + an untimed stalled readback |
| memexport storm | #7505 467.5 ms | #7561 515.2 ms | 1644 memexport syncs (6.6 MB), host-gpu wait 165.7/172.6 ms over ~1640 waits, cpu-write invalidations on memexport pages 3.8/3.1 MB; residual ~300-340 ms (per-sync overhead outside the timed wait) | memexport, not PSO |
| memexport storm | #5266 349.9 ms | #5298 324.2 ms | 2736 memexport syncs (11 MB), host-gpu wait 158.6/158.1 ms (2730x) | memexport |
| memexport | #7490 219.3 ms | #7542 202.9 ms | 128 memexport syncs (1 MB), host-gpu wait 28.0/26.9 (126x) | memexport |
| guest idle | #5068 228.3 ms | #5098 222.0 ms | gpu-thread idle 212.0/207.6: the guest submitted nothing (load on the CPU side) | not GPU |

Frames >= 100 ms by class: A1 create 1x 637 / memexport 8x 1708 / gpu-idle 1x 228 / other 2x 270 ms;
A2 memexport 10x 1919 / gpu-idle 1x 222 / other 5x 978 ms (other includes #7539).
- The async opt-in saves 141 ms on the burst frame (637 -> 496, -22%), not the full 298 ms: the residual grows by ~160 ms.
  Candidates (unproven): the untimed stalled readback in that frame waits longer, or the off-thread compile of the 67
  pipelines competes for CPU with the guest/command threads (MX570 laptop). Next step needs a timed "readback stalled
  ms" field in the slow-frame line (code change, not now).
- The bigger total cost is memexport sync storms (1.7-1.9 s of >= 100 ms frames per run), the same in both arms: PSO
  work won't fix those. The old #6553-#6615 / #7620 (pre-nops run) probably belong to this memexport class (they come
  after the burst, like #7505/#7561); not verified, that run's log was not re-read.

## gpman-native recovered hang (2026-11-25 ~20:54:35; Overseer FYI 03:10Z) - async-PSO opt-in: NOT related
Run `build\agent3\gameplay\runs\20261125-204323-gpman-native`: STUCK-LOCK on critical section 0x84959edc during story load
after a Toypad prompt timed out; recovered, WM_CLOSE exit 0; dump hang-43820.dmp (not analysed, waits for resume).
- run.json: bin_dir `build\agent3\gameplay\bin-native`, cvars {native_fps_limit: 60}; the run toml is the NativeGPU 0.2.0
  layout (native_fsr3=false, native_fps_limit=60) with no d3d12_async* key.
- bin-native rexruntime.dll 641BD22519921ACD and rexgpu-xenos.dll 9A7CC3F4853A8E8B are byte-identical to
  nativefinal2-bin (same two sha256 prefixes). The async-depth-only-pipeline opt-in exists only in devs5nops-bin
  (rexgpu-xenos.dll 55BE4D19142A0EE5), and it is off by default even there.
- So that build has no async-PSO code at all, and the native path doesn't create Xenos D3D12 pipelines. Lead to follow
  later: a guest critical section (0x8495xxxx is a guest address) held across the Toypad timeout / story-load path,
  i.e. game-side or the Toypad/HID emulation, not the GPU backend.

### Hang addresses mapped (2026-11-26 03:44; legodimensions.map of that run + gen-noflag sources; dmp NOT parsed)
This replaces the "game-side / Toypad" lead above: the lock owner was inside the native GPU draw hook.
- Owner tid 0x13, parked at lr 82BCE244 = sub_82BCE1F8+0x4C, which is the return address of `bl 0x83FC6A58`.
  sub_83FC6A58 is REX_HOOKed to `DrawIndexedVerticesHookQueued` (rexlego/src/gpu_native/draw.cpp:5205/5748; the map
  shows sub_83FC6A58 public in draw.cpp.obj). The guest lr doesn't change inside host code, so the owner was somewhere in
  that hook (inline DrawIndexedVerticesHook or the worker submit) while holding guest CS 0x84959edc.
- Owner callers: 82BCD688 = sub_82BCD668+0x20, 82B3A668 = sub_82B3A5D8+0x90, 82B6FFD0 = sub_82B6FF88+0x48,
  82B7309C = sub_82B726C8+0x9D4. 82100526 / 82110000 are stack-scan noise (below the first guest function
  sub_82620000; 82100526 isn't 4-aligned).
- Waiter tid 0x4: 82A2A270 = sub_82A2A260+0x10, a 0x28-byte wrapper around `__imp__RtlEnterCriticalSection`; callers
  82AED6BC = sub_82AED5A0+0x11C, 82B7132C = sub_82B71308+0x24, 82FB01A0 = sub_82FB0180+0x20, 82B7995C = sub_82B79938+0x24,
  82AB2108 = sub_82AB2040+0xC8, 82FEBDE0 = sub_82FEB7B8+0x628.
- frames.csv of that run: frame #28585 (frame clock ~674 s) took 11972 ms with 1775 draws and 232 pipeline creations
  costing 10757 ms (90% of the frame); #28587 1418 ms / 76 PSOs 815 ms; #28589 707 ms / 25 PSOs 223 ms. game.log at
  20:54:29-30 shows a burst of new guest textures/shaders (new scene). The detector fired at 671.09 s after 5 s.
- Reading: NOT a deadlock. It was an ~12 s synchronous native-PSO compile storm inside the draw hook on the guest render
  thread, which held game CS 0x84959edc while thread 0x4 waited for it. It recovered by itself (fps 3.9 -> 60 within
  ~60 s). This is the native path's own pipeline creation, not the Xenos d3d12 async opt-in. The same class shows smaller
  elsewhere in that run (#36188 1388 ms / 1130 ms PSO, #39052 1616 ms / 1311 ms PSO, ...). Leads: native PSO
  pre-warm or async creation in the native path; the run started with an empty native-pso.bin (`no startup pipeline
  recipes yet`), so a warm cache would likely have hidden most of it. Host-side proof needs the dmp's host stack
  (cdb isn't installed); not done.
