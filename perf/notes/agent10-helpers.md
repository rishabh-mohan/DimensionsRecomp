# Agent 10: guest-facing SDK hot helpers (task #9). Session 2: headers edited, see "Session 2" at the end

> **RESUME (14:45; board run 2, task #12: rating queue until 15:00; reads end ~14:50; then idle until W4b is done).** Read-only reviews, in order as items arrive. Each gets a b2r status row and a message to the owner and Agent 1. No builds, game runs or git writes; at most 2 threads. Files: b2r and helpers only (not `build/agent10/**` this task; scratch goes in the brain dir).
> - **1. Agent 2's S4a apply record:** DONE 13:42 (§29, row 30): ALL PASS, 6 rows, 72 checks (t12_s4a.py); #32 = L564 only. C1 follow-on: keep-watch.diff applies to S4a snap1 byte for byte; keep-watch-rexlego.diff is LF-only on a CRLF file, so keep CRLF (memory_watch.cpp → 70829846…). Sent ~13:42 to 2, 1.
> - **2. C1 re-check:** DONE 13:15 (§28, row 29). Sent ~13:20 to 12, 1.
> - **Side fix 13:20 (Agent 6's message):** b2r §27 "Before landing" item 2's "fixed Created ≥ unfixed" is struck (info only at default threads: +tail but 12 workers vs 10); item 4 (threads=0) is the positive control (U4 several times F4). Sent ~13:25 to 11.
> - **3. P2 fallback counter:** DONE 13:42 (§30, row 31): output-identical, SAFE, no switch; syntax PASS; commutes with s4-r1r2 (027204B5…). Sent ~13:42 to 12, 1.
> - **4. Agent 7's #18 + #20 step 1:** DONE 13:54 (§31, row 32): R1 stage 1 SAFE, conds 1-6 met (the hold order only decides which counter is charged; a failed EndSubmission's one `return false` comes before any change); ON SAFE to test. R2 step 1 SAFE; (d) holds by design. Syntax pending (A7, 13:46): when it lands, add it to §31 and row 32 and tell 7, 1. Sent ~13:54 to 7, 1.
> - **5. Agent 9's N1-N4:** DONE 13:54 (§32, row 33): fixed as asked; syntax PASS; §26 stands. Sent ~13:54 to 9, 1.
> - **6. Agent 5's M1:** DONE 13:54 (§33, row 34): SAFE at the default; ON output-identical and SAFE to test; applies only after S4a. Sent ~13:54 to 5, 1. Addendum 14:05: the head/tail sweep is already in `bench/agent5/m1_copybench.cpp` (AA313906…; RunCheck :332-362; its helper = the diff's, 31 lines), so before ON = build it, run it without `--skip-check` (exit 0), then the OFF/ON pair. M1 now follows C1. Sent ~14:10 to 5, 1.
> - **7. C1 v2 interdiff (Agent 12, 14:00):** DONE 14:10 (§34, row 35): exactly V1-V6, all re-derived, syntax PASS. SAFE at the default; gate D met; ON SAFE to test. kInitOnly works only in the overlay (FinalizeInit has no caller; the dev console can still flip both), so the test rule is launch-only sets, and Agent 12's init latch comes before default-ON or landing beyond tests. Sent ~14:10 to 12, 1, 5.
> - **4b. Agent 7's syntax + 14:01 re-stage (A7 14:05; A1 14:07):** DONE 14:13 (§31 addendum, row 32): syntax PASS (9 units, 18 compiles; dcl.cpp re-run on the final file); the nit changed 3 comment lines only; all re-derived; the p2c commute still gives 027204B5…. Confirmed for S4b: s4-r1r2.diff BD0C4A93446149BB. Sent ~14:15 to 7, 1, 2.
> - **Item 8, C1 v3 (A12, ~14:27; A1: before #26): DONE** (row 36, §35). SAFE; ON SAFE to test; my §34 latch condition is met, so S4b may take keep-watch-v3.diff DECCFE33… in place of v2 (same step, same rexlego diff). Sent ~14:45 to 12, 1, 2.
> - **Item 9, #26 `db16cyc_pause` (A9, ~14:22): DONE** (row 37, §36). Landing OFF SAFE; ON output-identical and SAFE to test, with 4 gates (toml line + new tool together; 20 in the arm's 10 TUs; keep the partition sidecar; functional pair + frame-time A/B). Sent ~14:45 to 9, 1.
> - **Next:** `@@done 12` by 15:00. No commands from 15:00; then idle until Agent 1 announces W4b is done.

> **Task #1 (12:40; board run 2 = old task #34, resumed after the 08:29-08:34 reboot): DONE, `@@done 1` sent ~12:45; superseded.** Notes and reads only; at most 2 threads; no builds, compiles, runs or git writes; no scripts or scans once Agent 1 announces window 4. Files: b2r, codegen-review, helpers, `build/agent10/**`. Inputs re-hashed 12:27-12:35: unchanged since 08:28.
> - **1. Fence-wait #24 (§26, row 27):** split into "Landing OFF needs" (a9 step 0: grants, syntax compile, batch-nolr build + map check with N2) and "Before ON needs" (steps 1-4: P1 controls, functional pair, sweep + Agent 6's arm with sleep_fail == 0), plus a Result line. Landing OFF SAFE; ON SAFE to test. The 08:28 send was lost in the reboot; re-sent ~12:45 to 9, 6, 11.
> - **2. #32 warm-boot fix (§27, row 28):** output-identical (timing only); SAFE; may ship without a switch (Agent 1's 07:48 rule). Before landing: a6 §10.2 runs 1-4. Sent ~12:45 to 11, 6.
> - **3. R1/R2 summary and row 23's path (§25 addendum 2; correction 7 fixed):** R1/R2 = Agent 7's rows 18-20, not C1's residuals. No rating change; #19 unrated. Row 23 confirmed (base `src/graphics/shared_memory.cpp` 15C89EDB… → 0BE4BADC…). Sent ~12:45 to 11.
> - **4. P2 counter (§25 addendum):** P2 ON needs Agent 12's counter (S4.12 L1128-1140), staged after window 4. **Open: rate it when staged** (`build/agent12/s4-p2/` unchanged since 07:04 at 12:35).
> - Old run (08:28), all done and sent: fix (i) §23 row 24; C1 §24 row 25; S4-DRAFT check §25 row 26. Report: `@@done 1` ~12:45. On a re-stage, re-rate only the delta: fence-wait vs D176CA8D…, C1 vs `build/agent10/s4/c1-checks.txt`, S4-DRAFT vs `build/agent10/s4/S4-DRAFT-snap1.md`.

> **RESUME (07:35; session 3, task #17: reviews part 2; task done), superseded.** Read-only, at most 2 threads (Agent 8's last run ended 07:00). No builds or game runs. Notes only from 08:30. Summary sent ~07:02. (b) done 07:35 and sent ~07:35 to 1, 3, 9; P2 §22 sent ~07:35 to 12, cc 1; `@@done 17` sent ~07:35. Next: wait for Agent 1. The fix (i) item 4 static check (heap_mutex_ sites without a preceding G) stays queued for S4.
> - **Done and sent:**
>   - nativeB: 1a static PASS (04:43); 1b route pair PASS (05:23).
>     - Tie-break verdict sent 06:19 to 1, 2, 3, 8, 9: every must-match item PASS. The front-end exit split repeated: nativeB 105.7/108.9 s vs native3d 118.9/120.5 s, first frame to exit.
>     - **Agent 1 (06:28): this is an OPEN item, not accepted. It is not a fail item and needs no rollback.** Written at the end of codegen-review.
>   - Earlier items:
>     - n-rows PASS (05:04);
>     - timerq §14 and pthrottle §16: SAFE as default-off candidates (05:23);
>     - Agent 7's top 3, §15 (04:53);
>     - R1/R2, §17 (goes in the summary only).
>   - §18 miss-cache: SAFE at the default; ON is output-identical under §15.2 1-8.
>     - The 06:18 addendum (Agent 4's 3 asks) went to 4, cc 1.
>     - Agent 1 recorded it as SAFE OFF, with no GO tonight. S4 items wait for the S4 plan with the user, and my insert-line check goes with it.
>   - §19, the PhysicalHeap::Protect race (Agent 12's S4.7): CONFIRMED, both forms. Sent 06:43 to 1, 12, 5. Addendum in §21: form 2 has no known trigger in this game.
>   - §20, Agent 12's #27 u diagnostic: SAFE OFF; ON is SAFE for functional runs. Sent 06:43 to 12, 1.
>   - §21, C1 = P1: SAFE OFF. ON is output-identical under conditions 1-4, apart from R1 and the bypass writers. Flip ON only with A-D. Sent 06:52 to 5, 12, cc 1.
> - **Done by 07:35 (open at 07:05):**
>   - **(b): done.** Result at the end of codegen-review: no codegen change found, and the item stays OPEN for S4. The notes below are the history.
>     - Tool: `fe/fediff.py ADDR...`. It reads both maps, takes each side's TU, and compares the snap1 and snapB3 bodies: a unified diff, plus a per-instruction compare with "ctx." dropped. Outputs go to `fe/out/`; each run appends to `fe/out/summary.txt`.
>     - Run 1 (06:58, `fe/run1-a9.txt`) covered Agent 9's 9 functions: front-end manager per-frame and init, page Input, request_page, page_event, main-menu A handler and AboutToShow, and the clocks sub_83FAF088 and sub_83FB2640. Seen so far: only B's mechanical rewrites (CR6 as a local with an SO=0 compare, rlwinm lowering, musttail epilogue).
>     - Next: classify every body diff automatically (rlw* checked by evaluation), then take Agent 9's full clock scan (~07:50).
>     - Agent 9 (06:57): B's locals are only CTR/XER/RESERVED/CR. GPRs stay in ctx.rN and REX_LOAD/STORE are volatile. mftb is the out-of-line Clock::QueryGuestTickCount() in both trees.
>
>     Agent 3's 06:48 timeline has no addresses. A1 response → exit INSTALL: native3d 59.6/61.3 s, nativeB 46.5/49.7, devoffB 68.5/73.8, devoff2 71.3. The CPU rate is 2.2-2.6 cores in every run. If nothing is found by 08:15, write it up as unexplained, for S4. No (c) runs.
>   - Summary written 07:05 (helpers.md "Task #17 summary") and sent to 1, cc 7. Then (b), then `@@done 17`.
>
> **RESUME (03:58, updated 05:38; session 3, task #17: reviews part 2), superseded.** Read-only, at most 2 threads, no builds or game runs, notes only from 08:30. Summary to Agent 1 by ~07:30, then `@@done 17`.
> - **1. nativeB gate.** nativeB-bin staged 04:34 (exe 01C4D5A3…, MANIFEST E5CBF30A…, fingerprint 81d1c3a7…) against `build/agent2/native3d-bin` (exe B90DF683…, fingerprint 335ff2d4…). Write-up: codegen-review "nativeB gate".
>   - a. Static: **PASS** (04:43), with Agent 9.
>     - Inputs: `nb/statecmp.py` MATCH (`--full` MATCH too); `nb/sumscheck.py` MATCH.
>     - Generated code: `nb/lrsites.py` PASS.
>     - Binaries: `nb/hookset.py` PASS (181 hooks, same set and objects). Agent 9's mapcmp: same sub_ and alias sets, .text −10.38%. fpcheck PASS (only the 13 codegen inputs differ). warncmp CHECK (2 host-only signatures from identical sources). MANIFEST 149 PASS / 0 FAIL / 34 NOTE.
>     - The fingerprint keys only `<exe dir>/cache/native-pso-recipes.bin` and the trigger-loaded pack. The harness runs from a fresh run dir, so both runs of the pair start cold (`nb/fpscan.py`).
>   - b. Route pair: **PASS (05:23).** Caveats: the placement relocation is not covered at runtime, and the front-end exit press differs (B at the 2nd B press, A ~7 s after the 3rd; run-to-run class), so I recommend a reversed-order tie-break pair. Written in codegen-review "1b. Route pair" and "1b verdict"; sent 05:23 to 1, 2, 8, 9.
>     - **Tie-break:** Agent 1 gave the GO (05:31) for the reversed-order pair (nativeB first, then native3d), run by Agent 8 after §11 (~05:50). My verdict is due within 20 min of its logs landing. Tools: logdiff, nativelines, warntypes, placescan, framepso, plus the exit press (input.csv log_lines after each B press, INSTALL batch time).
>     - A = native3d `build/agent3/runs/20261122-045945-bgate-long-native3d`; B = nativeB `…-050343-bgate-long-nativeB`.
>     - B: 54/54 steps, exit 0, 0 errors / 0 critical, no dump. logdiff NEW 0 / MORE 0 / flags 0. The 19 common warning types have equal counts. Slot heap 9/9 and pool copy 128/128 MATCH; fail lines 0.
>     - Placement relocation, A 1 / B 0: per-call and dependent on heap layout (213.56 s idle tail, 0 in 18 matrix runs). The lr site is unchanged, so this counts as not covered.
>     - The A stall (STUCK-LOCK plus watchdog dump) belongs to Agent 6 (task #25). I sent Agent 6 the mapwhere/logwin/framepso files, and at 05:38 the extras (codegen-review 1b, "Extras sent to Agent 6"): the owner's lr=82BCE244 returns from `bl 0x83FC6A58` = draw.cpp's `DrawIndexedVerticesHookQueued`, which runs inline on the serial path (PSO creation under kGraphicsLock). The 5.2 s frame lines up with the lock wait, and the 3.7 s frame after it is the minidump write. 05:46: Agent 3 and Agent 8 report the same STUCK-LOCK in OFF runs (devoffB attract-long 4 times, devoff3 warm once, cold none) on a CPU-saturated machine. So it is neither native- nor B-specific; it comes with CPU starvation. Watch item: window-4 quiet runs (codegen-review 1b, "05:46 update").
>     - New tools: `nb/placescan.py`, `nb/framepso.py`, `nb/mapwhere.py` (first run), `nb/logwin.py`, `nb/framealign.py`, `nb/genfunc.py` (v2: DEFINE_REX_FUNC, `--tu` for targeted reads), `nb/mapsym.py` (one map, hooked or guest).
> - **Rule (Agent 1, 05:31):** while a game runs (Agent 8's queue lasts until ~07:15), no recursive searches or scans over the SDK, DimensionsRecomp or build trees. Targeted reads only, at most 2 threads. Generated TUs are not in address order, so finding a guest function body needs the map's `__imp__` object first (`nb/mapsym.py`), then `nb/genfunc.py --tu N`.
> - **2. native3d n0/n2/n3 rows, with Agent 4: PASS (05:03, sent 05:04 to 1, 4, 2, 8; batch2-review §13 "After the apply").** Matrix `build/agent8/matrix/20261122-0452`. check_n_rows n2/n3 PASS; hash0 0/0/0 (native2 0/67,220/44,968); every other warning type has the same count as native2; top draws 8/0/1 and scenes 0→1→0→1→0→1→0→8 in all three. Tools: `nb/nrows.py`, new `nb/warntypes.py`. Earlier plan: Expect hash=0x0 to drop sharply in n2/n3 (native2 baselines 67,220 and 44,968), n0 unchanged (0 hash0, 66 warning/error lines), draws/frame unchanged (top values 8/0/1) and the scene sequence 0→1→0→1→0→1→0→8 (`nb/nrows-baselines.txt`, re-run 04:07 with the fixed `--run` append and boot heuristic: all 4 kept=True). Write-up goes in batch2-review §13 "After the apply". Running in Agent 8's slot since 04:52: `build/agent8/matrix/20261122-0452` (n0 `runs/0452-n0-r1`, then n2, n3; done ~04:59). The route pair follows.
> - **3. timerq:** §14 and row 15 (**SAFE**, default off). Sent 05:23 to 11, cc 1.
> - **4. Agent 7's top-3 S4 candidates:** **done** (batch2-review §15 and row 16; line sent 04:53 to 1, 7, 4).
> - **5. Agent 11's pthrottle** (`host_execution_throttling_optout`, default false; `build/agent11/pthrottle/stage/pthrottle.diff`, sha256 75756E8DCB04…, -4/+37, 7 hunks): low priority, not part of task #17. **SAFE** as a default-off candidate (batch2-review §16, row 17). Sent 05:23 to 11, cc 1. Mention it in the 07:30 summary.
> - **6. Agent 7's R1 stage 1 and R2** (Agent 1, 05:38; design level, `perf-notes/agent7-present.md` "Task #22" §4): R1 stage 1 **SAFE** as a default-off test bed under conditions 1-6 (no win alone); R2 step 1 **SAFE**, step 2 **SAFE-IF** (a)-(e). batch2-review §17 and row 18. Not sent separately; it goes in the 07:30 summary (to 1, cc 7).
>
> **RESUME (03:32, session 3, task #9: safety reviews), superseded.**
> - **Done and sent:**
>   1. Fix-a re-hash (02:17 to 1, 12, 6, 2): registry 4EC71328…, prefs 9CBE6DBF…, both = Agent 6's staged files.
>   2. Agent 12's two flips, in the same message: audio ON **SAFE** (§8) and `pause_safe_order` **SAFE** (§11).
>   3. S3 TSV (02:32 to 2, 1): `build/agent10/s3/S3-include.tsv` (A1E7C83F…, 28 INCLUDE). Agent 1 committed these inputs as game 001336f + SDK c5fe668.
>   4. OFF B-gate pass list (02:42 to 1, 3, 8, 9).
>   5. Agent 4's §S3.2 draw.cpp fix: **SAFE** (03:32 to 1, 2, 4; `agent10-batch2-review.md` §13 and row 14). After the apply, live draw.cpp must be 5EA1F357… (306,557 B, 5758 CRLF lines).
>   6. B verdict (03:32 to 1, 2, 9, 8, 3): static PASS (02:45), boot PASS (02:59), and the front-end route **PASS with partial coverage** (`agent10-codegen-review.md`, "Route level").
>      - Pair 1's `end` divergence was run-to-run variation. In the tie-break, both builds left the 220/534 screen ~19 s after the last press and played the same attract sequence.
>      - No rollback. Tools: `bgate/idlecount.py` and `bgate/framecmp.py`.
> - **Open:**
>   - Agent 11's S4 candidate `timer_queue_precise_wait` (low priority; staged in `build/agent11/timerq/stage/`, diff D07A2DC4878D…). Rate it in `agent10-batch2-review.md` §14 / row 15, then reply to 11 (cc 1). Applying it needs Agent 1's GO.
>   - If Agent 4 asks, re-hash live draw.cpp after the apply (expect 5EA1F357…).
>
> **RESUME (02:42, session 3, task #9), superseded.**
> - **Done and sent:**
>   1. Fix-a re-hash (02:17 to 1, 12, 6, 2): live registry 4EC71328… (fix-a + commit hunk), prefs 9CBE6DBF…, both = Agent 6's staged files.
>   2. Agent 12's two flips, same message: audio ON **SAFE** (§8; the diff is only line 48); `pause_safe_order` **SAFE** (§11; live rex_app.cpp 11DE333F… = the staged file).
>   3. S3 TSV (02:32 to 2, 1): `build/agent10/s3/S3-include.tsv`, sha256 A1E7C83F7CFA1372…, 28 INCLUDE / 0 EXCLUDE. The header records game 001336f + SDK c5fe668, plume e0c8871 (3 modified files) and simde 71fd833 (sse.h). Written up in `agent10-batch2-review.md` ("S3 include list"; row 10 now says #27 is live since 23:19).
>   4. OFF B-gate pass list (02:42 to 1, 3, 8, 9): the last section of `agent10-codegen-review.md`, "B game gate on devoffB (OFF build)". Tool: `build/agent10/bgate/logdiff.py`, self-test `selftest-0013-v2.txt`.
> - **Open:**
>   - B verdict. The static check passed at 02:45 (Agent 9's mapcmp; my `bgate/hookcheck.py` agrees). **Boot level PASS at 02:59** (`bgate/boot-B-0300.txt`): Agent 8's cold boot 0247-devoffB against 0013-cold-d0 (devoff2) and 0254-devoff3 gives 0 NEW, 0 GONE, 0 flags. Agent 8 sends the route run dirs at about 03:45. It needs one devoff2 run and one devoffB run on the same route (Agent 3's vpad, `-InputScript`), through Agent 8's slot, before 08:30. Then run logdiff, apply the pass list, write the verdict as a subsection of the codegen review and send it to 1, 2, 9 and 8 within 20 minutes. If the gate can't run: "boot gate only", or "verdict pending: gate not run" with Agent 1's agreement.
>   - (Done 02:41, no message needed.) The full-content scan `build/agent10/s3/scan-vs-s2-0217-full.txt` (2F10DFD4…) has the same 28 CHANGED lines as the fast scan, and every TSV row with the same live sha (`cmp-full-0242.txt`).
>   - Agent 4's §S3.2 draw.cpp fix (Agent 1, 02:47; approved in sequence at 02:46, SESSION2.md:1193-1200). Rate it when Agent 4 sends the scratch-validated patch. It's native-only, so check two things: the draws that reach the GPU don't change, and OFF builds don't compile it. Send the verdict to 1, 2 and 4. Then Agent 4 writes the live file at Agent 1's GO after native3 is staged, and Agent 2 builds native3d (S3d). Live draw.cpp before the fix: 50AA3B1D… (= S2 = S3). **Pre-checks done 02:58** (`agent10-batch2-review.md` §13, status row 14 pending): every caller is scoped, the recorder drops the same draws at 2713 with the same snapshot, the serial paths aren't reached, and OFF doesn't compile draw.cpp (CMake 61-141; snap1-off/snapB-off have no draw.cpp.obj). Left for the patch: diff and hash, then Agent 4's test results.
>   - Then `@@done 9`.
> - At 02:37 devoffB-bin wasn't staged yet (Agent 2's `snapB-game-build.log` was still growing).
>
> **RESUME (01:28, session 2 run 3; pause for the agy-grid relaunch), superseded.**
> - **Window 3 is over** (Agent 1, 01:16-01:20: 19/19 OK). Pause: no builds, no game runs, no new work until the relaunch. My state line went to Agent 1 with the 01:28 reply.
> - **Fix A and the ODR analysis are rated** in `agent10-batch2-review.md` §12; replies went to Agents 7 and 1 at 01:28.
>   - fix-a.patch: SAFE. Hunks 1 and 2 are inseparable.
>   - fix-a-commit.patch: SAFE and recommended.
>   - Agent 7's one-line alternative: NOT SAFE, because Restore defaults fails.
>   - (b): AGREE, plus S4 hazards 6 and 7 and a grep guard.
>   - Evidence: `build/agent10/review/r6/odr_fixa_checks.ps1` and its log; scratch copies in `r6/fixa/{a,ac,c}`.
>   - Agent 1 had already chosen (a). Agent 6 applies it at Agent 1's GO after the relaunch.
> - **After the relaunch, in order** (RESTART-PROMPT-S3.md E and F):
>   1. Re-hash the live settings files once Agent 6 applies fix-a. Expected: registry 8BA19C5F… (4EC71328… with hunk 3) and prefs 9CBE6DBF…; pristine values are A3733700… and C78112AA….
>   2. (D) Rate Agent 12's two flips:
>      - the `audio_shutdown_detach_worker` ON one-liner against §8;
>      - `pause_safe_order` against §11 (`safeorder_stage.ps1 -Check`, staged 11DE333F…).
>   3. Write the S3 file list (TSV) for Agent 2.
>   4. Give the B game-gate verdict (route: the last section of `agent10-codegen-review.md`).
> - Nothing is running. No DimensionsRecomp edits since the #9 headers (18:50).
>
> **RESUME (00:12, session 2 run 3), superseded.**
> - **Sent with the 00:12 reply:** (A) `batch-nolr` confirmed to Agents 1, 9 and 2; (B) the B game gate proposal to Agent 1; (C) `pause_safe_order` default ON rated SAFE to Agents 11 and 1.
>   - (A): Review 4 condition 1 is met (`agent10-codegen-review.md`, log row 00:00-00:08). Tools: `build/agent10/review/r5/lrdiff.py` (scan, compare) and `verify_sums.py`. Pickles: `r5/A-2328.pkl` (the 23:28 tree; copy in `r5/batch-2328`), `r5/off4.pkl`, `r5/B-nolr.pkl`. Report: `r5/lrdiff-report.txt`. Row 21 now also lists Agent 9's finds, `native_slot_growth.cpp:63, 76` and `settings_native_hooks.cpp:174`.
>   - (B): the section "B native game gate: proposal" at the end of `agent10-codegen-review.md`.
>   - (C): `agent10-batch2-review.md` §11. Agent 12 lands it after window 3 (`safeorder_stage.ps1 -Apply`).
> - **Pending (D):** #22 `audio_shutdown_detach_worker` ON. The §8 condition is met (noted at 00:08). Confirm the ON rating when Agent 12 sends the one-line diff after window 3.
> - **Limits:** quiet window 3 runs from 00:10 until Agent 1's end message (~01:00-01:15): read files and edit notes only. After it: only Agent 2 builds, I use at most 2 threads, and compile checks go only through `env/compile-one.ps1`.
> - No DimensionsRecomp edits since the #9 headers (18:50); none planned.
>
> **RESUME (23:46, session 2 run 3), superseded.**
> - **Task #15 (codegen cross-review of Agent 9): Review 4 is written** at the end of `perf-notes/agent10-codegen-review.md` (log row 23:13-23:40). `@@done 15` and one-line verdicts to Agents 9, 1 and 2 go out with the ~23:48 reply.
>   - Rows 17-20 (flush-mode elision, the skip_lr LR-user rule, test infra and fixture D, the inert-key removal): SAFE at the default (byte-identical) and SAFE when ON.
>   - **Row 21: `skip_lr` is UNSAFE for LEGO.** Host code reads `ctx.lr` to identify the caller, and under skip_lr guest code no longer writes it:
>     - the gpu_native `sub_83FC49E8` hook drains pool copies only when `ctx.lr == 0x83F9B660` (`hooks_buffer.cpp:388-389` → `:268-276`);
>     - XexGetProcedureAddress picks the thunk module from `ctx.lr` (`xboxkrnl_modules.cpp:155-177`; 3 LEGO call sites).
>     - The guest side is clean (`build/agent10/review/r4/skiplr-scan-off3.txt`, `skiplr-scan2.txt`); Agent 9's `build/agent9/diff/batch/lrscan.tsv` agrees.
>   - **Follow-up:** check that `build/agent9/configs/batch.toml` loses skip_lr (B2727250…, line 26 `skip_lr = true` at 23:45) and that the batch output is regenerated before Agent 2 builds B (`build/agent2/snapB`). If not, ping Agent 1.
>   - The diff was unchanged at 23:45: `agent9-chk4.patch` EB42B92C…, `agent9-chk4-tests.patch` 3EB43EAB….
> - **Task #25:** done at 22:44. The #27 exit fix is now applied live and verified. When Agent 12's 1000-run replica numbers arrive, note them in `agent10-batch2-review.md` §8.
> - **Limits:**
>   - Quiet window 2 ended at 23:09. Only Agent 2 builds. I use at most 2 threads, and compile checks go only through `env/compile-one.ps1`.
>   - **Quiet window 3** runs from 00:15 to about 01:00-01:15. Heavy work must finish or pause by 00:10; during the window, read and edit only.
> - No DimensionsRecomp edits since the #9 headers (18:50); none planned.
>
> **RESUME (22:44, session 2 run 3), superseded.**
> - **Task #25 (batch-2 review): DONE.** `@@done 25` was sent at 22:44. The table is `perf-notes/agent10-batch2-review.md`: items 1-10 are rated, and the diffs are in `build/agent10/b3/`.
>   - Item 7, Agent 6's #26 plume patch: SAFE, sent 22:33.
>   - Item 10, Agent 11's #27 exit fix: SAFE, sent 22:44 to 1 and 11. It is staged in `build/agent11/exitfix/` and is not live; it lands in batch 3 after S2 and after Agent 11's post-window checks.
>   - The S2 include list `build/agent10/b3/S2-include.tsv` (E1FF0497…) went to Agents 2 and 1 at 22:33. It takes 19 files and keeps Agent 9's 20 codegen files at S1 (Agent 1 agreed at 22:34).
>   - Follow-ups:
>     - When Agent 12's 1000-run replica numbers arrive, note them in §8. NEW with 0 HUNG and 0 CRASHED means ON can be the batch-3 default.
>     - If Agent 11 changes the staged #27 files, re-hash them against `HASHES.txt` and re-diff.
> - **Task #15 (open):** Review 3 is sent. B (flush-mode elision) is in progress: the codegen files changed at 22:12-22:13, while `agent9-codegen.md` is still at 21:28:45.
>   - The current diff is `build/agent10/review/agent9-now.patch` (EB42B92C…). `agent9-2137.patch` is UTF-16, so compare decoded text.
>   - Do Review 4 when Agent 9 marks B final; it feeds the separate codegen-option build. Then send `@@done 15`.
> - **Quiet window 2:** the matrix runs from 22:32 until about 23:20, so read and edit only. After it, only Agent 2 builds; I use at most 2 threads, with compile checks only through `env/compile-one.ps1`.
> - No DimensionsRecomp edits since the #9 headers (18:50); none planned.
>
> **RESUME (22:15, session 2 run 3), superseded.**
> - **Task #25 (batch-2 review, rolling, read-only):** the table is `perf-notes/agent10-batch2-review.md`, with diffs vs snap1 in `build/agent10/b3/`.
>   - Sent: items 1-6 at 21:48 (Agent 7 #20: 4 SAFE; Agent 6's async PSO SAFE at the default, and SAFE ON since 21:59; the pipeline_snapshot.h comment SAFE).
>   - Sent at 22:15: item 8 (Agent 12's #22: SAFE at the default OFF, SAFE-IF ON; flip the default in batch 3 after Agent 12's post-window replica) and item 9 (Agent 5's batch 2 with Agent 4's (a): SAFE at the default, legacy ON SAFE, staging pool ON SAFE-IF).
>   - Pending: item 7 (Agent 6's `prepare_plume.py` patch; still snap1 CED19F81 at 22:05) and item 10 (Agent 11's batch-3 exit fix, not sent yet).
>   - The one-line cleared/pending list by owner goes to Agent 1 by 22:40 (timer task-830). Send `@@done 25` when 7 and 10 are done, or when Agent 1 drops them.
> - **Task #15 (open):** Review 3 is sent. B (flush-mode elision) has no change since the 21:38 snapshot (`agent9-2137.patch` E839FB36…; builders 21:29-21:30, flush_mode.h 21:25). Do Review 4 when Agent 9 marks B final, then `@@done 15`.
> - **Quiet window 2 from ~21:56** (the user's timing matrix, until ~22:45; Agent 1 announces the end): no compiles, tests, benches, codegen or game launches. S2 is cut at the window's end.
> - No DimensionsRecomp edits since the #9 headers (18:50); none planned.
>
> **RESUME (21:48, session 2 run 3), superseded.** Items 1-6 sent; 7-9 pending; #15 Review 3 sent.
>
> **RESUME (20:25, session 2 run 2), superseded.**
> - **Task #9:** DONE and accepted (in the 20:15 batch). SDK header edits: `include/rex/ppc/intrinsics.h`, `include/rex/math.h`. No further SDK edits. Agent 1 deferred notes 3-4 (PPCContext memset, GetFunction mutex) to the first profile.
> - **Task #18 (batch-1 safety review):** DONE and accepted: 0 UNSAFE, 1 SAFE-IF (cheat FreezeMain). The table is in `perf-notes/agent10-batch1-review.md`.
> - **Task #21 (native-only always-on review):** DONE and accepted at 20:26 (24 SAFE). Verdicts are in `perf-notes/agent10-native-review.md`.
> - **Next review (Agent 1, 20:26): Agent 12's #22 audio-shutdown fix.** Start once Agent 12 lists it for batch 2. It goes always-on only if I rate it SAFE.
>   - Check 1: the normal path, where the worker exits within `kWorkerShutdownTimeout` (500 ms), is unchanged.
>   - Check 2: nothing is freed under a worker that is still running. The frees to watch are `worker_thread_.reset()` and `DestroyDriver` plus `SystemHeapFree` in `AudioSystem::Shutdown` (audio_system.cpp:214, :217-227), then `audio_system_.reset()` (runtime.cpp:301), `kernel_state_.reset()` (:307) and `memory_.reset()` (:317).
>   - State at 20:27: audio_system.cpp is still the baseline version (11:04:43, 394 lines).
>   - Baseline facts:
>     - The worker's `WaitAny` times out at 500 ms, and an idle pass then sleeps another 500 ms (L109-110, L166-169). So a normal exit can take up to about 500 ms, which races the 500 ms timeout.
>     - If Shutdown arrives while audio is paused, the worker is blocked on `resume_event_` with no timeout (L124-127). `shutdown_event_` never wakes it, so baseline always terminates it in that case.
> - **Task #15 (open):** the 20:46 re-snapshot `agent9-2046.patch` is identical to 20:21/19:44/19:13 (SHA F1A74D4E…). There are no untracked changes after 20:21, and agent9-codegen.md was last written at 18:21. Agent 1 (20:26) says #15 stays open until Agent 9 resurfaces. Re-snapshot every ~25 min. Send `@@done 15` once Agent 9 says the session's codegen changes are final. Edits after S1 (20:41:57, which is the 20:15 state) are batch 2.
> - **Rules from 19:5x:** Agent 2 snapshots S1 at 20:15:00, and any edit after that is batch 2. Agent-launched game runs are functional checks only (hidden desktop). Timing runs go to Agent 8's runner (specs by 20:20; I have none).
> - **20:38 freeze (Agent 1), lifted at 20:45 (Agent 2):** S1 was taken at 20:41:57 and is the 20:15 batch-1 state, since no DimensionsRecomp edits were found after 20:15:00. Editing the live tree is allowed again, and later edits are batch 2. My last DimensionsRecomp edits are the #9 headers (intrinsics.h 18:50:40, math.h 18:50:48). I have none pending.
> - The session-1 text, from "Status: no source edits" down to "Didn't get to read", is historical.
>
> **RESUME (19:07, session 2 run 2), superseded.**
> - **Task #9:** the SDK header edits are DONE: `include/rex/ppc/intrinsics.h` and `include/rex/math.h` (see "Session 2" below). Tests PASS at all four configs: v3, v2 and v3noavx2 (full, `build/agent10/test-post.log`) and portable (quick, `build/agent10/test-post-portable.log`, 19:05, after two bench-only fixes in `old_intrinsics.h` and `variants.h`).
>   - Running/next: the after bench (`build/agent10/bench-post.log`), then the compile check of a real generated TU against the edited headers (overlay include dir, `build/agent10/recomp61-H.txt`), then the session-2 section and the 20:15 batch listing for Agent 1.
>   - Do NOT re-install into build/sdk/install (pristine baseline). Pause everything in Agent 1's quiet windows (first about 20:15-20:45).
> - **Task #15:** the 18:31 review is in `perf-notes/agent10-codegen-review.md`. New snapshots: `build/agent10/review/agent9-1855.patch` and `agent9-1859.patch` (delta in `delta-1855-1859.txt`); `rotate_mask.h` is untracked, read it separately. Next: append the review of the 8 new option keys, rlwinm lowering, the vmx fallbacks, musttail and the handoff-error/non_argument checks, then send one-line summaries to Agents 9 and 1.
>
> **RESUME (18:35, session 2 run 2), superseded.**
> - **Task #9:** the bench files are written: `bench/agent10/{ppc_ref.h, variants.h, impls.h, kat.h, test_intrinsics.cpp, bench_intrinsics.cpp, build.ps1}`.
>   - `build.ps1 -Test -Quick -Configs v3` passed at 18:29: old, sdk, cand and alt all match the scalar PPC reference, and the KAT replay passes (240 runs).
>   - The full v3 test (2^32 cases) is running.
>   - Still to do: the baseline bench (`-Bench`), then the `intrinsics.h` and `math.h` edits, then all configs, the after bench and the session-2 section. **No SDK header has been edited yet.**
> - **Task #15:** first review is done at 18:31, `perf-notes/agent10-codegen-review.md` (the verdicts are mine; the subagent's draft holds the evidence). Summaries went to Agents 9 and 1. Next: re-snapshot Agent 9's diff with `git -C DimensionsRecomp/rexglue-sdk diff -- include/rex/codegen src/codegen` and compare it with `build/agent10/review/agent9-1811.patch`.
>
> **RESUME (paused 16:53 for the agy-grid restart).**
> - **Task #9 done so far:** designs are final, see `bench/agent10/DESIGN-notes.md`. `bench/agent10/old_intrinsics.h` holds a verbatim copy of `intrinsics.h` at 2897c31 in namespace `old_ppc`. **No SDK header has been edited yet**, so there is nothing half-applied. Nothing is running.
> - **Task #9 next:** write the `bench/agent10/{ppc_ref.h, impls.h, variants.h, test_intrinsics.cpp, test_math.cpp, bench_intrinsics.cpp, asm_probe.cpp, build.ps1}` files, then run `. .\env\devshell.ps1; powershell -NoProfile -File bench\agent10\build.ps1 -Test -Quick -Configs v3` and the baseline bench. Only after that, edit `intrinsics.h` and `math.h`.
> - **Task #15 (codegen cross-review):** acknowledged, not started. A review subagent was launched and stopped within a minute, with no output. Agent 9's diff snapshot is in `build/agent10/review/agent9-1650.patch`.

Status: no source edits, no builds. The toolchain wasn't ready and Agent 1 stopped the plan at 12:24.
Every cycle and µop figure below is an **estimate from reading the code**. None has been measured yet.
SDK = `DimensionsRecomp/rexglue-sdk`. Line numbers are at pin 2897c31.

## How the generated code uses these headers (evidence)
Emission-site counts come from grepping `src/codegen`:
- `CRRegister::compare(...)`: 63 sites (every cmp* and every record-form `.`). `setFromMask`: 13. `emit_set_flush_mode`: 77.
- `rex::ppc::simde_mm_*` helpers:
  - vctsxs and vctuxs: 6 each.
  - var-shift epi8/epi16 via `emit_vec_var_shift` (context.cpp:509): 4.
  - avg_epi*: 3. cvtepu32_ps_: 2. cmpgt_epu*: 2.
  - perm_epi8_, vslo, vsro, vsl, vsr, adds_epu32: 1 each.
  - The VectorMask*/VectorShiftTable* tables: 6 (memory.cpp:551-651, lvlx/lvrx/stvlx/stvrx/lvsl/lvsr).
- Generated code does **not** reference math.h, bit.h, vec128.h, `memory/utils.h` or the rex::lzcnt/tzcnt helpers. Codegen emits `__builtin_*` directly. `load_and_swap` is only used by the codegen tool. These headers are therefore off the guest hot path.
- `emit_vec_var_shift` masks the counts before calling the helper (context.cpp:517: `and` with 0xF for epi16, 0x7 for epi8). That makes exact SSE2/SSSE3/SSE4.1 forms possible (see #4).

## Ranked opportunities (expected win × frequency × confidence)

### 1. `simde_mm_vslo` / `simde_mm_vsro`: drop the memory round trip (high confidence)
- **Where:** [intrinsics.h:283-339](<workspace>/DimensionsRecomp/rexglue-sdk/include/rex/ppc/intrinsics.h#L283-L339)
- **What's slow:** the x86 path is:
  1. a 16 B store;
  2. a 16 B memset;
  3. a variable-length `memcpy(dst + n, src, 16 - n)`. The length isn't constant, so this is a libc call or a branchy inline expansion;
  4. a 16 B reload of bytes written by narrower stores. That reload is a store-forwarding failure, roughly 12-16 cycles on Golden Cove.

  There are also two branches. `shift_bytes >= 16` is dead code because the value is already masked with `& 0xF`.
- **Change:** one branch-free `pshufb` from a sliding 48-byte window. It's portable, because simde maps `shuffle_epi8` to `vqtbl1q` on ARM, so it can replace both `#if` arms.
  ```cpp
  // 0x80 lanes give zero. vslo reads the window at 16-n, vsro at 16+n.
  alignas(16) inline const uint8_t VectorOctetShiftTable[48] = {
      0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,
      0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,
      0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80,0x80};
  inline simde__m128i simde_mm_vslo(simde__m128i a, simde__m128i b) {
    int n = (simde_mm_extract_epi8(b, 0) >> 3) & 0xF;
    return simde_mm_shuffle_epi8(a, simde_mm_loadu_si128((const simde__m128i*)&VectorOctetShiftTable[16 - n]));
  }
  inline simde__m128i simde_mm_vsro(simde__m128i a, simde__m128i b) {
    int n = (simde_mm_extract_epi8(b, 0) >> 3) & 0xF;
    return simde_mm_shuffle_epi8(a, simde_mm_loadu_si128((const simde__m128i*)&VectorOctetShiftTable[16 + n]));
  }
  ```
  Proof sketch:
  - vslo, lane i, index `T[16-n+i]`: for i<n it's 0x80, giving 0. Otherwise it's i-n, giving `a[i-n]`. This matches `memcpy(dst+n, src, 16-n)`.
  - vsro, lane i, index `T[16+n+i]`: it's n+i while n+i<16, otherwise 0x80. This matches `memcpy(dst, src+n, 16-n)`.
- **Expected:** about 30+ cycles down to about 6 (pextrb, shr/and, movdqu, pshufb). Signatures are unchanged.
- **Risk:** low. It's a pure function and the result is bit-exact by construction.
- **Verify:** a unit test that compares against the old body (copied in as `ref_vslo/ref_vsro`). Use all 256 values of b's byte 0 (all n, plus junk bits) against 10k random `a` vectors and an `a` of 0..15. Then a microbench with dependent chains and random n, taking the median of 5 runs. Also run the PPC asm tests for vslo/vsro if any exist.

### 2. `simde_mm_perm_epi8_` (vperm): one fewer µop on the critical path (high confidence)
- **Where:** [intrinsics.h:159-164](<workspace>/DimensionsRecomp/rexglue-sdk/include/rex/ppc/intrinsics.h#L159-L164)
- **What's slow:** `sub(0xF, and(c, 0xF))` is two ops. For 4-bit x, `15 - x == ~x & 15`.
- **Change:**
  ```diff
  -  simde__m128i e = simde_mm_sub_epi8(d, simde_mm_and_si128(c, d));
  +  simde__m128i e = simde_mm_andnot_si128(c, d);  // 15 - (c & 15) == ~c & 15
  ```
- **Expected:** about 1 cycle out of roughly 5-6 per vperm. vperm is common in VMX128 code (swizzles, unaligned load merges).
- **Risk:** essentially none. pshufb only reads bit 7 and bits 0-3, and the new index has bit 7 clear, as the old one did.
- **Verify:** test all 256 control-byte values in every lane against random a/b, comparing with the old body. Then diff the asm: `pand+psubb` should become `pandn`.

### 3. VectorMask/VectorShiftTable tables: make them `alignas(16) inline const` (high confidence, small win)
- **Where:** [intrinsics.h:39, 58, 77, 96](<workspace>/DimensionsRecomp/rexglue-sdk/include/rex/ppc/intrinsics.h#L39-L115). Today they're declared `inline uint8_t VectorMaskL[] = {...}`.
- **What's slow / fragile:** codegen emits **aligned** `simde_mm_load_si128((simde__m128i*)&VectorMaskL[(x & 0xF) * 16])` (memory.cpp:551-651). The arrays are mutable, so they can't go into .rdata, and the optimizer can't fold constant-index loads such as `VectorMaskL` row 0 (memory.cpp:551/651). The 16 B alignment currently depends on clang's x86-64 large-array rule; nothing in the source guarantees it.
- **Change:** `alignas(16) inline const uint8_t VectorMaskL[] = {...};` (the same for all 4). Emitted C-style casts still compile because they cast away const, so codegen needs no change. Tell Agent 9 first: no signature change, but emitted code references these symbols.
- **Risk:** very low. Generated TUs need a full rebuild.
- **Verify:** compile one generated TU with compile-one, check the object for .rdata placement, and run the lvlx/lvrx/stvlx/stvrx/lvsl/lvsr asm tests.

### 4. Variable element shifts: stop going through emulated AVX2 32-bit shifts (medium confidence, rare ops)
- **Where:** [intrinsics.h:341-393](<workspace>/DimensionsRecomp/rexglue-sdk/include/rex/ppc/intrinsics.h#L341-L393) (`sllv_epi16`, `srlv_epi16`, `srav_epi16`, `sllv_epi8`).
- **What's slow:**
  - Each epi16 helper widens with 4 unpacks, calls `simde_mm_{sllv,srlv,srav}_epi32` twice, masks, and packs.
  - Those calls need AVX2. At the x86-64-v2 baseline simde uses its portable path. LLVM lowers shl to the pmulld/float-exponent trick and srl/sra to 4 splat shifts plus blends. That's about 25-40 µops per helper.
  - `sllv_epi8` nests two `sllv_epi16` calls, so it's probably 60+ µops.
- **Change:** counts are already in range (see the evidence section), so:
  ```cpp
  // sllv_epi16: a * (1 << c). The 0x8000 OR makes pshufb zero the high byte.
  simde__m128i idx = simde_mm_or_si128(count, simde_mm_set1_epi16((short)0x8000));
  simde__m128i lo = simde_mm_setr_epi8(1,2,4,8,16,32,64,(char)128,0,0,0,0,0,0,0,0);
  simde__m128i hi = simde_mm_setr_epi8(0,0,0,0,0,0,0,0,1,2,4,8,16,32,64,(char)128);
  simde__m128i pow2 = simde_mm_or_si128(simde_mm_shuffle_epi8(lo, idx),
                                        simde_mm_slli_epi16(simde_mm_shuffle_epi8(hi, idx), 8));
  return simde_mm_mullo_epi16(a, pow2);          // == (a << c) & 0xFFFF, the old result
  ```
  - `srlv_epi16`: `mulhi_epu16(a, 2^(16-c))` from the same lookup, blended back to `a` where c==0. Or use a 4-step blend ladder (psrlw 8/4/2/1 + pblendvb, with lane masks from `srai_epi16(slli_epi16(c, 15-k), 15)`).
  - `srav_epi16 = srlv_epi16(a ^ s, c) ^ s` with `s = srai_epi16(a, 15)`.
  - `sllv_epi8` (c is 0..7): use a 3-step ladder:
    1. `blendv(x, slli_epi16(x,4) & 0xF0, c<<5)`;
    2. the same with 2 / 0xFC / c<<6;
    3. `blendv(x, add_epi8(x,x), c<<7)`.
- **Expected:** about 6-16 µops instead of 25-60+. The ops behind these helpers (vslb/vslh/vsrh/vsrah) are rare in game code, so the overall win is small.
- **Risk:** medium. The equivalence has to hold for every lane value and count. It's only correct because the caller masks the counts, so add a comment saying so.
- **Verify:** exhaustive tests against the old bodies. For epi16 that's 65536 values × 16 counts; for epi8, 256 × 8. Microbench, median of 5. Agent 9 needs to keep the count masking in `emit_vec_var_shift`.

### 5. `simde_mm_vctuxs`: remove redundant masks (medium confidence)
- **Where:** [intrinsics.h:193-223](<workspace>/DimensionsRecomp/rexglue-sdk/include/rex/ppc/intrinsics.h#L193-L223)
- **What's slow:** about 20 ops. `max_ps(src, 0)` already returns +0 for NaN (maxps returns its 2nd operand) and for negative inputs. That makes the `cmpunord` and `cmplt` masks and their two `andnot`s redundant, about 4 ops.
- **Risk:** low on x86. On ARM it's only valid if simde keeps x86 NaN semantics, i.e. `SIMDE_FAST_NANS` and `SIMDE_FAST_MATH` are not defined. I didn't check the SDK's simde flags.
- **Verify:** sweep all 2^32 float bit patterns against the old body (a few seconds), and run the vctuxs/vcfpuxws128 asm tests.

### 6. `simde_mm_vsl`: branch-free x86 path (low win, 1 site)
- **Where:** [intrinsics.h:234-245](<workspace>/DimensionsRecomp/rexglue-sdk/include/rex/ppc/intrinsics.h#L234-L245)
- **Change:** `if (shift == 0)` isn't needed (psrlq by 64 gives 0), and the count can stay in an XMM register:
  ```cpp
  simde__m128i n = simde_mm_and_si128(simde_mm_srli_si128(b, 15), simde_mm_cvtsi32_si128(7));
  simde__m128i carry = simde_mm_srl_epi64(simde_mm_slli_si128(a, 8), simde_mm_sub_epi64(simde_mm_cvtsi32_si128(64), n));
  return simde_mm_or_si128(simde_mm_sll_epi64(a, n), carry);
  ```
- **Note (not perf):** vsl reads x86 byte 15 (PPC byte 0), while vslo/vsro read x86 byte 0 (PPC byte 15, matching the ISA's vB[121:124]). The ISA leaves vsl undefined unless every byte of vB is equal, so the two only differ for non-conforming input. Keep the current behaviour.
- **Verify:** test all 256 b-byte values against random a, comparing with the old body.

### 7. `CRRegister::compare` (hottest by site count). Measure first; probably leave it alone
- **Where:** [context.h:88-101](<workspace>/DimensionsRecomp/rexglue-sdk/include/rex/ppc/context.h#L88-L101)
- **Integer form:** cmp + 3 setcc + 4 byte stores + a load of xer.so.
  - When CR is a local (REX_CONFIG_CR_AS_LOCAL), clang folds setcc into jcc and drops the dead fields, so it's already optimal.
  - When CR lives in `ctx`, the 4 byte stores survive across calls. One candidate is a single packed 32-bit store (`lt | gt<<8 | eq<<16 | so<<24` via memcpy), but the shifts and ORs may cost more than they save, and it may block SROA/branch folding in the local case.
- **Double form:** `!un && (l<r)` is already folded by LLVM to `fcmp olt`, so source changes gain nothing.
- **Recommendation:** no change without asm and bench evidence. The real lever is the codegen config (CR/XER as locals), which belongs to Agent 9.

### Not worth doing (rejected, with reasons)
- **FPSCR `enableFlushMode` / `disableFlushMode`** (context.h:190-202): already cached in `csr` with `[[unlikely]]`. The cost is `ldmxcsr` on real transitions, which only codegen can reduce (see A below).
- **`cvtepu32_ps_`** (147-156): a hi/lo split would be about as short. Bit-exactness under non-RN rounding modes would need proof, and there are only 2 sites.
- **`vctsxs`, `avg_epi*`, `cmpgt_epu*`, `adds_epu32`, `vsr`:** already minimal SSE4.1 sequences.
- **`GuestToHostFunction` zero-init `PPCContext newCtx{}`** ([function.h:464](<workspace>/DimensionsRecomp/rexglue-sdk/include/rex/ppc/function.h#L464)): it memsets about 2.6 KB (128 VRs) per host→guest call. Skipping it means guest prologues read indeterminate values (UB/MSan noise). Only worth revisiting if a profile shows hot kernel callbacks.
- **`FunctionDispatcher::GetFunction`** ([function_dispatcher.cpp:323](<workspace>/DimensionsRecomp/rexglue-sdk/src/system/function_dispatcher.cpp#L323)): recursive_mutex + unordered_map, but only on the indirect-call fallback (the fast path is the REX_LOOKUP_FUNC table). Count calls first. If it's hot, check the guest function table before taking the lock, or use a `shared_mutex`.
- **`ExecuteTrap`** (function_dispatcher.cpp:175-185) copies the whole context twice, but traps are rare.
- **`SaveNonVolatiles` / `RestoreNonVolatiles`** and **stack.h `stack_push` bounds checks:** runtime-only, not emitted.

## Follow-ups for other owners (likely bigger wins; need the game, a profiler or codegen)
- **A. (Agent 9, probably the largest)** Elide redundant `REX_SET_FLUSH_MODE` (77 emission sites). Track the flush state per block/function in codegen and emit only on scalar↔vector FP transitions. Interleaved scalar and VMX FP code currently pays `ldmxcsr` per transition. Needs a profile of mixed FP code.
- **B. (Agent 9)** The scalar loops in vector.cpp (vsrb/vsrab/vsraw/vsrw/vrlw/vsubsws/vpkuhus/vpkuwus/vpkd3d128/vupkd3d128, all marked TODO) could be SIMD. vsrw/vsraw/vrlw can use the #4 techniques.
- **C. (Agent 9)** Enable CR/XER/CTR-as-local in the codegen config if it's off; I didn't find the project config.
- **D. (Agent 9)** In `pch_h.inja`:
  - `REX_LOAD/STORE` go through `volatile` pointers, which blocks combining and CSE;
  - the `REX_PHYS_HOST_OFFSET` `>= 0xE0000000` check runs on every access on Win32;
  - `ppc_setjmp` uses a `thread_local unordered_map`;
  - `REX_CHECK_GLOBAL_LOCK` takes a mutex.
- **E. (profile)** Measure how often host→guest callbacks run (the context zeroing above) and how often the dispatcher's indirect-call fallback is hit.

## Bugs noticed (not perf, not changed)
- [math.h:63](<workspace>/DimensionsRecomp/rexglue-sdk/include/rex/math.h#L63): `clamp_float<T>` stores its intermediate in `float`, so for T=double it truncates. Fix: `T clamped_to_min`.
- [math.h:190](<workspace>/DimensionsRecomp/rexglue-sdk/include/rex/math.h#L190): `rotate_left(v, 0)` shifts by the full width, which is UB. Generated code doesn't use it.
- intrinsics.h:287/318: the `shift_bytes >= 16` branch is dead.

## Resume plan (once env/devshell.ps1 and compile-one exist)
1. Write `bench/agent10/intrinsics_bench.cpp`. It's standalone: it includes `rex/ppc/intrinsics.h` and keeps the old bodies as `ref_*`. Build it with clang `-O2 -march=x86-64-v2` into `build/agent10/`. It holds the equivalence tests and median-of-5 timings for #1, #2, #4, #5 and #6.
2. Land #1, #2 and #3 first (high confidence), then #4 and #5 behind exhaustive tests, and #6 last. Tell Agent 9 before #3. No signature changes.
3. Compile-check one generated TU and a TU including `rex/ppc.h`. Run tests/unit/ppc and the PPC asm tests for vperm, vslo/vsro, lvsl/lvsr, lvlx/lvrx and vctuxs.
4. Inspect the asm for #7 in both CR-in-ctx and CR-as-local configs before touching `compare`.

## Didn't get to read
- **SDK headers:** hook.h, hash.h, memory.h, the rest of `include/rex/memory/**` (only utils.h was read), include/rex/system/xmemory.h.
- **SDK sources:** src/kernel/crt/**, src/core/{vec128,hash}.cpp, math_msvc.cpp (math_gcc.cpp skimmed).
- **Codegen builders:** floating_point.cpp, arithmetic.cpp, logical.cpp, system.cpp, control_flow.cpp, builder_context.h (I read context.cpp, comparison.cpp, vector.cpp and helpers.h, and memory.cpp only via grep).
- **Tests and config:** tests/unit/ppc/*, tests/unit/memory/*, tests/unit/system/function_dispatcher_test.cpp, the tests/ppc/asm harness, resources/templates/test/ppc_config_h.inja, the project codegen config (which `*_AS_LOCAL` modes are on), simde config flags (`SIMDE_FAST_NANS` etc.).
- **Generated code:** none to read; `rexlego/generated` doesn't exist yet.


---

## Session 2 (19:20): the helper changes are in the SDK working tree (task #9, re-issued)

Line numbers in this section are in the edited working tree. "Pin" means 2897c31.

### Batch listing for dev build 1 (cut-off 20:15)

| Item | Value |
|---|---|
| **Edited headers** | `DimensionsRecomp/rexglue-sdk/include/rex/ppc/intrinsics.h` and `DimensionsRecomp/rexglue-sdk/include/rex/math.h` (`git diff --stat`: 2 files, +105/−169). **FLAG: both reach every generated TU through `rex/ppc.h`, so a full game rebuild is needed.** |
| Other SDK files | None. Tests and benches live in `bench/agent10/**`; logs and objects live in `build/agent10/**`. |
| Cvars, options, defaults | None. The changes are always on. Each one is proven bit-identical to the pin (see the tests below). |
| Signatures | Unchanged. The four tables become `constexpr` (const), so their mangled names change (e.g. `?VectorMaskL@ppc@rex@@3QBEB`). That's harmless given the full rebuild. |
| Codegen | Nothing to change. The emitted C-style casts `(simde__m128i*)&VectorMaskL[...]` (memory.cpp:551-651) still compile. The count masking in `emit_vec_var_shift` is no longer needed, but it's harmless, so keep it. |
| Compile checks | All four bench configs build and pass: v3, v2, v3noavx2 and portable. A real generated TU (`legodimensions_recomp.61.cpp`) also compiles at the game's exact flags against the edited headers (see below). |
| How it reaches the game | The game compiles against `build/sdk/install/include`. That tree is pristine and I didn't touch it. So these edits only take effect in dev build 1, whose SDK Agent 2 builds from the 20:15 snapshot. |

**The four configs (Agent 1's rule for intrinsics.h and math.h): all PASS, so no helper was dropped.**

| Config | Flags (plus the common set in `bench/agent10/build.ps1:27`: `-std=c++23 -O2 -ffp-model=strict -fno-strict-aliasing` ...) | Element-shift path that compiles | Result | Log |
|---|---|---|---|---|
| v3 (game baseline) | `-march=x86-64-v3` | AVX2 `#if` | **PASS**, full | `build/agent10/test-post.log` (18:51-18:57) |
| v2 | `-march=x86-64-v2` | SSE4.1 `#else` | **PASS**, full | same log |
| v3noavx2 | `-march=x86-64-v3 -mno-avx2` | SSE4.1 `#else` | **PASS**, full | same log |
| portable | `-march=x86-64-v2 -DSIMDE_NO_NATIVE` (simde's generic C, as on a non-x86 host) | SSE4.1 `#else`, via generic C | **PASS**, quick (build.ps1 always runs portable in quick mode) | `build/agent10/test-post-portable.log` (19:05) |

- **Command:** `. .\env\devshell.ps1; powershell -NoProfile -File bench\agent10\build.ps1 -Test -Math -Configs v3,v2,v3noavx2,portable -Threads 2`.
- **About the portable row in `test-post.log`:** it records a compile failure in the bench's copy of the *pin* header, not in the edited SDK header. The bench-only adaptation below fixed it, and I then re-ran portable on its own.

### Changes

| # | Where | Change | Why | Risk and evidence |
|---|---|---|---|---|
| 1 | intrinsics.h:40, 59, 78, 97 | `VectorMaskL`, `VectorMaskR`, `VectorShiftTableL` and `VectorShiftTableR` change from `inline uint8_t[]` to `alignas(16) inline constexpr uint8_t[]`. Contents unchanged. | Codegen reads them with the **aligned** `simde_mm_load_si128`. Before, their 16-B alignment came only from clang's large-array rule. Being mutable also kept them out of .rdata and blocked constant folding. | None. The tables test checks contents and alignment. llvm-nm puts them in .rdata (type `R`) in the generated TU. |
| 2 | intrinsics.h:160 `perm_epi8_` (vperm) | `e = andnot(c, set1(0xF))` replaces `sub(0xF, and(c, 0xF))`. | One fewer op on the critical path: for a 4-bit x, 15 − x == ~x & 15. | None. pshufb reads only bit 7 and bits 0-3, and bit 7 of `e` is clear in both forms. |
| 3 | intrinsics.h:195 `vctuxs` | New body: `clamped = max(src, 0)`, `high = src >= 2^31`, then `cvtt(clamped − (high & 2^31)) \| (high << 31) \| (src >= 2^32)`. The old body was about 20 ops and included cmpunord/cmplt masks. | `max_ps` already maps NaN, −0 and negatives to +0, because it returns its 2nd operand on NaN. cvtt never sees an out-of-range value, so the result doesn't depend on cvttps returning 0x80000000. | Low. Verified on all 2^32 inputs, under both the default MXCSR and FTZ\|DAZ. |
| 4 | intrinsics.h:218 `vsl` | Branch-free and portable: `n = srli_si128(b, 15) & 7`, then `insert_ps(sll_epi64(a, n), sll_epi64(slli_si128(a, 4), n), 0xE0)`. The `#if` x86/ARM arms and the `#error` are gone. | Removes the `if (shift == 0)` branch and keeps the count in an XMM register. Also, the pin didn't compile under SIMDE_NO_NATIVE because it passed a non-constant imm8 to `slli/srli_epi64`. | Low: 10.24M cases. Like the pin, it still reads the count from x86 byte 15 (see bug note 1). |
| 5 | intrinsics.h:230 `vslo`, :244 `vsro` | One pshufb with a computed index. `n` is `(b >> 3) & 0xF` from x86 byte 0, broadcast. The vslo index is `iota − n`: negative lanes have bit 7 set, so pshufb writes 0. The vsro index is `(0x70 + i) + n`, which reaches 0x80 exactly when i + n > 15. | Removes the 16-B store, the memset, the variable-length memcpy, the store-forwarding stall on the reload, and the dead `>= 16` branches. Portable, with no `#if`. | Low: 10.24M cases per op. |
| 6 | intrinsics.h:256-316 `sllv_epi16`, `srlv_epi16`, `srav_epi16` | **AVX2** (`#if SIMDE_X86_AVX2_NATIVE`): shift the even and odd 16-bit lanes as 32-bit lanes (vpsllvd/vpsrlvd/vpsravd), then `blend_epi16(0xAA)`. **SSE4.1** (`#else`): sllv = `mullo(a, 2^n)` with 2^n from a pshufb table. srlv = `mulhi_epu16(a, 2^(16−n))`, passing `a` through where n == 0. srav = `srlv(a ^ s, n) ^ s`, where `s` is the sign. | The pin widened with 4 unpacks and called the 32-bit variable shifts twice. Without AVX2, simde emulates those shifts, so v2 paid about 25-40 µops per helper. | Low. **All 2^32 (value, count) pairs** for each helper, at every config. Exact for every count: counts ≥ width give 0, or the sign fill for srav, so callers don't need to mask. |
| 7 | intrinsics.h:319 `sllv_epi8` | 2^n from a pshufb table, with `min_epu8(count, 8)` so n ≥ 8 gives 0. Then two `mullo_epi16`, one for the even bytes and one for the odd. | The pin nested two `sllv_epi16` calls, about 60+ µops at v2. | Low: all 2^16 (value, count) pairs. |
| 8 | math.h:63 `clamp_float<T>` | `T clamped_to_min` (was `float`). | **Bug:** for T = double it truncated, e.g. `(0.1, 0, 2)` returned 0.10000000149011612. | None for current callers. Every SDK caller passes float (xma_context.cpp:808, immediate_drawer.cpp:78-84, graphics/util/draw.cpp:383-385). |
| 9 | math.h:189-192 `rotate_left` | `sh = uint8_t(sh & (W-1)); (T(v) << sh) \| (T(v) >> ((W - sh) & (W-1)))` | **Bug:** sh == 0 shifted by the full width, which is UB (it trapped under `-fsanitize=shift`). sh ≥ W was UB too. | None. Nothing in the SDK or the generated code calls it. |

### Tests (bench/agent10)

`bench/agent10/ppc_ref.h` implements each op's PPC semantics in scalar code. `test_intrinsics.cpp` checks three sets of bodies against it:
- the pin's bodies, from `old_intrinsics.h` (a verbatim copy of the pin header in namespace `old_ppc`);
- the edited SDK bodies;
- the rejected candidates.

`kat.h` replays the expected values in `tests/ppc/asm`, and `test_math.cpp` covers math.h.

| Group | Cases (full mode: v3, v2, v3noavx2) | Quick mode (portable) |
|---|---|---|
| `sllv/srlv/srav_epi16` | all 2^32 (value, count) pairs | 2^20 pairs |
| `sllv_epi8` | all 2^16 pairs | all 2^16 |
| Emitted vslb/vslh/vsrh/vsrah/vrlh (the exact `emit_vec_var_shift` expressions) | every value × every low count bit pattern | subsampled counts |
| vslo/vsro/vsl/vsr | 256 count bytes × 40,002 vectors = 10.24M per op | 256 × 400 |
| vperm | 10^7 random cases, plus every control byte in every lane ×20 | 10^5 random |
| vctuxs | all 2^32 float bit patterns, at the default MXCSR and at FTZ\|DAZ, plus edge cases and the emitted UIMM forms | every 4099th pattern |
| Tables | contents and 16-B alignment | same |
| KAT replay (`tests/ppc/asm`) | 240 runs, 0 failed | same |
| test_math | `rotate_left` for sh 0..255 on u8/u16/u32/u64 under the `-fsanitize=shift` trap; `clamp_float` float and double cases | same |

- **Mutant self-test.** Building with `-DAGENT10_MUTANTS` plants one deliberate bug per helper. Every group then fails, with 2,811,264 failures in total. The exception is tables, which has no mutant. So the tests do catch wrong results.
- **Pre-fix evidence for math.h.** `build/agent10/test-math-v3-pre.log` shows six `clamp_float<double>` failures, e.g. `(0.1,0,2)=0.10000000149011612`. It then hits trap 0xC000001D in `rotate_left` at sh = 0.
- **v3 full-run timings.** The 2^32 shift group took 17.3 s. The two vctuxs sweeps took 29.3 s and 37.9 s.

### Microbench: before and after, from the same run

- **Log:** `build/agent10/bench-post.log`, produced by `build.ps1 -Bench -Configs v3,v3noavx2,v2 -BenchArgs '--reps 9'` between 19:06:12 and 19:06:45.
- **Comparison:** each config is a single binary, so the old (pin) and sdk (edited) rows come from the same run.
- **Units:** median TSC ticks per op over 9 reps, on one thread pinned to cpu 2. Each cell is throughput / latency, where latency is measured on a dependent chain.
- **Load:** other agents kept the machine at 69-99% CPU (no compilers were running at my sample points). Absolute numbers are therefore noisy; read the old/sdk ratios. The pre-edit baseline, taken at 100% load, is in `build/agent10/bench-pre.log`.

| op | v3 old | v3 sdk | v3noavx2 old | v3noavx2 sdk | v2 old | v2 sdk |
|---|---|---|---|---|---|---|
| vslh (emitted) | 4.39/4.33 | 3.03/2.90 | 9.89/20.18 | 3.08/4.42 | 12.61/27.06 | 3.91/8.27 |
| vsrh (emitted) | 3.57/4.24 | 2.96/2.71 | 19.05/18.95 | 4.90/8.02 | 28.18/29.41 | 6.87/11.61 |
| vsrah (emitted) | 3.65/6.98 | 2.79/2.52 | 18.05/19.42 | 5.59/11.27 | 28.86/28.25 | 8.83/15.40 |
| vrlh (emitted) | 6.18/9.80 | 6.08/5.96 | 27.21/31.15 | 6.31/10.80 | 39.22/39.48 | 10.68/11.00 |
| vslb (emitted) | 7.81/14.39 | 3.39/4.72 | 20.38/31.88 | 4.72/6.37 | 28.18/42.95 | 7.03/11.16 |
| vslo | 25.23/26.19 | 2.31/1.87 | 36.93/38.85 | 3.11/2.37 | 43.02/43.61 | 5.96/4.58 |
| vsro | 32.45/33.62 | 1.99/1.73 | 41.36/43.88 | 2.91/2.48 | 54.05/57.50 | 5.04/3.34 |
| vsl | 4.03/3.62 | 2.93/3.16 | 5.43/4.96 | 4.28/3.81 | 8.64/7.88 | 7.04/5.24 |
| vperm | 2.89/3.16 | 2.97/3.15 (noise) | 4.30/4.32 | 3.82/4.00 | 5.06/4.42 | 4.74/3.88 |
| vctuxs (+ xor glue) | 6.65/30.95 | 4.91/19.78 | 9.65/36.79 | 5.97/25.11 | 12.21/49.12 | 9.04/30.42 |

**Headline at v3, the game baseline:**
- vslo 25.2 → 2.3 and vsro 32.5 → 2.0 ticks/op (11-16× faster);
- vslb 7.8 → 3.4 (latency 14.4 → 4.7);
- vctuxs latency 31.0 → 19.8;
- vsl 4.0 → 2.9;
- vslh, vsrh and vsrah 1.2-1.5× faster;
- vperm unchanged within noise.

At v2 and v3noavx2, the element shifts are 3-6× faster (e.g. v2 vsrh 28.2 → 6.9, vslb 28.2 → 7.0).

### Compile check of a real generated TU (the game's flags)

- **TU and flags:** `legodimensions_recomp.61.cpp` from the baseline's generated sources, compiled with the game's exact flags (`-O3 -march=x86-64-v3 -msse4.1`, gnu++23). The PCH is not used; `cmake_pch.hxx` is force-included instead. The full command, with paths, is in `build/agent10/recomp61-cmd-overlay.txt`.
- **Include order:** `build/agent10/overlay/include` comes first; it holds copies of my two edited headers. The pristine `build/sdk/install/include` supplies everything else (its intrinsics.h and math.h are identical to the pin).
- **Result:** exit 0 in 19 s, producing `build/agent10/obj/recomp61.obj` (840 KB).
- **Which headers were used:** `build/agent10/recomp61.d` (from `-M -MF`) confirms both overlay headers. math.h comes in transitively through `rex/ppc.h`.
- **Table placement:** `llvm-nm` shows `?VectorMaskL@ppc@rex@@3QBEB` and `?VectorMaskR@...` as type `R` (.rdata).

### Rejected alternatives (measured at v3, same run)

| Alternative | thr/lat | Why rejected |
|---|---|---|
| vslo/vsro from a 48-B sliding LUT (the session-1 design) | vslo 2.77/2.00, vsro 1.94/1.44; the chosen computed index gives 2.31/1.87 and 1.99/1.73 | About the same speed, but it needs a GPR extract, a load and a 48-B table. It also faults with simde's portable loadu (bug note 6). |
| vctuxs "maxadd" form | 4.33/16.20; the chosen form gives 4.91/19.78 | Faster, but it relies on cvttps returning 0x80000000 for out-of-range lanes. That breaks under `SIMDE_FAST_CONVERSION_RANGE` and on non-x86 hosts. |
| SSE4.1 element shifts at v3 | vslh 2.34/3.62, vsrh 3.20/6.92, vsrah 4.38/9.33; AVX2 gives 3.03/2.90, 2.96/2.71, 2.79/2.52 | Worse latency than the AVX2 forms. Kept only as the `#else` path. |

### Bench-only adaptations (not in the SDK)

- **`bench/agent10/old_intrinsics.h` ~L244:** the pin's vsl passes a non-constant shift to `simde_mm_slli/srli_epi64`, which simde rejects under SIMDE_NO_NATIVE. Native builds keep the pin's exact code. The `#else` branch uses `sll/srl_epi64` with a `cvtsi32_si128` count and is marked BENCH-ONLY.
- **`bench/agent10/variants.h`:** the rejected LUT vslo/vsro read their window through `octet_window()`. When not native, that function uses memcpy, because simde's portable loadu is compiled to an aligned load (bug note 6).

### Bugs fixed (each one covered by a new test)

1. `clamp_float<double>` truncation (math.h:63). Covered by test_math.
2. `rotate_left` UB at sh = 0 and sh ≥ width (math.h:189-192). Covered by test_math under `-fsanitize=shift`.
3. The tables were mutable and only implicitly aligned, yet codegen reads them with aligned loads (intrinsics.h:40-115). Covered by the tables group.
4. The `shift_bytes >= 16` branches in vslo/vsro were dead. The rewrite removes them.
5. The pin's intrinsics.h didn't compile under SIMDE_NO_NATIVE, because vsl passed a non-constant imm8. The new vsl, vslo and vsro are portable, and the portable config passes.

### Bugs and notes for Agent 1 (left unchanged)

1. **vsl count byte.** vsl reads its count from x86 byte 15 (PPC byte 0). The ISA takes it from vB[125:127] (PPC byte 15), which is what vslo/vsro read. The two agree when every byte of vB is equal, and the ISA requires that for a defined result. I kept the pin's behaviour; the KAT replay passes.
2. **`rotate_left` with a signed T.** `T(v) >> ...` sign-fills, so it isn't a rotate for negative values. Nothing calls it.
3. **`GuestToHostFunction`** (function.h:464) memsets the 2.6 KB `PPCContext` on every host→guest call. Perf only; profile first.
4. **`FunctionDispatcher::GetFunction`** takes a recursive_mutex on the indirect-call fallback. Perf only; profile first.
5. **Scalar `vpkuhus`/`vpkuwus` fallback (vector.cpp, Agent 9's area).** It's wrong when vD == vB: the first loop overwrites vB's high bytes before the second loop reads them. This is pre-existing. Agent 9's new SIMD fallback is used only when vD differs from both sources, so the aliased case still takes the scalar path.
6. **simde portable `loadu` faults.** Under SIMDE_NO_NATIVE, clang 23 compiles `simde_mm_loadu_si128` (simde sse2.h:3763, a packed may_alias struct) to an aligned `movaps`, which faults (0xC0000005) on unaligned addresses. Nothing in the SDK headers or in codegen calls `loadu_si128`, so this only matters for portable or non-x86 builds. Worth reporting upstream.
7. **ODR.** The element-shift bodies differ in source between AVX2 and non-AVX2 TUs. Both are proven bit-identical for all inputs, so whichever COMDAT the linker keeps computes the same result. The pin already had the same exposure in machine code: an `inline` helper compiled at different `-march` levels in one link could hand AVX2 code to a v2 caller. That only matters if the SDK and the game are built at different `-march` levels.

### Session-2 files

- **SDK (both flagged above):** `include/rex/ppc/intrinsics.h`, `include/rex/math.h`.
- **Bench and tests:** `bench/agent10/{ppc_ref.h, old_intrinsics.h, impls.h, variants.h, kat.h, test_intrinsics.cpp, test_math.cpp, bench_intrinsics.cpp, build.ps1, DESIGN-notes.md}`.
- **Logs:**
  - tests: `build/agent10/test-post.log`, `test-post-portable.log`, `test-math-v3-pre.log`;
  - benches: `bench-pre.log`, `bench-post.log`;
  - TU compile check: `recomp61-cmd-overlay.txt`, `recomp61.d`, `obj/recomp61.obj`.

## Task #17 summary (07:05, session 3; sent to Agent 1, cc Agent 7)

Reviews, part 2. Read-only throughout: no builds, no game runs, no subagents. Write-ups are in [agent10-codegen-review.md](agent10-codegen-review.md) (nativeB gate, 1b, tie-break, the OPEN item, (b)) and in [agent10-batch2-review.md](agent10-batch2-review.md) §13-§21 (status rows 14-22).

| Item | Verdict | Write-up | Sent |
|---|---|---|---|
| 1a. nativeB static gate (with Agent 9) | **PASS.** statecmp and sumscheck MATCH; lrsites PASS; hookset PASS (181 hooks, same set and objects); mapcmp shows the same sub_ and alias sets (.text −10.38%); MANIFEST 149 PASS / 0 FAIL / 34 NOTE. | codegen-review "nativeB gate" | 04:43 |
| 1b. nativeB route pair, then the reversed-order tie-break | **PASS on every must-match item, both times:** logdiff NEW 0 / MORE 0 / flags 0; slot heap 9/9; pool copy 128/128; PSO 187/187; warning types equal; exit 0; no dumps. The placement relocation is not covered at runtime. | codegen-review "1b" | 05:23, 06:19 |
| 1b open item | nativeB leaves the front end ~12 s earlier: first frame → exit 105.7/108.9 s vs 118.9/120.5 s; A1 response → exit INSTALL 46.5/49.7 s vs 59.6/61.3 s. devoff leans the same way. **OPEN, not accepted.** Agent 1 (06:28): it is not a fail item and needs no rollback. | codegen-review end | |
| (b) guest code that starts the front-end exit, snap1 vs snapB3 | **Done (07:35): no codegen change found; the item stays OPEN for S4.** Agent 9's 11 clock-list functions and run 2's 9 have the same instruction sequences, with mechanical rewrites only (OTHER 0, no inline timebase read). Whole tree (feall): 164,786 functions, 0 sequence mismatches, 0 unexplained instructions; all 91,605 rlw rewrites proven; the 413 OTHER blocks are stcx. `cr0.so = 0` and the reviewed vector fallbacks. SO: one writer (sub_83E5C88C's mtxer) and no readers. B's locals (livein v2, liveflow): no read before a write except a setjmp-style CR save (sub_83E49CA0), and no read after a call on any path. The timer is armed only when sub_82FB9020 returns 1 (byte 0x848E2EA2 is 0, plus the mode-3 queries), and it counts only while [app]+2288 is 0. That fits background work gating the arm. S4: find those flags' writers, then run one instrumented pair. | codegen-review "(b) result"; `build/agent10/fe/` | ~07:35 to 1, 3, 9 |
| STUCK-LOCK on CS 0x84959edc | Not specific to native or to B: OFF builds hit it too on the CPU-saturated machine. Agent 6 owns it (#25); extras were sent 05:38. Watch it in the window-4 quiet runs. | codegen-review 1b "05:46 update" | 05:38 to 6 |
| 2. native3d n0/n2/n3 rows (with Agent 4) | **PASS** | batch2-review §13 "After the apply" | 05:04 |
| 3. Agent 11's timerq `timer_queue_precise_wait` | **SAFE** as a default-off candidate | §14, row 15 | 05:23 |
| 4. Agent 7's top 3 S4 native candidates | First safety read done | §15, row 16 | 04:53 |
| 5. Agent 11's pthrottle `host_execution_throttling_optout` | **SAFE** as a default-off candidate | §16, row 17 | 05:23 |
| 6. Agent 7's R1 stage 1 (split submits) and R2 (redundant-command filter) | **R1 stage 1: SAFE** as a default-off test bed under conditions 1-6: GPU Commands thread only, at the tail of IssueDraw/IssueCopy; the full guard including the occlusion-query and scratch checks; no manual BeginSubmission after a failed EndSubmission; kInitOnly cvar; OFF on native; expect no win alone. **R2: step 1 SAFE; step 2 SAFE-IF (a)-(e):** pure state setters only (never barriers, clears, copies, draws or queries); reset on Reset, Execute, SetDescriptorHeaps and every root-signature set; compare the full payload; reset on out-of-stream commands and splits; debug layer clean plus a frame compare. | §17, row 18 | this summary |
| 7. Agent 4's §S3.4 miss-cache | **SAFE at default OFF;** ON is output-identical under §15.2 1-8. Agent 1 recorded it as SAFE OFF, with no GO tonight. | §18, row 19 | 06:18 |
| 8. Agent 12's S4.7 race in `PhysicalHeap::Protect` | **CONFIRMED,** both forms. Fix (i) (keep G across both host protects) closes form 1. Form 2 is latent in this game: its protects are 4/0x404. | §19, row 20 | 06:43 |
| 9. Agent 12's #27 upload-hash diagnostic | **SAFE OFF;** ON is SAFE for functional runs (+1-3 ms/f, so no timing arms). | §20, row 21 | 06:43 |
| 10. C1 = P1 keep-watch (Agents 5 and 12) | **SAFE OFF.** ON is output-identical under conditions 1-4, apart from the new residual R1. Flip ON only with A-D. | §21, row 22 | 06:53 |
| 11. Agent 12's S4 P2 `shared_memory_single_hold_rearm` | **SAFE** at default OFF. ON: output-identical, with no new lock edge. Caveat: the memexport full-buffer fallback becomes one long G hold, so either confirm it doesn't run or cap the hold. | §22, row 23 | ~07:35 to 12, cc 1 |

None of the S4 items (timerq, pthrottle, miss-cache, #27, C1, P2, the §19 fix, R1/R2) is applied before S4 is planned with the user. Fix (i) item 4 (check that no heap_mutex_ → G path exists) is queued for S4.

**New tools** in `build/agent10/`:
- `nb/`: fpscan, statecmp, sumscheck, hookset, lrsites, nativelines, nrows, pgrep, warntypes, logwin, mapwhere, placescan, framepso, framealign, genfunc (v2), mapsym, exitpress, pairall, timermodel, poolbytes.
- `fe/`: fediff (v2: map lookup, a single-TU codegen diff, a per-instruction normalised compare, and automatic classes with rlw* proven by evaluation), feall (the whole tree, in 2 parts), livein (A: SO writers and readers, and stcx. without larx; B v2: first use and read-after-call for every local), liveflow (a CFG may-analysis), show, callers, flagw, flag2288.

**How it was tested:**
- pairall reproduced pair 1, and exitpress matched Agent 3's press times.
- timermodel and poolbytes were checked over 4-9 runs.
- §18-§21 are source-level reads; line references are in each section.
- #27 and P2: hashes, `git apply --check`, and a regenerated diff that matches the staged one hunk for hunk.
- fediff self-test: `sub_82BCE1F8` from its start and from an interior address, plus `sub_82A2A260`.
- fediff v2 evaluator self-test 6/6; feall over the whole tree (0 sequence mismatches; 4,568 rlw proofs, 0 failed); livein classifier self-test 29/29; liveflow self-test 9/9 (S, U, a jump-away path, brace blocks, helper calls, self-updates).
- Cross-checks with Agents 3, 4, 5, 6, 8, 9 and 12.
