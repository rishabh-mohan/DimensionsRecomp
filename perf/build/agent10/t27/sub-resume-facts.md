# RESUME.md draft 1: fact check

Written by Agent 10's read-only helper on 2026-11-23, 06:34-06:55 local. All paths are workspace-relative.

- **File checked:** `perf-notes/RESUME.md`, sha256 prefix 8BE0AB49EBF1AB52, 299 lines, mtime 06:23:49. It was unchanged at 06:34, 06:44 and at the end.
- **Scope:** §0-§7, §9 and §10. As asked, §6 item 6 and §8 are skipped. §6 item 7 (SCRNSAVE) is left to the parent as well.
- **Marks:**
  - **OK:** a source agrees.
  - **WRONG:** a source disagrees; the right value is given.
  - **STALE:** right when RESUME was written (06:23), but a newer file has overtaken it.
  - **NOTE:** true but incomplete.
  - **UNVERIFIED:** no source found.
- **Citations:** `R:n` means RESUME line n. Sources are cited as file:line and were read between 06:34 and 06:51. SESSION2 had 3328 lines at the time (mtime 06:34:18).
- **Git:** only read-only commands, in both repos: `log`, `rev-parse`, `branch -vv`, `show --stat` and `config --get`. No `status` or `fetch`.

## 1. WRONG and STALE items (fix these first)

1. **R:54, COMMIT-CHECK "PASS, with 1 WARN about moltenvk": WRONG (stale).**
   - The current `build/agent2/COMMIT-CHECK.md` (06:06, hand note 06:16) says "RESULT: PASS (main check). Extended checks: PASS" (L18) and "RESULT: PASS; EXTENDED: PASS" (L125).
   - moltenvk is "PASS (note)" (L95): 10 symlink entries, of which 8 are absent in snap1 and 2 are plain files. The reason is that the snap1 copy didn't keep the symlinks (L114).
   - The fact sheet's L37 still quotes the 05:57 version, which had the WARN.
2. **R:157, W6 "faster in 10 of 10 rounds": WRONG as worded.**
   - By median frame time, p2fc beat s0 in **9 of 10** rounds (`build/agent8/readout/w-followup/W6.md` L7, L82: "9/10 (p 0.021)").
   - The exception is pass 1, round 1: p2fc 2.135 ms against s0's 2.079 ms (`build/agent8/matrix/20261123-0009/summary.md` L22, L25).
   - The 10 of 10 belongs to C1 = p2fc − p2f (W6.md L12, L86).
   - FINDINGS L14 has the same "all 10 rounds".
3. **R:220, W8a arms: WRONG against the staged matrix.**
   - RESUME says "native3d against native4b with #2 on (or the #1 pack)". It follows the plan row S4-DRAFT L404 ("native3d / n-S4a with #2 ON").
   - The staged W8a is n0 (miss cache off) against mc (`LEGO_NATIVE_SHADER_MISS_CACHE=1`), both on native4b-bin (`build/agent8/w-followup/matrix-window8a.json` L2, L29, L33).
   - Its GO line is `only=n0,mc repeats=6`: 13 runs, 27.4 min, runner 30 (`build/agent8/w-followup/PROPOSAL.md` L78).
   - W8a4 is the same comparison on native4 (`only=n4,n4mc`, PROPOSAL.md L79).
   - The W8a matrix is in `build/agent8/w-followup/`, not `bench/agent8/run/` (see R:291).
4. **R:106 and R:221-222, #21: STALE.** RESUME says "`LEGO_NATIVE_CHAIN_PRIORITY=1`, proposed … isn't rated".
   - **Current state:** staged as S4-T1 in `build/agent7/s4-t1/`, with values 1/2/3:
     - 1 = ABOVE_NORMAL priority on the chain threads;
     - 2 = EcoQoS opt-out;
     - 3 = both;
     - unset = no call.
   - **Agent 10's rating** (`build/agent10/t27/r21-s4t1.md` L5-9):
     - (a) the default-off test bed: SAFE;
     - (b) value 3 in F1/F3/W1/W8b: SAFE-IF 5 conditions, including the new F-CA;
     - (c) the MP4 restatement: ACCEPTED.
   - SESSION2 L3326 says "F-CA goes to the RESUME open items". RESUME has no F-CA.
   - **Still owed:** a build, the threaded-mode proofs and functional rows. It isn't committed.
