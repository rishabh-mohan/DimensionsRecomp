# Agent 3 handoff (11-23, before the pause)

Agent 3 runs the game for functional checks and keeps the run/measure harness. All my runs are functional only (hidden desktop, never timed); timing runs belong to Agent 8. I made no git changes; only Agent 1 commits or pushes.

## State (11-23, about 07:10)

- **Nothing is running.** None of my processes are left: no game, queue, postcheck, hostload, holdwatch, wait-event or sidecar. `build/agent3/s4b/STOP` exists, so `s4b-queue.ps1` ends before its first launch if someone starts it.
- **Last task (#23), done:**
  - **f10:** do the finding-10 hangs happen on a quiet host?
    - 0 of 4 quiet runs hung: f10a and f10a2 used s4b20's set, f10b and f10b2 gate B's set.
    - Under Agent 2's -j8 build last night, 4 of 6 runs hung (one-sided Fisher p = 0.07).
    - The long stall is host-side and comes in episodes.
    - Write-up: `build/agent3/f10/RESULTS.md`.
  - **Native4b re-pin rows.** Both were reported to Agents 1 and 4, who make the pin decision.
    - rpb0 PASS (06:17-06:19). `native3_boot_check.py` gave A/B/C/D PASS; output in `build/agent3/s4b/logs/rpb0.boot.txt`.
    - rpm4 PASS (06:20-06:29). Every REPIN section 3b check passes; output in `build/agent3/s4b/logs/rpm4.3b.txt` and `rpm4.draws.txt`.
- **S4b queue** (`build/agent3/s4b/queue.jsonl`).
  - Done: f10a, f10b, f10a2, f10b2, rpb0 and rpm4 (see `queue-state.jsonl`).
  - The other 19 pending rows are commented out with `#`. `queue.jsonl.bak-0550` is the file from before they were commented out.
- **Markers in `build/agent3/s4b/`.**
  - Still there from run 2: `ready-s4b-off`, `ready-dbg`, `ready-g3` and `ready-m1`. They record checks made on 11-22: the devoff4b-bin needles, d3d12SDKLayers.dll present, the G3 matrix, and Agent 5's G4. Re-check before reuse.
  - Removed at 06:59: the run-specific markers (`ready-later`, `ready-quiet`, `ready-repin`, `ready-rpm4`, `ready-f10r2`).

## What I own

| path | what |
|---|---|
| `build/agent3/s4b/` | the S4b functional queue (below) |
| `build/agent3/toypad/` | virtual Toy Pad tags (below) |
| `build/agent3/f10/` | the f10 analysis (below) |
| `build/agent3/s4a/` | the S4a queue tools from task #5: `s4a-queue.ps1`, `attach.ps1`, `s4a_check.py` (`s4b_check.py` imports it), `postcheck.ps1`, `slowstate.ps1` |
| `build/agent3/runs/` | 64 run folders, all functional. `rpb0-20261123-0617` and `rpm4-20261123-0620` are run-matrix output folders |
| `build/agent3/vpad/`, `seed/`, `selftest-bin/`, `selftest-runs/`, `patches/`, `rtpatch/`, `test/`, `scratch/`, `logs/` | older sessions; see the notes |
| `perf-notes/agent3-run-harness.md` | my notes. Section 9 = the S4b queue; 9.2.5 = task #23 |

`build/agent3/f10/` holds:

- `RESULTS.md`;
- the scripts `f10_results.py`, `sync_profile.py`, `align.py` and `cine.py`, plus `run_n2.ps1`, which runs all of them;
- their outputs (`*.n1.*` are the n = 1 versions) and `compare-lastnight.md`;
- the 05:50 prep scripts: `prep_0550.py`, `patch_queue_quiet.py`, `test_quiet.ps1`.

Shared files I wrote and maintain outside `build/agent3/`:

- `harness/run-game.ps1`, the functional runner, including `-InputScript`;
- `harness/vpad/`, the virtual XInput pad;
- `harness/route-report.ps1` and `harness/attract-report.py`;
- my route files in `harness/routes/`: `b-gate-menus*.txt`, `attract-long.txt`, `selftest-input.txt`.

### `build/agent3/s4b/`

- **`s4b-queue.ps1`**, the runner. It runs one row at a time from `queue.jsonl`, in file order.
  - Rows run through `harness/run-game.ps1` or run-matrix. Matrix rows write to `build/agent3/runs/<id>-<stamp>`, never to `build/agent8/matrix`.
  - It launches nothing while `perf-notes/WINDOW-HOLD.txt` or `PAUSE` exists. A `STOP` file ends the queue before the next launch.
  - `needs` lists marker files a row waits for. `-LastLaunch` and `-GamesClosed` are the cut-offs. `-QuietCpuPct` / `-QuietSampleSec` turn on the quiet-host gate.
  - Each launch also starts `holdwatch.ps1` (`holdwatch-m.ps1` for matrix rows), which stops my game if the HOLD file appears. Rows with `"toypad": true` also start the toypad sidecar.
  - State goes to `queue-state.jsonl` and the log to `logs/queue.out.txt`.
- **`postcheck.ps1`** runs after each finished row at Below Normal. It runs `s4b_check.py` against the row's base, and Agent 12's `p2c_check.py` on P2 rows. Output: `logs/<id>.check.txt` and `logs/<id>.p2c.txt`. Log: `logs/postcheck.out.txt`.
- **`s4b_check.py`**: S4b log families, logdiff on joined logs, BASE/PROOF lines, the STUCK-LOCK/hang scan, and a verdict hint.
- **`hostload.ps1`** writes a row every ~30 s to `logs/hostload.csv`: LoadPercentage, compiler counts, the game pid and the top 4 processes.
- **`wait-event.ps1 -Minutes N -Reset`** blocks until one of: a queue or postcheck line, a bin change, the W6 matrix, or a HOLD change.
- **Other scripts:**
  - `bincheck.py` finds the S4b cvar and log needles in a bin.
  - `gw_stats.py`.
  - `rpm4_3b_check.ps1` and `rpm4_draws.py` do the REPIN section 3b checks.
  - One-off edit scripts: `patch_f10_2255.py`, `add_f10r2_0628.py`, `reorder_*.py`, `stop_2233.py`, `fix_v0_2216.py`. Their `.bak-*` backups sit next to the files they changed.
- **Folders:** `logs/`; `checks/` (per-row checks and joined logs); `preflight/`; `g3/` (a copy of the W6 G3 matrix).

### `build/agent3/toypad/`

- **`toypad_sidecar.py`** places tags through the game's Toy Pad TCP listener (127.0.0.1:9191) when the route reaches a mark. It follows game.log across log rotation; that was fixed at 22:49 on 11-22, after gate B lost its tags.
- **Other tools:** `toypad_client.py`, `ldtag.py` (tag images), `fake_listener.py`, `explore.ps1`.
- **Self-tests:** `selftest_toypad.py --cpp`, `selftest_sidecar.py` and `selftest_rotation.py`. All passed on 11-22.
- **Data:**
  - `tags/`: Batman, Gandalf, Wyldstyle;
  - `routes/level-l.txt`: the vpad L route to the first level, 119 steps, about 430-500 s.
- **Rules** (decision 1, the user, 11-22 17:27):
  - user-mode only, with no drivers or system-wide installs;
  - nothing in `build/agent2/*-bin`;
  - saves isolated per run.

## Open items (none started)

From Agent 1's list for after the windows:

1. **s4bLV**, for C1 default-ON. It must run with the fixed sidecar, show 3/3 LOADs, and reach the level with verify on.
2. **s4bV0**: row 7 with the L route, which Agent 10 asked for. Agree the route with Agent 12 first. It goes together with:
   - **s4b04** and **s4b08**;
   - the long-cap p2fc + verify level-load row (cap > 600 s, S21 A).
3. **The remaining S4b rows**, commented out in `queue.jsonl`: s4b19, s4b02/05/06/03, s4b09-16, s4b21 and s4b25. Also an `s4b08c` row on the CTR bin, if P2's counter is still needed.
4. **f10 follow-ups.** Each needs Agent 1's OK.
   - A third quiet pair: p = 0.03 if it doesn't hang either.
   - A controlled-load repeat with about 8 busy user-mode threads and no build.
   - An s4b20-style loaded row with `slow_frame_log_ms=1`.
   - `-GpuLog` on such rows.

## How to restart the queue

1. Before every command, check that `perf-notes/WINDOW-HOLD.txt` doesn't exist. Get Agent 1's go.
2. Re-check the bins (`build/agent3/s4b/bincheck.py`, the MANIFEST). Then re-create the markers that the rows' `needs` lists name.
3. Edit `queue.jsonl`: uncomment or add rows; file order is priority.
   - A row id with a record in `queue-state.jsonl` that isn't marked `aborted` counts as done and is not run again. A `skipped` record counts as done too; there are none now.
   - Done so far: s4b01, s4b07, s4b17, s4b18, s4b20, s4b22, s4b23, s4b24, s4bL0, w6gA, w6gB, w6s1, w6s2, w6s3, g3q, f10a, f10b, f10a2, f10b2, rpb0 and rpm4.
   - To run one of these again, give it a new id.
4. Delete `build/agent3/s4b/STOP`.
5. Start these as background tasks, in this order:
   1. `hostload.ps1 -Until HH:mm:ss`;
   2. `postcheck.ps1 -Until HH:mm:ss`;
   3. `s4b-queue.ps1 -LastLaunch HH:mm -GamesClosed HH:mm`. For quiet-host rows add `-QuietCpuPct 40 -QuietSampleSec 10`.
6. Wait with `wait-event.ps1 -Minutes N -Reset`.
7. To stop, create `STOP`. Nothing new launches, and a running game finishes. Once the last check is written, stop postcheck and hostload.

## Rules that applied on 11-22/23

- Check `perf-notes/WINDOW-HOLD.txt` before every command or launch. While it exists, make no tool calls.
- Functional runs only, on the hidden desktop. No timed runs. Builds at most 2 threads; I made none.
- Never write to `build/agent8/matrix` or to a staged `build/agent2/*-bin`.
- Subagents only read, stage and check.
- Only Agent 1 commits or pushes.

## Where the results are

- **f10** (finding 10 on a quiet host): `build/agent3/f10/RESULTS.md`.
- **Finding 10 itself** (hang stacks, CP state): Agent 6's `build/agent6/hang/cp-state-s4b24-s4b20.md`. Its S7 covers GPU vs host.
- **Run-2 S4b queue** results, rulings and the sidecar fix: notes sections 9.2.1-9.2.4.
- **rpb0 / rpm4:** notes section 9.2.5, plus `build/agent3/s4b/logs/rpb0.boot.txt`, `rpm4.3b.txt` and `rpm4.draws.txt`.
- **S4a:** notes section 8.
