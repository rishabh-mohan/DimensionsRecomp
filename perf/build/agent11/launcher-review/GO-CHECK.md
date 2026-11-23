# Overnight GO lines vs the arm rules (Agent 11, 22:45, task #10)

This answers Agent 1's request (SESSION2 L3071, re-sent at 22:44): check W9, W5b and W4c (and W6 again) against arm rules (1)-(5).

**Method:** [static7.ps1](static7.ps1) is read-only. Output: [static7-out-2241.txt](static7-out-2241.txt), run at 22:41:55 against launcher run-night.ps1 16B90FA8. It replicates three launcher functions:

- `Parse-Go` (L225-243);
- `Test-Matrix` (L253-299): every arm in the file, plus each only= id;
- `Get-MatrixWarnings` (L322-327).

It also does four extra checks:

- hashes each bin's MANIFEST.txt;
- scans every arm for C1 switches (`physical_protect_keep_watch*`);
- compares each only= arm with the arm of the same id in the matrix that cleared it. For W5 that is `matrix-window5-s3d.json` 4D7D689B. For W4b it is `matrix-window4.json` 6CA4AC6E, the file RUN-WINDOW4B.cmd ran;
- checks the timed runs per arm. The launcher passes `-Repeats <n> -ColdShared` (Get-RunnerArgs L303), and run-matrix.ps1 L230 lets `-Repeats` override each arm's own `repeats`. So each only= arm gets exactly n timed runs. Agent 8's -PlanOnly counts agree (stage-W6/W9/W5b/W4c-2240xx/2241xx: 21/21/19/13 runs).

I ran no -PlanOnly myself.

| Window | GO (sha8, only=, repeats) | (1) C1 | (2) timed runs per arm | (3) baseline | (4) cvars/env vs purpose | (5) promoted copy | Verdict |
|---|---|---|---|---|---|---|---|
| W6 | E50D791B s0,p2,p2f,p2fc r5 | Only p2fc uses C1, and it has P2 + fix (i). f and fc (C1 without P2) are in the file but not in only= | 5 (21 runs) | s0 (ref) | p2 adds P2; p2f adds fix (i); p2fc adds C1 v3 with verify=false. One bin: devoff4b DE11A914079D7DF7 | bench/agent8/run, created 21:56:37, = GO | **OK** |
| W9 | CE0AD757 off,q0,q125,q250,q500 r4 | none | 4 (21 runs) | off (ref; no LEGO_GPU_WAIT_* key) | Each q&lt;Q&gt; sets BACKOFF_US=&lt;Q&gt; (matches its id) and SPIN_US=30, with no STATS key. cvars: framerate_limit=0 only. Bin: devoff4b DE11A914079D7DF7 | created 22:41:29, = GO | **OK** for the arms; the GO waits for s4b17's PASS (s4b17 started 22:31:04) |
| W5b | 23575AAA d11,d11t,d11p r6 | none | 6 (19 runs) | d11 (ref) | All 3 arms have the 8 timer cvars + framerate_limit=0. d11t adds only REX_TIMER_WAIT_BLOCKING=1. d11p adds only timer_queue_precise_wait=true (no blocking key). Bin, env, cvars, frames and driver are identical to W5's arms. Bin: devoff4 16DCC9399239E577 | created 22:40:55, = GO | **OK** |
| W4c | E2E3E4DA d0,B r6 | none | 6 (13 runs) | d0 (ref) | Both arms: framerate_limit=0, no env. They differ only by bin: devoff2 B87DC2D2CA22379F vs devoffB 8709476FF4778768. Identical to W4b's d0 and B except group, note and repeats | created 22:40:59, = GO | **OK** |

**Notes:**

- **Launcher rules:** every arm of all 4 files passes:
  - bins in build/agent2, each with MANIFEST.txt and legodimensions.exe;
  - env keys only from the 11 allowed;
  - driver `drivers/thread-cpu.ps1`;
  - no menu, profile, triggers, toml or seed_cache;
  - `sys_csv` true.

  As a sanity check, the replica refuses Agent 8's negative test (`neg/matrix-window4c-negenv.json`: arm B, env LEGO_BOGUS_KEY).
- **Extra promoted files:**
  - `matrix-window8a4.json` is also in bench/agent8/run (created 22:37:04), but W8a4 isn't in tonight's order, so no GO should name it.
  - W9's copy went in before s4b17's verdict. That is harmless, since a file starts nothing, but W9's GO must wait for s4b17's PASS.
- **Changes after this check:** a promoted file that changes gets a new sha, and the launcher then refuses its GO (Test-Matrix L258). Re-run static7 if any draft changes.
