# Agent 4: native renderer CPU cost per draw (tasks #3, #24)

> **DONE at 22:45 (run-2 task #12, from Agent 1 at 19:41): re-pin native once, on native4b. The pin record passed and Agent 3 has the handoff. Agent 1 announces the pin after Agent 3's runs pass.**
> - Step 1 (files) is DONE, all in `build/agent4/repin/` (shas as of 20:43):
>   - `REPIN.md` (02D08AF9) and `matrix-repin-native4b.json` (2580067D): n0old on native4-bin, n0/n2/n3 on native4b-bin.
>   - `matrix-repin-native4b-boot.json` (37DFC58F): 1 run with frontend=true, because native3_boot_check group A fails with frontend=false. Agent 1 OK'd the extra run at 20:30.
>   - `matrix-repin-packhit.json` (490964AC) was rewritten and is marked NOT TONIGHT.
>   - The native5 drafts are in `superseded/`.
>   - `repin_check.ps1` (81BE81D8) has the [5] fix: when the tree is applied, a frozen old-pin bin is reported as info.
>   - 20:39 (Agent 1): every run-matrix command now passes `-OutDir build\agent3\runs\repin[-boot|-packhit]-<stamp>`. Without it, the output lands in build\agent8\matrix and trips the HOLD manager. Agent 3 has been told.
> - Expected fp: 9b40acbbef4c57b3, from the pre-check `dryrun-snap1-1951.txt`. Sent to Agents 2 and 1 at 20:28 as provisional. Agent 1 (20:30): write the pin record only after step 1b confirms it on the real CMake re-run.
> - Step 1b is DONE (20:57, `build/agent4/repin/dryrun-native4b-1b-2055.txt`: 0 FAIL, 0 WARN). It ran after Agent 2's native4b configure at 20:53:23.
>   - [3]: memory_watch.cpp is 70829846 (172 CRLF / 0 bare LF). CMakeLists.txt is 1BF46D78, with #24 in.
>   - [4]: built (native-gpu-build.txt 20:53:53) = recomputed (271 inputs) = expected = 9b40acbbef4c57b3. That isn't 5e3ff55d.
>   - [5]: the old bins show as info.
>   - Confirmed to Agents 2 and 1. Next: step 3 once native4b-bin is staged (~21:20, Agent 2).
> - 22:32 (Agent 1): native4b staging is now ~22:55-23:10. The re-pin rows move to after tonight's windows: W8a4 runs tonight, and W8a moves to Monday's day session.
>   - If staging lands before ~23:40, write the pin record (step 3) and the Agent 3 handoff tonight, so Agent 3 can start the re-pin first thing after the windows. Otherwise do both after the windows.
>   - No tool calls while perf-notes/WINDOW-HOLD.txt exists or after Agent 1 announces a window. A backup check (every 10 min, to ~23:30) wakes me; during a window, end the turn without tool calls.
> - Step 3 is DONE (22:43, `build/agent4/repin/pin-native4b-2243.txt`, sha256 87DC898A, 0 FAIL / 0 WARN). Agent 2 staged native4b-bin at 22:40:17.
>   - [4]: built = recomputed (271 inputs) = expected = 9b40acbbef4c57b3, not 5e3ff55d. memory_watch.cpp.obj was rebuilt at 22:39:01.
>   - [5]: native4b-bin's MANIFEST is B63769FE (= Agent 2's sha256), with fp 9b40acbbef4c57b3 and exe DC6484C2: the same as the build dir, and not an old pin.
>   - Handed to Agent 3 at 22:45, for first thing after tonight's windows: the boot matrix and the 4-run matrix, both with -OutDir (REPIN.md section 3). The backup checks are cancelled, and @@done 12 is sent.
>   - After Agent 1 announces the pin: add `'9b40acbbef4c57b3' = 'native4b (S4b + S4c)'` to `$PINS` in repin_check.ps1.
> - The independent read (subagent f3a655f3) reported at 20:39 with 2 MISMATCHes, both fixed at 20:43:
>   - The S4-DRAFT line refs are now L73, L66/L293 and L16.
>   - Boot check group D is info-only, so a pass now also needs D's fingerprint line and VERDICT D=PASS.
>   - Also fixed: the B-line names (nativeB4b-bin), the 60 s warm-up floor, and the group B/C notes in boot.json.
> - Waiting on:
>   - Step 1b, after snap1-on's CMake re-run (build.ninja newer than 19:50:19, or Agent 2's message).
>   - Step 3, once `build/agent2/native4b-bin/MANIFEST.txt` exists.
>   - Then the handoff to Agent 3: the boot matrix plus the 4-run matrix, per REPIN.md section 3.
> - Agent 2 paused at 20:29 after the hook failed 3 times; its devoff4b build is still running. Native comes after devoff4b is staged.
> - After Agent 1 announces the pin: add `'9b40acbbef4c57b3' = 'native4b (S4b + S4c)'` to `$PINS` in repin_check.ps1.

