# W6: expected game.log lines per arm (Agent 6 helper, task #16 part 2)

Written 2026-11-22 ~21:55 by the read-only helper. Inputs are read-only: build/agent3/runs/*, build/agent5/w6-draft/matrix-window6.json, build/agent2/snap1 sources.
Outputs are in `build/agent6/w6/`:
- `expect-w6.json`: the machine-readable expectations.
- `log_diff.py`: the analysis script.
- `log-diff.txt`: its full output (per-run stats and every differing template).
- `src_grep.py` / `src-grep.txt`: the source hash check and grep.

## 0. Verdict

- **Verified:** P2 (`shared_memory_single_hold_rearm`) and fix (i) (`physical_protect_hold_global_lock`) print **no line of their own**, both in the source and in the logs:
  - G3-quick p2 vs s0 differ only in Toypad frame counts.
  - G3-quick p2f vs s0 do not differ at all.
  - Side 1 and the p2fi-level run have no switch line.
- **Verified:** p2fc prints `C1 keep-watch: on (with physical_protect_hold_global_lock)` once, and `C1 keep-watch: first kept protect at …` once. Both appeared in 3/3 C1 runs.
  - The init line is always the line right before `Reserving the guest memory arena...`.
  - The first kept protect was `ED19F000, 299892736 bytes` in every run. It came 1.9–5.2 s after the first log line, before the first frame.
  - p2fc also prints a varying number of `C1 keep-watch: N protects kept so far` lines.
- **Verified:** with verify=false no `C1 verify` line can print. The only call site is reached when `physical_protect_keep_watch_verify` is true. Side 2 and G3 p2fc had 0.
- `Recovered stale physical page protection`, `Unhandled guest physical write fault` and `PhysicalHeap::Protect failed` appear 0 times in all 10 runs. The same holds for `BaseHeap::Protect failed`.
- **P2's full-buffer counter has no line of its own.** It shows only as the last field of the `slow frame #` line, so it needs `slow_frame_log_ms` and is never visible in a timed arm.
  - It read `memexport full-buffer 0x (total 0)` on **every** slow-frame line: gate A 7271/7271, p2fi-level 14063/14063, side 1 33692/33692, side 2 35027/35027. This is checked independently with Select-String.
  - So G4 evidence: total 0.
- **Class (d):** only gate A's STUCK-LOCK episode: 5 `[error] STUCK-LOCK:` lines plus `[critical] [FATAL] Minidump written to hang-36276.dmp`. Agent 6 is analysing it. No other run has it, including side 2, which uses p2fc's set without verify.
- **Side 3 is missing.** No run dir with "side3" existed at 21:44.

## 1. Source table (S4b sources = snap1, all 12 MANIFEST after-hashes match)

Paths are relative to `build/agent2/snap1/DimensionsRecomp/rexglue-sdk/src`. All logging goes through REXSYS_/REXGPU_/REXKRNL_ macros. In the log the category is `[sys]`, `[gpu]` or `[krnl]`.

| cvar / message | file:line | level | exact format | prints when |
|---|---|---|---|---|
| `physical_protect_hold_global_lock` (fix (i)) | system/xmemory.cpp:46-48 def; latched :161-164; used :2276-2280 | – | **no log line** | Latched once in Memory::Initialize (kInitOnly). Write protects then take a second recursive hold of G. |
| `physical_protect_keep_watch` (C1) | xmemory.cpp:55-58 def; latched :161-164 | – | (see the next 3 rows) | latched at init |
| C1 init, blocked | xmemory.cpp:169 | INFO | `C1 keep-watch: on, but blocked for this process (native renderer)` | Once at init, if keep is on and the process blocked keep-watch. Native renderer only, never devoff4b. |
| C1 init, hold off | xmemory.cpp:171-172 | WARN | `C1 keep-watch: on, but physical_protect_hold_global_lock is off, so no protect is kept` | once at init, if keep is on and hold is off (no W6 arm) |
| C1 init, OK | xmemory.cpp:174 | INFO | `C1 keep-watch: on (with physical_protect_hold_global_lock)` | Once at init, if keep and hold are both on. Printed just before `Reserving the guest memory arena...` (:180). |
| C1 first kept | xmemory.cpp:784 (NoteKeptProtect, from PhysicalHeap::Protect :2286-2290) | INFO | `C1 keep-watch: first kept protect at {:08X}, {} bytes` | Once per process, at the first protect kept. A protect is kept when all of these hold: hold owned (write protect + hold latched), no old_protect, keep latched, and ProtectKeepWatch true (guards + data providers, :2329-2369). |
| C1 kept count | xmemory.cpp:786 | INFO | `C1 keep-watch: {} protects kept so far` | Per event: at kept = 2, 4, 8 … 2048, then every multiple of 4096 |
| C1 blocked at protect | xmemory.cpp:794-795 | INFO | `C1 keep-watch: blocked for this process (native renderer); every protect takes the normal path` | once, at the first protect when blocked (native only) |
| `shared_memory_single_hold_rearm` (P2) | graphics/shared_memory.cpp:34-37 def; read live at :314 (RangeWrittenByGpu) and :352 (MakeRangeValid) | – | **no log line** | – |
| P2's full-buffer counter | d3d12/command_processor.cpp:253 (`memexport_full_buffer_draws`); ++ at :3094-3095 (memexport draw with no known range → RangeWrittenByGpu(0, kBufferSize)) | – | only as the last field of the slow-frame line: `memexport full-buffer {}x (total {})` | needs slow_frame_log_ms |
| `physical_protect_keep_watch_verify` | graphics/shared_memory.cpp:43-46 def (kRequiresRestart flag, but read live at :381) | – | – | – |
| verify on | graphics/shared_memory.cpp:689-691 | INFO | `C1 verify: on. Hashing CPU uploads; K checks keep-watch protects, F checks write faults` | Once, at the first KeepWatchVerifyRecord. That needs verify on and an invalidation callback, i.e. the first MakeRangeValid. |
| verify mismatch | graphics/shared_memory.cpp:733-735 | WARN | `C1 verify {}: page {:08X} changed since its upload ({} so far){}` ({}=K at a kept protect, with suffix `; protect keeps the normal path`; F at a write fault) | Per mismatch: the first 256, then every 4096th. Needs the hash table from "verify on". |
| `shared_memory_upload_hash_log` | d3d12/shared_memory.cpp:40-43 def; read live at :539 | – | – | – |
| upload hash line | d3d12/shared_memory.cpp:105-112 | INFO | `S4 upload hash: frame {} calls {} ranges {} pages {} ({} KB) first {} unchanged {} changed {} blocks {} changed_blocks {} pages_in_changed_blocks {} u_page {:.4f} u_block {:.4f}` | One per frame with uploads, flushed at the next frame's first upload. The first frames show `u_page -1.0000`. |
| `slow_frame_log_ms` | d3d12/command_processor.cpp:79-82 def (UINT32, 0) | – | – | – |
| slow frame | d3d12/command_processor.cpp:290-304 | INFO | `slow frame #{}: {:.1f} ms \| gpu-thread idle {:.1f} \| host-gpu wait {:.1f} ({}x) \| shader translate {:.1f} ({}x) \| pipeline create {:.1f} ({}x), new {} \| texture load {:.1f} ({}x) \| readback {}x {} KB, {} stalled \| cpu-write invalidations {}x {} KB (on memexport pages {}x {} KB) \| memexport syncs {} ({} KB), on demand {} ({} KB) \| memexport full-buffer {}x (total {})` | Per swap with frame time ≥ threshold, skipping the first swap. With 1 ms that is every frame from #2. |
| memexport range note | d3d12/command_processor.cpp:3086-3088 → graphics/shared_memory.cpp:291 NoteMemexportRange | – | no log line (feeds the slow-frame counters) | slow_frame_log_ms only |
| flush reasons | d3d12/command_processor.cpp:3466-3475 | INFO | `memexport flush reasons (5 s):{}` | slow_frame_log_ms on, at a memexport readback batch flush, at most every 5 s. **0 in every run.** |
| stale protection | xmemory.cpp:672-675 | WARN | `Recovered stale physical page protection for guest {:08X} (host {:016X}, guest_protect {:08X})` | Per physical write fault that no callback/data provider handled while guest metadata allows the write (AccessViolationCallback) |
| unhandled fault | xmemory.cpp:687-691 | ERROR | `Unhandled guest physical write fault: guest={:08X} host={:016X} phys={:08X} guest_protect={:08X} physical_protect={:08X}` | the same path when recovery fails |
| protect failed | xmemory.cpp:2300 | ERROR | `PhysicalHeap::Protect failed due to parent heap failure` | per failing protect (normal path) |
| (related) | xmemory.cpp:1812-1872 | ERROR | `BaseHeap::Protect failed due to …` (zero size / out-of-bounds base address / out-of-bounds range / request spanning regions / uncommitted page / host VirtualProtect failure) | per failing protect |
| STUCK-LOCK | kernel/xboxkrnl/xboxkrnl_rtl.cpp:506-512, :523, :533, :618-631 | ERROR | `STUCK-LOCK: critical section {:#010x} still not acquired after {}s. owner=…`, then `… the owner is tid …` / `owner's callers:` / `waiter's callers:` / `GPU thread:` | Once per waiting episode (one "still not acquired" line per episode). One hang dump per session gives `[critical] [core] [FATAL] Minidump written to hang-<pid>.dmp`. |

## 2. Runs used (all on devoff4b-bin, exe sha DFBE1D43…, hidden desktop, functional only)

| tag | run dir (build/agent3/runs/) | real cvars (run.json) | route | status |
|---|---|---|---|---|
| s4b01 | 20261122-205356-s4b-01-off | `{}`. **No framerate_limit=0, so the 60 fps cap applies.** | harness/routes/b-gate-menus-long.txt (vpad) | done, exit 0, 226 s |
| s4bL0 | 20261122-210059-s4b-L0-off-level | framerate_limit=0 | toypad/routes/level-l.txt (vpad) | 119/119 steps, exit 0, 476 s |
| gateA | 20261122-210906-w6-gateA-p2fcv-level | framerate_limit=0, P2, hold, keep, **verify=true**, slow_frame_log_ms=1 | level-l.txt | **Halted at step 104/119.** RECOVERED HANG: 1 STUCK-LOCK at 544.95 s plus hang-36276.dmp. 12 fps mean. The level loaded around 450 s. |
| side2 | 20261122-211914-w6-side2-p2fc | framerate_limit=0, P2, hold, keep, verify=false, hash log, slow_frame_log_ms=1 | **no input script** (attract/title idle, SDL backend) | exit 0, 267 s. The log rotated: game.4…1 + game.log. |
| side1 | 20261122-212406-w6-side1-p2f | framerate_limit=0, P2, hold, hash log, slow_frame_log_ms=1 | **no input script** (attract) | exit 0, 272 s. Rotated: game.3…1 + game.log. |
| p2fiL | 20261122-213421-s4b-23-w6-p2fi-level (extra, new) | P2, hold, slow_frame_log_ms=1. **No framerate_limit=0, so capped.** | level-l.txt | exit 0, 463 s. Rotated: game.1 + game.log. |
| g3q_* | g3q-20261122-2128/runs/{2129-s0-r1,2130-p2-r1,2131-p2f-r1,2132-p2fc-r1} | the exact W6 arm cvars (from the matrix copy build/agent3/s4b/g3/matrix-g3.json) | W6 harness, no input (10 s warm-up + 20 s window, -Quick) | 4/4 OK, exit 0, ~60 s each |

- **g3q-20261122-2128** is the **G3 quick functional run of the W6 matrix itself** (arms s0/p2/p2f/p2fc). Its logs are the closest evidence for the timed arms.
- **Side 3: missing.**
- `20261122-214221-s4b-07-c1v-level` (probably C1+verify on level) was still running at 21:44 (no run.json yet) and was **not analysed**.

## 3. Per-run counts

The counts are substring counts over all game*.log files of a run. `kept` = the `N protects kept so far` lines, with the largest N in brackets. `first kept Δt` = time from the first log line.

| run | lines | warn | err | crit | STUCK-LOCK lines / episodes | stale | unhandled | PhysicalHeap::Protect failed | BaseHeap::Protect failed | C1 init (with hold) | C1 "on, but" / blocked | first kept (Δt) | kept lines (max N) | C1 verify on / K / F | S4 upload hash | slow frame | full-buffer total | flush reasons |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s4b01 | 215 | 142 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0/0/0 | 0 | 0 | – | 0 |
| s4bL0 | 594 | 144 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0/0/0 | 0 | 0 | – | 0 |
| gateA | 7534 | 142 | **5** | **1** | **5 / 1** | 0 | 0 | 0 | 0 | 1 | 0 / 0 | 1 (3.9 s) | 19 (32768) | **1**/0/0 | 0 | 7271 | 0 | 0 |
| side2 | 70199 | 40 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 1 | 0 / 0 | 1 (1.9 s) | 28 (69632) | 0/0/0 | 35048 | 35027 | 0 | 0 |
| side1 | 67483 | 40 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0/0/0 | 33697 | 33692 | 0 | 0 |
| p2fiL | 14679 | 144 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0/0/0 | 0 | 14063 | 0 | 0 |
| g3q_s0 | 90 | 40 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0/0/0 | 0 | 0 | – | 0 |
| g3q_p2 | 90 | 40 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0/0/0 | 0 | 0 | – | 0 |
| g3q_p2f | 90 | 40 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 | 0 | 0 | 0/0/0 | 0 | 0 | – | 0 |
| g3q_p2fc | 104 | 40 | 0 | 0 | 0 / 0 | 0 | 0 | 0 | 0 | 1 | 0 / 0 | 1 (5.2 s) | 16 (20480) | 0/0/0 | 0 | 0 | – | 0 |