5. **R:5, R:17, R:162 and R:211, formal read-outs "pending … due ~10:00": STALE.**
   - `build/agent8/readout/w-followup/W6.md` (06:39) and `W4c.md` (06:40) are in. The W9 and W5b read-outs aren't yet (06:44 listing).
   - **W6** (paired, 10 rounds, both passes):
     - median frame time **−10.3% [−13.6, −6.9]**, lower in 9 of 10 rounds;
     - fps **+18.0% [+14.1, +22.0]**;
     - CPU **−0.249 cores [−0.303, −0.195]** (W6.md L7, L82);
     - C1 = p2fc − p2f: −10.7% [−13.1, −8.3], 10 of 10 rounds (L12, L86).
     - The runner's −14% / +22% / −0.27 are pass-2 figures (L10). The pooled raw ratios are −12.8% and +21.8% (L82).
   - **W4c:**
     - B median **+2.6% [−1.2, +6.5]**, lower in 1 of 6 rounds;
     - fps **−1.7% [−4.9, +1.7]**;
     - CPU **+0.063 [−0.007, +0.133]** (W4c.md L7, L49);
     - W4b's hint was +6.4% fps (+15.1% without its run 6), and it did not repeat (L8).
   - So R:18 (−12 to −14%, fps +21-22%) and R:160 (+1.3%, fps −0.4%) are the runner's raw figures. The formal figures show a smaller gain for p2fc and a worse result for B.
6. **R:185-186 and R:211, Agent 6's logdiffs "to confirm": STALE (done, PASS).** Source: `build/agent6/wnight/RESULTS.md` (06:05); SESSION2 L3324 agrees.
   - 135 runs in the 7 night dirs, no FAIL (L7).
   - The only lines that appear in an arm and in no reference run are the switch proof lines (L17-20):
     - p2fc's 3 `C1 keep-watch:` lines;
     - the q arms' back-off init line;
     - d11p's precise-wait line.
   - W9 env and quantum proof: 42 of 42 runs (L21).
   - 0 STUCK-LOCK, 0 dumps (L13).
   - NOTEs:
     - 6 runs miss `Execution complete`, a benign exit race (L9);
     - W9 `0128-off-r2` hit the 3 s shutdown watchdog, the first sighting (L10).
7. **R:191 and R:211, finding 10's "f10a and f10b … running this morning": STALE.**
   - SESSION2 L3325: f10a and f10b PASS, with no hang (quiet host, untimed, devoff4b-bin).
   - The worst frame was 2.9 s against the 5 s detector. SESSION2 reads the earlier gate-B hang as "a starved host, with a small margin".
   - A second pair started at 06:32 and ends by 07:20 (`build/agent3/runs/20261123-063244-f10a2-m1-sfl-level` and `20261123-064014-f10b2-p2fc-level`). Its n=2 summary goes to Agents 6 and 11.
8. **R:215, the re-pin's "Still to run: step 4 …": STALE.**
   - `build/agent4/HANDOFF.md` L18: "boot check rpb0 PASS; matrix rpm4 PASS on every section 3(b) check. Agent 1 announces the pin."
   - The runs are `build/agent3/runs/rpb0-20261123-0617` and `rpm4-20261123-0620`. SESSION2 L3325 also says "rpm4 PASS".
   - Only step 5, Agent 1's announcement, is left. Until then the pin stays native4 (REPIN.md L55), so R:146 and the last sentence of R:215 are still true.
   - Wording: rpb0 is the 1-run boot check (REPIN.md L67) and rpm4 is the 4-run matrix (L78). R:215 calls both "the 4-run rpb0/rpm4 matrix".
9. **R:11, R:209 and R:299, per-agent HANDOFF.md: NOTE.**
   - At 06:44, only agents 2, 4, 6, 9, 10 and 12 had a `build/agent<N>/HANDOFF.md`. Agents 1, 3, 5, 7, 8 and 11 had none.
   - SESSION2 L3312 asked every agent for one. Re-check before the pause.