> **DONE at 19:38 (run-2 task #3, which resumes old task #25, after Agent 1's "go" at 19:31): the mc_smoke_check C3 fix ran and passed.** Outputs are in `build/agent4/r2t6/recheck/`:
> - selftest: 15/15 (`selftest-v2.txt`).
> - r6 with v2: PASS, 91 exact keys, 8 heap pairs, 0 unmatched (`r6-v2.txt`). The sectdiff against Agent 3's v1 log shows only the header, C3 and RESULT differ. The 107 C3 key rows match except for the new tag (`r6-sectdiff.txt`).
> - 0452-n0-r1 against itself: PASS with both v1 and v2. Only the header and the C3 heading line differ (`0452-sectdiff.txt`).
> - Negative control, `--c3-rpf-tol 0.001`: FAIL with 2 + 2 unmatched, the 3.50 / 3.48 keys (`r6-neg-rpf0.001.txt`).
> - sha256: `mc_smoke_check.py` `EB13FA9605E1CF48F000B6364F283420FCF12925A5212450EB6DACDD1238D183` (21,483 B, unchanged since 15:48); `mc_smoke_selftest.py` `42943833…5BCA`; `recheck/sectdiff.py` `121E9E34…9AD2`. sectdiff now decodes UTF-16, because Agent 3 saved its r6 log with a PowerShell `>`.
> - The spec's §4 has the v2 note. The native re-pin still waits for native4b (Agent 1 will send it separately).
>
> **The RESUME note from before (board run 2, 17:08, before the agy-grid restart). Task #25 (from Agent 1 at 15:35): the mc_smoke_check C3 fix. Code written at 15:48, NOT run yet.** W4b (started 15:41) is done. Agent 1's rule: run the checks only after its "go" (W5 runs first). Until then, file tools only, and no tool calls at all while `perf-notes/WINDOW-HOLD.txt` exists. The native re-pin waits for native4b.
> - Files in `build/agent4/r2t6/` (LF, no BOM): `mc_smoke_check.py` v2 (21,483 B), `mc_smoke_selftest.py` v2 (7,215 B, 15 cases), `recheck/sectdiff.py` (a section-by-section diff of two checker logs). v1 is kept as `mc_smoke_check.v1.py` (`1735FAA1…EB8E`) and `mc_smoke_selftest.v1.py` (`6BAF4AA1…3385`).
> - C3 v2: a key in both arms matches itself. VS 0xAC449538, PS 0xAC448F28 and any `--fixed` address are never paired. Other one-arm keys pair one to one by stage, rows/frame (`--c3-rpf-tol`, 0.10) and first and last row (`--c3-window-s`, 10 s, after the median first-row offset of the exact keys). Unmatched keys are listed with a reason.
> - Next, after "go": one Python process at a time, from the repo root, at BelowNormal (run `(Get-Process -Id $PID).PriorityClass='BelowNormal'` first). Outputs go to `build/agent4/r2t6/recheck/`.
>   1. `python build\agent4\r2t6\mc_smoke_selftest.py` → 15/15.
>   2. r6: `python build\agent4\r2t6\mc_smoke_check.py --off build\agent3\runs\20261122-142131-s4a-r6off-trace-native4 --on build\agent3\runs\20261122-141746-s4a-r6on-mc-trace-native4 --off-trace <workspace>\build\agent3\s4a\trace\r6off-t --on-trace <workspace>\build\agent3\s4a\trace\r6on-t --out build\agent4\r2t6\recheck\r6-v2.txt` (absolute trace paths, as Agent 3 used them) → PASS, 91 exact, 8 heap pairs, 0 unmatched. Then `python build\agent4\r2t6\recheck\sectdiff.py build\agent3\s4a\logs\r6-mc_smoke_check.txt build\agent4\r2t6\recheck\r6-v2.txt -v`: only the header, C3 and RESULT may differ.
>   3. `build\agent8\matrix\20261122-0452\runs\0452-n0-r1` against itself, with `mc_smoke_check.v1.py` and v2, then sectdiff → still PASS (C3 and C4 SKIP: no trace).
>   4. Negative control: step 2 plus `--c3-rpf-tol 0.001` → FAIL with 2 OFF-only + 2 ON-only unmatched (the 3.50 / 3.48 rows/frame keys).
>   5. The sha256 of both scripts, a one-line v2 note in `r2t6/miss-cache-on-smoke-spec.md` near line 83, then `@@done 25` with the sha256 and both re-check results.

> **BOARD RUN 2, task #6 (from Agent 1 at 13:04 on 2026-11-22, after the Windows Update restart at 08:29-08:34; game `08933a7`, SDK `c5fe668`): native support for S4a, and the s35 pack's status.** Reads, notes and small scripts only. No builds, game runs, shader compiles or pack runs before W4b. Files are in `build/agent4/r2t6/`. Reported to Agents 1 and 2 at about 13:50.
> - **Item 1, DONE at 13:48** (`r2t6/native4-check.txt`):
>   - native4-bin's applied shaders.cpp (`build/agent2/snap1/.../gpu_native/shaders.cpp`, `9567FE3F…1EFA`, 51,261 B) matches `build/agent4/s34/shaders.cpp` byte for byte.
>   - Agent 2's backup is the base `E87A2DEE…`. Its MANIFEST row is `S4a A4 … E87A2DEE43D38D8E -> 9567FE3F3B63637D`.
>   - snap1's gpu_native matches live except for shaders.cpp (184 files each).
>   - `snap1-on`'s `shaders.cpp.obj` is from 13:34:24. The exe (`65432C81…B811`, 13:34:42, fingerprint `5e3ff55de10f4f64`) contains `LEGO_NATIVE_SHADER_MISS_CACHE` and `shader_miss_cache_insert`.
>   - devoff4 compiles no gpu_native file, so it has no miss cache. Live shaders.cpp is still `E87A2DEE…`.
> - **Item 2, DONE at 13:29:** the miss-cache ON smoke spec went to Agent 3 (`r2t6/miss-cache-on-smoke-spec.md`).
>   - Checker: `r2t6/mc_smoke_check.py --off <run> --on <run> [--off-trace D] [--on-trace D]`. Exit 0 = pass, 1 = fail, 2 = bad input.
>   - Tests: `mc_smoke_selftest.py` 7/7; `0452-n0-r1` checked against itself PASSES.
>   - ON writes nothing to game.log. With `LEGO_NATIVE_TRACE_DIR` set, it adds up to 64 `shader_miss_cache_insert` rows to events.tsv.
>   - A trace dir changes render paths, so only compare a trace run with another trace run.
> - **Item 3, s35:** `run-071627` PASS 07:16:50. SHA256SUMS 34/34; gradient 4 of 4. All 4 placement shaders are in `runtime-cache.cpp` (PS `75A4D1AB`, VS `ACAF01F0`, VS `CCD76553`, PS `E81FD692`). b2r §15.1:
>   - Item 1 OPEN. It needs a 2nd dump run with `LEGO_DUMP_MISSING_SHADERS` and `LEGO_NATIVE_TRACE_DIR`. Only `0509-sd-r1` exists, and it has no trace. This waits until after W4b.
>   - Item 2 met offline, but Agent 2's build-time `lego_gpu_prelink_runtime` step is still open.
>   - Items 3-5 OPEN. Runtime hits need a bin that has the pack. The visual check is done with the user in S4. The n-row rule in proposal §6 isn't applied yet.
> - Told Agent 11 at 13:29: S4-DRAFT row 1 still says the -Go run is pending. Row 2's "ON adds log lines" should say events.tsv rows only.
> - **Task #16 (from Agent 1 at 13:52): the user's on-screen check of the 4 packed shaders (S4-DRAFT §4a question 4; b2r §15.1 items 3-5).** Notes only, written 14:02-14:05: `r2t6/VISUAL-CHECK.md`. It has a 3-line summary for the user, the build (Agent 2's snap1/snap1-on + the s35 inputs + `lego_gpu_prelink_runtime`, in a new folder), the agent checks (a traced n-row pair native4 vs pack, plus snapshot diffs for where to look), the user's steps (devoff4-bin as the reference, 2 × 300 s no-input runs, Win+PrtScn at 3 moments, ~15 min), the n-row pass rule, the fail paths and the user's 3 decisions.
> - **Task #20 (from Agent 1): native prep for the re-pin after S4b.** Notes and dry runs only, done by 14:40. `build/agent4/repin/REPIN.md` covers what the re-pin includes, the steps with their times, Agent 3's checks and my order: native4p first, then roll back, then S4b → native5 (the pin) → native5p. Also in that folder: `repin_check.ps1` (dry run by default, `-Go` needs `-W4bDone`; it recomputes the fingerprint and reproduces 5e3ff55d…/81d1c3a7… exactly) and two draft matrices. Finding: copied inputs need a fresh mtime, or the fingerprint step and the index recompile don't see them.

> **RESUME (session 3, 08:00 on 2026-11-22; task #12 closed at 06:14; the s35 scratch pack PASSED at 07:16).** `draw.cpp` is still mine. Other agents send me draw.cpp patches; nobody else edits it. Live draw.cpp is `5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410` (306,557 B, 5,758 lines, mtime 03:34:59). That is batch 3, the §S3.2 guard (§S2.11 batch 3). The batch-2 file (`50AA3B1D…`) is saved as `build/agent4/scratch/draw.before-s32.cpp`.
> - **Task #12 (from Agent 1, 02:47): the §S3.2 hash=0 fix. Steps 1-3 DONE. Agent 1's extras (b) and (c) were delivered at about 06:10, scratch only, and `@@done 12` went with them. Agent 1 closed #12 at 06:14.** 1 subagent used (read-only research on the AOT tooling, for (b)). Files: `bench/agent4/**`, `build/agent4/**`, these notes, draw.cpp.
>   - **Step 1, DONE at 03:15:** the patch was built and checked on scratch copies only, with results in §S3.2. Files are in `build/agent4/s32/`: `draw.cpp` (patched copy, `5EA1F357…4410`), `draw.before.cpp`, `draw-s32.patch` (`F5434325…2387`) and the scripts. The scratch tree is `build/agent4/s32tree/`. Sent to Agent 10 and Agent 1. Agent 10 rated it SAFE at 03:31.
>   - **Step 2, DONE at 03:34:59** (Agent 1's GO at 03:35, after Agent 10's SAFE at 03:31): `apply_live.ps1` wrote `5EA1F357…4410` behind hash checks; `git apply --check -R` rc=0; numstat `5 0`. Logged in §S2.11 batch 3 and §S3.2. The sha256 went to Agents 1, 2, 8 and 10. Agent 1 committed it as game `08933a7` (pushed).
>   - **Step 3, DONE at 05:05:**
>     - Agent 2 built native3d-bin (S3 plus this one-file delta) and staged it at 03:46 (exe `B90DF683…`, fingerprint `335ff2d47268f3a1`).
>     - Agent 8 ran n0/n2/n3 on it as functional runs on an idle machine, from my spec `bench/agent4/s3/matrix-native3d-functional.json`: `build/agent8/matrix/20261122-0452` (04:52-04:59).
>     - All three log 0 hash=0 lines (native2: 0 / 67,220 / 44,968). `check_n_rows.py` passes n2 and n3 with no new warning type (`bench/agent4/s3/check-native3d.json`), and Agent 10 agrees (`build/agent10/nb/`). Details: §S3.2 "Step 3".
>     - `|| !vs` isn't needed (Agent 1, 05:05), so there is no native3e build and `build/agent4/s33/` stays unused.
>     - th3 is back in the matrix: n0/th1/th2/th3 ×3, every arm on native3d-bin (§S3.4). Agent 8 has it for a later window.
>   - **Extras (Agent 1, 05:05; §S3.5):** delivered at about 06:10, scratch only, no live apply and no build tonight. Files are in `build/agent4/s34/`. Agent 1 put both in its artifact (06:14).
>     - (b) an AOT-pack proposal for placement VS `0xAC449538` / PS `0xAC448F28`: `aot-pack-proposal.md`. Agent 7 checks the dumped PS words before anything is packed.
>     - (c) the `LEGO_NATIVE_SHADER_MISS_CACHE` stopgap, default OFF, on scratch copies of shaders.cpp, for Agent 10's S4 review: `miss-cache-review.md`, `shaders-s34.patch` and the patched `shaders.cpp`. Live shaders.cpp (`E87A2DEE…916D`) is untouched.
>     - Agent 1's 05:05 question (are the 2 start-up "not present in AOT cache" hashes the placement pair?) is answered: no (§S3.2 "Step 3").
> - **(b) the scratch AOT pack, in `build/agent4/s35/`: DONE at 07:16:50, VERDICT PASS (Agent 1, 06:14, confirmed 06:31; §S3.5 "Scratch pack").** It has no task number. At most 2 threads at BelowNormal; no live apply, no bin; no writes to the game/SDK trees, the generated junction or any bin dir. Stop by 08:25 whatever the state; anything unfinished waits for S4.
>   - Gate 1 MET at 06:22: Agent 7 cleared the PS words. Gate 2 MET at 07:01: Agent 8's last run ended at 07:00:02 and its slot is over.
>   - `run_pack.ps1 -PlanOnly -Mask 2` at 06:36: PLAN OK. `-Go` at 07:16:27-07:16:50: `run-071627/`, VERDICT PASS. 4 of 4 compiled; index 19,116 → 19,122; both lookups print `PASS: 4 captured containers`; no side effects (§S3.5 "Go"). README.md "Results" and §S3.5 are filled in, and the result went to Agent 1 at about 07:25. Nothing more runs tonight.
> - **S4 list (mine; nothing tonight):**
>   - (b): an Agent 2 bin with the s35 outputs (§S3.5 "Not tonight (S4 handoff)"), Agent 8's functional n-rows, and the native vs Xenos screenshot check with the user. W4b is frozen at d0/B/d3/d11t, so the screenshot check can't go in window 4.
>   - (c), the miss cache: SAFE at OFF; it needs Agent 1's GO.
>   - Agent 7's #26 THREADED tail: the zero-code checks are done (#33, functional only). S4-T1 stays staged, with switch values 1 (priority), 2 (EcoQoS) and 3 (both), Agent 7's code details and a staged grid (§S3.5 "#33"; the spec is `perf-notes/agent7-present.md` "Task #26").
>   - T1–T13 and the timing matrix (§S3.4).
> - **Task #3 (session 3): DONE at 02:30.** It covered N1-N3 against §S2.12 (§S3.1), perf.csv against native-frames.csv (§S3.3) and the matrix trim to n0/th1/th2 ×4 (§S3.4).
> - **N1-N3 verdict:** N1 passes every check. N2 and N3 pass every check except one new warning type, `Native GPU shader cache miss: hash=0x0` (N2 67,220 lines, N3 44,968). Task #12 fixed it: native3d's n2/n3 log none (§S3.2). N3 prints no "Native draw batches" line, which is correct (§S3.1).
> - **Waiting:** nothing tonight; s35 passed at 07:16. Agent 10 rated (c) SAFE at default OFF, accepted the item-6 leaf mutex and signed off item 8 (`perf-notes/agent10-batch2-review.md` §18 plus addendum, row 19). (c) is parked for S4, and applying it needs Agent 1's GO. Agent 7 cleared the PS words at 06:22. T1–T13 (§S2.12) still wait for native timing data (my matrix, in a later window). Don't send `@@done 24` before then unless Agent 1 says so, because it releases draw.cpp.
> - **Native builds:**
>   - `build/agent2/native2-bin` (S2, exe `5D1B2DC6…`) was used by N1-N3, window 3's n0 and the current matrix. It needs `native_settings_frontend=false` (§S2.13).
>   - `build/agent2/native3-bin` (S3 with fix-a and S2's draw.cpp; exe `7F7F8586D219465C`, fingerprint `8f849b69907d4006`) was staged by Agent 2 at 02:50.
>   - native3d-bin (native3 plus §S3.2, draw.cpp `5EA1F357…`) was staged by Agent 2 at 03:46 as `build/agent2/native3d-bin`: exe `B90DF683D0A57A21…`, rexruntime `D1D66AC3716835AC` (same as native3), MANIFEST `368F9CE650EC56CE`, fingerprint `335ff2d47268f3a1`. Its MANIFEST names exactly my write (`50AA3B1D…` → `5EA1F357…`, mtime 03:34:59), and every file except the exe and map equals native3-bin. The matrix moves every arm to it together.
> - **Session-3 rules (Agent 1):**
>   - only Agent 2 builds (at most -j10); everyone else uses at most 2 threads;
>   - agent game runs are functional only and go through Agent 8's slot;
>   - no builds or game runs from 08:30 (window 4 waits for the user, about 10:00; W4b is frozen at d0/B/d3/d11t);
>   - questions go to Agent 1, not the user.
> - **A new draw.cpp patch:** check the live hash first; apply with a hash-checked `WriteAllBytes` (never git); compile v3 and v2 with full `-c`; re-run the fixtures (9/26), state shadow and `run_patched.py`; log it in §S2.11; tell the sender and Agent 10. The S2 cut was at about 23:15, so any new patch goes into the next batch.
> - **Quiet windows:** when Agent 1 announces one, pause all compiles, tests and benches until it ends. Editing and reading are fine.
> - **Never:** run ninja in build/dev, use more than 2 threads, or run git commands that change a repo. Compile only with `env/compile-one.ps1 ... -Db build/dev/compile_commands.json`.
> - **Earlier:** task #3 (sessions 1-2) was done at 20:06; §S2.1–§S2.10 are its report. The batch-2 async-PSO hooks were applied at 21:24:30 (§S2.11). Window 3's n0 (00:13–01:16, frames=native): 6.71 ms (6.55..6.87), GPU 43–50% (§S2.12). Native first-boot crash: §S2.13.

**Status (session 3):**
- Default path DONE.
- Elision DONE, opt-in.
- Batch 2 (#24): async-PSO hooks APPLIED, opt-in (`LEGO_NATIVE_PSO_ASYNC` unset by default).
- Threaded path: N1 functional PASS. N2/N3's hash=0 warnings are FIXED (§S3.2, task #12): batch 3 was applied at 03:34:59 (§S2.11) and committed as game `08933a7`; native3d's n0/n2/n3 pass the functional check with 0 hash=0 lines.
- Timing matrix READY for a later window (§S3.4): n0/th1/th2/th3 ×3 on native3d-bin, with Agent 8.
- Placement shaders VS `0xAC449538` / PS `0xAC448F28` (Agent 7): (b) the scratch AOT pack PASSED at 07:16 (`build/agent4/s35/run-071627/`: 4 of 4 compiled, 6 index rows, production lookup PASS 4); the bin, n-rows and screenshot check are S4. (c), the default-OFF miss cache, is rated SAFE by Agent 10 and parked for S4. Nothing is applied (§S3.5).
- T1–T13 PLANNED (§S2.12), waiting for native timing data.

§0-§7 below are the session-1 analysis (12:xx), kept as written. Their draw.cpp line numbers are from before the session-2 edits; §S2 has the current ones.

---

## S3. Session 3 (task #3, 02:05–02:30; task #12, 02:47–06:10): N1-N3 functional check, hash=0 warnings and their fix, matrix, placement-shader follow-ups

Paths are relative to `DimensionsRecomp/rexlego/src/gpu_native/`. draw.cpp line numbers are from batch 2 (`50AA3B1D…`). Since batch 3 (03:34:59, §S2.11), batch-2 lines after 1498 are at +5. New files for task #3: [check_n_rows.py](../bench/agent4/check_n_rows.py), and in `bench/agent4/s3/`: `check-n123.json`, `check-control-n0.json`, `perf_vs_native.py` and `perf-vs-native.json`. Task #3 didn't run the game or compile anything: Agent 8 ran N1-N3 in its slot, and I only read the run directories. Task #12's compiles and fixture runs used scratch copies only (§S3.2). Its files are in `build/agent4/`: `s32/` (the fix), `s33/` (the unused `|| !vs` follow-up) and `s34/` (the extras, §S3.5).

### S3.1 N1-N3 functional runs

Agent 8 ran them on `build/agent2/native2-bin` with `native_settings_frontend=false`, as functional runs with a 60 s window. Their fps numbers are not timing.
- N1: `build/agent8/matrix/s3-n123-0205/runs/0205-n1-r1`
- N2: `build/agent8/matrix/s3-n2-0210/runs/0210-n2-r1`. It was rerun alone: in `s3-n123-0205`, n2 is "NOT STARTED" because free RAM was 5.77 GB (under 6 GB) during Agent 2's build.
- N3: `build/agent8/matrix/s3-n123-0205/runs/0208-n3-r1`

Checker usage:

    python bench/agent4/check_n_rows.py --baseline <n0 run dirs> --rows n1=<dir> n2=<dir> n3=<dir> [--json OUT] [--examples N]

It reads game.2.log, game.1.log and game.log in that order, because game.log rotates at 5 MB and keeps 2 files. It reports lost boot lines. Checks per row:
- run.json status OK, and the env matches the row;
- `Native GPU: threaded recording ON (LEGO_NATIVE_THREADED=1)` exactly once;
- the batches line: `serial workers=0` (N1), `parallel workers=2` (N2), none (N3; see below);
- one `Native worker: last 600 frames …` line per 600 presents (±1.5);
- worker thread names from threads.csv;
- no new warning or error type compared with the baseline, and no baseline type above 2× its n0 maximum;
- a clean close.

It also prints, for information only: mean and max cores, thread counts, the top threads, GPU utilisation and fps.

Baseline: window 3's n0 runs `build/agent8/matrix/20261122-0013/runs/{0016-cold-n0,0030-n0-r1,0042-n0-r2,0054-n0-r3,0104-n0-r4}` (11 warning types, 66-67 warning lines per run). Output: `bench/agent4/s3/check-n123.json`.

| Row | Verdict | Batches line | Worker lines | Worker threads (busy %) | New warning type | Cores mean (max) | Peak threads | fps / median / p99 (not timing) |
|---|---|---|---|---|---|---|---|---|
| N1 | PASS | `serial workers=0` | 19 for 11,674 presents | recording (80.5%) | none | 1.75 (2.27) | 69 | 108.4 / 8.04 ms / 41.4 ms |
| N2 | FAIL, warnings only | `parallel workers=2` | 22 for 13,573 | preparation (60%), prepare 1, prepare 2, recording | 67,220× hash=0 | 1.92 (2.35) | 73 | 135.4 / 6.66 ms / 24.7 ms |
| N3 | FAIL, warnings only | none, as expected | 17 for 10,577 | preparation (59%), prepare 1, prepare 2, reclaim, recording (31.5%) | 44,968× hash=0 | 1.98 (2.33) | 73 | 90.2 / 10.53 ms / 25.3 ms |

- All three rows: status OK, env OK, the ON line exactly once, and a clean close with exit 0.
- N2's log rotated (game.1.log 5,242,814 B + game.log 2,011,592 B). Its boot lines were in game.1.log.
- N3's "missing from AOT index" warning reached its cap of 16 lines (n0 has 8). That is under the 2× rule, so it isn't flagged.
- **Negative control:** window 3's `0030-n0-r1`, checked as n1 with itself in the baseline, fails env, the ON line, batches, worker lines and thread names, and shows 0 new warning types (`bench/agent4/s3/check-control-n0.json`). So the checks can fail, and the warning diff stays silent on a run checked against itself.

**Why N3 has no batches line.** The line comes only from the one-time initializer in `NativeParallelDrawsEnabled()` (draw.cpp:5572-5583). Its callers are:
- CaptureParallelDraw (5099);
- the queued draw hook (5190);
- WorkerMain (native_worker.cpp:273).

With `LEGO_NATIVE_FULL_DRAW_PREPARATION=1`, WorkerMain hands over to CoordinatorMain (native_worker.cpp:260), and both queued hooks call CaptureFullDraw (draw.cpp:5177, 5206) before they reach 5190. So nothing calls it. §S2.12 expected `serial workers=2` for N3, which was wrong. The checker identifies N3 by its thread names instead; full preparation also starts the recorder thread (native_worker.cpp:346).

### S3.2 hash=0 shader cache misses (N2, N3): cause and fix (task #12)

**Status (06:10): APPLIED at 03:34:59 and VERIFIED in game.** Step 1 passed on scratch copies, Agent 10 rated it SAFE at 03:31 ([agent10-batch2-review.md](agent10-batch2-review.md) §13), and Agent 1 gave GO at 03:35. Live draw.cpp is `5EA1F357…4410` (§S2.11 batch 3), committed by Agent 1 as game `08933a7`. native3d's n0/n2/n3 log 0 hash=0 lines ("Step 3" below), so `|| !vs` ("Not covered" below) isn't needed.

Every run with `LEGO_NATIVE_PREPARE_THREADS=2` logs `Native GPU shader cache miss: hash=0x0000000000000000` (shader_archive.cpp:432). N2 logs about 760 lines/s. N3's rate goes up 4.7× at the light-to-heavy title switch, about 37 s after the first frame. N1 and n0 log none.

How it happens (line numbers from the live file):
1. The preparation paths capture shader bindings without the failed-bind check. N2 captures in CaptureParallelDraw (`CaptureShaderBindings()`, 5106). N3 captures in full preparation (`CaptureShaderBindings(vertex, pixel)`, 4944), once per frame for each shader pair.
2. Preparation runs under those bindings.
   - A worker's `PrepareDrawWork` installs them (`ShaderBindingsScope`, 1656) and calls `PrepareDrawGeometry` (1498) at 1667, unless the geometry is already done.
   - In N3, `CaptureDrawGeometry` (4654) also calls `PrepareDrawGeometry(work, true)` (4674). Each of its callers holds a scope over the same bindings (scope/call at 4718/4729, 4961/4962, 4974/4987 and 5120/5137).
3. `BoundShaderHash(kVertex)` is 0 when the captured vertex shader address is set but has no owner (`addresses[0] && !owners[0]`). Placement shaders that are missing from the AOT index are one example.
4. PrepareDrawGeometry then looks up hash 0 up to three times per draw, and every failed lookup warns.
   - The vertex-fetch planner looks it up first (`FindDxil`, 1533). No shader means no plan, so it falls back to `PrepareDrawGeometryLegacy` (1551 → 1293).
   - Legacy's input-usage lambda looks it up twice more (1368, 1380).
   - With the planner off, 1507 goes straight to Legacy.
   - Failed lookups aren't cached.
5. The recorder drops the same draw at 2713. `vertex_binding_failed` comes from `BoundShaderAddress` (2707-2708; shaders.cpp:682-686), on the same bindings. The serial path drops it in the same place, before its own geometry lookups (3108, 3120).

So the image doesn't change. The cost is wasted preparation and the log spam (about 760 lines/s). In long runs the spam also rotates game.log past its boot lines. This keeps th2's timing provisional and th3 out of the matrix.

**Which draws (Agent 7, 04:41; [agent7-present.md](agent7-present.md) Task #13 S3).** The failed binds come from placement VS `0xAC449538` (backing `0xED23D3E0`) and PS `0xAC448F28` (backing `0xED23D540`). Neither is in the AOT index, in any native2 run. A miss registers nothing, so every SetShader and the per-frame retry repeat the full lookup while holding LockRecording. In n-prof that cost 6.10 of 12.36 ms per frame of render-thread CPU. Agent 7 proposes either dumping them (`LEGO_DUMP_MISSING_SHADERS=1`) into the pack, or a negative cache in AdoptShader (shaders.cpp, which isn't mine). What I sent Agent 1 at 04:45:
- Every native mode drops these draws at the failed-bind test (live 2718-2725), so no native build has drawn them.
- In the logs (n0 `0030-n0-r1`, S3 N3), the first bind is 4-5 s after the first frame, and the hash=0 rate rises at the title switch.
- The PS's first 4 words are zero when it is bound.
- Whether the draws are visible can't be told from the code.
- Adding the shaders to the pack would draw them for the first time. That is a visual change, not just a perf change.
- BindShader's lock also stalls the recorder in th1-th3. If a fix lands before the matrix window, the matrix bin should include it.

**The fix** (approved by Agent 1 at 02:47 as task #12). The recorder's failed-bind test becomes the first statement of `PrepareDrawGeometry`, so a draw that the recorder will drop is never planned. 5 lines are inserted after 1498:

    // DispatchDraw drops a draw whose vertex shader failed to bind, so its geometry is never used.
    // Planning it anyway looks up hash 0 (one shader cache miss warning per lookup).
    bool vertex_binding_failed = false;
    BoundShaderAddress(ShaderStage::kVertex, &vertex_binding_failed);
    if (vertex_binding_failed) return false;

- **Where.** The first proposal put the test in Legacy's early return (1306). That misses the planner lookup at 1533, which runs before Legacy. The entry guard covers 1533, 1368 and 1380.
- **Same test, same bindings.** It is the recorder's own test (2707-2713). Every PrepareDrawGeometry call runs under a `ShaderBindingsScope` over the snapshot that the recorder installs later (4401 `head.shaders`, 4474 `work.shaders`, 5697 `work->shaders`). So exactly the draws the recorder drops skip preparation, and nothing that reaches the GPU changes.
- **Side effects, for failed-bind draws only.** `geometry_ready` stays false, as it does with the existing early returns (1520-1521, Legacy 1306). Then:
  - (a) PrepareDrawWork's `if (!work.geometry_ready)` (1667) runs the guard a second time, which costs two loads.
  - (b) The recorder takes the index metadata (2669-2670) from `InspectBufferResource` instead of the capture. That can only move the drop from 2713 to 2675, and both are drops. The barriers and framebuffer set between them (2691-2704) are per draw, and the next draw sets them again.
  - (c) Full-preparation template qualification sees `use_windows=false`, so it checks whole-buffer watches instead of window watches. That only decides whether a failed-bind capture becomes a template. Its repeats carry the same failed bindings and are dropped too.
  - The default serial path never calls PrepareDrawGeometry, so it is unchanged.
- **Not covered: vertex shader address 0.** Then `binding_failed` is false, so the guard lets the draw through.
  - The serial path drops such a draw at the null pipeline (2883-2895), before its geometry lookups. Its only record there is a long-probe event (`draw_pipeline_unavailable`), so n0's zero count doesn't show whether these draws exist.
  - If native3d's n2/n3 still log hash=0, these draws are the likely source.
  - Possible follow-up, not applied: `const u32 vs = BoundShaderAddress(...); if (vertex_binding_failed || !vs) return false;`. It is safe only if a VS-0 draw can never get a pipeline. `ResolveBoundShader` returns null without a resource (shaders.cpp:653-655), test_shader_binding_failures asserts `!ResolveBoundShader(kVertex, 0)`, and GetPipeline (1691) caches only pipelines it has built.
  - **Agent 1 (03:17): leave it out for now.** A second native3d build costs only about 3-4 min, and VS-0 draws would need their own proof that the recorder drops them too. If native3d's n2/n3 still log hash=0, prepare it then, with that proof.
  - Proof, done ahead (read-only, 03:25-04:02). It is complete, so `|| !vs` needs only the step-1 protocol if native3d still logs hash=0. Line numbers here are from the live batch-3 file (`5EA1F357…`):
    - **Only `FindDxil` warns** (shader_archive.cpp:432). GetPipeline's variant lookups use their own tables and never call it: `FindFloatBlendIndicesDxil`/`FindPositionPrecisionDxil` (float_blend_indices.cpp:27-34), `SelectIntegerInputShader` (integer_inputs.cpp:100) and `ResolveInstancedConstantsShader` (instanced_constants.cpp:35). DispatchDraw's uses of the VS hash between its failed-bind drop and the pipeline (2766, 2816, 2839, 2883) don't call it either. So n0's zero count says nothing about VS-0 draws.
    - **Address 0 never has an owner.** `BindShader(stage, 0)` stores the address with a null owner (shaders.cpp:579-581), and the refresh skips address 0 (600). The failed-adopt path (568-569) stores a nonzero address, and the only other writes reset owners (732, 894-895). The N2 capture `CaptureShaderBindings()` copies owners and addresses under one lock (611-612). The N3 capture `CaptureShaderBindings(v, p)` adopts nothing for 0 (620), and it is the only code that writes a snapshot's owners (628, 630). So for a VS-0 draw:
      - `BoundShaderHash` is 0 (813-821), so preparation warns;
      - `binding_failed` is false (685), so the current guard lets the draw through;
      - `ResolveBoundShader(kVertex)` returns null (653-655).
    - **No variant table has a hash-0 entry** in native3d's banks (Agent 2's snap1 tree). Float blend indices and position precision share one table (386 entries); instanced constants have 2,542 entries and integer inputs 7. Their shader caches hold only entries that were found.
    - **No VS-0 key ever gets a pipeline.** Key equality (265-279) and the key hash (287) use `vertex_shader_hash` and `bool(vertex_shader)`, so any equal key is also VS-0. GetPipeline (1696) returns a cached or in-flight pipeline (1700, 1705, 1710, 1713). It posts a compile (1860-1864) or caches a new pipeline (1879) only after its `!vs` check (1737). For a VS-0 key, `vs` (1731-1735) is always null, because every variant lookup misses on hash 0 and `ResolveBoundShader` has no owner. By induction, GetPipeline returns nullptr for every VS-0 key.
    - **The prepared-pipeline path gives the same result.** `PreparedValue::Resolve` (draw_preparation.h:17-24) returns the value cached for an equal key, or calls `prepare()` (GetPipeline, 2888) and caches that. `Reset` stores nullptr. Neither depends on `geometry_ready`.
    - **So the recorder drops every VS-0 draw** at the null pipeline (2891-2900, long-probe event `draw_pipeline_unavailable`). That is before its own geometry lookups (3102-3125), DispatchDraw's only `FindDxil` calls on the VS hash. (GetPipeline reaches `FindDxil` only through `ResolveBoundShader`, shaders.cpp:664, which needs an owner.) Skipping preparation for these draws can't change what is drawn, because `geometry_ready=false` is an ordinary preparation miss that the recorder handles itself. Their warnings stop instead of moving to the recorder.
    - Side effects (a)-(c) above apply to VS-0 draws the same way. In (b), the drop can move from the null pipeline (2891-2900) to the index check (2680). In (c), N3's VS-0 template repeats carry the same address 0.

**Step 1 (03:00–03:12), on scratch copies only; live draw.cpp untouched.** Files are in `build/agent4/s32/`: `make_patch.py`, `compile_copy.ps1`, `static_check.py`, `run_checks.ps1`, `objdiff.py`, and the step logs. The scratch tree `build/agent4/s32tree/DimensionsRecomp/` holds 2,286 files, copied without junctions. Its draw.cpp is the patched copy; the other 183 gpu_native files are byte-identical to live. Everything ran with at most 2 threads, no ninja and no game.

| Check | Result |
|---|---|
| Live draw.cpp | `50AA3B1D…BDD6`, 306,221 B, 5,753 lines, CRLF, mtime 21:24:30 |
| Patched copy (`draw.cpp`) | `5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410`, 306,557 B, 5,758 lines, CRLF |
| Patch (`draw-s32.patch`) | `F54343258029F89A47BDBCC1392461B0B79686219A804A7FAE9473CF51852387`, 787 B. It has 1 hunk, `@@ -1496,6 +1496,11 @@`, +5/−0. `apply_check.py`: MATCH. `git -C DimensionsRecomp apply --check` on live: rc=0 (read-only) |
| Compile v3 / v2 (compile-one full `-c`, 1 thread, scratch tree) | exit 0 each, 77 warnings, 0 errors (same as batch 2). Objects: 2,038,469 / 2,023,089 B (`build/agent4/obj/s32-v3`, `s32-v2`) |
| Object diff against batch 2 (`objdiff.py`, output in `objdiff-v3.txt`/`objdiff-v2.txt`) | Of the 794 functions in `.text`, only `PrepareDrawGeometry` changed: v3 3,712 → 3,536 B, v2 3,760 → 3,584 B. No COMDAT section changed. `.rdata` +21 B is the longer source path (`build/agent4/s32tree/`) |
| Disassembly (v3) | The function now starts with `BoundShaderAddress(6, &flag)`, `cmpb $0`, then `xor eax` and return. Stage 6 is the same `kVertex` value as its existing `BoundShaderHash` call |
| `static_check.py` | OK: the guard is the first statement; the planner and Legacy lookups are reachable only after it; DispatchDraw's lookups come after its drop |
| Fixtures (run_fixtures; live tree, then scratch tree) | 9/26 on both, the same pass set as batch 2 (`compare_fixtures.py`: SAME) |
| State shadow (scratch tree) | OK, 20 runs, 19 audit checks |
| `run_patched.py --trees s32` | 3/3 PASS (constant_timing, query_retirement, query_sample_pool) |
| test_parallel_geometry (not one of the 26; it extracts PrepareDrawGeometry) | Fails on live and patched alike: `dev-assets/sdk-install/include` is missing. With `CPLUS_INCLUDE_PATH=<tree>/rexglue-sdk/include`: live has 16 errors (stale stubs); patched has the same 16 plus `undeclared identifier 'BoundShaderAddress'`. Whoever revives this fixture needs that stub |

**Step 2: DONE at 03:34:59** (§S2.11 batch 3). `apply_live.ps1` wrote the tested bytes: live `5EA1F357…4410`, 306,557 B, 5,758 CRLF lines; `git apply --check -R` rc=0; numstat `5 0`. The sha256 went to Agents 1, 2, 8 and 10.

**Step 3: DONE at 05:05 (native3d functional check).** Agent 2 built native3d-bin from exactly this one-file delta (staged 03:46; exe `B90DF683…`, fingerprint `335ff2d47268f3a1`). Agent 8 ran n0/n2/n3 from `bench/agent4/s3/matrix-native3d-functional.json` (sha `FACD09D1…`) on an idle machine: `build/agent8/matrix/20261122-0452`, runs `0452-n0-r1`, `0454-n2-r1` and `0456-n3-r1` (04:52-04:59). I checked them with `check_n_rows.py` against `0452-n0-r1` plus window 3's n0 ×5; the output is `bench/agent4/s3/check-native3d.json`. Agent 10 checked them separately (`build/agent10/nb/`) and agrees.

| Row | hash=0 lines, native2 → native3d | check_n_rows.py | Other |
|---|---|---|---|
| n0 | 0 → 0 | baseline | 480 log lines, 66 warning lines (window 3's n0: 66-67) |
| n2 | 67,220 → 0 | PASS, 10/10 checks | `parallel workers=2`; 26 worker lines for 16,145 presents; 66 warning lines; clean close |
| n3 | 44,968 → 0 | PASS, 10/10 checks | no batches line (expected); 27 worker lines for 16,580 presents; reclaim thread present; 58 warning lines; clean close |

- Neither row has a new warning type against n0, or a baseline type above 2× n0's maximum. The fps (mean n2 109.6, n3 116.7) are functional numbers, not timing.
- **Why no hash=0 lines remain.** Agent 1 expected a few from the two missing placement shaders. There are none because those draws are exactly the failed-bind draws: VS `0xAC449538` is never adopted, so its captured owner is null and `binding_failed` is set, which is the guard's test. Planning was the only place that looked up their hash, and the recorder still drops them before its own lookups. No address-0 VS draw logged a lookup either, so `|| !vs` isn't needed. `build/agent4/s33/` (prepared at 04:07: `make_patch.py`, patch `DBFED1D8…9271`, `static_check.py`, `make_tree.py`, `run_checks.ps1`) stays unused.
- **The other shader warnings are unchanged, and capped.** AdoptShader's "missing placement shader" lines and BindShader's "unrecognized" lines both count in `g_shader_warning_count` (shaders.cpp:76). "Missing" prints while it is below 16, "unrecognized" while it is below 32, and both count even when they don't print. The two alternate, so n0 and n2 show 8 "missing" and 16 "unrecognized" lines. In n3, full preparation skips BindShader, so all 16 go to "missing". That is the n3 difference Agent 7 saw: a logging-cap effect, not a change in behaviour.
- **The 2 start-up warnings** in every native run (`shader not present in AOT cache, hash=0xA58EBA123EFB541C / 0x93B9F93B535E7CCA`; Agent 1's 05:05 question) are not the placement pair. They are CreateShaderResource misses (shaders.cpp:513), logged about 10 s before the first placement miss (05:09:24 on t26812 in Agent 8's dump run `build/agent8/matrix/20261122-0509/runs/0509-sd-r1`). Their dumps are `vs-A58EBA123EFB541C.bin` (704 B) and `ps-93B9F93B535E7CCA.bin` (156 B); the sizes match none of the 4 placement containers. They are registered create-hook objects that are never drawn (0 cache-miss lines). Like the placement misses, they come from native3d-bin's stub runtime shader cache, which holds 0 shaders.
- **A second placement pair.** The dump run also wrote `vs-CCD7655302B54D80.bin` / `ps-E81FD692C3AB35E1.bin` at 05:10:01 with no warning line, because the shared counter was already past its caps. So (b) packs all 4 placement containers (§S3.5).

### S3.3 perf.csv vs native-frames.csv (one frame source for every arm)

Script: `bench/agent4/s3/perf_vs_native.py`; output: `bench/agent4/s3/perf-vs-native.json`. It compares the two frame files on 7 native runs: window 3's n0 r1-r4 and S3's N1-N3. Both files are written in the same present call (device.cpp:2266-2276, fps_counter.h:37).
- perf.csv has one extra leading 0 row, so it is offset by +1 row.
- Over the window, mean fps agrees within 0.001%, the median within 0.002 ms and p99 within 0.015 ms.
- Single frames differ by up to about 4 ms in about 4% of frames, but the differences cancel out over the window.
- native-frames.csv's `draw_calls` median is 8 in every run, so that column says nothing.

So `"frames": "perf"` is a valid single source for native arms, and it is the source the OFF-build arms (d0, devoff, B) use. Window 3's n0 used frames=native with a 50 s window from 35 s, so it isn't compared with the S3 matrix.

### S3.4 Timing matrix, trimmed for a later window

[matrix-native-threaded.json](../bench/agent4/matrix-native-threaded.json): SHA256 `76FE0BAAD3BF36BCC8D020DAAE57CF20C61B47D9928766DB622D7210DEFF6248`, 7,931 B, LF, no BOM. History:
- `B858C76C…`: n0 and th1-th3 ×5 plus a cold run, 21 runs, about 63 min.
- `1F8BC5DD…C581` (02:20, task #3): n0/th1/th2 ×4 on native2-bin, th3 dropped.
- `419FAE1F…20C4` (05:05, task #12 step 3): th3 back, every arm on native3d-bin, ×3. Saved as `build/agent4/matrix-native-threaded.419FAE1F.json`.
- `76FE0BAA…6248` (06:05): adds `"sys_csv": true` and its note (Agent 8's suggestion, as in `bench/agent8/run/matrix-window4.json`). The arms are unchanged.

Contents:
- **Arms:** n0, th1, th2 and th3, 3 repeats each, round-robin, no cold run. th3 is back and th2 is no longer provisional, because native3d logs no hash=0 lines (§S3.2 "Step 3").
- **Same for every arm:** bin `build/agent2/native3d-bin`; cvars `native_settings_frontend=false native_fps_limit=0 framerate_limit=0`; driver `drivers/thread-cpu.ps1`; `"frames": "perf"`, with `LEGO_NATIVE_FRAME_METRICS=<run>\native-frames.csv` kept as a cross-check (same cost in every arm). Only the environment differs. If an AOT-pack or miss-cache bin (§S3.5) is staged before the matrix runs, every arm moves to it together, after that bin's own functional n-rows pass.
- **Window:** settle 5 s + warm-up 55 s from the first frame, so the window starts 60 s after the first frame, past the light-to-heavy title switch at 30-40 s. That meets Agent 8's `min_window_after_ff_s` (default 60). Measure 60 s, cooldown 5 s.
- **No cold run:** it is unscored, and its warm-up is capped at 10 s, which breaks the 60 s rule.
- **sys_csv:** `drivers/sys-csv.ps1` logs idle time, foreground window, input desktop, screensaver, CPU and power every 1 s (sys.csv, sys.json), so the runner flags runs disturbed by input, foreground loss, a screensaver or a power change.
- **`-PlanOnly`** (`run-matrix.ps1 -Matrix bench\agent4\matrix-native-threaded.json -PlanOnly`, 06:05; output `build/agent4/planonly-sys-csv.txt`): "12 runs (0 cold), about 30 min", rounds `n0 th1 th2 th3 | th1 th2 th3 n0 | th2 th3 n0 th1`, sys.csv ON, nothing started, exit 0. Its preflight FATAL was only Agent 8's game running at the time.
- **Time:** 4 arms × 3 repeats = 12 runs, the same count as the ×4 version. The planner says about 30 min (about 142 s per run). Window 3's native runs took about 16 s per run longer than planned, so expect 33-34 min; window 3's worst overhead on every run gives about 41 min, inside the 45 min cap.
- **Decision rule (3 repeats):** an arm counts only if its mean fps beats n0's in all 3 round-robin rounds AND its median frame time is below n0's lowest median. Report mean fps next to the median (frame times can be bimodal). Compare only within this matrix.
- **Check the runs** with `check_n_rows.py`, using this matrix's n0 runs as the baseline: `--rows n1=<th1 run> n2=<th2 run> n3=<th3 run>`. Expect no hash=0 lines in any arm.
- **Handover:** `1F8BC5DD…` went to Agent 8 at 02:30 and `419FAE1F…` after step 3; Agent 8 re-copied that byte-identical into `bench/agent8/run/`. `76FE0BAA…` went to Agent 8 at 06:10 to re-copy. It isn't run tonight; window 4 is mainly B vs devoff2. For the functional matrix (`matrix-native-functional.json`, with my n1-n3 rows), Agent 8 pins `min_window_after_ff_s` to 0, which keeps that matrix's 30 s protocol.

### S3.5 Placement shaders VS 0xAC449538 / PS 0xAC448F28: AOT-pack proposal (b), scratch pack (s35) and miss-cache stopgap (c)

Agent 1 (05:05) asked for both after the rows, by about 06:30, on scratch only: an S4 review, no live apply and no build tonight. shaders.cpp isn't mine, so (c) exists only as scratch copies. Agent 7 checks the dumped PS words before anything is packed. Everything is in `build/agent4/s34/`.

**(b) [aot-pack-proposal.md](../build/agent4/s34/aot-pack-proposal.md)** (sha256 `B89DFA7311F002A2C09BD7921069404052B61D2900BA96ECE607D7AD998A8D08`, 7,414 B):
- **Why:** BindShader is 49 % of render-thread CPU in Agent 7's n-prof. The draws that bind these shaders are dropped at the failed-bind test (draw.cpp:2712-2725), so packing the shaders also changes the image.
- **Root cause:** native3d-bin is built with the stub runtime shader cache (0 shaders; `build/agent2/snap1-on/CMakeCache.txt`), so every placement shader misses.
- **Inputs:** Agent 8's dump run, `build/agent8/matrix/20261122-0509/runs/0509-sd-r1/shader-dumps/`. Agent 7's check (`build/agent7/sd/shader-dump-check.txt`): 9 files dumped, all containers OK. Open question for Agent 7: the PS `0xAC448F28` dump's physical section starts with 12 zero words (words 0-11), and the second placement PS also starts with zero words. **Answered (Agent 7, 06:22, `build/agent7/sd/ps-words-check.txt`):** the words are real, not an artifact:
  - Each PS physical section is `[64 B literal constants][microcode]`. Words 0-11 are three zero float4s, and words 12-15 are luma weights.
  - The microcode is at physical offset 0x40, sizes 0x90 / 0x78, ending exactly at physical_size 208 / 184.
  - The VSs have their microcode at offset 0. The interpolator words match (0x2042 / 0x1021).
  - Packing all 4 is OK if the entries cover the whole physical section.
- **Path A (recommended):** steps 0-6 with exact commands, using Agent 6's `gradient_compiler.exe` and `lego_gpu_microcode_index.exe` (`build/agent6/aot/`), `merge_microcode_index.py` and `test_placement_capture_lookup.py` (`DimensionsRecomp/tools/gpu-aot/`) and `build/agent2/snap-native-inputs.py`, working in `build/agent4/s35/`. Then an Agent 2 bin, functional n-rows (pass rule in the doc) and a native vs Xenos screenshot check. **Correction (Agent 1, 06:14):** the screenshot check is an S4 step with the user, not window 4, because W4b is frozen at d0/B/d3/d11t. The doc's own "window 4" wording dates from 06:10 and is superseded; the doc itself stays unchanged (sha256 below). The doc also covers rollback, and why Path B (the LEGODX1 precompiled pack) is blocked.
- **Effort:** about 45 min of agent time, plus the screenshot check (an S4 step with the user).
- **Recommendation:** pack all 4 placement containers in one round, since the second pair uses the same mechanism. The 2 start-up containers are optional.

**(c) [miss-cache-review.md](../build/agent4/s34/miss-cache-review.md)** (sha256 `7AA19D11F71D4C2D0F5DC380A06FD5AB2A5BBA46507A0540BD54F71E821BF9D8`, 13,285 B). The patch is [shaders-s34.patch](../build/agent4/s34/shaders-s34.patch) (`328BDAE19ABFC6C8CD980847F8AE533A0360589760A1D67EFE7C2F4762F518DF`, +229/−11, 9 hunks) against live shaders.cpp `E87A2DEE…916D` (= `shaders.before.cpp`). It gives the scratch `shaders.cpp` `9567FE3F3B63637D9595D6B74B72567E1CAEA2D1A071E872D12660DFB37E1EFA` (51,261 B, 1,131 CRLF lines).
- **Design:** a negative cache in AdoptShader, keyed on (stage, guest address, container), as Agent 7 proposed. An entry stays valid while a CpuMemory stamp of the code's pages is unchanged; otherwise the lookup is retried at most once per `g_probe_frame`. It is OFF unless `LEGO_NATIVE_SHADER_MISS_CACHE=1`, and forced OFF when `LEGO_DUMP_MISSING_SHADERS` is set (the capture's own predicate), so a capture run never skips a capture. A replayed miss prints the same line through the shared `LogMissingPlacementShader`.
- **Review map:** Agent 10's §15.2 conditions 1-8 are mapped to patched lines. There is one deviation, in item 6: a leaf mutex (about 20 ns) instead of relying on the recording gate, whose two recursive halves depend on the mode. Known residuals: readability is checked from the protection only; the pool-copy window at hooks_buffer.cpp:190-198; the stamp is page-granular (both spans are on page `0xED23D000`).
- **Tests** (scratch, 1 thread, BelowNormal, no ninja): full `-c` compiles of v3 and v2, patched and control, all exit 0 with 0 errors and the same 2 warnings (`warn-diff.txt`). A new `objcheck.py` pairs functions by name, normalizes the disassembly and maps source_loc lines between the two files. v2 and v3 agree (`objcheck-v2.txt`, `objcheck-v3.txt`):
  - 383 functions are identical, and 7 differ only in spdlog `__LINE__` constants.
  - The 12 code changes are exactly AdoptShader, InvalidatePlacementShader, PoolCopyMayTouchShaders, InvalidatePoolCopyShaders, ResetShaderResources and the static initializer, with their EH funclets.
  - 55 functions were added (the helpers) and 3 removed (an old spdlog arg-pack instantiation).
  - `.rdata` adds only `LEGO_NATIVE_SHADER_MISS_CACHE`, `shader_miss_cache_insert`, `prefix=` and a helper's function name, which is a source_loc field that the game.log pattern doesn't print.
- **Expected gain:** at most about 5.98 of BindShader's 6.10 ms/f (FindShaderByMicrocode 3.10 + ReadableGuestSpan 2.88, out of 12.36 ms/f render-thread CPU in n-prof). The header ReadableGuestRange check remains. The image doesn't change, because the draws stay dropped.
- **Asks for Agent 10:** an S4 rating, acceptance of the item-6 deviation, and sign-off on item 8. **Answered (Agent 10):** SAFE at default OFF. The item-6 leaf mutex is accepted and item 8 is signed off (`perf-notes/agent10-batch2-review.md` §18 plus addendum, row 19). Optional later: a comment pointer at shader_archive.cpp:341-344. Applying it needs Agent 1's GO, and the ON run must show `shader_miss_cache_insert` for VS `AC449538` and PS `AC448F28`.

**Decision (Agent 1, 06:14, in its artifact):** (b) may be packed on scratch only, in `build/agent4/s35/`, once Agent 7 clears the PS words and Agent 8's last run has ended (below). (c) is parked for S4. Either one still needs a new Agent 2 bin and its own functional n-rows in S4; then the matrix moves every arm to that bin.

**Scratch pack ((b), [build/agent4/s35/README.md](../build/agent4/s35/README.md)).** Agent 1 approved it at 06:14 and confirmed at 06:31. Scratch only, at most 2 threads at BelowNormal, no live apply, no bin, no writes to the game/SDK trees, the generated junction or any bin dir; stop by 08:25.
- **Gates:**
  - (1) MET at 06:22: Agent 7 cleared the PS words.
  - (2) MET at 07:01: Agent 8 posted that its last run ended at 07:00:02, that its slot is over, and that none of its games or runners is running.
- **Inputs:** the 4 placement containers from `0509-sd-r1`, sha256-pinned (physical size; microcode offset+size):
  - VS `0xAC449538` = `vs-ACAF01F01E1C03D2.bin` (324; 0+324);
  - PS `0xAC448F28` = `ps-75A4D1ABA62F7594.bin` (208; 64+144);
  - the second pair, `vs-CCD7655302B54D80.bin` (288; 0+288) and `ps-E81FD692C3AB35E1.bin` (184; 64+120).
  - The memexport start-up VS and the start-up PS are not packed.
- **Driver (`run_pack.ps1`):**
  1. Agent 6's `gradient_compiler.exe` (DXIL only) and `lego_gpu_microcode_index.exe`.
  2. A merge into native3d-bin's index (snap1, 19,116 rows, `2DB85917…`) with `merge_microcode_index.py`.
  3. Static checks (`check_pack.py prelookup`).
  4. The unchanged `test_placement_capture_lookup.py`, without and then with the main archive.
  - Every tool and input is pinned by sha256 and re-checked after the run, and the top level of 11 read-only dirs is diffed.
- **Expectation:** 4 runtime-cache entries and 6 index rows. Each PS gets a whole-section row and an instruction-stream row; each VS gets 1, because its two signatures are the same.
  - The index prefix is XXH3 of the first 8 bytes. Both PS whole-section rows go into the zero-bytes bucket (`C77B3ABB6F87ACD9`), which already holds 6,636 PS rows and 1,209 VS rows of the 19,116.
  - Old lookups can't change unless a span is byte-identical to a new section over its full length (README, "Why existing lookups don't change").
- **PlanOnly** (06:36, 1 CPU, `plan-063629.txt`): PLAN OK; all 14 pins and 4 inputs ok; PRECHECK PASS.
- **Go: `run-071627/`, VERDICT PASS (07:16:27-07:16:50).** Affinity 0x3, BelowNormal, script sha256 `D29E23BE…8669`.
  - Steps: precheck, gradient_compiler (0.3 s; "AOT coverage: 4 of 4 unique shaders (100.00%)"), indexer ("Indexed 6 shader microcode blobs"), merge (19,116 → 19,122, all prior records preserved), prelookup, lookup (6.9 s) and lookup-main (9.7 s). All exit 0, and both lookups print `PASS: 4 captured containers`. Post check: 28 of 28 ok.
  - Runtime cache: 4 DXIL entries, 18,936 B decompressed. The PSs (`75A4D1AB…` 4,644 B, `E81FD692…` 3,772 B) have spec mask 2; the VSs (`ACAF01F0…` 5,420 B, `CCD76553…` 5,100 B) have spec mask 1. That is normal: the main cache has 8,329 / 1,203 / 69 entries with mask 2 / 1 / 0.
  - Index rows: PS 208 + 144 and 184 + 120 (whole section, then instruction stream); VS 324 and 288. The two PS whole-section rows go into the zero-bytes bucket (6,636 old stage-1 rows).
  - Negative controls pass: no container and no new signature is in the old index, and no container is in the main cache.
  - Side effects: none. Every pin is unchanged, and `tmp/` is empty.
  - sha256:
    - `runtime-cache.cpp`: `AEA36683202B97535C52DFA7D7548EEBA1D3512E70717C2DE381FB59CC29A734` (33,765 B);
    - merged `lego-microcode-index.cpp`: `E4C05782462452C3104A165AF588F21F42910FBD07A75A0071A34F89E3060617` (1,672,272 B);
    - `index-addition.cpp`: `154242FB07BEDC92075585D96C714CFA5273824EEE4B5FA9690F46CFBD3398F6`;
    - `pack-check.json`: `0985CFF7…A0EB`;
    - everything else: `run-071627/SHA256SUMS.txt`.
- **Not tonight (S4 handoff; README "Not done here (S4)"):**
  - **Agent 2, after Agent 1's GO:**
    - Point the CACHE FILEPATH `LEGO_NATIVE_RUNTIME_SHADER_CACHE` (CMake 283-285) at a snapshot copy of `run-071627/runtime-cache.cpp`. snap1-on and snapB3-on currently use `…/out/native-gpu/stubs/runtime-cache.cpp`.
    - Put `run-071627/lego-microcode-index.cpp` at the fixed `<snap>/rexlego/out/native-gpu/lego-microcode-index.cpp` (CMake 274-275). Do this only if that copy is still the merge base `2DB85917…`; otherwise re-merge `index-addition.cpp`.
    - `snap-native-inputs.py` copies only from the live tree, so these files need a direct, sha-checked copy.
  - **Prelink:** `LEGO_NATIVE_RUNTIME_PRELINKED_BANK` is empty, so the build re-runs `lego_gpu_prelink_runtime` (CMake 408-426 and 511-519). That makes the spec-mask entries usable. Its write stays inside the snapshot, because snap1's `rexlego/out` is a plain directory.
  - Agent 8's functional n-rows on that bin. Pass rule: the miss lines for the 4 hashes disappear, with no new warning type.
  - The native vs Xenos screenshot check with the user, because the placement draws stop being dropped.

**Agent 7's #26 THREADED tail (06:21, "your call"; `perf-notes/agent7-present.md` "Task #26"):**
- The extra >33 ms frames in n2/n3 are isolated spikes, about 2/s against about 0.2/s for n0.
- The guest waits 3.4-9.4 ms/f in `NativeWorkerThrottleFrames(1)`.
- Only the worker thread is ABOVE_NORMAL (native_worker.cpp:349).
- My call (S4 list, no runs tonight): zero-code checks first, n2 and n3 with `LEGO_NATIVE_TIMING=1` and n2 with `PARALLEL_DRAWS=0`. Then S4-T1 `LEGO_NATIVE_CHAIN_PRIORITY` (default OFF, with an EcoQoS opt-out), if the checks point at priority. Its switch values were split at 07:50: 1 priority, 2 EcoQoS, 3 both (see "#33" below).

**#33 zero-code read-out (Agent 7, 07:40; `perf-notes/agent7-present.md` "Task #33"; bins in `bench/agent7/w4b_readout/zero-code-bins.txt`).** FUNCTIONAL ONLY, SAT, n=1, one arm per matrix, all on native3d-bin.
- **Tail:** the >33 ms tail follows the E-core slow state (E-cores under 800 MHz).
  - n3t: 229.6 frames/min after the onset, 56.8 before.
  - n2s: 89.7 after, 22.7 before.
  - n2t: no onset; 23.0/min, p99 21.6 ms.
- **PARALLEL_DRAWS:** before the onset, n2s (`PARALLEL_DRAWS=0`) looks like n2t: 22.7 vs 23.0/min, p99 22.2 vs 21.6 ms. So it shows no tail change.
- **Where the time goes:** on the >33 ms frames the present/swap call itself runs long. No arm has pipeline creations or sync waits.
  - n3t: `present_cpu_ms` 18.8 vs 2.8, `swap_present_cpu_ms` 12.6 vs 1.9.
  - n2t: `present_cpu_ms` 5.2 vs 1.9.
  - n2s: swap 4.2 vs 1.2.
- **Present thread (my code read, 07:43):**
  - n2: the SwapHook task (draw.cpp:5448, then `PresentTexture` and the swap) runs on WorkerMain. That thread is already `THREAD_PRIORITY_ABOVE_NORMAL` (native_worker.cpp:347-349 and 259-297).
  - n3 (`FULL_DRAW_PREPARATION=1`): the same thread runs CoordinatorMain instead. It forwards the present task with `NativeRecorderSubmit` (:241-242; :226-231 under FSR3). RecorderMain runs it (:152-194, started at :346). That thread has no SetThreadPriority, so it is NORMAL.
  - native_worker.cpp:349 is the only priority call in `rexlego/src`, and nothing there touches power throttling.
  - All three game.logs show `Native worker: ... inline=0 drains=0`, so no task, the present included, ran on a guest thread. The guest's throttle_wait per 600 frames was 2.2-2.3 s in n2t, 2.5-2.9 s in n2s and 3.8-5.1 s in n3t.
- **Before/after split (Agent 7, 07:48, scratch; n=1, SAT).** `swap_present_cpu_ms` on the >33 ms frames vs the rest, with `present_cpu_ms` in brackets:
  - n2t, no onset: 1.1 vs 0.9.
  - n3t: before the onset 6.4 vs 1.6 (9.4 vs 2.4); after it, 15.6 vs 2.9 (23.5 vs 4.4).
  - n2s: before 1.0 vs 1.0; after 4.6 vs 1.3.
  - So n3's NORMAL present path grows even before the slow state, which fits priority as the cause of n3t's tail before the onset.
  - ABOVE_NORMAL looks like partial protection, not none. In the slow state the swap grows by 3.3 ms in n2s and by 12.8 ms in n3t.
  - About 35 ms of n2s's roughly 40 ms slow frames lies outside the swap.
- **What this means for S4-T1:**
  - In n3, S4-T1 raises the present thread itself from NORMAL to ABOVE_NORMAL. The growth before the onset (swap 6.4 vs 1.6 ms) is what it should shrink.
  - In n2 the present thread is already ABOVE_NORMAL. T1 as specced in #26 also raises the RecordingQueue thread (native_recording.cpp:138) and the prep-pool workers (native_preparation.h:21-26), and it opts every chain thread out of EcoQoS. So a gain in n2 wouldn't isolate EcoQoS. That is Agent 7's correction; my 07:45 rule "helps both = EcoQoS" was wrong.
  - Most of n2s's slow-frame time lies outside the swap, so expect less from T1 in n2 than in n3.
- **My call (07:50, corrected; aligned with Agent 7's spec at 07:58 and 08:00):** S4-T1 stays staged on my S4 list. No runs tonight. The reference is Agent 7's spec: `perf-notes/agent7-present.md`, "Task #26", "S4-T1 (proposal)" (about :473-490).
  - Switch values, taking Agent 7's split: `LEGO_NATIVE_CHAIN_PRIORITY` = 1 for priority only, 2 for the EcoQoS opt-out only and 3 for both; unset or 0 is OFF. One bin then covers every arm.
  - Code details (Agent 7, 07:52):
    - Value 1 gives the recorder, the RecordingQueue thread and the prep-pool workers ABOVE_NORMAL, as the worker already has.
    - Value 2 covers every chain thread, the worker/coordinator included. WorkerMain is already ABOVE_NORMAL (native_worker.cpp:349) but isn't opted out of EcoQoS, so in n2 value 2 must still reach it.
    - Parse the value once in a helper modelled on `NativeWorkerEnabled()` (native_worker.cpp:319-327: a function-local static, an exact string compare, one log line). Any other value means OFF.
    - Log one line naming the mode, at INFO like :323. `check_n_rows.py` counts only warning/error/critical lines as types (`LEVEL_RE`, :43), so a WARN-level mode line would fail "no new warning/error types vs n0" in arms 1-3.
  - S4 order (as in Agent 7's spec):
    1. A functional run, 0 vs 3: identical output, plus the mode line in game.log for each of 1, 2 and 3. In S4 I add a mode-line regex and an expected mode per row to `check_n_rows.py` (next to `BATCHES_RE`, :40), so the check confirms each arm's mode.
    2. The timed matrix to Agent 7's #33 checklist: n2/n3 x {0, 3} plus n0, at least 3 runs each (n0 adds about 10 min), interleaved, focused, on an unsaturated machine, with a sys.csv slow-state check per run and each run scored only up to its onset. n0 is the reference arm that the >33 ms excess is measured against; arm 0 is T1's control.
    3. Only if 3 helps: n2/n3 x {1, 2}, to attribute the gain to priority or to EcoQoS.
  - If 3 helps neither arm, the slow-state cost sits behind Present or outside the chain threads, and S4-T1 is dropped.
  - Step 2 runs in Agent 8's user-started runner, so its windows are focused; tonight's #33 runs were all on the hidden desktop. Agent 11's task #24 left visibility or foreground QoS open as a cause of the slow state. Drop rule (Agent 7, 07:58): if n2-0 and n3-0 show no slow state and sit within n0's range on >33 ms/min and p99, T1 has nothing to fix for players and is dropped at step 2.
  - Record SAT per run (the w4b_readout background column). A gain seen only while SAT, where priority matters most, does not carry over to an unsaturated machine.
  - Prior for value 2 (Agent 11's task #24, `perf-notes/agent11-kernel.md` "Result (task #24)"): a process-level EXECUTION_SPEED opt-out (d0 vs d0e, 3 pairs, hidden desktop, held in 99.6-99.7% of reads) did not keep the E cores out of the ~550 MHz state; it came in 3/3 runs of each arm. Agent 1 dropped `host_execution_throttling_optout` from S4 at 06:28. #24 measured the onset and the slow share on d0, not the frame tail, and a per-thread tag may act differently from the process flag (Agent 11's "not ruled out" list). So value 2 keeps its arm in step 3, with a low prior.

---

## S2. Session 2: changes, verification, numbers, in-game A/B plan

Paths are relative to `DimensionsRecomp/rexlego/src/gpu_native/`. Line numbers in §S2.1–§S2.10 are from the batch-1 tree (S1: draw.cpp has 5,719 lines). The batch-2 patch moves later draw.cpp lines down by up to 34 (table in §S2.11); §S2.11–§S2.12 use batch-2 numbers (5,753 lines). All benches: clang 23 from devshell, `-O2 -march=x86-64-v3`, at most 2 threads, median of 5 run medians. Bench and test sources are in `bench/agent4/`; results are in `build/agent4/`.

### S2.1 Changes for the 20:15 batch

| File | Change | Default behaviour | Header edit? |
|---|---|---|---|
| draw.cpp | items 5, 6, 4; SSE2 `#else`; elision; 5 new diagnostic hooks; SwapHook pacing call | identical | — |
| queries.cpp | item 1: `std::atomic<size_t> active_queries` | identical | — |
| long_probe.h | `LongProbeEnabled()` goes through `CachedProcessFlag` | identical | **yes, included by 7 TUs:** buffers, device, draw, hooks_portrait, queries, shaders, textures.cpp. It is not one of the 101 SDK headers in the generated-code closure |
| state_call_diagnostic.h | 12 new counters and CSV columns | identical (capture off unless `LEGO_NATIVE_STATE_CALLS` is set) | yes; draw.cpp only |
| draw_cached_flag.h (new, 24 lines) | `CachedProcessFlag<Read>()` | — | new; draw.cpp and long_probe.h |
| draw_log_throttle.h (new, 16 lines) | `TakeLogBudget(counter, limit)` | — | new; draw.cpp only |
| draw_state_shadow.h (new, 57 lines) | `DrawStateShadow` (std-only) | — | new; draw.cpp only |

| Variable | Default | Effect |
|---|---|---|
| `LEGO_NATIVE_ELIDE_STATE_CALLS` | unset → off. Only the exact value `1` enables it (`_dupenv_s`, read once) | Inline draws skip `setIndexBuffer` / `SetNativeBlendFactor` when the shadow proves the same value is already bound on the same recording (§S2.5) |
| `LEGO_NATIVE_STATE_CALLS=<csv>` (`_TRIGGER=<file>` optional) | unset → off | Unchanged semantics. The CSV gains `framebuffer_*`, `index_*` (incl. `index_skipped`), `blend_*` (incl. `blend_skipped`), `viewport_*` and `scissor_*`: 28 columns. The first 16 are as before |
| `LEGO_NATIVE_UNLOCKED_PACING` | unset → no-op | Agent 7's switch. It is read by `HostDevice::PaceFrameBeforeLock()`, which SwapHook now calls; unset, it returns before taking any lock |

> [!NOTE]
> One log-only difference (STATUS decision 5): the three per-draw "log the first N" throttles no longer print again after their u32 counter wraps. That would take 2^32 draws, about 10 h at 120k draws/s.

### S2.2 What changed, where

| Item | Where | What | Risk |
|---|---|---|---|
| 5 log throttles | draw_log_throttle.h:12-14; draw.cpp:2746, 2844, 3638 | `TakeLogBudget`: a relaxed load, then `fetch_add` only while under budget. It returns true for exactly the first N calls, as before | none |
| 6 diagnostics | draw_cached_flag.h:13-22; draw.cpp:437-438 (`TimingEnabled`, `PortraitProbeOn`), 445 (`DrawTimer(preparation)`), 479 (`ConstantTimer`: `TimingEnabled() && !t_preparing_draw`), 2481, 4760; long_probe.h:29-31 | Each process-constant flag is cached in a constant-initialised atomic byte (0 off, 1 on, 2 unread). Off costs one byte load and one predictable branch: no init guard, no call | none: the underlying flags were already process-constant statics |
| 4 TLS accessors | draw.cpp:128, 135, 142, 319, 427 (`Select_g_*(preparation)` overloads); 886 and 2461 (one `CurrentDrawPreparation()` per function) | The `g_*` macros resolve through the hoisted pointer. `t_draw_preparation` cannot change inside a draw.cpp function | low |
| 1 QueryDrawScope | queries.cpp:40 (counter), 114 (BEGIN), 125 (END, only while `queries` still maps to this query), 211 (Release), 230 (lock-free fast path, acquire), 234 (re-check under the lock), 311 (Reset) | The counter is maintained under `mutex`. The O(n) `none_of` walk is gone | low-med |
| AVX2 fallback | draw.cpp:3861, 3921, 3955 (`#if defined(__AVX2__)` … `#else` SSE2) | The AVX2 branch is the original text. The SSE2 branch makes identical bytes | none |
| Elision | draw_state_shadow.h; draw.cpp:583-653 (helpers), 2867 (lookup), 2947 (blend guard), 3549 and 3576 (index-buffer guards) | §S2.5 | opt-in only |
| Diagnostic columns | state_call_diagnostic.h:18-23, 26-37, 81-102, 150-172; draw.cpp:2671 (framebuffer), 2986-2991 (viewport, scissor) | Adjacent-equal counts plus elided-call counts | none (off by default) |
| Pacing hook (Agent 7) | draw.cpp:5344 | `HostDevice::PaceFrameBeforeLock()` between `PollCompletionCallbacks()` and `LockRecording()`. Reviewed: device.h:159-161, device.cpp:1855-1874 | none while `LEGO_NATIVE_UNLOCKED_PACING` is unset |

The session-2 diff vs `baseline/` is in `build/agent4/session2-diff.patch`. It is regenerated at the end of the session.

### S2.3 Verification

**Compile** (`env/compile-one.ps1 -Db build/dev/compile_commands.json -SyntaxOnly`, Release flags; logs in `build/agent4/compile/`):

| TU | `-march` | Result |
|---|---|---|
| draw.cpp, final (elision + pacing) | x86-64-v3 | exit 0; 71 warnings, all CRT `getenv` deprecation (`draw.pace.v3.log`) |
| draw.cpp with elision | x86-64-v2 | exit 0, 71 warnings (`draw.elide.v2.log`). Re-run at 20:05 on the final tree, with the pacing call: exit 0, 71 warnings, all CRT getenv deprecation (`draw.pace.v2.log`). `-PrintOnly` shows `-march=x86-64-v2` last on the line, so it overrides the database's `-march=x86-64-v3` |
| queries.cpp | x86-64-v3 | exit 0, 2 warnings |
| buffers.cpp, hooks_portrait.cpp, shaders.cpp, textures.cpp (long_probe.h includers) | x86-64-v3 | exit 0 |
| device.cpp (long_probe.h includer) | x86-64-v3 | exit 0 at 19:45 (`device.cpp.v3.recheck.log`). The earlier exit 1 was the then-missing generated `copy_color_ps.h` |

**Tests:**

| Test | Covers | Result |
|---|---|---|
| `bench/agent4/test_snapshot_simd.py --bench` | SSE2 vs AVX2 snapshot | PASS. v3 codegen identical to base (3,078 asm lines); SSE2 output byte-identical. AVX2 1,417 / 2,805 / 2,340 ns vs SSE2 2,870 / 4,525 / 3,426 ns (3 snapshot shapes) |
| `bench/agent4/run_fixtures.py` (26 gpu-aot fixtures) | everything they extract | Base and the final dev tree pass the **same** 9/26, with an identical failing set (re-run at 19:45, `build/agent4/fixtures-dev2/results.json`). The 9: buffer_variants, long_probe, portrait_probe, snapshot_selection, submission_waits, temporal_draw_route, texture_depth_upload, texture_source_residency, texture_use_refresh. The other 17 were already failing on base because their fakes are stale |
| `bench/agent4/fixtures/run_patched.py` (patched copies of test_constant_timing, test_query_sample_pool and test_query_retirement; see the README there) | items 6, 4, 1 | 3/3 PASS on base and dev (re-run at 19:45); 8/8 one-line mutants caught |
| `bench/agent4/test_state_call_diagnostic.py` | new ledger columns | PASS; negative control PASS |
| `bench/agent4/test_viewport_shadow.py` | viewport/scissor ledger | PASS |
| `bench/agent4/test_state_shadow.py` | elision (extracts draw.cpp:583-653 verbatim) | **OK: 20 runs, 19 audit checks.** 7/7 real cases, 13/13 mutants killed, 19/19 static audit checks |

`test_state_shadow.py` in detail (`build/agent4/state_shadow/results.md`):
- **Unit:** key changes; size, format and bitwise blend compares; gates. These cover the preparation gate, the full-preparation gate and the exact `"1"` parse.
- **Oracle:** 180,650 random draws against a simulated plume list, including:
  - list begin/end with serial bumps, layout and root-signature changes, SetDescriptorHeaps;
  - raw writers that call both plume notifies, or only one of them.

  The oracle checks that the D3D12 state the list ends up with, draw by draw, is the same as without elision. With elision on, 91,974 index-buffer and 92,479 blend calls were elided. With the variable unset, 0 were.
- **Negative controls:** these are contract violations (§S2.5), and the oracle must catch each one (exit 3):
  - the lookup moved after the layout bind;
  - a raw write with no notify;
  - a draw-layout rebind after a raw write.
- **Mutants**, all killed: no tripwire; ignore the serial; ignore both; no heaps check; no root-signature check; full-preparation gate removed; preparation gate removed; loose env parse; shadow ignores size; shadow ignores format; float (not bitwise) blend compare; Invalidate keeps blend; Begin ignores layout.
- **Static audit** of the live tree: every IB and blend writer in rexlego/src, and the plume begin/end/notify/flag semantics the tripwire relies on (list in §S2.5).

**Already-failing fixtures and the elision edit** (also in `bench/agent4/fixtures/README.md`): draw_index_bounds, shader_binding_failures and cull_state fail on base too. They now also meet `SameDrawIndexBuffer(draw_shadow, …)` and one more `CullDrawScissor(` use (draw.cpp:2988, the scissor diagnostic) in the extracted DispatchDraw text. Once their stale fakes are fixed, they need two stand-ins:
- `DrawStateShadow* draw_shadow = nullptr;`
- `template <class... A> bool SameDrawIndexBuffer(A&&...) { return false; }`

### S2.4 Numbers

Default path (`python bench/agent4/run_benches.py --runs 5`; `build/agent4/bench/results.md`). Other agents kept the CPU at 48-100% load, so absolute values are noisy. The before/after ratios are the result.

| Bench | Case | Before (ns) | After (ns) |
|---|---|---:|---:|
| log_throttle (3 sites per draw) | 1 thread | 34.2 | 1.75 |
| | 2 threads | 157.3 | 1.81 |
| cached_flag (5 flag calls + 20 LongProbe checks per draw) | per draw | 47.0 | 15.2 |
| | `TimingEnabled()`, one check | 2.35 | 0.68 |
| tls_accessor | no preparation: 12 → 3 accessor calls | 92.6 | 23.5 |
| | preparation: 14 → 3 calls | 82.4 | 37.2 |
| | for reference: 12 calls with Agent 7's inline accessor | — | 55.1 |
| query_scope | N=0 live queries, 1 thread | 44.0 | 2.50 |
| | N=16, 1 thread | 65.6 | 2.32 |
| | N=64, 1 thread | 164.9 | 2.13 |
| | N=256, 1 thread | 1,131 | 2.25 |
| | N=256, 2 threads | 2,476 | 2.35 |

The default path in isolation saves about **175 ns per draw** with no live queries (32 + 32 + 69 + 42), and more as live queries grow: up to 1.1 µs at N=256. That is about 0.18 ms of render-thread CPU per 1,000 draws. The in-game A/B (§S2.6, A1) decides the real figure.

Elision cost (`test_state_shadow.py` bench, ns per draw, median of 5; `build/agent4/state_shadow_bench_run1.md`). In this harness the two D3D12 calls are fakes costing about 1 ns.

| `LEGO_NATIVE_ELIDE_STATE_CALLS` | direct (no gate) | gated, repeated state | gated, changing state |
|---|---:|---:|---:|
| unset | 4.1 | 6.1 | 6.1 |
| 1 | 5.4 | 17.6 | 21.2 |

- **Off:** +2 ns per draw. The same direct code differs by 1.3 ns between runs, so this is at the noise floor.
- **On:** the shadow costs about 12-16 ns per draw more than the fakes. It pays off when each skipped real `IASetIndexBuffer` / `OMSetBlendFactor` (plume virtual call, D3D12 runtime, driver recording) costs more than about 6-8 ns. That cost is unmeasured.
- If the A/B is marginal, the conservative per-call re-check inside `SameDraw*` (`CheckInlineStateShadow`) can go. It is redundant today.

### S2.5 Redundant D3D12 state-call elision (STATUS decision 2)

**Scope.** Elision skips only:
- `setIndexBuffer` (draw.cpp:3550, 3577);
- `SetNativeBlendFactor` (draw.cpp:2948 → native_recording.cpp:534/542).

It applies only to inline draws: no `DrawPreparationContext`, full preparation off, and the list must be a `plume::D3D12CommandList` (`dynamic_cast`; prepared/tape lists bypass it).

These two states are safe to shadow for three reasons:
- plume caches neither of them;
- D3D12 keeps both until the list sets them again or is reset;
- PSO, root-signature and descriptor-heap changes leave them alone.

Layouts, PSOs, descriptor tables and framebuffers are left to measurement (CSV) and plume's own `PLUME_D3D12_STATE_CACHE`.

**Key.** The shadow is keyed on (command list, recording serial, pipeline layout). `DrawStateShadow::Begin` forgets every bound value when the key changes.

**Tripwire.** The tripwire reuses plume's own `descriptorHeapsSet`, `cachedGraphicsRootValid` and `cachedGraphicsRootSignature`.
- These are cleared by `begin()`, `end()`, `notifyCommandStateWasChangedExternally()` and `notifyDescriptorHeapWasChangedExternally()`. Binding another root signature replaces the cached one.
- They are checked at the lookup (draw.cpp:2867, before `BindNativeDrawLayout` re-validates them) and again in each `SameDraw*`.

**Required invalidation points**, as STATUS decision 2 asks:

| Event | Caught by |
|---|---|
| list begin/reset | serial in the key, and the plume flags |
| root-signature change | layout in the key, and the cached signature |
| SetDescriptorHeaps | `descriptorHeapsSet` |

**The serial is required, not defence in depth.** After a list reset, the first plume layout bind before the first draw makes the flags valid again. Without the serial the stale shadow would survive (mutant `ignore_serial`: killed at oracle step 698).

**Why one global shadow, not thread_local.** Every DispatchDraw caller without preparation records under `LockRecording` or `NativeRecordingMutex`, so they are serialized. Full preparation replays tapes onto the same list, so it is gated off.

**Contract limits.** The tripwire cannot see two cases:
- a raw D3D12 writer that sets the index buffer or blend factor and calls neither plume notify;
- a raw writer that notifies and then rebinds the draw layout through plume before the next draw.

The negative controls show the oracle catches both. The audit shows neither exists today:
- the only raw `IASetIndexBuffer` is native_overlay_gpu.cpp:176. device.cpp follows the overlay with both notifies, then `setFramebuffer(nullptr)`, the PRESENT barrier and `end()`, with no draw between;
- `OMSetBlendFactor` appears only in native_recording.cpp: tape replay (:322) and `SetNativeBlendFactor` (:542);
- the other raw passes notify plume afterwards (device.cpp:1568-1577, 2021-2027, 2067-2077; temporal_present.cpp:257);
- there is no `ClearState`, `ExecuteBundle` or `ExecuteIndirect`.

**Rule for future raw-D3D12 code on the frame list:** call `notifyCommandStateWasChangedExternally()` afterwards. A follow-up could add an explicit `InvalidateDrawStateShadow()` hook.

**Viewport/scissor.** These are diagnostic only this round. Eliding them needs hooks in the helper passes that set their own viewport (phase 2), and only if the CSV shows enough repeats.

### S2.6 In-game A/B plan

> [!NOTE]
> **Update at 20:05 (hidden-desktop rule).** Timing runs go through Agent 8's user-started runner; the rows are in §S2.10. A0 and A1 are not in it, because there is no baseline native ON exe.

Prerequisites:
- the NATIVE_GPU=ON dev exe and `build/baseline-bin`;
- Agent 3's boot procedure;
- the same save and a fixed camera path (or a static hub/menu scene);
- vsync off, the same resolution, FSR off;
- each measurement is the median of 5 runs × 60 s.

Never time with the CSV, `LEGO_NATIVE_TIMING` or the debug layer on. Those are correctness runs.

| Step | Run | Measure / compare | Pass |
|---|---|---|---|
| **A0** identity | dev vs base, default env. One extra run each with `LEGO_NATIVE_STATE_CALLS=<new file>` (it refuses to overwrite) | Screenshot diff; D3D12 debug layer; PIX one-frame API call list; CSV columns 1-16 per frame in a static scene | identical |
| **A1** default-path CPU | dev vs base, default env; then one run each with `LEGO_NATIVE_TIMING=1` | Frame time and render-thread CPU; per-draw timing | dev ≤ base. Expect about 0.1-0.2 ms per 1,000 draws |
| **B1** redundancy ratio (measure first) | dev, `LEGO_NATIVE_STATE_CALLS=<csv>` (optionally `_TRIGGER=<file>` to arm a chosen 120-frame window) | Per frame: `index_equal/index_calls` and `blend_equal/blend_calls` (the elision upper bound); also the `layout`, `pso`, `table0-3`, `framebuffer`, `viewport` and `scissor` `_equal` ratios for later rounds | Go to B3 only if index + blend repeats are a large share (≳30%) of those calls |
| **B2** plume cache (separate axis, not mine) | dev, `PLUME_D3D12_STATE_CACHE=1` vs unset | Frame time; plume prints "Plume D3D12 command state cache: enabled" | — |
| **B3** elision | dev, `LEGO_NATIVE_ELIDE_STATE_CALLS=1` vs unset; then one correctness run with the CSV, the debug layer and PIX | Frame time. `index_skipped ≤ index_equal` and `blend_skipped ≤ blend_equal`. PIX: every remaining call identical and in order; each missing call an exact repeat of the value already bound. Screenshot diff; debug layer | zero image diff, zero new debug-layer messages, win larger than run-to-run noise |

Elision stays OFF by default. Turning it on needs both B3 and an Agent 1 ruling.

### S2.7 Cross-owner status

- **Agent 7:**
  - the `PaceFrameBeforeLock()` call is applied and compile-checked;
  - the `CurrentDrawPreparation` inline diff was sent (device.h:93 becomes `extern thread_local` plus an inline accessor; device.cpp:756 is deleted). Agent 7 plans it for a batch after 20:15, as its item (h). Bench: 12 accessor calls 92.6 → 55.1 ns on its own; it stacks with the draw.cpp hoist.
- **Agent 5:** the registry diff was sent at 20:05 (§S2.9). It has:
  - (a) two exact one-line edits in `ResolveFramebuffer`. **Agent 5 applied it in batch 2**, at textures.cpp:3148 and 3155; I read the live lines at 22:02 and they match the diff. Agent 10's batch-2 review (22:14, [agent10-batch2-review.md](agent10-batch2-review.md) §9): SAFE and output-identical;
  - (b) a borrowed lookup for batch 2, with its lifetime contract. **Deferred**: there is no compile slot before the batch-2 cut-off. If it is picked up, it gets a new `LEGO_NATIVE_BORROWED_LOOKUP=1`, default OFF. Agent 5's extra conditions are in [agent5-uploads.md](agent5-uploads.md), "Agent 4's (b)": the pinned-owner path in `FindTexture`, `!NativeFullDrawPreparationEnabled()`, `LockRecording` held, no erase between lookup and use, and a mutant test that erases in between;
  - (c) and (d) as ideas.
- **Agent 8:** the run spec is §S2.10.
- **Agent 6:** its async-PSO hooks came as a patch at ~20:55 (`bench/agent6/draw-async.patch`). I rated them SAFE (default path identical) and applied them for batch 2 under #24 at 21:24:30. Details and hashes are in §S2.11. Agent 6 got the hashes at 21:47; Agent 10 reviewed the change under #25: SAFE at the default, SAFE-IF ON.

### S2.8 Not done

- Threaded items T1–T13 (§2): not started. Under #24 they wait for Agent 1's native timing data; the plan is §S2.12.
- Item 8 (the SetTexture flag hoist, hooks_state.cpp): not started.
- The per-call cost of real D3D12 `IASetIndexBuffer` / `OMSetBlendFactor`. It would size the elision win before the in-game A/B.

### S2.9 Registry diff for Agent 5 (textures.cpp, resource_registry.h)

Sent at 20:05. Agent 5 owns both files, so nothing here is applied.

**Cost of one registry hit.**
- Bench: `bench/agent4/registry_lookup_bench.cpp`, built against the real resource_registry.h, with 6 hot entries in a 2,054-entry registry. Results are in `build/agent4/bench-registry/results.md`.
- The machine was at 100% CPU load (Agent 2's build), so the absolute values are high; compare the ratios.
- The bench's unit tests check that the borrowed variant returns:
  - the same object as `Lookup`;
  - null for an absent address and after an erase;
  - the new owner after a replace at the same address.

| Case | ns per lookup: median of 5 (run medians) |
|---|---|
| 1T `Lookup` hit (`weak_ptr::lock` + release) | 91.0 (70.1-254.3) |
| 1T borrowed hit (raw pointer, same validation) | 17.2 (14.8-62.2) |
| 2T `Lookup` hit, both threads on the same entries | 206.9 (137.7-218.6) |
| 2T borrowed hit, same entries | 26.5 (20.1-31.3) |

**Hits per draw** (default path, one colour target plus depth): at least 4 hits and one shared_ptr copy, which is 10 locked RMWs.
- draw.cpp:2610 and 2615: `ResolveTextureResource` → `AdoptTexture` → `FindTextureAtUse` → `FindTexture`, one hit per target. Surfaces return early at textures.cpp:518.
- textures.cpp:3085 and 3092 (`ResolveFramebuffer`): one more hit per target.
- textures.cpp:3099: the `owner` copy.
- Each sampled texture adds 1-2 hits (`FindTextureAtUse`).

**(a) Exact and identical; any batch.** This removes the `owner` copy (2 locked RMWs per draw), and on draws without depth, a cross-TU call.

```diff
@@ textures.cpp:3092 @@
-  const auto depth = FindTexture(depth_stencil);
+  const auto depth = depth_stencil ? FindTexture(depth_stencil) : std::shared_ptr<TextureResource>{};
@@ textures.cpp:3099 @@
-  const auto owner = depth ? depth : colors[0];
+  const auto& owner = depth ? depth : colors[0];
```

Why it's identical:
- `FindTexture(0)` already returns `{}`. `FindPinnedOwner` returns `{}` for address 0 (device.cpp:757), and so does `Lookup` (resource_registry.h:51).
- `depth ? depth : colors[0]` is an lvalue of type `const std::shared_ptr<TextureResource>`, so the reference binds directly to `depth` or `colors[0]`.
  - Neither is moved or reassigned before the function returns (3100-3135).
  - 3132 still copies into `g_framebuffer_owners`.
  - `depth` and `colors` keep the object alive until the same point as before, under the same recording lock.

**(b) Batch 2, needs your lifetime proof: `LookupBorrowed`.** A new member next to `Lookup`, with its own TLS array, so `Lookup` stays byte-identical:

```cpp
  // Borrowed hit: takes no reference. Only for callers that exclude every writer of this
  // registry (emplace, erase, operator[], clear) for as long as they use the pointer.
  Resource* LookupBorrowed(uint32_t address, std::mutex& mutex) {
    if (!address) return nullptr;
    static const bool enabled = [] {
      const char* value = std::getenv("LEGO_NATIVE_RESOURCE_LOOKUP_CACHE");
      return !value || value[0] != '0';
    }();
    struct Borrowed { uint64_t registry = 0, generation = 0; uint32_t address = 0; Resource* raw = nullptr; };
    static thread_local std::array<Borrowed, 128> entries;
    const uint32_t hash = (address ^ (address >> 12) ^ (address >> 23)) * 0x9E3779B9u;
    auto& entry = entries[hash >> 25];
    const auto version = BucketVersion(address);
    if (enabled && entry.registry == identity_ && entry.generation == version && entry.address == address)
      return entry.raw;
    std::lock_guard lock(mutex);
    const auto found = Base::find(address);
    if (found == Base::end()) return nullptr;
    if (enabled) entry = {identity_, version, address, found->second.get()};
    return found->second.get();
  }
```

When it's safe:
- **Writers.** Every `g_textures` eraser holds `g_textures_mutex`, and all but one also hold `LockRecording`:
  - 1893: its callers hold it, per the comment at 495;
  - 3206: taken at 3201;
  - 3300: taken at 3277;
  - 3860: its callers take it at 3903 and 3921.
- **The exception** is the full-preparation deferred release at 3250-3254. A worker task erases there under `g_textures_mutex` only. So a borrowed pointer is safe only under `LockRecording` **and** with `!NativeFullDrawPreparationEnabled()`.
- **Same-thread erases.** A borrowed pointer is valid only until the same thread calls anything that can erase:
  - `FindTextureAtUse` → `RefreshTextureResourceHeader` (1893);
  - `PrepareTextureResource` → a pool-copy invalidation (3860).
- **Preparation mode.** Only when `!CurrentDrawPreparation()`; otherwise `FindTexture` returns pinned owners first.
- **`find()` is public.** Check that no site assigns through a `find()` iterator, which would skip `Advance`. 3859 moves out of `it->second` but erases right after, under the same lock, so it's fine.

First candidate: the hit path of `ResolveFramebuffer`'s locked section (3080-3107).
- Nothing between the lookups and `owner->framebuffers.find` can erase.
- Use borrowed pointers for the key and the hit. On a miss, fall through to today's shared lookups.
- Saves 2 hits (4 locked RMWs) per draw with depth, on top of (a).

**(c) Idea: pass the owners resolved in draw.cpp to `ResolveFramebuffer`.** This isn't identical as it stands:
- resolving RT1 can retire RT0 (3860);
- `FindTextureAtUse` can return null where `FindTexture` returns the stale record.

It would need `g_textures.Generation()` (resource_registry.h:35, bumped by every write) to be unchanged since the resolve, plus a null check, and a draw.cpp half from me.

**(d) Idea: a per-thread framebuffer memo.** Key it on:
- the render targets and the depth stencil;
- `g_textures.Generation()`;
- a framebuffer generation, bumped by `InvalidateFramebufferReferences` and by every `framebuffers` erase.

On repeat draws, it skips every lookup in `ResolveFramebuffer`.

### S2.10 Run spec for Agent 8's runner

Everything here needs the **native ON build** (S1, about 21:00-21:15). The OFF builds don't contain this code.

**Timing rows.** These run only in the runner the user starts; agent-launched runs are on a hidden desktop. Never time with the CSV, `LEGO_NATIVE_TIMING` or the debug layer on.

| Row | `-Env` | Runs |
|---|---|---|
| T0 control | none | 5 (or the matrix's native-default row) |
| T1 elision (B3) | `LEGO_NATIVE_ELIDE_STATE_CALLS=1` | 5 |
| T2 plume cache (B2, plume's axis) | `PLUME_D3D12_STATE_CACHE=1` | 5 |
| T3 both (optional) | `LEGO_NATIVE_ELIDE_STATE_CALLS=1;PLUME_D3D12_STATE_CACHE=1` | 5 |

- **Order.** Interleave the rows (T0 T1 T2 T3, five times) so drift hits each row alike.
- **Window.** Use the matrix's warm-up and window. Run uncapped (`-Toml framerate_limit=0`) if the matrix has such a row.
- **Enabling.** Only exactly `1` enables either variable. Plume reports its cache only on stderr ("Plume D3D12 command state cache: enabled"), not in game.log.
- **Read:**
  - from perf.csv (`frame_summary.py` over the window): frame time median and p99, and mean fps;
  - from proc.csv: mean `cpu_cores` over the window. Under a frame cap, a draw-path win shows up here.
  - For each row, take the median over its 5 runs. The T0 spread (min..max of its 5 runs) is the noise floor.
- **A win** counts only if T1 beats T0 by more than the T0 spread, with no `problems` in run.json and no new warnings or errors in game.log. Elision stays OFF by default until F2 is clean and Agent 1 rules.

**Functional rows.** These count calls, so the hidden desktop is fine; one run each.

| Row | `-Env` |
|---|---|
| F1 redundancy (B1) | `LEGO_NATIVE_STATE_CALLS=<run>\state_calls.csv;LEGO_NATIVE_STATE_CALLS_TRIGGER=<run>\state_calls.trigger` |
| F2 elision correctness (B3) | F1's, plus `;LEGO_NATIVE_ELIDE_STATE_CALLS=1`, with a new CSV path |

- **Trigger.** Create the trigger file at the measure start, like the profile trigger.
  - The game deletes it at the next present, writes 120 frames, then stops.
  - It never overwrites an existing CSV, and writes nothing if the trigger never appears.
- **CSV:** one `#` line, a header line, then one row per frame. The columns are `frame,draws,dropped_draws,recordings,layout_calls,layout_equal,pso_calls,pso_equal,table0_calls,table0_equal,...,table3_equal,framebuffer_calls,framebuffer_equal,index_calls,index_equal,index_skipped,blend_calls,blend_equal,blend_skipped,viewport_calls,viewport_equal,scissor_calls,scissor_equal`.
- **F1 read:**
  - Σ`index_equal`/Σ`index_calls` and Σ`blend_equal`/Σ`blend_calls` over the 120 rows. This is the elision ceiling; T1 is worth timing only if it is ≳30%.
  - The other `_equal/_calls` ratios are for later rounds.
  - `dropped_draws > 0` means that frame had more than 4,096 draws, so its counts are partial.
- **F2 read:** on every row, `index_skipped ≤ index_equal` and `blend_skipped ≤ blend_equal`. game.log has nothing new compared with F1.
- **Scene.** The numbers describe whatever scene the runner reaches (title or menu).

**Not in the runner: A0 and A1** (dev vs base for the default-path items). Those changes are unconditional and no baseline native ON exe exists, so their evidence stays the microbenches (§S2.4). An in-game check would need a second native ON exe built with the base draw.cpp, queries.cpp and long_probe.h.

### S2.11 Batch 2 (task #24): Agent 6's async-PSO hooks

Agent 6 owns the async compile code (`pipeline_async.h`; design in [agent6-async-pso-design.md](agent6-async-pso-design.md)). Its draw.cpp hooks came to me as a patch, and I applied it unchanged. The path is opt-in: `LEGO_NATIVE_PSO_ASYNC` is unset by default, and only a non-empty value other than `0` enables it.

| File | sha256 | Bytes | Lines |
|---|---|---|---|
| draw.cpp before: S1 (`build/agent2/snap1/MANIFEST-S1-2041.tsv`), also Agent 6's `build/agent6/draw_async/draw.orig.cpp` | `751C219EA5CCCD2F54E095412F0E8EB9B028EE21BC438CE9BC7B7CC40C1F0A99` | 304,444 | 5,719 |
| `bench/agent6/draw-async.patch` (1 file, 7 hunks, +48/−14) | `56D686EB1BC4D88B81F2B9582D31B6DF479B3AB3AC225C74D69A1F1A80DE47A4` | — | — |
| draw.cpp after (written 21:24:30), also Agent 6's `build/agent6/draw_async/draw.cpp` | `50AA3B1DEE61567838076EDF19CB7A5466727C3CC31BE3A80E6DCC3722D7BDD6` | 306,221 | 5,753 |

**How it was applied** (no git writes):
1. Checked the hashes of the live draw.cpp (`751C219E…`) and the patch (`56D686EB…`).
2. `build/agent4/scratch/apply_check.py` applied the patch in memory to the live file: 7 hunks, +48/−14, all 5,753 lines CRLF. The result hashed to `50AA3B1D…`, the same as Agent 6's patched file.
3. Saved the old file as `build/agent4/scratch/draw.before-b2.cpp`.
4. Wrote Agent 6's patched bytes over the live file with `[IO.File]::WriteAllBytes`, behind hash guards. `Copy-Item` would have kept the 20:04 mtime, and ninja could then skip the rebuild.
5. `git -C DimensionsRecomp apply --check -R ../bench/agent6/draw-async.patch` exits 0, so the whole patch is present.
6. Reviewer diff: `build/agent4/batch2-draw.patch` (`git diff --no-index`, 6,819 bytes, sha256 `04EA913EF661FA6CACF93F21F30BAAAE373A014ADD31EA0CF93BDFC8E9BB2B7F`). It is the same change as Agent 6's patch; only the file headers differ.

**Hooks** (batch-2 draw.cpp lines):

| Hook | Line |
|---|---|
| `#include "gpu_native/pipeline_async.h"` | 3 |
| comment and `g_async_pipelines` | 425-426 |
| `FinishPipeline`: the post-create checks, moved out of `GetPipeline` unchanged | 1670-1689 |
| `GetPipeline` miss: the toggle read, the two in-flight joins, `owners = CurrentShaderOwners()` | 1698-1714 |
| `CompilePipelineAsync` branch | 1855-1863 |
| synchronous path, now calling `FinishPipeline` | 1864-1875 (call at 1870) |
| `ResetDrawResources`: `DrainAsyncPipelineJobs()` before `g_pipeline_mutex` | 5714 |
| `g_async_pipelines.Clear()` | 5727 |

**Default path (toggle unset).** My review, checked against Agent 6's design §4-§5:
- A pipeline-cache hit runs the same code as before.
- A miss (a pipeline compile, which takes milliseconds) adds a call to `AsyncPipelineCompileEnabled()` (a cached static bool; the first call does one `getenv`, with no allocation and no log), two tests of the local `async`, and one empty `ShaderBindingsSnapshot`. `g_async_pipelines.Find` isn't called.
- The synchronous compile, its timing counters and the insert into `g_pipelines` are unchanged. `FinishPipeline` keeps the old checks, logs and log counters.
- Nothing starts a thread or allocates while the toggle is unset.
- Teardown: `DrainAsyncPipelineJobs()` runs before `g_pipeline_mutex` is taken, because posted compiles publish under that mutex, so it can't deadlock. With no jobs it returns at once, and `g_async_pipelines.Clear()` clears an empty table.

**Agent 10's review** (#25, 21:47; [agent10-batch2-review.md](agent10-batch2-review.md) §5-6) agrees:
- The applied hunks are exactly Agent 6's patch, with nothing else. Its own `-SyntaxOnly` on the live draw.cpp: exit 0, 77 warnings.
- SAFE at the default.
- SAFE-IF on. The condition: the process exits through `HostDevice::Shutdown`. The async runtime and its threads are never deleted, so a compile still running at an exit that skips Shutdown could touch `g_pipelines` after static destruction. This affects only exits, and only with the toggle on.

**Verification** (live tree, 21:25-21:36):

| Check | Result | Compared with before |
|---|---|---|
| compile-one, full `-c`, v3 (database flags) | exit 0, 78.0 s, 77 warnings (all `-Wdeprecated-declarations`), object 2,038,734 B in `build/agent4/obj/b2-v3/` | base had 71; the 6 new ones are `getenv` deprecations in `pipeline_async.h` (4) and `pipeline_stats.h` (2) |
| compile-one, full `-c`, v2 (`-Extra "-march=x86-64-v2"`) | exit 0, 72.4 s, the same 77 warnings, object 2,023,354 B in `build/agent4/obj/b2-v2/` | as v3 |
| syntax-only check of Agent 6's copy before applying (`build/agent4/scratch/precheck_async.ps1`) | v3 and v2 exit 0, 77 warnings each | — |
| `run_fixtures.py` | 9/26 (`build/agent4/fixtures-b2/`) | `compare_fixtures.py` against `fixtures-dev2`: the same passing and failing sets |
| `test_state_shadow.py --no-bench` | OK, 20 runs, 19 audit checks (`build/agent4/state_shadow-b2/`) | same |
| `fixtures/run_patched.py` | 3/3 on base and dev | same |
| Agent 6's `async_table_test` (Agent 6's run, 20:44) | 17/17 | — |

The compile checks used the live tree, which already has Agent 7's #20 `device.h` change (the inlined `CurrentDrawPreparation`).

**Line shift for §S2.1–§S2.10.** Outside the hunks, an S1 line L is now at L + shift:

| S1 lines | Shift |
|---|---|
| 6-420 | +1 |
| 427-1663 | +3 |
| 1670 | +24 |
| 1683-1816 | +35 |
| 1844-5678 | +32 |
| 5685-5690 | +33 |
| 5697-5719 | +34 |

**In-game A/B.** This is Agent 6's P5 row ([agent6-runspecs.md](agent6-runspecs.md)): P1 (`pso-cold`) against P5 (`;LEGO_NATIVE_PSO_ASYNC=1`), both cold, with `;LEGO_NATIVE_PSO_STATS=1`.
- It needs a native ON build from batch 2. The S1 native build doesn't have the hooks.
- With the toggle on, `FRAME_METRICS pipeline_creations` doesn't count async compiles, so read the "PSO async" and "compiles by thread" lines.
- A draw that is skipped while its pipeline compiles takes the null-pipeline path, so also check the screenshots for missing geometry during warm-up.

#### Batch 3 (task #12, applied 03:34:59): the §S3.2 hash=0 guard

Agent 1 approved the fix as task #12 (02:47) and gave GO at 03:35, after Agent 10 rated it SAFE (03:31, [agent10-batch2-review.md](agent10-batch2-review.md) §13). It is my own patch; the cause, the fix and the safety argument are in §S3.2. It changes only the threaded preparation paths (N2/N3). The default serial path never calls `PrepareDrawGeometry`.

| File | sha256 | Bytes | Lines |
|---|---|---|---|
| draw.cpp before: batch 2 (above), also DimensionsRecomp HEAD `001336f`; saved as `build/agent4/scratch/draw.before-s32.cpp` | `50AA3B1DEE61567838076EDF19CB7A5466727C3CC31BE3A80E6DCC3722D7BDD6` | 306,221 | 5,753 |
| `build/agent4/s32/draw-s32.patch` (1 file, 1 hunk `@@ -1496,6 +1496,11 @@`, +5/−0) | `F54343258029F89A47BDBCC1392461B0B79686219A804A7FAE9473CF51852387` | 787 | — |
| draw.cpp after (written 2026-11-22 03:34:59), also `build/agent4/s32/draw.cpp` | `5EA1F3576DCC2F90C7CBE410CFCDE093CB39D170A2BDD6259C3A85B41BE14410` | 306,557 | 5,758 |

**How it was applied** (no git writes), with `build/agent4/s32/apply_live.ps1`. Its `-DryRun` passed at 03:16 and 03:31.
1. Checked the live hash (`50AA3B1D…`) and the patched copy's hash (`5EA1F357…`).
2. Saved the live file as `build/agent4/scratch/draw.before-s32.cpp` and re-hashed the backup.
3. Re-checked the live hash, then wrote the patched bytes with `[IO.File]::WriteAllBytes`. The write gives the file a new mtime, so ninja rebuilds it.
4. Re-hashed the live file: `5EA1F357…`, 306,557 B, 5,758 CRLF line ends. Lines 1499-1503 are the guard.
5. `git apply --check -R build/agent4/s32/draw-s32.patch` (read-only, in DimensionsRecomp) exits 0, and `git diff HEAD --numstat` shows `5 0 rexlego/src/gpu_native/draw.cpp`.

**Verification.** The written bytes are the bytes that step 1 compiled and tested on scratch copies (§S3.2 table): v3 and v2 full `-c` exit 0 with the same 77 warnings as batch 2; only `PrepareDrawGeometry` changed in the objects; fixtures 9/26 (SAME as batch 2); state shadow OK; `run_patched.py` 3/3. The in-game check passed: native3d's n0/n2/n3 log 0 hash=0 lines, and n2/n3 pass `check_n_rows.py` (§S3.2, step 3). Agent 1 committed the file as game `08933a7` (pushed).

**Line shift.** Batch-2 lines 1-1498 are unchanged; lines 1499-5753 are now at L + 5. §S3.2 cites batch-2 numbers.

### S2.12 T1–T13 plan (task #24 part 2; waits for native timing data)

Not started. Agent 1 sends the native timing data first; until then this is a plan only.

**Scope.** Every T item is on a path that is off by default, so none of them can move the default numbers. T13 is a compile-time check only.

| Path | Enabled by | Default |
|---|---|---|
| Threaded recording (`NativeWorkerEnabled`, native_worker.cpp:319-323; logs "Native GPU: threaded recording ON/off") | `LEGO_NATIVE_THREADED`, exactly `1` | off |
| Preparation workers (`NativePreparationWorkerCount`, native_recording.cpp:521-527) | `LEGO_NATIVE_PREPARE_THREADS`, clamped to 0-8 | 0, off |
| Full draw preparation (native_recording.cpp:497-503) | `LEGO_NATIVE_FULL_DRAW_PREPARATION=1` plus preparation workers | off |
| Snapshot state bindings (state.cpp:100-106) | `LEGO_NATIVE_SNAPSHOT_STATE=1` | off |
| Parallel draws (`NativeParallelDrawsEnabled`, draw.cpp:5572; logs "Native draw batches: parallel\|serial workers=N") | preparation workers, `LEGO_NATIVE_PARALLEL_DRAWS` not `0`, retained draw state (on by default), snapshot state, and no trace toggles | off |

**Data I need** (any native ON build; the T paths are the same in S1 and batch 2):
- **Functional rows**, one run each (the hidden desktop is fine). For each, check the startup lines above and that game.log has no new errors or warnings:

  | Row | `-Env` |
  |---|---|
  | N1 threaded recording | `LEGO_NATIVE_THREADED=1` |
  | N2 parallel draws | `LEGO_NATIVE_THREADED=1;LEGO_NATIVE_PREPARE_THREADS=2;LEGO_NATIVE_SNAPSHOT_STATE=1` |
  | N3 full draw preparation | `LEGO_NATIVE_THREADED=1;LEGO_NATIVE_PREPARE_THREADS=2;LEGO_NATIVE_FULL_DRAW_PREPARATION=1` |

- **Launch** (Agent 1, 21:56; updated 23:50): Agent 8 holds the game slot. Native-bin's first boot crashed at 23:16 (§S2.13), so every native run now needs `-Cvar native_settings_frontend=false`. Agent 1 (23:48): Agent 8 runs N1-N3 before 00:05 if they fit, otherwise right after window 3. The commands I sent Agent 8 at 23:50 (functional only; `-Frames native` also sets `LEGO_NATIVE_FRAME_METRICS`). native2-bin is preferred because window 3's n0 uses it; native-bin works too:

  ```
  powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\run-timing.ps1 -BinDir build\agent2\native2-bin -WarmupFrom firstframe -Warmup 30 -Seconds 60 -Frames native -Cvar native_settings_frontend=false -Tag n1-threaded -Env 'LEGO_NATIVE_THREADED=1'
  ... -Tag n2-parallel -Env 'LEGO_NATIVE_THREADED=1;LEGO_NATIVE_PREPARE_THREADS=2;LEGO_NATIVE_SNAPSHOT_STATE=1'
  ... -Tag n3-fullprep -Env 'LEGO_NATIVE_THREADED=1;LEGO_NATIVE_PREPARE_THREADS=2;LEGO_NATIVE_FULL_DRAW_PREPARATION=1'
  ```

  Or use Agent 8's `matrix-native-functional.json` with that cvar added to n1-n3 (and f1/f2): `run-matrix.ps1 -Matrix bench\agent8\run\matrix-native-functional.json -NoPrompt -Only n1,n2,n3`.

  Expected in game.log: all three print `Native GPU: threaded recording ON (LEGO_NATIVE_THREADED=1)` and, every 600 presents, `Native worker: last 600 frames tasks=…` (draw.cpp:5455). `Native draw batches:` (draw.cpp:5581) should print `serial workers=0` (N1) and `parallel workers=2` (N2). N3 prints no batches line, because the full-preparation path never calls `NativeParallelDrawsEnabled()`. This plan first said `serial workers=2` for N3, which was wrong (§S3.1); N3 is identified by its thread names instead. **Result (S3, 02:19):** N1 passes every check. N2 and N3 pass every check except one new warning type, the hash=0 shader cache miss (§S3.1, §S3.2).
- **Timing rows** (the user-started runner only, in a later window; not window 4): N0, N1 and N2 as arms n0, th1 and th2, 4 runs each, round-robin, no cold run. N3 (th3) is dropped until the §S3.2 fix, and th2 is provisional until then. The matrix is [matrix-native-threaded.json](../bench/agent4/matrix-native-threaded.json) (S3: `1F8BC5DD…C581`), in Agent 8's format. Every arm runs on `build/agent2/native2-bin` with cvars `native_settings_frontend=false native_fps_limit=0 framerate_limit=0` (uncapped) and the `drivers/thread-cpu.ps1` driver. That driver writes the busiest-thread busy % (threads.csv, headroom.json) and NVML GPU utilisation (gpu.csv), which is what rule 2's GPU-bound test needs. Every arm reads `"frames": "perf"` (§S3.3), and the 60 s window starts 60 s after the first frame. `-PlanOnly` passes: 12 runs, about 37 min (40-41 min expected; §S3.4). Read them as in §S2.10: frame time median and p99, mean fps, mean `cpu_cores`, plus the busiest thread's busy %.
- **A sampled profile** of the best N row from Agent 8's analyser, if one exists, with per-thread sample counts.

**Decision rules:**
1. If no N row beats N0 by more than N0's spread, threaded mode can't become a default. Do T13 only. With the S3 matrix (4 round-robin rounds), an arm beats n0 only if its mean fps beats n0's in all 4 rounds and its median frame time is below n0's lowest median (§S3.4). If every row is frame-locked, judge by mean `cpu_cores` and p99 instead of the median frame time. Matrix 1's OFF builds sat at 16.66 ms in every run, and there `cpu_cores` is much noisier: base ranged 1.91-2.29 over its 6 runs ([summary.md](../build/agent8/matrix/20261121-2232/summary.md)).
   - Window 3's n0 (native2-bin, 4 scored runs): 6.71 ms (6.55..6.87), spread 4.8%. It read `native-frames.csv` and used a 50 s window from 35 s, so it is for orientation only. The bar comes from the S3 matrix's own n0.
2. If the frame is GPU-bound in the N rows, stop.
   - Window 3's n0: GPU 43–50% on average (max about 55%), with the top thread "Main XThread" 74–77% busy. So n0 is not GPU-bound in the title loop. The N rows still need their own check.
3. Otherwise, do an item only if its code is at least ~0.5% of the hottest thread's samples.
4. T10 also needs Agent 12's critical-region review and its own default-off toggle.

**Order** (draw.cpp first, smallest first; batch-2 lines):

| Step | Item | Where | Owner |
|---|---|---|---|
| 1 | T13: assert that the queued draw lambdas fit `std::function`'s small buffer | `static_assert` at 3941; lambdas at 5176 and 5204. Check `NativeWorkerSubmitCapture`'s parameter type first | me |
| 2 | T7: move the device snapshot instead of copying it | the two queued-hook lambdas, 5176-5217. `copy` is still used by the fallbacks after `CaptureParallelDraw`, so re-anchor first | me |
| 3 | T12, draw.cpp part: `[batch = std::move(batch)]` | 5601 | me; the preparation_footprint.h:30-36 part needs a grant |
| 4 | T6: fill the chunk jobs in place | 4564 (`reserve`), 4569 (`PreparationDependencyFilter`) | me |
| 5 | T8: a last-key memo in front of the thread_local maps | 4697-4700 (`memos`); 4924, 4941-4942 (`captured_pairs`) | me |
| 6 | T1: per-thread magazines for `SnapshotBlockAllocator` | 3838; `pool.mutex` at 3854 and 3871; `SnapshotDevice` 3886; `SnapshotDrawDevice` 3945 | me |
| 7 | T9: move out, copy, move back in `ParallelDrawWork` | 4951-4954, 5023-5027 | me |
| 8 | T10: one critical-region acquisition per draw | `CopyNativeGuestMetadata` at 4810 (per captured texture) and 5228 | me, after Agent 12's review; default off |
| 9 | T2, T4, T5 | native_worker.cpp. T4 also covers completion_queue.h, native_preparation.h and the two deques in draw.cpp (4260 `g_inflight_batches`, 4315 `batches_`) | needs a grant or patches |
| 10 | T3, T11 | native_preparation.h, native_recording.cpp (T11 at 306-309) | needs a grant or patches |

**For each item:**
- compile v3 and v2 with compile-one, full `-c`;
- fixtures stay at 9/26 with no new failures; state shadow and `run_patched.py` unchanged;
- a bench where the item can be measured (at most 2 threads, median of at least 5 runs, before and after): `snapshot_pool_bench` for T1 (1 producer and 1 consumer, not §2's 1+3) and `ring_vs_deque_bench` for T4;
- identity in threaded mode: N1/N2 functional runs with and without the change give the same game.log, FRAME_METRICS and, where the capture works, state-call CSV columns 1-16;
- re-anchor this table, because each edit moves the lines below it.

No benches, tests or compiles run during Agent 1's quiet windows.

### S2.13 Native first boot crash (23:16): not draw.cpp; workaround `native_settings_frontend=false`

Agent 8's native first boot (`build/agent8/runs/2315-native`, native-bin) died before the first frame: `[FATAL] Unhandled exception 0xE06D7363` on the UI thread, right after `Native write tracking: …` (device.cpp:918, the end of `HostDevice::Create`). Agent 7 found the same cause independently (`perf-notes/agent7-present.md`).

- **Decode.** I wrote two read-only scripts, `build/agent4/scratch/dump_cxx.py` and `dump_cxx2.py`. They read the WER full dump `legodimensions.exe.93080.dmp`: the exception record and the MSVC throw info, then a stack scan symbolised with the exe's .map. Output: `build/agent4/scratch/dump-2315-native-{1,2}.txt`.
- **Thrown type:** `std::runtime_error` (catchables `runtime_error`, `exception`).
- **Stack:** settings_registry.cpp `ReadRegistryValues` ← `MakeNativeRegistryBackend` read lambda ← gpu_native `CaptureBackend` ← `SettingsRevisionCoordinator::State` ← `NativeSettingsRuntime::NativeSettingsRuntime` ← `LegodimensionsApp::OnPreLaunchModule` (legodimensions_app.h:156, taken only when `native_settings_frontend` is true).
- **Message.** The what() heap block isn't in the dump. The frame still holds:
  - an empty `raw` string;
  - a key string_view of length 31;
  - the 65-character message string, which is 34 for `"Native setting is not registered: "` plus 31 for `present_fsr_sharpness_reduction`.

  That matches the string Agent 7 found: `Native setting is not registered: present_fsr_sharpness_reduction`.
- **Cause.** rexui is built without `REX_HAS_FIDELITYFX_SDK`, so rexglue-sdk presenter.cpp:43-78 registers only a bilinear-only `present_effect`, and not `present_fsr_*`. The runner's toml (a copy of `game/legodimensions.toml`) sets `native_settings_frontend = true`.
- **Workaround:** `--native_settings_frontend=false` (in a matrix arm: `"cvars": ["native_settings_frontend=false"]`). Window 3's n0 uses it, and so do all arms of my matrix since 23:50.
- **Not mine to fix.** The SDK define belongs to Agent 7/Agent 2. draw.cpp isn't involved.

---

## Session 1 analysis (12:xx; line numbers are from before the session-2 edits)

Every estimate below is a reasoned guess. Each item lists the measurement that would settle it.

Paths are relative to `DimensionsRecomp/rexlego/src/gpu_native/` unless stated. Source tags:
- **[A4]**: I read the lines myself.
- **[S1]**: diagnostics subagent.
- **[S2]**: worker-pipeline subagent.
- **[S3]**: state-hooks subagent.

S-tagged line numbers are unverified unless I also mark them [A4].

---

## 0. What actually runs per draw by default [A4 + S2]

| Switch | Where | Default |
|---|---|---|
| `LEGO_NATIVE_THREADED=1` → `NativeWorkerEnabled()` | native_worker.cpp:319-327 | **off** |
| `LEGO_NATIVE_FULL_DRAW_PREPARATION=1` (+ `LEGO_NATIVE_PREPARE_THREADS>0`) | native_recording.cpp:497-527 | **off** |
| `LEGO_NATIVE_SNAPSHOT_STATE=1` → `SnapshotStateBindingsEnabled()` | state.cpp:100 | **off** |
| `NativeParallelDrawsEnabled()` | draw.cpp:5389-5402 | **off** (needs the switches above) |
| `RendererOptimizationMask` bits | renderer_optimizations.h:14-25 | all off [S2] |
| `LEGO_NATIVE_QUEUED_GET`, `LEGO_NATIVE_DEFERRED_RELEASE` (`EnvSwitch`) | native_worker.cpp:484-499 | **on** (on unless set to `"0"`) [A4] |

**Default hot path:** `DrawVerticesHookQueued` / `DrawIndexedVerticesHookQueued` → `Draw*Hook` (draw.cpp:4966-4985) → `HostDevice::LockRecording()` → `PassProfileScope` → **`DispatchDraw` runs inline on the guest render thread** (draw.cpp:2366-~3560).

So the threaded machinery (snapshot pool, capture, preparation queues, recorder) costs roughly one cached static per draw by default. Items in §2 matter only if threaded mode becomes the default.

> [!WARNING]
> No code in rexlego sets the `LEGO_NATIVE_*` switches. I did **not** check launchers, `.bat` files or configs outside rexlego. Confirm which mode the shipped build runs before you prioritise §1 over §2.

---

## Summary ranking (expected win per draw, default path first)

| # | Opportunity | Where | Est. win / draw | Risk | Owner can act alone? | Session 2 |
|---|---|---|---|---|---|---|
| 1 | QueryDrawScope takes a mutex and walks every live query on **every draw** | queries.cpp:219-229; call sites draw.cpp:3373, 3381, 3441, 3467, 3476 [A4] | 25 ns to 0.5 µs (scales with live query count) | low-med | yes (queries.* is mine) | **done**: 44 → 2.5 ns (N=0), 1,131 → 2.3 ns (N=256) |
| 2 | Resource lookups: `weak_ptr::lock` plus shared_ptr release, two locked RMWs each, ~10-25 per draw | resource_registry.h:50-70 [S3]; DispatchDraw 2517-2528 + texture slots [A4] | 100-400 ns (if the link holds) | med | **no**: callers are in textures.cpp | diff sent to Agent 5 (§S2.9) |
| 3 | Redundant layout / descriptor / PSO / framebuffer calls | draw.cpp:546-564, 2578-2580, 3270/3274 [A4] | unknown, up to 100-300 ns | med | needs measurement + Agent 1 ruling on "identical" | **opt-in done** for index buffer + blend factor (§S2.5); the rest: measure with the CSV first |
| 4 | `Select_g_*` accessor macros: out-of-line call + TLS + init guard on each of 56 uses | draw.cpp:122-138, 310-314, 417-421 [A4] | 30-150 ns | low | yes, by hoisting (an inline accessor needs the device.cpp owner) | **done** (hoist): 92.6 → 23.5 ns; inline accessor is Agent 7's item (h) |
| 5 | Unconditional log-throttle `fetch_add` on every draw (2 locked RMWs; 3 if instanced) | draw.cpp:2654, 3525, 2752 [A4] | 10-25 ns (much more when contended) | ~none | yes | **done**: 34.2 → 1.75 ns (1T), 157 → 1.8 ns (2T) |
| 6 | Diagnostics that cost more than one branch when off | draw.cpp:425, 463, 2390; long_probe.h:27 [A4/S1] | 10-20 ns | none | yes | **done**: 47.0 → 15.2 ns per draw |
| 7 | Threaded path: snapshot allocator mutex, `call_once`, notify under lock, deque allocations, extra `notify_all`, shared_ptr copies, capture maps, global critical region per captured texture | §2 | large in threaded mode, ~0 by default | low-med | mostly yes | not started |
| 8 | State hooks: repeated flag evaluation in SetTexture | hooks_state.cpp:25-56, 252-268 [S3] | a few ns per call | low | yes | not started |
| 9 | **Build note:** AVX2 intrinsics compiled in unconditionally vs the x86-64-v2 baseline | draw.cpp:3741-3754, 3792-3836 [A4] | n/a (correctness) | n/a | yes | **done**: SSE2 `#else`; v2 compiles, v3 codegen identical |

**Do-first order when builds return (cheapest and safest first):** 5 → 6 → 4 → 1 → 8 → 7 → 2 (with the textures.cpp owner) → 3 (after measuring and a ruling).

---

## 1. Default-path opportunities

### 1.1 QueryDrawScope: a mutex plus an O(live queries) walk on every draw

- **Where:**
  - QueryDrawScope is built once per issued draw [A4]: `QueryDrawScope query_scope(commands, query_sample_scale);` at draw.cpp:3373, 3381, 3441, 3467 and 3476 (alternative draw branches).
  - Constructor body, queries.cpp:219-229 [S3]:
    ```cpp
    std::lock_guard lock(mutex);
    if (std::none_of(queries.begin(),queries.end(),
        [](const auto& entry) { return entry.second->active; })) return;
    ```
- **What is slow:** even when no query is active, every draw:
  - locks and unlocks `mutex`;
  - walks `std::unordered_map<u32, shared_ptr<Query>> queries` (queries.cpp:36);
  - pays two dependent loads per entry (node, then `Query`).
  
  With a query active it also does a `make_unique`, a shared_ptr copy per consumer, a second lock with a linear `sample_pool` scan, and a lock plus `emplace_back` in the destructor (queries.cpp:225-287 [S3]).
- **Proposed change** (keep the lock, make the test O(1)):
  ```diff
   // queries.cpp, next to `queries` (~36)
  +size_t active_queries = 0;  // guarded by mutex: number of entries in `queries` with active == true
   // QueryDrawScope::QueryDrawScope (~221)
     std::lock_guard lock(mutex);
  -  if (std::none_of(queries.begin(),queries.end(),
  -      [](const auto& entry) { return entry.second->active; })) return;
  +  if (!active_queries) return;
  ```
  Keep the counter in step under `mutex` at every active transition of an object **that is in `queries`** [S3 lines]:
  - **+1** at ~105-109 (`queries[address] = std::move(next)` with `next->active = true`). Decrement first if the replaced object was still active.
  - **-1** at ~116-117 and ~202-203, only on a true→false change, and only when `queries.find(address)->second == query`. An in-flight END can hold a query that `ResetQueryResources` has already dropped.
  - **= 0** at ~300 (`queries.clear()`).
  
  Phase 2, optional and medium risk: an atomic copy of the counter read before taking the lock. It skips the mutex entirely when nothing is active. This is safe on the inline path, where BEGIN/END and draws come from the same guest thread in program order. `ReleaseQuery` takes no recording lock in full-prep+queue mode, so the threaded paths need a separate argument.
- **Risk:** low-medium. The bookkeeping must be exact or query results change. The hazard is a race between ReleaseQuery and IssueQuery in threaded mode [S3].
- **Verify:**
  1. Size the win first: log `queries.size()` and the active count once per frame in a normal level.
  2. Bench `bench/agent4/query_scope_bench.cpp`: `none_of` vs counter for N ∈ {0, 16, 64, 256} live entries, median of 7 runs, `-march=x86-64-v2`.
  3. Correctness: in a debug build, assert `active_queries == count_if(active)` inside the scope constructor and run a level that uses occlusion queries. Diff the per-frame query results against the old build.

### 1.2 Per-draw resource lookups: two locked RMWs per lookup (needs the textures.cpp owner)

- **Where:**
  - DispatchDraw calls `ResolveTextureResource` five times for colour/depth (draw.cpp:2517-2524) and `ResolveFramebuffer` once (2528) [A4].
  - Each bound texture slot adds two more lookups (vsync notes / [A4]).
  - The likely backend is `ResourceRegistry::Lookup`, resource_registry.h:50-70 [S3]:
    ```cpp
    static thread_local std::array<Entry, 128> entries;      // direct-mapped, hash >> 25
    if (auto owner = entry.owner.lock()) return owner;       // :63  lock cmpxchg on the control block
    std::lock_guard lock(mutex);                             // :65  miss path
    ```
- **What is slow:**
  - Every hit costs `weak_ptr::lock()` (a locked CAS loop) plus a locked decrement when the returned `shared_ptr` dies.
  - The control-block line bounces when the recorder and the worker touch the same texture.
  - A miss costs the mutex, a hash find and two more atomics.
  - The 128-entry direct-mapped table makes hot textures that collide evict each other.
- **Proposed change:** describe only; the callers are in textures.cpp, which is not mine.
  - (a) A non-owning `Resource* LookupUnowned(key)` for callers that run under the recording lock, where retirement is deferred to fence completion (descriptor_retirement.h). Lifetime must be proven per caller.
  - (b) Memoise the five colour/depth resolves between draws, keyed on the bound addresses plus a registry generation counter bumped on every insert or retire.
  - (c) 2-way associativity for the TLS cache.
- **Risk:** medium (lifetime proofs).
- **Verify:**
  - Confirm that `ResolveTextureResource` → `ResourceRegistry::Lookup`.
  - Count lookups per draw.
  - Bench `bench/agent4/registry_lookup_bench.cpp`: `weak_ptr::lock` + release vs a raw pointer, with 1 and 2 threads touching the same entries.
  - Fixture `test_resource_registry`.

### 1.3 Redundant D3D12 state calls (measure first; needs a ruling)

- **Where [A4]:**
  - draw.cpp:546-564: the bind helper issues `setGraphicsPipelineLayout`, four `setGraphicsDescriptorSet` calls (tables 0-3) and `setPipeline` per draw.
  - draw.cpp:2578-2580: `commands->barriers(...)` and `setFramebuffer` on every draw.
  - draw.cpp:3270 / 3274: the motion pass sets `motion_fb` / `motion_pipeline`, then restores `framebuffer` / `pipeline`. The restore may be redundant if the next draw rebinds anyway.
- **What is unknown:** whether plume already filters equal-state calls. The plume sources are not in the tree (the rexglue-sdk/thirdparty submodule is not checked out).
- **Proposed change:** none until measured.
  - `state_call_diagnostic.h:19-66` already counts adjacent-equal layouts, PSOs and tables per guest draw: CSV columns `layout_equal`, `pso_equal`, `table0_equal`..`table3_equal`, written at Present by `NativeStateCalls()` (draw.cpp:533-541, 2564, 5201).
  - Its own header warns that *equal requests are not a D3D skip proof*.
  - Any elision must reset the cached last-layout/PSO/tables on:
    - a new command list;
    - a change of recording or serial;
    - a root-signature change (tables are invalidated, as the ledger does at :41);
    - any external plume user (FSR or compute passes, `External` tape commands).
- **Ruling needed from Agent 1:** dropping a call whose state is equal changes *the call stream* but not GPU state. The brief says "what reaches D3D12 must be IDENTICAL", yet it also lists redundant calls as a target. Decide which wins.
- **Verify:**
  1. `LEGO_NATIVE_STATE_CALLS=1` on a fixed scene gives the redundancy ratio, i.e. the upper bound on the win.
  2. If elision is allowed: compare a PIX capture of one frame before and after; every non-elided call must be identical and in the same order.

### 1.4 `Select_g_*` accessor macros: 56 TLS round-trips

- **Where [A4]:** draw.cpp:122-138, 310-314, 417-421.
  - `#define g_quad_indices Select_g_quad_indices()` and the same for `g_vertex_bindings`, `g_vertex_input_usage`, `g_prepared_draw` and `g_draw_timing`.
  - Each accessor does:
    ```cpp
    if (CurrentDrawPreparation()) { static thread_local T state; return state; } return g_..._serial;
    ```
  - `CurrentDrawPreparation()` is out of line (device.cpp:752); it reads `thread_local t_draw_preparation` (device.cpp:751).
  - The function-local `static thread_local` with a non-trivial constructor adds a TLS init-guard check.
- **What is slow:** every one of the 56 uses pays a call, a TLS access and possibly a guard. On the serial (default) path the call still happens. `DrawTimer`'s constructor runs `++g_draw_timing.calls` on every draw (draw.cpp:429-436; deliberate, for the cadence probe; keep it).
- **Proposed change (draw.cpp only):** in `DispatchDraw` and the other hot helpers, resolve each accessor once and use a local reference:
  ```diff
   void DispatchDraw(...) {
  +  auto& vertex_bindings = g_vertex_bindings;      // context cannot change inside this call
  +  auto& vertex_input_usage = g_vertex_input_usage;
  ...
  -  g_vertex_bindings.<field> = ...;
  +  vertex_bindings.<field> = ...;
  ```
  - **Why it is safe [A4]:** only device.cpp writes `t_draw_preparation` (751 defines it; 765 restores `previous_` in a scope destructor). So the selected object is fixed for the body of any draw.cpp function, which gives identical object identity.
  - Lower-churn alternative for the device.cpp owner: make `CurrentDrawPreparation()` inline by exposing `extern thread_local DrawPreparationContext* t_draw_preparation;` in the header. That removes the call from all 56 uses with no edits in draw.cpp.
- **Risk:** low. The one trap: a hoisted reference must not be used inside a lambda that runs on another thread or later. Check every hoist site for lambdas that capture by reference.
- **Verify:**
  - Bench `bench/agent4/tls_accessor_bench.cpp`: macro pattern vs hoisted reference vs inline accessor, median of 7.
  - Fixtures `test_draw_preparation`, `test_full_draw_pipeline`.
  - Agent 3's compile check of draw.cpp.

### 1.5 Unconditional log-throttle atomics on every draw

- **Where [A4]:**
  - draw.cpp:2654 `if (depth_state_logs.fetch_add(1) < 32)`: every DispatchDraw.
  - draw.cpp:3525 `if (issued_draw_logs.fetch_add(1) < 8)`: every submitted draw.
  - draw.cpp:2752 `if (instanced_logs.fetch_add(1) < 16)`: every instanced draw.
  
  The other `fetch_add` throttles (680, 778, 1681, 1739, 1882, 1964, 5151, 5297, 5367) are on failure or rare paths. 3569 `clear_sequence` is a real ID, not a throttle; leave it.
- **What is slow:**
  - A `lock xadd` on a static global, forever, long after the 8, 16 or 32 log lines were printed.
  - When `DispatchDraw` runs on several preparation threads (threaded mode), the cache line also ping-pongs between them.
- **Proposed change:**
  ```diff
   static std::atomic<u32> depth_state_logs{0};
  -if (depth_state_logs.fetch_add(1) < 32)
  +if (depth_state_logs.load(std::memory_order_relaxed) < 32 && depth_state_logs.fetch_add(1) < 32)
  ```
  Apply the same change at 3525 (`< 8`) and 2752 (`< 16`).
- **Risk:** none for rendering.
  - The first N log lines are identical.
  - Only difference: today the u32 counter wraps after 2^32 draws (about 10 h at 120k draws/s) and re-prints N lines. After the change it never re-prints.
  - Tell Agent 1 this log-only difference exists.
- **Verify:**
  - Bench `bench/agent4/log_throttle_bench.cpp`: old vs new, 1 and 4 threads.
  - Diff the log of a short run.

### 1.6 Diagnostics: make "off" one predictable branch

| Site | Off cost today | Change | Notes |
|---|---|---|---|
| `DrawTimer` ctor, draw.cpp:425 (once per draw, constructed at 2371) | out-of-line `NativeTextureTimingEnabled()` | `static const bool` cache in draw.cpp | Verified process-constant [A4]: textures.cpp:1478, `static const bool` from `_dupenv_s("LEGO_NATIVE_TIMING")` |
| `ConstantTimer` ctor, draw.cpp:463 | TLS read of `t_preparing_draw` + out-of-line call | `TimingEnabled() && !t_preparing_draw` | Both operands are side-effect free; result identical [S1] |
| `PortraitProbeEnabled()`, DispatchDraw ~2390 | out-of-line call per draw | local `static const bool portrait = PortraitProbeEnabled();` | Verified process-constant [A4]: hooks_portrait.cpp:57-62 = static env flag `&&` `LongProbeEnabled()` |
| `LongProbeEnabled()`, long_probe.h:27 (per texture slot at draw.cpp:1054 [S1], plus others) | guarded static `filesystem::path` + `.empty()` | `inline bool LongProbeEnabled() { static const bool enabled = !LongProbeDirectory().empty(); return enabled; }` | The directory is immutable after first use; check long_probe.h:18-27 has no setter |
| `PassProfileScope`, draw.cpp:3661 | guarded `Get()` + `capturing` load + branch | **no change** | `capturing` toggles at runtime. The dtor already early-outs at 3663 [A4], so off = guard + one branch |
| `NativeFsr3Enabled()`, fsr3_settings.cpp:128 | out-of-line seq_cst load (a plain `mov` on x86) | **no change** | A live setting: caching it would change behaviour when FSR mode toggles |
| `NativeStateCalls()`, draw.cpp:533-541 / 2564 | guard + pointer load + null check | none | fine |
| `BeginCpuDrawDiagnostic`, 2255-2272 / `TraceMeshDraw`, 2274 | static session, empty-trigger check / static bool | none | fine |
| `SlowNativeOperation`, slow_operation.h:16-56 | guard + branch, plus ~10 dead member stores | optional: initialise `names_`, `times_` and clocks only `if (active_)` | Only matters if it is constructed per draw (call sites not checked) [S1] |
| `pass_profile::End`, gpu_pass_profile.h:64-66 | `Get()` guard before the `index == ~0u` test | optional reorder | Unreachable when off via PassProfileScope (3663) [A4] |

Code for the first two rows:
```diff
+namespace { bool TimingEnabled() { static const bool enabled = NativeTextureTimingEnabled(); return enabled; } }
-  bool enabled = NativeTextureTimingEnabled();                        // :425
+  bool enabled = TimingEnabled();
-  bool enabled = !t_preparing_draw && NativeTextureTimingEnabled();   // :463
+  bool enabled = TimingEnabled() && !t_preparing_draw;
```

- **Note [S1]:** a function-local `static const bool` still costs a thread-safe-init guard check (MSVC: a TLS epoch compare), so it is not strictly one branch. A namespace-scope constant-initialised flag has no guard, but it moves the `getenv` to static-init time. Only do that if nothing calls `_putenv` / `SetEnvironmentVariable` at runtime (not checked).
- **Risk:** none. The only effect is that the first `NativeTextureTimingEnabled()` call can move slightly earlier.
- **Verify:**
  - Compile check plus diff review.
  - Run once with `LEGO_NATIVE_TIMING=1` and `LEGO_NATIVE_LONG_PROBE*` set, and check the timing and probe output still appears.
  - Unchecked: whether `REXLOG_*` skips argument evaluation when its level is off (rex/logging.h was not read). If it does not, gated log calls on hot paths may still format.

---

## 2. Threaded-path opportunities (matter only with `LEGO_NATIVE_THREADED=1` and friends)

All of these come from [S2] unless marked. I spot-read 3693-3731 and 4130-5045 earlier [A4].

| ID | Where | What | Proposed change | Risk |
|---|---|---|---|---|
| T1 | draw.cpp:3706-3728 (`SnapshotBlockAllocator`) [A4+S2] | One global `pool.mutex`, taken about 2× per draw: allocate on the game thread, free on coordinator, prep or reclaim threads | Per-thread magazine of 32 blocks; batch transfers under one lock; return leftovers in a thread_local destructor. Snapshot bytes are fully overwritten (comment at 3734), so the choice of block cannot change output | low-med |
| T2 | native_worker.cpp:397 (+412, 427) | `std::call_once` on every submit (an out-of-line call on MSVC) | `if (g_started.load(std::memory_order_acquire)) return;` before it (`g_started` is release-stored at the end of the once-lambda, :350) | low |
| T3 | native_preparation.h:59, 75; native_recording.cpp:164 | `notify_one` while still holding the lock | Notify after unlocking; the predicate is still changed under the mutex | low |
| T4 | native_worker.cpp:51, 56; native_preparation.h:20; draw.cpp:4133; completion_queue.h:27 | MSVC `std::deque` with elements over 8 bytes allocates on every push and frees on every pop, inside `g_queue_mutex` | Ring buffer that keeps its capacity (vector + head + count, growth preserves order) | low-med |
| T5 | native_worker.cpp:147 | `FinishRecorderTask` calls `notify_all` on `g_queue_progress` every batch, waking a throttled game thread for nothing | `if (task.present) g_queue_progress.notify_all();`. Every waiter is in that file (376, 523, 543, 568, 579); check each | medium |
| T6 | draw.cpp:4387, 4406-4407 | 2.6 KB `PreparationDependencyFilter` zeroed and copied per chunk; `task` shared_ptr copied twice | `emplace_back` and fill in place; move `task` into the lambda (`reserve` at 4382 prevents reallocation) | low |
| T7 | draw.cpp:4677 / 4711; 4999 / 5028 | Extra shared_ptr copy of the device snapshot | Move from `drawn.device` / `snapshot.device` (not into `CaptureParallelDraw`; the fallbacks at 5013 and 5037 still use it) | low |
| T8 | draw.cpp:4515-4523 (`memos`), 4742-4765 (`captured_pairs`) [A4] | Per-capture lookups in a `static thread_local std::unordered_map` | Last-key → pointer memo, reset with `.clear()`, or a direct-mapped array | low |
| T9 | draw.cpp:4769-4785, 4841-4845 [A4+S2] | Full `ParallelDrawWork` copies (`work->draw = capture_template.draw` and back), copies of the `pinned` vector of shared_ptrs, `ShaderBindingsSnapshot` copied twice | Move out the members that are reset straight after the copy; copy; move back | medium |
| T10 | draw.cpp:4628 (+5046) [A4] | `CopyNativeGuestMetadata` takes the **emulator-wide** `global_critical_region::AcquireDirect()` (guest_metadata.h:19 [S3]) once per captured texture | One acquisition per draw for all textures. That holds the lock longer, and a racing guest write could be observed differently, so prove it is acceptable first | medium |
| T11 | native_recording.cpp:306-309 | `External` wraps a 64-byte `std::function` inside another lambda, so it always heap-allocates | Push the command, then a separate `ResetReplayState` entry; playback order is unchanged | low-med |
| T12 | draw.cpp:5418; preparation_footprint.h:30-36 | Copy of `[batch]` at its last use; redundant range re-add | `[batch = std::move(batch)]`; early return when an existing range already contains the new one | low |
| T13 | draw.cpp:3788 `static_assert(sizeof(DrawSnapshot) <= 32)` [A4] / [S2 F9] | The draw lambdas (DrawSnapshot + four u32 = 48 B) exactly fill MSVC's `std::function` small buffer: the *lambda* must be ≤ 48 B (56 B minus the vptr). The existing assert bounds only DrawSnapshot, not the lambda | Name the lambda and add `static_assert(sizeof(capture) <= 48 && std::is_nothrow_move_constructible_v<decltype(capture)>)`, so any growth fails to compile instead of silently heap-allocating per draw | none |

**Verify** (once threaded mode is exercised):
- Benches `bench/agent4/snapshot_pool_bench.cpp` (global mutex vs magazine, 1 producer + 3 consumers) and `bench/agent4/ring_vs_deque_bench.cpp`.
- Fixtures `test_device_snapshot_pool`, `test_full_draw_pipeline`, `test_native_preparation`, `test_preparation_dependencies`, `test_preparation_physical_wait`, `test_temporal_worker`, `test_snapshot_bindings`.
- For T1, T6-T11: diff the tape contents or the PIX call list before and after.
- For T2-T5: count lock and allocation calls (ETW or VTune).

---

## 3. State hooks [S3; flag defaults checked by A4]

- **hooks_state.cpp:252-268, 25-56 (SetTexture):**
  - Today each call evaluates `NativeWorkerShouldQueue()` 3× and `SnapshotStateBindingsEnabled()` 2×, takes `LockRecording` when not queueing, and runs `RefreshTextureHeader`.
  - Hoist the two flags once per call; both are static-cached, so this is safe.
  - Equal-value calls **cannot** be skipped: `MergeTextureFetch` and `RefreshTextureHeader` have guest-visible effects.
- **hooks_state.cpp:139-165 (GetRenderTarget / GetDepthStencil):** the full `NativeWorkerDrain()` runs only when `NativeQueuedGetEnabled()` is false. That switch is **on by default** [A4: `EnvSwitch` at native_worker.cpp:484-488 is on unless set to `"0"`]. `NativeWorkerDrain` also returns immediately when the worker never started (native_worker.cpp:508). **Not an issue by default.**
- **state.cpp:19-56:** every `Bind*` takes `g_bindings_mutex`. It is uncontended in inline mode. No edit: skipping equal stores would need single-thread proof.
- **hooks_shader.cpp:81-130 (AddRef/Release; not mine):** up to four `IsNative*` lookups per call. A combined classification lookup is the possible fix; tell that file's owner.
- **No SetRenderState, SetSamplerState or `Set*ShaderConstant` hooks exist.** Those writes go straight into the guest device shadow. Their cost lands in DispatchDraw: the 8 KB `CopyBigEndianDwords` constant swap (draw.cpp:504) and BindConstants.

---

## 4. Build / correctness note for Agent 1 (not a perf item)

- `SnapshotDevice` (draw.cpp:3741-3754) and `SnapshotDrawDevice` (3792-3836) use `_mm256_*` (AVX2) unconditionally. rexlego/CMakeLists.txt:840 defaults to x86-64-v3, but BRIEF's baseline is **x86-64-v2, no AVX without CPUID dispatch**.
  - clang at `-march=x86-64-v2`: draw.cpp will not compile.
  - MSVC: it compiles, but faults with #UD on a CPU without AVX when the threaded snapshot path runs.
- Fix: a 128-bit SSE2 version (byte-identical result) or CPUID dispatch.

---

## 5. Looked at and left alone [A4]

- **Pooled work items:** `FullDrawWork` / `ParallelDrawWork` keep their vector capacity, and `g_full_draw_batch.reserve(limit)` is present.
- **Gated diagnostics:** the `std::set`, `std::to_string` and `std::ostringstream` uses at 2416, 2823, 3244, 3505, 3521, 3531, 5116 and 5203 are all behind diagnostics flags or once-only sets. `LongProbeEvent` formats only when enabled.
- **Bounded statics:** `logged_stencil` (2632) stops after 32 entries.
- **Already one cheap branch:** `BeginCpuDrawDiagnostic`, `TraceMeshDraw` and `NativeStateCalls`.
- **Memory order:** no edits needed. seq_cst loads are plain `mov`s on x86, and no per-draw seq_cst store was found [S2].
- **Possible false sharing:** `g_recorder_*` (native_worker.cpp:60) shares one line, but it is touched once per batch, so it was not worth it [S2].

---

## 6. Verification plan once a build exists

1. **Compile:** Agent 3's harness on draw.cpp and queries.cpp after each item.
2. **Fixtures (standalone, `build/agent4`, `ninja -j4`):**
   - test_blend_state, test_descriptor_retirement, test_device_snapshot_pool, test_draw_preparation, test_full_draw_pipeline, test_instanced_fetch
   - test_native_preparation, test_polygon_offset, test_preparation_dependencies, test_preparation_physical_wait, test_resource_registry
   - test_sampler_state, test_snapshot_bindings, test_temporal_worker, test_vertex_fetch_plan, test_d3d12_support
   
   The `*_sdk` / `*_gpu` variants need the SDK or a GPU.
3. **Microbenches (`bench/agent4`, `-march=x86-64-v2`, median of 7 runs):** query_scope, registry_lookup, tls_accessor, log_throttle, snapshot_pool, ring_vs_deque.
4. **D3D12 identity:** same save and scene before and after.
   - (a) `LEGO_NATIVE_STATE_CALLS=1`: the CSV must match exactly.
   - (b) A one-frame PIX capture: the API call list (calls, order, arguments) must match.
   - (c) Screenshot diff.
5. **CPU win:** `LEGO_NATIVE_TIMING=1` per-draw timing plus frame time over a fixed camera path, median of 5 runs, compared with the baseline build.

---

## 7. Not read / not verified

- **draw.cpp:**
  - 480-2366 (helpers, BindConstants, PrepareDrawGeometry*, PrepareDrawWork, pipeline creation and `g_pipelines` lookup under `g_pipeline_mutex` at ~1581/1772, CpuDrawDiagnostic). [S1] read 1-1200 for diagnostics only.
  - 2700-3656 apart from spot checks at 2740-2760, 3510-3535, 3656-3673 and grep hits: pipeline lookup, constants upload, vertex/index binding, draw issue, clears.
- **Other gpu_native files:**
  - native_worker.cpp and native_recording.cpp: only what [S2] read.
  - hooks_state.cpp, state.cpp and queries.cpp bodies: [S3] only.
  - The `ParallelDrawWork`, `ShaderBindingsSnapshot` and `DrawBindings` definitions.
  - memory_watch call sites; draw_work_pool.h (partial, [S2]); preparation_*.h and physical_*.h headers apart from what [S2] touched.
- **Outside gpu_native:**
  - textures.cpp: `ResolveTextureResource`, `ResolveFramebuffer`, `RegisterSampler` (mutex per sampler slot), `RefreshTextureHeader`.
  - device.cpp: `LockRecording` cost.
  - `CurrentCaptureStamps` callees (7 per draw in threaded mode [S2]).
  - **plume sources** (submodule absent), so plume's own redundant-call filtering is unknown.
  - `rex/logging.h` (whether disabled `REXLOG_*` still evaluates arguments).
  - Launchers and configs that may set `LEGO_NATIVE_*`.
- **Nothing was measured.** All per-draw figures above are estimates.