Further details:
- **Boot and exit:** every run has exactly 1 `Reserving the guest memory arena...` (line 17, or line 18 after the C1 init line) and 1 `Title terminated; hard-exiting process.`
- **Rotation:** every rotated run's oldest file starts with the boot line `DXGI adapter: …`, so no lines were lost to rotation.
- **The 40 warnings of the attract/G3 runs:** 2× `Stub XFileFsDeviceInformation!`, 2× `IoDismountVolumeByFileHandle(0xf8000160) - stub`, 1× `__imp__XamBackgroundDownloadSetMode STUB`, and 35× `[NtCreateFile] FAILED` (INSTALL0_2.HDR, and INSTALL0_2…18.DAT twice each).
- **Menu/level routes (142–144 warnings):** they repeat the INSTALL0 probes 4× (136) and add XAM stubs.
- **Kept protects per frame (a side note for R4, from the log only):**
  - side 2: 69632–73727 kept over 35027 frames, about 2.0–2.1 per frame (attract).
  - gate A: 32768–36863 over 7271 frames, about 4.5–5.1 per frame (verify on, level route).

## 4. Diffs, classified

Each diff compares templates: exact keys with numbers → `#`. Toypad frames are keyed by their 4 header bytes, the timestamp and `[tNNN]` are dropped, and `runs\<dir>` becomes a placeholder. The classes are:
- (a) a W6 arm switch;
- (b) an extra switch the timed arms don't have;
- (c) route, timing or run-varying;
- (d) other (flagged).

