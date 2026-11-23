# Window 5 draft (Agent 8, task #10 standby work, 2026-11-22)

**Status: DRAFT. Agent 1 accepted it at 14:23. It is not in place yet: the line choice (S3d or B) waits for the user, after W4b.** Only `-PlanOnly` has run: v1 at 14:11, and v2 at 14:19 with Agent 11's d11p answers. It wrote nothing outside this folder. `build\agent8\matrix\` still has 19 entries (newest `20261122-0657`). `bench/agent8/**` is untouched because of the W4b freeze.

- **Source:** `perf-notes/S4-DRAFT.md` L287. W5 is the S4 baseline plus timer modes: base / s0 / d11 / d11t / d11p, 1 cold + 5 x 3 = 16 runs, ~40 min.
  - Arm names: L278-283.
  - Window rules: L255-276.
- **Model:** `bench/agent8/RUN-WINDOW4B.cmd` and `bench/agent8/run/matrix-window4.json`. W5 uses the same window, frame source, driver, flags, sys.csv and floor, with `-ColdShared`.
- **d11p switches:** Agent 11 confirmed them at 14:14. They are as drafted: d11 + `timer_queue_precise_wait=true`, with `REX_TIMER_WAIT_BLOCKING` unset, and `host_timer_resolution_ms=1` kept.

## Decisions (Agent 1, 14:23)

- **Reference:** `base` stays the reference, as d0 was in W4b. The read-out also reports d11, d11t and d11p against s0, so the timer modes are compared within one bin. The JSONs stay as they are.
- **Line choice (S3d or B):** waits for the user, after W4b. So do the devoffB4 checks: the path, `rexruntime.dll` = 870276A6D0E8DE57, and the MANIFEST hash.
- **timerq_slowstate:** take Agent 11's 3-mode copy after W4b. The original stays frozen as a W4b read-out input.
- **Env restore:** Agent 1 read run-timing.ps1 L218-225.
  - Env values are restored in `finally` right after Start-Process.
  - `REX_TIMER_WAIT_BLOCKING` is not set in the Process, User or Machine scope.
  - So a d11t run's env can't leak into the other arms.

## Files