10. **R:212, "the SCRNSAVE fix, with its tests and reviews (Agents 8 and 10)": partly STALE.**
    - Agent 10's delta read is done and rated SAFE (`build/agent10/t27/scrnsave-delta.md`; SESSION2 L3326).
    - Agent 8's review and the tests weren't checked here (§8 is the parent's).
11. **R:5, "draft 1 (Nov 23, 06:40)": nit.** The file's mtime is 06:23:49.

**Smaller notes (not wrong):**
- **(a) W4b's d11t.** W4b also ran d11t (window 3's d11 bundle + `REX_TIMER_WAIT_BLOCKING=1`) on devoff2 (`bench/agent8/run/matrix-window4.json` L37, L42). RESUME leaves it out in R:88-89 ("W5 and W5b") and in R:139 ("devoff2: W4b and W4c d0").
- **(b) CTR and CG26.** R:93-94 and R:216 ("the CTR build (not built yet)", "CG26 … not run") are true. However, partial work exists in `build/agent2/ctr/` and `build/agent2/cg26/`, and REPIN.md L20 names the planned `devoff4b-ctr-bin` and `devoff4b-cg26-bin`.
- **(c) W4b's B fps.** R:155 "B: fps +6.0% (n = 3, Agent 8's interim read-out)" is right as attributed (S4-DRAFT L409). The runner summary and W4c.md L8 give +6.4%.
- **(d) Row 38's caveats.** R:87 cites caveats (a)-(f); S4-DRAFT row 38 (L259) lists (a)-(d) and (f), with no (e).
- **(e) W8a's length.** R:220 says ~33 min, as S4-DRAFT L404 does; PROPOSAL.md L78 says 27.4 min (runner 30).

## 2. Per section

### §0 header (R:1-12)
| R | claim | mark | source |
|---|---|---|---|
| 3 | paused on Monday, Nov 23, from ~13:00, for a few days to a week | OK | FINDINGS L6; SESSION2 L3297, L3308 (2026-11-23 is a Monday) |
| 5 | draft 1 (06:40), before the formal read-outs | STALE / nit | items 5 and 11 |
| 8-10, 12 | S4-DRAFT, FINDINGS, SESSION2, the fact sheet | OK | all exist; the fact sheet has 143 lines |
| 11 | `build/agent<N>/HANDOFF.md` | NOTE | item 9 |

### §1 (R:14-36)
| R | claim | mark | source |
|---|---|---|---|
| 16 | `perf/opt` on `mine` in both repos = S4a + S4b/S4c; new switches off | OK | `branch -vv`; fact sheet L11 |
| 17 | runner summaries; read-outs pending; gates: all 7 PASS | OK / STALE | NIGHT-RESULTS L15-27; item 5 |
| 18 | p2fc −12 to −14%, fps +21-22%, ~0.25 core | OK (runner) | summaries 0009 and 0313; formal −10.3% / +18.0% / −0.249 (item 5) |
| 20 | q500 0.70-0.79 core less | OK | summaries 0108 (1.72 vs 2.51) and 0401 (1.80 vs 2.50) |
| 21 | d11p ~0.2 core less | OK | summaries 0155 and 0451; SESSION2 L3295 |
| 22 | codegen B: no gain, drop | OK | summary 0239; W4c.md L7 |
| 23-28 | still open: the four leans, C1's default, the day launcher + SCRNSAVE, simde, the notes | OK, NOTE | FINDINGS L28; SESSION2 L3311, L3318; F-CA is missing (item 4) |
| 29-36 | next steps; a new PC needs new baselines | OK (plan) | §7; SESSION2 L3303 |