The full lists are in `log-diff.txt`.

| diff (run vs base) | same route? | (a) | (b) | (c) | (d) |
|---|---|---|---|---|---|
| gateA vs s4bL0 | yes (level-l), but gate A stopped at 104/119 | `C1 keep-watch: on (with …)` 0→1; `first kept protect at #, # bytes` 0→1; `# protects kept so far` 0→19 | `C1 verify: on. …` 0→1 (verify); `slow frame #…` 0→7271 (slow_frame_log_ms) | 14 templates. Toypad frames/pad-mode lines are far fewer: e.g. `Toypad[Write] 0B 16 55 14` 75→1, and the coloured `pad # mode # lit …` lines 186→0, so gate A never reached the in-level ToyPad light traffic. Also `XamUserReadProfileSettings: title setting # not set` 21→12, `NtCreateFile ttappdata:\GUI3\CONFIG.XML` 1→0 and `__imp__XNetLogonGetTitleID STUB` 1→0: the route ended early. | **STUCK-LOCK ×5 error lines (1 episode)** plus `[critical] [FATAL] Minidump written to hang-36276.dmp`. Not attributable from logs: side 2 (same set minus verify) and p2fiL had none. Agent 6 is analysing it. |
| p2fiL vs s4bL0 | yes (level-l); p2fiL capped at 60 fps | none | `slow frame #` 0→14063 | 10 Toypad count changes (±2–6), run-varying | none |
| side1 vs s4b01 | **no** (attract/no input vs menus route; s4b01 capped) | none (correct for p2f) | `S4 upload hash:` 0→33458 plus the first-frames variant `u_page -1…` 0→239; `slow frame #` 0→33692 | Toypad (fewer exchanges); XamUserReadProfileSettings 12→0; `NtCreateFile INSTALL0_#.DAT` 136→34. Also `SDL GameControllerDB: loaded # mappings.` and `SDL input driver initialized successfully` 0→1: the script tagged these "d?", but they are explained (c): they are present whenever the run has no vpad/xinput input backend (side runs, every G3 arm) and absent in all vpad route runs. | none |
| side2 vs s4b01 | **no** | the 3 C1 templates: 1 / 1 / 28 | upload hash 0→34842 (+206 first-frames lines); slow frame 0→35027 | the same as side1 | none |
| **side2 vs side1** | yes (both attract, same extra switches; they differ only in keep_watch=true/verify=false) | **exactly the 3 C1 templates** (1 / 1 / 28) | count-only changes to upload hash/slow frame (frame counts) | none | none |
| g3q_p2 vs g3q_s0 | yes (W6 harness) | none | none | 6 Toypad frame counts (2 vs 4 B1/B3 auth exchanges: periodic, timing) | none |
| g3q_p2f vs g3q_s0 | yes | none | none | **none (identical multisets)** | none |
| g3q_p2fc vs g3q_s0 | yes | the 3 C1 templates: 1 / 1 / 16 | none | 2 Toypad frame counts | none |
| g3q_s0 vs s4b01 (harness vs vpad route, both all OFF) | no | none | none | Toypad, XAM, INSTALL0 probe counts, and the SDL lines (input backend) | none |