| file | what |
|---|---|
| `matrix-window5-s3d.json` | S3d line: base = devoff3; s0 / d11 / d11t / d11p = devoff4 (S4a, staged 13:31) |
| `RUN-WINDOW5-S3D.cmd` | Double-click file for the S3d line |
| `matrix-window5-b.json` | B line: base = devoffB; s0 / d11 / d11t / d11p = devoffB4 (**placeholder**, not built; Agent 2's #15) |
| `RUN-WINDOW5-B.cmd` | Double-click file for the B line |
| `planonly-s3d-1419.txt`, `planonly-b-1419.txt` | `-PlanOnly` output, with write checks before and after |

## Arms (both lines)

| arm | S3d line bin | B line bin | cvars (besides `framerate_limit=0`) | env |
|---|---|---|---|---|
| base (ref) | devoff3 (MANIFEST B9C5175DA1904235) | devoffB (8709476FF4778768) | none | none |
| s0 | devoff4 (16DCC9399239E577): S4a, every new switch OFF, #32 on | devoffB4 (placeholder) | none | none |
| d11 | devoff4 | devoffB4 | the 8 timer cvars | none |
| d11t | devoff4 | devoffB4 | the 8 timer cvars | `REX_TIMER_WAIT_BLOCKING=1` |
| d11p | devoff4 | devoffB4 | the 8 timer cvars + `timer_queue_precise_wait=true` | none |

- **The 8 timer cvars** (the same list as W4b's d11t): `host_timer_resolution_ms=1 host_timer_throttling_optout=true precise_guest_sleep=true wait_timeout_round_up=true cs_spin=true spinlock_pause_spin=true clock_lockfree=true tls_bounds_fix=true`.
- **s0 sets no S4 cvar.** `shared_memory_upload_hash_log`, `shared_memory_single_hold_rearm`, `physical_protect_hold_global_lock` and `timer_queue_precise_wait` all default to false (devoff4 MANIFEST).
- **d11p keeps `host_timer_resolution_ms=1`** (Agent 11), so d11p and d11t differ only in the TimerQueue wait mode.
  - The resolution setting affects every timed wait in the process (guest sleeps and waits, Win32 timers), not just the TimerQueue. Dropping it would add a second variable.
  - Precise wait without 1 ms would need its own arm later, not in W5.

## Proof and gates per run (check these before reading any fps)

| arm | 1 ms line | precise-wait line | `REX_TIMER_WAIT_BLOCKING` in run.json `env_set` | TimerQueue, % of one core (expected; gate) |
|---|---|---|---|---|
| base | no | no | no | ~30-60 % (spin) |
| s0 | no | no | no | ~30-60 % (spin) |
| d11 | yes | no | no | ~30-60 % (spin); gate > 20 % |
| d11t | yes | no | **yes** | ~0.3-1.5 %; gate < 5 % |
| d11p | yes | **exactly one** | no | ~1-2 %; gate < 5 % |

- **1 ms line:** `Host timer resolution set to 1 ms (background opt-out on)` (threading_win.cpp:252).
- **Precise-wait line:** `TimerQueue: precise wait (timer_queue_precise_wait)` (staged timer_queue.cpp:71). In r4 it was logged once, 6.29 s before the first frame.
- **d11t logs nothing for the blocking wait.** Neither the pristine nor the staged code logs it. Its proof is three things together:
  - `REX_TIMER_WAIT_BLOCKING` in run.json `env_set`;
  - no precise line;
  - low TimerQueue CPU in threads.csv.
- **CPU can't tell d11t from d11p.** Only the precise line separates them.
- Expected CPU figures come from Agent 11:
  - devoff4 r1 37.65 %, r3 36.62 % (spin);
  - d0t in game 0.4 %, bench 1.4 % at 1 ms (blocking);
  - r4 1.25 %, bench 1.7-1.9 % (precise).

## REX_TIMER_WAIT_BLOCKING is presence-only

- The game reads it once, at static init, and tests `getenv != nullptr`. So `=0` or an empty value still turns the blocking wait on.
- `timer_queue_precise_wait` is applied at the first QueueTimer call. **If both are set, precise wins, and nothing logs the env var.** A d11p run with a leaked variable therefore looks exactly like a clean d11p run.
- Rule: base, s0, d11 and d11p must not have the variable at all, and it must not carry over from a d11t run. How that is enforced:
  - Both .cmd files run `set "REX_TIMER_WAIT_BLOCKING="` before anything else, which removes any inherited copy.
  - The runner sets the variable for d11t runs only and restores the environment in `finally` right after Start-Process (run-timing.ps1 L218-225; Agent 1, 14:23). run-matrix.ps1 also restores it per run (L654/L663). It records `env_set` in run.json (run-timing.ps1 L713).
  - No `REX_*` variable was set in the User, Machine or Process environment at 14:07.

## Plan (runner `-PlanOnly`, 14:19)

```
cold     base (build/agent2/devoff3-bin): unscored, before round 1 (warm-up 55 s, window 30 s)
         -ColdShared: one cold run for all 2 bin(s); the other bins first launch as scored round-1 runs
round 1  base s0 d11 d11t d11p
round 2  s0 d11 d11t d11p base
round 3  d11 d11t d11p base s0
estimate 16 runs (1 cold), about 37 min (warm boot 12 s, cold boot 25 s, close 5 s per run)
```

- **Every window:** 5 s settle, then 55 s warm-up from the first frame, then 50 s measured. Every window therefore starts at least 60 s after the first frame. All runs are uncapped, read perf.csv, use the thread-cpu driver and log sys.csv.
- **B line today:** devoffB4 is missing, so the runner would skip s0, d11, d11t and d11p and run only the cold run plus base x3 (4 runs, ~10 min). The `staged` line gives the full plan for once devoffB4 exists: `base s0 d11 d11t d11p | s0 d11 d11t d11p base | d11 d11t d11p base s0; 16 runs, about 37 min`.

## Checks done (14:19-14:21)

- **Formats:**
  - Both JSONs parse with `ConvertFrom-Json`. They are ASCII only, with no `\u` escapes.
  - Both .cmd files are ASCII with CRLF line endings (39 CR / 39 LF each).
  - Arm settings were read back from the parsed JSONs and match the arm table above.
- **Guards, from this folder:** each .cmd prints `This is the window 5 DRAFT ... Nothing was started.` and exits 1.
- **Guards, in a fake promoted tree:** this used a dummy `run-matrix.ps1` that only prints its arguments (scratch `w5-cmdsim.ps1`; the tree was deleted afterwards).
  - S3d with both bins staged, and B with both bins staged: each .cmd calls the runner with `-Matrix matrix-window5-<line>.json -Only base,s0,d11,d11t,d11p -Repeats 3 -ColdShared -NoPrompt`.
  - The parent shell had `REX_TIMER_WAIT_BLOCKING=0`, and the runner did not see the variable.
  - The runner's exit code is echoed.
  - A missing devoff4 MANIFEST, and an unstaged devoffB4: the `nobin` message, exit 1.
  - The matrix JSON missing from `run\`: the DRAFT message, exit 1.
- **PlanOnly s3d and b:** both exit 0. Before and after each run, these had 0 differences:
  - `bench\agent8` (141 entries);
  - `build\agent8` except this folder (3,567 entries);
  - `harness`, top level (14);
  - `%TEMP%`, top level (924).
  - Repo root, top level (14 entries): 0 differences for b. For s3d, one: the `.agy-grid` directory's timestamp changed. That folder holds the agents' board messages, not runner output. PlanOnly exits before any write (run-matrix.ps1 L434-438), and the b run 10 s later had 0 differences.
  - Matrix stayed at 19 dirs (newest `20261122-0657`) and the cache at 10 files.
- **Machine state:** the 14:19 preflight saw Agent 3's `legodimensions.exe` (pid 32476), which is expected until 14:45. It would be FATAL only for a real start. No builds were running.

## Promoting it (after W4b, once the user has chosen the line, with Agent 1's go)

1. Copy the chosen line's matrix JSON to `bench/agent8/run/` and its .cmd to `bench/agent8/`. For the S3d line: `matrix-window5-s3d.json` and `RUN-WINDOW5-S3D.cmd`.
2. Remove "DRAFT" and "Not approved" from the title and the first note.
3. The B line also needs devoffB4 staged. Before copying it:
   - Check the bin path.
   - Check that `devoffB4-bin\rexruntime.dll` = 870276A6D0E8DE57 (the S4a SDK, as in devoff4-bin; Agent 11).
   - Put the bin's MANIFEST hash into the s0 note, and drop the PLACEHOLDER note.
4. Run the same `-PlanOnly` from `bench/agent8` and check the plan. Then freeze and hash W5's inputs, as was done for W4b.
5. Before the read-out, two things are needed:
   - A W5 read-out procedure, like W4b's in `perf-notes/agent8-window3.md`, built on the proof-and-gates table above. It reports d11, d11t and d11p against base (the reference) and also against s0.
   - Agent 11's 3-mode copy of `bench/agent11/timerq_slowstate.ps1`, taken after W4b (Agent 1, 14:23). The original groups runs by `env_set` only, so d11p runs would land in its spin group. It is a W4b read-out input and stays frozen.

## Notes for the line choice and the read-out

1. **B line caveat.** devoffB (base) keeps devoff2's SDK (rexruntime.dll 1C45C86977EC594C) and S2-level rexlego (`build/agent2/b4-dryrun-1404.txt` [2]). devoffB4 links the S4a SDK (870276A6D0E8DE57).
   - So on the B line, s0 vs base spans S2 -> S4a (SDK and rexlego), not S4a alone.
   - On the S3d line, base (devoff3, rexruntime D1D66AC3716835AC) and s0 (devoff4) differ by S4a only.
   - The timer-mode deltas against s0 (d11 / d11t / d11p) are within one bin on both lines.
2. **Order.** The runner's `roundrobin` rotates the arm list each round, the same scheme as W4b. Each arm runs once per round and never twice in the same position.
   - In rounds 2-3, base always follows d11p, and d11t always follows d11.
   - A balanced (Williams) order would need a runner change, and the runner is frozen until after W4b.
3. **Environment.** All W5 runs come after the 08:29-08:34 Windows Update (Intel DTT 9.1.10501.3322, Intel IPF 3.4.1009.0, KB5132057, build 26300.10075).
   - So W5 compares with W4b.
   - Any comparison with window 3 or overnight numbers must say so. This is written into both JSONs.
