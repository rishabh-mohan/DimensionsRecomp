# Overnight plan after the queue (Agent 8, run-2 task #7 item 6), rev 22:35

Changes per Agent 1's 22:28 message:
- W8a and W8a4 move to a Monday daytime session (Section 5).
- The windows end by ~03:30-04:00.
- Section 3 explains how a hung or failed run is read.
- RUN-WINDOW6.cmd stays at `-Repeats 3`.

Definitions:
- **min** = Agent 7's formula 1.70 + 2.14·A·n (REPEATS.md).
- **runs** = 1 unscored cold run + A·n.
- **runner** = the run-matrix -PlanOnly estimate. The launcher's deadline check uses it: a GO is accepted only if now + runner + 10 min <= 07:30 and now < 06:45.
- **Quiet gate**: each window first waits for the launcher's quiet gate. That takes at least ~4 min, up to 30 min in the strict phase; I plan on 10 min.

## 1. Order, GO lines, what each still needs

| # | window | GO line (sha = draft sha = sha after -Promote, byte-for-byte copy) | A×n | runs | min | runner | latest GO for an end by 04:00 | still needs |
|---|---|---|---|---|---|---|---|---|
| 1 | **W6** | `GO W6 matrix-window6.json E50D791B6C38638F718A1AF65EB15EAF543A78AC8EA50B69DD1CC96AB7C9A0D2 only=s0,p2,p2f,p2fc repeats=5` | 4×5 | 21 | 44.5 (+ up to ~3 if p2fc closes are slow) | 48 | 03:00 | Nothing. Promoted 21:56; rechecked at repeats=5 at 22:09, OK ([stage-W6-220900.txt](../readout/w-followup/stage-W6-220900.txt)). |
| 2 | **W9** (gated) | `GO W9 matrix-window9.json CE0AD75792B47D59876C864B39797CD877404F911D12F92E6CC9C4351D747610 only=off,q0,q125,q250,q500 repeats=4` | 5×4 | 21 | 44.5 | 48 | 03:02 | s4b17 PASS: positive controls > 0. It runs after w6gB (~22:34). s4b18 already PASSed (Agent 1). Then `-Promote`. The staging test was OK at 22:14 ([stage-W9-221141.txt](../readout/w-followup/stage-W9-221141.txt)). |
| 3 | **W5b** | `GO W5b matrix-window5b.json 23575AAAE9DCBB85C9965AC8A3A8794916FFA881C09C656A6512C7EE462D5F76 only=d11,d11t,d11p repeats=6` | 3×6 | 19 | 40.2 | 44 | 03:06 | `-Promote` only. No functional rows: all three arms ran clean in W5 (devoff4, MANIFEST 16DCC9399239E577). |
| 4 | **W4c** | `GO W4c matrix-window4c.json E2E3E4DAAF7D30C7B8B2D28D21911E6EACDA5260963F9B99095EE70C09022396 only=d0,B repeats=6` | 2×6 | 13 | 27.4 | 30 | 03:20 | `-Promote` only. No functional rows: both arms ran clean in W4b (17/17, Agent 6's logdiff 0; devoff2 B87DC2D2CA22379F, devoffB 8709476FF4778768). |

Latest GO for an end by 04:00 = 04:00 − runner − 10 min gate.

Rules for the night:
- Take the windows in this order.
- If W9's gate has not passed when its turn comes, run W5b and W4c, then come back to W9 if it still fits by its latest GO.
- Write no GO after its latest-GO time. A window that does not fit goes to a Monday session.

## 2. Timeline (W6 GO at 00:05, 10-min gates)

| window | GO | start | end (formula) |
|---|---|---|---|
| W6 | 00:05 | ~00:15 | ~01:02 |
| W9 | ~01:02 | ~01:12 | ~01:57 |
| W5b | ~01:57 | ~02:07 | ~02:47 |
| W4c | ~02:47 | ~02:57 | **~03:24** |

- **All four:** 159.1 min of windows + ~40 min of gates.
  - If every window takes its runner estimate instead, the night ends ~03:35.
  - With 5-min gates (idle PC), it ends ~03:05.
- **Without W9** (gate not passed): W6 to 01:02, W5b 01:12-01:52, W4c 02:02-02:29.
- **Slow quiet gates:** if they push a window past its latest GO, the rule above drops the last window (W4c first), so the windows still end by ~04:00. Builds and tests can start after that.

## 3. How a hung or failed run is read

- **During the window:** run-matrix records a failed run and goes on with the next run in the same order.
  - A run fails only if it is KILLED after the 60 s WM_CLOSE timeout, is still running, or never had WM_CLOSE posted (run-timing.ps1 L609-611).
  - A slow close within 60 s is a clean close (L13-14) and does not touch the timing: `valid_timing` ignores the close (L639-647). Agent 1 saw closes up to 40 s under load, all OS teardown after the game's own exit.
- **Timing: the run is left out.**
  - Agent 7's readout.py keeps only scored runs with valid timing, not excluded, and with a scored frame window. It lists every run it leaves out, with the reason. So failed runs drop out by themselves.
  - A run that hung and recovered (a STUCK-LOCK line or hang dump, but exit 0 and valid timing) is left out too, with `--drop`, so its long frame does not enter the medians.
  - Every verdict is given with and without the flagged runs, as with W4b's run 6.
- **Counted per arm:** one table per window with, for each arm:
  - runs planned / timed / failed (exit code, KILLED);
  - STUCK-LOCK by owner site (Agent 6's kit);
  - hang dumps;
  - slow-state count (Agent 11's timerq_slowstate copy);
  - host CPU at each hang, from sys.csv (finding 10 is load-related).

  For W6: p2fc vs s0, plus p2 and p2f. Agent 12's run_gates.ps1 runs too; its G8 FAIL from gate A's recovered hang reads as WARN.
- **Too few runs:** an arm with fewer than 3 timed runs gets no timing verdict, only its counts. A hang in an arm but not in the ref is reported as a finding (count, owner lr, host load), not as timing.

## 4. What each window answers

- **W6:** the cost of P2 / P2f / P2fc vs s0 on devoff4b, at ±~2.9 % median ms. Plus the STUCK-LOCK and slow-state counts per arm (Section 3).
- **W9:** the #24 GPU-wait back-off sweep vs off: Q = 0/125/250/500 µs, spin 30 µs, no STATS. Precision ±3.2 % median ms (5 arms, n=4). Pick the largest CPU drop with no p99 or 1 % low loss beyond the spread.
- **W5b:** re-tests W5's d11t-vs-d11 lead at n=6 instead of 3. d11p comes along. Expected precision with 3 arms at n=6: about ±5.2 % on p99 and ±6.4 % on the 1 % low.
  - In W5, d11t's p99 was +8.2 % (CI [+0.5, +16.6]), a lead.
  - Its 1 % low was −7.7 %.
  - It used 13.7 % less game CPU.
- **W4c:** re-tests W4b's B-vs-d0 fps lead (+6.4 %, or +15.1 % without run 6; fragile) at n=6. Expected precision: about ±2.7 % median ms and ±2.3 % fps.

## 5. Monday and later (Agent 1, 22:28)

- **W8a** goes to a Monday daytime session, with W8b and W10. So does its fallback **W8a4**.
  - W8a: `GO W8a matrix-window8a.json A06E5E3AAEE25B079532DE8BFC9134D7462B5F842ECB9FADA19B6FD8DD8A475E only=n0,mc repeats=6`. 13 runs, 27.4 min, runner 30.
  - W8a4: `GO W8a4 matrix-window8a4.json 56BE00D8131981A735CC40142980316F9E834D0B51F103A143BA6105AA5DA1D1 only=n4,n4mc repeats=6`. Same size.
  - W8a still needs: native4b-bin with Agent 2's MANIFEST sha, Agent 4's re-pin, and PASS on rpb0/rpm4 and s4b02/s4b05.
  - W8a4 needs an OK to use native4's r6 PASS as its functional cover.
  - The drafts stay in build/agent8/w-followup. Re-stage them on the day; their shas only change if the drafts change.
- **W7:** Monday night at the earliest.

## 6. Caveats

- **Finding 10 is load-related, not C1** (Agent 3, Agent 1).
  - The same owner (lr 83FAF200 in sub_83FAF180) hit s4b24 (p2fc) and the C1-off row s4b20.
  - Both hits came while a -j 8 build had the host at 100 % CPU.
  - So nothing may compile during the windows. The launcher's quiet gate and valid_timing's build-process check catch a build at window start, not one that starts mid-window.
- **No C1:** no arm in these windows uses C1 (Agent 10's rule). W9's arms are env-only, with cvars `framerate_limit=0`.
- **Host state:** compare across windows (W6 s0, W9 off, W5) only under one host state (the power overlay, the 08:29 update). Otherwise compare within a window only.
- **Notes text:** each draft's notes give the repeats it was written for; W9's says repeats=3 (16 runs). The GO line's repeats is what runs.

## 7. Staging after you pick (by 23:45)

For each chosen window:

```
build\agent8\w-followup\stage-window.ps1 -Draft build\agent8\w-followup\matrix-window<X>.json -Id <X> -Only <arms> -Repeats <n> -Expect <bin>=<MANIFEST prefix>[,...] -Promote -VerifyFiles
```

What the script does:
1. It copies the draft byte for byte into `bench\agent8\run`. Matrix .json files are not pinned.
2. It runs the launcher's own functions read-only: Parse-Go, Test-Matrix, Get-MatrixWarnings, Get-BinHashes, and Get-Plan (run-matrix -PlanOnly). It starts -PlanOnly only while a queue game is running, or after the queue has closed (23:25).
3. It checks the planned runs and prints the GO line.
4. It writes `build\agent8\readout\w-followup\stage-<X>-<HHmmss>.txt` plus `inputs-<X>-<HHmmss>.txt`.

I send you the GO lines; I never write WINDOW-GO.txt.

Script tests ([tests-221054.txt](../readout/w-followup/tests-221054.txt)):
- 12/12 PASS: T1 W9 r4, T2 W5b r6 three arms, T3 W5b r6 two arms, T4 W4c, T5 W8a4, T6 W4cR (exit 0); the negative tests N1-N4 exit 1 and N5-N6 exit 2, as expected.

Status at 22:49: everything is promoted, and the final GO lines went to Agent 1 at ~22:47 (reports in `build\agent8\readout\w-followup\`; launcher 16B90FA8... of 22:11:21; -VerifyFiles; matrix folders 21/21 before and after each -PlanOnly):
- W6 r5: rechecked OK at 22:41:32 (`stage-W6-224132.txt`).
- W9 r4: s4b17 PASS (Agent 3, 22:41) and s4b18 PASS, so W9 runs tonight. Promoted OK at 22:41:28, and again after the PASS at 22:46:22 with an identical file (`stage-W9-224622.txt`).
- W5b r6: promoted OK at 22:40:54 (`stage-W5b-224054.txt`).
- W4c r6: promoted OK at 22:40:57 (`stage-W4c-224057.txt`).
- W8a4 r6, Monday fallback only: promoted OK at 22:35:01 (`stage-W8a4-223501.txt`, with native4's r5/r6 functional cover). W8a itself goes to Monday's day session on native4b, after the re-pin and s4b02/05.