## 5. Per-arm conclusion

The timed W6 runs use the same harness as the G3-quick run, are longer (5 s settle + 55 s warm-up + 50 s window; cold run 55+30), have no input, and run on the user's desktop.

| arm | must have, in every run | must not have | expected to vary | evidence | confidence |
|---|---|---|---|---|---|
| s0 | No switch line exists. As a log-integrity anchor only: `Reserving the guest memory arena` (once). | any `C1 keep-watch:`, any `C1 verify`, `S4 upload hash:`, `slow frame #`, `memexport flush reasons`, plus forbid_all | Toypad frame counts; warnings should stay 40 (0 err/crit) on the attract/harness route | g3q_s0, s4b01, s4bL0 | high |
| p2 | the same as s0 (P2 has no line) | the same as s0 | the same | g3q_p2 (vs s0: Toypad counts only); source | high |
| p2f | the same as s0 (fix (i) has no line) | the same as s0 | the same | g3q_p2f (identical to s0), side1, p2fiL; source | high |
| p2fc | `C1 keep-watch: on (with physical_protect_hold_global_lock)` (exactly 1, line before `Reserving the guest memory arena...`) and `C1 keep-watch: first kept protect at` (exactly 1; so far always `ED19F000, 299892736 bytes`, before the first frame) | any `C1 verify`; `C1 keep-watch: on, but` (hold-off or blocked variants); `C1 keep-watch: blocked`; the extra-switch lines; forbid_all | `C1 keep-watch: N protects kept so far`: present in 3/3 runs, but the count grows with run time. Expect about 20 lines in a ~135 s timed run, at roughly 270–350 kept/s in title/attract. Toypad counts vary. | g3q_p2fc, side2, gateA (+verify); source | high |
| f | the same as s0/p2f (fix (i) alone has no line; keep_watch is off, so no C1 line at all) | the same as s0 | the same as s0 | **no run.** Source plus p2f, since P2 adds no line. | high (derived) |
| fc | the same as p2fc: the init line (it depends only on the two latched cvars, xmemory.cpp:161-176) and `first kept protect at` | the same as p2fc | `protects kept so far` count | **no run.** Source: whether a protect is kept is decided in PhysicalHeap::Protect/ProtectKeepWatch (hold latch, keep latch, guards, data providers). P2 is not an input; it only adds recursive holds of G in RangeWrittenByGpu/MakeRangeValid. The first kept protect happens at module launch, before GPU-written data exists, so the SharedMemory guard allows it either way. | init line high; first kept protect high but not measured |

