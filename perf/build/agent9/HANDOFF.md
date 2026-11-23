# Agent 9 handoff (task #30)

Written 2026-11-23, about 06:05, before the break. All paths are relative to the workspace root.
Line numbers were checked 05:58-06:05 on 11-23. perf-notes/S4-DRAFT.md and perf-notes/SESSION2.md were
still being edited at that time. If their line numbers have moved, find the item by its heading or row number.

## 1. Status

- All my tasks are done. Nothing of mine is running: no jobs, subagents, timers or staged windows.
- I own only `build/agent9/**`. My working notes are in `perf-notes/agent9-codegen.md`, and only I edit it.
- Agent 1 committed and pushed the S4b/S4c code I drafted at 05:44 (perf-notes/SESSION2.md:3306-3312):
  - DimensionsRecomp `perf/opt` **b0bd3b4**, "S4b/S4c: keep-watch memory_watch, GPU wait back-off hooks, probe
    option; SDK at S4b";
  - rexglue-sdk **5350b1d**, "S4b: C1 v3 keep-watch, M1 non-temporal copy, P2 counter, r1r2, db16cyc_pause
    option".
- Notes, scripts and results (perf-notes/, build/, bench/) are not pushed. Exporting them is the user's call.
- None of my items needs the user.
- On resume, read `perf-notes/RESUME.md` first, once Agent 11 has written it (it did not exist at 06:00).

## 2. What I own

Never list `build/agent9` recursively; a recursive listing hung once. List one folder at a time.

| Path (under build/agent9/) | Contents | State |
|---|---|---|
| `s4/fence-wait/` | #24 GPU-wait back-off: design and drafts. `s4c/PACKAGE.md` is the S4c package (files, apply steps, map gate, before-ON steps 1-4) | landed in b0bd3b4, default OFF |
| `s4/spin/db16cyc-pause/` | #26 toml diffs A and B | SDK option landed; OFF in every build |
| `s4/scene-walk/` | #30 static analysis (`REPORT.md`) | CMake option landed; probe sources not written |
| `s4/fe-gate/` | #41 front-end gate notes | parked |
| `cg26-check/` | Task #18 check kit for Agent 2's CG26 bin (`cg26_check.py`, `README.md`, tests) | ready, 14/14 self-tests; CG26 not built |
| `s4-t1-preread.md`, `s4-t1-preread-cites.ps1` | Task #18 item 3: independent pre-read of #21 (S4-T1) for Agent 10 | done, 4/4 PASS |
| `android/` | Task #8 working files; the report is `perf-notes/ANDROID-FEASIBILITY.md` | done |
| `handoff/` | This task: `w9_clock_check.ps1` (read-only) and its output `w9-clock-check.txt` | done |
| `HANDOFF.md`, `BACKOFF-DEFAULT-ON.md` | This file; the default-ON design note | done |
| `asmcheck/`, `b-clock/`, `bin/`, `configs/`, `diff/`, `generated/`, `install/`, `logs/`, `ppctests/`, `prof/`, `regress/`, `repin/`, `review/`, `scratch/`, `tool/`, top-level `*.py` / `*.ps1` | Codegen work from sessions 1-2, documented in perf-notes/agent9-codegen.md | nothing pending |

## 3. S4c state: #24 back-off and #30 probe option

S4c is the back-off TU and two CMake blocks, on top of S4b. It is in b0bd3b4 and in Agent 2's
`build/agent2/devoff4b-bin` (S4b + S4c). That bin was staged on 11-22 at 20:49 (MANIFEST DE11A914079D7DF7, exe
DFBE1D43B28861A6). Its map check PASSes with 31 hooked aliases by name + object
(perf-notes/agent2-baseline.md:40-44).

### #24 GPU-wait back-off (stage 1)

- **CMake:** `DimensionsRecomp/rexlego/CMakeLists.txt:181-188` covers Xenos builds only
  (`if(NOT LEGODIMENSIONS_NATIVE_GPU)` at :184). It adds `src/gpu_wait_backoff.cpp` with
  `LEGO_GPU_WAIT_HOOK_GETDATA=1` (:185-187).
