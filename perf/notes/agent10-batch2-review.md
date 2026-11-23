# Agent 10: batch-2 safety review (task #25, rolling)

**Scope.** Every batch-2 change, rated at its defaults: SAFE, SAFE-IF (condition stated) or UNSAFE (must go behind an OFF toggle or out of batch 2). Read-only. I edit nobody's files.

**Base.** snap1 = S1 (20:41:57, the 20:15 batch-1 state) + p1 (Agent 7's perf-csv `device.cpp`, 4C15043E → 4DC63FA0; `build/agent2/snap1/PATCHES-S1.tsv`). Every diff below is live tree vs snap1. They are saved in `build/agent10/b3/`.

**Method.** Read every hunk of the live-vs-snap1 diff. Check the owner's tests; write my own only where a claim is untested. No builds. The only compile check is `env/compile-one.ps1 -SyntaxOnly` (at most 2 threads, never in a quiet window).

## Status

| # | Item | Owner | Live files:lines | Default | Verdict | Sent |
|---|---|---|---|---|---|---|
| 1 | (h) Inline `CurrentDrawPreparation` | A7 (#20) | device.h:93-95; device.cpp:755 | ON (same behaviour) | **SAFE** | 21:48 to 1, 7 |
| 2 | (i) FPS meter: touching cells cleared as one rect | A7 (#20) | fps_counter.h:52-78; device.cpp:2129-2137 | ON (output-identical); `LEGO_NATIVE_FPS_CELL_RECTS=1` restores batch 1 | **SAFE** | 21:48 to 1, 7 |
| 3 | (p) perf.csv rows | A7 (#20) | device.cpp:2275-2276 | ON; no-op without `--perf_log_csv` | **SAFE** | 21:48 to 1, 7 |
| 4 | (c') Gate comment on the window queries | A7 (#20) | device.cpp:1901-1904 | n/a | **SAFE** (comment only) | 21:48 to 1, 7 |
| 5 | Async-PSO patch (`bench/agent6/draw-async.patch`) | A6, applied by A4 | draw.cpp (see §5) | OFF (`LEGO_NATIVE_PSO_ASYNC` unset) | **SAFE** at the default; **SAFE** when ON (was SAFE-IF until 21:58, §5) | 21:48 to 1, 6, 4; ON update 21:59 to 1, 6 |
| 6 | Zero-fill comment | A6 | pipeline_snapshot.h:57-61 | n/a | **SAFE** (comment only) | in the item-5 line |
| 7 | Plume `D3D12_HEAP_TYPE_GPU_UPLOAD` → `static_cast<D3D12_HEAP_TYPE>(5)` as a `prepare_plume.py` patch | A6 (#26) | NEW `tools/gpu-aot/patches/plume-winsdk-compat.patch` (E03D29D0…, 640 B, 22:08:09); `prepare_plume.py` :77 (B3C87737…, 22:08:37); `test_prepare_plume.py` (DA360ABA…, 22:08:39) | n/a (tooling; the compiled plume source stays 564568D4… = S1+p2) | **SAFE** (§7) | 22:33 to 1, 6 |
| 8 | #22 audio-shutdown fix; S3 flips the default ON | A12 | SDK `audio_system.cpp` (C281FA86…, 21:56:43): cvar :47-52, `WorkerControl` :72-101, Setup :140-152, worker :160-270, Shutdown :285-358, `DetachWorker` :362-384; `audio_system.h` (4836B139…, 21:44:35) :61-69 | S2: OFF. S3: ON (`audio_shutdown_detach_worker=true`), live since 02:04 (4331A312…, 02:04:39; the one-line flip at :48) | **SAFE** OFF (equivalent rewrite); **SAFE** ON (condition met 00:08; live diff confirmed 02:17, §8) | 22:15 to 1, 12; ON 02:17 to 1, 12, 6, 2 |
| 9 | Batch 2: legacy-upload toggle, texture staging pool, upload-pool budget; carries Agent 4's (a) in `ResolveFramebuffer` | A5 (and A4 for (a)) | 8 files (§9) | OFF (`LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD`, `LEGO_NATIVE_TEXTURE_STAGING_POOL` unset) | **SAFE** at the default; legacy ON **SAFE**; staging pool ON **SAFE-IF** (§9) | 22:15 to 1, 5, 4 |
| 10 | #27, batch 3: the SDK `exit(0)`/`exit(1)` exits become `FlushLogging` + `std::_Exit` (xboxkrnl_hal.cpp:34, xam_ui.cpp:542), coordinated with A12's #22 | A11 (assigned by Agent 1, 22:01) | staged `build/agent11/exitfix/exitfix.diff` (B2C1FE21…, +19/-6; staged hal :15, :33-41 and xam_ui :12, :542-548). Live since 23:19 (Agent 11 copied the staged files in, `build/agent11/exitfix/apply-2319.txt`); live = staged: xam_ui.cpp 0A314946…, hal AB359E1D… (A12 touched the mtimes at 00:06:15, `touch-0006.txt`, content unchanged). In S3 | always on (no cvar) | **SAFE** (§10). Agent 11's landing checks passed: `check-live-2319.txt` all checks passed, `test-console-2315.txt` RESULT PASS | 22:44 to 1, 11; in the S3 TSV 02:32 to 2, 1 |
| 11 | S3: `pause_safe_order` default ON | A11 (A12 landed it 02:04) | `build/agent11/safeorder/safeorder.diff` (56952876…, -5/+7, rex_app.cpp :71-75, :741-745). Live rex_app.cpp 11DE333F… (02:04:38) = the staged file I rated; S2 has pristine E1569868… | ON; kill switch `--pause_safe_order=false` | **SAFE** (§11); confirmed on the live file 02:17 | 00:12 to 1, 11; live 02:17 to 1, 12, 6, 2 |
| 12 | S3 native startup fix (a): Fix A `fix-a.patch`, plus the optional `fix-a-commit.patch` | A6 (applied 02:05:27 at A1's GO) | `build/agent6/fix-a/` (71AEFF3D…, 50046A3F…): settings_registry.cpp:103-104 (+ :200), settings_preferences.cpp:69-71. Live (02:05:27, CRLF kept): registry 4EC71328… (with the commit hunk), prefs 9CBE6DBF… | always on (no cvar); no-op on FFX builds | **SAFE**; hunks 1 and 2 must ship together. The commit hunk is **SAFE** and recommended (§12). Agent 7's one-line alternative is **NOT SAFE** as written: it breaks Restore defaults | 01:28 to 1, 7; live re-hash 02:17 to 1, 6, 12, 2 |
| 13 | (b) ODR/layout analysis for a native build with the FFX source dir | A7 | `perf-notes/agent7-odr-ffx.md` (9EA96B22…) | parked by A1 (01:20) | **AGREE**: clean in practice, formally an ODR violation. I add S4 hazards 6-7 and a grep guard (§12) | 01:28 to 1, 7 |
| 14 | §S3.2: an early return on the failed vertex bind at the entry of `PrepareDrawGeometry` (draw.cpp:1498), to stop the `hash=0x0` cache-miss spam | A4 | `build/agent4/s32/draw-s32.patch` (F5434325…, +5/-0); draw.cpp 50AA3B1D… → 5EA1F357… (306,557 B) | native only (draw.cpp isn't compiled OFF) | **SAFE** (§13): the draws that reach the GPU don't change | 03:32 to 1, 2, 4; native3d n-rows PASS (§13 "After the apply") 05:04 to 1, 4, 2, 8 |
| 15 | S4 candidate `timer_queue_precise_wait`: high-resolution sleeps for the last 20 ms before each timer deadline | A11 | staged `build/agent11/timerq/stage/timer_queue.cpp` (015C04A22DACC592…, 16,091 B); `timerq.diff` (D07A2DC4878DAE8D…, -6/+73). Live = pristine D8724B29C43286B0… | OFF (`timer_queue_precise_wait=false`, kInitOnly) | **SAFE** as a default-off candidate (§14). Flipping the default needs caveat (a) handled and a game timing A/B | 05:23 to 11, cc 1 |
| 16 | Agent 7's top 3 S4 native candidates (first read only): 1a AOT fix for the missing placement shaders, 1b `LEGO_NATIVE_SHADER_MISS_CACHE=1`, 2 Main walk probe, 3 `LEGO_NATIVE_THREADED=1` | A7 (code owners A4, A6) | shaders.cpp, shader_archive.cpp, draw.cpp (read in the live tree; nothing staged) | 1a: data change; 1b: OFF; 2: compiled out; 3: OFF | First read (§15): 1a is not output-identical by design (gate it as a content fix with the user's visual check); 1b is output-identical only under conditions 1-7; 2 is a diagnostic only; 3 is covered by item 2's n2/n3 rows, plus proofs 2-5 | 04:53 to 1, 7, 4 |
| 17 | S4 candidate `host_execution_throttling_optout`: opt out of EcoQoS execution-speed throttling at startup | A11 | staged `build/agent11/pthrottle/stage/` (diff 75756E8DCB045A91…, −4/+37, 7 hunks): threading_timing.h, threading_win.cpp, runtime.cpp. Live = pristine (043FFE28…, C0EBD864…, 306B692B…) | OFF (`host_execution_throttling_optout=false`) | **SAFE** as a default-off candidate (§16). A default flip needs the hidden-desktop pair | 05:23 to 11, cc 1 |
| 18 | Agent 7's S4 designs: R1 stage 1, split submits at N KB through the existing `EndSubmission(false)` (`d3d12_submit_split_kb`, 0 = off); R2, a redundant-command filter in `DeferredCommandList` | A7 (Task #22 §4) | design only, nothing staged: SDK command_processor.cpp (:98, :2556-2561, :4122-4154, :4199-4326 checked), deferred_command_list.{h,cpp} | OFF | R1 stage 1 **SAFE** as a default-off test bed under conditions 1-6 (no win alone); R2 step 1 **SAFE**, step 2 **SAFE-IF** (a)-(e) (§17) | in the ~07:30 summary to 1, cc 7 |
| 19 | §S3.4 miss-cache stopgap `LEGO_NATIVE_SHADER_MISS_CACHE=1`: remember a placement-shader AOT miss behind a CPU write stamp, then replay it with the same warning | A4 | staged `build/agent4/s34/shaders-s34.patch` (328BDAE19ABFC6C8…, 14,441 B): shaders.cpp E87A2DEE… → 9567FE3F… (new block L209-410; AdoptShader L487-514; L929, L962-987, L1012, L1123). Live = pristine E87A2DEE… | OFF (env var unset; forced off under `LEGO_DUMP_MISSING_SHADERS`) | **SAFE** at the default. ON is output-identical under §15.2 1-8 (all met), apart from a protect-only log residual and up to 64 insert probes (§18, addendum 06:18: Agent 4's 3 asks answered) | 06:18 to 4, cc 1 |
| 20 | Agent 12's S4.7: upstream race in `PhysicalHeap::Protect` (G is released between TriggerCallbacks and the host protects) | A12 (S4.7) | SDK xmemory.cpp L2128-2144 (Protect), L1713-1799, L930-979, L2157-2271 (EAC), L2273-2430 (TriggerCallbacks); base shared_memory.cpp L303-336, L426-476 | n/a (upstream code, nothing staged) | **CONFIRMED** (§19). Form 1 (RW→RW) is a real race; its stale state lasts until the next TriggerCallbacks over the page. Form 2 (RO/NoAccess→RW) needs no race (pre-existing gap). Fix (i), G held across both host protects, closes form 1; (ii) alone doesn't. Both are correctness fixes, not output-identical | 06:43 to 1, 12, 5 |
| 21 | Agent 12's #27 S4 "u" diagnostic `shared_memory_upload_hash_log`: hash each uploaded page against its previous upload, one info line per frame | A12 (#27) | staged `build/agent12/s4-diag/upload-hash-log.diff` (D2905301…, 7,629 B, +145/-0, 4 hunks): d3d12/shared_memory.cpp → BB0838CE… (= `new/`, checked). Live = pristine B120D07C… | OFF (`shared_memory_upload_hash_log=false`, kHotReload) | **SAFE** at the default: no original line changed; one load and one untaken branch per upload call. ON: **SAFE** for functional runs, with no GPU-visible effect; +1-3 ms/f on GPU Commands, so no timing arms (§20) | 06:43 to 12, 1 |
| 22 | C1 = P1 `physical_protect_keep_watch`: keep the watches on protects that don't change access (a fast path at the top of `PhysicalHeap::Protect`) | A5 (#20 S4.5 C1) and A12 (S4.4 P1) | design only, nothing staged: SDK xmemory.cpp L560-582, L2128-2144, L2157-2271, L2273-2430; shared_memory.cpp L303-336, L502-575; primitive_processor.cpp L1351-1367, L1435-1440; xboxkrnl_memory.cpp L270-282, L484-503; base command_processor.cpp :315, :437, :1289, :1305, :1368 | OFF (`physical_protect_keep_watch=false`) | **SAFE** at the default. ON: output-identical under conditions 1-4 on devoff, apart from residual R1 (a §19 form-1 state no longer heals at the next lock) and the bypass writers, which only an ON run can clear. Flip ON only with A-D (§21) | 06:52 to 5, 12, cc 1 |
| 23 | Agent 12's S4 P2 `shared_memory_single_hold_rearm`: hold G once across a range's valid-bit update and its write-watch re-arm | A12 (#27 item 4) | staged `build/agent12/s4-p2/single-hold-rearm.diff` (77BEB64E…, 2,853 B, +30/-0, 3 hunks): base `src/graphics/shared_memory.cpp` 15C89EDB… (label corrected 07:55; it said "d3d12") → 0BE4BADC… (= `new/`; regenerated hunk for hunk). Live = pristine 15C89EDB… | OFF (`shared_memory_single_hold_rearm=false`) | **SAFE** at the default. ON: output-identical; no new lock edge and no `unlock()` under the hold. Caveat: the memexport full-buffer fallback (command_processor.cpp:3063) becomes one long G hold, ~3× today's longest; confirm it doesn't run, or cap one hold's length (§22). Fix (i) item 4 is queued for S4 | ~07:35 to 12, cc 1 |
| 24 | Agent 12's S4.7 fix (i) `physical_protect_hold_global_lock`: hold G across both host protects of a write protect in `PhysicalHeap::Protect` | A12 (#27 follow-up) | staged `build/agent12/s4-fixi/protect-hold-g.diff` (80CAD795…, 2,098 B, +19/-0, 2 hunks): xmemory.cpp 6E8FA1BA… → 141FB1A9… (= `new/` = C1's base; diff body re-derived equal). Live = pristine 6E8FA1BA… | OFF (`physical_protect_hold_global_lock=false`) | **SAFE** at the default. ON: **SAFE**, a correctness fix, not output-identical by design; no new lock edge. Item 4 PASS: no heap_mutex_ → G path. NOTE.md's "G first" wording is wrong on Windows (the reconcile lock is empty), and Alloc* nest view → parent without G, so C1 may nest only view → parent. ON only with C1 (§21 gate B) (§23) | ~08:09 to 12 (with §24) |
| 25 | Agent 12's S4 C1 `physical_protect_keep_watch`, as staged: keep the write watches on write protects that change no page's access (a fast path after fix (i)'s hold in `PhysicalHeap::Protect`), plus verify mode and a native latch | A12 (#31, from A5's #28) | staged `build/agent12/s4-c1/keep-watch.diff` (1B2BA4E3…, +362/-3, 19 hunks: xmemory.cpp/.h, shared_memory.cpp/.h, primitive_processor.cpp) and `keep-watch-rexlego.diff` (4D0C1079…, +6/-0, memory_watch.cpp). Bases: fix (i) `new/` 141FB1A9…, P2 `new/` 0BE4BADC…, the rest live. Every hash and orig → new body re-derived equal; the one-input chain `--check` exits 0 (HASHES' FAIL is a method artifact); syntax PASS (A12 07:54, 8 compiles, no new diagnostics) | OFF (`physical_protect_keep_watch=false`; `…_verify=false`, kRequiresRestart) | **SAFE** at the default. ON: **SAFE to test**. §21 conditions 1-4 met; guards run before the heap mutexes; no heap-mutex nesting; no lock edge beyond fix (i)'s. Gates B (enforced in code) and C (static latch) met. A is provided, with a blind spot: a bypass write after a kept lock shows only at the next lock or fault. D needs a kept-protect counter, which is also A's positive control. Agent 12's open items: the native fingerprint changes once (re-pin the native baselines); R2 is recovered by the AV path; E1 goes the safe direction; verify's K → normal path is safe but masks, so A is read from the K/F lines. Before landing: chain-order apply, full rebuild (new header members) (§24) | ~08:09 to 12 |
| 26 | Check of Agent 11's S4 draft plan: every item's rating and gate against rows 1-25 and §5-§24 | A11 (#30, #35) | `perf-notes/S4-DRAFT.md` (61,318 B, 07:58:42; copy `build/agent10/s4/S4-DRAFT-snap1.md`, CA69EB1F5482…) | n/a | Ratings **match** my notes, except C1 (#4), rated after the draft (§24). Gate corrections: C1 needs #5 ON (enforced in code, so "or R1 accepted" no longer applies); W6 needs a #8 + #5 arm so C1 is timed with fix (i) ON in both arms; P2's memexport count needs a counter that no staged diff has; the timer log line is `TimerQueue: precise wait`. No UNSAFE (§25). Agent 1 (~08:25): P2 ON in S4a needs that counter (~+4 lines; A12 stages it after window 4); I rate it when staged (§25 addendum) | ~08:15 to 11 |
| 27 | Agent 9's GPU-wait back-off, stage 1 (S4-DRAFT #24), merged with Agent 6's GetData-poll back-off and probe P1: H0 `sub_83FBF7D0` and H1 `sub_83FAF180` (L1, the fence wait), H2 `sub_83FB09E8` (L2, the query poll; gated on lr 0x82BDD028 and result 1; Xenos only), H3 `sub_83FC0C10` (STATS-only kick counter) | A9 (#32), A6 | draft `build/agent9/s4/fence-wait/gpu_wait_backoff.cpp.draft` (D176CA8D…, 16,485 B, 07:44:53; not compiled; unchanged at 12:34) + a `CMakeLists.txt` block before :168 inside `if(NOT LEGODIMENSIONS_NATIVE_GPU)` (define `LEGO_GPU_WAIT_HOOK_GETDATA=1`) | OFF (`LEGO_GPU_WAIT_BACKOFF_US` and `LEGO_GPU_WAIT_STATS` unset) | **SAFE** at the default. ON: **SAFE to test**, output-identical by construction: no guest writes, and only the next poll's time changes. L1's only time input, KTHREAD+0x58, is never written; L2 has no timeout. a9 S5.2.5 items 1-7 PASS against the A tree (`.429.cpp:7933-7958`, `.248.cpp:35234-35251`, `.107.cpp:36789-36868`) and B's pch. Risk: wake latency ≤ Q + timer slack; lock holds up to Q longer per stalled wait, with no new lock edge. Nits N1-N4 (N2: the map check must include H3, 27 → 31 hooked aliases). **Landing OFF: SAFE** once a9 S5.2.4 step 0 is done: grants, a syntax compile, and a batch-nolr build with skip_lr off plus the map check. The CMake edit changes the native fingerprint once. **Before ON** (steps 1-4): P1's positive controls (l2_tries > 0), the functional pair, and the sweep plus Agent 6's arm with sleep_fail == 0. Draft #25 and the fallback: not rated (§26) | ~08:28 to 9, 6, 11, lost in the 08:29 reboot; re-sent ~12:45 to 9, 6, 11 |
| 28 | Agent 6's warm-boot pipeline fix (S4-DRAFT #32; a6 attract-stalls §10.2 (b)): the loop at `pipeline_cache.cpp:564` compares with `creation_thread_original_count`, so storage init never starts its extra creation threads; the fix compares with `creation_thread_needed_count` | A6 | SDK `src/graphics/d3d12/pipeline_cache.cpp:564` (1 line). Live 5DBED81F611E25B1 (161,305 B, 11-21 11:06); the same line is in the baseline. Nothing staged. **Landed** with S4a at 14:56 (SDK 3bb65bb, game 1bd322e): live is now DA77744302CFC149 (161,303 B), the S4a snap1 file | no switch proposed; the path runs only on warm boots (stored pipelines) | **Output-identical** (timing only, as for #24): the same PSOs from the same descriptions, and the same log lines (only the "Created N … in X ms" value changes). ON's output is one an OFF run can produce (the tail finished before the first draw): in async mode it can remove a first-submission skip, never add one. **SAFE**: the handshake reads sound (no lost wakeup; the queue is empty at shutdown; the join and the wait mirror Shutdown() and EndSubmission). So it may ship **without a switch** (Agent 1's 07:48 rule). The block it turns on (:685-715) has never run here, so Agent 6's §10.2 runs 1-4 come before landing. Re-take warm-boot baselines taken without it (#36). #33 is independent (§27). **Gate PASS** (a6 §10.2.1, 14:55): line check, R1, run 2 (logdiff NEW 0 / MORE 0 / marker flags 0; the 33 GONE lines are info-level Toypad packets, timing noise), run 3 (5 of 5), run 4 (Created 6,516 → 1,191 ms, 5.5×) and F1t; every join and wait finished, no leaked threads. The rating stands (§27 Results) | ~12:45 to 11, 6; gate note ~14:56 to 6, 1; results ~15:45 (task #23) |
| 29 | C1 (#4) staged code, re-checked for the S4 queue: its place after fix (i)'s second acquire, view → parent only, §21 A-D, P2's long hold, and `chain-live-to-c1.diff` | A12 (Agent 1's task #12 item 2) | `build/agent12/s4-c1/`, unchanged since 07:59: keep-watch.diff 1B2BA4E3…, keep-watch-rexlego.diff 4D0C1079…, chain-live-to-c1.diff 1D2CC1F3… (37,746 B), NOTE.md, `syntax-20261122-075428.txt` (PASS). Live = pristine | OFF (`physical_protect_keep_watch=false`, `…_verify=false`) | **SAFE** at the default; ON **SAFE to test** once D has a kept-protect counter (§24 unchanged). The chain, applied in memory to the live SDK, reproduces all 6 staged files byte for byte (= #7 + #8 + #5 + C1). The fast path sits after fix (i)'s second acquire (new xmemory.cpp :2222-2234). The heap mutexes are never nested (:2336-2341; one scope each, :1863). C1 doesn't lengthen P2's hold, except in verify mode. A is provided (with a blind spot), B is enforced in code, C is met, D needs the counter. After S4a, apply keep-watch.diff, not the chain (§28) | ~13:20 to 12, 1 |
| 30 | Agent 2's S4a apply record: the before/after hashes of S4a's 6 rows against the rated diffs (#7, #8, #5, #38, #32; #2 native only) | A2 (Agent 1's task #12 item 1) | `build/agent2/s4a/` (HASHES.txt D9BEA59D…; real apply `work-132457` = dry run `work-132122`; `pc-warmboot.diff` 080122DD…); `snap1/PATCHES-S4a.tsv` B9612DA2…; tree `build/agent2/snap1/DimensionsRecomp`, backup `snap1-backup-S4a`. Live untouched | #7, #8, #5, #38: OFF (4 cvars, all default false); #32: always on; #2: native only, env var unset | **ALL PASS** (§29). Every before = live = the rated base, and every after = snap1 = my strict in-memory apply of the rated diff. #32 is exactly the L564 change (`original` → `needed`). verify-off PASS (23,843 files, 0 problems). keep-watch.diff applies to S4a snap1 byte for byte (C1's base confirmed). Its rexlego part must keep CRLF (memory_watch.cpp → 70829846…) | ~13:42 to 2, 1 |
| 31 | Agent 12's P2 memexport full-buffer counter: counts IssueDraw's `RangeWrittenByGpu(0, kBufferSize)` fallback draws and shows them on the slow-frame line (§25 item 4) | A12 (#13 step 3) | staged `build/agent12/s4-p2c/` (diff 29E02E24…, 2,998 B, +12/-2, 5 hunks): d3d12/command_processor.cpp 3AB3AA53… → 474C1CBA… (= `new/`, re-derived). Live = S4a = pristine for this file | always on (no switch); visible only with `slow_frame_log_ms` > 0 | **Output-identical** and **SAFE**; no switch needed (§30). Syntax PASS, no new diagnostics. For the next build, not S4a. It commutes with s4-r1r2 (same file, either order). P2 ON needs `total` from a next-build run: 0 closes §22's caveat; > 0 goes to Agent 1 | ~13:42 to 12, 1 |
| 32 | Agent 7's S4 #18 R1 stage 1, `d3d12_submit_split_kb` (end the submission at an IssueDraw/IssueCopy tail once the deferred list reaches N KB), and #20 step 1, the R2 deferred-command counters (`REX_D3D12_DEFERRED_COUNTERS`) | A7 (Agent 1's task #12 item 4; A7's task #9) | staged `build/agent7/s4-r1r2/` (13:24, NOTE 13:34; re-staged 14:01 with my dcl.cpp comment nit fixed, HASHES.txt 3B8DA461…): r1-split.diff 2516F199… (cp.h, cp.cpp, dcl.h; unchanged), r2-counters.diff 51999104… (dcl.cpp; was A8BE5FCB…), s4-r1r2.diff **BD0C4A93…** (both; was 12182A4C…). `orig/` = live (cp.cpp 3AB3AA53…, dcl.cpp FFDF7FB6…, cp.h 41F32B80…, dcl.h DA2F58B6…); all three diffs re-derived = `new/` at offsets 0 (again at 14:08 on the final files; the nit changed 3 comment lines only). Syntax **PASS** (9 units, 18 compiles, exit 0, no new diagnostics; dcl.cpp re-run on the final file) | R1: OFF (`d3d12_submit_split_kb=0`, kInitOnly); R2: compiled out (macro 0) | **R1 stage 1: SAFE** at the default (one compare per draw and per successful resolve; IssueCopy returns the same value). ON: **SAFE to test**, as a test bed (a small cost expected). §17 conditions 1-6 met. The hold order (query, scratch, pipelines) only decides which counter is charged, and each hold is needed. A failed EndSubmission only counts: its one `return false` comes before any state change. **R2 step 1: SAFE** (OFF = today's Execute); (a)-(d) hold, (d) by design. Confirmed for S4b: s4-r1r2.diff BD0C4A93446149BB. Before landing: a full SDK rebuild (cp.h layout). Commutes with p2c (027204B5…, also with the final diff) (§31 + addendum) | ~13:54 to 7, 1; addendum ~14:15 to 7, 1, 2 |
| 33 | Agent 9's N1-N4 fixes to the #24 GPU-wait back-off (row 27, §26) and step 0's syntax compile | A9 (Agent 1's task #12 item 5) | `build/agent9/s4/fence-wait/`: draft 01D9F8F3… (18,177 B, 395 lines; rated copy D176CA8D…), `gpu_wait_backoff.n1-n4.diff` 803B8382… (13:33), `syntax/gpu_wait_backoff.cpp` = draft, `syntax-20261122-132450.txt` (PASS) | OFF (env vars unset) | **N1-N4 fixed** as asked, with no other code change (10 hunks). Syntax **PASS**: B's exact devoffB flags and pch, both define variants, no new diagnostics; the -E positive control shows H0-H3 with the GetData define and H0-H1 without. §26 stands: **landing OFF SAFE** once the rest of step 0 is done (grants, then the batch-nolr build with skip_lr off and the map check expecting 31 aliases); ON **SAFE to test** after steps 1-4. The STATS line gains `sleep_sum` before `sleep_fail`, so parse it by field name (§32). The S4c package (this file plus its CMake block) is rated in row 38, §37 | ~13:54 to 9, 1 |
| 34 | Agent 5's M1 `shared_memory_upload_nontemporal_copy`: UploadRanges copies into the upload buffer with SSE2 streaming stores and one sfence | A5 (Agent 1's task #12 item 6) | staged `build/agent5/s4-m1/` (13:28): m1-nontemporal-copy.diff EBECE86E… (5,589 B, +72/-3, 5 hunks): d3d12/shared_memory.cpp BB0838CE… (#7's `new/` = S4a snap1) → 2A5ADF13… (= `new/`, re-derived). Live = pristine B120D07C…, so it applies only after S4a. Syntax PASS (13:20, no new diagnostics) | OFF (`shared_memory_upload_nontemporal_copy=false`) | **SAFE** at the default: one cvar read per UploadRanges call, and the copy is the original memcpy. ON: **output-identical** (the same bytes in the same order, fenced before the copy command is recorded) and **SAFE to test**. Before ON: build Agent 5's microbench `bench/agent5/m1_copybench.cpp` (AA313906…) and run it without `--skip-check`. Its RunCheck already has the head/tail sweep (the game's 4 KB-aligned ranges never run those paths), and its helper is the diff's, line for line. A pass is exit 0. Then the OFF/ON functional pair. The timing gain is a hypothesis until measured. M1 now follows C1 (Agent 5, 13:54: ~0.2-0.3 ms/f bound after C1). If P3 (#9) lands first, M1 needs a rebase (§33 + addendum) | ~13:54 to 5, 1; addendum ~14:10 to 5, 1 |
| 35 | Agent 12's C1 v2 interdiff (v1 → v2): a kept-protect counter with log lines (gate D), a once-only native "blocked" line, an init line, and kInitOnly on both cvars | A12 (Agent 1's task #12, after item 6; C1 needs an A/B, so this comes before S4b) | staged `build/agent12/s4-c1v2/` (13:49): v1-to-v2.diff CE5D9DAE… (4,770 B, 5 hunks, +43/-3; SDK xmemory.cpp only, v1 6C801EB2… → v2 DC23757A…), keep-watch-v2.diff 418D3D39… (S4a → C1 v2; replaces keep-watch.diff), keep-watch-rexlego.diff 4D0C1079… (v1's, unchanged), chain-live-to-c1v2.diff DC882A51…, NOTE.md BCD4A96C…, `syntax-20261122-134952.txt` (PASS). All re-derived at offsets 0. Live = pristine | OFF (`physical_protect_keep_watch=false`); it and `physical_protect_hold_global_lock` are now kInitOnly | **SAFE** at the default: v1's path (the new calls sit only on the ON branch), plus one cvar read at init. The only visible change: both entries are read-only in the overlay (settings_overlay.cpp :531). **Gate D is met** (the kept count and its lines; also A's positive control; native shows "blocked" and no "kept"). ON: **SAFE to test** (§24/§28 without the counter condition). kInitOnly is enforced only in the overlay: nothing calls FinalizeInit, so the dev console (console_overlay.cpp :221) can still flip both. Test rule: set both at launch, never mid-run. Before default-ON or landing beyond tests: Agent 12's init latch (§34) | ~14:10 to 12, 1, 5 |
| 36 | Agent 12's C1 v3 interdiff (v2 → v3): the init latch asked for in §34 (Memory::Initialize reads both cvars once; Protect reads only the latched copies), plus nit 2 (a load before the logged-once exchange) | A12 (Agent 1, 14:28: rate it before #26; if it is SAFE before the S4b build starts, S4b takes v3) | staged `build/agent12/s4-c1v3/` (14:22): v2-to-v3.diff 1FC8E2DC… (4,747 B, 6 hunks, +24/-6; SDK xmemory.cpp only, v2 DC23757A… → v3 BCA5E1CF…), keep-watch-v3.diff DECCFE33… (S4a → C1 v3; replaces keep-watch-v2.diff), keep-watch-rexlego.diff 4D0C1079… (v1's, unchanged), chain-live-to-c1v3.diff 0E61E1D0…, NOTE.md 9C9DCDCF…, `syntax-20261122-142307.txt` (PASS). All re-derived at offsets 0. Live = pristine | OFF (`physical_protect_keep_watch=false`; both cvars stay kInitOnly) | **SAFE** at the default: v2's path and log. Protect's two cvar reads become relaxed latch loads, and init does one more cvar read. ON: **SAFE to test**, the same as v2 when set at launch. The latches are stored after every launch source (cvar::Init, both LoadConfig calls) and before any heap exists. The only `REXCVAR_GET`s left are Initialize's two, so a mid-run console set no longer reaches Protect. My §34 condition is met: **fit for S4b in place of v2** (keep-watch-v3.diff DECCFE3373C27C3C at the same step, then the unchanged rexlego diff). Default-ON or landing beyond tests comes after the ON tests (§35) | ~14:45 to 12, 1, 2 |
| 37 | Agent 9's S4 #26: codegen option `db16cyc_pause` (default OFF), which makes each Xenon `db16cyc` emit `simde_mm_pause();` (x86 PAUSE) | A9 (staged under A9's task #17; rated after C1 v3) | staged `build/agent9/s4/spin/db16cyc-pause/` (14:15-14:22): db16cyc-pause.diff AC554DBB… (1,969 B; config.h +1, config.cpp +2, builders/system.cpp +6/-2; base = live = snap1 for all 3), toml-db16cyc-pause-A.diff 95D901B9… (live = snap1 config 7F775847… → 11707872…), toml-db16cyc-pause-B.diff 5D5892D3… (snapB = batch-nolr config E60EAF1C… → FFC119BF…), `syntax-20261122-141452.txt` (PASS). All re-derived at offsets 0 | OFF (no toml line; `db16cycPause=false`) | **Landing OFF: SAFE**. It changes the codegen tool only. With no toml line nothing new is emitted, and the option is in neither FingerprintModule's flags nor config_flags. So the regen is skipped, and a forced one writes identical files. ON: **output-identical** (PAUSE has no architectural effect) and **SAFE to test**. My census matches Agent 9's: 20 sites in 10 functions, in the 10 A TUs and 10 B TUs he listed, and no `simde_mm_pause` today. sub_83FAF180 (8 sites) is the back-off step of 6 GPU-progress poll loops. Gates: the toml line and the new tool in one build; exactly 20 in the arm's 10 TUs after the regen; keep codegen.partition.json; the functional pair plus a frame-time A/B, measured apart from #24 (§36) | ~14:45 to 9, 1 |
| 38 | Agent 9's #24 S4c package: the GPU-wait back-off TU and its CMake block, plus #30's CMake option, as an incremental S4c on top of S4b | A9 (A9's task #22; Agent 1's task #23 item 2) | staged `build/agent9/s4/fence-wait/s4c/` (15:52-15:59; HASHES.txt 0489BC9F…): primary `s4c-24-30.diff` DC02104E… (+417/-0: `rexlego/CMakeLists.txt` +22 in two CRLF blocks, #30's after base :155 and #24's after :167, plus the new `rexlego/src/gpu_wait_backoff.cpp` = the rated draft 01D9F8F3…); fallback `s4c-24-only.diff` A279DC71… (the #24 block only, CMake +9). Base CMakeLists 3690D5D7… = live = snap1 = snapB, and no S4b diff touches it; results 1BF46D78… (907 lines) and 9A4606A7… (894). Syntax PASS (15:52, S4a devoff4 flags). All re-derived at offsets 0 | OFF (`LEGO_GPU_WAIT_BACKOFF_US` unset; `LEGODIMENSIONS_SCENE_WALK_PROBE=OFF`) | **Landing OFF: SAFE**, both diffs. Output-identical at the default: with the env vars unset every hook calls `__imp__` at once and nothing is logged, and #30 OFF is one cache option. Xenos gains one TU and a relink. Native gains no TU, but the CMake edit changes its fingerprint, so `native_gpu_build_info.h` is rewritten and device.cpp, shader_archive.cpp and pipeline_library.cpp recompile (PACKAGE.md says "nothing new compiles"). Before landing: the grants; Agent 2's S4b-then-S4c build; the map gate, exactly 4 more hooked aliases than the S4b devoff map (27 → 31), checked by name and object, not by address or TU number; one native re-pin after the last fingerprint change. Accept the TU as 01D9F8F3… (LF) or 34D281E0… (CRLF, from an in-repo apply). #30 ON is not rateable (no probe sources). #24 ON: §26 items 4-6, unchanged, measured apart from #26 (§37) | ~16:20 to 9, 1 |
| 39 | Agent 2's folded S4b + S4c compose check: C1 v3 → M1 → P2c → r1r2 → #26 OFF → S4c, applied to S4a in both P2c/r1r2 orders | A2 (Agent 1's task #9 item 1; old #34) | `build/agent2/s4b-compose-1932-c1v3.txt` (77F0017A…, 12,894 B, 19:32:33) from `s4b-compose-check.py` (D08B74E0…, 17:03:15; `--c1 v3`, S4c `24-30`); scratch `build/agent2/s4b-check/`. The 7 diffs = the rated hashes (DECCFE33…, 4D0C1079…, EBECE86E…, 29E02E24…, BD0C4A93…, AC554DBB…, DC02104E…). Every S4a base (SDK 3bb65bb, game 1bd322e) = live = snap1 | OFF: the five S4b items at their defaults (#26 with no toml line); S4c with the env vars unset and #30 OFF | **PASS: SAFE to build** (§38). 0 FAIL, and re-derived three ways: Agent 2's git apply (both orders), my strict applier and GNU patch (subagent) give the same 16 files (13 SDK, 3 game), each = its rated step's `new/`; cp.cpp 027204B5… in either order. Land memory_watch.cpp as 70829846… (CRLF; plain git apply fails, and plain GNU patch exits 0 but writes the file all-LF, so check the hash or copy the staged file), the TU as 01D9F8F3… or 34D281E0…, and keep the toml at 7F775847… (#26 OFF; the report doesn't check it). r1r2 hunk 3's old side occurs 3 times in cp.cpp; every nearest-match applier picks the right one (the decoys are 1,236+ lines away), so a hand apply must go by line number. Gates: a full SDK + codegen-tool rebuild; the folded devoff map = devoff4's 27 hooked aliases + exactly the 4 #24 hooks = 31, by name and object; one native re-pin; Agent 2's snap1 verify | ~19:45 to 2, 1 |
| 40 | Agent 2's S4b apply and OFF build reports (snap1 = S4a + the 16 files of §38, built into devoff4b-bin), against §38's five gates | A2 (task #9 item 3; optional) | `build/agent2/s4b/HASHES.txt` (B9A450C3…, 16 rows), `prep-s4b-dryrun-1949.txt` (F83C7111…), `prep-s4b-apply-1950.txt` (DCB84EDC…), `snap4b-steps.txt`, `snap4b-sdk-build.log` (E195BB40…) + `snap1-sdk/.ninja_log`, `snap4b-gate.log` (1ECFA68F…), `snap4b-game-gen-check.log` (C5947E8D…), `s4b/checks/tree-check-2007.txt` (B83267F6…), `s4b/checks/w5-rehash-2035.txt` (3AAD2DD3…), `s4b/mapcheck-s4c.py` (F8CB7B49…); `s4b/checks/mapcheck-devoff4b.txt` (20:50:58, PASS); `devoff4b-bin/` (MANIFEST DE11A914…, map 52155274…) against `devoff4-bin/` (map DCC51E2B…); my scratch `t9_map.py` | OFF: every S4b switch at its default, #26 with no toml line, the pinned S1 generated output | **PASS on gates 1, 2, 3, 5** (§39). Files: the 16 = §38's finals (HASHES.txt and my own hash); live untouched; toml 7F775847… with no db16 line. SDK: the rebuild is dependency-complete (225/821 outputs, every includer of the changed headers rebuilt; the install copied the 10 changed files); gen-check 886/886 = baseline. Map: devoff4's 27 hooks + exactly the 4 #24 targets = 31 = expected-map.txt; each target's sub_ in gpu_wait_backoff.cpp.obj and its __imp__ in its devoff4 recomp object (Agent 2's mapcheck and my own parser agree). Bins: devoff4b-bin's 7 files match its MANIFEST (DE11A914…). Checks: verify 0 problems, tree-check only the 16 differences, the W5 bins 27/27 unchanged. Gate 4 (one native re-pin) open; the native build ran 20:53:12-22:39:53 (exit 0) and was staged at 22:40:12 (MANIFEST checks 124 PASS / 0 FAIL; native GPU fingerprint 9b40acbb…; `build/agent2/snap4b-run.txt`) | none; in @@done 9 (~20:58) |
| 41 | Agent 5's overnight launcher (RUN-NIGHT.cmd → run-night.ps1): safety read against P1-P5, the relaxed Defender gate and the hold manager | A5 (Agent 1's task #9 item 2; Agent 11 also reviews, its task #10) | final run-night.ps1 16B90FA8… (77,594 B, 1017 lines), README.md 0058C8F6… (271 lines), RUN-NIGHT.cmd D7A0362B… (1,197 B, 19 lines); earlier 00BFECD7…/924321AE…/163D7659…/3EFC5312…/B0902106…; hold-manager.ps1 D060F913…; ENV-KEYS-F1.txt D1AE6D57…; Agent 5's summary-go/-gate/-hold/-run and send-ctrlc.ps1; my scratch t9_param.ps1 + t9_lock.ps1; subagent B's second reads | REAL mode: the user double-clicks RUN-NIGHT.cmd at ~23:45 (no args); test hooks only with -DryRun | **SAFE** (§40). P1-P5 PASS; relaxed gate PASS; fix 2 consistent with the hold manager; fixes 1-11 and F1/F3 done: no taskkill /T (checked walk + Stop-One), the 3-name driver list, the build check in the last checks, the 07:30 hard stop (GraceMinutes 0). Agent 5's tests on 16B90FA8: go 16/16, gate 12/13 (t-relaxed: a load-timing miss of the test; PASS on B0902106 and in a solo re-run on 16B90FA8 at 22:28; gate code unchanged), hold 4/4, run 5/5 (STOP, the end time, a launcher error and Ctrl+C each kill the fake runner and its child); after the rating, pin 2/2 and a STOP-file smoke test of RUN-NIGHT.cmd (22:34: refused, exit 2). Optional: README L179/L182 overstate the walk's retry; one handle in Stop-One and the sweep; the try right after Start-Process | ~22:33 to 5, 1, 11 |
| 42 | Agent 3's G5: W6 gate A (w6gA), C1 + verify on devoff4b, with row 7 (s4b07) as extra data | A3 (asked 21:59; task #9, extra) | `build/agent3/s4b/logs/w6gA.check.txt` (30,076 B, 21:19:38) for `20261122-210906-w6-gateA-p2fcv-level` (devoff4b-bin, L route, 600 s; P2 + fix (i) + C1 + verify); `s4b07.check.txt` (14,440 B, 21:54:56) for `20261122-214221-s4b-07-c1v-level` (fix (i) + C1 + verify, no P2); Agent 12's row 7 reads (~22:15 game.log; 22:31 `build/agent12/s4-c1v3/new/sdk/src/graphics/shared_memory.cpp`); subagent B's check (22:44) of shared_memory.cpp A4A31038… and xmemory.cpp BCA5E1CF… | C1, P2 and verify OFF by default; G5 runs are functional only (verify is several times slower) | **G5 PASS, partial coverage** (§41). Gate A: C1 init x1, the first kept protect logged, kept 2 → 32768, verify on, K 0, F 0, P2c 0; 104/119 steps (the 600 s cap hit at story-load), so §21 A stays open for the level load. Fine for W6 (every C1 arm is p2fc). Before C1 default-ON: a p2fc + verify run that reaches the level with 3/3 tag loads (s4bLV with the fixed sidecar; Agent 1's condition, 22:46). Its STUCK-LOCK x5 is finding 10 (WARN, outside G5). Row 7 has fix (i) and lacks P2 (Agent 3's label corrected). Its F 92 fit a race in the verify check when P2 is off (Agent 12's code read, confirmed by subagent B; the F check can't tell race from real, so some could still be real misses), so C1 without P2 is unverified, not failed; C1 ships only as p2fc until s4bV0 (C1 off) or a verify-only fix settles it | ~22:07 to 3, 1, 12, 8 |
| 43 | Agent 3's W6 gate B (w6gB): the p2fc arm over the L route through the level load, verify off | A3 / Agent 1 (asked 22:46; task #9, extra) | `build/agent3/s4b/logs/w6gB.check.txt` (28,722 B, 22:31:36) for `20261122-222313-w6-gateB-p2fc-level` (devoff4b-bin, L route, 600 s cap; P2 + fix (i) + C1, verify off); `w6gB.p2c.txt` (22:31:39); `w6gB.sidecar.out.txt` (22:30:48); the run's game.2.log, game.1.log and game.log; `bench/agent8/run/matrix-window6.json` E50D791B… L27; `build/agent12/w6-gates/W6-GATES.md` C9A88703… L36-39, L212 | C1, P2 and verify OFF by default | **PASS for W6: level load without tags** (§42). 119/119 steps in 448 s, exit 0. C1 init x1, the first kept protect logged, kept 2 → 114688 through the level load; stale, unhandled and Protect-failed lines 0; P2c 0; logdiff MORE 0, and NEW only the 6 finding-10 hang lines (STUCK-LOCK x5, owner lr 83FAF200, plus a dump: WARN, as in gate A). No characters on the pad: game.log rotated at 22:23:58, so the sidecar missed the 22:24:20 trigger line (load-confirms 0/3; a harness bug). No W6 change: W6's timed runs are title + attract only. Verify was off, so §21 A stays open; the host was busy (CPU median 82.6 %; Agent 2's -j8 native build ran until 22:39:53). C1 default-ON still needs s4bLV (fixed sidecar, 3/3 LOADs, the level reached with verify on), a quiet host, and p2fc only | ~22:57 to 1, 3 |

## File hashes (SHA-256, first 16 hex)

| File | Live | snap1 | Live mtime | Diff |
|---|---|---|---|---|
| gpu_native/device.h | 703939AA91EFEA81 | 12391F5C… | 20:48:28 | `a7-device.h.vs-snap1.diff` |
| gpu_native/device.cpp | 3D01E63142DBFB50 | 4DC63FA0B804C5FE (S1+p1) | 20:48:29 | `a7-device.cpp.vs-snap1.diff`; also `a7-device.cpp.vs-batch1.diff` (vs `build/agent7/batch1/device.cpp` 4C15043E) |
| gpu_native/fps_counter.h | E05D6A554042B302 | 79FC841E3180CA0D | 20:48:29 | `a7-fps_counter.h.vs-snap1.diff` |
| gpu_native/draw.cpp | 50AA3B1DEE615678 | 751C219EA5CCCD2F | 21:24:30 | `a6-draw.cpp.vs-snap1.diff` |
| gpu_native/pipeline_snapshot.h | 42318B849FAE030B | A0B71DB586139545 | 20:48:11 | `a6-pipeline_snapshot.h.vs-snap1.diff` |
| SDK src/audio/audio_system.cpp | C281FA8625435EFE | 7E129AF6EA359947 | 21:56:43 | `a12-audio_system.cpp.vs-snap1.diff` |
| SDK include/rex/audio/audio_system.h | 4836B139802D3438 | 8F8A2E71A05258B0 | 21:44:35 | `a12-audio_system.h.vs-snap1.diff` |
| Agent 5's 8 files | see §9 | = `build/agent5/pre-batch2/` | 20:55:39 / 21:13:38 | `a5-<file>.vs-snap1.diff` |
| tools/gpu-aot/patches/plume-winsdk-compat.patch | E03D29D0758E6150 | (new, 640 B) | 22:08:09 | none (new file; checked in §7) |
| tools/gpu-aot/prepare_plume.py | B3C877379038091E | CED19F81CF923329 | 22:08:37 | `a6-prepare_plume.py.vs-snap1.diff` |
| tools/gpu-aot/test_prepare_plume.py | DA360ABA28D609A3 | 82039EBA12F58180 | 22:08:39 | `a6-test_prepare_plume.py.vs-snap1.diff` |
| thirdparty/plume/plume_d3d12.cpp | 564568D4D5853F22 | 564568D4D5853F22 (S1+p2; S1 was B88E4E86DE5E5DEC) | 21:34:50 | none (= snap1) |
| Agent 11's #27: 2 SDK files, live since 23:19 (= staged) | hal AB359E1D6C4DA1B9, xam_ui 0A314946FDB9FE1E | hal 4A0F84AE…, xam_ui 03E89D11… (pristine) | 00:06:15 (touched by A12; content from 23:19) | `a11-hal.vs-live.diff`, `a11-xam_ui.vs-live.diff` (staged vs the then-pristine live) |

Unchanged since S1 (checked): pipeline_async.h (45B608C5…), pipeline_creation_gate.h (E047CE11…), draw_work_pool.h, native_worker.h, `gpu_native/resource_registry.h` (DD63CA85…) and the SDK `include/rex/thread/mutex.h` (C30A4809…).

## S2 include list (sent 22:33 to Agents 2 and 1)

`build/agent10/b3/S2-include.tsv` (sha256 E1FF04974373119B…, 22:31:24) gives, per file: action, path, live and S1 sha256, live mtime, owner, item and verdict.
- I built it from a read-only comparison of the live tree with `MANIFEST-S1-2041.tsv` (`scan-vs-s1.ps1` → `scan-vs-s1-2229.txt`). It found 34 changed files, 12 new and 0 deleted. I ignored 7 of the new ones: they are 0-byte moltenvk placeholders from 16:03.
- INCLUDE: 19 files, each rated SAFE at its default (items 1-9):
  - A7 #20: device.cpp (with p1), device.h, fps_counter.h;
  - A6: draw.cpp, pipeline_snapshot.h;
  - A5 batch 2: the 8 files in §9;
  - A12 #22: audio_system.cpp, audio_system.h;
  - A6 #26: prepare_plume.py, test_prepare_plume.py and the new plume-winsdk-compat.patch;
  - `thirdparty/plume/plume_d3d12.cpp` (= S1+p2).
- EXCLUDE, kept at S1: Agent 9's 20 codegen files (#15; the flush-mode elision "B" is still in progress). Agent 1 agreed at 22:34: they go into a separate codegen-option build after my review of B.
- #27 is not in S2. It is staged outside the live tree and lands in batch 3 (§10).

## S3 include list (sent 02:32 to Agents 2 and 1)

`build/agent10/s3/S3-include.tsv` (sha256 A1E7C83F7CFA1372…, 10,744 B, generated 02:27:09) has the same columns as the S2 list. Its base is S2: snap1 after the S2 apply (`build/agent2/snap1/STATE-S2-2315.tsv`).
- **Scan.** A read-only comparison of the live tree with STATE-S2 (`build/agent10/s3/scan-vs-s2.py`, snap.py walk rules) → `scan-vs-s2-0215-fast.txt` (a7384814…). It found 28 changed files, 0 new and 0 deleted, and skipped 8 moltenvk directory links. I hashed the 48 STATE-S2 rows outside the walk (research/dxc-1.9.2609, rexlego/out/native-gpu) separately at 02:16: all unchanged. The full-content rescan (`--full`) confirms it: `scan-vs-s2-0217-full.txt` (2F10DFD41E0FA723) finished at 02:41:28 after 1,464 s, with all 23,795 files hashed. It has the same 28 CHANGED lines as the fast scan, every TSV row with the same live sha, and nothing else (`cmp-full.py` → `cmp-full-0242.txt`).
- **INCLUDE: all 28.** The generator (`make-s3-tsv.py`) re-hashes each file and checks that it equals its blob at HEAD (`git hash-object` = `ls-tree HEAD`).
  - A6, fix (a) (§12): settings_registry.cpp 4EC71328…, settings_preferences.cpp 9CBE6DBF….
  - A12 (§8): audio_system.cpp 4331A312… (#22 plus the ON flip).
  - A11, landed by A12 (§11): rex_app.cpp 11DE333F….
  - A11 #27 (§10): xam_ui.cpp 0A314946…, xboxkrnl_hal.cpp AB359E1D….
  - A9 #15: the 20 codegen files kept out of S2 (the B inputs; output-identical at the default, codegen review). 3 are new to snap1: flush_mode.h, instr_cr_so_fold.s, opt_config.toml. No game or runtime unit includes `rex/codegen/*`, so they rebuild only the codegen library and tool, not the generated units.
  - A1: `.gitignore`, `.gitmodules`. They aren't build inputs (no CMake file reads them); they're included so that snap1 equals the commits. My plan before 02:27 had them as EXCLUDE.
- **EXCLUDE:** none.
- **Build inputs (Agent 1, 02:22), recorded in the TSV header:** game 001336f and SDK c5fe668, on top of the 01:50 checkpoint (a0bdaa7, 90e7ccd). Also the uncommitted pre-sprint edits, as in S1/S2: plume checked out at e0c8871 (the game pins ceaeeee) with 3 modified files, and simde at 71fd833 (= the pin) with `x86/sse.h` modified. Nothing under plume or simde differs from snap1.
- **Checks:** Agent 2's `make-rules-from-tsv.py` with prefix a1e7c83f7cfa1372 → 28 include, 0 exclude rules (`S3-rules-check.txt`). Codegen for B and S3: `install/batch-nolr` only, never `install/batch`.

## 1-4. Agent 7, task #20 (all native ON only: `gpu_native/` is compiled only with `LEGODIMENSIONS_NATIVE_GPU=ON`)

Agent 7's listing: `agent7-present.md` "Batch 2 listing (task #20)". The vs-snap1 diffs contain exactly the four listed items and nothing else.

**(h) SAFE.**
- device.h:94 declares `extern thread_local DrawPreparationContext* t_draw_preparation;` and device.h:95 is the inline accessor. The S1 out-of-line accessor (S1 device.cpp:756) is deleted.
- The one definition is device.cpp:755 `= nullptr`. It is constant-initialised, so there is no dynamic TLS initialiser and no TLS guard on access. It is outside the anonymous namespace (which closes at :753), so it already had external linkage.
- A grep of rexlego finds no other definition of the accessor or of `t_draw_preparation`. The fixtures that declare their own `t_draw_preparation` (test_query_retirement, test_submission_waits) are standalone programs.
- No DLL boundary: `legodimensions` is one `add_executable` with all sources (`rexlego/CMakeLists.txt:169/172`), and there are no SHARED or MODULE libraries. (`thread_local` can't be dllimported anyway.)
- Same semantics under the MS and Itanium ABIs. Agent 7 syntax-checked all 18 includers on the live tree (20:48-20:52), and the gpu-aot fixtures are unchanged.

**(i) SAFE (output-identical).**
- `MergeTouchingRects` (fps_counter.h:52-78) merges along rows, then down columns. In-place writes are safe because the write index never passes the read index (rows ≤ i, merged ≤ i, j < merged).
- The union of two rects that share a whole edge is a rect, so each colour covers the same pixels. The shadows are recomputed from the merged cells with the same (+1, +1) offset (device.cpp:2134-2136); a translated union is the union of the translations. All black clears still come before all white ones.
- Bounds: each input cell passed `left+4<=width && top+4<=height` (device.cpp:2122), so merged cells and their shadows stay in bounds. The count never grows (≤ 60; array at :2114). `pixels` and `shadows` are locals.
- The toggle is a magic static (:2131). The batched multi-rect path only gets a shorter list.
- Agent 7's `test_fps_rects.py`: 640,064 cases pixel-identical against batch 1, the toggle path matches batch 1, and 200,000 random bitmaps give identical unions.

**(p) SAFE.** device.cpp:2275-2276 is identical to the S1+p1 patch (no hunk in the vs-snap1 diff). The #21 evidence still applies:
- `WriteCsvFrame` returns when `!g_csv_file` (counter.cpp:156-158), which is set only by `--perf_log_csv` (runtime.cpp:122-123).
- It runs inside `if (presented)`.
- `Profiler::Flip` is called only from command_processor.cpp:1068, which native mode doesn't run (legodimensions_app.h:114-115). `FlushCsv` runs at runtime.cpp:323.

**(c') SAFE.** device.cpp:1901-1904 is a comment only.

## 5-6. Agent 6: async-PSO patch (applied to draw.cpp by Agent 4) and the pipeline_snapshot.h comment

**Patch identity.** `bench/agent6/draw-async.patch` sha256 56D686EB1BC4D88B… (verified). Agent 4 applied it to the live draw.cpp at 21:24:30. `a6-draw.cpp.vs-snap1.diff` contains exactly the patch's hunks and nothing else. The helpers it calls already exist in S1: `ShaderBindingsSnapshot` (shaders.h:31-34: 2 `shared_ptr<void>` + 2 u32), `CurrentShaderOwners` (shaders.cpp:634) and `Lease::Release()` (pipeline_creation_gate.h:26).

**Compile check.** `env/compile-one.ps1 -SyntaxOnly` on the live draw.cpp: exit 0, 0 errors, 33 s, 77 warnings, all `getenv`/`fscanf` deprecation. Log: `build/agent10/b3/cc-draw-syntax.log`.

**Default (unset): SAFE.**
- `AsyncPipelineConfig()` is a magic static, read once (pipeline_async.h:338-350). When the variable is unset it returns disabled at :331 and logs nothing (:342). Its first call happens under `g_pipeline_mutex` and does only a `getenv`.
- draw.cpp:1699-1701 and 1708-1711: `async ? Find(...) : nullptr` yields null, so both branches are skipped. draw.cpp:1713-1714 builds an empty snapshot, which is trivial. The async branch at :1856-1863 is skipped.
- The sync path is unchanged apart from `FinishPipeline` (draw.cpp:1672-1688, used at :1870-1871). That is a verbatim move of the existing checks and logs, with the same caps of 16 and one static counter each.
- `ResetDrawResources` (draw.cpp:5714): `DrainAsyncPipelineJobs` is a no-op while the runtime pointer is null (pipeline_async.h:402-404). Only `PostAsyncPipelineJob` creates the runtime, and only when enabled (:373-379). `Clear()` on the null map is a no-op (:117; call at draw.cpp:5727).
- The new global `g_async_pipelines` (draw.cpp:426) holds only a `unique_ptr`, so it is constant-initialised and its destructor does nothing when it is empty.
- Agent 4 rated the patch SAFE as well.

**ON (`LEGO_NATIVE_PSO_ASYNC` set): SAFE** (SAFE-IF until 21:58; see the exit bullet below).
- Lock order is fine. `GetPipeline` never waits while holding `g_pipeline_mutex` (it unlocks at pipeline_async.h:430 and :445). Jobs take only `g_pipeline_mutex`, the compile mutex, the pool mutex and logging (:447-462). `SetNativePipelineStencilReference` takes no lock (draw.cpp:909-916).
- Shutdown order is fine. `ResetDrawResources` drains the jobs before it takes `g_pipeline_mutex`. Its only caller is `HostDevice::Shutdown` (live device.cpp:923-956): after `StopNativeWorker` (:925), with the recording gate and `g_mutex` held (:926-927). Jobs take neither, so there is no deadlock. The drain comes before `ResetShaderResources` (:943), `StopPipelineLibrary` (:949) and `g_state.reset()` (:953), so the device, the root layout, the shader owners and the pipeline library outlive every job.
- **Exit (revised 21:58 after Agent 6's reply): no new hazard, so ON is SAFE.** The runtime is created with `new` and never deleted (pipeline_async.h:359-370, `new` at :365), so its threads are never joined (the join at :147 never runs). That matters only if the EXE's static destructors run while a compile is in flight. The usual exits never run them while other threads are alive:
  - Window close: `ReXApp::OnClosing` calls `TerminateTitle`, `FlushLogging`, then `std::_Exit(0)` (rex_app.cpp:693-707). `_Exit` runs no atexit handlers and no static destructors.
  - The close watchdog (legodimensions_app.h:409-419, armed at :183) calls `TerminateProcess` after 250 ms.
  - Quit Game: `ExitNativeGameNow` calls `TerminateProcess` (native_process_exit.h:12-16; hooked up at legodimensions_app.h:280).
  - Update restart: `std::_Exit(0)` (legodimensions_app.h:100).
  - Crash popup: `ExitProcess(0)` (crash_popup.cpp:178). It ends the other threads before any DLL detach, and it doesn't run the EXE's atexit table.
  - `ReXApp::OnDestroy` calls `OnShutdown` (rex_app.cpp:840-845), which calls `HostDevice::Shutdown` (legodimensions_app.h:199-200), and that drains first.
- **Pre-existing, not from this patch (listed for Agent 1):** two SDK kernel exports call the CRT `exit()`. That runs the EXE's static destructors on the calling guest thread while every other thread keeps running, and it skips OnShutdown. They are `HalReturnToFirmware_entry` → `exit(0)` (xboxkrnl_hal.cpp:34) and `XamShowDirtyDiscErrorUI` → `exit(1)` (xam_ui.cpp:542). On those paths the threads that already exist (native worker, draw pool) are exposed in the same way (Agent 6's point), so an async compile thread is one more thread in the same class, not a new hazard. Possible fix, for the SDK kernel owner: send both through the `FlushLogging` + `std::_Exit` exit that `OnClosing` uses.
- By design, a draw whose PSO is still compiling is skipped.

**pipeline_snapshot.h (20:48:11): SAFE.** The only hunk vs snap1 rewrites the comment above `Allocate` (live :57-61) to say why the buffer must be zero-filled. The code is unchanged.

## 7. Agent 6: Plume heap-type fix (the snapshot version S1+p2, and the live-tree patch #26)

**The snapshot version, S1+p2 (Agent 2, 21:34:50, in native-bin): SAFE (same value).** Checked at 21:51.
- `thirdparty/plume/plume_d3d12.cpp:505` in snap1 (B88E4E86… → 564568D4…, line 505 only): `case RenderHeapType::GPU_UPLOAD: return static_cast<D3D12_HEAP_TYPE>(5);`.
- 5 is `D3D12_HEAP_TYPE_GPU_UPLOAD` in all three bundled headers: FidelityFX-SDK `cauldron/framework/libs/agilitysdk/include/d3d12.h`, `cauldron/framework/libs/dxheaders/include/directx/d3d12.h` and `sdk/tools/ffx_shader_compiler/libs/agilitysdk/include/d3d12.h`. The machine's Windows SDK 10.0.22621 `d3d12.h` defines only DEFAULT = 1 … CUSTOM = 4, so 5 aliases no other heap type there.
- So the compiled code passes the same value that a build against a newer `d3d12.h` would. The heap-type choice around it is unchanged: plume asks for a GPU-upload heap only if `GPUUploadHeapSupported` (OPTIONS16, :3911) is set, or it uses its UMA fallback pool (:3087, :3953-3954, :4058-4060, :4113).

**The live-tree version, Agent 6's #26 (22:08): SAFE (tooling only).** Reviewed 22:20-22:31.

Files (live vs snap1; diffs `a6-prepare_plume.py.vs-snap1.diff` and `a6-test_prepare_plume.py.vs-snap1.diff`):
- NEW `tools/gpu-aot/patches/plume-winsdk-compat.patch`: E03D29D0758E6150…558747EF, 640 B, 22:08:09. CRLF on all 12 lines, like `plume-lego.patch` and `plume-adapter-query.patch`.
- `tools/gpu-aot/prepare_plume.py`: B3C87737…320A6957 (snap1 CED19F81…), 22:08:37. +1/-0: one tuple appended last to the patch list (:77, "Native Plume Windows SDK compatibility fixes"). The six earlier patches, the apply/verify logic (:93-111) and both success messages are unchanged.
- `tools/gpu-aot/test_prepare_plume.py`: DA360ABA…5EFA8F76 (snap1 82039EBA…), 22:08:39. +24/-1: the patch joins the independently git-applied expected chain (:97), and one new fixture covers it: missing gives `--check` exit 2 with no writes, false git success on the already-applied and apply paths gives exit 2 "missing patched hunk", and the upgrade from the six-patch state is exact. Its sha256 is added to `verification.json`.

The patch has one hunk, `@@ -502,7 +502,7 @@` in `plume_d3d12.cpp` (`toD3D12(RenderHeapType)`). It changes only line 505, from `return D3D12_HEAP_TYPE_GPU_UPLOAD;` to p2's line verbatim (`return static_cast<D3D12_HEAP_TYPE>(5); // = D3D12_HEAP_TYPE_GPU_UPLOAD, …`). So the value argument above applies unchanged.

Checks (22:20-22:27; light, single-thread python and git, all before quiet window 2):
- In memory (Latin-1, byte-exact): the hunk's new side equals live lines 502-508 of `plume_d3d12.cpp` (564568D4…). Reverse-applying it gives B88E4E86DE5E5DEC…, the recorded pre-p2 hash.
- `prepare_plume.py --check` passed in all three runs below. It only does `git rev-parse`, `git apply --reverse --check` and a hunk-text match, and I ran it with `GIT_OPTIONAL_LOCKS=0`. Log: `build/agent10/b3/a6-plume-checks.log`.
  - the live plume with the live 7-patch script;
  - snap1's plume with the live script;
  - snap1's plume with snap1's 6-patch script.
- `test_prepare_plume.py build/agent10/b3/plume-test` printed `PASS: 18 actual-public-source Plume preparation checks; original checkout unchanged` (103 s). Its `verification.json`: a fresh CRLF clone at PIN e0c8871b plus the 7 patches applied independently with `git apply` gives `patched_source_sha256` = **564568D4D5853F22…**, byte-identical to the live and snap1 file. `preparer_sha256` = B3C87737… (the live script) and `winsdk_compat_patch_sha256` = E03D29D0….
- Agent 6's own run (22:23-22:26, `agent6-native-aot.md` §8.4) agrees.

Why SAFE:
- S2 compiles the same plume source, 564568D4, that S1+p2 (native-bin) already builds. The patch only lets a fresh public checkout reach it.
- Configure: `rexlego/CMakeLists.txt:79-88` runs `prepare_plume.py --check` (native ON only) and stops with FATAL_ERROR if it fails. With the 7th patch listed, a plume tree without the line-505 fix (the pre-p2 B88E4E86 state) now fails configure until `prepare_plume.py` is run once. Such a tree doesn't compile against Windows SDK 10.0.22621 anyway. The live, snap1 and baseline plume trees all pass. (`baseline/DimensionsRecomp/thirdparty/plume` is a junction to the live plume, so baseline follows live there. snap1's copy is independent, with a single hard link.)
- `prepare_plume.py` is a native fingerprint input (CMakeLists.txt:601), so the fingerprint changes. S2's `device.cpp` (:604, A7 #20) changes it anyway.
- Behaviour is unchanged: 5 is the enumerator's value in newer headers. Plume asks for a GPU-upload heap only when OPTIONS16 reports support (:3911), and per Agent 6 nothing outside Plume asks for one.

## 8. Agent 12: #22 audio-shutdown fix (reviewed 22:05-22:15)

**Listing.** `agent12-io-memory.md` "Batch 2: audio shutdown (task #22)" (:413-549). Only two SDK files change: `src/audio/audio_system.cpp` (C281FA86…, 21:56:43; snap1 7E129AF6…) and `include/rex/audio/audio_system.h` (4836B139…, 21:44:35; snap1 8F8A2E71…). Diffs: `a12-audio_system.cpp.vs-snap1.diff` (+169/-13) and `a12-audio_system.h.vs-snap1.diff` (+7/-1). `mutex.h` is unchanged (C30A4809… = snap1), and so is `xthread.*`. The line numbers below are live `audio_system.cpp` unless marked otherwise.

**Default (cvar `audio_shutdown_detach_worker` = false, :47-52): SAFE. It is an equivalent rewrite of snap1.**
- Setup (:140-152): `worker_control_` stays null, so `ctl` is null. The lambda captures `[this, ctl, keep]` (`keep` is null) and calls `WorkerThreadMain(nullptr)`.
- The worker loop:
  - `leave()` and `reenter()` (:163-172) are `if (ctl)` no-ops, and the extra `if (ctl && …)` at :223 is false.
  - :185-186 copies `wait_handles_` into a local array of the same type and count (header :100: `WaitHandle* wait_handles_[kMaximumClientCount + 1]`). The copy happens at the same point where the old `WaitAny(wait_handles_, …)` read the array, and `WaitMultiple` copies the native handles on entry anyway.
  - `resume_event_.get()` (:206) and `function_dispatcher_` / `worker_thread_->thread_state()` (:238-239) are read into locals just before the same calls.
  - `global_critical_region::AcquireDirect()` (:222) is the same as `Acquire()`: both return `std::unique_lock<std::recursive_mutex>(mutex())` (mutex.h:64-71, = snap1). The lock covers the same statements (:227-229).
  - The trailing `leave()` (:267) is a no-op.
- Shutdown (:285-358):
  - `detach_mode` is false, so `resume_event_` is not set.
  - The timeout branch is the old WARN + `Terminate(0)` (:317-319).
  - `detached` stays false, so it does `worker_thread_.reset()` (:327) and then the old `DestroyDriver` / `SystemHeapFree` loop (:349-357), in snap1's order.
- Layout: `AudioSystem` gains one `shared_ptr<WorkerControl>` member and two non-virtual private functions, so the vtable doesn't change.
  - The 6 includer TUs rebuild (Agent 12's list, :428-434). Nothing in rexlego or `generated/` includes the header.
  - Agent 12's `-SyntaxOnly` passed in all 6 on the 21:45 revision. The 21:56 revision changes only the .cpp (one more `Wait(host_thread, false, ms)`, the same overload as :310), and Agent 12 rechecks it after the window.
- The new cvar is absent from `legodimensions.toml`, so it stays false.

**ON: SAFE-IF (condition at the end).**

*The normal path (the worker exits within 500 ms) is unchanged.*
- Protocol trace: the phase starts Inside (:74). Every blocking call is bracketed by Leave (Inside → Outside) and Reenter (Outside → Inside):
  - WaitAny :187-190;
  - the resume wait :207-209;
  - G :221-226;
  - the callback :240-242;
  - the sleep :260-262.
  
  The final `leave()` at :267 is the last one. I traced every path (failed, timeout, shutdown event, paused, pumped, not pumped): each `leave()` follows Inside, so without Shutdown no CAS fails. The cost is 2 uncontended CAS operations per blocking call.
- `TryDetach` is only reached after the 500 ms wait fails (:310-315). A worker that exits in time gets the old teardown (:327, :349-357).
- The one ON difference on the normal path is the paused case. :297-301 sets `resume_event_` (auto-reset, :124) before `shutdown_event_`. The paused worker (:204-210) wakes, `continue`s, sees `worker_running_ == false` (atomic, header :82, set at :295) and exits. Before, it was terminated at 500 ms.

*AudioSystem frees nothing under a worker that is still running.*
- After 500 ms, `DetachWorker` (:362-384) first waits another 2000 ms. If the worker exits, it returns false and the old teardown runs with the worker gone.
- Otherwise `TryDetach` (a CAS from Outside to Detached) can succeed only while the worker is Outside. Exactly one of `TryDetach` and the worker's `Reenter` wins.
  - When the worker's `Reenter` fails, it calls `Park()` (:96-100), which holds no lock and is not alertable.
  - On the G path it unlocks G before parking (:223-225).
- On detach, Shutdown frees nothing the worker can reach:
  - `worker_thread_.release()` (:325) keeps the XThread (thread state, guest stack) and its `host_fn_`, which holds `keep` and so the control block.
  - The semaphores and events are released, not destroyed (:335-339).
  - `DestroyDriver` and `SystemHeapFree` are skipped (it returns at :344).
- The worker reads members only while Inside, so `audio_system_.reset()` (runtime.cpp:301) can free the object.
  - `~AudioSystem` (:128-132) only shuts down the XMA decoder again, as snap1 does, and destroys the now-null `unique_ptr`s.
  - `pause_fence_` is touched only while Inside (:205).
- Races I checked:
  - `Leave` against `ForceDetach` (a plain store, :93): `Leave`'s CAS fails and the worker parks before it blocks.
  - The final `leave()` (:267) against `TryDetach`: a harmless leak plus a WARN for a worker that was about to exit anyway.
  - A null `host_thread`: no terminate, just a reset; no worker is running.
  - The mode is latched at Setup (`worker_control_`), so a cvar change at run time can't split the two sides.

*Residual risks (these are the condition).*
- **R1.** Guest code on a detached worker can still run during the Runtime teardown, after `kernel_state_.reset()` (runtime.cpp:307) and `memory_.reset()` (:317). That happens if a callback blocked for more than 2.5 s resumes, or if a callback runs for that long.
  - TerminateTitle already applies the same policy to guest stragglers (kernel_state.cpp:1038-1040: "deliberately left running, never force-killed").
  - In the same case, OFF terminates the worker at 500 ms, which can orphan G (a hang) or crash in ntdll. Agent 12's 20-run smoke: old h gave 9 HUNG and 4 CRASHED; new h gave 20 clean.
- **R2.** `ForceDetach` (:376-380) on a worker still Inside after 2 s. The Inside stretches are a memcpy, member reads, `pause_fence_.Signal` and the debug logs for the first 10 callbacks. Only a stalled log call could last 2 s.
- **Reachability.** `AudioSystem::Shutdown` runs only from `Runtime::Shutdown` (runtime.cpp:299-301), through OnDestroy or setup failure. Window close is `std::_Exit` (rex_app.cpp:693-707) and Quit Game is TerminateProcess (§5), so in normal play neither mode runs this code.
- **Condition for making it the default.**
  - Agent 12's post-window checks pass: `-SyntaxOnly` on the 21:56 revision, and the 1000-run replica (old and new, h/p/b) shows NEW with 0 HUNG and 0 CRASHED.
  - Agent 1 accepts R1 as TerminateTitle's straggler policy.
  
  Making it the default is a one-line cvar flip (:48), so it fits batch 3. S2 takes the change at the default, OFF.
- **Condition met (00:08).**
  - Agent 12's replica (`agent12-io-memory.md:556-566`; exe EFEF2094 unless noted): NEW had 0 HUNG and 0 CRASHED in 4,000 runs (1,000 each of h, p and b, plus 1,000 h on exe E5DA67F4). OLD h had 429 HUNG and 171 CRASHED in 1,000; OLD b had 2 CRASHED.
  - `-SyntaxOnly` on the 21:56 revision exited 0 at 22:23 (:416, :527).
  - Agent 1 accepted R1 (~23:57), so the ON flip goes into S3.
  - I confirm the ON rating when Agent 12 sends the one-line diff after quiet window 3.
- **ON confirmed on the live file (02:17).** Agent 12 ran `s3flip_stage.ps1 -Apply` at 02:04 on Agent 1's GO.
  - Live `audio_system.cpp` is 4331A312A9FE8F15… (18,877 B, 02:04:39, LF only), the staged file. Its `git diff HEAD` equals the staged `build/agent12/s3flip/audio-default-on.diff` (BF399E59…, -1/+1).
  - My own `git diff --no-index` of the pristine copy (C281FA86…) against the staged file changes one line: :48 `audio_shutdown_detach_worker, false,` → `true,`.
  - `s3flip_stage.ps1 -Check` exits 3 (applied). The syntax check of the live file passed with only the 2 known decoder.h warnings (`build/agent12/s3flip/syntax-20261122-020455.txt`).
  - No toml, runner or bench file sets `audio_shutdown_detach_worker`, so every S3 arm runs ON. `--audio_shutdown_detach_worker=false` gives the old mode back.
  - **Verdict: SAFE ON.** The condition was met at 00:08, and the live change is that one line. The cost when ON is two uncontended CAS operations per blocking call on the audio worker. Undo: `s3flip_stage.ps1 -Revert`.

## 9. Agent 5: batch 2 (reviewed 21:58-22:15)

**Listing.** `agent5-uploads.md` (22:00:32) "Batch 2" (:282-406; listing at :334, tests at :364). The live hashes match Agent 5's list. `build/agent5/pre-batch2/` = snap1 (verified), and `resource_registry.h` is unchanged (DD63CA85… = snap1). Diffs: `build/agent10/b3/a5-<file>.vs-snap1.diff`.

| File (gpu_native/) | Live | mtime | vs snap1 |
|---|---|---|---|
| upload_legacy_paths.h | 5C823F13… | 20:55:39 | new, 1131 B |
| texture_volume_upload.h | D0601ECF… | 21:13:38 | +4/-2 |
| texture_scratch.h | 8F6A12AE… | 21:13:38 | +9 |
| texture_upload_source.h | FF9E1141… | 21:13:38 | +6 |
| vertex_upload.h | FFD2B023… | 21:13:38 | +29 |
| buffers.cpp | 75025044… | 21:13:38 | +4/-1 |
| upload_buffer_pool.h | 853E6C16… | 21:13:38 | +9/-4 |
| textures.cpp | 3011ADD4… | 21:13:38 | +66/-7 |

**Default (both variables unset): SAFE.** Only Agent 4's (a) changes code that runs by default, and its output is identical.
- `upload_legacy_paths.h:14-32`: `LegacyUploadPathsEnabled()` is a magic static that reads `LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD` once. It is on only if the variable is set, non-empty and doesn't start with '0'. The default cost is one guard check per call.
- The legacy branches are all skipped at the default:
  - `texture_volume_upload.h:279`: `if (!fast || LegacyUploadPathsEnabled())`.
  - `texture_scratch.h:23-27`: the legacy early return. The default falls through to the S1 lease path.
  - `texture_upload_source.h:47-50`: the legacy memsets.
  - `vertex_upload.h:77-99`: `SwapUploadElementBytesLegacy` is the old loop, verbatim. It is dispatched only when legacy is on (:107-108).
  - `buffers.cpp:491-493`: `Legacy ? new u8[len]() : new u8[len]`.
- `upload_buffer_pool.h`: `kDefaultBudget` is 192 MB, and the default constructor delegates to `explicit UploadBufferPool(uint64_t budget)`. `State` holds a `const uint64_t budget`, which the deleter reads; `Reset` keeps it. `g_upload_pool` (buffers.cpp) behaves as before.
- `textures.cpp:179-227`: the staging pool, inside the anonymous namespace (:64-1529).
  - `g_texture_staging_pool` (64 MB) allocates one `State` at static init even when the pool is disabled. That cost is trivial: the free list stays empty, so its destructor at exit frees nothing.
  - `TextureStagingPoolEnabled()` is a magic static and logs only when on.
  - The two allocation sites (:2368-2371, :2440-2443) get false from `UseTextureStagingPool()` and take the S1 `createBuffer` branch. Both arms of the ternary are `shared_ptr<RenderBuffer>`.
  - `ResetTextureStagingPool()` returns at once when the pool is disabled (it's called at :3329 and :3336).
- Agent 4's (a) in `ResolveFramebuffer` (:3110-3192):
  - :3148 skips `FindTexture(0)`. That call always returned `{}` with no side effect: `FindPinnedOwner` returns `{}` for address 0 (device.cpp:756-757), and `Lookup` returns `{}` before it touches the TLS cache or the mutex (resource_registry.h:51).
  - :3155 is `const auto& owner = depth ? depth : colors[0];`. Both operands are lvalues (`const shared_ptr` and `shared_ptr`), so the result is a `const shared_ptr` lvalue that binds directly, with no temporary.
  - `depth` is const, and `colors` isn't written after :3147. So every use of `owner` sees the same object as the old copy did: :3159, :3160, :3188 (which copies it into `g_framebuffer_owners`) and :3190. Both referents live until the return.
  - The only effect is one fewer refcount increment and decrement.

**Legacy ON (`LEGO_NATIVE_TEXTURE_LEGACY_UPLOAD=1`): SAFE.** It restores the S1-era loops and zeroing.
- `lease_` stays null on the legacy scratch path, so the destructor (texture_scratch.h:46-48) doesn't touch the thread block.
- No nit, withdrawn at 22:15 after Agent 5's reply. `base_size` can't be 0 at texture_upload_source.h:48: `Capture` returns early on `!base_size` (:40), so after `base_.resize(base_size)` (:46), `data()` is non-null. Only `mip_size` can be 0, and :49 guards it.

**Staging pool ON (`LEGO_NATIVE_TEXTURE_STAGING_POOL=1`): SAFE-IF the A/B shows no texture corruption.**
- `Acquire` takes a shared lock and `Reset` a unique lock, so Reset's state swap is ordered against the unlocked draw-preparation acquires. The deleter captures its `State`, so a release doesn't need the pool.
- A buffer goes back to the pool only at its last owner's release (the publication LRU, or RetireResource's fence slots). That is exactly where the default path destroys it, so reuse never comes earlier than destruction would. Every use rewrites all the bytes its copy footprints read (Agent 5's poison test).
- Resets happen in two places:
  - `StartTextureResources` (:3329);
  - `ResetTextureResources` (:3336), under LockRecording and before `publications.Reset`.
  
  `HostDevice::Shutdown` calls `ResetTextureResources` after `WaitForSubmittedFrames` (device.cpp:923-955), so pooled buffers are destroyed before their device.
- Memory: at most 64 MB idle, plus power-of-two rounding (at most 2x) on buffers the LRU holds.
- Both sites pass `upload_size` as a u32, and it is at most 64 MB whenever the pool is used.

**Agent 5's tests.** I didn't rerun them (quiet window). The logs postdate the 21:13:38 sources, and I checked their tails at 22:12.
- byteswap: 542,348 cases PASS on the v2 (SSSE3) and SSE2 (scalar) paths (`b2-tests-default.log`, `b2-tests-legacy.log`).
- Staging pool: `test_texture_staging_pool` passed (0 failures). Its stress run did 300,000 acquires with 31 concurrent resets and ended with 0 idle buffers (`b2-staging-pool.log`).
- Retention: 1,440 PASS, in both default and legacy (`retention-b2*.log`).
- Poison: the mutants are caught (`poison-b2*.log`).
- From Agent 5's notes: the untile differential (3,964,537 copies; v3, v2 and no-SSSE3), `compile-one -SyntaxOnly` on textures.cpp and buffers.cpp (exit 0), and the gpu-aot CPU checks (17 pass; the 7 failures are pre-existing).

## 10. Agent 11, #27: the SDK's CRT `exit()` exits become `FlushLogging` + `std::_Exit` (batch 3; reviewed 22:27-22:40)

Found during item 5 (§5): `HalReturnToFirmware_entry` calls `exit(0)` (xboxkrnl_hal.cpp:34) and `XamShowDirtyDiscErrorUI` calls `exit(1)` (xam_ui.cpp:542). Both run the EXE's static destructors on the calling guest thread while every other thread keeps running, and both skip OnShutdown. Agent 1 gave the fix (`FlushLogging` + `std::_Exit`, as `ReXApp::OnClosing` does at rex_app.cpp:700-706) to Agent 11 as a batch-3 task (22:01), coordinated with Agent 12's #22.

**Listing.** `agent11-kernel.md` "#27 exit-path fix" (:986-1115). The fix is staged in `build/agent11/exitfix/` (22:27) and is not in the live tree. It lands in batch 3 through `bench/agent11/exitfix_stage.ps1 -Apply`, which refuses if either live file changed since 22:27.
- `exitfix.diff`: B2C1FE21304AB4BD…, +19/-6, two hunks per file.
- Staged `xboxkrnl_hal.cpp` AB359E1D6C4DA1B9… and `xam_ui.cpp` 0A314946FDB9FE1E… (`HASHES.txt` has the full hashes). The pristine hashes recorded there equal live and snap1: 4A0F84AE84BC61B5… and 03E89D1119CB059D… (live mtime 11:04:45; rechecked 22:38).
- My diffs of staged vs live (`build/agent10/b3/a11-hal.vs-live.diff`, `a11-xam_ui.vs-live.diff`) contain exactly the hunks in `exitfix.diff` (numstat +10/-3 and +9/-3). Line endings stay LF, as in the live files, and there is no BOM.

**What changes (staged line numbers).** In each file:
- `#include <cstdlib>` is added for `std::_Exit` (hal :15, xam_ui :12).
- The old TODO comments become a comment that gives the reason (hal :33-38, xam_ui :542-546).
- `exit(0)` becomes `rex::FlushLogging(); std::_Exit(0);` (hal :40-41), and `exit(1)` becomes the same with code 1 (xam_ui :547-548).
- The log lines before the exit are unchanged. There is no cvar, so the fix is always on.

**Verdict: SAFE.** The new exit is a strict subset of the old one. It keeps the log flush and the process exit, and drops only the hazardous phase: the EXE's atexit handlers and static destructors running on a guest thread while other threads keep running.
- `rex::FlushLogging` is declared at `include/rex/logging/api.h:82` (namespace `rex`). Both files already include `<rex/logging.h>`, which includes api.h (:18).
  - It takes `g_mutex` and flushes each registered logger (`src/core/logging.cpp:327-332`).
  - It frees nothing, unlike `ShutdownLogging` (:307-325), which frees loggers that a straggler thread may still use.
- It is `ReXApp::OnClosing` (rex_app.cpp:693-707) minus `TerminateTitle`, and leaving that out is correct. Called from a guest thread, `TerminateTitle` terminates the caller and never returns (kernel_state.cpp:1059-1066), so `_Exit` would never run. `OnShutdown` would tear down the runtime this thread runs on. The new comment says both.
- The exit codes stay 0 and 1.
- These were the only CRT `exit(` calls in the SDK kernel and system directories (`xthread.cpp`'s `Exit(` is a method).
- The DirtyDisc dialog runs through `xeXamDispatchDialog(..., 0)`. With overlapped 0 it waits on a fence (xam_ui.cpp:87-92, `if (!overlapped)` at :105), so the dialog has closed before the exit, as the new comment says.
- What the old `exit()` ran that `_Exit` skips. I checked Agent 11's table against the code:
  - No `atexit` handlers are registered.
  - The pipeline library is `new`-ed and leaked on purpose (pipeline_library.cpp:684-690, :716-729). It is saved on the present thread and in `Stop` (Shutdown path only), so no static destructor ever saved it.
  - The toypad helper is in a job object with KILL_ON_JOB_CLOSE (toypad_app.cpp:131-155; table :1068), so it dies with the game on both paths.
  - Settings, saves, achievements and toypad figures don't depend on how the process exits.
  - Perf CSV (`g_csv_file`, flushed every 60 frames; table :1063): up to 59 tail rows are lost, as on window close.
  - Native `frames.csv` (function-local `static std::ofstream`, device.cpp:2298; table :1064): its tail buffer is lost, as on window close. Its destructor used to run while the render thread could still write to it, which is the hazard being removed.
  - Window close (`std::_Exit` in `OnClosing`) already skips all of these, so the main exit path is the precedent.
- #22 doesn't depend on these paths. `AudioSystem::Shutdown` runs only from `Runtime::Shutdown` (§8), which neither the old nor the new exit reaches.

**Landing sequence (Agent 11's plan, agent11-kernel.md:25-36).** These checks show that the fix compiles and applies. The verdict needs nothing beyond them.
1. After quiet window 2: run `exitfix_check.ps1`, then `exitfix_check.ps1 -Pristine` (which must fail), `exitfix_syntax.ps1` and `exitfix_test.ps1` (`/MD`, `/MT` and DLL test builds). Record the results in `build/agent11/exitfix/`.
2. After S2 is taken: run `exitfix_stage.ps1 -Apply`, then `exitfix_check.ps1 -Live` and `exitfix_syntax.ps1 -Live`.

## 11. Agent 11: S3 proposal, `pause_safe_order` default ON (reviewed 00:00-00:10)

**Listing.** `agent11-kernel.md` "S3 proposal" (:1202-1290). Staged in `build/agent11/safeorder/`, not in the live tree:
- `safeorder.diff`: 56952876…, 2,101 B, 23:48:47, LF; 2 hunks, -5/+7, all in `src/ui/rex_app.cpp`.
- Staged `rex_app.cpp` 11DE333F…. The live file is still pristine (E1569868…, 19:43:51), as `safeorder_stage.ps1 -Apply` requires.
- Hunk 1 (:71-75) changes the default from false to true and says in the help text why. Hunk 2 (:741-745) changes the comment to "default on" and cites test G.
- No code changes, and the kill switch stays (`--pause_safe_order=false`).

**Verdict: SAFE.** The safe order (task #17, already in S2) removes the deadlock, and it gives up nothing that the original order did correctly.
- **What runs while guest threads are stopped** (`SetGuestPaused`, rex_app.cpp:745-788):
  - Pause: `audio->Pause()`, the thread snapshot (the object table lock and an allocation) and the log line all run first, while the guest runs (:751-765). Then only the `Suspend` loop runs (:767-769).
  - Unpause: the `Resume` loop runs first, over the pause's own list (:774-779). `audio->Resume()`, the log line and `entries.clear()` run after every thread is running again.
  - `XThread::Suspend` (xthread.cpp:1015-1044) holds the global critical region and the object table lock until the thread has really stopped, so no thread stops while holding either one. On Win32, `XThread::Resume` (:964-974) is an atomic decrement plus `ResumeThread`, with no lock, allocation or log. Both orders use these same two calls.
  - The original order (:790-812) suspends first and then waits in `audio->Pause()` for the audio worker, which may be inside a guest callback that needs the stopped threads. That is test G's hang. It also logs while threads are stopped, and its unpause allocates and takes the object table lock before it resumes anything.
- **The unpause resumes only what the pause suspended.** The original unpause takes a fresh snapshot, so it also resumes threads the pause never suspended:
  - a thread the guest created suspended in the meantime starts early;
  - a running thread gets its guest suspend count wrapped (the Win32 `fetch_sub` has no floor).
- **One small difference, harmless.** `Suspend` increments the guest count (:1018) before it calls the host. If the host call fails, the safe unpause skips that entry, so the count stays one higher, where the original unpause decremented it. In practice only an exiting or exited thread fails there, and nothing suspends or resumes it again.
- **Shared by both orders:** a guest thread created between the snapshot and its creator's suspension isn't suspended. The comment at :750 is why audio pauses before the snapshot: threads created during that wait are still caught.
- **Lifetime.** `GetSafeOrderPause()` is leaked on purpose (:104-107), so nothing releases thread references at process exit. `active` latches the path (:745), so flipping the cvar during a pause can't strand a thread.
- **Who it affects.** `SetGuestPaused` runs only on focus changes (:818, :825) and from the debug cycle (`debug_pause_cycle_ms`, default 0). The pause on focus loss needs `pause_when_unfocused`, which defaults to false (window.cpp:43; offered in the settings UI, ui_theme.cpp:99). No repo toml sets either cvar, rexlego never calls `SetGuestPaused`, and every runner passes `--pause_when_unfocused=false`. So the flip matters only for players who turn that setting on, and for them it removes a hang.
- **Evidence.** Test G (#23): the original order hung in 2 of 2 runs. The 23:22 dump shows the UI thread in `pause_fence_.Wait()`, the Audio Worker in the game's callback blocked in `KeWaitForMultipleObjects`, and every guest thread suspended. The safe order passed 100 of 100 pauses (50 with B OFF, 50 with B ON). Agent 11's checks: `safeorder_stage.ps1` PASS 11/11, and the pristine and staged files both pass `-fsyntax-only` with the same 3 pre-existing warnings.
- **Not fixed in either order** (Agent 11's :1254-1261): a stopped thread could still hold a host lock (G, T, the CRT heap or the logger) that the UI thread's message loop needs. Cosmetic: "Guest suspended" is logged just before the threads actually stop.
- **With #22's ON flip in S3.** `Pause()` and `Resume()` don't change. The worker's `leave()`/`reenter()` are uncontended CAS operations unless Shutdown runs, so test G's result carries over. Worth doing: Agent 11's optional test G half 1 on the S3 build without an explicit `--pause_safe_order` (:1290), so that the default itself is tested.

**Landing (agent11-kernel.md:1284-1289).** Agent 12 runs `bench\agent11\safeorder_stage.ps1 -Apply` after quiet window 3 and before S3 is cut. The script refuses unless the live file still equals pristine E1569868…. Then `safeorder_stage.ps1 -Check` (`staged (applied)`) and `safeorder_syntax.ps1 -Live`, which is a compile, so not during a quiet window. To undo: `-Revert`.

**Landed (02:04).** Agent 12 ran `-Apply` on Agent 1's GO.
- Live `rex_app.cpp` is 11DE333FA4C0541F… (33,054 B, 02:04:38, LF only): the staged file I rated. `git diff HEAD` equals `safeorder.diff` (56952876…), and `-Check` says `staged (applied)`.
- `safeorder_syntax.ps1 -Live` passed with the 3 known warnings (xmemory.h:260, rex_app.h:99/:102; `build/agent11/safeorder/syntax-20261122-020520.txt`).
- No toml or runner sets `pause_safe_order`, so S3 runs the new default. Agent 11's `testg_session.ps1 -Only default` on devoff3 tests it.
- **Verdict unchanged: SAFE**, also together with #22's ON flip (last bullet of the verdict above).

## 12. S3 native startup fix: Agent 6's Fix A, its commit hunk, and Agent 7's one-line alternative; Agent 7's ODR/layout analysis for option (b) (reviewed 00:30-01:25)

Agent 1 chose (a) for S3 at 00:30 (RESTART-PROMPT-S3.md E1). This section is the rating it asked for. No compiles ran, because quiet window 3 was in force.

**Inputs** (all re-hashed at 01:20, unchanged):
- `build/agent6/fix-a/fix-a.patch`: 71AEFF3DE46F2BC3…, 1,865 B, 23:49:07. It changes 2 files, at `settings_registry.cpp:103` and `settings_preferences.cpp:69-71`. Agent 6 describes it in `agent6-crash-triage.md`, "Fix A as a unified diff" (A3BBAE43…).
- `build/agent6/fix-a/fix-a-commit.patch`: 50046A3FE23DCF03…, 866 B, 23:49:08. One hunk, `settings_registry.cpp:200`.
- Agent 7's untested one-line alternative: `agent7-s3-proposal.md` §(a) (459145C2…, 00:33:49).
- `perf-notes/agent7-odr-ffx.md`: 9EA96B22…, 15,381 B, 00:20:22, read in full.
- Live files (pristine, 10:57:52): `settings_registry.cpp` A3733700… (10,951 B) and `settings_preferences.cpp` C78112AA… (4,739 B).

**Checks.** Script `build/agent10/review/r6/odr_fixa_checks.ps1`, log `r6/odr_fixa_checks.log`. Everything ran on scratch copies in `r6/fixa/{a,ac,c}/`; no live edits.
- `git apply --check`, apply and `-R --check` all return rc=0 for fix-a.patch.
  - fix-a-commit.patch applies on top of it, and also alone (rc=0).
  - The paths are `a/rexlego/src/...`, so apply from `DimensionsRecomp/`.
- The results match Agent 6's hashes:
  - registry 8BA19C5F9AC2090F (11,187 B);
  - prefs 9CBE6DBF9CEDA62D (4,938 B);
  - registry with the commit hunk 4EC71328043FA6BA (11,224 B).
  - CRLF is kept (0 bare LF).
- `rex::cvar::GetFlagInfo(std::string_view)` is declared at `rexglue-sdk/include/rex/cvar.h:234` and implemented at `src/core/cvar.cpp:427-435`. It takes the recursive registry mutex and returns nullptr for an unknown name. The patch only null-tests the result, so the pointer-invalidation caveat doesn't apply.
- The mangled `GetFlagInfo` is already exported by rexruntime.dll in devoff1-bin, native-bin and native2-bin, next to `GetFlagByName` and `GetFlagSource`, which rexlego already imports. No SDK rebuild or new export is needed.
- For an unregistered name:
  - `GetFlagByName` returns "" (:373-381);
  - `GetFlagSource` returns kDefault (:383-390);
  - `SetFlagByName` → `SetFlagFromSource` returns kRejected (:298-322).
- The only compile evidence so far is Agent 6's clang `-fsyntax-only`. Agent 6 runs -SyntaxOnly again when it applies the patch at Agent 1's GO.

**Why builds without FFX fail, and where.**
- `present_fsr_sharpness_reduction` (:62) and `present_fsr_max_upsampling_passes` (:56) are registered only under `#if REX_HAS_FIDELITYFX_SDK` (`rexglue-sdk/src/ui/presenter.cpp:43-78`).
- In the other branch, `present_effect` (:75) allows only "bilinear".
- Every other catalog key is registered unconditionally (window.cpp, device.cpp, fsr3_settings.cpp, native_effects.cpp, cheat_menu.cpp:321).
- So in a build without the FFX source dir, the registry's read gets "" for the two FSR 1 keys and throws. Two paths run that read:
  - `NativeSettingsRuntime` (legodimensions_app.h:155-160, created only when `native_settings_frontend` is set, as the run toml does) → `CaptureBackend` → throw. This is the crash.
  - `LoadNativePreferences` (:122-141) turns the throw into a warning, so native-settings.toml is silently ignored in every build without FFX.

**Verdict: fix-a.patch SAFE; fix-a-commit.patch SAFE and recommended. Hunks 1 and 2 must ship together.** They're in one patch, so never split it.
- **Hunk 1** (registry:103, the crash fix): an empty read of an unregistered key falls back to `spec.default_value`.
  - For a registered key the new condition is always false. FFX builds, and every registered key, therefore behave exactly as before, including the throw on an empty value.
  - The defaults "0.2" and "4" pass the catalog's `Canonical`, so the snapshot gets the same values as `settings_snapshot.h:29-30`.
- **Hunk 2** (prefs:69-71) is required with hunk 1. Without it, a native-settings.toml holding a non-default FSR 1 value (saved by an FFX build, or edited by hand) quits the game at startup:
  1. hunk 1 reads the key as the default;
  2. the saved value differs, so the key is applied;
  3. `SetFlagByName` rejects the unknown name, and the write throws;
  4. the rollback write fails the same way, which sets `recovery_failed`;
  5. the app calls `QuitFromUIThread` (legodimensions_app.h:138-141).

  Hunk 2 skips unregistered keys the same way as overridden ones, so loading continues.
- **Hunk 3** (fix-a-commit.patch; registry:200, which is :202 after hunk 1):
  - Without it, every Save in a build without FFX writes the catalog defaults 0.2 and 4 into native-settings.toml, overwriting values an FFX build saved.
  - `SaveConfigPatch` (settings_config.cpp:158-184) parses the file, applies `insert_or_assign` only to the patch keys and rewrites the file atomically, so skipped keys keep their values.
  - It isn't needed for the crash, but it costs nothing.
- **These defaults can't change rendering, because FSR 1 can't be reached without FFX:**
  - device.cpp:2048-2069 needs `present_effect == "fsr"` (or the snapshot's fsr1), and the non-FFX `present_effect` never allows "fsr".
  - The FSR 1 menu rows are enabled only when it is "fsr" (settings_frontend.cpp:231-234).
- **Callers.** `NativeSettingOverrideReason` is called only at registry :169 (validate/normalize), :189 (commit check) and :200 (commit loop), and at prefs :71. I grepped all 255 rexlego src/gpu/gpu_native files. Fix A touches only the :71 and :200 call sites.

**Behaviour change for S3, for the matrix owners.**
- With Fix A, a build without FFX now applies an existing `<user_data_root>/native-settings.toml` (vsync, fps limit, scale, FSR 3 …) when `native_settings_load=true`, which is the cvar default. Until now the swallowed throw meant these were ignored.
- The runners pass `--native_settings_load=false` in every arm (agent8-window3.md:36, agent3-run-harness.md:38), so S3 stays comparable with S2. Keep that flag in every S3 arm.

**Left over (follow-up, not a blocker):**
- A toml with `present_effect = "fsr"`, saved by an FFX build, still makes a build without FFX reject the whole saved profile. The write is rejected, everything rolls back cleanly, `ok=false`, and a startup error dialog appears. It doesn't quit.
- The settings menu there still offers "fsr". Choosing it fails at Apply and restores cleanly.
- A later fix could hide "fsr" when the registered `present_effect` doesn't allow it (`GetFlagInfo(...)->constraints`).

**Agent 7's one-line alternative: NOT SAFE as written.** It puts `if (!rex::cvar::GetFlagInfo(key)) return "Setting is not available in this build";` at the top of `NativeSettingOverrideReason`. That covers hunks 2 and 3 and also blocks FSR 1 edits, but it breaks "Restore defaults" in every build without FFX:
- validate/normalize (registry :169) calls `NativeSettingOverrideReason` for each key;
- `Transaction::Defaults()` (settings_transaction.cpp:47-70) normalizes every key in `NativeSettingsDefaults()`, which is all 17 catalog keys (legodimensions_app.h:165 → settings_service.cpp:61), and fails as a whole if one key fails;
- so the "Restore defaults" row (settings_frontend.cpp:89, 305, 338) would always fail with "Setting is not available in this build".

It is also untested. A variant that would work: for an unregistered key, normalize succeeds only when the canonical value equals the catalog default. Already true today, and not caused by either fix: Defaults fails whenever any catalog key is overridden on the command line or by env.

**(b) ODR/layout analysis (agent7-odr-ffx.md): AGREE.** Clean in practice, formally an ODR violation (ill-formed, no diagnostic required), and no layout blocker. My spot checks match Agent 7's:
- `REX_HAS_FIDELITYFX*` appears only in these files (918 SDK and 255 rexlego files scanned):
  - include/rex/ui/presenter.h (12 lines);
  - include/rex/ui/d3d12/d3d12_presenter.h (4);
  - include/rex/ui/vulkan/presenter.h (4);
  - src/ui/{presenter, d3d12/d3d12_presenter, vulkan/vulkan_presenter}.cpp.
- CMake:
  - rexui is an OBJECT library (src/ui/CMakeLists.txt:99).
  - `REX_HAS_FIDELITYFX_SDK=1` is PRIVATE to rexui (:122-127), and `..._RUNTIME=1` is set only when the amd_fidelityfx targets exist (:130-141).
  - rexgpu-xenos is SHARED and links rexruntime (src/graphics/CMakeLists.txt:101, :136-139). It and the exe therefore compile the headers without the macro.
- presenter.h:
  - Guarded blocks: 215-228, 231-263, 276-302, 317-322 (the cas/fsr data members), 430-438, 449-453, 464-467, 473-484 (`kMaxGuestOutputPaintEffects`, which is 1 without FFX) and 551-618.
  - All virtuals (328, 330, 364, 639, 645, 686, 717) are outside the guards, so the vtable is the same in both builds.
  - The members from `guest_output_paint_config_` (:938) onward move. The inline `GetGuestOutputPaintConfigFromUIThread` (:365-367) and `AreDXGIUITicksWaitable` (:1008-1011) touch moved members.
- d3d12_presenter.h:
  - Guarded at 135-140, 151-163, 265-274 and 315-322 (no virtuals).
  - Layout-dependent: kViewCount (:198), the intermediate textures (:245-246), and the root signature and pipeline arrays (:286-291).
- Outside src/ui and include/rex/ui (1,037 files, including rexlego, rex_app.cpp and windowed_app_main_sdl.cpp), I grepped for the layout-sensitive pattern: paint config/flow/effects, `Create`, `PaintContext`, `sizeof(Presenter)`, `CreatePresenter`, dxgi_ui_tick, `guest_output_paint_config_`, and classes derived from Presenter.
  - The only match is graphics_system.cpp:112/115, the virtual `provider_->CreatePresenter(loss_cb)`. It dispatches into rexui (d3d12_provider.cpp:514-516 → `D3D12Presenter::Create`).
  - Every other use outside rexui is through a pointer only: d3d12/command_processor.cpp:2199/2285 (`RefreshGuestOutput`, virtual), graphics_system.h:59, interfaces/graphics.h:59, and rex_app.h:270 / rex_app.cpp:507 (`SetupOverlays`).

**Two hazards to add to Agent 7's S4 list:**
- (6) Which COMDAT copy the linker keeps inside one binary. Suppose a non-rexui TU in rexruntime.dll (or in the exe or rexgpu-xenos) ever odr-uses an inline Presenter/D3D12Presenter function that touches moved members: a getter after :938, `AreDXGIUITicksWaitable`, an inline constructor or `Create`. The linker may then keep the non-FFX copy for rexui's own callers in the same DLL, which silently breaks the FFX build.
- (7) If LTO is ever enabled for rexruntime, the effects of the ill-formed code (IFNDR) become less predictable.

**Guard for (b):**
- Before any (b) build, re-run the pattern grep outside src/ui and include/rex/ui. It must still return only the two `CreatePresenter` virtual calls in graphics_system.cpp. Use it together with Agent 7's §(b) staging checks.
- (b) does nothing for builds without the FFX source dir, so (a) is needed either way.

**After the relaunch:**
- Re-hash the live files once Agent 6 applies the patch. Expected: registry 8BA19C5F… (4EC71328… if hunk 3 is included) and prefs 9CBE6DBF….
- If Agent 1 wants more than Agent 6's -SyntaxOnly, run `env/compile-one.ps1` on the two patched TUs (at most 2 threads).

**Applied (02:05:27).** Agent 6 copied the staged files in at Agent 1's GO, hash-guarded. Undo: `build/agent6/fix-a/apply_fix_a.ps1 -Revert`.
- My re-hash at 02:09 matches the expected values above:
  - registry 4EC71328043FA6BA… (11,224 B; fix-a plus the commit hunk; git blob 4b56537 → a299f41);
  - prefs 9CBE6DBF9CEDA62D… (4,938 B; blob 2d72eac → f02940c);
  - both keep CRLF (registry 211 CR = 211 LF, prefs 110 = 110).
- `git diff HEAD` shows exactly hunks 1-3 (registry +5/-2, prefs +3/-1). Besides these two files, `git status` in the game repo shows only the `rexglue-sdk` and `thirdparty/plume` pointers.
- Agent 6's `compile-one -SyntaxOnly` (NATIVE_GPU=1) returned rc=0 for both. The registry keeps its 4 known getenv/sscanf warnings (now :136, :138, :151, :155); prefs has none. That is enough for S3. The full compile is Agent 2's devoff3/native3 build.
- **Verdict unchanged: SAFE**, with all three hunks together.


## 13. Agent 4: §S3.2 draw.cpp fix, an early return on the failed vertex bind (pre-checks 02:50-02:58; patch review 03:10-03:20: SAFE)

The patch puts the test at the entry of `PrepareDrawGeometry` (draw.cpp:1498), not in `PrepareDrawGeometryLegacy` at 1306 as proposed. The pre-checks below were written for the proposal; "Patch review" at the end re-checks them for the actual placement.

**Proposal** (`agent4-draw-path.md`:75-100). Add the recorder's failed-bind test to the early return at draw.cpp:1306-1307:
`bool vertex_binding_failed=false; BoundShaderAddress(ShaderStage::kVertex,&vertex_binding_failed); if (vertex_binding_failed || !declaration.supported || !declaration.elements || InstancedFetchShader(key.vertex_shader_hash)) return false;`
- Purpose: stop the `Native GPU shader cache miss: hash=0x0` spam (shader_archive.cpp:432; about 760 lines/s in N2/N3), which comes from `FindDxil(0,…)` in the input-usage lambda (1363-1368).
- Sequence (SESSION2.md:1193-1200): Agent 4 validates on scratch copies → I rate → Agent 4 writes the live file at Agent 1's GO (after native3 is staged) → Agent 2 builds native3d (S3d) → Agent 8 runs n0/n2/n3 functionally (check_n_rows.py). All before 08:30.

**Pre-checks on the live file** (50AA3B1D…, the same in S2 and S3), done before the patch arrived:
1. **Where the new test is true.** With a scope, `BoundShaderAddress` (shaders.cpp:683-687) sets `failed = addresses[0] && !owners[0]` from the captured snapshot. `BoundShaderHash` returns 0 for a null owner (shaders.cpp:813-817). So exactly these draws have vertex hash 0, which is where the `FindDxil(0,…)` lines come from. They are never multi-rate or instanced-fetch draws.
2. **No side effect for any other draw.** Every caller of `PrepareDrawGeometryLegacy` runs under a `ShaderBindingsScope`:
   - `PrepareDrawWork`: scope at 1656.
   - `CaptureDrawGeometry`, called from 4729 (scope 4718), 4962 (4961), 4987 (4974) and 5137 (5120).
   - So the new call always takes the scoped branch: two array reads. The unscoped branch is never reached from here. It calls `PollPrecompiledShaders()` and reads the live registry (shaders.cpp:688-693).
3. **The recorder already drops every draw the fix rejects.** `DispatchDraw` tests the same flag at 2707-2716 (`draw_missing_vertex_shader`, return false). That is before shader resolution, PSO lookup, geometry and any draw call. All three record sites read the same snapshot as preparation:
   - N3 head: 4474-4481, `work.shaders`. `work.draw.shaders` is a copy of it (4956/4967/4977).
   - N3 follower: 4401-4405, `head.shaders`. The follower's draw is a copy of the head's.
   - N2: 5696-5699, `work->shaders` (captured at 5106; prepared at 5089).
   - Snapshots aren't written after capture. The only writes are 4944/4952/4956/4965/4967/4977/5106 (capture) and 5022/5027 (template).
4. **What changes for those draws.**
   - Before the fix, preparation carried on and usually set `geometry_ready = true` (1343). Now `geometry_ready` and `geometry_valid` both stay false.
   - In `DispatchDraw`, the only `geometry_ready` consumer before 2713 is the index metadata at 2669. With the fix it comes from a live `InspectBufferResource` (2670; buffers.cpp:600). That is the path the serial hooks always take, and every preparation miss already takes it (1474/1488/1632/1645 leave `geometry_ready` false).
   - The draw returns false either way, so `FailActiveQueries` runs as before (5699-5700, 4626, 5155, 5165). It is idempotent (queries.cpp:298-306).
   - One case differs: the live and captured index windows disagree. The draw then exits at 2675, before the state-ledger, barrier and `setFramebuffer` lines (2686-2704), instead of after them. Nothing later depends on those lines. Every draw sets its own framebuffer (2704, 2969, 3410/3413/3417), and the clear and resolve paths set theirs (3745, 3763, 5322).
5. **N3 template and chain.** Template qualification (4993-5015) reads `use_windows`, `windows` and `vertices`, which the fix leaves at their defaults. A failed-bind capture can therefore now become the capture template or a chain head (4841-4857, 4868-4901). That still doesn't change what is submitted:
   - Any reuse carries the same null-owner snapshot (4952, 5022) and is dropped too. Followers of a failed head go through `PrepareFollowerFull` (not repeatable: `head.submitted` is false) and are dropped.
   - A fresh capture during the template's lifetime gets the same snapshot. The stamps include the batch number and `ShaderRegistryGeneration` (4754-4757), and the shader pair is memoised per frame (4939-4946).
   - Only batch boundaries (`kMergedBatchDraws`) can move. Order is kept.
6. **Serial (n0/N1) and FSR3-ordered paths are unchanged.** They call `DispatchDraw` with `t_recording_draw == nullptr` (5154, 5164, 5187, 5214). `PrepareDrawGeometry` is reached only from `PrepareDrawWork` and `CaptureDrawGeometry`.
   - With `LongProbeEnabled()`, pass_profile capturing or `TemporalInputsCandidate()`, the parallel captures are skipped (5099-5100, 4689). So long-probe event counts don't change either.
7. **OFF builds don't compile draw.cpp.**
   - CMakeLists.txt:123 is in `list(APPEND LEGODIMENSIONS_SOURCES` inside `if(LEGODIMENSIONS_NATIVE_GPU)` (61-141).
   - :151 is a source property inside 150-153.
   - :668 is a `LEGO_NATIVE_GPU_FINGERPRINT_INPUTS` entry inside 181-810. That list is hashed with file(SHA256), not compiled; it starts at :582.
   - Checked with `build/agent10/s32/cmake_nesting.py`.
   - Built trees agree: snap1-off and snapB-off (`LEGODIMENSIONS_NATIVE_GPU:BOOL=OFF`) have 0 `draw.cpp.obj` and 0 `gpu_native/draw.cpp` lines in build.ninja. snap1-on has 1 obj and 3 lines.
   - In native builds, the edit also changes `native-gpu-build.txt` (the fingerprint), as expected.

**Patch review (03:10-03:20): SAFE.**

The patch is `build/agent4/s32/draw-s32.patch` (F54343258029F89A…, 787 B): one hunk, `@@ -1496,6 +1496,11 @@`, +5/-0, CRLF content lines. It adds two comment lines and a new first statement to `PrepareDrawGeometry` (live line 1498):
`bool vertex_binding_failed = false; BoundShaderAddress(ShaderStage::kVertex, &vertex_binding_failed); if (vertex_binding_failed) return false;`
- At the entry, the test also covers the planner's `FindDxil` at 1533, as well as Legacy's at 1368/1380.
- Only the failed-bind test was added. The proposal's `|| !vs` was rightly left out.
- `key` and the hash lines are untouched.

| File | sha256 | Size |
|---|---|---|
| Before: live draw.cpp = `build/agent4/s32/draw.before.cpp` = HEAD 001336f | 50AA3B1DEE61567838076EDF19CB7A5466727C3CC31BE3A80E6DCC3722D7BDD6 | 306,221 B, 5753 CRLF lines |
| After: `build/agent4/s32/draw.cpp` = `build/agent4/s32tree/DimensionsRecomp/rexlego/src/gpu_native/draw.cpp` | 5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410 | 306,557 B, 5758 CRLF lines |

`git diff --no-index` of live against after shows exactly that hunk in 1 file. No header or CMake file changes.

**The pre-checks at the actual placement:**
1. **Always the scoped branch.** Legacy is called only from `PrepareDrawGeometry` (1507, 1551). `PrepareDrawGeometry` is called only from:
   - `PrepareDrawWork` at 1667 (scope at 1656);
   - `CaptureDrawGeometry` at 4674, whose callers are all scoped (pre-check 2).

   So `BoundShaderAddress` only reads two arrays. It never calls `PollPrecompiledShaders`.
2. **The draws it skips are already dropped.** It is the same test on the same snapshot as `DispatchDraw`'s drop at 2707-2716 (pre-check 3).
3. **Before that drop, `DispatchDraw` reads geometry only at 2669** (pre-check 4, unchanged).
4. **No stale ready geometry.** `ParallelDrawWork::Reset()` (374-395) and `ClearDrawGeometry` (4678-4685) both reset `geometry_ready`.
5. **Other readers of the geometry fields:**
   - `DispatchDraw` after 2716 (3047, 3078-3079, 3220, 3593), which these draws never reach;
   - the lease at 4279, which now leases nothing for them;
   - template qualification (pre-check 5).

   No routing decision reads `geometry_ready` or `geometry_valid`. Their only readers are 337/338, 380, 1667, 2669, 3047, 3075-3076, 3220, 3593, 4674 and 4681.
6. **Cost.** `PrepareDrawWork` runs the cheap test once more at record time.
7. **Unchanged paths.** The serial, FSR3-ordered and long-probe paths are unchanged (pre-check 6).
8. **Draws with vertex shader address 0** have `vertex_binding_failed == false`, so they behave as before.
9. **OFF builds** don't compile draw.cpp (pre-check 7).

**Agent 4's tests** (I read the logs):
- **Compiles.** `build/agent4/compile/draw.s32.v2.log` and `.v3.log`: 0 errors and 77 warnings each, the same as batch 2's `draw.async.v2/v3.log`.
- **objdiff** against the batch-2 objects (`s32/objdiff-v2.txt`, `objdiff-v3.txt`):
  - only `PrepareDrawGeometry` changes size (v2 3760 → 3584, v3 3712 → 3536, −176 B);
  - .rdata grows by 21 B, which is the scratch path in `__FILE__`;
  - 794 functions in both.
- **Fixtures.** 9/26 on base and patched, with the same pass set (`code == 0` in `fixtures-s32-base/results.json` and `fixtures-s32/results.json`).
- **State shadow** (`build/agent4/state_shadow-s32/results.md`): 20/20 runs, all audits ok.
- **run_patched.** 3/3 PASS.
- **`test_parallel_geometry`** doesn't build on either live or patched (`pg-live.log`, `pg-s32.log`: 'rex/types.h' not found, stale stubs). Not evidence either way.

**After the apply:**
- Live draw.cpp must be 5EA1F357… (306,557 B, 5758 CRLF lines).
- Expected n-rows (check_n_rows.py): the `Native GPU shader cache miss: hash=0x0` lines drop sharply in n2/n3 and stay the same in n0. Draws per frame and the marks stay the same.
- **Applied and confirmed (03:40).** Agent 4 wrote the live file at 03:34:59 (`build/agent4/s32/apply_live.ps1`; backup `build/agent4/scratch/draw.before-s32.cpp`, 306,221 B). My re-hash: live draw.cpp = 5EA1F357… (306,557 B, 5758 CRLF lines), the after-file I rated; git shows ` M rexlego/src/gpu_native/draw.cpp` on HEAD 001336f. Agent 2 staged `native3d-bin` at 03:46 (exe B90DF683…, MANIFEST 368F9CE6…, every non-exe file = native3-bin).
- **n-rows on native3d: PASS (05:00-05:03; task #17 item 2, with Agent 4).**
  - Source: Agent 8's matrix `build/agent8/matrix/20261122-0452` (`bench/agent4/s3/matrix-native3d-functional.json`), runs 0452-n0-r1, 0454-n2-r1 and 0456-n3-r1.
    - Every run has bin_dir native3d-bin. The MANIFEST shows S3d draw.cpp 50AA3B1D → 5EA1F357 and fingerprint 335ff2d47268f3a1.
    - Hidden desktop, so the runs are functional only.
  - `check_n_rows.py`: n2 PASS, n3 PASS, exit 0 (`build/agent10/nb/check_n_rows-native3d.txt` and `.json`).
    - Threaded recording is ON once.
    - n2 logs "parallel workers=2"; n3 has no batches line.
    - Worker lines and thread names are as expected.
    - No new warning/error type vs n0, and no baseline type above 2× n0.
    - Clean close, exit 0.
  - hash=0x0 lines: n0 0, n2 0, n3 0 (native2: 0, 67,220, 44,968). They don't just drop: they are gone.
  - Everything else is unchanged (`nb/warntypes-native3d.txt`): in each row, every other warning/error type has the same count as on native2.

    | row | native3d | native2 |
    |---|---|---|
    | n0 | 66 lines / 18 types | 66 / 18 |
    | n2 | 66 / 18 | 67,286 / 19 (66 / 18 plus the hash0 type) |
    | n3 | 58 / 16 | 45,026 / 17 (58 / 16 plus hash0) |
  - Draws per frame and the marks (`nb/nrows-native3d.txt`):
    - The top values are 8/0/1 in all three rows (shares 65.1/19.3/15.6, 65.1/18.9/16.0 and 66.4/17.8/15.8).
    - The scene sequence is 0→1→0→1→0→1→0→8 in all three, as on native2.
    - On native2, the n2/n3 rows had a smaller 8-draw share (59.7%, 50.4%) and a shorter final scene (8,099 and 5,336 frames, against 10,509 and 11,005 now). That fits the cost of logging the spam in the last scene: the same draws, at a higher frame rate.
  - Still present and unchanged, as expected, for VS 0xAC449538 and PS 0xAC448F28:
    - "placement … missing from AOT index": 4/4/8 per shader;
    - "unrecognized … shader resource": 8/8/0.
    - The guard doesn't touch these warnings. They are what §15.1's AOT fix would address.
  - Sent at 05:04 to 1, 4, 2 and 8.

**Verdict: SAFE.**
- The fix skips preparation only for draws that `DispatchDraw` already drops, so the draws that reach the GPU don't change.
- OFF builds don't compile draw.cpp.
- Sent to Agents 1, 2 and 4 at 03:32.

## 14. Agent 11: S4 candidate `timer_queue_precise_wait` (rating only; read 03:20-03:56)

**What it is.** A new SDK cvar, `timer_queue_precise_wait` (default false, `kInitOnly`, category "Runtime"), in `rexglue-sdk/src/core/timer_queue.cpp`. When it is on, the timer-queue thread waits on the condition variable until 20 ms before the next deadline, then sleeps the rest in high-resolution slices of at most 1 ms. Off, nothing changes.

| File | sha256 (first 16) | Size |
|---|---|---|
| Live `rexglue-sdk/src/core/timer_queue.cpp` (pristine) | D8724B29C43286B0 | 12,839 B |
| Staged `build/agent11/timerq/stage/timer_queue.cpp` | 015C04A22DACC592 | 16,091 B |
| `build/agent11/timerq/stage/timerq.diff` | D07A2DC4878DAE8D | 6,570 B, -6/+73 |

**The change** (one file, read in full; staged-file lines):
- `enum class Mode {kSpin, kBlocking, kPrecise}` (:56) replaces the `blocking_` bool; `spinning()` (:200) replaces `!blocking_`. The constructor still picks kBlocking from `REX_TIMER_WAIT_BLOCKING`, else kSpin (:58-59).
- `SelectMode()` (:67-74): under `std::call_once`, if the cvar is on, `mode_.store(kPrecise, release)` and `REXLOG_INFO("TimerQueue: precise wait (timer_queue_precise_wait)")`. `QueueTimer` calls it after the stopped check and before it publishes (:318-320).
- The deadline wait loads the mode once per call (:129). kPrecise with a finite deadline calls `WaitPrecise` (:153-154). The idle wait (deadline max, :151-152) and kBlocking (:156) are unchanged.
- `WaitPrecise` (:181-198): while `!ready()`, return at the deadline; farther than `kPreciseWindow` (20 ms) out, `cv_.wait_until(deadline - 20 ms, ready)`; inside the window, unlock, `SleepPrecise(min(remaining, kPreciseSlice = 1000 µs))`, relock and loop.

**Checks**
1. **Off is unchanged.** The mode stays kSpin or kBlocking, and `spinning()` equals the old `!blocking_` on every path. The added cost is one atomic load per wait and the `call_once` fast path per `QueueTimer`.
2. **No lost wake at the switch.** The consumer thread starts at static initialization, before the cvars are parsed, so the switch happens later, at the first `QueueTimer`.
   - `SelectMode` runs before every publication. `call_once` makes concurrent first callers wait until the store is done and synchronizes them with it, so every publisher reads kPrecise and calls `signal_all_when_blocking`.
   - A consumer still inside a kSpin wait (mode loaded before the switch) sees the publication by spinning, without a notify. The next wait loads kPrecise. kBlocking→kPrecise: the consumer is in a condition-variable wait either way and is notified.
   - The dispatch thread's own `QueueTimer` (periodic re-arm, deferred list :326-328) can't be the first caller, because a timer must already have fired.
3. **WaitPrecise is correct and bounded.**
   - `ready()` is true on any new publication or `Stop()`. Each slice is at most 1 ms and `ready()` is re-checked after it under the lock, so a new timer (earlier ones included) or `Stop()` is seen at most ~1 ms late. A notify sent during a slice finds no waiter, which is harmless because of the re-check.
   - `TimerThreadMain` (:247-312) then merges the new items, fires the due ones and recomputes the deadline from the new front, so an earlier timer is not held to the old deadline.
   - The window (20 ms) is longer than the default Windows tick (15.625 ms), so the condition-variable phase can't overshoot the deadline.
4. **Fail-safe.** If the first `QueueTimer` ran before the cvars were parsed, the mode would stay kSpin (the old behaviour), and the log line would be missing. That is how to tell.

**Caveats** (to settle before anyone flips the default)
- (a) Before Windows 10 1803 there is no high-resolution waitable timer, so `SleepPrecise` falls back to Sleep(0)/yield or Sleep(1)-tick loops. Agent 11's bench run without the high-resolution timer gave spin-like gaps. Suggestion: fall back to kBlocking, or warn, when the high-resolution timer is unavailable.
- (b) Confirm that the "TimerQueue: precise wait" line appears with the cvar on and is absent with it off.
- (c) Timer jitter becomes ~1 ms: bench gap p50 1.04 ms, p99 ~6 ms (spin p99 14 ms). Timer-thread CPU drops from 26.4% to 2.2% (timeBeginPeriod 0) or 1.7% (timeBeginPeriod 1).
- (d) A publication or `Stop()` is seen up to 1 ms late.
- (e) Logging at the first `QueueTimer` is fine: the macro is spdlog-based (`include/rex/logging/macros.h:64`), and the cvar can only be true after parsing.
- (f) The wait mode changes game frame time. In Agent 8's functional matrix 20261122-0330, d0t (devoff2 + `REX_TIMER_WAIT_BLOCKING=1`) had a median of 6.5 ms / 90.9 fps against d0f's 4.19 ms / 145 fps. That was a functional pair, not a timing run. Precise mode needs a game timing A/B through Agent 8 before any default flip.

**Agent 11's tests** (from its notes, "S3 Timer Queue", L1419+): stage self-checks 17/17; clang syntax PASS with no new diagnostics; stage-bench correctness PASS in all 7 modes.

**Verdict: SAFE as a default-off S4 candidate.**
- Off is unchanged. On is correct: no lost wake, and latency is bounded at about 1 ms.
- Applying it needs Agent 1's GO. Flipping the default needs (a) handled and a game timing A/B (f).
- My message to 11 (cc 1) is held until task #17 items 1 and 2 are done, as Agent 1 asked ("after 1 and 2").

## 15. Agent 7's top 3 S4 native candidates: first safety read (04:45-05:00; task #17 item 4)

Source: `perf-notes/agent7-present.md`, "Task #13 … §4 Top 3 S4 candidates" (04:40-04:45). I read the code in the live tree: shaders.cpp is unchanged since 11-21 19:58, and draw.cpp is at S3d (5EA1F357). This is read-only; nothing was applied. Agent 7's gains come from slow-state profiles, never from timing, so each candidate needs a window-4 timing A/B before any default changes.

| # | Candidate | Output-identical? | Default | Owner |
|---|---|---|---|---|
| 1a | Add the two missing placement shaders (VS 0xAC449538, PS 0xAC448F28) to the AOT pack | **No, by design**: the dropped draws come back | Not a switch. It is a data change; rollback is the older `LEGO_NATIVE_SHADER_CACHE` | Agent 4, Agent 6 (AOT) |
| 1b | `LEGO_NATIVE_SHADER_MISS_CACHE=1` stopgap | **Only under conditions 1-7 below**; otherwise not | OFF | Agent 4 (shaders.cpp) |
| 2 | Per-frame call-count probe for Main's scene walk | Not shipped: compiled out by default | Compiled out | Agent 7 |
| 3 | `LEGO_NATIVE_THREADED=1` | Frames: should be (same draws, same order). Guest-visible timing: no | OFF until window 4 | Agent 4, Agent 7 |

### 15.1 Missing placement shaders: the AOT fix (1a)

**Checked in the native2 logs:**
- n0 (`0030-n0-r1`): 8× "unrecognized pixel shader resource 0xAC448F28" and 8× "… vertex … 0xAC449538", plus 4× each "placement … missing from AOT index" (backing 0xED23D3E0 and 0xED23D540).
- n3 (`0208-n3-r1`, full preparation, no BindShader): 8× each "placement … missing".
- These are cap counts. One shared counter, `g_shader_warning_count`, caps all three warnings: "cannot adopt" < 16 (shaders.cpp:262), "missing from AOT index" < 16 (:297) and "unrecognized" < 32 (:571). These two shaders use up the whole budget in their first 16 misses. So the real miss count is higher, and **a later miss of any other shader would not be logged**.
- Likely link to §13: the `hash=0x0` spam in n2/n3 comes from draws whose vertex bind failed, and 0xAC449538 is the only failed vertex bind that gets logged. Unproven because of the cap. Item 2 (native3d n-rows) shows whether §13's early return removes it.

**Must prove:**
1. The capture is stable: one container per shader, and the same `container_hash`/`physical_hash` in the `missing_placement_shader_identity` probe events of two functional runs with `LEGO_DUMP_MISSING_SHADERS=1` (shaders.cpp:146-207; Agent 8's slot).
2. tools/gpu-aot compiles both, for every specialization value used, with no new warnings. The rebuilt `lego-dxil-cache.cpp` differs from the current one only by the two entries and their index rows.
3. Both hit at runtime: no "missing from AOT index" or "unrecognized … shader resource" lines for the two addresses, no `draw_missing_vertex_shader`/`draw_missing_pixel_shader` probe events for them, and no new shader-creation or PSO errors.
4. **The user checks it visually (window 4).** These draws have never been rendered natively, so a wrong translation would show up as new garbage on screen, not as a missing effect. Every native2 run hits them, so they are in the title/attract scene.
5. Change the n-row rule for this patch. Draws/frame will **rise** in the scenes that use the shaders, so "draws/frame unchanged" becomes "`draw_missing_*` = 0, draws/frame ≥ before, marks otherwise unchanged".
- Rollback: CMake keeps the older cache selectable (`LEGO_NATIVE_SHADER_CACHE`, rexlego/CMakeLists.txt:264-266, "keep older caches for rollback").
- Gate it as a content fix (functional check plus the user's visual check), not as a perf switch.

### 15.2 The miss-cache stopgap (1b): `LEGO_NATIVE_SHADER_MISS_CACHE=1`, default OFF

It can be output-identical to today's native, but only if all of the following hold:
1. **Key:** (stage, guest_address, container_address) **plus the pack generation** (`PrecompiledShaderPackGeneration()`). A trigger-loaded pack can add shaders at runtime (shaders.cpp:394-450 then repairs the registry and rebinds), and no cached miss may outlive that.
2. **Validity:** the same CPU-memory stamp rule as the hit path (`PlacementShaderUnchanged`, shaders.cpp:209-241), over every byte `FindShaderByMicrocode` can read. That function hashes up to each bucket entry's `microcodeSize` (shader_archive.cpp:300-358), so the stamp span is `[container, container + max microcodeSize]`. Prove that the max AOT microcodeSize is ≤ 64 KiB, as Agent 7 assumes, or stamp up to the real max.
3. **readable_size is an input.** Entries larger than it are skipped (shader_archive.cpp:307 and :350). A commit, protect or decommit/recommit on those pages with no guest write would change today's result but not the cached one. Either find a heap change counter, or prove that decommit/recommit invalidates the stamp and document the protect-only residual.
4. **No per-frame fallback** when no stamp is available (`code_stamp_unavailable`). Today a miss is retried on every bind. If the microcode appears mid-frame, a one-frame cache drops draws that today would be drawn. Don't cache misses that can't be stamped. There is precedent but not identity: the hit path already tolerates 16 frames without a stamp (:214-216), and full preparation captures each shader pair once per frame (draw.cpp:4943-4951).
5. **Logs:** a cached early return (before :288) must still do the `g_shader_warning_count` fetch_add and print the identical warning while the count is under the cap; cache the prefix and the 4 words with the entry. Otherwise the shared cap's warning mix changes and logdiff flags it. `CaptureMissingPlacementShader` already dedupes by container hash, so a cached miss can skip it.
6. **Locking:** both AdoptShader callers hold `HostDevice::LockRecording()` (BindShader :559/:562; `CaptureShaderBindings(v,p)` :624/:625). Keep the cache under that lock; it needs no new lock.
7. **Size and invalidation:** cap the entries (cf. the 256 capture cap), and drop an address's entry in `InvalidatePlacementShader` (hooks_shader.cpp:65 and :73) together with its registry entry.
8. It goes against the code's own rule. shader_archive.cpp:341-344 says "never cache across guest writes or bind calls". The stamp covers the writes; Agent 4, as owner, should sign off on dropping the bind-call part.

- **Tests:** an ON vs OFF functional pair should give logdiff NEW 0 / MORE 0 (warning lines included), the same draws/frame and marks, and the same `unrecognized_shader` probe events. Then a timing A/B in window 4.
- **Verdict:** with 1-7 it is output-identical. Without 4 it is not (up to 1 frame per microcode change), so it must stay OFF and serve only as a measurement switch.
- If 1a lands first, 1b is moot because there are no misses left. Its only use is to measure the miss cost before 1a.

### 15.3 The Main walk probe (candidate 2)

- It is a diagnostic, not a fix. Build it like area_watch, tt_lock_trace and icon_probe: **compiled out by default**. hookset shows their REX_HOOK targets unhooked in the normal build, so the timing builds keep 181 hooks and the hot recursive `sub_82F0CCD8` path gets no extra branch. The probe only counts: it calls through to the original body with ctx unchanged. Functional runs only, never timing.
- Rule out the frontend confound first: a-prof had the frontend on and n-prof had it off. One native `-Profile` pair, frontend on vs off, needs no code.
- One more cause to test with the probe: occlusion queries are the walk's only host→guest feedback. queries.cpp returns real hardware results with asynchronous readback ("no fabricated result", :53). The dropped placement draws (15.1) add 0 samples to any query that brackets them. If native's query outcomes differ from devoff's, the guest's visibility decisions differ, and so does the per-frame walk. The `query … complete draws= samples=` line (queries.cpp:197, when it is logged) gives the native side.

### 15.4 `LEGO_NATIVE_THREADED=1` (candidate 3)

- **It is already in the matrix.** The native3d n2 and n3 rows both set `LEGO_NATIVE_THREADED=1` and `LEGO_NATIVE_PREPARE_THREADS=2` (n2 adds `SNAPSHOT_STATE`, n3 adds `FULL_DRAW_PREPARATION`; `bench/agent4/s3/matrix-native3d-functional.json`). So item 2's runs are the functional "does it boot, what does render keep" run that Agent 7 asks for. A plain THREADED=1 row is optional, if the slot has time.
- **Must prove before any default change:**
  1. Item 2 passes on native3d: hash0 ≈ 0 in n2/n3 (native2: 67,220 and 44,968), draws/frame and marks equal to n0, and no new warning type.
  2. Same frames: the same draws in the same order with the same state. The n-row marks are a proxy; a per-frame draw-count diff from native-frames.csv against n0 is stronger.
  3. Guest-visible sync: query results and GPU→CPU readbacks are complete before the guest reads them (Agent 7's report (f): guest fence and idle waits drain the whole GPU). Later recording can delay query completion, so the guest sees "not ready" for longer. That is a guest-visible timing change, so the mode is not output-identical in the strict sense. Compare per-frame query outcomes, ON vs OFF.
  4. The capture worker. `CaptureShaderBindings(v,p)` calls `PlacementShaderUnchanged` without the recording lock (shaders.cpp:621-623, "registration hooks drain the capture first"), and that call mutates the resource (validated_frame, hashed_frame, code_stamp). Prove that all callers (draw.cpp:4949, :5111, :5190, :5217) run on the single capture worker and never on the PREPARE_THREADS workers, so it can't race BindShader or `RefreshBoundShaderResources`.
  5. Shutdown and device loss while work is queued.
- It stays OFF until window 4, which needs the user's timing A/B and visual check.

## 16. Agent 11: S4 candidate `host_execution_throttling_optout` (rating only; read 04:54-05:00)

Source: `perf-notes/agent11-kernel.md`, "S4 staging (task #19)", parts 1-2 (L1648-1773). The staged files are in `build/agent11/pthrottle/stage/`: `pthrottle.diff` (sha256 75756E8DCB045A91…, −4/+37, 7 hunks, 3 SDK files). I re-hashed at 04:56: all three live files are still pristine, so the diff applies as staged.

| file (`DimensionsRecomp/rexglue-sdk/`) | live = pristine | staged |
|---|---|---|
| `include/rex/threading_timing.h` | 043FFE289935 | 72EAB2800912 |
| `src/core/threading_win.cpp` | C0EBD864B9D2 | 8A7F7E24289A |
| `src/system/runtime.cpp` | 306B692BC091 | 27F4BC105FD3 |

**What changes**
- threading_timing.h: a new field, `keep_execution_speed_in_background = false`.
- threading_win.cpp:
  - `KeepTimerResolutionInBackground()` becomes `OptOutOfPowerThrottling(ULONG control_mask)`. StateMask stays 0.
  - A new constant, `kPowerThrottlingExecutionSpeed = 0x1`.
  - `ConfigureHostTiming` makes one combined call when both opt-outs are on, and retries 0x1 alone if that call fails. It logs an info or warn line only when the new field is set.
- runtime.cpp: the cvar `host_execution_throttling_optout` (default false). `Runtime::Setup` reads it once, under `!tool_mode_` (staged :145-152). The game always reaches `ConfigureHostTiming`, so the new cvar also works on its own. Tools never call it.

**My checks**
1. **OFF is unchanged.** Every new path is gated by `config.keep_execution_speed_in_background`, and only the cvar sets it (default false).
   - With only the timer opt-out on, the mask is 0x4: the same single call and the same debug line as today.
   - With both off, there is no call.
   - Agent 11's read-back test agrees: scenarios a, a1, a2, b, b1 and i0 are identical to pristine.
2. **One call site.**
   - The live tree has one `SetProcessInformation(ProcessPowerThrottling)` site (threading_win.cpp:155), and the renamed function has one caller (:229).
   - The game repo, the harness and Agent 8's runner make no such call (`build/agent10/nb/pgrep.py` over DimensionsRecomp, harness and bench). The only other users are Agent 7's microbench and Agent 11's test tools, which run as separate processes.
3. **Replace semantics.** A Set replaces the whole process state (Agent 11's tests f and h, and probe step 6, on build 26300). So one combined call (0x5) is the right design: with two calls, only the second would survive.
4. **Fallback.**
   - If 0x5 fails (Windows 10 rejects the Windows 11 timer flag with error 87), the code retries 0x1 alone.
   - `background_optout` stays false in that case, so "Host timer resolution set to … (background opt-out off)" stays truthful.
   - It never retries 0x4 alone after a failed 0x5. That is fine: 0x1 (Windows 10 1709) predates 0x4 (Windows 11), so no OS accepts 0x4 but rejects 0x1.
5. **Logs.** ON adds exactly one line:
   - info "Execution speed power throttling opt-out on"; or
   - warn "… failed (0x…)", before Windows 10 1709 or when the export is missing (tests j and j1: 0x7F).
   - logdiff will report the info line as NEW in an ON vs OFF pair. That is expected, so allow it for ON arms.
6. **Lifetime.** The setting is process-scoped. It is made once in Setup, on the main thread, before any guest thread starts. `RestoreHostTiming` makes no call, as today for 0x4, so there is nothing to undo at exit.

**Caveats**
- (a) **The effect is unproven.** The read-back shows the policy, not what the scheduler does with it. Before any default flip, Agent 11's hidden-desktop ABBAAB pair (part 2) must show that the slow state goes away. If it doesn't, drop both the cvar and the runner switch.
- (b) **Power.** ON keeps a backgrounded game at full QoS, which means more power and heat on laptops. That is the point, but turning it on by default would be a user-facing policy choice. Keep it OFF by default, as a player opt-in.
- (c) **Runner proposal (part 2).** The game's own Set (with `host_timer_throttling_optout=true`) replaces any earlier state (test h). So an external Set must be a read-modify-write that comes after `Runtime::Setup`. The proposal already does both: it applies at the first frame.
- (d) **Labels.** fps from runs with and without the opt-out aren't comparable. Label the arms.

**Verdict: SAFE as a default-off S4 candidate.** Applying it needs Agent 1's GO, and flipping the default needs (a).

## 17. Agent 7's S4 design proposals R1 stage 1 (split submits) and R2 (redundant-command filter) (design level only; read 05:39-05:45)

Source: `perf-notes/agent7-present.md`, "Task #22" §4 (L286-332). Nothing is staged. These are SDK files on the Xenos command-processor (devoff) path: `src/graphics/d3d12/command_processor.cpp` and `deferred_command_list.{h,cpp}`. The native path (`gpu_native/`) has its own device and submissions; draw.cpp never touches `deferred_command_list_` or `EndSubmission`. I checked Agent 7's line references in the live SDK and they all hold: :98, :2556-2561, :3180, :3926, :4122-4154, :4219, :4228, :4230, :4245-4248, :4324, :5715, :5771, deferred_command_list.h:646 and .cpp:241.

**R1 stage 1, `d3d12_submit_split_kb` (0 = off): SAFE as a default-off test bed, under conditions 1-6.**
- **Why the reuse holds.**
  - `EndSubmission(false)` never closes the frame: `is_closing_frame = is_swap && frame_open_` (:4219).
  - `BeginSubmission` on the next draw only reopens the submission, because `frame_open_` is still set. It resets the deferred list and every cached binding (viewport, scissor, blend factor, stencil ref, pipeline, root signature and root bits, heaps, topology), plus the RT cache, primitive processor and texture cache submission state (:4122-4154). So the next draw re-binds everything.
  - Per-frame state is untouched: the cbuffer maps and the pool reclaim happen only when a frame opens (:4156-4194).
  - The same path already runs mid-frame at :2559, :3180, :3926, :5715 and :5771. Agent 7 finds, though, that in this title it rarely fires (the frame arrives as one primary buffer), so the path is existing code but lightly exercised here.
- **Conditions.**
  1. The check runs only on the GPU Commands thread, at the tail of `IssueDraw`/`IssueCopy` (and of a dispatch, if any). It runs after the command and its barriers are fully recorded. Never mid-packet, and never inside the swap or `RefreshGuestOutput`.
  2. Guard: `cvar > 0 && submission_open_ && frame_open_ && CanEndSubmissionImmediately() && !active_occlusion_query_.valid && !scratch_buffer_used_ && list size >= N KB`.
     - The query guard matters: :4230 would otherwise end an active query early.
     - The scratch guard turns the :4228 assert into a skip.
  3. If `EndSubmission(false)` returns false (allocator creation failed, :4203-4211), the submission stays open. Carry on recording and don't call `BeginSubmission` by hand.
  4. Read the cvar once at init (kInitOnly, cached in a member), so OFF costs one compare per draw. OFF must be today's code.
  5. Native builds: leave it OFF unless tested separately, since this is devoff-path work. A native build's command processor may still see some guest work.
  6. Expect no win from stage 1 alone. Each split adds a Close plus `ExecuteCommandLists` (Agent 7: 0.54 ms/f for one per frame). Its value is validating the split rules for stage 2. Stage 2 (the submit worker) is not rated here; it is the risky part.
- **Tests (Agent 7's 1-3, plus two):**
  - Count the splits that were suppressed by the query guard in an occlusion-query scene, and by `CanEndSubmissionImmediately` while the PSO cache is cold.
  - Run one pass with `d3d12_readback_memexport=true`.
  - A logdiff of an ON arm against OFF should be clean. Splits add no log lines unless Agent 7 adds a counter line; if so, allow it.

**R2, redundant-command filter in `DeferredCommandList`: step 1 SAFE; step 2 SAFE-IF as a default-off candidate (conditions a-e). Low priority: the ceiling is −0.1 to −0.2 ms/f.**
- Step 1 (per-type counters, compiled out by default) has no OFF cost and no effect on output.
- Step 2 conditions:
  - (a) **Pure state setters only:** root constants, root CBV/SRV/UAV addresses, descriptor tables, PSO, topology, index/vertex buffers, RTs/DSV, viewports, scissors, blend factor and stencil ref.
    - Never filter barriers. A repeated transition is a bug elsewhere, and a UAV or aliasing barrier is a sync point, not a state.
    - Never filter clears, copies, draws, dispatches, queries, resolves or discards.
    - Agent 7's step-1 list includes "single-barrier `ResourceBarrier`" as a counter. That's fine to count, but it must not become a filter target.
  - (b) **Resets.**
    - Reset everything on `Reset` and at the start of `Execute`.
    - Reset descriptor tables on `SetDescriptorHeaps`.
    - Reset all root arguments on every `Set{Graphics,Compute}RootSignature` call, including a redundant one. D3D12 keeps bindings when the same signature is set again, but resetting is cheap and removes a rule to get right.
    - Keep graphics and compute root state separate. A PSO change does not reset root arguments.
  - (c) **Compare the full payload:** offsets and all root-constant values, and whole arrays with their counts for vertex buffers, RTVs, viewports and scissors, including the DSV handle.
  - (d) Any command that reaches the real list outside the deferred stream resets the filter, and so does a split (R1) through `Reset`.
  - (e) Tests: the D3D12 debug layer must show no new messages (it reports unset root parameters at draw time, which catches a bad reset rule), plus a frame comparison and R1's steps 2, 3 and 5. Go to step 2 only if step 1's counters show enough repeats.

**Verdict.** R1 stage 1: **SAFE** as a default-off test bed, under conditions 1-6. R2: step 1 **SAFE**; step 2 **SAFE-IF** (a)-(e). Both need Agent 1's GO to stage and are user-planned S4 items like the rest. Not sent separately; they go in the ~07:30 summary to Agent 1 (cc 7).

## 18. Agent 4: §S3.4 miss-cache stopgap `LEGO_NATIVE_SHADER_MISS_CACHE=1`, default OFF (read 05:48-05:57; rated against §15.2)

**Staged, not applied:** `build/agent4/s34/shaders-s34.patch` (328BDAE19ABFC6C8…, 14,441 B). It touches one file, `rexlego/src/gpu_native/shaders.cpp`: E87A2DEE43D38D8E (41,029 B) → 9567FE3F3B63637D (51,261 B).
- Live = `s34/shaders.before.cpp` = the `s34base` copy, unchanged since 11-21 19:58. The patched file = the `s34tree` copy.
- Hunks (line numbers in the patched file): a 202-line block after `CaptureMissingPlacementShader` (L209-410); AdoptShader replay L487-489, arm L497-500, log and remember L506-514; `InvalidatePlacementShader` L929; `PoolCopyMayTouchShaders` L962-987; `InvalidatePoolCopyShaders` L1012; `ResetShaderResources` L1123.
- Agent 4's compile checks: v2 and v3 (the game's flags) both rc=0, with 2 warnings, the same set as the control (`s34/warn-diff.txt`, `run_compiles*.log`). `objdiff-v2.txt`: +23.7 KB of sections.

**Default OFF: SAFE, with no behaviour change.**
- `ShaderMissCacheEnabled()` reads the env var once ("0" disables). It is forced false when `LEGO_DUMP_MISSING_SHADERS` is set, using the same "non-empty" test as `CaptureMissingPlacementShader` (L148-155).
- When OFF:
  - the replay and the arm are skipped (L488, L499), so `miss_arm.armed()` is false and nothing is remembered;
  - `ForgetShaderMisses`, `ClearShaderMisses` and `ShaderMissEntries` return before taking any lock;
  - `ForgetShaderMissesOverlapping` gets an empty list;
  - `PoolCopyMayTouchShaders` keeps `key[1] = 0`, because the miss generation stays 0, and marks nothing extra.
- The warning moved into `LogMissingPlacementShader` without changing what it prints: the same format string, stage word, prefix and 4 words. The `readable_size >= 12/16` guards are still conditional, so nothing is read past readable_size, and it uses the same shared counter and cap.

**ON: output-identical. §15.2 conditions 1-7 are met, and 8 is met because the owner wrote it.**
1. **Key.** Per stage, `guest_address << 32 | container_address`. The entry stores the pack generation, and `ShaderMissValid` requires it to be unchanged. `ArmShaderMiss` arms only at generation 0, so no miss is cached once a pack could add shaders. (The pack is consulted only when the generation is not 0, shader_archive.cpp:127 and :303; publishing a pack bumps it, :255.)
2. **Validity.** It uses the hit path's stamp: `WatchCpuMemory`, armed before the lookup, and `CpuMemoryUnchanged` on replay (memory_watch.cpp:99-149).
   - The span is the largest `microcodeSize` in the (stage, prefix) bucket, at least 16 (`ShaderMissSpan`). That covers every byte the lookup reads, because `FindShaderByMicrocode` visits only entries with the same prefix and stage and hashes each one up to its `microcodeSize` (shader_archive.cpp:339-356). This is better than relying on the 64 KiB assumption.
   - After the lookup, a prefix re-check (L118) drops a miss whose bytes changed before the arm, since its span came from the wrong bucket. A write after the arm dirties the stamp (L130).
3. **readable_size.** The entry is armed only when `readable_size >= span`, so no candidate was skipped for size, and a larger readable_size later can't add one.
   - A smaller one: Decommit and Release fire the physical callbacks (SDK xmemory.cpp:2098 and :2122). That bumps the page versions, so the entry becomes invalid.
   - **Residual (log only):** Protect fires the callbacks only when the new protection is writable (:2134). If the guest protects the pages to no-read and the bytes are unchanged, the entry stays valid.
     - Today that bind returns nullptr at `readable_size < 8` with no warning. With the cache it returns nullptr with the warning, and the counter moves one step.
     - The return value is the same. It would need the guest to make bound shader microcode unreadable. Accepted and documented.
4. **No stamp, no entry.** `armed()` means the stamp is non-empty. `WatchCpuMemory` returns an empty stamp when both watches are off (for example `LEGO_NATIVE_NO_MEMORY_WATCH`), or when the span isn't committed and readable, or isn't physically contiguous (memory_watch.cpp:77-92, :101-112). There is no frame-based fallback.
5. **Logs.** A replay does the same `g_shader_warning_count` fetch_add and prints the same line from the cached prefix and words. All 4 words are real, because span ≥ 16 and readable_size ≥ span when the entry was armed.
   - BindShader's later "unrecognized … shader resource" warning and its `unrecognized_shader` probe (L771-782) are untouched, so the shared counter runs through the same sequence.
   - Capture is always off when the cache is on, so skipping `CaptureMissingPlacementShader` changes nothing.
6. **Locking.** The patch adds a new leaf lock, `g_miss_cache_mutex`, instead of relying on the recording lock. Accepted:
   - nothing is acquired while it is held: `CpuMemoryUnchanged` is lock-free (memory_watch.cpp:131-149; the epoch cache goes through atomic_ref), and the pack generation is an atomic load;
   - `WatchCpuMemory`, which takes the global critical region, runs outside it, and `LongProbeEvent` runs after it is released;
   - every caller already holds `LockRecording` (BindShader L766, CaptureShaderBindings L831, InvalidatePlacementShader L927, PoolCopyMayTouchShaders L971, InvalidatePoolCopyShaders L993, ResetShaderResources L1107). So the mutex is uncontended on the serial path, and still correct if the gate is shared in preparation mode;
   - entries are immutable once inserted (`shared_ptr<const>`) and are validated outside the lock.
7. **Size and invalidation.**
   - The cap is 256 entries over both stages. When it is full, invalid entries are swept; if it is still full, the insert is skipped and the miss just takes the full path.
   - `InvalidatePlacementShader` forgets the address (L929), and `ResetShaderResources` clears everything (L1123).
   - Pool copies drop overlapping entries (L1012), and the footprint index marks the miss spans (L981-985).
   - Both pool-copy paths also bump the page versions before their memmove (hooks_buffer.cpp:343 under `LockRecording` at :306; the ordered path at :197), so the stamp alone would catch them. The extra `InvalidatePoolCopyShaders` calls caused by the marked pages only cost time: nothing is retired and nothing is rebound.
   - The bump-before-memmove design relies on readers being serialized with the copy (the recording lock, or the capture-order worker). The hit path makes the same assumption (L433-441); this patch adds nothing new there.
8. The cache sits above `FindShaderByMicrocode` and leaves that function's "within this lookup" rule as it is; the stamp takes over from the "never across bind calls" part. Agent 4 owns both files and wrote the patch, which counts as the owner's sign-off. Optional: a one-line pointer in the comment at shader_archive.cpp:341-344.

**Expected ON-only output:** up to 64 `shader_miss_cache_insert` long-probe events (L144-148). They are allowed in the ON/OFF logdiff; nothing else may differ.

**Perf caveats for the window-4 A/B (not safety issues):**
- Arming write-protects the span (`EnablePhysicalMemoryAccessCallbacks`), so the first guest write to those pages after each arm faults once. The hit path's stamps cost the same.
- If a missing shader sits in a large bucket, for example the zero-prefix one with thousands of entries, its span can exceed `readable_size` or cross a page that isn't physically contiguous. Then nothing is armed, and the switch does nothing for that shader. So the ON functional run must show `shader_miss_cache_insert` for both missing shaders (VS 0xAC449538 and PS 0xAC448F28; backing 0xED23D3E0 and 0xED23D540 in native2), or there is nothing to time.

**Tests before any default change:**
- An ON vs OFF functional pair in Agent 8's slot:
  - logdiff NEW 0 / MORE 0, apart from the insert probes;
  - equal warntypes counts (placement missing, unrecognized);
  - the same draws/frame and marks;
  - the same `unrecognized_shader` events.
- Then the window-4 timing A/B.
- If 1a (the AOT fix) lands first, this switch has nothing left to cache (§15.2).

**Verdict: SAFE** at the default (OFF). With ON, the output is identical apart from the protect-only log residual (condition 3) and the insert probes. Applying it needs Agent 1's GO.

**§18 addendum (06:18): Agent 4's review doc and its three asks.** Doc `build/agent4/s34/miss-cache-review.md` (sha256 7AA19D11F71D4C2D…, checked). Same patch (328BDAE1…) and the same patched shaders.cpp (9567FE3F…).
- **objcheck (the v2 and v3 ISAs agree):**
  - 383 functions are identical;
  - 7 differ only in `__LINE__` constants, each of which maps through the patch;
  - 12 have code changes. These are exactly the patched functions plus their EH funclets: AdoptShader, InvalidatePlacementShader, PoolCopyMayTouchShaders, InvalidatePoolCopyShaders, ResetShaderResources and the static initializer;
  - 55 are added (the helpers and their instantiations);
  - 3 are removed: one `log_` instantiation, replaced by one with the same value types, the same order and the same format string;
  - there are 4 new .rdata strings and none removed.

  This supports "OFF = today" at the object level: I had already read every changed function in §18.
- **Ask 1 (rating):** unchanged. SAFE at the default; with ON, the output is identical under §15.2 1-8, apart from the residuals below.
- **Ask 2 (item 6, the leaf mutex):** accepted, as in §18 item 6. Agent 4's lock-order statement matches my read: registry → miss only, and the mutex is never held across a guest query, a watch call or another lock.
- **Ask 3 (item 8):** signed off.
  - The rule at shader_archive.cpp:341-344 ("never cache across guest writes or bind calls") protects the per-lookup `hashes_by_size` memo, which has no invalidation.
  - The patch leaves that memo alone and caches one level up. That cache has explicit validity covering every input of `FindShaderByMicrocode` at pack generation 0:
    - the bytes: the stamp over the exact per-bucket span;
    - the stage: part of the key;
    - `readable_size`: at least the span when the entry is armed;
    - the pack: the generation. `FindShader` consults the pack only when the generation is not 0 (:127).
  - Optional, not a condition: a one-line pointer in that comment the next time shader_archive.cpp is edited.
- **Residuals, as numbered in Agent 4's doc:**
  - **1(i)** is my condition-3 residual.
  - **1(ii)** is the same class. After a protect-only change leaves `readable` at 8-15 bytes, today words 2-3 print as 0 and the cache prints the cached words.
    - It changes log content only, the bind returns the same nullptr, and it can affect only the first 16 warnings.
    - It needs a no-read protect on the page that follows the container's first 8 bytes. Both missing shaders sit mid-page in native2's layout (0xED23D3E0, 0xED23D540).
    - Accepted.
  - **2 (the pool-copy window):** both copy paths bump the page versions before the memmove (hooks_buffer.cpp:197→198 and :343→344).
    - So the window is a reader that arms between the bump and the end of the memmove.
    - Serialization excludes that reader: LockRecording at :306, and capture order on the ordered path. The registry's `code_stamp` relies on the same assumption (§18 item 7, last bullet).
    - Accepted: the cache is no weaker than the registry.
  - **3 (the page-granular stamp):** it can only cause false invalidations. Accepted.

## 19. Agent 12's S4.7: the upstream race in `PhysicalHeap::Protect` (confirm or refute; read 06:00-06:41)

**Ask.** Agent 1 asked for a quick confirm or refute of Agent 12's S4.7 (`perf-notes/agent12-io-memory.md` L828-842). Source level only. SDK `src/system/xmemory.cpp` at HEAD c5fe668; no batch touches it. Line numbers are xmemory.cpp unless marked.

**Verdict: CONFIRMED, both forms.** Form 1 is a real race. Form 2 is real too, and broader than a race: a pre-existing gap that needs no concurrency. Both are upstream code.

**The path.** `PhysicalHeap::Protect` (L2128-2144):
- takes G, the global critical region, at L2130;
- only for a protect with write access: `TriggerCallbacks(std::move(global_lock), …, is_write=true, unwatch_exact=true, unprotect=false)` at L2135. The lock moves into the call, so G is released when TriggerCallbacks returns;
- then runs `parent_heap_->Protect` (L2138) and `BaseHeap::Protect` (L2143) without G. Each takes only `heap_mutex_` (`AcquireHostPageReconcileLock`, L968-973, is empty when the page size ≥ the host page) and sets the host access at L1772. `ToPageAccess` (L930-941) maps any writable protect, WC included, to kReadWrite;
- a protect without write access keeps G throughout.

**Form 1, RW→RW (the game's Lock): confirmed.**
1. Main: TriggerCallbacks runs the SharedMemory and PrimitiveProcessor callbacks (the range becomes invalid), clears the watch bits (L2416-2427) and releases G.
2. In the window, GPU Commands requests the range. `RequestRanges` collects the invalid pages under G (base `shared_memory.cpp` L426-476). `UploadRanges` calls `MakeRangeValid` (base L303-336), whose `EnableAccessCallbacks` (L2157-2271) protects the page read-only and sets its bit under G.
3. Main: the view's host protect (L1772, reached through L2143) sets the page to RW. The window also spans the parent's VirtualProtect (L2138), so it is µs-scale.

The page is now valid, its bit is set and the host page is writable. The game's next writes don't fault, so the GPU keeps the old copy.
- **It persists.** EAC skips pages whose bit is set (L2238-2239), so later uploads don't re-arm it. Only a TriggerCallbacks over the page heals it: the next old-path Lock of the range (≈1 frame for a range locked every frame), a fault on a neighbour page whose widened unwatch covers it (L2353-2377), or Decommit/Release.
- **Odds.** The upload's EAC has to land inside that window. Rare, but the GPU thread uploads exactly the dynamic ranges the game locks, so a long session can hit it. Symptom: stale vertex or texture data until it heals.

**Form 2, ReadOnly/NoAccess→RW: confirmed, and not a race.**
- EAC never watches pages whose guest protect is NoAccess or ReadOnly (L2228-2239; the comment at L2231-2234 says so on purpose: real access violations are wanted there). When such a page becomes writable, TriggerCallbacks finds no watched page and returns without invalidating (L2306-2323).
- So a page that became valid while it was ReadOnly stays valid and unwatched once it is writable. All later guest writes are missed, with no concurrency involved. The comment in `PhysicalHeap::Protect` ("only invalidate if making writable again") shows that this case was meant to invalidate.
- The game's Lock protects are RW→RW (Agent 5). The exposure is the game's own protects that add write access to ReadOnly pages (NtProtectVirtualMemory, MmSetAddressProtect), if it makes any. A protect log would count them.

**Fixes.**
- **(i) Keep G across both host protects.** Use a TriggerCallbacks variant that hands the lock back, and run L2138 and L2143 under it. This closes form 1, because EAC can't run in between. G → `heap_mutex_` is the legal order (L1746-1748). Cost: G is held across two VirtualProtect calls on write protects; non-write protects already hold it.
- **(ii) Re-protect the watched pages after the host protect.** Not enough on its own: a guest write between L1772 and the re-protect is missed, because the page is already valid.
- **Form 2** needs its own fix: invalidate on any protect that adds write access, whether or not a page is watched. That can cost extra re-uploads; rate it separately.
- These are correctness fixes, not output-identical. Gate them like content fixes: a functional ON/OFF pair (logdiff, draws/frame), and no lock-order asserts.

**C1 (§21).** C1 keeps the watch on kept ranges, so no window opens for them. But it also removes today's healing: the next Lock takes the fast path, so a form-1 state left by an old-path protect persists. This is residual R1 in §21. I recommend landing fix (i) with C1.

**Read.** xmemory.cpp L560-582, L930-979, L1713-1799, L2128-2144, L2157-2271, L2273-2430; base shared_memory.cpp L277-336, L426-575. No runs.

## 20. Agent 12's #27: S4 "u" diagnostic `shared_memory_upload_hash_log`, default OFF (read 06:33-06:41)

**What it is.** Logging only. With the cvar on, every successful, non-empty `D3D12SharedMemory::UploadRanges` call hashes (XXH3-64) the guest copy of each page it just uploaded and compares that hash with the one from the page's previous upload. It prints one info line per frame with uploads. Purpose: measure u, the share of re-uploads that copy unchanged bytes, as an upper bound for P1 at page and at 256 KB block granularity (`build/agent12/s4-diag/DESIGN.md`).

**Inputs checked (06:36-06:39):**
- `upload-hash-log.diff`: sha256 D2905301…, 7,629 B, 179 lines, 4 hunks; **0 removed lines**, 145 added.
- Live SDK `src/graphics/d3d12/shared_memory.cpp` = `orig/` = B120D07C… (14,514 B). Git-clean, last commit 71782a3. `git apply --check` passes.
- `new/` (BB0838CE…, 20,888 B) = live + diff exactly: `git diff --no-index orig new` regenerates the staged hunks byte for byte. So Agent 12's syntax check (pristine vs staged, no new diagnostic) ran on the file the diff produces.
- Nit: DESIGN.md gives SDK HEAD 90e7ccd, but HEAD is c5fe668 (Agent 1's S3 commit). The file is the same in both, so this changes nothing.

**Agent 12's checklist:**
1. **OFF path: confirmed.**
   - Hunks 1-3 are outside function bodies: two includes, the cvar definition, and an anonymous-namespace struct with 3 helpers.
   - Hunk 4 adds only the `if (REXCVAR_GET(shared_memory_upload_hash_log)) {…}` block, between the end of the upload loop (L337) and the final `return true` (L338). The empty-call return (L306-308) and the error return (L322-325) are untouched.
   - Runtime cost: `REXCVAR_GET` calls `FLAGS_…_storage_()` (cvar.h:343), which returns a function-local static bool with a constant initializer, defined in the same TU. So it is inlinable and has no guard: one load and one untaken branch per successful non-empty call.
   - Static effects: one more `FlagRegistrar` entry (cvar.h:361-376, lifecycle kHotReload), so the flag appears in cvar listings and config dumps. The `UploadHashLog` object (~8.5 KiB of arrays, an idle mutex, 2 empty vectors) is constructed at startup and never touched. `rex/hash.h` defines `XXH_INLINE_ALL` (L20-21) before including `<xxhash.h>` (L28), so XXH3 stays TU-local and nothing changes at link time.
2. **Bounds: confirmed.**
   - `page_hashes` has `kBufferSize >> page_size_log2` entries (512 MB / 4 KB = 131,072, so 1 MiB); `page_hashed` has 2,048 u64 (16 KiB).
   - `UploadHashLogPages` returns when `page_first >= page_total` and clamps `page_count`. For a clamped page, the block index `(page << log2) >> 18` is < 2,048 = `kBlockCount`.
   - The hash reads `TranslatePhysical(first << log2) + page_size * i`: exactly the bytes the loop's memcpy read (L327-329 walk each range from `first` in chunks until its whole length is copied).
   - Per-frame counters fit in uint32.
3. **Threading: confirmed.**
   - All state is under `upload_hash_log.mutex`, which is taken only when ON.
   - UploadRanges is reached only through `SharedMemory::RequestRanges` (base shared_memory.cpp:360 → :488), on GPU Commands. So the mutex is uncontended.
   - `REXGPU_INFO` runs under the mutex, but logging never re-enters UploadRanges, and no other lock is taken under it. No lock-order edge is added.
4. **No GPU-visible effect when ON: confirmed.**
   - It reads guest memory and writes only its own state. It doesn't touch the upload buffers (it never reads the write-combined mapping), the deferred command list, valid bits, watches or guest memory.
   - The read is as safe as the memcpy it repeats; its window is only longer (the rest of the same call). Physical pages are never host-decommitted at runtime: the only `DeallocFixed` is `BaseHeap::Dispose` (xmemory.cpp:1113-1123). NoAccess needs `protect_on_release` (default false, L1689-1692) or a guest NoAccess protect.
5. **Syntax check:** not rerun (no compiles in the quiet window). Its input is confirmed above. Rerun it with `-Live` after the apply.
6. **Kill switch:** default false; `--shared_memory_upload_hash_log=true` for one run. Because the lifecycle is kHotReload, the flag can be toggled at runtime; DESIGN.md's caveat (stale hashes after a re-enable) covers that.

Also checked: the format string has 13 placeholders for 13 arguments, and `u_page`/`u_block` are -1, not a division by zero, when a frame has only first uploads.

**For the measurement (not safety):**
- **Pacing:** ON adds ~1-3 ms/f on GPU Commands. If that thread falls behind, more guest writes collect between two uploads of a page, so u can read a little low. This matters only for a close call: cross-check `pages`/frame against Agent 5's invalidation counts from the same log and against an OFF run of the same route.
- **Upper bound only** (DESIGN.md "How to read u"): an identical rewrite still faults under P1.
- **Nit (ON only):** `upload_hash_log` is a namespace-scope object. If an exit path ever ran static destructors while GPU Commands was still uploading, ON would touch freed vectors. That's no reason to block a diagnostic; a leaked heap singleton would remove it.

**Verdict: SAFE** at the default (OFF), output-identical. **ON is SAFE for functional runs**: no GPU-visible effect, but timings aren't comparable, so no timing arms. Applying and running it needs Agent 1's schedule after the S4 OK (DESIGN.md "Run plan").

## 21. C1 = P1 `physical_protect_keep_watch`: keep the watches on protects that don't change access (Agent 5's #20 S4.5 C1, Agent 12's S4.4 P1), default OFF (design level; read 06:00-06:50)

**Ask.** Agent 5, for Agent 1. Rate four things:
- Agent 12's checklist items 1-4 (`perf-notes/agent12-io-memory.md` L745-757): the bypass writers, the callback hooks, condition 3 with the old_protect restriction, and no lock-time side effects beyond diagnostics;
- Agent 5's condition 4 (no `provide_data` page);
- the RW|WC unprotect at :2391-2394 (no fault loop);
- the claim that the 256 KB write-time invalidation only re-uploads and re-decodes the same bytes (`perf-notes/agent5-uploads.md` L765-815).

Nothing is staged and nothing is built. SDK at c5fe668. Line numbers are xmemory.cpp unless marked.

**Verdict: SAFE at the default (OFF).** The old path runs unchanged. **ON is output-identical under conditions 1-4** (all four are needed) on the devoff (Xenos) path, with two exceptions that only an ON run can clear: residual R1 and the bypass writers. Flipping it ON needs A-D at the end of this section. Landing it OFF needs nothing.

**Item 1, bypass writers.**
- **CP writers, spot-checked (base `command_processor.cpp`):**
  - :315 ring-buffer read-pointer writeback;
  - :437 scratch-register writeback;
  - :1289 REG_TO_MEM;
  - :1305 MEM_WRITE;
  - :1368 WAIT_REG_MEM's memory write.

  All of them store through `memory_->TranslatePhysical`, the parent view, which is never watched. None calls TriggerCallbacks or a SharedMemory invalidation. MEM_WRITE's `OnGuestVisibleWrite` (:1297) lands deferred readbacks; it doesn't invalidate. Their targets are fence and readback words that the game polls on the CPU, normally not in a locked VB or a range the GPU reads.
- **Not read:** :1415, :1444, :1465, the d3d12 occlusion query :426, XMA :337 and cheat_engine. Agent 5's table puts them in the same class.
- **What C1 changes:** a bypass write into a range that is valid in SharedMemory leaves the GPU copy stale today as well, until the next lock of an overlapping range invalidates it. C1 removes that lock-time heal for fast-path ranges.
  - So C1 can only lengthen a stale window that already exists, and only where a bypass writer hits a locked range that the GPU reads.
  - That can't be ruled out statically for guest-chosen addresses, so verify mode becomes condition A.
- **rexlego writers** (PoolCopyHook memmove, textures.cpp) are compiled only with NATIVE_GPU=ON, so devoff doesn't have them. On native builds, rexlego's callback has no hook, so it forces the old path, but only once that callback is registered, and registration is lazy (`memory_watch.cpp:113-116`). See condition C.

**Item 2, callback hooks.**
- **The SharedMemory guard** (allow only if no page of the range is `valid_and_gpu_written`) is consistent. Its bits change only under G: MakeRangeValid (shared_memory.cpp:314-329), MemoryInvalidationCallback, and RangeWrittenByGpu through MakeRangeValid. The fast path holds G from the check to its last write, so the result can't go stale in between.
  - Implementation note: evaluate the hooks under G *before* taking the heap mutexes. A hook must take no lock and must not call into the heap.
- **PrimitiveProcessor always-allow is right.** It registers lazily (primitive_processor.cpp:1362-1366) and arms before it reads the indices (L1358 comment, L1367). It blocks an in-flight conversion through `cache_currently_processing_*` (L1351-1355). Its cache is valid only while the range is watched, and C1 keeps the watch.
- **rexlego's `MemoryWritten`** has no hook, by design (Agent 12). Keep it that way. A hook would need its own review, because rexlego's writers notify only rexlego: `memory_watch.cpp:151-154` bumps rexlego's versions, not SharedMemory's.

**Item 3, condition 3 and old_protect.**
- **Condition 3 is required.** Today the old path's invalidation clears valid and gpu_written (shared_memory.cpp:561-562), so the next RequestRange re-uploads guest memory over the resolved data. C1 must keep that behaviour, and condition 3 sends those ranges to the old path.
- **`old_protect == nullptr` is right.** For NtProtectVirtualMemory it is moot in practice: that function rejects every heap that isn't kGuestVirtual (`xboxkrnl_memory.cpp:270-272`), so it never reaches `PhysicalHeap::Protect`.
- **MmSetAddressProtect** (:484-503) passes no old_protect and discards the result (:502). So the guest can't see the fast path's failure behaviour either.
- **Internal callers** weren't enumerated (no recursive search in the quiet window). Any caller that passes old_protect keeps the old path, so this can only narrow the fast path.

**Item 4, lock-time side effects.** Today's lock-time TriggerCallbacks plus VirtualProtect has these non-diagnostic effects:
- (a) re-upload, texture re-decode and PrimitiveProcessor reconversion of the same bytes: invisible;
- (b) it heals a stale copy left by a bypass writer: item 1;
- (c) it heals a §19 form-1 state: R1 below;
- (d) watched pages go from host RO to RW. Under C1 they stay RO, and the first guest write faults and is handled before it retires (:579-580; Agent 12's ordering argument holds). Host code that writes through the guest view faults the same way and is handled like any watched page today.

`kMemoryInvalidate`, "cpu-write invalidations" and the memexport diag are diagnostics. So nothing else depends on lock time, apart from (b) and (c).

**Agent 5's (2), condition 4: needed, and not vacuous.**
- Data providers exist: d3d12 `command_processor.cpp:1140` installs `ProvideOnDemandMemexportThunk`, :3201 enables it, and xmemory.cpp:2569 sets `provide_data`.
- Today the old path makes those pages host-RW without delivering the data (L1772; SyncHostPageAccess returns at :977-979). C1 would deliver it on the next access (:566-578), which gives different bytes.
- Keep it: one bit test per page.

**Agent 5's (3), the fault loop: confirmed absent.**
- The fault path unprotects only pages that have their bit set, have no provide_data, and whose guest access is kReadWrite (L2391-2394).
- ToPageAccess maps RW|WC to kReadWrite (L930-941), so the game's 0x404 pages are unprotected and the write retries once.
- A page whose guest protect isn't writable stays protected and gets a real AV, as today.

**Agent 5's (4), the 256 KB widening: true.**
- SharedMemory widens to the 64-page block and stops at gpu_written pages (shared_memory.cpp:531-551). PrimitiveProcessor widens to its bucket (L1435-1440).
- TriggerCallbacks unwatches the intersection of the two, never less than the requested pages and at most 4 MB (L2353-2377). Each callback invalidated its own returned range, so unwatched ⊆ invalidated and invariant I holds.
- Neighbours re-upload the same bytes. The exception is a copy that (b) or (c) left stale; there the widening corrects it.

**Residual R1 (new).**
- Today a §19 form-1 state (valid, bit set, host RW) heals at the next old-path lock, because TriggerCallbacks sees the set bit. C1 sends that next lock down the fast path, so the state persists. Only a neighbour fault whose unwatch covers the page, an old-path protect, or Decommit/Release ends it.
- The race can still start from an old-path write protect under C1: a range that fails condition 3 or 4 (for example a resolve or memexport target), a range with a hookless callback, or the first protect after a runtime toggle.
- After that, the upload in the window makes the range non-GPU-written, so the next locks take the fast path and the GPU keeps a stale copy.
- The odds are low: it needs an upload of the same range in a µs window. But the effect lasts much longer than today's ≈1 frame.
- Fix (i) from §19 removes it at the source.

**Lock order and the fault rate.**
- The fast path takes G → view `heap_mutex_` → parent `heap_mutex_`. That is fine as long as no path nests the two heap mutexes the other way without G; physical-heap mutators take G first. Simplest: don't nest. Check and write each table under its own mutex while G is held.
- Use the same page rounding as `BaseHeap::Protect` (L1713-1750) for both tables. Send a zero-size or wrapping range to the old path.
- C1 turns write faults from ≈0 into F per frame. That runs the AV path (G, the callbacks, FireWatchesLocked and the texture-cache watch callbacks) far more often than today, so any latent lock inversion there will surface. The ON functional runs must include a level load; Agent 5's step 3 already does.

**C1 and §19.** C1 closes form 1 for fast-path protects: there is no G release and no host protect. Form 2 is outside C1's scope, because condition 2 excludes RO→RW.

**Conditions to flip ON** (none are needed to land it OFF):
- **A. Verify mode is required, not optional.** It needs 0 mismatches over the title, Agent 3's menu walk and one level load. A mismatch means a bypass writer (item 1) or an R1 state.
- **B. Fix (i) from §19 lands with C1** (under the same cvar, or its own cvar rated separately). Otherwise R1 has to be accepted in writing.
- **C. C1 is inert on native builds from startup,** not only after rexlego's lazy registration. Either register rexlego's callback at init, or force the cvar off when NATIVE_GPU=ON. It costs nothing, because rexlego's hookless callback forces the old path there anyway.
- **D. Agent 12's test 1** (no "Recovered stale physical page protection" or "Unhandled guest physical write fault" lines) plus Agent 5's step-3 pass criteria (logdiff NEW 0, frame hash or screenshot match). Then the timing A/B.

**§19 addendum (06:50).** Form 2 has no known trigger in this game. NtProtectVirtualMemory can't reach the physical heaps (`xboxkrnl_memory.cpp:270-272`), so only MmSetAddressProtect (:502) and internal callers can add write access to physical memory. Agent 5 found that the game's protects are all 4 or 0x404, RW→RW. So form 2 matters as an upstream bug and for other titles; for this game it is latent.

**Read.** xmemory.cpp L560-582, L930-979, L1100-1125, L1713-1799, L2128-2144, L2184-2250, L2273-2430; base shared_memory.cpp L277-336, L426-575; primitive_processor.cpp L1330-1445; memory_watch.cpp L60-160; base command_processor.cpp L308-318, L430-440, L1284-1308, L1362-1370; xboxkrnl_memory.cpp L268-292, L478-506. No runs.

## §22 Agent 12's S4 P2 `shared_memory_single_hold_rearm` (07:22, task #27 item 4; for Agents 12 and 1)

**What it is.** `build/agent12/s4-p2/single-hold-rearm.diff` (77BEB64E…, 2,853 B, 3 hunks, +30/-0) on SDK `src/graphics/shared_memory.cpp`, with the cvar `shared_memory_single_hold_rearm` (default false). When the cvar is on, `RangeWrittenByGpu` and `MakeRangeValid` each take G (the global critical region) once, after their bounds checks. The inner acquires then become recursive re-entries.

**My checks (read-only):**
- Hashes match NOTE.md and HASHES.txt:
  - live = `orig/` 15C89EDB… (24,698 B; git clean; last commit 33470b5; SDK HEAD c5fe668);
  - `new/` 0BE4BADC… (26,439 B);
  - diff 77BEB64E….
- `git apply --check` on the live SDK: OK.
- `git diff --no-index orig new` regenerates the staged diff hunk for hunk: `build/agent10/s3/p2-regen-body.txt` and `p2-staged-body.txt` are byte-equal after the 4 header lines.
- Agent 12's syntax check (07:02): PASS with no new diagnostics. I did not re-run it.

**Checklist**
1. **Off path: confirmed.**
   - The diff only adds lines; no original statement changes.
   - With the cvar off, the cost is a default-constructed `std::unique_lock<std::recursive_mutex>` (it holds no mutex and its destructor does nothing), one cvar load and one untaken branch.
   - The addition comes after the early returns.
   - The cvar is defined the same way as at primitive_processor.cpp:30.
2. **Recursion: confirmed.**
   - `global_critical_region::Acquire()` returns `std::unique_lock<std::recursive_mutex>(mutex())` on one static mutex (mutex.h:56-71, core/mutex.cpp:17). So the SharedMemory instance and the heap instances lock the same mutex.
   - FireWatches (:231), the scope at :315 and `EnableAccessCallbacks` (xmemory.cpp:2195) become re-entries.
   - Nothing under the hold releases G early:
     - `git grep "unlock()"` finds no hits in src/graphics or xmemory.cpp;
     - the watch callbacks receive G as a const reference (:235, :245, :258), so they can't release it.
   - So a release that was meant to free G completely can't be turned into a partial one.
3. **Lock order: confirmed, no new edge.**
   - Nothing between P2's acquire and the first inner acquire takes a lock. `RangeWrittenByGpu` goes straight to FireWatches, and `MakeRangeValid` straight to the scope at :315.
   - After the scope there are only three steps:
     - the `memory_invalidation_callback_handle_` test;
     - `Memory::EnablePhysicalMemoryAccessCallbacks` (:702-711), which takes no lock;
     - each view's `EnableAccessCallbacks`, which does only arithmetic before :2195 (L2157-2194) and keeps G to its end, through the seq_cst fence (L2271).
   - So everything that P2 newly covers either ran under G already or took no lock.
   - Nothing under the hold waits for another thread. EAC doesn't wait for data providers (L2212-2217), and the FireWatchesLocked callbacks already run under G today.
4. **Waiters: acceptable, with one caveat.**
   - The total time G is held stays the same. The longest single hold grows to the sum of today's sections.
   - For resolve-sized ranges (texture `cache.cpp:349`) that sum is the page loops of the 3 views, plus a VirtualProtect for each re-armed run of pages: microseconds.
   - **Caveat:** the memexport fallback `RangeWrittenByGpu(0, SharedMemory::kBufferSize)` (d3d12 command_processor.cpp:3063, used when `memexport_ranges_` is empty) would make one long hold. It would cover FireWatches over the whole buffer and the arm loops of all 3 views (about 131k system pages each, plus their protects): about 3× today's longest section. During that hold, these all wait for G:
     - a faulting guest writer (the AV path takes G);
     - VSync's interrupt;
     - XThreads object lookups.
   - This affects latency only, not correctness. For the ON runs, either:
     - confirm that this fallback doesn't run (today it isn't logged; NoteMemexportRange covers only ranged memexports); or
     - take the single hold only below a length cap (for example ≤ 4 MB).
   - Agent 12 chooses. Either way the gain on resolves stays.
5. **Interactions: confirmed.**
   - P2 changes no state that C1 reads.
   - Under the apply order, C1's `shared_memory.cpp` must be rebased onto P2's `new/` (0BE4BADC…). When it is, its hunks must equal the hunks rated in §21 apart from offsets. I have not re-rated it.
   - The diagnostic is in another file.
6. **Kill switch: confirmed.** Each call reads the cvar once and the lock is local to the call, so even a toggle at runtime can't leave G unbalanced.

**ON is output-identical: agreed.**
- With P2 on, every execution is one that today's code can also produce: the one where no other thread takes G in the gaps. SRW locks aren't fair, so the releasing thread can re-take G before a woken waiter runs.
- Threads that don't need G are unaffected.
- No new lock edge and no new wait under G, so no new deadlock.
- The order the GPU sees is unchanged: the valid bits, then the arm, then the fence.

**Verdict: SAFE as a default-off candidate. ON is output-identical and SAFE for functional and timing runs, with the memexport-fallback caveat (item 4).**
- Test plan as in NOTE.md. In step 2, also count the full-buffer `RangeWrittenByGpu` calls, or add the cap.
- Not applied before S4 is planned with the user.

**Fix (i), checklist item 4 (no path takes `heap_mutex_` and then G):** for S4, not tonight. See the status line in helpers.md.

**Read.** shared_memory.cpp L200-336 (live); xmemory.cpp L676-745 and L2150-2300; mutex.h L50-82; d3d12 command_processor.cpp L3036-3068. git grep for the callers of RangeWrittenByGpu and MakeRangeValid, for RegisterGlobalWatch and WatchMemoryRange, and for `unlock()`. No runs.

## §23 Agent 12's S4.7 fix (i) `physical_protect_hold_global_lock`, with checklist item 4 (07:40-07:55; task #34 item 1)

**What it is.** `build/agent12/s4-fixi/protect-hold-g.diff` (80CAD795…, 2,098 B, 2 hunks, +19/-0) on SDK `src/system/xmemory.cpp`, with the cvar `physical_protect_hold_global_lock` (default false). With the cvar on, a write protect in `PhysicalHeap::Protect` takes G a second time, right after the first acquire (:2130). TriggerCallbacks takes `global_lock` by value, so its release on return drops only the inner count, and G stays held through `parent_heap_->Protect` and `BaseHeap::Protect`. This is fix (i) from §19.

**Inputs checked (07:44-07:47):**
- Hashes match NOTE.md and HASHES.txt: live = `orig/` 6E8FA1BA… (107,670 B; git clean); `new/` 141FB1A9… (108,907 B); diff 80CAD795….
- `git apply --check` on the live SDK: OK. The live → `new/` diff (`build/agent10/s4/c1-orig-vs-live-xmemory.diff`) equals the staged diff body line for line (33 lines).
- C1's base: in `build/agent12/s4-c1/`, `orig/` and `new/` xmemory.cpp are both 141FB1A9… (= fix (i) `new/`), and its shared_memory.cpp is P2's 0BE4BADC…, as the apply chain says. At 07:44 C1 itself wasn't staged yet: `new/` = `orig/` for all 6 files.
- Agent 12's syntax check (07:02): PASS, no new diagnostics. Not re-run.

**Checklist (NOTE.md items 1-6):**
1. **Off path: confirmed.** The test is `(protect & kMemoryProtectWrite) && REXCVAR_GET(…)`, so a non-write protect doesn't even load the cvar. A write protect pays one cvar load and an empty `unique_lock` (no mutex; its destructor does nothing). No existing line changes.
2. **Recursion and release: confirmed.** `Acquire()` and `AcquireDirect()` both lock the one static `global_critical_region::mutex()` (mutex.h:58-71). The count goes 1 → 2 → 1 (TriggerCallbacks returns) → 0. `hold_global_lock` is declared after `global_lock`, so it is destroyed first; on the write path `global_lock` is already moved-from. The early `return false` paths release it by RAII.
3. **"locked_once": confirmed.** TriggerCallbacks never names its lock parameter (clang's unused-parameter warning at :2273, :2292 in the staged copy), so it can't unlock early. Its callbacks get no lock and already run under G today. Nothing between TriggerCallbacks and the return waits on another thread: two VirtualProtects, page-table writes, and SyncHostPageAccess, which returns at :977-979.
4. **Lock order: confirmed, no heap_mutex_ → G path.** See below; one wording fix to NOTE.md.
5. **Hold time:** as NOTE.md says. Timing only, not safety.
6. **Side effect: confirmed, stricter.** The view's `current_protect` write (:1789-1792) moves under G. EAC (:2228-2239) and TriggerCallbacks (:2391) read that field under G without heap_mutex_, so ON also removes today's unsynchronized read/write pair on write protects.

**Item 4, no path takes heap_mutex_ and then G: PASS.**
- `heap_mutex_` is protected (xmemory.h:234-275). BaseHeap, VirtualHeap and PhysicalHeap are its only users, all in xmemory.cpp. Subclasses outside xmemory.h weren't searched (no whole-tree scans).
- Every `heap_mutex_` scope (live line numbers) and what runs under it:
  - **Readers:** DumpMap :1126 (logging only), GetUnreservedPageCount :1179, QueryRegionInfo :1808, IsRangeCommittedReadable :1860, QuerySize :1876, QueryBaseAndSize :1889, QueryProtect :1903, QueryRangeAccess :1919. Page-table reads only.
  - **BaseHeap mutators:** AllocFixed :1384, AllocRange :1485, Decommit :1625, Release :1655, Protect :1749. Page-table work, logging, the host `rex::memory::AllocFixed`/`Protect`, the scribble memset, and `SyncHostPageAccess`. That last one takes no lock: it returns at :977-979 when the page size ≥ the host page; otherwise it reads watch bits (:2489-2505) and host-protects.
  - **PhysicalHeap Alloc :1988, AllocFixed :2021, AllocRange :2057.** Under the view's mutex they call `parent_heap_->AllocRange`/`AllocFixed` (the parent's mutex, nested) and `BaseHeap::AllocFixed` (recursive).
- G is taken at :682, :691, :714, :741, :2089, :2104, :2130, :2195 and :2543, and through AcquireHostPageReconcileLock (:972, :2484). None of these is reachable inside a `heap_mutex_` scope, except the reconcile lock in the nested calls of PhysicalHeap::Alloc*. There, the inner lock is non-empty only when the outer one is too:
  - outer: view page or parent page < host page (:2481-2487);
  - inner, parent: parent page < host page;
  - inner, view: the same test as the outer.

  So the inner acquire is always a recursive re-entry, never a new wait.
- The only G → `heap_mutex_` edges are the legal ones: PhysicalHeap Decommit, Release and non-write Protect today, plus write Protect with the cvar on. No `heap_mutex_` → G edge exists. Fix (i) adds G → parent mutex and G → view mutex for write protects. It takes them one after the other, never nested, and non-write protects already have both edges.
- **Correction to NOTE.md item 4, bullet 3 (and to my §21 "physical-heap mutators take G first").** On Windows the 9 reconcile sites (:1241, :1383, :1484, :1624, :1654, :1748, :1987, :2020, :2056) take no G at all. The reconcile lock is empty because every guest page size is ≥ the 4 KB host page (NOTE.md says so itself at L55). So "every path that takes both locks takes G first" isn't true there. The PASS rests on "no `heap_mutex_` scope acquires G" instead. Also, PhysicalHeap Alloc, AllocFixed and AllocRange nest view mutex → parent mutex **without G** (:1987-2003, :2020-2036, :2056-2074).
- **Consequence for C1:** if C1's fast path nests the two heap mutexes, the order must be view → parent. Parent → view would deadlock against PhysicalHeap::Alloc*, even though C1 holds G, because Alloc* takes no G on Windows. Not nesting (§21) avoids the question.
- **One pre-existing, debug-only exception:** with `scribble_heap=true` (default false), the 0xCD memset (:1447, :1607) writes guest memory under `heap_mutex_`. If a re-commit (AllocFixed over committed pages) hits a watched view page, the write faults, and the AV handler takes G while the view mutex is held. Fix (i) doesn't create this. Keep `scribble_heap` off in S4 runs.

**Verdict: SAFE at the default (OFF):** one untaken branch per write protect. **ON: SAFE.** It is a correctness fix, not output-identical by design: behaviour differs from today only when the §19 form-1 window is hit. It adds no lock edge.

**Turning it ON needs** NOTE.md's test plan 1-5:
- syntax with `-Live` after the apply;
- OFF behaves as today (logdiff NEW 0, same frame hash);
- ON functional runs (title, menu walk, one level load): logdiff NEW 0, no hang or stall, no "PhysicalHeap::Protect failed";
- with C1, my §21 gates A-D.

Timing only inside the C1 A/B. ON alone holds G across Main's write-protect VirtualProtects, which is most of MmSetAddressProtect's 0.54-1.02 ms/f, and GPU Commands can wait on that. I agree with NOTE.md: ON only together with C1 (§21 gate B).

**Form-2 design note (NOTE.md L103-122):** no code, so not rated. Its three asks fit the code I read: the forced pass runs under G; the page-table read takes G before `heap_mutex_` (the legal order); `unprotect = false` leaves host protection alone; and clearing watch bits on pages that have none is a no-op. Rate it when code exists. Low priority: agreed.

**Read.** xmemory.cpp L729-790, L960-990, L1100-1260, L1370-1613, L1600-1800, L1800-1935, L1975-2130, L2476-2550 (live, 6E8FA1BA…), plus targeted greps over L975-1096, L2157-2272, L2273-2431; xmemory.h L232-279; mutex.h L40-82; s4-fixi NOTE.md, HASHES.txt, the diff and the syntax log. No runs.

## §24 Agent 12's S4 C1 `physical_protect_keep_watch`, as staged (07:50-08:09; task #34 item 2)

**What it is.** `build/agent12/s4-c1/keep-watch.diff` (1B2BA4E3…, 522 lines, 19 hunks, +362/-3) on 5 SDK files, and `keep-watch-rexlego.diff` (4D0C1079…, +6/-0) on the game's `rexlego/src/gpu_native/memory_watch.cpp`. Staged 07:45-07:55 (NOTE.md); both hashes unchanged at 08:03. Not applied, not built. Two new cvars, both default false: `physical_protect_keep_watch` (xmemory.cpp) and `physical_protect_keep_watch_verify` (shared_memory.cpp, kRequiresRestart). This is C1 as rated at design level in §21. "kw:N" below is a keep-watch.diff line. Agent 12's write-up (design, patch map, residuals, test plan): `perf-notes/agent12-io-memory.md` S4.12, L1010-1131.

**Inputs checked (07:50-08:06; `build/agent10/s4/c1-checks.txt`):**
- All 12 `orig/` and `new/` files and both diffs match HASHES.txt. Bases: xmemory.cpp 141FB1A9… (fix (i) `new/`), shared_memory.cpp 0BE4BADC… (P2 `new/`); the other 3 SDK files and memory_watch.cpp are live.
- For each of the 6 files, `git diff --no-index orig new` gives a body equal to the staged hunks, line for line.
- **HASHES' "FAIL chain apply --check" is a method artifact.** With several patch files in one `git apply --check` call, each file is checked against the unmodified tree, so C1's hunks that sit on P2 and fix (i) can't match. One concatenated input (diag + P2 + fix (i) + C1, `build/agent10/s4/c1-chain-4.diff`, FDA3319B…) checks clean on the live SDK (exit 0), as does Agent 12's own `chain-live-to-c1.diff` (1D2CC1F3…). keep-watch-rexlego.diff checks clean on the live game repo. Agent 12's 4-step scratch chain also reproduces every `new/` hash.
- **Syntax: PASS** (Agent 12, `syntax-20261122-075428.txt`, 07:54). xmemory.cpp, shared_memory.cpp, primitive_processor.cpp and d3d12/shared_memory.cpp (an includer of the changed header) were each compiled as control and candidate: 8 compiles, all exit 0, no new diagnostics. memory_watch.cpp is native-only, so it was inspected, not compiled. My spot checks agree; every symbol C1 needs exists:
  - `XXH3_64bits` via `<rex/hash.h>` (it includes `<xxhash.h>`);
  - `memory::QueryProtect` (rex/memory/utils.h:115, via rex/memory.h);
  - `REXGPU_INFO`/`REXGPU_WARN` (rex/logging/macros.h:93-94);
  - `kBufferSize` is `uint32_t` (shared_memory.h:31), so the `std::min` compiles;
  - BaseHeap and PhysicalHeap are friends of Memory (xmemory.h:657, :659), so `memory_->system_page_size_` and both callback vectors are reachable;
  - xmemory.cpp already includes `<atomic>` and `<algorithm>`.

**What the code does:**
- **`PhysicalHeap::Protect` (kw:410-417).** Right after fix (i)'s second acquire comes `if (hold_global_lock.owns_lock() && !old_protect && REXCVAR_GET(physical_protect_keep_watch) && ProtectKeepWatch(…)) return true;`. `owns_lock()` is true only for a write protect with fix (i) on, so C1 can't engage without fix (i).
- **`ProtectKeepWatch` (kw:448-518)** runs under G (held twice). In order: the process latch; heap bounds, zero size and wrap; the guards; provide_data; the two page tables.
- **`BaseHeap::ProtectAccessUnchanged` (kw:370-401)** uses Protect's rounding and its region and commit checks, under that heap's `heap_mutex_` only. With `apply`, it re-checks under the same lock before it writes `current_protect`.
- **Guards (kw:56-70, kw:316-342).** `RegisterPhysicalMemoryInvalidationCallback` gets a third argument.
  - SharedMemory's guard checks `valid_and_gpu_written` (kw:187-213).
  - PrimitiveProcessor's guard always allows (kw:94-106).
  - rexlego keeps the 2-argument form, so its callback has no guard (rexlego diff L9-14).
- **Native latch (kw:347-357).** `Memory::BlockPhysicalProtectKeepWatch()` sets a `static constinit std::atomic<bool>`. memory_watch.cpp calls it from a namespace-scope initializer.
- **Verify mode (kw:127-134, :155-160, :168-172, :215-289).**
  - It hashes each CPU upload's pages after the arm.
  - K re-checks still-valid CPU pages inside the guard. A mismatch is logged, and that protect takes the normal path.
  - F checks at write faults (`!exact_range`), before the write lands.
- S4.12's patch map (L1077-1092) gives the same places in staged-file line numbers (B at xmemory.cpp:2231, guards :2300-2311, heap mutexes :2333-2341). They agree with the kw ranges above.

**§21 conditions, checked against the code:**
1. **Met: the cvar is on, `old_protect == nullptr`, and every page is committed, in one region, with unchanged access in both the view and the parent** (kw:414, :512-517, :385-394).
   - The rounding equals `BaseHeap::Protect`: start `(address - heap_base_) >> shift`, end from a 64-bit `address + size - 1`.
   - Zero size, out-of-heap, wrapping and sub-host-page heaps return false and keep the old path (kw:372-383, :453-456).
2. **Met: every callback has a guard, and every guard allows the range** (kw:476-487).
   - The physical range uses TriggerCallbacks' formula (live xmemory.cpp :2298-2339). The only difference: C1 returns false where TriggerCallbacks would clamp.
   - In the D3D12 build only SharedMemory and PrimitiveProcessor register a callback (SDK grep: shared_memory.cpp:43, primitive_processor.cpp:1364), and both now pass a guard.
3. **Met: no valid page in the range is `valid_and_gpu_written`** (kw:191-212). It uses the same block-mask idiom as TriggerCallbacks. Addresses outside the buffer are allowed, which is right: SharedMemory holds nothing there.
4. **Met: no `provide_data` host page under the guest pages Protect would change** (kw:489-507). It first rounds out to whole guest pages, as the normal path's host VirtualProtect does.

Two more checks:
- **Met: the guards run under G, before any heap mutex, and take no lock.** SharedMemory's guard reads only its flag arrays, which are written under G. In verify mode it also takes the logger's lock (a leaf) and calls `memory::QueryProtect` (VirtualQuery; no guest lock). PrimitiveProcessor's guard just returns true.
- **Check-then-apply race: handled.** Each apply re-checks under its own heap mutex, so a table that changed in between makes the apply return false. If the view applied and the parent didn't, Protect takes the normal path, which writes the same value into the view table again.

**Placement and lock edges: as asked.**
- The fast path sits after fix (i)'s second acquire and before `TriggerCallbacks(std::move(global_lock), …)`. On `return true`, RAII drops both holds.
- **No heap-mutex nesting.** Checking the view, checking the parent, applying to the view and applying to the parent are four separate scopes (kw:512-517). So §23's "view → parent only" constraint never comes up.
- **No new lock edge beyond fix (i)'s.**
  - C1 takes G → view mutex and G → parent mutex, one at a time. Fix (i) ON already adds both edges through `BaseHeap::Protect`.
  - Register and Unregister take G as today, and they update the guard vector inside the same scope (kw:316-342).
  - Verify's Record takes G from MakeRangeValid; under P2 that is a re-entry.
  - Item 4's PASS (§23) still holds: `ProtectAccessUnchanged` touches only the page table under its mutex.

**§21 flip-ON gates:**
- **A, verify mode with 0 mismatches: provided, with one blind spot.**
  - K catches a bypass write made before a lock. A bypass write made after a kept lock shows up only at that range's next lock (K) or its next write fault (F).
  - The game re-locks its dynamic VBs every frame, so normally this lags by one lock. A range that is locked once, bypass-written, then never locked or written again would be missed. Agent 12 also calls the coverage partial (S4.12 L1110).
  - Optional fix: a use-time check at RequestRange over still-valid CPU pages. Not required, given Agent 5's bypass list (§21 item 1).
- **B, fix (i) lands with C1: enforced in code** (`owns_lock()`).
- **C, inert on native from startup: met.**
  - memory_watch.cpp is compiled only under `LEGODIMENSIONS_NATIVE_GPU` (rexlego/CMakeLists.txt:61, :101-104) and is a direct source of the `legodimensions` executable (:169, :172), so its initializer always runs.
  - The atomic is `constinit`, so it is initialized before any dynamic initializer runs.
  - rexlego's guardless callback is a second stop.
  - Side effect: C1 can't be exercised on a native build at all. That's fine; §21 rated it for devoff only.
- **D: needs a kept-protect counter.** S4.12 step 6 reads test 1 as zero "Recovered stale physical page protection" and "Unhandled guest physical write fault" lines; both already exist (xmemory.cpp:632-651). What's missing is any count of kept protects.
  - Verify logs only mismatches, and K runs only inside the guard, after condition 3. So step 3's "0 K lines" can't be told apart from "C1 never got that far".
  - Add a kept-protect counter, or a one-time log at the first kept protect, before steps 3, 6 and 7. It is A's positive control as well.
  - The existing "cpu-write invalidations" count can stand in for faults per frame.

**Agent 12's open items** (Agent 1 asked for them at 08:02; S4.12 L1075, L1100-1106, L1114):
1. **The native fingerprint changes once (L1075): accepted, not a safety item.**
   - memory_watch.cpp is in `LEGO_NATIVE_GPU_FINGERPRINT_INPUTS` (rexlego/CMakeLists.txt:582, :659), so the rexlego hunk changes the native fingerprint and MANIFEST once. The devoff build doesn't compile the file.
   - After the apply, Agent 2's native baselines (native3d, nativeB) need re-pinning. A fingerprint mismatch against the old ones is expected, not a fail.
2. **R2, a page left host-RO that is no longer watched (L1102): acceptable.**
   - The old path heals such a page at the next lock, because `BaseHeap::Protect` rewrites the host protection. C1 leaves it RO until a write faults.
   - On that fault, TriggerCallbacks (xmemory.cpp:579) finds no watch. The recovery path (:584-638, written for "stale host protection state") then restores RW on that host page, since the guest protect is writable, which a kept write protect guarantees. The write is retried and completes.
   - An unwatched page has nothing cached, so nothing needs invalidating. The cost is one fault and one warning per page.
   - File reads don't hit it. `XFile::Read` writes through the unprotected physical alias (`TranslatePhysical`, xfile.cpp:268-273) and calls TriggerCallbacks afterwards (:293-295).
   - Step 6's zero-line rule counts R2 as a fail, which is the conservative reading. If R2 lines show up, look at them before C1 goes ON; no rollback is needed.
3. **E1, the 64 KB-page view vA0000000 (L1103): the safe direction.**
   - The old path's host VirtualProtect covers the whole rounded guest page, while only the requested range is unwatched. So it leaves the margin host pages RW while they are still watched, and a write there isn't caught.
   - C1 leaves them RO and watched, so such a write faults and invalidates. C1 is the more correct side.
   - The cost is extra faults and re-uploads of unchanged bytes, never a lost write. Step 7's faults per frame and the level-load ON run cover it.
4. **Verify mode's K → normal path (L1105): the safe direction, but it masks.**
   - A K mismatch sends that protect down the old path, which invalidates, so verify mode can only make behaviour safer.
   - The same switch hides the failure gate A looks for, so a verify run's output can't stand in for the C1 comparison.
   - A is read from the log, per S4.12 L1114: any K line with C1 ON fails A; F with C1 ON above the C1-OFF baseline means a kept watch missed a write. Output and timing comparisons (steps 6-7) need verify off.
5. **F's assumption (L1104): consistent with the code.**
   - `unwatch_exact_range == false` reaches the callbacks only from the AV path (xmemory.cpp:579), before the faulting write is retried.
   - The heap paths (:2098, :2122, :2135) and the file-read path (xfile.cpp:293-295) all pass true.
6. **Agreement.** S4.12's OFF-identity list (L1094-1099) matches the OFF path below, including the full rebuild of both trees. Its test plan (L1121-1131) covers OFF identity, A, B, C, D, the timing A/B (fix (i) ON in both arms) and the kill switches. My additions: the kept-protect counter, cvars set at launch, and A's blind spot.

**P2 long-hold caveat (§22 item 4), folded in:**
- C1 sits on P2's shared_memory.cpp, so P2's diff must be applied first even with P2's cvar off. The caveat itself applies only with P2 ON.
- C1 neither lengthens that hold nor needs P2 ON, except in verify mode. Record re-enters G on every MakeRangeValid: ~0.1 ms to zero 131,072 entries for the full-buffer fallback, and a hash of every page for CPU uploads. So verify runs are for function only, never for timing.
- After a full-buffer fallback every page is `gpu_written`, so condition 3 sends every lock down the old path until those ranges are invalidated. C1 sits inert for that stretch, which is safe.
- Agent 12 recorded the P2 memexport hold as an S4 gate of its own (S4.12 L1117-1120). It gates P2 ON, not C1.

**OFF path:**
- one more short-circuit test per write protect (fix (i) off: `owns_lock()` is false; fix (i) on: one cvar load);
- a guard pushed at each of the two registrations, and a `find_if` at Unregister;
- a null test per invalidation callback, and a cvar load per MakeRangeValid;
- on native, the latch store.

No behaviour change.

**Verdict: SAFE at the default (OFF). ON: SAFE to test.** It is output-identical under conditions 1-4, all implemented as rated in §21, with the bypass writers left to gate A. R1 is closed at its source by gate B, which the code enforces. R2 and E1 lean the safe way. No UNSAFE finding.

**Before landing, even OFF:**
- syntax is already PASS for the 4 compiled SDK TUs; memory_watch.cpp gets its first compile in Agent 2's native build;
- apply in chain order, as 4 calls or as one concatenated input;
- a full SDK install plus a game rebuild (devoff and native). `Memory` and `SharedMemory` gain data members (xmemory.h, shared_memory.h), and the game's TUs inline `TranslatePhysical` and similar accessors;
- re-pin the native baselines (open item 1).

**Turning it ON needs:**
- gates A-D above, with the kept-protect counter in place for A and D;
- both cvars (`physical_protect_hold_global_lock`, `physical_protect_keep_watch`) set at launch. Neither has a lifecycle, and a mid-run toggle could keep a form-1 state from before fix (i) went on, which C1 would never heal. Optional: kRequiresRestart for C1 would rule that out;
- optional: a one-time log when C1 is on but fix (i) is off (today it silently does nothing);
- ON runs that include a level load (§21, fault rate).

**Read.** keep-watch.diff (all 522 lines), keep-watch-rexlego.diff, HASHES.txt, NOTE.md, the syntax log's result lines; agent12-io-memory.md L690-800 (S4.4) and L1066-1131 (S4.12); live xmemory.cpp L578-700 and L2273-2425; xfile.cpp L268-335; rexlego/CMakeLists.txt L60-130, L630-680, L728-775. Targeted greps: Register and TriggerCallbacks callers in SDK src/include and rexlego; xmemory.h friends; hash.h, memory/utils.h, logging/macros.h, shared_memory.h. One-input `git apply --check` on the live SDK and the game repo. No runs, no builds.

## §25 Check of Agent 11's `perf-notes/S4-DRAFT.md` against these notes (08:10-08:15; task #34 item 3)

**Version checked:** 61,318 B, 07:58:42, 368 lines. My copy is `build/agent10/s4/S4-DRAFT-snap1.md` (SHA-256 CA69EB1F5482…). Agent 11 owns the file, so the corrections went to it by message; I edited nothing. If a newer version lands, diff it against the copy and re-check only the delta.

**Matches my notes (no change needed):**
- #1 AOT pack: first read only; a content fix gated on the user's visual check (row 16, §15.1).
- #2 miss cache: SAFE at the default; ON output-identical under §15.2 1-8 (row 19, §18).
- #3 threaded matrix: covered by row 16 item 3.
- #5 fix (i): SAFE OFF, ON SAFE, item 4 PASS; timed only inside the C1 A/B; ON only together with C1 (row 24, §23 L1167).
- #6 form-2: not rated, no code (§23 L1169).
- #7 u diag: SAFE OFF; ON for functional runs only (row 21, §20).
- #8 P2: SAFE OFF; ON output-identical; the memexport hold is an S4 gate (row 23, §22).
- #17: the toggles are row 9's.
- #18 R1 stage 1 and #20 R2: conditions 1-6 (cond 4 kInitOnly, cond 5 native OFF), (a)-(e), and Agent 1's GO to stage (row 18, §17 L779-803).
- #30 probe: compiled out; functional runs only; rule out the frontend confound first (§15.3 L703-704).
- #38 precise timer wait: SAFE default-off; caveats (a)-(d) and (f) (row 15, §14 L643-654). (e) needs no action.
- §1f's drops. §1g's apply chain (#7 → #8 → #5 → #4), item 14 (C1 touches a native fingerprint input) and item 15 (only C1 edits a closure header). §2b steps 1-2. §4a Q1 (C1 ON needs a level load).
- Rows unrated in the draft are unrated in my notes too: #9-#12, #14, #15, #19, #21, #25-#27, #32-#35.

**Corrections sent to Agent 11 (~08:15):**
1. **#4 C1 (row 4, §2a, §4b, "Changed since 07:44"): the staged code is now rated** (row 25, §24, 08:09): SAFE at the default; ON SAFE to test under §21 A-D. NOTE.md (07:59:48) and the syntax check (PASS, 07:54, 8 compiles) exist.
   - Gate B is enforced in code (`owns_lock()`), so C1 needs #5 ON. The draft's "or R1 accepted in writing" no longer applies, and R1 is closed by #5.
   - ON output risk: the bypass writers (gate A). E1 leaves margin pages in the 64 KB view RO and watched: extra faults, never a lost write.
   - ON also needs a kept-protect counter (D, and A's positive control) and both cvars set at launch.
   - Landing needs the chain order (diag → P2 → fix (i) → C1, then the rexlego diff), a full rebuild, and re-pinned native baselines (the fingerprint changes once). `…_verify` is kRequiresRestart.
   - Leaving C1 out of S4a (full rebuild, u_block first) is a planning call; the rating doesn't change it.
2. **Row 5 and §1g item 1:** the staged C1 nests neither heap mutex (four separate scopes), so the "view → parent only" rule is met, with no lock edge beyond fix (i)'s.
3. **W6:** time C1 with fix (i) ON in both arms (S4.12 step 7; §23 L1167). Add #8 + #5 as an arm. For example s0 / #8 / #8 + #5 / #8 + #5 + #4 at 1 + 4 × 3 = 13 runs, the same length.
4. **Row 8 and §2b step 3:** no staged diff counts the full-buffer `RangeWrittenByGpu` calls (S4.12 L1119: a counter would be its own small diff). Step 3 can't take the count unless that counter, or an existing log that shows the path, is in S4a.
5. **Row 38 (b) and §2b step 3:** the log line is `TimerQueue: precise wait (timer_queue_precise_wait)` (staged timer_queue.cpp:71), not "Timer Queue: …". A grep gate needs the exact text.
6. **Row 21 (S4-T1):** F's "Agent 10 wants one more code proof" has no source in my notes. My only threaded-mode asks are row 16 item 3 (covered by the n2/n3 rows, plus proofs 2-5), and they are for `LEGO_NATIVE_THREADED` itself. S4-T1 is unrated.
7. **§4b "the R1/R2 summary":** done in §24. R1 is closed by gate B; R2 is recovered by the AV stale-protection path; E1 goes the safe direction.
   - **Corrected 12:40 (board run 2): wrong R1/R2.** The draft's "R1/R2 summary" (L27, L321: it "may change … rows 18-20") means Agent 7's R1 and R2, its rows 18-20, not C1's residuals. The summary is in addendum 2 below and goes to Agent 11 ~12:45. The C1 residual note above stays as a side note for row 4.
8. **#24:** my rating follows (task #34 item 2).
9. **Row 32 (pipeline_cache.cpp:564) and §4b "#32's output-identical check":** my #34 brief's "#32" is Agent 9's task, the fence-wait item, which is the draft's #24. The draft's row 32 isn't in the brief. I'll read it after #24 if time allows. Until it is rated, it ships with a switch, as Agent 1 said.

**Result:** the draft's ratings match my notes, except C1, which was rated after the draft was written. Gate corrections: W6's fix (i)-ON control arm, P2's missing counter and the timer log text. No UNSAFE.

**Addendum to §25 (08:28; Agent 1, ~08:25):** Agent 12 checked at 08:20 that no existing log can prove P2's memexport full-buffer fallback never runs: the path logs nothing, and memexport_trace gives only a lower bound over the armed frames. Agent 1's decision: P2 ON in S4a needs a counter (~+4 lines), which Agent 12 stages after window 4. I rate it once it's staged; a cap comes only if the path runs. This settles correction 4.
- **Recorded 12:40 (board run 2, task #1 item 4):** P2 ON needs that counter (agent12-io-memory.md S4.12 L1128-1140).
  - The fallback is the `else` branch at d3d12 `command_processor.cpp:3060-3064` (`RangeWrittenByGpu(0, kBufferSize)`). It logs nothing.
  - Header route: a `kMemexportFullBuffer` id in `frame_stats.h`, one `frame_stats::Add` in that branch, and a `full-buffer {}x` field in the slow-frame line. About +4 lines in 2 files; 5 SDK TUs rebuild. The count prints only with `--slow_frame_log_ms`, so `bench/agent5/s4_slowframe.py` must accept the field.
  - One-TU route: a file-static relaxed atomic in d3d12 `command_processor.cpp`, read and reset in `ReportSlowFrame`.
  - Agent 12's staging checks: the rebuild cost, the overlap with #7's u diag (apply order), and a hold cap only if the count shows the path runs.
  - Not staged as of 12:35 (`build/agent12/s4-p2/` last written 07:04). I rate it once it's staged.

**Addendum 2 to §25 (12:40; board run 2, task #1 item 3): the R1/R2 summary and row 23's path**
- **R1/R2 are Agent 7's designs, the draft's rows 18-20** (b2r row 18, §17). Line numbers in this file shift as status rows are added (+4 since 07:58, with row 28), so cite §17 by condition: the draft's "L799" is cond (d) (now L803) and its "L802" is the verdict line (now L806).
  - **#18 R1 stage 1** (`d3d12_submit_split_kb`, 0 = off): **SAFE** as a default-off test bed under conditions 1-6. Cond 2 is the guard (it includes no active occlusion query and no scratch buffer). Cond 4 reads the cvar once (kInitOnly). Cond 5 keeps it OFF on native builds unless tested separately. Cond 6: no win alone, since each split adds a Close plus `ExecuteCommandLists`. Tests: count the splits that the query guard and `CanEndSubmissionImmediately` suppress, one pass with `d3d12_readback_memexport=true`, and a clean ON-vs-OFF logdiff.
  - **#19 R1 stage 2** (`d3d12_async_submit`, the submit worker): **not rated**. §17 cond 6 calls it the risky part.
  - **#20 R2:** step 1 (counters, compiled out by default) **SAFE**; step 2 (the filter) **SAFE-IF** (a)-(e). (a) Pure state setters only: never barriers, clears, copies, draws, dispatches, queries, resolves or discards. (b) Reset on Reset, at Execute, on SetDescriptorHeaps and on every root-signature set. (c) Compare the full payload. (d) A command outside the deferred stream, or an R1 split, resets the filter. (e) No new debug-layer messages, a frame comparison, and R1's tests. Go to step 2 only if step 1's counters show enough repeats; the ceiling is −0.1 to −0.2 ms/f.
  - Both need Agent 1's GO to stage (deferred to the S4 kickoff). The draft's rows 18 and 20 already say this, so **no rating cell changes**, and row 19 stays unrated. Row 20's assumed OFF default matches §17, which rates R2 as a default-off candidate.
- **Row 23's path (checked 12:34):** `single-hold-rearm.diff` (77BEB64E…) patches `a/src/graphics/shared_memory.cpp`, the base file, not d3d12's. Live 15C89EDB4B197C17 (24,698 B) = `orig/`; `new/` is 0BE4BADCAC666BEE (26,439 B). `src/graphics/d3d12/shared_memory.cpp` (B120D07C…) is #7's file. The draft's L19 has it right, so no change is needed.

## §26 Agent 9's GPU-wait back-off, stage 1 (S4-DRAFT #24, task #32), with Agent 6's GetData poll (08:16-08:28; task #34 item 2)

This is a read-only review of the draft: its rating at default OFF and what turning it ON needs, using a9 S5.2.5's list. Stage 2 (draft #25) and the sub_82BDCFB8 fallback have no diff, so they aren't rated.

**Inputs**
- Draft `build/agent9/s4/fence-wait/gpu_wait_backoff.cpp.draft`: 16,485 B, 07:44:53, 372 lines, SHA-256 D176CA8D888B3E8A…. Its header says it isn't compiled.
- a9 S5.2 (L219-402) and S4.1.1 (L457-500) in `agent9-codegen.md` (163,689 B, 07:45:53); a6h S9 item 4 (L285-295).
- Guest code in the A tree (`baseline/DimensionsRecomp/rexlego/generated/default/`): sub_82BDCFB8 at `.429.cpp:7890-7960`, sub_83FBF7D0 at `.248.cpp:35181-35262`, sub_83FAF180 at `.107.cpp:36777-36897`.
- The two pch files: B's `build/agent9/install/batch-nolr/generated/default/legodimensions_pch.h` (A5FE0D4BE8951BF3…) and the default `DimensionsRecomp/rexlego/generated/default/legodimensions_pch.h` (61BFA4CCB81A9D46…).
- SDK `include/rex/hook.h:42-49`; rexlego `CMakeLists.txt` :22, :143-168 and :582-583; `native_lock_elide.cpp:1-46`; `sample_profiler.cpp:64-85`; a `git grep` of `rexlego/src` for the five guest names (08:19).

**Verdict:** **SAFE** at the default: with all three env vars unset, every hook calls `__imp__` at once. ON: **SAFE to test**, and output-identical by construction: the hooks write no guest state, and only the time of the next poll changes. The risk is wake latency, at most Q plus timer slack per stalled poll. No UNSAFE.

**a9 S5.2.5 checklist**
1. **No guest writes: PASS.** REX_HOOK_RAW is `extern "C" REX_FUNC(name)` (hook.h:49), so ctx and base come from the generated signature.
   - The hooks read ctx.r3 (H1: waitctx; H2: the HRESULT after the call) and ctx.lr (H2, saved before the call).
   - They read guest memory only through REX_LOAD_U32/U8. There is no REX_STORE and no write to any ctx field.
   - All state is host-side: thread_local or the stats atomics.
   - The ON path does integer math only; doubles appear only in the STATS log line.
2. **Reset rules: PASS.**
   - H0 resets the L1 stall clock before and after each sub_83FBF7D0 call.
   - H1 resets on GPU off (dev+11069 & 2) and whenever block+0 != waitctx+8.
   - H2 resets on the try (lr 0x82BDD000) and on any result other than 1.
   - H1 reads the same words as the original, in the same order: waitctx+0, dev+11069 (the original returns 0 if & 2), dev+11024, then waitctx+8 against block+0 (`.107.cpp:36789-36825`). The original stores a moved block+0 to waitctx+8 (:36832-36837). So at H1's entry, waitctx+8 holds the previous poll's value (sub_83FAF088 seeds it; a9 S4.1.1).
   - The caller tests completion before every poll (`.248.cpp:35238-35251`). So a passed fence never reaches H1, and a moved word is never delayed.
   - Nesting: sub_83FBF7D0 may kick (sub_83FC0C10, `.248.cpp:35234-35236`) before its poll loop, and the kick can wait again (Agent 3's caller list includes 83FC0C10). The inner H0's resets run before the outer loop starts, so they don't disturb it.
   - Two STATS caveats follow from this. Nested time is counted twice in "L1 sum". And `l1_waits` counts calls (including r4 == 0 and fences that already passed), not stalls.
   - If any function polls sub_83FAF180 outside H0, its next wait starts with a stale stall clock and skips the spin phase. That costs latency only.
3. **lr gate and S_FALSE == 1: PASS** in the A tree.
   - `.429.cpp:7933-7934` sets `ctx.lr = 0x82BDD000` before the try, and :7955-7956 sets `ctx.lr = 0x82BDD028` before the loop call.
   - Both calls are followed by `cmpwi cr6,r3,1` (:7936, :7958), and the loop repeats while r3 == 1. `ctx.r3.u32 == 1` is the same test as the guest's signed compare for equality.
   - The gate depends on the ctx.lr store at each `bl`. B is `install/batch-nolr`, with skip_lr off (a9 L71, L96). A skip_lr build would silently disable H2: L2 would get no back-off, and the output would still be identical.
   - Positive control: P1's `l2_tries` > 0, since it counts only lr 0x82BDD000 matches.
4. **Xenos-only guard: PASS.**
   - `LEGODIMENSIONS_NATIVE_GPU` is the option at CMakeLists.txt:22. The block goes before `if(WIN32)` (:168) and uses the set_property pattern of :150-152.
   - git grep of `rexlego/src` (08:19): sub_83FB09E8 appears only at `gpu_native/queries.cpp:320` and sub_83FC0C10 only at `gpu_native/hooks_device.cpp:340`, both native-only. sub_83FBF7D0, sub_83FAF180 and sub_82BDCFB8 appear nowhere.
   - So a Xenos build has no duplicate strong symbol. On native, the CMake guard leaves the file out, and if it got in anyway, the define would keep H2/H3 out.
5. **OFF-path cost: PASS.**
   - Each hooked call costs the magic-static guard load, two bool loads, a branch, and one extra call level into `__imp__` (the compiler can make that a tail jump).
   - With the back-off OFF there is no QPC, TLS or guest load.
   - Cfg() runs once: three getenv calls and at most two log lines.
6. **Per-thread timer: PASS.**
   - It calls `CreateWaitableTimerExW(…, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_MODIFY_STATE | SYNCHRONIZE)` as rexlego's own `sample_profiler.cpp:70-71` does, so it compiles with the same flags.
   - The due time is relative (−us × 10, in 100 ns units), and each wait is capped at 20 ms.
   - A failed timer yields instead of sleeping (never Sleep(1)). A thread_local destructor closes the handle.
   - Before Windows 10 1803 there is no high-resolution timer, so the Q > 0 arms behave like Q = 0. `sleep_fail` shows when that happens.
7. **pch-equivalent loads: PASS.**
   - REX_LOAD_U8/U32 and REX_PHYS_HOST_OFFSET have identical text in B's pch (:124-133) and the default tree's (:120-129, the lines the draft cites).
   - Both use the hook's `base`, and both are volatile aligned loads, like the generated bodies.

**Also checked**
- **Clamps:** Q ≤ 2000 µs and S ≤ 200 µs; spin_ticks = qpf × S / 10^6 can't overflow. The STATS format string has 25 placeholders for 25 arguments, and the four `{:.Nf}` placeholders take doubles.
- **L1 output identity:**
  - The poll step's only time input is KTHREAD+0x58 (`.107.cpp:36820-36827`). It is compared at :36857-36868 against the image constant at 0x847F9AC0.
  - The SDK never writes KTHREAD+0x58 (a9 S4.1.1), so the timeout stays dead at any poll rate.
  - The post-wait elapsed values (dev+22008/22016, the dev+13836 callback) are wall-clock and already vary from run to run.
  - L2 has no counter and no timeout (`.429.cpp:7941-7960`).
- **Locks:**
  - The hook takes no lock and holds none while it sleeps.
  - The guest owner holds CS 0x84959edc while it polls (base1), so each stalled wait can hold the CS up to Q (plus slack) longer. That adds no lock edge and no new wait-for.
  - The 5 s STUCK-LOCK detector is unchanged.
  - On a CPU-starved machine (Agent 3, 05:24-05:32), the back-off gives the core to the CP thread. That is what Agent 6's arm tests.
- **Agent 6's GetData-poll back-off is H2**, the first option in a6h S9 item 4: REX_HOOK_RAW on sub_83FB09E8, gated on lr 0x82BDD028 and result 1. a6h's test additions are a9 S5.2.4 step 4. The back-off runs after the original call, so a kick inside GetData (q+24 == dev+11036) has already happened.

**Nits for Agent 9 (before the compile)**
- N1. ParseUs accepts "-5": strtoul wraps it, and the clamp then turns the back-off ON at Q = 2000. Reject a leading '-'.
- N2. Step 0's map check should list sub_83FC0C10 (H3) as well, and expect 4 new hooked aliases on a Xenos build (devoffB's 27 → 31).
- N3. The draft cites the pch macros at :120-129 (default tree). In B's pch they are at :124-133, with identical text.
- N4 (optional). STATS doesn't measure the real sleep length. A per-sleep duration sum would show the timer slack, which sets the latency cost.

**Landing OFF needs** (a9 S5.2.4 step 0: static review, build, map check)
1. S4 grants for `rexlego/src/gpu_wait_backoff.cpp` and `CMakeLists.txt` (Agent 1 / the user).
   - The CMake edit changes the native GPU fingerprint once, even though the item is Xenos-only, because CMakeLists.txt is the fingerprint's first input (:582-583).
   - Land it together with #30's option and C1 (§24), so the native baselines are re-pinned once.
2. A syntax compile against devoffB's compile_commands. Expect no new diagnostics, except possibly -Wdeprecated-declarations for the three std::getenv calls (native_lock_elide.cpp:42 makes the same call).
3. Agent 2's build: devoffB sources plus the file, OFF, batch-nolr codegen (skip_lr stays off), no regen. Then the step-0 map check, with N2.

**Before ON needs** (a9 S5.2.4 steps 1-4)

4. P1 (STATS=1, back-off OFF; profiling only):
   - Positive controls: l1_waits, l1_polls, l2_tries and kicks all > 0 on a route with occlusion queries.
   - P1 also sizes S and Q.
5. Functional (Q = 250 vs OFF):
   - logdiff NEW 0 / MORE 0 / flags 0, apart from the "GPU wait back-off: ON (…)" line;
   - the same exit codes;
   - no new STUCK-LOCK.
6. The window sweep and Agent 6's loaded arm as in a9 S5.2.4 (Agent 7's metric rule), with sleep_fail == 0 in every Q > 0 arm. Menus + attract only, until the Toy Pad question is answered.

**Result (12:40; board run 2, task #1 item 1).** Landing OFF: **SAFE** once items 1-3 are done. With the env vars unset every hook goes straight to `__imp__`, so the only landing cost is the one-time native fingerprint change. ON: **SAFE to test** after items 4-6. It is output-identical by construction, and its cost is wake latency. Fix N1 before the compile (cheap, not a blocker). No UNSAFE. Draft #25 and the sub_82BDCFB8 fallback stay unrated (no diff). The ~08:28 send was lost in the 08:29 reboot; re-sent ~12:45 to 9, 6, 11.

## §27 Agent 6's warm-boot pipeline fix (S4-DRAFT #32): output-identical check (12:40; board run 2, task #1 item 2; results and landing added 15:45, task #23)

**Question (Agent 1, 07:48):** is the one-line fix output-identical? If yes, it may ship without a switch. If not, it gets an OFF switch.

**Inputs**
- Live SDK `src/graphics/d3d12/pipeline_cache.cpp`: 161,305 B, 11-21 11:06:01, SHA-256 5DBED81F611E25B1. SDK HEAD is c5fe668, and `git status` shows only ` m thirdparty/simde`. Nothing is staged. The fix is a6 attract-stalls §10.2 (b): at L564, `while (creation_threads_.size() < creation_thread_original_count)` becomes `< creation_thread_needed_count`.
- Read: pipeline_cache.cpp L130-190 (constructor threads, Shutdown), L530-830 (storage init, EndSubmission), L925-1080 (the async path in ConfigurePipeline) and L3173-3320 (PrepareRuntimeDescriptionForQueuedCreation, CreationThread, CreateQueuedPipelinesOnProcessorThread); pipeline_cache.h L350-356, L414, L431; d3d12 command_processor.cpp L2712-2755; deferred_command_list.cpp L239-244; rex_app.cpp L596-636; graphics_system.cpp L373-393; base command_processor.cpp :126.
- a6 attract-stalls §10.2-§10.3 (L357-400); S4-DRAFT rows 32, 33 and 36 (L117, L118, L121) and its dropped list (L136).

**Today.** L560-563 compute `needed = max(min(N, logical) − 1, original)`, but L564's loop compares with `original`, so it never runs and no extra thread starts. L685's `size() > original` is then never true, so L685-715 never run. That block shuts the extra threads down from index `original`, joins them, then waits for the busy regular threads when `blocking` is set.
- Warm boot with the default `d3d12_pipeline_creation_threads` = −1, which gives max(¾ × 12, 1) = 9 threads on this 12-thread machine (L153-167). L668-675 queue every stored pipeline, and the GPU thread drains the queue as well (L684). Init then returns with up to 9 pipelines still being created.
- Storage init is blocking (rex_app.cpp:626-627, before `Resume()` at :632) and runs on the UI thread (graphics_system.cpp:373-393).
- Cold boots have no stored pipelines and never enter L555-729. Every harness run so far has been cold.

**With the fix.** needed = max(min(N, 12) − 1, 9): 2 extra threads when N ≥ 12, 1 when N = 11, none when N ≤ 10.
- L564-571 start the extra threads (index 9 and 10) with the constructor's creation code (L161-166).
- After the drain, L686-696 set `creation_threads_shutdown_from_ = 9` under `creation_request_lock_`, notify_all, and join them. L697-714 reset it to SIZE_MAX and, since `blocking` is true, wait until the 9 regular threads are idle.
- So init returns with every stored pipeline created (or failed). The INFO time then includes the tail, and the first frames after resume no longer wait for it.

**Same pipelines.** The queued path rebuilds the runtime description from `pipeline->description` (PrepareRuntimeDescriptionForQueuedCreation, L3173-3237). L646-647 copied that from the same runtime description that L677 uses inline. Stored pipelines have no pending shaders (`pending_vertex_shader`/`pending_pixel_shader` are nullptr, pipeline_cache.h:355-356), so nothing is translated on that path. The same description gives the same `CreateD3D12Pipeline` call: the same PSO, or the same failure (the state stays null either way).

**Draw output**
- Sync mode (`async_shader_compilation` off): no change. EndSubmission's wait (L795-813) and deferred_command_list.cpp:239-244 already resolve a stored pipeline at execute time.
- Async mode (the default, base command_processor.cpp:126): a draw whose PSO isn't created yet is skipped at record time (d3d12 command_processor.cpp:2726-2729). Today that can happen to a stored pipeline only in the first submission after resume, while the ≤ 9 tail pipelines finish, because every EndSubmission waits for the busy threads. With the fix the tail is done before resume.
- So ON gives the output of an OFF run whose tail finished first. It can remove a timing-dependent skip but never adds one. That is output-identical in #24's sense: only timing changes.
- `d3d12_pipeline_creation_threads=0`: today L677 creates every stored pipeline inline. With the fix, 11 temporary threads create them and are all joined (`shutdown_from = 0`). `creation_threads_` is then empty again, so gameplay stays synchronous (`use_async` needs threads, L942). Boot gets faster and the PSOs are the same.
  - One host-side difference: the stored pipelines now go through AddCompileWork/FinishCompileWork, so the host ImGui `ShaderCompileNoticeDialog` (rex_app.cpp:601-607) may show during boot. That is host UI, not guest output; it matters only for window captures in that config.
- Logs: the same lines. Only the value in "Created N graphics pipelines … in X milliseconds" (L718-723) changes.

**Handshake.** The source isn't new, but L685-715 has never run in this fork (a6 §10.2 "Risk").
- `shutdown_from_` is set under `creation_request_lock_` before notify_all, and CreationThread checks and waits under the same lock (L3246-3257), so no wakeup is lost. A busy temporary thread finishes its pipeline, then exits at L3253-3254.
- The queue is empty at shutdown, as the L689-690 comment assumes: only the GPU thread fills it, and it drained first.
- The join mirrors Shutdown() (L172-185), which runs at every clean exit. The busy/event wait is EndSubmission's pattern (L795-813), which runs every submission: busy is read and the set-event flag is set in one critical section, and the last thread to drop busy sets the event (L3248-3251). The event is requested only after the joins.
- No underflow: N ≥ 1 at L555, and the logical count is at least 1 (6 is the fallback).
- Agent 6 traced the same handshake (a6 §10.2: :3245-3266, :3279-3282) and found no deadlock. I agree.

**Verdict:** **output-identical** (timing only): the same PSOs, the same draws apart from removing a timing-dependent first-submission skip in async mode, and the same log lines. **SAFE.** Under Agent 1's 07:48 rule it may ship **without a switch**. Agent 6's optional bool cvar (default on, a6 §10.2) would only be a rollback lever for the never-run block, not an output guard. The rating doesn't replace the warm-boot runs.

**Before landing** (a6 §10.2's table; all passed, see Results below)
1. Cold run, fixed vs unfixed: no "from the storage" lines; counters within noise. This is a regression check only, since the path doesn't run.
2. Warm boot (`-SeedXenos build\agent3\seed\devoff2-214`), fixed vs unfixed: both INFO lines, N ≈ 214, and the same log lines apart from the "Created" value. ~~The fixed "Created" time is ≥ the unfixed one (it includes the tail), and the first frames after boot show no spike.~~
   - **Corrected 13:20** (Agent 6; `build/agent6/s10-2/spec.md` L65): at the default thread count the "Created" time is **info only**. The fix adds the in-flight tail (≤ 9 pipelines, about one creation time), but it also adds 2 workers: 11 creation threads plus the GPU thread's drain makes 12, against 9 + 1 = 10. So the value can go either way. This matches my reading above (9 regular threads; the fix's extra threads 9-10 are joined from index 9).
   - "No spike in the first frames" is a check both arms should pass, not evidence that the fix is active. The tail ends long before the first frame: storage is done by ~6 s, and the first frame comes at ~18 s.
3. 5 warm boots ending in WM_CLOSE, fixed: no hang between "Initializing shader storage" and the next guest line; clean exits.
4. Warm boot with `d3d12_pipeline_creation_threads=0`, fixed vs unfixed: it boots, and the "Created" time is shorter with the fix. **This is the positive control** (Agent 6's run 4, spec.md L57-61).
   - Unfixed creates all 214 pipelines one after another on one thread (L677). Fixed uses 11 temporary threads. So U4's "Created" should be several times F4's, and F4's should be close to a default-thread boot (~2 s).
   - It is the only ms comparison, so U4 and F4 run back to back if possible.
- Optional: `d3d12_pipeline_creation_threads=1` (10 temporary threads, shut down from index 1).

**Results** (copied 15:45 for task #23 from a6 §10.2.1, Agent 6's verdict 14:55; Agent 3 launched every run). Fixed (F) = `build/agent2/devoff4-bin` (the S3d line + #7, #8, #5 and #38, all OFF, + #32); unfixed (U) = `build/agent2/devoff3-bin`. Every warm run is seeded from `build/agent3/seed/devoff2-214`.

| Check | Runs | Result |
|---|---|---|
| Line check | `build/agent6/s10-2/linecheck-1331.txt` (13:31) | **PASS**: snap1 differs from live only at L564 (5DBED81F… → DA777443…, −2 B), the same as Agent 2's `pc-warmboot.diff`; my §29 check agrees |
| 1. Cold | R1 (devoff4 OFF) vs the devoff3 ref | **PASS**: no "from the storage" line in either; pm 235 = 235; frames 9,687 vs 9,537; first frame 14 s in both; 82 threads at 30 s in both; clean exits. R1's logdiff belongs to Agent 3's S4a gate |
| 2. Warm | U2 (13:17) vs F2 (14:34) | **PASS**: the same storage lines with the same N (229 shaders, 214 pipelines); pm 68 = 68; xpso +68 = +68; 82 threads at 30 s in both; clean exits, no dump, no STUCK-LOCK. Logdiff (Agent 3's `build/agent3/s4a/checks/F2-vs-U2-logdiff-warning.txt`, which I read): NEW 0 and MORE 0 at warning and above, marker flags 0, 142 warnings in both (info 322 vs 317). The 33 GONE keys are all `[info] [core]` `Toypad[Read ]` (4) and `Toypad[Write]` (29) packets whose payload bytes vary with route timing. Info only: Created 575 vs 1,521 ms (U2 ran during Agent 2's devoff4 build); first frame 10 vs 13 s; frames 12,595 vs 15,153 (Agent 3's sys.csv shows the slow state in both runs, F2's from ~210 s; #32 is done by ~2.5 s, and R1 shows no cold change) |
| 3. 5 warm boots ending in WM_CLOSE | F3a-F3d and F2 | **PASS, 5 of 5**: Created 881, 647, 1,715, 740 and 575 ms (F3c overlapped Agent 3's F2 postcheck); the guest line follows Created within 86 ms each time, so no hang; every exit clean, with no dump, crash event or STUCK-LOCK; 84 threads at 30 s = 75 + 9 regular, so both temporary threads were joined |
| 4. threads=0, the positive control | U4 then F4, back to back (14:28, 14:30) | **PASS**: Created 6,516 → 1,191 ms (5.5×); init to guest line 7,387 → 1,293 ms; first frame 19.0 → 10.0 s; clean exits; 75 threads at 30 s in both, so all 11 temporary threads were joined |
| Optional: threads=1 | F1t | **PASS**: Created 551 ms (1 regular + 10 temporary threads + the GPU thread); first frame 8.0 s; clean exit; 76 threads at 30 s = 75 + 1 regular |

My reading:

- **The gate passes, and nothing in §27 blocks landing.** The rating stands: output-identical (timing only), SAFE, no switch.
- The block at :685-715 had never run here. It has now run on 7 fixed warm boots (5 at the default thread count, plus threads=0 and threads=1). Every join and wait finished, and the 30-s thread counts show no leak. This matches the handshake read above.
- Run 4 shows the fix is active, as item 4 predicted: U4 is 5.5× F4. F4 (1,191 ms) is inside the default-thread range (575-1,715 ms).
- Item 2's "same log lines": this logdiff mode lists NEW and MORE only at warning and above, so info lines that appear only in F2 aren't listed. The code read above found no log call in the block, and s102_read found the same storage lines and N. I accept the 33 GONE Toypad packets as timing noise, since storage init reaches the Toypad code only through timing (sent ~14:56 to 6, 1).
- **Landed** in the live repos with S4a at 14:56 (Agent 1): SDK 3bb65bb ("S4a: …; #32 warm-boot fix"), game 1bd322e ("… SDK at S4a"; its `rexglue-sdk` gitlink is 3bb65bb). Checked read-only at 15:36-15:39: the live `pipeline_cache.cpp` is DA77744302CFC149 (161,303 B), the S4a snap1 file (§29), and `git diff c5fe668 3bb65bb` on that file is exactly the L564 hunk.
- Still open: re-take warm-boot baselines on fixed bins (#36; see Interactions).

**Interactions**
- #36 (`-SeedXenos` warm runs) goes through this path. Re-take any warm-boot baseline taken without #32; within one window, keep it the same in every arm.
- #33 (the no-wait mode, same file) changes EndSubmission, not storage init. With #32 the boot tail is done before resume, so #33 has no boot tail to skip. With threads = 0, `creation_threads_` is empty after init, so #33 stays inactive (it needs creation threads). #33 is visible by design and rated separately, not by this check.
- Agent 6's (a), per-thread translators (dropped, draft L136): the temporary threads only create stored pipelines and never translate, so there is no interaction if it comes back.
- Origin: the same line is in `baseline\DimensionsRecomp\rexglue-sdk\src\graphics\d3d12\pipeline_cache.cpp:564`, so our patches didn't introduce it (a6 §10.2). Upstream Xenia is unverified.

**Sent** ~12:45 to 11, 6.

## §28 C1's staged code, re-checked for the S4 queue (13:05-13:15; task #12 item 2)

**Asked (Agent 1, task #12):** check C1 (#4) as staged in `build/agent12/s4-c1/` (NOTE.md, `syntax-20261122-075428.txt`, keep-watch.diff, keep-watch-rexlego.diff, chain-live-to-c1.diff) for §21 A-D, its place after fix (i)'s second acquire, view → parent only, and P2's long-hold caveat. §24 rated the same files at 08:09. This section re-checks the four points on the code and adds the chain diff.

**Inputs: unchanged since 07:59.** keep-watch.diff 1B2BA4E30BC05A1E; keep-watch-rexlego.diff 4D0C10794188CF45; chain-live-to-c1.diff 1D2CC1F3A3845A3F (37,746 B, 07:51:36); HASHES.txt FBEC14B4…; NOTE.md F995EB81… (07:59:48); `syntax-20261122-075428.txt` 1618BCBC… (07:55:08). All 12 `orig/` and `new/` files hash as in §24. The live bases are pristine (SDK HEAD c5fe668; `git status` shows only ` m thirdparty/simde`).

**chain-live-to-c1.diff = #7 + #8 + #5 + C1, exactly.** I applied it in memory to the live SDK files with a hunk-by-hunk applier that asserts every context and removed line (scratch `t12_chain.py`). It reproduces all six staged files byte for byte:

| File | Live | Applied = staged | Hunks |
|---|---|---|---|
| include/rex/graphics/shared_memory.h | 4D861738A94B556B | 82A66445ED98B091 | 1, +13/-0 |
| include/rex/system/xmemory.h | 80100865A654AF04 | 5A70782EF00F0FB6 | 4, +29/-0 |
| src/graphics/d3d12/shared_memory.cpp | B120D07C6709D0D2 | BB0838CE3909E18A (#7's `s4-diag/new/`) | 4, +145/-0 |
| src/graphics/primitive_processor.cpp | E07F690223B564AE | 470BA4BED73B2ABF | 2, +5/-1 |
| src/graphics/shared_memory.cpp | 15C89EDB4B197C17 | A4A31038ABDFF94A | 7, +166/-2 |
| src/system/xmemory.cpp | 6E8FA1BA80EF9271 | 6C801EB2BA7D0D07 | 6, +198/-0 |

- So the chain is a valid one-input apply on the **pristine** tree only. Once S4a has landed #7, #8 and #5, it no longer applies.
- On top of S4a, apply `keep-watch.diff` alone. Its bases (xmemory.cpp 141FB1A9…, shared_memory.cpp 0BE4BADC…, the other three files pristine) are exactly what S4a produces, provided Agent 2's record shows those after-hashes (item 1). Then apply `keep-watch-rexlego.diff` to the game repo.

**1. Its place after fix (i)'s second acquire: as rated.** In the staged `new/` xmemory.cpp:
- :2210 takes G (`global_lock`). :2222-2225 is fix (i)'s second, recursive acquire (`hold_global_lock`), taken only for a write protect with `physical_protect_hold_global_lock` on.
- :2231-2234 is C1: `hold_global_lock.owns_lock() && !old_protect && REXCVAR_GET(physical_protect_keep_watch) && ProtectKeepWatch(…)` returns true. It comes before TriggerCallbacks (:2238-2240, which moves `global_lock` away) and before the parent and base protects (:2242-2247).
- So C1 runs only while G is held twice, and only with fix (i) on (gate B, in code). On `return true`, RAII releases `hold_global_lock`, then `global_lock`.

**2. View → parent only: met, with no nesting at all.**
- ProtectKeepWatch (:2272-2342) runs the guards (:2300-2311) and the provide_data scan (:2313-2331) first. Both run under G, before any heap mutex, and take no lock.
- Then come four sequential calls (:2336-2341): check the view, check the parent, apply to the view, apply to the parent. `BaseHeap::ProtectAccessUnchanged` (:1848-1879) takes only its own `heap_mutex_`, in one scope (:1863), and checks again inside that scope before it writes (:1865-1877).
- So the view and parent mutexes are never held together, and the order is view, then parent. The only edges are G → view and G → parent, which fix (i) ON already adds. §23's rule (Alloc* nests view → parent without G, so C1 may nest only view → parent) can't be broken.
- If the parent apply fails after the view apply, Protect takes the normal path, which writes the same `current_protect` into the view again (§24).

**3. §21 gates A-D, for the staged code**
- **A** (verify mode, 0 mismatches over the title, the menu walk and one level load): **provided** (`physical_protect_keep_watch_verify`, kRequiresRestart), with §24's blind spot: a bypass write after a kept lock shows only at that range's next lock (K) or write fault (F).
- **B** (fix (i) lands with C1): **met, enforced in code** (`owns_lock()`).
- **C** (inert on native from startup): **met.** memory_watch.cpp's namespace-scope initializer sets a `constinit` latch, which ProtectKeepWatch checks first (:2273). rexlego's guardless callback is a second stop (:2308).
- **D** (test 1's zero "Recovered stale physical page protection" / "Unhandled guest physical write fault" lines, plus Agent 5's step-3 criteria): the lines exist, but **nothing counts kept protects**, so a clean log can't show that C1 engaged. D, and A's positive control, need a kept-protect counter before ON. It isn't in this stage; the draft plans C1 v2.

**4. P2's long-hold caveat: C1 doesn't lengthen the hold.**
- C1 needs P2's **diff** (its shared_memory.cpp base is P2's `new/`), not P2 ON.
- C1 runs inside PhysicalHeap::Protect, not inside P2's single hold (SharedMemory's RangeWrittenByGpu/MakeRangeValid).
- Its fast path under G replaces the normal path's TriggerCallbacks and host VirtualProtect calls with bit-mask and page-table loops, so a kept protect holds G for less time. A fall-through adds only those loops before the normal path.
- One exception: verify mode's Record re-enters G inside MakeRangeValid (under P2's hold, a re-entry) and hashes pages there. Verify runs are for function only, never timed (§24).
- After a full-buffer fallback every page is `gpu_written`, so condition 3 sends every lock down the normal path until those ranges are invalidated. C1 sits inert, which is safe.
- The fallback counter (task #12 item 3) gates P2 ON, not C1.

**Verdict (unchanged from §24):**
- **SAFE** at the default (both cvars off). The OFF cost is one short-circuit test per write protect, the guard bookkeeping at registration, and the latch store on native.
- **ON: SAFE to test** once D has its kept-protect counter (C1 v2). Both cvars must be set at launch, and an ON run must include a level load.
- Landing needs the chain order (or keep-watch.diff on top of S4a), a full SDK install plus a game rebuild (xmemory.h and shared_memory.h gain members), and re-pinned native baselines.
- No UNSAFE.

**Read.** new/ xmemory.cpp :1840-1896 and :2205-2395; the chain's 6 sections (in-memory apply); the stage's hashes; §21's gates; §24. No builds, no runs.

## §29 Agent 2's S4a apply record (13:31-13:42; task #12 item 1)

**Asked (Agent 1, task #12 item 1):** check that each file's before/after hashes in Agent 2's S4a record match the rated diffs (#7, #8, #5, #38), and that #32 is exactly the L564 change.

**Inputs (read-only; the game build ran on snap1).**
- `build/agent2/s4a-prep-apply.txt`; `S4a-notes.txt` (6AC482D8…); `s4a/HASHES.txt` (D9BEA59D8ED9A699); `s4a/pc-warmboot.diff` (080122DD584F8414, 695 B).
- The real apply's work dir `s4a/work-132457` (13:24:57). Its rows equal the 13:21:22 dry run's (`work-132122`).
- `snap1/PATCHES-S4a.tsv` (B9612DA2…), `STATE-S4a-1325.tsv` (87DB470A…), `snap4a-verify-off.txt`.
- Tree `build/agent2/snap1/DimensionsRecomp`, backup `snap1-backup-S4a`.

**Method.** Scratch `t12_s4a.py` runs 12 checks per row:
- the record's diff hash = the diff on disk = the diff I rated;
- live = the record's before = the base I rated, and the backup holds the same bytes;
- snap1 = the record's after = the work copy = the staged `new/`;
- my own strict apply of the rated diff to the live file (in memory, every context and removed line asserted at its stated line) = the after bytes.

Result: **OVERALL PASS**, 6 rows, 72 checks.

| S4a row | File | Before (live = backup) | After (snap1 = my apply) | Rated diff | Hunks |
|---|---|---|---|---|---|
| #7 u diag | SDK d3d12/shared_memory.cpp | B120D07C6709D0D2 | BB0838CE3909E18A | `agent12/s4-diag/upload-hash-log.diff` D2905301… (§20) | 4, +145/-0 |
| #8 P2 | SDK graphics/shared_memory.cpp | 15C89EDB4B197C17 | 0BE4BADCAC666BEE | `agent12/s4-p2/single-hold-rearm.diff` 77BEB64E… (§22) | 3, +30/-0 |
| #5 fix (i) | SDK system/xmemory.cpp | 6E8FA1BA80EF9271 | 141FB1A947D59156 | `agent12/s4-fixi/protect-hold-g.diff` 80CAD795… (§23) | 2, +19/-0 |
| #38 precise wait | SDK core/timer_queue.cpp | D8724B29C43286B0 | 015C04A22DACC592 | `agent11/timerq/stage/timerq.diff` D07A2DC4878DAE8D (§14) | 9, +73/-6 |
| #32 warm boot | SDK d3d12/pipeline_cache.cpp | 5DBED81F611E25B1 | DA77744302CFC149 (161,303 B) | `agent2/s4a/pc-warmboot.diff` 080122DD584F8414 (§27) | 1, +1/-1 |
| #2 miss cache (native only) | game rexlego gpu_native/shaders.cpp | E87A2DEE43D38D8E | 9567FE3F3B63637D | `agent4/s34/shaders-s34.patch` 328BDAE19ABFC6C8 (§18) | 9, +229/-11 |

**#32 is exactly the L564 change.**
- Line 564 is the only changed line: `while (creation_threads_.size() < creation_thread_original_count) {` becomes `… < creation_thread_needed_count) {` (161,305 → 161,303 B).
- In the after file, `creation_thread_needed_count` has 2 uses (was 1) and `creation_thread_original_count` has 5 (was 6).
- The after hash equals the one I precomputed at 13:15 (helpers RESUME block).

**Other rows**
- #7, #8, #5 and #38 add four cvars, all default false (Agent 2: the names are in the devoff4 DLLs). #38's is kInitOnly. So at the defaults, #32 is S4a's only behaviour change (timing only, §27). The four OFF items cost what §14, §20, §22 and §23 rated.
- #2: the file is CRLF, and the apply kept CRLF (CR 913 → 1,131, the 218 net added lines). It matches row 19/§18. devoff4 doesn't compile gpu_native, so #2 is in native4 only (building since 13:33).
- The backup holds the six before files, with the before hashes. `snap4a-verify-off.txt`: 23,843 files, 6 backups checked, 0 problems, PASS. That is Agent 2's whole-tree check; mine covers the six rows.
- Live is untouched: the six live files still hash to the before column, and the SDK `git status` shows only ` m thirdparty/simde`.
- Not in S4a, as planned: C1 (#4), #24, the P2 counter (next build, §30), #18/#20 (§31), #26.

**C1 on top of S4a (a §28 follow-on)**
- keep-watch.diff (1B2BA4E3…) applies to the S4a snap1 SDK at offset 0, all 19 hunks. It reproduces the five staged `new/sdk` files byte for byte: xmemory.cpp 141FB1A9… → 6C801EB2…, shared_memory.cpp 0BE4BADC… → A4A31038…, and xmemory.h, shared_memory.h and primitive_processor.cpp as staged. So §28's "after S4a, apply keep-watch.diff" holds.
- keep-watch-rexlego.diff (4D0C1079…, +6/-0) applies at offset 0 to memory_watch.cpp. snap1 = live = `orig/` = 19AE1606C6DB7273 (CRLF, 166 lines). The diff is LF-only:
  - a byte-literal apply (mine) gives 2AAF00AF4B9E95E6 (8,048 B): six LF lines in a CRLF file;
  - with the file's CRLF kept, as Agent 2's applier did for #2, it gives the staged `new/` 70829846C4F321A9 (8,054 B, 172 CRLF lines);
  - the text is the same either way.
- **Landing check:** after the apply, memory_watch.cpp must hash 70829846…; otherwise copy the staged `new/` file.

**Verdict: ALL PASS.** The record matches the rated diffs in all six rows, and #32 is exactly the L564 change. No UNSAFE.

**Read.** The four record files and both work dirs; `t12_s4a.py`'s 72 checks; my own apply of all six rated diffs; `t12_diffcheck.py c1s4a` and `t12_mw.py` for C1. No builds, no runs.

**Sent** ~13:42 to 2, 1.

## §30 Agent 12's P2 memexport full-buffer counter (13:19-13:42; task #12 item 3)

**Asked (Agent 1, task #12 item 3; §25 item 4):** rate Agent 12's P2 memexport-fallback counter (one TU, d3d12 command_processor.cpp). P2 ON needs it, because of §22's long-hold caveat.

**Inputs.** `build/agent12/s4-p2c/`:
- `memexport-full-buffer-counter.diff` 29E02E249EDDFEFD (2,998 B, LF, 5 hunks, +12/-2);
- `orig/command_processor.cpp` 3AB3AA5360D4E987 (269,215 B, 5,840 lines) = live = S4a snap1 (S4a doesn't touch this file);
- `new/command_processor.cpp` 474C1CBAE6359D9E (269,826 B, 5,850 lines);
- NOTE.md (13:34:32) and `make_p2c.py` (D3DECDA3…);
- `syntax-20261122-132026.txt` (C19778A9…): **RESULT: PASS**. The candidate has the same 20 diagnostics as pristine, none new. All 20 are existing SDK-header -Wunused-parameter and -Wnontrivial-memcall warnings.

**Re-derived.** My applier (`t12_diffcheck.py p2c`) puts every hunk at its stated line on the live file (offsets 0) and reproduces `new/` byte for byte.

**Code (new/ line numbers)**
- :241: `std::atomic<uint64_t> memexport_full_buffer_draws{0};` is in the anonymous namespace (:115-313). It has internal linkage and is constant-initialized, so there is no init-order issue.
- :3069-3074: IssueDraw's `else` branch (memexport used, no resolved ranges) calls `RangeWrittenByGpu(0, SharedMemory::kBufferSize)`, then `fetch_add(1, relaxed)`. The count follows the call; it never replaces or reorders it.
- :264-266, ReportSlowFrame: `exchange(0)`, added to a function-static total. It runs after the frame_stats snapshot and before the threshold's early return (:273), and IssueSwap calls ReportSlowFrame unconditionally (:2202). So it runs on every swap, and `total` includes frames that weren't logged.
- Both sites run on the command thread. Relaxed is enough: the exchange is the only reader and orders nothing. Only ReportSlowFrame touches the function-static total.
- :283-284 and :293 add ` | memexport full-buffer {}x (total {})` at the end of the slow-frame line. I count 25 placeholders and 25 args, and fmt's compile-time check agrees (syntax PASS). The line is REXGPU_INFO and prints only when `slow_frame_log_ms` > 0.

**Coverage**
- The same draws' residency request (:2890-2891, `RequestRange(0, kBufferSize)`) has the counted branch's condition, `memexport_used && memexport_ranges_.empty()`. It is an upload request, not a GPU-write mark. So one count is one fallback draw, and that draw makes both calls.
- The SDK's only other full-buffer `RangeWrittenByGpu` is vulkan/command_processor.cpp:4166, and that backend is unused. So on D3D12 the counter sees every call that §22's caveat is about.

**Readers and logdiff**
- `bench/agent5/s4_slowframe.py` searches without an end anchor (:81), and `bench/agent12/s4_uhash.py` matches only the line start. Both still accept the line, but neither extracts the field. Use NOTE.md's regex (`memexport full-buffer (\d+)x \(total (\d+)\)`) on the last slow-frame line.
- logdiff: the line is info level, so `--min-level warning` ignores it. At info level with `slow_frame_log_ms` set, every slow-frame line's text differs from a build without the counter, so compare fields, not raw lines. Default runs are unaffected.

**Apply order**
- It shares no file with S4a (#7, #8, #5, #38, #32, #2). Its base is the live file, which S4a leaves unchanged.
- It shares d3d12/command_processor.cpp with Agent 7's s4-r1r2 (#18; §31), and the two commute (`t12_diffcheck.py cross`):
  - p2c onto r1r2's `new/` applies at offsets [12,12,12,12,22];
  - r1r2 onto p2c's `new/` applies at [0,9,10,10,10];
  - both orders give 027204B53A271D69. Either order works with offsets only, no fuzz.

**Verdict**
- **Output-identical** (log only: with `slow_frame_log_ms` unset, nothing visible changes) and **SAFE**. The cost is one relaxed RMW per fallback draw and one exchange per swap, on the command thread. It may ship **without a switch** (Agent 1's 07:48 rule). It goes in the next build, not S4a.
- **For P2 ON (§25 item 4):** read `total` from a next-build run with `slow_frame_log_ms` set, over the scenes P2 ON will run (title, menu walk, and a level load when allowed). P2 may be on or off, because the count doesn't depend on P2.
  - total = 0: §22's caveat is closed for those scenes.
  - total > 0: Agent 1 decides on a hold cap (none is staged) or keeps P2 off.
- No UNSAFE.

**Read.** new/ :115-313, :2202, :2876-2897 and :3052-3078; the diff; NOTE.md; the syntax log; `t12_diffcheck.py p2c`, `cross` and `misc`. No builds, no runs.

**Sent** ~13:42 to 12, 1.

## §31 Agent 7's #18 R1 stage 1 and #20 step 1 (13:30-13:57; task #12 item 4)

**Asked (Agent 1, task #12 item 4; Agent 7's task #9 message, 13:46):** rate Agent 7's staged R1 stage 1 (#18) and R2 step 1 (#20) against §17. Agent 7 asked for three close looks: the hold order and a failed `EndSubmission`; IssueCopy's return value with the cvar OFF; and whether R2 cond (d) holds by design.

**Inputs.** `build/agent7/s4-r1r2/` (diffs 13:24:33, HASHES.txt 13:27:15, NOTE.md 13:34:19), against SDK c5fe668 (cp = d3d12/command_processor, dcl = d3d12/deferred_command_list):

- `r1-split.diff` 2516F199… (8,237 B: cp.h, cp.cpp, dcl.h); `r2-counters.diff` A8BE5FCB… (20,086 B: dcl.cpp); `s4-r1r2.diff` 12182A4C… (28,323 B: both);
- `orig/` = live: cp.h 41F32B80…, dcl.h DA2F58B6…, cp.cpp 3AB3AA53…, dcl.cpp FFDF7FB6…;
- `new/`: cp.h 67F4E838… (+19/-0), dcl.h 9F6CC70A… (+3/-0), cp.cpp 760833A5… (+87/-4), dcl.cpp 183FF8FD… (+404/-0);
- syntax: **pending**. NOTE.md says SYNTAX_RESULT_PENDING. Agent 7 (13:46): the clang `-fsyntax-only` run is still going (dev-SDK flags; base vs new; cp.cpp, dcl.cpp with and without the macro, and the six other SDK files that include the headers). No `syntax-*.txt` in the stage at 13:50.

**Re-derived (`t12_diffcheck.py r1r2`).** `s4-r1r2.diff` on live puts every hunk at offset 0 and gives all four `new/` files byte for byte. `r1-split.diff` alone applies on live, and r1 then r2 = `new/`. r2 alone applies too, since they share no file.

**R1 stage 1 against §17 (new/ line numbers)**

| §17 cond | Where | Finding |
|---|---|---|
| 1. Tail of IssueDraw/IssueCopy only, after the command and its barriers | cp.cpp :3107-3111 (IssueDraw, just before `return true`), :3713-3717 (IssueCopy) | **Met.** Called only under `if (submit_split_bytes_)`, after the draw, its barriers and any memexport readback are recorded; in IssueCopy only after a successful resolve. Not called from IssueSwap or RefreshGuestOutput. IssueDraw's early returns skip the check (harmless) |
| 2. The guard | :4369-4383 | **Met.** Return unless `submission_open_ && frame_open_ && GetSizeBytes() >= submit_split_bytes_`. Then hold on an active occlusion query, then on the scratch buffer, then on pending pipelines (`!CanEndSubmissionImmediately()`) |
| 3. A failed `EndSubmission(false)` | :4384-4395 | **Met.** `failed` counts, and recording carries on in the open submission; no BeginSubmission |
| 4. kInitOnly, cached; OFF = today's code | :1189-1197 | **Met.** `REXCVAR_DEFINE_UINT32(d3d12_submit_split_kb, 0, …).lifecycle(kInitOnly)`, cached in SetupContext as `submit_split_bytes_ = kb * 1024`. Its INFO line logs only when on |
| 5. Native OFF | n/a | **Met.** Default 0; nothing sets it |
| 6. No win expected | cvar comment | **Met:** "expect a small cost, not a win" |

Other R1 changes: cp.h adds `<chrono>`, the MaybeSplitSubmission declaration and members at the class end (a layout change, so a full SDK rebuild; the game only relinks), and dcl.h adds `GetSizeBytes()`. The counter line (:4399-4408) prints about every 10 s, only while splits are due. Nit: `submit_split_last_log_{}` starts at the epoch, so the first due call logs at once. Harmless.

**Agent 7's three close looks**

1. **Hold order, then `EndSubmission(false)`.**
   - The three holds are pure reads in one else-if chain, and each bumps only its own counter. So the order decides only which counter a due call is charged to when several hold at once; every order holds exactly the same calls.
   - Each hold is needed. EndSubmission ends an active occlusion query early (:4266-4270, `D3DEndQuery` then `active_occlusion_query_ = {}`), which would change the query's result. It asserts that the scratch buffer is free (:4264). And it waits for pending pipeline creation (:4272, `pipeline_cache_->EndSubmission()`), which is a CPU stall, not an output change.
   - Query first is the right priority, because it is the only hold whose miss changes guest-visible results. held_scratch should stay 0 at a draw or resolve tail (the scratch buffer is taken and released inside one operation, :992-1032), so a non-zero count is a finding in itself.
   - A failed EndSubmission: its only `return false` (:4246, CreateCommandAllocator failed) comes before any change: no EndFrame (is_swap is false anyway), no EndQuery, no pipeline wait, no SubmitBarriers. The submission is left exactly as it was, so carrying on into it is correct, and BeginSubmission isn't called (cond 3).
2. **IssueCopy with the cvar OFF.** The two branches now assign `resolved` (from `Resolve(…)` or `IssueCopy_ReadbackResolvePath()`) instead of returning it: the same calls in the same order. `submit_split_bytes_ && resolved` short-circuits at 0, and `return resolved;` returns the same value. A failed resolve never splits.
3. **Cond (d) by design: confirmed.**
   - The shadow is a local of Execute (dcl.cpp :240), so each call starts empty.
   - The native list is touched only in SetupContext (cp.cpp :1182 `Close` after creation; :1184 `QueryInterface` for `command_list_1_`) and in EndSubmission (:4287-4290: allocator Reset, list Reset, Execute, Close). `command_list_` and `command_list_1_` are private (cp.h :490-491) with no getter; other components get only `GetDeferredCommandList()` (cp.h :71-73). So nothing reaches the native list outside the deferred stream, and a split is one more EndSubmission.
   - Comment nit (dcl.cpp :110-111): "the next BeginSubmission's Reset". The native list's Reset is EndSubmission's :4288; BeginSubmission (:4164) resets the deferred list. The claim (empty state at every Execute) holds either way.

**R2 step 1 (dcl.cpp)**

- OFF: every addition is inside `#if REX_D3D12_DEFERRED_COUNTERS`, which defaults to 0 through `#ifndef` (:26-27). Only the macro default and comments are unconditional, so OFF compiles to today's Execute.
- ON (a counters build only): the count runs before each replay and only counts. (a) Only pure state setters can repeat; barriers are counted as entries and never compared. (b) SetSignature resets that root's arguments, and SetDescriptorHeaps resets the tables. (c) The whole payload is compared (SetConstants compares every value at its offset). (d) Above. A static_assert ties the 41 names to the enum.
- SRV and UAV values are read through `SetRootConstantBufferViewArguments` (:247). The writers (dcl.h :361-389) and the replay (:574-599) already use that struct for SRV and UAV, so the layout matches.
- The counters are file-static with no lock. Execute runs only on the GPU Commands thread (inside EndSubmission), so that is safe. Constants with count 0 count as a repeat (mask 0), which is harmless for counting. The log prints about every 10 s, from Execute.

**Shared file.** cp.cpp is also in Agent 12's p2c (§30). The two commute: both orders give 027204B53A271D69, with offsets only.

**Verdict**

- **R1 stage 1: SAFE** at the default: one compare per draw and per successful resolve, with the same calls and return values. ON: **SAFE to test**, as a test bed (a small cost expected, not a win), per NOTE.md's test plan 1-8, including the held_query and held_pipelines positive controls, a run with `d3d12_readback_memexport=true`, the debug layer and a clean logdiff.
- **R2 step 1: SAFE** (compiled out; OFF = today's code). A counters build is for step 2's numbers only. Step 2 stays SAFE-IF (a)-(e) (§17).
- **Before landing:** Agent 7's syntax PASS (pending at 13:50; added here when it arrives), then a full SDK rebuild for the cp.h layout change.
- No UNSAFE.

**Read.** new/ cp.cpp :1182-1197, :2040-2054, :3098-3111, :3700-3719, :4110-4175, :4235-4300 and :4360-4409; cp.h :71-73 and :490-492; dcl.cpp :21-260 and :555-690; dcl.h :39, :328-389 and :612-623; the three diffs, NOTE.md and HASHES.txt; `t12_diffcheck.py r1r2` and `cross`. No builds, no runs.

**Sent** ~13:54 to 7, 1.

**Addendum (14:13; Agent 7, 14:05, and Agent 1, 14:07).** Agent 7's syntax result is in, and the 14:01 re-stage fixes my dcl.cpp comment nit. Both check out:

- Syntax **PASS**. `syntax-20261122-132724.txt` (Release, 13:27): 9 units × control/candidate = 18 compiles. All exit 0, and each unit has "no new diagnostics in the candidate" (control and candidate counts equal: 20, 12, 13 or 14). The units are cp.cpp, dcl.cpp with and without `REX_D3D12_DEFERRED_COUNTERS=1`, and the 6 live TUs that include the changed headers (graphics_system, pipeline_cache, primitive_processor, render_target_cache, shared_memory, texture_cache). No rexlego TU includes either header. That log's dcl.cpp candidate was the pre-nit file (183FF8FD…). `syntax-20261122-140147-only.txt` (14:01) re-runs both dcl.cpp variants on the final file (30FF5744…): exit 0, no new diagnostics, PASS.
- Re-stage (HASHES.txt 3B8DA461…; the old copies are in `pre-nit/`). `t12_nit.py`: dcl.cpp, r2-counters.diff and s4-r1r2.diff each differ from `pre-nit/` only in the same 3 `//` lines (dcl.cpp :110-112), with the same line counts (695, 433, 620). r1-split.diff is unchanged (2516F199…). New hashes: dcl.cpp 30FF57446EFB5D76, r2-counters.diff 5199910401AD86AC, s4-r1r2.diff BD0C4A93446149BB.
- Re-derived (`t12_diffcheck.py r1r2`, final files): s4-r1r2.diff on live (exact) gives all 4 `new/` files at offsets 0 (cp.cpp 760833A5…, cp.h 67F4E838…, dcl.h 9F6CC70A…, dcl.cpp 30FF5744…). r1-split + r2-counters = `new/`, and r2-counters also applies on live at offsets 0.
- p2c commute (`t12_diffcheck.py cross`): both orders still give cp.cpp 027204B53A271D69. The nit doesn't touch cp.cpp.
- The new comment (dcl.cpp :105-112) matches the code: each Execute replays into a native list that EndSubmission has just reset (cp.cpp :4287-4290), and an R1 split is an EndSubmission(false). That is cond (d) as rated above.

Row 32 stands. Confirmed for S4b: **s4-r1r2.diff BD0C4A93446149BB** (or r1-split.diff 2516F199… plus r2-counters.diff 5199910401AD86AC). Before landing, only the full SDK rebuild remains (cp.h layout).

**Sent** ~14:15 to 7, 1, 2.

## §32 Agent 9's N1-N4 fixes and the step 0 syntax compile (13:35-13:57; task #12 item 5)

**Asked (Agent 1, task #12 item 5):** a quick check of Agent 9's N1 fix and syntax result. N1-N4 are §26's nits on the #24 draft.

**Inputs.** `build/agent9/s4/fence-wait/`:

- `gpu_wait_backoff.cpp.draft` 01D9F8F3464C8614 (18,177 B, 395 lines, LF). §26 rated D176CA8D… (16,485 B, 372 lines);
- `gpu_wait_backoff.n1-n4.diff` 803B8382AA08E6F2 (git `--no-index` format, 13:33:32);
- `syntax/gpu_wait_backoff.cpp` = the draft (hash-checked);
- `syntax-20261122-132450.txt`: **RESULT: PASS**.

**The changes (my own diff of the rated copy against the draft, `t12_diffcheck.py n1 3`):** 10 hunks, each one N1-N4 or a comment, and no other code change.

- **N1, ParseUs:** `if (!s || *s < '0' || *s > '9') return false;` rejects "", "-5", "+5" and " 5", and the `*end` check rejects "5us". strtoul's overflow saturates and then clamps to the maximum (documented).
- Invalid values fail safe: a bad `LEGO_GPU_WAIT_SPIN_US` logs a WARN and the spin stays 30; a bad `LEGO_GPU_WAIT_BACKOFF_US` warns "not a plain number" and the back-off stays OFF.
- **N2:** the header's map check lists H0-H3: 27 → 31 hooked aliases.
- **N3:** the pch is cited at :120-129 (default tree) and :124-133 (B's pch).
- **N4:** a `sleep_ticks` atomic. QPC brackets SleepUs only when `c.stats` is set, through `Inc(std::atomic<uint64_t>& a, uint64_t n = 1)` (:207). The STATS line gains `sleep_sum {:.2f} ms` before `sleep_fail`: 26 placeholders, 26 arguments, matching types.
- Unchanged: with stats off, the sleep path's control flow is the rated one; with the env vars unset, every hook goes straight to `__imp__`, so OFF is unchanged.

**Syntax log.** B's exact devoffB flags (`build/agent2/snapB-off/compile_commands.json`), B's pch (A5FE0D4B…), clang 23.1.6:

- the control (native_lock_elide.cpp): 1 warning, getenv-deprecated;
- candidate (a), `-DLEGO_GPU_WAIT_HOOK_GETDATA=1`, and (b), without it: 3 warnings each, all getenv-deprecated; no new diagnostic text;
- the `-E` positive control: (a) defines H0-H3 (`sub_83FBF7D0`, `sub_83FAF180`, `sub_83FB09E8`, `sub_83FC0C10`) and (b) only H0-H1, as expected;
- lint (b): only the expected unused `kLrGetData*` and `t_l2`.

**Verdict**

- N1-N4: **fixed as asked**. Step 0's syntax compile: **done, PASS**.
- §26 stands. **Landing OFF: SAFE** once the rest of a9 S5.2.4 step 0 is done: grants, then a batch-nolr build with skip_lr off plus the map check expecting 31 aliases. ON: **SAFE to test** after steps 1-4.
- Caveat: the STATS line's field order changed (`sleep_sum` before `sleep_fail`), so any positional parser of "GPU wait stats" lines needs updating; parse by field name.
- No UNSAFE.

**Read.** The draft and its syntax copy (hashes), the n1-n4 diff, the syntax log, and my own diff of D176CA8D… against the draft. No builds, no runs.

**Sent** ~13:54 to 9, 1.

## §33 Agent 5's M1 non-temporal upload copy (13:30-13:57; task #12 item 6)

**Asked (Agent 1, task #12 item 6):** rate Agent 5's M1 when staged.

**Inputs.** `build/agent5/s4-m1/` (13:28):

- `m1-nontemporal-copy.diff` EBECE86E68369C88 (5,589 B, 5 hunks, +72/-3), on d3d12/shared_memory.cpp;
- base BB0838CE3909E18A (20,888 B) = #7's `new/` = S4a snap1; `new/` 2A5ADF13B5E433F1 (24,190 B, 555 lines);
- live = pristine B120D07C…, the file before #7;
- NOTE.md (13:28); `syntax-20261122-132054.txt`: PASS. The control and the candidate have the same 12 SDK-header warnings; none new.

**Re-derived (`t12_diffcheck.py m1`).** On the base and on S4a snap1, every hunk applies at offset 0 and gives `new/` byte for byte. It doesn't apply to live until S4a lands there.

**Code (new/ line numbers)**

- Includes: `<rex/platform.h>`, and `<emmintrin.h>` under `#if REX_ARCH_AMD64`. platform.h :78 defines `REX_ARCH_AMD64 1` on x64, and 5 SDK .cpp files already use the same test, so the SSE2 path is the one that builds here.
- Cvar `shared_memory_upload_nontemporal_copy`: bool, default false, GPU/D3D12, default lifecycle (it can change at run time; it is read per call).
- `CopyToUploadBufferNonTemporal` (~:189-219, anonymous namespace): the head, `(64 - (dst & 63)) & 63` clamped to the size, by memcpy; then 64 B blocks with 4 × `_mm_loadu_si128` and 4 × `_mm_stream_si128` (dst is 64-aligned after the head); the tail by memcpy; then one `_mm_sfence()`. The `#else` branch is a plain memcpy. Size 0 is fine.
- UploadRanges reads the cvar once per call, before the loop (:505). Per range: MakeRangeValid (:520), then the copy (:521-530: the helper, or the original memcpy with the same arguments), then D3DCopyBufferRegion (:531). The order is unchanged. #7's hash log (:539-551) reads guest memory, never the upload mapping.
- The ranges are 4 KB-aligned (RequestPartial), so in the game the head and the tail never run; only the 64 B blocks do.

**Ordering.** The upload heap is write-combined. The sfence orders the streaming stores before every later store, so they are visible before D3DCopyBufferRegion is recorded, and long before ExecuteCommandLists. The GPU reads the same bytes as after a memcpy.

**Overlap.** C1 doesn't touch d3d12/shared_memory.cpp. P3 (#9) does, so if P3 lands first, M1 needs a rebase.

**Verdict**

- **SAFE** at the default: one cvar read per UploadRanges call, and the copy is the original memcpy.
- ON: **output-identical** (the same bytes in the same order, fenced before the copy command is recorded) and **SAFE to test**.
- **Before ON:** Agent 5's microbench, with a head/tail correctness sweep (destination offsets 0-63 and sizes that aren't multiples of 64), because the game never runs those paths; then the OFF/ON functional pair. The timing gain is a hypothesis until measured.
- It applies only on top of #7 (S4a). No UNSAFE.

**Read.** The diff, the base and `new/`, NOTE.md, the syntax log, platform.h :78, and `t12_diffcheck.py m1`. No builds, no runs.

**Sent** ~13:54 to 5, 1.

**Addendum (14:05; Agent 5, 13:54 and 13:56).** The head/tail sweep that "Before ON" asks for is already in Agent 5's staged microbench, `bench/agent5/m1_copybench.cpp` AA3139068F09B28C (26,979 B, 13:41; syntax PASS with 0 diagnostics; not built or run):

- `CheckCase` (:289-330) fills guard bytes (0xCD, then 0x32) around dst, copies with the helper, reads back, and checks the lead guard, the copy (against src) and the tail guard.
- `RunCheck` (:332-362) covers dst offsets 0-63 × sizes 0-300 at each src offset, plus 7 large sizes (4095, 4096, 4097, 64 KiB + 17, 2 MiB, 2 MiB + 33, 3,844 KiB) × dst offsets {0, 1, 16, 63} × src offsets {0, 1}.
- main (:679-714) runs it on VirtualAlloc'd memory ("wb", src offsets 0, 1, 15, 33) and on the mapped 8 MiB upload-heap buffer ("upload", src offsets 0, 1). It exits 1 on any failure, 2 if there was no upload buffer (so that sweep didn't run), and 0 otherwise.
- The bench's `CopyToUploadBufferNonTemporal` (:105-135) is the helper in `new/` (:189-219): all 31 lines are identical (`t12_m1bench.py`).

So "Before ON" becomes: build the bench and run it without `--skip-check`. A pass is exit 0, with 0 failures on both check lines. Then comes the OFF/ON functional pair. Agent 5 also moves M1 behind C1: with C1 on, only 255-407 KB/f is left to copy, so M1's bound falls to ~0.2-0.3 ms/f. The verdict is unchanged.

**Sent** ~14:10 to 5, 1.

## §34 Agent 12's C1 v2 interdiff (13:50-14:10; task #12, after item 6)

**Asked.** Agent 12 (14:00): rate C1 v2, the v1 → v2 interdiff. Agent 1 moved it ahead of W4b so S4b can start right after. Agent 5 (13:54): C1 needs an A/B (u_block 0.9336, flat, against the 0.25 bar), so this rating comes before S4b.

**Inputs.** `build/agent12/s4-c1v2/`, staged 13:49:26-32. Hashes re-checked at 13:59 and unchanged:

- `v1-to-v2.diff` CE5D9DAEA4949C7D (4,770 B, 90 lines, 5 hunks, +43/-3), on SDK `src/system/xmemory.cpp` only: `v1/` 6C801EB2… (= C1 v1's `new/`) → `new/` DC23757AC206FCC5 (119,957 B, 2,842 lines);
- `keep-watch-v2.diff` 418D3D39947DB146 (571 lines, 20 hunks, +403/-4): the S4a output → C1 v2, replacing v1's `keep-watch.diff`;
- `keep-watch-rexlego.diff` 4D0C1079… (v1's, unchanged);
- `chain-live-to-c1v2.diff` DC882A5111EF169E (809 lines, 25 hunks, +596/-3), for reference;
- `make_c1v2.py` 8AC1412B…, `HASHES.txt` 0A24FFCB… (RESULT PASS), NOTE.md BCD4A96C… (10,899 B, 13:56:48);
- `syntax-20261122-134952.txt` B121A7C5…: PASS. The control (v1) and the candidate (v2) each have one diagnostic, the known unused parameter `global_lock_locked_once` (:2471 and :2511). None is new.

**Re-derived (`t12_diffcheck.py c1v2`): all PASS**

- `v1-to-v2.diff` on `v1/` (exact, offsets 0) gives `new/` DC23757A. My own udiff from v1 to v2 is also +43/-3.
- `keep-watch-v2.diff` on `orig/` and on S4a snap1 gives all 5 `new/` files at offsets 0: shared_memory.h 82A66445, xmemory.h 5A70782E, primitive_processor.cpp 470BA4BE, graphics/shared_memory.cpp A4A31038 and xmemory.cpp DC23757A. `orig/` = snap1 for all 5. It equals live for 3; the other 2 are S4a outputs (graphics/shared_memory.cpp 0BE4BADC, P2; xmemory.cpp 141FB1A9, fix (i)).
- The 4 other `new/` files equal v1's, and their keep-watch hunks are identical. xmemory.cpp goes from 6 hunks (+179/-0) to 7 (+220/-1); the -1 is #5's cvar line (V6).
- `chain-live-to-c1v2.diff` on live (exact) gives all 6 files, including d3d12/shared_memory.cpp = snap1 BB0838CE (#7).

**Code (new/ line numbers)**

- **V1/V6** (:46-57): `.lifecycle(kInitOnly)` on `physical_protect_keep_watch` and on `physical_protect_hold_global_lock`, plus a 2-line comment. The latter is #5's definition, edited inside this diff; #5's own diff (80CAD795…) is unchanged. `…_keep_watch_verify` keeps kRequiresRestart (a mid-run flip can only give false K lines).
- **V2** (:760-782): file-static `constinit std::atomic<uint64_t> physical_protect_kept_count{0}` and an `std::atomic<bool>` logged-once flag. `NoteKeptProtect` does a relaxed `fetch_add`. It logs the first kept protect (address, size), then at each power of two from 2 to 2048, then at every multiple of 4096. `NoteKeepWatchBlocked` does `exchange(true)` and logs once.
- **V3** (:2271): `NoteKeptProtect(address, size)` runs just before the keep-watch `return true`, with G held (`hold_global_lock.owns_lock()` is in the condition at :2269).
- **V4** (:2313): `NoteKeepWatchBlocked()` runs at ProtectKeepWatch's latch check (:2312), under G.
- **V5** (:151-162): in Memory::Initialize, before "Reserving the guest memory arena...", and only when keep_watch is on. It logs INFO "blocked" (native), WARN "hold_global_lock is off" (no protect is kept), or INFO "on (with …)". The launch values are final by then: cvar::Init (windowed_app_main_sdl.cpp :40), LoadConfig (rex_app.cpp :224, :277), logging (:293), then the runtime (:343, :356) → Memory::Initialize (runtime.cpp :150).
- OFF: V3 and V4 sit only on the ON branch, V5 is one cvar read at init, and V1/V6 are metadata only. So the default runs v1's path, which is the S4a path (§28).

**Logging under G.** V3 logs 12 lines up to 4,095 kept protects, then one per 4,096; V4 logs once. G is recursive, and a log call takes only the logger's own locks, so the lock order doesn't change. NOTE's precedent is slightly off: AccessViolationCallback's lines (new :658, :673) come after G has gone by value into TriggerCallbacks (:605; xmemory.h :323), so they run without G. PhysicalHeap::Decommit (:2211) and Release (:2226) do log under G. No change needed.

**kInitOnly.** It closes my mid-run toggle case (§24) in the settings overlay only:

- settings_overlay.cpp :531-536 draws kInitOnly entries disabled, with an " [init-only]" badge (:192) and the tooltip "Read-only - set at initialization only" (:549).
- cvar.cpp :311: SetFlagFromSource rejects a kInitOnly set only once `IsFinalized()`. `FinalizeInit()` has no caller (`git grep`: cvar.h :125 and cvar.cpp :719 only; none in the game repo). So launch sets work (command line, env, toml/LoadConfig), but so does any later set.
- The dev console (console_overlay.cpp :221) calls SetFlagByName, which sets with Source::kRuntime, the top rank (cvar.cpp :343; cvar.h :144-150). So it can still flip both cvars mid-run. kRequiresRestart wouldn't stop it either: cvar.cpp :320-327 applies the value, then calls MarkPendingRestart. kInitOnly is the right lifecycle; the gap is the missing FinalizeInit.

**Verdict**

- The interdiff is exactly V1-V6. Every apply and chain re-derives, and syntax is PASS.
- **SAFE** at the default: v1's path (§28), plus one cvar read at init. The only visible change is that both entries are read-only in the overlay.
- **Gate D is met** by the kept count and its lines. They are also A's positive control (a kept protect shows up as a line). V4/V5 give C a positive check on native ("blocked", and no "kept").
- ON: **SAFE to test**. §24/§28 now apply without the counter condition. NOTE's test plan: set both cvars at launch; cover the title, a menu walk and a level load; D's zero lines still apply; the native control shows "blocked" and no "kept"; one run with the hold off shows the WARN and no "kept".
- **Test rule:** don't touch either cvar in the dev console during a C1 run, because kInitOnly doesn't enforce that here.
- **Before default-ON, or landing beyond tests:** Agent 12's init latch (read both cvars once in Memory::Initialize, and have Protect use the latched values). Calling `rex::cvar::FinalizeInit()` after config load would also close the gap, but it changes every kInitOnly cvar, so it would need its own rating.
- Nit: on native with C1 ON, V4's `exchange` runs on every protect that reaches the latch; a relaxed load first would skip it. Negligible.
- Landing is as for v1 (§28): on top of S4a, `keep-watch-v2.diff` plus the unchanged rexlego diff (keep CRLF: memory_watch.cpp → 70829846…); a full SDK install and game rebuild; re-pin the native baselines. No UNSAFE.

**Read.** The interdiff, keep-watch-v2 and the chain; `v1/` and `new/` xmemory.cpp (:46-57, :151-162, :567-680, :760-782, :2200-2320); NOTE.md, HASHES.txt and the syntax log; cvar.h :125, :137, :144-150; cvar.cpp :83-94, :298-344; settings_overlay.cpp :505-560; console_overlay.cpp :205-227; rex_app.cpp :212-300; runtime.cpp :149-150; `t12_diffcheck.py c1v2`; read-only `git grep`. No builds, no runs.

**Sent** ~14:10 to 12, 1, 5.

## §35 Agent 12's C1 v3 interdiff (14:28-14:45; task #12, after §34)

**Asked.** Agent 12 (~14:27): rate C1 v3, which adds the init latch from §34 plus nit 2. Agent 1 (14:28): rate it now, before #26. If v3 is SAFE before the S4b build starts, S4b takes `keep-watch-v3.diff` instead of v2, at the same step with the same rexlego diff; otherwise S4b uses v2 as rated.

**Inputs.** `build/agent12/s4-c1v3/`, staged 14:22:38 (NOTE.md 9C9DCDCF…, HASHES.txt 0C5D3304…, make_c1v3.py 3FD56FD0…):

- `v2-to-v3.diff` 1FC8E2DCC452A6EF (4,747 B, 80 lines, 6 hunks, +24/-6), SDK `src/system/xmemory.cpp` only: `v2/` DC23757A… (= C1 v2's `new/`) → `new/` BCA5E1CF63686E73 (121,109 B, 2,860 lines);
- `keep-watch-v3.diff` DECCFE3373C27C3C (597 lines, 20 hunks, +422/-5): the S4a output → C1 v3, replacing `keep-watch-v2.diff` 418D3D39…;
- `keep-watch-rexlego.diff` 4D0C10794188CF45 (v1's, unchanged);
- `chain-live-to-c1v3.diff` 0E61E1D07C2BAB99 (829 lines, 25 hunks, +614/-3), for reference;
- `syntax-20261122-142307.txt` A82E9C879059AAC3: PASS. The control (v2) and the candidate (v3) each have one diagnostic, the known unused parameter `global_lock_locked_once` (:2511 and :2529). None is new.
- v2 is untouched: `s4-c1v2/new/` xmemory.cpp is still DC23757A, keep-watch-v2.diff 418D3D39 and NOTE.md BCD4A96C.

**Re-derived (`t12_diffcheck.py c1v3`): all PASS**

- `v2-to-v3.diff` on `v2/` (exact, offsets 0) gives `new/` BCA5E1CF. My own udiff from v2 to v3 is also +24/-6.
- `keep-watch-v3.diff` on `orig/` (exact) and on S4a snap1 (offset search, every offset 0) gives all 5 `new/` files. `orig/` = snap1 = v2's `orig/` for all 5.
- The 4 other `new/` files equal v2's (82A66445, 5A70782E, 470BA4BE, A4A31038), and their keep-watch hunks are identical to v2's. Only xmemory.cpp changes, from +220/-1 to +239/-2 against S4a. The extra -1 is fix (i)'s `REXCVAR_GET` line in Protect.
- `chain-live-to-c1v3.diff` on live (exact) gives all 6 files, including d3d12/shared_memory.cpp = snap1 BB0838CE (#7).

**Code (new/ line numbers)**

- **L0** (:53-54): the cvar comment now says that Memory::Initialize latches both.
- **L1** (:62-67): `physical_protect_hold_global_lock_latched` and `physical_protect_keep_watch_latched`. Both are file-static `constinit std::atomic<bool>{false}`, at the top of `namespace rex::memory`.
- **L2** (:159-164): Memory::Initialize reads both cvars once into `hold_on` and `keep_on`, then stores them (relaxed). This runs right after `file_name_`, before the arena and before any heap. V5's state line uses the same locals, with the same text and conditions.
- **L3** (:2277-2278, :2286-2287): Protect's hold condition (fix (i)) and C1's gate load the latches (relaxed).
- **N2** (:791-793): NoteKeepWatchBlocked loads the logged flag before its exchange. Two threads can both see false, but the exchange still picks one, so the line prints once.
- Read sites: the only `REXCVAR_GET`s of either cvar are :161-162. In the S4a snap1 SDK the only other read was fix (i)'s :2147, which L3 replaces (`git grep --no-index` over snap1 `src` and `include`). Nothing in the game repo or in `harness/legodimensions.toml` names either cvar. graphics/shared_memory.cpp :381 reads only `…_keep_watch_verify`.

**Latch timing.** The launch values are final before the store:

1. cvar::Init (windowed_app_main_sdl.cpp :40);
2. LoadConfig (rex_app.cpp :224, :277);
3. ConstructRuntime (:203, or :681 after the paths wizard) → `runtime_->Setup` (:356) → Runtime::Setup (runtime.cpp :104) → Memory::Initialize (:150).

Every heap, and every thread that can call Protect, is created after the store, so relaxed ordering is enough. A later set (dev console, kRuntime) changes the value the cvar shows, but not the latch. A restart applies it.

**Verdict**

- The interdiff is exactly L0-L3 and N2. Every apply and the chain re-derive, and syntax is PASS.
- **SAFE** at the default: v2's path and log (§34). Protect does two relaxed loads in place of two cvar reads, and init does one more cvar read.
- ON: **SAFE to test**, the same as v2 when set at launch. §34's test plan is unchanged. §34's test rule relaxes: a mid-run console flip can no longer reach Protect. It only shows a value that isn't in effect.
- **My §34 condition is met.** v3 is fit for S4b in place of v2: on top of S4a, apply `keep-watch-v3.diff` DECCFE33… at the same step, then the unchanged rexlego diff 4D0C1079… (keep CRLF). Default-ON, or landing beyond tests, still waits for the ON results (gate D, A's positive control, C's native check).
- Nits, no change needed:
  - after a mid-run set, the console and the overlay show a value that isn't in effect;
  - `…_keep_watch_verify` is still read live (kRequiresRestart; a flip can only give false K lines);
  - a second Memory::Initialize in one process would re-latch, which is right for a new arena.
- Landing is as for v2 (§34, §28): a full SDK install and game rebuild, then re-pin the native baselines. No UNSAFE.

**Read.** The interdiff; keep-watch-v3 and the chain (re-applied); `new/` xmemory.cpp at every cvar and latch line; NOTE.md and the syntax log; rex_app.cpp :160-300 and :322-356; runtime.cpp's function list (:104, :150); `t12_diffcheck.py c1v3`; read-only `git grep` (live SDK, snap1 with `--no-index`, game repo). No builds, no runs.

**Sent** ~14:45 to 12, 1, 2.

## §36 Agent 9's #26: db16cyc → PAUSE, codegen option `db16cyc_pause` (14:22-14:45; task #12, after §35)

**Asked.** Agent 9 (~14:22): rate #26, staged under his task #17 from Agent 1. Agent 1 (14:28, corrected 14:31): C1 v3 first, then #26, both by 15:00 if I can.

**Inputs.** `build/agent9/s4/spin/db16cyc-pause/` (HASHES.txt 2A94639C…, stage.py 21EACD7B…, syntax_check_codegen.ps1 44678FD4…):

- `db16cyc-pause.diff` AC554DBBD965BF94 (1,969 B, 3 files, +9/-2), applied from the SDK root with -p1. Its base is live c5fe668 = snap1 for all 3 files:
  - config.h D07C575F → CD39B0E1 (+1);
  - config.cpp 0ED529B7 → 4706A7F2 (+2);
  - builders/system.cpp D1269273 → FAD43720 (+6/-2).
- `toml-db16cyc-pause-A.diff` 95D901B9784705FA: live = snap1 `rexlego/legodimensions_config.toml` 7F775847 → 11707872. `db16cyc_pause = true` goes at L24, just before `[functions]` (L25). The file has no other root key.
- `toml-db16cyc-pause-B.diff` 5D5892D33D09AF9D: snapB = batch-nolr config E60EAF1C → FFC119BF. The line goes at L37, after `musttail_calls = true` and among the other root keys; `[functions]` is at L41.
- `syntax-20261122-141452.txt` 1057617D…: PASS (below).

**Re-derived (`t12_diffcheck.py db16 scan`): all PASS**

- The SDK diff applies exactly (offsets 0) on `base/`, the live SDK and the snap1 SDK, and gives `new/` each time.
- Toml A applies exactly on base-A, live and snap1; toml B on base-B, snapB and batch-nolr. Each gives the staged `new-*`. In both results no table header comes before the key, so it is a root key. It is read the same way as the B arm's existing root keys, through `hasBool` and `MergeBool` (config.cpp :70, :102-130).
- The TU383 candidate B35C1310, minus its 8 `\tsimde_mm_pause();` lines, equals the snapB control AE1749B6 byte for byte. Every pause line follows a `\t// db16cyc ` line.
- Census of every generated TU, both matching Agent 9's lists:
  - A (snap1 and live, 440 files): 20 db16cyc sites in TUs 107, 116, 125, 153, 169, 205, 284, 304, 321 and 432;
  - B (snapB, 432 files): 20 sites in TUs 107, 162, 265, 281, 329, 354, 378, 383, 389 and 394.
- Both trees hold the same 10 functions: sub_83FAF180 (8 sites); sub_83F99F80, sub_83FCB608 and sub_83F9A5B0 (2 each); sub_83E64900, sub_83EA90D0, sub_83E66CD8, sub_83E70320, sub_83E96348 and sub_83E63F38 (1 each). Neither tree has a `simde_mm_pause` today, so the post-regen count of 20 is exact.

**Code.**

- config.h :110: `bool db16cycPause = false;`.
- config.cpp :129-130: MergeBool from the root key `db16cyc_pause`.
- system.cpp `build_db16cyc` (:51; dispatched from instruction_dispatch.cpp :322) emits `\tsimde_mm_pause();` when the option is on, and nothing otherwise. The literal has no braces, so it is a valid fmt format string; the system.cpp candidate compiled.

**OFF.** Byte-identical. With no toml line, nothing new is emitted. The option is not in FingerprintModule's flags (project_recompiler.cpp :79-101: the templates, exception handlers and size limits only), nor in config_flags (codegen_writer.cpp :288-297, 8 flags). So a rebuilt tool skips the regen, and a forced one writes identical files (WriteIfChanged, codegen_writer.cpp :694).

**ON.** Output-identical: db16cyc changes no architectural state, and neither does PAUSE. Only timing changes.

- sub_83FAF180 is the back-off step of a GPU-progress wait. All 6 direct callers (B TUs 53, 230, 275, 311, 352, 359) run the same loop:
  1. sub_83FAF088 sets up;
  2. call sub_83FAF180, and exit if it returns 0;
  3. test a device word (+11024/+11036, +16968/+16976, or a fence-like value) and branch back to step 2.
- Its body is `cctpl`, 4 × 8 db16cyc, `cctpm`, then a no-progress watchdog. The watchdog compares the time since the watched word last moved against a global threshold, and only then calls sub_83FC91D0. Its clock (r30) is loaded through r13, not counted here, so PAUSE doesn't stretch the watchdog. I didn't confirm what that field holds.
- Today the 4-pass loop has an empty body (B: local ctr), so clang can delete it. PAUSE is a side-effecting builtin, so the loop stays: 32 PAUSEs per poll. That is ~1.1-1.5 µs on Skylake and later (~140 cycles each) and less on older Intel and on Zen, against Xenon's ~160 ns. Each wait then wakes at most one back-off later. The gain (less polling, the SMT sibling freed) is a hypothesis.
- I didn't inspect the other 9 functions (12 sites). Four of them have no direct caller.

**Syntax log (PASS).** clang 23.1.6, each TU with its own compile_commands entry:

- the system.cpp and config.cpp candidates exit 0 with no new diagnostics;
- the negative run without the new config.h fails on `db16cycPause`, so the new header was used;
- the TU383 candidate exits 0 with no new diagnostics.

**Verdict**

- **Landing OFF: SAFE.** It changes the codegen tool only. The generated tree, the stamp and the game build stay byte-identical.
- ON: **output-identical, SAFE to test.** Gates:
  1. The toml line lands with the new tool, in the same build. An old tool ignores the key and regens to identical output, and the stamp then holds the new toml hash. A later new tool would skip the regen, so ON would never take effect. If that happens, force one regen with the new tool.
  2. After the regen, `simde_mm_pause` appears exactly 20 times, in exactly the 10 TUs of the arm's list. Any other count fails the step.
  3. Keep codegen.partition.json: a fresh output dir renumbers every TU.
  4. Run the OFF/ON functional pair plus a frame-time A/B. Measure it apart from #24 (the host-side GPU-wait back-off), since both change how waiting behaves.
- If the A/B shows added latency, one option is one PAUSE per run of db16cyc: 4 per poll in sub_83FAF180, ~140 ns on Skylake and later, about Xenon's delay. It is not staged.
- Cost: ~130 s regen, the 10 TUs (~36 s for the longest), a ~5.5 s link, plus the codegen-tool rebuild. S4b is a full rebuild anyway. No UNSAFE.

**Read.** The three diffs (re-applied); HASHES.txt, stage.py and the syntax log; base-B toml L1-45 and base-A L14-32; project_recompiler.cpp :70-105; codegen_writer.cpp :276-325; config.cpp's `hasBool`/`MergeBool` lines; syntax TU383 :37095-37262; the 6 callers in snapB (`t12_db16ctx.py`); `t12_diffcheck.py db16 scan` (one process, BelowNormal). No builds, no runs.

**Sent** ~14:45 to 9, 1.

## §37 Agent 9's #24 S4c package: the GPU-wait back-off TU and its CMake block, with #30's CMake option (16:00-16:20; task #23 item 2)

**Asked.** Agent 1 (task #23 item 2, 15:35): rate Agent 9's #24 CMake package, with #30 if included, for landing OFF as an incremental S4c on top of S4b. Agent 9 (15:59, his task #22): rate the primary and the fallback diff.

**Inputs.** `build/agent9/s4/fence-wait/s4c/` (HASHES.txt 0489BC9F99D87878, PACKAGE.md 596E666D…, stage.py 3FF7FAE3…, maplines.py C4D1D339…, syntax_check_s4c.ps1 F24A9DBC…):

- `s4c-24-30.diff` DC02104EA76E0BF6 (20,630 B), the primary, applied with -p1 from `DimensionsRecomp/`:
  - `rexlego/CMakeLists.txt`: 2 hunks, +22/-0 (`@@ -153,6 +153,19 @@` for #30 and `@@ -165,6 +178,15 @@` for #24), all 34 hunk lines CRLF;
  - the new `rexlego/src/gpu_wait_backoff.cpp`: +395, LF.
- `s4c-24-only.diff` A279DC71D6CD4FAA (19,555 B), the fallback: the #24 hunk only (`@@ -165,6 +165,15 @@`) and the same new file.
- `base/` CMakeLists 3690D5D76AA9FBED (51,070 B, 885 CRLF lines); `new/` 1BF46D7878BA9A25 (52,311 B, 907); `new-24only/` 9A4606A7031375F7 (51,537 B, 894); `new/` gpu_wait_backoff.cpp 01D9F8F3464C8614 (18,177 B, 395 LF lines).
- The three checks: `apply-check.txt` 88125952… (PASS), `syntax-20261122-155218.txt` BE15A7A8… (PASS) and `expected-map.txt` 3F05E312… (PASS).

**Re-derived (`scratch/t23_s4c.py`, my strict applier from `t12_diffcheck.py`): all PASS**

- All 17 HASHES.txt rows match by full SHA-256, size and CR/LF counts.
- The CMakeLists is 3690D5D7… in live, snap1, snapB and `base/`. None of the three trees has the TU yet.
- Each diff applies exactly at its stated lines (offsets 0) on all four bases. The primary gives `new/` and the fallback `new-24only/`, CRLF throughout with no lone CR or LF.
- The new file, from either diff, equals the draft 01D9F8F3… that §32 rated. Its CRLF form is 34D281E006FB5FBE (18,572 B), HASHES.txt's "info" row.
- The fallback's hunk body equals the primary's second hunk, and the two TU hunks are identical, so the fallback is the primary minus the #30 block.
- difflib, base → `new/`: two inserted blocks (13 and 9 lines) and no other change. The fallback has the 9-line block only.
- Line positions in `new/`: the NATIVE_GPU option (:22) and `set(LEGODIMENSIONS_SOURCES` (:25) come before both blocks. The SCENE_WALK option is at :159 and `if(NOT LEGODIMENSIONS_NATIVE_GPU)` at :184. `add_executable` follows at :191/:194, and nothing reads the source list after it. The fingerprint input set moves from :582 to :604 (fallback :591).

**CMake read (`new/` :150-196)**

- #30 (:156-167): `option(LEGODIMENSIONS_SCENE_WALK_PROBE … OFF)`. OFF adds one cache entry and nothing else. ON stops the configure with a FATAL_ERROR until `src/scene_walk_probe.cpp` exists. Then it appends that file and gives `LEGODIMENSIONS_SCENE_WALK_PROBE=1` to native_memops.cpp and native_skin_diagnostics.cpp only. It isn't tied to NATIVE_GPU (the spec has a devoff and a native3d probe build).
- #24 (:181-188): inside `if(NOT LEGODIMENSIONS_NATIVE_GPU)`, it appends `src/gpu_wait_backoff.cpp` and gives that file alone `LEGO_GPU_WAIT_HOOK_GETDATA=1`, the set_property pattern of :151-152. It sits after the DEV_PROBES block and before `if(WIN32)`, so the append reaches add_executable.

**OFF (the rated file, unchanged)**

- With `LEGO_GPU_WAIT_BACKOFF_US`, `LEGO_GPU_WAIT_SPIN_US` and `LEGO_GPU_WAIT_STATS` unset, Cfg() (:119-149) logs nothing: its WARNs need a non-empty invalid value, and its INFO line needs ON or STATS. Every hook then calls `__imp__` at once (§26 item 5, §32).
- No duplicate hook on Xenos. In live `rexlego/src`, sub_83FB09E8 and sub_83FC0C10 are hooked only in native-only files (`gpu_native/queries.cpp:320`, `gpu_native/hooks_device.cpp:340`), and sub_83FBF7D0 and sub_83FAF180 nowhere. Of the staged diffs in every `build/*/s4*` dir, only the S4c pair (and the old n1-n4 draft diff) name the four functions or touch rexlego/CMakeLists.txt. A duplicate would fail the link anyway.

**Build effects**

- Both trees re-run CMake (7-25 s each, Agent 2).
- Xenos (devoff): one new TU and a relink. No other TU's command line changes: the define is source-scoped, and #30 OFF adds nothing.
- Native: no new TU, but CMakeLists.txt is the fingerprint's first input. At build time the fingerprint script (:766-787) hashes every input and rewrites `generated/native_gpu_build_info.h`, so its includers recompile: `gpu_native/device.cpp` (:37), `shader_archive.cpp` (:22) and `pipeline_library.cpp` (through `pipeline_recipes.h` :18). The relinked binary embeds the new fingerprint, hence the re-pin. PACKAGE.md's "Native: nothing new compiles" holds for new TUs only.
- One re-pin: C1's `memory_watch.cpp` (S4b) and this CMake edit (S4c) each change the native fingerprint, and #26's toml line would too if #26 goes ON (`legodimensions_config.toml` is input :588). Re-pin native3d and nativeB once, after the last of them lands, or fold S4c into S4b (no file overlap). That is Agent 1's call (S4-DRAFT L413).

**Syntax log (PASS).** clang 23.1.6 `-fsyntax-only` with the S4a devoff4 flags (`snap1-off` compile_commands, 477 entries):

- the control (native_lock_elide.cpp) and the TU with and without the define all exit 0;
- the only warnings are getenv deprecations: 1 in the control and 3 in each TU run;
- `-E` finds H0-H3 with the define and H0-H1 without.

These are S4a's headers, so Agent 2's S4b-then-S4c build is the real compile check.

**Map gate.** My census of the devoff4 map (DCC51E2B7A0040E2, 39,162,310 B):

- 164,786 `sub_` and 164,786 `__imp__` names, no duplicates, and 27 hooked aliases: crash_guards 2, main_menu_extras 3, name_trace 5, native_atomics 3, native_constants 1, native_lock_elide 7, native_markers 2, native_memops 2, scene_distance 2.
- All 4 targets are unhooked: each `sub_` sits at its `__imp__` address, in recomp .248 (sub_83FBF7D0), .107 (sub_83FAF180), .422 (sub_83FB09E8) and .232 (sub_83FC0C10).
- expected-map.txt's 31 names are exactly today's 27 plus the 4.

Gate, for Agent 2: the S4c devoff map holds the S4b devoff map's hooked set plus exactly these 4 (31 if S4b keeps 27; 29, H0-H1 only, would mean the define is missing). Each new `sub_` is in `gpu_wait_backoff.cpp.obj`, and each `__imp__` stays in the same recomp object as in the S4b map. Don't gate on exact addresses ("stays at 0001:…") or on TU numbers: those are devoff4's A-partition layout, and a B-tree build numbers them differently (sub_83FAF180 is B's TU383, §36). The rexlego objects link after the recomp range (0001:00000050-096d2e30; the hooked ones at 0970ea40-097a1aa0), so the recomp `__imp__` addresses will probably not move, but the gate doesn't need that. In either tree skip_lr stays off (H2's lr gate, §26 item 3).

**Interactions**

- S4b: no S4b diff touches rexlego/CMakeLists.txt or these hooks, so S4c applies to S4b's output as staged. PACKAGE.md's step 1 (CMakeLists still 3690D5D7… before the apply) confirms it.
- #26 (in S4b): additive. H1 always calls `__imp__sub_83FAF180`, so with #26 ON its PAUSEs still run inside. Measure #24 apart from #26 (§36 gate 4).
- EOL: a git apply inside the live repo (`core.autocrlf=true`, `* text=auto`) can write the TU as CRLF, 34D281E0… (the same text); GNU patch or a copy keeps LF, 01D9F8F3…. Either is fine; Agent 2's record should say which.

**Verdict**

- **Landing OFF: SAFE**, for the primary and the fallback. Output-identical at the default: pass-through hooks that log nothing while the env vars are unset, plus an inert option. The package is the rated draft, byte for byte, plus 22 (or 9) CMake lines.
- Before landing:
  1. the grants for `rexlego/CMakeLists.txt` and the new TU (Agent 1 / the user);
  2. Agent 2's S4b-then-S4c build: CMakeLists 3690D5D7… before the apply and 1BF46D78… (fallback 9A4606A7…) after; the TU 01D9F8F3… or 34D281E0…; devoff +1 TU; native recompiles the three fingerprint-header includers;
  3. the map gate above: +4 over S4b's devoff map, by name and object;
  4. one native re-pin, after the last fingerprint change (Agent 1's call: after S4c, or S4c folded into S4b).
- Primary or fallback: the same risk. The primary saves a later CMake edit for #30's probe build. The probe's own `#ifdef` lines in native_memops.cpp and native_skin_diagnostics.cpp (fingerprint inputs :753 and :634) will change the native fingerprint again whenever they land.
- #30 ON: not rateable until `src/scene_walk_probe.cpp` and those `#ifdef` lines exist (a9 S4.2.4). It is a separate build and never timed.
- #24 ON: §26 items 4-6 (PACKAGE.md's steps 1-4), unchanged.
- No UNSAFE.

**Read.** PACKAGE.md and HASHES.txt; both diffs (re-applied); `new/` CMakeLists :150-196; base :258-290 and :440-505; the fingerprint lines (:582, :766-802) and `build_info.h.in`; the TU's Cfg() (:96-175) and its hook lines; the syntax log and expected-map.txt; the devoff4 map (census); read-only `git grep` and `git log` of the live game repo; a name and CMake search of every staged `build/*/s4*` diff. No builds, no runs.

**Sent** ~16:20 to 9, 1.

## §38 Agent 2's folded S4b + S4c compose check (19:31-19:45; task #9 item 1, old #34)

**Asked.** Agent 1 (task #9, resumed from #34; 'go' 19:31): rate Agent 2's folded S4b + S4c compose check, C1 v3 → M1 → P2c → r1r2 → #26 OFF → S4c. FYI from Agent 1 (decision 1, the user, 17:27: YES): Agent 3 may use generated virtual Toy Pad tags in its hidden-desktop runs, so C1 ON's verify-mode level load (§21 A) can run in the S4b queue (its rows 7, 20 and 23).

**Inputs.**

- The report `build/agent2/s4b-compose-1932-c1v3.txt` 77F0017A3050E483 (12,894 B, 19:32:33), written by `build/agent2/s4b-compose-check.py` D08B74E0D86E7F14 (25,401 B, 17:03:15) with `--c1 v3` and S4c `24-30`. Its scratch is `build/agent2/s4b-check/` (`o1-v3`, `o2-v3`, `s4c-24-30`).
- The 7 diffs, each = the hash I rated: keep-watch-v3.diff DECCFE3373C27C3C (§35), keep-watch-rexlego.diff 4D0C10794188CF45 (§24), m1-nontemporal-copy.diff EBECE86E68369C88 (§33), memexport-full-buffer-counter.diff 29E02E249EDDFEFD (§30), s4-r1r2.diff BD0C4A93446149BB (§31), db16cyc-pause.diff AC554DBBD965BF94 (§36), s4c-24-30.diff DC02104EA76E0BF6 (§37).

**What the script does** (read in full; it writes only under `build/agent2/s4b-check/`):

- [1] hashes each staged diff against its staging record;
- [2] checks the 13 SDK bases: snap1 = the first step's staged "before", and live = snap1;
- [3a]/[3b] applies the SDK chain in two orders, o1 (P2c → r1r2, the asked order) and o2 (r1r2 → P2c), with `git -c core.autocrlf=false apply --verbose` on scratch copies outside any work tree. It checks every after-hash against the step's record; a file an earlier step changed is checked against its lone-apply record and flagged as chained;
- [4] compares the o1 and o2 finals (full SHA-256 and size);
- [5] memory_watch.cpp: the base, the diff and the staged after-file. A plain `apply --check` on the CRLF file fails (the diff is LF), so the file lands by copying the staged after-file, my §29 rule;
- [6] S4c on a scratch copy of the snap1 CMakeLists: the base, the absent TU, the apply, #30's option line, #24's block, and the TU's name counts (H0-H3 and the three env vars).

Result: **0 FAIL** (3.0 s). Offsets appear only on the chained cp.cpp: in o1, r1r2's hunk 2 at +9 and hunks 3-5 at +10; in o2, P2c's hunks 1-4 at +12 and hunk 5 at +22. No fuzz. Not covered: the toml (no step touches it, but nothing asserts it), the git HEADs (it checks content only), and the build effects (map, fingerprint), which are build gates below.

**Re-derived: all PASS.** Three independent applies of the chain to S4a give the same 16 files: Agent 2's git apply (o1 and o2), my strict applier (`scratch/t34_compose.py chain`, built on `t12_diffcheck.py`, 19:32) and GNU patch (a subagent, below).

- The HEADs are still S4a: SDK 3bb65bb, game 1bd322e. Every S4a base is the same in git HEAD, live and snap1.
- Each step applies at offsets 0 on its own base. The chained cp.cpp offsets match git's: [0, 9, 10, 10, 10] for r1r2 after P2c, and [12, 12, 12, 12, 22] for P2c after r1r2.
- The 15 single-step files equal their step's staged `new/`. cp.cpp is 027204B53A271D69 in both orders: the two steps' hunks are at least 16 lines apart (§31 addendum).
- The finals:

| File | After | Size, EOL | S4a | Step |
|---|---|---|---|---|
| SDK `include/rex/graphics/shared_memory.h` | 82A66445ED98B091 | 13,051 B, LF | 4D861738A94B556B | C1 v3 |
| SDK `include/rex/system/xmemory.h` | 5A70782EF00F0FB6 | 31,430 B, LF | 80100865A654AF04 | C1 v3 |
| SDK `src/graphics/primitive_processor.cpp` | 470BA4BED73B2ABF | 79,790 B, LF | E07F690223B564AE | C1 v3 |
| SDK `src/graphics/shared_memory.cpp` | A4A31038ABDFF94A | 32,711 B, LF | 0BE4BADCAC666BEE | C1 v3 |
| SDK `src/system/xmemory.cpp` | BCA5E1CF63686E73 | 121,109 B, LF | 141FB1A947D59156 | C1 v3 |
| game `rexlego/src/gpu_native/memory_watch.cpp` | 70829846C4F321A9 | 8,054 B, CRLF (172 lines) | 19AE1606C6DB7273 | C1 rexlego |
| SDK `src/graphics/d3d12/shared_memory.cpp` | 2A5ADF13B5E433F1 | 24,190 B, LF | BB0838CE3909E18A | M1 |
| SDK `src/graphics/d3d12/command_processor.cpp` | 027204B53A271D69 | 273,790 B, LF | 3AB3AA5360D4E987 | P2c + r1r2 |
| SDK `include/rex/graphics/d3d12/command_processor.h` | 67F4E8380C879377 | 41,218 B, LF | 41F32B80BABA213C | r1r2 |
| SDK `include/rex/graphics/d3d12/deferred_command_list.h` | 9F6CC70A6922232D | 26,607 B, LF | DA2F58B6CE3D7F6A | r1r2 |
| SDK `src/graphics/d3d12/deferred_command_list.cpp` | 30FF57446EFB5D76 | 34,034 B, LF | FFDF7FB66EC81715 | r1r2 |
| SDK `include/rex/codegen/config.h` | CD39B0E110D3E0FD | 7,032 B, LF | D07C575FF2904B87 | #26 |
| SDK `src/codegen/config.cpp` | 4706A7F22C3859D6 | 23,701 B, LF | 0ED529B7E5F0F4E7 | #26 |
| SDK `src/codegen/builders/system.cpp` | FAD4372074D32D69 | 12,947 B, LF | D1269273636B5A1A | #26 |
| game `rexlego/CMakeLists.txt` | 1BF46D7878BA9A25 | 52,311 B, CRLF (907 lines) | 3690D5D76AA9FBED | S4c |
| game `rexlego/src/gpu_wait_backoff.cpp` | 01D9F8F3464C8614 (CRLF form 34D281E006FB5FBE) | 18,177 B, LF (395 lines) | absent | S4c |

- `cmp` of Agent 2's `s4b-check/o1-v3`, `o2-v3` and `s4c-24-30` trees against my finals: every file there is identical.
- Every hash in the report is accounted for. Beyond the table there are only 760833A5D7D89ADC (r1r2 alone on S4a; it equals `build/agent7/s4-r1r2/new/sdk/src/graphics/d3d12/command_processor.cpp`, the §31 file) and A279DC71…/9A4606A7… (S4c's fallback diff and its CMakeLists, §37; informational).

**GNU patch (subagent, 19:35-19:43).** GNU patch 2.8.1 (Git for Windows `usr/bin/patch.exe`), each step with `--binary --verbose --forward --no-backup-if-mismatch -p1`, dry run first. The bases came from `git cat-file --filters` at 3bb65bb and 1bd322e; all 16, and the toml, equal live and snap1. Result: all 16 finals are byte-identical to mine, to the report's hashes and to Agent 2's three scratch trees. Fuzz 0 everywhere, no rejects. Its hunk messages match Agent 2's git apply word for word: in chain order r1r2's hunks 2-5 land at 1194 (+9), 3114, 3712 and 4369 (+10); in reverse order r1r2 alone gives 760833A5… and P2c then lands at 247, 273, 292, 301 (+12) and 3092 (+22), giving 027204B5…. Two EOL notes:

- memory_watch.cpp: the LF diff with `--binary` is refused ("different line endings"). Without `--binary`, patch exits 0 but rewrites the whole file as LF (18DE0334BA318CE5, 7,882 B): a silent trap. The subagent applied a CRLF-body copy of the diff with `--binary` and got 70829846…. So gate 1 below is a hash check, not an exit code.
- The new TU lands LF (01D9F8F3…). The repo's checkout filters would make it CRLF (34D281E0…) after a commit and a fresh checkout. Both are accepted (§37).

**r1r2 hunk 3, for hand applies.** Its 6-line old side (`    }`, `  }`, a blank, `  return true;`, `}`, a blank; the hunk adds the split check at the IssueDraw tail) occurs 3 times in S4a cp.cpp: :3082 (the IssueDraw tail, the right place), :4318 (the end of EndSubmission) and :5569 (the end of UpdateBindings); after P2c, :3092, :4328 and :5579. Each applier takes the match nearest the header line (`@@ -3082,6 +3104,12 @@`), and the decoys are 1,236 and 2,487 lines away, so git apply, GNU patch and my applier all land it at the IssueDraw tail. In the final file the new block occurs once (:3114) and the other two copies are unchanged (:4364, :5662). This is benign, but a hand apply must go by line number, not by text search.

**#26 OFF.** No step touches `rexlego/legodimensions_config.toml`; it stays 7F775847DB9CC2DA (18,145 B, CRLF; git = live = snap1, and unchanged in the subagent's tree after the chain). With no toml line `db16cycPause` stays false: the new tool emits nothing new, and the regen is skipped (§36).

**Scope check.** No S4b step changes the devoff hook set. The SDK steps have no hooks, and C1's rexlego file, memory_watch.cpp, is compiled only inside `if(LEGODIMENSIONS_NATIVE_GPU)` (live CMakeLists :61, appended at :104) and has no hook lines. So the folded devoff map gains only S4c's 4.

**Verdict: PASS. The fold is SAFE to build (landing OFF).**

- The folded chain on S4a gives exactly the 16 rated after-files, in either P2c/r1r2 order. Every step stays at its default (#26 with no toml line; S4c with the env vars unset and #30 OFF), so the OFF ratings of §24, §30, §31, §33, §35, §36 and §37 carry over. The fold adds nothing new: only cp.cpp is touched by two steps, and their hunks are 16+ lines apart.
- Gates for Agent 2's S4b build:
  1. Land exactly these 16 files (13 SDK, memory_watch.cpp, CMakeLists.txt, the new TU), checked by hash, not by an apply's exit code. memory_watch.cpp must hash 70829846C4F321A9 (CRLF; copy the staged after-file if an apply gives anything else; plain GNU patch gives 18DE0334… with exit 0). The TU may be 01D9F8F3… (LF) or 34D281E0… (CRLF); the record says which. The toml must still be 7F775847… (no #26 line).
  2. A full SDK rebuild (cp.h, dcl.h, xmemory.h and shared_memory.h change class layouts) and a rebuilt codegen tool (#26). With no toml line the regen is skipped; a forced one must write identical files (§36).
  3. The folded map gate: the S4b devoff map = devoff4's 27 hooked aliases + exactly sub_83FBF7D0, sub_83FAF180, sub_83FB09E8 and sub_83FC0C10 = 31 (29 would mean the GETDATA define is missing). Check by name and object: each new `sub_` in `gpu_wait_backoff.cpp.obj`, each `__imp__` in the same recomp object as in devoff4. Not by address or TU number (§37). skip_lr stays off.
  4. Native: memory_watch.cpp and the CMakeLists change both alter the native fingerprint (`native_gpu_build_info.h` is rewritten; device.cpp, shader_archive.cpp and pipeline_library.cpp recompile). With S4c folded in, that is **one** native re-pin, on the S4b native build. #26 OFF adds no fingerprint change.
  5. Agent 2's verify: snap1 = S4a + exactly these 16 files (0 problems elsewhere), and the W5 bins (devoff3-bin, devoff4-bin) re-hash unchanged.
- ON tests stay as rated: C1 v3 (§35; both cvars set at launch, with fix (i) ON, gate B), M1 (§33; the microbench first), r1r2 (§31), #26 (a separate toml + regen build, §36), #24 (§26 items 4-6), each measured apart. With decision 1, C1's verify-mode level load can run in the S4b queue.
- No UNSAFE.

**Read.** `s4b-compose-check.py` and the report, in full; my chain output (`t34_compose_out.txt`), the cmp of Agent 2's three scratch trees, a hash scan of the report, and the hunk-3 occurrence scan (`t9_amb.py`); live `rexlego/CMakeLists.txt` :60-112. No builds, no runs, no git writes.

**Sent** ~19:45 to 2, 1.

## §39 Agent 2's S4b apply and build reports, against the §38 gates (20:33-20:58; task #9 item 3)

**Why.** Optional follow-up to §38. Agent 2 applied the folded chain to snap1 at 19:50 and started the S4b OFF build at 19:51. This checks its reports against the five gates at the end of §38. Agent 2 is not waiting for it.

**Inputs** (all under `build/agent2/` unless named; read only):

- `s4b/HASHES.txt` B9A450C3269DB6F9 (5,665 B, 19:50:21; = `s4b/work-195014/HASHES.txt`), 16 rows.
- `prep-s4b-dryrun-1949.txt` F83C711157260634 (38,130 B, 19:49:39) and `prep-s4b-apply-1950.txt` DCB84EDCE9214E9A (38,282 B, 19:50:22).
- `S4b-notes.txt` A73CBBF5DB2D5C9C, `snap4b-verify-off.txt` B293042471DAA5BB, `snap1/STATE-S4a-1325.tsv` 87DB470A7D8BF317 and `snap1/STATE-S4b-1950.tsv` A739468D5FF55C40.
- `snap4b-steps.txt`, `snap4b-run.txt`, `snap4b-sdk-build.log` E195BB4080A79629 (272,974 B), `snap4b-sdk-install.log` 2F29476911CDDFB7 (174,507 B), `snap1-sdk/.ninja_log`, `snap4b-game-configure.log`, `snap4b-game-gen-check.log` C5947E8D28AC4F77 and `snap4b-gate.log` 1ECFA68F7C686854.
- `s4b/checks/tree-check-2007.txt` B83267F6A7DB7490 (it supersedes `tree-check-2005.txt`) and `s4b/checks/w5-rehash-2035.txt` 3AAD2DD319F3284F.
- `s4b/mapcheck-s4c.py` F8CB7B495F74D978 (8,209 B, 20:33:56) with its self-tests `s4b/checks/mapcheck-selftest-same.txt` B84947BB641206DD and `mapcheck-selftest-neg.txt` C6B50064FB44FB9E, and Agent 9's `build/agent9/s4/fence-wait/s4c/expected-map.txt` 3F05E3125DD7311F (4,467 B, 31 distinct `sub_` names).

**Gate 1, land exactly the 16 files, checked by hash: PASS.**

- HASHES.txt: each of the 16 befores = §38's S4a column and each after = §38's finals. memory_watch.cpp is 70829846C4F321A9 (CRLF, copied from the staged after-file), the TU is 01D9F8F3464C8614 (LF: 0 CR, 395 LF) and cp.cpp is 027204B53A271D69. In the chain, cp.cpp's r1r2 before is 474C1CBAE6359D9E = P2c's `new/` (§30).
- The dry run (19:49:35) has 91 checks PASS and 0 FAIL. The apply has 94 PASS, 0 FAIL, 16 files patched and RESULT PASS; its L85 says the 13 SDK results = the compose check's `o1-v3`. Both reports now check the toml (L110/L112: no `db16cyc_pause` line).
- My own hash of the 16 files at `snap1/DimensionsRecomp/<rel>`: 16/16 = §38's finals. `legodimensions_config.toml` is 7F775847DB9CC2DA (18,145 B) in snap1 and in live, with no db16 line. Live is untouched: its 16 files = the S4a befores and the TU is absent.

**Gate 2, a full SDK rebuild: PASS.**

- `cmake --build snap1-sdk --config Release -j 8 -- -k 0` ran 19:51:03-20:12:07, exit 0, steps [1/223] to [223/223] (the last links rexglue.exe). The install ran 20:12:07-20:13:42, exit 0, and copied exactly 10 files (rexglue.exe, rexgpu-xenos.dll/.lib, rexruntime.dll/.lib and 5 headers); 1,239 were up to date.
- `.ninja_log`: 225 of 821 outputs were rebuilt. They include all 8 changed .cpp objects (primitive_processor, graphics shared_memory, d3d12 shared_memory, d3d12 command_processor, d3d12 deferred_command_list, system xmemory, codegen config, codegen builders/system), rexgpu-xenos.dll, rexruntime.dll and rexglue.exe; by directory, src/graphics 37 (all but the third-party DXBCChecksum) and src/system 95. The 596 not rebuilt are third-party (sdl3 271, libavutil 81, libavcodec 80, libusb, spdlog, fmt, imgui and others), codegen templates and 72 rex TUs. None of those 72 includes rex/memory.h, rex/string.h (string.h:20 includes memory.h, and memory.h:27 includes xmemory.h), xmemory.h, either shared_memory.h, cp.h, dcl.h or codegen/config.h. So ninja rebuilt every dependant, which is the full rebuild §38 asked for.
- snap-gate (20:26): the installed rex headers are 340 hash-equal to the snapshot, plus the configure-generated version.h; rexglue_DIR is `snap1-sdk/install`; PASS.
- The OFF configure pins `REXGLUE_HOST_CODEGEN_EXECUTABLE` to `codegen-frozen/codegen-frozen.exe`, and gen-check (20:13:50-20:25:59) found 886/886 generated files identical to `baseline/`. The rebuilt codegen tool (#26) is not used by this build, which is right with no toml line. §36's "a forced regen writes identical files" belongs to the CG26 variant.

**Gate 3, the folded map (31, by name and object): PASS.**

- My own check: scratch `t9_map.py`, with its own map parser (it does not import Agent 9's `mapcmp.py`, so it is independent of Agent 2's checker). It compares `devoff4b-bin/legodimensions.map` 52155274A978A946 (39,181,442 B) with `devoff4-bin/legodimensions.map` DCC51E2B7A0040E2. A name counts as hooked when its `__imp__sub_` public is not at the address of its `sub_` public in the same map. No address is compared across maps.
- Both maps have the same 164,786 `sub_` names and the same 164,786 `__imp__sub_` names. Hooked: devoff4 27; devoff4b 31 = the 27 + exactly sub_83FBF7D0, sub_83FAF180, sub_83FB09E8 and sub_83FC0C10 = the 31 names in expected-map.txt. None of the 4 is hooked in devoff4.
- Each target's `sub_` is in gpu_wait_backoff.cpp.obj. Its `__imp__` is in the recomp object that held both its `sub_` and its `__imp__` in devoff4: sub_83FAF180 in legodimensions_recomp.107, sub_83FC0C10 in .232, sub_83FBF7D0 in .248 and sub_83FB09E8 in .422.
- The 27 old hooks keep both of their objects. No other `sub_` or `__imp__` changed object, and each of the 164,755 unhooked names has its `sub_` and `__imp__` in one object.
- gpu_wait_backoff.cpp.obj defines exactly the 4 `sub_` publics. It has 24 publics in all: the 4 hooks, 4 spdlog/fmt template functions, 13 string literals and 3 constants. The hook objects are devoff4's 9 plus gpu_wait_backoff.cpp.obj.
- The map belongs to the staged exe: the map timestamp 6b03a981 (20:48:33) = the PE TimeDateStamp of `devoff4b-bin/legodimensions.exe`. The same holds for devoff4 (6b0342cb).
- devoff4b-bin (staged 20:49:04-07): my own sha256 of each of its 7 files appears in its MANIFEST.txt DE11A914079D7DF7 (30,450 B).
  - As planned, the exe (DFBE1D43B28861A6), the map, rexgpu-xenos.dll (E3CB99CFDEA95E66) and rexruntime.dll (A33801D1538D6175) differ from devoff4-bin.
  - FiraSans-Regular.ttf, achievement_unlocked.wav and TracyClient.dll are byte-equal to devoff4-bin's.
  - Agent 2's stage log (`snap4b-run.txt` 20:49:05-08) records 16 S4b MANIFEST patch rows; 102 PASS / 0 FAIL / 61 NOTE; and the 12 new-string checks PASS.
- Agent 2's `s4b/checks/mapcheck-devoff4b.txt` (4,185 B, 20:50:58, mode s4c) agrees.
  - RESULT PASS with 31 hooked, and the same 4 recomp objects.
  - The per-object `sub_` sets = devoff4's with the 4 targets moved (448 objects), and the per-object `__imp__` sets are equal (438 objects).
  - Its 353,058 publics = my 353,009 plus the 49 repeated names my parser folds.
  - Its checker (read in full) tests the same things, by name and object. Its self-tests show it passes the same map (27 hooked) and can fail (the negative test gives FAIL (8)).

**Gate 4, one native re-pin: pending.** The S4b native build began at 20:53:12. `snap4b-run.txt` shows verify S4b with 0 problems and the native gen-check 886/886 PASS at 20:53:29, then the build from 20:53:30 (-j 8, Below Normal, into native4b-bin). It had not finished by 20:58. As §38 says, this is one re-pin: memory_watch.cpp and the CMakeLists change both alter the native fingerprint, and #26 OFF adds nothing. Two things still to check: the new fingerprint is pinned once, on native4b-bin; and the native map passes `mapcheck-s4c.py --mode same` against native4-bin (the #24 hooks are in OFF builds only).

**Gate 5, Agent 2's verify and the W5 bins: PASS.**

- `snap4b-verify-off.txt`: 23,844 files, 15 backups checked, 0 extra, 0 problems, RESULT PASS.
- tree-check-2007 (2005's check 0 had a UTF-16 decode bug): CHECK 1 16/16; CHECK 3, STATE-S4b's 23,844 rows = STATE-S4a's 23,843 + the TU, with exactly 16 differences (15 changed, 1 new) and 0 others; CHECK 5, the 15 backups = the befores; CHECK 0, the records are unchanged since the apply.
- w5-rehash-2035 (list `W5-INPUTS-1731.txt` A4D9C6AED9476D21): 27/27 rows unchanged, including devoff3-bin (MANIFEST B9C5175DA1904235) and devoff4-bin (MANIFEST 16DCC9399239E577), 7 files + MANIFEST each.

**FYI for the CTR and CG26 variants** (Agent 2's next items; nothing to change for S4b). `REX_D3D12_DEFERRED_COUNTERS` appears only in deferred_command_list.cpp (L21-681), not in cp.h, dcl.h or cp.cpp, so the CTR variant changes no class layout and the one-TU `recompile.py` + `relink.py` route is enough. For CG26: recompile every TU whose generated .cpp changed (expect §36's 10 TUs and 20 sites), check that no generated header changed, and keep `codegen.partition.json`.

**Verdict.** PASS on gates 1, 2, 3 and 5. Gate 4 stays open until the S4b native build is re-pinned. devoff4b-bin is exactly the §38 fold: the 16 files by hash, a dependency-complete SDK rebuild, the pinned S1 generated code, and the 31-name hook map by name and object (two independent checkers agree). Nothing is UNSAFE and Agent 2 has nothing to fix.

**Read.** In full: HASHES.txt, S4b-notes.txt, snap4b-run.txt, snap4b-steps.txt, snap4b-verify-off.txt, snap4b-gate.log, snap4b-game-configure.log, snap4b-game-gen-check.log, snap4b-native-gen-check.log, w5-rehash-2035.txt, mapcheck-s4c.py and mapcheck-devoff4b.txt. In part: the dry-run, apply and tree-check-2007 reports (heads, tails and the check lines), the SDK build and install log tails, and the headers of relink.py and recompile.py and both self-tests. Analysed: `snap1-sdk/.ninja_log` (rebuilt outputs by directory) and an include grep of the 72 rex TUs it did not rebuild. My own hashes: the 16 snap1 files, the 16 live files, the toml, the TU's line endings and devoff4b-bin's 7 files, plus my own parse of both maps (`t9_map.py`). No builds, no runs, no git.

**Sent.** No separate message (nothing to fix); in @@done 9 (~20:58).

## §40 Agent 5's overnight launcher, safety read (20:06-22:33; task #9 item 2)

**Why.** This is item 2 of Agent 1's task #9: a safety read of Agent 5's launcher in `bench/agent5/launch/` before the user starts it at ~23:45. The launcher may only:

- P1: run the pinned runner `bench/agent8/run/run-matrix.ps1`, on `bench/agent8/run` JSONs, with bins from `build/agent2`;
- P2: close only the 5 approved apps (ChatGPT, Copilot, Roblox, Task Manager, Wallpaper Engine; not Roblox Studio);
- P3: restore the screensaver;
- P4: refuse when the PC is locked, on battery or past the deadline;
- P5: write only to its own folders plus the GO/HOLD files.

Agent 1 added two more checks: the relaxed Defender gate (19:31), and fix 2 checked against Agent 1's hold manager. Agent 11 reviews the launcher too (its task #10). Agent 1's rulings:

- 21:02: must-fix are my items 5-7 and Agent 11's F1 (env names) and F3 (06:45 latest start); should-fix are item 8 and the try note.
- 21:29: must-fix are Stop-Tree without `/T` and the driver allowlist restored; should-fix is a build check in the last checks. "Copilot" on this PC is the Microsoft 365 Copilot app (Microsoft.MicrosoftOfficeHub, the only Copilot installed). The hard stop is 07:30, not 07:45.

**Versions read** (`run-night.ps1` unless named):

- 00BFECD7… (20:28): my pre-read and subagent B's full second read (20:51).
- 924321AE3A2C6686 (57,811 B, 788 lines, 20:50): my full read. Fixes 1-4 were checked on this version.
- 163D76596E575D8D (63,759 B, 846 lines, 21:01): delta read. Items 5-7 and the try note were checked on this version.
- 3EFC5312D0982E77 (72,276 B, 948 lines, 21:15): delta read, plus Close-Programs, Start-Window(Locked), Invoke-Runner, Stop-Tree, Invoke-Go and main in full. F1, F3 and item 8 were checked on this version, and my interim note (~21:24) is on it.
- B0902106C4D93581 (77,221 B, 1,010 lines, 21:42): delta read by me and by subagent B (21:50). Changes from 3EFC5312: Stop-Tree rewritten without taskkill (Get-Descendants, Stop-One), the 3-name driver list back, the build check in the last checks, `$GraceMinutes = 0` (hard stop 07:30), a launcher error or Ctrl+C while the runner runs stops it, the dry-run hook `-TestFailAfter`, and Log writes its files before the console.
- 16B90FA8654FAC08 (77,594 B, 1017 lines, 22:11:21): the final version. Delta read by me and by subagent B (22:18). One hunk, in Stop-One's catch (L805): when a kill is refused, it waits up to 3 s and logs `(ended on its own)` if the process is gone by then, else `(NOT killed: …)` as before. Agent 5 made it after t-run-deadline failed on B0902106 only on its `NOT killed` check: a conhost.exe whose program had just been killed refused the kill with `Access is denied` while it was already ending (t-run-deadline.console.txt L284). The change only alters the log text and adds at most 3 s per refused process; what gets killed is unchanged.
- `README.md` 39ECF5C21234B500 (252 lines; read in full), 581A03DB66D34A27 (263 lines, 21:28; delta), DE33302A86B8B6BF (270 lines, 22:04; delta) and 0058C8F61EEAA9F2 (23,844 B, 271 lines, 22:12:38) (final; delta: one added line, L182, on the walk's `(already gone)`, `(ended on its own)` and `(NOT killed: …)` notes). The final README gives 07:30 as the hard stop (L47, L177) and describes the walk instead of taskkill (L179; its only "taskkill" is "There is no `taskkill`"). It also has the 3-name driver list (L121), the build check in the last checks (L158), `-GraceMinutes` default 0 and `-TestFailAfter` among the dry-run hooks (L258), and the Ctrl+C exit code (L245). No 07:45 is left.
- `RUN-NIGHT.cmd` D7A0362BE90C12B4 (1,197 B, 19 lines; content unchanged since 21:51:46, mtime 22:32:59 from the pin group's restore), CRLF 19/19, read in full. The only change since F7190AB2… (1,012 B, 20:51) is one more echo line, for an exit code other than 0, 2 or 3 (e.g. Ctrl+C). It still clears REX_TIMER_WAIT_BLOCKING and LEGO_GPU_WAIT_STATS, starts the launcher by its full path with no arguments, and ends with `pause` and `endlocal & exit /b %RC%`. After a Ctrl+C, cmd.exe asks `Terminate batch job (Y/N)?` before these echo lines. README L77 says either answer is fine, and both are safe because the launcher's finally has already run.

Line numbers below are for the final version.

**P1, only the pinned runner, JSONs and bins: PASS.**

- The command is fixed. Get-RunnerArgs (L302) builds `powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File bench\agent8\run\run-matrix.ps1 -Matrix <json> -Only <arms> -Repeats <n> -ColdShared -NoPrompt`. `$RunMatrix` is set once (L36), and nothing in a GO or a matrix changes it. Since 3EFC5312 the runner runs as its own process (Invoke-Runner, P4).
- Pins. At start, Get-PinFiles (L184) hashes the launcher, RUN-NIGHT.cmd, run-matrix/run-timing/common/timing-env/winhelper.cs, every .py/.cs in bench/agent8/run, everything under `drivers\`, `harness\legodimensions.toml` and `harness\nvml.cs`. Invoke-Go compares them before anything runs (L899), so `-PlanOnly` only ever runs the pinned runner. Start-WindowLocked compares them again just before the start (L687), and once more after the run.
- The GO. Parse-Go (L225) accepts one line of 6 tokens: a plain `*.json` name (no folder, no `..`), a 64-hex sha256, `only=` and `repeats=1-20`. Test-Matrix (L253) requires that:
  - the file sits directly in bench/agent8/run and its sha256 = the GO's;
  - every arm, not only the `only=` ones, has a bin of the form `^build/agent2/<name>-bin/?$` with MANIFEST.txt and legodimensions.exe;
  - env keys are only the 11 in `build/agent8/w8w9/ENV-KEYS-F1.txt` (D1AE6D574C443EDE; Agent 8, approved by Agent 1 at 21:14), exact case. `$AllowedEnv` (L41) has the same 11 keys in the same order as the file's list (its L5-15);
  - no arm uses menu, profile, triggers, toml edits or seed_cache.
- The 11 keys are removed from the launcher's own environment at start (L976) and again just before the runner starts (L709), so an arm gets them only from its matrix. Env values are not checked. Of the 11 keys, only LEGO_NATIVE_FRAME_METRICS takes a path; the JSONs give `<run>\native-frames.csv`, and run-timing.ps1 maps `<run>` to the run dir (Expand-Run, :153).
- run-matrix.ps1 rejects unknown arm keys (`$ArmKeys` L52). `args` exists only inside a driver object (L153-154, L247). `cvars` go to the game as `-Cvar` (L472), so they can't name a bin, an env var or a toml.
- **The driver hole.** Up to 924321AE, only the driver's file was checked, never its args.
  - Both runner scripts use a plain `param()` with no CmdletBinding. The `-GamePid`/`-RunDir` that run-timing.ps1 adds fall into `$args`, and every other arg binds normally.
  - My scratch test `t9_param.ps1 -GamePid 123 -RunDir C:\r -BinDir C:\any -Env A=1` printed `BinDir=C:\any; Env=A=1`.
  - So `{"script":"run-matrix.ps1","args":["-Matrix","<any>",…]}`, or run-timing.ps1 with `-BinDir`/`-Env`/`-Toml`, would have run a bin, env or toml that was never checked.
  - 163D7659 accepted only a plain string `drivers/<name>.ps1` (case-sensitive) for thread-cpu.ps1, io-counters.ps1 or pso-stats-at-end.ps1, resolving to `bench\agent8\run\drivers\<name>` and pinned. Driver objects and args are refused.
  - 3EFC5312 dropped the 3-name list: any pinned `drivers/*.ps1` passed. That newly let in sys-csv.ps1, which run-timing starts by itself (a second copy fights over sys.csv), and any .ps1 put in `drivers\` before the start. Agent 1 made restoring the list a must-fix (21:29). The final version has it again: `$AllowedDrivers` (L45) = thread-cpu.ps1, pso-stats-at-end.ps1 and io-counters.ps1, checked case-sensitively (`-ccontains`, L292) together with the resolution and pin checks. Fixed.
  - The 18 JSONs in bench/agent8/run use only these plain strings (thread-cpu ×25, pso-stats-at-end ×7, io-counters ×2), so none of them is refused.
  - The runner resolves the path the same way as the launcher. run-matrix.ps1 Find-Script tries the matrix folder, then its own folder, then the repo; the launcher's Resolve-Driver (L247) uses the same order. In REAL mode the matrix folder is bench/agent8/run.
  - The 3 drivers start nothing (no Start-Process, iex or exe calls). They write to the run dir, `build/agent8/cache` (thread-cpu L72) and the game's PSO trigger file (pso-stats-at-end L59-81). With no args, io-counters' `-Out` stays in the run dir.
- Unknown arguments are refused with exit 2 (L32), so a mistyped `-DryRun` can't start REAL mode. The test hooks, including `-FakeRunner`, `-StartBy` and `-GraceMinutes` since 3EFC5312, are refused without `-DryRun` (L65). `-FakeRunner` is used only inside the dry-run branch (L721).

**P2, only the approved apps: PASS (after fix 9).**

- The name list is at L54 and the path rules at L60:
  - ChatGPT;
  - Copilot / Microsoft.Copilot only from `\WindowsApps\Microsoft.Copilot_` or `\WindowsApps\Microsoft.Windows.Ai.Copilot_`, and copilotapphost / copilotapp_proxy only from `\WindowsApps\Microsoft.MicrosoftOfficeHub_`. Agent 1 (21:29): on this PC "Copilot" is the Microsoft 365 Copilot app, so these are in the approved set;
  - Roblox, RobloxPlayerBeta and RobloxPlayerLauncher (the player), and Windows10Universal only from `\WindowsApps\ROBLOXCORPORATION.ROBLOX_` (the Store player; any Store app can run as Windows10Universal.exe). Roblox Studio (RobloxStudioBeta) is not on the list;
  - Taskmgr;
  - wallpaper32/64 and webwallpaper32/64, plus ui32/ui64 only from a wallpaper_engine folder.
- A path-checked name whose path can't be read (MainModule, then CIM ExecutablePath) is left alone and logged. Only processes in the launcher's own session are closed.
- Close-Programs (L490) sends CloseMainWindow, waits 10 s, then kills. Each program has its own try/catch (fix 1), and HasExited is checked. It runs when a GO is accepted and again just before the last checks.
- Task Manager usually runs elevated, so it may refuse to close. That is logged and not fatal (README L55).
- Nothing is closed in a dry run.
- **The kill path, Stop-Tree (L814).** It runs only on a STOP file, at the hard stop, or when the launcher fails while the runner runs. In 3EFC5312 it ran `taskkill /PID <runner> /T /F`. `/T` follows ParentProcessId links and never checks creation times, so it would also kill a process older than the runner whose dead parent once had the runner's PID, with its whole subtree. Examples are explorer.exe (its parent, userinit, exits at logon) and apps whose launcher has since exited. That breaks P2, and Agent 1 made it a must-fix (21:29). The final version has no taskkill; the only hit is a comment (L771). It works like this:
  - Stop-Tree reads the runner's start time, cut to 1 µs (CIM's precision), then kills the runner through its handle (L818).
  - Then, up to 3 times, Get-Descendants (L773) takes one Win32_Process snapshot and follows ParentProcessId down from the runner. It follows a process only if it was created at or after its parent (L788), so a process older than the runner, or older than its supposed parent in the tree, is never reached. The launcher's open handle keeps the runner's PID from being reused (L848).
  - Stop-One (L795) kills a process only if its PID still has the snapshot's start time (within 2 ms), so a PID reused between the snapshot and the kill is left alone. If the kill is refused, or the start time can't be read, it kills nothing else: it waits up to 3 s and logs `(ended on its own)` if the process is gone, else `(NOT killed: …)`.
  - If the start time or the snapshot can't be read, only the runner is killed, and the log says so in red.
  - Fixed.
- In REAL mode Stop-Tree also kills a legodimensions.exe, but only if it is in this session, started at or after the window's start and runs from under `build\agent2\` (L832). A dry run never touches legodimensions.

**P3, the screensaver is restored: PASS.**

- Save-Screensaver (L445) saves ScreenSaveActive and SCRNSAVE.EXE. An earlier save with no `restored` line is not overwritten; it is kept as `screensaver-saved-unrestored-<ts>.txt` and logged in yellow.
- Set-ScreensaverNone (L461) clears the active flag through SPI_SETSCREENSAVEACTIVE and removes SCRNSAVE.EXE.
- Restore-Screensaver (L469) puts both back and appends `restored`. If that fails, it logs where the saved values are.
- In the main finally (L1008-1012), each step runs in its own Try-Step: the screensaver first, then the HOLD, keep-awake and the state.
- Ctrl+C runs the finally. The X button or a restart doesn't, and README L78-84 tells the user what to do then. Keep-awake ends with the process anyway.

**P4, refuses when locked, on battery or past the deadline: PASS.**

- At start (main, L956), any of these refuses with exit 2: not on WinSta0\Default, LogonUI running, not on AC, a STOP file, a second launcher (mutex), a missing pinned file, or an end more than 14 h away (L965; item 6). The 14 h rule refuses a start after 07:30, and also one before 17:30, which doesn't matter at ~23:45. Agent 5's tests t-startref and t-mutex PASS.
- Get-Power (L160) uses GetSystemPowerStatus. It counts as AC only when ACLineStatus = 1 or BatteryFlag = 128; a failed call or an unknown state counts as not on AC (fix 3, fails closed).
- The deadline is 07:30 (Get-Deadline L611):
  - at GO, the runner estimate + 10 min must end by 07:30 (L906);
  - the gate checks the same on every pass (L651).
- F3, the latest window start, is 06:45 (`$LatestStartTime` L47, Get-LatestStart L616):
  - a GO read at or after 06:45 is refused (L907);
  - the gate gives up at 06:45 (L652);
  - the last checks refuse at or after it (L691);
  - a launcher started after 06:45 logs that every GO will be refused.
  - This is stricter than Agent 11's F3, which is fine.
- In the gate (Test-Gate L403), LogonUI or a lost AC in any of the 3 samples fails it.
- Last checks (Start-WindowLocked L685; item 7): after Close-Programs, the desktop, LogonUI and AC are checked again, together with the pins, the matrix rules and sha256, the bin hashes logged at GO, the deadline, the latest start and the HOLD. The final version also checks build and game processes there (L703; Agent 1's should-fix). In REAL mode it uses the real process list (`Use-Real` is true without a fixture) and the gate's `$BuildInc` names, legodimensions included.
- **Item 8, the runner is watched** (Invoke-Runner L845).
  - The runner runs as its own process (Start-Process -NoNewWindow -PassThru). Its output goes to `status\runner-<tag>.out.txt` / `.err.txt`, and is copied to the console and `runner-<tag>.txt` as it comes.
  - Every second, a STOP file or the hard stop ends the window at once through Stop-Tree.
  - A launcher error (the catch, L870) or Ctrl+C (the finally, L874) while the runner runs also goes through Stop-Tree. A normal end doesn't.
  - The hard stop was the end time + 15 min (07:45) in 3EFC5312; Agent 1 set it to 07:30 (21:29). The final version has `$GraceMinutes = 0` (L24), and `-GraceMinutes` is a dry-run-only hook, so in REAL mode the hard stop is the end time, 07:30.

**P5, writes only its own folders plus GO/HOLD: PASS.**

- Its files go to `bench/agent5/launch/status/`: log, state, gate, last-go, last-result, pins, screensaver-saved*, relaxed-gate, window-*.log, runner-*.txt and, since 3EFC5312, runner-*.out.txt/.err.txt. A dry run writes only to `status-dryrun/<tag>/`.
- perf-notes: the GO is deleted once read, and a GO that can't be deleted is refused. The HOLD is covered below. The STOP file is read and deleted; it is the launcher's own stop switch (README L63, L220).
- System state: the HKCU `Control Panel\Desktop` screensaver values (P3), the keep-awake request and Quick Edit in its own console.
- run-matrix.ps1 `-PlanOnly` writes nothing; there is no write call before its exit at L434-436.
- In REAL mode the matrix JSON is held open read-only with read sharing for the whole run (Start-Window L682). My scratch test `t9_lock.ps1`: with that handle open, ReadAllText (run-matrix.ps1:113), Copy-Item (:452), Get-FileHash, Get-Content and a child process all read the file, while a write or delete fails. So the lock can't break the runner, and nobody can change the JSON mid-run.
- The runner writes its results to `build/agent8/matrix/<date-time>/` (Agent 8's folder).

**Relaxed Defender gate: PASS.**

- Sampling, in Get-Sample (L380) and Get-Cores (L360): one sample per 60 s, from CIM Win32_Process kernel+user time per pid.
  - An unreadable process is a read error, and the gate fails.
  - A process that started inside the interval counts in full.
  - A process that was already running but is missing from the previous query gives no figure.
- Test-Gate (L403): the last 3 samples must all have a CPU figure and all be clean: no build or game process, RAM ≥ 6 GB, C: ≥ 6 GB free, no LogonUI, on AC, no read error, and the HOLD is its own.
- Strict: MsMpEng, OfficeClickToRun and CrossDeviceService are each < 0.1 core in all 3.
- Relaxed applies to MsMpEng only, and only from 30 min after GO acceptance: all 3 readable, each ≤ 1.2 cores, and max − min ≤ 0.2. OfficeClickToRun and CrossDeviceService stay strict, and nothing else relaxes.
- It gives up 120 min after the GO.
- The hooks that would change these values (`-StrictMinutes`, `-GiveUpMinutes`, `-SampleSeconds`, `-GateFixture`) are refused without `-DryRun`.
- Agent 5's gate tests: `summary-gate.txt` (20:39, on 00BFECD7) PASS 11/11, including relaxed, unstable, toohigh, lowres and real. Since then, all in `build/agent5/launch-test/results/`: on B0902106 (22:01-22:10) go 16/16, gate 13/13 (adding build, build-giveup, build-start, close, stop-start, stop-wait, stop-gate and json), hold 4/4 and run 4/5, where t-run-deadline failed only on its `NOT killed` check (see the final version above); on the final 16B90FA8 (22:12-22:24) hold 4/4 (22:14), go 16/16 (22:18), run 5/5 (22:22) and gate 12/13 (22:24). t-relaxed failed only on its exact-value checks. With 3 test groups running at once, the GO took 49 s to accept, and the first 3 CPU samples came at +0.4 min, after the test's 0.25-min strict phase. So the gate relaxed at once on the fixture's earlier values (MsMpEng 1.05/0.98/1.10: each ≤ 1.2 cores, spread 0.12), instead of refusing in the strict phase and then taking the expected 1.02/1.02/1.02. That is the rule working (L432). The same test passed on B0902106 (22:09), and the delta doesn't touch the gate. Agent 5 then re-ran t-relaxed alone on 16B90FA8 (22:26-22:28, `summary-gate-relaxed-rerun.txt`, with a 1-min strict phase): PASS. The gate collected 1.05/0.98/1.10, refused in the strict phase ("MsMpEng not < 0.1 core") until +1 min, and then passed relaxed on the expected 1.02/1.02/1.02.

**Fix 2 against the hold manager: consistent.**

- The launcher's side:
  - Set-Hold (L541) creates the HOLD with CreateNew, never over an existing file. It reads its token back and throws if it can't write.
  - Sync-Hold (L565) runs at GO, at every gate sample and just before the start. Its own HOLD → ok. No HOLD → it writes it again and logs that. A foreign HOLD → the gate fails with `foreign HOLD`.
  - Clear-Hold (L577) deletes only a HOLD that has its token. It retries 5 times and stops as soon as the HOLD is no longer its own.
- `build/agent1/hold/hold-manager.ps1` (D060F913…) polls every 5 s until 07:30. When inactive and a new `build/agent8/matrix` folder appears, it overwrites the HOLD (no token) and becomes active on that folder. When active, it deletes the HOLD on summary.md, or when stale (no legodimensions process and no writes in the folder for 6 min).
- Together:
  - Until the runner makes its folder, the HOLD is the launcher's. Then the manager takes it over, and the launcher doesn't look at the HOLD during the run.
  - At the end, the launcher leaves a taken-over HOLD alone.
  - Windows can't overlap, because the launcher waits as long as any foreign HOLD exists. The cost is liveness only: a stale foreign HOLD holds the window back until the 120-min give-up.
- Residual risk (no action): suppose a third party deleted the manager's HOLD while the manager was still active on an older folder. The manager's stale delete could then remove the launcher's HOLD before the start. Sync-Hold writes it again at the next sample. If it happens after the start, the manager re-takes the HOLD on the new folder within 5 s.

**Fixes from my pre-read (20:34), addendum (20:55) and interim note (~21:24), with Agent 11's F1/F3.** Status in the final version:

| # | Fix | Status |
|---|---|---|
| 1 | WaitForExit inside try | done (924321AE) |
| 2 | don't overwrite a foreign HOLD | done (924321AE) |
| 3 | Get-Power fails closed | done (924321AE) |
| 4 | RUN-NIGHT.cmd CRLF + a STOP smoke test | CRLF done; `endlocal & exit /b %RC%` passes the exit code on. No test runs the cmd itself (the pin tests only append a line and restore it); t-run-stop covers the STOP path through run-night.ps1, and the cmd is read in full |
| 5 | driver: plain allowed string, no args | done (163D7659); the list was dropped in 3EFC5312 and is back in the final version |
| 6 | refuse a start more than 14 h before the deadline | done (163D7659) |
| 7 | desktop/LogonUI/AC again after closing apps | done (163D7659) |
| 8 | runner with STOP/deadline polling | done (3EFC5312). Agent 5's run tests on 16B90FA8 (22:22; dry run with `-FakeRunner`, a fake runner that starts one sleeping child): normal end, STOP, the end time (a test grace), a launcher error (`-TestFailAfter 25`) and Ctrl+C all PASS. In each of the 4 kill cases walk 1 killed the child powershell.exe, its conhost.exe was `(already gone)` or `(ended on its own)`, `runner stopped: yes`, and both PIDs were gone |
| F1 | Agent 11: the env names (the 11 keys) | done (3EFC5312) |
| F3 | Agent 11: no window start after 06:45 | done (3EFC5312) |
| 9 | Stop-Tree without `/T` (Agent 1: must) | done (final): Get-Descendants + Stop-One, no taskkill |
| 10 | build check in the last checks (Agent 1: should) | done (final) |
| 11 | hard stop 07:30 (Agent 1) | done (final): `$GraceMinutes = 0` |

Notes, all done:

- Try-Step in the finally;
- `-NonInteractive`;
- bin hashes logged at GO, re-checked at the start and after the run;
- stray REX_/LEGO_ variables are logged;
- Roblox Studio is left alone.

Open notes, no action needed tonight:

- (B) Clear-Hold reads the token, then deletes. A HOLD written in between would be deleted, but that needs a writer inside a gap of microseconds, and the hold manager writes only when a new matrix folder appears.
- (B) The runner's own AC check (timing-env.ps1:53-54) fails open. The launcher's checks fail closed, so this is a note for Agent 8.
- (B) Join-Args drops '' values and doesn't double backslashes before a closing quote. No argument it gets has either.
- powercfg is called by bare name (L710), only to log the power scheme.
- Env values are not checked (see P1).
- (B, 21:50) Stop-One (L795) and the legodimensions sweep (L832) open the process by PID once for the start-time check and again for Kill, so a PID reused in those microseconds could be hit. `[void]$g.Handle` right after GetProcessById would make both use one handle.
- (B, 21:50) In Invoke-Runner, L848-854 run after Start-Process and before the try (L855). A Ctrl+C in that sub-millisecond gap would leave the runner unwatched. Opening the try right after Start-Process closes the gap.
- (B, 21:50) The Ctrl+C path had no test. Agent 5 has since added t-run-ctrlc: that launcher runs in its own hidden console, and `build/agent5/launch-test/send-ctrlc.ps1` (A8DDFEE9…, read by me) attaches only to that console, refuses (exit 13) if it is its own console or unknown, ignores Ctrl+C itself and sends CTRL_C_EVENT there. PASS on B0902106 (22:10) and on 16B90FA8 (22:22): `the launcher was interrupted (Ctrl+C?) while the runner was running`, then `killed (walk 1): powershell.exe:26464, conhost.exe:38832 (ended on its own)`, `runner stopped: yes` and `HOLD removed`.
- (B and me, 22:18) README L179 ("It walks up to 3 times, until nothing is left") and L182 ("the next walk then tries it again" after `(NOT killed: …)`) say more than the code does. Each walk starts again from the runner's PID in a new snapshot (L782), so a grandchild whose parent was killed in walk 1 is not reached again. This is harmless: for a process the runner started (same user, not elevated), a refused kill means it is already ending, and in REAL mode the legodimensions sweep (L832) covers the game whatever the tree. Fix the wording, or keep the entries that came back `NOT killed` and retry them with Stop-One (which re-checks PID and start time) in later walks. B adds that the sweep skips a legodimensions whose path can't be read, without a log line (L831).
- The pin tests (t-pin-go, t-pin-gate) append a line to the real RUN-NIGHT.cmd and restore it byte for byte in a finally, with a sha check. The 23:30 freeze should still re-hash RUN-NIGHT.cmd (D7A0362B…).

**Second reader.** Subagent B read 00BFECD7 in full (20:51). Rules 1-6: 1 FAIL (the driver hole), 2 PASS except the WaitForExit, 3 PASS, 4 PARTLY, 5 PASS, 6 PASS (the relaxed gate). It confirmed all 7 of my candidate issues (a, the HOLD overwrite; b, power failing open; c, WaitForExit; d, env; e, no runner timeout; f, the bins were not hashed; g, the LF cmd); a, b, c, f and g were fixed by 924321AE, and d and e by 3EFC5312. B's delta read of 163D7659 and 3EFC5312 (21:18) confirmed items 1-4, 6 and 7, found the dropped driver list, agreed on the `/T` risk, and added the build re-check, the bare powercfg and the open notes above. B's delta read of B0902106 (21:50) found no blockers; all 6 checks were CONFIRMED-OK. There is no taskkill. The walk never follows a process created before its parent, and a clock mismatch fails safe. PID reuse is handled. STOP, the 07:30 end, a launcher error and Ctrl+C all reach Stop-Tree, and a normal end doesn't. The REAL build check sees every session's processes, legodimensions included. Nothing new kills, writes or starts outside P1-P5: the only new writes are status\runner-<tag>.out/.err.txt, and FakeRunner and TestFailAfter are dry-run only. Its 3 optional notes are under Open notes. B's delta read of 16B90FA8 (22:18) found no blockers. (1) The new catch kills nothing: it is reached only after GetProcessById worked, and it only waits. (2) On .NET Framework, Kill() on a process that is already ending throws `Access is denied`, and WaitForExit(3000) returns true only when the process has ended or its PID no longer runs, so `(ended on its own)` is never logged for a running process. (3) The finally disposes the handle after the wait. (5) Stop-One is called only by Stop-Tree, and Stop-Tree only from Invoke-Runner (L863, L876). Its item (4) is the README note under Open notes.

**Verdict.** **SAFE** for run-night.ps1 16B90FA8654FAC08, README.md 0058C8F61EEAA9F2 and RUN-NIGHT.cmd D7A0362BE90C12B4, in REAL mode by double-click at ~23:45. P1-P5 PASS, the relaxed gate PASS, fix 2 is consistent with the hold manager, and fixes 1-11 and F1/F3 are done. That includes Agent 1's must-fixes (no taskkill `/T`, the 3-name driver list), the should-fix build check and the 07:30 hard stop (`$GraceMinutes = 0`; README L47 and L177 say 07:30). Agent 5's tests on the final hash: go 16/16, hold 4/4, run 5/5 and gate 12/13. The one miss, t-relaxed, is a load-timing artifact of the test (see the relaxed gate); it passed on B0902106, the gate code is unchanged, and Agent 5's solo re-run on 16B90FA8 passed (22:28). Nothing has to change before 23:30. Optional: the README retry wording (or the retry in code), one handle in Stop-One and the sweep, the try right after Start-Process, and a log line when the sweep can't read a path. Any later change to these 3 files needs a new delta read before the freeze.

**Later (22:36).** Agent 5: the night set is final and unchanged since the rating. RUN-NIGHT.cmd was re-hashed after the 22:33 pin group (D7A0362BE90C12B4, no change). Smoke test at 22:34: with `perf-notes/WINDOW-STOP.txt` present, `RUN-NIGHT.cmd < nul` refused on the hidden desktop ("WINDOW-STOP.txt exists: delete it first") and exited 2 after 7 s. Agent 5 then removed the STOP file and `status/`, and nothing was left running. The pin group, run alone: 2/2 PASS. Totals on 16B90FA8654FAC08: go 16/16, gate 13/13 (counting the t-relaxed solo re-run), hold 4/4, run 5/5, pin 2/2. Optional items a-d are deferred to after tonight, and the night set won't change.

**Read.**

- In full: run-night.ps1 924321AE (788 lines), README.md 39ECF5C2 (252 lines), RUN-NIGHT.cmd, hold-manager.ps1 and ENV-KEYS-F1.txt.
- Deltas: 00BFECD7 → 924321AE → 163D7659 → 3EFC5312 → B0902106 → 16B90FA8 (final), and README 39ECF5C2 → 581A03DB → DE33302A → 0058C8F6 (final), through my scratch diffs; Stop-One, Stop-Tree and Get-Descendants of the final version again in full.
- In part:
  - run-matrix.ps1: param block, `$ArmKeys`, Find-Script, the driver lines, the `-PlanOnly` exit and the writes before it;
  - run-timing.ps1: param block, Expand-Run, the driver start and its timeout;
  - the 3 drivers: start and write calls;
  - all 18 JSONs: driver fields and the LEGO_NATIVE_FRAME_METRICS values;
  - Agent 5's tests: `summary-gate.txt` (20:39) and `summary-go.txt` (20:54), then `summary-go/-gate/-hold/-run.txt` on B0902106 (22:04-22:10) and on 16B90FA8 (22:14-22:24; the gate one is kept as `summary-gate-full-16B90FA8.txt`) and the solo t-relaxed re-run (`summary-gate-relaxed-rerun.txt`, 22:28); the walk lines of every t-run-* console file (t-run-deadline on B0902106 in full), t-relaxed's gate lines, t-build-start and t-driver; the run group of `run-tests.ps1` (L400-481) and `send-ctrlc.ps1` in full.
- My own tests, scratch only: `t9_param.ps1` (parameter binding) and `t9_lock.ps1` (the matrix lock).
- No launcher or runner runs, no builds, no git.

**Sent.** Pre-read ~20:34 to 5, 1, 11 (fixes 1-4 and notes); addendum ~20:55 to 5, 1, 11 (items 5-8 and notes); interim ~21:24 to 5, 1, 11 (Stop-Tree `/T`, the driver list, the build check, the Copilot question, README and tests); the rating ~22:33 to 5, 1, 11.

## §41 Agent 3's G5: W6 gate A (C1 + verify on devoff4b), with row 7 as extra data (21:59-22:46; task #9, extra)

**Why.** At 21:59 Agent 3 asked for a G5 rating of W6 gate A. The question: does gate A give §21 A for C1 v3 on devoff4b? §21 A (L1068) means verify mode with 0 mismatches over the title, Agent 3's menu walk and one level load. Row 7 (s4b07) came with it as extra data. Agent 1 rated the run's STUCK-LOCK a WARN at 21:29 (finding 10), so G5 is about C1 only.

**Run.** w6gA = `20261122-210906-w6-gateA-p2fcv-level`: devoff4b-bin, L route, `-Seconds 600`. Cvars:
- `shared_memory_single_hold_rearm=true` (P2, row 23/§22);
- `physical_protect_hold_global_lock=true` (fix (i), row 24/§23);
- `physical_protect_keep_watch=true` (C1);
- `physical_protect_keep_watch_verify=true`;
- plus `framerate_limit=0` and `slow_frame_log_ms=1`.

So every switch of the p2fc arm is on, plus verify.

**Check results** (`build/agent3/s4b/logs/w6gA.check.txt`, 30,076 B, 21:19:38):
- **C1:** init "C1 keep-watch: on (with physical_protect_hold_global_lock)" x1 (21:09:13.865). The first kept protect is at ED19F000, 299,892,736 B (21:09:16.473). The kept count goes 2 → 32768 (19 lines, the last at 21:17:23). Verify on x1 (21:09:20.026).
- **Counters:** K 0 and F 0. Recovered-stale 0, unhandled physical 0, protect-failed 0, and no blocked or no-hold line. Memexport full-buffer total 0; P2c PASS (total 0).
- **Coverage:** 104/119 steps. The 600 s cap hit at story-load, so no level load ran. Agent 3 says verify runs about 5-10x slower on devoff4b. That fits Record's cost (L1286). Gate A also ran while a -j8 build held the host at 100 % CPU (Agent 6, 22:42).
- **Recovered hang:** STUCK-LOCK x5, owner lr 83FAF188 (sub_83FAF180). This is finding 10: WARN (Agent 1, 21:29; Agent 6 confirmed it at 21:55). Dump hang-36276.dmp. The run's errors 5 and critical 1 are those lines. Outside G5. Agent 6 (22:42; `build/agent6/hang/cp-state-s4b24-s4b20.md`) compared this hang with the 83FAF200 hangs in s4b-24 and s4b-20. All three CPs are in the memexport readback full-path sync: gate A's in its submit, the other two in its INFINITE fence wait (an Event wait, not hashing, K checks or hold_global_lock). Gate A's CP kernel time (75-86 %) comes with verify; s4b-24 and s4b-20, without verify, show 3-11 %. So verify slows the CP, but the hang doesn't need verify. All 3 hangs happened while a -j8 build held the host at 100 % CPU; a hang without that starvation is not shown and not ruled out (Agent 6).
- **Labels:** the PROOF labels said "through the level load", but the level wasn't reached. Agent 3 fixed the labels in s4b_check.py (~22:15): "to route mark story-load only, no level load" vs "through the level load".

**Rating.** **G5 PASS, partial coverage** (boot → menu walk → story-load).
- The positive control is there: the first kept protect is logged, and the kept count reaches 32768. So K 0 and F 0 can't mean "C1 never got that far" (§25 D, L1256-L1259).
- §21 A stays open for the level load. A's blind spot (§25 A, L1246) is unchanged.
- Fine for W6: every C1 arm there is p2fc (P2 + fix (i) + C1), as in gate A.
- Before C1 goes default-ON: a p2fc + verify run that reaches the level, with a longer cap and on a quiet host. Agent 1's condition (22:46) names that run: s4bLV, with the fixed sidecar, 3/3 LOADs and the level reached with verify on.
- W6 gate B (w6gB) runs with verify off, so it doesn't close §21 A. Agent 1 ruled at 22:46 that it counts for W6 as "level load without tags"; I rate it in §42.

**Row 7 (s4b07), extra data.** `20261122-214221-s4b-07-c1v-level`: the same bin, route and cap. Cvars: fix (i) + C1 + verify, and no P2 (`s4b07.check.txt`, 14,440 B, 21:54:56).
- **Results:** C1 init on (21:42:28.088); first kept protect ED19F000 (21:42:31.493); kept 2 → 32768; verify on at 21:42:38.567. K 0, **F 92**: the first at 21:42:43.283 on page 01C1B000, the last at 21:49:23.535 on page 02090000. Errors 0, STUCK 0. 104/119 steps; story-load at 202 s, and the level was loading (8131 draws) at the cap.
- **Correction** (sent at 22:07): Agent 3's note said row 7 has no fix (i). In fact it has fix (i) (`physical_protect_hold_global_lock`); C1 keeps a protect only with it (L1556-L1558). What row 7 lacks is P2 (`shared_memory_single_hold_rearm`).
- **My 22:07 call:** there was no C1-OFF verify baseline yet. Agent 12's rule is that F with C1 ON above the C1-OFF baseline means a kept watch missed a write. So I rated C1 without P2 "not cleared". I asked Agent 12 for the mechanism or a baseline, and asked Agent 8 not to add a C1-without-P2 arm.
- **Agent 12 (~22:15):**
  - The 92 F lines fall on 66 distinct pages, all in physical 01xxxxxx-02xxxxxx. The first came 4.7 s after "C1 verify: on." (during boot).
  - The first kept protect (ED19F000) doesn't cover those pages.
  - Gate A differs from row 7 in 3 cvars: P2, `framerate_limit=0` and `slow_frame_log_ms=1`.
  - Agent 3 staged s4bV0 (menus route, fix (i) + verify, C1 off, P2 off) to compare with s4b04 (the same plus C1). It runs only after Agent 1's OK.
- **Agent 12 (22:31), the mechanism,** in `build/agent12/s4-c1v3/new/sdk/src/graphics/shared_memory.cpp`:
  - MakeRangeValid sets the valid bits under G (L356-371), releases G, arms the watch (L373-377), and only then re-hashes the pages (KeepWatchVerifyRecord, L381-383 → L684-705).
  - A write fault in that gap runs the F check (L577-583) against the hash from the page's previous upload. Invalidation never clears the hashes. So any page the CPU changed since its last upload logs F, and that change is why the page is being re-uploaded.
  - With P2, `single_hold_lock` (L351-354) holds G until MakeRangeValid returns, so the fault waits for the fresh hash.
  - All 92 F lines are on one thread, the write-faulting one (t37048 = XThread90B8, F80001A8), on pages 01AE8000-022BF000: 18 at boot, 20 in the menus, 54 after the 3rd INSTALL0_2.DAT burst.
  - Gate A hit the same markers at about the same times (INSTALL bursts at +53/+59/+295 s vs row 7's +54/+61/+314 s after "C1 verify: on."). It had F 0 and ran 110 s past pad mode 3.
- **Subagent B's check (22:44)** used the live files: shared_memory.cpp A4A31038ABDFF94A (32,711 B, 782 lines; = Agent 12's HASHES "new") and xmemory.cpp BCA5E1CF63686E73.
  - Claims (1) and (3): CONFIRMED.
    - The arm at L373-377 is xmemory.cpp L799-808: 3 views, each taking and releasing G (L2451).
    - With P2, G is one process-wide recursive mutex, held from L351-354 until MakeRangeValid returns.
    - The fault enters TriggerCallbacks holding G (xmemory.cpp L581, L619), so F waits for the hash at L703.
  - Claim (2): CONFIRMED, with one wording fix. Valid bits are also written at L63, L114, L124 and L134, but only to clear them, so "valid is set only at L367" is exact. Hashes are written only at L703, and no invalidation path touches them.
  - With P2 on there is no stale-hash path, but two narrow non-race F sources remain:
    - a guest write fault during a file read: the read writes through the physical alias and invalidates only afterwards (xfile.cpp L266-295);
    - turning the verify cvar off at runtime: Record is gated on the cvar (L381) but F on the pointer (L581), so this gives false F too, not only the false K that Agent 12's NOTE (`build/agent12/s4-c1v3/NOTE.md` L38-39) mentions. This one doesn't apply to cvars set at launch.
  - Row 7 can mix race and real lines, because the F check can't tell them apart. A real miss gives the same line, with P2 on or off. It could be a host write through the physical alias that invalidates late or never, or a write through an alias view the watch doesn't cover. B's third path, fix (i)'s Protect race, needs fix (i) off, and row 7 had it on.
  - My reading: gate A is nearly the row 7 config with P2 on; only `framerate_limit=0` and `slow_frame_log_ms=1` differ. It covered the same phases and had F 0. The real-miss paths don't depend on P2, and none showed on this route in gate A. That supports Agent 12's reading of row 7 but doesn't prove it.
- **Result:** C1 without P2 is **unverified by this tool, not failed**. Two ways to settle it:
  - (a) s4bV0 (C1 off; approved for after tonight's windows). Agent 12 predicts F > 0 on the same pages and thread; F = 0 there would refute the race.
  - (b) A verify-only fix that clears `keep_watch_verify_hashes_[page]` inside the valid-bit scope, then a re-run of row 7, expecting F 0 if C1 is clean.
- Until (a) or (b) is done, C1 ships only as p2fc. Agent 8: still no C1-without-P2 arm.

**My line at L1286** reads "C1 neither lengthens that hold nor needs P2 ON, except in verify mode".
- At 22:07 I wrote that row 7 questions the "doesn't need P2 ON" part.
- With Agent 12's mechanism, row 7 shows a second verify-mode exception instead: without P2, verify's F check races MakeRangeValid's re-hash. The line's "except in verify mode" was about Record's cost, not this race.
- So the line holds for C1 itself, as a code reading. But no run yet shows C1 clean without P2, and a verify run needs P2 to give a clean F count.

**Later (22:51).** Agent 12 agreed with the runtime-flip false F (checked at 22:50: Record runs only with the cvar on, L381, but the F check runs whenever the hash pointer exists, L581). It will add that line to the NOTE (its L39-42) once source edits are allowed. It makes none tonight, so shared_memory.cpp A4A31038ABDFF94A stays the checked hash.

**Read.**
- w6gA.check.txt (21:19:38) and s4b07.check.txt (21:54:56) in full, plus both rows' queue.jsonl entries.
- agent3-run-harness.md L891 and L907; SESSION2.md L2902-2907 and L2923-2927; agent12-io-memory.md L1180-1213.
- b2r §21 A, §22, §23, §25 A/D and the P2 caveat in §25.
- Agent 3's messages (21:59, ~22:15, 22:41), Agent 12's (~22:15, 22:31), Agent 6's (22:42; its write-up itself not read) and Agent 1's ruling (22:46).
- Subagent B's check (22:44) of shared_memory.cpp A4A31038ABDFF94A and xmemory.cpp BCA5E1CF63686E73, plus the live d3d12 shared_memory.cpp, xfile.cpp and mutex.h.

**Sent.** The rating went ~22:07 to 3, 1, 12, 8: G5 PASS with partial coverage, the row 7 correction, the ask to Agent 12, and the ask to Agent 8 for no C1-without-P2 arm. Agent 12's mechanism and B's check are recorded here. They went ~22:46 to 12, 3, 1: claims (1)-(3) confirmed, row 7 could still mix, and the two narrow F sources with P2 on, including the runtime-flip false F for Agent 12's NOTE.

## §42 Agent 3's W6 gate B (w6gB): level load without tags (22:46-22:57; task #9, extra)

**Why.** At 22:41 Agent 3 reported that gate B's Toy Pad tags were never placed. At 22:46 Agent 1 ruled that gate B counts for W6 as "level load without tags" and asked me to rate it. I was to tell Agent 1 before 23:45 only if gate B should change W6.

**Run.** w6gB = `20261122-222313-w6-gateB-p2fc-level`: devoff4b-bin, scenario level-l.txt (the L route), 600 s cap. Cvars (w6gB.check.txt L2; "all as W6-GATES.md v2" at L82):
- `shared_memory_single_hold_rearm=true` (P2);
- `physical_protect_hold_global_lock=true` (fix (i));
- `physical_protect_keep_watch=true` (C1);
- `physical_protect_keep_watch_verify=false`;
- plus `framerate_limit=0` and `slow_frame_log_ms=1`.

So this is W6's p2fc arm. Gate A (§41) ran the same switches with verify on.

**Check results** (`build/agent3/s4b/logs/w6gB.check.txt`, 49B56DEC187FC5C3, 28,722 B, 22:31:36):
- **Run:** exit 0, closed by wm_close in 1.51 s at the route's end, 448.01 of 600 s, **119/119 steps**, first frame at 12.0 s (L2, L4).
- **C1:** init x1 (22:23:21.280); the first kept protect at ED19F000, 299,892,736 B (22:23:22.868); kept 2 → 114688 over 39 lines, rising through the level load to the route's end mark (L7-13, L36, L71-75).
- **Counters:** verify off ("C1 verify: on" x0, K 0; L74). Recovered-stale 0, unhandled physical 0, Protect-failed 0, and no blocked or no-hold line (L6, L76-77, L83).
- **P2:** memexport full-buffer total 0 over 36,553 slow-frame lines (L37, L80). `w6gB.p2c.txt` (FE01DB41AEDE331F, 22:31:39) gives PASS (total 0) up to the last logged frame, with memexport activity in 3,426 lines and 60,921 syncs.
- **Route:** the cand marks reach vortex (683/47145), v-idle, v-start, settled and end (785/123950) (L67). The base's attract scenes 788, 790 and 841 are missing because of timing after the route; the check doesn't count that as a BASE item (L64-65).
- **Recovered hang:** STUCK-LOCK x5 at 22:26:29 (L28-33): critical section 0x84959EDC, owner tid 0x17 parked at lr=83FAF200, the GPU thread on PM4 opcode 0x22 (DRAW_INDX). Dump hang-38764.dmp (L34). The run's errors 5 and critical 1 are those lines. This is finding 10, with the same lock, owner thread and lr as s4b-24 and s4b-20 (Agent 6, `build/agent6/hang/cp-state-s4b24-s4b20.md`).
- **logdiff** vs `20261122-210059-s4b-L0-off-level` (L41-49): NEW 6 (the 6 hang lines), MORE 0, FLAG 1 (fatal=1, the dump), GONE 73 with 1 unexpected ("Toypad listener: LOAD", from the missing tags).
- **Host:** sys.csv not slow, but the CPU median was 82.6 % (L70). Threads: XThread9038 65.4 %, GPU Commands 43.1 %, Main 37.5 % (L68).
- **Hint:** LOOK, 9 BASE misses and 0 proof misses (L84-85). Seven of the 9 are the hang: NEW 6, FLAG 1, dumps 1, the error/critical counts, stuck_lock 5, minidump 1 and fatal 1. The other 2 are the tags: the tags-placed mark (220/528 → 220/534) and the GONE LOAD line.

**Tags.** No characters were on the pad (`w6gB.sidecar.out.txt`, 0BEE1C5F8F80887C, 22:30:48):
- The tags were fine (batman, gandalf, wyldstyle), the listener was active, and the handshake ran (L2-16).
- Result (L22): trigger=False, placed=False, load-confirms 0/3.
- Cause, checked in the run's logs: game.log rotated at 22:23:58 (game.2.log ends then; game.1.log starts at 22:23:58.677). The trigger line "Toypad: pad 3 mode 1 lit FF FF FF" came at 22:24:20.774 (game.1.log:4757), after the rotation. Agent 1: the sidecar's tail reopened at the old offset, a harness bug.
- Rows 7, 20 and 23 had 3/3 LOADs (Agent 3).

**Rating.** **PASS for W6, as "level load without tags"** (Agent 1's ruling, 22:46).
- The p2fc arm ran the whole L route through the level load, with C1 keeping up to 114,688 protects. It had no stale, unhandled or Protect-failed lines, a P2 fallback total of 0, logdiff MORE 0, and no new lines besides the hang.
- G8 (W6-GATES.md L212): init and the first kept protect are present, and there are no stale, unhandled or Protect-failed lines. "logdiff NEW 0" is missed only by the 6 finding-10 lines (WARN), so read it by hand, as for gate A. The frame-hash/screenshot part is for the W6 runs against s0, not for this check.
- **No W6 change.** W6's timed runs are title + attract only (matrix-window6.json L27: 5 s settle, 55 s warm-up, 50 s measured), so they exercise less than gate B did. W6-GATES.md's run table (L36-39) has no gate B row, so gate B adds coverage and gates nothing there.
- Not covered: characters on the pad, and verify (off), so gate B doesn't close §21 A (L1068). It also ran on a busy host (82.6 %).

**C1 default-ON** still needs all of:
- s4bLV with the fixed sidecar: 3/3 LOADs and the level reached with verify on (Agent 1, 22:46);
- a quiet host;
- p2fc only, until s4bV0 or the verify-only fix settles C1 without P2 (§41, L2473).

**Finding 10.** Gate B's hang has the same form as the hangs in gate A, s4b-24 and s4b-20. Those three ran while a -j8 build held the host at 100 % CPU (Agent 6); gate B also ran during Agent 2's -j8 native build (20:53:12-22:39:53, `build/agent2/snap4b-run.txt`), with a CPU median of 82.6 %. W6 doesn't test finding 10 (no L route). Agent 6's direct test is two quiet-host L-route rows after the windows.

**Read.**
- w6gB.check.txt (22:31:36) in full, w6gB.p2c.txt (22:31:39) and w6gB.sidecar.out.txt (22:30:48).
- The run dir's file list, the first lines of game.2.log, game.1.log and game.log, and their "pad 3 mode 1 lit" and "Toypad listener: LOAD" lines.
- matrix-window6.json L27; W6-GATES.md L36-39, L205 and L212.
- Agent 3's message (22:41), Agent 1's ruling (22:46) and Agent 6's message (22:42).
- `build/agent2/snap4b-run.txt` (18,578 B, 22:40:17), for the times of Agent 2's -j8 native build.

**Sent.** ~22:57 to 1, 3: PASS for W6 as "level load without tags", no W6 change; the C1 default-ON conditions are unchanged.
