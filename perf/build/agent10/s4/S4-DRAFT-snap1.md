# S4 draft plan, for the user and Agent 1 to decide

Agent 11, tasks #30 and #35. Drafted 2026-11-22 06:55-07:28; updated 07:40-07:45 (Agent 10's P2 rating, Agent 9's merged back-off item) and from 07:50 under task #35 (see "Changed since 07:44").

**This is a draft only.** Nothing here is decided, applied or built. Every row is a proposal. Agent 10's ratings are quoted from the review notes, not re-done here.

**Changed since 07:44** (task #35):
- **Agent 1's answers to §4b (07:47):**
  - #37 is staged only, not an S4 item (marked in §1d, listed in §1f).
  - #7's two cost estimates are both recorded; it is functional-only either way.
  - #32 ships with a switch (OFF) unless Agent 10 rates it output-identical (its #34).
  - #8's memexport caveat is an S4 gate: count the calls in S4a's functional run, and decide a cap in S4 only if that path runs. The staged diff stays as it is.
  - The GO to stage #18 and #20 waits for the S4 kickoff with the user after window 4.
- **nativeB menu exit:** closed for tonight as (a), a recorded difference (§5). Its root cause is a new S4 functional item, #41 (§1h).
- **Harness:** the RECOVERED HANG relabel is done (§5).
- **#24:** Agent 9's draft hook had a style pass at 07:45, and it clamps Q to 2000 µs.
- **#5 fix (i) is rated** (Agent 10, ~07:56, b2r row 24, §23): SAFE at the default and SAFE ON. It is a correctness fix, not output-identical by design, and its checklist item 4 passed. C1 may nest the two heap mutexes only view → parent. ON only together with C1. Updated: row 5, Decisions item 1, §1g, §2a, §2b and §4b.
- **#4 C1 is staged** (Agent 12, 07:51, `build/agent12/s4-c1/`; HASHES.txt: RESULT PASS). Its code isn't rated yet, and its NOTE.md wasn't there at 07:55. Row 4 and §1g are updated.
- **b2r row 23's path** was corrected by Agent 10 at 07:55 (the base `src/graphics/shared_memory.cpp`), so that §4b note is gone.
- **#6 form-2:** Agent 10 won't rate it until code exists; low priority (§23).
- **§6:** the b2r line ranges were re-read at 07:55.

**Sources:** the S4 sections of each agent's notes, read 06:40-07:50 and again for task #35 (line ranges are in §6), plus messages from Agents 1, 2, 8 and 12. The notes were still changing tonight, so re-check the source before acting on a row.

**Still open (07:58; updated as inputs land):**
- C1 (#4): Agent 12's NOTE.md and syntax check (task #31, due 08:25), then Agent 10's rating of the staged code (§21 A-D, the view → parent rule, P2's long-hold caveat).
- Agent 10's other #34 items: #24's review, #32's output-identical check, the R1/R2 summary, and its check of this draft.

**Abbreviations used in the tables:**
- **Agents:** A4…A12 = Agent 4…Agent 12.
- **Files:**
  - b2r = `perf-notes/agent10-batch2-review.md`
  - F = `perf-notes/FINDINGS-AND-CHANGES.md`
  - a5 / a7 / a9 / a11 / a12 = `perf-notes/agentN-*.md`
  - a6h / a6s = `perf-notes/agent6-hang-triage.md` / `agent6-attract-stalls.md`
  - aot / mcr = `build/agent4/s34/aot-pack-proposal.md` / `miss-cache-review.md`
- **Effects:** M = measured, E = estimated. ms/f = milliseconds per frame. GPU Cmds = the GPU Commands thread. Main = the main game thread.
- **Builds:**
  - C++ = a game C++ build with no guest codegen regen;
  - regen = a codegen regen plus a full rebuild;
  - native = the native-GPU bin (rexlego `gpu_native`).
- **Paths:** SDK = `DimensionsRecomp/rexglue-sdk/`; rexlego = `DimensionsRecomp/rexlego/`.
- **Other:**
  - G = the emulator's global lock.
  - s0 = the first S4 build with every switch OFF.
  - W4b = timing window 4 (tonight's runner, `bench/agent8/RUN-WINDOW4B.cmd`).

## Decisions this draft asks for

1. **What goes into the first S4 build?** The proposal is a fast build, S4a: ~6-10 min at -j10 per Agent 2. It would hold the staged items that are SAFE or rated, all OFF:
   - #7 u diagnostic, #8 P2, #5 fix (i) and #38 precise timer wait (all SAFE at the default; fix (i) was rated at ~07:56, b2r §23);
   - on native, #2 miss cache, or #1 shader pack.

   C1 (#4), staged at 07:51 but not rated yet, would wait for two reasons:
   - It edits `xmemory.h`, which turns any build into a full rebuild of both game trees (~37-46 min).
   - Its value is unknown until #7's functional run measures u_block.

   If C1 turns out to be worth it, S4b would be one full rebuild with C1 and the codegen regen (#26, +3-4 min when bundled). See §2a and §3.
2. **Which timing windows, and in which order?** The proposal is W5 first (S4 baseline + timer modes; it needs only S4a), then W6 (upload path). W7-W10 would follow once their items are rated and built. See §2c.
3. **The user questions in §4a:** Toy Pad tags, simde, Defender/PresentMon, the native screenshot check and no-wait pop-in.
4. **The drops in §1f:** confirm them.

## 1. Items

### 1a. GPU memory / upload path, and native shaders

| # | item (owner) | files touched | switch (default) | Agent 10 rating | changes output? | build | expected effect (M/E, source) | test needed | depends on | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **AOT shader pack:** the 4 missing native placement shaders (VS 0xAC449538 / PS 0xAC448F28 + a 2nd pair) (A4, with A7; uses A6's tools) | No source edit. A4's `build/agent4/s35` output: `runtime-cache.cpp` (4 entries) via `-DLEGO_NATIVE_RUNTIME_SHADER_CACHE=<copy>` (today an 869 B stub), plus a merged `lego-microcode-index.cpp` (19,116 + 6 rows) (A2 §2) | none: a data change. Rollback = the previous cache / native3d-bin | first read only, **no verdict**. "Not output-identical by design; gate it as a content fix with the user's visual check" (b2r row 16, §15) | **YES, rendered:** the draws that are skipped today (likely title/menu) draw on native | offline shader compile. Bundled into the native build: < +1 min and < 1 MB, plus ~10-15 min of prep to copy the pack in from `build/agent4` (A2) | E: ≈2-2.5 ms/f render thread in the foreground; up to +15-25% native fps (A7's estimate; F Leads "Two missing native shaders") | b2r §15.1 items 1-5: a stable capture over 2 functional runs with `LEGO_DUMP_MISSING_SHADERS=1`; tools/gpu-aot builds both with no new warnings; both hit at run time (no missing/unrecognized lines, no `draw_missing_*`); **the user's visual check** (native vs Xenos screenshots via `LEGO_GPU_SNAPSHOT_DIR`; the Xenos reference needs the user's visible desktop); the n-row rule becomes `draw_missing_*` = 0, draws/frame ≥ before. Plus A8's stability capture (~8 min) | A4's s35 pack (its `-Go` run was pending at 07:06, A2); A2 build. Makes #2 moot | proposed (~45 min of agent work); nothing built |
| 2 | **Miss-cache stopgap** `LEGO_NATIVE_SHADER_MISS_CACHE` (A4; `shaders.cpp` is not an A4 file) | rexlego `gpu_native/shaders.cpp` only | env var; unset/0 = OFF (forced OFF when `LEGO_DUMP_MISSING_SHADERS` is set) | **SAFE** at the default; ON is output-identical under §15.2 1-8 (b2r row 19, §18) | no: draws stay dropped. ON adds log lines | incremental native C++ | E: upper bound ~6.0 ms/f render thread in the slow state; ~2-2.5 in the foreground (mcr L134-142; F Leads "Two missing native shaders") | functional ON/OFF pair: logdiff NEW 0 / MORE 0, same draws/frame; OFF vs the pre-patch bin gives the same logs; timing A/B with n-prof | moot if #1 lands; A1 GO | **STAGED** `build/agent4/s34/shaders-s34.patch` (328BDAE1…, +229/-11); compiles clean |
| 3 | Native threaded-modes timing matrix `bench/agent4/matrix-native-threaded.json` (A4) | none | arms n0/th1/th2/th3 (`LEGO_NATIVE_THREADED`) | covered by b2r row 16 item 3 | no (timing only) | none | M (functional, n=1): fps 101 → 110-117, but >33 ms frames 8 → ~70 and 1% low −31-34% (F L88; F Leads "Threaded native recording") | it is the test: ×3 per arm, ~30 min | a quiet user window | later-window option; W8b (§2c) can replace it once #21 is ready |
| 4 | **C1 = P1 `physical_protect_keep_watch`:** keep the watches on protects that don't change access (A5's design; A12 staged it at 07:51) | SDK `system/xmemory.cpp` + `include/rex/system/xmemory.h` (the fast path in `PhysicalHeap::Protect`), `graphics/shared_memory.cpp` + `include/rex/graphics/shared_memory.h` (verify mode), `graphics/primitive_processor.cpp`; game rexlego `gpu_native/memory_watch.cpp` (+6/-0; it turns C1 off for the process from static init, §21 C). Diffs: SDK `keep-watch.diff` (1B2BA4E3…, 19 hunks, +362/-3) and `keep-watch-rexlego.diff` (4D0C1079…) | cvars `physical_protect_keep_watch` (false, group Memory) and `physical_protect_keep_watch_verify` (false, group GPU: verify mode, §21 A) | the design: **SAFE** at the default. ON is output-identical under conditions 1-4 on devoff, apart from residual R1 and the bypass writers; "flip ON only with A-D" (b2r row 22, §21, 06:52). **The staged code isn't rated yet.** A10 will check §21 A-D, its place after fix (i)'s second acquire, the lock edges (view → parent only, §23) and P2's long-hold caveat | OFF: none. ON is meant to be identical, but it skips re-uploads, write faults go from ≈0 to F/frame through the AV path, and there is a stale-data risk (bypass writers, R1) | C++ (SDK). **It edits `xmemory.h`, which is in the generated-code closure: a full rebuild of both game trees, ~37-46 min instead of ~6-10 (A2, §3)** | E: GPU Cmds u_block × 3.64-3.85 ms/f, plus Main 0.54-1.02 ms/f (a5 S4.5; a12 S4.4). M (a-vol, 06:20): one 3,844 KB lock per frame. Fault cost on Main ≤0.25 ms/f (a12 S4.8; F 06:31 says ≤~0.14). u_block is unmeasured, so #7 decides: no-go if u_block < 0.1, A/B if ≥ 0.25 | build OFF with counters; functional C1-ON (title, menu walk, level load) with `--slow_frame_log_ms=1` and verify mode (`physical_protect_keep_watch_verify=true`, §21 A); ABBAAB with a profile per run, 60 s floor, sys.csv; b2r §21 A-D | **#5** (or R1 accepted in writing, §21 B). In the diff, the fast-path test starts with fix (i)'s hold (`hold_global_lock.owns_lock()`), so C1 seems to act only with fix (i) ON (my reading of keep-watch.diff L414; NOTE.md pending). Based on #8's and #5's new copies (0BE4BADC… / 141FB1A9…); #7's u result; A10's rating; a level load needs Toy Pad figures or the user | **STAGED** 07:51 by A12 (task #31) in `build/agent12/s4-c1/`, with `chain-live-to-c1.diff` (1D2CC1F3…: diag + P2 + fix (i) + C1 as one diff on live, for reference). `git apply --check` exits 0 for each step, the chain and the rexlego diff, and the 4-step chain on scratch copies reproduces every staged file (HASHES.txt: RESULT PASS). New: xmemory.cpp 6C801EB2…, xmemory.h 5A70782E…, shared_memory.cpp A4A31038…, shared_memory.h 82A66445…, primitive_processor.cpp 470BA4BE…, memory_watch.cpp 70829846… (CRLF). No NOTE.md or syntax check at 07:55 |
| 5 | **Fix (i) for the Protect race** (form 1, RW→RW): when a protect adds Write, `PhysicalHeap::Protect` takes G a second time, so G stays held through both host protects (A12) | SDK `system/xmemory.cpp` only (+19/-0, pure additions) | cvar `physical_protect_hold_global_lock`, false (group Memory) | **SAFE** at the default: one untaken branch per write protect. **ON: SAFE**, a correctness fix, not output-identical by design; it adds no lock edge (b2r row 24, §23, ~07:56). Checklist item 4 ("no path takes `heap_mutex_` and then G"): **PASS**. NOTE.md's "G first" wording is wrong on Windows, where the reconcile lock is empty, and PhysicalHeap Alloc* nest view → parent without G, so C1 may nest the heap mutexes only view → parent. ON only together with C1 (§21 gate B). The race itself: **CONFIRMED** (b2r row 20, §19, 06:43) | **YES, behaviour, but only when the race hits:** the page is then armed properly instead of staying watched but writable until the next lock. Not output-identical | C++ (SDK); `.cpp` only, so no full rebuild | correctness only, no fps gain. Cost ON alone: G is held across both host protects of every Write protect, which are most of Main's 0.54-1.02 ms/f in MmSetAddressProtect. With C1 ON, ≈0 (a12 S4.11) | NOTE.md's test plan 1-5 (b2r §23 L1160-1166): syntax with `-Live` after the apply; OFF behaves as today (logdiff NEW 0, the same frame hash); ON functional runs (title, menu walk, one level load): logdiff NEW 0, no hang or stall, no "PhysicalHeap::Protect failed"; with C1, §21 gates A-D. Timed only inside the C1 A/B. Keep `scribble_heap` off in S4 runs (a pre-existing, debug-only exception) | C1 (#4) depends on it. Same function, so C1's Protect change goes after fix (i)'s second acquire | **STAGED** `build/agent12/s4-fixi/protect-hold-g.diff` (80CAD795…; `xmemory.cpp` 6E8FA1BA… → 141FB1A9…); apply check and syntax PASS (07:02); rated SAFE ~07:56 (b2r §23) |
| 6 | **Form-2 fix** (RO/NoAccess→RW): invalidate on any protect that adds write access. A pre-existing upstream gap (A12, with A10) | SDK `system/xmemory.cpp`, Protect path (a force flag past TriggerCallbacks' any_watched early-out, :2321) | its own switch, not named | **not rated:** no code yet. A10 (§23, ~07:55): NOTE.md L103-122's three asks fit the code; rate it when code exists; low priority, agreed. Latent in this game: all its protects are RW→RW (b2r §19 addendum, 06:50) | **YES, behaviour:** extra invalidations and re-uploads | C++ (SDK) | correctness only; possible extra re-uploads (E, §19) | the same gate as #5 | independent of C1 | design only (note in `build/agent12/s4-fixi/NOTE.md`); an upstream gap that matters for other titles |
| 7 | **Upload-hash diagnostic ("u")** `shared_memory_upload_hash_log` (A12) | SDK `graphics/d3d12/shared_memory.cpp` only | cvar, false (hot-reload) | **SAFE** at the default. ON is SAFE for functional runs; +1-3 ms/f on GPU Cmds, so **no timing arms** (b2r row 21, §20) | no rendered change. ON writes 1 log line per frame (~14 MB per 5 min) | C++ (SDK), compiled in OFF | measurement only: it gives C1's u_block. Cost when ON: A10 says 1-3 ms/f, A12 says 0.25-0.4 (≤0.75) ms/f. Both are recorded: it is functional-only either way, so no decision is needed (Agent 1, 07:47) | syntax `-Live` after apply; one functional devoff title run with the cvar and `--slow_frame_log_ms=1` (~5 min); parser `bench/agent12/s4_uhash.py` | applied first (a12 S4.10); A1 schedules it after the S4 OK | **STAGED** `build/agent12/s4-diag/upload-hash-log.diff` (D2905301…, +145/-0); apply check and syntax PASS |
| 8 | **P2 `shared_memory_single_hold_rearm`:** one G hold per re-arm instead of 4-5 (A12) | SDK `graphics/shared_memory.cpp` only (+30/-0, pure additions) | cvar, false (group GPU) | **SAFE** as a default-off candidate: "ON is output-identical and SAFE for functional and timing runs" (b2r row 23, §22, 07:34). **Caveat:** the memexport fallback `RangeWrittenByGpu(0, SharedMemory::kBufferSize)` (d3d12 `command_processor.cpp:3063`, used when `memexport_ranges_` is empty) would become one long G hold, ~3× today's longest section (latency only). **An S4 gate, not a change tonight** (Agent 1, 07:47): count the full-buffer calls in S4a's functional run (§2b step 3); a length cap (e.g. ≤ 4 MB) is decided in S4, and only if that path runs. The staged diff stays as it is | no: output-identical (A12; A10 agrees, §22) | C++ (SDK) | E: 0.23-0.82 ms/f (a12 S4.4; F Leads "Memory re-uploads") | syntax PASS (07:02); build OFF; an ON functional run that also counts the full-buffer `RangeWrittenByGpu` calls (b2r §22 test step 2); timing A/B | the memexport count from S4a's functional run (an S4 gate); C1 is based on its output | **STAGED** `build/agent12/s4-p2/single-hold-rearm.diff` (77BEB64E…; 15C89EDB… → 0BE4BADC…); apply check and syntax PASS (07:02); rated SAFE 07:34 |
| 9 | P3 `shared_memory_batch_arm`: arm once per UploadRanges (A12) | SDK `graphics/d3d12/shared_memory.cpp` | cvar, OFF (a5 L751: "All are new cvars, default OFF") | not rated | no (intended) | C++ (SDK) | E: only for ranges > 2 MiB | only if the S4 counters show multi-chunk uploads | counters from the S4 build | conditional |
| 10 | P4 hot-range demotion (A12) | SDK `graphics/shared_memory.cpp/.h` | not given | not rated | unclear (behaviour change) | C++ (SDK) | E: an alternative to C1 | n/a | only if C1 is rated unsafe; C1 is now SAFE at the default | fallback, probably not needed |
| 11 | M1 non-temporal upload copy (A5) | SDK `graphics/d3d12/shared_memory.cpp:328` | cvar, OFF (name not given) | not rated. A5 asks A10 to check alignment/tail handling and an sfence after the streaming stores | no: the same bytes, GPU copy recorded in the same order (a5 L826) | C++ (SDK) | E: ≤ (1−u) × 2.9-3.1 ms/f × 10-30%, unmeasured; risk low | bench in `bench/agent5`, then functional + ABBAAB | #7's u; rebase on #7's file | proposed |
| 12 | M2 hash-skip (A5) | SDK `d3d12/shared_memory.cpp` + `graphics/shared_memory.cpp/.h` | not given | not rated; A10 to rate the collision risk | unclear: probabilistic (64-bit hash) | C++ (SDK) | E: at most u_page × memcpy, minus the hashing; reuses #7's hashing | n/a | only if C1 is unsafe | fallback |
| 13 | M3 async copy worker (A5) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | not recommended by A5 |
| 14 | G1 game-side protect filter: hook sub_82BD2808 and skip access-unchanged protects (A5) | rexlego `gpu_native/hooks_buffer.cpp` | not given | not rated | yes, unless A5's conditions 3-4 and the `current_protect` update hold | C++ (rexlego) | E | n/a | only if an SDK change is refused | fallback, high risk |
| 15 | C1 optional knobs: size floor; C1b (A5) | as #4 | size floor: cvar, 0 | not rated; C1b "needs its own rating" | as #4 | C++ | n/a | n/a | #4 | optional |
| 16 | Narrow the VB upload to the indexed span (A5) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | **dropped** by A5 (a5 S4) |
| 17 | Upload matrix on native3, slim x5 `bench/agent5/matrix-native-uploads-x5.json` (A5) | none | batch-2 upload toggles | toggles rated in b2r row 9 | no (timing) | none | "the 60 s scored windows will most likely tie"; it checks for a first-minute hitch (F L30) | 9-11 runs, ~23-28 min (full ~41 min) | a quiet window | later-window option |

### 1b. D3D12 submission and native threading

| # | item (owner) | files touched | switch (default) | Agent 10 rating | changes output? | build | expected effect (M/E, source) | test needed | depends on | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 18 | **R1 stage 1: split the end-of-frame submit** in `RefreshGuestOutput` (A7) | SDK `graphics/d3d12/command_processor.cpp/.h`, `d3d12/deferred_command_list.h` | cvar `d3d12_submit_split_kb`, 0 = OFF; kInitOnly (b2r §17 cond 4) | **SAFE** as a default-off test bed under conditions 1-6, "no win alone" (b2r row 18, §17). Cond 5: leave it OFF on native builds unless tested separately. "Both need Agent 1's GO to stage" (§17 L802) | no: the same image by design | C++ (SDK); its headers are in no game TU's deps (A2) | E for stages 1+2 together: GPU Cmds −0.7 to −1.0 ms/f of the ~1.3 ms/f swap submit, up to ~+20% fps if that thread stays the limit (a7 #22 §4; F Leads "Split the end-of-frame submit"). Stage 1 alone: no win expected | functional ON/OFF with a clean logdiff; count the splits suppressed by the query guard and by `CanEndSubmissionImmediately`; one pass with `d3d12_readback_memexport=true`; timing only with #19 | A1's GO to stage, deferred to the S4 kickoff with the user after window 4 (Agent 1, 07:47); #20 must reset its filter on a split | proposal (05:35); design only |
| 19 | R1 stage 2: hand the submit to a worker (A7) | as #18, plus the worker (not itemized in my sources) | cvar `d3d12_async_submit`, OFF | **not rated** | no (by design) | C++ (SDK) | E: most of #18's estimate | functional + a 10-min soak, then a timing A/B | #18; A10's rating; A1's GO | design only; risk medium-high (F) |
| 20 | R2: filter redundant commands (A7) | SDK `d3d12/deferred_command_list.h/.cpp` | cvar `d3d12_filter_redundant_commands`, OFF (assumed; the default isn't quoted) | step 1 **SAFE**; step 2 **SAFE-IF** (a)-(e) (b2r §17). (a): pure state setters only, never barriers, clears, copies or draws. (d): anything that reaches the real list outside the deferred stream resets the filter, and so does an R1 split (L799). (e): no new debug-layer messages, plus a frame comparison | no (intended) | C++ (SDK) | E: ≤0.2 ms/f (F: "ranked second") | D3D12 debug layer with no new messages; frame comparison; logdiff | A1's GO to stage (deferred to the S4 kickoff, as for #18); with #18 | design only |
| 21 | **S4-T1: raise the priority of the native worker chain** (A7, task #26) | rexlego `native_worker.cpp:346`, `native_recording.cpp:138`, `native_preparation.h:21-26` | env `LEGO_NATIVE_CHAIN_PRIORITY=1`; unset = OFF | **not rated.** F says "Agent 10 wants one more code proof"; I couldn't find its source in b2r (b2r §15.4's must-prove 1-5 cover `LEGO_NATIVE_THREADED` itself) | no ("same output", F) | native C++ | aims at the threaded modes' slow frames. With threading: >33 ms frames 8 → ~70 and 1% low −31-34% (M, functional, n=1; F L88). No fps estimate | W8b (§2c): threaded with chain priority off vs on; score p99, 1% low and >33 ms/min next to mean fps; ≥3 runs per arm | A10's rating; §15.4 must-prove 1-5 for threaded mode; #22's results (inconclusive: the slow state, see #22) | proposed; risk low-medium |
| 22 | Zero-code threaded checks (A7) | none | env `LEGO_NATIVE_TIMING=1` (n2, n3) and `LEGO_NATIVE_PARALLEL_DRAWS=0` (n2) on native3d | n/a (no code) | no | none | finds which chain stage holds the slow frames (diagnosis for #21) | it is the test (functional, hidden desktop) | none | **ran; inconclusive** (a7 "Task #33", 07:42). Functional only, on a saturated machine (busy ~100%, background ≥10 cores), n = 1 per arm: n2t (n2 + TIMING) 136.7 fps / p99 21.6 ms / 23 frames >33 ms per min, no slow state; n3t (n3 + TIMING) 122.9 / 37.2 / 114, slow state from 100 s; n2s (n2 + PARALLEL_DRAWS=0) 123.6 / 32.8 / 69, slow state from 79 s. The tail follows the E-core slow state (n3t: 76 of 114 slow frames after the onset; n2s: 58 of 69 in the two 10 s bins with E-cores at 566-663 MHz), so TIMING and PARALLEL_DRAWS can't be judged. A timed test needs n ≥ 3 interleaved with a reference arm, busy < 0.97, sys.csv with the slow-state check, and scoring ≥60 s after the first frame (A7) |
| 23 | Slowest-frames read-out for window 4's results (A7) | a new script in A7's bench (name not given) | n/a | n/a (tool) | no | none | scores p99, 1% low and >33 ms frames per minute per run | on W4b's results | none | in progress (F 06:38) |

### 1c. Render-thread busy-wait, stuck lock and codegen

Agent 9 merged the two render-thread busy-wait fixes and Agent 6's stuck-lock fix into one S4 item at 06:57 (F 06:58; F Leads "Two busy-waiting threads"). Stage 1 is the back-off hook (#24). Stage 2, the wake-up signal (#25), comes only if stage 1 hurts the slowest frames. Rows #24-#25 follow Agent 9's merged item (a9 S5.2, written 07:29-07:36). It also takes in Agent 6's GetData poll (Agent 1's scope addition, 07:20) and probe P1 (#28).

| # | item (owner) | files touched | switch (default) | Agent 10 rating | changes output? | build | expected effect (M/E, source) | test needed | depends on | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 24 | **GPU-wait back-off, stage 1** (A9; a9 S5.2.2). Merges (a2), A6's (e) (= Q 0), A6's GetData-poll fix and probe P1 (#28). Hooks: H0 `sub_83FBF7D0` (start of each fence wait, loop L1), H1 `sub_83FAF180` (L1's poll step), H2 `sub_83FB09E8` (GetData; loop L2, the back-to-back query poll, gated on lr 0x82BDD028), and H3, a STATS-only kick counter on `sub_83FC0C10`. A stalled wait spins `_mm_pause` for S µs, then calls `SwitchToThread`, then sleeps Q µs per poll on a high-resolution waitable timer | rexlego only: new `src/gpu_wait_backoff.cpp` (draft `build/agent9/s4/fence-wait/gpu_wait_backoff.cpp.draft`, 07:29; a style pass at 07:45 matched it to rexlego's hooks and the pch load macros; not compiled) + `CMakeLists.txt` before :168, inside `if(NOT LEGODIMENSIONS_NATIVE_GPU)`, with the define `LEGO_GPU_WAIT_HOOK_GETDATA=1` guarding H2/H3. No SDK change; env config only | env, read once: `LEGO_GPU_WAIT_BACKOFF_US=<Q>` (unset = OFF; 0 = yield on every later poll; > 0 = one yield, then a Q µs sleep per poll; Q is clamped to 2000 and each timer wait to 20 ms); `LEGO_GPU_WAIT_SPIN_US=<S>` (default 30, max 200); `LEGO_GPU_WAIT_STATS=1` (P1's counters, one log line per 5 s; works with the back-off OFF) | **not rated**. A10's review list (a9 S5.2.5): no guest writes; the reset rules; the lr gate and S_FALSE == 1; the Xenos-only guard; the OFF-path cost; the per-thread timer; the pch-equivalent loads | no: the hooks write no guest memory or registers; only the time of the next poll changes (a9 S5.2.2) | C++ (rexlego), no regen. **Xenos (devoff) builds only:** native never reaches L1's fence (Agent 3, 07:34), and it already hooks GetData in `gpu_native/queries.cpp`, so a GetData hook there would be a duplicate symbol | E: −0.7 to −0.8 of a core while the render thread waits; L1 spins 0.88 of a core, 13 ms/f (a-prof; F Leads). L2's share is unknown until P1. Latency: up to one quantum after the fence passes, half on average. No fps gain promised: on this ~15 W CPU it can only help by leaving power to GPU Cmds | a9 S5.2.4, menus + attract only until §4a Q1: (0) A10's review + A2's map check (the hooked names resolve to `gpu_wait_backoff.cpp.obj`); (1) P1: STATS=1, back-off OFF, one attract profiling run; (2) functional Q = 250 vs OFF: gate_logdiff NEW 0 / MORE 0 / flags 0, the same exit codes, no new STUCK-LOCK; (3) the W9 sweep (§2c); (4) A6's loaded-machine arm: devoffB hook build, attract-long, OFF vs ON, ≥3 runs each, STUCK-LOCK counted by owner site, frames ≥5 s | grants for rexlego `src` and `CMakeLists.txt` (A1/the user); A2's build (devoffB sources + the file, OFF, no regen, ≤ -j10); A10's review; A6 (step 4); A7's read-out (#23); the runner (A8's role) for steps 1-4 | merged S4 item; **draft hook written** (07:29; style pass 07:45), not compiled; risk medium (wake latency) |
| 25 | GPU-wait back-off, stage 2: wake on GPU write (A9's (a1); a9 S5.2.3) | the same hook file: in a stalled wait, H1 and H2 sleep with `WaitOnAddress` on a CP sequence counter (1 ms timeout) instead of the Q sleep. SDK `graphics/command_processor.cpp/.h`: `seq.fetch_add(1)` after every guest-visible CP store, and `WakeByAddressAll` when there are waiters: EVENT_WRITE_SHD :1415 (L1's fence and L2's q+24), EVENT_WRITE_ZPD :1449, :1274, :1294, :1312, :1419, :988 and the RPTR write-back :314-316. One counter serves both loops. Link `Synchronization.lib` | not given (it replaces #24's sleep in the same file) | **not rated**. A10 checks the memory-order argument and the SDK diff (a9 S4.1.3 (a1)) | no (A9) | C++ (SDK + rexlego), no regen | E: ~0.85 of a core freed (F Leads), with a shorter wake-up than #24's sleep. No fps gain promised | a9 S5.2.4 steps 0-4 again, with the SDK change | only if every #24 quantum loses on p99 or the 1% low in W9 (a9 S5.2.4 step 3); grants for both trees (adds SDK `command_processor.cpp/.h`); A6's stuck-lock check; A10's review | design only; risk medium |
| 26 | (b) codegen: `db16cyc` → `_mm_pause` (A9) | SDK `src/codegen/builders/system.cpp:51-73` | none at run time (a codegen change) | **not rated**; A10 to review the generated diff | no ("adds pauses only"), but **it changes generated code** | **regen + rebuild**: ~2-4 min per bin if few TUs have a db16cyc site (unverified; A9 can count), worst case ~35-45 min; +3-4 min if bundled with an `xmemory.h` batch (A2 §3) | E: cheaper guest spin loops; not quantified in my sources | generated-diff review; functional; timing A/B (W10) | A9's SDK codegen grant back; A2's regen; A10 | design only; risk low |
| 27 | (c) codegen spin policy (A9) | SDK codegen, probably near #26 | not given | not rated | unclear | regen + rebuild | not given | n/a | a grant + a regen | ranked last |
| 28 | Probe P1 (A9) | now inside #24's hook file: P1's pass-through hooks have to be H0/H1, since each name can have only one strong definition (a9 S5.2.2) | `LEGO_GPU_WAIT_STATS=1`; unset = OFF | with #24 (not rated) | no (diagnostic) | with #24 | counts waits per frame, the wait-duration histogram and L2's blocking polls per frame; these size S and Q | functional only: one attract profiling run, never timed (#24's step 1) | #24's build | **merged into #24** (a9 S5.2) |
| 29 | Probe P2: `--slow_frame_log_ms=1` (A9) | none | existing cvar | n/a | no (log lines only) | none | slow-frame log | any functional slot | none | can run now |
| 30 | Scene-walk count probe (A9, with A7) | new rexlego `src/scene_walk_probe.cpp/.h`; CMake option `LEGODIMENSIONS_SCENE_WALK_PROBE` (after :154); `#ifdef`s in `native_memops.cpp:166-185` and `native_skin_diagnostics.cpp:176-217` | CMake option, OFF (compiled out) | "diagnostic only" (b2r row 16 item 2). §15.3: "Functional runs only, never timing". Rule out the frontend confound first with one native `-Profile` pair, frontend on vs off (no code needed) | no (counts only) | a separate native probe build (native3d-probe) | explains up to 2.35 ms/f on native's Main. A9 says it's the UI/HUD render (F Leads "The main game thread's scene walk") | the no-code `-Profile` pair first; then functional probe runs only | A2's probe build; A10's review | proposed |
| 31 | Codegen: keep more guest registers as locals (A9) | n/a | n/a | n/a | n/a | regen | ~0 on the standard path (the ~2 ms/f was render-thread spin); it may help native's Main (F Leads) | n/a | n/a | moved down (06:00): not this round |

### 1d. Pipelines and shader storage

| # | item (owner) | files touched | switch (default) | Agent 10 rating | changes output? | build | expected effect (M/E, source) | test needed | depends on | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 32 | **Warm-boot pipeline fix:** `pipeline_cache.cpp:564`, `creation_thread_original_count` → `creation_thread_needed_count` (A6's (b)) | SDK `graphics/d3d12/pipeline_cache.cpp:564` (1 line) | a switch, OFF, unless A10 rates the fix output-identical (Agent 1, 07:47; A10 checks this in its #34) | **not rated** | output-identical (A6), but behaviour changes: from the second launch every cached pipeline is built before the game resumes (today up to ~9 can still be building). "The code it turns on has never run here" (F) | C++ (SDK) | E: fewer first-view freezes on warm boots; not quantified | warm boot with `-SeedXenos build\agent3\seed\devoff2-214`; functional | A10's rating, and its #34 check (a switch unless rated output-identical) | proposed |
| 33 | **Don't wait for pipelines** (opt-in no-wait mode) (A6's (c)) | SDK `d3d12/pipeline_cache.cpp/.h`, optionally `d3d12/command_processor.cpp` | cvar, false (placeholder name `d3d12_async_pipeline_no_wait`) | **not rated** | **YES, visible:** objects whose pipeline isn't ready are skipped for a few frames (pop-in) | C++ (SDK) | E: trades shader-compile freezes for a few frames of missing objects | functional; **the user judges the pop-in by eye** (§4a) | the user's answer | proposed |
| 34 | Dropped-draw counter for #33 (A6, optional) | SDK `d3d12/command_processor.cpp:2727` | with #33 | not rated | no | C++ (SDK) | counts the draws #33 skips | with #33 | #33 | optional |
| 35 | Native pipeline pre-build at a seeded boot (A6) | probably none: the existing recipe and seed files, via `PreparePipelineLibrary` and `LEGO_NATIVE_PSO_PREPARE_THREADS` (a6h §9). Whether code is needed isn't stated | existing env | not rated | no (intended) | probably none | M: a cold first visit froze 4.3 s for one 56-pipeline frame; with a warm driver cache the route built 187 pipelines in 283 ms (F Leads "Native pipeline builds") | a warm-recipes arm in the harness, "only allowed after window 4" | a harness change (A3/A8); after window 4 | proposed |
| 36 | Warm Xenos shader storage for benchmarks (A3, A6, A8; finding 8) | none (seed files copied per run) | runner option `-SeedXenos` | n/a | no (a measurement aid) | none | M: first-use pipeline builds 264 → 56, none in the proposed benchmark window (05:42; F Leads "Pre-filled shader cache") | done | none | ready for later windows |
| 37 | Delay the watchdog's crash dump until a lock has been held ~30 s (A6) | SDK, the krnl `RtlEnterCriticalSection` stuck path; the exact file isn't located yet | not given | not rated | no | C++ (SDK) | M: each dump freezes the game 1.7-3.6 s | with #24's loaded-machine arm | none (not S4) | **Staged only, not an S4 item** (Agent 1, 06:28; confirmed 07:47). F's Leads were stale and were fixed at 07:48. Listed in §1f |

### 1e. Timer and power (Agent 11)

| # | item (owner) | files touched | switch (default) | Agent 10 rating | changes output? | build | expected effect (M/E, source) | test needed | depends on | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 38 | **Precise timer wait** (A11, finding 6) | SDK `src/core/timer_queue.cpp` only (`timer_queue.h` is in the generated-code closure, so it stays untouched, A2) | cvar `timer_queue_precise_wait`, false, kInitOnly | **SAFE** as a default-off candidate (b2r row 15, §14). Before any default flip: (a) before Win10 1803 there is no high-resolution waitable timer, so fall back to blocking or warn; (b) the "Timer Queue: precise wait" line is present ON and absent OFF; (c) ~1 ms jitter (p50 1.04, p99 ~6 ms); (d) publication/Stop up to 1 ms late; (f) a game timing A/B through A8 | no rendered change, but the wait mode moves frame time (d0f vs d0t), so it needs timing | C++ (SDK), `.cpp` only | M (bench): precise 1.9% CPU, median gap 1.07 ms, p99 3.8 ms, 5.4% stale, vs spin 30.4% CPU, 49.7% stale (a11). M (in game): the TimerQueue thread spins 31-44% of a core on the hidden desktop and 62% in window 3; blocking 0.3-0.5%. E: precise ≈ blocking's CPU, without the ~15.6 ms rounding that blocking has at the default timer resolution | build OFF: no log line; ON smoke: the line appears and the thread's CPU drops; timing in W5 (§2c) | window 4's d11t result; caveat (a) | **STAGED** `build/agent11/timerq/stage/timer_queue.cpp` (015C04A2…), `build/agent11/timerq/timerq.diff` (D07A2DC4…, +73/-6); the live tree is pristine (D8724B29…) |
| 39 | **d11t timer bundle** (A11) | none: `bench/agent8/run/matrix-window4.json:37-42` | env `REX_TIMER_WAIT_BLOCKING=1` + 8 timer cvars, including `host_timer_resolution_ms=1` and `host_timer_throttling_optout=true` | n/a (existing switches) | no rendered change; it changes frame pacing | none | M: TimerQueue thread ~40% → 0.3-0.5% of a core; process 2.2-2.4 → 1.8-2.1 cores (F L69). Without the 1 ms resolution, blocking cost fps: d0t 90.9 vs d0f 145.2 fps (functional, n=1, 03:30), likely the ~15.6 ms default tick. Window 3 (timed), corrected by A7 at 07:42: the d11 arm (the 8 timer cvars, spin wait) = 157.8 fps, n = 3, −3.1% vs d0, every run outside d0's range (it read −2.3% before d11-r1 was flagged: light phase, scene 0.036) | W4b arm; every d11t game.log must show "Host timer resolution set to 1 ms (background opt-out on)" | none | **LIVE in window 4.** Window 4 can't separate the blocking wait from the other timer cvars (that needs d11 vs d11t, W5), doesn't test #38, and won't explain the slow state |
| 40 | **Measurement row: package-power columns in sys.csv** (A11 staged it; A8 owns the sampler. A bench tool, not game code) | A8's `bench/agent8/run/drivers/LdSys.cs`, via `bench/agent11/syscsv-pkg/LdSys.cs.diff` (+25/-4), plus the 1-line `sys_summary.py.diff` on `bench/agent8/run/sys_summary.py` (`header_ok` allows extra trailing columns; cosmetic) | none: once adopted, every sys.csv gets 4 columns at the end: `pkg_w, pp0_w, pp1_w, dram_w` (W, from the Energy Meter RAPL counters) | not rated (bench tool) | no game change | none: the sampler compiles its own DLL, and the cache key follows `LdSys.cs`'s hash | tests the power-limit (PL1) explanation of the slow state: a slow state on a package-power plateau points to PL1, and one well below any plateau rules it out | **Adoption (A8, after window 4):** (1) apply `LdSys.cs.diff` (and `sys_summary.py.diff`); (2) start the sampler once outside a timed run, so the DLL compile doesn't land in one; (3) `pthrottle_w4b_hash.ps1` then flags `LdSys.cs` and `sys_summary.py`, which is expected. Staging tests: `test_syscsv_pkg.ps1 -Compare -Rounds 3`, `test_sys_summary_compat.py` | window 4 finished; no W4b file changes before then | **STAGED and tested** (07:21-07:23, no game): `test_syscsv_pkg.ps1 -Compare -Rounds 3` PASS 58/58 (3 staged + 3 original sampler runs); sys_summary compat PASS; both diffs pass `git apply --check` against A8's current files (unchanged, hashes checked). The same sampler CPU as today (1.17 vs 1.15 ms per 1 Hz sample, medians); about +1.7 ms of wait per sample in the PDH collect. `dram_w` reads 0 on this laptop; the first row is not meaningful. Details in a11 |

### 1f. Dropped (not in S4)

| item | owner | when | reason |
|---|---|---|---|
| One DXBC shader translator per thread (A6's (a)) | A6 | 06:23 | Translation is only 1-2.5% of a compile freeze: 31.4 ms against 2,169.3 ms of pipeline creation over 49 misses (a6s §11.1; F Leads "One shader translator per thread") |
| Power-throttling opt-out `host_execution_throttling_optout`, and the runner switch | A11 | 06:27 | No effect (task #24). The opt-out was confirmed on, and the slow state came in 3 of 3 runs with it and 3 of 3 without (finding 7; F Leads "Power-throttling opt-out"). The staged diff (75756E8D…) is kept for reference only |
| `NativeWorkerThrottleFrames(2)` | A7 | task #26 | It would add up to one frame of latency; the game's pacing assumes at most one (draw.cpp:5449-5450); and it only absorbs guest-side hiccups, not stalls in the chain (a7 L299-302) |
| Narrow the VB upload to the indexed span (#16) | A5 | a5 S4 | dropped by A5 |
| M3 async copy worker (#13) | A5 | a5 S4 | not recommended by A5 |
| Codegen registers as locals (#31) | A9 | 06:00 | moved down rather than dropped: worth ~0 on the standard path |
| A6's (e), a zero-quantum back-off | A6 | 06:57 | merged into #24 (quantum 0), not dropped |
| Probe P1 (#28) and A6's GetData-poll fix | A9, A6 | 07:20-07:36 | merged into #24 (P1 = `LEGO_GPU_WAIT_STATS=1`; the GetData poll = hook H2, Xenos only), not dropped |
| Delay the watchdog's crash dump until a lock has been held ~30 s (#37) | A6 | 06:28; confirmed 07:47 | staged only, not an S4 item (Agent 1). F's Leads, which still listed it, were fixed at 07:48 |

### 1g. Shared files and apply order (from the notes; check again when staging)

1. **SDK `src/system/xmemory.cpp`, `PhysicalHeap::Protect` (L2128-2144):** #4 C1 (a fast path placed after fix (i)'s second acquire; it also edits `xmemory.h`), #5 fix (i) (a second G acquire; TriggerCallbacks :2273-2430 unchanged) and #6 form-2 all touch this one function. C1 may nest the two heap mutexes only view → parent (b2r §23).
2. **SDK `src/graphics/shared_memory.cpp/.h`:** #8 P2 (staged: 15C89EDB… → 0BE4BADC…), #4 C1 (based on 0BE4BADC…, → A4A31038…; it also edits `shared_memory.h`), #10 P4 and #12 M2.
3. **SDK `src/graphics/d3d12/shared_memory.cpp`:** #7 u diag (staged: B120D07C… → BB0838CE…), #9 P3, #11 M1 (:328) and #12 M2. Later patches rebase on BB0838CE….
   - **Apply chain** (a12 S4.10; A1 06:36): (1) #7 diag, (2) #8 P2, (3) #5 fix (i), (4) #4 C1. Applying the first three in order to scratch copies reproduces the staged files byte for byte (a12).
4. **SDK `d3d12/command_processor.cpp/.h`:** #18, #19, #33's optional part and #34 (:2727).
5. **SDK `d3d12/deferred_command_list.h/.cpp`:** #18 (.h) and #20 (.h/.cpp). A split resets R2's filter (b2r §17 cond (d)).
6. **SDK base `src/graphics/command_processor.cpp/.h`:** #25 (sequence counter + WakeByAddressAll). C1's bypass writers live in the same file (:315 :437 :1289 :1305 :1368 :1415 :1444 :1465), so the reviews overlap. No textual conflict is known.
7. **SDK `d3d12/pipeline_cache.cpp/.h`:** #32 (:564) and #33.
8. **rexlego `gpu_native/shaders.cpp`:** #2 only. #1 is data + CMake, so there is no textual conflict, but it makes #2 moot.
9. **rexlego `gpu_native/hooks_buffer.cpp`:** #14 G1. It is also C1's PoolCopyHook bypass writer (:197-198, :343-345; "likeliest real risk", native only) and the miss cache's residual 2 (:190-198).
10. **rexlego `CMakeLists.txt`:** #30's option (after :154) and #24's new hook file (before :168, inside `if(NOT LEGODIMENSIONS_NATIVE_GPU)`, so Xenos builds only). The CMake edit makes both trees re-run CMake (7-25 s each, A2).
11. **rexlego `native_worker.cpp` / `native_recording.cpp` / `native_preparation.h`:** #21 only. Every gpu_native file and `native_preparation.h` is a fingerprint input, so changing one also recompiles device.cpp, pipeline_library.cpp and shader_archive.cpp (A2).
12. **SDK `src/codegen/builders/system.cpp`:** #26, and probably #27. These are the only items that change generated code.
13. **SDK `src/core/timer_queue.cpp`:** #38 only.
14. **Native-only items:** #1, #2, #21, #30. #1 needs a CMake reconfigure. C1's §21 condition C keeps C1 inert on native from startup: in the staged code, rexlego `gpu_native/memory_watch.cpp` calls `Memory::BlockPhysicalProtectKeepWatch()` from static init. That is a gpu_native file, so C1 also touches a native fingerprint input (item 11). **Xenos-only:** #24 and #25's hook side. Native builds never reach L1's fence and already hook GetData in `gpu_native/queries.cpp` (a9 S5.2.1).
15. **Rebuild cost (A2):** `rex/system/xmemory.h` and `rex/thread/timer_queue.h` are in the generated-code closure. Through the PCH they reach all 440 generated TUs, so editing either one rebuilds both game trees fully. Of the items above, only C1 (#4) edits such a header. The other SDK headers on the list are in no game TU's deps: `graphics/command_processor.h`, `shared_memory.h`, `d3d12/command_processor.h`, `deferred_command_list.h` and `pipeline_cache.h`.

### 1h. Root-cause investigations (functional only; from 07:47)

| # | item (owner) | files touched | switch (default) | Agent 10 rating | changes output? | build | expected effect (M/E, source) | test needed | depends on | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 41 | **nativeB's earlier front-end exit: find the cause** (A9, A3 and A10; Agent 1, 07:47). nativeB leaves the front end ~12 s before native3d, then plays the same scenes. Closed for tonight as (a), a recorded difference: not a fail item, no rollback | step 1: none (static reads of the A tree). Step 2: instrumented runs; how the logging is added isn't specified yet | n/a (an investigation) | n/a. A10's "(b) result" (07:35): not a codegen change; the whole tree, 164,786 functions, has 0 sequence mismatches (codegen-review L717-769) | no (diagnosis only) | step 1: none. Step 2: whatever the logging needs (not specified); never timed | explains a recorded difference; no fps effect. INSTALL batch to exit: native3d 59.59 / 61.34 s, nativeB 46.50 / 49.70 s (ratio 0.78-0.81). The order nativeB < native3d < devoffB ≤ devoff2 follows guest CPU throughput (guest CPU: native3d 132 / 144 s, nativeB 100 / 113 s). Every host clock the guest can read is wall time and the same in all builds (a3 §7.5). Model (unverified): the front-end page timer waits for, or pauses during, guest background work | (1) **Find the writers** of byte 0x848E2EA2 (no constant-address store, so a computed or indexed address), of bits 3 and 6 of the guest bitset at 0x849004EC (tested in mode 3 via sub_82A832F8), and of [app]+2288. Known so far: sub_82FE08C8 sets +2288 on a "freeze" request; sub_82FE7E40 clears it on "resume", and so does sub_82FF68E8; both requests come from sub_82FF63A8 when the message name at 0x847AD990 matches (`build/agent9/b-clock/fe-gate-flags.txt`; a9 S5.1). (2) **One instrumented arm-time pair**, native3d vs nativeB, on `harness/routes/b-gate-menus-long.txt` (ready; sha256 1F3559C8…), same cvars. Log each sub_82FD4868 call, sub_82FB9020's result, the first event 5 that adds dt and the +2288 transitions, with QPC times. If the arm time moves by ~12 s while the counting time stays the same, that is the mechanism (A10) | window 4 finished (nothing runs before it, A3); for step 2, a way to log (not specified) | **closed for tonight as (a)**; S4 work. Sources: a9 S5.1 (L121-217), a3 §7.5 (L667-702), codegen-review L717-769 |

## 2. Proposed order (draft)

### 2a. Build batches, every new switch OFF

**S4a: the fast first build.** ~6-10 min at -j10 (A2): SDK ~2 min, devoff ~1.5-2 min (relink only), native ~2-3 min.
- **SDK (both bins), all staged:**
  - #7 u diag (SAFE);
  - #8 P2 (SAFE, b2r §22; its memexport caveat is an S4 gate: count the full-buffer calls in the functional run, §2b step 3);
  - #5 fix (i) (SAFE OFF and ON, b2r §23, ~07:56; checklist item 4 PASS; ON only later, with C1);
  - #38 precise timer wait (SAFE).
  - Apply chain: #7 → #8 → #5. #38 is a separate file.
- **Native only (rexlego):** #2 miss cache (staged, SAFE), or the #1 pack instead. The pack needs the s35 output, b2r §15.1 items 1-5 and §4a Q4 first. Bundled, it adds < 1 min, plus 10-15 min of prep.
- **Left out on purpose:**
  - **C1 (#4):** staged at 07:51 but not rated yet. It edits `xmemory.h`, which costs a full rebuild, and its value waits on #7's u_block.
  - **Items without a rating or a GO to stage:** #6, #11, #18-#21, #24-#25, #32-#34. #24 is one new rexlego TU with no SDK change, so it could join S4a once A10 has reviewed it: +0-5 s for the TU plus a CMake re-run of 7-25 s per tree (A2). A2's estimate put the hook TU in the native build, but stage 1 is now Xenos-only.
  - **The regen items:** #26 and #27.
  - **The probe build:** #30.

**S4b: one full rebuild, ~37-46 min (+3-4 min with the regen).** Only if #7's functional run gives a u_block of 0.25 or more (A/B territory). Contents:
- #4 C1 (with §21 A-D before it is ever turned ON);
- #26 db16cyc → `_mm_pause` (bundled);
- whatever is rated by then: #18 + #20 step 1, #21, #24, #11, #6, #32 (with a switch), #33 + #34.

If C1 is a no-go (u_block < 0.1), S4b becomes a fast build again (no `xmemory.h`). #26 on its own would then cost ~2-4 min per bin if few TUs have db16cyc sites, or up to ~35-45 min in the worst case.

**Separate builds:**
- **Probe build (never timed):** #30, as native3d-probe. P1 (#28) needs no build of its own: it is now inside #24's hook file (`LEGO_GPU_WAIT_STATS=1`).
- **Conditional or later:** #9, #10, #12, #14, #15, #19, #25, #27.

**Disk (A2):**
- ~0.56 GiB for two bins built in place;
- +4.2 GiB if the S3d trees are cloned first;
- ~4.2 GiB for a regen snapshot;
- free: 241 GiB.

### 2b. Functional checks for S4a (hidden desktop, never timed, one game at a time)

1. **Static checks:**
   - each staged diff applies to the pristine files, matching the hashes in its staging record;
   - the new cvars exist with their defaults: `shared_memory_upload_hash_log`, `shared_memory_single_hold_rearm`, `physical_protect_hold_global_lock` and `timer_queue_precise_wait`;
   - A2's manifest checks.
2. **OFF matches the base:** compare devoff-S4a with its base bin, and native-S4a with native3d.
   - logdiff NEW 0, with no log lines from any S4 switch;
   - the same draws/frame;
   - boot → title → attract, plus A3's menu walk;
   - a clean WM_CLOSE: exit 0, no dumps.
3. **One ON smoke run per switch** (~5 min each):
   - **`timer_queue_precise_wait=true`:** the "Timer Queue: precise wait" line appears, and the TimerQueue thread drops from 30-60% to a few % of a core.
   - **P2 ON:** logdiff NEW 0 and the same draws/frame. Count the full-buffer `RangeWrittenByGpu` calls: an S4 gate (b2r §22; Agent 1, 07:47). A length cap is decided in S4, and only if that path runs.
   - **Fix (i) ON:** NOTE.md's test plan (b2r §23): title, menu walk and one level load (the level load needs §4a Q1); logdiff NEW 0, no hang or stall, no "PhysicalHeap::Protect failed". It is timed only together with C1.
   - **Miss cache ON** (b2r §18): logdiff NEW 0 / MORE 0 and the same draws/frame.
4. **u diag ON (#7):** one devoff title run with `--slow_frame_log_ms=1`, read with `bench/agent12/s4_uhash.py`.
   - Its u_block decides S4b and W6.
   - Never in a timing arm.
5. **In every run:**
   - sys.csv on, and `scribble_heap` off (its default; b2r §23);
   - the slow-state check (`bench/agent11/timerq_slowstate.ps1`);
   - the package-power columns, once #40 is adopted (A8 applies it after window 4, then starts the sampler once outside a timed run for the DLL compile; the W4b hash then flags `LdSys.cs` and `sys_summary.py`, which is expected).

My estimate: steps 2-4 come to ~7-9 runs of ~5 min, so ~35-45 min of A8's functional time.

### 2c. Timing windows (45 min or less each)

Rules for every window:
- **Metric rule (a7 §3 L306-310; F):** score p99, 1% low and frames >33 ms per minute next to mean fps. p99.9 is secondary. Report per phase (10 s bins).
- **Runs:**
  - ≥3 runs per arm, plus one unscored cold run;
  - Latin-square rounds or ABBAAB;
  - sys.csv on;
  - every measured window starts ≥60 s after the first frame (W4b rule).
  - A12 asks for the median of ≥5 runs, which favours two-arm windows (ABBAAB × 2 = 6 per arm).
- **Before reading fps:**
  - the slow-state check per run;
  - each ON arm's log line is present;
  - ≥6 GB free memory (runner) or ≥8 GB (your check);
  - Defender below ~5% (F, window-4 step 3).
- **Run length:** ~2.5 min per uncapped title-screen run (W4b: 17 runs in ~43 min; my derivation). So 45 min holds at most ~17 runs.

Arm names:
- **base** = the bin S4 is built on: devoff3, or devoffB on the B line.
- **s0** = S4a with every switch OFF.
- **d11** = s0 + the 8 timer cvars (spin wait).
- **d11t** = d11 + `REX_TIMER_WAIT_BLOCKING=1`.
- **d11p** = d11 + `timer_queue_precise_wait=true`.

| window | needs first | arms | runs | ~min | question |
|---|---|---|---|---|---|
| **W5: S4 baseline + timer modes** | S4a + §2b passed; window 4's result | base / s0 / d11 / d11t / d11p | 1 cold + 5 × 3 = 16 | ~40 | Is s0 the same as base? What does the blocking wait do alone (d11 vs d11t)? Precise vs blocking? |
| **W6: upload path** | #7's u_block; #8's memexport count from §2b step 3 (a cap only if that path runs); for C1, S4b and §21 A-D | s0 / #8 / #8 + #5 + #4 | 1 + 3 × 4 = 13 | ~33 | GPU Cmds ms/f and the slowest frames. If C1 is a no-go: s0 vs #8, ABBAAB × 2 (13 runs, ~33 min) |
| **W7: submission** | S4b with #18/#20; #19 rated and soaked | s0 / #18 / #18 + #19 / #18 + #19 + #20 | 1 + 4 × 4 = 17 | ~43 | GPU Cmds and fps. #18 alone should tie (§17 cond 6) |
| **W8a: native shaders** | native S4a | native3d / n-S4a with #2 ON (or the #1 pack) | ABBAAB × 2 + 1 = 13 | ~33 | render-thread ms/f and fps on native |
| **W8b: native threading** | #21 rated and built. #22's functional runs were inconclusive (the slow state), so W8b needs a reference arm and busy < 0.97 (a7 "Task #33") | n0 / the best threaded mode / threaded + #21 | 1 + 3 × 4 = 13 | ~33 | the threaded modes' slowest frames with and without #21 (replaces #3) |
| **W9: render busy-wait** (devoff only: #24 is Xenos-only) | #24 built and reviewed; its P1 run and the Q = 250 functional pair done (a9 S5.2.4 steps 1-2) | hook off / Q = 0 / 125 / 250 / 500 µs | 1 + 5 × 3 = 16 | ~40 | process and render-thread CPU, GPU Cmds busy/blocked, fps and the slowest frames. Pick the largest CPU drop with no loss in p99 or the 1% low beyond the run-to-run spread; if every Q loses, go to #25. A6's loaded-machine arm is separate and functional |
| **W10: codegen** | the #26 build; A10's diff review | s0 / #26 | ABBAAB × 2 + 1 = 13 | ~33 | CPU and fps |

Options already defined in F (L26-33):
- #17, the upload matrix x5 (~23-28 min);
- #3, the native threaded matrix (~30 min);
- the attract benchmark (~42-45 min at 3 runs each). It needs a quiet machine, so it depends on §4a Q3;
- native3d vs nativeB (to be planned).

## 3. Build time and disk (Agent 2, 07:08; estimates only, ±30%, nothing built)

| batch | contents | time at -j10 | disk |
|---|---|---|---|
| **First batch without an `xmemory.h` change** | the SDK .cpp files + gpu_native files + 1 new hook TU | **~6-10 min**: SDK ~2 + devoff ~1.5-2 (no game compile edges: relink only) + native ~2-3 (7 TUs + the hook TU), including apply, MANIFESTs and gates | ~0.56 GiB (two bins built in place) |
| **The same with `xmemory.h` changed (C1)** | as above | **~37-46 min**: SDK ~5-6 + devoff ~15-19 + native ~17-21 (a full rebuild of both game trees) | the same |
| **#1 AOT pack** | A4's s35 `runtime-cache.cpp` + merged index (both fingerprint inputs) | bundled into the native build: **< +1 min**; as its own bin: ~2-3 min. Plus ~10-15 min of prep to copy it in from build/agent4 | bundled < 1 MB; own bin +~364 MiB |
| **#26 db16cyc regen** | codegen tool (< 1 min) + regen (~130 s) + gen-check (~61 s) + rebuild | ~2-4 min per bin if few TUs have a site (unverified); worst case ~35-45 min; **+3-4 min if bundled with an `xmemory.h` batch** | own snapshot ~4.2 GiB; in place: bins only (+0.47 GiB if the regen output is kept for a diff) |
| **Clone the S3d trees first** (optional) | | 2-4 min of copying | +4.2 GiB |

- Free disk: **241.45 GiB** on C: (07:02). One bin dir: devoff ~214 MiB, native ~364 MiB. Everything above together stays under ~10 GiB.
- A new hook TU goes beside the other TUs (+0-5 s). A TOML hook or override would be a regen.
- Sources: `perf-notes/agent2-baseline.md` L333-406; `build/agent2/s4-estimate.py` and `s4-estimate.txt`.

## 4. Open questions

### 4a. For the user

1. **Toy Pad tags** (F Q1). May Agent 3 use generated virtual Toy Pad tags (Batman, Gandalf, Wyldstyle) in its hidden-desktop test runs?
   - Saves stay in the run folder.
   - S4 impact: C1 can't be turned on without a verify-mode level load (b2r §21 A). Without figures, or you at the controls, runs reach only the title screen and the menus.
   - Until you answer: no.
2. **simde** (F Q2). Should the small `thirdparty/simde` edit (a Windows Clang fix) be committed as a patch file?
   - Backup: `build/agent1/simde-dirty-1122.diff`.
   - Until you answer, S4's commits leave it out, as S3's did.
3. **Defender / PresentMon** (F Q3). For later windows only: would you add a Windows Defender exclusion for the build folders, or turn off the NVIDIA app's PresentMon?
   - Tonight Defender used 1.8-3.7 cores with no game running (06:25-06:55), and PresentMon ~1 core.
   - S4 impact: the attract benchmark and quiet-vs-loaded comparisons need a quiet machine.
   - If both stay as they are, S4's windows stay comparable with windows 3 and 4.
   - Until you answer, nobody touches either.
4. **Screenshot check for the 4 native shaders (#1).** The pack changes the image by design: the skipped draws come back. So b2r §15.1 gates it as a content fix that needs your visual check.
   - The standard-path reference screenshot needs your visible desktop (`LEGO_GPU_SNAPSHOT_DIR`).
   - Will you do this check, and when?
   - Until then, the native option is the miss cache (#2), which changes nothing visible.
5. **No-wait mode pop-in (#33).** Would an opt-in mode be acceptable in which objects can be missing for a few frames, instead of the game freezing while shaders compile?
   - If not, #33 and #34 are dropped.

### 4b. For Agents 1, 10 and 12 (not for the user)

**Answered by Agent 1 (07:47):**
- **#37 watchdog dump delay:** staged only, not an S4 item; the 06:28 call stands. F's Leads were stale and were fixed at 07:48.
- **#7's cost when ON:** record both numbers (A10: +1-3 ms/f on GPU Cmds; A12: 0.25-0.4, at most 0.75 ms/f). It is functional-only either way, so no decision is needed.
- **#32:** it ships with a switch (OFF) unless Agent 10 rates it output-identical. Agent 10 checks this in its #34.
- **#8's memexport caveat:** an S4 gate, not a change tonight. Count the full-buffer `RangeWrittenByGpu` calls in S4a's functional run (§2b step 3). A length cap is decided in S4, and only if that path runs. The staged P2 diff stays as it is.
- **GO to stage #18 and #20:** deferred to the S4 kickoff with the user after window 4.

**Still open:**
- **Ratings still missing:** the staged C1 code (#4; the design was rated at 06:52), #6 (no code yet), #19, #21 (and the source of "one more code proof"), #24-#26, #32, #33. Rated since 07:30: #8 P2 (07:34, b2r row 23, §22) and #5 fix (i) (~07:56, b2r row 24, §23).
- **Switch names missing:** #6 and #11 (M1). #24's env vars are now named (a9 S5.2.2); #25 has no switch of its own (it replaces #24's sleep in the same file). C1's are `physical_protect_keep_watch` and `physical_protect_keep_watch_verify`.
- **Possible changes after this draft:** Agent 10's other #34 items (#24's review, #32's output-identical check, the R1/R2 summary, its check of this draft) may change the rating cells and rows 18-20; Agent 12's C1 NOTE.md (due 08:25) completes #4.

## 5. Open, but not S4 items

- **nativeB's menu exit: closed for tonight as (a), a recorded difference** (Agent 1, 07:47). nativeB leaves the front-end menu ~12 s earlier than native3d, in both orders (F 06:15); the exit follows guest CPU speed.
  - Not codegen: Agent 10's "(b) result" (07:35, codegen-review L717-769). The whole tree, 164,786 functions, has 0 sequence mismatches.
  - Not a host clock: Agent 3 (07:38-07:40, a3 §7.5). Every clock the guest can read is wall time and the same in all builds.
  - The root cause is S4 work: #41 (§1h).
- **The stuck game lock (finding 10):** v0.2.0 hits it too (F 06:48), so our changes didn't cause it. The S4 answer is #24, whose H2 hook covers the GetData loop that base1's lock owner spun in (a9 S5.2.1). #37, the watchdog dump delay, is staged only, not S4 (Agent 1).
- **Harness:**
  - **done:** "STUCK-LOCK + dump + exit 0" is now RECOVERED HANG. Agent 3 applied the patch to `harness/runstats.py` at 07:02, and its test (07:05) had 0 failures in 37 checks over 5 real runs and 14 mock cases. Exit codes don't change (a3 L650-658);
  - an optional lock-trace repro, only on A1's GO (`LEGO_TT_LOCK_TRACE`, `critical_section_stuck_seconds=30`).
- **The slow state** (E-cores at ~550 MHz in agent runs):
  - Ruled out: process-level EcoQoS / EXECUTION_SPEED (task #24, finding 7).
  - Still open: the package power limit (PL1, which #40 tests), per-thread or window-visibility QoS, and overlay/EPP.
  - A8 runs `timerq_slowstate.ps1` over W4b's fg=1 runs.

## 6. Sources (line ranges)

- **F** (`FINDINGS-AND-CHANGES.md`): 344 lines at 06:55, 345 at 07:04. From L96 on, everything moved down 1 line between those reads. Rows that cite F line numbers use the 06:55 read; most rows cite F sections instead.
  - Window-4 plan: L5-24.
  - Later options: L26-33.
  - Also used: L55, L63, L69-70, L84, L88.
  - Log 06:12-06:58: L96-106.
  - Questions: L108-111.
  - Where things stand: L113-123.
  - Leads for the next round: L128-149.
  - Findings 9-11: ~L257-278.
- **b2r** (1170 lines at 07:55; my earlier reads were up to 3 lines off):
  - Status: L9-36 (row 23, P2: L35; row 24, fix (i): L36).
  - §14 (#38): L613-655.
  - §15: L656-716 (§15.1 L667-683; §15.2 L684-699; §15.4 L706-716).
  - §16: L717-761. §17: L762-803 ((d) L799; verdict L802).
  - §18: L804-895.
  - §19: L896-931. §20: L932-971.
  - §21: L972-1056 (lock order L1041-1044; conditions A-D L1048-1052; the §19 addendum L1054).
  - §22 (P2, 07:34): L1058-1122 (verdict L1115).
  - §23 (fix (i), ~07:56): L1123-1170 (item 4 L1141-1156; verdict L1158; turning ON L1160-1166; form-2 note L1168).
- **a5** (`agent5-uploads.md`, 922 lines): S4 L670-922; S4.0 L674-680; S4.5 L749-833; S4.6 L835-849; S4.8 L861-903; x5 L915-922.
- **a12** (`agent12-io-memory.md`, 1004 lines at 07:11): RESUME L3-16; S4.4 ~L694-745; S4.8 ~L873-940; S4.9 L945-961; S4.10 L963-976; S4.11 L978-1004. Staging folders `build/agent12/s4-diag`, `s4-p2` and `s4-fixi` each have NOTE.md and HASHES.txt; `s4-c1` (07:51) has HASHES.txt and the diffs, but no NOTE.md yet (07:55).
- **a9** (`agent9-codegen.md`, 1954 lines at 07:45): S5.1, the 1b exit split, L121-217; S5.2, the merged back-off item, L219-402 (S5.2.1 L231-262; S5.2.2 L264-341; S5.2.3 L343-356; S5.2.4 L358-387; S5.2.5 L389-401). The S4 analysis (task #23) starts at L403; the line numbers I used for it at ~07:00 (S4 L89-542, S4.1.3 L234-318, S4.2.4 L428-456) have moved. Also `build/agent9/s4/fence-wait/gpu_wait_backoff.cpp.draft` (07:44) and `build/agent9/b-clock/fe-gate-flags.txt` (07:39).
- **a3** (`agent3-run-harness.md`, 702 lines at 07:37): harness fixes applied 07:02, L650-665; §7.5, the 1b exit split from the host side, L667-702.
- **a7** (`agent7-present.md`): task #26 L169-316 (§3 L268-315; S4-T1 L279-293; not proposed L299-302; metric L306-310); task #22 §4 L456-503; "Task #33" (zero-code threaded runs) from L187.
- **a6h:** §9 L205-230. **a6s:** §10 L285-419; §11 L420-468; §11.1 L469-527.
- **aot** (109 lines) and **mcr** (157 lines): whole files. Context from `agent4-draw-path.md`: L1-46 and L196-242.
- **`agent10-codegen-review.md`** (769 lines at 07:35): L1-38 has no S4 ratings; the 1b "(b) result" is L717-769.
- **Agent 2:** `perf-notes/agent2-baseline.md` L333-406.
- **a11** (`perf-notes/agent11-kernel.md`): the timer bench table (~L1525-1531, L1816) and the slow-state and #24 sections; #40's section.
