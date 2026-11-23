# Agent 7: native present, frame pacing and submission (tasks #6, #13, #20, #22, #26, #29 and #33; board run 2: #9, #19 and #30)

> **RESUME (23:34, board run 2). Re-read this first after any restart.**
> - **Task #17 (Agent 1, 22:04): #21 S4-T1 `LEGO_NATIVE_CHAIN_PRIORITY`, staged for Agent 10's rating on Monday morning so W8b can run Monday night. DONE ~23:00, paths sent to 10/9/8/1.**
>   - Rules: staging only (no builds, compiles, game runs or git writes); stop at 23:50 or on HOLD.
>   - Index: `build/agent7/s4-t1/README.md`.
>   - Files: RATE-REQUEST.md, s4-t1.diff (rev 2, +51/-0), SHA256SUMS.txt, before/, after/, make_s4t1.py (proofs 1-6), FUNCTIONAL-ROWS.md, matrix-s4t1-f1/f3.json, matrix-w8b-draft.json, queue-s4t1.jsonl, check_rows.py, and check/ (DIFF-REVIEW.md, MP4-STATIC.md, verify_diff.py).
>   - Rev 2 (22:48) fixed review S1: an inline hook and wrapper in native_preparation.h, plus a static Impl and installer in native_worker.cpp. After hashes: worker `071E2F4B...`, recording `00F03D84...` (unchanged), preparation `88C57831...`; diff `46FFD2E9...`.
>   - Checks (22:48): make_s4t1 ALL PROOFS PASS; check_rows ALL CHECKS PASS; git apply --check forward 0, -R 0, negative 1. The S1 fix itself had no second review (my 1 subagent was used); the read-only reviewer's check/verify_diff.py predates it.
>   - **Morning:**
>     1. Agent 10's verdict. If it asks for changes: edit make_s4t1.py, re-run it, then check_rows, then the 3 git apply checks.
>     2. Agent 2's compile. N3 residual: look for -D_WIN32_WINNT in the native4b compile command.
>     3. After F1/F3 run: the MP2 proxy (perf.csv draws distribution, light share) and the MP3 (draws, samples) sequence comparison.
>     4. Fingerprint re-pin note to Agents 2 and 8.
>   - Agent 9 (23:12) pre-read S4-T1 (`build/agent9/s4-t1-preread.md`): all 4 checks pass, no changes asked. Optional: (P2) F1 starts cold where the bin dir has no `<exe dir>/cache` (native4b-bin): n0 r1 and th3old r1 cold, th3 r1 warm; fix = one warm-up run per bin dir, or read (b) on r2 only. (P1) stale line refs: FUNCTIONAL-ROWS L40/L42/L160, matrix L27/L108, DIFF-REVIEW L79/L83, RATE-REQUEST L86 (:14-21 is :15-22 in the after file); mapping in its §5. **Morning, before Agent 10 rates if possible.**
> - **#19 (Agent 1, ~22:29; the S4 candidate number, not a grid task): R1 stage 2 `d3d12_async_submit`, OFF, kInitOnly. Dir `build/agent7/s4-r1s2/`.**
>   - Deliverables: staged diff, RATE-REQUEST.md for Agent 10, functional rows, 10-min soak plan, W7's arms. Target: Monday ~09:00, so W7 can run Monday night. Stop at 23:50 or on HOLD; resume when Agent 1 wakes me after tonight's windows. Report to Agent 1 and send paths to 10 (cc 8, 9); no `@@done` (not a grid task).
>   - Base = S4b SDK = snap1 (`build/agent2/snap1/DimensionsRecomp/rexglue-sdk/`, order C1 v3, M1, P2c, r1r2, #26). cp.cpp is P2c + r1r2 (`027204B5...`), NOT s4-r1r2/new (`760833A5...`, no P2c).
>   - **Done (23:10-23:15):** `make_s4r1s2.py` (exact-once edits E1-E16) wrote `orig/` checks, `new/sdk/`, `s4-r1s2.diff` (+320/-1, sha `06B0D371...`), `SHA256SUMS.txt`, `PROOFS.txt` (P1-P10 ALL PASS). `CHECKS.txt`: git apply --check forward 0, -R 0, negative 1.
>   - Design: 3-slot FIFO; `MaybeSplitSubmission` calls `EndSubmissionAsync()` when on (swaps the deferred list into a slot via new `DeferredCommandList::Swap`); thread "D3D12 Submit" does Reset/Execute/Close/ExecuteCommandLists/Signal in order. Drains (all `if (submit_async_)`): EndSubmission top, CheckSubmissionFence's `>= submission_current_` branch, PublishOnDemandMemexport, ShutdownContext (`ShutdownAsyncSubmit`), UpdateTileMappings in shared_memory/texture_cache (`FlushAsyncSubmissions`). Plain fence waits not drained. Inert unless `d3d12_submit_split_kb > 0` (WARN if async on with split 0).
>   - **Done (23:20):** `NOTE.md` (design doc, after-file line numbers): files+hashes, switch, per-file changes, threading model, queue-op table (P5), non-draining waits, lifetimes, shutdown/failure, conditions S2-1..S2-7, log lines, risks 1-6. Key after-file lines: cp.cpp cvar L114-124, SetupContext L1936-1965, ShutdownContext L1971/L1974, EndSubmissionAsync L4483-4588, DrainAsyncSubmissions L4590-4605, AsyncSubmitThread L4607-4644, ShutdownAsyncSubmit L4646-4666; OnPrimaryBufferEnd sync submit L2633-2636 drains ~1x/frame (possible "stage 2b").
>   - **W7** = S4-DRAFT.md:391 ("s0 / #18 / #18+#19 / #18+#19+#20", 1+4x4 = 17 runs). #20 step 1 is only a counters macro on another bin (devoff4b-ctr-bin) and step 2 is not staged, so propose 3 arms on ONE bin `<DEVOFF4B-S4R1S2>` (devoff4b + s4-r1s2.diff): s0 `d3d12_submit_split_kb=0`, s18 split N, s19 split N + `d3d12_async_submit=true`, all + `framerate_limit=0`, `env {}` (no ENV-KEYS-F1 key needed) -> 1+3x4 = 13 runs ~33 min; optional 4th s19h (split N/2) -> 17 runs ~43 min.
>   - Agent 3's #18 rows in `build/agent3/s4b/queue.jsonl` (s4b10-16, s4b25; needs `ready-s4b-off`, `ready-N`, `ready-dbg`, `ready-s4b-ctr`, `ready-later`). **N not chosen yet** (`ready-N` gate, likely from s4b16 counters); fallback K ~2-4 submissions/frame from s4b10's `d3d12_submit_split` lines.
>   - **Next (morning), in order:** (1) ~~Agent 9's S4-T1 P1 line-ref fixes + P2 note~~ DONE 23:27 (FUNCTIONAL-ROWS L6-8/L36-42/L67-84/L171-172, matrix-s4t1-f1 L27/L108, matrix-w8b-draft L26, RATE-REQUEST L80/L86, DIFF-REVIEW rev-2 numbers + addendum L15-16, README "Update 23:27"; check_rows ALL PASS 23:26; no code/diff/hash change); (2) ~~FUNCTIONAL-ROWS.md + `queue-s4r1s2.jsonl`~~ FIRST DRAFT 23:33 (9 rows a, b, i, j, c, d, f, e, g; est sum 2470 s = 41 min; refs = Agent 3's S4b rows s4b01/10/11/13/15/25/L0 on devoff4b-bin; bin dir `build\agent2\devoff4b-s4r1s2-bin`; gate `ready-s4r1s2` + `ready-N` for split rows + `ready-dbg` for g; bincheck needles cp.cpp:1944/1956/4581; queue JSON parsed OK, citations verified 23:31). Morning: re-check busy/slow-state commands, row minutes, a tested counter-line checker; (3) ~~SOAK.md~~ FIRST DRAFT 23:35 (soak = row e, 600 s level-l toypad vs s4bL0, + row j; manual add-ons optional; pass rules 1-6); (4) ~~matrix-w7-draft.json~~ DONE 23:29 (`build/agent7/s4-r1s2/matrix-w7-draft.json`: s0/s18/s19 + optional s19h at <N/2>, all on `<DEVOFF4B-S4R1S2>`, W5 window fields + repeats 4, env {}; keys checked against run-matrix.ps1 L49-55 TopKeys/ArmKeys/QuickKeys, which reject unknown keys; ASCII only); (5) RATE-REQUEST.md (copy s4-t1 structure: §1 Candidate, §2 Files and apply, §3 Switch, §4 What changed, §5 OFF = today (P3/P4/P8/P10), §6 Threads (D3D12 Submit worker, queue-op table P5, drains), §7 Log lines, §8 Build checks (P1-P10, CHECKS, syntax pending), §9 Code-read items (device removal, EnsureHostGpuMemoryAllocated vs global lock, query hold), §10 Risks (NOTE 1-6), §11 conditions S2-1..7 / must-prove → rows, §12 W7 arms, §13 Open items (N, syntax, stage 2b), §14 Verdict asked) + ~~README.md~~ done 23:33; (6) optional read-only reviewer subagent (re-run make_s4r1s2.py + 3 apply checks; check no EnsureHostGpuMemoryAllocated caller holds the global lock); (7) send paths: 10 (cc 8, 9, 1); mention syntax check still needed and the `ready-N` dependency.
>   - Exact log lines (new cp.cpp): #18 INIT L1216 `d3d12_submit_split_kb: splitting submissions at {} KB of deferred commands`; #18 counter L4475 `d3d12_submit_split: frame= submission= splits= failed= held_query= held_scratch= held_pipelines=` (~10 s); #19 WARN L1944 `d3d12_async_submit: needs d3d12_submit_split_kb above 0, staying off`; INIT L1956 `d3d12_async_submit: submitting splits on the submit thread (3 slots)`; ERROR L1959 `... failed to create the submit thread, staying off`; counter L4581 `d3d12_async_submit: frame= submission= chunks= queued_max= full_waits= full_wait_us= drains_waited= drain_wait_us= worker_us=`; thread name "D3D12 Submit" L1954.

> **RESUME (20:45, board run 2). Re-read this first after any restart.**
> - **Task #14 (Agent 1, ~20:30): T-std read-out kit for tonight's windows W6-W10. DONE ~21:50.** Files: `build/agent7/w4b-noise/readout.py` (new; imports noise_methods.py and noise_case.py, which stay unchanged), `test_noise_methods.py` (adds synthetic readout tests and the W4b/W5 regression against RESULTS.md; `--no-regression` skips the latter), `repeats.py` and `REPEATS.md` (repeats note), `READOUT.md` (kit doc), outputs `readout-w4b.md/json` and `readout-w5.md/json`.
>   - Kit: reads any bench/agent8 matrix dir. Arms and ref come from matrix.json; `--ref` overrides. Any n per arm and any number of rounds. Cold, invalid and excluded runs are left out as in W4b/W5. Output: T-std and B-block T-std, with the round-terms nested F test on median ms deciding which applies (p < 0.05: B-block). Guards: (a) light-share F, (b) raw GM rows with CI agreement, (c) host-flag list with residuals. G11 per run, plus a summary that is OK, MIXED (with an `--overlay`/`--rounds` suggestion) or NO DATA.
>   - Regression: W4b and W5 rows must equal RESULTS.md verbatim (bold stripped). W4b decides B-block and W5 decides T-std. F = 0.40 on (3, 11) and F = 0.33 on (4, 10). Flag rows and residual means from noise-case.
>   - Repeats note **due 22:30**: CI half-width per arm for 3/4/5 repeats x 2-5 arms, from W5's T-std CV (median ms 2.1 %, df 10), with minutes from W5's wall times (cold slot ~1.86 min + ~2.13 min per scored run). Also the Best-performance formula and a guess range.
>   - Rules: read-only on build/agent8/matrix; python at Below Normal, one process at a time; no game runs, builds or git writes; HOLD check before every command; at most 1 read-only checker subagent. When done: path and command to Agent 8, `@@done 14` to Agent 1.
> - **Progress (21:08):** readout.py, repeats.py, READOUT.md and the test additions are written. Self-test: RESULT PASS, 0 failed (21:01-21:07; it took 6 min under load at Below Normal). One fix: the W4b round terms are -4.0 / -3.1 / -3.9 % in the kit's 100 (e^b - 1); RESULTS.md's "3.1-4.1 %" is 100 |b|. Same fit; the test checks both, and round_test json now has 'b'. Since then the test prints a count of checks (`N checks`), and repeats tests were added (synthetic, plus the W5 inputs in the regression).
> - **Checker: DONE, 0 mismatches** (subagent `5ce3ebb7-e95e-4cf8-8568-34dcba71421b`, read-only, started 21:12; report `build/agent7/w4b-noise/check-readout/CHECK.md`). Self-test 112/112 PASS in 59 s; re-runs identical except the command line; its own script: 133 checks pass (all 19 RESULTS.md rows verbatim; round F W4b 7.029 on (3, 8), p 0.0124, W5 0.239 on (2, 8), p 0.793; all 7 REPEATS tables; slots 111.274 / 128.666 / 119.650 s, 33.87 min; unflagged s 0.014685 on df 7; CV range 0.70-1.75). Its doc notes were fixed at 21:29 in READOUT.md (`--normal-priority`; the G11 states OK / MIXED / PARTIAL / NO DATA; `--rounds`/`--drop` values that match no run; noise_methods loads w4b_readout.py). Also at 21:29: REPEATS.md's minutes sentence says "by construction" (W5's 33.9 min is the fit's own input), and a new self-test check "W4b guard b: raw agrees".
> - **Final run (21:30-21:45):** repeats.py re-run (REPEATS.md and repeats.json, 21:34), then the self-test: RESULT PASS (113 checks, 0 failed), 898 s at Below Normal (the machine was loaded).
> - **Running:** nothing. The 22:15 fallback timer ended with the checker's report.
> - **Outputs (21:10-21:11):**
>   - `readout-w4b.md/json`: primary B-block T-std, F = 7.03 on (3, 8), p = 0.012; B fps +6.0 [+0.5, +11.8] *; G11 OK best_efficiency 17/17.
>   - `readout-w5.md/json`: primary T-std, F = 0.24 on (2, 8), p = 0.793; G11 OK 16/16.
>   - `REPEATS.md/repeats.json`, labelled W5. ± per arm on median ms: n=3 ±3.8 (6 arms) to ±4.9 (2 arms); n=4 ±3.2 to ±3.7; n=5 ±2.8 to ±3.1. Minutes = 1.70 + 2.14 x A n (W5 measured 33.9). CV range 0.70-1.75x. Best performance: formula plus a CV 1-3 % table.
> - Messages: `agy-send to=8` (path, command, how to read it), `agy-send to=1` (the repeats note, the kit summary, the round-terms convention) and `@@done 14` go out at the end of the ~21:50 turn. After that nothing is pending.

> **Previous RESUME (20:15, board run 2), superseded by the block above.**
> - **Task #6 (Agent 1) = old #30: DONE ~20:15.** Write-up: `build/agent7/w4b-noise/RESULTS.md` (answer, methods, W4b and W5 tables, noise cases, recommendation, caveats). Per-method tables: `results-tables.md` (written by `results_tables.py`). Also `noise_case.py` with `noise-case-w5.md` and `noise-case-w4b.md`, `report.md/json` (W4b), `report-w5.md/json` (W5), and the DESIGN.md section "Added after 'go' (19:32-20:10)".
> - Tests: `python -B test_noise_methods.py` gives RESULT PASS (44 checks). Two checker subagents, both done, found 0 mismatches in both windows (`check-phase/`, `check-bct/`). B-block consistency: W5 is balanced and its deltas equal T-std's; its CV equals B-norm's x sqrt(df_norm/8).
> - Recommendation: **T-std** (GM delta with pooled CI, df = runs - arms; median ms and fps primary, p99 and 1 % low noisier). Use **B-block T-std** when the round terms are large (in W4b, rounds 2-4 are 3-4 % faster than round 1). Guards: light share per arm (F), raw pooled CI, host-flag list. Not for the verdict: B-norm CI (too narrow), L/D (sensitivity only), A, A2, C.
> - Key numbers: W4b median-ms band raw 19.6 -> T-std 7.8 -> B-block T-std 3.6 %; CV 12.2 -> 2.3 -> 1.4 %. W5 band 20.4 -> 6.5 % (B-block 5.7); CV 6.5 -> 2.1 %. Leads: B about +6 % fps in W4b (B-block T-std CI [+0.5, +11.8]); S4a 1-2.5 % slower (n.s.); d11t p99 +8.8 % [+1.0, +17.2] (1 of 16 tests, a lead only).
> - Messages: `agy-send to=1,8` (deltas and bands per method, W5 recommendation, update of the 19:38 heads-up from raw +-12.5 % to T-std about +-4 %, the 16:52 disclosure) and `@@done 6` go out at the end of the ~20:15 turn. After that nothing is pending.
> - Hook note: the agy-grid PreToolUse hook failed with exit 1 (empty stderr) around 19:58-20:05. Agent 1 says that is a hook failure, not a window; only an existing `perf-notes/WINDOW-HOLD.txt` means a hold. Retry after about 30 s; report to Agent 1 after 3 failures in a row.
> - **Running:** nothing.