- **TU:** `DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp`, 395 lines. The hooks pass calls through:
  - H0 sub_83FBF7D0;
  - H1 sub_83FAF180, the L1 fence-wait poll;
  - H2 sub_83FB09E8 and H3 sub_83FC0C10, the GetData poll. These two are built only under GETDATA.

  They never write guest memory or registers. Only poll timing changes (:14-15).
- **Switches** (:17-25). `Cfg()` reads them once, at the first hooked call (:119-149):
  - `LEGO_GPU_WAIT_BACKOFF_US` sets Q.
    - Unset or empty: OFF. Every hook calls the original at once.
    - 0: spin, then yield on every later poll (Agent 6's (e)).
    - Q > 0: spin, one SwitchToThread, then a Q us sleep per poll. The maximum is 2000.
  - `LEGO_GPU_WAIT_SPIN_US` sets S: default 30, maximum 200.
  - `LEGO_GPU_WAIT_STATS=1` turns on the P1 counters, one log line per 5 s. It is for profiling only and never
    goes in a timed arm.
  - Values are digits only (ParseUs :110-117), and a larger value clamps to the maximum. Anything else logs a
    WARN and is ignored: Q stays OFF and S stays 30 (:134-140).
  - The init line prints only when the back-off or stats is ON (:141-145). So an OFF run has no back-off line;
    Agent 6's expect rule relies on that (perf-notes/agent6-attract-stalls.md:829).
- **Default OFF.** Agent 10 rated landing it OFF as SAFE in b2r S37
  (perf-notes/agent10-batch2-review.md L2011; earlier reviews: S26 L1368, S32 L1758).
- **Gate runs** (perf-notes/agent3-run-harness.md):
  - s4b17, the P1 stats run: PASS (:971).
  - s4b18, Q = 250 with stats: PASS, sleep_fail 0 (:928-930).
  - s4b24, a W6 C1 gate run: a recovered finding-10 hang, with the owner inside sub_83FAF180, the poll that H1
    hooks (:923-927). That is a known hang site, not a back-off result. W9's 42 runs had 0 STUCK-LOCK (section 4).
- **Test order** (perf-notes/agent9-codegen.md S5.2.4, L358-388):
  - step 0: static checks;
  - step 1: P1;
  - step 2: the functional Q = 250 run;
  - step 3: the sweep (that is W9);
  - step 4: Agent 6's loaded-machine arm. **Not done.**
  - step 5: stage 2, only if needed.

### #30 scene-walk probe option

- **Only the CMake part exists:** `DimensionsRecomp/rexlego/CMakeLists.txt:156-167`, with
  `option(LEGODIMENSIONS_SCENE_WALK_PROBE ... OFF)` at :159.
  - ON needs `src/scene_walk_probe.cpp`. If the file is missing, configure stops with FATAL_ERROR (:161-162).
  - ON adds the define to native_memops.cpp and native_skin_diagnostics.cpp (:165-166).
  - A normal build has no probe hooks.
- **Not written:** the probe sources and the `#ifdef` hooks.
  - Spec: perf-notes/agent9-codegen.md S4.2.4 (L747).
  - Background: build/agent9/s4/scene-walk/REPORT.md, a static analysis. The walk is the UI/HUD render.
  - Row: perf-notes/S4-DRAFT.md row 30 (L241 at 06:00), owned by A9 with A7.
  - Only worth doing if the scene-walk question is still open after the break.

## 4. What W9 means

W9 ran the 21-run matrix `bench/agent8/run/matrix-window9.json` twice on devoff4b-bin. Every Q arm used S = 30.
Both passes were 21/21 OK with gate STRICT.
- Pass 1: `build/agent8/matrix/20261123-0108` (01:08-01:51).
- Pass 2: `build/agent8/matrix/20261123-0401` (04:01-04:44).

The table shows the runner summaries as median frame ms / fps / CPU cores (perf-notes/SESSION2.md:3232-3239
and 3276-3287). It is not the formal readout.

| Arm | Pass 1 | Pass 2 | Pass 2 vs off |
|---|---|---|---|
| off | 2.46 / 386 / 2.51 | 2.46 / 384.9 / 2.50 | reference |
| q0 | 2.48 / 387 / 2.49 | 2.47 / 385.5 / 2.47 | no change |
| q125 | 2.31 / 389 / 1.82 | 2.39 / 378.9 / 1.96 | -0.54 core, fps -1.6 % |
| q250 | 2.31 / 389 / 1.77 | 2.37 / 382.8 / 1.95 | -0.55 core, fps -0.5 % |
| q500 | 2.31 / 390 / 1.72 | 2.32 / 389.2 / 1.80 | -0.70 core (-28 %), fps +1.1 %, median -5.9 % |

Tails, p99 / p99.9 in ms:
- pass 1: q125 4.47 / 5.01, q250 4.50 / 5.11, q500 4.62 / 5.52, off 4.98 / 5.63;
- pass 2: q500 4.68 / 5.40, off 4.99 / 5.58.

What it means:
- The back-off saves CPU, not frame time: 0.54-0.79 core less, with no fps loss.
- **q500 (`LEGO_GPU_WAIT_BACKOFF_US=500`) looks best:**
  - It saves the most CPU in both passes: -0.79 core in pass 1, -0.70 in pass 2.
  - It loses no fps (+1.1 % in pass 2) and had the best tail in pass 2. In pass 1, q125/q250 had the better tail.
  - Agent 1 leans q500 (SESSION2.md:3287).
- q0 (yield only, no sleep) makes no measurable difference.
- **Logdiff:** Agent 6's results are in `build/agent6/wnight/out-W9-20261123-0108/w6-summary.txt` and
  `build/agent6/wnight/out-W9-20261123-0401/w6-summary.txt`.
  - Every q arm PASSes in both passes.
  - Each q run has exactly one back-off init line, and the off runs have none. That init line is the only new
    log key compared with off.
  - STUCK-LOCK 0, no dumps.
  - The off arm is NOTE in both passes. In each pass, one off run's log does not end with the clean-exit lines:
    0128-off-r2 ("Shutdown wedged past the close request") and 0429-off-r3. The back-off was unset in those
    runs, so #24 is not involved.
- **Formal readout:** Agents 7 and 8 pool the 8 runs per arm. It was still in progress at 06:00
  (`build/agent7/readout/`, `build/agent8/readout/w-followup/`). Its Q pick overrides this section.
- The default stays OFF. A design for turning it on by default is in `build/agent9/BACKOFF-DEFAULT-ON.md`.

## 5. Open questions

1. **Spin length S.**
   - s4b17 (P1 with stats, back-off OFF) saw 21,926 L1 waits, and their lengths are bimodal:
     - 32 % are under 50 us and 66 % are 4 ms or longer;
     - only 51 fall between 50 us and 1 ms;
     - total 314.5 s of waiting in 405 s, maximum 663 ms.

     Source: the side note at perf-notes/agent9-codegen.md L2464-2478.
   - S = 30 sits on the short mode. S = 50 would cover all of it for about 0.3 s more spin per 405 s.
   - Q is 0.3-1.2 % of a mean long wait (about 21.6 ms).
   - The run was taken during a -j 8 build, so its waits are inflated.
   - Next: stats runs at S = 30 and S = 50 on a quiet host or the new PC. Add a two-arm timed check only if the
     short mode has moved.
2. **Stats.**
   - Timed arms never run with stats, and s4b18 checked Q = 250 only, so sleep_fail at Q = 500 has never been
     observed.
   - Next: one functional (untimed) Q = 500 run with stats, which must show sleep_fail == 0.
   - Parsers must find fields by name, because sleep_sum comes before sleep_fail.
   - Keep the stats code. It is the only way to see the waits.
3. **The q125/q250 instability (pass 2 only).**
   - `build/agent9/handoff/w9-clock-check.txt` is the output of `w9_clock_check.ps1`, which is read-only. It
     reads each run's sys.csv and threads.csv and flags a run "lowclk" when its effective clock is 100 MHz or
     more below its arm's median in that pass.
   - Pass 1 has no lowclk runs. Pass 2 has 4, all between 04:07 and 04:25:
     - 04-q125-r1 (run dir 0407-q125-r1);
     - 05-q250-r1 (0409);
     - 10-q500-r2 (0419);
     - 12-q125-r3 (0423).
   - Those runs compared with the steady back-off runs:

     | Measure | Lowclk runs | Steady back-off runs |
     |---|---|---|
     | Effective clock | 1853-1947 MHz | about 2170-2205 MHz |
     | E-core utilisation | 47-54 % | about 34 % |
     | Main XThread busy | 75-79 % | about 65 % |
     | GPU Commands busy | 53-58 % | 46-48 % |

     The busy rise is about the clock ratio.
   - Frames: 18,250-18,909 in the bad q125/q250 runs, against 19,200-19,550 elsewhere. q500 r2 kept 19,291.
   - q250 r2 and r3 (04:17 and 04:25) also ran below the steady clock, at 2075 and 1996 MHz. They were not
     flagged because the q250 median is pulled down too.
   - The off run at 04:21 shows the same signs: the lowest off clock (1907 MHz) and 46 % E-core utilisation.
   - Most likely an intermittent host event loaded the E-cores and lowered the clocks.
     - The back-off arms show it because their CPU time follows the work.
     - The spinning arms (off, q0) are about 100 % busy while they wait, so they hide it.
     - Agent 1 saw CrossDeviceService at 0.68-0.87 core at 04:46-04:49 (SESSION2.md:3291).
     - This is not proven, because sys.csv has no per-process CPU.
   - So don't pick Q from those runs. Next:
     - add a per-process top-N CPU column to Agent 8's sys-csv driver (`bench/agent8/run/drivers/sys-csv.ps1`);
     - repeat the sweep on a quiet host.
4. **The loaded-machine arm** (S5.2.4 step 4, Agent 6) is not done. On a busy host, a sleeping waiter can wake
   late; this arm measures that cost. It is required before the back-off goes on by default.
5. **Measure #24 separately from #26.** Both change spin waits.
6. **Stage 2 (#25)**, waking on the GPU write (perf-notes/agent9-codegen.md S5.2.3, L343), is not needed now,
   because stage 1 costs no fps. It stays the fallback if the loaded arm shows slow frames.
7. **New PC.** All the numbers above come from this machine, which has P- and E-cores. On the new PC, take a
   new off baseline and run a small Q sweep (off, q250, q500, maybe q1000) before trusting any default.

## 6. #26 / CG26: db16cyc_pause

- **The SDK option landed in 5350b1d:**
  - the field `db16cycPause = false` is at `DimensionsRecomp/rexglue-sdk/include/rex/codegen/config.h:110`;
  - the toml key `db16cyc_pause` is merged at `DimensionsRecomp/rexglue-sdk/src/codegen/config.cpp:129-130`;
  - when it is set, build_db16cyc emits `simde_mm_pause()`
    (`DimensionsRecomp/rexglue-sdk/src/codegen/builders/system.cpp:51-56`).

  Agent 10 reviewed it in b2r S36 (perf-notes/agent10-batch2-review.md L1948).
- **OFF everywhere.** The live `DimensionsRecomp/rexlego/legodimensions_config.toml` has no db16cyc_pause line
  (checked 05:58). That toml is a native fingerprint input (CMakeLists.txt:610). So turning #26 on in the live
  tree means a native re-pin.
- **Toml diffs:** `build/agent9/s4/spin/db16cyc-pause/`.
  - Diff A is 95D901B9...; its new toml, 11707872..., is the one Agent 2 prepared.
  - Diff B is 5D5892D3....
  - Predicted ON output: 20 pauses in 10 TUs (perf-notes/agent9-codegen.md R2.17.5, L2149).
- **CG26 is not built.** That is Agent 2's ON bin, `build/agent2/devoff4b-cg26-bin`. It was queued after Agent
  3's L-route rows and CTR, and the break came first.
  - The recipe is at perf-notes/agent2-baseline.md:58-63, with tool 9145166C... and toml A.
  - To force the regen, delete cg26's `generated/default/codegen.stamp` or pass `--ignore-stamp`.
  - Touching the toml does not force a regen, because the fingerprint is computed from content
    (`DimensionsRecomp/rexglue-sdk/src/codegen/output_stamp.cpp:67-99`).
- **Check kit:** `build/agent9/cg26-check/`.
  - Run it with the command on README.md L12. Agent 2 plans `--out build/agent2/cg26/checks/kit18`; Agent 10 can
    write their own copy to build/agent10/cg26-check.
  - Exit codes: 0 PASS, 1 FAIL, 2 INCOMPLETE, 3 HELD. Self-tests: 14/14.
  - What it checks:
    - (a) the toml line and the new tool are in the same build;
    - (b) there are exactly 20 pauses in the arm's 10 TUs and none elsewhere;
    - (c) codegen.partition.json is unchanged;
    - (d) the MANIFEST hashes match.

    It also writes a diff summary per TU and site for Agent 10.
- **Gates before ON:**
  - the kit PASSes;
  - Agent 10's static gates (b2r S36) pass;
  - the functional pair passes;
  - a frame-time A/B, measured separately from #24.

  Fallback if 20 pauses cost frames: one PAUSE per db16cyc run.

## 7. Other finished work (nothing open)

- **#21 pre-read** (S4-T1, Agent 7's native worker priority change): `build/agent9/s4-t1-preread.md`, 4/4 PASS.
  It confirms four things:
  - the OFF path is unchanged;
  - the priority is set and then undone;
  - the change is native-only;
  - there are no new lock edges.

  Agent 7 applied my P1/P2 notes at 23:27 (build/agent7/s4-t1/README.md).
- **Android feasibility** (task #8): `perf-notes/ANDROID-FEASIBILITY.md`, with working files in
  `build/agent9/android/`.
- **#41 front-end gate:** perf-notes/agent9-codegen.md R2.11.4 (L2031) and R2.17.6 (L2172, the open items).
  Parked.

## 8. Resume checklist

1. Check `perf-notes/WINDOW-HOLD.txt` before every command. Read `perf-notes/RESUME.md` (Agent 11) and this file.
2. Read the formal W9 readout (Agents 7 and 8). If it confirms q500, the cheapest code step is step A of
   BACKOFF-DEFAULT-ON.md, which does not change behavior.
3. Before the back-off goes on by default, run these (section 8 of the design note):
   - the Q = 500 stats run (sleep_fail 0);
   - the loaded-machine arm;
   - the functional pair;
   - a two-pass timed confirmation.
4. A repeat on a quiet host, with per-process CPU in sys.csv, settles open question 3 and the spin question.
5. CG26: once Agent 2 builds it, run the kit (cg26-check/README.md), then Agent 10's static gates (b2r S36). Then
   run a functional pair and an A/B separately from #24.
6. #30: write the probe per S4.2.4 only if the scene-walk cost is still a question.
7. New PC: take new baselines before comparing with any number here.

## 9. Key files

| File | Why |
|---|---|
| `DimensionsRecomp/rexlego/src/gpu_wait_backoff.cpp` | #24 TU (switches :17-25, Cfg :119-149) |
| `DimensionsRecomp/rexlego/CMakeLists.txt` | #30 option :156-167, #24 block :181-188, native fingerprint inputs :604-625 and :753-761 |
| `build/agent9/s4/fence-wait/s4c/PACKAGE.md` | S4c package and the before-ON steps |
| `build/agent9/handoff/w9-clock-check.txt` | W9 per-run clock and E-core check |
| `build/agent9/cg26-check/README.md` | How to run the CG26 kit |
| `build/agent9/BACKOFF-DEFAULT-ON.md` | Default-ON design (a proposal) |
| `perf-notes/agent9-codegen.md` | S4.2.4 L747, S5.2.3 L343, S5.2.4 L358-388, R2.17.5 L2149, s4b17 note L2464-2478 |
| `perf-notes/agent10-batch2-review.md` | b2r S26 L1368, S32 L1758, S36 L1948, S37 L2011 |
| `perf-notes/agent3-run-harness.md` | Gate runs: s4b17 :971, s4b18 :928, s4b24 :923 |
| `perf-notes/agent2-baseline.md` | devoff4b-bin :40-44, CG26 recipe :58-63 |
| `perf-notes/S4-DRAFT.md` | Rows 24, 25, 26 and 30 (L235-241 at 06:00) |
| `build/agent8/matrix/20261123-0108/`, `build/agent8/matrix/20261123-0401/` | W9 run data (summary.md, results.csv, runs/) |
| `build/agent6/wnight/out-W9-20261123-0108/`, `build/agent6/wnight/out-W9-20261123-0401/` | W9 logdiffs |