## 6. The matrix claims, checked

1. "Every p2fc and fc game.log needs 'C1 keep-watch: on (with physical_protect_hold_global_lock)' and 'C1 keep-watch: first kept protect at'": **true for p2fc** (3/3). **Derived for fc.**
2. "…must have no 'C1 verify: on'": **true.** The only print site is KeepWatchVerifyRecord, which runs only with verify=true. I suggest the broader pattern `C1 verify` (no colon), which also catches the `C1 verify K|F:` warnings, although those can't appear without the "on" line.
3. "No arm may log stale / unhandled / PhysicalHeap::Protect failed": 0 in all 10 runs. These are failure-only lines (source rows above).
4. "P2 and fix (i) print no line of their own": **true** (source and logs).
5. "p2fc's init line also shows that fix (i) is ON": **true.** :174 needs both latches; with hold off the :171 WARN variant prints instead.
6. The p2 note, "Timed only if P2's full-buffer counter totals 0 in the untimed runs (G4)": **total 0** on every slow-frame line of gate A, side 1, side 2 and p2fi-level. The counter is only visible through `slow_frame_log_ms`.
7. The note that "kInitOnly latches keep_watch and hold_global_lock; verify and every other cvar are read live" matches the source: verify :381, P2 :314/:352, hash log :539, slow_frame_log_ms per swap.