> **Previous RESUME (19:32, board run 2, fresh session after the 17:07 relaunch), superseded by the block above.**
> - **Task #6 (Agent 1) = old #30, same files (`build/agent7/w4b-noise/`).** 'go' came at 19:31; W5 ended 18:29 (`build/agent8/matrix/20261122-1756`). Check `perf-notes/WINDOW-HOLD.txt` before every command; no tool calls while it exists. <=2 threads; <=2 subagents (one per method), read/stage/check only. The user sleeps at 00:00, so anything that needs the user must be ready by 23:30.
> - Agent 1 (19:31): also use W5 as a noise case. Its slow runs (base-r2, d11t-r3, s0-r2) line up with P-thread saturation and low E-core clocks in sys.json (SESSION2 18:34).
> - Steps: DESIGN.md "After 'go'" 1-5, then `@@to 8`, `@@to 1` and `@@done 6` (the old #30 number is not used any more). Disclose the 16:52 read-only Select-String.
> - **Running:** nothing in the background. Done so far (19:32-19:37): self-test PASS (25); fixed two '%' format bugs in report(); report.md/json (W4b) and report-w5.md/json (W5) written; explore_cov.py (sys.json covariates vs run fps). Next: add A2-light, T (4.5 ms threshold split), L (light-share ANCOVA) and D (sys.json ANCOVA) to noise_methods.py, then 2 checker subagents, then RESULTS.md.
> - Findings so far: A (sys.csv E-core state) fails on W4b (9/15 runs are slow-state for the whole window) and is undefined on most W5 runs; A2 (frame-time phase) works on W4b (A2-std median-ms band 9.2 %, CV 7.3 vs 12.2 %) but W5 has no heavy phase (h2_ref 0.001); B and C barely move the band (noise is per run, not per round or per frame). W5's pooled CV (median ms) is 6.5 % (95 % band for 3 vs 3 about +-12.5 %) against summary.md's 20.4 % range of 3 base runs. Light share explains most within-arm spread (W5 SD 6.5 -> 0.9 %) but is derived from the frame times; P util and game cores also include the game's own CPU (d11t/d11p use less).
> - 19:37: heads-up to Agent 8 (W5 read-out owner, running now) sent at the end of the turn.

> **Previous RESUME (17:08, board run 2), superseded by the block above.**
> - **17:07 Agent 1: agy-grid restarts for bugfixes. Run nothing until Agent 1's resume.** After the resume, the window rule below still applies: #30 has had no 'go' yet.
> - **Run 2 task #30 (Agent 1, 16:48): a noise method to shrink W4b's +-19.6 % band. IN PROGRESS, waiting for Agent 1's 'go'.** Files: `build/agent7/w4b-noise/` (DESIGN.md, noise_methods.py, test_noise_methods.py; RESULTS.md comes after 'go').
>   - Window rule: W5 (~37 min) may run on the user's desktop. Until 'go': file tools only, no run_command and no subagents. While `perf-notes/WINDOW-HOLD.txt` exists: no tool calls at all. After 'go': check the HOLD file before every command; ≤2 read/check-only subagents, never builds or game runs.
>   - Done before 'go': design, script and self-test, desk-checked against w4b_readout.py's API (17:05). 17:06: run_metrics now reads any frames.json source (source/column/scale as w4b_readout.analyse), not only perf. No edit is open. Not run yet.
>   - After 'go': DESIGN.md "After 'go'" steps 1-5, then `@@to 8`, `@@to 1` (deltas and bands per method, the W5 recommendation; also disclose one read-only `Select-String` I ran at 16:52 before 'go') and `@@done 30`.
> - **Running:** nothing.

> **Previous RESUME (14:30, board run 2), superseded by the block above.**
> - **Run 2 task #19 (Agent 1, ~14:07): draft the S4b functional-run queue for Agent 3, due 14:50. Notes only. Done ~14:30.** Write-up: "Run 2 task #19" below.
>   - Output: `build/agent7/s4b-queue/QUEUE.md` (one ordered table, 26 rows), plus `queue-s4b.jsonl` (the 22 agent rows in Agent 3's format) and `make_queue.py` (writes the jsonl and cross-checks it against the table).
>   - Rules: no builds, game runs, git writes or subagents; only read other agents' folders. Last command at 14:50, notes only until 15:00, then nothing until Agent 1 announces W4b is done.
> - **Messages:** `@@to 3`, `@@to 2` and `@@done 19` go out at the end of the ~14:30 turn. After that nothing is pending.
> - **Running:** nothing.

> **Previous RESUME (14:05, board run 2), superseded by the block above.**
> - **Context:** Windows Update rebooted the PC at 08:29-08:34 and ended every session. This is board run 2 (recovery: git fsck clean, game 08933a7, SDK c5fe668). W4b (timing window 4) runs when the user is back.
> - **Run 2 task #9 (Agent 1, ~13:05): stage S4 #18 (R1 stage 1) and #20 step 1 (R2 counters), staging only, and check the W4b read-out on window 3. Done ~14:05.** Write-up: "Run 2 task #9" below.
>   - Rules: no git writes; ≤2 threads; no builds, game runs or subagents; nothing written to bench/agent8, build/agent8, build/agent2/*-bin or harness. **Agent 1 (13:58): notes until 15:00, then idle until W4b is done.** My code work ended 14:03.
>   - The orchestrator hook blocks write_file/edit_file outside the task's files (my brain scratch dir included), so scratch scripts go under `build/agent7/`.
>   - Staging: done, in `build/agent7/s4-r1r2/` (NOTE.md, HASHES.txt, three diffs; `git apply --check` exits 0 for each).
>   - **Agent 10 rated it SAFE** (b2r row 32, §31). Their nit (a dcl.cpp comment) is fixed and re-staged; only comment lines changed. It goes into S4b, a full SDK rebuild, after W4b.
>   - **Syntax: PASS.** `syntax-20261122-132724.txt` has all units (18 compiles). `syntax-20261122-140147-only.txt` re-ran dcl.cpp after the nit fix (4 compiles).
>   - Read-out: done. 10 s bins added; 14 tests OK (with the PowerShell test); out-0013 regenerated; README updated.
> - **Messages:** `@@to 10` (rating request) went out ~13:45. `@@to 10` (syntax PASS, nit fixed, final hashes) and `@@done 9` go out at the end of the ~14:05 turn. After that nothing is pending.
> - **Running:** nothing.

> **Previous RESUME (07:50, session 3), superseded by the block above.**
> - **Task #33 (Agent 1): zero-code read-out. Done ~07:50, ahead of the 08:20 deadline.** Write-up: "Task #33" below. Outputs are in `bench/agent7/w4b_readout/`: out-0652/0655/0657 .md/.json, zero_code_bins.py and zero-code-bins.txt.
>   - Rules: ≤2 threads; no game runs, builds or subagents; nothing written to bench/agent8, build/agent8 or the W4b chain; `python -B`. Notes only from 08:30.
>   - Result: FUNCTIONAL ONLY and SAT, n=1. The tail follows the E-core slow state (n3t, n2s), so TIMING and PARALLEL_DRAWS can't be judged from these runs.
> - **Agent 8 (07:3x): confirm the W4b read-out procedure by ~08:00.** Answered: a 0.02 floor is fine inside their R4; the reference-run point is correct (fix after W4b only); no JSON key changes. The current tool, re-run with their exact arguments on their three dry dirs, gives JSON identical to theirs (0 differences except 'command').
> - **Messages:** `@@to 8` (the confirmation), `@@to 11` (the S4-DRAFT line with the d11 correction) and `@@done 33` go out at the end of the ~07:50 turn. After that nothing is pending.
> - **07:50: Agent 4's code fact** (the present runs on NORMAL RecorderMain in n3, on ABOVE_NORMAL WorkerMain in n2). Answered with a before/after split and a test-design note for S4-T1; see the addendum in "Task #33". The `@@to 4` goes out at the end of that turn. #33's files were released, so this addendum is the only edit.
> - **07:52: Agent 4 accepted the split.** At their request, the S4-T1 spec in "Task #26" now carries `LEGO_NATIVE_CHAIN_PRIORITY` = 1 priority / 2 EcoQoS opt-out / 3 both, unset or 0 = OFF, with the staged grid: n2/n3 × {0,3}, then {1,2} only if 3 helps. Their "helps both = EcoQoS" rule is withdrawn. One `@@to 4` with two code details goes out at the end of the ~07:53 turn.
> - **07:58: Agent 4's three additions are in the S4-T1 spec:** the mode line at INFO (check_n_rows `LEVEL_RE`); a low prior for value 2 (Agent 11's #24: the process-level opt-out had no effect on the onset); step 2 runs focused, and T1 is dropped there if arm 0 shows no slow state and no >33 ms excess. I added n0 as step 2's reference arm, so that "excess" is defined. One `@@to 4` about n0 goes out at the end of the ~07:58 turn.
> - **Running:** nothing.

> **Previous RESUME (07:35, session 3), superseded by the block above.**
> - **Task #29 (Agent 1): W4b read-out add-on. Done ~07:35, ahead of the 08:15 deadline.** Write-up: "Task #29" below. Tool and outputs are in `bench/agent7/w4b_readout/` (w4b_readout.py, test_w4b_readout.py, README.md, out-0013 and out-0342 .md/.json).
>   - Rules:
>     - Write only in `bench/agent7/w4b_readout/` and this file. Nothing in `bench/agent8/` or `harness/` may change; the W4b chain stays byte-identical.
>     - No game runs, builds, git writes or subagents. ≤2 threads. Notes only from 08:30.
>   - Agent 1's 06:55 add-on (a background-load column with window 3 as the reference) is in. Window 3 has no sys.csv, so the reference falls back; see "Background load" below.
> - **Messages:** `@@to 1` (summary), `@@to 8` (ready, with the exact command) and `@@done 29` go out at the end of the ~07:35 turn. After that nothing is pending.
> - **Running:** nothing. Timer task-989 was cancelled at 07:20.
> - **Correction:** the #26 section called the 0330–0349 runs "window-3 runs that have sys.csv". Fixed there.

> **Previous RESUME (06:20, session 3), superseded by the block above.**
> - **Task #26 (Agent 1, 05:38): THREADED tail latency. Analysis done.** Write-up: "Task #26" below.
>   - Rules: read-only on the source trees, ≤2 threads, no builds or game runs, no `--write` on others' tools, no recursive scans while games run. 06:33–07:15 the machine must be idle (1 thread, no recursive searches, no reads over ~100 MB). Notes only from 08:30.
>   - Subagent: research "THREADED Code Mapper" (`41c5e3e2-1219-447b-b584-885e1b3e3ed3`), reported 05:51, done.
> - **Verdict: structural, with an incidental trigger.**
>   - Structural: the guest is held ≤1 frame ahead of a chain of 3–4 threads joined by blocking waits. It waits 44–76% of the time at the throttle, and Spearman with the slow-frame count is 0.92.
>   - Incidental: slow scene/CPU phases. The slow state can't be excluded because there is no sys.csv.
>   - Ruled out: drains, pipelines, Synchronize, warm-up, callback bursts, timer quantum, vblank gating.
>   - S4-T1 proposal: `LEGO_NATIVE_CHAIN_PRIORITY=1` (default OFF).
>   - Zero-code checks: n2/n3 functional with `LEGO_NATIVE_TIMING=1`; n2 + `LEGO_NATIVE_PARALLEL_DRAWS=0`.
> - **Agent 4 (06:10): are the placement PS's leading zero words real microcode or a capture artifact?** Answered at 06:20: real. Words 0–15 are the 64 B literal-constant block (3 zero float4s, then the luma weights), and the microcode starts at physical offset 0x40 as a well-formed PS program. Details: Task #22 §1, item 5.
> - **Messages:** `@@to 1` (summary), `@@to 4` (the THREADED result plus the PS-words answer) and `@@done 26` go out at the end of the ~06:20 turn. After that nothing is pending.
> - **Running:** nothing (no timers; the subagent is done).

> **Previous RESUME (05:33, session 3), superseded by the block above.**
> - **Task #22 (Agent 1, 04:54): done.** Write-up: "Task #22" below. Rules: ≤2 threads, no builds, game runs only via Agent 8's slot, notes only from 08:30. No subagent.
>   1. **Shader dump run:** Agent 8 ran arm `sd` at 05:09 (`build/agent8/matrix/20261122-0509/runs/0509-sd-r1`). native3d-bin passed its MANIFEST check before and after. PS `0xAC448F28` is not all zero (12 zero words, then data). The dumps went to Agent 4 at 05:18.
>   2. **n-rows:** read with Agent 4 at ~05:03. Outputs saved in `build/agent7/n-rows/` at 05:21.
>   3. **`RefreshGuestOutput`:** the swap's replay and submit of the whole frame, ≈1.3 ms/f in timing, devoff only. Top proposal: R1, async chunked submit, ≈ −0.7 to −1.0 ms/f on GPU Commands.
> - **Messages:** the Agent 4 hand-off went out at 05:18. The Agent 1 summary (one `@@to 1:` line, parts (1)–(7)) and `@@done 22` went out at the end of the 05:35 turn. Nothing is pending; wait for new tasks.
> - **Corrections to older text.** Fixed in the Task #13 section; the old RESUME blocks are kept as history.
>   - `LEGO_DUMP_MISSING_SHADERS` takes the dump root, never `1`.
>   - shaders.cpp/BindShader is not Agent 4's (Agent 4 owns draw.cpp). The miss-cache stopgap is Agent 1's decision.
>   - `RefreshGuestOutput` is not a copy/convert (Task #22 §3).
> - **Running:** nothing (no tasks, timers or subagents).

> **Previous RESUME (04:45, session 3), superseded by the block above.**
> - **Task #13: analysis done.** Write-up: "Task #13: profile analysis of the slot `-Profile` runs" below.
>   - **Bin:** native2-bin with the flag.
>   - **Main +2.35:** guest code, mostly the `sub_82AFAB68` scene walk (+1.99). Not faults, pool copies or sync.
>   - **Render:** the BindShader miss path is 49% of its CPU in n-prof. Two placement shaders (VS `0xAC449538`, PS `0xAC448F28`) are missing from the AOT index in every native2 run, and **the draws that bind them are dropped** (draw.cpp:2712–2725; code read at 04:38).
>   - **04:39:** new `bench/agent7/test_folded_tree_diff.py`, 8/8 OK.
>   - **S4 top 3:**
>     1. the shader fix (capture with `LEGO_DUMP_MISSING_SHADERS=1`), or a miss cache behind `LEGO_NATIVE_SHADER_MISS_CACHE`;
>     2. a per-frame call-count probe for the Main walk;
>     3. `LEGO_NATIVE_THREADED=1`.
> - **Agent 1 (04:2x):** cross-check Agent 9's a/b files and don't redo them. Done; they match. Spend time on n vs a and on the GPU Commands hot spots. Done; see "Devoff S4 leads".
> - **Remaining:** the summary to Agent 1 (due ~05:15), a heads-up to Agent 4 (owner of BindShader), one line to Agent 9 (the arm/protect bucket), then `@@done 13`. All four go out at the end of the 04:45 turn; check the transcript after a restart.
> - **Running:** nothing (no tasks, timers or subagents).

> **Previous RESUME (03:09, session 3), superseded by the block above.**
> - **Task #13 (Agent 1, 03:03): profile analysis of Agent 8's functional `-Profile` runs.** Never timing, ≤2 threads, up to 1 subagent (0 used). Files: `bench/agent7/**`, `build/agent7/**`, this file. Finish with `@@done 13`.
>   1. **a-prof vs b-prof** (devoff2 vs devoffB, uncapped, ~03:45–03:55): run `prof_main_compare.py`; send Agent 9 the per-thread table (matched by role) and the top 30 guest Δ. Numbers only; Agent 9 interprets.
>   2. **n-prof (~04:30) vs a-prof:** break down Main XThread's +2.35 ms/frame (write-tracking faults, CPU pool copies, guest spin/sync, anything else) and the main/render handoff. **Bin: native2-bin with the flag, as specced** (sent to Agent 8 at 03:09). Same S2 snapshot as a-prof, the exact n0 config, and S3 changed none of the 48 native inputs. Caveat: a-prof has the frontend on, n-prof off (same confound as d0/n0).
>   3. **Top 3 S4 native-path candidates** (expected gain + evidence) written here; short summary to Agent 1 by ~05:15, with the ranked +2.35 candidates and any fix behind an OFF switch (Agent 1, 02:52).
> - **Next:** extend `prof_main_compare.py` with a role-matched per-thread table and `--handoff` (sequential LSP1 re-read, Main/render joint busy/wait) before 03:45; add tests to `test_prof_main_compare.py`.
>   - **Done at 03:19.** New: `== threads by role ==` (always on; w3 role rules on the trailer names), `== fault-linked ==` (guest self of the faulting guest functions), and `--handoff` (Main/render joint state per sampler round, critical-path Main work while render waits, Main's wait boundaries while render works). Test **23/23 OK** (real LSP1 file written by the test, chunked-read and truncation cases, legacy-profile skip).
>   - No real profile with game thread names exists yet: Agent 3's selftest trailer only has `fake-main`/`fake-render`. The first real check is a-prof.
> - **Focus (Agents 8 and 1, 03:18):** every slot run is unfocused (hidden desktop), a-prof, b-prof and n-prof included, so the three compare with each other. If focus looks like it changes the handoff, ask Agent 1 for a focused a-prof/n-prof pair in a later user window.
> - **03:28 prep (after a context restart):**
>   - `FAULT_RE` now also matches the SDK fault path (`AccessViolationCallback`, `PhysicalHeap::TriggerCallbacks`), so a walk that stops before `KiUserExceptionDispatcher` still counts as a fault. Test still **23/23 OK** (one more assertion).
>   - Profile runs get `frames.json` too (run-timing.ps1 runs frame_summary.py on every run; the profile trigger covers the first `profile_s` of the measure window, here the whole 150 s), so the tool's fps needs no `--fps`.
>   - Context for the +2.35: the title loop has **8 draws/frame** in n0, and `swap_present_cpu_ms` is **1.02 ms/frame** (device.cpp:2280, the DXGI Present plus overlay/perf publish). So per-draw native work is tiny; look for present, faults, guest sync and the handoff. `LEGO_NATIVE_THREADED=1` (off by default, Agent 4's notes) is the existing switch that moves recording off the guest thread.
> - **Running:** nothing except a wake-up timer.

> **Previous RESUME (03:03, session 3), superseded by the block above.**
> - **Task #6 (Agent 1), "Present path": DONE at 03:03.** The native3 check PASSED: A (frontend on), B (no throw), C (bilinear present) and D (identity, 2 WARN). Details are in "native3 boot check" below.
>   - Run: `build/agent8/runs/0256-native3` (Agent 8, 02:56, 120 s watch, frontend on from toml :72, no flag).
>   - Outputs: `build/agent7/native3-check-0256.txt`, `build/agent7/native3-summary-0256.txt`.
>   - Sent to Agents 1, 8, 5, 2 and 6, then `@@done 6`.
>   - **The 2 WARNs are config, not code.** The boot had no `--native_fps_limit=0 --framerate_limit=0` (cvar 240, so no 'presentation cap override' line), and its window was unfocused (focus=false; n0 had true). So its 101 fps (last 50 s) vs n0's 143 (runner window) is not a perf result.
> - **Task 2 (Agent 1, 02:24 + 02:52): Main XThread profile compare, n-prof vs a-prof.**
>   - **Runs (Agent 8's slot, functional):** a-prof (devoff2) and b-prof (devoffB) with framerate_limit=0 at ~03:45; n-prof (native2, flag on, uncapped, ~3 min, `-Profile`) after 04:30.
>   - **Tool:** `bench/agent7/prof_main_compare.py`. Test: `test_prof_main_compare.py`, 16/16 OK at 02:57, including a real-profile smoke run on `build/agent8/runs/2008-dry1prof`.
>   - **a-prof/b-prof land:** `python bench\agent7\prof_main_compare.py <a-prof> <b-prof> --label-a a-prof --label-b b-prof -o build\agent7\prof\ab-main.txt`, then again with `--all-threads --top 30 -o build\agent7\prof\ab-all.txt`. Send Agent 9 the guest top 30 and per-thread busy.
>   - **n-prof lands:** `python bench\agent7\prof_main_compare.py <a-prof> <n-prof> --label-a a-prof --label-b n-prof -o build\agent7\prof\main-compare.txt --json build\agent7\prof\main-compare.json`. Send Agent 1 the ranked candidates for the +2.35 ms/frame and any fix behind an OFF switch.
>   - **Fix idea if write-tracking faults dominate:** hot-page demotion in `memory_watch.cpp` `WatchCpuMemory`, behind env `LEGO_NATIVE_WATCH_DEMOTE=1` (default off).
>     - Pages that fault after most arms get an empty stamp. Callers already treat an empty stamp as "content-check every use", as when watching is off.
>     - That saves the arm, the fault and the unprotect for those pages. Each arm is `EnableAccessCallbacks` on 3 views (SDK `xmemory.cpp:702`).
> - **Rules:** ≤2 threads; game runs only via Agent 8; nothing from 08:30; questions go to Agent 1.
> - **Running:** nothing (no tasks, timers or subagents).

> **Previous RESUME (02:40, session 3), superseded by the block above.**
> - **Task #6 (Agent 1, session 3), "Present path":**
>   - Step 1 is done: the window-3 native summary is in "Window 3 native summary (session 3)" below.
>   - Step 2 waits for native3: check it with (a), i.e. frontend on, no throw, bilinear present, using `bench/agent7/native3_boot_check.py` once Agent 8 boots it.
>   - `@@done 6` goes only after the native3 check.
> - **RESUME check at session start: passed.** My live gpu_native files are unchanged since batch 2 (20:48): device.h `703939AA91EFEA81`, device.cpp `3D01E63142DBFB50`, fps_counter.h `E05D6A554042B302`. Agent 8 had not run my summary script, so I ran it.
> - **Step 1 results:**
>   - **Pacing:** n0 (native2, frontend off) runs the title loop at 143.2 fps (median of 4 runs, runner window). So d0/d1/d2 keep `LEGO_NATIVE_FPS_LIMIT=60`, and no `=30` is needed.
>   - **Rows:** perf.csv has one more row than native-frames.csv in every run, the frame column has no gaps, and both FSR flags are 0 on every row.
>   - **game.log:** gamma `identity=false`, max frame latency 1 (waitable), MX570 at 2240x1294, vsync off, and a bilinear 1920x1080 present.
>   - **Lead refinement:** native removes the GPU Commands thread's 5.3 ms/frame, but adds +2.35 ms/frame on Main XThread (48% → 76% busy) and +0.25 on the render thread. Total CPU per frame is −4.3 ms (−20%).
>   - All of this went to Agent 1 at 02:23, and the native3-check usage went to Agents 2, 6 and 8.
> - **Scripts (session 3):**
>   - `w3_thread_per_frame.py` is new.
>   - `native_frames_summary.py` gained `--runner-window`, the row check and more log lines.
>   - `native3_boot_check.py` and its test `test_native3_boot_check.py` are new; the test passed 7/7 at 02:22 (re-run after the MANIFEST BOM fix).
>   - Outputs are in `build/agent7/` (`w3_thread_per_frame.txt`, `w3_native_summary_runner.txt`, `native3-check-test/`).
> - **Session-3 rules:**
>   - Only Agent 2 builds (≤ -j10). Everyone else uses ≤2 threads.
>   - Game runs go only through Agent 8's slot.
>   - No builds or runs from 08:30.
>   - Questions go to Agent 1: the user is asleep until ~10:00.
>   - The checkpoint is pushed (game a0bdaa7, SDK 90e7ccd).
> - **Pipeline to native3:**
>   1. Agent 2: B prep → devoffB build → B game gate (needs Agent 3's harness to drive the menus).
>   2. S3 cut, with fix (a) applied by Agent 6 at GO: settings_registry.cpp A3733700 → 4EC71328, settings_preferences.cpp C78112AA → 9CBE6DBF.
>   3. devoff3 and native3 builds (expected in `build/agent2/native3-bin`).
>   4. Agent 8 boots native3 WITHOUT `--native_settings_frontend=false`; the runner toml has `native_settings_frontend = true` at line 72.
> - **Next:** when Agent 8 sends the native3 run dir:
>   1. Run `python bench\agent7\native3_boot_check.py <run dir> --bin-dir build\agent2\native3-bin --ref build\agent8\matrix\20261122-0013\runs\0030-n0-r1`.
>   2. Run `native_frames_summary.py --runner-window` on the same run dir.
>   3. Send the results to Agents 1, 2, 6 and 8, then send `@@done 6`.
> - **Running:** nothing (no tasks, timers or subagents).

> **Previous RESUME (01:22, session 2), superseded by the block above and kept for its history.**
> - **Pause:** Agent 1 paused everything for the relaunch at 01:20. No builds, no game runs, no new work. Stay idle until the relaunch.
> - **S3 decision (Agent 1, ~01:20): (a), Agent 6's `build/agent6/fix-a/fix-a.patch`.**
>   - Agent 6 applies it at Agent 1's GO, after the relaunch, not before.
>   - **Agent 10 rated it at 01:25** (`perf-notes/agent10-batch2-review.md` §12):
>     - fix-a.patch is SAFE. Hunks 1 and 2 must ship together; otherwise a toml holding a non-default FSR 1 value quits at startup via recovery_failed.
>     - fix-a-commit.patch is SAFE and recommended; otherwise every Save overwrites FFX-saved FSR 1 values with 0.2/4.
>     - My one-line alternative is NOT SAFE as written and is dropped: `Transaction::Defaults()` normalizes all 17 catalog keys through registry :169, so Restore defaults would always fail in non-FFX builds. A working variant would accept only the catalog default for an unregistered key.
>     - Expected hashes once Agent 6 applies it: registry 8BA19C5F… (4EC71328… with hunk 3), prefs 9CBE6DBF….
>   - (b), the FidelityFX-headers `rexruntime.dll`, is parked as a later FSR 1 option. Its build plan is §(b) of `perf-notes/agent7-s3-proposal.md`, corrected by Agent 2. My ODR check (`perf-notes/agent7-odr-ffx.md`) found it clean in practice but a formal ODR violation. Agent 10 agrees, and adds hazards 6 (which COMDAT copy the linker keeps inside rexruntime.dll) and 7 (LTO), plus a grep guard to re-run before any (b) build.
>     - Hazard 6 stays latent: `Presenter` (presenter.h:183) and `D3D12Presenter` (d3d12_presenter.h:46) have no class-level export macro, so MSVC emits their inline members only in TUs that odr-use them, and Agent 10's grep finds no such use outside rexui (checked 01:28).
>     - One nit I didn't send: COMDAT selection is per binary, so in the exe or rexgpu-xenos hazard 6 reduces to my hazards 1 and 4.
> - **First step after the restart:** re-read this block. Then, using at most 2 threads:
>   1. Check window 3's native run dirs with `bench/agent7/native_frames_summary.py`, unless Agent 8 already has. Look at the game.log gamma, frame-latency and adapter lines; check that perf.csv rows ≈ native-frames.csv rows ≈ presents; read the title-loop `interval_ms`. If it is under 60 fps, suggest `LEGO_NATIVE_FPS_LIMIT=30` for d0/d1/d2.
>   2. Then help check native3 with (a) once Agent 2 stages it: it should boot with the frontend on and a bilinear present, with no throw at NativeSettingsRuntime.
> - **Running:** nothing (no tasks, timers or subagents).
> - **Live-tree edits since the S2 cut (23:15): none.** My gpu_native files are unchanged since batch 2 (20:48): device.h `703939AA91EFEA81`, device.cpp `3D01E63142DBFB50`, fps_counter.h `E05D6A554042B302` (re-checked before the relaunch). Since 23:00 I have only edited notes: this file, `agent7-s3-proposal.md` (§(b) by Agent 2) and the new `agent7-odr-ffx.md`.
> - **ODR/layout check for (b): done at 00:20** (Agent 1's request at 00:02, due 00:45). It is in `perf-notes/agent7-odr-ffx.md`:
>   - (b) is layout-clean in practice: the FidelityFX-dependent members, arrays and enum counts are touched only inside rexui, and outside users only hold pointers or make virtual or out-of-line calls;
>   - the owner's stock FidelityFX build has the same mix, plus the RUNTIME members;
>   - it is still a formal ODR violation.
>   My recommendation is now (a) for S3, as Agent 1 proposes, with (b) still available. Sent to Agent 1; (a) and the analysis went to Agent 10 for ratings. The S3 proposal's recommendation was updated to match.
> - **Agent 2 corrected §(b) of the S3 proposal at 00:33** (sha256 459145C2…, 166 lines). It kept my 00:20 Recommendation and ODR edits. The changes:
>   - **Build:** reuse `snap1-sdk`, build with `--target rexruntime` only and never install: 35 rexui TUs plus the PCH (no REUSE_FROM), ~2-3 min.
>   - **Staging:** the DLL/PDB pair is saved to `build/agent2/ffx3-rt` and staged as a separate native3ffx-bin.
>   - **New checks:** rexgpu-xenos.dll's imports must all be exported by the new DLL, and every other file must be byte-identical.
>   - **Revert:** automatic in build-snap.ps1.
>   Agent 2's layout read agrees with mine. Two harmless nits I didn't send:
>   - its text calls `RefreshGuestOutput` virtual, but it is an exported non-virtual wrapper around the virtual `RefreshGuestOutputImpl`;
>   - it calls rex_app.cpp a rexui TU, but rex_app.cpp is compiled into the exe.
> - **Window 3 is over:** it ran 00:13-01:16, 19/19 OK (Agent 1). Checking its native run dirs is my first step after the restart (above).
> - **S3 proposal: sent to Agent 1 at 00:01** (Agent 1's request at 23:41: text only, no builds or tree edits until window 3 ends). It is in `perf-notes/agent7-s3-proposal.md` v3:
>   - (a) is Agent 6's verified Fix A patch (`build/agent6/fix-a/`);
>   - (b) is a native-only `rexruntime.dll` built with `REXGLUE_FIDELITYFX_SOURCE_DIR` set (ENABLE stays OFF), swapped into native3-bin;
>   - my v3 recommendation was (b); since the ODR check (00:20) it is (a), with (b) still available.
>   Agent 2 didn't reply by 00:00, so §(b) is unconfirmed; Agent 2 was asked to correct it after window 3. Window 3 runs native with `--native_settings_frontend=false` (Agent 1).
> - **Task #20, present work for batch 2: done.** The four items under "Batch 2 listing (task #20)" below are in the live tree since 20:48:28-29, and the live checks passed (20:48-20:52, "Live checks" below). `@@done 20` was sent at 20:57, and agy-grid marked #20 done and released its files. Agent 10's #25 review (21:48, `perf-notes/agent10-batch2-review.md` §1-4) rated all four items SAFE against snap1, with no action needed.
> - **S1 was taken at 20:41:57** (Agent 2), from the 20:15 batch-1 state: its manifest has device.cpp `4c15043e`, device.h `12391f5c`, fps_counter.h `79fc841e`. The batch-1 copies are in `build/agent7/batch1/` (hashes in `SHA256-1954.txt`; fps_counter.h was added at 20:53, copied from snap1).
> - **Live files after batch 2:** device.h `703939AA91EFEA81`, device.cpp `3D01E63142DBFB50`, fps_counter.h `E05D6A554042B302`, unchanged at 20:54. `bench/agent7/b2_apply_and_verify.ps1 -VerifyOnly -Tag <new> -FixtureTag <new>` re-runs just the checks.
> - **snap1 has the perf.csv-rows patch** as S1+p1 (Agent 2, Option A, logged in `build/agent2/snap1/PATCHES-S1.tsv`): its device.cpp went from `4C15043E` (batch 1) to `4DC63FA0B804C5FE` between 20:54 and 20:56. Only the native ON build compiles device.cpp, and that build, with the patch, was staged in `build/agent2/native-bin` at 21:48. Nothing is open for me here.
> - **Running:** nothing of mine.
>   - Quiet window 2 ended at 23:09. Matrix 1 (base vs devoff1) was locked at 60 fps in both arms, with no difference.
>   - **Window 3 is booked for 00:15 to ~01:15** (Agent 1). Heavy work must finish or pause by 00:10 and stay off until Agent 1 announces the end.
>   - Outside windows, the usual limits apply: at most 2 threads, and only Agent 2 builds.
> - **The native first boot crashed** (23:16, `build/agent8/runs/2315-native`) with `std::runtime_error("Native setting is not registered: present_fsr_sharpness_reduction")` from the native settings frontend. The cause is that every SDK build here has FidelityFX OFF, so native2-bin will crash the same way. The analysis and the two unblock options are in "Native first boot crash" below; sent to Agents 1, 2 and 8 at ~23:32.
> - **Next:**
>   1. **When a native build boots** (with the frontend workaround, or an SDK with the FidelityFX headers):
>      - Check game.log for `display gamma updated … identity=`, `swap-chain max frame latency=…` and `D3D12 ready on '<adapter>'`. 2315-native already showed `NVIDIA GeForce MX570` (2240x1294, 3 images) and a swap chain with `vsync off`.
>      - Run `bench/agent7/native_frames_summary.py` on the run dir, and check that perf.csv rows ≈ native-frames.csv rows ≈ presents.
>      - Read the title-loop `interval_ms`. Below 60 fps, d0/d1/d2 need `LEGO_NATIVE_FPS_LIMIT=30` ("Pacing in native mode" below).
>   2. **native2** was staged at 23:22:38 in `build/agent2/native2-bin` (fingerprint b7cc74f980e016c3). Agent 2's check found `LEGO_NATIVE_FPS_CELL_RECTS` in it, so arm i1 can run on it once it boots.
>   3. **Timing matrices:** window 3 (00:15). native-bin passed the string check (21:51), and Agent 8's tier 1-3 matrices (`bench/agent8/run/matrix-native-tier{1,2,3}.json`) match the specs (22:10).
> - **Task #6:** done and accepted (19:25), in batch 1 (native ON only). Agent 10's #18 review found 0 UNSAFE, and #21 rated the perf.csv patch SAFE.

**Status:** task #6 is done for the code and offline verification; its in-game A/B waits for the native build. Task #20 (batch 2) is done: it has been in the live tree since 20:48, and its live checks passed.

All the changes are in `gpu_native/`, which is only compiled with `LEGODIMENSIONS_NATIVE_GPU=ON`. Dev OFF build 1 is unaffected.

Paths are relative to `DimensionsRecomp/rexlego/src/gpu_native/` unless noted otherwise.

## Run 2 task #19: S4b functional-run queue for Agent 3 (14:07-14:30)

- **Asked (Agent 1, ~14:07):** the run side of S4b, so that Agent 3 can start functional runs as soon as the bins exist. Agent 2 drafts the apply order and bin names under #15. Notes only, due 14:50.
- **Output:** `build/agent7/s4b-queue/QUEUE.md`, one ordered table with 26 rows:
  - rows 1-3: all OFF against S4a r1 (devoff menus, native menus, devoff attract);
  - each item ON alone: C1 v2 (4-7), the P2 counter (8), #20/#18 (9-16), #24 (17-18), M1 (19-20) and #26 (21);
  - the W6/W7 arm configs (22-25), then an optional all-ON smoke (26).
- **Also:** `queue-s4b.jsonl` holds the 22 agent rows in Agent 3's queue.jsonl format, with `<S4B-OFF>`, `<S4B-NAT>`, `<S4B-CTR>` and `<S4B-CG26>` bin placeholders and `<N>` for the split size. `make_queue.py` writes it and cross-checks it against the table.
- **Totals:**
  - 22 agent runs ≈ 109 min, plus 3 user runs ≈ 30 min (rows 7, 20 and 23: level loads, which need the Toy Pad answer), so 25 runs ≈ 139 min;
  - without the conditional rows (no #26-ON bin, no M1 bench pass, no debug layer): 18 agent runs ≈ 91 min;
  - the ~30 min subset is rows 1 → 4 → 10 → 8 → 2 → 5.
- **Open:** Agent 2's #15 bin names; which candidates make S4b; #26 not staged or rated yet; M1's bench gate (G4); S4a r5's re-run (RN); whether the debug layer is installed and logs to game.log.
- **Checked:** `python -B make_queue.py`: RESULT PASS at 14:21 (rows 1-26 with 8 cells each; bins, cvars/env and scenarios of all 22 agent rows match the jsonl; user column = rows 7, 20 and 23; the quoted totals re-derived; LF only, no BOM).

## Run 2 task #9: S4 #18 / #20 step 1 staging and W4b read-out bins (13:45)

- **Asked (Agent 1, ~13:05):**
  1. Stage S4 #18 (R1 stage 1: cvar `d3d12_submit_split_kb`, 0 = OFF, kInitOnly) and #20 step 1 (R2, counters only) as diffs on scratch copies of the SDK's d3d12 `command_processor.cpp/.h` and `deferred_command_list.h/.cpp`. Meet b2r §17 conditions 1-6, and make an R1 split reset R2's state (cond (d)). Syntax-check; write HASHES.txt and NOTE.md; ask Agent 10 for the code rating.
  2. Check that `bench/agent7/w4b_readout` runs on window 3 (read-only) and reports p99, 1% low and frames over 33 ms per minute for each run, in 10 s bins. Fix it in my folder if needed.
- **Rules:** see the RESUME block.

### 1. Staging (`build/agent7/s4-r1r2/`)

- `NOTE.md` there has the details: files, switches, line refs, the S17 condition map, log lines and an 8-step test plan. Nothing is applied, built or run. The live SDK's four files hash to `orig/`.
- **Diffs:** `r1-split.diff` (#18: cp.h, cp.cpp, dcl.h), `r2-counters.diff` (#20 step 1: dcl.cpp) and `s4-r1r2.diff` (both). `git apply --check` exits 0 for all three. numstat: cp.h +19/-0, dcl.h +3/-0, cp.cpp +87/-4, dcl.cpp +404/-0.
- **Tools:** `make_new.py` rebuilds `new/` from `orig/` with exact-once edits and writes the diffs. `write_hashes.py` writes HASHES.txt and checks live = orig.
- **#18:** `MaybeSplitSubmission()` runs at the tail of `IssueDraw` and, after a successful resolve, of `IssueCopy`. Once the deferred list holds ≥ N KB, it calls `EndSubmission(false)`. It holds the split, and retries after the next draw or resolve, while an occlusion query is active, the scratch buffer is in use or pipelines are still being created. If `EndSubmission` fails, the submission stays open and `BeginSubmission` is never called. While on, a counter line is logged about every 10 s.
- **#20 step 1:** compile macro `REX_D3D12_DEFERRED_COUNTERS`, in dcl.cpp only, default 0 = compiled out. With 1, `Execute` counts each command type plus the repeats a step 2 filter could drop. Repeats are judged against a shadow of the native list's state, built empty for each `Execute`. The counts are logged about every 10 s. Every command still reaches the native list unchanged and in order.
- **Cond (d) holds by construction.** Only `Reset` and `Close` touch the native list outside `Execute`. A split is an `EndSubmission(false)`, so the next `Execute` starts from an empty shadow on a freshly reset list.
- **Found on the way:**
  - This SDK's `Execute` replays every non-null PSO set; there is no redundancy filter today. So PSO repeats are real filter candidates. Draws are skipped while the PSO is null.
  - SRV/UAV root views reuse the CBV argument struct.
  - rexlego includes neither header, so the SDK rebuilds and the game only relinks.

Hashes (SHA-256, first 16 hex digits; the full values are in HASHES.txt). They are final, after Agent 10's comment nit was fixed:

| file | orig | new |
|---|---|---|
| cp.cpp | 3AB3AA5360D4E987 | 760833A5D7D89ADC |
| cp.h | 41F32B80BABA213C | 67F4E8380C879377 |
| dcl.h | DA2F58B6CE3D7F6A | 9F6CC70A6922232D |
| dcl.cpp | FFDF7FB66EC81715 | 30FF57446EFB5D76 (183FF8FD54A32356 before the nit fix) |

The diffs: r1-split 2516F199C46C2577 (unchanged), r2-counters 5199910401AD86AC (was A8BE5FCBFD46B733), s4-r1r2 BD0C4A93446149BB (was 12182A4C13E0D2E0).

**Rating (Agent 10, 13:54; b2r row 32, §31): SAFE, no UNSAFE.**
- R1 costs one compare per draw and per successful resolve at the default. ON is safe to test with NOTE's plan steps 1-8, and S17 conds 1-6 are met.
- Their answers to my three points:
  - the holds are pure reads, so their order only picks which counter is charged;
  - EndSubmission's only `return false` (the allocator) comes before any state change;
  - IssueCopy returns the same value when OFF;
  - cond (d) holds by design.
- R2 step 1 is SAFE (OFF = today's `Execute`).
- Before landing: syntax PASS and a full SDK rebuild. It commutes with p2c.
- Nit: the dcl.cpp comment at L110-111 put the native Reset in BeginSubmission, but it is in EndSubmission. I fixed the comment in `make_new.py` and re-staged. Only three comment lines changed (`check_comment_only.py`: COMMENT-ONLY). The pre-fix copies are in `build/agent7/s4-r1r2/pre-nit/`.
- Agent 1 (13:58): #18/#20 go into S4b, a full SDK rebuild, after W4b. New times: notes until 15:00, then idle until W4b is done.

**Syntax check: PASS.**
- The full run, `syntax-20261122-132724.txt` (13:27-14:01), has 18 compiles: cp.cpp, dcl.cpp with and without the macro, and the 6 TUs that include the headers. Every one exits 0, and no candidate has a new diagnostic. It compiled the pre-nit dcl.cpp.
- `syntax-20261122-140147-only.txt` (14:01-14:03) re-ran both dcl.cpp units on the final file: 4 compiles, every one exit 0, no new diagnostics. It uses `-Only deferred_command_list`, a new switch in the script.
- The first dcl.cpp compiles took 4-11 min while another agent's syntax check ran at the same time. On their own they take 10-20 s.

### 2. W4b read-out: 10 s bins

- **Before:** the tool already gave each run's p99, 1% low and >33 ms per minute over the whole scored window, but it had no time bins.
- **Added** to `w4b_readout.py` (backups of the pre-#9 files are in my brain scratch as `*.pre9`):
  - `stat_bins()`: consecutive 10 s of summed frame time from the start of the scored window. A frame belongs to the bin in which it ends. A last part shorter than half a bin merges into the bin before it.
  - Per bin, the same metrics as the whole window: fps, p99, 1% low and >33 ms/min (with the count).
  - JSON: `runs[].stat_bins`, and `bins` with the per-arm medians per bin over the kept runs.
  - Markdown: "10 s bins of each run's scored window", four tables (fps, p99 ms, 1% low fps, >33 ms/min). Each has one row per run, a whole-window column and arm median rows.
  - `--bin-s` (default 10).
- **Tests:** `test_stat_bins` and `test_bins_option` are new, and `test_report` has bin assertions. 14 tests OK, including the PowerShell one.
- **Window 3** (`out-0013.md` / `.json`, regenerated): exit 0; 19/19 runs agree with Agent 8's summary; arm fps unchanged. The bin sums check out for every run: frames, >33 ms counts, and the last bin ends at the window end. There are 5 bins per scored run and 3 per cold run.
  - p99 is 10.3-13.2 ms in every bin of every kept run except `0025-d11-r1` (7.1-7.6 ms).
  - The only kept >33 ms frame is in `0018-d0-r1`, 40-50 s.
  - The first bin is the slowest in 9 of the 12 d0/base/d11 runs. The d0 median is 158.3 fps in 0-10 s and 163.6-165.6 fps after.
- **W4b command (unchanged):** `python -B bench\agent7\w4b_readout\w4b_readout.py build\agent8\matrix\<W4b dir> -o bench\agent7\w4b_readout\out-<stamp>.md --json bench\agent7\w4b_readout\out-<stamp>.json`.

## Task #33: zero-code read-out (session 3, 07:50)

> **FUNCTIONAL ONLY and SAT.** These were agent-slot runs on the hidden desktop. The CPU was saturated (busy median ≥0.99), there is n=1 per arm, and each matrix holds a single arm. The numbers only feed S4 timing plans; they are never a result.

- **Asked (Agent 1, task #33, report by 08:20):** read out the zero-code runs 0652 / 0655 / 0657 with `w4b_readout.py`, read-only.
- **Arms:** from `bench/agent8/zero/matrix-native3d-zero-code.json`; all on `build/agent2/native3d-bin`, frontend off, uncapped.
  - n2t = n2 (`THREADED=1`, `PREPARE_THREADS=2`, `SNAPSHOT_STATE=1`) + `LEGO_NATIVE_TIMING=1`.
  - n3t = n3 (`THREADED=1`, `PREPARE_THREADS=2`, `FULL_DRAW_PREPARATION=1`) + `LEGO_NATIVE_TIMING=1`.
  - n2s = n2 + `LEGO_NATIVE_PARALLEL_DRAWS=0`.
- **Commands:** `python -B bench\agent7\w4b_readout\w4b_readout.py build\agent8\matrix\20261122-<stamp> --all -o bench\agent7\w4b_readout\out-<stamp>.md --json bench\agent7\w4b_readout\out-<stamp>.json`, for stamps 0652, 0655 and 0657.
  - All three exit 0.
  - Each run agrees with its frames.json (frames, mean fps, p50, p99, >33) and with results.csv fps_mean. Arm fps equals summary.md.
  - No `__pycache__` was written.
- **Window:** 60 s, starting 60.0 s after the first-frame signal (the runner's 60 s floor). That is 60–120 s after the first frame.

| arm | run | fps | p50 ms | p99 ms | 1% low fps | >33 ms/min | slow state in window (recheck / timerq) | game cores | background cores (p90; busy) |
|---|---|---|---|---|---|---|---|---|---|
| n2t | 0652-n2t-r1 | 136.7 | 6.450 | 21.55 | 32.9 | 23.0 | no / no | 1.87~ | ≥10.1 (10.3; 100 %) SAT |
| n3t | 0655-n3t-r1 | 122.9 | 5.894 | 37.20 | 21.8 | 114.0 | 100 s, 17 % ! / 100 s, 8 % | 1.91 | ≥10.1 (10.3; 100 %) SAT |
| n2s | 0657-n2s-r1 | 123.6 | 6.179 | 32.80 | 24.8 | 69.0 | 79 s, 32 % ! / 79 s, 15 % | 1.99~ | ≥10.0 (10.2; 100 %) SAT |

- **Scene check:** not possible. These are native-frames runs, so there are no guest draw counts (native-frames.csv `draw_calls` is the presenter's 8 draws on every frame). With one arm per matrix there is no reference pool either.
  - The phase column reads "normal". Light-frame shares: n2t 0.06, n3t 0.07, n2s 0.01.
- **Background:** every run is SAT, so ≥10 cores is a floor. Window 3 has no sys.csv, so there is no unsaturated reference and no BG+ verdict.
- **Functional checks:**
  - n2t and n3t: TIMING is active. `present_cpu_ms` and `present_submit_cpu_ms` are non-zero, and game.log has 16 and 18 `Native timing:` lines, one per frame of ≥40 ms. That is rate-limited, so the log cost is negligible.
  - n2s: game.log shows `Native draw batches: serial workers=2` (n2t: `parallel workers=2`). The present_* columns are 0 because TIMING is off.
- **10 s bins:** [zero_code_bins.py](<workspace>/bench/agent7/w4b_readout/zero_code_bins.py), output in [zero-code-bins.txt](<workspace>/bench/agent7/w4b_readout/zero-code-bins.txt). The onset is the first of 3+ sys.csv samples in a row with E-cores under 800 MHz. It reproduces the recheck onsets: n3t 100.2 s, n2s 78.5 s after the first-frame signal.

| arm | before the onset: s, fps, >33/min, p99 ms | after the onset: s, fps, >33/min, p99 ms | worst 10 s bin |
|---|---|---|---|
| n2t | no onset (whole window: 60 s, 136.7, 23.0, 21.6) | - | 10–20 s: 9 frames >33, p99 30.6 (E-cores 1505 MHz) |
| n3t | 40.1 s, 139.7, 56.8, 28.0 | 19.9 s, 89.1, 229.6, 46.0 | 40–50 s: 67.6 fps, 61 frames >33, p99 54.5 (E-cores 558 MHz) |
| n2s | 18.5 s, 143.3, 22.7, 22.2 | 41.5 s, 114.8, 89.7, 34.8 | 20–30 s: 92.4 fps, 35 frames >33, p99 42.4 (E-cores 566 MHz) |

- **The tail follows the E-core clock.**
  - n3t: 76 of its 114 frames >33 ms fall after the onset, which is a third of the window.
  - n2s: 58 of its 69 frames >33 ms fall in 20–40 s, the two bins whose E-core median is 566–663 MHz. Once the E-cores are back at 1086–1196 MHz (40–60 s), n2s is clean again: 0 and 1 frames >33 ms, p99 22.7 and 16.7 ms.
- **Co-occurrence (>33 ms frames vs the rest):**
  - n3t: `present_cpu_ms` 18.8 vs 2.8, `swap_present_cpu_ms` 12.6 vs 1.9, `present_submit_cpu_ms` 4.1 vs 0.5, `callbacks_pending` 72 vs 31, `frame_slot_wait_ms` 1.6 vs 0.7.
  - n2t: `present_cpu_ms` 5.2 vs 1.9, `swap_present_cpu_ms` 1.1 vs 0.9.
  - n2s (TIMING off, so only `swap_present_cpu_ms` is filled): 4.2 vs 1.2.
  - No arm has pipeline creations or sync_* waits in the window.
  - So in the slow state the present/swap call itself runs long. That fits S4-T1's premise (chain threads landing on throttled cores) but does not prove it.
- **Before the onset:** n2s (22.7/min, p99 22.2) looks like n2t (23.0/min, p99 21.6), so PARALLEL_DRAWS=0 shows no tail change. n3t is higher (56.8/min, p99 28.0). That could be n3's FULL_DRAW_PREPARATION, but it rests on 38 frames from 40 s, and the E-cores already dipped to 1052 MHz at 30–40 s. All of this is n=1.
- **Verdict:** these runs can't attribute the tail to TIMING, PARALLEL_DRAWS or n2 vs n3. In n3t and n2s the tail is mostly the slow state. S4-T1 stays staged.
- **Addendum (07:50), after Agent 4's code fact (07:45):**
  - Where the present runs: in n2 and n2s, SwapHook (draw.cpp:5448) runs on WorkerMain, which is ABOVE_NORMAL (native_worker.cpp:347-349). In n3, the coordinator forwards it to RecorderMain (:152-194), which runs at NORMAL. All three game.logs show inline=0 drains=0.
  - `swap_present_cpu_ms` on the >33 ms frames vs the rest, before and after the onset (scratch `zc_split.py`, read-only):
    - n2t (no onset): 1.1 vs 0.9.
    - n3t before the onset: 6.4 vs 1.6 (`present_cpu_ms` 9.4 vs 2.4). After the onset: 15.6 vs 2.9 (`present_cpu_ms` 23.5 vs 4.4).
    - n2s before the onset: 1.0 vs 1.0. After the onset: 4.6 vs 1.3.
  - Reading (n=1, SAT):
    - n3's NORMAL present path already grows before the slow state, which fits Agent 4's priority explanation for n3t's pre-onset tail.
    - In the slow state, ABOVE_NORMAL looks like partial protection: the swap grows +3.3 ms in n2s against +12.8 ms in n3t.
    - About 35 ms of n2s's ~40 ms slow frames lies outside the swap.
  - Test-design note (sent to Agent 4):
    - S4-T1 as specced also raises the RecordingQueue thread and the prep-pool workers, and opts every chain thread out of EcoQoS. So in n2, ON is not EcoQoS-only.
    - A split value (1 = priority, 2 = EcoQoS opt-out, 3 = both) would isolate the lever. Agent 4 adopted it at 07:52, and the S4-T1 spec in "Task #26" now carries it.
    - Tonight's slot runs were all SAT, which is where priority matters most. Record SAT per run, and don't assume a gain measured SAT carries over to an unsaturated machine.
- **What a timed S4 test still has to show:**
  - n ≥ 3 per arm, interleaved, with an n0/d0-type reference arm in the same matrix (here every matrix had one arm);
  - an unsaturated machine: busy median < 0.97, i.e. a background cell without SAT. Every sys.csv window tonight was SAT: PresentMon under FrameView takes ~1 core, Dell TechHub ~1, and Defender 1.8–3.7 at times;
  - sys.csv on, with the slow state checked per run (recheck and timerq), and slow runs dropped or scored only up to the onset;
  - scoring from ≥60 s after the first frame, over a window of ≥60 s;
  - p99, 1 % low and >33 ms/min as the primary metrics (the adopted metric rule), fps secondary;
  - TIMING=1 in every arm or in none.
- **Window-3 correction (from task #29):** with d11-r1 flagged (light phase, scene 0.036), d11 reads 157.8 fps (157.5..160.3), n=3, −3.1 % vs d0, with every run outside d0's range. It previously read −2.3 % with overlapping ranges. Sent to Agent 11 for S4-DRAFT.md.

## Task #29: W4b read-out add-on (session 3, 07:35)

This is an optional, read-only add-on to Agent 8's W4b read-out. It applies the metric rule adopted after #26. Agent 8 owns the read-out and decides whether to use it.

- Tool: `bench/agent7/w4b_readout/w4b_readout.py`, with its self-test `test_w4b_readout.py` and `README.md`.
- It writes only `-o` and `--json`, and no `__pycache__`.
- It imports `bench/agent8/run/matrix_recheck.py` read-only and runs `bench/agent11/timerq_slowstate.ps1` as a read-only subprocess.

### What Agent 8 runs

Run this after the W4b timing matrix ends. It takes about 3 s, plus the timerq call:

```
python bench\agent7\w4b_readout\w4b_readout.py build\agent8\matrix\<W4b dir> -o bench\agent7\w4b_readout\out-<W4b dir>.md --json bench\agent7\w4b_readout\out-<W4b dir>.json
```

- Use `--all` only for functional matrices (agent-launched or `-Quick`). With it, the report carries a FUNCTIONAL ONLY banner.
- `--no-timerq` skips Agent 11's script.
- The background defaults are `--bg-ref` window 3, `--bg-margin 1.0` and `--sat-busy 0.97`. On a quiet morning run, `--bg-ref-cores X` fixes the reference.

### What it reports

**Per run**, over the runner's own scored window (frames.json `first_row`/`rows`):
- fps, p50, p99, the 1% low and >33 ms/min;
- a check against frames.json and results.csv;
- draws/frame and the scene distance;
- the runner's phase flag;
- the slow state, from both `matrix_recheck` and timerq;
- game cores and background cores.

**Per arm:**
- median (min..max), fps spread, and `n<3!` for arms with fewer than 3 runs;
- deltas against d0, marked better/worse only when every run lies outside d0's range;
- a per-round paired fps delta.

**Clean tables:** a second set of tables leaves out runs that have the slow state in the window, a SCENE? flag, BG+, or SAT (SAT only when not every run is SAT).

### Background load (Agent 1, 06:55)

**Formula.**
- system = 12 × min(1, `cpu_util_pct`/`cpu_perf_pct`), per sys.csv sample in the window;
- game = the proc.csv `cpu_s` slope;
- background = system − game;
- cell = median (p90; busy %).

**Validation.** With no game running, util/perf read +0.01 to +0.07 above `% Processor Time`/100 in 17 live 1 s samples (07:06 and 07:11). That held at 1 ms timer resolution too. One sample with util = perf is why the cell uses the median.

**Finding: every in-game window with sys.csv tonight was CPU-saturated.**
- The 20 runs from 0330 to 0657 had a window-median busy share of 0.994–1.000. The only exception is 0336-cold-d0 at 0.921.
- So background = 12 − game ≈ 9.5–10.3 cores, and that value is only a floor. Defender's 1.8–3.7 cores can't raise it; they take CPU from the game instead.
- The tool marks such runs SAT and prints a CPU SATURATED banner. BG+ (background > reference + 1.0 cores) applies only to unsaturated runs.
- Agent 3's sampler agrees (05:12–05:37, `build/agent3/logs/cpu-sampler-0528.csv`): 97–100% busy, msmpeng 1.2–4.8 cores, PresentMon_x64 1.0, dwm ~1.1.

**Standing load that is neither ours nor the game's.** PresentMon_x64 takes 1.0 core; it is a child of NVIDIA FrameView's `nvfvsdksvc_x64` and has run since 11-13. Dell TechHub DataManager.SubAgent takes ~1.0 core.

**Window 3 can't be the reference.**
- None of its 19 runs has sys.csv. Only 0330, 0336, 0342, 0349, 0620, 0652, 0655 and 0657 have it.
- The tool says so and prints window 3's game cores per arm instead (proc.csv over the scored window): d0 3.43, base 3.42, d11 3.47, n0 2.33.
- Reference order: `--bg-ref-cores`, then the unsaturated scored runs of `--bg-ref`, then this matrix's own unsaturated runs, then none.

### Scene check calibration

The scene distance is a 1-D Wasserstein distance on ln(1 + draws). Measured values:

| runs | distance |
|---|---|
| same scene: 2232, 0013, 0330–0349, 0620 | 0.000–0.005 (window 3's d0 leave-one-out 0.000; highest 0346-d3-r1 at 0.005) |
| window 3's light-phase run 0025-d11-r1 (draws 218 vs 226, 294.6 fps) | 0.036 |
| unscored cold runs | 0.016–0.019 |

- I lowered the floor from 0.15 to 0.015: 3× the largest same-scene distance, and under half the light-phase distance.
- With 0.015, 0013 flags 0025-d11-r1. Without that run, d11 is n=3 at 157.8 fps (157.5..160.3), −3.1% against d0 and "worse". With it, d11 was −2.3% and "overlap", with an 86% spread.
- The arm medians don't change.
- Native-frames runs have no guest draw counts, so they aren't compared.

### Outputs and self-test

**`out-0013` (window 3):**
- 19/19 runs agree with frames.json and with results.csv `fps_mean`.
- Arm fps match Agent 8's window-3 `summary.md`: d0 162.857 (summary.md 162.858), base 160.802, d11 159.038, n0 143.217.
- No background values (no sys.csv). timerq matched 0 of 19 runs.

**`out-0342` (W4b `-Quick` dry run, `--all`, FUNCTIONAL ONLY):**
- 5/5 runs agree. Arm fps: d0 172.107, B 100.348, d3 94.202, d0t 166.342.
- d0-r1, B-r1 and d3-r1 have the slow state in the window. The onsets (39/29/37 s) are the same in recheck and timerq.
- Every run is SAT (background ≥ 9.6–10.3 cores), so the clean table keeps only d0t.

**Self-test** (`python bench\agent7\w4b_readout\test_w4b_readout.py`): 12 tests OK at 07:24, including the PowerShell timerq integration. It uses a synthetic 10-run matrix and covers:
- stats and nearest rank;
- scene distance, including the light-phase and 1-draw-jitter cases at the default floor;
- slow state;
- background: SAT, BG+, the reference dir, `--bg-ref-cores` and the proc.csv fallback;
- mismatch reporting;
- no bytecode.

**Integrity checks:**
- No new `__pycache__`. The ones in `bench/agent7` and `bench/agent8/run` predate 06:00.
- The W4b chain is unchanged: `RUN-WINDOW4B.cmd`, `run-matrix.ps1`, `run-timing.ps1`, `common.ps1`, `matrix-window4.json` and `matrix_recheck.py` were last written 03:15–04:23, and `harness/legodimensions.toml` on 11-21 at 21:45.

### For the W4b read-out

- Score p99, the 1% low and >33 ms/min as well as mean fps, with n ≥ 3 per arm.
- If the morning run is unsaturated, BG+ becomes meaningful.
- If it is SAT again, the per-round paired deltas still compare the arms, but the absolute fps are CPU-contended.

## Task #26: THREADED tail latency in the native3d n-rows (session 3, 06:20)

Task #26 is Agent 1's question from 05:38. In the native3d n-rows (`build/agent8/matrix/20261122-0452`, functional, n=1), `LEGO_NATIVE_THREADED=1` raised fps from 101 to 110/117, but frames over 33 ms went from 8 to 74/68 and p99 from 23.8 to 33.7/32.2 ms. Why? Rules: read-only on the source trees, ≤2 threads, no builds or game runs, no `--write` on others' tools, notes only from 08:30. One research subagent mapped the THREADED code (reported 05:51). **All numbers here are functional (n=1, hidden desktop, unfocused, uncapped), never timing.**

**Arms** (from each run's `summary.txt` env). All three have 3 command slots, swap-chain max frame latency 1 (waitable, `latency_wait=0`) and tearing on.

| arm | THREADED env | busiest threads (thread-cpu) |
|---|---|---|
| n0 | off | render XThread 78% (the guest records inline) |
| n2, "mode A" | `THREADED=1 SNAPSHOT_STATE=1 PREPARE_THREADS=2` | worker "Native GPU preparation" 55.8%; RecordingQueue thread "Native GPU recording" 11% |
| n3, "mode B" | `THREADED=1 FULL_DRAW_PREPARATION=1 PREPARE_THREADS=2` | recorder "Native GPU recording" 55.4%; coordinator (the worker thread) 20.7% |

**Short answer: structural, with an incidental trigger.**
- With THREADED on, the guest's swap queues the present and then waits until the worker chain is at most one frame behind (draw.cpp:5447-5451).
- The chain is 3–4 threads joined by blocking waits, and in these runs it sets the frame rate: in the window the guest waits at that throttle for 46–76% of the wall time.
- In the slower phases the chain's time per frame doubles. Any stall in one of its threads then goes straight to the screen as one long frame, because there is no slack to absorb it.
- At the same throughput (85–100 fps), THREADED makes about 2 frames >33 ms per second, against about 0.2 for n0.
- Which phases are slow is incidental (scene content or CPU state). The slow state can't be excluded.

### 1. Slow-state control: not applicable

- `python bench\agent8\run\matrix_recheck.py build\agent8\matrix\20261122-0452 --all` (no `--write`) shows the slow column as `-` for n0, n2 and n3. The functional matrix ran only `drivers/thread-cpu.ps1`, so there is no sys.csv (no E-core clock).
- `bench\agent11\timerq_slowstate.ps1 -Since 20261122-0452` finds 0 runs, for the same reason.
- Context: with `-Since 20261122-0300` the slow state hit 12 of 16 runs, with onsets 27–100 s after the first frame. The n-row windows are 60–120 s after the first frame, so any of the three arms could have been in it.
- The GPU clock is no proxy:
  - gpu.csv shows clock dips in all three arms: idle throttle reason 0x1, ~1000–1340 MHz vs 1740, ~11 W vs 17 W, utilisation flat at 30–42%. So the GPU idles there; it doesn't limit.
  - On 12 runs with sys.csv from the 03:30–03:49 W4 functional/dry-run matrices (0330–0349), GPU MHz vs E-core MHz gives Spearman −0.22 over 39 bins (power: −0.04). (Until 07:35 this line called them "window-3 runs". Window 3 has no sys.csv in any of its 19 runs.)
- So the stop condition ("n2/n3 in the slow state, n0 not") is not established either way, and I continued.
- THREADED is probably more exposed to the slow state than n0, but that can't be checked without per-thread core data. Its chain threads are unpinned and mostly NORMAL priority, so they can land on E-cores, which run at ~550 MHz in that state. n0's recording runs on a pinned guest thread.

Recheck numbers (runner window, 60 s each; ms unless noted; 1% low = mean of the slowest 1% of frames, as fps):

| arm | fps | p50 | p95 | p99 | p99.9 | 1% low | >33 ms | 20–33 ms |
|---|---|---|---|---|---|---|---|---|
| n0 | 101.0 | 9.26 | 15.85 | 23.7 | 34.9 | 35.2 fps | 8 | 113 (1.9%) |
| n2 | 109.6 | 7.21 | 21.64 | 33.7 | 54.5 | 23.2 fps | 74 | 322 (4.9%) |
| n3 | 116.7 | 6.68 | 19.55 | 32.3 | 51.4 | 24.1 fps | 68 | 273 (3.9%) |

### 2. Where the slow frames are and what comes with them

**Shape.**
- They are isolated single frames: n2 has 70 singles and 2 pairs, n3 has 62 singles and 3 pairs (n0: 6 singles and 1 pair).
- The frames around them are normal (median ~7 ms), and no short catch-up frame follows (0 of 74, 0 of 68).
- The time they spend above the median is 0.4% (n0), 4.3% (n2) and 4.0% (n3) of the window.
- Not warm-up: the window starts ~69 s after launch, and the slow frames are spread through it.
- Not periodic: per-second counts have Fano factors of 1.7 (n2) and 3.7 (n3), and the gaps have a CV of 1.5 and 2.1. That is bursty, with no period.

**Placement: they follow the slower phases.** Per 10 s of the window:

| arm | >33 ms frames per bin | fps per bin |
|---|---|---|
| n0 | 0, 0, 0, 1, 4, 3 | 113, 121, 95, 96, 93, 88 |
| n2 | 2, 5, 15, 16, 32, 4 | 133, 131, 93, 86, 90, 124 |
| n3 | 7, 10, 2, 44, 4, 1 | 89, 111, 141, 96, 118, 144 |

n0's last four bins run at 88–96 fps, the same as n2's slow bins (86–93), but they have 0–4 slow frames per bin instead of 15–32.

**The guest waits on the chain.**
- game.log's "Native worker: last 600 frames … throttle_wait=" line (draw.cpp:5457-5463) sums the guest's wait in `NativeWorkerThrottleFrames(1)` (draw.cpp:5451, native_worker.cpp:574-583). That is a condition-variable wait with no timeout, until `g_pending_presents <= 1`.
- I aligned the 600-frame chunks with the window using the log timestamps (offset +5 to +13 frames; `build/agent7/tail/throttle-align.txt`).
- In the window the guest waits 3.4–8.5 ms per frame in n2 and 3.7–9.4 ms in n3. That is 46–74% and 57–76% of wall time.
- The share is high in the fast phases too: 0.62–0.76 before the window, at 165–215 fps, with only 2 slow frames per 4,200.
  - What changes in the slow phases is the chain's time per frame, ~5.9 → ~11.5 ms. The guest's wait doubles with it, ~3.8 → ~8 ms per frame.
- Per chunk, the slow-frame count tracks the throttle: Spearman 0.92 in both n2 (11 chunks) and n3 (12 chunks).
  - n2's chunks 21–24 (85–93 fps, share 0.66–0.74, throttle 7.1–8.5 ms per frame) hold 60 of its 74 slow frames.
- Note: `interval_ms` in native-frames.csv is the worker/recorder's present-to-present time (device.cpp:2290-2297), not the guest's swap-to-swap time.

**Ruled out in the window:**
- **LockRecording drains:** every in-window worker line says `drains=0 inline=0 drain_wait=0.0ms`. Drain waits occur only before the window:
  - n2: 25 drains and 255 inline runs at 04:54:46, then 6 and 8 at 04:55:15;
  - n3: 71 ms and 743 ms of capture-drain wait in its first 1,200 frames.
- **PollCompletionCallbacks:** it only try_locks (device.cpp:1361-1363), so it never blocks.
- **Pipeline creation and Synchronize:** `pipeline_creations` is always counted and is 0, and `sync_calls` is 0.
- **Completion-callback bursts:**
  - n3's pending count peaks at ~198. Without `LEGO_NATIVE_BATCH_COMPLETION_CALLBACKS=1`, the drain runs one callback per try_lock round (device.cpp:1367).
  - A burst frame costs ~+5 ms (median 11.5 vs 6.7 ms). But P(>33 ms | ≥50 executed) is 0.012, against 0.0097 otherwise: 1 of n3's 68 slow frames.
  - n2 shows no link.
- **Timer quantum:**
  - The hot paths have no Sleep(1) or short timeout. Every wait is a cv wait without timeout, except the drain's 200 µs `wait_for` (native_worker.cpp:543), which isn't used here.
  - The excess over the median is spread over 8–28 ms (median 15.8 / 15.7 ms, vs 11.0 for n0), with no peaks at 15.6 or 31.2 ms.
  - The SDK keeps its timer resolution in the background (`src/core/threading_win.cpp:134-157`) only if `keep_timer_resolution_in_background` is set. game.log doesn't say whether it was.
- **60 Hz vblank gating:** all presents are weakly phase-locked to 16.6665 ms (Rayleigh R 0.20–0.31 for ordinary frames). Frames with a swap ≥5 ms are no more locked in n2/n3 (R 0.14/0.19, against 0.20/0.24 for the controls).
- **`perf.functions_dispatched`** grows with frame length (~0.2 per ms), so it is an effect, not a cause.

**Columns.**
- `LEGO_NATIVE_TIMING` was unset (textures.cpp:1531-1541; any non-empty value turns it on). So every `*_ms` stage column, `frame_slot_wait_ms`, `present_cpu_ms` etc. is 0, and `frame_slot_wait_calls` is a constant 2.
- The guest's throttle wait and the chain's joins aren't in any CSV column.
- The one live timer is `swap_present_cpu_ms` (device.cpp:2177-2281: DXGI Present, `rex::perf::WriteCsvFrame` and the overlay/settings publish, all on the worker). It splits the slow frames into two kinds:

| | n0 | n2 | n3 |
|---|---|---|---|
| type S: swap ≥10 ms (the excess sits in the swap; per-frame p75 share 99%) | 3 | 33 | 30 |
| type O: swap <5 ms (the excess sits in untimed chain waits) | 5 | 41 | 35 |
| frames with swap ≥10 ms per minute (all frames) | 20 | 103 | 196 |
| P(>33 ms given swap ≥10 ms) | 0.15 | 0.32 | 0.15 |
| swap's share of the slow frames' excess | 21% | 41% | 40% |

n3 also has 3 slow frames with a swap of 5–10 ms.

### 3. Verdict, S4 candidate, metric rule

**Verdict: structural, with an incidental trigger.**
- **Structural.** THREADED turns one guest thread into a pipeline of 3–4 threads joined by blocking waits, and the swap holds the guest to at most one frame ahead of it (draw.cpp:5448-5451).
  - **Mode A (n2):** the worker is the only thread raised to ABOVE_NORMAL (native_worker.cpp:349). It holds the recording lock, blocks on the prep pool's `job.get()` (draw.cpp:5687-5711) and joins the RecordingQueue at every `end()` (native_recording.cpp:335, :166-170). Then it waits for a frame slot's fence and calls DXGI Present.
  - **Mode B (n3):** the coordinator (the worker thread) waits at barriers (native_worker.cpp:220). The recorder (started at native_worker.cpp:346), n3's busiest thread at 55%, runs at NORMAL priority.
  - **Other threads:** the RecordingQueue thread (native_recording.cpp:138) and the prep pool (native_preparation.h:21-26) are NORMAL and unpinned. The guest XThreads are each pinned to one logical CPU in 0–5 (SDK `src/system/xthread.cpp:919-922`), with game-set priorities up to HIGHEST (:866-880). The CPU has 12 logical processors, likely 2P+8E.
  - **Result:** in the slower phases the chain is the bottleneck and has no slack. A stall in any one of its threads (preemption, a long Present, a join) reaches the screen 1:1 as an isolated long frame. n0 runs the same phases on one thread with no handoffs and gets ~10× fewer.
- **Incidental:** which phases are slow (scene content or CPU state; the slow state can't be excluded), the hidden desktop, and n=1.
- **Unresolved:** which chain wait carries the type O frames, and why Present takes ≥10 ms while the GPU idles. Both need `LEGO_NATIVE_TIMING=1`.

**S4-T1 (proposal): `LEGO_NATIVE_CHAIN_PRIORITY`, default OFF (unset or 0).** The values were updated at 07:52 with Agent 4 (their notes, SS3.5 "#33"). One bin serves every arm.
- **Values:**
  - `1` = priority only. Give the recorder, the RecordingQueue thread and the prep-pool workers `THREAD_PRIORITY_ABOVE_NORMAL`, as the worker already has.
  - `2` = EcoQoS opt-out only, with no priority change. Opt every chain thread out of EcoQoS: the worker/coordinator, the recorder, the RecordingQueue thread and the prep-pool workers. Use `SetThreadInformation(ThreadPowerThrottling)` with ControlMask = EXECUTION_SPEED and StateMask = 0.
  - `3` = both.
  - Why split: in n2 the present (SwapHook, draw.cpp:5448) already runs on the ABOVE_NORMAL worker (native_worker.cpp:347-349). In n3 it runs on the NORMAL recorder (:152-194). So a gain from `3` alone can't separate the priority lever from the EcoQoS lever (see the Task #33 addendum).
  - Value `2` has a low prior (Agent 4, 07:56). Agent 11's task #24 (agent11-kernel.md, "Result (task #24)") applied a process-level EXECUTION_SPEED opt-out: d0 vs d0e, 3 pairs, held in 99.6–99.7 % of reads. The ~550 MHz E-core state still came in 3/3 runs on each side, and Agent 1 dropped the opt-out from S4 at 06:28. But #24 measured the onset, not the tail, and a per-thread tag can act differently (thread placement rather than the cluster clock). So `2` keeps its step-3 arm.
- **Output-identical:** it changes scheduling only. Ordering is fixed by the queues, cvs and fences, so the frames and their content don't change.
- **Files:**
  - native_worker.cpp: the RecorderMain start at :346;
  - native_recording.cpp: the RecordingQueue thread at :138;
  - native_preparation.h: the pool workers at :21-26.
  - Parse the value once in a helper, the way `NativeWorkerEnabled()` does. Any other value means OFF.
  - Log one line naming the mode, at INFO like native_worker.cpp:323. check_n_rows.py counts warning, error and critical lines as types (`LEVEL_RE`, :43), so a WARN line would fail arms 1–3. Agent 4 adds a mode-line check to check_n_rows.py for step 1.
- **Risk: low to medium.** ABOVE_NORMAL chain threads (not HIGHEST) could delay guest XThreads on the shared cores. Watch the guest's frame time and the audio.
- **Expected effect:** on p99, the 1% low and the >33 ms count, not on mean fps. The size isn't known. A gain measured only on SAT runs doesn't carry over to an unsaturated machine.
- **Test (staged with Agent 4, 07:52):**
  1. a functional run, 0 vs 3, with frames.json and identical output, plus the mode line in game.log for each of 1, 2 and 3;
  2. the timed matrix to the Task #33 checklist: n2/n3 × {0, 3} plus n0 as the reference arm, ≥3 runs each, interleaved, scored by the metric rule below, with SAT recorded per run (w4b_readout bg column). It runs focused in Agent 8's runner, since #24 left visibility QoS open. If the focused arm-0 runs show no slow state and no >33 ms excess (n2-0 and n3-0 within n0's range on >33 ms/min and p99), T1 is dropped at step 2;
  3. n2/n3 × {1, 2} only if `3` helps. Drop T1 if `3` helps in neither mode.

**Zero-code checks first** (functional, Agent 8's slot, at Agent 1's discretion):
- n2 and n3 with `LEGO_NATIVE_TIMING=1`, to see which chain stage holds the type O excess and how the swap splits;
- n2 with `LEGO_NATIVE_PARALLEL_DRAWS=0` (the switch at draw.cpp:5577-5590). It removes the prep-pool joins; "prepare 2" is only 1.1% busy.

**Not proposed: `NativeWorkerThrottleFrames(2)`.**
- It would add up to one frame of latency.
- The comment at draw.cpp:5449-5450 says the game's pacing assumes at most one.
- It only absorbs hiccups on the guest side, not stalls in the chain.

**Instrumentation (later, under TIMING or its own default-OFF switch):** put the guest's `throttle_us` (native_worker.cpp:582), the drain wait and the worker's join/barrier time per frame into native-frames.csv.

**Metric rule: yes.**
- A later THREADED timing window should score p99, the 1% low and frames >33 ms per minute as primary metrics next to mean fps, with p99.9 as secondary.
- Here THREADED gains 8.5% / 15.5% fps but loses 34% / 31% of the 1% low, and has ~9× the frames >33 ms.
- Use ≥3 runs per arm with sys.csv (so the slow state can be checked), focused if possible.
- Report per phase (10 s bins or 600-frame chunks), because the slow frames sit in particular phases.

**Tools and outputs:**
- `bench/agent7/threaded_tail.py`, tested by `bench/agent7/test_threaded_tail.py` (4/4 OK). It covers the window from frames.json, percentiles, the histogram, 10 s bins, clustering, the CSV columns vs slow frames, conditional rates and the swap split. Outputs: `build/agent7/tail/threaded-tail.txt` and `threaded-tail-callbacks.txt`.
- Helpers in `bench/agent7/tail/` (run from the repo root): `tail_rows.py`, `tail_quanta.py`, `throttle_align.py`, `gpu_bins.py`, `slowstate_gpu_proxy.py`, `vblank_phase.py`. Their outputs have the same names in `build/agent7/tail/` (`tail-rows.txt`, `tail-quanta.txt`, `throttle-align.txt`, `gpu-bins.txt`, `slowstate-gpu-proxy.txt`, `vblank-phase.txt`).
- Paths: gpu_native files are relative to `DimensionsRecomp/rexlego/src/gpu_native/`, SDK paths to `DimensionsRecomp/rexglue-sdk/`.

## Task #22: shader dumps, native3d n-rows and `RefreshGuestOutput` (session 3, 05:33)

Task #22 is Agent 1's set of follow-ups to #13 (sent 04:54, per the 04:46 decisions). Rules: ≤2 threads, no builds, game runs only through Agent 8's slot, notes only from 08:30. No subagent was used.

### 1. Shader dump run (`sd`)

**Spec:** `bench/agent7/matrix-shader-dump.json`, sent to Agent 8 at ~05:02. `run-matrix.ps1 -PlanOnly` passed; the runner raised the warm-up from 30 to 60 s.
- One arm, `sd`: native3d-bin (exe `B90DF683D0A57A21`) with the n0 arm of `bench/agent4/s3/matrix-native3d-functional.json`. That is: frontend off, `native_fps_limit=0`, `framerate_limit=0`, native frames, `drivers/thread-cpu.ps1`.
- Plus `LEGO_DUMP_MISSING_SHADERS=<run>\shader-dumps`. The runner expands `<run>` to the absolute run dir.
  - The value is the dump root (shaders.cpp:355–372), so never `1`.
  - It also turns on the pool-copy XXH3 check (hooks_buffer.cpp:331–345), so the run is functional only.

**Run:** Agent 8, 05:09:09–05:11:40, in `build/agent8/matrix/20261122-0509/runs/0509-sd-r1`. Exit 0, clean close, no .dmp. Agent 8's log is `build/agent8/scratch/sdump-run.log`.

**Results.** `python bench\agent7\shader_dump_check.py <run> -o build\agent7\sd\shader-dump-check.txt` gives RESULT PASS.
1. **Bin dir vs MANIFEST: PASS before (05:00) and after (05:14)**, in `build/agent7/sd/bin-check-{pre,post}.txt`.
   - All 8 listed files match their hashes, and there are no extra files or dirs.
   - The newest file is still the MANIFEST (sha256 `368F9CE650EC56CE`, 03:46:16).
   - So nothing was written to native3d-bin.
2. **Dumps:** 9 files and 9 "dumped missing shader" lines.
   - 0 failed dumps, 0 dir errors, 0 pool-verify failures, 0 `hash=0` lines.
   - 8 "missing from AOT index" warnings: 4 VS + 4 PS, all at 05:09:34.

| dir | file | bytes | physical | first physical words | shader |
|---|---|---|---|---|---|
| `placement-containers` | `vs-ACAF01F01E1C03D2.bin` | 1304 | 0x144 | `F2556004 600A1200 12000000 00006010` | VS `0xAC449538` |
| `placement-containers` | `ps-75A4D1ABA62F7594.bin` | 1716 | 0xD0 | 12 zero words, then `3DE978D5 3F1645A2 3E991687 00000000` | PS `0xAC448F28` |
| `placement-containers` | `vs-CCD7655302B54D80.bin` | 944 | 0x120 | `70956004 600A1200 12000000 00005010` | 2nd VS (05:10:01) |
| `placement-containers` | `ps-E81FD692C3AB35E1.bin` | 1640 | 0xB8 | 12 zero words, then `3DE978D5 3E991687 3F1645A2` | 2nd PS (05:10:01) |
| `placement-raw` | `vs-DCD4AD8441398283.bin` | 2048 | (raw) | `F2556004 600A1200 …` | VS backing `0xED23D3E0` |
| `placement-raw` | `ps-C77B3ABB6F87ACD9.bin` | 2048 | (raw) | 8 zero words, … | PS backing `0xED23D540` |
| `placement-raw` | `vs-98D43959C65B882A.bin` | 96 | (raw) | `70956004 600A1200 …` | 2nd VS |
| top level | `vs-A58EBA123EFB541C.bin` | 704 | 0x190 | (no marker) | "not present in AOT cache" miss (CreateShaderResource, shaders.cpp:514) |
| top level | `ps-93B9F93B535E7CCA.bin` | 156 | 0x24 | (no marker) | same |

3. **PS `0xAC448F28` is not all zero.**
   - The container's physical section is 208 B, 103 of them non-zero.
   - Words 0–11 are zero, which fits Agent 4's "first 4 words are zero at bind".
   - From byte 48 it reads `3DE978D5 3F1645A2 3E991687 00000000 00011003 00001200 C4000000 00002004 20061000 56000000 00003008 00002000 …`. That is three floats (0.114, 0.587, 0.299: the Rec.601 luma weights), then code-like words.
   - The raw dump (2048 B read from the backing) matches the container's physical section over all 208 B.
   - The VS raw dump holds the same bytes at +0x160 (= `0xED23D540 − 0xED23D3E0`). The VS physical section ends at +0x144, followed by 28 zero bytes and then the PS. So the capture agrees with guest memory.
4. **Handed to Agent 4 at 05:18:** the dir, the report and the facts above.
5. **Real data, not a capture artifact** (Agent 4's question at 06:10, answered 06:20). Tool `bench/agent7/sd/ps_words_check.py`, output `build/agent7/sd/ps-words-check.txt`.
   - In both placement PS containers the physical section is [64 B of literal constants][microcode]. The definition table has one entry, `01FC0010 00000000`: register 0x1FC, 16 floats, at physical offset 0. So words 0–11 are three zero float4s, and words 12–15 are the luma weights (0.114, 0.587, 0.299, 0; the second PS has 0.114, 0.299, 0.587, 0).
   - The shader descriptor (at `shader_offset`) puts the microcode at physical offset 0x40, size 0x90 (second PS: 0x78). That ends exactly at `physical_size` (208 / 184).
   - From 0x40 the words decode as a well-formed Xenos PS control-flow program: 5 CF instructions in 3 slots, `ALLOC` colors, ending in `EXEC_END`, with ALU slots 3–10 (second PS: 3–8). The scan finds no other start offset. Word 0 doesn't decode (8 NOPs, then out-of-range addresses).
   - Both VS have no definition table, and their microcode starts at physical offset 0 (7 CF in 4 slots, `ALLOC` position and interpolators).
   - All four pass the size and marker checks. Each VS/PS pair has matching interpolator words: VS `ACAF01F0…` / PS `75A4D1AB…` 0x2042, and VS `CCD76553…` / PS `E81FD692…` 0x1021.
   - So the zero words at bind are the literal block at the start of the physical section. `FindShaderByMicrocode` already expects zero prefixes: it picks candidates by the 8-byte prefix hash, then checks the full physical hash for each candidate size (shader_archive.cpp:339–345, "Thousands of physical shader sections share eight zero prefix bytes").
   - Packing all four containers is fine on this evidence, as long as each pack entry's size and hash cover the whole physical section, literal block included.

**Notes on the dumps:**
- **Missing warning lines (Agent 4, 05:28).** The second pair (05:10:01) has no warning lines of its own. All three shader warnings share one counter, `g_shader_warning_count` (shaders.cpp:76), capped at <16 (:262, :297) and <32 (:571). By 05:10 it was past 32, so the second pair was dumped with no line.
  - The same counter explains n3's "8× instead of 4×" (§2). Full preparation skips BindShader, so "missing" gets all 16 slots instead of alternating with "unrecognized".
- **No raw file for `ps-E81FD692C3AB35E1`.** Its zero prefix gives the existing raw name `ps-C77B3ABB6F87ACD9.bin`, and the capture skips existing names.
- **Layouts.**
  - A placement container (`CaptureMissingPlacementShader`, shaders.cpp:146–207) has three parts: the virtual section, a 4-byte marker (a copy of header bytes 8–11), then the physical microcode. The virtual section starts with the big-endian `ShaderContainer` (d3d.h:116).
  - The top-level dumps are virtual + physical with no marker. Their sizes add up exactly: 0x130 + 0x190 = 704, and 0x78 + 0x24 = 156.

**New tools** (both tests pass):
- `bench/agent7/bin_manifest_check.py <bin dir>` (`check(bin_dir, manifest, do_hash)`). It walks the dir and fails on a hash mismatch, a missing file or any extra file or dir. Test `test_bin_manifest_check.py`: 4/4 OK.
- `bench/agent7/shader_dump_check.py <run> [--bin DIR] [--dumps DIR] [-o OUT]`. Test `test_shader_dump_check.py`: 4/4 OK. It:
  - parses the containers;
  - links raw dumps to the warnings (raw name = XXH3 of the first 8 bytes = the logged prefix);
  - compares raw dumps with the container physical sections;
  - greps game.log;
  - runs the bin check.

### 2. native3d n-rows (read with Agent 4, numbers sent ~05:03)

**Runs:** Agent 8's `build/agent8/matrix/20261122-0452/runs/{0452-n0-r1, 0454-n2-r1, 0456-n3-r1}`. All use native3d-bin with the n0 flags (frontend off, uncapped), one functional run each, on the hidden desktop. **Not timing** (n = 1, unfocused).

**Outputs**, saved at 05:21:
- `build/agent7/n-rows/native-summary.txt`, from `native_frames_summary.py --runner-window`;
- `thread-per-frame.txt`, from `w3_thread_per_frame.py --diff n2:n0 --diff n3:n0`.

| | n0 | n2 | n3 |
|---|---|---|---|
| env (besides frame metrics) | none | `LEGO_NATIVE_THREADED=1`, `_PREPARE_THREADS=2`, `_SNAPSHOT_STATE=1` | `LEGO_NATIVE_THREADED=1`, `_PREPARE_THREADS=2`, `_FULL_DRAW_PREPARATION=1` |
| fps (60 s runner window) | 101.0 | 109.6 | 116.7 |
| p50 / p99 / p99.9 (ms) | 9.27 / 23.8 / 34.8 | 7.21 / 33.7 / 54.5 | 6.68 / 32.2 / 51.4 |
| frames > 33 ms | 8 | 74 | 68 |
| `swap_present_cpu_ms` | 1.60 | 1.40 | 2.50 |
| CPU ms/f: Main / render XThread / unnamed | 4.33 / 7.76 / 0.94 | 2.98 / 1.51 / 7.32 | 3.19 / 1.39 / 8.05 |
| CPU ms/f, total | 18.9 | 16.7 | 18.0 |

- **THREADED** moves the render thread's recording to unnamed workers: render −6.3 ms/f, unnamed +6.4 (n2) and +7.1 (n3).
  - Mean fps is up 9% (n2) and 16% (n3), and p50 is down.
  - But the tail is much worse: p99 is up 9–10 ms, and there are 8–9× as many frames over 33 ms.
  - Whether this is a net win needs the window-4 timing A/B (Agent 10's condition, §5).
- **`gpu_cmd` is 0 in every native row.** Native never runs `RefreshGuestOutput`, so §3–§4 apply to devoff only.
- **game.log:**
  - 0 `hash=0` lines and 0 "shader cache miss" lines in all three rows.
  - n2 and n3 have no warning type that n0 lacks.
  - "threaded recording ON" appears in n2 and n3; "Native draw batches: parallel workers=2" in n2 only.
  - n3 logs the placement warning pair 8× instead of 4× (the shared counter, §1).

### 3. `Presenter::RefreshGuestOutput` on GPU Commands (devoff only)

**Correction to Task #13 ("Devoff S4 leads"):** it is not a guest-output copy/convert. Almost all of it is the swap's `EndSubmission(true)`, which replays and submits the whole frame's D3D12 commands.

**What runs per frame.** SDK `src/graphics/d3d12/command_processor.cpp`, unchanged since 11-21 11:06:
1. **IssueSwap.** The guest's swap packet reaches `D3D12CommandProcessor::IssueSwap` (:2184) on GPU Commands. It calls `presenter->RefreshGuestOutput(…)` with a refresher lambda. The presenter (`src/ui/presenter.cpp` 559–640) picks a free guest-output image from its mailbox and runs the lambda on the same thread.
2. **The lambda** records the display-gamma compute pass into the deferred list (:2441–2466): the ramp upload if the ramp changed, one-use SRV/UAV descriptors, root signature, constants, pipeline, barriers, and one `Dispatch` of 16×8-pixel groups. FXAA is off here (`swap_post_effect='none'`). It ends with `SubmitBarriers()` and `EndSubmission(true)` (:2546–2547).
3. **`EndSubmission(true)`** (:4199–4322) closes the frame and the submission:
   - `texture_cache_->EndFrame()` and `primitive_processor_->EndFrame()` (:4221–4225);
   - ends an open occlusion query (:4230–4234);
   - `pipeline_cache_->EndSubmission()`, which waits for async pipeline creation, then `SubmitBarriers()` (:4236–4240);
   - allocator `Reset`, list `Reset`, then **`deferred_command_list_.Execute()`** (:4251–4253). Execute replays every D3D12 call recorded since the submission opened into the real `ID3D12GraphicsCommandList`: draws, root parameters, descriptor tables, barriers, copies, and resolve and EDRAM dispatches. The NVIDIA UMD encodes the frame here;
   - `Close`, `ExecuteCommandLists`, allocator bookkeeping and `Signal(submission_fence_)` (:4254–4270);
   - frame bookkeeping (`closed_frame_submissions_`, :4279–4285) and the rare cache clear (:4287).
4. **Publish.** The presenter publishes the image to the mailbox. The UI thread then paints it (`present_effect='fsr'`) and presents. That cost lands on the UI thread, not on GPU Commands.

**Profile.** a-prof / b-prof, slow state, never timing; folded stacks in `build/agent7/prof/{a,b}-gpucmd.folded`.

| under `RefreshGuestOutput` | a-prof ms/f | b-prof ms/f |
|---|---|---|
| total (samples) | 2.09 (27) | 2.20 (28) |
| in `EndSubmission(true)` (rexgpu-xenos `fn_B78B0`) | 26 of 27 samples | 27 of 28 |
| ├ `deferred_command_list_.Execute` (`fn_FC120`) | 1.006 | 1.177 |
| │ └ NVIDIA UMD / D3D12Core | 0.696 / ~0.30 | 0.706 / ~0.47 |
| ├ `Close` + `ExecuteCommandLists` (D3D12Core `fn_3F890`) | 0.542 | 0.549 |
| └ other D3D12Core calls (`fn_14450`, `fn_20605C`, `fn_209DC0`) | ~0.15 each | ~0.15 each |
| gamma-pass recording; presenter mailbox CAS | ≤1 sample each | ≤1 sample each |
| leaf DLLs | nvwgf2umx 1.316, win32u 0.387, D3D12Core 0.155 | nvwgf2umx 1.491, ntdll 0.314, D3D12Core 0.235 |

- **Size:** 27–28 samples, so 2se ≈ ±1.15 ms/f. That is ~25% of GPU Commands' busy time (8.44 / 9.42 ms/f).
- **The whole frame is one submission.** At most 1 `EndSubmission` sample falls outside `RefreshGuestOutput`.
  - `d3d12_submit_on_primary_buffer_end` (default true, :98; not set in the toml) ends a submission only at the end of an `ExecutePrimaryBuffer` call (`OnPrimaryBufferEnd`, :2556–2561), and only if no pipelines are being created (`CanEndSubmissionImmediately`, :4324).
  - The other `EndSubmission(false)` sites don't show either: the on-demand memexport publish (:3180), `CheckSubmissionFence` (:3926) and the occlusion-query paths (:5715, :5771).
  - So the frame most likely reaches GPU Commands as one primary-buffer chunk that ends with the swap. It is recorded, then replayed and submitted in one go at the swap, and the GPU waits for all of it.
- **Timing estimate: ≈1.3 ms/f** for `RefreshGuestOutput`, scaling by 5.34 / 8.44. This is an estimate: driver time may not scale like the rest.
  - Window 3's d0 (devoff, 163 fps) has GPU Commands at 5.34 ms/f and 87% busy: it is the critical thread.
  - Main is at 2.97 ms/f (48%). Render is at 4.69 ms/f (76%), mostly spinning for ring-buffer space.
  - util_gpu's median is 54–57%, so the GPU has headroom.
- **The rest of GPU Commands, for context:**
  - memcpy (VCRUNTIME140, both copies) is 3.17 / 2.98 ms/f, most likely shared-memory uploads.
  - The ntdll leaves are write-tracking (`PhysicalHeap::Protect` → `VirtualProtect`) and lock contention (`_Mtx_unlock` → `NtSetInformationThread`).

### 4. S4 proposals for `RefreshGuestOutput` (devoff path)

These are SDK files, so proposals only. They are ranked by expected ms/f on GPU Commands in timing. Each sits behind a default-OFF cvar, read once at startup.

**R1. Async chunked submit.** Expected **≈ −0.7 to −1.0 ms/f** on GPU Commands.
- **Where the gain comes from:** the replay and submit of every chunk but the last moves to a worker. That is (K−1)/K × 1.3 ms/f for K equal chunks. It is more if the split is placed so that the worker finishes before the swap; then K = 2–4 is enough.
- **fps:** if GPU Commands stays critical at ~87% busy, this is worth up to ~+20% fps (the GPU is ~55% busy, Main is at 2.97 ms/f). Unverified.
- **Stage 1, split points** (cvar `d3d12_submit_split_kb`, 0 = off). When the open submission's deferred list passes N KB, end it with the existing `EndSubmission(false)` path. Split only:
  - after a whole draw, dispatch or resolve;
  - if `CanEndSubmissionImmediately()` holds (no async pipelines pending, :4324);
  - if no occlusion query is active (`EndSubmission` would end it early, :4230);
  - if the scratch buffer is free (asserted at :4228).

  Alone, stage 1 adds one submission per split on GPU Commands. Close + `ExecuteCommandLists` costs 0.54 ms/f for one per frame (slow state), and its fixed part is unknown. So stage 1 is a test bed for the split rules (K = 2), not a win by itself. The GPU does start each frame earlier.
- **Stage 2, submit worker** (cvar `d3d12_async_submit`).
  - At a split, GPU Commands swaps the deferred list for a pooled one, takes the next allocator, assigns the fence value (`submission_current_++`) and queues the chunk with release ordering.
  - The worker does allocator/list `Reset`, `Execute`, `Close`, `ExecuteCommandLists` and `Signal`.
  - The swap's `EndSubmission(true)` and every existing `EndSubmission(false)` caller drain the queue first, then submit synchronously. So the presenter and the readback paths are untouched.
- **Why the output is identical:**
  - **Existing path.** A split reuses `EndSubmission(false)`/`BeginSubmission`, which already run mid-frame today: primary-buffer end :2559, memexport publish :3180, fence wait :3926, occlusion paths :5715/:5771. `BeginSubmission` re-establishes every cached binding (:4122–4154). Frame accounting doesn't change, because `EndSubmission(false)` never closes the frame (:4219).
  - **Barriers.** `ExecuteCommandLists` boundaries only add full UAV and aliasing barriers (:4245–4248). That changes timing, not results.
  - **Unsafe states are avoided.** Splits skip the three states where ending a submission would change behaviour: pending pipelines, an active occlusion query, the scratch buffer in use.
  - **Queue order.** Chunks are submitted in FIFO order, and every other direct-queue user drains the FIFO first: the swap, `CheckSubmissionFence` waits, `AwaitAllQueueOperationsCompletion`, `UpdateTileMappings`, device removal and shutdown.
  - **Lifetimes.** Fence values are still assigned on GPU Commands, and every tracker is keyed by submission number (allocators, upload and readback pools, texture/RT caches). So nothing a queued chunk references is retired before its `Signal`.
  - **OFF.** With the cvars off, today's code runs unchanged.
- **Files:**
  - SDK `src/graphics/d3d12/command_processor.cpp`: cvars near :98, the split check, the worker, the drains;
  - `include/rex/graphics/d3d12/command_processor.h`: members;
  - `include/rex/graphics/d3d12/deferred_command_list.h`: a `Swap()` of `command_stream_` (:646). `deferred_command_list_` keeps its name, so no recording call site changes.
- **Risk:** stage 1 low–medium. Stage 2 medium–high:
  - threads around the queue and the allocator lists;
  - device removal and shutdown;
  - `Execute` resolves pipeline handles through the processor (`GetD3D12PipelineByHandle`, deferred_command_list.cpp:241). That is safe off-thread only because splits wait until no pipelines are pending.
- **Test plan:**
  1. A build with both cvars OFF matches today's output and log.
  2. Per stage, a functional ON/OFF pair in Agent 8's slot: frame comparison of the title loop and one gameplay scene (Agent 3's harness or screenshots), a game.log diff, and a submissions-per-frame count.
  3. ON with the D3D12 debug layer: no new messages.
  4. Stage 2 soak: 10 min with resize, alt-tab, occlusion-query scenes and memexport readback (`d3d12_readback_memexport=true`).
  5. Window-4 timing A/B, ≥3 runs per arm: GPU Commands ms/f, worker ms/f, fps, p99.

**R2. Redundant-command filter in `DeferredCommandList`.** Expected **−0.1 to −0.2 ms/f at most**. All of `Execute` is ~0.64–0.74 ms/f in timing, and the processor already caches most state.
- **Step 1:** per-type command counters in `Execute`, compiled out by default. They show whether repeated root parameters, descriptor tables, `SetDescriptorHeaps` or single-barrier `ResourceBarrier` calls are worth filtering. Step 2 comes only after that.
- **Step 2** (cvar `d3d12_filter_redundant_commands`): drop a command that sets exactly the state already set in the same list. The filter resets on `Reset`, on `SetDescriptorHeaps` and on root-signature changes.
- **Why the output is identical:** setting a D3D12 state to its current value is a no-op.
- **Files:** `deferred_command_list.{h,cpp}`.
- **Risk:** low–medium. A wrong reset rule would drop a needed bind; the debug layer and a frame comparison would catch it.
- **Test plan:** a counters run (functional), then R1's steps 2, 3 and 5.

**Rejected:**
- **Skip the gamma pass for an identity ramp.** The title ramp isn't identity (`identity=false`), and recording the pass costs ≤1 sample.
- **Cache the per-frame UAV/SRV descriptors.** That saves microseconds.
- **Record straight into the real command list.** The UMD work just moves into recording, and it breaks async pipeline creation, which is why the list is deferred (:4125–4127).
- **Make the swap chunk async too** (R1 plus a publish from the worker). It would save another ~0.2–0.3 ms/f, but it changes the presenter's contract: presenter.cpp publishes when the refresher returns. Not for S4.

**Next step, no code:** name D3D12Core's `fn_14450`/`fn_20605C`/`fn_209DC0` (~0.45 ms/f in the slow state) with Microsoft's public D3D12Core symbols before proposing anything there. nvwgf2umx has no public symbols.

### 5. Agent 10's safety review of the Task #13 candidates

- **1a, the AOT pack fix:** not output-identical, because it brings back the dropped draws. It needs a frame comparison as well as the timing A/B.
- **1b, the miss cache (`LEGO_NATIVE_SHADER_MISS_CACHE`):** only under conditions:
  - the pack generation in the key;
  - a stamp over the full span;
  - `readable_size`;
  - no per-frame fallback;
  - replay of the warning caps.
- **The Main call-count probe:** compiled out by default.
- **THREADED:** covered by the n2/n3 rows (§2), plus a proof that the unlocked `PlacementShaderUnchanged` at shaders.cpp:622 runs only on the capture worker.
- **All of them** need a window-4 timing A/B.
- **Ownership:** shaders.cpp is not Agent 4's (Agent 4 owns draw.cpp). The miss-cache stopgap is Agent 1's decision.

## Task #13: profile analysis of the slot `-Profile` runs (session 3, 04:40)

Agent 8's runs are in `build/agent8/matrix/20261122-0357/runs`. All three were unfocused on the hidden desktop, uncapped, with a 150 s profile window, and all exited 0.

| run | dir | bin | window fps | sampler rounds | Main / render tid |
|---|---|---|---|---|---|
| a-prof | `0357-a-prof-r1` | devoff2 | 67.7 | 191 (1.3/s) | 39692 / 88804 (F80001A8) |
| b-prof | `0401-b-prof-r1` | devoffB | 67.8 | 188 (1.3/s) | 32908 / 97548 (F80001AC) |
| n-prof | `0405-n-prof-r1` | native2-bin, n0 flags | 70.8 | 255 (1.7/s) | 8908 / 53568 (F8000190) |

- **Bin choice:** native2-bin with the flag (frontend off, uncapped), which is the exact n0 config and the same S2 snapshot as a-prof. I told Agent 8 at 03:09.

> [!WARNING]
> These are profile numbers, never timing.
> - The sampler ran at 1–2 rounds/s against a nominal ~1000, because it was CPU-saturated. That gives ~190–255 samples per thread. `~` means |Δ| < 2se.
> - All three runs were in the hidden-desktop slow state (E-cores ~550 MHz).
> - a-prof has the frontend on and n-prof has it off. This is the same confound as d0/n0.
>
> Slow-state factors against n0 timing:
> - render CPU/frame is 2.5× (12.36 vs 4.94 ms/f);
> - `swap_present_cpu_ms` is 2.2× (2.19 vs 1.01; native-frames.csv);
> - Main is only 1.1× (6.04 vs 5.31).
>
> So Main's ms carry over to timing. For render, only the shares carry over.

**Outputs** (all in `build/agent7/prof/`):
- `main-compare.txt`/`.json`: a vs n, Main, `--handoff`.
- `an-all.txt`/`.json`: a vs n, all threads, top 30.
- `ab-main.txt`, `ab-all.txt`: a vs b.
- Folded stacks `{a,b,n}-main`, `n-render` and `{a,b}-gpucmd` `.folded`.
- Tree diffs: `an-main-tree-top.txt`, `an-main-tree-afab.txt`, `n-render-bindshader.txt`, `ab-gpucmd-tree.txt`, `ab-gpucmd-boundary.txt`.

**New tool:** `bench/agent7/folded_tree_diff.py` diffs two `analyze_profile.py --folded` files as a call tree, with `--root`, `--guest-only` and `--leaves`. Test: `test_folded_tree_diff.py`, **8/8 OK** at 04:39. It covers the row maths and `~`, root and outside counts, row order, `--min`/`--depth`, the guest-only trampoline drop and boundary leaf, and hook names.

### 1. a-prof vs b-prof (devoff2 vs devoffB)

Agent 9 ran the same tool (`build/agent9/prof/ab-*-a9.txt`, notes S3.8). My copies match: all-threads busy 47.205/47.170 ms/f, Main 3.637/3.532, and no role Δ is significant.

The one significant bucket is **write-tracking arm/protect: 1.083 → 2.276 ms/f (+1.19, 2se 1.03; 14 → 30 samples)**.
- `EnablePhysicalMemoryAccessCallbacks` inclusive goes 0.077 → 0.628.
- By thread it is GPU Commands 0.62 → 1.26~ and Main +0.56~.
- It is just above 2se, so it is borderline.

### 2. Main XThread +2.35 ms/frame (n-prof vs a-prof)

Main busy goes **3.637 → 6.040 ms/f (+2.40, 2se 1.57)**, which matches window 3's +2.35. It is guest code. Faults, pool copies and sync are ruled out.

| Main bucket (busy ms/f) | a-prof | n-prof | Δ (2se) |
|---|---|---|---|
| guest code | 2.863 (37) | 5.154 (93) | **+2.290** (1.42) |
| rexlego host (memset/memcpy hooks `sub_83E46040`/`sub_83E45090`, `sub_82A34208`) | 0 | 0.443 (8) | +0.443 (0.31) |
| rexruntime (incl. `UX_INPUT_STATE` H2G ← `sub_82A32128`, 0.22) | 0.077 | 0.222 | +0.144~ |
| write-tracking fault (VEH) | 0.077 (1) | 0 | −0.077~ |
| write-tracking arm/protect | 0.464 (6) | 0.166 (3) | −0.298~ |
| CPU pool copy | 0 | 0 | 0 |
| host sync/spin/yield | 0.155 | 0.055 | −0.099~ |

**Where the guest time grew:** almost all of it (+1.99 of +2.40) is in one subtree. These are guest-only stacks, from `an-main-tree-afab.txt`:

| inclusive path | a ms/f (n) | n ms/f (n) | Δ (2se) |
|---|---|---|---|
| `sub_82FEB7B8` (main loop body) | 3.482 (45) | 5.985 (108) | +2.50 (1.55) |
| ├ `sub_82AFAB68` → `sub_82AF9BC0` | 1.006 (13) | 2.992 (54) | **+1.99** (0.99) |
| │ └ `sub_82FCC500` → `sub_82FCB308` → `sub_82F050B0` | 0.696 (9) | 2.272 (41) | +1.58 (0.85) |
| │  └ `sub_82EF8C18` → `sub_82F0CCD8` (recursive) | 0.619 (8) | 2.161 (39) | +1.54 (0.82) |
| │   └ `sub_82EFE948` → `sub_82EF3B38` → `sub_82EF3180` | 0.387 (5) | 1.441 (26) | +1.05 (0.66) |
| │    └ `sub_82EF2FE0` → `sub_82EF2E28` → `sub_82EF2368` | 0.155 (2) | 0.665 (12) | +0.51 (0.44) |
| ├ `sub_82AB2040` | 1.935 (25) | 2.217 (40) | +0.28~ |
| ├ `sub_82FE9068` | 0.232 (3) | 0.554 (10) | +0.32~ |
| └ `sub_82A45F48` → `sub_82A32128` → `UX_INPUT_STATE` | 0 | 0.222 (4) | +0.22 |

- **The growth is broad.** Under `sub_82AFAB68`, n-prof has ~45 distinct leaves. The largest are:
  - the graphics-layer functions `sub_82B61580` (5), `sub_82B62C1C` (3), `sub_82B62528` (3) and `sub_82B53308` (2);
  - the memset hook (3);
  - everything else has 1 sample each.
  
  So there is no spin loop and no single hot leaf. It looks like the recursive scene/render-list walk does more work per frame, or the same work more slowly. The rest of Main grew only ×1.16.
- **The subtree is state-dependent even within devoff.** a vs b gives 1.006 (13) vs 0.314 (4) ms/f. n-prof's 2.99 is well outside that range, and window 3 shows the +2.35 in every n0 run.
- **No OFF-switch fix for Main:** there is no host hot spot to remove.
  - Next step: a functional per-frame call count of `sub_82F0CCD8`/`sub_82EF3180` (and the `sub_82B6xxxx` leaves) in devoff2 vs native2. That tells "more nodes per frame" from "same nodes, slower".
  - The frontend confound (on in a-prof, off in n-prof) also needs ruling out.

**Handoff (Main vs render), joint state per sampler round, ms/f:**

| state | a obs | a indep | n obs | n indep |
|---|---|---|---|---|
| main busy / render busy | 3.482 | 3.409 | 4.987 | 5.282 |
| main busy / render wait | 0.155 | 0.229 | **1.053** | 0.758 |
| main wait / render busy | 10.370 | 10.443 | 7.370 | 7.075 |
| main wait / render wait | 0.774 | 0.700 | 0.720 | 1.015 |

The conditional probabilities:

| | a-prof | n-prof |
|---|---|---|
| P(main busy) | 24.6% | 42.7% |
| P(render busy) | 93.7% | 87.5% |
| P(render wait \| main busy) | 4.3% | 17.4% |
| P(main wait \| render busy) | 74.9% | 59.6% |

- **a-prof is render-bound.** Main waits 10.37 ms/f in a guest critical section (`UX_RTL_CRITICAL_SECTION` ← `sub_82A2A260`). Meanwhile render spins in the ring-buffer wait (`sub_83FAF180`, 5.96 ms/f; Agent 9's S3.8).
- **n-prof: render is still the busier thread in the slow state, but it now idles on Main some of the time.**
  - Render waits 1.05 ms/f (19 rounds) at the `sub_83FA6020` kernel wait. Meanwhile Main runs guest code (+0.84 ms/f of critical-path Main work, in graphics-layer leaves).
  - While Main waits (7.37 ms/f), render runs SwapHook 2.44, BindShader 2.00 and DrawVertices 1.61 ms/f.

### 3. Render thread (n-prof): the BindShader miss path is 49% of its CPU

Render (XThreadD140) is busy 12.36 ms/f. `n-render-bindshader.txt` breaks down the BindShader part:

| frame (inclusive) | ms/f (n) |
|---|---|
| `BindShader` ← guest `sub_82B79FB8` (SetShader hook, hooks_shader.cpp:35–50) | **6.10** (110 of 223) |
| └ `AdoptShader` | 5.99 (108) |
|  ├ `FindShaderByMicrocode` (self 1.66; `unordered_map<u32,u64>` 1.16 incl. `operator new` 0.33; XXH3 0.22) | 3.10 (56) |
|  └ `ReadableGuestSpan` → `BaseHeap::QueryRegionInfo` | 2.88 (52) |

**Cause: two placement shaders are missing from the AOT index in every native2 run.**
- VS `0xAC449538` (microcode at `0xED23D3E0`);
- PS `0xAC448F28` (microcode at `0xED23D540`).

The game.log of n-prof and of all five window-3 n0 runs hits the warning caps for both shaders: 4× "placement … missing from AOT index" and 8× "unrecognized … shader resource". So the real count is higher.

**Why a miss costs so much:** on a miss, `AdoptShader` registers nothing (shaders.cpp:294–308). So every SetVertexShader/SetPixelShader of these two shaders repeats two steps:
- **`ReadableGuestSpan`** (shaders.cpp:111–144) makes two `QueryRegionInfo` calls. Each one scans the page table forward to the end of the containing allocation, under the heap lock.
- **`FindShaderByMicrocode`** (shader_archive.cpp:319–358) walks the 8-byte-prefix bucket (its comment says thousands of sections share a zero prefix). It also builds a fresh hash map per call, runs XXH3 once per distinct size, and calls `FindPrecompiledByMicrocode` under `g_pack_mutex`.

No sample lands in the success path (`FindShaderTextureMask`, `FindShaderPhysicalSize`, `WatchCpuMemory`, registry insert). That pattern means a pure miss.

**Timing estimate (not measured):** about half of n0's 4.94 ms/f render CPU, ≈2–2.5 ms/f.

**The draws that bind these shaders are dropped.** Code read at 04:38; shaders.cpp is unchanged since 11-21 19:58.
- On a miss, `BindShader` (shaders.cpp:558–583) stores the address with a null resource and returns false. It holds `HostDevice::LockRecording()` for the whole lookup.
- `BoundShaderAddress` (:682–694) then reports `binding_failed`, and the draw returns early at draw.cpp:2712–2725 (probe events `draw_missing_vertex_shader`/`draw_missing_pixel_shader`). draw.cpp last changed at 03:34, so these lines may move.
- So native draws less than devoff in this scene. That slightly flatters native in d0/n0-style comparisons. Fixing the archive brings the draws back, along with some of their render cost.
- The PS backing starts with zero words (`prefix=0xC77B3ABB6F87ACD9`, the XXH3 of 8 zero bytes). So each PS miss walks the large zero-prefix bucket, which fits FindShaderByMicrocode's self 1.66 + hash map 1.16 ms/f.

### 4. Top 3 S4 candidates for the native path

1. **Shader miss path on the render thread.**
   - **Expected gain:** ≈2–2.5 ms/f of render CPU (49% of render busy in n-prof).
   - **Effect on fps:** in n0, Main is 76% busy and render 71% at 143 fps. Cutting render removes most of Main's waits, up to ~+15–25% fps until Main's 5.31 ms/f binds. Either way it frees most of a core.
   - **Real fix (no switch needed):** in one functional run, capture the two shaders with `LEGO_DUMP_MISSING_SHADERS=<dump dir>` (`CaptureMissingPlacementShader`, shaders.cpp:146–207, called on every miss at :295). *Corrected 05:33: this said `=1` and named Agent 4 as the owner. The value is the dump root, and shaders.cpp isn't Agent 4's. The capture is done (Task #22 §1).* Then add them to the AOT pack. This also restores the dropped draws, so the net render gain is a little below the miss cost.
   - **Stopgap behind an OFF switch** (proposed, not applied; shaders.cpp is not mine): `LEGO_NATIVE_SHADER_MISS_CACHE=1`, read once, default off. The output stays identical to today's native (the draws stay dropped), so ON vs OFF is a clean timing A/B of the miss cost.
     - In `AdoptShader`, after reading `container_address` (:282) and before `ReadableGuestSpan` (:288), return `nullptr` if (stage, guest_address, container_address) is a cached miss whose CPU-memory stamp is unchanged. The stamp covers the first 64 KiB of the microcode, the max physical size (cf. :178).
     - If no stamp is available, retry once per `g_probe_frame`. That is the policy `RefreshBoundShaderResources` already applies to unavailable bindings (:597–604).
     - Record misses at :294. The log and probe caps are unchanged.
     - A guest write to the microcode re-arms the lookup.
2. **Main's guest work (+2.0 ms/f in the `sub_82AFAB68` scene walk).**
   - **Expected gain:** up to 2.35 ms/f on Main, the busier thread in timing (5.31 vs 4.94 ms/f). That is ≤ ~+30% fps, and only together with #1.
   - **Evidence and next step:** see §2. There is no host fix yet. First run the per-frame call-count probe, and rule out the frontend confound.
3. **Present and draw recording on the guest render thread.**
   - **Cost now:** SwapHook → `HostDevice::PresentTexture` takes 3.27–3.55 ms/f in the slow state (1.01 ms/f `swap_present_cpu_ms` in n0). The DrawVertices hook takes 2.88 ms/f in the slow state.
   - **Expected gain:** ≈1–1.5 ms/f off the render thread in timing.
   - **Switch:** the existing `LEGO_NATIVE_THREADED=1` (native_worker.cpp:319–327) moves recording to a worker. It is worth one functional run in Agent 8's slot before 08:30, to see that it boots and what the render thread keeps.

**Devoff S4 leads (GPU Commands; Agent 1's ask at ~04:23).** GPU Commands is busy 8.44/9.42 ms/f (a/b, slow state, 57% busy) and blocked for the rest. Render spends ~94% of its time in the ring-buffer wait spin, so the devoff title is bound by GPU Commands throughput. From `ab-gpucmd-boundary.txt`:
- `memcpy` (VCRUNTIME140 `fn_11200`) called straight from rexgpu-xenos: 2.01/2.75 ms/f. This is most likely the shared-memory upload of CPU-written pages. rexgpu-xenos has no symbols in the profile, so naming the caller needs its PDB.
- `Presenter::RefreshGuestOutput`: 2.09/2.20 ms/f, of which the NVIDIA UMD is 1.32/1.49. *Corrected 05:33:* it is not a copy/convert. It is the swap's `EndSubmission(true)`: the replay and submission of the whole frame's deferred command list, on the GPU Commands thread (Task #22 §3).
- A second VCRUNTIME copy (`fn_10E40`): 1.08/0.16.
- Write-tracking re-arm (`EnableAccessCallbacks`, plus `EnablePhysicalMemoryAccessCallbacks` in B): 0.62/1.26. This is the borderline bucket from §1.

## native3 boot check (session 3, 03:00)

**Run:** `build/agent8/runs/0256-native3` (Agent 8, start 02:56:49, 120 s watch, exit 0).
- **Bin:** `build/agent2/native3-bin`: exe 7F7F8586D219465C, rexruntime D1D66AC3716835AC, fingerprint 8f849b69907d4006.
- **MANIFEST fix-(a) rows:** settings_registry.cpp A3733700… → 4EC71328…, settings_preferences.cpp C78112AA… → 9CBE6DBF….
- **Args:** `--native_settings_load=false --discord_rpc=false --audio_mute=true --pause_when_unfocused=false` (no `--native_settings_frontend=false`).
- **Env:** `LEGO_NATIVE_FRAME_METRICS`.

**`native3_boot_check.py` vs `0030-n0-r1`: A=PASS B=PASS C=PASS D=PASS (2 WARN) → PASS.** Output: `build/agent7/native3-check-0256.txt`.

| Group | Evidence |
|---|---|
| A (frontend on) | From toml :72, no override. "Native settings graph bound: generation=1" at L410; frontend transitions at L400 and L470-471 (current=7 at 02:57:35). |
| B (no throw) | 482 log lines, no throw/fatal lines. First present at L128, after 'Native write tracking' at L44 (the S2 throw point). Exit 0, no WER files or dumps. 13642 native rows. |
| C (bilinear) | spatial_fsr_presented = 0 and fsr_enabled = 0 on every row. 1920x1080 scene → 2240x1294 output. The toml's `present_effect='fsr'` is rejected by the non-FFX SDK, so the present is bilinear. |
| D (identity) | exe, rexruntime and fingerprint match. perf.csv 13643 = native 13642 + 1. Frame column 2..13643, 0 gaps. MX570, vsync off, threaded recording off, max frame latency 1 (waitable). |

**The 2 WARNs are config, not code:**
- `native_fps_limit_cvar=240` (n0 sets 0 via `--native_fps_limit=0`);
- no 'presentation cap override' line (n0 logs it at L134).

The boot also differs from n0 in two other ways:
- it has no `--framerate_limit=0` (the toml says 60);
- its window was unfocused (focus=false; n0 had focus=true).

**Frames, last 50 s (rows 8426-13478):** 101.05 fps; mean 9.90 ms, p50 8.92, p99 34.2; 60 frames > 33 ms. swap_present_cpu_ms 1.55 (n0: 1.02); 8 draws/frame.
- **This is not a timing result.** It was a functional run, with different caps, focus and frontend. n0's 143.4 fps comes from a runner window.
- A timed native3 run needs n0's args without `--native_settings_frontend=false`, and a focused window.

## Window 3 native summary (session 3, 02:40)

The run dirs are in `build/agent8/matrix/20261122-0013/runs/` (window 3, 00:13-01:16).
- **n0** is native2-bin (fingerprint b7cc74f980e016c3) run with `--native_settings_frontend=false --native_fps_limit=0 --framerate_limit=0`. Its frames come from native-frames.csv.
- **d0, base and d11** are the PM4 builds, with frames from perf.csv.

### Frame times
Command: `native_frames_summary.py --seconds 50 --runner-window`. This scores the runner's window from frames.json and reproduces frames.json exactly: `first_row` is a 0-based data-row index.

| run | fps | mean ms | sd | p50 | p99 | p99.9 | >33 ms | cores |
|---|---|---|---|---|---|---|---|---|
| 0030-n0-r1 | 143.38 | 6.974 | 1.397 | 6.691 | 11.372 | 14.113 | 0 | 2.44 |
| 0042-n0-r2 | 136.68 | 7.316 | 1.656 | 6.873 | 12.591 | 14.966 | 0 | 2.55 |
| 0054-n0-r3 | 146.58 | 6.822 | 1.310 | 6.554 | 10.968 | 13.808 | 0 | 2.38 |
| 0104-n0-r4 | 143.05 | 6.990 | 1.350 | 6.722 | 11.289 | 14.149 | 0 | 2.42 |
| median | 143.22 | | 1.374 | | 11.331 | 14.131 | | 2.43 |

- The table shows the perf.csv numbers over the same frames, shifted one row. native-frames.csv agrees to within 0.015 ms at p99.
- My session-start run used the tail window instead (the last 50 s before a 2 s skip). It gave 138.5-147.7 fps (median 144.05), and 161.8 fps for 0016-cold-n0.
- **Row check:**
  - perf.csv rows = native-frames.csv rows + 1 in every run. perf.csv has a leading 0 row, so perf row k+1 = native row k.
  - The native frame column is contiguous (frame 2..N, 0 gaps), so each native row is one present.
  - `spatial_fsr_presented` and `fsr_enabled` are 0 on every row.
- **Present config:**
  - Last row: vsync 0, fps cap 0, output 2240x1294, refresh 60, scene and present source 1920x1080, no FSR.
  - Window means: `swap_present_cpu_ms` 1.01-1.04 and `draw_calls` 8 per frame in the title loop.
  - `frame_slot_wait`, `acquire`, `present_submit` and `sync` read 0 because detailed timing is off.
- **game.log**, at init:
  - `swap chain ready (vsync off)`
  - `Native GPU [b7cc74f980e016c3]: D3D12 ready on 'NVIDIA GeForce MX570' (2240x1294, 3 images)`
  - `threaded recording off`

  Then on the render thread:
  - `display gamma updated from title ramp … identity=false`
  - `presented internal texture 1920x1080 (before swap-chain copy)`
  - `presentation cap override=-1`
  - `swap-chain max frame latency=1 query=00000000 waitable=true latency_wait=0 set=00000001`
  - `present override sync=-1 flags=0`

  There are no FSR 1 warnings: `present_effect` resolved to bilinear, because the non-FFX SDK rejects the toml's 'fsr'.
- **Pacing:** the title loop runs at ~143 fps, well above 60. So d0/d1/d2 keep `LEGO_NATIVE_FPS_LIMIT=60`, and the limiter has slack to sleep. `=30` is not needed ("Pacing in native mode" below).

### CPU per frame by thread role
Command: `w3_thread_per_frame.py --runs build\agent8\matrix\20261122-0013\runs`. Output: `build/agent7/w3_thread_per_frame.txt`.
- ms/frame = busy_pct × 10 / fps.
- busy_pct is from Agent 8's thread-cpu driver (threads.csv). fps here covers the whole measure window (`rows_by_end_bytes / end_bytes_window_s`), which the driver window covers to within 1-3 s.
- Values are medians of 4 runs, in ms per frame.

| arm | fps | Main | render | GPU Cmds | TimerQueue | worker2 | VSync | audio | other XThreads | other | total | Main % | render % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 163.07 | 2.965 | 4.688 | 5.338 | 3.824 | 1.493 | 0.411 | 0.365 | 0.912 | 1.328 | 21.332 | 48.3 | 76.1 |
| base | 161.97 | 2.954 | 4.672 | 5.372 | 3.822 | 1.548 | 0.407 | 0.356 | 0.937 | 1.339 | 21.428 | 48.4 | 76.5 |
| d11 | 159.59 | 3.080 | 4.885 | 5.398 | 3.868 | 1.588 | 0.370 | 0.345 | 1.121 | 1.357 | 22.088 | 48.9 | 77.5 |
| n0 | 143.03 | 5.313 | 4.940 | 0 | 3.636 | 1.241 | 0 | 0.207 | 0.585 | 1.059 | 17.049 | 75.9 | 70.8 |
| n0 − d0 | −20.04 | +2.348 | +0.252 | −5.338 | −0.188 | −0.252 | −0.411 | −0.158 | −0.327 | −0.269 | −4.283 | | |

- The render thread is the busiest XThread other than Main: F80001A8/AC/B0 in the PM4 builds, F8000190/8C in native. 0025-d11-r1 ran in a light state (297 fps); the medians absorb it.
- **Refining Agent 1's lead** ("native2 renders 12% fewer frames at 30% less CPU, CPU-bound on Main XThread"):
  - **Where the time moves:** native removes the GPU Commands thread's 5.3 ms/frame, and VSync's 0.4. But Main XThread does +2.35 ms/frame more (2.97 → 5.31, i.e. 48% → 76% busy), and the render thread +0.25 (4.69 → 4.94, 71% busy).
  - **Totals:** CPU per frame drops 4.3 ms (−20%), and process cores drop from 3.55 to 2.43 (−31%, Agent 8's arm means).
  - **Which thread does what:** in native, the draws and presents run on the guest render thread, not on Main XThread. The render thread's TID logs the clears, shaders, gamma, presents and latency lines; Main XThread logs surface creation, sampler defaults, CPU pool copies and Toypad.
  - **The bottleneck:** neither thread is saturated (Main 76%, render 71%). Main + render = 10.3 ms/frame against a 7.0 ms frame, so they partly overlap. The frame is likely bound by the main ↔ render handoff, with Main the longer leg.
  - **What a fix could gain:** cutting Main's extra time should raise fps until the render thread (4.9 ms, ≈ 200 fps) or the handoff becomes the limit.
- **Suggested next look (not started by me):** a CPU profile of Main XThread on native2 against d0 in the title loop. It needs a game run, so it goes through Agent 8's slot.
  - Candidates for the +2.35 ms: write-tracking faults (`Native write tracking`), CPU pool copies and uploads, and guest spin or sync waits that the PM4 path hid in GPU Commands.
  - Owners to coordinate with: Agent 4 (draw path, N1-N3), Agent 5 (uploads), Agent 11 (TimerQueue at 52-62% of a core) and Agent 12.

### native3 check (step 2): ready
`bench/agent7/native3_boot_check.py <run dir> [--bin-dir] [--ref] [--min-frames 600]` prints PASS/FAIL/WARN/INFO lines and a verdict per group. Exit codes: 0 = no FAIL, 1 = any FAIL, 2 = usage error.
- **A. Frontend on:** the effective `native_settings_frontend` must be true. Precedence: a run.json arg > the run-dir toml > run.json toml_set > the default (false).
- **B. No throw:**
  - none of the 7 throw/fatal patterns in game.log;
  - a present line after `Native write tracking`, the S2 throw point;
  - run.json OK: status, exited_early, werfault_seen, exit code;
  - no `*.dmp` or `wer-*` files;
  - at least 600 native rows.
- **C. Bilinear present:**
  - `spatial_fsr_presented` = 0 and `fsr_enabled` = 0 on every row;
  - no `Native FSR 1:` warnings.

  INFO lines: rexruntime.dll is a non-FFX SDK, and the present size.
- **D. Info:**
  - MANIFEST lists fix (a) (settings_registry.cpp → 4EC71328 or 8BA19C5F; settings_preferences.cpp → 9CBE6DBF);
  - the fingerprint matches game.log;
  - run-dir binaries match `--bin-dir`;
  - perf = native + 1, with no frame gaps;
  - the present-path log lines;
  - interval_ms over the runner window;
  - with `--ref`: the last-row config, log lines and fps against native2.
- **Test:** `test_native3_boot_check.py`, 7/7 OK. Outputs are in `build/agent7/native3-check-test/<case>.txt`.

  | case | input | verdict | exit |
  |---|---|---|---|
  | real-n0 | n0-r1 | A FAIL (CLI false), B/C PASS | 1 |
  | real-2315 | 2315-native | A PASS (toml line 72), B FAIL (the throw, exit 0xC0000374, WER, dumps, no frames), C FAIL (no rows) | 1 |
  | pos | n0-r1 with the flag removed | A/B/C/D PASS | 0 |
  | fsr1 | pos + FSR 1 rows and warning | C FAIL | 1 |
  | crash | pos + 2315 crash lines and a dump | B FAIL | 1 |
  | cli-true | toml false, CLI true | A PASS | 0 |
  | cli-false | CLI false | A FAIL | 1 |
- **What the native3 boot needs from Agent 8:**
  - no `--native_settings_frontend=false` (drop it from the arm's cvar list);
  - `LEGO_NATIVE_FRAME_METRICS` set;
  - at least 600 frames;
  - and it must be functional only, through Agent 8's slot.

## Native first boot crash (native-bin, `build/agent8/runs/2315-native`, 23:16)
- **What happened:** Agent 8's first boot of `build/agent2/native-bin` (a functional run on the hidden desktop) finished native GPU init: `Native GPU [befeb1184e6c7abc]: D3D12 ready on 'NVIDIA GeForce MX570' (2240x1294, 3 images)`, swap chain `vsync off`, 3 command slots, threaded recording off. Right after `Native write tracking: …` (23:16:08.262), the main thread (t86424) hit an unhandled C++ exception 0xE06D7363 with no guest context. The crash handling then hit 0xC0000374 (heap corruption), and the process exited at 74 s. There were no frames, perf.csv is empty, and there is no native-frames.csv.
- **The exception:** decoded from the full dump `legodimensions.exe.93080.dmp`, using my scratch script `mdmp_cxx.py` (exception record, MSVC throw info, stack scan symbolised with the exe's .map) and a string scan of the dump. It is `std::runtime_error("Native setting is not registered: present_fsr_sharpness_reduction")`.
  - **Stack:** `ReadRegistryValues` (settings_registry.cpp:104) ← the `MakeNativeRegistryBackend` read lambda ← the `CaptureBackend` lambda (gpu_native) ← the `SettingsRevisionCoordinator::State` constructor (settings_revision.cpp:25, `registry.read()`) ← the `NativeSettingsRuntime` constructor ← `OnPreLaunchModule` (legodimensions_app.h:155-157), just after `HostDevice::Create` returned true.
- **Cause:** every SDK build in this workspace has `REXGLUE_ENABLE_FIDELITYFX=OFF` in its CMakeCache: build/dev, build/sdk, build/sdk-dev and build/agent2/snap1-sdk.
  - So rexui doesn't get `REX_HAS_FIDELITYFX_SDK` (ui/CMakeLists.txt:122-127), and presenter.cpp:43-78 registers only a bilinear-only `present_effect`. `present_fsr_sharpness_reduction` and `present_fsr_max_upsampling_passes` are never registered.
  - **String check:** rexruntime.dll in native-bin, devoff1-bin and devoff2-bin has `present_effect` but neither of those two names.
  - The native settings catalog (settings_registry.cpp:27-45) needs both of them, so `ReadRegistryValues` throws on the first one.
  - **Trigger:** the runner's toml, a copy of the owner's `game/legodimensions.toml`, sets `native_settings_frontend = true` (line 72). The cvar defaults to false (settings_native_hooks.cpp:16), and only when it is true does the game build NativeSettingsRuntime.
  - The same toml also sets `present_effect = 'fsr'`, `present_fsr_max_upsampling_passes = 1`, `present_fsr_quality_mode = 'quality'` and `present_fsr_sharpness_reduction = 0.0` (lines 37-40), with `native_fsr3 = false`. An SDK built with FidelityFX wrote it, so the owner's native config presents with FSR 1 (device.cpp:2048 `fsr1_requested`).
- **native2-bin** (staged 23:22) uses the same rexruntime.dll as devoff2-bin (`1C45C869…`), so it will crash the same way.
- **Unblock options** (for Agents 1, 2 and 8 to decide):
  1. **No rebuild:** run native with `--native_settings_frontend=false`, or set it to false in the run-dir toml. The command line wins over the toml: cvar.cpp:130 skips a config value "already set by a higher-priority source". NativeSettingsRuntime then isn't built, and nothing else reads the registry at boot:
     - the QueuedSettings and `Transaction` constructors only store the backend; the reads are in `Transaction::Open`, `Apply` and so on (settings_transaction.cpp);
     - `LoadNativePreferences` didn't read in this run.

     **Caveat:** `present_effect` stays bilinear, because this SDK can't select 'fsr'. The native present then runs bilinear rather than the owner's FSR 1. My (b) clear skip only applies outside FSR 1, so n0 vs a1 would overstate (b) for FSR 1 users. This needs one functional boot to confirm.
  2. **SDK fix:** reconfigure the SDK with `-DREXGLUE_FIDELITYFX_SOURCE_DIR=<abs>/DimensionsRecomp/rexglue-sdk/thirdparty/FidelityFX-SDK` and keep `REXGLUE_ENABLE_FIDELITYFX=OFF`, so there is no FetchContent and no FFX runtime build.
     - The headers are there: `sdk/include` and `ffx-api/include` exist, at eee08db, which is rexglue_fidelityfx.cmake's GIT_TAG.
     - ui/CMakeLists.txt:122-127 then gives rexui `REX_HAS_FIDELITYFX_SDK=1`. That registers both cvars and allows `present_effect = 'fsr'`, which matches the owner's config.
     - Then rebuild rexui and rexruntime.dll, and swap the DLL into native2-bin. The exe looks these cvars up by name.

     **Caveats:** the compile is untested. The public `rex/ui/presenter.h` has 12 `REX_HAS_FIDELITYFX_SDK` guards, and the define is PRIVATE to rexui. So everything outside rexui compiles against the same headers as in the owner's FidelityFX build:
     - Three guarded members at presenter.h:317 (`cas_additional_sharpness_`, `fsr_max_upsampling_passes_`, `fsr_sharpness_reduction_`) change `Presenter`'s layout only inside rexui.
     - presenter.h is also included outside rexui, through graphics_system.h, command_processor.h, window.h and d3d12_presenter.h (src/graphics/d3d12/command_processor.cpp).
     - The owner's FidelityFX build has the same split and runs, so the split should be harmless. (23:33)

## Pacing in native mode (23:15)
- **The 60 fps cap in matrix 1 doesn't apply to native mode.** Matrix 1 (the PM4 path, base vs devoff1) is held at 60 fps by guest pacing: the SDK's `vsync` cvar is locked false, so the guest vblank is emulated at 60 Hz. The native path paces itself instead:
  - its `LimitFrameRate` uses `native_fps_limit`, which defaults to 240 (device.cpp:75);
  - its VSync reads the host setting (device.cpp:2183-2187).
- **Owner's numbers** (`DimensionsRecomp/tools/gpu-aot/native-performance-vsync-20261010.md`, owner's PC, 1080p):
  - upper hub: ~60 fps with VSync, 100-150 fps without;
  - main menu: 30-40 fps, GPU-bound (`WaitForSubmissionLocked` ~16%).
- **What this means for my arms:**
  - **d0/d1/d2** use `LEGO_NATIVE_FPS_LIMIT=60`. If the title loop runs below 60 fps here (MX570 at 2240x1294), the limiter never sleeps and d1 vs d0 measures nothing. In that case, ask Agent 8 for `LEGO_NATIVE_FPS_LIMIT=30` in tiers 1 and 3.
  - **a1 vs n0 and i1:** if the loop is GPU-bound, these may show real gains.
  - **To check:** `interval_ms` from the first native run that boots.

## Batch 2 listing (task #20)

**Status (21:48): in the live tree since 20:48:28-29; the live checks passed (20:48-20:52, "Live checks" below). Agent 10's #25 review rated (h), (i), (p) and (c') SAFE against snap1, with no action needed (`perf-notes/agent10-batch2-review.md` §1-4).** `bench/agent7/b2_apply_and_verify.ps1` applied the two scripts after checking the batch-1 hashes. Line numbers are for the files after the edits: device.cpp 2629 lines, device.h 200, fps_counter.h 79.

| Item | Files and lines | Default | Toggle (env var, read once) | TUs rebuilt | Evidence |
|---|---|---|---|---|---|
| (h) Inline `CurrentDrawPreparation` (Agent 4's request) | device.h:93-95: a comment, `extern thread_local DrawPreparationContext* t_draw_preparation;` and the inline accessor. The out-of-line definition at S1 device.cpp:756 is deleted. Line 755, the `thread_local` definition, stays: it is outside the anonymous namespace, so it already has external linkage | ON (same behaviour) | none | **18**: every device.h includer in `build/dev` (17 gpu_native TUs plus main.cpp, which only the native ON build compiles) | Agent 4's TLS bench: 92.6 → 55.1 ns per call |
| (p) perf.csv rows | device.cpp:2275-2276 | ON | none; a no-op without `--perf_log_csv` | 1 (device.cpp) | The same 2 lines as the approved batch-1 S1 patch. Agent 1 checked the order against `Profiler::Flip`; Agent 10's #21 rated it SAFE |
| (c') Comment on the window queries | device.cpp:1901-1904 | n/a | n/a | 1 (device.cpp) | Comment only (Agent 10's suggestion): the reads before g_mutex rely on g_state and its swap chain being replaced only under the full recording gate (Create, Shutdown) |
| (i) The FPS meter clears touching cells as one rect | fps_counter.h:52-78 (`MergeTouchingRects`); device.cpp:2129-2137 | ON (output-identical) | `LEGO_NATIVE_FPS_CELL_RECTS=1` keeps one clear per cell (the batch-1 path) | 1 (device.cpp; nothing else in src includes fps_counter.h) | `bench/agent7/test_fps_rects.py`, below |

- **TU count:** the four items rebuild 18 TUs in total, device.cpp included. Agent 1 estimated ~21; `bench/agent7/device_h_includers.py` finds 18 in `build/dev/compile_commands.json`, reached directly or through gpu_pass_profile.h and legodimensions_app.h.
- **(h) and the fixtures:** the `CurrentDrawPreparation` mocks (test_binding_caches, test_preparation_metadata, test_texture_depth_upload, test_texture_prepare, test_texture_cpu_authority_gpu.cpp) are standalone programs that don't include device.h. test_query_retirement and test_submission_waits declare their own `t_draw_preparation`. Nothing redefines the accessor, so the batch-1 reason for deferring it was wrong.
- **(i), why:** `native_show_fps` defaults to true (device.cpp:79), so the meter's clears run on every default present. The old code clears every lit 3×3 cell's shadow (black), then every cell (white), one single-rect clear each.
  - `MergeTouchingRects` joins rects that share a whole edge, first along rows, then down columns. Each join replaces two rects with their union, which is itself a rect, so each colour covers the same pixels. The shadows are recomputed from the merged cells with the same (+1, +1) offset. All black clears still come before all white ones.
  - The clears stay single-rect. The multi-rect path (`LEGO_NATIVE_FPS_OVERLAY_BATCHED`, which once crashed nvwgf2umx.dll) is unchanged apart from getting the shorter list.
  - **Test:** `test_fps_rects.py` compiles the digit block from the new device.cpp and from `build/agent7/batch1/device.cpp` against the real fps_counter.h, and paints every clear into a framebuffer. For 640,064 cases (readings 0..10000 × 64 window sizes) the frames are pixel-identical, the toggle path matches batch 1, and every rect is in bounds. 200,000 random bitmaps (half of them shuffled) give identical unions.
  - **Clears per present:** mean 79.7 → 35.1 (−56%). At 60 fps 48 → 20; 120 fps 56 → 20; 144 fps 46 → 18; 240 fps 64 → 26.
- **Runner arm for batch-2 builds (Agent 8):** i1 = `LEGO_NATIVE_FPS_CELL_RECTS=1` (the batch-1 meter) against n0, both with the meter on (the default). Expect n0 ≥ i1; the difference is about 45 single-rect clears per present.

### Checks on the staged copies (20:33-20:38)

| Check | Command | Result |
|---|---|---|
| Syntax, all 18 includers, against the staged headers and device.cpp | `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent7\stage_compile.ps1 <tag> <tu.cpp>...` (puts the stage first with `-iquote`; with `STAGE_EXTRA=-H`, draw.cpp and hooks_device.cpp were seen to open the staged device.h) | All exit 0 with 0 errors. Warnings match `build/agent7/syntax-b2-before/summary.txt`, except device.cpp 27 → 28: the new one is the file's usual `getenv` deprecation warning, for the toggle at 2131. main.cpp reaches device.h through legodimensions_app.h, which resolves the include next to itself, so main.cpp saw the live header; the live run after S1 covers it |
| FPS rects | `. .\env\devshell.ps1 -Quiet; python bench\agent7\test_fps_rects.py --device build\agent7\b2-stage\src\gpu_native\device.cpp --include build\agent7\b2-stage\src --out build\agent7\test-fps-rects-stage` | PASS (see (i)) |
| Fixtures | static check | No fixture extracts or asserts on a changed line. No fixture extracts the FPS block. test_native_overlay (passing) only checks the order copy draw < `RenderNativeOverlays(` < `RenderTextureLayout::PRESENT`, which is unchanged. test_gpu_timestamps extracts from the `gpu_timestamps` guard onwards, after the FPS block. test_fps_counter.cpp and test_native_frame_stats.cpp include fps_counter.h but aren't in `run_tests.ps1` |

### Live checks (20:48-20:52, after S1)

Command: `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent7\b2_apply_and_verify.ps1` (defaults: `-Tag b2-after -FixtureTag after3`). It applied the edits only after the live files matched the batch-1 hashes, then ran every check below. Report: `build/agent7/b2-apply-b2-after/report.txt`.

| Check | Result |
|---|---|
| Result hashes | device.h `703939AA91EFEA81`, device.cpp `3D01E63142DBFB50`, fps_counter.h `E05D6A554042B302`. These match the staged dry run and were unchanged at 20:54 |
| The other device.h includers | Unchanged against the 20:16 hashes in `build/agent7/syntax-b2-before/hashes.txt` (new list: `build/agent7/b2-apply-b2-after/hashes.txt`). Only device.h and device.cpp changed |
| Syntax, all 18 includers (`build/agent7/syntax-b2-after`) | All exit 0 with 0 errors. This includes main.cpp, which saw the edited header this time. Warnings match `syntax-b2-before`, except device.cpp 27 → 28: the new one is the `getenv` deprecation warning for the toggle at device.cpp:2131 |
| gpu-aot fixtures (`build/agent7/tests-after3` vs baseline, `compare_fixtures.py`) | "RESULT: no change against baseline". The same 6 pass (submission_waits, native_overlay, resize_fences, completion_callbacks, presentation_metrics, present_rect.cpp). The 11 stale ones fail with the same diagnostics |
| `test_fps_rects.py`, live device.cpp vs `build/agent7/batch1/device.cpp` (output in `build/agent7/test-fps-rects-b2-after`) | PASS. 640,064 digit cases are pixel-identical, and the cell-rect path matches batch 1. Mean clears per present 79.7 → 35.1. By reading: 30 fps 46 → 18, 165 fps 56 → 24, 1000 fps 82 → 26, 8888 fps 104 → 56. The worst ratio is 7/13 (digit 8). 200,000 random bitmaps give identical unions |
| `test_fps_counter.cpp` | Build and run exit 0 |
| Batch-1 copy of fps_counter.h | Added to `build/agent7/batch1/` at 20:53 from the snap1 copy (`79FC841E3180CA0D`, appended to `SHA256-1954.txt`) |

### Not in batch 2, with reasons
- **Gate-wait stats (follow-up 7):** `LockRecording` (device.cpp:774-779) is extracted by the stale `test_draw_device_view.py`, and `NativeRecordingGate` (native_worker.h) isn't mine. Queries, shaders, textures, native_worker and device.cpp:1361 also lock `NativeRecordingMutex()` directly, so counting in `LockRecording` would miss part of the gate. Worth doing only if the d0/d1 A/B shows an effect.
- **Overlay idle-skip (follow-up 4):** `QueueNativeOverlayFrame` is extracted by `test_native_overlay.py`, and the gain is one cross-thread post per frame.
- **FPS digit atlas (the rest of follow-up 5):** it needs a new texture, shader and PSO in the AOT pipeline, and (i) already halves the clears.
- **FSR 1 clear skip (follow-up 3):** FSR 1 is off by default (`present_effect`), and proving its passes cover the image needs fsr1_present.h, which isn't mine.
- **The hooks_device.cpp:282-284 comment (follow-up 10):** it is inside a fixture-extracted body.
- **Adapter logging (follow-up 9):** already there. device.cpp:903-906 logs `Native GPU [<fingerprint>]: D3D12 ready on '<adapter>' (WxH, N images)` at startup. The A/B plan said otherwise and is fixed. `EnumAdapterByGpuPreference` would be a Plume patch.
- **Moving the (g) wait (follow-up 6, corrected):** the wait already runs right after the present, which is the start of the guest's next frame. Moving it to the start of SwapHook would delay the present of a frame that is already recorded, which adds latency. The useful move is to after SwapHook releases the gate (draw.cpp, Agent 4), and only if the g1 A/B shows promise.

## Batch 1 listing (20:15 snapshot, task #6)

Line numbers in this section and in the batch-1 sections below are for the S1 files (device.cpp 2617 lines). After batch 2, device.cpp lines up to 755 are unchanged, 757-1901 move up 1, 1904-2127 move down 1, 2128-2264 move down 10, and 2265 onwards move down 12. device.h lines after 93 move down 2.

| Item | Files and lines | Default | Toggle (env var, read once) | When the toggle is off / old path restored |
|---|---|---|---|---|
| (a) Skip the gamma pass for an identity ramp | device.cpp:255, 1683-1696, 1850-1852, 1966-1972 | ON (output-identical) | `LEGO_NATIVE_FORCE_GAMMA_PASS=1` runs the pass again | Old pass, unchanged |
| (b) Skip the back-buffer clear when the copy covers it | device.cpp:2048-2059; present_rect.h:24-28 | ON (output-identical) | `LEGO_NATIVE_FULL_PRESENT_CLEAR=1` clears every present | Old clear, unchanged |
| (c) Window queries before g_mutex | device.cpp:1902-1912 | ON (same values) | none | n/a |
| (d) Limiter sleep outside the recording gate | device.cpp:1769-1784, 1825-1841, 1855-1874, 1883-1886; device.h:159-161; plus Agent 4's call in draw.cpp SwapHook (draw.cpp:5344, added 19:24) | OFF | `LEGO_NATIVE_UNLOCKED_PACING=1` (2000 µs margin) or `500..20000` µs | One static check per present; `LimitFrameRate` is byte-identical |
| (e) Frames-in-flight cap (report #1) | device.cpp:316, 1698-1754, 2391-2398, 2423-2426 | OFF | `LEGO_NATIVE_FRAMES_IN_FLIGHT=1..6`, intended for use with `LEGO_NATIVE_COMMAND_SLOTS=12` | No wait, no bookkeeping |
| (g) Swap-chain frame-latency wait | device.cpp:317, 1756-1767, 2179-2190, 2427 | OFF | `LEGO_NATIVE_LATENCY_WAIT=1..3` | No wait. Adds one `GetMaximumFrameLatency` call and one log line per device |
| (f) Report #2, guest waits | none; documented below | n/a | n/a | n/a |

- **Header edits (each one rebuilds the files that include it):**
  - device.h:159-161 adds `static void PaceFrameBeforeLock();` with a 2-line comment.
  - present_rect.h:24-28 adds `constexpr bool PresentRectCoversTarget(PresentRect, uint32_t, uint32_t)`.
- **No cvars were added.** The toggles are environment variables, read once into function statics, the same way as the file's existing `LEGO_NATIVE_*` switches.
- **New or extended log lines:**
  - `display gamma updated from title ramp ... identity={}`: the ` identity=` field is new.
  - `swap-chain max frame latency={} query={} waitable={} latency_wait={} set={}`: once per device.
  - `frames-in-flight cap={}`, `swap-chain latency wait={}` and `unlocked frame pacing margin={}us`: only when the env var is set.
  - `frames-in-flight cap={} waited on {} of the last 600 presents, {} ms total`: every 600 presents while (e) is on.

## Changes

### (a) Skip the display-gamma pass for an identity ramp (ON)
- **Where:**
  - `State::gamma_identity` (device.cpp:255).
  - `DisplayGammaIsIdentity` (1683-1696).
  - Set in `SetDisplayGamma` (1850) and logged there (1851-1852).
  - The gate is at 1966-1972.
- **What:** if the title's ramp maps every 8-bit input back to itself on every channel, the compute pass is skipped and the resolved input is presented directly.
- **Why:** the pass costs, on every present, a full-resolution compute dispatch with UAV barriers, a 1 KB ramp upload and 3 descriptor writes (session-1 item 5).
- **Exactness:**
  - The ramp is stored as R10G10B10A2_UNORM and the pass writes RGBA8. Output i is exact when |255·level − 1023·i| ≤ 409 (under 0.4 ULP) for every entry and channel. A linear ramp rounded to 10 bits passes this test, and the test is conservative.
  - RGB is then bit-identical. Only back-buffer alpha can differ. The swap chain is FLIP_DISCARD and created without an alpha mode (UNSPECIFIED), so DXGI ignores alpha, and the overlays blend with their own source alpha.
- **Risk:** low. Any non-identity ramp still gets the pass. `LEGO_NATIVE_FORCE_GAMMA_PASS=1` restores the old path.
- **Verification:**
  - `bench/agent7/test_present_skips.py` (see Verification).
  - In game, the log line shows `identity=true|false` for every ramp the title sets.

### (b) Skip the full back-buffer clear when the copy covers every texel (ON)
- **Where:** device.cpp:2048-2059, plus `PresentRectCoversTarget` in present_rect.h:24-28.
- **What:** the clear still runs if any of these holds:
  - `LEGO_NATIVE_FULL_PRESENT_CLEAR=1` is set;
  - FSR 1 is requested;
  - the present rect doesn't cover (0, 0, width, height);
  - the acquired back buffer's size differs from width×height.
- **Why:** the full-screen clear ran every present, and the copy then overwrote it (session-1 item 6).
- **Exactness:**
  - The copy (device.cpp:2080-2098) is a full-viewport triangle: viewport = present rect, scissor = the full image, opaque blend, full write mask, no discard. So when the rect is the whole image, every texel is written.
  - With FLIP_DISCARD the previous contents are undefined anyway.
  - FSR 1 keeps the clear, because its passes haven't been proven to cover the image.
- **Risk:** low. Letterboxed or integer-scaled output still clears.
- **Verification:**
  - `test_present_rect.cpp` passes.
  - `test_present_skips.py` checks the predicate against `FitPresentRect` for 3,203,200 size pairs.

### (c) Win32 window queries before g_mutex (ON, same values)
- **Where:** device.cpp:1902-1912, before `std::unique_lock lock(g_mutex)` at 1914.
- **What:** `GetForegroundWindow`, `GetWindowLongPtrW(GWL_STYLE)` and `MonitorFromWindow` now run before g_mutex is taken. They still run under the recording gate, which is the only lock that `g_state` and its swap chain change under.
- **Measured:** all three together cost **31-33 ns per present** (microbench, foreground-like runs). Session 1 estimated microseconds, which was wrong. The gain is negligible, but the change costs nothing and keeps win32k calls out of g_mutex. A cache was rejected (see below).
- **Risk:** trivial.
- **Verification:** fixtures (`test_presentation_metrics.py` passes), plus microbench `[win32]`.

### (d) Limiter sleep outside the recording gate (OFF: `LEGO_NATIVE_UNLOCKED_PACING`)
- **Where:**
  - `UnlockedPacingMarginUs` (device.cpp:1773-1784): `=1` means 2000 µs; other positive values are clamped to 500..20000 µs; unset or ≤0 means off.
  - `PublishFramePace` (1825-1841) publishes `LimitFrameRate`'s next deadline to `g_pace_next` and `g_pace_limit` (1769-1771). PresentTexture calls it only when the toggle is on (1883-1886).
  - `HostDevice::PaceFrameBeforeLock` (1855-1874; declared at device.h:159-161) sleeps on a thread-local high-resolution waitable timer until `deadline − margin`, capped at 1 s. It takes no lock.
  - **Caller:** Agent 4 added `HostDevice::PaceFrameBeforeLock();` to SwapHook at draw.cpp:5344 (saved 19:24), between `HostDevice::PollCompletionCallbacks();` and `auto recording = HostDevice::LockRecording();`.
- **What:**
  - Most of the frame-rate wait now happens before SwapHook takes the recording gate.
  - `LimitFrameRate` is byte-identical to the original. It still waits under the gate for the same deadline, including its 0.5 ms spin.
  - So presents keep their schedule, as long as everything between the pre-lock wake-up and the limiter fits in the margin: timer lateness, waiting for the gate, and the work before the limiter.
- **Why:** with a 60 FPS cap, the old limiter held the gate for most of each frame while it slept and spun (session-1 item 4).
- **Why the spin stays under the gate:** the task requires the same pacing.
  - If the gate were released before the final spin, re-taking the gate and the pre-present work would land after the deadline, shifting the present by a variable amount.
  - A shorter or cooperative spin (`Sleep(0)`, `SwitchToThread`) can lose a scheduler quantum.
  - So only the sleep moves.
- **Exact deadline:**
  - On both of its branches, `LimitFrameRate` sets `next = max(next + period, now)`, where `now` is read before any wait.
  - `PublishFramePace` repeats that arithmetic, using the time taken just before `LimitFrameRate` was called in place of `now`.
  - By induction, the published deadline is never later than `LimitFrameRate`'s, and is earlier only by the gap between the two clock reads. The microbench measured that gap at 0.0-0.5 µs.
  - If the published deadline is stale (for example, written by another thread), the wake time is already past and the function returns at once. `LimitFrameRate` then waits exactly as before.
- **Measured** (pacing simulation, `present_microbench-191001.txt`, foreground-like, 5 runs per row, medians):
  - The simulation uses verbatim copies of `LimitFrameRate`, `PublishFramePace` and `PaceFrameBeforeLock`.
  - Frame shape: 2000 µs of guest work outside the gate, 600 µs under the gate before the limiter, and 400 µs after the present.
  - "Pub-gap" is `LimitFrameRate`'s next deadline minus `PublishFramePace`'s, min..max over every frame and run.

  | Cap | Mode | Interval mean (µs) | Interval sd | Late p99 | Gate held per frame | Pub-gap (µs) |
  |---|---|---|---|---|---|---|
  | 60 | old | 16666.9 | 848 | 2089 | **14651** | n/a |
  | 60 | margin 2000 µs | 16666.7 | 399 | 1438 | **2100** | 0.1..0.2 |
  | 60 | margin 4000 µs | 16666.7 | 574 | 1720 | 4049 | 0.0..0.2 |
  | 120 | old | 8333.3 | 892 | 2981 | **6313** | n/a |
  | 120 | margin 2000 µs | 8333.3 | 679 | 2338 | **2095** | 0.0..0.2 |
  | 120 | margin 4000 µs | 8333.3 | 667 | 2528 | 4071 | 0.1..0.3 |
  | 240 | old | 4169.9 | 536 | 2546 | 2147 | n/a |
  | 240 | margin 2000 µs | 4166.7 | 507 | 2156 | 2143 | 0.0..0.2 |
  | 240 | margin 4000 µs | 4183.2 | 752 | 4124 | 2143 | 0.1..0.5 |

  - **Mean intervals match** at every cap.
  - The sd and p99 columns are dominated by timer lateness on this shared, loaded machine (timer p99 was 1.4-4.3 ms in this run). Across runs they move both ways: in the 18:58 run, 120 FPS with margin 2000 µs had an sd of 579 against 371 for old. This is noise, not a measured improvement.
  - At 240 FPS nothing changes, because the frame is shorter than the margin plus the work.
  - The spin under the gate is unchanged at about 130-170 µs per frame.
  - Keep `=1` (2000 µs) as the default meaning. A/B both `=1` and `=4000` in game.
- **Caveats:**
  - In threaded mode (`LEGO_NATIVE_THREADED=1`), the worker holds NativeRecordingMutex across a batch of tasks (native_worker.cpp:270-290), so the sleep is still under the gate. Pacing is unchanged either way.
  - The benefit depends on which other threads need the gate during the limiter wait. That hasn't been measured; the A/B and follow-up 7 cover it.
- **Risk:** low to medium (pacing), hence OFF. If timer lateness plus gate wait plus pre-limiter work exceeds the margin, that frame presents late by the excess.
- **Verification:** compile check, fixtures, and the microbench above.

### (e) Frames-in-flight cap: report #1, the ring counts submissions (OFF: `LEGO_NATIVE_FRAMES_IN_FLIGHT`)
- **Where:**
  - `State::present_serials` (device.cpp:316).
  - `NativeFramesInFlight` (1698-1711).
  - `PresentThrottle`, `FindPresentThrottleLocked` and `WaitPresentThrottle` (1713-1754).
  - The serial is recorded at 2391-2398, and the wait is at 2426, after g_mutex is released but still under the recording gate.
- **What:** after each present, wait until the present submitted N presents earlier (N = 1..6) has completed on the GPU. This only adds a wait. The ring bookkeeping (slot count, slot fences, `WaitForSubmissionLocked`) is unchanged.
- **Why (report #1):**
  - The ring has 3 slots, and every guest kickoff, `Synchronize` call and present uses one. So `BeginFrameCommandsLocked` waits on the fence from 3 submissions ago, which is often the current or previous frame.
  - tools/gpu-aot/native-performance-vsync-20261010.md reports ~16% of the render thread in `WaitForSubmissionLocked` in the main menu.
  - The existing `LEGO_NATIVE_COMMAND_SLOTS=12` removes that stall, but lets the CPU run up to 12 submissions ahead, which can be several frames of latency.
  - (e) adds a cap counted in frames instead: use `COMMAND_SLOTS=12` with `FRAMES_IN_FLIGHT=2` (or 1).
- **Design:**
  - Under g_mutex, the throttle finds the slot whose `slot_submission` equals the recorded serial, AddRefs that slot's D3D12 fence, and takes value `fenceValue − 1`. Plume signals `fenceValue` and then increments it (plume_d3d12.cpp:2850-2852; its own wait uses `fenceValue − 1` at 2860).
  - It waits on an event outside g_mutex, with a 1 s timeout.
  - If the slot has been reused or the serial has already completed, there is nothing to wait for. A slot is only reused after a verified wait.
  - It logs the wait count every 600 presents.
- **Why not session 1's sketch:** making the ring itself wait on "N presents ago" would mean editing `WaitForSubmissionLocked` and `BeginFrameCommandsLocked`. Fixtures compile those functions (`test_frame_ring_transaction`, `test_command_slots`, `test_gpu_timestamps`).
- **Risk:** medium (pacing and latency), hence OFF. With 3 slots it is mostly redundant, since the ring already caps the queue.
- **Verification:** compile check, plus fixtures: `test_submission_waits.py`, `test_resize_fences.py` and `test_completion_callbacks.py` pass and are unchanged. Still needs the in-game A/B.

### (g) Swap-chain frame-latency wait (OFF: `LEGO_NATIVE_LATENCY_WAIT`)
- **Where:**
  - `State::latency_configured` (device.cpp:317).
  - `NativeLatencyWait` (1756-1767).
  - Configure and log once per device at 2179-2189; the waitable is fetched at 2190; the wait is at 2427.
- **What:** with a value of 1..3, call `SetMaximumFrameLatency(N)` once, then after each successful present wait up to 1 s on the swap chain's waitable object.
- **Plume facts, verified** (plume_d3d12.cpp:1360-1391):
  - The swap chain is FLIP_DISCARD and is created with `FRAME_LATENCY_WAITABLE_OBJECT`, plus ALLOW_TEARING when supported.
  - Plume calls `SetMaximumFrameLatency(desc.maxFrameLatency)`. device.cpp passes 0, which DXGI rejects, so the default stays in place. The new once-per-device log line shows the value DXGI kept.
  - `RebuildSwapChain` only calls `resize()`, which is ResizeBuffers on the same chain (device.cpp:692-697), so the setting survives resizes.
- **When off:** no wait. It adds one `GetMaximumFrameLatency` call and one log line per device.
- **Risk:** medium (pacing), hence OFF. The wait runs under the recording gate; follow-up 6 (corrected in batch 2) would move it to after SwapHook releases the gate.
- **Verification:** compile check. Still needs the in-game A/B.

### (f) Report #2: guest fence and idle waits drain the whole GPU. Documented, not implemented
- **The 4 `BlockOnFence` call sites (sub_83FBF8A0) never run natively.** They either sit under the original Swap, which `SwapHookQueued` (draw.cpp:5620) replaces, or run at device destruction (sub_83FCF400). One more possible path, through callback sub_83FC2808, wasn't traced. A targeted wait would therefore gain about nothing.
- **A targeted wait would also have to drain the native worker's queue** (`KickOffSegmentHook` → `NativeWorkerSubmit`, hooks_device.cpp:272).
- `BlockUntilIdle` is a full drain by design. A targeted `BlockUntilNotBusy` (kResource) would need per-resource last-use serials (follow-up 1).
- Fixtures extract the hook bodies (`BlockUntilNotBusyHook`, `BlockUntilIdleHook`, `BlockOnFenceHook`, `InsertCallbackHook`, `KickOffSegmentHook`, `KickOffHook`) and the ring functions, so none of them were touched.
- **Comment bug, not edited because the body is fixture-extracted:** the comment at hooks_device.cpp:282-284 says "Callers store the returned ring marker…". In fact, `KickOff`'s return value is used as the PM4 write cursor; returning dev+0x6000 works only because that address is scratch.

### (h) Inline `CurrentDrawPreparation`: batch 2
Done in task #20; see "Batch 2 listing". The fixture mocks turned out to be standalone, and the change rebuilds 18 TUs.

## Verification

| Check | Command | Result |
|---|---|---|
| Fixtures (19:10-19:11, after the final edit) | `powershell -NoProfile -File bench\agent7\run_tests.ps1 after2` then `python bench\agent7\compare_fixtures.py baseline after2` | **RESULT: no change against baseline.** The same 6 pass: submission_waits, native_overlay, resize_fences, completion_callbacks, presentation_metrics and present_rect.cpp. The 11 stale fixtures fail with the same diagnostics as at baseline. |
| Compile (19:17, after the final edit) | `powershell -NoProfile -ExecutionPolicy Bypass -File env\compile-one.ps1 DimensionsRecomp\rexlego\src\gpu_native\device.cpp -OutDir build\agent7\obj -Db build\dev\compile_commands.json -SyntaxOnly` | Exit 0, 0 errors, using the real generated `build/dev/generated/native_gpu_build_info.h` (no stub). All 27 warnings are the file's usual `getenv`/`sscanf` deprecation warnings, the same count as before the edits. Log: `build/agent7/compile-device-syntax3.log`. A 19:09 run with a stub for that header gave the same result (`compile-device-syntax2.log`). |
| Unit | `. .\env\devshell.ps1 -Quiet; python bench\agent7\test_present_skips.py` | PASS. See below. |
| Microbench | `python bench\agent7\run_microbench.py --runs 5 --foreground` | Win32 31.4 ns per present; pacing table in (d). Output: `build/agent7/bench/present_microbench-191001.txt`. |

- **Unit test details** (`test_present_skips.py`):
  - A linear 16-bit decoded ramp is classified identity (worst error 0.1848 ULP), and so is a 10-bit rounded ramp (worst 0.1232 ULP).
  - Of 12,216 single-entry perturbations, 2,304 still give exact output. 1,692 of those are classified identity, each with at least 0.1 ULP margin, and nothing inexact is classified identity.
  - 0 of 20,000 random ramps are accepted.
  - Present rects: 3,203,200 size pairs checked, 121 of them covering; the `static_assert`s pass.
- **Stub header:** no longer used. The 19:09 compile used `build/agent7/stubinc/native_gpu_build_info.h` (only the fingerprint constant) because `build/dev` didn't have the generated header yet. The 19:17 check used the real header, and the stub directory was deleted at 19:22.
- **Stale fixtures and code I changed:** I checked each one statically. None of them extracts or asserts on a line I edited:
  - `test_frame_rate_settings.py` compiles the `LimitFrameRate` body, which is byte-identical again.
  - `test_frame_cadence.py` extracts device.cpp:2278-2388; my edits are at 2179-2190 and 2391+.
  - `test_gpu_timestamps.py` extracts the protected `gpu_timestamps`…`MarkSubmissionLocked` blocks, which are unchanged.
  - `test_native_vsync.py` asserts on `NativeVsyncRequested` and the `setVsyncEnabled` text, which are unchanged.
  - The others (command slots, frame ring, draw device view, sampler settings, CPU resource wait, queued frame boundaries, threaded callback) cover functions I didn't touch.

## Runner specs for Agent 8 (native ON build, 20:10)
These are the timing runs for (a)/(b), (d), (e) and (g) in Agent 8's user-started runner. They replace the arm table in the A/B plan below. Runs launched from agent commands are functional checks only (hidden desktop).

- **Bin:** `build/agent2/native-bin`, staged 21:48. It is S1 + p1 (my perf.csv rows) + p2 (the Plume `GPU_UPLOAD` cast) + Agent 6's N1/N1i/N1d inputs. The exe sha256 starts `3B329E9550A1178C`, and its native GPU fingerprint is `befeb1184e6c7abc`. The game needs `legodimensions.toml` in its working dir; the runner writes one into each run dir, which it uses as the working dir.
  - **String check (21:51):** the exe contains every batch-1 toggle name (`LEGO_NATIVE_FORCE_GAMMA_PASS`, `_FULL_PRESENT_CLEAR`, `_UNLOCKED_PACING`, `_FRAMES_IN_FLIGHT`, `_COMMAND_SLOTS`, `_LATENCY_WAIT`) and the new log lines (`identity=`, `swap-chain max frame latency`, `unlocked frame pacing margin`, `frames-in-flight cap`). It doesn't contain `LEGO_NATIVE_FPS_CELL_RECTS`, as expected for batch 1, so arm i1 needs a batch-2 build.
- **Agent 8's matrices (22:09):** three files in `bench/agent8/run/`, all checked against the table below at 22:10. The arms and env match.
  - `matrix-native-tier1.json`: n0 ×5; a1, d0 and d1 ×3; plus Agent 4's t1 and t2 ×5. 25 runs, about 75 min.
  - `matrix-native-tier2.json`: n0, e0, e1, v0 and g1 ×3, plus e0-diag and e1-diag ×1. 18 runs, about 54 min.
  - `matrix-native-tier3.json`: d1/d2, e1/e2 and g1/g2 ×3, each pair in one session. 19 runs, about 57 min.
  - Each starts with one unscored cold run and uses round-robin order (the `run-matrix.ps1` default), a 30 s warm-up from the first frame and 60 s windows.
- **One run:** `powershell -NoProfile -ExecutionPolicy Bypass -File bench\agent8\run\run-timing.ps1 -BinDir <native ON bin> -Tag <arm>-r<k> -Warmup 120 -Seconds 60 -Env '<env>'`
  - `-Warmup 120`: the baseline's first frame came 61 s after start, and the native boot time isn't known yet. Once the first native boot shows when frames start, use (first frame + 30 s).
  - **Every** arm's `-Env` starts with `LEGO_NATIVE_FRAME_METRICS=native-frames.csv`. The path is relative, and the runner's CWD is the run dir. It writes one CSV row per present, the same cost in every arm.
  - Don't set `LEGO_NATIVE_TIMING` in timing rounds: it turns on texture timing, which perturbs frame times. Without it, the CSV's `frame_slot_wait_ms`, `acquire_cpu_ms` and `present_submit_cpu_ms` stay 0; `interval_ms` and `swap_present_cpu_ms` are filled. For the slot waits, do one extra run each of e0 and e1 with `;LEGO_NATIVE_TIMING=1` and label it diagnostic.
  - Order: round-robin through a tier's arms (n0, a1, d0, d1, n0, a1, …), at least 3 rounds (5 preferred). Tier 1 first.
- **perf.csv rows:** native-bin has the one-line patch as S1+p1 (`build/agent2/snap1/PATCHES-S1.tsv`), so perf.csv gets one row per present. Without the patch, the S1 native present calls `ResetFrameCounters()` but not `WriteCsvFrame()`, so perf.csv stays header-only and the runner flags "no frames". With such a build, read the frame times from `native-frames.csv` (`interval_ms`) with the script below.

| Tier | Arm | `-Env`, after `LEGO_NATIVE_FRAME_METRICS=native-frames.csv;` | Compare | Expected; game.log check |
|---|---|---|---|---|
| 1 | n0 | nothing: the new defaults, (a), (b) and (c) on, VSync off, cap 240 | reference | `display gamma updated … identity=`. If it's only ever `false`, (a) is inactive and n0/a1 measures (b) alone |
| 1 | a1 | `LEGO_NATIVE_FORCE_GAMMA_PASS=1;LEGO_NATIVE_FULL_PRESENT_CLEAR=1` (the old present path) | a1 vs n0: mean fps, p50, p99, cores | n0 ≥ a1 |
| 1 | d0 | `LEGO_NATIVE_VSYNC=0;LEGO_NATIVE_FPS_LIMIT=60` | reference for d1 | `presentation cap override=60`. The script's last-row line must show `native_vsync=0` (the settings menu can override the env) |
| 1 | d1 | `LEGO_NATIVE_VSYNC=0;LEGO_NATIVE_FPS_LIMIT=60;LEGO_NATIVE_UNLOCKED_PACING=1` | d1 vs d0: sd, p99, p99.9, cores | Mean fps within ±0.5% of d0; sd and p99 no worse. `unlocked frame pacing margin=2000us` |
| 2 | e0 | `LEGO_NATIVE_COMMAND_SLOTS=12` | e0 vs n0: the bigger ring alone | — |
| 2 | e1 | `LEGO_NATIVE_COMMAND_SLOTS=12;LEGO_NATIVE_FRAMES_IN_FLIGHT=2` | e1 vs e0: fps, p99, sd | `frames-in-flight cap=2`, then `… waited on N of the last 600 presents` every 600 presents |
| 2 | v0 | `LEGO_NATIVE_VSYNC=1` | reference for g1 | swap-chain line shows `vsync on` |
| 2 | g1 | `LEGO_NATIVE_VSYNC=1;LEGO_NATIVE_LATENCY_WAIT=1` | g1 vs v0: sd, p99 | `swap-chain latency wait=1`; `swap-chain max frame latency=… latency_wait=1 set=…` |
| 3 | d2 | d1 with `LEGO_NATIVE_UNLOCKED_PACING=4000` | d2 vs d1 | `margin=4000us` |
| 3 | e2 | e1 with `LEGO_NATIVE_FRAMES_IN_FLIGHT=1` | e2 vs e1 | `cap=1` |
| 3 | g2 | g1 with `LEGO_NATIVE_LATENCY_WAIT=2` | g2 vs g1 | `latency wait=2` |

- **What to read and send back:**
  - From each run's `summary.txt`: status and problems, mean fps, median, p99, p99.9, max, frames > 33 ms and > 100 ms, CPU cores (mean and max).
  - Then, for all run dirs at once: `python bench\agent7\native_frames_summary.py build\agent8\runs\<HHmm>-<arm>-r<k> …`. It prints per run the perf.csv and native-frames.csv stats with stddev, the present-path column means, cores and the game.log toggle lines, then per-arm medians. Put its output in your notes, or just send me the run dir names and I'll analyse them.
  - Keep the run dirs (perf.csv, native-frames.csv, game.log, proc.csv).
- **Script check (20:05):** on a synthetic 4,000-row run, the stats match the known pattern (1 frame in 100 at 40 ms gives p99 16.667 and p99.9 40.000, with 35 frames > 33 ms in 3,551). It also parses Agent 8's real `build/agent8/runs/1928-first/perf.csv`.

## A/B plan (native ON build; Agent 8 runs it while Agent 3 is away)
- **Common setup:**
  - Same scenes: main menu idle for 60 s, and the hub (idle, then the same walk) for 60 s.
  - At least 3 runs per arm (5 preferred); compare medians.
  - Env for every run: `LEGO_NATIVE_FRAME_METRICS=<run>.csv`. Add `LEGO_NATIVE_TIMING=1` (for `frame_slot_wait_ms` and sync calls by reason) only in diagnostic runs, since it perturbs timing. Add `LEGO_NATIVE_GPU_TIMESTAMPS=<run>-gpu.csv` for the GPU-side arms.
  - For the pacing arms, turn VSync off (`LEGO_NATIVE_VSYNC=0`) so the limiter does the pacing.
- **First, read the startup log:**
  - `swap-chain max frame latency=… waitable=…` (the DXGI default).
  - `display gamma updated … identity=…`: if it's always `false`, (a) has no effect.
  - Which adapter is in use: `Native GPU [<fingerprint>]: D3D12 ready on '<adapter>' (WxH, N images)` (S1 device.cpp:904-907). `LEGO_NATIVE_ADAPTER` overrides the choice.

| Arm | Env (on top of the common env) | Look at |
|---|---|---|
| A0 | none (new defaults: (a), (b), (c) on) | FPS, GPU frame time |
| A1 | `LEGO_NATIVE_FORCE_GAMMA_PASS=1 LEGO_NATIVE_FULL_PRESENT_CLEAR=1` (the old present path) | A0 vs A1 FPS and GPU time; a screenshot of each, whose RGB must match |
| B1 | `LEGO_NATIVE_COMMAND_SLOTS=12` | FPS, `frame_slot_wait_ms`, input latency (PresentMon, if available) |
| B2 | `LEGO_NATIVE_COMMAND_SLOTS=12 LEGO_NATIVE_FRAMES_IN_FLIGHT=2` | Same, plus the `frames-in-flight … waited on N of the last 600 presents` lines |
| B3 | `LEGO_NATIVE_COMMAND_SLOTS=12 LEGO_NATIVE_FRAMES_IN_FLIGHT=1` | Same |
| C1, C2 | `LEGO_NATIVE_LATENCY_WAIT=1`, then `=2` (VSync on and off) | FPS, frame-time stddev, latency |
| D0, D1, D2 | `LEGO_NATIVE_FPS_LIMIT=60` (and `=120`) with: no toggle (D0); `LEGO_NATIVE_UNLOCKED_PACING=1` (D1); `=4000` (D2) | Frame-time mean and stddev from the metrics CSV, render-thread CPU %. Agent 4's SwapHook call is in (draw.cpp:5344); check that the log shows `unlocked frame pacing margin=…us` |

## Rejected ideas
- **Publishing the deadline from inside `LimitFrameRate`** (my first version, 18:46-19:08): `test_frame_rate_settings.py` compiles that body on its own. Replaced by `PublishFramePace`.
- **Estimating the deadline as "last present + period":** after a late frame, `LimitFrameRate` catches up to its schedule, and the estimate would miss that and wake late by the lateness. The exact mirror is used instead.
- **Moving all of `LimitFrameRate` before `LockRecording`:** shifts the present by the variable work between the start of SwapHook and the present.
- **A shorter or cooperative final spin** (`Sleep(0)`, `SwitchToThread`): can lose a quantum and present late.
- **Caching the Win32 queries:** they cost 31 ns per present. A cache would add invalidation risk on focus and monitor changes for no gain.
- **Routing `BlockOnFence` to a targeted wait:** the path never runs natively, so the benefit is about zero (see (f)).
- **Editing fixture-extracted hook bodies or the ring functions** (`WaitForSubmissionLocked`, `BeginFrameCommandsLocked`, `Synchronize`, `KickOff*Hook`, and so on): fixture constraints. (e) gets the effect with a wait outside them.
- **(h), inlining `CurrentDrawPreparation`:** deferred in batch 1 on a fixture concern that turned out to be wrong; done in batch 2.

## Ranked follow-ups
1. **Count sync calls by reason in gameplay** (`LEGO_NATIVE_TIMING=1`). If kResource is frequent, add per-resource last-use serials for `BlockUntilNotBusy`, with a targeted wait that also drains the worker queue.
2. **Display gamma (display_gamma_gpu.h, not my file):** cache the ramp upload and the descriptors per slot with a generation counter, and fold the LUT into the copy or RCAS shader. This removes the pass for non-identity ramps too.
3. **Extend the clear skip to FSR 1** once its passes are proven to cover the image, and batch the FSR 1 barriers.
4. **Skip the native-overlay post when nothing is visible** (native_overlay.cpp:169-180). This needs a thread-safe "has dialogs" flag.
5. **FPS overlay:** batch 2's (i) merges touching cells (−56% clears). The meter is on by default (`native_show_fps`). A digit atlas would need a new texture, shader and PSO.
6. **Move the (g) latency wait to after SwapHook releases the gate** (draw.cpp, Agent 4), only if the g1 A/B shows promise. Not to the start of SwapHook: that would delay the present of a frame that is already recorded.
7. **Instrument waits on the recording gate per thread,** to size the benefit of (d). Then make the limiter's spin window adaptive to the timer lateness measured in game. This needs native_worker.h's `NativeRecordingGate` (not mine), because several callers lock `NativeRecordingMutex()` directly and `LockRecording` is fixture-extracted.
8. **Threaded mode:** release the worker's gate around the pre-lock sleep (native_worker.cpp).
9. **Adapter:** Plume picks the adapter with the most `DedicatedVideoMemory`, so the MX570 should win over Iris Xe. The chosen adapter is already logged at startup (`... ready on '<adapter>'`); check it in the first native boot. Optionally use `EnumAdapterByGpuPreference` (a Plume patch).
10. **Fix the hooks_device.cpp:282-284 comment** together with whoever refreshes that fixture.
11. **(h): inline `CurrentDrawPreparation`:** done in batch 2.

## Status of the session-1 items (appendix below)

| Session-1 item | Session-2 outcome |
|---|---|
| 1. Ring counts submissions | (e), OFF toggle |
| 2. Guest waits drain the GPU | (f), documented; follow-up 1 |
| 3. Latency waitable unused | (g), OFF toggle; Plume facts verified |
| 4. Limiter spins under the lock | (d), OFF toggle |
| 5. Gamma pass for an identity ramp | (a), ON; caching and LUT folding are follow-up 2 |
| 6. Full back-buffer clear | (b), ON; FSR 1 is follow-up 3 |
| 7. Win32 queries under g_mutex | (c), ON; measured at 31 ns, not µs |
| 8. FSR 1 barriers | follow-up 3 |
| 9. FPS overlay clears | (i) in batch 2, ON (output-identical); follow-up 5 |
| 10. Hidden overlay post | follow-up 4 |
| 11. Adapter selection | Plume compares `DedicatedVideoMemory` (plume_d3d12.cpp:3828-3957); the adapter is already logged at startup; follow-up 9 |
| 12. Minor items | no action |

## Appendix: session-1 analysis (16:53, unchanged)
Kept for reference. Line numbers are from the pre-session-2 device.cpp (`perf/opt` @ v0.2.0), so they are now off by up to about 250 lines. Where this appendix and the sections above differ, the sections above are current. The Plume source was read in session 2, so the open Plume questions in items 3 and 11 are answered above.

### Opportunities, ranked by expected win

#### 1. The frame ring counts submissions, not frames, so the CPU can't get a frame ahead
- **Where:** device.cpp:206-212 `NativeCommandSlotCount()` returns 3. The env var `LEGO_NATIVE_COMMAND_SLOTS` only accepts 3 or 12. The comment at device.cpp:221-222 says "Guest kickoffs consume slots independently of swap-chain presentation". Also `SubmitRecordedWork()` at device.cpp:1380-1401 and `BeginFrameCommandsLocked` at device.cpp:699-747. The latter calls `WaitForSubmissionLocked` (device.cpp:644-676), which calls `queue->waitForCommandFence` at line 657.
- **What's slow:** Every guest kickoff ends and submits the open command list and advances `frame_slot`. `Synchronize` (1268-1276), the acquire-failure path (1779-1788) and present (1974-1988, 2206) also use up slots. Opening the next list waits on the fence from 3 submissions ago. With 3 or more submissions per displayed frame, that fence belongs to the current or previous frame. The CPU then blocks on the GPU mid-frame, so CPU and GPU take turns instead of overlapping.
- **Evidence:** tools/gpu-aot/native-performance-vsync-20261010.md reports the render thread spending about 16% of its time in `WaitForSubmissionLocked` in the main menu.
- **Proposed change:** Measure first, then put it behind a cvar whose default keeps the exact old path (use the same cvar macro as `native_fps_limit` at device.cpp:75):
  ```cpp
  // device.cpp ~206 (sketch)
  // cvar native_frame_slots, default 3 (= legacy), clamp 3..16
  uint32_t NativeCommandSlotCount() {
    /* existing env override (3 / 12) first */
    return std::clamp<int32_t>(cvar_native_frame_slots, 3, 16);
  }
  ```
  A better long-term fix: keep the per-slot fences, but make `BeginFrameCommandsLocked` wait on "N presented frames ago" (for example N=2) instead of "3 submissions ago". Track the submission serial at each present and wait for that serial's fence.
- **Risk:** Medium. This changes pacing and latency, because more queued work means more latency, so the cvar must be OFF by default. Upload pages (4 MB per slot, `AllocateDrawUpload` 1206-1240), descriptor heaps and semaphores are all per slot, so memory grows with the slot count. Resource lifetimes are safe in the "more slots" direction.
- **How to verify:** tools/gpu-aot `test_resize_fences.py`, `test_temporal_worker*`, `test_native_vsync.py`. At runtime, use `LEGO_NATIVE_GPU_TIMESTAMPS=<csv>` and `LEGO_NATIVE_FRAME_METRICS`. Compare `frame_slot_wait` ms, FPS and PresentMon latency.

#### 2. Every guest fence or idle wait drains the whole GPU
- **Where:** `HostDevice::Synchronize` at device.cpp:1253-1310 submits the open list, then waits on **all** slots. Callers:
  - hooks_device.cpp:187-190, `BlockUntilIdle` (kIdle)
  - hooks_device.cpp:196-200, `BlockOnFence` (kFence). Its comment says a "full host drain is conservative".
  - hooks_device.cpp:260, `BlockUntilNotBusy` (kResource), after skipping non-native resources at lines 218 and 245-249
  - textures.cpp:3728 (kResource)
  - gpu_pass_profile.h:76 (diagnostics only)
- **What's slow:** Each call empties the GPU pipeline. The CPU waits for all queued GPU work, then the GPU sits idle while the CPU records the next batch. One such call per frame is enough to remove all CPU/GPU overlap.
- **Proposed change** (cvar `native_targeted_sync`, OFF by default):
  - `BlockOnFence`: when the guest inserts the fence, record the host submission serial, then wait only on that serial's slot fence.
  - `BlockUntilNotBusy`: track the last submission serial that referenced the resource and wait only on that.
  - `BlockUntilIdle` keeps the full drain.
- **Risk:** Medium to high. Wrong ordering would break the title's CPU readbacks (locks on render targets, queries). The old path must stay exact when the cvar is off.
- **How to verify:** Use the per-reason sync counters (`sync_calls` / `sync_ms` by reason in the texture-timing log) and the long-wait log line "completion callback GPU wait took". **Count first:** if the hub and levels show about 0 kFence/kResource syncs per frame, move this item down.

#### 3. The frame-latency waitable is never used, and the swap-chain config is unverified
- **Where:** device.cpp:854-855 creates the swap chain through Plume with `RenderSwapChainDesc(hwnd, B8G8R8A8_UNORM, 3)`. device.cpp never waits on the swap chain or its waitable object (no `wait(` call). The comment near device.cpp:679 mentions the latency object.
- **Already known:** tools/gpu-aot/test_native_vsync.py and patches/plume-lego.patch show how Present is called:
  - SyncInterval is `vsync && !enablePresentWait ? 1 : 0`.
  - With vsync off and tearing supported, it passes `DXGI_PRESENT_ALLOW_TEARING` (device.cpp:2031-2035 logs `tearing=`).
  - So tearing with VSync off looks handled already.
- **Unverified** without Plume source (prepare_plume.py pins e0c8871b930dc1a6544bf457f2348c456b9d7e13):
  - FLIP_DISCARD vs FLIP_SEQUENTIAL
  - whether `DXGI_SWAP_CHAIN_FLAG_FRAME_LATENCY_WAITABLE_OBJECT` is set
  - the `SetMaximumFrameLatency` value (the DXGI default is 3)
- **Proposed change** (cvar `native_latency_wait`, OFF by default): if the swap chain has the waitable, call `SetMaximumFrameLatency(1 or 2)` when it's created. Then call `WaitForSingleObjectEx(waitable, 1000, TRUE)` at frame start, before `LimitFrameRate` and `LockRecording`. This cuts input latency by up to 1-2 frames and lets the limiter sleep instead of spin. It probably needs a new Plume patch under tools/gpu-aot/patches, which I don't own, so coordinate with whoever does.
- **Risk:** Medium (pacing).
- **How to verify:** PresentMon (MsBetweenPresents, display latency), `test_native_vsync.py`, `test_presentation_metrics.py`, `test_window_mode.*`.

#### 4. The frame limiter busy-spins while holding the recording lock
- **Where:** `LimitFrameRate` at device.cpp:1691-1716 uses a high-res waitable timer, then a `YieldProcessor` spin for the last ~0.5 ms. `native_fps_limit` defaults to 240 (device.cpp:75). It's called at the top of `PresentTexture` (device.cpp:1736), **after** `LockRecording()` (device.cpp:1731).
- **What's slow:**
  - A core spins on every frame of a battery-powered laptop, where the MX570 and Iris Xe share power and thermal headroom.
  - While the limiter sleeps, it holds the recording lock, which blocks the temporal worker and other recorders.
- **Proposed change:** Move `LimitFrameRate()` ahead of `LockRecording()`. This changes lock order and timing, so put it behind a cvar that's OFF by default. Also try a shorter spin window (about 0.25 ms) on the high-res timer.
- **Risk:** Low to medium (jitter at high caps).
- **How to verify:** Frame-time stddev in PresentMon at 60/120/240 caps, and per-thread CPU% (ETW / Process Explorer).

#### 5. The display gamma compute pass runs every present once a ramp is set, even an identity ramp
- **Where:** The pass is at device.cpp:1804-1871. It's controlled by `gamma_table_valid`, which is set by the SetGammaRamp hook (hooks_device.cpp:346-369) and by `SetDisplayGamma` (device.cpp:1719-1727). Also `DisplayGammaGpu::Apply` in display_gamma_gpu.h (~55-86).
- **What's slow:** Every present runs a full-res compute dispatch with a UAV surface and barriers, so the whole output is read and written once more. That's about 16 MB of traffic per frame at 1080p RGBA8. `Apply` also does a Map/memcpy/Unmap of the 1 KB ramp and recreates 3 descriptors for every frame and slot. If the title sets an identity ramp, which is common, all of this is wasted work.
- **Proposed change** (pure efficiency, output stays exact, so it can be ON):
  ```cpp
  // SetDisplayGamma (device.cpp ~1719)
  gamma_table_valid = true;
  gamma_identity = IsIdentityRamp(table);  // exact under the shader's quantisation
  // PresentTexture (device.cpp ~1804)
  if (gamma_table_valid && !gamma_identity) { /* existing pass */ }
  ```
  Also cache the ramp upload and descriptors per slot with a generation counter, so `Apply` only rewrites them when they change. Later, fold the LUT into the final copy or FSR1 RCAS shader to remove the pass entirely.
- **Risk:** Low, as long as the identity test exactly matches how the shader samples the LUT. If the shader interpolates, identity must hold under interpolation too, so check the shader.
- **How to verify:** The `test_display_gamma*` fixtures in tools/gpu-aot, plus a readback compare of old vs new output for identity and non-identity ramps. Use GPU timestamps around the pass.

#### 6. The whole back buffer is cleared every present
- **Where:** device.cpp:1880, a `clearColor` on the acquired swap-chain image each present.
- **What's slow:** The clear covers the full screen even when `present_rect` already covers the whole output. The copy or FSR pass then overwrites every pixel anyway. With the flip model the buffer contents are undefined, so only the letterbox bars actually need clearing.
- **Proposed change** (pure efficiency): skip the clear when `present_rect` equals the full output. Otherwise, clear only the 2 bar rects, using separate single-rect clears, since multi-rect clears crashed nvwgf2umx.dll before.
- **Risk:** Low. Keep the clear whenever the image isn't fully covered: integer scaling, aspect bars, or rounding in present_rect.h.
- **How to verify:** `test_present_rect.cpp`, `test_window_mode.*`, and screenshot compares at 16:9, 21:9 and 4:3 windows.

#### 7. Win32 window and monitor queries on every present, under g_mutex
- **Where:** device.cpp:2001-2015 calls `GetForegroundWindow`, `GetWindowLongPtrW` and `MonitorFromWindow`, plus a linear vector search, on every present. `GetFullscreenState` and `EnumDisplaySettingsW` only run on a change (2027-2049).
- **Proposed change** (pure efficiency): cache the results and refresh every N presents, or on WM_SIZE / WM_MOVE / WM_DISPLAYCHANGE / activation. The win is small (µs per present, plus win32k locking), and the risk is trivial.
- **How to verify:** `test_window_mode.*`, `test_presentation_metrics.py`.

#### 8. FSR1 presenter barriers
- **Where:** device.cpp:1882-1901. In fsr1_present.h:172-199, each pass has a PIXEL_SHADER_RESOURCE ↔ RENDER_TARGET barrier pair on the intermediates, and there are per-slot heaps (12 slots).
- **Proposed change:** Batch the transitions into one barrier call at each pass boundary. Leave intermediates in the state the next frame expects, which saves one transition. Minor win.
- **How to verify:** `test_fsr1_present_gpu.cpp`, GPU timestamps.

#### 9. FPS overlay does up to 120 single-rect clears per present (only when show_fps is on)
- **Where:** device.cpp:1924-1961. The batched path is behind `LEGO_NATIVE_FPS_OVERLAY_BATCHED`, because multi-rect clears crashed nvwgf2umx.dll on 2026-10-10.
- **Proposed change:** Draw the digits with one textured quad from a digit atlas, or with one compute pass. This only matters when the counter is visible, so priority is low.

#### 10. Hidden overlay still costs a CPU post per present
- **Where:** native_overlay.cpp:169-180. `QueueNativeOverlayFrame` posts a `CallInUIThreadDeferred` lambda (capturing a shared_ptr) every present, even with no dialogs open. The GPU side already returns early (native_overlay_gpu.cpp:147-151).
- **Proposed change:** Skip the post when no dialogs or ImGui windows are visible. This needs a thread-safe `HasDialogs()`, for example an atomic flag. It saves one allocation and one cross-thread post per frame.
- **How to verify:** `test_native_overlay*.{py,cpp}`.

#### 11. Adapter selection on the hybrid laptop (MX570 + Iris Xe). Worth a lot if the wrong GPU is picked
- **Where:** device.cpp:824-826. The env var `LEGO_NATIVE_ADAPTER` picks an adapter by name. Otherwise Plume chooses; the comment says "most video memory". tools/gpu-aot/patches/plume-adapter-query.patch exists.
- **Analysis:**
  - If Plume compares `DedicatedVideoMemory`, the MX570 (2 GB) wins. If it compares shared or total memory, Iris Xe could win. I can't tell without the Plume source.
  - On Optimus laptops the display is attached to the iGPU, so a cross-adapter copy at present can't be avoided.
- **Proposed change:**
  - Plume patch: enumerate with `IDXGIFactory6::EnumAdapterByGpuPreference(DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE)`, falling back to `EnumAdapters1`. Keep the env override.
  - Log the chosen adapter's name and `DedicatedVideoMemory` at startup.
  - Add a cvar for the preference.
  - Check whether the exe exports `NvOptimusEnablement` / `AmdPowerXpressRequestHighPerformance`.
- **Risk:** Low.
- **How to verify:** Startup log, the GPU engine column in Task Manager, FPS on the user's laptop.

#### 12. Minor items, no action needed
- GPU timestamps are off unless `LEGO_NATIVE_GPU_TIMESTAMPS` is set (device.cpp:886-899). Readback is mapped after fence completion (gpu_timestamps.h:101-130), so there's no stall.
- `RefreshCompletedSubmissionsLocked` (617-635) calls GetCompletedValue once per slot, which is cheap.
- `RebuildSwapChain` (688-697) waits on all frames, but only on resize.
- temporal_present.cpp:319-331, `RejectTemporalMotion`, creates a framebuffer and does 2 clears per call when motion is rejected. Caching the framebuffer per target would help a little (low priority).
- `AllocateDrawUpload` (1206-1240) uses 4 MB upload pages per slot. Fine.

### Rejected, with reason
- Overlay GPU cost when hidden: already zero (early return).
- Timestamp and query readback stalls: none in the timestamp path, since readback happens after the fence. The F10 pass profile (gpu_pass_profile.h:76) drains the GPU on purpose and is diagnostics only.
- VSync-off tearing support: already present (ALLOW_TEARING flag plus SyncInterval 0, per test_native_vsync.py), pending confirmation in the Plume source.

### What I didn't get to read or verify
- **Plume D3D12 source.** It isn't checked out anywhere on disk. Unread: swap-chain flags, FLIP model, waitable object, MaxFrameLatency, adapter enumeration.
- temporal_* files other than temporal_present.cpp: temporal_shaders.h, temporal_texture_history.h, and the temporal camera, composition and worker sources.
- FSR3 upscaler sources (fsr3_settings.*, Fsr3Upscaler) and the FSR1 shader bodies.
- depth_resample.*, depth_alias*, color_alias_*, scaled_resolve.h, resolve_region.h, render_extent.h, present_rect.h.
- visual_effects.h, tonemap_dof.h, fps_counter.h, settings_runtime.*, settings_snapshot.*, hooks_portrait.cpp, crash_*, renderdoc_probe.h, portrait_probe.h, build_info.h.in, shaders/**.
- native_overlay.cpp outside lines 160-185, and native_overlay_gpu.cpp outside lines 145-195.
- device.cpp: only skimmed the ResolveHdrColor / resolve section (~1420-1560) and CreateFrameRing (~440-500).
- Callers of kickoff and Synchronize in draw.cpp, queries.cpp and gpu_pass_profile.h aren't traced. **The submissions-per-frame count is inferred, not measured.**
- No fixtures built or run, and no microbenchmarks (no toolchain or harness was available).