### §2 (R:38-114)
| R | claim | mark | source |
|---|---|---|---|
| 42 | both on `mine`, no force, 0 ahead / 0 behind | OK | `branch -vv`: game `b0bd3b4` and SDK `5350b1d` = `mine/perf/opt`; SESSION2 L3309 |
| 46 | `b0bd3b4` (05:40): CMakeLists, memory_watch.cpp, new gpu_wait_backoff.cpp, SDK pointer | OK | `show --stat`: 4 files (CMakeLists +22, memory_watch.cpp +6, gpu_wait_backoff.cpp +395, rexglue-sdk) |
| 46 | `5350b1d`: 13 files (C1 v3, M1, P2's counter, R1/R2 step 1, db16cyc_pause) | OK | `show --stat`: 13 files, +1027/−15; fact sheet L28 |
| 47 | S4a: `1bd322e` (#2, SDK pointer) / `3bb65bb` (#7 #8 #5 #38 #32) | OK | `show --stat`: 1bd322e = shaders.cpp + the SDK pointer; 3bb65bb = both shared_memory.cpp, xmemory.cpp, timer_queue.cpp, pipeline_cache.cpp |
| 48-49 | S3d `08933a7` (draw.cpp); S3 `001336f` / `c5fe668` | OK | `show --stat` |
| 50-51 | `a0bdaa7` / `90e7ccd`; before the sprint: `127e04b` / `2897c31` | OK | the parents of `a0bdaa7` and `90e7ccd` |
| 46-50 | the gitlinks match the table | OK | `b0bd3b4`→`5350b1d`, `1bd322e`→`3bb65bb`, `a0bdaa7`→`90e7ccd`, `001336f`→`c5fe668` |
| 53 | 16 files in HASHES.txt, all match | OK | HASHES.txt L2-17 (13 SDK + 3 game); COMMIT-CHECK L64 |
| 54 | COMMIT-CHECK PASS with 1 WARN | WRONG | item 1 |
| 55 | `main` `895a529` = `origin/main`; `toypad-ui` `516e631` | OK | `branch -vv` |
| 59-62 | S4a: #7 #8 #5 #38 off; #32 on, output-identical; #2 native, off | OK | S4-DRAFT L401; fact sheet L57; build/agent4/HANDOFF.md L17 |
| 63 | S4b + S4c built on Nov 22's evening, committed on Nov 23 | OK | MANIFESTs: devoff4b 20:49, native4b 22:40; SESSION2 L3309 |
| 64-70 | C1 v3 (switches, counter, native latch); P2's counter; M1; #18; the #20 macro; #26; #24's hooks (Xenos only, pass-through while unset) | OK | xmemory.cpp:55; graphics/shared_memory.cpp:43; REPIN.md L30-31, L81; gpu_wait_backoff.cpp:123 |
| 71 | #30: CMake option only, OFF; turning it on stops configure | OK | rexlego/CMakeLists.txt:159, :161-162; scene_walk_probe.cpp is absent |
| 73 | Agent 10: SAFE to build (compose check, 19:47) | OK | S4-DRAFT L411; `build/agent2/s4b-compose-1932-c1v3.txt` exists; the "landing off" wording is UNVERIFIED |
| 81-82 | P2 `shared_memory_single_hold_rearm`, fix (i) `physical_protect_hold_global_lock`: cvars, false | OK | graphics/shared_memory.cpp:34; xmemory.cpp:46; arms: fact sheet L101 |
| 83-84 | C1 keep-watch (kInitOnly, needs #5) / verify (kRequiresRestart) | OK | xmemory.cpp:55; graphics/shared_memory.cpp:43; fact sheet L46-54 |
| 85-86 | #24 env: unset / 0 / Q (max 2000), spin 30 (max 200); stats env; W9 q0-q500 | OK | gpu_wait_backoff.cpp:123, :125, :129; fact sheet L64-65, L102 |
| 87 | #38 `timer_queue_precise_wait`: false, kInitOnly; W5/W5b d11p | OK | timer_queue.cpp:31; S4-DRAFT L259 (note d) |
| 88-89 | the timer bundle; `REX_TIMER_WAIT_BLOCKING` presence-only; "W5 and W5b" | OK, NOTE | fact sheet L103; timer_queue.cpp:59; W4b's d11t is missing (note a) |
| 90-91 | #7 hash log, #11 non-temporal copy: cvars, false | OK | d3d12/shared_memory.cpp:40, :50 |
| 92 | #18 `d3d12_submit_split_kb`: 0, kInitOnly; W7 | OK | d3d12/command_processor.cpp:109; S4-DRAFT L403 |
| 93 | #20 macro: 0; the CTR build isn't built | OK, NOTE | deferred_command_list.cpp:27; note b |
| 94 | #26 `db16cyc_pause` via the toml: false, needs a regen | OK | codegen/config.cpp:129-130; fact sheet L56; the toml has no db16 line today; REPIN.md L36 |
| 95-96 | #30 option OFF; #2 env unset = off, moot if #1 lands | OK | CMakeLists.txt:159; fact sheet L63; S4-DRAFT L201 |
| 98-103 | the always-on items; `pause_safe_order` and `audio_shutdown_detach_worker` default on | OK | rex_app.cpp:71; audio_system.cpp:48 |
| 105 | #19 `d3d12_async_submit`, a design | OK | S4-DRAFT L223 (cvar OFF, not rated) |
| 106 | #21 =1, proposed | STALE | item 4 |
| 107 | #33: the placeholder `d3d12_async_pipeline_no_wait` | OK | S4-DRAFT L249; Agent 6's proposal: SESSION2 L3196 |
| 111-114 | third-party trees and notes not committed; the user decides; the export in build/agent1/perf-export/ | OK | FINDINGS L8; SESSION2 L3310-3311, L3327 |

### §3 (R:116-133)
| R | claim | mark | source |
|---|---|---|---|
| 119 | the SDK is a standalone clone, not an initialized submodule | OK | the SDK's `.git` is a directory; `DimensionsRecomp/.git/modules/rexglue-sdk` is absent |
| 120 | `.gitmodules` lacks FidelityFX-SDK and snapdragon-gsr; `submodule status` fails | OK | 23 path entries, 0 hits; fact sheet L9 (status not re-run here) |
| 121-123 | gitlink `ceaeeee` absent locally; pin `e0c8871`; prepare_plume.py + `--check` | OK | `rev-parse --verify` fails; prepare_plume.py L9; plume HEAD `e0c8871` |
| 124 | 7 plume patches; winsdk-compat (S1 + p2) for SDK 10.0.22621 | OK | 7 `plume-*.patch` (+3 xenosrecomp); patch L9; SESSION2 L3310 |
| 125-127 | prepare_simde.py; pin `71fd833` = the SDK's gitlink; the m64 patch; question 2 open | OK | prepare_simde.py L9, L63; FINDINGS L28 |
| 128-130 | `core.autocrlf=true` in both; 271 inputs, including the CRLF files | OK | `config --get`; REPIN.md L30-31, L37 |
| 131 | Release; game x86-64-v3, SDK x86-64-v2; a MANIFEST per bin | OK | the MANIFEST headers |
| 133 | both `--check` runs passed, 06:01-06:04 | OK | fact sheet L15, L76-77 |

### §4 (R:135-147)
| R | bin | mark | source |
|---|---|---|---|
| 139 | devoff2: S2; W4b/W4c d0 | OK, NOTE | MANIFEST B87DC2D2 (11-21 23:18); matrix-window4.json L29; also W4b's d11t (L37) |
| 140 | devoffB: codegen B, from S2 | OK | MANIFEST 8709476F; matrix-window4.json L31 |
| 141 | devoff3: S3; W4b d3, W5 base | OK | MANIFEST B9C5175D; matrix-window4.json L33; summary 20261122-1756 |
| 142 | devoff4: S4a; the W5 arms, W5b | OK | MANIFEST 16DCC939; build/agent6/wnight/RESULTS.md L38 |
| 143 | devoff4b: S4b + S4c; W6, W9 | OK | MANIFEST DE11A914 (20:49); the night summaries |
| 144-147 | native3d `335ff2d4…`; native4 `5e3ff55d…` (the current pin); native4b `9b40acbb…` (22:40, not pinned); nativeB `81d1c3a7…` | OK | REPIN.md L3, L16-19; pin-native4b-2243.txt L34; the MANIFESTs; fact sheet L92-95 |

### §5 (R:149-179)
| R | claim | mark | source |
|---|---|---|---|
| 155 | W4b: 17 runs; ±19.6%; d11t 2.91 vs 3.44 cores (−15%); B fps +6.0% | OK | summary 20261122-1541 L4; S4-DRAFT L409; note c |
| 156 | W5: 16 runs; ±20.4%; d11t/d11p ~0.4 core (~13%) less | OK | summary 20261122-1756 L4 (2.74 / 2.75 vs 3.17) |
| 157 | W6: 21 runs each; −11.8% [−14%]; fps +21% [+22%]; 0.22 [0.27] core | OK (runner) | summaries; NIGHT-RESULTS L44; W6.md L10 |
| 157 | faster in 10 of 10 rounds | WRONG | item 2 |
| 157 | p99 5.04 vs 5.00; p99.9 6.49 vs 5.74; p2f p99.9 6.40, one frame over 33 ms | OK | summary 0313; SESSION2 L3272 |
| 158 | W9: 21 runs each; q500 0.79 [0.70] core (−31% [−28%]); fps +1%; p99 4.62 [4.68] vs 4.98 [4.99]; q125/q250 unsteady in pass 2 | OK, NOTE | summaries 0108/0401; NIGHT-RESULTS L45, L49; SESSION2 L3283-3286; add Agent 9's clock check (§4, item 4 below) |
| 159 | W5b: 19 runs each; d11p 0.20 [0.21] core (−8%); fps unchanged; d11t −0.8% fps in pass 2 | OK | summaries 0155/0451; NIGHT-RESULTS L46; SESSION2 L3291-3296 |
| 160 | W4c: 13 runs; +1.3%, fps −0.4%, +0.07 core; slower in 5 of 6; no second pass | OK (runner) | summary 0239; W4c.md L49; NIGHT-RESULTS L47; SESSION2 L3298; the formal figures are in item 5 |
| 162 | read-outs pending | STALE | item 5 |
| 164-170 | 7 PASS; exit 0; 0 FAIL / 0 NEW; STRICT, Defender 0.00; no leftover process; G8's raw FAIL = the finding-10 dump waived at 22:25; flagged runs p2fc r2, q125 r1/r3 | OK | NIGHT-RESULTS L15-27, L39, L44, L49, L64-67, L79, L83-84 |
| 173-175 | Windows Update; the Defender exclusion at ~23:16; the power overlay | OK | S4-DRAFT L385-387, L416; FINDINGS L28; NIGHT-RESULTS L73-77; SESSION2 L3323 |
| 176-178 | slow state = E-cores under 800 MHz; every scored W5 run; no night run (G10) | OK | S4-DRAFT L501; NIGHT-RESULTS L52-53; bench/agent8/run/matrix_recheck.py L112-117, L203 |
| 179 | cold round 1 widened s0's band to ±21.4%; pass 2 rated p2fc FASTER | OK | summaries 0009 and 0313 |

### §6 (R:181-200)
| R | claim | mark | source |
|---|---|---|---|
| 183-184, 187 | keep/drop after the read-outs and a confirmation window; p2fc's p99.9; drop B, B4 deferred | OK (plan) | S4-DRAFT L401, L411 |
| 185-186 | confirm q500 and d11p with Agent 6's logdiffs | STALE | item 6 |
| 188-190 | C1's default needs s4bLV and s4bV0; row 7's F 92 | OK | S4-DRAFT L51; SESSION2 L3110, L2967 |
| 191 | the finding-10 rows are running | STALE | item 7 |
| 192-193 | simde open; the notes: the user decides | OK | FINDINGS L28; SESSION2 L3311 |
| 194-200 | items 6 and 7 | skipped (parent) | |

### §7 (R:202-239)
| R | claim | mark | source |
|---|---|---|---|
| 204-209 | restart checks | OK (plan), NOTE | HANDOFFs: item 9 |
| 210-212 | leftovers | STALE | items 5-7 and 10 |
| 214 | s4bV0 and s4bLV | OK | S4-DRAFT L51 |
| 215 | re-pin steps 0-3 passed (0 FAIL, 0 WARN); step 4 still to run | OK / STALE | pin-native4b-2243.txt L54; item 8 |
| 216 | the CTR and CG26 builds | OK, NOTE | note b |
| 217-219 | W7/#19: the design isn't rated; staging, rating, build, soak; 17 runs, ~43 min; #18 alone should tie | OK | S4-DRAFT L223, L403 |
| 220 | W8a's arms; 13 runs; needs the native4b pin; W8a4 is the fallback | WRONG (arms) / OK | item 3; PROPOSAL.md L77-79 |
| 221-223 | #21 unrated; W8b: n0 / best threaded / threaded + #21, 13 runs, ~33 min, busy < 0.97 | STALE (#21) / OK | item 4; S4-DRAFT L405; the parked T1-T13 plan: build/agent4/HANDOFF.md L20 |
| 224 | CG26 / W10: s0 / #26, 13 runs, ~33 min | OK | S4-DRAFT L407 |
| 225-227 | #33 opt-in, off by default; Agent 6 proposed it; #34 optional | OK | FINDINGS L28; SESSION2 L3196; S4-DRAFT L249-250 |
| 228-230 | the screenshot check: one hour at the visible desktop; `LEGO_GPU_SNAPSHOT_DIR`; Agent 4 stages the kit | OK, NOTE | FINDINGS L28; SESSION2 L3196-3199, L3312; the kit is ready (build/agent4/HANDOFF.md L19) |
| 231 | the confirmation window: kept switches against s0, two passes | UNVERIFIED | FINDINGS L30 says only "a confirmation window"; no hit in PROPOSAL.md; SESSION2 L2943 (the older plan) says "vs S3d" |
| 232-239 | keep/drop; the defaults to flip; the back-off is env-only and needs a default in code or config | OK (plan), NOTE | gpu_wait_backoff.cpp:123 (getenv only); Agent 9's design `build/agent9/BACKOFF-DEFAULT-ON.md` isn't cited |

### §9 (R:260-284)
| R | claim | mark | source |
|---|---|---|---|
| 263-264 | i7-1255U, 15 W, 2 P + 8 E, 12 logical; P-cores at 1.92-1.95 GHz in W5; MX570 | OK | fact sheet L124; SESSION2 L2685; S4-DRAFT L34 |
| 266 | "a new PC needs new baselines" (SESSION2 L3303) | OK | SESSION2 L3303 |
| 268 | the matrices hard-code bin paths; the GO lines pin the matrix sha256 | OK | matrix-window4.json L29-37; PROPOSAL.md L78-79 |
| 268 | … and MANIFEST hashes | NOTE (partly backed) | matrix-window6.json L20 records the bin's exe sha256 in a note, and L27 accepts only `build/agent2/<name>-bin` bins that have a MANIFEST.txt; no MANIFEST-hash field found |
| 270 | the cold run and at least 3 rounds | UNVERIFIED | advice; no source |
| 271-272 | new noise bands; re-run W6, W9 and W5b | OK (plan) | |
| 273 | a fingerprint carries over only with 271 identical inputs; REPIN.md; dry run by default; re-record the PSO/seed caches | OK | REPIN.md L8, L37-38; fact sheet L122-123 |
| 275-281 | the host values (quiet list, 6 GB gates, slow-state rule, P/E classes, NVML, launcher times, SDK workaround) | OK | fact sheet L126-141; see the note below this table |
| 283 | run-day.ps1 repeats them | skipped (day launcher) | |
| 284 | host settings; -j8/-j10 Below Normal; S4-DRAFT §3's build times | OK | S4-DRAFT L411, L419-431; NIGHT-RESULTS L73-77 |

On R:277, "a CPU without E-cores never trips it": this fits matrix_recheck.py L113-114, which skips rows without `e_eff_mhz`, provided the sampler leaves that column empty on such a CPU.

### §10 (R:286-299)
- Every listed path exists (checked 06:39-06:51).
- NOTE: W8a's matrix is in `build/agent8/w-followup/` (item 3), and 6 HANDOFFs are missing (item 9).
- Paths a restart needs that §10 lacks:
  - `build/agent6/wnight/RESULTS.md`;
  - `build/agent9/BACKOFF-DEFAULT-ON.md` and `build/agent9/HANDOFF.md`;
  - `build/agent7/s4-t1/` and `build/agent10/t27/r21-s4t1.md`;
  - `build/agent2/ctr/` and `build/agent2/cg26/`;
  - `build/agent4/screenshot-kit/README.md`;
  - `build/agent3/runs/` (f10, rpb0, rpm4).

## 3. Public-safety scan of RESUME.md

- **Grep: 0 hits.** Patterns: drive-letter paths, user-profile paths, the local account name, `@`, `http`, `github`, `mail`, `token`, words starting with `key`, `passw`, `secret`, `DESKTOP-`/`LAPTOP-`, `.local` and IPv4 patterns.
- **Left in, all generic:**
  - `HKCU\Control Panel\Desktop` (R:249, §8);
  - "its disk check on C:" (R:280; a drive letter only);
  - the CPU and GPU models (R:263-264);
  - Windows SDK 10.0.22621.
- **Schedule:** R:3 gives the pause dates (allowed). Two mild mentions: R:228 "a one-hour slot at the visible desktop" and R:245 "double-clicks it and leaves the PC". Nothing else is personal.
- **No remote URL or account name:** R:16 and R:42 say only "the remote `mine`". The account URLs are in SESSION2 L3297 and L3308, and export_perf.py scrubs the account name (SESSION2 L3327).

## 4. What a restart in a week needs that RESUME lacks

1. **F-CA** in the open items (SESSION2 L3326), plus #21's actual state (item 4).
2. **The formal read-outs:**
   - the W6 and W4c numbers (item 5);
   - W6's guard (a) warning on the light share (W6.md L108);
   - the W9 and W5b read-outs, still to come in `build/agent8/readout/w-followup/`.
3. **Agent 6's night logdiffs** (item 6), with the two NOTEs to watch: the `Execution complete` race and the first 3 s shutdown watchdog (W9 `0128-off-r2`).
4. **Agent 9's notes** (`build/agent9/HANDOFF.md`, `BACKOFF-DEFAULT-ON.md`):
   - **The default design:** a design for making q500 a default, which §7 step 11 needs.
   - **W9 pass 2 had 4 "lowclk" runs**, 04:07-04:25, flagged because the effective clock was at least 100 MHz below the arm median (1853-1947 against ~2170-2205 MHz): q125 r1, q250 r1, q500 r2 and q125 r3 (HANDOFF L157-176).
     - They are read as host-driven, not proven (SESSION2 L3323).
     - They explain R:158's "unsteady". This isn't the slow-state rule, so R:178 stands.
   - **Still open:** one untimed Q = 500 run with stats must show `sleep_fail == 0` (HANDOFF L152-154).
5. **Finding 10:** f10a and f10b PASS; add the f10a2/f10b2 result when it lands (item 7).
6. **The re-pin:** step 4 PASS, and only Agent 1's announcement is left. After that come the `$PINS` line and the pack-state keying (REPIN.md L53; build/agent4/HANDOFF.md, open item 3).
7. **CTR and CG26:** the partial state in `build/agent2/ctr/` and `build/agent2/cg26/` (note b).
8. **The six missing HANDOFFs** (item 9).
9. **Git on a fresh clone:**
   - how to get the `mine` remote back (`git remote -v` in both repos; keep the account name out of public notes);
   - SESSION2 L3300 plans to "commit again at the end of the grace period". If that happens, the hashes in §2 move on from `b0bd3b4`/`5350b1d`.
10. **The export:** `export_perf.py`'s scrubbing and the ~47 files that mention the personal schedule (SESSION2 L3327) belong to the "where the notes go" decision.
11. **Agent 4's items:** the screenshot kit is ready, and the threaded-modes plan for W8b is parked (build/agent4/HANDOFF.md L19-20; `bench/agent4/matrix-native-threaded.json`).
12. **FYI for the parent's §6.6 and §8:**
    - Agent 10's SCRNSAVE delta read is SAFE.
    - Day condition 1 is met in staged form: run-day B67EBD6C was generated from run-night 565D30D4 (SESSION2 L3326).

**Counts:**
- WRONG: 3 (items 1-3).
- STALE: 6 (items 4-8 and 10), plus 1 nit (item 11).
- NOTE: 1 (item 9), plus 5 smaller notes and R:268's MANIFEST part, which is only partly backed.
- UNVERIFIED: 3 (the R:73 wording, R:231, R:270).