## 7. Caveats and open questions

- Side 1 and side 2 have **no all-OFF reference on their route** (attract, no input). Diffs vs s4b01 mix in route and input-backend differences. The clean C1 isolation is side2 vs side1, and P2/fix (i) are isolated by g3q p2/p2f vs g3q s0.
- s4b01 and p2fiL ran **capped at 60 fps** (no `framerate_limit=0`). This doesn't change which switch lines appear.
- Gate A stopped at step 104/119 and had no in-level ToyPad light traffic. It ran at 12–20 fps even in title/menus, against ~60 fps capped for p2fi-level and ~135 fps for side 2. This only shows what the logs and summary say; I did not check whether verify hashing is the cause. Its STUCK-LOCK is class (d), left to Agent 6.
- f and fc are derived, not measured. If the decision table picks s0,f,fc, one G3-quick f/fc pass would confirm `first kept protect at` without P2.
- The forbid_all additions beyond the matrix's G10 (`BaseHeap::Protect failed`, `STUCK-LOCK`, `Minidump written to`) are my suggestions. Drop them if a hang should not invalidate a timed run.
- Level totals (warning/error/critical) must be counted on the `[level]` token of the full line. The JSON patterns are message substrings.
- `20261122-214221-s4b-07-c1v-level` was in progress and is not included. Side 3 does not exist yet.
